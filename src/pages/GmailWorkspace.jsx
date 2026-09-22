import { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle, ArrowLeft, CheckCircle2, Inbox, Loader2, Mail,
  PlusCircle, RefreshCw, Search, Send, ShieldCheck, Sparkles, Star
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useBackend } from '../context/BackendContext.jsx';
import { apiFetch } from '../services/apiClient.js';

/**
 * GmailWorkspace - real Gmail.
 * ---------------------------------------------------------------------------
 * There is no sample inbox here. If no Google account is linked, the page says
 * so and offers the connect flow. Every message shown comes from Gmail.
 */
const FOLDERS = [
  { id: 'inbox', label: 'Inbox', query: 'in:inbox', icon: Inbox },
  { id: 'unread', label: 'Unread', query: 'is:unread in:inbox', icon: Mail },
  { id: 'important', label: 'Important', query: 'is:important in:inbox', icon: AlertTriangle },
  { id: 'starred', label: 'Starred', query: 'is:starred', icon: Star },
  { id: 'sent', label: 'Sent', query: 'in:sent', icon: Send }
];

function formatDate(value) {
  if (!value) return '';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  const now = new Date();
  const sameDay = parsed.toDateString() === now.toDateString();
  return sameDay
    ? parsed.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
    : parsed.toLocaleDateString(undefined, { day: 'numeric', month: 'short' });
}

function senderName(from) {
  if (!from) return 'Unknown sender';
  const match = from.match(/^"?([^"<]+)"?\s*</);
  return (match ? match[1] : from).trim();
}

