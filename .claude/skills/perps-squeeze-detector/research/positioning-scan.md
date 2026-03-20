# Positioning Scan

## Purpose

Pull and tally Hyperliquid smart money perpetual positions to identify extreme long/short imbalances. This is the foundation of every squeeze analysis — without a significant imbalance, there's no squeeze.

## Primary Tool

**Tool:** `mcp__nansen__token_current_top_holders`

**Parameters:**
- `tokenId`: Token symbol (e.g., "ETH", "BTC", "WIF")
- `mode`: `"perps"`
- `labelType`: `"smart_money"`
- `chain`: `"hyperliquid"`

## What to Extract

From each position in the results:

| Field | What It Tells You |
|-------|-------------------|
| **Direction** (long/short) | Which side they're on |
| **Position size ($)** | Dollar magnitude of the bet |
| **Entry price** | Where they entered — are they underwater? |
| **Mark price** | Current price — compare to entry for P&L |
| **Liquidation price** | Critical for cascade mapping |
| **Entity/label** | Who is this trader? (fund name, smart money label) |

## Tally Process

1. **Separate positions** into long and short buckets
2. **Sum dollar amounts** for each side:
   - `total_long_$` = sum of all long position sizes
   - `total_short_$` = sum of all short position sizes
3. **Count traders** on each side:
   - `long_count` = number of long positions
   - `short_count` = number of short positions
4. **Calculate imbalance ratio:**
   - `ratio = max(total_long, total_short) / min(total_long, total_short)`
   - Direction = whichever side is larger is the "crowded" side

## Imbalance Thresholds

| Ratio | Classification | Action |
|-------|---------------|--------|
| <2:1 | Balanced | No squeeze setup — skip |
| 2:1 - 3:1 | Mild imbalance | Note but don't trade |
| 3:1 - 5:1 | Significant imbalance | Investigate further |
| 5:1 - 10:1 | Extreme imbalance | Squeeze setup forming — proceed to liquidation map |
| 10:1+ | Critical imbalance | High probability squeeze — full analysis |

## Underwater Assessment

For each position on the crowded side:
- **Entry price vs mark price** — Is the trader profitable or underwater?
- Underwater traders are MORE likely to get squeezed (tighter stops, higher stress)
- Profitable traders have more cushion before liquidation
- Flag traders with >20% unrealized loss — they're the first dominos

## Position Concentration

Check if the imbalance is:
- **Distributed** — Many traders on one side (stronger signal, harder to unwind quietly)
- **Concentrated** — One whale on one side (could unwind in a single trade, less cascade)

Distributed imbalances create better squeeze setups because cascading liquidations feed on each other.

## Output

After this step you should have:

```
Positioning Summary:
- Total Long: $X.XM across N traders
- Total Short: $X.XM across N traders
- Imbalance: X:1 [direction]-heavy
- Crowded Side: [Long/Short]
- Underwater Traders: N of M on crowded side
- Concentration: [Distributed/Concentrated]
```
