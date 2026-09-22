import { useEffect, useState } from 'react';
import { CheckSquare, Circle, CheckCircle2, Clock, Plus, Sparkles, Filter, Trash2, Calendar, AlertCircle } from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';
import { apiFetch } from '../services/apiClient.js';

export default function TasksWorkspace() {
  const { apiClient } = useBackend();
  const [tasks, setTasks] = useState([]);
  const [filter, setFilter] = useState('all'); // 'all' | 'today' | 'upcoming' | 'completed' | 'ai_suggested'
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskProject, setNewTaskProject] = useState('Second Brain AI OS');
  const [newTaskPriority, setNewTaskPriority] = useState('medium');
  const [isAdding, setIsAdding] = useState(false);

  async function loadTasks() {
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/os/tasks`);
      if (res.ok) {
        const data = await res.json();
        setTasks(data);
      }
    } catch {
      //
    }
  }

  useEffect(() => {
    loadTasks();
  }, []);

  async function handleToggle(taskId, currentStatus) {
    const nextStatus = currentStatus === 'completed' ? 'pending' : 'completed';
    setTasks(prev => prev.map(t => t.id === taskId ? { ...t, status: nextStatus } : t));
    try {
      await apiFetch(`${apiClient.baseUrl}/api/os/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus })
      });
    } catch {
      //
    }
  }

  async function handleCreateTask(e) {
    e?.preventDefault();
    if (!newTaskTitle.trim()) return;
    setIsAdding(true);
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/os/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newTaskTitle.trim(),
          project: newTaskProject,
          priority: newTaskPriority,
          due_date: new Date().toISOString().split('T')[0]
        })
      });
      if (res.ok) {
        setNewTaskTitle('');
        await loadTasks();
      }
    } finally {
      setIsAdding(false);
    }
  }

  async function handleDelete(taskId) {
    setTasks(prev => prev.filter(t => t.id !== taskId));
    await apiFetch(`${apiClient.baseUrl}/api/os/tasks/${taskId}`, { method: 'DELETE' });
  }

  const filteredTasks = tasks.filter(t => {
    if (filter === 'completed') return t.status === 'completed';
    if (filter === 'today') return t.status !== 'completed';
    if (filter === 'ai_suggested') return t.ai_suggested;
    return true;
  });

  return (
    <div className="flex h-full w-full flex-col bg-[#111318] p-6 text-slate-100 font-sans select-none overflow-y-auto thin-scrollbar">
      <div className="mx-auto w-full max-w-5xl space-y-6">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <CheckSquare size={18} className="text-cyan-400" />
              <h2 className="text-base font-bold text-white uppercase tracking-wider font-mono">Tasks & Directives Management</h2>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">Autonomous task extraction, deadline alerts, and project-aligned priorities.</p>
          </div>

          <div className="flex items-center gap-1.5 rounded-xl border border-white/10 bg-black/40 p-1">
            {['all', 'today', 'completed', 'ai_suggested'].map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setFilter(f)}
                className={`rounded-lg px-3 py-1 text-xs font-semibold capitalize transition ${
                  filter === f ? 'bg-cyan-400 text-slate-950 shadow-glow font-bold' : 'text-slate-400 hover:text-white'
                }`}
              >
                {f.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Quick Add Task Bar */}
        <form onSubmit={handleCreateTask} className="flex flex-wrap items-center gap-2 rounded-2xl border border-white/10 bg-[#161820] p-2">
          <input
            type="text"
            value={newTaskTitle}
            onChange={(e) => setNewTaskTitle(e.target.value)}
            placeholder="Create an immediate task or directive..."
            className="flex-1 min-w-[240px] bg-transparent px-3 text-xs text-white outline-none placeholder:text-slate-500 font-medium"
          />

          <select
            value={newTaskProject}
            onChange={(e) => setNewTaskProject(e.target.value)}
            className="rounded-lg border border-white/10 bg-black/50 px-3 py-1.5 text-xs text-slate-300 outline-none"
          >
            <option value="Second Brain AI OS">Second Brain AI OS</option>
            <option value="Air Pollution Project">Air Pollution Project</option>
            <option value="Research Hub">Research Hub</option>
            <option value="General">General</option>
          </select>

          <select
            value={newTaskPriority}
            onChange={(e) => setNewTaskPriority(e.target.value)}
            className="rounded-lg border border-white/10 bg-black/50 px-3 py-1.5 text-xs text-slate-300 outline-none"
          >
            <option value="high">High Priority</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <button
            type="submit"
            disabled={!newTaskTitle.trim() || isAdding}
            className="flex items-center gap-1.5 rounded-xl bg-cyan-400 px-4 py-1.5 text-xs font-bold text-slate-950 transition hover:bg-cyan-300 disabled:opacity-40"
          >
            <Plus size={14} /> Add Task
          </button>
        </form>

        {/* Tasks List */}
        <div className="space-y-2">
          {filteredTasks.map((t) => {
            const isCompleted = t.status === 'completed';
            return (
              <div
                key={t.id}
                className={`flex items-center justify-between rounded-xl border p-3.5 transition ${
                  isCompleted
                    ? 'border-white/5 bg-black/30 text-slate-500'
                    : 'border-white/10 bg-[#161820] text-slate-200 hover:border-cyan-400/40'
                }`}
              >
                <div className="flex items-center gap-3 truncate">
                  <button
                    type="button"
                    onClick={() => handleToggle(t.id, t.status)}
                    className="text-cyan-400 hover:scale-110 transition shrink-0"
                  >
                    {isCompleted ? <CheckCircle2 size={16} className="text-emerald-400" /> : <Circle size={16} />}
                  </button>
                  <div className="truncate">
                    <span className={`text-xs font-medium block truncate ${isCompleted ? 'line-through text-slate-500' : 'text-slate-100'}`}>
                      {t.title}
                    </span>
                    <div className="flex items-center gap-2 text-[10px] text-slate-400 font-mono mt-0.5">
                      <span className="text-cyan-300">{t.project}</span>
                      {t.due_date && <span>· Due: {t.due_date}</span>}
                      {t.ai_suggested && (
                        <span className="flex items-center gap-1 text-amber-300 font-bold">
                          <Sparkles size={10} /> AI Suggested
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => handleDelete(t.id)}
                  className="p-1 text-slate-500 hover:text-red-400 transition ml-2"
                  title="Delete"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
