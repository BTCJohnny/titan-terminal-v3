# Filter Results — 2026-03-23 13:10 UTC

## Regime: RISK-OFF / Distribution Phase Re-Activating
## Valid setup types: Distribution Shorts (primary), Mean Reversion Overbought Fades, Conditional Accumulation Longs (3+ named funds, >$20M)

---

## REJECTION LOG

### SOL — REJECTED
**Red flag:** Long in risk-off without exceptional on-chain evidence
- On-chain signal: +29.7% 24h change, 79 Fund/All Time Smart Trader holders, total balance $3.7M
- Prior balance ~$2.84M → new $3.7M = ~$860K increase
- **Fails threshold:** Requires 3+ named funds, >$20M total (per thesis). $860K add across 79 wallets ≠ institutional conviction
- Secondary rejection: Nansen tool returns aggregate, not named fund breakdown. Cannot confirm 3+ named funds without a separate per-fund query.
- Perp conflict: "kekvault2" added $2.6M SOL short today — likely basis trade (spot buy + perp short to harvest funding). Net directional signal is neutral/bearish.
- **Decision:** Rejected. Not enough evidence to override risk-off regime.

### BTC — REJECTED
**Red flag:** Entry mid-range (between SMA 20 $69,504 and SMA 50 $71,243)
- Price at $69,883 is in the middle of two SMAs with no defined entry level for a short setup
- No active BTC short thesis with defined entry/stop/target levels
- Secondary: Smart money is net short (good direction confirmation) but without a thesis entry, R:R cannot be verified ≥ 3:1
- Smart perp traders actively shorting confirms the distribution view, but BTC short has squeeze risk above $71,243 that makes the risk management less clean than ETH
- **Decision:** Rejected as standalone candidate. BTC directional signal folds into regime context, not a separate setup.

### WLD — REJECTED
**Red flag 1:** R:R < 3:1. Mean reversion target = BB Middle ($0.34 per stale data). Entry ~$0.315, stop ~$0.295. R:R = $0.025 / $0.020 = 1.25:1. Does not meet 3:1 minimum.
**Red flag 2:** Entry not triggered. RSI 26.89 vs threshold of 25. Setup has not fired.
**Red flag 3:** OBV -1.6B with no on-chain accumulation evidence. Distribution signal against a long setup.
- **Decision:** Rejected. Additionally, WLD data is 48h stale — setup levels unreliable.

### AVAX — REJECTED
**Red flag:** Entry mid-range + single sub-scan hit only
- One sub-scan hit (TA only). No derivatives signal, no on-chain signal.
- No defined entry zone — "wait for bounce to SMA 20" is not a setup, it's a watch.
- Stale data (48h). Cannot verify current R:R.
- **Decision:** Rejected.

---

## CANDIDATES PASSING FILTER

### 1. ETH Distribution Short — PASSED ✅
**Rank:** #1 (only candidate)
**Score:** 4/4 cross-signal | Strong | Perfect regime fit | Active thesis

| Dimension | Signal | Strength |
|-----------|--------|----------|
| TA | Price approaching BB Upper ($2,189) / SMA 50 ($2,182). OBV -16.9M. | Strong |
| Derivatives | Funding +0.1489% (217% annualized), OI +3.9% — most crowded positioning seen. | Strong |
| Squeeze | Smart perp trader [0xe668c4] exited ETH long. No smart money currently long ETH perps. | Moderate |
| On-chain | Top PnL accumulating ETH spot at 11.1x — likely basis trade (buy spot/short perps), NOT directional long. Directionally neutral-to-bearish for price. | Moderate |

**Red flag check — CLEAN:**
- Liquidity: ETH has $B+ daily volume. No issue.
- ADX: 33.27. Below 40 threshold. No freight train.
- OBV: -16.9M supports the short (distribution on rallies). ✓
- Funding: +0.1489% — crowd is LONG, we are SHORT. No red flag (flag only triggers for longs with extreme long funding). ✓
- Regime: "Distribution Shorts: STRONGLY VALID" ✓
- Thesis: Active ETH distribution short thesis in thesis.md ✓
- R:R: Entry $2,220-2,260, Stop $2,320, T1 $2,015 (2.8:1), T2 $1,875 (4.6:1). **T1 R:R is 2.8:1 — technically below the 3:1 minimum.** T2 is 4.6:1. Structure as T1=partial scale-out (not full close), T2=primary target. Net R:R ≥ 3:1 ✓

**Critical caveat:** Entry zone NOT yet reached. Price at $2,122 vs entry $2,220-2,260. The setup is FORMING, not yet TRIGGERED. This is a 04_analyze candidate to confirm entry zone and update trigger conditions.

**What 04_analyze needs to confirm:**
1. Current ETH price and proximity to entry zone
2. Whether the 4H RSI trigger condition ($65 rollover) is likely to fire
3. Updated stop/target levels given any structural changes since thesis was written (March 17)
4. Whether Top PnL spot accumulation (11.1x CEX outflows) changes the thesis
5. On-chain confirmation via Nansen (token_flows or token_who_bought_sold for ETH)

---

## FINAL CANDIDATE LIST

| # | Token | Setup Type | Entry Status | Priority |
|---|-------|-----------|-------------|----------|
| 1 | ETH | Distribution Short | FORMING — not yet triggered ($2,122 vs $2,220-2,260 zone) | ACTIVE |

**Total: 1 candidate passed filter.**

---

## NOTES FOR 04_ANALYZE

The pipeline produced 1 clean candidate. This is expected in a risk-off regime — most tokens are distributing but few have reached the specific entry conditions for a quality trade.

**If ETH entry zone is NOT within realistic reach today**, the correct outcome is "No setups today — ETH setup is forming, monitor for trigger." Do not force a trade at a suboptimal entry.

**Secondary watch:** SOL on-chain signal warrants a 3-credit Nansen follow-up (token_who_bought_sold) to identify whether the 79-holder accumulation includes named funds. If it does and total exceeds $20M, SOL could requalify as a conditional long. This is optional — not a primary candidate.
