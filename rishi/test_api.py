import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure current directory is on python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import Base, get_db
from main import app

# In-memory SQLite engine for automated test isolation
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_01_health_check():
    """Verify health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "StockSense" in data["app_name"]


def test_02_auth_flow():
    """Test user signup, login, OTP reset, and profile retrieval."""
    # 1. Signup
    signup_payload = {
        "name": "Alex Manager",
        "email": "alex.manager@example.com",
        "password": "Password@123",
        "role": "inventory_manager"
    }
    signup_res = client.post("/api/v1/auth/signup", json=signup_payload)
    assert signup_res.status_code == 201
    assert signup_res.json()["success"] is True
    assert signup_res.json()["data"]["email"] == "alex.manager@example.com"

    # 2. Login
    login_payload = {
        "email": "alex.manager@example.com",
        "password": "Password@123"
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token_data = login_res.json()["data"]
    token = token_data["access_token"]
    assert token is not None

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Get Profile
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["data"]["name"] == "Alex Manager"

    # 4. Forgot password & OTP verification
    forgot_res = client.post("/api/v1/auth/forgot-password", json={"email": "alex.manager@example.com"})
    assert forgot_res.status_code == 200
    dev_otp = forgot_res.json()["data"].get("dev_otp")
    assert dev_otp is not None

    # Verify OTP
    verify_res = client.post("/api/v1/auth/verify-otp", json={"email": "alex.manager@example.com", "otp": dev_otp})
    assert verify_res.status_code == 200
    assert verify_res.json()["data"]["verified"] is True

    # Reset Password
    reset_res = client.post("/api/v1/auth/reset-password", json={
        "email": "alex.manager@example.com",
        "otp": dev_otp,
        "new_password": "NewSecretPassword@456"
    })
    assert reset_res.status_code == 200

    # Login with new password
    new_login = client.post("/api/v1/auth/login", json={
        "email": "alex.manager@example.com",
        "password": "NewSecretPassword@456"
    })
    assert new_login.status_code == 200


def test_03_settings_warehouses_and_locations():
    """Test warehouse and location management."""
    # Login to get token
    login_res = client.post("/api/v1/auth/login", json={
        "email": "alex.manager@example.com",
        "password": "NewSecretPassword@456"
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Warehouse
    wh_res = client.post("/api/v1/warehouses", json={
        "name": "Central Distribution Hub",
        "code": "CDH-01",
        "address": "400 Logistics Expressway",
        "city": "Dallas"
    }, headers=headers)
    assert wh_res.status_code == 201
    wh_id = wh_res.json()["data"]["id"]

    # Create Locations
    loc1_res = client.post("/api/v1/locations", json={
        "warehouse_id": wh_id,
        "name": "Main Store",
        "code": "LOC-MAIN",
        "location_type": "internal"
    }, headers=headers)
    assert loc1_res.status_code == 201

    loc2_res = client.post("/api/v1/locations", json={
        "warehouse_id": wh_id,
        "name": "Production Floor",
        "code": "LOC-PROD",
        "location_type": "production"
    }, headers=headers)
    assert loc2_res.status_code == 201

    # List locations
    list_loc = client.get(f"/api/v1/locations?warehouse_id={wh_id}")
    assert list_loc.status_code == 200
    assert len(list_loc.json()["data"]) == 2


def test_04_inventory_lifecycle_from_pdf():
    """
    Test exact 4-step example from problem statement PDF:
    Step 1: Receive 100 kg Steel from Vendor -> Stock: +100
    Step 2: Internal transfer: Main Store -> Production Rack -> Stock unchanged in total
    Step 3: Deliver 20 steel -> Stock: -20
    Step 4: Adjust damaged items (3 kg damaged) -> Stock: -3
    Everything logged in Stock Ledger.
    """
    login_res = client.post("/api/v1/auth/login", json={
        "email": "alex.manager@example.com",
        "password": "NewSecretPassword@456"
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Category
    cat_res = client.post("/api/v1/categories", json={
        "name": "Metals & Alloys",
        "code": "CAT-METALS",
        "description": "Raw industrial metals"
    }, headers=headers)
    assert cat_res.status_code == 201
    cat_id = cat_res.json()["data"]["id"]

    # 2. Create Product: Steel Rods
    prod_res = client.post("/api/v1/products", json={
        "name": "Steel Rods",
        "sku": "STEEL-ROD-01",
        "category_id": cat_id,
        "uom": "kg",
        "cost_price": 50.0,
        "selling_price": 75.0,
        "min_stock_level": 40.0,
        "max_stock_level": 500.0,
        "reorder_quantity": 100.0
    }, headers=headers)
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["data"]["id"]

    # Fetch locations
    locs = client.get("/api/v1/locations").json()["data"]
    main_store_id = next(l["id"] for l in locs if l["name"] == "Main Store")
    prod_floor_id = next(l["id"] for l in locs if l["name"] == "Production Floor")

    # Step 1 : Receive Goods from Vendor (Receive 100 kg Steel -> Stock: +100)
    receipt_res = client.post("/api/v1/receipts", json={
        "supplier_name": "Tata Steel Ltd",
        "destination_location_id": main_store_id,
        "notes": "Step 1: Raw steel shipment",
        "items": [
            {"product_id": prod_id, "quantity_expected": 100.0, "quantity_received": 100.0}
        ]
    }, headers=headers)
    assert receipt_res.status_code == 201
    receipt_id = receipt_res.json()["data"]["id"]

    # Validate receipt
    val_receipt = client.post(f"/api/v1/receipts/{receipt_id}/validate", headers=headers)
    assert val_receipt.status_code == 200
    assert val_receipt.json()["data"]["status"] == "done"

    # Check product stock: should be 100
    p_check = client.get(f"/api/v1/products/{prod_id}").json()["data"]
    assert p_check["total_stock"] == 100.0

    # Step 2 : Move to production rack (Internal Transfer: Main Store -> Production Floor, 50 kg)
    transfer_res = client.post("/api/v1/transfers", json={
        "source_location_id": main_store_id,
        "destination_location_id": prod_floor_id,
        "notes": "Step 2: Move to production rack",
        "items": [
            {"product_id": prod_id, "quantity": 50.0}
        ]
    }, headers=headers)
    assert transfer_res.status_code == 201
    transfer_id = transfer_res.json()["data"]["id"]

    val_transfer = client.post(f"/api/v1/transfers/{transfer_id}/validate", headers=headers)
    assert val_transfer.status_code == 200
    assert val_transfer.json()["data"]["status"] == "done"

    # Check total stock: unchanged in total (100.0), but location breakdown has 50 in Main Store and 50 in Production Floor
    p_stock_locs = client.get(f"/api/v1/products/{prod_id}/stock").json()["data"]
    stock_by_loc = {s["location_id"]: s["quantity"] for s in p_stock_locs}
    assert stock_by_loc[main_store_id] == 50.0
    assert stock_by_loc[prod_floor_id] == 50.0

    # Step 3 : Deliver finished goods (Deliver 20 steel from Main Store -> Stock: -20)
    del_res = client.post("/api/v1/deliveries", json={
        "customer_name": "Apex Engineering",
        "source_location_id": main_store_id,
        "shipping_address": "88 Industrial Park",
        "notes": "Step 3: Customer delivery",
        "items": [
            {"product_id": prod_id, "quantity_demand": 20.0, "quantity_done": 20.0}
        ]
    }, headers=headers)
    assert del_res.status_code == 201
    del_id = del_res.json()["data"]["id"]

    # Pick & Pack
    client.post(f"/api/v1/deliveries/{del_id}/pick", headers=headers)
    client.post(f"/api/v1/deliveries/{del_id}/pack", headers=headers)

    # Validate delivery
    val_del = client.post(f"/api/v1/deliveries/{del_id}/validate", headers=headers)
    assert val_del.status_code == 200
    assert val_del.json()["data"]["status"] == "done"

    # Check stock: Main Store should now have 30, Production Floor has 50, Total = 80
    p_check3 = client.get(f"/api/v1/products/{prod_id}").json()["data"]
    assert p_check3["total_stock"] == 80.0

    # Step 4 : Adjust damaged items (3 kg steel damaged at Production Floor -> counted=47)
    adj_res = client.post("/api/v1/adjustments", json={
        "product_id": prod_id,
        "location_id": prod_floor_id,
        "counted_quantity": 47.0,
        "reason": "Step 4: 3 kg steel damaged during cutting",
        "auto_validate": True
    }, headers=headers)
    assert adj_res.status_code == 201
    adj_data = adj_res.json()["data"]
    assert adj_data["difference_quantity"] == -3.0
    assert adj_data["status"] == "done"

    # Final Total Stock should be 30 (Main Store) + 47 (Production Floor) = 77
    p_final = client.get(f"/api/v1/products/{prod_id}").json()["data"]
    assert p_final["total_stock"] == 77.0


def test_05_stock_ledger_and_dashboard():
    """Verify Stock Ledger audit trail and Dashboard KPIs & Dynamic filters."""
    # 1. Stock Ledger entries
    ledger_res = client.get("/api/v1/move-history")
    assert ledger_res.status_code == 200
    entries = ledger_res.json()["data"]["items"]
    assert len(entries) >= 4

    types_recorded = {e["move_type"] for e in entries}
    assert "receipt" in types_recorded
    assert "internal_transfer" in types_recorded
    assert "delivery" in types_recorded
    assert "inventory_adjustment" in types_recorded

    # 2. Dashboard KPIs
    kpis_res = client.get("/api/v1/dashboard/kpis")
    assert kpis_res.status_code == 200
    kpi_data = kpis_res.json()["data"]
    assert kpi_data["total_products"] >= 1
    assert kpi_data["total_stock_units"] == 77.0
    assert kpi_data["completed_operations_count"] >= 4

    # 3. Dynamic Filters
    doc_res = client.get("/api/v1/dashboard/documents?document_type=all&status=done")
    assert doc_res.status_code == 200
    docs = doc_res.json()["data"]["items"]
    assert len(docs) >= 3


if __name__ == "__main__":
    pytest.main(["-v", __file__])
