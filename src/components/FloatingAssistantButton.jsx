import { BotMessageSquare } from 'lucide-react';
import { useAssistant } from '../context/AssistantContext.jsx';

function FloatingAssistantButton() {
  const { isAssistantRunning, toggleAssistant } = useAssistant();

  return (
    <button
      type="button"
      onClick={toggleAssistant}
      className="fixed bottom-6 right-6 z-20 flex h-14 w-14 items-center justify-center rounded-xl border border-cyanGlow/30 bg-cyanGlow/15 text-cyanGlow shadow-glow transition hover:-translate-y-1 hover:bg-cyanGlow/20"
      aria-label="Toggle assistant"
      title={isAssistantRunning ? 'Stop assistant' : 'Start assistant'}
    >
      <span
        className={[
          'absolute -right-1 -top-1 h-3 w-3 rounded-full',
          isAssistantRunning ? 'status-pulse bg-mintGlow' : 'bg-slate-500'
        ].join(' ')}
      />
      <BotMessageSquare size={24} />
    </button>
  );
}

export default FloatingAssistantButton;
