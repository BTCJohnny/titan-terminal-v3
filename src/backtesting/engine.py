#!/usr/bin/env python3
"""
Titan Terminal v2 — Backtest Engine
====================================
Walks historical OHLCV + derivatives data, evaluates signal conditions,
simulates trades with scale-out at T1, and reports performance metrics.

Pure Python computation — zero API calls.

Usage:
    python3 src/backtesting/engine.py run --symbol BTC --timeframe 4h --days 180 --strategy '{...}'
    python3 src/backtesting/engine.py run --symbol BTC --timeframe 4h --days 180 --strategy-file strategies/crowded.json
    python3 src/backtesting/engine.py coverage --symbol BTC
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

from src.analysis.indicators import (
    get_cached_data, calculate_rsi, calculate_macd,
    calculate_bollinger_bands, calculate_atr, calculate_adx,
    calculate_sma, calculate_obv, from_timestamp_utc
)
from src.backtesting.signals import SIGNAL_REGISTRY

# Database paths
OHLCV_DB = PROJECT_ROOT / "data" / "titan_data.db"
INTEL_DB = PROJECT_ROOT / "data" / "titan_intelligence.db"

# Warm-up bars required (SMA 200 needs 199 prior bars)
WARMUP_BARS = 200


# ============================================================================
# DATA LOADING
# ============================================================================

def load_candles(symbol: str, timeframe: str, days: int) -> list:
    """Load OHLCV candles from titan_data.db."""
    return get_cached_data(symbol, timeframe, days=days)


def load_derivatives(symbol: str, start_date: str, end_date: str) -> dict:
    """
    Load derivatives snapshots from titan_intelligence.db.
    Returns dict keyed by date string (YYYY-MM-DD) for fast lookup.
    """
    if not INTEL_DB.exists():
        return {}

    conn = sqlite3.connect(INTEL_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM derivatives_snapshots
        WHERE symbol = ? AND timestamp_utc >= ? AND timestamp_utc <= ?
        ORDER BY timestamp_utc ASC
    """, (symbol.upper(), start_date, end_date + "T23:59:59"))

    rows = cursor.fetchall()
    conn.close()

    # Key by date — if multiple rows per day, use the latest
    by_date = {}
    for row in rows:
        ts = row["timestamp_utc"]
        # Extract date from ISO timestamp (e.g., "2026-03-19T00:00:00+00:00")
        date_str = ts[:10]
        by_date[date_str] = dict(row)

    return by_date


# ============================================================================
# INDICATOR PRE-COMPUTATION
# ============================================================================

def precompute_indicators(candles: list) -> dict:
    """
    Compute all indicators for the full candle series at once.
    Returns dict of parallel arrays indexed by bar position.
    """
    closes = [c["c"] for c in candles]
    volumes = [c["v"] for c in candles]
    n = len(candles)

    # Core indicators
    rsi = calculate_rsi(closes, 14)
    macd = calculate_macd(closes, 12, 26, 9)
    bb = calculate_bollinger_bands(closes, 20, 2.0)
    atr = calculate_atr(candles, 14)
    adx_data = calculate_adx(candles, 14)
    obv = calculate_obv(candles)

    sma_20 = calculate_sma(closes, 20)
    sma_50 = calculate_sma(closes, 50)
    sma_200 = calculate_sma(closes, 200)

    # OBV SMA(20)
    obv_floats = [float(v) if v is not None else 0.0 for v in obv]
    obv_sma_20 = calculate_sma(obv_floats, 20)

    # Volume SMA(20)
    vol_sma_20 = calculate_sma(volumes, 20)

    # BB width and BB width percentile
    bb_widths = []
    for i in range(n):
        if bb["upper"][i] is not None and bb["lower"][i] is not None and bb["middle"][i] is not None and bb["middle"][i] != 0:
            bb_widths.append((bb["upper"][i] - bb["lower"][i]) / bb["middle"][i])
        else:
            bb_widths.append(None)

    bb_width_percentiles = [None] * n
    for i in range(n):
        if bb_widths[i] is None:
            continue
        window = []
        for j in range(max(0, i - 99), i + 1):
            if bb_widths[j] is not None:
                window.append(bb_widths[j])
        if len(window) > 1:
            rank = sum(1 for w in window if w < bb_widths[i])
            bb_width_percentiles[i] = rank / len(window)
        else:
            bb_width_percentiles[i] = 0.5

    return {
        "rsi": rsi,
        "macd_line": macd["macd"],
        "macd_signal": macd["signal"],
        "macd_histogram": macd["histogram"],
        "bb_upper": bb["upper"],
        "bb_middle": bb["middle"],
        "bb_lower": bb["lower"],
        "bb_widths": bb_widths,
        "bb_width_percentiles": bb_width_percentiles,
        "atr": atr,
        "adx": adx_data["adx"],
        "plus_di": adx_data["plus_di"],
        "minus_di": adx_data["minus_di"],
        "sma_20": sma_20,
        "sma_50": sma_50,
        "sma_200": sma_200,
        "obv": obv,
        "obv_sma_20": obv_sma_20,
        "vol_sma_20": vol_sma_20,
    }


