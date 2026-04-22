# Sector Rotation

## Purpose
Identify which sectors are leading or lagging — follow the money.

## How to Use
Say: "Sector rotation" or "Which sectors are moving?"

Examples:
- "Sector rotation analysis"
- "What sectors are hot?"
- "Where is money rotating to?"
- "Sector performance today"

## What It Does

1. Scans tokens by sector
2. Calculates sector-level performance
3. Identifies leaders and laggards
4. Spots rotation patterns

## Output Format

```
## Sector Rotation — [Date]

### Performance (24h)

| Sector | Performance | Net Flow | Leader | Laggard |
|--------|-------------|----------|--------|---------|
| AI/ML | +8.5% | +$50M | RENDER | FET |
| DeFi | +3.2% | +$20M | AAVE | UNI |
| L1/L2 | +1.5% | -$10M | SOL | AVAX |
| Memes | -2.1% | -$30M | DOGE | SHIB |

### Rotation Pattern
[Description of where money is flowing]

### Sector to Watch
**[Sector]** — [Why it's interesting]

### Trading Implication
[What the rotation suggests for positioning]
```

## Available Sectors

| Sector | Examples |
|--------|----------|
| Artificial Intelligence | RENDER, FET, OCEAN |
| AI Agents | VIRTUAL, AI16Z |
| DeFi Lending | AAVE, COMP, MKR |
| Decentralised Exchanges | UNI, SUSHI, CRV |
| L1/L2 | SOL, AVAX, ARB, OP |
| Memecoins | DOGE, SHIB, PEPE |
| GameFi | AXS, SAND, MANA |
| RWAs | ONDO, MAPLE |

## Tools Used

1. `token_discovery_screener` (Nansen) — Filter by sector
   ```
   sectors: ["Artificial Intelligence"], timeframe: "24h", orderBy: "priceChange"
   ```

2. `get-coins` (CoinStats) — Category filtering
   ```
   categories: "defi", sortBy: "priceChange1d"
   ```

## Rotation Patterns

**Risk-On Rotation:**
BTC/ETH → Large caps → Mid caps → Small caps → Memes

**Risk-Off Rotation:**
Memes → Small caps → Mid caps → BTC/ETH → Stables

**Sector Rotation:**
Money flows from overbought sectors to underperforming sectors with catalysts.

## Trading Application

- **Lead sectors:** Look for entries in lagging tokens within hot sectors
- **Lag sectors:** Avoid or short; money is leaving
- **Rotation point:** When leader pauses, next sector often starts
