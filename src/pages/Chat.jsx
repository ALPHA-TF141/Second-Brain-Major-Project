import { useEffect, useRef, useState } from 'react';
import { Bot, Clock, Link2, MessageSquareText, SendHorizontal, Sparkles } from 'lucide-react';
import PageHeader from '../components/PageHeader.jsx';
import { useBackend } from '../context/BackendContext.jsx';
import { createChatSocket } from '../services/chatSocket.js';

const modes = [
  { id: 'summary', label: 'Summary' },
  { id: 'detailed', label: 'Detailed' },
  { id: 'timeline', label: 'Timeline' },
  { id: 'teaching', label: 'Teaching' },
  { id: 'coding', label: 'Coding' }
];

function Chat() {
  const { apiClient, loginDemo } = useBackend();
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Ask me about your captured sessions, OCR notes, coding work, research, or learning history.'
    }
  ]);
  const [conversations, setConversations] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [input, setInput] = useState('');
  const [mode, setMode] = useState('summary');
  const [references, setReferences] = useState([]);
  const [socketStatus, setSocketStatus] = useState('disconnected');
  const [isTyping, setIsTyping] = useState(false);
  const socketRef = useRef(null);
  const bottomRef = useRef(null);

  async function ensureLogin() {
    if (!apiClient.getToken()) await loginDemo();
  }

  async function loadConversations() {
    if (!apiClient.getToken()) return;
    apiClient.fetchConversations().then(setConversations).catch(() => setConversations([]));
  }

  function connectSocket() {
    socketRef.current?.close();
    const socket = createChatSocket({
      onOpen: () => setSocketStatus('connected'),
      onClose: () => setSocketStatus('disconnected'),
      onError: () => setSocketStatus('error'),
      onEvent: handleStreamEvent
    });
    socketRef.current = socket;
  }

  function handleStreamEvent(event) {
    if (event.type === 'conversation') {
      setConversationId(event.conversation_id);
      return;
    }
    if (event.type === 'references') {
      setReferences(event.items || []);
      return;
    }
    if (event.type === 'typing') {
      setIsTyping(event.status === 'started');
      return;
    }
    if (event.type === 'token') {
      setMessages((current) => {
        const copy = [...current];
        const last = copy[copy.length - 1];
        if (last?.role === 'assistant' && last.streaming) {
          last.content += event.token;
          return copy;
        }
        return [...copy, { role: 'assistant', content: event.token, streaming: true }];
      });
      return;
    }
    if (event.type === 'done') {
      setIsTyping(false);
      setMessages((current) => current.map((message) => ({ ...message, streaming: false })));
      loadConversations();
    }
  }

  async function sendMessage(event) {
    event?.preventDefault();
    const question = input.trim();
    if (!question) return;

    await ensureLogin();
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      connectSocket();
      await new Promise((resolve) => setTimeout(resolve, 350));
    }

    setMessages((current) => [...current, { role: 'user', content: question }]);
    setInput('');
    setReferences([]);
    setIsTyping(true);
    socketRef.current?.send(JSON.stringify({ question, conversation_id: conversationId, mode }));
  }

  async function loadConversation(id) {
    setConversationId(id);
    const history = await apiClient.fetchConversationMessages(id);
    setMessages(history.map((item) => ({ role: item.role, content: item.content })));
    const retrieved = await apiClient.fetchConversationRetrieved(id);
    setReferences(retrieved.map((item) => ({ memory_id: item.memory_id, score: Number(item.score || 0) })));
  }

  useEffect(() => {
    loadConversations();
    connectSocket();
    return () => socketRef.current?.close();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  return (
    <div>
      <PageHeader
        eyebrow="AI Memory Chat"
        title="Conversational RAG assistant"
        description="Ask questions about captured activity, OCR knowledge, reconstructed sessions, and semantic memories with streaming responses."
      />

      <div className="grid gap-5 xl:grid-cols-[260px_1fr_320px]">
        <aside className="glass-panel rounded-lg p-4">
          <div className="mb-4 flex items-center gap-2">
            <MessageSquareText size={18} className="text-cyanGlow" />
            <h3 className="font-semibold">Conversations</h3>
          </div>
          <button
            type="button"
            onClick={() => {
              setConversationId(null);
              setMessages([{ role: 'assistant', content: 'New memory chat ready.' }]);
              setReferences([]);
            }}
            className="mb-3 w-full rounded-lg border border-cyanGlow/30 bg-cyanGlow/10 px-3 py-2 text-sm font-semibold text-cyanGlow transition hover:bg-cyanGlow/20"
          >
            New Chat
          </button>
          <div className="thin-scrollbar max-h-[610px] space-y-2 overflow-y-auto">
            {conversations.map((conversation) => (
              <button
                type="button"
                key={conversation.id}
                onClick={() => loadConversation(conversation.id)}
                className={`w-full rounded-lg border p-3 text-left text-sm transition hover:bg-white/8 ${conversationId === conversation.id ? 'border-cyanGlow/40 bg-cyanGlow/10' : 'border-white/10 bg-white/5'}`}
              >
                <p className="line-clamp-1 font-medium text-slate-200">{conversation.title}</p>
                <p className="mt-1 text-xs text-slate-500">{conversation.mode}</p>
              </button>
            ))}
          </div>
        </aside>

        <section className="glass-panel flex min-h-[720px] flex-col rounded-lg">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-5 py-4">
            <div className="flex items-center gap-2 text-sm text-mintGlow">
              <Sparkles size={16} />
              Stream {socketStatus}
            </div>
            <div className="flex flex-wrap gap-2">
              {modes.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setMode(item.id)}
                  className={`rounded-lg border px-3 py-2 text-xs font-semibold transition ${mode === item.id ? 'border-mintGlow/30 bg-mintGlow/10 text-mintGlow' : 'border-white/10 bg-white/5 text-slate-400 hover:bg-white/10'}`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          <div className="thin-scrollbar flex-1 space-y-4 overflow-y-auto p-5">
            {messages.map((message, index) => (
              <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[820px] rounded-lg border px-4 py-3 text-sm leading-6 ${message.role === 'user' ? 'border-cyanGlow/25 bg-cyanGlow/12 text-slate-100' : 'border-white/10 bg-white/6 text-slate-300'}`}>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <Bot size={16} className="text-cyanGlow" />
                Second Brain is thinking...
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <form onSubmit={sendMessage} className="flex gap-3 border-t border-white/10 p-4">
            <input
              type="text"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask: What did I study yesterday?"
              className="min-w-0 flex-1 rounded-lg border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-cyanGlow/50"
            />
            <button type="submit" className="flex items-center gap-2 rounded-lg bg-cyanGlow px-4 py-3 text-sm font-bold text-slate-950 transition hover:bg-cyan-300">
              <SendHorizontal size={17} />
              Send
            </button>
          </form>
        </section>

        <aside className="glass-panel rounded-lg p-4">
          <div className="mb-4 flex items-center gap-2">
            <Link2 size={18} className="text-mintGlow" />
            <h3 className="font-semibold">Memory References</h3>
          </div>
          <div className="thin-scrollbar max-h-[420px] space-y-3 overflow-y-auto">
            {references.map((item, index) => (
              <div key={`${item.memory_id}-${index}`} className="rounded-lg border border-white/10 bg-white/5 p-3">
                <p className="text-sm font-semibold text-slate-100">Memory {item.memory_id}</p>
                {item.title && <p className="mt-1 line-clamp-2 text-sm text-slate-400">{item.title}</p>}
                {item.score !== undefined && <p className="mt-2 text-xs text-mintGlow">Score {Math.round(Number(item.score) * 100)}%</p>}
              </div>
            ))}
            {!references.length && <p className="rounded-lg border border-white/10 bg-white/5 p-4 text-sm text-slate-500">Retrieved memory citations will appear here.</p>}
          </div>

          <div className="mt-5 rounded-lg border border-white/10 bg-white/5 p-4">
            <div className="mb-3 flex items-center gap-2">
              <Clock size={17} className="text-warningGlow" />
              <h4 className="font-semibold">Try Asking</h4>
            </div>
            <div className="space-y-2 text-sm text-slate-400">
              {['What was I studying yesterday?', 'Summarize my OCR learning sessions.', 'When did I learn about FastAPI?', 'What coding work did I do last night?'].map((suggestion) => (
                <button key={suggestion} type="button" onClick={() => setInput(suggestion)} className="block w-full rounded-lg border border-white/10 bg-slate-950/40 p-2 text-left transition hover:bg-white/10">
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default Chat;
