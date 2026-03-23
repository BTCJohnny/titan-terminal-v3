#!/usr/bin/env python3
"""
Titan Terminal v3 — Auto Signal Bridge
========================================
Connects the graduated strategy signal checker to the paper trading engine.
Runs hourly: checks which strategies are firing, applies portfolio constraints,
and creates PENDING setups for the paper engine to execute.

Usage:
    python3 src/trading/auto_signal_bridge.py run              # Run bridge, create setups
    python3 src/trading/auto_signal_bridge.py run --dry-run    # Show what would be created, don't write
    python3 src/trading/auto_signal_bridge.py run --cron       # Compact output for cron
    python3 src/trading/auto_signal_bridge.py status           # Show current bridge state
    python3 src/trading/auto_signal_bridge.py expire           # Manually expire stale PENDING setups
"""

# TODO: signal_checker.py currently loads only 4h candles for all strategies.
# This means 1h strategies are evaluated against 4h indicator values, which
# may cause slight entry timing differences vs backtested results.
# Future enhancement: modify check_graduated_strategies() to load candles
# at the strategy's native timeframe (1h or 4h).

import argparse
import json
import sqlite3
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.backtesting.signal_checker import check_graduated_strategies
from src.storage.intelligence import get_connection

# ============================================================================
# CONSTANTS
# ============================================================================

MAX_POSITIONS = 5
CASH_FLOOR_PCT = 0.30
MAX_DIRECTIONAL = 3
RISK_PER_TRADE_PCT = 2.0
SETUP_EXPIRY_HOURS = 24
DEDUP_HOURS = 4

REPORTS_DIR = PROJECT_ROOT / "signals" / "dashboards"


# ============================================================================
# PORTFOLIO STATE
# ============================================================================

def get_portfolio_state() -> dict | None:
    """Read current paper portfolio: cash, open positions, pending setups."""
    conn = get_connection()

    portfolio = conn.execute(
        "SELECT current_cash, starting_balance FROM paper_portfolio WHERE is_active = 1 LIMIT 1"
    ).fetchone()

    if not portfolio:
        conn.close()
        return None

    cash = portfolio[0]
    starting = portfolio[1]

    open_positions = conn.execute(
        "SELECT token, direction, remaining_units, entry_price FROM paper_positions WHERE status = 'OPEN'"
    ).fetchall()

    pending_setups = conn.execute(
        "SELECT token, direction, setup_id FROM trade_setups WHERE status = 'PENDING'"
    ).fetchall()

    # Equity = cash + open positions valued at entry price (approximation)
    positions_value = sum(row[2] * row[3] for row in open_positions)
    equity = cash + positions_value

    conn.close()

    return {
        "cash": cash,
        "equity": equity,
        "starting_balance": starting,
        "open_positions": [{"token": r[0], "direction": r[1]} for r in open_positions],
        "pending_setups": [{"token": r[0], "direction": r[1], "setup_id": r[2]} for r in pending_setups],
    }


# ============================================================================
# PORTFOLIO CONSTRAINT CHECK
# ============================================================================

def can_enter(state: dict, symbol: str, direction: str, position_size_usd: float) -> tuple[bool, str]:
    """Check if portfolio can accept a new setup. Returns (ok, reason)."""
    open_symbols = {p["token"] for p in state["open_positions"]}
    pending_symbols = {p["token"] for p in state["pending_setups"]}

    if symbol in open_symbols:
        return False, "symbol_has_position"
    if symbol in pending_symbols:
        return False, "symbol_has_pending"

    total_active = len(state["open_positions"]) + len(state["pending_setups"])
    if total_active >= MAX_POSITIONS:
        return False, "max_positions"

    same_dir_count = (
        sum(1 for p in state["open_positions"] if p["direction"] == direction)
        + sum(1 for p in state["pending_setups"] if p["direction"] == direction)
    )
    if same_dir_count >= MAX_DIRECTIONAL:
        return False, "max_directional"

    required_floor = state["equity"] * CASH_FLOOR_PCT
    if state["cash"] - position_size_usd < required_floor:
        return False, "cash_floor"

    return True, "ok"


# ============================================================================
# DEDUPLICATION
# ============================================================================

def check_dedup(symbol: str, strategy_name: str) -> bool:
    """Return True if this strategy+symbol was already created within DEDUP_HOURS."""
    conn = get_connection()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=DEDUP_HOURS)).isoformat()
    row = conn.execute(
        "SELECT COUNT(*) FROM trade_setups WHERE token = ? AND skill_name = ? AND timestamp_utc > ?",
        (symbol.upper(), strategy_name, cutoff),
    ).fetchone()
    conn.close()
    return row[0] > 0


