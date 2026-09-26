from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.api.deps import get_db
from app.models.move_history import StockLedger
from app.models.product import Product
from app.schemas.move_history import StockLedgerResponse
from app.schemas.common import ApiResponse, PaginatedResponse

router = APIRouter(prefix="/move-history", tags=["Move History & Stock Ledger"])


def _format_ledger_entry(entry: StockLedger) -> StockLedgerResponse:
    res = StockLedgerResponse.model_validate(entry)
    if entry.product:
        res.product_name = entry.product.name
        res.product_sku = entry.product.sku
        res.uom = entry.product.uom
    if entry.from_location:
        res.from_location_name = entry.from_location.name
        res.from_warehouse_name = entry.from_location.warehouse.name if entry.from_location.warehouse else None
    if entry.to_location:
        res.to_location_name = entry.to_location.name
        res.to_warehouse_name = entry.to_location.warehouse.name if entry.to_location.warehouse else None
    if entry.user:
        res.user_name = entry.user.name
    return res


@router.get("", response_model=ApiResponse[PaginatedResponse[StockLedgerResponse]])
def get_move_history(
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    location_id: Optional[int] = Query(None, description="Filter by from/to location ID"),
    warehouse_id: Optional[int] = Query(None, description="Filter by warehouse ID"),
    move_type: Optional[str] = Query(None, description="receipt, delivery, internal_transfer, inventory_adjustment, initial_stock"),
    reference: Optional[str] = Query(None, description="Filter by document reference number"),
    search: Optional[str] = Query(None, description="Search in product name, SKU or reference"),
    start_date: Optional[datetime] = Query(None, description="Start date ISO"),
    end_date: Optional[datetime] = Query(None, description="End date ISO"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Search and filter the complete enterprise Stock Ledger / Move History audit trail.
    """
    query = db.query(StockLedger)

    if product_id:
        query = query.filter(StockLedger.product_id == product_id)

    if location_id:
        query = query.filter(
            or_(
                StockLedger.from_location_id == location_id,
                StockLedger.to_location_id == location_id
            )
        )

    if move_type:
        query = query.filter(StockLedger.move_type == move_type)

    if reference:
        query = query.filter(StockLedger.reference_number.ilike(f"%{reference.strip()}%"))

    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.join(Product, StockLedger.product_id == Product.id).filter(
            or_(
                Product.name.ilike(search_fmt),
                Product.sku.ilike(search_fmt),
                StockLedger.reference_number.ilike(search_fmt)
            )
        )

    if start_date:
        query = query.filter(StockLedger.timestamp >= start_date)
    if end_date:
        query = query.filter(StockLedger.timestamp <= end_date)

    total = query.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    offset = (page - 1) * page_size

    entries = query.order_by(StockLedger.timestamp.desc()).offset(offset).limit(page_size).all()
    items = [_format_ledger_entry(e) for e in entries]

    return ApiResponse(
        success=True,
        message="Stock ledger entries retrieved.",
        data=PaginatedResponse[StockLedgerResponse](
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )
