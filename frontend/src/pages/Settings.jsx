import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Settings as SettingsIcon, Shield, CheckCircle, Database, Server, Cpu, RefreshCw } from 'lucide-react';
import api from '../api/axios';

const Settings = () => {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-panel p-5 rounded-2xl">
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-indigo-400" /> Platform Settings & Telemetry
        </h2>
        <p className="text-xs text-slate-400">User Profile, RBAC Permissions Matrix & Local Stack Status</p>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* User Profile Card */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-700/60 space-y-4">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2 border-b border-slate-700/60 pb-3">
            <Shield className="w-4 h-4 text-indigo-400" /> Authenticated Profile
          </h3>

          <div className="space-y-3">
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-400">Full Name:</span>
              <span className="font-bold text-slate-100">{user?.first_name} {user?.last_name}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-400">Email Address:</span>
              <span className="font-mono text-indigo-300">{user?.email}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-400">Username:</span>
              <span className="font-mono text-slate-200">{user?.username}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-400">Assigned Role:</span>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${user?.role === 'MANAGER' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'}`}>
                {user?.role === 'MANAGER' ? 'Inventory Manager' : 'Warehouse Staff'}
              </span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-400">Department:</span>
              <span className="text-slate-300">{user?.department || 'Operations'}</span>
            </div>
          </div>
        </div>

        {/* Local Services Infrastructure Status */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-700/60 space-y-4">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2 border-b border-slate-700/60 pb-3">
            <Server className="w-4 h-4 text-emerald-400" /> Local System Telemetry
          </h3>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900 border border-slate-800">
              <span className="flex items-center gap-2 font-semibold text-slate-300">
                <Database className="w-4 h-4 text-blue-400" /> Database Engine
              </span>
              <span className="text-emerald-400 font-bold flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5" /> PostgreSQL (Local)
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900 border border-slate-800">
              <span className="flex items-center gap-2 font-semibold text-slate-300">
                <Cpu className="w-4 h-4 text-purple-400" /> Background Jobs Broker
              </span>
              <span className="text-emerald-400 font-bold flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5" /> Celery + Redis
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900 border border-slate-800">
              <span className="flex items-center gap-2 font-semibold text-slate-300">
                <RefreshCw className="w-4 h-4 text-cyan-400" /> Real-time Protocol
              </span>
              <span className="text-emerald-400 font-bold flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5" /> Django Channels (WebSockets)
              </span>
            </div>
          </div>
        </div>

        {/* RBAC Matrix Card */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-700/60 space-y-4 col-span-1 md:col-span-2">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2 border-b border-slate-700/60 pb-3">
            Role-Based Access Control (RBAC) Permissions Matrix
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-800/80 text-slate-400 uppercase font-bold border-b border-slate-700">
                <tr>
                  <th className="px-4 py-2">System Module</th>
                  <th className="px-4 py-2 text-center">Inventory Manager</th>
                  <th className="px-4 py-2 text-center">Warehouse Staff</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                <tr>
                  <td className="px-4 py-2 font-bold text-slate-200">Product Management & Reorder Levels</td>
                  <td className="px-4 py-2 text-center text-emerald-400 font-bold">Full Create / Edit / Archive</td>
                  <td className="px-4 py-2 text-center text-indigo-400">View Only</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 font-bold text-slate-200">Warehouse & Location Hierarchy</td>
                  <td className="px-4 py-2 text-center text-emerald-400 font-bold">Manage Warehouses & Racks</td>
                  <td className="px-4 py-2 text-center text-indigo-400">View Layouts</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 font-bold text-slate-200">Inbound Receipts Validation</td>
                  <td className="px-4 py-2 text-center text-emerald-400 font-bold">Create & Validate</td>
                  <td className="px-4 py-2 text-center text-emerald-400 font-bold">Create & Validate</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 font-bold text-slate-200">Outbound Delivery Validation</td>
                  <td className="px-4 py-2 text-center text-emerald-400 font-bold">Create & Validate</td>
                  <td className="px-4 py-2 text-center text-emerald-400 font-bold">Create & Validate</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 font-bold text-slate-200">Internal Location Transfers</td>
                  <td className="px-4 py-2 text-center text-emerald-400 font-bold">Schedule & Execute</td>
                  <td className="px-4 py-2 text-center text-emerald-400 font-bold">Schedule & Execute</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 font-bold text-slate-200">Inventory Adjustments</td>
                  <td className="px-4 py-2 text-center text-emerald-400 font-bold">Audit & Reconcile</td>
                  <td className="px-4 py-2 text-center text-amber-400">Draft Only</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 font-bold text-slate-200">Stock Ledger & Export</td>
                  <td className="px-4 py-2 text-center text-emerald-400 font-bold">Full Export CSV Access</td>
                  <td className="px-4 py-2 text-center text-emerald-400 font-bold">Full Export CSV Access</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
