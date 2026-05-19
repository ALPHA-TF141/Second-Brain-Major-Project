import { BellRing } from 'lucide-react';
import { useAssistant } from '../context/AssistantContext.jsx';

function NotificationPanel() {
  const { notifications } = useAssistant();

  return (
    <section className="glass-panel rounded-lg p-5">
      <div className="mb-4 flex items-center gap-2">
        <BellRing size={18} className="text-cyanGlow" />
        <h3 className="font-semibold">Notifications</h3>
      </div>
      <div className="space-y-3">
        {notifications.map((notification) => (
          <div key={notification.id} className="rounded-lg border border-white/10 bg-white/5 p-3">
            <p className="text-sm font-semibold text-slate-100">{notification.title}</p>
            <p className="mt-1 text-sm text-slate-400">{notification.message}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export default NotificationPanel;
