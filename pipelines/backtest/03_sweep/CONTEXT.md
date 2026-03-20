# Stage: 03_sweep — Parameter Optimization

## Purpose

Sweep parameters on the top strategies to determine if they're robust (work across a range of settings) or fragile (only work at one exact parameter set).

## Inputs

| Source | File | Layer |
|--------|------|-------|
| Previous stage | `../02_scenarios/output/scenario_results.md` | 4 (working) |

## Process

### Step 1: Run Phase 3

```bash
python3 src/backtesting/scanner.py phase3 --symbol [SYMBOL] --timeframe [TF] --days [DAYS] --top 5
```

### Step 2: Assess Robustness

For each strategy:
- **Robust:** Performance degrades gracefully as parameters change. The strategy works across a *range*, not just one setting.
- **Fragile:** Performance collapses with small parameter changes. This is almost certainly overfit.

### Step 3: Filter

Keep only robust strategies. Flag and discard fragile ones regardless of peak performance.

## Outputs

| File | Contents |
|------|----------|
| `output/sweep_results.md` | Per-strategy parameter sensitivity: optimal range, degradation curve, robust/fragile classification |

## Review Gate

- Any strategies that are robust but have modest performance? (these are often the real ones)
- Any that look too good to be true? (likely fragile — check the sweep)