# ============================================================================
# EXPIRY
# ============================================================================

def expire_stale_setups() -> int:
    """Mark PENDING setups older than SETUP_EXPIRY_HOURS as EXPIRED. Returns count expired."""
    conn = get_connection()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=SETUP_EXPIRY_HOURS)).isoformat()
    cursor = conn.execute(
        "UPDATE trade_setups SET status = 'EXPIRED' WHERE status = 'PENDING' AND timestamp_utc < ?",
        (cutoff,),
    )
    expired = cursor.rowcount
    conn.commit()
    conn.close()
    return expired


# ============================================================================
# SETUP CREATION
# ============================================================================

def create_setup(signal: dict) -> str:
    """Create a PENDING setup from a firing signal. Returns setup_id."""
    setup_id = (
        f"auto_{signal['symbol'].upper()}_"
        f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}_"
        f"{uuid.uuid4().hex[:6]}"
    )
    now = datetime.now(timezone.utc).isoformat()

    notes = json.dumps({
        "source": "auto_signal_bridge",
        "backtest_pf": signal.get("backtest_pf"),
        "backtest_wr": signal.get("backtest_wr"),
        "backtest_trades": signal.get("backtest_trades"),
        "derivatives_age_hours": signal.get("derivatives_age_hours"),
    })

    conn = get_connection()
    conn.execute(
        """INSERT INTO trade_setups
           (setup_id, timestamp_utc, token, direction,
            entry_price, stop_loss, target_1, target_2,
            position_size_usd, status, skill_name, pattern_type, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, ?, ?)""",
        (
            setup_id,
            now,
            signal["symbol"].upper(),
            signal["direction"],
            signal.get("suggested_entry"),
            signal.get("suggested_stop"),
            signal.get("suggested_t1"),
            signal.get("suggested_t2"),
            signal.get("position_size_usd"),
            signal["strategy_name"],
            "auto_signal_bridge",
            notes,
        ),
    )
    conn.commit()
    conn.close()
    return setup_id


# ============================================================================
# MAIN BRIDGE LOGIC
# ============================================================================

def run_bridge(dry_run: bool = False) -> dict:
    """
    Main bridge function. Returns summary dict.

    1. Expire stale PENDING setups
    2. Check graduated strategies for firing signals
    3. Apply portfolio constraints
    4. Create PENDING setups (or report in dry-run mode)
    """
    now = datetime.now(timezone.utc)
    summary = {
        "timestamp": now.isoformat(),
        "expired": 0,
        "signals_checked": 0,
        "signals_firing": 0,
        "setups_created": [],
        "rejections": [],
        "errors": [],
    }

    # Step 1: Expire stale setups
    if not dry_run:
        summary["expired"] = expire_stale_setups()

    # Step 2: Check graduated strategies
    try:
        results = check_graduated_strategies()
    except Exception as e:
        summary["errors"].append(f"Signal checker failed: {str(e)[:200]}")
        return summary

    summary["signals_checked"] = len(results)

    # Filter to firing signals that have trade levels
    firing = [r for r in results if r.get("firing") and r.get("suggested_entry")]
    summary["signals_firing"] = len(firing)

    if not firing:
        return summary

    # Step 3: Get portfolio state
    state = get_portfolio_state()
    if state is None:
        summary["errors"].append(
            "Paper portfolio not initialized. Run: python3 src/trading/paper_engine.py init"
        )
        return summary

    # Step 4: Resolve conflicts — one setup per symbol, highest PF wins
    by_symbol: dict = {}
    for sig in firing:
        sym = sig["symbol"]
        if sym not in by_symbol or sig.get("backtest_pf", 0) > by_symbol[sym].get("backtest_pf", 0):
            by_symbol[sym] = sig

    # Sort by PF descending so best strategies get priority slots
    candidates = sorted(by_symbol.values(), key=lambda s: s.get("backtest_pf", 0), reverse=True)

    # Step 5: Apply constraints and create setups
    for sig in candidates:
        sym = sig["symbol"]
        direction = sig["direction"]
        position_size = sig.get("position_size_usd", 0)
        strategy_name = sig.get("strategy_name", "Unknown")

        # Dedup check
        if check_dedup(sym, strategy_name):
            summary["rejections"].append({
                "symbol": sym,
                "strategy": strategy_name,
                "reason": "dedup_recent",
            })
            continue

        # Portfolio constraint check
        ok, reason = can_enter(state, sym, direction, position_size)
        if not ok:
            summary["rejections"].append({
                "symbol": sym,
                "strategy": strategy_name,
                "reason": reason,
            })
            continue

        # Create (or preview) the setup
        record = {
            "symbol": sym,
            "direction": direction,
            "strategy": strategy_name,
            "entry": sig.get("suggested_entry"),
            "stop": sig.get("suggested_stop"),
            "t1": sig.get("suggested_t1"),
            "t2": sig.get("suggested_t2"),
            "size_usd": position_size,
            "pf": sig.get("backtest_pf"),
        }

        if dry_run:
            record["dry_run"] = True
            summary["setups_created"].append(record)
        else:
            try:
                setup_id = create_setup(sig)
                record["setup_id"] = setup_id
                summary["setups_created"].append(record)
            except Exception as e:
                summary["errors"].append(f"Failed to create setup for {sym}: {str(e)[:100]}")
                continue

        # Update local state so subsequent candidates see accurate slot counts
        state["pending_setups"].append({"token": sym, "direction": direction, "setup_id": "pending"})
        state["cash"] = max(0.0, state["cash"] - position_size)

    return summary


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================

