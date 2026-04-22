# Smart Money Moves Interpreter

## Who is "Smart Money"?

Nansen labels wallets based on historical profitability:

| Label | Definition |
|-------|------------|
| All Time Smart Trader | Consistently profitable across all market conditions |
| 180D Smart Trader | Profitable over the last 180 days |
| 90D Smart Trader | Profitable over the last 90 days |
| 30D Smart Trader | Profitable over the last 30 days |
| Fund | Known institutional fund wallets |
| Smart HL Perps Trader | Profitable Hyperliquid traders |

## Why It Matters

Smart money has a track record of buying before pumps and selling before dumps. Their movements are leading indicators.

## How to Read

| Smart Money Action | Interpretation |
|--------------------|----------------|
| Increasing positions | Bullish — accumulating before expected move |
| Holding steady | Neutral — conviction but no urgency |
| Reducing positions | Bearish — taking profits or de-risking |
| New positions | Very bullish — fresh conviction |
| Exiting entirely | Very bearish — lost confidence |

## Signal Strength

| Number of Actors | Strength |
|------------------|----------|
| 5+ funds/traders | High conviction signal |
| 2-4 actors | Moderate signal |
| 1 actor | Weak — could be noise |

## Time Context

| Timeframe | Interpretation |
|-----------|----------------|
| 24h changes | Short-term positioning |
| 7d changes | Swing trade positioning |
| 30d changes | Trend positioning |

## Real-World Examples

### Strong Bullish Signal
```
3 funds added $5M+ positions in 7 days
5 All Time Smart Traders increased by 20%+
New positions from 2 previously uninvested funds
= High conviction accumulation
```

### Warning Signal
```
Top fund reduced position by 40%
3 Smart Traders sold entire positions
No new fund entries
= Distribution in progress
```

## Fund vs Smart Trader

| Type | Typical Behavior |
|------|------------------|
| Funds | Larger positions, longer holds, fundamentals-focused |
| Smart Traders | More active, shorter holds, momentum-focused |

When both agree (buying or selling), signal is stronger.

## Limitations

1. **Delayed labeling** — New profitable wallets take time to get labeled
2. **Not infallible** — Smart money makes mistakes too
3. **Position size unknown** — % change matters more than absolute
4. **Hedging** — May have offsetting positions elsewhere

## Combining with Other Signals

Smart money is most useful when combined with:
- **CEX flows** — Are exchange flows confirming?
- **Top PnL traders** — What are the best performers doing?
- **Fresh wallets** — Are new entrants coming in?

## Where to Find This Data

**Nansen Tools:**
- `token_current_top_holders` with `labelType: "smart_money"`
- `smart_traders_and_funds_token_balances` — Aggregated holdings
- `token_recent_flows_summary` — Smart Money segment

**Sample Query:**
```
token_current_top_holders:
  chain: ethereum
  tokenAddress: 0x...
  labelType: smart_money
  order_by: balance_change_7d
```
