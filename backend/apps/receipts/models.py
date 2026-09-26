from django.db import models
from django.conf import settings
from apps.products.models import Product
from apps.warehouses.models import Warehouse, Location

class DocumentStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    WAITING = 'WAITING', 'Waiting'
    READY = 'READY', 'Ready'
    DONE = 'DONE', 'Done'
    CANCELLED = 'CANCELLED', 'Cancelled'

class Receipt(models.Model):
    receipt_number = models.CharField(max_length=50, unique=True, db_index=True)
    supplier_name = models.CharField(max_length=150)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='receipts')
    destination_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='receipts')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.DRAFT)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.receipt_number} - {self.supplier_name} ({self.status})"


class ReceiptItem(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.product.name} on {self.receipt.receipt_number}"
