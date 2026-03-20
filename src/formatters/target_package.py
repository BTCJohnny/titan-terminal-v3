#!/usr/bin/env python3
"""
Target Package Formatter
========================
Calculates position sizing based on 2% risk with minimum 3:1 RR.
Supports 3 profit targets (T1, T2, T3) for scaling out.

Usage:
    python target_package.py '{"token": "ETH", "account": 50000, ...}'
    OR
    from formatters.target_package import format_target_package
    markdown = format_target_package(data_dict)
"""

import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================================
# CONSTANTS
# ============================================================================

# Position sizing limits by category
CATEGORY_LIMITS = {
    "blue_chip": {"max_pct": 30, "tokens": ["BTC", "ETH"]},
    "large_cap": {"max_pct": 15, "rank_max": 50},
    "mid_cap": {"max_pct": 10, "rank_max": 100},
    "small_cap": {"max_pct": 5, "rank_max": 500},
    "degen": {"max_pct": 2, "rank_max": None},  # 100+ or new
}

DEFAULT_SCALE_OUT = [0.33, 0.33, 0.34]  # T1, T2, T3 percentages

# Emojis
TARGET_EMOJI = "\U0001F3AF"  # Target
MONEY_EMOJI = "\U0001F4B0"   # Money bag
WARNING_EMOJI = "\u26A0\uFE0F"  # Warning
CHECK_EMOJI = "\u2705"        # Check
X_EMOJI = "\u274C"            # X


# ============================================================================
# POSITION SIZING CALCULATIONS
# ============================================================================

def calculate_position_size(
    account: float,
    entry: float,
    stop: float,
    risk_pct: float = 2.0,
    leverage: float = 1.0
) -> Dict[str, float]:
    """
    Calculate position size based on risk percentage.

    Args:
        account: Account balance in USD
        entry: Entry price
        stop: Stop loss price
        risk_pct: Risk percentage of account (default 2%)
        leverage: Leverage multiplier (default 1x)

    Returns:
        Dict with:
            - risk_amount: Dollar amount at risk
            - risk_per_unit: Dollar risk per unit
            - position_units: Number of units to buy/sell
            - position_usd: Total position value in USD
            - margin_required: Margin required if leveraged
            - effective_risk_pct: Actual risk % after leverage
    """
    risk_amount = account * (risk_pct / 100)
    risk_per_unit = abs(entry - stop)

    if risk_per_unit == 0:
        raise ValueError("Entry and stop cannot be the same price")

    position_units = risk_amount / risk_per_unit
    position_usd = position_units * entry

    # Leverage calculations
    margin_required = position_usd / leverage if leverage > 1 else position_usd
    effective_risk_pct = (risk_amount / account) * leverage

    return {
        "risk_amount": round(risk_amount, 2),
        "risk_per_unit": round(risk_per_unit, 6),
        "position_units": round(position_units, 6),
        "position_usd": round(position_usd, 2),
        "margin_required": round(margin_required, 2),
        "effective_risk_pct": round(effective_risk_pct, 2),
    }


def calculate_rr(entry: float, stop: float, target: float, direction: str) -> float:
    """
    Calculate risk/reward ratio for a target.

    Args:
        entry: Entry price
        stop: Stop loss price
        target: Target price
        direction: "LONG" or "SHORT"

    Returns:
        RR ratio (e.g., 3.0 means 3:1)
    """
    risk = abs(entry - stop)
    if risk == 0:
        return 0.0

    if direction.upper() == "LONG":
        reward = target - entry
    else:  # SHORT
        reward = entry - target

    return round(reward / risk, 2)


