import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Package, Warehouse, ArrowDownRight, ArrowUpRight,
  Repeat, SlidersHorizontal, History, Settings, ShieldCheck, UserCheck
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Sidebar = () => {
  const { user } = useAuth();

  const navItems = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'Products', path: '/products', icon: Package },
    { label: 'Warehouses', path: '/warehouses', icon: Warehouse },
    { label: 'Receipts', path: '/receipts', icon: ArrowDownRight },
    { label: 'Deliveries', path: '/deliveries', icon: ArrowUpRight },
    { label: 'Transfers', path: '/transfers', icon: Repeat },
    { label: 'Adjustments', path: '/adjustments', icon: SlidersHorizontal },
    { label: 'Stock Ledger', path: '/ledger', icon: History },
    { label: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <aside className="w-64 glass-panel border-r border-slate-700/60 flex flex-col h-screen sticky top-0 z-30">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-700/60 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white font-extrabold shadow-lg shadow-indigo-500/30 text-xl">
          S
        </div>
        <div>
          <h1 className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent">
            StockSense
          </h1>
          <p className="text-[10px] uppercase font-bold tracking-widest text-indigo-400">Inventory Core</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white shadow-md shadow-indigo-500/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <Icon className="w-5 h-5" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Role Footer */}
      <div className="p-4 border-t border-slate-700/60 bg-slate-850/60">
        <div className="flex items-center gap-3 p-2.5 rounded-xl bg-slate-800/80 border border-slate-700/50">
          {user?.role === 'MANAGER' ? (
            <ShieldCheck className="w-5 h-5 text-indigo-400" />
          ) : (
            <UserCheck className="w-5 h-5 text-emerald-400" />
          )}
          <div className="truncate">
            <p className="text-xs font-bold text-slate-200 truncate">{user?.first_name ? `${user.first_name} ${user.last_name}` : user?.username}</p>
            <p className="text-[11px] text-slate-400 font-medium truncate">{user?.role === 'MANAGER' ? 'Inventory Manager' : 'Warehouse Staff'}</p>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
