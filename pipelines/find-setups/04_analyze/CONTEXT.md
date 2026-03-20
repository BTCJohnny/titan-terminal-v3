# Stage: 04_analyze — Deep Dive Per Candidate

## Purpose

Run the full token-analysis pipeline on each candidate from 03_filter. This stage delegates — it does not contain its own analysis logic.

## Inputs

| Source | File | Layer |
|--------|------|-------|
| Previous stage | `../03_filter/output/candidates.md` | 4 (working) |

## Process

For each candidate token in `candidates.md`:

1. Run the `pipelines/token-analysis/` pipeline end-to-end
2. Store results in `output/[TOKEN]/` (mirroring the token-analysis output structure)

If candidates.md says "No setups today," skip this stage entirely.

### Delegation

Read `pipelines/token-analysis/CONTEXT.md` for the full pipeline. Execute all 5 stages for each candidate:
- 01_resolve → 02_technical → 03_onchain → 04_derivatives → 05_verdict

### Nansen Budget Awareness

Each candidate costs ~15-20 Nansen credits for full analysis. With 3 candidates, that's 45-60 credits. Check the session budget before starting the third candidate.

## Outputs

| File | Contents |
|------|----------|
| `output/[TOKEN]/` | Full token-analysis output for each candidate (identity.md, ta_verdict.md, flows.md, accumulation.md, derivatives.md, perps.md, verdict.md, trade_card.md) |

## Review Gate

Before proceeding to 05_setup:
- Review each candidate's verdict — do you agree with the direction call?
- Any candidates you want to drop before generating setup cards?
- Any verdict that contradicts an active thesis? (the verdict should flag this)