export default function GmailWorkspace() {
  const { apiClient } = useBackend();
  const navigate = useNavigate();

  const [status, setStatus] = useState({ configured: false, accounts: [] });
  const [accountId, setAccountId] = useState('');
  const [folder, setFolder] = useState('inbox');
  const [search, setSearch] = useState('');
  const [messages, setMessages] = useState([]);
  const [selected, setSelected] = useState(null);
  const [bodyLoading, setBodyLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [draft, setDraft] = useState('');
  const [aiBusy, setAiBusy] = useState(false);
  const [taskNotice, setTaskNotice] = useState('');

  const accounts = status.accounts || [];
  const account = useMemo(
    () => accounts.find((a) => a.id === accountId) || accounts[0] || null,
    [accounts, accountId]
  );

  async function loadStatus() {
    try {
      // Unified: returns Google OAuth accounts AND IMAP accounts together.
      const res = await apiFetch(`${apiClient.baseUrl}/api/mail/accounts`);
      if (res.ok) {
        const data = await res.json();
        const list = Array.isArray(data) ? data : [];
        setStatus({ configured: true, accounts: list });
        if (!accountId && list.length) setAccountId(list[0].id);
      }
    } catch {
      setError('Backend unreachable.');
    }
  }

  async function loadMessages() {
    if (!account?.id) return;
    setLoading(true);
    setError('');
    setSelected(null);
    try {
      const query = search.trim();
      const params = new URLSearchParams({
        account_id: account.id,
        folder,
        limit: '30'
      });
      if (query) params.set('q', query);
      const res = await apiFetch(`${apiClient.baseUrl}/api/mail/messages?${params.toString()}`);
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || 'Could not read this mailbox.');
        setMessages([]);
      } else {
        setMessages(data.messages || []);
      }
    } catch (err) {
      setError(String(err.message || err));
      setMessages([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadStatus(); }, []);
  useEffect(() => { loadMessages(); }, [account?.id, folder]);

  async function openMessage(message) {
    setSelected({ ...message, body: '' });
    setDraft('');
    setTaskNotice('');
    setBodyLoading(true);
    try {
      const res = await apiFetch(
        `${apiClient.baseUrl}/api/mail/message/${encodeURIComponent(message.id)}` +
        `?account_id=${encodeURIComponent(account.id)}&folder=${encodeURIComponent(folder)}`
      );
      const data = await res.json();
      if (res.ok) setSelected(data);
      else setError(data.detail || 'Could not open that message.');
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setBodyLoading(false);
    }
  }

  /** Turn an email into a real task in the OS task store. */
  async function convertToTask(message) {
    const due = new Date(Date.now() + 2 * 86400000).toISOString().slice(0, 10);
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/os/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: `Email: ${message.subject}`.slice(0, 120),
          project: 'Email Follow-ups',
          priority: message.important ? 'high' : 'medium',
          due_date: due,
          status: 'pending'
        })
      });
      setTaskNotice(res.ok
        ? 'Task created in your task list.'
        : 'Could not create that task.');
    } catch {
      setTaskNotice('Could not create that task.');
    }
  }

  /** Ask the local LLM for a reply draft (never auto-sends). */
  async function generateDraft(message) {
    setAiBusy(true);
    setDraft('');
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/chat/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query:
            `Write a short, professional reply to this email. Return only the reply body.\n\n` +
            `From: ${message.from}\nSubject: ${message.subject}\n\n${(message.body || message.snippet || '').slice(0, 1500)}`,
          limit: 3
        })
      });
      const data = await res.json();
      setDraft(data.answer || data.response || data.message || 'No draft returned.');
    } catch {
      setDraft('Could not reach the local language model.');
    } finally {
      setAiBusy(false);
    }
  }

  function goConnect() {
    // Connecting now offers two routes (IMAP app password, or Google OAuth),
    // so the Integrations page owns that choice.
    navigate('/integrations');
  }

  /* ------------------------------------------------------------------ *
   * Not configured / not connected - say so plainly, never fake mail.
   * ------------------------------------------------------------------ */
  if (!status.configured || accounts.length === 0) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-[#111318] p-6 text-slate-100 font-sans">
        <div className="w-full max-w-lg rounded-2xl border border-white/10 bg-[#0f1422] p-7 text-center space-y-4">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-amber-400/30 bg-amber-500/10">
            <Mail size={20} className="text-amber-300" />
          </div>
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-white">Gmail Not Connected</h2>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              No mail account is connected yet, so there is nothing real to show here.
              Connect one on the Integrations page - you can use a Gmail App Password
              (no Google Cloud project, no verification) or Google OAuth.
            </p>
          </div>

          <button
            type="button"
            onClick={goConnect}
            className="w-full rounded-xl border border-cyan-400/30 bg-cyan-500/10 px-4 py-2.5 text-xs font-semibold text-cyan-200 hover:bg-cyan-500/20 transition"
          >
            Connect a mail account →
          </button>
          <p className="text-[10px] text-slate-500">
            Gmail App Password or Google OAuth - both work, neither is simulated.
          </p>
        </div>
      </div>
    );
  }

  /* ---------------------------------------------------------------- inbox */
  return (
    <div className="flex h-full w-full flex-col bg-[#111318] text-slate-100 font-sans select-none">
      {/* Account switcher */}
      <div className="flex items-center gap-2 border-b border-white/10 px-4 py-2 overflow-x-auto">
        {accounts.map((a) => (
          <button
            key={a.id}
            type="button"
            onClick={() => { setAccountId(a.id); setSearch(''); setFolder('inbox'); }}
            className={`flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-[11px] whitespace-nowrap transition ${
              account?.id === a.id
                ? 'border-cyan-400/40 bg-cyan-500/10 text-cyan-200 font-semibold'
                : 'border-white/10 bg-white/5 text-slate-400 hover:bg-white/10'
            }`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            {a.email}
            <span className="rounded bg-white/5 px-1 py-0.5 text-[9px] font-mono text-slate-500">
              {a.provider === 'imap' ? 'IMAP' : 'OAUTH'}
            </span>
          </button>
        ))}
        <button
          type="button"
          onClick={loadMessages}
          className="ml-auto flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 text-[11px] text-slate-300 hover:bg-white/10 shrink-0"
        >
          <RefreshCw size={11} className={loading ? 'animate-spin' : ''} /> Sync
        </button>
      </div>

      <div className="flex flex-1 min-h-0">
        {/* Folders */}
        <div className="w-44 shrink-0 border-r border-white/10 p-2 space-y-0.5">
          {FOLDERS.map((f) => (
            <button
              key={f.id}
              type="button"
              onClick={() => { setFolder(f.id); setSearch(''); }}
              className={`flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs transition ${
                folder === f.id && !search
                  ? 'bg-cyan-500/10 text-cyan-200 font-semibold'
                  : 'text-slate-400 hover:bg-white/5'
              }`}
            >
              <f.icon size={13} /> {f.label}
            </button>
          ))}
          <div className="pt-3 mt-3 border-t border-white/5 px-2">
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-500">
              <ShieldCheck size={10} /> READ-ONLY
            </div>
            <p className="text-[10px] text-slate-600 mt-1 leading-snug">
              Jarvis can read your mail but never send or delete it.
            </p>
          </div>
        </div>

        {/* List */}
        <div className={`${selected ? 'hidden md:flex' : 'flex'} w-full md:w-80 shrink-0 flex-col border-r border-white/10`}>
          <div className="flex items-center gap-2 border-b border-white/10 px-3 py-2">
            <Search size={13} className="text-slate-500" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') loadMessages(); }}
              placeholder="Search Gmail (e.g. from:sharma)"
              className="w-full bg-transparent text-xs outline-none placeholder:text-slate-500"
            />
          </div>

          <div className="flex-1 overflow-y-auto thin-scrollbar">
            {loading && (
              <div className="flex items-center justify-center py-8 text-xs text-slate-500">
                <Loader2 size={14} className="animate-spin mr-2" /> Loading {account.email}…
              </div>
            )}

            {!loading && error && (
              <div className="m-3 rounded-lg border border-red-400/20 bg-red-500/10 p-3 text-[11px] text-red-200">
                {error}
              </div>
            )}

            {!loading && !error && messages.length === 0 && (
              <p className="p-4 text-center text-xs text-slate-500">No messages in this view.</p>
            )}

            {!loading && messages.map((message) => (
              <button
                key={message.id}
                type="button"
                onClick={() => openMessage(message)}
                className={`w-full border-b border-white/5 px-3 py-2.5 text-left transition hover:bg-white/5 ${
                  selected?.id === message.id ? 'bg-cyan-500/10' : ''
                }`}
              >
                <div className="flex items-center gap-2">
                  {message.unread && <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 shrink-0" />}
                  <span className={`truncate text-xs ${message.unread ? 'font-bold text-white' : 'text-slate-300'}`}>
                    {senderName(message.from)}
                  </span>
                  <span className="ml-auto shrink-0 text-[10px] text-slate-500">{formatDate(message.date)}</span>
                </div>
                <p className={`mt-0.5 truncate text-[11px] ${message.unread ? 'text-slate-200' : 'text-slate-400'}`}>
                  {message.subject}
                </p>
                <p className="truncate text-[10px] text-slate-500 mt-0.5">{message.snippet}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Reader */}
        <div className={`${selected ? 'flex' : 'hidden md:flex'} flex-1 flex-col min-w-0`}>
          {!selected ? (
            <div className="flex flex-1 items-center justify-center text-xs text-slate-500">
              Select a message to read it.
            </div>
          ) : (
            <>
              <div className="border-b border-white/10 px-5 py-3">
                <button
                  type="button"
                  onClick={() => setSelected(null)}
                  className="mb-2 flex items-center gap-1 text-[11px] text-cyan-400 md:hidden"
                >
                  <ArrowLeft size={11} /> Back
                </button>
                <h3 className="text-sm font-bold text-white leading-snug">{selected.subject}</h3>
                <p className="mt-1 text-[11px] text-slate-400 break-all">
                  <span className="text-slate-300">{selected.from}</span>
                  {selected.to ? ` → ${selected.to}` : ''}
                </p>
                <p className="text-[10px] text-slate-500">{selected.date}</p>
              </div>

              <div className="flex flex-wrap items-center gap-2 border-b border-white/5 px-5 py-2.5">
                <button
                  type="button"
                  onClick={() => convertToTask(selected)}
                  className="flex items-center gap-1.5 rounded-lg border border-cyan-400/30 bg-cyan-500/10 px-3 py-1.5 text-[11px] font-semibold text-cyan-200 hover:bg-cyan-500/20"
                >
                  <PlusCircle size={12} /> Create task
                </button>
                <button
                  type="button"
                  onClick={() => generateDraft(selected)}
                  disabled={aiBusy}
                  className="flex items-center gap-1.5 rounded-lg border border-amber-400/30 bg-amber-500/10 px-3 py-1.5 text-[11px] font-semibold text-amber-200 hover:bg-amber-500/20 disabled:opacity-40"
                >
                  {aiBusy ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
                  Draft reply (local AI)
                </button>
                {taskNotice && <span className="text-[11px] text-emerald-300">{taskNotice}</span>}
              </div>

              <div className="flex-1 overflow-y-auto thin-scrollbar px-5 py-4">
                {bodyLoading
                  ? <div className="flex items-center gap-2 text-xs text-slate-500"><Loader2 size={13} className="animate-spin" /> Loading message…</div>
                  : <pre className="whitespace-pre-wrap break-words font-sans text-[12.5px] leading-relaxed text-slate-200">{selected.body || selected.snippet}</pre>}

                {draft && (
                  <div className="mt-5 rounded-xl border border-amber-400/20 bg-amber-500/5 p-4">
                    <div className="mb-2 flex items-center gap-1.5 text-[10px] font-mono font-bold uppercase tracking-wider text-amber-300">
                      <Sparkles size={10} /> AI draft - review before sending
                    </div>
                    <pre className="whitespace-pre-wrap break-words font-sans text-[12.5px] leading-relaxed text-slate-200">{draft}</pre>
                    <p className="mt-2 text-[10px] text-slate-500">
                      Jarvis has read-only access, so it cannot send this for you.
                    </p>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
