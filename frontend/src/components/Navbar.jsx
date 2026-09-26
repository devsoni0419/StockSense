import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Bell, Sun, Moon, LogOut, User, Wifi, WifiOff, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useSocket } from '../context/SocketContext';
import api from '../api/axios';

const Navbar = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { isConnected, toastMessage, setToastMessage } = useSocket();
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState('');
  const [notifications, setNotifications] = useState([]);
  const [showNotifMenu, setShowNotifMenu] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      const res = await api.get('/notifications/');
      setNotifications(res.data.results || res.data || []);
    } catch (e) {
      console.error("Error fetching notifications:", e);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/products?search=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const markAllRead = async () => {
    try {
      await api.post('/notifications/mark_all_read/');
      setNotifications(notifications.map(n => ({ ...n, is_read: true })));
    } catch (e) {
      console.error("Error marking read:", e);
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <header className="h-16 glass-panel border-b border-slate-700/60 sticky top-0 z-20 px-6 flex items-center justify-between">
      {/* Global Search Bar */}
      <form onSubmit={handleSearchSubmit} className="relative w-80">
        <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
        <input
          type="text"
          placeholder="Search SKU, Product, Receipt..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 bg-slate-900/80 border border-slate-700/70 rounded-xl text-sm focus:outline-none focus:border-indigo-500 text-slate-100 placeholder:text-slate-500 transition"
        />
      </form>

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        {/* WebSocket Real-time Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/80 border border-slate-700/60 text-xs font-semibold">
          {isConnected ? (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span className="text-emerald-400">Live WS</span>
            </>
          ) : (
            <>
              <WifiOff className="w-3.5 h-3.5 text-amber-400" />
              <span className="text-amber-400">Connecting...</span>
            </>
          )}
        </div>

        {/* Live Toast Banner */}
        {toastMessage && (
          <div className="hidden md:flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-indigo-600/90 text-white text-xs font-medium border border-indigo-400/30 animate-pulse">
            <CheckCircle2 className="w-4 h-4" />
            <span>{toastMessage}</span>
          </div>
        )}

        {/* Notification Bell */}
        <div className="relative">
          <button
            onClick={() => setShowNotifMenu(!showNotifMenu)}
            className="p-2.5 rounded-xl bg-slate-800/80 border border-slate-700/60 text-slate-300 hover:text-white hover:bg-slate-700 transition relative"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-rose-500 text-white font-bold text-[10px] flex items-center justify-center border-2 border-slate-900">
                {unreadCount}
              </span>
            )}
          </button>

          {showNotifMenu && (
            <div className="absolute right-0 mt-2 w-80 glass-panel rounded-2xl border border-slate-700 shadow-2xl p-4 space-y-3 z-50 animate-fade-in">
              <div className="flex items-center justify-between border-b border-slate-700/60 pb-2">
                <h4 className="text-sm font-bold text-slate-100">Notifications</h4>
                {unreadCount > 0 && (
                  <button onClick={markAllRead} className="text-xs text-indigo-400 hover:underline">
                    Mark all read
                  </button>
                )}
              </div>
              <div className="max-h-64 overflow-y-auto space-y-2">
                {notifications.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-4">No notifications yet.</p>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      className={`p-2.5 rounded-xl text-xs border ${
                        n.is_read ? 'bg-slate-900/40 border-slate-800 text-slate-400' : 'bg-indigo-950/40 border-indigo-500/30 text-slate-200'
                      }`}
                    >
                      <p className="font-semibold text-slate-100">{n.title}</p>
                      <p className="mt-1 leading-relaxed">{n.message}</p>
                      <p className="text-[10px] text-slate-500 mt-1">{new Date(n.created_at).toLocaleTimeString()}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Dark / Light Mode Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2.5 rounded-xl bg-slate-800/80 border border-slate-700/60 text-slate-300 hover:text-white hover:bg-slate-700 transition"
          title="Toggle Theme"
        >
          {theme === 'dark' ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5 text-indigo-400" />}
        </button>

        {/* User Profile Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-3 p-1.5 pr-3 rounded-xl bg-slate-800/80 border border-slate-700/60 hover:bg-slate-700 transition"
          >
            <div className="w-8 h-8 rounded-lg bg-indigo-600 text-white font-bold flex items-center justify-center text-sm">
              {user?.first_name ? user.first_name[0] : user?.username?.[0] || 'U'}
            </div>
            <span className="text-xs font-semibold text-slate-200 hidden sm:inline">{user?.first_name || user?.username}</span>
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-48 glass-panel rounded-2xl border border-slate-700 shadow-2xl p-2 z-50 animate-fade-in">
              <div className="p-2 border-b border-slate-700/60">
                <p className="text-xs font-bold text-slate-200">{user?.first_name} {user?.last_name}</p>
                <p className="text-[11px] text-slate-400 truncate">{user?.email}</p>
              </div>
              <button
                onClick={() => { setShowUserMenu(false); navigate('/settings'); }}
                className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 rounded-xl transition"
              >
                <User className="w-4 h-4" /> Profile & Settings
              </button>
              <button
                onClick={logout}
                className="w-full flex items-center gap-2 px-3 py-2 text-xs font-semibold text-rose-400 hover:bg-rose-500/10 rounded-xl transition"
              >
                <LogOut className="w-4 h-4" /> Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
