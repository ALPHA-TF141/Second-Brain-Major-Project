import { useEffect, useState } from 'react';
import { AlertTriangle, Bell, CheckCircle2, Loader2, Mail, RefreshCw, Trash2, Zap } from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';
import { apiFetch } from '../services/apiClient.js';

/**
 * NotificationsWorkspace - real alerts only.
 * ---------------------------------------------------------------------------
 * Every item here was produced by an agent (mail ingestion, insight collisions,
 * vault syncs). Nothing is seeded, so an empty list genuinely means "nothing
 * has happened yet" rather than "here are some example cards".
 */
const KINDS = {
  email_action: { label: 'EMAIL ACTION', color: 'text-amber-300', bg: 'bg-amber-400/10', icon: Mail },
  email_important: { label: 'IMPORTANT MAIL', color: 'text-red-300', bg: 'bg-red-400/10', icon: Mail },
  email: { label: 'MAIL', color: 'text-cyan-300', bg: 'bg-cyan-400/10', icon: Mail },
  insight: { label: 'INSIGHT', color: 'text-purple-300', bg: 'bg-purple-400/10', icon: Zap },
  info: { label: 'SYSTEM', color: 'text-slate-300', bg: 'bg-white/5', icon: Bell }
};

const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'unread', label: 'Unread' },
  { id: 'important', label: 'Important' },
  { id: 'mail', label: 'Mail' }
];

function relativeTime(value) {
  if (!value) return '';
  const then = new Date(value);
  if (Number.isNaN(then.getTime())) return '';
  const seconds = Math.floor((Date.now() - then.getTime()) / 1000);
  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return then.toLocaleDateString(undefined, { day: 'numeric', month: 'short' });
}

export default function NotificationsWorkspace() {
  const { apiClient } = useBackend();
  const [notifications, setNotifications] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load() {
    setLoading(true);
    setError('');
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/os/notifications?limit=100`);
      if (!res.ok) {
        setError('Could not load notifications.');
        setNotifications([]);
      } else {
        const data = await res.json();
        setNotifications(Array.isArray(data) ? data : []);
      }
    } catch {
      setError('Backend unreachable.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const timer = setInterval(load, 30000);
    return () => clearInterval(timer);
  }, []);

  async function markRead(item) {
    if (item.read) return;
    setNotifications((current) => current.map((n) => (n.id === item.id ? { ...n, read: true } : n)));
    try {
      await apiFetch(`${apiClient.baseUrl}/api/os/notifications/${item.id}/read`, { method: 'POST' });
    } catch {
      // optimistic update is fine; the next poll reconciles
    }
  }

  async function clearRead() {
    try {
      await apiFetch(`${apiClient.baseUrl}/api/os/notifications?only_read=true`, { method: 'DELETE' });
      await load();
    } catch {
      // ignore
    }
  }

  const visible = notifications.filter((n) => {
    if (filter === 'unread') return !n.read;
    if (filter === 'important') return n.priority === 'high';
    if (filter === 'mail') return String(n.source) === 'mail' || String(n.kind).startsWith('email');
    return true;
  });

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div className="flex h-full w-full flex-col bg-[#111318] p-6 text-slate-100 font-sans select-none overflow-y-auto thin-scrollbar">
      <div className="mx-auto w-full max-w-4xl space-y-5">
        {/* Header */}
        <div className="flex flex-wrap items-end justify-between gap-3 border-b border-white/10 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Bell size={18} className="text-cyan-400" />
              <h2 className="text-base font-bold text-white uppercase tracking-wider font-mono">Notifications</h2>
              {unreadCount > 0 && (
                <span className="rounded bg-cyan-400/10 px-2 py-0.5 text-[10px] font-mono font-bold text-cyan-300">
                  {unreadCount} UNREAD
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Real alerts raised by your agents - mail deadlines, important messages, insights. Nothing here is seeded.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={load}
              className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 hover:bg-white/10"
            >
              <RefreshCw size={12} className={loading ? 'animate-spin' : ''} /> Refresh
            </button>
            <button
              type="button"
              onClick={clearRead}
              disabled={!notifications.some((n) => n.read)}
              className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 hover:bg-white/10 disabled:opacity-40"
            >
              <Trash2 size={12} /> Clear read
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex gap-1">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              type="button"
              onClick={() => setFilter(f.id)}
              className={`rounded-lg px-3 py-1.5 text-xs transition ${
                filter === f.id ? 'bg-white/10 text-white font-semibold' : 'text-slate-400 hover:bg-white/5'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {error && (
          <div className="rounded-xl border border-red-400/20 bg-red-500/10 p-3 text-[11px] text-red-200">
            {error}
          </div>
        )}

        {loading && notifications.length === 0 && (
          <div className="flex items-center justify-center py-12 text-xs text-slate-500">
            <Loader2 size={14} className="animate-spin mr-2" /> Loading…
          </div>
        )}

        {!loading && visible.length === 0 && (
          <div className="rounded-2xl border border-white/10 bg-[#0f1422] p-10 text-center">
            <Bell size={22} className="mx-auto text-slate-600" />
            <p className="mt-3 text-xs text-slate-400">
              {notifications.length === 0
                ? 'No notifications yet. Connect a mailbox and sync - deadlines Jarvis finds will show up here.'
                : 'Nothing matches this filter.'}
            </p>
          </div>
        )}

        <div className="space-y-2">
          {visible.map((item) => {
            const kind = KINDS[item.kind] || KINDS.info;
            const Icon = kind.icon;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => markRead(item)}
                className={`w-full rounded-xl border p-3.5 text-left transition hover:border-cyan-400/30 ${
                  item.read ? 'border-white/5 bg-[#0f1422]/60' : 'border-white/10 bg-[#0f1422]'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${kind.bg}`}>
                    <Icon size={13} className={kind.color} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      {!item.read && <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />}
                      <p className={`text-xs ${item.read ? 'text-slate-300' : 'font-semibold text-white'}`}>
                        {item.title}
                      </p>
                      {item.priority === 'high' && (
                        <span className="flex items-center gap-1 rounded bg-red-400/10 px-1.5 py-0.5 text-[9px] font-mono font-bold text-red-300">
                          <AlertTriangle size={8} /> HIGH
                        </span>
                      )}
                      <span className={`rounded px-1.5 py-0.5 text-[9px] font-mono ${kind.bg} ${kind.color}`}>
                        {kind.label}
                      </span>
                    </div>
                    {item.body && (
                      <p className="mt-1 text-[11px] text-slate-400 leading-relaxed break-words">{item.body}</p>
                    )}
                  </div>
                  <span className="shrink-0 text-[10px] text-slate-500">{relativeTime(item.timestamp)}</span>
                </div>
              </button>
            );
          })}
        </div>

        {notifications.length > 0 && (
          <p className="flex items-center gap-1.5 border-t border-white/5 pt-4 text-[11px] text-slate-500">
            <CheckCircle2 size={11} /> Click a notification to mark it read. Auto-refreshes every 30 seconds.
          </p>
        )}
      </div>
    </div>
  );
}
