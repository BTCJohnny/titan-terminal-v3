# Scan: SYRUP 4h — 20260322

**Duration:** 7.6s
**Period:** 180 days

## Phase 1: Individual Signals (top 5)
- **bb_touch_upper** (SHORT) — 13 trades, PF 2.71, WR 61.5%
- **funding_extreme_positive** (SHORT) — 11 trades, PF 2.65, WR 63.6%
- **oi_surge** (LONG) — 18 trades, PF 1.91, WR 55.6%
- **funding_extreme_negative** (LONG) — 5 trades, PF 1.80, WR 60.0%
- **macd_bearish_cross** (SHORT) — 15 trades, PF 1.60, WR 46.7%

## Phase 2: Scenarios (top 5)
- **D2: Trend Mean Reversion Short** (SHORT) — 1 trades, PF inf, WR 100.0%
- **G2: Momentum Continuation Long** (LONG) — 3 trades, PF 3.61, WR 66.7%
- **D1: Volatility Squeeze Breakout** (LONG) — 8 trades, PF 2.46, WR 50.0%
- **G5: Derivatives Squeeze Long** (LONG) — 1 trades, PF inf, WR 100.0%
- **E10: OI Div Bullish + RSI Oversold (ETH)** (LONG) — 9 trades, PF 2.76, WR 55.6%

## Phase 3: Parameter Sweep (top 5)
- **D1: Volatility Squeeze Breakout [bb_squeeze_pct=0.3]** (LONG) — 8 trades, PF 4.20, WR 62.5%
- **D1: Volatility Squeeze Breakout [stop_atr_mult=1.12]** (LONG) — 8 trades, PF 3.31, WR 50.0%
- **D1: Volatility Squeeze Breakout [target1_atr_mult=1.5]** (LONG) — 8 trades, PF 10.03, WR 87.5%
- **E3: BB Upper Touch + Death Cross [stop_atr_mult=0.75]** (SHORT) — 9 trades, PF 2.99, WR 44.4%
- **D1: Volatility Squeeze Breakout [bb_squeeze_pct=0.25]** (LONG) — 9 trades, PF 3.21, WR 55.6%

## Phase 4: Walk-Forward Validation
- **D1: Volatility Squeeze Breakout [bb_squeeze_pct=0.3]** — PASS
- **E3: BB Upper Touch + Death Cross [stop_atr_mult=0.75]** — PASS
- **E10: OI Div Bullish + RSI Oversold (ETH) [target1_atr_mult=4.5]** — PASS
- **E8: OI Surge + RSI Oversold (ETH) [oi_surge_pct=2.5]** — PASS
- **C1: OI Accumulation [target1_atr_mult=1.5]** — PASS

## Graduated Strategies
No strategies graduated.
