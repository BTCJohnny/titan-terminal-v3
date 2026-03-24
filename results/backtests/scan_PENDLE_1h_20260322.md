# Scan: PENDLE 1h — 20260322

**Duration:** 101.2s
**Period:** 180 days

## Phase 1: Individual Signals (top 5)
- **fear_greed_extreme_greed** (SHORT) — 7 trades, PF 2.74, WR 57.1%
- **oi_surge** (LONG) — 37 trades, PF 2.25, WR 56.8%
- **oi_price_divergence_bullish** (LONG) — 38 trades, PF 2.13, WR 57.9%
- **obv_divergence_bullish** (LONG) — 6 trades, PF 2.34, WR 66.7%
- **macd_bearish_cross** (SHORT) — 93 trades, PF 1.16, WR 40.9%

## Phase 2: Scenarios (top 5)
- **D1: Volatility Squeeze Breakout** (LONG) — 12 trades, PF 11.46, WR 83.3%
- **E10: OI Div Bullish + RSI Oversold (ETH)** (LONG) — 10 trades, PF 14.80, WR 90.0%
- **C1: OI Accumulation** (LONG) — 10 trades, PF 7.81, WR 80.0%
- **E7: OI Surge + BB Squeeze (ETH)** (LONG) — 20 trades, PF 3.49, WR 65.0%
- **D2: Trend Mean Reversion Short** (SHORT) — 1 trades, PF inf, WR 100.0%

## Phase 3: Parameter Sweep (top 5)
- **E10: OI Div Bullish + RSI Oversold (ETH) [stop_atr_mult=1.0]** (LONG) — 8 trades, PF 9.35, WR 75.0%
- **D1: Volatility Squeeze Breakout [stop_atr_mult=1.12]** (LONG) — 3 trades, PF 7.16, WR 66.7%
- **C1: OI Accumulation [stop_atr_mult=1.0]** (LONG) — 8 trades, PF 9.02, WR 75.0%
- **D1: Volatility Squeeze Breakout [adx_weak=15.0]** (LONG) — 7 trades, PF 16.75, WR 85.7%
- **E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.0]** (LONG) — 8 trades, PF 8.80, WR 75.0%

## Phase 4: Walk-Forward Validation
- **E10: OI Div Bullish + RSI Oversold (ETH) [stop_atr_mult=1.0]** — PASS
- **C1: OI Accumulation [stop_atr_mult=1.0]** — PASS
- **D1: Volatility Squeeze Breakout [adx_weak=15.0]** — PASS
- **E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.0]** — PASS
- **E7: OI Surge + BB Squeeze (ETH) [oi_surge_pct=3.0]** — PASS

## Graduated Strategies
- **E7: OI Surge + BB Squeeze (ETH) [oi_surge_pct=3.0]** — PF 4.77, WR 71%, 17 trades
