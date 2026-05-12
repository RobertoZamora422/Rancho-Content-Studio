import { API_BASE_URL } from "./healthService";
import type {
  CalendarItem,
  CalendarItemCreate,
  CalendarItemListResponse,
  CalendarItemUpdate,
  CalendarMarkPublishedRequest,
  CalendarQuery
} from "../types/calendar";

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Backend local respondio con estado ${response.status}.`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        message = payload.detail;
      }
    } catch {
      // Keep the generic HTTP message.
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export async function listCalendarItems(query: CalendarQuery = {}): Promise<CalendarItemListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/calendar${buildQuery(query)}`);
  return parseResponse<CalendarItemListResponse>(response);
}

export async function createCalendarItem(payload: CalendarItemCreate): Promise<CalendarItem> {
  const response = await fetch(`${API_BASE_URL}/api/calendar/items`, {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "POST"
  });
  return parseResponse<CalendarItem>(response);
}

export async function updateCalendarItem(
  itemId: number,
  payload: CalendarItemUpdate
): Promise<CalendarItem> {
  const response = await fetch(`${API_BASE_URL}/api/calendar/items/${itemId}`, {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "PUT"
  });
  return parseResponse<CalendarItem>(response);
}

export async function markCalendarItemPublished(
  itemId: number,
  payload: CalendarMarkPublishedRequest
): Promise<CalendarItem> {
  const response = await fetch(`${API_BASE_URL}/api/calendar/items/${itemId}/mark-published`, {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "POST"
  });
  return parseResponse<CalendarItem>(response);
}

export async function cancelCalendarItem(itemId: number): Promise<CalendarItem> {
  const response = await fetch(`${API_BASE_URL}/api/calendar/items/${itemId}`, {
    method: "DELETE"
  });
  return parseResponse<CalendarItem>(response);
}

function buildQuery(query: CalendarQuery) {
  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== null && `${value}`.trim() !== "") {
      params.set(key, `${value}`);
    }
  });
  const serialized = params.toString();
  return serialized ? `?${serialized}` : "";
}
