# Titan Terminal v3 — Architecture Specification

> Handoff document for the v3 branch. Contains every architectural decision made during the design session on 2026-03-20. The new chat should read this document first, then proceed to implementation.

**Status:** Design complete. Ready for branch creation and implementation.
**Source paper:** arXiv:2603.16021 — "Interpretable Context Methodology: Folder Structure as Agentic Architecture" (Van Clief & McDermott, 2026)
**Project:** `/Users/johnny_main/Developer/projects/titan-terminal-v2`

---

## What this is

A restructure of Titan Terminal v2 from a Claude Code skills/commands architecture to an ICM-informed pipeline architecture. The goal: find profitable bullish and bearish setups through broad-to-narrow scanning, with a learning loop that improves the system over time.

## What stays the same

- Claude Code as the execution environment (agents, commands, settings)
- Python scripts in `src/` (all computation, data fetching, formatting)
- SQLite databases in `data/`
- Paper trading engine in `src/trading/`
- Git version control
- The 3 Laws (Protect Capital, Seek Asymmetric Upside, Reject the Noise)

## What changes

- **Primary workflow flips from bottom-up to top-down.** Instead of "pick a token, analyze it," the system scans a universe, filters to candidates, then deep-dives survivors.
- **Skills disappear.** Their domain knowledge migrates into pipeline stage CONTEXT.md contracts.
- **Commands shrink from 16 to 8.** Five scan commands merge into `/find-setups`.
- **Every pipeline run saves intermediate artifacts.** Full traceability for post-trade review.
- **A learning loop** (`/review`) traces outcomes back to specific stages and proposes `_config/` improvements.
- **CEX flows join the regime check** to detect tradeable counter-trend bounces inside bear markets.

---

## The 5 architectural principles

1. **Organized by workflow, not by abstraction.** If you want to know how token analysis works, you read one directory top-to-bottom.
2. **Every stage produces a surviving artifact.** No more black-box verdicts. Each pillar's output lives in its own file.
3. **Single source of truth.** Stage contracts live in `pipelines/`. Commands are thin routers (~15 lines). No duplication.
4. **Factory vs product separation.** `_config/` is the factory (stable across runs). `output/` directories are the product (unique per run).
5. **Claude Code compatibility preserved.** `.claude/` stays. Agents, commands, and settings work exactly as before.

---

## ICM 5-layer context hierarchy (adapted)

| Layer | File | Purpose | Token budget |
|-------|------|---------|-------------|
| 0 | `CLAUDE.md` | Agent identity, 3 Laws, personality, output rules | ~800 |
| 1 | `CONTEXT.md` (root) | Pipeline routing — maps user intent to pipeline path | ~300 |
| 2 | `pipelines/*/NN_stage/CONTEXT.md` | Stage contracts: Inputs / Process / Outputs | 200-500 |
| 3 | `_config/` | Thesis, interpreters, playbooks, red flags, position sizing | 500-2,000 |
| 4 | `*/output/` and `runs/` | Stage outputs, intermediate files, archived runs | varies |

Each stage's total context: 2,000–5,000 tokens. Current monolithic `/analyze` loads 15,000+ tokens.

---

## Full directory tree

