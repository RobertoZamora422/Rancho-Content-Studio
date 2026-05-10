type ModulePageProps = {
  label: string;
  title: string;
  description: string;
  nextPhase: string;
};

export function ModulePage({ label, title, description, nextPhase }: ModulePageProps) {
  return (
    <section className="placeholder-view">
      <p className="section-label">{label}</p>
      <h1>{title}</h1>
      <p>{description}</p>
      <div className="module-state">
        <p className="metric-label">Estado</p>
        <strong>Preparado para {nextPhase}</strong>
      </div>
    </section>
  );
}
