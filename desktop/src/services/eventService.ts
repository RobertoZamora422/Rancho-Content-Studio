import { API_BASE_URL, parseApiResponse } from "./apiClient";
import type { ContentEvent, EventCreate, EventListResponse, EventUpdate } from "../types/events";

export async function listEvents(includeArchived = false): Promise<EventListResponse> {
  const searchParams = new URLSearchParams();
  if (includeArchived) {
    searchParams.set("include_archived", "true");
  }
  const query = searchParams.toString();
  const response = await fetch(`${API_BASE_URL}/api/events${query ? `?${query}` : ""}`);
  return parseApiResponse<EventListResponse>(response);
}

export async function createEvent(payload: EventCreate): Promise<ContentEvent> {
  const response = await fetch(`${API_BASE_URL}/api/events`, {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "POST"
  });
  return parseApiResponse<ContentEvent>(response);
}

export async function getEvent(eventId: number): Promise<ContentEvent> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}`);
  return parseApiResponse<ContentEvent>(response);
}

export async function updateEvent(eventId: number, payload: EventUpdate): Promise<ContentEvent> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}`, {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "PUT"
  });
  return parseApiResponse<ContentEvent>(response);
}

export async function archiveEvent(eventId: number): Promise<ContentEvent> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/archive`, {
    method: "POST"
  });
  return parseApiResponse<ContentEvent>(response);
}

export async function deleteEvent(eventId: number): Promise<ContentEvent> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}`, {
    method: "DELETE"
  });
  return parseApiResponse<ContentEvent>(response);
}
