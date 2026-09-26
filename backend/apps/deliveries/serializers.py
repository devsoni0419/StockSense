from rest_framework import serializers
from .models import Delivery, DeliveryItem
from apps.products.serializers import ProductSerializer

class DeliveryItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_sku = serializers.ReadOnlyField(source='product.sku')

    class Meta:
        model = DeliveryItem
        fields = ('id', 'product', 'product_name', 'product_sku', 'quantity')


class DeliverySerializer(serializers.ModelSerializer):
    items = DeliveryItemSerializer(many=True)
    warehouse_name = serializers.ReadOnlyField(source='warehouse.name')
    source_location_name = serializers.ReadOnlyField(source='source_location.name')
    created_by_name = serializers.SerializerMethodField()
    status_display = serializers.ReadOnlyField(source='get_status_display')

    class Meta:
        model = Delivery
        fields = (
            'id', 'delivery_number', 'customer_name', 'warehouse', 'warehouse_name',
            'source_location', 'source_location_name', 'date', 'status',
            'status_display', 'notes', 'created_by', 'created_by_name', 'items',
            'created_at', 'updated_at'
        )

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return 'System'

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        if 'delivery_number' not in validated_data or not validated_data['delivery_number']:
            import datetime, random
            today_str = datetime.date.today().strftime('%Y%m%d')
            rand_code = random.randint(1000, 9999)
            validated_data['delivery_number'] = f"DEL-{today_str}-{rand_code}"

        delivery = Delivery.objects.create(**validated_data)
        for item in items_data:
            DeliveryItem.objects.create(delivery=delivery, **item)
        return delivery

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item in items_data:
                DeliveryItem.objects.create(delivery=instance, **item)
        return instance