def validate_rr(
    entry: float,
    stop: float,
    targets: list,
    direction: str,
    min_rr: float = 3.0
) -> Tuple[bool, str, Optional[float]]:
    """
    Validate that T3 meets minimum RR requirement.

    Args:
        entry: Entry price
        stop: Stop loss price
        targets: List of [T1, T2, T3] prices
        direction: "LONG" or "SHORT"
        min_rr: Minimum RR for T3 (default 3.0)

    Returns:
        Tuple of (is_valid, message, suggested_t3)
    """
    if len(targets) < 3:
        return False, "Need 3 targets (T1, T2, T3)", None

    t3 = targets[2]
    t3_rr = calculate_rr(entry, stop, t3, direction)

    if t3_rr >= min_rr:
        return True, f"T3 RR {t3_rr}:1 meets minimum {min_rr}:1", None

    # Calculate suggested T3 for minimum RR
    risk = abs(entry - stop)
    if direction.upper() == "LONG":
        suggested_t3 = entry + (risk * min_rr)
    else:
        suggested_t3 = entry - (risk * min_rr)

    return False, f"T3 RR {t3_rr}:1 below minimum {min_rr}:1", round(suggested_t3, 6)


def validate_direction(entry: float, stop: float, targets: list, direction: str) -> Tuple[bool, str]:
    """
    Validate that stop and targets are correct for direction.

    Returns:
        Tuple of (is_valid, message)
    """
    if direction.upper() == "LONG":
        if stop >= entry:
            return False, "LONG: Stop must be below entry"
        for i, t in enumerate(targets, 1):
            if t <= entry:
                return False, f"LONG: T{i} must be above entry"
    else:  # SHORT
        if stop <= entry:
            return False, "SHORT: Stop must be above entry"
        for i, t in enumerate(targets, 1):
            if t >= entry:
                return False, f"SHORT: T{i} must be below entry"

    return True, "Valid"


def get_token_category(token: str, rank: Optional[int] = None) -> str:
    """
    Determine token category for position limit.

    Args:
        token: Token symbol
        rank: Market cap rank (optional)

    Returns:
        Category name
    """
    token_upper = token.upper()

    # Blue chips
    if token_upper in CATEGORY_LIMITS["blue_chip"]["tokens"]:
        return "blue_chip"

    if rank is None:
        return "degen"  # Unknown rank = treat as degen

    if rank <= CATEGORY_LIMITS["large_cap"]["rank_max"]:
        return "large_cap"
    elif rank <= CATEGORY_LIMITS["mid_cap"]["rank_max"]:
        return "mid_cap"
    elif rank <= CATEGORY_LIMITS["small_cap"]["rank_max"]:
        return "small_cap"
    else:
        return "degen"


def check_category_limit(
    token: str,
    position_pct: float,
    rank: Optional[int] = None
) -> Tuple[bool, str, float]:
    """
    Check if position size exceeds category limit.

    Args:
        token: Token symbol
        position_pct: Position as % of account
        rank: Market cap rank (optional)

    Returns:
        Tuple of (is_within_limit, message, max_pct)
    """
    category = get_token_category(token, rank)
    max_pct = CATEGORY_LIMITS[category]["max_pct"]

    category_display = category.replace("_", " ").title()

    if position_pct <= max_pct:
        return True, f"{category_display}: Position {position_pct:.1f}% within {max_pct}% limit", max_pct
    else:
        return False, f"{WARNING_EMOJI} {category_display}: Position {position_pct:.1f}% exceeds {max_pct}% limit", max_pct


def calculate_scale_out(
    position_units: float,
    scale_pcts: list = None
) -> list:
    """
    Calculate units to sell at each target.

    Args:
        position_units: Total position size in units
        scale_pcts: List of percentages for each target (default [33%, 33%, 34%])

    Returns:
        List of units to sell at each target
    """
    if scale_pcts is None:
        scale_pcts = DEFAULT_SCALE_OUT

    units_per_target = []
    remaining = position_units

    for i, pct in enumerate(scale_pcts):
        if i == len(scale_pcts) - 1:
            # Last target gets all remaining
            units_per_target.append(round(remaining, 6))
        else:
            units = round(position_units * pct, 6)
            units_per_target.append(units)
            remaining -= units

    return units_per_target


