# Volume Analysis

## Purpose
Identify volume contraction during the accumulation phase. Declining volume while price stabilizes indicates selling exhaustion — weak hands have exited, setting up conditions for a low-volume breakout.

## Data Source

Use price history from Step 2 (price-positioning) or:
```bash
python3 src/analysis/indicators.py download [TOKEN] --timeframe 1d --force
python3 src/analysis/indicators.py analyze [TOKEN] --indicators obv
```

Or from Nansen:
```
Tool: mcp__nansen__token_ohlcv
Parameters:
  tokenAddress: "[contract-address]"
  chain: "[chain]"
  date: { from: "30D_AGO", to: "NOW" }
```

## What to Measure

### Volume Contraction

Calculate the **average daily volume over the last 20 trading days** as the baseline, then compare against the **most recent 7-day average**:

```
Contraction % = (7d_avg - 20d_avg) / 20d_avg * 100
```

**⚠️ IMPORTANT:** Always use 7d vs 20d. Do NOT use 7d vs 30d — a 30d average is too diluted by older data and understates the contraction signal.

| Contraction | Score | Interpretation |
|-------------|-------|---------------|
| 20%+ below 20d avg | 2 pts | **Strong dry-up** — sellers exhausted |
| 10-20% below 20d avg | 1 pt | Moderate contraction — interest fading |
| Near average or above | 0 pts | Normal volume — no dry-up signal |

### Volume at Lows vs Volume at Highs

Key volume-at-price principles:
- **High volume at lows** = capitulation selling (bearish short-term, but may be near bottom)
- **Low volume at lows** = sellers exhausted, no more supply to push price down (bullish)
- **High volume on up-moves** = demand entering (breakout confirmation)

### OBV (On-Balance Volume) Divergence

If OBV is rising while price is flat/declining = **stealth accumulation**. Volume on up-candles exceeds volume on down-candles, but price hasn't responded yet.

## The Volume Dry-Up + Breakout Sequence

The classic pattern:

```
Phase 1: DECLINE
  - Price falling, volume elevated
  - Selling pressure active

Phase 2: DRY-UP (accumulation zone)
  - Price stabilizes in narrow range
  - Volume drops 20-40% below average
  - Low volatility, boring price action
  - THIS IS WHERE ENTITIES ARE LOADING

Phase 3: BREAKOUT
  - Volume spike 2x+ average on up-move
  - Price breaks above consolidation range
  - Breakout on high volume = real (not fake)
  - Breakout on low volume = suspect (likely fails)
```

## Case Study Evidence

**SOL:**
- Dec 1-10: Daily volume $6.5-7.7B (normal)
- Dec 13-14: Volume dropped to $5.2-5.4B (dry-up beginning)
- Dec 20-28: Volume $5.0-6.5B during accumulation (**30% below avg**)
- Jan 2-6: Volume $6.4-8.4B (breakout)
- Jan 12-15: Volume $8.2-11.2B (**2x expansion** = confirmation)

**ZRO:**
- Volume at Dec 25 low was **40% below average** — classic exhaustion
- Breakout volume was 2.5x+ average

## Volume + Entity Confirmation

The strongest signal is volume dry-up WHILE entities are loading:
- Low volume = nobody else is paying attention
- Entity balance increasing = informed money is quietly absorbing supply
- When volume returns (breakout), the supply squeeze is already in place

If volume is HIGH while entities accumulate, the move may be more visible to the market and thus less alpha-generating.

## Output

Report:
- **Current volume vs 20d avg:** X% [above/below]
- **Volume trend (last 2 weeks):** Declining / Stable / Rising
- **Volume at recent lows:** X% of average (high/low)
- **OBV divergence:** Yes / No
- **Score:** X/2
