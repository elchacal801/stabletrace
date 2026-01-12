from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SupplyPoint(BaseModel):
    timestamp: datetime
    supply: float
    chain: str

class AssetSupplyResponse(BaseModel):
    asset_id: str
    symbol: str
    name: str # from dim_assets
    current_supply: float
    history: List[SupplyPoint]

class GlobalSupplyPoint(BaseModel):
    timestamp: datetime
    total_supply: float
