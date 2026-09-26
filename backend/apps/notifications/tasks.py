from celery import shared_task
from django.db.models import F
from apps.products.models import Product
from .models import Notification, NotificationType
from stocksense.utils import broadcast_dashboard_update
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_low_stock_levels():
    """
    Periodic Celery task to check product stock levels against reorder levels
    and create notifications & trigger WebSocket alerts.
    """
    logger.info("Running background low stock audit task...")

    # Check Out of Stock
    out_of_stock_products = Product.objects.filter(is_archived=False, current_stock__lte=0)
    for p in out_of_stock_products:
        exists = Notification.objects.filter(
            product=p,
            alert_type=NotificationType.OUT_OF_STOCK,
            is_read=False
        ).exists()
        if not exists:
            Notification.objects.create(
                title=f"OUT OF STOCK: {p.name}",
                message=f"Product {p.name} (SKU: {p.sku}) is completely out of stock!",
                alert_type=NotificationType.OUT_OF_STOCK,
                product=p
            )
            broadcast_dashboard_update(
                update_type='OUT_OF_STOCK_ALERT',
                message=f"Product {p.name} is OUT OF STOCK!",
                data={'product_id': p.id, 'sku': p.sku}
            )

    # Check Low Stock
    low_stock_products = Product.objects.filter(
        is_archived=False,
        current_stock__gt=0,
        current_stock__lte=F('reorder_level')
    )
    for p in low_stock_products:
        exists = Notification.objects.filter(
            product=p,
            alert_type=NotificationType.LOW_STOCK,
            is_read=False
        ).exists()
        if not exists:
            Notification.objects.create(
                title=f"LOW STOCK ALERT: {p.name}",
                message=f"Product {p.name} (SKU: {p.sku}) stock ({p.current_stock}) is below reorder level ({p.reorder_level}).",
                alert_type=NotificationType.LOW_STOCK,
                product=p
            )
            broadcast_dashboard_update(
                update_type='LOW_STOCK_ALERT',
                message=f"Product {p.name} is LOW ON STOCK ({p.current_stock} remaining)",
                data={'product_id': p.id, 'sku': p.sku}
            )

    return f"Processed {out_of_stock_products.count()} out of stock and {low_stock_products.count()} low stock items."
