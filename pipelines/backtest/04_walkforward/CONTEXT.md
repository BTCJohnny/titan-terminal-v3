# Stage: 04_walkforward — Out-of-Sample Validation

## Purpose

Test the surviving robust strategies on out-of-sample data to confirm they have genuine edge, not just in-sample fit. This is the final graduation test.

## Inputs

| Source | File | Layer |
|--------|------|-------|
| Previous stage | `../03_sweep/output/sweep_results.md` | 4 (working) |
| Reference | `_config/thesis.md` | 3 (factory) |

## Process

### Step 1: Run Phase 4

```bash
python3 src/backtesting/scanner.py phase4 --symbol [SYMBOL] --timeframe [TF] --days [DAYS] --top 5
```

### Step 2: Evaluate Walk-Forward Results

For each strategy:
- **Graduated:** Out-of-sample performance is ≥60% of in-sample performance. Real edge.
- **Degraded:** Out-of-sample performance is 30-60% of in-sample. Marginal — monitor.
- **Failed:** Out-of-sample performance is <30% of in-sample. Overfit. Discard.

### Step 3: Regime Check

Compare graduated strategies against `_config/thesis.md`:
- Do winning strategies match the current regime?
- Would they have worked in the opposite regime? (regime-dependent vs regime-agnostic)

### Step 4: Graduation Decision

For each graduated strategy, decide:
- **Promote to paper engine:** Create a live signal checker entry
- **Promote to watchlist:** Monitor but don't auto-trade
- **Hold:** Promising but needs more data

### Step 5: Promote to Paper Engine (if graduated)

```bash
python3 src/backtesting/signal_checker.py check  # Verify current signal status
```

If signal is currently firing, create setup:
```bash
python3 src/storage/intelligence.py log-setup --token [SYMBOL] --direction [DIR] --entry [PRICE] --stop [STOP] --target1 [T1] --target2 [T2] --pattern "[STRATEGY_NAME]" --ta-summary "[CONDITIONS]"
```

## Outputs

| File | Contents |
|------|----------|
| `output/walkforward_results.md` | Per-strategy: in-sample vs out-of-sample comparison, graduation status, regime context, promotion recommendation |

## Post-Output Actions

1. Archive the full backtest run to `runs/backtest/[SYMBOL]_[YYYY-MM-DD]/`
2. Save graduated strategies to `results/backtests/`
3. If any strategy is currently firing, flag it as a Priority Action

## Review Gate

Final decision on each graduated strategy:
- Promote to paper engine?
- What position size? (start conservative — 50% of normal until 10+ live trades confirm edge)
- Set a review date (re-evaluate after 30 days or 10 trades, whichever comes first)
