import sys
import os
import argparse
import logging
from api.db import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ingest")

def run_defillama_ingest():
    from ingest.connectors.defillama import ingest_defillama
    logger.info("Starting DefiLlama ingest...")
    ingest_defillama()
    logger.info("DefiLlama ingest complete.")

def run_pipeline(source=None):
    # Ensure DB is ready
    init_db()
    
    if source == "defillama" or source is None:
        run_defillama_ingest()
    
    if source == "coingecko" or source is None:
        from ingest.connectors.coingecko import ingest_coingecko
        logger.info("Starting CoinGecko ingest...")
        ingest_coingecko()
        logger.info("CoinGecko ingest complete.")

    if source == "sanctions" or source == "ofac" or source is None:
        from ingest.connectors.sanctions_ofac import ingest_ofac
        logger.info("Starting Sanctions (OFAC) ingest...")
        ingest_ofac()
        logger.info("Sanctions (OFAC) ingest complete.")

    if source == "sanctions" or source == "opensanctions" or source is None:
        try:
            from ingest.connectors.sanctions_opensanctions import ingest_opensanctions
            logger.info("Starting Sanctions (OpenSanctions) ingest...")
            ingest_opensanctions()
        except Exception as e:
            logger.error(f"Error during OpenSanctions ingest: {e}")
            
    # Deprecated standalone UK/UN in favor of OpenSanctions
    # if source == "uk": ...

    if source == "risk" or source == "cryptoscamdb" or source is None:
        try:
            from ingest.connectors.risk_cryptoscamdb import ingest_cryptoscamdb
            logger.info("Starting CryptoScamDB ingest...")
            ingest_cryptoscamdb()
        except Exception as e:
            logger.error(f"Error during CryptoScamDB ingest: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run StableTrace Ingest Pipeline")
    parser.add_argument("--source", type=str, help="Specific source to run (default: all)", choices=["defillama", "coingecko", "sanctions", "ofac", "opensanctions", "risk", "cryptoscamdb"])
    
    args = parser.parse_args()
    
    run_pipeline(args.source)
