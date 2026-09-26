from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class StockByLocation(BaseModel):
    location_id: int
    location_name: str
    warehouse_id: int
    warehouse_name: str
    quantity: float
    reserved_quantity: float


class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    sku: str = Field(..., min_length=2, max_length=100)
    category_id: Optional[int] = None
    uom: str = Field("Units", max_length=30)
    description: Optional[str] = None
    cost_price: Optional[float] = 0.0
    selling_price: Optional[float] = 0.0
    min_stock_level: Optional[float] = 10.0
    max_stock_level: Optional[float] = 100.0
    reorder_quantity: Optional[float] = 50.0
    is_active: bool = True


class ProductCreate(ProductBase):
    initial_stock: Optional[float] = Field(0.0, ge=0.0)
    initial_location_id: Optional[int] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    sku: Optional[str] = Field(None, min_length=2, max_length=100)
    category_id: Optional[int] = None
    uom: Optional[str] = None
    description: Optional[str] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    min_stock_level: Optional[float] = None
    max_stock_level: Optional[float] = None
    reorder_quantity: Optional[float] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    total_stock: float = 0.0
    category_name: Optional[str] = None
    is_low_stock: bool = False
    is_out_of_stock: bool = False
    created_at: datetime
    updated_at: datetime


class ProductDetailResponse(ProductResponse):
    stock_by_location: List[StockByLocation] = []


class LowStockAlertResponse(BaseModel):
    product_id: int
    product_name: str
    sku: str
    category_name: Optional[str] = None
    current_stock: float
    min_stock_level: float
    reorder_quantity: float
    uom: str
    deficit: float
