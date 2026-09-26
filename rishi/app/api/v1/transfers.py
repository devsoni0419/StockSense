from datetime import datetime, timezone
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.transfer import InternalTransfer, InternalTransferItem
from app.models.location import Location
from app.models.product import Product
from app.models.user import User
from app.schemas.transfer import (
    InternalTransferCreate, InternalTransferUpdate,
    InternalTransferResponse, InternalTransferItemResponse
)
from app.schemas.common import ApiResponse
from app.services.stock_service import transfer_stock

router = APIRouter(prefix="/transfers", tags=["Operations: Internal Transfers"])


def _format_transfer_response(transfer: InternalTransfer) -> InternalTransferResponse:
    res = InternalTransferResponse.model_validate(transfer)
    res.source_location_name = transfer.source_location.name if transfer.source_location else None
    res.source_warehouse_name = transfer.source_location.warehouse.name if transfer.source_location and transfer.source_location.warehouse else None
    res.destination_location_name = transfer.destination_location.name if transfer.destination_location else None
    res.destination_warehouse_name = transfer.destination_location.warehouse.name if transfer.destination_location and transfer.destination_location.warehouse else None
    res.created_by_name = transfer.created_by_user.name if transfer.created_by_user else None

    items = []
    for item in transfer.items:
        i_res = InternalTransferItemResponse.model_validate(item)
        i_res.product_name = item.product.name if item.product else None
        i_res.product_sku = item.product.sku if item.product else None
        i_res.uom = item.product.uom if item.product else None
        items.append(i_res)
    res.items = items
    return res


@router.get("", response_model=ApiResponse[List[InternalTransferResponse]])
def list_transfers(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (draft, waiting, ready, done, canceled)"),
    source_location_id: Optional[int] = Query(None, description="Filter by source location ID"),
    destination_location_id: Optional[int] = Query(None, description="Filter by destination location ID"),
    db: Session = Depends(get_db)
):
    """List internal stock transfers with optional filters."""
    query = db.query(InternalTransfer)
    if status_filter:
        query = query.filter(InternalTransfer.status == status_filter)
    if source_location_id:
        query = query.filter(InternalTransfer.source_location_id == source_location_id)
    if destination_location_id:
        query = query.filter(InternalTransfer.destination_location_id == destination_location_id)

    transfers = query.order_by(InternalTransfer.created_at.desc()).all()
    return ApiResponse(
        success=True,
        message="Internal transfers retrieved successfully.",
        data=[_format_transfer_response(t) for t in transfers]
    )


@router.post("", response_model=ApiResponse[InternalTransferResponse], status_code=status.HTTP_201_CREATED)
def create_internal_transfer(
    transfer_in: InternalTransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new internal transfer request."""
    if transfer_in.source_location_id == transfer_in.destination_location_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source and destination locations cannot be identical."
        )

    src_loc = db.query(Location).filter(Location.id == transfer_in.source_location_id).first()
    if not src_loc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source location not found.")

    dest_loc = db.query(Location).filter(Location.id == transfer_in.destination_location_id).first()
    if not dest_loc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination location not found.")

    for it in transfer_in.items:
        prod = db.query(Product).filter(Product.id == it.product_id).first()
        if not prod:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product ID {it.product_id} not found.")

    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:4].upper()
    ref_num = f"INT-{date_str}-{unique_suffix}"

    transfer = InternalTransfer(
        reference_number=ref_num,
        source_location_id=transfer_in.source_location_id,
        destination_location_id=transfer_in.destination_location_id,
        notes=transfer_in.notes,
        status="draft",
        created_by_user_id=current_user.id
    )
    db.add(transfer)
    db.flush()

    for item_in in transfer_in.items:
        item = InternalTransferItem(
            transfer_id=transfer.id,
            product_id=item_in.product_id,
            quantity=item_in.quantity
        )
        db.add(item)

    db.commit()
    db.refresh(transfer)

    return ApiResponse(
        success=True,
        message="Internal transfer created successfully.",
        data=_format_transfer_response(transfer)
    )


@router.get("/{transfer_id}", response_model=ApiResponse[InternalTransferResponse])
def get_transfer(transfer_id: int, db: Session = Depends(get_db)):
    """Get internal transfer details by ID."""
    transfer = db.query(InternalTransfer).filter(InternalTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internal transfer not found.")

    return ApiResponse(
        success=True,
        message="Internal transfer retrieved.",
        data=_format_transfer_response(transfer)
    )


@router.put("/{transfer_id}", response_model=ApiResponse[InternalTransferResponse])
def update_transfer(
    transfer_id: int,
    transfer_in: InternalTransferUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update internal transfer details before validation."""
    transfer = db.query(InternalTransfer).filter(InternalTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internal transfer not found.")

    if transfer.status == "done":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot edit a completed transfer.")

    if transfer_in.source_location_id is not None:
        transfer.source_location_id = transfer_in.source_location_id
    if transfer_in.destination_location_id is not None:
        transfer.destination_location_id = transfer_in.destination_location_id
    if transfer_in.notes is not None:
        transfer.notes = transfer_in.notes
    if transfer_in.status is not None:
        transfer.status = transfer_in.status.value if hasattr(transfer_in.status, "value") else str(transfer_in.status)

    if transfer_in.items is not None:
        db.query(InternalTransferItem).filter(InternalTransferItem.transfer_id == transfer.id).delete()
        for item_in in transfer_in.items:
            item = InternalTransferItem(
                transfer_id=transfer.id,
                product_id=item_in.product_id,
                quantity=item_in.quantity
            )
            db.add(item)

    db.commit()
    db.refresh(transfer)

    return ApiResponse(
        success=True,
        message="Internal transfer updated successfully.",
        data=_format_transfer_response(transfer)
    )


@router.post("/{transfer_id}/validate", response_model=ApiResponse[InternalTransferResponse])
def validate_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate Internal Transfer:
    Transfers items from source to destination location.
    Company total stock remains unchanged, location balances update, and move is logged in Stock Ledger.
    """
    transfer = db.query(InternalTransfer).filter(InternalTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internal transfer not found.")

    if transfer.status == "done":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transfer is already validated.")
    if transfer.status == "canceled":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot validate a canceled transfer.")

    try:
        for item in transfer.items:
            transfer_stock(
                db=db,
                product_id=item.product_id,
                source_location_id=transfer.source_location_id,
                destination_location_id=transfer.destination_location_id,
                quantity=item.quantity,
                reference_number=transfer.reference_number,
                user_id=current_user.id,
                notes=f"Internal transfer: {transfer.source_location.name} -> {transfer.destination_location.name}"
            )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    transfer.status = "done"
    transfer.validated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(transfer)

    return ApiResponse(
        success=True,
        message=f"Internal transfer {transfer.reference_number} validated successfully.",
        data=_format_transfer_response(transfer)
    )


@router.post("/{transfer_id}/cancel", response_model=ApiResponse[InternalTransferResponse])
def cancel_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel an internal transfer."""
    transfer = db.query(InternalTransfer).filter(InternalTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internal transfer not found.")

    if transfer.status == "done":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel an already completed transfer.")

    transfer.status = "canceled"
    db.commit()
    db.refresh(transfer)

    return ApiResponse(
        success=True,
        message=f"Internal transfer {transfer.reference_number} canceled.",
        data=_format_transfer_response(transfer)
    )
