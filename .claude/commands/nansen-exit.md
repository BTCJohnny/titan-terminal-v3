---
name: nansen-exit
description: Check if smart money is exiting a token you hold. 4 Nansen credits.
argument-hint: <TOKEN> [CHAIN]
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - mcp__nansen
---

# /nansen-exit $ARGUMENTS

Run the exit-check pipeline. Read `pipelines/exit-check/CONTEXT.md` for the full stage map, then execute stages 01 and 02.

Default chain: ethereum. Parse $ARGUMENTS for optional chain override.

Save to `results/skill-runs/nansen-exit-signal/[TOKEN]_[YYYY-MM-DD].md`.