```
titan-terminal-v2/
│
├── CLAUDE.md                          ← LAYER 0: Agent identity (~800 tok)
│                                        3 Laws, personality, position sizing,
│                                        output rules, autonomous refresh logic.
│                                        Slimmed down — no workflow details.
│
├── CONTEXT.md                         ← LAYER 1: Pipeline routing (~300 tok)
│                                        Maps user intent → pipeline path.
│                                        Lists all pipelines + shared resources.
│
├── pipelines/                         ← LAYER 2: All workflows
│   │
│   ├── find-setups/                     PRIMARY PIPELINE — daily driver
│   │   ├── CONTEXT.md                   Master scan: universe → regime → scans → filter → analyze → setup
│   │   │
│   │   ├── 01_regime/                   Market structure check
│   │   │   ├── CONTEXT.md               Inputs: BTC structure, derivatives, ETF, F&G, CEX flows
│   │   │   │                            Process: determine regime + sub-regime
│   │   │   │                            Outputs: regime.md
│   │   │   │                            References: _config/thesis.md, _config/interpreters/
│   │   │   └── output/
│   │   │       └── regime.md            Risk-on / risk-off / chop + sub-regime
│   │   │                                + which setup types are valid today
│   │   │
│   │   ├── 02_scan/                     Parallel scans across universe
│   │   │   ├── CONTEXT.md               Inputs: 01_regime/output/regime.md, _config/universe.md
│   │   │   │                            Process: 4 parallel sub-scans
│   │   │   │                            Outputs: ta_hits.md, deriv_hits.md, onchain_hits.md, squeeze_hits.md
│   │   │   │                            Scripts: indicators.py, coinglass_fetcher.py, hyperliquid_fetcher.py,
│   │   │   │                                     cex_monitor.py, signal_checker.py
│   │   │   └── output/
│   │   │       ├── ta_hits.md           Tokens with TA signal clusters
│   │   │       ├── deriv_hits.md        Extreme funding, OI divergence, crowded positioning
│   │   │       ├── onchain_hits.md      Smart money movement, exchange flow spikes
│   │   │       └── squeeze_hits.md      Imbalance ratios 5:1+
│   │   │
│   │   ├── 03_filter/                   Apply red flags + regime fit + rank
│   │   │   ├── CONTEXT.md               Inputs: all 02 outputs + _config/red-flags.md + 01 regime
│   │   │   │                            Process: reject, rank, select top 0-3
│   │   │   │                            Outputs: candidates.md
│   │   │   └── output/
│   │   │       └── candidates.md        0-3 tokens ranked. Or "No setups today — here's why"
│   │   │
│   │   ├── 04_analyze/                  Deep dive per candidate
│   │   │   ├── CONTEXT.md               For each candidate: run token-analysis pipeline
│   │   │   └── output/                  One subfolder per candidate token
│   │   │       └── [TOKEN]/             Contains all token-analysis stage outputs
│   │   │
│   │   └── 05_setup/                    Generate actionable trade cards
│   │       ├── CONTEXT.md               Entry, stop, targets, position size, R:R
│   │       │                            References: _config/position-sizing.md, _config/thesis.md
│   │       └── output/
│   │           └── setups.md            Final actionable setups — or confirmed "nothing today"
│   │
│   ├── token-analysis/                  DEEP ANALYSIS PIPELINE (called by find-setups/04 or /analyze)
│   │   ├── CONTEXT.md                   Pipeline overview: stage map, parallel execution,
│   │   │                                signal hierarchy, review mode
│   │   │
│   │   ├── 01_resolve/                  Token identity + market snapshot
│   │   │   ├── CONTEXT.md               Inputs: token symbol
│   │   │   │                            Process: Nansen search + CoinStats
│   │   │   │                            Outputs: identity.md
│   │   │   └── output/
│   │   │       └── identity.md
│   │   │
│   │   ├── 02_technical/                Multi-timeframe TA (parallel)
│   │   │   ├── CONTEXT.md               Inputs: identity.md
│   │   │   │                            Process: delegate to ta-analyst
│   │   │   │                            Outputs: ta_verdict.md
│   │   │   └── output/
│   │   │       └── ta_verdict.md
│   │   │
│   │   ├── 03_onchain/                  On-chain flows + accumulation (parallel)
│   │   │   ├── CONTEXT.md               Inputs: identity.md
│   │   │   │                            Process: Nansen flows, holders, scoring
│   │   │   │                            Outputs: flows.md, accumulation.md
│   │   │   │                            References: _config/interpreters/onchain/, _config/thesis.md
│   │   │   └── output/
│   │   │       ├── flows.md
│   │   │       └── accumulation.md
│   │   │
│   │   ├── 04_derivatives/              Derivatives + perps (parallel)
│   │   │   ├── CONTEXT.md               Inputs: identity.md
│   │   │   │                            Process: Coinglass + Nansen perps
│   │   │   │                            Outputs: derivatives.md, perps.md
│   │   │   │                            References: _config/interpreters/derivatives/
│   │   │   └── output/
│   │   │       ├── derivatives.md
│   │   │       └── perps.md
│   │   │
│   │   └── 05_verdict/                  Synthesis + trade card
│   │       ├── CONTEXT.md               Inputs: ALL prior outputs (02-04)
│   │       │                            Process: signal hierarchy, thesis check, format
│   │       │                            Outputs: verdict.md, trade_card.md
│   │       │                            References: _config/thesis.md, signal-hierarchy.md, position-sizing.md
│   │       └── output/
│   │           ├── verdict.md
│   │           └── trade_card.md
│   │
│   ├── review/                          LEARNING PIPELINE — weekly or after N trades close
│   │   ├── CONTEXT.md
│   │   │
│   │   ├── 01_outcomes/                 Pull closed trades, match to run archives
│   │   │   ├── CONTEXT.md               Inputs: analytics.py summary, runs/ archive
│   │   │   └── output/
│   │   │       └── outcomes.md          What the system said vs what happened
│   │   │
│   │   ├── 02_diagnosis/                Trace failures to specific stages
│   │   │   ├── CONTEXT.md               Inputs: outcomes.md + original run artifacts
│   │   │   └── output/
│   │   │       └── diagnosis.md         Root cause per losing trade
│   │   │
│   │   └── 03_propose/                  Propose _config/ improvements
│   │       ├── CONTEXT.md
│   │       └── output/
│   │           └── proposals.md         Concrete diffs. Human reviews before applying.
│   │
│   ├── exit-check/                      MINI-PIPELINE for /nansen-exit (2 stages)
│   │   ├── CONTEXT.md
│   │   ├── 01_signals/
│   │   │   ├── CONTEXT.md
│   │   │   └── output/
│   │   └── 02_verdict/
│   │       ├── CONTEXT.md
│   │       └── output/
│   │
│   └── backtest/                        BACKTESTING PIPELINE (4-phase, maps to scanner.py)
│       ├── CONTEXT.md
│       ├── 01_signals/
│       │   ├── CONTEXT.md
│       │   └── output/
│       ├── 02_scenarios/
│       │   ├── CONTEXT.md
│       │   └── output/
│       ├── 03_sweep/
│       │   ├── CONTEXT.md
│       │   └── output/
│       └── 04_walkforward/
│           ├── CONTEXT.md
│           └── output/
│
├── _config/                           ← LAYER 3: Stable reference material (the factory)
│   │
│   ├── universe.md                      Scan universe: BTC, ETH + top 30 HL by OI
│   ├── thesis.md                        Active trading framework, regime, bias
│   ├── mission.md                       Trading philosophy, edge definition
│   ├── brain.md                         Operations manual for complex analysis
│   ├── signal-hierarchy.md              On-Chain > Perps > Derivatives > TA + decision rules
│   ├── position-sizing.md               Category limits, risk per trade, min R:R
│   ├── red-flags.md                     Automatic rejection criteria
│   ├── nansen-budget.md                 Credit limits, cost-per-call table
│   │
│   ├── interpreters/                    How to read specific data types
│   │   ├── accumulation-scores.md
│   │   ├── cex-flows.md
│   │   ├── funding-rates.md
│   │   ├── smart-money-moves.md
│   │   └── derivatives-signals.md
│   │
│   ├── playbooks/                       Domain analysis guides
│   │   ├── nansen/
│   │   ├── technical/
│   │   ├── market/
│   │   └── signals/
│   │
│   └── examples/                        Few-shot reference outputs (from old skills/examples/)
│       ├── trade-card-example.md
│       ├── accumulation-example.md
│       └── squeeze-example.md
│
├── src/                               ← PYTHON SCRIPTS (stays at project root)
│   ├── analysis/                        TA indicators
│   ├── data/                            OHLCV fetching + caching
│   ├── fetchers/                        Coinglass, Hyperliquid, signals
│   ├── formatters/                      Trade card, signal card, target package
│   ├── storage/                         SQLite: intelligence, nansen cache
│   ├── backtesting/                     Engine, scanner, scenarios, signals
│   ├── trading/                         Paper engine, analytics
│   └── watchers/                        CEX monitor, watchlist, alert checker
│
├── .claude/                           ← CLAUDE CODE INTERFACE (thin routers)
│   ├── settings.json
│   ├── settings.local.json
│   ├── agents/
│   │   ├── ta-analyst.md                7-Question TA framework (Sonnet)
│   │   ├── wyckoff-analyst.md           Subjective pattern interpretation
│   │   └── signal-validator.md          External signal cross-check
│   └── commands/                        8 COMMANDS (down from 16)
│       ├── find-setups.md               → pipelines/find-setups/ (PRIMARY)
│       ├── analyze.md                   → pipelines/token-analysis/ (ad-hoc deep dive)
│       ├── review.md                    → pipelines/review/ (learning loop)
│       ├── ta.md                        → pipelines/token-analysis/02_technical/ only
│       ├── liquidity.md                 → pipelines/token-analysis/04_derivatives/
│       ├── nansen-exit.md               → pipelines/exit-check/
│       ├── portfolio.md                 Paper trading: status, tick, positions, performance
│       └── scan.md                      → pipelines/backtest/ (4-phase discovery)
│
├── runs/                              ← LAYER 4: Archived pipeline outputs
│   ├── find-setups/
│   │   └── 2026-03-20/
│   ├── token-analysis/
│   │   └── BTC_2026-03-20_1430/
│   ├── review/
│   │   └── 2026-03-20/
│   └── session/ (legacy, from v2 runs)
│
├── trading/                           ← PORTFOLIO + JOURNAL
│   ├── portfolio.md
│   ├── alerts.md
│   └── journal/
│       └── 2026_Q1.md
│
├── data/                              ← DATABASES
│   ├── titan_data.db
│   ├── titan_intelligence.db
│   └── ohlcv_cache.db
│
├── signals/dashboards/                ← CRON SNAPSHOTS
├── config/                            ← APP CONFIG (token_list.json, wallets.json)
├── tests/                             ← SMOKE TESTS
├── scripts/                           ← UTILITY SCRIPTS
│
├── V3-ARCHITECTURE-SPEC.md            ← THIS FILE
├── BUILD-TRACKER.md
├── README.md
├── requirements.txt
├── .env / .env.example / .gitignore
```

