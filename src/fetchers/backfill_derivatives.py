#!/usr/bin/env python3
"""
Derivatives Historical Backfill
================================
Downloads 180 days of historical derivatives data from Coinglass and stores
daily rows in the derivatives_snapshots table for backtesting.

Per-symbol (6 API calls each):
    1. Funding Rate OHLC history
    2. OI aggregated history
    3. Global L/S account ratio
    4. Top trader L/S ratios (account + position = 2 calls)
    5. Aggregated liquidation history

Global (3 API calls, BTC-level):
    6. Fear & Greed history
    7. BTC ETF flow history
    8. Coinbase Premium history

Usage:
    python3 src/fetchers/backfill_derivatives.py backfill              # Full backfill
    python3 src/fetchers/backfill_derivatives.py backfill --symbol BTC  # Single symbol
    python3 src/fetchers/backfill_derivatives.py backfill --dry-run     # Preview only
    python3 src/fetchers/backfill_derivatives.py coverage               # Check coverage
"""

import argparse
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.fetchers.coinglass_fetcher import (
    fetch_funding_rate_ohlc,
    fetch_oi_history,
    fetch_global_ls_ratio,
    fetch_top_ls_ratios,
    fetch_liquidation_history,
    fetch_fear_greed,
    fetch_btc_etf_flows,
    fetch_coinbase_premium,
)

INTEL_DB = PROJECT_ROOT / "data" / "titan_intelligence.db"

UNIVERSE = sorted(set([
    "BTC", "ETH", "SOL", "HYPE", "DOGE", "XRP", "AVAX", "LINK", "SUI", "ARB",
    "OP", "PEPE", "WIF", "TIA", "SEI", "INJ", "JUP", "ONDO", "PYTH", "STX",
    "NEAR", "FTM", "AAVE", "MKR", "PENDLE", "TAO", "RENDER", "ZRO", "AERO", "WLD",
    "BNB", "BCH", "ENS", "UNI", "FLOW", "ASTER", "XPL", "SKYAI", "SKY",
    "SYRUP", "WLFI", "FARTCOIN", "PUMP", "ENA", "0G",
]))

BARS_180D = 1080  # 180 days * 6 bars/day at 4h


# ============================================================================
# HELPERS
# ============================================================================

def _get_bar_time(bar: dict) -> int:
    """Extract timestamp (ms) from a bar dict, trying common field names."""
    for key in ("time", "t", "createTime", "timestamp"):
        v = bar.get(key, 0)
        if v:
            return int(v)
    return 0


def ts_to_date(ts_ms: int) -> str:
    """Convert millisecond timestamp to YYYY-MM-DD string."""
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def group_by_date_last(bars: list) -> dict:
    """Group bars by date, keeping only the last bar per date (snapshot fields)."""
    by_date = {}
    for bar in bars:
        if not isinstance(bar, dict):
            continue
        ts = _get_bar_time(bar)
        if ts <= 0:
            continue
        date = ts_to_date(ts)
        by_date[date] = bar  # later bars overwrite earlier (list is chronological)
    return by_date


def group_by_date_sum(bars: list, sum_keys: list) -> dict:
    """Group bars by date, summing specified fields (for cumulative data like liquidations)."""
    by_date = defaultdict(lambda: {k: 0.0 for k in sum_keys})
    for bar in bars:
        if not isinstance(bar, dict):
            continue
        ts = _get_bar_time(bar)
        if ts <= 0:
            continue
        date = ts_to_date(ts)
        for k in sum_keys:
            val = bar.get(k, 0)
            if val is not None:
                by_date[date][k] += float(val)
    return dict(by_date)


# ============================================================================
# DERIVED FIELD COMPUTATIONS
# ============================================================================

def compute_funding_bias(rate: float) -> str:
    if rate > 0.0003:
        return "long_crowded"
    elif rate > 0.0001:
        return "moderately_long"
    elif rate < -0.0003:
        return "short_crowded"
    elif rate < -0.0001:
        return "moderately_short"
    return "neutral"


def compute_oi_trend(change_pct: float) -> str:
    if change_pct > 5:
        return "rising"
    elif change_pct < -5:
        return "falling"
    return "flat"


