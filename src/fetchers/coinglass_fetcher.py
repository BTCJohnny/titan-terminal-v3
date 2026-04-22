#!/usr/bin/env python3
"""
Coinglass Derivatives Intelligence
====================================
Fetches derivatives data from Coinglass API — funding rates, OI, L/S ratios,
liquidation, options, ETF flows, Fear & Greed, and Coinbase Premium.

API: https://open-api-v4.coinglass.com (Hobbyist plan, 30 req/min)

Available endpoints (Hobbyist tier, 11 total):
    GET /api/futures/liquidation/coin-list                  — Per-coin liquidation totals
    GET /api/option/max-pain                                — Options max pain by expiry
    GET /api/option/info                                    — Options OI, volume, put/call ratio
    GET /api/futures/funding-rate/exchange-list              — Cross-exchange funding rates
    GET /api/futures/open-interest/aggregated-history        — OI history (OHLC)
    GET /api/futures/open-interest/exchange-list             — OI snapshot by exchange
    GET /api/futures/global-long-short-account-ratio/history — Global L/S account ratio
    GET /api/futures/top-long-short-account-ratio/history    — Top trader L/S account ratio
    GET /api/futures/top-long-short-position-ratio/history   — Top trader L/S position ratio
    GET /api/etf/bitcoin/flow-history                       — BTC ETF flow history
    GET /api/index/fear-greed-history                        — Fear & Greed index
    GET /api/coinbase-premium-index                          — Coinbase Premium

Premium endpoints (require upgrade — kept as stubs):
    GET /api/futures/liquidation/map         — Liquidation by price level
    GET /api/futures/liquidation/order       — Individual liquidation events
    GET /api/futures/orderbook/large-limit-order — Large resting orders

Usage:
    python3 src/fetchers/coinglass_fetcher.py --token BTC --price 84000                    # Liquidity report
    python3 src/fetchers/coinglass_fetcher.py --token BTC --derivatives --price 84000      # Full derivatives
    python3 src/fetchers/coinglass_fetcher.py --market                                     # Market pulse
    python3 src/fetchers/coinglass_fetcher.py --scan                                       # Scan all coins
    python3 src/fetchers/coinglass_fetcher.py --token BTC --json                           # Raw JSON
    python3 src/fetchers/coinglass_fetcher.py --token BTC --debug                          # Debug mode
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "signals" / "dashboards"
CG_BASE = "https://open-api-v4.coinglass.com"

# Rate limiting: 30 req/min for Hobbyist plan
_request_timestamps: list[float] = []
RATE_LIMIT = 30
RATE_WINDOW = 60  # seconds

# Add parent for cache imports
sys.path.insert(0, str(PROJECT_ROOT))


def _get_api_key() -> str | None:
    """Load API key from .env or environment."""
    key = os.environ.get("COINGLASS_API_KEY")
    if key:
        return key
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("COINGLASS_API_KEY="):
                val = line.split("=", 1)[1].split("#")[0].strip()
                if val:
                    return val
    return None


def _check_rate_limit():
    """Track and warn on rate limit."""
    now = time.time()
    _request_timestamps[:] = [t for t in _request_timestamps if now - t < RATE_WINDOW]
    if len(_request_timestamps) >= RATE_LIMIT - 2:
        print(f"  ⚠️  Rate limit warning: {len(_request_timestamps)}/{RATE_LIMIT} requests in last 60s",
              file=sys.stderr)
    if len(_request_timestamps) >= RATE_LIMIT:
        wait = RATE_WINDOW - (now - _request_timestamps[0]) + 1
        print(f"  🛑 Rate limit hit. Waiting {wait:.0f}s...", file=sys.stderr)
        time.sleep(wait)
    _request_timestamps.append(now)


def cg_get(endpoint: str, params: dict | None = None, debug: bool = False) -> dict | list | None:
    """
    GET request to Coinglass API.

    Returns parsed JSON data (unwrapped from {"code":"0","data":...}), or None on error.
    """
    api_key = _get_api_key()
    if not api_key:
        print("  ⚠️  COINGLASS_API_KEY not set. Add it to .env", file=sys.stderr)
        return None

    _check_rate_limit()

    url = f"{CG_BASE}{endpoint}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        if query:
            url = f"{url}?{query}"

    try:
        req = urllib.request.Request(
            url,
            headers={"CG-API-KEY": api_key, "Accept": "application/json"},
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            data = json.loads(raw)

            if debug:
                print(f"\n  [DEBUG] GET {url}", file=sys.stderr)
                print(f"  [DEBUG] Response: {json.dumps(data, indent=2)[:2000]}", file=sys.stderr)

            if isinstance(data, dict):
                code = data.get("code", "")
                if str(code) != "0":
                    msg = data.get("msg", "Unknown error")
                    print(f"  ⚠️  Coinglass API error: {msg} (code={code})", file=sys.stderr)
                    return None
                return data.get("data")
            return data

    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()[:200]
        except Exception:
            pass
        if e.code == 429:
            print(f"  Rate limited (429). Waiting 60s then retrying...", file=sys.stderr)
            time.sleep(60)
            try:
                req2 = urllib.request.Request(
                    url,
                    headers={"CG-API-KEY": api_key, "Accept": "application/json"},
                    method="GET"
                )
                with urllib.request.urlopen(req2, timeout=30) as resp2:
                    raw2 = resp2.read().decode()
                    data2 = json.loads(raw2)
                    if isinstance(data2, dict) and str(data2.get("code", "")) == "0":
                        return data2.get("data")
                    return data2
            except Exception as retry_err:
                print(f"  Retry failed: {retry_err}", file=sys.stderr)
                return None
        print(f"  Coinglass HTTP {e.code}: {body}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  Coinglass API error: {e}", file=sys.stderr)
        return None


# ===========================================================================
# Cache helpers
# ===========================================================================

def _cache_check(tool_name: str, token: str, params: dict) -> tuple[bool, dict | list | None]:
    """Check nansen_cache for a stored response."""
    try:
        from src.storage.nansen_cache import check_cache
        hit, response_json = check_cache(tool_name, token, params)
        if hit and response_json:
            return True, json.loads(response_json)
    except Exception:
        pass
    return False, None


def _cache_store(tool_name: str, token: str, params: dict, data):
    """Store response in nansen_cache."""
    try:
        from src.storage.nansen_cache import store_response
        store_response(tool_name, token, params, json.dumps(data),
                       tool_source="coinglass_api")
    except Exception as e:
        print(f"  ⚠️  Cache store failed: {e}", file=sys.stderr)


# ===========================================================================
# Data functions — Hobbyist tier (working)
# ===========================================================================

def fetch_coin_liquidation_list(exchange: str = "Binance",
                                 debug: bool = False) -> list | None:
    """
    Fetch liquidation summary for all coins.
    Fields per coin: symbol, liquidation_usd_24h/12h/4h/1h, long/short breakdowns.

    Returns:
        List of coin liquidation summaries or None
    """
    cache_key = {"exchange": exchange}
    hit, cached = _cache_check("coinglass_coin_list", "_ALL", cache_key)
    if hit:
        return cached

    data = cg_get("/api/futures/liquidation/coin-list",
                  {"exchange": exchange}, debug=debug)
    if data:
        _cache_store("coinglass_coin_list", "_ALL", cache_key, data)
    return data


def fetch_options_max_pain(symbol: str, exchange: str = "Deribit",
                           debug: bool = False) -> list | None:
    """
    Fetch options max pain by expiry date.
    Returns list of expiries with max_pain_price, call/put OI.

    Response format per item:
        date, max_pain_price, call_open_interest, put_open_interest,
        call_open_interest_market_value, put_open_interest_market_value,
        call_open_interest_notional, put_open_interest_notional
    """
    cache_key = {"symbol": symbol.upper(), "exchange": exchange}
    hit, cached = _cache_check("coinglass_max_pain", symbol, cache_key)
    if hit:
        return cached

    data = cg_get("/api/option/max-pain",
                  {"symbol": symbol.upper(), "exchange": exchange}, debug=debug)
    if data:
        _cache_store("coinglass_max_pain", symbol, cache_key, data)
    return data


def fetch_options_info(symbol: str, exchange: str = "Deribit",
                       debug: bool = False) -> list | None:
    """
    Fetch options overview — OI, volume, put/call ratio per exchange.

    Response format per item:
        exchange_name, open_interest, open_interest_usd, volume_usd_24h,
        open_interest_change_24h, volume_change_24h, oi_market_share
    """
    cache_key = {"symbol": symbol.upper(), "exchange": exchange}
    hit, cached = _cache_check("coinglass_max_pain", symbol,
                                {"symbol": symbol.upper(), "exchange": exchange, "type": "info"})
    if hit:
        return cached

    data = cg_get("/api/option/info",
                  {"symbol": symbol.upper(), "exchange": exchange}, debug=debug)
    if data:
        _cache_store("coinglass_max_pain", symbol,
                     {"symbol": symbol.upper(), "exchange": exchange, "type": "info"}, data)
    return data


# ===========================================================================
# Data functions — Premium tier (stubs, return None on Hobbyist)
# ===========================================================================

def fetch_liquidation_map(symbol: str, exchange: str = "Binance",
                          range_val: str = "1d", debug: bool = False) -> dict | None:
    """
    Fetch liquidation by price level. REQUIRES PREMIUM PLAN.
    On Hobbyist plan, returns None.
    """
    pair = f"{symbol.upper()}USDT"
    params = {"symbol": pair, "exchange": exchange, "range": range_val}
    cache_key = {"symbol": pair, "exchange": exchange, "range": range_val}

    hit, cached = _cache_check("coinglass_liquidation_map", symbol, cache_key)
    if hit:
        return cached

    data = cg_get("/api/futures/liquidation/map", params, debug=debug)
    if data:
        _cache_store("coinglass_liquidation_map", symbol, cache_key, data)
    return data


def fetch_large_limit_orders(symbol: str, exchange: str = "Binance",
                              debug: bool = False) -> dict | None:
    """
    Fetch large resting limit orders. REQUIRES PREMIUM PLAN.
    On Hobbyist plan, returns None.
    """
    pair = f"{symbol.upper()}USDT"
    params = {"symbol": pair, "exchange": exchange}
    cache_key = {"symbol": pair, "exchange": exchange}

    hit, cached = _cache_check("coinglass_large_limit_orders", symbol, cache_key)
    if hit:
        return cached

    data = cg_get("/api/futures/orderbook/large-limit-order", params, debug=debug)
    if data:
        _cache_store("coinglass_large_limit_orders", symbol, cache_key, data)
    return data


# ===========================================================================
# Data functions — Derivatives Intelligence (Hobbyist tier, new)
# ===========================================================================

def _ensure_pair_format(symbol: str) -> str:
    """Append USDT if symbol doesn't already end with it."""
    s = symbol.upper()
    if not s.endswith("USDT"):
        return s + "USDT"
    return s


def fetch_funding_rates(symbol: str, debug: bool = False) -> list | None:
    """
    Fetch funding rates for all symbols (endpoint returns all 1055+ symbols in one call).
    Cache with token "_ALL" since we get everything at once.
    """
    cache_key = {"type": "all_funding"}
    hit, cached = _cache_check("coinglass_funding_rates", "_ALL", cache_key)
    if hit:
        return cached

    data = cg_get("/api/futures/funding-rate/exchange-list", debug=debug)
    if data:
        _cache_store("coinglass_funding_rates", "_ALL", cache_key, data)
    return data


def fetch_oi_history(symbol: str, interval: str = "4h", limit: int = 24,
                     debug: bool = False) -> list | None:
    """
    Fetch aggregated OI history (OHLC format).
    Default: 24 x 4h candles = 4 days of OI data.
    """
    cache_key = {"symbol": symbol.upper(), "interval": interval, "limit": str(limit)}
    hit, cached = _cache_check("coinglass_oi_history", symbol, cache_key)
    if hit:
        return cached

    data = cg_get("/api/futures/open-interest/aggregated-history",
                  {"symbol": symbol.upper(), "interval": interval, "limit": str(limit)},
                  debug=debug)
    if data:
        _cache_store("coinglass_oi_history", symbol, cache_key, data)
    return data


