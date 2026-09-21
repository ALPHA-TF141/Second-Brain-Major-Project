import { useEffect, useState } from 'react';
import { Activity, CheckCircle2, Clock, AlertTriangle, RefreshCw, Zap } from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';

export default function AgentActivityLog() {
  const { apiClient } = useBackend();
  const [activities, setActivities] = useState([]);
  const [selectedActivity, setSelectedActivity] = useState(null);

  async function loadActivities() {
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/os/activity`);
      if (res.ok) {
        const data = await res.json();
        setActivities(data);
      }
    } catch {
      //
    }
  }

  useEffect(() => {
    loadActivities();
    const interval = setInterval(loadActivities, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex h-full w-full flex-col bg-[#111318] p-6 text-slate-100 font-sans select-none overflow-y-auto thin-scrollbar">
      <div className="mx-auto w-full max-w-4xl space-y-6">
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Zap size={18} className="text-cyan-400" />
              <h2 className="text-base font-bold text-white uppercase tracking-wider font-mono">Agent Autonomous Activity Audit Log</h2>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">Chronological trail of background intelligence, knowledge ingestion, and sync actions.</p>
          </div>
          <button
            type="button"
            onClick={loadActivities}
            className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 hover:bg-white/10"
          >
            <RefreshCw size={12} /> Refresh Log
          </button>
        </div>

        {/* Timeline Log */}
        <div className="relative pl-6 border-l border-white/10 space-y-4">
          {activities.map((act) => (
            <div
              key={act.id}
              onClick={() => setSelectedActivity(act)}
              className="group relative cursor-pointer rounded-xl border border-white/5 bg-[#161820] p-3.5 transition hover:border-cyan-400/40 hover:bg-[#1a1e28]"
            >
              {/* Dot Marker on Timeline Line */}
              <div className="absolute -left-[31px] top-4 h-3 w-3 rounded-full border-2 border-[#111318] bg-cyan-400 group-hover:scale-125 transition" />

              <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono mb-1">
                <span className="text-cyan-300 font-bold uppercase">{act.type.replace('_', ' ')}</span>
                <span>{act.timestamp}</span>
              </div>

              <h4 className="text-xs font-bold text-slate-100">{act.title}</h4>
              <p className="mt-1 text-[11px] text-slate-400 leading-relaxed">{act.details}</p>

              <div className="mt-2 flex items-center justify-between text-[9px] text-slate-500 font-mono pt-1.5 border-t border-white/5">
                <span className="text-emerald-400 font-bold uppercase">Status: {act.status}</span>
                <span>Click for inspection</span>
              </div>
            </div>
          ))}

          {activities.length === 0 && (
            <p className="text-xs text-slate-500 italic py-6">Autonomous background actions will record here as you work.</p>
          )}
        </div>
      </div>
    </div>
  );
}
