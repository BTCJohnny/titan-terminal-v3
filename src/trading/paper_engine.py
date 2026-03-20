#!/usr/bin/env python3
"""
Paper Trading Engine
====================
Manages a virtual $50,000 portfolio against live OHLCV prices.
Auto-enters PENDING setups when entry prices are hit, auto-exits on
stop/target hits with 50% scale-out at T1.

Uses: data/titan_intelligence.db (same DB as intelligence.py)

Usage:
    python3 src/trading/paper_engine.py tick              # Run tick engine
    python3 src/trading/paper_engine.py tick --cron        # Cron mode (compact output)
    python3 src/trading/paper_engine.py status             # Show portfolio status
    python3 src/trading/paper_engine.py init               # Init with $50,000
    python3 src/trading/paper_engine.py init --balance X   # Init with custom balance
    python3 src/trading/paper_engine.py init --reset       # Reset everything
    python3 src/trading/paper_engine.py history             # Recent equity snapshots
    python3 src/trading/paper_engine.py history --days 7    # Last 7 days
    python3 src/trading/paper_engine.py positions           # Open positions
    python3 src/trading/paper_engine.py positions --closed  # Closed positions
    python3 src/trading/paper_engine.py positions --all     # All positions
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from src.storage.intelligence import (
    get_connection,
    get_latest_cached_price,
    refresh_active_tokens,
    update_setup_entered,
    update_setup_closed,
)

# Directories
REPORTS_DIR = PROJECT_ROOT / "signals" / "dashboards"
DB_PATH = PROJECT_ROOT / "data" / "titan_intelligence.db"

DEFAULT_BALANCE = 50000.0

# ============================================================================
# SCHEMA
# ============================================================================

PAPER_SCHEMA = """
CREATE TABLE IF NOT EXISTS paper_portfolio (
    id INTEGER PRIMARY KEY,
    created_at TEXT NOT NULL,
    starting_balance REAL NOT NULL DEFAULT 50000.0,
    current_cash REAL NOT NULL DEFAULT 50000.0,
    total_deposited REAL NOT NULL DEFAULT 50000.0,
    total_withdrawn REAL NOT NULL DEFAULT 0.0,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS paper_positions (
    id INTEGER PRIMARY KEY,
    setup_id TEXT NOT NULL,
    opened_at TEXT NOT NULL,
    closed_at TEXT,

    token TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_price REAL NOT NULL,
    total_units REAL NOT NULL,
    remaining_units REAL NOT NULL,
    position_value_usd REAL NOT NULL,

    original_stop REAL NOT NULL,
    current_stop REAL NOT NULL,
    target_1 REAL,
    target_2 REAL,
    target_3 REAL,

    partial_closes TEXT DEFAULT '[]',

    realized_pnl_usd REAL NOT NULL DEFAULT 0.0,
    unrealized_pnl_usd REAL,

    status TEXT NOT NULL DEFAULT 'OPEN',
    close_reason TEXT,

    UNIQUE(setup_id)
);

CREATE INDEX IF NOT EXISTS idx_paper_pos_status ON paper_positions(status);
CREATE INDEX IF NOT EXISTS idx_paper_pos_token ON paper_positions(token);
CREATE INDEX IF NOT EXISTS idx_paper_pos_setup ON paper_positions(setup_id);

CREATE TABLE IF NOT EXISTS equity_snapshots (
    id INTEGER PRIMARY KEY,
    timestamp_utc TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'tick',

    cash REAL NOT NULL,
    positions_value REAL NOT NULL,
    total_equity REAL NOT NULL,

    total_return_pct REAL,
    peak_equity REAL,
    drawdown_pct REAL,

    open_positions INTEGER NOT NULL DEFAULT 0,
    pending_setups INTEGER NOT NULL DEFAULT 0,

    entries_filled INTEGER NOT NULL DEFAULT 0,
    exits_filled INTEGER NOT NULL DEFAULT 0,
    tick_summary TEXT
);

CREATE INDEX IF NOT EXISTS idx_equity_ts ON equity_snapshots(timestamp_utc);
"""


def init_paper_tables(conn: sqlite3.Connection) -> None:
    """Create paper trading tables if they don't exist."""
    conn.executescript(PAPER_SCHEMA)
    conn.commit()


# ============================================================================
# PORTFOLIO MANAGEMENT
# ============================================================================

def get_portfolio(conn: sqlite3.Connection) -> Optional[Dict]:
    """Get the paper portfolio row."""
    row = conn.execute("SELECT * FROM paper_portfolio WHERE is_active = 1 LIMIT 1").fetchone()
    return dict(row) if row else None


def init_portfolio(balance: float = DEFAULT_BALANCE, conn: sqlite3.Connection = None) -> Dict:
    """Create the paper portfolio. Returns the portfolio dict."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    init_paper_tables(conn)

    existing = get_portfolio(conn)
    if existing:
        if close_conn:
            conn.close()
        return existing

    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO paper_portfolio (created_at, starting_balance, current_cash, total_deposited)
           VALUES (?, ?, ?, ?)""",
        (now, balance, balance, balance)
    )
    conn.commit()

    # Log initial equity snapshot
    conn.execute(
        """INSERT INTO equity_snapshots
           (timestamp_utc, source, cash, positions_value, total_equity,
            total_return_pct, peak_equity, drawdown_pct, open_positions, pending_setups)
           VALUES (?, 'init', ?, 0.0, ?, 0.0, ?, 0.0, 0, 0)""",
        (now, balance, balance, balance)
    )
    conn.commit()

    portfolio = get_portfolio(conn)
    if close_conn:
        conn.close()
    return portfolio


