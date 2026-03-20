# Titan Terminal v2

Autonomous crypto trading intelligence system. Claude Code is the brain — Python tools are the hands.

## The 3 Laws

1. **Protect Capital** — Prevent losses first
2. **Seek Asymmetric Upside** — 3R minimum (reward ≥ 3x risk)
3. **Reject the Noise** — Data only, no hype/vibes

## Personality

Contrarian, ruthless, concise. Verdict first, then logic. Never hedge language.

---

## Project Structure

```
.claude/agents/       ← Specialist subagents (Claude delegates to these)
.claude/commands/     ← Slash commands (/start-session, /analyze, etc.)
.claude/skills/       ← Domain knowledge (trade card, accumulator, squeeze detector)
reference/            ← Playbooks, interpreters, philosophy (load on demand)
src/analysis/         ← TA indicators (Python math)
src/data/             ← OHLCV fetching and caching
src/fetchers/         ← Signal DB queries, Hyperliquid data, Coinglass derivatives intelligence
src/formatters/       ← Trade card, signal card, target package renderers
src/storage/          ← SQLite intelligence tracking
src/backtesting/       ← Strategy backtesting engine and scanner
src/trading/          ← Paper trading engine and analytics
src/watchers/         ← Cron: CEX flow monitor, watchlist monitor
my-trading/           ← Portfolio, alerts, trading journal
data/                 ← SQLite databases
results/              ← Saved analysis outputs
signals/dashboards/   ← Cron-generated snapshots
config/               ← Token list, wallet config
```

## Key Reference Docs

Read these ONLY when the task requires them:

| Doc | When to read | Path |
|-----|-------------|------|
| Active trading thesis | Session start, before /analyze verdicts | `reference/titan-thesis.md` |
| Trading philosophy | Before any verdict | `reference/titan-mission.md` |
| Operations manual | Complex multi-step analysis | `reference/titan-brain.md` |
| Nansen playbooks | On-chain analysis | `reference/playbooks/nansen/` |
| Technical playbooks | TA analysis | `reference/playbooks/technical/` |
| Market playbooks | Macro overview | `reference/playbooks/market/` |
| Signal validation | External signal check | `reference/playbooks/signals/` |
| CEX flow guide | Interpreting exchange flows | `reference/interpreters/cex-flows.md` |
| Funding rate guide | Interpreting perp funding | `reference/interpreters/funding-rates.md` |
| Smart money guide | Reading fund positioning | `reference/interpreters/smart-money-moves.md` |
| Accumulation scoring | Reading 0-5 scores | `reference/interpreters/accumulation-scores.md` |

---

## CLI Commands

### Technical Analysis
```bash
python3 src/analysis/indicators.py analyze [TOKEN] --timeframe 4h
```

### Data Fetching
```bash
python3 src/data/ohlcv_client.py download [TOKEN] --timeframe 4h
python3 src/data/ohlcv_client.py download [TOKEN] --timeframe 4h --force
python3 src/fetchers/signals_fetcher.py recent --hours 72
python3 src/fetchers/signals_fetcher.py token --token [TOKEN]
python3 src/fetchers/hyperliquid_fetcher.py
```

### Coinglass Derivatives Intelligence
```bash
python3 src/fetchers/coinglass_fetcher.py --token BTC --price 84000                    # Liquidity report (liquidation + options)
python3 src/fetchers/coinglass_fetcher.py --token BTC --derivatives --price 84000      # Full derivatives (funding, OI, L/S + liquidity)
python3 src/fetchers/coinglass_fetcher.py --market                                     # Market pulse (ETF + F&G + premium + BTC/ETH funding+OI+L/S)
python3 src/fetchers/coinglass_fetcher.py --scan                                       # Scan all coins by liquidation
python3 src/fetchers/coinglass_fetcher.py --token BTC --json                           # Raw JSON output
python3 src/fetchers/coinglass_fetcher.py --token BTC --debug                          # Print raw API responses
```

### Monitoring
```bash
python3 src/watchers/cex_monitor.py snapshot
python3 src/watchers/cex_monitor.py alerts
python3 src/watchers/watchlist_monitor.py review
python3 src/watchers/watchlist_monitor.py check [TOKEN]
python3 src/watchers/watchlist_monitor.py summary
python3 src/watchers/alert_checker.py '{"TOKEN": price, ...}'
python3 src/watchers/alert_checker.py --update '{"TOKEN": price, ...}'
```

