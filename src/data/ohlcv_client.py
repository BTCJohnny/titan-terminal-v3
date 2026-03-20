#!/usr/bin/env python3
"""
OHLCV Client
============
Thin wrapper around indicators.py for downloading and caching OHLCV data.

Usage:
    python3 src/data/ohlcv_client.py download BTC --timeframe 4h
    python3 src/data/ohlcv_client.py download ETH --timeframe 1d --force
    python3 src/data/ohlcv_client.py list
"""

import sys
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Delegate entirely to indicators.py — it owns the download logic and DB
from src.analysis.indicators import main

if __name__ == "__main__":
    main()
