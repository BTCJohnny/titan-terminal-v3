# Funding Rate & Perps Positioning

## Purpose
Check Hyperliquid perps for smart money directional positioning. Who's long, who's short, who's making money.

## Tool
```
mcp__nansen__token_current_top_holders:
  tokenAddress: "[SYMBOL]"    # Simple symbol for perps: "PYTH", "LINK"
  mode: "perps"
  labelType: "smart_money"
```

Note: For perps mode, use simple token symbol (not chain/contract).

## What to Extract

Per smart money position: wallet label, side (long/short), position size USD, entry price, unrealized PnL.

## Interpretation

**Key insight:** Who is profitable tells you the direction.

| Pattern | Signal |
|---------|--------|
| Smart money net short AND profitable | **Bearish** |
| Smart money net long AND profitable | **Bullish** |
| Split with no clear profitable side | **Neutral** |
| Smart money long but underwater | **Bearish** — trapped longs add selling pressure |
| Smart money short but underwater | **Bullish** — trapped shorts fuel squeeze |

### Size Ratios
- >5:1 either direction = strong signal
- 2-5:1 = moderate lean
- <2:1 = no clear direction

### Contrarian (Funding Rate)
| Rate | Meaning |
|------|---------|
| Highly positive (>0.01%) | Crowded long — bearish contrarian |
| Highly negative (<-0.01%) | Crowded short — bullish contrarian |

Use contrarian logic only when crowded side is NOT smart money.

## Output Format
```
## Funding Rate: [Bullish/Bearish/Neutral]
- **Smart Money Positioning:** [Net Long/Net Short/Balanced]
- **Contrarian Signal:** [Yes/No]

[Interpretation paragraph with specific positions cited]
```

If no perps data: omit section entirely. Note "No Hyperliquid listing" if relevant.
