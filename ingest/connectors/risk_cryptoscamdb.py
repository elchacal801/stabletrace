import requests
import logging
from datetime import datetime
from api.db import get_db_connection

logger = logging.getLogger(__name__)

# Using raw GitHub data or API. API is better if available, but raw is reliable for lists.
# CryptoScamDB API: https://api.cryptoscamdb.org/v1/addresses (Status: 502 often)
# Fallback to GitHub Raw
import requests
import yaml
import logging
import urllib.parse
from datetime import datetime
from api.db import get_db_connection

logger = logging.getLogger(__name__)

# Using raw GitHub data from the main list
CRYPTOSCAMDB_YAML_URL = "https://raw.githubusercontent.com/CryptoScamDB/blacklist/master/data/urls.yaml"

def fetch_cryptoscamdb():
    logger.info("Fetching CryptoScamDB (urls.yaml)...")
    try:
        response = requests.get(CRYPTOSCAMDB_YAML_URL, timeout=60)
        response.raise_for_status()
        # Parse YAML
        try:
            return yaml.safe_load(response.content)
        except ImportError:
            # Fallback if PyYAML not installed, though it usually is.
            # If we really lack it, we might need a manual parser or verify install.
            logger.error("PyYAML not installed. Cannot parse CryptoScamDB.")
            return []
        except Exception as e:
            logger.error(f"Failed to parse YAML: {e}")
            return []
    except Exception as e:
        logger.error(f"Failed to fetch CryptoScamDB: {e}")
        return []

def normalize_and_save(data):
    """
    Data is a list of dicts:
    - name: ...
      category: ...
      addresses:
        ETH: [0x..., 0x...]
        BTC: [1...]
    """
    conn = get_db_connection()
    timestamp = datetime.now()
    source_ref = "CryptoScamDB"
    
    if not isinstance(data, list):
         logger.warning("CryptoScamDB response was not a list.")
         return
    
    logger.info(f"Processing {len(data)} entries from CryptoScamDB...")

    # Clean up old
    conn.execute("DELETE FROM fact_sanctioned_addresses WHERE source_ref = ?", [source_ref])
    
    rows = []
    entities = {}

    for entry in data:
        name = entry.get("name", "Unknown")
        category = entry.get("category", "Scam")
        subcat = entry.get("subcategory", "")
        
        # Addresses is a dict of chain -> list of addrs
        addresses = entry.get("addresses", {})
        if not addresses:
            continue
            
        full_name = f"{name} ({subcat})" if subcat else name
        ent_id = f"CSDB-{name.replace(' ', '_').replace('.', '_')}"[:64]
        
        # Track Entity
        if ent_id not in entities:
             entities[ent_id] = (full_name, category)
             
        for chain_key, addr_list in addresses.items():
            # Normalized chain names
            chain = "Unknown"
            ck = chain_key.upper()
            if ck == "ETH": chain = "Ethereum"
            elif ck == "BTC": chain = "Bitcoin"
            elif ck == "LTC": chain = "Litecoin"
            else: chain = ck
            
            for addr in addr_list:
                rows.append((
                    addr,
                    chain,
                    ent_id,
                    timestamp,
                    0.9,
                    source_ref
                ))

    # Insert Entities
    unique_ents = list(entities.items())
    conn.execute("CREATE TEMP TABLE IF NOT EXISTS temp_csdb_ents (entity_id VARCHAR, name VARCHAR, program VARCHAR)")
    conn.executemany("INSERT INTO temp_csdb_ents VALUES (?, ?, ?)", [(k, v[0], v[1]) for k, v in unique_ents])
    
    conn.execute("""
        INSERT INTO dim_sanctions_entity (entity_id, name, program, authority, source_url, last_updated, opencorporates_search_url)
        SELECT 
            entity_id, 
            name, 
            program, 
            'CryptoScamDB', 
            'https://cryptoscamdb.org', 
            ?,
            'https://opencorporates.com/companies?q=' || replace(name, ' ', '+')
        FROM temp_csdb_ents
        WHERE entity_id NOT IN (SELECT entity_id FROM dim_sanctions_entity)
    """, [timestamp])
    
    conn.execute("DROP TABLE temp_csdb_ents")

    # Insert Addresses
    if rows:
        chunk_size = 5000
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i:i+chunk_size]
            conn.executemany("""
                INSERT INTO fact_sanctioned_addresses (address, chain, entity_id, listed_date, confidence_score, source_ref)
                VALUES (?, ?, ?, ?, ?, ?)
            """, chunk)
    
    conn.commit()
    conn.close()
    logger.info(f"CryptoScamDB ingest complete. Ingested {len(rows)} addresses.")

def ingest_cryptoscamdb():
    data = fetch_cryptoscamdb()
    if data:
        normalize_and_save(data)
