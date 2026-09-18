import { useEffect, useState } from 'react';
import { Globe, Key, Link as LinkIcon, RefreshCw, Send, Sparkles, Youtube, Twitter, Instagram, CheckCircle2, AlertCircle, ShieldCheck, UserCheck } from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';

export default function SocialIngestionHub({ onIngested }) {
  const { apiClient } = useBackend();
  const [url, setUrl] = useState('');
  const [notes, setNotes] = useState('');
  const [isIngesting, setIsIngesting] = useState(false);
  const [status, setStatus] = useState(null);
  const [showAccountModal, setShowAccountModal] = useState(false);
  const [igUsername, setIgUsername] = useState('');
  const [isSavingAccount, setIsSavingAccount] = useState(false);
  const [resultMessage, setResultMessage] = useState(null);

  async function loadStatus() {
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/social/status`);
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch {
      // Backend booting
    }
  }

  useEffect(() => {
    loadStatus();
  }, []);

  async function handleIngest(e) {
    e?.preventDefault();
    if (!url.trim()) return;
    setIsIngesting(true);
    setResultMessage(null);
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/social/ingest-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim(), user_notes: notes.trim() })
      });
      const data = await res.json();
      if (res.ok) {
        setResultMessage({
          type: 'success',
          text: `Synthesized ${data.platform.toUpperCase()}: ${data.title}`,
          cardId: data.card_id
        });
        setUrl('');
        setNotes('');
        onIngested?.(data);
      } else {
        setResultMessage({ type: 'error', text: data.detail || 'Ingestion failed' });
      }
    } catch (err) {
      setResultMessage({ type: 'error', text: String(err) });
    } finally {
      setIsIngesting(false);
    }
  }

  async function connectAccount(platform) {
    setIsSavingAccount(true);
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/social/connect-account`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          platform,
          username: igUsername.trim()
        })
      });
      if (res.ok) {
        await loadStatus();
        setShowAccountModal(false);
      }
    } catch (err) {
      console.warn('Could not save account session:', err);
    } finally {
      setIsSavingAccount(false);
    }
  }

  return (
    <div className="glass-panel relative overflow-hidden rounded-2xl p-5 border border-cyanGlow/25 bg-gradient-to-r from-slate-950/85 via-[#070e24]/85 to-slate-950/85 shadow-2xl backdrop-blur-xl">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-cyanGlow/30 bg-cyanGlow/10 text-cyanGlow shadow-glow">
            <Globe size={19} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">Native Social Media & Web Scraper</h3>
            <p className="text-xs text-slate-400">100% Free & Built-In: Ingest YouTube full transcripts, X posts, Instagram reels & research papers with zero paid SaaS fees.</p>
          </div>
        </div>

        {/* Free Native Engine Badges */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowAccountModal(true)}
            className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 text-xs font-semibold text-slate-300 transition hover:bg-white/10"
          >
            <Key size={12} className="text-cyanGlow" />
            <span>Link Accounts (Local)</span>
          </button>

          <span className="flex items-center gap-1 rounded-full border border-mintGlow/30 bg-mintGlow/10 px-2.5 py-0.5 text-[10px] font-bold text-mintGlow uppercase tracking-wider">
            <ShieldCheck size={11} /> 100% Free & Private
          </span>
        </div>
      </div>

      {/* URL Input Form */}
      <form onSubmit={handleIngest} className="space-y-3">
        <div className="flex flex-col gap-2 sm:flex-row">
          <div className="relative flex-1">
            <LinkIcon className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste any YouTube video, Tweet, Instagram reel, or Research article URL..."
              className="w-full rounded-xl border border-white/10 bg-black/60 py-2.5 pl-9 pr-4 text-xs text-slate-100 outline-none focus:border-cyanGlow"
            />
          </div>

          <button
            type="submit"
            disabled={isIngesting || !url.trim()}
            className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyanGlow to-mintGlow px-5 py-2.5 text-xs font-bold text-slate-950 shadow-glow transition hover:opacity-90 disabled:opacity-40 shrink-0"
          >
            {isIngesting ? <RefreshCw size={14} className="animate-spin" /> : <Sparkles size={14} />}
            {isIngesting ? 'Extracting & Transcribing...' : 'Ingest to Brain'}
          </button>
        </div>

        {/* Quick Platform Indicators */}
        <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-400">
          <span className="flex items-center gap-1 text-slate-300">
            <Youtube size={13} className="text-red-400" /> Native Audio Transcripts
          </span>
          <span className="flex items-center gap-1 text-slate-300">
            <Twitter size={13} className="text-sky-400" /> X Threads & Media
          </span>
          <span className="flex items-center gap-1 text-slate-300">
            <Instagram size={13} className="text-pink-400" /> Reels & Captions
          </span>
          <span className="flex items-center gap-1 text-slate-300">
            <Globe size={13} className="text-mintGlow" /> Clean Web Markdown
          </span>
        </div>
      </form>

      {/* Result Toast Notification */}
      {resultMessage && (
        <div className={`mt-3 flex items-center justify-between rounded-xl border p-3 text-xs ${resultMessage.type === 'success' ? 'border-mintGlow/30 bg-mintGlow/10 text-mintGlow' : 'border-red-400/30 bg-red-500/10 text-red-300'}`}>
          <div className="flex items-center gap-2">
            {resultMessage.type === 'success' ? <CheckCircle2 size={15} /> : <AlertCircle size={15} />}
            <span className="font-semibold">{resultMessage.text}</span>
          </div>
          <button type="button" onClick={() => setResultMessage(null)} className="text-slate-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {/* Account Connector Modal */}
      {showAccountModal && (
        <div
          onClick={() => setShowAccountModal(false)}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-6 backdrop-blur-xl"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-lg rounded-2xl border border-white/20 bg-slate-950 p-6 shadow-2xl"
          >
            <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2.5">
                <UserCheck className="text-cyanGlow" size={19} />
                <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wide">Connect Personal Accounts (100% Local)</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowAccountModal(false)}
                className="rounded-lg bg-white/10 px-2.5 py-1 text-xs text-slate-400 hover:text-white"
              >
                Close
              </button>
            </div>

            <div className="space-y-4 text-xs text-slate-300">
              <p className="leading-relaxed">
                Jarvis scrapes all public YouTube transcripts, Tweets, and articles automatically with zero credentials.
                To scrape your own private saved bookmarks or reels from Instagram or X, link your handle below (stored 100% on your laptop, zero cloud transmission):
              </p>

              <div>
                <label className="font-semibold text-slate-300">Instagram Handle / Profile:</label>
                <input
                  type="text"
                  value={igUsername}
                  onChange={(e) => setIgUsername(e.target.value)}
                  placeholder="e.g. your_instagram_username"
                  className="mt-1.5 w-full rounded-lg border border-white/10 bg-black/60 px-3.5 py-2 text-xs text-slate-100 outline-none focus:border-cyanGlow"
                />
              </div>

              <div className="rounded-xl border border-mintGlow/20 bg-mintGlow/10 p-3 text-[11px] text-mintGlow">
                ✓ <strong>Zero Paid APIs:</strong> No subscriptions to Apify or SupaData are ever required. All scraping runs natively from your machine.
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAccountModal(false)}
                  className="rounded-lg bg-white/10 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-white/15"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => connectAccount('instagram')}
                  disabled={isSavingAccount || !igUsername.trim()}
                  className="flex items-center gap-1.5 rounded-lg bg-cyanGlow px-5 py-2 text-xs font-bold text-slate-950 shadow-glow disabled:opacity-50"
                >
                  {isSavingAccount ? <RefreshCw size={13} className="animate-spin" /> : <Sparkles size={13} />}
                  Save Local Session
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
