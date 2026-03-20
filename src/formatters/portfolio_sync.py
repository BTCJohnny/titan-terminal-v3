#!/usr/bin/env python3
"""
Portfolio Sync Formatter
========================
Formats CoinStats portfolio data into my-trading/portfolio.md.

Usage:
    python3 src/formatters/portfolio_sync.py '{"result": [...]}'
    python3 src/formatters/portfolio_sync.py --file response.json
    python3 src/formatters/portfolio_sync.py --dry-run '{"result": [...]}'

Flags:
    --dry-run    Print formatted output without writing to file
    --file       Read JSON from file instead of CLI argument
"""

import json
import sys
import re
import argparse
from datetime import datetime
from pathlib import Path

PORTFOLIO_PATH = Path(__file__).parent.parent.parent / "my-trading" / "portfolio.md"

# ============================================================================
# CHAIN DETECTION
# ============================================================================

CHAIN_MAP = {
    "ethereum": "Ethereum",
    "bitcoin": "Bitcoin",
    "binance-coin": "BSC",
    "solana": "Solana",
    "usd-coin": "Ethereum",
    "aave-v3-weth": "Base (Aave)",
}

CHAIN_SUFFIXES = {
    "_ethereum": "Ethereum",
    "_bsc": "BSC",
    "_solana": "Solana",
    "_base": "Base",
    "_arbitrum": "Arbitrum",
    "_polygon": "Polygon",
    "_optimism": "Optimism",
    "_avalanche": "Avalanche",
}


def detect_chain(identifier: str) -> str:
    if identifier in CHAIN_MAP:
        return CHAIN_MAP[identifier]
    if "binance-bridged-usdt" in identifier:
        return "BSC"
    if "binance-bridged-usdc" in identifier:
        return "BSC"
    for suffix, chain in CHAIN_SUFFIXES.items():
        if identifier.endswith(suffix):
            return chain
    return identifier


# ============================================================================
# CLASSIFICATION
# ============================================================================

def classify(symbol: str, identifier: str) -> str:
    stables = {"USDC", "USDT", "BSC-USD", "DAI", "BUSD"}
    if symbol in stables or "bridged-usdt" in identifier or "bridged-usdc" in identifier:
        return "stablecoin"
    if symbol in {"BTC", "WBTC"}:
        return "btc"
    if symbol in {"ETH", "WETH", "STETH", "AWETH"} or "weth" in identifier.lower():
        return "eth"
    if symbol == "BNB":
        return "bnb"
    return "altcoin"


def verdict(pnl_pct: float) -> str:
    if pnl_pct >= 50:
        return "🚀 Ripping"
    if pnl_pct >= 10:
        return "🟢 Strong"
    if pnl_pct >= 0:
        return "🟢 Green"
    if pnl_pct >= -10:
        return "🟡 Dipping"
    if pnl_pct >= -30:
        return "🔴 Underwater"
    if pnl_pct >= -80:
        return "🔴 Deep Red"
    return "💀 Dead"


# ============================================================================
# NUMBER FORMATTING
# ============================================================================

def fmt_amount(value: float, is_stablecoin: bool = False) -> str:
    if is_stablecoin or value >= 1000:
        return f"{value:,.0f}" if value == int(value) or is_stablecoin else f"{value:,.0f}"
    if value >= 1:
        return f"{value:,.2f}"
    return f"{value:,.6f}"


def fmt_price(value: float) -> str:
    if value >= 1:
        return f"${value:,.2f}"
    if value >= 0.01:
        return f"${value:.4f}"
    return f"${value:.6f}"


def fmt_pnl_pct(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.1f}%"


def fmt_value(value: float) -> str:
    return f"${value:,.0f}"


# ============================================================================
# PARSE HOLDINGS
# ============================================================================

def parse_holdings(data: dict) -> list:
    items = data.get("result", [])
    holdings = []

    for item in items:
        try:
            coin = item.get("coin", {})
            symbol = coin.get("symbol", "???")
            name = coin.get("name", symbol)
            identifier = coin.get("identifier", "")
            rank = coin.get("rank")
            count = item.get("count", 0)
            price = item.get("price", {}).get("USD", 0)
            value = count * price

            avg_buy = item.get("averageBuy", {})
            avg_cost = avg_buy.get("unrealized", {}).get("USD")
            if avg_cost is None:
                avg_cost = avg_buy.get("allTime", {}).get("USD", 0)

            pnl_pct = item.get("profitPercent", {}).get("unrealized", {}).get("USD", 0)
            pnl_usd = item.get("profit", {}).get("unrealized", {}).get("USD", 0)

            chain = detect_chain(identifier)
            category = classify(symbol, identifier)
            is_stable = category == "stablecoin"

            holdings.append({
                "symbol": symbol,
                "name": name,
                "identifier": identifier,
                "rank": rank,
                "count": count,
                "price": price,
                "value": value,
                "avg_cost": avg_cost,
                "pnl_pct": pnl_pct,
                "pnl_usd": pnl_usd,
                "chain": chain,
                "category": category,
                "is_stable": is_stable,
            })
        except Exception as e:
            print(f"Warning: skipping holding — {e}", file=sys.stderr)
            continue

    holdings.sort(key=lambda h: h["value"], reverse=True)
    return holdings


