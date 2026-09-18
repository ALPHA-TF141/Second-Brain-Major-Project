import { useEffect, useState } from 'react';
import { Globe, Key, Link as LinkIcon, RefreshCw, Send, Sparkles, Youtube, Twitter, Instagram, CheckCircle2, AlertCircle } from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';

export default function SocialIngestionHub({ onIngested }) {
  const { apiClient } = useBackend();
  const [url, setUrl] = useState('');
  const [notes, setNotes] = useState('');
  const [isIngesting, setIsIngesting] = useState(false);
  const [status, setStatus] = useState(null);
  const [showConfig, setShowConfig] = useState(false);
  const [apifyToken, setApifyToken] = useState('');
  const [supadataKey, setSupadataKey] = useState('');
  const [isSavingKeys, setIsSavingKeys] = useState(false);
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

  async function saveKeys(e) {
    e?.preventDefault();
    setIsSavingKeys(true);
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/social/keys`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          apify_api_token: apifyToken,
          supadata_api_key: supadataKey
        })
      });
      if (res.ok) {
        await loadStatus();
        setShowConfig(false);
      }
    } catch (err) {
      console.warn('Could not save API keys:', err);
    } finally {
      setIsSavingKeys(false);
    }
  }

  return (
    <div className="glass-panel relative overflow-hidden rounded-2xl p-5 border border-cyanGlow/25 bg-gradient-to-r from-slate-950/85 via-[#070e24]/85 to-slate-950/85 shadow-2xl backdrop-blur-xl">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-cyanGlow/30 bg-cyanGlow/10 text-cyanGlow">
            <Globe size={19} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">Social Intel & Cloud Scraper</h3>
            <p className="text-xs text-slate-400">Ingest YouTube transcripts, Tweets, Instagram reels & Web research directly into memory.</p>
          </div>
        </div>

        {/* Integration Badges */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowConfig(true)}
            className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 text-xs font-semibold text-slate-300 transition hover:bg-white/10"
          >
            <Key size={12} className="text-cyanGlow" />
            <span>Connect Accounts</span>
          </button>

          <span className={`flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${status?.supadata_connected ? 'border border-mintGlow/30 bg-mintGlow/10 text-mintGlow' : 'border border-slate-700 bg-slate-800 text-slate-400'}`}>
            SupaData {status?.supadata_connected ? '●' : '○'}
          </span>
          <span className={`flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${status?.apify_connected ? 'border border-cyanGlow/30 bg-cyanGlow/10 text-cyanGlow' : 'border border-slate-700 bg-slate-800 text-slate-400'}`}>
            Apify {status?.apify_connected ? '●' : '○'}
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
              placeholder="Paste any YouTube video, Tweet, Instagram reel, or Research URL..."
              className="w-full rounded-xl border border-white/10 bg-black/60 py-2.5 pl-9 pr-4 text-xs text-slate-100 outline-none focus:border-cyanGlow"
            />
          </div>

          <button
            type="submit"
            disabled={isIngesting || !url.trim()}
            className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyanGlow to-mintGlow px-5 py-2.5 text-xs font-bold text-slate-950 shadow-glow transition hover:opacity-90 disabled:opacity-40 shrink-0"
          >
            {isIngesting ? <RefreshCw size={14} className="animate-spin" /> : <Sparkles size={14} />}
            {isIngesting ? 'Scraping & Synthesizing...' : 'Ingest to Brain'}
          </button>
        </div>

        {/* Quick Platform Icons */}
        <div className="flex items-center gap-4 text-[11px] text-slate-500">
          <span className="flex items-center gap-1 text-slate-400">
            <Youtube size={13} className="text-red-400" /> Full Transcripts
          </span>
          <span className="flex items-center gap-1 text-slate-400">
            <Twitter size={13} className="text-sky-400" /> Threads & Posts
          </span>
          <span className="flex items-center gap-1 text-slate-400">
            <Instagram size={13} className="text-pink-400" /> Reels & Captions
          </span>
          <span className="flex items-center gap-1 text-slate-400">
            <Globe size={13} className="text-mintGlow" /> Papers & Markdown
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

      {/* API Key Connection Modal */}
      {showConfig && (
        <div
          onClick={() => setShowConfig(false)}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-6 backdrop-blur-xl"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-lg rounded-2xl border border-white/20 bg-slate-950 p-6 shadow-2xl"
          >
            <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2.5">
                <Key className="text-cyanGlow" size={18} />
                <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wide">Connect Scraper Accounts</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowConfig(false)}
                className="rounded-lg bg-white/10 px-2.5 py-1 text-xs text-slate-400 hover:text-white"
              >
                Close
              </button>
            </div>

            <form onSubmit={saveKeys} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300">SupaData API Key (For Instant YouTube Transcripts & Web Markdown):</label>
                <input
                  type="password"
                  value={supadataKey}
                  onChange={(e) => setSupadataKey(e.target.value)}
                  placeholder="Paste your SupaData API Key..."
                  className="mt-1.5 w-full rounded-lg border border-white/10 bg-black/60 px-3.5 py-2 text-xs text-slate-100 outline-none focus:border-cyanGlow"
                />
                <p className="mt-1 text-[10px] text-slate-500">Get a free key from <a href="https://supadata.ai" target="_blank" rel="noreferrer" className="text-cyanGlow underline">supadata.ai</a>.</p>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">Apify API Token (For Instagram, Twitter/X, & LinkedIn Actors):</label>
                <input
                  type="password"
                  value={apifyToken}
                  onChange={(e) => setApifyToken(e.target.value)}
                  placeholder="apify_api_..."
                  className="mt-1.5 w-full rounded-lg border border-white/10 bg-black/60 px-3.5 py-2 text-xs text-slate-100 outline-none focus:border-cyanGlow"
                />
                <p className="mt-1 text-[10px] text-slate-500">Get a token from <a href="https://console.apify.com/account/integrations" target="_blank" rel="noreferrer" className="text-cyanGlow underline">console.apify.com</a>.</p>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowConfig(false)}
                  className="rounded-lg bg-white/10 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-white/15"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSavingKeys}
                  className="flex items-center gap-1.5 rounded-lg bg-cyanGlow px-5 py-2 text-xs font-bold text-slate-950 shadow-glow"
                >
                  {isSavingKeys ? <RefreshCw size={13} className="animate-spin" /> : <Sparkles size={13} />}
                  Save & Connect
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
