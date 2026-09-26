from datetime import datetime, timezone
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.adjustment import StockAdjustment
from app.models.location import Location
from app.models.product import Product
from app.models.user import User
from app.schemas.adjustment import StockAdjustmentCreate, StockAdjustmentResponse
from app.schemas.common import ApiResponse
from app.services.stock_service import get_or_create_quant, adjust_stock

router = APIRouter(prefix="/adjustments", tags=["Operations: Inventory Adjustments"])


def _format_adjustment_response(adj: StockAdjustment) -> StockAdjustmentResponse:
    res = StockAdjustmentResponse.model_validate(adj)
    res.product_name = adj.product.name if adj.product else None
    res.product_sku = adj.product.sku if adj.product else None
    res.uom = adj.product.uom if adj.product else None
    res.location_name = adj.location.name if adj.location else None
    res.warehouse_name = adj.location.warehouse.name if adj.location and adj.location.warehouse else None
    res.created_by_name = adj.created_by_user.name if adj.created_by_user else None
    return res


@router.get("", response_model=ApiResponse[List[StockAdjustmentResponse]])
def list_adjustments(
    status_filter: Optional[str] = Query(None, alias="status", description="draft, done, canceled"),
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    location_id: Optional[int] = Query(None, description="Filter by location ID"),
    db: Session = Depends(get_db)
):
    """List stock adjustments with filters."""
    query = db.query(StockAdjustment)
    if status_filter:
        query = query.filter(StockAdjustment.status == status_filter)
    if product_id:
        query = query.filter(StockAdjustment.product_id == product_id)
    if location_id:
        query = query.filter(StockAdjustment.location_id == location_id)

    adjustments = query.order_by(StockAdjustment.created_at.desc()).all()
    return ApiResponse(
        success=True,
        message="Stock adjustments retrieved successfully.",
        data=[_format_adjustment_response(a) for a in adjustments]
    )


@router.post("", response_model=ApiResponse[StockAdjustmentResponse], status_code=status.HTTP_201_CREATED)
def create_stock_adjustment(
    adj_in: StockAdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create an inventory adjustment to reconcile recorded stock with physical count.
    If auto_validate is True, the stock is immediately reconciled and logged in the Stock Ledger.
    """
    prod = db.query(Product).filter(Product.id == adj_in.product_id).first()
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    loc = db.query(Location).filter(Location.id == adj_in.location_id).first()
    if not loc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found.")

    quant = get_or_create_quant(db, adj_in.product_id, adj_in.location_id)
    recorded_qty = quant.quantity
    diff_qty = adj_in.counted_quantity - recorded_qty

    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:4].upper()
    ref_num = f"ADJ-{date_str}-{unique_suffix}"

    adjustment = StockAdjustment(
        reference_number=ref_num,
        product_id=adj_in.product_id,
        location_id=adj_in.location_id,
        recorded_quantity=recorded_qty,
        counted_quantity=adj_in.counted_quantity,
        difference_quantity=diff_qty,
        reason=adj_in.reason,
        notes=adj_in.notes,
        status="draft",
        created_by_user_id=current_user.id
    )
    db.add(adjustment)
    db.flush()

    if adj_in.auto_validate:
        adjust_stock(
            db=db,
            product_id=adj_in.product_id,
            location_id=adj_in.location_id,
            counted_quantity=adj_in.counted_quantity,
            reference_number=ref_num,
            reason=adj_in.reason,
            user_id=current_user.id,
            notes=adj_in.notes
        )
        adjustment.status = "done"
        adjustment.validated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(adjustment)

    status_msg = "applied immediately" if adj_in.auto_validate else "saved as draft"
    return ApiResponse(
        success=True,
        message=f"Stock adjustment {adjustment.reference_number} created and {status_msg}.",
        data=_format_adjustment_response(adjustment)
    )


@router.get("/{adjustment_id}", response_model=ApiResponse[StockAdjustmentResponse])
def get_adjustment(adjustment_id: int, db: Session = Depends(get_db)):
    """Get stock adjustment details by ID."""
    adjustment = db.query(StockAdjustment).filter(StockAdjustment.id == adjustment_id).first()
    if not adjustment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock adjustment not found.")

    return ApiResponse(
        success=True,
        message="Stock adjustment retrieved.",
        data=_format_adjustment_response(adjustment)
    )


@router.post("/{adjustment_id}/validate", response_model=ApiResponse[StockAdjustmentResponse])
def validate_adjustment(
    adjustment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate draft stock adjustment:
    Reconciles product quant to counted quantity and logs delta in Stock Ledger.
    """
    adjustment = db.query(StockAdjustment).filter(StockAdjustment.id == adjustment_id).first()
    if not adjustment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock adjustment not found.")

    if adjustment.status == "done":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Adjustment is already validated.")
    if adjustment.status == "canceled":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot validate a canceled adjustment.")

    adjust_stock(
        db=db,
        product_id=adjustment.product_id,
        location_id=adjustment.location_id,
        counted_quantity=adjustment.counted_quantity,
        reference_number=adjustment.reference_number,
        reason=adjustment.reason,
        user_id=current_user.id,
        notes=adjustment.notes
    )

    adjustment.status = "done"
    adjustment.validated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(adjustment)

    return ApiResponse(
        success=True,
        message=f"Stock adjustment {adjustment.reference_number} validated and applied.",
        data=_format_adjustment_response(adjustment)
    )


@router.post("/{adjustment_id}/cancel", response_model=ApiResponse[StockAdjustmentResponse])
def cancel_adjustment(
    adjustment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a draft adjustment."""
    adjustment = db.query(StockAdjustment).filter(StockAdjustment.id == adjustment_id).first()
    if not adjustment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock adjustment not found.")

    if adjustment.status == "done":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel an already applied adjustment.")

    adjustment.status = "canceled"
    db.commit()
    db.refresh(adjustment)

    return ApiResponse(
        success=True,
        message=f"Stock adjustment {adjustment.reference_number} canceled.",
        data=_format_adjustment_response(adjustment)
    )
