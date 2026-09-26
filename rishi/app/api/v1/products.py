from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.api.deps import get_db, get_current_user
from app.models.product import Product
from app.models.category import Category
from app.models.location import Location
from app.models.user import User
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    ProductDetailResponse, StockByLocation, LowStockAlertResponse
)
from app.schemas.common import ApiResponse
from app.services.stock_service import (
    increase_stock, get_product_total_stock,
    get_product_stock_by_location, get_low_stock_alerts
)

router = APIRouter(prefix="/products", tags=["Products & Stock Availability"])


@router.get("", response_model=ApiResponse[List[ProductResponse]])
def list_products(
    search: Optional[str] = Query(None, description="Search by product name or SKU"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    low_stock_only: Optional[bool] = Query(False, description="Filter items at or below reorder level"),
    out_of_stock_only: Optional[bool] = Query(False, description="Filter items with zero stock"),
    db: Session = Depends(get_db)
):
    """
    List all products with stock counts, smart search, and inventory filters.
    """
    query = db.query(Product).filter(Product.is_active == True)

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_fmt),
                Product.sku.ilike(search_fmt)
            )
        )

    products = query.order_by(Product.name.asc()).all()

    results = []
    for prod in products:
        total_stock = get_product_total_stock(db, prod.id)
        is_low = total_stock <= (prod.min_stock_level or 0.0)
        is_out = total_stock <= 0.0

        if low_stock_only and not is_low:
            continue
        if out_of_stock_only and not is_out:
            continue

        item = ProductResponse.model_validate(prod)
        item.total_stock = total_stock
        item.category_name = prod.category.name if prod.category else None
        item.is_low_stock = is_low
        item.is_out_of_stock = is_out
        results.append(item)

    return ApiResponse(
        success=True,
        message="Products retrieved successfully.",
        data=results
    )


