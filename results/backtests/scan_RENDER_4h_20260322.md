# Scan: RENDER 4h — 20260322

**Duration:** 7.7s
**Period:** 180 days

## Phase 1: Individual Signals (top 5)
- **funding_extreme_negative** (LONG) — 4 trades, PF 5.07, WR 75.0%
- **oi_surge** (LONG) — 20 trades, PF 2.18, WR 60.0%
- **ls_crowd_long** (SHORT) — 2 trades, PF 1.81, WR 50.0%
- **obv_divergence_bearish** (SHORT) — 8 trades, PF 1.72, WR 50.0%
- **adx_strong_trend** (LONG) — 25 trades, PF 1.37, WR 48.0%

## Phase 2: Scenarios (top 5)
- **F5: Distribution Fade** (SHORT) — 1 trades, PF inf, WR 100.0%
- **F7: RSI Extreme Oversold Snap** (LONG) — 1 trades, PF inf, WR 100.0%
- **G8: Triple Energy Buildup** (LONG) — 3 trades, PF 3.64, WR 66.7%
- **D1: Volatility Squeeze Breakout** (LONG) — 6 trades, PF 3.34, WR 66.7%
- **E6: MACD Rollover + OBV Divergence** (SHORT) — 1 trades, PF inf, WR 100.0%

## Phase 3: Parameter Sweep (top 5)
- **D1: Volatility Squeeze Breakout [adx_weak=10.0]** (LONG) — 1 trades, PF inf, WR 100.0%
- **D1: Volatility Squeeze Breakout [adx_weak=15.0]** (LONG) — 3 trades, PF inf, WR 100.0%
- **D1: Volatility Squeeze Breakout [stop_atr_mult=1.12]** (LONG) — 6 trades, PF 4.44, WR 66.7%
- **D1: Volatility Squeeze Breakout [stop_atr_mult=0.75]** (LONG) — 5 trades, PF 3.91, WR 60.0%
- **E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.0]** (LONG) — 10 trades, PF 4.29, WR 70.0%

## Phase 4: Walk-Forward Validation
- **D1: Volatility Squeeze Breakout [stop_atr_mult=1.12]** — PASS
- **E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.0]** — PASS
- **E10: OI Div Bullish + RSI Oversold (ETH) [stop_atr_mult=1.0]** — PASS
- **F2: Oversold Bounce (Any Regime)** — PASS
- **E9: OI Surge Standalone (ETH) [stop_atr_mult=1.0]** — PASS

## Graduated Strategies
- **E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.0]** — PF 4.29, WR 70%, 10 trades
- **E10: OI Div Bullish + RSI Oversold (ETH) [stop_atr_mult=1.0]** — PF 4.29, WR 70%, 10 trades
