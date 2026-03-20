#!/usr/bin/env python3
"""
Trade Card Formatter
====================
Converts JSON interpretation data into formatted Titan Trade Card markdown.
Saves ~150 tokens per card by handling formatting in Python.

Usage:
    python trade_card.py '{"token": "ETH", ...}'
    OR
    from formatters.trade_card import format_trade_card
    markdown = format_trade_card(data_dict)
"""

import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.storage.intelligence import log_trade_card

# ============================================================================
# EMOJI MAPPINGS
# ============================================================================

VERDICT_EMOJIS = {
    "bullish": "\U0001F7E2",   # Green circle
    "bearish": "\U0001F534",   # Red circle
    "neutral": "\U0001F7E1",   # Yellow circle
}

SIGNAL_EMOJIS = {
    "bullish": "\U0001F4C8",   # Chart up
    "bearish": "\U0001F4C9",   # Chart down
    "mixed": "\U000023F9",     # Stop button (neutral)
    "neutral": "\U000023F9",
}

POINT_EMOJIS = {
    "bullish": "\u2705",       # Green check
    "bearish": "\u274C",       # Red X
    "neutral": "\u26A0\uFE0F", # Warning
    "info": "\u2139\uFE0F",    # Info
}

TOKEN_EMOJIS = {
    "BTC": "\U0001F7E0",       # Orange circle
    "ETH": "\U0001F535",       # Blue circle
    "SOL": "\U0001F7E3",       # Purple circle
    "DOGE": "\U0001F436",      # Dog
    "SHIB": "\U0001F415",      # Dog face
    "PEPE": "\U0001F438",      # Frog
    "default": "\U0001F4B0",   # Money bag
}


def get_token_emoji(token: str) -> str:
    """Get emoji for token."""
    return TOKEN_EMOJIS.get(token.upper(), TOKEN_EMOJIS["default"])


def format_currency(value: float, decimals: int = 2) -> str:
    """Format currency with commas and appropriate suffix."""
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.2f}K"
    else:
        return f"${value:,.{decimals}f}"


def format_number(value: float) -> str:
    """Format number with appropriate suffix."""
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    elif abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    elif abs(value) >= 1_000:
        return f"{value / 1_000:.2f}K"
    else:
        return f"{value:,.2f}"


def format_percent(value: float) -> str:
    """Format percentage."""
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"


# ============================================================================
# TRADE CARD FORMATTER
# ============================================================================

