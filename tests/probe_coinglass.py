#!/usr/bin/env python3
"""
Coinglass Hobbyist Tier — Endpoint Probe
==========================================
Tests every Coinglass API endpoint we plan to use and reports which ones
work on the Hobbyist plan. Read-only discovery — no production code changes.

Usage:
    python3 tests/probe_coinglass.py
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CG_BASE = "https://open-api-v4.coinglass.com"


def _get_api_key() -> str | None:
    key = os.environ.get("COINGLASS_API_KEY")
    if key:
        return key
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("COINGLASS_API_KEY="):
                val = line.split("=", 1)[1].split("#")[0].strip()
                if val:
                    return val
    return None


def probe_endpoint(name: str, path: str, params: dict, api_key: str) -> dict:
    """Hit one endpoint and return result dict."""
    url = f"{CG_BASE}{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"

    result = {
        "name": name,
        "path": path,
        "status": "ERROR",
        "code": None,
        "message": None,
        "data_shape": None,
    }

    try:
        req = urllib.request.Request(
            url,
            headers={"CG-API-KEY": api_key, "Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            data = json.loads(raw)

            if isinstance(data, dict):
                code = str(data.get("code", ""))
                msg = data.get("msg", "")
                result["code"] = code
                result["message"] = msg

                if code == "0":
                    result["status"] = "PASS"
                    inner = data.get("data")
                    result["data_shape"] = _describe_shape(inner)
                else:
                    result["status"] = "FAIL"
            else:
                result["status"] = "PASS"
                result["data_shape"] = _describe_shape(data)

    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()[:300]
        except Exception:
            pass
        result["code"] = str(e.code)
        result["message"] = body
        result["status"] = "FAIL"
    except Exception as e:
        result["message"] = str(e)
        result["status"] = "ERROR"

    return result


def _describe_shape(data) -> str:
    if data is None:
        return "null"
    if isinstance(data, list):
        if len(data) == 0:
            return "empty list"
        sample = data[0]
        if isinstance(sample, dict):
            keys = list(sample.keys())[:5]
            return f"list of {len(data)} items, keys: {keys}"
        return f"list of {len(data)} items"
    if isinstance(data, dict):
        keys = list(data.keys())[:8]
        return f"dict with keys: {keys}"
    return f"{type(data).__name__}: {str(data)[:80]}"


# ─── Endpoint definitions ───────────────────────────────────────────

CATEGORIES = [
    ("BASELINE (should all pass)", [
        ("Liquidation Coin List", "/api/futures/liquidation/coin-list", {"exchange": "Binance"}),
        ("Options Max Pain", "/api/option/max-pain", {"symbol": "BTC", "exchange": "Deribit"}),
        ("Options Info", "/api/option/info", {"symbol": "BTC"}),
    ]),
    ("FUTURES DERIVATIVES", [
        ("Funding Rate Exchange List", "/api/futures/funding-rate/exchange-list", {"symbol": "BTC"}),
        ("OI Aggregated History", "/api/futures/open-interest/ohlc-aggregated-history", {"symbol": "BTC", "interval": "4h", "limit": "6"}),
        ("Global L/S Account Ratio", "/api/futures/long-short-ratio/global-account", {"symbol": "BTC", "interval": "4h", "limit": "6"}),
        ("Top L/S Account Ratio", "/api/futures/long-short-ratio/top-account", {"symbol": "BTC", "interval": "4h", "limit": "6"}),
        ("Top L/S Position Ratio", "/api/futures/long-short-ratio/top-position", {"symbol": "BTC", "interval": "4h", "limit": "6"}),
        ("Taker Buy/Sell History (Aggregated)", "/api/futures/taker-buy-sell/aggregated-history", {"symbol": "BTC", "interval": "1h", "limit": "6"}),
        ("Taker Buy/Sell History (Pair)", "/api/futures/taker-buy-sell/history", {"symbol": "BTCUSDT", "exchange": "Binance", "interval": "1h", "limit": "6"}),
        ("Net Long/Short Position", "/api/futures/long-short-ratio/net-position", {"symbol": "BTC"}),
        ("Futures CVD History", "/api/futures/taker-buy-sell/cvd-history", {"symbol": "BTCUSDT", "exchange": "Binance", "interval": "4h", "limit": "6"}),
        ("Futures Aggregated CVD", "/api/futures/taker-buy-sell/aggregated-cvd-history", {"symbol": "BTC", "interval": "4h", "limit": "6"}),
    ]),
    ("OI DETAIL", [
        ("OI OHLC History (Pair)", "/api/futures/open-interest/ohlc-history", {"symbol": "BTCUSDT", "exchange": "Binance", "interval": "4h", "limit": "6"}),
        ("OI Exchange List", "/api/futures/open-interest/exchange-list", {"symbol": "BTC"}),
    ]),
    ("LIQUIDATION (expect premium-only)", [
        ("Liquidation Map (Pair)", "/api/futures/liquidation/map", {"symbol": "BTCUSDT", "exchange": "Binance", "range": "1d"}),
        ("Liquidation Map (Aggregated)", "/api/futures/liquidation/aggregated-map", {"symbol": "BTC", "range": "1d"}),
        ("Liquidation Order", "/api/futures/liquidation/order", {"symbol": "BTCUSDT", "exchange": "Binance"}),
        ("Liquidation Heatmap Model1", "/api/futures/liquidation/heatmap", {"symbol": "BTCUSDT", "exchange": "Binance", "range": "3d"}),
        ("Liquidation History (Pair)", "/api/futures/liquidation/history", {"symbol": "BTCUSDT", "exchange": "Binance", "interval": "4h", "limit": "6"}),
        ("Liquidation History (Aggregated)", "/api/futures/liquidation/aggregated-history", {"symbol": "BTC", "interval": "4h", "limit": "6"}),
        ("Liquidation Max Pain", "/api/futures/liquidation/max-pain", {"symbol": "BTCUSDT", "exchange": "Binance"}),
    ]),
    ("ORDERBOOK", [
        ("Orderbook Bid/Ask (Pair)", "/api/futures/orderbook/history", {"symbol": "BTCUSDT", "exchange": "Binance", "interval": "4h", "limit": "6"}),
        ("Orderbook Heatmap", "/api/futures/orderbook/heatmap", {"symbol": "BTCUSDT", "exchange": "Binance"}),
        ("Large Orderbook", "/api/futures/orderbook/large-limit-order", {"symbol": "BTCUSDT", "exchange": "Binance"}),
    ]),
    ("HYPERLIQUID", [
        ("Hyperliquid Whale Alert", "/api/futures/hyperliquid/whale-alert", {}),
        ("Hyperliquid Whale Position", "/api/futures/hyperliquid/whale-position", {"symbol": "BTC"}),
        ("Hyperliquid Positions by Coin", "/api/futures/hyperliquid/position", {"symbol": "BTC"}),
        ("Hyperliquid L/S Account Ratio", "/api/futures/hyperliquid/long-short-account-ratio-history", {"symbol": "BTC", "interval": "4h", "limit": "6"}),
    ]),
    ("ON-CHAIN / EXCHANGE DATA", [
        ("Exchange Balance List", "/api/onchain/exchange-balance-list", {"symbol": "BTC"}),
        ("Exchange Balance Chart", "/api/onchain/exchange-balance-chart", {"symbol": "BTC", "exchange": "Binance", "interval": "4h", "limit": "6"}),
        ("Whale Transfer", "/api/onchain/whale-transfer", {"symbol": "BTC"}),
        ("Token Unlock List", "/api/onchain/token-unlock-list", {}),
    ]),
    ("ETF", [
        ("BTC ETF Flows History", "/api/etf/flows-history", {}),
        ("BTC ETF List", "/api/etf/bitcoin-list", {}),
        ("BTC ETF NetAssets History", "/api/etf/bitcoin-etf-netassets-history", {}),
        ("ETH ETF Flows History", "/api/etf/ethereum-etf-flows-history", {}),
    ]),
    ("INDICATORS", [
        ("Fear & Greed Index", "/api/indicator/fear-greed", {}),
        ("Coinbase Premium", "/api/indicator/coinbase-premium", {}),
        ("Futures Basis", "/api/indicator/basis", {"symbol": "BTC"}),
        ("BTC RSI List", "/api/indicator/futures-rsi-list", {}),
        ("Altcoin Season Index", "/api/indicator/altcoin-season-index", {}),
        ("BTC Dominance", "/api/indicator/bitcoin-dominance", {}),
    ]),
    ("SPOT", [
        ("Spot Coins Markets", "/api/spot/coins-markets", {}),
        ("Spot Taker Buy/Sell", "/api/spot/taker-buy-sell/aggregated-history", {"symbol": "BTC", "interval": "1h", "limit": "6"}),
    ]),
    ("MULTI-TIMEFRAME / MARKETS", [
        ("Coins Price Change", "/api/futures/coins-price-change", {}),
        ("Coins Markets", "/api/futures/coins-markets", {}),
    ]),
]


def main():
    api_key = _get_api_key()
    if not api_key:
        print("\n  COINGLASS_API_KEY not set. Add it to .env")
        sys.exit(1)

    # Count total endpoints
    total = sum(len(eps) for _, eps in CATEGORIES)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    print(f"\n=== Coinglass Hobbyist Tier — Endpoint Probe ===", flush=True)
    print(f"Date: {now}")
    print(f"Plan: Hobbyist (30 req/min)")
    print(f"Endpoints to test: {total}")
    print(f"Estimated time: ~{total * 2}s\n")

    all_results = []
    counter = 0
    pass_count = 0
    fail_count = 0
    error_count = 0

    for cat_name, endpoints in CATEGORIES:
        cat_results = []
        for name, path, params in endpoints:
            counter += 1
            print(f"  Testing {counter}/{total}: {name}...", end=" ", file=sys.stderr, flush=True)

            result = probe_endpoint(name, path, params, api_key)
            result["category"] = cat_name

            if result["status"] == "PASS":
                pass_count += 1
                print("PASS", file=sys.stderr)
            elif result["status"] == "FAIL":
                fail_count += 1
                print(f"FAIL (code={result['code']}, msg={result['message'][:60] if result['message'] else ''})", file=sys.stderr)
            else:
                error_count += 1
                print(f"ERROR ({result['message'][:60] if result['message'] else ''})", file=sys.stderr)

            cat_results.append(result)
            all_results.append(result)

            # Rate limit: 2s between requests
            if counter < total:
                time.sleep(2)

        # Print category results
        print(f"\n{cat_name}:")
        for r in cat_results:
            icon = {"PASS": "  ✅", "FAIL": "  ❌", "ERROR": "  ⚠️ "}[r["status"]]
            detail = ""
            if r["status"] == "PASS":
                detail = f"— {r['data_shape']}"
            elif r["status"] == "FAIL":
                detail = f"— code {r['code']}: \"{r['message'][:80] if r['message'] else 'unknown'}\""
            else:
                detail = f"— {r['message'][:80] if r['message'] else 'unknown error'}"
            print(f"{icon} {r['name']:<42} {detail}")

    # Summary
    print(f"\n{'=' * 65}")
    print(f"=== SUMMARY ===")
    print(f"  ✅ Available: {pass_count}/{total} endpoints")
    print(f"  ❌ Blocked:   {fail_count}/{total} endpoints (require higher tier)")
    print(f"  ⚠️  Error:     {error_count}/{total} endpoints (network/param issues)")

    # Priority endpoints
    priority_names = [
        "Funding Rate Exchange List",
        "OI Aggregated History",
        "Global L/S Account Ratio",
        "Taker Buy/Sell History (Aggregated)",
        "BTC ETF Flows History",
        "Fear & Greed Index",
        "Coinbase Premium",
    ]
    print(f"\n=== PRIORITY ENDPOINT STATUS ===")
    for i, pname in enumerate(priority_names, 1):
        match = next((r for r in all_results if r["name"] == pname), None)
        if match:
            icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "⚠️ "}[match["status"]]
            print(f"  #{i} {icon} {pname}")
        else:
            print(f"  #{i} ❓ {pname} — not tested")

    # Available list
    available = [r for r in all_results if r["status"] == "PASS"]
    blocked = [r for r in all_results if r["status"] == "FAIL"]

    print(f"\n=== AVAILABLE ENDPOINTS (copy this list) ===")
    for r in available:
        print(f"  {r['path']}")

    print(f"\n=== BLOCKED ENDPOINTS (require upgrade) ===")
    for r in blocked:
        msg = r["message"][:60] if r["message"] else "unknown"
        print(f"  {r['path']} — \"{msg}\"")

    # Surprise wins
    premium_expected = {"Liquidation Map (Pair)", "Liquidation Map (Aggregated)",
                        "Liquidation Order", "Liquidation Heatmap Model1",
                        "Liquidation Max Pain", "Orderbook Heatmap",
                        "Large Orderbook"}
    surprises = [r for r in all_results if r["name"] in premium_expected and r["status"] == "PASS"]
    if surprises:
        print(f"\n=== SURPRISE WINS (expected premium, got access!) ===")
        for r in surprises:
            print(f"  ✅ {r['name']} — {r['data_shape']}")
    else:
        print(f"\n=== SURPRISE WINS ===")
        print(f"  None — all expected-premium endpoints are blocked as anticipated.")

    # Save report
    report_dir = PROJECT_ROOT / "results"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"coinglass_probe_{datetime.now().strftime('%Y-%m-%d')}.md"

    lines = []
    lines.append(f"# Coinglass Hobbyist Tier — Endpoint Probe Results")
    lines.append(f"**Date:** {now}")
    lines.append(f"**Plan:** Hobbyist (30 req/min)")
    lines.append(f"**Available:** {pass_count}/{total} | **Blocked:** {fail_count}/{total} | **Error:** {error_count}/{total}")
    lines.append("")

    for cat_name, _ in CATEGORIES:
        cat_items = [r for r in all_results if r["category"] == cat_name]
        lines.append(f"## {cat_name}")
        for r in cat_items:
            icon = {"PASS": "PASS", "FAIL": "FAIL", "ERROR": "ERROR"}[r["status"]]
            detail = r["data_shape"] if r["status"] == "PASS" else (r["message"][:100] if r["message"] else "unknown")
            lines.append(f"- **{icon}** `{r['path']}` — {r['name']} — {detail}")
        lines.append("")

    lines.append("## Priority Endpoints")
    for i, pname in enumerate(priority_names, 1):
        match = next((r for r in all_results if r["name"] == pname), None)
        if match:
            icon = "PASS" if match["status"] == "PASS" else "FAIL"
            lines.append(f"{i}. **{icon}** {pname}")

    lines.append("")
    lines.append("## Available Endpoints")
    for r in available:
        lines.append(f"- `{r['path']}`")

    lines.append("")
    lines.append("## Blocked Endpoints")
    for r in blocked:
        lines.append(f"- `{r['path']}` — {r['message'][:80] if r['message'] else 'unknown'}")

    with open(report_path, "w") as f:
        f.write("\n".join(lines))

    print(f"\n💾 Report saved to: {report_path}")


if __name__ == "__main__":
    main()
