#!/usr/bin/env python3
"""
Nansen API Response Cache
=========================
Stores and retrieves Nansen MCP responses to avoid re-fetching recent data.

TTLs by tool (how long a response is considered fresh):
  - token_recent_flows_summary   : 6h  (flows shift within hours)
  - token_current_top_holders    : 12h (onchain positions change slowly)
  - token_current_top_holders    : 1h  (perps mode — positions change fast)
  - general_search               : 24h (token identity rarely changes)
  - smart_traders_and_funds_*    : 2h
  - token_flows                  : 6h
  - token_who_bought_sold        : 6h
  - wallet_pnl_*                 : 12h
  - default                      : 6h

Usage:
  # Check cache before calling Nansen:
  python3 src/storage/nansen_cache.py check --tool token_recent_flows_summary \\
      --token ETH --params '{"chain":"ethereum","lookbackPeriod":"1d"}'

  # Store after a Nansen call:
  python3 src/storage/nansen_cache.py store --tool token_recent_flows_summary \\
      --token ETH --params '{"chain":"ethereum","lookbackPeriod":"1d"}' \\
      --response '{"result":"..."}'

  # Show cache stats:
  python3 src/storage/nansen_cache.py stats

  # Show cached entries for a token:
  python3 src/storage/nansen_cache.py list --token ETH

  # Purge expired entries:
  python3 src/storage/nansen_cache.py purge

Exit codes for `check`:
  0 = CACHE_HIT   (response printed to stdout)
  1 = CACHE_MISS  (nothing printed, caller must fetch from Nansen)
"""

import sqlite3
import json
import hashlib
import argparse
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "titan_intelligence.db"

# TTL in hours per tool type
TTL_HOURS = {
    "general_search": 24,
    "token_recent_flows_summary": 6,
    "token_flows": 6,
    "token_who_bought_sold": 6,
    "token_transfers": 6,
    "token_ohlcv": 6,
    "token_dex_trades": 6,
    "token_recent_flows_summary_multi": 6,
    "smart_traders_and_funds_perp_trades": 2,
    "smart_traders_and_funds_token_balances": 2,
    "token_current_top_holders_onchain": 12,
    "token_current_top_holders_perps": 1,
    "token_current_top_holders": 12,   # default (onchain assumed)
    "token_pnl_leaderboard": 12,
    "token_quant_scores": 12,
    "wallet_pnl_for_token": 12,
    "wallet_pnl_summary": 12,
    "address_portfolio": 12,
    "address_historical_balances": 12,
    "address_counterparties": 12,
    "address_transactions": 6,
    "address_related_addresses": 24,
    "nansen_score_top_tokens": 12,
    "token_discovery_screener": 12,
    "growth_chain_rank": 12,
    "hyperliquid_leaderboard": 2,
    "transaction_lookup": 24,
    # Coinglass TTLs (liquidation data moves fast)
    "coinglass_liquidation_map": 1,
    "coinglass_max_pain": 1,
    "coinglass_large_limit_orders": 1,
    "coinglass_aggregated_history": 6,
    "coinglass_coin_list": 6,
    # Coinglass derivatives intelligence TTLs
    "coinglass_funding_rates": 1,
    "coinglass_oi_history": 1,
    "coinglass_oi_exchange_list": 1,
    "coinglass_global_ls_ratio": 2,
    "coinglass_top_ls_account": 2,
    "coinglass_top_ls_position": 2,
    "coinglass_btc_etf": 6,
    "coinglass_fear_greed": 6,
    "coinglass_coinbase_premium": 1,
    # Coinglass snapshot pipeline TTLs
    "coinglass_spot_cvd": 4,
    "coinglass_spot_taker": 4,
    "coinglass_spot_netflow": 4,
    "coinglass_spot_coin_netflow": 4,
    "coinglass_futures_basis": 4,
    "coinglass_futures_spot_vol": 6,
    "coinglass_opt_fut_oi_ratio": 6,
    "coinglass_agg_orderbook": 4,
    "coinglass_oi_exchange_hist": 4,
    "coinglass_liq_heatmap": 2,
    "coinglass_liq_heatmap_m3": 2,
    "coinglass_btc_sth_sopr": 6,
    "coinglass_btc_lth_sopr": 6,
    "coinglass_btc_sth_rp": 6,
    "coinglass_btc_lth_rp": 6,
    "coinglass_btc_nupl": 6,
    "coinglass_btc_active_addr": 6,
    "coinglass_btc_reserve_risk": 6,
    "coinglass_btc_correlation": 6,
    "coinglass_btc_macro_osc": 6,
    "coinglass_btc_etf_assets": 6,
    "coinglass_btc_etf_premium": 6,
    "coinglass_grayscale_premium": 6,
    "coinglass_funding_rate_ohlc": 4,
    "coinglass_liq_history": 4,
    "default": 6,
}


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _cache_key(tool_name: str, params: dict) -> str:
    """Stable hash of tool + params for cache lookup."""
    # Normalize: sort keys, strip nulls
    clean = {k: v for k, v in sorted(params.items()) if v is not None}
    raw = f"{tool_name}:{json.dumps(clean, sort_keys=True)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _ttl_for(tool_name: str, params: dict) -> int:
    """Return TTL in hours for a given tool call."""
    # Distinguish perps vs onchain for token_current_top_holders
    if tool_name == "token_current_top_holders":
        if params.get("mode") == "perps":
            return TTL_HOURS["token_current_top_holders_perps"]
        return TTL_HOURS["token_current_top_holders_onchain"]
    return TTL_HOURS.get(tool_name, TTL_HOURS["default"])


