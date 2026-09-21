import { useEffect, useState } from 'react';
import { Link2, ShieldCheck, CheckCircle2, AlertCircle, RefreshCw, Key, ExternalLink, Cpu, GitBranch, Globe, Mail, Calendar } from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';

export default function IntegrationsManager() {
  const { apiClient } = useBackend();
  const [integrations, setIntegrations] = useState({});
  const [connectingKey, setConnectingKey] = useState(null);
  const [accountEmail, setAccountEmail] = useState('');

  async function loadIntegrations() {
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/os/integrations`);
      if (res.ok) {
        const data = await res.json();
        setIntegrations(data);
      }
    } catch {
      //
    }
  }

  useEffect(() => {
    loadIntegrations();
  }, []);

  async function toggleConnect(key, currentlyConnected) {
    if (!currentlyConnected && key !== 'github' && key !== 'ollama' && key !== 'scraper') {
      setConnectingKey(key);
      return;
    }

    try {
      const res = await fetch(`${apiClient.baseUrl}/api/os/integrations/${key}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          connected: !currentlyConnected,
          email: currentlyConnected ? '' : (accountEmail || 'immanuel.user@university.edu')
        })
      });
      if (res.ok) {
        await loadIntegrations();
        setConnectingKey(null);
      }
    } catch {
      //
    }
  }

  return (
    <div className="flex h-full w-full flex-col bg-[#111318] p-6 text-slate-100 font-sans select-none overflow-y-auto thin-scrollbar">
      <div className="mx-auto w-full max-w-5xl space-y-6">
        <div className="border-b border-white/10 pb-4">
          <div className="flex items-center gap-2">
            <Link2 size={18} className="text-cyan-400" />
            <h2 className="text-base font-bold text-white uppercase tracking-wider font-mono">Connected Services & Integrations</h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">Manage external APIs, local AI acceleration, and permission boundaries.</p>
        </div>

        {/* Integrations Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(integrations).map(([key, item]) => {
            const isConn = item.connected;

            return (
              <div
                key={key}
                className={`rounded-2xl border p-5 flex flex-col justify-between transition ${
                  isConn ? 'border-cyan-500/25 bg-[#161820]' : 'border-white/5 bg-black/40'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`h-2.5 w-2.5 rounded-full ${isConn ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}`} />
                      <h4 className="text-sm font-bold text-white">{item.service_name}</h4>
                    </div>
                    <span className={`text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded-full border ${isConn ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400' : 'border-slate-700 bg-slate-800 text-slate-400'}`}>
                      {isConn ? 'Connected' : 'Not Connected'}
                    </span>
                  </div>

                  <p className="text-xs text-slate-400 leading-relaxed mb-3">{item.description}</p>

                  {/* Permissions Granted */}
                  {item.permissions && (
                    <div className="space-y-1 mb-3">
                      <span className="text-[10px] font-mono text-slate-500 uppercase block font-bold">Permissions:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {item.permissions.map((p) => (
                          <span key={p} className="rounded bg-white/5 border border-white/5 px-2 py-0.5 text-[10px] text-slate-300 font-mono">
                            ✓ {p}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="pt-3 border-t border-white/5 flex items-center justify-between">
                  {item.account && (
                    <span className="text-[11px] font-mono text-cyan-300">Account: {item.account}</span>
                  )}
                  {item.email && (
                    <span className="text-[11px] font-mono text-cyan-300">{item.email}</span>
                  )}
                  {!item.account && !item.email && <span className="text-[10px] text-slate-500 font-mono">Self-Hosted</span>}

                  <button
                    type="button"
                    onClick={() => toggleConnect(key, isConn)}
                    className={`rounded-xl px-4 py-1.5 text-xs font-bold transition ${
                      isConn
                        ? 'border border-red-500/30 bg-red-500/10 text-red-300 hover:bg-red-500/20'
                        : 'bg-cyan-400 text-slate-950 hover:bg-cyan-300 shadow-glow'
                    }`}
                  >
                    {isConn ? 'Disconnect' : 'Connect Account'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