def fetch_oi_exchange_list(symbol: str, debug: bool = False) -> list | None:
    """
    Fetch OI snapshot across all exchanges for a symbol.
    Returns ~25 items including an "All" aggregate row.
    """
    cache_key = {"symbol": symbol.upper()}
    hit, cached = _cache_check("coinglass_oi_exchange_list", symbol, cache_key)
    if hit:
        return cached

    data = cg_get("/api/futures/open-interest/exchange-list",
                  {"symbol": symbol.upper()}, debug=debug)
    if data:
        _cache_store("coinglass_oi_exchange_list", symbol, cache_key, data)
    return data


def fetch_global_ls_ratio(symbol: str, exchange: str = "Binance",
                           interval: str = "4h", limit: int = 6,
                           debug: bool = False) -> list | None:
    """
    Fetch global long/short account ratio history.
    CRITICAL: Requires PAIR format (BTCUSDT, not BTC).
    """
    pair = _ensure_pair_format(symbol)
    cache_key = {"symbol": pair, "exchange": exchange,
                 "interval": interval, "limit": str(limit)}
    hit, cached = _cache_check("coinglass_global_ls_ratio", symbol, cache_key)
    if hit:
        return cached

    data = cg_get("/api/futures/global-long-short-account-ratio/history",
                  {"symbol": pair, "exchange": exchange,
                   "interval": interval, "limit": str(limit)},
                  debug=debug)
    if data:
        _cache_store("coinglass_global_ls_ratio", symbol, cache_key, data)
    return data


def fetch_top_ls_ratios(symbol: str, exchange: str = "Binance",
                         interval: str = "4h", limit: int = 6,
                         debug: bool = False) -> dict | None:
    """
    Fetch top trader L/S ratios — both account and position.
    Makes 2 API calls. Returns {"account": [...], "position": [...]}.
    """
    pair = _ensure_pair_format(symbol)
    params = {"symbol": pair, "exchange": exchange,
              "interval": interval, "limit": str(limit)}

    # Account ratio
    acct_cache_key = dict(params, type="account")
    acct_hit, acct_cached = _cache_check("coinglass_top_ls_account", symbol, acct_cache_key)
    if acct_hit:
        account_data = acct_cached
    else:
        account_data = cg_get("/api/futures/top-long-short-account-ratio/history",
                              params, debug=debug)
        if account_data:
            _cache_store("coinglass_top_ls_account", symbol, acct_cache_key, account_data)

    # Position ratio
    pos_cache_key = dict(params, type="position")
    pos_hit, pos_cached = _cache_check("coinglass_top_ls_position", symbol, pos_cache_key)
    if pos_hit:
        position_data = pos_cached
    else:
        position_data = cg_get("/api/futures/top-long-short-position-ratio/history",
                               params, debug=debug)
        if position_data:
            _cache_store("coinglass_top_ls_position", symbol, pos_cache_key, position_data)

    if account_data is None and position_data is None:
        return None
    return {"account": account_data or [], "position": position_data or []}


def fetch_btc_etf_flows(debug: bool = False) -> list | None:
    """Fetch BTC ETF flow history. Returns full history (564+ days)."""
    cache_key = {"type": "btc_etf"}
    hit, cached = _cache_check("coinglass_btc_etf", "BTC", cache_key)
    if hit:
        return cached

    data = cg_get("/api/etf/bitcoin/flow-history", debug=debug)
    if data:
        _cache_store("coinglass_btc_etf", "BTC", cache_key, data)
    return data


def fetch_fear_greed(debug: bool = False) -> dict | None:
    """
    Fetch Fear & Greed index history.
    Returns {"data_list": [...], "price_list": [...], "time_list": [...]}.
    """
    cache_key = {"type": "fear_greed"}
    hit, cached = _cache_check("coinglass_fear_greed", "_MARKET", cache_key)
    if hit:
        return cached

    data = cg_get("/api/index/fear-greed-history", debug=debug)
    if data:
        _cache_store("coinglass_fear_greed", "_MARKET", cache_key, data)
    return data


def fetch_coinbase_premium(interval: str = "4h", limit: int = 6,
                            debug: bool = False) -> list | None:
    """
    Fetch Coinbase Premium Index.
    CRITICAL: This endpoint 500s without interval and limit params.
    """
    cache_key = {"interval": interval, "limit": str(limit)}
    hit, cached = _cache_check("coinglass_coinbase_premium", "BTC", cache_key)
    if hit:
        return cached

    data = cg_get("/api/coinbase-premium-index",
                  {"interval": interval, "limit": str(limit)}, debug=debug)
    if data:
        _cache_store("coinglass_coinbase_premium", "BTC", cache_key, data)
    return data


def fetch_funding_rate_ohlc(symbol: str, interval: str = "4h", limit: int = 1080,
                             debug: bool = False) -> list | None:
    """
    Fetch OI-weighted funding rate OHLC history for a specific symbol.
    Uses the OI-weighted endpoint which aggregates across exchanges by open interest.
    Default: 1080 x 4h candles = 180 days.
    Symbol format: plain symbol (BTC, not BTCUSDT).
    """
    cache_key = {"symbol": symbol.upper(), "interval": interval, "limit": str(limit)}
    hit, cached = _cache_check("coinglass_funding_rate_ohlc", symbol, cache_key)
    if hit:
        return cached

    data = cg_get("/api/futures/funding-rate/oi-weight-history",
                  {"symbol": symbol.upper(), "interval": interval, "limit": str(limit)},
                  debug=debug)
    if data:
        _cache_store("coinglass_funding_rate_ohlc", symbol, cache_key, data)
    return data


def fetch_liquidation_history(symbol: str, interval: str = "4h", limit: int = 1080,
                               exchange_list: str = "Binance,OKX,Bybit,Bitget,dYdX",
                               debug: bool = False) -> list | None:
    """
    Fetch aggregated liquidation history (long/short totals per interval).
    Default: 1080 x 4h candles = 180 days.
    Symbol format: plain symbol (BTC, not BTCUSDT).
    exchange_list: comma-separated exchanges (required by Coinglass API).
    """
    cache_key = {"symbol": symbol.upper(), "interval": interval, "limit": str(limit)}
    hit, cached = _cache_check("coinglass_liq_history", symbol, cache_key)
    if hit:
        return cached

    data = cg_get("/api/futures/liquidation/aggregated-history",
                  {"symbol": symbol.upper(), "interval": interval, "limit": str(limit),
                   "exchange_list": exchange_list},
                  debug=debug)
    if data:
        _cache_store("coinglass_liq_history", symbol, cache_key, data)
    return data


# ===========================================================================
# Snapshot endpoints — Spot CVD & Taker
# ===========================================================================

def fetch_spot_aggregated_cvd(symbol: str, interval: str = "h4",
                               exchange_list: str = "Binance,OKX,Bybit,Bitget",
                               debug: bool = False) -> list | None:
    """Fetch aggregated spot CVD history. Spot CVD rising + funding negative = strongest bullish signal."""
    cache_key = {"symbol": symbol.upper(), "interval": interval}
    hit, cached = _cache_check("coinglass_spot_cvd", symbol, cache_key)
    if hit:
        return cached
    data = cg_get("/api/spot/aggregated-cvd/history",
                  {"symbol": symbol.upper(), "interval": interval,
                   "exchange_list": exchange_list}, debug=debug)
    if data:
        _cache_store("coinglass_spot_cvd", symbol, cache_key, data)
    return data


def fetch_spot_taker_buy_sell(symbol: str, interval: str = "h4",
                               exchange_list: str = "Binance,OKX,Bybit,Bitget",
                               debug: bool = False) -> list | None:
    """Fetch aggregated spot taker buy/sell volume history."""
    cache_key = {"symbol": symbol.upper(), "interval": interval}
    hit, cached = _cache_check("coinglass_spot_taker", symbol, cache_key)
    if hit:
        return cached
    data = cg_get("/api/spot/aggregated-taker-buy-sell-volume/history",
                  {"symbol": symbol.upper(), "interval": interval,
                   "exchange_list": exchange_list}, debug=debug)
    if data:
        _cache_store("coinglass_spot_taker", symbol, cache_key, data)
    return data


def fetch_spot_netflow_list(symbol: str, debug: bool = False) -> list | None:
    """Fetch spot net flow list across exchanges."""
    cache_key = {"symbol": symbol.upper()}
    hit, cached = _cache_check("coinglass_spot_netflow", symbol, cache_key)
    if hit:
        return cached
    data = cg_get("/api/spot/netflow-list",
                  {"symbol": symbol.upper()}, debug=debug)
    if data:
        _cache_store("coinglass_spot_netflow", symbol, cache_key, data)
    return data


def fetch_spot_coin_netflow(symbol: str, debug: bool = False) -> dict | None:
    """Fetch per-coin spot flow detail."""
    cache_key = {"symbol": symbol.upper()}
    hit, cached = _cache_check("coinglass_spot_coin_netflow", symbol, cache_key)
    if hit:
        return cached
    data = cg_get("/api/spot/coin/netflow",
                  {"symbol": symbol.upper()}, debug=debug)
    if data:
        _cache_store("coinglass_spot_coin_netflow", symbol, cache_key, data)
    return data


# ===========================================================================
# Snapshot endpoints — Futures Basis & Speculation
# ===========================================================================

def fetch_futures_basis(symbol: str, interval: str = "h4",
                        exchange: str = "Binance",
                        debug: bool = False) -> list | None:
    """Fetch futures basis history. Widening = speculative excess, narrowing = deleveraging."""
    pair = _ensure_pair_format(symbol)
    cache_key = {"symbol": pair, "interval": interval, "exchange": exchange}
    hit, cached = _cache_check("coinglass_futures_basis", symbol, cache_key)
    if hit:
        return cached
    data = cg_get("/api/futures/basis/history",
                  {"symbol": pair, "exchange": exchange, "interval": interval},
                  debug=debug)
    if data:
        _cache_store("coinglass_futures_basis", symbol, cache_key, data)
    return data


def fetch_futures_spot_volume_ratio(symbol: str = "BTC", interval: str = "h4",
                                     exchange_list: str = "Binance,OKX,Bybit,Bitget",
                                     debug: bool = False) -> dict | list | None:
    """Fetch futures/spot volume ratio. High = overleveraged market."""
    cache_key = {"symbol": symbol.upper(), "interval": interval}
    hit, cached = _cache_check("coinglass_futures_spot_vol", symbol, cache_key)
    if hit:
        return cached
    data = cg_get("/api/futures_spot_volume_ratio",
                  {"symbol": symbol.upper(), "interval": interval,
                   "exchange_list": exchange_list}, debug=debug)
    if data:
        _cache_store("coinglass_futures_spot_vol", symbol, cache_key, data)
    return data


def fetch_options_futures_oi_ratio(debug: bool = False) -> dict | list | None:
    """Fetch options/futures OI ratio. Options OI rising = hedging increasing."""
    cache_key = {"type": "options_futures_oi_ratio"}
    hit, cached = _cache_check("coinglass_opt_fut_oi_ratio", "_MARKET", cache_key)
    if hit:
        return cached
    data = cg_get("/api/index/option-vs-futures-oi-ratio", debug=debug)
    if data:
        _cache_store("coinglass_opt_fut_oi_ratio", "_MARKET", cache_key, data)
    return data


# ===========================================================================
# Snapshot endpoints — Large Orders & Orderbook
# ===========================================================================

def fetch_aggregated_orderbook(symbol: str, interval: str = "h4",
                                exchange_list: str = "Binance,OKX,Bybit,Bitget",
                                debug: bool = False) -> list | None:
    """Fetch aggregated ask/bid history. Shows bid/ask imbalance over time."""
    cache_key = {"symbol": symbol.upper(), "interval": interval}
    hit, cached = _cache_check("coinglass_agg_orderbook", symbol, cache_key)
    if hit:
        return cached
    data = cg_get("/api/futures/orderbook/aggregated-ask-bids-history",
                  {"symbol": symbol.upper(), "interval": interval,
                   "exchange_list": exchange_list}, debug=debug)
    if data:
        _cache_store("coinglass_agg_orderbook", symbol, cache_key, data)
    return data


# ===========================================================================
# Snapshot endpoints — OI by Exchange
# ===========================================================================

