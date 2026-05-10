export type JobLog = {
  id: number;
  job_id: number;
  original_media_id: number | null;
  level: string;
  message: string;
  file_path: string | null;
  details_json: string | null;
  created_at: string;
};

export type ProcessingJob = {
  id: number;
  event_id: number | null;
  job_type: string;
  status: string;
  progress_percent: number;
  total_items: number;
  processed_items: number;
  failed_items: number;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  logs: JobLog[];
};

export type JobListResponse = {
  items: ProcessingJob[];
};
