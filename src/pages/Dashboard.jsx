import { useEffect, useState } from 'react';
import { BrainCircuit, ExternalLink, Image as ImageIcon, Layers, Mic2, Power, Search, Sparkles } from 'lucide-react';
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
        const res = await fetch(`${apiClient.baseUrl}/api/graph/vault/cards?limit=6`);
        if (res.ok) {
          const data = await res.json();
          if (active && Array.isArray(data)) {
            setVaultCards(data);
          }
        }
      } catch {
        // Backend still booting
      }
    }

    loadCards();
    const interval = setInterval(loadCards, 8000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [apiClient]);

  const domainBadges = {
    Technology: 'border-cyan-400/30 bg-cyan-500/10 text-cyan-300',
    Science: 'border-emerald-400/30 bg-emerald-500/10 text-emerald-300',
    Geopolitics: 'border-amber-400/30 bg-amber-500/10 text-amber-300',
    Research: 'border-purple-400/30 bg-purple-500/10 text-purple-300'
  };

  return (
    <div>
      <PageHeader
        eyebrow="Cognitive Command Center"
        title="Jarvis Second Brain Autonomous Cortex"
        description="Autonomous multi-agent knowledge capture, ephemeral OCR, real-time science/tech curation, and persistent GitHub memory vault."
        action={
          <button
            type="button"
            onClick={() => {
              toggleAssistant();
              addNotification('Cortex State Updated', isAssistantRunning ? 'Jarvis transitioned to Standby.' : 'Jarvis cognitive swarm active.');
            }}
            className="flex items-center justify-center gap-2 rounded-lg border border-cyanGlow/30 bg-cyanGlow/12 px-4 py-3 text-sm font-semibold text-cyanGlow shadow-glow transition hover:bg-cyanGlow/20"
          >
            <Power size={17} />
            {isAssistantRunning ? 'Pause Swarm' : 'Activate Jarvis Swarm'}
          </button>
        }
      />

      {/* Top 3D Neural Brain & System Metrics Grid */}
      <div className="mb-5 grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
        <NeuralBrain3D
          state={brainState}
          domainFocus="Technology, Science & Geopolitics"
        />

        <div className="flex flex-col justify-between gap-3">
          <div className="grid flex-1 gap-3 sm:grid-cols-2">
            <StatusCard
              title="Cortex Status"
              value={isAssistantRunning ? 'Cognitive' : 'Standby'}
              detail="Autonomous multi-agent swarm state."
              accent={isAssistantRunning ? 'mint' : 'cyan'}
            />
            <StatusCard
              title="Speech Engine"
              value={isListening ? 'Listening' : 'Ready'}
              detail="Dual-stream Tamil & English voice recognition."
              accent="mint"
            />
            <StatusCard
              title="Memory Vault"
              value="GitHub Synced"
              detail="Representative Hero Captures. Zero disk bloat."
              accent="amber"
            />
            <StatusCard
              title="Curator Agent"
              value="Best-Shot Mode"
              detail="Picks highest-context frame. Purges duplicates."
            />
          </div>

          <BackendStatus />
        </div>
      </div>

      {/* Live Curated Knowledge Cards & Hero Screen Captures */}
      {vaultCards.length > 0 && (
        <section className="glass-panel mb-5 rounded-lg p-5">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers className="text-cyanGlow" size={20} />
              <div>
                <h3 className="font-semibold text-slate-200">Curated Knowledge Cards & Hero Captures</h3>
                <p className="text-xs text-slate-400">Single highest-content visual evidence preserved per information cluster.</p>
              </div>
            </div>
            <span className="text-xs text-slate-500">Live Memory Layer</span>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {vaultCards.map((card) => {
              const heroUrl = card.hero_image
                ? `${apiClient.baseUrl}/${card.hero_image.replace(/\\/g, '/')}`
                : null;

              return (
                <div key={card.id} className="flex flex-col justify-between rounded-lg border border-white/10 bg-white/5 p-4 transition hover:border-cyanGlow/40 hover:bg-white/[0.08]">
                  <div>
                    {/* Hero Image Thumbnail */}
                    {heroUrl ? (
                      <div
                        onClick={() => setSelectedCardImage(heroUrl)}
                        className="group relative mb-3 h-36 w-full cursor-pointer overflow-hidden rounded-md border border-white/10 bg-slate-950"
                      >
                        <img
                          src={heroUrl}
                          alt={card.topic}
                          className="h-full w-full object-cover transition duration-300 group-hover:scale-105"
                          loading="lazy"
                        />
                        <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition group-hover:opacity-100">
                          <span className="flex items-center gap-1.5 rounded-full bg-cyanGlow/90 px-3 py-1 text-xs font-bold text-slate-950">
                            <ImageIcon size={13} /> View Full Hero Capture
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="mb-3 flex h-14 items-center justify-center rounded-md border border-dashed border-white/10 bg-slate-950/40 text-[11px] text-slate-500">
                        <span>Text Synthesized · Image Redundant / Pruned</span>
                      </div>
                    )}

                    {/* Domain & Topic Badges */}
                    <div className="mb-2 flex flex-wrap items-center gap-2">
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
                    <p className="mt-1 text-xs leading-5 text-slate-400 line-clamp-2">{card.summary}</p>

                    {/* Key Pointers */}
                    {card.key_pointers && card.key_pointers.length > 0 && (
                      <div className="mt-3 space-y-1 rounded bg-black/30 p-2 text-[11px] text-slate-300">
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
                  <div className="mt-3 pt-2 border-t border-white/5 flex items-center justify-between text-[10px] text-slate-500">
                    <span>{card.app_source}</span>
                    <span className="text-cyanGlow/80 font-mono">{card.id.slice(5, 17)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Modules and Notifications */}
      <div className="grid gap-5 xl:grid-cols-[1.4fr_0.8fr]">
        <section className="glass-panel rounded-lg p-5">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h3 className="font-semibold">Autonomous Agent Swarm</h3>
              <p className="mt-1 text-sm text-slate-500">Continuous background agents running on your machine.</p>
            </div>
            <span className="flex items-center gap-1.5 rounded-lg border border-mintGlow/20 bg-mintGlow/10 px-3 py-1 text-xs font-semibold text-mintGlow">
              <Sparkles size={12} /> Swarm Online
            </span>
          </div>

          <div className="grid gap-3 md:grid-cols-3">
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
                tag: 'Cloud Sync',
                text: 'Saves lightweight WebP hero images + JSON cards to repo.'
              }
            ].map((item) => (
              <div key={item.title} className="rounded-lg border border-white/10 bg-white/5 p-4 transition hover:border-cyanGlow/30 hover:bg-white/[0.07]">
                <div className="mb-3 flex items-center justify-between">
                  <item.icon className="text-cyanGlow" size={22} />
                  <span className="rounded bg-white/10 px-2 py-0.5 text-[10px] uppercase tracking-wider text-slate-300">{item.tag}</span>
                </div>
                <p className="font-semibold text-slate-200">{item.title}</p>
                <p className="mt-2 text-xs leading-5 text-slate-400">{item.text}</p>
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
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-6 backdrop-blur-md"
        >
          <div className="relative max-h-[90vh] max-w-[90vw] overflow-hidden rounded-xl border border-white/20 bg-slate-950 p-2 shadow-2xl">
            <img
              src={selectedCardImage}
              alt="Hero Screen Capture"
              className="max-h-[82vh] w-auto rounded-lg object-contain"
            />
            <div className="mt-2 flex items-center justify-between px-2 text-xs text-slate-400">
              <span>Representative Hero Screen Capture · GitHub Memory Layer</span>
              <button
                type="button"
                onClick={() => setSelectedCardImage(null)}
                className="rounded bg-white/10 px-3 py-1 text-slate-200 transition hover:bg-white/20"
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
