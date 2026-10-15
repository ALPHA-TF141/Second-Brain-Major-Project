import { useCallback, useEffect, useState } from 'react';
import PageHeader from '../components/PageHeader.jsx';
import { apiClient, apiFetch } from '../services/apiClient.js';

const EMPTY_FORM = { content: '', title: '', topic_label: '', tags: '' };

// Turn a FastAPI error body into a readable message.
async function errorMessage(res, fallback) {
  try {
    const body = await res.json();
    if (typeof body?.detail === 'string') return body.detail;
    if (Array.isArray(body?.detail)) return body.detail.map((d) => d.msg).join('; ');
  } catch {
    // body was not JSON
  }
  return `${fallback} (HTTP ${res.status})`;
}

function parseTags(text) {
  return text.split(',').map((t) => t.trim()).filter(Boolean);
}

export default function KnowledgeWorkspace() {
  const [memories, setMemories] = useState([]);
  const [query, setQuery] = useState('');
  const [source, setSource] = useState('');
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [loading, setLoading] = useState(false);

  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState(EMPTY_FORM);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit: '100' });
      if (query) params.set('q', query);
      if (source) params.set('source_type', source);
      const res = await apiFetch(`${apiClient.baseUrl}/api/memory/search?${params}`);
      if (!res.ok) throw new Error(await errorMessage(res, 'Could not load memories'));
      setMemories(await res.json());
      setError('');
    } catch (exc) {
      setError(String(exc?.message || exc));
    } finally {
      setLoading(false);
    }
  }, [query, source]);

  useEffect(() => {
    const timer = setTimeout(load, 250);
    return () => clearTimeout(timer);
  }, [load]);

  function select(memory) {
    setSelected(memory);
    setEditing(false);
    setNotice('');
  }

  async function createMemory(event) {
    event.preventDefault();
    if (!form.content.trim()) {
      setError('A memory needs some content.');
      return;
    }
    setBusy(true);
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/memory/memories`, {
        method: 'POST',
        body: JSON.stringify({
          content: form.content,
          title: form.title.trim() || undefined,
          topic_label: form.topic_label.trim() || undefined,
          tags: parseTags(form.tags),
        }),
      });
      if (!res.ok) throw new Error(await errorMessage(res, 'Could not save the memory'));
      const created = await res.json();
      setForm(EMPTY_FORM);
      setCreating(false);
      setNotice('Memory saved.');
      setError('');
      setSelected(created);
      await load();
    } catch (exc) {
      setError(String(exc?.message || exc));
    } finally {
      setBusy(false);
    }
  }

  function startEdit() {
    setEditForm({
      content: selected.content || '',
      title: selected.title || '',
      topic_label: selected.topic_label || '',
      tags: (selected.tags || []).join(', '),
    });
    setEditing(true);
    setNotice('');
  }

  async function saveEdit(event) {
    event.preventDefault();
    if (!editForm.content.trim()) {
      setError('Content cannot be empty.');
      return;
    }
    setBusy(true);
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/memory/memories/${selected.id}`, {
        method: 'PUT',
        body: JSON.stringify({
          content: editForm.content,
          title: editForm.title.trim() || undefined,
          topic_label: editForm.topic_label.trim() || undefined,
          tags: parseTags(editForm.tags),
        }),
      });
      if (!res.ok) throw new Error(await errorMessage(res, 'Could not update the memory'));
      const updated = await res.json();
      setSelected(updated);
      setEditing(false);
      setNotice('Changes saved.');
      setError('');
      await load();
    } catch (exc) {
      setError(String(exc?.message || exc));
    } finally {
      setBusy(false);
    }
  }

  async function deleteMemory() {
    if (!selected) return;
    if (!window.confirm('Delete this memory? It will be removed from search, the graph and retrieval.')) return;
    setBusy(true);
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/memory/memories/${selected.id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error(await errorMessage(res, 'Could not delete the memory'));
      setSelected(null);
      setNotice('Memory deleted.');
      setError('');
      await load();
    } catch (exc) {
      setError(String(exc?.message || exc));
    } finally {
      setBusy(false);
    }
  }

  const fieldClass = 'w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-slate-200 outline-none focus:border-cyan-400/50';

  return (
    <div className="flex flex-col gap-6 p-6">
      <PageHeader
        eyebrow="Knowledge store"
        title="Memories"
        description="Every captured memory - screen OCR, mail, web and social ingestion, plus notes you write here - searchable across the personal knowledge store."
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
          <option value="manual">Written by me</option>
          <option value="screen">Screen OCR</option>
          <option value="mail">Mail</option>
          <option value="social">Web / social</option>
          <option value="browser">Browser</option>
          <option value="code">Code</option>
          <option value="document">Document</option>
        </select>
        <button
          type="button"
          onClick={() => { setCreating((v) => !v); setError(''); setNotice(''); }}
          className="rounded-lg border border-cyan-400/40 bg-cyan-500/10 px-4 py-2 text-sm text-cyan-200 hover:bg-cyan-500/20"
        >
          {creating ? 'Cancel' : 'New memory'}
        </button>
      </div>

      {error && (
        <div role="alert" className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-4 py-2 text-sm text-rose-300">
          {error}
        </div>
      )}
      {notice && !error && (
        <div role="status" className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-4 py-2 text-sm text-emerald-300">
          {notice}
        </div>
      )}

      {creating && (
        <form onSubmit={createMemory} className="glass-panel flex flex-col gap-3 rounded-xl p-5">
          <label className="flex flex-col gap-1 text-xs text-slate-400">
            Content *
            <textarea
              value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
              rows={4}
              maxLength={20000}
              className={fieldClass}
              placeholder="A fact, note or event to remember"
            />
          </label>
          <div className="grid gap-3 md:grid-cols-3">
            <label className="flex flex-col gap-1 text-xs text-slate-400">
              Title (optional)
              <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} maxLength={220} className={fieldClass} />
            </label>
            <label className="flex flex-col gap-1 text-xs text-slate-400">
              Topic (optional)
              <input value={form.topic_label} onChange={(e) => setForm({ ...form, topic_label: e.target.value })} maxLength={160} className={fieldClass} />
            </label>
            <label className="flex flex-col gap-1 text-xs text-slate-400">
              Tags (comma separated)
              <input value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} className={fieldClass} />
            </label>
          </div>
          <div className="flex justify-end">
            <button type="submit" disabled={busy} className="rounded-lg bg-cyan-500/20 px-4 py-2 text-sm text-cyan-100 hover:bg-cyan-500/30 disabled:opacity-50">
              {busy ? 'Saving…' : 'Save memory'}
            </button>
          </div>
        </form>
      )}

      <div className="grid gap-4 lg:grid-cols-[1fr_380px]">
        <ul className="flex flex-col gap-2">
          {loading && memories.length === 0 && (
            <li className="rounded-lg border border-white/10 bg-white/5 px-4 py-6 text-sm text-slate-400">Loading memories…</li>
          )}
          {memories.map((memory) => (
            <li key={memory.id}>
              <button
                type="button"
                onClick={() => select(memory)}
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
          {!loading && memories.length === 0 && (
            <li className="rounded-lg border border-white/10 bg-white/5 px-4 py-6 text-sm text-slate-400">
              {query || source ? 'No memories match the current filter.' : 'No memories yet. Use "New memory" to add one.'}
            </li>
          )}
        </ul>

        <aside className="glass-panel h-fit rounded-xl p-5">
          <h2 className="mb-3 font-mono text-sm font-bold uppercase tracking-wider text-cyan-300">
            Detail
          </h2>
          {!selected ? (
            <p className="text-sm text-slate-400">Select a memory to inspect it.</p>
          ) : editing ? (
            <form onSubmit={saveEdit} className="flex flex-col gap-3 text-sm">
              <textarea
                value={editForm.content}
                onChange={(e) => setEditForm({ ...editForm, content: e.target.value })}
                rows={6}
                maxLength={20000}
                className={fieldClass}
                aria-label="Memory content"
              />
              <input value={editForm.title} onChange={(e) => setEditForm({ ...editForm, title: e.target.value })} maxLength={220} className={fieldClass} aria-label="Title" />
              <input value={editForm.topic_label} onChange={(e) => setEditForm({ ...editForm, topic_label: e.target.value })} maxLength={160} className={fieldClass} aria-label="Topic" />
              <input value={editForm.tags} onChange={(e) => setEditForm({ ...editForm, tags: e.target.value })} className={fieldClass} aria-label="Tags" placeholder="tags, comma separated" />
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setEditing(false)} className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-slate-300">Cancel</button>
                <button type="submit" disabled={busy} className="rounded-lg bg-cyan-500/20 px-3 py-1.5 text-xs text-cyan-100 disabled:opacity-50">Save</button>
              </div>
            </form>
          ) : (
            <div className="flex flex-col gap-3 text-sm">
              <p className="font-medium text-slate-100">{selected.title}</p>
              <p className="whitespace-pre-wrap text-slate-300">{selected.content}</p>
              {selected.tags?.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {selected.tags.map((tag) => (
                    <span key={tag} className="rounded bg-white/5 px-2 py-0.5 font-mono text-[10px] text-slate-400">{tag}</span>
                  ))}
                </div>
              )}
              <dl className="grid grid-cols-2 gap-2 font-mono text-[11px] text-slate-500">
                <div>source: {selected.source_type}</div>
                <div>app: {selected.app_source || '—'}</div>
                <div>topic: {selected.topic_label || '—'}</div>
                <div>created: {(selected.created_at || '').slice(0, 10)}</div>
              </dl>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={startEdit} disabled={busy} className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-slate-200 hover:bg-white/5 disabled:opacity-50">Edit</button>
                <button type="button" onClick={deleteMemory} disabled={busy} className="rounded-lg border border-rose-500/40 px-3 py-1.5 text-xs text-rose-300 hover:bg-rose-500/10 disabled:opacity-50">Delete</button>
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
