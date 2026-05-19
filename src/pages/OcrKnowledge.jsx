import { useEffect, useMemo, useState } from 'react';
import { BrainCircuit, FileText, ListFilter, RefreshCw, Search, Sparkles } from 'lucide-react';
import PageHeader from '../components/PageHeader.jsx';
import { useBackend } from '../context/BackendContext.jsx';

function OcrKnowledge() {
  const { apiClient, loginDemo, liveEvents } = useBackend();
  const [status, setStatus] = useState({ is_running: false, queued: 0, last_error: '' });
  const [chunks, setChunks] = useState([]);
  const [topics, setTopics] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [query, setQuery] = useState('');
  const [sourceType, setSourceType] = useState('');
  const [selectedChunk, setSelectedChunk] = useState(null);
  const [isBusy, setIsBusy] = useState(false);

  const ocrEvents = useMemo(() => liveEvents.filter((event) => event.type === 'ocr_status'), [liveEvents]);

  async function ensureLogin() {
    if (!apiClient.getToken()) {
      await loginDemo();
    }
  }

  async function refresh() {
    if (!apiClient.getToken()) return;
    const [nextStatus, nextChunks, nextTopics, nextSessions] = await Promise.all([
      apiClient.ocrStatus(),
      apiClient.fetchSemanticChunks(query, sourceType),
      apiClient.fetchDetectedTopics(),
      apiClient.fetchProcessedSessions()
    ]);
    setStatus(nextStatus);
    setChunks(nextChunks);
    setTopics(nextTopics);
    setSessions(nextSessions);
    setSelectedChunk((current) => current || nextChunks[0] || null);
  }

  async function queueUnprocessed() {
    setIsBusy(true);
    try {
      await ensureLogin();
      await apiClient.queueUnprocessedOcr();
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
  }, [query, sourceType]);

  useEffect(() => {
    refresh();
  }, [ocrEvents.length]);

  return (
    <div>
      <PageHeader
        eyebrow="OCR Knowledge"
        title="Screen understanding pipeline"
        description="Extract readable text from screenshots, clean noisy OCR, detect topics, and organize knowledge chunks for future memory systems."
        action={
          <button
            type="button"
            onClick={queueUnprocessed}
            disabled={isBusy}
            className="flex items-center gap-2 rounded-lg bg-cyanGlow px-4 py-3 text-sm font-bold text-slate-950 transition hover:bg-cyan-300 disabled:opacity-40"
          >
            <RefreshCw size={17} />
            Process Screenshots
          </button>
        }
      />

      <div className="mb-5 grid gap-4 md:grid-cols-4">
        <section className="glass-panel rounded-lg p-4">
          <BrainCircuit size={21} className="mb-4 text-mintGlow" />
          <p className="text-sm text-slate-500">OCR Worker</p>
          <h3 className="mt-2 text-xl font-semibold">{status.is_running ? 'Running' : 'Stopped'}</h3>
        </section>
        <section className="glass-panel rounded-lg p-4">
          <ListFilter size={21} className="mb-4 text-cyanGlow" />
          <p className="text-sm text-slate-500">Queue</p>
          <h3 className="mt-2 text-xl font-semibold">{status.queued}</h3>
        </section>
        <section className="glass-panel rounded-lg p-4">
          <FileText size={21} className="mb-4 text-warningGlow" />
          <p className="text-sm text-slate-500">Chunks</p>
          <h3 className="mt-2 text-xl font-semibold">{chunks.length}</h3>
        </section>
        <section className="glass-panel rounded-lg p-4">
          <Sparkles size={21} className="mb-4 text-cyanGlow" />
          <p className="text-sm text-slate-500">Topics</p>
          <h3 className="mt-2 text-xl font-semibold">{topics.length}</h3>
        </section>
      </div>

      <div className="mb-5 grid gap-3 lg:grid-cols-[1fr_220px]">
        <label className="flex items-center gap-3 rounded-lg border border-white/10 bg-slate-950/50 px-4 py-3">
          <Search size={18} className="text-slate-500" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search extracted knowledge..."
            className="min-w-0 flex-1 bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-600"
          />
        </label>
        <select
          value={sourceType}
          onChange={(event) => setSourceType(event.target.value)}
          className="rounded-lg border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-slate-200 outline-none"
        >
          <option value="">All sources</option>
          <option value="screen">Screen</option>
          <option value="browser">Browser</option>
          <option value="code">Code</option>
          <option value="document">Document</option>
          <option value="youtube">YouTube</option>
          <option value="article">Article</option>
        </select>
      </div>

      <div className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <section className="glass-panel rounded-lg p-5">
          <h3 className="font-semibold">Extracted Content Cards</h3>
          <div className="thin-scrollbar mt-4 max-h-[620px] space-y-3 overflow-y-auto">
            {chunks.map((chunk) => (
              <button
                type="button"
                key={chunk.id}
                onClick={() => setSelectedChunk(chunk)}
                className={[
                  'w-full rounded-lg border p-4 text-left transition hover:bg-white/8',
                  selectedChunk?.id === chunk.id ? 'border-cyanGlow/40 bg-cyanGlow/10' : 'border-white/10 bg-white/5'
                ].join(' ')}
              >
                <div className="mb-2 flex items-center justify-between gap-3">
                  <p className="truncate text-sm font-semibold text-slate-100">{chunk.topic_label}</p>
                  <span className="rounded-md border border-white/10 px-2 py-1 text-xs text-slate-400">{chunk.source_type}</span>
                </div>
                <p className="line-clamp-3 text-sm leading-6 text-slate-400">{chunk.content}</p>
              </button>
            ))}
            {!chunks.length && (
              <div className="rounded-lg border border-white/10 bg-white/5 p-5 text-sm text-slate-500">
                No OCR chunks yet. Capture screenshots in Live Activity, then process them here.
              </div>
            )}
          </div>
        </section>

        <section className="glass-panel rounded-lg p-5">
          <h3 className="font-semibold">Screenshot + Extracted Text</h3>
          {selectedChunk ? (
            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              <div className="flex min-h-[320px] items-center justify-center overflow-hidden rounded-lg border border-white/10 bg-slate-950/50">
                <img
                  src={`${apiClient.baseUrl}/api/capture/screenshots/${selectedChunk.screenshot_id}/image?token=${encodeURIComponent(apiClient.getToken())}`}
                  alt="OCR source screenshot"
                  className="max-h-[460px] w-full object-contain"
                />
              </div>
              <div className="thin-scrollbar max-h-[460px] overflow-y-auto rounded-lg border border-white/10 bg-white/5 p-4">
                <p className="mb-3 text-xs uppercase text-cyanGlow">{selectedChunk.app_source || 'unknown source'}</p>
                <h4 className="mb-3 font-semibold">{selectedChunk.topic_label}</h4>
                <p className="whitespace-pre-wrap text-sm leading-6 text-slate-300">{selectedChunk.content}</p>
              </div>
            </div>
          ) : (
            <div className="mt-4 rounded-lg border border-white/10 bg-white/5 p-6 text-sm text-slate-500">
              Select a knowledge card to inspect the screenshot and extracted text.
            </div>
          )}

          <div className="mt-5 grid gap-4 lg:grid-cols-2">
            <div className="rounded-lg border border-white/10 bg-white/5 p-4">
              <h4 className="font-semibold">Detected Topics</h4>
              <div className="mt-3 flex flex-wrap gap-2">
                {topics.slice(0, 10).map((topic) => (
                  <span key={topic.id} className="rounded-lg border border-mintGlow/20 bg-mintGlow/10 px-3 py-1 text-xs text-mintGlow">
                    {topic.topic_label}
                  </span>
                ))}
              </div>
            </div>
            <div className="rounded-lg border border-white/10 bg-white/5 p-4">
              <h4 className="font-semibold">Session Knowledge</h4>
              <div className="mt-3 space-y-2">
                {sessions.slice(0, 3).map((session) => (
                  <div key={session.id}>
                    <p className="text-sm font-medium text-slate-200">{session.title}</p>
                    <p className="line-clamp-2 text-xs leading-5 text-slate-500">{session.summary}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </div>

      {status.last_error && (
        <p className="mt-4 rounded-lg border border-red-400/20 bg-red-500/10 p-3 text-sm text-red-200">
          OCR warning: {status.last_error}
        </p>
      )}
    </div>
  );
}

export default OcrKnowledge;
