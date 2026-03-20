# Funding Rates Interpreter

## What Are Funding Rates?

Funding rates are periodic payments between long and short traders in perpetual futures markets. They keep perp prices anchored to spot prices.

## The Mechanism

| Funding Rate | Who Pays | Market Sentiment |
|--------------|----------|------------------|
| Positive (>0) | Longs pay shorts | Bullish bias (more longs) |
| Negative (<0) | Shorts pay longs | Bearish bias (more shorts) |
| Near zero | Balanced | Neutral |

## How to Read

### Moderate Positive (+0.01% to +0.05%)
- Normal bullish sentiment
- Healthy market structure
- No immediate concern

### High Positive (>0.05%)
- Overleveraged longs
- Crowded trade
- Correction risk increasing
- **Contrarian bearish signal**

### Moderate Negative (-0.05% to -0.01%)
- Normal bearish sentiment
- Shorts have conviction
- Can sustain downtrend

### High Negative (<-0.05%)
- Overleveraged shorts
- Crowded short trade
- Short squeeze risk
- **Contrarian bullish signal**

## Time Periods

Funding is typically paid every 8 hours:
- 00:00 UTC
- 08:00 UTC
- 16:00 UTC

**Annualized rate** = Funding rate × 3 × 365

## Real-World Examples

### Short Squeeze Setup
```
Funding: -0.15% (shorts paying heavily)
Price: Consolidating after drop
Smart money: Quietly accumulating
= High probability short squeeze
```

### Long Liquidation Setup
```
Funding: +0.25% (longs paying extreme premium)
Open interest: At all-time highs
Price: Extended from support
= Correction likely, longs will get liquidated
```

## Extreme Readings

| Level | Meaning |
|-------|---------|
| > +0.1% | Extreme greed, expect pullback |
| +0.03% to +0.1% | Bullish but elevated risk |
| -0.01% to +0.03% | Normal range |
| -0.1% to -0.01% | Bearish but elevated short risk |
| < -0.1% | Extreme fear, expect bounce |

## Trading Application

### With the Trend
- Use moderate funding as confirmation
- Positive funding + uptrend = continue long
- Negative funding + downtrend = continue short

### Contrarian
- Extreme funding = fade the crowd
- Very high positive = look for short entries
- Very negative = look for long entries

## Limitations

1. **Can stay extreme** — Markets can remain irrational
2. **Different by token** — Each token has its own normal range
3. **Exchange-specific** — Rates vary across exchanges
4. **Not timing** — Signals direction risk, not exact timing

## Combining with Other Signals

Funding rates are most useful when combined with:
- **Open interest** — High OI + extreme funding = volatility coming
- **Price action** — Is price confirming or diverging?
- **Smart money perps** — What are profitable traders doing?

## Where to Find This Data

**Hyperliquid:**
```bash
python3 src/fetchers/hyperliquid_fetcher.py
```

**Nansen for Smart Perp Traders:**
```
smart_traders_and_funds_perp_trades:
  order_by: valueUsd
  order_by_direction: desc
```

**Note:** Funding rate data typically requires direct exchange API access. Titan uses Hyperliquid fetcher for this.
