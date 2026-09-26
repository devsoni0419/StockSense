from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from .models import Delivery, DeliveryItem
from .serializers import DeliverySerializer
from apps.receipts.models import DocumentStatus
from apps.inventory.models import Stock
from apps.ledger.models import StockLedger, MovementType
from stocksense.utils import broadcast_dashboard_update

class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.all().select_related('warehouse', 'source_location', 'created_by').prefetch_related('items', 'items__product').order_by('-created_at')
    serializer_class = DeliverySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['delivery_number', 'customer_name', 'notes']
    filterset_fields = ['status', 'warehouse', 'source_location']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def validate_delivery(self, request, pk=None):
        delivery = self.get_object()

        if delivery.status == DocumentStatus.DONE:
            return Response({'error': 'Delivery is already validated.'}, status=status.HTTP_400_BAD_REQUEST)
        if delivery.status == DocumentStatus.CANCELLED:
            return Response({'error': 'Cannot validate a cancelled delivery.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # First check stock availability for all items with row locking
            errors = []
            location = delivery.source_location

            for item in delivery.items.all():
                stock = Stock.objects.filter(product=item.product, location=location).select_for_update().first()
                available_qty = stock.quantity if stock else 0
                if available_qty < item.quantity:
                    errors.append(
                        f"Insufficient stock for '{item.product.name}' (SKU: {item.product.sku}) at '{location.name}'. "
                        f"Requested: {item.quantity}, Available: {available_qty}"
                    )

            if errors:
                return Response({'error': 'Validation failed due to stock shortages.', 'details': errors}, status=status.HTTP_400_BAD_REQUEST)

            # Deduct stock and record ledger
            delivery.status = DocumentStatus.DONE
            delivery.save()

            for item in delivery.items.all():
                product = item.product
                qty = item.quantity

                stock = Stock.objects.get(product=product, location=location)
                stock.quantity -= qty
                stock.save()

                product.current_stock -= qty
                product.save()

                StockLedger.objects.create(
                    reference=delivery.delivery_number,
                    product=product,
                    movement_type=MovementType.DELIVERY,
                    source_location=location,
                    quantity=-qty,
                    user=request.user,
                    notes=f"Customer: {delivery.customer_name}"
                )

        # Broadcast WebSocket update
        broadcast_dashboard_update(
            update_type='DELIVERY_VALIDATED',
            message=f"Delivery Order {delivery.delivery_number} validated (-{sum(i.quantity for i in delivery.items.all())} units)",
            data={'delivery_id': delivery.id, 'delivery_number': delivery.delivery_number}
        )

        return Response({
            'message': f"Delivery Order {delivery.delivery_number} successfully validated.",
            'delivery': DeliverySerializer(delivery).data
        })

    @action(detail=True, methods=['post'])
    def cancel_delivery(self, request, pk=None):
        delivery = self.get_object()
        if delivery.status == DocumentStatus.DONE:
            return Response({'error': 'Cannot cancel a completed delivery.'}, status=status.HTTP_400_BAD_REQUEST)
        delivery.status = DocumentStatus.CANCELLED
        delivery.save()
        return Response({'message': f"Delivery {delivery.delivery_number} cancelled."})