def fetch_oi_exchange_history(symbol: str, range_val: str = "all",
                               debug: bool = False) -> dict | list | None:
    """Fetch OI by exchange over time. CME rising = institutional, Bybit = retail."""
    cache_key = {"symbol": symbol.upper(), "range": range_val}
    hit, cached = _cache_check("coinglass_oi_exchange_hist", symbol, cache_key)
    if hit:
        return cached
    data = cg_get("/api/futures/open-interest/exchange-history-chart",
                  {"symbol": symbol.upper(), "range": range_val}, debug=debug)
    if data:
        _cache_store("coinglass_oi_exchange_hist", symbol, cache_key, data)
    return data


# ===========================================================================
# Snapshot endpoints — Liquidation Heatmaps
# ===========================================================================

def fetch_liq_heatmap_model1(symbol: str, debug: bool = False) -> dict | list | None:
    """Fetch aggregated liquidation heatmap (model 1). Shows liq cluster targets."""
    cache_key = {"symbol": symbol.upper(), "model": "1"}
    hit, cached = _cache_check("coinglass_liq_heatmap", symbol, cache_key)
    if hit:
        return cached
    data = cg_get("/api/futures/liquidation/aggregated-heatmap/model1",
                  {"symbol": symbol.upper()}, debug=debug)
    if data:
        _cache_store("coinglass_liq_heatmap", symbol, cache_key, data)
    return data


def fetch_liq_heatmap_model3(symbol: str, debug: bool = False) -> dict | list | None:
    """Fetch aggregated liquidation heatmap (model 3). Cross-reference with model 1."""
    cache_key = {"symbol": symbol.upper(), "model": "3"}
    hit, cached = _cache_check("coinglass_liq_heatmap_m3", symbol, cache_key)
    if hit:
        return cached
    data = cg_get("/api/futures/liquidation/aggregated-heatmap/model3",
                  {"symbol": symbol.upper()}, debug=debug)
    if data:
        _cache_store("coinglass_liq_heatmap_m3", symbol, cache_key, data)
    return data


# ===========================================================================
# Snapshot endpoints — BTC Macro On-Chain
# ===========================================================================

def fetch_btc_sth_sopr(debug: bool = False) -> dict | list | None:
    """STH SOPR < 1 at VP support = capitulation buy zone."""
    cache_key = {"type": "sth_sopr"}
    hit, cached = _cache_check("coinglass_btc_sth_sopr", "BTC", cache_key)
    if hit:
        return cached
    data = cg_get("/api/index/bitcoin-sth-sopr", debug=debug)
    if data:
        _cache_store("coinglass_btc_sth_sopr", "BTC", cache_key, data)
    return data


def fetch_btc_lth_sopr(debug: bool = False) -> dict | list | None:
    """LTH distributing at VAH = macro distribution."""
    cache_key = {"type": "lth_sopr"}
    hit, cached = _cache_check("coinglass_btc_lth_sopr", "BTC", cache_key)
    if hit:
        return cached
    data = cg_get("/api/index/bitcoin-lth-sopr", debug=debug)
    if data:
        _cache_store("coinglass_btc_lth_sopr", "BTC", cache_key, data)
    return data


def fetch_btc_sth_realized_price(debug: bool = False) -> dict | list | None:
    """STH cost basis — dynamic support/resistance."""
    cache_key = {"type": "sth_realized_price"}
    hit, cached = _cache_check("coinglass_btc_sth_rp", "BTC", cache_key)
    if hit:
        return cached
    data = cg_get("/api/index/bitcoin-sth-realized-price", debug=debug)
    if data:
        _cache_store("coinglass_btc_sth_rp", "BTC", cache_key, data)
    return data


def fetch_btc_lth_realized_price(debug: bool = False) -> dict | list | None:
    """LTH cost basis — deep macro floor."""
    cache_key = {"type": "lth_realized_price"}
    hit, cached = _cache_check("coinglass_btc_lth_rp", "BTC", cache_key)
    if hit:
        return cached
    data = cg_get("/api/index/bitcoin-lth-realized-price", debug=debug)
    if data:
        _cache_store("coinglass_btc_lth_rp", "BTC", cache_key, data)
    return data


def fetch_btc_nupl(debug: bool = False) -> dict | list | None:
    """Net unrealized P/L — euphoria/capitulation gauge."""
    cache_key = {"type": "nupl"}
    hit, cached = _cache_check("coinglass_btc_nupl", "BTC", cache_key)
    if hit:
        return cached
    data = cg_get("/api/index/bitcoin-net-unrealized-profit-loss", debug=debug)
    if data:
        _cache_store("coinglass_btc_nupl", "BTC", cache_key, data)
    return data


def fetch_btc_active_addresses(debug: bool = False) -> dict | list | None:
    """Network activity — rising activity + rising VA = real demand."""
    cache_key = {"type": "active_addresses"}
    hit, cached = _cache_check("coinglass_btc_active_addr", "BTC", cache_key)
    if hit:
        return cached
    data = cg_get("/api/index/bitcoin-active-addresses", debug=debug)
    if data:
        _cache_store("coinglass_btc_active_addr", "BTC", cache_key, data)
    return data


def fetch_btc_reserve_risk(debug: bool = False) -> dict | list | None:
    """Risk/reward ratio from HODLer conviction."""
    cache_key = {"type": "reserve_risk"}
    hit, cached = _cache_check("coinglass_btc_reserve_risk", "BTC", cache_key)
    if hit:
        return cached
    data = cg_get("/api/index/bitcoin-reserve-risk", debug=debug)
    if data:
        _cache_store("coinglass_btc_reserve_risk", "BTC", cache_key, data)
    return data


def fetch_btc_correlation(debug: bool = False) -> dict | list | None:
    """BTC vs SPY/GLD/TLT — regime context."""
    cache_key = {"type": "correlation"}
    hit, cached = _cache_check("coinglass_btc_correlation", "BTC", cache_key)
    if hit:
        return cached
    data = cg_get("/api/index/bitcoin-correlation", debug=debug)
    if data:
        _cache_store("coinglass_btc_correlation", "BTC", cache_key, data)
    return data


def fetch_btc_macro_oscillator(debug: bool = False) -> dict | list | None:
    """BMO composite — confirms macro cycle position."""
    cache_key = {"type": "macro_oscillator"}
    hit, cached = _cache_check("coinglass_btc_macro_osc", "BTC", cache_key)
    if hit:
        return cached
    data = cg_get("/api/index/bitcoin-macro-oscillator", debug=debug)
    if data:
        _cache_store("coinglass_btc_macro_osc", "BTC", cache_key, data)
    return data


# ===========================================================================
# Snapshot endpoints — ETF Detail
# ===========================================================================

def fetch_btc_etf_net_assets(debug: bool = False) -> list | None:
    """BTC ETF AUM trend — rising AUM + positive flows = institutional conviction."""
    cache_key = {"type": "btc_etf_net_assets"}
    hit, cached = _cache_check("coinglass_btc_etf_assets", "BTC", cache_key)
    if hit:
        return cached
    data = cg_get("/api/etf/bitcoin/net-assets/history", debug=debug)
    if data:
        _cache_store("coinglass_btc_etf_assets", "BTC", cache_key, data)
    return data


def fetch_btc_etf_premium_discount(debug: bool = False) -> list | None:
    """ETF NAV divergence — premium = demand exceeding supply."""
    cache_key = {"type": "btc_etf_premium"}
    hit, cached = _cache_check("coinglass_btc_etf_premium", "BTC", cache_key)
    if hit:
        return cached
    data = cg_get("/api/etf/bitcoin/premium-discount/history", debug=debug)
    if data:
        _cache_store("coinglass_btc_etf_premium", "BTC", cache_key, data)
    return data


def fetch_grayscale_premium(debug: bool = False) -> list | None:
    """GBTC premium/discount — institutional sentiment barometer."""
    cache_key = {"type": "grayscale_premium"}
    hit, cached = _cache_check("coinglass_grayscale_premium", "BTC", cache_key)
    if hit:
        return cached
    data = cg_get("/api/grayscale/premium-history", debug=debug)
    if data:
        _cache_store("coinglass_grayscale_premium", "BTC", cache_key, data)
    return data


# ===========================================================================
# Interpretation functions
# ===========================================================================

def interpret_funding_rate_ohlc(data: list) -> list:
    """
    Interpret funding rate OHLC history — extract close rate per bar with bias.
    Returns list of dicts: [{time, close, bias}, ...]
    """
    if not data or not isinstance(data, list):
        return []

    bars = []
    for item in data:
        if not isinstance(item, dict):
            continue
        t = item.get("time", item.get("t", 0))
        close = float(item.get("close", item.get("c", 0)) or 0)

        if close > 0.0003:
            bias = "long_crowded"
        elif close > 0.0001:
            bias = "moderately_long"
        elif close < -0.0003:
            bias = "short_crowded"
        elif close < -0.0001:
            bias = "moderately_short"
        else:
            bias = "neutral"

        bars.append({"time": t, "close": close, "bias": bias})

    return bars


def interpret_coin_liquidations(coins: list, symbol: str) -> dict:
    """
    Interpret liquidation data for a specific coin from the coin-list.

    Returns:
        {
            "symbol": str,
            "total_24h_usd": float,
            "long_liq_24h_usd": float,
            "short_liq_24h_usd": float,
            "long_short_ratio": float,   # >1 = more longs liquidated, <1 = more shorts
            "bias": "long_pain" | "short_pain" | "balanced",
            "recent_acceleration": bool,  # 1h pace > 4h avg pace
            "timeframe_breakdown": {...},
            "interpretation": str,
        }
    """
    result = {
        "symbol": symbol.upper(),
        "total_24h_usd": 0, "long_liq_24h_usd": 0, "short_liq_24h_usd": 0,
        "long_short_ratio": 1.0, "bias": "balanced",
        "recent_acceleration": False, "timeframe_breakdown": {},
        "interpretation": f"No liquidation data for {symbol.upper()}",
    }

    if not coins:
        return result

    # Find the token in coin list
    match = None
    for coin in coins:
        if isinstance(coin, dict) and coin.get("symbol", "").upper() == symbol.upper():
            match = coin
            break

    if not match:
        return result

    total_24h = float(match.get("liquidation_usd_24h", 0) or 0)
    long_24h = float(match.get("long_liquidation_usd_24h", 0) or 0)
    short_24h = float(match.get("short_liquidation_usd_24h", 0) or 0)
    total_12h = float(match.get("liquidation_usd_12h", 0) or 0)
    long_12h = float(match.get("long_liquidation_usd_12h", 0) or 0)
    short_12h = float(match.get("short_liquidation_usd_12h", 0) or 0)
    total_4h = float(match.get("liquidation_usd_4h", 0) or 0)
    long_4h = float(match.get("long_liquidation_usd_4h", 0) or 0)
    short_4h = float(match.get("short_liquidation_usd_4h", 0) or 0)
    total_1h = float(match.get("liquidation_usd_1h", 0) or 0)
    long_1h = float(match.get("long_liquidation_usd_1h", 0) or 0)
    short_1h = float(match.get("short_liquidation_usd_1h", 0) or 0)

    # Long/short ratio — which side is getting wrecked
    ls_ratio = long_24h / short_24h if short_24h > 0 else (99.0 if long_24h > 0 else 1.0)

    if ls_ratio > 2.0:
        bias = "long_pain"  # Longs getting liquidated = price dropping = bearish
    elif ls_ratio < 0.5:
        bias = "short_pain"  # Shorts getting liquidated = price pumping = bullish
    else:
        bias = "balanced"

    # Acceleration: is 1h pace above 4h average?
    pace_4h_per_hour = total_4h / 4 if total_4h > 0 else 0
    acceleration = total_1h > pace_4h_per_hour * 1.5 and total_1h > 10000

    tf = {
        "24h": {"total": total_24h, "long": long_24h, "short": short_24h},
        "12h": {"total": total_12h, "long": long_12h, "short": short_12h},
        "4h": {"total": total_4h, "long": long_4h, "short": short_4h},
        "1h": {"total": total_1h, "long": long_1h, "short": short_1h},
    }

    # Build interpretation
    parts = []
    parts.append(f"{symbol.upper()} 24h liquidations: {_fmt_usd(total_24h)} (Long: {_fmt_usd(long_24h)} | Short: {_fmt_usd(short_24h)})")

    if bias == "long_pain":
        parts.append(f"Longs getting wrecked {ls_ratio:.1f}x more than shorts — bearish pressure, price declining")
    elif bias == "short_pain":
        parts.append(f"Shorts getting wrecked — bullish pressure, price rising")
    else:
        parts.append(f"Balanced liquidation (L/S ratio: {ls_ratio:.1f}x)")

    if acceleration:
        parts.append(f"⚡ ACCELERATION: 1h liquidations ({_fmt_usd(total_1h)}) running above 4h average pace")

    result.update({
        "total_24h_usd": total_24h,
        "long_liq_24h_usd": long_24h,
        "short_liq_24h_usd": short_24h,
        "long_short_ratio": round(ls_ratio, 2),
        "bias": bias,
        "recent_acceleration": acceleration,
        "timeframe_breakdown": tf,
        "interpretation": ". ".join(parts),
    })
    return result


