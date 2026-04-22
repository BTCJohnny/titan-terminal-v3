#!/usr/bin/env python3
"""
Titan Terminal v3 — Technical Analysis Engine
==============================================
CLI tool for downloading, caching, and analyzing crypto OHLCV data.
All computation is deterministic Python math. Claude Code interprets the results.

Usage:
    python3 src/analysis/indicators.py download <SYMBOL> [--timeframe 4h] [--full]
    python3 src/analysis/indicators.py analyze <SYMBOL> [--timeframe 4h] [--indicators rsi,macd,bb,sma,atr,adx,obv,sr]
    python3 src/analysis/indicators.py report <SYMBOL> [--timeframe 4h]
    python3 src/analysis/indicators.py list

Data Sources (Free — Fallback Chain):
    1. Binance Futures via CCXT (primary) — 1500 candles/batch, 300+ perps
    2. Hyperliquid API — 5000 candles, 228 perps
    3. Coinbase API — 300 candles, 1150+ coins
    4. CoinMarketCap Quotes (last resort) — latest price only

Storage: SQLite (data/titan_data.db)
"""

import argparse
import sqlite3
import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
import sys

# Add project root to path so src.fetchers imports work when run as a script
_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Optional import for Binance fetcher (fallback gracefully if not available)
try:
    from src.fetchers.binance_fetcher import fetch_from_binance
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False


def load_env_key(key_name: str) -> Optional[str]:
    """Load an API key from .env file."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    if not env_path.exists():
        return None

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith(f"{key_name}=") and not line.startswith("#"):
                value = line.split("=", 1)[1].strip()
                if value and value != '""' and value != "''":
                    return value
    return None


def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def from_timestamp_utc(ts_ms: int) -> datetime:
    """Convert millisecond timestamp to UTC datetime."""
    return datetime.fromtimestamp(ts_ms / 1000, timezone.utc)


def fmt_price(value, decimals: int = 2) -> str:
    """Format a price value, handling None gracefully."""
    if value is None:
        return "N/A"
    return f"${value:,.{decimals}f}"


def fmt_num(value, decimals: int = 2) -> str:
    """Format a number, handling None gracefully."""
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def _format_divergence_line(div) -> str:
    """Format a divergence dict as a one-line string for the report."""
    if not div:
        return "None detected"
    return f"{div['label']} ({div['strength']}, score {div['score']}/100, {div['bars_ago']} bars ago)"


# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "titan_data.db"

# CoinMarketCap API (requires key — last resort)
CMC_API = "https://pro-api.coinmarketcap.com/v2"

# Supported timeframes (used for argparse choices)
SUPPORTED_TIMEFRAMES = [
    "1m", "3m", "5m", "15m", "30m",
    "1h", "2h", "4h", "6h", "8h", "12h",
    "1d", "3d", "1w", "1M"
]

# CMC timeframe mappings (interval parameter)
CMC_TIMEFRAME_MAP = {
    "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "4h": "4h", "12h": "12h",
    "1d": "1d", "1w": "7d", "1M": "30d"
}

# How many candles to fetch per timeframe (Coinbase returns up to 300)
CANDLES_PER_REQUEST = 300

# Default candle count for initial fetch per timeframe (~180 days of data)
# Hyperliquid supports up to 5000 if needed
DEFAULT_CANDLE_COUNT = 1080

# Per-timeframe minimum candle counts (ensures sufficient history for analysis)
TIMEFRAME_CANDLE_MINIMUMS = {
    "1h": 4320,   # 180 days × 24h
    "4h": 1080,   # 180 days × 6
    "1d": 365,    # 365 days
    "1w": 200,    # ~4 years
}

def get_default_candle_count(timeframe: str) -> int:
    """Return the target candle count for a given timeframe."""
    return TIMEFRAME_CANDLE_MINIMUMS.get(timeframe, DEFAULT_CANDLE_COUNT)


# ============================================================================
# DATABASE LAYER
# ============================================================================

def init_db():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ohlcv (
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL NOT NULL,
            PRIMARY KEY (symbol, timeframe, timestamp)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_tf
        ON ohlcv (symbol, timeframe, timestamp DESC)
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            last_updated INTEGER NOT NULL,
            PRIMARY KEY (symbol, timeframe)
        )
    """)

    conn.commit()
    conn.close()


def get_cached_data(symbol: str, timeframe: str, days: int = 90) -> list:
    """Retrieve cached OHLCV data from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cutoff = int((utc_now() - timedelta(days=days)).timestamp() * 1000)

    cursor.execute("""
        SELECT timestamp, open, high, low, close, volume
        FROM ohlcv
        WHERE symbol = ? AND timeframe = ? AND timestamp >= ?
        ORDER BY timestamp ASC
    """, (symbol.upper(), timeframe, cutoff))

    rows = cursor.fetchall()
    conn.close()

    return [{"t": r[0], "o": r[1], "h": r[2], "l": r[3], "c": r[4], "v": r[5]} for r in rows]


def save_candles(symbol: str, timeframe: str, candles: list):
    """Save OHLCV candles to SQLite (upsert)."""
    if not candles:
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.executemany("""
        INSERT OR REPLACE INTO ohlcv (symbol, timeframe, timestamp, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (symbol.upper(), timeframe, c["t"], c["o"], c["h"], c["l"], c["c"], c["v"])
        for c in candles
    ])

    # Update metadata
    cursor.execute("""
        INSERT OR REPLACE INTO metadata (symbol, timeframe, last_updated)
        VALUES (?, ?, ?)
    """, (symbol.upper(), timeframe, int(utc_now().timestamp() * 1000)))

    conn.commit()
    conn.close()


def get_last_update(symbol: str, timeframe: str) -> Optional[datetime]:
    """Get the last update time for a symbol/timeframe pair."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT last_updated FROM metadata
        WHERE symbol = ? AND timeframe = ?
    """, (symbol.upper(), timeframe))

    row = cursor.fetchone()
    conn.close()

    if row:
        return from_timestamp_utc(row[0])
    return None


def list_cached_symbols() -> list:
    """List all cached symbols and their data ranges."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT symbol, timeframe,
               MIN(timestamp) as earliest,
               MAX(timestamp) as latest,
               COUNT(*) as candles
        FROM ohlcv
        GROUP BY symbol, timeframe
        ORDER BY symbol, timeframe
    """)

    rows = cursor.fetchall()
    conn.close()

    return [{
        "symbol": r[0],
        "timeframe": r[1],
        "earliest": from_timestamp_utc(r[2]).strftime("%Y-%m-%d"),
        "latest": from_timestamp_utc(r[3]).strftime("%Y-%m-%d"),
        "candles": r[4]
    } for r in rows]


def get_latest_cached_timestamp(symbol: str, timeframe: str) -> Optional[int]:
    """Get the most recent cached timestamp for a symbol/timeframe pair."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT MAX(timestamp) FROM ohlcv
        WHERE symbol = ? AND timeframe = ?
    """, (symbol.upper(), timeframe))

    row = cursor.fetchone()
    conn.close()

    return row[0] if row and row[0] else None


def get_cached_candle_count(symbol: str, timeframe: str) -> int:
    """Get the number of cached candles for a symbol/timeframe pair."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM ohlcv
        WHERE symbol = ? AND timeframe = ?
    """, (symbol.upper(), timeframe))

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else 0


