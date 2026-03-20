# Technical Analysis (v2 — Multi-Timeframe)

## Purpose
Get a complete multi-timeframe TA assessment. In v2, this is delegated entirely to the **ta-analyst subagent** — you do NOT run the Python tools directly from the Trade Card workflow.

## How It Works

Delegate to the ta-analyst subagent with this task:

> Run a complete 7-Question technical analysis for [TOKEN] across Weekly, Daily, and 4H timeframes. Download data, run all 8 indicators (RSI, MACD, ADX+DI, BB, OBV, S/R, SMA 50/200, ATR), interpret results, resolve timeframe conflicts, and return the structured verdict with key levels, confidence score, and the "So What?" section.

The ta-analyst returns:
- **Verdict:** Direction + confidence + recommended action
- **Timeframe breakdown:** Weekly, Daily, 4H each with direction and key reason
- **Alignment:** All aligned / Mostly aligned / Conflicting
- **Key levels:** Support, resistance, invalidation, ATR stop distance
- **Regime:** SMA 50/200 structure
- **Momentum & volume:** MACD, RSI, OBV readings
- **Volatility:** BB state, ATR
- **"So What?":** Specific entry/stop/target with R:R

## Condensing for the Trade Card

The full ta-analyst output is detailed. For the Trade Card's Price Action section, condense it into this format:
```
## Price Action: [2-3 Word Summary]

**Regime:** [Full bull / Full bear / Transitional] — Price [above/below] SMA 200, [Golden Cross / Death Cross / neither]

[Flowing paragraph connecting the most important findings across timeframes.
Lead with the most actionable signal. Reference which timeframe it comes from.
Tell the STORY of what the market is doing. End with the "So What?" in plain English.]

**Timeframe Alignment:** [All aligned / Mostly aligned / Conflicting]
- Weekly: [direction] — [1-line key reason]
- Daily: [direction] — [1-line key reason]
- 4H: [direction] — [1-line key reason]

**Key Levels:** Support $X ([strength]) | Resistance $X ([strength]) | Invalidation $X
**TA Confidence:** [X]%
```

## Summary Examples

Good 2-3 word summaries:
- "Weak Downtrend, No Floor"
- "Testing Key Support"
- "Breakout Above Resistance"
- "Directionless Chop"
- "Oversold Bounce Setup"
- "Bull Trend, Pulling Back"
- "Bearish, All Timeframes Aligned"

## Key Difference from v1

v1 ran single-timeframe 4H analysis inline. v2 delegates to the ta-analyst subagent which runs 3 timeframes with the 7-Question framework. The Trade Card doesn't re-run TA — it receives and condenses the subagent's output. For full TA detail, use `/ta [TOKEN]`.