def format_summary(summary: dict) -> str:
    """Format bridge run summary for interactive display."""
    ts = summary["timestamp"][:19].replace("T", " ") + " UTC"
    lines = []
    lines.append("")
    lines.append("=" * 62)
    lines.append("  AUTO SIGNAL BRIDGE")
    lines.append(f"  {ts}")
    lines.append("=" * 62)

    lines.append(f"\n  Expired stale setups: {summary['expired']}")
    lines.append(
        f"  Signals checked: {summary['signals_checked']} | "
        f"Firing: {summary['signals_firing']}"
    )

    if summary["setups_created"]:
        lines.append(f"\n  SETUPS CREATED ({len(summary['setups_created'])}):")
        for s in summary["setups_created"]:
            tag = " [DRY RUN]" if s.get("dry_run") else f"  {s.get('setup_id', '')}"
            lines.append(
                f"    {s['symbol']:8s} {s['direction']:5s}  "
                f"Entry ${s['entry']:,.2f}  Stop ${s['stop']:,.2f}  "
                f"T1 ${s['t1']:,.2f}  Size ${s['size_usd']:,.0f}  "
                f"PF {s['pf']}{tag}"
            )
    else:
        lines.append("\n  No setups created.")

    if summary["rejections"]:
        lines.append(f"\n  REJECTED ({len(summary['rejections'])}):")
        for r in summary["rejections"]:
            lines.append(f"    {r['symbol']:8s}  {r['strategy'][:40]}  → {r['reason']}")

    if summary["errors"]:
        lines.append(f"\n  ERRORS ({len(summary['errors'])}):")
        for e in summary["errors"]:
            lines.append(f"    {e}")

    lines.append("\n" + "=" * 62)
    return "\n".join(lines)


def format_cron(summary: dict) -> str:
    """One-line summary for cron log."""
    ts = summary["timestamp"][:19] + "Z"
    created = len(summary["setups_created"])
    rejected = len(summary["rejections"])
    firing = summary["signals_firing"]
    errors = len(summary["errors"])
    return (
        f"[{ts}] Signals: {firing} firing | "
        f"Created: {created} | Rejected: {rejected} | "
        f"Expired: {summary['expired']} | Errors: {errors}"
    )


