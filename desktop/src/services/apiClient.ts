export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8010";

type ApiErrorPayload = {
  detail?: unknown;
};

export async function parseApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response));
  }

  return response.json() as Promise<T>;
}

async function getApiErrorMessage(response: Response): Promise<string> {
  const fallback = `Backend local respondio con estado ${response.status}.`;
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return formatDetail(payload.detail) ?? fallback;
  } catch {
    return fallback;
  }
}

function formatDetail(detail: unknown): string | null {
  if (typeof detail === "string" && detail.trim().length > 0) {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: unknown };
    if (typeof first.msg === "string") {
      return first.msg;
    }
  }

  return null;
}
