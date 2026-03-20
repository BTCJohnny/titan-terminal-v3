---
name: scan
description: 4-phase strategy discovery — backtest scanner against historical data.
argument-hint: <SYMBOL> [--timeframe TF] [--days N]
allowed-tools:
  - Read
  - Bash
---

# /scan $ARGUMENTS

Run the backtest pipeline. Read `pipelines/backtest/CONTEXT.md` for the full stage map.

Parse $ARGUMENTS for symbol (required), timeframe (default 4h), and days (default 180).

Check data coverage first:
```bash
python3 src/backtesting/engine.py coverage --symbol [SYMBOL]
```

Then execute stages 01 through 04 in order. Each phase builds on the previous.
