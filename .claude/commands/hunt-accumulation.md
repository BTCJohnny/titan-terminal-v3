---
name: hunt-accumulation
description: Top-down market scan for pre-breakout accumulation patterns — entity loading, exchange outflows, volume dry-ups near range lows. Nansen-heavy (15-20 credits).
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - mcp__nansen
  - mcp__coinstats
---

# /hunt-accumulation

Run a top-down market scan for pre-breakout accumulation patterns.

## Execution

**This command delegates to the `pre-breakout-accumulator` skill's `hunt-setups` workflow.**

1. Load the skill from `.claude/skills/pre-breakout-accumulator/SKILL.md`
2. Follow the `hunt-setups` workflow exactly as specified
3. Apply the additions below on top of the skill's workflow

---

## Additions Beyond the Skill's Base Workflow

### Entity-First Screening (Secondary Pass)

After the token discovery screener (flow-first), run a second pass that's entity-first:

```
Tool: mcp__nansen__smart_traders_and_funds_token_balances
Parameters:
  chains: ["ethereum", "solana", "base", "arbitrum"]
  includeSmartMoneyLabels: ["Fund", "All Time Smart Trader"]
```

Filter for:
- Positions > $100k (ignore dust)
- 24h change > +5% (active accumulation happening NOW)
- 2+ funds in the same token (convergence — multiple independent actors reaching the same conclusion)

Cross-reference against the flow-first candidates. Any token that appears in BOTH screens gets automatic promotion to deep dive.

### Derivatives Confirmation

For each candidate scoring 5+ from the Alpha Score, run:
```bash
python3 src/fetchers/coinglass_fetcher.py --token [CANDIDATE] --derivatives --json
```

Add as a **qualitative flag** (not a score change):
- If funding rate is negative while entities accumulate: "Derivatives aligned — shorts will fuel the breakout"
- If OI is expanding while entities accumulate: "New positions building alongside entity loading"
- If L/S ratio shows extreme short crowding: "Contrarian setup — retail short, smart money long"

Include these flags in the hunt report and the self-critique section. They do NOT change the Alpha Score — they add conviction context.

### Distributor Exhaustion Check

For any identified distributor (entity with declining balance), calculate:
- Remaining position size (current balance)
- Weekly sell rate (balance change over last 7d)
- Estimated weeks of sell pressure remaining: `remaining / weekly_sell_rate`

If estimated sell pressure > 4 weeks, flag: "Active distribution overhead — [Entity] has ~[X] weeks of sell pressure remaining at current rate"

Include this in the self-critique section. It doesn't change the score but it's critical context for whether accumulation is being absorbed or just matched by distribution.

### Mandatory DB Logging

After the hunt completes, log ALL scored candidates (not just high scorers) to the DB:

```bash
python3 src/storage/intelligence.py store-hunt \
    --date [YYYY-MM-DD] \
    --data '[{"token": "ENA", "chain": "ethereum", "token_address": "0x...", "price_at_hunt": 0.1047, "alpha_score": 6, "entity_convergence_score": 2, "exchange_flow_score": 1, "volume_dry_up_score": 1, "perps_score": 0, "exchange_net_flow_usd": -21400000, "num_entities_buying": 3, "num_entities_selling": 2, "top_entity": "OKX Ventures", "top_entity_change": "+71%", "exbal_outflow_days": null, "exbal_balance_change_pct": null, "verdict": "MODERATE", "verdict_reason": "Watchlist — entity loading starting but conflicting exchange flow data"}]'
```

Also log entity snapshots for each candidate that gets a deep dive:
```bash
python3 src/storage/intelligence.py store-entities \
    --token [TOKEN] --date [YYYY-MM-DD] --chain [CHAIN] \
    --data '[{"entity_name": "OKX Ventures", "entity_address": "0x...", "entity_type": "VC", "balance": 10800000, "balance_usd": 1130000, "change_7d": 414900, "change_30d": 4500000}]'
```

### Auto-Save Report

Save the hunt report to: `results/skill-runs/pre-breakout-accumulator/hunt_[YYYY-MM-DD].md`

Create the directory if it doesn't exist:
```bash
mkdir -p results/skill-runs/pre-breakout-accumulator
```

### Nansen Credit Tracking

At the end of the hunt, count and report total Nansen credits used. Format: `**Nansen credits used this hunt:** X` at the bottom of the report.

---

## Key Thresholds

| Score | Rating | Action |
|-------|--------|--------|
| 8-12 | Strong/Alpha | Flag for immediate `/analyze [TOKEN]` |
| 5-7 | Moderate | Add to watchlist, re-check in 5-7 days |
| 0-4 | Weak | Pass — insufficient signals |

---

## Error Handling

- If Nansen token discovery is unavailable, fall back to entity-first screening only
- If fewer than 3 candidates qualify, analyze whatever qualifies
- If Coinglass is unavailable, skip derivatives confirmation and note it
- Note which tokens had data issues so the user knows the scan was partial

---

## Formatting Rules

- Verdict first — lead with the best candidate and its score
- Quantify everything — dollar amounts, ratios, percentages
- Use the skill's persona: contrarian, data-driven, no vibes
- Bold all Alpha Scores
- Include weekly entity position tables for deep-dive candidates (NOT bullet points — structured tables with week-by-week data as specified in the skill's entity-tracking.md)
