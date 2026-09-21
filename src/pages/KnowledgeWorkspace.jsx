import { useEffect, useState } from 'react';
import { BookOpen, Layers, Network, Search, ExternalLink, Image as ImageIcon, Sparkles, Plus, FileText, ChevronRight } from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';
import { useNavigate } from 'react-router-dom';

export default function KnowledgeWorkspace() {
  const { apiClient } = useBackend();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('wiki'); // 'wiki' | 'cards' | 'tags'
  const [wikiArticles, setWikiArticles] = useState([]);
  const [vaultCards, setVaultCards] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const [search, setSearch] = useState('');

  async function loadKnowledge() {
    try {
      const [wRes, cRes] = await Promise.all([
        fetch(`${apiClient.baseUrl}/api/graph/vault/wiki`),
        fetch(`${apiClient.baseUrl}/api/graph/vault/cards?limit=25`)
      ]);
      if (wRes.ok) setWikiArticles(await wRes.json());
      if (cRes.ok) setVaultCards(await cRes.json());
    } catch {
      //
    }
  }

  useEffect(() => {
    loadKnowledge();
  }, []);

  async function openArticle(art) {
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/graph/vault/wiki/article?path=${encodeURIComponent(art.path)}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedDoc({ ...art, content: data.content });
      }
    } catch {
      //
    }
  }

  const filteredWiki = wikiArticles.filter(a => search ? a.title.toLowerCase().includes(search.toLowerCase()) || a.domain.toLowerCase().includes(search.toLowerCase()) : true);
  const filteredCards = vaultCards.filter(c => search ? (c.topic || c.window_title).toLowerCase().includes(search.toLowerCase()) : true);

  return (
    <div className="flex h-full w-full flex-col bg-[#111318] p-6 text-slate-100 font-sans select-none overflow-y-auto thin-scrollbar">
      <div className="mx-auto w-full max-w-6xl space-y-6">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <BookOpen size={18} className="text-cyan-400" />
              <h2 className="text-base font-bold text-white uppercase tracking-wider font-mono">Knowledge Base & Master Wiki</h2>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">Self-improving digital encyclopedia autonomously compiled from your browsing and research.</p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => navigate('/knowledge-graph')}
              className="flex items-center gap-1.5 rounded-xl border border-cyan-400/30 bg-cyan-500/15 px-3.5 py-1.5 text-xs font-bold text-cyan-300 shadow-glow hover:bg-cyan-500/25 transition"
            >
              <Network size={13} />
              Open Obsidian Graph View &rarr;
            </button>
          </div>
        </div>

        {/* Search & Mode Switcher */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="relative flex-1 max-w-md">
            <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search across all knowledge entries, topics, tags..."
              className="w-full rounded-xl border border-white/10 bg-[#161820] py-2 pl-9 pr-3 text-xs text-white outline-none focus:border-cyan-400"
            />
          </div>

          <div className="flex items-center gap-1 rounded-xl border border-white/10 bg-black/40 p-1">
            <button
              type="button"
              onClick={() => setActiveTab('wiki')}
              className={`rounded-lg px-3.5 py-1 text-xs font-bold transition ${activeTab === 'wiki' ? 'bg-cyan-400 text-slate-950 shadow-glow' : 'text-slate-400 hover:text-white'}`}
            >
              Master Wiki ({wikiArticles.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('cards')}
              className={`rounded-lg px-3.5 py-1 text-xs font-bold transition ${activeTab === 'cards' ? 'bg-cyan-400 text-slate-950 shadow-glow' : 'text-slate-400 hover:text-white'}`}
            >
              Curated Cards ({vaultCards.length})
            </button>
          </div>
        </div>

        {/* Tab 1: Master Wiki Articles */}
        {activeTab === 'wiki' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredWiki.map((art, idx) => (
              <div
                key={idx}
                onClick={() => openArticle(art)}
                className="group cursor-pointer rounded-2xl border border-white/10 bg-[#161820] p-5 flex flex-col justify-between hover:border-cyan-400/40 hover:bg-[#1a1e28] transition space-y-3"
              >
                <div>
                  <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono mb-1.5">
                    <span className="rounded bg-cyan-400/10 px-2 py-0.5 text-cyan-300 font-bold uppercase">{art.domain}</span>
                    <span>{art.updated_at}</span>
                  </div>
                  <h4 className="text-sm font-bold text-white group-hover:text-cyan-300 transition">{art.title}</h4>
                  <p className="mt-1.5 text-xs text-slate-400 line-clamp-3 leading-relaxed">{art.preview || 'Autonomous topic compilation.'}</p>
                </div>
                <div className="pt-2 border-t border-white/5 flex items-center justify-between text-xs text-cyan-400 font-medium">
                  <span>Read Synthesis</span>
                  <ChevronRight size={13} className="group-hover:translate-x-1 transition" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tab 2: Curated Knowledge Cards */}
        {activeTab === 'cards' && (
          <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredCards.map((card) => {
              const heroUrl = card.hero_image
                ? (card.hero_image.startsWith('http') ? card.hero_image : `${apiClient.baseUrl}/${card.hero_image.replace(/\\/g, '/')}`)
                : null;

              return (
                <div key={card.id} className="rounded-xl border border-white/10 bg-[#161820] p-4 flex flex-col justify-between space-y-2">
                  <div>
                    {heroUrl && (
                      <div
                        onClick={() => setSelectedImage(heroUrl)}
                        className="relative mb-2 h-28 w-full cursor-pointer overflow-hidden rounded-lg border border-white/10 bg-black"
                      >
                        <img src={heroUrl} alt={card.topic} className="h-full w-full object-cover" />
                      </div>
                    )}
                    <span className="rounded bg-white/10 px-2 py-0.5 text-[9px] font-bold text-cyan-300 uppercase">{card.domain}</span>
                    <h4 className="text-xs font-bold text-white line-clamp-1 mt-1">{card.topic || card.window_title}</h4>
                    <p className="text-[11px] text-slate-400 line-clamp-2 mt-0.5">{card.summary}</p>
                  </div>
                  <div className="border-t border-white/5 pt-1.5 text-[10px] text-slate-500 font-mono">
                    {card.app_source}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Reader Modal */}
      {selectedDoc && (
        <div
          onClick={() => setSelectedDoc(null)}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-6 backdrop-blur-xl"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="thin-scrollbar relative flex max-h-[88vh] w-full max-w-3xl flex-col rounded-2xl border border-white/20 bg-slate-950 p-6 shadow-2xl overflow-y-auto"
          >
            <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3">
              <div>
                <span className="rounded bg-cyan-400/10 px-2 py-0.5 text-[10px] font-bold uppercase text-cyan-300 font-mono">
                  {selectedDoc.domain} · Master Synthesis
                </span>
                <h3 className="text-lg font-bold text-white mt-1">{selectedDoc.title}</h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedDoc(null)}
                className="rounded-lg bg-white/10 px-3 py-1.5 text-xs font-bold text-slate-300 hover:bg-white/20"
              >
                Close
              </button>
            </div>
            <div className="prose prose-invert max-w-none text-xs leading-relaxed text-slate-200 whitespace-pre-wrap font-mono bg-black/50 p-5 rounded-xl border border-white/5">
              {selectedDoc.content}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
