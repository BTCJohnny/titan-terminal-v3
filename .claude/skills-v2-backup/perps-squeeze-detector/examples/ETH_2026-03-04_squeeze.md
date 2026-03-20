# ETH Short Squeeze — 2026-03-04

**The case study that inspired the perps-squeeze-detector skill.**

---

## Discovery Context

During a routine ETH analysis, HL smart money perps data revealed a 61:1 short imbalance — $80M+ short vs $1.3M long. This extreme crowding, combined with BTC breaking $70k, created a high-conviction short squeeze setup.

---

## Positioning Summary

**Long:** ~$1.3M across 2 traders
**Short:** ~$80M+ across multiple smart money entities
**Imbalance:** 61:1 short-heavy
**Concentration:** Distributed across multiple funds — strong cascade potential

### Key Short Positions

| Trader | Size | Entry | Liq Price | Status |
|--------|------|-------|-----------|--------|
| Multiple SM entities | $80M+ total | Various ~$2,000 | $2,203-$2,478 | Underwater as price approached $2,100 |

---

## Liquidation Cascade Map

**Squeeze Direction:** Short squeeze (price UP)
**Trigger Line:** $2,203 (6.8% from ~$2,063)
**Total Cascade Fuel:** $23.7M forced buying between $2,203-$2,478

| Zone | Price Range | Forced Buy Pressure | Cumulative |
|------|-------------|---------------------|------------|
| Trigger | $2,203 | First liquidations | ~$5M |
| Acceleration | $2,203-$2,478 | Cascade builds | $23.7M |
| Exhaustion | >$2,478 | Fuel runs out | $23.7M total |

**Key insight:** $23.7M in forced buying is significant mechanical pressure. Once the trigger line breaks, the cascade is self-reinforcing.

---

## Macro Context

| Factor | Assessment | Detail |
|--------|-----------|--------|
| CEX Flows | **Opposing** | ETH showing net distribution on CEX — spot selling |
| BTC Momentum | **Supportive** | BTC broke $70k — altcoin catalyst activated |
| Funding Rate | **Supportive** | Negative funding — shorts paying, pressure building |
| Position Trend | **Fuel adding** | New shorts still opening |
| Spot Divergence | **YES** | Spot distributing BUT perps massively short = divergence |

**Catalyst Score:** 3/5

**Critical insight:** The divergence between spot distribution and perps crowding is what made this setup unique. Spot says sell, perps says sell harder — but perps is SO crowded that the mechanical unwind overpowers the spot flow.

---

## Squeeze Score: 8/10 — Alpha

| Signal | Score | Detail |
|--------|-------|--------|
| Position Imbalance | 3/3 | 61:1 short-heavy — extreme by any measure |
| Liquidation Proximity | 1/2 | First liq at $2,203 (6.8%) — reachable but not imminent |
| Cascade Density | 2/2 | $23.7M forced buying in single cascade zone |
| Macro Catalyst | 1/2 | BTC catalyst present but CEX flows oppose |
| Spot Divergence | 1/1 | Spot distributing vs perps short = max divergence |

---

## Trade Setup

### Primary: Long (Short Squeeze)

| Level | Price | Distance | Rationale |
|-------|-------|----------|-----------|
| Entry | $2,063 | — | Current price, before trigger line |
| Stop | $1,950 | -5.5% | Below recent structure and round number |
| Target 1 | $2,475 | +20.0% | Cascade exhaustion zone |
| Target 2 | $2,650 | +28.4% | Extension beyond cascade (momentum overshoot) |
| R:R | 3.6:1 | — | To T1. Excellent asymmetry. |

### Secondary: Short After Squeeze

| Level | Price | Rationale |
|-------|-------|-----------|
| Entry | $2,475-$2,500 | Where cascade fuel exhausts |
| Stop | $2,650 | Above extension zone |
| Target | $2,200 | Back to pre-squeeze levels |

---

## Key Lessons

1. **61:1 ratios are rare** — When you see one, pay attention. This level of crowding almost always unwinds.

2. **Divergence is the conviction multiplier** — Spot said "distribute" but perps were so crowded short that the mechanical cascade overwhelmed the spot selling. The disagreement between spot and perps was the signal.

3. **BTC as catalyst** — For altcoin squeezes, BTC breaking a key level is often the match that lights the fuse. The $70k break provided the initial push toward the trigger line.

4. **CEX headwind isn't disqualifying** — Distribution backdrop reduced the score by 1 point but didn't invalidate the setup. Mechanical liquidation pressure ($23.7M) > spot flow pressure in this case.

5. **The cascade is math, not opinion** — Once $2,203 breaks, the forced buying is mechanical. No one decides to buy — they're forced to close. This is what makes squeeze setups different from regular technical analysis.

---

## Outcome

*[To be updated when trade resolves]*

Status: PENDING
Entry: $2,063
Stop: $1,950
T1: $2,475
T2: $2,650
