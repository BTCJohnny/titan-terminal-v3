---
name: performance
description: Paper trading performance analytics — win rate, profit factor, drawdown, strategy breakdown, equity curve.
allowed-tools:
  - Read
  - Bash
---

# /performance

Analyze paper trading performance across all closed positions.

## Execution

### Full Performance Summary
```bash
python3 src/trading/analytics.py summary
```

### Performance by Strategy
```bash
python3 src/trading/analytics.py by-strategy
```

### Performance by Direction (LONG vs SHORT)
```bash
python3 src/trading/analytics.py by-direction
```

### Recent Trades
```bash
python3 src/trading/analytics.py recent-trades
```

## Interpretation

After running analytics, provide:
1. **Edge assessment**: Does the system have a statistical edge? (profit factor > 1.5, win rate > 50%, positive expectancy)
2. **Strategy ranking**: Which setup types are most profitable? Which should be avoided?
3. **Risk assessment**: Is drawdown within acceptable limits? Is position sizing appropriate?
4. **Direction bias**: Are longs or shorts performing better? Does this match the market regime?
5. **Recommendations**: Based on the data, what should change? More of what's working, less of what isn't.

Compare results against the 3 Laws:
- Law 1 (Protect Capital): Max drawdown < 10%? Average loss < 2% of equity?
- Law 2 (Asymmetric Upside): Average R achieved > 2? Profit factor > 2?
- Law 3 (Reject Noise): Are losses concentrated in specific setups that should be filtered out?
