from rest_framework import serializers
from .models import Receipt, ReceiptItem
from apps.products.serializers import ProductSerializer

class ReceiptItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_sku = serializers.ReadOnlyField(source='product.sku')

    class Meta:
        model = ReceiptItem
        fields = ('id', 'product', 'product_name', 'product_sku', 'quantity')


class ReceiptSerializer(serializers.ModelSerializer):
    items = ReceiptItemSerializer(many=True)
    warehouse_name = serializers.ReadOnlyField(source='warehouse.name')
    destination_location_name = serializers.ReadOnlyField(source='destination_location.name')
    created_by_name = serializers.SerializerMethodField()
    status_display = serializers.ReadOnlyField(source='get_status_display')

    class Meta:
        model = Receipt
        fields = (
            'id', 'receipt_number', 'supplier_name', 'warehouse', 'warehouse_name',
            'destination_location', 'destination_location_name', 'date', 'status',
            'status_display', 'notes', 'created_by', 'created_by_name', 'items',
            'created_at', 'updated_at'
        )

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return 'System'

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        # Auto-generate receipt number if missing
        if 'receipt_number' not in validated_data or not validated_data['receipt_number']:
            import datetime, random
            today_str = datetime.date.today().strftime('%Y%m%d')
            rand_code = random.randint(1000, 9999)
            validated_data['receipt_number'] = f"REC-{today_str}-{rand_code}"

        receipt = Receipt.objects.create(**validated_data)
        for item in items_data:
            ReceiptItem.objects.create(receipt=receipt, **item)
        return receipt

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item in items_data:
                ReceiptItem.objects.create(receipt=instance, **item)
        return instance
