#!/usr/bin/env python3
"""
Signals Fetcher
===============
Query MarketInsights signals from external signals database for validation.

External Database: /Users/johnny_main/Developer/data/signals/signals.db
Provider Filter: MarketInsights only

Usage:
    python3 src/fetchers/signals_fetcher.py recent --hours 24
    python3 src/fetchers/signals_fetcher.py token --token BTC
    python3 src/fetchers/signals_fetcher.py show --id 123
    python3 src/fetchers/signals_fetcher.py providers
"""

import os
import sqlite3
import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

# ============================================================================
# CONFIGURATION
# ============================================================================

def _load_signals_db_path() -> Path:
    """Get signals DB path from env, .env file, or default."""
    # Check environment variable first
    env_val = os.environ.get("SIGNALS_DB_PATH")
    if env_val:
        return Path(env_val)

    # Try .env file at project root
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("SIGNALS_DB_PATH=") and not line.startswith("#"):
                    value = line.split("=", 1)[1].strip()
                    if value and value != '""' and value != "''":
                        return Path(value)

    # Default
    return Path("/Users/johnny_main/Developer/data/signals/signals.db")


# External signals database (read-only)
SIGNALS_DB_PATH = _load_signals_db_path()

# Only fetch from MarketInsights provider
PROVIDER_FILTER = "MarketInsights"


# ============================================================================
# DATABASE CONNECTION
# ============================================================================

