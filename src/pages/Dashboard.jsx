import { useState } from 'react';
import { BrainCircuit, Mic2, Power, Search, Sparkles } from 'lucide-react';
import BackendStatus from '../components/BackendStatus.jsx';
import NeuralBrain3D from '../components/NeuralBrain3D.jsx';
import NotificationPanel from '../components/NotificationPanel.jsx';
import PageHeader from '../components/PageHeader.jsx';
import StatusCard from '../components/StatusCard.jsx';
import { useAssistant } from '../context/AssistantContext.jsx';
import { useBackend } from '../context/BackendContext.jsx';

function Dashboard() {
  const { isAssistantRunning, isListening, toggleAssistant, addNotification } = useAssistant();
  const { apiStatus } = useBackend();

  // Dynamic cognitive brain state determination
  const brainState = isListening
    ? 'listening'
    : isAssistantRunning
    ? 'thinking'
    : apiStatus === 'online' || apiStatus === 'authenticated'
    ? 'idle'
    : 'idle';

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
              detail="Zero local disk bloat. Ephemeral screen capture."
              accent="amber"
            />
            <StatusCard
              title="Curator Agent"
              value="Tech & Science"
              detail="Filters noise/memes. Elevates deep knowledge."
            />
          </div>

          <BackendStatus />
        </div>
      </div>

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
                text: 'Grabs snapshots, extracts text, immediately deletes raw image.'
              },
              {
                icon: Mic2,
                title: 'Curation Agent',
                tag: 'Noise Filter',
                text: 'Purges duplicates & social scrolling. Elevates Science & Tech.'
              },
              {
                icon: Search,
                title: 'GitHub Vault Agent',
                tag: 'Cloud Sync',
                text: 'Packages structured JSON cards and updates Knowledge Graph.'
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
    </div>
  );
}

export default Dashboard;