def check_cache(tool_name: str, token: str, params: dict) -> tuple[bool, str | None]:
    """
    Check if a fresh cached response exists.

    Returns:
        (hit, response_json) — hit=True means fresh cache found
    """
    cache_key = _cache_key(tool_name, params)
    ttl_hours = _ttl_for(tool_name, params)
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=ttl_hours)).isoformat()

    conn = get_connection()
    row = conn.execute(
        """SELECT r.response_json, q.timestamp_utc
           FROM mcp_queries q
           JOIN mcp_responses r ON q.query_id = r.query_id
           WHERE q.tool_name = ?
             AND q.context_token = ?
             AND q.parameters_json LIKE ?
             AND q.success = 1
             AND q.timestamp_utc > ?
           ORDER BY q.timestamp_utc DESC
           LIMIT 1""",
        (tool_name, token.upper(), f'%{cache_key}%', cutoff)
    ).fetchone()
    conn.close()

    if row:
        return True, row["response_json"]
    return False, None


def store_response(tool_name: str, token: str, params: dict, response: str,
                    tool_source: str = "nansen_mcp") -> str:
    """
    Store an API response in the cache.

    Args:
        tool_name: The tool/endpoint name
        token: Token symbol
        params: Query parameters
        response: JSON response string
        tool_source: Source identifier ("nansen_mcp", "coinglass_api", etc.)

    Returns:
        query_id
    """
    import uuid
    cache_key = _cache_key(tool_name, params)
    query_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    # Embed cache_key in parameters_json for lookup
    params_with_key = dict(params)
    params_with_key["_cache_key"] = cache_key

    conn = get_connection()
    conn.execute(
        """INSERT INTO mcp_queries
           (query_id, timestamp_utc, tool_name, tool_source, parameters_json,
            context_type, context_token, success)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (query_id, timestamp, tool_name, tool_source,
         json.dumps(params_with_key), "token", token.upper(), 1)
    )
    response_json = response if isinstance(response, str) else json.dumps(response)
    conn.execute(
        """INSERT INTO mcp_responses (query_id, response_json, response_size_bytes, created_at)
           VALUES (?, ?, ?, ?)""",
        (query_id, response_json, len(response_json), timestamp)
    )
    conn.commit()
    conn.close()

    return query_id


def get_stats() -> dict:
    """Return cache statistics."""
    conn = get_connection()

    total = conn.execute("SELECT COUNT(*) FROM mcp_queries WHERE tool_source IN ('nansen_mcp','nansen_api')").fetchone()[0]
    by_tool = conn.execute(
        """SELECT tool_name, COUNT(*) as cnt,
                  MAX(timestamp_utc) as latest,
                  SUM(r.response_size_bytes) as total_bytes
           FROM mcp_queries q
           JOIN mcp_responses r ON q.query_id = r.query_id
           WHERE q.tool_source IN ('nansen_mcp', 'nansen_api')
           GROUP BY tool_name
           ORDER BY cnt DESC"""
    ).fetchall()
    by_token = conn.execute(
        """SELECT context_token, COUNT(*) as cnt
           FROM mcp_queries
           WHERE tool_source IN ('nansen_mcp', 'nansen_api')
           GROUP BY context_token
           ORDER BY cnt DESC"""
    ).fetchall()
    conn.close()

    return {
        "total_cached_calls": total,
        "by_tool": [dict(r) for r in by_tool],
        "by_token": [dict(r) for r in by_token],
    }


def list_token(token: str) -> list:
    """List cached entries for a token."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT q.tool_name, q.timestamp_utc, q.parameters_json,
                  r.response_size_bytes
           FROM mcp_queries q
           JOIN mcp_responses r ON q.query_id = r.query_id
           WHERE q.context_token = ? AND q.tool_source = 'nansen_mcp'
           ORDER BY q.timestamp_utc DESC""",
        (token.upper(),)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def purge_expired() -> int:
    """Delete expired cache entries. Returns count deleted."""
    conn = get_connection()
    deleted = 0
    tools = conn.execute(
        "SELECT DISTINCT tool_name FROM mcp_queries"
    ).fetchall()

    for tool_row in tools:
        tool = tool_row["tool_name"]
        # Use the shortest TTL for safety since we don't have params here
        ttl = TTL_HOURS.get(tool, TTL_HOURS["default"])
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=ttl)).isoformat()
        query_ids = conn.execute(
            "SELECT query_id FROM mcp_queries WHERE tool_name=? AND timestamp_utc < ?",
            (tool, cutoff)
        ).fetchall()
        for qid in query_ids:
            conn.execute("DELETE FROM mcp_responses WHERE query_id=?", (qid["query_id"],))
            conn.execute("DELETE FROM mcp_queries WHERE query_id=?", (qid["query_id"],))
            deleted += 1

    conn.commit()
    conn.close()
    return deleted


def _age_str(timestamp_utc: str) -> str:
    """Human-readable age from ISO timestamp."""
    try:
        dt = datetime.fromisoformat(timestamp_utc.replace("Z", "+00:00"))
        diff = datetime.now(timezone.utc) - dt
        h = diff.total_seconds() / 3600
        if h < 1:
            return f"{int(diff.total_seconds() / 60)}m ago"
        if h < 24:
            return f"{h:.1f}h ago"
        return f"{diff.days}d ago"
    except Exception:
        return timestamp_utc


def main():
    parser = argparse.ArgumentParser(description="Nansen API response cache")
    sub = parser.add_subparsers(dest="cmd")

    # check
    p_check = sub.add_parser("check", help="Check if fresh cache exists")
    p_check.add_argument("--tool", required=True)
    p_check.add_argument("--token", required=True)
    p_check.add_argument("--params", default="{}", help="JSON params string")

    # store
    p_store = sub.add_parser("store", help="Store a Nansen response")
    p_store.add_argument("--tool", required=True)
    p_store.add_argument("--token", required=True)
    p_store.add_argument("--params", default="{}", help="JSON params string")
    p_store.add_argument("--response", required=True, help="JSON response string")
    p_store.add_argument("--source", default="nansen_mcp", help="Tool source (nansen_mcp, coinglass_api)")

    # stats
    sub.add_parser("stats", help="Show cache statistics")

    # list
    p_list = sub.add_parser("list", help="List cached entries for a token")
    p_list.add_argument("--token", required=True)

    # purge
    sub.add_parser("purge", help="Delete expired cache entries")

    args = parser.parse_args()

    if args.cmd == "check":
        params = json.loads(args.params)
        hit, response = check_cache(args.tool, args.token, params)
        if hit:
            ttl = _ttl_for(args.tool, params)
            print(f"CACHE_HIT (TTL={ttl}h)")
            print(response)
            sys.exit(0)
        else:
            ttl = _ttl_for(args.tool, params)
            print(f"CACHE_MISS (TTL={ttl}h — fetch from Nansen)")
            sys.exit(1)

    elif args.cmd == "store":
        params = json.loads(args.params)
        qid = store_response(args.tool, args.token, params, args.response,
                             tool_source=args.source)
        ttl = _ttl_for(args.tool, params)
        print(f"Stored: {qid} (TTL={ttl}h, source={args.source})")

    elif args.cmd == "stats":
        stats = get_stats()
        print(f"\nNansen Cache Stats")
        print(f"  Total cached calls: {stats['total_cached_calls']}")
        if stats["by_tool"]:
            print(f"\n  By tool:")
            for t in stats["by_tool"]:
                size_kb = (t["total_bytes"] or 0) / 1024
                print(f"    {t['tool_name']}: {t['cnt']} calls, {size_kb:.1f}KB, last {_age_str(t['latest'])}")
        if stats["by_token"]:
            print(f"\n  By token:")
            for t in stats["by_token"]:
                print(f"    {t['context_token']}: {t['cnt']} calls")

    elif args.cmd == "list":
        rows = list_token(args.token)
        if not rows:
            print(f"No cached entries for {args.token.upper()}")
        else:
            print(f"\nCached entries for {args.token.upper()} ({len(rows)} total):")
            for r in rows:
                params = json.loads(r["parameters_json"])
                params.pop("_cache_key", None)
                age = _age_str(r["timestamp_utc"])
                size_kb = (r["response_size_bytes"] or 0) / 1024
                print(f"  {r['tool_name']} | {age} | {size_kb:.1f}KB | {json.dumps(params)}")

    elif args.cmd == "purge":
        n = purge_expired()
        print(f"Purged {n} expired cache entries")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
