#!/usr/bin/env python3
"""
Paper Trading Performance Analytics
====================================
Queries paper_positions and equity_snapshots to compute strategy
performance metrics. Pure computation — Claude interprets the results.

Uses: data/titan_intelligence.db (same DB as paper_engine.py)

Usage:
    python3 src/trading/analytics.py summary                 # Full performance report
    python3 src/trading/analytics.py summary --days 30       # Last 30 days
    python3 src/trading/analytics.py by-strategy             # Breakdown by setup type
    python3 src/trading/analytics.py by-direction            # LONG vs SHORT
    python3 src/trading/analytics.py equity-curve --days 30  # Equity data points
    python3 src/trading/analytics.py equity-curve --csv      # Export as CSV
    python3 src/trading/analytics.py recent-trades           # Last 20 closed trades
    python3 src/trading/analytics.py recent-trades --limit 50
"""

import argparse
import csv
import io
import json
import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.storage.intelligence import get_connection
from src.trading.paper_engine import init_paper_tables, get_portfolio


# ============================================================================
# HELPERS
# ============================================================================

def _safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Division that returns default on zero denominator."""
    if denominator == 0:
        return default
    return numerator / denominator


def _round2(val: Optional[float]) -> Optional[float]:
    """Round to 2 decimals, None-safe."""
    if val is None:
        return None
    return round(val, 2)


def _get_closed_positions(conn: sqlite3.Connection, days: int = 90) -> List[Dict]:
    """Get closed paper positions within the time window."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows = conn.execute(
        """SELECT pp.*, ts.pattern_type, ts.direction as setup_direction
           FROM paper_positions pp
           LEFT JOIN trade_setups ts ON pp.setup_id = ts.setup_id
           WHERE pp.status = 'CLOSED' AND pp.closed_at >= ?
           ORDER BY pp.closed_at DESC""",
        (cutoff,)
    ).fetchall()
    return [dict(r) for r in rows]


def _holding_hours(opened_at: str, closed_at: Optional[str]) -> float:
    """Calculate holding time in hours."""
    if not closed_at:
        return 0.0
    try:
        opened = datetime.fromisoformat(opened_at.replace("Z", "+00:00"))
        closed = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
        return (closed - opened).total_seconds() / 3600
    except (ValueError, TypeError):
        return 0.0


def _calculate_r_achieved(pos: Dict) -> Optional[float]:
    """Calculate R-multiple achieved for a closed position."""
    entry = pos["entry_price"]
    stop = pos["original_stop"]
    risk_per_unit = abs(entry - stop)
    if risk_per_unit <= 0:
        return None
    pnl_per_unit = _safe_div(pos["realized_pnl_usd"], pos["total_units"], 0.0)
    return round(pnl_per_unit / risk_per_unit, 2)


# ============================================================================
# PERFORMANCE SUMMARY
# ============================================================================

