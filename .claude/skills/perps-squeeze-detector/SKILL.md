# Description: Detect extreme positioning imbalances on Hyperliquid perps for mechanical squeeze plays.
# Version: 1.0

name: perps-squeeze-detector
version: 1.0
description: >
  Identifies extreme long/short positioning imbalances on Hyperliquid perpetuals
  using smart money data from Nansen. Maps liquidation cascades to calculate
  forced buy/sell pressure zones, then generates high-conviction squeeze trade setups.
  The core thesis: when smart money crowds one side 5:1+, the mechanical unwind
  creates predictable price movements through liquidation cascades.

commands:
  - scan-squeeze: "Analyze a specific token's HL perps positioning for squeeze potential"
  - hunt-squeezes: "Scan across tokens for extreme positioning imbalances"

---

## Overview

Extreme positioning imbalances on Hyperliquid perps create **mechanical squeeze opportunities**. When smart money crowds one side of a trade (5:1+ ratio), the forced liquidation cascade that follows is:

1. **Predictable** — Liquidation prices are known, cascade math is simple
2. **Quantifiable** — Dollar amounts of forced buying/selling can be calculated
3. **High R:R** — Entry before cascade, stop below trigger, targets at cascade exhaustion

This skill formalizes the process discovered during the ETH analysis on 2026-03-04, where a 61:1 short imbalance ($80M short vs $1.3M long) revealed $23.7M in forced buy pressure between $2,200-$2,478.

**Core edge:** Liquidation cascades are mechanical, not discretionary. Once triggered, forced buying/selling creates momentum that feeds on itself.

---

## Commands

### `scan-squeeze [TOKEN]`

Analyze a specific token's HL perps positioning for squeeze potential.

**Workflow:**

1. **Positioning Scan** → [research/positioning-scan.md](research/positioning-scan.md)
   - Pull HL smart money perps data
   - Tally long $ vs short $, count traders each side
   - Calculate imbalance ratio
   - Identify underwater traders (entry vs mark price)

2. **Liquidation Map** → [research/liquidation-map.md](research/liquidation-map.md)
   - Extract liquidation prices from minority side
   - Sort by distance from current price
   - Identify cascade clusters (liquidations within 2-3% of each other)
   - Calculate cumulative forced pressure per zone
   - Find the trigger line (first liquidation level)

3. **Macro Context** → [research/macro-context.md](research/macro-context.md)
   - CEX flow direction (accumulation vs distribution backdrop)
   - BTC momentum (correlation catalyst)
   - Funding rate assessment
   - Spot vs perps divergence check

4. **Squeeze Score** → [synthesis/squeeze-score.md](synthesis/squeeze-score.md)
   - Calculate 0-10 score across 5 signals
   - Determine conviction level

5. **Generate Report** → [synthesis/output-format.md](synthesis/output-format.md)
   - Positioning summary
   - Liquidation cascade map
   - Trade setup (both squeeze direction AND post-squeeze fade)
   - Position sizing with 2% risk

### `hunt-squeezes`

Scan across tokens for extreme positioning imbalances.

**Workflow:**

1. **Candidate Screening** → [research/candidate-screening.md](research/candidate-screening.md)
   - Pull `smart_traders_and_funds_perp_trades` for recent activity
   - Group by token, count long vs short trades
   - Filter for >70% one-sided activity

2. **Deep Scan Top Candidates**
   - Run full `scan-squeeze` on top 3 candidates
   - Rank by Squeeze Score

3. **Hunt Report** → [synthesis/output-format.md](synthesis/output-format.md)
   - Summary table of all candidates screened
   - Detailed analysis of top 3
   - Watchlist recommendations

---

## Parallel Execution Guide

### scan-squeeze parallel groups

**Group 1 (parallel):**
- Positioning scan (`token_current_top_holders` mode=perps)
- CEX flows (`token_recent_flows_summary`)
- Spot smart money (`token_current_top_holders` mode=spot, labelType=smart_money)
- Recent perp trades (`smart_traders_and_funds_perp_trades`)

