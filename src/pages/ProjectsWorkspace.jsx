import { useEffect, useState } from 'react';
import { Rocket, CheckSquare, FileText, Folder, Mail, Network, Sparkles, Clock, ArrowRight, Layers } from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';
import { useNavigate } from 'react-router-dom';
import { apiFetch, readList } from '../services/apiClient.js';

export default function ProjectsWorkspace() {
  const { apiClient } = useBackend();
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState('proj_1');
  const [projectDetail, setProjectDetail] = useState(null);
  const [activeProjectTab, setActiveProjectTab] = useState('overview'); // 'overview' | 'tasks' | 'notes' | 'graph' | 'ai'

  async function loadProjects() {
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/os/projects`);
      if (res.ok) {
        const data = await readList(res);
        setProjects(data);
      }
    } catch {
      //
    }
  }

  async function loadDetail(id) {
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/os/projects/${id}`);
      if (res.ok) {
        const data = await res.json();
        setProjectDetail(data);
      }
    } catch {
      //
    }
  }

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      loadDetail(selectedProjectId);
    }
  }, [selectedProjectId]);

  return (
    <div className="flex h-full w-full bg-[#111318] text-slate-100 font-sans select-none overflow-hidden">
      {/* Left Projects Rail */}
      <div className="w-64 shrink-0 border-r border-[#262626] bg-[#161820] p-3 text-xs flex flex-col justify-between">
        <div>
          <div className="flex items-center gap-2 mb-4 px-2">
            <Rocket size={16} className="text-purple-400" />
            <h3 className="font-bold text-white uppercase tracking-wider text-[11px]">Active Projects</h3>
          </div>

          <div className="space-y-1.5">
            {projects.map((p) => {
              const isSelected = selectedProjectId === p.id;
              return (
                <div
                  key={p.id}
                  onClick={() => setSelectedProjectId(p.id)}
                  className={`cursor-pointer rounded-xl p-3 transition border ${
                    isSelected
                      ? 'border-purple-400/40 bg-purple-500/15 text-white'
                      : 'border-white/5 bg-black/40 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <h4 className="font-bold text-xs truncate">{p.name}</h4>
                  <p className="mt-1 text-[11px] text-slate-400 line-clamp-1">{p.description}</p>
                  <div className="mt-2 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                    <span className="text-purple-300 font-bold">{p.task_count} Tasks</span>
                    <span>Due: {p.deadline}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="rounded-xl border border-white/5 bg-black/40 p-2.5 text-[10px] text-slate-400 font-mono">
          <span>Unified Knowledge Cross-Link</span>
        </div>
      </div>

      {/* Main Project Workspace */}
      <div className="flex flex-1 flex-col min-w-0 bg-[#111318] overflow-hidden">
        {projectDetail ? (
          <div className="flex flex-1 flex-col min-h-0">
            {/* Project Header */}
            <div className="border-b border-[#262626] bg-[#14161d] p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <span className="text-[10px] font-mono text-purple-400 uppercase tracking-wider font-bold">
                    Project Workspace · {(projectDetail.status || 'active').toUpperCase()}
                  </span>
                  <h2 className="text-xl font-bold text-white mt-0.5">{projectDetail.name}</h2>
                  <p className="text-xs text-slate-400 mt-1 max-w-2xl">{projectDetail.description}</p>
                </div>

                <div className="flex items-center gap-2">
                  <span className="rounded-lg border border-purple-400/30 bg-purple-500/10 px-3 py-1 text-xs font-mono text-purple-300">
                    Deadline: {projectDetail.deadline}
                  </span>
                </div>
              </div>

              {/* Sub-tabs: Overview | Tasks | Notes | Files | Graph | Ask AI */}
              <div className="flex items-center gap-2 mt-4 pt-3 border-t border-white/5 text-xs">
                {[
                  { id: 'overview', label: 'Overview', icon: Rocket },
                  { id: 'tasks', label: `Tasks (${projectDetail.tasks?.length || 0})`, icon: CheckSquare },
                  { id: 'notes', label: 'Related Notes', icon: FileText },
                  { id: 'graph', label: 'Project Graph', icon: Network },
                  { id: 'ai', label: 'Ask AI About Project', icon: Sparkles }
                ].map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeProjectTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveProjectTab(tab.id)}
                      className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-medium transition ${
                        isActive
                          ? 'bg-purple-500/20 text-purple-300 border border-purple-400/30'
                          : 'text-slate-400 hover:text-white hover:bg-white/5'
                      }`}
                    >
                      <Icon size={13} />
                      <span>{tab.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Sub-tab Content Area */}
            <div className="flex-1 overflow-y-auto thin-scrollbar p-6">
              {activeProjectTab === 'overview' && (
                <div className="space-y-6 max-w-4xl">
                  {/* Linked Tags */}
                  <div>
                    <h4 className="text-xs font-mono uppercase text-slate-400 font-bold mb-2">Connected Knowledge Tags</h4>
                    <div className="flex flex-wrap gap-2">
                      {projectDetail.tags?.map((t) => (
                        <span key={t} className="rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-cyan-300">
                          #{t}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Summary Metric Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                    <div className="rounded-xl border border-white/5 bg-black/40 p-3">
                      <span className="text-slate-500 block text-[10px] uppercase">PROJECT HEALTH</span>
                      <span className="text-emerald-400 font-bold text-sm">Active & Progressing</span>
                    </div>
                    <div className="rounded-xl border border-white/5 bg-black/40 p-3">
                      <span className="text-slate-500 block text-[10px] uppercase">KNOWLEDGE ASSETS</span>
                      <span className="text-cyan-400 font-bold text-sm">{projectDetail.notes_count} Notes · {projectDetail.files_count} Files</span>
                    </div>
                    <div className="rounded-xl border border-white/5 bg-black/40 p-3">
                      <span className="text-slate-500 block text-[10px] uppercase">SCHEDULED REVIEWS</span>
                      <span className="text-amber-400 font-bold text-sm">{projectDetail.events?.length || 1} Upcoming Meeting</span>
                    </div>
                  </div>
                </div>
              )}

              {activeProjectTab === 'tasks' && (
                <div className="space-y-2 max-w-3xl">
                  {projectDetail.tasks?.map((t) => (
                    <div key={t.id} className="flex items-center justify-between rounded-xl border border-white/5 bg-black/40 p-3 text-xs">
                      <div>
                        <span className="font-semibold text-white block">{t.title}</span>
                        <span className="text-[10px] text-slate-500 font-mono">Priority: {(t.priority || 'medium').toUpperCase()} · Due: {t.due_date || 'No due date'}</span>
                      </div>
                      <span className="text-[10px] text-emerald-400 uppercase font-mono font-bold">● {t.status}</span>
                    </div>
                  ))}
                  {(!projectDetail.tasks || projectDetail.tasks.length === 0) && (
                    <p className="text-xs text-slate-500 italic">No tasks explicitly assigned to this project yet.</p>
                  )}
                </div>
              )}

              {activeProjectTab === 'graph' && (
                <div className="h-[60vh] rounded-2xl border border-white/10 overflow-hidden flex flex-col items-center justify-center text-center p-6 bg-black/40">
                  <Network size={36} className="text-purple-400 mb-2" />
                  <h4 className="text-sm font-bold text-white">Project Isolated Knowledge Sub-Graph</h4>
                  <p className="text-xs text-slate-400 mt-1 max-w-md">
                    Isolates conceptual dependencies, research datasets, and machine learning components linked specifically to {projectDetail.name}.
                  </p>
                  <button
                    type="button"
                    onClick={() => navigate('/knowledge-graph')}
                    className="mt-4 rounded-xl bg-purple-500 px-4 py-2 text-xs font-bold text-slate-950 shadow-glow"
                  >
                    Open in Global Knowledge Graph &rarr;
                  </button>
                </div>
              )}

              {activeProjectTab === 'ai' && (
                <div className="rounded-2xl border border-white/10 bg-black/40 p-5 space-y-3 max-w-2xl">
                  <div className="flex items-center gap-2 text-xs font-bold text-cyan-300">
                    <Sparkles size={14} />
                    <span>Ask Jarvis About {projectDetail.name}</span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Jarvis will query all connected notes, tasks, files, and emails for this project using local RAG.
                  </p>
                  <button
                    type="button"
                    onClick={() => navigate(`/chat`)}
                    className="flex items-center gap-2 rounded-xl bg-cyan-400 px-4 py-2 text-xs font-bold text-slate-950"
                  >
                    Launch Conversational Agent &rarr;
                  </button>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex flex-1 items-center justify-center text-xs text-slate-500">
            Select a project from the left rail.
          </div>
        )}
      </div>
    </div>
  );
}
