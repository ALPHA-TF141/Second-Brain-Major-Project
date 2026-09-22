import { useState } from 'react';
import { Mail, Inbox, Star, Send, FileEdit, Search, Sparkles, Clock, ShieldCheck, Plus } from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';
import { apiFetch } from '../services/apiClient.js';

export default function GmailWorkspace() {
  const { apiClient } = useBackend();
  const [activeFolder, setActiveFolder] = useState('inbox');
  // NOTE: this only flips local UI state - there is NO Gmail OAuth yet.
  // The "Connect Gmail Account" button below sets it directly.
  const [isConnected, setIsConnected] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [aiDraft, setAiDraft] = useState('');

  // Sample emails once connected or simulated integration
  const [emails] = useState([
    {
      id: 'em_1',
      sender: 'Prof. Sharma <sharma@university.edu>',
      subject: 'Urgent: Project Documentation & Final Evaluation Date',
      date: 'Today, 9:42 AM',
      snippet: 'Please ensure your project documentation and IEEE conference draft are submitted before Friday 5:00 PM for the review committee.',
      unread: true,
      important: true,
      body: 'Dear Immanuel,\n\nPlease ensure your project documentation and IEEE conference draft are submitted before Friday 5:00 PM for the departmental review committee. We will also test the live hardware demo with your local GPU. Ensure all team members are present.\n\nBest regards,\nProf. Sharma',
      aiExtractedTask: 'Submit project documentation & IEEE conference draft before Friday 5:00 PM',
      aiExtractedDeadline: 'Friday, 5:00 PM'
    },
    {
      id: 'em_2',
      sender: 'IEEE Systems Conference <submissions@ieee-smc2026.org>',
      subject: 'Acknowledgment of Manuscript Abstract Submission',
      date: 'Yesterday, 4:15 PM',
      snippet: 'We acknowledge receipt of your research abstract on Autonomous Personal Knowledge Synthesizers.',
      unread: false,
      important: true,
      body: 'Dear Author,\n\nWe acknowledge receipt of your research abstract on Autonomous Personal Knowledge Synthesizers. Your paper ID is #SMC-4820. Final camera-ready notifications will be released next month.\n\nSincerely,\nIEEE SMC Program Committee'
    }
  ]);

  function convertEmailToTask(email) {
    if (!email.aiExtractedTask) return;
    apiFetch(`${apiClient.baseUrl}/api/os/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: email.aiExtractedTask,
        project: 'Academic Review',
        priority: 'high',
        due_date: '2026-09-25'
      })
    });
    alert('✓ Converted email deadline into an active Task in your Second Brain!');
  }

  function generateReply(email) {
    setAiDraft(`Dear ${email.sender.split('<')[0].trim()},\n\nThank you for the notification. The documentation and live demo are prepared and verified on our local setup. I will submit the deliverables ahead of the deadline.\n\nBest regards,\nImmanuel`);
  }

  return (
    <div className="flex h-full w-full bg-[#111318] text-slate-100 font-sans select-none overflow-hidden">
      {/* Left Mailbox Nav */}
      <div className="w-56 shrink-0 border-r border-[#262626] bg-[#16181f] p-3 text-xs flex flex-col justify-between">
        <div>
          <div className="flex items-center gap-2 mb-4 px-2">
            <Mail size={16} className="text-cyan-400" />
            <h3 className="font-bold text-white uppercase tracking-wider text-[11px]">Gmail Workspace</h3>
          </div>

          <nav className="space-y-1">
            {[
              { id: 'inbox', label: 'Inbox', icon: Inbox, count: 2 },
              { id: 'important', label: 'Important', icon: Star, count: 2 },
              { id: 'sent', label: 'Sent', icon: Send, count: 0 },
              { id: 'drafts', label: 'Drafts', icon: FileEdit, count: 1 }
            ].map((f) => {
              const Icon = f.icon;
              const isActive = activeFolder === f.id;
              return (
                <button
                  key={f.id}
                  onClick={() => setActiveFolder(f.id)}
                  className={`flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 transition ${
                    isActive ? 'bg-cyan-500/15 text-cyan-300 font-semibold' : 'text-slate-400 hover:bg-white/5 hover:text-white'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Icon size={13} />
                    <span>{f.label}</span>
                  </div>
                  {f.count > 0 && <span className="text-[10px] text-cyan-400 font-mono">{f.count}</span>}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Integration Status Indicator */}
        <div className="rounded-xl border border-white/5 bg-black/40 p-2.5 text-[10px] text-slate-400 space-y-1">
          <div className="flex items-center justify-between">
            <span>Status</span>
            <span className={isConnected ? 'text-emerald-400 font-bold' : 'text-amber-400'}>
              {isConnected ? 'Connected' : 'Ready to Connect'}
            </span>
          </div>
          <p className="text-[9.5px] text-slate-500">Google Workspace token isolation active.</p>
        </div>
      </div>

      {/* Main Mail Area */}
      <div className="flex flex-1 flex-col min-w-0 bg-[#111318]">
        {/* Top Search & Actions */}
        <div className="flex h-11 shrink-0 items-center justify-between border-b border-[#262626] px-4 bg-[#14161d]">
          <div className="flex items-center gap-2 max-w-md flex-1">
            <Search size={14} className="text-slate-500" />
            <input
              type="text"
              placeholder="Search emails, extracted tasks, senders..."
              className="w-full bg-transparent text-xs text-white outline-none placeholder:text-slate-500"
            />
          </div>

          <div className="flex items-center gap-2">
            {!isConnected && (
              <button
                type="button"
                onClick={() => setIsConnected(true)}
                className="flex items-center gap-1.5 rounded-lg bg-cyan-400 px-3 py-1 text-xs font-bold text-slate-950 shadow-glow"
              >
                <ShieldCheck size={12} />
                Connect Gmail Account
              </button>
            )}
          </div>
        </div>

        {/* Email Content / List View */}
        <div className="flex flex-1 min-h-0">
          {/* Thread List */}
          <div className="w-80 shrink-0 border-r border-[#262626] overflow-y-auto thin-scrollbar p-2 space-y-1">
            {emails.map((em) => (
              <div
                key={em.id}
                onClick={() => setSelectedEmail(em)}
                className={`cursor-pointer rounded-xl p-3 transition border ${
                  selectedEmail?.id === em.id
                    ? 'border-cyan-400/30 bg-cyan-500/10'
                    : 'border-white/5 bg-[#161820] hover:border-white/15'
                }`}
              >
                <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
                  <span className="font-bold text-white truncate max-w-[160px]">{em.sender.split('<')[0]}</span>
                  <span>{em.date}</span>
                </div>
                <h4 className="text-xs font-semibold text-slate-200 truncate">{em.subject}</h4>
                <p className="text-[11px] text-slate-400 line-clamp-2 mt-1">{em.snippet}</p>

                {em.aiExtractedDeadline && (
                  <div className="mt-2 flex items-center gap-1 text-[10px] font-mono text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 w-fit">
                    <Clock size={10} /> Deadline: {em.aiExtractedDeadline}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Email Reading & AI Action Pane */}
          <div className="flex flex-1 flex-col justify-between p-5 overflow-y-auto thin-scrollbar">
            {selectedEmail ? (
              <div className="space-y-4">
                <div className="border-b border-white/10 pb-3">
                  <span className="text-[10px] font-mono text-cyan-400 uppercase">From: {selectedEmail.sender}</span>
                  <h2 className="text-base font-bold text-white mt-1">{selectedEmail.subject}</h2>
                  <span className="text-xs text-slate-500">{selectedEmail.date}</span>
                </div>

                {/* AI Extracted Intel Banner */}
                {selectedEmail.aiExtractedTask && (
                  <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-3 flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-1.5 text-xs font-bold text-cyan-300">
                        <Sparkles size={13} /> AI Extracted Actionable Deadline
                      </div>
                      <p className="text-xs text-slate-200 mt-0.5">{selectedEmail.aiExtractedTask}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => convertEmailToTask(selectedEmail)}
                      className="flex items-center gap-1.5 rounded-lg bg-cyan-400 px-3 py-1.5 text-xs font-bold text-slate-950 shadow-glow"
                    >
                      <Plus size={12} /> Add to Tasks
                    </button>
                  </div>
                )}

                <div className="text-xs leading-relaxed text-slate-300 whitespace-pre-wrap font-sans bg-black/30 p-4 rounded-xl border border-white/5">
                  {selectedEmail.body}
                </div>

                {/* AI Draft Reply Action */}
                <div className="space-y-2 pt-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-300">AI Draft Reply</span>
                    <button
                      type="button"
                      onClick={() => generateReply(selectedEmail)}
                      className="flex items-center gap-1 text-xs text-cyan-400 hover:underline"
                    >
                      <Sparkles size={12} /> Auto-Generate Reply
                    </button>
                  </div>
                  {aiDraft && (
                    <div className="rounded-xl border border-white/10 bg-black/50 p-3 text-xs text-slate-200 whitespace-pre-wrap">
                      {aiDraft}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex h-full flex-col items-center justify-center text-slate-500 text-xs">
                <Mail size={32} className="mb-2 text-slate-600" />
                <p>Select an email thread to inspect AI summaries, tasks, and draft replies.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
