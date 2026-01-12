import requests
import logging
import time
from datetime import datetime
from api.db import get_db_connection

logger = logging.getLogger(__name__)

COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
# Free tier has limits (approx 10-30 calls/min). We must be gentle.

def fetch_coin_metadata(coin_ids):
    """
    Fetches metadata (images, links, current market cap rank) for a list of coins.
    """
    # CoinGecko /coins/markets endpoint is efficient for this.
    # vs_currency=usd
    # ids=comma_separated
    
    # We need to chunk this to avoid long URL errors or limits if we have many.
    # Let's do top 250 chunks.
    
    base_params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 250,
        "page": 1,
        "sparkline": "false"
    }
    
    # Filter by IDs if possible, but standard 'list all' is better for discovery?
    # Actually, we should only query for assets we already know are stablecoins (from dim_assets).
    # But for now, let's just use the 'category=stablecoins' filter if CG supports it?
    # Yes: category="stablecoins"
    
    params = base_params.copy()
    params["category"] = "stablecoins"
    
    all_coins = []
    
    try:
        while True:
            logger.info(f"Fetching CoinGecko stablecoins page {params['page']}...")
            response = requests.get(f"{COINGECKO_API_URL}/coins/markets", params=params, timeout=30)
            
            if response.status_code == 429:
                logger.warning("CoinGecko Rate Limit hit. Waiting 60s...")
                time.sleep(60)
                continue
                
            response.raise_for_status()
            data = response.json()
            
            if not data:
                break
                
            all_coins.extend(data)
            
            if len(data) < 250:
                break
                
            params["page"] += 1
            # Be polite
            time.sleep(1.5)
            
        return all_coins

    except Exception as e:
        logger.error(f"Failed to fetch from CoinGecko: {e}")
        return []

def normalize_and_save(coins):
    conn = get_db_connection()
    timestamp = datetime.now()
    
    logger.info(f"Processing {len(coins)} assets from CoinGecko...")
    
    # We primarily want to UPDATE dim_assets with images/links if matching,
    # OR insert new ones if we missed them from DefiLlama (unlikely but possible).
    # We also want to record prices as a secondary source.
    
    # 1. Update dim_assets (image_url, etc - need to add columns to schema first? 
    # The current schema doesn't have image_url. Let's add it dynamically or just ignore for now and focus on prices/ranking)
    # Actually, let's update schema to include image_url.
    
    price_rows = []
    
    # Check if column exists, if not add it (Migration Logic - Simplified)
    try:
        conn.execute("ALTER TABLE dim_assets ADD COLUMN IF NOT EXISTS image_url VARCHAR")
        conn.execute("ALTER TABLE dim_assets ADD COLUMN IF NOT EXISTS market_cap_rank INTEGER")
    except Exception as e:
        logger.warning(f"Schema migration warning: {e}")

    for coin in coins:
        cg_id = coin.get("id")
        symbol = coin.get("symbol")
        name = coin.get("name")
        image = coin.get("image")
        rank = coin.get("market_cap_rank")
        price = coin.get("current_price")
        
        # Upsert Metadata
        # We match on coingecko_id (if we have it) OR symbol (fuzzy).
        # DefiLlama ingest populated 'coingecko_id'.
        
        conn.execute("""
            UPDATE dim_assets 
            SET image_url = ?, market_cap_rank = ?, last_updated = ?
            WHERE coingecko_id = ? OR (coingecko_id IS NULL AND lower(symbol) = lower(?))
        """, [image, rank, timestamp, cg_id, symbol])
        
        # Insert Price
        if price is not None:
            # We need the asset_id to insert into fact_prices.
            # We have to fetch it first.
            row = conn.execute("SELECT asset_id FROM dim_assets WHERE coingecko_id = ? OR (coingecko_id IS NULL AND lower(symbol) = lower(?))", [cg_id, symbol]).fetchone()
            
            if row:
                asset_id = row[0]
                price_rows.append((
                    timestamp,
                    asset_id,
                    float(price),
                    "coingecko",
                    timestamp
                ))

    # Bulk Insert Prices
    if price_rows:
        conn.executemany("""
            INSERT INTO fact_prices (timestamp, asset_id, price_usd, source, ingested_at)
            VALUES (?, ?, ?, ?, ?)
        """, price_rows)
        
    conn.commit()
    conn.close()
    logger.info(f"Updated CoinGecko metadata and inserted {len(price_rows)} prices.")

def ingest_coingecko():
    data = fetch_coin_metadata([])
    if data:
        normalize_and_save(data)
