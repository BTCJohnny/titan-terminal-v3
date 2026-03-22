#!/usr/bin/env python3
"""
Titan Terminal v3 — Portfolio-Level Backtest Simulator
=======================================================
Replays all graduated strategies through a single unified capital pool.
Enforces real-world constraints: max 5 positions, 1 per symbol, 30% cash floor.

Cash accounting model:
  - Entry: cash -= units * entry_price  (buy at cost)
  - LONG partial/final close: cash += units * exit_price
  - SHORT partial/final close: cash += units * (2*entry - exit_price)
  Equity = cash + MTM of remaining open units

Usage:
    python3 src/backtesting/portfolio_sim.py run --capital 10000 --days 180
    python3 src/backtesting/portfolio_sim.py run --capital 10000 --days 180 --json
    python3 src/backtesting/portfolio_sim.py run --capital 10000 --days 180 --verbose
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis.indicators import from_timestamp_utc
from src.backtesting.engine import (
    WARMUP_BARS,
    build_context,
    evaluate_signals,
    load_candles,
    load_derivatives,
    precompute_indicators,
)

GRADUATED_DIR = PROJECT_ROOT / "results" / "backtests" / "graduated"
RESULTS_DIR = PROJECT_ROOT / "results" / "backtests"

MAX_POSITIONS = 5
CASH_FLOOR_PCT = 0.30
RISK_PER_TRADE_PCT = 2.0
MAX_DIRECTIONAL = 3


# ============================================================================
# STRATEGY LOADING
# ============================================================================

def load_graduated_strategies() -> list:
    """Load all graduated_*.json files. Return list of strategy dicts."""
    strategies = []
    for f in sorted(GRADUATED_DIR.glob("graduated_*.json")):
        try:
            data = json.loads(f.read_text())
            strategies.append(data)
        except Exception as e:
            print(f"  [WARN] Failed to load {f.name}: {e}")
    return strategies


# ============================================================================
# DATA LOADING
# ============================================================================

def load_pair_data(symbol: str, timeframe: str, days: int, verbose: bool = False) -> dict | None:
    """
    Load candles, derivatives, and precompute indicators for a (symbol, tf) pair.
    Returns None if insufficient data.
    """
    if verbose:
        print(f"    {symbol:10s} {timeframe:3s} ...", end="", flush=True)

    candles = load_candles(symbol, timeframe, days=days + 60)
    if not candles or len(candles) < WARMUP_BARS + 10:
        count = len(candles) if candles else 0
        if verbose:
            print(f" SKIP ({count} bars, need >{WARMUP_BARS + 10})")
        return None

    start_date = from_timestamp_utc(candles[0]["t"]).strftime("%Y-%m-%d")
    end_date = from_timestamp_utc(candles[-1]["t"]).strftime("%Y-%m-%d")

    deriv = load_derivatives(symbol, start_date, end_date)
    ind = precompute_indicators(candles)

    # Timestamp → bar index lookup
    ts_to_idx = {c["t"]: i for i, c in enumerate(candles)}

    if verbose:
        print(f" {len(candles):>5} bars  {len(deriv):>3} deriv days")

    return {
        "candles": candles,
        "ind": ind,
        "deriv": deriv,
        "ts_to_idx": ts_to_idx,
        "start_date": start_date,
        "end_date": end_date,
    }


# ============================================================================
# EQUITY / CASH CALCULATIONS
# ============================================================================

def calculate_equity(portfolio: dict, current_prices: dict) -> float:
    """
    Cash + mark-to-market value of all remaining open position units.

    LONG remaining value  = remaining_units * current_price
    SHORT remaining value = remaining_units * (2*entry - current_price)
      (amount returned if closed now at market)
    """
    equity = portfolio["cash"]
    for sym, pos in portfolio["positions"].items():
        price = current_prices.get(sym, pos["entry_price"])
        remaining = pos["remaining_units"]
        if pos["direction"] == "LONG":
            equity += remaining * price
        else:
            equity += remaining * (2.0 * pos["entry_price"] - price)
    return equity


# ============================================================================
# PORTFOLIO CONSTRAINT CHECKS
# ============================================================================

def can_enter(portfolio: dict, entry: dict, current_prices: dict) -> tuple[bool, str]:
    """
    Check if the portfolio can accept a new position.
    Returns (True, "ok") or (False, reason).
    """
    sym = entry["symbol"]

    if len(portfolio["positions"]) >= MAX_POSITIONS:
        return False, "max_positions"

    if sym in portfolio["positions"]:
        return False, "symbol_occupied"

    direction = entry["direction"]
    same_dir = sum(
        1 for p in portfolio["positions"].values() if p["direction"] == direction
    )
    if same_dir >= MAX_DIRECTIONAL:
        return False, "max_directional"

    # Cash floor check — estimate position value from ATR + stop distance
    equity = calculate_equity(portfolio, current_prices)
    risk_usd = equity * (RISK_PER_TRADE_PCT / 100.0)
    atr_val = entry.get("atr_val", 0.0)
    stop_atr_mult = entry.get("stop_atr_mult", 2.0)
    current_price = current_prices.get(sym, 0.0)

    if atr_val > 0 and current_price > 0:
        stop_dist = atr_val * stop_atr_mult
        if stop_dist > 0:
            est_units = risk_usd / stop_dist
            est_position_value = est_units * current_price
        else:
            est_position_value = risk_usd * 5
    else:
        est_position_value = risk_usd * 5  # fallback: ~5x leverage assumption

    required_floor = equity * CASH_FLOOR_PCT
    if portfolio["cash"] - est_position_value < required_floor:
        return False, "cash_floor"

    return True, "ok"


# ============================================================================
# POSITION ENTRY
# ============================================================================

def execute_entry(
    portfolio: dict,
    entry: dict,
    open_price: float,
    current_prices: dict,
) -> bool:
    """
    Open a new position at open_price.
    Deducts position value from cash.
    Returns True if position was opened.
    """
    sym = entry["symbol"]
    tf = entry["timeframe"]
    direction = entry["direction"]
    atr_val = entry["atr_val"]
    stop_atr_mult = entry["stop_atr_mult"]
    t1_mult = entry["target1_atr_mult"]
    t2_mult = entry.get("target2_atr_mult")
    scale_out_pct = entry.get("scale_out_pct", 0.5)
    max_bars = entry.get("max_bars", 60)

    if direction == "LONG":
        stop = open_price - (atr_val * stop_atr_mult)
        target_1 = open_price + (atr_val * t1_mult)
        target_2 = open_price + (atr_val * t2_mult) if t2_mult else None
    else:
        stop = open_price + (atr_val * stop_atr_mult)
        target_1 = open_price - (atr_val * t1_mult)
        target_2 = open_price - (atr_val * t2_mult) if t2_mult else None

    risk_per_unit = abs(open_price - stop)
    if risk_per_unit <= 0:
        return False

    # 2% risk on current equity
    all_prices = dict(current_prices)
    all_prices[sym] = open_price
    equity = calculate_equity(portfolio, all_prices)
    risk_usd = equity * (RISK_PER_TRADE_PCT / 100.0)

    units = risk_usd / risk_per_unit
    position_value = units * open_price

    # Cap at available cash (no margin)
    if position_value > portfolio["cash"]:
        units = portfolio["cash"] / open_price
        position_value = portfolio["cash"]

    if units <= 0 or position_value <= 0:
        return False

    portfolio["cash"] -= position_value

    portfolio["positions"][sym] = {
        "symbol": sym,
        "timeframe": tf,
        "strategy_name": entry["strategy_name"],
        "strategy_pf": entry["strategy_pf"],
        "direction": direction,
        "entry_price": open_price,
        "entry_ts": entry.get("signal_ts", 0),
        "stop": stop,
        "original_stop": stop,
        "target_1": target_1,
        "target_2": target_2,
        "total_units": units,
        "remaining_units": units,
        "position_value": position_value,
        "realized_pnl": 0.0,
        "bars_held": 0,
        "t1_hit": False,
        "scale_out_pct": scale_out_pct,
        "max_bars": max_bars,
        "risk_usd": risk_usd,
    }
    return True


# ============================================================================
# POSITION MANAGEMENT
# ============================================================================

def manage_position(
    portfolio: dict,
    sym: str,
    candles: list,
    bar_idx: int,
) -> bool:
    """
    Manage open position for `sym` at bar bar_idx.
    Handles stop, T1 scale-out, T2, and max_bars timeout.
    Returns True if position was closed this bar.
    """
    pos = portfolio["positions"][sym]
    direction = pos["direction"]
    scale_out_pct = pos["scale_out_pct"]
    max_bars = pos["max_bars"]

    pos["bars_held"] += 1

    bar = candles[bar_idx]
    bar_high = bar["h"]
    bar_low = bar["l"]
    bar_close = bar["c"]

    closed = False

    if direction == "LONG":
        # Check stop
        if bar_low <= pos["stop"]:
            exit_price = pos["stop"]
            pnl = pos["remaining_units"] * (exit_price - pos["entry_price"])
            pos["realized_pnl"] += pnl
            pos["exit_price"] = exit_price
            pos["exit_reason"] = "STOP_BE" if pos["t1_hit"] else "STOP"
            closed = True

        # Check T1
        elif not pos["t1_hit"] and bar_high >= pos["target_1"]:
            close_units = pos["total_units"] * scale_out_pct
            partial_pnl = close_units * (pos["target_1"] - pos["entry_price"])
            pos["realized_pnl"] += partial_pnl
            pos["remaining_units"] -= close_units
            pos["t1_hit"] = True
            pos["stop"] = pos["entry_price"]  # move to breakeven
            # Return T1 proceeds to cash immediately
            portfolio["cash"] += close_units * pos["target_1"]

            if pos["target_2"] is None or pos["remaining_units"] < 0.0001:
                pos["exit_price"] = pos["target_1"]
                pos["exit_reason"] = "T1"
                closed = True

        # Check T2
        elif pos["t1_hit"] and pos["target_2"] is not None and bar_high >= pos["target_2"]:
            final_pnl = pos["remaining_units"] * (pos["target_2"] - pos["entry_price"])
            pos["realized_pnl"] += final_pnl
            pos["exit_price"] = pos["target_2"]
            pos["exit_reason"] = "T2"
            closed = True

    else:  # SHORT
        # Check stop
        if bar_high >= pos["stop"]:
            exit_price = pos["stop"]
            pnl = pos["remaining_units"] * (pos["entry_price"] - exit_price)
            pos["realized_pnl"] += pnl
            pos["exit_price"] = exit_price
            pos["exit_reason"] = "STOP_BE" if pos["t1_hit"] else "STOP"
            closed = True

        # Check T1
        elif not pos["t1_hit"] and bar_low <= pos["target_1"]:
            close_units = pos["total_units"] * scale_out_pct
            partial_pnl = close_units * (pos["entry_price"] - pos["target_1"])
            pos["realized_pnl"] += partial_pnl
            pos["remaining_units"] -= close_units
            pos["t1_hit"] = True
            pos["stop"] = pos["entry_price"]  # breakeven
            # Return T1 proceeds to cash (SHORT: 2*entry - T1)
            portfolio["cash"] += close_units * (2.0 * pos["entry_price"] - pos["target_1"])

            if pos["target_2"] is None or pos["remaining_units"] < 0.0001:
                pos["exit_price"] = pos["target_1"]
                pos["exit_reason"] = "T1"
                closed = True

        # Check T2
        elif pos["t1_hit"] and pos["target_2"] is not None and bar_low <= pos["target_2"]:
            final_pnl = pos["remaining_units"] * (pos["entry_price"] - pos["target_2"])
            pos["realized_pnl"] += final_pnl
            pos["exit_price"] = pos["target_2"]
            pos["exit_reason"] = "T2"
            closed = True

    # Max bars timeout
    if not closed and pos["bars_held"] >= max_bars:
        if direction == "LONG":
            pnl = pos["remaining_units"] * (bar_close - pos["entry_price"])
        else:
            pnl = pos["remaining_units"] * (pos["entry_price"] - bar_close)
        pos["realized_pnl"] += pnl
        pos["exit_price"] = bar_close
        pos["exit_reason"] = "MAX_BARS"
        closed = True

    if closed:
        pos["exit_ts"] = bar["t"]
        exit_price = pos["exit_price"]
        remaining = pos["remaining_units"]

        # Return remaining proceeds to cash
        if direction == "LONG":
            portfolio["cash"] += remaining * exit_price
        else:
            portfolio["cash"] += remaining * (2.0 * pos["entry_price"] - exit_price)

        # Build trade record
        entry_price = pos["entry_price"]
        risk_per_unit = abs(entry_price - pos["original_stop"])
        total_risk = pos["total_units"] * risk_per_unit
        r_achieved = (pos["realized_pnl"] / total_risk) if total_risk > 0 else 0.0

        portfolio["closed_trades"].append({
            "symbol": sym,
            "timeframe": pos["timeframe"],
            "strategy_name": pos["strategy_name"],
            "strategy_pf": pos["strategy_pf"],
            "direction": direction,
            "entry_price": round(entry_price, 6),
            "exit_price": round(exit_price, 6),
            "stop": round(pos["original_stop"], 6),
            "target_1": round(pos["target_1"], 6),
            "target_2": round(pos["target_2"], 6) if pos["target_2"] else None,
            "total_units": pos["total_units"],
            "pnl_usd": round(pos["realized_pnl"], 4),
            "r_achieved": round(r_achieved, 3),
            "exit_reason": pos["exit_reason"],
            "bars_held": pos["bars_held"],
            "t1_hit": pos["t1_hit"],
            "entry_ts": pos["entry_ts"],
            "exit_ts": pos["exit_ts"],
        })

        del portfolio["positions"][sym]
        return True

    return False


# ============================================================================
# MAIN SIMULATION
# ============================================================================

def run_simulation(capital: float, days: int, verbose: bool = False) -> dict:
    """
    Run the full portfolio backtest simulation over all graduated strategies.
    Returns a results dict with metrics, trade log, equity curve, and rejections.
    """
    sep = "═" * 62
    print(f"\n{sep}")
    print(f"  PORTFOLIO BACKTEST SIMULATOR")
    print(f"  Capital: ${capital:,.0f}  |  Period: {days} days")
    print(f"{sep}\n")

    # ── 1. Load graduated strategies ─────────────────────────────────
    strategies = load_graduated_strategies()
    print(f"  Loaded {len(strategies)} graduated strategies")

    strats_by_pair = defaultdict(list)
    for s in strategies:
        strats_by_pair[(s["symbol"], s["timeframe"])].append(s)

    unique_pairs = sorted(strats_by_pair.keys())
    print(f"  Unique (symbol, timeframe) pairs: {len(unique_pairs)}\n")

    # ── 2. Load data for each pair ────────────────────────────────────
    print("  Loading OHLCV + indicators...")
    data_by_pair = {}
    skipped_pairs = []

    for sym, tf in unique_pairs:
        result = load_pair_data(sym, tf, days, verbose=True)
        if result is None:
            skipped_pairs.append((sym, tf))
            strats_by_pair.pop((sym, tf), None)
        else:
            data_by_pair[(sym, tf)] = result

    loaded_pairs = list(data_by_pair.keys())

    if skipped_pairs:
        print(f"\n  Skipped {len(skipped_pairs)} pair(s) — insufficient OHLCV data:")
        for sym, tf in skipped_pairs:
            print(f"    - {sym} {tf}")

    total_strats = sum(len(v) for v in strats_by_pair.values())
    print(f"\n  Ready: {len(loaded_pairs)} pairs, {total_strats} strategies\n")

    # ── 3. Build global timeline ──────────────────────────────────────
    ts_to_pairs: dict[int, list] = defaultdict(list)
    for pair in loaded_pairs:
        for c in data_by_pair[pair]["candles"]:
            ts_to_pairs[c["t"]].append(pair)

    global_timeline = sorted(ts_to_pairs.keys())
    print(f"  Global timeline: {len(global_timeline):,} bars across all pairs")
    print(f"  Date range: {from_timestamp_utc(global_timeline[0]).strftime('%Y-%m-%d')} "
          f"→ {from_timestamp_utc(global_timeline[-1]).strftime('%Y-%m-%d')}\n")

    # ── 4. Portfolio state ────────────────────────────────────────────
    portfolio: dict = {
        "cash": capital,
        "starting_capital": capital,
        "positions": {},       # symbol → position dict
        "closed_trades": [],
        "equity_curve": [],    # [(ts, equity), ...]
        "rejected_signals": [],
    }

    pending_entries: dict = {}   # (sym, tf) → entry candidate
    last_prices: dict = {}       # sym → last seen close price

    equity_peak = capital
    max_concurrent = 0
    total_signals_fired = 0

    print("  Running simulation...\n")

    # ── 5. Walk the global timeline ───────────────────────────────────
    for ts in global_timeline:
        pairs_at_ts = ts_to_pairs[ts]

        # Update last seen close prices
        for sym, tf in pairs_at_ts:
            bar_idx = data_by_pair[(sym, tf)]["ts_to_idx"][ts]
            last_prices[sym] = data_by_pair[(sym, tf)]["candles"][bar_idx]["c"]

        # ── 5a. Execute pending entries at this bar's open ────────────
        entries_to_execute = []
        for sym, tf in pairs_at_ts:
            if (sym, tf) in pending_entries:
                bar_idx = data_by_pair[(sym, tf)]["ts_to_idx"][ts]
                open_price = data_by_pair[(sym, tf)]["candles"][bar_idx]["o"]
                entry = pending_entries.pop((sym, tf))
                entry["execute_open"] = open_price
                entries_to_execute.append(entry)

        # Prioritize by backtest profit factor (highest wins when slots limited)
        entries_to_execute.sort(key=lambda e: e["strategy_pf"], reverse=True)

        for entry in entries_to_execute:
            sym = entry["symbol"]
            if sym in portfolio["positions"]:
                portfolio["rejected_signals"].append({
                    "ts": ts,
                    "symbol": sym,
                    "timeframe": entry["timeframe"],
                    "strategy": entry["strategy_name"],
                    "reason": "symbol_occupied_at_execution",
                })
                continue

            ok, reason = can_enter(portfolio, entry, last_prices)
            if ok:
                opened = execute_entry(portfolio, entry, entry["execute_open"], last_prices)
                if opened and verbose:
                    dt = from_timestamp_utc(ts).strftime("%Y-%m-%d %H:%M")
                    print(f"  ENTRY  {sym:8s} {entry['timeframe']:3s} "
                          f"{entry['direction']:5s} @ {entry['execute_open']:.4f}  "
                          f"[{entry['strategy_name'][:38]}]  ({dt})")
            else:
                portfolio["rejected_signals"].append({
                    "ts": ts,
                    "symbol": sym,
                    "timeframe": entry["timeframe"],
                    "strategy": entry["strategy_name"],
                    "reason": reason,
                })

        # ── 5b. Manage open positions ─────────────────────────────────
        for sym, tf in pairs_at_ts:
            if sym in portfolio["positions"]:
                pos = portfolio["positions"][sym]
                if pos["timeframe"] == tf:
                    bar_idx = data_by_pair[(sym, tf)]["ts_to_idx"][ts]
                    was_closed = manage_position(
                        portfolio, sym, data_by_pair[(sym, tf)]["candles"], bar_idx
                    )
                    if was_closed and verbose:
                        trade = portfolio["closed_trades"][-1]
                        dt = from_timestamp_utc(ts).strftime("%Y-%m-%d %H:%M")
                        sign = "+" if trade["pnl_usd"] >= 0 else ""
                        print(f"  EXIT   {sym:8s} {tf:3s}  "
                              f"{sign}${trade['pnl_usd']:.2f}  "
                              f"[{trade['exit_reason']}]  ({dt})")

        # ── 5c. Evaluate signals — queue pending entries ──────────────
        for sym, tf in pairs_at_ts:
            # Skip if we already have a position on this symbol
            if sym in portfolio["positions"]:
                continue
            # Skip if already queued for this pair
            if (sym, tf) in pending_entries:
                continue

            strats = strats_by_pair.get((sym, tf), [])
            if not strats:
                continue

            bar_idx = data_by_pair[(sym, tf)]["ts_to_idx"][ts]
            if bar_idx < WARMUP_BARS:
                continue

            candles_list = data_by_pair[(sym, tf)]["candles"]
            if bar_idx + 1 >= len(candles_list):
                continue  # no next bar to enter on

            pair_data = data_by_pair[(sym, tf)]
            ctx = build_context(
                bar_idx,
                pair_data["candles"],
                pair_data["ind"],
                pair_data["deriv"],
            )

            atr_val = ctx.get("atr_14")
            if atr_val is None or atr_val <= 0:
                continue

            # Evaluate each strategy for this pair
            candidates = []
            for strat in strats:
                entry_signals = strat.get("entry_signals", [])
                entry_params = strat.get("entry_params", {})
                exclude_signals = strat.get("filters", {}).get("exclude_signals", [])

                if not entry_signals:
                    continue

                sig_results = evaluate_signals(ctx, entry_signals, entry_params)
                all_fired = all(sig_results.values())

                if all_fired and exclude_signals:
                    excl = evaluate_signals(ctx, exclude_signals, entry_params)
                    if any(excl.values()):
                        all_fired = False

                if all_fired:
                    candidates.append(strat)

            if not candidates:
                continue

            total_signals_fired += 1

            # Conflict resolution: highest PF strategy wins
            best = max(candidates, key=lambda s: s["backtest_metrics"]["profit_factor"])
            exit_cfg = best.get("exit", {})

            pending_entries[(sym, tf)] = {
                "symbol": sym,
                "timeframe": tf,
                "strategy_name": best["name"],
                "strategy_pf": best["backtest_metrics"]["profit_factor"],
                "direction": best["direction"],
                "atr_val": atr_val,
                "stop_atr_mult": exit_cfg.get("stop_atr_mult", 2.0),
                "target1_atr_mult": exit_cfg.get("target1_atr_mult", 3.0),
                "target2_atr_mult": exit_cfg.get("target2_atr_mult"),
                "scale_out_pct": exit_cfg.get("scale_out_pct", 0.5),
                "max_bars": exit_cfg.get("max_bars", 60),
                "signal_ts": ts,
            }

        # ── 5d. Equity snapshot ───────────────────────────────────────
        equity = calculate_equity(portfolio, last_prices)
        equity_peak = max(equity_peak, equity)
        portfolio["equity_curve"].append((ts, equity))

        n_open = len(portfolio["positions"])
        max_concurrent = max(max_concurrent, n_open)

        # Safety stop
        if equity < 500:
            print(f"\n  [WARN] Equity collapsed to ${equity:.2f} — stopping simulation.")
            break

    # ── 6. Force-close all remaining open positions ───────────────────
    open_syms = list(portfolio["positions"].keys())
    if open_syms:
        print(f"  Force-closing {len(open_syms)} open position(s) at end of data...")

    for sym in open_syms:
        pos = portfolio["positions"][sym]
        tf = pos["timeframe"]
        candles_list = data_by_pair[(sym, tf)]["candles"]
        last_bar = candles_list[-1]
        last_close = last_bar["c"]
        last_ts = last_bar["t"]
        direction = pos["direction"]

        # Compute final P&L on remaining units
        if direction == "LONG":
            pnl = pos["remaining_units"] * (last_close - pos["entry_price"])
        else:
            pnl = pos["remaining_units"] * (pos["entry_price"] - last_close)
        pos["realized_pnl"] += pnl
        pos["exit_price"] = last_close
        pos["exit_reason"] = "END_OF_DATA"
        pos["exit_ts"] = last_ts

        # Return remaining proceeds
        if direction == "LONG":
            portfolio["cash"] += pos["remaining_units"] * last_close
        else:
            portfolio["cash"] += pos["remaining_units"] * (
                2.0 * pos["entry_price"] - last_close
            )

        entry_price = pos["entry_price"]
        risk_per_unit = abs(entry_price - pos["original_stop"])
        total_risk = pos["total_units"] * risk_per_unit
        r_achieved = (pos["realized_pnl"] / total_risk) if total_risk > 0 else 0.0

        portfolio["closed_trades"].append({
            "symbol": sym,
            "timeframe": tf,
            "strategy_name": pos["strategy_name"],
            "strategy_pf": pos["strategy_pf"],
            "direction": direction,
            "entry_price": round(entry_price, 6),
            "exit_price": round(last_close, 6),
            "stop": round(pos["original_stop"], 6),
            "target_1": round(pos["target_1"], 6),
            "target_2": round(pos["target_2"], 6) if pos["target_2"] else None,
            "total_units": pos["total_units"],
            "pnl_usd": round(pos["realized_pnl"], 4),
            "r_achieved": round(r_achieved, 3),
            "exit_reason": "END_OF_DATA",
            "bars_held": pos["bars_held"],
            "t1_hit": pos["t1_hit"],
            "entry_ts": pos["entry_ts"],
            "exit_ts": last_ts,
        })
        del portfolio["positions"][sym]

    # ── 7. Compute and return metrics ─────────────────────────────────
    final_equity = portfolio["cash"]  # all positions closed

    return _compute_metrics(
        portfolio=portfolio,
        starting_capital=capital,
        final_equity=final_equity,
        equity_peak=equity_peak,
        max_concurrent=max_concurrent,
        total_signals_fired=total_signals_fired,
        total_strats=total_strats,
        skipped_pairs=skipped_pairs,
        days=days,
    )


# ============================================================================
# METRICS
# ============================================================================

def _compute_metrics(
    portfolio: dict,
    starting_capital: float,
    final_equity: float,
    equity_peak: float,
    max_concurrent: int,
    total_signals_fired: int,
    total_strats: int,
    skipped_pairs: list,
    days: int,
) -> dict:
    """Compute performance metrics from closed trades and equity curve."""
    trades = portfolio["closed_trades"]
    total_trades = len(trades)

    total_pnl = sum(t["pnl_usd"] for t in trades)
    total_return_pct = (final_equity / starting_capital - 1.0) * 100.0

    wins = [t for t in trades if t["pnl_usd"] > 0.01]
    losses = [t for t in trades if t["pnl_usd"] < -0.01]
    gross_profit = sum(t["pnl_usd"] for t in wins)
    gross_loss = sum(t["pnl_usd"] for t in losses)
    pf = abs(gross_profit / gross_loss) if gross_loss != 0 else (float("inf") if gross_profit > 0 else 0)
    win_rate = len(wins) / total_trades if total_trades > 0 else 0.0
    avg_r = sum(t["r_achieved"] for t in trades) / total_trades if total_trades > 0 else 0.0

    # Max drawdown from equity curve
    max_dd_usd = 0.0
    max_dd_pct = 0.0
    peak = starting_capital
    dd_start_ts = None
    longest_dd_days = 0
    current_dd_start = None

    for ts, eq in portfolio["equity_curve"]:
        if eq > peak:
            peak = eq
            if current_dd_start is not None:
                dd_bars = (ts - current_dd_start) / (1000 * 86400)
                longest_dd_days = max(longest_dd_days, dd_bars)
            current_dd_start = None
        else:
            dd = peak - eq
            dd_pct = (dd / peak * 100) if peak > 0 else 0.0
            if dd > max_dd_usd:
                max_dd_usd = dd
                dd_start_ts = ts
            if dd_pct > max_dd_pct:
                max_dd_pct = dd_pct
            if current_dd_start is None:
                current_dd_start = ts

    # Avg concurrent positions
    if portfolio["equity_curve"]:
        # Approximate from trade overlap — use a simpler approach: count bars in position
        avg_concurrent = 0.0
        if total_trades > 0:
            total_bars_held = sum(t["bars_held"] for t in trades)
            timeline_len = len(portfolio["equity_curve"])
            avg_concurrent = total_bars_held / timeline_len if timeline_len > 0 else 0.0
    else:
        avg_concurrent = 0.0

    # Per-strategy attribution
    strat_stats: dict = {}
    for t in trades:
        sn = t["strategy_name"]
        if sn not in strat_stats:
            strat_stats[sn] = {"trades": 0, "pnl_usd": 0.0, "wins": 0}
        strat_stats[sn]["trades"] += 1
        strat_stats[sn]["pnl_usd"] += t["pnl_usd"]
        if t["pnl_usd"] > 0:
            strat_stats[sn]["wins"] += 1

    top_strategies = sorted(
        strat_stats.items(), key=lambda x: x[1]["pnl_usd"], reverse=True
    )[:10]

    # Per-symbol attribution
    sym_stats: dict = {}
    for t in trades:
        sym = t["symbol"]
        if sym not in sym_stats:
            sym_stats[sym] = {"trades": 0, "pnl_usd": 0.0, "wins": 0}
        sym_stats[sym]["trades"] += 1
        sym_stats[sym]["pnl_usd"] += t["pnl_usd"]
        if t["pnl_usd"] > 0:
            sym_stats[sym]["wins"] += 1

    top_symbols = sorted(
        sym_stats.items(), key=lambda x: x[1]["pnl_usd"], reverse=True
    )[:10]

    # Monthly breakdown
    monthly: dict = {}
    for t in trades:
        if t["exit_ts"]:
            dt = from_timestamp_utc(t["exit_ts"])
            month_key = dt.strftime("%Y-%m")
            if month_key not in monthly:
                monthly[month_key] = {"pnl_usd": 0.0, "trades": 0}
            monthly[month_key]["pnl_usd"] += t["pnl_usd"]
            monthly[month_key]["trades"] += 1

    # Rejection breakdown
    rejection_counts: dict = {}
    for r in portfolio["rejected_signals"]:
        reason = r["reason"]
        rejection_counts[reason] = rejection_counts.get(reason, 0) + 1

    # Exit reason breakdown
    exit_reasons: dict = {}
    for t in trades:
        r = t["exit_reason"]
        exit_reasons[r] = exit_reasons.get(r, 0) + 1

    # Daily equity curve (downsample for JSON output)
    daily_equity: list = []
    seen_days: set = set()
    for ts, eq in portfolio["equity_curve"]:
        day = from_timestamp_utc(ts).strftime("%Y-%m-%d")
        if day not in seen_days:
            seen_days.add(day)
            daily_equity.append({"date": day, "equity": round(eq, 2)})

    return {
        "starting_capital": starting_capital,
        "final_equity": round(final_equity, 2),
        "total_return_pct": round(total_return_pct, 2),
        "total_pnl_usd": round(total_pnl, 2),
        "profit_factor": round(pf, 2) if pf != float("inf") else 999.0,
        "win_rate": round(win_rate, 3),
        "avg_r": round(avg_r, 3),
        "total_trades": total_trades,
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "max_drawdown_usd": round(max_dd_usd, 2),
        "max_drawdown_pct": round(max_dd_pct, 2),
        "longest_drawdown_days": round(longest_dd_days, 1),
        "max_concurrent_positions": max_concurrent,
        "avg_concurrent_positions": round(avg_concurrent, 2),
        "total_signals_fired": total_signals_fired,
        "total_rejections": len(portfolio["rejected_signals"]),
        "rejection_breakdown": rejection_counts,
        "exit_reason_breakdown": exit_reasons,
        "strategies_loaded": total_strats,
        "pairs_skipped": [f"{s} {t}" for s, t in skipped_pairs],
        "days": days,
        "top_strategies": [
            {
                "name": name,
                "trades": stats["trades"],
                "wins": stats["wins"],
                "pnl_usd": round(stats["pnl_usd"], 2),
            }
            for name, stats in top_strategies
        ],
        "top_symbols": [
            {
                "symbol": sym,
                "trades": stats["trades"],
                "wins": stats["wins"],
                "pnl_usd": round(stats["pnl_usd"], 2),
            }
            for sym, stats in top_symbols
        ],
        "monthly_breakdown": [
            {"month": k, "pnl_usd": round(v["pnl_usd"], 2), "trades": v["trades"]}
            for k, v in sorted(monthly.items())
        ],
        "daily_equity": daily_equity,
        "trade_log": portfolio["closed_trades"],
        "rejection_log": portfolio["rejected_signals"][:500],  # cap for file size
    }


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================

def format_report(m: dict) -> str:
    """Format the metrics dict into a human-readable report string."""
    sep = "═" * 62
    cap = m["starting_capital"]
    eq = m["final_equity"]
    ret = m["total_return_pct"]
    sign = "+" if ret >= 0 else ""

    lines = [
        sep,
        f"  PORTFOLIO BACKTEST — ${cap:,.0f} starting capital — {m['days']} days",
        sep,
        "",
        "  PERFORMANCE",
        f"    Starting capital:      ${cap:>12,.2f}",
        f"    Final equity:          ${eq:>12,.2f}",
        f"    Total return:          {sign}{ret:>10.1f}%",
        f"    Total P&L:             ${m['total_pnl_usd']:>+12,.2f}",
        f"    Profit factor:         {m['profit_factor']:>12.2f}",
        f"    Win rate:              {m['win_rate']*100:>11.1f}%",
        f"    Avg R per trade:       {m['avg_r']:>12.2f}",
        f"    Total trades:          {m['total_trades']:>12}",
        f"    Wins / Losses:         {m['winning_trades']} / {m['losing_trades']}",
        "",
        "  RISK",
        f"    Max drawdown:          ${m['max_drawdown_usd']:>10,.2f}  ({m['max_drawdown_pct']:.1f}%)",
        f"    Longest drawdown:      {m['longest_drawdown_days']:>10.0f} days",
        f"    Max concurrent pos:    {m['max_concurrent_positions']:>12}",
        f"    Avg concurrent pos:    {m['avg_concurrent_positions']:>12.1f}",
        "",
        "  SIGNAL STATS",
        f"    Strategies loaded:     {m['strategies_loaded']:>12}",
        f"    Signals fired:         {m['total_signals_fired']:>12}",
        f"    Rejections:            {m['total_rejections']:>12}",
    ]

    if m["rejection_breakdown"]:
        for reason, count in sorted(m["rejection_breakdown"].items(), key=lambda x: -x[1]):
            lines.append(f"      {reason:<30} {count:>5}")

    lines += [
        "",
        "  EXIT REASONS",
    ]
    for reason, count in sorted(m["exit_reason_breakdown"].items(), key=lambda x: -x[1]):
        lines.append(f"    {reason:<30} {count:>5}")

    if m["top_strategies"]:
        lines += ["", "  TOP 10 STRATEGIES BY P&L"]
        for i, s in enumerate(m["top_strategies"], 1):
            pnl_sign = "+" if s["pnl_usd"] >= 0 else ""
            lines.append(
                f"    {i:>2}. {s['name'][:44]:<44} "
                f"{s['trades']:>3} trades  {pnl_sign}${s['pnl_usd']:>8,.2f}"
            )

    if m["top_symbols"]:
        lines += ["", "  TOP 10 SYMBOLS BY P&L"]
        for i, s in enumerate(m["top_symbols"], 1):
            pnl_sign = "+" if s["pnl_usd"] >= 0 else ""
            lines.append(
                f"    {i:>2}. {s['symbol']:<10}  "
                f"{s['trades']:>3} trades  {pnl_sign}${s['pnl_usd']:>8,.2f}"
            )

    if m["monthly_breakdown"]:
        lines += ["", "  MONTHLY P&L BREAKDOWN"]
        for row in m["monthly_breakdown"]:
            pnl_sign = "+" if row["pnl_usd"] >= 0 else ""
            lines.append(
                f"    {row['month']}:  {pnl_sign}${row['pnl_usd']:>8,.2f}  ({row['trades']} trades)"
            )

    lines += ["", sep]
    return "\n".join(lines)


# ============================================================================
# SAVE OUTPUT
# ============================================================================

def save_results(metrics: dict, output_json: bool) -> tuple[str, str | None]:
    """Save markdown report and optionally JSON. Returns (md_path, json_path|None)."""
    today = datetime.now().strftime("%Y%m%d")
    md_path = RESULTS_DIR / f"portfolio_sim_{today}.md"
    json_path = RESULTS_DIR / f"portfolio_sim_{today}.json" if output_json else None

    report = format_report(metrics)
    md_path.write_text(report)

    if json_path:
        json_path.write_text(json.dumps(metrics, indent=2, default=str))

    return str(md_path), str(json_path) if json_path else None


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Portfolio-level backtest simulator")
    sub = parser.add_subparsers(dest="command")

    run_cmd = sub.add_parser("run", help="Run the portfolio simulation")
    run_cmd.add_argument("--capital", type=float, default=10000.0, help="Starting capital (default: 10000)")
    run_cmd.add_argument("--days", type=int, default=180, help="Backtest period in days (default: 180)")
    run_cmd.add_argument("--json", action="store_true", help="Output JSON results file")
    run_cmd.add_argument("--verbose", action="store_true", help="Print every entry and exit")

    args = parser.parse_args()

    if args.command == "run":
        metrics = run_simulation(
            capital=args.capital,
            days=args.days,
            verbose=args.verbose,
        )

        report = format_report(metrics)
        print(report)

        md_path, json_path = save_results(metrics, output_json=args.json)
        print(f"\n  Saved: {md_path}")
        if json_path:
            print(f"  Saved: {json_path}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
