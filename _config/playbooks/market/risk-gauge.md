# Risk Gauge

## Purpose
Assess whether the market is in risk-on or risk-off mode.

## How to Use
Say: "Risk gauge" or "Is it risk-on or risk-off?"

Examples:
- "Risk gauge"
- "Risk-on or risk-off?"
- "What's the market risk appetite?"
- "Should I be aggressive or defensive?"

## What It Does

1. Checks BTC dominance trend
2. Reviews stablecoin flows
3. Assesses funding rates
4. Monitors volatility (implied vs realized)
5. Checks smart money positioning

## Output Format

```
## Risk Gauge — [Date]

### Risk Level: [Risk-On / Neutral / Risk-Off]

| Indicator | Reading | Signal |
|-----------|---------|--------|
| BTC Dominance | XX.X% (↑/↓) | Risk-On/Off |
| Stablecoin Flows | +/-$XXM | Risk-On/Off |
| Funding Rates | +/-X.XX% | Risk-On/Off |
| Smart Money | Buying/Selling | Risk-On/Off |
| Fear & Greed | XX | Risk-On/Off |

### Score: X/5 Risk-On Signals

### Interpretation
[What this means for position sizing and strategy]

### Recommended Stance
- **Position Size:** Full / Reduced / Minimal
- **Strategy:** Aggressive / Balanced / Defensive
```

## Risk Indicators

### BTC Dominance
| Trend | Signal |
|-------|--------|
| Rising | Risk-Off (flight to BTC safety) |
| Falling | Risk-On (money flowing to alts) |

### Stablecoin Flows
| Flow | Signal |
|------|--------|
| Outflows from exchanges | Risk-On (deploying to buy) |
| Inflows to exchanges | Risk-Off (parking in safety) |

### Funding Rates
| Rate | Signal |
|------|--------|
| Positive (>0.01%) | Risk-On (longs paying shorts) |
| Negative (<0) | Risk-Off (shorts paying longs) |
| Extremely positive (>0.1%) | Overleveraged, correction risk |

### Smart Money
| Activity | Signal |
|----------|--------|
| Increasing exposure | Risk-On |
| Reducing exposure | Risk-Off |

## Tools Used

1. `get-coin-by-id` (CoinStats) — BTC dominance
2. `token_flows` (Nansen) — Stablecoin flows
3. `smart_traders_and_funds_token_balances` (Nansen) — Fund positioning
4. `smart_traders_and_funds_perp_trades` (Nansen) — Perp activity

## Position Sizing Guide

| Risk Level | Max Position | Stop Distance |
|------------|--------------|---------------|
| Risk-On | 100% of normal | Tight stops OK |
| Neutral | 50-75% of normal | Standard stops |
| Risk-Off | 25-50% of normal | Wide stops or no trades |

## Trading Application

**Risk-On Environment:**
- Full position sizes
- Aggressive entries
- Trade momentum and breakouts
- Hold winners longer

**Risk-Off Environment:**
- Reduced sizes
- Defensive positioning
- Focus on quality setups only
- Quick profit-taking
- Consider hedges
