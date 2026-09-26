from rest_framework import serializers
from .models import InternalTransfer, TransferItem

class TransferItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_sku = serializers.ReadOnlyField(source='product.sku')

    class Meta:
        model = TransferItem
        fields = ('id', 'product', 'product_name', 'product_sku', 'quantity')


class InternalTransferSerializer(serializers.ModelSerializer):
    items = TransferItemSerializer(many=True)
    source_location_name = serializers.ReadOnlyField(source='source_location.name')
    source_warehouse_name = serializers.ReadOnlyField(source='source_location.warehouse.name')
    destination_location_name = serializers.ReadOnlyField(source='destination_location.name')
    destination_warehouse_name = serializers.ReadOnlyField(source='destination_location.warehouse.name')
    created_by_name = serializers.SerializerMethodField()
    status_display = serializers.ReadOnlyField(source='get_status_display')

    class Meta:
        model = InternalTransfer
        fields = (
            'id', 'transfer_number', 'source_location', 'source_location_name', 'source_warehouse_name',
            'destination_location', 'destination_location_name', 'destination_warehouse_name',
            'date', 'status', 'status_display', 'notes', 'created_by', 'created_by_name',
            'items', 'created_at', 'updated_at'
        )

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return 'System'

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        if 'transfer_number' not in validated_data or not validated_data['transfer_number']:
            import datetime, random
            today_str = datetime.date.today().strftime('%Y%m%d')
            rand_code = random.randint(1000, 9999)
            validated_data['transfer_number'] = f"TRF-{today_str}-{rand_code}"

        transfer = InternalTransfer.objects.create(**validated_data)
        for item in items_data:
            TransferItem.objects.create(transfer=transfer, **item)
        return transfer

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item in items_data:
                TransferItem.objects.create(transfer=instance, **item)
        return instance
