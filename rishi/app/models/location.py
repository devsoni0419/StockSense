from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    # Type: internal (normal storage), production (production floor), transit, vendor, customer, inventory_loss
    location_type = Column(String(50), default="internal", nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    warehouse = relationship("Warehouse", back_populates="locations")
    stock_quants = relationship("StockQuant", back_populates="location", cascade="all, delete-orphan")
