#!/usr/bin/env python3
"""
CEX Flow Cron Monitor
=====================
Automated monitoring of CEX flows for BTC, ETH, USDT, USDC using direct Nansen API calls.

Produces enriched dashboards with per-segment smart money breakdowns,
narrative summaries, and delta-vs-prior comparisons.

Schedule: Every 12 hours at 0600 and 1800

Usage:
    python3 src/watchers/cex_monitor.py snapshot              # Fetch fresh data
    python3 src/watchers/cex_monitor.py snapshot --cron       # Cron mode (outputs to file)
    python3 src/watchers/cex_monitor.py status                # Show latest snapshot
    python3 src/watchers/cex_monitor.py alerts                # Check alerts only

API Usage: ~8 calls per check (4 flow summaries + 4 prices)
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import requests

# Add parent to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

NANSEN_API_KEY = os.getenv("NANSEN_API_KEY")
BASE_URL = "https://api.nansen.ai"

# Directories
DATA_FILE = PROJECT_ROOT / "data" / "cex_health.json"
REPORTS_DIR = PROJECT_ROOT / "signals" / "dashboards"
DB_FILE = PROJECT_ROOT / "data" / "titan_intelligence.db"

# Token configuration
TOKENS = {
    "ETH": {
        "address": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "chain": "ethereum",
        "proxy": "WETH"
    },
    "BTC": {
        "address": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
        "chain": "ethereum",
        "proxy": "WBTC"
    },
    "USDT": {
        "address": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "chain": "ethereum",
        "proxy": None
    },
    "USDC": {
        "address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "chain": "ethereum",
        "proxy": None
    }
}

STABLECOINS = {"USDT", "USDC"}

# Smart money segments from Nansen flow-intelligence API
SMART_MONEY_SEGMENTS = {
    "smart_trader": "Smart Traders",
    "whale": "Whales",
    "top_pnl": "Top PnL",
    "public_figure": "Public Figures",
    "fresh_wallet": "Fresh Wallets"
}

# Alert thresholds
ALERT_THRESHOLDS = {
    "large_flow_multiplier": 2.0,    # 2x average = notable
    "extreme_flow_multiplier": 4.0,  # 4x average = critical
    "smart_money_threshold": 10_000_000,  # $10M net = significant
    "watch_flow_multiplier": 1.3,    # 1.3x average = worth noting
}

# Flow signals
FLOW_SIGNALS = {
    "very_bullish": "🟢🟢",
    "bullish": "🟢",
    "neutral": "🟡",
    "slight_bearish": "🟠",
    "bearish": "🔴",
    "very_bearish": "🔴🔴"
}

SIGNAL_LABELS = {
    "very_bullish": "Very Bullish",
    "bullish": "Bullish",
    "neutral": "Neutral",
    "slight_bearish": "Mildly Bearish",
    "bearish": "Bearish",
    "very_bearish": "Very Bearish"
}


# ============================================================================
# NANSEN API FUNCTIONS
# ============================================================================

def get_headers() -> Dict[str, str]:
    """Get API headers for Nansen API v1."""
    if not NANSEN_API_KEY:
        raise ValueError("NANSEN_API_KEY not set in .env")
    return {
        "apiKey": NANSEN_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


def fetch_token_flows(chain: str, token_address: str, lookback: str = "1d") -> Optional[Dict]:
    """
    Fetch flow intelligence from Nansen API v1.

    Uses POST /api/v1/tgm/flow-intelligence endpoint.

    Args:
        chain: Blockchain (e.g., 'ethereum')
        token_address: Token contract address
        lookback: Lookback period ('5m', '1h', '6h', '12h', '1d', '7d')

    Returns:
        Flow intelligence dict or None on error
    """
    url = f"{BASE_URL}/api/v1/tgm/flow-intelligence"
    payload = {
        "chain": chain,
        "token_address": token_address,
        "timeframe": lookback
    }

    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️  Error fetching flows for {token_address}: {e}")
        return None


def fetch_token_price(chain: str, token_address: str, symbol: str = "") -> Optional[float]:
    """
    Fetch current price from Nansen token-information API.

    Uses POST /api/v1/tgm/token-information endpoint.
    """
    url = f"{BASE_URL}/api/v1/tgm/token-information"
    payload = {
        "chain": chain,
        "token_address": token_address,
        "timeframe": "1d"
    }

    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict):
            price = data.get("data", {}).get("price_usd") or \
                    data.get("data", {}).get("priceUsd") or \
                    data.get("price_usd") or \
                    data.get("priceUsd")
            if price:
                return float(price)

        return None
    except requests.exceptions.RequestException:
        return None


# ============================================================================
# DATA PARSING
# ============================================================================

def interpret_flow_signal(net_flow: float, vs_average: float, symbol: str = "") -> str:
    """
    Interpret flow signal based on direction, magnitude, and asset type.

    Stablecoin flows are inverted: inflow to exchange = bullish (buying power staged).
    Crypto flows: outflow from exchange = bullish (accumulation).
    """
    is_stable = symbol in STABLECOINS

    if is_stable:
        is_bullish = net_flow > 0  # Stablecoin inflow to exchange = buying power
    else:
        is_bullish = net_flow < 0  # Crypto outflow from exchange = accumulation

    if is_bullish:
        if vs_average >= ALERT_THRESHOLDS["extreme_flow_multiplier"]:
            return "very_bullish"
        elif vs_average >= ALERT_THRESHOLDS["large_flow_multiplier"]:
            return "bullish"
        else:
            return "neutral"
    else:
        if vs_average >= ALERT_THRESHOLDS["extreme_flow_multiplier"]:
            return "very_bearish"
        elif vs_average >= ALERT_THRESHOLDS["large_flow_multiplier"]:
            return "bearish"
        elif vs_average >= 1.5:
            return "slight_bearish"
        else:
            return "neutral"


def parse_exchange_flows(flows_data: Dict, symbol: str) -> Dict:
    """
    Parse exchange flow data from Nansen flow-intelligence API response.

    The API returns flat structure with fields like:
    - exchange_net_flow_usd, exchange_avg_flow_usd
    """
    if not flows_data:
        return {
            "net_flow_usd": 0,
            "direction": "unknown",
            "vs_average": 1.0,
            "signal": "neutral"
        }

    data = flows_data.get("data", [])
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
    elif not isinstance(data, dict):
        data = {}

    exchange_flow = data.get("exchange_net_flow_usd", 0) or 0
    avg_flow = abs(data.get("exchange_avg_flow_usd", 1) or 1)

    vs_average = abs(exchange_flow / avg_flow) if avg_flow != 0 else 1.0

    direction = "outflow" if exchange_flow < 0 else "inflow"
    signal = interpret_flow_signal(exchange_flow, vs_average, symbol)

    return {
        "net_flow_usd": exchange_flow,
        "direction": direction,
        "vs_average": round(vs_average, 1),
        "signal": signal
    }


def interpret_segment_signal(symbol: str, segment: str, net_flow: float, vs_average: float) -> Tuple[str, str]:
    """
    Interpret smart money segment flow signal.

    Returns (signal_key, human_label) tuple.
    """
    is_stable = symbol in STABLECOINS

    if is_stable:
        if net_flow < 0:  # Outflow = deploying stables to buy crypto
            if vs_average >= 8.0:
                return ("very_bullish", "Aggressive deployment")
            elif vs_average >= 3.0:
                return ("bullish", "Deploying capital")
            elif vs_average >= 1.5:
                return ("neutral", "Minor deployment")
            else:
                return ("neutral", "Negligible")
        else:  # Inflow = accumulating stables
            if segment == "fresh_wallet":
                if vs_average >= 2.0:
                    return ("bullish", "New stablecoin capital")
                return ("neutral", "New stablecoin capital")
            if vs_average >= 3.0:
                return ("slight_bearish", "Heavy stable accumulation")
            elif vs_average >= 1.5:
                return ("neutral", "Accumulating stables")
            else:
                return ("neutral", "Modest accumulation")
    else:  # Crypto (BTC, ETH)
        if net_flow > 0:  # Inflow = accumulating crypto
            label = "New capital entering" if segment == "fresh_wallet" else "Accumulating"
            if vs_average >= 3.0:
                return ("very_bullish", label)
            elif vs_average >= 1.5:
                return ("bullish", label)
            else:
                return ("neutral", "Minor accumulation")
        else:  # Outflow = selling crypto
            if vs_average >= 3.0:
                return ("bearish", "Heavy selling")
            elif vs_average >= 1.5:
                return ("slight_bearish", "Profit taking")
            elif vs_average >= 0.5:
                return ("neutral", "Minor profit taking")
            else:
                return ("neutral", "Negligible")


def parse_smart_money_flows(flows_data: Dict, symbol: str = "") -> Dict:
    """
    Parse smart money flow data with per-segment breakdown.

    Returns dict with segments (each containing net_flow, avg_flow, vs_average, signal, label)
    and legacy totals for backward compatibility.
    """
    if not flows_data:
        return {"segments": {}, "totals": {"top_pnl": 0, "whales": 0, "smart_traders": 0}}

    data = flows_data.get("data", [])
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
    elif not isinstance(data, dict):
        data = {}

    segments = {}
    for api_key, display_name in SMART_MONEY_SEGMENTS.items():
        net_flow = data.get(f"{api_key}_net_flow_usd", 0) or 0
        avg_flow = abs(data.get(f"{api_key}_avg_flow_usd", 0) or 0)
        vs_average = abs(net_flow / avg_flow) if avg_flow > 0 else 0.0

        # Skip segments with no data at all
        if net_flow == 0 and avg_flow == 0:
            continue

        signal, label = interpret_segment_signal(symbol, api_key, net_flow, vs_average)

        segments[api_key] = {
            "display_name": display_name,
            "net_flow_usd": net_flow,
            "avg_flow_usd": avg_flow,
            "vs_average": round(vs_average, 1),
            "direction": "outflow" if net_flow < 0 else "inflow",
            "signal": signal,
            "label": label
        }

    # Legacy totals for backward compatibility with old snapshots
    totals = {
        "top_pnl": data.get("top_pnl_net_flow_usd", 0) or 0,
        "whales": data.get("whale_net_flow_usd", 0) or 0,
        "smart_traders": data.get("smart_trader_net_flow_usd", 0) or 0
    }

    return {"segments": segments, "totals": totals}


def parse_price(price_data: Dict) -> float:
    """Parse price from OHLCV response."""
    if not price_data:
        return 0.0

    candles = price_data.get("data", [])
    if candles and len(candles) > 0:
        return candles[-1].get("close", 0.0)

    return 0.0


# ============================================================================
# SNAPSHOT CREATION
# ============================================================================

def create_snapshot(verbose: bool = True, debug: bool = False) -> Dict:
    """Create complete CEX health snapshot by fetching from Nansen API."""
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")

    if verbose:
        print(f"\n  📊 Creating CEX snapshot: {timestamp}")
        print(f"  {'─' * 50}")

    snapshot = {
        "date": timestamp,
        "market_context": {},
        "exchange_flows_24h": {},
        "exchange_flows_7d": {},
        "smart_money_flows_24h": {},
        "summary": {}
    }

    for symbol, config in TOKENS.items():
        if verbose:
            print(f"  Fetching {symbol}...", end=" ", flush=True)

        # Fetch 24h flows
        flows_24h = fetch_token_flows(config["chain"], config["address"], "1d")

        if debug and flows_24h:
            print(f"\n  DEBUG {symbol} 24h response: {json.dumps(flows_24h, indent=2)[:500]}...")

        if flows_24h:
            snapshot["exchange_flows_24h"][symbol] = parse_exchange_flows(flows_24h, symbol)
            snapshot["smart_money_flows_24h"][symbol] = parse_smart_money_flows(flows_24h, symbol)
        else:
            snapshot["exchange_flows_24h"][symbol] = {
                "net_flow_usd": 0, "direction": "unknown",
                "vs_average": 1.0, "signal": "neutral"
            }
            snapshot["smart_money_flows_24h"][symbol] = {
                "segments": {}, "totals": {"top_pnl": 0, "whales": 0, "smart_traders": 0}
            }

        # Fetch 7d flows
        flows_7d = fetch_token_flows(config["chain"], config["address"], "7d")
        if flows_7d:
            snapshot["exchange_flows_7d"][symbol] = parse_exchange_flows(flows_7d, symbol)

        # Fetch price (for BTC/ETH only)
        if symbol in ["BTC", "ETH"]:
            price = fetch_token_price(config["chain"], config["address"], symbol)
            if price:
                snapshot["market_context"][f"{symbol.lower()}_price"] = price

        if verbose:
            print("✓")

    # Generate summary
    snapshot["summary"] = generate_summary(snapshot)

    if verbose:
        print(f"  {'─' * 50}")
        print(f"  ✅ Snapshot complete")

    return snapshot


def generate_summary(snapshot: Dict) -> Dict:
    """Generate overall summary with narrative from snapshot data."""
    flows = snapshot.get("exchange_flows_24h", {})
    smart_money = snapshot.get("smart_money_flows_24h", {})

    # Count bullish/bearish signals from exchange flows
    bullish_count = 0
    bearish_count = 0
    for symbol, data in flows.items():
        signal = data.get("signal", "neutral")
        if "bullish" in signal:
            bullish_count += 1
        elif "bearish" in signal:
            bearish_count += 1

    # Count smart money bullish/bearish signals
    sm_bullish = 0
    sm_bearish = 0
    for symbol, sm_data in smart_money.items():
        for seg_key, seg in sm_data.get("segments", {}).items():
            sig = seg.get("signal", "neutral")
            if "bullish" in sig:
                sm_bullish += 1
            elif "bearish" in sig:
                sm_bearish += 1

    # Determine overall signal — weigh exchange flows + smart money
    total_bullish = bullish_count + (1 if sm_bullish > sm_bearish else 0)
    total_bearish = bearish_count + (1 if sm_bearish > sm_bullish else 0)

    if total_bullish >= 3:
        overall_signal = "accumulation"
        confidence = "high" if total_bullish >= 4 else "medium-high"
    elif total_bearish >= 3:
        overall_signal = "distribution"
        confidence = "high" if total_bearish >= 4 else "medium-high"
    elif total_bullish > total_bearish:
        overall_signal = "accumulation"
        confidence = "medium" if total_bullish >= 2 else "low"
    elif total_bearish > total_bullish:
        overall_signal = "distribution"
        confidence = "medium" if total_bearish >= 2 else "low"
    else:
        overall_signal = "consolidation"
        confidence = "medium"

    # Check for BTC/ETH divergence
    btc_signal = flows.get("BTC", {}).get("signal", "neutral")
    eth_signal = flows.get("ETH", {}).get("signal", "neutral")
    if ("bullish" in btc_signal and "bearish" in eth_signal) or \
       ("bearish" in btc_signal and "bullish" in eth_signal):
        overall_signal = "divergence"

    narrative = build_narrative(flows, smart_money)

    return {
        "overall_signal": overall_signal,
        "confidence": confidence,
        "narrative": narrative,
        "exchange_bullish": bullish_count,
        "exchange_bearish": bearish_count,
        "sm_bullish": sm_bullish,
        "sm_bearish": sm_bearish
    }


def build_narrative(flows: Dict, smart_money: Dict) -> str:
    """Build a narrative summary paragraph from flow data."""
    observations = []

    # 1. Find the dominant exchange flow signal (highest vs_avg above threshold)
    dominant = None
    max_vs_avg = 0
    for symbol, data in flows.items():
        vs_avg = data.get("vs_average", 1.0)
        if vs_avg > max_vs_avg and vs_avg >= 1.3:
            max_vs_avg = vs_avg
            dominant = (symbol, data)

    if dominant:
        sym, d = dominant
        net = d["net_flow_usd"]
        vs = d["vs_average"]
        direction = d["direction"]
        amount = format_flow(abs(net))
        if sym in STABLECOINS:
            if direction == "inflow":
                observations.append(
                    f"{sym} exchange inflows at {vs:.1f}x average ({amount}) — buying power being staged"
                )
            else:
                observations.append(
                    f"{sym} exchange outflows at {vs:.1f}x average ({amount}) — capital leaving exchanges"
                )
        else:
            if direction == "inflow":
                observations.append(
                    f"{sym} exchange inflows at {vs:.1f}x average ({amount}) — selling pressure"
                )
            else:
                observations.append(
                    f"{sym} exchange outflows at {vs:.1f}x average ({amount}) — accumulation"
                )

    # 2. Notable smart money activity (vs_avg >= 2.0)
    notable_sm = []
    for symbol, sm_data in smart_money.items():
        for seg_key, seg in sm_data.get("segments", {}).items():
            vs = seg.get("vs_average", 0)
            if vs >= 2.0:
                notable_sm.append((symbol, seg))

    notable_sm.sort(key=lambda x: x[1].get("vs_average", 0), reverse=True)

    if notable_sm:
        sm_parts = []
        for sym, seg in notable_sm[:3]:
            name = seg["display_name"]
            vs = seg["vs_average"]
            label = seg["label"]
            sm_parts.append(f"{name} {sym} at {vs:.1f}x ({label.lower()})")
        observations.append("Smart money: " + ", ".join(sm_parts))

    # 3. Counter-signals (non-dominant flows that are notable)
    for symbol, data in flows.items():
        signal = data.get("signal", "neutral")
        vs = data.get("vs_average", 1.0)
        if signal != "neutral" and vs >= 1.3 and (dominant is None or symbol != dominant[0]):
            direction = data["direction"]
            if "bearish" in signal:
                observations.append(f"{symbol} {direction} at {vs:.1f}x — mild headwind")
            elif "bullish" in signal and dominant and "bearish" in dominant[1].get("signal", ""):
                observations.append(f"{symbol} {direction} at {vs:.1f}x — partial offset")

    if not observations:
        return "Normal flow activity across all tracked assets. No significant deviations from average."

    return ". ".join(observations) + "."


# ============================================================================
# DATA PERSISTENCE
# ============================================================================

def load_cex_data() -> Dict:
    """Load existing CEX health data."""
    if not DATA_FILE.exists():
        return create_empty_data()

    with open(DATA_FILE, 'r') as f:
        return json.load(f)


def save_cex_data(data: Dict):
    """Save CEX health data to JSON file."""
    data['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')

    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)


def create_empty_data() -> Dict:
    """Create empty data structure."""
    return {
        "metadata": {
            "description": "CEX Health Tracker - Daily exchange flow snapshots",
            "tracked_assets": list(TOKENS.keys()),
            "data_source": "Nansen",
            "created": datetime.now().strftime('%Y-%m-%d'),
            "last_updated": datetime.now().strftime('%Y-%m-%d')
        },
        "tokens": TOKENS,
        "snapshots": [],
        "alerts": {
            "thresholds": ALERT_THRESHOLDS,
            "active_alerts": []
        }
    }


def save_snapshot(snapshot: Dict, max_snapshots: int = 30):
    """
    Save snapshot to cex_health.json and database.

    Args:
        snapshot: Snapshot to save
        max_snapshots: Maximum snapshots to keep (default 30 = 15 days at 2x/day)
    """
    data = load_cex_data()

    # Get previous before appending
    previous = data["snapshots"][-1] if data.get("snapshots") else None

    data["snapshots"].append(snapshot)

    if len(data["snapshots"]) > max_snapshots:
        data["snapshots"] = data["snapshots"][-max_snapshots:]

    alerts = check_alerts(snapshot, previous)
    if alerts:
        data["alerts"]["active_alerts"] = alerts

    save_cex_data(data)
    save_to_db(snapshot)


def save_to_db(snapshot: Dict):
    """Save snapshot to cex_snapshots table in SQLite database."""
    try:
        import sqlite3

        if not DB_FILE.exists():
            print(f"  ⚠️  Database not found: {DB_FILE}")
            return

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cex_snapshots'")
        table_exists = cursor.fetchone() is not None

        if table_exists:
            cursor.execute("PRAGMA table_info(cex_snapshots)")
            columns = {row[1] for row in cursor.fetchall()}
            if 'date' not in columns and 'snapshot_date' not in columns:
                cursor.execute("DROP TABLE cex_snapshots")
                table_exists = False

        if not table_exists:
            cursor.execute("""
                CREATE TABLE cex_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    btc_price REAL,
                    eth_price REAL,
                    btc_flow REAL,
                    eth_flow REAL,
                    usdt_flow REAL,
                    usdc_flow REAL,
                    overall_signal TEXT,
                    confidence TEXT,
                    snapshot_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        ctx = snapshot.get("market_context", {})
        flows = snapshot.get("exchange_flows_24h", {})
        summary = snapshot.get("summary", {})

        cursor.execute("""
            INSERT INTO cex_snapshots (
                date, btc_price, eth_price, btc_flow, eth_flow, usdt_flow, usdc_flow,
                overall_signal, confidence, snapshot_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot["date"],
            ctx.get("btc_price", 0),
            ctx.get("eth_price", 0),
            flows.get("BTC", {}).get("net_flow_usd", 0),
            flows.get("ETH", {}).get("net_flow_usd", 0),
            flows.get("USDT", {}).get("net_flow_usd", 0),
            flows.get("USDC", {}).get("net_flow_usd", 0),
            summary.get("overall_signal", "unknown"),
            summary.get("confidence", "unknown"),
            json.dumps(snapshot)
        ))

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"  ⚠️  Error saving to database: {e}")


def get_previous_snapshot(data: Dict) -> Optional[Dict]:
    """Get the second-to-last snapshot for comparison."""
    if len(data.get("snapshots", [])) < 2:
        return None
    return data["snapshots"][-2]


def load_prior_snapshot() -> Optional[Dict]:
    """Load the snapshot before the most recent one from cex_health.json.

    Call AFTER save_snapshot so the current snapshot is already appended.
    Returns the second-to-last entry (the true prior).
    """
    data = load_cex_data()
    snapshots = data.get("snapshots", [])
    if len(snapshots) >= 2:
        return snapshots[-2]
    return None


# ============================================================================
# ALERTS
# ============================================================================

def check_alerts(snapshot: Dict, previous: Optional[Dict] = None) -> List[Dict]:
    """
    Check for alert conditions including bullish signals.

    Returns alerts sorted by priority (CRITICAL > HIGH BULLISH > HIGH > BULLISH > WATCH).
    """
    alerts = []

    for symbol in TOKENS:
        flows = snapshot.get("exchange_flows_24h", {}).get(symbol, {})
        vs_avg = flows.get("vs_average", 1.0)
        net_flow = flows.get("net_flow_usd", 0)
        signal = flows.get("signal", "neutral")
        direction = "outflow" if net_flow < 0 else "inflow"
        is_bullish_flow = "bullish" in signal

        # Extreme flow alert (4x+)
        if vs_avg >= ALERT_THRESHOLDS["extreme_flow_multiplier"]:
            if is_bullish_flow:
                context = _bullish_context(symbol, direction, net_flow)
                alerts.append({
                    "date": snapshot["date"], "asset": symbol,
                    "type": f"extreme_{direction}", "value": net_flow,
                    "vs_average": vs_avg, "priority": "HIGH BULLISH",
                    "emoji": "🟢",
                    "message": f"{symbol} {direction}s {vs_avg:.1f}x average — {context}"
                })
            else:
                context = _bearish_context(symbol, direction, net_flow)
                alerts.append({
                    "date": snapshot["date"], "asset": symbol,
                    "type": f"extreme_{direction}", "value": net_flow,
                    "vs_average": vs_avg, "priority": "CRITICAL",
                    "emoji": "🔴",
                    "message": f"{symbol} {direction}s {vs_avg:.1f}x average — {context}"
                })

        # Large flow alert (2x+)
        elif vs_avg >= ALERT_THRESHOLDS["large_flow_multiplier"]:
            if is_bullish_flow:
                context = _bullish_context(symbol, direction, net_flow)
                alerts.append({
                    "date": snapshot["date"], "asset": symbol,
                    "type": f"large_{direction}", "value": net_flow,
                    "vs_average": vs_avg, "priority": "BULLISH",
                    "emoji": "🟢",
                    "message": f"{symbol} {direction}s {vs_avg:.1f}x average — {context}"
                })
            else:
                alerts.append({
                    "date": snapshot["date"], "asset": symbol,
                    "type": f"large_{direction}", "value": net_flow,
                    "vs_average": vs_avg, "priority": "HIGH",
                    "emoji": "🟠",
                    "message": f"{symbol} {direction}s {vs_avg:.1f}x average"
                })

        # Watch level (1.3x+ with non-neutral signal)
        elif vs_avg >= ALERT_THRESHOLDS["watch_flow_multiplier"] and signal != "neutral":
            emoji = "🟢" if is_bullish_flow else "🔴"
            context = _bullish_context(symbol, direction, net_flow) if is_bullish_flow \
                else _bearish_context(symbol, direction, net_flow)
            alerts.append({
                "date": snapshot["date"], "asset": symbol,
                "type": f"watch_{direction}", "value": net_flow,
                "vs_average": vs_avg, "priority": "WATCH",
                "emoji": emoji,
                "message": f"{symbol} {direction}s {vs_avg:.1f}x average — {context}"
            })

        # Flow reversal detection
        if previous:
            prev_flow = previous.get("exchange_flows_24h", {}).get(symbol, {}).get("net_flow_usd", 0)
            if (net_flow > 0) != (prev_flow > 0) and prev_flow != 0:
                new_direction = "inflow" if net_flow > 0 else "outflow"
                alerts.append({
                    "date": snapshot["date"], "asset": symbol,
                    "type": "flow_reversal", "value": net_flow,
                    "vs_average": vs_avg, "priority": "WATCH",
                    "emoji": "🟡",
                    "message": f"{symbol} flow reversed to {new_direction}"
                })

    # Smart money alerts (notable segments at 5x+)
    smart_money = snapshot.get("smart_money_flows_24h", {})
    for symbol, sm_data in smart_money.items():
        for seg_key, seg in sm_data.get("segments", {}).items():
            vs = seg.get("vs_average", 0)
            if vs >= 5.0:
                name = seg["display_name"]
                label = seg["label"]
                seg_direction = seg["direction"]
                is_bullish = "bullish" in seg.get("signal", "neutral")
                emoji = "🟢" if is_bullish else "🔴"
                if is_bullish and vs >= 8.0:
                    priority = "HIGH BULLISH"
                elif is_bullish:
                    priority = "BULLISH"
                else:
                    priority = "WATCH"
                alerts.append({
                    "date": snapshot["date"], "asset": symbol,
                    "type": f"smart_money_{seg_key}", "value": seg["net_flow_usd"],
                    "vs_average": vs, "priority": priority,
                    "emoji": emoji,
                    "message": f"{name} {symbol} {seg_direction} at {vs:.1f}x average — {label.lower()}"
                })

    # Sort: CRITICAL > HIGH BULLISH > HIGH > BULLISH > WATCH
    priority_order = {"CRITICAL": 0, "HIGH BULLISH": 1, "HIGH": 2, "BULLISH": 3, "WATCH": 4}
    alerts.sort(key=lambda a: priority_order.get(a["priority"], 5))

    return alerts


def _bullish_context(symbol: str, direction: str, net_flow: float) -> str:
    """Generate bullish context description."""
    amount = format_flow(abs(net_flow))
    is_stable = symbol in STABLECOINS
    if is_stable:
        if direction == "inflow":
            return f"{amount} buying power staged on exchanges"
        else:
            return f"{amount} being deployed from exchanges"
    else:
        if direction == "outflow":
            return f"{amount} withdrawn from exchanges (accumulation)"
        else:
            return f"{amount} moved to exchanges"


def _bearish_context(symbol: str, direction: str, net_flow: float) -> str:
    """Generate bearish context description."""
    amount = format_flow(abs(net_flow))
    is_stable = symbol in STABLECOINS
    if is_stable:
        if direction == "outflow":
            return f"{amount} buying power leaving exchanges"
        else:
            return f"{amount} stablecoins moving to exchanges"
    else:
        if direction == "inflow":
            return f"{amount} deposited to exchanges (selling pressure)"
        else:
            return f"{amount} leaving exchanges"


# ============================================================================
# REPORTING
# ============================================================================

def format_flow(value: float) -> str:
    """Format flow value in human-readable format."""
    abs_val = abs(value)
    sign = "+" if value > 0 else "-"

    if abs_val >= 1_000_000_000:
        return f"{sign}${abs_val/1_000_000_000:.2f}B"
    elif abs_val >= 1_000_000:
        return f"{sign}${abs_val/1_000_000:.1f}M"
    elif abs_val >= 1_000:
        return f"{sign}${abs_val/1_000:.1f}K"
    else:
        return f"{sign}${abs_val:.0f}"


def generate_report(snapshot: Dict, previous: Optional[Dict] = None) -> str:
    """Generate enriched markdown report with per-segment smart money and delta tracking."""
    lines = [f"# CEX Health: {snapshot['date']}", ""]

    # Market context
    ctx = snapshot.get("market_context", {})
    if ctx:
        btc_price = ctx.get("btc_price", 0)
        eth_price = ctx.get("eth_price", 0)
        if btc_price or eth_price:
            lines.append("## Market")
            lines.append(f"**BTC:** ${btc_price:,.0f} | **ETH:** ${eth_price:,.0f}")
            lines.append("")

    # Exchange flows 24h — enriched format
    lines.append("## Exchange Flows (24h)")
    lines.append("| Asset | Exchange Net Flow | vs Avg | Signal |")
    lines.append("|-------|------------------|--------|--------|")

    flows = snapshot.get("exchange_flows_24h", {})
    for symbol in TOKENS:
        if symbol in flows:
            data = flows[symbol]
            net = data.get("net_flow_usd", 0)
            vs_avg = data.get("vs_average", 1.0)
            signal = data.get("signal", "neutral")
            signal_emoji = FLOW_SIGNALS.get(signal, "🟡")
            signal_label = SIGNAL_LABELS.get(signal, "Neutral")
            direction = data.get("direction", "")

            flow_str = f"{format_flow(net)} {direction}"

            # Add proxy note for BTC/ETH
            display_symbol = symbol
            if TOKENS[symbol].get("proxy"):
                display_symbol = f"{symbol} ({TOKENS[symbol]['proxy']} proxy)"

            # Add context to stablecoin signals
            if symbol in STABLECOINS and signal != "neutral":
                if "bullish" in signal:
                    signal_label += " (buying power staged)"
                elif "bearish" in signal:
                    signal_label += " (capital leaving)"

            lines.append(f"| {display_symbol} | {flow_str} | {vs_avg:.1f}x | {signal_emoji} {signal_label} |")

    lines.append("")

    # Smart money flows — enriched per-segment table
    smart = snapshot.get("smart_money_flows_24h", {})
    has_segments = any(sm_data.get("segments") for sm_data in smart.values())

    if has_segments:
        lines.append("## Smart Money (24h)")
        lines.append("| Asset | Segment | Flow | vs Avg | Signal |")
        lines.append("|-------|---------|------|--------|--------|")

        # Collect all segment rows, sort by vs_average descending
        rows = []
        for symbol in TOKENS:
            if symbol in smart:
                segments = smart[symbol].get("segments", {})
                for seg_key, seg in segments.items():
                    vs = seg.get("vs_average", 0)
                    # Show segments with meaningful activity
                    if vs >= 0.5 or abs(seg.get("net_flow_usd", 0)) >= 100_000:
                        rows.append((symbol, seg, vs))

        rows.sort(key=lambda x: x[2], reverse=True)

        for symbol, seg, vs in rows:
            name = seg["display_name"]
            net = seg["net_flow_usd"]
            direction = seg["direction"]
            signal = seg.get("signal", "neutral")
            label = seg.get("label", "")
            signal_emoji = FLOW_SIGNALS.get(signal, "🟡")
            flow_str = f"{format_flow(net)} {direction}"
            vs_str = f"{vs:.1f}x" if vs > 0 else "~0x"

            lines.append(f"| {symbol} | {name} | {flow_str} | {vs_str} | {signal_emoji} {label} |")

        lines.append("")
    else:
        # Fallback to legacy simple table (for old snapshot data)
        lines.append("## Smart Money (24h)")
        lines.append("| Asset | Top PnL | Whales |")
        lines.append("|-------|---------|--------|")

        for symbol in ["BTC", "ETH"]:
            if symbol in smart:
                totals = smart[symbol].get("totals", smart[symbol])
                top_pnl = totals.get("top_pnl", 0)
                whales = totals.get("whales", 0)
                lines.append(f"| {symbol} | {format_flow(top_pnl)} | {format_flow(whales)} |")

        lines.append("")

    # Alerts — enriched with bullish/bearish context
    alerts = check_alerts(snapshot, previous)
    if alerts:
        lines.append("## Alerts")
        for alert in alerts:
            emoji = alert.get("emoji", "🟠")
            priority = alert["priority"]
            message = alert["message"]
            lines.append(f"- {emoji} **[{priority}]** {message}")
        lines.append("")

    # Summary — narrative format
    summary = snapshot.get("summary", {})
    if summary:
        lines.append("## Summary")
        signal = summary.get("overall_signal", "unknown")
        confidence = summary.get("confidence", "unknown")
        narrative = summary.get("narrative", summary.get("notes", ""))

        signal_emoji = "🟢" if "accum" in signal.lower() else \
                       "🔴" if "distrib" in signal.lower() else \
                       "⚡" if "diverg" in signal.lower() else "🟡"

        lines.append(f"**Signal:** {signal_emoji} {signal.title()} | **Confidence:** {confidence.title()}")
        lines.append("")
        if narrative:
            lines.append(narrative)
            lines.append("")

    # Delta vs prior snapshot
    if previous:
        delta_lines = generate_delta(snapshot, previous)
        if delta_lines:
            lines.append(f"## Delta vs Prior Snapshot ({previous.get('date', 'unknown')})")
            for dl in delta_lines:
                lines.append(f"- {dl}")
            lines.append("")

    return "\n".join(lines)


def generate_delta(current: Dict, previous: Dict) -> List[str]:
    """Generate delta comparison lines between current and previous snapshot."""
    deltas = []

    curr_flows = current.get("exchange_flows_24h", {})
    prev_flows = previous.get("exchange_flows_24h", {})

    for symbol in TOKENS:
        curr = curr_flows.get(symbol, {})
        prev = prev_flows.get(symbol, {})

        curr_vs = curr.get("vs_average", 1.0)
        prev_vs = prev.get("vs_average", 1.0)
        curr_dir = curr.get("direction", "")
        prev_dir = prev.get("direction", "")

        # Report direction changes
        if prev_dir and curr_dir and prev_dir != curr_dir:
            deltas.append(
                f"{symbol}: {prev_vs:.1f}x {prev_dir} → {curr_vs:.1f}x {curr_dir} (direction reversed)"
            )
        # Report significant magnitude changes
        elif abs(curr_vs - prev_vs) >= 0.5 or curr_vs >= 2.0 or prev_vs >= 2.0:
            if curr_vs != prev_vs:
                trend = "↑" if curr_vs > prev_vs else "↓"
                deltas.append(f"{symbol}: {prev_vs:.1f}x → {curr_vs:.1f}x {curr_dir} {trend}")

    # Smart money notable changes
    curr_sm = current.get("smart_money_flows_24h", {})
    prev_sm = previous.get("smart_money_flows_24h", {})

    for symbol in TOKENS:
        curr_segs = curr_sm.get(symbol, {}).get("segments", {})
        prev_segs = prev_sm.get(symbol, {}).get("segments", {})

        for seg_key in set(list(curr_segs.keys()) + list(prev_segs.keys())):
            curr_seg = curr_segs.get(seg_key, {})
            prev_seg = prev_segs.get(seg_key, {})

            curr_seg_vs = curr_seg.get("vs_average", 0)
            prev_seg_vs = prev_seg.get("vs_average", 0)

            # Only report notable smart money changes (either was >= 3x)
            if curr_seg_vs >= 3.0 or prev_seg_vs >= 3.0:
                name = SMART_MONEY_SEGMENTS.get(seg_key, seg_key)
                if prev_seg_vs > 0:
                    trend = "more aggressive" if curr_seg_vs > prev_seg_vs else "less aggressive"
                    deltas.append(f"{name} {symbol}: {prev_seg_vs:.1f}x → {curr_seg_vs:.1f}x ({trend})")
                elif curr_seg_vs >= 3.0:
                    deltas.append(f"{name} {symbol}: new at {curr_seg_vs:.1f}x")

    # Overall signal change
    curr_signal = current.get("summary", {}).get("overall_signal", "unknown")
    prev_signal = previous.get("summary", {}).get("overall_signal", "unknown")
    if curr_signal != prev_signal:
        deltas.append(f"Overall signal: {prev_signal.title()} → {curr_signal.title()}")

    return deltas


def save_report(snapshot: Dict) -> str:
    """Save enriched report to signals/dashboards/ directory."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    report_path = REPORTS_DIR / f"cex_{timestamp}.md"

    # Load previous snapshot for delta comparison
    # (called after save_snapshot, so current is [-1] and prior is [-2])
    previous = load_prior_snapshot()

    report = generate_report(snapshot, previous)

    with open(report_path, 'w') as f:
        f.write(report)

    return str(report_path)


def print_status(data: Dict):
    """Print current status from latest snapshot."""
    if not data.get("snapshots"):
        print("\n  ⚠️  No snapshots available. Run 'snapshot' to fetch data.")
        return

    snapshot = data["snapshots"][-1]

    print("\n" + "=" * 60)
    print("  🏦 CEX FLOW STATUS")
    print("=" * 60)

    print(f"\n  📅 Latest: {snapshot['date']}")

    ctx = snapshot.get("market_context", {})
    if ctx:
        print(f"  📊 BTC: ${ctx.get('btc_price', 0):,.0f} | ETH: ${ctx.get('eth_price', 0):,.0f}")

    print(f"\n  {'Asset':<8} {'Net Flow':<14} {'vs Avg':<10} {'Signal':<12}")
    print(f"  {'-' * 50}")

    flows = snapshot.get("exchange_flows_24h", {})
    for symbol in TOKENS:
        if symbol in flows:
            data = flows[symbol]
            net = data.get("net_flow_usd", 0)
            vs_avg = data.get("vs_average", 1.0)
            signal = data.get("signal", "neutral")
            signal_emoji = FLOW_SIGNALS.get(signal, "🟡")
            print(f"  {symbol:<8} {format_flow(net):<14} {vs_avg:.1f}x{'':<6} {signal_emoji} {signal:<10}")

    summary = snapshot.get("summary", {})
    if summary:
        print(f"\n  📋 Signal: {summary.get('overall_signal', 'unknown').upper()}")
        print(f"  📋 Confidence: {summary.get('confidence', 'unknown').upper()}")
        narrative = summary.get("narrative", summary.get("notes", ""))
        if narrative:
            print(f"\n  📝 {narrative[:200]}")

    print("\n" + "=" * 60)


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="CEX Flow Cron Monitor - Direct Nansen API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  snapshot      Fetch fresh data and create snapshot
  status        Show latest snapshot status
  alerts        Check alerts only

Examples:
  python3 src/watchers/cex_monitor.py snapshot              # Interactive
  python3 src/watchers/cex_monitor.py snapshot --cron       # Cron mode
  python3 src/watchers/cex_monitor.py status                # Check status
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # snapshot
    snapshot_parser = subparsers.add_parser('snapshot', help='Create new snapshot')
    snapshot_parser.add_argument('--cron', action='store_true', help='Cron mode (save to file)')
    snapshot_parser.add_argument('--debug', action='store_true', help='Show debug output')

    # status
    subparsers.add_parser('status', help='Show latest status')

    # alerts
    subparsers.add_parser('alerts', help='Show alerts only')

    args = parser.parse_args()

    # Only snapshot requires the API key; status/alerts read local files
    if not NANSEN_API_KEY and args.command == "snapshot":
        print("❌ Error: NANSEN_API_KEY not set in .env")
        sys.exit(1)

    if args.command == "snapshot":
        snapshot = create_snapshot(verbose=not args.cron, debug=getattr(args, 'debug', False))

        # Save snapshot (appends to cex_health.json + database)
        save_snapshot(snapshot)

        # Save enriched report (loads prior snapshot for delta comparison)
        report_path = save_report(snapshot)

        if args.cron:
            print(f"Report saved to: {report_path}")
            summary = snapshot.get("summary", {})
            print(f"Signal: {summary.get('overall_signal', 'unknown')} | Confidence: {summary.get('confidence', 'unknown')}")
            alerts = check_alerts(snapshot)
            if alerts:
                for alert in alerts:
                    print(f"[{alert['priority']}] {alert['message']}")
        else:
            previous = load_prior_snapshot()
            print("\n" + generate_report(snapshot, previous))
            print(f"\n  💾 Saved to: {report_path}")

    elif args.command == "status":
        data = load_cex_data()
        print_status(data)

    elif args.command == "alerts":
        data = load_cex_data()
        if not data.get("snapshots"):
            print("\n  ⚠️  No snapshots available.")
            return

        snapshot = data["snapshots"][-1]
        previous = get_previous_snapshot(data)
        alerts = check_alerts(snapshot, previous)

        if alerts:
            print("\n  🚨 ACTIVE ALERTS")
            print(f"  {'─' * 50}")
            for alert in alerts:
                emoji = alert.get("emoji", "🟠")
                print(f"  {emoji} [{alert['priority']}] {alert['message']}")
        else:
            print("\n  ✅ No active alerts.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