def compute_ls_smart_money_lean(pos_ratio: float) -> str:
    if pos_ratio > 1.15:
        return "long"
    elif pos_ratio < 0.85:
        return "short"
    return "neutral"


def compute_fear_greed_label(value: int) -> str:
    if value <= 20:
        return "Extreme Fear"
    elif value <= 40:
        return "Fear"
    elif value <= 60:
        return "Neutral"
    elif value <= 80:
        return "Greed"
    return "Extreme Greed"


def compute_coinbase_premium_bias(rate: float) -> str:
    if rate > 0.0005:
        return "us_buying"
    elif rate < -0.0005:
        return "us_selling"
    return "neutral"


def compute_etf_fields(etf_by_date: dict, date: str) -> dict:
    """Compute ETF derived fields for a given date from the full daily flow map."""
    result = {}

    if date not in etf_by_date:
        return result

    all_dates = sorted(etf_by_date.keys(), reverse=True)
    try:
        idx = all_dates.index(date)
    except ValueError:
        return result

    flow = etf_by_date[date]
    result["etf_latest_day_flow_usd"] = flow

    # Weekly net: this date + 6 prior
    weekly_dates = all_dates[idx:idx + 7]
    weekly_net = sum(etf_by_date.get(d, 0) for d in weekly_dates)
    result["etf_weekly_net_flow_usd"] = weekly_net

    # Streak: consecutive same-sign days
    streak = 0
    sign = 1 if flow >= 0 else -1
    for d in all_dates[idx:]:
        f = etf_by_date.get(d, 0)
        if (f >= 0 and sign > 0) or (f < 0 and sign < 0):
            streak += 1
        else:
            break
    result["etf_streak_days"] = streak * sign

    # Bias
    if weekly_net > 500_000_000:
        result["etf_bias"] = "strong_inflow"
    elif weekly_net > 100_000_000:
        result["etf_bias"] = "moderate_inflow"
    elif weekly_net < -500_000_000:
        result["etf_bias"] = "strong_outflow"
    elif weekly_net < -100_000_000:
        result["etf_bias"] = "moderate_outflow"
    else:
        result["etf_bias"] = "mixed"

    return result


# ============================================================================
# DATA FETCHING
# ============================================================================

def fetch_symbol_data(symbol: str, dry_run: bool = False) -> dict:
    """Fetch all 6 per-symbol data sources. Returns dict of raw data."""
    results = {"symbol": symbol, "errors": [], "counts": {}}

    if dry_run:
        results["counts"] = {
            "funding": BARS_180D, "oi": BARS_180D, "ls": BARS_180D,
            "top_ls_acct": BARS_180D, "top_ls_pos": BARS_180D, "liq": BARS_180D,
        }
        return results

    # 1. Funding Rate OHLC (1 API call)
    funding = fetch_funding_rate_ohlc(symbol, interval="4h", limit=BARS_180D)
    if funding and isinstance(funding, list):
        results["funding"] = funding
        results["counts"]["funding"] = len(funding)
    else:
        results["errors"].append("funding")
        results["counts"]["funding"] = 0

    # 2. OI History (1 API call)
    oi = fetch_oi_history(symbol, interval="4h", limit=BARS_180D)
    if oi and isinstance(oi, list):
        results["oi"] = oi
        results["counts"]["oi"] = len(oi)
    else:
        results["errors"].append("oi")
        results["counts"]["oi"] = 0

    # 3. Global L/S (1 API call)
    ls = fetch_global_ls_ratio(symbol, interval="4h", limit=BARS_180D)
    if ls and isinstance(ls, list):
        results["ls"] = ls
        results["counts"]["ls"] = len(ls)
    else:
        results["errors"].append("ls")
        results["counts"]["ls"] = 0

    # 4. Top L/S — account + position (2 API calls)
    top_ls = fetch_top_ls_ratios(symbol, interval="4h", limit=BARS_180D)
    if top_ls and isinstance(top_ls, dict):
        results["top_ls"] = top_ls
        acct = top_ls.get("account", [])
        pos = top_ls.get("position", [])
        results["counts"]["top_ls_acct"] = len(acct) if isinstance(acct, list) else 0
        results["counts"]["top_ls_pos"] = len(pos) if isinstance(pos, list) else 0
    else:
        results["errors"].append("top_ls")
        results["counts"]["top_ls_acct"] = 0
        results["counts"]["top_ls_pos"] = 0

    # 5. Liquidation History (1 API call)
    liq = fetch_liquidation_history(symbol, interval="4h", limit=BARS_180D)
    if liq and isinstance(liq, list):
        results["liq"] = liq
        results["counts"]["liq"] = len(liq)
    else:
        results["errors"].append("liq")
        results["counts"]["liq"] = 0

    return results


