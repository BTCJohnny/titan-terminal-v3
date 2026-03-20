# Pipeline: backtest

> 4-phase strategy discovery and validation against historical data. Maps to `src/backtesting/scanner.py`.

## Entry Point

- `/scan [SYMBOL]` — full 4-phase scan
- Can also run individual phases

## Flow

```
01_signals → 02_scenarios → 03_sweep → 04_walkforward
```

Each phase builds on the previous. The scanner does the heavy computation in Python — the pipeline structures the interpretation and decision-making around it.

## Stage Map

| Stage | Scanner Phase | Purpose | Key Output |
|-------|-------------|---------|------------|
| 01_signals | Phase 1 | Test individual indicator signals | `signal_results.md` — which signals have edge |
| 02_scenarios | Phase 2 | Combine signals into strategies | `scenario_results.md` — which combos work |
| 03_sweep | Phase 3 | Optimize parameters on top strategies | `sweep_results.md` — robust vs fragile |
| 04_walkforward | Phase 4 | Out-of-sample validation | `walkforward_results.md` — real edge or overfit? |

## Prerequisites

Check data coverage before starting:
```bash
python3 src/backtesting/engine.py coverage --symbol [SYMBOL]
```

If coverage is insufficient, download first:
```bash
python3 src/data/ohlcv_client.py download [SYMBOL] --timeframe 4h --force
```
