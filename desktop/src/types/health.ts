export type HealthResponse = {
  status: "ok";
  app: string;
  version: string;
};

export type HealthStatus = "checking" | "connected" | "unavailable";

export type HealthCheckResult = {
  health: HealthResponse | null;
  status: HealthStatus;
  error: string | null;
  refresh: () => Promise<void>;
};
