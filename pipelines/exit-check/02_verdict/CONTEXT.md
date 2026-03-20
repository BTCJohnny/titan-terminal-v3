# Stage: 02_verdict — Exit Risk Assessment

## Purpose

Apply decision logic to the 4 signal sources and produce a clear exit risk verdict: HIGH / ELEVATED / CLEAN.

## Inputs

| Source | File | Layer |
|--------|------|-------|
| Previous stage | `../01_signals/output/signals_raw.md` | 4 (working) |

## Process

### Decision Logic

**🔴 HIGH EXIT RISK — all three conditions present:**
- Negative smart_trader net_flow_usd in flow intelligence
- Smart Trader/Fund labels appear as net sellers in who-bought-sold
- Sustained negative SM netflow across multiple hours

**🟡 ELEVATED CAUTION — one or more of:**
- Negative smart_trader net_flow but small magnitude (<$50K)
- Only 1-2 SM wallets selling (single whale rebalancing, not trend)
- SM netflow negative in 1h but positive in 24h (short-term noise)

**🟢 NO EXIT SIGNAL — all conditions clean:**
- Smart trader net_flow_usd positive or flat
- No SM labels in major sellers
- SM netflow stable or positive

### Interpretation Guardrails

- Do NOT treat a single whale selling as a red flag — look for MULTIPLE SM wallets selling
- Do NOT panic on exchange inflows alone — could be staking, lending, market-making
- Do NOT ignore magnitude — $10K of SM selling on a $500M cap token is irrelevant
- Do NOT treat fresh_wallets selling as smart money — often airdrop dumpers or bots
- Scale the signal to the token's daily volume

### Paper Position Cross-Reference

If exit risk is 🔴 HIGH, check for open paper position:
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('data/titan_intelligence.db')
rows = conn.execute(\"SELECT symbol, direction, entry_price, current_pnl_pct FROM paper_positions WHERE symbol LIKE '%[TOKEN]%' AND status='OPEN'\").fetchall()
for r in rows: print(f'{r[0]} {r[1]} @ {r[2]} | PnL: {r[3]}%')
conn.close()
"
```
If a position exists, flag it explicitly in the output.

### Format Output

```
## [🔴/🟡/🟢] Exit Signal: [TOKEN] on [CHAIN]

**Verdict:** [HIGH EXIT RISK / ELEVATED CAUTION / NO EXIT SIGNAL]

**Flow Intelligence:**
- Smart Trader net flow: [value] (negative = selling)
- Whale net flow: [value]
- Exchange net flow: [value]

**Top Smart Money Sellers:**
- [address_label]: sold $[amount]
- [address_label]: sold $[amount]

**SM Netflow Trend:** [direction over recent hours]

**Recent SM DEX Sells:** [count] sells totaling $[amount] in last [timeframe]

**Recommendation:** [action based on verdict]
```

## Outputs

| File | Contents |
|------|----------|
| `output/exit_verdict.md` | Emoji verdict, signal breakdown, paper position flag if relevant, recommendation |

## Post-Output Actions

Save to `results/skill-runs/nansen-exit-signal/[TOKEN]_[YYYY-MM-DD].md`

## Review Gate

- Does the verdict match the weight of evidence?
- If 🔴 HIGH and you have a position: review and decide (tighten stop, partial exit, or hold)
- If data was partial (1+ queries failed): note reduced confidence
