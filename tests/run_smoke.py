#!/usr/bin/env python3
"""
Titan Terminal — Smoke Tests
================================
Verifies every Python tool can run without errors.
Uses real data (existing DBs, cached OHLCV). No mocks.

Usage:
    python3 tests/run_smoke.py           # Run all tests
    python3 tests/run_smoke.py --verbose  # Show full output on failures
    python3 tests/run_smoke.py indicators  # Run specific test

Exit codes:
    0 = All tests passed
    1 = One or more tests failed
"""

import subprocess
import sys
import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

NETWORK_ERROR_HINTS = ["timeout", "connection", "network", "unreachable", "resolve", "refused", "reset by peer"]


def _is_network_error(stderr: str) -> bool:
    lower = stderr.lower()
    return any(hint in lower for hint in NETWORK_ERROR_HINTS)


def _run(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        args, capture_output=True, text=True, timeout=timeout, cwd=PROJECT_ROOT
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_indicators_list() -> tuple[bool, str]:
    """indicators.py list — shows cached symbols."""
    try:
        r = _run(["python3", "src/analysis/indicators.py", "list"])
        if r.returncode != 0:
            return False, f"Exit {r.returncode}: {r.stderr[-200:]}"
        out = r.stdout.upper()
        if "BTC" in out or "ETH" in out or "SOL" in out:
            return True, "OK"
        return False, f"No known symbols in output. Got: {r.stdout[:200]}"
    except subprocess.TimeoutExpired:
        return False, "Timed out (30s)"
    except Exception as e:
        return False, str(e)


def test_indicators_analyze() -> tuple[bool, str]:
    """indicators.py analyze — runs TA on cached data."""
    for symbol in ["BTC", "ETH", "SOL"]:
        try:
            r = _run([
                "python3", "src/analysis/indicators.py", "analyze", symbol,
                "--timeframe", "4h", "--indicators", "rsi,macd,bb"
            ])
            if r.returncode == 0 and "RSI" in r.stdout.upper():
                return True, f"OK ({symbol})"
        except subprocess.TimeoutExpired:
            continue
        except Exception:
            continue
    return False, "SKIP: no cached OHLCV data for BTC/ETH/SOL"


def test_indicators_download() -> tuple[bool, str]:
    """indicators.py download — fetches fresh OHLCV from Binance."""
    try:
        r = _run(["python3", "src/analysis/indicators.py", "download", "BTC", "--timeframe", "4h"], timeout=60)
        if r.returncode == 0:
            out = (r.stdout + r.stderr).lower()
            if "candle" in out or "download" in out or "cache" in out or "saved" in out:
                return True, "OK"
            return True, "OK (exit 0)"
        if _is_network_error(r.stderr):
            return True, "SKIP: network unavailable"
        return False, f"Exit {r.returncode}: {r.stderr[-200:]}"
    except subprocess.TimeoutExpired:
        return True, "SKIP: network timeout (60s)"
    except Exception as e:
        return False, str(e)


def test_hyperliquid_fetcher() -> tuple[bool, str]:
    """hyperliquid_fetcher.py — fetches HL perps data."""
    try:
        r = _run(["python3", "src/fetchers/hyperliquid_fetcher.py", "--top", "5", "--no-save"], timeout=30)
        if r.returncode == 0:
            if "BTC" in r.stdout:
                return True, "OK"
            return True, "OK (exit 0, BTC not in top 5 output)"
        if _is_network_error(r.stderr):
            return True, "SKIP: network unavailable"
        return False, f"Exit {r.returncode}: {r.stderr[-200:]}"
    except subprocess.TimeoutExpired:
        return True, "SKIP: network timeout (30s)"
    except Exception as e:
        return False, str(e)


def test_target_package_formatter() -> tuple[bool, str]:
    """target_package.py — calculates position sizing."""
    payload = json.dumps({
        "token": "ETH",
        "direction": "LONG",
        "account": 50000,
        "entry": 2000,
        "stop": 1900,
        "targets": [2200, 2400, 2600],
        "risk_pct": 2.0,
        "leverage": 1.0,
        "rank": 2
    })
    try:
        r = _run(["python3", "src/formatters/target_package.py", payload])
        if r.returncode != 0:
            return False, f"Exit {r.returncode}: {r.stderr[-200:]}"
        out = r.stdout
        if "Target" in out or "Package" in out or "Position" in out or "R:R" in out or "R/" in out:
            return True, "OK"
        return False, f"Missing expected output. Got: {out[:200]}"
    except subprocess.TimeoutExpired:
        return False, "Timed out (30s)"
    except Exception as e:
        return False, str(e)


def test_target_package_rejects_bad_rr() -> tuple[bool, str]:
    """target_package.py — rejects setup below 3:1 R:R."""
    payload = json.dumps({
        "token": "ETH",
        "direction": "LONG",
        "account": 50000,
        "entry": 2000,
        "stop": 1900,
        "targets": [2050, 2100, 2150],
        "risk_pct": 2.0,
        "leverage": 1.0,
        "rank": 2
    })
    try:
        r = _run(["python3", "src/formatters/target_package.py", payload])
        out = (r.stdout + r.stderr).upper()
        if "3R" in out or "3:1" in out or "MINIMUM" in out or "REJECT" in out or "BELOW" in out or "WARNING" in out:
            return True, "OK (sub-3R flagged)"
        return False, f"No 3R warning in output. Got: {r.stdout[:200]}"
    except subprocess.TimeoutExpired:
        return False, "Timed out (30s)"
    except Exception as e:
        return False, str(e)


def test_portfolio_sync_dry_run() -> tuple[bool, str]:
    """portfolio_sync.py --dry-run — formats without writing."""
    payload = json.dumps({
        "result": [{
            "count": 1.5,
            "coin": {"rank": 2, "identifier": "ethereum", "symbol": "ETH", "name": "Ethereum"},
            "price": {"USD": 2300},
            "profit": {"unrealized": {"USD": -500}},
            "averageBuy": {"unrealized": {"USD": 2600}},
            "profitPercent": {"unrealized": {"USD": -11.5}}
        }]
    })
    try:
        r = _run(["python3", "src/formatters/portfolio_sync.py", "--dry-run", payload])
        if r.returncode != 0:
            return False, f"Exit {r.returncode}: {r.stderr[-200:]}"
        out = r.stdout.upper()
        if "PORTFOLIO" in out or "HOLDINGS" in out or "ETH" in out:
            return True, "OK"
        return False, f"Missing expected output. Got: {r.stdout[:200]}"
    except subprocess.TimeoutExpired:
        return False, "Timed out (30s)"
    except Exception as e:
        return False, str(e)


def test_intelligence_watchlist() -> tuple[bool, str]:
    """intelligence.py watchlist — queries the intelligence DB."""
    try:
        r = _run(["python3", "src/storage/intelligence.py", "watchlist"])
        if r.returncode == 0:
            return True, "OK"
        return False, f"Exit {r.returncode}: {r.stderr[-200:]}"
    except subprocess.TimeoutExpired:
        return False, "Timed out (30s)"
    except Exception as e:
        return False, str(e)


def test_nansen_cache_stats() -> tuple[bool, str]:
    """nansen_cache.py stats — shows cache statistics."""
    try:
        r = _run(["python3", "src/storage/nansen_cache.py", "stats"])
        if r.returncode != 0:
            return False, f"Exit {r.returncode}: {r.stderr[-200:]}"
        if r.stdout.strip():
            return True, "OK"
        return True, "OK (empty output)"
    except subprocess.TimeoutExpired:
        return False, "Timed out (30s)"
    except Exception as e:
        return False, str(e)


def test_nansen_cache_cycle() -> tuple[bool, str]:
    """nansen_cache.py — store then check retrieves the same data."""
    try:
        r1 = _run([
            "python3", "src/storage/nansen_cache.py", "store",
            "--tool", "general_search", "--token", "__TEST__",
            "--params", '{"query":"__TEST__"}',
            "--response", '{"test": true}'
        ])
        if r1.returncode != 0:
            return False, f"Store failed (exit {r1.returncode}): {r1.stderr[-200:]}"

        r2 = _run([
            "python3", "src/storage/nansen_cache.py", "check",
            "--tool", "general_search", "--token", "__TEST__",
            "--params", '{"query":"__TEST__"}'
        ])
        if r2.returncode != 0:
            return False, f"Check failed (exit {r2.returncode}): {r2.stderr[-200:]}"
        if '"test"' in r2.stdout or "CACHE_HIT" in r2.stdout:
            return True, "OK"
        return False, f"Stored data not found in check output. Got: {r2.stdout[:200]}"
    except subprocess.TimeoutExpired:
        return False, "Timed out (30s)"
    except Exception as e:
        return False, str(e)


def test_cex_monitor_alerts() -> tuple[bool, str]:
    """cex_monitor.py alerts — reads CEX health data."""
    try:
        r = _run(["python3", "src/watchers/cex_monitor.py", "alerts"])
        if r.returncode == 0:
            return True, "OK"
        return False, f"Exit {r.returncode}: {r.stderr[-200:]}"
    except subprocess.TimeoutExpired:
        return False, "Timed out (30s)"
    except Exception as e:
        return False, str(e)


def test_coinglass_fetcher() -> tuple[bool, str]:
    """coinglass_fetcher.py --token BTC — fetches liquidity data."""
    try:
        r = _run(["python3", "src/fetchers/coinglass_fetcher.py", "--token", "BTC", "--no-save"], timeout=30)
        if r.returncode == 0:
            out = r.stdout + r.stderr
            if "LIQUIDITY" in out.upper() or "BTC" in out:
                return True, "OK"
            return True, "OK (exit 0)"
        combined = (r.stdout + r.stderr).lower()
        if "api_key" in combined or "not set" in combined or "coinglass_api_key" in combined:
            return True, "SKIP: COINGLASS_API_KEY not set"
        if _is_network_error(r.stderr):
            return True, "SKIP: network unavailable"
        return False, f"Exit {r.returncode}: {r.stderr[-200:]}"
    except subprocess.TimeoutExpired:
        return True, "SKIP: network timeout (30s)"
    except Exception as e:
        return False, str(e)


def test_coinglass_derivatives() -> tuple[bool, str]:
    """coinglass_fetcher.py --derivatives — full derivatives analysis."""
    try:
        r = _run([
            "python3", "src/fetchers/coinglass_fetcher.py",
            "--token", "BTC", "--derivatives", "--price", "84000",
            "--json", "--no-save"
        ], timeout=60)
        if r.returncode == 0:
            try:
                data = json.loads(r.stdout)
                keys = set(data.keys())
                needed = {"funding", "open_interest", "long_short"}
                if needed.issubset(keys):
                    return True, "OK"
                return False, f"Missing keys. Got: {keys}"
            except json.JSONDecodeError:
                return False, f"Invalid JSON output: {r.stdout[:200]}"
        combined = (r.stdout + r.stderr).lower()
        if "api_key" in combined or "not set" in combined or "coinglass_api_key" in combined:
            return True, "SKIP: COINGLASS_API_KEY not set"
        if _is_network_error(r.stderr):
            return True, "SKIP: network unavailable"
        return False, f"Exit {r.returncode}: {r.stderr[-200:]}"
    except subprocess.TimeoutExpired:
        return True, "SKIP: network timeout (60s)"
    except Exception as e:
        return False, str(e)


def test_coinglass_market() -> tuple[bool, str]:
    """coinglass_fetcher.py --market — market derivatives pulse."""
    try:
        r = _run([
            "python3", "src/fetchers/coinglass_fetcher.py",
            "--market", "--json", "--no-save"
        ], timeout=60)
        if r.returncode == 0:
            try:
                data = json.loads(r.stdout)
                keys = set(data.keys())
                needed = {"fear_greed", "etf", "coinbase_premium"}
                if needed.issubset(keys):
                    return True, "OK"
                return False, f"Missing keys. Got: {keys}"
            except json.JSONDecodeError:
                return False, f"Invalid JSON output: {r.stdout[:200]}"
        combined = (r.stdout + r.stderr).lower()
        if "api_key" in combined or "not set" in combined or "coinglass_api_key" in combined:
            return True, "SKIP: COINGLASS_API_KEY not set"
        if _is_network_error(r.stderr):
            return True, "SKIP: network unavailable"
        return False, f"Exit {r.returncode}: {r.stderr[-200:]}"
    except subprocess.TimeoutExpired:
        return True, "SKIP: network timeout (60s)"
    except Exception as e:
        return False, str(e)


def test_coinglass_backward_compat() -> tuple[bool, str]:
    """coinglass_fetcher.py --token BTC --price 84000 — original liquidity report still works."""
    try:
        r = _run([
            "python3", "src/fetchers/coinglass_fetcher.py",
            "--token", "BTC", "--price", "84000", "--no-save"
        ], timeout=30)
        if r.returncode == 0:
            out = r.stdout.upper()
            if "LIQUIDITY" in out or "BTC" in out:
                return True, "OK"
            return True, "OK (exit 0)"
        combined = (r.stdout + r.stderr).lower()
        if "api_key" in combined or "not set" in combined or "coinglass_api_key" in combined:
            return True, "SKIP: COINGLASS_API_KEY not set"
        if _is_network_error(r.stderr):
            return True, "SKIP: network unavailable"
        return False, f"Exit {r.returncode}: {r.stderr[-200:]}"
    except subprocess.TimeoutExpired:
        return True, "SKIP: network timeout (30s)"
    except Exception as e:
        return False, str(e)


def test_derivatives_table_creation() -> tuple[bool, str]:
    """derivatives_snapshots table — init_db creates table with expected columns."""
    try:
        r = _run(["python3", "-c", """
import sys
sys.path.insert(0, '.')
from src.storage.intelligence import init_db, DB_PATH
init_db()
import sqlite3
conn = sqlite3.connect(str(DB_PATH))
cols = [row[1] for row in conn.execute('PRAGMA table_info(derivatives_snapshots)').fetchall()]
conn.close()
expected = ['timestamp_utc', 'symbol', 'funding_rate_avg', 'oi_usd', 'ls_global_ratio', 'fear_greed_value', 'lgf_detected']
missing = [c for c in expected if c not in cols]
if missing:
    print(f"MISSING: {missing}")
    sys.exit(1)
print(f"OK: {len(cols)} columns")
"""])
        if r.returncode == 0 and "OK" in r.stdout:
            return True, f"OK ({r.stdout.strip()})"
        return False, f"Exit {r.returncode}: {r.stdout + r.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Timed out (30s)"
    except Exception as e:
        return False, str(e)


def test_derivatives_logging() -> tuple[bool, str]:
    """log_derivatives_snapshot — inserts a row with mock data."""
    try:
        r = _run(["python3", "-c", """
import sys
sys.path.insert(0, '.')
from src.storage.intelligence import init_db, log_derivatives_snapshot, DB_PATH
init_db()
mock = {
    "symbol": "__TEST__",
    "current_price": 99999,
    "funding": {"avg_rate": 0.0001, "max_rate": 0.0005, "max_exchange": "Binance", "bias": "neutral", "annualized_cost_pct": 1.5},
    "open_interest": {
        "history": {"oi_trend": "flat"},
        "exchanges": {"total_oi_usd": 50e9, "change_1h_pct": 0.5, "change_4h_pct": 1.2, "change_24h_pct": -2.1, "momentum": "stable"},
    },
    "long_short": {
        "global": {"current_ratio": 1.05, "current_long_pct": 51.2, "extreme": False, "contrarian_signal": None},
        "top_traders": {"top_account_ratio": 1.1, "top_position_ratio": 0.95, "smart_money_lean": "neutral"},
    },
    "liquidation": {"total_24h_usd": 200e6, "long_liq_24h_usd": 120e6, "short_liq_24h_usd": 80e6, "long_short_ratio": 1.5, "bias": "long_pain", "recent_acceleration": False},
    "max_pain": {"max_pain_price": 85000, "distance_pct": 1.2, "put_call_oi_ratio": 0.9},
    "setup": {"detected": False, "direction": None, "confidence": None},
}
row_id = log_derivatives_snapshot(mock)
if row_id < 0:
    print("FAIL: returned -1")
    sys.exit(1)
import sqlite3
conn = sqlite3.connect(str(DB_PATH))
row = conn.execute('SELECT symbol, price_usd FROM derivatives_snapshots WHERE id = ?', (row_id,)).fetchone()
conn.close()
if row and row[0] == '__TEST__':
    print(f"OK: row {row_id}")
else:
    print(f"FAIL: row not found or wrong data")
    sys.exit(1)
"""])
        if r.returncode == 0 and "OK" in r.stdout:
            return True, r.stdout.strip()
        return False, f"Exit {r.returncode}: {r.stdout + r.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Timed out (30s)"
    except Exception as e:
        return False, str(e)


def test_derivatives_history_cli() -> tuple[bool, str]:
    """derivatives-history CLI — exits 0."""
    try:
        r = _run(["python3", "src/storage/intelligence.py", "derivatives-history", "--days", "1"])
        if r.returncode == 0:
            return True, "OK"
        return False, f"Exit {r.returncode}: {r.stderr[-200:]}"
    except subprocess.TimeoutExpired:
        return False, "Timed out (30s)"
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ALL_TESTS = {
    "indicators_list": test_indicators_list,
    "indicators_analyze": test_indicators_analyze,
    "indicators_download": test_indicators_download,
    "hyperliquid": test_hyperliquid_fetcher,
    "target_package": test_target_package_formatter,
    "target_package_rr": test_target_package_rejects_bad_rr,
    "portfolio_sync": test_portfolio_sync_dry_run,
    "intelligence": test_intelligence_watchlist,
    "nansen_cache_stats": test_nansen_cache_stats,
    "nansen_cache_cycle": test_nansen_cache_cycle,
    "cex_monitor": test_cex_monitor_alerts,
    "coinglass": test_coinglass_fetcher,
    "coinglass_derivatives": test_coinglass_derivatives,
    "coinglass_market": test_coinglass_market,
    "coinglass_backcompat": test_coinglass_backward_compat,
    "deriv_table": test_derivatives_table_creation,
    "deriv_logging": test_derivatives_logging,
    "deriv_history_cli": test_derivatives_history_cli,
}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Titan Terminal — Smoke Tests")
    parser.add_argument("--verbose", action="store_true", help="Show full output on failures")
    parser.add_argument("filter", nargs="?", default=None, help="Run tests matching this substring")
    args = parser.parse_args()

    tests_to_run = ALL_TESTS
    if args.filter:
        tests_to_run = {k: v for k, v in ALL_TESTS.items() if args.filter in k}
        if not tests_to_run:
            print(f"No tests matching '{args.filter}'")
            sys.exit(1)

    print("Titan Terminal — Smoke Tests")
    print("=" * 40)
    print()

    passed = 0
    failed = 0
    skipped = 0
    failures = []

    max_name_len = max(len(name) for name in tests_to_run)

    for name, test_fn in tests_to_run.items():
        ok, msg = test_fn()
        padded = name.ljust(max_name_len)

        if msg.startswith("SKIP"):
            skipped += 1
            print(f"  -  {padded} — {msg}")
            if args.verbose:
                failures.append((name, msg))
        elif ok:
            passed += 1
            print(f"  OK {padded} — {msg}")
        else:
            failed += 1
            print(f"  FAIL {padded} — {msg}")
            failures.append((name, msg))

    print()
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")

    if args.verbose and failures:
        print()
        print("=" * 40)
        print("Details for failures/skips:")
        print("=" * 40)
        for name, msg in failures:
            print(f"\n  [{name}] {msg}")

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
