function PageHeader({ eyebrow, title, description, action }) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-cyanGlow">{eyebrow}</p>
        <h2 className="mt-2 text-3xl font-semibold text-white">{title}</h2>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">{description}</p>
      </div>
      {action}
    </div>
  );
}

export default PageHeader;
