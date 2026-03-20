# Token Lookup

## Purpose
Resolve a token symbol into chain, contract address, and CoinStats ID needed by downstream tools.

## Primary Method: Nansen General Search
```
mcp__nansen__general_search: query "[TOKEN_SYMBOL]"
```

**Parse the result:**
- Extract `chain` (e.g., "solana", "ethereum", "base")
- Extract `contractAddress`
- If multiple results, pick highest market cap

## CoinStats ID Convention

CoinStats uses lowercase-hyphenated names:
- Simple: `bitcoin`, `ethereum`, `solana`, `chainlink`
- Multi-word: `pyth-network`, `internet-computer`, `the-graph`
- Suffixed: `wrapped-bitcoin`, `lido-dao`
```
mcp__coinstats__get-coin-by-id: coinId "[lowercase-hyphenated-name]"
```

## Common Gotchas

| Issue | Solution |
|-------|----------|
| Multi-chain tokens (USDC on ETH, SOL, BASE) | Pick primary/highest-volume chain |
| Native tokens (BTC, ETH, SOL) | Some Nansen flow tools limited — note in card |
| Wrapped versions (WETH, WBTC) | Use wrapped address for on-chain tools |
| Token not found in Nansen | Fall back to CoinStats only; note "on-chain data unavailable" |

## Output

After this step you should have:
- **Symbol:** e.g., "PYTH"
- **Chain:** e.g., "solana"
- **Contract address:** e.g., "HZ1Jov...BCt3"
- **CoinStats ID:** e.g., "pyth-network"
