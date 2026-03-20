# Stage: 04_derivatives — Derivatives Intelligence + Perps Positioning

## Purpose

Map the derivatives landscape: funding rates, open interest, liquidation zones, L/S ratios, smart money perp positions. Identifies mechanical pressure (squeeze setups, liquidation cascades) and crowd positioning.

## Inputs

| Source | File | Layer |
|--------|------|-------|
| Previous stage | `../01_resolve/output/identity.md` | 4 (working) |
| Reference | `_config/interpreters/derivatives-signals.md` | 3 (factory) |
| Reference | `_config/interpreters/funding-rates.md` | 3 (factory) |

## Process

### Step 1: Coinglass Derivatives (no Nansen credits)

```bash
python3 src/fetchers/coinglass_fetcher.py --token [TOKEN] --price [PRICE] --derivatives --json
```

If COINGLASS_API_KEY is not set or call fails, skip — note "Derivatives data unavailable" and proceed to Step 2.

From JSON output, extract using `_config/interpreters/derivatives-signals.md`:
- **Funding rate:** cross-exchange average, bias, annualized cost
- **Open Interest:** current, 24h change %, trend (rising/falling/flat), exchange momentum
- **L/S Ratio:** global account, top trader account + position ratios, smart money lean
- **Liquidation activity:** 24h totals, long/short breakdown, L/S ratio, cascade risk
- **Options max pain:** nearest expiry target, distance from price (BTC/ETH only)
- **Liquidity Grab Fade:** detect if conditions align for a mechanical snap-back

### Step 2: Smart Money Perps Positioning (Nansen — check cache first)

```
mcp__nansen__token_current_top_holders: tokenAddress "[TOKEN]", mode "perps", labelType "smart_money"
```

If the token has no perps market, skip and note "No perps data available."

Extract: net long vs short by smart money, trader count each side, any extreme positioning (>5:1 ratio).

### Step 3: Combined Derivatives Reading

Synthesize both sources using `_config/interpreters/derivatives-signals.md`:
- Is funding extreme? → crowding risk
- Is OI expanding while L/S is extreme? → cascade risk
- Do top trader positions diverge from global accounts? → smart money vs retail
- Does OI diverge from price? → directional signal
- What are smart money perps traders positioned? → directional conviction

### Standalone mode (`/liquidity [TOKEN]`)

When invoked via `/liquidity`, run only this stage using Coinglass data (skip Nansen perps to save credits). Render the liquidity report format directly:
- Liquidation activity table (24h/12h/4h/1h)
- Options max pain (BTC/ETH only)
- Options sentiment (BTC/ETH only)
- Liquidity Grab Fade detection

## Scripts Used

- `python3 src/fetchers/coinglass_fetcher.py --token [TOKEN] --price [PRICE] --derivatives --json`
- `python3 src/storage/nansen_cache.py check/store`

## Outputs

| File | Contents |
|------|----------|
| `output/derivatives.md` | Funding, OI, L/S ratios, liquidation activity, options data (BTC/ETH), Liquidity Grab Fade detection, 2-3 sentence synthesis |
| `output/perps.md` | Smart money perp positioning, net long/short, trader counts, contrarian signal assessment |

## Review Gate

- Any extreme readings that demand attention? (funding >0.1%, L/S >5:1)
- Does the derivatives picture confirm or conflict with on-chain?
- Is a Liquidity Grab Fade setup detected? (actionable if so)
