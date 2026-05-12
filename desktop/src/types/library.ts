export type LibraryMediaItem = {
  id: number;
  source_type: string;
  event_id: number;
  event_name: string;
  event_type: string | null;
  event_date: string | null;
  title: string;
  filename: string;
  media_type: string;
  file_type: string | null;
  status: string;
  local_path: string;
  relative_path: string | null;
  thumbnail_url: string | null;
  file_exists: boolean;
  width: number | null;
  height: number | null;
  duration_seconds: number | null;
  original_media_id: number | null;
  curated_media_id: number | null;
  enhanced_media_id: number | null;
  created_at: string;
};

export type LibraryMediaListResponse = {
  items: LibraryMediaItem[];
};

export type LibraryPieceItem = {
  id: number;
  event_id: number;
  event_name: string;
  event_type: string | null;
  event_date: string | null;
  piece_type: string;
  title: string;
  purpose: string | null;
  target_platform: string | null;
  aspect_ratio: string | null;
  status: string;
  output_path: string | null;
  absolute_output_path: string | null;
  thumbnail_url: string | null;
  media_count: number;
  copy_count: number;
  approved_copy_count: number;
  created_at: string;
  updated_at: string;
};

export type LibraryPieceListResponse = {
  items: LibraryPieceItem[];
};

export type LibraryCopyItem = {
  id: number;
  piece_id: number;
  event_id: number;
  event_name: string;
  event_type: string | null;
  event_date: string | null;
  piece_title: string;
  copy_type: string;
  variant_label: string | null;
  body_preview: string;
  status: string;
  output_path: string | null;
  absolute_output_path: string | null;
  created_at: string;
  updated_at: string;
};

export type LibraryCopyListResponse = {
  items: LibraryCopyItem[];
};

export type LibrarySearchItem = {
  entity_type: string;
  id: number;
  event_id: number;
  event_name: string;
  title: string;
  subtitle: string | null;
  status: string;
  date: string | null;
  local_path: string | null;
  thumbnail_url: string | null;
};

export type LibrarySearchResponse = {
  items: LibrarySearchItem[];
};

export type LibraryQuery = {
  event_id?: number;
  date_from?: string;
  date_to?: string;
  event_type?: string;
  file_type?: string;
  piece_type?: string;
  copy_type?: string;
  status?: string;
  q?: string;
  source_type?: string;
  limit?: number;
};
