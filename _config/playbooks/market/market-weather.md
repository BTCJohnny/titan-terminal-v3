# Market Weather

## Purpose
Daily market overview — is it sunny (bullish), stormy (bearish), or cloudy (uncertain)?

## How to Use
Say: "Market weather" or "Market check"

Examples:
- "Market weather report"
- "Market check"
- "How's the market looking?"
- "Daily market overview"

## What It Does

1. Checks BTC and ETH price action (market leaders)
2. Reviews total crypto market cap trend
3. Assesses smart money flows across chains
4. Checks sector performance
5. Synthesizes into weather metaphor

## Output Format

```
# Market Weather Report — [Date]

## Conditions: [Sunny/Cloudy/Stormy] ☀️/⛅/🌧️

### Market Leaders

| Asset | Price | 24h Change | 7d Change |
|-------|-------|------------|-----------|
| BTC | $XX,XXX | +X.X% | +X.X% |
| ETH | $X,XXX | +X.X% | +X.X% |

### Market Cap
**Total:** $X.XXT | **24h Change:** +X.X%

### Smart Money Activity
[Summary of fund flows — bullish, bearish, or mixed]

### Sector Performance
| Sector | 24h | Leader |
|--------|-----|--------|
| DeFi | +X% | [token] |
| L1/L2 | +X% | [token] |
| Memes | +X% | [token] |

### Forecast
[1-2 sentence outlook]

---

**Trading Stance:** [Risk-On / Risk-Off / Neutral]
```

## Weather Conditions

| Condition | Criteria |
|-----------|----------|
| ☀️ Sunny | BTC up, ETH up, smart money buying, sectors green |
| ⛅ Cloudy | Mixed signals, no clear direction |
| 🌧️ Stormy | BTC down, ETH down, smart money selling, sectors red |

## Tools Used

1. `get-coin-by-id` (CoinStats) — BTC/ETH prices
2. `get-market-cap` (CoinStats) — Total market cap
3. `smart_traders_and_funds_token_balances` (Nansen) — Smart money
4. `token_discovery_screener` (Nansen) — Sector leaders

## Auto-Dashboard

Market weather can auto-update `signals/dashboards/daily-signals.md` when run.
