from datetime import datetime, timezone
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.delivery import DeliveryOrder, DeliveryOrderItem
from app.models.location import Location
from app.models.product import Product
from app.models.user import User
from app.schemas.delivery import (
    DeliveryOrderCreate, DeliveryOrderUpdate,
    DeliveryOrderResponse, DeliveryOrderItemResponse
)
from app.schemas.common import ApiResponse
from app.services.stock_service import decrease_stock

router = APIRouter(prefix="/deliveries", tags=["Operations: Delivery Orders (Outgoing Goods)"])


def _format_delivery_response(order: DeliveryOrder) -> DeliveryOrderResponse:
    res = DeliveryOrderResponse.model_validate(order)
    res.source_location_name = order.source_location.name if order.source_location else None
    res.source_warehouse_name = order.source_location.warehouse.name if order.source_location and order.source_location.warehouse else None
    res.created_by_name = order.created_by_user.name if order.created_by_user else None

    items = []
    for item in order.items:
        i_res = DeliveryOrderItemResponse.model_validate(item)
        i_res.product_name = item.product.name if item.product else None
        i_res.product_sku = item.product.sku if item.product else None
        i_res.uom = item.product.uom if item.product else None
        items.append(i_res)
    res.items = items
    return res


@router.get("", response_model=ApiResponse[List[DeliveryOrderResponse]])
def list_deliveries(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (draft, waiting, ready, done, canceled)"),
    location_id: Optional[int] = Query(None, description="Filter by source location ID"),
    customer: Optional[str] = Query(None, description="Filter by customer name"),
    db: Session = Depends(get_db)
):
    """List outgoing delivery orders with dynamic filters."""
    query = db.query(DeliveryOrder)
    if status_filter:
        query = query.filter(DeliveryOrder.status == status_filter)
    if location_id:
        query = query.filter(DeliveryOrder.source_location_id == location_id)
    if customer:
        query = query.filter(DeliveryOrder.customer_name.ilike(f"%{customer}%"))

    orders = query.order_by(DeliveryOrder.created_at.desc()).all()
    return ApiResponse(
        success=True,
        message="Delivery orders retrieved successfully.",
        data=[_format_delivery_response(o) for o in orders]
    )


