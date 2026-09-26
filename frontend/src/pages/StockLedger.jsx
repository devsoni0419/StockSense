import React, { useState, useEffect } from 'react';
import { History, Download, Search, Filter } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import api from '../api/axios';

const StockLedger = () => {
  const [ledgerEntries, setLedgerEntries] = useState([]);
  const [products, setProducts] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedMovementType, setSelectedMovementType] = useState('');
  const [selectedProduct, setSelectedProduct] = useState('');
  const [selectedWarehouse, setSelectedWarehouse] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  useEffect(() => {
    fetchAuxiliary();
  }, []);

  useEffect(() => {
    fetchLedger();
  }, [searchTerm, selectedMovementType, selectedProduct, selectedWarehouse, startDate, endDate]);

  const fetchAuxiliary = async () => {
    try {
      const [prodRes, whRes] = await Promise.all([
        api.get('/products/'),
        api.get('/warehouses/')
      ]);
      setProducts(prodRes.data.results || prodRes.data || []);
      setWarehouses(whRes.data.results || whRes.data || []);
    } catch (e) {
      console.error('Error fetching auxiliary ledger data:', e);
    }
  };

  const fetchLedger = async () => {
    setLoading(true);
    try {
      const params = {};
      if (searchTerm) params.search = searchTerm;
      if (selectedMovementType) params.movement_type = selectedMovementType;
      if (selectedProduct) params.product = selectedProduct;
      if (selectedWarehouse) params.warehouse = selectedWarehouse;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const res = await api.get('/ledger/', { params });
      setLedgerEntries(res.data.results || res.data || []);
    } catch (e) {
      console.error('Error fetching stock ledger:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = () => {
    const params = new URLSearchParams();
    if (searchTerm) params.append('search', searchTerm);
    if (selectedMovementType) params.append('movement_type', selectedMovementType);
    if (selectedProduct) params.append('product', selectedProduct);
    if (selectedWarehouse) params.append('warehouse', selectedWarehouse);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const downloadUrl = `/api/ledger/export_csv/?${params.toString()}`;
    window.open(downloadUrl, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-5 rounded-2xl">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <History className="w-6 h-6 text-indigo-400" /> Immutable Stock Ledger History
          </h2>
          <p className="text-xs text-slate-400">Complete double-entry audit trail of every stock movement across the enterprise</p>
        </div>

        <button
          onClick={handleExportCSV}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold flex items-center gap-2 transition shadow-lg shadow-indigo-600/30"
        >
          <Download className="w-4 h-4" /> Export Ledger CSV
        </button>
      </div>

      {/* Filter Bar Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {/* Search */}
        <div className="relative col-span-1 sm:col-span-2">
          <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search Reference, SKU, User..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-100"
          />
        </div>

        {/* Movement Type */}
        <select
          value={selectedMovementType}
          onChange={(e) => setSelectedMovementType(e.target.value)}
          className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-200"
        >
          <option value="">All Movement Types</option>
          <option value="RECEIPT">Receipt (+Stock)</option>
          <option value="DELIVERY">Delivery (-Stock)</option>
          <option value="INTERNAL_TRANSFER">Internal Transfer</option>
          <option value="ADJUSTMENT">Adjustment</option>
        </select>

        {/* Product Filter */}
        <select
          value={selectedProduct}
          onChange={(e) => setSelectedProduct(e.target.value)}
          className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-200"
        >
          <option value="">All Products</option>
          {products.map((p) => (
            <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>
          ))}
        </select>

        {/* Warehouse Filter */}
        <select
          value={selectedWarehouse}
          onChange={(e) => setSelectedWarehouse(e.target.value)}
          className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-200"
        >
          <option value="">All Warehouses</option>
          {warehouses.map((w) => (
            <option key={w.id} value={w.id}>{w.name} ({w.code})</option>
          ))}
        </select>
      </div>

      {/* Date Range Row */}
      <div className="flex flex-wrap items-center gap-3 glass-panel p-3.5 rounded-xl border border-slate-800 text-xs">
        <span className="font-semibold text-slate-400 flex items-center gap-1">
          <Filter className="w-3.5 h-3.5 text-indigo-400" /> Date Range Filter:
        </span>
        <input
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          className="px-3 py-1 bg-slate-900 border border-slate-700 rounded-lg text-slate-200"
        />
        <span className="text-slate-500">to</span>
        <input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          className="px-3 py-1 bg-slate-900 border border-slate-700 rounded-lg text-slate-200"
        />
        {(startDate || endDate) && (
          <button
            onClick={() => { setStartDate(''); setEndDate(''); }}
            className="text-indigo-400 hover:underline ml-auto font-semibold"
          >
            Clear Dates
          </button>
        )}
      </div>

      {/* Ledger Table */}
      <div className="glass-panel rounded-2xl overflow-hidden border border-slate-700/60 shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-800/90 text-xs uppercase font-bold text-slate-400 border-b border-slate-700/60">
              <tr>
                <th className="px-6 py-4">Timestamp</th>
                <th className="px-6 py-4">Reference</th>
                <th className="px-6 py-4">Product</th>
                <th className="px-6 py-4">Movement Type</th>
                <th className="px-6 py-4">Source Location</th>
                <th className="px-6 py-4">Destination Location</th>
                <th className="px-6 py-4 text-center">Quantity</th>
                <th className="px-6 py-4">User</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan="8" className="text-center py-8 text-slate-500 text-xs">Loading ledger entries...</td>
                </tr>
              ) : ledgerEntries.length === 0 ? (
                <tr>
                  <td colSpan="8" className="text-center py-8 text-slate-500 text-xs">No stock movement logs found.</td>
                </tr>
              ) : (
                ledgerEntries.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-6 py-4 text-xs font-mono text-slate-400">
                      {new Date(l.date).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 font-mono font-bold text-indigo-400 text-xs">{l.reference}</td>
                    <td className="px-6 py-4">
                      <p className="font-bold text-slate-200">{l.product_name}</p>
                      <p className="text-[10px] font-mono text-slate-500">{l.product_sku}</p>
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={l.movement_type} />
                    </td>
                    <td className="px-6 py-4 text-xs font-medium text-slate-400">
                      {l.source_location_name ? `${l.source_warehouse_name} / ${l.source_location_name}` : '—'}
                    </td>
                    <td className="px-6 py-4 text-xs font-medium text-slate-400">
                      {l.destination_location_name ? `${l.destination_warehouse_name} / ${l.destination_location_name}` : '—'}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`font-extrabold text-sm ${l.quantity > 0 ? 'text-emerald-400' : l.quantity < 0 ? 'text-rose-400' : 'text-slate-300'}`}>
                        {l.quantity > 0 ? `+${l.quantity}` : l.quantity}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-300 font-semibold">{l.user_name}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default StockLedger;
