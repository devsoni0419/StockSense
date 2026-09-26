import React, { useState, useEffect } from 'react';
import { SlidersHorizontal, Plus, CheckCircle, Search } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import api from '../api/axios';

const Adjustments = () => {
  const [adjustments, setAdjustments] = useState([]);
  const [products, setProducts] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');

  // Modals & Action
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [validatingAdj, setValidatingAdj] = useState(null);
  const [validatingLoading, setValidatingLoading] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    product: '',
    location: '',
    counted_quantity: 0,
    reason: 'DISCREPANCY',
    date: new Date().toISOString().split('T')[0],
    notes: ''
  });

  const [error, setError] = useState('');

  useEffect(() => {
    fetchAuxiliary();
  }, []);

  useEffect(() => {
    fetchAdjustments();
  }, [searchTerm]);

  const fetchAuxiliary = async () => {
    try {
      const [prodRes, locRes] = await Promise.all([
        api.get('/products/'),
        api.get('/locations/')
      ]);
      setProducts(prodRes.data.results || prodRes.data || []);
      setLocations(locRes.data.results || locRes.data || []);
    } catch (e) {
      console.error('Error loading auxiliary adjustment data:', e);
    }
  };

  const fetchAdjustments = async () => {
    setLoading(true);
    try {
      const params = {};
      if (searchTerm) params.search = searchTerm;

      const res = await api.get('/adjustments/', { params });
      setAdjustments(res.data.results || res.data || []);
    } catch (e) {
      console.error('Error loading adjustments:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAdjustment = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/adjustments/', formData);
      setShowCreateModal(false);
      resetForm();
      fetchAdjustments();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error creating adjustment.');
    }
  };

  const resetForm = () => {
    setFormData({
      product: '',
      location: '',
      counted_quantity: 0,
      reason: 'DISCREPANCY',
      date: new Date().toISOString().split('T')[0],
      notes: ''
    });
    setError('');
  };

  const handleValidateConfirm = async () => {
    if (!validatingAdj) return;
    setValidatingLoading(true);
    try {
      await api.post(`/adjustments/${validatingAdj.id}/validate_adjustment/`);
      setValidatingAdj(null);
      fetchAdjustments();
    } catch (err) {
      alert(err.response?.data?.error || 'Adjustment validation failed.');
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
            <SlidersHorizontal className="w-6 h-6 text-orange-400" /> Physical Stock Adjustments
          </h2>
          <p className="text-xs text-slate-400">Reconcile physical stock audits, damaged goods & count discrepancies</p>
        </div>

        <button
          onClick={() => { resetForm(); setShowCreateModal(true); }}
          className="px-4 py-2 bg-orange-600 hover:bg-orange-500 text-white rounded-xl text-xs font-bold flex items-center gap-2 transition shadow-lg shadow-orange-600/30"
        >
          <Plus className="w-4 h-4" /> Create Stock Adjustment
        </button>
      </div>

      {/* Search Filter */}
      <div className="relative">
        <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
        <input
          type="text"
          placeholder="Search by Adjustment Ref, Product..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100"
        />
      </div>

      {/* Adjustments Table */}
      <div className="glass-panel rounded-2xl overflow-hidden border border-slate-700/60 shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-800/90 text-xs uppercase font-bold text-slate-400 border-b border-slate-700/60">
              <tr>
                <th className="px-6 py-4">Adjustment Ref</th>
                <th className="px-6 py-4">Product Name</th>
                <th className="px-6 py-4">Location</th>
                <th className="px-6 py-4 text-center">System Qty</th>
                <th className="px-6 py-4 text-center">Counted Qty</th>
                <th className="px-6 py-4 text-center">Difference</th>
                <th className="px-6 py-4">Reason</th>
                <th className="px-6 py-4 text-center">Status</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan="9" className="text-center py-8 text-slate-500 text-xs">Loading adjustments...</td>
                </tr>
              ) : adjustments.length === 0 ? (
                <tr>
                  <td colSpan="9" className="text-center py-8 text-slate-500 text-xs">No stock adjustments recorded.</td>
                </tr>
              ) : (
                adjustments.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-6 py-4 font-mono font-bold text-orange-400 text-xs">{a.adjustment_number}</td>
                    <td className="px-6 py-4 font-bold text-slate-200">{a.product_name}</td>
                    <td className="px-6 py-4 text-xs font-semibold text-slate-400">{a.warehouse_name} / {a.location_name}</td>
                    <td className="px-6 py-4 text-center font-bold text-slate-400">{a.system_quantity}</td>
                    <td className="px-6 py-4 text-center font-bold text-indigo-300">{a.counted_quantity}</td>
                    <td className="px-6 py-4 text-center">
                      <span className={`px-2 py-0.5 rounded text-xs font-mono font-extrabold ${a.difference < 0 ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : a.difference > 0 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'text-slate-400'}`}>
                        {a.difference > 0 ? `+${a.difference}` : a.difference}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-300">{a.reason_display}</td>
                    <td className="px-6 py-4 text-center">
                      <StatusBadge status={a.status} />
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      {a.status !== 'DONE' && a.status !== 'CANCELLED' && (
                        <button
                          onClick={() => setValidatingAdj(a)}
                          className="px-3 py-1.5 bg-orange-600/90 hover:bg-orange-500 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 ml-auto shadow"
                        >
                          <CheckCircle className="w-3.5 h-3.5" /> Validate Adjustment
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

      {/* Create Adjustment Modal */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="Create Inventory Adjustment">
        {error && <p className="text-xs text-rose-400 p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/30">{error}</p>}
        <form onSubmit={handleCreateAdjustment} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Target Product *</label>
            <select
              required
              value={formData.product}
              onChange={(e) => setFormData({ ...formData, product: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-200"
            >
              <option value="">Select Product</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>{p.name} ({p.sku}) — System Total: {p.current_stock}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Location Rack *</label>
            <select
              required
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-200"
            >
              <option value="">Select Location</option>
              {locations.map((l) => (
                <option key={l.id} value={l.id}>{l.warehouse_code} ➔ {l.name}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Actual Physical Counted Qty *</label>
              <input
                type="number"
                min="0"
                required
                value={formData.counted_quantity}
                onChange={(e) => setFormData({ ...formData, counted_quantity: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Adjustment Reason</label>
              <select
                value={formData.reason}
                onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-200"
              >
                <option value="DAMAGED">Damaged Goods</option>
                <option value="DISCREPANCY">Physical Audit Discrepancy</option>
                <option value="LOST">Lost or Stolen</option>
                <option value="FOUND">Found Extra Stock</option>
                <option value="EXPIRED">Expired Stock</option>
                <option value="OTHER">Other Reason</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Audit Notes / Explanation</label>
            <textarea
              rows="2"
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              placeholder="e.g. 3 units damaged during forklift operation"
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100"
            />
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-700">
            <button type="button" onClick={() => setShowCreateModal(false)} className="px-4 py-2 text-xs border border-slate-700 rounded-xl">Cancel</button>
            <button type="submit" className="px-4 py-2 text-xs bg-orange-600 font-bold rounded-xl text-white">Save Adjustment</button>
          </div>
        </form>
      </Modal>

      {/* Validate Confirmation Dialog */}
      <ConfirmDialog
        isOpen={!!validatingAdj}
        onClose={() => setValidatingAdj(null)}
        onConfirm={handleValidateConfirm}
        title={`Validate Adjustment ${validatingAdj?.adjustment_number}`}
        message={`Validating will update location stock to ${validatingAdj?.counted_quantity} units and log difference (${validatingAdj?.difference > 0 ? '+' : ''}${validatingAdj?.difference}) to Stock Ledger. Proceed?`}
        confirmText="Validate Adjustment"
        confirmStyle="bg-orange-600 hover:bg-orange-500"
        loading={validatingLoading}
      />
    </div>
  );
};

export default Adjustments;
