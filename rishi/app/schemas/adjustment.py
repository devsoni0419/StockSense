from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.common import OperationStatus


class StockAdjustmentCreate(BaseModel):
    product_id: int
    location_id: int
    counted_quantity: float = Field(..., ge=0.0)
    reason: str = Field("Physical Count Reconciliation", max_length=100)
    notes: Optional[str] = None
    auto_validate: bool = Field(True, description="Immediately apply adjustment to stock upon creation")


class StockAdjustmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_number: str
    product_id: int
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    uom: Optional[str] = None
    location_id: int
    location_name: Optional[str] = None
    warehouse_name: Optional[str] = None
    recorded_quantity: float
    counted_quantity: float
    difference_quantity: float
    reason: str
    status: OperationStatus
    notes: Optional[str] = None
    created_by_user_id: Optional[int] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    validated_at: Optional[datetime] = None