def interpret_options_max_pain(data: list, current_price: float) -> dict:
    """
    Interpret options max pain data — nearest expiry max pain is the magnet.

    Returns:
        {
            "nearest_expiry": str,
            "max_pain_price": float,
            "distance_pct": float,
            "direction": "above" | "below" | "at",
            "put_call_oi_ratio": float,  # >1 = put heavy = bearish sentiment
            "expiries": [...],
            "interpretation": str,
        }
    """
    result = {
        "nearest_expiry": None, "max_pain_price": 0, "distance_pct": 0,
        "direction": "at", "put_call_oi_ratio": 1.0, "expiries": [],
        "interpretation": "No options max pain data available",
    }

    if not data or not isinstance(data, list) or current_price <= 0:
        return result

    expiries = []
    for item in data:
        if not isinstance(item, dict):
            continue
        mp = float(item.get("max_pain_price", 0) or 0)
        call_oi = float(item.get("call_open_interest", 0) or 0)
        put_oi = float(item.get("put_open_interest", 0) or 0)
        date = item.get("date", "")

        if mp <= 0:
            continue

        expiries.append({
            "date": date,
            "max_pain_price": mp,
            "call_oi": call_oi,
            "put_oi": put_oi,
            "put_call_ratio": round(put_oi / call_oi, 2) if call_oi > 0 else 0,
            "distance_pct": round(((mp - current_price) / current_price) * 100, 2),
        })

    if not expiries:
        return result

    # Nearest expiry (first in list, already sorted by date from API)
    nearest = expiries[0]
    mp = nearest["max_pain_price"]
    dist = nearest["distance_pct"]

    if dist > 1.0:
        direction = "above"
    elif dist < -1.0:
        direction = "below"
    else:
        direction = "at"

    # Aggregate put/call ratio across all expiries
    total_puts = sum(e["put_oi"] for e in expiries)
    total_calls = sum(e["call_oi"] for e in expiries)
    pc_ratio = round(total_puts / total_calls, 2) if total_calls > 0 else 0

    parts = []
    parts.append(f"Nearest options max pain: ${mp:,.0f} ({dist:+.1f}% from ${current_price:,.0f})")
    if direction == "above":
        parts.append(f"Max pain ABOVE price — magnetic pull upward. MMs benefit if price rises to ${mp:,.0f}")
    elif direction == "below":
        parts.append(f"Max pain BELOW price — magnetic pull downward. MMs benefit if price drops to ${mp:,.0f}")
    else:
        parts.append(f"Price near max pain — MMs comfortable, expect range-bound")

    if pc_ratio > 1.3:
        parts.append(f"Put/Call OI ratio: {pc_ratio:.2f}x — heavy put protection, bearish hedging")
    elif pc_ratio < 0.7:
        parts.append(f"Put/Call OI ratio: {pc_ratio:.2f}x — call-heavy, bullish positioning")
    else:
        parts.append(f"Put/Call OI ratio: {pc_ratio:.2f}x — balanced")

    result.update({
        "nearest_expiry": nearest["date"],
        "max_pain_price": mp,
        "distance_pct": dist,
        "direction": direction,
        "put_call_oi_ratio": pc_ratio,
        "expiries": expiries[:5],
        "interpretation": ". ".join(parts),
    })
    return result


def interpret_options_info(data: list) -> dict:
    """
    Interpret options info — total OI, volume, put/call breakdown.

    Returns:
        {
            "total_oi_usd": float,
            "volume_24h_usd": float,
            "oi_change_24h_pct": float,
            "interpretation": str,
        }
    """
    result = {
        "total_oi_usd": 0, "volume_24h_usd": 0, "oi_change_24h_pct": 0,
        "interpretation": "No options info available",
    }

    if not data or not isinstance(data, list):
        return result

    # Find "All" exchange aggregate, or sum up
    agg = None
    for item in data:
        if isinstance(item, dict) and item.get("exchange_name") == "All":
            agg = item
            break

    if not agg:
        agg = data[0] if data else {}

    oi_usd = float(agg.get("open_interest_usd", 0) or 0)
    vol_usd = float(agg.get("volume_usd_24h", 0) or 0)
    oi_change = float(agg.get("open_interest_change_24h", 0) or 0)

    parts = []
    parts.append(f"Options OI: {_fmt_usd(oi_usd)} | 24h Volume: {_fmt_usd(vol_usd)}")
    if oi_change > 5:
        parts.append(f"OI growing +{oi_change:.1f}% in 24h — new positions being opened")
    elif oi_change < -5:
        parts.append(f"OI declining {oi_change:.1f}% in 24h — positions closing")

    result.update({
        "total_oi_usd": oi_usd,
        "volume_24h_usd": vol_usd,
        "oi_change_24h_pct": oi_change,
        "interpretation": ". ".join(parts),
    })
    return result


def detect_liquidity_grab_setup(
    liq_data: dict,
    max_pain_interp: dict,
    options_interp: dict,
    current_price: float
) -> dict:
    """
    Detect Liquidity Grab Fade setups using available Hobbyist data.

    On Hobbyist plan, uses:
    - Liquidation bias (long_pain vs short_pain) as directional signal
    - Options max pain as magnetic target
    - Put/call ratio as sentiment confirmation

    A setup is detected when:
    1. Liquidation bias shows one side getting wrecked (directional move underway)
    2. Max pain is in the OPPOSITE direction (snap-back magnet)
    3. Put/call ratio confirms the contrarian trade

    Returns:
        {
            "detected": bool,
            "direction": "long" | "short" | None,
            "confidence": "high" | "medium" | "low",
            "snap_back_target": float,
            "thesis": str,
            "components": {...}
        }
    """
    result = {
        "detected": False,
        "direction": None,
        "confidence": "low",
        "snap_back_target": None,
        "thesis": "No liquidity grab setup detected",
        "components": {},
    }

    if current_price <= 0:
        return result

    bias = liq_data.get("bias", "balanced")
    ls_ratio = liq_data.get("long_short_ratio", 1.0)
    acceleration = liq_data.get("recent_acceleration", False)
    mp_direction = max_pain_interp.get("direction", "at")
    mp_price = max_pain_interp.get("max_pain_price", 0)
    mp_dist = max_pain_interp.get("distance_pct", 0)
    pc_ratio = max_pain_interp.get("put_call_oi_ratio", 1.0)

    conditions_met = 0
    direction = None
    snap_target = None
    reasons = []

    # LONG setup: longs getting liquidated (price dropping) + max pain above (snap up)
    if bias == "long_pain" and ls_ratio > 2.0:
        reasons.append(f"Longs getting liquidated {ls_ratio:.1f}x more than shorts — flush underway")
        conditions_met += 1
        direction = "long"

        if mp_direction == "above" and abs(mp_dist) > 1.5:
            reasons.append(f"Max pain ${mp_price:,.0f} is {mp_dist:+.1f}% above — magnetic pull for snap-back")
            conditions_met += 1
            snap_target = mp_price

        if pc_ratio > 1.2:
            reasons.append(f"Put/Call {pc_ratio:.2f}x — heavy put protection suggests floor nearby")
            conditions_met += 1

    # SHORT setup: shorts getting liquidated (price pumping) + max pain below (snap down)
    elif bias == "short_pain" and ls_ratio < 0.5:
        reasons.append(f"Shorts getting squeezed — price pumping into resistance")
        conditions_met += 1
        direction = "short"

        if mp_direction == "below" and abs(mp_dist) > 1.5:
            reasons.append(f"Max pain ${mp_price:,.0f} is {mp_dist:+.1f}% below — gravity for snap-back")
            conditions_met += 1
            snap_target = mp_price

        if pc_ratio < 0.8:
            reasons.append(f"Put/Call {pc_ratio:.2f}x — call-heavy, complacent longs vulnerable")
            conditions_met += 1

    if acceleration and conditions_met >= 1:
        reasons.append("⚡ Liquidation acceleration — cascade may be exhausting")
        conditions_met += 1

    if conditions_met >= 2:
        confidence = "high" if conditions_met >= 3 else "medium"
        thesis = f"Liquidity Grab Fade {direction.upper()}: {' + '.join(reasons)}"
        result.update({
            "detected": True,
            "direction": direction,
            "confidence": confidence,
            "snap_back_target": snap_target,
            "thesis": thesis,
            "components": {
                "conditions_met": conditions_met,
                "reasons": reasons,
                "max_pain_price": mp_price,
                "liquidation_bias": bias,
                "ls_ratio": ls_ratio,
            },
        })

    return result


# ===========================================================================
# Interpretation functions — Derivatives Intelligence (new)
# ===========================================================================

def interpret_funding_rates(data: list, symbol: str) -> dict:
    """Interpret funding rate data for a specific symbol from the all-symbols response."""
    result = {
        "symbol": symbol.upper(),
        "avg_rate": 0.0, "avg_rate_pct": "0.0000%",
        "max_rate": 0.0, "max_exchange": "", "min_rate": 0.0, "min_exchange": "",
        "num_exchanges": 0, "annualized_cost_pct": 0.0,
        "bias": "neutral",
        "interpretation": f"No funding rate data for {symbol.upper()}",
    }

    if not data:
        return result

    # Find matching symbol
    match = None
    for item in data:
        if isinstance(item, dict) and item.get("symbol", "").upper() == symbol.upper():
            match = item
            break

    if not match:
        return result

    exchanges = match.get("stablecoin_margin_list") or []
    if not exchanges:
        return result

    rates = []
    intervals = []
    for ex in exchanges:
        rate = ex.get("funding_rate")
        if rate is not None:
            rates.append((ex.get("exchange", "Unknown"), float(rate),
                          int(ex.get("funding_rate_interval", 8))))
            intervals.append(int(ex.get("funding_rate_interval", 8)))

    if not rates:
        return result

    # Simple average (equal weight since no volume data)
    avg_rate = sum(r[1] for r in rates) / len(rates)
    avg_interval = sum(intervals) / len(intervals) if intervals else 8

    max_entry = max(rates, key=lambda x: x[1])
    min_entry = min(rates, key=lambda x: x[1])

    # Bias determination
    if avg_rate > 0.0003:
        bias = "long_crowded"
    elif avg_rate > 0.0001:
        bias = "moderately_long"
    elif avg_rate < -0.0003:
        bias = "short_crowded"
    elif avg_rate < -0.0001:
        bias = "moderately_short"
    else:
        bias = "neutral"

    # Annualized cost
    annualized = avg_rate * (24 / avg_interval) * 365 * 100

    parts = []
    parts.append(f"{symbol.upper()} avg funding: {avg_rate*100:.4f}% across {len(rates)} exchanges")
    if bias == "long_crowded":
        parts.append("Longs paying heavily — crowded long positioning, squeeze DOWN risk")
    elif bias == "short_crowded":
        parts.append("Shorts paying heavily — crowded short positioning, squeeze UP risk")
    elif bias == "moderately_long":
        parts.append("Slight long bias — moderate crowding")
    elif bias == "moderately_short":
        parts.append("Slight short bias — moderate crowding")
    else:
        parts.append("Neutral funding — no directional crowding")
    parts.append(f"Annualized cost: {annualized:.1f}% for the dominant side")

    result.update({
        "avg_rate": round(avg_rate, 8),
        "avg_rate_pct": f"{avg_rate*100:.4f}%",
        "max_rate": round(max_entry[1], 8),
        "max_exchange": max_entry[0],
        "min_rate": round(min_entry[1], 8),
        "min_exchange": min_entry[0],
        "num_exchanges": len(rates),
        "annualized_cost_pct": round(annualized, 2),
        "bias": bias,
        "interpretation": ". ".join(parts),
    })
    return result


