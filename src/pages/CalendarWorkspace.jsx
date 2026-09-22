import { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle, Calendar as CalendarIcon, Clock, ExternalLink, Loader2,
  MapPin, RefreshCw, ShieldCheck, Users
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useBackend } from '../context/BackendContext.jsx';
import { apiFetch, openInBrowser } from '../services/apiClient.js';

/**
 * CalendarWorkspace - real Google Calendar.
 * ---------------------------------------------------------------------------
 * Reads events straight from Google. When nothing is connected it says so
 * rather than rendering placeholder meetings.
 */
const RANGES = [
  { id: 'today', label: 'Today', daysBack: 0, daysAhead: 1 },
  { id: 'week', label: 'Next 7 days', daysBack: 1, daysAhead: 7 },
  { id: 'month', label: 'Next 30 days', daysBack: 1, daysAhead: 30 }
];

function dayKey(value) {
  if (!value) return 'unknown';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'unknown' : date.toDateString();
}

function formatDay(key) {
  if (key === 'unknown') return 'Date unknown';
  const date = new Date(key);
  const today = new Date().toDateString();
  const tomorrow = new Date(Date.now() + 86400000).toDateString();
  if (key === today) return 'Today';
  if (key === tomorrow) return 'Tomorrow';
  return date.toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' });
}

function formatTime(event) {
  if (event.all_day) return 'All day';
  const start = new Date(event.start);
  const end = event.end ? new Date(event.end) : null;
  if (Number.isNaN(start.getTime())) return '';
  const opts = { hour: '2-digit', minute: '2-digit' };
  return end && !Number.isNaN(end.getTime())
    ? `${start.toLocaleTimeString(undefined, opts)} - ${end.toLocaleTimeString(undefined, opts)}`
    : start.toLocaleTimeString(undefined, opts);
}

