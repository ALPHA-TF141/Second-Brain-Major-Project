import { Navigate, Route, Routes } from 'react-router-dom';
import AppLayout from '../layouts/AppLayout.jsx';
import Dashboard from '../pages/Dashboard.jsx';
import Chat from '../pages/Chat.jsx';
import Timeline from '../pages/Timeline.jsx';
import LiveActivity from '../pages/LiveActivity.jsx';
import OcrKnowledge from '../pages/OcrKnowledge.jsx';
import SemanticMemory from '../pages/SemanticMemory.jsx';
import VoiceAssistant from '../pages/VoiceAssistant.jsx';
import Settings from '../pages/Settings.jsx';
import KnowledgeGraph from '../pages/KnowledgeGraph.jsx';

function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/timeline" element={<Timeline />} />
        <Route path="/activity" element={<LiveActivity />} />
        <Route path="/ocr" element={<OcrKnowledge />} />
        <Route path="/semantic" element={<SemanticMemory />} />
        <Route path="/knowledge-graph" element={<KnowledgeGraph />} />
        <Route path="/voice" element={<VoiceAssistant />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default AppRoutes;
