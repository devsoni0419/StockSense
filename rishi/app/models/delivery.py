from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class DeliveryOrder(Base):
    """Outgoing stock delivery order for customer shipment."""
    __tablename__ = "delivery_orders"

    id = Column(Integer, primary_key=True, index=True)
    reference_number = Column(String(50), unique=True, index=True, nullable=False)
    customer_name = Column(String(150), nullable=False)
    source_location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    # Status: draft (created), waiting (picking), ready (packed), done (validated/shipped), canceled
    status = Column(String(30), default="draft", nullable=False, index=True)
    shipping_address = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    validated_at = Column(DateTime, nullable=True)

    # Relationships
    source_location = relationship("Location")
    created_by_user = relationship("User", back_populates="deliveries")
    items = relationship("DeliveryOrderItem", back_populates="delivery_order", cascade="all, delete-orphan")


class DeliveryOrderItem(Base):
    __tablename__ = "delivery_order_items"

    id = Column(Integer, primary_key=True, index=True)
    delivery_order_id = Column(Integer, ForeignKey("delivery_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity_demand = Column(Float, nullable=False, default=1.0)
    quantity_done = Column(Float, nullable=False, default=0.0)

    # Relationships
    delivery_order = relationship("DeliveryOrder", back_populates="items")
    product = relationship("Product", back_populates="delivery_items")
