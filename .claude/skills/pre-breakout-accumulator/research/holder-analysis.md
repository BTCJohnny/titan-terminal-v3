# Top 100 Holder Analysis

## Purpose
Check if top holders are net accumulating or distributing. Top 100 holder flows provide a broad view of whether large participants are adding to positions during the consolidation phase.

## Tool

```
Tool: mcp__nansen__token_current_top_holders
Parameters:
  tokenAddress: "[contract-address]"
  chain: "[chain]"
  labelType: "top_100_holders"
```

## What to Measure

### Net Supply Change

Calculate the net change in supply held by top 100 holders over the analysis window (typically 30 days):

| Supply Change | Score | Interpretation |
|---------------|-------|---------------|
| +10% supply | 2 pts | **Strong accumulation** — large holders aggressively buying |
| +5% supply | 1 pt | Moderate accumulation — steady inflows |
| < +5% supply | 0 pts | No significant accumulation |
| Negative | 0 pts | Distribution — holders reducing positions |

### Who's Accumulating vs Distributing

Break down the top 100 by category:

| Category | Bullish If | Bearish If |
|----------|-----------|------------|
| **Exchange wallets** | Shrinking (supply leaving) | Growing (supply entering) |
| **Fund/labeled wallets** | Growing positions | Reducing positions |
| **DeFi protocol wallets** | Stable or growing | Unwinding (deleveraging) |
| **Team/foundation wallets** | Stable | Shrinking (insider selling) |
| **Unlabeled wallets** | New large wallets appearing | Large wallets disappearing |

### Key Patterns

**Positive signal — ZRO:**
- Top 100 holders net accumulated +7.7M ZRO during the study period
- Most accumulation came from **unlabeled wallets** (not known entities)
- This suggests informed participants operating through fresh wallets

**Negative signal — distribution pattern:**
- Top 100 holders reducing positions
- Exchange wallets growing (more supply available for sale)
- Team wallets shrinking (insiders exiting)
- DeFi wallets unwinding (leveraged positions closing)

### Retail vs Institutional

A critical distinction:
- **Retail exchanges accumulating** (Robinhood, Upbit, Coinbase consumer) = retail buying
- **Institutional wallets accumulating** (funds, market makers, treasury) = institutional buying

Retail buying alone is NOT an accumulation signal for this skill. The LINK Trade Card showed retail (Robinhood +788k LINK) as the sole bid while institutions were absent — a distribution target, not accumulation.

**The signal is:** Non-retail, non-exchange top holders increasing positions while exchange supply decreases.

## Supplementary: Insider Activity

Check for notable insider moves within the top 100:
- Founder/CEO buys (highest alpha — see ZRO case study)
- Team multisig activity (distributions vs holding)
- Labeled "High Balance" wallets making moves during drawdowns

```
Tool: mcp__nansen__token_current_top_holders
Parameters:
  tokenAddress: "[contract-address]"
  chain: "[chain]"
  labelType: "smart_money"
```

## Limitations

- Top 100 is a snapshot, not a time series — you see current state and recent changes, not full history
- "Top 100" includes exchanges and contracts, which may not reflect directional conviction
- For native tokens, holder data may be less granular

## Output

Report:
- **Top 100 net supply change:** +X% over [period]
- **Key accumulators:** [names/labels if available]
- **Key distributors:** [names/labels]
- **Exchange wallet trend:** Growing / Shrinking
- **Insider activity:** Notable / None
- **Score:** X/2
