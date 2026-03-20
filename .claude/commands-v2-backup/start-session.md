---
name: start-session
description: Morning session briefing — watchlist review, signal check, CEX health, squeeze scan, accumulator review, and prioritized action list.
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - mcp__nansen
  - mcp__coinstats
---

# /start-session

Run the full Titan morning session briefing. This is the first thing to run at the start of every trading session.

## What This Produces

A prioritized session briefing that answers: "What happened while I was away, what needs attention, and what should I do first?"

---

## Execution Plan

### Step 0 — Data Freshness Check (run first, before anything else)

**Load Current Thesis**

Read `reference/titan-thesis.md` to load the current market regime, active theses, and hunting priorities. This frames the entire session briefing — data is evaluated against the thesis, not in a vacuum.

Before pulling any analysis, confirm all data sources are current. Run these checks in parallel:

**OHLCV Cache Age**
```bash
python3 -c "
import sqlite3, time
from pathlib import Path
db = Path('data/titan_data.db')
if not db.exists():
    print('OHLCV: NO CACHE FILE')
else:
    conn = sqlite3.connect(db)
    rows = conn.execute(\"SELECT symbol, timeframe, MAX(timestamp) as latest FROM ohlcv GROUP BY symbol, timeframe ORDER BY latest DESC LIMIT 10\").fetchall()
    now = time.time() * 1000
    for r in rows:
        age_h = (now - r[2]) / 3600000
        status = 'STALE' if age_h > 24 else 'OK'
        print(f'{r[0]} {r[1]}: {age_h:.1f}h old [{status}]')
    conn.close()
"
```

**CEX Dashboard Age**
```bash
ls -t signals/dashboards/cex_*.md 2>/dev/null | head -1 | xargs -I{} stat -f "%Sm %N" -t "%Y-%m-%d %H:%M" {} 2>/dev/null || echo "CEX: NO DASHBOARD FILES"
```

**Signals DB Last Entry**
```bash
python3 -c "
import sqlite3
from pathlib import Path
db = Path('/Users/johnny_main/Developer/data/signals/signals.db')
if not db.exists():
    print('SIGNALS: DB NOT FOUND')
else:
    conn = sqlite3.connect(db)
    try:
        row = conn.execute(\"SELECT MAX(created_at) FROM signals\").fetchone()
        print(f'SIGNALS: last entry = {row[0]}')
    except Exception as e:
        print(f'SIGNALS: error — {e}')
    conn.close()
"
```

**Watchlist Last Updated**
```bash
python3 -c "
import sqlite3
from pathlib import Path
db = Path('data/titan_intelligence.db')
if not db.exists():
    print('WATCHLIST: DB NOT FOUND')
else:
    conn = sqlite3.connect(db)
    try:
        row = conn.execute(\"SELECT COUNT(*), MAX(updated_at) FROM watchlist WHERE status='active'\").fetchone()
        print(f'WATCHLIST: {row[0]} active items, last updated {row[1]}')
    except Exception as e:
        print(f'WATCHLIST: error — {e}')
    conn.close()
"
```

**Portfolio Sync**

Sync portfolio from CoinStats to get current holdings and PnL:

1. Call CoinStats MCP:
```
mcp__coinstats__get-portfolio-coins: shareToken "NL3S076anq11Ibz", limit 50
```

2. Pass the response to the formatter:
```bash
python3 src/formatters/portfolio_sync.py '<JSON_RESPONSE>'
```

3. Read the summary line from stdout and include in the Data Status line.

If CoinStats fails, note "Portfolio: STALE" in Data Status and continue — don't block the session.

**Evaluate freshness and decide:**

- If any OHLCV data is **>24h stale** for watchlist tokens: run `python3 src/data/ohlcv_client.py download [TOKEN] --timeframe 4h` for each stale token before proceeding.
- If the CEX dashboard is **>24h old** or missing: run `python3 src/watchers/cex_monitor.py snapshot` before Step 3.
- If signals DB is **unreachable**: note it and skip Step 2.
- If all data is fresh (< 24h): proceed immediately.

Report the freshness check as a single line at the top of the final briefing:
`**Data Status:** OHLCV [OK/REFRESHED/STALE], CEX [OK/REFRESHED/STALE], Signals [OK/UNAVAILABLE], Watchlist [OK/EMPTY]`

---

### Group 1 — Run in Parallel (no dependencies)

#### Step 1: Watchlist Review

```bash
python3 src/watchers/watchlist_monitor.py review
```

Extract:
- Number of active watches
- Items with changed analysis (price moved significantly, new signals)
- Priority grouping (triggered alerts > entry zones approaching > stable watches)
- Any items that need re-analysis

#### Step 1b: Alert Check

Check price alerts against current market prices:

