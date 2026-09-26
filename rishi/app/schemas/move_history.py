from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.common import MovementType


class StockLedgerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    reference_number: str
    move_type: MovementType
    product_id: int
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    uom: Optional[str] = None
    
    from_location_id: Optional[int] = None
    from_location_name: Optional[str] = None
    from_warehouse_name: Optional[str] = None
    
    to_location_id: Optional[int] = None
    to_location_name: Optional[str] = None
    to_warehouse_name: Optional[str] = None
    
    quantity: float
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    notes: Optional[str] = None


class MoveHistoryFilter(BaseModel):
    product_id: Optional[int] = None
    location_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    move_type: Optional[MovementType] = None
    reference_number: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    page_size: int = 50