---

## Key decisions log

### Paper trading engine: KEEP
The paper engine is the data layer for the learning loop. `/review` reads outcome data from paper_positions to trace what happened. Without it, there's nothing to learn from. Access consolidated into one `/portfolio` command (status, tick, positions, performance).

### Python code location: STAYS IN `src/`
Scripts are shared across multiple pipelines (indicators.py used by token-analysis, find-setups, and backtest). Moving them into pipeline folders would break imports and duplicate code. Stage CONTEXT.md files reference scripts by full path.

### Commands: 16 → 8
**Cut (absorbed into `/find-setups` stages):** `/start-session`, `/market-check`, `/hunt-accumulation`, `/hunt-squeezes`, `/check-signals`, `/analyze-accumulation`, `/target-package`, `/scan-wyckoff`

**Keep:** `/find-setups` (primary), `/analyze` (ad-hoc), `/review` (learning), `/ta` (quick), `/liquidity` (quick), `/nansen-exit` (quick), `/portfolio` (operational), `/scan` (advanced)

### Skills: REMOVE all 4, migrate to pipeline stages
- `titan-trade-card/` → `pipelines/token-analysis/` stages
- `pre-breakout-accumulator/` → `pipelines/find-setups/02_scan/` (on-chain sub-scan)
- `perps-squeeze-detector/` → `pipelines/find-setups/02_scan/` (squeeze sub-scan)
- `nansen-exit-signal/` → `pipelines/exit-check/`
- `examples/` from skills → `_config/examples/`

