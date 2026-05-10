export type ContentEvent = {
  id: number;
  name: string;
  event_type: string | null;
  event_date: string | null;
  folder_name: string | null;
  root_path: string | null;
  event_path: string | null;
  status: string;
  metadata_date_source: string | null;
  notes: string | null;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
};

export type EventListResponse = {
  items: ContentEvent[];
};

export type EventCreate = {
  name: string;
  event_type: string | null;
  event_date: string;
  notes: string | null;
};

export type EventUpdate = {
  name?: string;
  event_type?: string | null;
  event_date?: string;
  notes?: string | null;
};
