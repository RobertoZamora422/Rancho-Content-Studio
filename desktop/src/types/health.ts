export type HealthResponse = {
  status: "ok";
  app: string;
  version: string;
};

export type HealthStatus = "checking" | "connected" | "unavailable";
