import React, { useState, useEffect } from 'react';
import { ArrowUpRight, Plus, CheckCircle, Search, Trash2, AlertTriangle } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import api from '../api/axios';

const Deliveries = () => {
  const [deliveries, setDeliveries] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [locations, setLocations] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');

  // Modals & Errors
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [validatingDelivery, setValidatingDelivery] = useState(null);
  const [validatingLoading, setValidatingLoading] = useState(false);
  const [validationError, setValidationError] = useState(null);

  // Form State
  const [formData, setFormData] = useState({
    customer_name: '',
    warehouse: '',
    source_location: '',
    date: new Date().toISOString().split('T')[0],
    notes: '',
    items: [{ product: '', quantity: 5 }]
  });

  const [error, setError] = useState('');

  useEffect(() => {
    fetchAuxiliary();
  }, []);

  useEffect(() => {
    fetchDeliveries();
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
      console.error('Error loading auxiliary delivery data:', e);
    }
  };

  const fetchDeliveries = async () => {
    setLoading(true);
    try {
      const params = {};
      if (searchTerm) params.search = searchTerm;
      if (selectedStatus) params.status = selectedStatus;

      const res = await api.get('/deliveries/', { params });
      setDeliveries(res.data.results || res.data || []);
    } catch (e) {
      console.error('Error loading deliveries:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleWarehouseChange = (whId) => {
    setFormData({ ...formData, warehouse: whId, source_location: '' });
  };

  const filteredLocations = locations.filter(l => l.warehouse.toString() === formData.warehouse.toString());

  const handleAddItem = () => {
    setFormData({
      ...formData,
      items: [...formData.items, { product: '', quantity: 5 }]
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

  const handleCreateDelivery = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/deliveries/', formData);
      setShowCreateModal(false);
      resetForm();
      fetchDeliveries();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error creating delivery order.');
    }
  };

  const resetForm = () => {
    setFormData({
      customer_name: '',
      warehouse: '',
      source_location: '',
      date: new Date().toISOString().split('T')[0],
      notes: '',
      items: [{ product: '', quantity: 5 }]
    });
    setError('');
  };

  const handleValidateConfirm = async () => {
    if (!validatingDelivery) return;
    setValidatingLoading(true);
    setValidationError(null);
    try {
      await api.post(`/deliveries/${validatingDelivery.id}/validate_delivery/`);
      setValidatingDelivery(null);
      fetchDeliveries();
    } catch (err) {
      const resp = err.response?.data;
      setValidationError(resp?.details || [resp?.error || 'Validation failed due to stock shortages.']);
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
            <ArrowUpRight className="w-6 h-6 text-purple-400" /> Outbound Delivery Orders
          </h2>
          <p className="text-xs text-slate-400">Process customer shipments & validate stock deductions safely</p>
        </div>

        <button
          onClick={() => { resetForm(); setShowCreateModal(true); }}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-bold flex items-center gap-2 transition shadow-lg shadow-purple-600/30"
        >
          <Plus className="w-4 h-4" /> Create Delivery Order
        </button>
      </div>

      {/* Validation Stock Shortage Error Banner */}
      {validationError && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl space-y-2">
          <div className="flex items-center gap-2 text-rose-400 font-bold text-sm">
            <AlertTriangle className="w-5 h-5" /> Delivery Stock Shortage Error
          </div>
          <ul className="list-disc list-inside text-xs text-rose-300 space-y-1">
            {validationError.map((err, i) => (
              <li key={i}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Filters */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by Delivery Ref, Customer..."
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

      {/* Deliveries Table */}
      <div className="glass-panel rounded-2xl overflow-hidden border border-slate-700/60 shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-800/90 text-xs uppercase font-bold text-slate-400 border-b border-slate-700/60">
              <tr>
                <th className="px-6 py-4">Delivery Ref</th>
                <th className="px-6 py-4">Customer</th>
                <th className="px-6 py-4">Source Location</th>
                <th className="px-6 py-4">Items Included</th>
                <th className="px-6 py-4">Date</th>
                <th className="px-6 py-4 text-center">Status</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan="7" className="text-center py-8 text-slate-500 text-xs">Loading delivery orders...</td>
                </tr>
              ) : deliveries.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-8 text-slate-500 text-xs">No delivery orders found.</td>
                </tr>
              ) : (
                deliveries.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-6 py-4 font-mono font-bold text-purple-400 text-xs">{d.delivery_number}</td>
                    <td className="px-6 py-4 font-medium text-slate-200">{d.customer_name}</td>
                    <td className="px-6 py-4 text-xs">
                      <p className="font-semibold text-slate-300">{d.warehouse_name}</p>
                      <p className="text-[10px] text-slate-500">From ➔ {d.source_location_name}</p>
                    </td>
                    <td className="px-6 py-4 text-xs">
                      {d.items?.map((item, idx) => (
                        <div key={idx} className="text-slate-300">
                          <strong>{item.quantity}</strong>x {item.product_name}
                        </div>
                      ))}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400">{d.date}</td>
                    <td className="px-6 py-4 text-center">
                      <StatusBadge status={d.status} />
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      {d.status !== 'DONE' && d.status !== 'CANCELLED' && (
                        <button
                          onClick={() => { setValidationError(null); setValidatingDelivery(d); }}
                          className="px-3 py-1.5 bg-purple-600/90 hover:bg-purple-500 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 ml-auto shadow"
                        >
                          <CheckCircle className="w-3.5 h-3.5" /> Validate (-Stock)
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

      {/* Create Delivery Order Modal */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="Create Outbound Delivery Order" maxWidth="max-w-3xl">
        {error && <p className="text-xs text-rose-400 p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/30">{error}</p>}
        <form onSubmit={handleCreateDelivery} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Customer / Destination *</label>
              <input
                type="text"
                required
                value={formData.customer_name}
                onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
                placeholder="e.g. Horizon BuildCorp Inc."
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Delivery Date *</label>
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
              <label className="block text-xs font-semibold text-slate-300 mb-1">Source Warehouse *</label>
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
              <label className="block text-xs font-semibold text-slate-300 mb-1">Source Location / Rack *</label>
              <select
                required
                disabled={!formData.warehouse}
                value={formData.source_location}
                onChange={(e) => setFormData({ ...formData, source_location: e.target.value })}
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
                className="text-xs text-purple-400 hover:underline flex items-center gap-1 font-semibold"
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
                      <option key={p.id} value={p.id}>{p.name} ({p.sku}) — Stock: {p.current_stock}</option>
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
            <button type="submit" className="px-4 py-2 text-xs bg-purple-600 font-bold rounded-xl text-white">Save Delivery Order</button>
          </div>
        </form>
      </Modal>

      {/* Validate Confirmation Dialog */}
      <ConfirmDialog
        isOpen={!!validatingDelivery}
        onClose={() => setValidatingDelivery(null)}
        onConfirm={handleValidateConfirm}
        title={`Validate Delivery Order ${validatingDelivery?.delivery_number}`}
        message="Validating will deduct the requested product quantities from the source location. System will verify stock availability first to prevent negative inventory. Proceed?"
        confirmText="Validate & Dispatch Stock"
        confirmStyle="bg-purple-600 hover:bg-purple-500"
        loading={validatingLoading}
      />
    </div>
  );
};

export default Deliveries;
