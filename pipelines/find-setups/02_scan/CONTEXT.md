# Stage: 02_scan — Parallel Universe Scan

## Purpose

Scan the token universe across 4 dimensions to find tokens with signal clusters. This is a broad net — filtering happens in 03_filter.

## Inputs

| Source | File | Layer |
|--------|------|-------|
| Previous stage | `../01_regime/output/regime.md` | 4 (working) |
| Reference | `_config/universe.md` | 3 (factory) |
| Reference | `_config/interpreters/funding-rates.md` | 3 (factory) |
| Reference | `_config/interpreters/accumulation-scores.md` | 3 (factory) |
| Reference | `_config/interpreters/derivatives-signals.md` | 3 (factory) |

## Process

Read `regime.md` to know which setup types are valid today. Only scan for valid types.

Run 4 sub-scans in parallel across the universe defined in `_config/universe.md`:

### Sub-scan A: Technical Analysis Signals

For each token in the universe:
```bash
python3 src/analysis/indicators.py analyze [TOKEN] --timeframe 4h --indicators rsi,macd,bb,obv,adx,sma
```

Flag tokens with signal clusters:
- OBV divergence on 2+ timeframes (distribution or accumulation)
- RSI at extremes (>70 or <25) with ADX confirmation
- BB squeeze (tight bands about to break)
- SMA regime alignment matching the valid setup types

### Sub-scan B: Derivatives Signals

```bash
python3 src/fetchers/coinglass_fetcher.py --scan
```

Plus per-token checks for top hits:
```bash
python3 src/fetchers/coinglass_fetcher.py --token [TOKEN] --derivatives --json
```

Flag tokens with:
- Extreme funding (>0.03% or <-0.03%)
- OI divergence from price
- Crowded L/S ratio (>5:1 either direction)

### Sub-scan C: On-Chain Signals (top 20 by market cap only — Nansen budget)

```
mcp__nansen__smart_traders_and_funds_token_balances:
  chains: ["ethereum", "solana", "base", "arbitrum"]
  includeSmartMoneyLabels: ["Fund", "All Time Smart Trader"]
```

Flag tokens with:
- 2+ funds accumulating simultaneously (>$100k positions, >5% 24h change)
- Smart money net selling on a rallying token (distribution signal)
- Exchange flow spikes (inflows >2x average or outflows >2x average)

### Sub-scan D: Squeeze Signals

```
mcp__nansen__smart_traders_and_funds_perp_trades
```

Group by token. Flag tokens with:
- >70% one-sided activity
- Imbalance ratio 5:1+
- First liquidation cluster <5% from current price

## Scripts Used

- `python3 src/analysis/indicators.py analyze [TOKEN] --timeframe [TF] --indicators [LIST]`
- `python3 src/fetchers/coinglass_fetcher.py --scan`
- `python3 src/fetchers/coinglass_fetcher.py --token [TOKEN] --derivatives --json`
- `python3 src/fetchers/hyperliquid_fetcher.py`

## Outputs

| File | Contents |
|------|----------|
| `output/ta_hits.md` | Tokens with TA signal clusters — which signals, which timeframes |
| `output/deriv_hits.md` | Tokens with extreme funding, OI divergence, crowded positioning |
| `output/onchain_hits.md` | Tokens with smart money movement, exchange flow spikes |
| `output/squeeze_hits.md` | Tokens with imbalance ratios 5:1+, cascade potential |

Each hit file should list: token, signals found, strength rating (weak/moderate/strong), and which valid setup type it matches.

## Review Gate

Before proceeding to 03_filter:
- Are any scans missing data? (Nansen unavailable, Coinglass key missing, etc.)
- Do any hits look like false positives from bad data?
- Any tokens you want to force-include or force-exclude?
