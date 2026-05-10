import { API_BASE_URL } from "./healthService";
import type { ContentEvent, EventCreate, EventListResponse, EventUpdate } from "../types/events";

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

export async function listEvents(includeArchived = false): Promise<EventListResponse> {
  const searchParams = new URLSearchParams();
  if (includeArchived) {
    searchParams.set("include_archived", "true");
  }
  const query = searchParams.toString();
  const response = await fetch(`${API_BASE_URL}/api/events${query ? `?${query}` : ""}`);
  return parseResponse<EventListResponse>(response);
}

export async function createEvent(payload: EventCreate): Promise<ContentEvent> {
  const response = await fetch(`${API_BASE_URL}/api/events`, {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "POST"
  });
  return parseResponse<ContentEvent>(response);
}

export async function getEvent(eventId: number): Promise<ContentEvent> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}`);
  return parseResponse<ContentEvent>(response);
}

export async function updateEvent(eventId: number, payload: EventUpdate): Promise<ContentEvent> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}`, {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "PUT"
  });
  return parseResponse<ContentEvent>(response);
}

export async function archiveEvent(eventId: number): Promise<ContentEvent> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/archive`, {
    method: "POST"
  });
  return parseResponse<ContentEvent>(response);
}

export async function deleteEvent(eventId: number): Promise<ContentEvent> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}`, {
    method: "DELETE"
  });
  return parseResponse<ContentEvent>(response);
}
