# Momentum Check

## Purpose
Quick assessment of momentum using RSI, MACD, and ADX indicators.

## How to Use
Say: "Momentum check on [TOKEN]" or "RSI MACD for [TOKEN]"

Examples:
- "Momentum check on ETH"
- "Is BTC momentum bullish?"
- "RSI MACD ADX for SOL"
- "Check momentum on LINK"

## What It Does

1. Calculates RSI (Relative Strength Index)
2. Calculates MACD (Moving Average Convergence Divergence)
3. Calculates ADX (Average Directional Index)
4. Synthesizes into overall momentum verdict

## Output Format

```
## Momentum Check: [TOKEN]

### Indicators

| Indicator | Value | Signal |
|-----------|-------|--------|
| RSI (14) | XX | Oversold/Neutral/Overbought |
| MACD | X.XX | Bullish/Bearish (above/below signal) |
| ADX | XX | Weak/Moderate/Strong trend |

### Momentum: [Bullish/Bearish/Neutral]

**Summary:** [1-2 sentence interpretation]
```

## CLI Command

```bash
python3 src/analysis/indicators.py analyze ETH --indicators rsi,macd,adx
```

## Indicator Interpretation

### RSI (Relative Strength Index)
| Range | Condition | Action |
|-------|-----------|--------|
| <30 | Oversold | Look for long entries |
| 30-70 | Neutral | Follow trend |
| >70 | Overbought | Look for exits/shorts |

### MACD
| Condition | Signal |
|-----------|--------|
| MACD > Signal line | Bullish momentum |
| MACD < Signal line | Bearish momentum |
| Histogram expanding | Momentum increasing |
| Histogram contracting | Momentum fading |

### ADX (Trend Strength)
| Range | Meaning |
|-------|---------|
| <20 | No trend / ranging |
| 20-25 | Trend emerging |
| 25-50 | Strong trend |
| >50 | Extremely strong trend |

## Confluence

**Strong Bullish:**
- RSI rising from oversold
- MACD above signal and rising
- ADX >25 confirming trend

**Strong Bearish:**
- RSI falling from overbought
- MACD below signal and falling
- ADX >25 confirming trend

**Wait for Clarity:**
- RSI neutral (40-60)
- MACD near zero line
- ADX <20 (no trend)
