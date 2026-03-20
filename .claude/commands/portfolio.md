---
name: portfolio
description: Show paper trading portfolio — current balance, open positions, allocation, and equity history.
allowed-tools:
  - Read
  - Bash
---

# /portfolio

Show the current state of the paper trading portfolio.

## Execution

### Current Status
```bash
python3 src/trading/paper_engine.py status
```

### Open Positions
```bash
python3 src/trading/paper_engine.py positions
```

### Closed Positions (recent)
```bash
python3 src/trading/paper_engine.py positions --closed
```

### Equity History (last 7 days)
```bash
python3 src/trading/paper_engine.py history --days 7
```

## Interpretation

After running the commands, synthesize:
- **Portfolio health**: Is equity growing? What's the drawdown?
- **Position risk**: Are open positions concentrated in one sector?
- **Cash reserve**: How much dry powder is available for new setups?
- **Thesis alignment**: Do open positions match the current regime from `reference/titan-thesis.md`?
