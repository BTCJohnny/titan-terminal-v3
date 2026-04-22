#!/bin/bash
# Titan Terminal v2 — Snapshot Cron Wrapper
# Runs Coinglass or Nansen snapshot with timestamped log output.
#
# Usage:
#   scripts/snapshot_cron.sh coinglass
#   scripts/snapshot_cron.sh nansen

set -euo pipefail

PROJECT_DIR="/Users/johnny_main/Developer/projects/titan-terminal-v2"
PYTHON="/opt/homebrew/bin/python3"
LOG_DIR="$PROJECT_DIR/logs/cron"
TIMESTAMP=$(date -u +"%Y-%m-%d_%H")

cd "$PROJECT_DIR"

case "${1:-}" in
    coinglass)
        LOG_FILE="$LOG_DIR/${TIMESTAMP}-coinglass.log"
        echo "=== Coinglass Snapshot $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" >> "$LOG_FILE"
        $PYTHON src/fetchers/coinglass_fetcher.py --snapshot-all --json >> "$LOG_FILE" 2>&1
        echo "Exit: $?" >> "$LOG_FILE"
        echo "=== Sync to Cowork ===" >> "$LOG_FILE"
        $PYTHON src/storage/intelligence.py sync >> "$LOG_FILE" 2>&1
        ;;
    nansen)
        LOG_FILE="$LOG_DIR/${TIMESTAMP}-nansen.log"
        echo "=== Nansen Snapshot $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" >> "$LOG_FILE"
        $PYTHON src/fetchers/nansen_fetcher.py --snapshot-all --json >> "$LOG_FILE" 2>&1
        echo "Exit: $?" >> "$LOG_FILE"
        echo "=== Sync to Cowork ===" >> "$LOG_FILE"
        $PYTHON src/storage/intelligence.py sync >> "$LOG_FILE" 2>&1
        ;;
    *)
        echo "Usage: $0 {coinglass|nansen}"
        exit 1
        ;;
esac
