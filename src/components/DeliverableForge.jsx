import { useEffect, useState } from 'react';
import { BookOpen, Copy, Check, Download, FileText, Layers, RefreshCw, Sparkles, Terminal, Wrench } from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';

export default function DeliverableForge() {
  const { apiClient } = useBackend();
  const [deliverableType, setDeliverableType] = useState('research_paper');
  const [topic, setTopic] = useState('Autonomous Multi-Agent Cognitive Architectures');
  const [instructions, setInstructions] = useState('');
  const [isForging, setIsForging] = useState(false);
  const [deliverables, setDeliverables] = useState([]);
  const [activeDoc, setActiveDoc] = useState(null);
  const [copied, setCopied] = useState(false);

  async function loadDeliverables() {
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/graph/deliverables`);
      if (res.ok) {
        const data = await res.json();
        setDeliverables(data);
      }
    } catch (e) {
      console.warn('Could not list deliverables:', e);
    }
  }

  useEffect(() => {
    loadDeliverables();
  }, []);

  async function forgeDeliverable() {
    if (!topic.trim()) return;
    setIsForging(true);
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/graph/deliverables/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deliverable_type: deliverableType,
          topic: topic.trim(),
          user_instructions: instructions.trim()
        })
      });
      if (res.ok) {
        const result = await res.json();
        setActiveDoc(result);
        await loadDeliverables();
      }
    } catch (e) {
      console.error('Failed to forge deliverable:', e);
    } finally {
      setIsForging(false);
    }
  }

  async function openExistingDoc(item) {
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/graph/deliverables/content?filename=${encodeURIComponent(item.filename)}`);
      if (res.ok) {
        const data = await res.json();
        setActiveDoc({ ...item, content: data.content });
      }
    } catch (e) {
      console.error('Could not fetch deliverable content:', e);
    }
  }

  function copyDoc() {
    if (!activeDoc?.content) return;
    navigator.clipboard.writeText(activeDoc.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function downloadDoc() {
    if (!activeDoc?.content) return;
    const blob = new Blob([activeDoc.content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = activeDoc.filename || `${activeDoc.topic}.md`;
    link.click();
    URL.revokeObjectURL(url);
  }

  const types = [
    { id: 'research_paper', label: 'Academic Literature Review', icon: BookOpen, desc: 'Complete paper with abstract, methodology & citations' },
    { id: 'cheatsheet', label: 'Exam & Concept Cheatsheet', icon: FileText, desc: 'High-yield definitions, formulas & 10s recall list' },
    { id: 'architecture_spec', label: 'System Architecture Spec', icon: Terminal, desc: 'Component specs, invariants & ASCII diagrams' },
    { id: 'executive_summary', label: 'Strategic Intel Briefing', icon: Sparkles, desc: 'Bottom-line insights & actionable implications' }
  ];

  return (
    <section className="glass-panel rounded-2xl p-6">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-mintGlow/30 bg-mintGlow/10 text-mintGlow">
            <Wrench size={19} />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-100">1-Click Deliverable Forge</h3>
            <p className="text-xs text-slate-400">Transform raw browsing and captured knowledge into publication-ready documents.</p>
          </div>
        </div>
        <span className="rounded-full border border-mintGlow/20 bg-mintGlow/10 px-3 py-1 text-[11px] font-semibold text-mintGlow">
          Powered by Local Qwen 2.5
        </span>
      </div>

      {/* Type Selection */}
      <div className="mb-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {types.map((t) => {
          const Icon = t.icon;
          const isSelected = deliverableType === t.id;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setDeliverableType(t.id)}
              className={`flex flex-col items-start rounded-xl border p-3.5 text-left transition ${
                isSelected
                  ? 'border-cyanGlow/50 bg-cyanGlow/10 shadow-glow'
                  : 'border-white/10 bg-slate-950/40 hover:border-white/20 hover:bg-white/5'
              }`}
            >
              <div className="mb-2 flex items-center gap-2">
                <Icon size={16} className={isSelected ? 'text-cyanGlow' : 'text-slate-400'} />
                <span className={`text-xs font-bold ${isSelected ? 'text-white' : 'text-slate-300'}`}>{t.label}</span>
              </div>
              <p className="text-[11px] text-slate-500 leading-snug">{t.desc}</p>
            </button>
          );
        })}
      </div>

      {/* Input Controls */}
      <div className="mb-6 space-y-3 rounded-xl border border-white/5 bg-slate-950/60 p-4">
        <div>
          <label className="text-xs font-semibold text-slate-400">Target Topic or Focus Domain:</label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. Quantum Computing, React Internal Fiber Architecture, Semi-conductor Geopolitics..."
            className="mt-1.5 w-full rounded-lg border border-white/10 bg-black/50 px-3.5 py-2 text-sm text-slate-100 outline-none focus:border-cyanGlow"
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-400">Custom Directives / Specific Requirements (Optional):</label>
          <input
            type="text"
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="e.g. Focus on IEEE evaluation metrics, include Python code snippets, compare against prior art..."
            className="mt-1.5 w-full rounded-lg border border-white/10 bg-black/50 px-3.5 py-2 text-xs text-slate-300 outline-none focus:border-cyanGlow"
          />
        </div>

        <div className="flex justify-end pt-1">
          <button
            type="button"
            onClick={forgeDeliverable}
            disabled={isForging || !topic.trim()}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyanGlow to-mintGlow px-5 py-2.5 text-xs font-bold text-slate-950 shadow-glow transition hover:opacity-90 disabled:opacity-40"
          >
            {isForging ? <RefreshCw size={14} className="animate-spin" /> : <Sparkles size={14} />}
            {isForging ? 'Synthesizing Full Document (30s)...' : 'Forge Publication-Ready Document'}
          </button>
        </div>
      </div>

      {/* Forged Deliverables Grid */}
      {deliverables.length > 0 && (
        <div>
          <div className="mb-3 flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-400">
            <span>Forged Deliverables Archive</span>
            <span className="font-mono text-cyanGlow">{deliverables.length} Documents</span>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {deliverables.map((doc, i) => (
              <div
                key={i}
                onClick={() => openExistingDoc(doc)}
                className="group flex cursor-pointer flex-col justify-between rounded-xl border border-white/10 bg-slate-950/40 p-4 transition hover:border-cyanGlow/40 hover:bg-slate-900/80"
              >
                <div>
                  <div className="mb-1.5 flex items-center justify-between text-[10px] text-slate-500">
                    <span className="font-bold uppercase text-cyanGlow">{doc.filename.split('_')[0]}</span>
                    <span>{doc.created_at}</span>
                  </div>
                  <h4 className="text-xs font-bold text-slate-200 group-hover:text-cyanGlow line-clamp-1">{doc.title}</h4>
                  <p className="mt-1 text-[11px] leading-relaxed text-slate-400 line-clamp-2">{doc.preview}</p>
                </div>
                <div className="mt-3 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                  <span>{doc.word_count} words</span>
                  <span className="text-cyanGlow group-hover:underline">Open Reader &rarr;</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Document Reader Modal */}
      {activeDoc && (
        <div
          onClick={() => setActiveDoc(null)}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-6 backdrop-blur-xl"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="thin-scrollbar relative flex max-h-[90vh] w-full max-w-4xl flex-col rounded-2xl border border-white/20 bg-slate-950 p-6 shadow-2xl"
          >
            <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3">
              <div>
                <span className="rounded bg-cyanGlow/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-cyanGlow">
                  Forged Document · {activeDoc.word_count} Words
                </span>
                <h3 className="mt-1 text-lg font-bold text-slate-100">{activeDoc.title}</h3>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={copyDoc}
                  className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold text-slate-300 transition hover:bg-white/10"
                >
                  {copied ? <Check size={13} className="text-mintGlow" /> : <Copy size={13} />}
                  {copied ? 'Copied' : 'Copy'}
                </button>
                <button
                  type="button"
                  onClick={downloadDoc}
                  className="flex items-center gap-1.5 rounded-lg border border-cyanGlow/30 bg-cyanGlow/15 px-3 py-1.5 text-xs font-bold text-cyanGlow transition hover:bg-cyanGlow/25"
                >
                  <Download size={13} />
                  Download .md
                </button>
                <button
                  type="button"
                  onClick={() => setActiveDoc(null)}
                  className="rounded-lg bg-white/10 px-3 py-1.5 text-xs font-bold text-slate-300 hover:bg-white/20"
                >
                  Close
                </button>
              </div>
            </div>

            <div className="thin-scrollbar flex-1 overflow-y-auto rounded-xl border border-white/5 bg-black/50 p-5 font-mono text-xs leading-relaxed text-slate-200 whitespace-pre-wrap">
              {activeDoc.content}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
