# -*- coding: utf-8 -*-
{
    'name': 'StockSense - Modular Inventory Management System',
    'version': '1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Centralized Inventory Management System for Odoo Hackathon',
    'description': """
StockSense - Inventory Management System
=========================================
Modular Inventory System replacing manual registers and Excel sheets:
- Centralized Inventory Dashboard with KPIs & Charts
- Multi-Warehouse & Multi-Location Stock Management
- Receipts (Incoming Stock Workflow)
- Delivery Orders (Outgoing Stock Workflow)
- Internal Stock Transfers
- Physical Inventory Adjustments
- Immutable Stock Ledger (Audit Log)
- Real-time Low Stock & Out of Stock Alerts
- Role-based Access Control (Warehouse Staff & Inventory Manager)
    """,
    'author': 'StockSense Team',
    'website': 'https://github.com/stocksense',
    'depends': ['base', 'web'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/dashboard_views.xml',
        'views/product_views.xml',
        'views/warehouse_views.xml',
        'views/receipt_views.xml',
        'views/delivery_views.xml',
        'views/transfer_views.xml',
        'views/adjustment_views.xml',
        'views/ledger_views.xml',
        'views/menus.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'stocksense/static/src/css/stocksense.css',
            'stocksense/static/src/js/dashboard.js',
            'stocksense/static/src/xml/dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
