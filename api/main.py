from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import duckdb
from api.db import get_db_connection
from api.models.responses import GlobalSupplyPoint, AssetSupplyResponse, SupplyPoint
from typing import List
from api.routers import risk

app = FastAPI(title="StableTrace API", version="0.1.0")

app.include_router(risk.router)

# Allow CORS for Next.js local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "stabletrace-api"}

@app.get("/")
def root():
    return {
        "message": "Welcome to StableTrace API",
        "docs": "/docs",
        "endpoints": ["/health", "/supply/global", "/supply/assets"]
    }

@app.get("/supply/global", response_model=List[GlobalSupplyPoint])
def get_global_supply(days: int = 30):
    """
    Returns total stablecoin supply over time.
    """
    conn = get_db_connection(read_only=True)
    try:
        # Aggregate supply by day
        # Note: This is an approximation if we have mixed sources.
        # Assuming source='defillama' is the main one.
        query = """
            SELECT 
                date_trunc('day', timestamp) as day, 
                SUM(supply) as total_supply 
            FROM fact_supply 
            WHERE source = 'defillama'
            GROUP BY day
            ORDER BY day DESC
            LIMIT ?
        """
        # DuckDB requires a list for parameters
        rows = conn.execute(query, [days]).fetchall()
        
        results = []
        for r in rows:
            results.append(GlobalSupplyPoint(
                timestamp=r[0],
                total_supply=r[1]
            ))
        return results
    finally:
        conn.close()

@app.get("/supply/assets")
def get_top_assets(limit: int = 10):
    conn = get_db_connection(read_only=True)
    try:
        # Get latest supply for each asset
        query = """
            WITH latest AS (
                SELECT 
                    asset_id, 
                    supply, 
                    ROW_NUMBER() OVER (PARTITION BY asset_id ORDER BY timestamp DESC) as rn
                FROM fact_supply
                WHERE source = 'defillama'
            )
            SELECT 
                d.symbol, 
                d.name, 
                l.supply
            FROM latest l
            JOIN dim_assets d ON l.asset_id = d.asset_id
            WHERE l.rn = 1
            ORDER BY l.supply DESC
            LIMIT ?
        """
        rows = conn.execute(query, [limit]).fetchall()
        return [{"symbol": r[0], "name": r[1], "supply": r[2]} for r in rows]
    finally:
        conn.close()
