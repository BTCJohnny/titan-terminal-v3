# Token Deep Dive

## Purpose
Comprehensive on-chain analysis combining all Nansen data for a complete token profile.

## How to Use
Say: "Deep dive on [TOKEN]" or "Full Nansen analysis for [TOKEN]"

Examples:
- "Deep dive on ETH"
- "Full on-chain analysis for AAVE"
- "Nansen deep dive on SOL"
- "Complete token profile for LINK"

## What It Does

Combines multiple Nansen queries into a complete picture:

1. **Token Overview** — Price, market cap, holder stats
2. **Accumulation Check** — 5-signal scoring
3. **Top Holders** — Who owns this token
4. **Smart Money Activity** — Fund positioning
5. **Recent Flows** — Exchange and segment flows
6. **PnL Leaders** — Who's profitable on this token
7. **Recent Trades** — Notable DEX activity

## Output Format

```
# [TOKEN] — On-Chain Deep Dive

## Overview
**Price:** $X | **Market Cap:** $X | **Holders:** X

---

## Accumulation Check: [Score]/5 — [Status]
[5-signal breakdown]

---

## Top Holders
| Rank | Label | Balance | Ownership % | 7d Change |
|------|-------|---------|-------------|-----------|

---

## Smart Money Positioning
[Fund and smart trader activity]

---

## Flow Analysis (24h)
| Segment | Flow | Signal |
|---------|------|--------|

---

## Top PnL Traders
| Trader | Total PnL | ROI | Still Holding |
|--------|-----------|-----|---------------|

---

## Recent Large Trades
| Time | Action | Size | Trader |
|------|--------|------|--------|

---

## Verdict
**[Bullish/Bearish/Neutral]** — [Summary]

Key Points:
- [Most important finding]
- [Second key insight]
- [Risk to watch]
```

## Tools Used

1. `general_search` — Get token address and basic info
   ```
   query: [TOKEN], result_type: "token"
   ```

2. `token_recent_flows_summary` — Segment flows
   ```
   chain: [chain], tokenAddress: [address], lookbackPeriod: "1d"
   ```

3. `token_current_top_holders` — Top 100 holders
   ```
   chain: [chain], tokenAddress: [address], labelType: "top_100_holders"
   ```

4. `token_current_top_holders` — Smart money holders
   ```
   chain: [chain], tokenAddress: [address], labelType: "smart_money"
   ```

5. `token_pnl_leaderboard` — Top performers
   ```
   chain: [chain], tokenAddress: [address], dateRange: {from: "30D_AGO", to: "NOW"}
   ```

6. `token_dex_trades` — Recent DEX activity
   ```
   chain: [chain], tokenAddress: [address], dateRange: {from: "24H_AGO", to: "NOW"}, order_by: "valueUsd"
   ```

7. `token_ohlcv` — Price data
   ```
   chain: [chain], tokenAddress: [address], date: {from: "7D_AGO", to: "NOW"}
   ```

## When to Use

- **Before opening a position** — Full due diligence
- **Large position sizing** — Need complete picture
- **Conflicting signals** — Want more data points
- **Unknown token** — First-time research

## Time Estimate

This playbook makes 6-8 API calls, so expect ~30-60 seconds for full analysis.

## Customization

For faster analysis, request specific sections:
- "Deep dive on ETH, focus on smart money"
- "AAVE deep dive, skip recent trades"
- "Just the accumulation check and top holders for SOL"
