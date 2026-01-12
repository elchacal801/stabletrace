import requests
import pandas as pd
import logging
from datetime import datetime
from api.db import get_db_connection

logger = logging.getLogger(__name__)

DEFILLAMA_STABLECOINS_URL = "https://stablecoins.llama.fi/stablecoins?includePrices=true"

def fetch_defillama_data():
    """
    Fetches the list of all stablecoins from DefiLlama.
    """
    try:
        response = requests.get(DEFILLAMA_STABLECOINS_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("peggedAssets", [])
    except Exception as e:
        logger.error(f"Failed to fetch data from DefiLlama: {e}")
        raise

def normalize_and_save(assets):
    """
    Normalizes the DefiLlama data and saves to DuckDB.
    Updates dim_assets and inserts into fact_supply and fact_prices.
    """
    conn = get_db_connection()
    timestamp = datetime.now()

    logger.info(f"Processing {len(assets)} assets from DefiLlama...")

    # Lists for bulk insert
    dim_rows = []
    supply_rows = []
    price_rows = []

    for asset in assets:
        # dim_asset fields
        # DefiLlama ID is usually the 'id' field, but we can store it.
        # gecko_id is 'gecko_id'
        
        asset_id = asset.get("id") # internal defillama id
        symbol = asset.get("symbol")
        name = asset.get("name")
        gecko_id = asset.get("gecko_id")
        price = asset.get("price")
        
        # We can't easily get 'decimals' or contract from this high-level endpoint easily for ALL chains.
        # But we get the break down by chain in 'chainCirculating'.
        
        dim_rows.append((
            str(asset_id),
            symbol,
            name,
            gecko_id,
            str(asset_id), # defillama_id
            "Multi", # Main chain is ambiguous for multi-chain assets, defaulting to Multi
            "stablecoin",
            timestamp
        ))

        # Fact Supply: Total Circulating
        # The API returns 'circulating' which is total. 
        # It also returns 'chainCirculating' which is a dict of chain -> amount.
        
        total_supply = asset.get("circulating")
        
        # Handle case where circulating is a dict (e.g. {'peggedUSD': 123})
        if isinstance(total_supply, dict):
            total_supply = total_supply.get("peggedUSD", 0.0)
            
        if total_supply:
            try:
                supply_float = float(total_supply)
                supply_rows.append((
                    timestamp,
                    str(asset_id),
                    "Total",
                    supply_float,
                    "defillama",
                    timestamp
                ))
            except (ValueError, TypeError):
                logger.warning(f"Could not parse supply for {symbol}: {total_supply}")

            
        # Fact Supply: Per Chain
        chain_data = asset.get("chainCirculating", {})
        for chain_name, chain_obj in chain_data.items():
            # chain_obj might be a dict with 'current' -> amount under keys like 'PeggedUSD' etc. 
            # Actually DefiLlama API structure for chainCirculating is: 
            # "chainCirculating": { "Ethereum": { "current": { "PeggedUSD": 123.4 }, ... } }
            # OR sometimes simpler. Let's handle the safe case.
            
            amount = 0.0
            if isinstance(chain_obj, dict):
                 # Try to find the circulating amount. Usually deep inside.
                 # Actually for this endpoint, let's look at a sample response logic or keep it simple.
                 # The /stablecoins endpoint returns simple chainCirculating: { "Ethereum": 100, "BSC": 50 } 
                 # wait, let me verify. The 'chainCirculating' in /stablecoins is usually straight amounts.
                 # Re-verifying structure via defensive coding:
                 pass 
            
            # For MVP, we will rely on DefiLlama's "circulating" (Total) to start.
            # And try to parse "chains" list if available to tag.
            
            # Let's inspect 'chains' list in the object which lists where it is.
            # For strict MVP supply breakdown, let's stick to Total Supply first to ensure chart works.
            # We can expand to per-chain ingestion in next iteration.

        # Fact Price
        if price:
            price_rows.append((
                timestamp,
                str(asset_id),
                float(price),
                "defillama",
                timestamp
            ))

    # Bulk Insert - Dimensions
    # DuckDB distinct upsert pattern
    # We will use valid SQL for this.
    
    # Create temp table for upsert
    conn.execute("CREATE TEMP TABLE IF NOT EXISTS staging_dim_assets AS SELECT * FROM dim_assets WHERE 1=0")
    
    # DuckDB executemany is efficient
    conn.executemany("""
        INSERT INTO dim_assets (asset_id, symbol, name, coingecko_id, defillama_id, chain, category, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (asset_id) DO UPDATE SET 
            symbol=EXCLUDED.symbol,
            name=EXCLUDED.name,
            coingecko_id=EXCLUDED.coingecko_id,
            last_updated=EXCLUDED.last_updated
    """, dim_rows)

    # Bulk Insert - Facts
    # Just append
    conn.executemany("""
        INSERT INTO fact_supply (timestamp, asset_id, chain, supply, source, ingested_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, supply_rows)

    conn.executemany("""
        INSERT INTO fact_prices (timestamp, asset_id, price_usd, source, ingested_at)
        VALUES (?, ?, ?, ?, ?)
    """, price_rows)
    
    conn.commit()
    conn.close()
    logger.info(f"Ingested {len(supply_rows)} supply records and {len(price_rows)} price records.")

def ingest_defillama():
    data = fetch_defillama_data()
    normalize_and_save(data)

def backfill_history(limit: int = 10):
    """
    Backfills historical supply data for the top N stablecoins.
    Fetches full history from DefiLlama and replaces existing fact_supply entries.
    """
    logger.info(f"Starting backfill for top {limit} assets...")
    
    # 1. Get Top Assets from DefiLlama
    data = fetch_defillama_data()
    # Sort by circulating (desc)
    # Handle None values for circulating and dicts
    def get_circ(x):
        val = x.get("circulating")
        if isinstance(val, dict):
            return val.get("peggedUSD", 0)
        return val or 0
        
    data.sort(key=get_circ, reverse=True)
    top_assets = data[:limit]
    
    conn = get_db_connection()
    try:
        for asset in top_assets:
            symbol = asset.get("symbol")
            defillama_id = asset.get("id")
            
            # Find internal asset_id
            # We assume ingestion has run at least once so dim_assets exists
            row = conn.execute("SELECT asset_id FROM dim_assets WHERE defillama_id = ?", [str(defillama_id)]).fetchone()
            if not row:
                logger.warning(f"Asset {symbol} (DL ID: {defillama_id}) not found in dim_assets. Skipping backfill.")
                continue
            
            asset_id = row[0]
            logger.info(f"Backfilling {symbol} ({asset_id})...")
            
            # Fetch History
            url = f"https://stablecoins.llama.fi/stablecoin/{defillama_id}"
            try:
                res = requests.get(url, timeout=30)
                res.raise_for_status()
                details = res.json()
            except Exception as e:
                logger.error(f"Failed to fetch history for {symbol}: {e}")
                continue
                
            history_points = details.get("tokens", [])
            supply_rows = []
            
            for point in history_points:
                ts = point.get("date") # unix timestamp
                circulating = point.get("circulating", {}).get("peggedUSD")
                
                if ts and circulating:
                    dt = datetime.fromtimestamp(ts)
                    supply_rows.append((
                        dt,
                        asset_id,
                        "Total",
                        float(circulating),
                        "defillama",
                        datetime.now()
                    ))
            
            if supply_rows:
                # DELETE existing entries for this asset to verify clean history
                conn.execute("DELETE FROM fact_supply WHERE asset_id = ? AND source = 'defillama'", [asset_id])
                
                # Bulk Insert
                conn.executemany("""
                    INSERT INTO fact_supply (timestamp, asset_id, chain, supply, source, ingested_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, supply_rows)
                
                logger.info(f"Inserted {len(supply_rows)} historical points for {symbol}.")
                
        conn.commit()
    finally:
        conn.close()
