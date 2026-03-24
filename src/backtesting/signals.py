#!/usr/bin/env python3
"""
Titan Terminal v2 — Signal Library
===================================
Pure boolean signal functions for backtesting.
Each signal takes a pre-computed data context dict and returns True/False.

Usage:
    python3 src/backtesting/signals.py list           # List all signals
    python3 src/backtesting/signals.py list --ta       # TA signals only
    python3 src/backtesting/signals.py list --deriv    # Derivatives signals only
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# TA SIGNALS (computed from OHLCV + indicators)
# ============================================================================

def rsi_overbought(data, params=None) -> bool:
    """RSI above threshold. Default: 70"""
    threshold = (params or {}).get("rsi_ob", 70)
    return data.get("rsi_14") is not None and data["rsi_14"] >= threshold


def rsi_oversold(data, params=None) -> bool:
    """RSI below threshold. Default: 30"""
    threshold = (params or {}).get("rsi_os", 30)
    return data.get("rsi_14") is not None and data["rsi_14"] <= threshold


def macd_bullish_cross(data, params=None) -> bool:
    """MACD histogram crossed from negative to positive this bar."""
    hist = data.get("macd_histogram")
    prev = data.get("macd_histogram_prev")
    return hist is not None and prev is not None and hist > 0 and prev <= 0


def macd_bearish_cross(data, params=None) -> bool:
    """MACD histogram crossed from positive to negative this bar."""
    hist = data.get("macd_histogram")
    prev = data.get("macd_histogram_prev")
    return hist is not None and prev is not None and hist < 0 and prev >= 0


def bb_squeeze(data, params=None) -> bool:
    """BB width in lowest percentile (compressed volatility). Default: 20th pctile."""
    pct_threshold = (params or {}).get("bb_squeeze_pct", 0.20)
    pct = data.get("bb_width_percentile")
    return pct is not None and pct <= pct_threshold


def bb_touch_upper(data, params=None) -> bool:
    """Price at or above upper Bollinger Band."""
    return data.get("price_vs_bb_upper") is not None and data["price_vs_bb_upper"] >= 0


def bb_touch_lower(data, params=None) -> bool:
    """Price at or below lower Bollinger Band."""
    return data.get("price_vs_bb_lower") is not None and data["price_vs_bb_lower"] <= 0


def adx_strong_trend(data, params=None) -> bool:
    """ADX above threshold (strong trend). Default: 25"""
    threshold = (params or {}).get("adx_strong", 25)
    return data.get("adx") is not None and data["adx"] >= threshold


def adx_weak_trend(data, params=None) -> bool:
    """ADX below threshold (no trend / ranging). Default: 20"""
    threshold = (params or {}).get("adx_weak", 20)
    return data.get("adx") is not None and data["adx"] <= threshold


def trend_bullish(data, params=None) -> bool:
    """SMA 50 > SMA 200 (golden cross active)."""
    s50 = data.get("sma_50")
    s200 = data.get("sma_200")
    return s50 is not None and s200 is not None and s50 > s200


def trend_bearish(data, params=None) -> bool:
    """SMA 50 < SMA 200 (death cross active)."""
    s50 = data.get("sma_50")
    s200 = data.get("sma_200")
    return s50 is not None and s200 is not None and s50 < s200


def obv_divergence_bearish(data, params=None) -> bool:
    """Price rising over 20 bars but OBV declining — distribution."""
    pc = data.get("price_change_20")
    obv_s = data.get("obv_slope")
    return pc is not None and obv_s is not None and pc > 0.02 and obv_s < -0.02


def obv_divergence_bullish(data, params=None) -> bool:
    """Price falling over 20 bars but OBV rising — accumulation."""
    pc = data.get("price_change_20")
    obv_s = data.get("obv_slope")
    return pc is not None and obv_s is not None and pc < -0.02 and obv_s > 0.02


def volume_surge(data, params=None) -> bool:
    """Volume above X times average. Default: 1.5x"""
    threshold = (params or {}).get("vol_surge", 1.5)
    vr = data.get("volume_ratio")
    return vr is not None and vr >= threshold


# ============================================================================
# DERIVATIVES SIGNALS (computed from derivatives_snapshots)
# ============================================================================

def funding_extreme_positive(data, params=None) -> bool:
    """Funding rate extremely positive (longs paying heavily). Default: 0.008 (P90 of 180d data)"""
    threshold = (params or {}).get("funding_extreme_pos", 0.008)
    fr = data.get("funding_rate_avg")
    return fr is not None and fr >= threshold


def funding_extreme_negative(data, params=None) -> bool:
    """Funding rate extremely negative (shorts paying). Default: -0.01 (P10 of 180d data)"""
    threshold = (params or {}).get("funding_extreme_neg", -0.01)
    fr = data.get("funding_rate_avg")
    return fr is not None and fr <= threshold


def oi_surge(data, params=None) -> bool:
    """OI increased significantly in 24h. Default: 5%"""
    threshold = (params or {}).get("oi_surge_pct", 5.0)
    chg = data.get("oi_change_24h_pct")
    return chg is not None and chg >= threshold


def oi_price_divergence_bullish(data, params=None) -> bool:
    """OI rising while price falling — accumulation (building positions on dip)."""
    chg = data.get("oi_change_24h_pct")
    pc = data.get("price_change_5")
    return chg is not None and pc is not None and chg > 2.0 and pc < -0.01


def oi_price_divergence_bearish(data, params=None) -> bool:
    """OI rising while price rising — leverage building (fragile rally)."""
    chg = data.get("oi_change_24h_pct")
    pc = data.get("price_change_5")
    return chg is not None and pc is not None and chg > 2.0 and pc > 0.01


def ls_crowd_long(data, params=None) -> bool:
    """Global L/S ratio shows crowd is heavily long. Default: 1.8 (64% long)"""
    threshold = (params or {}).get("ls_crowd_long", 1.8)
    r = data.get("ls_global_ratio")
    return r is not None and r >= threshold


def ls_crowd_short(data, params=None) -> bool:
    """Global L/S ratio shows crowd is heavily short. Default: 0.85 (P10 of 180d data)"""
    threshold = (params or {}).get("ls_crowd_short", 0.85)
    r = data.get("ls_global_ratio")
    return r is not None and r <= threshold


def top_trader_divergence(data, params=None) -> bool:
    """Top traders lean opposite to the crowd."""
    global_r = data.get("ls_global_ratio")
    top_r = data.get("ls_top_account_ratio")
    if global_r is None or top_r is None:
        return False
    # Crowd long, pros short
    if global_r > 1.5 and top_r < 0.9:
        return True
    # Crowd short, pros long
    if global_r < 0.67 and top_r > 1.1:
        return True
    return False


def liq_cascade_long(data, params=None) -> bool:
    """Massive long liquidations (>$X in 24h). Default: 10M (P95 of 180d data)"""
    threshold = (params or {}).get("liq_cascade_usd", 10_000_000)
    liq = data.get("liq_long_24h_usd")
    return liq is not None and liq >= threshold


def liq_cascade_short(data, params=None) -> bool:
    """Massive short liquidations (>$X in 24h). Default: 5M (P95 of 180d data)"""
    threshold = (params or {}).get("liq_cascade_usd", 5_000_000)
    liq = data.get("liq_short_24h_usd")
    return liq is not None and liq >= threshold


def fear_greed_extreme_fear(data, params=None) -> bool:
    """Fear & Greed index in extreme fear territory. Default: <= 20"""
    threshold = (params or {}).get("fg_fear", 20)
    fg = data.get("fear_greed_value")
    return fg is not None and fg <= threshold


def fear_greed_extreme_greed(data, params=None) -> bool:
    """Fear & Greed in extreme greed. Default: >= 65 (above P95 of 180d data; max was 75)"""
    threshold = (params or {}).get("fg_greed", 65)
    fg = data.get("fear_greed_value")
    return fg is not None and fg >= threshold


def etf_inflow_streak(data, params=None) -> bool:
    """BTC ETF inflows for N+ consecutive days. Default: 3 days"""
    threshold = (params or {}).get("etf_streak", 3)
    streak = data.get("etf_streak_days")
    return streak is not None and streak >= threshold


def coinbase_premium_positive(data, params=None) -> bool:
    """Coinbase premium positive (US institutional demand). Default: > 0.02 (P75 of 180d data)"""
    threshold = (params or {}).get("cb_premium_pos", 0.02)
    rate = data.get("coinbase_premium_rate")
    return rate is not None and rate >= threshold


# ============================================================================
# SIGNAL REGISTRY
# ============================================================================

SIGNAL_REGISTRY = {
    # TA signals
    "rsi_overbought": rsi_overbought,
    "rsi_oversold": rsi_oversold,
    "macd_bullish_cross": macd_bullish_cross,
    "macd_bearish_cross": macd_bearish_cross,
    "bb_squeeze": bb_squeeze,
    "bb_touch_upper": bb_touch_upper,
    "bb_touch_lower": bb_touch_lower,
    "adx_strong_trend": adx_strong_trend,
    "adx_weak_trend": adx_weak_trend,
    "trend_bullish": trend_bullish,
    "trend_bearish": trend_bearish,
    "obv_divergence_bearish": obv_divergence_bearish,
    "obv_divergence_bullish": obv_divergence_bullish,
    "volume_surge": volume_surge,
    # Derivatives signals
    "funding_extreme_positive": funding_extreme_positive,
    "funding_extreme_negative": funding_extreme_negative,
    "oi_surge": oi_surge,
    "oi_price_divergence_bullish": oi_price_divergence_bullish,
    "oi_price_divergence_bearish": oi_price_divergence_bearish,
    "ls_crowd_long": ls_crowd_long,
    "ls_crowd_short": ls_crowd_short,
    "top_trader_divergence": top_trader_divergence,
    "liq_cascade_long": liq_cascade_long,
    "liq_cascade_short": liq_cascade_short,
    "fear_greed_extreme_fear": fear_greed_extreme_fear,
    "fear_greed_extreme_greed": fear_greed_extreme_greed,
    "etf_inflow_streak": etf_inflow_streak,
    "coinbase_premium_positive": coinbase_premium_positive,
}

# Classify signals by type
TA_SIGNALS = [k for k in SIGNAL_REGISTRY if not k.startswith((
    "funding_", "oi_", "ls_", "liq_", "fear_", "etf_", "coinbase_", "top_trader"
))]
DERIV_SIGNALS = [k for k in SIGNAL_REGISTRY if k not in TA_SIGNALS]


# ============================================================================
# CLI
# ============================================================================

def cmd_list(args):
    """List all registered signals."""
    if args.ta:
        names = TA_SIGNALS
        header = "TA Signals"
    elif args.deriv:
        names = DERIV_SIGNALS
        header = "Derivatives Signals"
    else:
        names = list(SIGNAL_REGISTRY.keys())
        header = "All Signals"

    print(f"\n{header} ({len(names)})")
    print("=" * 60)

    for name in names:
        fn = SIGNAL_REGISTRY[name]
        doc = (fn.__doc__ or "").strip().split("\n")[0]
        sig_type = "DERIV" if name in DERIV_SIGNALS else "TA"
        print(f"  [{sig_type:5s}] {name:35s} {doc}")

    print()


def main():
    parser = argparse.ArgumentParser(description="Titan Signal Library")
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="List all signals")
    list_parser.add_argument("--ta", action="store_true", help="TA signals only")
    list_parser.add_argument("--deriv", action="store_true", help="Derivatives signals only")
    list_parser.set_defaults(func=cmd_list)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
