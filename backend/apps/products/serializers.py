from rest_framework import serializers
from .models import Category, Product

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'created_at', 'product_count')

    def get_product_count(self, obj):
        return obj.products.filter(is_archived=False).count()


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    stock_status = serializers.ReadOnlyField()
    location_stocks = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'sku', 'barcode', 'category', 'category_name',
            'unit_of_measure', 'initial_stock', 'current_stock', 'reorder_level',
            'is_archived', 'stock_status', 'location_stocks', 'created_at', 'updated_at'
        )

    def get_location_stocks(self, obj):
        # Dynamically import Stock to avoid circular dependency
        from apps.inventory.models import Stock
        stocks = Stock.objects.filter(product=obj, quantity__gt=0).select_related('location', 'location__warehouse')
        return [
            {
                'stock_id': s.id,
                'warehouse_id': s.location.warehouse.id,
                'warehouse_name': s.location.warehouse.name,
                'location_id': s.location.id,
                'location_name': s.location.name,
                'quantity': s.quantity
            }
            for s in stocks
        ]