1. Read `my-trading/alerts.md` to identify unique tokens with pending alerts
2. For each unique token, fetch current price via CoinStats:
   ```
   mcp__coinstats__get-coin-by-id: coinId "[token-id]"
   ```
   Build a prices JSON: `{"BNB": 667.94, "ZRO": 2.17, ...}`

   **For tokens CoinStats doesn't index** (micro-caps, newer tokens): try `mcp__coinstats__get-coins` with a search, or note "NO PRICE DATA" and move on. Don't block the session for missing prices.

3. Run the checker:
   ```bash
   python3 src/watchers/alert_checker.py --update '<PRICES_JSON>'
   ```

4. Any TRIGGERED or APPROACHING alerts should surface in the Priority Actions section of the briefing.

If all token price lookups fail, note "Alerts: UNCHECKED" in Data Status and continue.

#### Step 2: Signal Check (72h)

```bash
python3 src/fetchers/signals_fetcher.py recent --hours 72
```

Extract:
- Number of new signals in the last 3 days
- Token, direction, and date for each
- Flag any signals for tokens already on the watchlist (overlap = higher priority)

#### Step 3b: Derivatives Pulse

```bash
python3 src/fetchers/coinglass_fetcher.py --market --json
```

#### Step 3c: Graduated Strategy Signals

Check if any backtested graduated strategies have entry conditions currently met:

```bash
python3 src/backtesting/signal_checker.py check
```

If OHLCV data is stale (refreshed in Step 0), the signal checker will use the refreshed data.

Extract:
- Number of strategies currently firing
- For each firing strategy: symbol, direction, suggested levels, and backtest metrics
- For non-firing strategies: which signals are missing (useful context)

**If any strategy is FIRING:** This is a Priority Action. Include the suggested trade levels in Priority Actions so the user can create the trade setup.

If COINGLASS_API_KEY is not set, skip this step silently and note "Derivatives: UNAVAILABLE" in Data Status.

From the JSON output, extract:
- BTC + ETH funding rates (cross-exchange average, bias)
- BTC + ETH OI momentum (1h/4h/24h change from exchange list)
- BTC ETF flows (latest day + weekly net + streak)
- Fear & Greed index (value, label, contrarian signal if extreme)
- Coinbase Premium (US institutional bias)
- BTC Global L/S ratio + Top trader lean

#### Step 3: CEX Health Pulse

Read the most recent CEX dashboard snapshot:

```bash
ls -t signals/dashboards/cex_*.md | head -1
```

