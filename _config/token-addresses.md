# Token Addresses — Fresh Wallet Scan Reference

**Last Updated:** 2026-04-06

Addresses for `token_current_top_holders` calls. Avoids burning Nansen credits on `general_search` lookups.

## Ethereum

| Token | Address | Sector |
|-------|---------|--------|
| AAVE | 0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9 | DeFi |
| LINK | 0x514910771af9ca656af840dff83e8264ecf986ca | Oracle |
| PENDLE | 0x808507121b80c02388fad14726482e061b8da827 | DeFi |
| MKR | 0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2 | DeFi |
| UNI | 0x1f9840a85d5af5bf1d1762f925bdaddc4201f984 | DeFi |
| ONDO | 0xfAbA6f8e4a5E8Ab82F62fe7C39859FA577269BE3 | RWA |
| ZRO | 0x6985884c4392d348587b19cb9eaaf157f13271cd | L0/Infra |
| LDO | 0x5a98fcbea516cf06857215779fd812ca3bef1b32 | DeFi |
| WETH | 0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2 | L1 |
| ARB | 0xb50721bcf8d664c30412cfbc6cf7a15145234ad1 | L2 |
| EIGEN | 0xec53bf9167f50cdeb3ae105f56099aaab9061f83 | Restaking |
| RENDER | 0x6de037ef9ad2725eb40118bb1702ebb27e4aeb24 | AI/Compute |
| WLD | 0x163f8c2467924be0ae7b5347228cabf260318753 | DePIN |
| INJ | 0xe28b3b32b6c345a34ff64674606124dd5aceca30 | L1 |
| PYTH | 0xefb97ebc02e5e8f66612e79cf94ef49bee3b6ef0 | Oracle |

## Base

| Token | Address | Sector |
|-------|---------|--------|
| AERO | 0x940181a94a35a4569e4529a3cdfb74e38fd98631 | DeFi |

## Solana

| Token | Address | Sector |
|-------|---------|--------|
| JUP | JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN | DeFi |
| BONK | DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263 | Meme |
| WIF | EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm | Meme |

## Notes

- BTC, ETH, SOL are native tokens — use wrapped versions (WBTC, WETH) or skip for fresh wallet scan (native token holders are dominated by DeFi protocols)
- HYPE: native on Hyperliquid/HyperEVM — check if `token_current_top_holders` supports hyperevm chain. Address TBD.
- SUI, SEI, NEAR, FTM, AVAX, STX: native L1 tokens on their own chains. Use general_search to find wrapped/bridged versions if needed, or skip (low priority for fresh wallet scan).
- Tokens not listed: use `general_search` (1 credit) to find address, then add to this file.
- **Keep this file updated** when tokens enter/leave the universe.
