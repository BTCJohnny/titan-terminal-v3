# Nansen API Budget

**Last Updated:** 2026-03-20

## Session Limit: 100 Credits

Track usage across all Nansen MCP calls in a session. Report running total after each Nansen-using stage.

| Threshold | Action |
|-----------|--------|
| 80 credits | ⚠️ Warn: "80/100 Nansen credits used this session." |
| 100 credits | 🛑 Stop: "100 credit limit reached. Approve more? (Y to continue, N to stop on-chain analysis)" |
| If approved | Continue in 10-credit increments, prompting at each |

**Per-analysis cap:** No single `/analyze` or pipeline run should use more than 20 credits without prompting.

---

## Credit Costs Per Tool

### 1 Credit
| Tool | Use For |
|------|---------|
| `general_search` | Token resolution (symbol → chain + address) |
| `transaction_lookup` | Single transaction details |
| `address_transactions` | Wallet transaction history |

### 2 Credits
| Tool | Use For |
|------|---------|
| `token_flows` | Smart money netflow trend |
| `token_recent_flows_summary` | Flow intelligence by segment (1d or 7d) |
| `token_ohlcv` | On-chain price history |
| `token_transfers` | Token transfer history |
| `address_portfolio` | Wallet portfolio snapshot |
| `address_historical_balances` | Entity position tracking over time |
| `address_counterparties` | Wallet interaction partners |
| `address_related_addresses` | Linked wallet discovery |

### 3 Credits
| Tool | Use For |
|------|---------|
| `token_current_top_holders` | Top holders (smart money or top 100) |
| `token_who_bought_sold` | Buyer/seller breakdown by label |
| `token_pnl_leaderboard` | Top PnL traders for a token |
| `token_quant_scores` | Quantitative scoring |
| `wallet_pnl_for_token` | Single wallet PnL on a specific token |
| `wallet_pnl_summary` | Wallet overall PnL |
| `hyperliquid_leaderboard` | HL top traders |

### 5 Credits
| Tool | Use For |
|------|---------|
| `smart_traders_and_funds_token_balances` | Broad smart money positioning scan |
| `smart_traders_and_funds_perp_trades` | Smart money perp activity scan |
| `token_discovery_screener` | Token discovery for hunt workflows |
| `token_dex_trades` | Recent DEX trade activity |
| `token_recent_flows_summary` (multi-asset) | Multi-token flow scan |
| `growth_chain_rank` | Chain growth ranking |
| `nansen_score_top_tokens` | Top scored tokens |

---

## Typical Credit Usage by Pipeline

| Pipeline / Command | Typical Credits | Notes |
|-------------------|----------------|-------|
| `/analyze [TOKEN]` | 15-20 | Full trade card: identity (1) + flows 1d+7d (4) + holders ×2 (6) + perps (3) = 14 minimum |
| `/nansen-exit [TOKEN]` | 4 | Cheapest on-chain check: 4 parallel queries at 1 credit each |
| `/find-setups` (full) | 40-80 | Regime (0) + scan on-chain (5-10) + squeeze scan (5) + analyze 1-3 candidates (15-60) |
| `/hunt-accumulation` | 20-40 | Discovery screener (5) + entity scans + flow checks per candidate |
| `/hunt-squeezes` | 10-20 | Broad perp scan (5) + deep scan top 3 candidates |

## Cache Rules

Before any Nansen call, check cache first:
```bash
python3 src/storage/nansen_cache.py check --tool [TOOL] --token [TOKEN] --params '[JSON]'
```

| Data Type | Cache TTL |
|-----------|----------|
| Flow summaries (1d, 7d) | 6 hours |
| On-chain holders (smart money, top 100) | 12 hours |
| Perps holders | 1 hour |
| Token identity / general search | 24 hours |

On `CACHE_HIT`: use stored response (0 credits). On `CACHE_MISS`: fetch live, then store immediately.

---

## Cost-Saving Tips

1. **Run `/nansen-exit` before `/analyze`** — if exit risk is 🟢 CLEAN, the 4-credit check saved you 15 credits of unnecessary deep analysis
2. **Cache is your friend** — if you ran `/analyze ETH` 2 hours ago, most data is still cached. Only perps (1h TTL) needs refreshing.
3. **On-chain scan in /find-setups uses top 20 only** — don't scan the full 32-token universe on-chain. TA and derivatives scans are free.
4. **Batch entity checks** — `smart_traders_and_funds_token_balances` (5 credits) gives broad positioning across all tokens. Better than calling `token_current_top_holders` (3 credits) per token.
