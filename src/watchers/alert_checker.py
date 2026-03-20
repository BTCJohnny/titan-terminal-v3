#!/usr/bin/env python3
"""
Alert Checker
=============
Checks price alerts against current prices and reports status.

Usage:
    python3 src/watchers/alert_checker.py '{"BNB": 667.94, "ZRO": 2.17}'
    python3 src/watchers/alert_checker.py --update '{"BNB": 667.94, "ZRO": 2.17}'
    python3 src/watchers/alert_checker.py --file prices.json
    python3 src/watchers/alert_checker.py --file prices.json --update

Flags:
    --update    Rewrite alerts.md with updated statuses + move triggered to history
    --file      Read prices JSON from file instead of CLI argument
"""

import json
import sys
import re
import argparse
from datetime import datetime, date
from pathlib import Path

ALERTS_PATH = Path(__file__).parent.parent.parent / "my-trading" / "alerts.md"

# ============================================================================
# PARSING
# ============================================================================

def parse_table_rows(lines: list[str]) -> list[list[str]]:
    """Parse markdown table rows into lists of cell values. Skips header and separator."""
    rows = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        # split produces empty strings at start/end from leading/trailing |
        cells = cells[1:-1] if len(cells) > 2 else cells
        # Skip separator rows (|:---|:---|)
        if cells and all(re.match(r'^[-:\s]+$', c) for c in cells):
            continue
        if cells:
            rows.append(cells)
    return rows


def parse_active_alerts(content: str) -> list[dict]:
    """Parse the Active Alerts table from alerts.md."""
    alerts = []
    in_section = False
    header_found = False
    table_lines = []

    for line in content.split("\n"):
        if line.strip().startswith("## Active Alerts"):
            in_section = True
            continue
        if in_section and line.strip().startswith("## "):
            break
        if in_section and line.strip().startswith("---"):
            break
        if in_section:
            table_lines.append(line)

    rows = parse_table_rows(table_lines)
    for row in rows:
        # Skip the header row
        if row and row[0].lower() == "ticker":
            header_found = True
            continue
        if not header_found:
            continue
        if len(row) < 5:
            print(f"WARNING: Skipping malformed row: {row}", file=sys.stderr)
            continue
        try:
            target_str = row[2].replace("$", "").replace(",", "").strip()
            target = float(target_str)
        except ValueError:
            print(f"WARNING: Can't parse target price '{row[2]}' for {row[0]}", file=sys.stderr)
            continue

        alerts.append({
            "ticker": row[0].strip(),
            "direction": row[1].strip(),
            "target": target,
            "note": row[3].strip(),
            "status": row[4].strip(),
        })

    return alerts


def parse_daily_reminders(content: str) -> dict[str, dict]:
    """Parse Daily Check Reminders table. Returns {token: {setup_id, added, ...}}."""
    reminders = {}
    in_section = False
    header_found = False
    table_lines = []

    for line in content.split("\n"):
        if line.strip().startswith("## Daily Check Reminders"):
            in_section = True
            continue
        if in_section and line.strip().startswith("## "):
            break
        if in_section and line.strip().startswith("---"):
            break
        if in_section:
            table_lines.append(line)

    rows = parse_table_rows(table_lines)
    for row in rows:
        if row and row[0].lower() == "token":
            header_found = True
            continue
        if not header_found:
            continue
        if len(row) < 5:
            continue
        token = row[0].strip()
        added_str = row[4].strip()
        try:
            added_date = datetime.strptime(added_str, "%Y-%m-%d").date()
        except ValueError:
            added_date = None
        reminders[token] = {
            "setup_id": row[1].strip(),
            "entry_zone": row[2].strip(),
            "frequency": row[3].strip(),
            "added": added_date,
        }

    return reminders


def parse_triggered_history(content: str) -> list[dict]:
    """Parse existing Triggered History entries."""
    history = []
    in_section = False
    header_found = False
    table_lines = []

    for line in content.split("\n"):
        if line.strip().startswith("## Triggered History"):
            in_section = True
            continue
        if in_section and line.strip().startswith("## "):
            break
        if in_section and line.strip().startswith("---"):
            break
        if in_section:
            table_lines.append(line)

    rows = parse_table_rows(table_lines)
    for row in rows:
        if row and row[0].lower() == "ticker":
            header_found = True
            continue
        if not header_found:
            continue
        if len(row) < 5:
            continue
        history.append({
            "ticker": row[0].strip(),
            "direction": row[1].strip(),
            "target": row[2].strip(),
            "triggered_at": row[3].strip(),
            "date": row[4].strip(),
        })

    return history


# ============================================================================
# TRIGGER LOGIC
# ============================================================================