def reset_portfolio(balance: float = DEFAULT_BALANCE) -> Dict:
    """Drop and recreate all paper trading tables."""
    conn = get_connection()
    init_paper_tables(conn)
    conn.execute("DELETE FROM paper_positions")
    conn.execute("DELETE FROM paper_portfolio")
    conn.execute("DELETE FROM equity_snapshots")
    conn.commit()
    portfolio = init_portfolio(balance, conn)
    conn.close()
    return portfolio


# ============================================================================
# TICK ENGINE
# ============================================================================

def _calculate_pnl(direction: str, entry_price: float, exit_price: float, units: float) -> float:
    """Calculate PnL for a close."""
    if direction == "LONG":
        return (exit_price - entry_price) * units
    else:  # SHORT
        return (entry_price - exit_price) * units


def _cash_returned(direction: str, entry_price: float, exit_price: float, units: float) -> float:
    """Calculate cash returned when closing a position."""
    if direction == "LONG":
        return exit_price * units
    else:  # SHORT: original margin (entry * units) + pnl
        return entry_price * units + (entry_price - exit_price) * units


def _record_partial_close(
    conn: sqlite3.Connection,
    pos: Dict,
    price: float,
    units: float,
    reason: str,
    now: str,
) -> float:
    """Record a partial close on a position. Returns PnL for the close."""
    pnl = _calculate_pnl(pos["direction"], pos["entry_price"], price, units)
    cash_back = _cash_returned(pos["direction"], pos["entry_price"], price, units)

    partials = json.loads(pos["partial_closes"] or "[]")
    partials.append({
        "timestamp": now,
        "price": round(price, 6),
        "units": round(units, 8),
        "pnl_usd": round(pnl, 2),
        "reason": reason,
    })

    new_remaining = pos["remaining_units"] - units
    new_realized = pos["realized_pnl_usd"] + pnl

    conn.execute(
        """UPDATE paper_positions
           SET remaining_units = ?, realized_pnl_usd = ?, partial_closes = ?
           WHERE id = ?""",
        (round(new_remaining, 8), round(new_realized, 2), json.dumps(partials), pos["id"])
    )

    # Update portfolio cash
    conn.execute(
        "UPDATE paper_portfolio SET current_cash = current_cash + ? WHERE is_active = 1",
        (round(cash_back, 2),)
    )

    return pnl


def _close_position(
    conn: sqlite3.Connection,
    pos: Dict,
    price: float,
    units: float,
    reason: str,
    close_reason: str,
    now: str,
) -> float:
    """Fully close a position (or close remaining units). Returns PnL."""
    pnl = _record_partial_close(conn, pos, price, units, reason, now)

    conn.execute(
        """UPDATE paper_positions
           SET status = 'CLOSED', closed_at = ?, close_reason = ?
           WHERE id = ?""",
        (now, close_reason, pos["id"])
    )

    return pnl


def _has_hit_t1(pos: Dict) -> bool:
    """Check if T1 was already taken (remaining < total)."""
    return pos["remaining_units"] < pos["total_units"]


