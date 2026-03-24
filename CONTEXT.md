# Titan Terminal — Command Router

## Commands

### `/hunt`
**Purpose:** Daily alpha scan. Pull all data sources, reason through them, surface 0-5 opportunity cards.

**Workflow:**
1. **Fetch all data in parallel:**
   - Coinglass market pulse: `python3 src/fetchers/coinglass_fetcher.py --market --json`
   - Coinglass liquidation scan: `python3 src/fetchers/coinglass_fetcher.py --scan`
   - CEX flows: `python3 src/watchers/cex_monitor.py snapshot` (or read latest if <6h old)
   - BTC regime check: `python3 src/analysis/indicators.py analyze BTC --timeframe 1w --indicators sma,adx,obv` and `--timeframe 1d`
   - Hyperliquid perps: `python3 src/fetchers/hyperliquid_fetcher.py`
   - Nansen smart money scan: `smart_traders_and_funds_token_balances` (5 credits) + `smart_traders_and_funds_perp_trades` (5 credits)

2. **Determine market regime:**
   Read `_config/thesis.md` for current regime definition and criteria.
   Assess: risk-on / risk-off / chop based on BTC structure, F&G, ETF flows, CEX flows, Coinbase premium.
   Determine which trade directions are valid today.

3. **Scan for anomalies across the universe** (`_config/universe.md`):
   Look for divergences between crowd behavior and smart money:
   - Nansen: 2+ funds accumulating >$20M? Smart money selling into rallies? Exchange flows >3x avg?
   - Coinglass: Extreme funding? OI divergence from price? Crowded L/S >5:1? Liquidation clusters <5% away?
   - CEX flows: Individual token flows via Nansen `token_recent_flows_summary` (2 credits each) for tokens that pass initial screen

4. **Apply convergence filter:**
   Only surface tokens where 2+ independent evidence types point the same direction.
   Apply `_config/red-flags.md` to reject disqualified setups.
   Read `_config/interpreters/` for how to interpret each data type.

5. **Rank 0-5 opportunities by conviction:**
   Weight by evidence type (see signal hierarchy in CLAUDE.md).
   Minimum bar: high conviction across at least 2 different evidence types.
   "Nothing today" when nothing meets the bar.

6. **Output:** Present findings with:
   - Market regime summary (risk-on/off/chop, F&G, BTC trend, ETF flow direction, CEX flow summary)
   - 0-5 opportunity cards, each with: token, direction, conviction, alpha thesis (2-3 sentences WHY), key data points, signal alignment
   - Nansen credits used

**Reference files:** `_config/thesis.md`, `_config/signal-hierarchy.md`, `_config/universe.md`, `_config/red-flags.md`, `_config/interpreters/`

---

### `/analyze [TOKEN]`
**Purpose:** Deep dive on one token. Full multi-source analysis with directional verdict.

**Workflow:**
1. **Resolve token identity:**
   - Nansen `general_search` for chain + contract (1 credit)
   - CoinStats `get-coin-by-id` for price, market cap, rank

2. **Fetch all data in parallel:**
   - **TA (multi-timeframe):** Download + analyze across W/D/4H/1H
     ```
     python3 src/analysis/indicators.py download [TOKEN] --timeframe 1w
     python3 src/analysis/indicators.py download [TOKEN] --timeframe 1d
     python3 src/analysis/indicators.py download [TOKEN] --timeframe 4h
     python3 src/analysis/indicators.py download [TOKEN] --timeframe 1h
     python3 src/analysis/indicators.py analyze [TOKEN] --timeframe 1w
     python3 src/analysis/indicators.py analyze [TOKEN] --timeframe 1d
     python3 src/analysis/indicators.py analyze [TOKEN] --timeframe 4h
     python3 src/analysis/indicators.py analyze [TOKEN] --timeframe 1h --indicators rsi,bb,atr,sr
     ```
   - **On-chain:** Nansen `token_recent_flows_summary` 1d + 7d (4 credits), `token_current_top_holders` smart_money + all (6 credits)
   - **Derivatives:** `python3 src/fetchers/coinglass_fetcher.py --token [TOKEN] --derivatives --price [PRICE] --json`
   - **CEX flows:** Nansen `token_recent_flows_summary` with exchange segment (2 credits, often covered by on-chain call above)

