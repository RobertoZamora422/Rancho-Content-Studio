export type CalendarPieceSummary = {
  id: number;
  title: string;
  piece_type: string;
  target_platform: string | null;
  status: string;
  thumbnail_url: string | null;
};

export type CalendarEventSummary = {
  id: number;
  name: string;
  event_type: string | null;
  event_date: string | null;
};

export type CalendarItem = {
  id: number;
  event_id: number | null;
  piece_id: number | null;
  title: string;
  platform: string | null;
  scheduled_for: string | null;
  scheduled_date: string | null;
  scheduled_time: string | null;
  status: string;
  published_at: string | null;
  published_url: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  event: CalendarEventSummary | null;
  piece: CalendarPieceSummary | null;
};

export type CalendarItemListResponse = {
  items: CalendarItem[];
};

export type CalendarItemCreate = {
  piece_id: number;
  scheduled_date?: string | null;
  scheduled_time?: string | null;
  platform: string;
  status: string;
  title?: string | null;
  published_url?: string | null;
  notes?: string | null;
};

export type CalendarItemUpdate = {
  piece_id?: number | null;
  scheduled_date?: string | null;
  scheduled_time?: string | null;
  platform?: string | null;
  status?: string | null;
  title?: string | null;
  published_url?: string | null;
  notes?: string | null;
};

export type CalendarMarkPublishedRequest = {
  published_url?: string | null;
  notes?: string | null;
};

export type CalendarQuery = {
  event_id?: number;
  date_from?: string;
  date_to?: string;
  platform?: string;
  status?: string;
  q?: string;
};
