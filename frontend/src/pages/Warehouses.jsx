import React, { useState, useEffect } from 'react';
import { Warehouse as WarehouseIcon, MapPin, Plus, Layers, Boxes } from 'lucide-react';
import Modal from '../components/Modal';
import api from '../api/axios';

const Warehouses = () => {
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [showWhModal, setShowWhModal] = useState(false);
  const [showLocModal, setShowLocModal] = useState(false);

  // Forms
  const [whForm, setWhForm] = useState({ name: '', code: '', address: '' });
  const [locForm, setLocForm] = useState({ warehouse: '', name: '', code: '', location_type: 'STORAGE' });
  const [error, setError] = useState('');

  useEffect(() => {
    fetchWarehouses();
  }, []);

  const fetchWarehouses = async () => {
    setLoading(true);
    try {
      const res = await api.get('/warehouses/');
      setWarehouses(res.data.results || res.data || []);
    } catch (e) {
      console.error('Error fetching warehouses:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWarehouse = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/warehouses/', whForm);
      setShowWhModal(false);
      setWhForm({ name: '', code: '', address: '' });
      fetchWarehouses();
    } catch (err) {
      setError(err.response?.data?.code?.[0] || 'Error creating warehouse.');
    }
  };

  const handleCreateLocation = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/locations/', locForm);
      setShowLocModal(false);
      setLocForm({ warehouse: '', name: '', code: '', location_type: 'STORAGE' });
      fetchWarehouses();
    } catch (err) {
      setError(err.response?.data?.code?.[0] || 'Error creating location.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-5 rounded-2xl">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <WarehouseIcon className="w-6 h-6 text-indigo-400" /> Multi-Warehouse & Location Hierarchy
          </h2>
          <p className="text-xs text-slate-400">Manage fulfillment centers, racks, production floors & storage zones</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => { setError(''); setShowLocModal(true); }}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold flex items-center gap-2 transition"
          >
            <Plus className="w-4 h-4 text-indigo-400" /> Add Location Rack
          </button>
          <button
            onClick={() => { setError(''); setShowWhModal(true); }}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold flex items-center gap-2 transition shadow-lg shadow-indigo-600/30"
          >
            <Plus className="w-4 h-4" /> Add Warehouse
          </button>
        </div>
      </div>

      {/* Warehouses Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {loading ? (
          <div className="col-span-2 text-center py-12 text-slate-500 text-xs">Loading warehouse layouts...</div>
        ) : warehouses.length === 0 ? (
          <div className="col-span-2 text-center py-12 text-slate-500 text-xs">No warehouses configured yet.</div>
        ) : (
          warehouses.map((wh) => (
            <div key={wh.id} className="glass-panel p-6 rounded-2xl border border-slate-700/60 space-y-4">
              <div className="flex items-start justify-between border-b border-slate-700/60 pb-3">
                <div>
                  <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-[10px] font-bold border border-indigo-500/30">
                    {wh.code}
                  </span>
                  <h3 className="text-lg font-bold text-slate-100 mt-1">{wh.name}</h3>
                  <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                    <MapPin className="w-3.5 h-3.5 text-slate-500" /> {wh.address || 'No address specified'}
                  </p>
                </div>
                <span className="px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-bold border border-emerald-500/30">
                  Active Facility
                </span>
              </div>

              {/* Locations List */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
                  <span>Locations & Zones ({wh.locations?.length || 0})</span>
                  <span className="text-[10px] font-normal text-indigo-400">Rack / Shelf / Floor</span>
                </h4>

                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {wh.locations?.length === 0 ? (
                    <p className="text-xs text-slate-500 py-2">No child locations added to this warehouse yet.</p>
                  ) : (
                    wh.locations.map((loc) => (
                      <div key={loc.id} className="p-3 bg-slate-900/80 rounded-xl border border-slate-800 flex items-center justify-between">
                        <div className="flex items-center gap-2.5">
                          <Layers className="w-4 h-4 text-indigo-400" />
                          <div>
                            <p className="text-xs font-bold text-slate-200">{loc.name}</p>
                            <p className="text-[10px] font-mono text-slate-500">{loc.code}</p>
                          </div>
                        </div>
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px] font-semibold border border-slate-700">
                          {loc.location_type}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Warehouse Modal */}
      <Modal isOpen={showWhModal} onClose={() => setShowWhModal(false)} title="Create New Warehouse Facility">
        {error && <p className="text-xs text-rose-400 p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/30">{error}</p>}
        <form onSubmit={handleCreateWarehouse} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Warehouse Name *</label>
            <input
              type="text"
              required
              value={whForm.name}
              onChange={(e) => setWhForm({ ...whForm, name: e.target.value })}
              placeholder="e.g. Main Warehouse"
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Warehouse Code *</label>
            <input
              type="text"
              required
              value={whForm.code}
              onChange={(e) => setWhForm({ ...whForm, code: e.target.value })}
              placeholder="e.g. MWH"
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100 font-mono"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Street Address</label>
            <textarea
              rows="2"
              value={whForm.address}
              onChange={(e) => setWhForm({ ...whForm, address: e.target.value })}
              placeholder="100 Industrial Parkway..."
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100"
            />
          </div>
          <div className="flex justify-end gap-3 pt-3 border-t border-slate-700">
            <button type="button" onClick={() => setShowWhModal(false)} className="px-4 py-2 text-xs border border-slate-700 rounded-xl">Cancel</button>
            <button type="submit" className="px-4 py-2 text-xs bg-indigo-600 font-bold rounded-xl text-white">Create Warehouse</button>
          </div>
        </form>
      </Modal>

      {/* Create Location Modal */}
      <Modal isOpen={showLocModal} onClose={() => setShowLocModal(false)} title="Create Storage Location / Rack">
        {error && <p className="text-xs text-rose-400 p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/30">{error}</p>}
        <form onSubmit={handleCreateLocation} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Select Parent Warehouse *</label>
            <select
              required
              value={locForm.warehouse}
              onChange={(e) => setLocForm({ ...locForm, warehouse: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-200"
            >
              <option value="">Select Warehouse</option>
              {warehouses.map((w) => (
                <option key={w.id} value={w.id}>{w.name} ({w.code})</option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Location Name *</label>
              <input
                type="text"
                required
                value={locForm.name}
                onChange={(e) => setLocForm({ ...locForm, name: e.target.value })}
                placeholder="e.g. Rack A"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Location Code *</label>
              <input
                type="text"
                required
                value={locForm.code}
                onChange={(e) => setLocForm({ ...locForm, code: e.target.value })}
                placeholder="e.g. MWH-RACK-A"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100 font-mono"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Location Zone Type</label>
            <select
              value={locForm.location_type}
              onChange={(e) => setLocForm({ ...locForm, location_type: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-200"
            >
              <option value="STORAGE">Storage Rack / Shelf</option>
              <option value="PRODUCTION">Production Floor</option>
              <option value="RECEIVING">Receiving Dock</option>
              <option value="SHIPPING">Shipping Bay</option>
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-3 border-t border-slate-700">
            <button type="button" onClick={() => setShowLocModal(false)} className="px-4 py-2 text-xs border border-slate-700 rounded-xl">Cancel</button>
            <button type="submit" className="px-4 py-2 text-xs bg-indigo-600 font-bold rounded-xl text-white">Create Location</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Warehouses;
