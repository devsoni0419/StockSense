from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    uom = Column(String(30), default="Units", nullable=False)  # Unit of Measure: Units, kg, pcs, m, liters, etc.
    description = Column(Text, nullable=True)
    cost_price = Column(Float, default=0.0)
    selling_price = Column(Float, default=0.0)
    
    # Reordering rules
    min_stock_level = Column(Float, default=10.0)  # Low stock threshold
    max_stock_level = Column(Float, default=100.0)
    reorder_quantity = Column(Float, default=50.0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    category = relationship("Category", back_populates="products")
    stock_quants = relationship("StockQuant", back_populates="product", cascade="all, delete-orphan")
    receipt_items = relationship("ReceiptItem", back_populates="product")
    delivery_items = relationship("DeliveryOrderItem", back_populates="product")
    transfer_items = relationship("InternalTransferItem", back_populates="product")
    adjustments = relationship("StockAdjustment", back_populates="product")
    ledger_entries = relationship("StockLedger", back_populates="product")


class StockQuant(Base):
    """Tracks current real-time inventory quantity of a product at a specific location."""
    __tablename__ = "stock_quants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)
    quantity = Column(Float, default=0.0, nullable=False)
    reserved_quantity = Column(Float, default=0.0, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("product_id", "location_id", name="uq_product_location"),
    )

    # Relationships
    product = relationship("Product", back_populates="stock_quants")
    location = relationship("Location", back_populates="stock_quants")
