---
name: market-check
description: Quick market overview — BTC and ETH health, total market cap, smart money activity, and a trading stance assessment.
allowed-tools:
  - Read
  - Bash
  - mcp__nansen
  - mcp__coinstats
---

# /market-check

Quick market health check. Answers: "Is the market risk-on, risk-off, or neutral right now?"

## What This Produces

A Market Weather Report — a concise snapshot of market conditions using BTC and ETH as barometers, plus smart money activity for directional bias.

---

## Execution Plan

### Step 1: Market Leaders (parallel)

Fetch BTC and ETH data simultaneously:

```
mcp__coinstats__get-coin-by-id: coinId "bitcoin"
mcp__coinstats__get-coin-by-id: coinId "ethereum"
```

Extract for each: price, 24h change %, 7d change %, market cap, 24h volume.

### Step 2: Total Market Cap

```
mcp__coinstats__get-market-cap
```

Extract: total crypto market cap, 24h change %, BTC dominance %.

### Step 2b: Derivatives Temperature

```bash
python3 src/fetchers/coinglass_fetcher.py --market --json
```

If COINGLASS_API_KEY is not set or call fails, skip and note "Derivatives data unavailable."

### Step 3: Smart Money Activity

```
mcp__nansen__smart_traders_and_funds_token_balances
```

Extract: What are the top smart money funds buying or selling? Any notable position changes in the last 24h?

If Nansen fails, skip this section and note "Smart money data unavailable."

### Step 4: Watchlist Pulse (optional)

If the watchlist has active items:

```bash
python3 src/watchers/watchlist_monitor.py summary
```

Include a 1-line watchlist status. If no watchlist items exist, skip this step entirely.

---

### Step 5: Synthesize Weather Report

Determine market conditions:

| Condition | Criteria |
|-----------|----------|
| ☀️ **Sunny (Risk-On)** | BTC up, ETH up, smart money buying, positive market cap trend + F&G > 50, ETF inflows, positive Coinbase premium |
| ⛅ **Cloudy (Neutral)** | Mixed signals — some up, some down, no clear direction + mixed derivatives signals |
| 🌧️ **Stormy (Risk-Off)** | BTC down, ETH down, smart money selling, declining market cap + F&G < 30, ETF outflows, extreme funding, negative Coinbase premium |

### Output Format

```
# Market Weather — [YYYY-MM-DD]

## Conditions: [☀️ Sunny / ⛅ Cloudy / 🌧️ Stormy]

**BTC:** $XX,XXX ([+/-]X.X% 24h | [+/-]X.X% 7d)
**ETH:** $X,XXX ([+/-]X.X% 24h | [+/-]X.X% 7d)
**Total Market Cap:** $X.XXT ([+/-]X.X% 24h) | **BTC Dominance:** XX.X%

---

## Derivatives Temperature
**Fear & Greed:** [value] — [label]
**BTC Funding:** [rate]% | **ETH Funding:** [rate]%
**BTC OI:** [+/-X% 24h] | **Momentum:** [Expanding/Contracting/Stable]
**ETF Flows:** $[latest day] | **Weekly:** $[net flow]
**Coinbase Premium:** [+/-$X] — [US buying/selling/neutral]
**BTC L/S (Global):** [X.Xx] — [X% long]

## Smart Money
[What are funds doing? Buying, selling, rotating? 2-3 sentences max.]

## Watchlist Pulse
[1-line summary of watchlist status, or omit if no watchlist items]

---

**Trading Stance:** [Risk-On / Risk-Off / Neutral] — [1-sentence reason]
```

---

## Formatting Rules

- This is a QUICK check — keep it under 20 lines of output
- Verdict first (conditions + stance), then supporting data
- Bold all prices and percentages
- If any data source fails, complete what you can — partial weather is better than no weather
- Never hedge the trading stance — pick one and own it
