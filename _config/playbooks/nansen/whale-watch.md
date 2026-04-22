# Whale Watch

## Purpose
Track large holder movements for a specific token — who's accumulating, who's distributing.

## How to Use
Say: "Whale watch on [TOKEN]" or "Track whales for [TOKEN]"

Examples:
- "Whale watch on ETH"
- "Track whales for SOL"
- "Who are the big holders of AAVE?"
- "Whale activity on BTC"

## What It Does

1. Gets top 25 holders by balance
2. Checks 24h/7d/30d balance changes
3. Identifies whale buying (inflows > outflows)
4. Identifies whale selling (outflows > inflows)
5. Flags notable movements

## Output Format

```
## Whale Watch: [TOKEN]

### Top Holders

| Rank | Label | Balance | 24h Change | 7d Change |
|------|-------|---------|------------|-----------|
| 1 | [label] | $X.XM | +X% | +X% |

### Whale Sentiment: [Accumulating/Distributing/Neutral]

**Accumulating:** X whales increasing positions
**Distributing:** X whales decreasing positions
**Stable:** X whales unchanged

### Notable Moves
- [Whale] added $X.XM in 24h
- [Whale] sold $X.XM this week

### Interpretation
[What whale behavior suggests about price direction]
```

## Tools Used

1. `token_current_top_holders` — Top holders by balance
   ```
   chain: [chain], tokenAddress: [address], labelType: "top_100_holders", order_by: "amount"
   ```

2. `token_current_top_holders` — Whale segment specifically
   ```
   chain: [chain], tokenAddress: [address], labelType: "whale"
   ```

3. `token_who_bought_sold` — Recent whale buying/selling
   ```
   chain: [chain], tokenAddress: [address], include_labels: ["Whale"], time_range: {from: "7D_AGO", to: "NOW"}
   ```

## Interpretation Guide

**Whales Accumulating:**
- Multiple top holders increasing positions
- 24h changes positive across the board
- Often precedes price appreciation

**Whales Distributing:**
- Top holders reducing positions
- Large outflows in recent days
- Can signal upcoming selling pressure

**Mixed/Neutral:**
- Some buying, some selling
- No clear directional bias
- Wait for clearer signal

## Watch For

- **Concentration risk:** If top 10 hold >50%, whale moves have outsized impact
- **Exchange wallets:** Exchanges in top holders = available supply
- **Labeled whales:** Known entities (funds, projects) vs anonymous
