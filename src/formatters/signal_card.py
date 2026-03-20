#!/usr/bin/env python3
"""
Signal Card Formatter
=====================
Converts signal validation data into formatted Signal Check markdown.
Saves ~150 tokens per card by handling formatting in Python.

Usage:
    python3 src/formatters/signal_card.py '{"symbol": "BTC", ...}'
    OR
    from src.formatters.signal_card import format_signal_card
    markdown = format_signal_card(data_dict)
"""

import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.storage.intelligence import (
    log_signal_validation,
    add_to_watchlist,
    get_watchlist_by_signal
)

# ============================================================================
# EMOJI MAPPINGS
# ============================================================================

DIRECTION_EMOJIS = {
    "long": "\U0001F7E2",   # Green circle
    "short": "\U0001F534",  # Red circle
}

VERDICT_EMOJIS = {
    "bullish": "\U0001F7E2",   # Green circle
    "bearish": "\U0001F534",   # Red circle
    "neutral": "\U0001F7E1",   # Yellow circle
    "mixed": "\U0001F7E1",     # Yellow circle
}

RECOMMENDATION_EMOJIS = {
    "valid": "\u2705",           # Green check
    "invalid": "\u274C",         # Red X
    "needs_confirmation": "\u26A0\uFE0F",  # Warning
}

SIGNAL_EMOJIS = {
    "bullish": "\u2705",       # Green check
    "bearish": "\u274C",       # Red X
    "neutral": "\u2796",       # Minus
    "mixed": "\u2796",         # Minus
}

TOKEN_EMOJIS = {
    "BTC": "\U0001F7E0",       # Orange circle
    "ETH": "\U0001F535",       # Blue circle
    "SOL": "\U0001F7E3",       # Purple circle
    "DOGE": "\U0001F436",      # Dog
    "PEPE": "\U0001F438",      # Frog
    "default": "\U0001F4CA",   # Bar chart
}


def get_token_emoji(token: str) -> str:
    """Get emoji for token."""
    return TOKEN_EMOJIS.get(token.upper(), TOKEN_EMOJIS["default"])


def format_currency(value: float, decimals: int = 2) -> str:
    """Format currency with commas and appropriate suffix."""
    if value is None:
        return "N/A"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.2f}K"
    else:
        return f"${value:,.{decimals}f}"


# ============================================================================
# SIGNAL CARD FORMATTER
# ============================================================================