def save_report(summary: dict) -> Path:
    """Save detailed JSON report to signals/dashboards/."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    path = REPORTS_DIR / f"signal_bridge_{ts}.json"
    path.write_text(json.dumps(summary, indent=2))
    return path


# ============================================================================
# STATUS COMMAND
# ============================================================================

def show_status() -> str:
    """Show current bridge state: open positions, pending setups, slot availability."""
    conn = get_connection()

    portfolio = conn.execute(
        "SELECT current_cash, starting_balance FROM paper_portfolio WHERE is_active = 1 LIMIT 1"
    ).fetchone()

    if not portfolio:
        conn.close()
        return "\n  Paper portfolio not initialized.\n  Run: python3 src/trading/paper_engine.py init\n"

    cash = portfolio[0]
    starting = portfolio[1]

    open_pos = conn.execute(
        """SELECT token, direction, entry_price, remaining_units,
                  unrealized_pnl_usd, opened_at
           FROM paper_positions WHERE status = 'OPEN'
           ORDER BY opened_at ASC"""
    ).fetchall()

    pending = conn.execute(
        """SELECT token, direction, entry_price, position_size_usd,
                  timestamp_utc, setup_id
           FROM trade_setups WHERE status = 'PENDING'
           ORDER BY timestamp_utc ASC"""
    ).fetchall()

    # Last bridge run
    last_run = conn.execute(
        """SELECT timestamp_utc FROM trade_setups
           WHERE pattern_type = 'auto_signal_bridge'
           ORDER BY timestamp_utc DESC LIMIT 1"""
    ).fetchone()

    conn.close()

    positions_value = sum(r[2] * r[3] for r in open_pos)
    equity = cash + positions_value
    total_active = len(open_pos) + len(pending)
    slots_free = MAX_POSITIONS - total_active
    floor = equity * CASH_FLOOR_PCT
    cash_above_floor = cash - floor

    now = datetime.now(timezone.utc)

    lines = []
    lines.append("")
    lines.append("=" * 62)
    lines.append("  BRIDGE STATUS")
    lines.append(f"  {now.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("=" * 62)

    lines.append(f"\n  Slots: {total_active}/{MAX_POSITIONS} used  ({slots_free} free)")
    lines.append(f"  Cash:  ${cash:,.2f}  (floor ${floor:,.2f}  available ${cash_above_floor:,.2f})")
    lines.append(f"  Equity: ${equity:,.2f}")

    if last_run:
        lines.append(f"  Last bridge run: {last_run[0][:19].replace('T', ' ')} UTC")

    if open_pos:
        lines.append(f"\n  OPEN POSITIONS ({len(open_pos)}):")
        for r in open_pos:
            token, direction, entry, units, upnl, opened_at = r
            age_h = (now - datetime.fromisoformat(opened_at.replace("Z", "+00:00"))).total_seconds() / 3600
            upnl_str = f"${upnl:+,.2f}" if upnl is not None else "N/A"
            lines.append(
                f"    {token:8s} {direction:5s}  Entry ${entry:,.2f}  "
                f"Units {units:.4f}  uPnL {upnl_str}  Age {age_h:.0f}h"
            )
    else:
        lines.append("\n  No open positions.")

    if pending:
        lines.append(f"\n  PENDING SETUPS ({len(pending)}):")
        for r in pending:
            token, direction, entry, size_usd, ts_utc, setup_id = r
            ts = datetime.fromisoformat(ts_utc.replace("Z", "+00:00"))
            age_h = (now - ts).total_seconds() / 3600
            expire_h = max(0, SETUP_EXPIRY_HOURS - age_h)
            size_str = f"${size_usd:,.0f}" if size_usd is not None else "N/A"
            lines.append(
                f"    {token:8s} {direction:5s}  Entry ${entry:,.2f}  "
                f"Size {size_str}  Age {age_h:.1f}h  "
                f"(expires in {expire_h:.0f}h)"
            )
    else:
        lines.append("\n  No pending setups.")

    lines.append("\n" + "=" * 62)
    return "\n".join(lines)


# ============================================================================
# CLI
# ============================================================================

def cmd_run(args):
    dry_run = args.dry_run
    cron_mode = args.cron

    summary = run_bridge(dry_run=dry_run)

    if not cron_mode:
        print(format_summary(summary))
    else:
        print(format_cron(summary))

    if not dry_run and not cron_mode:
        report_path = save_report(summary)
        print(f"\n  Report saved: {report_path.relative_to(PROJECT_ROOT)}")
    elif not dry_run and cron_mode:
        save_report(summary)


def cmd_status(args):
    print(show_status())


def cmd_expire(args):
    expired = expire_stale_setups()
    print(f"\n  Expired {expired} stale PENDING setup(s) (>{SETUP_EXPIRY_HOURS}h old).\n")


def main():
    parser = argparse.ArgumentParser(description="Titan Auto Signal Bridge")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run bridge and create PENDING setups")
    run_parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    run_parser.add_argument("--cron", action="store_true", help="Compact one-line output for cron")
    run_parser.set_defaults(func=cmd_run)

    status_parser = subparsers.add_parser("status", help="Show current bridge state")
    status_parser.set_defaults(func=cmd_status)

    expire_parser = subparsers.add_parser("expire", help="Manually expire stale PENDING setups")
    expire_parser.set_defaults(func=cmd_expire)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
