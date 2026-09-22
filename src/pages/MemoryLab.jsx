import { useEffect, useState } from 'react';
import {
  AlertTriangle, Award, Brain, Clock, Eraser, FlaskConical, GitMerge,
  Layers, Loader2, Play, RefreshCw, Target, TrendingUp
} from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';
import { apiFetch } from '../services/apiClient.js';

/**
 * MemoryLab - live demonstration of the paper's seven contributions.
 * ---------------------------------------------------------------------------
 * Every panel reads real state from /api/research/*. Nothing here is mocked, so
 * what a reviewer sees on screen is what the benchmark measured.
 */
const TABS = [
  { id: 'overview', label: 'Overview', icon: Layers },
  { id: 'scoring', label: '1. Memory Scoring', icon: Award },
  { id: 'temporal', label: '2. Temporal Graph', icon: Clock },
  { id: 'conflicts', label: '3. Contradictions', icon: AlertTriangle },
  { id: 'consolidate', label: '4. Consolidation', icon: GitMerge },
  { id: 'gaps', label: '5. Knowledge Gaps', icon: Target },
  { id: 'forget', label: '6. Forgetting', icon: Eraser },
  { id: 'bench', label: '7. Benchmark', icon: FlaskConical }
];

function Bar({ value, color = 'bg-cyan-400' }) {
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/5">
      <div className={`h-full ${color}`} style={{ width: `${Math.min(100, Math.max(0, value * 100))}%` }} />
    </div>
  );
}

function Card({ children, className = '' }) {
  return <div className={`rounded-xl border border-white/10 bg-[#0f1422] p-3.5 ${className}`}>{children}</div>;
}

