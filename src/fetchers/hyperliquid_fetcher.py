#!/usr/bin/env python3
"""
Hyperliquid Perps Fetcher
=========================
Fetches perps market data from the Hyperliquid public API for squeeze detection.
No API key required.

Endpoints used:
    POST https://api.hyperliquid.xyz/info
    - {"type": "metaAndAssetCtxs"} — funding rates, OI, mark price for all perps

Output: JSON to signals/dashboards/hl_perps_YYYYMMDD_HHMM.json
        Summary printed to stdout

Usage:
    python3 src/fetchers/hyperliquid_fetcher.py             # Fetch and save
    python3 src/fetchers/hyperliquid_fetcher.py --top 20    # Show top 20 by OI
    python3 src/fetchers/hyperliquid_fetcher.py --token BTC # Show specific token
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "signals" / "dashboards"
HL_API = "https://api.hyperliquid.xyz/info"

# Squeeze detection thresholds
IMBALANCE_THRESHOLD = 5.0   # 5:1 long/short ratio = extreme
FUNDING_EXTREME = 0.001     # 0.1% per 8h = extreme (annualizes to ~45%)

# TradFi derivative symbols on Hyperliquid
TRADFI_COINS = {
    "CL": "xyz:CL", "GOLD": "xyz:GOLD", "SILVER": "xyz:SILVER",
    "EUR": "xyz:EUR", "JPY": "xyz:JPY",
    "USA500": "cash:USA500", "SPX": "SPX",
}
TRADFI_LABELS = {
    "CL": "WTI Crude Oil", "GOLD": "Gold", "SILVER": "Silver",
    "EUR": "EUR/USD", "JPY": "JPY/USD",
    "USA500": "S&P 500", "SPX": "S&P 500 Direct",
}


def hl_post(payload: dict) -> dict | list | None:
    """POST to Hyperliquid info endpoint."""
    try:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            HL_API,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ⚠️  Hyperliquid API error: {e}", file=sys.stderr)
        return None


def fetch_perps_data() -> list[dict]:
    """
    Fetch all perps market data from Hyperliquid.

    Returns list of dicts with fields:
        symbol, mark_price, funding_rate, open_interest_usd,
        long_ratio, short_ratio, imbalance_ratio, squeeze_bias
    """
    data = hl_post({"type": "metaAndAssetCtxs"})
    if not data or not isinstance(data, list) or len(data) < 2:
        return []

    universe = data[0].get("universe", [])  # Asset metadata (name, szDecimals, etc.)
    asset_ctxs = data[1]                    # Live market data per asset

    results = []
    for i, ctx in enumerate(asset_ctxs):
        if i >= len(universe):
            break

        symbol = universe[i].get("name", f"ASSET_{i}")

        try:
            mark_price = float(ctx.get("markPx", 0) or 0)
            funding_rate = float(ctx.get("funding", 0) or 0)
            open_interest = float(ctx.get("openInterest", 0) or 0)  # In base asset units
            oi_usd = open_interest * mark_price

            # Hyperliquid provides premium (basis) but not long/short split directly.
            # Use funding rate as proxy: positive = long-heavy, negative = short-heavy.
            # We store the raw funding rate and derive bias.
            annualized_funding = funding_rate * 3 * 365  # 3 payments/day

            if funding_rate > FUNDING_EXTREME:
                squeeze_bias = "short"  # Longs paying heavily → short squeeze risk
                imbalance_ratio = min(abs(annualized_funding) / (FUNDING_EXTREME * 3 * 365) * 5, 99)
            elif funding_rate < -FUNDING_EXTREME:
                squeeze_bias = "long"   # Shorts paying heavily → long squeeze risk
                imbalance_ratio = min(abs(annualized_funding) / (FUNDING_EXTREME * 3 * 365) * 5, 99)
            else:
                squeeze_bias = "neutral"
                imbalance_ratio = 1.0

            results.append({
                "symbol": symbol,
                "mark_price": mark_price,
                "funding_rate": funding_rate,
                "funding_rate_pct": round(funding_rate * 100, 4),
                "annualized_funding_pct": round(annualized_funding * 100, 1),
                "open_interest_usd": round(oi_usd, 0),
                "imbalance_ratio": round(imbalance_ratio, 1),
                "squeeze_bias": squeeze_bias,
            })

        except (TypeError, ValueError):
            continue

    return results


def fetch_tradfi_mark_prices() -> list[dict]:
    """
    Fetch current mark prices for TradFi derivatives on Hyperliquid.
    Uses the latest 1m candle for each symbol to get the current price.
    """
    results = []
    for user_sym, hl_coin in TRADFI_COINS.items():
        now_ms = int(datetime.now().timestamp() * 1000)
        start_ms = now_ms - 120_000  # last 2 minutes

        payload = {
            "type": "candleSnapshot",
            "req": {
                "coin": hl_coin,
                "interval": "1m",
                "startTime": start_ms,
                "endTime": now_ms
            }
        }
        data = hl_post(payload)
        if data and isinstance(data, list) and len(data) > 0:
            latest = data[-1]
            results.append({
                "symbol": user_sym,
                "hl_coin": hl_coin,
                "label": TRADFI_LABELS.get(user_sym, user_sym),
                "mark_price": float(latest.get("c", 0)),
                "high": float(latest.get("h", 0)),
                "low": float(latest.get("l", 0)),
                "volume": float(latest.get("v", 0)),
            })
        else:
            results.append({
                "symbol": user_sym,
                "hl_coin": hl_coin,
                "label": TRADFI_LABELS.get(user_sym, user_sym),
                "mark_price": 0,
                "high": 0,
                "low": 0,
                "volume": 0,
                "error": "No data returned",
            })
    return results


def score_squeeze(token: dict) -> int:
    """
    Score squeeze potential 0-10.
    Higher = more extreme positioning imbalance.
    """
    score = 0
    funding = abs(token["funding_rate"])
    oi = token["open_interest_usd"]

    # Funding rate extremity (0-5 pts)
    if funding > FUNDING_EXTREME * 4:
        score += 5
    elif funding > FUNDING_EXTREME * 2:
        score += 3
    elif funding > FUNDING_EXTREME:
        score += 1

    # OI size — larger OI = more fuel for squeeze (0-3 pts)
    if oi > 100_000_000:
        score += 3
    elif oi > 10_000_000:
        score += 2
    elif oi > 1_000_000:
        score += 1

    # Direction consistency bonus (0-2 pts)
    if token["squeeze_bias"] != "neutral":
        score += 2

    return score


def format_usd(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value/1_000:.0f}K"
    return f"${value:.0f}"


def print_summary(tokens: list[dict], top_n: int = 15):
    """Print top squeeze candidates to stdout."""
    scored = [(score_squeeze(t), t) for t in tokens]
    scored.sort(key=lambda x: x[0], reverse=True)

    print(f"\n{'─' * 65}")
    print(f"  🔥 HYPERLIQUID PERPS — TOP SQUEEZE CANDIDATES ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print(f"{'─' * 65}")
    print(f"  {'Symbol':<10} {'Mark Px':>10} {'Funding/8h':>11} {'Ann%':>8} {'OI':>10} {'Bias':>8} {'Score':>6}")
    print(f"  {'─' * 63}")

    for score, t in scored[:top_n]:
        bias_icon = "📈" if t["squeeze_bias"] == "short" else "📉" if t["squeeze_bias"] == "long" else "  "
        print(
            f"  {t['symbol']:<10} "
            f"{t['mark_price']:>10,.4g} "
            f"{t['funding_rate_pct']:>+10.4f}% "
            f"{t['annualized_funding_pct']:>+7.1f}% "
            f"{format_usd(t['open_interest_usd']):>10} "
            f"{bias_icon} {t['squeeze_bias']:<6} "
            f"{score:>5}/10"
        )

    print(f"\n  Score 7+: extreme positioning. Score 5-6: elevated. Below 5: normal.")
    print(f"  Positive funding = longs heavy → short squeeze risk if price drops.")
    print(f"  Negative funding = shorts heavy → long squeeze risk if price pumps.")


def print_token(tokens: list[dict], symbol: str):
    """Print data for a specific token."""
    symbol = symbol.upper()
    match = next((t for t in tokens if t["symbol"] == symbol), None)
    if not match:
        print(f"  ⚠️  {symbol} not found in Hyperliquid perps data.")
        return

    score = score_squeeze(match)
    print(f"\n  {symbol} PERPS (Hyperliquid)")
    print(f"  {'─' * 40}")
    print(f"  Mark Price:       {match['mark_price']:,.4g}")
    print(f"  Funding (8h):     {match['funding_rate_pct']:+.4f}%")
    print(f"  Annualized:       {match['annualized_funding_pct']:+.1f}%")
    print(f"  Open Interest:    {format_usd(match['open_interest_usd'])}")
    print(f"  Squeeze Bias:     {match['squeeze_bias']}")
    print(f"  Squeeze Score:    {score}/10")


def save_data(tokens: list[dict]) -> str:
    """Save full perps data to JSON file."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    path = REPORTS_DIR / f"hl_perps_{timestamp}.json"

    output = {
        "fetched_at": datetime.now().isoformat(),
        "token_count": len(tokens),
        "tokens": tokens
    }

    with open(path, 'w') as f:
        json.dump(output, f, indent=2)

    return str(path)


