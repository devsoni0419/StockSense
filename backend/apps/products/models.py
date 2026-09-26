from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    UNIT_CHOICES = [
        ('units', 'Units'),
        ('pcs', 'Pieces'),
        ('kg', 'Kilograms'),
        ('meters', 'Meters'),
        ('boxes', 'Boxes'),
        ('packs', 'Packs'),
        ('liters', 'Liters'),
    ]

    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    barcode = models.CharField(max_length=100, blank=True, null=True, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    unit_of_measure = models.CharField(max_length=20, choices=UNIT_CHOICES, default='units')
    initial_stock = models.IntegerField(default=0)
    current_stock = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=10)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_low_stock(self):
        return 0 < self.current_stock <= self.reorder_level

    @property
    def is_out_of_stock(self):
        return self.current_stock <= 0

    @property
    def stock_status(self):
        if self.is_out_of_stock:
            return 'OUT_OF_STOCK'
        elif self.is_low_stock:
            return 'LOW_STOCK'
        return 'IN_STOCK'

    def __str__(self):
        return f"{self.name} ({self.sku})"