def fetch_global_data(dry_run: bool = False) -> dict:
    """Fetch the 3 global/BTC-level data sources."""
    results = {"errors": [], "counts": {}}

    if dry_run:
        results["counts"] = {"fear_greed": 564, "etf": 564, "coinbase_premium": BARS_180D}
        return results

    # Fear & Greed (1 API call)
    fg = fetch_fear_greed()
    if fg and isinstance(fg, dict):
        results["fear_greed"] = fg
        results["counts"]["fear_greed"] = len(fg.get("data_list", []))
    else:
        results["errors"].append("fear_greed")
        results["counts"]["fear_greed"] = 0

    # BTC ETF Flows (1 API call)
    etf = fetch_btc_etf_flows()
    if etf and isinstance(etf, list):
        results["etf"] = etf
        results["counts"]["etf"] = len(etf)
    else:
        results["errors"].append("etf")
        results["counts"]["etf"] = 0

    # Coinbase Premium (1 API call)
    cb = fetch_coinbase_premium(interval="4h", limit=BARS_180D)
    if cb and isinstance(cb, list):
        results["coinbase_premium"] = cb
        results["counts"]["coinbase_premium"] = len(cb)
    else:
        results["errors"].append("coinbase_premium")
        results["counts"]["coinbase_premium"] = 0

    return results


# ============================================================================
# DATA ASSEMBLY
# ============================================================================

def build_global_by_date(global_data: dict) -> dict:
    """Convert global data into per-date dicts for merging into symbol rows."""
    by_date = defaultdict(dict)

    # Fear & Greed — parallel arrays: data_list[i] ↔ time_list[i]
    fg = global_data.get("fear_greed")
    if fg and isinstance(fg, dict):
        data_list = fg.get("data_list", [])
        time_list = fg.get("time_list", [])
        for i, ts in enumerate(time_list):
            if i < len(data_list):
                date = ts_to_date(int(ts))
                value = int(float(data_list[i]))
                by_date[date]["fear_greed_value"] = value
                by_date[date]["fear_greed_label"] = compute_fear_greed_label(value)

    # ETF flows — build date→flow map, then compute derived fields per date
    etf = global_data.get("etf")
    etf_by_date = {}
    if etf and isinstance(etf, list):
        for item in etf:
            if not isinstance(item, dict):
                continue
            ts = item.get("timestamp", 0)
            if ts <= 0:
                continue
            date = ts_to_date(ts)
            flow = float(item.get("flow_usd", 0) or 0)
            etf_by_date[date] = flow

        for date in etf_by_date:
            by_date[date].update(compute_etf_fields(etf_by_date, date))

    # Coinbase Premium — take last 4h bar per date
    cb = global_data.get("coinbase_premium")
    if cb and isinstance(cb, list):
        cb_by_date = group_by_date_last(cb)
        for date, bar in cb_by_date.items():
            rate = float(bar.get("premium_rate", 0) or 0)
            by_date[date]["coinbase_premium_rate"] = round(rate, 6)
            by_date[date]["coinbase_premium_bias"] = compute_coinbase_premium_bias(rate)

    return dict(by_date)


