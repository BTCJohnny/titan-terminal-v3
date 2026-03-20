---
name: find-setups
description: Primary daily workflow — scan the universe for 0-3 actionable trade setups.
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - mcp__nansen
  - mcp__coinstats
---

# /find-setups

Run the find-setups pipeline. Read `pipelines/find-setups/CONTEXT.md` for the full stage map, then execute stages 01 through 05 in order.

Each stage has its own CONTEXT.md with Inputs / Process / Outputs. Follow each contract exactly. Pause for human review at each gate.

"No setups today" is a valid and expected outcome.

After completion, archive all stage outputs to `runs/find-setups/[YYYY-MM-DD]/`.
