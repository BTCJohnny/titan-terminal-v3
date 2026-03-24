# Scan: SKYAI 1h — 20260322

**Duration:** 75.7s
**Period:** 180 days

## Phase 1: Individual Signals (top 5)
- **oi_price_divergence_bullish** (LONG) — 49 trades, PF 4.77, WR 69.4%
- **oi_surge** (LONG) — 59 trades, PF 2.73, WR 62.7%
- **ls_crowd_short** (LONG) — 16 trades, PF 2.60, WR 62.5%
- **ls_crowd_long** (SHORT) — 19 trades, PF 1.61, WR 52.6%
- **bb_squeeze** (LONG) — 70 trades, PF 1.42, WR 45.7%

## Phase 2: Scenarios (top 5)
- **E11: Triple Short (MACD + Death Cross + Crowd Long)** (SHORT) — 6 trades, PF 11.42, WR 83.3%
- **H5: Double Contrarian Long (Fear + Crowd)** (LONG) — 1 trades, PF inf, WR 100.0%
- **E8: OI Surge + RSI Oversold (ETH)** (LONG) — 7 trades, PF 22.98, WR 85.7%
- **E10: OI Div Bullish + RSI Oversold (ETH)** (LONG) — 5 trades, PF 19.71, WR 80.0%
- **E7: OI Surge + BB Squeeze (ETH)** (LONG) — 27 trades, PF 4.24, WR 63.0%

## Phase 3: Parameter Sweep (top 5)
- **E7: OI Surge + BB Squeeze (ETH) [stop_atr_mult=0.75]** (LONG) — 7 trades, PF 5.48, WR 57.1%
- **E11: Triple Short (MACD + Death Cross + Crowd Long) [target2_atr_mult=9.0]** (SHORT) — 5 trades, PF inf, WR 100.0%
- **E11: Triple Short (MACD + Death Cross + Crowd Long) [stop_atr_mult=1.12]** (SHORT) — 3 trades, PF 7.66, WR 66.7%
- **E11: Triple Short (MACD + Death Cross + Crowd Long) [target2_atr_mult=7.5]** (SHORT) — 5 trades, PF inf, WR 100.0%
- **E8: OI Surge + RSI Oversold (ETH) [oi_surge_pct=2.5]** (LONG) — 6 trades, PF inf, WR 100.0%

## Phase 4: Walk-Forward Validation
- **E7: OI Surge + BB Squeeze (ETH) [stop_atr_mult=0.75]** — PASS
- **E11: Triple Short (MACD + Death Cross + Crowd Long) [target2_atr_mult=9.0]** — FAIL
- **E8: OI Surge + RSI Oversold (ETH) [oi_surge_pct=2.5]** — PASS
- **E10: OI Div Bullish + RSI Oversold (ETH) [target1_atr_mult=4.5]** — PASS
- **C1: OI Accumulation [target1_atr_mult=4.5]** — PASS

## Graduated Strategies
No strategies graduated.
