from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_sku = serializers.ReadOnlyField(source='product.sku')

    class Meta:
        model = Notification
        fields = ('id', 'title', 'message', 'alert_type', 'product', 'product_name', 'product_sku', 'is_read', 'created_at')
