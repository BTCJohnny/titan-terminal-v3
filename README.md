# Titan Terminal v2

Autonomous crypto trading intelligence system powered by Claude Code.

Claude Code (your Max subscription) is the brain — it reads market data, interprets indicators, and synthesizes verdicts. Python scripts handle computation (math, data fetching, caching). Zero external API costs.

---

## Setup

1. Clone this repo and `cd` into it
2. Copy `.env.example` to `.env` and fill in your API keys
3. Copy `config/wallets.example.json` to `config/wallets.json` with your CoinStats share token
4. Copy `my-trading/portfolio.example.md` and `my-trading/alerts.example.md` (remove `.example` suffix, fill in your data)
5. Install Python dependencies: `pip3 install requests`
6. Open Claude Code in this directory — it reads `CLAUDE.md` automatically and discovers all commands, subagents, and skills

---

## Commands

### `/start-session` — Morning Briefing

Run this first every trading day. It checks everything in parallel and gives you a prioritized action list.

**What it does:**
- Reviews your watchlist for changes
- Checks the last 72 hours of MarketInsights signals
- Reads the latest CEX flow snapshot
- Scans for perps squeeze setups on Hyperliquid
- Reviews active accumulation setups
- Synthesizes into a prioritized briefing with "do this first" at the top

**When to use:** Start of every session. Again after 6+ hours if you're in a long session.

---

### `/market-check` — Market Weather

Quick read on whether the market is risk-on or risk-off.

**What it does:**
- Pulls BTC and ETH price, 24h/7d changes
- Checks total market cap trend
- Checks smart money fund activity (deploying or hoarding stablecoins?)
- Synthesizes into a weather metaphor: Sunny (risk-on), Cloudy (neutral), Stormy (risk-off)

**When to use:** After `/start-session` to set the tone for the day. Before entering any new trade to check if the macro supports it.

---

### `/ta [TOKEN]` — Quick Technical Analysis

TA-only check using the 7-Question framework across Weekly, Daily, and 4H timeframes.

**What it does:**
- Delegates to the ta-analyst subagent
- Downloads OHLCV data for 3 timeframes
- Runs 8 indicators: RSI, MACD, ADX+DI, Bollinger Bands, OBV, S/R levels, SMA 50/200, ATR
- Resolves timeframe conflicts (Weekly > Daily > 4H)
- Returns a verdict with confidence score, key levels, and a "So What?" section with specific trade levels

**When to use:** Quick structure check before committing to a full `/analyze`. Comparing TA across several tokens. Monitoring watchlist items for technical changes.

---

### `/analyze [TOKEN]` — Full Trade Card

The complete analysis. Combines 4 data pillars into a single directional verdict.

**What it does:**
1. Resolves the token on Nansen (chain, contract address)
2. Pulls market snapshot from CoinStats (price, cap, volume, rank)
3. Delegates multi-timeframe TA to the ta-analyst subagent
4. Queries on-chain flows from Nansen (exchange flows, smart money, whales)
5. Checks perps positioning (smart money long/short ratio on Hyperliquid)
6. Scores accumulation across 5 on-chain signals (0–5 scale)
7. Synthesizes a verdict using the signal weight hierarchy: on-chain > perps > TA
8. Auto-saves to `results/trade-cards/` and appends to your quarterly journal

**Signal weight hierarchy:** When signals conflict, on-chain wins. On-chain shows what people are doing with real money. Perps shows what traders are betting. TA shows what price has already done — it lags by definition.

**When to use:** Before entering any trade. When a squeeze or signal looks interesting and you need the full picture.

---

### `/check-signals [TOKEN or hours:N]` — Signal Validation

Validates external MarketInsights trading signals against your TA and on-chain data.

**What it does:**
1. Fetches recent signals from the MarketInsights database (default: last 72 hours)
2. For each signal, delegates TA validation to the signal-validator subagent
3. Adds on-chain validation via Nansen for signals that pass TA screening
4. Produces a final recommendation: VALID (take the trade), INVALID (skip), or NEEDS_CONFIRMATION (watchlist it)

**Argument options:**
- No argument → signals from last 72 hours
- Token name (e.g., `ETH`) → signals for that token only
- `hours:24` → signals from last 24 hours

**When to use:** After `/start-session` flags new signals. When someone sends you a trade idea and you want Titan's take.

---

### `/hunt-squeezes` — Perps Squeeze Scanner

Scans for extreme positioning imbalances on Hyperliquid perpetuals.

**What it does:**
1. Pulls recent smart money perp trades across all tokens
2. Groups by token, identifies extreme one-sided positioning (>70% long or short)
3. Runs full squeeze analysis on the top 3 candidates: positioning ratio, liquidation cascade map, macro context
4. Scores each from 0–10

**Key thresholds:**
- Score 8–10: High conviction setup — run `/analyze` immediately
- Score 6–7: Strong — add to watchlist
- Score 4–5: Watch only
- Below 4: No setup

