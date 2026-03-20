# Output Format

## Purpose
Defines the report structure for both `analyze-token` and `hunt-setups` commands.

---

## analyze-token Report

```markdown
# [TOKEN] — Pre-Breakout Accumulation Report

## Executive Summary
**Alpha Score: [X]/12 — [Rating]**
[1-2 sentence verdict: Is this an accumulation setup or not? If yes, what's the expected move?]

---

## Price Positioning
**30d Range:** $[low] — $[high] (Current: $[price])
**Distance from Low:** [X]% — [Score]/2
**Consolidation Band:** ±[X]% over [period]
**Divergence:** [Yes/No] — [entity accumulating while price flat/down]

---

## Entity Tracking

### [Entity 1 Name] ([Type])
| Period | Balance | Change | Action |
|--------|---------|--------|--------|
| Week 1 | $X | baseline | Holding |
| Week 2 | $X | +X% | Accumulating |
| ...    | ...| ...    | ...     |

**Signal Strength:** [Weak/Strong/Alpha] — [X]/3

### [Entity 2 Name] ([Type])
[Same table format]

### Insider Activity
[Any founder/CEO/team wallet moves — flag prominently if present]

---

## Exchange Flows
**Net Flow (4 weeks):** -$[X]M / -[X] tokens
**% of Supply:** [X]%
**Pattern:** [Steady outflows / Single event / Mixed]
**Score:** [X]/2

---

## Volume Analysis
**Current vs 20d Avg:** [X]% [above/below]
**Trend:** [Declining / Stable / Rising]
**Volume at Recent Lows:** [X]% of average
**Score:** [X]/2

---

## Top 100 Holders
**Net Supply Change:** [+/-X]% over [period]
**Key Accumulators:** [names if available]
**Key Distributors:** [names if available]
**Exchange Wallet Trend:** [Growing / Shrinking]
**Score:** [X]/2

---

## Alpha Score: [X]/12 — [Rating]
*For native tokens (SOL, ETH, BTC): [X]/10 — [Rating] (exchange flows N/A)*

| Signal | Score | Evidence |
|--------|-------|----------|
| Entity Balance Increase | [X]/3 | [detail] |
| Price at Range Low | [X]/2 | [detail] |
| Volume Contraction | [X]/2 | [detail] |
| Exchange Outflows | [X]/2 | [detail] |
| Top 100 Holder Increase | [X]/2 | [detail] |

---

## Pattern Match
**Primary Pattern:** [Classic / SM Divergence / Volume Dry-Up]
**Phase:** [Where in the pattern are we?]
**Expected Move:** [X-Y]% based on consolidation range and pattern type

---

## Playbook

**If Alpha Score 8+:**
- Entry zone: $[X] - $[Y] (current accumulation range)
- Stop: $[X] (below consolidation low, 1.5-2x ATR)
- Target 1: $[X] (+[X]%, [X]R)
- Target 2: $[X] (+[X]%, [X]R)
- Position sizing: Per Titan limits ([category] = max [X]%)

**If Alpha Score 5-7:**
- Add to watchlist
- Re-check in [X] days
- Trigger conditions: [what would upgrade to 8+?]

**If Alpha Score 0-4:**
- Pass — insufficient signals
- [Brief note on what's missing]

---

## Self-Critique
- **What could invalidate this setup:** [specific risks]
- **Data limitations:** [what we couldn't verify]
- **Next check date:** [when to re-evaluate]

---
*Generated: [date] | Skill: pre-breakout-accumulator v2.1*
```

---

## hunt-setups Report

```markdown
# Pre-Breakout Hunt — [Date]

## Screening Parameters
- Universe: Top [X] tokens by [criteria]
- Filters: MC $50M-$5B, 30d change <+10%, declining volume
- Entities tracked: Wintermute, Jump Trading, Paradigm, a16z, Polychain

## Results: [X] Candidates Found

| Token | Price vs 30d Low | Entity Signal | Exchange Flow | Volume | Quick Score |
|-------|-------------------|---------------|---------------|--------|-------------|
| [TOKEN1] | Within [X]% | [entity] +[X]% | -[X]% supply | -[X]% | ~[X]/12 |
| [TOKEN2] | Within [X]% | [entity] +[X]% | -[X]% supply | -[X]% | ~[X]/12 |
| [TOKEN3] | Within [X]% | [entity] +[X]% | -[X]% supply | -[X]% | ~[X]/12 |

## Top Candidate: [TOKEN]
[1-2 sentence summary of why this is the strongest setup]

## Recommendation
[Action: deep dive specific tokens, or "no setups today"]

---
*Generated: [date] | Skill: pre-breakout-accumulator v2.1*
```

---

## Formatting Rules

### DO
- Lead with the Alpha Score and verdict in the executive summary
- Use tables for entity tracking data (week-by-week changes)
- Include specific dollar amounts and percentages
- Name the pattern being matched
- Provide a concrete playbook (entry, stop, targets) for strong setups
- Include self-critique section — what could be wrong?

### DON'T
- Pad with commentary when data is thin — say "insufficient data"
- Override the Alpha Score with narrative — the score IS the verdict
- Present weak setups (0-4) as opportunities — be clear: "Pass"
- Skip the self-critique — every setup has risks, name them

## Auto-Save

### Report Files
```
results/skill-runs/pre-breakout-accumulator/[TOKEN]_[YYYY-MM-DD]_[event].md
```

Events: `analysis`, `breakout`, `invalidated`

Examples:
- `ZRO_2026-01-12_breakout.md`
- `SOL_2025-12-01_2026-01-15.md`
- `AVAX_2026-03-02_analysis.md`

### Database Logging
For setups scoring 8+, log to `trade_setups` table:
```bash
python3 src/storage/intelligence.py log-setup \
    --token [TOKEN] --direction LONG \
    --entry [price] --stop [price] --target1 [price] --target2 [price] \
    --rr [ratio] --skill pre-breakout-accumulator
```

### Journal
# Journal: Auto-append to my-trading/journal/YYYY_QX.md (manual for now — journal formatter not yet ported)
