# Scan: ASTER 1h — 20260322

**Duration:** 50.0s
**Period:** 180 days

## Phase 1: Individual Signals (top 5)
- **oi_surge** (LONG) — 21 trades, PF 3.52, WR 71.4%
- **fear_greed_extreme_greed** (SHORT) — 5 trades, PF 9.93, WR 80.0%
- **liq_cascade_short** (SHORT) — 3 trades, PF 6.27, WR 66.7%
- **oi_price_divergence_bullish** (LONG) — 32 trades, PF 2.00, WR 59.4%
- **obv_divergence_bearish** (SHORT) — 11 trades, PF 1.51, WR 45.5%

## Phase 2: Scenarios (top 5)
- **E6: MACD Rollover + OBV Divergence** (SHORT) — 1 trades, PF inf, WR 100.0%
- **H2: Greed Distribution Short** (SHORT) — 2 trades, PF inf, WR 100.0%
- **H6: Greed Standalone Short** (SHORT) — 4 trades, PF 4.88, WR 75.0%
- **H3: Double Contrarian Short (Greed + Crowd)** (SHORT) — 5 trades, PF 9.93, WR 80.0%
- **E8: OI Surge + RSI Oversold (ETH)** (LONG) — 14 trades, PF 3.00, WR 64.3%

## Phase 3: Parameter Sweep (top 5)
- **H3: Double Contrarian Short (Greed + Crowd) [ls_crowd_long=2.5]** (SHORT) — 1 trades, PF inf, WR 100.0%
- **E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.0]** (LONG) — 11 trades, PF 5.48, WR 63.6%
- **C1: OI Accumulation [stop_atr_mult=1.0]** (LONG) — 10 trades, PF 4.52, WR 60.0%
- **G7: Compressed Breakdown Bear [stop_atr_mult=0.75]** (SHORT) — 5 trades, PF 3.30, WR 40.0%
- **H3: Double Contrarian Short (Greed + Crowd) [target2_atr_mult=7.5]** (SHORT) — 4 trades, PF inf, WR 100.0%

## Phase 4: Walk-Forward Validation
- **E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.0]** — PASS
- **C1: OI Accumulation [stop_atr_mult=1.0]** — PASS
- **G7: Compressed Breakdown Bear [stop_atr_mult=0.75]** — FAIL
- **H3: Double Contrarian Short (Greed + Crowd) [target1_atr_mult=4.5]** — FAIL
- **E9: OI Surge Standalone (ETH) [oi_surge_pct=2.5]** — PASS

## Graduated Strategies
- **E8: OI Surge + RSI Oversold (ETH) [stop_atr_mult=1.0]** — PF 5.48, WR 64%, 11 trades
- **C1: OI Accumulation [stop_atr_mult=1.0]** — PF 4.52, WR 60%, 10 trades
- **E9: OI Surge Standalone (ETH) [oi_surge_pct=2.5]** — PF 2.75, WR 67%, 36 trades
