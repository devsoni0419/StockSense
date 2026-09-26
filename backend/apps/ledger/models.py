from django.db import models
from django.conf import settings
from apps.products.models import Product
from apps.warehouses.models import Location

class MovementType(models.TextChoices):
    RECEIPT = 'RECEIPT', 'Receipt'
    DELIVERY = 'DELIVERY', 'Delivery Order'
    INTERNAL_TRANSFER = 'INTERNAL_TRANSFER', 'Internal Transfer'
    ADJUSTMENT = 'ADJUSTMENT', 'Inventory Adjustment'

class StockLedger(models.Model):
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    reference = models.CharField(max_length=100, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ledger_entries')
    movement_type = models.CharField(max_length=30, choices=MovementType.choices)
    source_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='outgoing_ledger')
    destination_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_ledger')
    quantity = models.IntegerField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Stock Ledger History'

    def __str__(self):
        return f"[{self.movement_type}] {self.reference} - {self.product.name}: {self.quantity}"
