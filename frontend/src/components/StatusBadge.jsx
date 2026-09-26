import React from 'react';

const StatusBadge = ({ status }) => {
  const getBadgeStyle = (statusStr) => {
    switch (statusStr?.toUpperCase()) {
      case 'DRAFT':
        return 'bg-slate-700/60 text-slate-300 border-slate-600';
      case 'WAITING':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'READY':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'DONE':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'CANCELLED':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/30';
      case 'IN_STOCK':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'LOW_STOCK':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30 animate-pulse';
      case 'OUT_OF_STOCK':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/30 animate-pulse';
      case 'RECEIPT':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'DELIVERY':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'INTERNAL_TRANSFER':
        return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30';
      case 'ADJUSTMENT':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      default:
        return 'bg-slate-700 text-slate-300 border-slate-600';
    }
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${getBadgeStyle(status)}`}>
      {status?.replace('_', ' ')}
    </span>
  );
};

export default StatusBadge;
