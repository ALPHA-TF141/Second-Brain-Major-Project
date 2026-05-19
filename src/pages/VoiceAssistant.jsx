import { Mic2, Radio, Volume2 } from 'lucide-react';
import PageHeader from '../components/PageHeader.jsx';
import { useAssistant } from '../context/AssistantContext.jsx';

function VoiceAssistant() {
  const { isListening, toggleListening, addNotification } = useAssistant();

  return (
    <div>
      <PageHeader
        eyebrow="Voice Assistant"
        title="Listening console"
        description="A visual foundation for wake word detection, speech recognition, Tamil voice commands, and spoken replies."
      />

      <section className="glass-panel grid gap-8 rounded-lg p-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="flex flex-col items-center justify-center rounded-lg border border-white/10 bg-slate-950/40 p-8">
          <div
            className={[
              'mb-6 flex h-36 w-36 items-center justify-center rounded-full border transition duration-300',
              isListening
                ? 'border-mintGlow/40 bg-mintGlow/10 text-mintGlow shadow-glow'
                : 'border-white/10 bg-white/5 text-slate-500'
            ].join(' ')}
          >
            <Mic2 size={48} />
          </div>
          <h3 className="text-2xl font-semibold">{isListening ? 'Listening' : 'Standby'}</h3>
          <p className="mt-3 text-center text-sm leading-6 text-slate-400">
            This is a fake listening indicator. Real audio capture can be connected in a later phase.
          </p>
          <button
            type="button"
            onClick={() => {
              toggleListening();
              addNotification('Voice mode updated', 'The listening indicator changed state.');
            }}
            className="mt-6 rounded-lg bg-mintGlow px-5 py-3 text-sm font-bold text-slate-950 transition hover:bg-emerald-300"
          >
            {isListening ? 'Stop Listening' : 'Start Listening'}
          </button>
        </div>

        <div className="grid gap-4">
          {[
            { icon: Radio, title: 'Wake word', text: 'Reserved for always-on activation logic.' },
            { icon: Volume2, title: 'Speech output', text: 'Reserved for text-to-speech responses.' },
            { icon: Mic2, title: 'Tamil commands', text: 'Reserved for Tamil speech interaction.' }
          ].map((item) => (
            <div key={item.title} className="rounded-lg border border-white/10 bg-white/5 p-5">
              <item.icon size={22} className="mb-4 text-cyanGlow" />
              <p className="font-semibold">{item.title}</p>
              <p className="mt-2 text-sm leading-6 text-slate-400">{item.text}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default VoiceAssistant;