def get_performance_summary(days: int = 90) -> Dict:
    """Compute full performance metrics over the given window."""
    conn = get_connection()
    init_paper_tables(conn)

    portfolio = get_portfolio(conn)
    if not portfolio:
        conn.close()
        return {"error": "No paper portfolio initialized"}

    starting = portfolio["starting_balance"]

    # Current equity from latest snapshot
    latest_snap = conn.execute(
        "SELECT * FROM equity_snapshots ORDER BY timestamp_utc DESC LIMIT 1"
    ).fetchone()
    current_equity = dict(latest_snap)["total_equity"] if latest_snap else starting

    # Closed positions in window
    positions = _get_closed_positions(conn, days)

    # Split wins/losses/partials
    wins = [p for p in positions if p["realized_pnl_usd"] > 0]
    losses = [p for p in positions if p["realized_pnl_usd"] < 0]
    partials = [p for p in positions if p["realized_pnl_usd"] == 0]

    total_trades = len(positions)
    win_count = len(wins)
    loss_count = len(losses)
    partial_count = len(partials)
    win_rate = _safe_div(win_count, total_trades)

    # P&L stats
    gross_profit = sum(p["realized_pnl_usd"] for p in wins)
    gross_loss = sum(p["realized_pnl_usd"] for p in losses)
    profit_factor = _safe_div(gross_profit, abs(gross_loss))

    avg_win_usd = _safe_div(gross_profit, win_count)
    avg_loss_usd = _safe_div(gross_loss, loss_count)

    # Percentage P&L
    win_pcts = []
    for p in wins:
        if p["position_value_usd"] > 0:
            win_pcts.append(p["realized_pnl_usd"] / p["position_value_usd"] * 100)
    loss_pcts = []
    for p in losses:
        if p["position_value_usd"] > 0:
            loss_pcts.append(p["realized_pnl_usd"] / p["position_value_usd"] * 100)

    avg_win_pct = _safe_div(sum(win_pcts), len(win_pcts)) if win_pcts else 0.0
    avg_loss_pct = _safe_div(sum(loss_pcts), len(loss_pcts)) if loss_pcts else 0.0

    largest_win = max((p["realized_pnl_usd"] for p in wins), default=0.0)
    largest_loss = min((p["realized_pnl_usd"] for p in losses), default=0.0)

    expectancy = (win_rate * avg_win_usd) + ((1 - win_rate) * avg_loss_usd)

    # Max drawdown from equity snapshots
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    snapshots = conn.execute(
        """SELECT timestamp_utc, total_equity, peak_equity, drawdown_pct
           FROM equity_snapshots WHERE timestamp_utc >= ?
           ORDER BY timestamp_utc ASC""",
        (cutoff,)
    ).fetchall()
    snapshots = [dict(s) for s in snapshots]

    max_dd_pct = 0.0
    max_dd_usd = 0.0
    max_dd_start = None
    max_dd_end = None
    current_dd_pct = 0.0

    if snapshots:
        peak = snapshots[0]["total_equity"]
        dd_start = snapshots[0]["timestamp_utc"]
        for s in snapshots:
            eq = s["total_equity"]
            if eq > peak:
                peak = eq
                dd_start = s["timestamp_utc"]
            dd = peak - eq
            dd_pct = _safe_div(dd, peak) * 100
            if dd_pct > max_dd_pct:
                max_dd_pct = dd_pct
                max_dd_usd = dd
                max_dd_start = dd_start[:10]
                max_dd_end = s["timestamp_utc"][:10]
        # Current drawdown
        last = snapshots[-1]
        if last["drawdown_pct"] is not None:
            current_dd_pct = last["drawdown_pct"]

    # R-multiple tracking
    r_values = []
    for p in positions:
        r = _calculate_r_achieved(p)
        if r is not None:
            r_values.append(r)

    avg_r = _safe_div(sum(r_values), len(r_values)) if r_values else 0.0
    trades_above_3r = sum(1 for r in r_values if r >= 3.0)
    trades_below_1r_loss = sum(1 for r in r_values if r < -1.0)

    # Timing stats
    hold_times = [_holding_hours(p["opened_at"], p["closed_at"]) for p in positions]
    win_hold = [_holding_hours(p["opened_at"], p["closed_at"]) for p in wins]
    loss_hold = [_holding_hours(p["opened_at"], p["closed_at"]) for p in losses]

    avg_hold = _safe_div(sum(hold_times), len(hold_times)) if hold_times else 0.0
    avg_win_hold = _safe_div(sum(win_hold), len(win_hold)) if win_hold else 0.0
    avg_loss_hold = _safe_div(sum(loss_hold), len(loss_hold)) if loss_hold else 0.0

    # Active state
    open_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM paper_positions WHERE status = 'OPEN'"
    ).fetchone()["cnt"]
    pending_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM trade_setups WHERE status = 'PENDING'"
    ).fetchone()["cnt"]

    # Capital deployed
    open_value = conn.execute(
        "SELECT COALESCE(SUM(position_value_usd), 0) as val FROM paper_positions WHERE status = 'OPEN'"
    ).fetchone()["val"]
    capital_deployed_pct = _safe_div(open_value, current_equity) * 100

    conn.close()

    return {
        "period_days": days,
        "starting_equity": _round2(starting),
        "current_equity": _round2(current_equity),
        "total_return_pct": _round2((current_equity - starting) / starting * 100) if starting > 0 else 0.0,
        "total_return_usd": _round2(current_equity - starting),
        # Trade stats
        "total_trades": total_trades,
        "wins": win_count,
        "losses": loss_count,
        "partials": partial_count,
        "win_rate": _round2(win_rate),
        # P&L stats
        "gross_profit_usd": _round2(gross_profit),
        "gross_loss_usd": _round2(gross_loss),
        "profit_factor": _round2(profit_factor),
        "avg_win_usd": _round2(avg_win_usd),
        "avg_loss_usd": _round2(avg_loss_usd),
        "avg_win_pct": _round2(avg_win_pct),
        "avg_loss_pct": _round2(avg_loss_pct),
        "largest_win_usd": _round2(largest_win),
        "largest_loss_usd": _round2(largest_loss),
        "expectancy_usd": _round2(expectancy),
        # Risk stats
        "max_drawdown_pct": _round2(max_dd_pct),
        "max_drawdown_usd": _round2(max_dd_usd),
        "max_drawdown_start": max_dd_start,
        "max_drawdown_end": max_dd_end,
        "current_drawdown_pct": _round2(current_dd_pct),
        # R-multiple tracking
        "avg_r_achieved": _round2(avg_r),
        "trades_above_3r": trades_above_3r,
        "trades_below_1r_loss": trades_below_1r_loss,
        # Timing stats
        "avg_holding_hours": round(avg_hold),
        "avg_win_holding_hours": round(avg_win_hold),
        "avg_loss_holding_hours": round(avg_loss_hold),
        # Active state
        "open_positions": open_count,
        "pending_setups": pending_count,
        "capital_deployed_pct": _round2(capital_deployed_pct),
    }


