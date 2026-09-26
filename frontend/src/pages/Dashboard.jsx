import React, { useState, useEffect } from 'react';
import {
  Package, Boxes, AlertTriangle, XCircle, ArrowDownRight, ArrowUpRight,
  Repeat, Filter, RefreshCw
} from 'lucide-react';
import {
  ResponsiveContainer, AreaChart, Area, BarChart, Bar, XAxis, YAxis,
  Tooltip, CartesianGrid, Legend, Cell, PieChart, Pie
} from 'recharts';
import StatCard from '../components/StatCard';
import { useSocket } from '../context/SocketContext';
import api from '../api/axios';

const Dashboard = () => {
  const [kpis, setKpis] = useState(null);
  const [charts, setCharts] = useState(null);
  const [warehouses, setWarehouses] = useState([]);
  const [categories, setCategories] = useState([]);

  // Filters
  const [selectedWarehouse, setSelectedWarehouse] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [loading, setLoading] = useState(true);

  const { lastMessage } = useSocket();

  useEffect(() => {
    fetchAuxiliaryData();
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [selectedWarehouse, selectedCategory]);

  // Real-time WebSocket trigger
  useEffect(() => {
    if (lastMessage) {
      console.log('⚡ Dashboard auto-refreshing via WebSocket trigger:', lastMessage);
      fetchDashboardData();
    }
  }, [lastMessage]);

  const fetchAuxiliaryData = async () => {
    try {
      const [whRes, catRes] = await Promise.all([
        api.get('/warehouses/'),
        api.get('/categories/')
      ]);
      setWarehouses(whRes.data.results || whRes.data || []);
      setCategories(catRes.data.results || catRes.data || []);
    } catch (e) {
      console.error('Error fetching filter options:', e);
    }
  };

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const params = {};
      if (selectedWarehouse) params.warehouse = selectedWarehouse;
      if (selectedCategory) params.category = selectedCategory;

      const [kpiRes, chartRes] = await Promise.all([
        api.get('/dashboard/kpis/', { params }),
        api.get('/dashboard/charts/', { params })
      ]);

      setKpis(kpiRes.data);
      setCharts(chartRes.data);
    } catch (e) {
      console.error('Error loading dashboard data:', e);
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel p-5 rounded-2xl">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            Inventory Dashboard
          </h2>
          <p className="text-xs text-slate-400">Real-time telemetry and KPI stock metrics</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-slate-400 font-semibold">
            <Filter className="w-4 h-4 text-indigo-400" /> Filters:
          </div>

          {/* Warehouse Filter */}
          <select
            value={selectedWarehouse}
            onChange={(e) => setSelectedWarehouse(e.target.value)}
            className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs font-semibold focus:outline-none focus:border-indigo-500 text-slate-200"
          >
            <option value="">All Warehouses</option>
            {warehouses.map((w) => (
              <option key={w.id} value={w.id}>{w.name} ({w.code})</option>
            ))}
          </select>

          {/* Category Filter */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs font-semibold focus:outline-none focus:border-indigo-500 text-slate-200"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>

          <button
            onClick={fetchDashboardData}
            className="p-2 rounded-xl bg-slate-800 border border-slate-700 hover:bg-slate-700 text-slate-300 transition"
            title="Refresh Data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Products"
          value={kpis?.total_products ?? '—'}
          icon={Package}
          color="indigo"
          subtitle="Catalog Active Products"
        />
        <StatCard
          title="Total Stock Units"
          value={kpis?.total_stock_quantity ?? '—'}
          icon={Boxes}
          color="emerald"
          subtitle="Physical Inventory Units"
        />
        <StatCard
          title="Low Stock Items"
          value={kpis?.low_stock_items ?? '—'}
          icon={AlertTriangle}
          color="amber"
          subtitle="Requires Reorder"
        />
        <StatCard
          title="Out of Stock Items"
          value={kpis?.out_of_stock_items ?? '—'}
          icon={XCircle}
          color="rose"
          subtitle="Critical Shortage"
        />
      </div>

      {/* Document Operations Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Pending Receipts"
          value={kpis?.pending_receipts ?? '—'}
          icon={ArrowDownRight}
          color="blue"
          subtitle="Incoming Stock Orders"
        />
        <StatCard
          title="Pending Deliveries"
          value={kpis?.pending_deliveries ?? '—'}
          icon={ArrowUpRight}
          color="purple"
          subtitle="Outgoing Customer Orders"
        />
        <StatCard
          title="Scheduled Transfers"
          value={kpis?.scheduled_transfers ?? '—'}
          icon={Repeat}
          color="cyan"
          subtitle="Internal Location Moves"
        />
      </div>

      {/* Charts Section Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Stock Movement Timeline */}
        <div className="glass-panel p-5 rounded-2xl space-y-4">
          <h3 className="text-sm font-bold text-slate-200">Stock Movement History (Last 7 Days)</h3>
          <div className="h-64">
            {charts?.stock_movement_timeline ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={charts.stock_movement_timeline}>
                  <defs>
                    <linearGradient id="receiptColor" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="deliveryColor" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                  <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }} />
                  <Legend />
                  <Area type="monotone" dataKey="receipts" name="Receipts (+)" stroke="#10b981" fillOpacity={1} fill="url(#receiptColor)" />
                  <Area type="monotone" dataKey="deliveries" name="Deliveries (-)" stroke="#8b5cf6" fillOpacity={1} fill="url(#deliveryColor)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs">Loading chart data...</div>
            )}
          </div>
        </div>

        {/* Low Stock Alert Bar Chart */}
        <div className="glass-panel p-5 rounded-2xl space-y-4">
          <h3 className="text-sm font-bold text-slate-200">Low Stock Level Warnings</h3>
          <div className="h-64">
            {charts?.low_stock_chart ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={charts.low_stock_chart}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="sku" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }} />
                  <Legend />
                  <Bar dataKey="current_stock" name="Current Stock" fill="#f59e0b" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="reorder_level" name="Reorder Threshold" fill="#ef4444" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs">Loading chart data...</div>
            )}
          </div>
        </div>

        {/* Warehouse Inventory Distribution */}
        <div className="glass-panel p-5 rounded-2xl space-y-4">
          <h3 className="text-sm font-bold text-slate-200">Warehouse Distribution</h3>
          <div className="h-64">
            {charts?.warehouse_distribution ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={charts.warehouse_distribution}
                    dataKey="total_stock"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={({ name, total_stock }) => `${name}: ${total_stock}`}
                  >
                    {charts.warehouse_distribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs">Loading chart data...</div>
            )}
          </div>
        </div>

        {/* Incoming vs Outgoing Summary */}
        <div className="glass-panel p-5 rounded-2xl space-y-4 flex flex-col justify-between">
          <h3 className="text-sm font-bold text-slate-200">Total Volume Analysis</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-center">
              <p className="text-xs text-emerald-400 font-semibold uppercase">Total Incoming Stock</p>
              <h4 className="text-3xl font-extrabold text-white mt-1">+{charts?.incoming_vs_outgoing?.incoming || 0}</h4>
              <p className="text-[11px] text-slate-400 mt-1">Units Received</p>
            </div>
            <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/30 text-center">
              <p className="text-xs text-purple-400 font-semibold uppercase">Total Outgoing Stock</p>
              <h4 className="text-3xl font-extrabold text-white mt-1">-{charts?.incoming_vs_outgoing?.outgoing || 0}</h4>
              <p className="text-[11px] text-slate-400 mt-1">Units Dispatched</p>
            </div>
          </div>
          <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-700/50 text-xs text-slate-400">
            <span className="font-bold text-indigo-400">✨ Real-time Telemetry:</span> Dashboard updates automatically via WebSockets on every receipt, delivery, transfer, or adjustment validation.
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
