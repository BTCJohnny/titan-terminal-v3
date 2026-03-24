# Scan: RENDER 1h — 20260322

**Duration:** 92.7s
**Period:** 180 days

## Phase 1: Individual Signals (top 5)
- **fear_greed_extreme_greed** (SHORT) — 7 trades, PF 8.10, WR 85.7%
- **oi_price_divergence_bullish** (LONG) — 39 trades, PF 4.26, WR 71.8%
- **oi_surge** (LONG) — 30 trades, PF 3.87, WR 73.3%
- **ls_crowd_long** (SHORT) — 16 trades, PF 2.59, WR 62.5%
- **macd_bearish_cross** (SHORT) — 90 trades, PF 1.37, WR 50.0%

## Phase 2: Scenarios (top 5)
- **A1: Crowded Long Fade** (SHORT) — 1 trades, PF inf, WR 100.0%
- **H1: Greed Top Short (Sentiment + RSI)** (SHORT) — 1 trades, PF inf, WR 100.0%
- **E8: OI Surge + RSI Oversold (ETH)** (LONG) — 8 trades, PF 15.50, WR 87.5%
- **C1: OI Accumulation** (LONG) — 6 trades, PF 11.18, WR 83.3%
- **E10: OI Div Bullish + RSI Oversold (ETH)** (LONG) — 6 trades, PF 10.98, WR 83.3%

## Phase 3: Parameter Sweep (top 5)
- **E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.0]** (LONG) — 3 trades, PF inf, WR 100.0%
- **C1: OI Accumulation [stop_atr_mult=1.0]** (LONG) — 2 trades, PF inf, WR 100.0%
- **E10: OI Div Bullish + RSI Oversold (ETH) [stop_atr_mult=1.0]** (LONG) — 2 trades, PF inf, WR 100.0%
- **E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.5]** (LONG) — 5 trades, PF inf, WR 100.0%
- **C1: OI Accumulation [stop_atr_mult=1.5]** (LONG) — 4 trades, PF inf, WR 100.0%

## Phase 4: Walk-Forward Validation
- **E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.5]** — PASS
- **C1: OI Accumulation [target1_atr_mult=4.5]** — PASS
- **E10: OI Div Bullish + RSI Oversold (ETH) [target1_atr_mult=4.5]** — PASS
- **H3: Double Contrarian Short (Greed + Crowd) [ls_crowd_long=2.5]** — FAIL
- **G6: Compressed Breakout Bull [target2_atr_mult=9.0]** — PASS

## Graduated Strategies
No strategies graduated.
