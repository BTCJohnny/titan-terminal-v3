#!/usr/bin/env python3
"""
Derivatives Historical Backfill
================================
One-time script to populate derivatives_snapshots with 180 days of historical data.

Usage:
    python3 scripts/backfill_derivatives.py                    # BTC + ETH, 180 days
    python3 scripts/backfill_derivatives.py --symbols BTC      # BTC only
    python3 scripts/backfill_derivatives.py --days 90           # 90 days only
    python3 scripts/backfill_derivatives.py --dry-run           # Show what would be inserted without writing
    python3 scripts/backfill_derivatives.py --debug             # Print API response details
"""

import argparse
import json
import sqlite3
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.fetchers.coinglass_fetcher import cg_get, _ensure_pair_format

DB_PATH = PROJECT_ROOT / "data" / "titan_intelligence.db"
DELAY = 2  # seconds between API calls


# ============================================================================
# Helpers
# ============================================================================

def ts_to_date(ts_ms) -> str:
    """Convert millisecond timestamp to YYYY-MM-DD string."""
    return datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def date_to_iso(date_str: str) -> str:
    """Convert YYYY-MM-DD to ISO timestamp at midnight UTC."""
    return f"{date_str}T00:00:00+00:00"


def safe_float(val, default=None):
    """Safely convert to float."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


# ============================================================================
# Data Fetching
# ============================================================================

def fetch_all_series(symbol: str, days: int, debug: bool = False) -> dict:
    """
    Fetch all historical data series for a symbol.
    Returns dict of {endpoint_name: raw_data_list}.
    """
    pair = _ensure_pair_format(symbol)
    results = {}
    api_calls = 0

    # 1. OI History (coin symbol)
    print(f"  Fetching OI history...", end=" ", flush=True)
    data = cg_get("/api/futures/open-interest/aggregated-history",
                  {"symbol": symbol.upper(), "interval": "1d", "limit": str(days)},
                  debug=debug)
    api_calls += 1
    results["oi_history"] = data or []
    print(f"{'✓' if data else '✗'} ({len(data or [])} items)")
    time.sleep(DELAY)

    # 2. Global L/S Ratio (pair format + exchange)
    print(f"  Fetching Global L/S ratio...", end=" ", flush=True)
    data = cg_get("/api/futures/global-long-short-account-ratio/history",
                  {"symbol": pair, "exchange": "Binance",
                   "interval": "1d", "limit": str(days)},
                  debug=debug)
    api_calls += 1
    results["global_ls"] = data or []
    print(f"{'✓' if data else '✗'} ({len(data or [])} items)")
    time.sleep(DELAY)

    # 3. Top L/S Account Ratio (pair format + exchange)
    print(f"  Fetching Top L/S Account ratio...", end=" ", flush=True)
    data = cg_get("/api/futures/top-long-short-account-ratio/history",
                  {"symbol": pair, "exchange": "Binance",
                   "interval": "1d", "limit": str(days)},
                  debug=debug)
    api_calls += 1
    results["top_ls_account"] = data or []
    print(f"{'✓' if data else '✗'} ({len(data or [])} items)")
    time.sleep(DELAY)

    # 4. Top L/S Position Ratio (pair format + exchange)
    print(f"  Fetching Top L/S Position ratio...", end=" ", flush=True)
    data = cg_get("/api/futures/top-long-short-position-ratio/history",
                  {"symbol": pair, "exchange": "Binance",
                   "interval": "1d", "limit": str(days)},
                  debug=debug)
    api_calls += 1
    results["top_ls_position"] = data or []
    print(f"{'✓' if data else '✗'} ({len(data or [])} items)")
    time.sleep(DELAY)

    # 5. Coinbase Premium (no symbol needed)
    print(f"  Fetching Coinbase Premium...", end=" ", flush=True)
    data = cg_get("/api/coinbase-premium-index",
                  {"interval": "1d", "limit": str(days)},
                  debug=debug)
    api_calls += 1
    results["coinbase_premium"] = data or []
    print(f"{'✓' if data else '✗'} ({len(data or [])} items)")
    time.sleep(DELAY)

    # 6. Funding Rate History (pair format + exchange)
    print(f"  Fetching Funding Rate history...", end=" ", flush=True)
    data = cg_get("/api/futures/funding-rate/history",
                  {"symbol": pair, "exchange": "Binance",
                   "interval": "1d", "limit": str(days)},
                  debug=debug)
    api_calls += 1
    results["funding_history"] = data or []
    print(f"{'✓' if data else '✗'} ({len(data or [])} items)")
    time.sleep(DELAY)

    # 7. Liquidation Aggregated History (coin symbol + exchange_list)
    print(f"  Fetching Liquidation history...", end=" ", flush=True)
    data = cg_get("/api/futures/liquidation/aggregated-history",
                  {"symbol": symbol.upper(), "exchange_list": "Binance",
                   "interval": "1d", "limit": str(days)},
                  debug=debug)
    api_calls += 1
    results["liq_history"] = data or []
    print(f"{'✓' if data else '✗'} ({len(data or [])} items)")
    time.sleep(DELAY)

    print(f"  API calls: {api_calls}")
    return results


def fetch_market_series(days: int, debug: bool = False) -> dict:
    """
    Fetch market-level data (ETF flows, Fear & Greed).
    These are fetched once and applied to both BTC and ETH rows.
    """
    results = {}

    # ETF flows (returns full history, we filter later)
    print(f"  Fetching BTC ETF flows...", end=" ", flush=True)
    data = cg_get("/api/etf/bitcoin/flow-history", debug=debug)
    results["etf_flows"] = data or []
    print(f"{'✓' if data else '✗'} ({len(data or [])} items)")
    time.sleep(DELAY)

    # Fear & Greed (returns parallel arrays)
    print(f"  Fetching Fear & Greed index...", end=" ", flush=True)
    data = cg_get("/api/index/fear-greed-history", debug=debug)
    results["fear_greed"] = data or {}
    print(f"{'✓' if data else '✗'}")
    time.sleep(DELAY)

    return results


# ============================================================================
# Data Assembly
# ============================================================================

def build_daily_data(symbol: str, token_series: dict, market_series: dict,
                     days: int) -> dict:
    """
    Join all time-series data by date into a unified dict.
    Returns {date_str: {column: value, ...}}.
    """
    daily = {}

    # --- OI History ---
    oi_data = token_series.get("oi_history", [])
    prev_oi = None
    for item in oi_data:
        if not isinstance(item, dict):
            continue
        date_str = ts_to_date(item["time"])
        daily.setdefault(date_str, {})
        oi_close = safe_float(item.get("close"), 0)
        daily[date_str]["oi_usd"] = oi_close
        # Compute day-over-day OI change
        if prev_oi and prev_oi > 0:
            daily[date_str]["oi_change_24h_pct"] = round(
                (oi_close - prev_oi) / prev_oi * 100, 2)
        prev_oi = oi_close

    # --- Global L/S Ratio ---
    for item in token_series.get("global_ls", []):
        if not isinstance(item, dict):
            continue
        date_str = ts_to_date(item["time"])
        daily.setdefault(date_str, {})
        ratio = safe_float(item.get("global_account_long_short_ratio"), 1.0)
        long_pct = safe_float(item.get("global_account_long_percent"), 50.0)
        daily[date_str]["ls_global_ratio"] = round(ratio, 4)
        daily[date_str]["ls_global_long_pct"] = round(long_pct, 2)
        # Extreme / contrarian
        daily[date_str]["ls_extreme"] = 1 if (ratio > 2.5 or ratio < 0.4) else 0
        if ratio > 2.5:
            daily[date_str]["ls_contrarian_signal"] = "short"
        elif ratio < 0.4:
            daily[date_str]["ls_contrarian_signal"] = "long"

    # --- Top L/S Account Ratio ---
    for item in token_series.get("top_ls_account", []):
        if not isinstance(item, dict):
            continue
        date_str = ts_to_date(item["time"])
        daily.setdefault(date_str, {})
        daily[date_str]["ls_top_account_ratio"] = round(
            safe_float(item.get("top_account_long_short_ratio"), 1.0), 4)

    # --- Top L/S Position Ratio ---
    for item in token_series.get("top_ls_position", []):
        if not isinstance(item, dict):
            continue
        date_str = ts_to_date(item["time"])
        daily.setdefault(date_str, {})
        pos_ratio = safe_float(item.get("top_position_long_short_ratio"), 1.0)
        daily[date_str]["ls_top_position_ratio"] = round(pos_ratio, 4)
        # Smart money lean
        if pos_ratio > 1.15:
            daily[date_str]["ls_smart_money_lean"] = "long"
        elif pos_ratio < 0.85:
            daily[date_str]["ls_smart_money_lean"] = "short"
        else:
            daily[date_str]["ls_smart_money_lean"] = "neutral"

    # --- Coinbase Premium ---
    for item in token_series.get("coinbase_premium", []):
        if not isinstance(item, dict):
            continue
        # Coinbase premium timestamps may be seconds or ms
        ts = item.get("time", 0)
        if ts > 1e12:
            ts = ts / 1000
        date_str = datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")
        daily.setdefault(date_str, {})
        rate = safe_float(item.get("premium_rate"), 0)
        daily[date_str]["coinbase_premium_rate"] = round(rate, 6)
        if rate > 0.0005:
            daily[date_str]["coinbase_premium_bias"] = "us_buying"
        elif rate < -0.0005:
            daily[date_str]["coinbase_premium_bias"] = "us_selling"
        else:
            daily[date_str]["coinbase_premium_bias"] = "neutral"

    # --- Funding Rate History ---
    funding_data = token_series.get("funding_history", [])
    if funding_data:
        for item in funding_data:
            if not isinstance(item, dict):
                continue
            date_str = ts_to_date(item["time"])
            daily.setdefault(date_str, {})
            # OHLC format — use close value (percentage as decimal, e.g. 0.001 = 0.1%)
            fr_close = safe_float(item.get("close"), 0)
            daily[date_str]["funding_rate_avg"] = round(fr_close / 100, 8)  # Convert from pct to rate
            # Determine bias using same thresholds as live fetcher
            rate = fr_close / 100
            if rate > 0.0003:
                daily[date_str]["funding_bias"] = "long_crowded"
            elif rate > 0.0001:
                daily[date_str]["funding_bias"] = "moderately_long"
            elif rate < -0.0003:
                daily[date_str]["funding_bias"] = "short_crowded"
            elif rate < -0.0001:
                daily[date_str]["funding_bias"] = "moderately_short"
            else:
                daily[date_str]["funding_bias"] = "neutral"

    # --- Liquidation History ---
    liq_data = token_series.get("liq_history", [])
    if liq_data:
        for item in liq_data:
            if not isinstance(item, dict):
                continue
            date_str = ts_to_date(item["time"])
            daily.setdefault(date_str, {})
            long_liq = safe_float(item.get("aggregated_long_liquidation_usd"), 0)
            short_liq = safe_float(item.get("aggregated_short_liquidation_usd"), 0)
            total_liq = long_liq + short_liq
            daily[date_str]["liq_24h_usd"] = round(total_liq, 2)
            daily[date_str]["liq_long_24h_usd"] = round(long_liq, 2)
            daily[date_str]["liq_short_24h_usd"] = round(short_liq, 2)
            ls_ratio = long_liq / short_liq if short_liq > 0 else (99.0 if long_liq > 0 else 1.0)
            daily[date_str]["liq_ls_ratio"] = round(ls_ratio, 2)
            if ls_ratio > 2.0:
                daily[date_str]["liq_bias"] = "long_pain"
            elif ls_ratio < 0.5:
                daily[date_str]["liq_bias"] = "short_pain"
            else:
                daily[date_str]["liq_bias"] = "balanced"

    # --- ETF Flows (BTC only but applied to both symbols) ---
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    etf_data = market_series.get("etf_flows", [])
    # Build sorted list for streak/weekly calculations
    etf_by_date = {}
    for item in etf_data:
        if not isinstance(item, dict):
            continue
        ts = item.get("timestamp", 0)
        date_str = ts_to_date(ts)
        if date_str < cutoff_date:
            continue
        flow = safe_float(item.get("flow_usd"), 0)
        etf_by_date[date_str] = flow

    # Sort dates for streak + weekly calc
    sorted_etf_dates = sorted(etf_by_date.keys())
    for i, date_str in enumerate(sorted_etf_dates):
        daily.setdefault(date_str, {})
        flow = etf_by_date[date_str]
        daily[date_str]["etf_latest_day_flow_usd"] = round(flow, 2)

        # Weekly net: sum of this day and previous 6
        start_idx = max(0, i - 6)
        weekly_dates = sorted_etf_dates[start_idx:i + 1]
        weekly_net = sum(etf_by_date.get(d, 0) for d in weekly_dates)
        daily[date_str]["etf_weekly_net_flow_usd"] = round(weekly_net, 2)

        # Streak: count consecutive same-sign days ending at current date
        streak = 0
        sign = 1 if flow >= 0 else -1
        for j in range(i, -1, -1):
            d = sorted_etf_dates[j]
            f = etf_by_date.get(d, 0)
            if (f >= 0 and sign > 0) or (f < 0 and sign < 0):
                streak += 1
            else:
                break
        daily[date_str]["etf_streak_days"] = streak * sign

        # ETF bias
        if weekly_net > 500_000_000:
            daily[date_str]["etf_bias"] = "strong_inflow"
        elif weekly_net > 100_000_000:
            daily[date_str]["etf_bias"] = "moderate_inflow"
        elif weekly_net < -500_000_000:
            daily[date_str]["etf_bias"] = "strong_outflow"
        elif weekly_net < -100_000_000:
            daily[date_str]["etf_bias"] = "moderate_outflow"
        else:
            daily[date_str]["etf_bias"] = "mixed"

    # --- Fear & Greed ---
    fg_raw = market_series.get("fear_greed", {})
    if isinstance(fg_raw, dict):
        data_list = fg_raw.get("data_list", [])
        time_list = fg_raw.get("time_list", [])
        if data_list and time_list and len(data_list) == len(time_list):
            for i, ts in enumerate(time_list):
                date_str = ts_to_date(ts)
                if date_str < cutoff_date:
                    continue
                daily.setdefault(date_str, {})
                val = int(float(data_list[i]))
                daily[date_str]["fear_greed_value"] = val
                if val <= 20:
                    daily[date_str]["fear_greed_label"] = "Extreme Fear"
                elif val <= 40:
                    daily[date_str]["fear_greed_label"] = "Fear"
                elif val <= 60:
                    daily[date_str]["fear_greed_label"] = "Neutral"
                elif val <= 80:
                    daily[date_str]["fear_greed_label"] = "Greed"
                else:
                    daily[date_str]["fear_greed_label"] = "Extreme Greed"

    return daily


# ============================================================================
# Database Insert
# ============================================================================

def insert_rows(symbol: str, daily_data: dict, dry_run: bool = False) -> int:
    """Insert backfill rows into derivatives_snapshots. Returns count inserted."""
    if dry_run:
        # Count dates that have at least OI data
        count = sum(1 for d in daily_data.values() if "oi_usd" in d)
        return count

    conn = sqlite3.connect(str(DB_PATH))

    # Get existing backfill dates for this symbol to avoid duplicates
    existing = set()
    for row in conn.execute(
        "SELECT timestamp_utc FROM derivatives_snapshots WHERE symbol = ? AND source = 'backfill'",
        (symbol.upper(),)
    ).fetchall():
        # Extract date from ISO timestamp
        existing.add(row[0][:10])

    inserted = 0
    skipped = 0
    for date_str in sorted(daily_data.keys()):
        row = daily_data[date_str]
        # Only insert if we have OI data (most reliable anchor)
        if "oi_usd" not in row:
            continue
        # Skip if already exists
        if date_str in existing:
            skipped += 1
            continue

        conn.execute("""
            INSERT INTO derivatives_snapshots (
                timestamp_utc, symbol, source, price_usd,
                funding_rate_avg, funding_bias,
                oi_usd, oi_change_24h_pct,
                ls_global_ratio, ls_global_long_pct,
                ls_top_account_ratio, ls_top_position_ratio,
                ls_smart_money_lean, ls_extreme, ls_contrarian_signal,
                liq_24h_usd, liq_long_24h_usd, liq_short_24h_usd,
                liq_ls_ratio, liq_bias,
                fear_greed_value, fear_greed_label,
                coinbase_premium_rate, coinbase_premium_bias,
                etf_latest_day_flow_usd, etf_weekly_net_flow_usd,
                etf_streak_days, etf_bias
            ) VALUES (
                ?, ?, 'backfill', NULL,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?
            )
        """, (
            date_to_iso(date_str), symbol.upper(),
            row.get("funding_rate_avg"), row.get("funding_bias"),
            row.get("oi_usd"), row.get("oi_change_24h_pct"),
            row.get("ls_global_ratio"), row.get("ls_global_long_pct"),
            row.get("ls_top_account_ratio"), row.get("ls_top_position_ratio"),
            row.get("ls_smart_money_lean"), row.get("ls_extreme", 0),
            row.get("ls_contrarian_signal"),
            row.get("liq_24h_usd"), row.get("liq_long_24h_usd"),
            row.get("liq_short_24h_usd"), row.get("liq_ls_ratio"),
            row.get("liq_bias"),
            row.get("fear_greed_value"), row.get("fear_greed_label"),
            row.get("coinbase_premium_rate"), row.get("coinbase_premium_bias"),
            row.get("etf_latest_day_flow_usd"), row.get("etf_weekly_net_flow_usd"),
            row.get("etf_streak_days"), row.get("etf_bias"),
        ))
        inserted += 1

    conn.commit()
    conn.close()

    if skipped:
        print(f"  Skipped {skipped} existing rows")
    return inserted


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Derivatives Historical Backfill")
    parser.add_argument("--symbols", type=str, default="BTC,ETH",
                        help="Comma-separated symbols (default: BTC,ETH)")
    parser.add_argument("--days", type=int, default=180,
                        help="Number of days to backfill (default: 180)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be inserted without writing")
    parser.add_argument("--debug", action="store_true",
                        help="Print raw API responses")
    args = parser.parse_args()

    symbols = [s.strip().upper() for s in args.symbols.split(",")]

    print("=" * 65)
    print(f"  Derivatives Historical Backfill")
    print(f"  Symbols: {', '.join(symbols)} | Days: {args.days}")
    if args.dry_run:
        print(f"  Mode: DRY RUN (no database writes)")
    print("=" * 65)

    # Check existing data
    if DB_PATH.exists():
        conn = sqlite3.connect(str(DB_PATH))
        for sym in symbols:
            cnt = conn.execute(
                "SELECT COUNT(*) FROM derivatives_snapshots WHERE symbol = ? AND source = 'backfill'",
                (sym,)
            ).fetchone()[0]
            if cnt > 0:
                min_dt = conn.execute(
                    "SELECT MIN(timestamp_utc) FROM derivatives_snapshots WHERE symbol = ? AND source = 'backfill'",
                    (sym,)
                ).fetchone()[0]
                max_dt = conn.execute(
                    "SELECT MAX(timestamp_utc) FROM derivatives_snapshots WHERE symbol = ? AND source = 'backfill'",
                    (sym,)
                ).fetchone()[0]
                print(f"\n  ⚠️  {sym} already has {cnt} backfill rows ({min_dt[:10]} to {max_dt[:10]})")
                print(f"  New rows will be added for missing dates only.")
        conn.close()

    # Fetch market-level data once
    print(f"\n{'─' * 65}")
    print(f"  Fetching market-level data...")
    print(f"{'─' * 65}")
    market_series = fetch_market_series(args.days, debug=args.debug)

    # Track coverage
    coverage = {
        "oi_history": {}, "global_ls": {}, "top_ls_account": {},
        "top_ls_position": {}, "coinbase_premium": {},
        "funding_history": {}, "liq_history": {},
        "etf_flows": len(market_series.get("etf_flows", [])),
        "fear_greed": bool(market_series.get("fear_greed", {}).get("data_list")),
    }

    results = {}
    for sym in symbols:
        print(f"\n{'─' * 65}")
        print(f"  Fetching {sym} data ({args.days} days)...")
        print(f"{'─' * 65}")

        token_series = fetch_all_series(sym, args.days, debug=args.debug)

        # Track coverage per symbol
        for key in ["oi_history", "global_ls", "top_ls_account",
                     "top_ls_position", "coinbase_premium",
                     "funding_history", "liq_history"]:
            coverage[key][sym] = len(token_series.get(key, []))

        print(f"\n  Assembling daily data for {sym}...")
        daily_data = build_daily_data(sym, token_series, market_series, args.days)
        dates_with_oi = sum(1 for d in daily_data.values() if "oi_usd" in d)
        print(f"  {len(daily_data)} dates assembled, {dates_with_oi} with OI anchor")

        if daily_data:
            sorted_dates = sorted(d for d in daily_data.keys() if "oi_usd" in daily_data[d])
            if sorted_dates:
                print(f"  Range: {sorted_dates[0]} to {sorted_dates[-1]}")

        print(f"\n  {'[DRY RUN] Would insert' if args.dry_run else 'Inserting'} rows for {sym}...")
        count = insert_rows(sym, daily_data, dry_run=args.dry_run)
        results[sym] = count
        print(f"  {'Would insert' if args.dry_run else 'Inserted'}: {count} rows")

    # Report
    print(f"\n{'=' * 65}")
    print(f"  {'DRY RUN SUMMARY' if args.dry_run else 'BACKFILL COMPLETE'}")
    print(f"{'=' * 65}")

    for sym, count in results.items():
        print(f"  {sym}: {count} rows {'(would be inserted)' if args.dry_run else 'inserted'}")

    print(f"\n  Data coverage:")
    for key in ["oi_history", "global_ls", "top_ls_account",
                 "top_ls_position", "coinbase_premium",
                 "funding_history", "liq_history"]:
        sym_counts = coverage[key]
        if isinstance(sym_counts, dict):
            parts = " + ".join(f"{s}: {c}" for s, c in sym_counts.items())
            all_ok = all(c > 0 for c in sym_counts.values())
            emoji = "✅" if all_ok else "❌"
            label = key.replace("_", " ").title()
            print(f"    {emoji} {label:<22} {parts}")
    # ETF
    etf_count = coverage["etf_flows"]
    print(f"    {'✅' if etf_count > 0 else '❌'} {'ETF Flows':<22} {etf_count} days (BTC only, applied to both)")
    # F&G
    fg_ok = coverage["fear_greed"]
    print(f"    {'✅' if fg_ok else '❌'} {'Fear & Greed':<22} {'full history' if fg_ok else 'NOT AVAILABLE'}")

    if not args.dry_run:
        print(f"\n  Verify:")
        for sym in symbols:
            print(f"    python3 src/storage/intelligence.py derivatives-stats --symbol {sym} --days {args.days}")


if __name__ == "__main__":
    main()
