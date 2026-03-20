# Squeeze Score

## Purpose

Synthesize all research signals into a single 0-10 Squeeze Score that determines conviction level and recommended action.

## Scoring Methodology

### Signal 1: Position Imbalance (0-3 points)

The foundation — how extreme is the crowding?

| Imbalance Ratio | Points | Notes |
|-----------------|--------|-------|
| <3:1 | 0 | Not extreme enough |
| 3:1 - 5:1 | 1 | Significant but not compelling alone |
| 5:1 - 10:1 | 2 | Extreme — squeeze setup forming |
| 10:1+ | 3 | Critical — high probability squeeze |

**Bonus:** +0.5 if position concentration is distributed (many traders, not one whale). Round final score.

### Signal 2: Liquidation Proximity (0-2 points)

How close is the trigger line to current price?

| Distance to First Liquidation | Points | Notes |
|-------------------------------|--------|-------|
| >10% | 0 | Too far — needs major catalyst |
| 5-10% | 1 | Reachable with moderate catalyst |
| <5% | 2 | Imminent — any push triggers cascade |

### Signal 3: Cascade Density (0-2 points)

How much forced pressure does the cascade generate?

| Cumulative Forced Pressure (First Cluster) | Points | Notes |
|---------------------------------------------|--------|-------|
| <$5M | 0 | Insufficient to move price meaningfully |
| $5M - $10M | 1 | Moderate impact, needs volume support |
| $10M+ | 2 | Significant mechanical pressure |

**Adjustment:** Scale relative to token's daily volume. $5M on a $10M/day token is more impactful than $5M on a $500M/day token.

### Signal 4: Macro Catalyst (0-2 points)

Does the environment support the squeeze?

| Catalyst Score (from macro-context.md) | Points | Notes |
|----------------------------------------|--------|-------|
| Negative (macro opposes) | 0 | Fighting the trend |
| 0-2 (neutral/mild) | 1 | Needs specific trigger |
| 3-5 (strong support) | 2 | Macro aligned — catalyst present |

### Signal 5: Spot Divergence (0-1 point)

The conviction multiplier — spot and perps disagree.

| Divergence | Points | Notes |
|------------|--------|-------|
| Spot agrees with perps direction | 0 | Consensus — crowded side may be right |
| Spot disagrees with perps direction | 1 | Divergence — one side is wrong |

## Score Calculation

```
Squeeze Score = Imbalance (0-3) + Proximity (0-2) + Density (0-2) + Macro (0-2) + Divergence (0-1)
```

**Maximum: 10**

## Interpretation

| Score | Rating | Action |
|-------|--------|--------|
| 8-10 | **Alpha** | High conviction squeeze play — generate trade setup |
| 6-7 | **Strong** | Consider entry, wait for trigger confirmation |
| 4-5 | **Moderate** | Add to watchlist, needs catalyst development |
| 0-3 | **Weak** | No squeeze setup — pass |

## Score Breakdown Format

Present as:

```
## Squeeze Score: X/10 — [Alpha/Strong/Moderate/Weak]

| Signal | Score | Detail |
|--------|-------|--------|
| Position Imbalance | X/3 | X:1 [direction]-heavy |
| Liquidation Proximity | X/2 | First liq at $X,XXX (X.X%) |
| Cascade Density | X/2 | $X.XM forced pressure in Zone 1 |
| Macro Catalyst | X/2 | [Summary of catalyst environment] |
| Spot Divergence | X/1 | [Agrees/Disagrees] — [detail] |
```

## Edge Cases

- **Score 8+ but concentrated in one whale:** Reduce effective score by 1. One trader can unwind quietly without cascade.
- **Score 6-7 with strong divergence:** The divergence point makes it worth watching closely even without full score.
- **Score 8+ but squeeze already partially triggered:** If price already moved 10%+ toward liquidations, remaining fuel matters more than initial score. Recalculate with remaining positions only.
