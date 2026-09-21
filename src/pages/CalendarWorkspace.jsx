import { useEffect, useState } from 'react';
import { Calendar as CalIcon, Clock, Plus, Sparkles, MapPin, CheckCircle2, ChevronRight } from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';

export default function CalendarWorkspace() {
  const { apiClient } = useBackend();
  const [events, setEvents] = useState([]);
  const [newTitle, setNewTitle] = useState('');
  const [newTime, setNewTime] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  async function loadEvents() {
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/os/calendar`);
      if (res.ok) {
        const data = await res.json();
        setEvents(data);
      }
    } catch {
      //
    }
  }

  useEffect(() => {
    loadEvents();
  }, []);

  async function handleAddEvent(e) {
    e?.preventDefault();
    if (!newTitle.trim()) return;
    setIsAdding(true);
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/os/calendar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newTitle.trim(),
          start_time: newTime || 'Today, 3:00 PM',
          end_time: 'Today, 4:00 PM',
          location: 'Lab / Conference',
          ai_insight: 'Synthesize research notes beforehand.'
        })
      });
      if (res.ok) {
        setNewTitle('');
        setNewTime('');
        await loadEvents();
      }
    } finally {
      setIsAdding(false);
    }
  }

  return (
    <div className="flex h-full w-full flex-col bg-[#111318] p-6 text-slate-100 font-sans select-none overflow-y-auto thin-scrollbar">
      <div className="mx-auto w-full max-w-4xl space-y-6">
        <div className="border-b border-white/10 pb-4">
          <div className="flex items-center gap-2">
            <CalIcon size={18} className="text-cyan-400" />
            <h2 className="text-base font-bold text-white uppercase tracking-wider font-mono">Calendar & Schedule Intelligence</h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">Timeline of academic evaluations, project meetings, and AI-predicted schedule insights.</p>
        </div>

        {/* Quick Add Event */}
        <form onSubmit={handleAddEvent} className="flex gap-2 rounded-2xl border border-white/10 bg-[#161820] p-2">
          <input
            type="text"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="Schedule event, project review, or deadline..."
            className="flex-1 bg-transparent px-3 text-xs text-white outline-none placeholder:text-slate-500 font-medium"
          />
          <input
            type="text"
            value={newTime}
            onChange={(e) => setNewTime(e.target.value)}
            placeholder="Time (e.g. 2:00 PM)"
            className="w-36 rounded-lg border border-white/10 bg-black/50 px-2.5 py-1 text-xs text-slate-200 outline-none"
          />
          <button
            type="submit"
            disabled={!newTitle.trim() || isAdding}
            className="flex items-center gap-1.5 rounded-xl bg-cyan-400 px-4 py-1 text-xs font-bold text-slate-950 transition hover:bg-cyan-300 disabled:opacity-40"
          >
            <Plus size={13} /> Add Event
          </button>
        </form>

        {/* Events Timeline */}
        <div className="space-y-3">
          {events.map((evt) => (
            <div key={evt.id} className="rounded-2xl border border-white/10 bg-[#161820] p-4 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-bold text-white">{evt.title}</h4>
                <span className="flex items-center gap-1 text-[11px] font-mono text-cyan-300">
                  <Clock size={12} /> {evt.start_time} - {evt.end_time}
                </span>
              </div>

              <div className="flex items-center gap-2 text-xs text-slate-400">
                <MapPin size={13} className="text-slate-500" />
                <span>{evt.location}</span>
                <span className="text-slate-600">·</span>
                <span className="text-purple-300">{evt.project_id}</span>
              </div>

              {evt.ai_insight && (
                <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/10 p-2.5 flex items-center gap-2 text-xs text-cyan-200">
                  <Sparkles size={13} className="text-cyan-400 shrink-0" />
                  <span>AI Schedule Insight: {evt.ai_insight}</span>
                </div>
              )}
            </div>
          ))}

          {events.length === 0 && (
            <p className="text-xs text-slate-500 italic py-6">No scheduled calendar events.</p>
          )}
        </div>
      </div>
    </div>
  );
}
