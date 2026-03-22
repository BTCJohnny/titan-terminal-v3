#!/usr/bin/env python3
"""
Titan Terminal — Backtest Results Aggregator
=============================================
Reads all Phase 4 JSON result files and produces a cross-universe report.
Zero API calls — pure Python aggregation.

Commands:
    report            Full report (stdout + saved to results/backtests/)
    graduates         Just the graduation summary table
    compare           Diff against a baseline JSON file
    export-graduates  Write graduated strategies to results/backtests/graduated/

Usage:
    python3 src/backtesting/aggregate_results.py report
    python3 src/backtesting/aggregate_results.py graduates
    python3 src/backtesting/aggregate_results.py compare --baseline results/backtests/baseline_ta_only.json
    python3 src/backtesting/aggregate_results.py export-graduates
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

RESULTS_DIR = PROJECT_ROOT / "results" / "backtests"
GRADUATED_DIR = RESULTS_DIR / "graduated"

# Graduation criteria (mirrors scanner.py)
GRAD_MIN_TRADES = 10
GRAD_MIN_WIN_RATE = 0.45
GRAD_MIN_PF = 1.8
GRAD_MAX_DD = 15.0
GRAD_MIN_AVG_R = 0.5


# ============================================================================
# DATA LOADING
# ============================================================================

def _pf_float(pf) -> float:
    """Convert profit_factor (may be 'inf' string) to float."""
    if isinstance(pf, str):
        return 999.0
    return float(pf) if pf else 0.0


def _fmt_pf(pf) -> str:
    """Format profit factor for display."""
    if isinstance(pf, str):
        return pf
    if pf is None:
        return "—"
    v = float(pf)
    if v >= 999:
        return "inf"
    return f"{v:.2f}"


def _base_name(name: str) -> str:
    """Strip [param=value] suffix to get base scenario name.

    'E1: MACD Rollover + Death Cross [target1_atr_mult=4.5]'
    → 'E1: MACD Rollover + Death Cross'
    """
    return re.sub(r"\s*\[.*\]$", "", name).strip()


def _is_graduate(survivor: dict) -> bool:
    """Apply graduation criteria to the 'full' metrics of a Phase 4 survivor."""
    if not survivor.get("walk_forward_pass"):
        return False
    full = survivor.get("full", {})
    pf = _pf_float(full.get("profit_factor", 0))
    return (
        full.get("total_trades", 0) >= GRAD_MIN_TRADES
        and full.get("win_rate", 0) >= GRAD_MIN_WIN_RATE
        and pf >= GRAD_MIN_PF
        and full.get("max_drawdown_pct", 999) <= GRAD_MAX_DD
        and full.get("avg_r_achieved", 0) >= GRAD_MIN_AVG_R
    )


def load_all_phase4() -> list[dict]:
    """Load all phase4_*.json files. Returns list of file-level dicts."""
    files = sorted(RESULTS_DIR.glob("phase4_*.json"))
    results = []
    for f in files:
        try:
            data = json.loads(f.read_text())
            data["_file"] = f.name
            results.append(data)
        except Exception as e:
            print(f"  WARN: failed to load {f.name}: {e}", file=sys.stderr)
    return results


# ============================================================================
# AGGREGATION
# ============================================================================

def aggregate(all_files: list[dict]) -> dict:
    """
    Crunch all phase4 data into aggregated structures.

    Returns a dict with:
        files_found, symbols_found, total_survivors, total_wf_passes,
        graduates (list), strategy_leaderboard (list),
        per_symbol (dict), all_scenario_names (set),
        dead_scenarios (list), zero_trade_scenarios (list)
    """
    symbols_found = set()
    total_survivors = 0
    total_wf_passes = 0
    graduates = []  # list of dicts with symbol, timeframe, name, full metrics, strategy

    # scenario_name -> {symbols, timeframes, pf_list, trade_count_list}
    scenario_stats: dict[str, dict] = defaultdict(lambda: {
        "symbols": set(), "timeframes": set(),
        "pf_list": [], "trade_list": [], "grads": []
    })

    # scenario_name -> total trades across ALL files (for zero-trade detection)
    scenario_trade_totals: dict[str, int] = defaultdict(int)

    # per_symbol[symbol][timeframe] = list of graduate summaries
    per_symbol: dict[str, dict] = defaultdict(lambda: defaultdict(list))

    for data in all_files:
        symbol = data.get("symbol", "?")
        timeframe = data.get("timeframe", "?")
        symbols_found.add(symbol)

        for survivor in data.get("survivors", []):
            total_survivors += 1
            if survivor.get("walk_forward_pass"):
                total_wf_passes += 1

            full = survivor.get("full", {})
            base = _base_name(survivor["name"])
            trades = full.get("total_trades", 0)
            scenario_trade_totals[base] += trades

            if _is_graduate(survivor):
                pf = _pf_float(full.get("profit_factor", 0))
                direction = full.get("direction") or survivor.get("direction", "?")
                strategy = full.get("strategy")

                grad = {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "name": survivor["name"],
                    "base_name": base,
                    "direction": direction,
                    "walk_forward_pass": survivor.get("walk_forward_pass"),
                    "full": full,
                    "train": survivor.get("train", {}),
                    "test": survivor.get("test", {}),
                    "strategy": strategy,
                }
                graduates.append(grad)

                scenario_stats[base]["symbols"].add(symbol)
                scenario_stats[base]["timeframes"].add(timeframe)
                scenario_stats[base]["pf_list"].append(pf)
                scenario_stats[base]["trade_list"].append(trades)
                scenario_stats[base]["grads"].append(grad)

                per_symbol[symbol][timeframe].append({
                    "name": survivor["name"],
                    "base": base,
                    "direction": direction,
                    "pf": pf,
                    "trades": trades,
                    "win_rate": full.get("win_rate", 0),
                    "max_dd": full.get("max_drawdown_pct", 0),
                    "avg_r": full.get("avg_r_achieved", 0),
                })

    # Build strategy leaderboard (sorted by # symbols graduated)
    leaderboard = []
    for base, stats in scenario_stats.items():
        avg_pf = sum(stats["pf_list"]) / len(stats["pf_list"]) if stats["pf_list"] else 0
        avg_trades = sum(stats["trade_list"]) / len(stats["trade_list"]) if stats["trade_list"] else 0
        # Cap avg_pf display at 20 if inf values inflating
        real_pf_list = [p for p in stats["pf_list"] if p < 999]
        avg_pf_display = (sum(real_pf_list) / len(real_pf_list)) if real_pf_list else avg_pf
        leaderboard.append({
            "base_name": base,
            "grad_count": len(stats["grads"]),
            "symbol_count": len(stats["symbols"]),
            "symbols": sorted(stats["symbols"]),
            "timeframes": sorted(stats["timeframes"]),
            "avg_test_pf": avg_pf_display,
            "avg_trades": avg_trades,
        })
    leaderboard.sort(key=lambda x: (-x["symbol_count"], -x["avg_test_pf"]))

    # Dead scenarios: zero graduates across ALL files
    try:
        from src.backtesting.scenarios import SCENARIOS
        all_scenario_names = {s["name"] for s in SCENARIOS}
    except Exception:
        all_scenario_names = set(scenario_trade_totals.keys())

    graduated_bases = set(scenario_stats.keys())
    dead_scenarios = sorted(all_scenario_names - graduated_bases)
    zero_trade_scenarios = sorted(
        name for name in all_scenario_names
        if scenario_trade_totals.get(name, 0) == 0
    )
    low_trade_scenarios = sorted(
        (name, scenario_trade_totals[name])
        for name in dead_scenarios
        if scenario_trade_totals.get(name, 0) > 0
    )

    return {
        "files_found": len(all_files),
        "symbols_found": sorted(symbols_found),
        "total_survivors": total_survivors,
        "total_wf_passes": total_wf_passes,
        "graduates": graduates,
        "leaderboard": leaderboard,
        "per_symbol": {k: dict(v) for k, v in per_symbol.items()},
        "all_scenario_names": all_scenario_names,
        "dead_scenarios": dead_scenarios,
        "zero_trade_scenarios": zero_trade_scenarios,
        "low_trade_dead_scenarios": low_trade_scenarios,
        "scenario_trade_totals": dict(scenario_trade_totals),
    }


# ============================================================================
# REPORT RENDERING
# ============================================================================

def render_report(agg: dict, date_str: str) -> str:
    lines = []
    files_found = agg["files_found"]
    symbols = agg["symbols_found"]
    graduates = agg["graduates"]
    leaderboard = agg["leaderboard"]
    per_symbol = agg["per_symbol"]

    unique_strategies = len(set(g["base_name"] for g in graduates))
    unique_grads_by_key = len(set((g["symbol"], g["timeframe"], g["base_name"]) for g in graduates))

    lines.append(f"FULL UNIVERSE BACKTEST REPORT — with derivatives data")
    lines.append(f"Generated: {date_str}")
    lines.append("=" * 60)

    # ── 1. Summary ──────────────────────────────────────────────
    lines.append("\n## 1. SUMMARY\n")
    timeframes = sorted(set(g["timeframe"] for g in graduates)) if graduates else ["1h", "4h"]
    lines.append(f"  Phase 4 files found  : {files_found}")
    lines.append(f"  Symbols scanned      : {len(symbols)}")
    lines.append(f"  Total survivors      : {agg['total_survivors']}")
    lines.append(f"  Walk-forward passes  : {agg['total_wf_passes']}")
    lines.append(f"  Total graduates      : {len(graduates)}")
    lines.append(f"  Unique strategies    : {unique_strategies}")
    lines.append(f"  Unique sym×strat     : {unique_grads_by_key}")

    # ── 2. Strategy Leaderboard ──────────────────────────────────
    lines.append("\n## 2. STRATEGY LEADERBOARD (by cross-symbol consistency)\n")
    lines.append(f"  {'#':<3}  {'Strategy':<48}  {'Syms':>4}  {'Grads':>5}  {'AvgPF':>6}  Symbols")
    lines.append(f"  {'-'*3}  {'-'*48}  {'-'*4}  {'-'*5}  {'-'*6}  {'-'*30}")
    for i, row in enumerate(leaderboard, 1):
        sym_list = ",".join(row["symbols"])
        if len(sym_list) > 35:
            sym_list = sym_list[:32] + "..."
        avg_pf_str = f"{row['avg_test_pf']:.2f}" if row["avg_test_pf"] < 900 else "inf"
        lines.append(
            f"  {i:<3}  {row['base_name']:<48}  {row['symbol_count']:>4}  "
            f"{row['grad_count']:>5}  {avg_pf_str:>6}  {sym_list}"
        )

    # ── 3. Per-Symbol Summary ────────────────────────────────────
    lines.append("\n## 3. PER-SYMBOL SUMMARY\n")
    for symbol in sorted(per_symbol.keys()):
        for tf in sorted(per_symbol[symbol].keys()):
            grads = per_symbol[symbol][tf]
            if not grads:
                continue
            parts = []
            for g in grads:
                pf_str = f"{g['pf']:.2f}" if g["pf"] < 900 else "inf"
                dir_tag = f" ({g['direction']})" if g["direction"] != "LONG" else ""
                parts.append(f"{g['base']}{dir_tag} PF:{pf_str}")
            lines.append(f"  {symbol} ({tf}): {len(grads)} graduate{'s' if len(grads)!=1 else ''}")
            for g in grads:
                pf_str = f"{g['pf']:.2f}" if g["pf"] < 900 else "inf"
                dir_tag = f"({g['direction']}) " if g["direction"] != "LONG" else ""
                lines.append(
                    f"    {dir_tag}{g['name']}  "
                    f"PF:{pf_str}  WR:{g['win_rate']:.1%}  "
                    f"Trades:{g['trades']}  DD:{g['max_dd']:.1f}%  AvgR:{g['avg_r']:.2f}"
                )
        # symbols with zero graduates
        if symbol not in {g["symbol"] for g in graduates}:
            lines.append(f"  {symbol}: 0 graduates")

    # Symbols with no graduates at all
    symbols_with_grads = set(g["symbol"] for g in graduates)
    no_grad_symbols = sorted(set(symbols) - symbols_with_grads)
    if no_grad_symbols:
        lines.append(f"\n  Symbols with 0 graduates: {', '.join(no_grad_symbols)}")

    # ── 4. Dead Scenario Report ──────────────────────────────────
    lines.append("\n## 4. DEAD SCENARIOS (0 graduates)\n")
    dead = agg["dead_scenarios"]
    zero_trade = set(agg["zero_trade_scenarios"])
    low_trade = dict(agg["low_trade_dead_scenarios"])

    if not dead:
        lines.append("  None — every scenario graduated on at least one symbol.")
    else:
        lines.append(f"  {len(dead)} scenarios produced 0 graduates:\n")
        for name in dead:
            trades = agg["scenario_trade_totals"].get(name, 0)
            if trades == 0:
                tag = "  [ZERO TRADES — signal never fires]"
            else:
                tag = f"  [{trades} trades total, none meeting graduation criteria]"
            lines.append(f"    {name}{tag}")

    # ── 5. Derivatives Impact Summary ───────────────────────────
    lines.append("\n## 5. DERIVATIVES IMPACT SUMMARY\n")
    deriv_scenarios = {
        "A1: Crowded Long Fade", "A2: Crowded Short Squeeze", "A3: Long Liq Cascade Bounce",
        "A4: Fear & Greed Extreme Fear Buy",
        "B1: ETF Inflow Momentum", "B2: OI Breakout Long", "B3: OI Breakout Short",
        "C1: OI Accumulation", "C2: OI Distribution", "C3: Smart Money Divergence",
        "G4: Derivatives Distribution Short", "G5: Derivatives Squeeze Long",
        "G9: Short Squeeze Exhaustion Fade", "G10: Smart Money Accumulation Dip",
        "H1: Greed Top Short (Sentiment + RSI)", "H2: Greed Distribution Short",
        "H3: Double Contrarian Short (Greed + Crowd)", "H4: Fear Accumulation Long",
        "H5: Double Contrarian Long (Fear + Crowd)", "H6: Greed Standalone Short",
        "I1: Full Institutional Bull", "I2: ETF Dip Buy",
        "I3: Coinbase Momentum Long", "I4: Coinbase Accumulation",
    }

    graduated_deriv = [name for name in set(g["base_name"] for g in graduates) if name in deriv_scenarios]
    dead_deriv = [name for name in agg["dead_scenarios"] if name in deriv_scenarios]
    alive_never_grad = [
        (name, agg["scenario_trade_totals"].get(name, 0))
        for name in deriv_scenarios
        if name not in agg["dead_scenarios"] and name not in (g["base_name"] for g in graduates)
    ]

    lines.append(f"  Derivatives scenarios that GRADUATED: {len(graduated_deriv)}")
    for name in sorted(graduated_deriv):
        count = sum(1 for g in graduates if g["base_name"] == name)
        lines.append(f"    ✓ {name} ({count} symbol-timeframe combos)")

    lines.append(f"\n  Derivatives scenarios with trades but NO graduation: {len(alive_never_grad)}")
    for name, trades in sorted(alive_never_grad):
        lines.append(f"    ~ {name} ({trades} trades, criteria not met)")

    lines.append(f"\n  Derivatives scenarios still DEAD (0 trades): {len([n for n in dead_deriv if n in zero_trade])}")
    for name in sorted(dead_deriv):
        trades = agg["scenario_trade_totals"].get(name, 0)
        tag = "0 trades" if trades == 0 else f"{trades} trades, not graduating"
        lines.append(f"    ✗ {name} ({tag})")

    return "\n".join(lines)


def render_graduates_table(graduates: list[dict]) -> str:
    """Short graduation summary table."""
    lines = ["GRADUATION SUMMARY", "=" * 60, ""]
    by_sym: dict[str, list] = defaultdict(list)
    for g in graduates:
        key = f"{g['symbol']} ({g['timeframe']})"
        by_sym[key].append(g)

    for key in sorted(by_sym.keys()):
        grads = by_sym[key]
        lines.append(f"{key}: {len(grads)} graduate{'s' if len(grads)!=1 else ''}")
        for g in grads:
            full = g["full"]
            pf = _pf_float(full.get("profit_factor", 0))
            pf_str = f"{pf:.2f}" if pf < 900 else "inf"
            lines.append(
                f"  {g['name']}"
                f"  PF:{pf_str}"
                f"  WR:{full.get('win_rate',0):.1%}"
                f"  T:{full.get('total_trades',0)}"
                f"  DD:{full.get('max_drawdown_pct',0):.1f}%"
            )
    lines.append("")
    lines.append(f"Total: {len(graduates)} graduates across {len(by_sym)} symbol/timeframe combinations")
    return "\n".join(lines)


# ============================================================================
# COMPARE COMMAND
# ============================================================================

def render_compare(agg: dict, baseline_path: str) -> str:
    """Diff current graduates against a baseline JSON."""
    try:
        baseline = json.loads(Path(baseline_path).read_text())
    except Exception as e:
        return f"ERROR: Could not load baseline: {e}"

    lines = [f"COMPARISON vs BASELINE: {baseline_path}", "=" * 60, ""]

    # Baseline may be a phase4 file or a simple dict with 'graduates' key
    if "graduates" in baseline:
        base_grads = set(
            f"{g['symbol']}|{g['timeframe']}|{g.get('base_name', _base_name(g['name']))}"
            for g in baseline["graduates"]
        )
        base_wf = baseline.get("total_wf_passes", "?")
        base_total = len(baseline["graduates"])
    elif "survivors" in baseline:
        # Single phase4 file used as baseline
        base_grads = set()
        for s in baseline["survivors"]:
            if _is_graduate(s):
                sym = baseline.get("symbol", "?")
                tf = baseline.get("timeframe", "?")
                base_grads.add(f"{sym}|{tf}|{_base_name(s['name'])}")
        base_wf = sum(1 for s in baseline["survivors"] if s.get("walk_forward_pass"))
        base_total = len(base_grads)
    else:
        return "ERROR: Baseline format not recognised (expected 'graduates' or 'survivors' key)"

    current_grads = set(
        f"{g['symbol']}|{g['timeframe']}|{g['base_name']}"
        for g in agg["graduates"]
    )
    new_grads = current_grads - base_grads
    lost_grads = base_grads - current_grads

    lines.append(f"  Baseline graduates : {base_total}")
    lines.append(f"  Current graduates  : {len(agg['graduates'])}")
    lines.append(f"  Net change         : {len(agg['graduates']) - base_total:+d}")
    lines.append(f"  Baseline WF passes : {base_wf}")
    lines.append(f"  Current WF passes  : {agg['total_wf_passes']}")
    lines.append("")

    if new_grads:
        lines.append(f"NEW graduates (not in baseline): {len(new_grads)}")
        for key in sorted(new_grads):
            lines.append(f"  + {key.replace('|', ' ')}")
    else:
        lines.append("No new graduates vs baseline.")

    lines.append("")
    if lost_grads:
        lines.append(f"LOST graduates (were in baseline): {len(lost_grads)}")
        for key in sorted(lost_grads):
            lines.append(f"  - {key.replace('|', ' ')}")
    else:
        lines.append("No lost graduates vs baseline.")

    return "\n".join(lines)


# ============================================================================
# EXPORT GRADUATES
# ============================================================================

def export_graduates(graduates: list[dict], date_str: str) -> int:
    """Write each graduate as a standalone JSON to results/backtests/graduated/."""
    GRADUATED_DIR.mkdir(parents=True, exist_ok=True)
    written = 0

    for g in graduates:
        symbol = g["symbol"]
        base = g["base_name"]
        full = g["full"]
        direction = g.get("direction") or full.get("direction", "?")
        strategy = g.get("strategy") or {}

        # Safe filename: strip colons, spaces → underscores
        safe_base = re.sub(r"[:\s/\\]+", "_", base).strip("_")
        filename = f"graduated_{symbol}_{g['timeframe']}_{safe_base}_{date_str}.json"

        payload = {
            "name": g["name"],
            "base_name": base,
            "symbol": symbol,
            "timeframe": g["timeframe"],
            "direction": direction,
            "entry_signals": strategy.get("entry_signals", []),
            "entry_params": strategy.get("entry_params", {}),
            "exit": strategy.get("exit", {}),
            "filters": strategy.get("filters", {}),
            "backtest_metrics": {
                "total_trades": full.get("total_trades", 0),
                "win_rate": full.get("win_rate", 0),
                "profit_factor": full.get("profit_factor", 0),
                "max_drawdown_pct": full.get("max_drawdown_pct", 0),
                "avg_r_achieved": full.get("avg_r_achieved", 0),
                "walk_forward": "PASS" if g.get("walk_forward_pass") else "FAIL",
            },
            "walk_forward": {
                "train": g.get("train", {}),
                "test": g.get("test", {}),
            },
        }

        out_path = GRADUATED_DIR / filename
        out_path.write_text(json.dumps(payload, indent=2, default=str))
        written += 1

    return written


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Backtest results aggregator")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("report", help="Full report (stdout + saved)")
    sub.add_parser("graduates", help="Graduation summary table")

    p_compare = sub.add_parser("compare", help="Compare against baseline")
    p_compare.add_argument("--baseline", required=True, help="Path to baseline JSON file")

    sub.add_parser("export-graduates", help="Write graduated strategies to results/backtests/graduated/")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    date_str = datetime.now().strftime("%Y%m%d")
    all_files = load_all_phase4()

    if not all_files:
        print(f"ERROR: No phase4_*.json files found in {RESULTS_DIR}", file=sys.stderr)
        sys.exit(1)

    agg = aggregate(all_files)

    if args.command == "report":
        report = render_report(agg, date_str)
        print(report)
        out_path = RESULTS_DIR / f"universe_report_{date_str}.md"
        out_path.write_text(report)
        print(f"\n── Saved to {out_path.relative_to(PROJECT_ROOT)}")

    elif args.command == "graduates":
        print(render_graduates_table(agg["graduates"]))

    elif args.command == "compare":
        print(render_compare(agg, args.baseline))

    elif args.command == "export-graduates":
        n = export_graduates(agg["graduates"], date_str)
        print(f"Exported {n} graduated strategies to {GRADUATED_DIR.relative_to(PROJECT_ROOT)}/")


if __name__ == "__main__":
    main()