def build_context(i: int, candles: list, ind: dict, deriv_by_date: dict) -> dict:
    """
    Build the data context dict for bar i.
    """
    c = candles[i]
    closes = [x["c"] for x in candles]

    # Basic bar data
    ctx = {
        "close": c["c"],
        "open": c["o"],
        "high": c["h"],
        "low": c["l"],
        "volume": c["v"],
        "timestamp": c["t"],
    }

    # TA indicators
    ctx["rsi_14"] = ind["rsi"][i] if i < len(ind["rsi"]) else None
    ctx["macd_line"] = ind["macd_line"][i] if i < len(ind["macd_line"]) else None
    ctx["macd_signal"] = ind["macd_signal"][i] if i < len(ind["macd_signal"]) else None
    ctx["macd_histogram"] = ind["macd_histogram"][i] if i < len(ind["macd_histogram"]) else None
    ctx["bb_upper"] = ind["bb_upper"][i] if i < len(ind["bb_upper"]) else None
    ctx["bb_middle"] = ind["bb_middle"][i] if i < len(ind["bb_middle"]) else None
    ctx["bb_lower"] = ind["bb_lower"][i] if i < len(ind["bb_lower"]) else None
    ctx["bb_width"] = ind["bb_widths"][i] if i < len(ind["bb_widths"]) else None
    ctx["bb_width_percentile"] = ind["bb_width_percentiles"][i] if i < len(ind["bb_width_percentiles"]) else None
    ctx["adx"] = ind["adx"][i] if i < len(ind["adx"]) else None
    ctx["plus_di"] = ind["plus_di"][i] if i < len(ind["plus_di"]) else None
    ctx["minus_di"] = ind["minus_di"][i] if i < len(ind["minus_di"]) else None
    ctx["atr_14"] = ind["atr"][i] if i < len(ind["atr"]) else None
    ctx["sma_20"] = ind["sma_20"][i] if i < len(ind["sma_20"]) else None
    ctx["sma_50"] = ind["sma_50"][i] if i < len(ind["sma_50"]) else None
    ctx["sma_200"] = ind["sma_200"][i] if i < len(ind["sma_200"]) else None
    ctx["obv"] = ind["obv"][i] if i < len(ind["obv"]) else None
    ctx["obv_sma_20"] = ind["obv_sma_20"][i] if i < len(ind["obv_sma_20"]) else None

    # OBV slope: (OBV - OBV[20]) / |OBV[20]|
    if i >= 20 and ind["obv"][i] is not None and ind["obv"][i - 20] is not None:
        prev_obv = ind["obv"][i - 20]
        if prev_obv != 0:
            ctx["obv_slope"] = (ind["obv"][i] - prev_obv) / abs(prev_obv)
        else:
            ctx["obv_slope"] = 0.0
    else:
        ctx["obv_slope"] = None

    # Derived TA
    if ctx["close"] is not None and ctx["sma_50"] is not None and ctx["sma_50"] != 0:
        ctx["price_vs_sma50"] = (ctx["close"] - ctx["sma_50"]) / ctx["sma_50"]
    else:
        ctx["price_vs_sma50"] = None

    if ctx["close"] is not None and ctx["sma_200"] is not None and ctx["sma_200"] != 0:
        ctx["price_vs_sma200"] = (ctx["close"] - ctx["sma_200"]) / ctx["sma_200"]
    else:
        ctx["price_vs_sma200"] = None

    if ctx["close"] is not None and ctx["bb_upper"] is not None and ctx["bb_upper"] != 0:
        ctx["price_vs_bb_upper"] = (ctx["close"] - ctx["bb_upper"]) / ctx["bb_upper"]
    else:
        ctx["price_vs_bb_upper"] = None

    if ctx["close"] is not None and ctx["bb_lower"] is not None and ctx["bb_lower"] != 0:
        ctx["price_vs_bb_lower"] = (ctx["close"] - ctx["bb_lower"]) / ctx["bb_lower"]
    else:
        ctx["price_vs_bb_lower"] = None

    # Previous bar values
    if i >= 1:
        ctx["rsi_prev"] = ind["rsi"][i - 1] if i - 1 < len(ind["rsi"]) else None
        ctx["macd_histogram_prev"] = ind["macd_histogram"][i - 1] if i - 1 < len(ind["macd_histogram"]) else None
        ctx["close_prev"] = candles[i - 1]["c"]
    else:
        ctx["rsi_prev"] = None
        ctx["macd_histogram_prev"] = None
        ctx["close_prev"] = None

    # Volume ratio
    vol_sma = ind["vol_sma_20"][i] if i < len(ind["vol_sma_20"]) else None
    if vol_sma is not None and vol_sma > 0:
        ctx["volume_sma_20"] = vol_sma
        ctx["volume_ratio"] = c["v"] / vol_sma
    else:
        ctx["volume_sma_20"] = None
        ctx["volume_ratio"] = None

    # Price action lookback
    highs_window = [candles[j]["h"] for j in range(max(0, i - 19), i + 1)]
    lows_window = [candles[j]["l"] for j in range(max(0, i - 19), i + 1)]
    ctx["high_20"] = max(highs_window) if highs_window else None
    ctx["low_20"] = min(lows_window) if lows_window else None

    if i >= 5 and closes[i - 5] != 0:
        ctx["price_change_5"] = (closes[i] - closes[i - 5]) / closes[i - 5]
    else:
        ctx["price_change_5"] = None

    if i >= 20 and closes[i - 20] != 0:
        ctx["price_change_20"] = (closes[i] - closes[i - 20]) / closes[i - 20]
    else:
        ctx["price_change_20"] = None

    # Derivatives data (daily — lookup by date)
    bar_date = datetime.fromtimestamp(c["t"] / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    deriv = deriv_by_date.get(bar_date)

    if deriv:
        ctx["funding_rate_avg"] = deriv.get("funding_rate_avg")
        ctx["funding_bias"] = deriv.get("funding_bias")
        ctx["oi_usd"] = deriv.get("oi_usd")
        ctx["oi_change_24h_pct"] = deriv.get("oi_change_24h_pct")
        ctx["oi_trend"] = deriv.get("oi_trend")
        ctx["ls_global_ratio"] = deriv.get("ls_global_ratio")
        ctx["ls_global_long_pct"] = deriv.get("ls_global_long_pct")
        ctx["ls_top_account_ratio"] = deriv.get("ls_top_account_ratio")
        ctx["ls_top_position_ratio"] = deriv.get("ls_top_position_ratio")
        ctx["ls_smart_money_lean"] = deriv.get("ls_smart_money_lean")
        ctx["ls_extreme"] = bool(deriv.get("ls_extreme"))
        ctx["liq_24h_usd"] = deriv.get("liq_24h_usd")
        ctx["liq_long_24h_usd"] = deriv.get("liq_long_24h_usd")
        ctx["liq_short_24h_usd"] = deriv.get("liq_short_24h_usd")
        ctx["liq_ls_ratio"] = deriv.get("liq_ls_ratio")
        ctx["fear_greed_value"] = deriv.get("fear_greed_value")
        ctx["fear_greed_label"] = deriv.get("fear_greed_label")
        ctx["coinbase_premium_rate"] = deriv.get("coinbase_premium_rate")
        ctx["coinbase_premium_bias"] = deriv.get("coinbase_premium_bias")
        ctx["etf_latest_day_flow_usd"] = deriv.get("etf_latest_day_flow_usd")
        ctx["etf_weekly_net_flow_usd"] = deriv.get("etf_weekly_net_flow_usd")
        ctx["etf_streak_days"] = deriv.get("etf_streak_days")
        ctx["etf_bias"] = deriv.get("etf_bias")
    else:
        for key in [
            "funding_rate_avg", "funding_bias", "oi_usd", "oi_change_24h_pct",
            "oi_trend", "ls_global_ratio", "ls_global_long_pct",
            "ls_top_account_ratio", "ls_top_position_ratio", "ls_smart_money_lean",
            "ls_extreme", "liq_24h_usd", "liq_long_24h_usd", "liq_short_24h_usd",
            "liq_ls_ratio", "fear_greed_value", "fear_greed_label",
            "coinbase_premium_rate", "coinbase_premium_bias",
            "etf_latest_day_flow_usd", "etf_weekly_net_flow_usd",
            "etf_streak_days", "etf_bias",
        ]:
            ctx[key] = None

    # Derivatives lookback (previous day)
    prev_date = None
    if i >= 1:
        prev_date = datetime.fromtimestamp(candles[i - 1]["t"] / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    # For intraday timeframes, previous bar might be same day — find actual previous day
    if prev_date == bar_date and i >= 6:
        for back in range(2, min(i + 1, 50)):
            check_date = datetime.fromtimestamp(candles[i - back]["t"] / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            if check_date != bar_date:
                prev_date = check_date
                break

    prev_deriv = deriv_by_date.get(prev_date) if prev_date else None
    if prev_deriv:
        ctx["funding_rate_avg_prev"] = prev_deriv.get("funding_rate_avg")
        ctx["oi_usd_prev"] = prev_deriv.get("oi_usd")
        ctx["ls_global_ratio_prev"] = prev_deriv.get("ls_global_ratio")
        ctx["fear_greed_value_prev"] = prev_deriv.get("fear_greed_value")
    else:
        ctx["funding_rate_avg_prev"] = None
        ctx["oi_usd_prev"] = None
        ctx["ls_global_ratio_prev"] = None
        ctx["fear_greed_value_prev"] = None

    return ctx


# ============================================================================
# SIGNAL EVALUATION
# ============================================================================

def evaluate_signals(ctx: dict, signal_names: list, params: dict = None) -> dict:
    """Evaluate a list of signals against the context. Returns {name: bool}."""
    results = {}
    for name in signal_names:
        fn = SIGNAL_REGISTRY.get(name)
        if fn:
            results[name] = fn(ctx, params)
        else:
            results[name] = False
    return results


# ============================================================================
# BACKTEST ENGINE
# ============================================================================

def run_backtest(
    strategy: dict,
    symbol: str,
    timeframe: str = "4h",
    days: int = 180,
    initial_capital: float = 50000.0,
    risk_per_trade_pct: float = 2.0,
) -> dict:
    """
    Run a backtest for the given strategy against historical data.

    Returns a result dict with performance metrics and trade list.
    """
    name = strategy.get("name", "Unnamed")
    direction = strategy.get("direction", "LONG").upper()
    entry_signals = strategy.get("entry_signals", [])
    entry_params = strategy.get("entry_params", {})
    exit_cfg = strategy.get("exit", {})
    filters = strategy.get("filters", {})
    exclude_signals = filters.get("exclude_signals", [])

    stop_atr_mult = exit_cfg.get("stop_atr_mult", 2.0)
    t1_atr_mult = exit_cfg.get("target1_atr_mult", 3.0)
    t2_atr_mult = exit_cfg.get("target2_atr_mult", 6.0)
    scale_out_pct = exit_cfg.get("scale_out_pct", 0.5)
    max_bars = exit_cfg.get("max_bars", 60)

    # --- Load data ---
    candles = load_candles(symbol, timeframe, days=days + 60)  # extra buffer for warmup
    if len(candles) < WARMUP_BARS + 10:
        return {"error": f"Insufficient OHLCV data: {len(candles)} bars (need >{WARMUP_BARS})"}

    # Date range
    start_dt = from_timestamp_utc(candles[0]["t"])
    end_dt = from_timestamp_utc(candles[-1]["t"])
    start_date = start_dt.strftime("%Y-%m-%d")
    end_date = end_dt.strftime("%Y-%m-%d")

    # Load derivatives
    deriv_by_date = load_derivatives(symbol, start_date, end_date)
    deriv_days = len(deriv_by_date)

    # --- Pre-compute indicators ---
    ind = precompute_indicators(candles)

    # --- Walk bars ---
    capital = initial_capital
    trades = []
    position = None  # current open position or None
    equity_peak = initial_capital

    n = len(candles)

    for i in range(WARMUP_BARS, n):
        ctx = build_context(i, candles, ind, deriv_by_date)

        # --- Position management ---
        if position is not None:
            pos = position
            pos["bars_held"] += 1

            bar_high = candles[i]["h"]
            bar_low = candles[i]["l"]
            bar_close = candles[i]["c"]

            closed = False

            if direction == "LONG":
                # Check stop
                if bar_low <= pos["stop"]:
                    exit_price = pos["stop"]
                    pnl = pos["remaining_units"] * (exit_price - pos["entry_price"])
                    pos["realized_pnl"] += pnl
                    reason = "STOP" if not pos["t1_hit"] else "STOP_BE"
                    pos["scale_out_details"].append({
                        "price": exit_price, "pct": 1.0 - scale_out_pct if pos["t1_hit"] else 1.0,
                        "reason": reason
                    })
                    pos["exit_price"] = exit_price
                    pos["exit_reason"] = reason
                    closed = True

                # Check T1
                elif not pos["t1_hit"] and bar_high >= pos["target_1"]:
                    close_units = pos["total_units"] * scale_out_pct
                    partial_pnl = close_units * (pos["target_1"] - pos["entry_price"])
                    pos["realized_pnl"] += partial_pnl
                    pos["remaining_units"] -= close_units
                    pos["t1_hit"] = True
                    pos["stop"] = pos["entry_price"]  # move to breakeven
                    pos["scale_out_details"].append({
                        "price": pos["target_1"], "pct": scale_out_pct, "reason": "T1"
                    })

                    # If no T2 defined or remaining is ~0, close fully
                    if pos["target_2"] is None or pos["remaining_units"] < 0.0001:
                        pos["exit_price"] = pos["target_1"]
                        pos["exit_reason"] = "T1"
                        closed = True

                # Check T2 (after T1)
                elif pos["t1_hit"] and pos["target_2"] is not None and bar_high >= pos["target_2"]:
                    final_pnl = pos["remaining_units"] * (pos["target_2"] - pos["entry_price"])
                    pos["realized_pnl"] += final_pnl
                    pos["scale_out_details"].append({
                        "price": pos["target_2"], "pct": 1.0 - scale_out_pct, "reason": "T2"
                    })
                    pos["exit_price"] = pos["target_2"]
                    pos["exit_reason"] = "T2"
                    closed = True

            else:  # SHORT
                # Check stop
                if bar_high >= pos["stop"]:
                    exit_price = pos["stop"]
                    pnl = pos["remaining_units"] * (pos["entry_price"] - exit_price)
                    pos["realized_pnl"] += pnl
                    reason = "STOP" if not pos["t1_hit"] else "STOP_BE"
                    pos["scale_out_details"].append({
                        "price": exit_price, "pct": 1.0 - scale_out_pct if pos["t1_hit"] else 1.0,
                        "reason": reason
                    })
                    pos["exit_price"] = exit_price
                    pos["exit_reason"] = reason
                    closed = True

                # Check T1
                elif not pos["t1_hit"] and bar_low <= pos["target_1"]:
                    close_units = pos["total_units"] * scale_out_pct
                    partial_pnl = close_units * (pos["entry_price"] - pos["target_1"])
                    pos["realized_pnl"] += partial_pnl
                    pos["remaining_units"] -= close_units
                    pos["t1_hit"] = True
                    pos["stop"] = pos["entry_price"]  # breakeven
                    pos["scale_out_details"].append({
                        "price": pos["target_1"], "pct": scale_out_pct, "reason": "T1"
                    })

                    if pos["target_2"] is None or pos["remaining_units"] < 0.0001:
                        pos["exit_price"] = pos["target_1"]
                        pos["exit_reason"] = "T1"
                        closed = True

                # Check T2
                elif pos["t1_hit"] and pos["target_2"] is not None and bar_low <= pos["target_2"]:
                    final_pnl = pos["remaining_units"] * (pos["entry_price"] - pos["target_2"])
                    pos["realized_pnl"] += final_pnl
                    pos["scale_out_details"].append({
                        "price": pos["target_2"], "pct": 1.0 - scale_out_pct, "reason": "T2"
                    })
                    pos["exit_price"] = pos["target_2"]
                    pos["exit_reason"] = "T2"
                    closed = True

            # Check max bars
            if not closed and pos["bars_held"] >= max_bars:
                if direction == "LONG":
                    pnl = pos["remaining_units"] * (bar_close - pos["entry_price"])
                else:
                    pnl = pos["remaining_units"] * (pos["entry_price"] - bar_close)
                pos["realized_pnl"] += pnl
                pos["scale_out_details"].append({
                    "price": bar_close,
                    "pct": pos["remaining_units"] / pos["total_units"] if pos["total_units"] > 0 else 1.0,
                    "reason": "MAX_BARS"
                })
                pos["exit_price"] = bar_close
                pos["exit_reason"] = "MAX_BARS"
                closed = True

            if closed:
                pos["exit_bar"] = i
                pos["exit_date"] = from_timestamp_utc(candles[i]["t"]).strftime("%Y-%m-%d %H:%M")
                capital += pos["realized_pnl"]
                equity_peak = max(equity_peak, capital)
                _finalize_trade(pos, trades, direction)
                position = None

            continue  # skip entry check when holding a position

        # --- Entry check ---
        if not entry_signals:
            continue

        # Evaluate entry signals
        sig_results = evaluate_signals(ctx, entry_signals, entry_params)
        all_entry = all(sig_results.values())

        # Check exclusion filters
        if all_entry and exclude_signals:
            excl_results = evaluate_signals(ctx, exclude_signals, entry_params)
            if any(excl_results.values()):
                all_entry = False

        if not all_entry:
            continue

        # Entry triggers — execute at NEXT bar's open
        if i + 1 >= n:
            continue  # end of data

        atr_val = ctx.get("atr_14")
        if atr_val is None or atr_val <= 0:
            continue  # can't size without ATR

        entry_price = candles[i + 1]["o"]
        if entry_price <= 0:
            continue

        # Compute stops and targets
        if direction == "LONG":
            stop_price = entry_price - (atr_val * stop_atr_mult)
            target_1 = entry_price + (atr_val * t1_atr_mult)
            target_2 = entry_price + (atr_val * t2_atr_mult) if t2_atr_mult else None
        else:
            stop_price = entry_price + (atr_val * stop_atr_mult)
            target_1 = entry_price - (atr_val * t1_atr_mult)
            target_2 = entry_price - (atr_val * t2_atr_mult) if t2_atr_mult else None

        # Position sizing: 2% risk
        risk_usd = capital * (risk_per_trade_pct / 100.0)
        risk_per_unit = abs(entry_price - stop_price)
        if risk_per_unit <= 0:
            continue

        units = risk_usd / risk_per_unit
        position_value = units * entry_price

        if position_value > capital:
            continue  # insufficient capital

        position = {
            "entry_bar": i + 1,
            "entry_date": from_timestamp_utc(candles[i + 1]["t"]).strftime("%Y-%m-%d %H:%M"),
            "entry_price": entry_price,
            "stop": stop_price,
            "original_stop": stop_price,
            "target_1": target_1,
            "target_2": target_2,
            "total_units": units,
            "remaining_units": units,
            "realized_pnl": 0.0,
            "bars_held": 0,
            "t1_hit": False,
            "scale_out_details": [],
            "signals_at_entry": sig_results,
        }

    # --- Force-close any open position at end of data ---
    if position is not None:
        last_close = candles[-1]["c"]
        if direction == "LONG":
            pnl = position["remaining_units"] * (last_close - position["entry_price"])
        else:
            pnl = position["remaining_units"] * (position["entry_price"] - last_close)
        position["realized_pnl"] += pnl
        position["scale_out_details"].append({
            "price": last_close,
            "pct": position["remaining_units"] / position["total_units"] if position["total_units"] > 0 else 1.0,
            "reason": "END_OF_DATA"
        })
        position["exit_price"] = last_close
        position["exit_reason"] = "END_OF_DATA"
        position["exit_bar"] = n - 1
        position["exit_date"] = from_timestamp_utc(candles[-1]["t"]).strftime("%Y-%m-%d %H:%M")
        capital += position["realized_pnl"]
        _finalize_trade(position, trades, direction)
        position = None

    # --- Compute performance metrics ---
    return _compute_metrics(
        strategy_name=name,
        direction=direction,
        symbol=symbol,
        timeframe=timeframe,
        candles=candles,
        trades=trades,
        initial_capital=initial_capital,
        final_capital=capital,
        deriv_days=deriv_days,
        days=days,
        start_date=start_date,
        end_date=end_date,
    )


def _finalize_trade(pos: dict, trades: list, direction: str):
    """Convert a closed position into a trade record."""
    entry = pos["entry_price"]
    exit_p = pos["exit_price"]
    risk_per_unit = abs(entry - pos["original_stop"])

    if direction == "LONG":
        move_per_unit = exit_p - entry if pos["exit_reason"] != "T1" else 0
    else:
        move_per_unit = entry - exit_p if pos["exit_reason"] != "T1" else 0

    # For composite exits (T1 + something), the total pnl is already computed
    total_pnl = pos["realized_pnl"]

    # Calculate total PnL percentage relative to position value
    position_value = pos["total_units"] * entry
    pnl_pct = (total_pnl / position_value * 100) if position_value > 0 else 0

    # R achieved
    total_risk = pos["total_units"] * risk_per_unit
    r_achieved = (total_pnl / total_risk) if total_risk > 0 else 0

    trades.append({
        "entry_bar": pos["entry_bar"],
        "entry_date": pos["entry_date"],
        "entry_price": round(entry, 2),
        "direction": direction,
        "stop": round(pos["original_stop"], 2),
        "target_1": round(pos["target_1"], 2),
        "target_2": round(pos["target_2"], 2) if pos["target_2"] else None,
        "exit_price": round(exit_p, 2),
        "exit_date": pos["exit_date"],
        "exit_reason": pos["exit_reason"],
        "bars_held": pos["bars_held"],
        "pnl_usd": round(total_pnl, 2),
        "pnl_pct": round(pnl_pct, 2),
        "r_achieved": round(r_achieved, 2),
        "scale_out_details": pos["scale_out_details"],
        "signals_at_entry": pos["signals_at_entry"],
    })


def _compute_metrics(
    strategy_name, direction, symbol, timeframe, candles, trades,
    initial_capital, final_capital, deriv_days, days, start_date, end_date
) -> dict:
    """Compute full performance metrics from trade list."""
    total = len(trades)

    if total == 0:
        return {
            "strategy_name": strategy_name,
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "period": {"start": start_date, "end": end_date, "days": days, "bars": len(candles)},
            "data": {
                "ohlcv_bars": len(candles),
                "derivatives_days": deriv_days,
                "derivatives_coverage_pct": round(deriv_days / max(days, 1) * 100, 1),
            },
            "total_trades": 0,
            "wins": 0, "losses": 0, "breakeven": 0,
            "win_rate": 0,
            "total_pnl_usd": 0, "total_pnl_pct": 0,
            "gross_profit_usd": 0, "gross_loss_usd": 0,
            "profit_factor": 0,
            "avg_win_usd": 0, "avg_loss_usd": 0,
            "largest_win_usd": 0, "largest_loss_usd": 0,
            "expectancy_usd": 0,
            "max_drawdown_pct": 0, "max_drawdown_usd": 0,
            "avg_r_achieved": 0, "trades_above_3r": 0,
            "avg_bars_held": 0, "avg_win_bars": 0, "avg_loss_bars": 0,
            "trades": [],
        }

    wins = [t for t in trades if t["pnl_usd"] > 0.01]
    losses = [t for t in trades if t["pnl_usd"] < -0.01]
    breakevens = [t for t in trades if -0.01 <= t["pnl_usd"] <= 0.01]

    gross_profit = sum(t["pnl_usd"] for t in wins)
    gross_loss = sum(t["pnl_usd"] for t in losses)
    total_pnl = sum(t["pnl_usd"] for t in trades)

    profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else float("inf") if gross_profit > 0 else 0

    # Drawdown calculation — walk equity curve
    equity = initial_capital
    peak = initial_capital
    max_dd_usd = 0
    max_dd_pct = 0
    for t in trades:
        equity += t["pnl_usd"]
        peak = max(peak, equity)
        dd = peak - equity
        dd_pct = (dd / peak * 100) if peak > 0 else 0
        if dd > max_dd_usd:
            max_dd_usd = dd
        if dd_pct > max_dd_pct:
            max_dd_pct = dd_pct

    avg_r = sum(t["r_achieved"] for t in trades) / total

    return {
        "strategy_name": strategy_name,
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "direction": direction,
        "period": {
            "start": start_date,
            "end": end_date,
            "days": days,
            "bars": len(candles),
        },
        "data": {
            "ohlcv_bars": len(candles),
            "derivatives_days": deriv_days,
            "derivatives_coverage_pct": round(deriv_days / max(days, 1) * 100, 1),
        },
        "total_trades": total,
        "wins": len(wins),
        "losses": len(losses),
        "breakeven": len(breakevens),
        "win_rate": round(len(wins) / total, 3),

        "total_pnl_usd": round(total_pnl, 2),
        "total_pnl_pct": round(total_pnl / initial_capital * 100, 2),
        "gross_profit_usd": round(gross_profit, 2),
        "gross_loss_usd": round(gross_loss, 2),
        "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else "inf",
        "avg_win_usd": round(gross_profit / len(wins), 2) if wins else 0,
        "avg_loss_usd": round(gross_loss / len(losses), 2) if losses else 0,
        "largest_win_usd": round(max(t["pnl_usd"] for t in wins), 2) if wins else 0,
        "largest_loss_usd": round(min(t["pnl_usd"] for t in losses), 2) if losses else 0,
        "expectancy_usd": round(total_pnl / total, 2),

        "max_drawdown_pct": round(max_dd_pct, 2),
        "max_drawdown_usd": round(max_dd_usd, 2),
        "avg_r_achieved": round(avg_r, 2),
        "trades_above_3r": sum(1 for t in trades if t["r_achieved"] >= 3.0),

        "avg_bars_held": round(sum(t["bars_held"] for t in trades) / total, 1),
        "avg_win_bars": round(sum(t["bars_held"] for t in wins) / len(wins), 1) if wins else 0,
        "avg_loss_bars": round(sum(t["bars_held"] for t in losses) / len(losses), 1) if losses else 0,

        "trades": trades,
    }


# ============================================================================
# COVERAGE REPORT
# ============================================================================

def show_coverage(symbol: str):
    """Show data coverage available for backtesting."""
    symbol = symbol.upper()
    print(f"\n{symbol} Backtest Data Coverage:")

    # OHLCV by timeframe
    if not OHLCV_DB.exists():
        print("  No OHLCV database found.")
        return

    conn = sqlite3.connect(OHLCV_DB)
    cursor = conn.cursor()

    for tf in ["1h", "4h", "1d", "1w"]:
        cursor.execute("""
            SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
            FROM ohlcv WHERE symbol = ? AND timeframe = ?
        """, (symbol, tf))
        row = cursor.fetchone()
        count = row[0] or 0
        if count > 0:
            mn = from_timestamp_utc(row[1]).strftime("%Y-%m-%d")
            mx = from_timestamp_utc(row[2]).strftime("%Y-%m-%d")
            total_days = (from_timestamp_utc(row[2]) - from_timestamp_utc(row[1])).days
            print(f"  {tf:4s}  {count:5d} candles  [{mn} -> {mx}]  {total_days} days")
        else:
            print(f"  {tf:4s}  No data")

    conn.close()

    # Derivatives
    if INTEL_DB.exists():
        conn2 = sqlite3.connect(INTEL_DB)
        cursor2 = conn2.cursor()
        cursor2.execute("""
            SELECT COUNT(*), MIN(timestamp_utc), MAX(timestamp_utc)
            FROM derivatives_snapshots WHERE symbol = ?
        """, (symbol,))
        row2 = cursor2.fetchone()
        count2 = row2[0] or 0
        if count2 > 0:
            mn2 = row2[1][:10]
            mx2 = row2[2][:10]
            print(f"  Derivatives:  {count2} snapshots  [{mn2} -> {mx2}]")
        else:
            print(f"  Derivatives:  No data")
        conn2.close()

        # Overlap check with 4h
        conn3 = sqlite3.connect(OHLCV_DB)
        cursor3 = conn3.cursor()
        cursor3.execute("""
            SELECT MIN(timestamp), MAX(timestamp)
            FROM ohlcv WHERE symbol = ? AND timeframe = '4h'
        """, (symbol,))
        ohlcv_range = cursor3.fetchone()
        conn3.close()

        if ohlcv_range[0] and count2 > 0:
            ohlcv_start = from_timestamp_utc(ohlcv_range[0]).strftime("%Y-%m-%d")
            ohlcv_end = from_timestamp_utc(ohlcv_range[1]).strftime("%Y-%m-%d")
            overlap_start = max(ohlcv_start, mn2)
            overlap_end = min(ohlcv_end, mx2)
            if overlap_start <= overlap_end:
                from datetime import datetime as dt
                os_dt = dt.strptime(overlap_start, "%Y-%m-%d")
                oe_dt = dt.strptime(overlap_end, "%Y-%m-%d")
                overlap_days = (oe_dt - os_dt).days
                status = "sufficient for backtesting" if overlap_days >= 30 else "limited"
                print(f"  Overlap (4h + derivatives): {overlap_days} days — {'✓' if overlap_days >= 30 else '⚠'} {status}")
            else:
                print(f"  Overlap (4h + derivatives): 0 days — ⚠ no overlap")
    else:
        print(f"  Derivatives:  No database found")

    print()


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================

def format_result(result: dict) -> str:
    """Format backtest result as human-readable output."""
    if "error" in result:
        return f"\n  ❌ ERROR: {result['error']}\n"

    r = result
    direction = r.get("direction", "LONG")
    lines = []
    lines.append("")
    lines.append("=" * 62)
    lines.append(f"  📊 BACKTEST: {r['strategy_name']} ({direction})")
    lines.append(f"  {r['symbol']} {r['timeframe']} · {r['period']['days']} days · {r['period']['start']} → {r['period']['end']}")
    lines.append("=" * 62)

    # Data coverage
    d = r["data"]
    lines.append(f"\n  📦 DATA: {d['ohlcv_bars']} bars OHLCV · {d['derivatives_days']} days derivatives ({d['derivatives_coverage_pct']}% coverage)")

    if r["total_trades"] == 0:
        lines.append("\n  ⚠️  No trades triggered. Try relaxing signal conditions.")
        lines.append("=" * 62)
        return "\n".join(lines)

    # Performance
    lines.append(f"\n  📈 PERFORMANCE")
    lines.append(f"    Trades: {r['total_trades']} | Win rate: {r['win_rate']*100:.1f}% ({r['wins']}W / {r['losses']}L / {r['breakeven']}BE)")
    lines.append(f"    P&L: ${r['total_pnl_usd']:+,.2f} ({r['total_pnl_pct']:+.1f}%)")
    lines.append(f"    Profit factor: {r['profit_factor']} | Expectancy: ${r['expectancy_usd']:+,.2f}/trade")
    lines.append(f"    Avg win: ${r['avg_win_usd']:+,.2f} | Avg loss: ${r['avg_loss_usd']:+,.2f}")
    lines.append(f"    Largest win: ${r['largest_win_usd']:+,.2f} | Largest loss: ${r['largest_loss_usd']:+,.2f}")

    # Risk
    lines.append(f"\n  🛡️  RISK")
    lines.append(f"    Max drawdown: ${r['max_drawdown_usd']:,.2f} ({r['max_drawdown_pct']:.1f}%)")
    lines.append(f"    Avg R: {r['avg_r_achieved']:.2f} | Trades ≥3R: {r['trades_above_3r']}")
    lines.append(f"    Avg hold: {r['avg_bars_held']:.0f} bars | Win avg: {r['avg_win_bars']:.0f} | Loss avg: {r['avg_loss_bars']:.0f}")

    # Recent trades (last 5)
    if r["trades"]:
        lines.append(f"\n  📋 RECENT TRADES (last 5)")
        for t in r["trades"][-5:]:
            entry_s = f"${t['entry_price']:,.0f}" if t["entry_price"] >= 100 else f"${t['entry_price']:.2f}"
            exit_s = f"${t['exit_price']:,.0f}" if t["exit_price"] >= 100 else f"${t['exit_price']:.2f}"
            reason = t["exit_reason"]
            if t.get("scale_out_details") and len(t["scale_out_details"]) > 1:
                reasons = [s["reason"] for s in t["scale_out_details"]]
                reason = "+".join(dict.fromkeys(reasons))  # dedupe preserving order
            lines.append(
                f"    {t['entry_date'][:10]}  {t['direction']:5s}  {entry_s} → {exit_s}  "
                f"${t['pnl_usd']:+,.0f}  {reason:10s}  {t['bars_held']:3d} bars  {t['r_achieved']:+.1f}R"
            )

    lines.append("")
    lines.append("=" * 62)
    return "\n".join(lines)


# ============================================================================
# CLI
# ============================================================================

def cmd_run(args):
    """Run a backtest."""
    # Load strategy
    if args.strategy_file:
        path = Path(args.strategy_file)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if not path.exists():
            print(f"Strategy file not found: {path}")
            return
        with open(path) as f:
            strategy = json.load(f)
    elif args.strategy:
        try:
            strategy = json.loads(args.strategy)
        except json.JSONDecodeError as e:
            print(f"Invalid strategy JSON: {e}")
            return
    else:
        print("Provide --strategy (JSON string) or --strategy-file (path)")
        return

    result = run_backtest(
        strategy=strategy,
        symbol=args.symbol,
        timeframe=args.timeframe,
        days=args.days,
        initial_capital=args.capital,
        risk_per_trade_pct=args.risk,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_result(result))


def cmd_coverage(args):
    """Show data coverage for backtesting."""
    show_coverage(args.symbol)


def main():
    parser = argparse.ArgumentParser(description="Titan Backtest Engine")
    subparsers = parser.add_subparsers(dest="command")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a backtest")
    run_parser.add_argument("--symbol", required=True, help="Token symbol (e.g., BTC)")
    run_parser.add_argument("--timeframe", default="4h", help="Candle timeframe (default: 4h)")
    run_parser.add_argument("--days", type=int, default=180, help="Days of history (default: 180)")
    run_parser.add_argument("--strategy", help="Strategy as JSON string")
    run_parser.add_argument("--strategy-file", help="Path to strategy JSON file")
    run_parser.add_argument("--capital", type=float, default=50000.0, help="Initial capital (default: 50000)")
    run_parser.add_argument("--risk", type=float, default=2.0, help="Risk per trade %% (default: 2.0)")
    run_parser.add_argument("--json", action="store_true", help="Output raw JSON")
    run_parser.set_defaults(func=cmd_run)

    # Coverage command
    cov_parser = subparsers.add_parser("coverage", help="Show data coverage")
    cov_parser.add_argument("--symbol", required=True, help="Token symbol")
    cov_parser.set_defaults(func=cmd_coverage)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
