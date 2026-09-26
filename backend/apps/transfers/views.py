from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from .models import InternalTransfer, TransferItem
from .serializers import InternalTransferSerializer
from apps.receipts.models import DocumentStatus
from apps.inventory.models import Stock
from apps.ledger.models import StockLedger, MovementType
from stocksense.utils import broadcast_dashboard_update

class InternalTransferViewSet(viewsets.ModelViewSet):
    queryset = InternalTransfer.objects.all().select_related(
        'source_location', 'source_location__warehouse',
        'destination_location', 'destination_location__warehouse', 'created_by'
    ).prefetch_related('items', 'items__product').order_by('-created_at')
    serializer_class = InternalTransferSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['transfer_number', 'notes']
    filterset_fields = ['status', 'source_location', 'destination_location']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def validate_transfer(self, request, pk=None):
        transfer = self.get_object()

        if transfer.status == DocumentStatus.DONE:
            return Response({'error': 'Transfer is already validated.'}, status=status.HTTP_400_BAD_REQUEST)
        if transfer.status == DocumentStatus.CANCELLED:
            return Response({'error': 'Cannot validate a cancelled transfer.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Check availability at source location
            errors = []
            source_loc = transfer.source_location
            dest_loc = transfer.destination_location

            for item in transfer.items.all():
                stock = Stock.objects.filter(product=item.product, location=source_loc).select_for_update().first()
                avail = stock.quantity if stock else 0
                if avail < item.quantity:
                    errors.append(
                        f"Insufficient stock for '{item.product.name}' at '{source_loc.name}'. "
                        f"Requested: {item.quantity}, Available: {avail}"
                    )

            if errors:
                return Response({'error': 'Transfer failed due to stock shortages.', 'details': errors}, status=status.HTTP_400_BAD_REQUEST)

            transfer.status = DocumentStatus.DONE
            transfer.save()

            for item in transfer.items.all():
                product = item.product
                qty = item.quantity

                # 1. Deduct from source location
                src_stock = Stock.objects.get(product=product, location=source_loc)
                src_stock.quantity -= qty
                src_stock.save()

                # 2. Add to destination location
                dst_stock, created = Stock.objects.select_for_update().get_or_create(
                    product=product,
                    location=dest_loc,
                    defaults={'quantity': 0}
                )
                dst_stock.quantity += qty
                dst_stock.save()

                # Note: Total company stock for product remains unchanged!

                # 3. Ledger entry
                StockLedger.objects.create(
                    reference=transfer.transfer_number,
                    product=product,
                    movement_type=MovementType.INTERNAL_TRANSFER,
                    source_location=source_loc,
                    destination_location=dest_loc,
                    quantity=qty,
                    user=request.user,
                    notes=f"Moved from {source_loc.name} to {dest_loc.name}"
                )

        # Broadcast WebSocket update
        broadcast_dashboard_update(
            update_type='TRANSFER_VALIDATED',
            message=f"Transfer {transfer.transfer_number} validated ({source_loc.name} ➔ {dest_loc.name})",
            data={'transfer_id': transfer.id, 'transfer_number': transfer.transfer_number}
        )

        return Response({
            'message': f"Transfer {transfer.transfer_number} successfully validated.",
            'transfer': InternalTransferSerializer(transfer).data
        })

    @action(detail=True, methods=['post'])
    def cancel_transfer(self, request, pk=None):
        transfer = self.get_object()
        if transfer.status == DocumentStatus.DONE:
            return Response({'error': 'Cannot cancel a completed transfer.'}, status=status.HTTP_400_BAD_REQUEST)
        transfer.status = DocumentStatus.CANCELLED
        transfer.save()
        return Response({'message': f"Transfer {transfer.transfer_number} cancelled."})
