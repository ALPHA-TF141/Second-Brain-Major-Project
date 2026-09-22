import { useEffect, useRef, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  Loader2,
  Link2,
  Mail,
  Calendar,
  Trash2,
  RefreshCw,
  ShieldCheck,
  Info
} from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';
import { apiFetch, openInBrowser } from '../services/apiClient.js';

/**
 * IntegrationsManager
 * ---------------------------------------------------------------------------
 * REAL Google integration. No mock accounts, no fake "Connected" badges.
 *
 * If Google credentials are not configured the page says exactly that and links
 * to the setup steps, instead of pretending a connection exists.
 */
const SUGGESTED_ACCOUNTS = [
  'immanuellourdu@gmail.com',
  'lmariaimmanuel@gmail.com',
  'vtu24334@veltech.edu.in'
];

export default function IntegrationsManager() {
  const { apiClient } = useBackend();

  const [google, setGoogle] = useState({ configured: false, accounts: [], account_count: 0, setup_help: '' });
  const [local, setLocal] = useState({});
  const [pendingEmail, setPendingEmail] = useState('');
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState(null);
  const pollRef = useRef(null);

  const accounts = google.accounts || [];
  const connectedEmails = accounts.map((a) => (a.email || '').toLowerCase());

  async function loadAll() {
    try {
      const [gRes, lRes] = await Promise.all([
        apiFetch(`${apiClient.baseUrl}/api/google/status`),
        apiFetch(`${apiClient.baseUrl}/api/os/integrations`)
      ]);
      if (gRes.ok) setGoogle(await gRes.json());
      if (lRes.ok) setLocal(await lRes.json());
    } catch {
      setNotice({ type: 'error', text: 'Could not reach the backend. Is it running?' });
    }
  }

  useEffect(() => {
    loadAll();
    return () => clearInterval(pollRef.current);
  }, []);

  // After sending the user to Google we poll for the account to appear, because
  // the browser tab is where the flow actually completes.
  function startPolling(expectedEmail) {
    clearInterval(pollRef.current);
    let attempts = 0;
    pollRef.current = setInterval(async () => {
      attempts += 1;
      await loadAll();
      const found = expectedEmail
        ? connectedEmails.includes(expectedEmail.toLowerCase())
        : true;
      if (found && attempts > 1) {
        clearInterval(pollRef.current);
        setNotice({ type: 'success', text: `${expectedEmail || 'Account'} connected.` });
        setPendingEmail('');
      }
      if (attempts > 60) {
        clearInterval(pollRef.current);
        setPendingEmail('');
      }
    }, 2000);
  }

  async function connect(email) {
    const target = (email || pendingEmail || '').trim();
    if (!target) {
      setNotice({ type: 'error', text: 'Enter the email address you want to connect.' });
      return;
    }

    setBusy(target);
    setNotice(null);
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/google/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: target, services: ['gmail', 'calendar'] })
      });
      const data = await res.json();

      if (!res.ok) {
        setNotice({ type: 'error', text: data.detail || 'Could not start the Google sign-in flow.' });
        return;
      }

      const opened = await openInBrowser(data.auth_url);
      if (!opened.ok) {
        setNotice({
          type: 'error',
          text: `Could not open your browser (${opened.error || 'blocked'}). Open this URL manually: ${data.auth_url}`
        });
        return;
      }

      setPendingEmail(target);
      setNotice({
        type: 'info',
        text: `Approve access for ${target} in the browser tab that just opened. This page updates automatically.`
      });
      startPolling(target);
    } catch (err) {
      setNotice({ type: 'error', text: String(err.message || err) });
    } finally {
      setBusy('');
    }
  }

  async function disconnect(account) {
    if (!window.confirm(`Disconnect ${account.email}? Jarvis will forget the access token.`)) return;
    setBusy(account.id);
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/google/accounts/${account.id}`, { method: 'DELETE' });
      if (res.ok) {
        setNotice({ type: 'success', text: `${account.email} disconnected.` });
        await loadAll();
      } else {
        setNotice({ type: 'error', text: 'Could not disconnect that account.' });
      }
    } finally {
      setBusy('');
    }
  }

  const noticeStyles = {
    success: 'border-emerald-400/30 bg-emerald-500/10 text-emerald-200',
    error: 'border-red-400/30 bg-red-500/10 text-red-200',
    info: 'border-cyan-400/30 bg-cyan-500/10 text-cyan-100'
  };

  return (
    <div className="flex h-full w-full flex-col bg-[#111318] p-6 text-slate-100 font-sans select-none overflow-y-auto thin-scrollbar">
      <div className="mx-auto w-full max-w-5xl space-y-6">
        {/* Header */}
        <div className="border-b border-white/10 pb-4 flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Link2 size={18} className="text-cyan-400" />
              <h2 className="text-base font-bold text-white uppercase tracking-wider font-mono">
                Connected Services &amp; Integrations
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Real OAuth connections. Nothing here is simulated - if an account is not linked it stays unlinked.
            </p>
          </div>
          <button
            type="button"
            onClick={loadAll}
            className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 hover:bg-white/10 transition shrink-0"
          >
            <RefreshCw size={12} /> Refresh
          </button>
        </div>

        {/* Notice */}
        {notice && (
          <div className={`rounded-xl border px-4 py-3 text-xs leading-relaxed flex items-start gap-2 ${noticeStyles[notice.type] || noticeStyles.info}`}>
            {notice.type === 'error' ? <AlertTriangle size={14} className="mt-0.5 shrink-0" />
              : notice.type === 'success' ? <CheckCircle2 size={14} className="mt-0.5 shrink-0" />
                : <Loader2 size={14} className="mt-0.5 shrink-0 animate-spin" />}
            <span className="break-all">{notice.text}</span>
          </div>
        )}

        {/* Not configured */}
        {!google.configured && (
          <div className="rounded-2xl border border-amber-400/30 bg-amber-500/5 p-5 space-y-3">
            <div className="flex items-center gap-2 text-amber-300">
              <AlertTriangle size={16} />
              <h3 className="text-sm font-bold uppercase tracking-wider font-mono">Google is not configured yet</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Connecting Gmail and Calendar needs OAuth credentials from your own Google Cloud project.
              This is a one-time, ~5 minute setup - Google requires it so that no third party (including
              me) ever handles your password.
            </p>
            <div className="rounded-xl border border-white/10 bg-black/30 p-3">
              <p className="text-[11px] font-mono text-slate-400 mb-1.5">Add to backend/.env :</p>
              <pre className="text-[11px] font-mono text-cyan-300 whitespace-pre-wrap break-all">{`GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret`}</pre>
              <p className="text-[11px] font-mono text-slate-500 mt-2">
                Redirect URI to register: <span className="text-amber-300">{google.redirect_uri}</span>
              </p>
            </div>
            <p className="text-xs text-slate-400">
              Full walkthrough: open <span className="font-mono text-cyan-300">GOOGLE_SETUP.md</span> in the project root.
            </p>
          </div>
        )}

        {/* Google accounts */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Mail size={14} className="text-red-400" />
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">
              Google Accounts - Gmail &amp; Calendar
            </h3>
            <span className={`ml-auto rounded px-2 py-0.5 text-[10px] font-mono font-bold ${
              accounts.length ? 'bg-emerald-400/10 text-emerald-300' : 'bg-slate-500/10 text-slate-400'
            }`}>
              {accounts.length ? `${accounts.length} CONNECTED` : 'NONE CONNECTED'}
            </span>
          </div>

          {/* Connected accounts */}
          {accounts.map((account) => (
            <div key={account.id} className="rounded-2xl border border-emerald-400/20 bg-[#0f1422] p-4 flex items-center gap-3">
              {account.picture
                ? <img src={account.picture} alt="" className="h-9 w-9 rounded-full border border-white/10" />
                : <div className="h-9 w-9 rounded-full bg-emerald-400/10 border border-emerald-400/20 flex items-center justify-center">
                    <Mail size={14} className="text-emerald-300" />
                  </div>}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-semibold text-white truncate">{account.email}</p>
                  <CheckCircle2 size={12} className="text-emerald-400 shrink-0" />
                </div>
                <p className="text-[11px] text-slate-400 truncate">
                  {account.name || 'Google account'} · {account.services?.join(', ') || 'gmail, calendar'}
                </p>
                {account.status === 'error' && (
                  <p className="text-[11px] text-red-300 mt-0.5">Token problem - reconnect this account.</p>
                )}
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                <span className="hidden sm:inline-flex items-center gap-1 rounded bg-white/5 border border-white/10 px-2 py-1 text-[10px] font-mono text-slate-400">
                  <ShieldCheck size={10} /> read-only
                </span>
                <button
                  type="button"
                  onClick={() => disconnect(account)}
                  disabled={busy === account.id}
                  className="rounded-lg border border-red-400/20 bg-red-500/10 p-2 text-red-300 hover:bg-red-500/20 transition disabled:opacity-40"
                  title="Disconnect"
                >
                  {busy === account.id ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
                </button>
              </div>
            </div>
          ))}

          {/* Connect flow */}
          {google.configured && (
            <div className="rounded-2xl border border-white/10 bg-[#0f1422] p-4 space-y-3">
              <p className="text-xs text-slate-300">
                Connect an account. Your browser opens Google's consent screen, then this page updates itself.
              </p>

              <div className="flex flex-wrap gap-2">
                {SUGGESTED_ACCOUNTS.map((email) => {
                  const done = connectedEmails.includes(email.toLowerCase());
                  return (
                    <button
                      key={email}
                      type="button"
                      disabled={done || busy === email || !!pendingEmail}
                      onClick={() => connect(email)}
                      className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-semibold transition ${
                        done
                          ? 'border-emerald-400/20 bg-emerald-500/10 text-emerald-300 cursor-default'
                          : 'border-cyan-400/30 bg-cyan-500/10 text-cyan-200 hover:bg-cyan-500/20 disabled:opacity-40'
                      }`}
                    >
                      {busy === email ? <Loader2 size={12} className="animate-spin" />
                        : done ? <CheckCircle2 size={12} /> : <ExternalLink size={12} />}
                      {email}
                    </button>
                  );
                })}
              </div>

              <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-white/5">
                <input
                  value={pendingEmail}
                  onChange={(e) => setPendingEmail(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') connect(); }}
                  placeholder="or type another Google address..."
                  className="min-w-0 flex-1 rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-xs outline-none focus:border-cyan-400/40"
                />
                <button
                  type="button"
                  onClick={() => connect()}
                  disabled={!pendingEmail.trim() || !!busy}
                  className="rounded-lg bg-cyan-400 px-4 py-2 text-xs font-bold text-slate-950 disabled:opacity-40"
                >
                  Connect
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Local services (honest reporting) */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Info size={14} className="text-slate-400" />
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">
              Local Services
            </h3>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {['github', 'ollama', 'scraper'].map((key) => {
              const item = local[key];
              if (!item) return null;
              return (
                <div key={key} className="rounded-xl border border-white/10 bg-[#0f1422] p-3.5">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold text-white">{item.service_name || key}</p>
                    <span className={`rounded px-1.5 py-0.5 text-[10px] font-mono font-bold ${
                      item.connected ? 'bg-emerald-400/10 text-emerald-300' : 'bg-amber-400/10 text-amber-300'
                    }`}>
                      {item.connected ? 'CONNECTED' : 'NOT CONNECTED'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">{item.description}</p>
                </div>
              );
            })}
          </div>
        </div>

        <p className="text-[11px] text-slate-500 leading-relaxed border-t border-white/5 pt-4">
          <ShieldCheck size={11} className="inline mb-0.5" /> Jarvis requests read-only access
          (<span className="font-mono">gmail.readonly</span>, <span className="font-mono">calendar.readonly</span>).
          It cannot send, delete, or modify anything. Tokens are encrypted on disk under{' '}
          <span className="font-mono">backend/data/</span>, which is git-ignored and never synced to your vault.
        </p>
      </div>
    </div>
  );
}
