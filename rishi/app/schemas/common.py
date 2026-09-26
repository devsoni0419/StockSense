from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel
from enum import Enum

T = TypeVar("T")


class OperationStatus(str, Enum):
    DRAFT = "draft"
    WAITING = "waiting"
    READY = "ready"
    DONE = "done"
    CANCELED = "canceled"


class MovementType(str, Enum):
    RECEIPT = "receipt"
    DELIVERY = "delivery"
    INTERNAL_TRANSFER = "internal_transfer"
    INVENTORY_ADJUSTMENT = "inventory_adjustment"
    INITIAL_STOCK = "initial_stock"


class UserRole(str, Enum):
    INVENTORY_MANAGER = "inventory_manager"
    WAREHOUSE_STAFF = "warehouse_staff"
    ADMIN = "admin"


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation successful"
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
