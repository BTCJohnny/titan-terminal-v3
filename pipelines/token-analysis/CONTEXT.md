# Pipeline: token-analysis

> Deep analysis of a single token. Answers: "Should I buy, sell, or ignore this right now — and why?"

## Entry Points

- `/analyze [TOKEN]` — one deep dive
- `find-setups/04_analyze` — called per candidate during the daily scan
- `/ta [TOKEN]` — runs only stage 02_technical
- `/liquidity [TOKEN]` — runs only stage 04_derivatives

## Flow

```
01_resolve → [02_technical + 03_onchain + 04_derivatives] (parallel) → 05_verdict
```

Stages 02, 03, and 04 are fully independent after 01 completes — run them in parallel.

## Stage Map

| Stage | Purpose | Key Output |
|-------|---------|------------|
| 01_resolve | Token identity + market snapshot | `identity.md` — chain, address, price, cap, CoinStats ID |
| 02_technical | Multi-timeframe TA via ta-analyst subagent | `ta_verdict.md` — direction, confidence, key levels, R:R |
| 03_onchain | On-chain flows + accumulation scoring | `flows.md` + `accumulation.md` — who's buying/selling, 5-signal score |
| 04_derivatives | Derivatives intelligence + perps positioning | `derivatives.md` + `perps.md` — funding, OI, L/S, liquidations, smart money perps |
| 05_verdict | Synthesis + trade card | `trade_card.md` — directional call, thesis, setup levels |

## Signal Hierarchy

```
On-Chain (03) > Perps (04) > Derivatives (04) > Technical (02)
```

When signals conflict, higher-weight sources win. See `_config/signal-hierarchy.md` for full decision rules.

## Nansen Cache

Before any Nansen MCP call, check the cache:
```bash
python3 src/storage/nansen_cache.py check --tool [TOOL] --token [TOKEN] --params '[JSON]'
```

Cache TTLs: flows 6h, on-chain holders 12h, perps 1h, identity search 24h.

On `CACHE_HIT`, use stored response. On `CACHE_MISS`, fetch live then store:
```bash
python3 src/storage/nansen_cache.py store --tool [TOOL] --token [TOKEN] --params '[JSON]' --response '[JSON]'
```

## Nansen Budget

Full token-analysis costs ~15-20 credits. Track running total. See CLAUDE.md for credit table.
