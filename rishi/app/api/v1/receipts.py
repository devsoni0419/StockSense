from datetime import datetime, timezone
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.receipt import Receipt, ReceiptItem
from app.models.location import Location
from app.models.product import Product
from app.models.user import User
from app.schemas.receipt import ReceiptCreate, ReceiptUpdate, ReceiptResponse, ReceiptItemResponse
from app.schemas.common import ApiResponse, OperationStatus
from app.services.stock_service import increase_stock

router = APIRouter(prefix="/receipts", tags=["Operations: Receipts (Incoming Goods)"])


def _format_receipt_response(receipt: Receipt) -> ReceiptResponse:
    res = ReceiptResponse.model_validate(receipt)
    res.destination_location_name = receipt.destination_location.name if receipt.destination_location else None
    res.destination_warehouse_name = receipt.destination_location.warehouse.name if receipt.destination_location and receipt.destination_location.warehouse else None
    res.created_by_name = receipt.created_by_user.name if receipt.created_by_user else None
    
    items = []
    for item in receipt.items:
        i_res = ReceiptItemResponse.model_validate(item)
        i_res.product_name = item.product.name if item.product else None
        i_res.product_sku = item.product.sku if item.product else None
        i_res.uom = item.product.uom if item.product else None
        items.append(i_res)
    res.items = items
    return res


@router.get("", response_model=ApiResponse[List[ReceiptResponse]])
def list_receipts(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (draft, waiting, ready, done, canceled)"),
    location_id: Optional[int] = Query(None, description="Filter by destination location ID"),
    supplier: Optional[str] = Query(None, description="Filter by supplier name"),
    db: Session = Depends(get_db)
):
    """List incoming stock receipts with dynamic filters."""
    query = db.query(Receipt)
    if status_filter:
        query = query.filter(Receipt.status == status_filter)
    if location_id:
        query = query.filter(Receipt.destination_location_id == location_id)
    if supplier:
        query = query.filter(Receipt.supplier_name.ilike(f"%{supplier}%"))

    receipts = query.order_by(Receipt.created_at.desc()).all()
    return ApiResponse(
        success=True,
        message="Receipts retrieved successfully.",
        data=[_format_receipt_response(r) for r in receipts]
    )


@router.post("", response_model=ApiResponse[ReceiptResponse], status_code=status.HTTP_201_CREATED)
def create_receipt(
    receipt_in: ReceiptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new incoming stock receipt with line items.
    """
    location = db.query(Location).filter(Location.id == receipt_in.destination_location_id).first()
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination location not found.")

    # Validate products
    for it in receipt_in.items:
        prod = db.query(Product).filter(Product.id == it.product_id).first()
        if not prod:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID {it.product_id} not found.")

    # Generate reference number e.g. REC-YYYYMMDD-XXXX
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:4].upper()
    ref_num = f"REC-{date_str}-{unique_suffix}"

    receipt = Receipt(
        reference_number=ref_num,
        supplier_name=receipt_in.supplier_name,
        destination_location_id=receipt_in.destination_location_id,
        scheduled_date=receipt_in.scheduled_date,
        notes=receipt_in.notes,
        status="draft",
        created_by_user_id=current_user.id
    )
    db.add(receipt)
    db.flush()

    for item_in in receipt_in.items:
        item = ReceiptItem(
            receipt_id=receipt.id,
            product_id=item_in.product_id,
            quantity_expected=item_in.quantity_expected,
            quantity_received=item_in.quantity_received or item_in.quantity_expected
        )
        db.add(item)

    db.commit()
    db.refresh(receipt)

    return ApiResponse(
        success=True,
        message="Receipt created successfully.",
        data=_format_receipt_response(receipt)
    )


@router.get("/{receipt_id}", response_model=ApiResponse[ReceiptResponse])
def get_receipt(receipt_id: int, db: Session = Depends(get_db)):
    """Get receipt details by ID."""
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found.")

    return ApiResponse(
        success=True,
        message="Receipt details retrieved.",
        data=_format_receipt_response(receipt)
    )


@router.put("/{receipt_id}", response_model=ApiResponse[ReceiptResponse])
def update_receipt(
    receipt_id: int,
    receipt_in: ReceiptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update draft or waiting receipt."""
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found.")

    if receipt.status == "done":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit an already validated receipt."
        )

    if receipt_in.supplier_name is not None:
        receipt.supplier_name = receipt_in.supplier_name
    if receipt_in.destination_location_id is not None:
        location = db.query(Location).filter(Location.id == receipt_in.destination_location_id).first()
        if not location:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination location not found.")
        receipt.destination_location_id = receipt_in.destination_location_id
    if receipt_in.scheduled_date is not None:
        receipt.scheduled_date = receipt_in.scheduled_date
    if receipt_in.notes is not None:
        receipt.notes = receipt_in.notes
    if receipt_in.status is not None:
        receipt.status = receipt_in.status.value if hasattr(receipt_in.status, "value") else str(receipt_in.status)

    if receipt_in.items is not None:
        # Replace items
        db.query(ReceiptItem).filter(ReceiptItem.receipt_id == receipt.id).delete()
        for item_in in receipt_in.items:
            item = ReceiptItem(
                receipt_id=receipt.id,
                product_id=item_in.product_id,
                quantity_expected=item_in.quantity_expected,
                quantity_received=item_in.quantity_received
            )
            db.add(item)

    db.commit()
    db.refresh(receipt)

    return ApiResponse(
        success=True,
        message="Receipt updated successfully.",
        data=_format_receipt_response(receipt)
    )


@router.post("/{receipt_id}/validate", response_model=ApiResponse[ReceiptResponse])
def validate_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate Receipt:
    Automatically increases product stock at destination location and logs each entry in Stock Ledger.
    """
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found.")

    if receipt.status == "done":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Receipt is already validated.")
    if receipt.status == "canceled":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot validate a canceled receipt.")

    # Process each item in the receipt
    for item in receipt.items:
        qty_to_add = item.quantity_received if item.quantity_received > 0 else item.quantity_expected
        # Update received qty if it was 0
        if item.quantity_received == 0:
            item.quantity_received = qty_to_add

        increase_stock(
            db=db,
            product_id=item.product_id,
            location_id=receipt.destination_location_id,
            quantity=qty_to_add,
            reference_number=receipt.reference_number,
            move_type="receipt",
            user_id=current_user.id,
            notes=f"Receipt from {receipt.supplier_name}"
        )

    receipt.status = "done"
    receipt.validated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(receipt)

    return ApiResponse(
        success=True,
        message=f"Receipt {receipt.reference_number} validated successfully. Stock has been incremented.",
        data=_format_receipt_response(receipt)
    )


@router.post("/{receipt_id}/cancel", response_model=ApiResponse[ReceiptResponse])
def cancel_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a draft or waiting receipt."""
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found.")

    if receipt.status == "done":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel an already completed receipt.")

    receipt.status = "canceled"
    db.commit()
    db.refresh(receipt)

    return ApiResponse(
        success=True,
        message=f"Receipt {receipt.reference_number} canceled.",
        data=_format_receipt_response(receipt)
    )
