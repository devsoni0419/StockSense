from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'sku', 'barcode', 'category__name']
    filterset_fields = ['category', 'is_archived', 'unit_of_measure']

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('stock_status')
        if status_param == 'LOW_STOCK':
            qs = qs.filter(current_stock__lte=models.F('reorder_level'), current_stock__gt=0)
        elif status_param == 'OUT_OF_STOCK':
            qs = qs.filter(current_stock__lte=0)
        elif status_param == 'IN_STOCK':
            qs = qs.filter(current_stock__gt=models.F('reorder_level'))
        return qs

    @action(detail=True, methods=['post'])
    def toggle_archive(self, request, pk=None):
        product = self.get_object()
        product.is_archived = not product.is_archived
        product.save()
        return Response({
            'status': 'archived' if product.is_archived else 'active',
            'product': ProductSerializer(product).data
        })
