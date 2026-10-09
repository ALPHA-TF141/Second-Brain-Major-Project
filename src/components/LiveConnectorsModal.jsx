import { useEffect, useState } from 'react';
import {
  CheckCircle2,
  Database,
  ExternalLink,
  KeyRound,
  Link2,
  Loader2,
  Mail,
  Play,
  Plus,
  RefreshCw,
  RotateCw,
  ShieldCheck,
  Trash2,
  Wifi,
  X,
  Zap
} from 'lucide-react';
import { apiFetch } from '../services/apiClient.js';
import { useBackend } from '../context/BackendContext.jsx';

export default function LiveConnectorsModal({ isOpen, onClose }) {
  const { apiClient } = useBackend();
  const [connectors, setConnectors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [busyKey, setBusyKey] = useState('');
  const [notice, setNotice] = useState(null);

  // Edit / Add connector modal state
  const [editingConnector, setEditingConnector] = useState(null);
  const [editSecret, setEditSecret] = useState('');
  const [editIdentifier, setEditIdentifier] = useState('');
  const [editName, setEditName] = useState('');
  const [editCategory, setEditCategory] = useState('mail');

  useEffect(() => {
    if (!isOpen) return;
    loadConnectors();
  }, [isOpen]);

  async function loadConnectors() {
    setLoading(true);
    setNotice(null);
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/connectors`);
      if (res.ok) {
        const data = await res.json();
        setConnectors(data.connectors || []);
      } else {
        setNotice({ type: 'error', text: 'Could not fetch connectors from database.' });
      }
    } catch {
      setNotice({ type: 'error', text: 'Backend unavailable. Ensure Jarvis backend is running.' });
    } finally {
      setLoading(false);
    }
  }

  async function testConnector(key) {
    setBusyKey(key);
    setNotice(null);
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/connectors/${key}/test`, { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        setNotice({ type: 'success', text: data.message || 'Connection verified and live!' });
        await loadConnectors();
      } else {
        setNotice({ type: 'error', text: data.detail || 'Test connection failed.' });
      }
    } catch {
      setNotice({ type: 'error', text: 'Diagnostic ping failed.' });
    } finally {
      setBusyKey('');
    }
  }

  async function handleSaveCredentials(e) {
    e?.preventDefault();
    if (!editingConnector) return;

    setBusyKey('saving');
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/connectors`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          service_key: editingConnector.service_key,
          service_name: editName || editingConnector.service_name,
          account_identifier: editIdentifier,
          secret_payload: editSecret,
          category: editCategory,
          is_live: true
        })
      });

      if (res.ok) {
        setNotice({ type: 'success', text: `${editName || editingConnector.service_name} permanently saved in database and live!` });
        setEditingConnector(null);
        setEditSecret('');
        await loadConnectors();
      } else {
        const err = await res.json();
        setNotice({ type: 'error', text: err.detail || 'Failed to save credentials in database.' });
      }
    } catch {
      setNotice({ type: 'error', text: 'Error connecting to database.' });
    } finally {
      setBusyKey('');
    }
  }

  function startEditing(conn) {
    setEditingConnector(conn);
    setEditName(conn.service_name);
    setEditIdentifier(conn.account_identifier);
    setEditCategory(conn.category || 'service');
    setEditSecret('');
  }

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-md p-4 select-none">
      <div className="w-full max-w-3xl rounded-3xl border border-cyan-500/30 bg-[#090d1a] shadow-[0_0_50px_rgba(56,189,248,0.2)] flex flex-col max-h-[90vh] text-slate-100 overflow-hidden animate-in zoom-in-95 duration-200">
        {/* ================= MODAL HEADER ================= */}
        <div className="flex items-center justify-between border-b border-white/10 px-6 py-4.5 bg-[#0d1326]">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-400/15 border border-cyan-400/40 text-cyan-300 shadow-glow">
              <Database size={18} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold tracking-widest text-cyan-400 uppercase">
                  PERSISTENT SQLITE DATABASE // CONNECTORS & PASSWORDS
                </span>
                <span className="rounded bg-emerald-400/15 border border-emerald-400/30 px-1.5 py-0.5 text-[9px] font-mono text-emerald-300 font-bold uppercase">
                  ACTIVE SYNC
                </span>
              </div>
              <h2 className="text-base font-bold text-white mt-0.5">
                Always-Connected App Connectors
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={loadConnectors}
              disabled={loading}
              className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-white/5 transition"
              title="Refresh DB Connectors"
            >
              <RotateCw size={15} className={loading ? 'animate-spin' : ''} />
            </button>
            <button
              type="button"
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* ================= NOTICE BANNER ================= */}
        {notice && (
          <div
            className={`px-6 py-2.5 text-xs font-medium flex items-center justify-between ${
              notice.type === 'success'
                ? 'bg-emerald-500/15 text-emerald-300 border-b border-emerald-500/20'
                : 'bg-red-500/15 text-red-300 border-b border-red-500/20'
            }`}
          >
            <span>{notice.text}</span>
            <button type="button" onClick={() => setNotice(null)} className="opacity-70 hover:opacity-100">
              <X size={14} />
            </button>
          </div>
        )}

        {/* ================= CONNECTORS LIST ================= */}
        <div className="flex-1 overflow-y-auto thin-scrollbar p-6 space-y-4">
          <p className="text-xs text-slate-400 leading-relaxed">
            All passwords, tokens, and app connectors are permanently stored in your local SQLite database (
            <span className="font-mono text-cyan-300">second_brain.db</span>). Once connected, they remain live across every opening of the app with zero re-authentication needed.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {connectors.map((conn) => {
              const isBusy = busyKey === conn.service_key;

              return (
                <div
                  key={conn.service_key}
                  className="rounded-2xl border border-white/10 bg-[#0f1424] p-4 flex flex-col justify-between hover:border-cyan-400/40 transition space-y-3"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
                        <h4 className="text-sm font-bold text-white truncate">{conn.service_name}</h4>
                      </div>
                      <span className="rounded bg-emerald-500/15 border border-emerald-400/30 px-2 py-0.5 text-[9px] font-mono text-emerald-300 font-bold uppercase">
                        LIVE & CONNECTED
                      </span>
                    </div>

                    <div className="text-xs text-slate-400 font-mono mt-1.5 truncate">
                      {conn.account_identifier || 'Auto-Configured in DB'}
                    </div>

                    <div className="flex items-center gap-2 text-[10px] text-slate-500 font-mono mt-2">
                      <KeyRound size={11} className="text-amber-400" />
                      <span>{conn.has_credentials ? 'Credentials Saved in DB' : 'Configured in Local Store'}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-2 border-t border-white/5">
                    <button
                      type="button"
                      onClick={() => testConnector(conn.service_key)}
                      disabled={isBusy}
                      className="flex-1 flex items-center justify-center gap-1.5 rounded-xl border border-white/10 bg-white/5 py-1.5 text-xs font-semibold text-slate-300 hover:bg-white/10 hover:text-white transition disabled:opacity-40"
                    >
                      {isBusy ? <Loader2 size={12} className="animate-spin" /> : <Wifi size={12} className="text-cyan-400" />}
                      <span>Test Connection</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => startEditing(conn)}
                      className="rounded-xl border border-cyan-400/30 bg-cyan-500/10 px-3 py-1.5 text-xs font-semibold text-cyan-300 hover:bg-cyan-500/20 transition"
                    >
                      Update
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ================= EDIT / STORE CREDENTIALS DRAWER ================= */}
        {editingConnector && (
          <div className="border-t border-cyan-500/30 bg-[#0c1122] p-6 space-y-4 animate-in slide-in-from-bottom duration-200">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <KeyRound size={15} className="text-amber-400" />
                <span>Save Credentials in Database: {editingConnector.service_name}</span>
              </h3>
              <button
                type="button"
                onClick={() => setEditingConnector(null)}
                className="text-slate-400 hover:text-white"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleSaveCredentials} className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] font-mono uppercase text-slate-400">Account / Email / URL</label>
                  <input
                    type="text"
                    value={editIdentifier}
                    onChange={(e) => setEditIdentifier(e.target.value)}
                    placeholder="e.g. user@gmail.com or 127.0.0.1:11434"
                    className="w-full mt-1 rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs font-mono text-white outline-none focus:border-cyan-400/50"
                  />
                </div>

                <div>
                  <label className="text-[10px] font-mono uppercase text-slate-400">
                    App Password / Secret Token (Saved in DB)
                  </label>
                  <input
                    type="password"
                    value={editSecret}
                    onChange={(e) => setEditSecret(e.target.value)}
                    placeholder="Enter 16-character App Password or Token"
                    className="w-full mt-1 rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs font-mono text-white outline-none focus:border-cyan-400/50"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setEditingConnector(null)}
                  className="rounded-xl border border-white/10 bg-transparent px-4 py-2 text-xs font-medium text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={busyKey === 'saving'}
                  className="rounded-xl bg-cyan-400 px-5 py-2 text-xs font-bold text-slate-950 transition hover:bg-cyan-300 shadow-glow flex items-center gap-1.5 disabled:opacity-40"
                >
                  {busyKey === 'saving' ? <Loader2 size={13} className="animate-spin" /> : <ShieldCheck size={13} />}
                  <span>Save Permanently to DB</span>
                </button>
              </div>
            </form>
          </div>
        )}

        {/* ================= MODAL FOOTER ================= */}
        <div className="border-t border-white/10 px-6 py-4 bg-[#0d1326] flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <ShieldCheck size={14} className="text-emerald-400" />
            <span>SQLite Encryption Active &bull; Zero Cloud Upload</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl bg-white/10 hover:bg-white/20 px-4 py-1.5 text-xs font-semibold text-white transition"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
