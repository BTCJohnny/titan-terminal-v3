# Trend Analysis

## Purpose
Multi-timeframe trend assessment to identify the dominant direction.

## How to Use
Say: "Trend analysis for [TOKEN]" or "What's the trend on [TOKEN]?"

Examples:
- "Trend analysis for ETH"
- "What's the trend on BTC?"
- "Is SOL in an uptrend?"
- "Multi-timeframe trend for LINK"

## What It Does

1. Analyzes multiple timeframes (1h, 4h, 1d)
2. Checks price vs moving averages
3. Calculates trend strength (ADX)
4. Identifies trend alignment or divergence

## Output Format

```
## Trend Analysis: [TOKEN]

### Multi-Timeframe View

| Timeframe | Trend | Strength | Price vs MA |
|-----------|-------|----------|-------------|
| 1H | Up/Down/Ranging | Weak/Moderate/Strong | Above/Below 20 EMA |
| 4H | Up/Down/Ranging | Weak/Moderate/Strong | Above/Below 50 EMA |
| 1D | Up/Down/Ranging | Weak/Moderate/Strong | Above/Below 200 EMA |

### Trend Alignment: [Aligned/Mixed/Conflicting]

**Primary Trend (Daily):** [Up/Down/Ranging]
**Trading Trend (4H):** [Up/Down/Ranging]
**Momentum (1H):** [Up/Down/Ranging]

### Summary
[Interpretation of trend alignment and trading implications]
```

## CLI Commands

```bash
# Analyze each timeframe
python3 src/analysis/indicators.py download ETH --timeframe 1h
python3 src/analysis/indicators.py analyze ETH --indicators adx,ema

python3 src/analysis/indicators.py download ETH --timeframe 4h
python3 src/analysis/indicators.py analyze ETH --indicators adx,ema

python3 src/analysis/indicators.py download ETH --timeframe 1d
python3 src/analysis/indicators.py analyze ETH --indicators adx,ema
```

## Trend Rules

### Uptrend Criteria
- Price making higher highs and higher lows
- Price above key moving averages (20, 50, 200)
- ADX >25 with +DI > -DI

### Downtrend Criteria
- Price making lower highs and lower lows
- Price below key moving averages
- ADX >25 with -DI > +DI

### Ranging/No Trend
- Price oscillating without clear direction
- ADX <20
- Moving averages flat or intertwined

## Timeframe Hierarchy

| Timeframe | Purpose | Weight |
|-----------|---------|--------|
| Daily | Primary trend direction | Highest |
| 4-Hour | Trading trend, swing trades | Medium |
| 1-Hour | Entry timing, momentum | Lowest |

## Trading Application

**All Timeframes Aligned Up:**
- High-confidence long entries
- Buy dips to support
- Use trailing stops

**All Timeframes Aligned Down:**
- High-confidence short entries
- Sell rallies to resistance
- Avoid bottom-picking

**Mixed Timeframes:**
- Reduce position size
- Wait for alignment
- Trade the dominant timeframe only
