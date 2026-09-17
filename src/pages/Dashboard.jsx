import { useEffect, useState } from 'react';
import { BrainCircuit, ExternalLink, Image as ImageIcon, Layers, Mic2, Power, Search, Sparkles, Activity, ShieldCheck, Database, GitBranch } from 'lucide-react';
import BackendStatus from '../components/BackendStatus.jsx';
import NeuralBrain3D from '../components/NeuralBrain3D.jsx';
import NotificationPanel from '../components/NotificationPanel.jsx';
import PageHeader from '../components/PageHeader.jsx';
import StatusCard from '../components/StatusCard.jsx';
import { useAssistant } from '../context/AssistantContext.jsx';
import { useBackend } from '../context/BackendContext.jsx';

function Dashboard() {
  const { isAssistantRunning, isListening, toggleAssistant, addNotification } = useAssistant();
  const { apiStatus, apiClient } = useBackend();
  const [vaultCards, setVaultCards] = useState([]);
  const [selectedCardImage, setSelectedCardImage] = useState(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [activeNodeCount, setActiveNodeCount] = useState(480);

  // Dynamic cognitive brain state determination
  const brainState = isListening
    ? 'listening'
    : isAssistantRunning
    ? 'thinking'
    : apiStatus === 'online' || apiStatus === 'authenticated'
    ? 'idle'
    : 'idle';

  // Fetch recent persistent JSON Memory Cards
  useEffect(() => {
    let active = true;
    async function loadCards() {
      try {
        const res = await fetch(`${apiClient.baseUrl}/api/graph/vault/cards?limit=8`);
        if (res.ok) {
          const data = await res.json();
          if (active && Array.isArray(data)) {
            setVaultCards(data);
            // Increment 3D node count as new cards are synthesized
            setActiveNodeCount(480 + data.length * 8);
          }
        }
      } catch {
        // Backend booting
      }
    }

    loadCards();
    const interval = setInterval(loadCards, 6000);
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
        addNotification('GitHub Vault Synced', 'Memory cards, hero captures, and graph pushed to GitHub.');
      }
    } catch {
      addNotification('Sync Notice', 'Background sync will retry automatically.');
    } finally {
      setIsSyncing(false);
    }
  }

  const domainBadges = {
    Technology: 'border-cyan-400/30 bg-cyan-500/10 text-cyan-300',
    Science: 'border-emerald-400/30 bg-emerald-500/10 text-emerald-300',
    Geopolitics: 'border-amber-400/30 bg-amber-500/10 text-amber-300',
    Research: 'border-purple-400/30 bg-purple-500/10 text-purple-300'
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Cinematic Top Header */}
      <PageHeader
        eyebrow="Stark AI Foundation"
        title="JARVIS Autonomous Cognitive Cortex"
        description="Autonomous multi-agent intelligence, ephemeral 0MB screen ingestion, real-time science/tech curation, and persistent GitHub memory vault."
        action={
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={triggerVaultSync}
              disabled={isSyncing}
              className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-xs font-bold text-slate-200 transition hover:bg-white/10 disabled:opacity-50"
            >
              <GitBranch size={15} className={isSyncing ? 'animate-spin text-cyanGlow' : 'text-slate-400'} />
              {isSyncing ? 'Pushing to GitHub...' : 'Auto-Sync Active (60s)'}
            </button>
            <button
              type="button"
              onClick={() => {
                toggleAssistant();
                addNotification('Cortex State Updated', isAssistantRunning ? 'Jarvis transitioned to Standby.' : 'Jarvis cognitive swarm active.');
              }}
              className="flex items-center justify-center gap-2 rounded-xl border border-cyanGlow/40 bg-gradient-to-r from-cyanGlow/20 to-mintGlow/15 px-5 py-2.5 text-sm font-bold text-cyanGlow shadow-glow transition hover:from-cyanGlow/30 hover:to-mintGlow/25"
            >
              <Power size={17} />
              {isAssistantRunning ? 'Pause Swarm' : 'Activate Jarvis Swarm'}
            </button>
          </div>
        }
      />

      {/* Massive 3D Neural Brain Hero Viewport */}
      <div className="w-full">
        <NeuralBrain3D
          state={brainState}
          nodeCount={activeNodeCount}
          domainFocus="Technology, Science & Global Intel"
        />
      </div>

      {/* Futuristic Telemetry Metrics Grid */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatusCard
          title="Cognitive Cortex"
          value={isAssistantRunning ? 'Autonomous' : 'Standby'}
          detail="Active multi-agent neural ingestion."
          accent={isAssistantRunning ? 'mint' : 'cyan'}
        />
        <StatusCard
          title="Speech & Wake"
          value={isListening ? 'Listening' : 'Active'}
          detail="Tamil & English dual stream audio."
          accent="mint"
        />
        <StatusCard
          title="Memory Vault"
          value="GitHub Synced"
          detail="Ephemeral captures · 0MB local bloat."
          accent="amber"
        />
        <StatusCard
          title="Curation Filter"
          value="Best-Shot Mode"
          detail="High-context frame selection active."
        />
      </div>

      {/* Backend & Diagnostics Module */}
      <BackendStatus />

      {/* Curated Knowledge Cards & Hero Screen Captures */}
      <section className="glass-panel rounded-2xl p-6">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-cyanGlow/30 bg-cyanGlow/10 text-cyanGlow">
              <Layers size={19} />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">Curated Knowledge Cards & Hero Captures</h3>
              <p className="text-xs text-slate-400">Single highest-content visual evidence preserved per information cluster.</p>
            </div>
          </div>
          <span className="flex items-center gap-1.5 rounded-full border border-mintGlow/20 bg-mintGlow/10 px-3 py-1 text-[11px] font-semibold text-mintGlow">
            <Activity size={13} /> {vaultCards.length} Live Knowledge Cards
          </span>
        </div>

        {vaultCards.length > 0 ? (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {vaultCards.map((card) => {
              const heroUrl = card.hero_image
                ? `${apiClient.baseUrl}/${card.hero_image.replace(/\\/g, '/')}`
                : null;

              return (
                <div
                  key={card.id}
                  className="group flex flex-col justify-between overflow-hidden rounded-xl border border-white/10 bg-slate-950/60 p-4 transition duration-200 hover:-translate-y-1 hover:border-cyanGlow/40 hover:bg-slate-900/80 hover:shadow-glow"
                >
                  <div>
                    {/* Hero Image Thumbnail */}
                    {heroUrl ? (
                      <div
                        onClick={() => setSelectedCardImage(heroUrl)}
                        className="relative mb-3 h-36 w-full cursor-pointer overflow-hidden rounded-lg border border-white/10 bg-black/60"
                      >
                        <img
                          src={heroUrl}
                          alt={card.topic}
                          className="h-full w-full object-cover transition duration-300 group-hover:scale-105"
                          loading="lazy"
                        />
                        <div className="absolute inset-0 flex items-center justify-center bg-black/45 opacity-0 transition group-hover:opacity-100">
                          <span className="flex items-center gap-1.5 rounded-full bg-cyanGlow px-3 py-1 text-xs font-bold text-slate-950 shadow-glow">
                            <ImageIcon size={13} /> View Full Hero Capture
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="mb-3 flex h-20 items-center justify-center rounded-lg border border-dashed border-white/10 bg-black/30 p-2 text-center text-[11px] text-slate-500">
                        <span>Text Synthesized · Image Redundant or Pruned</span>
                      </div>
                    )}

                    {/* Domain & Topic Badges */}
                    <div className="mb-2 flex flex-wrap items-center gap-1.5">
                      <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wide ${domainBadges[card.domain] || 'border-slate-500/30 bg-slate-500/10 text-slate-300'}`}>
                        {card.domain}
                      </span>
                      {card.priority === 'high' && (
                        <span className="rounded-full border border-red-400/30 bg-red-500/10 px-2 py-0.5 text-[10px] font-semibold text-red-300 uppercase">
                          High Context
                        </span>
                      )}
                    </div>

                    <h4 className="text-sm font-semibold text-slate-100 line-clamp-1">{card.topic || card.window_title}</h4>
                    <p className="mt-1.5 text-xs leading-5 text-slate-400 line-clamp-2">{card.summary}</p>

                    {/* Key Pointers */}
                    {card.key_pointers && card.key_pointers.length > 0 && (
                      <div className="mt-3 space-y-1 rounded-lg bg-black/40 p-2.5 text-[11px] text-slate-300">
                        {card.key_pointers.slice(0, 2).map((ptr, idx) => (
                          <div key={idx} className="flex items-start gap-1.5">
                            <span className="text-cyanGlow">▪</span>
                            <span className="line-clamp-1">{ptr}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Entities & Footer */}
                  <div className="mt-3.5 flex items-center justify-between border-t border-white/5 pt-2 text-[10px] text-slate-500">
                    <span className="truncate max-w-[120px]">{card.app_source}</span>
                    <span className="font-mono text-cyanGlow/80">{card.id.slice(5, 17)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-white/10 py-14 text-center">
            <Layers className="mb-3 text-slate-600" size={32} />
            <h4 className="font-semibold text-slate-300">No Knowledge Cards Formed Yet</h4>
            <p className="mt-1 max-w-md text-xs text-slate-500">
              Browse any YouTube video, technical article, or code in VS Code. Jarvis will automatically curate the content, select the single best Hero frame, and pop new nodes into your 3D Cortex.
            </p>
          </div>
        )}
      </section>

      {/* Autonomous Agent Swarm & Notifications */}
      <div className="grid gap-6 xl:grid-cols-[1.4fr_0.8fr]">
        <section className="glass-panel rounded-2xl p-6">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h3 className="font-bold text-slate-100">Autonomous Agent Swarm</h3>
              <p className="mt-0.5 text-xs text-slate-400">Continuous background cognitive processes executing on your machine.</p>
            </div>
            <span className="flex items-center gap-1.5 rounded-lg border border-mintGlow/20 bg-mintGlow/10 px-3 py-1 text-xs font-bold text-mintGlow">
              <Sparkles size={13} /> Swarm Synchronized
            </span>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {[
              {
                icon: BrainCircuit,
                title: 'Sensory Agent',
                tag: 'Screen & OCR',
                text: 'Selects the single richest frame. Deletes redundant screenshots.'
              },
              {
                icon: Mic2,
                title: 'Curation Agent',
                tag: 'Best-Shot Filter',
                text: 'Compares context scores. Elevates deep Science & Tech.'
              },
              {
                icon: Search,
                title: 'GitHub Vault Agent',
                tag: 'Autonomous Sync',
                text: 'Silently commits lightweight WebP hero images + JSON cards to repo.'
              }
            ].map((item) => (
              <div key={item.title} className="rounded-xl border border-white/10 bg-white/5 p-4.5 transition hover:border-cyanGlow/40 hover:bg-white/[0.08]">
                <div className="mb-3 flex items-center justify-between">
                  <item.icon className="text-cyanGlow" size={22} />
                  <span className="rounded bg-white/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-slate-300">{item.tag}</span>
                </div>
                <p className="font-semibold text-slate-200">{item.title}</p>
                <p className="mt-1.5 text-xs leading-5 text-slate-400">{item.text}</p>
              </div>
            ))}
          </div>
        </section>

        <NotificationPanel />
      </div>

      {/* Full-Screen Image Lightbox Modal */}
      {selectedCardImage && (
        <div
          onClick={() => setSelectedCardImage(null)}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-6 backdrop-blur-xl"
        >
          <div className="relative max-h-[92vh] max-w-[92vw] overflow-hidden rounded-2xl border border-white/20 bg-slate-950 p-3 shadow-2xl">
            <img
              src={selectedCardImage}
              alt="Hero Screen Capture"
              className="max-h-[84vh] w-auto rounded-xl object-contain"
            />
            <div className="mt-3 flex items-center justify-between px-2 text-xs text-slate-400">
              <span>Representative Hero Screen Capture · Persistent GitHub Memory Layer</span>
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

export default Dashboard;
