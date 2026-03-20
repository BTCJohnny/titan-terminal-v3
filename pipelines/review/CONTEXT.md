# Pipeline: review

> Learning loop. Traces closed trade outcomes back to specific pipeline stages, diagnoses failures, and proposes concrete `_config/` improvements. Run weekly or after N trades close.

## Flow

```
01_outcomes → 02_diagnosis → 03_propose → Human reviews → applies or rejects → Git commit
```

## Design Principle

This pipeline improves the *factory*, not the *product*. The goal is to find recurring patterns in output edits and trade failures, then fix them at the source (`_config/` files, stage contracts) so every future run benefits.

## Stage Map

| Stage | Purpose | Key Output |
|-------|---------|------------|
| 01_outcomes | Pull closed trades, match to run archives | `outcomes.md` — what the system said vs what happened |
| 02_diagnosis | Trace failures to specific stages | `diagnosis.md` — root cause per losing trade |
| 03_propose | Propose `_config/` improvements | `proposals.md` — concrete diffs with rationale |

## What Gets Improved Over Time

- `_config/interpreters/` — tighter thresholds after false positives
- `_config/red-flags.md` — grows as new failure patterns emerge
- `_config/signal-hierarchy.md` — weight adjustments based on outcome data
- `_config/thesis.md` — regime signals validated or corrected
- Stage CONTEXT.md files — process steps refined based on recurring errors
