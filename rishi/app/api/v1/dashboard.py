from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.deps import get_db
from app.models.product import Product, StockQuant
from app.models.receipt import Receipt
from app.models.delivery import DeliveryOrder
from app.models.transfer import InternalTransfer
from app.models.adjustment import StockAdjustment
from app.models.move_history import StockLedger
from app.models.location import Location
from app.schemas.dashboard import DashboardKPIs, DashboardDocumentItem
from app.schemas.common import ApiResponse, PaginatedResponse
from app.services.stock_service import get_low_stock_alerts, get_product_total_stock
from app.api.v1.move_history import _format_ledger_entry

router = APIRouter(prefix="/dashboard", tags=["Dashboard & KPIs"])


@router.get("/kpis", response_model=ApiResponse[DashboardKPIs])
def get_dashboard_kpis(db: Session = Depends(get_db)):
    """
    Retrieve real-time snapshot of inventory operations and KPIs.
    """
    # Total Products
    total_products = db.query(Product).filter(Product.is_active == True).count()

    # Total Units in Stock
    total_stock_units = db.query(func.coalesce(func.sum(StockQuant.quantity), 0.0)).scalar() or 0.0

    # Low Stock Alerts and Out of Stock Count
    low_stock_alerts = get_low_stock_alerts(db)
    low_stock_count = len(low_stock_alerts)
    out_of_stock_count = sum(1 for a in low_stock_alerts if a.current_stock <= 0.0)

    # Pending Operations (draft, waiting, ready)
    pending_receipts = db.query(Receipt).filter(Receipt.status.in_(["draft", "waiting", "ready"])).count()
    pending_deliveries = db.query(DeliveryOrder).filter(DeliveryOrder.status.in_(["draft", "waiting", "ready"])).count()
    internal_transfers_sched = db.query(InternalTransfer).filter(InternalTransfer.status.in_(["draft", "waiting", "ready"])).count()

    # Completed Operations
    done_receipts = db.query(Receipt).filter(Receipt.status == "done").count()
    done_deliveries = db.query(DeliveryOrder).filter(DeliveryOrder.status == "done").count()
    done_transfers = db.query(InternalTransfer).filter(InternalTransfer.status == "done").count()
    done_adjustments = db.query(StockAdjustment).filter(StockAdjustment.status == "done").count()
    completed_operations = done_receipts + done_deliveries + done_transfers + done_adjustments

    # Recent Movements from Stock Ledger
    recent_entries = db.query(StockLedger).order_by(StockLedger.timestamp.desc()).limit(10).all()
    recent_movements = [_format_ledger_entry(e) for e in recent_entries]

    kpis = DashboardKPIs(
        total_products=total_products,
        total_stock_units=float(total_stock_units),
        low_stock_items_count=low_stock_count,
        out_of_stock_items_count=out_of_stock_count,
        pending_receipts_count=pending_receipts,
        pending_deliveries_count=pending_deliveries,
        internal_transfers_scheduled_count=internal_transfers_sched,
        completed_operations_count=completed_operations,
        low_stock_items=low_stock_alerts[:10],
        recent_movements=recent_movements
    )

    return ApiResponse(
        success=True,
        message="Dashboard KPIs computed successfully.",
        data=kpis
    )


