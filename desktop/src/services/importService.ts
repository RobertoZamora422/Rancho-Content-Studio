import { API_BASE_URL } from "./healthService";
import type {
  ImportResponse,
  MediaSource,
  MetadataProcessResponse,
  OriginalMediaListResponse,
  ScanResponse,
  VisualAnalysisProcessResponse
} from "../types/importing";
import type { JobListResponse } from "../types/jobs";

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

export async function listSources(eventId: number): Promise<MediaSource[]> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/sources`);
  return parseResponse<MediaSource[]>(response);
}

export async function addSource(eventId: number, sourcePath: string): Promise<MediaSource> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/sources`, {
    body: JSON.stringify({ source_path: sourcePath }),
    headers: {
      "Content-Type": "application/json"
    },
    method: "POST"
  });
  return parseResponse<MediaSource>(response);
}

export async function scanSources(eventId: number): Promise<ScanResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/scan`, {
    method: "POST"
  });
  return parseResponse<ScanResponse>(response);
}

export async function importMedia(eventId: number): Promise<ImportResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/import`, {
    method: "POST"
  });
  return parseResponse<ImportResponse>(response);
}

export async function processMetadataAndThumbnails(
  eventId: number
): Promise<MetadataProcessResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/process-metadata`, {
    method: "POST"
  });
  return parseResponse<MetadataProcessResponse>(response);
}

export async function analyzePhotos(eventId: number): Promise<VisualAnalysisProcessResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/analyze-photos`, {
    method: "POST"
  });
  return parseResponse<VisualAnalysisProcessResponse>(response);
}

export async function listOriginalMedia(eventId: number): Promise<OriginalMediaListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/media/original`);
  return parseResponse<OriginalMediaListResponse>(response);
}

export async function listEventJobs(eventId: number): Promise<JobListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/jobs`);
  return parseResponse<JobListResponse>(response);
}
