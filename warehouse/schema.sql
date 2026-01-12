-- Canonical Tables

CREATE SEQUENCE IF NOT EXISTS seq_asset_id;

CREATE TABLE IF NOT EXISTS dim_assets (
    asset_id VARCHAR DEFAULT nextval('seq_asset_id'),
    symbol VARCHAR,
    name VARCHAR,
    coingecko_id VARCHAR,
    defillama_id VARCHAR,
    chain VARCHAR,
    category VARCHAR,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (asset_id)
);

CREATE TABLE IF NOT EXISTS fact_supply (
    timestamp TIMESTAMP,
    asset_id VARCHAR,
    chain VARCHAR,
    supply DOUBLE,
    source VARCHAR,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_prices (
    timestamp TIMESTAMP,
    asset_id VARCHAR,
    price_usd DOUBLE,
    source VARCHAR,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Risk / Enrichment Tables

CREATE TABLE IF NOT EXISTS fact_events (
    timestamp TIMESTAMP,
    event_type VARCHAR,
    title VARCHAR,
    summary VARCHAR,
    source VARCHAR,
    details JSON
);

CREATE TABLE IF NOT EXISTS dim_sanctions_entity (
    entity_id VARCHAR PRIMARY KEY,
    name VARCHAR,
    program VARCHAR,
    authority VARCHAR,
    source_url VARCHAR,
    last_updated TIMESTAMP,
    opencorporates_search_url VARCHAR
);

CREATE TABLE IF NOT EXISTS fact_sanctioned_addresses (
    address VARCHAR,
    chain VARCHAR,
    entity_id VARCHAR,
    listed_date TIMESTAMP,
    confidence_score DOUBLE
);
