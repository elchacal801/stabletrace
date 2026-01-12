from fastapi import APIRouter
from api.db import get_db_connection
from pydantic import BaseModel
from typing import List, Dict

router = APIRouter(prefix="/risk", tags=["risk"])

class SanctionsSummary(BaseModel):
    chain: str
    count: int

class SanctionedEntity(BaseModel):
    entity_id: str
    name: str
    program: str
    authority: str
    addresses: List[dict] # {address, chain}
    opencorporates_search_url: str = None
    source_url: str = None

@router.get("/stats")
def get_risk_stats():
    """
    Returns high-level risk statistics.
    """
    conn = get_db_connection(read_only=True)
    try:
        total_entities = conn.execute("SELECT COUNT(*) FROM dim_sanctions_entity").fetchone()[0]
        total_addresses = conn.execute("SELECT COUNT(*) FROM fact_sanctioned_addresses").fetchone()[0]
        return {
            "total_entities": total_entities,
            "total_addresses": total_addresses
        }
    finally:
        conn.close()

@router.get("/sanctions/summary", response_model=List[SanctionsSummary])
def get_sanctions_summary():
    """
    Returns count of sanctioned addresses per chain.
    """
    conn = get_db_connection(read_only=True)
    try:
        query = """
            SELECT chain, COUNT(*) as count
            FROM fact_sanctioned_addresses
            GROUP BY chain
            ORDER BY count DESC
        """
        rows = conn.execute(query).fetchall()
        return [{"chain": r[0], "count": r[1]} for r in rows]
    finally:
        conn.close()

@router.get("/filters")
def get_risk_filters():
    """
    Returns unique values for filtering (Attributes, Authorities).
    """
    conn = get_db_connection(read_only=True)
    try:
        authorities = conn.execute("SELECT DISTINCT authority FROM dim_sanctions_entity ORDER BY authority").fetchall()
        return {
            "authorities": [r[0] for r in authorities]
        }
    finally:
        conn.close()

@router.get("/sanctions/latest")
def get_latest_sanctions(limit: int = 50, offset: int = 0, search: str = None, authority: str = None):
    """
    Returns latest sanctioned entities with their addresses.
    Supports search (by name or address), filtering, and pagination.
    """
    conn = get_db_connection(read_only=True)
    try:
        params = []
        where_parts = []
        
        if search:
            search_term = f"%{search}%"
            where_parts.append("(e.name ILIKE ? OR f.address ILIKE ?)")
            params.extend([search_term, search_term])
            
        if authority:
            where_parts.append("e.authority = ?")
            params.append(authority)
            
        where_clause = ""
        if where_parts:
            where_clause = "WHERE " + " AND ".join(where_parts)
            
        # Get Total Count for Pagination
        count_query = f"""
            SELECT COUNT(*)
            FROM fact_sanctioned_addresses f
            JOIN dim_sanctions_entity e ON f.entity_id = e.entity_id
            {where_clause}
        """
        
        count_params = list(params) 
        total_count = conn.execute(count_query, count_params).fetchone()[0]

        # Now add limit/offset for the main query
        params.extend([limit, offset])

        query = f"""
            SELECT 
                e.entity_id, e.name, e.program, e.authority, e.opencorporates_search_url, e.source_url,
                f.address, f.chain, f.listed_date
            FROM fact_sanctioned_addresses f
            JOIN dim_sanctions_entity e ON f.entity_id = e.entity_id
            {where_clause}
            ORDER BY f.listed_date DESC
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(query, params).fetchall()
        
        # Group by entity
        results = {}
        for r in rows:
            eid = r[0]
            if eid not in results:
                results[eid] = {
                    "entity_id": eid,
                    "name": r[1],
                    "program": r[2],
                    "authority": r[3],
                    "opencorporates_search_url": r[4],
                    "source_url": r[5],
                    "addresses": []
                }
            results[eid]["addresses"].append({
                "address": r[6], 
                "chain": r[7],
                "date": r[8]
            })
            
        return {
            "items": list(results.values()),
            "total": total_count
        }
    finally:
        conn.close()
