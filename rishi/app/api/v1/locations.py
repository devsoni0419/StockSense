from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.location import Location
from app.models.warehouse import Warehouse
from app.models.user import User
from app.schemas.location import LocationCreate, LocationUpdate, LocationResponse
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/locations", tags=["Locations (Settings)"])


@router.get("", response_model=ApiResponse[List[LocationResponse]])
def list_locations(
    warehouse_id: Optional[int] = Query(None, description="Filter by warehouse ID"),
    location_type: Optional[str] = Query(None, description="Filter by type (internal, production, transit, etc.)"),
    db: Session = Depends(get_db)
):
    """List storage locations with optional filtering."""
    query = db.query(Location)
    if warehouse_id:
        query = query.filter(Location.warehouse_id == warehouse_id)
    if location_type:
        query = query.filter(Location.location_type == location_type)
    
    locations = query.order_by(Location.warehouse_id.asc(), Location.name.asc()).all()
    
    results = []
    for loc in locations:
        res = LocationResponse.model_validate(loc)
        res.warehouse_name = loc.warehouse.name if loc.warehouse else None
        results.append(res)

    return ApiResponse(
        success=True,
        message="Locations retrieved successfully.",
        data=results
    )


@router.post("", response_model=ApiResponse[LocationResponse], status_code=status.HTTP_201_CREATED)
def create_location(
    loc_in: LocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new location within a warehouse."""
    warehouse = db.query(Warehouse).filter(Warehouse.id == loc_in.warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specified warehouse does not exist.")

    existing = db.query(Location).filter(
        Location.warehouse_id == loc_in.warehouse_id,
        (Location.name == loc_in.name) | (Location.code == loc_in.code)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Location with name '{loc_in.name}' or code '{loc_in.code}' already exists in this warehouse."
        )

    location = Location(
        warehouse_id=loc_in.warehouse_id,
        name=loc_in.name,
        code=loc_in.code.upper(),
        location_type=loc_in.location_type,
        is_active=loc_in.is_active
    )
    db.add(location)
    db.commit()
    db.refresh(location)

    res = LocationResponse.model_validate(location)
    res.warehouse_name = warehouse.name
    return ApiResponse(
        success=True,
        message="Location created successfully.",
        data=res
    )


@router.get("/{location_id}", response_model=ApiResponse[LocationResponse])
def get_location(location_id: int, db: Session = Depends(get_db)):
    """Get location details by ID."""
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found.")
    
    res = LocationResponse.model_validate(location)
    res.warehouse_name = location.warehouse.name if location.warehouse else None
    return ApiResponse(
        success=True,
        message="Location details retrieved.",
        data=res
    )


@router.put("/{location_id}", response_model=ApiResponse[LocationResponse])
def update_location(
    location_id: int,
    loc_in: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update location details."""
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found.")

    if loc_in.warehouse_id is not None:
        wh = db.query(Warehouse).filter(Warehouse.id == loc_in.warehouse_id).first()
        if not wh:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target warehouse does not exist.")
        location.warehouse_id = loc_in.warehouse_id

    if loc_in.name is not None:
        location.name = loc_in.name
    if loc_in.code is not None:
        location.code = loc_in.code.upper()
    if loc_in.location_type is not None:
        location.location_type = loc_in.location_type
    if loc_in.is_active is not None:
        location.is_active = loc_in.is_active

    db.commit()
    db.refresh(location)

    res = LocationResponse.model_validate(location)
    res.warehouse_name = location.warehouse.name if location.warehouse else None
    return ApiResponse(
        success=True,
        message="Location updated successfully.",
        data=res
    )


@router.delete("/{location_id}", response_model=ApiResponse[dict])
def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a location."""
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found.")

    # Check if stock exists
    has_stock = any(q.quantity > 0 for q in location.stock_quants)
    if has_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete location with remaining stock. Transfer or adjust stock to zero first."
        )

    db.delete(location)
    db.commit()
    return ApiResponse(
        success=True,
        message="Location deleted successfully.",
        data={"id": location_id}
    )
