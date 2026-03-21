# Scan Universe

**Last Updated:** 2026-03-20

## Core Pair
- **BTC** — regime barometer, always monitored
- **ETH** — second barometer, active short thesis

## Scan Universe: Top 30 Hyperliquid by Open Interest

The scan universe is dynamic — rebuilt weekly from the top 30 tokens by open interest on Hyperliquid. High OI means liquid perps markets, which means the derivatives signals (funding, L/S, liquidation maps) are meaningful.

### How to Refresh

```bash
python3 src/fetchers/hyperliquid_fetcher.py
```

Parse the output and update the list below. Tokens drop off when they leave the top 30 by OI. Tokens get added when they enter.

### Current Universe (as of 2026-03-20)

BTC, ETH, SOL, HYPE, DOGE, XRP, AVAX, LINK, SUI, ARB, OP, PEPE, WIF, TIA, SEI, INJ, JUP, ONDO, PYTH, STX, NEAR, FTM, AAVE, MKR, PENDLE, TAO, RENDER, ZRO, AERO, WLD

### Scan Scope by Stage

| Stage | What gets scanned | Why |
|-------|------------------|-----|
| 02_scan sub-A (TA) | Full universe (32 tokens) | TA is cheap — just Python math on cached OHLCV |
| 02_scan sub-B (Derivatives) | Full universe | Coinglass scan endpoint covers all at once |
| 02_scan sub-C (On-chain) | Top 20 by market cap only | Nansen credits are expensive — focus on liquid tokens |
| 02_scan sub-D (Squeeze) | Full universe | Single Nansen perp call covers all |

### Exclusions

Tokens that should never appear in scan results regardless of signals:
- Stablecoins (USDT, USDC, DAI, etc.)
- Wrapped tokens (WBTC, WETH, etc.)
- Tokens with <$1M daily volume on Hyperliquid (no liquidity to trade)

### Sector Tags

Used by 03_filter for thesis alignment:

| Sector | Tokens |
|--------|--------|
| L1 / Infrastructure | BTC, ETH, SOL, SUI, SEI, NEAR, FTM, AVAX, STX |
| DeFi / Yield | AAVE, MKR, PENDLE, AERO, JUP |
| L2 | ARB, OP |
| Oracle / Data | LINK, PYTH |
| AI / Compute | TAO, RENDER |
| Meme | DOGE, PEPE, WIF, WLD |
| Modular | TIA |
| DePIN / New | HYPE, ONDO, INJ, ZRO |
