import { useEffect, useState } from 'react';
import { Folder, FileText, Image as ImageIcon, Search, Download, ExternalLink, HardDrive, RefreshCw } from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';
import { apiFetch, readList } from '../services/apiClient.js';

export default function FilesWorkspace() {
  const { apiClient } = useBackend();
  const [cards, setCards] = useState([]);
  const [search, setSearch] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);

  async function loadFiles() {
    try {
      const res = await apiFetch(`${apiClient.baseUrl}/api/graph/vault/cards?limit=30`);
      if (res.ok) setCards(await readList(res));
    } catch {
      //
    }
  }

  useEffect(() => {
    loadFiles();
  }, []);

  const heroCaptures = (Array.isArray(cards) ? cards : []).filter(c => c.hero_image);

  return (
    <div className="flex h-full w-full flex-col bg-[#111318] p-6 text-slate-100 font-sans select-none overflow-y-auto thin-scrollbar">
      <div className="mx-auto w-full max-w-5xl space-y-6">
        <div className="border-b border-white/10 pb-4">
          <div className="flex items-center gap-2">
            <Folder size={18} className="text-cyan-400" />
            <h2 className="text-base font-bold text-white uppercase tracking-wider font-mono">Files & Memory Vault Artifacts</h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">Persistent visual evidence captures, documents, and generated markdown assets.</p>
        </div>

        {/* Hero Captures Grid */}
        <div className="space-y-3">
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
            <span>Preserved Hero Screen Captures (80KB WebP)</span>
            <span className="text-cyan-400 font-mono">{heroCaptures.length} Files</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {heroCaptures.map((c) => {
              const url = c.hero_image?.startsWith('http') ? c.hero_image : `${apiClient.baseUrl}/${c.hero_image?.replace(/\\/g, '/')}`;
              return (
                <div key={c.id} className="rounded-2xl border border-white/10 bg-[#161820] overflow-hidden group">
                  <div
                    onClick={() => setSelectedImage(url)}
                    className="relative h-36 w-full cursor-pointer bg-black"
                  >
                    <img src={url} alt={c.topic} className="h-full w-full object-cover group-hover:scale-105 transition" />
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
                      <span className="rounded-full bg-cyan-400 px-3 py-1 text-xs font-bold text-slate-950">View Full Image</span>
                    </div>
                  </div>
                  <div className="p-3">
                    <span className="text-[10px] text-cyan-300 font-bold uppercase">{c.domain}</span>
                    <h4 className="text-xs font-semibold text-white line-clamp-1 mt-0.5">{c.topic || c.window_title}</h4>
                    <p className="text-[10px] text-slate-500 font-mono mt-1">Stored in: {c.hero_image}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {selectedImage && (
        <div
          onClick={() => setSelectedImage(null)}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-6 backdrop-blur-xl"
        >
          <div className="relative max-h-[92vh] max-w-[92vw] overflow-hidden rounded-2xl border border-white/20 bg-slate-950 p-3 shadow-2xl">
            <img src={selectedImage} alt="Hero View" className="max-h-[84vh] w-auto rounded-xl object-contain" />
            <button
              type="button"
              onClick={() => setSelectedImage(null)}
              className="mt-3 rounded-lg bg-white/10 px-3.5 py-1.5 text-xs text-white"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
