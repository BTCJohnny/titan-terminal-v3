# Stage: 02_technical — Multi-Timeframe Technical Analysis

## Purpose

Run the 7-Question TA framework across Weekly, Daily, 4H, and 1H timeframes. Produces a directional verdict with confidence score and 1H-refined entry/stop/target levels.

## Inputs

| Source | File | Layer |
|--------|------|-------|
| Previous stage | `../01_resolve/output/identity.md` | 4 (working) |

## Process

Delegate the entire analysis to the **ta-analyst** subagent (`.claude/agents/ta-analyst.md`). Send this task:

> Run a complete 7-Question technical analysis for [TOKEN] across Weekly, Daily, and 4H timeframes. Download data, run all 8 indicators (RSI, MACD, ADX+DI, BB, OBV, S/R, SMA 50/200, ATR), interpret results, resolve timeframe conflicts, then drill down to 1H (S/R, ATR, RSI, BB) to refine precise entry, stop, and target levels. Return the structured verdict with 1H-refined key levels, R:R at each target, confidence score, and the "So What?" section. **Explicitly evaluate both long and short setups** — if the data supports a short opportunity (confirmed downtrend, distribution, breakdown structure, crowded longs), flag it directly with 1H-refined entry, stop, and R:R. Do not bias toward longs by default.

Do NOT re-run or second-guess the ta-analyst's output. Use it directly.

### Standalone mode (`/ta [TOKEN]`)

When invoked via `/ta`, run only this stage (skip 01_resolve — just download data and delegate). Display the ta-analyst's output directly as the final response.

## Scripts Used (by the ta-analyst subagent)

- `python3 src/analysis/indicators.py download [TOKEN] --timeframe [TF]`
- `python3 src/analysis/indicators.py analyze [TOKEN] --timeframe [TF] --indicators rsi,macd,bb,sma,atr,adx,obv,sr`

## Outputs

| File | Contents |
|------|----------|
| `output/ta_verdict.md` | Direction, confidence %, timeframe breakdown, key levels (entry/stop/T1/T2/T3), R:R at each target, regime (SMA structure), momentum & volume summary, "So What?" section |

## Review Gate

- Does the directional call match your read of the chart?
- Are the key levels reasonable? (entry near S/R, stop beyond structural invalidation)
- Is the R:R at T3 ≥ 3:1?
