import { useEffect, useState } from 'react';
import { BookOpen, ExternalLink, Image as ImageIcon, Layers, Mic2, Power, Search, Sparkles, Activity, ShieldCheck, Database, GitBranch, FileText, CheckSquare, Zap, Network, Sliders } from 'lucide-react';
import ObsidianGraphView from '../components/ObsidianGraphView.jsx';
import ObsidianFileTree from '../components/ObsidianFileTree.jsx';
import ExecutiveBriefingWidget from '../components/ExecutiveBriefingWidget.jsx';
import SocialIngestionHub from '../components/SocialIngestionHub.jsx';
import DeliverableForge from '../components/DeliverableForge.jsx';
import { useAssistant } from '../context/AssistantContext.jsx';
import { useBackend } from '../context/BackendContext.jsx';

export default function Dashboard() {
  const { isAssistantRunning, isListening, toggleAssistant, addNotification } = useAssistant();
  const { apiStatus, apiClient, username } = useBackend();
  const [graphNodes, setGraphNodes] = useState([]);
  const [graphEdges, setGraphEdges] = useState([]);
  const [vaultCards, setVaultCards] = useState([]);
  const [wikiArticles, setWikiArticles] = useState([]);
  const [activeTab, setActiveTab] = useState('graph'); // 'graph' | 'todo' | 'forge' | 'cards' | 'wiki'
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedCardImage, setSelectedCardImage] = useState(null);
  const [activeCategory, setActiveCategory] = useState('Research Hub');
  const [isSyncing, setIsSyncing] = useState(false);

  // Load live nodes and edges from Memory Vault
  useEffect(() => {
    let active = true;
    async function loadData() {
      try {
        const [vaultRes, cardsRes, wikiRes] = await Promise.all([
          fetch(`${apiClient.baseUrl}/api/graph/vault`),
          fetch(`${apiClient.baseUrl}/api/graph/vault/cards?limit=12`),
          fetch(`${apiClient.baseUrl}/api/graph/vault/wiki`)
        ]);

        if (vaultRes.ok && active) {
          const vaultData = await vaultRes.json();
          if (vaultData && Array.isArray(vaultData.nodes)) {
            setGraphNodes(vaultData.nodes);
            setGraphEdges(vaultData.edges || []);
          }
        }

        if (cardsRes.ok && active) {
          const cardsData = await cardsRes.json();
          if (Array.isArray(cardsData)) setVaultCards(cardsData);
        }

        if (wikiRes.ok && active) {
          const wikiData = await wikiRes.json();
          if (Array.isArray(wikiData)) setWikiArticles(wikiData);
        }
      } catch {
        // Backend booting
      }
    }

    loadData();
    const interval = setInterval(loadData, 6000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [apiClient]);

  async function triggerVaultSync() {
    setIsSyncing(true);
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/graph/vault/sync`, { method: 'POST' });
      if (res.ok) {
        addNotification('Vault Synced', 'Memory graph and cards synchronized to GitHub.');
      }
    } catch {
      addNotification('Sync Notice', 'Background sync is running.');
    } finally {
      setIsSyncing(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-4.25rem)] w-full flex-col overflow-hidden bg-[#161616] text-slate-100 font-sans select-none rounded-xl border border-[#2a2a2a]">
      {/* Top Obsidian Tab Navigation Bar */}
      <div className="flex h-10 shrink-0 items-center justify-between border-b border-[#262626] bg-[#1a1a1a] px-3">
        {/* Left Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto thin-scrollbar">
          {[
            { id: 'graph', label: 'Graph view', icon: Network },
            { id: 'cards', label: 'Curated Cards', icon: Layers },
            { id: 'wiki', label: 'Master Wiki', icon: BookOpen },
            { id: 'forge', label: 'Deliverable Forge', icon: Sparkles },
            { id: 'todo', label: 'Master To-Do', icon: CheckSquare }
          ].map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 rounded-t-md px-3.5 py-1.5 text-xs font-medium transition border-t-2 ${
                  isActive
                    ? 'bg-[#181818] text-white border-cyan-400 font-semibold'
                    : 'bg-transparent text-slate-400 border-transparent hover:text-slate-200 hover:bg-white/5'
                }`}
              >
                <Icon size={13} className={isActive ? 'text-cyan-400' : 'text-slate-500'} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Right User & System Telemetry */}
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1.5 text-slate-400">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <strong className="text-white font-mono">{username || 'Immanuel'}</strong>
          </span>

          <button
            type="button"
            onClick={triggerVaultSync}
            disabled={isSyncing}
            className="flex items-center gap-1.5 rounded bg-white/5 px-2.5 py-1 text-[11px] text-slate-300 hover:bg-white/10 transition border border-white/5"
          >
            <GitBranch size={12} className={isSyncing ? 'animate-spin text-cyan-400' : 'text-slate-400'} />
            <span>{isSyncing ? 'Syncing...' : 'GitHub Auto-Sync (60s)'}</span>
          </button>
        </div>
      </div>

      {/* Main Workspace Body (Obsidian Dual Pane: Left Tree + Right Content) */}
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Left Obsidian Vault File Explorer */}
        <ObsidianFileTree
          onSelectCategory={(cat) => {
            setActiveCategory(cat);
            if (activeTab !== 'graph') setActiveTab('graph');
          }}
          activeCategory={activeCategory}
        />

        {/* Right Main Content Pane */}
        <div className="flex flex-1 flex-col min-w-0 bg-[#181818] overflow-hidden">
          {/* TAB 1: MASSIVE OBSIDIAN GRAPH VIEW (Default Centerpiece) */}
          {activeTab === 'graph' && (
            <div className="relative flex-1 h-full w-full">
              <ObsidianGraphView
                nodes={graphNodes}
                edges={graphEdges}
                onSelectNode={(node) => setSelectedNode(node)}
                activeFilter={activeCategory}
              />

              {/* Node Inspector Drawer on Click */}
              {selectedNode && (
                <div className="absolute top-4 right-4 z-30 w-80 rounded-xl border border-white/15 bg-black/90 p-4 shadow-2xl backdrop-blur-2xl text-xs space-y-3">
                  <div className="flex items-center justify-between border-b border-white/10 pb-2">
                    <div>
                      <span className="rounded bg-cyan-400/10 px-2 py-0.5 text-[10px] font-bold uppercase text-cyan-400">
                        {selectedNode.domain || 'Node'}
                      </span>
                      <h4 className="mt-1 text-sm font-bold text-white">{selectedNode.label}</h4>
                    </div>
                    <button
                      type="button"
                      onClick={() => setSelectedNode(null)}
                      className="rounded p-1 text-slate-400 hover:text-white hover:bg-white/10"
                    >
                      &times;
                    </button>
                  </div>

                  {selectedNode.hero_image && (
                    <div
                      onClick={() => setSelectedCardImage(`${apiClient.baseUrl}/${selectedNode.hero_image.replace(/\\/g, '/')}`)}
                      className="relative h-28 w-full cursor-pointer overflow-hidden rounded-lg border border-white/10 bg-black"
                    >
                      <img
                        src={`${apiClient.baseUrl}/${selectedNode.hero_image.replace(/\\/g, '/')}`}
                        alt={selectedNode.label}
                        className="h-full w-full object-cover hover:scale-105 transition"
                      />
                    </div>
                  )}

                  <p className="text-slate-300 leading-relaxed text-[11px]">
                    {selectedNode.summary || 'Cognitive entity synthesized into your Second Brain memory graph.'}
                  </p>

                  <div className="border-t border-white/10 pt-2 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                    <span>Connected to Core</span>
                    <span className="text-cyan-400">Node ID: {String(selectedNode.id).slice(0, 12)}</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: CURATED KNOWLEDGE CARDS */}
          {activeTab === 'cards' && (
            <div className="thin-scrollbar flex-1 overflow-y-auto p-5 space-y-5">
              <SocialIngestionHub onIngested={() => triggerVaultSync()} />

              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {vaultCards.map((card) => {
                  const heroUrl = card.hero_image
                    ? `${apiClient.baseUrl}/${card.hero_image.replace(/\\/g, '/')}`
                    : null;

                  return (
                    <div
                      key={card.id}
                      className="flex flex-col justify-between rounded-xl border border-white/10 bg-[#1f1f1f] p-4 transition hover:border-cyan-400/50"
                    >
                      <div>
                        {heroUrl ? (
                          <div
                            onClick={() => setSelectedCardImage(heroUrl)}
                            className="relative mb-3 h-32 w-full cursor-pointer overflow-hidden rounded-lg border border-white/10 bg-black"
                          >
                            <img src={heroUrl} alt={card.topic} className="h-full w-full object-cover" />
                          </div>
                        ) : (
                          <div className="mb-3 flex h-16 items-center justify-center rounded-lg border border-dashed border-white/10 bg-black/30 text-[11px] text-slate-500">
                            <span>Image Pruned · Zero Disk Waste</span>
                          </div>
                        )}

                        <span className="rounded bg-white/10 px-2 py-0.5 text-[10px] font-bold uppercase text-cyan-300">
                          {card.domain}
                        </span>
                        <h4 className="mt-1.5 text-xs font-bold text-white line-clamp-1">{card.topic || card.window_title}</h4>
                        <p className="mt-1 text-[11px] leading-relaxed text-slate-400 line-clamp-2">{card.summary}</p>
                      </div>

                      <div className="mt-3 pt-2 border-t border-white/5 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                        <span className="truncate max-w-[120px]">{card.app_source}</span>
                        <span className="text-cyan-400">{card.id.slice(5, 17)}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 3: MASTER WIKI ARTICLES */}
          {activeTab === 'wiki' && (
            <div className="thin-scrollbar flex-1 overflow-y-auto p-5">
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {wikiArticles.map((art, idx) => (
                  <div key={idx} className="rounded-xl border border-white/10 bg-[#1f1f1f] p-5 space-y-2">
                    <span className="rounded bg-cyan-400/10 px-2 py-0.5 text-[10px] font-bold uppercase text-cyan-400">
                      {art.domain}
                    </span>
                    <h4 className="text-sm font-bold text-white">{art.title}</h4>
                    <p className="text-xs text-slate-400 line-clamp-3">{art.preview}</p>
                    <div className="pt-2 text-[10px] text-slate-500 font-mono">Updated: {art.updated_at}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 4: DELIVERABLE FORGE */}
          {activeTab === 'forge' && (
            <div className="thin-scrollbar flex-1 overflow-y-auto p-5">
              <DeliverableForge />
            </div>
          )}

          {/* TAB 5: MASTER TO-DO */}
          {activeTab === 'todo' && (
            <div className="thin-scrollbar flex-1 overflow-y-auto p-6 max-w-2xl space-y-3">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-2">Immanuel's Priority Directives</h3>
              {[
                { title: 'Test YouTube Transcript Ingestion with Sub-Second Scraper', done: true },
                { title: 'Review Autonomous GitHub Vault Auto-Sync Commits', done: true },
                { title: 'Present IEEE Conference Proposal to Faculty', done: false },
                { title: 'Explore Force-Directed Obsidian Node Cluster', done: true },
                { title: 'Test Alt + J Golden Transparent Floating Orb', done: true },
              ].map((task, i) => (
                <div key={i} className="flex items-center gap-3 rounded-lg border border-white/10 bg-[#1f1f1f] p-3 text-xs text-slate-300">
                  <input type="checkbox" defaultChecked={task.done} className="h-4 w-4 accent-cyan-400 rounded" />
                  <span className={task.done ? 'line-through text-slate-500' : 'text-white font-medium'}>{task.title}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Full-Screen Image Lightbox Modal */}
      {selectedCardImage && (
        <div
          onClick={() => setSelectedCardImage(null)}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-6 backdrop-blur-xl"
        >
          <div className="relative max-h-[92vh] max-w-[92vw] overflow-hidden rounded-2xl border border-white/20 bg-slate-950 p-3 shadow-2xl">
            <img src={selectedCardImage} alt="Hero Screen Capture" className="max-h-[84vh] w-auto rounded-xl object-contain" />
            <div className="mt-3 flex items-center justify-between px-2 text-xs text-slate-400">
              <span>Representative Hero Screen Capture · Persistent Memory Layer</span>
              <button
                type="button"
                onClick={() => setSelectedCardImage(null)}
                className="rounded-lg bg-white/10 px-3.5 py-1.5 font-bold text-slate-200 transition hover:bg-white/20"
              >
                Close Preview (Esc)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
