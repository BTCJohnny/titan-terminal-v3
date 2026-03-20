# Liquidation Map

## Purpose

Build a liquidation cascade map from the crowded side's positions. This reveals where forced buying/selling will occur, how much pressure each level generates, and where the cascade fuel runs out.

## Prerequisites

Requires completed [positioning-scan.md](positioning-scan.md) with individual position data including liquidation prices.

## Building the Map

### Step 1: Identify the Minority Side

The squeeze direction is AGAINST the crowded side:
- **Crowded shorts** → Short squeeze (price goes UP, shorts get liquidated)
- **Crowded longs** → Long squeeze (price goes DOWN, longs get liquidated)

### Step 2: Sort by Liquidation Distance

**For short squeeze** (most common in crypto):
- Sort short positions by **ascending liquidation price** (closest to current price first)
- These are the first dominos — the positions that get liquidated first as price rises

**For long squeeze:**
- Sort long positions by **descending liquidation price** (closest to current price first)
- These get liquidated first as price falls

### Step 3: Calculate Distance from Current Price

For each position:
```
distance_% = abs(liquidation_price - current_price) / current_price * 100
```

### Step 4: Identify Cascade Clusters

A **cascade cluster** = multiple liquidations within 2-3% of each other.

Why clusters matter:
- Liquidation 1 triggers forced buy → price moves up
- Price movement triggers Liquidation 2 → more forced buy → price moves more
- This cascade effect accelerates through clusters
- Fuel gaps (>5% between clusters) = cascade pauses

### Step 5: Calculate Cumulative Pressure

For each liquidation and cluster:
- **Individual pressure** = position size of that trader
- **Cluster pressure** = sum of all positions in the cluster
- **Cumulative pressure** = running total from first liquidation through current level

## Output Format: Liquidation Cascade Table

```
| # | Trader | Direction | Size | Entry | Liq Price | Distance | Cumulative |
|---|--------|-----------|------|-------|-----------|----------|------------|
| 1 | Fund A | SHORT | $5.2M | $2,000 | $2,203 | 6.8% | $5.2M |
| 2 | Fund B | SHORT | $8.1M | $1,980 | $2,245 | 8.8% | $13.3M |
| 3 | Fund C | SHORT | $10.4M | $1,950 | $2,478 | 20.1% | $23.7M |
```

## Key Metrics to Extract

### Trigger Line
- **Definition:** The first liquidation level closest to current price
- **Distance:** How far price needs to move to start the cascade
- <5% = imminent, 5-10% = catalyst needed, >10% = distant

### Cascade Zones
Group liquidations into zones:
- **Zone 1 (Trigger):** First 1-2 liquidations — starts the cascade
- **Zone 2 (Acceleration):** Next cluster — cascade gains momentum
- **Zone 3 (Exhaustion):** Final liquidations — cascade fuel runs out

### Fuel Gaps
- Gaps >5% between liquidation levels = cascade may stall
- Gaps <2% between levels = cascade accelerates through
- The first major fuel gap is your **primary target** (take profit before momentum dies)

### Total Cascade Pressure
- Sum of all position sizes that would be force-closed
- This is the total mechanical buying/selling pressure
- Compare to average daily volume for impact assessment

## Cascade Impact Assessment

| Total Forced Pressure | vs Daily Volume | Impact |
|-----------------------|-----------------|--------|
| >50% of daily volume | Massive | Price will move significantly |
| 20-50% of daily volume | Large | Noticeable price impact |
| 10-20% of daily volume | Moderate | Needs additional flow |
| <10% of daily volume | Small | Squeeze alone won't move price much |

## Output

After this step you should have:

```
Liquidation Cascade Map:
- Squeeze Direction: [Short/Long] squeeze
- Trigger Line: $X,XXX (X.X% from current)
- Cascade Zones:
  - Zone 1 (Trigger): $X,XXX-$X,XXX — $X.XM forced [buy/sell]
  - Zone 2 (Acceleration): $X,XXX-$X,XXX — $X.XM cumulative
  - Zone 3 (Exhaustion): $X,XXX-$X,XXX — $X.XM total
- Fuel Gaps: [location and size]
- Total Cascade Pressure: $X.XM
- vs Daily Volume: X.X%
```