def calculate_pnl_at_target(
    entry: float,
    target: float,
    units: float,
    direction: str
) -> float:
    """
    Calculate profit in USD at a target.

    Returns:
        Profit in USD (positive for profit)
    """
    if direction.upper() == "LONG":
        pnl = (target - entry) * units
    else:
        pnl = (entry - target) * units

    return round(pnl, 2)


# ============================================================================
# FORMATTING HELPERS
# ============================================================================

def format_currency(value: float, decimals: int = 2) -> str:
    """Format currency with commas and appropriate suffix."""
    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    elif abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    elif abs(value) >= 1_000:
        return f"${value:,.{decimals}f}"
    else:
        return f"${value:,.{decimals}f}"


def format_price(value: float) -> str:
    """Format price with appropriate decimals."""
    if value >= 1000:
        return f"${value:,.2f}"
    elif value >= 1:
        return f"${value:,.4f}"
    elif value >= 0.01:
        return f"${value:.6f}"
    else:
        return f"${value:.8f}"


def format_units(value: float, token: str) -> str:
    """Format units with token symbol."""
    if value >= 1000:
        return f"{value:,.2f} {token}"
    elif value >= 1:
        return f"{value:.4f} {token}"
    else:
        return f"{value:.6f} {token}"


def format_percent(value: float, include_sign: bool = True) -> str:
    """Format percentage."""
    sign = "+" if value > 0 and include_sign else ""
    if value < 0:
        sign = ""  # Negative sign included in value
    return f"{sign}{value:.2f}%"


# ============================================================================
# MAIN FORMATTER
# ============================================================================

