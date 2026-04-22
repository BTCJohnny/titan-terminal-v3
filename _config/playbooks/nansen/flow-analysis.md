# Flow Analysis

## Purpose
Analyze exchange inflows and outflows to gauge buying vs selling pressure.

## How to Use
Say: "Flow analysis for [TOKEN]" or "Check exchange flows for [TOKEN]"

Examples:
- "Flow analysis for ETH"
- "Exchange flows on BTC"
- "Is money flowing into or out of SOL?"
- "CEX flow check for LINK"

## What It Does

1. Gets total flows by segment (Exchange, Smart Money, Whales, Fresh Wallets)
2. Compares inflows vs outflows for each segment
3. Calculates net flow direction
4. Compares to historical average

## Key Concept

**Exchange Inflows** = Tokens moving TO exchanges = Selling pressure
**Exchange Outflows** = Tokens leaving exchanges = Accumulation

Counterintuitive but critical:
- High inflows → Bearish (people depositing to sell)
- High outflows → Bullish (people withdrawing to hold)

## Output Format

```
## Flow Analysis: [TOKEN]

### Segment Flows (Last 24h)

| Segment | Flow | vs Average | Signal |
|---------|------|------------|--------|
| Exchange | -$X.XM | X.Xx | Bullish (outflows) |
| Smart Money | +$X.XM | X.Xx | Bullish (buying) |
| Whales | -$X.XM | X.Xx | Bearish (selling) |
| Fresh Wallets | +$X.XM | X.Xx | Bullish (new buyers) |
| Top PnL | +$X.XM | X.Xx | Bullish |

### Net Flow: [Bullish/Bearish/Neutral]

**Summary:** [1-2 sentence interpretation]
```

## Tools Used

1. `token_recent_flows_summary` — Quick segment snapshot
   ```
   chain: [chain], tokenAddress: [address], lookbackPeriod: "1d"
   ```

2. `token_flows` — Hourly breakdown for detailed analysis
   ```
   chain: [chain], tokenAddress: [address], holder_segment: "exchange", dateRange: {from: "7D_AGO", to: "NOW"}
   ```

## Interpretation Guide

**Strong Bullish:**
- Exchange outflows (negative exchange flow)
- Smart money inflows
- Fresh wallet inflows
- Top PnL traders buying

**Strong Bearish:**
- Exchange inflows (positive exchange flow)
- Smart money outflows
- Whale distribution
- Top PnL traders selling

**Mixed:**
- Conflicting signals across segments
- Flows near average
- Wait for clearer direction

## Lookback Periods

| Period | Use Case |
|--------|----------|
| 5m, 1h | Intraday trading, scalping |
| 6h, 12h | Short-term swing setups |
| 1d | Standard analysis (default) |
| 7d | Trend confirmation |

## Historical Context

The "vs Average" ratio is key:
- **>2x average** = Significant move
- **1-2x average** = Moderate activity
- **<1x average** = Below normal
