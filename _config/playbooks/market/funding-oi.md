# Funding Rate + Open Interest Check

## Purpose
Analyze derivatives positioning data to identify overleveraged conditions and sentiment extremes that often precede reversals.

## How to Use
Say: "Funding and OI check for [TOKEN]" or "Derivatives positioning for [TOKEN]"

Examples:
- "Funding and OI check for BTC"
- "Derivatives positioning for ETH"
- "Check funding rates on SOL"
- "Is DOGE overleveraged?"

## What It Does

1. **Funding Rate Analysis** — Fetch funding rates via Binance, interpret vs thresholds
2. **Open Interest Screening** — Query Nansen for OI data on Hyperliquid perps
3. **Smart Money Perps** — Check fund/smart trader positioning on Hyperliquid

## Output Format

```
## Derivatives Check: [TOKEN] — [Date]

### Funding Rate
**Current:** [+/-X.XXX%] | **7D Avg:** [+/-X.XXX%]
**Signal:** [Extreme Greed / Elevated / Neutral / Elevated Fear / Extreme Fear]

### Open Interest
**Current OI:** $XXX.XM
**24H Change:** +/-XX%
**Signal:** [Rising (more leverage) / Falling (deleveraging)]

### Smart Money Perps (Hyperliquid)
| Side | Count | Value |
|------|-------|-------|
| Long | X | $XXM |
| Short | X | $XXM |
**Net Position:** [Bullish / Bearish / Neutral]

### Interpretation
[What the derivatives data tells us about positioning and likely moves]

### Contrarian Alert
[If extremes detected — what the crowded trade might be]
```

## Interpretation Thresholds

### Funding Rates
| Funding Rate | Signal | Meaning |
|--------------|--------|---------|
| > +0.1% | Extreme Greed | Longs overleveraged, contrarian bearish |
| +0.03% to +0.1% | Elevated | Bullish bias, watch for reversal |
| -0.01% to +0.03% | Neutral | No extreme positioning |
| -0.1% to -0.01% | Elevated Fear | Bearish bias, watch for squeeze |
| < -0.1% | Extreme Fear | Shorts overleveraged, contrarian bullish |

### Open Interest Signals
| OI Trend | Price Trend | Signal |
|----------|-------------|--------|
| Rising | Rising | Healthy uptrend (new money entering longs) |
| Rising | Falling | Healthy downtrend (new money entering shorts) |
| Falling | Rising | Short squeeze (shorts covering) |
| Falling | Falling | Long liquidations (longs capitulating) |

### Contrarian Framework
| Condition | Contrarian View |
|-----------|-----------------|
| Funding > +0.1% + Rising OI | Too many longs — fade the crowd |
| Funding < -0.1% + Rising OI | Too many shorts — squeeze incoming |
| Funding extreme + OI declining | Liquidation cascade underway — wait |

## Tools Used

1. **Binance Fetcher** (local CLI):
   ```bash
   python3 src/fetchers/binance_fetcher.py BTC --funding --days 7
   ```

2. **Nansen MCP** — `token_discovery_screener`:
   - Filter by `hyperliquid` chain
   - Use `openInterest` and `volume` filters
   - Sort by `netflow` or `openInterest`

3. **Nansen MCP** — `smart_traders_and_funds_perp_trades`:
   - Filter by token symbol
   - Check Long vs Short distribution
   - Filter by `includeSmartMoneyLabels: ["Fund", "All Time Smart Trader"]`

## Example Workflow

```
User: "Funding and OI check for ETH"

Claude:
1. Run: python3 src/fetchers/binance_fetcher.py ETH --funding --days 7
2. Query Nansen token_discovery_screener for ETH on hyperliquid
3. Query smart_traders_and_funds_perp_trades for ETH
4. Synthesize into output format
5. Flag any contrarian alerts
```

## Trading Application

**When to Use:**
- Before entering a position — check if you're joining a crowded trade
- During a trade — monitor for leverage buildup against you
- After big moves — check if positioning has reset

**Position Sizing Adjustments:**
| Funding Condition | Size Adjustment |
|-------------------|-----------------|
| Extreme (>0.1% or <-0.1%) | Reduce size 50% |
| Elevated | Reduce size 25% |
| Neutral | Full size |
| Against your direction | Consider reversal |

**Caution Flags:**
- Funding >0.1% on long entry = HIGH RISK
- Funding <-0.1% on short entry = HIGH RISK
- Both extremes = potential liquidation cascade
