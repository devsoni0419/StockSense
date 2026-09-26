from rest_framework import serializers
from .models import InventoryAdjustment
from apps.inventory.models import Stock

class InventoryAdjustmentSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_sku = serializers.ReadOnlyField(source='product.sku')
    location_name = serializers.ReadOnlyField(source='location.name')
    warehouse_name = serializers.ReadOnlyField(source='location.warehouse.name')
    user_name = serializers.SerializerMethodField()
    reason_display = serializers.ReadOnlyField(source='get_reason_display')
    status_display = serializers.ReadOnlyField(source='get_status_display')

    class Meta:
        model = InventoryAdjustment
        fields = (
            'id', 'adjustment_number', 'product', 'product_name', 'product_sku',
            'location', 'location_name', 'warehouse_name', 'system_quantity',
            'counted_quantity', 'difference', 'reason', 'reason_display',
            'status', 'status_display', 'notes', 'user', 'user_name', 'date',
            'created_at', 'updated_at'
        )

    def get_user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return 'System'

    def create(self, validated_data):
        if 'adjustment_number' not in validated_data or not validated_data['adjustment_number']:
            import datetime, random
            today_str = datetime.date.today().strftime('%Y%m%d')
            rand_code = random.randint(1000, 9999)
            validated_data['adjustment_number'] = f"ADJ-{today_str}-{rand_code}"

        # Populate current system_quantity from Stock balance if not explicitly provided
        product = validated_data.get('product')
        location = validated_data.get('location')
        if product and location:
            stock = Stock.objects.filter(product=product, location=location).first()
            validated_data['system_quantity'] = stock.quantity if stock else 0

        return super().create(validated_data)
