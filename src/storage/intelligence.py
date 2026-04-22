#!/usr/bin/env python3
"""
Titan Terminal v3
===========================
Query/response tracking for MCP calls, LLM interpretations, and trade cards.
Enables future model evaluation and cost tracking.

Storage: SQLite (data/titan_intelligence.db)
"""

import sqlite3
import json
import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List, Any

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "titan_intelligence.db"
COWORK_DB_PATH = Path("/Users/johnny_main/Developer/Claude_Cowork/Alpha-Terminal/database/titan_intelligence.db")

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

SCHEMA = """
-- Track every MCP tool call
CREATE TABLE IF NOT EXISTS mcp_queries (
    id INTEGER PRIMARY KEY,
    query_id TEXT UNIQUE,
    timestamp_utc TEXT,
    tool_name TEXT,
    tool_source TEXT,
    parameters_json TEXT,
    context_type TEXT,
    context_token TEXT,
    success INTEGER DEFAULT 1
);

-- Store raw API responses
CREATE TABLE IF NOT EXISTS mcp_responses (
    id INTEGER PRIMARY KEY,
    query_id TEXT REFERENCES mcp_queries(query_id),
    response_json TEXT,
    response_size_bytes INTEGER,
    created_at TEXT
);

-- Store LLM interpretations (for future evaluation)
CREATE TABLE IF NOT EXISTS llm_interpretations (
    id INTEGER PRIMARY KEY,
    interpretation_id TEXT UNIQUE,
    query_ids TEXT,
    timestamp_utc TEXT,
    interpretation_type TEXT,
    token TEXT,
    signal TEXT,
    confidence TEXT,
    summary TEXT,
    model_version TEXT,
    tokens_used INTEGER,
    evaluation_score REAL,
    evaluation_notes TEXT,
    evaluated_by TEXT,
    evaluated_at TEXT
);

-- Store complete Trade Cards
CREATE TABLE IF NOT EXISTS trade_cards (
    id INTEGER PRIMARY KEY,
    card_id TEXT UNIQUE,
    timestamp_utc TEXT,
    token TEXT,
    verdict TEXT,
    full_markdown TEXT,
    total_tokens_used INTEGER,
    accuracy_score REAL,
    price_at_evaluation REAL,
    evaluated_at TEXT
);

-- CEX health snapshots (time-series alongside JSON)
CREATE TABLE IF NOT EXISTS cex_snapshots (
    id INTEGER PRIMARY KEY,
    snapshot_id TEXT UNIQUE,
    timestamp_utc TEXT,
    asset TEXT,
    exchange_inflows REAL,
    exchange_outflows REAL,
    net_flow REAL,
    signal TEXT,
    raw_json TEXT
);

-- Mentor consultations (Opus 4.6 second opinions)
CREATE TABLE IF NOT EXISTS mentor_consultations (
    id INTEGER PRIMARY KEY,
    consultation_id TEXT UNIQUE,
    timestamp_utc TEXT,

    -- Context
    token TEXT,
    question_type TEXT,
    initial_verdict TEXT,
    initial_confidence REAL,

    -- Query
    question_asked TEXT,
    context_provided TEXT,

    -- Response
    mentor_agrees INTEGER,
    confidence_adjustment REAL,
    mentor_reasoning TEXT,
    suggested_action TEXT,

    -- Tracking
    tokens_used INTEGER,
    model TEXT,
    api_cost_usd REAL,

    -- Evaluation (backtest later)
    final_decision TEXT,
    outcome_correct INTEGER,
    evaluation_notes TEXT
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_mcp_queries_tool ON mcp_queries(tool_name);
CREATE INDEX IF NOT EXISTS idx_mcp_queries_context ON mcp_queries(context_type, context_token);
CREATE INDEX IF NOT EXISTS idx_mcp_queries_timestamp ON mcp_queries(timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_trade_cards_token ON trade_cards(token);
CREATE INDEX IF NOT EXISTS idx_trade_cards_timestamp ON trade_cards(timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_cex_snapshots_asset ON cex_snapshots(asset, timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_mentor_token ON mentor_consultations(token);
CREATE INDEX IF NOT EXISTS idx_mentor_timestamp ON mentor_consultations(timestamp_utc);

-- Token flow snapshots for time-series tracking
CREATE TABLE IF NOT EXISTS flow_snapshots (
    id INTEGER PRIMARY KEY,
    snapshot_id TEXT UNIQUE,
    timestamp_utc TEXT,
    token TEXT,
    chain TEXT,
    token_address TEXT,
    price_usd REAL,

    -- Exchange flows (from token_recent_flows_summary)
    exchange_net_flow REAL,
    exchange_flow_ratio REAL,
    exchange_wallets INTEGER,
    exchange_signal TEXT,

    -- Fresh wallet flows
    fresh_wallet_net_flow REAL,
    fresh_wallet_ratio REAL,
    fresh_wallet_count INTEGER,
    fresh_wallet_signal TEXT,

    -- Smart money flows
    smart_money_net_flow REAL,
    smart_money_ratio REAL,
    smart_money_wallets INTEGER,
    smart_money_signal TEXT,

    -- Top PnL trader flows
    top_pnl_net_flow REAL,
    top_pnl_ratio REAL,
    top_pnl_wallets INTEGER,
    top_pnl_signal TEXT,

    -- Whale flows
    whale_net_flow REAL,
    whale_ratio REAL,
    whale_wallets INTEGER,
    whale_signal TEXT,

    -- Aggregate metrics
    accumulation_score INTEGER,  -- 0-5 count of bullish signals
    overall_signal TEXT,  -- "ACCUMULATING", "DISTRIBUTING", "MIXED", "QUIET"

    -- Raw data for debugging
    raw_json TEXT,
    lookback_period TEXT  -- "1d", "7d" etc
);

CREATE INDEX IF NOT EXISTS idx_flow_token ON flow_snapshots(token, timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_flow_timestamp ON flow_snapshots(timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_flow_signal ON flow_snapshots(overall_signal);

-- Signal validations (external signals validated against Titan data)
CREATE TABLE IF NOT EXISTS signal_validations (
    id INTEGER PRIMARY KEY,
    validation_id TEXT UNIQUE,
    timestamp_utc TEXT,

    -- External signal reference
    external_signal_id INTEGER,      -- ID from external signals.db
    symbol TEXT,
    direction TEXT,                  -- LONG/SHORT
    provider TEXT,                   -- Always "MarketInsights" for now
    signal_analysis TEXT,            -- MarketInsights commentary

    -- Titan validation
    accumulation_score INTEGER,      -- 0-5 Titan score
    ta_verdict TEXT,                 -- Bullish/Bearish/Neutral
    onchain_verdict TEXT,            -- Bullish/Bearish/Neutral/Mixed
    signal_aligns INTEGER,           -- Boolean: Does signal match Titan?

    -- Mentor review (if triggered)
    mentor_consulted INTEGER,        -- Boolean
    mentor_verdict TEXT,             -- Mentor's take
    mentor_confidence_adj REAL,

    -- Final recommendation
    titan_recommendation TEXT,       -- VALID/INVALID/NEEDS_CONFIRMATION
    recommendation_reason TEXT,

    -- Chart analysis
    chart_analyzed INTEGER,          -- Boolean: Was image reviewed?
    chart_notes TEXT,
    chart_path TEXT,                 -- Path to chart image

    -- Suggested trade levels (if signal looks valid)
    suggested_entry REAL,
    suggested_stop REAL,
    suggested_target REAL,

    -- Tracking
    trade_taken INTEGER,             -- Boolean: Did user take this trade?
    trade_outcome TEXT,              -- WIN/LOSS/SKIP
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_validation_symbol ON signal_validations(symbol);
CREATE INDEX IF NOT EXISTS idx_validation_timestamp ON signal_validations(timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_validation_recommendation ON signal_validations(titan_recommendation);
CREATE INDEX IF NOT EXISTS idx_validation_external_id ON signal_validations(external_signal_id);

-- Signal watchlist for ongoing monitoring
CREATE TABLE IF NOT EXISTS signal_watchlist (
    id INTEGER PRIMARY KEY,
    watch_id TEXT UNIQUE,
    created_at TEXT,
    updated_at TEXT,

    -- What we're watching
    symbol TEXT,
    chain TEXT,
    token_address TEXT,

    -- Source reference
    source_type TEXT,              -- 'telegram_signal' | 'manual' | 'skill'
    external_signal_id INTEGER,    -- FK to signals.db if telegram
    validation_id TEXT,            -- FK to signal_validations if from validation

    -- Watch configuration
    watch_type TEXT,               -- 'entry_timing' | 'confirmation' | 'structural' | 'invalidation'
    direction TEXT,                -- LONG/SHORT (expected direction)

    -- Thesis and conditions
    original_thesis TEXT,          -- Why we're watching
    entry_conditions TEXT,         -- JSON: What would trigger entry
    invalidation_conditions TEXT,  -- JSON: What would remove from watchlist
    confirmation_needed TEXT,      -- What we're waiting to see

    -- Price context at creation
    price_at_creation REAL,
    support_level REAL,
    resistance_level REAL,
    stop_level REAL,
    target_level REAL,

    -- Snapshot of original analysis
    original_accumulation_score INTEGER,
    original_ta_verdict TEXT,
    original_onchain_verdict TEXT,
    original_perps_bias TEXT,      -- 'long_heavy' | 'short_heavy' | 'balanced'

    -- Current state (updated on review)
    last_checked TEXT,
    last_price REAL,
    current_accumulation_score INTEGER,
    current_ta_verdict TEXT,
    current_onchain_verdict TEXT,
    current_perps_bias TEXT,
    status_changed INTEGER,        -- Boolean: Has analysis changed since last check?
    change_summary TEXT,           -- What changed

    -- Status
    status TEXT,                   -- 'active' | 'triggered' | 'invalidated' | 'expired' | 'taken' | 'removed'
    status_reason TEXT,            -- Why status changed
    triggered_at TEXT,
    expires_at TEXT,               -- Optional expiration

    -- Outcome tracking
    trade_taken INTEGER,           -- Boolean
    trade_setup_id TEXT,           -- FK to trade_setups if trade was taken
    outcome_notes TEXT,

    -- Review settings
    check_frequency TEXT,          -- 'session' | 'daily' | 'hourly'
    priority INTEGER DEFAULT 5,    -- 1-10, higher = more important
    notify_on_change INTEGER DEFAULT 1  -- Boolean: Alert user if analysis changes
);

CREATE INDEX IF NOT EXISTS idx_watchlist_symbol ON signal_watchlist(symbol);
CREATE INDEX IF NOT EXISTS idx_watchlist_status ON signal_watchlist(status);
CREATE INDEX IF NOT EXISTS idx_watchlist_source ON signal_watchlist(source_type);
CREATE INDEX IF NOT EXISTS idx_watchlist_last_checked ON signal_watchlist(last_checked);
CREATE INDEX IF NOT EXISTS idx_watchlist_priority ON signal_watchlist(priority DESC);

-- Daily exchange balance tracking (14-day trend — the SKY lesson)
CREATE TABLE IF NOT EXISTS exchange_balance_daily (
    id INTEGER PRIMARY KEY,
    token TEXT NOT NULL,
    date TEXT NOT NULL,
    chain TEXT,
    token_address TEXT,

    -- Balance data
    balance REAL,
    balance_usd REAL,
    inflows REAL,
    inflows_usd REAL,
    outflows REAL,
    outflows_usd REAL,
    net_flow REAL,
    net_flow_usd REAL,
    price REAL,

    -- Metadata
    source TEXT DEFAULT 'nansen',
    created_at TEXT,

    UNIQUE(token, date)
);

CREATE INDEX IF NOT EXISTS idx_exbal_token ON exchange_balance_daily(token, date);
CREATE INDEX IF NOT EXISTS idx_exbal_date ON exchange_balance_daily(date);

-- Entity position snapshots (smart money tracking over time)
CREATE TABLE IF NOT EXISTS entity_snapshots (
    id INTEGER PRIMARY KEY,
    snapshot_id TEXT,
    token TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    chain TEXT,
    token_address TEXT,

    -- Entity info
    entity_name TEXT,
    entity_address TEXT NOT NULL,
    entity_type TEXT,
    entity_label TEXT,

    -- Position data
    balance REAL,
    balance_usd REAL,
    change_1d REAL,
    change_7d REAL,
    change_30d REAL,
    ownership_pct REAL,

    -- Context
    avg_entry_price REAL,
    pnl_usd REAL,

    -- Metadata
    source TEXT DEFAULT 'nansen',
    created_at TEXT,

    UNIQUE(token, entity_address, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_entity_token ON entity_snapshots(token, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_entity_address ON entity_snapshots(entity_address);
CREATE INDEX IF NOT EXISTS idx_entity_name ON entity_snapshots(entity_name);
CREATE INDEX IF NOT EXISTS idx_entity_type ON entity_snapshots(entity_type);

-- Hunt results (scored accumulation candidates with outcome tracking)
CREATE TABLE IF NOT EXISTS hunt_results (
    id INTEGER PRIMARY KEY,
    result_id TEXT UNIQUE,
    hunt_id TEXT,
    hunt_date TEXT,

    -- Token info
    token TEXT NOT NULL,
    chain TEXT,
    token_address TEXT,
    price_at_hunt REAL,

    -- Alpha Score breakdown (0-12)
    alpha_score INTEGER,
    entity_convergence_score INTEGER,
    exchange_flow_score INTEGER,
    volume_dry_up_score INTEGER,
    perps_score INTEGER,

    -- Key metrics at time of hunt
    exchange_net_flow_usd REAL,
    exchange_flow_ratio REAL,
    num_entities_buying INTEGER,
    num_entities_selling INTEGER,
    top_entity TEXT,
    top_entity_change TEXT,

    -- Exchange balance trend
    exbal_outflow_days INTEGER,
    exbal_balance_change_pct REAL,

    -- Verdict
    verdict TEXT,
    verdict_reason TEXT,

    -- Outcome tracking (filled in later)
    price_7d_later REAL,
    price_14d_later REAL,
    price_30d_later REAL,
    pct_change_7d REAL,
    pct_change_14d REAL,
    pct_change_30d REAL,
    outcome_notes TEXT,

    -- Metadata
    created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_hunt_token ON hunt_results(token);
CREATE INDEX IF NOT EXISTS idx_hunt_date ON hunt_results(hunt_date);
CREATE INDEX IF NOT EXISTS idx_hunt_verdict ON hunt_results(verdict);
CREATE INDEX IF NOT EXISTS idx_hunt_score ON hunt_results(alpha_score DESC);
CREATE INDEX IF NOT EXISTS idx_hunt_id ON hunt_results(hunt_id);

-- Derivatives time-series snapshots (one row per token per fetch)
CREATE TABLE IF NOT EXISTS derivatives_snapshots (
    id INTEGER PRIMARY KEY,
    timestamp_utc TEXT NOT NULL,
    symbol TEXT NOT NULL,
    source TEXT NOT NULL,

    -- Price context
    price_usd REAL,

    -- Funding Rate
    funding_rate_avg REAL,
    funding_rate_max REAL,
    funding_rate_max_exchange TEXT,
    funding_bias TEXT,
    funding_annualized_pct REAL,

    -- Open Interest
    oi_usd REAL,
    oi_change_1h_pct REAL,
    oi_change_4h_pct REAL,
    oi_change_24h_pct REAL,
    oi_trend TEXT,
    oi_momentum TEXT,

    -- Long/Short Ratios
    ls_global_ratio REAL,
    ls_global_long_pct REAL,
    ls_top_account_ratio REAL,
    ls_top_position_ratio REAL,
    ls_smart_money_lean TEXT,
    ls_extreme INTEGER DEFAULT 0,
    ls_contrarian_signal TEXT,

    -- Liquidation
    liq_24h_usd REAL,
    liq_long_24h_usd REAL,
    liq_short_24h_usd REAL,
    liq_ls_ratio REAL,
    liq_bias TEXT,
    liq_acceleration INTEGER DEFAULT 0,

    -- Options (BTC/ETH only, NULL for others)
    options_max_pain REAL,
    options_max_pain_distance_pct REAL,
    options_put_call_ratio REAL,

    -- Market-level fields (only populated by market_pulse, NULL for per-token)
    fear_greed_value INTEGER,
    fear_greed_label TEXT,
    coinbase_premium_rate REAL,
    coinbase_premium_bias TEXT,
    etf_latest_day_flow_usd REAL,
    etf_weekly_net_flow_usd REAL,
    etf_streak_days INTEGER,
    etf_bias TEXT,

    -- Setup detection
    lgf_detected INTEGER DEFAULT 0,
    lgf_direction TEXT,
    lgf_confidence TEXT
);

CREATE INDEX IF NOT EXISTS idx_deriv_symbol_time ON derivatives_snapshots(symbol, timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_deriv_source ON derivatives_snapshots(source);
CREATE INDEX IF NOT EXISTS idx_deriv_timestamp ON derivatives_snapshots(timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_deriv_funding_bias ON derivatives_snapshots(funding_bias);
CREATE INDEX IF NOT EXISTS idx_deriv_ls_extreme ON derivatives_snapshots(ls_extreme);

"""

# ============================================================================
# SNAPSHOT PIPELINE TABLES (cron-fed, 6h cadence)
# ============================================================================

