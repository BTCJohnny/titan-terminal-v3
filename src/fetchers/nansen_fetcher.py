#!/usr/bin/env python3
"""
Nansen REST API Fetcher
========================
Direct REST API fetcher for Nansen on-chain intelligence. Runs on cron
for automated data collection, also available for interactive CLI queries.

Dual-path architecture:
  Cron  → this script calls Nansen REST API → stores to DB + warms cache
  Live  → Claude calls Nansen MCP tools    → also stores to cache

Both paths feed the same snapshot tables and cache in titan_intelligence.db.

Endpoints (v1):
  /api/v1/tgm/flow-intelligence   → token_recent_flows_summary
  /api/v1/tgm/flows               → token_flows
  /api/v1/tgm/holders             → token_current_top_holders (onchain)
  /api/v1/tgm/perp-positions      → token_current_top_holders (perps)
  /api/v1/tgm/indicators          → token_quant_scores
  /api/v1/smart-money/perp-trades  → smart_traders_and_funds_perp_trades
  /api/v1/smart-money/holdings     → smart_traders_and_funds_token_balances

Usage:
  # Cron mode (every 6h via snapshot_cron.sh)
  python3 src/fetchers/nansen_fetcher.py --snapshot-all --json

  # Interactive queries
  python3 src/fetchers/nansen_fetcher.py --token ETH --flows
  python3 src/fetchers/nansen_fetcher.py --token ETH --holders
  python3 src/fetchers/nansen_fetcher.py --token BTC --indicators
  python3 src/fetchers/nansen_fetcher.py --perp-trades
  python3 src/fetchers/nansen_fetcher.py --sm-holdings

  # Status
  python3 src/fetchers/nansen_fetcher.py --freshness
"""

import argparse
import json
import os
import sys
import time
import uuid
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.storage.nansen_cache import store_response, check_cache
from src.storage.intelligence import (
    log_nansen_snapshot, log_snapshot_run, finish_snapshot_run,
    check_snapshot_freshness, log_flow_snapshot
)

# ============================================================================
# Configuration
# ============================================================================

BASE_URL = "https://api.nansen.ai/api/v1"

