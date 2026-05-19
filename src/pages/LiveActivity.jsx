import { useEffect, useMemo, useState } from 'react';
import { Activity, Camera, Clock, Monitor, Pause, Play, Square, Wifi } from 'lucide-react';
import PageHeader from '../components/PageHeader.jsx';
import { useBackend } from '../context/BackendContext.jsx';

function formatDuration(startedAt) {
  if (!startedAt) return '00:00';
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000));
  const minutes = Math.floor(seconds / 60).toString().padStart(2, '0');
  const rest = (seconds % 60).toString().padStart(2, '0');
  return `${minutes}:${rest}`;
}

function LiveActivity() {
  const { apiClient, socketStatus, liveEvents, loginDemo, username } = useBackend();
  const [status, setStatus] = useState({ is_active: false, is_paused: false });
  const [screenshots, setScreenshots] = useState([]);
  const [activity, setActivity] = useState([]);
  const [duration, setDuration] = useState('00:00');
  const [isBusy, setIsBusy] = useState(false);

  const latestScreenshot = screenshots[0];
  const captureEvents = useMemo(
    () => liveEvents.filter((event) => ['capture_status', 'active_window', 'screenshot', 'clipboard'].includes(event.type)),
    [liveEvents]
  );

  async function refreshCapture() {
    if (!apiClient.getToken()) return;
    try {
      const [nextStatus, nextScreenshots, nextActivity] = await Promise.all([
        apiClient.captureStatus(),
        apiClient.captureScreenshots(),
        apiClient.captureActivity()
      ]);
      setStatus(nextStatus);
      setScreenshots(nextScreenshots);
      setActivity(nextActivity);
    } catch {
      setStatus((current) => ({ ...current, is_active: false }));
    }
  }

  async function ensureLogin() {
    if (!apiClient.getToken()) {
      await loginDemo();
    }
  }

  async function startCapture() {
    setIsBusy(true);
    try {
      await ensureLogin();
      const nextStatus = await apiClient.startCapture({
        sessionType: 'study',
        screenshotIntervalSeconds: 5
      });
      setStatus(nextStatus);
      await refreshCapture();
    } finally {
      setIsBusy(false);
    }
  }

  async function stopCapture() {
    setIsBusy(true);
    try {
      setStatus(await apiClient.stopCapture());
      await refreshCapture();
    } finally {
      setIsBusy(false);
    }
  }

  async function togglePause() {
    setIsBusy(true);
    try {
      setStatus(status.is_paused ? await apiClient.resumeCapture() : await apiClient.pauseCapture());
    } finally {
      setIsBusy(false);
    }
  }

  useEffect(() => {
    refreshCapture();
  }, []);

  useEffect(() => {
    refreshCapture();
  }, [liveEvents.length]);

  useEffect(() => {
    const timer = window.setInterval(() => setDuration(formatDuration(status.started_at)), 1000);
    return () => window.clearInterval(timer);
  }, [status.started_at]);

  return (
    <div>
      <PageHeader
        eyebrow="Live Memory Capture"
        title="Passive activity recorder"
        description="Manual start/stop capture for screenshots, active windows, clipboard changes, selected file activity, and live session metadata."
        action={
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={startCapture}
              disabled={status.is_active || isBusy}
              className="flex items-center gap-2 rounded-lg bg-mintGlow px-4 py-3 text-sm font-bold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Play size={17} />
              Start
            </button>
            <button
              type="button"
              onClick={togglePause}
              disabled={!status.is_active || isBusy}
              className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm font-semibold text-slate-200 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Pause size={17} />
              {status.is_paused ? 'Resume' : 'Pause'}
            </button>
            <button
              type="button"
              onClick={stopCapture}
              disabled={!status.is_active || isBusy}
              className="flex items-center gap-2 rounded-lg border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm font-semibold text-red-200 transition hover:bg-red-500/20 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Square size={17} />
              Stop
            </button>
          </div>
        }
      />

      <div className="mb-5 grid gap-4 md:grid-cols-4">
        <section className="glass-panel rounded-lg p-4">
          <Activity size={21} className="mb-4 text-mintGlow" />
          <p className="text-sm text-slate-500">Memory Capture</p>
          <h3 className="mt-2 text-xl font-semibold">{status.is_active ? (status.is_paused ? 'Paused' : 'Active') : 'Stopped'}</h3>
        </section>
        <section className="glass-panel rounded-lg p-4">
          <Monitor size={21} className="mb-4 text-cyanGlow" />
          <p className="text-sm text-slate-500">Current App</p>
          <h3 className="mt-2 truncate text-xl font-semibold">{status.current_app || 'Waiting'}</h3>
        </section>
        <section className="glass-panel rounded-lg p-4">
          <Clock size={21} className="mb-4 text-warningGlow" />
          <p className="text-sm text-slate-500">Session Duration</p>
          <h3 className="mt-2 text-xl font-semibold">{duration}</h3>
        </section>
        <section className="glass-panel rounded-lg p-4">
          <Wifi size={21} className="mb-4 text-cyanGlow" />
          <p className="text-sm text-slate-500">Live Socket</p>
          <h3 className="mt-2 text-xl font-semibold">{socketStatus}</h3>
        </section>
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <section className="glass-panel rounded-lg p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="font-semibold">Live Screenshot Feed</h3>
              <p className="mt-1 text-sm text-slate-500">Screenshots are saved locally only while capture is active.</p>
            </div>
            <span className="rounded-lg border border-cyanGlow/20 bg-cyanGlow/10 px-3 py-1 text-xs font-semibold text-cyanGlow">
              {status.screenshot_count || screenshots.length} captured
            </span>
          </div>

          <div className="flex min-h-[330px] items-center justify-center overflow-hidden rounded-lg border border-white/10 bg-slate-950/50">
            {latestScreenshot ? (
              <img
                src={`${apiClient.baseUrl}/api/capture/screenshots/${latestScreenshot.id}/image?token=${encodeURIComponent(apiClient.getToken())}`}
                alt="Latest capture"
                className="max-h-[420px] w-full object-contain"
              />
            ) : (
              <div className="text-center text-slate-500">
                <Camera size={42} className="mx-auto mb-3 text-slate-600" />
                <p>No screenshots captured yet</p>
              </div>
            )}
          </div>
        </section>

        <section className="glass-panel rounded-lg p-5">
          <h3 className="font-semibold">Activity Stream</h3>
          <p className="mt-1 text-sm text-slate-500">Window switches, screenshots, clipboard, and file events.</p>
          <div className="thin-scrollbar mt-4 max-h-[430px] space-y-3 overflow-y-auto">
            {[...captureEvents, ...activity.map((item) => ({ type: item.activity_type, data: { title: item.title, details: item.details }, timestamp: item.created_at }))].slice(0, 20).map((event, index) => (
              <div key={`${event.timestamp}-${index}`} className="rounded-lg border border-white/10 bg-white/5 p-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-slate-100">{event.type}</p>
                  <span className="text-xs text-slate-500">{new Date(event.timestamp).toLocaleTimeString()}</span>
                </div>
                <p className="mt-2 line-clamp-2 text-sm text-slate-400">
                  {event.data?.window_title || event.data?.details || event.data?.preview || event.data?.title || event.data?.status || 'Live event received'}
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="glass-panel mt-5 rounded-lg p-5">
        <h3 className="font-semibold">Privacy Guardrails</h3>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          {['Manual Start/Stop only', 'Pause mode supported', 'Sensitive app exclusions', 'No browser history scraping'].map((item) => (
            <div key={item} className="rounded-lg border border-white/10 bg-white/5 p-3 text-sm text-slate-300">
              {item}
            </div>
          ))}
        </div>
        <p className="mt-4 text-sm text-slate-500">Logged in as {username || 'demo user when started'}.</p>
      </section>
    </div>
  );
}

export default LiveActivity;