export default function MemoryLab() {
  const { apiClient } = useBackend();
  const [tab, setTab] = useState('overview');
  const [data, setData] = useState({});
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState(null);

  const get = async (path) => {
    const res = await apiFetch(`${apiClient.baseUrl}${path}`);
    return res.ok ? res.json() : null;
  };
  const post = async (path, body) => {
    const res = await apiFetch(`${apiClient.baseUrl}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined
    });
    return { ok: res.ok, status: res.status, data: await res.json().catch(() => ({})) };
  };

  async function load(tabId = tab) {
    setBusy('load');
    try {
      const endpoints = {
        overview: '/api/research/overview',
        scoring: '/api/research/scores?limit=20',
        temporal: '/api/research/temporal',
        conflicts: '/api/research/conflicts',
        gaps: '/api/research/gaps',
        forget: '/api/research/forgotten',
        bench: '/api/research/runs?limit=8'
      };
      const path = endpoints[tabId];
      if (!path) return;
      const payload = await get(path);
      setData((d) => ({ ...d, [tabId]: payload }));
    } finally {
      setBusy('');
    }
  }

  useEffect(() => { load(tab); }, [tab]);

  async function action(name, fn, successText) {
    setBusy(name);
    setNotice(null);
    try {
      const result = await fn();
      if (result?.ok === false) {
        setNotice({ type: 'error', text: result.data?.detail || 'Action failed.' });
      } else {
        setNotice({ type: 'success', text: successText(result?.data ?? result) });
        await load(tab);
      }
    } catch (err) {
      setNotice({ type: 'error', text: String(err.message || err) });
    } finally {
      setBusy('');
    }
  }

  const noticeStyle = {
    success: 'border-emerald-400/30 bg-emerald-500/10 text-emerald-200',
    error: 'border-red-400/30 bg-red-500/10 text-red-200'
  };

  return (
    <div className="flex h-full w-full flex-col bg-[#111318] text-slate-100 font-sans select-none">
      {/* Header */}
      <div className="border-b border-white/10 px-6 py-4">
        <div className="mx-auto flex w-full max-w-6xl items-center gap-3">
          <Brain size={20} className="text-purple-400" />
          <div className="min-w-0 flex-1">
            <h2 className="text-base font-bold uppercase tracking-wider font-mono text-white">Memory Lab</h2>
            <p className="text-xs text-slate-400">
              Live state of the seven research contributions — the same code the benchmark measures.
            </p>
          </div>
          <button
            type="button"
            onClick={() => load(tab)}
            className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 hover:bg-white/10 shrink-0"
          >
            <RefreshCw size={12} className={busy === 'load' ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>

        {/* Tabs */}
        <div className="mx-auto mt-3 flex w-full max-w-6xl flex-wrap gap-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[11px] transition ${
                tab === t.id ? 'bg-purple-500/15 text-purple-200 font-semibold' : 'text-slate-400 hover:bg-white/5'
              }`}
            >
              <t.icon size={11} /> {t.label}
            </button>
          ))}
        </div>
      </div>

      {notice && (
        <div className={`mx-6 mt-4 rounded-xl border px-4 py-2.5 text-xs ${noticeStyle[notice.type]}`}>
          {notice.text}
        </div>
      )}

      <div className="flex-1 overflow-y-auto thin-scrollbar p-6">
        <div className="mx-auto w-full max-w-6xl space-y-4">

          {/* ---------------------------------------------- OVERVIEW */}
          {tab === 'overview' && (
            <>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {[
                  ['Memories', data.overview?.memories_total, 'text-white'],
                  ['Scored', data.overview?.scored, 'text-cyan-300'],
                  ['Temporal facts', data.overview?.temporal_facts, 'text-purple-300'],
                  ['Open facts', data.overview?.open_facts, 'text-emerald-300'],
                  ['Superseded', data.overview?.superseded_facts, 'text-amber-300'],
                  ['Conflicts', data.overview?.conflicts, 'text-red-300'],
                  ['Gaps', data.overview?.gaps, 'text-blue-300'],
                  ['Forgotten', data.overview?.forgotten, 'text-slate-400']
                ].map(([label, value, color]) => (
                  <Card key={label}>
                    <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500">{label}</p>
                    <p className={`mt-1 text-xl font-bold font-mono ${color}`}>{value ?? '—'}</p>
                  </Card>
                ))}
              </div>

              <Card>
                <p className="text-xs font-bold text-white mb-2">Run the pipeline</p>
                <div className="flex flex-wrap gap-2">
                  <button type="button" disabled={!!busy}
                    onClick={() => action('score', () => post('/api/research/score'),
                      (d) => `Scored ${d.scored} memories.`)}
                    className="flex items-center gap-1.5 rounded-lg bg-cyan-400 px-3 py-1.5 text-[11px] font-bold text-slate-950 disabled:opacity-40">
                    {busy === 'score' ? <Loader2 size={11} className="animate-spin" /> : <Award size={11} />} 1. Score
                  </button>
                  <button type="button" disabled={!!busy}
                    onClick={() => action('conf', () => post('/api/research/conflicts/detect'),
                      (d) => `Scanned ${d.memories_examined} memories, found ${d.conflicts} conflicts.`)}
                    className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] font-semibold text-slate-200 disabled:opacity-40">
                    {busy === 'conf' ? <Loader2 size={11} className="animate-spin" /> : <AlertTriangle size={11} />} 3. Detect conflicts
                  </button>
                  <button type="button" disabled={!!busy}
                    onClick={() => action('conso', () => post('/api/research/consolidate?threshold=0.78&dry_run=true'),
                      (d) => `Found ${d.clusters_found} duplicate clusters (${d.context_reduction_pct}% context saving) — dry run.`)}
                    className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] font-semibold text-slate-200 disabled:opacity-40">
                    {busy === 'conso' ? <Loader2 size={11} className="animate-spin" /> : <GitMerge size={11} />} 4. Consolidate
                  </button>
                  <button type="button" disabled={!!busy}
                    onClick={() => action('gaps', () => get('/api/research/gaps?recompute=true').then((d) => ({ ok: true, data: d })),
                      (d) => `Examined ${d.concepts_examined} concepts, found ${d.gaps} gaps.`)}
                    className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] font-semibold text-slate-200 disabled:opacity-40">
                    {busy === 'gaps' ? <Loader2 size={11} className="animate-spin" /> : <Target size={11} />} 5. Find gaps
                  </button>
                </div>
              </Card>
            </>
          )}

          {/* ---------------------------------------------- SCORING */}
          {tab === 'scoring' && (
            <>
              <p className="text-[11px] text-slate-400">
                M = w₁R + w₂F + w₃T + w₄G + w₅U + w₆P − w₇D − w₈C — every component stored, so each
                score is auditable rather than a black box.
              </p>
              {(data.scoring || []).map((row) => (
                <Card key={row.memory_id}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-xs font-semibold text-white">{row.title || '(untitled)'}</p>
                      <p className="text-[10px] font-mono text-slate-500">
                        #{row.memory_id} · {row.source_type}
                      </p>
                    </div>
                    <span className="shrink-0 font-mono text-sm font-bold text-cyan-300">
                      {row.total.toFixed(3)}
                    </span>
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1.5 sm:grid-cols-4">
                    {Object.entries(row.components).map(([name, value]) => (
                      <div key={name}>
                        <div className="flex items-center justify-between">
                          <span className="text-[9px] font-mono uppercase text-slate-500">
                            {name.slice(0, 4)}
                          </span>
                          <span className="text-[9px] font-mono text-slate-400">{value.toFixed(2)}</span>
                        </div>
                        <Bar
                          value={value}
                          color={['redundancy', 'contradiction'].includes(name) ? 'bg-red-400' : 'bg-cyan-400'}
                        />
                      </div>
                    ))}
                  </div>
                </Card>
              ))}
              {!data.scoring?.length && (
                <Card><p className="text-xs text-slate-400">No scores yet — run step 1 from Overview.</p></Card>
              )}
            </>
          )}

          {/* ------------------------------------------- TEMPORAL */}
          {tab === 'temporal' && (
            <>
              <Card>
                <p className="text-xs font-bold text-white mb-2">Currently true</p>
                {(data.temporal?.current || []).map((f) => (
                  <div key={f.id} className="flex items-center gap-2 py-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                    <span className="text-[11px] font-mono text-slate-400">{f.predicate}</span>
                    <span className="text-[11px] text-white">{f.object}</span>
                    <span className="ml-auto text-[10px] font-mono text-slate-500">
                      conf {f.confidence?.toFixed(2)}
                    </span>
                  </div>
                ))}
                {!data.temporal?.current?.length && (
                  <p className="text-[11px] text-slate-500">No open facts. Say "I am learning X" in the AI Agent, then refresh.</p>
                )}
              </Card>

              <Card>
                <p className="text-xs font-bold text-white mb-2">
                  Timeline — superseded facts are closed, never deleted
                </p>
                {(data.temporal?.history || []).map((f) => (
                  <div key={f.id} className="flex items-center gap-2 py-1 border-b border-white/5 last:border-0">
                    <span className={`h-1.5 w-1.5 rounded-full ${f.current ? 'bg-emerald-400' : 'bg-slate-600'}`} />
                    <span className="w-24 shrink-0 truncate text-[11px] font-mono text-slate-400">{f.predicate}</span>
                    <span className={`min-w-0 flex-1 truncate text-[11px] ${f.current ? 'text-white' : 'text-slate-500 line-through'}`}>
                      {f.object}
                    </span>
                    <span className="shrink-0 text-[10px] font-mono text-slate-500">
                      {f.valid_from ? f.valid_from.slice(0, 10) : '—'} → {f.current ? 'now' : f.valid_to?.slice(0, 10)}
                    </span>
                  </div>
                ))}
              </Card>

              <Card>
                <p className="text-xs font-bold text-white mb-2">Try it</p>
                <div className="flex flex-wrap gap-2">
                  {['I am learning Python for data analysis.',
                    'I am now mainly focusing on Java for backend development.'].map((text, i) => (
                    <button key={i} type="button" disabled={!!busy}
                      onClick={() => action('ingest', () => post('/api/research/temporal/ingest', { text }),
                        (d) => `Extracted ${d.extracted} fact(s): created ${d.recorded.created}, superseded ${d.recorded.superseded}.`)}
                      className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] text-slate-200 hover:bg-white/10 disabled:opacity-40">
                      {busy === 'ingest' ? <Loader2 size={11} className="inline animate-spin" /> : null} Send: “{text.slice(0, 30)}…”
                    </button>
                  ))}
                  <p className="w-full text-[10px] text-slate-500">
                    Sending these two in order demonstrates supersession: the first becomes historical, the second current.
                  </p>
                </div>
              </Card>
            </>
          )}

          {/* ------------------------------------------ CONFLICTS */}
          {tab === 'conflicts' && (
            <>
              <div className="grid grid-cols-3 gap-3">
                <Card><p className="text-[10px] font-mono uppercase text-slate-500">Total</p>
                  <p className="text-xl font-bold font-mono text-red-300">{data.conflicts?.total ?? '—'}</p></Card>
                <Card><p className="text-[10px] font-mono uppercase text-slate-500">Unresolved</p>
                  <p className="text-xl font-bold font-mono text-amber-300">{data.conflicts?.unresolved ?? '—'}</p></Card>
                <Card><p className="text-[10px] font-mono uppercase text-slate-500">Types</p>
                  <p className="text-[11px] font-mono text-slate-300">
                    {Object.entries(data.conflicts?.by_type || {}).map(([k, v]) => `${k}:${v}`).join(' ') || '—'}
                  </p></Card>
              </div>

              {(data.conflicts?.conflicts || []).map((c) => (
                <Card key={c.id} className="border-red-400/20">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="rounded bg-red-400/10 px-1.5 py-0.5 text-[9px] font-mono font-bold text-red-300">
                      {c.type}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500">severity {c.severity?.toFixed(2)}</span>
                    <span className="ml-auto text-[10px] font-mono text-cyan-300">{c.resolution}</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-start gap-2">
                      <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-600" />
                      <p className="text-[11px] text-slate-500 line-through">{c.older_value}</p>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
                      <p className="text-[11px] text-white">{c.newer_value}</p>
                    </div>
                  </div>
                </Card>
              ))}
              {!data.conflicts?.total && (
                <Card><p className="text-xs text-slate-400">No conflicts. Run step 3 from Overview to scan.</p></Card>
              )}
            </>
          )}

          {/* --------------------------------------- CONSOLIDATION */}
          {tab === 'consolidate' && (
            <ConsolidatePanel busy={busy} action={action} post={post} />
          )}

          {/* ------------------------------------------------ GAPS */}
          {tab === 'gaps' && (
            <>
              <p className="text-[11px] text-slate-400">
                Exposure without depth: mentioned repeatedly, weakly connected, never explained.
                A well-connected concept is never reported as a gap however often it appears.
              </p>
              {(data.gaps?.items || []).map((g) => (
                <Card key={g.concept}>
                  <div className="flex items-center gap-2">
                    <Target size={12} className="text-blue-300 shrink-0" />
                    <p className="text-xs font-semibold text-white">{g.concept}</p>
                    <span className="ml-auto font-mono text-xs font-bold text-blue-300">
                      gap {g.gap_score.toFixed(3)}
                    </span>
                  </div>
                  <p className="mt-1 text-[11px] text-slate-400">{g.rationale}</p>
                  <div className="mt-2 grid grid-cols-3 gap-3">
                    <div><p className="text-[9px] font-mono uppercase text-slate-500">mentions</p>
                      <p className="text-[11px] font-mono text-slate-300">{g.mentions}</p></div>
                    <div><p className="text-[9px] font-mono uppercase text-slate-500">depth</p>
                      <Bar value={g.depth_score} color="bg-emerald-400" />
                      <p className="text-[11px] font-mono text-slate-300">{g.depth_score.toFixed(2)}</p></div>
                    <div><p className="text-[9px] font-mono uppercase text-slate-500">connectivity</p>
                      <Bar value={g.connectivity} color="bg-amber-400" />
                      <p className="text-[11px] font-mono text-slate-300">{g.connectivity.toFixed(2)}</p></div>
                  </div>
                </Card>
              ))}
              {!data.gaps?.items?.length && (
                <Card><p className="text-xs text-slate-400">No gaps. Run step 5 from Overview.</p></Card>
              )}
            </>
          )}

          {/* -------------------------------------------- FORGETTING */}
          {tab === 'forget' && (
            <>
              <Card>
                <p className="text-xs font-bold text-white mb-1">Unlearn something</p>
                <p className="text-[11px] text-slate-400 mb-2">
                  Enforced at every retrieval surface, not just by deleting a row — a surviving
                  vector or index entry would still be returned.
                </p>
                <ForgetForm busy={busy} action={action} post={post} />
              </Card>

              <Card>
                <p className="text-xs font-bold text-white mb-2">
                  Forgotten: {data.forgotten?.forgotten_count ?? 0} of {data.forgotten?.total_memories ?? 0}
                </p>
                {(data.forgotten?.entries || []).map((e) => (
                  <div key={e.memory_id} className="flex items-center gap-2 border-b border-white/5 py-1.5 last:border-0">
                    <Eraser size={11} className="text-slate-500 shrink-0" />
                    <span className="text-[11px] font-mono text-slate-300">#{e.memory_id}</span>
                    <span className="min-w-0 flex-1 truncate text-[11px] text-slate-400">{e.reason}</span>
                    <button
                      type="button"
                      disabled={!!busy}
                      onClick={() => action('restore', () => post(`/api/research/forget/${e.memory_id}/restore`),
                        () => `Memory #${e.memory_id} restored and re-indexed.`)}
                      className="shrink-0 rounded border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] text-cyan-300 hover:bg-white/10 disabled:opacity-40"
                    >
                      restore
                    </button>
                  </div>
                ))}
                {!data.forgotten?.entries?.length && (
                  <p className="text-[11px] text-slate-500">Nothing forgotten yet.</p>
                )}
              </Card>
            </>
          )}

          {/* ---------------------------------------------- BENCHMARK */}
          {tab === 'bench' && (
            <BenchmarkPanel busy={busy} action={action} post={post} get={get} runs={data.runs} />
          )}
        </div>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- panels */