SNAPSHOT_SCHEMA = """
-- Spot CVD & Taker Data (Coinglass)
CREATE TABLE IF NOT EXISTS spot_flow_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_utc TEXT NOT NULL,
    symbol TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    interval TEXT,
    data_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_spot_flow_symbol ON spot_flow_snapshots(symbol, timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_spot_flow_endpoint ON spot_flow_snapshots(endpoint);

-- Futures Basis & Speculation (Coinglass)
CREATE TABLE IF NOT EXISTS basis_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_utc TEXT NOT NULL,
    symbol TEXT,
    endpoint TEXT NOT NULL,
    interval TEXT,
    data_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_basis_symbol ON basis_snapshots(symbol, timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_basis_endpoint ON basis_snapshots(endpoint);

-- Large Orders & Orderbook (Coinglass)
CREATE TABLE IF NOT EXISTS orderbook_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_utc TEXT NOT NULL,
    symbol TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    interval TEXT,
    data_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_orderbook_symbol ON orderbook_snapshots(symbol, timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_orderbook_endpoint ON orderbook_snapshots(endpoint);

-- OI by Exchange over time (Coinglass)
CREATE TABLE IF NOT EXISTS oi_exchange_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_utc TEXT NOT NULL,
    symbol TEXT NOT NULL,
    interval TEXT,
    data_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_oi_exchange_symbol ON oi_exchange_snapshots(symbol, timestamp_utc);

-- Liquidation Heatmaps (Coinglass)
CREATE TABLE IF NOT EXISTS liquidation_heatmap_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_utc TEXT NOT NULL,
    symbol TEXT NOT NULL,
    model TEXT NOT NULL,
    data_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_liq_heatmap_symbol ON liquidation_heatmap_snapshots(symbol, timestamp_utc);

-- BTC Macro On-Chain (Coinglass)
CREATE TABLE IF NOT EXISTS btc_onchain_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_utc TEXT NOT NULL,
    indicator TEXT NOT NULL,
    data_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_btc_onchain_indicator ON btc_onchain_snapshots(indicator, timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_btc_onchain_time ON btc_onchain_snapshots(timestamp_utc);

-- Nansen Flow Snapshots (cron-fed from cache)
CREATE TABLE IF NOT EXISTS nansen_flow_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_utc TEXT NOT NULL,
    token TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    holder_segment TEXT,
    lookback_period TEXT,
    data_json TEXT NOT NULL,
    source_query_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_nansen_flow_token ON nansen_flow_snapshots(token, timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_nansen_flow_tool ON nansen_flow_snapshots(tool_name);

-- Nansen Holder Snapshots
CREATE TABLE IF NOT EXISTS nansen_holder_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_utc TEXT NOT NULL,
    token TEXT NOT NULL,
    chain TEXT,
    label_type TEXT,
    mode TEXT,
    data_json TEXT NOT NULL,
    source_query_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_nansen_holder_token ON nansen_holder_snapshots(token, timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_nansen_holder_label ON nansen_holder_snapshots(label_type);

-- Nansen Perp Trade Snapshots
CREATE TABLE IF NOT EXISTS nansen_perp_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_utc TEXT NOT NULL,
    data_json TEXT NOT NULL,
    source_query_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_nansen_perp_time ON nansen_perp_snapshots(timestamp_utc);

-- Nansen Quant Score Snapshots
CREATE TABLE IF NOT EXISTS nansen_quant_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_utc TEXT NOT NULL,
    token TEXT NOT NULL,
    data_json TEXT NOT NULL,
    source_query_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_nansen_quant_token ON nansen_quant_snapshots(token, timestamp_utc);

-- Snapshot Metadata (tracks each cron run)
CREATE TABLE IF NOT EXISTS snapshot_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    run_type TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    endpoints_succeeded INTEGER DEFAULT 0,
    endpoints_failed INTEGER DEFAULT 0,
    total_rows_inserted INTEGER DEFAULT 0,
    error_log TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_snapshot_meta_type ON snapshot_metadata(run_type, started_at);
CREATE INDEX IF NOT EXISTS idx_snapshot_meta_run ON snapshot_metadata(run_id);

-- Structured output from /analyze command
CREATE TABLE IF NOT EXISTS analyze_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT UNIQUE,
    timestamp_utc TEXT NOT NULL,
    token TEXT NOT NULL,
    price_usd REAL,

    -- Verdict
    verdict TEXT,
    conviction TEXT,
    direction TEXT,

    -- Accumulation Score (0-5)
    accumulation_score REAL,
    exchange_flows_signal TEXT,
    fresh_wallets_signal TEXT,
    smart_money_signal TEXT,
    top_pnl_signal TEXT,
    whale_signal TEXT,

    -- Signal Hierarchy Pillar Verdicts
    onchain_verdict TEXT,
    perps_verdict TEXT,
    derivatives_verdict TEXT,
    ta_verdict TEXT,

    -- Key Levels (JSON arrays)
    support_levels_json TEXT,
    resistance_levels_json TEXT,

    -- TA Summary
    ta_weekly_rsi REAL,
    ta_daily_rsi REAL,
    ta_4h_rsi REAL,
    ta_weekly_adx REAL,
    ta_daily_adx REAL,
    ta_trend_direction TEXT,

    -- Derivatives Summary
    funding_rate REAL,
    oi_usd REAL,
    oi_change_24h_pct REAL,
    ls_global_ratio REAL,
    ls_crowding TEXT,

    -- Invalidation
    invalidation_criteria TEXT,

    -- Cost tracking
    nansen_credits_used INTEGER,

    -- Full report
    full_markdown TEXT,

    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_analyze_token ON analyze_snapshots(token, timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_analyze_verdict ON analyze_snapshots(verdict, token);

-- Structured output from /accum-distro command
CREATE TABLE IF NOT EXISTS accum_distro_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT UNIQUE,
    timestamp_utc TEXT NOT NULL,
    token TEXT NOT NULL,
    chain TEXT,
    token_address TEXT,
    price_usd REAL,

    -- Layer Verdicts
    layer1_verdict TEXT,
    layer2_verdict TEXT,
    layer3_verdict TEXT,

    -- Layer 1: CEX Flows
    cex_net_flow_usd REAL,
    cex_inflow_usd REAL,
    cex_outflow_usd REAL,
    cex_flow_vs_avg REAL,

    -- Layer 2: Smart Money
    sm_holders_count INTEGER,
    sm_balance_usd REAL,
    sm_balance_change_24h_pct REAL,
    sm_net_buy_volume_usd REAL,
    sm_buyer_count INTEGER,
    sm_seller_count INTEGER,

    -- Layer 3: Fresh Wallets
    fresh_wallet_count INTEGER,
    fresh_wallet_max_score INTEGER,
    fresh_wallet_total_usd REAL,

    -- Final Verdict
    final_verdict TEXT,
    conviction TEXT,

    -- Cost tracking
    nansen_credits_used INTEGER,

    -- Full report
    full_markdown TEXT,

    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_accum_distro_token ON accum_distro_snapshots(token, timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_accum_distro_verdict ON accum_distro_snapshots(final_verdict, token);
"""


def init_db() -> None:
    """Initialize database with schema."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    # Execute statements individually to handle legacy table schema mismatches
    # (e.g., cex_snapshots was created with different columns than SCHEMA defines)
    combined_schema = SCHEMA + "\n" + SNAPSHOT_SCHEMA
    for statement in combined_schema.split(';'):
        statement = statement.strip()
        if statement:
            try:
                conn.execute(statement)
            except sqlite3.OperationalError as e:
                # Only suppress errors from legacy table schema mismatches
                # (e.g., CREATE INDEX on columns that don't exist in old tables)
                if 'already exists' not in str(e) and 'no such column' not in str(e):
                    raise
    conn.commit()
    conn.close()


def migrate_db() -> None:
    """Run database migrations — create any new tables if not present."""
    init_db()


def get_connection() -> sqlite3.Connection:
    """Get database connection, initializing if needed."""
    if not DB_PATH.exists():
        init_db()
    else:
        # Run migrations for existing databases
        migrate_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def sync_to_cowork() -> bool:
    """Copy local DB to Cowork directory so it has fresh data."""
    if not DB_PATH.exists():
        print(f"[sync] Source DB not found: {DB_PATH}")
        return False
    if not COWORK_DB_PATH.parent.exists():
        print(f"[sync] Cowork directory not found: {COWORK_DB_PATH.parent}")
        return False
    try:
        shutil.copy2(DB_PATH, COWORK_DB_PATH)
        size_mb = COWORK_DB_PATH.stat().st_size / (1024 * 1024)
        print(f"[sync] Copied {size_mb:.1f}MB → {COWORK_DB_PATH}")
        return True
    except Exception as e:
        print(f"[sync] Failed: {e}")
        return False


# ============================================================================
# MCP QUERY LOGGING
# ============================================================================

def log_mcp_query(
    tool_name: str,
    tool_source: str,
    parameters: Dict[str, Any],
    context_type: Optional[str] = None,
    context_token: Optional[str] = None
) -> str:
    """
    Log an MCP tool call.

    Returns:
        query_id for linking to response
    """
    query_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    conn.execute(
        """INSERT INTO mcp_queries
           (query_id, timestamp_utc, tool_name, tool_source, parameters_json, context_type, context_token)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (query_id, timestamp, tool_name, tool_source, json.dumps(parameters), context_type, context_token)
    )
    conn.commit()
    conn.close()

    return query_id


def log_mcp_response(query_id: str, response: Any) -> None:
    """Store the raw response for a query."""
    response_json = json.dumps(response) if not isinstance(response, str) else response
    timestamp = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    conn.execute(
        """INSERT INTO mcp_responses (query_id, response_json, response_size_bytes, created_at)
           VALUES (?, ?, ?, ?)""",
        (query_id, response_json, len(response_json), timestamp)
    )
    conn.commit()
    conn.close()


def mark_query_failed(query_id: str) -> None:
    """Mark a query as failed."""
    conn = get_connection()
    conn.execute("UPDATE mcp_queries SET success = 0 WHERE query_id = ?", (query_id,))
    conn.commit()
    conn.close()


# ============================================================================
# LLM INTERPRETATION LOGGING
# ============================================================================

def log_interpretation(
    interpretation_type: str,
    token: str,
    signal: str,
    summary: str,
    query_ids: Optional[List[str]] = None,
    confidence: str = "medium",
    model_version: str = "claude-opus-4-5",
    tokens_used: Optional[int] = None
) -> str:
    """
    Log an LLM interpretation for future evaluation.

    Returns:
        interpretation_id
    """
    interpretation_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    conn.execute(
        """INSERT INTO llm_interpretations
           (interpretation_id, query_ids, timestamp_utc, interpretation_type, token,
            signal, confidence, summary, model_version, tokens_used)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (interpretation_id, json.dumps(query_ids or []), timestamp, interpretation_type,
         token, signal, confidence, summary, model_version, tokens_used)
    )
    conn.commit()
    conn.close()

    return interpretation_id


# ============================================================================
# TRADE CARD LOGGING
# ============================================================================

def log_trade_card(
    token: str,
    verdict: str,
    full_markdown: str,
    total_tokens_used: Optional[int] = None
) -> str:
    """
    Log a complete trade card.

    Returns:
        card_id
    """
    card_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    conn.execute(
        """INSERT INTO trade_cards
           (card_id, timestamp_utc, token, verdict, full_markdown, total_tokens_used)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (card_id, timestamp, token, verdict, full_markdown, total_tokens_used)
    )
    conn.commit()
    conn.close()

    return card_id


# ============================================================================
# CEX SNAPSHOT LOGGING
# ============================================================================

def log_cex_snapshot(
    asset: str,
    exchange_inflows: float,
    exchange_outflows: float,
    net_flow: float,
    signal: str,
    raw_data: Optional[Dict] = None
) -> str:
    """Log a CEX health snapshot."""
    snapshot_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    conn.execute(
        """INSERT INTO cex_snapshots
           (snapshot_id, timestamp_utc, asset, exchange_inflows, exchange_outflows,
            net_flow, signal, raw_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (snapshot_id, timestamp, asset, exchange_inflows, exchange_outflows,
         net_flow, signal, json.dumps(raw_data) if raw_data else None)
    )
    conn.commit()
    conn.close()

    return snapshot_id


# ============================================================================
# MENTOR CONSULTATION LOGGING
# ============================================================================

def log_mentor_consultation(
    token: str,
    question_type: str,
    initial_verdict: str,
    initial_confidence: float,
    question_asked: str,
    context_provided: str,
    mentor_agrees: bool,
    confidence_adjustment: float,
    mentor_reasoning: str,
    suggested_action: str,
    tokens_used: int,
    model: str
) -> str:
    """
    Log a mentor consultation.

    Returns:
        consultation_id
    """
    consultation_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    cost = 0.0  # v2: No API cost — Claude Code uses subscription

    conn = get_connection()
    conn.execute(
        """INSERT INTO mentor_consultations
           (consultation_id, timestamp_utc, token, question_type, initial_verdict,
            initial_confidence, question_asked, context_provided, mentor_agrees,
            confidence_adjustment, mentor_reasoning, suggested_action, tokens_used,
            model, api_cost_usd)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (consultation_id, timestamp, token.upper(), question_type, initial_verdict,
         initial_confidence, question_asked, context_provided, 1 if mentor_agrees else 0,
         confidence_adjustment, mentor_reasoning, suggested_action, tokens_used,
         model, cost)
    )
    conn.commit()
    conn.close()

    return consultation_id


def get_mentor_consultations(token: Optional[str] = None, limit: int = 20) -> List[Dict]:
    """Get recent mentor consultations."""
    conn = get_connection()

    if token:
        cursor = conn.execute(
            """SELECT * FROM mentor_consultations
               WHERE token = ?
               ORDER BY timestamp_utc DESC LIMIT ?""",
            (token.upper(), limit)
        )
    else:
        cursor = conn.execute(
            "SELECT * FROM mentor_consultations ORDER BY timestamp_utc DESC LIMIT ?",
            (limit,)
        )

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_mentor_stats() -> Dict:
    """Get mentor consultation statistics."""
    conn = get_connection()
    stats = {}

    # Total consultations
    cursor = conn.execute("SELECT COUNT(*) FROM mentor_consultations")
    stats['total_consultations'] = cursor.fetchone()[0]

    # Total cost
    cursor = conn.execute("SELECT SUM(api_cost_usd) FROM mentor_consultations")
    stats['total_cost_usd'] = cursor.fetchone()[0] or 0

    # Total tokens
    cursor = conn.execute("SELECT SUM(tokens_used) FROM mentor_consultations")
    stats['total_tokens'] = cursor.fetchone()[0] or 0

    # Agreement rate
    cursor = conn.execute("SELECT AVG(mentor_agrees) FROM mentor_consultations")
    stats['agreement_rate'] = cursor.fetchone()[0] or 0

    # By question type
    cursor = conn.execute(
        """SELECT question_type, COUNT(*) as count
           FROM mentor_consultations
           GROUP BY question_type"""
    )
    stats['by_question_type'] = {row[0]: row[1] for row in cursor.fetchall()}

    # By suggested action
    cursor = conn.execute(
        """SELECT suggested_action, COUNT(*) as count
           FROM mentor_consultations
           GROUP BY suggested_action"""
    )
    stats['by_suggested_action'] = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()
    return stats

# ============================================================================
# FLOW SNAPSHOT LOGGING
# ============================================================================

