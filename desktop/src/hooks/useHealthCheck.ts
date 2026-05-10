import { useCallback, useEffect, useState } from "react";

import { getHealth } from "../services/healthService";
import type { HealthCheckResult, HealthResponse, HealthStatus } from "../types/health";

export function useHealthCheck(): HealthCheckResult {
  const [status, setStatus] = useState<HealthStatus>("checking");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const controller = new AbortController();
    setStatus("checking");
    setError(null);

    try {
      const response = await getHealth(controller.signal);
      setHealth(response);
      setStatus("connected");
    } catch (currentError) {
      setHealth(null);
      setStatus("unavailable");
      setError(
        currentError instanceof Error
          ? currentError.message
          : "No se pudo conectar con el backend local."
      );
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {
    health,
    status,
    error,
    refresh
  };
}
