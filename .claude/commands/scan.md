---
name: scan
description: Run the backtesting scanner to discover and validate trading strategies against historical data.
allowed-tools:
  - Read
  - Bash
---

# /scan

Run the automated strategy discovery pipeline against historical data.

## Quick Start

Full scan on BTC (all 4 phases):
```bash
python3 src/backtesting/scanner.py full --symbol BTC --timeframe 4h --days 180
```

## Available Commands

### Check data coverage first
```bash
python3 src/backtesting/engine.py coverage --symbol BTC
python3 src/backtesting/engine.py coverage --symbol ETH
```

### Phase 1: Individual signals
```bash
python3 src/backtesting/scanner.py phase1 --symbol BTC --timeframe 4h --days 180
```

### Phase 2: Scenario combinations
```bash
python3 src/backtesting/scanner.py phase2 --symbol BTC --timeframe 4h --days 180
```

### Phase 3: Parameter sweep (top N from Phase 2)
```bash
python3 src/backtesting/scanner.py phase3 --symbol BTC --timeframe 4h --days 180 --top 5
```

### Phase 4: Walk-forward validation
```bash
python3 src/backtesting/scanner.py phase4 --symbol BTC --timeframe 4h --days 180 --top 5
```

### Run a single scenario
```bash
python3 src/backtesting/engine.py run --symbol BTC --timeframe 4h --days 180 --strategy-file results/backtests/graduated_strategy.json
```

## After Running

Read the scanner output and provide:

1. **Leaderboard interpretation**: Which scenarios have real edge? Which are noise?
2. **Signal analysis**: Which individual signals contribute most? Which are redundant?
3. **Parameter sensitivity**: Are the best strategies robust (work across parameter ranges) or fragile (only work at one setting)?
4. **Regime context**: Compare results against current thesis in `reference/titan-thesis.md`. Do winning strategies match the current regime?
5. **Recommendations**: Which graduated strategies should be promoted to the paper engine? Suggest specific trade setups.

Read the JSON results files in `results/backtests/` for full detail.

## Promoting to Paper Engine

When a strategy graduates, create a trade setup for the paper engine:
```bash
python3 src/storage/intelligence.py log-setup --token BTC --direction SHORT --entry [PRICE] --stop [STOP] --target1 [T1] --target2 [T2] --pattern "[STRATEGY_NAME]" --ta-summary "[TA conditions at entry]"
```

The paper engine's 4h cron will then monitor and execute.
