import React, { useState } from 'react';
import Modal from './Modal';
import { QrCode, Search, CheckCircle } from 'lucide-react';

const BarcodeScannerModal = ({ isOpen, onClose, onSelectProduct, products = [] }) => {
  const [skuInput, setSkuInput] = useState('');
  const [foundProduct, setFoundProduct] = useState(null);
  const [error, setError] = useState('');

  const handleScan = (e) => {
    e.preventDefault();
    setError('');
    const matched = products.find(
      (p) => p.sku.toLowerCase() === skuInput.trim().toLowerCase() ||
             p.barcode === skuInput.trim()
    );
    if (matched) {
      setFoundProduct(matched);
    } else {
      setFoundProduct(null);
      setError(`No product found with SKU/Barcode "${skuInput}"`);
    }
  };

  const handleConfirm = () => {
    if (foundProduct) {
      onSelectProduct(foundProduct);
      setSkuInput('');
      setFoundProduct(null);
      onClose();
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Barcode / SKU Scanner Simulator" maxWidth="max-w-md">
      <div className="space-y-4">
        <div className="flex flex-col items-center p-6 border-2 border-dashed border-indigo-500/40 rounded-2xl bg-indigo-950/20 text-center relative overflow-hidden">
          <div className="w-full h-1 bg-indigo-500/80 absolute top-0 left-0 animate-pulse"></div>
          <QrCode className="w-12 h-12 text-indigo-400 mb-2 animate-bounce" />
          <p className="text-xs text-indigo-300 font-semibold uppercase tracking-wider">Scan Barcode or Enter SKU</p>
        </div>

        <form onSubmit={handleScan} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="e.g. RAW-STL-001 or 890123456001"
              value={skuInput}
              onChange={(e) => setSkuInput(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm focus:outline-none focus:border-indigo-500 text-slate-100"
              autoFocus
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold transition"
          >
            Scan
          </button>
        </form>

        {error && (
          <p className="text-xs text-rose-400 bg-rose-500/10 p-2.5 rounded-xl border border-rose-500/20">{error}</p>
        )}

        {foundProduct && (
          <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl space-y-2">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
              <CheckCircle className="w-4 h-4" /> Matched Product
            </div>
            <p className="text-sm text-slate-200 font-medium">{foundProduct.name}</p>
            <div className="flex justify-between text-xs text-slate-400">
              <span>SKU: {foundProduct.sku}</span>
              <span>Stock: {foundProduct.current_stock} {foundProduct.unit_of_measure}</span>
            </div>
            <button
              onClick={handleConfirm}
              className="w-full mt-2 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs rounded-xl transition"
            >
              Select Product
            </button>
          </div>
        )}
      </div>
    </Modal>
  );
};

export default BarcodeScannerModal;
