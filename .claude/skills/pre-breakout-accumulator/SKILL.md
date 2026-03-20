# Description: Detects pre-breakout accumulation patterns — entity loading, exchange outflows, volume ups — before price moves.
# Version: 2.1

name: pre-breakout-accumulator
version: 2.1
description: >
  Detects classic pre-breakout accumulation patterns using on-chain data.
  Two modes: analyze a specific token for accumulation signals, or scan the market
  top-down to find tokens matching the pattern. Based on the ZRO insider-buy and
  SOL entity-loading case studies.

commands:
  - analyze-token: "Run full pre-breakout analysis on a specific token"
  - hunt-setups: "Top-down scan for tokens matching accumulation patterns"

---

## Overview

Pre-breakout accumulation is the quiet phase before a price move where informed participants
(insiders, market makers, funds) load positions while retail is distracted or fearful.

**The core thesis:** When entities with information advantages accumulate at range lows
while volume dries up, the supply squeeze creates conditions for a sharp markup phase.

**What makes this different from the Trade Card:**
- Trade Cards answer "buy or avoid?" for any token right now
- This skill hunts for a **specific pattern** — the quiet loading phase that precedes breakouts
- It uses **entity-level tracking** (individual fund positions over time) not just aggregate flows
- It produces an **Alpha Score** (0-12) measuring pattern strength

---

## Slash Commands

- `/hunt-accumulation` — Run the hunt-setups workflow with DB logging + derivatives overlay
- `/analyze-accumulation [TOKEN]` — Run the analyze-token workflow with full report

## Commands

### `analyze-token [TOKEN]`

Deep dive on a specific token to check for pre-breakout accumulation signals.

**Workflow:**
1. Resolve token identity (chain, address) → [research/token-lookup.md](research/token-lookup.md)
2. Get price history to identify range and positioning → [research/price-positioning.md](research/price-positioning.md)
3. Track entity positions over time → [research/entity-tracking.md](research/entity-tracking.md)
4. Check exchange flows for supply squeeze → [research/exchange-flows.md](research/exchange-flows.md)
5. Analyze volume for dry-up pattern → [research/volume-analysis.md](research/volume-analysis.md)
6. Check top 100 holder accumulation → [research/holder-analysis.md](research/holder-analysis.md)
7. Calculate Alpha Score → [synthesis/alpha-score.md](synthesis/alpha-score.md)
8. Generate report → [synthesis/output-format.md](synthesis/output-format.md)

### `hunt-setups`

Top-down market scan to find tokens matching accumulation patterns.

**Workflow:**
1. Screen candidates via token discovery → [research/candidate-screening.md](research/candidate-screening.md)
2. Quick-filter each candidate for key signals (entity loading + price at range low)
3. Score survivors with full Alpha Score
4. Branch on hit count:
   - 0 hits → "No setups today. Market too quiet."
   - 1-3 hits → Deep dive each with `analyze-token`
   - 4+ hits → Rank top 3 by Alpha Score, summarize, ask for deep dives
5. Output results table

---

## Parallel Execution Guide

For `analyze-token`, steps 2-6 are **independent** after token lookup:

```
Step 1: Token Lookup (must complete first)
    │
    ├── Step 2: Price History + Positioning   (parallel)
    ├── Step 3: Entity Tracking               (parallel — multiple entity queries)
    ├── Step 4: Exchange Flows                 (parallel)
    ├── Step 5: Volume Analysis               (parallel — uses price history data)
    └── Step 6: Top 100 Holders               (parallel)
    │
Step 7: Alpha Score (uses all data)
Step 8: Report Generation
```

For `hunt-setups`, Step 1 runs first, then each candidate can be evaluated in parallel.

---

## Tool Inventory

### MCP Tools
| Tool | Step | Purpose |
|------|------|---------|
| `mcp__nansen__general_search` | 1 | Resolve token chain + contract address |
| `mcp__nansen__token_ohlcv` | 2 | Price history for range/low identification |
| `mcp__nansen__address_historical_balances` | 3 | Track entity positions over time (use `entity_id`) |
| `mcp__nansen__smart_traders_and_funds_token_balances` | 3 | Broad smart money positioning |
| `mcp__nansen__token_recent_flows_summary` | 4 | Exchange flow data by segment |
| `mcp__nansen__token_current_top_holders` | 6 | Top 100 holder analysis |
| `mcp__nansen__token_discovery_screener` | hunt | Candidate screening for hunt-setups |

