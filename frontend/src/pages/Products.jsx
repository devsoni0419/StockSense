import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Package, Plus, Search, QrCode, Archive, Eye, Edit, AlertCircle, Layers
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import Modal from '../components/Modal';
import BarcodeScannerModal from '../components/BarcodeScannerModal';
import api from '../api/axios';

const Products = () => {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters & Search
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchTerm, setSearchTerm] = useState(searchParams.get('search') || '');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedStockStatus, setSelectedStockStatus] = useState('');

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showScannerModal, setShowScannerModal] = useState(false);
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [selectedProductLocations, setSelectedProductLocations] = useState(null);

  // Form State
  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    barcode: '',
    category: '',
    unit_of_measure: 'units',
    initial_stock: 0,
    current_stock: 0,
    reorder_level: 10,
  });

  const [editingId, setEditingId] = useState(null);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchAuxiliary();
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [searchTerm, selectedCategory, selectedStockStatus]);

  const fetchAuxiliary = async () => {
    try {
      const res = await api.get('/categories/');
      setCategories(res.data.results || res.data || []);
    } catch (e) {
      console.error('Error fetching categories:', e);
    }
  };

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const params = {};
      if (searchTerm) params.search = searchTerm;
      if (selectedCategory) params.category = selectedCategory;
      if (selectedStockStatus) params.stock_status = selectedStockStatus;

      const res = await api.get('/products/', { params });
      setProducts(res.data.results || res.data || []);
    } catch (e) {
      console.error('Error fetching products:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrUpdate = async (e) => {
    e.preventDefault();
    setError('');
    try {
      if (editingId) {
        await api.patch(`/products/${editingId}/`, formData);
      } else {
        const payload = {
          ...formData,
          current_stock: formData.initial_stock
        };
        await api.post('/products/', payload);
      }
      setShowCreateModal(false);
      resetForm();
      fetchProducts();
    } catch (err) {
      setError(err.response?.data?.sku?.[0] || 'Error saving product details.');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      sku: '',
      barcode: '',
      category: '',
      unit_of_measure: 'units',
      initial_stock: 0,
      current_stock: 0,
      reorder_level: 10,
    });
    setEditingId(null);
    setError('');
  };

  const openEditModal = (p) => {
    setEditingId(p.id);
    setFormData({
      name: p.name,
      sku: p.sku,
      barcode: p.barcode || '',
      category: p.category || '',
      unit_of_measure: p.unit_of_measure,
      initial_stock: p.initial_stock,
      current_stock: p.current_stock,
      reorder_level: p.reorder_level,
    });
    setShowCreateModal(true);
  };

  const toggleArchive = async (id) => {
    try {
      await api.post(`/products/${id}/toggle_archive/`);
      fetchProducts();
    } catch (e) {
      console.error('Error archiving product:', e);
    }
  };

  const viewStockLocations = (product) => {
    setSelectedProductLocations(product);
    setShowLocationModal(true);
  };

  return (
    <div className="space-y-6">
      {/* Header & Main Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-5 rounded-2xl">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Package className="w-6 h-6 text-indigo-400" /> Product Inventory Catalog
          </h2>
          <p className="text-xs text-slate-400">Manage SKUs, reorder thresholds & location balances</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowScannerModal(true)}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold flex items-center gap-2 transition"
          >
            <QrCode className="w-4 h-4 text-indigo-400" /> Scan SKU / Barcode
          </button>

          <button
            onClick={() => { resetForm(); setShowCreateModal(true); }}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold flex items-center gap-2 transition shadow-lg shadow-indigo-600/30"
          >
            <Plus className="w-4 h-4" /> Add Product
          </button>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by Name, SKU or Barcode..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm focus:outline-none focus:border-indigo-500 text-slate-100"
          />
        </div>

        {/* Category Filter */}
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm focus:outline-none focus:border-indigo-500 text-slate-200"
        >
          <option value="">All Categories</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>

        {/* Stock Status Filter */}
        <select
          value={selectedStockStatus}
          onChange={(e) => setSelectedStockStatus(e.target.value)}
          className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm focus:outline-none focus:border-indigo-500 text-slate-200"
        >
          <option value="">All Stock Statuses</option>
          <option value="IN_STOCK">In Stock</option>
          <option value="LOW_STOCK">Low Stock</option>
          <option value="OUT_OF_STOCK">Out of Stock</option>
        </select>
      </div>

      {/* Products Table */}
      <div className="glass-panel rounded-2xl overflow-hidden border border-slate-700/60 shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-800/90 text-xs uppercase font-bold text-slate-400 border-b border-slate-700/60">
              <tr>
                <th className="px-6 py-4">Product Info</th>
                <th className="px-6 py-4">SKU / Barcode</th>
                <th className="px-6 py-4">Category</th>
                <th className="px-6 py-4 text-center">Total Stock</th>
                <th className="px-6 py-4 text-center">Reorder Level</th>
                <th className="px-6 py-4 text-center">Status</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan="7" className="text-center py-8 text-slate-500 text-xs">Loading product catalog...</td>
                </tr>
              ) : products.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-8 text-slate-500 text-xs">No products found matching filters.</td>
                </tr>
              ) : (
                products.map((p) => (
                  <tr key={p.id} className={`hover:bg-slate-800/40 transition ${p.is_archived ? 'opacity-50' : ''}`}>
                    <td className="px-6 py-4">
                      <p className="font-bold text-slate-100">{p.name}</p>
                      <p className="text-xs text-slate-400">{p.unit_of_measure}</p>
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-mono text-xs font-semibold text-indigo-400">{p.sku}</p>
                      {p.barcode && <p className="text-[10px] font-mono text-slate-500">{p.barcode}</p>}
                    </td>
                    <td className="px-6 py-4 text-xs">{p.category_name || 'Uncategorized'}</td>
                    <td className="px-6 py-4 text-center">
                      <span className="font-extrabold text-white text-base">{p.current_stock}</span>
                      <span className="text-xs text-slate-400 ml-1">{p.unit_of_measure}</span>
                    </td>
                    <td className="px-6 py-4 text-center text-xs font-semibold text-slate-400">
                      {p.reorder_level}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <StatusBadge status={p.stock_status} />
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      <button
                        onClick={() => viewStockLocations(p)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-400 hover:bg-slate-800 transition"
                        title="View Location Stock Breakdown"
                      >
                        <Layers className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => openEditModal(p)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                        title="Edit Product"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => toggleArchive(p.id)}
                        className={`p-1.5 rounded-lg transition ${p.is_archived ? 'text-emerald-400 hover:bg-emerald-500/10' : 'text-slate-400 hover:text-rose-400 hover:bg-slate-800'}`}
                        title={p.is_archived ? 'Unarchive' : 'Archive'}
                      >
                        <Archive className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create / Edit Product Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title={editingId ? "Edit Product Details" : "Create New Inventory Product"}
      >
        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs font-semibold">
            {error}
          </div>
        )}
        <form onSubmit={handleCreateOrUpdate} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Product Name *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g. Steel Rods (12mm)"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm focus:outline-none focus:border-indigo-500 text-slate-100"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">SKU Code *</label>
              <input
                type="text"
                required
                value={formData.sku}
                onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                placeholder="e.g. RAW-STL-001"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm focus:outline-none focus:border-indigo-500 text-slate-100 font-mono"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Category</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm focus:outline-none focus:border-indigo-500 text-slate-200"
              >
                <option value="">Select Category</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Unit of Measure</label>
              <select
                value={formData.unit_of_measure}
                onChange={(e) => setFormData({ ...formData, unit_of_measure: e.target.value })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm focus:outline-none focus:border-indigo-500 text-slate-200"
              >
                <option value="units">Units</option>
                <option value="pcs">Pieces</option>
                <option value="kg">Kilograms</option>
                <option value="meters">Meters</option>
                <option value="boxes">Boxes</option>
                <option value="packs">Packs</option>
                <option value="liters">Liters</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Barcode / EAN (Optional)</label>
              <input
                type="text"
                value={formData.barcode}
                onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
                placeholder="e.g. 890123456001"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm focus:outline-none focus:border-indigo-500 text-slate-100 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Reorder Level Threshold</label>
              <input
                type="number"
                min="0"
                required
                value={formData.reorder_level}
                onChange={(e) => setFormData({ ...formData, reorder_level: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm focus:outline-none focus:border-indigo-500 text-slate-100"
              />
            </div>
          </div>

          {!editingId && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Initial Opening Stock</label>
              <input
                type="number"
                min="0"
                value={formData.initial_stock}
                onChange={(e) => setFormData({ ...formData, initial_stock: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm focus:outline-none focus:border-indigo-500 text-slate-100"
              />
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-700/60">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="px-4 py-2 border border-slate-700 rounded-xl text-slate-300 hover:bg-slate-800 text-sm font-semibold transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-bold transition"
            >
              {editingId ? 'Save Changes' : 'Create Product'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Barcode Scanner Modal */}
      <BarcodeScannerModal
        isOpen={showScannerModal}
        onClose={() => setShowScannerModal(false)}
        products={products}
        onSelectProduct={(product) => {
          setSearchTerm(product.sku);
        }}
      />

      {/* Location Stock Breakdown Modal */}
      <Modal
        isOpen={showLocationModal}
        onClose={() => setShowLocationModal(false)}
        title={`Stock Balances: ${selectedProductLocations?.name}`}
      >
        {selectedProductLocations && (
          <div className="space-y-4">
            <div className="p-3 bg-slate-800/80 rounded-xl flex justify-between items-center border border-slate-700">
              <div>
                <p className="text-xs text-slate-400 font-mono">SKU: {selectedProductLocations.sku}</p>
                <p className="text-sm font-bold text-slate-100">{selectedProductLocations.name}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-slate-400">Total Stock</p>
                <p className="text-lg font-extrabold text-indigo-400">{selectedProductLocations.current_stock} {selectedProductLocations.unit_of_measure}</p>
              </div>
            </div>

            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Location Breakdown</h4>
            <div className="space-y-2">
              {selectedProductLocations.location_stocks?.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-4">No location stock assigned yet.</p>
              ) : (
                selectedProductLocations.location_stocks?.map((loc, i) => (
                  <div key={i} className="p-3 bg-slate-900 rounded-xl border border-slate-700/60 flex justify-between items-center">
                    <div>
                      <p className="text-xs font-bold text-slate-200">{loc.warehouse_name} ({loc.warehouse_id})</p>
                      <p className="text-xs text-slate-400 font-semibold">{loc.location_name}</p>
                    </div>
                    <p className="text-sm font-extrabold text-emerald-400">
                      {loc.quantity} <span className="text-xs text-slate-400 font-normal">{selectedProductLocations.unit_of_measure}</span>
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Products;
