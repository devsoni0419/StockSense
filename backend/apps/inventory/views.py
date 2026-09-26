from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Stock
from .serializers import StockSerializer

class StockViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Stock.objects.all().select_related('product', 'location', 'location__warehouse').order_by('product__name')
    serializer_class = StockSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['product__name', 'product__sku', 'location__name', 'location__warehouse__name']
    filterset_fields = ['product', 'location', 'location__warehouse']
