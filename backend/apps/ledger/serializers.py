from rest_framework import serializers
from .models import StockLedger

class StockLedgerSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_sku = serializers.ReadOnlyField(source='product.sku')
    source_location_name = serializers.ReadOnlyField(source='source_location.name')
    source_warehouse_name = serializers.ReadOnlyField(source='source_location.warehouse.name')
    destination_location_name = serializers.ReadOnlyField(source='destination_location.name')
    destination_warehouse_name = serializers.ReadOnlyField(source='destination_location.warehouse.name')
    user_name = serializers.SerializerMethodField()
    movement_type_display = serializers.ReadOnlyField(source='get_movement_type_display')

    class Meta:
        model = StockLedger
        fields = (
            'id', 'date', 'reference', 'product', 'product_name', 'product_sku',
            'movement_type', 'movement_type_display',
            'source_location', 'source_location_name', 'source_warehouse_name',
            'destination_location', 'destination_location_name', 'destination_warehouse_name',
            'quantity', 'user', 'user_name', 'notes'
        )

    def get_user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return 'System'
