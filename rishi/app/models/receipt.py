from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Receipt(Base):
    """Incoming stock receipt from vendor/supplier."""
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    reference_number = Column(String(50), unique=True, index=True, nullable=False)
    supplier_name = Column(String(150), nullable=False)
    destination_location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    # Status: draft, waiting, ready, done, canceled
    status = Column(String(30), default="draft", nullable=False, index=True)
    scheduled_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    validated_at = Column(DateTime, nullable=True)

    # Relationships
    destination_location = relationship("Location")
    created_by_user = relationship("User", back_populates="receipts")
    items = relationship("ReceiptItem", back_populates="receipt", cascade="all, delete-orphan")


class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity_expected = Column(Float, nullable=False, default=1.0)
    quantity_received = Column(Float, nullable=False, default=0.0)

    # Relationships
    receipt = relationship("Receipt", back_populates="items")
    product = relationship("Product", back_populates="receipt_items")
