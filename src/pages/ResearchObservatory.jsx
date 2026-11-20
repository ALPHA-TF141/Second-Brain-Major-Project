import { useCallback, useEffect, useRef, useState } from 'react';
import { Activity, ArrowDownToLine, FlaskConical, RefreshCw, Play, ArrowUpRight, Calculator } from 'lucide-react';
import { Link } from 'react-router-dom';
import { apiClient, apiFetch } from '../services/apiClient.js';
import './ResearchObservatory.css';
import { useBackend } from '../context/BackendContext.jsx';

const METRICS = ['hit_at_k', 'mrr', 'stale_top1_rate', 'forgotten_leak_rate', 'duplicate_rate', 'evidence_recall', 'staleness_rate', 'avg_context_chars'];
const LABELS = { hit_at_k: 'Hit@5', mrr: 'MRR', stale_top1_rate: 'Stale@1', forgotten_leak_rate: 'Leakage', duplicate_rate: 'Duplicate rate', evidence_recall: 'Evidence recall', staleness_rate: 'Stale / returned', avg_context_chars: 'Context chars' };
const MODE = { vanilla: 'TF-IDF', hybrid: 'Hybrid', graph: 'Graph', adaptive: 'Adaptive', adaptive_graph: 'Adaptive + graph' };
const fmt = (v, digits = 4) => typeof v === 'number' ? v.toFixed(digits) : '—';
const signed = v => typeof v === 'number' ? `${v > 0 ? '+' : ''}${v.toFixed(4)}` : '—';
async function observatoryRequest(path, post = false, body) {
  const r = await apiFetch(`${apiClient.baseUrl}${path}`, post ? { method: 'POST', ...(body ? { body: JSON.stringify(body) } : {}) } : {});
  const j = await r.json();
  if (!r.ok) throw new Error(typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail || j));
  return j;
}
function download(value, filename) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' }));
  const a = document.createElement('a'); a.href = url; a.download = filename; a.click(); URL.revokeObjectURL(url);
}
function numericLeaves(value, path = '') {
  if (typeof value === 'number') return [{ path, value }];
  if (!value || typeof value !== 'object') return [];
  return Object.entries(value).flatMap(([k, v]) => numericLeaves(v, path ? `${path}.${k}` : k));
}
function Json({ value, label = 'Inspect full data' }) {
  return <details className="ro-json"><summary>{label}</summary><pre>{JSON.stringify(value, null, 2)}</pre></details>;
}
function Panel({ title, subtitle, children, action }) {
  return <section className="ro-panel"><div className="ro-panel-title"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{action}</div>{children}</section>;
}
function NumericExplorer({ value }) {
  const [filter, setFilter] = useState('');
  const [page, setPage] = useState(0);
  const rows = numericLeaves(value).filter(r => r.path.toLowerCase().includes(filter.toLowerCase()));
  return <><div className="ro-tools"><input placeholder="Find a number by its data path…" aria-label="Filter calculation paths" value={filter} onChange={e => { setFilter(e.target.value); setPage(0); }} /><span>{rows.length} numeric values</span></div><div className="ro-table-wrap"><table><thead><tr><th>Exact JSON path</th><th>Recorded value</th></tr></thead><tbody>{rows.slice(page * 100, (page + 1) * 100).map(r => <tr key={r.path}><td className="ro-mono">{r.path}</td><td>{r.value}</td></tr>)}</tbody></table></div><div className="ro-tools"><button disabled={!page} onClick={() => setPage(p => p - 1)}>Previous</button><span>Page {page + 1} / {Math.max(1, Math.ceil(rows.length / 100))}</span><button disabled={(page + 1) * 100 >= rows.length} onClick={() => setPage(p => p + 1)}>Next</button></div><Json value={value} label="Full artifact, including labels and non-numeric data" /></>;
}

