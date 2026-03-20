# Accumulation Check

## Purpose
Score a token's accumulation signals (0-5) using on-chain data to determine if smart money is buying or selling.

## How to Use
Say: "Run the accumulation check for [TOKEN]"

Examples:
- "Run the accumulation check for ETH"
- "Accumulation check on SOL"
- "Check accumulation for AAVE"

## What It Does

Evaluates 5 key signals and scores each as Bullish or Bearish:

| Signal | Tool | Bullish | Bearish |
|--------|------|---------|---------|
| Exchange Flows | `token_recent_flows_summary` | Outflows (leaving CEX) | Inflows (to CEX) |
| Fresh Wallets | `token_recent_flows_summary` | High inflows (new buyers) | Low/negative |
| Smart Money | `token_current_top_holders` (smart_money) | Buying/holding | Selling |
| Top PnL Traders | `token_recent_flows_summary` | Net positive | Net negative |
| Whale Activity | `token_flows` or `token_who_bought_sold` | Accumulating | Distributing |

## Scoring

| Score | Interpretation |
|-------|----------------|
| 4-5 | Strong accumulation — Smart money buying |
| 2-3 | Mixed signals — Wait for clarity |
| 0-1 | Distribution — Smart money selling |

## Output Format

```
## Accumulation Check: [Score]/5 — [Accumulating/Mixed/Distributing]

- Exchange flows: [Bullish/Bearish] — [detail]
- Fresh wallets: [Bullish/Bearish] — [detail]
- Smart money: [Bullish/Bearish] — [detail]
- Top PnL traders: [Bullish/Bearish] — [detail]
- Whale activity: [Bullish/Bearish] — [detail]
```

## Tools Used

1. `token_recent_flows_summary` — Get segment flows (exchange, fresh wallets, top PnL)
   ```
   chain: [chain], tokenAddress: [address], lookbackPeriod: "1d"
   ```

2. `token_current_top_holders` — Check smart money positions
   ```
   chain: [chain], tokenAddress: [address], labelType: "smart_money"
   ```

3. `token_who_bought_sold` — Whale buying/selling activity
   ```
   chain: [chain], tokenAddress: [address], buy_or_sell: "BUY"/"SELL", time_range: {from: "7D_AGO", to: "NOW"}
   ```

## Interpretation Guide

**Strong Accumulation (4-5):**
Smart money and whales are buying while exchange outflows increase. This often precedes price moves up.

**Mixed (2-3):**
Conflicting signals. Some smart money buying, some selling. Wait for clearer direction.

**Distribution (0-1):**
Smart money exiting. Exchange inflows indicate selling pressure. Risk of price decline.
