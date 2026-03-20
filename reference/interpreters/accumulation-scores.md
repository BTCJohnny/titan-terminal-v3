# Accumulation Scores Interpreter

## What Is the Accumulation Score?

A 0-5 score based on 5 on-chain signals that indicate whether smart money is accumulating or distributing a token.

## The 5 Signals

| # | Signal | Bullish (✓) | Bearish (✗) |
|---|--------|-------------|-------------|
| 1 | Exchange Flows | Outflows (leaving CEX) | Inflows (to CEX) |
| 2 | Fresh Wallets | High inflows (new buyers) | Low/negative |
| 3 | Smart Money | Buying/holding | Selling |
| 4 | Top PnL Traders | Net positive | Net negative |
| 5 | Whale Activity | Accumulating | Distributing |

Each bullish signal = +1 point.

## Score Interpretation

| Score | Status | Trading Implication |
|-------|--------|---------------------|
| 5/5 | Strong Accumulation | High conviction long |
| 4/5 | Accumulation | Confident long |
| 3/5 | Mixed | Wait for clarity or reduce size |
| 2/5 | Leaning Distribution | Caution, avoid new longs |
| 1/5 | Distribution | Consider shorts or avoid |
| 0/5 | Strong Distribution | High conviction short or stay away |

## How Each Signal Works

### 1. Exchange Flows
**Source:** `token_recent_flows_summary` → Exchange segment

| Reading | Meaning |
|---------|---------|
| Negative flow (outflows) | ✓ Bullish — tokens leaving exchanges |
| Positive flow (inflows) | ✗ Bearish — tokens going to sell |

### 2. Fresh Wallets
**Source:** `token_recent_flows_summary` → Fresh Wallets segment

| Reading | Meaning |
|---------|---------|
| Positive inflows | ✓ Bullish — new buyers entering |
| Negative/zero | ✗ Bearish — no new interest |

### 3. Smart Money
**Source:** `token_current_top_holders` with `labelType: smart_money`

| Reading | Meaning |
|---------|---------|
| Increasing positions | ✓ Bullish — smart money buying |
| Decreasing positions | ✗ Bearish — smart money selling |

### 4. Top PnL Traders
**Source:** `token_recent_flows_summary` → Top PnL segment

| Reading | Meaning |
|---------|---------|
| Net positive flow | ✓ Bullish — profitable traders buying |
| Net negative flow | ✗ Bearish — profitable traders selling |

### 5. Whale Activity
**Source:** `token_who_bought_sold` or `token_flows` (whale segment)

| Reading | Meaning |
|---------|---------|
| More buying than selling | ✓ Bullish — whales accumulating |
| More selling than buying | ✗ Bearish — whales distributing |

## Real-World Examples

### Strong Accumulation (5/5)
```
✓ Exchange flows: -$12M (outflows)
✓ Fresh wallets: +$8M inflows
✓ Smart money: 3 funds added positions
✓ Top PnL: Net +$5M
✓ Whales: $20M bought vs $3M sold

Score: 5/5 — Strong Accumulation
Action: High conviction long setup
```

### Mixed (3/5)
```
✓ Exchange flows: -$2M (small outflows)
✗ Fresh wallets: Flat
✓ Smart money: Holding steady
✗ Top PnL: Slight selling
✓ Whales: Modest accumulation

Score: 3/5 — Mixed
Action: Wait for clearer signals or small position
```

### Distribution (1/5)
```
✗ Exchange flows: +$30M (inflows)
✗ Fresh wallets: Negative
✗ Smart money: Reducing positions
✗ Top PnL: Heavy selling
✓ Whales: Still holding (but not adding)

Score: 1/5 — Distribution
Action: Avoid longs, consider shorts
```

## Using the Score

### Entry Decisions
| Score | Position Size |
|-------|---------------|
| 5/5 | Full size per limits |
| 4/5 | 75% of normal |
| 3/5 | 50% or wait |
| 2/5 | Avoid or 25% |
| 0-1/5 | No long, maybe short |

### Exit Decisions
- Score dropping from 4+ to 2- = Consider taking profits
- Score improving while in position = Hold or add

## Limitations

1. **Lagging indicator** — Reflects recent activity, not future
2. **Varies by token** — Memecoins behave differently than blue chips
3. **Market regime** — Bull markets tolerate lower scores
4. **Not timing** — Doesn't tell you exactly when to enter

## Where to Find This Data

**Run accumulation check:**
Say "Run the accumulation check for [TOKEN]" to Claude.

**Playbook location:**
`reference/playbooks/nansen/accumulation-check.md`