def interpret_oi_history(data: list, symbol: str) -> dict:
    """Interpret OI aggregated history — trend, 24h change, acceleration."""
    result = {
        "symbol": symbol.upper(),
        "current_oi_usd": 0.0, "oi_24h_ago_usd": 0.0,
        "oi_change_24h_pct": 0.0, "oi_change_period_pct": 0.0,
        "oi_trend": "flat",
        "interpretation": f"No OI history for {symbol.upper()}",
    }

    if not data or len(data) < 2:
        return result

    candles = []
    for item in data:
        if isinstance(item, dict):
            candles.append({
                "time": item.get("time", 0),
                "close": float(item.get("close", 0) or 0),
            })

    if len(candles) < 2:
        return result

    current_oi = candles[-1]["close"]
    first_oi = candles[0]["close"]

    # 24h ago: 6 candles back for 4h interval
    idx_24h = max(0, len(candles) - 7)
    oi_24h_ago = candles[idx_24h]["close"]

    change_24h_pct = ((current_oi - oi_24h_ago) / oi_24h_ago * 100) if oi_24h_ago > 0 else 0
    change_period_pct = ((current_oi - first_oi) / first_oi * 100) if first_oi > 0 else 0

    if change_24h_pct > 5:
        trend = "rising"
    elif change_24h_pct < -5:
        trend = "falling"
    else:
        trend = "flat"

    parts = []
    parts.append(f"{symbol.upper()} OI: {_fmt_usd(current_oi)} ({change_24h_pct:+.1f}% 24h)")
    if trend == "rising":
        parts.append("OI expanding — new positions entering the market")
    elif trend == "falling":
        parts.append("OI contracting — positions being closed")
    else:
        parts.append("OI stable — no significant position changes")

    result.update({
        "current_oi_usd": current_oi,
        "oi_24h_ago_usd": oi_24h_ago,
        "oi_change_24h_pct": round(change_24h_pct, 2),
        "oi_change_period_pct": round(change_period_pct, 2),
        "oi_trend": trend,
        "interpretation": ". ".join(parts),
    })
    return result


def interpret_oi_exchange_snapshot(data: list, symbol: str) -> dict:
    """Interpret OI exchange snapshot — total OI, change rates, momentum, top movers."""
    result = {
        "symbol": symbol.upper(),
        "total_oi_usd": 0.0,
        "change_1h_pct": 0.0, "change_4h_pct": 0.0, "change_24h_pct": 0.0,
        "momentum": "stable",
        "top_exchange_changes": [],
        "interpretation": f"No OI exchange data for {symbol.upper()}",
    }

    if not data:
        return result

    agg = None
    exchanges = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if item.get("exchange") == "All":
            agg = item
        else:
            exchanges.append(item)

    if not agg:
        return result

    total_oi = float(agg.get("open_interest_usd", 0) or 0)
    c1h = float(agg.get("open_interest_change_percent_1h", 0) or 0)
    c4h = float(agg.get("open_interest_change_percent_4h", 0) or 0)
    c24h = float(agg.get("open_interest_change_percent_24h", 0) or 0)

    if c1h > 1 and c4h > 1:
        momentum = "expanding"
    elif c1h < -1 and c4h < -1:
        momentum = "contracting"
    else:
        momentum = "stable"

    top_changes = []
    for ex in exchanges:
        name = ex.get("exchange", "Unknown")
        ex_c1h = float(ex.get("open_interest_change_percent_1h", 0) or 0)
        ex_oi = float(ex.get("open_interest_usd", 0) or 0)
        top_changes.append({"exchange": name, "change_1h_pct": round(ex_c1h, 2), "oi_usd": ex_oi})
    top_changes.sort(key=lambda x: abs(x["change_1h_pct"]), reverse=True)

    parts = []
    parts.append(f"{symbol.upper()} total OI: {_fmt_usd(total_oi)} ({c24h:+.1f}% 24h)")
    if momentum == "expanding":
        parts.append(f"OI expanding rapidly (+{c1h:.1f}% 1h, +{c4h:.1f}% 4h) — new positions entering")
    elif momentum == "contracting":
        parts.append(f"OI contracting ({c1h:.1f}% 1h, {c4h:.1f}% 4h) — positions closing")
    if top_changes:
        top = top_changes[0]
        parts.append(f"Biggest mover: {top['exchange']} ({top['change_1h_pct']:+.1f}% 1h)")

    result.update({
        "total_oi_usd": total_oi,
        "change_1h_pct": round(c1h, 2),
        "change_4h_pct": round(c4h, 2),
        "change_24h_pct": round(c24h, 2),
        "momentum": momentum,
        "top_exchange_changes": top_changes[:3],
        "interpretation": ". ".join(parts),
    })
    return result


def interpret_global_ls_ratio(data: list, symbol: str) -> dict:
    """Interpret global long/short account ratio — crowd positioning + contrarian signal."""
    result = {
        "symbol": symbol.upper(),
        "current_long_pct": 50.0, "current_short_pct": 50.0, "current_ratio": 1.0,
        "trend": "stable", "extreme": False, "contrarian_signal": None,
        "interpretation": f"No L/S ratio data for {symbol.upper()}",
    }

    if not data or not isinstance(data, list) or len(data) == 0:
        return result

    latest = data[-1] if isinstance(data[-1], dict) else data[0]
    first = data[0] if isinstance(data[0], dict) else latest

    long_pct = float(latest.get("global_account_long_percent", 50) or 50)
    short_pct = float(latest.get("global_account_short_percent", 50) or 50)
    ratio = float(latest.get("global_account_long_short_ratio", 1.0) or 1.0)
    first_ratio = float(first.get("global_account_long_short_ratio", 1.0) or 1.0)

    if ratio > first_ratio * 1.05:
        trend = "more_longs"
    elif ratio < first_ratio * 0.95:
        trend = "more_shorts"
    else:
        trend = "stable"

    extreme = ratio > 2.5 or ratio < 0.4

    contrarian = None
    if ratio > 2.5:
        contrarian = "short"
    elif ratio < 0.4:
        contrarian = "long"

    parts = []
    parts.append(f"{symbol.upper()} Global L/S: {ratio:.2f}x ({long_pct:.1f}% long / {short_pct:.1f}% short)")
    if extreme:
        if contrarian == "short":
            parts.append("EXTREME long crowding — contrarian short signal")
        else:
            parts.append("EXTREME short crowding — contrarian long signal")
    elif trend == "more_longs":
        parts.append("Crowd shifting long — retail piling into longs")
    elif trend == "more_shorts":
        parts.append("Crowd shifting short — retail piling into shorts")

    result.update({
        "current_long_pct": round(long_pct, 2),
        "current_short_pct": round(short_pct, 2),
        "current_ratio": round(ratio, 2),
        "trend": trend,
        "extreme": extreme,
        "contrarian_signal": contrarian,
        "interpretation": ". ".join(parts),
    })
    return result


def interpret_top_ls_ratios(account_data: list, position_data: list, symbol: str) -> dict:
    """Interpret top trader L/S ratios — account vs position divergence reveals conviction."""
    result = {
        "symbol": symbol.upper(),
        "top_account_long_pct": 50.0, "top_account_ratio": 1.0,
        "top_position_long_pct": 50.0, "top_position_ratio": 1.0,
        "account_position_divergence": False,
        "smart_money_lean": "neutral",
        "interpretation": f"No top trader L/S data for {symbol.upper()}",
    }

    acct_long = 50.0
    acct_ratio = 1.0
    pos_long = 50.0
    pos_ratio = 1.0

    if account_data and isinstance(account_data, list) and len(account_data) > 0:
        latest_acct = account_data[-1] if isinstance(account_data[-1], dict) else {}
        acct_long = float(latest_acct.get("top_account_long_percent", 50) or 50)
        acct_ratio = float(latest_acct.get("top_account_long_short_ratio", 1.0) or 1.0)

    if position_data and isinstance(position_data, list) and len(position_data) > 0:
        latest_pos = position_data[-1] if isinstance(position_data[-1], dict) else {}
        pos_long = float(latest_pos.get("top_position_long_percent", 50) or 50)
        pos_ratio = float(latest_pos.get("top_position_long_short_ratio", 1.0) or 1.0)

    # Divergence: significant gap between account % and position %
    divergence = abs(acct_long - pos_long) > 5

    # Smart money lean based on position ratio (size-weighted)
    if pos_ratio > 1.15:
        lean = "long"
    elif pos_ratio < 0.85:
        lean = "short"
    else:
        lean = "neutral"

    parts = []
    parts.append(f"{symbol.upper()} Top Traders — Account: {acct_ratio:.2f}x ({acct_long:.1f}% long), Position: {pos_ratio:.2f}x ({pos_long:.1f}% long)")
    if divergence:
        if acct_long > pos_long:
            parts.append(f"Account/Position divergence: many small longs (acct {acct_long:.0f}%) but position weight lower ({pos_long:.0f}%) — retail long, smart money less convinced")
        else:
            parts.append(f"Account/Position divergence: fewer longs by count (acct {acct_long:.0f}%) but larger positions ({pos_long:.0f}%) — concentrated conviction longs")
    if lean == "long":
        parts.append("Smart money lean: LONG (position-weighted)")
    elif lean == "short":
        parts.append("Smart money lean: SHORT (position-weighted)")

    result.update({
        "top_account_long_pct": round(acct_long, 2),
        "top_account_ratio": round(acct_ratio, 2),
        "top_position_long_pct": round(pos_long, 2),
        "top_position_ratio": round(pos_ratio, 2),
        "account_position_divergence": divergence,
        "smart_money_lean": lean,
        "interpretation": ". ".join(parts),
    })
    return result


def interpret_btc_etf_flows(data: list) -> dict:
    """Interpret BTC ETF flow history — weekly net, streak, top ETF."""
    result = {
        "latest_day_flow_usd": 0.0, "latest_day_date": "",
        "latest_day_top_etf": "", "latest_day_top_etf_flow_usd": 0.0,
        "weekly_net_flow_usd": 0.0,
        "streak_days": 0,
        "bias": "mixed",
        "interpretation": "No BTC ETF flow data available",
    }

    if not data or not isinstance(data, list):
        return result

    sorted_data = sorted(data, key=lambda x: x.get("timestamp", 0), reverse=True)
    if not sorted_data:
        return result

    latest = sorted_data[0]
    latest_flow = float(latest.get("flow_usd", 0) or 0)
    latest_ts = latest.get("timestamp", 0)
    latest_date = datetime.fromtimestamp(latest_ts / 1000).strftime("%Y-%m-%d") if latest_ts else ""

    # Top ETF by absolute flow for latest day
    etf_flows = latest.get("etf_flows", []) or []
    top_etf = ""
    top_etf_flow = 0.0
    for ef in etf_flows:
        f = float(ef.get("flow_usd", 0) or 0)
        if abs(f) > abs(top_etf_flow):
            top_etf_flow = f
            top_etf = ef.get("etf_ticker", "")

    # Weekly net (last 7 entries)
    weekly = sorted_data[:7]
    weekly_net = sum(float(d.get("flow_usd", 0) or 0) for d in weekly)

    # Streak: consecutive same-sign flow days
    streak = 0
    if sorted_data:
        sign = 1 if float(sorted_data[0].get("flow_usd", 0) or 0) >= 0 else -1
        for d in sorted_data:
            f = float(d.get("flow_usd", 0) or 0)
            if (f >= 0 and sign > 0) or (f < 0 and sign < 0):
                streak += 1
            else:
                break
        streak = streak * sign

    if weekly_net > 500_000_000:
        bias = "strong_inflow"
    elif weekly_net > 100_000_000:
        bias = "moderate_inflow"
    elif weekly_net < -500_000_000:
        bias = "strong_outflow"
    elif weekly_net < -100_000_000:
        bias = "moderate_outflow"
    else:
        bias = "mixed"

    parts = []
    parts.append(f"BTC ETF latest: {_fmt_usd(abs(latest_flow))} {'inflow' if latest_flow >= 0 else 'outflow'} ({latest_date})")
    parts.append(f"Weekly net: {_fmt_usd(abs(weekly_net))} {'inflow' if weekly_net >= 0 else 'outflow'}")
    if abs(streak) > 3:
        direction = "inflow" if streak > 0 else "outflow"
        parts.append(f"{abs(streak)}-day {direction} streak — sustained institutional {'buying' if streak > 0 else 'selling'}")

    result.update({
        "latest_day_flow_usd": latest_flow,
        "latest_day_date": latest_date,
        "latest_day_top_etf": top_etf,
        "latest_day_top_etf_flow_usd": top_etf_flow,
        "weekly_net_flow_usd": weekly_net,
        "streak_days": streak,
        "bias": bias,
        "interpretation": ". ".join(parts),
    })
    return result


