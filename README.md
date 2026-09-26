# StockSense — Enterprise Inventory Management System

**StockSense** is a full-stack, real-time Inventory Management System built for the Odoo Hackathon. It features multi-warehouse tracking, location-level stock control, automated incoming receipts, outbound delivery validation with negative stock prevention, internal stock transfers, physical count adjustments, immutable stock ledgers, low-stock background alerts (Celery + Redis), and real-time WebSocket dashboard telemetry (Django Channels).

---

## 🚀 Tech Stack

### Frontend
- **Framework**: React.js (Vite)
- **Styling**: Tailwind CSS + Glassmorphism Dark/Light Theme
- **Routing**: React Router DOM (v6)
- **HTTP Client**: Axios (with JWT refresh interceptor)
- **Data Visualization**: Recharts (Stock movement timeline, Low stock bar chart, Warehouse distribution donut chart)
- **Iconography**: Lucide Icons
- **Real-Time**: Native WebSocket API

### Backend
- **Framework**: Python 3.10+ & Django 4.2
- **API Engine**: Django REST Framework (DRF)
- **Authentication**: JWT (`djangorestframework-simplejwt`) + OTP-based password reset
- **Real-Time WebSockets**: Django Channels (ASGI + Daphne)
- **Background Jobs**: Celery (Periodic low-stock audits)
- **Message Broker & Cache**: Redis
- **Database**: PostgreSQL (with graceful fallback to SQLite for instant local execution)

---

## 📁 Architecture Overview

```
StockSense/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── stocksense/            # Main Django configuration & ASGI/WS routing
│   └── apps/
│       ├── authentication/    # JWT Auth, Roles (Manager/Staff), OTP Password Reset
│       ├── products/          # Products, Categories, SKU/Barcode, Reorder thresholds
│       ├── warehouses/        # Multi-warehouse & Location Racks/Zones hierarchy
│       ├── inventory/         # Stock balances per location
│       ├── receipts/          # Inbound purchase receipts workflow (Draft -> Done)
│       ├── deliveries/        # Outbound delivery workflow with stock shortage prevention
│       ├── transfers/         # Internal transfers (Rack A -> Production Floor)
│       ├── adjustments/       # Physical inventory audit corrections
│       ├── ledger/            # Immutable stock ledger history & CSV Exporter
│       ├── dashboard/         # Real-time KPI metrics & Recharts data endpoints
│       └── notifications/     # Low stock & Out of stock alerts + Celery task
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── api/               # Axios instance with JWT interceptors
│       ├── context/           # AuthContext, ThemeContext, SocketContext
│       ├── components/        # Layout, Sidebar, Navbar, StatCard, StatusBadge, Modals
│       └── pages/             # Dashboard, Products, Warehouses, Receipts, Deliveries, Transfers, Adjustments, StockLedger, Settings
└── README.md
```

---

## ⚡ Quick Start & Local Setup Instructions

### Prerequisites
- **Python**: 3.10 or higher
- **Node.js**: v18 or higher & `npm`
- **PostgreSQL**: (Optional, default settings fallback to local SQLite for zero-config dev)
- **Redis**: (Optional, Channels falls back to InMemoryChannelLayer if Redis is offline)

---

### Step 1: Backend Setup (Django REST Framework)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create environment file:
   ```bash
   cp .env.example .env
   ```
   *(To use SQLite locally without setting up PostgreSQL, set `USE_SQLITE=True` in `.env`)*

5. Run Database Migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. Seed Database with Realistic Demo Data:
   ```bash
   python manage.py seed_data
   ```

7. Start the Django Server (ASGI/Daphne with WebSockets):
   ```bash
   python manage.py runserver
   ```
   *The backend server will run at `http://127.0.0.1:8000/`.*

---

### Step 2: Celery Background Worker (Optional for Background Alerts)

In a separate terminal window:
```bash
cd backend
# Windows
celery -A stocksense worker --pool=solo -l info

# Linux/macOS
celery -A stocksense worker -l info
```

---

### Step 3: Frontend Setup (React.js + Vite)

In a separate terminal window:
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *The React web application will be available at `http://localhost:5173/`.*

---

## 🔑 Hackathon Demo Credentials

