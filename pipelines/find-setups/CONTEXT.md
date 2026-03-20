# Pipeline: find-setups

> Primary daily workflow. Scans the universe top-down to find 0-3 actionable trade setups.

## Flow

```
01_regime → 02_scan → 03_filter → 04_analyze → 05_setup → runs/
```

Each stage writes to its own `output/` folder. Human reviews at each gate.

## Critical Design Decision

**"Nothing today" is a first-class outcome.** The system should NOT always find something. If nothing passes the filter, say so with market context and what would need to change. Quality over quantity.

## Stage Map

| Stage | Purpose | Key Inputs | Key Output |
|-------|---------|-----------|------------|
| 01_regime | Market structure check | BTC data, derivatives, ETF, F&G, CEX flows | `regime.md` — risk-on/off/chop + valid setup types |
| 02_scan | 4 parallel sub-scans | regime.md, `_config/universe.md` | ta_hits.md, deriv_hits.md, onchain_hits.md, squeeze_hits.md |
| 03_filter | Apply red flags + rank | All 02 outputs, `_config/red-flags.md`, regime.md | `candidates.md` — 0-3 ranked candidates |
| 04_analyze | Deep dive per candidate | candidates.md | Per-token analysis (runs token-analysis pipeline) |
| 05_setup | Generate trade cards | All 04 outputs, `_config/position-sizing.md` | `setups.md` — actionable entries or "nothing today" |

## After Completion

Archive the full run to `runs/find-setups/[YYYY]/` — copy all stage outputs. This archive feeds the `/review` learning loop.
