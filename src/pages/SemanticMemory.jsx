import { useEffect, useMemo, useState } from 'react';
import { Brain, GitBranch, Layers3, Network, RefreshCw, Search, Sparkles } from 'lucide-react';
import PageHeader from '../components/PageHeader.jsx';
import { useBackend } from '../context/BackendContext.jsx';

function SemanticMemory() {
  const { apiClient, loginDemo } = useBackend();
  const [query, setQuery] = useState('Python OCR tutorial');
  const [sourceType, setSourceType] = useState('');
  const [status, setStatus] = useState({ queued: 0, indexed_memories: 0, last_error: '' });
  const [results, setResults] = useState([]);
  const [selected, setSelected] = useState(null);
  const [related, setRelated] = useState([]);
  const [clusters, setClusters] = useState([]);
  const [context, setContext] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [isBusy, setIsBusy] = useState(false);

  const topClusters = useMemo(() => clusters.slice(0, 8), [clusters]);

  async function ensureLogin() {
    if (!apiClient.getToken()) await loginDemo();
  }

  async function refreshMeta() {
    if (!apiClient.getToken()) return;
    const [nextStatus, nextClusters, nextJobs] = await Promise.all([
      apiClient.semanticStatus(),
      apiClient.fetchSemanticClusters(),
      apiClient.fetchEmbeddingJobs()
    ]);
    setStatus(nextStatus);
    setClusters(nextClusters);
    setJobs(nextJobs);
  }

  async function runSearch() {
    setIsBusy(true);
    try {
      await ensureLogin();
      const payload = { query, limit: 10, source_type: sourceType || '' };
      const nextResults = await apiClient.hybridSemanticSearch(payload);
      setResults(nextResults);
      setSelected(nextResults[0] || null);
      setContext(await apiClient.assembleSemanticContext({ query, limit: 5 }));
      await refreshMeta();
    } finally {
      setIsBusy(false);
    }
  }

  async function indexMemories() {
    setIsBusy(true);
    try {
      await ensureLogin();
      await apiClient.indexSemanticMemories();
      await refreshMeta();
    } finally {
      setIsBusy(false);
    }
  }

  async function rebuildClusters() {
    setIsBusy(true);
    try {
      await ensureLogin();
      await apiClient.rebuildSemanticClusters();
      await apiClient.detectSemanticRelationships();
      await refreshMeta();
    } finally {
      setIsBusy(false);
    }
  }

  useEffect(() => {
    refreshMeta();
  }, []);

  useEffect(() => {
    if (!selected) {
      setRelated([]);
      return;
    }
    apiClient.relatedSemanticMemories(selected.memory_id).then(setRelated).catch(() => setRelated([]));
  }, [selected?.memory_id]);

  return (
    <div>
      <PageHeader
        eyebrow="Semantic Memory"
        title="AI memory explorer"
        description="Generate embeddings, index memories in ChromaDB, search by meaning, and discover related memories without RAG or chat yet."
        action={
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={indexMemories} disabled={isBusy} className="flex items-center gap-2 rounded-lg border border-cyanGlow/30 bg-cyanGlow/10 px-4 py-3 text-sm font-semibold text-cyanGlow transition hover:bg-cyanGlow/20 disabled:opacity-40">
              <RefreshCw size={17} />
              Index
            </button>
            <button type="button" onClick={rebuildClusters} disabled={isBusy} className="flex items-center gap-2 rounded-lg bg-mintGlow px-4 py-3 text-sm font-bold text-slate-950 transition hover:bg-emerald-300 disabled:opacity-40">
              <Network size={17} />
              Cluster
            </button>
          </div>
        }
      />

      <div className="mb-5 grid gap-4 md:grid-cols-4">
        <section className="glass-panel rounded-lg p-4">
          <Brain size={21} className="mb-4 text-mintGlow" />
          <p className="text-sm text-slate-500">Vector Index</p>
          <h3 className="mt-2 text-xl font-semibold">{status.indexed_memories || 0}</h3>
        </section>
        <section className="glass-panel rounded-lg p-4">
          <Layers3 size={21} className="mb-4 text-cyanGlow" />
          <p className="text-sm text-slate-500">Embedding Queue</p>
          <h3 className="mt-2 text-xl font-semibold">{status.queued || 0}</h3>
        </section>
        <section className="glass-panel rounded-lg p-4">
          <GitBranch size={21} className="mb-4 text-warningGlow" />
          <p className="text-sm text-slate-500">Clusters</p>
          <h3 className="mt-2 text-xl font-semibold">{clusters.length}</h3>
        </section>
        <section className="glass-panel rounded-lg p-4">
          <Sparkles size={21} className="mb-4 text-cyanGlow" />
          <p className="text-sm text-slate-500">Worker</p>
          <h3 className="mt-2 text-xl font-semibold">{status.is_running ? 'Running' : 'Stopped'}</h3>
        </section>
      </div>

      <section className="glass-panel mb-5 rounded-lg p-4">
        <div className="grid gap-3 lg:grid-cols-[1fr_180px_130px]">
          <label className="flex items-center gap-3 rounded-lg border border-white/10 bg-slate-950/50 px-4 py-3">
            <Search size={18} className="text-slate-500" />
            <input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => event.key === 'Enter' && runSearch()} placeholder="Search by meaning..." className="min-w-0 flex-1 bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-600" />
          </label>
          <select value={sourceType} onChange={(event) => setSourceType(event.target.value)} className="rounded-lg border border-white/10 bg-slate-950/70 px-4 py-3 text-sm outline-none">
            <option value="">All sources</option>
            <option value="screen">Screen</option>
            <option value="code">Code</option>
            <option value="article">Article</option>
            <option value="document">Document</option>
            <option value="youtube">YouTube</option>
            <option value="clipboard">Clipboard</option>
          </select>
          <button type="button" onClick={runSearch} disabled={isBusy || !query.trim()} className="rounded-lg bg-cyanGlow px-4 py-3 text-sm font-bold text-slate-950 transition hover:bg-cyan-300 disabled:opacity-40">Search</button>
        </div>
      </section>

      <div className="grid gap-5 xl:grid-cols-[0.95fr_1.1fr_0.85fr]">
        <section className="glass-panel rounded-lg p-5">
          <h3 className="font-semibold">Semantic Results</h3>
          <div className="thin-scrollbar mt-4 max-h-[650px] space-y-3 overflow-y-auto">
            {results.map((result) => (
              <button key={result.memory_id} type="button" onClick={() => setSelected(result)} className={`w-full rounded-lg border p-4 text-left transition hover:bg-white/8 ${selected?.memory_id === result.memory_id ? 'border-cyanGlow/40 bg-cyanGlow/10' : 'border-white/10 bg-white/5'}`}>
                <div className="mb-2 flex items-center justify-between gap-3">
                  <p className="truncate font-semibold text-slate-100">{result.title}</p>
                  <span className="rounded-md bg-mintGlow/10 px-2 py-1 text-xs text-mintGlow">{Math.round(result.score * 100)}%</span>
                </div>
                <p className="line-clamp-3 text-sm leading-6 text-slate-400">{result.content}</p>
                <p className="mt-3 text-xs text-slate-500">{result.source_type} · {result.app_source}</p>
              </button>
            ))}
            {!results.length && <p className="rounded-lg border border-white/10 bg-white/5 p-5 text-sm text-slate-500">Index memories, then search for an idea like "Python OCR tutorial".</p>}
          </div>
        </section>

        <section className="glass-panel rounded-lg p-5">
          <h3 className="font-semibold">Connected Memory</h3>
          {selected ? (
            <div className="mt-4 space-y-4">
              {selected.screenshot_id && (
                <div className="overflow-hidden rounded-lg border border-white/10 bg-slate-950/50">
                  <img src={`${apiClient.baseUrl}/api/capture/screenshots/${selected.screenshot_id}/image?token=${encodeURIComponent(apiClient.getToken())}`} alt="Semantic memory screenshot" className="max-h-72 w-full object-contain" loading="lazy" />
                </div>
              )}
              <div>
                <p className="text-xs uppercase text-cyanGlow">{selected.topic_label}</p>
                <h4 className="mt-2 text-xl font-semibold">{selected.title}</h4>
                <p className="mt-2 text-sm text-slate-500">Similarity {Math.round(selected.score * 100)}% · {new Date(selected.created_at).toLocaleString()}</p>
              </div>
              <p className="whitespace-pre-wrap rounded-lg border border-white/10 bg-white/5 p-4 text-sm leading-6 text-slate-300">{selected.content}</p>
              <div>
                <h4 className="mb-3 font-semibold">Related Suggestions</h4>
                <div className="space-y-2">
                  {related.map((item) => (
                    <button key={item.memory_id} type="button" onClick={() => setSelected(item)} className="w-full rounded-lg border border-white/10 bg-white/5 p-3 text-left text-sm text-slate-300 transition hover:bg-white/10">
                      <span className="font-medium text-slate-100">{item.title}</span>
                      <span className="ml-2 text-xs text-mintGlow">{Math.round(item.score * 100)}%</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="mt-4 rounded-lg border border-white/10 bg-white/5 p-5 text-sm text-slate-500">Select a semantic result to inspect its context.</p>
          )}
        </section>

        <section className="glass-panel rounded-lg p-5">
          <h3 className="font-semibold">Topic Clusters</h3>
          <div className="mt-4 flex flex-wrap gap-2">
            {topClusters.map((cluster) => (
              <span key={cluster.id} className="rounded-lg border border-mintGlow/20 bg-mintGlow/10 px-3 py-2 text-xs text-mintGlow">{cluster.label} · {cluster.size}</span>
            ))}
          </div>

          <div className="mt-5 rounded-lg border border-white/10 bg-white/5 p-4">
            <h4 className="font-semibold">Assembled Context</h4>
            <div className="mt-3 space-y-3">
              {context?.items?.map((item) => (
                <div key={item.memory_id}>
                  <p className="text-sm font-medium text-slate-200">{item.title}</p>
                  <p className="line-clamp-2 text-xs leading-5 text-slate-500">{item.content}</p>
                </div>
              ))}
              {!context?.items?.length && <p className="text-sm text-slate-500">Run a search to assemble context.</p>}
            </div>
          </div>

          <div className="mt-5 rounded-lg border border-white/10 bg-white/5 p-4">
            <h4 className="font-semibold">Recent Jobs</h4>
            <div className="mt-3 space-y-2">
              {jobs.slice(0, 5).map((job) => (
                <div key={job.id} className="flex items-center justify-between gap-3 text-sm">
                  <span className="text-slate-400">Memory {job.memory_id || '-'}</span>
                  <span className={job.status === 'failed' ? 'text-red-300' : 'text-mintGlow'}>{job.status}</span>
                </div>
              ))}
              {!jobs.length && <p className="text-sm text-slate-500">No embedding jobs yet.</p>}
            </div>
          </div>
        </section>
      </div>

      {status.last_error && <p className="mt-4 rounded-lg border border-warningGlow/20 bg-warningGlow/10 p-3 text-sm text-warningGlow">Semantic engine note: {status.last_error}</p>}
    </div>
  );
}

export default SemanticMemory;