def format_target_package(data: Dict[str, Any]) -> str:
    """
    Format a complete Target Package from JSON data.

    Expected input schema:
    {
        "token": "ETH",
        "direction": "LONG",  # or "SHORT"
        "account": 50000,     # Account balance in USD
        "entry": 3450,        # Entry price
        "stop": 3300,         # Stop loss price
        "targets": [3600, 3800, 4200],  # T1, T2, T3 prices
        "risk_pct": 2.0,      # Optional, default 2%
        "leverage": 1.0,      # Optional, default 1x
        "rank": 2,            # Optional, for category limit check
        "scale_out": [0.33, 0.33, 0.34],  # Optional, scale out percentages
        "notes": "..."        # Optional notes
    }

    Args:
        data: Target package data dictionary

    Returns:
        Formatted markdown string
    """
    # Extract data
    token = data.get("token", "UNKNOWN").upper()
    direction = data.get("direction", "LONG").upper()
    account = data.get("account", 0)
    entry = data.get("entry", 0)
    stop = data.get("stop", 0)
    targets = data.get("targets", [])
    risk_pct = data.get("risk_pct", 2.0)
    leverage = data.get("leverage", 1.0)
    rank = data.get("rank")
    scale_out = data.get("scale_out", DEFAULT_SCALE_OUT)
    notes = data.get("notes", "")

    lines = []
    errors = []
    warnings = []

    # ========== VALIDATION ==========

    # Validate direction consistency
    dir_valid, dir_msg = validate_direction(entry, stop, targets, direction)
    if not dir_valid:
        errors.append(dir_msg)

    # Validate minimum RR
    rr_valid, rr_msg, suggested_t3 = validate_rr(entry, stop, targets, direction)
    if not rr_valid:
        errors.append(rr_msg)
        if suggested_t3:
            errors.append(f"Suggested T3: {format_price(suggested_t3)}")

    # If critical errors, return error message
    if errors:
        lines.append(f"# {X_EMOJI} Target Package: REJECTED")
        lines.append("")
        lines.append("## Validation Errors")
        for err in errors:
            lines.append(f"- {X_EMOJI} {err}")
        lines.append("")
        lines.append("Fix the issues above and try again.")
        return "\n".join(lines)

    # ========== CALCULATIONS ==========

    # Position sizing
    sizing = calculate_position_size(account, entry, stop, risk_pct, leverage)

    # Category limit check
    position_pct = (sizing["position_usd"] / account) * 100
    limit_ok, limit_msg, max_pct = check_category_limit(token, position_pct, rank)
    if not limit_ok:
        warnings.append(limit_msg)
        # Calculate recommended max position
        max_position_usd = account * (max_pct / 100)
        max_units = max_position_usd / entry
        warnings.append(f"Recommended max: {format_units(max_units, token)} ({format_currency(max_position_usd)})")

    # Leverage warning
    if leverage > 1 and sizing["effective_risk_pct"] > 10:
        warnings.append(f"{WARNING_EMOJI} Effective risk {sizing['effective_risk_pct']}% exceeds 10% with {leverage}x leverage")

    # Liquidity context validation (optional — if Coinglass data provided)
    liq_ctx = data.get("liquidity_context")
    if liq_ctx:
        # Check if stop sits on a liquidation cluster (stop-hunt risk)
        liq_clusters = liq_ctx.get("clusters", [])
        for cluster in liq_clusters:
            c_price = cluster.get("price", 0)
            c_usd = cluster.get("total_usd", 0)
            if c_price > 0 and c_usd > 100_000:
                dist_to_stop = abs(c_price - stop) / stop * 100
                if dist_to_stop <= 1.0:
                    warnings.append(f"{WARNING_EMOJI} Stop-hunt risk: liquidation cluster ({format_currency(c_usd)}) at {format_price(c_price)} is within {dist_to_stop:.1f}% of stop")

        # Check for large limit walls near entry/stop as confirmation
        bid_walls = liq_ctx.get("bid_walls", [])
        ask_walls = liq_ctx.get("ask_walls", [])
        for wall in bid_walls:
            w_price = wall.get("price", 0)
            w_usd = wall.get("amount_usd", 0)
            if w_price > 0 and w_usd > 100_000:
                dist_to_entry = abs(w_price - entry) / entry * 100
                if dist_to_entry <= 1.5 and direction == "LONG":
                    warnings.append(f"{CHECK_EMOJI} Bid wall {format_currency(w_usd)} at {format_price(w_price)} confirms entry support")
        for wall in ask_walls:
            w_price = wall.get("price", 0)
            w_usd = wall.get("amount_usd", 0)
            if w_price > 0 and w_usd > 100_000:
                dist_to_entry = abs(w_price - entry) / entry * 100
                if dist_to_entry <= 1.5 and direction == "SHORT":
                    warnings.append(f"{CHECK_EMOJI} Ask wall {format_currency(w_usd)} at {format_price(w_price)} confirms entry resistance")

    # Calculate RR for each target
    target_rrs = [calculate_rr(entry, stop, t, direction) for t in targets]

    # Calculate gain % for each target
    if direction == "LONG":
        target_gains = [((t - entry) / entry) * 100 for t in targets]
        risk_pct_price = ((entry - stop) / entry) * 100
    else:
        target_gains = [((entry - t) / entry) * 100 for t in targets]
        risk_pct_price = ((stop - entry) / entry) * 100

    # Scale out calculations
    scale_units = calculate_scale_out(sizing["position_units"], scale_out)
    scale_pnls = [calculate_pnl_at_target(entry, targets[i], scale_units[i], direction)
                  for i in range(len(targets))]

    # ========== FORMAT OUTPUT ==========

    # Header
    dir_emoji = "\U0001F7E2" if direction == "LONG" else "\U0001F534"  # Green/Red circle
    lines.append(f"# {TARGET_EMOJI} Target Package: {token} {dir_emoji} {direction}")
    lines.append("")

    # Warnings section
    if warnings:
        lines.append("## Warnings")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    # Setup Summary
    lines.append("## Setup Summary")
    lines.append(f"**Entry:** {format_price(entry)} | **Stop:** {format_price(stop)} | **Risk:** {format_percent(-abs(risk_pct_price))}")
    lines.append("")

    # Targets & RR Table
    lines.append("## Targets & RR")
    lines.append("")
    lines.append("| Target | Price | Gain | RR | Scale Out |")
    lines.append("|--------|-------|------|-----|-----------|")

    target_labels = ["T1", "T2", "T3"]
    for i, (label, price, gain, rr, pct) in enumerate(zip(
        target_labels, targets, target_gains, target_rrs, scale_out
    )):
        lines.append(f"| {label} | {format_price(price)} | {format_percent(gain)} | {rr}R | {int(pct*100)}% |")

    lines.append("")

    # Position Sizing
    lines.append(f"## Position Sizing ({risk_pct}% Risk)")
    lines.append("")
    lines.append(f"**Account:** {format_currency(account)}")
    lines.append(f"**Risk Amount:** {format_currency(sizing['risk_amount'])} ({risk_pct}%)")
    lines.append(f"**Position Size:** {format_units(sizing['position_units'], token)} ({format_currency(sizing['position_usd'])})")

    if leverage > 1:
        lines.append(f"**Leverage:** {leverage}x")
        lines.append(f"**Margin Required:** {format_currency(sizing['margin_required'])}")
        lines.append(f"**Effective Risk:** {format_percent(sizing['effective_risk_pct'], include_sign=False)}")

    lines.append("")

    # Quick Reference
    lines.append("## Quick Reference")
    lines.append("")
    action = "BUY" if direction == "LONG" else "SELL"
    lines.append(f"**{action}:** {format_units(sizing['position_units'], token)} @ {format_price(entry)}")
    lines.append(f"**STOP:** {format_price(stop)} (-{format_currency(sizing['risk_amount'])})")

    for i, (label, price, units, pnl) in enumerate(zip(
        target_labels, targets, scale_units, scale_pnls
    )):
        close_action = "sell" if direction == "LONG" else "cover"
        lines.append(f"**{label}:** {format_price(price)} ({close_action} {format_units(units, token)}, +{format_currency(pnl)})")

    # Total potential profit
    total_pnl = sum(scale_pnls)
    lines.append("")
    lines.append(f"**Max Profit (all targets):** +{format_currency(total_pnl)} ({format_percent(target_gains[2])})")

    # Notes
    if notes:
        lines.append("")
        lines.append("## Notes")
        lines.append(notes)

    lines.append("")
    lines.append("---")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    return "\n".join(lines)


