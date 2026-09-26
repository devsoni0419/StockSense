from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.common import OperationStatus


class ReceiptItemBase(BaseModel):
    product_id: int
    quantity_expected: float = Field(..., gt=0.0)
    quantity_received: float = Field(0.0, ge=0.0)


class ReceiptItemCreate(ReceiptItemBase):
    pass


class ReceiptItemResponse(ReceiptItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    receipt_id: int
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    uom: Optional[str] = None


class ReceiptBase(BaseModel):
    supplier_name: str = Field(..., min_length=2, max_length=150)
    destination_location_id: int
    scheduled_date: Optional[datetime] = None
    notes: Optional[str] = None


class ReceiptCreate(ReceiptBase):
    items: List[ReceiptItemCreate] = Field(..., min_length=1)


class ReceiptUpdate(BaseModel):
    supplier_name: Optional[str] = Field(None, min_length=2, max_length=150)
    destination_location_id: Optional[int] = None
    scheduled_date: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[OperationStatus] = None
    items: Optional[List[ReceiptItemCreate]] = None


class ReceiptResponse(ReceiptBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_number: str
    status: OperationStatus
    created_by_user_id: Optional[int] = None
    created_by_name: Optional[str] = None
    destination_location_name: Optional[str] = None
    destination_warehouse_name: Optional[str] = None
    created_at: datetime
    validated_at: Optional[datetime] = None
    items: List[ReceiptItemResponse] = []
