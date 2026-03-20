# Stage: 01_signals — Individual Signal Testing

## Purpose

Test each indicator signal in isolation to determine which ones have genuine edge on this symbol and timeframe.

## Inputs

| Source | File | Layer |
|--------|------|-------|
| User input | Symbol, timeframe (default 4h), lookback days (default 180) | — |

## Process

### Step 1: Run Phase 1

```bash
python3 src/backtesting/scanner.py phase1 --symbol [SYMBOL] --timeframe [TF] --days [DAYS]
```

### Step 2: Interpret Results

Read the output and assess:
- Which individual signals show positive expectancy?
- Which signals are noise (win rate near 50%, low profit factor)?
- Which signals have enough sample size to be meaningful (>20 trades)?
- Are there clear long vs short asymmetries?

### Step 3: Compare to Current Thesis

Check against `_config/thesis.md`:
- Do the winning signals align with the current regime?
- Are there signals that work against the regime? (contrarian opportunity or overfit risk?)

## Outputs

| File | Contents |
|------|----------|
| `output/signal_results.md` | Ranked signal table: signal name, direction, win rate, profit factor, # trades, edge assessment |

## Review Gate

- Any signals with suspiciously high performance? (likely overfit if <10 trades)
- Any expected signals that failed? (worth investigating why)
- Ready to combine into scenarios?
