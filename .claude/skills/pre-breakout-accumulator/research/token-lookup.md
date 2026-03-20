# Token Lookup

## Purpose
Resolve a token symbol into chain, contract address, and identify key wallets (founders, team, known entities).

## Primary Method: Nansen General Search

```
Tool: mcp__nansen__general_search
Parameters:
  query: "[TOKEN_SYMBOL]"    # e.g., "ZRO", "SOL"
```

**Extract:**
- Chain (e.g., "ethereum", "solana")
- Contract address
- Any labeled entity wallets associated with the token

## Founder/Team Wallet Identification

This is critical for the pre-breakout skill. Insider wallets often provide the highest-alpha signal (see ZRO case study where CEO buy was the key signal).

**How to identify founder wallets:**
1. Check `token_current_top_holders` for labels containing "Founder", "CEO", "Team", "Treasury"
2. Search Nansen for known team members by name
3. Check project documentation/etherscan for treasury addresses

**Track these wallet categories:**
- Founder/CEO personal wallets
- Team treasury/multisig
- Known investor wallets (from funding rounds)
- Project-associated smart contracts (vesting, staking)

## Native Token Limitation

For native tokens (SOL, ETH, BTC), some Nansen flow tools return limited data. In these cases:
- Entity tracking via `address_historical_balances` still works (primary signal)
- Exchange flow data may be unavailable — score that signal as N/A
- Note the limitation in the report

## Output

After this step you should have:
- **Symbol** + **Chain** + **Contract address**
- **Known entity wallets** (founders, team, key funds)
- **Any limitations** noted for downstream steps
