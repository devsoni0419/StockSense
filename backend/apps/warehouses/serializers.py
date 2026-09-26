from rest_framework import serializers
from .models import Warehouse, Location

class LocationSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.ReadOnlyField(source='warehouse.name')
    warehouse_code = serializers.ReadOnlyField(source='warehouse.code')

    class Meta:
        model = Location
        fields = ('id', 'warehouse', 'warehouse_name', 'warehouse_code', 'name', 'code', 'location_type', 'created_at')


class WarehouseSerializer(serializers.ModelSerializer):
    locations = LocationSerializer(many=True, read_only=True)
    total_locations = serializers.SerializerMethodField()

    class Meta:
        model = Warehouse
        fields = ('id', 'name', 'code', 'address', 'is_active', 'locations', 'total_locations', 'created_at')

    def get_total_locations(self, obj):
        return obj.locations.count()