### Intelligence Database
```bash
python3 src/storage/intelligence.py watchlist
python3 src/storage/intelligence.py watchlist-add --symbol [TOKEN] --type structural --thesis "..."
python3 src/storage/intelligence.py setup-stats
python3 src/storage/intelligence.py list-setups
```

### Derivatives History
```bash
python3 src/storage/intelligence.py derivatives-history --symbol BTC --days 7
python3 src/storage/intelligence.py derivatives-history --days 1           # all tokens, last 24h
python3 src/storage/intelligence.py derivatives-stats --symbol BTC --days 30
python3 src/storage/intelligence.py derivatives-export --symbol BTC --days 90 --output data/btc_90d.csv
```

### Backfill Historical Data
```bash
python3 scripts/backfill_derivatives.py                      # BTC + ETH, 180 days
python3 scripts/backfill_derivatives.py --symbols BTC        # BTC only
python3 scripts/backfill_derivatives.py --days 90            # Last 90 days only
python3 scripts/backfill_derivatives.py --dry-run            # Preview without writing
```

### Testing
```bash
python3 tests/run_smoke.py              # Run all smoke tests
python3 tests/run_smoke.py --verbose    # Show details on failures
python3 tests/run_smoke.py indicators   # Run specific test
```

### Paper Trading
```bash
python3 src/trading/paper_engine.py tick                # Process setups, fill entries/exits
python3 src/trading/paper_engine.py tick --cron         # Cron mode (compact output + saves report)
python3 src/trading/paper_engine.py status              # Current portfolio status
python3 src/trading/paper_engine.py positions            # Open positions
python3 src/trading/paper_engine.py positions --closed   # Closed positions
python3 src/trading/paper_engine.py history              # Recent equity snapshots
python3 src/trading/paper_engine.py history --days 7     # Last 7 days
python3 src/trading/paper_engine.py init                 # Initialize portfolio ($50k)
python3 src/trading/paper_engine.py init --reset         # Reset all paper trading data
```

### Performance Analytics
```bash
python3 src/trading/analytics.py summary                 # Full performance report
python3 src/trading/analytics.py summary --days 30       # Last 30 days
python3 src/trading/analytics.py by-strategy             # Breakdown by setup type
python3 src/trading/analytics.py by-direction            # LONG vs SHORT comparison
python3 src/trading/analytics.py recent-trades           # Recent closed trades
python3 src/trading/analytics.py equity-curve --csv      # Export equity curve
```

### Backtesting
```bash
python3 src/backtesting/engine.py coverage --symbol BTC                    # Data coverage check
python3 src/backtesting/engine.py run --symbol BTC --timeframe 4h --days 180 --strategy '...'  # Single backtest
python3 src/backtesting/scanner.py full --symbol BTC --timeframe 4h --days 180  # Full 4-phase scan
python3 src/backtesting/scanner.py phase1 --symbol BTC --timeframe 4h --days 180  # Individual signals
python3 src/backtesting/scanner.py phase2 --symbol BTC --timeframe 4h --days 180  # Scenario scan
python3 src/backtesting/scanner.py phase3 --symbol BTC --timeframe 4h --days 180  # Parameter sweep
python3 src/backtesting/scanner.py phase4 --symbol BTC --timeframe 4h --days 180  # Walk-forward test
python3 src/backtesting/scenarios.py list                                         # List all scenarios
```

### Strategy Signal Checker
```bash
python3 src/backtesting/signal_checker.py check                # Check graduated strategies vs live data
python3 src/backtesting/signal_checker.py check --json         # JSON output
python3 src/backtesting/signal_checker.py list                 # List all graduated strategies
```

### Formatters (LLM returns JSON → Python renders markdown)
```bash
python3 src/formatters/trade_card.py '{...}'
python3 src/formatters/signal_card.py '{...}'
python3 src/formatters/target_package.py '{...}'
python3 src/formatters/portfolio_sync.py '{"result": [...]}'
```

---

## MCP Tools Available

| Server | Key Tools | Use For |
|--------|-----------|---------|
| **Nansen** | `token_flows`, `token_recent_flows_summary`, `token_current_top_holders`, `smart_traders_and_funds_token_balances`, `token_pnl_leaderboard`, `token_who_bought_sold` | On-chain flows, smart money, whale activity |
| **CoinStats** | `get-coin-by-id`, `get-coin-chart-by-id`, `get-coins`, `get-market-cap` | Prices, market data, portfolio |

---

## Databases

