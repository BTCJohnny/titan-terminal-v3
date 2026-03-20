---
name: paper-trade
description: Run the paper trading engine tick — processes setups, fills entries/exits, and shows portfolio status.
allowed-tools:
  - Read
  - Bash
---

# /paper-trade

Run the paper trading engine. This processes all pending and active trade setups against current OHLCV prices.

## What It Does

1. Refreshes OHLCV data for all active tokens
2. Checks PENDING setups — enters positions if entry price is hit
3. Checks OPEN positions — closes on stop/target hits (50% at T1, rest rides to T2)
4. Logs equity snapshot and reports all actions taken

## Execution

```bash
python3 src/trading/paper_engine.py tick
```

## After the Tick

Review the output and:
- If entries were filled: note which setups are now active
- If stops were hit: check if the thesis was wrong or just bad timing
- If targets were hit: good trade — note what worked
- If errors (no price data): run OHLCV download for those tokens

If the user asks for status without running a tick:
```bash
python3 src/trading/paper_engine.py status
```
