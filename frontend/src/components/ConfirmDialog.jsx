import React from 'react';
import Modal from './Modal';
import { AlertTriangle } from 'lucide-react';

const ConfirmDialog = ({ isOpen, onClose, onConfirm, title, message, confirmText = "Confirm", confirmStyle = "bg-emerald-600 hover:bg-emerald-500", loading = false }) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} maxWidth="max-w-md">
      <div className="flex flex-col items-center text-center p-2">
        <div className="p-3 rounded-full bg-amber-500/20 text-amber-400 mb-4 border border-amber-500/30">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <p className="text-slate-300 text-sm mb-6">{message}</p>
        <div className="flex justify-end gap-3 w-full">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium rounded-xl border border-slate-700 hover:bg-slate-800 text-slate-300 transition"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={loading}
            className={`px-4 py-2 text-sm font-semibold rounded-xl text-white transition flex items-center gap-2 ${confirmStyle}`}
          >
            {loading ? 'Processing...' : confirmText}
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default ConfirmDialog;
