#!/usr/bin/env python3
"""
Watchlist Monitor
=================
Review and update signal watchlist items. Designed to run:
1. At session startup (interactive mode)
2. Via cron (batch mode with file output)

Usage:
    python3 src/watchers/watchlist_monitor.py review              # Interactive review
    python3 src/watchers/watchlist_monitor.py review --cron       # Cron mode (outputs to file)
    python3 src/watchers/watchlist_monitor.py summary             # Quick summary
    python3 src/watchers/watchlist_monitor.py check HYPE          # Check specific symbol
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.storage.intelligence import (
    get_active_watchlist,
    get_watchlist_for_review,
    get_watchlist_stats,
    update_watchlist_check,
    update_watchlist_status,
    get_watchlist_item,
    expire_old_watchlist_items
)

# Output directory for cron reports
REPORTS_DIR = Path(__file__).parent.parent.parent / "signals" / "dashboards"


# ============================================================================
# OHLCV REFRESH
# ============================================================================

def refresh_watchlist_ohlcv(timeframes: List[str] = None) -> Dict[str, str]:
    """
    Download fresh OHLCV data for all active watchlist symbols.

    Args:
        timeframes: List of timeframes to download (default: ['4h', '1d'])

    Returns:
        Dict mapping symbol to status ('ok', 'error', or error message)
    """
    if timeframes is None:
        timeframes = ['4h', '1d']

    items = get_active_watchlist()
    symbols = list({item['symbol'] for item in items})

    if not symbols:
        return {}

    ta_script = PROJECT_ROOT / "src" / "analysis" / "indicators.py"
    results = {}

    for symbol in sorted(symbols):
        for tf in timeframes:
            key = f"{symbol}_{tf}"
            try:
                result = subprocess.run(
                    [sys.executable, str(ta_script), "download", symbol, "--timeframe", tf],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=str(PROJECT_ROOT),
                )
                if result.returncode == 0:
                    results[key] = "ok"
                else:
                    err = result.stderr.strip().split('\n')[-1] if result.stderr else "unknown error"
                    results[key] = f"error: {err}"
            except subprocess.TimeoutExpired:
                results[key] = "error: timeout"
            except Exception as e:
                results[key] = f"error: {e}"

    return results


def format_refresh_summary(results: Dict[str, str]) -> str:
    """Format OHLCV refresh results for logging."""
    if not results:
        return "No symbols to refresh."

    ok = sum(1 for v in results.values() if v == "ok")
    errors = {k: v for k, v in results.items() if v != "ok"}

    lines = [f"OHLCV refresh: {ok}/{len(results)} succeeded"]
    for key, err in errors.items():
        lines.append(f"  FAIL: {key} — {err}")

    return "\n".join(lines)


# ============================================================================
# REVIEW LOGIC
# ============================================================================

def format_watchlist_summary(items: List[Dict]) -> str:
    """
    Format a summary of watchlist items for display.

    Args:
        items: List of watchlist items

    Returns:
        Formatted markdown string
    """
    if not items:
        return "No active watchlist items."

    lines = ["# 📋 Titan Watchlist Summary", ""]

    # Group by source
    by_source = {}
    for item in items:
        source = item['source_type']
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(item)

    for source, source_items in by_source.items():
        source_label = {
            'telegram_signal': '📱 Telegram Signals',
            'manual': '✍️ Manual Watches',
            'skill': '🤖 Skill-Generated'
        }.get(source, source)

        lines.append(f"## {source_label}")
        lines.append("")
        lines.append("| Symbol | Direction | Type | Price | Last Check | Status |")
        lines.append("|--------|-----------|------|-------|------------|--------|")

        for item in source_items:
            symbol = item['symbol']
            direction = item['direction'] or '-'
            watch_type = item['watch_type']
            price = f"${item['last_price']:.2f}" if item['last_price'] else '-'
            last_check = item['last_checked'][:10] if item['last_checked'] else 'Never'

            # Status indicator
            if item['status_changed']:
                status = "⚠️ Changed"
            elif item['status'] == 'active':
                status = "✅ Active"
            else:
                status = item['status']

            lines.append(f"| {symbol} | {direction} | {watch_type} | {price} | {last_check} | {status} |")

        lines.append("")

    return "\n".join(lines)


def format_review_item(item: Dict, analysis: Dict = None) -> str:
    """
    Format a single watchlist item for review output.

    Args:
        item: Watchlist item dict
        analysis: Optional new analysis data

    Returns:
        Formatted markdown string
    """
    lines = []
    emoji = "🔔" if item['source_type'] == 'telegram_signal' else "👀"

    lines.append(f"### {emoji} {item['symbol']} {item['direction'] or ''}")
    lines.append(f"**Watch ID:** `{item['watch_id']}` | **Type:** {item['watch_type']}")

    if item['original_thesis']:
        lines.append(f"**Thesis:** {item['original_thesis']}")

    lines.append("")

    # Price comparison
    if item['price_at_creation'] and item['last_price']:
        change = ((item['last_price'] - item['price_at_creation']) / item['price_at_creation']) * 100
        change_str = f"{change:+.1f}%"
        lines.append(f"**Price:** ${item['last_price']:.2f} ({change_str} from entry)")
    elif item['last_price']:
        lines.append(f"**Price:** ${item['last_price']:.2f}")

    # Key levels
    levels = []
    if item['support_level']:
        levels.append(f"Support: ${item['support_level']:.2f}")
    if item['resistance_level']:
        levels.append(f"Resistance: ${item['resistance_level']:.2f}")
    if item['stop_level']:
        levels.append(f"Stop: ${item['stop_level']:.2f}")
    if levels:
        lines.append(f"**Levels:** {' | '.join(levels)}")

    lines.append("")

    # Analysis comparison
    lines.append("| Metric | Original | Current |")
    lines.append("|--------|----------|---------|")
    lines.append(f"| Accumulation Score | {item['original_accumulation_score'] or '-'}/5 | {item['current_accumulation_score'] or '-'}/5 |")
    lines.append(f"| TA Verdict | {item['original_ta_verdict'] or '-'} | {item['current_ta_verdict'] or '-'} |")
    lines.append(f"| On-Chain | {item['original_onchain_verdict'] or '-'} | {item['current_onchain_verdict'] or '-'} |")
    lines.append(f"| Perps Bias | {item['original_perps_bias'] or '-'} | {item['current_perps_bias'] or '-'} |")

    lines.append("")

    # Change summary
    if item['status_changed'] and item['change_summary']:
        lines.append(f"⚠️ **Analysis Changed:** {item['change_summary']}")
        lines.append("")

    # Entry/invalidation conditions
    if item['entry_conditions']:
        conditions = item['entry_conditions'] if isinstance(item['entry_conditions'], dict) else {}
        if conditions:
            lines.append(f"**Entry Triggers:** {json.dumps(conditions)}")
    if item['invalidation_conditions']:
        conditions = item['invalidation_conditions'] if isinstance(item['invalidation_conditions'], dict) else {}
        if conditions:
            lines.append(f"**Invalidation:** {json.dumps(conditions)}")

    lines.append("")
    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def generate_session_review(frequency: str = "session") -> str:
    """
    Generate a session review report for watchlist items.

    This is the main function called at Titan session startup.

    Args:
        frequency: Check frequency filter ('session', 'daily', 'hourly')

    Returns:
        Markdown report string
    """
    # Expire old items first
    expired_count = expire_old_watchlist_items()

    # Get items needing review
    items = get_watchlist_for_review(check_frequency=frequency)
    stats = get_watchlist_stats()

    lines = ["# 📊 Titan Watchlist Review", ""]
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Active Items:** {stats['active']} | **Needs Review:** {len(items)} | **Analysis Changed:** {stats['analysis_changed']}")

    if expired_count > 0:
        lines.append(f"**Auto-Expired:** {expired_count} items")

    lines.append("")

    if not items:
        lines.append("✅ **No items need review at this time.**")
        lines.append("")
        lines.append("All watchlist items are up to date.")
        return "\n".join(lines)

    lines.append("## Items Requiring Review")
    lines.append("")
    lines.append("The following items haven't been checked recently and need your attention:")
    lines.append("")

    # Group by priority
    high_priority = [i for i in items if i['priority'] >= 7]
    normal_priority = [i for i in items if i['priority'] < 7]

    if high_priority:
        lines.append("### 🔴 High Priority")
        lines.append("")
        for item in high_priority:
            lines.append(format_review_item(item))

    if normal_priority:
        lines.append("### 🟡 Normal Priority")
        lines.append("")
        for item in normal_priority:
            lines.append(format_review_item(item))

    # Action suggestions
    lines.append("## Suggested Actions")
    lines.append("")
    lines.append("For each item above, you can:")
    lines.append("1. **Re-analyze:** Say \"Check [SYMBOL]\" to run fresh analysis")
    lines.append("2. **Update status:** Say \"Update watchlist [ID] to [triggered/invalidated]\"")
    lines.append("3. **Remove:** Say \"Remove [SYMBOL] from watchlist\"")
    lines.append("4. **Take trade:** Say \"Take the [SYMBOL] trade\" to convert to trade setup")
    lines.append("")

    return "\n".join(lines)


def generate_cron_report() -> tuple[str, str]:
    """
    Generate a report suitable for cron execution.

    Returns:
        Tuple of (report_content, report_path)
    """
    report = generate_session_review()

    # Save to file
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    report_path = REPORTS_DIR / f"watchlist_review_{timestamp}.md"

    with open(report_path, 'w') as f:
        f.write(report)

    return report, str(report_path)


def get_items_with_changes() -> List[Dict]:
    """Get all active items where analysis has changed."""
    items = get_active_watchlist()
    return [i for i in items if i.get('status_changed')]


def check_single_symbol(symbol: str) -> Optional[Dict]:
    """
    Get watchlist item for a specific symbol.

    Args:
        symbol: Token symbol

    Returns:
        Watchlist item dict or None
    """
    items = get_active_watchlist(symbol=symbol.upper())
    return items[0] if items else None


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Titan Watchlist Monitor"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # review
    review_parser = subparsers.add_parser('review', help='Generate review report')
    review_parser.add_argument('--cron', action='store_true', help='Cron mode (save to file)')
    review_parser.add_argument('--refresh', action='store_true', help='Download fresh OHLCV data before review')
    review_parser.add_argument('--frequency', choices=['session', 'daily', 'hourly'], default='session')

    # summary
    subparsers.add_parser('summary', help='Quick watchlist summary')

    # check
    check_parser = subparsers.add_parser('check', help='Check specific symbol')
    check_parser.add_argument('symbol', help='Token symbol')

    # changes
    subparsers.add_parser('changes', help='List items with changed analysis')

    args = parser.parse_args()

    if args.command == "review":
        if args.refresh:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Refreshing OHLCV data for watchlist symbols...")
            results = refresh_watchlist_ohlcv()
            print(format_refresh_summary(results))
            print()

        if args.cron:
            report, path = generate_cron_report()
            print(f"Report saved to: {path}")
            # Also print summary to stdout for cron logs
            stats = get_watchlist_stats()
            print(f"Active: {stats['active']} | Needs Review: {stats['needs_review']} | Changed: {stats['analysis_changed']}")
        else:
            print(generate_session_review(args.frequency))

    elif args.command == "summary":
        items = get_active_watchlist()
        print(format_watchlist_summary(items))

    elif args.command == "check":
        item = check_single_symbol(args.symbol)
        if item:
            print(format_review_item(item))
        else:
            print(f"No watchlist item found for {args.symbol.upper()}")

    elif args.command == "changes":
        items = get_items_with_changes()
        if not items:
            print("No items with changed analysis.")
            return
        print(f"\n=== Items with Changed Analysis ({len(items)}) ===\n")
        for item in items:
            print(f"[{item['watch_id']}] {item['symbol']} - {item['change_summary'] or 'Analysis changed'}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
