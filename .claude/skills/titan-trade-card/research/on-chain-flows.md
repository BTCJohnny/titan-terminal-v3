# On-Chain Flow Analysis

## Purpose
Query Nansen for exchange flows, smart money, whale activity, fresh wallets, and top PnL trader behavior. Feeds into Flow Signals section and Accumulation Check.

## Required Queries

### 1. Recent Flows Summary (run twice: 1d and 7d)
```
mcp__nansen__token_recent_flows_summary:
  chain: "[chain]"
  contractAddress: "[address]"
  lookbackWindow: "1d"
```
```
mcp__nansen__token_recent_flows_summary:
  chain: "[chain]"
  contractAddress: "[address]"
  lookbackWindow: "7d"
```

### 2. Top Holders (run twice: smart_money and top_100_holders)
```
mcp__nansen__token_current_top_holders:
  chain: "[chain]"
  contractAddress: "[address]"
  labelType: "smart_money"
```
```
mcp__nansen__token_current_top_holders:
  chain: "[chain]"
  contractAddress: "[address]"
  labelType: "top_100_holders"
```

## Interpretation

| Pattern | Signal |
|---------|--------|
| Exchange outflows > 2x avg | Bullish — accumulation into cold storage |
| Exchange inflows > 2x avg | Bearish — preparing to sell |
| Whale accumulation + low volume | Bullish — quiet accumulation |
| Smart money absent + retail buying | Bearish — retail is exit liquidity |
| Fresh wallets >10x avg + no smart money | Bearish — likely unlocks/airdrops, not organic |
| All segments "no significant flow" | Neutral — market doesn't care about this token |

### Smart Money View

| Pattern | Signal |
|---------|--------|
| Large positions and/or increasing | Bullish — institutional conviction |
| Trivial amounts (<$10k) or absent | Bearish — no institutional interest |
| Present but static | Neutral — parked, not active |

### Top 100 View

| Pattern | Signal |
|---------|--------|
| Exchange wallets growing | Bearish — more supply on exchanges |
| DeFi protocol wallets shrinking | Bearish — positions unwinding |
| Team/foundation wallets shrinking | Bearish — insider selling |

## Output

Label overall flow as **Bullish**, **Bearish**, or **Mixed**. Write an interpretation paragraph: dominant direction, who's buying/selling, divergences, "So what?" conclusion.

## Exit Signal Integration

If the `nansen-exit-signal` skill is available (`.claude/skills/nansen-exit-signal/SKILL.md`), also run the exit signal check and include the verdict in this section. The exit signal uses 4 additional MCP calls (4 credits) and produces a 🔴/🟡/🟢 exit risk level. Include the exit risk verdict after the flow interpretation paragraph when running a full `/analyze`.

## Limitations
- Native tokens (BTC, ETH, SOL): flow tools may return limited data
- Low-cap tokens: may have insufficient on-chain data
- Multi-chain: query primary chain, note if significant activity elsewhere
