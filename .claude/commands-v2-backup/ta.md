---
name: ta
description: Quick multi-timeframe technical analysis using the 7-Question framework. TA only — no on-chain, no accumulation scoring, no trade card.
argument-hint: <TOKEN>
allowed-tools:
  - Read
  - Bash
---

# /ta $ARGUMENTS

Run a focused 7-Question technical analysis for the specified token across Weekly, Daily, and 4H timeframes.

This is the **TA-only** command. For a full Trade Card with on-chain flows, accumulation scoring, and verdict synthesis, use `/analyze` instead.

## Execution

Delegate the entire analysis to the **ta-analyst** subagent with this task:

> Run a complete 7-Question technical analysis for $ARGUMENTS across Weekly, Daily, and 4H timeframes. Download data, run all 8 indicators (RSI, MACD, ADX+DI, BB, OBV, S/R, SMA 50/200, ATR), interpret results, resolve timeframe conflicts, then drill down to 1H (S/R, ATR, RSI, BB) to refine precise entry, stop, and target levels. Return the structured verdict with 1H-refined key levels, R:R at each target, confidence score, and the "So What?" section. **Explicitly evaluate both long and short setups** — if the data supports a short opportunity (confirmed downtrend, distribution, breakdown structure, crowded longs), flag it directly with 1H-refined entry, stop, and R:R. Do not bias toward longs by default.

Display the ta-analyst's output directly. Do not add additional synthesis or commentary — the subagent's verdict is the final output.

## When to Use

- Quick TA check before deciding whether to run a full `/analyze`
- Monitoring tokens already on the watchlist for technical changes
- Comparing TA across multiple tokens quickly
- Any time you need price structure without on-chain context
