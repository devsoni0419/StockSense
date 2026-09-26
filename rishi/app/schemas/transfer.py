from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.common import OperationStatus


class InternalTransferItemBase(BaseModel):
    product_id: int
    quantity: float = Field(..., gt=0.0)


class InternalTransferItemCreate(InternalTransferItemBase):
    pass


class InternalTransferItemResponse(InternalTransferItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transfer_id: int
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    uom: Optional[str] = None


class InternalTransferBase(BaseModel):
    source_location_id: int
    destination_location_id: int
    notes: Optional[str] = None


class InternalTransferCreate(InternalTransferBase):
    items: List[InternalTransferItemCreate] = Field(..., min_length=1)


class InternalTransferUpdate(BaseModel):
    source_location_id: Optional[int] = None
    destination_location_id: Optional[int] = None
    notes: Optional[str] = None
    status: Optional[OperationStatus] = None
    items: Optional[List[InternalTransferItemCreate]] = None


class InternalTransferResponse(InternalTransferBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_number: str
    status: OperationStatus
    created_by_user_id: Optional[int] = None
    created_by_name: Optional[str] = None
    source_location_name: Optional[str] = None
    source_warehouse_name: Optional[str] = None
    destination_location_name: Optional[str] = None
    destination_warehouse_name: Optional[str] = None
    created_at: datetime
    validated_at: Optional[datetime] = None
    items: List[InternalTransferItemResponse] = []
