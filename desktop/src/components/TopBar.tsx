import { API_BASE_URL } from "../services/apiClient";
import type { HealthCheckResult } from "../types/health";

type TopBarProps = {
  healthCheck: HealthCheckResult;
};

export function TopBar({ healthCheck }: TopBarProps) {
  const { health, status, refresh } = healthCheck;

  return (
    <header className="top-bar">
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
        <p className="metric-label">API</p>
        <strong>{health?.version ?? "Sin respuesta"}</strong>
      </div>
      <div className="api-endpoint">
        <p className="metric-label">Endpoint</p>
        <code>{API_BASE_URL}</code>
      </div>
      <button className="secondary-action" onClick={refresh} type="button">
        Verificar
      </button>
    </header>
  );
}
