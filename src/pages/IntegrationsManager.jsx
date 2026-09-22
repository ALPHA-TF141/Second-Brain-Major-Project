import { useEffect, useRef, useState } from 'react';
import {
  AlertTriangle, Brain, Calendar, CheckCircle2, ChevronDown, ExternalLink, Info,
  KeyRound, Link2, Loader2, Mail, RefreshCw, ShieldCheck, Trash2, Zap
} from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';
import { apiFetch, openInBrowser } from '../services/apiClient.js';

/**
 * IntegrationsManager
 * ---------------------------------------------------------------------------
 * Two honest ways to connect real mail and calendar data:

 *   MAIL     Gmail App Password over IMAP
 *              - no Google Cloud project, no verification, no expiry, free
 *              - works for personal Gmail accounts
 *   MAIL     Google OAuth  (secondary)
 *              - required for Workspace/college accounts since May 2025
 *              - needs a Client ID/Secret and, to publish, Google verification
 *   CALENDAR Private iCal address (ICS)
 *              - no OAuth at all, read-only, free, never expires

 * Nothing here is simulated. If something is not connected it says so.
 */
const ACCOUNTS = [
  { email: 'immanuellourdu@gmail.com', kind: 'personal' },
  { email: 'lmariaimmanuel@gmail.com', kind: 'personal' },
  { email: 'vtu24334@veltech.edu.in', kind: 'workspace' }
];