**Group 2 (after Group 1):**
- Liquidation map (needs positioning data)
- Macro context synthesis (needs flow + positioning data)

**Group 3 (after Group 2):**
- Squeeze Score calculation
- Report generation

### hunt-squeezes parallel groups

**Group 1:**
- Pull `smart_traders_and_funds_perp_trades` (broad scan)

**Group 2 (after filtering):**
- Run `scan-squeeze` on top 3 candidates in parallel

---

## Tool Inventory

| Step | Tool | Parameters |
|------|------|------------|
| Positioning Scan | `mcp__nansen__token_current_top_holders` | `tokenId`, `mode: "perps"`, `labelType: "smart_money"` |
| Spot Comparison | `mcp__nansen__token_current_top_holders` | `tokenId`, `mode: "spot"`, `labelType: "smart_money"` |
| Recent Trades | `mcp__nansen__smart_traders_and_funds_perp_trades` | `tokenId` or broad scan |
| CEX Flows | `mcp__nansen__token_recent_flows_summary` | `tokenId` |
| Exchange Flows | `mcp__nansen__token_flows` | `tokenId` |
| Who Bought/Sold | `mcp__nansen__token_who_bought_sold` | `tokenId` |
| Technical Data | `python3 src/analysis/indicators.py report [TOKEN]` | CLI |
| BTC Context | `python3 src/analysis/indicators.py report BTC` | CLI |

---

## Secondary Use Cases

Beyond pure squeeze plays, HL perps positioning data enables:

### 1. Contrarian Fade After Squeeze
Once cascade fuel is exhausted, fade back the other direction. The "where to short after a short squeeze" (or vice versa) analysis. Fuel gaps in the liquidation map show where momentum dies.

### 2. Crowded Trade Warning
Flag when positioning gets extreme on tokens you already hold. If you're long ETH and smart money perps go 10:1 long, that's a risk management signal — your trade is crowded.

### 3. Breakout Validation
"Does smart money perps positioning agree with this breakout?" If a token breaks resistance and perps are heavily short, the squeeze adds mechanical fuel to the breakout.

### 4. Entry Timing Catalyst
If you're already bullish on a token from on-chain/TA analysis and perps are heavily short, the squeeze provides a timing catalyst. The thesis is already valid — perps give you the "when."

### 5. Liquidation-Based S/R Levels
Clusters of liquidations act as price magnets. Use them for:
- Stop placement (below/above liquidation clusters)
- Target placement (at liquidation exhaustion points)
- Support/resistance in general analysis

---

## Key Thresholds

| Metric | Threshold | Interpretation |
|--------|-----------|----------------|
| Imbalance Ratio | 3:1+ | Significant — worth investigating |
| Imbalance Ratio | 5:1+ | Extreme — squeeze setup forming |
| Imbalance Ratio | 10:1+ | Critical — squeeze likely with any catalyst |
| First Liquidation | <5% from price | Imminent trigger |
| First Liquidation | 5-10% from price | Catalyst needed |
| First Liquidation | >10% from price | Distant — watchlist only |
| Cascade Cluster | $10M+ forced pressure | High impact squeeze |
| Cascade Cluster | $5M+ forced pressure | Moderate impact |
| Squeeze Score | 8-10 | Alpha — high conviction |
| Squeeze Score | 6-7 | Strong — consider entry |
| Squeeze Score | 4-5 | Moderate — watchlist |
| Squeeze Score | 0-3 | Weak — no setup |

---

## Examples

- [ETH Short Squeeze — 2026-03-04](examples/ETH_2026-03-04_squeeze.md) — 61:1 imbalance, $23.7M cascade, Score 8/10

---

## Persona

Same Titan persona applies:
- **Verdict first** — "Squeeze Score: 8/10 Alpha" before the breakdown
- **Quantify everything** — Dollar amounts, ratios, percentages, distances
- **Contrarian lens** — The crowd is always wrong at extremes
- **No hedging** — "Squeeze likely" or "No setup" — never "might squeeze"
- **Mechanical framing** — This is math, not opinion. Liquidations are forced, not discretionary