function LiveProbe({ revision }) {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('adaptive');
  const [spec, setSpec] = useState(null);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (!spec) return;
    let cancelled = false;
    setBusy(true);
    observatoryRequest('/api/observatory/probe', true, spec)
      .then(r => { if (!cancelled) { setData(r); setError(''); } })
      .catch(e => { if (!cancelled) setError(e.message); })
      .finally(() => { if (!cancelled) setBusy(false); });
    return () => { cancelled = true; };
  }, [spec, revision]);
  return <Panel title="Live retrieval outcome & calculation trace" subtitle="Set a query once; it is rerun when a new database revision is observed. Operational retrieval only—no invented accuracy.">
    <form className="ro-tools" onSubmit={e => { e.preventDefault(); setSpec({ query, mode, k: 5 }); }}>
      <input aria-label="Live retrieval query" placeholder="Ask a question about the live memories…" value={query} onChange={e => setQuery(e.target.value)} required />
      <select aria-label="Live retrieval mode" value={mode} onChange={e => setMode(e.target.value)}>{Object.entries(MODE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
      <button type="submit" disabled={busy}>{busy ? 'Calculating…' : 'Inspect live retrieval'}</button>
    </form>
    {error && <div className="ro-error">{error}</div>}
    {data && <><div className="ro-muted">{data.results.length} returned · {data.sampled_at} · {data.policy}</div>
      <div className="ro-table-wrap"><table><thead><tr><th>Rank</th><th>Memory</th><th>Actual ranking score</th></tr></thead><tbody>{data.results.map((r, i) => <tr key={r.memory_id}><td>{i + 1}</td><td>#{r.memory_id} · {r.title}</td><td>{fmt(r.score, 6)}</td></tr>)}</tbody></table></div>
      <Json value={data.trace} label="Candidate scores, hybrid fusion, graph and adaptive arithmetic" />
      <p className="ro-muted">{data.note}</p>
    </>}
  </Panel>;
}

export default function ResearchObservatory() {
  const { apiStatus } = useBackend();
  const [tab, setTab] = useState('benchmark');
  const [reference, setReference] = useState(null);
  const [run, setRun] = useState(null);
  const [source, setSource] = useState('');
  const [runs, setRuns] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [liveError, setLiveError] = useState('');
  const [live, setLive] = useState(null);
  const [auto, setAuto] = useState(true);
  const [offset, setOffset] = useState(0);
  const [changes, setChanges] = useState([]);
  const [scoreId, setScoreId] = useState(null);
  const [mode, setMode] = useState('adaptive');
  const [artifactName, setArtifactName] = useState('personas');
  const [artifact, setArtifact] = useState(null);
  const [previous, setPrevious] = useState(null);
  const previousLive = useRef(null);
  const loading = useRef(false);
  const mounted = useRef(true);

  const refreshLive = useCallback(async () => {
    if (loading.current || document.hidden || !apiClient.getToken()) return;
    loading.current = true;
    try {
      const data = await observatoryRequest(`/api/observatory/live?offset=${offset}&limit=50`);
      if (!mounted.current) return;
      const before = previousLive.current;
      if (before && before.revision !== data.revision) {
        const delta = Object.fromEntries(Object.keys(data.counts).map(k => [k, data.counts[k] - (before.counts[k] || 0)]).filter(([, v]) => v !== 0));
        setChanges(c => [{ at: data.sampled_at, revision: data.revision, delta, note: Object.keys(delta).length ? 'Count change observed' : 'Record content or derived values changed without a count change' }, ...c].slice(0, 100));
      }
      previousLive.current = data; setLive(data); setLiveError('');
    } catch (e) { if (mounted.current) setLiveError(e.message); }
    finally { loading.current = false; }
  }, [offset]);

  useEffect(() => {
    mounted.current = true;
    async function boot() {
      if (!apiClient.getToken()) return;
      try {
        const [ref, history, baseline] = await Promise.all([observatoryRequest('/api/observatory/reference'), observatoryRequest('/api/observatory/runs'), observatoryRequest('/api/observatory/artifacts/core')]);
        if (!mounted.current) return;
        setError(''); setReference(ref); setRuns(history); setRun(baseline.data); setSource('Committed artifact · not measured in this session');
        if (history.length) {
          const latest = await observatoryRequest(`/api/observatory/runs/${history[0].id}`);
          if (mounted.current) { setRun(latest.data); setSource(`Saved isolated run #${latest.id}`); }
        }
      } catch (e) { if (mounted.current) setError(e.message); }
    }
    boot();
    return () => { mounted.current = false; };
  }, [apiStatus]);
  useEffect(() => {
    refreshLive();
    const timer = auto ? setInterval(refreshLive, 5000) : null;
    const visible = () => { if (auto) refreshLive(); };
    window.addEventListener('focus', visible);
    document.addEventListener('visibilitychange', visible);
    return () => { clearInterval(timer); window.removeEventListener('focus', visible); document.removeEventListener('visibilitychange', visible); };
  }, [auto, refreshLive]);

  async function execute() {
    setBusy(true); setError('');
    try {
      const measured = await observatoryRequest('/api/observatory/runs', true);
      setPrevious(run); setRun(measured.data); setSource(`Measured isolated run #${measured.id}`);
      setRuns(await observatoryRequest('/api/observatory/runs'));
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }
  async function chooseRun(id) {
    try { const r = await observatoryRequest(`/api/observatory/runs/${id}`); setPrevious(run); setRun(r.data); setSource(`Saved isolated run #${r.id}`); }
    catch (e) { setError(e.message); }
  }
  const scores = live?.scores || [];
  const selectedScore = scores.find(s => s.memory_id === scoreId) || scores[0];
  const outcome = run?.results?.[mode];
  const calculation = run?.calculations?.[mode];

  return <div className="observatory">
    <header className="ro-header"><div><div className="ro-eyebrow"><FlaskConical size={14} /> SECONDBRAIN / RESEARCH WORKSPACE</div><h1>From memory to measurement.</h1><p>Inspect the evidence. Recompute the numbers. Track what actually changes.</p></div><div className="ro-header-actions"><Link to="/memory-lab">Pipeline controls <ArrowUpRight size={14} /></Link><button onClick={() => download(tab === 'live' ? live : run, 'secondbrain-research.json')} disabled={tab === 'live' ? !live : !run}><ArrowDownToLine size={15} /> Export JSON</button></div></header>
    <div className="ro-tabs"><button className={tab === 'benchmark' ? 'selected' : ''} onClick={() => setTab('benchmark')}><FlaskConical size={16} /> IEEE benchmark</button><button className={tab === 'live' ? 'selected' : ''} onClick={() => setTab('live')}><Activity size={16} /> Live calculations</button><button className={tab === 'artifacts' ? 'selected' : ''} onClick={() => setTab('artifacts')}><Calculator size={16} /> All research artifacts</button><span className="ro-chip">Evidence, not a target-chasing dashboard</span></div>
    {error && <div className="ro-error" role="alert">{error}</div>}

    {tab === 'benchmark' && <>
      <div className="ro-runbar"><div><span className="ro-dot" /> {source || 'Loading recorded data…'}<small>Core corpus · k = 5 · 15 synthetic memories · 11 queries / 9 answerable</small></div><button className="ro-primary" onClick={execute} disabled={busy}>{busy ? <RefreshCw size={15} className="ro-spin" /> : <Play size={15} />}{busy ? 'Running in isolated process…' : 'Run core experiment'}</button></div>
      {busy && <div className="ro-notice">Runs all five retrieval configurations on a fresh temporary database. This can take several minutes. No fabricated progress percentage; live notes and derived state are not reset. Closing this page does not cancel the server request.</div>}
      <div className="ro-kpis">{[['Answerable', outcome?.answerable_questions, 'MRR & Hit@5 denominator'], ['All queries', outcome?.questions, 'Stale@1 denominator'], ['Measured MRR', fmt(outcome?.mrr), MODE[mode]], ['Measured stale@1', fmt(outcome?.stale_top1_rate), 'Lower is better; not accuracy']].map(([label, value, hint]) => <div className="ro-kpi" key={label}><span>{label}</span><strong>{value ?? '—'}</strong><small>{hint}</small></div>)}</div>
      <Panel title="Measured results × paper reference" subtitle="Each cell: measured / paper target (Δ). Targets are never substituted for results. A mismatch is a finding, not something to hide.">
        <div className="ro-table-wrap"><table className="ro-comparison"><thead><tr><th>Retrieval system</th>{METRICS.slice(0, 5).map(k => <th key={k}>{LABELS[k]}</th>)}</tr></thead><tbody>{Object.entries(run?.results || {}).map(([name, result]) => <tr key={name} className={name === mode ? 'selected-row' : ''} onClick={() => setMode(name)}><td><button className="ro-text-button" onClick={() => setMode(name)}>{MODE[name] || name}</button></td>{METRICS.slice(0, 5).map(key => { const target = reference?.targets?.[name]?.[key]; return <td key={key}><strong>{fmt(result[key], 3)}</strong><small>paper {fmt(target, 3)} · Δ {typeof target === 'number' ? signed(result[key] - target) : '—'}</small></td>; })}</tr>)}</tbody></table></div>
        <div className="ro-tools"><label>Inspect mode <select value={mode} onChange={e => setMode(e.target.value)}>{Object.entries(MODE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label><label>Load saved run <select value="" onChange={e => e.target.value && chooseRun(e.target.value)}><option value="">Select a completed run…</option>{runs.map(r => <option key={r.id} value={r.id}>#{r.id} · {String(r.created_at)} · {r.duration_ms} ms</option>)}</select></label></div>
      </Panel>
      <Panel title="Calculation ledger" subtitle="Numerators, denominators and substitutions reconstructed from the per-query records. Undefined or missing inputs stay blank—not zero.">
        <div className="ro-table-wrap"><table><thead><tr><th>Metric / definition</th><th>Calculation</th><th>Recomputed</th><th>Reported</th><th>Reconciliation</th></tr></thead><tbody>{METRICS.map(key => { const c = calculation?.[key]; return <tr key={key}><td><b>{LABELS[key]}</b><small>{reference?.metric_definitions?.[key]}</small></td><td className="ro-mono">{c?.denominator !== undefined ? `${fmt(c.numerator, 6)} / ${c.denominator}` : 'Raw inputs missing'}</td><td>{fmt(c?.value, 6)}</td><td>{fmt(outcome?.[key], 6)}</td><td><span className={`ro-badge ${c?.matches_reported === false ? 'warning' : ''}`}>{c?.matches_reported === null || !c ? 'Unavailable' : c.matches_reported ? 'Within rounding' : 'Mismatch'}</span></td></tr>; })}</tbody></table></div><Json value={calculation} label="Exact summation terms and metric formulas" />
      </Panel>
      {previous && <Panel title="Change from previously displayed run" subtitle="Measured-to-measured difference, separate from paper targets."><div className="ro-table-wrap"><table><thead><tr><th>System</th>{METRICS.slice(0, 5).map(k => <th key={k}>Δ {LABELS[k]}</th>)}</tr></thead><tbody>{Object.entries(run?.results || {}).map(([name, r]) => <tr key={name}><td>{MODE[name]}</td>{METRICS.slice(0, 5).map(k => <td key={k}>{typeof previous.results?.[name]?.[k] === 'number' ? signed(r[k] - previous.results[name][k]) : '—'}</td>)}</tr>)}</tbody></table></div></Panel>}
      <Panel title="Query-by-query evidence" subtitle="Open a question to inspect gold labels, forbidden keys, retrieved ranks, reciprocal rank and the real pipeline calculation trace.">
        {(outcome?.per_question || []).map(q => <details className="ro-question" key={q.id}><summary><span className="ro-badge">{q.type}</span><b>{q.question}</b><span>{q.answerable ? `rank ${q.rank || 'miss'} · RR ${fmt(q.reciprocal_rank, 3)}` : 'No gold · excluded from MRR'}{q.top1_is_stale ? ' · forbidden @1' : ''}</span></summary><div className="ro-question-body"><p className="ro-mono">RR = {q.answerable ? q.rank > 0 ? `1 / ${q.rank} = ${fmt(1 / q.rank, 6)}` : '0 (no gold retrieved)' : 'not included (no gold labels)'}</p><div className="ro-label-pair"><span>Gold: {(q.gold_keys || []).join(', ') || 'See historical corpus definition'}</span><span>Forbidden: {(q.forbidden_keys || []).join(', ') || 'See historical corpus definition'}</span></div><div className="ro-table-wrap"><table><thead><tr><th>Rank</th><th>Memory key</th><th>Returned score</th><th>Gold</th><th>Forbidden</th><th>Forgotten</th></tr></thead><tbody>{(q.ranking || (q.retrieved || []).map((key, i) => ({ key, rank: i + 1 }))).map(r => <tr key={r.rank}><td>{r.rank}</td><td>{r.key}</td><td>{fmt(r.score, 6)}</td><td>{r.gold === undefined ? '—' : String(r.gold)}</td><td>{r.forbidden === undefined ? '—' : String(r.forbidden)}</td><td>{r.forgotten === undefined ? '—' : String(r.forgotten)}</td></tr>)}</tbody></table></div>{q.pipeline_trace?.candidate_calculations && <div className="ro-table-wrap"><h3>Adaptive candidate arithmetic (before final top-k)</h3><table><thead><tr><th>Memory</th><th>Prior</th><th>Temporal × conflict</th><th>Importance factor</th><th>Product</th><th>Kept after dedup</th></tr></thead><tbody>{q.pipeline_trace.candidate_calculations.map(c => <tr key={c.memory_id}><td>#{c.memory_id}</td><td>1 / {c.input_rank} = {fmt(c.prior)}</td><td>{fmt(c.temporal_factor_applied)} × {fmt(c.conflict_factor)}</td><td>{fmt(c.importance_factor)}</td><td>{fmt(c.adjusted_score, 6)}</td><td>{String(c.kept_after_dedup)}</td></tr>)}</tbody></table></div>}<Json value={q} label="Full question calculation and pipeline trace" /></div></details>)}
      </Panel>
      <Panel title="Reproducibility & interpretation" subtitle="An environment mismatch can change results. Matching a rounded number is not proof of matching an experiment."><Json value={run?.provenance || run?.configuration} label="Model availability, configuration and provenance" /><Json value={run?.graph} label="Graph construction measurements" /><ul className="ro-caveats">{(reference?.caveats || []).map(c => <li key={c}>{c}</li>)}</ul><Json value={run} label="Every recorded value in this run" /></Panel>
    </>}

    {tab === 'live' && <>
      <div className="ro-runbar"><div><span className="ro-dot" /> {liveError ? 'Disconnected · showing last successful sample' : live ? `Observed ${new Date(live.sampled_at).toLocaleTimeString()}` : 'Connecting…'}<small>Read-only polling every 5 seconds while visible · revision {live?.revision || '—'}</small></div><div className="ro-tools"><label><input type="checkbox" checked={auto} onChange={e => setAuto(e.target.checked)} /> Auto refresh</label><button onClick={refreshLive}><RefreshCw size={14} /> Refresh</button></div></div>
      {liveError && <div className="ro-error">{liveError}</div>}
      <div className="ro-notice">No live accuracy is invented. MRR, Hit@5 and leakage require labelled evaluation queries. These are operational counts and actual scoring calculations. {live?.freshness_note}</div>
      <div className="ro-counts">{Object.entries(live?.counts || {}).map(([key, value]) => <div className="ro-kpi" key={key}><span>{key.replaceAll('_', ' ')}</span><strong>{value}</strong></div>)}</div>
      <LiveProbe revision={live?.revision} />
      <div className="ro-two-col"><Panel title="Memory importance, fully expanded" subtitle={`${live?.score_count || 0} active memories · displayed in pages of 50. Not a retrieval score.`}><div className="ro-tools"><select aria-label="Memory calculation" value={selectedScore?.memory_id || ''} onChange={e => setScoreId(Number(e.target.value))}>{scores.map(s => <option value={s.memory_id} key={s.memory_id}>#{s.memory_id} · {s.title}</option>)}</select></div><div className="ro-equation">{live?.score_equation}<br /><b>M = min(1.5, max(0, S))</b></div>{selectedScore ? <><div className="ro-table-wrap"><table><thead><tr><th>Component</th><th>Value</th><th>Weight</th><th>Contribution</th></tr></thead><tbody>{selectedScore.terms.map(t => <tr key={t.name}><td><b>{t.name}</b><details><summary>Definition</summary><p>{t.formula}</p></details></td><td>{fmt(t.input, 6)}</td><td>{signed(t.weight)}</td><td>{fmt(t.contribution, 6)}</td></tr>)}</tbody></table></div><div className="ro-total">Σ contributions = {fmt(selectedScore.raw_sum, 6)}<br />Clipped score = <b>{fmt(selectedScore.total, 6)}</b></div><p className="ro-muted">Age {fmt(selectedScore.age_days, 4)} days → 2^(−age/45). Stored score {fmt(selectedScore.persisted_total, 6)} · recalculation Δ {signed(selectedScore.persisted_delta)}. Last stored {selectedScore.persisted_at || 'never'}.</p><Json value={selectedScore} label="Exact per-memory inputs and timestamps" /></> : <p className="ro-empty">Add a memory in Knowledge to see real calculations here.</p>}<div className="ro-tools"><button disabled={!offset} onClick={() => setOffset(o => Math.max(0, o - 50))}>Previous 50</button><span>{offset + 1}–{Math.min(offset + 50, live?.score_count || 0)}</span><button disabled={offset + 50 >= (live?.score_count || 0)} onClick={() => setOffset(o => o + 50)}>Next 50</button></div></Panel>
      <Panel title="Observed state changes" subtitle="Session-only sampled history, not a durable per-operation event log. Changes between samples can be combined.">{changes.length ? changes.slice(0, 20).map((c, i) => <div className="ro-change" key={`${c.revision}-${i}`}><time>{new Date(c.at).toLocaleTimeString()}</time><p>{c.note}</p>{Object.entries(c.delta).map(([k, v]) => <span className="ro-badge" key={k}>{k}: {v > 0 ? '+' : ''}{v}</span>)}</div>) : <p className="ro-empty">Waiting for a database change. Add/edit a memory, run extraction, consolidate or forget a record using the project controls.</p>}<button disabled={!changes.length} onClick={() => download(changes, 'observed-state-changes.json')}>Export sampled history</button><div className="ro-notice">Scoring is recalculated from the full active corpus on each sample. Recency changes with the clock even if the database revision does not change.</div></Panel></div>
      <Panel title="Graph & corpus calculations"><div className="ro-equation">Mean stored graph degree = 2E / N = {live?.graph_mean_degree?.numerator ?? '—'} / {live?.graph_mean_degree?.denominator ?? '—'} = {fmt(live?.graph_mean_degree?.value)}<br />Mean current importance = {fmt(live?.mean_importance?.numerator, 6)} / {live?.mean_importance?.denominator ?? '—'} = {fmt(live?.mean_importance?.value, 6)}</div><p className="ro-muted">Graph totals include all stored node/edge types. Derived data may lag ingestion. Stored rows are not a measure of correctness.</p></Panel>
      <Panel title="Temporal validity intervals" subtitle="[valid_from, valid_to). Source-active flags expose rows that outlive their source."><div className="ro-table-wrap"><table><thead><tr><th>Fact / source</th><th>Subject → predicate → object</th><th>Valid from</th><th>Valid to</th><th>Superseded by</th><th>Source active</th></tr></thead><tbody>{(live?.temporal || []).map(f => <tr key={f.id}><td>#{f.id} / #{f.source_memory_id}</td><td>{f.subject} → {f.predicate} → {f.object}</td><td>{f.valid_from}</td><td>{f.valid_to || 'Open'}</td><td>{f.superseded_by || '—'}</td><td>{String(f.source_active)}</td></tr>)}</tbody></table></div></Panel>
      <Panel title="Conflict damping" subtitle="A factor is only applied when the retrieval pipeline's conditions select that conflict. Inspect benchmark traces for the applied product."><div className="ro-table-wrap"><table><thead><tr><th>Memory pair</th><th>Detector / type</th><th>Severity</th><th>Substitution</th><th>Factor</th><th>Resolution</th></tr></thead><tbody>{(live?.conflicts || []).map(c => <tr key={c.id}><td>#{c.older} ↔ #{c.newer}</td><td>{c.method} / {c.type}</td><td>{fmt(c.severity)}</td><td>{c.substitution}</td><td>{fmt(c.damping_factor)}</td><td>{c.resolution} · {c.resolved ? 'resolved' : 'open'}</td></tr>)}</tbody></table></div></Panel>
      <Panel title="Consolidation savings & knowledge-gap arithmetic" subtitle="These use stored pipeline results; observing them does not silently run consolidation or claim validated knowledge gaps."><h3>Recorded consolidation groups</h3><Json value={live?.consolidations || []} label="Member IDs, thresholds, before/after counts and reduction fractions" /><h3>Gap = exposure × (1−depth) × (1−0.5×connectivity)</h3><div className="ro-table-wrap"><table><thead><tr><th>Concept</th><th>Mentions / exposure</th><th>Depth</th><th>Connectivity</th><th>Recomputed</th><th>Stored</th></tr></thead><tbody>{(live?.gaps || []).map(g => <tr key={g.concept}><td>{g.concept}</td><td>{g.mentions} / {fmt(g.exposure)}</td><td>{fmt(g.depth)}</td><td>{fmt(g.connectivity)}</td><td>{fmt(g.recomputed_from_stored_inputs, 6)}</td><td>{fmt(g.stored_gap, 6)}</td></tr>)}</tbody></table></div><Json value={live} label="Complete live calculation snapshot" /></Panel>
    </>}

    {tab === 'artifacts' && <Panel title="All recorded research numbers" subtitle="Core, personas, ablations, scaling, statistics and conflict diagnostics. Historical artifacts are clearly labelled; they are not silently treated as fresh runs."><div className="ro-tools"><select value={artifactName} onChange={e => setArtifactName(e.target.value)} aria-label="Research artifact">{Object.keys(reference?.artifacts || {}).map(k => <option key={k} value={k}>{k.replaceAll('_', ' ')}</option>)}</select><button onClick={async () => { setError(''); try { setArtifact(await observatoryRequest(`/api/observatory/artifacts/${artifactName}`)); } catch (e) { setError(e.message); } }}>Inspect artifact</button>{artifact && <button onClick={() => download(artifact, artifact.file)}>Export artifact</button>}</div>{artifact ? <><div className="ro-notice">{artifact.file} · {artifact.warning}</div><NumericExplorer key={artifact.file} value={artifact.data} /></> : <p className="ro-empty">Choose an artifact. Every stored numeric value is available by exact JSON path, with the complete raw data below.</p>}</Panel>}
    <footer className="ro-footer">RESEARCH OBSERVATORY · Retrieval outcomes ≠ generated-answer accuracy · Reference: IEEE manuscript, not a guarantee</footer>
  </div>;
}
