from django.db import models

class Warehouse(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Location(models.Model):
    LOCATION_TYPES = [
        ('STORAGE', 'Storage Rack / Shelf'),
        ('PRODUCTION', 'Production Floor'),
        ('RECEIVING', 'Receiving Dock'),
        ('SHIPPING', 'Shipping Bay'),
    ]

    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='locations')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES, default='STORAGE')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('warehouse', 'code')

    def __str__(self):
        return f"{self.warehouse.code} -> {self.name}"