def build_daily_rows(symbol: str, raw: dict) -> list:
    """Convert raw 4h bar data into daily derivatives_snapshots rows."""
    # Group each dataset by date
    funding_by_date = {}
    oi_by_date = {}
    ls_by_date = {}
    top_acct_by_date = {}
    top_pos_by_date = {}
    liq_by_date = {}

    if "funding" in raw and isinstance(raw["funding"], list):
        funding_by_date = group_by_date_last(raw["funding"])

    if "oi" in raw and isinstance(raw["oi"], list):
        oi_by_date = group_by_date_last(raw["oi"])

    if "ls" in raw and isinstance(raw["ls"], list):
        ls_by_date = group_by_date_last(raw["ls"])

    if "top_ls" in raw and isinstance(raw["top_ls"], dict):
        acct = raw["top_ls"].get("account", [])
        pos = raw["top_ls"].get("position", [])
        if isinstance(acct, list):
            top_acct_by_date = group_by_date_last(acct)
        if isinstance(pos, list):
            top_pos_by_date = group_by_date_last(pos)

    # Liquidations: SUM per day (cumulative data, not snapshot)
    if "liq" in raw and isinstance(raw["liq"], list):
        liq_sum_keys = [
            "longLiquidationUsd", "shortLiquidationUsd",
            "buyVolUsd", "sellVolUsd",
            "long_liquidation_usd", "short_liquidation_usd",
            "aggregated_long_liquidation_usd", "aggregated_short_liquidation_usd",
        ]
        liq_by_date = group_by_date_sum(raw["liq"], liq_sum_keys)

    # Collect all dates
    all_dates = sorted(set(
        list(funding_by_date.keys()) +
        list(oi_by_date.keys()) +
        list(ls_by_date.keys()) +
        list(top_acct_by_date.keys()) +
        list(top_pos_by_date.keys()) +
        list(liq_by_date.keys())
    ))

    rows = []
    prev_oi_close = None

    for date in all_dates:
        row = {
            "timestamp_utc": f"{date}T23:59:00+00:00",
            "symbol": symbol.upper(),
            "source": "backfill",
        }

        # Funding — close of last 4h bar
        fb = funding_by_date.get(date)
        if fb:
            rate = float(fb.get("close", fb.get("c", 0)) or 0)
            row["funding_rate_avg"] = rate
            row["funding_bias"] = compute_funding_bias(rate)

        # OI — close of last 4h bar, compute 24h change vs previous day
        ob = oi_by_date.get(date)
        if ob:
            oi_close = float(ob.get("close", ob.get("c", 0)) or 0)
            row["oi_usd"] = oi_close
            if prev_oi_close and prev_oi_close > 0:
                change_pct = ((oi_close - prev_oi_close) / prev_oi_close) * 100
                row["oi_change_24h_pct"] = round(change_pct, 2)
                row["oi_trend"] = compute_oi_trend(change_pct)
            prev_oi_close = oi_close

        # Global L/S — last bar per day
        lb = ls_by_date.get(date)
        if lb:
            ratio = float(
                lb.get("global_account_long_short_ratio",
                       lb.get("longShortRatio",
                              lb.get("longAccount", 0))) or 0
            )
            long_pct = float(
                lb.get("global_account_long_percent",
                       lb.get("longRate",
                              lb.get("longPercent", 0))) or 0
            )
            if ratio > 0:
                row["ls_global_ratio"] = round(ratio, 4)
            if long_pct > 0:
                row["ls_global_long_pct"] = round(long_pct, 2)
            row["ls_extreme"] = 1 if (ratio > 2.5 or (0 < ratio < 0.4)) else 0

        # Top L/S — account + position, last bar per day
        tab = top_acct_by_date.get(date)
        if tab:
            acct_ratio = float(
                tab.get("top_account_long_short_ratio",
                        tab.get("longShortRatio",
                                tab.get("longAccount", 0))) or 0
            )
            if acct_ratio > 0:
                row["ls_top_account_ratio"] = round(acct_ratio, 4)

        tpb = top_pos_by_date.get(date)
        if tpb:
            pos_ratio = float(
                tpb.get("top_position_long_short_ratio",
                        tpb.get("longShortRatio",
                                tpb.get("longAccount", 0))) or 0
            )
            if pos_ratio > 0:
                row["ls_top_position_ratio"] = round(pos_ratio, 4)
                row["ls_smart_money_lean"] = compute_ls_smart_money_lean(pos_ratio)

        # Liquidation — SUM of all 4h bars for the day
        lqb = liq_by_date.get(date)
        if lqb:
            long_liq = (
                lqb.get("longLiquidationUsd", 0) +
                lqb.get("buyVolUsd", 0) +
                lqb.get("long_liquidation_usd", 0) +
                lqb.get("aggregated_long_liquidation_usd", 0)
            )
            short_liq = (
                lqb.get("shortLiquidationUsd", 0) +
                lqb.get("sellVolUsd", 0) +
                lqb.get("short_liquidation_usd", 0) +
                lqb.get("aggregated_short_liquidation_usd", 0)
            )
            total_liq = long_liq + short_liq
            if total_liq > 0:
                ls_liq_ratio = (long_liq / short_liq) if short_liq > 0 else 99.0
                row["liq_24h_usd"] = total_liq
                row["liq_long_24h_usd"] = long_liq
                row["liq_short_24h_usd"] = short_liq
                row["liq_ls_ratio"] = round(ls_liq_ratio, 2)

        rows.append(row)

    return rows