3. **Interpret each pillar:**
   Read relevant interpreters from `_config/interpreters/`:
   - On-chain: `accumulation-scores.md`, `smart-money-moves.md`, `cex-flows.md`
   - Derivatives: `derivatives-signals.md`, `funding-rates.md`

4. **Synthesize verdict using signal hierarchy:**
   On-Chain > Perps > Derivatives > TA.
   See `_config/signal-hierarchy.md` for conflict resolution matrix.
   Apply regime modifier from `_config/thesis.md`.

5. **Output:** Detailed analysis with:
   - Token identity + market snapshot
   - TA summary across all timeframes (verdict first, then key indicator readings)
   - On-chain flows + smart money positioning
   - Derivatives snapshot (funding, OI, L/S, liquidations)
   - CEX flows (direction, multiplier vs average)
   - **Directional verdict:** BULLISH / BEARISH / NEUTRAL with conviction level
   - Key levels (support, resistance from S/R analysis)
   - What would change the verdict (invalidation criteria)

**Nansen budget:** ~15-20 credits per analysis.

---

### `/targets [TOKEN] [LONG/SHORT] [entry] [stop]`
**Purpose:** Generate S/R levels and position sizing for a specific setup.

**Workflow:**
1. **Fetch S/R data:**
   ```
   python3 src/analysis/indicators.py download [TOKEN] --timeframe 4h
   python3 src/analysis/indicators.py download [TOKEN] --timeframe 1d
   python3 src/analysis/indicators.py analyze [TOKEN] --timeframe 4h --indicators sr,atr,bb
   python3 src/analysis/indicators.py analyze [TOKEN] --timeframe 1d --indicators sr,atr,bb
   ```

2. **Identify key levels:**
   - Support levels (for long entries / short targets)
   - Resistance levels (for short entries / long targets)
   - ATR for stop distance calibration
   - BB for volatility context

3. **Generate target package:**
   If entry + stop provided:
   ```
   python3 src/formatters/target_package.py '{"token": "[TOKEN]", "direction": "[LONG/SHORT]", "entry": [PRICE], "stop": [PRICE], "account": [AMOUNT], "targets": [T1, T2, T3]}'
   ```
   If only token + direction: suggest entry/stop/targets based on S/R analysis, then run target_package.py.

4. **Output:**
   - Key S/R levels with touch counts and strength
   - Suggested entry zone, stop loss, T1/T2/T3 targets
   - Position size based on 2% risk rule
   - R:R calculation for each target
   - Category limit check from `_config/position-sizing.md`

**Accepts flexible input:**
- Minimal: `/targets ETH LONG` — Claude finds levels from TA
- Partial: `/targets ETH LONG entry 1985 stop 1850` — Claude suggests targets
- Full: `/targets ETH LONG entry 1985 stop 1850 targets 2100 2300 2700 account 50000`
- Portfolio amount: specify once per session and it carries through

---

## Routing Rules

- "hunt", "scan", "what's interesting", "morning briefing", "start session" → `/hunt`
- Names a specific token for analysis → `/analyze [TOKEN]`
- Asks about levels, sizing, entry, stop, targets → `/targets [TOKEN]`
- Asks about market regime, BTC structure → `/hunt` (regime is part of the hunt output)
- Ambiguous → ask: "Are you looking for new opportunities across the market, or a deep dive on a specific token?"

## Shared Reference

| Resource | Path |
|----------|------|
| Active thesis | `_config/thesis.md` |
| Signal hierarchy | `_config/signal-hierarchy.md` |
| Universe | `_config/universe.md` |
| Red flags | `_config/red-flags.md` |
| Position sizing | `_config/position-sizing.md` |
| Interpreters | `_config/interpreters/` |
| Playbooks | `_config/playbooks/` |
| Examples | `_config/examples/` |
| Nansen budget | `_config/nansen-budget.md` |
