# Macro Context

## Purpose

A squeeze needs a catalyst to trigger. This step assesses whether the macro environment supports or opposes the squeeze direction, and identifies potential catalysts.

## Context Checks

### 1. CEX Flow Direction

**Tool:** `mcp__nansen__token_recent_flows_summary` with `tokenId`

| Flow Direction | For Short Squeeze | For Long Squeeze |
|---------------|-------------------|------------------|
| Net outflows (leaving CEX) | Supportive — supply squeeze + perps squeeze | Opposing — spot accumulation contradicts long squeeze |
| Net inflows (to CEX) | Opposing — distribution backdrop | Supportive — selling pressure + perps squeeze |
| Neutral | Neutral | Neutral |

**Key insight:** The most powerful setups have **spot disagreeing with perps**. If spot is distributing but perps are heavily short, the divergence creates higher conviction — one side is wrong.

### 2. BTC Momentum

**Tool:** `python3 src/analysis/indicators.py report BTC` (CLI)

For altcoin squeezes, BTC direction matters:
- **BTC pumping** → Altcoin shorts get squeezed (beta correlation)
- **BTC dumping** → Altcoin longs get squeezed
- **BTC ranging** → Need token-specific catalyst

Check:
- BTC trend direction (4h and daily)
- Recent momentum (RSI, MACD)
- Key levels (breaking resistance = catalyst for alt short squeezes)

### 3. Funding Rate

**Tool:** Already available from positioning scan data

| Funding | Squeeze Direction | Signal |
|---------|-------------------|--------|
| Highly negative | Short squeeze | Shorts paying — pressure building on shorts |
| Slightly negative | Short squeeze | Mild short pressure |
| Neutral | Either | No directional pressure |
| Slightly positive | Long squeeze | Mild long pressure |
| Highly positive | Long squeeze | Longs paying — pressure building on longs |

Funding rate that aligns with squeeze direction = pressure building = higher conviction.

### 4. Recent Smart Money Trades

**Tool:** `mcp__nansen__smart_traders_and_funds_perp_trades` with `tokenId`

Check:
- Are **new** positions being opened on the crowded side? (adding fuel)
- Are positions being **closed** on the crowded side? (unwinding = squeeze may not materialize)
- Are any traders **switching sides**? (smart money front-running the squeeze)
- Recent trade timestamps — is the crowding getting worse or better?

### 5. Spot Market Agreement

**Tool:** `mcp__nansen__token_current_top_holders` with `mode: "spot"`, `labelType: "smart_money"`

Compare spot vs perps positioning:
- **Spot accumulating + Perps short** = Divergence → highest conviction short squeeze
- **Spot distributing + Perps long** = Divergence → highest conviction long squeeze
- **Spot and perps agree** = Consensus → lower squeeze conviction (crowded side may be right)

### 6. Divergence Assessment

The **holy grail** of squeeze setups: spot and perps disagree.

| Spot | Perps | Interpretation |
|------|-------|----------------|
| Accumulating | Heavily short | **Max squeeze conviction** — spot buyers will push price into liquidations |
| Distributing | Heavily short | **Reduced conviction** — squeeze is fighting the spot trend |
| Accumulating | Heavily long | **Reduced conviction** — both sides agree, crowded long may be right |
| Distributing | Heavily long | **Max squeeze conviction** — spot sellers will push price into liquidations |

## Catalyst Checklist

Score each factor:

| Factor | Supports Squeeze | Neutral | Opposes Squeeze |
|--------|-----------------|---------|-----------------|
| CEX flows | +1 | 0 | -1 |
| BTC momentum | +1 | 0 | -1 |
| Funding alignment | +1 | 0 | -1 |
| New positions still opening | +1 | 0 | -1 |
| Spot divergence | +1 | 0 | 0 |

**Total: -4 to +5**
- +3 to +5: Strong catalyst environment
- 0 to +2: Needs specific trigger
- Negative: Macro opposes squeeze — reduced conviction

## Output

After this step you should have:

```
Macro Context:
- CEX Flows: [Supportive/Opposing/Neutral] — [detail]
- BTC Momentum: [Supportive/Opposing/Neutral] — [detail]
- Funding Rate: [Supportive/Opposing/Neutral] — [rate]
- New Positions: [Still opening/Closing] — [detail]
- Spot Divergence: [Yes/No] — [detail]
- Catalyst Score: X/5
- Key Insight: [The "So what?" synthesis]
```
