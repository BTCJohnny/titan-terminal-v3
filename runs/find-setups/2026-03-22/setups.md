# Find-Setups Output — 2026-03-22

**Regime:** Risk-Off → Counter-Trend Bounce (shifted from Distribution Phase overnight)
**Scanned:** 32 tokens (20 with TA data, 12 missing OHLCV)
**Filtered:** 5 hits → 2 candidates → 2 setups (both conditional on pullback entries)
**Nansen Credits:** 10/100 session

---

## ⚠️ Portfolio Constraint

| Metric | Value |
|--------|-------|
| Equity | $50,241 |
| Cash | $18,096 |
| Open | CL SHORT ($32,145) |
| Stablecoin floor (30%) | $15,072 |
| **Available for new positions** | **$3,024** |

Cash constraint limits new deployment to ~$3,024 total. Only one of the two setups below can be taken at full sizing. Choose the highest-conviction play.

---

## 🟢 BTC — LONG Setup (Mean Reversion Bounce)

**Thesis:** BTC is testing the 4H SMA 200 ($68,891) / BB lower ($68,919) with 1H RSI at 32.1 (oversold), extreme short crowding (-0.30% funding across 21 exchanges), F&G at 9 (extreme fear), and today's options max pain at $70,000 pulling price 1.2% higher. This is a mechanical snap-back trade — short covering + max pain magnetism = tactical bounce to the 4H BB middle band.

**Regime fit:** Mean Reversion Long (valid in Counter-Trend Bounce sub-regime)

**Entry:** $69,000 - $69,200 (current zone — at 4H SMA 200 + BB lower support cluster)
**Stop:** $68,400 (below 4H low at $68,636 with buffer)
**Risk per unit:** ~$700

| Target | Price | R:R | Action |
|--------|-------|-----|--------|
| T1 | $70,000 | 1.3:1 | Take 40% — max pain magnet, first resistance |
| T2 | $70,241 | 1.6:1 | Take 40% — 4H BB middle / Daily SMA 20 |
| T3 | $71,731 | **3.8:1** | Trail final 20% — 1H resistance + near 1H SMA 200 |

**Position sizing:**
- Available cash: $3,024 (stablecoin floor binding)
- Position: **0.044 BTC** (~$3,024)
- Risk: 0.044 × $700 = **$30.80** (0.06% of portfolio)
- Note: Well below 2% risk budget — stablecoin floor is the constraint, not risk

