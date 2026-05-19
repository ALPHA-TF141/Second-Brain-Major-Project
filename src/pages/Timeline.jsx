import { useEffect, useMemo, useState } from 'react';
import { CalendarDays, Download, Filter, Images, RefreshCw, Search, Tags } from 'lucide-react';
import PageHeader from '../components/PageHeader.jsx';
import { useBackend } from '../context/BackendContext.jsx';

function Timeline() {
  const { apiClient, loginDemo } = useBackend();
  const [timeline, setTimeline] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [selectedMemory, setSelectedMemory] = useState(null);
  const [selectedSession, setSelectedSession] = useState(null);
  const [filters, setFilters] = useState({ q: '', source_type: '', topic: '', app: '', group: 'day' });
  const [isBusy, setIsBusy] = useState(false);

  const flatMemories = useMemo(() => timeline.flatMap((group) => group.memories), [timeline]);
  const selectedSessionMemories = selectedSession ? flatMemories.filter((memory) => memory.session_id === selectedSession.session_id) : [];

  async function ensureLogin() {
    if (!apiClient.getToken()) {
      await loginDemo();
    }
  }

  async function refresh() {
    if (!apiClient.getToken()) return;
    const [nextTimeline, nextSessions] = await Promise.all([
      apiClient.fetchMemoryTimeline(filters),
      apiClient.fetchMemorySessions()
    ]);
    setTimeline(nextTimeline);
    setSessions(nextSessions);
    setSelectedMemory((current) => current || nextTimeline[0]?.memories?.[0] || null);
    setSelectedSession((current) => current || nextSessions[0] || null);
  }

  async function rebuildArchive() {
    setIsBusy(true);
    try {
      await ensureLogin();
      await apiClient.rebuildMemoryArchive();
      await refresh();
    } finally {
      setIsBusy(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(refresh, 250);
    return () => window.clearTimeout(timer);
  }, [filters]);

  return (
    <div>
      <PageHeader
        eyebrow="Memory Timeline"
        title="Digital memory archive"
        description="Searchable chronological memories reconstructed from screenshots, OCR chunks, activity metadata, topics, clipboard, apps, and sessions."
        action={
          <button
            type="button"
            onClick={rebuildArchive}
            disabled={isBusy}
            className="flex items-center gap-2 rounded-lg bg-cyanGlow px-4 py-3 text-sm font-bold text-slate-950 transition hover:bg-cyan-300 disabled:opacity-40"
          >
            <RefreshCw size={17} />
            Rebuild Archive
          </button>
        }
      />

      <section className="glass-panel mb-5 rounded-lg p-4">
        <div className="grid gap-3 xl:grid-cols-[1fr_160px_160px_160px_130px]">
          <label className="flex items-center gap-3 rounded-lg border border-white/10 bg-slate-950/50 px-4 py-3">
            <Search size={18} className="text-slate-500" />
            <input
              value={filters.q}
              onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value }))}
              placeholder="Search memories, tags, topics..."
              className="min-w-0 flex-1 bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-600"
            />
          </label>
          <input
            value={filters.topic}
            onChange={(event) => setFilters((current) => ({ ...current, topic: event.target.value }))}
            placeholder="Topic"
            className="rounded-lg border border-white/10 bg-slate-950/50 px-4 py-3 text-sm outline-none"
          />
          <input
            value={filters.app}
            onChange={(event) => setFilters((current) => ({ ...current, app: event.target.value }))}
            placeholder="App"
            className="rounded-lg border border-white/10 bg-slate-950/50 px-4 py-3 text-sm outline-none"
          />
          <select
            value={filters.source_type}
            onChange={(event) => setFilters((current) => ({ ...current, source_type: event.target.value }))}
            className="rounded-lg border border-white/10 bg-slate-950/70 px-4 py-3 text-sm outline-none"
          >
            <option value="">All sources</option>
            <option value="screen">Screen</option>
            <option value="code">Code</option>
            <option value="article">Article</option>
            <option value="document">Document</option>
            <option value="youtube">YouTube</option>
            <option value="clipboard">Clipboard</option>
          </select>
          <select
            value={filters.group}
            onChange={(event) => setFilters((current) => ({ ...current, group: event.target.value }))}
            className="rounded-lg border border-white/10 bg-slate-950/70 px-4 py-3 text-sm outline-none"
          >
            <option value="day">Daily</option>
            <option value="week">Weekly</option>
          </select>
        </div>
      </section>

      <div className="grid gap-5 xl:grid-cols-[0.75fr_1.1fr_0.85fr]">
        <section className="glass-panel rounded-lg p-5">
          <div className="mb-4 flex items-center gap-2">
            <CalendarDays size={18} className="text-cyanGlow" />
            <h3 className="font-semibold">Grouped Sessions</h3>
          </div>
          <div className="thin-scrollbar max-h-[680px] space-y-3 overflow-y-auto">
            {sessions.map((session) => (
              <button
                key={session.id}
                type="button"
                onClick={() => setSelectedSession(session)}
                className={[
                  'w-full rounded-lg border p-4 text-left transition hover:bg-white/8',
                  selectedSession?.id === session.id ? 'border-cyanGlow/40 bg-cyanGlow/10' : 'border-white/10 bg-white/5'
                ].join(' ')}
              >
                <p className="font-semibold text-slate-100">{session.title}</p>
                <p className="mt-2 line-clamp-3 text-sm leading-6 text-slate-400">{session.summary}</p>
                <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
                  <span>{session.memory_count} memories</span>
                  <span>{session.session_type}</span>
                </div>
              </button>
            ))}
            {!sessions.length && <p className="rounded-lg border border-white/10 bg-white/5 p-4 text-sm text-slate-500">No reconstructed sessions yet. Process OCR, then rebuild the archive.</p>}
          </div>
        </section>

        <section className="glass-panel rounded-lg p-5">
          <div className="mb-4 flex items-center gap-2">
            <Filter size={18} className="text-mintGlow" />
            <h3 className="font-semibold">Memory Feed</h3>
          </div>
          <div className="thin-scrollbar max-h-[680px] space-y-5 overflow-y-auto">
            {timeline.map((group) => (
              <div key={group.label}>
                <div className="sticky top-0 z-10 mb-3 bg-slate-950/90 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyanGlow backdrop-blur">
                  {group.label}
                </div>
                <div className="space-y-3">
                  {group.memories.map((memory) => (
                    <button
                      type="button"
                      key={memory.id}
                      onClick={() => setSelectedMemory(memory)}
                      className={[
                        'w-full rounded-lg border p-4 text-left transition hover:bg-white/8',
                        selectedMemory?.id === memory.id ? 'border-mintGlow/40 bg-mintGlow/10' : 'border-white/10 bg-white/5'
                      ].join(' ')}
                    >
                      <div className="mb-2 flex items-center justify-between gap-3">
                        <p className="truncate font-semibold text-slate-100">{memory.title}</p>
                        <span className="rounded-md border border-white/10 px-2 py-1 text-xs text-slate-400">{memory.source_type}</span>
                      </div>
                      <p className="line-clamp-3 text-sm leading-6 text-slate-400">{memory.content}</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {memory.tags.slice(0, 5).map((tag) => (
                          <span key={tag} className="rounded-md bg-white/7 px-2 py-1 text-xs text-slate-400">{tag}</span>
                        ))}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ))}
            {!timeline.length && <p className="rounded-lg border border-white/10 bg-white/5 p-5 text-sm text-slate-500">No memories match the current filters.</p>}
          </div>
        </section>

        <section className="glass-panel rounded-lg p-5">
          <h3 className="font-semibold">Memory Detail</h3>
          {selectedMemory ? (
            <div className="mt-4 space-y-4">
              {selectedMemory.screenshot_id && (
                <div className="overflow-hidden rounded-lg border border-white/10 bg-slate-950/50">
                  <img
                    src={`${apiClient.baseUrl}/api/capture/screenshots/${selectedMemory.screenshot_id}/image?token=${encodeURIComponent(apiClient.getToken())}`}
                    alt="Memory screenshot"
                    className="max-h-64 w-full object-contain"
                    loading="lazy"
                  />
                </div>
              )}
              <div>
                <p className="text-xs uppercase text-cyanGlow">{selectedMemory.category}</p>
                <h4 className="mt-2 text-xl font-semibold">{selectedMemory.title}</h4>
                <p className="mt-2 text-sm text-slate-500">{new Date(selectedMemory.created_at).toLocaleString()} · {selectedMemory.app_source}</p>
              </div>
              <p className="whitespace-pre-wrap rounded-lg border border-white/10 bg-white/5 p-4 text-sm leading-6 text-slate-300">{selectedMemory.content}</p>
              <div>
                <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
                  <Tags size={16} className="text-mintGlow" />
                  Tags
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedMemory.tags.map((tag) => (
                    <span key={tag} className="rounded-lg border border-mintGlow/20 bg-mintGlow/10 px-3 py-1 text-xs text-mintGlow">{tag}</span>
                  ))}
                </div>
              </div>
              {selectedSession && (
                <a
                  href={apiClient.exportSessionUrl(selectedSession.session_id)}
                  className="flex items-center justify-center gap-2 rounded-lg border border-cyanGlow/30 bg-cyanGlow/10 px-4 py-3 text-sm font-semibold text-cyanGlow transition hover:bg-cyanGlow/20"
                >
                  <Download size={16} />
                  Export Session
                </a>
              )}
            </div>
          ) : (
            <p className="mt-4 rounded-lg border border-white/10 bg-white/5 p-5 text-sm text-slate-500">Select a memory to inspect details.</p>
          )}

          <div className="mt-5 rounded-lg border border-white/10 bg-white/5 p-4">
            <div className="mb-3 flex items-center gap-2">
              <Images size={17} className="text-warningGlow" />
              <h4 className="font-semibold">Session Preview</h4>
            </div>
            <div className="space-y-2">
              {selectedSessionMemories.slice(0, 4).map((memory) => (
                <p key={memory.id} className="line-clamp-1 text-sm text-slate-400">{memory.title}</p>
              ))}
              {!selectedSessionMemories.length && <p className="text-sm text-slate-500">Choose a reconstructed session.</p>}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

export default Timeline;