def log_flow_snapshot(
    token: str,
    chain: str = None,
    token_address: str = None,
    price_usd: float = None,
    exchange_net_flow: float = None,
    exchange_flow_ratio: float = None,
    exchange_wallets: int = None,
    exchange_signal: str = None,
    fresh_wallet_net_flow: float = None,
    fresh_wallet_ratio: float = None,
    fresh_wallet_count: int = None,
    fresh_wallet_signal: str = None,
    smart_money_net_flow: float = None,
    smart_money_ratio: float = None,
    smart_money_wallets: int = None,
    smart_money_signal: str = None,
    top_pnl_net_flow: float = None,
    top_pnl_ratio: float = None,
    top_pnl_wallets: int = None,
    top_pnl_signal: str = None,
    whale_net_flow: float = None,
    whale_ratio: float = None,
    whale_wallets: int = None,
    whale_signal: str = None,
    lookback_period: str = "1d",
    raw_data: Dict = None
) -> str:
    """
    Log a token flow snapshot.

    Returns:
        snapshot_id
    """
    snapshot_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    # Calculate accumulation score (count bullish signals)
    signals = [exchange_signal, fresh_wallet_signal, smart_money_signal, top_pnl_signal, whale_signal]
    bullish_count = sum(1 for s in signals if s and s.lower() in ['bullish', 'accumulating', 'buying'])
    bearish_count = sum(1 for s in signals if s and s.lower() in ['bearish', 'distributing', 'selling'])

    # Determine overall signal
    if bullish_count >= 4:
        overall_signal = "ACCUMULATING"
    elif bearish_count >= 4:
        overall_signal = "DISTRIBUTING"
    elif bullish_count == 0 and bearish_count == 0:
        overall_signal = "QUIET"
    else:
        overall_signal = "MIXED"

    conn = get_connection()
    conn.execute(
        """INSERT INTO flow_snapshots
           (snapshot_id, timestamp_utc, token, chain, token_address, price_usd,
            exchange_net_flow, exchange_flow_ratio, exchange_wallets, exchange_signal,
            fresh_wallet_net_flow, fresh_wallet_ratio, fresh_wallet_count, fresh_wallet_signal,
            smart_money_net_flow, smart_money_ratio, smart_money_wallets, smart_money_signal,
            top_pnl_net_flow, top_pnl_ratio, top_pnl_wallets, top_pnl_signal,
            whale_net_flow, whale_ratio, whale_wallets, whale_signal,
            accumulation_score, overall_signal, raw_json, lookback_period)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (snapshot_id, timestamp, token.upper(), chain, token_address, price_usd,
         exchange_net_flow, exchange_flow_ratio, exchange_wallets, exchange_signal,
         fresh_wallet_net_flow, fresh_wallet_ratio, fresh_wallet_count, fresh_wallet_signal,
         smart_money_net_flow, smart_money_ratio, smart_money_wallets, smart_money_signal,
         top_pnl_net_flow, top_pnl_ratio, top_pnl_wallets, top_pnl_signal,
         whale_net_flow, whale_ratio, whale_wallets, whale_signal,
         bullish_count, overall_signal, json.dumps(raw_data) if raw_data else None, lookback_period)
    )
    conn.commit()
    conn.close()

    return snapshot_id


# ============================================================================
# ON-CHAIN RESEARCH DATA STORAGE
# ============================================================================

def log_exchange_balance_daily(
    token: str,
    daily_data: List[Dict],
    chain: str = None,
    token_address: str = None
) -> int:
    """
    Store daily exchange balance data for trend analysis.

    Args:
        token: Token symbol
        daily_data: List of dicts with keys: date, balance, balance_usd,
                    inflows, inflows_usd, outflows, outflows_usd,
                    net_flow, net_flow_usd, price
        chain: Blockchain
        token_address: Contract address

    Returns:
        Number of rows upserted
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    count = 0

    for day in daily_data:
        conn.execute(
            """INSERT OR REPLACE INTO exchange_balance_daily
               (token, date, chain, token_address, balance, balance_usd,
                inflows, inflows_usd, outflows, outflows_usd,
                net_flow, net_flow_usd, price, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (token.upper(), day.get('date'), chain, token_address,
             day.get('balance'), day.get('balance_usd'),
             day.get('inflows'), day.get('inflows_usd'),
             day.get('outflows'), day.get('outflows_usd'),
             day.get('net_flow'), day.get('net_flow_usd'),
             day.get('price'), timestamp)
        )
        count += 1

    conn.commit()
    conn.close()
    return count


def log_entity_snapshot(
    token: str,
    snapshot_date: str,
    entities: List[Dict],
    chain: str = None,
    token_address: str = None
) -> int:
    """
    Store entity position snapshots for diff tracking.

    Args:
        token: Token symbol
        snapshot_date: YYYY-MM-DD
        entities: List of dicts with keys: entity_name, entity_address,
                  entity_type, entity_label, balance, balance_usd,
                  change_1d, change_7d, change_30d, ownership_pct,
                  avg_entry_price, pnl_usd
        chain: Blockchain
        token_address: Contract address

    Returns:
        Number of rows upserted
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    count = 0

    for entity in entities:
        snapshot_id = str(uuid.uuid4())[:8]
        conn.execute(
            """INSERT OR REPLACE INTO entity_snapshots
               (snapshot_id, token, snapshot_date, chain, token_address,
                entity_name, entity_address, entity_type, entity_label,
                balance, balance_usd, change_1d, change_7d, change_30d,
                ownership_pct, avg_entry_price, pnl_usd, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (snapshot_id, token.upper(), snapshot_date, chain, token_address,
             entity.get('entity_name'), entity.get('entity_address'),
             entity.get('entity_type'), entity.get('entity_label'),
             entity.get('balance'), entity.get('balance_usd'),
             entity.get('change_1d'), entity.get('change_7d'),
             entity.get('change_30d'), entity.get('ownership_pct'),
             entity.get('avg_entry_price'), entity.get('pnl_usd'),
             timestamp)
        )
        count += 1

    conn.commit()
    conn.close()
    return count


def log_hunt_result(
    hunt_date: str,
    candidates: List[Dict],
    hunt_id: str = None
) -> str:
    """
    Store scored hunt candidates with outcome tracking.

    Args:
        hunt_date: YYYY-MM-DD
        candidates: List of dicts with scored candidate data
        hunt_id: Optional hunt ID (auto-generated if not provided)

    Returns:
        hunt_id for the batch
    """
    if hunt_id is None:
        hunt_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now(timezone.utc).isoformat()
    conn = get_connection()

    for candidate in candidates:
        result_id = str(uuid.uuid4())[:8]
        conn.execute(
            """INSERT INTO hunt_results
               (result_id, hunt_id, hunt_date, token, chain, token_address,
                price_at_hunt, alpha_score, entity_convergence_score,
                exchange_flow_score, volume_dry_up_score, perps_score,
                exchange_net_flow_usd, exchange_flow_ratio,
                num_entities_buying, num_entities_selling,
                top_entity, top_entity_change,
                exbal_outflow_days, exbal_balance_change_pct,
                verdict, verdict_reason, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (result_id, hunt_id, hunt_date,
             candidate.get('token', '').upper(),
             candidate.get('chain'), candidate.get('token_address'),
             candidate.get('price_at_hunt'), candidate.get('alpha_score'),
             candidate.get('entity_convergence_score'),
             candidate.get('exchange_flow_score'),
             candidate.get('volume_dry_up_score'),
             candidate.get('perps_score'),
             candidate.get('exchange_net_flow_usd'),
             candidate.get('exchange_flow_ratio'),
             candidate.get('num_entities_buying'),
             candidate.get('num_entities_selling'),
             candidate.get('top_entity'),
             candidate.get('top_entity_change'),
             candidate.get('exbal_outflow_days'),
             candidate.get('exbal_balance_change_pct'),
             (candidate.get('verdict') or '').upper() or None,
             candidate.get('verdict_reason'),
             timestamp)
        )

    conn.commit()
    conn.close()
    return hunt_id


# ============================================================================
# ON-CHAIN RESEARCH DATA QUERIES
# ============================================================================

def get_exchange_balance_trend(
    token: str,
    days: int = 14
) -> Dict:
    """
    Get exchange balance trend with summary stats.

    Returns:
        Dict with 'days' (list of daily data) and 'summary' (computed stats)
    """
    conn = get_connection()
    cursor = conn.execute(
        """SELECT * FROM exchange_balance_daily
           WHERE token = ?
           ORDER BY date DESC
           LIMIT ?""",
        (token.upper(), days)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not rows:
        return {'days': [], 'summary': {}}

    # Compute summary stats
    outflow_days = sum(1 for r in rows if r.get('net_flow') and r['net_flow'] < 0)
    inflow_days = sum(1 for r in rows if r.get('net_flow') and r['net_flow'] > 0)

    balances = [r['balance'] for r in rows if r.get('balance')]
    if len(balances) >= 2:
        # rows are DESC, so first = newest, last = oldest
        newest_balance = balances[0]
        oldest_balance = balances[-1]
        balance_change_pct = ((newest_balance - oldest_balance) / oldest_balance * 100) if oldest_balance else 0
    else:
        balance_change_pct = 0

    total_inflows = sum(r.get('inflows_usd') or 0 for r in rows)
    total_outflows = sum(r.get('outflows_usd') or 0 for r in rows)

    summary = {
        'token': token.upper(),
        'data_days': len(rows),
        'outflow_days': outflow_days,
        'inflow_days': inflow_days,
        'balance_change_pct': round(balance_change_pct, 2),
        'total_inflows_usd': total_inflows,
        'total_outflows_usd': total_outflows,
        'net_flow_usd': total_inflows - total_outflows,
        'newest_date': rows[0]['date'] if rows else None,
        'oldest_date': rows[-1]['date'] if rows else None,
    }

    return {'days': rows, 'summary': summary}


def get_entity_diff(
    token: str,
    current_entities: List[Dict] = None,
    days_back: int = 7
) -> Dict:
    """
    Compare current entity positions vs stored snapshot.

    Args:
        token: Token symbol
        current_entities: List of current entity dicts (with entity_address, balance).
                         If None, compares two most recent stored snapshots.
        days_back: How far back to look for comparison snapshot

    Returns:
        Dict with 'new', 'removed', 'changed', 'unchanged' entity lists
    """
    conn = get_connection()

    # Get stored snapshot from days_back ago (or the oldest available)
    cursor = conn.execute(
        """SELECT * FROM entity_snapshots
           WHERE token = ?
           AND snapshot_date <= date('now', ?)
           ORDER BY snapshot_date DESC""",
        (token.upper(), f'-{days_back} days')
    )
    stored_rows = [dict(row) for row in cursor.fetchall()]

    # If no current_entities provided, use the latest stored snapshot as "current"
    if current_entities is None:
        cursor = conn.execute(
            """SELECT * FROM entity_snapshots
               WHERE token = ?
               ORDER BY snapshot_date DESC""",
            (token.upper(),)
        )
        latest_rows = [dict(row) for row in cursor.fetchall()]
        conn.close()

        if not latest_rows:
            return {'new': [], 'removed': [], 'changed': [], 'unchanged': [],
                    'latest_date': None, 'comparison_date': None}

        latest_date = latest_rows[0]['snapshot_date']
        current_by_addr = {}
        for r in latest_rows:
            if r['snapshot_date'] == latest_date:
                current_by_addr[r['entity_address']] = r
    else:
        conn.close()
        latest_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        current_by_addr = {e['entity_address']: e for e in current_entities if e.get('entity_address')}

    # Build stored lookup (most recent per address from the older snapshot)
    stored_by_addr = {}
    comparison_date = None
    for r in stored_rows:
        addr = r['entity_address']
        if addr not in stored_by_addr:
            stored_by_addr[addr] = r
            if comparison_date is None:
                comparison_date = r['snapshot_date']

    # Compute diffs
    new_entities = []
    removed_entities = []
    changed_entities = []
    unchanged_entities = []

    for addr, curr in current_by_addr.items():
        if addr not in stored_by_addr:
            new_entities.append(curr)
        else:
            stored = stored_by_addr[addr]
            curr_bal = curr.get('balance') or 0
            stored_bal = stored.get('balance') or 0
            if stored_bal != 0:
                change_pct = ((curr_bal - stored_bal) / abs(stored_bal)) * 100
            else:
                change_pct = 100 if curr_bal > 0 else 0

            if abs(change_pct) > 1:  # >1% change threshold
                changed_entities.append({
                    'entity_name': curr.get('entity_name') or stored.get('entity_name'),
                    'entity_address': addr,
                    'old_balance': stored_bal,
                    'new_balance': curr_bal,
                    'change': curr_bal - stored_bal,
                    'change_pct': round(change_pct, 2),
                    'entity_type': curr.get('entity_type') or stored.get('entity_type'),
                })
            else:
                unchanged_entities.append(curr)

    for addr, stored in stored_by_addr.items():
        if addr not in current_by_addr:
            removed_entities.append(stored)

    return {
        'new': new_entities,
        'removed': removed_entities,
        'changed': sorted(changed_entities, key=lambda x: abs(x.get('change_pct', 0)), reverse=True),
        'unchanged': unchanged_entities,
        'latest_date': latest_date,
        'comparison_date': comparison_date,
    }


def get_entity_history(
    token: str,
    entity_address: str = None,
    days: int = 30,
    limit: int = 100
) -> List[Dict]:
    """Get entity snapshot history for a token."""
    conn = get_connection()

    conditions = ["token = ?", "snapshot_date >= date('now', ?)"]
    params: list = [token.upper(), f'-{days} days']

    if entity_address:
        conditions.append("entity_address = ?")
        params.append(entity_address)

    params.append(limit)
    where = " AND ".join(conditions)

    cursor = conn.execute(
        f"""SELECT * FROM entity_snapshots
            WHERE {where}
            ORDER BY snapshot_date DESC, balance DESC
            LIMIT ?""",
        params
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_hunt_history(
    token: str = None,
    days: int = 90,
    verdict: str = None,
    limit: int = 20
) -> List[Dict]:
    """Get past hunt results with optional filters."""
    conn = get_connection()

    conditions = ["hunt_date >= date('now', ?)"]
    params: list = [f'-{int(days)} days']

    if token:
        conditions.append("token = ?")
        params.append(token.upper())
    if verdict:
        conditions.append("verdict = ?")
        params.append(verdict.upper())

    params.append(limit)
    where = " AND ".join(conditions)

    cursor = conn.execute(
        f"""SELECT * FROM hunt_results
            WHERE {where}
            ORDER BY hunt_date DESC, alpha_score DESC
            LIMIT ?""",
        params
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def update_hunt_outcome(
    result_id: str,
    price_7d_later: float = None,
    price_14d_later: float = None,
    price_30d_later: float = None
) -> None:
    """Fill in outcome prices for a hunt result."""
    conn = get_connection()

    # Get the original hunt price
    cursor = conn.execute(
        "SELECT price_at_hunt FROM hunt_results WHERE result_id = ?",
        (result_id,)
    )
    row = cursor.fetchone()
    if not row or not row['price_at_hunt']:
        conn.close()
        return

    price_at = row['price_at_hunt']

    updates = []
    params: list = []

    if price_7d_later is not None:
        updates.extend(["price_7d_later = ?", "pct_change_7d = ?"])
        params.extend([price_7d_later, round((price_7d_later - price_at) / price_at * 100, 2)])
    if price_14d_later is not None:
        updates.extend(["price_14d_later = ?", "pct_change_14d = ?"])
        params.extend([price_14d_later, round((price_14d_later - price_at) / price_at * 100, 2)])
    if price_30d_later is not None:
        updates.extend(["price_30d_later = ?", "pct_change_30d = ?"])
        params.extend([price_30d_later, round((price_30d_later - price_at) / price_at * 100, 2)])

    if updates:
        params.append(result_id)
        conn.execute(
            f"UPDATE hunt_results SET {', '.join(updates)} WHERE result_id = ?",
            params
        )
        conn.commit()
    conn.close()


def get_flow_history(
    token: str,
    days: int = 30,
    limit: int = 100
) -> List[Dict]:
    """Get flow history for a token."""
    conn = get_connection()
    cursor = conn.execute(
        """SELECT * FROM flow_snapshots
           WHERE token = ?
           AND timestamp_utc >= datetime('now', ?)
           ORDER BY timestamp_utc DESC
           LIMIT ?""",
        (token.upper(), f'-{days} days', limit)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_latest_flow(token: str) -> Optional[Dict]:
    """Get most recent flow snapshot for a token."""
    conn = get_connection()
    cursor = conn.execute(
        """SELECT * FROM flow_snapshots
           WHERE token = ?
           ORDER BY timestamp_utc DESC
           LIMIT 1""",
        (token.upper(),)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_flow_comparison(token: str, days_back: int = 7) -> Dict:
    """
    Compare current flow to historical average.

    Returns dict with current values and % change from average.
    """
    conn = get_connection()

    # Get latest snapshot
    cursor = conn.execute(
        """SELECT * FROM flow_snapshots
           WHERE token = ?
           ORDER BY timestamp_utc DESC LIMIT 1""",
        (token.upper(),)
    )
    latest = cursor.fetchone()
    if not latest:
        conn.close()
        return {}

    latest = dict(latest)

    # Get historical averages
    cursor = conn.execute(
        """SELECT
           AVG(exchange_net_flow) as avg_exchange,
           AVG(fresh_wallet_net_flow) as avg_fresh,
           AVG(smart_money_net_flow) as avg_smart,
           AVG(top_pnl_net_flow) as avg_pnl,
           AVG(whale_net_flow) as avg_whale,
           COUNT(*) as snapshot_count
           FROM flow_snapshots
           WHERE token = ?
           AND timestamp_utc >= datetime('now', ?)
           AND timestamp_utc < datetime('now', '-1 day')""",
        (token.upper(), f'-{days_back} days')
    )
    avgs = dict(cursor.fetchone())
    conn.close()

    comparison = {
        'token': token.upper(),
        'latest_timestamp': latest['timestamp_utc'],
        'snapshot_count': avgs['snapshot_count'],
        'current': {
            'exchange': latest['exchange_net_flow'],
            'fresh_wallet': latest['fresh_wallet_net_flow'],
            'smart_money': latest['smart_money_net_flow'],
            'top_pnl': latest['top_pnl_net_flow'],
            'whale': latest['whale_net_flow'],
            'overall_signal': latest['overall_signal'],
            'accumulation_score': latest['accumulation_score']
        },
        'historical_avg': {
            'exchange': avgs['avg_exchange'],
            'fresh_wallet': avgs['avg_fresh'],
            'smart_money': avgs['avg_smart'],
            'top_pnl': avgs['avg_pnl'],
            'whale': avgs['avg_whale']
        }
    }

    return comparison


def get_all_latest_flows(tokens: List[str] = None) -> List[Dict]:
    """Get latest flow for multiple tokens."""
    conn = get_connection()

    if tokens:
        placeholders = ','.join('?' * len(tokens))
        cursor = conn.execute(
            f"""SELECT f1.* FROM flow_snapshots f1
               INNER JOIN (
                   SELECT token, MAX(timestamp_utc) as max_ts
                   FROM flow_snapshots
                   WHERE token IN ({placeholders})
                   GROUP BY token
               ) f2 ON f1.token = f2.token AND f1.timestamp_utc = f2.max_ts
               ORDER BY f1.token""",
            [t.upper() for t in tokens]
        )
    else:
        cursor = conn.execute(
            """SELECT f1.* FROM flow_snapshots f1
               INNER JOIN (
                   SELECT token, MAX(timestamp_utc) as max_ts
                   FROM flow_snapshots
                   GROUP BY token
               ) f2 ON f1.token = f2.token AND f1.timestamp_utc = f2.max_ts
               ORDER BY f1.token"""
        )

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_flow_stats() -> Dict:
    """Get flow logging statistics."""
    conn = get_connection()
    stats = {}

    # Total snapshots
    cursor = conn.execute("SELECT COUNT(*) FROM flow_snapshots")
    stats['total_snapshots'] = cursor.fetchone()[0]

    # Unique tokens tracked
    cursor = conn.execute("SELECT COUNT(DISTINCT token) FROM flow_snapshots")
    stats['tokens_tracked'] = cursor.fetchone()[0]

    # Snapshots by token
    cursor = conn.execute(
        """SELECT token, COUNT(*) as count,
           MIN(timestamp_utc) as first_snapshot,
           MAX(timestamp_utc) as last_snapshot
           FROM flow_snapshots
           GROUP BY token
           ORDER BY count DESC"""
    )
    stats['by_token'] = {row[0]: {'count': row[1], 'first': row[2], 'last': row[3]}
                        for row in cursor.fetchall()}

    # Signal distribution
    cursor = conn.execute(
        """SELECT overall_signal, COUNT(*) as count
           FROM flow_snapshots
           GROUP BY overall_signal"""
    )
    stats['signal_distribution'] = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()
    return stats


# ============================================================================
# SIGNAL VALIDATION LOGGING
# ============================================================================

def log_signal_validation(
    external_signal_id: int,
    symbol: str,
    direction: str,
    provider: str = "MarketInsights",
    signal_analysis: str = None,
    accumulation_score: int = None,
    ta_verdict: str = None,
    onchain_verdict: str = None,
    signal_aligns: bool = None,
    mentor_consulted: bool = False,
    mentor_verdict: str = None,
    mentor_confidence_adj: float = None,
    titan_recommendation: str = None,
    recommendation_reason: str = None,
    chart_analyzed: bool = False,
    chart_notes: str = None,
    chart_path: str = None,
    suggested_entry: float = None,
    suggested_stop: float = None,
    suggested_target: float = None
) -> str:
    """
    Log a signal validation result.

    Args:
        external_signal_id: ID from external signals.db
        symbol: Token symbol
        direction: LONG or SHORT
        provider: Signal provider (default: MarketInsights)
        signal_analysis: MarketInsights commentary
        accumulation_score: Titan's 0-5 score
        ta_verdict: Technical analysis verdict
        onchain_verdict: On-chain verdict
        signal_aligns: Whether signal matches Titan analysis
        mentor_consulted: Whether mentor was consulted
        mentor_verdict: Mentor's assessment
        mentor_confidence_adj: Confidence adjustment from mentor
        titan_recommendation: VALID/INVALID/NEEDS_CONFIRMATION
        recommendation_reason: Reason for recommendation
        chart_analyzed: Whether chart was reviewed
        chart_notes: Notes from chart analysis
        chart_path: Path to chart image
        suggested_entry: Suggested entry price
        suggested_stop: Suggested stop loss
        suggested_target: Suggested target price

    Returns:
        validation_id for tracking
    """
    validation_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    conn.execute(
        """INSERT INTO signal_validations
           (validation_id, timestamp_utc, external_signal_id, symbol, direction,
            provider, signal_analysis, accumulation_score, ta_verdict, onchain_verdict,
            signal_aligns, mentor_consulted, mentor_verdict, mentor_confidence_adj,
            titan_recommendation, recommendation_reason, chart_analyzed, chart_notes,
            chart_path, suggested_entry, suggested_stop, suggested_target)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (validation_id, timestamp, external_signal_id, symbol.upper(), direction.upper(),
         provider, signal_analysis, accumulation_score, ta_verdict, onchain_verdict,
         1 if signal_aligns else (0 if signal_aligns is not None else None),
         1 if mentor_consulted else 0, mentor_verdict, mentor_confidence_adj,
         titan_recommendation, recommendation_reason,
         1 if chart_analyzed else 0, chart_notes, chart_path,
         suggested_entry, suggested_stop, suggested_target)
    )
    conn.commit()
    conn.close()

    return validation_id


def get_validation_by_id(validation_id: str) -> Optional[Dict]:
    """Get a specific validation by ID."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT * FROM signal_validations WHERE validation_id = ?",
        (validation_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_validation_by_signal_id(external_signal_id: int) -> Optional[Dict]:
    """Get validation by external signal ID."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT * FROM signal_validations WHERE external_signal_id = ? ORDER BY timestamp_utc DESC LIMIT 1",
        (external_signal_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_recent_validations(
    symbol: str = None,
    recommendation: str = None,
    limit: int = 20
) -> List[Dict]:
    """
    Get recent signal validations.

    Args:
        symbol: Filter by token symbol
        recommendation: Filter by recommendation (VALID/INVALID/NEEDS_CONFIRMATION)
        limit: Maximum number of results

    Returns:
        List of validation dictionaries
    """
    conn = get_connection()

    conditions = []
    params = []

    if symbol:
        conditions.append("symbol = ?")
        params.append(symbol.upper())

    if recommendation:
        conditions.append("titan_recommendation = ?")
        params.append(recommendation.upper())

    params.append(limit)

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
    else:
        where_clause = ""

    cursor = conn.execute(
        f"""SELECT * FROM signal_validations
            {where_clause}
            ORDER BY timestamp_utc DESC LIMIT ?""",
        params
    )

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_validation_stats(days: int = 30) -> Dict:
    """
    Get signal validation statistics.

    Args:
        days: Lookback period in days

    Returns:
        Dictionary with validation statistics
    """
    conn = get_connection()
    stats = {}

    cutoff = f"-{days} days"

    # Total validations
    cursor = conn.execute(
        """SELECT COUNT(*) FROM signal_validations
           WHERE timestamp_utc >= datetime('now', ?)""",
        (cutoff,)
    )
    stats['total_validations'] = cursor.fetchone()[0]

    # By recommendation
    cursor = conn.execute(
        """SELECT titan_recommendation, COUNT(*) as count
           FROM signal_validations
           WHERE timestamp_utc >= datetime('now', ?)
           GROUP BY titan_recommendation""",
        (cutoff,)
    )
    stats['by_recommendation'] = {row[0] or 'UNKNOWN': row[1] for row in cursor.fetchall()}

    # Signal alignment rate
    cursor = conn.execute(
        """SELECT AVG(signal_aligns) FROM signal_validations
           WHERE timestamp_utc >= datetime('now', ?) AND signal_aligns IS NOT NULL""",
        (cutoff,)
    )
    stats['alignment_rate'] = cursor.fetchone()[0] or 0

    # Mentor consultation rate
    cursor = conn.execute(
        """SELECT AVG(mentor_consulted) FROM signal_validations
           WHERE timestamp_utc >= datetime('now', ?)""",
        (cutoff,)
    )
    stats['mentor_consultation_rate'] = cursor.fetchone()[0] or 0

    # By symbol
    cursor = conn.execute(
        """SELECT symbol, COUNT(*) as count
           FROM signal_validations
           WHERE timestamp_utc >= datetime('now', ?)
           GROUP BY symbol
           ORDER BY count DESC
           LIMIT 10""",
        (cutoff,)
    )
    stats['by_symbol'] = {row[0]: row[1] for row in cursor.fetchall()}

    # Accuracy (if outcomes tracked)
    cursor = conn.execute(
        """SELECT trade_outcome, COUNT(*) as count
           FROM signal_validations
           WHERE timestamp_utc >= datetime('now', ?)
           AND trade_outcome IS NOT NULL
           GROUP BY trade_outcome""",
        (cutoff,)
    )
    stats['by_outcome'] = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()
    return stats


def update_validation_outcome(
    validation_id: str,
    trade_taken: bool,
    trade_outcome: str = None,
    notes: str = None
) -> None:
    """
    Update validation with trade outcome.

    Args:
        validation_id: Validation ID
        trade_taken: Whether user took the trade
        trade_outcome: WIN/LOSS/SKIP
        notes: Additional notes
    """
    conn = get_connection()
    conn.execute(
        """UPDATE signal_validations
           SET trade_taken = ?, trade_outcome = ?, notes = ?
           WHERE validation_id = ?""",
        (1 if trade_taken else 0, trade_outcome, notes, validation_id)
    )
    conn.commit()
    conn.close()


# ============================================================================
# SIGNAL WATCHLIST FUNCTIONS
# ============================================================================

def add_to_watchlist(
    symbol: str,
    source_type: str,
    watch_type: str,
    direction: str = None,
    chain: str = None,
    token_address: str = None,
    external_signal_id: int = None,
    validation_id: str = None,
    original_thesis: str = None,
    entry_conditions: Dict = None,
    invalidation_conditions: Dict = None,
    confirmation_needed: str = None,
    price_at_creation: float = None,
    support_level: float = None,
    resistance_level: float = None,
    stop_level: float = None,
    target_level: float = None,
    original_accumulation_score: int = None,
    original_ta_verdict: str = None,
    original_onchain_verdict: str = None,
    original_perps_bias: str = None,
    check_frequency: str = "session",
    priority: int = 5,
    expires_at: str = None
) -> str:
    """
    Add a token/signal to the watchlist for ongoing monitoring.

    Args:
        symbol: Token symbol (e.g., HYPE, BTC)
        source_type: 'telegram_signal' | 'manual' | 'skill'
        watch_type: 'entry_timing' | 'confirmation' | 'structural' | 'invalidation'
        direction: Expected direction LONG/SHORT
        chain: Blockchain (ethereum, hyperevm, etc.)
        token_address: Contract address
        external_signal_id: Reference to external signals.db
        validation_id: Reference to signal_validations
        original_thesis: Why we're watching this
        entry_conditions: Dict of conditions that would trigger entry
        invalidation_conditions: Dict of conditions that would invalidate
        confirmation_needed: What we're waiting to see
        price_at_creation: Current price when added
        support_level: Key support level
        resistance_level: Key resistance level
        stop_level: Where stop loss would be
        target_level: Target price
        original_accumulation_score: Score at time of adding (0-5)
        original_ta_verdict: TA verdict when added
        original_onchain_verdict: On-chain verdict when added
        original_perps_bias: Perps positioning when added
        check_frequency: 'session' | 'daily' | 'hourly'
        priority: 1-10 (higher = more important)
        expires_at: Optional expiration date

    Returns:
        watch_id
    """
    watch_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    conn.execute(
        """INSERT INTO signal_watchlist (
            watch_id, created_at, updated_at, symbol, chain, token_address,
            source_type, external_signal_id, validation_id, watch_type, direction,
            original_thesis, entry_conditions, invalidation_conditions, confirmation_needed,
            price_at_creation, support_level, resistance_level, stop_level, target_level,
            original_accumulation_score, original_ta_verdict, original_onchain_verdict, original_perps_bias,
            last_checked, last_price, current_accumulation_score, current_ta_verdict,
            current_onchain_verdict, current_perps_bias, status, check_frequency, priority, expires_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            watch_id, timestamp, timestamp, symbol.upper(), chain, token_address,
            source_type, external_signal_id, validation_id, watch_type, direction,
            original_thesis,
            json.dumps(entry_conditions) if entry_conditions else None,
            json.dumps(invalidation_conditions) if invalidation_conditions else None,
            confirmation_needed,
            price_at_creation, support_level, resistance_level, stop_level, target_level,
            original_accumulation_score, original_ta_verdict, original_onchain_verdict, original_perps_bias,
            timestamp, price_at_creation, original_accumulation_score, original_ta_verdict,
            original_onchain_verdict, original_perps_bias, 'active', check_frequency, priority, expires_at
        )
    )
    conn.commit()
    conn.close()
    return watch_id


def get_active_watchlist(
    source_type: str = None,
    watch_type: str = None,
    symbol: str = None,
    check_frequency: str = None
) -> List[Dict]:
    """
    Get all active watchlist items, optionally filtered.

    Args:
        source_type: Filter by source ('telegram_signal', 'manual', 'skill')
        watch_type: Filter by type ('entry_timing', 'confirmation', etc.)
        symbol: Filter by symbol
        check_frequency: Filter by check frequency

    Returns:
        List of watchlist items
    """
    conn = get_connection()
    conditions = ["status = 'active'"]
    params = []

    if source_type:
        conditions.append("source_type = ?")
        params.append(source_type)
    if watch_type:
        conditions.append("watch_type = ?")
        params.append(watch_type)
    if symbol:
        conditions.append("symbol = ?")
        params.append(symbol.upper())
    if check_frequency:
        conditions.append("check_frequency = ?")
        params.append(check_frequency)

    where_clause = " AND ".join(conditions)
    cursor = conn.execute(
        f"""SELECT * FROM signal_watchlist
            WHERE {where_clause}
            ORDER BY priority DESC, created_at DESC""",
        params
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Parse JSON fields
    for row in rows:
        if row.get('entry_conditions'):
            try:
                row['entry_conditions'] = json.loads(row['entry_conditions'])
            except:
                pass
        if row.get('invalidation_conditions'):
            try:
                row['invalidation_conditions'] = json.loads(row['invalidation_conditions'])
            except:
                pass

    return rows


# Alias for backwards compatibility
get_watchlist = get_active_watchlist


def get_watchlist_item(watch_id: str) -> Optional[Dict]:
    """Get a single watchlist item by ID."""
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM signal_watchlist WHERE watch_id = ?", (watch_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        item = dict(row)
        if item.get('entry_conditions'):
            try:
                item['entry_conditions'] = json.loads(item['entry_conditions'])
            except:
                pass
        if item.get('invalidation_conditions'):
            try:
                item['invalidation_conditions'] = json.loads(item['invalidation_conditions'])
            except:
                pass
        return item
    return None


def update_watchlist_check(
    watch_id: str,
    last_price: float = None,
    current_accumulation_score: int = None,
    current_ta_verdict: str = None,
    current_onchain_verdict: str = None,
    current_perps_bias: str = None,
    status_changed: bool = False,
    change_summary: str = None
) -> None:
    """
    Update a watchlist item after a review check.

    Args:
        watch_id: Watchlist item ID
        last_price: Current price
        current_accumulation_score: Current accumulation score (0-5)
        current_ta_verdict: Current TA verdict
        current_onchain_verdict: Current on-chain verdict
        current_perps_bias: Current perps bias
        status_changed: Whether analysis has changed
        change_summary: Description of what changed
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    conn.execute(
        """UPDATE signal_watchlist
           SET updated_at = ?, last_checked = ?, last_price = ?,
               current_accumulation_score = ?, current_ta_verdict = ?,
               current_onchain_verdict = ?, current_perps_bias = ?,
               status_changed = ?, change_summary = ?
           WHERE watch_id = ?""",
        (timestamp, timestamp, last_price, current_accumulation_score,
         current_ta_verdict, current_onchain_verdict, current_perps_bias,
         1 if status_changed else 0, change_summary, watch_id)
    )
    conn.commit()
    conn.close()


def update_watchlist_status(
    watch_id: str,
    status: str,
    status_reason: str = None,
    trade_taken: bool = None,
    trade_setup_id: str = None,
    outcome_notes: str = None
) -> None:
    """
    Update the status of a watchlist item.

    Args:
        watch_id: Watchlist item ID
        status: New status ('active', 'triggered', 'invalidated', 'expired', 'taken', 'removed')
        status_reason: Why status changed
        trade_taken: Whether a trade was taken
        trade_setup_id: Reference to trade_setups if trade taken
        outcome_notes: Notes about the outcome
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    conn = get_connection()

    updates = ["updated_at = ?", "status = ?", "status_reason = ?"]
    params = [timestamp, status, status_reason]

    if status == 'triggered':
        updates.append("triggered_at = ?")
        params.append(timestamp)

    if trade_taken is not None:
        updates.append("trade_taken = ?")
        params.append(1 if trade_taken else 0)

    if trade_setup_id:
        updates.append("trade_setup_id = ?")
        params.append(trade_setup_id)

    if outcome_notes:
        updates.append("outcome_notes = ?")
        params.append(outcome_notes)

    params.append(watch_id)

    conn.execute(
        f"UPDATE signal_watchlist SET {', '.join(updates)} WHERE watch_id = ?",
        params
    )
    conn.commit()
    conn.close()


def get_watchlist_stats() -> Dict:
    """Get statistics about the watchlist."""
    conn = get_connection()
    stats = {}

    # Total by status
    cursor = conn.execute(
        "SELECT status, COUNT(*) FROM signal_watchlist GROUP BY status"
    )
    stats['by_status'] = {row[0]: row[1] for row in cursor.fetchall()}
    stats['active'] = stats['by_status'].get('active', 0)

    # By source type (active only)
    cursor = conn.execute(
        "SELECT source_type, COUNT(*) FROM signal_watchlist WHERE status = 'active' GROUP BY source_type"
    )
    stats['by_source'] = {row[0]: row[1] for row in cursor.fetchall()}

    # By watch type (active only)
    cursor = conn.execute(
        "SELECT watch_type, COUNT(*) FROM signal_watchlist WHERE status = 'active' GROUP BY watch_type"
    )
    stats['by_watch_type'] = {row[0]: row[1] for row in cursor.fetchall()}

    # Items needing review (active, not checked in 24h)
    cursor = conn.execute(
        """SELECT COUNT(*) FROM signal_watchlist
           WHERE status = 'active'
           AND (last_checked IS NULL OR last_checked < datetime('now', '-24 hours'))"""
    )
    stats['needs_review'] = cursor.fetchone()[0]

    # Items with changed analysis
    cursor = conn.execute(
        "SELECT COUNT(*) FROM signal_watchlist WHERE status = 'active' AND status_changed = 1"
    )
    stats['analysis_changed'] = cursor.fetchone()[0]

    # Expired items (still marked active but past expires_at)
    cursor = conn.execute(
        """SELECT COUNT(*) FROM signal_watchlist
           WHERE status = 'active'
           AND expires_at IS NOT NULL
           AND expires_at < datetime('now')"""
    )
    stats['expired_pending'] = cursor.fetchone()[0]

    # Trades taken from watchlist
    cursor = conn.execute(
        "SELECT COUNT(*) FROM signal_watchlist WHERE trade_taken = 1"
    )
    stats['trades_taken'] = cursor.fetchone()[0]

    conn.close()
    return stats


def get_watchlist_for_review(check_frequency: str = "session") -> List[Dict]:
    """
    Get watchlist items that need review based on check frequency.

    Args:
        check_frequency: 'session' | 'daily' | 'hourly'

    Returns:
        List of items needing review
    """
    conn = get_connection()

    # Determine the check interval
    if check_frequency == "hourly":
        interval = "-1 hours"
    elif check_frequency == "daily":
        interval = "-24 hours"
    else:  # session - check if not checked today
        interval = "-12 hours"

    cursor = conn.execute(
        """SELECT * FROM signal_watchlist
           WHERE status = 'active'
           AND check_frequency = ?
           AND (last_checked IS NULL OR last_checked < datetime('now', ?))
           ORDER BY priority DESC, created_at DESC""",
        (check_frequency, interval)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def remove_from_watchlist(watch_id: str, reason: str = "Manual removal") -> None:
    """Remove an item from the watchlist."""
    update_watchlist_status(watch_id, 'removed', status_reason=reason)


def expire_old_watchlist_items() -> int:
    """
    Mark expired watchlist items as expired.

    Returns:
        Number of items expired
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cursor = conn.execute(
        """UPDATE signal_watchlist
           SET status = 'expired', updated_at = ?, status_reason = 'Auto-expired'
           WHERE status = 'active'
           AND expires_at IS NOT NULL
           AND expires_at < datetime('now')""",
        (timestamp,)
    )
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count


def get_watchlist_by_validation(validation_id: str) -> Optional[Dict]:
    """Get watchlist item by its validation_id."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT * FROM signal_watchlist WHERE validation_id = ?",
        (validation_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_watchlist_by_signal(external_signal_id: int) -> Optional[Dict]:
    """Get watchlist item by its external signal ID."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT * FROM signal_watchlist WHERE external_signal_id = ?",
        (external_signal_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ============================================================================
# QUERY FUNCTIONS
# ============================================================================

def get_recent_queries(limit: int = 50, tool_name: Optional[str] = None) -> List[Dict]:
    """Get recent MCP queries."""
    conn = get_connection()

    if tool_name:
        cursor = conn.execute(
            """SELECT * FROM mcp_queries
               WHERE tool_name = ?
               ORDER BY timestamp_utc DESC LIMIT ?""",
            (tool_name, limit)
        )
    else:
        cursor = conn.execute(
            "SELECT * FROM mcp_queries ORDER BY timestamp_utc DESC LIMIT ?",
            (limit,)
        )

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_trade_cards_for_token(token: str, limit: int = 10) -> List[Dict]:
    """Get historical trade cards for a token."""
    conn = get_connection()
    cursor = conn.execute(
        """SELECT * FROM trade_cards
           WHERE token = ?
           ORDER BY timestamp_utc DESC LIMIT ?""",
        (token.upper(), limit)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_cex_history(asset: str, days: int = 7) -> List[Dict]:
    """Get CEX flow history for an asset."""
    conn = get_connection()
    cursor = conn.execute(
        """SELECT * FROM cex_snapshots
           WHERE asset = ?
           AND timestamp_utc >= datetime('now', ?)
           ORDER BY timestamp_utc DESC""",
        (asset.upper(), f'-{days} days')
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_query_stats() -> Dict:
    """Get query statistics."""
    conn = get_connection()

    stats = {}

    # Total queries
    cursor = conn.execute("SELECT COUNT(*) FROM mcp_queries")
    stats['total_queries'] = cursor.fetchone()[0]

    # Success rate
    cursor = conn.execute("SELECT AVG(success) FROM mcp_queries")
    stats['success_rate'] = cursor.fetchone()[0] or 0

    # Queries by tool
    cursor = conn.execute(
        """SELECT tool_name, COUNT(*) as count
           FROM mcp_queries
           GROUP BY tool_name
           ORDER BY count DESC LIMIT 10"""
    )
    stats['queries_by_tool'] = {row[0]: row[1] for row in cursor.fetchall()}

    # Total trade cards
    cursor = conn.execute("SELECT COUNT(*) FROM trade_cards")
    stats['total_trade_cards'] = cursor.fetchone()[0]

    conn.close()
    return stats


# ============================================================================
# DERIVATIVES TIME-SERIES LOGGING
# ============================================================================

def log_derivatives_snapshot(analysis: dict) -> int:
    """
    Log a derivatives analysis result as a flat row in derivatives_snapshots.
    Called after run_derivatives_analysis() returns.

    Returns row id, or -1 on error.
    """
    try:
        conn = get_connection()
        timestamp = datetime.now(timezone.utc).isoformat()
        symbol = analysis.get("symbol", "UNKNOWN").upper()

        funding = analysis.get("funding", {})
        oi_hist = analysis.get("open_interest", {}).get("history", {})
        oi_ex = analysis.get("open_interest", {}).get("exchanges", {})
        gl = analysis.get("long_short", {}).get("global", {})
        tl = analysis.get("long_short", {}).get("top_traders", {})
        liq = analysis.get("liquidation", {})
        mp = analysis.get("max_pain", {})
        setup = analysis.get("setup", {})

        cursor = conn.execute("""
            INSERT INTO derivatives_snapshots (
                timestamp_utc, symbol, source, price_usd,
                funding_rate_avg, funding_rate_max, funding_rate_max_exchange,
                funding_bias, funding_annualized_pct,
                oi_usd, oi_change_1h_pct, oi_change_4h_pct, oi_change_24h_pct,
                oi_trend, oi_momentum,
                ls_global_ratio, ls_global_long_pct,
                ls_top_account_ratio, ls_top_position_ratio,
                ls_smart_money_lean, ls_extreme, ls_contrarian_signal,
                liq_24h_usd, liq_long_24h_usd, liq_short_24h_usd,
                liq_ls_ratio, liq_bias, liq_acceleration,
                options_max_pain, options_max_pain_distance_pct, options_put_call_ratio,
                lgf_detected, lgf_direction, lgf_confidence
            ) VALUES (
                ?, ?, 'derivatives', ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?
            )
        """, (
            timestamp, symbol, analysis.get("current_price", 0),
            funding.get("avg_rate", 0), funding.get("max_rate", 0),
            funding.get("max_exchange"), funding.get("bias"),
            funding.get("annualized_cost_pct", 0),
            oi_ex.get("total_oi_usd", 0),
            oi_ex.get("change_1h_pct", 0), oi_ex.get("change_4h_pct", 0),
            oi_ex.get("change_24h_pct", 0),
            oi_hist.get("oi_trend"), oi_ex.get("momentum"),
            gl.get("current_ratio", 0), gl.get("current_long_pct", 0),
            tl.get("top_account_ratio", 0), tl.get("top_position_ratio", 0),
            tl.get("smart_money_lean"), 1 if gl.get("extreme") else 0,
            gl.get("contrarian_signal"),
            liq.get("total_24h_usd", 0), liq.get("long_liq_24h_usd", 0),
            liq.get("short_liq_24h_usd", 0), liq.get("long_short_ratio", 0),
            liq.get("bias"), 1 if liq.get("recent_acceleration") else 0,
            mp.get("max_pain_price", 0), mp.get("distance_pct", 0),
            mp.get("put_call_oi_ratio", 0),
            1 if setup.get("detected") else 0,
            setup.get("direction"), setup.get("confidence"),
        ))
        conn.commit()
        row_id = cursor.lastrowid
        conn.close()
        return row_id
    except Exception as e:
        import sys as _sys
        print(f"  ⚠️  Derivatives snapshot logging failed: {e}", file=_sys.stderr)
        return -1


def log_market_snapshot(pulse: dict) -> list:
    """
    Log a market pulse result as two rows (BTC + ETH) in derivatives_snapshots.
    Called after run_market_pulse() returns.

    Returns list of row ids, or empty list on error.
    """
    try:
        conn = get_connection()
        timestamp = datetime.now(timezone.utc).isoformat()
        row_ids = []

        # Shared market-level fields
        fg = pulse.get("fear_greed", {})
        cb = pulse.get("coinbase_premium", {})
        etf = pulse.get("etf", {})

        fg_value = fg.get("value")
        fg_label = fg.get("label")
        cb_rate = cb.get("premium_rate", 0)
        cb_bias = cb.get("bias")
        etf_latest = etf.get("latest_day_flow_usd", 0)
        etf_weekly = etf.get("weekly_net_flow_usd", 0)
        etf_streak = etf.get("streak_days", 0)
        etf_bias = etf.get("bias")

        # BTC row — full data
        btc_f = pulse.get("btc_funding", {})
        btc_oi = pulse.get("btc_oi", {})
        btc_ls = pulse.get("btc_ls", {})
        btc_top = pulse.get("btc_top_ls", {})

        cursor = conn.execute("""
            INSERT INTO derivatives_snapshots (
                timestamp_utc, symbol, source, price_usd,
                funding_rate_avg, funding_rate_max, funding_rate_max_exchange,
                funding_bias, funding_annualized_pct,
                oi_usd, oi_change_1h_pct, oi_change_4h_pct, oi_change_24h_pct,
                oi_momentum,
                ls_global_ratio, ls_global_long_pct,
                ls_top_account_ratio, ls_top_position_ratio,
                ls_smart_money_lean, ls_extreme, ls_contrarian_signal,
                fear_greed_value, fear_greed_label,
                coinbase_premium_rate, coinbase_premium_bias,
                etf_latest_day_flow_usd, etf_weekly_net_flow_usd,
                etf_streak_days, etf_bias
            ) VALUES (
                ?, 'BTC', 'market_pulse', NULL,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?,
                ?,
                ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?
            )
        """, (
            timestamp,
            btc_f.get("avg_rate", 0), btc_f.get("max_rate", 0),
            btc_f.get("max_exchange"), btc_f.get("bias"),
            btc_f.get("annualized_cost_pct", 0),
            btc_oi.get("total_oi_usd", 0), btc_oi.get("change_1h_pct", 0),
            btc_oi.get("change_4h_pct", 0), btc_oi.get("change_24h_pct", 0),
            btc_oi.get("momentum"),
            btc_ls.get("current_ratio", 0), btc_ls.get("current_long_pct", 0),
            btc_top.get("top_account_ratio", 0), btc_top.get("top_position_ratio", 0),
            btc_top.get("smart_money_lean"), 1 if btc_ls.get("extreme") else 0,
            btc_ls.get("contrarian_signal"),
            fg_value, fg_label, cb_rate, cb_bias,
            etf_latest, etf_weekly, etf_streak, etf_bias,
        ))
        row_ids.append(cursor.lastrowid)

        # ETH row — funding + OI only, no L/S
        eth_f = pulse.get("eth_funding", {})
        eth_oi = pulse.get("eth_oi", {})

        cursor = conn.execute("""
            INSERT INTO derivatives_snapshots (
                timestamp_utc, symbol, source, price_usd,
                funding_rate_avg, funding_rate_max, funding_rate_max_exchange,
                funding_bias, funding_annualized_pct,
                oi_usd, oi_change_1h_pct, oi_change_4h_pct, oi_change_24h_pct,
                oi_momentum,
                fear_greed_value, fear_greed_label,
                coinbase_premium_rate, coinbase_premium_bias,
                etf_latest_day_flow_usd, etf_weekly_net_flow_usd,
                etf_streak_days, etf_bias
            ) VALUES (
                ?, 'ETH', 'market_pulse', NULL,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?,
                ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?
            )
        """, (
            timestamp,
            eth_f.get("avg_rate", 0), eth_f.get("max_rate", 0),
            eth_f.get("max_exchange"), eth_f.get("bias"),
            eth_f.get("annualized_cost_pct", 0),
            eth_oi.get("total_oi_usd", 0), eth_oi.get("change_1h_pct", 0),
            eth_oi.get("change_4h_pct", 0), eth_oi.get("change_24h_pct", 0),
            eth_oi.get("momentum"),
            fg_value, fg_label, cb_rate, cb_bias,
            etf_latest, etf_weekly, etf_streak, etf_bias,
        ))
        row_ids.append(cursor.lastrowid)

        conn.commit()
        conn.close()
        return row_ids
    except Exception as e:
        import sys as _sys
        print(f"  ⚠️  Market snapshot logging failed: {e}", file=_sys.stderr)
        return []


# ============================================================================
# DERIVATIVES QUERY FUNCTIONS
# ============================================================================

def get_derivatives_history(symbol: str = None, days: int = 7,
                            source: str = None, limit: int = 50) -> list:
    """Get recent derivatives snapshots."""
    conn = get_connection()
    conditions = []
    params = []

    if symbol:
        conditions.append("symbol = ?")
        params.append(symbol.upper())
    if source:
        conditions.append("source = ?")
        params.append(source)

    conditions.append("timestamp_utc >= datetime('now', ?)")
    params.append(f"-{days} days")

    where = " AND ".join(conditions)
    params.append(limit)

    cursor = conn.execute(f"""
        SELECT * FROM derivatives_snapshots
        WHERE {where}
        ORDER BY timestamp_utc DESC
        LIMIT ?
    """, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_derivatives_stats(symbol: str, days: int = 30) -> dict:
    """Get summary statistics for a token's derivatives history."""
    conn = get_connection()
    cutoff_param = f"-{days} days"

    cursor = conn.execute("""
        SELECT COUNT(*) as cnt,
               AVG(funding_rate_avg) as avg_funding,
               MIN(funding_rate_avg) as min_funding,
               MAX(funding_rate_avg) as max_funding,
               AVG(oi_usd) as avg_oi,
               MIN(oi_usd) as min_oi,
               MAX(oi_usd) as max_oi,
               AVG(ls_global_ratio) as avg_ls,
               MIN(ls_global_ratio) as min_ls,
               MAX(ls_global_ratio) as max_ls,
               AVG(liq_24h_usd) as avg_liq,
               SUM(liq_24h_usd) as total_liq,
               AVG(fear_greed_value) as avg_fg,
               MIN(fear_greed_value) as min_fg,
               MAX(fear_greed_value) as max_fg,
               AVG(etf_weekly_net_flow_usd) as avg_etf_weekly,
               MIN(etf_weekly_net_flow_usd) as min_etf_weekly,
               MAX(etf_weekly_net_flow_usd) as max_etf_weekly
        FROM derivatives_snapshots
        WHERE symbol = ? AND timestamp_utc >= datetime('now', ?)
    """, (symbol.upper(), cutoff_param))
    row = cursor.fetchone()

    # Count extreme events
    cursor2 = conn.execute("""
        SELECT
            SUM(CASE WHEN funding_rate_avg > 0.0003 THEN 1 ELSE 0 END) as funding_high,
            SUM(CASE WHEN funding_rate_avg < -0.0003 THEN 1 ELSE 0 END) as funding_low,
            SUM(CASE WHEN ls_global_ratio > 2.5 THEN 1 ELSE 0 END) as ls_high,
            SUM(CASE WHEN ls_global_ratio < 0.4 THEN 1 ELSE 0 END) as ls_low,
            SUM(CASE WHEN lgf_detected = 1 THEN 1 ELSE 0 END) as lgf_count
        FROM derivatives_snapshots
        WHERE symbol = ? AND timestamp_utc >= datetime('now', ?)
    """, (symbol.upper(), cutoff_param))
    extremes = cursor2.fetchone()

    conn.close()

    return {
        "symbol": symbol.upper(),
        "days": days,
        "snapshot_count": row["cnt"] if row else 0,
        "avg_funding": row["avg_funding"] if row else 0,
        "min_funding": row["min_funding"] if row else 0,
        "max_funding": row["max_funding"] if row else 0,
        "avg_oi": row["avg_oi"] if row else 0,
        "min_oi": row["min_oi"] if row else 0,
        "max_oi": row["max_oi"] if row else 0,
        "avg_ls": row["avg_ls"] if row else 0,
        "min_ls": row["min_ls"] if row else 0,
        "max_ls": row["max_ls"] if row else 0,
        "avg_liq": row["avg_liq"] if row else 0,
        "total_liq": row["total_liq"] if row else 0,
        "avg_fg": row["avg_fg"] if row else 0,
        "min_fg": row["min_fg"] if row else 0,
        "max_fg": row["max_fg"] if row else 0,
        "avg_etf_weekly": row["avg_etf_weekly"] if row else 0,
        "min_etf_weekly": row["min_etf_weekly"] if row else 0,
        "max_etf_weekly": row["max_etf_weekly"] if row else 0,
        "funding_high_count": extremes["funding_high"] if extremes else 0,
        "funding_low_count": extremes["funding_low"] if extremes else 0,
        "ls_high_count": extremes["ls_high"] if extremes else 0,
        "ls_low_count": extremes["ls_low"] if extremes else 0,
        "lgf_count": extremes["lgf_count"] if extremes else 0,
    }


def export_derivatives_csv(symbol: str = None, days: int = 30,
                           output_path: str = None) -> str:
    """Export derivatives snapshots to CSV."""
    import csv
    import io

    conn = get_connection()
    conditions = ["timestamp_utc >= datetime('now', ?)"]
    params = [f"-{days} days"]

    if symbol:
        conditions.append("symbol = ?")
        params.append(symbol.upper())

    where = " AND ".join(conditions)
    cursor = conn.execute(f"""
        SELECT * FROM derivatives_snapshots
        WHERE {where}
        ORDER BY timestamp_utc ASC
    """, params)

    rows = cursor.fetchall()
    if not rows:
        conn.close()
        return ""

    columns = [desc[0] for desc in cursor.description]
    conn.close()

    if output_path:
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for row in rows:
                writer.writerow(row)
        return output_path
    else:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(row)
        return buf.getvalue()


# ============================================================================
# SNAPSHOT PIPELINE FUNCTIONS (cron-fed)
# ============================================================================

def log_cg_snapshot(table: str, symbol: str, endpoint: str, data,
                    interval: str = None, model: str = None,
                    indicator: str = None) -> int:
    """
    Generic logger for Coinglass snapshot tables.

    Args:
        table: Target table name
        symbol: Token symbol (or None for market-wide)
        endpoint: Endpoint identifier
        data: Raw data (dict or list) to store as JSON
        interval: Time interval if applicable
        model: Model identifier (for liquidation heatmaps)
        indicator: Indicator name (for btc_onchain)

    Returns:
        Row ID or -1 on error
    """
    if data is None:
        return -1
    timestamp = datetime.now(timezone.utc).isoformat()
    data_json = json.dumps(data) if not isinstance(data, str) else data

    conn = get_connection()
    try:
        if table == "spot_flow_snapshots":
            cursor = conn.execute(
                """INSERT INTO spot_flow_snapshots
                   (timestamp_utc, symbol, endpoint, interval, data_json)
                   VALUES (?, ?, ?, ?, ?)""",
                (timestamp, symbol.upper(), endpoint, interval, data_json))
        elif table == "basis_snapshots":
            cursor = conn.execute(
                """INSERT INTO basis_snapshots
                   (timestamp_utc, symbol, endpoint, interval, data_json)
                   VALUES (?, ?, ?, ?, ?)""",
                (timestamp, symbol.upper() if symbol else None, endpoint,
                 interval, data_json))
        elif table == "orderbook_snapshots":
            cursor = conn.execute(
                """INSERT INTO orderbook_snapshots
                   (timestamp_utc, symbol, endpoint, interval, data_json)
                   VALUES (?, ?, ?, ?, ?)""",
                (timestamp, symbol.upper(), endpoint, interval, data_json))
        elif table == "oi_exchange_snapshots":
            cursor = conn.execute(
                """INSERT INTO oi_exchange_snapshots
                   (timestamp_utc, symbol, interval, data_json)
                   VALUES (?, ?, ?, ?)""",
                (timestamp, symbol.upper(), interval, data_json))
        elif table == "liquidation_heatmap_snapshots":
            cursor = conn.execute(
                """INSERT INTO liquidation_heatmap_snapshots
                   (timestamp_utc, symbol, model, data_json)
                   VALUES (?, ?, ?, ?)""",
                (timestamp, symbol.upper(), model, data_json))
        elif table == "btc_onchain_snapshots":
            cursor = conn.execute(
                """INSERT INTO btc_onchain_snapshots
                   (timestamp_utc, indicator, data_json)
                   VALUES (?, ?, ?)""",
                (timestamp, indicator, data_json))
        elif table == "etf_flow_snapshots":
            cursor = conn.execute(
                """INSERT INTO etf_flow_snapshots
                   (timestamp_utc, asset, data_json)
                   VALUES (?, ?, ?)""",
                (timestamp, symbol.upper() if symbol else "BTC", data_json))
        else:
            conn.close()
            return -1
        conn.commit()
        row_id = cursor.lastrowid
        conn.close()
        return row_id
    except Exception as e:
        conn.close()
        import sys as _sys
        print(f"  Warning: log_cg_snapshot({table}) failed: {e}", file=_sys.stderr)
        return -1


def log_nansen_snapshot(table: str, token: str, data, tool_name: str = None,
                        holder_segment: str = None, lookback_period: str = None,
                        chain: str = None, label_type: str = None,
                        mode: str = None, source_query_id: str = None) -> int:
    """
    Logger for Nansen snapshot tables.

    Returns:
        Row ID or -1 on error
    """
    if data is None:
        return -1
    timestamp = datetime.now(timezone.utc).isoformat()
    data_json = json.dumps(data) if not isinstance(data, str) else data

    conn = get_connection()
    try:
        if table == "nansen_flow_snapshots":
            cursor = conn.execute(
                """INSERT INTO nansen_flow_snapshots
                   (timestamp_utc, token, tool_name, holder_segment,
                    lookback_period, data_json, source_query_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (timestamp, token.upper(), tool_name, holder_segment,
                 lookback_period, data_json, source_query_id))
        elif table == "nansen_holder_snapshots":
            cursor = conn.execute(
                """INSERT INTO nansen_holder_snapshots
                   (timestamp_utc, token, chain, label_type, mode,
                    data_json, source_query_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (timestamp, token.upper(), chain, label_type, mode,
                 data_json, source_query_id))
        elif table == "nansen_perp_snapshots":
            cursor = conn.execute(
                """INSERT INTO nansen_perp_snapshots
                   (timestamp_utc, data_json, source_query_id)
                   VALUES (?, ?, ?)""",
                (timestamp, data_json, source_query_id))
        elif table == "nansen_quant_snapshots":
            cursor = conn.execute(
                """INSERT INTO nansen_quant_snapshots
                   (timestamp_utc, token, data_json, source_query_id)
                   VALUES (?, ?, ?, ?)""",
                (timestamp, token.upper(), data_json, source_query_id))
        else:
            conn.close()
            return -1
        conn.commit()
        row_id = cursor.lastrowid
        conn.close()
        return row_id
    except Exception as e:
        conn.close()
        import sys as _sys
        print(f"  Warning: log_nansen_snapshot({table}) failed: {e}", file=_sys.stderr)
        return -1


def log_snapshot_run(run_id: str, run_type: str) -> int:
    """Start a snapshot run — insert metadata row. Returns row ID."""
    timestamp = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO snapshot_metadata
           (run_id, run_type, started_at)
           VALUES (?, ?, ?)""",
        (run_id, run_type, timestamp))
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def finish_snapshot_run(run_id: str, succeeded: int, failed: int,
                        rows_inserted: int, errors: list = None) -> None:
    """Finish a snapshot run — update metadata with results."""
    timestamp = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    conn.execute(
        """UPDATE snapshot_metadata
           SET finished_at = ?, endpoints_succeeded = ?, endpoints_failed = ?,
               total_rows_inserted = ?, error_log = ?
           WHERE run_id = ?""",
        (timestamp, succeeded, failed, rows_inserted,
         json.dumps(errors) if errors else None, run_id))
    conn.commit()
    conn.close()


def log_analyze_report(
    token: str,
    price_usd: float = None,
    verdict: str = None,
    conviction: str = None,
    direction: str = None,
    accumulation_score: float = None,
    exchange_flows_signal: str = None,
    fresh_wallets_signal: str = None,
    smart_money_signal: str = None,
    top_pnl_signal: str = None,
    whale_signal: str = None,
    onchain_verdict: str = None,
    perps_verdict: str = None,
    derivatives_verdict: str = None,
    ta_verdict: str = None,
    support_levels: list = None,
    resistance_levels: list = None,
    ta_weekly_rsi: float = None,
    ta_daily_rsi: float = None,
    ta_4h_rsi: float = None,
    ta_weekly_adx: float = None,
    ta_daily_adx: float = None,
    ta_trend_direction: str = None,
    funding_rate: float = None,
    oi_usd: float = None,
    oi_change_24h_pct: float = None,
    ls_global_ratio: float = None,
    ls_crowding: str = None,
    invalidation_criteria: str = None,
    nansen_credits_used: int = None,
    full_markdown: str = None,
) -> str:
    """Log structured /analyze output. Returns report_id."""
    report_id = str(uuid.uuid4())[:12]
    timestamp = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO analyze_snapshots (
                report_id, timestamp_utc, token, price_usd,
                verdict, conviction, direction,
                accumulation_score,
                exchange_flows_signal, fresh_wallets_signal,
                smart_money_signal, top_pnl_signal, whale_signal,
                onchain_verdict, perps_verdict, derivatives_verdict, ta_verdict,
                support_levels_json, resistance_levels_json,
                ta_weekly_rsi, ta_daily_rsi, ta_4h_rsi,
                ta_weekly_adx, ta_daily_adx, ta_trend_direction,
                funding_rate, oi_usd, oi_change_24h_pct,
                ls_global_ratio, ls_crowding,
                invalidation_criteria, nansen_credits_used, full_markdown
            ) VALUES (
                ?, ?, ?, ?,
                ?, ?, ?,
                ?,
                ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?
            )""",
            (report_id, timestamp, token.upper(), price_usd,
             verdict, conviction, direction,
             accumulation_score,
             exchange_flows_signal, fresh_wallets_signal,
             smart_money_signal, top_pnl_signal, whale_signal,
             onchain_verdict, perps_verdict, derivatives_verdict, ta_verdict,
             json.dumps(support_levels) if support_levels else None,
             json.dumps(resistance_levels) if resistance_levels else None,
             ta_weekly_rsi, ta_daily_rsi, ta_4h_rsi,
             ta_weekly_adx, ta_daily_adx, ta_trend_direction,
             funding_rate, oi_usd, oi_change_24h_pct,
             ls_global_ratio, ls_crowding,
             invalidation_criteria, nansen_credits_used, full_markdown))
        conn.commit()
        conn.close()
        return report_id
    except Exception as e:
        conn.close()
        import sys as _sys
        print(f"  Warning: log_analyze_report failed: {e}", file=_sys.stderr)
        return ""


def get_latest_analyze(token: str) -> Optional[Dict]:
    """Get the most recent analyze snapshot for a token."""
    conn = get_connection()
    row = conn.execute(
        """SELECT * FROM analyze_snapshots
           WHERE token = ? ORDER BY timestamp_utc DESC LIMIT 1""",
        (token.upper(),)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_analyze_history(token: str, limit: int = 10) -> List[Dict]:
    """Get analyze snapshot history for a token."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT report_id, timestamp_utc, token, price_usd,
                  verdict, conviction, direction, accumulation_score,
                  onchain_verdict, perps_verdict, derivatives_verdict, ta_verdict,
                  ta_trend_direction, ls_crowding, nansen_credits_used
           FROM analyze_snapshots
           WHERE token = ? ORDER BY timestamp_utc DESC LIMIT ?""",
        (token.upper(), limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def log_accum_distro_report(
    token: str,
    chain: str = None,
    token_address: str = None,
    price_usd: float = None,
    layer1_verdict: str = None,
    layer2_verdict: str = None,
    layer3_verdict: str = None,
    cex_net_flow_usd: float = None,
    cex_inflow_usd: float = None,
    cex_outflow_usd: float = None,
    cex_flow_vs_avg: float = None,
    sm_holders_count: int = None,
    sm_balance_usd: float = None,
    sm_balance_change_24h_pct: float = None,
    sm_net_buy_volume_usd: float = None,
    sm_buyer_count: int = None,
    sm_seller_count: int = None,
    fresh_wallet_count: int = None,
    fresh_wallet_max_score: int = None,
    fresh_wallet_total_usd: float = None,
    final_verdict: str = None,
    conviction: str = None,
    nansen_credits_used: int = None,
    full_markdown: str = None,
) -> str:
    """Log structured /accum-distro output. Returns report_id."""
    report_id = str(uuid.uuid4())[:12]
    timestamp = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO accum_distro_snapshots (
                report_id, timestamp_utc, token, chain, token_address, price_usd,
                layer1_verdict, layer2_verdict, layer3_verdict,
                cex_net_flow_usd, cex_inflow_usd, cex_outflow_usd, cex_flow_vs_avg,
                sm_holders_count, sm_balance_usd, sm_balance_change_24h_pct,
                sm_net_buy_volume_usd, sm_buyer_count, sm_seller_count,
                fresh_wallet_count, fresh_wallet_max_score, fresh_wallet_total_usd,
                final_verdict, conviction, nansen_credits_used, full_markdown
            ) VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?
            )""",
            (report_id, timestamp, token.upper(), chain, token_address, price_usd,
             layer1_verdict, layer2_verdict, layer3_verdict,
             cex_net_flow_usd, cex_inflow_usd, cex_outflow_usd, cex_flow_vs_avg,
             sm_holders_count, sm_balance_usd, sm_balance_change_24h_pct,
             sm_net_buy_volume_usd, sm_buyer_count, sm_seller_count,
             fresh_wallet_count, fresh_wallet_max_score, fresh_wallet_total_usd,
             final_verdict, conviction, nansen_credits_used, full_markdown))
        conn.commit()
        conn.close()
        return report_id
    except Exception as e:
        conn.close()
        import sys as _sys
        print(f"  Warning: log_accum_distro_report failed: {e}", file=_sys.stderr)
        return ""


def get_latest_accum_distro(token: str) -> Optional[Dict]:
    """Get the most recent accum/distro snapshot for a token."""
    conn = get_connection()
    row = conn.execute(
        """SELECT * FROM accum_distro_snapshots
           WHERE token = ? ORDER BY timestamp_utc DESC LIMIT 1""",
        (token.upper(),)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_accum_distro_history(token: str, limit: int = 10) -> List[Dict]:
    """Get accum/distro snapshot history for a token."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT report_id, timestamp_utc, token, chain, price_usd,
                  layer1_verdict, layer2_verdict, layer3_verdict,
                  final_verdict, conviction, nansen_credits_used
           FROM accum_distro_snapshots
           WHERE token = ? ORDER BY timestamp_utc DESC LIMIT ?""",
        (token.upper(), limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def check_snapshot_freshness(stale_hours: float = 7.0) -> Dict[str, Dict]:
    """
    Check freshness of all snapshot tables.

    Returns:
        Dict of {table_name: {"last_snapshot": str, "age_hours": float, "stale": bool}}
    """
    conn = get_connection()
    tables = {
        "derivatives_snapshots": "timestamp_utc",
        "spot_flow_snapshots": "timestamp_utc",
        "basis_snapshots": "timestamp_utc",
        "orderbook_snapshots": "timestamp_utc",
        "oi_exchange_snapshots": "timestamp_utc",
        "liquidation_heatmap_snapshots": "timestamp_utc",
        "btc_onchain_snapshots": "timestamp_utc",
        "etf_flow_snapshots": "timestamp_utc",
        "nansen_flow_snapshots": "timestamp_utc",
        "nansen_holder_snapshots": "timestamp_utc",
        "nansen_perp_snapshots": "timestamp_utc",
        "nansen_quant_snapshots": "timestamp_utc",
        "cex_snapshots": "timestamp_utc",
    }

    result = {}
    now = datetime.now(timezone.utc)

    for table, ts_col in tables.items():
        try:
            row = conn.execute(
                f"SELECT MAX({ts_col}) as latest FROM {table}"
            ).fetchone()
            latest = row["latest"] if row and row["latest"] else None

            if latest:
                try:
                    dt = datetime.fromisoformat(latest.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    age_hours = (now - dt).total_seconds() / 3600
                except Exception:
                    age_hours = 999.0
                result[table] = {
                    "last_snapshot": latest,
                    "age_hours": round(age_hours, 2),
                    "stale": age_hours > stale_hours,
                }
            else:
                result[table] = {
                    "last_snapshot": None,
                    "age_hours": None,
                    "stale": True,
                }
        except Exception:
            result[table] = {
                "last_snapshot": None,
                "age_hours": None,
                "stale": True,
            }

    conn.close()
    return result


# ============================================================================
# HELPERS
# ============================================================================

def _parse_json_input(data_str: str) -> Any:
    """Parse JSON from string or file path."""
    if not data_str:
        return None
    # If it looks like a file path
    if not data_str.strip().startswith(('[', '{')):
        path = Path(data_str)
        if path.exists():
            return json.loads(path.read_text())
    return json.loads(data_str)


def _format_number(n: float) -> str:
    """Format large numbers: 1.2B, 338.2M, 12.5K."""
    if n is None:
        return '-'
    abs_n = abs(n)
    sign = '-' if n < 0 else ''
    if abs_n >= 1e9:
        return f"{sign}{abs_n/1e9:.1f}B"
    elif abs_n >= 1e6:
        return f"{sign}{abs_n/1e6:.1f}M"
    elif abs_n >= 1e3:
        return f"{sign}{abs_n/1e3:.1f}K"
    else:
        return f"{sign}{abs_n:.2f}"


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI for database management."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Titan Intelligence Database CLI")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # init
    subparsers.add_parser('init', help='Initialize database')

    # sync
    subparsers.add_parser('sync', help='Sync local DB to Cowork directory')

    # stats
    subparsers.add_parser('stats', help='Query statistics')

    # recent
    subparsers.add_parser('recent', help='Recent MCP queries')

    # mentor-stats
    subparsers.add_parser('mentor-stats', help='Mentor consultation statistics')

    # flow-stats
    subparsers.add_parser('flow-stats', help='Flow logging statistics')

    # flow-history
    flow_hist_parser = subparsers.add_parser('flow-history', help='Flow history for a token')
    flow_hist_parser.add_argument('token', help='Token symbol')
    flow_hist_parser.add_argument('--days', type=int, default=30, help='Lookback days (default: 30)')
    flow_hist_parser.add_argument('--limit', type=int, default=20, help='Max results (default: 20)')

    # flow-latest
    flow_latest_parser = subparsers.add_parser('flow-latest', help='Latest flows for all tracked tokens')
    flow_latest_parser.add_argument('--tokens', help='Comma-separated token list (default: all)')

    # flow-compare
    flow_compare_parser = subparsers.add_parser('flow-compare', help='Compare current vs historical flows')
    flow_compare_parser.add_argument('token', help='Token symbol')
    flow_compare_parser.add_argument('--days', type=int, default=7, help='Historical lookback (default: 7)')

    # validation-stats
    val_stats_parser = subparsers.add_parser('validation-stats', help='Signal validation statistics')
    val_stats_parser.add_argument('--days', type=int, default=30, help='Lookback days (default: 30)')

    # list-validations
    list_val_parser = subparsers.add_parser('list-validations', help='List recent signal validations')
    list_val_parser.add_argument('--token', help='Filter by token')
    list_val_parser.add_argument('--recommendation', choices=['VALID', 'INVALID', 'NEEDS_CONFIRMATION'])
    list_val_parser.add_argument('--limit', type=int, default=20, help='Max results (default: 20)')

    # show-validation
    show_val_parser = subparsers.add_parser('show-validation', help='Show validation details')
    show_val_parser.add_argument('validation_id', help='Validation ID')

    # update-validation-outcome
    update_val_parser = subparsers.add_parser('update-validation', help='Update validation with trade outcome')
    update_val_parser.add_argument('--validation-id', required=True, help='Validation ID')
    update_val_parser.add_argument('--taken', action='store_true', help='Trade was taken')
    update_val_parser.add_argument('--outcome', choices=['WIN', 'LOSS', 'SKIP'], help='Trade outcome')
    update_val_parser.add_argument('--notes', help='Additional notes')

    # ========== WATCHLIST COMMANDS ==========

    # watchlist-add
    watch_add_parser = subparsers.add_parser('watchlist-add', help='Add token to watchlist')
    watch_add_parser.add_argument('--symbol', required=True, help='Token symbol')
    watch_add_parser.add_argument('--source', choices=['telegram_signal', 'manual', 'skill'], default='manual', help='Source type')
    watch_add_parser.add_argument('--type', choices=['entry_timing', 'confirmation', 'structural', 'invalidation'], default='structural', help='Watch type')
    watch_add_parser.add_argument('--direction', choices=['LONG', 'SHORT'], help='Expected direction')
    watch_add_parser.add_argument('--thesis', help='Why watching this token')
    watch_add_parser.add_argument('--price', type=float, help='Current price')
    watch_add_parser.add_argument('--support', type=float, help='Support level')
    watch_add_parser.add_argument('--resistance', type=float, help='Resistance level')
    watch_add_parser.add_argument('--priority', type=int, default=5, help='Priority 1-10')
    watch_add_parser.add_argument('--frequency', choices=['session', 'daily', 'hourly'], default='session', help='Check frequency')
    watch_add_parser.add_argument('--signal-id', type=int, help='External signal ID')
    watch_add_parser.add_argument('--validation-id', help='Validation ID')

    # watchlist (list active items)
    watch_list_parser = subparsers.add_parser('watchlist', help='List active watchlist items')
    watch_list_parser.add_argument('--source', choices=['telegram_signal', 'manual', 'skill'], help='Filter by source')
    watch_list_parser.add_argument('--type', choices=['entry_timing', 'confirmation', 'structural', 'invalidation'], help='Filter by type')
    watch_list_parser.add_argument('--symbol', help='Filter by symbol')

    # watchlist-show
    watch_show_parser = subparsers.add_parser('watchlist-show', help='Show watchlist item details')
    watch_show_parser.add_argument('watch_id', help='Watchlist item ID')

    # watchlist-update
    watch_update_parser = subparsers.add_parser('watchlist-update', help='Update watchlist item status')
    watch_update_parser.add_argument('--watch-id', required=True, help='Watchlist item ID')
    watch_update_parser.add_argument('--status', choices=['active', 'triggered', 'invalidated', 'expired', 'taken', 'removed'], help='New status')
    watch_update_parser.add_argument('--reason', help='Reason for status change')
    watch_update_parser.add_argument('--trade-taken', action='store_true', help='Trade was taken')
    watch_update_parser.add_argument('--setup-id', help='Trade setup ID')

    # watchlist-remove
    watch_remove_parser = subparsers.add_parser('watchlist-remove', help='Remove item from watchlist')
    watch_remove_parser.add_argument('watch_id', help='Watchlist item ID')
    watch_remove_parser.add_argument('--reason', default='Manual removal', help='Removal reason')

    # watchlist-stats
    subparsers.add_parser('watchlist-stats', help='Watchlist statistics')

    # watchlist-review
    watch_review_parser = subparsers.add_parser('watchlist-review', help='Get items needing review')
    watch_review_parser.add_argument('--frequency', choices=['session', 'daily', 'hourly'], default='session', help='Check frequency')

    # watchlist-expire
    subparsers.add_parser('watchlist-expire', help='Expire old watchlist items')

    # ========== ON-CHAIN RESEARCH DATA COMMANDS ==========

    # store-exchange-balance
    store_exbal_parser = subparsers.add_parser('store-exchange-balance', help='Store daily exchange balance data')
    store_exbal_parser.add_argument('--token', required=True, help='Token symbol')
    store_exbal_parser.add_argument('--chain', help='Blockchain (e.g., ethereum)')
    store_exbal_parser.add_argument('--address', help='Token contract address')
    store_exbal_parser.add_argument('--data', required=True, help='JSON array of daily data (or file path)')

    # store-entities
    store_ent_parser = subparsers.add_parser('store-entities', help='Store entity position snapshots')
    store_ent_parser.add_argument('--token', required=True, help='Token symbol')
    store_ent_parser.add_argument('--date', required=True, help='Snapshot date (YYYY-MM-DD)')
    store_ent_parser.add_argument('--chain', help='Blockchain')
    store_ent_parser.add_argument('--address', help='Token contract address')
    store_ent_parser.add_argument('--data', required=True, help='JSON array of entities (or file path)')

    # store-hunt
    store_hunt_parser = subparsers.add_parser('store-hunt', help='Store hunt results')
    store_hunt_parser.add_argument('--date', required=True, help='Hunt date (YYYY-MM-DD)')
    store_hunt_parser.add_argument('--hunt-id', help='Hunt ID (auto-generated if not provided)')
    store_hunt_parser.add_argument('--data', required=True, help='JSON array of candidates (or file path)')

    # exchange-trend
    extrend_parser = subparsers.add_parser('exchange-trend', help='Show exchange balance trend')
    extrend_parser.add_argument('token', help='Token symbol')
    extrend_parser.add_argument('--days', type=int, default=14, help='Number of days (default: 14)')

    # entity-diff
    entdiff_parser = subparsers.add_parser('entity-diff', help='Show entity changes vs stored snapshot')
    entdiff_parser.add_argument('token', help='Token symbol')
    entdiff_parser.add_argument('--days-back', type=int, default=7, help='Compare against snapshot from N days ago')
    entdiff_parser.add_argument('--data', help='Current entities JSON (omit to compare two stored snapshots)')

    # entity-history
    enthist_parser = subparsers.add_parser('entity-history', help='Show entity position history')
    enthist_parser.add_argument('token', help='Token symbol')
    enthist_parser.add_argument('--address', help='Filter by entity address')
    enthist_parser.add_argument('--days', type=int, default=30, help='Lookback days (default: 30)')
    enthist_parser.add_argument('--limit', type=int, default=50, help='Max results (default: 50)')

    # hunt-history
    hunthist_parser = subparsers.add_parser('hunt-history', help='Show past hunt results')
    hunthist_parser.add_argument('--token', help='Filter by token')
    hunthist_parser.add_argument('--verdict', choices=['STRONG', 'MODERATE', 'WEAK', 'ELIMINATED'], help='Filter by verdict')
    hunthist_parser.add_argument('--days', type=int, default=90, help='Lookback days (default: 90)')
    hunthist_parser.add_argument('--limit', type=int, default=20, help='Max results (default: 20)')

    # backtest-hunts
    backtest_parser = subparsers.add_parser('backtest-hunts', help='Fill in outcome prices for old hunts')
    backtest_parser.add_argument('--result-id', help='Specific result ID to update')
    backtest_parser.add_argument('--price-7d', type=float, help='Price 7 days later')
    backtest_parser.add_argument('--price-14d', type=float, help='Price 14 days later')
    backtest_parser.add_argument('--price-30d', type=float, help='Price 30 days later')


    # derivatives-history
    deriv_hist_parser = subparsers.add_parser('derivatives-history', help='Show recent derivatives snapshots')
    deriv_hist_parser.add_argument('--symbol', help='Token symbol (default: all)')
    deriv_hist_parser.add_argument('--days', type=int, default=7, help='Lookback days (default: 7)')
    deriv_hist_parser.add_argument('--source', choices=['derivatives', 'market_pulse'], help='Filter by source')
    deriv_hist_parser.add_argument('--limit', type=int, default=50, help='Max results (default: 50)')

    # derivatives-stats
    deriv_stats_parser = subparsers.add_parser('derivatives-stats', help='Derivatives summary statistics')
    deriv_stats_parser.add_argument('--symbol', required=True, help='Token symbol')
    deriv_stats_parser.add_argument('--days', type=int, default=30, help='Lookback days (default: 30)')

    # derivatives-export
    deriv_export_parser = subparsers.add_parser('derivatives-export', help='Export derivatives data to CSV')
    deriv_export_parser.add_argument('--symbol', help='Token symbol (default: all)')
    deriv_export_parser.add_argument('--days', type=int, default=30, help='Lookback days (default: 30)')
    deriv_export_parser.add_argument('--output', help='Output file path (default: stdout)')

    # snapshot-freshness
    fresh_parser = subparsers.add_parser('snapshot-freshness', help='Check freshness of all snapshot tables')
    fresh_parser.add_argument('--stale-hours', type=float, default=7.0, help='Hours before a table is stale (default: 7)')
    fresh_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # log-analyze
    log_analyze_parser = subparsers.add_parser('log-analyze', help='Log structured /analyze output')
    log_analyze_parser.add_argument('--json', dest='json_data', required=True,
                                     help='JSON object with analyze fields')

    # analyze-history
    analyze_hist_parser = subparsers.add_parser('analyze-history', help='Show analyze history for a token')
    analyze_hist_parser.add_argument('token', help='Token symbol')
    analyze_hist_parser.add_argument('--limit', type=int, default=10, help='Max results (default: 10)')

    # log-accum-distro
    log_ad_parser = subparsers.add_parser('log-accum-distro', help='Log structured /accum-distro output')
    log_ad_parser.add_argument('--json', dest='json_data', required=True,
                                help='JSON object with accum-distro fields')

    # accum-distro-history
    ad_hist_parser = subparsers.add_parser('accum-distro-history', help='Show accum/distro history for a token')
    ad_hist_parser.add_argument('token', help='Token symbol')
    ad_hist_parser.add_argument('--limit', type=int, default=10, help='Max results (default: 10)')

    # log-nansen (raw Nansen MCP responses)
    log_nansen_parser = subparsers.add_parser('log-nansen', help='Log raw Nansen MCP response to snapshot table')
    log_nansen_parser.add_argument('--json', dest='json_data', required=True,
                                    help='JSON: {table, token, data, tool_name, ...}')

    # refresh-setups (existing cron command)
    subparsers.add_parser('refresh-setups', help='Refresh OHLCV for active watchlist setups + BTC/ETH/SOL')

    args = parser.parse_args()

    if args.command == "init":
        init_db()
        print(f"Database initialized at {DB_PATH}")

    elif args.command == "sync":
        ok = sync_to_cowork()
        sys.exit(0 if ok else 1)

    elif args.command == "stats":
        stats = get_query_stats()
        print(f"Total MCP queries: {stats['total_queries']}")
        print(f"Success rate: {stats['success_rate']:.1%}")
        print(f"Total trade cards: {stats['total_trade_cards']}")
        print("\nQueries by tool:")
        for tool, count in stats['queries_by_tool'].items():
            print(f"  {tool}: {count}")

    elif args.command == "recent":
        queries = get_recent_queries(10)
        for q in queries:
            print(f"{q['timestamp_utc'][:19]} | {q['tool_name']} | {q['context_token'] or '-'}")

    elif args.command == "mentor-stats":
        stats = get_mentor_stats()
        print(f"Total mentor consultations: {stats['total_consultations']}")
        print(f"Total tokens used: {stats['total_tokens']:,}")
        print(f"Total cost: ${stats['total_cost_usd']:.4f}")
        print(f"Agreement rate: {stats['agreement_rate']:.1%}")
        if stats['by_question_type']:
            print("\nBy question type:")
            for qtype, count in stats['by_question_type'].items():
                print(f"  {qtype}: {count}")
        if stats['by_suggested_action']:
            print("\nBy suggested action:")
            for action, count in stats['by_suggested_action'].items():
                print(f"  {action}: {count}")

    elif args.command == "flow-stats":
        stats = get_flow_stats()
        print(f"\n=== Flow Logging Statistics ===\n")
        print(f"Total snapshots: {stats['total_snapshots']}")
        print(f"Tokens tracked: {stats['tokens_tracked']}")
        if stats['by_token']:
            print("\nBy Token:")
            for token, data in stats['by_token'].items():
                print(f"  {token}: {data['count']} snapshots ({data['first'][:10]} to {data['last'][:10]})")
        if stats['signal_distribution']:
            print("\nSignal Distribution:")
            for signal, count in stats['signal_distribution'].items():
                print(f"  {signal}: {count}")

    elif args.command == "flow-history":
        flows = get_flow_history(args.token, days=args.days, limit=args.limit)
        if not flows:
            print(f"No flow history for {args.token.upper()}")
            return
        print(f"\n=== Flow History: {args.token.upper()} ({len(flows)} snapshots) ===\n")
        print(f"{'Date':<12} {'Price':<10} {'Exchange':<12} {'Fresh':<12} {'Smart$':<12} {'PnL':<12} {'Signal':<12} {'Score'}")
        print("-" * 100)
        for f in flows:
            date = f['timestamp_utc'][:10] if f['timestamp_utc'] else '-'
            price = f"${f['price_usd']:.2f}" if f['price_usd'] else '-'
            exch = f"${f['exchange_net_flow']/1e6:.1f}M" if f['exchange_net_flow'] else '-'
            fresh = f"${f['fresh_wallet_net_flow']/1e6:.1f}M" if f['fresh_wallet_net_flow'] else '-'
            smart = f"${f['smart_money_net_flow']/1e6:.1f}M" if f['smart_money_net_flow'] else '-'
            pnl = f"${f['top_pnl_net_flow']/1e6:.1f}M" if f['top_pnl_net_flow'] else '-'
            signal = f['overall_signal'] or '-'
            score = f"{f['accumulation_score']}/5" if f['accumulation_score'] is not None else '-'
            print(f"{date:<12} {price:<10} {exch:<12} {fresh:<12} {smart:<12} {pnl:<12} {signal:<12} {score}")

    elif args.command == "flow-latest":
        tokens = args.tokens.split(',') if args.tokens else None
        flows = get_all_latest_flows(tokens)
        if not flows:
            print("No flow data found.")
            return
        print(f"\n=== Latest Flows ({len(flows)} tokens) ===\n")
        print(f"{'Token':<8} {'Date':<12} {'Exchange':<12} {'Fresh':<12} {'Smart$':<12} {'Signal':<12} {'Score'}")
        print("-" * 85)
        for f in flows:
            date = f['timestamp_utc'][:10] if f['timestamp_utc'] else '-'
            exch = f"${f['exchange_net_flow']/1e6:.1f}M" if f['exchange_net_flow'] else '-'
            fresh = f"${f['fresh_wallet_net_flow']/1e6:.1f}M" if f['fresh_wallet_net_flow'] else '-'
            smart = f"${f['smart_money_net_flow']/1e6:.1f}M" if f['smart_money_net_flow'] else '-'
            signal = f['overall_signal'] or '-'
            score = f"{f['accumulation_score']}/5" if f['accumulation_score'] is not None else '-'
            print(f"{f['token']:<8} {date:<12} {exch:<12} {fresh:<12} {smart:<12} {signal:<12} {score}")

    elif args.command == "flow-compare":
        comparison = get_flow_comparison(args.token, days_back=args.days)
        if not comparison:
            print(f"No flow data for {args.token.upper()}")
            return
        print(f"\n=== Flow Comparison: {comparison['token']} ===")
        print(f"Latest: {comparison['latest_timestamp'][:19]}")
        print(f"Historical samples: {comparison['snapshot_count']} (past {args.days} days)\n")
        print(f"{'Segment':<15} {'Current':<15} {'Avg ({args.days}d)':<15}")
        print("-" * 45)
        curr = comparison['current']
        hist = comparison['historical_avg']
        for seg in ['exchange', 'fresh_wallet', 'smart_money', 'top_pnl', 'whale']:
            c = f"${curr[seg]/1e6:.2f}M" if curr[seg] else '-'
            h = f"${hist[seg]/1e6:.2f}M" if hist[seg] else '-'
            print(f"{seg:<15} {c:<15} {h:<15}")
        print(f"\nOverall Signal: {curr['overall_signal']} | Accumulation Score: {curr['accumulation_score']}/5")

    elif args.command == "validation-stats":
        stats = get_validation_stats(days=args.days)
        print(f"\n=== Signal Validation Statistics ({args.days} days) ===\n")
        print(f"Total validations: {stats['total_validations']}")
        print(f"Signal alignment rate: {stats['alignment_rate']:.1%}")
        print(f"Mentor consultation rate: {stats['mentor_consultation_rate']:.1%}")
        if stats['by_recommendation']:
            print("\nBy Recommendation:")
            for rec, count in stats['by_recommendation'].items():
                print(f"  {rec}: {count}")
        if stats['by_symbol']:
            print("\nBy Symbol:")
            for symbol, count in stats['by_symbol'].items():
                print(f"  {symbol}: {count}")
        if stats['by_outcome']:
            print("\nBy Outcome:")
            for outcome, count in stats['by_outcome'].items():
                print(f"  {outcome}: {count}")

    elif args.command == "list-validations":
        validations = get_recent_validations(
            symbol=args.token,
            recommendation=args.recommendation,
            limit=args.limit
        )
        if not validations:
            print("No validations found.")
            return
        print(f"\n{'ID':<10} {'Symbol':<8} {'Dir':<6} {'Titan':<20} {'Aligns':<8} {'Date':<12}")
        print("-" * 70)
        for v in validations:
            aligns = "Yes" if v['signal_aligns'] else ("No" if v['signal_aligns'] == 0 else "-")
            date = v['timestamp_utc'][:10] if v['timestamp_utc'] else '-'
            print(f"{v['validation_id']:<10} {v['symbol']:<8} {v['direction']:<6} {v['titan_recommendation'] or '-':<20} {aligns:<8} {date:<12}")

    elif args.command == "show-validation":
        val = get_validation_by_id(args.validation_id)
        if not val:
            print(f"Validation {args.validation_id} not found.")
            return
        print(f"\n=== Validation {val['validation_id']} ===\n")
        print(f"Symbol: {val['symbol']} {val['direction']}")
        print(f"Provider: {val['provider']}")
        print(f"External Signal ID: {val['external_signal_id']}")
        print(f"Created: {val['timestamp_utc'][:19]}")
        print(f"\n--- Titan Validation ---")
        print(f"Accumulation Score: {val['accumulation_score']}/5" if val['accumulation_score'] is not None else "Accumulation Score: -")
        print(f"TA Verdict: {val['ta_verdict'] or '-'}")
        print(f"On-Chain Verdict: {val['onchain_verdict'] or '-'}")
        print(f"Signal Aligns: {'Yes' if val['signal_aligns'] else 'No' if val['signal_aligns'] == 0 else '-'}")
        print(f"\n--- Recommendation ---")
        print(f"Titan Says: {val['titan_recommendation'] or '-'}")
        if val['recommendation_reason']:
            print(f"Reason: {val['recommendation_reason']}")
        if val['mentor_consulted']:
            print(f"\n--- Mentor Review ---")
            print(f"Mentor Verdict: {val['mentor_verdict'] or '-'}")
            print(f"Confidence Adj: {val['mentor_confidence_adj'] or 0:+.2f}")
        if val['chart_analyzed']:
            print(f"\n--- Chart Notes ---")
            print(val['chart_notes'] or 'No notes')
        if val['suggested_entry']:
            print(f"\n--- Suggested Levels ---")
            print(f"Entry: ${val['suggested_entry']} | Stop: ${val['suggested_stop'] or '-'} | Target: ${val['suggested_target'] or '-'}")
        if val['trade_outcome']:
            print(f"\n--- Outcome ---")
            print(f"Trade Taken: {'Yes' if val['trade_taken'] else 'No'}")
            print(f"Outcome: {val['trade_outcome']}")
            if val['notes']:
                print(f"Notes: {val['notes']}")

    elif args.command == "update-validation":
        update_validation_outcome(
            validation_id=args.validation_id,
            trade_taken=args.taken,
            trade_outcome=args.outcome,
            notes=args.notes
        )
        print(f"Validation {args.validation_id} updated")

    # ========== WATCHLIST HANDLERS ==========

    elif args.command == "watchlist-add":
        watch_id = add_to_watchlist(
            symbol=args.symbol,
            source_type=args.source,
            watch_type=args.type,
            direction=args.direction,
            original_thesis=args.thesis,
            price_at_creation=args.price,
            support_level=args.support,
            resistance_level=args.resistance,
            priority=args.priority,
            check_frequency=args.frequency,
            external_signal_id=args.signal_id,
            validation_id=args.validation_id
        )
        print(f"Added {args.symbol} to watchlist: {watch_id}")

    elif args.command == "watchlist":
        items = get_active_watchlist(
            source_type=args.source,
            watch_type=args.type,
            symbol=args.symbol
        )
        if not items:
            print("No active watchlist items.")
            return
        print(f"\n=== Active Watchlist ({len(items)} items) ===\n")
        print(f"{'ID':<10} {'Symbol':<8} {'Dir':<6} {'Type':<15} {'Source':<15} {'Price':<10} {'Priority'}")
        print("-" * 80)
        for item in items:
            direction = item['direction'] or '-'
            price = f"${item['last_price']:.2f}" if item['last_price'] else '-'
            print(f"{item['watch_id']:<10} {item['symbol']:<8} {direction:<6} {item['watch_type']:<15} {item['source_type']:<15} {price:<10} {item['priority']}")

    elif args.command == "watchlist-show":
        item = get_watchlist_item(args.watch_id)
        if not item:
            print(f"Watchlist item {args.watch_id} not found.")
            return
        print(f"\n=== Watchlist Item: {item['watch_id']} ===\n")
        print(f"Symbol: {item['symbol']} {item['direction'] or ''}")
        print(f"Source: {item['source_type']} | Type: {item['watch_type']}")
        print(f"Status: {item['status']}")
        print(f"Priority: {item['priority']} | Check: {item['check_frequency']}")
        print(f"\nCreated: {item['created_at'][:19]}")
        print(f"Last Checked: {item['last_checked'][:19] if item['last_checked'] else 'Never'}")
        if item['original_thesis']:
            print(f"\nThesis: {item['original_thesis']}")
        print(f"\n--- Price Levels ---")
        print(f"At Creation: ${item['price_at_creation']:.2f}" if item['price_at_creation'] else "At Creation: -")
        print(f"Current: ${item['last_price']:.2f}" if item['last_price'] else "Current: -")
        if item['support_level']:
            print(f"Support: ${item['support_level']}")
        if item['resistance_level']:
            print(f"Resistance: ${item['resistance_level']}")
        print(f"\n--- Analysis ---")
        print(f"Original: Score {item['original_accumulation_score']}/5 | TA: {item['original_ta_verdict']} | On-chain: {item['original_onchain_verdict']}")
        print(f"Current:  Score {item['current_accumulation_score']}/5 | TA: {item['current_ta_verdict']} | On-chain: {item['current_onchain_verdict']}")
        if item['status_changed']:
            print(f"\n⚠️  Analysis Changed: {item['change_summary']}")
        if item['entry_conditions']:
            print(f"\nEntry Conditions: {item['entry_conditions']}")
        if item['invalidation_conditions']:
            print(f"Invalidation: {item['invalidation_conditions']}")

    elif args.command == "watchlist-update":
        update_watchlist_status(
            watch_id=args.watch_id,
            status=args.status,
            status_reason=args.reason,
            trade_taken=args.trade_taken if hasattr(args, 'trade_taken') else None,
            trade_setup_id=args.setup_id if hasattr(args, 'setup_id') else None
        )
        print(f"Watchlist item {args.watch_id} updated to '{args.status}'")

    elif args.command == "watchlist-remove":
        remove_from_watchlist(args.watch_id, reason=args.reason)
        print(f"Removed {args.watch_id} from watchlist")

    elif args.command == "watchlist-stats":
        stats = get_watchlist_stats()
        print(f"\n=== Watchlist Statistics ===\n")
        print(f"Active items: {stats['active']}")
        print(f"Needs review: {stats['needs_review']}")
        print(f"Analysis changed: {stats['analysis_changed']}")
        print(f"Expired pending: {stats['expired_pending']}")
        print(f"Trades taken: {stats['trades_taken']}")
        if stats['by_status']:
            print("\nBy Status:")
            for status, count in stats['by_status'].items():
                print(f"  {status}: {count}")
        if stats['by_source']:
            print("\nBy Source:")
            for source, count in stats['by_source'].items():
                print(f"  {source}: {count}")
        if stats['by_watch_type']:
            print("\nBy Type:")
            for wtype, count in stats['by_watch_type'].items():
                print(f"  {wtype}: {count}")

    elif args.command == "watchlist-review":
        items = get_watchlist_for_review(check_frequency=args.frequency)
        if not items:
            print(f"No items need {args.frequency} review.")
            return
        print(f"\n=== Items Needing Review ({len(items)}) ===\n")
        for item in items:
            last_check = item['last_checked'][:10] if item['last_checked'] else 'Never'
            print(f"[{item['watch_id']}] {item['symbol']} {item['direction'] or ''} - {item['watch_type']} (last: {last_check})")
            if item['original_thesis']:
                print(f"    Thesis: {item['original_thesis'][:60]}...")

    elif args.command == "watchlist-expire":
        count = expire_old_watchlist_items()
        print(f"Expired {count} watchlist items")

    # ========== ON-CHAIN RESEARCH DATA HANDLERS ==========

    elif args.command == "store-exchange-balance":
        data = _parse_json_input(args.data)
        count = log_exchange_balance_daily(
            token=args.token, daily_data=data,
            chain=args.chain, token_address=args.address
        )
        print(f"Stored {count} daily balance rows for {args.token.upper()}")

    elif args.command == "store-entities":
        data = _parse_json_input(args.data)
        count = log_entity_snapshot(
            token=args.token, snapshot_date=args.date,
            entities=data, chain=args.chain, token_address=args.address
        )
        print(f"Stored {count} entity snapshots for {args.token.upper()} on {args.date}")

    elif args.command == "store-hunt":
        data = _parse_json_input(args.data)
        hunt_id = log_hunt_result(
            hunt_date=args.date, candidates=data,
            hunt_id=args.hunt_id
        )
        print(f"Stored {len(data)} hunt candidates (hunt_id: {hunt_id})")

    elif args.command == "exchange-trend":
        result = get_exchange_balance_trend(args.token, days=args.days)
        if not result['days']:
            print(f"No exchange balance data for {args.token.upper()}")
            return
        s = result['summary']
        print(f"\n=== Exchange Balance Trend: {s['token']} ({s['data_days']} days) ===")
        print(f"Period: {s['oldest_date']} -> {s['newest_date']}")
        print(f"Balance Change: {s['balance_change_pct']:+.1f}%")
        print(f"Outflow Days: {s['outflow_days']}/{s['data_days']} | Inflow Days: {s['inflow_days']}/{s['data_days']}")
        print(f"Total Inflows: ${_format_number(s['total_inflows_usd'])} | Outflows: ${_format_number(s['total_outflows_usd'])}")
        print(f"Net: ${_format_number(s['net_flow_usd'])}\n")
        print(f"{'Date':<12} {'Balance':<15} {'Inflows':<12} {'Outflows':<12} {'Net':<12} {'Price':<10}")
        print("-" * 75)
        for d in result['days']:
            bal = _format_number(d['balance']) if d.get('balance') else '-'
            inf = f"${_format_number(d['inflows_usd'])}" if d.get('inflows_usd') else '-'
            outf = f"${_format_number(d['outflows_usd'])}" if d.get('outflows_usd') else '-'
            net = f"${_format_number(d['net_flow_usd'])}" if d.get('net_flow_usd') else '-'
            price = f"${d['price']:.4f}" if d.get('price') else '-'
            print(f"{d['date']:<12} {bal:<15} {inf:<12} {outf:<12} {net:<12} {price:<10}")

    elif args.command == "entity-diff":
        current = _parse_json_input(args.data) if args.data else None
        diff = get_entity_diff(args.token, current_entities=current, days_back=args.days_back)
        print(f"\n=== Entity Diff: {args.token.upper()} ===")
        print(f"Latest: {diff['latest_date']} vs Stored: {diff['comparison_date'] or 'N/A'}\n")
        if diff['new']:
            print(f"NEW ENTITIES ({len(diff['new'])}):")
            for e in diff['new']:
                name = e.get('entity_name') or e.get('entity_address', '?')[:12]
                bal = _format_number(e.get('balance'))
                print(f"  + {name}: {bal}")
        if diff['removed']:
            print(f"\nREMOVED ({len(diff['removed'])}):")
            for e in diff['removed']:
                name = e.get('entity_name') or e.get('entity_address', '?')[:12]
                print(f"  - {name}")
        if diff['changed']:
            print(f"\nCHANGED ({len(diff['changed'])}):")
            for e in diff['changed']:
                name = e.get('entity_name') or e.get('entity_address', '?')[:12]
                print(f"  ~ {name}: {_format_number(e['old_balance'])} -> {_format_number(e['new_balance'])} ({e['change_pct']:+.1f}%)")
        if not diff['new'] and not diff['removed'] and not diff['changed']:
            print("No changes detected.")

    elif args.command == "entity-history":
        rows = get_entity_history(
            args.token, entity_address=args.address,
            days=args.days, limit=args.limit
        )
        if not rows:
            print(f"No entity history for {args.token.upper()}")
            return
        print(f"\n=== Entity History: {args.token.upper()} ({len(rows)} records) ===\n")
        print(f"{'Date':<12} {'Entity':<25} {'Type':<15} {'Balance':<15} {'30d Chg':<12} {'Own%':<8}")
        print("-" * 90)
        for r in rows:
            name = (r.get('entity_name') or r.get('entity_address', '?')[:12])[:24]
            etype = (r.get('entity_type') or '-')[:14]
            bal = _format_number(r.get('balance'))
            chg = _format_number(r.get('change_30d')) if r.get('change_30d') else '-'
            own = f"{r['ownership_pct']:.2f}%" if r.get('ownership_pct') else '-'
            print(f"{r['snapshot_date']:<12} {name:<25} {etype:<15} {bal:<15} {chg:<12} {own:<8}")

    elif args.command == "hunt-history":
        results = get_hunt_history(
            token=args.token, days=args.days,
            verdict=args.verdict, limit=args.limit
        )
        if not results:
            print("No hunt results found.")
            return
        print(f"\n=== Hunt History ({len(results)} results) ===\n")
        print(f"{'Date':<12} {'Token':<8} {'Score':<7} {'Verdict':<12} {'Price':<10} {'7d':<8} {'14d':<8} {'30d':<8}")
        print("-" * 80)
        for r in results:
            score = f"{r['alpha_score']}/12" if r.get('alpha_score') is not None else '-'
            price = f"${r['price_at_hunt']:.4f}" if r.get('price_at_hunt') else '-'
            d7 = f"{r['pct_change_7d']:+.1f}%" if r.get('pct_change_7d') is not None else '-'
            d14 = f"{r['pct_change_14d']:+.1f}%" if r.get('pct_change_14d') is not None else '-'
            d30 = f"{r['pct_change_30d']:+.1f}%" if r.get('pct_change_30d') is not None else '-'
            print(f"{r['hunt_date']:<12} {r['token']:<8} {score:<7} {r['verdict'] or '-':<12} {price:<10} {d7:<8} {d14:<8} {d30:<8}")

    elif args.command == "backtest-hunts":
        if args.result_id:
            update_hunt_outcome(
                result_id=args.result_id,
                price_7d_later=args.price_7d,
                price_14d_later=args.price_14d,
                price_30d_later=args.price_30d
            )
            print(f"Updated outcome for {args.result_id}")
        else:
            # Show hunts that need outcome data
            results = get_hunt_history(days=90, limit=50)
            needs_update = [r for r in results if r.get('price_7d_later') is None]
            if not needs_update:
                print("All hunt results have outcome data.")
                return
            print(f"\n=== Hunts Needing Outcome Data ({len(needs_update)}) ===\n")
            print(f"{'ID':<10} {'Date':<12} {'Token':<8} {'Score':<7} {'Price':<10}")
            print("-" * 50)
            for r in needs_update:
                score = f"{r['alpha_score']}/12" if r.get('alpha_score') is not None else '-'
                price = f"${r['price_at_hunt']:.4f}" if r.get('price_at_hunt') else '-'
                print(f"{r['result_id']:<10} {r['hunt_date']:<12} {r['token']:<8} {score:<7} {price:<10}")

    # ========== OHLCV REFRESH HANDLERS ==========

    # ========== DERIVATIVES HISTORY HANDLERS ==========

    elif args.command == "derivatives-history":
        rows = get_derivatives_history(
            symbol=args.symbol, days=args.days,
            source=args.source, limit=args.limit
        )
        if not rows:
            sym_label = args.symbol.upper() if args.symbol else "all tokens"
            print(f"No derivatives history for {sym_label} (last {args.days} days)")
            return

        sym_label = args.symbol.upper() if args.symbol else "All Tokens"
        print(f"\n=== Derivatives History: {sym_label} (last {args.days} days, {len(rows)} snapshots) ===\n")
        print(f"  {'Date/Time':<18} {'Sym':<5} {'Funding%':<10} {'OI':<9} {'OI∆24h':<8} {'L/S':<6} {'Long%':<7} {'Top Lean':<10} {'Liq24h':<10} {'F&G':<5} {'Premium'}")
        print(f"  {'─' * 105}")
        for r in rows:
            ts = r['timestamp_utc'][:16] if r['timestamp_utc'] else '-'
            sym = r['symbol'] or '-'
            fr = f"{r['funding_rate_avg']*100:.4f}%" if r.get('funding_rate_avg') else '-'
            oi = _format_number(r.get('oi_usd')) if r.get('oi_usd') else '-'
            oi_c = f"{r['oi_change_24h_pct']:+.1f}%" if r.get('oi_change_24h_pct') else '-'
            ls = f"{r['ls_global_ratio']:.2f}x" if r.get('ls_global_ratio') else '-'
            lp = f"{r['ls_global_long_pct']:.1f}%" if r.get('ls_global_long_pct') else '-'
            lean = (r.get('ls_smart_money_lean') or '-')[:9]
            liq = _format_number(r.get('liq_24h_usd')) if r.get('liq_24h_usd') else '-'
            fg = str(r['fear_greed_value']) if r.get('fear_greed_value') is not None else '-'
            prem = f"{r['coinbase_premium_rate']*100:+.2f}%" if r.get('coinbase_premium_rate') else '-'
            print(f"  {ts:<18} {sym:<5} {fr:<10} {oi:<9} {oi_c:<8} {ls:<6} {lp:<7} {lean:<10} {liq:<10} {fg:<5} {prem}")

    elif args.command == "derivatives-stats":
        stats = get_derivatives_stats(symbol=args.symbol, days=args.days)
        if stats['snapshot_count'] == 0:
            print(f"No derivatives data for {args.symbol.upper()} (last {args.days} days)")
            return

        print(f"\n=== Derivatives Stats: {stats['symbol']} (last {stats['days']} days, {stats['snapshot_count']} snapshots) ===\n")
        avg_f = stats['avg_funding'] or 0
        min_f = stats['min_funding'] or 0
        max_f = stats['max_funding'] or 0
        print(f"  Funding Rate:  avg {avg_f*100:+.4f}%  |  min {min_f*100:+.4f}%  |  max {max_f*100:+.4f}%")
        print(f"  Open Interest: avg {_format_number(stats['avg_oi'] or 0)}    |  min {_format_number(stats['min_oi'] or 0)}    |  max {_format_number(stats['max_oi'] or 0)}")
        avg_ls = stats['avg_ls'] or 0
        min_ls = stats['min_ls'] or 0
        max_ls = stats['max_ls'] or 0
        print(f"  L/S Ratio:     avg {avg_ls:.2f}x     |  min {min_ls:.2f}x     |  max {max_ls:.2f}x")
        avg_liq = stats['avg_liq'] or 0
        total_liq = stats['total_liq'] or 0
        print(f"  Liquidations:  avg {_format_number(avg_liq)}/snap |  total {_format_number(total_liq)}")
        if stats.get('avg_fg'):
            print(f"  Fear & Greed:  avg {stats['avg_fg']:.0f}        |  min {stats['min_fg'] or 0}          |  max {stats['max_fg'] or 0}")
        if stats.get('avg_etf_weekly'):
            print(f"  ETF Weekly:    avg {_format_number(stats['avg_etf_weekly'] or 0)}    |  min {_format_number(stats['min_etf_weekly'] or 0)}     |  max {_format_number(stats['max_etf_weekly'] or 0)}")

        print(f"\n  Extreme Events (last {stats['days']}d):")
        print(f"    - {stats['funding_high_count'] or 0}x funding > 0.03% (long crowded)")
        print(f"    - {stats['funding_low_count'] or 0}x funding < -0.03% (short crowded)")
        print(f"    - {stats['ls_high_count'] or 0}x L/S ratio > 2.5 (extreme longs)")
        print(f"    - {stats['ls_low_count'] or 0}x L/S ratio < 0.4 (extreme shorts)")
        print(f"    - {stats['lgf_count'] or 0}x Liquidity Grab Fade detected")

    elif args.command == "derivatives-export":
        result = export_derivatives_csv(
            symbol=args.symbol, days=args.days,
            output_path=args.output
        )
        if not result:
            sym_label = args.symbol.upper() if args.symbol else "any token"
            print(f"No derivatives data for {sym_label} (last {args.days} days)")
        elif args.output:
            print(f"Exported to {args.output}")
        else:
            print(result)

    elif args.command == "snapshot-freshness":
        freshness = check_snapshot_freshness(stale_hours=args.stale_hours)
        if args.json:
            print(json.dumps(freshness, indent=2, default=str))
        else:
            print(f"\n=== Snapshot Freshness (stale > {args.stale_hours}h) ===\n")
            print(f"  {'Table':<35} {'Last Snapshot':<22} {'Age':<10} {'Status'}")
            print(f"  {'─' * 80}")
            for table, info in sorted(freshness.items()):
                last = info['last_snapshot'][:19] if info['last_snapshot'] else 'NEVER'
                age = f"{info['age_hours']:.1f}h" if info['age_hours'] is not None else '-'
                status = 'STALE' if info['stale'] else 'OK'
                marker = '  ' if not info['stale'] else '!!'
                print(f"{marker} {table:<35} {last:<22} {age:<10} {status}")

    elif args.command == "log-analyze":
        data = _parse_json_input(args.json_data)
        if not data or not data.get("token"):
            print("Error: JSON must include 'token' field", file=sys.stderr)
            sys.exit(1)
        report_id = log_analyze_report(
            token=data["token"],
            price_usd=data.get("price_usd"),
            verdict=data.get("verdict"),
            conviction=data.get("conviction"),
            direction=data.get("direction"),
            accumulation_score=data.get("accumulation_score"),
            exchange_flows_signal=data.get("exchange_flows_signal"),
            fresh_wallets_signal=data.get("fresh_wallets_signal"),
            smart_money_signal=data.get("smart_money_signal"),
            top_pnl_signal=data.get("top_pnl_signal"),
            whale_signal=data.get("whale_signal"),
            onchain_verdict=data.get("onchain_verdict"),
            perps_verdict=data.get("perps_verdict"),
            derivatives_verdict=data.get("derivatives_verdict"),
            ta_verdict=data.get("ta_verdict"),
            support_levels=data.get("support_levels"),
            resistance_levels=data.get("resistance_levels"),
            ta_weekly_rsi=data.get("ta_weekly_rsi"),
            ta_daily_rsi=data.get("ta_daily_rsi"),
            ta_4h_rsi=data.get("ta_4h_rsi"),
            ta_weekly_adx=data.get("ta_weekly_adx"),
            ta_daily_adx=data.get("ta_daily_adx"),
            ta_trend_direction=data.get("ta_trend_direction"),
            funding_rate=data.get("funding_rate"),
            oi_usd=data.get("oi_usd"),
            oi_change_24h_pct=data.get("oi_change_24h_pct"),
            ls_global_ratio=data.get("ls_global_ratio"),
            ls_crowding=data.get("ls_crowding"),
            invalidation_criteria=data.get("invalidation_criteria"),
            nansen_credits_used=data.get("nansen_credits_used"),
            full_markdown=data.get("full_markdown"),
        )
        if report_id:
            print(json.dumps({"report_id": report_id, "token": data["token"], "status": "logged"}))
        else:
            print("Error: failed to log analyze report", file=sys.stderr)
            sys.exit(1)

    elif args.command == "analyze-history":
        history = get_analyze_history(args.token, limit=args.limit)
        if not history:
            print(f"No analyze snapshots found for {args.token}")
        else:
            print(f"\n=== Analyze History: {args.token} ({len(history)} reports) ===\n")
            for r in history:
                ts = r['timestamp_utc'][:16]
                v = r.get('verdict', '?')
                c = r.get('conviction', '?')
                acc = r.get('accumulation_score')
                acc_str = f"  Accum: {acc}/5" if acc is not None else ""
                price = f"  ${r['price_usd']:,.0f}" if r.get('price_usd') else ""
                print(f"  {ts}  {v} ({c}){price}{acc_str}")
                pillars = []
                for p in ['onchain_verdict', 'perps_verdict', 'derivatives_verdict', 'ta_verdict']:
                    if r.get(p):
                        pillars.append(f"{p.replace('_verdict','')}: {r[p]}")
                if pillars:
                    print(f"    {' | '.join(pillars)}")

    elif args.command == "log-accum-distro":
        data = _parse_json_input(args.json_data)
        if not data or not data.get("token"):
            print("Error: JSON must include 'token' field", file=sys.stderr)
            sys.exit(1)
        report_id = log_accum_distro_report(
            token=data["token"],
            chain=data.get("chain"),
            token_address=data.get("token_address"),
            price_usd=data.get("price_usd"),
            layer1_verdict=data.get("layer1_verdict"),
            layer2_verdict=data.get("layer2_verdict"),
            layer3_verdict=data.get("layer3_verdict"),
            cex_net_flow_usd=data.get("cex_net_flow_usd"),
            cex_inflow_usd=data.get("cex_inflow_usd"),
            cex_outflow_usd=data.get("cex_outflow_usd"),
            cex_flow_vs_avg=data.get("cex_flow_vs_avg"),
            sm_holders_count=data.get("sm_holders_count"),
            sm_balance_usd=data.get("sm_balance_usd"),
            sm_balance_change_24h_pct=data.get("sm_balance_change_24h_pct"),
            sm_net_buy_volume_usd=data.get("sm_net_buy_volume_usd"),
            sm_buyer_count=data.get("sm_buyer_count"),
            sm_seller_count=data.get("sm_seller_count"),
            fresh_wallet_count=data.get("fresh_wallet_count"),
            fresh_wallet_max_score=data.get("fresh_wallet_max_score"),
            fresh_wallet_total_usd=data.get("fresh_wallet_total_usd"),
            final_verdict=data.get("final_verdict"),
            conviction=data.get("conviction"),
            nansen_credits_used=data.get("nansen_credits_used"),
            full_markdown=data.get("full_markdown"),
        )
        if report_id:
            print(json.dumps({"report_id": report_id, "token": data["token"], "status": "logged"}))
        else:
            print("Error: failed to log accum-distro report", file=sys.stderr)
            sys.exit(1)

    elif args.command == "log-nansen":
        data = _parse_json_input(args.json_data)
        if not data or not data.get("table") or not data.get("token") or "data" not in data:
            print("Error: JSON must include 'table', 'token', and 'data' fields", file=sys.stderr)
            sys.exit(1)
        valid_tables = ["nansen_flow_snapshots", "nansen_holder_snapshots",
                        "nansen_perp_snapshots", "nansen_quant_snapshots"]
        if data["table"] not in valid_tables:
            print(f"Error: table must be one of {valid_tables}", file=sys.stderr)
            sys.exit(1)
        row_id = log_nansen_snapshot(
            table=data["table"],
            token=data["token"],
            data=data["data"],
            tool_name=data.get("tool_name"),
            holder_segment=data.get("holder_segment"),
            lookback_period=data.get("lookback_period"),
            chain=data.get("chain"),
            label_type=data.get("label_type"),
            mode=data.get("mode"),
            source_query_id=data.get("source_query_id"),
        )
        if row_id > 0:
            print(json.dumps({"row_id": row_id, "table": data["table"],
                               "token": data["token"], "status": "stored"}))
        else:
            print("Error: failed to store Nansen snapshot", file=sys.stderr)
            sys.exit(1)

    elif args.command == "accum-distro-history":
        history = get_accum_distro_history(args.token, limit=args.limit)
        if not history:
            print(f"No accum/distro snapshots found for {args.token}")
        else:
            print(f"\n=== Accum/Distro History: {args.token} ({len(history)} reports) ===\n")
            for r in history:
                ts = r['timestamp_utc'][:16]
                fv = r.get('final_verdict', '?')
                c = r.get('conviction', '?')
                price = f"  ${r['price_usd']:,.2f}" if r.get('price_usd') else ""
                print(f"  {ts}  {fv} ({c}){price}")
                layers = []
                for lbl, key in [('CEX', 'layer1_verdict'), ('SM', 'layer2_verdict'), ('Fresh', 'layer3_verdict')]:
                    if r.get(key):
                        layers.append(f"{lbl}: {r[key]}")
                if layers:
                    print(f"    {' | '.join(layers)}")

    elif args.command == "refresh-setups":
        # Refresh OHLCV for active watchlist setups + BTC/ETH/SOL
        import subprocess
        conn = get_connection()
        rows = conn.execute(
            "SELECT DISTINCT symbol FROM signal_watchlist WHERE status = 'active'"
        ).fetchall()
        conn.close()
        symbols = list(set([r['symbol'] for r in rows] + ['BTC', 'ETH', 'SOL']))
        for sym in symbols:
            print(f"Refreshing OHLCV for {sym}...")
            subprocess.run(
                [sys.executable, str(Path(__file__).parent.parent / "analysis" / "indicators.py"),
                 "download", sym, "--timeframe", "4h"],
                capture_output=True)
        print(f"Refreshed {len(symbols)} symbols: {', '.join(symbols)}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
