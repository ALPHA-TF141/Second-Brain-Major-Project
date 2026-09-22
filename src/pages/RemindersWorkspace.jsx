import { useEffect, useState } from 'react';
import { Bell, Clock, Plus, CheckCircle2, Circle, RefreshCw, Repeat } from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';
import { apiFetch } from '../services/apiClient.js';

export default function RemindersWorkspace() {
  const { apiClient } = useBackend();
  const [reminders, setReminders] = useState([]);
  const [text, setText] = useState('');
  const [time, setTime] = useState('');
  const [recurring, setRecurring] = useState('None');
  const [isAdding, setIsAdding] = useState(false);

  async function loadReminders() {
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/os/reminders`);
      if (res.ok) {
        const data = await res.json();
        setReminders(data);
      }
    } catch {
      //
    }
  }

  useEffect(() => {
    loadReminders();
  }, []);

  async function handleToggle(id) {
    setReminders(prev => prev.map(r => r.id === id ? { ...r, status: r.status === 'active' ? 'completed' : 'active' } : r));
    try {
      await apiFetch(`${apiClient.baseUrl}/api/os/reminders/${id}/toggle`, { method: 'PUT' });
    } catch {
      //
    }
  }

  async function handleAdd(e) {
    e?.preventDefault();
    if (!text.trim()) return;
    setIsAdding(true);
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/os/reminders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text.trim(),
          remind_at: time || 'Today at 5:00 PM',
          recurring
        })
      });
      if (res.ok) {
        setText('');
        setTime('');
        await loadReminders();
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
            <Bell size={18} className="text-amber-400" />
            <h2 className="text-base font-bold text-white uppercase tracking-wider font-mono">Reminders & Cognitive Alarms</h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">Time-based alerts and recurring habit tracking managed by Jarvis.</p>
        </div>

        {/* Quick Add Reminder */}
        <form onSubmit={handleAdd} className="flex flex-wrap gap-2 rounded-2xl border border-white/10 bg-[#161820] p-2">
          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Set reminder (e.g. 'Submit project documentation')..."
            className="flex-1 min-w-[200px] bg-transparent px-3 text-xs text-white outline-none placeholder:text-slate-500 font-medium"
          />
          <input
            type="text"
            value={time}
            onChange={(e) => setTime(e.target.value)}
            placeholder="Time (e.g. 5:00 PM)"
            className="w-36 rounded-lg border border-white/10 bg-black/50 px-2.5 py-1 text-xs text-slate-200 outline-none"
          />
          <select
            value={recurring}
            onChange={(e) => setRecurring(e.target.value)}
            className="rounded-lg border border-white/10 bg-black/50 px-2 py-1 text-xs text-slate-300 outline-none"
          >
            <option value="None">One-Time</option>
            <option value="Daily">Daily</option>
            <option value="Weekly">Weekly</option>
          </select>
          <button
            type="submit"
            disabled={!text.trim() || isAdding}
            className="flex items-center gap-1.5 rounded-xl bg-amber-400 px-4 py-1 text-xs font-bold text-slate-950 transition hover:bg-amber-300 disabled:opacity-40"
          >
            <Plus size={13} /> Set
          </button>
        </form>

        {/* Reminders List */}
        <div className="space-y-2">
          {reminders.map((r) => {
            const isCompleted = r.status === 'completed';
            return (
              <div
                key={r.id}
                onClick={() => handleToggle(r.id)}
                className={`flex cursor-pointer items-center justify-between rounded-xl border p-3.5 transition ${
                  isCompleted ? 'border-white/5 bg-black/30 text-slate-500' : 'border-white/10 bg-[#161820] text-slate-200 hover:border-amber-400/40'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="text-amber-400">
                    {isCompleted ? <CheckCircle2 size={16} className="text-emerald-400" /> : <Circle size={16} />}
                  </div>
                  <div>
                    <span className={`text-xs font-medium block ${isCompleted ? 'line-through text-slate-500' : 'text-slate-100'}`}>
                      {r.text}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono flex items-center gap-2 mt-0.5">
                      <span className="flex items-center gap-1"><Clock size={10} /> {r.remind_at}</span>
                      {r.recurring !== 'None' && (
                        <span className="flex items-center gap-1 text-cyan-400"><Repeat size={10} /> {r.recurring}</span>
                      )}
                    </span>
                  </div>
                </div>

                <span className="text-[10px] font-mono text-slate-500 uppercase">{r.status}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
