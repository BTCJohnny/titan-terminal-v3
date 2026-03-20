# Price Positioning

## Purpose
Determine if the token's price is in an accumulation zone — near the 30-day low, in a consolidation range, with price stability suggesting supply absorption.

## Tool: Price History

```
Tool: mcp__nansen__token_ohlcv
Parameters:
  tokenAddress: "[contract-address]"
  chain: "[chain]"
  date: { from: "30D_AGO", to: "NOW" }    # 30-day window minimum
```

**Alternative:** Use Titan TA engine for more data:
```bash
python3 src/analysis/indicators.py download [TOKEN] --timeframe 1d --force
```

## What to Measure

### 1. Distance from 30-Day Low

Calculate: `(current_price - 30d_low) / 30d_low * 100`

| Distance | Score | Interpretation |
|----------|-------|---------------|
| Within 10% of 30d low | 2 pts | **Prime accumulation zone** — price at maximum fear |
| Within 20% of 30d low | 1 pt | Accumulation zone — still discounted |
| > 20% above 30d low | 0 pts | Extended — accumulation window may have passed |

### 2. Consolidation Range

Measure the price band over the last 2-4 weeks:

| Range Width | Interpretation |
|-------------|---------------|
| ±5% or tighter | Very tight consolidation — squeeze imminent |
| ±5-8% | Normal accumulation range |
| ±8-15% | Wide but acceptable if trending toward tighter |
| > ±15% | Not consolidating — still in volatile phase |

**The ideal setup:** Price grinds into a tighter and tighter range near the low, with lower highs and higher lows converging.

### 3. Price Stability During Entity Accumulation

This is the **divergence signal** — the most reliable pattern:
- Entities are increasing positions (balance going up)
- Price is flat or slightly down (no markup yet)
- Volume is declining (nobody else is paying attention)

If price is rising while entities accumulate, the move may already be priced in. The alpha is in catching the quiet phase.

## Output

Report:
- **30-day range:** Low $X — High $X (current $X)
- **Distance from low:** X% (score: X/2)
- **Consolidation band:** ±X% over [timeframe]
- **Divergence present:** Yes/No — entities accumulating while price [stable/declining]

## Key Insight from Case Studies

**ZRO:** CEO bought at $1.24 on Dec 25 — the exact 30-day low. Price was ±8% range. Breakout came 18 days later at +62%.

**SOL:** Wintermute started loading at $117-$125 (within 10% of 30d low). Price was in a ±5% consolidation zone for 14 days. Breakout came with +26%.

**Pattern:** The tighter the consolidation near the low, the more explosive the breakout.
