from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from .models import InventoryAdjustment
from .serializers import InventoryAdjustmentSerializer
from apps.receipts.models import DocumentStatus
from apps.inventory.models import Stock
from apps.ledger.models import StockLedger, MovementType
from stocksense.utils import broadcast_dashboard_update

class InventoryAdjustmentViewSet(viewsets.ModelViewSet):
    queryset = InventoryAdjustment.objects.all().select_related('product', 'location', 'location__warehouse', 'user').order_by('-created_at')
    serializer_class = InventoryAdjustmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['adjustment_number', 'product__name', 'product__sku', 'notes']
    filterset_fields = ['status', 'product', 'location', 'reason']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def validate_adjustment(self, request, pk=None):
        adj = self.get_object()

        if adj.status == DocumentStatus.DONE:
            return Response({'error': 'Adjustment is already validated.'}, status=status.HTTP_400_BAD_REQUEST)
        if adj.status == DocumentStatus.CANCELLED:
            return Response({'error': 'Cannot validate a cancelled adjustment.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            adj.status = DocumentStatus.DONE
            adj.save()

            product = adj.product
            location = adj.location
            diff = adj.difference

            # 1. Update location stock
            stock, created = Stock.objects.select_for_update().get_or_create(
                product=product,
                location=location,
                defaults={'quantity': 0}
            )
            stock.quantity = adj.counted_quantity
            stock.save()

            # 2. Update overall product stock
            product.current_stock += diff
            product.save()

            # 3. Write Stock Ledger entry
            StockLedger.objects.create(
                reference=adj.adjustment_number,
                product=product,
                movement_type=MovementType.ADJUSTMENT,
                source_location=location if diff < 0 else None,
                destination_location=location if diff > 0 else None,
                quantity=diff,
                user=request.user,
                notes=f"Adjustment ({adj.get_reason_display()}): System={adj.system_quantity}, Counted={adj.counted_quantity}"
            )

        # Broadcast WebSocket update
        broadcast_dashboard_update(
            update_type='ADJUSTMENT_VALIDATED',
            message=f"Adjustment {adj.adjustment_number} validated for {product.name} ({diff:+d} units)",
            data={'adjustment_id': adj.id, 'adjustment_number': adj.adjustment_number}
        )

        return Response({
            'message': f"Adjustment {adj.adjustment_number} successfully validated.",
            'adjustment': InventoryAdjustmentSerializer(adj).data
        })
