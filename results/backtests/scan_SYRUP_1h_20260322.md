# Scan: SYRUP 1h — 20260322

**Duration:** 103.3s
**Period:** 180 days

## Phase 1: Individual Signals (top 5)
- **funding_extreme_positive** (SHORT) — 34 trades, PF 3.47, WR 67.6%
- **oi_surge** (LONG) — 45 trades, PF 2.69, WR 62.2%
- **fear_greed_extreme_greed** (SHORT) — 7 trades, PF 3.20, WR 71.4%
- **oi_price_divergence_bullish** (LONG) — 54 trades, PF 2.15, WR 61.1%
- **obv_divergence_bullish** (LONG) — 6 trades, PF 1.46, WR 50.0%

## Phase 2: Scenarios (top 5)
- **H2: Greed Distribution Short** (SHORT) — 1 trades, PF inf, WR 100.0%
- **D1: Volatility Squeeze Breakout** (LONG) — 13 trades, PF 5.87, WR 69.2%
- **E7: OI Surge + BB Squeeze (ETH)** (LONG) — 25 trades, PF 4.86, WR 68.0%
- **B2: OI Breakout Long** (LONG) — 8 trades, PF 2.83, WR 62.5%
- **E9: OI Surge Standalone (ETH)** (LONG) — 69 trades, PF 2.15, WR 60.9%

## Phase 3: Parameter Sweep (top 5)
- **E7: OI Surge + BB Squeeze (ETH) [stop_atr_mult=0.75]** (LONG) — 1 trades, PF inf, WR 100.0%
- **D1: Volatility Squeeze Breakout [adx_weak=10.0]** (LONG) — 1 trades, PF inf, WR 100.0%
- **G8: Triple Energy Buildup [stop_atr_mult=1.12]** (LONG) — 2 trades, PF inf, WR 100.0%
- **B2: OI Breakout Long [stop_atr_mult=1.12]** (LONG) — 4 trades, PF inf, WR 100.0%
- **D1: Volatility Squeeze Breakout [oi_surge_pct=3.75]** (LONG) — 8 trades, PF 17.85, WR 87.5%

## Phase 4: Walk-Forward Validation
- **D1: Volatility Squeeze Breakout [oi_surge_pct=3.75]** — PASS
- **E7: OI Surge + BB Squeeze (ETH) [bb_squeeze_pct=0.375]** — PASS
- **G8: Triple Energy Buildup [vol_surge=0.75]** — PASS
- **B2: OI Breakout Long [adx_strong=31.25]** — PASS
- **E9: OI Surge Standalone (ETH) [stop_atr_mult=1.5]** — PASS

## Graduated Strategies
- **E7: OI Surge + BB Squeeze (ETH) [bb_squeeze_pct=0.375]** — PF 5.98, WR 75%, 28 trades
- **G8: Triple Energy Buildup [vol_surge=0.75]** — PF 4.31, WR 68%, 19 trades
- **E9: OI Surge Standalone (ETH) [stop_atr_mult=1.5]** — PF 2.39, WR 56%, 66 trades
