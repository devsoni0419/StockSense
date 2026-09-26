import React, { useState, useEffect } from 'react';
import { ArrowDownRight, Plus, CheckCircle, XCircle, Search, Trash2, Layers } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import api from '../api/axios';

const Receipts = () => {
  const [receipts, setReceipts] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [locations, setLocations] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');

  // Modals & Action States
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [validatingReceipt, setValidatingReceipt] = useState(null);
  const [validatingLoading, setValidatingLoading] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    supplier_name: '',
    warehouse: '',
    destination_location: '',
    date: new Date().toISOString().split('T')[0],
    notes: '',
    items: [{ product: '', quantity: 10 }]
  });

  const [error, setError] = useState('');

  useEffect(() => {
    fetchAuxiliary();
  }, []);

  useEffect(() => {
    fetchReceipts();
  }, [searchTerm, selectedStatus]);

  const fetchAuxiliary = async () => {
    try {
      const [whRes, locRes, prodRes] = await Promise.all([
        api.get('/warehouses/'),
        api.get('/locations/'),
        api.get('/products/')
      ]);
      setWarehouses(whRes.data.results || whRes.data || []);
      setLocations(locRes.data.results || locRes.data || []);
      setProducts(prodRes.data.results || prodRes.data || []);
    } catch (e) {
      console.error('Error loading auxiliary receipt data:', e);
    }
  };

  const fetchReceipts = async () => {
    setLoading(true);
    try {
      const params = {};
      if (searchTerm) params.search = searchTerm;
      if (selectedStatus) params.status = selectedStatus;

      const res = await api.get('/receipts/', { params });
      setReceipts(res.data.results || res.data || []);
    } catch (e) {
      console.error('Error loading receipts:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleWarehouseChange = (whId) => {
    setFormData({ ...formData, warehouse: whId, destination_location: '' });
  };

  const filteredLocations = locations.filter(l => l.warehouse.toString() === formData.warehouse.toString());

  const handleAddItem = () => {
    setFormData({
      ...formData,
      items: [...formData.items, { product: '', quantity: 10 }]
    });
  };

  const handleRemoveItem = (index) => {
    const newItems = formData.items.filter((_, i) => i !== index);
    setFormData({ ...formData, items: newItems });
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index][field] = value;
    setFormData({ ...formData, items: newItems });
  };

  const handleCreateReceipt = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/receipts/', formData);
      setShowCreateModal(false);
      resetForm();
      fetchReceipts();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error creating receipt order.');
    }
  };

  const resetForm = () => {
    setFormData({
      supplier_name: '',
      warehouse: '',
      destination_location: '',
      date: new Date().toISOString().split('T')[0],
      notes: '',
      items: [{ product: '', quantity: 10 }]
    });
    setError('');
  };

  const handleValidateConfirm = async () => {
    if (!validatingReceipt) return;
    setValidatingLoading(true);
    try {
      await api.post(`/receipts/${validatingReceipt.id}/validate_receipt/`);
      setValidatingReceipt(null);
      fetchReceipts();
    } catch (err) {
      alert(err.response?.data?.error || 'Validation failed.');
    } finally {
      setValidatingLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-5 rounded-2xl">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <ArrowDownRight className="w-6 h-6 text-emerald-400" /> Incoming Stock Receipts
          </h2>
          <p className="text-xs text-slate-400">Manage supplier purchase receipts & inbound warehouse stock validation</p>
        </div>

        <button
          onClick={() => { resetForm(); setShowCreateModal(true); }}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold flex items-center gap-2 transition shadow-lg shadow-emerald-600/30"
        >
          <Plus className="w-4 h-4" /> Create Receipt
        </button>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by Receipt Number, Supplier..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100"
          />
        </div>

        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-200"
        >
          <option value="">All Statuses</option>
          <option value="DRAFT">Draft</option>
          <option value="WAITING">Waiting</option>
          <option value="READY">Ready</option>
          <option value="DONE">Done (Validated)</option>
          <option value="CANCELLED">Cancelled</option>
        </select>
      </div>

      {/* Receipts Table */}
      <div className="glass-panel rounded-2xl overflow-hidden border border-slate-700/60 shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-800/90 text-xs uppercase font-bold text-slate-400 border-b border-slate-700/60">
              <tr>
                <th className="px-6 py-4">Receipt Ref</th>
                <th className="px-6 py-4">Supplier</th>
                <th className="px-6 py-4">Destination</th>
                <th className="px-6 py-4">Items Included</th>
                <th className="px-6 py-4">Date</th>
                <th className="px-6 py-4 text-center">Status</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan="7" className="text-center py-8 text-slate-500 text-xs">Loading receipt orders...</td>
                </tr>
              ) : receipts.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-8 text-slate-500 text-xs">No receipts found.</td>
                </tr>
              ) : (
                receipts.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-6 py-4 font-mono font-bold text-indigo-400 text-xs">{r.receipt_number}</td>
                    <td className="px-6 py-4 font-medium text-slate-200">{r.supplier_name}</td>
                    <td className="px-6 py-4 text-xs">
                      <p className="font-semibold text-slate-300">{r.warehouse_name}</p>
                      <p className="text-[10px] text-slate-500">➔ {r.destination_location_name}</p>
                    </td>
                    <td className="px-6 py-4 text-xs">
                      {r.items?.map((item, idx) => (
                        <div key={idx} className="text-slate-300">
                          <strong>{item.quantity}</strong>x {item.product_name}
                        </div>
                      ))}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400">{r.date}</td>
                    <td className="px-6 py-4 text-center">
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      {r.status !== 'DONE' && r.status !== 'CANCELLED' && (
                        <button
                          onClick={() => setValidatingReceipt(r)}
                          className="px-3 py-1.5 bg-emerald-600/90 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 ml-auto shadow"
                        >
                          <CheckCircle className="w-3.5 h-3.5" /> Validate (+Stock)
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Receipt Modal */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="Create Inbound Stock Receipt" maxWidth="max-w-3xl">
        {error && <p className="text-xs text-rose-400 p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/30">{error}</p>}
        <form onSubmit={handleCreateReceipt} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Supplier Name *</label>
              <input
                type="text"
                required
                value={formData.supplier_name}
                onChange={(e) => setFormData({ ...formData, supplier_name: e.target.value })}
                placeholder="e.g. Apex Steel Suppliers Ltd."
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Receipt Date *</label>
              <input
                type="date"
                required
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Target Warehouse *</label>
              <select
                required
                value={formData.warehouse}
                onChange={(e) => handleWarehouseChange(e.target.value)}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-200"
              >
                <option value="">Select Warehouse</option>
                {warehouses.map((w) => (
                  <option key={w.id} value={w.id}>{w.name} ({w.code})</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Destination Location / Rack *</label>
              <select
                required
                disabled={!formData.warehouse}
                value={formData.destination_location}
                onChange={(e) => setFormData({ ...formData, destination_location: e.target.value })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-200 disabled:opacity-50"
              >
                <option value="">Select Location</option>
                {filteredLocations.map((l) => (
                  <option key={l.id} value={l.id}>{l.name} ({l.code})</option>
                ))}
              </select>
            </div>
          </div>

          {/* Line Items */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Products & Quantities</h4>
              <button
                type="button"
                onClick={handleAddItem}
                className="text-xs text-indigo-400 hover:underline flex items-center gap-1 font-semibold"
              >
                <Plus className="w-3.5 h-3.5" /> Add Another Line Item
              </button>
            </div>

            {formData.items.map((item, index) => (
              <div key={index} className="flex items-center gap-3 p-3 bg-slate-900 rounded-xl border border-slate-800">
                <div className="flex-1">
                  <select
                    required
                    value={item.product}
                    onChange={(e) => handleItemChange(index, 'product', e.target.value)}
                    className="w-full px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-xs text-slate-100"
                  >
                    <option value="">Select Product</option>
                    {products.map((p) => (
                      <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>
                    ))}
                  </select>
                </div>

                <div className="w-28">
                  <input
                    type="number"
                    min="1"
                    required
                    value={item.quantity}
                    onChange={(e) => handleItemChange(index, 'quantity', parseInt(e.target.value) || 1)}
                    className="w-full px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-xs text-slate-100"
                  />
                </div>

                {formData.items.length > 1 && (
                  <button
                    type="button"
                    onClick={() => handleRemoveItem(index)}
                    className="p-1 text-slate-500 hover:text-rose-400 transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-700">
            <button type="button" onClick={() => setShowCreateModal(false)} className="px-4 py-2 text-xs border border-slate-700 rounded-xl">Cancel</button>
            <button type="submit" className="px-4 py-2 text-xs bg-emerald-600 font-bold rounded-xl text-white">Save Receipt</button>
          </div>
        </form>
      </Modal>

      {/* Validate Confirmation Dialog */}
      <ConfirmDialog
        isOpen={!!validatingReceipt}
        onClose={() => setValidatingReceipt(null)}
        onConfirm={handleValidateConfirm}
        title={`Validate Inbound Receipt ${validatingReceipt?.receipt_number}`}
        message="Validating this receipt will immediately increase product stock levels at the destination location, generate Stock Ledger audit records, and broadcast live WebSocket dashboard updates. Proceed?"
        confirmText="Validate & Add Stock"
        confirmStyle="bg-emerald-600 hover:bg-emerald-500"
        loading={validatingLoading}
      />
    </div>
  );
};

export default Receipts;
