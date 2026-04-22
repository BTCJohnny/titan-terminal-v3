#!/usr/bin/env python3
"""
Nansen Snapshot Pipeline
========================
Reads from nansen_cache (mcp_queries/mcp_responses) and stores parsed
snapshots into dedicated nansen_* tables in titan_intelligence.db.

Runs on 6h cron, 15 minutes after Coinglass snapshot.

Budget: 33 credits/cycle (separate from interactive 20-credit cap).
Cache-first: skip live calls if data within TTL.

Usage:
    python3 src/fetchers/nansen_snapshot.py --snapshot-all
    python3 src/fetchers/nansen_snapshot.py --snapshot-all --json
    python3 src/fetchers/nansen_snapshot.py --freshness
"""

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.storage.nansen_cache import check_cache, store_response, TTL_HOURS
from src.storage.intelligence import (
    log_nansen_snapshot, log_snapshot_run, finish_snapshot_run,
    check_snapshot_freshness, get_connection
)

# ============================================================================
# Nansen MCP tool wrappers — check cache, optionally fetch live
# ============================================================================

# Credit costs per tool (from nansen-budget.md)
CREDIT_COSTS = {
    "token_flows": 2,
    "token_recent_flows_summary": 2,
    "token_current_top_holders": 4,
    "smart_traders_and_funds_perp_trades": 2,
    "token_quant_scores": 2,
}


def _get_cached_or_warn(tool_name: str, token: str, params: dict) -> tuple[dict | None, str | None]:
    """
    Check cache for a Nansen response.
    Returns (data_dict, query_id) or (None, None) if cache miss.
    """
    hit, response_json = check_cache(tool_name, token, params)
    if hit and response_json:
        try:
            data = json.loads(response_json)
            # Try to find the query_id for source tracking
            conn = get_connection()
            row = conn.execute(
                """SELECT query_id FROM mcp_queries
                   WHERE tool_name = ? AND context_token = ? AND success = 1
                   ORDER BY timestamp_utc DESC LIMIT 1""",
                (tool_name, token.upper())
            ).fetchone()
            conn.close()
            query_id = row["query_id"] if row else None
            return data, query_id
        except Exception:
            return None, None
    return None, None


# ============================================================================
# Snapshot definitions — what to capture each cycle
# ============================================================================

def _flow_snapshots(debug: bool = False) -> list[dict]:
    """Define all Nansen flow snapshot jobs."""
    jobs = []

    # ETH flows by segment (1d lookback)
    for segment in ["exchange", "whale", "smart_money"]:
        jobs.append({
            "tool": "token_flows",
            "token": "ETH",
            "params": {"chain": "ethereum", "holder_segment": segment,
                       "lookbackPeriod": "1d"},
            "table": "nansen_flow_snapshots",
            "kwargs": {"tool_name": "token_flows",
                       "holder_segment": segment, "lookback_period": "1d"},
            "label": f"ETH flows ({segment}, 1d)",
            "credits": 2,
        })

    # ETH recent flows summary (1d + 7d)
    for period in ["1d", "7d"]:
        jobs.append({
            "tool": "token_recent_flows_summary",
            "token": "ETH",
            "params": {"chain": "ethereum", "lookbackPeriod": period},
            "table": "nansen_flow_snapshots",
            "kwargs": {"tool_name": "token_recent_flows_summary",
                       "holder_segment": "all", "lookback_period": period},
            "label": f"ETH flows summary ({period})",
            "credits": 2,
        })

    return jobs


def _holder_snapshots(debug: bool = False) -> list[dict]:
    """Define all Nansen holder snapshot jobs."""
    jobs = []

    # ETH on-chain holders
    for label_type in ["smart_money", "top_100_holders"]:
        jobs.append({
            "tool": "token_current_top_holders",
            "token": "ETH",
            "params": {"chain": "ethereum", "labelType": label_type},
            "table": "nansen_holder_snapshots",
            "kwargs": {"tool_name": "token_current_top_holders",
                       "chain": "ethereum", "label_type": label_type,
                       "mode": "onchain"},
            "label": f"ETH holders ({label_type})",
            "credits": 4,
        })

    # BTC + ETH perps on Hyperliquid
    for token in ["BTC", "ETH"]:
        jobs.append({
            "tool": "token_current_top_holders",
            "token": token,
            "params": {"chain": "hyperliquid", "labelType": "smart_money",
                       "mode": "perps"},
            "table": "nansen_holder_snapshots",
            "kwargs": {"tool_name": "token_current_top_holders",
                       "chain": "hyperliquid", "label_type": "smart_money",
                       "mode": "perps"},
            "label": f"{token} perp holders (SM, HL)",
            "credits": 4,
        })

    return jobs


def _perp_snapshots(debug: bool = False) -> list[dict]:
    """Define Nansen perp trade snapshot jobs."""
    return [{
        "tool": "smart_traders_and_funds_perp_trades",
        "token": "_ALL",
        "params": {"sortBy": "valueUsd", "sortOrder": "desc"},
        "table": "nansen_perp_snapshots",
        "kwargs": {"tool_name": "smart_traders_and_funds_perp_trades"},
        "label": "SM perp trades (latest)",
        "credits": 2,
    }]


