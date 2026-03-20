---
name: ta
description: Quick multi-timeframe technical analysis — TA only, no on-chain.
argument-hint: <TOKEN>
allowed-tools:
  - Read
  - Bash
---

# /ta $ARGUMENTS

Run only stage 02_technical of the token-analysis pipeline. Read `pipelines/token-analysis/02_technical/CONTEXT.md` and follow its standalone mode instructions.

Delegates entirely to the ta-analyst subagent. Display the subagent's output directly.