def format_signal_card(
    data: Dict[str, Any],
    log_to_db: bool = True,
    add_to_watchlist_auto: bool = True
) -> str:
    """
    Format a complete Signal Check card from validation data.

    Expected input schema:
    {
        "external_signal_id": 123,
        "symbol": "BTC",
        "direction": "LONG",
        "provider": "MarketInsights",
        "signal_analysis": "Price breaking out of descending triangle...",
        "chart_path": "/path/to/chart.jpg",

        "accumulation_check": {
            "score": 3,
            "verdict": "Mixed",
            "signals": [
                {"name": "Exchange flows", "verdict": "Bullish", "detail": "Outflows 1.5x avg"},
                {"name": "Smart money", "verdict": "Bearish", "detail": "Selling into strength"},
                ...
            ]
        },

        "technical_analysis": {
            "verdict": "Bullish",
            "summary": "RSI oversold, MACD crossing up"
        },

        "chart_notes": "Clean breakout from triangle, volume confirming",

        "titan_recommendation": "VALID",
        "recommendation_reason": "TA aligns with signal direction, on-chain mixed but not bearish",

        "mentor_review": {  # Optional
            "consulted": true,
            "verdict": "Proceed with caution",
            "confidence_adj": -0.1,
            "reasoning": "Smart money selling is a concern"
        },

        "suggested_levels": {  # Optional, for valid signals
            "entry": 45000,
            "stop": 43500,
            "target": 48000
        }
    }

    Args:
        data: Signal validation data dictionary
        log_to_db: Whether to log validation to database

    Returns:
        Formatted markdown string
    """
    symbol = data.get("symbol", "UNKNOWN").upper()
    direction = data.get("direction", "LONG").upper()
    provider = data.get("provider", "MarketInsights")
    signal_analysis = data.get("signal_analysis", "")
    chart_path = data.get("chart_path")

    accum = data.get("accumulation_check", {})
    ta = data.get("technical_analysis", {})
    chart_notes = data.get("chart_notes", "")
    recommendation = data.get("titan_recommendation", "NEEDS_CONFIRMATION")
    reason = data.get("recommendation_reason", "")
    mentor = data.get("mentor_review", {})
    levels = data.get("suggested_levels", {})

    # Emojis
    token_emoji = get_token_emoji(symbol)
    dir_emoji = DIRECTION_EMOJIS.get(direction.lower(), "\U0001F4CA")
    rec_emoji = RECOMMENDATION_EMOJIS.get(recommendation.lower(), "\u2753")

    # Build markdown
    lines = []

    # Header
    lines.append(f"# {token_emoji} Signal Check: {symbol} {direction}")
    lines.append("")

    # MarketInsights section
    lines.append(f"## {provider} Take")
    lines.append(f"**Direction:** {dir_emoji} {direction}")
    lines.append("")

    if signal_analysis:
        # Summarize the analysis (first 2-3 sentences or 300 chars)
        summary = signal_analysis
        if len(summary) > 400:
            # Try to cut at sentence boundary
            cut_point = summary[:400].rfind('.')
            if cut_point > 200:
                summary = summary[:cut_point + 1]
            else:
                summary = summary[:400] + "..."
        lines.append(f"**Analysis:** {summary}")
        lines.append("")

    if chart_path:
        lines.append(f"*Chart available: `{chart_path}`*")
        lines.append("")

    # Titan Validation section
    lines.append("## Titan Validation")
    lines.append("")

    # Accumulation Check
    accum_score = accum.get("score", 0)
    accum_verdict = accum.get("verdict", "Unknown")
    accum_emoji = VERDICT_EMOJIS.get(accum_verdict.lower(), "\u2753")

    lines.append(f"### Accumulation Check: {accum_score}/5 — {accum_emoji} {accum_verdict}")

    accum_signals = accum.get("signals", [])
    if accum_signals:
        for sig in accum_signals:
            name = sig.get("name", "Signal")
            verdict = sig.get("verdict", "Unknown")
            detail = sig.get("detail", "")
            emoji = SIGNAL_EMOJIS.get(verdict.lower(), "\u2796")
            lines.append(f"- {emoji} **{name}:** {verdict} — {detail}")
    lines.append("")

    # Technical Analysis
    ta_verdict = ta.get("verdict", "Neutral")
    ta_emoji = VERDICT_EMOJIS.get(ta_verdict.lower(), "\u2753")
    ta_summary = ta.get("summary", "")

    lines.append(f"### Technical Analysis: {ta_emoji} {ta_verdict}")
    if ta_summary:
        lines.append(ta_summary)
    lines.append("")

    # Chart Review
    if chart_notes:
        lines.append("### Chart Review")
        lines.append(chart_notes)
        lines.append("")

    # Verdict section
    lines.append("## Verdict")
    lines.append("")

    # Determine alignment
    signal_aligns = _check_alignment(direction, accum_verdict, ta_verdict)
    aligns_text = "Agrees" if signal_aligns else "Disagrees"
    aligns_emoji = "\u2705" if signal_aligns else "\u274C"

    lines.append(f"**Signal vs Titan:** {aligns_emoji} {aligns_text}")
    lines.append(f"**Recommendation:** {rec_emoji} **{recommendation}**")

    if reason:
        lines.append(f"**Reason:** {reason}")
    lines.append("")

    # Mentor Review (if present)
    if mentor.get("consulted"):
        lines.append("---")
        lines.append("")
        lines.append("## \U0001F393 Mentor Review")
        lines.append("")

        mentor_verdict = mentor.get("verdict", "")
        if mentor_verdict:
            lines.append(f"**Mentor's Take:** {mentor_verdict}")

        mentor_reasoning = mentor.get("reasoning", "")
        if mentor_reasoning:
            lines.append(f"**Reasoning:** {mentor_reasoning}")

        conf_adj = mentor.get("confidence_adj", 0)
        if conf_adj:
            adj_sign = "+" if conf_adj > 0 else ""
            lines.append(f"**Confidence Adjustment:** {adj_sign}{conf_adj:.2f}")
        lines.append("")

    # Suggested Levels (for valid/conditional signals)
    if levels and recommendation.upper() in ["VALID", "NEEDS_CONFIRMATION"]:
        lines.append("---")
        lines.append("")
        lines.append("## If Taking This Trade")
        lines.append("")

        entry = levels.get("entry")
        stop = levels.get("stop")
        target = levels.get("target")

        if entry:
            lines.append(f"**Suggested Entry:** {format_currency(entry, 4)}")
        if stop:
            lines.append(f"**Stop Loss:** {format_currency(stop, 4)}")
        if target:
            lines.append(f"**Target:** {format_currency(target, 4)}")

        # Calculate R:R if we have all levels
        if entry and stop and target:
            risk = abs(entry - stop)
            reward = abs(target - entry)
            if risk > 0:
                rr = reward / risk
                lines.append(f"**Risk/Reward:** {rr:.1f}R")
        lines.append("")

    # Log to database and handle post-validation actions
    validation_id = None
    watch_id = None

    if log_to_db:
        external_id = data.get("external_signal_id")
        if external_id:
            validation_id = log_signal_validation(
                external_signal_id=external_id,
                symbol=symbol,
                direction=direction,
                provider=provider,
                signal_analysis=signal_analysis[:500] if signal_analysis else None,
                accumulation_score=accum_score,
                ta_verdict=ta_verdict,
                onchain_verdict=accum_verdict,
                signal_aligns=signal_aligns,
                mentor_consulted=mentor.get("consulted", False),
                mentor_verdict=mentor.get("verdict"),
                mentor_confidence_adj=mentor.get("confidence_adj"),
                titan_recommendation=recommendation,
                recommendation_reason=reason,
                chart_analyzed=bool(chart_notes),
                chart_notes=chart_notes,
                chart_path=chart_path,
                suggested_entry=levels.get("entry"),
                suggested_stop=levels.get("stop"),
                suggested_target=levels.get("target")
            )

            # Handle watchlist action
            if add_to_watchlist_auto and validation_id:
                watch_id = handle_post_validation_actions(data, validation_id, recommendation)

    # Footer with tracking info
    lines.append("---")
    footer_parts = [f"Validated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", f"Provider: {provider}"]
    if validation_id:
        footer_parts.append(f"ID: {validation_id[:8]}")
    if watch_id:
        footer_parts.append(f"Watch: {watch_id}")
    lines.append(f"*{' | '.join(footer_parts)}*")

    markdown = "\n".join(lines)
    return markdown


