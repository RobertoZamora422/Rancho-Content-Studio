import type { EnhancedMedia } from "./importing";

export type PieceGenerationResponse = {
  job_id: number;
  total_available_media: number;
  pieces_created: number;
  pieces_skipped: number;
};

export type ContentPieceMedia = {
  id: number;
  piece_id: number;
  original_media_id: number | null;
  enhanced_media_id: number | null;
  position: number;
  role: string | null;
  notes: string | null;
  enhanced_media: EnhancedMedia | null;
};

export type ContentPiece = {
  id: number;
  event_id: number;
  piece_type: string;
  title: string;
  purpose: string | null;
  target_platform: string | null;
  aspect_ratio: string | null;
  output_path: string | null;
  status: string;
  metadata_json: string | null;
  created_at: string;
  updated_at: string;
  approved_at: string | null;
  rejected_at: string | null;
  media_items: ContentPieceMedia[];
};

export type ContentPieceListResponse = {
  items: ContentPiece[];
};

export type ContentPieceUpdate = {
  title?: string;
  purpose?: string | null;
  target_platform?: string | null;
  aspect_ratio?: string | null;
  status?: string;
  media_item_order?: number[];
};

export type ExportPackageRequest = {
  export_type: string;
  include_copies: boolean;
  write_event_date_metadata: boolean;
  group_by_type: boolean;
  include_summary: boolean;
};

export type ExportPackageItem = {
  id: number;
  package_id: number;
  content_piece_id: number | null;
  generated_copy_id: number | null;
  enhanced_media_id: number | null;
  item_type: string;
  output_path: string;
  absolute_output_path: string;
  item_order: number | null;
  metadata_written: boolean;
  metadata_status: string | null;
  error_message: string | null;
  created_at: string;
};

export type ExportPackage = {
  id: number;
  event_id: number;
  name: string;
  export_type: string;
  output_path: string;
  absolute_output_path: string;
  status: string;
  created_at: string;
  updated_at: string;
  finished_at: string | null;
  items: ExportPackageItem[];
};

export type ExportPackageRunResponse = {
  job_id: number;
  package: ExportPackage;
  total_pieces: number;
  media_exported: number;
  copies_exported: number;
  failed_items: number;
  summary_path: string | null;
};

export type ExportPackageListResponse = {
  items: ExportPackage[];
};

export type OpenExportFolderResponse = {
  package_id: number;
  path: string;
  opened: boolean;
  message: string;
};