def get_connection() -> sqlite3.Connection:
    """Get read-only connection to external signals database."""
    if not SIGNALS_DB_PATH.exists():
        raise FileNotFoundError(f"Signals database not found at {SIGNALS_DB_PATH}")

    # Open as read-only via URI
    conn = sqlite3.connect(f"file:{SIGNALS_DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================================
# QUERY FUNCTIONS
# ============================================================================

def get_recent_signals(hours: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get MarketInsights signals from the last N hours.

    Args:
        hours: Number of hours to look back
        limit: Maximum number of signals to return

    Returns:
        List of signal dictionaries
    """
    conn = get_connection()
    cutoff = datetime.now() - timedelta(hours=hours)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")

    cursor = conn.execute(
        """SELECT * FROM signals
           WHERE provider = ?
           AND created_at >= ?
           ORDER BY created_at DESC
           LIMIT ?""",
        (PROVIDER_FILTER, cutoff_str, limit)
    )

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_signal_by_id(signal_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a single signal by its database ID.

    Args:
        signal_id: Database row ID

    Returns:
        Signal dictionary or None if not found
    """
    conn = get_connection()
    cursor = conn.execute(
        "SELECT * FROM signals WHERE id = ? AND provider = ?",
        (signal_id, PROVIDER_FILTER)
    )

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_signals_for_token(symbol: str, days: int = 7, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get MarketInsights signals for a specific token.

    Args:
        symbol: Token symbol (e.g., BTC, ETH)
        days: Number of days to look back
        limit: Maximum number of signals to return

    Returns:
        List of signal dictionaries
    """
    conn = get_connection()
    cutoff = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")

    # Match symbol case-insensitively
    cursor = conn.execute(
        """SELECT * FROM signals
           WHERE provider = ?
           AND UPPER(symbol) = UPPER(?)
           AND created_at >= ?
           ORDER BY created_at DESC
           LIMIT ?""",
        (PROVIDER_FILTER, symbol, cutoff_str, limit)
    )

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_signal_image_path(signal_id: int) -> Optional[str]:
    """
    Get the chart image path for a signal.

    Args:
        signal_id: Database row ID

    Returns:
        Absolute path to image file, or None if no image
    """
    signal = get_signal_by_id(signal_id)
    if signal and signal.get("has_image") and signal.get("image_path"):
        image_path = Path(signal["image_path"])
        if image_path.exists():
            return str(image_path)
    return None


def get_signals_with_images(hours: int = 24, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get recent signals that have chart images attached.

    Args:
        hours: Number of hours to look back
        limit: Maximum number of signals to return

    Returns:
        List of signal dictionaries with images
    """
    conn = get_connection()
    cutoff = datetime.now() - timedelta(hours=hours)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")

    cursor = conn.execute(
        """SELECT * FROM signals
           WHERE provider = ?
           AND has_image = 1
           AND created_at >= ?
           ORDER BY created_at DESC
           LIMIT ?""",
        (PROVIDER_FILTER, cutoff_str, limit)
    )

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_latest_signal_for_token(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get the most recent signal for a token.

    Args:
        symbol: Token symbol (e.g., BTC, ETH)

    Returns:
        Signal dictionary or None if no signals found
    """
    signals = get_signals_for_token(symbol, days=30, limit=1)
    return signals[0] if signals else None


def get_signal_stats() -> Dict[str, Any]:
    """
    Get statistics about MarketInsights signals.

    Returns:
        Dictionary with signal statistics
    """
    conn = get_connection()
    stats = {}

    # Total signals
    cursor = conn.execute(
        "SELECT COUNT(*) FROM signals WHERE provider = ?",
        (PROVIDER_FILTER,)
    )
    stats["total_signals"] = cursor.fetchone()[0]

    # Signals with images
    cursor = conn.execute(
        "SELECT COUNT(*) FROM signals WHERE provider = ? AND has_image = 1",
        (PROVIDER_FILTER,)
    )
    stats["signals_with_images"] = cursor.fetchone()[0]

    # Signals by direction
    cursor = conn.execute(
        """SELECT direction, COUNT(*) as count
           FROM signals
           WHERE provider = ?
           GROUP BY direction""",
        (PROVIDER_FILTER,)
    )
    stats["by_direction"] = {row[0]: row[1] for row in cursor.fetchall()}

    # Top tokens
    cursor = conn.execute(
        """SELECT UPPER(symbol) as symbol, COUNT(*) as count
           FROM signals
           WHERE provider = ?
           GROUP BY UPPER(symbol)
           ORDER BY count DESC
           LIMIT 10""",
        (PROVIDER_FILTER,)
    )
    stats["top_tokens"] = {row[0]: row[1] for row in cursor.fetchall()}

    # Signals in last 24h
    cutoff = datetime.now() - timedelta(hours=24)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.execute(
        """SELECT COUNT(*) FROM signals
           WHERE provider = ? AND created_at >= ?""",
        (PROVIDER_FILTER, cutoff_str)
    )
    stats["last_24h"] = cursor.fetchone()[0]

    # Signals in last 7d
    cutoff = datetime.now() - timedelta(days=7)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.execute(
        """SELECT COUNT(*) FROM signals
           WHERE provider = ? AND created_at >= ?""",
        (PROVIDER_FILTER, cutoff_str)
    )
    stats["last_7d"] = cursor.fetchone()[0]

    # Date range
    cursor = conn.execute(
        """SELECT MIN(created_at), MAX(created_at)
           FROM signals WHERE provider = ?""",
        (PROVIDER_FILTER,)
    )
    row = cursor.fetchone()
    stats["first_signal"] = row[0]
    stats["last_signal"] = row[1]

    conn.close()
    return stats


def get_available_providers() -> List[str]:
    """
    Get list of all providers in the signals database.

    Returns:
        List of provider names
    """
    conn = get_connection()
    cursor = conn.execute(
        "SELECT DISTINCT provider FROM signals WHERE provider IS NOT NULL"
    )
    providers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return providers


def search_signals(
    symbol: str = None,
    direction: str = None,
    has_image: bool = None,
    days: int = 30,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Search signals with multiple filters.

    Args:
        symbol: Filter by token symbol
        direction: Filter by direction (long/short)
        has_image: Filter by whether signal has chart image
        days: Number of days to look back
        limit: Maximum number of signals to return

    Returns:
        List of matching signal dictionaries
    """
    conn = get_connection()
    cutoff = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")

    conditions = ["provider = ?", "created_at >= ?"]
    params = [PROVIDER_FILTER, cutoff_str]

    if symbol:
        conditions.append("UPPER(symbol) = UPPER(?)")
        params.append(symbol)

    if direction:
        conditions.append("direction = ?")
        params.append(direction.lower())

    if has_image is not None:
        conditions.append("has_image = ?")
        params.append(1 if has_image else 0)

    params.append(limit)

    query = f"""SELECT * FROM signals
                WHERE {' AND '.join(conditions)}
                ORDER BY created_at DESC
                LIMIT ?"""

    cursor = conn.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


# ============================================================================
# DIRECTION INFERENCE
# ============================================================================

def infer_direction(message: str) -> str:
    """
    Infer trade direction from message text.

    Ignores the stored direction column (unreliable) and derives
    direction from the actual analysis content.

    Args:
        message: Signal message/analysis text

    Returns:
        'LONG', 'SHORT', or 'NEUTRAL' if ambiguous
    """
    if not message:
        return 'NEUTRAL'

    text = message.lower()

    # Bearish/short indicators
    bearish_words = [
        'bearish', 'short', 'breakdown', 'broken down', 'broke down',
        'downside', 'downtrend', 'sell', 'selling', 'weakness',
        'distribution', 'rejected', 'rejection', 'failed', 'losing support',
        'lost support', 'below support', 'lower low', 'head and shoulders',
        'descending', 'falling', 'drop', 'crash', 'dump', 'capitulation'
    ]

    # Bullish/long indicators
    bullish_words = [
        'bullish', 'long', 'breakout', 'breaking out', 'broke out',
        'upside', 'uptrend', 'buy', 'buying', 'strength',
        'accumulation', 'accumulating', 'bounce', 'bouncing', 'recovery',
        'reclaim', 'reclaiming', 'above resistance', 'higher high',
        'ascending', 'rising', 'rally', 'pump', 'moon'
    ]

    bear_score = sum(1 for word in bearish_words if word in text)
    bull_score = sum(1 for word in bullish_words if word in text)

    if bear_score > bull_score:
        return 'SHORT'
    elif bull_score > bear_score:
        return 'LONG'
    return 'NEUTRAL'


# ============================================================================
# FORMATTING HELPERS
# ============================================================================

def format_signal_summary(signal: Dict[str, Any]) -> str:
    """
    Format a signal as a one-line summary.

    Args:
        signal: Signal dictionary

    Returns:
        Formatted summary string
    """
    symbol = (signal.get("symbol") or "?").upper()
    created = (signal.get("created_at") or "")[:16]  # Trim to YYYY-MM-DD HH:MM
    has_img = "+" if signal.get("has_image") else " "
    signal_id = signal.get("id", "?")

    # Get message text for direction inference
    message = signal.get("setup_description") or signal.get("raw_message") or ""

    # Infer direction from message text (ignore stored direction)
    direction = infer_direction(message)

    # Get first line of setup description for display
    desc = message.split("\n")[0][:50] if message else "Chart analysis"

    return f"[{signal_id:>4}] {symbol:<6} {direction:<7} {created} {has_img} {desc}"


def format_signal_detail(signal: Dict[str, Any]) -> str:
    """
    Format a signal with full details.

    Args:
        signal: Signal dictionary

    Returns:
        Multi-line formatted string
    """
    lines = []

    symbol = (signal.get("symbol") or "?").upper()
    signal_id = signal.get("id", "?")

    # Get message text for direction inference
    message = signal.get("setup_description") or signal.get("raw_message") or ""

    # Infer direction from message text (ignore stored direction)
    direction = infer_direction(message)

    lines.append(f"=== Signal #{signal_id}: {symbol} {direction} ===")
    lines.append("")

    # Metadata
    lines.append(f"Created: {signal.get('created_at') or 'N/A'}")
    lines.append(f"Signal Type: {signal.get('signal_type') or 'N/A'}")
    lines.append(f"Market: {signal.get('market_type') or 'spot'} | Timeframe: {signal.get('timeframe') or '1D'}")

    # Levels (if provided)
    if signal.get("entry_1"):
        entries = [signal.get(f"entry_{i}") for i in range(1, 4) if signal.get(f"entry_{i}")]
        lines.append(f"Entries: {', '.join(str(e) for e in entries)}")

    if signal.get("stop_loss"):
        lines.append(f"Stop Loss: {signal['stop_loss']}")

    targets = [signal.get(f"target_{i}") for i in range(1, 6) if signal.get(f"target_{i}")]
    if targets:
        lines.append(f"Targets: {', '.join(str(t) for t in targets)}")

    lines.append("")

    # Analysis content
    desc = signal.get("setup_description") or signal.get("raw_message") or "No description available"
    lines.append("Analysis:")
    lines.append(desc)

    # Image info
    if signal.get("has_image"):
        lines.append("")
        lines.append(f"Chart Image: {signal.get('image_path', 'Available')}")

    return "\n".join(lines)


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Query MarketInsights signals for Titan validation"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # recent
    recent_parser = subparsers.add_parser("recent", help="Get recent signals")
    recent_parser.add_argument("--hours", type=int, default=24, help="Hours to look back (default: 24)")
    recent_parser.add_argument("--limit", type=int, default=20, help="Max signals (default: 20)")

    # token
    token_parser = subparsers.add_parser("token", help="Get signals for a token")
    token_parser.add_argument("--token", required=True, help="Token symbol (e.g., BTC)")
    token_parser.add_argument("--days", type=int, default=7, help="Days to look back (default: 7)")

    # show
    show_parser = subparsers.add_parser("show", help="Show signal details")
    show_parser.add_argument("--id", type=int, required=True, help="Signal ID")

    # stats
    subparsers.add_parser("stats", help="Show signal statistics")

    # providers
    subparsers.add_parser("providers", help="List available providers")

    # search
    search_parser = subparsers.add_parser("search", help="Search signals with filters")
    search_parser.add_argument("--token", help="Filter by token")
    search_parser.add_argument("--direction", choices=["long", "short"], help="Filter by direction")
    search_parser.add_argument("--with-image", action="store_true", help="Only signals with images")
    search_parser.add_argument("--days", type=int, default=30, help="Days to look back")
    search_parser.add_argument("--limit", type=int, default=20, help="Max results")

    args = parser.parse_args()

    try:
        if args.command == "recent":
            signals = get_recent_signals(hours=args.hours, limit=args.limit)
            if not signals:
                print(f"No MarketInsights signals in the last {args.hours} hours")
                return

            print(f"\n=== Recent MarketInsights Signals ({len(signals)} found) ===\n")
            print(f"{'ID':>5}  {'Symbol':<6} {'Dir':<5} {'Date':<16} {'Img'} {'Description'}")
            print("-" * 70)
            for sig in signals:
                print(format_signal_summary(sig))

        elif args.command == "token":
            signals = get_signals_for_token(args.token, days=args.days)
            if not signals:
                print(f"No MarketInsights signals for {args.token.upper()} in the last {args.days} days")
                return

            print(f"\n=== {args.token.upper()} Signals ({len(signals)} found) ===\n")
            for sig in signals:
                print(format_signal_summary(sig))

        elif args.command == "show":
            signal = get_signal_by_id(args.id)
            if not signal:
                print(f"Signal #{args.id} not found (or not from MarketInsights)")
                return

            print(format_signal_detail(signal))

        elif args.command == "stats":
            stats = get_signal_stats()
            print("\n=== MarketInsights Signal Statistics ===\n")
            print(f"Total Signals: {stats['total_signals']}")
            print(f"With Images: {stats['signals_with_images']}")
            print(f"Last 24h: {stats['last_24h']}")
            print(f"Last 7d: {stats['last_7d']}")
            print(f"\nDate Range: {stats['first_signal']} to {stats['last_signal']}")

            if stats['by_direction']:
                print("\nBy Direction:")
                for direction, count in stats['by_direction'].items():
                    print(f"  {direction}: {count}")

            if stats['top_tokens']:
                print("\nTop Tokens:")
                for token, count in stats['top_tokens'].items():
                    print(f"  {token}: {count}")

        elif args.command == "providers":
            providers = get_available_providers()
            print("\n=== Available Providers ===\n")
            for p in providers:
                marker = " <-- Active" if p == PROVIDER_FILTER else ""
                print(f"  {p}{marker}")
            print(f"\nNote: This tool is hardcoded to use '{PROVIDER_FILTER}' only")

        elif args.command == "search":
            signals = search_signals(
                symbol=args.token,
                direction=args.direction,
                has_image=True if args.with_image else None,
                days=args.days,
                limit=args.limit
            )
            if not signals:
                print("No signals match the search criteria")
                return

            print(f"\n=== Search Results ({len(signals)} found) ===\n")
            for sig in signals:
                print(format_signal_summary(sig))

        else:
            parser.print_help()

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