# ============================================================================
# PERFORMANCE BY STRATEGY
# ============================================================================

def get_performance_by_strategy(days: int = 90) -> List[Dict]:
    """Group closed positions by pattern_type and return per-strategy stats."""
    conn = get_connection()
    init_paper_tables(conn)
    positions = _get_closed_positions(conn, days)
    conn.close()

    # Group by pattern_type
    groups: Dict[str, List[Dict]] = {}
    for p in positions:
        strategy = p.get("pattern_type") or "Unknown"
        groups.setdefault(strategy, []).append(p)

    results = []
    for strategy, trades in sorted(groups.items(), key=lambda x: -len(x[1])):
        wins = [t for t in trades if t["realized_pnl_usd"] > 0]
        losses = [t for t in trades if t["realized_pnl_usd"] < 0]
        total_pnl = sum(t["realized_pnl_usd"] for t in trades)
        gross_profit = sum(t["realized_pnl_usd"] for t in wins)
        gross_loss = abs(sum(t["realized_pnl_usd"] for t in losses))

        pnl_pcts = []
        for t in trades:
            if t["position_value_usd"] > 0:
                pnl_pcts.append(t["realized_pnl_usd"] / t["position_value_usd"] * 100)

        r_values = [_calculate_r_achieved(t) for t in trades]
        r_values = [r for r in r_values if r is not None]

        results.append({
            "strategy": strategy,
            "trades": len(trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": _round2(_safe_div(len(wins), len(trades))),
            "avg_pnl_pct": _round2(_safe_div(sum(pnl_pcts), len(pnl_pcts))) if pnl_pcts else 0.0,
            "total_pnl_usd": _round2(total_pnl),
            "profit_factor": _round2(_safe_div(gross_profit, gross_loss)),
            "avg_r_achieved": _round2(_safe_div(sum(r_values), len(r_values))) if r_values else 0.0,
        })

    return results


# ============================================================================
# PERFORMANCE BY DIRECTION
# ============================================================================

def get_performance_by_direction(days: int = 90) -> Dict:
    """Return stats split by LONG vs SHORT."""
    conn = get_connection()
    init_paper_tables(conn)
    positions = _get_closed_positions(conn, days)
    conn.close()

    result = {}
    for direction in ["LONG", "SHORT"]:
        trades = [p for p in positions if p["direction"] == direction]
        wins = [t for t in trades if t["realized_pnl_usd"] > 0]
        losses = [t for t in trades if t["realized_pnl_usd"] < 0]
        total_pnl = sum(t["realized_pnl_usd"] for t in trades)
        gross_profit = sum(t["realized_pnl_usd"] for t in wins)
        gross_loss = abs(sum(t["realized_pnl_usd"] for t in losses))

        r_values = [_calculate_r_achieved(t) for t in trades]
        r_values = [r for r in r_values if r is not None]

        result[direction] = {
            "trades": len(trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": _round2(_safe_div(len(wins), len(trades))),
            "total_pnl_usd": _round2(total_pnl),
            "profit_factor": _round2(_safe_div(gross_profit, gross_loss)),
            "avg_r_achieved": _round2(_safe_div(sum(r_values), len(r_values))) if r_values else 0.0,
        }

    return result


# ============================================================================
# EQUITY CURVE
# ============================================================================

def get_equity_curve(days: int = 90) -> List[Dict]:
    """Return equity snapshots as a time series."""
    conn = get_connection()
    init_paper_tables(conn)

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows = conn.execute(
        """SELECT timestamp_utc, total_equity, drawdown_pct
           FROM equity_snapshots
           WHERE timestamp_utc >= ?
           ORDER BY timestamp_utc ASC""",
        (cutoff,)
    ).fetchall()
    conn.close()

    return [
        {
            "timestamp": dict(r)["timestamp_utc"],
            "equity": _round2(dict(r)["total_equity"]),
            "drawdown_pct": _round2(dict(r)["drawdown_pct"] or 0.0),
        }
        for r in rows
    ]


# ============================================================================
# RECENT TRADES
# ============================================================================

def get_recent_trades(limit: int = 20) -> List[Dict]:
    """Return recently closed positions with full details."""
    conn = get_connection()
    init_paper_tables(conn)

    rows = conn.execute(
        """SELECT pp.*, ts.pattern_type
           FROM paper_positions pp
           LEFT JOIN trade_setups ts ON pp.setup_id = ts.setup_id
           WHERE pp.status = 'CLOSED'
           ORDER BY pp.closed_at DESC
           LIMIT ?""",
        (limit,)
    ).fetchall()
    conn.close()

    results = []
    for r in rows:
        p = dict(r)
        partials = json.loads(p["partial_closes"] or "[]")
        hold_h = _holding_hours(p["opened_at"], p["closed_at"])
        r_achieved = _calculate_r_achieved(p)

        results.append({
            "token": p["token"],
            "direction": p["direction"],
            "setup_id": p["setup_id"],
            "pattern_type": p.get("pattern_type") or "Unknown",
            "entry_price": p["entry_price"],
            "close_reason": p["close_reason"],
            "realized_pnl_usd": _round2(p["realized_pnl_usd"]),
            "pnl_pct": _round2(
                p["realized_pnl_usd"] / p["position_value_usd"] * 100
                if p["position_value_usd"] > 0 else 0.0
            ),
            "r_achieved": r_achieved,
            "holding_hours": round(hold_h),
            "partial_closes": len(partials),
            "opened_at": p["opened_at"][:19],
            "closed_at": (p["closed_at"] or "")[:19],
        })

    return results


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================

def format_summary(data: Dict) -> str:
    """Format performance summary for display."""
    if "error" in data:
        return data["error"]

    lines = []
    lines.append(f"{'═' * 62}")

    # Portfolio
    sign = "+" if data["total_return_pct"] >= 0 else ""
    lines.append(f"  📊 PAPER ${data['starting_equity']:,.2f}")
    lines.append(f"    Current:   ${data['current_equity']:,.2f}  ({sign}{data['total_return_pct']:.2f}%)")

    # Find peak from equity curve
    peak = data["current_equity"] + (data["max_drawdown_usd"] if data["current_drawdown_pct"] > 0 else 0)
    lines.append(f"    Drawdown:  -{data['current_drawdown_pct']:.2f}% (from peak)")

    # Trades
    lines.append(f"")
    lines.append(f"  📈 TRADES")
    lines.append(f"    Total: {data['total_trades']} closed | Win rate: {data['win_rate'] * 100:.1f}%")
    lines.append(f"    Wins: {data['wins']} | Losses: {data['losses']} | Partial: {data['partials']}")

    if data["total_trades"] > 0:
        lines.append(
            f"    Avg win: +${data['avg_win_usd']:,.2f} (+{data['avg_win_pct']:.1f}%) | "
            f"Avg loss: ${data['avg_loss_usd']:,.2f} ({data['avg_loss_pct']:.1f}%)"
        )
        lines.append(
            f"    Largest win: +${data['largest_win_usd']:,.2f} | "
            f"Largest loss: ${data['largest_loss_usd']:,.2f}"
        )

    # Risk
    lines.append(f"")
    lines.append(f"  ⚖️  RISK")
    lines.append(f"    Profit factor: {data['profit_factor']:.2f}")
    lines.append(f"    Expectancy: +${data['expectancy_usd']:,.2f}/trade")
    lines.append(
        f"    Max drawdown: -{data['max_drawdown_pct']:.1f}% (${data['max_drawdown_usd']:,.0f})"
    )
    if data["max_drawdown_start"]:
        lines.append(f"    Drawdown period: {data['max_drawdown_start']} → {data['max_drawdown_end']}")
    lines.append(f"    Avg R achieved: {data['avg_r_achieved']:.1f}R")

    # Timing
    lines.append(f"")
    lines.append(f"  ⏱️  TIMING")
    lines.append(
        f"    Avg hold: {data['avg_holding_hours']}h | "
        f"Avg win hold: {data['avg_win_holding_hours']}h | "
        f"Avg loss hold: {data['avg_loss_holding_hours']}h"
    )

    # Active
    lines.append(f"")
    lines.append(f"  🔄 ACTIVE")
    lines.append(
        f"    Open positions: {data['open_positions']} | "
        f"Pending setups: {data['pending_setups']}"
    )
    lines.append(f"    Capital deployed: {data['capital_deployed_pct']:.1f}%")

    lines.append(f"")
    lines.append(f"{'═' * 62}")
    return "\n".join(lines)


def format_by_strategy(data: List[Dict]) -> str:
    """Format strategy breakdown."""
    if not data:
        return "No closed trades to analyze."

    lines = []
    lines.append(f"{'═' * 62}")
    lines.append(f"  PERFORMANCE BY STRATEGY")
    lines.append(f"{'═' * 62}")

    for s in data:
        wr = s["win_rate"] * 100
        sign = "+" if s["total_pnl_usd"] >= 0 else ""
        lines.append(f"")
        lines.append(f"  {s['strategy']}")
        lines.append(f"    Trades: {s['trades']} | Win rate: {wr:.0f}% ({s['wins']}W/{s['losses']}L)")
        lines.append(f"    Total PnL: {sign}${s['total_pnl_usd']:,.2f} | Avg: {sign}{s['avg_pnl_pct']:.1f}%")
        lines.append(f"    Profit factor: {s['profit_factor']:.2f} | Avg R: {s['avg_r_achieved']:.1f}")

    lines.append(f"")
    lines.append(f"{'═' * 62}")
    return "\n".join(lines)


def format_by_direction(data: Dict) -> str:
    """Format direction breakdown."""
    lines = []
    lines.append(f"{'═' * 62}")
    lines.append(f"  PERFORMANCE BY DIRECTION")
    lines.append(f"{'═' * 62}")

    for direction in ["LONG", "SHORT"]:
        d = data.get(direction, {})
        if not d or d["trades"] == 0:
            lines.append(f"")
            lines.append(f"  {direction}: No trades")
            continue

        wr = d["win_rate"] * 100
        sign = "+" if d["total_pnl_usd"] >= 0 else ""
        lines.append(f"")
        lines.append(f"  {direction}")
        lines.append(f"    Trades: {d['trades']} | Win rate: {wr:.0f}% ({d['wins']}W/{d['losses']}L)")
        lines.append(f"    Total PnL: {sign}${d['total_pnl_usd']:,.2f}")
        lines.append(f"    Profit factor: {d['profit_factor']:.2f} | Avg R: {d['avg_r_achieved']:.1f}")

    lines.append(f"")
    lines.append(f"{'═' * 62}")
    return "\n".join(lines)


def format_recent_trades(trades: List[Dict]) -> str:
    """Format recent trades list."""
    if not trades:
        return "No closed trades found."

    lines = []
    lines.append(f"{'═' * 62}")
    lines.append(f"  RECENT TRADES ({len(trades)})")
    lines.append(f"{'═' * 62}")

    for t in trades:
        pnl_sign = "+" if t["realized_pnl_usd"] >= 0 else ""
        r_str = f"{t['r_achieved']:.1f}R" if t["r_achieved"] is not None else "N/A"
        lines.append(f"")
        lines.append(
            f"  {t['token']} {t['direction']} | {t['pattern_type']} | {t['close_reason']}"
        )
        lines.append(
            f"    PnL: {pnl_sign}${t['realized_pnl_usd']:,.2f} ({pnl_sign}{t['pnl_pct']:.1f}%) | "
            f"R: {r_str} | Hold: {t['holding_hours']}h"
        )
        lines.append(f"    {t['opened_at']} → {t['closed_at']}")

    lines.append(f"")
    lines.append(f"{'═' * 62}")
    return "\n".join(lines)


def format_equity_csv(curve: List[Dict]) -> str:
    """Format equity curve as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "equity", "drawdown_pct"])
    for point in curve:
        writer.writerow([point["timestamp"], point["equity"], point["drawdown_pct"]])
    return output.getvalue()


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Paper Trading Analytics — Titan Terminal v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # summary
    summary_parser = subparsers.add_parser("summary", help="Full performance summary")
    summary_parser.add_argument("--days", type=int, default=90, help="Analysis window (days)")

    # by-strategy
    strat_parser = subparsers.add_parser("by-strategy", help="Performance by strategy")
    strat_parser.add_argument("--days", type=int, default=90, help="Analysis window (days)")

    # by-direction
    dir_parser = subparsers.add_parser("by-direction", help="LONG vs SHORT performance")
    dir_parser.add_argument("--days", type=int, default=90, help="Analysis window (days)")

    # equity-curve
    eq_parser = subparsers.add_parser("equity-curve", help="Equity curve data")
    eq_parser.add_argument("--days", type=int, default=90, help="Analysis window (days)")
    eq_parser.add_argument("--csv", action="store_true", help="Output as CSV")

    # recent-trades
    recent_parser = subparsers.add_parser("recent-trades", help="Recent closed trades")
    recent_parser.add_argument("--limit", type=int, default=20, help="Number of trades")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "summary":
        data = get_performance_summary(args.days)
        print(format_summary(data))

    elif args.command == "by-strategy":
        data = get_performance_by_strategy(args.days)
        print(format_by_strategy(data))

    elif args.command == "by-direction":
        data = get_performance_by_direction(args.days)
        print(format_by_direction(data))

    elif args.command == "equity-curve":
        curve = get_equity_curve(args.days)
        if args.csv:
            print(format_equity_csv(curve))
        else:
            if not curve:
                print("No equity snapshots found.")
            else:
                print(f"Equity curve: {len(curve)} data points ({args.days}d window)")
                for point in curve[-10:]:  # Show last 10
                    ts = point["timestamp"][:19]
                    print(f"  {ts}  ${point['equity']:,.2f}  DD: {point['drawdown_pct']:.2f}%")
                if len(curve) > 10:
                    print(f"  ... ({len(curve) - 10} earlier points not shown, use --csv for full export)")

    elif args.command == "recent-trades":
        trades = get_recent_trades(args.limit)
        print(format_recent_trades(trades))


if __name__ == "__main__":
    main()
