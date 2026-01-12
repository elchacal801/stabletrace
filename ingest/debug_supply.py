from api.db import get_db_connection
import pandas as pd

conn = get_db_connection(read_only=True)
print("--- Last 10 Timestamps in fact_supply ---")
df = conn.execute("""
    SELECT timestamp, COUNT(DISTINCT asset_id) as asset_count, SUM(supply) as total_supply
    FROM fact_supply
    WHERE source = 'defillama'
    GROUP BY timestamp
    ORDER BY timestamp DESC
    LIMIT 10
""").df()
print(df)

print("\n--- Assets in the latest timestamp ---")
latest_ts = df.iloc[0]['timestamp']
df_latest = conn.execute("""
    SELECT dp.symbol, fs.supply
    FROM fact_supply fs
    JOIN dim_assets dp ON fs.asset_id = dp.asset_id
    WHERE fs.timestamp = ?
    ORDER BY fs.supply DESC
""", [latest_ts]).df()
print(df_latest)
