---
name: liquidity
description: Quick derivatives check — liquidations, max pain, funding, L/S ratios.
argument-hint: <TOKEN>
allowed-tools:
  - Read
  - Bash
  - mcp__coinstats
---

# /liquidity $ARGUMENTS

Run only stage 04_derivatives of the token-analysis pipeline. Read `pipelines/token-analysis/04_derivatives/CONTEXT.md` and follow its standalone mode instructions.

Uses Coinglass data only (no Nansen credits). Renders the liquidity report format directly.
