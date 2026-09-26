import React, { useState, useEffect } from 'react';
import { Repeat, Plus, CheckCircle, Search, Trash2, ArrowRight } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import api from '../api/axios';

const Transfers = () => {
  const [transfers, setTransfers] = useState([]);
  const [locations, setLocations] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');

  // Modals & Action
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [validatingTransfer, setValidatingTransfer] = useState(null);
  const [validatingLoading, setValidatingLoading] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    source_location: '',
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
    fetchTransfers();
  }, [searchTerm, selectedStatus]);

  const fetchAuxiliary = async () => {
    try {
      const [locRes, prodRes] = await Promise.all([
        api.get('/locations/'),
        api.get('/products/')
      ]);
      setLocations(locRes.data.results || locRes.data || []);
      setProducts(prodRes.data.results || prodRes.data || []);
    } catch (e) {
      console.error('Error loading auxiliary transfer data:', e);
    }
  };

  const fetchTransfers = async () => {
    setLoading(true);
    try {
      const params = {};
      if (searchTerm) params.search = searchTerm;
      if (selectedStatus) params.status = selectedStatus;

      const res = await api.get('/transfers/', { params });
      setTransfers(res.data.results || res.data || []);
    } catch (e) {
      console.error('Error loading transfers:', e);
    } finally {
      setLoading(false);
    }
  };

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

  const handleCreateTransfer = async (e) => {
    e.preventDefault();
    setError('');
    if (formData.source_location === formData.destination_location) {
      setError('Source and Destination locations must be different.');
      return;
    }
    try {
      await api.post('/transfers/', formData);
      setShowCreateModal(false);
      resetForm();
      fetchTransfers();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error creating internal transfer.');
    }
  };

  const resetForm = () => {
    setFormData({
      source_location: '',
      destination_location: '',
      date: new Date().toISOString().split('T')[0],
      notes: '',
      items: [{ product: '', quantity: 10 }]
    });
    setError('');
  };

  const handleValidateConfirm = async () => {
    if (!validatingTransfer) return;
    setValidatingLoading(true);
    try {
      await api.post(`/transfers/${validatingTransfer.id}/validate_transfer/`);
      setValidatingTransfer(null);
      fetchTransfers();
    } catch (err) {
      alert(err.response?.data?.error || err.response?.data?.details?.[0] || 'Transfer validation failed.');
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
            <Repeat className="w-6 h-6 text-cyan-400" /> Internal Stock Transfers
          </h2>
          <p className="text-xs text-slate-400">Move stock between warehouses, racks & production floors without affecting total company inventory balance</p>
        </div>

        <button
          onClick={() => { resetForm(); setShowCreateModal(true); }}
          className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-xs font-bold flex items-center gap-2 transition shadow-lg shadow-cyan-600/30"
        >
          <Plus className="w-4 h-4" /> Schedule Transfer
        </button>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by Transfer Ref..."
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

      {/* Transfers Table */}
      <div className="glass-panel rounded-2xl overflow-hidden border border-slate-700/60 shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-800/90 text-xs uppercase font-bold text-slate-400 border-b border-slate-700/60">
              <tr>
                <th className="px-6 py-4">Transfer Ref</th>
                <th className="px-6 py-4">Source Location</th>
                <th className="px-6 py-4">Destination Location</th>
                <th className="px-6 py-4">Items Moved</th>
                <th className="px-6 py-4">Date</th>
                <th className="px-6 py-4 text-center">Status</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan="7" className="text-center py-8 text-slate-500 text-xs">Loading internal transfers...</td>
                </tr>
              ) : transfers.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-8 text-slate-500 text-xs">No internal transfers found.</td>
                </tr>
              ) : (
                transfers.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-6 py-4 font-mono font-bold text-cyan-400 text-xs">{t.transfer_number}</td>
                    <td className="px-6 py-4 text-xs font-semibold text-slate-300">
                      {t.source_warehouse_name} / <span className="text-indigo-300">{t.source_location_name}</span>
                    </td>
                    <td className="px-6 py-4 text-xs font-semibold text-slate-300">
                      {t.destination_warehouse_name} / <span className="text-emerald-300">{t.destination_location_name}</span>
                    </td>
                    <td className="px-6 py-4 text-xs">
                      {t.items?.map((item, idx) => (
                        <div key={idx} className="text-slate-300">
                          <strong>{item.quantity}</strong>x {item.product_name}
                        </div>
                      ))}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400">{t.date}</td>
                    <td className="px-6 py-4 text-center">
                      <StatusBadge status={t.status} />
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      {t.status !== 'DONE' && t.status !== 'CANCELLED' && (
                        <button
                          onClick={() => setValidatingTransfer(t)}
                          className="px-3 py-1.5 bg-cyan-600/90 hover:bg-cyan-500 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 ml-auto shadow"
                        >
                          <CheckCircle className="w-3.5 h-3.5" /> Validate Move
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

      {/* Create Internal Transfer Modal */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="Schedule Internal Stock Transfer" maxWidth="max-w-3xl">
        {error && <p className="text-xs text-rose-400 p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/30">{error}</p>}
        <form onSubmit={handleCreateTransfer} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Source Location *</label>
              <select
                required
                value={formData.source_location}
                onChange={(e) => setFormData({ ...formData, source_location: e.target.value })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-200"
              >
                <option value="">Select Source Location</option>
                {locations.map((l) => (
                  <option key={l.id} value={l.id}>{l.warehouse_code} ➔ {l.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Destination Location *</label>
              <select
                required
                value={formData.destination_location}
                onChange={(e) => setFormData({ ...formData, destination_location: e.target.value })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-200"
              >
                <option value="">Select Destination Location</option>
                {locations.map((l) => (
                  <option key={l.id} value={l.id}>{l.warehouse_code} ➔ {l.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Transfer Date *</label>
            <input
              type="date"
              required
              value={formData.date}
              onChange={(e) => setFormData({ ...formData, date: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100"
            />
          </div>

          {/* Line Items */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Products & Quantities to Move</h4>
              <button
                type="button"
                onClick={handleAddItem}
                className="text-xs text-cyan-400 hover:underline flex items-center gap-1 font-semibold"
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
            <button type="submit" className="px-4 py-2 text-xs bg-cyan-600 font-bold rounded-xl text-white">Save Transfer</button>
          </div>
        </form>
      </Modal>

      {/* Validate Confirmation Dialog */}
      <ConfirmDialog
        isOpen={!!validatingTransfer}
        onClose={() => setValidatingTransfer(null)}
        onConfirm={handleValidateConfirm}
        title={`Validate Transfer ${validatingTransfer?.transfer_number}`}
        message="Validating will deduct stock from the source location and add it to the destination location. Total company inventory balance will remain unchanged. Proceed?"
        confirmText="Validate & Move Stock"
        confirmStyle="bg-cyan-600 hover:bg-cyan-500"
        loading={validatingLoading}
      />
    </div>
  );
};

export default Transfers;
