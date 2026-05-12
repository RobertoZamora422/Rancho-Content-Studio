import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { listEvents } from "../../services/eventService";
import { API_BASE_URL } from "../../services/healthService";
import {
  listLibraryCopies,
  listLibraryMedia,
  listLibraryPieces,
  searchLibrary
} from "../../services/libraryService";
import type { ContentEvent } from "../../types/events";
import type {
  LibraryCopyItem,
  LibraryMediaItem,
  LibraryPieceItem,
  LibraryQuery,
  LibrarySearchItem
} from "../../types/library";

type LibraryView = "media" | "pieces" | "copies" | "search";
type SelectedDetail =
  | { item: LibraryMediaItem; type: "media" }
  | { item: LibraryPieceItem; type: "piece" }
  | { item: LibraryCopyItem; type: "copy" }
  | { item: LibrarySearchItem; type: "search" };

const libraryViews: Array<{ label: string; value: LibraryView }> = [
  { label: "Medios", value: "media" },
  { label: "Piezas", value: "pieces" },
  { label: "Copies", value: "copies" },
  { label: "Busqueda global", value: "search" }
];

export function LibraryPage() {
  const [events, setEvents] = useState<ContentEvent[]>([]);
  const [view, setView] = useState<LibraryView>("media");
  const [eventId, setEventId] = useState("");
  const [eventType, setEventType] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [fileType, setFileType] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sourceType, setSourceType] = useState("");
  const [query, setQuery] = useState("");
  const [mediaItems, setMediaItems] = useState<LibraryMediaItem[]>([]);
  const [pieceItems, setPieceItems] = useState<LibraryPieceItem[]>([]);
  const [copyItems, setCopyItems] = useState<LibraryCopyItem[]>([]);
  const [searchItems, setSearchItems] = useState<LibrarySearchItem[]>([]);
  const [selectedDetail, setSelectedDetail] = useState<SelectedDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const eventTypeOptions = useMemo(
    () => Array.from(new Set(events.map((event) => event.event_type).filter(Boolean))).sort(),
    [events]
  );

  const totalItems =
    view === "media"
      ? mediaItems.length
      : view === "pieces"
        ? pieceItems.length
        : view === "copies"
          ? copyItems.length
          : searchItems.length;

  useEffect(() => {
    async function loadInitialEvents() {
      try {
        const response = await listEvents(true);
        setEvents(response.items);
      } catch (currentError) {
        setError(currentError instanceof Error ? currentError.message : "No se pudieron cargar eventos.");
      }
    }
    void loadInitialEvents();
  }, []);

  useEffect(() => {
    void loadLibrary();
  }, [view, eventId, eventType, dateFrom, dateTo, fileType, statusFilter, sourceType, query]);

  async function loadLibrary() {
    setLoading(true);
    setError(null);
    const filters = buildFilters();
    try {
      if (view === "media") {
        const response = await listLibraryMedia({ ...filters, source_type: sourceType || undefined });
        setMediaItems(response.items);
        setSelectedDetail(response.items[0] ? { item: response.items[0], type: "media" } : null);
      } else if (view === "pieces") {
        const response = await listLibraryPieces(filters);
        setPieceItems(response.items);
        setSelectedDetail(response.items[0] ? { item: response.items[0], type: "piece" } : null);
      } else if (view === "copies") {
        const response = await listLibraryCopies(filters);
        setCopyItems(response.items);
        setSelectedDetail(response.items[0] ? { item: response.items[0], type: "copy" } : null);
      } else {
        const response = await searchLibrary(filters);
        setSearchItems(response.items);
        setSelectedDetail(response.items[0] ? { item: response.items[0], type: "search" } : null);
      }
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudo consultar la biblioteca.");
    } finally {
      setLoading(false);
    }
  }

  function buildFilters(): LibraryQuery {
    return {
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      event_id: eventId ? Number(eventId) : undefined,
      event_type: eventType || undefined,
      file_type: fileType || undefined,
      limit: 120,
      q: query || undefined,
      status: statusFilter || undefined
    };
  }

  return (
    <section className="library-view">
      <div className="page-heading">
        <p className="section-label">Fase 15</p>
        <h1>Biblioteca</h1>
        <p>
          Consulta historica de medios, versiones, piezas y copies registrados en SQLite con rutas
          locales visibles y miniaturas cuando existen.
        </p>
      </div>

      {error ? <p className="inline-error">{error}</p> : null}

      <section className="library-filters">
        <div className="library-tabs">
          {libraryViews.map((option) => (
            <button
              className={`outline-action ${view === option.value ? "active-filter" : ""}`}
              key={option.value}
              onClick={() => setView(option.value)}
              type="button"
            >
              {option.label}
            </button>
          ))}
        </div>

        <div className="library-filter-grid">
          <label className="field-group">
            <span>Buscar</span>
            <input
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Evento, archivo, pieza o copy"
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
            <span>Tipo de evento</span>
            <select onChange={(event) => setEventType(event.target.value)} value={eventType}>
              <option value="">Todos</option>
              {eventTypeOptions.map((option) => (
                <option key={option} value={option ?? ""}>
                  {option}
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
          <label className="field-group">
            <span>Tipo</span>
            <select onChange={(event) => setFileType(event.target.value)} value={fileType}>
              <option value="">Todos</option>
              <option value="image">Imagen</option>
              <option value="video">Video</option>
              <option value="reel">Reel</option>
              <option value="carousel">Carrusel</option>
              <option value="story">Historia</option>
              <option value="single_post">Post individual</option>
              <option value="caption">Caption</option>
              <option value="hashtags">Hashtags</option>
            </select>
          </label>
          <label className="field-group">
            <span>Estado</span>
            <select onChange={(event) => setStatusFilter(event.target.value)} value={statusFilter}>
              <option value="">Todos</option>
              <option value="imported">Importado</option>
              <option value="user_selected">Seleccionado</option>
              <option value="completed">Mejorado</option>
              <option value="generated">Generado</option>
              <option value="approved">Aprobado</option>
              <option value="rejected">Rechazado</option>
              <option value="published">Publicado</option>
            </select>
          </label>
          <label className="field-group">
            <span>Origen</span>
            <select
              disabled={view !== "media"}
              onChange={(event) => setSourceType(event.target.value)}
              value={sourceType}
            >
              <option value="">Todos</option>
              <option value="original">Original</option>
              <option value="curated">Curado</option>
              <option value="enhanced">Mejorado</option>
            </select>
          </label>
        </div>
      </section>

      <section className="library-summary-row">
        <div>
          <span>Resultados</span>
          <strong>{loading ? "Consultando" : totalItems}</strong>
        </div>
        <div>
          <span>Eventos activos/archivados</span>
          <strong>{events.length}</strong>
        </div>
        <div>
          <span>Vista</span>
          <strong>{formatView(view)}</strong>
        </div>
      </section>

      {totalItems === 0 && !loading ? (
        <article className="empty-state">
          <h2>Sin resultados</h2>
          <p>Ajusta filtros o procesa eventos para que la biblioteca tenga contenido consultable.</p>
        </article>
      ) : null}

      <section className="library-layout">
        <div className="library-results-grid">{renderResults()}</div>
        <aside className="library-detail-panel">{renderDetail(selectedDetail)}</aside>
      </section>
    </section>
  );

  function renderResults() {
    if (view === "media") {
      return mediaItems.map((item) => (
        <button
          className="library-card"
          key={`${item.source_type}-${item.id}`}
          onClick={() => setSelectedDetail({ item, type: "media" })}
          type="button"
        >
          {renderThumbnail(item.thumbnail_url, item.media_type)}
          <span>{formatSourceType(item.source_type)}</span>
          <strong>{item.title}</strong>
          <small>{item.event_name}</small>
          <code>{item.local_path}</code>
        </button>
      ));
    }

    if (view === "pieces") {
      return pieceItems.map((item) => (
        <button
          className="library-card"
          key={`piece-${item.id}`}
          onClick={() => setSelectedDetail({ item, type: "piece" })}
          type="button"
        >
          {renderThumbnail(item.thumbnail_url, item.piece_type)}
          <span>{formatPieceType(item.piece_type)}</span>
          <strong>{item.title}</strong>
          <small>{item.event_name}</small>
          <small>
            {item.media_count} medios | {item.approved_copy_count} copies aprobados
          </small>
        </button>
      ));
    }

    if (view === "copies") {
      return copyItems.map((item) => (
        <button
          className="library-card text-card"
          key={`copy-${item.id}`}
          onClick={() => setSelectedDetail({ item, type: "copy" })}
          type="button"
        >
          <span>{formatCopyType(item.copy_type)}</span>
          <strong>{item.variant_label ?? item.copy_type}</strong>
          <small>{item.event_name}</small>
          <p>{item.body_preview}</p>
        </button>
      ));
    }

    return searchItems.map((item) => (
      <button
        className="library-card"
        key={`${item.entity_type}-${item.id}`}
        onClick={() => setSelectedDetail({ item, type: "search" })}
        type="button"
      >
        {renderThumbnail(item.thumbnail_url, item.entity_type)}
        <span>{formatSearchType(item.entity_type)}</span>
        <strong>{item.title}</strong>
        <small>{item.event_name}</small>
        <p>{item.subtitle}</p>
      </button>
    ));
  }
}

function renderDetail(detail: SelectedDetail | null) {
  if (!detail) {
    return (
      <article className="empty-state">
        <h2>Detalle</h2>
        <p>Selecciona un resultado para revisar rutas, estado y relacion con el evento.</p>
      </article>
    );
  }

  if (detail.type === "media") {
    const item = detail.item;
    return (
      <article className="detail-card">
        <p className="section-label">{formatSourceType(item.source_type)}</p>
        <h2>{item.title}</h2>
        {renderThumbnail(item.thumbnail_url, item.media_type)}
        <DetailRow label="Evento" value={item.event_name} />
        <DetailRow label="Fecha" value={formatDate(item.event_date)} />
        <DetailRow label="Tipo" value={`${item.media_type} ${item.file_type ?? ""}`} />
        <DetailRow label="Estado" value={item.status} />
        <DetailRow label="Archivo existe" value={item.file_exists ? "Si" : "No"} />
        <DetailRow label="Ruta local" value={item.local_path} />
        <Link className="link-action" to={`/events/${item.event_id}`}>
          Abrir evento
        </Link>
      </article>
    );
  }

  if (detail.type === "piece") {
    const item = detail.item;
    return (
      <article className="detail-card">
        <p className="section-label">{formatPieceType(item.piece_type)}</p>
        <h2>{item.title}</h2>
        {renderThumbnail(item.thumbnail_url, item.piece_type)}
        <DetailRow label="Evento" value={item.event_name} />
        <DetailRow label="Plataforma" value={item.target_platform ?? "Sin plataforma"} />
        <DetailRow label="Estado" value={item.status} />
        <DetailRow label="Medios" value={`${item.media_count}`} />
        <DetailRow label="Copies aprobados" value={`${item.approved_copy_count}`} />
        <DetailRow label="Ruta" value={item.absolute_output_path ?? item.output_path ?? "Sin archivo propio"} />
        <Link className="link-action" to={`/events/${item.event_id}`}>
          Abrir evento
        </Link>
      </article>
    );
  }

  if (detail.type === "copy") {
    const item = detail.item;
    return (
      <article className="detail-card">
        <p className="section-label">{formatCopyType(item.copy_type)}</p>
        <h2>{item.variant_label ?? item.copy_type}</h2>
        <DetailRow label="Evento" value={item.event_name} />
        <DetailRow label="Pieza" value={item.piece_title} />
        <DetailRow label="Estado" value={item.status} />
        <DetailRow label="Ruta" value={item.absolute_output_path ?? item.output_path ?? "Sin archivo"} />
        <p className="copy-preview">{item.body_preview}</p>
        <Link className="link-action" to={`/events/${item.event_id}`}>
          Abrir evento
        </Link>
      </article>
    );
  }

  const item = detail.item;
  return (
    <article className="detail-card">
      <p className="section-label">{formatSearchType(item.entity_type)}</p>
      <h2>{item.title}</h2>
      {renderThumbnail(item.thumbnail_url, item.entity_type)}
      <DetailRow label="Evento" value={item.event_name} />
      <DetailRow label="Estado" value={item.status} />
      <DetailRow label="Ruta" value={item.local_path ?? "Sin ruta"} />
      <p>{item.subtitle}</p>
      <Link className="link-action" to={`/events/${item.event_id}`}>
        Abrir evento
      </Link>
    </article>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="detail-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function renderThumbnail(url: string | null, fallback: string) {
  if (!url) {
    return <div className="library-thumb">{fallback.toUpperCase()}</div>;
  }
  return (
    <div className="library-thumb">
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

function formatView(value: LibraryView) {
  return libraryViews.find((view) => view.value === value)?.label ?? value;
}

function formatSourceType(value: string) {
  const labels: Record<string, string> = {
    curated: "Curado",
    enhanced: "Mejorado",
    original: "Original"
  };
  return labels[value] ?? value;
}

function formatSearchType(value: string) {
  if (value.startsWith("media:")) {
    return formatSourceType(value.replace("media:", ""));
  }
  if (value === "piece") {
    return "Pieza";
  }
  if (value === "copy") {
    return "Copy";
  }
  return value;
}

function formatPieceType(value: string) {
  const labels: Record<string, string> = {
    carousel: "Carrusel",
    promo_piece: "Pieza promocional",
    reel: "Reel",
    single_post: "Post individual",
    story: "Historia"
  };
  return labels[value] ?? value;
}

function formatCopyType(value: string) {
  const labels: Record<string, string> = {
    caption: "Caption",
    cover_text: "Texto de portada",
    hashtags: "Hashtags",
    reel_short_copy: "Copy breve",
    story_text: "Historia"
  };
  return labels[value] ?? value;
}

function formatDate(value: string | null) {
  if (!value) {
    return "Sin fecha";
  }
  return new Intl.DateTimeFormat("es-EC", { dateStyle: "medium" }).format(new Date(`${value}T00:00:00`));
}
