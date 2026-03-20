---
name: analyze
description: Full Titan Trade Card — deep dive on any token with TA, on-chain, derivatives, and verdict.
argument-hint: <TOKEN>
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - mcp__nansen
  - mcp__coinstats
---

# /analyze $ARGUMENTS

Run the token-analysis pipeline for $ARGUMENTS. Read `pipelines/token-analysis/CONTEXT.md` for the full stage map, then execute stages 01 through 05 in order.

Stages 02, 03, and 04 are independent — run them in parallel after 01 completes.

Save the trade card to `results/trade-cards/[TOKEN]_[YYYY-MM-DD].md` and auto-journal to `trading/journal/`.
