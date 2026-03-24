#!/usr/bin/env python3
"""
Derivatives Distribution Analysis
===================================
Analyze actual distributions of derivatives data from Coinglass backfill
to calibrate signal thresholds for backtesting.

Usage:
    python3 src/backtesting/analyze_derivatives.py distributions              # All symbols
    python3 src/backtesting/analyze_derivatives.py distributions --symbol BTC # Single symbol
    python3 src/backtesting/analyze_derivatives.py coverage                   # Field coverage by symbol
"""

import argparse
import json
import sqlite3
import statistics
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

INTEL_DB = PROJECT_ROOT / "data" / "titan_intelligence.db"
RESULTS_DIR = PROJECT_ROOT / "results" / "backtests"

FIELDS = [
    "funding_rate_avg",
    "oi_change_24h_pct",
    "ls_global_ratio",
    "ls_top_account_ratio",
    "ls_top_position_ratio",
    "liq_24h_usd",
    "liq_long_24h_usd",
    "liq_short_24h_usd",
    "fear_greed_value",
    "coinbase_premium_rate",
    "etf_weekly_net_flow_usd",
    "etf_streak_days",
]


def get_percentile(sorted_vals, p):
    """Get percentile value from sorted list."""
    n = len(sorted_vals)
    if n == 0:
        return None
    idx = int(n * p / 100)
    return sorted_vals[min(idx, n - 1)]


def compute_field_stats(values):
    """Compute distribution stats for a list of numeric values."""
    if not values:
        return None
    vals = sorted(values)
    return {
        "count": len(vals),
        "min": round(min(vals), 6),
        "max": round(max(vals), 6),
        "mean": round(statistics.mean(vals), 6),
        "p5": round(get_percentile(vals, 5), 6),
        "p10": round(get_percentile(vals, 10), 6),
        "p25": round(get_percentile(vals, 25), 6),
        "p50": round(get_percentile(vals, 50), 6),
        "p75": round(get_percentile(vals, 75), 6),
        "p90": round(get_percentile(vals, 90), 6),
        "p95": round(get_percentile(vals, 95), 6),
        "p99": round(get_percentile(vals, 99), 6),
    }


def cmd_distributions(args):
    """Compute and display distributions for all derivatives fields."""
    if not INTEL_DB.exists():
        print(f"No database at {INTEL_DB}")
        return

    conn = sqlite3.connect(INTEL_DB)
    conn.row_factory = sqlite3.Row

    where = 'source = "backfill"'
    params = []
    if args.symbol:
        where += " AND symbol = ?"
        params.append(args.symbol.upper())

    rows = conn.execute(
        f"SELECT * FROM derivatives_snapshots WHERE {where}", params
    ).fetchall()

    total = len(rows)
    symbols = set(r["symbol"] for r in rows)
    label = args.symbol.upper() if args.symbol else f"ALL ({len(symbols)} symbols)"
    print(f"Derivatives Distributions — {label}")
    print(f"Total rows: {total}")
    print("=" * 70)

    results = {"_meta": {"total_rows": total, "symbols": len(symbols)}}

    for field in FIELDS:
        vals = [r[field] for r in rows if r[field] is not None]
        if not vals:
            print(f"\n{field}: NO DATA (0/{total})")
            results[field] = {"count": 0, "coverage_pct": 0}
            continue

        stats = compute_field_stats(vals)
        stats["total_rows"] = total
        stats["coverage_pct"] = round(100 * len(vals) / total, 1)
        results[field] = stats

        # Format numbers based on magnitude
        def fmt(v):
            if abs(v) >= 1_000_000:
                return f"${v:,.0f}"
            elif abs(v) >= 1:
                return f"{v:.2f}"
            else:
                return f"{v:.6f}"

        print(f"\n{field}")
        print(f"  Count: {stats['count']}/{total} ({stats['coverage_pct']}%)")
        print(f"  Min: {fmt(stats['min'])}   Max: {fmt(stats['max'])}   Mean: {fmt(stats['mean'])}")
        print(f"  P5={fmt(stats['p5'])}  P10={fmt(stats['p10'])}  P25={fmt(stats['p25'])}  P50={fmt(stats['p50'])}")
        print(f"  P75={fmt(stats['p75'])}  P90={fmt(stats['p90'])}  P95={fmt(stats['p95'])}  P99={fmt(stats['p99'])}")

    # Per-symbol breakdown for key fields
    if not args.symbol:
        print("\n" + "=" * 70)
        print("PER-SYMBOL BREAKDOWN (key fields)")
        print("=" * 70)

        key_fields = ["funding_rate_avg", "ls_global_ratio", "liq_24h_usd"]
        syms = sorted(symbols)[:10]  # Top 10

        for field in key_fields:
            print(f"\n{field}:")
            per_sym = {}
            for sym in syms:
                vals = [r[field] for r in rows if r["symbol"] == sym and r[field] is not None]
                if not vals:
                    continue
                s = compute_field_stats(vals)
                per_sym[sym] = s

                def fmt(v):
                    if abs(v) >= 1_000_000:
                        return f"${v:,.0f}"
                    elif abs(v) >= 1:
                        return f"{v:.4f}"
                    else:
                        return f"{v:.6f}"

                print(f"  {sym:6s} n={s['count']:3d}  P10={fmt(s['p10'])}  P50={fmt(s['p50'])}  P90={fmt(s['p90'])}  max={fmt(s['max'])}")

            results[f"{field}_by_symbol"] = per_sym

    conn.close()

    # Save JSON
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / "derivatives_distributions.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved to {out_path}")


