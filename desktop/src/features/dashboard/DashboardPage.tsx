import { Link, useOutletContext } from "react-router-dom";

import type { HealthCheckResult } from "../../types/health";

const workflowSteps = [
  "Configurar carpeta local",
  "Crear evento",
  "Importar material",
  "Curar y mejorar",
  "Generar piezas",
  "Exportar y planificar"
];

const quickActions = [
  {
    description: "Crear o abrir eventos y continuar el flujo de importacion.",
    label: "Eventos",
    path: "/events"
  },
  {
    description: "Revisar medios, piezas y copies ya registrados.",
    label: "Biblioteca",
    path: "/library"
  },
  {
    description: "Aprobar piezas, copies y preparar paquetes finales.",
    label: "Piezas",
    path: "/pieces"
  },
  {
    description: "Planificar publicaciones manuales desde piezas aprobadas.",
    label: "Calendario",
    path: "/calendar"
  }
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
            Centro local para importar, revisar, mejorar y preparar contenido
            de eventos sin depender de la nube ni modificar archivos originales.
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
        <p className="section-label">Siguiente paso</p>
        <h2>Trabajar por evento</h2>
        <p>
          Empieza en Eventos para crear una carpeta de trabajo o continuar un
          evento existente. Desde el detalle se ejecutan importacion, analisis,
          curacion, mejoras y revision de jobs.
        </p>
        <Link className="link-action" to="/events">
          Abrir eventos
        </Link>
      </section>

      <section className="quick-action-grid" aria-label="Acciones principales">
        {quickActions.map((action) => (
          <Link className="quick-action-card" key={action.path} to={action.path}>
            <strong>{action.label}</strong>
            <span>{action.description}</span>
          </Link>
        ))}
      </section>
    </section>
  );
}