def check_trigger(direction: str, target: float, current: float) -> str:
    """
    Returns: 'TRIGGERED', 'APPROACHING', or 'ACTIVE'

    Direction-specific trigger conditions:
    - BUY: price drops to/below target (buying the dip)
    - SELL: price rises to/above target (take profit)
    - BREAKOUT: price rises above target
    - SHORT ENTRY: price rises to/above target (enter short at resistance)
    - STOP: price rises above target (stop loss for shorts)
    - T1/T2/T3: price drops to/below target (short profit targets)
    - INVALIDATE: price rises above target (thesis broken)
    """
    triggers_below = {"BUY", "T1", "T2", "T3"}
    triggers_above = {"SELL", "BREAKOUT", "SHORT ENTRY", "STOP", "INVALIDATE"}

    if direction in triggers_below:
        triggered = current <= target
    elif direction in triggers_above:
        triggered = current >= target
    else:
        triggered = False

    if triggered:
        return "TRIGGERED"

    distance_pct = abs(current - target) / target * 100 if target != 0 else 999
    if distance_pct <= 5.0:
        return "APPROACHING"

    return "ACTIVE"


# ============================================================================
# STALENESS DETECTION
# ============================================================================

ENTRY_DIRECTIONS = {"BUY", "BREAKOUT", "SHORT ENTRY"}

def detect_stale_alerts(alerts: list[dict], reminders: dict[str, dict], today: date) -> dict[str, dict]:
    """
    Returns {ticker: {stale: bool, days: int, reason: str}} for tokens in reminders.

    A token's alerts are stale if:
    - Added >21 days ago
    - No alerts triggered
    - For multi-alert setups: only stale if the ENTRY alert itself is stale
    """
    stale_info = {}
    stale_threshold = 21

    for token, info in reminders.items():
        if info["added"] is None:
            stale_info[token] = {"stale": False, "days": None, "reason": "Unknown added date"}
            continue

        days_old = (today - info["added"]).days
        if days_old <= stale_threshold:
            continue

        # Get all alerts for this token
        token_alerts = [a for a in alerts if a["ticker"] == token]

        # Check if any alert is already triggered
        any_triggered = any("TRIGGERED" in a["status"].upper() for a in token_alerts)
        if any_triggered:
            continue

        # For multi-alert setups (has non-entry alerts like STOP, T1, etc.)
        entry_alerts = [a for a in token_alerts if a["direction"] in ENTRY_DIRECTIONS]
        non_entry_alerts = [a for a in token_alerts if a["direction"] not in ENTRY_DIRECTIONS]

        if non_entry_alerts and entry_alerts:
            # Multi-alert setup — only stale if entry is pending (not triggered)
            entry_triggered = any("TRIGGERED" in a["status"].upper() for a in entry_alerts)
            if entry_triggered:
                # Entry was hit, non-entry alerts are part of active trade — not stale
                continue

        stale_info[token] = {
            "stale": True,
            "days": days_old,
            "reason": f"Added {info['added'].isoformat()} ({days_old} days ago)",
        }

    return stale_info


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report(alerts: list[dict], prices: dict[str, float],
                    reminders: dict[str, dict], today: date) -> dict:
    """Generate the alert check report. Returns structured results."""
    triggered = []
    approaching = []
    active = []
    no_price = []
    already_triggered = []

    for alert in alerts:
        ticker = alert["ticker"]

        # Skip already-triggered alerts
        if "TRIGGERED" in alert["status"].upper():
            already_triggered.append(alert)
            continue

        if ticker not in prices:
            no_price.append(alert)
            continue

        current = prices[ticker]
        status = check_trigger(alert["direction"], alert["target"], current)

        distance_pct = abs(current - alert["target"]) / alert["target"] * 100 if alert["target"] != 0 else 0
        # Determine if current is above or below target
        if current >= alert["target"]:
            direction_str = f"+{distance_pct:.1f}% past target"
        else:
            direction_str = f"{distance_pct:.1f}% away"

        result = {
            **alert,
            "current": current,
            "status_check": status,
            "distance_pct": distance_pct,
            "distance_str": direction_str,
        }

        if status == "TRIGGERED":
            triggered.append(result)
        elif status == "APPROACHING":
            approaching.append(result)
        else:
            active.append(result)

    stale = detect_stale_alerts(alerts, reminders, today)

    # Unique tokens in alerts
    all_tickers = set(a["ticker"] for a in alerts if "TRIGGERED" not in a["status"].upper())
    no_price_tickers = set(a["ticker"] for a in no_price)

    return {
        "triggered": triggered,
        "approaching": approaching,
        "active": active,
        "no_price": no_price,
        "no_price_tickers": no_price_tickers,
        "already_triggered": already_triggered,
        "stale": stale,
        "total_tickers": len(all_tickers),
        "priced_tickers": len(all_tickers - no_price_tickers),
    }