# ============================================================================
# DATABASE WRITES
# ============================================================================

def write_rows(rows: list, conn: sqlite3.Connection) -> int:
    """Insert or update rows in derivatives_snapshots. Returns count written."""
    written = 0
    for row in rows:
        date = row["timestamp_utc"][:10]
        symbol = row["symbol"]

        # Check for existing backfill row on this date + symbol
        cursor = conn.execute(
            "SELECT id FROM derivatives_snapshots "
            "WHERE symbol = ? AND timestamp_utc LIKE ? AND source = 'backfill'",
            (symbol, f"{date}%")
        )
        existing = cursor.fetchone()

        if existing:
            # Update: set all non-key fields that have values
            sets = []
            vals = []
            for k, v in row.items():
                if k in ("timestamp_utc", "symbol", "source"):
                    continue
                if v is not None:
                    sets.append(f"{k} = ?")
                    vals.append(v)
            if sets:
                vals.append(existing[0])
                conn.execute(
                    f"UPDATE derivatives_snapshots SET {', '.join(sets)} WHERE id = ?",
                    vals
                )
        else:
            # Insert new row
            cols = list(row.keys())
            placeholders = ", ".join(["?"] * len(cols))
            col_names = ", ".join(cols)
            conn.execute(
                f"INSERT INTO derivatives_snapshots ({col_names}) VALUES ({placeholders})",
                [row.get(c) for c in cols]
            )
        written += 1

    return written


# ============================================================================
# COMMANDS
# ============================================================================