def interpret_fear_greed(data: dict) -> dict:
    """Interpret Fear & Greed index — current value, label, trend, contrarian signal."""
    result = {
        "value": 50, "label": "Neutral", "avg_7d": 50.0,
        "trend": "stable", "contrarian_signal": None,
        "interpretation": "No Fear & Greed data available",
    }

    if not data or not isinstance(data, dict):
        return result

    data_list = data.get("data_list", [])
    if not data_list:
        return result

    current = int(data_list[-1])

    if current <= 20:
        label = "Extreme Fear"
    elif current <= 40:
        label = "Fear"
    elif current <= 60:
        label = "Neutral"
    elif current <= 80:
        label = "Greed"
    else:
        label = "Extreme Greed"

    last_7 = data_list[-7:] if len(data_list) >= 7 else data_list
    avg_7d = sum(float(v) for v in last_7) / len(last_7)

    if current > avg_7d + 5:
        trend = "rising"
    elif current < avg_7d - 5:
        trend = "falling"
    else:
        trend = "stable"

    contrarian = None
    if current <= 20:
        contrarian = "long"
    elif current >= 80:
        contrarian = "short"

    parts = []
    parts.append(f"Fear & Greed: {current} — {label}")
    if contrarian == "long":
        parts.append("Extreme Fear — contrarian long signal. Markets most fearful = historically best buying opportunities")
    elif contrarian == "short":
        parts.append("Extreme Greed — contrarian short signal. Maximum complacency = risk of correction")
    parts.append(f"7d avg: {avg_7d:.0f}, trend: {trend}")

    result.update({
        "value": current,
        "label": label,
        "avg_7d": round(avg_7d, 1),
        "trend": trend,
        "contrarian_signal": contrarian,
        "interpretation": ". ".join(parts),
    })
    return result


def interpret_coinbase_premium(data: list) -> dict:
    """Interpret Coinbase Premium Index — US institutional buying/selling signal."""
    result = {
        "premium_usd": 0.0, "premium_rate": 0.0, "premium_rate_pct": "0.00%",
        "avg_rate": 0.0,
        "bias": "neutral",
        "interpretation": "No Coinbase Premium data available",
    }

    if not data or not isinstance(data, list):
        return result

    latest = data[-1] if isinstance(data[-1], dict) else {}
    premium = float(latest.get("premium", 0) or 0)
    rate = float(latest.get("premium_rate", 0) or 0)

    rates = [float(d.get("premium_rate", 0) or 0) for d in data if isinstance(d, dict)]
    avg_rate = sum(rates) / len(rates) if rates else 0

    if rate > 0.0005:
        bias = "us_buying"
    elif rate < -0.0005:
        bias = "us_selling"
    else:
        bias = "neutral"

    sign = "+" if rate >= 0 else ""
    rate_pct = f"{sign}{rate*100:.2f}%"

    parts = []
    parts.append(f"Coinbase Premium: ${premium:,.2f} ({rate_pct})")
    if bias == "us_buying":
        parts.append("US institutions buying above global price — bullish institutional demand")
    elif bias == "us_selling":
        parts.append("US institutions selling below global price — bearish institutional flow")
    else:
        parts.append("Neutral premium — no significant US/global price divergence")

    result.update({
        "premium_usd": premium,
        "premium_rate": round(rate, 6),
        "premium_rate_pct": rate_pct,
        "avg_rate": round(avg_rate, 6),
        "bias": bias,
        "interpretation": ". ".join(parts),
    })
    return result


# ===========================================================================
# Helpers
# ===========================================================================

def _fmt_usd(value: float) -> str:
    """Format USD amount."""
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:.0f}"


# ===========================================================================
# Report rendering
# ===========================================================================

def render_report(symbol: str, current_price: float,
                  liq_data: dict, max_pain_interp: dict,
                  options_interp: dict, setup: dict) -> str:
    """Render full liquidity report to stdout."""
    lines = []
    lines.append(f"\n{'─' * 65}")
    lines.append(f"  💧 LIQUIDITY REPORT — {symbol.upper()} @ ${current_price:,.2f}")
    lines.append(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"{'─' * 65}")

    # Liquidation summary
    lines.append(f"\n  📊 LIQUIDATION ACTIVITY")
    lines.append(f"  {liq_data['interpretation']}")

    tf = liq_data.get("timeframe_breakdown", {})
    if tf:
        lines.append(f"\n  {'Period':<8} {'Total':>12} {'Long':>12} {'Short':>12}")
        lines.append(f"  {'─' * 46}")
        for period in ["24h", "12h", "4h", "1h"]:
            if period in tf:
                t = tf[period]
                lines.append(f"  {period:<8} {_fmt_usd(t['total']):>12} {_fmt_usd(t['long']):>12} {_fmt_usd(t['short']):>12}")

    # Options Max Pain
    lines.append(f"\n  🎯 OPTIONS MAX PAIN")
    lines.append(f"  {max_pain_interp['interpretation']}")

    expiries = max_pain_interp.get("expiries", [])
    if expiries:
        lines.append(f"\n  {'Expiry':<10} {'Max Pain':>12} {'Distance':>10} {'P/C Ratio':>10}")
        lines.append(f"  {'─' * 44}")
        for e in expiries[:5]:
            lines.append(f"  {e['date']:<10} ${e['max_pain_price']:>10,.0f} {e['distance_pct']:>+9.1f}% {e['put_call_ratio']:>9.2f}x")

    # Options Info
    if options_interp.get("total_oi_usd", 0) > 0:
        lines.append(f"\n  📋 OPTIONS OVERVIEW")
        lines.append(f"  {options_interp['interpretation']}")

    # Setup detection
    lines.append(f"\n  {'─' * 63}")
    if setup["detected"]:
        emoji = "🟢" if setup["direction"] == "long" else "🔴"
        lines.append(f"  {emoji} LIQUIDITY GRAB FADE DETECTED — {setup['direction'].upper()}")
        lines.append(f"  Confidence: {setup['confidence'].upper()}")
        lines.append(f"  {setup['thesis']}")
        if setup["snap_back_target"]:
            lines.append(f"  Snap-back target: ${setup['snap_back_target']:,.0f}")
    else:
        lines.append(f"  ⚪ No Liquidity Grab Fade setup detected")

    lines.append(f"{'─' * 65}")
    return "\n".join(lines)


