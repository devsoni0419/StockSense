from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from .models import Receipt, ReceiptItem, DocumentStatus
from .serializers import ReceiptSerializer
from apps.inventory.models import Stock
from apps.ledger.models import StockLedger, MovementType
from stocksense.utils import broadcast_dashboard_update

class ReceiptViewSet(viewsets.ModelViewSet):
    queryset = Receipt.objects.all().select_related('warehouse', 'destination_location', 'created_by').prefetch_related('items', 'items__product').order_by('-created_at')
    serializer_class = ReceiptSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['receipt_number', 'supplier_name', 'notes']
    filterset_fields = ['status', 'warehouse', 'destination_location']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def validate_receipt(self, request, pk=None):
        receipt = self.get_object()

        if receipt.status == DocumentStatus.DONE:
            return Response({'error': 'Receipt is already validated.'}, status=status.HTTP_400_BAD_REQUEST)
        if receipt.status == DocumentStatus.CANCELLED:
            return Response({'error': 'Cannot validate a cancelled receipt.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            receipt.status = DocumentStatus.DONE
            receipt.save()

            for item in receipt.items.all():
                product = item.product
                location = receipt.destination_location
                qty = item.quantity

                # 1. Update/Create location stock balance
                stock, created = Stock.objects.select_for_update().get_or_create(
                    product=product,
                    location=location,
                    defaults={'quantity': 0}
                )
                stock.quantity += qty
                stock.save()

                # 2. Update overall product stock
                product.current_stock += qty
                product.save()

                # 3. Write Stock Ledger entry
                StockLedger.objects.create(
                    reference=receipt.receipt_number,
                    product=product,
                    movement_type=MovementType.RECEIPT,
                    destination_location=location,
                    quantity=qty,
                    user=request.user,
                    notes=f"Supplier: {receipt.supplier_name}"
                )

        # 4. Broadcast WebSocket update
        broadcast_dashboard_update(
            update_type='RECEIPT_VALIDATED',
            message=f"Receipt {receipt.receipt_number} validated (+{sum(i.quantity for i in receipt.items.all())} units)",
            data={'receipt_id': receipt.id, 'receipt_number': receipt.receipt_number}
        )

        return Response({
            'message': f"Receipt {receipt.receipt_number} successfully validated.",
            'receipt': ReceiptSerializer(receipt).data
        })

    @action(detail=True, methods=['post'])
    def cancel_receipt(self, request, pk=None):
        receipt = self.get_object()
        if receipt.status == DocumentStatus.DONE:
            return Response({'error': 'Cannot cancel a completed receipt.'}, status=status.HTTP_400_BAD_REQUEST)
        receipt.status = DocumentStatus.CANCELLED
        receipt.save()
        return Response({'message': f"Receipt {receipt.receipt_number} cancelled."})
