# MarketInsights Signal Validation

Validate external trading signals from MarketInsights Telegram channel against Titan's on-chain data and technical analysis.

## Purpose

MarketInsights posts chart analysis with directional calls (long/short). This playbook validates whether those signals align with Titan's data-driven analysis before taking a trade.

## Trigger Phrases

| Command | Action |
|---------|--------|
| "What signals came in?" | List recent MarketInsights signals |
| "Check signals" | Same as above |
| "Validate the [TOKEN] signal" | Full validation on specific token |
| "Any signals for [TOKEN]?" | Token-specific signal query |
| "Show me the [TOKEN] signal" | Display + validate specific signal |
| "Validate signal [ID]" | Validate a specific signal by database ID |

## What It Does

### 1. List Recent Signals
When user asks "What signals came in?" or "Check signals":

```
1. Query signals_fetcher.py for recent MarketInsights signals (last 24h)
2. Display as formatted list with:
   - Signal ID
   - Token symbol
   - Direction (LONG/SHORT)
   - Date
   - Whether chart is available
3. Ask user which signal to validate (or validate all)
```

### 2. Full Signal Validation
When validating a specific signal:

```
1. Get signal details from external database
2. Display the chart image (if available) using Read tool
3. Summarize MarketInsights analysis

4. Run Titan Accumulation Check (5 on-chain signals):
   - Exchange flows: token_recent_flows_summary
   - Fresh wallets: token_recent_flows_summary
   - Smart money: token_current_top_holders (smart_money)
   - Top PnL traders: token_recent_flows_summary
   - Whale activity: token_flows or token_who_bought_sold

5. Run Titan Technical Analysis:
   - python3 src/analysis/indicators.py download [TOKEN] --timeframe 4h
   - python3 src/analysis/indicators.py analyze [TOKEN] --indicators rsi,macd,bb,adx,obv

6. Compare: Does MarketInsights direction match Titan verdict?

7. If conflict detected or crowded trade (0/5 or 5/5):
   - Automatically consult mentor for second opinion

8. Determine recommendation using this logic:
   | Signal | Titan TA | On-Chain      | Recommendation        |
   |--------|----------|---------------|-----------------------|
   | Long   | Bullish  | Accumulating  | VALID - Full size     |
   | Long   | Bullish  | Mixed         | VALID - Reduced size  |
   | Long   | Bearish  | Any           | INVALID - Conflicting |
   | Long   | Neutral  | Accumulating  | NEEDS_CONFIRMATION    |
   | Short  | Bearish  | Distributing  | VALID - Full size     |
   | Short  | Bullish  | Any           | INVALID - Conflicting |

9. If signal looks valid, suggest entry/stop/target levels based on:
   - Chart structure
   - Support/resistance from TA
   - Risk/reward calculation

10. Format output using signal_card.py
11. Store validation in signal_validations table
```

## Output Format

```markdown
# [EMOJI] Signal Check: [SYMBOL] [DIRECTION]

## MarketInsights Take
**Direction:** [LONG/SHORT]
**Analysis:** [Their technical commentary summary]
[Chart image displayed if available]

## Titan Validation

### Accumulation Check: [Score]/5 - [Verdict]
- [Exchange flows verdict + detail]
- [Fresh wallets verdict + detail]
- [Smart money verdict + detail]
- [Top PnL traders verdict + detail]
- [Whale activity verdict + detail]

### Technical Analysis: [Verdict]
[Titan's own TA summary with key indicators]

### Chart Review
[Notes from analyzing the chart image]

## Verdict
**Signal vs Titan:** [Agrees/Disagrees]
**Recommendation:** [VALID/INVALID/NEEDS_CONFIRMATION]
**Reason:** [Why]

## If Taking This Trade
**Suggested Entry:** $X
**Stop Loss:** $X
**Target:** $X
**Risk/Reward:** X.XR
```

## Tools Used

| Tool | Purpose |
|------|---------|
| `signals_fetcher.py` | Query external signals database |
| `token_recent_flows_summary` | Quick flow snapshot (exchange, fresh, PnL traders) |
| `token_current_top_holders` | Smart money positioning |
| `token_flows` | Detailed flow history |
| `src/analysis/indicators.py` | Technical analysis |
| `Read tool` | Display chart images |
| `mentor.py` | Second opinion on conflicts |
| `signal_card.py` | Format output |

## Mentor Triggers

The mentor is automatically consulted when:

1. **Signal Conflict:** MarketInsights direction conflicts with Titan TA verdict
   - Long signal + Bearish TA
   - Short signal + Bullish TA

2. **Crowded Trade:** Accumulation score is extreme
   - 5/5 (all bullish) - Consensus trap risk
   - 0/5 (all bearish) - Consensus trap risk

3. **Manual Request:** User adds "with mentor review" to request

## CLI Commands

```bash
# List recent signals
python3 src/fetchers/signals_fetcher.py recent --hours 24

# Get signals for specific token
python3 src/fetchers/signals_fetcher.py token --token BTC

# Show signal details
python3 src/fetchers/signals_fetcher.py show --id 123

# View signal statistics
python3 src/fetchers/signals_fetcher.py stats

# Check validation statistics
python3 src/storage/intelligence.py validation-stats

# List recent validations
python3 src/storage/intelligence.py list-validations
```

## Examples

### Example 1: List signals
```
User: "What signals came in?"

Titan: [Lists recent MarketInsights signals]

# Recent MarketInsights Signals

| ID | Symbol | Direction | Date | Has Chart |
|:--:|:------:|:---------:|:----:|:---------:|
| 258 | CVX | LONG | 2026-01-23 | Yes |
| 259 | AVAX | LONG | 2026-01-23 | Yes |
| 260 | BTC | LONG | 2026-01-24 | Yes |

3 signals shown. Say "Validate the CVX signal" to check one.
```

### Example 2: Validate specific signal
```
User: "Validate the CVX signal"

Titan: [Runs full validation workflow, displays chart, runs accumulation check,
        runs TA, compares verdicts, outputs Signal Check card]
```

### Example 3: Token-specific query
```
User: "Any signals for ETH?"

Titan: [Queries signals for ETH, shows if any exist, offers to validate]
```

## Notes

- MarketInsights signals are **analysis-based**, not exact setups
- They provide direction + technical commentary, not precise entry/stop/target
- Titan adds the quantitative validation layer
- Always check the chart image for context
- Signal database is read-only - Titan stores validations separately