def _check_alignment(direction: str, accum_verdict: str, ta_verdict: str) -> bool:
    """
    Check if external signal direction aligns with Titan's analysis.

    Args:
        direction: LONG or SHORT
        accum_verdict: Accumulation verdict (Bullish/Bearish/Mixed/Neutral)
        ta_verdict: TA verdict (Bullish/Bearish/Neutral)

    Returns:
        True if signal aligns with Titan, False otherwise
    """
    direction = direction.upper()
    accum_lower = accum_verdict.lower()
    ta_lower = ta_verdict.lower()

    # For LONG signals
    if direction == "LONG":
        # Aligns if TA is bullish and on-chain is not bearish
        if ta_lower == "bullish" and accum_lower != "bearish":
            return True
        # Also aligns if both are bullish
        if ta_lower == "bullish" and accum_lower == "bullish":
            return True
        return False

    # For SHORT signals
    elif direction == "SHORT":
        # Aligns if TA is bearish and on-chain is not bullish
        if ta_lower == "bearish" and accum_lower != "bullish":
            return True
        # Also aligns if both are bearish
        if ta_lower == "bearish" and accum_lower == "bearish":
            return True
        return False

    return False


def format_signal_list(signals: List[Dict[str, Any]]) -> str:
    """
    Format a list of signals as a summary table.

    Args:
        signals: List of signal dictionaries from signals_fetcher

    Returns:
        Formatted markdown table
    """
    if not signals:
        return "No signals found."

    lines = []
    lines.append("# Recent MarketInsights Signals")
    lines.append("")
    lines.append("| ID | Symbol | Direction | Date | Has Chart |")
    lines.append("|:--:|:------:|:---------:|:----:|:---------:|")

    for sig in signals:
        sig_id = sig.get("id", "?")
        symbol = sig.get("symbol", "?").upper()
        direction = sig.get("direction", "?").upper()
        date = sig.get("created_at", "")[:10]
        has_chart = "\u2705" if sig.get("has_image") else "\u274C"

        dir_emoji = DIRECTION_EMOJIS.get(direction.lower(), "")
        lines.append(f"| {sig_id} | {symbol} | {dir_emoji} {direction} | {date} | {has_chart} |")

    lines.append("")
    lines.append(f"*{len(signals)} signals shown*")

    return "\n".join(lines)


