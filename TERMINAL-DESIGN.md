# Titan Terminal v2 — Rework Design Doc

**Created:** 2026-03-24
**Status:** Design complete, build starting

---

## What Is Titan Terminal?

An intelligence terminal that answers: **"What's interesting right now and why?"**

It does NOT trade. It does NOT backtest. It surfaces opportunities using Nansen + Coinglass + Hyperliquid data, with Claude Code (Opus) reasoning through the alpha and displaying results in a dashboard artifact.

When something looks interesting, John takes those insights to his exchange or to Titan Trader for execution.

---

## Two Projects, Two Purposes

| Project | Purpose | Location | Repo |
|---------|---------|----------|------|
| **Titan Trader** | Autotrading system (pipelines, paper engine, backtesting, cron) | `/Users/johnny_main/Developer/projects/titan-trader` | BTCJohnny/titan-trader (private) |
| **Titan Terminal v2** | Intelligence terminal (alpha surfacing, reasoning, dashboard) | `/Users/johnny_main/Developer/projects/titan-terminal-v2` | BTCJohnny/titan-terminal-v2 |

---

## 3 Commands

### `/hunt` — Daily Driver
"What's interesting right now?"

1. Pull ALL data sources in parallel:
   - Nansen smart money flows + whale activity (MCP)
   - Coinglass derivatives scan (all coins) + market pulse (BTC/ETH macro)
   - Hyperliquid perps positioning
   - BTC regime check via indicators.py (weekly + daily structure)
   - CEX flows snapshot (cex_monitor.py or latest cached)
2. Claude reads thesis, applies signal hierarchy, reasons through everything
3. Output: **dashboard artifact** in Claude.ai showing:
   - Market regime bar (risk-on/off/chop, F&G, BTC trend, ETF flows, Coinbase premium, CEX flow summary)
   - 0-5 opportunity cards ranked by conviction
   - Claude's reasoning visible per card

### `/analyze [TOKEN]` — Deep Dive
"Tell me everything about this one."

- Full TA across W/D/4H/1H (7-Question framework, 8 indicators)
- Nansen on-chain flows + smart money positioning
- Coinglass derivatives deep dive (funding, OI, L/S, liquidations)
- CEX flows for this token via Nansen `token_recent_flows_summary`
- Synthesize verdict using signal hierarchy
- Output: detailed analysis with directional call

### `/targets [TOKEN] [direction] [entry] [stop]` — Position Sizing
"How do I play this?"

- S/R analysis via indicators.py
- Key levels for both long and short bids
- Target package with T1/T2/T3
- Position sizing based on portfolio amount + 2% risk rule
- Uses existing target_package.py formatter

---

## What We Keep

### Python Tools
| File | Why |
|------|-----|
| `src/analysis/indicators.py` | TA on demand — S/R, market structure, 7-Question framework |
| `src/data/ohlcv_client.py` | OHLCV cache — avoid re-fetching price data |
| `src/fetchers/coinglass_fetcher.py` | 11 Coinglass endpoints — derivatives intelligence |
| `src/fetchers/hyperliquid_fetcher.py` | Perps positioning data |
| `src/fetchers/binance_fetcher.py` | OHLCV fallback source via CCXT |
| `src/formatters/target_package.py` | Position sizing calculator |
| `src/formatters/portfolio_sync.py` | Lightweight portfolio context for regime |
| `src/storage/nansen_cache.py` | Saves Nansen credits via TTL caching |
| `src/watchers/cex_monitor.py` | CEX flow snapshots (BTC/ETH/USDT/USDC) |

### Storage / Databases
| What | Why |
|------|-----|
| `data/titan_data.db` | OHLCV price cache |
| `data/ohlcv_cache.db` | Fast OHLCV lookup |
| `data/titan_intelligence.db` | Keep `derivatives_snapshots` table (historical derivatives data for reasoning). Strip trade execution tables. |
| `signals/dashboards/` | CEX snapshots + Coinglass reports (keep generating these) |
| Nansen cache (in nansen_cache.py) | Credit-saving response cache with TTLs |

### Config / Reference
| File | Why |
|------|-----|
| `_config/thesis.md` | Active trading framework — the lens Claude reasons through |
| `_config/signal-hierarchy.md` | Conflict resolution rules |
| `_config/universe.md` | Scan universe definition |
| `_config/position-sizing.md` | Category limits + risk rules |
| `_config/red-flags.md` | Rejection criteria |
| `_config/nansen-budget.md` | Credit management |
| `_config/mission.md` | Trading philosophy |
| `_config/brain.md` | Operations manual |
| `_config/interpreters/` | All 5 (accumulation-scores, cex-flows, derivatives-signals, funding-rates, smart-money-moves) |
| `_config/playbooks/nansen/` | Keep — on-chain playbooks |
| `_config/playbooks/signals/` | Keep — signal interpretation |
| `_config/playbooks/market/` | Keep — market regime playbooks |
| `_config/examples/` | Keep — few-shot examples for Claude |

### MCP Servers
- **Nansen** — On-chain flows, smart money, whale activity
- **CoinStats** — Prices, market data, portfolio sync

---

## What We Strip

