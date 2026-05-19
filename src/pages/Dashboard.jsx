import { BrainCircuit, Mic2, Power, Search } from 'lucide-react';
import BackendStatus from '../components/BackendStatus.jsx';
import NotificationPanel from '../components/NotificationPanel.jsx';
import PageHeader from '../components/PageHeader.jsx';
import StatusCard from '../components/StatusCard.jsx';
import { useAssistant } from '../context/AssistantContext.jsx';

function Dashboard() {
  const { isAssistantRunning, isListening, toggleAssistant, addNotification } = useAssistant();

  return (
    <div>
      <PageHeader
        eyebrow="Command center"
        title="AI foundation dashboard"
        description="A clean desktop shell for the future memory, voice, OCR, RAG, semantic search, and Tamil assistant layers."
        action={
          <button
            type="button"
            onClick={() => {
              toggleAssistant();
              addNotification('Assistant toggled', 'The fake runtime status was updated.');
            }}
            className="flex items-center justify-center gap-2 rounded-lg border border-cyanGlow/30 bg-cyanGlow/12 px-4 py-3 text-sm font-semibold text-cyanGlow shadow-glow transition hover:bg-cyanGlow/20"
          >
            <Power size={17} />
            {isAssistantRunning ? 'Stop Assistant' : 'Start Assistant'}
          </button>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatusCard title="AI Status" value={isAssistantRunning ? 'Online' : 'Idle'} detail="Mock runtime switch for the future local assistant core." />
        <StatusCard title="Listening" value={isListening ? 'Active' : 'Paused'} detail="Voice UI placeholder for later speech recognition." accent="mint" />
        <StatusCard title="Memory Nodes" value="128" detail="Static placeholder for future long-term memory entries." accent="amber" />
        <StatusCard title="Search Index" value="Ready" detail="Reserved for semantic search and RAG pipeline health." />
      </div>

      <div className="mt-5">
        <BackendStatus />
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[1.4fr_0.8fr]">
        <section className="glass-panel rounded-lg p-5">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h3 className="font-semibold">Assistant Modules</h3>
              <p className="mt-1 text-sm text-slate-500">Phase 1 placeholders, ready for real services later.</p>
            </div>
            <span className="rounded-lg border border-mintGlow/20 bg-mintGlow/10 px-3 py-1 text-xs font-semibold text-mintGlow">Stable</span>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            {[
              { icon: BrainCircuit, title: 'Memory', text: 'User facts and context' },
              { icon: Mic2, title: 'Voice', text: 'Wake word and speech' },
              { icon: Search, title: 'RAG', text: 'Docs and knowledge search' }
            ].map((item) => (
              <div key={item.title} className="rounded-lg border border-white/10 bg-white/5 p-4">
                <item.icon className="mb-4 text-cyanGlow" size={24} />
                <p className="font-semibold">{item.title}</p>
                <p className="mt-2 text-sm text-slate-400">{item.text}</p>
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
