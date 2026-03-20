# Stage: 03_onchain — On-Chain Flows + Accumulation Scoring

## Purpose

Determine who is buying, who is selling, and whether the on-chain evidence supports accumulation or distribution. Produces a 5-signal accumulation score (0-5).

## Inputs

| Source | File | Layer |
|--------|------|-------|
| Previous stage | `../01_resolve/output/identity.md` | 4 (working) |
| Reference | `_config/interpreters/accumulation-scores.md` | 3 (factory) |
| Reference | `_config/interpreters/smart-money-moves.md` | 3 (factory) |
| Reference | `_config/interpreters/cex-flows.md` | 3 (factory) |
| Reference | `_config/thesis.md` | 3 (factory) |

## Process

Check Nansen cache for each call before making live requests (see pipeline CONTEXT.md for cache instructions).

### Step 1: Flow Summary (parallel — 2 calls)

```
mcp__nansen__token_recent_flows_summary: chain "[chain]", tokenAddress "[address]", lookbackPeriod "1d"
mcp__nansen__token_recent_flows_summary: chain "[chain]", tokenAddress "[address]", lookbackPeriod "7d"
```

Extract: net flows by segment (smart_trader, whale, exchange, fresh_wallets), total inflows/outflows.

### Step 2: Top Holders (parallel — 2 calls)

```
mcp__nansen__token_current_top_holders: chain "[chain]", tokenAddress "[address]", labelType "smart_money"
mcp__nansen__token_current_top_holders: chain "[chain]", tokenAddress "[address]", labelType "top_100_holders"
```

Extract: who holds, position sizes, any recent position changes, named funds vs anonymous wallets.

### Step 3: Interpret Flows

Using `_config/interpreters/cex-flows.md` and `_config/interpreters/smart-money-moves.md`:
- Are exchange flows showing accumulation (outflows) or distribution (inflows)?
- Are smart money wallets adding or reducing?
- Any divergence between smart money and retail flow?
- What's the "So what?" — one-sentence conclusion.

### Step 4: Score Accumulation

Using `_config/interpreters/accumulation-scores.md`, score 5 signals:

| Signal | Source | Bullish | Bearish |
|--------|--------|---------|---------|
| Exchange Flows | flow_summary | Net outflows (leaving CEX) | Net inflows (to CEX) |
| Fresh Wallets | flow_summary | High new wallet inflow | Low/negative |
| Smart Money | top_holders smart_money | Buying/holding | Selling/reducing |
| Top PnL Traders | flow_summary | Net positive flow | Net negative flow |
| Whale Activity | top_holders top_100 | Accumulating | Distributing |

Score: 5/5 = Strong Accumulation, 4/5 = Accumulation, 3/5 = Mild Accumulation, 2/5 = Mixed, 1/5 = Distribution, 0/5 = Strong Distribution.

## Scripts Used

- `python3 src/storage/nansen_cache.py check/store`

## Outputs

| File | Contents |
|------|----------|
| `output/flows.md` | Exchange flows (1d + 7d), smart money direction, whale activity, interpretation prose with "So what?" |
| `output/accumulation.md` | 5-signal score table with ratings, overall label, one-sentence thesis |

## Review Gate

- Does the accumulation score match your gut read of on-chain activity?
- Any data gaps (Nansen failures) that reduce confidence?
- Does on-chain contradict the TA direction? (If so, on-chain wins per signal hierarchy)