### Remove entirely
| What | Why |
|------|-----|
| `pipelines/` (all 5 pipelines, 24 stage contracts) | Too rigid for intelligence terminal |
| `src/backtesting/` (signals, engine, scenarios, scanner, signal_checker) | Titan Trader's job |
| `src/trading/` (paper_engine, analytics) | Titan Trader's job |
| `src/watchers/watchlist_monitor.py` | Titan Trader's job |
| `src/watchers/alert_checker.py` | Titan Trader's job |
| `src/fetchers/signals_fetcher.py` | MarketInsights signals = Titan Trader's domain |
| `src/formatters/trade_card.py` | Replaced by dashboard opportunity cards |
| `src/formatters/signal_card.py` | No longer needed |
| `.claude/agents/` (all 3 subagents) | One brain — Opus handles everything |
| `.claude/commands-v2-backup/` | Old v2 commands, no longer needed |
| `.claude/skills-v2-backup/` | Old v2 skills, no longer needed |
| `my-trading/` | Duplicate of `trading/` (was pending cleanup) |
| `reference/` | Duplicate of `_config/` (was pending cleanup) |
| `_config/playbooks/technical/` | TA playbooks less relevant for intelligence terminal |
| `runs/` contents | Fresh start (keep the directory structure) |
| `results/trade-cards/` | Titan Trader's output |
| `results/backtests/` | Titan Trader's output |
| `results/skill-runs/` | Old v2 output |
| `V3-ARCHITECTURE-SPEC.md` | Historical — lives in Titan Trader now |
| `BUILD-TRACKER.md` | Historical — lives in Titan Trader now |
| `SESSION-HANDOFF.md` | Historical — lives in Titan Trader now |
| `scripts/cron_paper_engine.sh` | Titan Trader's cron |

### Modify
| What | Change |
|------|--------|
| `src/storage/intelligence.py` | Keep `derivatives_snapshots` table + any general tables. Strip `trade_setups`, `paper_positions`, `paper_portfolio`, `equity_snapshots` tables. |
| `CLAUDE.md` | Rewrite for terminal identity (not trader) |
| `CONTEXT.md` | Rewrite — no pipeline routing, just 3 commands |
| `README.md` | Rewrite for terminal |
| `.claude/commands/` | Replace 8 commands with 3: hunt, analyze, targets |
| `.claude/settings.json` | Simplify — remove subagent references |

---

## Dashboard Design

React artifact rendered in Claude.ai (not a hosted app).

### Layout

**Top: Market Regime Bar**
- Regime label: Risk-On / Risk-Off / Chop
- F&G index with color
- BTC trend (above/below SMA 50/200)
- ETF flow direction (inflow/outflow + magnitude)
- Coinbase premium (+/-)
- CEX flows summary: BTC + ETH + stablecoins with multiplier + direction arrows
- Delta vs prior (trend arrows showing if flows are accelerating or decelerating)

**Middle: Opportunity Cards (0-5)**
Each card shows:
- Token name + current price + 24h change
- Direction: LONG or SHORT
- Conviction: High / Medium / Low (visual indicator)
- Alpha thesis: 2-3 sentences of WHY (Claude's actual reasoning)
- Key data points: specific evidence with numbers
  - On-chain: exchange flows (direction + multiplier), smart money positioning
  - Derivatives: funding rate, OI trend, L/S ratio, liquidation clusters
  - TA context: regime alignment, key S/R levels
- Signal alignment: visual showing which pillars agree/disagree
- "Analyze deeper" action

**Bottom: Meta**
- Nansen credits used this scan
- Data freshness timestamps per source
- Current thesis regime from `_config/thesis.md`

---

## Opus Reasoning Framework

### How Claude determines opportunity cards:

**Layer 1: Regime** — BTC structure, F&G, ETF flows, Coinbase premium, CEX stablecoin flows → determines valid trade directions

**Layer 2: Scan for anomalies** — sweep universe for divergences between crowd behavior and smart money:
- Nansen: 2+ funds accumulating >$20M? Smart money selling into a rally? Exchange flows >3x average?
- Coinglass: Extreme funding? OI divergence from price? Crowded L/S >5:1? Liquidation clusters <5% away?
- CEX flows: Individual token exchange flows via Nansen `token_recent_flows_summary` for tokens that pass initial screen

**Layer 3: Convergence** — multiple independent signal types pointing same direction:
- Strong: on-chain + derivatives + TA aligned (3 independent sources)
- Moderate: on-chain + derivatives aligned, TA neutral
- Weak: single source only → does not make the cut

**Layer 4: Conviction scoring** — weight by evidence type:
- Highest: 3+ funds accumulating >$20M
- High: CEX flows >3x average, smart money perps positioning
- Medium-High: Extreme funding + crowded L/S (mechanical)
- Medium: OI divergence, TA signal cluster
- Low: Single fund buying, TA alone

**Minimum bar for an opportunity card:** High conviction across at least 2 different evidence types.

**"Nothing today" is the correct output** when nothing meets the bar.

---

## Cowork Migration Path (Future)

- `/hunt` becomes a scheduled task (morning, every 4-6h)
- Dashboard artifacts persist in Cowork workspace
- Track: which opportunities surfaced → which John acted on → what happened
- Thesis auto-updates based on observed outcomes

---

## Build Steps

| Step | What | Prompt |
|------|------|--------|
| 1 | Strip titan-terminal-v2 down to terminal components | Ready to write |
| 2 | Rewrite CLAUDE.md + CONTEXT.md for terminal identity | Next session |
| 3 | Write 3 commands: /hunt, /analyze, /targets | Next session |
| 4 | Build dashboard artifact template (React) | Next session |
| 5 | Test /hunt end-to-end on Opus | Live test |
| 6 | Iterate dashboard with real data | Ongoing |