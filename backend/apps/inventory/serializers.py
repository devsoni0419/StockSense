from rest_framework import serializers
from .models import Stock

class StockSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_sku = serializers.ReadOnlyField(source='product.sku')
    unit_of_measure = serializers.ReadOnlyField(source='product.unit_of_measure')
    warehouse_id = serializers.ReadOnlyField(source='location.warehouse.id')
    warehouse_name = serializers.ReadOnlyField(source='location.warehouse.name')
    location_name = serializers.ReadOnlyField(source='location.name')

    class Meta:
        model = Stock
        fields = (
            'id', 'product', 'product_name', 'product_sku', 'unit_of_measure',
            'location', 'location_name', 'warehouse_id', 'warehouse_name',
            'quantity', 'updated_at'
        )
