---
name: analyze-accumulation
description: Deep-dive a specific token for pre-breakout accumulation signals — entity loading, exchange outflows, volume dry-up, holder analysis. Nansen-heavy (6-10 credits).
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - mcp__nansen
  - mcp__coinstats
---

# /analyze-accumulation [TOKEN]

Deep-dive a specific token for pre-breakout accumulation signals.

## Execution

**This command delegates to the `pre-breakout-accumulator` skill's `analyze-token` workflow.**

1. Load the skill from `.claude/skills/pre-breakout-accumulator/SKILL.md`
2. Follow the `analyze-token [TOKEN]` workflow exactly as specified
3. Apply the additions below on top of the skill's workflow

---

## Additions Beyond the Skill's Base Workflow

### Derivatives Confirmation

Run Coinglass for the token and add qualitative flags (do NOT change the Alpha Score):

```bash
python3 src/fetchers/coinglass_fetcher.py --token [TOKEN] --derivatives --json
```

Add flags:
- If funding rate is negative while entities accumulate: "Derivatives aligned — shorts will fuel breakout"
- If OI is expanding while entities accumulate: "New positions building alongside entity loading"
- If L/S ratio shows extreme short crowding: "Contrarian setup — retail short, smart money long"

### Distributor Exhaustion Check

For any identified distributor (entity with declining balance), calculate:
- Remaining position size (current balance)
- Weekly sell rate (balance change over last 7d)
- Estimated weeks of sell pressure remaining: `remaining / weekly_sell_rate`

If estimated sell pressure > 4 weeks, flag: "Active distribution overhead — [Entity] has ~[X] weeks of sell pressure remaining at current rate"

If total distribution rate across all sellers exceeds total accumulation rate across all buyers, flag: "NET entity flow is negative — distribution exceeds accumulation"

### Mandatory 14-Day Exchange Balance Trend

The skill's exchange-flows.md has a MANDATORY note about checking 14-day balance trends. This command MUST run:

```
Tool: mcp__nansen__token_flows
Parameters:
  tokenAddress: "[contract-address]"
  chain: "[chain]"
  holder_segment: "exchange"
  dateRange: { from: "14D_AGO", to: "NOW" }
```

Count outflow days vs inflow days. Report: "14d balance trend: X outflow days / Y inflow days. Balance [declining/flat/rising]."

If the snapshot shows inflows but the balance trend shows outflows: flag prominently and score based on the TREND.

### Mandatory Entity Position Tables

The output MUST include structured weekly entity tables, not bullet points. Format per entity-tracking.md:

```markdown
### [Entity Name] ([Type])
| Period | Balance | Change | Action |
|--------|---------|--------|--------|
| Week 1 | $X | baseline | Holding |
| Week 2 | $X | +X% | Accumulating |
| Week 3 | $X | +X% | Heavy Loading |
```

If weekly data isn't available from Nansen, use the available granularity (7d/30d change) but note: "Weekly breakdown unavailable — using [X] granularity."

### Volume Measurement

Use **7-day average vs 20-day average** for the volume contraction score. Do NOT compare 7d vs 30d — a 30d average is too diluted by older data and understates the contraction signal.

### DB Logging

Log entity snapshots and exchange balance data after the analysis:
```bash
python3 src/storage/intelligence.py store-entities --token [TOKEN] --date [YYYY-MM-DD] --chain [CHAIN] --data '[...]'
python3 src/storage/intelligence.py store-exchange-balance --token [TOKEN] --chain [CHAIN] --data '[...]'
```

If the token was part of a hunt, also update the hunt result with the deep-dive findings.

### Auto-Save Report

Save to: `results/skill-runs/pre-breakout-accumulator/[TOKEN]_[YYYY-MM-DD]_analysis.md`

Create the directory if it doesn't exist:
```bash
mkdir -p results/skill-runs/pre-breakout-accumulator
```

---

## Output Format

Follow the output-format.md template EXACTLY. The report MUST include:

1. Executive Summary with Alpha Score up top
2. Price Positioning section with consolidation band width
3. Entity Tracking with weekly tables
4. Exchange Flows with 14d balance trend
5. Volume Analysis with 7d vs 20d comparison
6. Top 100 Holders with category breakdown
7. Alpha Score table
8. Pattern Match identification
9. Playbook (entry/stop/targets for 8+, re-check conditions for 5-7, pass for 0-4)
10. Self-Critique (including distributor exhaustion if applicable)
11. Derivatives flags (if available)

---

## Nansen Credit Tracking

At the end of the analysis, count and report total Nansen credits used. Format: `**Nansen credits used this analysis:** X` at the bottom of the report.
