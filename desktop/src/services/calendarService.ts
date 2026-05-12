import { API_BASE_URL, parseApiResponse } from "./apiClient";
import type {
  CalendarItem,
  CalendarItemCreate,
  CalendarItemListResponse,
  CalendarItemUpdate,
  CalendarMarkPublishedRequest,
  CalendarQuery
} from "../types/calendar";

export async function listCalendarItems(query: CalendarQuery = {}): Promise<CalendarItemListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/calendar${buildQuery(query)}`);
  return parseApiResponse<CalendarItemListResponse>(response);
}

export async function createCalendarItem(payload: CalendarItemCreate): Promise<CalendarItem> {
  const response = await fetch(`${API_BASE_URL}/api/calendar/items`, {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "POST"
  });
  return parseApiResponse<CalendarItem>(response);
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
  return parseApiResponse<CalendarItem>(response);
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
  return parseApiResponse<CalendarItem>(response);
}

export async function cancelCalendarItem(itemId: number): Promise<CalendarItem> {
  const response = await fetch(`${API_BASE_URL}/api/calendar/items/${itemId}`, {
    method: "DELETE"
  });
  return parseApiResponse<CalendarItem>(response);
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
