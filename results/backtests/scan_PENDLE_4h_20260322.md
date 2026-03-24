# Scan: PENDLE 4h — 20260322

**Duration:** 8.3s
**Period:** 180 days

## Phase 1: Individual Signals (top 5)
- **macd_bearish_cross** (SHORT) — 19 trades, PF 2.33, WR 57.9%
- **funding_extreme_negative** (LONG) — 4 trades, PF 1.98, WR 50.0%
- **funding_extreme_positive** (SHORT) — 22 trades, PF 1.98, WR 59.1%
- **obv_divergence_bearish** (SHORT) — 6 trades, PF 1.78, WR 50.0%
- **trend_bearish** (SHORT) — 22 trades, PF 1.77, WR 54.5%

## Phase 2: Scenarios (top 5)
- **E6: MACD Rollover + OBV Divergence** (SHORT) — 1 trades, PF inf, WR 100.0%
- **F5: Distribution Fade** (SHORT) — 2 trades, PF 2.45, WR 50.0%
- **E7: OI Surge + BB Squeeze (ETH)** (LONG) — 12 trades, PF 2.78, WR 66.7%
- **D1: Volatility Squeeze Breakout** (LONG) — 5 trades, PF 4.06, WR 80.0%
- **F4: Accumulation Bounce** (LONG) — 4 trades, PF 3.33, WR 75.0%

## Phase 3: Parameter Sweep (top 5)
- **D1: Volatility Squeeze Breakout [target2_atr_mult=3.0]** (LONG) — 5 trades, PF 7.77, WR 80.0%
- **D1: Volatility Squeeze Breakout [adx_weak=25.0]** (LONG) — 7 trades, PF 9.11, WR 85.7%
- **D1: Volatility Squeeze Breakout [adx_weak=30.0]** (LONG) — 7 trades, PF 9.10, WR 85.7%
- **D1: Volatility Squeeze Breakout [target2_atr_mult=4.5]** (LONG) — 5 trades, PF 6.79, WR 80.0%
- **D1: Volatility Squeeze Breakout [target1_atr_mult=3.75]** (LONG) — 4 trades, PF 5.43, WR 75.0%

## Phase 4: Walk-Forward Validation
- **D1: Volatility Squeeze Breakout [target2_atr_mult=3.0]** — PASS
- **G12: MACD Bullish + ADX Strong (SHORT) [stop_atr_mult=1.0]** — PASS
- **E7: OI Surge + BB Squeeze (ETH) [oi_surge_pct=2.5]** — PASS
- **E1: MACD Rollover + Death Cross [stop_atr_mult=1.0]** — FAIL
- **H4: Fear Accumulation Long [stop_atr_mult=3.12]** — PASS

## Graduated Strategies
- **G12: MACD Bullish + ADX Strong (SHORT) [stop_atr_mult=1.0]** — PF 2.81, WR 47%, 15 trades
- **E7: OI Surge + BB Squeeze (ETH) [oi_surge_pct=2.5]** — PF 5.48, WR 80%, 10 trades
