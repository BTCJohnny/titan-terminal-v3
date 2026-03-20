# Description: Detects when smart money is exiting a token. Combines flow intelligence, seller breakdown by wallet label, smart money netflow trends, and recent DEX trade activity to produce an exit risk verdict.
# Version: 1.0

name: nansen-exit-signal
version: 1.0
description: >
  Detects when smart money is exiting a token. Combines flow intelligence,
  seller breakdown by wallet label, smart money netflow trends, and recent
  DEX trade activity to produce an exit risk verdict. Use when checking if
  a held position is at risk of smart money distribution.

commands:
  - /nansen-exit: "Check if smart money is exiting a token you hold"

---

## Overview

Answers one question: **"Is smart money exiting a token I hold? Should I be worried?"**

Combines 4 Nansen MCP data sources into a single exit risk verdict. Costs 4 Nansen API credits per check — the cheapest on-chain signal in the toolkit.

---

## When To Use

- When the user asks about exit risk on a held position
- When `/analyze` is running and on-chain data is relevant
- When the user explicitly runs `/nansen-exit`
- When reviewing open paper trading positions for risk

---

## Required Inputs

- **TOKEN**: Token contract address OR token symbol. If symbol, use Nansen `general_search` to resolve to address first (0 credits).
- **CHAIN**: Blockchain (default: `ethereum`). Supported: ethereum, solana, base, arbitrum, polygon, bnb, optimism, avalanche.

---

## Step-by-Step Process

### Step 1 — Flow Intelligence (1 credit)

**Tool:** `mcp__nansen__token_recent_flows_summary`

Call with token address and chain. Extract `net_flow_usd` for each label category:
- `smart_trader` — the primary signal
- `whale`
- `exchange`
- `fresh_wallets`

**Key signal:** Negative `smart_trader` net flow = smart money is net selling.

### Step 2 — Who Is Selling (1 credit)

**Tool:** `mcp__nansen__token_who_bought_sold`

Call with token address, chain, limit 20. Examine the seller side:
- Which addresses have `address_label` containing "Smart Trader", "Fund", "Smart LP", or similar smart money labels?
- What's the `sold_volume_usd` for each?

**Key signal:** Smart money labels appearing as net sellers with significant USD volume.

### Step 3 — Smart Money Netflow Trend (1 credit)

**Tool:** `mcp__nansen__token_flows`

Call with token address and chain. Derive netflow direction across recent hourly periods.

**Key signal:** Sustained negative SM netflow across multiple hours = conviction selling, not just one whale rebalancing.

### Step 4 — Recent DEX Trades (1 credit)

**Tool:** `mcp__nansen__token_dex_trades`

Call with token address, chain, limit 20. Scan for `SELL` actions where `trader_address_label` contains smart money labels.

**Key signal:** Clustering of SM sell trades in recent hours.

---

## Decision Logic — The Verdict

### 🔴 HIGH EXIT RISK (Red Flag)

All three conditions present:
- Negative `smart_trader` net_flow_usd in flow intelligence
- Smart Trader/Fund labels appear as net sellers in who-bought-sold
- Sustained negative SM netflow across multiple hours

**Recommend:** Review position immediately. Consider partial exit or tightening stop.

### 🟡 ELEVATED CAUTION

One or more of:
- Negative smart_trader net_flow BUT small magnitude (<$50K)
- Only 1-2 SM wallets selling (could be single whale rebalancing)
- SM netflow negative in 1h but positive in 24h (short-term noise)

**Recommend:** Monitor closely. Check again in 4-8 hours.

### 🟢 NO EXIT SIGNAL

All conditions clean:
- Smart trader net_flow_usd is positive or flat
- No SM labels in major sellers
- SM netflow stable or positive

**Recommend:** Position looks clean from on-chain perspective.

---

## Edge Cases & Interpretation Guardrails

- **Do NOT** treat a single whale selling as a red flag — one wallet rebalancing is noise, not signal. Look for **multiple** SM wallets selling.
- **Do NOT** panic on exchange inflows alone — tokens moving to exchanges could be for staking, lending, or market-making, not just selling.
- **Do NOT** ignore magnitude — $10K of SM selling on a $500M market cap token is irrelevant. Scale the signal to the token's daily volume.
- **Do NOT** treat `fresh_wallets` selling as smart money — fresh wallets are often airdrop dumpers or bot wallets, not informed traders.
- **Do NOT** override TA signals with on-chain alone — this is ONE input. If TA shows strength but on-chain shows mild SM selling, it's a "watch" not a "sell."
- Remember the signal hierarchy: On-Chain > Perps > TA. But that means on-chain *confirms or denies* — it doesn't operate in isolation.

---

## Output Format

```markdown
## [🔴/🟡/🟢] Exit Signal: [TOKEN] on [CHAIN]

**Verdict:** [HIGH EXIT RISK / ELEVATED CAUTION / NO EXIT SIGNAL]

**Flow Intelligence:**
- Smart Trader net flow: [value] (negative = selling)
- Whale net flow: [value]
- Exchange net flow: [value]

**Top Smart Money Sellers:**
- [address_label]: sold $[amount]
- [address_label]: sold $[amount]

**SM Netflow Trend:** [direction over recent hours]

**Recent SM DEX Sells:** [count] sells totaling $[amount] in last [timeframe]

**Recommendation:** [action based on verdict]
```

---

## Parallel Execution

All 4 MCP calls are independent — launch them in parallel after token resolution:

```
Step 0: Token resolution (if symbol → general_search)
    ├── Step 1: Flow Intelligence        (parallel)
    ├── Step 2: Who Is Selling           (parallel)
    ├── Step 3: SM Netflow Trend         (parallel)
    └── Step 4: Recent DEX Trades        (parallel)
Step 5: Verdict synthesis (uses all data)
```

---

## Tool Inventory

| Step | Tool | Parameters | Credits |
|------|------|------------|---------|
| Token Resolve | `mcp__nansen__general_search` | `query: "[symbol]"` | 0 |
| Flow Intelligence | `mcp__nansen__token_recent_flows_summary` | `chain`, `contractAddress` | 1 |
| Who Bought/Sold | `mcp__nansen__token_who_bought_sold` | `chain`, `contractAddress`, `limit: 20` | 1 |
| SM Netflow | `mcp__nansen__token_flows` | `chain`, `contractAddress` | 1 |
| DEX Trades | `mcp__nansen__token_dex_trades` | `chain`, `contractAddress`, `limit: 20` | 1 |

**Total per check: 4 credits** (+ 0 if symbol resolution needed)

---

## Persona

Same Titan persona applies:
- **Verdict first** — "🔴 HIGH EXIT RISK" or "🟢 Clean" before the breakdown
- **Quantify everything** — Dollar amounts, wallet counts, timeframes
- **No hedging** — "Smart money is exiting" or "No exit signal" — never "might be exiting"
- **Contrarian lens** — If everyone is selling, who's the exit liquidity? If no one's selling, is the crowd complacent?
