from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
import datetime

from apps.products.models import Product, Category
from apps.warehouses.models import Warehouse, Location
from apps.inventory.models import Stock
from apps.receipts.models import Receipt, DocumentStatus
from apps.deliveries.models import Delivery
from apps.transfers.models import InternalTransfer
from apps.ledger.models import StockLedger, MovementType

class DashboardKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        warehouse_id = request.query_params.get('warehouse')
        category_id = request.query_params.get('category')

        # Base product queryset
        products_qs = Product.objects.filter(is_archived=False)
        if category_id:
            products_qs = products_qs.filter(category_id=category_id)

        total_products = products_qs.count()
        total_stock_qty = products_qs.aggregate(total=Sum('current_stock'))['total'] or 0

        # Low stock & Out of stock counts
        low_stock_count = products_qs.filter(
            current_stock__gt=0,
            current_stock__lte=F('reorder_level')
        ).count()

        out_of_stock_count = products_qs.filter(current_stock__lte=0).count()

        # Pending document counts
        pending_statuses = [DocumentStatus.DRAFT, DocumentStatus.WAITING, DocumentStatus.READY]

        receipts_qs = Receipt.objects.filter(status__in=pending_statuses)
        deliveries_qs = Delivery.objects.filter(status__in=pending_statuses)
        transfers_qs = InternalTransfer.objects.filter(status__in=pending_statuses)

        if warehouse_id:
            receipts_qs = receipts_qs.filter(warehouse_id=warehouse_id)
            deliveries_qs = deliveries_qs.filter(warehouse_id=warehouse_id)
            transfers_qs = transfers_qs.filter(
                Q(source_location__warehouse_id=warehouse_id) |
                Q(destination_location__warehouse_id=warehouse_id)
            )

        return Response({
            'total_products': total_products,
            'total_stock_quantity': total_stock_qty,
            'low_stock_items': low_stock_count,
            'out_of_stock_items': out_of_stock_count,
            'pending_receipts': receipts_qs.count(),
            'pending_deliveries': deliveries_qs.count(),
            'scheduled_transfers': transfers_qs.count(),
        })


class DashboardChartsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        warehouse_id = request.query_params.get('warehouse')
        category_id = request.query_params.get('category')

        # 1. Warehouse-wise stock distribution
        warehouses = Warehouse.objects.filter(is_active=True)
        warehouse_data = []
        for wh in warehouses:
            stock_qty = Stock.objects.filter(location__warehouse=wh)
            if category_id:
                stock_qty = stock_qty.filter(product__category_id=category_id)
            sum_qty = stock_qty.aggregate(total=Sum('quantity'))['total'] or 0
            warehouse_data.append({
                'id': wh.id,
                'name': wh.name,
                'code': wh.code,
                'total_stock': sum_qty
            })

        # 2. Low stock products chart
        low_stock_products = Product.objects.filter(
            is_archived=False,
            current_stock__lte=F('reorder_level')
        ).order_by('current_stock')[:8]

        low_stock_chart_data = [
            {
                'name': p.name,
                'sku': p.sku,
                'current_stock': max(0, p.current_stock),
                'reorder_level': p.reorder_level
            }
            for p in low_stock_products
        ]

        # 3. Stock Movement Timeline (Last 7 days)
        today = timezone.now().date()
        timeline_data = []
        for i in range(6, -1, -1):
            day = today - datetime.timedelta(days=i)
            day_start = timezone.make_aware(datetime.datetime.combine(day, datetime.time.min))
            day_end = timezone.make_aware(datetime.datetime.combine(day, datetime.time.max))

            ledger_entries = StockLedger.objects.filter(date__gte=day_start, date__lte=day_end)
            if category_id:
                ledger_entries = ledger_entries.filter(product__category_id=category_id)

            receipts = ledger_entries.filter(movement_type=MovementType.RECEIPT).aggregate(t=Sum('quantity'))['t'] or 0
            deliveries = abs(ledger_entries.filter(movement_type=MovementType.DELIVERY).aggregate(t=Sum('quantity'))['t'] or 0)
            transfers = ledger_entries.filter(movement_type=MovementType.INTERNAL_TRANSFER).aggregate(t=Sum('quantity'))['t'] or 0
            adjustments = ledger_entries.filter(movement_type=MovementType.ADJUSTMENT).aggregate(t=Sum('quantity'))['t'] or 0

            timeline_data.append({
                'date': day.strftime('%b %d'),
                'receipts': receipts,
                'deliveries': deliveries,
                'transfers': transfers,
                'adjustments': adjustments
            })

        # 4. Incoming vs Outgoing comparison
        total_incoming = StockLedger.objects.filter(movement_type=MovementType.RECEIPT).aggregate(t=Sum('quantity'))['t'] or 0
        total_outgoing = abs(StockLedger.objects.filter(movement_type=MovementType.DELIVERY).aggregate(t=Sum('quantity'))['t'] or 0)

        return Response({
            'warehouse_distribution': warehouse_data,
            'low_stock_chart': low_stock_chart_data,
            'stock_movement_timeline': timeline_data,
            'incoming_vs_outgoing': {
                'incoming': total_incoming,
                'outgoing': total_outgoing
            }
        })
