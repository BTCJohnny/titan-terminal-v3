# Scan: ASTER 4h — 20260322

**Duration:** 7.0s
**Period:** 180 days

## Phase 1: Individual Signals (top 5)
- **obv_divergence_bullish** (LONG) — 9 trades, PF 2.00, WR 66.7%
- **macd_bearish_cross** (SHORT) — 17 trades, PF 1.51, WR 52.9%
- **ls_crowd_long** (SHORT) — 21 trades, PF 1.38, WR 47.6%
- **bb_touch_upper** (SHORT) — 13 trades, PF 1.43, WR 53.8%
- **oi_surge** (LONG) — 14 trades, PF 1.40, WR 57.1%

## Phase 2: Scenarios (top 5)
- **F5: Distribution Fade** (SHORT) — 1 trades, PF inf, WR 100.0%
- **H4: Fear Accumulation Long** (LONG) — 5 trades, PF inf, WR 100.0%
- **F8: RSI Extreme Overbought Fade** (SHORT) — 1 trades, PF inf, WR 100.0%
- **G8: Triple Energy Buildup (SHORT)** (SHORT) — 3 trades, PF 2.61, WR 66.7%
- **E2: MACD Rollover + Crowd Long** (SHORT) — 12 trades, PF 2.21, WR 58.3%

## Phase 3: Parameter Sweep (top 5)
- **E4: BB Upper + Crowd Long [stop_atr_mult=0.75]** (SHORT) — 6 trades, PF 3.96, WR 66.7%
- **H4: Fear Accumulation Long [fg_fear=10.0]** (LONG) — 3 trades, PF inf, WR 100.0%
- **H4: Fear Accumulation Long [target1_atr_mult=5.0]** (LONG) — 5 trades, PF inf, WR 100.0%
- **H4: Fear Accumulation Long [fg_fear=15.0]** (LONG) — 4 trades, PF inf, WR 100.0%
- **H4: Fear Accumulation Long [target2_atr_mult=4.0]** (LONG) — 6 trades, PF 150.91, WR 83.3%

## Phase 4: Walk-Forward Validation
- **E4: BB Upper + Crowd Long [stop_atr_mult=0.75]** — FAIL
- **H4: Fear Accumulation Long [target1_atr_mult=5.0]** — PASS
- **G7: Compressed Breakdown Bear [target1_atr_mult=1.5]** — PASS
- **E2: MACD Rollover + Crowd Long [target1_atr_mult=3.75]** — PASS
- **E1: MACD Rollover + Death Cross [stop_atr_mult=1.0]** — PASS

## Graduated Strategies
- **E2: MACD Rollover + Crowd Long [target1_atr_mult=3.75]** — PF 2.45, WR 58%, 12 trades
