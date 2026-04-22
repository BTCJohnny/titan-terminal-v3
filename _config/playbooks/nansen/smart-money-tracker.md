# Smart Money Scan

## Purpose
Discover what funds and smart traders are accumulating across the market.

## How to Use
Say: "Run the smart money scan" or "What is smart money buying?"

Examples:
- "Smart money scan"
- "What are funds accumulating?"
- "Smart money scan on Solana"
- "What's smart money buying on Base?"

## What It Does

1. Queries smart money token balances across chains
2. Identifies tokens with significant fund accumulation
3. Filters for meaningful positions (not dust)
4. Shows 24h balance changes to spot fresh accumulation

## Parameters

| Parameter | Default | Options |
|-----------|---------|---------|
| Chains | all | ethereum, solana, base, bnb, arbitrum, etc. |
| Smart Money Labels | All | Fund, All Time Smart Trader, 30D Smart Trader |

## Output Format

```
## Smart Money Scan — [Date]

### Top Fund Holdings (24h Change)

| Token | Chain | Balance USD | 24h Change |
|-------|-------|-------------|------------|
| [TOKEN] | [chain] | $X.XM | +X.X% |

### Notable Moves
- [Insight about significant accumulation]
- [Insight about new positions]

### Interpretation
[What this means for market direction]
```

## Tools Used

1. `smart_traders_and_funds_token_balances` — Aggregated smart money holdings
   ```
   chains: ["ethereum", "solana", "base"], includeSmartMoneyLabels: ["Fund", "All Time Smart Trader"]
   ```

2. `token_discovery_screener` — Find tokens with smart money activity
   ```
   onlySmartTradersAndFunds: true, orderBy: "netflow", timeframe: "24h"
   ```

## Interpretation Guide

**High Fund Accumulation:**
When multiple funds are adding to the same token, it often signals institutional conviction.

**Fresh Positions:**
New positions (not just adding to existing) can indicate early-stage accumulation before a move.

**Declining Positions:**
Funds reducing positions may be taking profits or de-risking.

## Filters to Consider

- **Minimum position size:** $100K+ to filter dust
- **24h change threshold:** >5% change to spot active accumulation
- **Multiple funds:** 2+ funds in same token = higher conviction
