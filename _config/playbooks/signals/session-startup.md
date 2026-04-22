# Session Startup: Watchlist Review

Run this workflow at the start of every Titan Trading session to review monitored signals and tokens.

## Trigger Phrases

| Command | Action |
|---------|--------|
| "Start session" | Full startup review |
| "Morning check" | Same as above |
| "What's on the watchlist?" | List active items |
| "Any watchlist updates?" | Check for changed analysis |
| "Review watchlist" | Full review with re-analysis |

## What It Does

### 1. Quick Summary (Default)
When user starts a session:

```
1. Run: python3 src/watchers/watchlist_monitor.py summary
2. Show active watchlist items grouped by source
3. Highlight any items with changed analysis
4. List high-priority items (priority >= 7)
```

### 2. Full Review (On Request)
When user says "Review watchlist" or at start if items need review:

```
1. Get items needing review (not checked in 12+ hours)
2. For each item:
   a. Run quick accumulation check (token_recent_flows_summary)
   b. Get latest price
   c. Compare to original thesis
   d. Note any significant changes
3. Update watchlist items with current data
4. Report changes to user
5. Suggest actions for changed items
```

### 3. Check for New Signals
Also check for new incoming signals:

```
1. Run: python3 src/fetchers/signals_fetcher.py recent --hours 24
2. List any signals not yet validated
3. Offer to validate new signals
```

## Output Format

```markdown
# Good [morning/afternoon], Titan's Watchlist Review

## Summary
**Active Items:** X | **High Priority:** X | **Analysis Changed:** X

## High Priority Items
[List of priority >= 7 items with current status]

## Items with Changed Analysis
[List of items where analysis differs from original]

## New Signals (Last 24h)
[List of unvalidated signals if any]

## Suggested Actions
- [Actionable items based on review]
```

## CLI Commands

```bash
# Quick summary
python3 src/watchers/watchlist_monitor.py summary

# Full review
python3 src/watchers/watchlist_monitor.py review

# Check specific symbol
python3 src/watchers/watchlist_monitor.py check HYPE

# List items with changed analysis
python3 src/watchers/watchlist_monitor.py changes

# Cron mode (save to file)
python3 src/watchers/watchlist_monitor.py review --cron
```

## Cron Setup

For automated monitoring, add to crontab:

```bash
# Check watchlist every 6 hours
0 */6 * * * cd /Users/johnny_main/Developer/projects/titan-terminal-v3 && python3 src/watchers/watchlist_monitor.py review --cron

# Check for new signals every 4 hours
0 */4 * * * cd /Users/johnny_main/Developer/projects/titan-terminal-v3 && python3 src/fetchers/signals_fetcher.py recent --hours 4 >> signals/dashboards/new_signals.log
```

## Workflow Integration

This playbook connects to:
- `_config/playbooks/signals/market-insights.md` — For validating new signals
- `_config/playbooks/nansen/accumulation-check.md` — For re-analyzing watchlist items
- Trade setup workflow — For converting valid signals to trades

## Notes

- Session review is non-blocking: just reports status, doesn't auto-take actions
- User decides which items to re-analyze or act on
- High priority items should be reviewed even if recently checked
- Changed analysis items require manual verification before action
