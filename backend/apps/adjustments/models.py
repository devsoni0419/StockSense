from django.db import models
from django.conf import settings
from apps.products.models import Product
from apps.warehouses.models import Location
from apps.receipts.models import DocumentStatus

class AdjustmentReason(models.TextChoices):
    DAMAGED = 'DAMAGED', 'Damaged Goods'
    DISCREPANCY = 'DISCREPANCY', 'Physical Audit Discrepancy'
    LOST = 'LOST', 'Lost or Stolen'
    FOUND = 'FOUND', 'Found Extra Stock'
    EXPIRED = 'EXPIRED', 'Expired Stock'
    OTHER = 'OTHER', 'Other Reason'

class InventoryAdjustment(models.Model):
    adjustment_number = models.CharField(max_length=50, unique=True, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='adjustments')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='adjustments')
    system_quantity = models.IntegerField(default=0)
    counted_quantity = models.IntegerField(default=0)
    difference = models.IntegerField(default=0)
    reason = models.CharField(max_length=30, choices=AdjustmentReason.choices, default=AdjustmentReason.DISCREPANCY)
    status = models.CharField(max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.DRAFT)
    notes = models.TextField(blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        self.difference = self.counted_quantity - self.system_quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.adjustment_number} - {self.product.name} ({self.difference:+d})"