@router.get("/documents", response_model=ApiResponse[PaginatedResponse[DashboardDocumentItem]])
def list_dashboard_documents(
    document_type: Optional[str] = Query(None, description="receipt, delivery, internal, adjustment, or all"),
    status: Optional[str] = Query(None, description="draft, waiting, ready, done, canceled"),
    warehouse_id: Optional[int] = Query(None, description="Filter by warehouse ID"),
    location_id: Optional[int] = Query(None, description="Filter by location ID"),
    category_id: Optional[int] = Query(None, description="Filter by product category ID"),
    search: Optional[str] = Query(None, description="Filter by reference or party name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Unified multi-document dynamic filter API:
    - By document type: Receipts / Delivery / Internal / Adjustments
    - By status: Draft, Waiting, Ready, Done, Canceled
    - By warehouse or location
    - By product category
    """
    doc_type = (document_type or "all").lower()
    items: List[DashboardDocumentItem] = []

    # 1. Receipts
    if doc_type in ["all", "receipt", "receipts"]:
        r_query = db.query(Receipt)
        if status:
            r_query = r_query.filter(Receipt.status == status)
        if location_id:
            r_query = r_query.filter(Receipt.destination_location_id == location_id)
        if warehouse_id:
            r_query = r_query.join(Location, Receipt.destination_location_id == Location.id).filter(Location.warehouse_id == warehouse_id)
        if search:
            r_query = r_query.filter(
                (Receipt.reference_number.ilike(f"%{search}%")) |
                (Receipt.supplier_name.ilike(f"%{search}%"))
            )
        for r in r_query.all():
            # If category_id specified, check if any item matches category
            if category_id:
                has_cat = any(it.product.category_id == category_id for it in r.items if it.product)
                if not has_cat:
                    continue

            total_qty = sum(it.quantity_received if it.quantity_received > 0 else it.quantity_expected for it in r.items)
            items.append(DashboardDocumentItem(
                id=r.id,
                reference_number=r.reference_number,
                document_type="receipt",
                status=r.status,
                partner_or_type=f"Vendor: {r.supplier_name}",
                location_name=r.destination_location.name if r.destination_location else None,
                warehouse_name=r.destination_location.warehouse.name if r.destination_location and r.destination_location.warehouse else None,
                item_count=len(r.items),
                total_quantity=total_qty,
                created_at=r.created_at,
                validated_at=r.validated_at
            ))

    # 2. Deliveries
    if doc_type in ["all", "delivery", "deliveries"]:
        d_query = db.query(DeliveryOrder)
        if status:
            d_query = d_query.filter(DeliveryOrder.status == status)
        if location_id:
            d_query = d_query.filter(DeliveryOrder.source_location_id == location_id)
        if warehouse_id:
            d_query = d_query.join(Location, DeliveryOrder.source_location_id == Location.id).filter(Location.warehouse_id == warehouse_id)
        if search:
            d_query = d_query.filter(
                (DeliveryOrder.reference_number.ilike(f"%{search}%")) |
                (DeliveryOrder.customer_name.ilike(f"%{search}%"))
            )
        for d in d_query.all():
            if category_id:
                has_cat = any(it.product.category_id == category_id for it in d.items if it.product)
                if not has_cat:
                    continue

            total_qty = sum(it.quantity_done if it.quantity_done > 0 else it.quantity_demand for it in d.items)
            items.append(DashboardDocumentItem(
                id=d.id,
                reference_number=d.reference_number,
                document_type="delivery",
                status=d.status,
                partner_or_type=f"Customer: {d.customer_name}",
                location_name=d.source_location.name if d.source_location else None,
                warehouse_name=d.source_location.warehouse.name if d.source_location and d.source_location.warehouse else None,
                item_count=len(d.items),
                total_quantity=total_qty,
                created_at=d.created_at,
                validated_at=d.validated_at
            ))

    # 3. Internal Transfers
    if doc_type in ["all", "internal", "transfer", "transfers"]:
        t_query = db.query(InternalTransfer)
        if status:
            t_query = t_query.filter(InternalTransfer.status == status)
        if location_id:
            t_query = t_query.filter(
                (InternalTransfer.source_location_id == location_id) |
                (InternalTransfer.destination_location_id == location_id)
            )
        if warehouse_id:
            t_query = t_query.join(Location, InternalTransfer.source_location_id == Location.id).filter(Location.warehouse_id == warehouse_id)
        if search:
            t_query = t_query.filter(InternalTransfer.reference_number.ilike(f"%{search}%"))
        for t in t_query.all():
            if category_id:
                has_cat = any(it.product.category_id == category_id for it in t.items if it.product)
                if not has_cat:
                    continue

            total_qty = sum(it.quantity for it in t.items)
            items.append(DashboardDocumentItem(
                id=t.id,
                reference_number=t.reference_number,
                document_type="internal_transfer",
                status=t.status,
                partner_or_type=f"Transfer: {t.source_location.name} -> {t.destination_location.name}",
                location_name=f"{t.source_location.name} -> {t.destination_location.name}",
                warehouse_name=t.source_location.warehouse.name if t.source_location and t.source_location.warehouse else None,
                item_count=len(t.items),
                total_quantity=total_qty,
                created_at=t.created_at,
                validated_at=t.validated_at
            ))

    # 4. Stock Adjustments
    if doc_type in ["all", "adjustment", "adjustments"]:
        a_query = db.query(StockAdjustment)
        if status:
            a_query = a_query.filter(StockAdjustment.status == status)
        if location_id:
            a_query = a_query.filter(StockAdjustment.location_id == location_id)
        if warehouse_id:
            a_query = a_query.join(Location, StockAdjustment.location_id == Location.id).filter(Location.warehouse_id == warehouse_id)
        if search:
            a_query = a_query.filter(
                (StockAdjustment.reference_number.ilike(f"%{search}%")) |
                (StockAdjustment.reason.ilike(f"%{search}%"))
            )
        for a in a_query.all():
            if category_id and a.product and a.product.category_id != category_id:
                continue

            items.append(DashboardDocumentItem(
                id=a.id,
                reference_number=a.reference_number,
                document_type="adjustment",
                status=a.status,
                partner_or_type=f"Reason: {a.reason}",
                location_name=a.location.name if a.location else None,
                warehouse_name=a.location.warehouse.name if a.location and a.location.warehouse else None,
                item_count=1,
                total_quantity=abs(a.difference_quantity),
                created_at=a.created_at,
                validated_at=a.validated_at
            ))

    # Sort descending by creation date
    items.sort(key=lambda x: x.created_at, reverse=True)

    total_count = len(items)
    total_pages = max(1, (total_count + page_size - 1) // page_size)
    offset = (page - 1) * page_size
    paginated_items = items[offset:offset + page_size]

    return ApiResponse(
        success=True,
        message=f"Found {total_count} documents matching dynamic filter criteria.",
        data=PaginatedResponse[DashboardDocumentItem](
            items=paginated_items,
            total=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )
