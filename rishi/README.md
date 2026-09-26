# StockSense - Modern Inventory Management System (IMS) API

> Built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**. Complete REST API implementation based on the StockSense problem statement.

---

## 📋 Overview

**StockSense** digitizes and streamlines enterprise stock operations to replace manual registers, spreadsheets, and fragmented tracking systems with a real-time, centralized, modular application.

### Target Personas
- **Inventory Managers**: Manage incoming receipts, outgoing shipments, replenishment, and reordering rules.
- **Warehouse Staff**: Execute picking, packing, internal warehouse transfers, shelving, and physical counting adjustments.

---

## 🚀 Key Features

1. **Authentication & Profile Management**:
   - JWT-based authentication with role-based access control (`inventory_manager`, `warehouse_staff`, `admin`).
   - OTP-based password reset flow (Request OTP -> Verify OTP -> Reset Password).
   - Profile retrieval and update endpoints.

2. **Dashboard & Real-Time KPIs**:
   - Total products registered & total units in stock.
   - Low stock alerts & out-of-stock items count.
   - Pending operations counters (Receipts, Deliveries, Internal Transfers).
   - Dynamic multi-filter engine: filter documents by document type, status (`draft`, `waiting`, `ready`, `done`, `canceled`), warehouse, location, and product category.

3. **Product Management & Reordering Rules**:
   - Product creation with SKU, Unit of Measure (UoM), Category, and optional initial stock.
   - Real-time stock breakdown per warehouse and location.
   - Automated reordering rules: `min_stock_level`, `max_stock_level`, and `reorder_quantity`.
   - Dedicated low-stock alerts endpoint.

4. **Operations**:
   - **Receipts (Incoming Stock)**: Vendor receipt creation, line item reception, and automatic stock increment on validation.
   - **Delivery Orders (Outgoing Stock)**: Customer order dispatch with picking (`waiting`), packing (`ready`), and validation (`done`) reducing on-hand inventory.
   - **Internal Transfers**: Stock transfer across locations/warehouses (e.g. Main Store → Production Floor, Rack A → Rack B) maintaining enterprise stock totals.
   - **Stock Adjustments**: Fix mismatches between recorded stock and physical count (e.g., 3 kg damaged steel written off with delta recorded).
   - **Move History / Stock Ledger**: Immutable audit ledger recording every single stock movement across the enterprise.

5. **Settings (Multi-Warehouse & Locations)**:
   - Multi-warehouse configuration (e.g., Main Warehouse, Warehouse 2).
   - Multi-location hierarchy (Main Store, Production Floor, Rack A, Rack B, Transit, etc.).

---

## 🛠️ Project Structure

All files reside strictly inside the `rishi/` folder:

```text
rishi/
├── .env                  # Environment variables & PostgreSQL database URL
├── .env.example          # Environment template reference
├── requirements.txt      # Python dependencies
├── main.py               # FastAPI application entrypoint & health check
├── seed_data.py          # Demo data seeding script
├── test_api.py           # Automated test suite (100% passing)
├── README.md             # Documentation
└── app/
    ├── config.py         # Pydantic Settings configuration loader
    ├── database.py       # SQLAlchemy engine, session maker, Base, and init_db
    ├── api/
    │   ├── deps.py       # Auth dependencies (get_current_user, require_role)
    │   └── v1/           # API Routers
    │       ├── auth.py          # Authentication, OTP, & profile
    │       ├── products.py      # Products, stock per location, alerts
    │       ├── categories.py    # Product categories
    │       ├── warehouses.py    # Warehouses
    │       ├── locations.py     # Locations and racks
    │       ├── receipts.py      # Incoming goods receipts
    │       ├── deliveries.py    # Customer delivery orders
    │       ├── transfers.py     # Internal stock transfers
    │       ├── adjustments.py   # Inventory reconciliation adjustments
    │       ├── move_history.py  # Stock Ledger audit trail
    │       └── dashboard.py     # KPIs & dynamic multi-filter documents
    ├── models/           # SQLAlchemy 2.0 ORM models
    │   ├── user.py
    │   ├── category.py
    │   ├── warehouse.py
    │   ├── location.py
    │   ├── product.py
    │   ├── receipt.py
    │   ├── delivery.py
    │   ├── transfer.py
    │   ├── adjustment.py
    │   └── move_history.py
    ├── schemas/          # Pydantic V2 schemas & DTOs
    ├── services/         # Core business logic
    │   ├── stock_service.py     # Stock movement, transfer, adjustment, & ledger engine
    │   └── otp_service.py       # OTP generation and verification
    └── utils/
        └── security.py          # Bcrypt hashing & PyJWT tokens
```

