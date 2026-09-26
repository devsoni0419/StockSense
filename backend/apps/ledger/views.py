from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
import csv
from .models import StockLedger
from .serializers import StockLedgerSerializer

class StockLedgerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockLedger.objects.all().select_related(
        'product', 'source_location', 'source_location__warehouse',
        'destination_location', 'destination_location__warehouse', 'user'
    ).order_by('-date')
    serializer_class = StockLedgerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['reference', 'product__name', 'product__sku', 'notes', 'user__username']
    filterset_fields = ['product', 'movement_type', 'source_location', 'destination_location']

    def get_queryset(self):
        qs = super().get_queryset()
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        warehouse_id = self.request.query_params.get('warehouse')

        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)
        if warehouse_id:
            qs = qs.filter(
                models.Q(source_location__warehouse_id=warehouse_id) |
                models.Q(destination_location__warehouse_id=warehouse_id)
            )
        return qs

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="StockSense_Stock_Ledger.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Date', 'Reference', 'Product Name', 'SKU', 'Movement Type',
            'Source Location', 'Destination Location', 'Quantity', 'User', 'Notes'
        ])

        for entry in queryset:
            writer.writerow([
                entry.date.strftime('%Y-%m-%d %H:%M:%S'),
                entry.reference,
                entry.product.name,
                entry.product.sku,
                entry.get_movement_type_display(),
                f"{entry.source_location.warehouse.code} / {entry.source_location.name}" if entry.source_location else '-',
                f"{entry.destination_location.warehouse.code} / {entry.destination_location.name}" if entry.destination_location else '-',
                entry.quantity,
                entry.user.get_full_name() if entry.user else 'System',
                entry.notes or ''
            ])

        return response
