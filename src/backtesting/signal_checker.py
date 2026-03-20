#!/usr/bin/env python3
"""
Titan Terminal v2 — Graduated Strategy Signal Checker
=====================================================
Evaluates graduated backtested strategies against current live data.
Surfaces strategies whose entry conditions are currently met.

Usage:
    python3 src/backtesting/signal_checker.py check          # Check all graduated strategies
    python3 src/backtesting/signal_checker.py check --json    # JSON output for programmatic use
    python3 src/backtesting/signal_checker.py list            # List graduated strategies
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.backtesting.engine import (
    precompute_indicators, build_context, evaluate_signals,
    load_candles, load_derivatives,
)
from src.analysis.indicators import from_timestamp_utc

# Paths
GRADUATED_DIR = PROJECT_ROOT / "results" / "backtests" / "graduated"
INTEL_DB = PROJECT_ROOT / "data" / "titan_intelligence.db"
WARMUP_BARS = 200


# ============================================================================
# LOAD GRADUATED STRATEGIES
# ============================================================================

def load_graduated_strategies() -> list:
    """Load all graduated strategy JSON files."""
    if not GRADUATED_DIR.exists():
        return []
    strategies = []
    for f in sorted(GRADUATED_DIR.glob("graduated_*.json")):
        try:
            data = json.loads(f.read_text())
            data["_file"] = f.name
            strategies.append(data)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  Warning: skipping {f.name}: {e}", file=sys.stderr)
    return strategies


# ============================================================================
# DERIVATIVES AGE CHECK
# ============================================================================

def get_derivatives_age(symbol: str) -> tuple:
    """
    Get the age of the latest derivatives snapshot for a symbol.
    Returns (age_hours: float, stale: bool, timestamp_str: str or None).
    """
    if not INTEL_DB.exists():
        return None, True, None

    try:
        conn = sqlite3.connect(INTEL_DB)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT timestamp_utc FROM derivatives_snapshots "
            "WHERE symbol = ? ORDER BY timestamp_utc DESC LIMIT 1",
            (symbol.upper(),)
        ).fetchone()
        conn.close()

        if not row:
            return None, True, None

        ts_str = row["timestamp_utc"]
        # Parse ISO timestamp
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        age_hours = (now - ts).total_seconds() / 3600
        return round(age_hours, 1), age_hours > 24, ts_str
    except Exception:
        return None, True, None


# ============================================================================
# PORTFOLIO EQUITY
# ============================================================================

def get_portfolio_equity() -> float:
    """Read current portfolio equity from paper trading. Falls back to 50000."""
    if not INTEL_DB.exists():
        return 50000.0
    try:
        conn = sqlite3.connect(INTEL_DB)
        row = conn.execute("SELECT current_cash FROM paper_portfolio LIMIT 1").fetchone()
        conn.close()
        if row and row[0]:
            return float(row[0])
    except Exception:
        pass
    return 50000.0


# ============================================================================
# CORE: CHECK GRADUATED STRATEGIES
# ============================================================================

def check_graduated_strategies() -> list:
    """
    Check all graduated strategies against current market data.

    Returns list of dicts with firing status, signal details, and suggested levels.
    """
    strategies = load_graduated_strategies()
    if not strategies:
        return []

    # Group strategies by symbol to avoid redundant data loading
    by_symbol = {}
    for s in strategies:
        sym = s.get("symbol", "").upper()
        if sym not in by_symbol:
            by_symbol[sym] = []
        by_symbol[sym].append(s)

    equity = get_portfolio_equity()
    results = []

    for symbol, strats in by_symbol.items():
        # Load OHLCV — 90 days gives ~540 4h bars, enough for SMA 200 warmup
        candles = load_candles(symbol, "4h", days=90)
        if len(candles) < WARMUP_BARS + 10:
            for s in strats:
                results.append({
                    "strategy_name": s.get("name", "Unknown"),
                    "symbol": symbol,
                    "direction": s.get("direction", "LONG"),
                    "firing": False,
                    "signals": {},
                    "error": f"Insufficient OHLCV data: {len(candles)} bars (need >{WARMUP_BARS})",
                })
            continue

        # Date range for derivatives
        start_dt = from_timestamp_utc(candles[0]["t"])
        end_dt = from_timestamp_utc(candles[-1]["t"])
        start_date = start_dt.strftime("%Y-%m-%d")
        end_date = end_dt.strftime("%Y-%m-%d")

        # Pre-compute indicators (once per symbol)
        ind = precompute_indicators(candles)

        # Load derivatives
        deriv_by_date = load_derivatives(symbol, start_date, end_date)

        # Build context for the last bar
        last_idx = len(candles) - 1
        ctx = build_context(last_idx, candles, ind, deriv_by_date)

        # Derivatives age
        deriv_age_hours, deriv_stale, deriv_ts = get_derivatives_age(symbol)

        # Current price and ATR
        current_price = candles[-1]["c"]
        atr = ctx.get("atr_14")

        # Evaluate each strategy
        for s in strats:
            entry_signals = s.get("entry_signals", [])
            entry_params = s.get("entry_params", {})
            filters = s.get("filters", {})
            exclude_signals = filters.get("exclude_signals", [])
            direction = s.get("direction", "LONG").upper()
            exit_cfg = s.get("exit", {})
            metrics = s.get("backtest_metrics", {})

            # Evaluate entry signals
            sig_results = evaluate_signals(ctx, entry_signals, entry_params)
            all_firing = all(sig_results.values()) if sig_results else False

            # Check exclusion filters
            if all_firing and exclude_signals:
                excl_results = evaluate_signals(ctx, exclude_signals, entry_params)
                if any(excl_results.values()):
                    all_firing = False

            result = {
                "strategy_name": s.get("name", "Unknown"),
                "symbol": symbol,
                "direction": direction,
                "firing": all_firing,
                "signals": sig_results,
                "current_price": current_price,
                "atr_14": atr,
                "derivatives_age_hours": deriv_age_hours,
                "derivatives_stale": deriv_stale,
                "backtest_pf": metrics.get("profit_factor", 0),
                "backtest_wr": metrics.get("win_rate", 0),
                "backtest_trades": metrics.get("total_trades", 0),
            }

            # Compute suggested trade levels if firing and ATR available
            if all_firing and atr and atr > 0:
                stop_mult = exit_cfg.get("stop_atr_mult", 2.0)
                t1_mult = exit_cfg.get("target1_atr_mult", 3.0)
                t2_mult = exit_cfg.get("target2_atr_mult", t1_mult * 2)

                if direction == "SHORT":
                    stop = current_price + (atr * stop_mult)
                    t1 = current_price - (atr * t1_mult)
                    t2 = current_price - (atr * t2_mult)
                else:
                    stop = current_price - (atr * stop_mult)
                    t1 = current_price + (atr * t1_mult)
                    t2 = current_price + (atr * t2_mult)

                # Position sizing: 2% risk
                risk_usd = equity * 0.02
                risk_per_unit = abs(current_price - stop)
                if risk_per_unit > 0:
                    units = risk_usd / risk_per_unit
                    position_size_usd = units * current_price
                else:
                    position_size_usd = 0

                result["suggested_entry"] = round(current_price, 2)
                result["suggested_stop"] = round(stop, 2)
                result["suggested_t1"] = round(t1, 2)
                result["suggested_t2"] = round(t2, 2)
                result["position_size_usd"] = round(position_size_usd, 2)
                result["equity"] = round(equity, 2)

            results.append(result)

    # Sort: firing strategies first, then by backtest profit factor descending
    results.sort(key=lambda r: (not r["firing"], -r.get("backtest_pf", 0)))
    return results


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================

def format_check_output(results: list) -> str:
    """Format signal check results as human-readable output."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = []
    lines.append("")
    lines.append("=" * 62)
    lines.append("  GRADUATED STRATEGY SIGNAL CHECK")
    lines.append(f"  {now}")
    lines.append("=" * 62)

    if not results:
        lines.append("")
        lines.append("  No graduated strategies found.")
        lines.append(f"  Directory: {GRADUATED_DIR}")
        lines.append("")
        lines.append("=" * 62)
        return "\n".join(lines)

    firing_count = sum(1 for r in results if r["firing"])

    for r in results:
        lines.append("")
        if r.get("error"):
            lines.append(f"  !! ERROR: {r['strategy_name']}")
            lines.append(f"     {r['error']}")
            continue

        if r["firing"]:
            lines.append(f"  FIRING: {r['strategy_name']}")
            lines.append(f"     Symbol: {r['symbol']} {r['direction']}")

            # Signal status
            sig_parts = []
            for name, val in r["signals"].items():
                sig_parts.append(f"{name} {'OK' if val else 'NO'}")
            lines.append(f"     Signals: {' | '.join(sig_parts)}")

            # Price and levels
            price = r.get("current_price", 0)
            atr_val = r.get("atr_14", 0)
            lines.append(f"     Price: ${price:,.2f} | ATR: ${atr_val:,.2f}" if atr_val else f"     Price: ${price:,.2f}")

            if "suggested_entry" in r:
                lines.append(
                    f"     Levels: Entry ${r['suggested_entry']:,.2f} | "
                    f"Stop ${r['suggested_stop']:,.2f} | "
                    f"T1 ${r['suggested_t1']:,.2f} | "
                    f"T2 ${r['suggested_t2']:,.2f}"
                )
                lines.append(
                    f"     Size: ${r['position_size_usd']:,.0f} "
                    f"(2% risk on ${r['equity']:,.0f})"
                )

            lines.append(
                f"     Backtest: PF {r['backtest_pf']} | "
                f"WR {r['backtest_wr']*100:.0f}% | "
                f"{r['backtest_trades']} trades"
            )

            # Derivatives age
            if r.get("derivatives_age_hours") is not None:
                age = r["derivatives_age_hours"]
                stale_flag = " (STALE)" if r["derivatives_stale"] else ""
                lines.append(f"     Derivatives: {age:.1f}h old{stale_flag}")

        else:
            lines.append(f"  NOT FIRING: {r['strategy_name']}")
            lines.append(f"     Symbol: {r['symbol']} {r['direction']}")

            # Signal status — show which are missing
            sig_parts = []
            for name, val in r["signals"].items():
                sig_parts.append(f"{name} {'OK' if val else 'NO'}")
            lines.append(f"     Signals: {' | '.join(sig_parts)}")

            if r.get("derivatives_age_hours") is not None:
                age = r["derivatives_age_hours"]
                stale_flag = " (STALE)" if r["derivatives_stale"] else ""
                lines.append(f"     Derivatives: {age:.1f}h old{stale_flag}")

    lines.append("")
    lines.append("=" * 62)
    lines.append(f"  Summary: {firing_count} firing / {len(results)} graduated strategies")
    if firing_count > 0:
        firing_names = [r["strategy_name"] for r in results if r["firing"]]
        lines.append(f"  Action needed: Review {', '.join(firing_names)}")
    lines.append("=" * 62)
    lines.append("")

    return "\n".join(lines)