def tick() -> Dict[str, Any]:
    """
    Run one tick of the paper trading engine.
    Returns a summary dict with all actions taken.
    """
    now = datetime.now(timezone.utc).isoformat()
    errors: List[str] = []
    entries_filled: List[Dict] = []
    exits_filled: List[Dict] = []
    partials_filled: List[Dict] = []

    # Step 1: Refresh prices
    try:
        refresh_result = refresh_active_tokens()
        if refresh_result.get("errors"):
            for err in refresh_result["errors"]:
                errors.append(f"Refresh: {err}")
    except Exception as e:
        errors.append(f"Refresh failed: {str(e)[:100]}")

    # Step 2: Get portfolio state
    conn = get_connection()
    init_paper_tables(conn)

    portfolio = get_portfolio(conn)
    if not portfolio:
        portfolio = init_portfolio(DEFAULT_BALANCE, conn)
        portfolio = get_portfolio(conn)

    starting_balance = portfolio["starting_balance"]

    # Step 3: Process PENDING setups
    pending_setups = conn.execute(
        """SELECT ts.* FROM trade_setups ts
           WHERE ts.status = 'PENDING'
             AND NOT EXISTS (SELECT 1 FROM paper_positions pp WHERE pp.setup_id = ts.setup_id)
           ORDER BY ts.timestamp_utc ASC"""
    ).fetchall()
    pending_setups = [dict(r) for r in pending_setups]

    for setup in pending_setups:
        token = setup["token"]
        setup_id = setup["setup_id"]
        direction = setup["direction"]
        entry_price = setup["entry_price"]
        stop_loss = setup["stop_loss"]

        if not entry_price or not stop_loss:
            errors.append(f"{token}: missing entry/stop on setup {setup_id}")
            continue

        price = get_latest_cached_price(token)
        if price is None:
            errors.append(f"{token}: no price data — skipped")
            continue

        # Check entry trigger
        triggered = False
        if direction == "LONG" and price <= entry_price:
            triggered = True
        elif direction == "SHORT" and price >= entry_price:
            triggered = True

        if not triggered:
            continue

        # Calculate position size
        position_size_usd = setup.get("position_size_usd")
        if position_size_usd and position_size_usd > 0:
            units = position_size_usd / entry_price
            position_value = position_size_usd
        else:
            # Refresh portfolio for current equity
            portfolio = get_portfolio(conn)
            current_equity = _calculate_equity(conn, portfolio)
            risk_usd = current_equity * 0.02
            risk_per_unit = abs(entry_price - stop_loss)
            if risk_per_unit <= 0:
                errors.append(f"{token}: entry == stop, can't size position")
                continue
            units = risk_usd / risk_per_unit
            position_value = units * entry_price

        # Check cash available
        portfolio = get_portfolio(conn)
        if portfolio["current_cash"] < position_value:
            errors.append(
                f"{token}: insufficient cash — need ${position_value:,.2f}, have ${portfolio['current_cash']:,.2f}"
            )
            continue

        # Deduct cash
        conn.execute(
            "UPDATE paper_portfolio SET current_cash = current_cash - ? WHERE is_active = 1",
            (round(position_value, 2),)
        )

        # Create paper position
        conn.execute(
            """INSERT INTO paper_positions
               (setup_id, opened_at, token, direction, entry_price, total_units,
                remaining_units, position_value_usd, original_stop, current_stop,
                target_1, target_2, target_3, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')""",
            (
                setup_id, now, token, direction, entry_price,
                round(units, 8), round(units, 8), round(position_value, 2),
                stop_loss, stop_loss,
                setup.get("target_1"), setup.get("target_2"), setup.get("target_3"),
            )
        )
        conn.commit()

        # Update trade_setup status
        try:
            update_setup_entered(setup_id, entry_price)
        except Exception as e:
            errors.append(f"{token}: failed to update setup status: {str(e)[:80]}")

        entries_filled.append({
            "token": token,
            "setup_id": setup_id,
            "direction": direction,
            "entry_price": entry_price,
            "units": round(units, 8),
            "value_usd": round(position_value, 2),
        })

    # Step 4: Process OPEN positions
    open_positions = conn.execute(
        "SELECT * FROM paper_positions WHERE status = 'OPEN'"
    ).fetchall()
    open_positions = [dict(r) for r in open_positions]

    for pos in open_positions:
        token = pos["token"]
        direction = pos["direction"]
        entry_price = pos["entry_price"]
        current_stop = pos["current_stop"]
        target_1 = pos["target_1"]
        target_2 = pos["target_2"]
        target_3 = pos["target_3"]
        remaining = pos["remaining_units"]

        price = get_latest_cached_price(token)
        if price is None:
            conn.execute(
                "UPDATE paper_positions SET unrealized_pnl_usd = NULL WHERE id = ?",
                (pos["id"],)
            )
            errors.append(f"{token}: no price data for open position — skipped")
            continue

        # Determine effective T2 target: use target_3 if target_2 is None but target_3 exists
        effective_t2 = target_2
        effective_t2_label = "T2"
        if effective_t2 is None and target_3 is not None:
            effective_t2 = target_3
            effective_t2_label = "T3"

        # Determine the final target (highest priority after T1)
        final_target = None
        final_target_label = None
        if target_3 is not None and target_2 is not None:
            final_target = target_3
            final_target_label = "T3"
        elif effective_t2 is not None:
            final_target = effective_t2
            final_target_label = effective_t2_label

        # a. Stop loss check (highest priority — protect capital)
        stop_hit = False
        if direction == "LONG" and price <= current_stop:
            stop_hit = True
        elif direction == "SHORT" and price >= current_stop:
            stop_hit = True

        if stop_hit:
            had_t1 = _has_hit_t1(pos)
            close_reason = "STOP_AFTER_T1" if had_t1 else "STOP"
            outcome = "PARTIAL" if had_t1 else "LOSS"
            pnl = _close_position(conn, pos, current_stop, remaining, "STOP", close_reason, now)
            conn.commit()

            try:
                update_setup_closed(
                    pos["setup_id"], current_stop, outcome,
                    hit_target=1 if had_t1 else 0,
                    pnl_usd=round(pos["realized_pnl_usd"] + pnl, 2),
                )
            except Exception as e:
                errors.append(f"{token}: failed to close setup: {str(e)[:80]}")

            exits_filled.append({
                "token": token,
                "setup_id": pos["setup_id"],
                "direction": direction,
                "exit_price": current_stop,
                "reason": close_reason,
                "pnl_usd": round(pos["realized_pnl_usd"] + pnl, 2),
                "units": round(remaining, 8),
            })
            continue

        # Check if we should process T1 + higher targets in the same tick (price gapped)
        t1_not_yet_taken = remaining == pos["total_units"]

        # b. Check final target (T2 or T3) — only if T1 was already taken
        if _has_hit_t1(pos) and final_target is not None:
            final_hit = False
            if direction == "LONG" and price >= final_target:
                final_hit = True
            elif direction == "SHORT" and price <= final_target:
                final_hit = True

            if final_hit:
                hit_num = 3 if final_target_label == "T3" else 2
                close_reason = f"{final_target_label}_AFTER_T1"
                pnl = _close_position(
                    conn, pos, final_target, remaining, final_target_label, close_reason, now
                )
                conn.commit()

                try:
                    update_setup_closed(
                        pos["setup_id"], final_target, "WIN",
                        hit_target=hit_num,
                        pnl_usd=round(pos["realized_pnl_usd"] + pnl, 2),
                    )
                except Exception as e:
                    errors.append(f"{token}: failed to close setup: {str(e)[:80]}")

                exits_filled.append({
                    "token": token,
                    "setup_id": pos["setup_id"],
                    "direction": direction,
                    "exit_price": final_target,
                    "reason": close_reason,
                    "pnl_usd": round(pos["realized_pnl_usd"] + pnl, 2),
                    "units": round(remaining, 8),
                })
                continue

        # c. Target 1 hit (first time)
        if t1_not_yet_taken and target_1 is not None:
            t1_hit = False
            if direction == "LONG" and price >= target_1:
                t1_hit = True
            elif direction == "SHORT" and price <= target_1:
                t1_hit = True

            if t1_hit:
                # If no T2 target, close 100% at T1
                if effective_t2 is None:
                    pnl = _close_position(
                        conn, pos, target_1, remaining, "T1", "T1_FULL", now
                    )
                    conn.commit()

                    try:
                        update_setup_closed(
                            pos["setup_id"], target_1, "WIN",
                            hit_target=1,
                            pnl_usd=round(pos["realized_pnl_usd"] + pnl, 2),
                        )
                    except Exception as e:
                        errors.append(f"{token}: failed to close setup: {str(e)[:80]}")

                    exits_filled.append({
                        "token": token,
                        "setup_id": pos["setup_id"],
                        "direction": direction,
                        "exit_price": target_1,
                        "reason": "T1_FULL",
                        "pnl_usd": round(pos["realized_pnl_usd"] + pnl, 2),
                        "units": round(remaining, 8),
                    })
                    continue
                else:
                    # Close 50%, move stop to breakeven
                    close_units = pos["total_units"] * 0.5
                    pnl = _record_partial_close(conn, pos, target_1, close_units, "T1", now)

                    # Move stop to breakeven
                    conn.execute(
                        "UPDATE paper_positions SET current_stop = ? WHERE id = ?",
                        (entry_price, pos["id"])
                    )
                    conn.commit()

                    partials_filled.append({
                        "token": token,
                        "setup_id": pos["setup_id"],
                        "direction": direction,
                        "price": target_1,
                        "reason": "T1",
                        "units": round(close_units, 8),
                        "pnl_usd": round(pnl, 2),
                    })

                    # Re-read position for potential same-tick T2/T3 processing
                    pos_updated = dict(conn.execute(
                        "SELECT * FROM paper_positions WHERE id = ?", (pos["id"],)
                    ).fetchone())

                    # Check if T2/T3 also hit in same tick (price gapped)
                    if final_target is not None:
                        final_hit = False
                        if direction == "LONG" and price >= final_target:
                            final_hit = True
                        elif direction == "SHORT" and price <= final_target:
                            final_hit = True

                        if final_hit:
                            hit_num = 3 if final_target_label == "T3" else 2
                            close_reason = f"{final_target_label}_AFTER_T1"
                            remaining_now = pos_updated["remaining_units"]
                            pnl2 = _close_position(
                                conn, pos_updated, final_target, remaining_now,
                                final_target_label, close_reason, now
                            )
                            conn.commit()

                            try:
                                total_pnl = pos_updated["realized_pnl_usd"] + pnl2
                                update_setup_closed(
                                    pos["setup_id"], final_target, "WIN",
                                    hit_target=hit_num,
                                    pnl_usd=round(total_pnl, 2),
                                )
                            except Exception as e:
                                errors.append(f"{token}: failed to close setup: {str(e)[:80]}")

                            exits_filled.append({
                                "token": token,
                                "setup_id": pos["setup_id"],
                                "direction": direction,
                                "exit_price": final_target,
                                "reason": close_reason,
                                "pnl_usd": round(pos_updated["realized_pnl_usd"] + pnl2, 2),
                                "units": round(remaining_now, 8),
                            })
                            continue

        # d. No exit — update unrealized PnL
        # Re-read position in case it was partially closed above
        pos_current = dict(conn.execute(
            "SELECT * FROM paper_positions WHERE id = ?", (pos["id"],)
        ).fetchone())
        if pos_current["status"] == "OPEN":
            unrealized = _calculate_pnl(direction, entry_price, price, pos_current["remaining_units"])
            conn.execute(
                "UPDATE paper_positions SET unrealized_pnl_usd = ? WHERE id = ?",
                (round(unrealized, 2), pos["id"])
            )
            conn.commit()

    # Step 5: Log equity snapshot
    portfolio = get_portfolio(conn)
    cash = portfolio["current_cash"]

    # Calculate positions value
    open_pos_rows = conn.execute(
        "SELECT * FROM paper_positions WHERE status = 'OPEN'"
    ).fetchall()
    open_pos_list = [dict(r) for r in open_pos_rows]

    positions_value = 0.0
    open_pos_summary = []
    for p in open_pos_list:
        price = get_latest_cached_price(p["token"])
        if price is not None:
            pv = p["remaining_units"] * price
        else:
            pv = p["remaining_units"] * p["entry_price"]  # fallback
        positions_value += pv
        open_pos_summary.append({
            "token": p["token"],
            "direction": p["direction"],
            "setup_id": p["setup_id"],
            "entry_price": p["entry_price"],
            "remaining_units": p["remaining_units"],
            "unrealized_pnl": p["unrealized_pnl_usd"],
            "current_stop": p["current_stop"],
        })

    total_equity = cash + positions_value

    # Peak equity
    peak_row = conn.execute(
        "SELECT MAX(total_equity) as peak FROM equity_snapshots"
    ).fetchone()
    peak_equity = peak_row["peak"] if peak_row and peak_row["peak"] is not None else starting_balance
    peak_equity = max(peak_equity, total_equity)

    drawdown_pct = 0.0
    if total_equity < peak_equity and peak_equity > 0:
        drawdown_pct = round((peak_equity - total_equity) / peak_equity * 100, 2)

    total_return_pct = round((total_equity - starting_balance) / starting_balance * 100, 2)

    # Count pending setups
    pending_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM trade_setups WHERE status = 'PENDING'"
    ).fetchone()["cnt"]

    tick_summary_json = json.dumps({
        "entries": [e["token"] for e in entries_filled],
        "exits": [e["token"] for e in exits_filled],
        "partials": [p["token"] for p in partials_filled],
        "errors": errors,
    })

    conn.execute(
        """INSERT INTO equity_snapshots
           (timestamp_utc, source, cash, positions_value, total_equity,
            total_return_pct, peak_equity, drawdown_pct,
            open_positions, pending_setups, entries_filled, exits_filled, tick_summary)
           VALUES (?, 'tick', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            now, round(cash, 2), round(positions_value, 2), round(total_equity, 2),
            total_return_pct, round(peak_equity, 2), drawdown_pct,
            len(open_pos_list), pending_count,
            len(entries_filled), len(exits_filled) + len(partials_filled),
            tick_summary_json,
        )
    )
    conn.commit()
    conn.close()

    return {
        "timestamp": now,
        "entries_filled": entries_filled,
        "exits_filled": exits_filled,
        "partials_filled": partials_filled,
        "open_positions": open_pos_summary,
        "equity": {
            "cash": round(cash, 2),
            "positions_value": round(positions_value, 2),
            "total_equity": round(total_equity, 2),
            "return_pct": total_return_pct,
            "drawdown_pct": drawdown_pct,
            "peak_equity": round(peak_equity, 2),
        },
        "errors": errors,
    }


def _calculate_equity(conn: sqlite3.Connection, portfolio: Dict) -> float:
    """Calculate total equity (cash + open positions at market)."""
    cash = portfolio["current_cash"]
    open_pos = conn.execute(
        "SELECT * FROM paper_positions WHERE status = 'OPEN'"
    ).fetchall()
    positions_value = 0.0
    for p in open_pos:
        p = dict(p)
        price = get_latest_cached_price(p["token"])
        if price is not None:
            positions_value += p["remaining_units"] * price
        else:
            positions_value += p["remaining_units"] * p["entry_price"]
    return cash + positions_value


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================

def format_tick_report(result: Dict) -> str:
    """Format tick result for interactive display."""
    ts = result["timestamp"][:19].replace("T", " ") + " UTC"
    eq = result["equity"]

    lines = []
    lines.append(f"{'─' * 60}")
    lines.append(f"  PAPER TRADE ENGINE — {ts}")
    lines.append(f"{'─' * 60}")

    # Actions
    actions = result["entries_filled"] + result["exits_filled"] + result["partials_filled"]
    if actions:
        lines.append("")
        lines.append("  ACTIONS:")
        for e in result["entries_filled"]:
            lines.append(
                f"    ENTRY: {e['token']} {e['direction']} — "
                f"{e['units']:.4f} units @ ${e['entry_price']:,.2f} (${e['value_usd']:,.2f})"
            )
        for p in result["partials_filled"]:
            pnl_sign = "+" if p["pnl_usd"] >= 0 else ""
            lines.append(
                f"    T1 HIT: {p['token']} — closed 50% at ${p['price']:,.2f} "
                f"({pnl_sign}${p['pnl_usd']:,.2f}), stop -> breakeven"
            )
        for e in result["exits_filled"]:
            pnl_sign = "+" if e["pnl_usd"] >= 0 else ""
            lines.append(
                f"    {e['reason']}: {e['token']} {e['direction']} — "
                f"closed at ${e['exit_price']:,.2f} ({pnl_sign}${e['pnl_usd']:,.2f})"
            )
    else:
        lines.append("")
        lines.append("  ACTIONS: None")

    # Portfolio
    lines.append("")
    lines.append("  PORTFOLIO:")
    lines.append(f"    Cash:      ${eq['cash']:,.2f}")
    lines.append(f"    Positions: ${eq['positions_value']:,.2f} ({len(result['open_positions'])} open)")
    lines.append(f"    Equity:    ${eq['total_equity']:,.2f}")
    sign = "+" if eq["return_pct"] >= 0 else ""
    lines.append(f"    Return:    {sign}{eq['return_pct']:.2f}%")
    lines.append(f"    Drawdown:  {eq['drawdown_pct']:.2f}%")

    # Open positions
    if result["open_positions"]:
        lines.append("")
        lines.append("  OPEN POSITIONS:")
        for p in result["open_positions"]:
            upnl = p["unrealized_pnl"]
            if upnl is not None:
                pnl_sign = "+" if upnl >= 0 else ""
                pnl_str = f"unrealized: {pnl_sign}${upnl:,.2f}"
            else:
                pnl_str = "unrealized: N/A"
            lines.append(
                f"    {p['token']} {p['direction']} [{p['setup_id'][:8]}] — "
                f"{p['remaining_units']:.4f} units @ ${p['entry_price']:,.2f} | {pnl_str}"
            )

    # Errors
    if result["errors"]:
        lines.append("")
        lines.append("  ERRORS:")
        for err in result["errors"]:
            lines.append(f"    {err}")

    lines.append("")
    lines.append(f"{'─' * 60}")
    return "\n".join(lines)


def format_tick_cron(result: Dict) -> str:
    """Format tick result for cron (one-line summary)."""
    eq = result["equity"]
    ts = result["timestamp"][:19] + "Z"
    sign = "+" if eq["return_pct"] >= 0 else ""
    return (
        f"[{ts}] "
        f"Entries: {len(result['entries_filled'])} | "
        f"Exits: {len(result['exits_filled'])} | "
        f"Partials: {len(result['partials_filled'])} | "
        f"Equity: ${eq['total_equity']:,.2f} ({sign}{eq['return_pct']:.2f}%) | "
        f"DD: {eq['drawdown_pct']:.2f}%"
    )


def save_cron_report(result: Dict) -> Path:
    """Save a detailed cron report to signals/dashboards/."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc)
    filename = f"paper_trade_{ts.strftime('%Y%m%d_%H%M')}.md"
    path = REPORTS_DIR / filename

    report = format_tick_report(result)
    path.write_text(report)
    return path


# ============================================================================
# STATUS / HISTORY / POSITIONS COMMANDS
# ============================================================================

def cmd_status() -> str:
    """Show current portfolio status without running a tick."""
    conn = get_connection()
    init_paper_tables(conn)

    portfolio = get_portfolio(conn)
    if not portfolio:
        conn.close()
        return "No paper portfolio initialized. Run: python3 src/trading/paper_engine.py init"

    cash = portfolio["current_cash"]
    starting = portfolio["starting_balance"]

    open_pos = conn.execute(
        "SELECT * FROM paper_positions WHERE status = 'OPEN'"
    ).fetchall()
    open_pos = [dict(r) for r in open_pos]

    positions_value = 0.0
    for p in open_pos:
        price = get_latest_cached_price(p["token"])
        if price is not None:
            positions_value += p["remaining_units"] * price
        else:
            positions_value += p["remaining_units"] * p["entry_price"]

    total_equity = cash + positions_value
    return_pct = (total_equity - starting) / starting * 100

    closed_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM paper_positions WHERE status = 'CLOSED'"
    ).fetchone()["cnt"]

    pending_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM trade_setups WHERE status = 'PENDING'"
    ).fetchone()["cnt"]

    # Win/loss stats
    wins = conn.execute(
        "SELECT COUNT(*) as cnt FROM paper_positions WHERE status = 'CLOSED' AND realized_pnl_usd > 0"
    ).fetchone()["cnt"]
    losses = conn.execute(
        "SELECT COUNT(*) as cnt FROM paper_positions WHERE status = 'CLOSED' AND realized_pnl_usd <= 0"
    ).fetchone()["cnt"]

    total_realized = conn.execute(
        "SELECT COALESCE(SUM(realized_pnl_usd), 0) as total FROM paper_positions WHERE status = 'CLOSED'"
    ).fetchone()["total"]

    # Peak / drawdown
    peak_row = conn.execute(
        "SELECT MAX(total_equity) as peak FROM equity_snapshots"
    ).fetchone()
    peak = peak_row["peak"] if peak_row and peak_row["peak"] else starting
    peak = max(peak, total_equity)
    dd = 0.0
    if total_equity < peak and peak > 0:
        dd = (peak - total_equity) / peak * 100

    conn.close()

    sign = "+" if return_pct >= 0 else ""
    lines = []
    lines.append(f"{'─' * 60}")
    lines.append(f"  PAPER PORTFOLIO STATUS")
    lines.append(f"{'─' * 60}")
    lines.append(f"  Created:     {portfolio['created_at'][:10]}")
    lines.append(f"  Starting:    ${starting:,.2f}")
    lines.append(f"")
    lines.append(f"  Cash:        ${cash:,.2f}")
    lines.append(f"  Positions:   ${positions_value:,.2f} ({len(open_pos)} open)")
    lines.append(f"  Equity:      ${total_equity:,.2f}")
    lines.append(f"  Return:      {sign}{return_pct:.2f}%")
    lines.append(f"  Peak:        ${peak:,.2f}")
    lines.append(f"  Drawdown:    {dd:.2f}%")
    lines.append(f"")
    lines.append(f"  Closed:      {closed_count} trades ({wins}W / {losses}L)")
    lines.append(f"  Realized:    ${total_realized:,.2f}")
    lines.append(f"  Pending:     {pending_count} setups")

    if open_pos:
        lines.append(f"")
        lines.append(f"  OPEN POSITIONS:")
        for p in open_pos:
            price = get_latest_cached_price(p["token"])
            if price is not None and p["unrealized_pnl_usd"] is not None:
                pnl_sign = "+" if p["unrealized_pnl_usd"] >= 0 else ""
                pnl_str = f"{pnl_sign}${p['unrealized_pnl_usd']:,.2f}"
            else:
                pnl_str = "N/A"
            stop_moved = " (BE)" if p["current_stop"] == p["entry_price"] and _has_hit_t1(p) else ""
            lines.append(
                f"    {p['token']} {p['direction']} — "
                f"{p['remaining_units']:.4f} @ ${p['entry_price']:,.2f} | "
                f"stop: ${p['current_stop']:,.2f}{stop_moved} | "
                f"PnL: {pnl_str}"
            )

    lines.append(f"{'─' * 60}")
    return "\n".join(lines)


