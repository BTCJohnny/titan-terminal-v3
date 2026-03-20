---
name: nansen-exit
description: Check if smart money is exiting a token you hold
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - mcp__nansen
---

# /nansen-exit

Check the Nansen Exit Signal for a token to determine if smart money is distributing.

## Usage

`/nansen-exit [TOKEN] [CHAIN]`

- **TOKEN**: Contract address or symbol (e.g., ETH, 0x...)
- **CHAIN**: Optional, defaults to ethereum (supports: ethereum, solana, base, arbitrum, polygon, bnb, optimism, avalanche)

---

## Execution

This command delegates to the **nansen-exit-signal** skill. Load the skill from `.claude/skills/nansen-exit-signal/SKILL.md` and follow its process exactly.

### Steps

1. **Token Resolution** — If TOKEN is a symbol (not an address), use Nansen MCP `general_search` to resolve it to a contract address (0 credits).

2. **Load Skill** — Read `.claude/skills/nansen-exit-signal/SKILL.md` for interpretation logic and decision thresholds.

3. **Run 4 MCP Queries in Parallel** (4 credits total):
   - `token_recent_flows_summary` — flow intelligence
   - `token_who_bought_sold` — seller breakdown (limit 20)
   - `token_flows` — SM netflow trend
   - `token_dex_trades` — recent SM trades (limit 20)

4. **Apply Decision Logic** — Use the skill's verdict framework (🔴 HIGH / 🟡 ELEVATED / 🟢 CLEAN) to determine exit risk level.

5. **Present Verdict** — Format output per the skill's output template.

6. **Cross-Reference Paper Positions** — If exit risk is 🔴 HIGH, check for an open paper trading position:
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

### Auto-Save

Save the exit signal report to: `results/skill-runs/nansen-exit-signal/[TOKEN]_[YYYY-MM-DD].md`

---

## Do NOT

- Run this without the skill loaded — the interpretation logic lives there
- Call more than 20 results per query — keep MCP credit usage reasonable (4 credits total)
- Present raw MCP JSON to the user — always interpret and format per the skill template
- Make trading decisions — present the signal and recommendation, let John decide

---

## Error Handling

- If token resolution fails, ask the user for the contract address directly
- If any single MCP query fails, proceed with the remaining 3 — partial data is better than no data
- If all queries fail, report "Nansen data unavailable" and suggest checking again later
- Note which queries had data issues so the user knows the signal was partial

## Formatting Rules

- Verdict first — lead with the emoji and risk level
- Quantify everything — dollar amounts, wallet counts, trade counts
- Use the skill's persona: contrarian, quantified, no hedging
- Bold all verdicts and key metrics
