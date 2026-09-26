from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class LocationBase(BaseModel):
    warehouse_id: int
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=50)
    location_type: str = Field("internal", description="internal, production, transit, vendor, customer, inventory_loss")
    is_active: bool = True


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    warehouse_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    location_type: Optional[str] = None
    is_active: Optional[bool] = None


class LocationResponse(LocationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    warehouse_name: Optional[str] = None
