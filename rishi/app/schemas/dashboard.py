from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.schemas.common import OperationStatus, MovementType
from app.schemas.product import LowStockAlertResponse
from app.schemas.move_history import StockLedgerResponse


class DashboardKPIs(BaseModel):
    total_products: int
    total_stock_units: float
    low_stock_items_count: int
    out_of_stock_items_count: int
    pending_receipts_count: int
    pending_deliveries_count: int
    internal_transfers_scheduled_count: int
    completed_operations_count: int
    low_stock_items: List[LowStockAlertResponse] = []
    recent_movements: List[StockLedgerResponse] = []


class DashboardDocumentItem(BaseModel):
    id: int
    reference_number: str
    document_type: str  # receipt, delivery, internal_transfer, adjustment
    status: OperationStatus
    partner_or_type: Optional[str] = None  # Supplier name or Customer name or Internal
    location_name: Optional[str] = None
    warehouse_name: Optional[str] = None
    item_count: int = 0
    total_quantity: float = 0.0
    created_at: datetime
    validated_at: Optional[datetime] = None


class DashboardFilterParams(BaseModel):
    document_type: Optional[str] = None  # receipt, delivery, transfer, adjustment, all
    status: Optional[OperationStatus] = None
    warehouse_id: Optional[int] = None
    location_id: Optional[int] = None
    category_id: Optional[int] = None
    search: Optional[str] = None
    page: int = 1
    page_size: int = 20