### CEX flows: YES, included in regime check
CEX flows discriminate between three bear-market sub-regimes:
1. **Distribution phase** (short bias): Inflows on bounces, smart money selling
2. **Counter-trend bounce** (selective longs): Outflows during dips, stablecoin inflows, shorts crowded
3. **Regime transition** (widen long scope): Sustained outflows 2+ weeks, accumulation across 3+ assets

`01_regime/CONTEXT.md` requires CEX data as input alongside derivatives, BTC structure, ETF flows.

### Rich output for Claude Code
Claude Code should use formatted markdown with strategic use of bold, emojis, horizontal rules, and clear section headers. Trade cards and session briefings should be visually scannable. Regime output should clearly label which setup types are valid/invalid today.

---

## Primary workflow: `/find-setups`

```
Universe (BTC, ETH + top 30 HL by OI)
    │
    ▼
01_regime — BTC structure, derivatives, ETF, F&G, CEX flows
    │         Sets bias: risk-on / risk-off / chop + sub-regime
    │         Outputs which setup types are valid today
    ▼
02_scan — 4 parallel sub-scans across universe
    │       TA signals, derivatives, on-chain (top 20), squeezes
    ▼
03_filter — Apply red flags, min liquidity, regime fit
    │         Rank by conviction → 0-3 candidates
    │         "No setups today" is a valid and expected outcome
    ▼
04_analyze — Deep dive per candidate (runs token-analysis pipeline)
    │
    ▼
05_setup — Entry, stop, targets, size, R:R
    │         Final actionable setups or confirmed "nothing today"
    ▼
runs/ — Full archive for traceability
```