### Python CLI
| Command | Step | Purpose |
|---------|------|---------|
| `python3 src/analysis/indicators.py download [TOKEN] --timeframe 1d --force` | 2 | Download daily OHLCV |
| `python3 src/analysis/indicators.py analyze [TOKEN] --indicators obv,atr` | 5 | Volume and volatility data |
| `python3 src/fetchers/coinglass_fetcher.py --token [TOKEN] --derivatives --json` | Derivatives | Funding rate, OI, L/S ratio confirmation |
| `python3 src/storage/intelligence.py store-hunt --date [DATE] --data '[JSON]'` | DB | Log hunt results |
| `python3 src/storage/intelligence.py store-entities --token [TOKEN] --date [DATE] --data '[JSON]'` | DB | Log entity snapshots |
| `python3 src/storage/intelligence.py store-exchange-balance --token [TOKEN] --data '[JSON]'` | DB | Log exchange balance data |
| `python3 src/storage/intelligence.py exchange-trend [TOKEN]` | DB | Query stored exchange balance trends |
| `python3 src/storage/intelligence.py entity-diff [TOKEN]` | DB | Compare entity positions vs stored snapshot |
| `python3 src/storage/intelligence.py entity-history [TOKEN]` | DB | View entity position history |
| `python3 src/storage/intelligence.py hunt-history` | DB | View past hunt results |

---

## Pattern Library

Three recognized accumulation patterns. See [synthesis/patterns.md](synthesis/patterns.md) for full details.

| Pattern | Key Signal | Example |
|---------|-----------|---------|
| **Classic Accumulation** | Price in tight range + volume declining + entity loading | ZRO (v1.0) |
| **Smart Money Divergence** | Price flat/down while entity balances increase | SOL (v1.1) |
| **Volume Dry-Up** | Post-decline volume collapse + price stabilization | Common pre-breakout |

---

## Key Entities to Track

These funds/market makers showed predictive accumulation patterns in backtests:

| Entity | Type | Signal Characteristics |
|--------|------|----------------------|
| **Wintermute** | Market Maker | High signal — trades ranges aggressively, 3x position on SOL |
| **Jump Trading** | Prop Firm | Steadier accumulation, longer holds |
| **Paradigm Fund** | VC | Longer timeframe signals |
| **a16z** | VC | Early-stage accumulation |
| **Polychain Capital** | VC | Mid/large cap focus |

**Key insight from ZRO:** The highest-alpha signal was an **unlabeled insider** (CEO Bryan Pellegrino), not Nansen's labeled smart money. Always check founder/team wallets — they have better information than any fund.

---

## Alpha Score Quick Reference

### Standard Scale (/12)
| Score | Rating | Action |
|-------|--------|--------|
| 0-4 | Weak | Pass — insufficient signals |
| 5-7 | Moderate | Watchlist only — monitor for strengthening |
| 8-10 | Strong | Consider entry — strong pattern |
| 11-12 | Alpha | High conviction — full position |

### Adjusted Scale (/10, for native tokens)
When exchange flow data is unavailable (native tokens like SOL, ETH on L1, BTC):
| Score | Rating | Action |
|-------|--------|--------|
| 0-3 | Weak | Pass |
| 4-6 | Moderate | Watchlist only |
| 7-8 | Strong | Consider entry |
| 9-10 | Alpha | High conviction |

Full scoring methodology: [synthesis/alpha-score.md](synthesis/alpha-score.md)

---

## Examples

See completed analyses:
- [ZRO — Insider Buy + Exchange Outflows (7.5/10)](examples/ZRO_breakout.md)
- [SOL — Entity Loading + Volume Dry-Up (8/12)](examples/SOL_accumulation.md)

---

## Persona

Same as all Titan skills: contrarian, data-driven, no vibes.
- If the accumulation signals aren't there, say "No setup. Pass."
- If entities are loading but price is extended, say "Too late. Wait for pullback."
- Quantify everything — dollar amounts, percentage changes, timeframes.
- The Alpha Score is the verdict. Don't override it with narrative.
