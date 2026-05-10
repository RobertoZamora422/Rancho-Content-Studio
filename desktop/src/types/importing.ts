export type MediaSource = {
  id: number;
  event_id: number;
  source_path: string;
  source_type: string;
  status: string;
  file_count: number;
  scanned_at: string | null;
  imported_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type ScanSourceSummary = {
  source_id: number;
  source_path: string;
  supported_files: number;
  unsupported_files: number;
  failed_files: number;
};

export type ScanResponse = {
  job_id: number;
  total_sources: number;
  supported_files: number;
  unsupported_files: number;
  failed_files: number;
  sources: ScanSourceSummary[];
};

export type ImportResponse = {
  job_id: number;
  imported_files: number;
  skipped_files: number;
  failed_files: number;
  total_files: number;
};

export type OriginalMedia = {
  id: number;
  event_id: number;
  source_id: number | null;
  original_path: string;
  relative_path: string | null;
  filename: string;
  extension: string | null;
  media_type: string;
  mime_type: string | null;
  file_size_bytes: number | null;
  checksum_sha256: string | null;
  capture_datetime: string | null;
  date_source: string | null;
  width: number | null;
  height: number | null;
  duration_seconds: number | null;
  thumbnail_path: string | null;
  status: string;
  original_exists: boolean;
  imported_at: string;
};

export type OriginalMediaListResponse = {
  items: OriginalMedia[];
};
