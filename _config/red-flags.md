# Red Flags — Automatic Rejection Criteria

**Last Updated:** 2026-03-20

Any single red flag disqualifies a setup. No overrides without explicit human approval at the 03_filter review gate.

This file grows over time via the `/review` learning loop as new failure patterns emerge.

---

## Liquidity Red Flags

- **24h volume < $5M** on the primary exchange — not enough liquidity to enter/exit without slippage
- **Hyperliquid OI < $2M** — perps market too thin for derivatives signals to be meaningful
- **Bid-ask spread > 0.5%** — illiquid, execution will be poor
- **No perps market exists** AND the setup relies on derivatives/squeeze signals — the signal source doesn't exist

## On-Chain Red Flags

- **Smart money is actively selling** (distribution) while the setup is a long — on-chain overrides TA per signal hierarchy
- **Single wallet concentration > 20%** of circulating supply — whale manipulation risk
- **Token unlock within 14 days** releasing >5% of circulating supply — supply dilution incoming
- **Contract is unverified or proxy-upgradeable** with no audit — rug risk

## Technical Red Flags

- **ADX > 40 against the trade direction** — extremely strong trend opposing your trade. Don't fade a freight train.
- **R:R < 3:1 at T3** — doesn't meet the minimum. Find a better entry or pass.
- **Entry is mid-range** (between S/R levels, mid-BB) — no edge. Wait for price to reach a level.
- **OBV divergence against the trade** — volume is telling you the move is fake

## Derivatives Red Flags

- **Funding rate > 0.1% for a LONG entry** — extreme crowding on your side. You're the last buyer.
- **Funding rate < -0.1% for a SHORT entry** — extreme crowding on your side. You're the last seller.
- **L/S ratio > 5:1 in your trade direction** — you're with the crowd at an extreme. Contrarian pressure incoming.

## Regime Red Flags

- **Long setup in risk-off without exceptional on-chain evidence** — requires 3+ funds, >$20M (per thesis accumulation long criteria). Without it, the regime rejects the long.
- **Setup type not listed as "VALID" in current regime.md output** — the regime stage explicitly gates which setup types are allowed today.

## Structural Red Flags

- **Token listed < 7 days ago** — insufficient data for TA or on-chain analysis. No history = no edge.
- **Token is a rebasing/elastic supply token** — standard TA doesn't work. OBV, S/R, and SMA are meaningless.
- **Token has had a >50% drawdown in the last 7 days** AND is a long setup — could be catching a falling knife. Requires extreme oversold (RSI < 20) + accumulation (4+/5) to override.

## Sector Red Flags

- **Meme token long in risk-off** — volume dries up, no institutional flow, pure retail. The thesis explicitly excludes memes in risk-off.
- **AI/Compute sector long when sector is overextended** — per thesis, no active positions until sector cools.

---

## How This File Is Used

1. `find-setups/03_filter` loads this file and checks every candidate against every rule
2. Any match = automatic rejection with logged reason
3. Human can override at the review gate (but must acknowledge the red flag)
4. `/review` pipeline may propose additions to this file based on post-trade analysis

## Adding New Red Flags

When `/review` proposes a new red flag:
1. Add it to the appropriate section above
2. Include the date added and which trade(s) inspired it
3. Git commit with message referencing the review run