def cmd_history(days: int = None, limit: int = 10) -> str:
    """Show recent equity snapshots."""
    conn = get_connection()
    init_paper_tables(conn)

    if days:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        rows = conn.execute(
            """SELECT * FROM equity_snapshots
               WHERE timestamp_utc >= ?
               ORDER BY timestamp_utc DESC""",
            (cutoff,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM equity_snapshots ORDER BY timestamp_utc DESC LIMIT ?",
            (limit,)
        ).fetchall()

    conn.close()
    rows = [dict(r) for r in rows]

    if not rows:
        return "No equity snapshots found."

    lines = []
    lines.append(f"{'─' * 60}")
    lines.append(f"  EQUITY HISTORY ({len(rows)} snapshots)")
    lines.append(f"{'─' * 60}")
    lines.append(f"  {'Timestamp':<22} {'Equity':>12} {'Return':>8} {'DD':>6} {'Open':>5} {'Source':<6}")
    lines.append(f"  {'─' * 22} {'─' * 12} {'─' * 8} {'─' * 6} {'─' * 5} {'─' * 6}")

    for r in rows:
        ts = r["timestamp_utc"][:19]
        sign = "+" if (r["total_return_pct"] or 0) >= 0 else ""
        lines.append(
            f"  {ts:<22} ${r['total_equity']:>10,.2f} "
            f"{sign}{r['total_return_pct'] or 0:>6.2f}% "
            f"{r['drawdown_pct'] or 0:>5.2f}% "
            f"{r['open_positions']:>4} "
            f"{r['source']:<6}"
        )

    lines.append(f"{'─' * 60}")
    return "\n".join(lines)


def cmd_positions(show_closed: bool = False, show_all: bool = False) -> str:
    """Show paper positions."""
    conn = get_connection()
    init_paper_tables(conn)

    if show_all:
        rows = conn.execute(
            "SELECT * FROM paper_positions ORDER BY opened_at DESC"
        ).fetchall()
        title = "ALL POSITIONS"
    elif show_closed:
        rows = conn.execute(
            "SELECT * FROM paper_positions WHERE status = 'CLOSED' ORDER BY closed_at DESC"
        ).fetchall()
        title = "CLOSED POSITIONS"
    else:
        rows = conn.execute(
            "SELECT * FROM paper_positions WHERE status = 'OPEN' ORDER BY opened_at DESC"
        ).fetchall()
        title = "OPEN POSITIONS"

    conn.close()
    positions = [dict(r) for r in rows]

    if not positions:
        return f"No {title.lower()} found."

    lines = []
    lines.append(f"{'─' * 60}")
    lines.append(f"  {title} ({len(positions)})")
    lines.append(f"{'─' * 60}")

    for p in positions:
        lines.append(f"")
        status_icon = "OPEN" if p["status"] == "OPEN" else "CLOSED"
        lines.append(f"  [{status_icon}] {p['token']} {p['direction']} — {p['setup_id'][:12]}")
        lines.append(f"    Entry: ${p['entry_price']:,.2f} | Units: {p['total_units']:.4f} (remaining: {p['remaining_units']:.4f})")
        lines.append(f"    Value: ${p['position_value_usd']:,.2f} | Stop: ${p['current_stop']:,.2f}")

        targets = []
        if p["target_1"]:
            targets.append(f"T1: ${p['target_1']:,.2f}")
        if p["target_2"]:
            targets.append(f"T2: ${p['target_2']:,.2f}")
        if p["target_3"]:
            targets.append(f"T3: ${p['target_3']:,.2f}")
        if targets:
            lines.append(f"    Targets: {' | '.join(targets)}")

        lines.append(f"    Opened: {p['opened_at'][:19]}")

        if p["status"] == "CLOSED":
            lines.append(f"    Closed: {(p['closed_at'] or '')[:19]} | Reason: {p['close_reason']}")
            pnl_sign = "+" if p["realized_pnl_usd"] >= 0 else ""
            lines.append(f"    Realized PnL: {pnl_sign}${p['realized_pnl_usd']:,.2f}")
        else:
            if p["unrealized_pnl_usd"] is not None:
                pnl_sign = "+" if p["unrealized_pnl_usd"] >= 0 else ""
                lines.append(f"    Unrealized PnL: {pnl_sign}${p['unrealized_pnl_usd']:,.2f}")

        partials = json.loads(p["partial_closes"] or "[]")
        if partials:
            lines.append(f"    Partial closes: {len(partials)}")
            for pc in partials:
                pnl_sign = "+" if pc["pnl_usd"] >= 0 else ""
                lines.append(
                    f"      {pc['reason']}: {pc['units']:.4f} @ ${pc['price']:,.2f} "
                    f"({pnl_sign}${pc['pnl_usd']:,.2f}) — {pc['timestamp'][:19]}"
                )

    lines.append(f"")
    lines.append(f"{'─' * 60}")
    return "\n".join(lines)


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Paper Trading Engine — Titan Terminal v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # tick
    tick_parser = subparsers.add_parser("tick", help="Run the tick engine")
    tick_parser.add_argument("--cron", action="store_true", help="Cron mode (compact output)")

    # status
    subparsers.add_parser("status", help="Show current portfolio status")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize portfolio")
    init_parser.add_argument("--balance", type=float, default=DEFAULT_BALANCE, help="Starting balance")
    init_parser.add_argument("--reset", action="store_true", help="Reset everything")

    # history
    history_parser = subparsers.add_parser("history", help="Show equity history")
    history_parser.add_argument("--days", type=int, help="Number of days to show")

    # positions
    pos_parser = subparsers.add_parser("positions", help="Show paper positions")
    pos_parser.add_argument("--closed", action="store_true", help="Show closed positions")
    pos_parser.add_argument("--all", action="store_true", help="Show all positions")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "init":
        if args.reset:
            confirm = input("This will DELETE all paper trading data. Type 'yes' to confirm: ")
            if confirm.strip().lower() != "yes":
                print("Aborted.", file=sys.stderr)
                sys.exit(1)
            portfolio = reset_portfolio(args.balance)
            print(f"Portfolio reset. Balance: ${portfolio['current_cash']:,.2f}")
        else:
            portfolio = init_portfolio(args.balance)
            print(f"Portfolio initialized. Balance: ${portfolio['current_cash']:,.2f}")

    elif args.command == "tick":
        result = tick()
        if args.cron:
            print(format_tick_cron(result))
            report_path = save_cron_report(result)
            print(f"Report saved to: {report_path}")
        else:
            print(format_tick_report(result))

    elif args.command == "status":
        print(cmd_status())

    elif args.command == "history":
        print(cmd_history(days=args.days))

    elif args.command == "positions":
        print(cmd_positions(show_closed=args.closed, show_all=args.all))


if __name__ == "__main__":
    main()
