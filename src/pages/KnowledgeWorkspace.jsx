import { useCallback, useEffect, useState } from 'react';
import PageHeader from '../components/PageHeader.jsx';
import { apiClient, apiFetch } from '../services/apiClient.js';

export default function KnowledgeWorkspace() {
  const [memories, setMemories] = useState([]);
  const [query, setQuery] = useState('');
  const [source, setSource] = useState('');
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const params = new URLSearchParams({ limit: '100' });
      if (query) params.set('q', query);
      if (source) params.set('source_type', source);
      const res = await apiFetch(`${apiClient.baseUrl}/api/memory/search?${params}`);
      if (res?.ok) setMemories(await res.json());
      setError('');
    } catch (exc) {
      setError(String(exc?.message || exc));
    }
  }, [query, source]);

  useEffect(() => {
    const timer = setTimeout(load, 250);
    return () => clearTimeout(timer);
  }, [load]);

  return (
    <div className="flex flex-col gap-6 p-6">
      <PageHeader
        eyebrow="Knowledge store"
        title="Memories"
        description="Every captured memory - screen OCR, mail, web and social ingestion - searchable across the personal knowledge store."
      />

      <div className="flex flex-wrap items-center gap-3">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search memories..."
          className="min-w-[220px] flex-1 rounded-lg border border-white/10 bg-black/40 px-4 py-2 text-sm text-slate-200 outline-none focus:border-cyan-400/50"
        />
        <select
          value={source}
          onChange={(event) => setSource(event.target.value)}
          className="rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-slate-200 outline-none focus:border-cyan-400/50"
        >
          <option value="">All sources</option>
          <option value="screen">Screen OCR</option>
          <option value="mail">Mail</option>
          <option value="social">Web / social</option>
          <option value="browser">Browser</option>
          <option value="code">Code</option>
          <option value="document">Document</option>
        </select>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-4 py-2 text-sm text-rose-300">
          {error}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[1fr_380px]">
        <ul className="flex flex-col gap-2">
          {memories.map((memory) => (
            <li key={memory.id}>
              <button
                type="button"
                onClick={() => setSelected(memory)}
                className={`w-full rounded-lg border px-4 py-3 text-left text-sm transition ${
                  selected?.id === memory.id
                    ? 'border-cyan-400/50 bg-cyan-500/10'
                    : 'border-white/10 bg-white/5 hover:border-cyan-400/30'
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="truncate font-medium text-slate-100">
                    {memory.title || 'Untitled memory'}
                  </span>
                  <span className="shrink-0 font-mono text-[10px] uppercase text-slate-500">
                    {memory.source_type}
                  </span>
                </div>
                <p className="mt-1 line-clamp-2 text-xs text-slate-400">
                  {(memory.content || '').slice(0, 220)}
                </p>
              </button>
            </li>
          ))}
          {memories.length === 0 && (
            <li className="rounded-lg border border-white/10 bg-white/5 px-4 py-6 text-sm text-slate-400">
              No memories match the current filter.
            </li>
          )}
        </ul>

        <aside className="glass-panel h-fit rounded-xl p-5">
          <h2 className="mb-3 font-mono text-sm font-bold uppercase tracking-wider text-cyan-300">
            Detail
          </h2>
          {!selected ? (
            <p className="text-sm text-slate-400">Select a memory to inspect it.</p>
          ) : (
            <div className="flex flex-col gap-3 text-sm">
              <p className="font-medium text-slate-100">{selected.title}</p>
              <p className="whitespace-pre-wrap text-slate-300">{selected.content}</p>
              <dl className="grid grid-cols-2 gap-2 font-mono text-[11px] text-slate-500">
                <div>source: {selected.source_type}</div>
                <div>app: {selected.app_source || '—'}</div>
                <div>topic: {selected.topic_label || '—'}</div>
                <div>created: {(selected.created_at || '').slice(0, 10)}</div>
              </dl>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
