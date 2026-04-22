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
   - **Nansen discovery scan** (3 queries, ~15 credits — see step 1b)
   - **Fresh wallet scan** (`/fresh-wallets all` — 15 tokens × 2 credits = 30 credits — see step 1c)

1b. **Nansen Discovery Scan (run in parallel with step 1):**
   Three screener queries to surface smart money flow anomalies beyond the tracked universe.

   **Query A — Smart money spot buying:**
   ```
   token_discovery_screener:
     chains: [ethereum, base, solana, arbitrum]
     onlySmartTradersAndFunds: true
     marketCapUsd: {from: 50000000}
     liquidity: {from: 100000}
     orderBy: netflow
     orderByDirection: desc
     timeframe: 24h
   ```

   **Query B — Smart money spot selling:**
   Same as Query A but `orderByDirection: asc`. Surfaces distribution.

   **Query C — Smart money HL perps positioning:**
   ```
   token_discovery_screener:
     chains: [hyperliquid]
     onlySmartTradersAndFunds: true
     orderBy: netflow
     orderByDirection: desc
     timeframe: 24h
   ```
   Returns: open long/short positions (USD), trader count, funding, net flow per token.

   **How to read the discovery scan:**
   - **Spot (A+B):** If spot flows are quiet (tiny volumes, few tokens), smart money is sitting on hands — all action is via derivatives. If a token shows >$500K net flow from 3+ traders, flag for deeper look.
   - **HL perps (C):** The key columns are `Current Longs USD` vs `Current Shorts USD` (the STOCK of open positions) and `Net Flow` (today's FLOW). Look for:
     - **Flow vs stock divergence:** Smart money positioned short but today buying = potential covering / thesis change. This is the highest-signal pattern.
     - **Extreme long/short ratios:** >10:1 in either direction = crowded trade. Cross-reference with Coinglass funding to confirm.
     - **Tokens outside the universe:** If smart money is actively trading a token not in `_config/universe.md`, flag it — they see something the scan didn't.
     - **Trader count:** 5+ traders in same direction = consensus. 1 trader = noise.
   - **Compare with prior scan:** Read the most recent `hunt_*.md` or `session_summary_*.md` for prior discovery scan data. Tokens where smart money position direction has CHANGED since last scan get highest priority — a flip represents a decision.

1c. **Fresh Wallet Scan (run in parallel with steps 1 and 1b):**
   Run the full `/fresh-wallets all` scan (15 tokens). This catches unlabeled accumulation that the labeled SM scan misses — often the earliest signal. Use addresses from `_config/token-addresses.md`.

   For each token, call `token_current_top_holders` (2 credits each):
   ```
   token_current_top_holders:
     tokenAddress: [from config]
     chain: [from config]
     labelType: top_100_holders
     order_by: balance_change_30d
     order_by_direction: desc
   ```

   **Flag fresh wallets** using criteria from `/fresh-wallets` command (Sent=0, 30d Change=Balance, generic label, >$100K).
   **Compare with prior scan** (`fresh_wallets_*.md`) — new wallets, increased positions, wallets that started sending.
   Include fresh wallet findings in the hunt output as an independent evidence type.

2. **Determine market regime:**
   Read `_config/thesis.md` for current regime definition and criteria.
   Assess: risk-on / risk-off / chop based on BTC structure, F&G, ETF flows, CEX flows, Coinbase premium.
   Determine which trade directions are valid today.

3. **Scan for anomalies across the universe** (`_config/universe.md`):
   Look for divergences between crowd behavior and smart money:
   - Nansen: 2+ funds accumulating >$20M? Smart money selling into rallies? Exchange flows >3x avg?
   - Coinglass: Extreme funding? OI divergence from price? Crowded L/S >5:1? Liquidation clusters <5% away?
   - CEX flows: Individual token flows via Nansen `token_recent_flows_summary` (2 credits each) for tokens that pass initial screen
   - **Discovery scan anomalies (from step 1b):**
     - Cross-reference HL perps stock with Coinglass funding. If both extreme in same direction, flag for opportunity card.
     - Flag any token where HL smart money is net buying >$200K today while cumulative position is short (covering signal).
     - Flag any token with smart money spot buying >$500K that isn't in the current universe — potential new thesis.
     - Note when spot screener is dead quiet — means smart money is exclusively using derivatives, which changes how to weight perps vs on-chain data.
   - **Fresh wallet anomalies (from step 1c):**
     - Any token with >$10M in fresh wallet accumulation (score 3+) is an independent evidence type for convergence.
     - Cross-reference fresh wallets with SM spot: if labeled SM is flat but fresh wallets are loading, it's early-stage accumulation before labels are applied.
     - Flag tokens where fresh wallet activity CHANGED vs prior scan (new wallets appeared, positions grew, or wallets started sending/distributing).

4. **Apply convergence filter:**
   Only surface tokens where 2+ independent evidence types point the same direction.
   Apply `_config/red-flags.md` to reject disqualified setups.
   Read `_config/interpreters/` for how to interpret each data type.
   Discovery scan data counts as an independent evidence type (smart money positioning) distinct from Coinglass derivatives data.

5. **Rank 0-5 opportunities by conviction:**
   Weight by evidence type (see signal hierarchy in CLAUDE.md).
   Minimum bar: high conviction across at least 2 different evidence types.
   "Nothing today" when nothing meets the bar.

6. **Output:** Present findings with:
   - Market regime summary (risk-on/off/chop, F&G, BTC trend, ETF flow direction, CEX flow summary)
   - **Discovery scan summary:**
     - Smart money spot activity level (active / quiet / dead)
     - HL perps positioning table (top 5-8 tokens by smart money position size: shorts $, longs $, ratio, today's flow)
     - Any tokens flagged outside the universe
     - Flow vs stock divergences (covering / accumulating signals)
   - **Fresh wallet scan summary:**
     - Per-token: count of flagged fresh wallets, total USD accumulated, top fresh wallet scores
     - Cross-wallet patterns (same wallet in multiple tokens)
     - Delta vs prior fresh wallet scan (new wallets, position changes, distribution signals)
     - Tokens with zero fresh wallet signal (also useful — confirms no stealth accumulation)
   - 0-5 opportunity cards, each with: token, direction, conviction, alpha thesis (2-3 sentences WHY), key data points, signal alignment
   - Nansen credits used

7. **Save output:** Write the complete hunt output to `signals/dashboards/hunt_YYYYMMDD_HHMM.md` using current UTC time. This matches the existing naming convention for CEX snapshots (`cex_YYYYMMDD_HHMM.md`) and Coinglass reports (`cg_liquidity_*_YYYYMMDD_HHMM.json`).

**Nansen budget for /hunt:** ~65-75 credits (10 smart money scan + 15 discovery scan + 30 fresh wallet scan + ~10-20 for individual token flows in step 3).

**Reference files:** `_config/thesis.md`, `_config/signal-hierarchy.md`, `_config/universe.md`, `_config/red-flags.md`, `_config/interpreters/`

---

### `/analyze [TOKEN]`
**Purpose:** Deep dive on one token. Full multi-source analysis with directional verdict.

**Workflow:**
1. **Resolve token identity:**
   - Nansen `general_search` for chain + contract (1 credit)
   - CoinStats `get-coin-by-id` for price, market cap, rank

2. **Review prior analyses:**
   - Glob `signals/dashboards/analyze_[TOKEN]_*.md` and `signals/dashboards/accum_distro_[TOKEN]_*.md`
   - Read the most recent report (if one exists)
   - Extract: prior verdict, accumulation score, key levels, any signals that were flagged as strengthening/weakening
   - This informs the current analysis — trajectory matters:
     - **Accelerating signal** (score rising across reports): upgrade conviction
     - **Decelerating signal** (score falling, funds exiting): downgrade even if current snapshot looks OK
     - **Level validation**: if prior S/R levels were respected, they get more weight
     - **Flipped signals**: a signal that changed direction carries more weight than one that stayed the same (it represents a decision to change)
   - Current data always drives the verdict — prior analyses add or subtract conviction via trajectory

3. **Fetch all data in parallel:**
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
   - **Fresh wallets:** Nansen `token_current_top_holders` sorted by `balance_change_30d` desc (2 credits) — flag unlabeled wallets with >$100K, Sent=0, 30d accumulation. Score 0-5 per CLAUDE.md fresh wallet criteria. Compare with prior `/fresh-wallets` or `/analyze` output for delta.
   - **Derivatives:** `python3 src/fetchers/coinglass_fetcher.py --token [TOKEN] --derivatives --price [PRICE] --json`
   - **CEX flows:** Nansen `token_recent_flows_summary` with exchange segment (2 credits, often covered by on-chain call above)

4. **Interpret each pillar:**
   Read relevant interpreters from `_config/interpreters/`:
   - On-chain: `accumulation-scores.md`, `smart-money-moves.md`, `cex-flows.md`
   - Derivatives: `derivatives-signals.md`, `funding-rates.md`

5. **Synthesize verdict using signal hierarchy:**
   On-Chain > Perps > Derivatives > TA.
   See `_config/signal-hierarchy.md` for conflict resolution matrix.
   Apply regime modifier from `_config/thesis.md`.
   Factor in trajectory from prior analyses (step 2) — strengthen or weaken conviction based on direction of change.

6. **Output:** Detailed analysis with:
   - Token identity + market snapshot
   - **Delta from prior analysis** (if prior report exists):
     - Verdict change (e.g., "Bullish → Cautious Bullish")
     - Accumulation score change (e.g., "3/5 → 3.5/5 — accelerating")
     - Signals that flipped, strengthened, or degraded
     - Whether prior key levels were respected by price
   - TA summary across all timeframes (verdict first, then key indicator readings)
   - On-chain flows + smart money positioning
   - **Fresh wallet activity** (count flagged, total USD, top scores, delta vs prior scan)
   - Derivatives snapshot (funding, OI, L/S, liquidations)
   - CEX flows (direction, multiplier vs average)
   - **Directional verdict:** BULLISH / BEARISH / NEUTRAL with conviction level
   - Key levels (support, resistance from S/R analysis)
   - What would change the verdict (invalidation criteria)

7. **Save output:** Write the complete analysis to `signals/dashboards/analyze_[TOKEN]_YYYYMMDD_HHMM.md` using the token name (UPPERCASE) and current UTC time. Example: `analyze_ETH_20260324_1520.md`.

**Nansen budget:** ~17-22 credits per analysis (includes 2-credit fresh wallet scan).

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

5. **Save output:** Write the complete target package to `signals/dashboards/targets_[TOKEN]_YYYYMMDD_HHMM.md` using the token name (UPPERCASE) and current UTC time. Example: `targets_ETH_20260324_1530.md`.

**Accepts flexible input:**
- Minimal: `/targets ETH LONG` — Claude finds levels from TA
- Partial: `/targets ETH LONG entry 1985 stop 1850` — Claude suggests targets
- Full: `/targets ETH LONG entry 1985 stop 1850 targets 2100 2300 2700 account 50000`
- Portfolio amount: specify once per session and it carries through

---

### `/fresh-wallets [TIER]`
**Purpose:** Scan universe tokens for stealth accumulation by fresh (unlabeled) wallets. Surfaces institutional accumulation before Nansen labels exist.

**Why this matters:** Fresh wallets are the earliest accumulation signal — they catch buying BEFORE smart money labels are applied. The standard `/hunt` pipeline only sees labeled smart money, which is inherently late.

**Workflow:**
1. **Select tokens to scan:**
   - Look up which tokens were scanned in the most recent `fresh_wallets_*.md` report
   - **Tier 1 — Priority (every scan):** Active thesis tokens + any token that previously showed fresh wallet activity. Currently: ZRO, LINK, AAVE, ONDO, HYPE + thesis tokens.
   - **Tier 2 — Rotation (fill remaining slots):** Pick tokens from the universe that haven't been scanned recently, until you reach 10 tokens total.
   - **Override:** `/fresh-wallets all` scans 15 tokens (30 credits). `/fresh-wallets [TOKEN TOKEN TOKEN]` scans specific tokens.
   - Use addresses from `_config/token-addresses.md` (no general_search needed).

2. **For each token, run `token_current_top_holders`:**
   ```
   token_current_top_holders:
     tokenAddress: [from config]
     chain: [from config]
     labelType: top_100_holders
     order_by: balance_change_30d
     order_by_direction: desc
   ```
   Cost: 2 credits per token.

3. **Flag fresh wallets using these criteria:**
   - **Sent = 0** (or near-zero) — wallet only receives, never sends. Accumulation-only.
   - **30d Change = Balance** (entire position built in 30 days)
   - **Label is generic** — "Token Millionaire", "ETH Millionaire", "High Balance", or unlabeled `[0x...]`. NOT an exchange, fund, protocol, or identified entity.
   - **Balance USD > $100K** — meaningful position size
   - **Fresh Wallet Score (0-5):** +1 zero sends, +1 all-30d accumulation, +1 >$500K position, +1 no identity label, +1 appears in multiple tokens (cross-wallet)

4. **Cross-reference wallets across tokens:**
   - Track wallet addresses that appear in multiple token scans
   - Same wallet accumulating 3+ tokens = portfolio building pattern (highest signal)
   - Note the total USD across all tokens for cross-wallet entities

5. **Compare with prior scan:**
   - Read most recent `fresh_wallets_*.md`
   - Flag: new wallets that appeared since last scan, wallets that increased position, wallets that started sending (distribution began)

6. **Output:**
   - Summary: tokens scanned, total fresh wallet $ found, cross-wallet entities
   - Per-token table: wallet address, label, balance USD, 30d change, sent history, fresh score
   - Cross-wallet pattern table: entity wallets, tokens held, total USD
   - Tokens with zero fresh wallet signal (also useful — confirms no stealth accumulation)
   - Credits used
   - Which tokens to scan next rotation

7. **Save output:** `signals/dashboards/fresh_wallets_YYYYMMDD_HHMM.md`

**Nansen budget:** ~20 credits per scan (10 tokens × 2 credits). Max 30 credits for `/fresh-wallets all`.

**Recommended cadence:** Every 2-3 days. Full universe coverage every ~1 week via rotation.

**Integration with /hunt:** When `/fresh-wallets` finds significant accumulation (>$20M fresh wallets for a token), that token gets flagged in the next `/hunt` as an independent evidence type — "Fresh wallet accumulation" sits alongside on-chain/perps/derivatives/TA in the signal hierarchy, weighted equal to on-chain smart money.

---

## Routing Rules

- "hunt", "scan", "what's interesting", "morning briefing", "start session" → `/hunt`
- "fresh wallets", "stealth accumulation", "who's accumulating", "new wallets" → `/fresh-wallets`
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
| Token addresses | `_config/token-addresses.md` |
