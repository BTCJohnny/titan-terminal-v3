# Entity Tracking

## Purpose
Track individual fund and market maker positions over time. This is the **highest-signal data source** in the skill — entity-level balance changes reveal accumulation before any aggregate metric does.

## Why Entity Tracking > Aggregate Flows

Aggregate flow data (exchange flows, "smart money" labels) averages out the signal. Entity tracking isolates **specific actors** with known information advantages:
- A market maker increasing position 3x in 2 weeks is a clear signal
- That same accumulation might be invisible in aggregate "smart money" flow data
- Named entities have track records — you can assess their signal quality

## Primary Tool: Historical Balances

```
Tool: mcp__nansen__address_historical_balances
Parameters:
  entity_id: "[entity-name]"     # e.g., "Wintermute", "Jump Trading"
  chain: "[chain]"               # e.g., "solana", "ethereum"
```

**Run for each entity in the tracking list.** Query at least these:

| Entity | Type | Why Track |
|--------|------|-----------|
| Wintermute | Market Maker | Highest signal from SOL backtest — 3x position before breakout |
| Jump Trading | Prop Firm | Steadier accumulation pattern, confirms Wintermute signal |
| Paradigm Fund | VC | Longer-timeframe conviction signal |
| a16z | VC | Early-stage, pre-announcement accumulation |
| Polychain Capital | VC | Mid/large cap focus |

**Also query any token-specific entities** identified in the token lookup step (founders, team wallets).

## What to Extract

For each entity, build a **weekly position table**:

| Period | Avg Balance | Peak Balance | Change | Action |
|--------|-------------|--------------|--------|--------|
| Week 1 | $X | $X | baseline | Holding |
| Week 2 | $X | $X | +X% | **Accumulating** |
| Week 3 | $X | $X | +X% | **Heavy Loading** |
| Week 4 | $X | $X | -X% | Distributing |

## Magnitude Thresholds (Alpha Score Input)

| Balance Change | Rating | Score |
|----------------|--------|-------|
| +25-50% | Weak signal | 1 pt |
| +50-100% | Strong signal | 2 pts |
| +100%+ | Alpha signal | 3 pts |

**The 3-point alpha threshold** comes from the SOL case study where Wintermute went from $20M to $63M (3x / +215%).

## Interpretation Framework

### Accumulation Phase Signals
- Entity balance increasing week-over-week
- Accumulation accelerating (bigger adds each week)
- Multiple entities accumulating simultaneously (confirmation)
- Peak position reached BEFORE price breakout

### Distribution Phase Signals (entity already selling)
- Entity balance declining after a price run
- Sharp position reduction (>30% in a week)
- Multiple entities reducing simultaneously
- **This means you're too late** — the breakout already happened

### Key Patterns

**Wintermute Pattern (from SOL):**
```
Week 1-2: Testing positions (small adds)
Week 3-4: Heavy accumulation (+45%, +36%)
Week 5:   Peak loading ($63.2M)
Week 6:   DISTRIBUTION into rally
```
Wintermute front-runs price moves by 1-2 weeks. When Wintermute starts distributing, the markup phase is ending.

**Jump Trading Pattern (from SOL):**
```
Slower, steadier adds (+4%, +7%, +5%, +19%)
Continues accumulating even after breakout
More "hold and compound" vs "trade the range"
```
Jump confirms conviction but enters later. Use Wintermute for timing, Jump for conviction.

**Insider Pattern (from ZRO):**
```
Single large buy at or near local low
Often via DEX/aggregator (CoW Protocol, 1inch)
Timing is the key signal — WHY did they buy NOW?
```
Insider buys near lows are the highest-conviction signal because they have information you don't.

## Supplementary Tool: Smart Money Balances

```
Tool: mcp__nansen__smart_traders_and_funds_token_balances
Parameters:
  chains: ["ethereum", "solana", "base"]
  includeSmartMoneyLabels: ["Fund", "All Time Smart Trader"]
```

This gives a broader view of fund positioning but at lower granularity than entity tracking. Use it to:
- Identify entities you didn't know held the token
- Get a quick "is anyone institutional even in this token?" answer
- Cross-reference with entity tracking data

## DB-Assisted Tracking

On every run, log entity positions to the intelligence DB:
```bash
python3 src/storage/intelligence.py store-entities \
    --token [TOKEN] --date [YYYY-MM-DD] --chain [CHAIN] \
    --data '[{"entity_name": "Wintermute", "entity_address": "0x...", "entity_type": "Market Maker", "balance": 63200000, "balance_usd": 63200000, "change_7d": 14000000, "change_30d": 43000000}]'
```

On subsequent runs, check stored history BEFORE querying Nansen:
```bash
python3 src/storage/intelligence.py entity-diff [TOKEN]
python3 src/storage/intelligence.py entity-history [TOKEN] --days 30
```

This gives you:
- **Week-over-week position changes** from your own historical snapshots
- **New entity detection** (entities that appeared since last snapshot)
- **Distribution detection** (entities that reduced positions since last snapshot)

The DB data is more precise than Nansen's sometimes-limited historical view because it's YOUR observations at specific points in time.

### Distributor Exhaustion

For any entity with a declining balance:
1. Current remaining position: [balance] tokens / $[USD]
2. Weekly sell rate: [7d change] tokens/week
3. Estimated weeks remaining: remaining / weekly_sell_rate

Flag if > 4 weeks: "⚠️ Active distribution overhead — [Entity] has ~X weeks of sell pressure at current rate"

If total distribution rate across all sellers exceeds total accumulation rate across all buyers, flag: "⚠️ NET entity flow is negative — distribution exceeds accumulation"

---

## Limitations

- Entity data often has **weekly granularity**, not daily — can't pinpoint exact entry dates
- Not all entities are tracked by Nansen — some operate through unlabeled wallets
- Entity identifiers may differ across chains (Wintermute on ETH vs SOL)
- **Balance ≠ buying.** An entity's balance can increase from receiving tokens (vesting, airdrops) not just market purchases. Check the source of balance increases.

## Output

For each tracked entity, report:
- **Entity name** + wallet type
- **Position size** (current USD value)
- **Change over analysis window** (% and USD)
- **Accumulation phase timing** (which weeks showed loading)
- **Signal strength:** Weak / Strong / Alpha (per magnitude thresholds)
