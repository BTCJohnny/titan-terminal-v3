#!/usr/bin/env python3
"""
Coinglass Hobbyist Tier — Re-Probe with Corrected v4 Paths
============================================================
Targeted test of priority endpoints using paths from the actual v4 API docs.

Usage:
    python3 tests/probe_coinglass_v2.py
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
    url = f"{CG_BASE}{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"

    result = {
        "name": name,
        "path": path,
        "params": params,
        "status": "ERROR",
        "code": None,
        "message": None,
        "data_shape": None,
        "sample": None,
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
                    result["sample"] = _get_sample(inner)
                else:
                    result["status"] = "FAIL"
            else:
                result["status"] = "PASS"
                result["data_shape"] = _describe_shape(data)
                result["sample"] = _get_sample(data)

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
            keys = list(sample.keys())
            return f"list of {len(data)} items, keys: {keys}"
        return f"list of {len(data)} items, type={type(sample).__name__}"
    if isinstance(data, dict):
        keys = list(data.keys())
        return f"dict with keys: {keys}"
    return f"{type(data).__name__}: {str(data)[:100]}"


def _get_sample(data) -> str:
    if data is None:
        return "null"
    if isinstance(data, list) and len(data) > 0:
        first = data[0]
        return json.dumps(first, default=str)[:300]
    if isinstance(data, dict):
        return json.dumps(data, default=str)[:300]
    return str(data)[:300]


# ─── Endpoint definitions ───────────────────────────────────────────

CATEGORIES = [
    ("BASELINE (re-confirm)", [
        ("Funding Rate Exchange List", "/api/futures/funding-rate/exchange-list", {"symbol": "BTC"}),
        ("Liquidation Coin List", "/api/futures/liquidation/coin-list", {"exchange": "Binance"}),
        ("Options Max Pain", "/api/option/max-pain", {"symbol": "BTC", "exchange": "Deribit"}),
        ("Options Info", "/api/option/info", {"symbol": "BTC"}),
    ]),
    ("PRIORITY — corrected v4 paths", [
        ("#2 OI Aggregated History", "/api/futures/open-interest/aggregated-history", {"symbol": "BTC", "interval": "4h", "limit": "6"}),
        ("#3 Global L/S Account Ratio", "/api/futures/global-long-short-account-ratio/history", {"symbol": "BTC", "exchange": "Binance", "interval": "4h", "limit": "6"}),
        ("#4 Taker Buy/Sell Aggregated", "/api/futures/aggregated-taker-buy-sell-volume/history", {"symbol": "BTC", "interval": "1h", "limit": "6"}),
        ("#5 BTC ETF Flows", "/api/etf/bitcoin/flow-history", {}),
        ("#6 Fear & Greed Index", "/api/index/fear-greed-history", {}),
        ("#7 Coinbase Premium", "/api/coinbase-premium-index", {}),
    ]),
    ("BONUS — additional v4 endpoints", [
        ("OI Exchange List", "/api/futures/open-interest/exchange-list", {"symbol": "BTC"}),
        ("Coin Liquidation History", "/api/futures/aggregated-liquidation/history", {"symbol": "BTC", "interval": "4h", "limit": "6"}),
        ("Top L/S Account Ratio", "/api/futures/top-long-short-account-ratio/history", {"symbol": "BTC", "exchange": "Binance", "interval": "4h", "limit": "6"}),
        ("Top L/S Position Ratio", "/api/futures/top-long-short-position-ratio/history", {"symbol": "BTC", "exchange": "Binance", "interval": "4h", "limit": "6"}),
        ("Futures Basis", "/api/futures/basis", {"symbol": "BTC"}),
        ("Aggregated CVD", "/api/futures/aggregated-taker-buy-sell-volume/cvd-history", {"symbol": "BTC", "interval": "4h", "limit": "6"}),
        ("Hyperliquid Whale Alert", "/api/futures/hyperliquid/whale-alert", {}),
        ("Hyperliquid Whale Position", "/api/futures/hyperliquid/whale-position", {"symbol": "BTC"}),
        ("Exchange Balance List", "/api/exchange/balance-list", {"symbol": "BTC"}),
        ("Token Unlock List", "/api/token/unlock-list", {}),
        ("Bitcoin Dominance", "/api/index/bitcoin-dominance", {}),
        ("Altcoin Season Index", "/api/index/altcoin-season", {}),
    ]),
]


def main():
    api_key = _get_api_key()
    if not api_key:
        print("\n  COINGLASS_API_KEY not set. Add it to .env")
        sys.exit(1)

    total = sum(len(eps) for _, eps in CATEGORIES)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    print(f"\n=== Coinglass v2 Re-Probe — Corrected v4 Paths ===", flush=True)
    print(f"Date: {now}")
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
                short_msg = result["message"][:80] if result["message"] else ""
                print(f"FAIL (code={result['code']}, msg={short_msg})", file=sys.stderr)
            else:
                error_count += 1
                print(f"ERROR ({result['message'][:60] if result['message'] else ''})", file=sys.stderr)

            cat_results.append(result)
            all_results.append(result)

            if counter < total:
                time.sleep(2)

        # Print category results
        print(f"\n{cat_name}:")
        for r in cat_results:
            icon = {"PASS": "  ✅", "FAIL": "  ❌", "ERROR": "  ⚠️ "}[r["status"]]
            if r["status"] == "PASS":
                print(f"{icon} {r['name']}")
                print(f"       Shape: {r['data_shape']}")
                if r["sample"]:
                    print(f"       Sample: {r['sample'][:200]}")
            else:
                detail = ""
                if r["code"] == "401" or (r["message"] and "Upgrade" in str(r["message"])):
                    detail = "TIER-BLOCKED (401 Upgrade plan)"
                elif r["code"] == "404":
                    detail = f"PATH NOT FOUND (404)"
                elif r["code"] == "400":
                    detail = f"BAD PARAMS: {r['message'][:80] if r['message'] else ''}"
                else:
                    detail = f"code={r['code']}: {r['message'][:80] if r['message'] else ''}"
                print(f"{icon} {r['name']} — {detail}")

    # Summary
    print(f"\n{'=' * 65}")
    print(f"=== SUMMARY ===")
    print(f"  ✅ Available: {pass_count}/{total}")
    print(f"  ❌ Blocked:   {fail_count}/{total}")
    print(f"  ⚠️  Error:     {error_count}/{total}")

    # Failure breakdown
    tier_blocked = [r for r in all_results if r["status"] == "FAIL" and
                    (r["code"] == "401" or (r["message"] and "Upgrade" in str(r["message"])))]
    path_wrong = [r for r in all_results if r["status"] == "FAIL" and r["code"] == "404"]
    bad_params = [r for r in all_results if r["status"] == "FAIL" and r["code"] == "400"]
    other_fail = [r for r in all_results if r["status"] == "FAIL" and
                  r not in tier_blocked and r not in path_wrong and r not in bad_params]

    print(f"\n  Failure breakdown:")
    print(f"    401 Tier-blocked:  {len(tier_blocked)}")
    print(f"    404 Wrong path:    {len(path_wrong)}")
    print(f"    400 Bad params:    {len(bad_params)}")
    print(f"    Other:             {len(other_fail)}")

    if tier_blocked:
        print(f"\n  Tier-blocked endpoints:")
        for r in tier_blocked:
            print(f"    ❌ {r['path']}")

    if path_wrong:
        print(f"\n  Still-wrong paths (need further correction):")
        for r in path_wrong:
            print(f"    ❌ {r['path']}")

    if bad_params:
        print(f"\n  Bad params (path exists, fix params):")
        for r in bad_params:
            print(f"    ❌ {r['path']} — {r['message'][:80] if r['message'] else ''}")

    # Priority status
    priority_names = [
        ("#2 OI Aggregated History", "OI Aggregated History"),
        ("#3 Global L/S Account Ratio", "Global L/S Account Ratio"),
        ("#4 Taker Buy/Sell Aggregated", "Taker Buy/Sell Aggregated"),
        ("#5 BTC ETF Flows", "BTC ETF Flows"),
        ("#6 Fear & Greed Index", "Fear & Greed Index"),
        ("#7 Coinbase Premium", "Coinbase Premium"),
    ]
    print(f"\n=== PRIORITY ENDPOINT VERDICT ===")
    print(f"  #1 ✅ Funding Rate Exchange List — confirmed working (baseline)")
    for pname, short in priority_names:
        match = next((r for r in all_results if r["name"] == pname), None)
        if match:
            icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "⚠️ "}[match["status"]]
            reason = ""
            if match["status"] == "FAIL":
                if match["code"] == "401" or (match["message"] and "Upgrade" in str(match["message"])):
                    reason = " — TIER-BLOCKED"
                elif match["code"] == "404":
                    reason = " — WRONG PATH (still 404)"
                else:
                    reason = f" — code {match['code']}"
            elif match["status"] == "PASS":
                reason = f" — {match['data_shape'][:60]}"
            print(f"  {icon} {pname}{reason}")

    # Save report
    report_dir = PROJECT_ROOT / "results"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"coinglass_probe_v2_{datetime.now().strftime('%Y-%m-%d')}.md"

    lines = []
    lines.append(f"# Coinglass v2 Re-Probe — Corrected v4 Paths")
    lines.append(f"**Date:** {now}")
    lines.append(f"**Available:** {pass_count}/{total} | **Blocked:** {fail_count}/{total} | **Error:** {error_count}/{total}")
    lines.append(f"**Failure breakdown:** {len(tier_blocked)} tier-blocked, {len(path_wrong)} wrong path, {len(bad_params)} bad params")
    lines.append("")

    for cat_name, _ in CATEGORIES:
        cat_items = [r for r in all_results if r["category"] == cat_name]
        lines.append(f"## {cat_name}")
        for r in cat_items:
            status = r["status"]
            if status == "PASS":
                lines.append(f"- **PASS** `{r['path']}` — {r['name']}")
                lines.append(f"  - Shape: {r['data_shape']}")
                lines.append(f"  - Sample: `{r['sample'][:200] if r['sample'] else 'n/a'}`")
            else:
                detail = r["message"][:100] if r["message"] else "unknown"
                lines.append(f"- **{status}** `{r['path']}` — {r['name']} — {detail}")
        lines.append("")

    lines.append("## Available Endpoints (Hobbyist)")
    for r in all_results:
        if r["status"] == "PASS":
            lines.append(f"- `{r['path']}` — {r['name']}")

    with open(report_path, "w") as f:
        f.write("\n".join(lines))

    print(f"\n💾 Report saved to: {report_path}")


if __name__ == "__main__":
    main()
