import requests
import json
import logging
import urllib.parse
from datetime import datetime
from api.db import get_db_connection

logger = logging.getLogger(__name__)

# Filtered dataset (Sanctions only, no PEPs)
OPENSANCTIONS_URL = "https://data.opensanctions.org/datasets/latest/sanctions/entities.ftm.json"

def fetch_and_load_opensanctions():
    conn = get_db_connection()
    timestamp = datetime.now()
    
    logger.info("Starting OpenSanctions ingest (Stream -> Staging)...")
    
    # 1. Create Staging Tables
    conn.execute("CREATE OR REPLACE TEMP TABLE stg_os_entities (id VARCHAR, name VARCHAR, authority VARCHAR, last_change TIMESTAMP)")
    conn.execute("CREATE OR REPLACE TEMP TABLE stg_os_wallets (address VARCHAR, currency VARCHAR, holder_id VARCHAR)")
    
    # 2. Stream and Buffer
    # We'll batch inserts for performance
    entity_batch = []
    wallet_batch = []
    batch_size = 5000
    
    try:
        with requests.get(OPENSANCTIONS_URL, stream=True, timeout=120) as r:
            r.raise_for_status()
            
            for line in r.iter_lines():
                if not line: continue
                try:
                    data = json.loads(line)
                    schema = data.get("schema")
                    props = data.get("properties", {})
                    
                    ent_id = data.get("id")
                    
                    # EXTRACT ENTITY DATA
                    # We store basically everyone just in case they are a holder
                    # Metadata: Name
                    name = data.get("caption") or props.get("name", [None])[0]
                    if not name and "name" in props:
                         name = props["name"][0]
                    
                    # Authority: extracted from 'datasets'
                    # data['datasets'] is a list like ['us_ofac_sdn', 'sanctions']
                    # We pick the most specific one that isn't 'sanctions' or 'default'
                    datasets = data.get("datasets", [])
                    authority = "OpenSanctions"
                    for d in datasets:
                        if d not in ["sanctions", "default", "openanctions"]:
                            authority = d
                            break
                    
                    last_change = data.get("last_change")
                    
                    if schema in ["Person", "Company", "Organization", "LegalEntity", "Vessel", "Aircraft"]:
                        entity_batch.append((ent_id, name, authority, last_change))
                    
                    # EXTRACT WALLET DATA
                    if schema == "CryptoWallet":
                        # address mapping
                        public_keys = props.get("publicKey", [])
                        currencies = props.get("currency", [])
                        holders = props.get("holder", [])
                        
                        # Flatten: 1 wallet entity might have multiple keys/currencies (rare)
                        # usually 1:1, but holder might be multiple
                        
                        for pk in public_keys:
                            curr = currencies[0] if currencies else "Unknown"
                            
                            if not holders:
                                # Orphan wallet? Skip or log?
                                # Sometimes mapped via opposite edge? 
                                # For now, skip if no holder (can't link to sanction)
                                continue
                                
                            for holder in holders:
                                wallet_batch.append((pk, curr, holder))
                                
                    # Flush Batches
                    if len(entity_batch) >= batch_size:
                        conn.executemany("INSERT INTO stg_os_entities VALUES (?, ?, ?, ?)", entity_batch)
                        entity_batch = []
                        
                    if len(wallet_batch) >= batch_size:
                        conn.executemany("INSERT INTO stg_os_wallets VALUES (?, ?, ?)", wallet_batch)
                        wallet_batch = []
                        
                except Exception as e:
                    # Malformed line?
                    continue
                    
        # Flush remaining
        if entity_batch:
            conn.executemany("INSERT INTO stg_os_entities VALUES (?, ?, ?, ?)", entity_batch)
        if wallet_batch:
            conn.executemany("INSERT INTO stg_os_wallets VALUES (?, ?, ?)", wallet_batch)
            
        logger.info("Staging complete. Normalizing to final tables...")
        
        # 3. Normalize to Final Tables
        
        # We only care about entities that ARE holders of a wallet
        # JOIN stg_os_wallets -> stg_os_entities
        
        # Insert/Update Authorities (Entities)
        # Note: We prefix IDs with 'OS-' to avoid collision with OFAC- (though OFAC IDs are usually integers)
        # Actually OpenSanctions IDs are unique strings. We can use them directly or prefix.
        # Let's prefix for safety: "OS-<id>"
        
        # Update/Insert Dim Entities
        # We construct the OC Search URL
        conn.execute("""
            INSERT INTO dim_sanctions_entity (entity_id, name, program, authority, source_url, last_updated, opencorporates_search_url)
            SELECT DISTINCT 
                'OS-' || e.id, 
                e.name, 
                'OpenSanctions Consolidated', 
                e.authority, 
                'https://opensanctions.org/entities/' || e.id, 
                CAST(e.last_change as TIMESTAMP),
                'https://opencorporates.com/companies?q=' || replace(e.name, ' ', '+')
            FROM stg_os_entities e
            JOIN stg_os_wallets w ON e.id = w.holder_id
            WHERE 'OS-' || e.id NOT IN (SELECT entity_id FROM dim_sanctions_entity)
        """)
        
        # Insert Facts (Addresses)
        # Filter duplicates based on address+chain? 
        # Or simple clear and reload for this source?
        # OpenSanctions is aggressive, might duplicate OFAC.
        # IF we use this, we might want to DISABLE the standalone 'sanctions_ofac' connector 
        # OR handle duplicates.
        # Strategy: distinct source_ref = 'OpenSanctions'.
        
        count_before = conn.execute("SELECT count(*) FROM fact_sanctioned_addresses WHERE source_ref = 'OpenSanctions'").fetchone()[0]
        conn.execute("DELETE FROM fact_sanctioned_addresses WHERE source_ref = 'OpenSanctions'")
        
        conn.execute(f"""
            INSERT INTO fact_sanctioned_addresses (address, chain, entity_id, listed_date, confidence_score, source_ref)
            SELECT DISTINCT
                w.address,
                w.currency,
                'OS-' || w.holder_id,
                '{timestamp}'::TIMESTAMP,
                1.0,
                'OpenSanctions'
            FROM stg_os_wallets w
            JOIN stg_os_entities e ON w.holder_id = e.id
        """)
        
        count_after = conn.execute("SELECT count(*) FROM fact_sanctioned_addresses WHERE source_ref = 'OpenSanctions'").fetchone()[0]
        
        logger.info(f"OpenSanctions Import Summary: {count_after} addresses (Prev: {count_before}).")
        
        # Cleanup
        conn.execute("DROP TABLE stg_os_entities")
        conn.execute("DROP TABLE stg_os_wallets")
        
        conn.commit()
        conn.close()

    except Exception as e:
        logger.error(f"OpenSanctions Ingest Failed: {e}")
        # Ensure cleanup
        try:
            conn = get_db_connection()
            conn.execute("DROP TABLE IF EXISTS stg_os_entities")
            conn.execute("DROP TABLE IF EXISTS stg_os_wallets")
            conn.close()
        except:
            pass
        raise e

def ingest_opensanctions():
    fetch_and_load_opensanctions()
