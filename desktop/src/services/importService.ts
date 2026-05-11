import { API_BASE_URL } from "./healthService";
import type {
  CuratedMedia,
  CuratedMediaListResponse,
  CuratedMediaUpdate,
  CurationProcessResponse,
  ImportResponse,
  MediaSource,
  MetadataProcessResponse,
  OriginalMediaListResponse,
  ScanResponse,
  SimilarityDetectionResponse,
  SimilarityGroupListResponse,
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

export async function detectSimilarity(eventId: number): Promise<SimilarityDetectionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/detect-similarity`, {
    method: "POST"
  });
  return parseResponse<SimilarityDetectionResponse>(response);
}

export async function curateMedia(eventId: number): Promise<CurationProcessResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/curate-media`, {
    method: "POST"
  });
  return parseResponse<CurationProcessResponse>(response);
}

export async function listOriginalMedia(eventId: number): Promise<OriginalMediaListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/media/original`);
  return parseResponse<OriginalMediaListResponse>(response);
}

export async function listSimilarityGroups(eventId: number): Promise<SimilarityGroupListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/similarity-groups`);
  return parseResponse<SimilarityGroupListResponse>(response);
}

export async function listCuratedMedia(eventId: number): Promise<CuratedMediaListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/curated-media`);
  return parseResponse<CuratedMediaListResponse>(response);
}

export async function updateCuratedMedia(
  eventId: number,
  curatedId: number,
  payload: CuratedMediaUpdate
): Promise<CuratedMedia> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/curated-media/${curatedId}`, {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "PATCH"
  });
  return parseResponse<CuratedMedia>(response);
}

export async function listEventJobs(eventId: number): Promise<JobListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/jobs`);
  return parseResponse<JobListResponse>(response);
}
