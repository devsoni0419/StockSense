from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/categories", tags=["Product Categories"])


@router.get("", response_model=ApiResponse[List[CategoryResponse]])
def list_categories(db: Session = Depends(get_db)):
    """List all product categories."""
    categories = db.query(Category).order_by(Category.name.asc()).all()
    return ApiResponse(
        success=True,
        message="Categories retrieved successfully.",
        data=[CategoryResponse.model_validate(c) for c in categories]
    )


@router.post("", response_model=ApiResponse[CategoryResponse], status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new product category."""
    existing = db.query(Category).filter(Category.name == category_in.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{category_in.name}' already exists."
        )

    category = Category(
        name=category_in.name,
        code=category_in.code,
        description=category_in.description
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    return ApiResponse(
        success=True,
        message="Category created successfully.",
        data=CategoryResponse.model_validate(category)
    )


@router.get("/{category_id}", response_model=ApiResponse[CategoryResponse])
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get category details by ID."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
    return ApiResponse(
        success=True,
        message="Category details retrieved.",
        data=CategoryResponse.model_validate(category)
    )


@router.put("/{category_id}", response_model=ApiResponse[CategoryResponse])
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a product category."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

    if category_in.name is not None:
        category.name = category_in.name
    if category_in.code is not None:
        category.code = category_in.code
    if category_in.description is not None:
        category.description = category_in.description

    db.commit()
    db.refresh(category)
    return ApiResponse(
        success=True,
        message="Category updated successfully.",
        data=CategoryResponse.model_validate(category)
    )


@router.delete("/{category_id}", response_model=ApiResponse[dict])
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a product category."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

    if category.products:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category because it contains associated products."
        )

    db.delete(category)
    db.commit()
    return ApiResponse(
        success=True,
        message="Category deleted successfully.",
        data={"id": category_id}
    )
