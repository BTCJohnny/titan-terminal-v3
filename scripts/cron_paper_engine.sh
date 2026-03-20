#!/bin/bash
# Paper Trade Engine — runs every 4 hours
# Crontab entry:
#   0 */4 * * * /Users/johnny_main/Developer/projects/titan-terminal-v2/scripts/cron_paper_engine.sh >> /Users/johnny_main/Developer/projects/titan-terminal-v2/logs/paper_engine.log 2>&1

cd /Users/johnny_main/Developer/projects/titan-terminal-v2

# Activate any virtual env if needed (currently using system Python)
# source .venv/bin/activate

echo "=== Paper Engine Tick: $(date -u '+%Y-%m-%dT%H:%M:%SZ') ==="

python3 src/trading/paper_engine.py tick --cron

echo "--- End tick ---"
echo ""
