#!/bin/bash
# Auto Signal Bridge — runs every hour
# Crontab entry:
#   0 * * * * /Users/johnny_main/Developer/projects/titan-terminal-v2/scripts/cron_signal_bridge.sh >> /Users/johnny_main/Developer/projects/titan-terminal-v2/logs/signal_bridge.log 2>&1

cd /Users/johnny_main/Developer/projects/titan-terminal-v2

echo "=== Signal Bridge: $(date -u '+%Y-%m-%dT%H:%M:%SZ') ==="

python3 src/trading/auto_signal_bridge.py run --cron

echo "--- End bridge ---"
echo ""
