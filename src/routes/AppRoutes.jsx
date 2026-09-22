import { Navigate, Route, Routes } from 'react-router-dom';
import AppLayout from '../layouts/AppLayout.jsx';
import HomeOS from '../pages/HomeOS.jsx';
import AgentWorkspace from '../pages/AgentWorkspace.jsx';
import GmailWorkspace from '../pages/GmailWorkspace.jsx';
import CalendarWorkspace from '../pages/CalendarWorkspace.jsx';
import TasksWorkspace from '../pages/TasksWorkspace.jsx';
import NotificationsWorkspace from '../pages/NotificationsWorkspace.jsx';
import RemindersWorkspace from '../pages/RemindersWorkspace.jsx';
import KnowledgeWorkspace from '../pages/KnowledgeWorkspace.jsx';
import KnowledgeGraphPage from '../pages/KnowledgeGraph.jsx';
import FilesWorkspace from '../pages/FilesWorkspace.jsx';
import ProjectsWorkspace from '../pages/ProjectsWorkspace.jsx';
import AutomationsWorkspace from '../pages/AutomationsWorkspace.jsx';
import AgentActivityLog from '../pages/AgentActivityLog.jsx';
import IntegrationsManager from '../pages/IntegrationsManager.jsx';
import MemoryLab from '../pages/MemoryLab.jsx';
import VoiceAssistant from '../pages/VoiceAssistant.jsx';
import Settings from '../pages/Settings.jsx';
import JarvisHoloOrb from '../pages/JarvisHoloOrb.jsx';

export default function AppRoutes() {
  return (
    <Routes>
      {/* Floating Transparent Golden Holographic Orb (Standalone overlay) */}
      <Route path="/jarvis-orb" element={<JarvisHoloOrb />} />

      {/* Main Autonomous AI Personal OS Shell */}
      <Route element={<AppLayout />}>
        {/* 1. Home Command Center */}
        <Route path="/" element={<HomeOS />} />

        {/* 2. Full-Screen AI Agent */}
        <Route path="/agent" element={<AgentWorkspace />} />
        <Route path="/chat" element={<AgentWorkspace />} />

        {/* 3. Connected Gmail Workspace */}
        <Route path="/gmail" element={<GmailWorkspace />} />

        {/* 4. Calendar Workspace */}
        <Route path="/calendar" element={<CalendarWorkspace />} />

        {/* 5. Tasks Management */}
        <Route path="/tasks" element={<TasksWorkspace />} />

        {/* 6. Notifications Center */}
        <Route path="/notifications" element={<NotificationsWorkspace />} />

        {/* 7. Reminders Workspace */}
        <Route path="/reminders" element={<RemindersWorkspace />} />

        {/* 8. Knowledge Base & Wiki */}
        <Route path="/knowledge" element={<KnowledgeWorkspace />} />

        {/* 9. Dedicated Interactive Obsidian Knowledge Graph */}
        <Route path="/knowledge-graph" element={<KnowledgeGraphPage />} />

        {/* 10. Files & Artifacts */}
        <Route path="/files" element={<FilesWorkspace />} />

        {/* 11. Projects Workspace */}
        <Route path="/projects" element={<ProjectsWorkspace />} />

        {/* 12. Automations & Workflows */}
        <Route path="/automations" element={<AutomationsWorkspace />} />

        {/* 13. Agent Activity Audit Log */}
        <Route path="/activity" element={<AgentActivityLog />} />

        {/* 14b. Memory Lab - the research layer demonstration */}
        <Route path="/memory-lab" element={<MemoryLab />} />

        {/* 14. Integrations Manager */}
        <Route path="/integrations" element={<IntegrationsManager />} />

        {/* 15. Voice Companion & Settings */}
        <Route path="/voice" element={<VoiceAssistant />} />
        <Route path="/settings" element={<Settings />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
