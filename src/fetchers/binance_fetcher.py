'''
Binance USDⓈ-M Perpetual Futures Data Fetcher
=============================================

Fetches OHLCV data and funding rates from Binance Futures via CCXT.
Primary OHLCV source in the Titan TA fallback chain.

STANDALONE USAGE:
================
    # OHLCV data
    python3 src/fetchers/binance_fetcher.py BTC --timeframe 4h --candles 100

    # Funding rates
    python3 src/fetchers/binance_fetcher.py ETH --funding --days 7

PROGRAMMATIC USAGE:
==================
    from src.fetchers.binance_fetcher import fetch_from_binance, fetch_binance_funding_rates, get_binance_funding_summary

    # List return (for indicators.py integration)
    candles = fetch_from_binance('BTC', '4h', 500)

    # Funding rates
    rates = fetch_binance_funding_rates('BTC', limit=100)

    # Funding summary for squeeze detector
    summary = get_binance_funding_summary('BTC', days=7)

API DETAILS:
============
    Exchange: Binance USDⓈ-M Perpetual Futures (binanceusdm)
    OHLCV: 1500 candles/batch via CCXT (no auth required)
    Funding: fetch_funding_rate_history (no auth required)
    CCXT Symbol Format: BTC/USDT:USDT

TIMEFRAMES:
===========
    1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
'''

import argparse
import time
from datetime import datetime, timezone

import ccxt

# ============================================================================
# CONFIGURATION
# ============================================================================

BATCH_SIZE = 1500  # Max candles per CCXT fetch_ohlcv call
BATCH_DELAY = 0.3  # Seconds between batches

# Timeframe to milliseconds (for pagination calculations)
TIMEFRAME_MS = {
    "1m": 60000, "3m": 180000, "5m": 300000, "15m": 900000, "30m": 1800000,
    "1h": 3600000, "2h": 7200000, "4h": 14400000, "6h": 21600000, "8h": 28800000,
    "12h": 43200000, "1d": 86400000, "3d": 259200000, "1w": 604800000, "1M": 2592000000
}

SUPPORTED_TIMEFRAMES = list(TIMEFRAME_MS.keys())

# Funding rate extreme threshold (annualized >100% or <-100% is extreme)
FUNDING_EXTREME_ANNUALIZED = 1.0  # 100%

# ============================================================================
# EXCHANGE SINGLETON
# ============================================================================

_exchange = None


def _get_exchange() -> ccxt.binanceusdm:
    """Get or create the CCXT binanceusdm exchange instance."""
    global _exchange
    if _exchange is None:
        _exchange = ccxt.binanceusdm({
            'enableRateLimit': True,
        })
    return _exchange


# ============================================================================
# SYMBOL NORMALIZATION
# ============================================================================

def normalize_symbol(symbol: str) -> str:
    """
    Normalize to CCXT binanceusdm format: 'BTC/USDT:USDT'
    Accepts: BTC, ETH, BTCUSDT, BTC/USDT, BTC/USDT:USDT
    """
    symbol = symbol.upper().strip().replace("-", "/")
    # Already in correct format
    if symbol.endswith(":USDT"):
        return symbol
    # Strip any USDT suffixes to get the base
    symbol = symbol.replace("/USDT", "").replace("USDT", "")
    return f"{symbol}/USDT:USDT"


# ============================================================================
# OHLCV FETCHING
# ============================================================================

def fetch_from_binance(symbol: str, timeframe: str, candle_count: int = 500) -> list:
    """
    Fetch OHLCV candles from Binance Futures via CCXT.
    Primary integration point for indicators.py.

    Args:
        symbol: Token symbol (e.g., 'BTC', 'ETH', 'BTCUSDT', 'BTC/USDT:USDT')
        timeframe: Candle timeframe (e.g., '4h', '1d')
        candle_count: Number of candles to fetch (batches automatically if > 1500)

    Returns:
        List of dicts with keys: t, o, h, l, c, v (timestamps in milliseconds)
        Empty list on failure — never raises.
    """
    if timeframe not in SUPPORTED_TIMEFRAMES:
        return []

    ccxt_symbol = normalize_symbol(symbol)
    exchange = _get_exchange()

    try:
        if candle_count <= BATCH_SIZE:
            ohlcv = exchange.fetch_ohlcv(ccxt_symbol, timeframe, limit=candle_count)
            return _convert_ohlcv(ohlcv)
        else:
            return _fetch_batched(exchange, ccxt_symbol, timeframe, candle_count)

    except (ccxt.BadSymbol, ccxt.ExchangeError, ccxt.NetworkError):
        return []
    except Exception:
        return []


