# Stage: 02_scenarios — Strategy Combination Scan

## Purpose

Combine individual signals into multi-condition strategies and test which combinations produce better results than individual signals alone.

## Inputs

| Source | File | Layer |
|--------|------|-------|
| Previous stage | `../01_signals/output/signal_results.md` | 4 (working) |

## Process

### Step 1: Run Phase 2

```bash
python3 src/backtesting/scanner.py phase2 --symbol [SYMBOL] --timeframe [TF] --days [DAYS]
```

### Step 2: Interpret Results

- Which combinations have real synergy (better than individual components)?
- Which combinations are redundant (no improvement over single signal)?
- Are the best strategies long-biased, short-biased, or balanced?
- Do any match known setup types from the thesis?

### Step 3: Select Top Candidates

Identify the top 5 strategies by profit factor × sample size (balances edge with reliability).

## Outputs

| File | Contents |
|------|----------|
| `output/scenario_results.md` | Top strategies: components, direction, PF, WR, # trades, synergy assessment |

## Review Gate

- Do the top strategies make intuitive sense? (if a combo doesn't have a logical thesis, be skeptical)
- Enough trades in each to trust the results? (>30 minimum)
