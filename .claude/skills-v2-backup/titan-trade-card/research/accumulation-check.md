# Accumulation Check (5-Signal Scoring)

## Purpose
Score 5 on-chain signals. Count bullish signals for a 0-5 accumulation score. This is the single most important section — it tells you whether real money is entering the token.

## The 5 Signals

### 1. Exchange Flows
Source: `token_recent_flows_summary` (exchange segment)
- Net outflows from exchanges → **Bullish** (accumulation into cold storage)
- Net inflows to exchanges → **Bearish** (preparing to sell)
- No significant flow → **Neutral**

### 2. Fresh Wallets
Source: `token_recent_flows_summary` (fresh wallets segment)
- High inflows to new wallets (>3x avg) → **Bullish** (new buyers)
- Low/negative flows → **Bearish** (no new interest)
- **Caveat:** >10x avg + no smart money = likely unlocks/airdrops → rate **Bearish**

### 3. Smart Money
Source: `token_current_top_holders` (smart_money)
- Significant positions, increasing → **Bullish**
- Trivial amounts (<$10k) or absent → **Bearish**
- Present but static → **Neutral**

### 4. Top PnL Traders
Source: `token_recent_flows_summary` (top PnL segment)
- Net positive flow (buying) → **Bullish**
- Net negative flow (selling) → **Bearish**
- No significant flow → **Neutral**

### 5. Whale Activity
Source: `token_recent_flows_summary` (whale segment)
- Accumulating (net positive, multiple wallets) → **Bullish**
- Distributing (net negative) → **Bearish**
- No significant flow → **Neutral**

## Scoring

| Score | Label | Meaning |
|-------|-------|---------|
| 5/5 | Strong Accumulation | Every signal bullish |
| 4/5 | Accumulation | Strong on-chain conviction |
| 3/5 | Mild Accumulation | Mixed but leaning positive |
| 2/5 | Mixed | No clear direction |
| 1/5 | Distribution | Most signals bearish or absent |
| 0/5 | No Accumulation | Complete absence of buying |

**Neutral does NOT count as bullish.** 5 neutral signals = 0/5. Absence of accumulation IS the signal.

## Output Format
```
## Accumulation Check: [X]/5 — [Label]

| Signal | Rating | Detail |
|--------|--------|--------|
| Exchange Flows | [Rating] | [1-line explanation] |
| Fresh Wallets | [Rating] | [1-line explanation] |
| Smart Money | [Rating] | [1-line explanation] |
| Top PnL Traders | [Rating] | [1-line explanation] |
| Whale Activity | [Rating] | [1-line explanation] |
```

Always this exact table. 5 rows. Same column order.