### Critical design note
"No setups today" is a first-class outcome. The system should NOT always find something. If nothing passes the filter, say so with the market context and what would need to change.

---

## Learning loop: `/review`

```
01_outcomes — Pull closed paper trades, match to runs/ archives
02_diagnosis — Trace failures back to specific pipeline stages
03_propose — Propose concrete _config/ file updates
    │
    ▼
Human reviews proposals → applies or rejects → Git commit
```

What gets improved over time:
- `_config/interpreters/` — tighter thresholds after false positives
- `_config/red-flags.md` — grows as new failure patterns emerge
- `_config/signal-hierarchy.md` — weight adjustments based on outcome data
- `_config/thesis.md` — regime signals validated or corrected

---

## Stage CONTEXT.md template

Every stage contract follows this format:

```markdown
# Stage: [Name]

## Purpose
[One sentence: what this stage does and why]

## Inputs
| Source | File | Layer |
|--------|------|-------|
| Previous stage | ../01_resolve/output/identity.md | 4 (working) |
| Reference | _config/thesis.md | 3 (factory) |
| Reference | _config/interpreters/onchain/ | 3 (factory) |

## Process
[Step-by-step instructions for the agent]
[Include interpretation rules, decision criteria]
[Reference specific scripts by full path]

## Scripts used
- `src/fetchers/coinglass_fetcher.py --token [TOKEN] --derivatives --json`
- `src/analysis/indicators.py analyze [TOKEN] --timeframe 4h`

## Outputs
| File | Contents |
|------|----------|
| output/flows.md | Exchange flows, smart money, interpretation |
| output/accumulation.md | 5-signal score table + label |

## Review gate
[What should the human check before proceeding?]
[What would cause a re-run or edit?]
```

---

## Migration plan

### Step 1: Create v3 branch
```bash
cd /Users/johnny_main/Developer/projects/titan-terminal-v2
git checkout -b v3-architecture
```

### Step 2: Create folder structure
Create all `pipelines/`, `_config/`, `runs/`, `trading/` directories with empty CONTEXT.md files.

### Step 3: Migrate `_config/`
Move reference material:
- `reference/titan-thesis.md` → `_config/thesis.md`
- `reference/titan-mission.md` → `_config/mission.md`
- `reference/titan-brain.md` → `_config/brain.md`
- `reference/interpreters/` → `_config/interpreters/`
- `reference/playbooks/` → `_config/playbooks/`
Create new files: `universe.md`, `signal-hierarchy.md`, `position-sizing.md`, `red-flags.md`, `nansen-budget.md`, `derivatives-signals.md`

### Step 4: Write pipeline CONTEXT.md files
Start with `find-setups/` (primary pipeline), then `token-analysis/`, then `review/`.
Each stage CONTEXT.md extracts logic from the old command/skill files.

### Step 5: Rewrite commands as thin routers
Replace 300-line commands with 15-line routers that point to pipelines.

### Step 6: Remove `.claude/skills/`
After all skill knowledge is migrated to pipeline stages.

### Step 7: Slim down CLAUDE.md
Move position sizing, signal hierarchy, and Nansen budget to `_config/` files.
CLAUDE.md keeps only: identity, 3 Laws, personality, output format rules, autonomous refresh.

### Step 8: Update `my-trading/` → `trading/`
Rename and update any internal references.

### Step 9: Test
Run `/find-setups` end-to-end. Verify intermediate outputs survive. Verify `/analyze TOKEN` still works standalone.

### Step 10: Git commit
Commit v3 branch. Keep v2 main branch intact.

---

## Context for the implementor

- **John is non-technical.** He doesn't write code. Claude Code prompts should be complete and paste-ready.
- **Python scripts are NOT modified in this restructure.** Only the orchestration layer changes (folders, CONTEXT.md files, commands).
- **The v2 branch must remain fully functional.** All work happens on the v3 branch.
- **Rich output matters.** Claude Code should produce visually scannable markdown with bold metrics, emojis for status, and clear section headers.
- **"Nothing today" is success.** The system should not force-find setups. Quality over quantity.