def cmd_coverage(args):
    """Show which symbols have data for which fields."""
    if not INTEL_DB.exists():
        print(f"No database at {INTEL_DB}")
        return

    conn = sqlite3.connect(INTEL_DB)

    # Get all symbols with backfill data
    syms = [r[0] for r in conn.execute(
        'SELECT DISTINCT symbol FROM derivatives_snapshots WHERE source = "backfill" ORDER BY symbol'
    ).fetchall()]

    print(f"Coverage Matrix — {len(syms)} symbols, {len(FIELDS)} fields")
    print(f"{'Symbol':<8}", end="")
    short_names = {
        "funding_rate_avg": "fund",
        "oi_change_24h_pct": "oi_chg",
        "ls_global_ratio": "ls_gl",
        "ls_top_account_ratio": "ls_ta",
        "ls_top_position_ratio": "ls_tp",
        "liq_24h_usd": "liq",
        "liq_long_24h_usd": "liq_l",
        "liq_short_24h_usd": "liq_s",
        "fear_greed_value": "f&g",
        "coinbase_premium_rate": "cb_pr",
        "etf_weekly_net_flow_usd": "etf",
        "etf_streak_days": "etf_s",
    }
    for f in FIELDS:
        print(f"{short_names.get(f, f[:6]):>7}", end="")
    print(f"{'total':>7}")
    print("-" * (8 + 7 * (len(FIELDS) + 1)))

    for sym in syms:
        print(f"{sym:<8}", end="")
        total_days = conn.execute(
            'SELECT COUNT(*) FROM derivatives_snapshots WHERE source = "backfill" AND symbol = ?',
            (sym,)
        ).fetchone()[0]
        for field in FIELDS:
            count = conn.execute(
                f'SELECT COUNT(*) FROM derivatives_snapshots WHERE source = "backfill" AND symbol = ? AND {field} IS NOT NULL',
                (sym,)
            ).fetchone()[0]
            pct = round(100 * count / total_days) if total_days > 0 else 0
            marker = f"{pct:>6}%" if pct > 0 else "     -"
            print(marker, end="")
        print(f"{total_days:>7}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Derivatives Distribution Analysis")
    sub = parser.add_subparsers(dest="command")

    dist = sub.add_parser("distributions", help="Compute field distributions")
    dist.add_argument("--symbol", type=str, help="Single symbol (default: all)")

    sub.add_parser("coverage", help="Show field coverage by symbol")

    args = parser.parse_args()
    if args.command == "distributions":
        cmd_distributions(args)
    elif args.command == "coverage":
        cmd_coverage(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
