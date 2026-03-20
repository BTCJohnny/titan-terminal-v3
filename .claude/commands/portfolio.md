---
name: portfolio
description: Paper trading — status, tick, positions, performance.
argument-hint: [status|tick|positions|performance]
allowed-tools:
  - Read
  - Bash
  - mcp__coinstats
---

# /portfolio $ARGUMENTS

Operational command — no pipeline. Run the appropriate paper trading CLI command.

| Argument | Command |
|----------|---------|
| (none) or status | `python3 src/trading/paper_engine.py status` |
| tick | `python3 src/trading/paper_engine.py tick` |
| positions | `python3 src/trading/paper_engine.py positions` |
| closed | `python3 src/trading/paper_engine.py positions --closed` |
| performance | `python3 src/trading/analytics.py summary` |
| by-strategy | `python3 src/trading/analytics.py by-strategy` |
| by-direction | `python3 src/trading/analytics.py by-direction` |

For portfolio sync, also run:
```
mcp__coinstats__get-portfolio-coins: shareToken "NL3S076anq11Ibz", limit 50
```
Pass response to: `python3 src/formatters/portfolio_sync.py '<JSON>'`