def format_trade_card(
    data: Dict[str, Any],
    log_to_db: bool = True,
) -> str:
    """
    Format a complete Titan Trade Card from JSON data.

    Expected input schema:
    {
        "token": "ETH",
        "snapshot": {
            "price": 3450.50,
            "market_cap": 415000000000,
            "rank": 2,
            "change_24h": -2.5  # optional
        },
        "price_action": {
            "summary": "Testing support",  # 2-3 words
            "interpretation": "Price is consolidating..."  # paragraph
        },
        "flow_signals": {
            "signal": "Bullish",  # Bullish/Bearish/Mixed
            "interpretation": "Exchange outflows..."  # paragraph
        },
        "verdict": {
            "signal": "Bullish",  # Bullish/Bearish/Neutral
            "summary": "Accumulation zone with strong holder conviction",
            "points": [
                {"type": "bullish", "text": "Exchange outflows 2.1x average"},
                {"type": "bullish", "text": "Smart money accumulating"},
                {"type": "neutral", "text": "Volume declining"}
            ]
        }
    }

    Args:
        data: Trade card data dictionary
        log_to_db: Whether to log to database

    Returns:
        Formatted markdown string
    """
    token = data.get("token", "UNKNOWN").upper()
    snapshot = data.get("snapshot", {})
    price_action = data.get("price_action", {})
    flow_signals = data.get("flow_signals", {})
    verdict_data = data.get("verdict", {})

    token_emoji = get_token_emoji(token)
    verdict_signal = verdict_data.get("signal", "Neutral").lower()
    verdict_emoji = VERDICT_EMOJIS.get(verdict_signal, VERDICT_EMOJIS["neutral"])

    # Build markdown
    lines = []

    # Header
    lines.append(f"# {token_emoji} {token} — Titan Trade Card")
    lines.append("")

    # Snapshot
    lines.append("## Snapshot")
    price = snapshot.get("price", 0)
    mcap = snapshot.get("market_cap", 0)
    rank = snapshot.get("rank", "N/A")
    change_24h = snapshot.get("change_24h")

    snapshot_parts = [f"**Price:** {format_currency(price)}"]
    snapshot_parts.append(f"**Market Cap:** {format_currency(mcap)}")
    snapshot_parts.append(f"**Rank:** #{rank}")
    if change_24h is not None:
        snapshot_parts.append(f"**24h:** {format_percent(change_24h)}")

    lines.append(" | ".join(snapshot_parts))
    lines.append("")

    # Price Action
    pa_summary = price_action.get("summary", "Consolidating")
    pa_interpretation = price_action.get("interpretation", "")
    lines.append(f"## Price Action: {pa_summary}")
    if pa_interpretation:
        lines.append(pa_interpretation)
    lines.append("")

    # Flow Signals
    flow_signal = flow_signals.get("signal", "Mixed")
    flow_emoji = SIGNAL_EMOJIS.get(flow_signal.lower(), SIGNAL_EMOJIS["neutral"])
    flow_interpretation = flow_signals.get("interpretation", "")
    lines.append(f"## Flow Signals: {flow_emoji} {flow_signal}")
    if flow_interpretation:
        lines.append(flow_interpretation)
    lines.append("")

    # Liquidity Map (optional — only if Coinglass data present)
    liquidity_map = data.get("liquidity_map")
    if liquidity_map:
        liq_signal = liquidity_map.get("signal", "Neutral")
        liq_emoji = SIGNAL_EMOJIS.get(liq_signal.lower(), SIGNAL_EMOJIS["neutral"])
        lines.append(f"## Liquidity Map: {liq_emoji} {liq_signal}")

        # Liquidation activity
        liq_total = liquidity_map.get("total_24h_usd", 0)
        liq_long = liquidity_map.get("long_liq_24h_usd", 0)
        liq_short = liquidity_map.get("short_liq_24h_usd", 0)
        ls_ratio = liquidity_map.get("long_short_ratio", 1.0)
        bias = liquidity_map.get("bias", "balanced")

        parts = []
        if liq_total > 0:
            parts.append(f"**24h Liquidations:** {format_currency(liq_total)}")
            parts.append(f"**L/S:** {ls_ratio:.1f}x")
        if parts:
            lines.append(" | ".join(parts))

        # Max pain
        max_pain = liquidity_map.get("max_pain_price")
        max_pain_dist = liquidity_map.get("max_pain_distance_pct")
        pc_ratio = liquidity_map.get("put_call_oi_ratio")

        mp_parts = []
        if max_pain and max_pain > 0:
            mp_parts.append(f"**Max Pain:** {format_currency(max_pain)} ({max_pain_dist:+.1f}%)")
        if pc_ratio and pc_ratio > 0:
            mp_parts.append(f"**P/C Ratio:** {pc_ratio:.2f}x")
        if mp_parts:
            lines.append(" | ".join(mp_parts))

        liq_interp = liquidity_map.get("interpretation", "")
        if liq_interp:
            lines.append(liq_interp)

        setup = liquidity_map.get("setup")
        if setup and setup.get("detected"):
            dir_emoji = "\U0001F7E2" if setup.get("direction") == "long" else "\U0001F534"
            lines.append(f"\n{dir_emoji} **Liquidity Grab Fade — {setup.get('direction', '').upper()}** (Confidence: {setup.get('confidence', '').upper()})")
            if setup.get("thesis"):
                lines.append(setup["thesis"])

        lines.append("")

    # Verdict
    verdict_signal_display = verdict_data.get("signal", "Neutral")
    verdict_summary = verdict_data.get("summary", "")
    verdict_points = verdict_data.get("points", [])

    lines.append("## Verdict")
    lines.append(f"**{verdict_emoji} {verdict_signal_display}** — {verdict_summary}")
    lines.append("")

    for point in verdict_points:
        point_type = point.get("type", "info").lower()
        point_emoji = POINT_EMOJIS.get(point_type, POINT_EMOJIS["info"])
        point_text = point.get("text", "")
        lines.append(f"- {point_emoji} {point_text}")

    lines.append("")
    lines.append("---")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    markdown = "\n".join(lines)

    # Log to database
    if log_to_db:
        log_trade_card(
            token=token,
            verdict=verdict_signal_display,
            full_markdown=markdown
        )

    return markdown


def format_mini_card(data: Dict[str, Any]) -> str:
    """
    Format a condensed trade card (for lists/summaries).

    Returns single paragraph summary.
    """
    token = data.get("token", "UNKNOWN").upper()
    verdict_data = data.get("verdict", {})
    snapshot = data.get("snapshot", {})

    token_emoji = get_token_emoji(token)
    verdict = verdict_data.get("signal", "Neutral")
    verdict_emoji = VERDICT_EMOJIS.get(verdict.lower(), VERDICT_EMOJIS["neutral"])
    price = snapshot.get("price", 0)
    summary = verdict_data.get("summary", "")

    return f"{token_emoji} **{token}** @ {format_currency(price)} — {verdict_emoji} {verdict}: {summary}"


# ============================================================================
# BATCH FORMATTING
# ============================================================================

def format_multi_token_summary(tokens: List[Dict[str, Any]]) -> str:
    """
    Format multiple token summaries into a list.

    Input: List of trade card data dicts
    """
    lines = ["# Token Summary", ""]

    for data in tokens:
        lines.append(format_mini_card(data))

    return "\n".join(lines)


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI for testing trade card formatting."""
    if len(sys.argv) < 2:
        # Demo with sample data
        sample = {
            "token": "ETH",
            "snapshot": {
                "price": 3450.50,
                "market_cap": 415000000000,
                "rank": 2,
                "change_24h": -2.5
            },
            "price_action": {
                "summary": "Testing support",
                "interpretation": "Price is consolidating at the $3,400 support level after a week of declining volume. The 4h RSI is oversold at 28, suggesting a potential bounce."
            },
            "flow_signals": {
                "signal": "Bullish",
                "interpretation": "Exchange outflows are 2.1x the 7-day average. Smart money wallets have added $45M in the past 24h. Top 100 holders showing net accumulation."
            },
            "verdict": {
                "signal": "Bullish",
                "summary": "Accumulation zone with strong holder conviction",
                "points": [
                    {"type": "bullish", "text": "Exchange outflows 2.1x average"},
                    {"type": "bullish", "text": "Smart money accumulating $45M/24h"},
                    {"type": "neutral", "text": "Volume declining - wait for confirmation"}
                ]
            }
        }
        print(format_trade_card(sample, log_to_db=False))
    else:
        # Parse JSON from argument
        try:
            data = json.loads(sys.argv[1])
            print(format_trade_card(data))
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