**When to use:** Daily as part of your hunt for asymmetric trades. When funding rates are extreme. When you want mechanical, math-based setups rather than narrative-driven ones.

---

### `/target-package [TOKEN] [entry $X] [stop $Y] [targets $T1 $T2 $T3]` — Position Sizing

Calculates exact position sizing with 2% risk, 3:1 minimum R:R, and 3 profit targets for scaling out.

**What it does:**
1. Validates the setup (direction, stop placement, 3R minimum on T3)
2. Checks token category limits (Blue Chip 30%, Large Cap 15%, Mid Cap 10%, Small Cap 5%, Degen 2%)
3. Calculates position size based on 2% account risk
4. Generates scale-out plan: sell 33% at T1, 33% at T2, 34% at T3
5. Auto-saves to results and journal

**Input flexibility:**
- Minimal: `/target-package ETH` — Claude finds levels from TA, asks for your account balance
- Partial: `/target-package ETH long entry $1985 stop $1850` — Claude suggests targets
- Complete: `/target-package ETH long entry $1985 stop $1850 targets $2100 $2300 $2700 account $50000` — generates immediately

**The 3R rule is non-negotiable.** If T3 can't achieve 3:1 risk:reward, the setup is rejected. Find better levels or walk away.

**When to use:** After `/analyze` gives a bullish or bearish verdict and you want to enter. Never enter a trade without running this first.

---

## Typical Workflows

### Morning Routine (~10 min)
```
/start-session          → What needs attention today?
/market-check           → Risk-on or risk-off?
```

### Hunting Longs
```
/hunt-squeezes          → Any crowded shorts to squeeze?
/check-signals          → Any validated buy signals?
/analyze [TOKEN]        → Full Trade Card on best candidate
/target-package [TOKEN] → Size the trade
```

### Hunting Shorts
```
/hunt-squeezes          → Any crowded longs to fade?
/analyze [TOKEN]        → Is on-chain showing distribution?
/target-package [TOKEN] short → Size the short
```

### Quick Check on a Token
```
/ta [TOKEN]             → Just the technicals
```

### From Idea to Trade (the funnel)
```
/ta [TOKEN]             → Gate 1: Does TA support the direction?
/analyze [TOKEN]        → Gate 2: Does on-chain confirm?
/target-package [TOKEN] → Gate 3: Does R:R qualify (3:1+)?
Execute                 → All 3 gates passed
```

Fail any gate, no trade.

---

## The 3 Laws

Every analysis, verdict, and trade recommendation is filtered through:

1. **Protect Capital** — Prevent losses first. Flag risks prominently. 2% max risk per trade.
2. **Seek Asymmetric Upside** — 3R minimum. If reward isn't 3x the risk, reject the trade.
3. **Reject the Noise** — Data only. No hype, no vibes, no influencer takes. On-chain flows, smart money positioning, and price structure are the only inputs that matter.

---

## Architecture

```
Claude Code (Max subscription) = The Brain
  ├── CLAUDE.md                    → Project context (loaded every session)
  ├── .claude/agents/              → 3 specialist subagents
  │   ├── ta-analyst.md            → Multi-timeframe TA (7-Question framework)
  │   ├── wyckoff-analyst.md       → Wyckoff phase interpretation
  │   └── signal-validator.md      → External signal validation
  ├── .claude/commands/            → 7 slash commands (listed above)
  ├── .claude/skills/              → 3 domain knowledge packages
  │   ├── titan-trade-card/        → Trade Card methodology (11 files)
  │   ├── pre-breakout-accumulator/→ Accumulation detection (13 files)
  │   └── perps-squeeze-detector/  → Squeeze plays (8 files)
  └── src/                         → Python tools (computation only)
      ├── analysis/indicators.py   → TA indicators (RSI, MACD, BB, ADX, OBV, S/R, SMA, ATR)
      ├── fetchers/                → Signal DB queries, Hyperliquid data
      ├── formatters/              → Trade card, signal card, target package renderers
      ├── storage/intelligence.py  → SQLite watchlist + trade setup tracking
      └── watchers/                → CEX flow monitor, watchlist monitor

MCP Servers (external data):
  ├── Nansen     → On-chain flows, smart money, whale activity
  └── CoinStats  → Prices, market cap, portfolio
```

---

## File Locations

| What | Where |
|------|-------|
| Trade Card results | `results/trade-cards/` |
| Skill run results | `results/skill-runs/` |
| Trading journal | `my-trading/journal/YYYY_QN.md` |
| Portfolio | `my-trading/portfolio.md` |
| Price alerts | `my-trading/alerts.md` |
| Token universe | `config/token_list.json` |
| CEX dashboards | `signals/dashboards/` |
| Reference playbooks | `reference/playbooks/` |
| Interpreter guides | `reference/interpreters/` |
| OHLCV cache | `data/titan_data.db` |
| Watchlist + setups | `data/titan_intelligence.db` |