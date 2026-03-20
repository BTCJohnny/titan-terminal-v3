# CEX Flows Interpreter

## What Are CEX Flows?

CEX (Centralized Exchange) flows track tokens moving into and out of exchanges like Binance, Coinbase, etc.

## The Key Insight

**Inflows to exchanges = Selling pressure**
People deposit tokens to exchanges to sell them.

**Outflows from exchanges = Accumulation**
People withdraw tokens to hold in self-custody.

This is counterintuitive but critical to understand.

## How to Read

| Flow Direction | Meaning | Trading Signal |
|----------------|---------|----------------|
| Large inflows | Tokens moving TO exchanges | Bearish — selling pressure coming |
| Large outflows | Tokens leaving exchanges | Bullish — accumulation happening |
| Balanced | Normal trading activity | Neutral — no directional bias |

## Magnitude Matters

| vs Average | Interpretation |
|------------|----------------|
| >3x average | Significant move, pay attention |
| 2-3x average | Elevated activity |
| 1-2x average | Normal variance |
| <1x average | Below normal activity |

## Time Context

| Lookback | Use Case |
|----------|----------|
| 5m, 1h | Intraday scalping |
| 6h, 12h | Short-term swings |
| 1d | Daily bias (most common) |
| 7d | Trend confirmation |

## Real-World Examples

### Bullish Setup
```
Exchange flows: -$50M (3.2x average)
= Large outflows = Tokens leaving exchanges
= People withdrawing to hold
= Bullish signal
```

### Bearish Setup
```
Exchange flows: +$120M (4.5x average)
= Large inflows = Tokens depositing to sell
= Selling pressure building
= Bearish signal
```

## Limitations

1. **Not all inflows sell immediately** — Some are for trading, staking, etc.
2. **Whale manipulation** — Large holders can fake signals
3. **Exchange-specific** — Different exchanges have different user bases
4. **Timing unclear** — Inflows may sell today or next week

## Combining with Other Signals

CEX flows are most powerful when combined with:
- **Smart money flows** — Are funds also moving?
- **Price action** — Is price confirming the flow direction?
- **Funding rates** — What are perp traders doing?

## Where to Find This Data

**Nansen Tools:**
- `token_recent_flows_summary` — Quick snapshot with exchange segment
- `token_flows` — Hourly breakdown by holder segment (set `holder_segment: "exchange"`)

**CLI:**
```bash
python3 src/watchers/cex_monitor.py snapshot
```
