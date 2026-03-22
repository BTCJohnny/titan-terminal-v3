#!/usr/bin/env python3
"""
Titan Terminal v2 — Strategy Scanner
======================================
4-phase automated strategy discovery pipeline.

Phase 1: Individual signal scan (each signal alone)
Phase 2: Scenario scan (12 predefined + bidirectional variants)
Phase 3: Parameter sweep (top N from Phase 2)
Phase 4: Walk-forward validation (train/test split)

Usage:
    python3 src/backtesting/scanner.py phase1 --symbol BTC --timeframe 4h --days 180
    python3 src/backtesting/scanner.py phase2 --symbol BTC --timeframe 4h --days 180
    python3 src/backtesting/scanner.py phase3 --symbol BTC --timeframe 4h --days 180 --top 5
    python3 src/backtesting/scanner.py phase4 --symbol BTC --timeframe 4h --days 180 --top 5
    python3 src/backtesting/scanner.py full --symbol BTC --timeframe 4h --days 180
"""

import argparse
import json
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.backtesting.engine import run_backtest
from src.backtesting.signals import SIGNAL_REGISTRY
from src.backtesting.scenarios import (
    SCENARIOS, get_all_scenarios, generate_sweep_variants, _deep_copy_strategy
)

RESULTS_DIR = PROJECT_ROOT / "results" / "backtests"


# ============================================================================
# SIGNAL DIRECTION MAP
# ============================================================================

SIGNAL_DIRECTION = {
    "rsi_overbought": "SHORT", "rsi_oversold": "LONG",
    "macd_bullish_cross": "LONG", "macd_bearish_cross": "SHORT",
    "bb_touch_upper": "SHORT", "bb_touch_lower": "LONG",
    "bb_squeeze": "LONG",
    "obv_divergence_bearish": "SHORT", "obv_divergence_bullish": "LONG",
    "adx_strong_trend": "LONG", "adx_weak_trend": "LONG",
    "trend_bullish": "LONG", "trend_bearish": "SHORT",
    "volume_surge": "LONG",
    "funding_extreme_positive": "SHORT", "funding_extreme_negative": "LONG",
    "ls_crowd_long": "SHORT", "ls_crowd_short": "LONG",
    "liq_cascade_long": "LONG", "liq_cascade_short": "SHORT",
    "fear_greed_extreme_fear": "LONG", "fear_greed_extreme_greed": "SHORT",
    "oi_surge": "LONG",
    "oi_price_divergence_bullish": "LONG", "oi_price_divergence_bearish": "SHORT",
    "top_trader_divergence": "LONG",
    "etf_inflow_streak": "LONG", "coinbase_premium_positive": "LONG",
}

# Default exit params for Phase 1 single-signal tests
DEFAULT_EXIT = {
    "stop_atr_mult": 2.0,
    "target1_atr_mult": 3.0,
    "target2_atr_mult": 6.0,
    "scale_out_pct": 0.5,
    "max_bars": 60,
}

# Graduation criteria
GRAD_MIN_TRADES = 10
GRAD_MIN_WIN_RATE = 0.45
GRAD_MIN_PF = 1.8
GRAD_MAX_DD = 15.0
GRAD_MIN_AVG_R = 0.5


# ============================================================================
# RESULTS HELPERS
# ============================================================================

