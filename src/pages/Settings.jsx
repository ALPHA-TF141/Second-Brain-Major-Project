import PageHeader from '../components/PageHeader.jsx';

const settings = ['Launch on startup', 'Enable mock notifications', 'Use compact sidebar', 'Prepare Tamil mode'];

function Settings() {
  return (
    <div>
      <PageHeader
        eyebrow="Settings"
        title="Assistant preferences"
        description="Basic settings UI placeholders for the future desktop assistant configuration."
      />

      <section className="glass-panel rounded-lg p-5">
        <div className="space-y-3">
          {settings.map((setting, index) => (
            <label key={setting} className="flex items-center justify-between rounded-lg border border-white/10 bg-white/5 p-4">
              <span className="text-sm font-medium text-slate-200">{setting}</span>
              <input
                type="checkbox"
                defaultChecked={index < 2}
                className="h-5 w-5 accent-cyanGlow"
              />
            </label>
          ))}
        </div>
      </section>
    </div>
  );
}

export default Settings;
