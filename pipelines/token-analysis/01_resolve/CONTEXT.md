# Stage: 01_resolve — Token Identity + Market Snapshot

## Purpose

Resolve the token's chain, contract address, and CoinStats ID, then fetch a current market snapshot. This data is required by all subsequent stages.

## Inputs

| Source | File | Layer |
|--------|------|-------|
| User input | Token symbol (e.g., "ETH", "HYPE", "ZRO") | — |

## Process

### Step 1: Resolve Token Identity

Check Nansen cache first:
```bash
python3 src/storage/nansen_cache.py check --tool general_search --token [TOKEN] --params '{"query":"[TOKEN]"}'
```

On `CACHE_MISS`:
```
mcp__nansen__general_search: query "[TOKEN]"
```
Then store the response.

Extract:
- Token name and symbol
- Chain (ethereum, solana, base, arbitrum, etc.)
- Contract address

Determine the CoinStats ID (lowercase-hyphenated: "ethereum", "bitcoin", "pyth-network", "chainlink").

If the token cannot be found, stop the pipeline: "Could not resolve [TOKEN]. Check the symbol and try again."

### Step 2: Market Snapshot

```
mcp__coinstats__get-coin-by-id: coinId "[coinstats-id]"
```

Extract: price, market cap, rank, 24h volume, FDV, circulating supply, total supply, 24h change %, 7d change %.

## Scripts Used

- `python3 src/storage/nansen_cache.py check/store`

## Outputs

| File | Contents |
|------|----------|
| `output/identity.md` | Token name, symbol, chain, contract address, CoinStats ID, price, market cap, rank, volume, FDV, supply, 24h/7d change |

## Review Gate

- Is the correct token resolved? (watch for symbol collisions — e.g., "LINK" on multiple chains)
- Is the price data current?
