# Stage: 01_regime — Market Structure Check

## Purpose

Determine the current market regime and which setup types are valid today. This gates the entire pipeline — if the regime says "no longs," the scanner won't look for longs.

## Inputs

| Source | File | Layer |
|--------|------|-------|
| Reference | `_config/thesis.md` | 3 (factory) |
| Reference | `_config/interpreters/cex-flows.md` | 3 (factory) |
| Reference | `_config/interpreters/funding-rates.md` | 3 (factory) |

## Process

### Step 1: Fetch Market Data (parallel)

Run all data fetches simultaneously:

**BTC structure:**
```bash
python3 src/analysis/indicators.py analyze BTC --timeframe 1d --indicators sma,adx,obv
python3 src/analysis/indicators.py analyze BTC --timeframe 1w --indicators sma,adx
```

**Derivatives pulse:**
```bash
python3 src/fetchers/coinglass_fetcher.py --market --json
```
Extracts: BTC/ETH funding, OI momentum, ETF flows, Fear & Greed, Coinbase premium, global L/S.

**CEX flows:**
```bash
ls -t signals/dashboards/cex_*.md | head -1
```
Read the most recent snapshot. If >24h old, run `python3 src/watchers/cex_monitor.py snapshot` first.

**Portfolio sync:**
```
mcp__coinstats__get-portfolio-coins: shareToken "NL3S076anq11Ibz", limit 50
```
Pass response to: `python3 src/formatters/portfolio_sync.py '<JSON>'`

### Step 2: Determine Regime

Evaluate against thesis and data:

| Regime | Criteria |
|--------|----------|
| **Risk-On** | BTC weekly above SMA 50+200, ETF inflows, F&G >50, CEX outflows, positive premium |
| **Risk-Off** | BTC weekly below SMA 50+200, ETF outflows, F&G <30, CEX inflows/distribution, negative premium |
| **Chop** | Mixed signals, BTC between SMAs, no clear directional bias |

### Step 3: Determine Sub-Regime (Risk-Off only)

Use CEX flow data (see `_config/interpreters/cex-flows.md`):

| Sub-Regime | CEX Signal | Valid Setups |
|------------|-----------|-------------|
| Distribution phase | Inflows on bounces, SM selling | Shorts only |
| Counter-trend bounce | Outflows during dips, stablecoin inflows, crowded shorts | Selective longs + shorts |
| Regime transition | Sustained outflows 2+ weeks, accumulation across 3+ assets | Widen long scope |

### Step 4: List Valid Setup Types

Based on regime + sub-regime, explicitly state which setup types from the thesis are valid today:
- Distribution Shorts: [VALID/INVALID] — reason
- Accumulation Longs: [VALID/INVALID] — reason
- Breakout Plays: [VALID/INVALID + direction constraint] — reason
- Mean Reversion: [VALID/INVALID] — reason

### Step 5: Check Active Theses

Compare current data against all active theses in `_config/thesis.md`:
- Entry zones hit? → Flag as priority action
- Invalidation levels breached? → Flag for thesis update
- Regime change signals fired? → Flag for thesis rewrite

## Scripts Used

- `python3 src/analysis/indicators.py analyze BTC --timeframe [TF] --indicators [LIST]`
- `python3 src/fetchers/coinglass_fetcher.py --market --json`
- `python3 src/watchers/cex_monitor.py snapshot`
- `python3 src/formatters/portfolio_sync.py '<JSON>'`

## Outputs

| File | Contents |
|------|----------|
| `output/regime.md` | Regime label, sub-regime, valid setup types, thesis status, data freshness line, derivatives pulse summary |

## Review Gate

Before proceeding to 02_scan, confirm:
- Does the regime label match your read of the market?
- Are the valid setup types correct for current conditions?
- Are any thesis invalidation flags correct?