def format_mini_signal(signal: Dict[str, Any]) -> str:
    """
    Format a signal as a one-line summary.

    Args:
        signal: Signal dictionary

    Returns:
        One-line summary string
    """
    symbol = signal.get("symbol", "?").upper()
    direction = signal.get("direction", "?").upper()
    date = signal.get("created_at", "")[:10]

    token_emoji = get_token_emoji(symbol)
    dir_emoji = DIRECTION_EMOJIS.get(direction.lower(), "")

    # Get first sentence of analysis
    desc = signal.get("setup_description", signal.get("raw_message", ""))
    if desc:
        first_sentence = desc.split('.')[0]
        if len(first_sentence) > 60:
            first_sentence = first_sentence[:60] + "..."
    else:
        first_sentence = "Chart analysis"

    has_chart = "\U0001F4CA" if signal.get("has_image") else ""

    return f"{token_emoji} **{symbol}** {dir_emoji} {direction} ({date}) {has_chart} — {first_sentence}"


# ============================================================================
# RECOMMENDATION LOGIC
# ============================================================================

def handle_post_validation_actions(
    data: Dict[str, Any],
    validation_id: str,
    recommendation: str
) -> Optional[str]:
    """
    Handle post-validation actions based on recommendation.

    - VALID: Add to watchlist as 'entry_timing' (ready for entry)
    - NEEDS_CONFIRMATION: Add to watchlist as 'confirmation' (waiting for condition)
    - INVALID: Optionally add as 'structural' watch (monitoring for reversal)

    Args:
        data: Full validation data dict
        validation_id: The generated validation ID
        recommendation: VALID/INVALID/NEEDS_CONFIRMATION

    Returns:
        watch_id if added to watchlist, None otherwise
    """
    external_id = data.get("external_signal_id")
    symbol = data.get("symbol", "").upper()
    direction = data.get("direction", "").upper()

    # Check if already on watchlist
    if external_id:
        existing = get_watchlist_by_signal(external_id)
        if existing:
            return existing.get('watch_id')

    accum = data.get("accumulation_check", {})
    ta = data.get("technical_analysis", {})
    levels = data.get("suggested_levels", {})
    perps_data = data.get("perps_data", {})

    # Determine watch type based on recommendation
    if recommendation == "VALID":
        watch_type = "entry_timing"
        thesis = f"MarketInsights {direction} signal validated by Titan. Watching for entry timing."
        priority = 8
    elif recommendation == "NEEDS_CONFIRMATION":
        watch_type = "confirmation"
        thesis = f"MarketInsights {direction} signal needs confirmation. {data.get('recommendation_reason', '')}"
        priority = 6
    else:  # INVALID
        # Don't auto-add invalid signals to watchlist
        return None

    # Determine perps bias
    perps_bias = None
    if perps_data:
        long_count = perps_data.get('long_count', 0)
        short_count = perps_data.get('short_count', 0)
        if short_count > long_count * 2:
            perps_bias = 'short_heavy'
        elif long_count > short_count * 2:
            perps_bias = 'long_heavy'
        else:
            perps_bias = 'balanced'

    # Add to watchlist
    watch_id = add_to_watchlist(
        symbol=symbol,
        source_type='telegram_signal',
        watch_type=watch_type,
        direction=direction,
        external_signal_id=external_id,
        validation_id=validation_id,
        original_thesis=thesis,
        price_at_creation=data.get("current_price"),
        support_level=levels.get("stop"),  # Often stop is near support
        resistance_level=levels.get("target"),
        stop_level=levels.get("stop"),
        target_level=levels.get("target"),
        original_accumulation_score=accum.get("score"),
        original_ta_verdict=ta.get("verdict"),
        original_onchain_verdict=accum.get("verdict"),
        original_perps_bias=perps_bias,
        check_frequency="session",
        priority=priority
    )

    return watch_id