def format_mini_package(data: Dict[str, Any]) -> str:
    """
    Format a condensed target package (for lists/summaries).

    Returns single line summary.
    """
    token = data.get("token", "UNKNOWN").upper()
    direction = data.get("direction", "LONG").upper()
    entry = data.get("entry", 0)
    stop = data.get("stop", 0)
    targets = data.get("targets", [])

    dir_emoji = "\U0001F7E2" if direction == "LONG" else "\U0001F534"
    t3 = targets[2] if len(targets) > 2 else 0
    rr = calculate_rr(entry, stop, t3, direction)

    return f"{dir_emoji} **{token}** {direction} @ {format_price(entry)} | Stop: {format_price(stop)} | T3: {format_price(t3)} ({rr}R)"


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI for testing target package formatting."""
    if len(sys.argv) < 2:
        # Demo with sample data
        sample = {
            "token": "ETH",
            "direction": "LONG",
            "account": 50000,
            "entry": 3450,
            "stop": 3300,
            "targets": [3600, 3800, 4200],
            "risk_pct": 2.0,
            "leverage": 1.0,
            "rank": 2,
        }
        print(format_target_package(sample))
        print("\n" + "="*50 + "\n")
        print("Mini format:")
        print(format_mini_package(sample))
    else:
        # Parse JSON from argument
        try:
            data = json.loads(sys.argv[1])
            print(format_target_package(data))
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
