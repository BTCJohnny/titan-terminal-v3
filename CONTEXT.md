# Titan Terminal v3 — Pipeline Router

Route user intent to the correct pipeline. Read the pipeline's own CONTEXT.md for stage details.

## Pipelines

| Command | Pipeline | What it does |
|---------|----------|-------------|
| `/find-setups` | `pipelines/find-setups/` | **Primary daily workflow.** Universe → regime → scan → filter → analyze → setup cards. |
| `/analyze [TOKEN]` | `pipelines/token-analysis/` | Deep dive on one token. 5 pillars: identity, TA, on-chain, derivatives, verdict. |
| `/review` | `pipelines/review/` | Learning loop. Match closed trades to run archives, diagnose failures, propose _config improvements. |
| `/nansen-exit [TOKEN]` | `pipelines/exit-check/` | Quick check: is smart money exiting a token you hold? 4 Nansen credits. |
| `/scan [SYMBOL]` | `pipelines/backtest/` | 4-phase strategy discovery against historical data. |
| `/ta [TOKEN]` | `pipelines/token-analysis/` | TA only — delegates to ta-analyst subagent. |
| `/liquidity [TOKEN]` | `pipelines/token-analysis/04_derivatives/` | Quick derivatives check — liquidations, max pain, L/S, funding. |
| `/portfolio` | (operational) | Paper trading: status, tick, positions, performance. No pipeline — direct CLI. |

## Shared Resources

| Resource | Path | Used by |
|----------|------|---------|
| Active thesis | `_config/thesis.md` | find-setups (01, 03, 05), token-analysis (05), review (02) |
| Signal hierarchy | `_config/signal-hierarchy.md` | token-analysis (05), find-setups (05) |
| Position sizing | `_config/position-sizing.md` | find-setups (05), token-analysis (05) |
| Red flags | `_config/red-flags.md` | find-setups (03) |
| Universe | `_config/universe.md` | find-setups (02) |
| Interpreters | `_config/interpreters/` | token-analysis (03, 04), find-setups (01, 02) |
| Playbooks | `_config/playbooks/` | Various stages as needed |
| Examples | `_config/examples/` | token-analysis (05), find-setups (05) |

## Routing Rules

- If the user says "start session" or "morning briefing" → `/find-setups`
- If the user names a specific token for analysis → `/analyze [TOKEN]`
- If the user asks about exit risk on a held position → `/nansen-exit [TOKEN]`
- If the user asks about backtesting or strategy discovery → `/scan`
- If the user asks about portfolio or paper trading → `/portfolio` (direct CLI, no pipeline)
- If the user asks to review past trades or improve the system → `/review`
- If ambiguous, ask: "Are you looking for new setups across the market, or a deep dive on a specific token?"
