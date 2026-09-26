from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class StockAdjustment(Base):
    """Inventory adjustment to reconcile recorded stock with physical count."""
    __tablename__ = "stock_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    reference_number = Column(String(50), unique=True, index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    recorded_quantity = Column(Float, nullable=False, default=0.0)
    counted_quantity = Column(Float, nullable=False, default=0.0)
    difference_quantity = Column(Float, nullable=False, default=0.0)  # counted - recorded
    reason = Column(String(100), default="Physical Count Reconciliation", nullable=False)  # Damaged, Theft, Audit, etc.
    # Status: draft, done, canceled
    status = Column(String(30), default="draft", nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    validated_at = Column(DateTime, nullable=True)

    # Relationships
    product = relationship("Product", back_populates="adjustments")
    location = relationship("Location")
    created_by_user = relationship("User", back_populates="adjustments")