# ============================================================================
# CHANGE DETECTION
# ============================================================================

def parse_old_portfolio(path: Path) -> tuple:
    """Parse existing portfolio.md to extract old holdings and last sync date.
    Returns (dict of symbol -> amount, previous_date_str)."""
    if not path.exists():
        return None, None

    try:
        text = path.read_text()
    except Exception:
        return None, None

    old_holdings = {}
    previous_date = None

    # Extract date from "Last Updated:" line
    date_match = re.search(r"\*\*Last Updated:\*\*\s*(.+?)\s*—", text)
    if date_match:
        previous_date = date_match.group(1).strip()

    # Parse Holdings table rows
    in_holdings = False
    for line in text.splitlines():
        if "| Ticker" in line and "Amount" in line:
            in_holdings = True
            continue
        if in_holdings and line.startswith("|:"):
            continue  # separator row
        if in_holdings and line.startswith("|"):
            cols = [c.strip() for c in line.split("|")]
            # cols[0] is empty (before first |), cols[1] is Ticker, cols[2] is Amount
            if len(cols) >= 3:
                ticker = cols[1].strip()
                amount_str = cols[2].strip().replace(",", "")
                try:
                    amount = float(amount_str)
                    old_holdings[ticker] = amount
                except ValueError:
                    pass
        elif in_holdings and line.startswith("---"):
            break
        elif in_holdings and not line.startswith("|"):
            break

    if not old_holdings:
        return None, previous_date

    return old_holdings, previous_date


def detect_changes(old_holdings: dict, new_holdings: list, previous_date: str) -> list:
    """Compare old vs new holdings and return list of change dicts."""
    if old_holdings is None:
        return []

    changes = []
    new_map = {h["symbol"]: h for h in new_holdings}
    old_symbols = set(old_holdings.keys())
    new_symbols = set(new_map.keys())

    # New positions
    for sym in sorted(new_symbols - old_symbols):
        h = new_map[sym]
        changes.append({
            "action": "🟢 NEW",
            "details": f"{sym} — {fmt_amount(h['count'])} tokens ({fmt_value(h['value'])})",
        })

    # Exited positions
    for sym in sorted(old_symbols - new_symbols):
        old_amt = old_holdings[sym]
        changes.append({
            "action": "🔴 EXITED",
            "details": f"{sym} — was {fmt_amount(old_amt)} tokens",
        })

    # Changed amounts
    for sym in sorted(old_symbols & new_symbols):
        old_amt = old_holdings[sym]
        new_amt = new_map[sym]["count"]
        h = new_map[sym]

        if old_amt == 0:
            continue

        pct_change = abs(new_amt - old_amt) / old_amt
        if pct_change < 0.01:
            continue

        if h["is_stable"]:
            old_val = old_amt  # stablecoins: amount ≈ value
            new_val = new_amt
            if new_val > old_val * 1.01:
                changes.append({
                    "action": "💵 STABLES",
                    "details": f"{sym} grew from {fmt_value(old_val)} → {fmt_value(new_val)}",
                })
            elif new_val < old_val * 0.99:
                changes.append({
                    "action": "💵 STABLES",
                    "details": f"{sym} decreased from {fmt_value(old_val)} → {fmt_value(new_val)}",
                })
        else:
            if new_amt > old_amt:
                changes.append({
                    "action": "🟢 BOUGHT",
                    "details": f"{sym} — {fmt_amount(old_amt)} → {fmt_amount(new_amt)}",
                })
            else:
                changes.append({
                    "action": "🔴 SOLD",
                    "details": f"{sym} — {fmt_amount(old_amt)} → {fmt_amount(new_amt)}",
                })

    return changes


# ============================================================================
# MARKDOWN GENERATION
# ============================================================================