def _fetch_batched(exchange: ccxt.binanceusdm, ccxt_symbol: str,
                   timeframe: str, total_candles: int) -> list:
    """
    Fetch more than 1500 candles by paginating backwards using the `since` parameter.
    """
    tf_ms = TIMEFRAME_MS.get(timeframe, 14400000)
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    all_candles = []
    remaining = total_candles
    current_end_ms = now_ms

    while remaining > 0:
        batch_size = min(remaining, BATCH_SIZE)
        since_ms = current_end_ms - (batch_size * tf_ms)

        try:
            ohlcv = exchange.fetch_ohlcv(
                ccxt_symbol, timeframe,
                since=since_ms,
                limit=batch_size
            )
        except (ccxt.BadSymbol, ccxt.ExchangeError, ccxt.NetworkError):
            break
        except Exception:
            break

        if not ohlcv:
            break

        batch = _convert_ohlcv(ohlcv)
        all_candles = batch + all_candles  # Prepend (older data first)
        remaining -= len(batch)

        # Move window back to just before this batch's earliest candle
        current_end_ms = ohlcv[0][0] - 1

        if remaining > 0:
            time.sleep(BATCH_DELAY)

    # Deduplicate and sort ascending
    seen = set()
    unique = []
    for c in all_candles:
        if c["t"] not in seen:
            seen.add(c["t"])
            unique.append(c)

    unique.sort(key=lambda x: x["t"])
    return unique


def _convert_ohlcv(ohlcv: list) -> list:
    """Convert CCXT OHLCV rows [[ts, o, h, l, c, v], ...] to internal format."""
    return [
        {
            "t": int(c[0]),
            "o": float(c[1]),
            "h": float(c[2]),
            "l": float(c[3]),
            "c": float(c[4]),
            "v": float(c[5]),
        }
        for c in ohlcv
        if c[1] is not None  # Skip candles with null OHLCV (Binance edge case)
    ]


# ============================================================================
# FUNDING RATE FETCHING
# ============================================================================

def fetch_binance_funding_rates(symbol: str, limit: int = 100) -> list:
    """
    Fetch historical funding rates from Binance Futures.

    Args:
        symbol: Token symbol (e.g., 'BTC', 'BTCUSDT')
        limit: Number of records to fetch

    Returns:
        List of dicts with keys: symbol, fundingTime, fundingRate
        Empty list on failure — never raises.
    """
    ccxt_symbol = normalize_symbol(symbol)
    exchange = _get_exchange()

    try:
        history = exchange.fetch_funding_rate_history(ccxt_symbol, limit=limit)
        # CCXT returns list of dicts; normalize to our expected shape
        result = []
        for entry in history:
            result.append({
                "symbol": ccxt_symbol,
                "fundingTime": entry.get("timestamp", 0),
                "fundingRate": entry.get("fundingRate", 0.0),
            })
        return result

    except (ccxt.BadSymbol, ccxt.ExchangeError, ccxt.NetworkError):
        return []
    except Exception:
        return []


def get_binance_funding_summary(symbol: str, days: int = 7) -> dict:
    """
    Return a funding rate summary for the squeeze detector.

    Args:
        symbol: Token symbol
        days: Number of days of history to analyze

    Returns:
        Dict with: avg_rate, latest_rate, annualized_rate, is_extreme, direction
        Empty dict on failure.
    """
    # Funding every 8h = 3 per day
    limit = min(days * 3 + 5, 500)
    rates = fetch_binance_funding_rates(symbol, limit=limit)

    if not rates:
        return {}

    funding_values = [r["fundingRate"] for r in rates if r.get("fundingRate") is not None]

    if not funding_values:
        return {}

    avg_rate = sum(funding_values) / len(funding_values)
    latest_rate = funding_values[-1]
    # Annualized: 3 payments/day × 365 days
    annualized_rate = avg_rate * 3 * 365
    is_extreme = abs(annualized_rate) >= FUNDING_EXTREME_ANNUALIZED
    direction = "long_heavy" if avg_rate > 0 else "short_heavy"

    return {
        "avg_rate": avg_rate,
        "latest_rate": latest_rate,
        "annualized_rate": annualized_rate,
        "is_extreme": is_extreme,
        "direction": direction,
        "sample_count": len(funding_values),
    }


# ============================================================================
# DATAFRAME WRAPPER (CLI use — pandas imported lazily)
# ============================================================================

