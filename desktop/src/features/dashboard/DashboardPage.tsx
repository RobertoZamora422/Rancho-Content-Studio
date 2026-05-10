import { useOutletContext } from "react-router-dom";

import type { HealthCheckResult } from "../../types/health";

const workflowSteps = [
  "Crear evento",
  "Seleccionar carpeta",
  "Procesar",
  "Revisar",
  "Aprobar",
  "Exportar"
];

type DashboardContext = {
  healthCheck: HealthCheckResult;
};

export function DashboardPage() {
  const { healthCheck } = useOutletContext<DashboardContext>();
  const { health, status, error, refresh } = healthCheck;

  return (
    <section className="dashboard-view">
      <div className="page-heading">
        <p className="section-label">Rancho Flor Maria</p>
        <div>
          <h1>Rancho Content Studio</h1>
          <p>
            Base local para preparar contenido de eventos sin depender de la
            nube ni modificar archivos originales.
          </p>
        </div>
      </div>

      <div className="status-strip">
        <div>
          <p className="metric-label">Backend local</p>
          <strong className={`health-state ${status}`}>
            {status === "connected"
              ? "Conectado"
              : status === "checking"
                ? "Verificando"
                : "No disponible"}
          </strong>
        </div>
        <div>
          <p className="metric-label">Version API</p>
          <strong>{health?.version ?? "Sin respuesta"}</strong>
        </div>
        <button className="secondary-action" onClick={refresh} type="button">
          Verificar conexion
        </button>
      </div>

      {error ? <p className="inline-error">{error}</p> : null}

      <div className="workflow-grid" aria-label="Flujo principal">
        {workflowSteps.map((step, index) => (
          <article className="workflow-step" key={step}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <h2>{step}</h2>
          </article>
        ))}
      </div>

      <section className="foundation-panel">
        <p className="section-label">Fase actual</p>
        <h2>Base tecnica inicial</h2>
        <p>
          El proyecto queda preparado con FastAPI, SQLite, React, Vite, Tauri,
          rutas de navegacion y conexion visible con el backend local. Las fases
          de importacion, analisis visual, curacion, mejora y exportacion se
          implementaran encima de esta base.
        </p>
      </section>
    </section>
  );
}
