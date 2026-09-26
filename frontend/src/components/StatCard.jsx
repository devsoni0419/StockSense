import React from 'react';

const StatCard = ({ title, value, icon: Icon, color = 'indigo', subtitle }) => {
  const colorMap = {
    indigo: 'from-indigo-500/20 to-purple-500/10 border-indigo-500/30 text-indigo-400',
    emerald: 'from-emerald-500/20 to-teal-500/10 border-emerald-500/30 text-emerald-400',
    amber: 'from-amber-500/20 to-orange-500/10 border-amber-500/30 text-amber-400',
    rose: 'from-rose-500/20 to-red-500/10 border-rose-500/30 text-rose-400',
    blue: 'from-blue-500/20 to-cyan-500/10 border-blue-500/30 text-blue-400',
    purple: 'from-purple-500/20 to-pink-500/10 border-purple-500/30 text-purple-400',
    cyan: 'from-cyan-500/20 to-blue-500/10 border-cyan-500/30 text-cyan-400',
  };

  const styleClass = colorMap[color] || colorMap.indigo;

  return (
    <div className={`p-5 rounded-2xl bg-gradient-to-br border glass-panel relative overflow-hidden transition-all duration-300 hover:-translate-y-1 ${styleClass}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-wider font-semibold opacity-80">{title}</p>
          <h3 className="text-3xl font-extrabold mt-2 tracking-tight text-white">{value}</h3>
          {subtitle && <p className="text-xs mt-1 text-slate-400 font-medium">{subtitle}</p>}
        </div>
        {Icon && (
          <div className="p-3.5 rounded-xl bg-slate-800/80 border border-slate-700/60 shadow-inner">
            <Icon className="w-6 h-6" />
          </div>
        )}
      </div>
    </div>
  );
};

export default StatCard;
