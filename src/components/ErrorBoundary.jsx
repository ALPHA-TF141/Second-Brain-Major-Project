import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ error, errorInfo });
    console.error('CRITICAL REACT RENDER ERROR CAUGHT:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-screen w-screen flex-col items-center justify-center bg-[#030712] p-8 text-slate-100 font-mono select-none">
          <div className="max-w-2xl w-full rounded-2xl border border-red-500/40 bg-red-950/20 p-6 shadow-2xl backdrop-blur-2xl space-y-4">
            <div className="flex items-center gap-3 text-red-400 border-b border-red-500/20 pb-3">
              <AlertTriangle size={24} className="animate-pulse shrink-0" />
              <div>
                <h2 className="text-sm font-bold uppercase tracking-wider">JARVIS Neural Core Diagnostic Exception</h2>
                <p className="text-[11px] text-slate-400">A runtime error occurred in the React view layer.</p>
              </div>
            </div>

            <div className="rounded-xl border border-white/10 bg-black/60 p-4 text-xs text-red-300 overflow-x-auto whitespace-pre-wrap leading-relaxed">
              {this.state.error && this.state.error.toString()}
            </div>

            {this.state.errorInfo && (
              <details className="text-[10px] text-slate-400">
                <summary className="cursor-pointer hover:text-white">Component Stack Trace</summary>
                <div className="mt-2 rounded bg-black/40 p-3 max-h-44 overflow-y-auto font-mono text-[9.5px]">
                  {this.state.errorInfo.componentStack}
                </div>
              </details>
            )}

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => window.location.reload()}
                className="flex items-center gap-2 rounded-xl bg-cyan-400 px-4 py-2 text-xs font-bold text-slate-950 transition hover:bg-cyan-300"
              >
                <RefreshCw size={13} />
                Restart Interface
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
