import requests
import pandas as pd
import io
import logging
import urllib.parse
from datetime import datetime
from api.db import get_db_connection

logger = logging.getLogger(__name__)

OFAC_SDN_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"

def fetch_ofac_sdn():
    logger.info("Fetching OFAC SDN List (Official)...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Connection": "keep-alive"
    }
    
    try:
        response = requests.get(OFAC_SDN_URL, headers=headers, timeout=120)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logger.error(f"Failed to fetch OFAC SDN: {e}.")
        raise e

def parse_crypto_addresses(content):
    cols = ["ent_num", "SDN_Name", "SDN_Type", "Program", "Title", "Call_Sign", 
            "Vess_type", "Tonnage", "GRT", "Vess_flag", "Vess_owner", "Remarks"]
            
    try:
        df = pd.read_csv(io.BytesIO(content), names=cols, on_bad_lines='skip', dtype=str)
    except Exception as e:
        logger.error(f"Failed to parse CSV: {e}")
        return []

    df = df.fillna("")
    crypto_df = df[df['Remarks'].str.contains("Digital Currency Address", na=False, case=False)]
    
    results = []
    
    for _, row in crypto_df.iterrows():
        remarks = row['Remarks']
        entity_name = row['SDN_Name']
        program = row['Program']
        ent_id = str(row['ent_num'])
        
        if not program or str(program).lower() == 'nan':
            program = "Unspecified"
            
        parts = remarks.split(';')
        for part in parts:
            if "Digital Currency Address" in part:
                 # Clean up "alt." artifacts and other noise
                 clean = part.replace("Digital Currency Address", "").replace("alt.", "").strip()
                 
                 if clean.startswith("-"):
                     clean = clean[1:].strip()
                 
                 subparts = clean.split()
                 if len(subparts) >= 2:
                     curr = subparts[0].upper()
                     addr = subparts[1]
                     
                     # Validation heuristic
                     if len(addr) < 10: 
                         continue

                     chain = "Unknown"
                     if curr == "XBT": chain = "Bitcoin"
                     elif curr == "ETH": chain = "Ethereum"
                     elif curr == "TRX": chain = "Tron"
                     elif curr == "LTC": chain = "Litecoin"
                     elif curr == "XMR": chain = "Monero"
                     elif curr == "USDC": chain = "Ethereum" 
                     elif curr == "USDT": chain = "Ethereum"
                     else: chain = curr
                     
                     results.append({
                         "address": addr,
                         "chain": chain,
                         "entity_id": ent_id,
                         "entity_name": entity_name,
                         "program": program,
                         "source": "OFAC SDN"
                     })
                     
    return results

def normalize_and_save(records):
    conn = get_db_connection()
    timestamp = datetime.now()
    
    logger.info(f"Ingesting {len(records)} sanctioned addresses from OFAC...")
    
    try:
        conn.execute("ALTER TABLE fact_sanctioned_addresses ADD COLUMN IF NOT EXISTS source_ref VARCHAR")
    except Exception as e:
        logger.debug(f"Column source_ref might already exist: {e}")

    conn.execute("DELETE FROM fact_sanctioned_addresses WHERE source_ref = 'OFAC SDN'")
    
    entities = {}
    for r in records:
        entities[r['entity_id']] = (r['entity_name'], r['program'])
        
    for ent_id, (name, prog) in entities.items():
        existing = conn.execute("SELECT 1 FROM dim_sanctions_entity WHERE entity_id = ?", [ent_id]).fetchone()
        if existing:
             conn.execute("UPDATE dim_sanctions_entity SET last_updated = ? WHERE entity_id = ?", [timestamp, ent_id])
        else:
             search_url = f"https://opencorporates.com/companies?q={urllib.parse.quote_plus(name)}"
             conn.execute("""
                INSERT INTO dim_sanctions_entity (entity_id, name, program, authority, source_url, last_updated, opencorporates_search_url)
                VALUES (?, ?, ?, 'OFAC', ?, ?, ?)
             """, [ent_id, name, prog, OFAC_SDN_URL, timestamp, search_url])

    rows = []
    for r in records:
        rows.append((
            r['address'],
            r['chain'],
            r['entity_id'],
            timestamp,
            1.0, 
            "OFAC SDN"
        ))
        
    if rows:
        conn.executemany("""
            INSERT INTO fact_sanctioned_addresses (address, chain, entity_id, listed_date, confidence_score, source_ref)
            VALUES (?, ?, ?, ?, ?, ?)
        """, rows)
    
    conn.commit()
    conn.close()
    logger.info("OFAC ingest complete.")

def ingest_ofac():
    content = fetch_ofac_sdn()
    if content:
        records = parse_crypto_addresses(content)
        normalize_and_save(records)
