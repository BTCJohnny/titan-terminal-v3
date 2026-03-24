# Scan: SKYAI 4h — 20260322

**Duration:** 8.4s
**Period:** 180 days

## Phase 1: Individual Signals (top 5)
- **oi_price_divergence_bullish** (LONG) — 18 trades, PF 4.57, WR 72.2%
- **bb_touch_lower** (LONG) — 9 trades, PF 5.07, WR 77.8%
- **rsi_oversold** (LONG) — 5 trades, PF 2.63, WR 60.0%
- **oi_surge** (LONG) — 28 trades, PF 2.43, WR 64.3%
- **fear_greed_extreme_fear** (LONG) — 19 trades, PF 2.67, WR 68.4%

## Phase 2: Scenarios (top 5)
- **E8: OI Surge + RSI Oversold (ETH)** (LONG) — 4 trades, PF inf, WR 100.0%
- **E10: OI Div Bullish + RSI Oversold (ETH)** (LONG) — 3 trades, PF inf, WR 100.0%
- **H4: Fear Accumulation Long** (LONG) — 3 trades, PF inf, WR 100.0%
- **C1: OI Accumulation** (LONG) — 3 trades, PF inf, WR 100.0%
- **G6: Compressed Breakout Bull** (LONG) — 8 trades, PF 5.61, WR 75.0%

## Phase 3: Parameter Sweep (top 5)
- **D1: Volatility Squeeze Breakout [adx_weak=10.0]** (LONG) — 1 trades, PF inf, WR 100.0%
- **D1: Volatility Squeeze Breakout [adx_weak=15.0]** (LONG) — 7 trades, PF 6.63, WR 71.4%
- **D1: Volatility Squeeze Breakout [stop_atr_mult=0.75]** (LONG) — 15 trades, PF 3.74, WR 46.7%
- **E9: OI Surge Standalone (ETH) [stop_atr_mult=1.0]** (LONG) — 37 trades, PF 3.36, WR 56.8%
- **D1: Volatility Squeeze Breakout [target1_atr_mult=4.5]** (LONG) — 12 trades, PF 5.16, WR 66.7%

## Phase 4: Walk-Forward Validation
- **D1: Volatility Squeeze Breakout [adx_weak=15.0]** — PASS
- **E9: OI Surge Standalone (ETH) [stop_atr_mult=1.0]** — PASS
- **E7: OI Surge + BB Squeeze (ETH) [stop_atr_mult=0.75]** — PASS
- **G6: Compressed Breakout Bull [target1_atr_mult=3.75]** — PASS
- **A4: Fear & Greed Extreme Fear Buy [fg_fear=15.0]** — PASS

## Graduated Strategies
- **E9: OI Surge Standalone (ETH) [stop_atr_mult=1.0]** — PF 3.36, WR 57%, 37 trades
- **A4: Fear & Greed Extreme Fear Buy [fg_fear=15.0]** — PF 6.19, WR 83%, 12 trades