def main():
    parser = argparse.ArgumentParser(description="Hyperliquid Perps Fetcher")
    parser.add_argument("--top", type=int, default=15, help="Show top N by squeeze score (default: 15)")
    parser.add_argument("--token", type=str, help="Show data for a specific token")
    parser.add_argument("--no-save", action="store_true", help="Don't save to file")
    parser.add_argument("--json", action="store_true", help="Output raw JSON to stdout")
    parser.add_argument("--tradfi", action="store_true", help="Include TradFi derivatives (commodities, forex, indices)")
    args = parser.parse_args()

    print(f"\n  Fetching Hyperliquid perps data...", end=" ", flush=True)
    tokens = fetch_perps_data()

    if not tokens:
        print("❌ Failed")
        sys.exit(1)

    print(f"✓ ({len(tokens)} perps)")

    if args.json:
        print(json.dumps(tokens, indent=2))
        return

    if args.token:
        print_token(tokens, args.token)
    else:
        print_summary(tokens, args.top)

    if args.tradfi:
        print(f"\n  Fetching TradFi mark prices...", end=" ", flush=True)
        tradfi = fetch_tradfi_mark_prices()
        live = [t for t in tradfi if t["mark_price"] > 0]
        print(f"✓ ({len(live)}/{len(tradfi)} assets)")
        print(f"\n{'─' * 55}")
        print(f"  📊 TRADFI DERIVATIVES (Hyperliquid)")
        print(f"{'─' * 55}")
        print(f"  {'Symbol':<10} {'Asset':<20} {'Price':>12}")
        print(f"  {'─' * 53}")
        for t in tradfi:
            if t["mark_price"] > 0:
                print(f"  {t['symbol']:<10} {t['label']:<20} {t['mark_price']:>12,.2f}")
            else:
                print(f"  {t['symbol']:<10} {t['label']:<20} {'No data':>12}")

    if not args.no_save:
        path = save_data(tokens)
        print(f"\n  💾 Saved to: {path}")


if __name__ == "__main__":
    main()
