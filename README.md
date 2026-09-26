# 📦 StockSense — Centralized Inventory Management System (Odoo Custom Module)

> **Built for Odoo Hackathon 2026**

StockSense is a modular, native Odoo custom module designed to replace paper registers and Excel spreadsheets with a real-time, centralized inventory control system.

---

## ✨ Features

- 📊 **Control Center Dashboard**: KPIs for Total Stock, Low Stock, Out of Stock, Pending Receipts, Deliveries, and Transfers.
- 📦 **Product Management**: SKU tracking, categories, unit of measure, price, and reorder levels.
- 🏬 **Multi-Warehouse & Locations**: Multi-warehouse hierarchy (`Main Warehouse / Rack A / Shelf 1`) with location quants.
- 🚚 **Incoming Stock (Receipts)**: `Draft` → `Ready` → `Done` workflow with automatic location stock updates.
- 📤 **Outgoing Stock (Deliveries)**: `Draft` → `Ready` → `Done` workflow with server-side negative stock prevention.
- 🔄 **Internal Transfers**: Relocate stock between internal locations while preserving company stock balance.
- 🛠️ **Physical Inventory Adjustments**: Reconcile physical counts vs system counts with discrepancy tracking (damaged, lost, audit variance).
- 📜 **Immutable Stock Ledger**: Read-only audit log of every stock movement with strict ORM immutability.
- 🔔 **Low Stock & Out of Stock Alerts**: Real-time alerts when stock reaches reorder level or zero.
- 🔒 **Role-Based Access Control**: Configured security groups for Warehouse Staff and Inventory Managers.

---

## 📂 Project Structure

```text
StockSense/
└── stocksense/
    ├── __init__.py
    ├── __manifest__.py
    ├── models/
    ├── views/
    ├── security/
    ├── static/
    └── data/
```

---

## 🚀 Quick Setup & Installation

1. Copy the `stocksense` folder into your Odoo `addons` path.
2. Restart your local Odoo server.
3. Enable **Developer Mode** in Odoo.
4. Go to **Apps** -> **Update Apps List**.
5. Search for `StockSense` and click **Install**.

---

## 📜 Hackathon Presentation Walkthrough
Refer to [`stocksense/HACKATHON_DEMO_GUIDE.md`](file:///c:/Users/devso/StockSense/stocksense/HACKATHON_DEMO_GUIDE.md) for the complete 14-step presentation script.