def _quant_snapshots(debug: bool = False) -> list[dict]:
    """Define Nansen quant score snapshot jobs."""
    jobs = []
    for token in ["BTC", "ETH"]:
        jobs.append({
            "tool": "token_quant_scores",
            "token": token,
            "params": {"symbol": token},
            "table": "nansen_quant_snapshots",
            "kwargs": {"tool_name": "token_quant_scores"},
            "label": f"{token} quant scores",
            "credits": 2,
        })
    return jobs


# ============================================================================
# Snapshot orchestrator
# ============================================================================

def run_snapshot_all(debug: bool = False) -> dict:
    """
    Run all Nansen snapshot jobs.
    Reads from cache first. If cache miss, logs warning (live MCP calls
    must be made by the interactive session or a separate trigger).

    Returns summary dict.
    """
    run_id = str(uuid.uuid4())[:8]
    started = datetime.now(timezone.utc).isoformat()

    try:
        log_snapshot_run(run_id, "nansen")
    except Exception as e:
        print(f"  Warning: Could not init snapshot metadata: {e}", file=sys.stderr)

    succeeded = 0
    failed = 0
    rows = 0
    errors = []
    credits_used = 0
    cache_hits = 0
    cache_misses = 0

    # Collect all jobs
    all_jobs = (
        _flow_snapshots(debug) +
        _holder_snapshots(debug) +
        _perp_snapshots(debug) +
        _quant_snapshots(debug)
    )

    print(f"\n  === Nansen Snapshot Run {run_id} ===", file=sys.stderr)
    print(f"  Started: {started}", file=sys.stderr)
    print(f"  Jobs: {len(all_jobs)} (budget: 33 credits)", file=sys.stderr)

    for job in all_jobs:
        label = job["label"]
        tool = job["tool"]
        token = job["token"]
        params = job["params"]
        table = job["table"]
        kwargs = job["kwargs"]

        try:
            print(f"  [{label}] ", end="", flush=True, file=sys.stderr)

            # Check cache
            data, query_id = _get_cached_or_warn(tool, token, params)

            if data is not None:
                cache_hits += 1
                print("CACHE_HIT -> ", end="", file=sys.stderr)
            else:
                cache_misses += 1
                print("CACHE_MISS (skipping live call) ", file=sys.stderr)
                errors.append(f"{label}: cache miss, no live data")
                failed += 1
                continue

            # Store snapshot
            row_id = log_nansen_snapshot(
                table, token=token, data=data,
                source_query_id=query_id, **kwargs)

            if row_id > 0:
                print("STORED", file=sys.stderr)
                succeeded += 1
                rows += 1
            else:
                print("STORE_FAIL", file=sys.stderr)
                failed += 1
                errors.append(f"{label}: storage failed")

        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            failed += 1
            errors.append(f"{label}: {str(e)[:100]}")

    # Finish metadata
    try:
        finish_snapshot_run(run_id, succeeded, failed, rows, errors or None)
    except Exception:
        pass

    finished = datetime.now(timezone.utc).isoformat()
    print(f"\n  === Nansen Snapshot Complete ===", file=sys.stderr)
    print(f"  Run ID: {run_id}", file=sys.stderr)
    print(f"  Finished: {finished}", file=sys.stderr)
    print(f"  Cache: {cache_hits} hits / {cache_misses} misses", file=sys.stderr)
    print(f"  Stored: {succeeded} | Failed: {failed} | Rows: {rows}", file=sys.stderr)
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
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "errors": errors,
    }


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Nansen Snapshot Pipeline")
    parser.add_argument("--snapshot-all", action="store_true",
                        help="Run all Nansen snapshots from cache into DB")
    parser.add_argument("--freshness", action="store_true",
                        help="Check Nansen snapshot table freshness")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    parser.add_argument("--debug", action="store_true",
                        help="Debug mode")
    args = parser.parse_args()

    if args.freshness:
        freshness = check_snapshot_freshness()
        nansen_tables = {k: v for k, v in freshness.items() if k.startswith("nansen_")}
        if args.json:
            print(json.dumps(nansen_tables, indent=2, default=str))
        else:
            print(f"\n  === Nansen Snapshot Freshness ===\n")
            for table, info in sorted(nansen_tables.items()):
                last = info['last_snapshot'][:19] if info['last_snapshot'] else 'NEVER'
                age = f"{info['age_hours']:.1f}h" if info['age_hours'] is not None else '-'
                status = 'STALE' if info['stale'] else 'OK'
                print(f"  {table:<30} {last:<22} {age:<8} {status}")
        return

    if args.snapshot_all:
        # PID file to prevent concurrent runs
        pid_file = PROJECT_ROOT / "logs" / "nansen_snapshot.pid"
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        if pid_file.exists():
            try:
                old_pid = int(pid_file.read_text().strip())
                os.kill(old_pid, 0)
                print(f"Snapshot already running (PID {old_pid}). Skipping.",
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

    parser.print_help()


if __name__ == "__main__":
    main()