---

## ⚙️ Configuration (.env)

Configure your settings in `c:/rishi/rishi/StockSense/rishi/.env`:

```ini
# PostgreSQL Database URL (paste your PostgreSQL URL here)
# Supports postgresql+psycopg:// or postgresql://
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/stocksense_db

# Security
SECRET_KEY=stocksense-super-secure-production-jwt-secret-key-replace-in-production-2026
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# App Settings
PROJECT_NAME="StockSense - Modern Inventory Management System"
API_V1_PREFIX=/api/v1
ENVIRONMENT=development
DEBUG=True

# OTP & Alerts
OTP_EXPIRE_MINUTES=10
DEFAULT_LOW_STOCK_THRESHOLD=10
CORS_ORIGINS=["*"]
```

---

## 🚀 Running the Application

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Database
Paste your PostgreSQL connection string into `.env`:
```ini
DATABASE_URL=postgresql+psycopg://<your_user>:<your_password>@<your_host>:5432/<your_dbname>
```
*Note: The application automatically creates all tables on startup via `init_db()`.*

### 3. (Optional) Seed Demo Data
To populate sample warehouses, locations, categories, products (Steel Rods, Chairs, Frames, Screws), and test users:
```bash
python seed_data.py
```

**Default Test Accounts**:
| Role | Email | Password |
| :--- | :--- | :--- |
| **Inventory Manager** | `manager@stocksense.com` | `Manager@123` |
| **Warehouse Staff** | `staff@stocksense.com` | `Staff@123` |
| **Administrator** | `admin@stocksense.com` | `Admin@123` |

### 4. Start FastAPI Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# or:
python main.py
```

### 5. Interactive API Documentation
Open your browser to explore the Swagger UI:
- **Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/](http://localhost:8000/)

---

## 🧪 Running Automated Tests

Run the test suite:
```bash
python -m pytest test_api.py -v
```

All 5 core test suites pass seamlessly:
1. `test_01_health_check`
2. `test_02_auth_flow` (Signup, Login, Me, OTP Request, OTP Verification, Password Reset)
3. `test_03_settings_warehouses_and_locations`
4. `test_04_inventory_lifecycle_from_pdf` (Exact 4-step flow: Receive 100 kg steel -> Transfer 50 kg to Production Floor -> Deliver 20 steel -> Adjust 3 kg damaged steel)
5. `test_05_stock_ledger_and_dashboard` (Stock Ledger audit trail, KPI calculations, and dynamic filters)

---

## 📖 API Endpoints Reference

### 🔐 Authentication (`/api/v1/auth`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/signup` | Register a new user |
| `POST` | `/api/v1/auth/login` | Login and obtain JWT token |
| `POST` | `/api/v1/auth/forgot-password` | Request 6-digit password reset OTP |
| `POST` | `/api/v1/auth/verify-otp` | Verify validity of OTP code |
| `POST` | `/api/v1/auth/reset-password` | Reset password using verified OTP |
| `GET` | `/api/v1/auth/me` | Get current user profile |
| `PUT` | `/api/v1/auth/me` | Update profile information |
| `POST` | `/api/v1/auth/logout` | Logout |

