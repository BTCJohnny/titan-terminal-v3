# Stage: 05_setup — Generate Actionable Trade Cards

## Purpose

Convert analysis verdicts into concrete, executable trade setups with entry, stop, targets, position size, and R:R. This is the final output the trader acts on.

## Inputs

| Source | File | Layer |
|--------|------|-------|
| Previous stage | `../04_analyze/output/[TOKEN]/verdict.md` | 4 (working) |
| Previous stage | `../04_analyze/output/[TOKEN]/trade_card.md` | 4 (working) |
| Previous stage | `../01_regime/output/regime.md` | 4 (working) |
| Reference | `_config/position-sizing.md` | 3 (factory) |
| Reference | `_config/thesis.md` | 3 (factory) |
| Reference | `_config/signal-hierarchy.md` | 3 (factory) |
| Reference | `_config/examples/trade-card-example.md` | 3 (factory) |

## Process

### For each candidate with a Bullish or Bearish verdict:

1. **Extract key levels** from the trade card — entry, stop, T1, T2, T3
2. **Calculate position size** using `_config/position-sizing.md` rules:
   - Risk per trade: 2% of portfolio
   - Category limits apply (blue chip 30%, large cap 15%, etc.)
   - Dollar risk = portfolio × 2%
   - Position size = dollar risk / |entry - stop|
3. **Calculate R:R** at each target — flag if T3 < 3:1
4. **Regime alignment check** — does this setup match the valid types from regime.md?
5. **Thesis alignment** — does this confirm or contradict an active thesis?

### For candidates with Neutral verdict:

State: "[TOKEN] analyzed but no actionable setup. Reason: [from verdict]"

### If no candidates had actionable verdicts:

State: "No setups today. [N] tokens scanned, [M] passed filter, [K] analyzed — none produced actionable R:R."

### Format each setup card:

```
## [EMOJI] [TOKEN] — [DIRECTION] Setup

**Thesis:** [one-sentence from verdict]
**Regime fit:** [which setup type this matches]

**Entry:** $X | **Stop:** $X | **Risk:** $X ([stop distance])
**T1:** $X (R:R X.X:1) | **T2:** $X (R:R X.X:1) | **T3:** $X (R:R X.X:1)
**Position size:** $X ([category] limit) | **Risk:** $X (X% of portfolio)

**Key signals:**
- [strongest signal]
- [second signal]
- [risk/watch condition]

**Invalidation:** [what kills this trade]
```

## Scripts Used

None — this is pure synthesis from previous stage outputs and _config rules.

## Outputs

| File | Contents |
|------|----------|
| `output/setups.md` | All setup cards (or "nothing today" with context), plus session summary |

## Post-Output Actions

1. Archive the full run: copy all stage outputs to `runs/find-setups/[YYYY-MM-DD]/`
2. Auto-journal: append setups.md to `trading/journal/YYYY_QN.md`
3. If any setup is actionable, suggest: "Create paper trade? Run `/portfolio` to enter."

## Review Gate

Final human decision:
- Enter the trade, modify levels, or pass?
- Any position sizing adjustments?
- Flag if this is the first trade in new direction (regime shift)
