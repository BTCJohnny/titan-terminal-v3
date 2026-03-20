#!/usr/bin/env python3
"""
Coinglass Fix-Probe — L/S Ratio + Coinbase Premium
====================================================
6-endpoint probe to resolve last unknowns: BTCUSDT symbol format
for L/S ratios and alternate Coinbase Premium paths.

Usage:
    python3 tests/probe_coinglass_fix.py
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


# ─── Endpoints to probe ──────────────────────────────────────────

ENDPOINTS_TO_PROBE = [
    # L/S ratios — try BTCUSDT instead of BTC (the error said "pair does not exist")
    ("Global L/S Ratio (BTCUSDT)", "/api/futures/global-long-short-account-ratio/history",
     {"symbol": "BTCUSDT", "exchange": "Binance", "interval": "4h", "limit": "6"}),

    ("Top L/S Account Ratio (BTCUSDT)", "/api/futures/top-long-short-account-ratio/history",
     {"symbol": "BTCUSDT", "exchange": "Binance", "interval": "4h", "limit": "6"}),

    ("Top L/S Position Ratio (BTCUSDT)", "/api/futures/top-long-short-position-ratio/history",
     {"symbol": "BTCUSDT", "exchange": "Binance", "interval": "4h", "limit": "6"}),

    # Coinbase Premium — retry with different approaches
    # Try 1: no params (the docs show no required params)
    ("Coinbase Premium (no params)", "/api/coinbase-premium-index", {}),

    # Try 2: with interval param (some history endpoints need this)
    ("Coinbase Premium (with interval)", "/api/coinbase-premium-index",
     {"interval": "4h", "limit": "6"}),

    # Try 3: different path guess — maybe it's under /api/indicator/
    ("Coinbase Premium (alt path)", "/api/indicator/coinbase-premium-index", {}),
]


def main():
    api_key = _get_api_key()
    if not api_key:
        print("\n  COINGLASS_API_KEY not set. Add it to .env")
        sys.exit(1)

    total = len(ENDPOINTS_TO_PROBE)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    print(f"\n=== Coinglass Fix-Probe — L/S Ratio + Coinbase Premium ===", flush=True)
    print(f"Date: {now}")
    print(f"Endpoints to test: {total}")
    print(f"Estimated time: ~{total * 2}s\n")

    all_results = []
    pass_count = 0
    fail_count = 0
    error_count = 0

    for i, (name, path, params) in enumerate(ENDPOINTS_TO_PROBE):
        print(f"  Testing {i+1}/{total}: {name}...", end=" ", file=sys.stderr, flush=True)

        result = probe_endpoint(name, path, params, api_key)

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

        all_results.append(result)

        if i < total - 1:
            time.sleep(2)

    # Print detailed results
    print(f"\n{'=' * 65}")
    print(f"RESULTS")
    print(f"{'=' * 65}")

    for r in all_results:
        icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "⚠️ "}[r["status"]]
        print(f"\n{icon} {r['name']}")
        print(f"   Path: {r['path']}")
        print(f"   Params: {r['params']}")
        print(f"   HTTP code: {r['code']}")

        if r["status"] == "PASS":
            print(f"   Shape: {r['data_shape']}")
            if r["sample"]:
                print(f"   Sample: {r['sample'][:200]}")
        else:
            detail = ""
            if r["code"] == "401" or (r["message"] and "Upgrade" in str(r["message"])):
                detail = "TIER-BLOCKED (401 Upgrade plan)"
            elif r["code"] == "404":
                detail = "PATH NOT FOUND (404)"
            elif r["code"] == "400":
                detail = f"BAD PARAMS: {r['message'][:120] if r['message'] else ''}"
            else:
                detail = f"{r['message'][:120] if r['message'] else 'unknown'}"
            print(f"   Error: {detail}")

    # Summary
    print(f"\n{'=' * 65}")
    print(f"SUMMARY: ✅ {pass_count} PASS | ❌ {fail_count} FAIL | ⚠️  {error_count} ERROR")
    print(f"{'=' * 65}")

    # L/S ratio verdict
    ls_results = [r for r in all_results if "L/S" in r["name"]]
    ls_pass = [r for r in ls_results if r["status"] == "PASS"]
    print(f"\nL/S Ratio with BTCUSDT: {len(ls_pass)}/{len(ls_results)} working")

    # Coinbase Premium verdict
    cb_results = [r for r in all_results if "Coinbase" in r["name"]]
    cb_pass = [r for r in cb_results if r["status"] == "PASS"]
    print(f"Coinbase Premium: {len(cb_pass)}/{len(cb_results)} working")

    # Save report
    report_dir = PROJECT_ROOT / "results"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"coinglass_probe_fix_{datetime.now().strftime('%Y-%m-%d')}.md"

    lines = []
    lines.append(f"# Coinglass Fix-Probe — L/S Ratio + Coinbase Premium")
    lines.append(f"**Date:** {now}")
    lines.append(f"**Results:** ✅ {pass_count} PASS | ❌ {fail_count} FAIL | ⚠️ {error_count} ERROR")
    lines.append("")

    for r in all_results:
        status = r["status"]
        if status == "PASS":
            lines.append(f"### ✅ {r['name']}")
            lines.append(f"- Path: `{r['path']}`")
            lines.append(f"- Params: `{r['params']}`")
            lines.append(f"- Shape: {r['data_shape']}")
            lines.append(f"- Sample: `{r['sample'][:200] if r['sample'] else 'n/a'}`")
        else:
            lines.append(f"### ❌ {r['name']}")
            lines.append(f"- Path: `{r['path']}`")
            lines.append(f"- Params: `{r['params']}`")
            lines.append(f"- Code: {r['code']}")
            lines.append(f"- Error: {r['message'][:200] if r['message'] else 'unknown'}")
        lines.append("")

    lines.append("## Verdict")
    lines.append(f"- L/S Ratio with BTCUSDT: **{len(ls_pass)}/{len(ls_results)}** working")
    lines.append(f"- Coinbase Premium: **{len(cb_pass)}/{len(cb_results)}** working")

    with open(report_path, "w") as f:
        f.write("\n".join(lines))

    print(f"\n💾 Report saved to: {report_path}")


if __name__ == "__main__":
    main()
