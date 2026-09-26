from django.db import models
from apps.products.models import Product
from apps.warehouses.models import Location

class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stocks')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='stocks')
    quantity = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'location')
        verbose_name_plural = 'Stock Balances'

    def __str__(self):
        return f"{self.product.sku} at {self.location}: {self.quantity}"
