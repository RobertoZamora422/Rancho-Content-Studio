import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  cancelCalendarItem,
  createCalendarItem,
  listCalendarItems,
  markCalendarItemPublished,
  updateCalendarItem
} from "../../services/calendarService";
import { listEvents } from "../../services/eventService";
import { API_BASE_URL } from "../../services/apiClient";
import { listLibraryPieces } from "../../services/libraryService";
import type { CalendarItem } from "../../types/calendar";
import type { ContentEvent } from "../../types/events";
import type { LibraryPieceItem } from "../../types/library";

const platforms = [
  { label: "Instagram", value: "instagram" },
  { label: "Facebook", value: "facebook" },
  { label: "TikTok", value: "tiktok" },
  { label: "WhatsApp Business", value: "whatsapp_business" },
  { label: "Google Photos", value: "google_photos" },
  { label: "Multiple", value: "multiple" },
  { label: "Otra", value: "other" }
];

const publicationStatuses = [
  { label: "Sin programar", value: "not_scheduled" },
  { label: "Programada", value: "scheduled" },
  { label: "Lista para publicar", value: "ready_to_publish" },
  { label: "Publicada", value: "published" },
  { label: "Cancelada", value: "cancelled" }
];

export function CalendarPage() {
  const [events, setEvents] = useState<ContentEvent[]>([]);
  const [pieces, setPieces] = useState<LibraryPieceItem[]>([]);
  const [items, setItems] = useState<CalendarItem[]>([]);
  const [eventId, setEventId] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [platformFilter, setPlatformFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [query, setQuery] = useState("");
  const [selectedItemId, setSelectedItemId] = useState<number | null>(null);
  const [draftPieceId, setDraftPieceId] = useState("");
  const [draftDate, setDraftDate] = useState("");
  const [draftTime, setDraftTime] = useState("09:00");
  const [draftPlatform, setDraftPlatform] = useState("instagram");
  const [draftStatus, setDraftStatus] = useState("scheduled");
  const [draftNotes, setDraftNotes] = useState("");
  const [draftPublishedUrl, setDraftPublishedUrl] = useState("");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const selectedItem = useMemo(
    () => items.find((item) => item.id === selectedItemId) ?? null,
    [items, selectedItemId]
  );

  const groupedItems = useMemo(() => groupCalendarItems(items), [items]);

  useEffect(() => {
    async function loadBaseData() {
      try {
        const [eventResponse, pieceResponse] = await Promise.all([
          listEvents(true),
          listLibraryPieces({ limit: 250, status: "approved" })
        ]);
        setEvents(eventResponse.items);
        setPieces(pieceResponse.items);
        setDraftPieceId(pieceResponse.items[0] ? `${pieceResponse.items[0].id}` : "");
      } catch (currentError) {
        setError(currentError instanceof Error ? currentError.message : "No se pudieron cargar datos base.");
      }
    }
    void loadBaseData();
  }, []);

  useEffect(() => {
    void loadCalendar();
  }, [eventId, statusFilter, platformFilter, dateFrom, dateTo, query]);

  useEffect(() => {
    if (selectedItem) {
      setDraftPieceId(selectedItem.piece_id ? `${selectedItem.piece_id}` : "");
      setDraftDate(selectedItem.scheduled_date ?? "");
      setDraftTime(selectedItem.scheduled_time ?? "09:00");
      setDraftPlatform(selectedItem.platform ?? "instagram");
      setDraftStatus(selectedItem.status);
      setDraftNotes(selectedItem.notes ?? "");
      setDraftPublishedUrl(selectedItem.published_url ?? "");
    }
  }, [selectedItem?.id]);

  async function loadCalendar() {
    setLoading(true);
    setError(null);
    try {
      const response = await listCalendarItems({
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        event_id: eventId ? Number(eventId) : undefined,
        platform: platformFilter || undefined,
        q: query || undefined,
        status: statusFilter || undefined
      });
      setItems(response.items);
      setSelectedItemId((current) => {
        if (current && response.items.some((item) => item.id === current)) {
          return current;
        }
        return response.items[0]?.id ?? null;
      });
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudo cargar calendario.");
    } finally {
      setLoading(false);
    }
  }

  function clearDraft() {
    setSelectedItemId(null);
    setDraftPieceId(pieces[0] ? `${pieces[0].id}` : "");
    setDraftDate("");
    setDraftTime("09:00");
    setDraftPlatform("instagram");
    setDraftStatus("scheduled");
    setDraftNotes("");
    setDraftPublishedUrl("");
  }

  async function saveCalendarItem() {
    if (!draftPieceId) {
      setError("Selecciona una pieza aprobada para planificar.");
      return;
    }
    setActionLoading(true);
    setError(null);
    setMessage(null);
    try {
      const payload = {
        notes: draftNotes || null,
        piece_id: Number(draftPieceId),
        platform: draftPlatform,
        published_url: draftPublishedUrl || null,
        scheduled_date: draftDate || null,
        scheduled_time: draftTime || null,
        status: draftStatus
      };
      const saved = selectedItem
        ? await updateCalendarItem(selectedItem.id, payload)
        : await createCalendarItem(payload);
      setSelectedItemId(saved.id);
      setMessage(selectedItem ? "Item de calendario actualizado." : "Pieza planificada.");
      await loadCalendar();
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudo guardar calendario.");
    } finally {
      setActionLoading(false);
    }
  }

  async function markPublished() {
    if (!selectedItem) {
      return;
    }
    setActionLoading(true);
    setError(null);
    setMessage(null);
    try {
      const published = await markCalendarItemPublished(selectedItem.id, {
        notes: draftNotes || null,
        published_url: draftPublishedUrl || null
      });
      setSelectedItemId(published.id);
      setMessage("Publicacion marcada manualmente como publicada.");
      await loadCalendar();
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudo marcar como publicada.");
    } finally {
      setActionLoading(false);
    }
  }

  async function cancelSelected() {
    if (!selectedItem) {
      return;
    }
    setActionLoading(true);
    setError(null);
    setMessage(null);
    try {
      const cancelled = await cancelCalendarItem(selectedItem.id);
      setSelectedItemId(cancelled.id);
      setMessage("Programacion cancelada sin eliminar contenido.");
      await loadCalendar();
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudo cancelar programacion.");
    } finally {
      setActionLoading(false);
    }
  }

  return (
    <section className="calendar-view">
      <div className="page-heading">
        <p className="section-label">Agenda editorial</p>
        <h1>Calendario</h1>
        <p>
          Agenda local para planificar piezas aprobadas, registrar estado editorial y marcar
          publicaciones realizadas manualmente.
        </p>
      </div>

      {error ? <p className="inline-error">{error}</p> : null}
      {message ? <p className="inline-success">{message}</p> : null}

      <section className="calendar-filters">
        <label className="field-group">
          <span>Buscar</span>
          <input
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Evento, pieza o nota"
            value={query}
          />
        </label>
        <label className="field-group">
          <span>Evento</span>
          <select onChange={(event) => setEventId(event.target.value)} value={eventId}>
            <option value="">Todos</option>
            {events.map((event) => (
              <option key={event.id} value={event.id}>
                {event.name}
              </option>
            ))}
          </select>
        </label>
        <label className="field-group">
          <span>Estado</span>
          <select onChange={(event) => setStatusFilter(event.target.value)} value={statusFilter}>
            <option value="">Todos</option>
            {publicationStatuses.map((status) => (
              <option key={status.value} value={status.value}>
                {status.label}
              </option>
            ))}
          </select>
        </label>
        <label className="field-group">
          <span>Plataforma</span>
          <select onChange={(event) => setPlatformFilter(event.target.value)} value={platformFilter}>
            <option value="">Todas</option>
            {platforms.map((platform) => (
              <option key={platform.value} value={platform.value}>
                {platform.label}
              </option>
            ))}
          </select>
        </label>
        <label className="field-group">
          <span>Desde</span>
          <input onChange={(event) => setDateFrom(event.target.value)} type="date" value={dateFrom} />
        </label>
        <label className="field-group">
          <span>Hasta</span>
          <input onChange={(event) => setDateTo(event.target.value)} type="date" value={dateTo} />
        </label>
      </section>

      <section className="calendar-summary-row">
        <div>
          <span>Planificadas</span>
          <strong>{items.filter((item) => item.status === "scheduled").length}</strong>
        </div>
        <div>
          <span>Listas</span>
          <strong>{items.filter((item) => item.status === "ready_to_publish").length}</strong>
        </div>
        <div>
          <span>Publicadas</span>
          <strong>{items.filter((item) => item.status === "published").length}</strong>
        </div>
        <div>
          <span>Piezas aprobadas</span>
          <strong>{pieces.length}</strong>
        </div>
      </section>

      <section className="calendar-layout">
        <div className="agenda-panel">
          <div className="section-heading-row">
            <div>
              <p className="section-label">Agenda</p>
              <h2>{loading ? "Consultando calendario" : `${items.length} items`}</h2>
            </div>
            <button className="outline-action" onClick={clearDraft} type="button">
              Nuevo
            </button>
          </div>

          {items.length === 0 && !loading ? (
            <article className="empty-state">
              <h2>Sin publicaciones planificadas</h2>
              <p>Selecciona una pieza aprobada y define fecha, plataforma y estado.</p>
            </article>
          ) : null}

          {groupedItems.map((group) => (
            <article className="agenda-group" key={group.dateKey}>
              <h2>{group.label}</h2>
              <div className="agenda-list">
                {group.items.map((item) => (
                  <button
                    className={`agenda-item ${selectedItem?.id === item.id ? "active" : ""}`}
                    key={item.id}
                    onClick={() => setSelectedItemId(item.id)}
                    type="button"
                  >
                    {renderCalendarThumb(item)}
                    <div>
                      <span>{formatPlatform(item.platform)}</span>
                      <strong>{item.title}</strong>
                      <small>
                        {item.scheduled_time ?? "Sin hora"} | {formatPublicationStatus(item.status)}
                      </small>
                      <small>{item.event?.name ?? "Sin evento"}</small>
                    </div>
                  </button>
                ))}
              </div>
            </article>
          ))}
        </div>

        <aside className="calendar-editor-panel">
          <div className="section-heading-row">
            <div>
              <p className="section-label">{selectedItem ? "Editar item" : "Programar pieza"}</p>
              <h2>{selectedItem ? selectedItem.title : "Nueva publicacion"}</h2>
            </div>
            {selectedItem ? <strong>{formatPublicationStatus(selectedItem.status)}</strong> : null}
          </div>

          <label className="field-group">
            <span>Pieza aprobada</span>
            <select
              disabled={actionLoading || pieces.length === 0}
              onChange={(event) => setDraftPieceId(event.target.value)}
              value={draftPieceId}
            >
              {pieces.map((piece) => (
                <option key={piece.id} value={piece.id}>
                  {piece.title} | {piece.event_name}
                </option>
              ))}
            </select>
          </label>
          <div className="calendar-editor-grid">
            <label className="field-group">
              <span>Fecha</span>
              <input onChange={(event) => setDraftDate(event.target.value)} type="date" value={draftDate} />
            </label>
            <label className="field-group">
              <span>Hora</span>
              <input onChange={(event) => setDraftTime(event.target.value)} type="time" value={draftTime} />
            </label>
          </div>
          <div className="calendar-editor-grid">
            <label className="field-group">
              <span>Plataforma</span>
              <select onChange={(event) => setDraftPlatform(event.target.value)} value={draftPlatform}>
                {platforms.map((platform) => (
                  <option key={platform.value} value={platform.value}>
                    {platform.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="field-group">
              <span>Estado</span>
              <select onChange={(event) => setDraftStatus(event.target.value)} value={draftStatus}>
                {publicationStatuses.map((status) => (
                  <option key={status.value} value={status.value}>
                    {status.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label className="field-group">
            <span>URL publicada</span>
            <input
              onChange={(event) => setDraftPublishedUrl(event.target.value)}
              placeholder="Opcional"
              value={draftPublishedUrl}
            />
          </label>
          <label className="field-group">
            <span>Notas</span>
            <textarea onChange={(event) => setDraftNotes(event.target.value)} value={draftNotes} />
          </label>

          <div className="settings-actions">
            <button
              className="secondary-action"
              disabled={actionLoading || pieces.length === 0}
              onClick={saveCalendarItem}
              type="button"
            >
              {selectedItem ? "Guardar cambios" : "Programar pieza"}
            </button>
            <button
              className="outline-action"
              disabled={actionLoading || !selectedItem}
              onClick={markPublished}
              type="button"
            >
              Marcar publicado
            </button>
            <button
              className="danger-action"
              disabled={actionLoading || !selectedItem}
              onClick={cancelSelected}
              type="button"
            >
              Cancelar
            </button>
          </div>

          {selectedItem?.event_id ? (
            <Link className="link-action" to={`/events/${selectedItem.event_id}`}>
              Abrir evento origen
            </Link>
          ) : null}
        </aside>
      </section>
    </section>
  );
}

function groupCalendarItems(items: CalendarItem[]) {
  const groups = new Map<string, CalendarItem[]>();
  items.forEach((item) => {
    const key = item.scheduled_date ?? "sin-fecha";
    const current = groups.get(key) ?? [];
    current.push(item);
    groups.set(key, current);
  });
  return Array.from(groups.entries()).map(([dateKey, groupItems]) => ({
    dateKey,
    items: groupItems,
    label: dateKey === "sin-fecha" ? "Sin fecha" : formatDate(dateKey)
  }));
}

function renderCalendarThumb(item: CalendarItem) {
  const url = item.piece?.thumbnail_url;
  if (!url) {
    return <div className="agenda-thumb">{item.piece?.piece_type.toUpperCase() ?? "PIEZA"}</div>;
  }
  return (
    <div className="agenda-thumb">
      <img alt="" loading="lazy" src={thumbnailSrc(url)} />
    </div>
  );
}

function thumbnailSrc(value: string) {
  if (value.startsWith("http")) {
    return value;
  }
  return `${API_BASE_URL}${value}`;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("es-EC", { dateStyle: "full" }).format(new Date(`${value}T00:00:00`));
}

function formatPlatform(value: string | null) {
  return platforms.find((platform) => platform.value === value)?.label ?? value ?? "Sin plataforma";
}

function formatPublicationStatus(value: string) {
  return publicationStatuses.find((status) => status.value === value)?.label ?? value;
}
