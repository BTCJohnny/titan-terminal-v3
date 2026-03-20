# Verdict Synthesis

## Purpose
Combine all 4 pillars into a single directional call. The verdict is the most important part of the Trade Card.

## Signal Weight Hierarchy
```
On-Chain Flows & Accumulation  >  Perps Positioning  >  Technical Analysis
```

On-chain = what people DO. Perps = what smart traders BET. TA = what price DID (lags). Higher weight wins conflicts.

## Decision Matrix

### All Pillars Agree
| TA | On-Chain | Perps | Verdict |
|----|----------|-------|---------|
| Bullish | Accumulation (4-5) | Net Long | **Bullish — High Conviction** |
| Bearish | Distribution (0-1) | Net Short | **Bearish — High Conviction** |
| Neutral | Mixed (2-3) | Balanced | **Neutral — No Edge, Wait** |

### On-Chain vs TA Conflicts (on-chain wins)
| TA | On-Chain | Resolution |
|----|----------|------------|
| Bullish | Distribution (0-1) | **Bearish** — Smart money selling into strength |
| Bearish | Accumulation (4-5) | **Bullish** — Smart money buying the dip |
| Neutral | Accumulation (4-5) | **Bullish (Watch)** — Setup building, wait for TA confirmation |

### Perps vs On-Chain Conflicts (on-chain wins)
| On-Chain | Perps | Resolution |
|----------|-------|------------|
| Accumulation | Net Short | **Cautious Bullish** — On-chain trumps, smaller size |
| Distribution | Net Long | **Bearish** — Trapped longs add selling pressure |

## Confidence Modifiers

**Strengthens:** All pillars agree, accumulation at extremes (0 or 5), large perps positions, multiple smart money wallets confirming, ADX > 25.

**Weakens:** Conflicting pillars, accumulation 2-3, low liquidity, ADX < 15, token unlock distorting flows.

## Verdict Format

1. **Direction:** Bullish / Bearish / Neutral
2. **One-sentence thesis** — quotable, captures the entire setup
3. **4-6 verdict points** with descriptive emojis, strongest signal first
4. **Closing instruction** — specific entry/stop OR "do not touch" + reversal conditions

## Verdict Vocabulary

Use exactly one: **Bullish**, **Bearish**, **Neutral**

Thesis examples:
- "Dead money. No accumulation, no smart money interest, persistent downtrend with zero reversal signals."
- "Accumulation zone. Smart money at range lows while retail sells."
- "Ghost chain. Zero on-chain activity, perps overwhelmingly short, only retail buying."

## Closing Statement

- Bullish: Specific entry zone, stop level, what accumulation score supports
- Bearish: "Do not touch this." + specific conditions that would change the call
- Neutral: "Wait for [catalyst]. Check back when [condition]."

Be ruthless. If the data says avoid it, say so without softening.
