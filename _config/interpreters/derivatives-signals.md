# Derivatives Signals Interpreter

## What Are Derivatives Signals?

Derivatives signals come from perpetual futures, options, and liquidation data. They reveal how leveraged traders are positioned — and where the mechanical pressure is building.

## Signal Sources

| Source | Data | Tool |
|--------|------|------|
| Hyperliquid | Funding rate, OI, smart perp positions | `python3 src/fetchers/hyperliquid_fetcher.py` |
| Coinglass | Liquidation maps, large limit orders, max pain | `python3 src/fetchers/coinglass_fetcher.py` |
| Nansen | Smart money perp trades | `smart_traders_and_funds_perp_trades` |

---

## 1. Funding Rate

**What it measures:** Cost of holding longs vs shorts in perpetual futures.

| Reading | Meaning | Action |
|---------|---------|--------|
| > +0.1% | Extreme long crowding | Contrarian short — longs will get squeezed |
| +0.03% to +0.1% | Elevated bullish bias | Reduce long size, watch for reversal |
| -0.01% to +0.03% | Neutral | No contrarian signal |
| -0.1% to -0.01% | Elevated short bias | Watch for short squeeze |
| < -0.1% | Extreme short crowding | Contrarian long — shorts will get squeezed |

---

## 2. Open Interest (OI)

**What it measures:** Total value of open derivative positions.

| OI Trend | Price Trend | Signal |
|----------|-------------|--------|
| Rising | Rising | New money entering longs — healthy uptrend |
| Rising | Falling | New money entering shorts — healthy downtrend |
| Falling | Rising | Short squeeze — shorts covering |
| Falling | Falling | Long liquidations — longs capitulating |

**Key rule:** Rising OI + extreme funding = leverage bubble. When it unwinds, it unwinds fast.

---

## 3. Liquidation Maps

**What it measures:** Where forced liquidations will cluster if price moves.

- **Long liquidation zones:** Price ranges where long positions get force-closed (price DOWN triggers)
- **Short liquidation zones:** Price ranges where short positions get force-closed (price UP triggers)

**Cascade logic:** Once the first liquidation triggers, forced selling (or buying) pushes price into the next cluster — self-reinforcing.

| Scenario | What to Expect |
|----------|----------------|
| Dense short liq cluster above price | Short squeeze fuel — break above triggers cascade |
| Dense long liq cluster below price | Long liquidation risk — break below triggers cascade |
| Thin liquidation zones | No mechanical momentum — move fades |

---

## 4. Long/Short Ratio

**What it measures:** Ratio of accounts holding longs vs shorts on a token.

| Reading | Interpretation |
|---------|----------------|
| >5:1 long-heavy | Extreme crowded trade — short squeeze DOWN risk |
| 2-5:1 long-heavy | Elevated longs — watch for long liquidation |
| 0.5:1 to 2:1 | Balanced — no extreme positioning |
| 2-5:1 short-heavy | Elevated shorts — short squeeze UP risk |
| >5:1 short-heavy | Extreme crowding — squeeze UP highly probable |

---

## 5. Smart Money Perp Positions

**What it measures:** What profitable Hyperliquid traders are actually positioned in.

| Signal | Meaning |
|--------|---------|
| Smart money net long, large size | Directional conviction — they expect UP |
| Smart money net short, large size | Directional conviction — they expect DOWN |
| Smart money split | Uncertainty or hedging |
| Smart money opposing retail | Follow smart money — retail is usually wrong at extremes |

---

## Combined Reading: The Full Derivatives Picture

The highest conviction setups combine all signals:

**Squeeze UP setup:**
- Funding negative (shorts paying)
- OI rising (new shorts opening)
- Dense short liq cluster above current price
- Smart money perps net long

**Squeeze DOWN setup:**
- Funding very positive (longs paying)
- OI rising (new longs opening)
- Dense long liq cluster below current price
- Smart money perps net short

---

## Where to Find This Data

```bash
# Full derivatives check (funding, OI, L/S, liquidations)
python3 src/fetchers/coinglass_fetcher.py --token BTC --derivatives --price 84000

# Liquidation map only
python3 src/fetchers/coinglass_fetcher.py --token BTC --price 84000

# Hyperliquid perps + smart money positions
python3 src/fetchers/hyperliquid_fetcher.py
```

**Nansen for smart perp traders:**
```
smart_traders_and_funds_perp_trades:
  includeSmartMoneyLabels: ["Fund", "All Time Smart Trader", "Smart HL Perps Trader"]
  order_by: valueUsd
```
