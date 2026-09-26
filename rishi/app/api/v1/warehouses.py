from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.warehouse import Warehouse
from app.models.user import User
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate, WarehouseResponse
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/warehouses", tags=["Warehouses (Settings)"])


@router.get("", response_model=ApiResponse[List[WarehouseResponse]])
def list_warehouses(db: Session = Depends(get_db)):
    """List all warehouses with location counts."""
    warehouses = db.query(Warehouse).order_by(Warehouse.name.asc()).all()
    results = []
    for wh in warehouses:
        res = WarehouseResponse.model_validate(wh)
        res.location_count = len(wh.locations)
        results.append(res)
    
    return ApiResponse(
        success=True,
        message="Warehouses retrieved successfully.",
        data=results
    )


@router.post("", response_model=ApiResponse[WarehouseResponse], status_code=status.HTTP_201_CREATED)
def create_warehouse(
    wh_in: WarehouseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new warehouse."""
    existing = db.query(Warehouse).filter(
        (Warehouse.code == wh_in.code) | (Warehouse.name == wh_in.name)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Warehouse with name '{wh_in.name}' or code '{wh_in.code}' already exists."
        )

    warehouse = Warehouse(
        name=wh_in.name,
        code=wh_in.code.upper(),
        address=wh_in.address,
        city=wh_in.city,
        is_active=wh_in.is_active
    )
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)

    return ApiResponse(
        success=True,
        message="Warehouse created successfully.",
        data=WarehouseResponse.model_validate(warehouse)
    )


@router.get("/{warehouse_id}", response_model=ApiResponse[WarehouseResponse])
def get_warehouse(warehouse_id: int, db: Session = Depends(get_db)):
    """Get warehouse details by ID."""
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found.")
    
    res = WarehouseResponse.model_validate(warehouse)
    res.location_count = len(warehouse.locations)
    return ApiResponse(
        success=True,
        message="Warehouse details retrieved.",
        data=res
    )


@router.put("/{warehouse_id}", response_model=ApiResponse[WarehouseResponse])
def update_warehouse(
    warehouse_id: int,
    wh_in: WarehouseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update warehouse details."""
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found.")

    if wh_in.name is not None:
        warehouse.name = wh_in.name
    if wh_in.code is not None:
        warehouse.code = wh_in.code.upper()
    if wh_in.address is not None:
        warehouse.address = wh_in.address
    if wh_in.city is not None:
        warehouse.city = wh_in.city
    if wh_in.is_active is not None:
        warehouse.is_active = wh_in.is_active

    db.commit()
    db.refresh(warehouse)
    res = WarehouseResponse.model_validate(warehouse)
    res.location_count = len(warehouse.locations)
    return ApiResponse(
        success=True,
        message="Warehouse updated successfully.",
        data=res
    )


@router.delete("/{warehouse_id}", response_model=ApiResponse[dict])
def delete_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a warehouse."""
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found.")

    if warehouse.locations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete warehouse with existing locations. Delete or reassign locations first."
        )

    db.delete(warehouse)
    db.commit()
    return ApiResponse(
        success=True,
        message="Warehouse deleted successfully.",
        data={"id": warehouse_id}
    )