@router.post("", response_model=ApiResponse[ProductDetailResponse], status_code=status.HTTP_201_CREATED)
def create_product(
    prod_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new product with optional initial stock and reordering rules.
    If initial stock is provided, stock is initialized and logged in the Stock Ledger.
    """
    existing_sku = db.query(Product).filter(Product.sku == prod_in.sku).first()
    if existing_sku:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU '{prod_in.sku}' already exists."
        )

    if prod_in.category_id:
        cat = db.query(Category).filter(Category.id == prod_in.category_id).first()
        if not cat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

    product = Product(
        name=prod_in.name,
        sku=prod_in.sku.upper().strip(),
        category_id=prod_in.category_id,
        uom=prod_in.uom,
        description=prod_in.description,
        cost_price=prod_in.cost_price or 0.0,
        selling_price=prod_in.selling_price or 0.0,
        min_stock_level=prod_in.min_stock_level if prod_in.min_stock_level is not None else 10.0,
        max_stock_level=prod_in.max_stock_level if prod_in.max_stock_level is not None else 100.0,
        reorder_quantity=prod_in.reorder_quantity if prod_in.reorder_quantity is not None else 50.0,
        is_active=prod_in.is_active
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # Optional initial stock provisioning
    if prod_in.initial_stock and prod_in.initial_stock > 0:
        target_location_id = prod_in.initial_location_id
        if not target_location_id:
            # Fallback to first available internal location
            first_loc = db.query(Location).filter(Location.is_active == True).first()
            if not first_loc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot initialize stock: No warehouse location found. Please create a location first."
                )
            target_location_id = first_loc.id

        increase_stock(
            db=db,
            product_id=product.id,
            location_id=target_location_id,
            quantity=prod_in.initial_stock,
            reference_number=f"INIT-{product.sku}",
            move_type="initial_stock",
            user_id=current_user.id,
            notes=f"Initial stock for product {product.name}"
        )
        db.commit()

    total_stock = get_product_total_stock(db, product.id)
    stock_breakdown = get_product_stock_by_location(db, product.id)

    res = ProductDetailResponse.model_validate(product)
    res.total_stock = total_stock
    res.category_name = product.category.name if product.category else None
    res.is_low_stock = total_stock <= (product.min_stock_level or 0.0)
    res.is_out_of_stock = total_stock <= 0.0
    res.stock_by_location = stock_breakdown

    return ApiResponse(
        success=True,
        message="Product created successfully.",
        data=res
    )


@router.get("/alerts/low-stock", response_model=ApiResponse[List[LowStockAlertResponse]])
def get_all_low_stock_alerts(db: Session = Depends(get_db)):
    """
    Retrieve all products currently below their reordering min_stock_level.
    """
    alerts = get_low_stock_alerts(db)
    return ApiResponse(
        success=True,
        message=f"Found {len(alerts)} items requiring reordering.",
        data=alerts
    )


@router.get("/{product_id}", response_model=ApiResponse[ProductDetailResponse])
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Get detailed product information including stock breakdown across all locations and warehouses.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    total_stock = get_product_total_stock(db, product.id)
    stock_breakdown = get_product_stock_by_location(db, product.id)

    res = ProductDetailResponse.model_validate(product)
    res.total_stock = total_stock
    res.category_name = product.category.name if product.category else None
    res.is_low_stock = total_stock <= (product.min_stock_level or 0.0)
    res.is_out_of_stock = total_stock <= 0.0
    res.stock_by_location = stock_breakdown

    return ApiResponse(
        success=True,
        message="Product details retrieved.",
        data=res
    )


@router.get("/{product_id}/stock", response_model=ApiResponse[List[StockByLocation]])
def get_product_stock_locations(product_id: int, db: Session = Depends(get_db)):
    """
    Get real-time stock availability per warehouse and location for a product.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    stock_breakdown = get_product_stock_by_location(db, product.id)
    return ApiResponse(
        success=True,
        message=f"Stock availability for {product.name} retrieved.",
        data=stock_breakdown
    )


@router.put("/{product_id}", response_model=ApiResponse[ProductResponse])
def update_product(
    product_id: int,
    prod_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update product information and reordering rules."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    if prod_in.sku is not None:
        new_sku = prod_in.sku.upper().strip()
        existing = db.query(Product).filter(Product.sku == new_sku, Product.id != product_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with SKU '{new_sku}' already exists."
            )
        product.sku = new_sku

    if prod_in.category_id is not None:
        cat = db.query(Category).filter(Category.id == prod_in.category_id).first()
        if not cat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
        product.category_id = prod_in.category_id

    if prod_in.name is not None:
        product.name = prod_in.name
    if prod_in.uom is not None:
        product.uom = prod_in.uom
    if prod_in.description is not None:
        product.description = prod_in.description
    if prod_in.cost_price is not None:
        product.cost_price = prod_in.cost_price
    if prod_in.selling_price is not None:
        product.selling_price = prod_in.selling_price
    if prod_in.min_stock_level is not None:
        product.min_stock_level = prod_in.min_stock_level
    if prod_in.max_stock_level is not None:
        product.max_stock_level = prod_in.max_stock_level
    if prod_in.reorder_quantity is not None:
        product.reorder_quantity = prod_in.reorder_quantity
    if prod_in.is_active is not None:
        product.is_active = prod_in.is_active

    db.commit()
    db.refresh(product)

    total_stock = get_product_total_stock(db, product.id)
    res = ProductResponse.model_validate(product)
    res.total_stock = total_stock
    res.category_name = product.category.name if product.category else None
    res.is_low_stock = total_stock <= (product.min_stock_level or 0.0)
    res.is_out_of_stock = total_stock <= 0.0

    return ApiResponse(
        success=True,
        message="Product updated successfully.",
        data=res
    )


@router.delete("/{product_id}", response_model=ApiResponse[dict])
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deactivate or delete a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    # Soft delete
    product.is_active = False
    db.commit()

    return ApiResponse(
        success=True,
        message="Product deactivated successfully.",
        data={"id": product_id}
    )
