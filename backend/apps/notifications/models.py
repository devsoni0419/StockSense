from django.db import models
from apps.products.models import Product

class NotificationType(models.TextChoices):
    LOW_STOCK = 'LOW_STOCK', 'Low Stock Alert'
    OUT_OF_STOCK = 'OUT_OF_STOCK', 'Out of Stock Alert'
    SYSTEM = 'SYSTEM', 'System Notification'

class Notification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    alert_type = models.CharField(max_length=30, choices=NotificationType.choices, default=NotificationType.LOW_STOCK)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.alert_type}] {self.title}"