def _ensure_results_dir():
    """Create results/backtests/ if needed."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def _save_json(data: dict, filename: str):
    """Save JSON results to results/backtests/."""
    _ensure_results_dir()
    path = RESULTS_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    return path


def _extract_summary(result: dict) -> dict:
    """Extract key metrics from a backtest result (drop full trade list for leaderboard)."""
    if "error" in result:
        return {"name": result.get("strategy_name", "?"), "error": result["error"]}
    return {
        "name": result.get("strategy_name", "?"),
        "direction": result.get("direction", "?"),
        "total_trades": result.get("total_trades", 0),
        "win_rate": result.get("win_rate", 0),
        "profit_factor": result.get("profit_factor", 0),
        "expectancy_usd": result.get("expectancy_usd", 0),
        "total_pnl_usd": result.get("total_pnl_usd", 0),
        "max_drawdown_pct": result.get("max_drawdown_pct", 0),
        "avg_r_achieved": result.get("avg_r_achieved", 0),
    }


def _format_pf(pf):
    """Format profit factor for display."""
    if isinstance(pf, str):
        return pf  # "inf"
    return f"{pf:.2f}"


# ============================================================================
# LEADERBOARD DISPLAY
# ============================================================================

def _print_leaderboard(title: str, results: list, symbol: str, timeframe: str, days: int):
    """Print a sorted leaderboard table."""
    # Filter out errors and zero-trade results, sort by expectancy
    valid = [r for r in results if "error" not in r and r.get("total_trades", 0) > 0]
    valid.sort(key=lambda r: r.get("expectancy_usd", 0), reverse=True)

    zero_trade = [r for r in results if "error" not in r and r.get("total_trades", 0) == 0]
    errors = [r for r in results if "error" in r]

    print()
    print("=" * 90)
    print(f"  {title} — {symbol} {timeframe} ({days} days)")
    print("=" * 90)
    print(f"  {'#':>3s}  {'Strategy':<40s} {'Dir':5s} {'Trades':>6s} {'WR':>6s} {'PF':>6s} {'Exp/T':>8s} {'DD':>6s}")
    print(f"  {'─'*3}  {'─'*40} {'─'*5} {'─'*6} {'─'*6} {'─'*6} {'─'*8} {'─'*6}")

    for i, r in enumerate(valid):
        name = r["name"][:40]
        wr = f"{r['win_rate']*100:.1f}%" if r["win_rate"] else "0.0%"
        pf = _format_pf(r["profit_factor"])
        exp = f"${r['expectancy_usd']:+,.0f}"
        dd = f"{r['max_drawdown_pct']:.1f}%"
        trades = str(r["total_trades"])
        direction = r.get("direction", "?")
        print(f"  {i+1:3d}  {name:<40s} {direction:5s} {trades:>6s} {wr:>6s} {pf:>6s} {exp:>8s} {dd:>6s}")

    # Summary line
    above_1 = sum(1 for r in valid if _pf_value(r.get("profit_factor", 0)) > 1.0)
    above_15 = sum(1 for r in valid if _pf_value(r.get("profit_factor", 0)) > 1.5)
    total_tested = len(results)
    print(f"  {'─'*3}  {'─'*40} {'─'*5} {'─'*6} {'─'*6} {'─'*6} {'─'*8} {'─'*6}")
    print(f"       Profitable (PF > 1.0): {above_1}/{total_tested} | Strong (PF > 1.5): {above_15}/{total_tested}")

    if zero_trade:
        print(f"       No trades triggered: {len(zero_trade)}")
    if errors:
        print(f"       Errors: {len(errors)}")

    if valid:
        best = valid[0]
        print(f"       Top: {best['name']} (PF {_format_pf(best['profit_factor'])}, {best['total_trades']} trades)")

    print("=" * 90)
    print()


def _pf_value(pf) -> float:
    """Convert profit factor to float for comparison."""
    if isinstance(pf, str):
        return float("inf") if pf == "inf" else 0
    return float(pf)


# ============================================================================
# PHASE 1: Individual Signal Scan
# ============================================================================

def run_phase1(symbol: str, timeframe: str, days: int) -> list:
    """Test each signal alone as a standalone entry trigger."""
    print(f"\n  Phase 1: Individual Signal Scan — {symbol} {timeframe} ({days} days)")
    print(f"  Testing {len(SIGNAL_REGISTRY)} signals individually...\n")

    results = []
    total = len(SIGNAL_REGISTRY)
    start = time.time()

    for idx, sig_name in enumerate(SIGNAL_REGISTRY.keys(), 1):
        direction = SIGNAL_DIRECTION.get(sig_name, "LONG")
        strategy = {
            "name": sig_name,
            "direction": direction,
            "entry_signals": [sig_name],
            "entry_params": {},
            "exit": dict(DEFAULT_EXIT),
            "filters": {},
        }

        print(f"  Testing {idx}/{total}: {sig_name} ({direction})...", end="", flush=True)
        result = run_backtest(strategy, symbol, timeframe, days)
        summary = _extract_summary(result)
        results.append(summary)
        trades = summary.get("total_trades", 0)
        pf = _format_pf(summary.get("profit_factor", 0))
        print(f" {trades} trades, PF {pf}")

    elapsed = time.time() - start
    print(f"\n  Phase 1 complete in {elapsed:.1f}s")

    # Save results
    filename = f"phase1_{symbol}_{timeframe}.json"
    _save_json({"phase": 1, "symbol": symbol, "timeframe": timeframe, "days": days, "results": results}, filename)
    print(f"  Saved: results/backtests/{filename}")

    _print_leaderboard("PHASE 1: Individual Signal Scan", results, symbol, timeframe, days)
    return results


# ============================================================================
# PHASE 2: Scenario Scan
# ============================================================================

def run_phase2(symbol: str, timeframe: str, days: int) -> list:
    """Test all predefined scenarios."""
    scenarios = get_all_scenarios()
    print(f"\n  Phase 2: Scenario Scan — {symbol} {timeframe} ({days} days)")
    print(f"  Testing {len(scenarios)} scenarios...\n")

    results = []
    total = len(scenarios)
    start = time.time()

    for idx, scenario in enumerate(scenarios, 1):
        print(f"  Testing {idx}/{total}: {scenario['name']}...", end="", flush=True)
        result = run_backtest(scenario, symbol, timeframe, days)
        summary = _extract_summary(result)
        results.append(summary)
        trades = summary.get("total_trades", 0)
        pf = _format_pf(summary.get("profit_factor", 0))
        print(f" {trades} trades, PF {pf}")

    elapsed = time.time() - start
    print(f"\n  Phase 2 complete in {elapsed:.1f}s")

    filename = f"phase2_{symbol}_{timeframe}.json"
    _save_json({"phase": 2, "symbol": symbol, "timeframe": timeframe, "days": days, "results": results}, filename)
    print(f"  Saved: results/backtests/{filename}")

    _print_leaderboard("PHASE 2: Scenario Scan", results, symbol, timeframe, days)
    return results


# ============================================================================
# PHASE 3: Parameter Sweep
# ============================================================================

def run_phase3(symbol: str, timeframe: str, days: int, top_n: int = 5, phase2_results: list = None) -> list:
    """Sweep parameters on top N scenarios from Phase 2."""
    # Load Phase 2 results if not passed
    if phase2_results is None:
        p2_path = RESULTS_DIR / f"phase2_{symbol}_{timeframe}.json"
        if not p2_path.exists():
            print(f"  Phase 2 results not found. Run phase2 first.")
            return []
        with open(p2_path) as f:
            phase2_results = json.load(f).get("results", [])

    # Filter: must have trades and positive expectancy
    candidates = [
        r for r in phase2_results
        if "error" not in r and r.get("total_trades", 0) >= 5
    ]
    candidates.sort(key=lambda r: r.get("expectancy_usd", 0), reverse=True)
    top_candidates = candidates[:top_n]

    if not top_candidates:
        print(f"  No qualifying scenarios from Phase 2 (need 5+ trades).")
        return []

    print(f"\n  Phase 3: Parameter Sweep — {symbol} {timeframe} ({days} days)")
    print(f"  Sweeping top {len(top_candidates)} scenarios from Phase 2...\n")

    all_results = []
    start = time.time()

    for candidate in top_candidates:
        cand_name = candidate["name"]
        # Find the original scenario definition
        scenario = _find_scenario_by_name(cand_name)
        if not scenario:
            print(f"  Skipping {cand_name} — scenario definition not found")
            continue

        variants = generate_sweep_variants(scenario)
        print(f"\n  Sweeping: {cand_name} ({len(variants)} variants)")

        variant_results = []
        for idx, variant in enumerate(variants, 1):
            print(f"    {idx}/{len(variants)}: {variant['name'][:60]}...", end="", flush=True)
            result = run_backtest(variant, symbol, timeframe, days)
            summary = _extract_summary(result)
            # Store full strategy for Phase 4
            summary["strategy"] = variant
            variant_results.append(summary)
            trades = summary.get("total_trades", 0)
            pf = _format_pf(summary.get("profit_factor", 0))
            print(f" {trades} trades, PF {pf}")

        all_results.extend(variant_results)

        # Print mini-leaderboard for this scenario's variants
        _print_leaderboard(f"SWEEP: {cand_name}", variant_results, symbol, timeframe, days)

    elapsed = time.time() - start
    print(f"\n  Phase 3 complete in {elapsed:.1f}s")

    # Save — strip strategy dicts from JSON (too verbose), keep names
    save_results = []
    for r in all_results:
        sr = {k: v for k, v in r.items() if k != "strategy"}
        save_results.append(sr)

    filename = f"phase3_{symbol}_{timeframe}.json"
    _save_json({
        "phase": 3, "symbol": symbol, "timeframe": timeframe, "days": days,
        "top_n": top_n, "results": save_results
    }, filename)
    print(f"  Saved: results/backtests/{filename}")

    _print_leaderboard("PHASE 3: Parameter Sweep (All Variants)", all_results, symbol, timeframe, days)
    return all_results


def _get_base_scenario_name(name: str) -> str:
    """Extract the base scenario name from a variant name.

    Examples:
        "E1: MACD Rollover + Death Cross" -> "E1: MACD Rollover + Death Cross"
        "E1: MACD Rollover + Death Cross [stop_atr_mult=2.5]" -> "E1: MACD Rollover + Death Cross"
        "G12: MACD Bullish + ADX Strong (SHORT)" -> "G12: MACD Bullish + ADX Strong (SHORT)"
        "G12: MACD Bullish + ADX Strong (SHORT) [adx_strong=31.25]" -> "G12: MACD Bullish + ADX Strong (SHORT)"
    """
    bracket_idx = name.find(" [")
    if bracket_idx >= 0:
        return name[:bracket_idx]
    return name


def _find_scenario_by_name(name: str) -> dict | None:
    """Find a scenario by its exact name."""
    for s in get_all_scenarios():
        if s["name"] == name:
            return s
    # Try fuzzy match (name might have been truncated)
    for s in get_all_scenarios():
        if name.startswith(s["name"][:20]):
            return s
    return None


# ============================================================================
# PHASE 4: Walk-Forward Validation
# ============================================================================

def run_phase4(symbol: str, timeframe: str, days: int, top_n: int = 5, phase3_results: list = None) -> list:
    """Walk-forward validation: train on first 2/3, test on last 1/3."""
    # Load Phase 3 results if not passed
    if phase3_results is None:
        p3_path = RESULTS_DIR / f"phase3_{symbol}_{timeframe}.json"
        if not p3_path.exists():
            print(f"  Phase 3 results not found. Run phase3 first.")
            return []
        with open(p3_path) as f:
            phase3_results = json.load(f).get("results", [])

    # Select best variant per scenario, then take top N scenarios
    candidates = [
        r for r in phase3_results
        if "error" not in r and r.get("total_trades", 0) >= 5
    ]

    # Group by base scenario name (strip parameter variant suffixes)
    by_scenario = defaultdict(list)
    for r in candidates:
        base_name = _get_base_scenario_name(r["name"])
        by_scenario[base_name].append(r)

    # Pick the best variant per scenario (by expectancy)
    best_per_scenario = []
    for base_name, variants in by_scenario.items():
        variants.sort(key=lambda r: r.get("expectancy_usd", 0), reverse=True)
        best_per_scenario.append(variants[0])

    # Sort deduplicated list and take top N
    best_per_scenario.sort(key=lambda r: r.get("expectancy_usd", 0), reverse=True)
    top_candidates = best_per_scenario[:top_n]

    if not top_candidates:
        print(f"  No qualifying strategies from Phase 3.")
        return []

    print(f"  Selected {len(top_candidates)} candidates (best per scenario):")
    for c in top_candidates:
        base = _get_base_scenario_name(c["name"])
        print(f"    {base} → {c['name'][:60]} (exp=${c.get('expectancy_usd', 0):+,.0f})")
    print()

    train_days = int(days * 2 / 3)
    test_days = days - train_days

    print(f"\n  Phase 4: Walk-Forward Validation — {symbol} {timeframe}")
    print(f"  Train: {train_days} days | Test: {test_days} days")
    print(f"  Validating top {len(top_candidates)} strategies...\n")

    survivors = []
    start = time.time()

    for idx, candidate in enumerate(top_candidates, 1):
        cand_name = candidate["name"]
        # Reconstruct or find strategy
        strategy = candidate.get("strategy")
        if not strategy:
            strategy = _find_scenario_by_name(cand_name)
        if not strategy:
            # Build a minimal strategy from the name if it was a single signal
            if cand_name in SIGNAL_REGISTRY:
                direction = SIGNAL_DIRECTION.get(cand_name, "LONG")
                strategy = {
                    "name": cand_name,
                    "direction": direction,
                    "entry_signals": [cand_name],
                    "entry_params": {},
                    "exit": dict(DEFAULT_EXIT),
                    "filters": {},
                }
            else:
                print(f"  {idx}. {cand_name} — SKIP (strategy not found)")
                continue

        print(f"  {idx}. {cand_name}")

        # Train period
        print(f"     Train ({train_days}d)...", end="", flush=True)
        train_result = run_backtest(strategy, symbol, timeframe, train_days)
        train_sum = _extract_summary(train_result)
        train_pf = _format_pf(train_sum.get("profit_factor", 0))
        train_trades = train_sum.get("total_trades", 0)
        print(f" {train_trades} trades, PF {train_pf}")

        # Test period — use most recent test_days
        print(f"     Test  ({test_days}d)...", end="", flush=True)
        test_result = run_backtest(strategy, symbol, timeframe, test_days)
        test_sum = _extract_summary(test_result)
        test_pf = _format_pf(test_sum.get("profit_factor", 0))
        test_trades = test_sum.get("total_trades", 0)
        print(f" {test_trades} trades, PF {test_pf}")

        # Both periods must be profitable
        train_profitable = _pf_value(train_sum.get("profit_factor", 0)) > 1.0
        test_profitable = _pf_value(test_sum.get("profit_factor", 0)) > 1.0

        wf_pass = train_profitable and test_profitable
        status = "PASS" if wf_pass else "FAIL"
        reason = ""
        if not train_profitable:
            reason = "train unprofitable"
        elif not test_profitable:
            reason = "test unprofitable"

        print(f"     Walk-forward: {'✅' if wf_pass else '❌'} {status}{' — ' + reason if reason else ''}")

        entry = {
            "name": cand_name,
            "walk_forward_pass": wf_pass,
            "train": train_sum,
            "test": test_sum,
            "full": candidate,
        }
        if strategy:
            entry["strategy"] = strategy
        survivors.append(entry)

    elapsed = time.time() - start
    print(f"\n  Phase 4 complete in {elapsed:.1f}s")

    passed = [s for s in survivors if s["walk_forward_pass"]]
    failed = [s for s in survivors if not s["walk_forward_pass"]]
    print(f"  Walk-forward: {len(passed)} passed, {len(failed)} failed")

    filename = f"phase4_{symbol}_{timeframe}.json"
    # Strip strategy from save to keep JSON clean
    save_survivors = []
    for s in survivors:
        ss = {k: v for k, v in s.items() if k != "strategy"}
        save_survivors.append(ss)
    _save_json({
        "phase": 4, "symbol": symbol, "timeframe": timeframe, "days": days,
        "train_days": train_days, "test_days": test_days,
        "survivors": save_survivors
    }, filename)
    print(f"  Saved: results/backtests/{filename}")

    return survivors


# ============================================================================
# GRADUATION CHECK
# ============================================================================

def _check_graduation(survivors: list, full_days_results: list = None):
    """Check each Phase 4 survivor against graduation criteria."""
    print()
    print("=" * 90)
    print("  GRADUATION CHECK")
    print("=" * 90)

    passed_wf = [s for s in survivors if s.get("walk_forward_pass")]
    if not passed_wf:
        print("  No strategies passed walk-forward validation.")
        print("=" * 90)
        return []

    graduated = []

    for s in passed_wf:
        name = s["name"]
        # Use full-period metrics for graduation
        full = s.get("full", {})
        trades = full.get("total_trades", 0)
        wr = full.get("win_rate", 0)
        pf = _pf_value(full.get("profit_factor", 0))
        dd = full.get("max_drawdown_pct", 100)
        avg_r = full.get("avg_r_achieved", 0)

        reasons = []
        if trades < GRAD_MIN_TRADES:
            reasons.append(f"only {trades} trades (need {GRAD_MIN_TRADES}+)")
        if wr < GRAD_MIN_WIN_RATE:
            reasons.append(f"WR {wr*100:.1f}% (need {GRAD_MIN_WIN_RATE*100:.0f}%+)")
        if pf < GRAD_MIN_PF:
            reasons.append(f"PF {pf:.2f} (need {GRAD_MIN_PF}+)")
        if dd > GRAD_MAX_DD:
            reasons.append(f"DD {dd:.1f}% (max {GRAD_MAX_DD}%)")
        if avg_r < GRAD_MIN_AVG_R:
            reasons.append(f"Avg R {avg_r:.2f} (need {GRAD_MIN_AVG_R}+)")

        if not reasons:
            print(f"  ✅ GRADUATED: {name} — PF {pf:.2f}, WR {wr*100:.0f}%, {trades} trades")
            graduated.append(s)
        else:
            print(f"  ❌ FAILED: {name} — {', '.join(reasons)}")

    print()
    print(f"  Graduated: {len(graduated)}/{len(passed_wf)} walk-forward survivors")
    print("=" * 90)
    return graduated


# ============================================================================
# FULL SCAN
# ============================================================================

def run_full(symbol: str, timeframe: str, days: int, top_n: int = 5):
    """Run all 4 phases sequentially."""
    full_start = time.time()

    print("\n" + "=" * 90)
    print(f"  TITAN STRATEGY SCANNER — FULL SCAN")
    print(f"  {symbol} {timeframe} | {days} days | Top {top_n} for sweep/validation")
    print("=" * 90)

    # Phase 1
    p1_results = run_phase1(symbol, timeframe, days)

    # Phase 2
    p2_results = run_phase2(symbol, timeframe, days)

    # Phase 3
    p3_results = run_phase3(symbol, timeframe, days, top_n, p2_results)

    # Phase 4
    p4_survivors = run_phase4(symbol, timeframe, days, top_n, p3_results)

    # Graduation
    graduated = _check_graduation(p4_survivors)

    total_elapsed = time.time() - full_start
    print(f"\n  Full scan complete in {total_elapsed:.1f}s")

    # Save summary markdown
    _save_scan_summary(symbol, timeframe, days, p1_results, p2_results, p3_results, p4_survivors, graduated, total_elapsed)

    return graduated


def _save_scan_summary(symbol, timeframe, days, p1, p2, p3, p4, graduated, elapsed):
    """Save a human-readable summary markdown."""
    _ensure_results_dir()
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"scan_{symbol}_{timeframe}_{date_str}.md"
    path = RESULTS_DIR / filename

    lines = []
    lines.append(f"# Scan: {symbol} {timeframe} — {date_str}")
    lines.append(f"")
    lines.append(f"**Duration:** {elapsed:.1f}s")
    lines.append(f"**Period:** {days} days")
    lines.append(f"")

    # Phase 1 top 5
    lines.append(f"## Phase 1: Individual Signals (top 5)")
    p1_valid = sorted(
        [r for r in p1 if r.get("total_trades", 0) > 0],
        key=lambda r: r.get("expectancy_usd", 0), reverse=True
    )[:5]
    for r in p1_valid:
        lines.append(f"- **{r['name']}** ({r.get('direction', '?')}) — {r['total_trades']} trades, PF {_format_pf(r['profit_factor'])}, WR {r['win_rate']*100:.1f}%")
    lines.append(f"")

    # Phase 2 top 5
    lines.append(f"## Phase 2: Scenarios (top 5)")
    p2_valid = sorted(
        [r for r in p2 if r.get("total_trades", 0) > 0],
        key=lambda r: r.get("expectancy_usd", 0), reverse=True
    )[:5]
    for r in p2_valid:
        lines.append(f"- **{r['name']}** ({r.get('direction', '?')}) — {r['total_trades']} trades, PF {_format_pf(r['profit_factor'])}, WR {r['win_rate']*100:.1f}%")
    lines.append(f"")

    # Phase 3 top 5
    lines.append(f"## Phase 3: Parameter Sweep (top 5)")
    p3_valid = sorted(
        [r for r in p3 if r.get("total_trades", 0) > 0],
        key=lambda r: r.get("expectancy_usd", 0), reverse=True
    )[:5]
    for r in p3_valid:
        lines.append(f"- **{r['name']}** ({r.get('direction', '?')}) — {r['total_trades']} trades, PF {_format_pf(r['profit_factor'])}, WR {r['win_rate']*100:.1f}%")
    lines.append(f"")

    # Phase 4
    lines.append(f"## Phase 4: Walk-Forward Validation")
    for s in p4:
        status = "PASS" if s.get("walk_forward_pass") else "FAIL"
        lines.append(f"- **{s['name']}** — {status}")
    lines.append(f"")

    # Graduated
    lines.append(f"## Graduated Strategies")
    if graduated:
        for g in graduated:
            full = g.get("full", {})
            lines.append(f"- **{g['name']}** — PF {_format_pf(full.get('profit_factor', 0))}, WR {full.get('win_rate', 0)*100:.0f}%, {full.get('total_trades', 0)} trades")
    else:
        lines.append(f"No strategies graduated.")
    lines.append(f"")

    with open(path, "w") as f:
        f.write("\n".join(lines))

    print(f"  Summary saved: results/backtests/{filename}")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Titan Strategy Scanner")
    subparsers = parser.add_subparsers(dest="command")

    # Common args
    def add_common(p):
        p.add_argument("--symbol", required=True, help="Token symbol (e.g., BTC)")
        p.add_argument("--timeframe", default="4h", help="Candle timeframe (default: 4h)")
        p.add_argument("--days", type=int, default=180, help="Days of history (default: 180)")

    # Phase 1
    p1 = subparsers.add_parser("phase1", help="Individual signal scan")
    add_common(p1)

    # Phase 2
    p2 = subparsers.add_parser("phase2", help="Scenario scan")
    add_common(p2)

    # Phase 3
    p3 = subparsers.add_parser("phase3", help="Parameter sweep")
    add_common(p3)
    p3.add_argument("--top", type=int, default=5, help="Top N scenarios to sweep (default: 5)")

    # Phase 4
    p4 = subparsers.add_parser("phase4", help="Walk-forward validation")
    add_common(p4)
    p4.add_argument("--top", type=int, default=5, help="Top N to validate (default: 5)")

    # Full
    full = subparsers.add_parser("full", help="Full 4-phase scan")
    add_common(full)
    full.add_argument("--top", type=int, default=5, help="Top N for sweep/validation (default: 5)")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return

    if args.command == "phase1":
        run_phase1(args.symbol, args.timeframe, args.days)
    elif args.command == "phase2":
        run_phase2(args.symbol, args.timeframe, args.days)
    elif args.command == "phase3":
        run_phase3(args.symbol, args.timeframe, args.days, args.top)
    elif args.command == "phase4":
        run_phase4(args.symbol, args.timeframe, args.days, args.top)
    elif args.command == "full":
        run_full(args.symbol, args.timeframe, args.days, args.top)


if __name__ == "__main__":
    main()
