from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
import datetime

from apps.authentication.models import User, UserRole
from apps.products.models import Category, Product
from apps.warehouses.models import Warehouse, Location
from apps.inventory.models import Stock
from apps.receipts.models import Receipt, ReceiptItem, DocumentStatus
from apps.deliveries.models import Delivery, DeliveryItem
from apps.transfers.models import InternalTransfer, TransferItem
from apps.adjustments.models import InventoryAdjustment, AdjustmentReason
from apps.ledger.models import StockLedger, MovementType
from apps.notifications.models import Notification, NotificationType

class Command(BaseCommand):
    help = 'Seeds realistic hackathon demo data for StockSense'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Seeding StockSense Database...'))

        with transaction.atomic():
            # 1. Create Users
            manager, _ = User.objects.get_or_create(
                email='admin@stocksense.com',
                defaults={
                    'username': 'admin',
                    'first_name': 'Alex',
                    'last_name': 'Morgan',
                    'role': UserRole.MANAGER,
                    'is_staff': True,
                    'is_superuser': True,
                    'department': 'Inventory Management'
                }
            )
            manager.set_password('admin123')
            manager.save()

            staff, _ = User.objects.get_or_create(
                email='staff@stocksense.com',
                defaults={
                    'username': 'staff',
                    'first_name': 'Sam',
                    'last_name': 'Taylor',
                    'role': UserRole.STAFF,
                    'department': 'Warehouse Operations'
                }
            )
            staff.set_password('staff123')
            staff.save()

            self.stdout.write('Created Users (admin@stocksense.com / staff@stocksense.com)')

            # 2. Create Warehouses & Locations
            mwh, _ = Warehouse.objects.get_or_create(
                code='MWH',
                defaults={'name': 'Main Warehouse', 'address': '100 Industrial Parkway, Zone A'}
            )
            wh2, _ = Warehouse.objects.get_or_create(
                code='WH2',
                defaults={'name': 'Secondary Distribution Center', 'address': '45 Logistics Blvd, Zone B'}
            )

            # Locations for MWH
            rack_a, _ = Location.objects.get_or_create(warehouse=mwh, code='MWH-RACK-A', defaults={'name': 'Rack A', 'location_type': 'STORAGE'})
            rack_b, _ = Location.objects.get_or_create(warehouse=mwh, code='MWH-RACK-B', defaults={'name': 'Rack B', 'location_type': 'STORAGE'})
            prod_floor, _ = Location.objects.get_or_create(warehouse=mwh, code='MWH-PROD-1', defaults={'name': 'Production Floor', 'location_type': 'PRODUCTION'})
            receiving_dock, _ = Location.objects.get_or_create(warehouse=mwh, code='MWH-REC-1', defaults={'name': 'Receiving Dock', 'location_type': 'RECEIVING'})

            # Locations for WH2
            wh2_rack_a, _ = Location.objects.get_or_create(warehouse=wh2, code='WH2-RACK-A', defaults={'name': 'Rack A', 'location_type': 'STORAGE'})
            wh2_rack_b, _ = Location.objects.get_or_create(warehouse=wh2, code='WH2-RACK-B', defaults={'name': 'Rack B', 'location_type': 'STORAGE'})
            shipping_bay, _ = Location.objects.get_or_create(warehouse=wh2, code='WH2-SHIP-1', defaults={'name': 'Shipping Bay', 'location_type': 'SHIPPING'})

            self.stdout.write('Created Warehouses & Locations')

            # 3. Create Categories
            cat_raw, _ = Category.objects.get_or_create(name='Raw Materials', defaults={'description': 'Metals, wood, raw components'})
            cat_elec, _ = Category.objects.get_or_create(name='Electronics & IT', defaults={'description': 'Laptops, sensors, cables'})
            cat_furn, _ = Category.objects.get_or_create(name='Office Furniture', defaults={'description': 'Chairs, desks, cabinets'})
            cat_const, _ = Category.objects.get_or_create(name='Construction Materials', defaults={'description': 'Cement, bricks, tiles'})
            cat_safe, _ = Category.objects.get_or_create(name='Safety & PPE', defaults={'description': 'Helmets, gloves, vests'})

            # 4. Create Products
            products_data = [
                {'name': 'Steel Rods (12mm)', 'sku': 'RAW-STL-001', 'barcode': '890123456001', 'category': cat_raw, 'unit_of_measure': 'pcs', 'initial': 150, 'current': 150, 'reorder': 30, 'location': rack_a},
                {'name': 'Ergonomic Mesh Office Chair', 'sku': 'FRN-CHR-002', 'barcode': '890123456002', 'category': cat_furn, 'unit_of_measure': 'units', 'initial': 45, 'current': 45, 'reorder': 10, 'location': rack_b},
                {'name': 'Developer Laptop Pro 15"', 'sku': 'ELC-LTP-003', 'barcode': '890123456003', 'category': cat_elec, 'unit_of_measure': 'units', 'initial': 25, 'current': 25, 'reorder': 5, 'location': wh2_rack_a},
                {'name': 'Portland Cement Bags (50kg)', 'sku': 'CNS-CMT-004', 'barcode': '890123456004', 'category': cat_const, 'unit_of_measure': 'boxes', 'initial': 200, 'current': 200, 'reorder': 40, 'location': prod_floor},
                {'name': 'Hardwood Panels (4x8ft)', 'sku': 'RAW-WDN-005', 'barcode': '890123456005', 'category': cat_raw, 'unit_of_measure': 'pcs', 'initial': 80, 'current': 80, 'reorder': 20, 'location': rack_a},
                {'name': 'Industrial Safety Helmets', 'sku': 'SAF-HLM-006', 'barcode': '890123456006', 'category': cat_safe, 'unit_of_measure': 'pcs', 'initial': 60, 'current': 8, 'reorder': 15, 'location': rack_b}, # LOW STOCK DEMO!
                {'name': 'High-Visibility Safety Vests', 'sku': 'SAF-VST-007', 'barcode': '890123456007', 'category': cat_safe, 'unit_of_measure': 'pcs', 'initial': 100, 'current': 0, 'reorder': 25, 'location': wh2_rack_b}, # OUT OF STOCK DEMO!
                {'name': '4K Ultra HD Monitor 27"', 'sku': 'ELC-MNT-008', 'barcode': '890123456008', 'category': cat_elec, 'unit_of_measure': 'units', 'initial': 30, 'current': 30, 'reorder': 8, 'location': wh2_rack_a},
                {'name': 'CAT6 Ethernet Cable (300m)', 'sku': 'ELC-CBL-009', 'barcode': '890123456009', 'category': cat_elec, 'unit_of_measure': 'packs', 'initial': 40, 'current': 40, 'reorder': 10, 'location': rack_a},
                {'name': 'Standing Desk Frame', 'sku': 'FRN-DSK-010', 'barcode': '890123456010', 'category': cat_furn, 'unit_of_measure': 'units', 'initial': 18, 'current': 18, 'reorder': 5, 'location': rack_b},
                {'name': 'Heavy Duty Protective Gloves', 'sku': 'SAF-GLV-011', 'barcode': '890123456011', 'category': cat_safe, 'unit_of_measure': 'packs', 'initial': 120, 'current': 120, 'reorder': 30, 'location': wh2_rack_b},
                {'name': 'Copper Wires (100m spool)', 'sku': 'RAW-CPR-012', 'barcode': '890123456012', 'category': cat_raw, 'unit_of_measure': 'meters', 'initial': 500, 'current': 500, 'reorder': 100, 'location': prod_floor},
            ]

            created_products = {}
            for pdata in products_data:
                prod, _ = Product.objects.get_or_create(
                    sku=pdata['sku'],
                    defaults={
                        'name': pdata['name'],
                        'barcode': pdata['barcode'],
                        'category': pdata['category'],
                        'unit_of_measure': pdata['unit_of_measure'],
                        'initial_stock': pdata['initial'],
                        'current_stock': pdata['current'],
                        'reorder_level': pdata['reorder'],
                    }
                )
                created_products[prod.sku] = prod

                # Stock balance entry
                Stock.objects.get_or_create(
                    product=prod,
                    location=pdata['location'],
                    defaults={'quantity': pdata['current']}
                )

                # Initial ledger entry
                StockLedger.objects.get_or_create(
                    reference=f"INIT-{prod.sku}",
                    product=prod,
                    movement_type=MovementType.RECEIPT,
                    destination_location=pdata['location'],
                    quantity=pdata['current'],
                    user=manager,
                    notes="Initial Stock Initialization"
                )

            self.stdout.write(f'Created {len(created_products)} Products & Stock Balances')

            # 5. Create Sample Pending & Completed Transactions
            today = datetime.date.today()

            # Completed Receipt
            rec1, _ = Receipt.objects.get_or_create(
                receipt_number='REC-2026-0001',
                defaults={
                    'supplier_name': 'Apex Steel Suppliers Ltd.',
                    'warehouse': mwh,
                    'destination_location': rack_a,
                    'date': today - datetime.timedelta(days=2),
                    'status': DocumentStatus.DONE,
                    'notes': 'Received initial batch of high grade steel rods.',
                    'created_by': manager
                }
            )
            ReceiptItem.objects.get_or_create(receipt=rec1, product=created_products['RAW-STL-001'], defaults={'quantity': 50})

            # Pending Draft Receipt
            rec2, _ = Receipt.objects.get_or_create(
                receipt_number='REC-2026-0002',
                defaults={
                    'supplier_name': 'TechMatics Global Corp',
                    'warehouse': wh2,
                    'destination_location': wh2_rack_a,
                    'date': today,
                    'status': DocumentStatus.READY,
                    'notes': 'Awaiting dock arrival of developer laptops.',
                    'created_by': staff
                }
            )
            ReceiptItem.objects.get_or_create(receipt=rec2, product=created_products['ELC-LTP-003'], defaults={'quantity': 10})

            # Completed Delivery
            del1, _ = Delivery.objects.get_or_create(
                delivery_number='DEL-2026-0001',
                defaults={
                    'customer_name': 'Horizon BuildCorp Inc.',
                    'warehouse': mwh,
                    'source_location': prod_floor,
                    'date': today - datetime.timedelta(days=1),
                    'status': DocumentStatus.DONE,
                    'notes': 'Dispatched cement bags for site B development.',
                    'created_by': manager
                }
            )
            DeliveryItem.objects.get_or_create(delivery=del1, product=created_products['CNS-CMT-004'], defaults={'quantity': 20})

            # Pending Delivery Order
            del2, _ = Delivery.objects.get_or_create(
                delivery_number='DEL-2026-0002',
                defaults={
                    'customer_name': 'NextGen Software Labs',
                    'warehouse': wh2,
                    'source_location': wh2_rack_a,
                    'date': today,
                    'status': DocumentStatus.WAITING,
                    'notes': 'Scheduled order for 4K Monitors.',
                    'created_by': staff
                }
            )
            DeliveryItem.objects.get_or_create(delivery=del2, product=created_products['ELC-MNT-008'], defaults={'quantity': 5})

            # Internal Transfer (Completed)
            trf1, _ = InternalTransfer.objects.get_or_create(
                transfer_number='TRF-2026-0001',
                defaults={
                    'source_location': rack_a,
                    'destination_location': prod_floor,
                    'date': today - datetime.timedelta(days=1),
                    'status': DocumentStatus.DONE,
                    'notes': 'Transferred steel rods from Storage Rack A to Production Floor.',
                    'created_by': staff
                }
            )
            TransferItem.objects.get_or_create(transfer=trf1, product=created_products['RAW-STL-001'], defaults={'quantity': 30})

            # Inventory Adjustment
            adj1, _ = InventoryAdjustment.objects.get_or_create(
                adjustment_number='ADJ-2026-0001',
                defaults={
                    'product': created_products['SAF-HLM-006'],
                    'location': rack_b,
                    'system_quantity': 11,
                    'counted_quantity': 8,
                    'difference': -3,
                    'reason': AdjustmentReason.DAMAGED,
                    'status': DocumentStatus.DONE,
                    'notes': '3 safety helmets found damaged during routine physical count.',
                    'user': manager,
                    'date': today
                }
            )

            # 6. Low stock & Out of stock notifications
            Notification.objects.get_or_create(
                title='LOW STOCK ALERT: Industrial Safety Helmets',
                defaults={
                    'message': 'Product Industrial Safety Helmets (SKU: SAF-HLM-006) stock (8) is below reorder level (15).',
                    'alert_type': NotificationType.LOW_STOCK,
                    'product': created_products['SAF-HLM-006']
                }
            )
            Notification.objects.get_or_create(
                title='OUT OF STOCK ALERT: High-Visibility Safety Vests',
                defaults={
                    'message': 'Product High-Visibility Safety Vests (SKU: SAF-VST-007) is completely out of stock!',
                    'alert_type': NotificationType.OUT_OF_STOCK,
                    'product': created_products['SAF-VST-007']
                }
            )

            self.stdout.write(self.style.SUCCESS('Successfully seeded StockSense database with realistic hackathon demo data!'))
