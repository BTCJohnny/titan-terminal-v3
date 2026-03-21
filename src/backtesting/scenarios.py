#!/usr/bin/env python3
"""
Titan Terminal v2 — Scenario Library
======================================
54 trading scenarios grouped by thesis type.
Each scenario has a clear hypothesis for WHY it should work.

Usage:
    python3 src/backtesting/scenarios.py list                 # List all scenarios
    python3 src/backtesting/scenarios.py show A1              # Show scenario details
    python3 src/backtesting/scenarios.py show --all           # Show all with full params
    python3 src/backtesting/scenarios.py sweep A1             # Show sweep variants
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# SCENARIO DEFINITIONS
# ============================================================================

SCENARIOS = [
    # ───── A. CONTRARIAN ─────
    {
        "name": "A1: Crowded Long Fade",
        "description": "Short when longs are overleveraged and RSI overbought — cascade risk",
        "direction": "SHORT",
        "entry_signals": ["funding_extreme_positive", "ls_crowd_long", "rsi_overbought"],
        "entry_params": {"funding_extreme_pos": 0.0003, "ls_crowd_long": 1.8, "rsi_ob": 70},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 60},
        "filters": {}
    },
    {
        "name": "A2: Crowded Short Squeeze",
        "description": "Long when shorts are overleveraged and RSI oversold — squeeze fuel",
        "direction": "LONG",
        "entry_signals": ["funding_extreme_negative", "ls_crowd_short", "rsi_oversold"],
        "entry_params": {"funding_extreme_neg": -0.0003, "ls_crowd_short": 0.55, "rsi_os": 30},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 60},
        "filters": {}
    },
    {
        "name": "A3: Long Liq Cascade Bounce",
        "description": "Buy after massive long liquidations — cascade overshoots fair value",
        "direction": "LONG",
        "entry_signals": ["liq_cascade_long", "rsi_oversold"],
        "entry_params": {"liq_cascade_usd": 100_000_000, "rsi_os": 35},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 2.5, "target2_atr_mult": 5.0, "scale_out_pct": 0.5, "max_bars": 40},
        "filters": {}
    },
    {
        "name": "A4: Fear & Greed Extreme Fear Buy",
        "description": "Contrarian long at extreme fear — market oversold on sentiment",
        "direction": "LONG",
        "entry_signals": ["fear_greed_extreme_fear"],
        "entry_params": {"fg_fear": 20},
        "exit": {"stop_atr_mult": 2.5, "target1_atr_mult": 4.0, "target2_atr_mult": 8.0, "scale_out_pct": 0.5, "max_bars": 90},
        "filters": {}
    },

    # ───── B. MOMENTUM ─────
    {
        "name": "B1: ETF Inflow Momentum",
        "description": "Long when institutional money flowing in via ETFs + trend confirmed",
        "direction": "LONG",
        "entry_signals": ["etf_inflow_streak", "coinbase_premium_positive", "trend_bullish"],
        "entry_params": {"etf_streak": 3, "cb_premium_pos": 0.0005},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 80},
        "filters": {}
    },
    {
        "name": "B2: OI Breakout Long",
        "description": "Long when OI surging + ADX confirms trend + volume spike — real momentum",
        "direction": "LONG",
        "entry_signals": ["oi_surge", "adx_strong_trend", "volume_surge"],
        "entry_params": {"oi_surge_pct": 5.0, "adx_strong": 25, "vol_surge": 1.5},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 2.5, "target2_atr_mult": 5.0, "scale_out_pct": 0.5, "max_bars": 40},
        "filters": {"exclude_signals": ["trend_bearish"]}
    },
    {
        "name": "B3: OI Breakout Short",
        "description": "Short when OI surging + strong bearish trend + volume — breakdown momentum",
        "direction": "SHORT",
        "entry_signals": ["oi_surge", "adx_strong_trend", "trend_bearish", "volume_surge"],
        "entry_params": {"oi_surge_pct": 5.0, "adx_strong": 25, "vol_surge": 1.5},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 2.5, "target2_atr_mult": 5.0, "scale_out_pct": 0.5, "max_bars": 40},
        "filters": {}
    },

    # ───── C. DIVERGENCE ─────
    {
        "name": "C1: OI Accumulation",
        "description": "Long when OI building while price dips — someone loading quietly",
        "direction": "LONG",
        "entry_signals": ["oi_price_divergence_bullish", "rsi_oversold"],
        "entry_params": {"rsi_os": 35},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 60},
        "filters": {}
    },
    {
        "name": "C2: OI Distribution",
        "description": "Short when leverage building on rising price — fragile rally",
        "direction": "SHORT",
        "entry_signals": ["oi_price_divergence_bearish", "rsi_overbought"],
        "entry_params": {"rsi_ob": 65},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 60},
        "filters": {}
    },
    {
        "name": "C3: Smart Money Divergence",
        "description": "Follow top traders when they lean opposite to the crowd",
        "direction": "LONG",
        "entry_signals": ["top_trader_divergence", "ls_crowd_short"],
        "entry_params": {},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 60},
        "filters": {}
    },

    # ───── D. REGIME-BASED ─────
    {
        "name": "D1: Volatility Squeeze Breakout",
        "description": "BB squeeze + no trend + OI building = coiled spring. Direction TBD.",
        "direction": "LONG",
        "entry_signals": ["bb_squeeze", "adx_weak_trend", "oi_surge"],
        "entry_params": {"bb_squeeze_pct": 0.20, "adx_weak": 20, "oi_surge_pct": 3.0},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 40},
        "filters": {}
    },
    {
        "name": "D2: Trend Mean Reversion Short",
        "description": "In bearish regime, short RSI overbought bounces + OBV divergence",
        "direction": "SHORT",
        "entry_signals": ["trend_bearish", "rsi_overbought", "obv_divergence_bearish"],
        "entry_params": {"rsi_ob": 65},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 2.0, "target2_atr_mult": 4.0, "scale_out_pct": 0.5, "max_bars": 30},
        "filters": {}
    },

    # ───── E. DATA-INFORMED (2-signal combos from Phase 1 winners) ─────
    # Thresholds calibrated from 180-day derivatives distributions:
    #   ls_crowd_long = 1.9 (BTC p50 — above-median long positioning)
    #   oi_surge_pct = 2.0 (BTC/ETH p75 — fires ~20-25% of days)
    #   Funding excluded (max 0.0001 in data, original 0.0003 unreachable)

    # === CROSS-ASSET SHORTS (worked on both BTC and ETH in Phase 1) ===

    {
        "name": "E1: MACD Rollover + Death Cross",
        "description": "MACD bearish cross in a confirmed downtrend — momentum aligns with regime",
        "direction": "SHORT",
        "entry_signals": ["macd_bearish_cross", "trend_bearish"],
        "entry_params": {},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 60},
        "filters": {}
    },
    {
        "name": "E2: MACD Rollover + Crowd Long",
        "description": "MACD bearish cross when crowd is long — timing + positioning alignment",
        "direction": "SHORT",
        "entry_signals": ["macd_bearish_cross", "ls_crowd_long"],
        "entry_params": {"ls_crowd_long": 1.9},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 60},
        "filters": {}
    },
    {
        "name": "E3: BB Upper Touch + Death Cross",
        "description": "Price hits upper BB in a bearish regime — overbought in downtrend",
        "direction": "SHORT",
        "entry_signals": ["bb_touch_upper", "trend_bearish"],
        "entry_params": {},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 2.5, "target2_atr_mult": 5.0, "scale_out_pct": 0.5, "max_bars": 45},
        "filters": {}
    },
    {
        "name": "E4: BB Upper + Crowd Long",
        "description": "Price at BB upper when crowd is positioned long — distribution fade",
        "direction": "SHORT",
        "entry_signals": ["bb_touch_upper", "ls_crowd_long"],
        "entry_params": {"ls_crowd_long": 1.9},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 2.5, "target2_atr_mult": 5.0, "scale_out_pct": 0.5, "max_bars": 45},
        "filters": {}
    },
    {
        "name": "E5: Death Cross + Crowd Long",
        "description": "Bearish regime + crowd positioned wrong — regime filter + crowd fade",
        "direction": "SHORT",
        "entry_signals": ["trend_bearish", "ls_crowd_long"],
        "entry_params": {"ls_crowd_long": 1.9},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 60},
        "filters": {}
    },
    {
        "name": "E6: MACD Rollover + OBV Divergence",
        "description": "Momentum rolling over + volume confirms distribution — strongest TA short",
        "direction": "SHORT",
        "entry_signals": ["macd_bearish_cross", "obv_divergence_bearish"],
        "entry_params": {},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 2.5, "target2_atr_mult": 5.0, "scale_out_pct": 0.5, "max_bars": 45},
        "filters": {}
    },

    # === ETH-SPECIFIC LONGS (OI-driven, only worked on ETH in Phase 1) ===

    {
        "name": "E7: OI Surge + BB Squeeze (ETH)",
        "description": "New money entering compressed volatility — breakout fuel accumulating",
        "direction": "LONG",
        "entry_signals": ["oi_surge", "bb_squeeze"],
        "entry_params": {"oi_surge_pct": 2.0, "bb_squeeze_pct": 0.25},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 40},
        "filters": {}
    },
    {
        "name": "E8: OI Surge + RSI Oversold (ETH)",
        "description": "New money entering while price oversold — bounce with fuel",
        "direction": "LONG",
        "entry_signals": ["oi_surge", "rsi_oversold"],
        "entry_params": {"oi_surge_pct": 2.0, "rsi_os": 35},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 50},
        "filters": {}
    },
    {
        "name": "E9: OI Surge Standalone (ETH)",
        "description": "Pure OI surge signal — ETH Phase 1 showed PF 4.92 standalone",
        "direction": "LONG",
        "entry_signals": ["oi_surge"],
        "entry_params": {"oi_surge_pct": 2.0},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 60},
        "filters": {}
    },
    {
        "name": "E10: OI Div Bullish + RSI Oversold (ETH)",
        "description": "OI building while price drops + oversold — accumulation bounce",
        "direction": "LONG",
        "entry_signals": ["oi_price_divergence_bullish", "rsi_oversold"],
        "entry_params": {"rsi_os": 35},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 50},
        "filters": {}
    },

    # === TIGHTER SHORT ENTRIES (higher conviction, from BTC winners) ===

    {
        "name": "E11: Triple Short (MACD + Death Cross + Crowd Long)",
        "description": "All three BTC short signals aligned — highest conviction",
        "direction": "SHORT",
        "entry_signals": ["macd_bearish_cross", "trend_bearish", "ls_crowd_long"],
        "entry_params": {"ls_crowd_long": 1.9},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 50},
        "filters": {}
    },
    {
        "name": "E12: RSI OB Short + Death Cross (ETH)",
        "description": "RSI overbought in bearish regime — ETH Phase 1 showed PF 2.30 on RSI OB",
        "direction": "SHORT",
        "entry_signals": ["rsi_overbought", "trend_bearish"],
        "entry_params": {"rsi_ob": 70},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 2.5, "target2_atr_mult": 5.0, "scale_out_pct": 0.5, "max_bars": 40},
        "filters": {}
    },

    # ───── F. MEAN REVERSION ─────
    # Based on the thesis mean reversion setup type: fade extreme overextensions,
    # target BB middle band, tight stops beyond the extreme.

    {
        "name": "F1: Oversold Bounce (Uptrend)",
        "description": "BB lower touch + RSI oversold in a bullish regime — buy the dip in an uptrend",
        "direction": "LONG",
        "entry_signals": ["bb_touch_lower", "rsi_oversold", "trend_bullish"],
        "entry_params": {"rsi_os": 30},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 2.0, "target2_atr_mult": 4.0, "scale_out_pct": 0.5, "max_bars": 30},
        "filters": {}
    },
    {
        "name": "F2: Oversold Bounce (Any Regime)",
        "description": "BB lower touch + RSI oversold — pure mean reversion, no regime filter",
        "direction": "LONG",
        "entry_signals": ["bb_touch_lower", "rsi_oversold"],
        "entry_params": {"rsi_os": 25},
        "exit": {"stop_atr_mult": 2.0, "target2_atr_mult": 3.5, "scale_out_pct": 0.5, "max_bars": 25},
        "filters": {}
    },
    {
        "name": "F3: Overbought Fade (Downtrend)",
        "description": "BB upper touch + RSI overbought in bearish regime — sell the rip in a downtrend",
        "direction": "SHORT",
        "entry_signals": ["bb_touch_upper", "rsi_overbought", "trend_bearish"],
        "entry_params": {"rsi_ob": 70},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 2.0, "target2_atr_mult": 4.0, "scale_out_pct": 0.5, "max_bars": 30},
        "filters": {}
    },
    {
        "name": "F4: Accumulation Bounce",
        "description": "BB lower + OBV bullish divergence — oversold but smart money buying",
        "direction": "LONG",
        "entry_signals": ["bb_touch_lower", "obv_divergence_bullish"],
        "entry_params": {},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 2.5, "target2_atr_mult": 5.0, "scale_out_pct": 0.5, "max_bars": 40},
        "filters": {}
    },
    {
        "name": "F5: Distribution Fade",
        "description": "BB upper + OBV bearish divergence — overbought with hidden selling",
        "direction": "SHORT",
        "entry_signals": ["bb_touch_upper", "obv_divergence_bearish"],
        "entry_params": {},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 2.5, "target2_atr_mult": 5.0, "scale_out_pct": 0.5, "max_bars": 40},
        "filters": {}
    },
    {
        "name": "F6: Fear Oversold Bounce",
        "description": "Extreme fear + BB lower — sentiment and price both at extremes",
        "direction": "LONG",
        "entry_signals": ["fear_greed_extreme_fear", "bb_touch_lower"],
        "entry_params": {"fg_fear": 20},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 45},
        "filters": {}
    },
    {
        "name": "F7: RSI Extreme Oversold Snap",
        "description": "RSI < 20 standalone — extreme oversold, mechanical bounce territory",
        "direction": "LONG",
        "entry_signals": ["rsi_oversold"],
        "entry_params": {"rsi_os": 20},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 2.0, "target2_atr_mult": 4.0, "scale_out_pct": 0.5, "max_bars": 20},
        "filters": {}
    },
    {
        "name": "F8: RSI Extreme Overbought Fade",
        "description": "RSI > 80 standalone — extreme overbought, mechanical pullback",
        "direction": "SHORT",
        "entry_signals": ["rsi_overbought"],
        "entry_params": {"rsi_ob": 80},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 2.0, "target2_atr_mult": 4.0, "scale_out_pct": 0.5, "max_bars": 20},
        "filters": {}
    },

    # ───── G. CONFLUENCE (3-4 signal high-conviction combos) ─────
    # The hypothesis: more independent signals aligned = higher win rate,
    # fewer trades but better expectancy per trade.

    {
        "name": "G1: Triple Buy (MACD + OBV + RSI)",
        "description": "MACD bullish cross + OBV accumulation + oversold — three independent signals aligned",
        "direction": "LONG",
        "entry_signals": ["macd_bullish_cross", "obv_divergence_bullish", "rsi_oversold"],
        "entry_params": {"rsi_os": 35},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 60},
        "filters": {}
    },
    {
        "name": "G2: Momentum Continuation Long",
        "description": "MACD bullish + golden cross + volume surge — trend continuation with fuel",
        "direction": "LONG",
        "entry_signals": ["macd_bullish_cross", "trend_bullish", "volume_surge"],
        "entry_params": {"vol_surge": 1.5},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 50},
        "filters": {}
    },
    {
        "name": "G3: Quad Short (MACD + OBV + Trend + Crowd)",
        "description": "All four short signals — maximum conviction, rare but deadly",
        "direction": "SHORT",
        "entry_signals": ["macd_bearish_cross", "obv_divergence_bearish", "trend_bearish", "ls_crowd_long"],
        "entry_params": {"ls_crowd_long": 1.9},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 3.0, "target2_atr_mult": 7.0, "scale_out_pct": 0.5, "max_bars": 50},
        "filters": {}
    },
    {
        "name": "G4: Derivatives Distribution Short",
        "description": "Extreme funding + crowded longs + OBV divergence — derivatives confirm distribution",
        "direction": "SHORT",
        "entry_signals": ["funding_extreme_positive", "ls_crowd_long", "obv_divergence_bearish"],
        "entry_params": {"funding_extreme_pos": 0.0003, "ls_crowd_long": 1.8},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 60},
        "filters": {}
    },
    {
        "name": "G5: Derivatives Squeeze Long",
        "description": "Extreme negative funding + crowded shorts + OBV accumulation — squeeze with smart money",
        "direction": "LONG",
        "entry_signals": ["funding_extreme_negative", "ls_crowd_short", "obv_divergence_bullish"],
        "entry_params": {"funding_extreme_neg": -0.0003, "ls_crowd_short": 0.55},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 60},
        "filters": {}
    },
    {
        "name": "G6: Compressed Breakout Bull",
        "description": "BB squeeze + MACD bullish cross + golden cross — volatility expansion in uptrend",
        "direction": "LONG",
        "entry_signals": ["bb_squeeze", "macd_bullish_cross", "trend_bullish"],
        "entry_params": {"bb_squeeze_pct": 0.20},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 40},
        "filters": {}
    },
    {
        "name": "G7: Compressed Breakdown Bear",
        "description": "BB squeeze + MACD bearish cross + death cross — volatility expansion in downtrend",
        "direction": "SHORT",
        "entry_signals": ["bb_squeeze", "macd_bearish_cross", "trend_bearish"],
        "entry_params": {"bb_squeeze_pct": 0.20},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 40},
        "filters": {}
    },
    {
        "name": "G8: Triple Energy Buildup",
        "description": "OI surge + volume surge + BB squeeze — all energy indicators say explosion imminent",
        "direction": "LONG",
        "entry_signals": ["oi_surge", "volume_surge", "bb_squeeze"],
        "entry_params": {"oi_surge_pct": 3.0, "vol_surge": 1.5, "bb_squeeze_pct": 0.25},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 35},
        "filters": {}
    },
    {
        "name": "G9: Short Squeeze Exhaustion Fade",
        "description": "Massive short liquidations + RSI overbought — squeeze done, fade the overshoot",
        "direction": "SHORT",
        "entry_signals": ["liq_cascade_short", "rsi_overbought"],
        "entry_params": {"liq_cascade_usd": 100_000_000, "rsi_ob": 75},
        "exit": {"stop_atr_mult": 1.5, "target1_atr_mult": 2.0, "target2_atr_mult": 4.0, "scale_out_pct": 0.5, "max_bars": 30},
        "filters": {}
    },
    {
        "name": "G10: Smart Money Accumulation Dip",
        "description": "Top traders diverge from crowd + OI building on dip + RSI oversold — institutional loading",
        "direction": "LONG",
        "entry_signals": ["top_trader_divergence", "oi_price_divergence_bullish", "rsi_oversold"],
        "entry_params": {"rsi_os": 35},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 60},
        "filters": {}
    },
    {
        "name": "G11: MACD Bullish + Golden Cross",
        "description": "MACD momentum turning up in established uptrend — trend continuation",
        "direction": "LONG",
        "entry_signals": ["macd_bullish_cross", "trend_bullish"],
        "entry_params": {},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 60},
        "filters": {}
    },
    {
        "name": "G12: MACD Bullish + ADX Strong",
        "description": "MACD momentum turning up in strong trend — confirmed trend acceleration",
        "direction": "LONG",
        "entry_signals": ["macd_bullish_cross", "adx_strong_trend"],
        "entry_params": {"adx_strong": 25},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 50},
        "filters": {}
    },

    # ───── H. SENTIMENT (fear/greed combos) ─────
    # Fear & Greed extremes + technical or derivatives confirmation.

    {
        "name": "H1: Greed Top Short (Sentiment + RSI)",
        "description": "Extreme greed + RSI overbought — sentiment and momentum both exhausted",
        "direction": "SHORT",
        "entry_signals": ["fear_greed_extreme_greed", "rsi_overbought"],
        "entry_params": {"fg_greed": 80},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 60},
        "filters": {}
    },
    {
        "name": "H2: Greed Distribution Short",
        "description": "Extreme greed + OBV bearish divergence — euphoric crowd, smart money exiting",
        "direction": "SHORT",
        "entry_signals": ["fear_greed_extreme_greed", "obv_divergence_bearish"],
        "entry_params": {"fg_greed": 80},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 60},
        "filters": {}
    },
    {
        "name": "H3: Double Contrarian Short (Greed + Crowd)",
        "description": "Extreme greed + crowded longs — two independent contrarian sell signals",
        "direction": "SHORT",
        "entry_signals": ["fear_greed_extreme_greed", "ls_crowd_long"],
        "entry_params": {"fg_greed": 80, "ls_crowd_long": 1.8},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 60},
        "filters": {}
    },
    {
        "name": "H4: Fear Accumulation Long",
        "description": "Extreme fear + OBV bullish divergence — panicking crowd, smart money buying",
        "direction": "LONG",
        "entry_signals": ["fear_greed_extreme_fear", "obv_divergence_bullish"],
        "entry_params": {"fg_fear": 20},
        "exit": {"stop_atr_mult": 2.5, "target1_atr_mult": 4.0, "target2_atr_mult": 8.0, "scale_out_pct": 0.5, "max_bars": 90},
        "filters": {}
    },
    {
        "name": "H5: Double Contrarian Long (Fear + Crowd)",
        "description": "Extreme fear + crowded shorts — two independent contrarian buy signals",
        "direction": "LONG",
        "entry_signals": ["fear_greed_extreme_fear", "ls_crowd_short"],
        "entry_params": {"fg_fear": 20, "ls_crowd_short": 0.55},
        "exit": {"stop_atr_mult": 2.5, "target1_atr_mult": 4.0, "target2_atr_mult": 8.0, "scale_out_pct": 0.5, "max_bars": 90},
        "filters": {}
    },
    {
        "name": "H6: Greed Standalone Short",
        "description": "Extreme greed standalone — contrarian fade at sentiment peak",
        "direction": "SHORT",
        "entry_signals": ["fear_greed_extreme_greed"],
        "entry_params": {"fg_greed": 80},
        "exit": {"stop_atr_mult": 2.5, "target1_atr_mult": 4.0, "target2_atr_mult": 8.0, "scale_out_pct": 0.5, "max_bars": 90},
        "filters": {}
    },

    # ───── I. INSTITUTIONAL (ETF + Coinbase premium combos) ─────
    # Institutional flow signals combined with technical confirmation.

    {
        "name": "I1: Full Institutional Bull",
        "description": "ETF inflows + OI surge + golden cross — institutions, leverage, and regime aligned",
        "direction": "LONG",
        "entry_signals": ["etf_inflow_streak", "oi_surge", "trend_bullish"],
        "entry_params": {"etf_streak": 3, "oi_surge_pct": 3.0},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 80},
        "filters": {}
    },
    {
        "name": "I2: ETF Dip Buy",
        "description": "ETF inflows continuing while RSI oversold — institutions buying the dip",
        "direction": "LONG",
        "entry_signals": ["etf_inflow_streak", "rsi_oversold"],
        "entry_params": {"etf_streak": 3, "rsi_os": 35},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 60},
        "filters": {}
    },
    {
        "name": "I3: Coinbase Momentum Long",
        "description": "Coinbase premium + MACD bullish + volume surge — US institutional buying + momentum",
        "direction": "LONG",
        "entry_signals": ["coinbase_premium_positive", "macd_bullish_cross", "volume_surge"],
        "entry_params": {"cb_premium_pos": 0.0005, "vol_surge": 1.5},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 50},
        "filters": {}
    },
    {
        "name": "I4: Coinbase Accumulation",
        "description": "Coinbase premium + OBV bullish divergence — US institutions accumulating on dip",
        "direction": "LONG",
        "entry_signals": ["coinbase_premium_positive", "obv_divergence_bullish"],
        "entry_params": {"cb_premium_pos": 0.0005},
        "exit": {"stop_atr_mult": 2.0, "target1_atr_mult": 3.0, "target2_atr_mult": 6.0, "scale_out_pct": 0.5, "max_bars": 60},
        "filters": {}
    },
]


# ============================================================================
# BIDIRECTIONAL VARIANTS
# ============================================================================

def get_all_scenarios() -> list:
    """Return all scenarios including bidirectional duplicates."""
    all_scenarios = []
    # Scenarios that should get a flipped direction variant
    bidirectional = {
        "C3: Smart Money Divergence",
        "D1: Volatility Squeeze Breakout",
        "G8: Triple Energy Buildup",   # Could break up or down
        "G12: MACD Bullish + ADX Strong",  # Strong trend could be either direction
    }
    for s in SCENARIOS:
        all_scenarios.append(s)
        if s["name"] in bidirectional:
            variant = _deep_copy_strategy(s)
            variant["name"] = s["name"] + " (SHORT)" if s["direction"] == "LONG" else s["name"] + " (LONG)"
            variant["direction"] = "SHORT" if s["direction"] == "LONG" else "LONG"
            # Flip crowd signals
            flips = {
                "ls_crowd_short": "ls_crowd_long",
                "ls_crowd_long": "ls_crowd_short",
                "macd_bullish_cross": "macd_bearish_cross",
                "macd_bearish_cross": "macd_bullish_cross",
                "trend_bullish": "trend_bearish",
                "trend_bearish": "trend_bullish",
                "obv_divergence_bullish": "obv_divergence_bearish",
                "obv_divergence_bearish": "obv_divergence_bullish",
                "rsi_oversold": "rsi_overbought",
                "rsi_overbought": "rsi_oversold",
                "funding_extreme_positive": "funding_extreme_negative",
                "funding_extreme_negative": "funding_extreme_positive",
            }
            variant["entry_signals"] = [
                flips.get(sig, sig) for sig in s["entry_signals"]
            ]
            # Flip param keys
            new_params = {}
            param_flips = {
                "rsi_os": "rsi_ob", "rsi_ob": "rsi_os",
                "ls_crowd_long": "ls_crowd_short", "ls_crowd_short": "ls_crowd_long",
                "funding_extreme_pos": "funding_extreme_neg", "funding_extreme_neg": "funding_extreme_pos",
            }
            for k, v in variant.get("entry_params", {}).items():
                new_key = param_flips.get(k, k)
                # Flip sign for funding
                if k.startswith("funding_extreme"):
                    v = -abs(v) if "neg" in new_key else abs(v)
                new_params[new_key] = v
            variant["entry_params"] = new_params
            all_scenarios.append(variant)
    return all_scenarios


# ============================================================================
# PARAMETER SWEEP
# ============================================================================

def generate_sweep_variants(scenario: dict) -> list:
    """Generate parameter sweep variants for a scenario.

    Varies each numeric param across 5 steps: 0.5x, 0.75x, 1.0x, 1.25x, 1.5x.
    Returns list of variant dicts.
    """
    variants = [scenario]  # Include base scenario

    base_params = scenario.get("entry_params", {})
    base_exit = scenario.get("exit", {})

    # Sweep entry params
    for key, base_val in base_params.items():
        if isinstance(base_val, (int, float)):
            for mult in [0.5, 0.75, 1.25, 1.5]:
                variant = _deep_copy_strategy(scenario)
                variant["entry_params"][key] = round(base_val * mult, 6)
                variant["name"] = f"{scenario['name']} [{key}={variant['entry_params'][key]}]"
                variants.append(variant)

    # Sweep exit params (stop and target multipliers)
    for key in ["stop_atr_mult", "target1_atr_mult", "target2_atr_mult"]:
        base_val = base_exit.get(key)
        if base_val:
            for mult in [0.5, 0.75, 1.25, 1.5]:
                variant = _deep_copy_strategy(scenario)
                variant["exit"][key] = round(base_val * mult, 2)
                variant["name"] = f"{scenario['name']} [{key}={variant['exit'][key]}]"
                variants.append(variant)

    return variants


def _deep_copy_strategy(strategy: dict) -> dict:
    """Deep copy a strategy dict."""
    return json.loads(json.dumps(strategy))


# ============================================================================
# LOOKUP HELPERS
# ============================================================================

def find_scenario(query: str) -> dict | None:
    """Find a scenario by name prefix (e.g., 'A1', 'B2', 'D1')."""
    query_upper = query.upper().strip()
    for s in get_all_scenarios():
        name_upper = s["name"].upper()
        # Match by prefix like "A1" or full name
        if name_upper.startswith(query_upper) or query_upper in name_upper:
            return s
    return None


# ============================================================================
# CLI
# ============================================================================

def cmd_list(args):
    """List all scenarios."""
    scenarios = get_all_scenarios()
    print(f"\nScenarios ({len(scenarios)})")
    print("=" * 72)

    current_category = None
    for s in scenarios:
        # Category header
        prefix = s["name"][:1]
        cat_map = {"A": "CONTRARIAN", "B": "MOMENTUM", "C": "DIVERGENCE", "D": "REGIME-BASED", "E": "DATA-INFORMED", "F": "MEAN REVERSION", "G": "CONFLUENCE", "H": "SENTIMENT", "I": "INSTITUTIONAL"}
        cat = cat_map.get(prefix, "OTHER")
        if cat != current_category:
            current_category = cat
            print(f"\n  ── {cat} ──")

        direction = s["direction"]
        n_signals = len(s.get("entry_signals", []))
        short_tag = " (SHORT)" if "(SHORT)" in s["name"] else ""
        base_name = s["name"].replace(" (SHORT)", "")
        print(f"  {base_name:40s} {direction:5s}  {n_signals} signals{short_tag}")

    print()


def cmd_show(args):
    """Show scenario details."""
    if args.all:
        for s in get_all_scenarios():
            _print_scenario(s)
        return

    if not args.query:
        print("Provide a scenario ID (e.g., A1) or --all")
        return

    scenario = find_scenario(args.query)
    if not scenario:
        print(f"Scenario not found: {args.query}")
        return

    _print_scenario(scenario)


def cmd_sweep(args):
    """Show sweep variants for a scenario."""
    if not args.query:
        print("Provide a scenario ID (e.g., A1)")
        return

    scenario = find_scenario(args.query)
    if not scenario:
        print(f"Scenario not found: {args.query}")
        return

    variants = generate_sweep_variants(scenario)
    print(f"\nSweep variants for {scenario['name']} ({len(variants)} total)")
    print("=" * 72)

    for i, v in enumerate(variants):
        tag = " (BASE)" if i == 0 else ""
        print(f"  {i+1:3d}. {v['name']}{tag}")

    print()


def _print_scenario(s: dict):
    """Print a single scenario in detail."""
    print(f"\n{'=' * 62}")
    print(f"  {s['name']}")
    print(f"  {s.get('description', '')}")
    print(f"{'=' * 62}")
    print(f"  Direction: {s['direction']}")
    print(f"  Entry signals: {', '.join(s.get('entry_signals', []))}")
    if s.get("entry_params"):
        print(f"  Entry params: {json.dumps(s['entry_params'])}")
    if s.get("exit"):
        e = s["exit"]
        print(f"  Exit: stop {e.get('stop_atr_mult', '?')} ATR | T1 {e.get('target1_atr_mult', '?')} ATR | T2 {e.get('target2_atr_mult', '?')} ATR | scale {e.get('scale_out_pct', '?')*100:.0f}% | max {e.get('max_bars', '?')} bars")
    if s.get("filters", {}).get("exclude_signals"):
        print(f"  Excludes: {', '.join(s['filters']['exclude_signals'])}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Titan Scenario Library")
    subparsers = parser.add_subparsers(dest="command")

    # List
    subparsers.add_parser("list", help="List all scenarios")

    # Show
    show_parser = subparsers.add_parser("show", help="Show scenario details")
    show_parser.add_argument("query", nargs="?", help="Scenario ID (e.g., A1)")
    show_parser.add_argument("--all", action="store_true", help="Show all scenarios")

    # Sweep
    sweep_parser = subparsers.add_parser("sweep", help="Show sweep variants")
    sweep_parser.add_argument("query", help="Scenario ID (e.g., A1)")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return

    cmd_map = {"list": cmd_list, "show": cmd_show, "sweep": cmd_sweep}
    cmd_map[args.command](args)


if __name__ == "__main__":
    main()