def cmd_backfill(args):
    """Run the backfill."""
    symbols = [args.symbol.upper()] if args.symbol else UNIVERSE
    dry_run = args.dry_run

    print(f"Derivatives Backfill — {len(symbols)} symbols, 180 days, "
          f"{'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Database: {INTEL_DB}")
    print()

    if not dry_run:
        from src.storage.intelligence import init_db
        init_db()
        conn = sqlite3.connect(INTEL_DB)

    # Phase 1: Global data (F&G, ETF, Coinbase Premium)
    print("[GLOBAL] Fetching Fear & Greed, ETF flows, Coinbase Premium...")
    global_data = fetch_global_data(dry_run)
    fg_count = global_data["counts"].get("fear_greed", 0)
    etf_count = global_data["counts"].get("etf", 0)
    cb_count = global_data["counts"].get("coinbase_premium", 0)
    print(f"  Fear & Greed: {fg_count} days, ETF: {etf_count} days, "
          f"Coinbase Premium: {cb_count} bars")
    if global_data["errors"]:
        print(f"  ⚠️  Failed: {', '.join(global_data['errors'])}")

    if not dry_run:
        global_by_date = build_global_by_date(global_data)
    else:
        global_by_date = {}

    print()

    # Phase 2: Per-symbol data
    total_written = 0
    succeeded = []
    partial = []
    failed = []

    for idx, symbol in enumerate(symbols, 1):
        print(f"[{idx}/{len(symbols)}] {symbol}", end=" — ")

        raw = fetch_symbol_data(symbol, dry_run)
        counts = raw["counts"]

        count_parts = []
        for k in ["funding", "oi", "ls"]:
            count_parts.append(f"{k}: {counts.get(k, 0)} bars")
        count_parts.append(
            f"top_ls: {counts.get('top_ls_acct', 0)}+{counts.get('top_ls_pos', 0)} bars"
        )
        count_parts.append(f"liq: {counts.get('liq', 0)} bars")
        print(", ".join(count_parts))

        if dry_run:
            print(f"  → ~180 daily rows (dry run)")
            succeeded.append(symbol)
            continue

        # Build daily rows from 4h bar data
        rows = build_daily_rows(symbol, raw)

        # Merge global data into all symbol rows
        for row in rows:
            date = row["timestamp_utc"][:10]
            gd = global_by_date.get(date, {})

            # F&G is market-wide — merge into all symbols
            if "fear_greed_value" in gd:
                row.setdefault("fear_greed_value", gd["fear_greed_value"])
                row.setdefault("fear_greed_label", gd.get("fear_greed_label"))

            # ETF + Coinbase Premium — BTC-specific but market-relevant
            if symbol == "BTC":
                for k in ["etf_latest_day_flow_usd", "etf_weekly_net_flow_usd",
                           "etf_streak_days", "etf_bias",
                           "coinbase_premium_rate", "coinbase_premium_bias"]:
                    if k in gd:
                        row.setdefault(k, gd[k])

        # Write to database
        written = write_rows(rows, conn)
        conn.commit()
        total_written += written

        print(f"  → {written} daily rows written")

        if raw["errors"]:
            if len(raw["errors"]) >= 4:
                failed.append(symbol)
                print(f"  ⚠️  Failed endpoints: {', '.join(raw['errors'])}")
            else:
                partial.append(symbol)
                print(f"  ⚠️  Partial data (missing: {', '.join(raw['errors'])})")
        else:
            succeeded.append(symbol)

    if not dry_run:
        conn.close()

    # Summary
    print()
    print(f"Summary: {total_written} rows written across {len(symbols)} symbols")
    if succeeded:
        print(f"  ✅ Full data: {len(succeeded)} symbols")
    if partial:
        print(f"  ⚠️  Partial: {', '.join(partial)}")
    if failed:
        print(f"  ❌ Failed: {', '.join(failed)}")


def cmd_coverage(args):
    """Show what's in the database."""
    if not INTEL_DB.exists():
        print(f"No database found at {INTEL_DB}")
        return

    conn = sqlite3.connect(INTEL_DB)

    cursor = conn.execute(
        "SELECT symbol, source, COUNT(*) as cnt, "
        "MIN(timestamp_utc) as first_ts, MAX(timestamp_utc) as last_ts "
        "FROM derivatives_snapshots GROUP BY symbol, source ORDER BY symbol, source"
    )
    rows = cursor.fetchall()

    if not rows:
        print("No derivatives data in database.")
        conn.close()
        return

    print(f"{'Symbol':<10} {'Source':<15} {'Rows':>6} {'First':>12} {'Last':>12}")
    print("-" * 60)
    for symbol, source, cnt, first_ts, last_ts in rows:
        print(f"{symbol:<10} {source:<15} {cnt:>6} "
              f"{first_ts[:10]:>12} {last_ts[:10]:>12}")

    # Backfill totals
    cursor = conn.execute(
        "SELECT COUNT(DISTINCT symbol), COUNT(*), "
        "MIN(timestamp_utc), MAX(timestamp_utc) "
        "FROM derivatives_snapshots WHERE source = 'backfill'"
    )
    bf = cursor.fetchone()
    if bf and bf[0] > 0:
        print(f"\nBackfill totals: {bf[0]} symbols, {bf[1]} rows, "
              f"{bf[2][:10]} to {bf[3][:10]}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Derivatives Historical Backfill")
    sub = parser.add_subparsers(dest="command")

    bf = sub.add_parser("backfill", help="Download and store historical derivatives data")
    bf.add_argument("--symbol", type=str, help="Single symbol to backfill (default: all)")
    bf.add_argument("--dry-run", action="store_true", help="Preview without writing")

    sub.add_parser("coverage", help="Show database coverage")

    args = parser.parse_args()

    if args.command == "backfill":
        cmd_backfill(args)
    elif args.command == "coverage":
        cmd_coverage(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