def format_list_output(strategies: list) -> str:
    """Format graduated strategy list."""
    if not strategies:
        return "  No graduated strategies found.\n"

    lines = []
    lines.append(f"  Graduated Strategies ({len(strategies)}):")
    for s in strategies:
        name = s.get("name", "Unknown")
        symbol = s.get("symbol", "?")
        direction = s.get("direction", "?")
        metrics = s.get("backtest_metrics", {})
        pf = metrics.get("profit_factor", 0)
        wr = metrics.get("win_rate", 0)
        trades = metrics.get("total_trades", 0)
        lines.append(
            f"    {symbol:5s}  {direction:5s}  {name:55s}  "
            f"PF {pf:<5}  WR {wr*100:.0f}%  {trades} trades"
        )
    lines.append("")
    return "\n".join(lines)


# ============================================================================
# CLI
# ============================================================================

def cmd_check(args):
    """Check graduated strategies against live data."""
    results = check_graduated_strategies()
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_check_output(results))


def cmd_list(args):
    """List graduated strategies."""
    strategies = load_graduated_strategies()
    print(format_list_output(strategies))


def main():
    parser = argparse.ArgumentParser(description="Titan Graduated Strategy Signal Checker")
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Check strategies against live data")
    check_parser.add_argument("--json", action="store_true", help="Output JSON")
    check_parser.set_defaults(func=cmd_check)

    list_parser = subparsers.add_parser("list", help="List graduated strategies")
    list_parser.set_defaults(func=cmd_list)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