def format_report(results: dict, today: date) -> str:
    """Format the report as a readable string."""
    lines = []
    lines.append(f"ALERT CHECK — {today.strftime('%B %d, %Y')}")
    lines.append(f"Prices provided for {results['priced_tickers']}/{results['total_tickers']} tokens")
    lines.append("")

    if results["triggered"]:
        lines.append(f"🔴 TRIGGERED ({len(results['triggered'])}):")
        for r in results["triggered"]:
            lines.append(f"  {r['ticker']} {r['direction']} ${r['target']:,.2f} — current ${r['current']:,.2f} ({r['distance_str']})")
        lines.append("")

    if results["approaching"]:
        lines.append(f"🟡 APPROACHING ({len(results['approaching'])}):")
        for r in results["approaching"]:
            lines.append(f"  {r['ticker']} {r['direction']} ${r['target']:,.2f} — current ${r['current']:,.2f} ({r['distance_str']})")
        lines.append("")

    if results["active"]:
        lines.append(f"🟢 ACTIVE ({len(results['active'])}):")
        for r in results["active"]:
            lines.append(f"  {r['ticker']} {r['direction']} ${r['target']:,.2f} — current ${r['current']:,.2f} ({r['distance_str']})")
        lines.append("")

    if results["no_price_tickers"]:
        lines.append(f"⚠️ NO PRICE DATA ({len(results['no_price_tickers'])}):")
        lines.append(f"  {', '.join(sorted(results['no_price_tickers']))}")
        lines.append("")

    if results["already_triggered"]:
        lines.append(f"✅ ALREADY TRIGGERED ({len(results['already_triggered'])}):")
        for r in results["already_triggered"]:
            lines.append(f"  {r['ticker']} {r['direction']} ${r['target']:,.2f} — {r['status']}")
        lines.append("")

    stale_items = {k: v for k, v in results["stale"].items() if v.get("stale")}
    if stale_items:
        lines.append(f"⏰ STALE (>{21} days without trigger):")
        for token, info in stale_items.items():
            if info["days"] is not None:
                lines.append(f"  {token} — added {info['days']} days ago. Review or remove.")
            else:
                lines.append(f"  {token} — added unknown. Review or remove.")
        lines.append("")

    # Summary line
    counts = []
    counts.append(f"{len(results['triggered'])} triggered")
    counts.append(f"{len(results['approaching'])} approaching")
    counts.append(f"{len(results['active'])} active")
    if results["no_price_tickers"]:
        counts.append(f"{len(results['no_price_tickers'])} no data")
    if stale_items:
        counts.append(f"{len(stale_items)} stale")
    lines.append(f"Summary: {', '.join(counts)}")

    return "\n".join(lines)


# ============================================================================
# FILE UPDATE
# ============================================================================

def format_price(price: float) -> str:
    """Format price for display — no trailing zeros, sensible precision."""
    if price >= 100:
        return f"${price:,.2f}"
    elif price >= 1:
        return f"${price:.2f}"
    elif price >= 0.01:
        return f"${price:.4f}"
    else:
        return f"${price:.6f}"