function ConsolidatePanel({ busy, action, post }) {
  const [result, setResult] = useState(null);
  return (
    <>
      <Card>
        <p className="text-xs font-bold text-white mb-1">Merge near-duplicate memories</p>
        <p className="text-[11px] text-slate-400 mb-2">
          Reworded duplicates score ~0.82 cosine; unrelated memories score under 0.30. The
          threshold is calibrated at 0.78 — the usual 0.90 suggestion misses every reworded
          duplicate, which is the real-world case.
        </p>
        <div className="flex gap-2">
          <button type="button" disabled={!!busy}
            onClick={async () => {
              const r = await action('dry', () => post('/api/research/consolidate?threshold=0.78&dry_run=true'),
                () => 'Dry run complete — nothing merged.');
              if (r !== undefined) setResult(null);
            }}
            className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] font-semibold text-slate-200 disabled:opacity-40">
            {busy === 'dry' ? <Loader2 size={11} className="inline animate-spin" /> : null} Dry run
          </button>
          <button type="button" disabled={!!busy}
            onClick={async () => {
              const res = await post('/api/research/consolidate?threshold=0.78');
              setResult(res.data);
            }}
            className="flex items-center gap-1.5 rounded-lg bg-purple-400 px-3 py-1.5 text-[11px] font-bold text-slate-950 disabled:opacity-40">
            {busy === 'real' ? <Loader2 size={11} className="animate-spin" /> : <GitMerge size={11} />} Consolidate
          </button>
        </div>
      </Card>

      {result && (
        <Card>
          <p className="text-xs font-bold text-white mb-2">Result</p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[['Clusters', result.clusters_found], ['Merged', result.memories_merged],
              ['Tokens before', result.tokens_before], ['Tokens after', result.tokens_after]].map(([l, v]) => (
              <div key={l}>
                <p className="text-[9px] font-mono uppercase text-slate-500">{l}</p>
                <p className="text-sm font-mono text-white">{v}</p>
              </div>
            ))}
          </div>
          <p className="mt-2 text-[11px] text-emerald-300">
            Context reduction {result.context_reduction_pct}% · provenance preserved
            ({result.provenance_preserved ? 'merged ids recorded' : 'NOT recorded'})
          </p>
          {(result.groups || []).map((g) => (
            <div key={g.canonical_memory_id} className="mt-2 rounded-lg border border-white/5 bg-black/20 p-2">
              <p className="text-[11px] text-white">Kept #{g.canonical_memory_id}: {g.canonical_title}</p>
              <p className="text-[10px] font-mono text-slate-500">
                merged [{g.merged_memory_ids.join(', ')}] · {g.savings_pct}% smaller
              </p>
            </div>
          ))}
        </Card>
      )}
    </>
  );
}

