# Session Handoff — Titan Terminal v3 Migration

## What to read first

Read the v3 architecture spec — it contains every decision and the full design:
`/Users/johnny_main/Developer/projects/titan-terminal-v2/V3-ARCHITECTURE-SPEC.md`

## What was completed this session

We migrated Titan Terminal from v2 (monolithic commands + skills) to v3 (ICM pipeline architecture) on the `v3-architecture` branch. All work is committed across ~8 commits:

1. **Scaffolded the full folder structure** — `pipelines/`, `_config/`, `runs/`, `trading/`
2. **Migrated _config/** — copied reference material from `reference/` and skill examples from `.claude/skills/` into the new `_config/` structure
3. **Wrote CLAUDE.md** (slimmed from 250→120 lines) + **root CONTEXT.md** (pipeline router)
4. **Wrote all 24 pipeline CONTEXT.md stage contracts:**
   - `find-setups/` (5 stages) — primary daily scan workflow
   - `token-analysis/` (5 stages) — deep dive engine
   - `review/` (3 stages) — learning loop
   - `exit-check/` (2 stages) — smart money exit signal
   - `backtest/` (4 stages) — strategy discovery
5. **Rewrote 16 commands as 8 thin routers** pointing to pipelines (v2 commands backed up to `.claude/commands-v2-backup/`)
6. **Removed `.claude/skills/`** (backed up to `.claude/skills-v2-backup/`)
7. **Migrated `my-trading/` → `trading/`** (originals preserved)
8. **Wrote the 5 remaining _config/ reference files:** `universe.md`, `signal-hierarchy.md`, `position-sizing.md`, `red-flags.md`, `nansen-budget.md`
9. **Expanded the backtest scenario library** from 24→58 scenarios across 9 categories (A-I), widened parameter sweep from 3→5 steps
10. **Ran backtests on BTC + ETH** (4h + 1h). Key findings:
    - E9 OI Surge (ETH 1h) — best candidate, PF 2.06→2.30 in walk-forward
    - E7 OI Surge + BB Squeeze (ETH 1h) — PF 2.48, zero degradation
    - G2 Momentum Continuation Long (ETH 1h) — only new-library graduation
    - G12 failed walk-forward on BTC despite dominating Phase 3 (recency bias)
    - BTC 4h is short-dominant, ETH shows bidirectional edge
    - Phase 4 top-5 bottleneck identified — should validate top 10 or require P3 train PF >1.5
11. **Tested `/ta BTC`** — works perfectly on the v3 pipeline routing

## What is running right now

A **full universe backtest** is running in Claude Code. It:
- Fetched top 20 Hyperliquid tokens by OI
- Combined with all ~24 symbols already in the OHLCV database
- Downloaded 4h + 1h data for anything missing
- Is running Phase 2 → 3 → 4 on every symbol, both timeframes
- Will produce a cull analysis identifying which of the 58 scenarios are dead (0 trades across all symbols)

Results will be in `results/backtests/` — look for the newest `phase2_*.json` and `phase4_*.json` files.

## What to do next (in priority order)

1. **Analyze the full universe backtest results** when they complete. Key question: which scenarios had 0 trades across ALL symbols on BOTH timeframes? Those get culled from `src/backtesting/scenarios.py`.

2. **Decide on regime-segmented testing.** Current 180-day window is bear-dominant (Oct 2025→Mar 2026). We discussed extending to 365 days to capture the bull phase (Sep 2024→Oct 2025). Two approaches discussed:
   - Quick version: run a second scan with `--days 365`, compare leaderboards manually
   - Proper version: modify `engine.py` to tag candles with bull/bear regime (SMA 50 vs 200) and split performance metrics
   - Recommendation: do the quick version first, only build the proper version if leaderboard comparison reveals interesting bull/bear splits

3. **Fix the Phase 4 top-5 bottleneck.** G12 dominated Phase 3 on BTC 4h but failed walk-forward, blocking older strategies from being validated. Two proposed fixes: validate top 10 instead of top 5, or require Phase 3 winners to have train-window PF >1.5 before entering Phase 4.

4. **Test `/analyze ETH` on Opus** — full 5-stage token-analysis pipeline. This hasn't been tested yet on v3.

5. **Test `/find-setups`** — the primary daily workflow, end-to-end.

6. **Cleanup:** Delete `my-trading/`, `reference/`, `.claude/commands-v2-backup/`, `.claude/skills-v2-backup/` once testing confirms v3 works.

## Key files to reference

| File | What it is |
|------|-----------|
| `V3-ARCHITECTURE-SPEC.md` | Full design spec — read this first |
| `CLAUDE.md` | Slimmed agent identity (v3) |
| `CONTEXT.md` | Root pipeline router |
| `pipelines/find-setups/CONTEXT.md` | Primary workflow overview |
| `pipelines/token-analysis/CONTEXT.md` | Analysis engine overview |
| `_config/thesis.md` | Active trading thesis + regime |
| `_config/signal-hierarchy.md` | Conflict resolution rules |
| `_config/red-flags.md` | Automatic rejection criteria |
| `src/backtesting/scenarios.py` | 58 scenarios (will be culled based on results) |
| `src/backtesting/scanner.py` | 4-phase scanner engine |
| `results/backtests/` | All backtest results including the running full-universe scan |

## About John

Non-technical crypto trader based in Lisbon. Doesn't write code — uses Claude Code via paste-ready prompts. Thinks strategically. When producing Claude Code prompts: include goal, file paths, input/output expectations, edge cases, validation steps, and git commit message. Flag when Opus is needed vs Sonnet.
