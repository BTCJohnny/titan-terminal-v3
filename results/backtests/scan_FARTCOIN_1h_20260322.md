# Scan: FARTCOIN 1h — 20260322

**Duration:** 80.8s
**Period:** 180 days

## Phase 1: Individual Signals (top 5)
- **oi_price_divergence_bullish** (LONG) — 36 trades, PF 5.08, WR 72.2%
- **oi_surge** (LONG) — 28 trades, PF 4.46, WR 75.0%
- **fear_greed_extreme_greed** (SHORT) — 8 trades, PF 3.24, WR 62.5%
- **ls_crowd_short** (LONG) — 7 trades, PF 3.18, WR 71.4%
- **rsi_overbought** (SHORT) — 38 trades, PF 1.95, WR 57.9%

## Phase 2: Scenarios (top 5)
- **C1: OI Accumulation** (LONG) — 10 trades, PF 12.77, WR 90.0%
- **E10: OI Div Bullish + RSI Oversold (ETH)** (LONG) — 10 trades, PF 10.15, WR 80.0%
- **E8: OI Surge + RSI Oversold (ETH)** (LONG) — 10 trades, PF 9.87, WR 80.0%
- **G8: Triple Energy Buildup** (LONG) — 20 trades, PF 3.49, WR 60.0%
- **D1: Volatility Squeeze Breakout** (LONG) — 11 trades, PF 3.89, WR 63.6%

## Phase 3: Parameter Sweep (top 5)
- **C1: OI Accumulation [stop_atr_mult=1.0]** (LONG) — 11 trades, PF 14.61, WR 81.8%
- **E10: OI Div Bullish + RSI Oversold (ETH) [stop_atr_mult=1.0]** (LONG) — 11 trades, PF 14.49, WR 81.8%
- **E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.0]** (LONG) — 11 trades, PF 14.09, WR 81.8%
- **C1: OI Accumulation [stop_atr_mult=1.5]** (LONG) — 10 trades, PF 9.20, WR 80.0%
- **E10: OI Div Bullish + RSI Oversold (ETH) [stop_atr_mult=1.5]** (LONG) — 10 trades, PF 9.12, WR 80.0%

## Phase 4: Walk-Forward Validation
- **C1: OI Accumulation [stop_atr_mult=1.0]** — PASS
- **E10: OI Div Bullish + RSI Oversold (ETH) [stop_atr_mult=1.0]** — PASS
- **E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.0]** — PASS
- **D1: Volatility Squeeze Breakout [adx_weak=15.0]** — PASS
- **G8: Triple Energy Buildup [oi_surge_pct=3.75]** — PASS

## Graduated Strategies
- **C1: OI Accumulation [stop_atr_mult=1.0]** — PF 14.61, WR 82%, 11 trades
- **E10: OI Div Bullish + RSI Oversold (ETH) [stop_atr_mult=1.0]** — PF 14.49, WR 82%, 11 trades
- **E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.0]** — PF 14.09, WR 82%, 11 trades
- **G8: Triple Energy Buildup [oi_surge_pct=3.75]** — PF 3.77, WR 61%, 18 trades