| Database | Location | Purpose |
|----------|----------|---------|
| `titan_data.db` | `data/` | OHLCV price cache |
| `titan_intelligence.db` | `data/` | Trade setups, watchlist, signals, mentor consultations |
| `ohlcv_cache.db` | `data/` | Fast OHLCV lookup cache |
| `signals.db` | External: `/Users/johnny_main/Developer/data/signals/signals.db` | MarketInsights Telegram signals (read-only) |

---

## Position Sizing Limits

| Category | Max % |
|----------|-------|
| Blue Chip (BTC, ETH) | 30% |
| Large Cap (Top 50) | 15% |
| Mid Cap (Top 100) | 10% |
| Small Cap (100+) | 5% |
| Degen/New (<30 days) | 2% |

Risk per trade: **2% max.** Minimum R:R = **3:1.**

---

## Autonomous Data Refresh

Claude is authorized to refresh stale data without prompting. Apply this logic whenever data age is checked:

**OHLCV data** — if any watchlist token's 4h or 1d data is >24h old, run the download command before analysis:
```bash
python3 src/data/ohlcv_client.py download [TOKEN] --timeframe 4h
python3 src/data/ohlcv_client.py download [TOKEN] --timeframe 1d
```
If the script is missing or errors, note it and continue with stale data.

**CEX dashboard** — if the most recent snapshot is >6h old, auto-run before any CEX-dependent analysis:
```bash
python3 src/watchers/cex_monitor.py snapshot
```

**Hyperliquid perps data** — if needed for a squeeze scan and last fetch is >4h old:
```bash
python3 src/fetchers/hyperliquid_fetcher.py
```

**Coinglass derivatives** — if needed for /analyze or /liquidity and last fetch is >1h old:
```bash
python3 src/fetchers/coinglass_fetcher.py --token [TOKEN] --derivatives --price [PRICE] --json
```

**Coinglass market pulse** — if needed for /start-session or /market-check and last fetch is >1h old:
```bash
python3 src/fetchers/coinglass_fetcher.py --market --json
```
Requires COINGLASS_API_KEY in .env. If not set, skip silently.

**Signals** — the signals DB is maintained externally (read-only). Do not attempt to refresh it.

Always report what was refreshed vs what was already current in the Data Status line.

---

## Nansen Credit Budget

**Session limit: 100 credits.** Track usage across every Nansen MCP call in the session.

### Credit costs per call

| Cost | Tools |
|------|-------|
| 1 credit | `general_search`, `transaction_lookup`, `address_transactions` |
| 2 credits | `token_flows`, `token_recent_flows_summary`, `token_ohlcv`, `token_transfers`, `address_portfolio`, `address_historical_balances`, `address_counterparties`, `address_related_addresses` |
| 3 credits | `token_current_top_holders`, `token_who_bought_sold`, `token_pnl_leaderboard`, `token_quant_scores`, `wallet_pnl_for_token`, `wallet_pnl_summary`, `hyperliquid_leaderboard` |
| 5 credits | `smart_traders_and_funds_token_balances`, `smart_traders_and_funds_perp_trades`, `token_discovery_screener`, `growth_chain_rank`, `nansen_score_top_tokens`, `token_dex_trades`, `token_recent_flows_summary` (multi-asset) |

### Rules

- **Track running total** — maintain a mental tally across all Nansen calls in the session
- **At 80 credits** — warn: "⚠️ 80/100 Nansen credits used this session."
- **At 100 credits** — stop and prompt: "🛑 100 Nansen credit limit reached. Approve more? (Y to continue, N to stop on-chain analysis)"
- **If user approves** — continue in 10-credit increments, prompting again at each threshold
- **Per-analysis cap** — no single `/analyze` or skill run should use more than 20 credits without prompting first
- **Always show credit cost** — when reporting on-chain findings, note "(X credits used, Y remaining)"

---

## Output Rules

- Verdict first, then logic
- Bold text, strategic emojis, insights over raw data
- Never use ASCII tables or code blocks for data display
- Never fabricate data — say "Data unavailable" if missing
- Partial report is better than no report
- If one API fails, complete the rest of the analysis

---

## Auto-Journaling

Every trade card and market report auto-appends to the quarterly journal:
- `my-trading/journal/YYYY_QX.md`
- Include date/time and `---` separator

## Results Storage

- Trade cards: `results/trade-cards/[TOKEN]_[YYYY-MM-DD].md`
- Skill runs: `results/skill-runs/[skill-name]/[TOKEN]_[YYYY-MM-DD].md`
