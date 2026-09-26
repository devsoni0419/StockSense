from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.product import Product, StockQuant
from app.models.location import Location
from app.models.warehouse import Warehouse
from app.models.move_history import StockLedger
from app.schemas.product import StockByLocation, LowStockAlertResponse


def get_or_create_quant(db: Session, product_id: int, location_id: int) -> StockQuant:
    """Retrieve existing stock quant or initialize a new record at 0."""
    quant = db.query(StockQuant).filter(
        StockQuant.product_id == product_id,
        StockQuant.location_id == location_id
    ).first()
    
    if not quant:
        quant = StockQuant(
            product_id=product_id,
            location_id=location_id,
            quantity=0.0,
            reserved_quantity=0.0
        )
        db.add(quant)
        db.flush()
    return quant


def increase_stock(
    db: Session,
    product_id: int,
    location_id: int,
    quantity: float,
    reference_number: str,
    move_type: str = "receipt",
    user_id: Optional[int] = None,
    notes: Optional[str] = None
) -> StockQuant:
    """
    Increase product stock at a specific location and append to Stock Ledger.
    Used for incoming Receipts, Initial Stock, etc.
    """
    if quantity <= 0:
        raise ValueError("Quantity to increase must be strictly positive.")
    
    quant = get_or_create_quant(db, product_id, location_id)
    quant.quantity += quantity
    
    ledger_entry = StockLedger(
        reference_number=reference_number,
        move_type=move_type,
        product_id=product_id,
        from_location_id=None,
        to_location_id=location_id,
        quantity=quantity,
        user_id=user_id,
        notes=notes
    )
    db.add(ledger_entry)
    db.flush()
    return quant


def decrease_stock(
    db: Session,
    product_id: int,
    location_id: int,
    quantity: float,
    reference_number: str,
    move_type: str = "delivery",
    user_id: Optional[int] = None,
    notes: Optional[str] = None,
    allow_negative: bool = False
) -> StockQuant:
    """
    Decrease product stock at a specific location and append to Stock Ledger.
    Used for Delivery Orders, scrap, etc.
    """
    if quantity <= 0:
        raise ValueError("Quantity to decrease must be strictly positive.")
    
    quant = get_or_create_quant(db, product_id, location_id)
    
    if not allow_negative and quant.quantity < quantity:
        product = db.query(Product).filter(Product.id == product_id).first()
        prod_name = product.name if product else f"ID {product_id}"
        raise ValueError(
            f"Insufficient stock for '{prod_name}'. Available: {quant.quantity}, Requested: {quantity}."
        )
    
    quant.quantity -= quantity
    
    ledger_entry = StockLedger(
        reference_number=reference_number,
        move_type=move_type,
        product_id=product_id,
        from_location_id=location_id,
        to_location_id=None,
        quantity=quantity,
        user_id=user_id,
        notes=notes
    )
    db.add(ledger_entry)
    db.flush()
    return quant


def transfer_stock(
    db: Session,
    product_id: int,
    source_location_id: int,
    destination_location_id: int,
    quantity: float,
    reference_number: str,
    user_id: Optional[int] = None,
    notes: Optional[str] = None
) -> Tuple[StockQuant, StockQuant]:
    """
    Internal Transfer: Decreases source stock and increases destination stock.
    Overall company inventory remains unchanged.
    """
    if source_location_id == destination_location_id:
        raise ValueError("Source and destination locations cannot be the same.")
    if quantity <= 0:
        raise ValueError("Transfer quantity must be strictly positive.")
    
    source_quant = get_or_create_quant(db, product_id, source_location_id)
    if source_quant.quantity < quantity:
        product = db.query(Product).filter(Product.id == product_id).first()
        prod_name = product.name if product else f"ID {product_id}"
        raise ValueError(
            f"Insufficient stock for '{prod_name}' at source location. Available: {source_quant.quantity}, Requested: {quantity}."
        )
    
    dest_quant = get_or_create_quant(db, product_id, destination_location_id)
    
    source_quant.quantity -= quantity
    dest_quant.quantity += quantity
    
    ledger_entry = StockLedger(
        reference_number=reference_number,
        move_type="internal_transfer",
        product_id=product_id,
        from_location_id=source_location_id,
        to_location_id=destination_location_id,
        quantity=quantity,
        user_id=user_id,
        notes=notes
    )
    db.add(ledger_entry)
    db.flush()
    return source_quant, dest_quant


def adjust_stock(
    db: Session,
    product_id: int,
    location_id: int,
    counted_quantity: float,
    reference_number: str,
    reason: str = "Physical Count Reconciliation",
    user_id: Optional[int] = None,
    notes: Optional[str] = None
) -> Tuple[StockQuant, float]:
    """
    Reconcile recorded stock with physical count.
    Sets stock to counted_quantity and logs delta in Stock Ledger.
    """
    if counted_quantity < 0:
        raise ValueError("Counted physical quantity cannot be negative.")
    
    quant = get_or_create_quant(db, product_id, location_id)
    recorded_qty = quant.quantity
    difference = counted_quantity - recorded_qty
    
    quant.quantity = counted_quantity
    
    from_loc = location_id if difference < 0 else None
    to_loc = location_id if difference > 0 else None
    
    ledger_entry = StockLedger(
        reference_number=reference_number,
        move_type="inventory_adjustment",
        product_id=product_id,
        from_location_id=from_loc,
        to_location_id=to_loc,
        quantity=abs(difference),
        user_id=user_id,
        notes=f"Adjustment: recorded={recorded_qty}, counted={counted_quantity}, diff={difference}. Reason: {reason}. {notes or ''}".strip()
    )
    db.add(ledger_entry)
    db.flush()
    return quant, difference


def get_product_total_stock(db: Session, product_id: int) -> float:
    """Calculate aggregate stock quantity across all locations for a product."""
    total = db.query(func.coalesce(func.sum(StockQuant.quantity), 0.0)).filter(
        StockQuant.product_id == product_id
    ).scalar()
    return float(total or 0.0)


def get_product_stock_by_location(db: Session, product_id: int) -> List[StockByLocation]:
    """Return on-hand inventory per location and warehouse for a product."""
    results = (
        db.query(StockQuant, Location, Warehouse)
        .join(Location, StockQuant.location_id == Location.id)
        .join(Warehouse, Location.warehouse_id == Warehouse.id)
        .filter(StockQuant.product_id == product_id)
        .all()
    )
    
    breakdown = []
    for quant, loc, wh in results:
        breakdown.append(StockByLocation(
            location_id=loc.id,
            location_name=loc.name,
            warehouse_id=wh.id,
            warehouse_name=wh.name,
            quantity=quant.quantity,
            reserved_quantity=quant.reserved_quantity
        ))
    return breakdown


def get_low_stock_alerts(db: Session) -> List[LowStockAlertResponse]:
    """
    Evaluate all active products and return those with stock <= min_stock_level.
    """
    products = db.query(Product).filter(Product.is_active == True).all()
    alerts = []
    
    for prod in products:
        total_stock = get_product_total_stock(db, prod.id)
        min_lvl = prod.min_stock_level or 0.0
        if total_stock <= min_lvl:
            deficit = max(0.0, min_lvl - total_stock)
            alerts.append(LowStockAlertResponse(
                product_id=prod.id,
                product_name=prod.name,
                sku=prod.sku,
                category_name=prod.category.name if prod.category else None,
                current_stock=total_stock,
                min_stock_level=min_lvl,
                reorder_quantity=prod.reorder_quantity or 0.0,
                uom=prod.uom,
                deficit=deficit
            ))
    return alerts
