import { useEffect, useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import ObsidianRibbon from '../components/ObsidianRibbon.jsx';
import ObsidianFileTree from '../components/ObsidianFileTree.jsx';
import ObsidianTabBar from '../components/ObsidianTabBar.jsx';
import AmbientCapsuleHUD from '../components/AmbientCapsuleHUD.jsx';
import { useBackend } from '../context/BackendContext.jsx';

export default function AppLayout() {
  const { apiClient, loginDemo } = useBackend();
  const navigate = useNavigate();
  const location = useLocation();

  const [activeTab, setActiveTab] = useState('graph');
  const [activeRibbonView, setActiveRibbonView] = useState('files');
  const [activeCategory, setActiveCategory] = useState('Artificial Intelligence');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Auto-start capture and login as Immanuel automatically
  useEffect(() => {
    let cancelled = false;

    async function boot() {
      try {
        if (!apiClient.getToken()) await loginDemo('Immanuel');
        const status = await apiClient.captureStatus().catch(() => null);
        if (!cancelled && status && !status.is_active) {
          await apiClient.startCapture({
            sessionType: 'continuous',
            screenshotIntervalSeconds: 5
          }).catch((e) => console.warn('Auto-capture start failed:', e));
        }
      } catch (e) {
        console.warn('Boot failed:', e);
      }
    }

    boot();

    const handleCapture = (cmd) => {
      if (cmd === 'pause') apiClient.pauseCapture().catch(() => {});
      else if (cmd === 'resume') apiClient.resumeCapture().catch(() => {});
    };
    const ipc = window.secondBrain;
    if (ipc?.onCaptureCommand) {
      ipc.onCaptureCommand(handleCapture);
    }

    return () => { cancelled = true; };
  }, [apiClient, loginDemo]);

  // Sync active tab with route
  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    if (tabId === 'graph') navigate('/');
    else if (tabId === 'todo') navigate('/');
    else if (tabId === 'research') navigate('/');
    else if (tabId === 'focus') navigate('/');
  };

  const handleRibbonChange = (viewId) => {
    setActiveRibbonView(viewId);
    if (viewId === 'files') {
      setIsSidebarOpen(!isSidebarOpen);
    } else if (viewId === 'graph') {
      setActiveTab('graph');
      navigate('/');
    } else if (viewId === 'settings') {
      navigate('/settings');
    }
  };

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-[#161616] text-[#dcddde] select-none font-sans">
      {/* Top Obsidian Window Bar with Document Tabs & Native Frameless Window Controls */}
      <ObsidianTabBar
        activeTab={activeTab}
        onTabChange={handleTabChange}
        onCloseTab={(id) => {}}
      />

      {/* Main Dual-Pane Obsidian Body */}
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Leftmost Obsidian Ribbon (Activity Bar) */}
        <ObsidianRibbon
          activeView={activeRibbonView}
          onViewChange={handleRibbonChange}
        />

        {/* Left Collapsible Vault File Explorer */}
        {isSidebarOpen && (
          <ObsidianFileTree
            onSelectCategory={(cat) => {
              setActiveCategory(cat);
              setActiveTab('graph');
              navigate('/');
            }}
            activeCategory={activeCategory}
          />
        )}

        {/* Main Content Area (Full-Bleed Force-Directed Knowledge Graph) */}
        <main className="flex flex-1 flex-col min-w-0 bg-[#1e1e1e] overflow-hidden relative">
          <Outlet />
        </main>
      </div>

      {/* Ambient Floating Jarvis Orb Trigger (Alt + J / Alt + Space) */}
      <AmbientCapsuleHUD />
    </div>
  );
}
