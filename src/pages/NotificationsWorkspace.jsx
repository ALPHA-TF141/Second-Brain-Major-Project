import { useState } from 'react';
import { Bell, Sparkles, CheckCircle2, AlertCircle, Clock, Filter, Trash2 } from 'lucide-react';

export default function NotificationsWorkspace() {
  const [filter, setFilter] = useState('all'); // 'all' | 'important' | 'unread' | 'ai_filtered'
  const [notifications, setNotifications] = useState([
    {
      id: 1,
      title: 'Assignment Deadline Detected by AI',
      message: 'Prof. Sharma emailed: Submit IEEE conference proposal before Friday 5:00 PM.',
      timestamp: 'Today, 9:42 AM',
      type: 'important',
      unread: true,
      aiFiltered: true
    },
    {
      id: 2,
      title: 'Autonomous GitHub Memory Vault Sync Complete',
      message: 'Committed and pushed 4 new knowledge cards and 80KB WebP hero captures to your repository.',
      timestamp: 'Today, 8:15 AM',
      type: 'system',
      unread: false,
      aiFiltered: true
    },
    {
      id: 3,
      title: 'Proactive Insight Collision Formed',
      message: 'Active coding session in VS Code (memory.py) linked with research paper on arXiv.',
      timestamp: 'Yesterday, 4:20 PM',
      type: 'important',
      unread: false,
      aiFiltered: true
    },
    {
      id: 4,
      title: 'Sub-Second YouTube Transcript Extraction',
      message: 'Extracted 983 words of spoken transcript in 0.98s and compiled into Master Topic Wiki.',
      timestamp: 'Yesterday, 2:10 PM',
      type: 'system',
      unread: false,
      aiFiltered: false
    }
  ]);

  const filtered = notifications.filter(n => {
    if (filter === 'important') return n.type === 'important';
    if (filter === 'unread') return n.unread;
    if (filter === 'ai_filtered') return n.aiFiltered;
    return true;
  });

  return (
    <div className="flex h-full w-full flex-col bg-[#111318] p-6 text-slate-100 font-sans select-none overflow-y-auto thin-scrollbar">
      <div className="mx-auto w-full max-w-4xl space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Bell size={18} className="text-cyan-400" />
              <h2 className="text-base font-bold text-white uppercase tracking-wider font-mono">Notification Center</h2>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">AI-filtered intelligence alerts, deadlines, and autonomous background milestones.</p>
          </div>

          <div className="flex items-center gap-1.5 rounded-xl border border-white/10 bg-black/40 p-1 text-xs">
            {['all', 'important', 'unread', 'ai_filtered'].map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setFilter(f)}
                className={`rounded-lg px-3 py-1 font-semibold capitalize transition ${filter === f ? 'bg-cyan-400 text-slate-950 shadow-glow font-bold' : 'text-slate-400 hover:text-white'}`}
              >
                {f.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2.5">
          {filtered.map((n) => (
            <div
              key={n.id}
              className={`rounded-2xl border p-4 transition ${
                n.unread ? 'border-cyan-500/30 bg-[#161822]' : 'border-white/5 bg-black/40 text-slate-400'
              }`}
            >
              <div className="flex items-center justify-between mb-1 text-[10px] font-mono">
                <span className={`font-bold uppercase ${n.type === 'important' ? 'text-amber-400' : 'text-cyan-400'}`}>
                  {n.type}
                </span>
                <span>{n.timestamp}</span>
              </div>
              <h4 className="text-xs font-bold text-white">{n.title}</h4>
              <p className="text-xs text-slate-300 mt-1 leading-relaxed">{n.message}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
