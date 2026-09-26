from django.db import models
from django.conf import settings
from apps.products.models import Product
from apps.warehouses.models import Location
from apps.receipts.models import DocumentStatus

class InternalTransfer(models.Model):
    transfer_number = models.CharField(max_length=50, unique=True, db_index=True)
    source_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='outgoing_transfers')
    destination_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='incoming_transfers')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.DRAFT)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transfer_number} ({self.source_location.name} -> {self.destination_location.name})"


class TransferItem(models.Model):
    transfer = models.ForeignKey(InternalTransfer, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.product.name} on {self.transfer.transfer_number}"