@router.post("", response_model=ApiResponse[DeliveryOrderResponse], status_code=status.HTTP_201_CREATED)
def create_delivery_order(
    order_in: DeliveryOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new customer delivery order."""
    location = db.query(Location).filter(Location.id == order_in.source_location_id).first()
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source location not found.")

    for it in order_in.items:
        prod = db.query(Product).filter(Product.id == it.product_id).first()
        if not prod:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product ID {it.product_id} not found.")

    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:4].upper()
    ref_num = f"DEL-{date_str}-{unique_suffix}"

    order = DeliveryOrder(
        reference_number=ref_num,
        customer_name=order_in.customer_name,
        source_location_id=order_in.source_location_id,
        shipping_address=order_in.shipping_address,
        notes=order_in.notes,
        status="draft",
        created_by_user_id=current_user.id
    )
    db.add(order)
    db.flush()

    for item_in in order_in.items:
        item = DeliveryOrderItem(
            delivery_order_id=order.id,
            product_id=item_in.product_id,
            quantity_demand=item_in.quantity_demand,
            quantity_done=item_in.quantity_done or item_in.quantity_demand
        )
        db.add(item)

    db.commit()
    db.refresh(order)

    return ApiResponse(
        success=True,
        message="Delivery order created successfully.",
        data=_format_delivery_response(order)
    )


@router.get("/{delivery_id}", response_model=ApiResponse[DeliveryOrderResponse])
def get_delivery_order(delivery_id: int, db: Session = Depends(get_db)):
    """Get delivery order details by ID."""
    order = db.query(DeliveryOrder).filter(DeliveryOrder.id == delivery_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery order not found.")

    return ApiResponse(
        success=True,
        message="Delivery order retrieved.",
        data=_format_delivery_response(order)
    )


@router.put("/{delivery_id}", response_model=ApiResponse[DeliveryOrderResponse])
def update_delivery_order(
    delivery_id: int,
    order_in: DeliveryOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update delivery order details before validation."""
    order = db.query(DeliveryOrder).filter(DeliveryOrder.id == delivery_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery order not found.")

    if order.status == "done":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot edit completed delivery orders.")

    if order_in.customer_name is not None:
        order.customer_name = order_in.customer_name
    if order_in.source_location_id is not None:
        loc = db.query(Location).filter(Location.id == order_in.source_location_id).first()
        if not loc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source location not found.")
        order.source_location_id = order_in.source_location_id
    if order_in.shipping_address is not None:
        order.shipping_address = order_in.shipping_address
    if order_in.notes is not None:
        order.notes = order_in.notes
    if order_in.status is not None:
        order.status = order_in.status.value if hasattr(order_in.status, "value") else str(order_in.status)

    if order_in.items is not None:
        db.query(DeliveryOrderItem).filter(DeliveryOrderItem.delivery_order_id == order.id).delete()
        for item_in in order_in.items:
            item = DeliveryOrderItem(
                delivery_order_id=order.id,
                product_id=item_in.product_id,
                quantity_demand=item_in.quantity_demand,
                quantity_done=item_in.quantity_done
            )
            db.add(item)

    db.commit()
    db.refresh(order)

    return ApiResponse(
        success=True,
        message="Delivery order updated successfully.",
        data=_format_delivery_response(order)
    )


@router.post("/{delivery_id}/pick", response_model=ApiResponse[DeliveryOrderResponse])
def pick_delivery_items(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Step 1 in Delivery Process: Pick items (sets status to 'waiting' / in-progress)."""
    order = db.query(DeliveryOrder).filter(DeliveryOrder.id == delivery_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery order not found.")

    if order.status in ["done", "canceled"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot pick order in status '{order.status}'.")

    order.status = "waiting"
    db.commit()
    db.refresh(order)

    return ApiResponse(
        success=True,
        message=f"Order {order.reference_number}: Items marked as picked.",
        data=_format_delivery_response(order)
    )


@router.post("/{delivery_id}/pack", response_model=ApiResponse[DeliveryOrderResponse])
def pack_delivery_items(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Step 2 in Delivery Process: Pack items (sets status to 'ready')."""
    order = db.query(DeliveryOrder).filter(DeliveryOrder.id == delivery_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery order not found.")

    if order.status in ["done", "canceled"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot pack order in status '{order.status}'.")

    order.status = "ready"
    db.commit()
    db.refresh(order)

    return ApiResponse(
        success=True,
        message=f"Order {order.reference_number}: Items packed and ready for shipment.",
        data=_format_delivery_response(order)
    )


@router.post("/{delivery_id}/validate", response_model=ApiResponse[DeliveryOrderResponse])
def validate_delivery_order(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Step 3 in Delivery Process: Validate delivery.
    Automatically reduces stock at source location and logs each entry in Stock Ledger.
    """
    order = db.query(DeliveryOrder).filter(DeliveryOrder.id == delivery_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery order not found.")

    if order.status == "done":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Delivery order is already validated.")
    if order.status == "canceled":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot validate a canceled delivery order.")

    # Deduct stock for each line item
    try:
        for item in order.items:
            qty_to_deliver = item.quantity_done if item.quantity_done > 0 else item.quantity_demand
            if item.quantity_done == 0:
                item.quantity_done = qty_to_deliver

            decrease_stock(
                db=db,
                product_id=item.product_id,
                location_id=order.source_location_id,
                quantity=qty_to_deliver,
                reference_number=order.reference_number,
                move_type="delivery",
                user_id=current_user.id,
                notes=f"Delivery to customer {order.customer_name}"
            )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    order.status = "done"
    order.validated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)

    return ApiResponse(
        success=True,
        message=f"Delivery order {order.reference_number} validated. Stock successfully deducted.",
        data=_format_delivery_response(order)
    )


@router.post("/{delivery_id}/cancel", response_model=ApiResponse[DeliveryOrderResponse])
def cancel_delivery_order(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a delivery order."""
    order = db.query(DeliveryOrder).filter(DeliveryOrder.id == delivery_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery order not found.")

    if order.status == "done":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel an already completed delivery order.")

    order.status = "canceled"
    db.commit()
    db.refresh(order)

    return ApiResponse(
        success=True,
        message=f"Delivery order {order.reference_number} canceled.",
        data=_format_delivery_response(order)
    )
