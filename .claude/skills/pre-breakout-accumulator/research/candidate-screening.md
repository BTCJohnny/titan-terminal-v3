# Candidate Screening (hunt-setups)

## Purpose
Top-down market scan to identify tokens that may be in a pre-breakout accumulation phase. This is Step 1 of the `hunt-setups` command — filter the universe down to a manageable candidate list before running full analysis.

## Tool: Token Discovery Screener

```
Tool: mcp__nansen__token_discovery_screener
Parameters:
  orderBy: "netflow"             # Sort by net flow to find tokens with outflows
  timeframe: "7d"                # 7-day window
  onlySmartTradersAndFunds: true # Focus on smart money activity
```

**Alternative screening parameters:**

```
# By smart money activity
orderBy: "smart_money_netflow"
timeframe: "30d"

# By volume (looking for dry-ups)
orderBy: "volume"
timeframe: "24h"

# By market cap range (filter by size)
minMarketCap: 50000000         # $50M minimum
maxMarketCap: 5000000000       # $5B maximum
```

## Screening Criteria

### Quick Filters (eliminate non-candidates fast)

| Filter | Threshold | Why |
|--------|-----------|-----|
| Market cap | $50M - $5B | Below $50M = too illiquid. Above $5B = harder to accumulate quietly |
| 30d price change | < +10% | Price should NOT already be running. Looking for flat/down |
| Volume trend | Declining or stable | Rising volume = already in play, not quiet accumulation |
| Smart money flow | Positive or neutral | If smart money is actively selling, skip |

### Signal Check (for candidates passing quick filters)

For each candidate, do a rapid check of:

1. **Price at range low?** — Is current price within 20% of 30-day low?
2. **Entity loading?** — Any tracked entities increasing positions?
3. **Exchange balance declining?** — Use `token_flows` with `holder_segment: exchange` over 14 days. Count outflow days vs inflow days. If outflow days dominate (8+ of 14), the trend is accumulation.
4. **Volume declining?** — Recent volume below 20-day average?
5. **Smart money holding static?** — Are known funds holding positions without selling? Static holdings in a dip = silent conviction (not "no signal").

If a token hits 2+ of these, it's a candidate for full `analyze-token` treatment.

**⚠️ DO NOT eliminate a candidate based solely on a single-day exchange flow snapshot.** The SKY miss (March 2026) proved that one noisy inflow day can mask a structural outflow trend. Always check the 14-day balance trajectory before marking a token as "Distribution." See [exchange-flows.md](exchange-flows.md) for the full case study.

## Branching Logic

After screening:

| Hits | Action |
|------|--------|
| **0** | "No setups today. Market too quiet or too extended." |
| **1-3** | Run full `analyze-token` on each — generate complete reports |
| **4+** | Quick-score each with approximate Alpha Score. Rank top 3. Present table and ask "Ready to deep-dive any of these?" |

## Output: Candidate Table

```markdown
## Hunt Results — [Date]

| Token | Price vs 30d Low | Entity Signal | Exchange Flow | Volume | Quick Score |
|-------|-------------------|---------------|---------------|--------|-------------|
| TOKEN1 | Within 8% | Wintermute +45% | -2.1% supply | -25% | ~7/12 |
| TOKEN2 | Within 15% | Jump +20% | -0.8% supply | -18% | ~5/12 |
| TOKEN3 | Within 5% | CEO buy $100k | -3.5% supply | -30% | ~9/12 |

**Top candidate: TOKEN3** — CEO insider buy + heavy exchange outflows + deep volume dry-up
Ready to run full analysis on any of these?
```

## Supplementary: Smart Money Broad Scan

To find tokens where multiple funds are accumulating:

```
Tool: mcp__nansen__smart_traders_and_funds_token_balances
Parameters:
  chains: ["ethereum", "solana", "base", "arbitrum"]
  includeSmartMoneyLabels: ["Fund", "All Time Smart Trader"]
```

Filter for:
- Positions > $100k (ignore dust)
- 24h change > +5% (active accumulation)
- 2+ funds in the same token (convergence signal)

## Entity-First Screening (Secondary Pass)

After the flow-first screen from the token discovery screener, run a second pass that starts from entities rather than tokens:

```
Tool: mcp__nansen__smart_traders_and_funds_token_balances
Parameters:
  chains: ["ethereum", "solana", "base", "arbitrum"]
  includeSmartMoneyLabels: ["Fund", "All Time Smart Trader"]
```

**Filter for:**
- Positions > $100k (ignore dust)
- 24h change > +5% (active accumulation happening NOW)
- 2+ funds in the same token (convergence — multiple independent actors reaching the same conclusion)

**Why this matters:**
The flow-first screen catches tokens where AGGREGATE flows are moving. But the best accumulation happens quietly — the ZRO example proved this. Nansen's 12 "smart money" wallets held only ~$1.1M and were flat. The alpha was the CEO buying through an unlabeled wallet.

Entity-first screening asks: "Which tokens is Wintermute quietly increasing?" rather than "Which tokens have notable flows?" — a fundamentally different and often more productive question.

**Cross-reference with flow-first results:**
Any token that appears in BOTH the flow-first screen AND the entity-first screen gets automatic promotion to deep dive — convergence of two independent screening methodologies is a high-conviction signal.

---

## Frequency

`hunt-setups` is designed to run periodically:
- **Daily:** Quick screen during morning session
- **Weekly:** Deep scan with full entity tracking
- **On-demand:** When market conditions change (post-crash, sector rotation)
