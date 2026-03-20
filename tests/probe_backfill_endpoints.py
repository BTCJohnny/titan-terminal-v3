#!/usr/bin/env python3
"""
Probe Backfill Endpoints
========================
Test 2 unverified historical endpoints needed for derivatives backfill:
1. Funding Rate OHLC History — /api/futures/funding-rate/history
2. Liquidation Aggregated History — /api/futures/liquidation/aggregated-history

Run: python3 tests/probe_backfill_endpoints.py
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.fetchers.coinglass_fetcher import cg_get

TESTS = [
    # Funding Rate History
    ("FR History (BTC)", "/api/futures/funding-rate/history",
     {"symbol": "BTC", "interval": "4h", "limit": "6"}),
    ("FR History (BTCUSDT)", "/api/futures/funding-rate/history",
     {"symbol": "BTCUSDT", "interval": "4h", "limit": "6"}),
    ("FR History (BTCUSDT + Binance)", "/api/futures/funding-rate/history",
     {"symbol": "BTCUSDT", "exchange": "Binance", "interval": "4h", "limit": "6"}),

    # Liquidation Aggregated History
    ("Liq Agg History (BTC)", "/api/futures/liquidation/aggregated-history",
     {"symbol": "BTC", "interval": "4h", "limit": "6"}),
    ("Liq Agg History (BTCUSDT)", "/api/futures/liquidation/aggregated-history",
     {"symbol": "BTCUSDT", "interval": "4h", "limit": "6"}),
]

def main():
    print("=" * 65)
    print("  Backfill Endpoint Probe")
    print("=" * 65)

    results = []
    for name, path, params in TESTS:
        print(f"\n  Testing: {name}")
        print(f"  Path: {path}")
        print(f"  Params: {params}")

        data = cg_get(path, params, debug=False)
        time.sleep(2)

        if data is None:
            print(f"  Result: ❌ FAIL")
            results.append((name, "FAIL", None))
        else:
            print(f"  Result: ✅ PASS")
            if isinstance(data, list):
                print(f"  Shape: list of {len(data)} items", end="")
                if data and isinstance(data[0], dict):
                    print(f", keys: {list(data[0].keys())}")
                    sample = json.dumps(data[0], default=str)[:200]
                    print(f"  Sample: {sample}")
                else:
                    print()
                    if data:
                        print(f"  First item type: {type(data[0]).__name__}")
                        print(f"  Sample: {str(data[0])[:200]}")
            elif isinstance(data, dict):
                print(f"  Shape: dict with keys: {list(data.keys())}")
                sample = json.dumps(data, default=str)[:200]
                print(f"  Sample: {sample}")
            else:
                print(f"  Shape: {type(data).__name__}")
                print(f"  Sample: {str(data)[:200]}")
            results.append((name, "PASS", data))

    print(f"\n{'=' * 65}")
    print("  SUMMARY")
    print(f"{'=' * 65}")
    passes = sum(1 for _, s, _ in results if s == "PASS")
    fails = sum(1 for _, s, _ in results if s == "FAIL")
    print(f"  ✅ {passes} PASS | ❌ {fails} FAIL")
    for name, status, _ in results:
        emoji = "✅" if status == "PASS" else "❌"
        print(f"  {emoji} {name}")

if __name__ == "__main__":
    main()
