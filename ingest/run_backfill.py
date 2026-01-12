import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ingest.connectors.defillama import backfill_history

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    print("Running backfill...")
    backfill_history(limit=15) # Top 15 slightly better coverage
    print("Done.")
