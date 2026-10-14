import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import PageHeader from '../components/PageHeader.jsx';
import StatusCard from '../components/StatusCard.jsx';
import { apiClient, apiFetch } from '../services/apiClient.js';

export default function Dashboard() {
  const [overview, setOverview] = useState(null);
  const [recent, setRecent] = useState([]);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const [overviewRes, recentRes] = await Promise.all([
        apiFetch(`${apiClient.baseUrl}/api/research/overview`).catch(() => null),
        apiFetch(`${apiClient.baseUrl}/api/memory/search?limit=8`).catch(() => null),
      ]);
      if (overviewRes?.ok) setOverview(await overviewRes.json());
      if (recentRes?.ok) setRecent(await recentRes.json());
      setError('');
    } catch (exc) {
      setError(String(exc?.message || exc));
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="flex flex-col gap-6 p-6">
      <PageHeader
        eyebrow="Second Brain"
        title="Adaptive personal memory"
        description="Temporal personal knowledge graph with memory consolidation and contradiction-aware retrieval-augmented generation."
      />

      {error && (
        <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-4 py-2 text-sm text-rose-300">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatusCard
          title="Memories"
          value={overview?.memories_total ?? '—'}
          detail="stored in the personal knowledge store"
        />
        <StatusCard
          title="Temporal facts"
          value={overview?.temporal_facts ?? '—'}
          detail={`${overview?.open_facts ?? 0} open / ${overview?.superseded_facts ?? 0} superseded`}
          accent="mint"
        />
        <StatusCard
          title="Open conflicts"
          value={overview?.conflicts ?? '—'}
          detail="contradictions detected across memories"
          accent="amber"
        />
        <StatusCard
          title="Forgotten / gaps"
          value={`${overview?.forgotten ?? 0} / ${overview?.gaps ?? 0}`}
          detail="retrieval-enforced forgetting and knowledge gaps"
        />
      </div>

      <section className="glass-panel rounded-xl p-5">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-mono text-sm font-bold uppercase tracking-wider text-cyan-300">
            Research layer
          </h2>
          <Link to="/memory-lab" className="text-xs text-cyan-400 hover:underline">
            Open Memory Lab &rarr;
          </Link>
        </div>
        <p className="text-sm leading-6 text-slate-400">
          Adaptive memory scoring, temporal knowledge graph, contradiction-aware hybrid
          retrieval, memory consolidation, knowledge-gap detection, retrieval-enforced
          forgetting and PersonalBrain-Bench - additive and individually switchable.
          The Memory Lab demonstrates each mechanism and runs the benchmark.
        </p>
      </section>

      <section className="glass-panel rounded-xl p-5">
        <h2 className="mb-3 font-mono text-sm font-bold uppercase tracking-wider text-cyan-300">
          Recent memories
        </h2>
        {recent.length === 0 ? (
          <p className="text-sm text-slate-400">
            No memories yet. Start a capture session, connect Gmail, or ingest a web page
            from the Integrations workspace.
          </p>
        ) : (
          <ul className="flex flex-col gap-2">
            {recent.map((memory) => (
              <li
                key={memory.id}
                className="flex items-center justify-between rounded-lg border border-white/5 bg-black/30 px-3 py-2 text-sm"
              >
                <span className="truncate text-slate-200">
                  {memory.title || (memory.content || '').slice(0, 80)}
                </span>
                <span className="ml-3 shrink-0 font-mono text-[10px] uppercase text-slate-500">
                  {memory.source_type}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