def determine_recommendation(
    direction: str,
    ta_verdict: str,
    accum_verdict: str,
    accum_score: int = None
) -> tuple[str, str]:
    """
    Determine Titan's recommendation based on signal and analysis.

    Args:
        direction: Signal direction (LONG/SHORT)
        ta_verdict: TA verdict (Bullish/Bearish/Neutral)
        accum_verdict: On-chain verdict (Bullish/Bearish/Mixed/Neutral)
        accum_score: Accumulation score (0-5)

    Returns:
        (recommendation, reason)

    Recommendation Logic:
    | Signal | Titan TA | On-Chain      | Recommendation |
    |--------|----------|---------------|----------------|
    | Long   | Bullish  | Accumulating  | VALID — Full size |
    | Long   | Bullish  | Mixed         | VALID — Reduced size |
    | Long   | Bearish  | Any           | INVALID — Conflicting |
    | Long   | Neutral  | Accumulating  | NEEDS_CONFIRMATION |
    | Short  | Bearish  | Distributing  | VALID — Full size |
    | Short  | Bullish  | Any           | INVALID — Conflicting |
    """
    direction = direction.upper()
    ta_lower = ta_verdict.lower()
    accum_lower = accum_verdict.lower()

    # Normalize accumulation verdict
    is_accumulating = accum_lower in ["bullish", "accumulating", "accumulation"]
    is_distributing = accum_lower in ["bearish", "distributing", "distribution"]
    is_mixed = accum_lower in ["mixed", "neutral"]

    if direction == "LONG":
        if ta_lower == "bullish":
            if is_accumulating:
                return "VALID", "TA bullish + on-chain accumulating. Full size."
            elif is_mixed:
                return "VALID", "TA bullish + on-chain mixed. Consider reduced size."
            elif is_distributing:
                return "NEEDS_CONFIRMATION", "TA bullish but on-chain distributing. Wait for alignment."
        elif ta_lower == "bearish":
            return "INVALID", "Signal conflicts with bearish TA."
        else:  # Neutral
            if is_accumulating:
                return "NEEDS_CONFIRMATION", "TA neutral but on-chain accumulating. Wait for TA confirmation."
            else:
                return "INVALID", "TA neutral and on-chain not supporting."

    elif direction == "SHORT":
        if ta_lower == "bearish":
            if is_distributing:
                return "VALID", "TA bearish + on-chain distributing. Full size."
            elif is_mixed:
                return "VALID", "TA bearish + on-chain mixed. Consider reduced size."
            elif is_accumulating:
                return "NEEDS_CONFIRMATION", "TA bearish but on-chain accumulating. Wait for alignment."
        elif ta_lower == "bullish":
            return "INVALID", "Signal conflicts with bullish TA."
        else:  # Neutral
            if is_distributing:
                return "NEEDS_CONFIRMATION", "TA neutral but on-chain distributing. Wait for TA confirmation."
            else:
                return "INVALID", "TA neutral and on-chain not supporting."

    return "NEEDS_CONFIRMATION", "Unable to determine alignment."


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI for testing signal card formatting."""
    if len(sys.argv) < 2:
        # Demo with sample data
        sample = {
            "external_signal_id": 123,
            "symbol": "BTC",
            "direction": "LONG",
            "provider": "MarketInsights",
            "signal_analysis": "BTC is forming a bullish ascending triangle on the 4H timeframe. Price is compressing against the upper resistance at $45,000 with higher lows forming. Volume is declining into the apex, typical of a continuation pattern.",
            "chart_path": "/path/to/chart.jpg",

            "accumulation_check": {
                "score": 3,
                "verdict": "Mixed",
                "signals": [
                    {"name": "Exchange flows", "verdict": "Bullish", "detail": "Outflows 1.5x avg"},
                    {"name": "Fresh wallets", "verdict": "Bullish", "detail": "New buyers entering"},
                    {"name": "Smart money", "verdict": "Bearish", "detail": "Reducing exposure"},
                    {"name": "Top PnL traders", "verdict": "Neutral", "detail": "Flat positioning"},
                    {"name": "Whale activity", "verdict": "Bullish", "detail": "Accumulating quietly"}
                ]
            },

            "technical_analysis": {
                "verdict": "Bullish",
                "summary": "RSI at 55, MACD bullish cross forming. ADX at 28 showing trend strength building. Price above 20 and 50 EMAs."
            },

            "chart_notes": "Clean ascending triangle formation. Support trendline tested 3x. Watch for breakout above $45K with volume.",

            "titan_recommendation": "VALID",
            "recommendation_reason": "TA aligns with signal direction. On-chain mixed but not bearish. Smart money selling is a concern but not a dealbreaker.",

            "suggested_levels": {
                "entry": 44800,
                "stop": 43500,
                "target": 48000
            }
        }
        print(format_signal_card(sample, log_to_db=False))
    else:
        # Parse JSON from argument
        try:
            data = json.loads(sys.argv[1])
            print(format_signal_card(data))
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
