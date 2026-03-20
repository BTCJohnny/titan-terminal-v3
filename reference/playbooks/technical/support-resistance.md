# Support & Resistance

## Purpose
Identify key price levels for entries, exits, and stop placement.

## How to Use
Say: "Support and resistance for [TOKEN]" or "Key levels for [TOKEN]"

Examples:
- "Support and resistance for ETH"
- "Key levels for BTC"
- "Where are support and resistance for SOL?"
- "S/R levels on LINK"

## What It Does

1. Downloads recent OHLCV data (4h default)
2. Calculates swing highs and lows
3. Identifies support levels (price floors)
4. Identifies resistance levels (price ceilings)
5. Notes current price relative to levels

## Output Format

```
## Support & Resistance: [TOKEN]

**Current Price:** $X,XXX

### Key Levels

| Level | Type | Distance | Strength |
|-------|------|----------|----------|
| $X,XXX | Resistance | +X.X% | Strong (tested 3x) |
| $X,XXX | Resistance | +X.X% | Moderate |
| **$X,XXX** | **Current** | — | — |
| $X,XXX | Support | -X.X% | Strong |
| $X,XXX | Support | -X.X% | Moderate |

### Trading Zones
- **Resistance Zone:** $X,XXX - $X,XXX
- **Support Zone:** $X,XXX - $X,XXX

### Interpretation
[Where price is relative to key levels, what a break would mean]
```

## CLI Command

```bash
python3 src/analysis/indicators.py analyze ETH --indicators sr
```

## Level Strength

| Tests | Strength | Meaning |
|-------|----------|---------|
| 3+ | Strong | Well-established level, expect reaction |
| 2 | Moderate | Likely to hold, but could break |
| 1 | Weak | Tentative level, needs confirmation |

## Trading Application

**At Support:**
- Look for long entries
- Place stops below support
- Target resistance above

**At Resistance:**
- Look for short entries or profit-taking
- Place stops above resistance
- Watch for breakout confirmation

**Between Levels:**
- Wait for price to reach key level
- Avoid chasing in no-man's land
