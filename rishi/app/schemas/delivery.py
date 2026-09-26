from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.common import OperationStatus


class DeliveryOrderItemBase(BaseModel):
    product_id: int
    quantity_demand: float = Field(..., gt=0.0)
    quantity_done: float = Field(0.0, ge=0.0)


class DeliveryOrderItemCreate(DeliveryOrderItemBase):
    pass


class DeliveryOrderItemResponse(DeliveryOrderItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    delivery_order_id: int
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    uom: Optional[str] = None


class DeliveryOrderBase(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=150)
    source_location_id: int
    shipping_address: Optional[str] = None
    notes: Optional[str] = None


class DeliveryOrderCreate(DeliveryOrderBase):
    items: List[DeliveryOrderItemCreate] = Field(..., min_length=1)


class DeliveryOrderUpdate(BaseModel):
    customer_name: Optional[str] = Field(None, min_length=2, max_length=150)
    source_location_id: Optional[int] = None
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[OperationStatus] = None
    items: Optional[List[DeliveryOrderItemCreate]] = None


class DeliveryOrderResponse(DeliveryOrderBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_number: str
    status: OperationStatus
    created_by_user_id: Optional[int] = None
    created_by_name: Optional[str] = None
    source_location_name: Optional[str] = None
    source_warehouse_name: Optional[str] = None
    created_at: datetime
    validated_at: Optional[datetime] = None
    items: List[DeliveryOrderItemResponse] = []