def save_report(symbol: str, data: dict) -> str:
    """Save full liquidity data to JSON file."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    path = REPORTS_DIR / f"cg_liquidity_{symbol.upper()}_{timestamp}.json"

    output = {
        "fetched_at": datetime.now().isoformat(),
        "symbol": symbol.upper(),
        **data,
    }

    with open(path, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    return str(path)


def render_scan(coins: list, top_n: int = 20) -> str:
    """Render coin liquidation scan."""
    # Sort by 24h total liquidations
    scored = []
    for coin in coins:
        if not isinstance(coin, dict):
            continue
        sym = coin.get("symbol", "?")
        total = float(coin.get("liquidation_usd_24h", 0) or 0)
        long_liq = float(coin.get("long_liquidation_usd_24h", 0) or 0)
        short_liq = float(coin.get("short_liquidation_usd_24h", 0) or 0)
        total_1h = float(coin.get("liquidation_usd_1h", 0) or 0)
        ls_ratio = long_liq / short_liq if short_liq > 0 else (99.0 if long_liq > 0 else 1.0)
        scored.append((total, sym, long_liq, short_liq, ls_ratio, total_1h))

    scored.sort(key=lambda x: x[0], reverse=True)

    lines = []
    lines.append(f"\n{'─' * 75}")
    lines.append(f"  💧 COIN LIQUIDATION SCAN ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    lines.append(f"{'─' * 75}")
    lines.append(f"  {'Symbol':<10} {'24h Total':>12} {'Long':>12} {'Short':>12} {'L/S':>6} {'1h':>10}")
    lines.append(f"  {'─' * 73}")

    for total, sym, long_liq, short_liq, ls_ratio, total_1h in scored[:top_n]:
        if total < 1000:
            continue
        bias = "📉" if ls_ratio > 2.0 else "📈" if ls_ratio < 0.5 else "  "
        accel = "⚡" if total_1h > (total / 24) * 1.5 and total_1h > 10000 else "  "
        lines.append(
            f"  {sym:<10} {_fmt_usd(total):>12} {_fmt_usd(long_liq):>12} {_fmt_usd(short_liq):>12} "
            f"{ls_ratio:>5.1f}x {_fmt_usd(total_1h):>10} {bias}{accel}"
        )

    lines.append(f"\n  📉 = Long pain (bearish)  📈 = Short pain (bullish)  ⚡ = 1h acceleration")
    lines.append(f"  L/S > 2 = longs getting wrecked. L/S < 0.5 = shorts getting wrecked.")
    lines.append(f"{'─' * 75}")
    return "\n".join(lines)


# ===========================================================================
# Full analysis pipeline
# ===========================================================================

def run_full_analysis(symbol: str, current_price: float = 0,
                      debug: bool = False) -> dict:
    """
    Run complete liquidity analysis for a token.

    Uses 3 API calls on Hobbyist plan:
    1. Coin liquidation list (get this token's liq data)
    2. Options max pain (nearest expiry magnet)
    3. Options info (OI, volume, sentiment)
    """
    symbol = symbol.upper()
    print(f"\n  Fetching Coinglass data for {symbol}...", file=sys.stderr, flush=True)

    # 1. Coin liquidation list
    coins = fetch_coin_liquidation_list(debug=debug)
    liq_data = interpret_coin_liquidations(coins, symbol) if coins else {
        "symbol": symbol, "total_24h_usd": 0, "long_liq_24h_usd": 0,
        "short_liq_24h_usd": 0, "long_short_ratio": 1.0, "bias": "balanced",
        "recent_acceleration": False, "timeframe_breakdown": {},
        "interpretation": "Liquidation data unavailable",
    }

    # 2. Options max pain (only BTC and ETH have liquid options)
    max_pain_data = None
    max_pain_interp = {
        "nearest_expiry": None, "max_pain_price": 0, "distance_pct": 0,
        "direction": "at", "put_call_oi_ratio": 1.0, "expiries": [],
        "interpretation": f"No options market for {symbol}" if symbol not in ("BTC", "ETH") else "Options max pain unavailable",
    }
    if symbol in ("BTC", "ETH"):
        max_pain_data = fetch_options_max_pain(symbol, debug=debug)
        if max_pain_data:
            max_pain_interp = interpret_options_max_pain(max_pain_data, current_price)

    # 3. Options info
    options_info_data = None
    options_interp = {
        "total_oi_usd": 0, "volume_24h_usd": 0, "oi_change_24h_pct": 0,
        "interpretation": "Options info unavailable",
    }
    if symbol in ("BTC", "ETH"):
        options_info_data = fetch_options_info(symbol, debug=debug)
        if options_info_data:
            options_interp = interpret_options_info(options_info_data)

    # Detect setup
    setup = detect_liquidity_grab_setup(liq_data, max_pain_interp, options_interp, current_price)

    return {
        "symbol": symbol,
        "current_price": current_price,
        "liquidation": liq_data,
        "max_pain": max_pain_interp,
        "options": options_interp,
        "setup": setup,
        "raw": {
            "coin_list_match": liq_data,
            "max_pain": max_pain_data,
            "options_info": options_info_data,
        },
    }


# ===========================================================================
# Derivatives analysis pipeline (new)
# ===========================================================================

def run_derivatives_analysis(symbol: str, current_price: float = 0,
                              debug: bool = False) -> dict:
    """
    Run complete derivatives analysis for a token.
    Combines: funding rates + OI history + OI exchange snapshot +
    global L/S ratio + top L/S ratios + existing liquidity analysis.
    """
    symbol = symbol.upper()
    print(f"\n  Fetching derivatives intelligence for {symbol}...", file=sys.stderr, flush=True)

    # 1. Funding rates (returns all symbols in one call)
    funding_data = fetch_funding_rates(symbol, debug=debug)
    funding_interp = interpret_funding_rates(funding_data, symbol) if funding_data else {
        "symbol": symbol, "avg_rate": 0, "avg_rate_pct": "N/A",
        "bias": "neutral", "interpretation": "Funding rate data unavailable",
    }

    # 2. OI history
    oi_history = fetch_oi_history(symbol, debug=debug)
    oi_history_interp = interpret_oi_history(oi_history, symbol) if oi_history else {
        "symbol": symbol, "current_oi_usd": 0, "oi_trend": "flat",
        "interpretation": "OI history unavailable",
    }

    # 3. OI exchange snapshot
    oi_exchanges = fetch_oi_exchange_list(symbol, debug=debug)
    oi_exchange_interp = interpret_oi_exchange_snapshot(oi_exchanges, symbol) if oi_exchanges else {
        "symbol": symbol, "total_oi_usd": 0, "momentum": "stable",
        "interpretation": "OI exchange data unavailable",
    }

    # 4. Global L/S ratio
    global_ls = fetch_global_ls_ratio(symbol, debug=debug)
    global_ls_interp = interpret_global_ls_ratio(global_ls, symbol) if global_ls else {
        "symbol": symbol, "current_ratio": 1.0, "extreme": False,
        "interpretation": "Global L/S ratio unavailable",
    }

    # 5. Top trader L/S ratios (2 API calls)
    top_ls = fetch_top_ls_ratios(symbol, debug=debug)
    if top_ls:
        top_ls_interp = interpret_top_ls_ratios(
            top_ls.get("account", []), top_ls.get("position", []), symbol)
    else:
        top_ls_interp = {
            "symbol": symbol, "smart_money_lean": "neutral",
            "interpretation": "Top trader L/S data unavailable",
        }

    # 6. Existing liquidity analysis (liquidation + options)
    liquidity = run_full_analysis(symbol, current_price=current_price, debug=debug)

    return {
        "symbol": symbol,
        "current_price": current_price,
        "funding": funding_interp,
        "open_interest": {
            "history": oi_history_interp,
            "exchanges": oi_exchange_interp,
        },
        "long_short": {
            "global": global_ls_interp,
            "top_traders": top_ls_interp,
        },
        "liquidation": liquidity.get("liquidation", {}),
        "max_pain": liquidity.get("max_pain", {}),
        "options": liquidity.get("options", {}),
        "setup": liquidity.get("setup", {}),
    }


def run_market_pulse(debug: bool = False) -> dict:
    """
    Run market-wide derivatives pulse.
    BTC + ETH funding rates + OI snapshots + BTC L/S + top L/S +
    BTC ETF flows + Fear & Greed + Coinbase Premium.
    """
    print(f"\n  Fetching market derivatives pulse...", file=sys.stderr, flush=True)

    # Funding rates (single call returns all symbols)
    funding_data = fetch_funding_rates("BTC", debug=debug)
    btc_funding = interpret_funding_rates(funding_data, "BTC") if funding_data else {
        "symbol": "BTC", "bias": "neutral", "interpretation": "Unavailable"}
    eth_funding = interpret_funding_rates(funding_data, "ETH") if funding_data else {
        "symbol": "ETH", "bias": "neutral", "interpretation": "Unavailable"}

    # OI exchange snapshots (2 calls)
    btc_oi = fetch_oi_exchange_list("BTC", debug=debug)
    btc_oi_interp = interpret_oi_exchange_snapshot(btc_oi, "BTC") if btc_oi else {
        "symbol": "BTC", "momentum": "stable", "interpretation": "Unavailable"}
    eth_oi = fetch_oi_exchange_list("ETH", debug=debug)
    eth_oi_interp = interpret_oi_exchange_snapshot(eth_oi, "ETH") if eth_oi else {
        "symbol": "ETH", "momentum": "stable", "interpretation": "Unavailable"}

    # BTC Global L/S ratio
    btc_ls = fetch_global_ls_ratio("BTC", debug=debug)
    btc_ls_interp = interpret_global_ls_ratio(btc_ls, "BTC") if btc_ls else {
        "symbol": "BTC", "current_ratio": 1.0, "interpretation": "Unavailable"}

    # BTC Top trader L/S
    btc_top_ls = fetch_top_ls_ratios("BTC", debug=debug)
    if btc_top_ls:
        btc_top_ls_interp = interpret_top_ls_ratios(
            btc_top_ls.get("account", []), btc_top_ls.get("position", []), "BTC")
    else:
        btc_top_ls_interp = {"symbol": "BTC", "smart_money_lean": "neutral",
                              "interpretation": "Unavailable"}

    # BTC ETF flows
    etf_data = fetch_btc_etf_flows(debug=debug)
    etf_interp = interpret_btc_etf_flows(etf_data) if etf_data else {
        "bias": "mixed", "interpretation": "Unavailable"}

    # Fear & Greed
    fg_data = fetch_fear_greed(debug=debug)
    fg_interp = interpret_fear_greed(fg_data) if fg_data else {
        "value": 0, "label": "Unknown", "interpretation": "Unavailable"}

    # Coinbase Premium
    cb_data = fetch_coinbase_premium(debug=debug)
    cb_interp = interpret_coinbase_premium(cb_data) if cb_data else {
        "bias": "neutral", "interpretation": "Unavailable"}

    return {
        "btc_funding": btc_funding,
        "eth_funding": eth_funding,
        "btc_oi": btc_oi_interp,
        "eth_oi": eth_oi_interp,
        "btc_ls": btc_ls_interp,
        "btc_top_ls": btc_top_ls_interp,
        "etf": etf_interp,
        "fear_greed": fg_interp,
        "coinbase_premium": cb_interp,
    }


# ===========================================================================
# Report rendering — Derivatives Intelligence (new)
# ===========================================================================

def render_derivatives_report(symbol: str, current_price: float, data: dict) -> str:
    """Render full derivatives intelligence report to stdout."""
    lines = []
    lines.append(f"\n{'─' * 65}")
    lines.append(f"  📊 DERIVATIVES INTELLIGENCE — {symbol.upper()} @ ${current_price:,.2f}")
    lines.append(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"{'─' * 65}")

    # Funding
    f = data.get("funding", {})
    lines.append(f"\n  💰 FUNDING RATES")
    lines.append(f"  {f.get('interpretation', 'N/A')}")

    # OI
    oi_hist = data.get("open_interest", {}).get("history", {})
    oi_ex = data.get("open_interest", {}).get("exchanges", {})
    lines.append(f"\n  📈 OPEN INTEREST")
    lines.append(f"  {oi_hist.get('interpretation', 'N/A')}")
    lines.append(f"  {oi_ex.get('interpretation', 'N/A')}")

    # L/S Ratios
    gl = data.get("long_short", {}).get("global", {})
    tl = data.get("long_short", {}).get("top_traders", {})
    lines.append(f"\n  ⚖️  LONG/SHORT RATIOS")
    lines.append(f"  {gl.get('interpretation', 'N/A')}")
    lines.append(f"  {tl.get('interpretation', 'N/A')}")

    # Liquidation (from existing)
    liq = data.get("liquidation", {})
    lines.append(f"\n  💧 LIQUIDATION ACTIVITY")
    lines.append(f"  {liq.get('interpretation', 'N/A')}")

    # Max Pain
    mp = data.get("max_pain", {})
    if mp.get("max_pain_price", 0) > 0:
        lines.append(f"\n  🎯 OPTIONS MAX PAIN")
        lines.append(f"  {mp.get('interpretation', 'N/A')}")

    # Setup
    setup = data.get("setup", {})
    lines.append(f"\n  {'─' * 63}")
    if setup.get("detected"):
        emoji = "🟢" if setup.get("direction") == "long" else "🔴"
        lines.append(f"  {emoji} LIQUIDITY GRAB FADE DETECTED — {setup.get('direction', '').upper()}")
        lines.append(f"  Confidence: {setup.get('confidence', '').upper()}")
        lines.append(f"  {setup.get('thesis', '')}")
    else:
        lines.append(f"  ⚪ No Liquidity Grab Fade setup detected")

    lines.append(f"{'─' * 65}")
    return "\n".join(lines)


def render_market_pulse(data: dict) -> str:
    """Render market derivatives pulse report to stdout."""
    lines = []
    lines.append(f"\n{'─' * 65}")
    lines.append(f"  🌐 MARKET DERIVATIVES PULSE")
    lines.append(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"{'─' * 65}")

    # Fear & Greed
    fg = data.get("fear_greed", {})
    lines.append(f"\n  😱 FEAR & GREED")
    lines.append(f"  {fg.get('interpretation', 'N/A')}")

    # Coinbase Premium
    cb = data.get("coinbase_premium", {})
    lines.append(f"\n  🏦 COINBASE PREMIUM")
    lines.append(f"  {cb.get('interpretation', 'N/A')}")

    # Funding Rates
    bf = data.get("btc_funding", {})
    ef = data.get("eth_funding", {})
    lines.append(f"\n  💰 FUNDING RATES")
    lines.append(f"  BTC: {bf.get('avg_rate_pct', 'N/A')} — {bf.get('bias', 'N/A')}")
    lines.append(f"  ETH: {ef.get('avg_rate_pct', 'N/A')} — {ef.get('bias', 'N/A')}")

    # OI
    bo = data.get("btc_oi", {})
    eo = data.get("eth_oi", {})
    lines.append(f"\n  📈 OPEN INTEREST")
    lines.append(f"  BTC: {_fmt_usd(bo.get('total_oi_usd', 0))} ({bo.get('change_24h_pct', 0):+.1f}% 24h) — {bo.get('momentum', 'N/A')}")
    lines.append(f"  ETH: {_fmt_usd(eo.get('total_oi_usd', 0))} ({eo.get('change_24h_pct', 0):+.1f}% 24h) — {eo.get('momentum', 'N/A')}")

    # BTC L/S
    bl = data.get("btc_ls", {})
    bt = data.get("btc_top_ls", {})
    lines.append(f"\n  ⚖️  BTC LONG/SHORT")
    lines.append(f"  Global: {bl.get('current_ratio', 1.0):.2f}x ({bl.get('current_long_pct', 50):.1f}% long)")
    lines.append(f"  Top Trader Lean: {bt.get('smart_money_lean', 'neutral').upper()}")

    # ETF
    etf = data.get("etf", {})
    lines.append(f"\n  🏛️  BTC ETF FLOWS")
    lines.append(f"  {etf.get('interpretation', 'N/A')}")

    lines.append(f"\n{'─' * 65}")
    return "\n".join(lines)


# ===========================================================================
# Snapshot-all orchestrator (cron pipeline)
# ===========================================================================

def run_snapshot_all(debug: bool = False) -> dict:
    """
    Run all snapshot endpoints for the 6h cron pipeline.
    Fetches ~35 endpoints, stores into titan_intelligence.db snapshot tables.
    Returns summary dict with counts.
    """
    import uuid as _uuid
    run_id = str(_uuid.uuid4())[:8]
    started = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Import storage
    try:
        from src.storage.intelligence import (
            log_cg_snapshot, log_snapshot_run, finish_snapshot_run,
            log_derivatives_snapshot, log_market_snapshot)
        log_snapshot_run(run_id, "coinglass")
    except Exception as e:
        print(f"  Warning: Could not init snapshot metadata: {e}", file=sys.stderr)

    succeeded = 0
    failed = 0
    rows = 0
    errors = []

    def _snap(label, fetch_fn, table, symbol=None, endpoint=None,
              interval=None, model=None, indicator=None):
        nonlocal succeeded, failed, rows, errors
        try:
            print(f"  [{label}] Fetching...", end=" ", flush=True, file=sys.stderr)
            data = fetch_fn()
            if data is None:
                print("EMPTY", file=sys.stderr)
                failed += 1
                errors.append(f"{label}: returned None")
                return
            row_id = log_cg_snapshot(
                table, symbol=symbol, endpoint=endpoint, data=data,
                interval=interval, model=model, indicator=indicator)
            if row_id > 0:
                print("OK", file=sys.stderr)
                succeeded += 1
                rows += 1
            else:
                print("STORE_FAIL", file=sys.stderr)
                failed += 1
                errors.append(f"{label}: storage failed")
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            failed += 1
            errors.append(f"{label}: {str(e)[:100]}")

    print(f"\n  === Coinglass Snapshot Run {run_id} ===", file=sys.stderr)
    print(f"  Started: {started}", file=sys.stderr)

    # ── 1. Spot CVD & Taker (BTC, ETH) ──
    for sym in ["BTC", "ETH"]:
        _snap(f"Spot CVD {sym}",
              lambda s=sym: fetch_spot_aggregated_cvd(s, debug=debug),
              "spot_flow_snapshots", symbol=sym, endpoint="aggregated_cvd", interval="h4")
        _snap(f"Spot Taker {sym}",
              lambda s=sym: fetch_spot_taker_buy_sell(s, debug=debug),
              "spot_flow_snapshots", symbol=sym, endpoint="taker_buy_sell", interval="h4")
        _snap(f"Spot Netflow {sym}",
              lambda s=sym: fetch_spot_netflow_list(s, debug=debug),
              "spot_flow_snapshots", symbol=sym, endpoint="netflow_list")
        _snap(f"Spot Coin Netflow {sym}",
              lambda s=sym: fetch_spot_coin_netflow(s, debug=debug),
              "spot_flow_snapshots", symbol=sym, endpoint="coin_netflow")

    # ── 2. Futures Basis & Speculation ──
    for sym in ["BTC", "ETH"]:
        _snap(f"Futures Basis {sym}",
              lambda s=sym: fetch_futures_basis(s, debug=debug),
              "basis_snapshots", symbol=sym, endpoint="futures_basis", interval="h4")
    for sym in ["BTC", "ETH"]:
        _snap(f"Futures/Spot Vol Ratio {sym}",
              lambda s=sym: fetch_futures_spot_volume_ratio(s, debug=debug),
              "basis_snapshots", symbol=sym, endpoint="futures_spot_vol_ratio", interval="h4")
    _snap("Options/Futures OI Ratio",
          lambda: fetch_options_futures_oi_ratio(debug=debug),
          "basis_snapshots", symbol="_MARKET", endpoint="options_futures_oi_ratio")

    # ── 3. Large Orders & Orderbook ──
    for sym in ["BTC", "ETH"]:
        _snap(f"Large Orders {sym}",
              lambda s=sym: fetch_large_limit_orders(s, debug=debug),
              "orderbook_snapshots", symbol=sym, endpoint="large_limit_order")
        _snap(f"Agg Orderbook {sym}",
              lambda s=sym: fetch_aggregated_orderbook(s, debug=debug),
              "orderbook_snapshots", symbol=sym, endpoint="aggregated_ask_bids", interval="h4")

    # ── 4. OI by Exchange ──
    for sym in ["BTC", "ETH"]:
        _snap(f"OI Exchange Hist {sym}",
              lambda s=sym: fetch_oi_exchange_history(s, range_val="4h", debug=debug),
              "oi_exchange_snapshots", symbol=sym, interval="4h")

    # ── 5. Liquidation Heatmaps ──
    for sym in ["BTC", "ETH"]:
        _snap(f"Liq Heatmap M1 {sym}",
              lambda s=sym: fetch_liq_heatmap_model1(s, debug=debug),
              "liquidation_heatmap_snapshots", symbol=sym, model="model1")
        _snap(f"Liq Heatmap M3 {sym}",
              lambda s=sym: fetch_liq_heatmap_model3(s, debug=debug),
              "liquidation_heatmap_snapshots", symbol=sym, model="model3")

    # ── 6. BTC Macro On-Chain ──
    btc_onchain = [
        ("STH SOPR", fetch_btc_sth_sopr, "sth_sopr"),
        ("LTH SOPR", fetch_btc_lth_sopr, "lth_sopr"),
        ("STH Realized Price", fetch_btc_sth_realized_price, "sth_realized_price"),
        ("LTH Realized Price", fetch_btc_lth_realized_price, "lth_realized_price"),
        ("NUPL", fetch_btc_nupl, "nupl"),
        ("Active Addresses", fetch_btc_active_addresses, "active_addresses"),
        ("Reserve Risk", fetch_btc_reserve_risk, "reserve_risk"),
        ("Correlation", fetch_btc_correlation, "correlation"),
        ("Macro Oscillator", fetch_btc_macro_oscillator, "macro_oscillator"),
    ]
    for label, fn, ind in btc_onchain:
        _snap(f"BTC {label}",
              lambda f=fn: f(debug=debug),
              "btc_onchain_snapshots", symbol="BTC", indicator=ind)

    # Coinbase Premium (uses existing function)
    _snap("Coinbase Premium",
          lambda: fetch_coinbase_premium(interval="h4", limit=6, debug=debug),
          "btc_onchain_snapshots", symbol="BTC", indicator="coinbase_premium")

    # ── 7. ETF Detail ──
    _snap("BTC ETF Net Assets",
          lambda: fetch_btc_etf_net_assets(debug=debug),
          "etf_flow_snapshots", symbol="BTC", endpoint="net_assets")
    _snap("BTC ETF Premium/Discount",
          lambda: fetch_btc_etf_premium_discount(debug=debug),
          "etf_flow_snapshots", symbol="BTC", endpoint="premium_discount")
    _snap("Grayscale Premium",
          lambda: fetch_grayscale_premium(debug=debug),
          "etf_flow_snapshots", symbol="BTC", endpoint="grayscale_premium")

    # ── 8. Existing derivatives + market pulse (bonus — also store to time-series) ──
    try:
        pulse = run_market_pulse(debug=debug)
        if pulse:
            log_market_snapshot(pulse)
            succeeded += 1
            rows += 2  # BTC + ETH rows
            print(f"  [Market Pulse] OK", file=sys.stderr)
    except Exception as e:
        failed += 1
        errors.append(f"market_pulse: {str(e)[:100]}")
        print(f"  [Market Pulse] ERROR: {e}", file=sys.stderr)

    for sym in ["BTC", "ETH"]:
        try:
            analysis = run_derivatives_analysis(sym, debug=debug)
            if analysis:
                log_derivatives_snapshot(analysis)
                succeeded += 1
                rows += 1
                print(f"  [Derivatives {sym}] OK", file=sys.stderr)
        except Exception as e:
            failed += 1
            errors.append(f"derivatives_{sym}: {str(e)[:100]}")
            print(f"  [Derivatives {sym}] ERROR: {e}", file=sys.stderr)

    # Finish metadata
    try:
        finish_snapshot_run(run_id, succeeded, failed, rows, errors or None)
    except Exception:
        pass

    finished = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"\n  === Snapshot Complete ===", file=sys.stderr)
    print(f"  Run ID: {run_id}", file=sys.stderr)
    print(f"  Finished: {finished}", file=sys.stderr)
    print(f"  Succeeded: {succeeded} | Failed: {failed} | Rows: {rows}", file=sys.stderr)
    if errors:
        print(f"  Errors:", file=sys.stderr)
        for e in errors:
            print(f"    - {e}", file=sys.stderr)

    return {
        "run_id": run_id,
        "started": started,
        "finished": finished,
        "succeeded": succeeded,
        "failed": failed,
        "rows_inserted": rows,
        "errors": errors,
    }


# ===========================================================================
# CLI
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="Coinglass Derivatives Intelligence")
    parser.add_argument("--token", type=str, help="Token symbol (e.g., BTC, ETH)")
    parser.add_argument("--price", type=float, default=0, help="Current price (for max pain interpretation)")
    parser.add_argument("--scan", action="store_true", help="Scan all coins by liquidation volume")
    parser.add_argument("--derivatives", action="store_true",
                        help="Full derivatives analysis (funding, OI, L/S, liquidation)")
    parser.add_argument("--market", action="store_true",
                        help="Market derivatives pulse (ETF, F&G, premium, BTC/ETH funding+OI+L/S)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON to stdout")
    parser.add_argument("--debug", action="store_true", help="Print raw API responses to stderr")
    parser.add_argument("--no-save", action="store_true", help="Don't save to file")
    parser.add_argument("--snapshot-all", action="store_true",
                        help="Cron mode: snapshot all endpoints into titan_intelligence.db")
    args = parser.parse_args()

    if not args.token and not args.scan and not args.market and not args.snapshot_all:
        parser.print_help()
        sys.exit(1)

    api_key = _get_api_key()
    if not api_key:
        print("\n  COINGLASS_API_KEY not set.")
        print("  Add your key to .env: COINGLASS_API_KEY=your_key_here")
        sys.exit(1)

    # --snapshot-all mode: cron pipeline
    if args.snapshot_all:
        # PID file to prevent concurrent runs
        pid_file = PROJECT_ROOT / "logs" / "coinglass_snapshot.pid"
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        if pid_file.exists():
            try:
                old_pid = int(pid_file.read_text().strip())
                # Check if PID is still running
                os.kill(old_pid, 0)
                print(f"Snapshot already running (PID {old_pid}). Skipping.", file=sys.stderr)
                sys.exit(0)
            except (ProcessLookupError, ValueError):
                pass  # Stale PID file, continue
        pid_file.write_text(str(os.getpid()))
        try:
            result = run_snapshot_all(debug=args.debug)
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            sys.exit(0 if result["failed"] == 0 else 1)
        finally:
            try:
                pid_file.unlink()
            except Exception:
                pass
        return

    # --market mode: macro dashboard
    if args.market:
        pulse = run_market_pulse(debug=args.debug)
        if args.json:
            print(json.dumps(pulse, indent=2, default=str))
        else:
            print(render_market_pulse(pulse))
        if not args.no_save:
            path = save_report("MARKET_PULSE", pulse)
            print(f"\n  💾 Saved to: {path}")
            # Log to time-series DB
            try:
                from src.storage.intelligence import log_market_snapshot
                log_market_snapshot(pulse)
            except Exception as e:
                print(f"  ⚠️  Market pulse logging failed: {e}", file=sys.stderr)
        return

    # --scan mode: coin liquidation scan
    if args.scan:
        print(f"\n  Scanning coin liquidation list...", end=" ", flush=True)
        coins = fetch_coin_liquidation_list(debug=args.debug)
        if not coins:
            print("❌ Failed")
            sys.exit(1)

        print(f"✓ ({len(coins)} coins)")
        if args.json:
            print(json.dumps(coins, indent=2, default=str))
        else:
            print(render_scan(coins))
        return

    # --derivatives mode: full per-token derivatives analysis
    if args.derivatives:
        if args.price <= 0 and not args.json:
            print(f"\n  ⚠️  Pass --price for max pain interpretation (e.g., --price 84000)")
        analysis = run_derivatives_analysis(args.token, current_price=args.price, debug=args.debug)
        if args.json:
            print(json.dumps(analysis, indent=2, default=str))
        else:
            print(render_derivatives_report(analysis["symbol"], analysis["current_price"], analysis))
        if not args.no_save:
            path = save_report(analysis["symbol"], analysis)
            print(f"\n  💾 Saved to: {path}")
            # Log to time-series DB
            try:
                from src.storage.intelligence import log_derivatives_snapshot
                log_derivatives_snapshot(analysis)
            except Exception as e:
                print(f"  ⚠️  Derivatives logging failed: {e}", file=sys.stderr)
        return

    # Default: original liquidity report (backward compatible)
    if args.price <= 0 and not args.json:
        print(f"\n  ⚠️  Pass --price for max pain interpretation (e.g., --price 84000)")

    analysis = run_full_analysis(args.token, current_price=args.price, debug=args.debug)

    if args.json:
        output = {k: v for k, v in analysis.items() if k != "raw"}
        print(json.dumps(output, indent=2, default=str))
    else:
        report = render_report(
            analysis["symbol"],
            analysis["current_price"],
            analysis["liquidation"],
            analysis["max_pain"],
            analysis["options"],
            analysis["setup"],
        )
        print(report)

    if not args.no_save:
        path = save_report(analysis["symbol"], analysis)
        print(f"\n  💾 Saved to: {path}")


if __name__ == "__main__":
    main()
