# Candidate Screening

## Purpose

For the `hunt-squeezes` command: systematically scan across tokens to find those with extreme positioning imbalances worth investigating with a full `scan-squeeze` analysis.

## Primary Tool

**Tool:** `mcp__nansen__smart_traders_and_funds_perp_trades`

**Parameters:**
- No specific `tokenId` — pull broad recent activity
- Sort by value/size to see largest positions first

## Screening Process

### Step 1: Pull Recent Perp Activity

Fetch recent smart money perpetual trades across all tokens. This gives a snapshot of where smart money is active in perps.

### Step 2: Group by Token

For each token with activity:
- Count long trades vs short trades
- Sum long $ vs short $
- Calculate one-sided percentage: `max_side / total * 100`

### Step 3: Filter for Extremes

| One-Sided % | Classification | Action |
|-------------|---------------|--------|
| >90% | Extreme | Priority candidate — run scan-squeeze |
| 70-90% | Significant | Strong candidate — run scan-squeeze |
| 50-70% | Mild lean | Skip — not extreme enough |
| ~50% | Balanced | Skip |

### Step 4: Quick Viability Check

Before running full `scan-squeeze`, quick-filter candidates:

1. **Liquidity check** — Is there enough open interest for a meaningful squeeze? Skip tokens with <$5M total OI.
2. **Volume check** — Is the token actively traded? Dead tokens don't squeeze.
3. **Recent price action** — Has the squeeze already happened? If price moved 20%+ in squeeze direction recently, the opportunity may be gone.

### Step 5: Rank and Select

Rank remaining candidates by:
1. One-sided percentage (higher = better)
2. Total dollar amount on crowded side (more fuel = bigger squeeze)
3. Number of traders on crowded side (distributed = better cascade)

Select **top 3** for full `scan-squeeze` analysis.

## Alternative Screening Method

If broad perp trade data is limited, use these as starting points:

1. **Tokens from watchlist** — Check perps positioning on tokens you're already tracking
2. **Recent movers** — Tokens that moved 10%+ recently may have forced liquidations building
3. **High funding rate tokens** — Extreme funding = extreme positioning
4. **Nansen token discovery** — Use `mcp__nansen__token_discovery_screener` to find trending tokens, then check their perps

## Output

After this step you should have:

```
Squeeze Hunt Screening:
Tokens scanned: N
Candidates identified: N

| Token | Long $ | Short $ | Ratio | One-Sided % | OI | Priority |
|-------|--------|---------|-------|-------------|-----|----------|
| TOKEN1 | $X.XM | $X.XM | X:1 | XX% | $XM | High |
| TOKEN2 | $X.XM | $X.XM | X:1 | XX% | $XM | Medium |

Top 3 for full analysis: [TOKEN1, TOKEN2, TOKEN3]
```