def rewrite_alerts_file(content: str, alerts: list[dict], results: dict,
                        history: list[dict], today: date) -> str:
    """Rewrite alerts.md with updated statuses."""
    today_str = today.strftime("%B %d, %Y")
    today_short = today.strftime("%b %d")

    # Build lookup of check results by (ticker, direction, target)
    result_lookup = {}
    for category in ["triggered", "approaching", "active"]:
        for r in results[category]:
            key = (r["ticker"], r["direction"], r["target"])
            result_lookup[key] = r

    stale_info = results["stale"]

    # Separate alerts into still-active and newly-triggered
    new_active_alerts = []
    new_history_entries = []

    for alert in alerts:
        key = (alert["ticker"], alert["direction"], alert["target"])

        # Already triggered before this check — keep as-is in active table
        if "TRIGGERED" in alert["status"].upper():
            # Move to history if not already there
            new_history_entries.append({
                "ticker": alert["ticker"],
                "direction": alert["direction"],
                "target": format_price(alert["target"]),
                "triggered_at": alert["status"],  # preserve original status text
                "date": today.isoformat(),
            })
            continue

        r = result_lookup.get(key)
        if r is None:
            # No price data — keep as-is, maybe flag stale
            ticker_stale = stale_info.get(alert["ticker"], {})
            if ticker_stale.get("stale"):
                alert["status"] = f"⏰ STALE ({ticker_stale['days']}d)"
            new_active_alerts.append(alert)
            continue

        if r["status_check"] == "TRIGGERED":
            # Move to history
            alert["status"] = f"✅ TRIGGERED ({today_short}, price at {format_price(r['current'])})"
            new_history_entries.append({
                "ticker": alert["ticker"],
                "direction": alert["direction"],
                "target": format_price(alert["target"]),
                "triggered_at": format_price(r["current"]),
                "date": today.isoformat(),
            })
        elif r["status_check"] == "APPROACHING":
            alert["status"] = f"🟡 Approaching ({format_price(r['current'])})"
            new_active_alerts.append(alert)
        else:
            # ACTIVE — reset to pending
            ticker_stale = stale_info.get(alert["ticker"], {})
            if ticker_stale.get("stale"):
                alert["status"] = f"⏰ STALE ({ticker_stale['days']}d)"
            else:
                alert["status"] = "⏳ Pending"
            new_active_alerts.append(alert)

    # Merge new history with existing history
    all_history = list(history) + new_history_entries

    # Reconstruct file
    lines = []
    lines.append("# 🔔 TITAN PRICE ALERTS")
    lines.append("")
    lines.append(f"**Last Updated:** {today_str}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Active Alerts")
    lines.append("")
    lines.append("| Ticker | Direction | Target Price | Note | Status |")
    lines.append("|:-------|:----------|-------------:|:-----|:-------|")
    for a in new_active_alerts:
        target_str = format_price(a["target"])
        lines.append(f"| {a['ticker']} | {a['direction']} | {target_str} | {a['note']} | {a['status']} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Preserve Daily Check Reminders section exactly
    reminders_section = extract_section(content, "## Daily Check Reminders")
    if reminders_section:
        lines.append(reminders_section.rstrip())
    else:
        lines.append("## Daily Check Reminders")
        lines.append("")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Triggered History
    lines.append("## Triggered History")
    lines.append("")
    lines.append("| Ticker | Direction | Target Price | Triggered At | Date |")
    lines.append("|:-------|:----------|-------------:|-------------:|:-----|")
    for h in all_history:
        lines.append(f"| {h['ticker']} | {h['direction']} | {h['target']} | {h['triggered_at']} | {h['date']} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Alerts are checked automatically during \"Titan Dashboard\"*")
    lines.append("")

    return "\n".join(lines)


def extract_section(content: str, header: str) -> str | None:
    """Extract a full section (header through end) from markdown content."""
    lines = content.split("\n")
    start = None
    end = None
    for i, line in enumerate(lines):
        if line.strip().startswith(header):
            start = i
            continue
        if start is not None and line.strip().startswith("---"):
            end = i
            break
        if start is not None and line.strip().startswith("## ") and i > start:
            end = i
            break

    if start is not None:
        if end is not None:
            return "\n".join(lines[start:end])
        return "\n".join(lines[start:])
    return None


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Check price alerts against current prices")
    parser.add_argument("prices", nargs="?", help="JSON string of {TOKEN: price, ...}")
    parser.add_argument("--update", action="store_true", help="Rewrite alerts.md with updated statuses")
    parser.add_argument("--file", help="Read prices JSON from file instead of CLI argument")
    args = parser.parse_args()

    # Load prices
    if args.file:
        try:
            prices = json.loads(Path(args.file).read_text())
        except Exception as e:
            print(f"ERROR: Failed to read prices file: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.prices:
        try:
            prices = json.loads(args.prices)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("ERROR: Provide prices as JSON argument or with --file", file=sys.stderr)
        sys.exit(1)

    # Normalize keys to uppercase
    prices = {k.upper(): v for k, v in prices.items()}

    # Read alerts file
    if not ALERTS_PATH.exists():
        print(f"No alerts file found at {ALERTS_PATH}", file=sys.stderr)
        sys.exit(1)

    content = ALERTS_PATH.read_text()
    today = date.today()

    # Parse
    alerts = parse_active_alerts(content)
    reminders = parse_daily_reminders(content)
    history = parse_triggered_history(content)

    if not alerts:
        print("No active alerts found in alerts.md")
        sys.exit(0)

    # Generate report
    results = generate_report(alerts, prices, reminders, today)
    report = format_report(results, today)
    print(report)

    # Update file if requested
    if args.update:
        try:
            new_content = rewrite_alerts_file(content, alerts, results, history, today)
            ALERTS_PATH.write_text(new_content)
            print(f"\n✅ alerts.md updated successfully")
        except Exception as e:
            print(f"\n❌ Failed to update alerts.md: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
