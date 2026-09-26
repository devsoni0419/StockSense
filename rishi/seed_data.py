import os
import sys

# Ensure current directory is on python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, init_db
from app.models.user import User
from app.models.category import Category
from app.models.warehouse import Warehouse
from app.models.location import Location
from app.models.product import Product
from app.models.receipt import Receipt, ReceiptItem
from app.models.delivery import DeliveryOrder, DeliveryOrderItem
from app.models.transfer import InternalTransfer, InternalTransferItem
from app.models.adjustment import StockAdjustment
from app.utils.security import hash_password
from app.services.stock_service import increase_stock, transfer_stock, adjust_stock


def seed():
    """Populate database with demo inventory and user accounts."""
    print("Initializing tables...")
    init_db()
    db = SessionLocal()

    try:
        print("Checking if database is already seeded...")
        existing_user = db.query(User).filter(User.email == "manager@stocksense.com").first()
        if existing_user:
            print("Database already contains seed data. Skipping.")
            return

        print("Seeding Users...")
        manager = User(
            name="Sarah Connor (Inventory Manager)",
            email="manager@stocksense.com",
            hashed_password=hash_password("Manager@123"),
            role="inventory_manager",
            is_active=True
        )
        staff = User(
            name="John Doe (Warehouse Staff)",
            email="staff@stocksense.com",
            hashed_password=hash_password("Staff@123"),
            role="warehouse_staff",
            is_active=True
        )
        admin = User(
            name="System Administrator",
            email="admin@stocksense.com",
            hashed_password=hash_password("Admin@123"),
            role="admin",
            is_active=True
        )
        db.add_all([manager, staff, admin])
        db.commit()
        db.refresh(manager)
        db.refresh(staff)

        print("Seeding Warehouses...")
        wh_main = Warehouse(name="Main Warehouse", code="WH-MAIN", address="100 Logistics Blvd", city="Chicago")
        wh_secondary = Warehouse(name="Warehouse 2", code="WH-02", address="45 Harbor Way", city="Newark")
        db.add_all([wh_main, wh_secondary])
        db.commit()
        db.refresh(wh_main)
        db.refresh(wh_secondary)

        print("Seeding Locations...")
        loc_main_store = Location(warehouse_id=wh_main.id, name="Main Store", code="LOC-MAIN", location_type="internal")
        loc_production = Location(warehouse_id=wh_main.id, name="Production Floor", code="LOC-PROD", location_type="production")
        loc_rack_a = Location(warehouse_id=wh_main.id, name="Rack A", code="LOC-RACKA", location_type="internal")
        loc_rack_b = Location(warehouse_id=wh_main.id, name="Rack B", code="LOC-RACKB", location_type="internal")
        loc_wh2_storage = Location(warehouse_id=wh_secondary.id, name="Bulk Storage WH2", code="LOC-WH2-BULK", location_type="internal")
        
        db.add_all([loc_main_store, loc_production, loc_rack_a, loc_rack_b, loc_wh2_storage])
        db.commit()
        db.refresh(loc_main_store)
        db.refresh(loc_production)
        db.refresh(loc_rack_a)
        db.refresh(loc_rack_b)

        print("Seeding Categories...")
        cat_raw = Category(name="Raw Materials", code="CAT-RAW", description="Base metals, polymers, and raw inputs")
        cat_finished = Category(name="Finished Goods", code="CAT-FG", description="Packaged final consumer products")
        cat_hardware = Category(name="Hardware & Parts", code="CAT-HDW", description="Fasteners, brackets, and accessories")
        db.add_all([cat_raw, cat_finished, cat_hardware])
        db.commit()
        db.refresh(cat_raw)
        db.refresh(cat_finished)
        db.refresh(cat_hardware)

        print("Seeding Products...")
        p_steel = Product(
            name="Steel Rods",
            sku="SKU-STEEL-ROD",
            category_id=cat_raw.id,
            uom="kg",
            description="High tensile steel rods 10mm",
            cost_price=45.0,
            selling_price=65.0,
            min_stock_level=50.0,
            max_stock_level=500.0,
            reorder_quantity=100.0
        )
        p_chair = Product(
            name="Ergonomic Office Chair",
            sku="SKU-CHAIR-ERGO",
            category_id=cat_finished.id,
            uom="Units",
            description="Adjustable mesh office chair with lumbar support",
            cost_price=120.0,
            selling_price=220.0,
            min_stock_level=15.0,
            max_stock_level=100.0,
            reorder_quantity=30.0
        )
        p_frames = Product(
            name="Steel Frames",
            sku="SKU-FRAME-STEEL",
            category_id=cat_finished.id,
            uom="Units",
            description="Welded frame subassemblies",
            cost_price=80.0,
            selling_price=140.0,
            min_stock_level=10.0,
            max_stock_level=80.0,
            reorder_quantity=20.0
        )
        p_screws = Product(
            name="Industrial Screws (M8)",
            sku="SKU-SCREW-M8",
            category_id=cat_hardware.id,
            uom="pcs",
            description="Galvanized M8 hex screws",
            cost_price=0.20,
            selling_price=0.50,
            min_stock_level=200.0,  # Alert trigger (we will give 40 pcs)
            max_stock_level=2000.0,
            reorder_quantity=500.0
        )
        p_wood = Product(
            name="Wooden Desk Boards",
            sku="SKU-WOOD-BOARD",
            category_id=cat_raw.id,
            uom="Units",
            description="Solid oak desktop slabs",
            cost_price=75.0,
            selling_price=130.0,
            min_stock_level=5.0,  # 0 stock -> out of stock
            max_stock_level=50.0,
            reorder_quantity=15.0
        )
        db.add_all([p_steel, p_chair, p_frames, p_screws, p_wood])
        db.commit()
        db.refresh(p_steel)
        db.refresh(p_chair)
        db.refresh(p_frames)
        db.refresh(p_screws)
        db.refresh(p_wood)

        print("Executing initial movements (Step 1-4 flow from problem statement)...")
        # Step 1: Receive Goods from Vendor (Receive 100 kg Steel -> Stock: +100)
        increase_stock(
            db=db,
            product_id=p_steel.id,
            location_id=loc_main_store.id,
            quantity=100.0,
            reference_number="REC-2026-0001",
            move_type="receipt",
            user_id=manager.id,
            notes="Step 1: Received from Apex Metals Corp"
        )

        # Initial stock for chairs: 30 chairs in Main Store
        increase_stock(
            db=db,
            product_id=p_chair.id,
            location_id=loc_main_store.id,
            quantity=30.0,
            reference_number="REC-2026-0002",
            move_type="receipt",
            user_id=manager.id,
            notes="Initial stock for chairs"
        )

        # Initial stock for frames: 25 in Main Store
        increase_stock(
            db=db,
            product_id=p_frames.id,
            location_id=loc_main_store.id,
            quantity=25.0,
            reference_number="REC-2026-0003",
            move_type="receipt",
            user_id=manager.id,
            notes="Initial stock for frames"
        )

        # Low stock item: 40 screws (threshold is 200)
        increase_stock(
            db=db,
            product_id=p_screws.id,
            location_id=loc_rack_a.id,
            quantity=40.0,
            reference_number="REC-2026-0004",
            move_type="receipt",
            user_id=staff.id,
            notes="Partial screw shipment"
        )

        # Step 2: Internal Transfer: Main Store -> Production Rack / Floor
        transfer_stock(
            db=db,
            product_id=p_steel.id,
            source_location_id=loc_main_store.id,
            destination_location_id=loc_production.id,
            quantity=50.0,
            reference_number="INT-2026-0001",
            user_id=staff.id,
            notes="Step 2: Move steel to production rack"
        )

        # Step 3: Deliver finished goods (Deliver 20 frames)
        # We also create a delivery order document
        del_order = DeliveryOrder(
            reference_number="DEL-2026-0001",
            customer_name="MegaCorp Logistics",
            source_location_id=loc_main_store.id,
            status="done",
            shipping_address="742 Evergreen Terrace",
            created_by_user_id=manager.id
        )
        db.add(del_order)
        db.flush()
        del_item = DeliveryOrderItem(
            delivery_order_id=del_order.id,
            product_id=p_frames.id,
            quantity_demand=20.0,
            quantity_done=20.0
        )
        db.add(del_item)
        # Deduct stock for Step 3: Deliver 20 frames -> Stock for frames: -20
        from app.services.stock_service import decrease_stock
        decrease_stock(
            db=db,
            product_id=p_frames.id,
            location_id=loc_main_store.id,
            quantity=20.0,
            reference_number=del_order.reference_number,
            move_type="delivery",
            user_id=staff.id,
            notes="Step 3: Deliver 20 frames to customer"
        )

        # Step 4: Adjust damaged items (3 kg steel damaged -> Stock: -3)
        # Adjust stock at production floor from 50 to 47
        adjust_stock(
            db=db,
            product_id=p_steel.id,
            location_id=loc_production.id,
            counted_quantity=47.0,
            reference_number="ADJ-2026-0001",
            reason="Step 4: 3 kg steel damaged during cutting",
            user_id=staff.id,
            notes="Damaged raw material written off"
        )
        adj_record = StockAdjustment(
            reference_number="ADJ-2026-0001",
            product_id=p_steel.id,
            location_id=loc_production.id,
            recorded_quantity=50.0,
            counted_quantity=47.0,
            difference_quantity=-3.0,
            reason="Damaged in production",
            status="done",
            created_by_user_id=staff.id
        )
        db.add(adj_record)

        # Also add a pending Receipt
        rec_pending = Receipt(
            reference_number="REC-2026-0005",
            supplier_name="Global Steel Suppliers Ltd",
            destination_location_id=loc_main_store.id,
            status="waiting",
            notes="Expected delivery by end of week",
            created_by_user_id=manager.id
        )
        db.add(rec_pending)
        db.flush()
        rec_pending_item = ReceiptItem(
            receipt_id=rec_pending.id,
            product_id=p_steel.id,
            quantity_expected=200.0,
            quantity_received=0.0
        )
        db.add(rec_pending_item)

        # Also add a draft Delivery Order
        del_pending = DeliveryOrder(
            reference_number="DEL-2026-0002",
            customer_name="Acme Furniture Co",
            source_location_id=loc_main_store.id,
            status="draft",
            notes="Sales order for 10 chairs",
            created_by_user_id=manager.id
        )
        db.add(del_pending)
        db.flush()
        del_pending_item = DeliveryOrderItem(
            delivery_order_id=del_pending.id,
            product_id=p_chair.id,
            quantity_demand=10.0,
            quantity_done=0.0
        )
        db.add(del_pending_item)

        # Also add a scheduled internal transfer
        trans_sched = InternalTransfer(
            reference_number="INT-2026-0002",
            source_location_id=loc_main_store.id,
            destination_location_id=loc_wh2_storage.id,
            status="waiting",
            notes="Scheduled replenishment to Warehouse 2",
            created_by_user_id=staff.id
        )
        db.add(trans_sched)
        db.flush()
        trans_item = InternalTransferItem(
            transfer_id=trans_sched.id,
            product_id=p_chair.id,
            quantity=5.0
        )
        db.add(trans_item)

        db.commit()
        print("StockSense successfully seeded with demo data!")
        print("\nDemo Accounts:")
        print("  Inventory Manager: manager@stocksense.com  / Password: Manager@123")
        print("  Warehouse Staff:   staff@stocksense.com    / Password: Staff@123")
        print("  Administrator:     admin@stocksense.com    / Password: Admin@123\n")

    except Exception as e:
        db.rollback()
        print(f"\n[StockSense Database Notice] Could not seed database: {e}")
        print("\nNote: Make sure your PostgreSQL database is running and your DATABASE_URL in .env is configured.")
        print("Example DATABASE_URL: postgresql+psycopg://username:password@localhost:5432/stocksense_db")
        print("Once configured, re-run 'python seed_data.py' to populate demo data.\n")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