def build_category_rows(holdings: list, total_value: float) -> list:
    """Build Position Breakdown rows grouped by category."""
    groups = {}
    for h in holdings:
        cat = h["category"]
        if cat not in groups:
            groups[cat] = {"symbols": [], "value": 0}
        groups[cat]["symbols"].append(h["symbol"])
        groups[cat]["value"] += h["value"]

    rows = []

    # Stablecoins first
    if "stablecoin" in groups:
        g = groups["stablecoin"]
        label = "💵 Stablecoins (" + " + ".join(g["symbols"]) + ")"
        pct = (g["value"] / total_value * 100) if total_value else 0
        rows.append(f"| {label} | {fmt_value(g['value'])} | {pct:.1f}% |")

    # ETH
    if "eth" in groups:
        g = groups["eth"]
        label = "🔵 " + " + ".join(g["symbols"])
        pct = (g["value"] / total_value * 100) if total_value else 0
        rows.append(f"| {label} | {fmt_value(g['value'])} | {pct:.1f}% |")

    # BTC
    if "btc" in groups:
        g = groups["btc"]
        label = "🟠 " + " + ".join(g["symbols"])
        pct = (g["value"] / total_value * 100) if total_value else 0
        rows.append(f"| {label} | {fmt_value(g['value'])} | {pct:.1f}% |")

    # BNB
    if "bnb" in groups:
        g = groups["bnb"]
        label = "🟡 BNB"
        pct = (g["value"] / total_value * 100) if total_value else 0
        rows.append(f"| {label} | {fmt_value(g['value'])} | {pct:.1f}% |")

    # Altcoins — each separately
    if "altcoin" in groups:
        for h in holdings:
            if h["category"] == "altcoin":
                pct = (h["value"] / total_value * 100) if total_value else 0
                if pct >= 1:
                    label = f"🤖 {h['symbol']}"
                else:
                    label = f"🧪 Other ({h['symbol']})"
                rows.append(f"| {label} | {fmt_value(h['value'])} | {pct:.1f}% |")

    return rows