### 📊 Dashboard (`/api/v1/dashboard`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/dashboard/kpis` | Real-time KPIs: stock units, low stock, pending receipts/deliveries |
| `GET` | `/api/v1/dashboard/documents` | Dynamic multi-filter: by doc type, status, warehouse, category, etc. |

### 📦 Products (`/api/v1/products`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/products` | List products with SKU search, category, low stock filter |
| `POST` | `/api/v1/products` | Create product with optional initial stock & reorder rules |
| `GET` | `/api/v1/products/alerts/low-stock` | Retrieve all items currently below reorder levels |
| `GET` | `/api/v1/products/{id}` | Product details with stock breakdown per warehouse & location |
| `GET` | `/api/v1/products/{id}/stock` | Stock availability per location for a specific product |
| `PUT` | `/api/v1/products/{id}` | Update product information & reordering rules |
| `DELETE` | `/api/v1/products/{id}` | Soft delete / deactivate product |

### 📥 Receipts / Incoming Stock (`/api/v1/receipts`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/receipts` | List incoming receipts with status/supplier filters |
| `POST` | `/api/v1/receipts` | Create new incoming receipt (vendor, destination, line items) |
| `GET` | `/api/v1/receipts/{id}` | Get receipt details and items |
| `PUT` | `/api/v1/receipts/{id}` | Edit draft receipt |
| `POST` | `/api/v1/receipts/{id}/validate` | **Validate receipt**: increases stock & logs in Stock Ledger |
| `POST` | `/api/v1/receipts/{id}/cancel` | Cancel receipt |

### 📤 Delivery Orders / Outgoing Stock (`/api/v1/deliveries`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/deliveries` | List outgoing customer delivery orders |
| `POST` | `/api/v1/deliveries` | Create delivery order |
| `GET` | `/api/v1/deliveries/{id}` | Get delivery order details |
| `PUT` | `/api/v1/deliveries/{id}` | Edit draft delivery order |
| `POST` | `/api/v1/deliveries/{id}/pick` | Mark order items as picked (`waiting`) |
| `POST` | `/api/v1/deliveries/{id}/pack` | Mark order items as packed (`ready`) |
| `POST` | `/api/v1/deliveries/{id}/validate` | **Validate delivery**: decreases stock & logs in Stock Ledger |
| `POST` | `/api/v1/deliveries/{id}/cancel` | Cancel delivery order |

### 🔄 Internal Transfers (`/api/v1/transfers`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/transfers` | List internal transfers |
| `POST` | `/api/v1/transfers` | Create transfer request (source loc -> dest loc) |
| `GET` | `/api/v1/transfers/{id}` | Get transfer details |
| `PUT` | `/api/v1/transfers/{id}` | Update transfer before validation |
| `POST` | `/api/v1/transfers/{id}/validate` | **Validate transfer**: moves stock between locations |
| `POST` | `/api/v1/transfers/{id}/cancel` | Cancel transfer |

### ⚖️ Stock Adjustments (`/api/v1/adjustments`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/adjustments` | List stock reconciliation adjustments |
| `POST` | `/api/v1/adjustments` | Create adjustment with recorded vs counted count & auto-validate |
| `GET` | `/api/v1/adjustments/{id}` | Get adjustment details |
| `POST` | `/api/v1/adjustments/{id}/validate` | Validate draft adjustment and reconcile inventory |
| `POST` | `/api/v1/adjustments/{id}/cancel` | Cancel draft adjustment |

### 📜 Move History & Stock Ledger (`/api/v1/move-history`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/move-history` | Paginated immutable audit ledger of every stock movement |

### 🏷️ Categories & Settings (`/api/v1/categories`, `/warehouses`, `/locations`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET/POST` | `/api/v1/categories` | Manage product categories |
| `GET/POST` | `/api/v1/warehouses` | Multi-warehouse management |
| `GET/POST` | `/api/v1/locations` | Warehouse locations/zones/racks |