def fetch_binance_data(symbol: str, timeframe: str, total_candles: int = 500,
                       verbose: bool = True):
    """
    Fetch OHLCV and return as a pandas DataFrame.
    Pandas is imported lazily — only needed for CLI/standalone use.

    Returns:
        pandas.DataFrame with columns: timestamp, open, high, low, close, volume
    """
    import pandas as pd  # Lazy import

    if verbose:
        print(f"\nFetching {total_candles} x {timeframe} candles for {symbol.upper()} from Binance Futures...")

    candles = fetch_from_binance(symbol, timeframe, total_candles)

    if not candles:
        if verbose:
            print(f"No data returned for {symbol}")
        return pd.DataFrame()

    df = pd.DataFrame(candles)
    df['timestamp'] = pd.to_datetime(df['t'], unit='ms', utc=True).dt.tz_localize(None)
    df = df.rename(columns={'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume'})
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    df = df.sort_values('timestamp').reset_index(drop=True)

    if verbose:
        print(f"Fetched {len(df)} candles")
        print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

    return df


def get_funding_rate_df(symbol: str, days: int = 7):
    """
    Get funding rates as a pandas DataFrame.
    Pandas is imported lazily — only needed for CLI/standalone use.

    Returns:
        pandas.DataFrame with columns: timestamp, funding_rate
    """
    import pandas as pd  # Lazy import

    limit = min(days * 3 + 10, 500)
    rates = fetch_binance_funding_rates(symbol, limit=limit)

    if not rates:
        return pd.DataFrame()

    df = pd.DataFrame(rates)
    df['timestamp'] = pd.to_datetime(df['fundingTime'], unit='ms', utc=True).dt.tz_localize(None)
    df['funding_rate'] = df['fundingRate'].astype(float)
    df = df[['timestamp', 'funding_rate']].sort_values('timestamp').reset_index(drop=True)
    return df


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Binance USDⓈ-M Perpetual Futures Data Fetcher (CCXT)"
    )
    parser.add_argument("symbol", help="Token symbol (e.g., BTC, ETH)")
    parser.add_argument("--timeframe", "-t", default="4h",
                        choices=SUPPORTED_TIMEFRAMES,
                        help="Candle timeframe (default: 4h)")
    parser.add_argument("--candles", "-c", type=int, default=200,
                        help="Number of candles to fetch (default: 200)")
    parser.add_argument("--funding", "-f", action="store_true",
                        help="Fetch funding rates instead of OHLCV")
    parser.add_argument("--days", "-d", type=int, default=7,
                        help="Days of funding rate history (default: 7)")
    parser.add_argument("--summary", action="store_true",
                        help="Print funding summary (squeeze detector format)")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress verbose output")

    args = parser.parse_args()

    if args.funding or args.summary:
        if not args.quiet:
            print(f"\nFetching {args.days} days of funding rates for {args.symbol.upper()}...")

        if args.summary:
            summary = get_binance_funding_summary(args.symbol, args.days)
            if not summary:
                print(f"No funding data available for {args.symbol}")
                return
            print(f"\nFunding Summary ({args.symbol.upper()}, {args.days}d):")
            print(f"  Latest Rate:    {summary['latest_rate'] * 100:.4f}%")
            print(f"  Avg Rate:       {summary['avg_rate'] * 100:.4f}%")
            print(f"  Annualized:     {summary['annualized_rate'] * 100:.2f}%")
            print(f"  Direction:      {summary['direction']}")
            print(f"  Extreme:        {'YES ⚠️' if summary['is_extreme'] else 'No'}")
            print(f"  Sample Count:   {summary['sample_count']}")
        else:
            df = get_funding_rate_df(args.symbol, args.days)
            if df.empty:
                print(f"No funding data available for {args.symbol}")
                return
            if not args.quiet:
                print(f"\nFunding Rate Data ({len(df)} records):")
                print(df.to_string(index=False))
                avg = df['funding_rate'].mean()
                latest = df['funding_rate'].iloc[-1]
                annual = avg * 3 * 365 * 100
                print(f"\nSummary:")
                print(f"  Average Rate: {avg * 100:.4f}%")
                print(f"  Latest Rate:  {latest * 100:.4f}%")
                print(f"  Min Rate:     {df['funding_rate'].min() * 100:.4f}%")
                print(f"  Max Rate:     {df['funding_rate'].max() * 100:.4f}%")
                print(f"  Annualized:   {annual:.2f}%")
    else:
        df = fetch_binance_data(
            symbol=args.symbol,
            timeframe=args.timeframe,
            total_candles=args.candles,
            verbose=not args.quiet,
        )

        if df.empty:
            print(f"No data available for {args.symbol}")
            return

        if not args.quiet:
            print(f"\nSample data (last 5 candles):")
            print(df.tail().to_string(index=False))


if __name__ == "__main__":
    main()
