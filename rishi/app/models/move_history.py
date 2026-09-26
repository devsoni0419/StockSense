from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class StockLedger(Base):
    """
    Stock Ledger / Move History:
    Immutable audit log recording every single stock movement across the enterprise:
    Receipts (+), Deliveries (-), Internal Transfers (from -> to), and Adjustments (+/-).
    """
    __tablename__ = "stock_ledger"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    reference_number = Column(String(50), index=True, nullable=False)
    # Movement types: receipt, delivery, internal_transfer, inventory_adjustment, initial_stock
    move_type = Column(String(50), nullable=False, index=True)
    
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    from_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    to_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    quantity = Column(Float, nullable=False)  # Transferred quantity
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    product = relationship("Product", back_populates="ledger_entries")
    from_location = relationship("Location", foreign_keys=[from_location_id])
    to_location = relationship("Location", foreign_keys=[to_location_id])
    user = relationship("User", back_populates="ledger_entries")
