function StatusCard({ title, value, detail, accent = 'cyan' }) {
  const accentClasses = {
    cyan: 'text-cyanGlow bg-cyanGlow/10 border-cyanGlow/25',
    mint: 'text-mintGlow bg-mintGlow/10 border-mintGlow/25',
    amber: 'text-warningGlow bg-warningGlow/10 border-warningGlow/25'
  };

  return (
    <section className="glass-panel rounded-lg p-5 transition duration-200 hover:-translate-y-1">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-slate-400">{title}</p>
        <span className={`h-3 w-3 rounded-full border ${accentClasses[accent]}`} />
      </div>
      <h3 className="text-3xl font-semibold">{value}</h3>
      <p className="mt-3 text-sm leading-6 text-slate-400">{detail}</p>
    </section>
  );
}

export default StatusCard;
