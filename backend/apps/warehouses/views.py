from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Warehouse, Location
from .serializers import WarehouseSerializer, LocationSerializer

class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all().order_by('name')
    serializer_class = WarehouseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code', 'address']


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all().order_by('warehouse__name', 'name')
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'code', 'warehouse__name']
    filterset_fields = ['warehouse', 'location_type']