Read that file and extract:
- Overall CEX flow direction (accumulation / distribution / neutral)
- Which assets have notable flows (large inflows or outflows)
- Any active alerts
- Age of the snapshot (if older than 24h, note it's stale)

If no snapshot files exist, note "No CEX dashboard data available. Run `python3 src/watchers/cex_monitor.py snapshot` to generate."

---

### Group 2 — Run After Group 1 (uses watchlist context)

#### Step 4: Squeeze Scan

Run the perps-squeeze-detector skill's hunt-squeezes workflow. This scans across tokens for extreme positioning imbalances on Hyperliquid perps.

Use `mcp__nansen__smart_traders_and_funds_perp_trades` to pull recent smart money perp activity, group by token, identify extreme one-sided positioning (>70%), then run `mcp__nansen__token_current_top_holders` with `mode: "perps"` on the top 3 candidates.

Flag any tokens with Squeeze Score 6+ or imbalance ratio 5:1+.

If Nansen perp calls fail, note "Squeeze scan unavailable — Nansen perp data error" and continue.

#### Step 5: Accumulator Review

Check stored accumulation data for active watchlist items.

**5a. Check stored entity diffs:**
For each active watchlist item with `source_type = 'skill'` or thesis mentioning accumulation:
```bash
python3 src/storage/intelligence.py entity-diff [SYMBOL] --days-back 7
```

Flag any entities that:
- Increased position >25% since last snapshot (accumulation accelerating)
- Decreased position >25% since last snapshot (distribution starting — thesis may be breaking)
- New entities appeared (fresh interest)

**5b. Check stored exchange balance trends:**
```bash
python3 src/storage/intelligence.py exchange-trend [SYMBOL] --days 14
```

Flag if:
- Balance declining >5% over 14 days (supply squeeze building)
- Balance increasing >5% over 14 days (supply returning — bearish)

**5c. Check hunt history for outcome tracking:**
```bash
python3 src/storage/intelligence.py hunt-history --days 30
```

For any past hunt candidates that are 7+ days old and don't have outcome data yet, flag them for price check: "Hunt candidate [TOKEN] from [DATE] needs 7d/14d/30d price update."

If no stored accumulator data exists for any watchlist items, note: "No stored accumulator data. Run `/hunt-accumulation` or `/analyze-accumulation [TOKEN]` to seed the database."

---

### Group 3 — Synthesize After All Steps Complete

#### Step 6: Session Briefing

Synthesize all findings into a single prioritized briefing using this format:

```
# Titan Session Briefing — [YYYY-MM-DD]

**Data Status:** OHLCV [OK/REFRESHED/STALE] · CEX [OK/REFRESHED/STALE] · Signals [OK/UNAVAILABLE] · Watchlist [OK/EMPTY] · Portfolio [SYNCED/STALE] · Alerts [CHECKED/UNCHECKED] · Derivatives [OK/UNAVAILABLE]

## Priority Actions
1. [Highest priority — triggered alerts, entry zones hit, conflicting signals]
2. [Second priority]
3. [...]

**Thesis-aware prioritization:** When generating Priority Actions, compare overnight price action against all active theses in titan-thesis.md:
- If a thesis entry zone was hit → 🔴 "Entry zone hit on [TOKEN] — review and decide"
- If a thesis invalidation level was breached → 🔴 "Thesis invalidated: [TOKEN] closed above/below $X"
- If a regime change signal fired → 🔴 "Regime change signal: [description]"
- If a graduated strategy is FIRING → 🔴 "Strategy signal: [STRATEGY_NAME] — [SYMBOL] [DIRECTION] at $[PRICE]. Create setup?"

## Thesis Status
**Regime:** [from titan-thesis.md] | **Bias:** [from titan-thesis.md]
- [THESIS 1]: [entry hit? / invalidated? / unchanged] — [1-line update]
- [THESIS 2]: [entry hit? / invalidated? / unchanged]
- [...]
[If any thesis was invalidated by overnight price action, flag it as 🔴 in Priority Actions]

## Watchlist Status
- **Active:** N items | **Changed:** N | **Needs review:** N
[1-line summary of the most important watchlist change, if any]

## New Signals (72h)
- **N new signals** — [summary of notable ones by token and direction]
[Flag any signals that overlap with watchlist tokens]

## Market Context
- **CEX:** [Accumulation / Distribution / Neutral] — [1-line detail]
- **Key flows:** [Notable asset flows from CEX dashboard]

## Derivatives Pulse
**Fear & Greed:** [value] — [label] | **Coinbase Premium:** [+/-$X] ([bias])
**BTC Funding:** [rate]% ([bias]) | **ETH Funding:** [rate]% ([bias])
**BTC OI:** [trend] ([+/-X% 24h]) | **ETH OI:** [trend] ([+/-X% 24h])
**ETF Flows:** $[latest day] | **Weekly:** $[net] ([X-day [inflow/outflow] streak])
**BTC L/S (Global):** [X.Xx] ([X% long]) | **Top Trader Lean:** [Long/Short/Neutral]

[1-2 sentence synthesis: What does the derivatives market say about the current regime? Does it confirm or contradict the thesis?]

## Strategy Signals
**Graduated:** N strategies | **Firing:** N
[For each firing strategy:]
🔴 **[STRATEGY_NAME]** — [SYMBOL] [DIRECTION] at $[PRICE]
  Entry $[X] | Stop $[X] | T1 $[X] | T2 $[X] | Size $[X]
  Backtest: PF [X] | WR [X]% | [N] trades

[For non-firing strategies, one line each:]
⚪ [STRATEGY_NAME] — [SYMBOL] [DIRECTION] — waiting for [missing signal]

## Squeeze Watch
[Any tokens with Score 6+ or imbalance 5:1+, or "No extreme positioning detected"]

## Portfolio
**Total:** $X | **Positions:** N | **Unrealized PnL:** [+/-]$X ([+/-]X.X%)
[1-line summary of changes since last sync, or "No changes" if unchanged]

## Alerts
[Summary from alert_checker.py — triggered count, approaching count, stale count]
[If any triggered: list them with action suggestion]
[If any approaching: list them with distance %]
[If any stale: suggest review/removal]

## Accumulator Setups
[Status of active accumulation watches, or "No active setups"]

## Suggested Next Steps
1. [Most actionable item — e.g., "Run /analyze on X — entry zone approaching"]
2. [Second action]
3. [Optional third action]
```

---

## Formatting Rules

- **Priority Actions is the most important section** — if the user reads nothing else, this tells them what to do
- Any TRIGGERED alert should be the #1 priority action. Any APPROACHING alert should also appear in Priority Actions.
- Bold key metrics and token names
- Use descriptive emojis for priority actions (🔴 urgent, 🟡 watch, 🟢 stable)
- Keep it concise — this is a briefing, not a report
- If any data source failed, note it but don't let it block the rest of the briefing
- Partial briefing is always better than no briefing