# Token addresses for on-chain endpoints (ethereum unless noted).
# Perp endpoints use symbol directly — no address needed.
TOKEN_REGISTRY = {
    "ETH":    {"address": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", "chain": "ethereum"},
    "BTC":    {"address": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599", "chain": "ethereum"},
    "SOL":    {"address": "So11111111111111111111111111111111111111112",  "chain": "solana"},
    "LINK":   {"address": "0x514910771af9ca656af840dff83e8264ecf986ca", "chain": "ethereum"},
    "AAVE":   {"address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9", "chain": "ethereum"},
    "UNI":    {"address": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984", "chain": "ethereum"},
    "MKR":    {"address": "0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2", "chain": "ethereum"},
    "PENDLE": {"address": "0x808507121b80c02388fad14726482e061b8da827", "chain": "ethereum"},
    "TAO":    {"address": "0x77e06c9eccf2e797fd462a92b6d7642ef85b0a44", "chain": "ethereum"},
    "RENDER": {"address": "0x6de037ef9ad2725eb40118bb1702ebb27e4aeb24", "chain": "ethereum"},
    "ARB":    {"address": "0xb50721bcf8d664c30412cfbc6cf7a15145234ad1", "chain": "ethereum"},
    "OP":     {"address": "0x4200000000000000000000000000000000000042", "chain": "optimism"},
    "HYPE":   {"address": "0x93773942b8cce35bb109bf952d85a4a3e592d30a", "chain": "ethereum"},
}

# Rate limiting (conservative — API allows 20/s, 500/min)
_request_timestamps: list[float] = []
RATE_LIMIT_PER_SECOND = 15
RATE_LIMIT_PER_MINUTE = 400
REQUEST_DELAY = 0.3  # minimum seconds between requests

_api_key_cache: str | None = None


def _load_api_key() -> str:
    global _api_key_cache
    if _api_key_cache:
        return _api_key_cache
    key = os.environ.get("NANSEN_API_KEY")
    if not key:
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("NANSEN_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not key:
        print("Error: NANSEN_API_KEY not found in env or .env", file=sys.stderr)
        sys.exit(1)
    _api_key_cache = key
    return key


def _resolve_token(symbol: str) -> dict | None:
    """Look up token address and chain from registry."""
    info = TOKEN_REGISTRY.get(symbol.upper())
    if not info:
        print(f"  Token {symbol} not in registry. "
              f"Known: {', '.join(sorted(TOKEN_REGISTRY.keys()))}",
              file=sys.stderr)
    return info


def _parse_flow_to_structured(token: str, data: dict, lookback: str = "1d") -> str | None:
    """
    Parse raw Nansen flow-intelligence response into a structured
    flow_snapshots row via log_flow_snapshot().

    Returns snapshot_id on success, None on failure.
    """
    try:
        # Handle both list and dict responses
        if isinstance(data, list):
            entry = data[0] if data else {}
        elif isinstance(data, dict):
            inner = data.get("data", data)
            entry = inner[0] if isinstance(inner, list) and inner else inner
        else:
            return None

        if not entry:
            return None

        def _signal(net_flow):
            if net_flow is None:
                return None
            if net_flow > 0:
                return "bullish"
            elif net_flow < 0:
                return "bearish"
            return "neutral"

        exchange_net = entry.get("exchange_net_flow_usd")
        smart_net = entry.get("smart_trader_net_flow_usd")
        whale_net = entry.get("whale_net_flow_usd")
        top_pnl_net = entry.get("top_pnl_net_flow_usd")
        fresh_net = entry.get("fresh_wallets_net_flow_usd")

        snapshot_id = log_flow_snapshot(
            token=token,
            chain="ethereum",
            exchange_net_flow=exchange_net,
            exchange_wallets=entry.get("exchange_wallet_count"),
            exchange_signal=_signal(exchange_net),
            smart_money_net_flow=smart_net,
            smart_money_wallets=entry.get("smart_trader_wallet_count"),
            smart_money_signal=_signal(smart_net),
            whale_net_flow=whale_net,
            whale_wallets=entry.get("whale_wallet_count"),
            whale_signal=_signal(whale_net),
            top_pnl_net_flow=top_pnl_net,
            top_pnl_wallets=entry.get("top_pnl_wallet_count"),
            top_pnl_signal=_signal(top_pnl_net),
            fresh_wallet_net_flow=fresh_net,
            fresh_wallet_count=entry.get("fresh_wallets_wallet_count"),
            fresh_wallet_signal=_signal(fresh_net),
            lookback_period=lookback,
            raw_data=entry,
        )
        return snapshot_id
    except Exception as e:
        print(f"  Warning: flow_snapshots parse failed: {e}", file=sys.stderr)
        return None


# ============================================================================
# HTTP Client
# ============================================================================

def nansen_post(endpoint: str, body: dict, debug: bool = False) -> dict | None:
    """POST to Nansen REST API with rate limiting and retry."""
    global _request_timestamps
    api_key = _load_api_key()

    # Rate limit
    now = time.time()
    _request_timestamps = [t for t in _request_timestamps if now - t < 60]
    recent_1s = sum(1 for t in _request_timestamps if now - t < 1)
    if recent_1s >= RATE_LIMIT_PER_SECOND:
        time.sleep(1.0)
    if len(_request_timestamps) >= RATE_LIMIT_PER_MINUTE:
        wait = 60 - (now - _request_timestamps[0])
        if wait > 0:
            print(f"  Rate limit: waiting {wait:.0f}s", file=sys.stderr)
            time.sleep(wait)

    # Minimum delay between requests
    if _request_timestamps:
        elapsed = time.time() - _request_timestamps[-1]
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)

    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    headers = {"Content-Type": "application/json", "apikey": api_key}

    if debug:
        print(f"  POST {url}", file=sys.stderr)
        print(f"  Body: {json.dumps(body)[:300]}", file=sys.stderr)

    try:
        resp = requests.post(url, json=body, headers=headers, timeout=30)
        _request_timestamps.append(time.time())

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 60))
            print(f"  429 rate limited — retrying in {retry_after}s",
                  file=sys.stderr)
            time.sleep(retry_after)
            resp = requests.post(url, json=body, headers=headers, timeout=30)
            _request_timestamps.append(time.time())

        if resp.status_code != 200:
            err = resp.text[:300]
            print(f"  API {resp.status_code}: {err}", file=sys.stderr)
            return None

        result = resp.json()
        credits_used = resp.headers.get("X-Nansen-Credits-Used")
        credits_left = resp.headers.get("X-Nansen-Credits-Remaining")
        if debug and credits_used:
            print(f"  Credits: {credits_used} used, {credits_left} remaining",
                  file=sys.stderr)
        return result

    except requests.exceptions.Timeout:
        print(f"  Timeout: {url}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  Request error: {e}", file=sys.stderr)
        return None


# ============================================================================
# Fetch Functions
# ============================================================================

def fetch_flow_intelligence(token: str, timeframe: str = "1d",
                            debug: bool = False) -> dict | None:
    """Flow intelligence by segment (= MCP token_recent_flows_summary).
    Endpoint: POST /api/v1/tgm/flow-intelligence
    Note: BTC and Hyperliquid tokens are NOT supported.
    """
    info = _resolve_token(token)
    if not info:
        return None
    body = {
        "chain": info["chain"],
        "token_address": info["address"],
        "timeframe": timeframe,
    }
    return nansen_post("tgm/flow-intelligence", body, debug=debug)


def fetch_flows(token: str, segment: str = "top_100_holders",
                days_back: int = 1, debug: bool = False) -> dict | None:
    """Hourly flows by holder segment (= MCP token_flows).
    Endpoint: POST /api/v1/tgm/flows
    """
    info = _resolve_token(token)
    if not info:
        return None
    now = datetime.now(timezone.utc)
    body = {
        "chain": info["chain"],
        "token_address": info["address"],
        "label": segment,
        "date": {
            "from": (now - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "pagination": {"page": 1, "per_page": 100},
    }
    return nansen_post("tgm/flows", body, debug=debug)


def fetch_holders(token: str, label_type: str = "all_holders",
                  debug: bool = False) -> dict | None:
    """On-chain top holders (= MCP token_current_top_holders, onchain mode).
    Endpoint: POST /api/v1/tgm/holders
    """
    info = _resolve_token(token)
    if not info:
        return None
    body = {
        "chain": info["chain"],
        "token_address": info["address"],
        "label_type": label_type,
        "pagination": {"page": 1, "per_page": 25},
        "order_by": [{"field": "value_usd", "direction": "DESC"}],
    }
    return nansen_post("tgm/holders", body, debug=debug)


def fetch_perp_positions(token: str, label_type: str = "smart_money",
                         debug: bool = False) -> dict | None:
    """Hyperliquid perp positions (= MCP token_current_top_holders, perps mode).
    Endpoint: POST /api/v1/tgm/perp-positions
    """
    body = {
        "token_symbol": token.upper(),
        "label_type": label_type,
        "pagination": {"page": 1, "per_page": 25},
        "order_by": [{"field": "position_value_usd", "direction": "DESC"}],
    }
    return nansen_post("tgm/perp-positions", body, debug=debug)


def fetch_indicators(token: str, debug: bool = False) -> dict | None:
    """Nansen quant indicators (= MCP token_quant_scores).
    Endpoint: POST /api/v1/tgm/indicators
    """
    info = _resolve_token(token)
    if not info:
        return None
    body = {
        "chain": info["chain"],
        "token_address": info["address"],
    }
    return nansen_post("tgm/indicators", body, debug=debug)


def fetch_sm_perp_trades(debug: bool = False) -> dict | None:
    """Smart money perp trades (= MCP smart_traders_and_funds_perp_trades).
    Endpoint: POST /api/v1/smart-money/perp-trades
    """
    body = {
        "pagination": {"page": 1, "per_page": 25},
        "order_by": [{"field": "value_usd", "direction": "DESC"}],
    }
    return nansen_post("smart-money/perp-trades", body, debug=debug)


def fetch_sm_holdings(chains: list | None = None,
                      debug: bool = False) -> dict | None:
    """Smart money token holdings (= MCP smart_traders_and_funds_token_balances).
    Endpoint: POST /api/v1/smart-money/holdings
    """
    body = {
        "chains": chains or ["all"],
        "pagination": {"page": 1, "per_page": 25},
        "order_by": [{"field": "value_usd", "direction": "DESC"}],
    }
    return nansen_post("smart-money/holdings", body, debug=debug)


# ============================================================================
# Snapshot Orchestrator
# ============================================================================

def run_snapshot_all(debug: bool = False) -> dict:
    """
    Run all Nansen snapshot jobs via REST API.
    Stores to snapshot tables AND warms the cache.

    Budget: ~12 API calls per cycle.
    """
    run_id = str(uuid.uuid4())[:8]
    started = datetime.now(timezone.utc).isoformat()

    try:
        log_snapshot_run(run_id, "nansen")
    except Exception as e:
        print(f"  Warning: Could not init snapshot metadata: {e}",
              file=sys.stderr)

    succeeded = 0
    failed = 0
    rows = 0
    errors: list[str] = []

    def _snap(label: str, fetch_fn, table: str, token: str = "_ALL",
              cache_tool: str | None = None, cache_params: dict | None = None,
              post_process=None, **db_kwargs):
        """Execute one snapshot job: fetch → store → cache → post-process."""
        nonlocal succeeded, failed, rows
        try:
            print(f"  [{label}] ", end="", flush=True, file=sys.stderr)
            data = fetch_fn()
            if data is None:
                print("FAIL", file=sys.stderr)
                failed += 1
                errors.append(f"{label}: fetch returned None")
                return

            # Extract data payload (REST wraps in {data: [...], warnings: ...})
            payload = data.get("data", data) if isinstance(data, dict) else data

            # Store in snapshot table
            row_id = log_nansen_snapshot(table, token=token, data=payload,
                                         **db_kwargs)
            if row_id > 0:
                print("OK", end="", file=sys.stderr)
                succeeded += 1
                rows += 1
            else:
                print("STORE_FAIL", file=sys.stderr)
                failed += 1
                errors.append(f"{label}: storage failed")
                return

            # Warm cache for MCP sessions
            if cache_tool:
                try:
                    store_response(cache_tool, token, cache_params or {},
                                   json.dumps(data), tool_source="nansen_api")
                    print(" +cache", file=sys.stderr)
                except Exception:
                    print(" (cache skip)", file=sys.stderr)
            else:
                print("", file=sys.stderr)

            # Post-process (e.g., parse into structured tables)
            if post_process:
                try:
                    post_process(token, payload)
                except Exception as pp_err:
                    print(f"  Warning: post-process failed: {pp_err}", file=sys.stderr)

        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            failed += 1
            errors.append(f"{label}: {str(e)[:100]}")

    total_jobs = 12
    print(f"\n  === Nansen Snapshot Run {run_id} ===", file=sys.stderr)
    print(f"  Started: {started}", file=sys.stderr)
    print(f"  Jobs: {total_jobs} endpoints via REST API", file=sys.stderr)
    print(f"  Source: https://api.nansen.ai/api/v1\n", file=sys.stderr)

    # ── 1. Flow Intelligence — ETH only (BTC not supported) ──
    for period in ["1d", "7d"]:
        _snap(
            f"ETH flow intelligence ({period})",
            lambda p=period: fetch_flow_intelligence("ETH", timeframe=p,
                                                     debug=debug),
            "nansen_flow_snapshots", token="ETH",
            cache_tool="token_recent_flows_summary",
            cache_params={"chain": "ethereum", "lookbackPeriod": period},
            post_process=(lambda t, d, lb=period: _parse_flow_to_structured(t, d, lb)),
            tool_name="token_recent_flows_summary",
            holder_segment="all", lookback_period=period,
        )

    # ── 2. Flows by Segment — ETH ──
    for segment in ["exchange", "whale", "smart_money"]:
        _snap(
            f"ETH flows ({segment})",
            lambda s=segment: fetch_flows("ETH", segment=s, debug=debug),
            "nansen_flow_snapshots", token="ETH",
            cache_tool="token_flows",
            cache_params={"chain": "ethereum", "holder_segment": segment,
                          "lookbackPeriod": "1d"},
            tool_name="token_flows",
            holder_segment=segment, lookback_period="1d",
        )

    # ── 3. On-chain Holders — ETH ──
    for label_type, rest_label in [("smart_money", "smart_money"),
                                    ("top_100_holders", "all_holders")]:
        _snap(
            f"ETH holders ({label_type})",
            lambda lt=rest_label: fetch_holders("ETH", label_type=lt,
                                                 debug=debug),
            "nansen_holder_snapshots", token="ETH",
            cache_tool="token_current_top_holders",
            cache_params={"chain": "ethereum", "labelType": label_type},
            tool_name="token_current_top_holders",
            chain="ethereum", label_type=label_type, mode="onchain",
        )

    # ── 4. Perp Positions — BTC + ETH on Hyperliquid ──
    for token in ["BTC", "ETH"]:
        _snap(
            f"{token} perp positions (SM, HL)",
            lambda t=token: fetch_perp_positions(t, debug=debug),
            "nansen_holder_snapshots", token=token,
            cache_tool="token_current_top_holders",
            cache_params={"chain": "hyperliquid", "labelType": "smart_money",
                          "mode": "perps"},
            tool_name="token_current_top_holders",
            chain="hyperliquid", label_type="smart_money", mode="perps",
        )

    # ── 5. SM Perp Trades ──
    _snap(
        "SM perp trades (latest)",
        lambda: fetch_sm_perp_trades(debug=debug),
        "nansen_perp_snapshots", token="_ALL",
        cache_tool="smart_traders_and_funds_perp_trades",
        cache_params={"sortBy": "valueUsd", "sortOrder": "desc"},
        tool_name="smart_traders_and_funds_perp_trades",
    )

    # ── 6. Quant Indicators — BTC + ETH ──
    for token in ["BTC", "ETH"]:
        _snap(
            f"{token} indicators",
            lambda t=token: fetch_indicators(t, debug=debug),
            "nansen_quant_snapshots", token=token,
            cache_tool="token_quant_scores",
            cache_params={"symbol": token},
            tool_name="token_quant_scores",
        )

    # Finalize
    try:
        finish_snapshot_run(run_id, succeeded, failed, rows, errors or None)
    except Exception:
        pass

    finished = datetime.now(timezone.utc).isoformat()
    print(f"\n  === Nansen Snapshot Complete ===", file=sys.stderr)
    print(f"  Run ID: {run_id}", file=sys.stderr)
    print(f"  Finished: {finished}", file=sys.stderr)
    print(f"  Stored: {succeeded} | Failed: {failed} | Rows: {rows}",
          file=sys.stderr)
    if errors:
        print(f"  Errors:", file=sys.stderr)
        for e in errors:
            print(f"    - {e}", file=sys.stderr)

    return {
        "run_id": run_id,
        "started": started,
        "finished": finished,
        "succeeded": succeeded,
        "failed": failed,
        "rows_inserted": rows,
        "errors": errors,
    }


# ============================================================================
# Pretty-Print Helpers (interactive mode)
# ============================================================================

def _print_flow_intelligence(token: str, data: dict):
    print(f"\n  === {token} Flow Intelligence ===\n")
    entries = data.get("data", [])
    if not entries:
        print("  No data")
        return
    entry = entries[0] if isinstance(entries, list) else entries
    segments = [
        ("public_figure", "Public Figures"),
        ("top_pnl", "Top PnL Traders"),
        ("whale", "Whales"),
        ("smart_trader", "Smart Traders"),
        ("exchange", "Exchanges"),
        ("fresh_wallets", "Fresh Wallets"),
    ]
    for key, name in segments:
        net = entry.get(f"{key}_net_flow_usd")
        avg = entry.get(f"{key}_avg_flow_usd")
        wallets = entry.get(f"{key}_wallet_count")
        if net is not None:
            sign = "+" if net >= 0 else ""
            avg_str = f"avg {avg:>12,.0f}" if avg is not None else "avg          N/A"
            print(f"  {name:<20} {sign}{net:>14,.0f} USD"
                  f"  ({avg_str}, {wallets or '?'} wallets)")


def _print_holders(token: str, data: dict):
    print(f"\n  === {token} Top Holders ===\n")
    entries = data.get("data", [])
    if not entries:
        print("  No data")
        return
    print(f"  {'Label':<32} {'Balance':>14}  {'Value USD':>14}  {'Own%':>6}")
    print(f"  {'─'*32} {'─'*14}  {'─'*14}  {'─'*6}")
    for h in entries[:15]:
        label = (h.get("address_label") or h.get("address", "?"))[:32]
        amount = h.get("token_amount", 0)
        value = h.get("value_usd", 0)
        pct = h.get("ownership_percentage", 0)
        print(f"  {label:<32} {amount:>14,.2f}  ${value:>13,.0f}  {pct:>5.2f}%")


def _print_perp_positions(token: str, data: dict):
    print(f"\n  === {token} Perp Positions (Hyperliquid) ===\n")
    entries = data.get("data", [])
    if not entries:
        print("  No data")
        return
    print(f"  {'Label':<25} {'Side':<6} {'Value USD':>14}"
          f"  {'Entry':>10} {'Liq':>10}  {'uPnL':>12}")
    print(f"  {'─'*25} {'─'*6} {'─'*14}  {'─'*10} {'─'*10}  {'─'*12}")
    for p in entries[:15]:
        label = (p.get("address_label") or p.get("address", "?"))[:25]
        side = p.get("side", "?")
        val = p.get("position_value_usd", 0)
        entry = p.get("entry_price", 0)
        liq = p.get("liquidation_price", 0)
        upnl = p.get("upnl_usd", 0)
        sign = "+" if upnl >= 0 else ""
        print(f"  {label:<25} {side:<6} ${val:>13,.0f}"
              f"  {entry:>10,.2f} {liq:>10,.2f}  {sign}{upnl:>11,.0f}")


def _print_indicators(token: str, data: dict):
    print(f"\n  === {token} Nansen Indicators ===\n")
    for category in ["reward_indicators", "risk_indicators"]:
        indicators = data.get(category, [])
        if not indicators:
            continue
        title = "REWARD" if "reward" in category else "RISK"
        print(f"  {title} Indicators:")
        for ind in indicators:
            name = ind.get("indicator_type", "?")
            score = ind.get("score", "?")
            signal = ind.get("signal", "?")
            pct = ind.get("signal_percentile", "?")
            triggered = (ind.get("last_trigger_on") or "?")[:10]
            print(f"    {name:<25} {score:<10} "
                  f"signal={signal:<10} pct={pct:<6} ({triggered})")
        print()


def _print_sm_perp_trades(data: dict):
    print(f"\n  === Smart Money Perp Trades ===\n")
    entries = data.get("data", [])
    if not entries:
        print("  No data")
        return
    print(f"  {'Token':<8} {'Side':<6} {'Action':<8}"
          f"  {'Value USD':>12}  {'Trader':<25}")
    print(f"  {'─'*8} {'─'*6} {'─'*8}  {'─'*12}  {'─'*25}")
    for t in entries[:20]:
        token = t.get("token_symbol", "?")
        side = t.get("side", "?")
        action = t.get("action", "?")
        value = t.get("value_usd", 0)
        label = (t.get("trader_address_label")
                 or t.get("trader_address", "?"))[:25]
        print(f"  {token:<8} {side:<6} {action:<8}"
              f"  ${value:>11,.0f}  {label}")


def _print_sm_holdings(data: dict):
    print(f"\n  === Smart Money Holdings ===\n")
    entries = data.get("data", [])
    if not entries:
        print("  No data")
        return
    print(f"  {'Token':<10} {'Chain':<12} {'Value USD':>14}"
          f"  {'Holders':>8}  {'24h Chg':>8}")
    print(f"  {'─'*10} {'─'*12} {'─'*14}  {'─'*8}  {'─'*8}")
    for h in entries[:20]:
        token = h.get("token_symbol", "?")
        chain = h.get("chain", "?")
        value = h.get("value_usd", 0)
        holders = h.get("holders_count", 0)
        chg = h.get("balance_24h_percent_change", 0)
        sign = "+" if chg >= 0 else ""
        print(f"  {token:<10} {chain:<12} ${value:>13,.0f}"
              f"  {holders:>8}  {sign}{chg:.1f}%")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Nansen REST API Fetcher — direct API for cron + CLI")
    parser.add_argument("--snapshot-all", action="store_true",
                        help="Run all Nansen snapshots via REST API")
    parser.add_argument("--token", type=str,
                        help="Token symbol (ETH, BTC, SOL, ...)")
    parser.add_argument("--flows", action="store_true",
                        help="Fetch flow intelligence for --token")
    parser.add_argument("--holders", action="store_true",
                        help="Fetch on-chain top holders for --token")
    parser.add_argument("--perp-pos", action="store_true",
                        help="Fetch HL perp positions for --token")
    parser.add_argument("--indicators", action="store_true",
                        help="Fetch quant indicators for --token")
    parser.add_argument("--perp-trades", action="store_true",
                        help="Fetch SM perp trades (all tokens)")
    parser.add_argument("--sm-holdings", action="store_true",
                        help="Fetch SM token holdings (all chains)")
    parser.add_argument("--freshness", action="store_true",
                        help="Check Nansen snapshot table freshness")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    parser.add_argument("--debug", action="store_true",
                        help="Show API requests and responses")
    args = parser.parse_args()

    # ── Freshness check ──
    if args.freshness:
        freshness = check_snapshot_freshness()
        nansen = {k: v for k, v in freshness.items()
                  if k.startswith("nansen_")}
        if args.json:
            print(json.dumps(nansen, indent=2, default=str))
        else:
            print(f"\n  === Nansen Snapshot Freshness ===\n")
            for table, info in sorted(nansen.items()):
                last = (info["last_snapshot"][:19]
                        if info["last_snapshot"] else "NEVER")
                age = (f"{info['age_hours']:.1f}h"
                       if info["age_hours"] is not None else "-")
                status = "STALE" if info["stale"] else "OK"
                print(f"  {table:<30} {last:<22} {age:<8} {status}")
        return

    # ── Snapshot mode (cron) ──
    if args.snapshot_all:
        pid_file = PROJECT_ROOT / "logs" / "nansen_fetcher.pid"
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        if pid_file.exists():
            try:
                old_pid = int(pid_file.read_text().strip())
                os.kill(old_pid, 0)
                print(f"Already running (PID {old_pid}). Skipping.",
                      file=sys.stderr)
                sys.exit(0)
            except (ProcessLookupError, ValueError):
                pass
        pid_file.write_text(str(os.getpid()))
        try:
            result = run_snapshot_all(debug=args.debug)
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            sys.exit(0 if result["failed"] == 0 else 1)
        finally:
            try:
                pid_file.unlink()
            except Exception:
                pass
        return

    # ── Interactive: token-specific queries ──
    if args.token:
        token = args.token.upper()

        if args.flows:
            data = fetch_flow_intelligence(token, debug=args.debug)
            if not data:
                print(f"No flow data for {token}")
                sys.exit(1)
            if args.json:
                print(json.dumps(data, indent=2))
            else:
                _print_flow_intelligence(token, data)
            return

        if args.holders:
            data = fetch_holders(token, debug=args.debug)
            if not data:
                print(f"No holder data for {token}")
                sys.exit(1)
            if args.json:
                print(json.dumps(data, indent=2))
            else:
                _print_holders(token, data)
            return

        if args.perp_pos:
            data = fetch_perp_positions(token, debug=args.debug)
            if not data:
                print(f"No perp position data for {token}")
                sys.exit(1)
            if args.json:
                print(json.dumps(data, indent=2))
            else:
                _print_perp_positions(token, data)
            return

        if args.indicators:
            data = fetch_indicators(token, debug=args.debug)
            if not data:
                print(f"No indicator data for {token}")
                sys.exit(1)
            if args.json:
                print(json.dumps(data, indent=2))
            else:
                _print_indicators(token, data)
            return

        print(f"Specify --flows, --holders, --perp-pos, or --indicators "
              f"with --token")
        return

    # ── Interactive: global queries ──
    if args.perp_trades:
        data = fetch_sm_perp_trades(debug=args.debug)
        if not data:
            print("No SM perp trade data")
            sys.exit(1)
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            _print_sm_perp_trades(data)
        return

    if args.sm_holdings:
        data = fetch_sm_holdings(debug=args.debug)
        if not data:
            print("No SM holdings data")
            sys.exit(1)
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            _print_sm_holdings(data)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
