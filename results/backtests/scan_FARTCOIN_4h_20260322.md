# Scan: FARTCOIN 4h — 20260322

**Duration:** 7.5s
**Period:** 180 days

## Phase 1: Individual Signals (top 5)
- **ls_crowd_short** (LONG) — 3 trades, PF inf, WR 100.0%
- **oi_surge** (LONG) — 16 trades, PF 4.41, WR 75.0%
- **ls_crowd_long** (SHORT) — 7 trades, PF 6.82, WR 85.7%
- **oi_price_divergence_bullish** (LONG) — 16 trades, PF 2.44, WR 62.5%
- **obv_divergence_bearish** (SHORT) — 9 trades, PF 1.76, WR 55.6%

## Phase 2: Scenarios (top 5)
- **E5: Death Cross + Crowd Long** (SHORT) — 3 trades, PF inf, WR 100.0%
- **D1: Volatility Squeeze Breakout** (LONG) — 4 trades, PF 4.88, WR 75.0%
- **C1: OI Accumulation** (LONG) — 6 trades, PF 3.50, WR 66.7%
- **E4: BB Upper + Crowd Long** (SHORT) — 2 trades, PF 2.45, WR 50.0%
- **H4: Fear Accumulation Long** (LONG) — 3 trades, PF 3.14, WR 66.7%

## Phase 3: Parameter Sweep (top 5)
- **C1: OI Accumulation [rsi_os=17.5]** (LONG) — 1 trades, PF inf, WR 100.0%
- **E8: OI Surge + RSI Oversold (ETH) [rsi_os=17.5]** (LONG) — 1 trades, PF inf, WR 100.0%
- **E10: OI Div Bullish + RSI Oversold (ETH) [rsi_os=17.5]** (LONG) — 1 trades, PF inf, WR 100.0%
- **C1: OI Accumulation [rsi_os=26.25]** (LONG) — 2 trades, PF inf, WR 100.0%
- **C1: OI Accumulation [stop_atr_mult=1.0]** (LONG) — 8 trades, PF 4.07, WR 50.0%

## Phase 4: Walk-Forward Validation
- **C1: OI Accumulation [stop_atr_mult=1.0]** — PASS
- **E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.0]** — PASS
- **E10: OI Div Bullish + RSI Oversold (ETH) [stop_atr_mult=1.0]** — PASS
- **E9: OI Surge Standalone (ETH) [stop_atr_mult=1.5]** — PASS
- **E7: OI Surge + BB Squeeze (ETH) [stop_atr_mult=0.75]** — PASS

## Graduated Strategies
- **E9: OI Surge Standalone (ETH) [stop_atr_mult=1.5]** — PF 3.33, WR 62%, 21 trades
