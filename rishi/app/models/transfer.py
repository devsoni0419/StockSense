from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class InternalTransfer(Base):
    """Internal stock movement between locations or warehouses."""
    __tablename__ = "internal_transfers"

    id = Column(Integer, primary_key=True, index=True)
    reference_number = Column(String(50), unique=True, index=True, nullable=False)
    source_location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    destination_location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    # Status: draft, waiting, ready, done, canceled
    status = Column(String(30), default="draft", nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    validated_at = Column(DateTime, nullable=True)

    # Relationships
    source_location = relationship("Location", foreign_keys=[source_location_id])
    destination_location = relationship("Location", foreign_keys=[destination_location_id])
    created_by_user = relationship("User", back_populates="transfers")
    items = relationship("InternalTransferItem", back_populates="transfer", cascade="all, delete-orphan")


class InternalTransferItem(Base):
    __tablename__ = "internal_transfer_items"

    id = Column(Integer, primary_key=True, index=True)
    transfer_id = Column(Integer, ForeignKey("internal_transfers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)

    # Relationships
    transfer = relationship("InternalTransfer", back_populates="items")
    product = relationship("Product", back_populates="transfer_items")
