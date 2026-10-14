import { Navigate, Route, Routes } from 'react-router-dom';
import AppLayout from '../layouts/AppLayout.jsx';
import Dashboard from '../pages/Dashboard.jsx';
import AgentWorkspace from '../pages/AgentWorkspace.jsx';
import GmailWorkspace from '../pages/GmailWorkspace.jsx';
import KnowledgeWorkspace from '../pages/KnowledgeWorkspace.jsx';
import IntegrationsManager from '../pages/IntegrationsManager.jsx';
import MemoryLab from '../pages/MemoryLab.jsx';
import VoiceAssistant from '../pages/VoiceAssistant.jsx';
import Settings from '../pages/Settings.jsx';

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        {/* Home: memory store overview */}
        <Route path="/" element={<Dashboard />} />

        {/* RAG chat over the personal knowledge store */}
        <Route path="/agent" element={<AgentWorkspace />} />
        <Route path="/chat" element={<AgentWorkspace />} />

        {/* Mail ingestion workspace (Gmail via OAuth/IMAP) */}
        <Route path="/gmail" element={<GmailWorkspace />} />

        {/* Memory store browser */}
        <Route path="/knowledge" element={<KnowledgeWorkspace />} />

        {/* Research layer demonstration: temporal PKG, conflicts,
            consolidation, forgetting, gaps and PersonalBrain-Bench */}
        <Route path="/memory-lab" element={<MemoryLab />} />

        {/* Web & social ingestion + connected accounts */}
        <Route path="/integrations" element={<IntegrationsManager />} />

        {/* Voice companion (wake word + speech I/O) */}
        <Route path="/voice" element={<VoiceAssistant />} />
        <Route path="/settings" element={<Settings />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