export default function IntegrationsManager() {
  const { apiClient } = useBackend();

  const [mailAccounts, setMailAccounts] = useState([]);
  const [calendarSources, setCalendarSources] = useState([]);
  const [google, setGoogle] = useState({ configured: false, accounts: [] });
  const [local, setLocal] = useState({});

  const [imapEmail, setImapEmail] = useState('');
  const [imapPassword, setImapPassword] = useState('');
  const [imapLabel, setImapLabel] = useState('');
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState(null);
  const [showImapHelp, setShowImapHelp] = useState(false);

  const [icsUrl, setIcsUrl] = useState('');
  const [icsLabel, setIcsLabel] = useState('');
  const [showIcsHelp, setShowIcsHelp] = useState(false);

  const pollRef = useRef(null);

  // Mail -> Brain ingestion
  const [syncStatus, setSyncStatus] = useState(null);
  const [syncResult, setSyncResult] = useState(null);
  const [syncing, setSyncing] = useState(false);

  const mailEmails = mailAccounts.map((a) => (a.email || '').toLowerCase());

  async function loadAll() {
    try {
      const [mailRes, calRes, googRes, localRes, syncRes] = await Promise.all([
        apiFetch(`${apiClient.baseUrl}/api/mail/accounts`),
        apiFetch(`${apiClient.baseUrl}/api/calendar/sources`),
        apiFetch(`${apiClient.baseUrl}/api/google/status`),
        apiFetch(`${apiClient.baseUrl}/api/os/integrations`),
        apiFetch(`${apiClient.baseUrl}/api/mail/sync/status`)
      ]);
      if (mailRes.ok) setMailAccounts(await mailRes.json());
      if (calRes.ok) setCalendarSources(await calRes.json());
      if (googRes.ok) setGoogle(await googRes.json());
      if (localRes.ok) setLocal(await localRes.json());
      if (syncRes.ok) setSyncStatus(await syncRes.json());
    } catch {
      setNotice({ type: 'error', text: 'Could not reach the backend. Is it running?' });
    }
  }

  useEffect(() => {
    loadAll();
    return () => clearInterval(pollRef.current);
  }, []);

  function pollFor(expectedEmail) {
    clearInterval(pollRef.current);
    let attempts = 0;
    pollRef.current = setInterval(async () => {
      attempts += 1;
      const res = await apiFetch(`${apiClient.baseUrl}/api/mail/accounts`);
      const list = res.ok ? await res.json() : [];
      if (list.some((a) => (a.email || '').toLowerCase() === expectedEmail.toLowerCase())) {
        clearInterval(pollRef.current);
        await loadAll();
        setNotice({ type: 'success', text: `${expectedEmail} connected.` });
      }
      if (attempts > 60) clearInterval(pollRef.current);
    }, 2000);
  }

  /* ---------------------------------------------------- IMAP connect */
  async function connectImap(email) {
    const address = (email || imapEmail).trim();
    const password = imapPassword.replace(/\s/g, '');

    if (!address) { setNotice({ type: 'error', text: 'Enter the email address.' }); return; }
    if (!password) { setNotice({ type: 'error', text: 'Enter the 16-character App Password.' }); return; }

    setBusy(address);
    setNotice({ type: 'info', text: `Signing in to ${address} to verify the password…` });
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/mail/imap/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: address, app_password: password, label: imapLabel })
      });
      const data = await res.json();

      if (!res.ok) {
        setNotice({ type: 'error', text: data.detail || 'Could not connect that account.' });
        return;
      }

      setNotice({
        type: 'success',
        text: `${address} connected. ${data.verified?.total_messages ?? 0} messages, ` +
              `${data.verified?.unread ?? 0} unread.`
      });
      setImapPassword('');
      setImapEmail('');
      setImapLabel('');
      await loadAll();
    } catch (err) {
      setNotice({ type: 'error', text: String(err.message || err) });
    } finally {
      setBusy('');
    }
  }

  /* --------------------------------------------------- Calendar feed */
  async function addFeed() {
    if (!icsUrl.trim()) { setNotice({ type: 'error', text: 'Paste the calendar iCal address.' }); return; }
    setBusy('ics');
    setNotice({ type: 'info', text: 'Checking that address is a real calendar…' });
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/calendar/feed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: icsUrl.trim(), label: icsLabel })
      });
      const data = await res.json();
      if (!res.ok) {
        setNotice({ type: 'error', text: data.detail || 'Could not read that calendar.' });
        return;
      }
      setNotice({
        type: 'success',
        text: `Calendar connected - ${data.source?.stats?.parsed_events ?? 0} events found.`
      });
      setIcsUrl('');
      setIcsLabel('');
      await loadAll();
    } catch (err) {
      setNotice({ type: 'error', text: String(err.message || err) });
    } finally {
      setBusy('');
    }
  }

  /* ------------------------------------------------------ Google OAuth */
  async function connectGoogle(email) {
    setBusy(email);
    setNotice(null);
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/google/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, services: ['gmail', 'calendar'] })
      });
      const data = await res.json();
      if (!res.ok) {
        setNotice({ type: 'error', text: data.detail || 'Could not start Google sign-in.' });
        return;
      }
      const opened = await openInBrowser(data.auth_url);
      if (!opened.ok) {
        setNotice({ type: 'error', text: `Could not open your browser: ${data.auth_url}` });
        return;
      }
      setNotice({ type: 'info', text: `Approve access for ${email} in the browser tab, then come back.` });
      pollFor(email);
    } finally {
      setBusy('');
    }
  }

  async function disconnect(account) {
    if (!window.confirm(`Disconnect ${account.email}?`)) return;
    setBusy(account.id);
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/mail/accounts/${account.id}`, { method: 'DELETE' });
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

  async function syncNow() {
    setSyncing(true);
    setSyncResult(null);
    setNotice({ type: 'info', text: 'Reading new mail and building memories…' });
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/mail/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ account_id: '' })
      });
      const data = await res.json();
      if (!res.ok) {
        setNotice({ type: 'error', text: data.detail || 'Sync failed.' });
        return;
      }
      setSyncResult(data);
      setNotice({
        type: 'success',
        text: `${data.ingested ?? 0} email(s) turned into memories` +
              (data.skipped_bulk ? `, ${data.skipped_bulk} bulk skipped` : '') +
              (data.actions ? `, ${data.actions} action item(s) detected` : '') + '.'
      });
      await loadAll();
    } catch (err) {
      setNotice({ type: 'error', text: String(err.message || err) });
    } finally {
      setSyncing(false);
    }
  }

  async function removeFeed(source) {
    if (!window.confirm(`Remove "${source.name}"?`)) return;
    setBusy(source.id);
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/calendar/feed/${source.id}`, { method: 'DELETE' });
      if (res.ok) {
        setNotice({ type: 'success', text: 'Calendar removed.' });
        await loadAll();
      }
    } finally {
      setBusy('');
    }
  }

  const noticeStyle = {
    success: 'border-emerald-400/30 bg-emerald-500/10 text-emerald-200',
    error: 'border-red-400/30 bg-red-500/10 text-red-200',
    info: 'border-cyan-400/30 bg-cyan-500/10 text-cyan-100'
  };

  const icalSources = calendarSources.filter((s) => s.provider === 'ical');
  const oauthCalendarSources = calendarSources.filter((s) => s.provider === 'google');

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
              Real connections only. Nothing here is simulated or seeded.
            </p>
          </div>
          <button
            type="button"
            onClick={loadAll}
            className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 hover:bg-white/10 shrink-0"
          >
            <RefreshCw size={12} /> Refresh
          </button>
        </div>

        {notice && (
          <div className={`rounded-xl border px-4 py-3 text-xs leading-relaxed flex items-start gap-2 ${noticeStyle[notice.type]}`}>
            {notice.type === 'error' ? <AlertTriangle size={14} className="mt-0.5 shrink-0" />
              : notice.type === 'success' ? <CheckCircle2 size={14} className="mt-0.5 shrink-0" />
                : <Loader2 size={14} className="mt-0.5 shrink-0 animate-spin" />}
            <span className="break-all">{notice.text}</span>
          </div>
        )}

        {/* ==================== MAIL ==================== */}
        <section className="space-y-3">
          <div className="flex items-center gap-2">
            <Mail size={14} className="text-cyan-400" />
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">Mail</h3>
            <span className={`ml-auto rounded px-2 py-0.5 text-[10px] font-mono font-bold ${
              mailAccounts.length ? 'bg-emerald-400/10 text-emerald-300' : 'bg-slate-500/10 text-slate-400'
            }`}>
              {mailAccounts.length ? `${mailAccounts.length} CONNECTED` : 'NONE CONNECTED'}
            </span>
          </div>

          {mailAccounts.map((account) => (
            <div key={account.id} className="rounded-2xl border border-emerald-400/20 bg-[#0f1422] p-4 flex items-center gap-3">
              <div className="h-9 w-9 shrink-0 rounded-full bg-emerald-400/10 border border-emerald-400/20 flex items-center justify-center">
                <Mail size={14} className="text-emerald-300" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-semibold text-white truncate">{account.email}</p>
                  <CheckCircle2 size={12} className="text-emerald-400 shrink-0" />
                  <span className="rounded bg-white/5 border border-white/10 px-1.5 py-0.5 text-[9px] font-mono text-slate-400">
                    {account.provider_label}
                  </span>
                </div>
                {account.stats?.checked_at && (
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    {account.stats.total_messages ?? 0} messages · {account.stats.unread ?? 0} unread
                  </p>
                )}
                {account.status === 'error' && (
                  <p className="text-[11px] text-red-300 mt-0.5 break-all">{account.error || 'Credentials rejected.'}</p>
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

          {/* IMAP connect - the recommended path */}
          <div className="rounded-2xl border border-cyan-400/20 bg-[#0f1422] p-4 space-y-3">
            <div className="flex items-start gap-2">
              <Zap size={14} className="mt-0.5 text-cyan-300 shrink-0" />
              <div>
                <p className="text-xs font-bold text-white">Connect with a Gmail App Password</p>
                <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                  Recommended. No Google Cloud project, no OAuth consent screen, no verification,
                  no 7-day expiry, no fee. Works for personal Gmail accounts.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {ACCOUNTS.map(({ email, kind }) => {
                const done = mailEmails.includes(email);
                return (
                  <button
                    key={email}
                    type="button"
                    disabled={done || !!busy}
                    onClick={() => { setImapEmail(email); setImapLabel(kind === 'workspace' ? 'College' : 'Personal'); }}
                    className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-left text-[11px] font-semibold transition ${
                      done
                        ? 'border-emerald-400/20 bg-emerald-500/10 text-emerald-300'
                        : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 disabled:opacity-40'
                    }`}
                  >
                    {done ? <CheckCircle2 size={12} /> : <KeyRound size={12} />}
                    <span className="truncate">{email}</span>
                    {kind === 'workspace' && !done && (
                      <span className="ml-auto shrink-0 rounded bg-amber-400/10 px-1.5 py-0.5 text-[9px] text-amber-300">
                        may need OAuth
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            <div className="space-y-2 pt-1 border-t border-white/5">
              <input
                value={imapEmail}
                onChange={(e) => setImapEmail(e.target.value)}
                placeholder="Gmail address"
                className="w-full rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-xs outline-none focus:border-cyan-400/40"
              />
              <input
                type="password"
                value={imapPassword}
                onChange={(e) => setImapPassword(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') connectImap(); }}
                placeholder="16-character App Password (spaces are fine)"
                className="w-full rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-xs outline-none focus:border-cyan-400/40"
              />
              <div className="flex gap-2">
                <input
                  value={imapLabel}
                  onChange={(e) => setImapLabel(e.target.value)}
                  placeholder="Label (optional)"
                  className="min-w-0 flex-1 rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-xs outline-none"
                />
                <button
                  type="button"
                  onClick={() => connectImap()}
                  disabled={!imapEmail.trim() || !imapPassword.trim() || !!busy}
                  className="flex items-center gap-1.5 rounded-lg bg-cyan-400 px-4 py-2 text-xs font-bold text-slate-950 disabled:opacity-40"
                >
                  {busy ? <Loader2 size={12} className="animate-spin" /> : <KeyRound size={12} />}
                  Connect
                </button>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setShowImapHelp((v) => !v)}
              className="flex items-center gap-1 text-[11px] text-cyan-400 hover:underline"
            >
              <ChevronDown size={11} className={showImapHelp ? 'rotate-180 transition' : 'transition'} />
              How do I get an App Password?
            </button>
            {showImapHelp && (
              <ol className="ml-4 list-decimal space-y-1 text-[11px] text-slate-400 leading-relaxed">
                <li>Go to <span className="font-mono text-cyan-300">myaccount.google.com/security</span></li>
                <li>Turn on <b className="text-slate-300">2-Step Verification</b> if it is off (required)</li>
                <li>Open <span className="font-mono text-cyan-300">myaccount.google.com/apppasswords</span></li>
                <li>Name it <span className="font-mono">Jarvis</span> and click Create</li>
                <li>Copy the 16 characters Google shows and paste them above</li>
              </ol>
            )}
          </div>

          {/* Google OAuth - secondary */}
          <div className="rounded-2xl border border-white/10 bg-[#0f1422] p-4 space-y-2">
            <div className="flex items-start gap-2">
              <Info size={14} className="mt-0.5 text-slate-400 shrink-0" />
              <div className="min-w-0">
                <p className="text-xs font-bold text-white">Or connect with Google OAuth</p>
                <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                  Needed for Workspace (college) accounts, which stopped accepting App Passwords in
                  May 2025. Requires a free Google Cloud project - see{' '}
                  <span className="font-mono text-cyan-300">GOOGLE_SETUP.md</span>.
                  {!google.configured && ' Not configured yet.'}
                </p>
              </div>
            </div>
            {google.configured ? (
              <div className="flex flex-wrap gap-2 pt-1">
                {ACCOUNTS.map(({ email }) => {
                  const done = (google.accounts || []).some(
                    (a) => (a.email || '').toLowerCase() === email.toLowerCase());
                  return (
                    <button
                      key={email}
                      type="button"
                      disabled={done || !!busy}
                      onClick={() => connectGoogle(email)}
                      className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-[11px] font-semibold transition ${
                        done
                          ? 'border-emerald-400/20 bg-emerald-500/10 text-emerald-300'
                          : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 disabled:opacity-40'
                      }`}
                    >
                      {done ? <CheckCircle2 size={11} /> : <ExternalLink size={11} />}
                      {email}
                    </button>
                  );
                })}
              </div>
            ) : (
              <div className="rounded-lg border border-white/10 bg-black/30 p-2.5">
                <pre className="text-[10px] font-mono text-cyan-300 whitespace-pre-wrap break-all">{`GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...`}</pre>
              </div>
            )}
          </div>
        </section>

        {/* ==================== MAIL -> BRAIN ==================== */}
        {mailAccounts.length > 0 && (
          <section className="space-y-3">
            <div className="flex items-center gap-2">
              <Brain size={14} className="text-purple-400" />
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">
                Mail → Brain
              </h3>
              <span className={`ml-auto rounded px-2 py-0.5 text-[10px] font-mono font-bold ${
                syncStatus?.enabled ? 'bg-emerald-400/10 text-emerald-300' : 'bg-slate-500/10 text-slate-400'
              }`}>
                {syncStatus?.enabled ? `AUTO EVERY ${syncStatus.interval_minutes}m` : 'MANUAL ONLY'}
              </span>
            </div>

            <div className="rounded-2xl border border-purple-400/20 bg-[#0f1422] p-4 space-y-3">
              <p className="text-[11px] text-slate-400 leading-relaxed">
                New mail is read (never marked as read), turned into a memory you can ask
                questions about, written into the vault + wiki + knowledge graph, and
                scanned for deadlines that become tasks and alerts.
              </p>

              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={syncNow}
                  disabled={syncing}
                  className="flex items-center gap-1.5 rounded-lg bg-purple-400 px-4 py-2 text-xs font-bold text-slate-950 disabled:opacity-40"
                >
                  {syncing ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
                  {syncing ? 'Syncing…' : 'Sync mail now'}
                </button>
                {syncStatus && (
                  <span className="text-[11px] text-slate-500">
                    {syncStatus.folders?.join(', ')} · max {syncStatus.limit_per_run} per run
                    {syncStatus.skip_bulk ? ' · bulk skipped' : ''}
                  </span>
                )}
              </div>

              {/* per-account ingestion totals */}
              {syncStatus?.stats && Object.keys(syncStatus.stats).length > 0 && (
                <div className="space-y-1.5 pt-2 border-t border-white/5">
                  {Object.entries(syncStatus.stats).map(([accountId, stat]) => (
                    <div key={accountId} className="flex items-center justify-between text-[11px]">
                      <span className="text-slate-400 truncate">{stat.email || accountId}</span>
                      <span className="text-slate-500 font-mono shrink-0">
                        {stat.total_ingested || 0} stored · {stat.actions || 0} actions
                        {stat.last_sync ? ` · ${new Date(stat.last_sync).toLocaleTimeString()}` : ''}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {syncResult?.results?.some((r) => r.messages?.length > 0) && (
                <div className="space-y-1 pt-2 border-t border-white/5">
                  <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
                    Just ingested
                  </p>
                  {syncResult.results.flatMap((r) => r.messages || []).slice(0, 6).map((m, i) => (
                    <div key={i} className="flex items-start gap-2 text-[11px]">
                      <span className={`mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full ${
                        m.importance === 'high' ? 'bg-red-400'
                          : m.importance === 'normal' ? 'bg-amber-400' : 'bg-slate-500'
                      }`} />
                      <span className="text-slate-300 truncate">{m.subject}</span>
                      {m.actions > 0 && (
                        <span className="ml-auto shrink-0 rounded bg-amber-400/10 px-1.5 py-0.5 text-[9px] font-mono text-amber-300">
                          {m.actions} ACTION
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}

              <div className="flex items-start gap-1.5 pt-2 border-t border-white/5 text-[10px] text-slate-500">
                <ShieldCheck size={10} className="mt-0.5 shrink-0" />
                <span>
                  Memories are searchable in AI Agent and appear in Knowledge, the graph and
                  the wiki. Tune the interval in <span className="font-mono">backend/.env</span>{' '}
                  (<span className="font-mono">MAIL_SYNC_INTERVAL_MINUTES</span>).
                </span>
              </div>
            </div>
          </section>
        )}

        {/* ==================== CALENDAR ==================== */}
        <section className="space-y-3">
          <div className="flex items-center gap-2">
            <Calendar size={14} className="text-amber-400" />
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">Calendar</h3>
            <span className={`ml-auto rounded px-2 py-0.5 text-[10px] font-mono font-bold ${
              calendarSources.length ? 'bg-emerald-400/10 text-emerald-300' : 'bg-slate-500/10 text-slate-400'
            }`}>
              {calendarSources.length ? `${calendarSources.length} CONNECTED` : 'NONE CONNECTED'}
            </span>
          </div>

          {icalSources.map((source) => (
            <div key={source.id} className="rounded-2xl border border-emerald-400/20 bg-[#0f1422] p-4 flex items-center gap-3">
              <div className="h-9 w-9 shrink-0 rounded-full bg-amber-400/10 border border-amber-400/20 flex items-center justify-center">
                <Calendar size={14} className="text-amber-300" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-semibold text-white truncate">{source.name}</p>
                  <CheckCircle2 size={12} className="text-emerald-400 shrink-0" />
                  <span className="rounded bg-white/5 border border-white/10 px-1.5 py-0.5 text-[9px] font-mono text-slate-400">
                    iCal
                  </span>
                </div>
                {source.stats && (
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    {source.stats.parsed_events ?? 0} events in this calendar
                  </p>
                )}
              </div>
              <button
                type="button"
                onClick={() => removeFeed(source)}
                disabled={busy === source.id}
                className="rounded-lg border border-red-400/20 bg-red-500/10 p-2 text-red-300 hover:bg-red-500/20 transition disabled:opacity-40 shrink-0"
                title="Remove"
              >
                {busy === source.id ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
              </button>
            </div>
          ))}

          {oauthCalendarSources.map((source) => (
            <div key={source.id} className="rounded-2xl border border-emerald-400/20 bg-[#0f1422] p-4 flex items-center gap-3">
              <Calendar size={14} className="text-amber-300 shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-white truncate">{source.email}</p>
                <p className="text-[11px] text-slate-500">Live via Google OAuth</p>
              </div>
              <button
                type="button"
                onClick={() => disconnect(source)}
                disabled={busy === source.id}
                className="rounded-lg border border-red-400/20 bg-red-500/10 p-2 text-red-300 hover:bg-red-500/20 transition disabled:opacity-40 shrink-0"
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))}

          <div className="rounded-2xl border border-amber-400/20 bg-[#0f1422] p-4 space-y-3">
            <div className="flex items-start gap-2">
              <Zap size={14} className="mt-0.5 text-amber-300 shrink-0" />
              <div>
                <p className="text-xs font-bold text-white">Add a calendar by private iCal address</p>
                <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                  Recommended. Read-only, no OAuth, no expiry, and it works even for calendars
                  Google would not let a third-party app touch.
                </p>
              </div>
            </div>

            <input
              value={icsUrl}
              onChange={(e) => setIcsUrl(e.target.value)}
              placeholder="https://calendar.google.com/calendar/ical/…/private-…/basic.ics"
              className="w-full rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-[11px] font-mono outline-none focus:border-amber-400/40"
            />
            <div className="flex gap-2">
              <input
                value={icsLabel}
                onChange={(e) => setIcsLabel(e.target.value)}
                placeholder="Label, e.g. College"
                className="min-w-0 flex-1 rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-xs outline-none"
              />
              <button
                type="button"
                onClick={addFeed}
                disabled={!icsUrl.trim() || !!busy}
                className="flex items-center gap-1.5 rounded-lg bg-amber-400 px-4 py-2 text-xs font-bold text-slate-950 disabled:opacity-40"
              >
                {busy === 'ics' ? <Loader2 size={12} className="animate-spin" /> : <Calendar size={12} />}
                Add
              </button>
            </div>

            <button
              type="button"
              onClick={() => setShowIcsHelp((v) => !v)}
              className="flex items-center gap-1 text-[11px] text-amber-400 hover:underline"
            >
              <ChevronDown size={11} className={showIcsHelp ? 'rotate-180 transition' : 'transition'} />
              Where do I find this address?
            </button>
            {showIcsHelp && (
              <ol className="ml-4 list-decimal space-y-1 text-[11px] text-slate-400 leading-relaxed">
                <li>Open <span className="font-mono text-amber-300">calendar.google.com</span></li>
                <li>Click the gear icon → <b className="text-slate-300">Settings</b></li>
                <li>In the left list, click the calendar you want under <b className="text-slate-300">Settings for my calendars</b></li>
                <li>Scroll to <b className="text-slate-300">Integrate calendar</b></li>
                <li>Copy <b className="text-slate-300">Secret address in iCal format</b> and paste it above</li>
                <li>Repeat for each account (switch Google account first)</li>
              </ol>
            )}
          </div>
        </section>

        {/* ==================== LOCAL ==================== */}
        <section className="space-y-3">
          <div className="flex items-center gap-2">
            <Info size={14} className="text-slate-400" />
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">Local Services</h3>
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
        </section>

        <p className="text-[11px] text-slate-500 leading-relaxed border-t border-white/5 pt-4">
          <ShieldCheck size={11} className="inline mb-0.5" /> Everything here is read-only: Jarvis can
          read mail and calendars but never send, delete, or modify. Credentials are encrypted on disk
          under <span className="font-mono">backend/data/</span>, which is git-ignored and never part of
          the vault sync to GitHub.
        </p>
      </div>
    </div>
  );
}