export default function CalendarWorkspace() {
  const { apiClient } = useBackend();
  const navigate = useNavigate();

  const [status, setStatus] = useState({ configured: false, accounts: [] });
  const [accountId, setAccountId] = useState('');
  const [range, setRange] = useState('week');
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const accounts = status.accounts || [];
  const account = useMemo(
    () => accounts.find((a) => a.id === accountId) || accounts[0] || null,
    [accounts, accountId]
  );

  async function loadStatus() {
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/calendar/sources`);
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

  async function loadEvents() {
    if (!account?.id) return;
    setLoading(true);
    setError('');
    const config = RANGES.find((r) => r.id === range) || RANGES[1];
    try {
      const res = await apiFetch(
        `${apiClient.baseUrl}/api/calendar/source-events` +
        `?source_id=${encodeURIComponent(account.id)}` +
        `&days_ahead=${config.daysAhead}&days_back=${config.daysBack}`
      );
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || 'Could not read this calendar.');
        setEvents([]);
      } else {
        setEvents(data.events || []);
      }
    } catch (err) {
      setError(String(err.message || err));
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadStatus(); }, []);
  useEffect(() => { loadEvents(); }, [account?.id, range]);

  function goConnect() {
    navigate('/integrations');
  }

  // Group events by day for a readable agenda.
  const grouped = useMemo(() => {
    const map = new Map();
    for (const event of events) {
      const key = dayKey(event.start);
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(event);
    }
    return [...map.entries()].sort((a, b) => {
      if (a[0] === 'unknown') return 1;
      if (b[0] === 'unknown') return -1;
      return new Date(a[0]) - new Date(b[0]);
    });
  }, [events]);

  /* ------------------------------------------------- not connected state */
  if (!status.configured || accounts.length === 0) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-[#111318] p-6 text-slate-100 font-sans">
        <div className="w-full max-w-lg rounded-2xl border border-white/10 bg-[#0f1422] p-7 text-center space-y-4">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-amber-400/30 bg-amber-500/10">
            <CalendarIcon size={20} className="text-amber-300" />
          </div>
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-white">Calendar Not Connected</h2>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              No calendar source is connected, so there are no real events to display.
              Add one on the Integrations page - the quickest way is your calendar's
              private iCal address, which needs no Google Cloud project at all.
            </p>
          </div>

          <button
            type="button"
            onClick={goConnect}
            className="w-full rounded-xl border border-cyan-400/30 bg-cyan-500/10 px-4 py-2.5 text-xs font-semibold text-cyan-200 hover:bg-cyan-500/20 transition"
          >
            Add a calendar source →
          </button>
          <p className="text-[10px] text-slate-500">
            Private iCal address, or Google OAuth - both read-only.
          </p>
        </div>
      </div>
    );
  }

  /* ------------------------------------------------------------- agenda */
  return (
    <div className="flex h-full w-full flex-col bg-[#111318] p-6 text-slate-100 font-sans select-none overflow-y-auto thin-scrollbar">
      <div className="mx-auto w-full max-w-4xl space-y-5">
        <div className="flex flex-wrap items-end justify-between gap-3 border-b border-white/10 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <CalendarIcon size={18} className="text-amber-400" />
              <h2 className="text-base font-bold text-white uppercase tracking-wider font-mono">Schedule</h2>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Live from {account.email} · read-only
            </p>
          </div>
          <button
            type="button"
            onClick={loadEvents}
            className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 hover:bg-white/10"
          >
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>

        {/* Account + range switchers */}
        <div className="flex flex-wrap items-center gap-2">
          {accounts.map((a) => (
            <button
              key={a.id}
              type="button"
              onClick={() => setAccountId(a.id)}
              className={`flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-[11px] transition ${
                account?.id === a.id
                  ? 'border-amber-400/40 bg-amber-500/10 text-amber-200 font-semibold'
                  : 'border-white/10 bg-white/5 text-slate-400 hover:bg-white/10'
              }`}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              {a.email}
              <span className="rounded bg-white/5 px-1 py-0.5 text-[9px] font-mono text-slate-500">
                {a.provider === 'ical' ? 'ICS' : 'OAUTH'}
              </span>
            </button>
          ))}
          <div className="ml-auto flex gap-1">
            {RANGES.map((r) => (
              <button
                key={r.id}
                type="button"
                onClick={() => setRange(r.id)}
                className={`rounded-lg px-2.5 py-1 text-[11px] transition ${
                  range === r.id ? 'bg-white/10 text-white font-semibold' : 'text-slate-400 hover:bg-white/5'
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-red-400/20 bg-red-500/10 p-3 text-[11px] text-red-200 break-all">
            {error}
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center py-10 text-xs text-slate-500">
            <Loader2 size={14} className="animate-spin mr-2" /> Reading {account.email}…
          </div>
        )}

        {!loading && !error && events.length === 0 && (
          <div className="rounded-2xl border border-white/10 bg-[#0f1422] p-8 text-center">
            <CalendarIcon size={22} className="mx-auto text-slate-600" />
            <p className="mt-2 text-xs text-slate-400">
              No events in this range for {account.email}.
            </p>
          </div>
        )}

        {!loading && grouped.map(([key, dayEvents]) => (
          <div key={key} className="space-y-2">
            <h3 className="text-[11px] font-mono font-bold uppercase tracking-wider text-amber-300">
              {formatDay(key)}
            </h3>
            <div className="space-y-2">
              {dayEvents.map((event) => (
                <div
                  key={event.id}
                  className="rounded-xl border border-white/10 bg-[#0f1422] p-3.5 hover:border-amber-400/30 transition"
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-amber-400/20 bg-amber-500/10">
                      <Clock size={13} className="text-amber-300" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold text-white truncate">{event.summary}</p>
                        {event.html_link && (
                          <button
                            type="button"
                            onClick={() => openInBrowser(event.html_link)}
                            className="shrink-0 text-slate-500 hover:text-cyan-400"
                            title="Open in Google Calendar"
                          >
                            <ExternalLink size={11} />
                          </button>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400 mt-0.5">{formatTime(event)}</p>
                      {event.location && (
                        <p className="mt-1 flex items-center gap-1 text-[11px] text-slate-400">
                          <MapPin size={10} /> {event.location}
                        </p>
                      )}
                      {event.attendees?.length > 0 && (
                        <p className="mt-1 flex items-center gap-1 text-[11px] text-slate-500">
                          <Users size={10} /> {event.attendees.length} attendee{event.attendees.length > 1 ? 's' : ''}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}

        <p className="flex items-center gap-1.5 border-t border-white/5 pt-4 text-[11px] text-slate-500">
          <ShieldCheck size={11} /> Read-only access. Jarvis cannot create, edit, or delete events.
        </p>
      </div>
    </div>
  );
}