Use the following quick-login credentials on the Login screen:

| Role | Email | Password | Access Rights |
| :--- | :--- | :--- | :--- |
| **Inventory Manager** | `admin@stocksense.com` | `admin123` | Full access: CRUD products, reorder thresholds, warehouses, receipts, deliveries, transfers, adjustments & ledger CSV export |
| **Warehouse Staff** | `staff@stocksense.com` | `staff123` | Operations access: View products, validate receipts, deliveries & internal transfers |

---

## 🎯 End-to-End Hackathon Demo Flow

Follow this exact scenario to demonstrate all StockSense core capabilities:

1. **Login as Inventory Manager**:
   - Open `http://localhost:5173/login`. Click **"Manager Demo"** quick button and sign in.
2. **Open Dashboard**:
   - Observe live KPIs (Total Products, Stock Units, Low Stock Items, Pending Receipts/Deliveries).
3. **Create a New Product**:
   - Go to **Products** page -> click **"+ Add Product"**.
   - Name: `Titanium Bolts (10mm)`, SKU: `RAW-TTN-099`, Unit: `pcs`, Initial Stock: `100`, Reorder Level: `25`.
4. **Create & Validate an Inbound Receipt (+100 Stock)**:
   - Go to **Receipts** -> click **"+ Create Receipt"**.
   - Supplier: `Titanium Forge Corp`, Target Warehouse: `Main Warehouse (MWH)`, Destination: `Rack A`. Add 100 Titanium Bolts.
   - Click **"Validate (+Stock)"**.
   - Observe immediate toast alert and real-time stock increase to 200.
5. **Transfer 40 Units to Production Floor**:
   - Go to **Transfers** -> click **"+ Schedule Transfer"**.
   - Source: `Main Warehouse -> Rack A`, Destination: `Main Warehouse -> Production Floor`. Quantity: `40`.
   - Click **"Validate Move"**.
   - Verify Rack A has 160 units, Production Floor has 40 units, total product stock remains 200.
6. **Create Outbound Delivery (-20 Units)**:
   - Go to **Deliveries** -> click **"+ Create Delivery Order"**.
   - Customer: `Aerospace Dynamics`, Warehouse: `Main Warehouse`, Source Location: `Production Floor`. Quantity: `20`.
   - Click **"Validate (-Stock)"**. Stock on Production Floor decreases from 40 to 20.
7. **Perform Physical Inventory Adjustment (-3 Damaged)**:
   - Go to **Adjustments** -> click **"+ Create Stock Adjustment"**.
   - Product: `Titanium Bolts`, Location: `Rack A`, Counted Quantity: `157` (System was 160, Difference: -3). Reason: `Damaged Goods`.
   - Click **"Validate Adjustment"**.
8. **Inspect Stock Ledger**:
   - Go to **Stock Ledger**. Observe the complete immutable history of all 4 movements (Receipt, Transfer, Delivery, Adjustment). Click **"Export Ledger CSV"** to download the audit spreadsheet.
9. **Low Stock Alerts & Real-Time Updates**:
   - Set reorder level higher than current stock to trigger low-stock banner and WebSocket live updates across connected clients.

---

## 🛠 Database Schema Highlights

- `User`: Custom user model with `role` (`MANAGER` / `STAFF`) and OTP model `PasswordResetOTP`.
- `Category` & `Product`: Categorized catalog with SKU index, barcode, unit of measure, initial stock, current stock, and reorder levels.
- `Warehouse` & `Location`: Hierarchical facility modeling (`Warehouse` ➔ `Location` e.g., Storage Rack, Production Floor, Shipping Bay).
- `Stock`: Unique balance per `(product, location)`.
- `Receipt` & `ReceiptItem`: Inbound shipment workflow.
- `Delivery` & `DeliveryItem`: Outbound order dispatch with atomic row locking (`select_for_update`) to prevent negative inventory.
- `InternalTransfer` & `TransferItem`: Intra-facility location movements.
- `InventoryAdjustment`: Audit count corrections with automatic difference calculations.
- `StockLedger`: Immutable, append-only historical audit trail.
- `Notification`: Low stock and out-of-stock alert logs.

---

## 📜 License
StockSense is created for the Odoo Hackathon 2026. All rights reserved.