def calculate_candles_needed(symbol: str, timeframe: str) -> tuple[int, str]:
    """
    Calculate how many candles to fetch based on existing cache.

    Returns: (candle_count, fetch_mode)
        - fetch_mode: "initial" (no cache) or "incremental" (fill gap)
    """
    latest_ts = get_latest_cached_timestamp(symbol, timeframe)

    if latest_ts is None:
        # No cache - do initial full fetch
        return get_default_candle_count(timeframe), "initial"

    # Calculate gap from last cached candle to now
    tf_ms = {
        "1m": 60000, "3m": 180000, "5m": 300000, "15m": 900000, "30m": 1800000,
        "1h": 3600000, "2h": 7200000, "4h": 14400000, "8h": 28800000, "12h": 43200000,
        "1d": 86400000, "3d": 259200000, "1w": 604800000, "1M": 2592000000
    }.get(timeframe, 14400000)

    now_ms = int(utc_now().timestamp() * 1000)
    gap_ms = now_ms - latest_ts
    candles_needed = (gap_ms // tf_ms) + 10  # Add buffer of 10 candles for overlap/safety

    # Cap at reasonable amount for incremental, minimum 50
    candles_needed = max(50, min(candles_needed, 500))

    return candles_needed, "incremental"


# ============================================================================
# DATA FETCHING
# ============================================================================

def fetch_from_cmc_quotes(symbol: str) -> list:
    """Fetch latest quote from CoinMarketCap API (free tier compatible)."""
    api_key = load_env_key("COINMARKETCAP_API_KEY")
    if not api_key:
        print("CMC API key not configured in .env", file=sys.stderr)
        return []

    # Use v1 quotes endpoint (free tier)
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={symbol.upper()}&convert=USD"

    try:
        req = urllib.request.Request(url, headers={
            "X-CMC_PRO_API_KEY": api_key,
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())

            if data.get("status", {}).get("error_code") == 0:
                symbol_data = data.get("data", {}).get(symbol.upper(), {})
                if symbol_data:
                    quote = symbol_data.get("quote", {}).get("USD", {})
                    if quote:
                        ts_str = quote.get("last_updated", "")
                        ts = int(datetime.fromisoformat(
                            ts_str.replace("Z", "+00:00")
                        ).timestamp() * 1000)

                        price = float(quote.get("price", 0))
                        volume = float(quote.get("volume_24h", 0))
                        pct_24h = float(quote.get("percent_change_24h", 0))

                        # Estimate OHLC from current price and 24h change
                        open_price = price / (1 + pct_24h / 100) if pct_24h else price

                        return [{
                            "t": ts,
                            "o": open_price,
                            "h": max(price, open_price) * 1.01,  # Estimate
                            "l": min(price, open_price) * 0.99,  # Estimate
                            "c": price,
                            "v": volume
                        }]
            return []

    except Exception as e:
        print(f"CMC Quotes Error: {e}", file=sys.stderr)
        return []


def fetch_historical_from_cmc(symbol: str, timeframe: str, count: int = 50) -> list:
    """Fetch historical OHLCV data from CoinMarketCap API."""
    api_key = load_env_key("COINMARKETCAP_API_KEY")
    if not api_key:
        return []

    interval = CMC_TIMEFRAME_MAP.get(timeframe, "daily")

    # Calculate time range
    now = utc_now()
    tf_hours = {"5m": 0.083, "15m": 0.25, "30m": 0.5, "1h": 1, "4h": 4,
                "12h": 12, "1d": 24, "1w": 168, "1M": 720}
    hours_back = tf_hours.get(timeframe, 4) * count

    time_start = (now - timedelta(hours=hours_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
    time_end = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    url = (f"{CMC_API}/cryptocurrency/ohlcv/historical"
           f"?symbol={symbol.upper()}&convert=USD"
           f"&time_start={time_start}&time_end={time_end}&interval={interval}")

    try:
        req = urllib.request.Request(url, headers={
            "X-CMC_PRO_API_KEY": api_key,
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())

            if data.get("status", {}).get("error_code") == 0:
                symbol_data = data.get("data", {})
                quotes = symbol_data.get("quotes", [])

                candles = []
                for q in quotes:
                    quote = q.get("quote", {}).get("USD", {})
                    ts_str = q.get("time_open", "")
                    if ts_str and quote:
                        ts = int(datetime.fromisoformat(
                            ts_str.replace("Z", "+00:00")
                        ).timestamp() * 1000)
                        candles.append({
                            "t": ts,
                            "o": float(quote.get("open", 0)),
                            "h": float(quote.get("high", 0)),
                            "l": float(quote.get("low", 0)),
                            "c": float(quote.get("close", 0)),
                            "v": float(quote.get("volume", 0))
                        })
                return candles

            return []

    except Exception as e:
        print(f"CMC Historical Error: {e}", file=sys.stderr)
        return []


# ============================================================================
# HYPERLIQUID API (PRIMARY SOURCE)
# ============================================================================

# Hyperliquid timeframe mapping
HL_TIMEFRAME_MAP = {
    "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "2h": "2h", "4h": "4h", "8h": "8h", "12h": "12h",
    "1d": "1d", "3d": "3d", "1w": "1w", "1M": "1M"
}

# TradFi derivative symbol mapping — Hyperliquid uses prefixed coin names
TRADFI_SYMBOL_MAP = {
    "CL": "xyz:CL", "GOLD": "xyz:GOLD", "SILVER": "xyz:SILVER",
    "EUR": "xyz:EUR", "JPY": "xyz:JPY",
    "USA500": "cash:USA500", "SPX": "SPX",
}


def is_tradfi_symbol(symbol: str) -> bool:
    """Check if a symbol is a TradFi derivative on Hyperliquid."""
    return symbol.upper() in TRADFI_SYMBOL_MAP


def get_hl_coin_name(symbol: str) -> str:
    """Get the Hyperliquid API coin name for a symbol (handles TradFi prefixes)."""
    return TRADFI_SYMBOL_MAP.get(symbol.upper(), symbol.upper())


def fetch_from_hyperliquid(symbol: str, timeframe: str, candle_count: int = None) -> list:
    """
    Fetch candlestick data from Hyperliquid API (primary source).
    Free API, no key required, 5000 candles max per request.
    Returns perps data (not spot).

    Args:
        symbol: Token symbol (e.g., BTC, ETH)
        timeframe: Candle timeframe (e.g., 4h, 1d)
        candle_count: Number of candles to fetch (default: per-timeframe minimum)
    """
    if candle_count is None:
        candle_count = get_default_candle_count(timeframe)
    hl_tf = HL_TIMEFRAME_MAP.get(timeframe)
    if not hl_tf:
        return []

    # Calculate time window
    tf_ms = {
        "1m": 60000, "3m": 180000, "5m": 300000, "15m": 900000, "30m": 1800000,
        "1h": 3600000, "2h": 7200000, "4h": 14400000, "8h": 28800000, "12h": 43200000,
        "1d": 86400000, "3d": 259200000, "1w": 604800000, "1M": 2592000000
    }.get(timeframe, 14400000)

    now = utc_now()
    end_ts = int(now.timestamp() * 1000)
    start_ts = end_ts - (candle_count * tf_ms)

    try:
        req_body = json.dumps({
            "type": "candleSnapshot",
            "req": {
                "coin": get_hl_coin_name(symbol),
                "interval": hl_tf,
                "startTime": start_ts,
                "endTime": end_ts
            }
        }).encode()

        req = urllib.request.Request(
            "https://api.hyperliquid.xyz/info",
            data=req_body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())

            if isinstance(data, list) and len(data) > 0:
                return [
                    {"t": int(c["t"]), "o": float(c["o"]), "h": float(c["h"]),
                     "l": float(c["l"]), "c": float(c["c"]), "v": float(c["v"])}
                    for c in data
                ]
            return []

    except Exception:
        return []


# ============================================================================
# COINBASE API (SECONDARY SOURCE)
# ============================================================================

# Coinbase timeframe mapping - uses seconds! (no 4h!)
CB_TIMEFRAME_MAP = {
    "1m": 60, "5m": 300, "15m": 900,
    "30m": 1800, "1h": 3600, "2h": 7200,
    "6h": 21600, "1d": 86400
}


def fetch_from_coinbase(symbol: str, timeframe: str, candle_count: int = 300) -> list:
    """
    Fetch candlestick data from Coinbase public API (no auth required for OHLCV).
    Returns up to 300 candles per request.
    Note: Coinbase has no 4h timeframe - use fetch_from_coinbase_aggregated() instead.
    """
    # For 4h, we need to aggregate from 1h
    if timeframe == "4h":
        return fetch_from_coinbase_aggregated(symbol, candle_count)

    cb_tf = CB_TIMEFRAME_MAP.get(timeframe)
    if not cb_tf:
        return []

    # Coinbase uses SYMBOL-USD format
    product_id = f"{symbol.upper()}-USD"

    # Calculate time range
    now = utc_now()
    tf_seconds = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600,
                  "2h": 7200, "6h": 21600, "1d": 86400}.get(timeframe, 3600)

    end_ts = int(now.timestamp())
    start_ts = end_ts - (candle_count * tf_seconds)

    url = (f"https://api.exchange.coinbase.com/products/{product_id}/candles"
           f"?granularity={cb_tf}&start={start_ts}&end={end_ts}")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TitanTA/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())

            if isinstance(data, list) and len(data) > 0:
                # Coinbase returns [time, low, high, open, close, volume] - newest first
                candles = []
                for c in reversed(data):  # Reverse to get oldest first
                    candles.append({
                        "t": int(c[0]) * 1000,  # Convert to ms
                        "o": float(c[3]),
                        "h": float(c[2]),
                        "l": float(c[1]),
                        "c": float(c[4]),
                        "v": float(c[5])
                    })
                return candles
            return []

    except Exception:
        return []


def fetch_from_coinbase_aggregated(symbol: str, candle_count: int = 300) -> list:
    """
    Fetch 4h candles by aggregating 1h candles from Coinbase.
    Fetches 4x the candles needed, then combines every 4 into 1.
    """
    # Fetch 4x the 1h candles (capped at 300 per request)
    needed_1h = min(candle_count * 4, 300)
    one_hour_candles = fetch_from_coinbase(symbol, "1h", needed_1h)

    if len(one_hour_candles) < 4:
        return []

    return aggregate_candles(one_hour_candles, 4)


def aggregate_candles(candles: list, factor: int) -> list:
    """
    Aggregate smaller timeframe candles into larger ones.
    E.g., factor=4 combines 4 x 1h candles into 1 x 4h candle.
    E.g., factor=6 combines 6 x 4h candles into 1 x daily candle.

    Note: If candle count is not evenly divisible by factor, trailing
    candles are dropped (e.g., 100 candles with factor=6 yields 16
    aggregated candles, discarding the last 4 source candles).
    """
    if not candles or factor < 2:
        return candles

    aggregated = []
    for i in range(0, len(candles) - factor + 1, factor):
        group = candles[i:i + factor]
        aggregated.append({
            "t": group[0]["t"],  # Timestamp of first candle
            "o": group[0]["o"],  # Open of first candle
            "h": max(c["h"] for c in group),  # Highest high
            "l": min(c["l"] for c in group),  # Lowest low
            "c": group[-1]["c"],  # Close of last candle
            "v": sum(c["v"] for c in group)  # Sum of volume
        })

    return aggregated


# ============================================================================
# UNIFIED FETCH WITH FALLBACK CHAIN
# ============================================================================

def fetch_candles_from_api(symbol: str, timeframe: str, candle_count: int = None) -> tuple[list, str]:
    """
    Fetch candlestick data with fallback logic.

    Fallback Chain:
        1. Binance Futures via CCXT (primary) — 1500 candles/batch, 300+ perps
        2. Hyperliquid (secondary) — 5000 candles, 228 perps
        3. Coinbase (tertiary) — 300 candles, 1150+ coins
        4. CMC Quotes (last resort) — latest price only

    Args:
        symbol: Token symbol
        timeframe: Candle timeframe
        candle_count: Number of candles to fetch

    Returns: (candles, source_name)
    """
    # 0. TradFi fast-path — only Hyperliquid carries these (skip Binance/Coinbase/CMC)
    if is_tradfi_symbol(symbol):
        candles = fetch_from_hyperliquid(symbol, timeframe, candle_count)
        if candles:
            return candles, "Hyperliquid (TradFi)"
        return [], "None"

    # 1. Try Binance Futures first (best coverage, CCXT batches beyond 1500)
    if BINANCE_AVAILABLE:
        bn_count = min(candle_count or DEFAULT_CANDLE_COUNT, 5000)
        candles = fetch_from_binance(symbol, timeframe, bn_count)
        if candles:
            return candles, "Binance Futures"
        print(f"Binance failed for {symbol}, trying Hyperliquid...", file=sys.stderr)
    else:
        print(f"Binance CCXT not available, trying Hyperliquid...", file=sys.stderr)

    # 2. Try Hyperliquid (good for HL-listed perps)
    candles = fetch_from_hyperliquid(symbol, timeframe, candle_count)
    if candles:
        return candles, "Hyperliquid"

    print(f"Hyperliquid failed for {symbol}, trying Coinbase...", file=sys.stderr)

    # 3. Fallback to Coinbase (broadest spot coverage) - limited to 300 candles
    cb_count = min(candle_count or 300, 300)
    candles = fetch_from_coinbase(symbol, timeframe, cb_count)
    if candles:
        return candles, "Coinbase"

    print(f"Coinbase failed for {symbol}, trying CMC...", file=sys.stderr)

    # 4. Last resort: CMC quotes (free tier - single data point)
    candles = fetch_from_cmc_quotes(symbol)
    if candles:
        print(f"Note: Only latest quote available (no historical data)", file=sys.stderr)
        return candles, "CoinMarketCap (latest quote)"

    return [], "None"


def should_refresh(symbol: str, timeframe: str) -> bool:
    """Determine if cached data needs refreshing."""
    last_update = get_last_update(symbol, timeframe)

    if last_update is None:
        return True

    # Refresh intervals based on timeframe
    refresh_intervals = {
        "1m": timedelta(minutes=5),
        "5m": timedelta(minutes=15),
        "15m": timedelta(minutes=30),
        "30m": timedelta(hours=1),
        "1h": timedelta(hours=2),
        "4h": timedelta(hours=4),
        "6h": timedelta(hours=6),
        "12h": timedelta(hours=12),
        "1d": timedelta(days=1),
    }

    interval = refresh_intervals.get(timeframe, timedelta(hours=4))
    return utc_now() - last_update > interval


# ============================================================================
# TECHNICAL ANALYSIS LIBRARY
# ============================================================================

def calculate_sma(closes: list, period: int) -> list:
    """Simple Moving Average."""
    if len(closes) < period:
        return [None] * len(closes)

    sma = [None] * (period - 1)
    for i in range(period - 1, len(closes)):
        sma.append(sum(closes[i - period + 1:i + 1]) / period)
    return sma


def calculate_ema(closes: list, period: int) -> list:
    """Exponential Moving Average (internal helper — used by MACD)."""
    if len(closes) < period:
        return [None] * len(closes)

    multiplier = 2 / (period + 1)
    ema = [None] * (period - 1)

    # First EMA is SMA
    first_sma = sum(closes[:period]) / period
    ema.append(first_sma)

    for i in range(period, len(closes)):
        ema.append((closes[i] - ema[-1]) * multiplier + ema[-1])

    return ema


def calculate_rsi(closes: list, period: int = 14) -> list:
    """Relative Strength Index."""
    if len(closes) < period + 1:
        return [None] * len(closes)

    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]

    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]

    rsi = [None] * period

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_loss == 0:
        rsi.append(100)
    else:
        rs = avg_gain / avg_loss
        rsi.append(100 - (100 / (1 + rs)))

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            rsi.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi.append(100 - (100 / (1 + rs)))

    return rsi


def calculate_macd(closes: list, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """MACD (Moving Average Convergence Divergence)."""
    if len(closes) < slow + signal:
        return {"macd": [None] * len(closes), "signal": [None] * len(closes), "histogram": [None] * len(closes)}

    ema_fast = calculate_ema(closes, fast)
    ema_slow = calculate_ema(closes, slow)

    macd_line = []
    for i in range(len(closes)):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            macd_line.append(ema_fast[i] - ema_slow[i])
        else:
            macd_line.append(None)

    # Calculate signal line (EMA of MACD)
    macd_values = [v for v in macd_line if v is not None]
    if len(macd_values) >= signal:
        signal_ema = calculate_ema(macd_values, signal)
        # Pad signal line to match original length
        signal_line = [None] * (len(closes) - len(signal_ema)) + signal_ema
    else:
        signal_line = [None] * len(closes)

    # Histogram
    histogram = []
    for i in range(len(closes)):
        if macd_line[i] is not None and signal_line[i] is not None:
            histogram.append(macd_line[i] - signal_line[i])
        else:
            histogram.append(None)

    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}


def calculate_bollinger_bands(closes: list, period: int = 20, std_dev: float = 2.0) -> dict:
    """Bollinger Bands."""
    if len(closes) < period:
        return {"upper": [None] * len(closes), "middle": [None] * len(closes), "lower": [None] * len(closes)}

    middle = calculate_sma(closes, period)
    upper = []
    lower = []

    for i in range(len(closes)):
        if middle[i] is not None:
            # Calculate standard deviation
            window = closes[i - period + 1:i + 1]
            mean = sum(window) / period
            variance = sum((x - mean) ** 2 for x in window) / period
            std = variance ** 0.5

            upper.append(middle[i] + std_dev * std)
            lower.append(middle[i] - std_dev * std)
        else:
            upper.append(None)
            lower.append(None)

    return {"upper": upper, "middle": middle, "lower": lower}


def calculate_atr(candles: list, period: int = 14) -> list:
    """Average True Range."""
    if len(candles) < period + 1:
        return [None] * len(candles)

    true_ranges = [candles[0]["h"] - candles[0]["l"]]  # First TR is just high - low

    for i in range(1, len(candles)):
        high_low = candles[i]["h"] - candles[i]["l"]
        high_close = abs(candles[i]["h"] - candles[i-1]["c"])
        low_close = abs(candles[i]["l"] - candles[i-1]["c"])
        true_ranges.append(max(high_low, high_close, low_close))

    atr = [None] * (period - 1)
    atr.append(sum(true_ranges[:period]) / period)

    for i in range(period, len(true_ranges)):
        atr.append((atr[-1] * (period - 1) + true_ranges[i]) / period)

    return atr


def calculate_adx(candles: list, period: int = 14) -> dict:
    """
    Average Directional Index - measures trend strength (not direction).
    Returns: {"adx": list, "plus_di": list, "minus_di": list}

    ADX > 25 = strong trend, ADX < 20 = weak/no trend
    +DI > -DI = bullish trend, -DI > +DI = bearish trend
    """
    if len(candles) < period * 2:
        n = len(candles)
        return {"adx": [None] * n, "plus_di": [None] * n, "minus_di": [None] * n}

    # Calculate True Range, +DM, -DM
    tr_list = []
    plus_dm = []
    minus_dm = []

    for i in range(1, len(candles)):
        high = candles[i]["h"]
        low = candles[i]["l"]
        prev_high = candles[i-1]["h"]
        prev_low = candles[i-1]["l"]
        prev_close = candles[i-1]["c"]

        # True Range
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_list.append(tr)

        # Directional Movement
        up_move = high - prev_high
        down_move = prev_low - low

        if up_move > down_move and up_move > 0:
            plus_dm.append(up_move)
        else:
            plus_dm.append(0)

        if down_move > up_move and down_move > 0:
            minus_dm.append(down_move)
        else:
            minus_dm.append(0)

    # Smooth TR, +DM, -DM using Wilder's smoothing
    def wilder_smooth(data: list, period: int) -> list:
        smoothed = [None] * (period - 1)
        smoothed.append(sum(data[:period]))
        for i in range(period, len(data)):
            smoothed.append(smoothed[-1] - (smoothed[-1] / period) + data[i])
        return smoothed

    atr_smooth = wilder_smooth(tr_list, period)
    plus_dm_smooth = wilder_smooth(plus_dm, period)
    minus_dm_smooth = wilder_smooth(minus_dm, period)

    # Calculate +DI and -DI
    plus_di = [None] * len(candles)
    minus_di = [None] * len(candles)
    dx_list = []

    for i in range(period - 1, len(tr_list)):
        idx = i + 1  # Offset for candles array
        if atr_smooth[i] and atr_smooth[i] > 0:
            pdi = 100 * plus_dm_smooth[i] / atr_smooth[i]
            mdi = 100 * minus_dm_smooth[i] / atr_smooth[i]
            plus_di[idx] = pdi
            minus_di[idx] = mdi

            # DX
            if pdi + mdi > 0:
                dx_list.append(100 * abs(pdi - mdi) / (pdi + mdi))
            else:
                dx_list.append(0)

    # Calculate ADX (smoothed DX)
    adx = [None] * len(candles)
    if len(dx_list) >= period:
        first_adx_idx = period * 2 - 1
        adx[first_adx_idx] = sum(dx_list[:period]) / period

        for i in range(period, len(dx_list)):
            idx = i + period
            if idx < len(candles):
                adx[idx] = (adx[idx - 1] * (period - 1) + dx_list[i]) / period

    return {"adx": adx, "plus_di": plus_di, "minus_di": minus_di}


def calculate_obv(candles: list) -> list:
    """
    On-Balance Volume - cumulative volume indicator.
    Rising OBV = accumulation (buying), Falling OBV = distribution (selling)
    """
    if len(candles) < 2:
        return [None] * len(candles)

    obv = [0]  # Start at 0
    for i in range(1, len(candles)):
        if candles[i]["c"] > candles[i-1]["c"]:
            obv.append(obv[-1] + candles[i]["v"])
        elif candles[i]["c"] < candles[i-1]["c"]:
            obv.append(obv[-1] - candles[i]["v"])
        else:
            obv.append(obv[-1])

    return obv


# ============================================================================
# RSI DIVERGENCE DETECTION
# ============================================================================

def detect_array_swing_points(values: list, lookback: int = 3) -> dict:
    """
    Detect swing highs and lows in a 1D numeric array (e.g. RSI values).

    Args:
        values: List of numeric values (may contain None for warmup period)
        lookback: Bars on each side to confirm a swing (default: 3)

    Returns:
        {"swing_highs": [(idx, value), ...],
         "swing_lows": [(idx, value), ...]}
    """
    if len(values) < lookback * 2 + 1:
        return {"swing_highs": [], "swing_lows": []}

    swing_highs = []
    swing_lows = []

    for i in range(lookback, len(values) - lookback):
        if values[i] is None:
            continue

        # Check for swing high
        is_high = True
        for j in range(i - lookback, i + lookback + 1):
            if j != i and (values[j] is None or values[j] >= values[i]):
                is_high = False
                break
        if is_high:
            swing_highs.append((i, values[i]))

        # Check for swing low
        is_low = True
        for j in range(i - lookback, i + lookback + 1):
            if j != i and (values[j] is None or values[j] <= values[i]):
                is_low = False
                break
        if is_low:
            swing_lows.append((i, values[i]))

    return {"swing_highs": swing_highs, "swing_lows": swing_lows}


def _score_divergence(bars_ago: int, rsi_delta: float, span_bars: int, report_window: int = 50) -> tuple:
    """
    Score a divergence on recency, RSI magnitude, and span.

    Returns:
        (score: int, strength: str)
    """
    # Recency: 0-40 pts — more recent = higher score
    recency = max(0, 40 * (1 - bars_ago / report_window))

    # RSI magnitude: 0-35 pts — larger RSI delta = stronger signal (caps at delta=35)
    magnitude = min(35, rsi_delta * 1.0)

    # Span: 0-25 pts — peaks around 25 bars, triangular approximation
    span = max(0, 25 * (1 - abs(span_bars - 25) / 50))

    score = int(recency + magnitude + span)
    if score >= 70:
        strength = "strong"
    elif score >= 40:
        strength = "moderate"
    else:
        strength = "weak"

    return score, strength


def detect_rsi_divergences(
    candles: list,
    rsi: list,
    scan_window: int = 100,
    report_window: int = 50,
    match_tolerance: int = 5
) -> list:
    """
    Detect RSI divergences by comparing price swing points to RSI swing points.

    Args:
        candles: Full list of OHLCV candle dicts
        rsi: Full RSI array (same length as candles)
        scan_window: How far back to look for swing points (default: 100)
        report_window: Only report divergences completing within this many bars (default: 50)
        match_tolerance: +/- bars to match a price swing to an RSI swing (default: 5)

    Returns:
        List of divergence dicts sorted by score descending.
    """
    n = len(candles)
    if n < scan_window:
        scan_window = n

    offset = n - scan_window

    # Detect price swings on the scan window
    price_swings = detect_swing_points(candles[offset:], lookback=5)
    # Detect RSI swings on the scan window
    rsi_swings = detect_array_swing_points(rsi[offset:], lookback=3)

    def _match_swings(price_pts, rsi_pts):
        """Match price swing points to nearest RSI swing points within tolerance."""
        matched = []
        for p_idx, p_val, _ts in price_pts:
            best = None
            best_dist = match_tolerance + 1
            for r_idx, r_val in rsi_pts:
                dist = abs(p_idx - r_idx)
                if dist <= match_tolerance and dist < best_dist:
                    best = (r_idx, r_val)
                    best_dist = dist
            if best:
                matched.append((p_idx, p_val, best[0], best[1]))
        return matched

    matched_highs = _match_swings(price_swings["swing_highs"], rsi_swings["swing_highs"])
    matched_lows = _match_swings(price_swings["swing_lows"], rsi_swings["swing_lows"])

    divergences = []

    # Check consecutive matched swing highs for bearish divergences
    for i in range(1, len(matched_highs)):
        p_idx_a, p_val_a, r_idx_a, r_val_a = matched_highs[i - 1]
        p_idx_b, p_val_b, r_idx_b, r_val_b = matched_highs[i]

        bars_ago = scan_window - 1 - p_idx_b
        span = p_idx_b - p_idx_a

        if bars_ago >= report_window:
            continue

        div_type = None
        if p_val_b > p_val_a and r_val_b < r_val_a:
            div_type = "bearish"
            label = "Regular Bearish"
        elif p_val_b < p_val_a and r_val_b > r_val_a:
            div_type = "hidden_bearish"
            label = "Hidden Bearish"

        if div_type:
            rsi_delta = abs(r_val_b - r_val_a)
            score, strength = _score_divergence(bars_ago, rsi_delta, span, report_window)
            divergences.append({
                "type": div_type,
                "label": label,
                "price_points": [(p_idx_a + offset, round(p_val_a, 2)),
                                 (p_idx_b + offset, round(p_val_b, 2))],
                "rsi_points": [(r_idx_a + offset, round(r_val_a, 2)),
                               (r_idx_b + offset, round(r_val_b, 2))],
                "bars_ago": bars_ago,
                "rsi_delta": round(rsi_delta, 1),
                "span_bars": span,
                "score": score,
                "strength": strength,
                "timestamp": candles[p_idx_b + offset]["t"]
            })

    # Check consecutive matched swing lows for bullish divergences
    for i in range(1, len(matched_lows)):
        p_idx_a, p_val_a, r_idx_a, r_val_a = matched_lows[i - 1]
        p_idx_b, p_val_b, r_idx_b, r_val_b = matched_lows[i]

        bars_ago = scan_window - 1 - p_idx_b
        span = p_idx_b - p_idx_a

        if bars_ago >= report_window:
            continue

        div_type = None
        if p_val_b < p_val_a and r_val_b > r_val_a:
            div_type = "bullish"
            label = "Regular Bullish"
        elif p_val_b > p_val_a and r_val_b < r_val_a:
            div_type = "hidden_bullish"
            label = "Hidden Bullish"

        if div_type:
            rsi_delta = abs(r_val_b - r_val_a)
            score, strength = _score_divergence(bars_ago, rsi_delta, span, report_window)
            divergences.append({
                "type": div_type,
                "label": label,
                "price_points": [(p_idx_a + offset, round(p_val_a, 2)),
                                 (p_idx_b + offset, round(p_val_b, 2))],
                "rsi_points": [(r_idx_a + offset, round(r_val_a, 2)),
                               (r_idx_b + offset, round(r_val_b, 2))],
                "bars_ago": bars_ago,
                "rsi_delta": round(rsi_delta, 1),
                "span_bars": span,
                "score": score,
                "strength": strength,
                "timestamp": candles[p_idx_b + offset]["t"]
            })

    # Deduplicate: if two divergences of the same type share a swing point, keep higher score
    seen = {}
    deduped = []
    for d in sorted(divergences, key=lambda x: x["score"], reverse=True):
        key = (d["type"], tuple(d["price_points"][1]))
        if key not in seen:
            seen[key] = True
            deduped.append(d)

    return sorted(deduped, key=lambda x: x["score"], reverse=True)


# ============================================================================
# SUPPORT/RESISTANCE DETECTION
# ============================================================================

def detect_swing_points(candles: list, lookback: int = 5) -> dict:
    """
    Detect swing highs (local maxima) and swing lows (local minima).

    A swing high is a candle whose high is greater than all highs within
    `lookback` bars on each side. Same logic for swing lows with lows.

    Args:
        candles: List of OHLCV dicts with keys t, o, h, l, c, v
        lookback: Number of bars on each side to check (default: 5)

    Returns:
        {"swing_highs": [(idx, price, timestamp), ...],
         "swing_lows": [(idx, price, timestamp), ...]}
    """
    if len(candles) < lookback * 2 + 1:
        return {"swing_highs": [], "swing_lows": []}

    swing_highs = []
    swing_lows = []

    for i in range(lookback, len(candles) - lookback):
        current = candles[i]

        # Check for swing high
        is_swing_high = True
        for j in range(i - lookback, i + lookback + 1):
            if j != i and candles[j]["h"] >= current["h"]:
                is_swing_high = False
                break

        if is_swing_high:
            swing_highs.append((i, current["h"], current["t"]))

        # Check for swing low
        is_swing_low = True
        for j in range(i - lookback, i + lookback + 1):
            if j != i and candles[j]["l"] <= current["l"]:
                is_swing_low = False
                break

        if is_swing_low:
            swing_lows.append((i, current["l"], current["t"]))

    return {"swing_highs": swing_highs, "swing_lows": swing_lows}


def cluster_price_levels(price_points: list, tolerance_pct: float = 0.5) -> list:
    """
    Cluster nearby price levels into S/R zones.

    Algorithm: Sort by price, merge adjacent points within tolerance.

    Args:
        price_points: List of (idx, price, timestamp) tuples
        tolerance_pct: Percentage tolerance for clustering (default: 0.5%)

    Returns:
        [{"price": avg, "touches": count, "timestamps": [...]}, ...]
    """
    if not price_points:
        return []

    # Sort by price
    sorted_points = sorted(price_points, key=lambda x: x[1])

    clusters = []
    current_cluster = {
        "prices": [sorted_points[0][1]],
        "timestamps": [sorted_points[0][2]]
    }

    for i in range(1, len(sorted_points)):
        _, price, timestamp = sorted_points[i]
        cluster_avg = sum(current_cluster["prices"]) / len(current_cluster["prices"])

        # Check if within tolerance of cluster average
        tolerance = cluster_avg * (tolerance_pct / 100)

        if abs(price - cluster_avg) <= tolerance:
            # Add to current cluster
            current_cluster["prices"].append(price)
            current_cluster["timestamps"].append(timestamp)
        else:
            # Finalize current cluster and start new one
            clusters.append({
                "price": sum(current_cluster["prices"]) / len(current_cluster["prices"]),
                "touches": len(current_cluster["prices"]),
                "timestamps": current_cluster["timestamps"]
            })
            current_cluster = {
                "prices": [price],
                "timestamps": [timestamp]
            }

    # Don't forget the last cluster
    clusters.append({
        "price": sum(current_cluster["prices"]) / len(current_cluster["prices"]),
        "touches": len(current_cluster["prices"]),
        "timestamps": current_cluster["timestamps"]
    })

    return clusters


def calculate_support_resistance(
    candles: list,
    current_price: float,
    lookback: int = 5,
    tolerance_pct: float = 0.5,
    min_touches: int = 2,
    resample_factor: int = 6
) -> dict:
    """
    Calculate support and resistance levels by resampling and detecting swing points.

    Flow:
    1. Resample smaller timeframe candles to larger (e.g., 4h → daily)
    2. Detect swing highs/lows
    3. Cluster into S/R zones
    4. Filter by min_touches
    5. Calculate distance from current price

    Args:
        candles: List of OHLCV dicts (e.g., 4h candles)
        current_price: Current price for distance calculation
        lookback: Bars on each side for swing detection (default: 5)
        tolerance_pct: Clustering tolerance percentage (default: 0.5%)
        min_touches: Minimum touches to qualify as S/R (default: 2)
        resample_factor: Aggregation factor (default: 6, i.e., 6x4h=1d)

    Returns:
        Dict with support_levels, resistance_levels, nearest_support,
        nearest_resistance, and metadata
    """
    if len(candles) < resample_factor * (lookback * 2 + 1):
        return {
            "support_levels": [],
            "resistance_levels": [],
            "nearest_support": None,
            "nearest_resistance": None,
            "current_price": current_price,
            "risk_reward_to_levels": None,
            "meta": {
                "timeframe_source": "4h",
                "timeframe_analyzed": "daily",
                "candles_analyzed": len(candles),
                "swing_lookback": lookback,
                "error": "Insufficient data for S/R analysis"
            }
        }

    # Step 1: Resample to higher timeframe
    resampled = aggregate_candles(candles, resample_factor)

    # Step 2: Detect swing points
    swing_points = detect_swing_points(resampled, lookback)

    # Step 3: Cluster highs → resistance, lows → support
    resistance_clusters = cluster_price_levels(swing_points["swing_highs"], tolerance_pct)
    support_clusters = cluster_price_levels(swing_points["swing_lows"], tolerance_pct)

    # Step 4: Filter by min_touches and add strength classification
    def classify_strength(touches: int) -> str:
        return "strong" if touches >= 3 else "moderate"

    resistance_levels = []
    for cluster in resistance_clusters:
        if cluster["touches"] >= min_touches:
            distance_pct = ((cluster["price"] - current_price) / current_price) * 100
            resistance_levels.append({
                "price": round(cluster["price"], 2),
                "touches": cluster["touches"],
                "strength": classify_strength(cluster["touches"]),
                "distance_pct": round(distance_pct, 2)
            })

    support_levels = []
    for cluster in support_clusters:
        if cluster["touches"] >= min_touches:
            distance_pct = ((cluster["price"] - current_price) / current_price) * 100
            support_levels.append({
                "price": round(cluster["price"], 2),
                "touches": cluster["touches"],
                "strength": classify_strength(cluster["touches"]),
                "distance_pct": round(distance_pct, 2)
            })

    # Sort: resistance by price ascending (nearest first), support by price descending (nearest first)
    resistance_levels.sort(key=lambda x: x["price"])
    support_levels.sort(key=lambda x: x["price"], reverse=True)

    # Step 5: Find nearest levels
    nearest_resistance = None
    for level in resistance_levels:
        if level["price"] > current_price:
            nearest_resistance = level["price"]
            break

    nearest_support = None
    for level in support_levels:
        if level["price"] < current_price:
            nearest_support = level["price"]
            break

    # Step 6: Calculate risk/reward to levels
    # Risk = distance to support (downside), Reward = distance to resistance (upside)
    # Ratio < 1 = closer to support (good entry), Ratio > 1 = closer to resistance (risky entry)
    risk_reward = None
    if nearest_support and nearest_resistance:
        distance_to_support = current_price - nearest_support
        distance_to_resistance = nearest_resistance - current_price
        # Validate both distances are positive (price is between S/R levels)
        if distance_to_support > 0 and distance_to_resistance > 0:
            risk_reward = round(distance_to_support / distance_to_resistance, 2)

    return {
        "support_levels": support_levels,
        "resistance_levels": resistance_levels,
        "nearest_support": nearest_support,
        "nearest_resistance": nearest_resistance,
        "current_price": round(current_price, 2),
        "risk_reward_to_levels": risk_reward,
        "meta": {
            "timeframe_source": "4h",
            "timeframe_analyzed": "daily",
            "candles_analyzed": len(candles),
            "resampled_candles": len(resampled),
            "swing_lookback": lookback,
            "swing_highs_found": len(swing_points["swing_highs"]),
            "swing_lows_found": len(swing_points["swing_lows"])
        }
    }


# ============================================================================
# ANALYSIS & REPORTING
# ============================================================================

def analyze_symbol(symbol: str, timeframe: str = "4h", indicators: list = None) -> dict:
    """Run technical analysis on a symbol."""
    if indicators is None:
        indicators = ["rsi", "macd", "bb", "sma", "atr", "adx", "obv", "sr"]

    # Use more history for higher timeframes to get enough candles for indicators
    days_lookup = {"1w": 1500, "1M": 6000, "1d": 540}
    days = days_lookup.get(timeframe, 90)

    candles = get_cached_data(symbol, timeframe, days=days)

    if not candles:
        return {"error": f"No data for {symbol} ({timeframe}). Run 'download' first."}

    closes = [c["c"] for c in candles]
    latest = candles[-1]

    result = {
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "latest_price": latest["c"],
        "latest_time": from_timestamp_utc(latest["t"]).strftime("%Y-%m-%d %H:%M UTC"),
        "candles_analyzed": len(candles),
        "indicators": {}
    }

    # Calculate requested indicators
    if "rsi" in indicators:
        rsi = calculate_rsi(closes)
        result["indicators"]["RSI_14"] = round(rsi[-1], 2) if rsi[-1] else None

        # RSI Divergence detection
        divergences = detect_rsi_divergences(candles, rsi)
        result["indicators"]["RSI_divergences"] = divergences
        result["indicators"]["RSI_primary_divergence"] = divergences[0] if divergences else None

    if "sma" in indicators:
        sma_20 = calculate_sma(closes, 20)
        sma_50 = calculate_sma(closes, 50)
        sma_200 = calculate_sma(closes, 200)
        result["indicators"]["SMA_20"] = round(sma_20[-1], 2) if sma_20[-1] else None
        result["indicators"]["SMA_50"] = round(sma_50[-1], 2) if sma_50[-1] else None
        result["indicators"]["SMA_200"] = round(sma_200[-1], 2) if sma_200[-1] else None

    if "macd" in indicators:
        macd = calculate_macd(closes)
        result["indicators"]["MACD"] = round(macd["macd"][-1], 4) if macd["macd"][-1] else None
        result["indicators"]["MACD_Signal"] = round(macd["signal"][-1], 4) if macd["signal"][-1] else None
        result["indicators"]["MACD_Histogram"] = round(macd["histogram"][-1], 4) if macd["histogram"][-1] else None

    if "bb" in indicators:
        bb = calculate_bollinger_bands(closes)
        result["indicators"]["BB_Upper"] = round(bb["upper"][-1], 2) if bb["upper"][-1] else None
        result["indicators"]["BB_Middle"] = round(bb["middle"][-1], 2) if bb["middle"][-1] else None
        result["indicators"]["BB_Lower"] = round(bb["lower"][-1], 2) if bb["lower"][-1] else None

    if "atr" in indicators:
        atr = calculate_atr(candles)
        result["indicators"]["ATR_14"] = round(atr[-1], 4) if atr[-1] else None

    if "adx" in indicators:
        adx_data = calculate_adx(candles)
        result["indicators"]["ADX_14"] = round(adx_data["adx"][-1], 2) if adx_data["adx"][-1] else None
        result["indicators"]["Plus_DI"] = round(adx_data["plus_di"][-1], 2) if adx_data["plus_di"][-1] else None
        result["indicators"]["Minus_DI"] = round(adx_data["minus_di"][-1], 2) if adx_data["minus_di"][-1] else None

    if "obv" in indicators:
        obv = calculate_obv(candles)
        result["indicators"]["OBV"] = round(obv[-1], 0) if obv[-1] is not None else None

    if "sr" in indicators:
        sr_data = calculate_support_resistance(candles, latest["c"])
        result["indicators"]["support_resistance"] = sr_data

    return result


def generate_report(symbol: str, timeframe: str = "4h") -> str:
    """Generate a full TA report for Titan Brain consumption."""
    analysis = analyze_symbol(symbol, timeframe)

    if "error" in analysis:
        return analysis["error"]

    ind = analysis["indicators"]
    price = analysis["latest_price"]

    # Determine signals
    signals = []

    # RSI Signal — Divergence is primary, OB/OS is secondary
    rsi = ind.get("RSI_14")
    primary_div = ind.get("RSI_primary_divergence")

    if primary_div and primary_div["strength"] != "weak":
        div = primary_div
        signals.append(
            f"RSI DIVERGENCE: {div['label']} (score {div['score']}/100, "
            f"{div['strength']}) — {div['bars_ago']} bars ago, "
            f"RSI delta {div['rsi_delta']:.1f}"
        )
        # OB/OS as reinforcing context
        if rsi and rsi > 70:
            if div["type"] in ("bearish", "hidden_bearish"):
                signals.append(f"  + RSI Overbought ({rsi}) — reinforces bearish divergence")
            else:
                signals.append(f"  + RSI Overbought ({rsi})")
        elif rsi and rsi < 30:
            if div["type"] in ("bullish", "hidden_bullish"):
                signals.append(f"  + RSI Oversold ({rsi}) — reinforces bullish divergence")
            else:
                signals.append(f"  + RSI Oversold ({rsi})")
    elif rsi:
        if rsi > 70:
            signals.append(f"RSI OVERBOUGHT ({rsi})")
        elif rsi < 30:
            signals.append(f"RSI OVERSOLD ({rsi})")
        else:
            signals.append(f"RSI Neutral ({rsi})")

    # MACD Signal
    macd_hist = ind.get("MACD_Histogram")
    if macd_hist:
        if macd_hist > 0:
            signals.append("MACD Bullish (histogram +)")
        else:
            signals.append("MACD Bearish (histogram -)")

    # Bollinger Band Position
    bb_upper = ind.get("BB_Upper")
    bb_lower = ind.get("BB_Lower")
    if bb_upper and bb_lower:
        if price >= bb_upper:
            signals.append("Price at BB Upper (resistance)")
        elif price <= bb_lower:
            signals.append("Price at BB Lower (support)")

    # Trend (SMA)
    sma_50 = ind.get("SMA_50")
    sma_200 = ind.get("SMA_200")
    if sma_50 and sma_200:
        if sma_50 > sma_200:
            signals.append("Golden Cross (SMA50 > SMA200)")
        else:
            signals.append("Death Cross (SMA50 < SMA200)")

    # ADX Signal (trend strength)
    adx = ind.get("ADX_14")
    plus_di = ind.get("Plus_DI")
    minus_di = ind.get("Minus_DI")
    if adx:
        if adx > 25:
            if plus_di and minus_di:
                direction = "Bullish" if plus_di > minus_di else "Bearish"
                signals.append(f"ADX Strong Trend ({adx}) — {direction}")
            else:
                signals.append(f"ADX Strong Trend ({adx})")
        else:
            signals.append(f"ADX Weak/No Trend ({adx})")

    # Support/Resistance Signal
    sr = ind.get("support_resistance", {})
    nearest_support = sr.get("nearest_support")
    nearest_resistance = sr.get("nearest_resistance")
    if nearest_support and nearest_resistance:
        rr = sr.get("risk_reward_to_levels")
        signals.append(f"Support: {fmt_price(nearest_support)} | Resistance: {fmt_price(nearest_resistance)}")
        if rr is not None:
            if rr < 1:
                signals.append(f"R:R to levels = 1:{rr:.1f} — Closer to support (potential bounce zone)")
            else:
                signals.append(f"R:R to levels = {rr:.1f}:1 — Closer to resistance (potential rejection zone)")
    elif nearest_support:
        signals.append(f"Support: {fmt_price(nearest_support)} | No resistance detected above")
    elif nearest_resistance:
        signals.append(f"Resistance: {fmt_price(nearest_resistance)} | No support detected below")

    # Build report
    report = f"""
================================================================================
TITAN TA REPORT: {analysis['symbol']} ({analysis['timeframe']})
================================================================================
Generated: {utc_now().strftime('%Y-%m-%d %H:%M UTC')}
Data Points: {analysis['candles_analyzed']} candles
Latest Price: ${price:,.2f} ({analysis['latest_time']})

INDICATORS
----------
RSI (14):        {fmt_num(ind.get('RSI_14'))}
RSI Divergence:  {_format_divergence_line(ind.get('RSI_primary_divergence'))}
MACD:            {fmt_num(ind.get('MACD'), 4)} | Signal: {fmt_num(ind.get('MACD_Signal'), 4)} | Hist: {fmt_num(ind.get('MACD_Histogram'), 4)}
Bollinger Bands: Upper {fmt_price(ind.get('BB_Upper'))} | Mid {fmt_price(ind.get('BB_Middle'))} | Lower {fmt_price(ind.get('BB_Lower'))}
SMA:             20: {fmt_price(ind.get('SMA_20'))} | 50: {fmt_price(ind.get('SMA_50'))} | 200: {fmt_price(ind.get('SMA_200'))}
ATR (14):        {fmt_price(ind.get('ATR_14'), 4)}
ADX (14):        {fmt_num(ind.get('ADX_14'))} | +DI: {fmt_num(ind.get('Plus_DI'))} | -DI: {fmt_num(ind.get('Minus_DI'))}
OBV:             {fmt_num(ind.get('OBV'), 0)}
S/R:             Support {fmt_price(ind.get('support_resistance', {}).get('nearest_support'))} | Resistance {fmt_price(ind.get('support_resistance', {}).get('nearest_resistance'))}

SIGNALS
-------
""" + "\n".join(f"• {s}" for s in signals) + """

================================================================================
"""
    return report


# ============================================================================
# CLI INTERFACE
# ============================================================================

def cmd_download(args):
    """Download/refresh OHLCV data for a symbol."""
    symbol = args.symbol.upper()
    timeframe = args.timeframe

    # Calculate how many candles we need
    candles_needed, fetch_mode = calculate_candles_needed(symbol, timeframe)
    cached_count = get_cached_candle_count(symbol, timeframe)

    # --full flag forces full backfill to timeframe minimum regardless of cache
    target_count = get_default_candle_count(timeframe)
    if args.full:
        candles_needed = target_count
        fetch_mode = "full_backfill"

    # Auto-backfill if cache is below the timeframe minimum
    elif fetch_mode == "incremental" and cached_count < target_count:
        candles_needed = target_count
        fetch_mode = "full_backfill"

    if fetch_mode == "initial":
        print(f"Downloading {symbol} ({timeframe}) — Initial fetch of {candles_needed} bars...")
    elif fetch_mode == "full_backfill":
        print(f"Downloading {symbol} ({timeframe}) — Full backfill of {candles_needed} bars...")
        print(f"  Existing cache: {cached_count} candles (will be extended)")
    else:
        print(f"Downloading {symbol} ({timeframe}) — Incremental update ({candles_needed} new bars)...")
        print(f"  Existing cache: {cached_count} candles")

    # Check if refresh is needed (skip for force, initial, or full_backfill)
    if not args.force and fetch_mode == "incremental" and not should_refresh(symbol, timeframe):
        last = get_last_update(symbol, timeframe)
        print(f"Data is fresh (last update: {last.strftime('%Y-%m-%d %H:%M UTC')})")
        print(f"Use --force to re-download anyway, or --full to backfill to {target_count} bars.")
        return

    candles, source = fetch_candles_from_api(symbol, timeframe, candles_needed)

    if candles:
        save_candles(symbol, timeframe, candles)

        # Get updated total count
        new_total = get_cached_candle_count(symbol, timeframe)

        if fetch_mode == "initial":
            print(f"✓ Saved {len(candles)} candles for {symbol} ({timeframe})")
        elif fetch_mode == "full_backfill":
            print(f"✓ Backfilled {len(candles)} candles, total now: {new_total}")
        else:
            print(f"✓ Added {len(candles)} candles, total now: {new_total}")

        print(f"  Source: {source}")

        # Show date range from cache (full range)
        cached = get_cached_data(symbol, timeframe, days=9999)
        if cached:
            earliest = from_timestamp_utc(cached[0]["t"])
            latest = from_timestamp_utc(cached[-1]["t"])
            days_of_data = (latest - earliest).days
            print(f"  Date range: {earliest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')} ({days_of_data} days)")
    else:
        print(f"No data received for {symbol}.")
        print("Tried: Binance Futures, Hyperliquid, Coinbase, CoinMarketCap")
        print("Check symbol exists or add CMC API key to .env")


def cmd_analyze(args):
    """Run technical analysis on a symbol."""
    indicators = args.indicators.split(",") if args.indicators else None
    result = analyze_symbol(args.symbol, args.timeframe, indicators)
    print(json.dumps(result, indent=2))


def cmd_report(args):
    """Generate a full TA report."""
    report = generate_report(args.symbol, args.timeframe)
    print(report)


def cmd_list(args):
    """List all cached symbols."""
    symbols = list_cached_symbols()

    if not symbols:
        print("No cached data. Use 'download' to fetch data.")
        return

    print(f"{'Symbol':<10} {'Timeframe':<10} {'Earliest':<12} {'Latest':<12} {'Candles':<10}")
    print("-" * 54)
    for s in symbols:
        print(f"{s['symbol']:<10} {s['timeframe']:<10} {s['earliest']:<12} {s['latest']:<12} {s['candles']:<10}")


def main():
    # Initialize database
    init_db()

    parser = argparse.ArgumentParser(
        description="Titan Terminal v3 — Technical Analysis Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Download command
    dl_parser = subparsers.add_parser("download", help="Download OHLCV data")
    dl_parser.add_argument("symbol", help="Symbol to download (e.g., BTC, ETH)")
    dl_parser.add_argument("--timeframe", "-t", default="4h",
                          choices=SUPPORTED_TIMEFRAMES,
                          help="Candle timeframe (default: 4h)")
    dl_parser.add_argument("--force", "-f", action="store_true",
                          help="Force refresh even if data is fresh")
    dl_parser.add_argument("--full", action="store_true",
                          help="Force full fetch (backfill existing cache)")
    dl_parser.set_defaults(func=cmd_download)

    # Analyze command
    an_parser = subparsers.add_parser("analyze", help="Run technical analysis")
    an_parser.add_argument("symbol", help="Symbol to analyze")
    an_parser.add_argument("--timeframe", "-t", default="4h",
                          help="Timeframe to analyze (default: 4h)")
    an_parser.add_argument("--indicators", "-i",
                          help="Comma-separated indicators (rsi,macd,bb,sma,atr,adx,obv,sr)")
    an_parser.set_defaults(func=cmd_analyze)

    # Report command
    rp_parser = subparsers.add_parser("report", help="Generate full TA report")
    rp_parser.add_argument("symbol", help="Symbol for report")
    rp_parser.add_argument("--timeframe", "-t", default="4h",
                          help="Timeframe for report (default: 4h)")
    rp_parser.set_defaults(func=cmd_report)

    # List command
    ls_parser = subparsers.add_parser("list", help="List cached symbols")
    ls_parser.set_defaults(func=cmd_list)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