def format_portfolio(holdings: list, changes: list, previous_date: str) -> str:
    now = datetime.now()
    date_str = now.strftime("%B %d, %Y").replace(" 0", " ")

    total_value = sum(h["value"] for h in holdings)
    active = [h for h in holdings if not h["is_stable"]]
    total_pnl = sum(h["pnl_usd"] for h in active)
    num_positions = len(active)

    lines = []

    # Header
    lines.append("# 💼 TITAN PORTFOLIO LEDGER")
    lines.append("")
    lines.append(f"**Last Updated:** {date_str} — Titan Sync")
    lines.append("**Wallet:** `0xc35...df53`")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Holdings table
    lines.append("## Holdings")
    lines.append("")
    lines.append("| Ticker | Amount | Chain | Avg Cost | Current Price | PnL (%) | Value ($) |")
    lines.append("|:-------|-------:|:------|----------:|--------------:|--------:|----------:|")

    for h in holdings:
        amt_str = fmt_amount(h["count"], h["is_stable"])
        avg_str = fmt_price(h["avg_cost"]) if h["avg_cost"] else "N/A"
        price_str = fmt_price(h["price"])
        pnl_str = fmt_pnl_pct(h["pnl_pct"])
        val_str = fmt_value(h["value"])
        lines.append(f"| {h['symbol']} | {amt_str} | {h['chain']} | {avg_str} | {price_str} | {pnl_str} | {val_str} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"**Total Portfolio Value:** {fmt_value(total_value)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Position Breakdown
    lines.append("## Position Breakdown")
    lines.append("")
    lines.append("| Category | Value | % of Portfolio |")
    lines.append("|:---------|------:|---------------:|")
    for row in build_category_rows(holdings, total_value):
        lines.append(row)
    lines.append("")
    lines.append("---")
    lines.append("")

    # Active Positions
    lines.append("## Active Positions (with Entry Data)")
    lines.append("")
    lines.append("| Ticker | Entry | Current | PnL ($) | PnL (%) | Verdict |")
    lines.append("|:-------|------:|--------:|--------:|--------:|:--------|")

    for h in active:
        entry_str = fmt_price(h["avg_cost"]) if h["avg_cost"] else "N/A"
        price_str = fmt_price(h["price"])
        pnl_sign = "+" if h["pnl_usd"] >= 0 else ""
        pnl_dollar = f"{pnl_sign}{fmt_value(h['pnl_usd'])}"
        # Fix: fmt_value adds $, but we need sign before $
        if h["pnl_usd"] < 0:
            pnl_dollar = f"-{fmt_value(abs(h['pnl_usd']))}"
        else:
            pnl_dollar = f"+{fmt_value(h['pnl_usd'])}"
        pnl_str = fmt_pnl_pct(h["pnl_pct"])
        v = verdict(h["pnl_pct"])
        lines.append(f"| {h['symbol']} | {entry_str} | {price_str} | {pnl_dollar} | {pnl_str} | {v} |")

    lines.append("")
    pnl_sign = "+" if total_pnl >= 0 else "-"
    lines.append(f"**Net Unrealized PnL (Active Positions):** {pnl_sign}{fmt_value(abs(total_pnl))}")
    lines.append("")
    lines.append("---")

    # Changes section
    if changes:
        lines.append("")
        lines.append(f"## Changes Since Last Sync ({previous_date or 'unknown'})")
        lines.append("")
        lines.append("| Action | Details |")
        lines.append("|:-------|:--------|")
        for c in changes:
            lines.append(f"| {c['action']} | {c['details']} |")
        lines.append("")
        lines.append("---")

    lines.append("")
    lines.append("*Sync via CoinStats API — Share Token NL3S076anq11Ibz*")

    return "\n".join(lines)


# ============================================================================
# SUMMARY
# ============================================================================

def build_summary(holdings: list, changes: list) -> str:
    now = datetime.now()
    date_str = now.strftime("%B %d, %Y").replace(" 0", " ")

    total_value = sum(h["value"] for h in holdings)
    active = [h for h in holdings if not h["is_stable"]]
    num_positions = len(active)
    total_pnl = sum(h["pnl_usd"] for h in active)
    total_cost = sum(h["avg_cost"] * h["count"] for h in active if h["avg_cost"])
    pnl_pct = (total_pnl / total_cost * 100) if total_cost else 0

    sign = "+" if total_pnl >= 0 else ""
    summary = f"Portfolio synced — {date_str}\n"
    summary += f"Total: {fmt_value(total_value)} | Positions: {num_positions} | PnL: {sign}{fmt_value(total_pnl)} ({sign}{pnl_pct:.1f}%)"

    if changes:
        new_items = [c for c in changes if "NEW" in c["action"]]
        exited = [c for c in changes if "EXITED" in c["action"]]
        parts = []
        if new_items:
            syms = [c["details"].split(" —")[0] for c in new_items]
            parts.append(f"+{len(new_items)} new ({', '.join(syms)})")
        if exited:
            syms = [c["details"].split(" —")[0] for c in exited]
            parts.append(f"-{len(exited)} exited ({', '.join(syms)})")
        bought = [c for c in changes if "BOUGHT" in c["action"]]
        sold = [c for c in changes if "SOLD" in c["action"]]
        if bought:
            parts.append(f"{len(bought)} increased")
        if sold:
            parts.append(f"{len(sold)} decreased")
        if parts:
            summary += f"\nChanges: {', '.join(parts)}"
    else:
        summary += "\nNo changes detected"

    return summary


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Portfolio Sync Formatter")
    parser.add_argument("json_data", nargs="?", help="JSON string from CoinStats API")
    parser.add_argument("--file", help="Read JSON from file instead of CLI argument")
    parser.add_argument("--dry-run", action="store_true", help="Print output without writing to file")

    args = parser.parse_args()

    # Load JSON
    if args.file:
        try:
            raw = Path(args.file).read_text()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.json_data:
        raw = args.json_data
    else:
        print("Error: provide JSON as argument or use --file", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if "result" not in data:
        print("Error: JSON missing 'result' key", file=sys.stderr)
        sys.exit(1)

    # Parse holdings
    holdings = parse_holdings(data)
    if not holdings:
        print("Error: no valid holdings found in data", file=sys.stderr)
        sys.exit(1)

    # Change detection
    old_holdings, previous_date = parse_old_portfolio(PORTFOLIO_PATH)
    if old_holdings is None:
        changes = []
        if not PORTFOLIO_PATH.exists():
            print("First sync — no previous portfolio found", file=sys.stderr)
        else:
            print("Previous format unrecognized — writing fresh", file=sys.stderr)
    else:
        changes = detect_changes(old_holdings, holdings, previous_date)

    # Format
    markdown = format_portfolio(holdings, changes, previous_date)

    if args.dry_run:
        print(markdown)
    else:
        PORTFOLIO_PATH.parent.mkdir(parents=True, exist_ok=True)
        PORTFOLIO_PATH.write_text(markdown + "\n")
        print(build_summary(holdings, changes))


if __name__ == "__main__":
    main()
