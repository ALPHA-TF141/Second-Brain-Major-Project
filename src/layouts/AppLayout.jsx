import { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar.jsx';
import Navbar from '../components/Navbar.jsx';
import FloatingAssistantButton from '../components/FloatingAssistantButton.jsx';
import { useBackend } from '../context/BackendContext.jsx';

function AppLayout() {
  const { apiClient, loginDemo } = useBackend();

  // Auto-start capture once on app launch + handle tray commands
  useEffect(() => {
    let cancelled = false;

    async function boot() {
      try {
        // 1. Ensure we are logged in (demo)
        if (!apiClient.getToken()) await loginDemo();

        // 2. Start capture automatically if not already running
        const status = await apiClient.captureStatus().catch(() => null);
        if (!cancelled && status && !status.is_active) {
          await apiClient.startCapture({
            sessionType: 'continuous',
            screenshotIntervalSeconds: 5
          }).catch((e) => console.warn('Auto-capture start failed:', e));
        }
      } catch (e) {
        console.warn('Jarvis boot failed:', e);
      }
    }

    boot();

    // 3. Listen for tray Pause/Resume commands (from Electron)
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

  return (
    <div className="h-screen overflow-hidden bg-ink/80 text-slate-100">
      <div className="flex h-full">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <Navbar />
          <main className="thin-scrollbar min-h-0 flex-1 overflow-y-auto px-4 pb-5 pt-4 sm:px-6">
            <Outlet />
          </main>
        </div>
      </div>
      <FloatingAssistantButton />
    </div>
  );
}

export default AppLayout;