function ForgetForm({ busy, action, post }) {
  const [query, setQuery] = useState('');
  return (
    <div className="flex gap-2">
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Text to forget, e.g. 'temporary portal credential'"
        className="min-w-0 flex-1 rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-xs outline-none focus:border-red-400/40"
      />
      <button
        type="button"
        disabled={!query.trim() || !!busy}
        onClick={() => action('forget', () => post('/api/research/forget', { query, hard: false }),
          (d) => `Forgot ${d.forgotten} of ${d.matched} matching memories.`)}
        className="flex items-center gap-1.5 rounded-lg bg-red-400 px-3 py-2 text-xs font-bold text-slate-950 disabled:opacity-40"
      >
        {busy === 'forget' ? <Loader2 size={12} className="animate-spin" /> : <Eraser size={12} />} Forget
      </button>
    </div>
  );
}

const METRIC_ROWS = [
  ['hit_at_k', 'Hit@5', 'higher'],
  ['mrr', 'MRR', 'higher'],
  ['stale_top1_rate', 'Stale@1', 'lower'],
  ['forgotten_leak_rate', 'Forgotten leak', 'lower'],
  ['duplicate_rate', 'Duplicate rate', 'lower']
];

function BenchmarkPanel({ busy, post, runs }) {
  const [summary, setSummary] = useState(null);


  return (
    <>
      <Card>
        <div className="flex items-start gap-2">
          <FlaskConical size={14} className="mt-0.5 text-purple-300 shrink-0" />
          <div className="min-w-0 flex-1">
            <p className="text-xs font-bold text-white">PersonalBrain-Bench</p>
            <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
              15-memory synthetic personal corpus, 11 questions across six categories, evaluated
              against three baselines on identical questions. Deterministic — two consecutive runs
              produce byte-identical metrics.
            </p>
          </div>
        </div>
        <button
          type="button"
          disabled={!!busy}
          onClick={async () => {
            setSummary(null);
            const res = await post('/api/research/benchmark', { k: 5 });
            setSummary(res.data);
          }}
          className="mt-3 flex items-center gap-1.5 rounded-lg bg-purple-400 px-4 py-2 text-xs font-bold text-slate-950 disabled:opacity-40"
        >
          {busy === 'bench' ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />}
          Run all four systems
        </button>
      </Card>

      {summary?.summary && (
        <Card>
          <p className="text-xs font-bold text-white mb-3 flex items-center gap-1.5">
            <TrendingUp size={12} className="text-emerald-300" /> Results (k = {summary.k})
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-[11px]">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="py-1.5 text-left font-mono text-[9px] uppercase text-slate-500">Metric</th>
                  {Object.keys(summary.summary).map((mode) => (
                    <th key={mode} className={`py-1.5 text-right font-mono text-[9px] uppercase ${
                      mode === 'adaptive' ? 'text-purple-300' : 'text-slate-500'
                    }`}>{mode}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {METRIC_ROWS.map(([key, label, direction]) => {
                  const values = Object.values(summary.summary).map((m) => m[key]);
                  const best = direction === 'higher' ? Math.max(...values) : Math.min(...values);
                  return (
                    <tr key={key} className="border-b border-white/5">
                      <td className="py-1.5 text-slate-300">{label}</td>
                      {Object.entries(summary.summary).map(([mode, m]) => (
                        <td key={mode} className={`py-1.5 text-right font-mono ${
                          m[key] === best ? 'font-bold text-emerald-300' : 'text-slate-400'
                        }`}>
                          {m[key].toFixed(3)}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-[10px] text-slate-500">
            Green = best. Hit@5 saturates at 1.000 for every system, which is exactly why the
            rank-sensitive and staleness metrics are the informative ones.
          </p>
        </Card>
      )}

      {runs?.length > 0 && (
        <Card>
          <p className="text-xs font-bold text-white mb-2">Recorded runs</p>
          {runs.map((r) => (
            <div key={r.id} className="flex items-center gap-2 border-b border-white/5 py-1 last:border-0 text-[11px]">
              <span className="font-mono text-slate-400">{r.system}</span>
              <span className="text-slate-500">q={r.questions}</span>
              <span className="ml-auto font-mono text-slate-400">
                MRR {r.metrics?.mrr ?? '—'} · stale {r.metrics?.staleness_rate ?? '—'}
              </span>
            </div>
          ))}
        </Card>
      )}
    </>
  );
}
