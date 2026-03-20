# Market Snapshot

## Purpose
Gather current price, market cap, rank, volume, FDV, supply, and recent changes.

## Tool
```
mcp__coinstats__get-coin-by-id: coinId "[coinstats-id]"
```

## Fields to Extract

| Field | Source Key | Format |
|-------|-----------|--------|
| Price | `price` | $X.XX (appropriate decimals) |
| Market Cap | `marketCap` | $X.XXB or $X.XXM |
| Rank | `rank` | #N |
| 24h Volume | `volume` | $X.XXM |
| FDV | `fullyDilutedValuation` | $X.XXB |
| Circulating Supply | `availableSupply` | X.XXB or X.XXM |
| Total Supply | `totalSupply` | X.XXB or X.XXM |
| 24h Change | `priceChange1d` | +X.XX% or -X.XX% |
| 7d Change | `priceChange1w` | +X.XX% or -X.XX% |

## Output Format
```
## Snapshot
**Price:** $X | **Market Cap:** $X | **Rank:** #X
**Volume:** $X | **FDV:** $X | **Supply:** XB / XB
**24h:** +X% | **7d:** -X%
```

Always this exact 3-line layout. No variation.

## Dilution Flags

- Supply ratio >90% circulating = minimal dilution risk
- 50-70% = moderate dilution (common for newer tokens)
- <50% = heavy dilution ahead — flag in verdict
- FDV/MCap ratio >2x = significant future selling pressure from unlocks
