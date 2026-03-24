# Titan Terminal

Intelligence terminal for crypto trading alpha, powered by Claude Code.

Surfaces opportunities using Nansen on-chain flows, Coinglass derivatives data, Hyperliquid perps positioning, and multi-timeframe technical analysis. Claude Code (Opus) reasons through the data and presents findings.

**This is NOT a trading system.** It does not execute trades, backtest, or manage positions. It answers: "What's interesting right now and why?" When you find something worth trading, take it to your exchange.

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env  # Add COINGLASS_API_KEY
pip3 install requests ccxt

# 2. Open Claude Code in this directory — reads CLAUDE.md automatically

# 3. Run your first scan
/hunt
```

## Commands

### `/hunt` — What's Interesting Right Now?

Pulls data from every source in parallel (Nansen smart money, Coinglass derivatives, Hyperliquid perps, CEX flows, BTC regime), reasons through it all, and surfaces 0-5 opportunity cards ranked by conviction.

"Nothing today" is a valid and expected outcome. The terminal does not force-find setups.

### `/analyze [TOKEN]` — Deep Dive

Full analysis on one token: multi-timeframe TA (W/D/4H/1H), Nansen on-chain flows, Coinglass derivatives, CEX flows. Produces a directional verdict using the signal hierarchy (On-Chain > Perps > Derivatives > TA).

### `/targets [TOKEN] [LONG/SHORT]` — Position Sizing

Identifies S/R levels, suggests entry/stop/targets, calculates position sizing with 2% risk and 3:1 minimum R:R. Accepts flexible input — from just a token name to fully specified levels.

## Signal Hierarchy

```
On-Chain Flows  >  Perps Positioning  >  Derivatives Intelligence  >  Technical Analysis
```

Higher weight wins conflicts. Always.

## Architecture

```
Claude Code (Opus, Max subscription) = The Brain
  ├── CLAUDE.md           → Terminal identity, 3 Laws, data sources
  ├── CONTEXT.md          → Command routing
  ├── _config/            → Thesis, interpreters, playbooks, red flags
  └── src/                → Python tools (computation only)
      ├── analysis/       → indicators.py (8 indicators, multi-timeframe)
      ├── data/           → ohlcv_client.py (OHLCV cache)
      ├── fetchers/       → coinglass, hyperliquid, binance
      ├── formatters/     → target_package, portfolio_sync
      ├── storage/        → intelligence.py, nansen_cache.py
      └── watchers/       → cex_monitor.py
```

## Data Sources

| Source | What | Cost |
|--------|------|------|
| Nansen MCP | Smart money flows, whale activity, exchange flows | 100 credits/session |
| Coinglass API | Funding, OI, L/S, liquidations, ETF flows, F&G, premium | Hobbyist $29/mo |
| Hyperliquid API | Perps positioning, OI by token | Free |
| CoinStats MCP | Prices, market cap, portfolio | Free |
| indicators.py | 8 TA indicators, multi-timeframe, S/R levels | Free (local compute) |
| CEX monitor | BTC/ETH/USDT/USDC exchange flow snapshots | Free |

## Reference Material (`_config/`)

| File | Purpose |
|------|---------|
| `thesis.md` | Active regime, setup types, hunting priorities |
| `signal-hierarchy.md` | Conflict resolution rules |
| `universe.md` | Scan universe (32 tokens) |
| `interpreters/` | How to read: flows, funding, smart money, derivatives, accumulation |
| `playbooks/` | Nansen, signals, market regime playbooks |
| `position-sizing.md` | Category limits, risk rules |
| `red-flags.md` | Automatic rejection criteria |