**Key signals (strongest first per hierarchy):**
- 📊 4H RSI 31.45 + 1H RSI 32.1 — dual-timeframe oversold at structural support
- 💸 Funding -0.30% (annualized -438%) — most extreme short crowding this quarter
- 😱 F&G = 9 — extreme fear, historically bottom-tier reading, contrarian long
- 🎯 Max pain $70,000 (today's expiry) — MM incentive to pull price UP 1.2%
- 📈 Daily OBV positive (+271K) — the one constructive volume signal
- ⚠️ 1H OBV -865K — bounce is short covering, not accumulation. Caps upside ambition.

**Entry confirmation:**
1. 1H candle holds above $68,900 (4H SMA 200 area)
2. 1H MACD histogram stops accelerating negative (currently -71.8)
3. A 1H close back above $69,400 with MACD contracting = trigger
4. If $68,400 breaks before confirmation → skip

**Invalidation:** 4H close below $68,400. Funding normalizes above -0.05%. MACD keeps accelerating down.

---

## 🟡 ETH — LONG Setup (Mean Reversion) → then SHORT at Higher Levels

**Thesis:** ETH has a two-phase opportunity. Phase 1: MR long from the 4H BB lower ($2,092) + max pain $2,125 pull. Phase 2: Flip short at $2,150-$2,205 where weekly downtrend (ADX 45.81), OBV distribution (negative all 4 timeframes), and a smart perps trader's $2.6M short all converge. The long is fuel — the short is the real trade.

**Regime fit:** Phase 1 — Mean Reversion Long. Phase 2 — Distribution Short.

### Phase 1: LONG (conditional — needs $16 more drop)

**Entry:** $2,077 - $2,093 (1H BB lower + 4H BB lower + $2,088 broken S/R)
**Stop:** $2,053 (tight, below noise but above SMA 200 structural floor)
**Risk per unit:** ~$32

| Target | Price | R:R | Action |
|--------|-------|-----|--------|
| T1 | $2,125 | 1.0:1 | Take 50% — max pain / 1H BB middle |
| T2 | $2,151 | 1.9:1 | Take 40% — 1H resistance / 4H BB middle |
| T3 | $2,204 | **3.5:1** | Trail final 10% — 1H upper resistance |

**Position sizing:**
- Available cash: $3,024 (if BTC not taken)
- Position: **1.45 ETH** (~$3,024)
- Risk: 1.45 × $32 = **$46.40** (0.09% of portfolio)

### Phase 2: SHORT (triggered by Phase 1 success or independent)

**Entry:** $2,150 - $2,205 (1H resistance + 4H BB upper + 1H SMA 200)
**Stop:** $2,240
**Risk per unit:** ~$65

| Target | Price | R:R | Action |
|--------|-------|-----|--------|
| T1 | $2,088 | 1.4:1 | Take 25% |
| T2 | $2,038 | 2.5:1 | Take 50% |
| T3 | $1,906 | **5.4-8.6:1** | Trail remaining 25% |

**Position sizing (Phase 2 — WITH the trend):**
- Category limit: Blue Chip 30% × Risk-Off 100% (short) = $15,072
- But cash constraint = $3,024 (unless Phase 1 closed first)
- Position: **1.39 ETH** ($3,024) if cash-constrained
- Risk: 1.39 × $65 = $90 (0.18% of portfolio)

**Key signals:**
- 🏦 Top PnL accumulating ETH at 3.0x average — supports Phase 1 long (on-chain highest)
- 💸 Funding -0.14% — shorts crowded, squeeze fuel for bounce
- 🎯 Max pain $2,125 today, $2,350 on 3/27 — pulls price up
- 🐻 Smart HL Perps Trader opened $2.6M short at $2,152 — supports Phase 2 short
- 📉 OBV negative ALL 4 timeframes — distribution is real and ongoing
- 📊 Weekly ADX 45.81, DI- dominant — macro bear freight train is intact

**Entry confirmation (Phase 1):** Price reaches $2,077-$2,093 zone with 1H RSI < 35.
**Entry confirmation (Phase 2):** Price bounces to $2,150+ and 4H RSI rises above 55.

**Invalidation:** Phase 1 — 4H close below $2,038. Phase 2 — Daily close above $2,240 on positive OBV.

---

## Recommendation: Pick One

| Setup | Conviction | Actionable Now? | R:R (T3) | Risk |
|-------|-----------|----------------|----------|------|
| **BTC Long** | Higher | Yes — at support now | 3.8:1 ✅ | $31 |
| ETH Long (Phase 1) | Moderate | No — needs $16 drop | 3.5:1 ✅ | $46 |
| ETH Short (Phase 2) | Highest | No — needs bounce to $2,150+ | 5.4-8.6:1 ✅✅ | $90 |

**BTC is the recommended action.** It's at the entry zone NOW, has no conflicting smart money signals, and the max pain pull is same-day (urgent). ETH Phase 1 needs more downside, and Phase 2 (the real conviction trade) requires patience for the bounce to deliver price to the short zone.

If passing on BTC: set alerts at ETH $2,093 (Phase 1) and $2,150 (Phase 2).

---

## Watchlist Updates

**HYPE** — BB squeeze forming, ADX 16.74. Positive OBV. $75M institutional thesis intact. Price $39.69 — above entry zone ($36-37.50). Monitor for pullback or breakout above $42.33.

**SOL** — Smart money accumulated +28.8% in 24h ($3.6M, 80 holders). Testing 4H SMA 200 ($86.11). Below on-chain evidence threshold ($3.6M vs $20M required). If RSI drops below 30 and SMA 200 holds, reassess.

---

## 24h Inversion Log

Yesterday's #1 setup (ETH short at $2,200) is **SUSPENDED**. The three pillars that powered it have all inverted in 24 hours:

| Pillar | Yesterday | Today |
|--------|-----------|-------|
| ETH Funding | +0.242% (longs crowded) | **-0.14%** (shorts crowded) |
| CEX Flows | Distribution (7.9x BTC inflows) | **Accumulation** (flows reversed) |
| Smart Money | Selling into bounces | **Top PnL accumulating 3.0x** |
| F&G | 11 (Extreme Fear) | **9** (more extreme) |
| BTC Funding | -0.049% | **-0.30%** (6x more extreme) |

This is why the pipeline exists — yesterday's conviction trade is today's danger zone. The data changed; the thesis changes.

---

## Session Summary

**The market is at peak fear.** F&G 9, BTC funding -0.30%, ETH funding flipped, CEX flows reversed from distribution to accumulation. Every contrarian signal is flashing simultaneously. The weekly trends remain unambiguously bearish — this is a bounce setup within a bear market, not a reversal.

The two setups reflect this: tactical MR longs at structural support with tight targets, not position trades. BTC is cleaner (no conflicting signals), ETH is more complex (two-phase with the short being the real money). Both are capped by the $3,024 available cash — small positions, small risk, but asymmetric R:R if the squeeze materializes.

**"Do nothing and wait" is still a valid option.** The bounce may not materialize. The weekly freight train doesn't care about your funding rate thesis. These are calculated bets at extreme levels, not high-conviction trend trades.
