import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { eventSubdirectories } from "./eventFolders";
import { archiveEvent, deleteEvent, getEvent } from "../../services/eventService";
import { API_BASE_URL } from "../../services/healthService";
import {
  addSource,
  importMedia,
  listEventJobs,
  listOriginalMedia,
  listSources,
  processMetadataAndThumbnails,
  scanSources
} from "../../services/importService";
import type { ContentEvent } from "../../types/events";
import type {
  ImportResponse,
  MediaSource,
  MetadataProcessResponse,
  OriginalMedia,
  ScanResponse
} from "../../types/importing";
import type { ProcessingJob } from "../../types/jobs";

export function EventDetailPage() {
  const navigate = useNavigate();
  const { eventId } = useParams();
  const numericEventId = Number(eventId);
  const [event, setEvent] = useState<ContentEvent | null>(null);
  const [sources, setSources] = useState<MediaSource[]>([]);
  const [mediaItems, setMediaItems] = useState<OriginalMedia[]>([]);
  const [jobs, setJobs] = useState<ProcessingJob[]>([]);
  const [sourcePath, setSourcePath] = useState("");
  const [lastScan, setLastScan] = useState<ScanResponse | null>(null);
  const [lastImport, setLastImport] = useState<ImportResponse | null>(null);
  const [lastMetadata, setLastMetadata] = useState<MetadataProcessResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function loadEvent() {
    if (!Number.isInteger(numericEventId)) {
      setError("Identificador de evento invalido.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setEvent(await getEvent(numericEventId));
    } catch (currentError) {
      setError(
        currentError instanceof Error ? currentError.message : "No se pudo cargar el evento."
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadImportState(currentEventId: number) {
    try {
      const [sourceResponse, mediaResponse, jobResponse] = await Promise.all([
        listSources(currentEventId),
        listOriginalMedia(currentEventId),
        listEventJobs(currentEventId)
      ]);
      setSources(sourceResponse);
      setMediaItems(mediaResponse.items);
      setJobs(jobResponse.items);
    } catch (currentError) {
      setError(
        currentError instanceof Error
          ? currentError.message
          : "No se pudo cargar el estado de importacion."
      );
    }
  }

  useEffect(() => {
    void loadEvent();
  }, [numericEventId]);

  useEffect(() => {
    if (event) {
      void loadImportState(event.id);
    }
  }, [event?.id]);

  async function handleAddSource(formEvent: FormEvent<HTMLFormElement>) {
    formEvent.preventDefault();
    if (!event || sourcePath.trim().length === 0) {
      return;
    }

    setActionLoading(true);
    setError(null);
    setMessage(null);

    try {
      await addSource(event.id, sourcePath);
      setSourcePath("");
      setMessage("Fuente local registrada.");
      await loadImportState(event.id);
    } catch (currentError) {
      setError(
        currentError instanceof Error ? currentError.message : "No se pudo registrar la fuente."
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function handleScan() {
    if (!event) {
      return;
    }

    setActionLoading(true);
    setError(null);
    setMessage(null);

    try {
      const scan = await scanSources(event.id);
      setLastScan(scan);
      setMessage(`Escaneo completado: ${scan.supported_files} archivos compatibles.`);
      await loadImportState(event.id);
    } catch (currentError) {
      setError(
        currentError instanceof Error ? currentError.message : "No se pudo escanear la fuente."
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function handleImport() {
    if (!event) {
      return;
    }

    setActionLoading(true);
    setError(null);
    setMessage(null);

    try {
      const importResult = await importMedia(event.id);
      setLastImport(importResult);
      setMessage(
        `Importacion completada: ${importResult.imported_files} nuevos, ${importResult.skipped_files} omitidos.`
      );
      await loadImportState(event.id);
    } catch (currentError) {
      setError(
        currentError instanceof Error ? currentError.message : "No se pudo importar el material."
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function handleProcessMetadata() {
    if (!event) {
      return;
    }

    setActionLoading(true);
    setError(null);
    setMessage(null);

    try {
      const result = await processMetadataAndThumbnails(event.id);
      setLastMetadata(result);
      setMessage(
        `Metadatos y miniaturas procesados: ${result.metadata_updated} metadatos, ${result.thumbnails_generated} miniaturas.`
      );
      await loadImportState(event.id);
    } catch (currentError) {
      setError(
        currentError instanceof Error
          ? currentError.message
          : "No se pudieron procesar metadatos y miniaturas."
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function handleArchive() {
    if (!event) {
      return;
    }
    setActionLoading(true);
    setError(null);
    setMessage(null);
    try {
      setEvent(await archiveEvent(event.id));
      setMessage("Evento archivado. No se elimino ninguna carpeta local.");
    } catch (currentError) {
      setError(
        currentError instanceof Error ? currentError.message : "No se pudo archivar el evento."
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function handleLogicalDelete() {
    if (!event) {
      return;
    }
    setActionLoading(true);
    setError(null);
    setMessage(null);
    try {
      await deleteEvent(event.id);
      navigate("/events");
    } catch (currentError) {
      setError(
        currentError instanceof Error
          ? currentError.message
          : "No se pudo dar de baja el evento."
      );
    } finally {
      setActionLoading(false);
    }
  }

  return (
    <section className="event-detail-view">
      <Link className="back-link" to="/events">
        Volver a eventos
      </Link>

      {error ? <p className="inline-error">{error}</p> : null}
      {message ? <p className="inline-success">{message}</p> : null}

      {loading ? (
        <article className="empty-state">
          <h1>Cargando evento</h1>
        </article>
      ) : null}

      {!loading && event ? (
        <>
          <div className="page-heading">
            <p className="section-label">{event.event_type ?? "Evento"}</p>
            <h1>{event.name}</h1>
            <p>
              Carpeta local creada para este evento. Las siguientes fases usaran
              esta estructura para importar, procesar y exportar material.
            </p>
          </div>

          <section className="detail-grid">
            <article>
              <p className="metric-label">Fecha</p>
              <strong>{event.event_date ?? "Sin fecha"}</strong>
            </article>
            <article>
              <p className="metric-label">Estado</p>
              <strong>{event.status}</strong>
            </article>
            <article>
              <p className="metric-label">Fuente fecha metadata</p>
              <strong>{event.metadata_date_source ?? "Pendiente"}</strong>
            </article>
          </section>

          <section className="path-panel">
            <p className="metric-label">Ruta local del evento</p>
            <code>{event.event_path ?? "Sin ruta"}</code>
          </section>

          <section className="folder-grid">
            {eventSubdirectories.map((folder) => (
              <article className="folder-tile" key={folder}>
                <span>{/^\d{2}_/.test(folder) ? folder.slice(0, 2) : "--"}</span>
                <strong>{folder}</strong>
              </article>
            ))}
          </section>

          <section className="import-panel">
            <div className="section-heading-row">
              <div>
                <p className="section-label">Importacion</p>
                <h2>Fuente local</h2>
              </div>
              <div className="settings-actions">
                <button
                  className="outline-action"
                  disabled={actionLoading || sources.length === 0}
                  onClick={handleScan}
                  type="button"
                >
                  Escanear
                </button>
                <button
                  className="secondary-action"
                  disabled={actionLoading || sources.length === 0}
                  onClick={handleImport}
                  type="button"
                >
                  Importar a 01_Originales
                </button>
              </div>
            </div>

            <form className="source-form" onSubmit={handleAddSource}>
              <label className="field-group">
                <span>Carpeta fuente</span>
                <input
                  onChange={(formEvent) => setSourcePath(formEvent.target.value)}
                  placeholder="C:\\Fotos\\Evento"
                  value={sourcePath}
                />
              </label>
              <button
                className="secondary-action"
                disabled={actionLoading || sourcePath.trim().length === 0}
                type="submit"
              >
                Registrar fuente
              </button>
            </form>

            <div className="source-grid">
              {sources.length === 0 ? (
                <article className="empty-state">
                  <h2>No hay fuentes registradas</h2>
                  <p>Registra una carpeta local externa al evento para escanear e importar.</p>
                </article>
              ) : null}
              {sources.map((source) => (
                <article className="source-card" key={source.id}>
                  <p className="metric-label">Fuente</p>
                  <code>{source.source_path}</code>
                  <strong>{source.status}</strong>
                  <span>{source.notes ?? `${source.file_count} archivos compatibles`}</span>
                </article>
              ))}
            </div>

            {lastScan ? (
              <p className="import-summary">
                Escaneo job #{lastScan.job_id}: {lastScan.supported_files} compatibles,{" "}
                {lastScan.unsupported_files} no compatibles, {lastScan.failed_files} fallidos.
              </p>
            ) : null}
            {lastImport ? (
              <p className="import-summary">
                Importacion job #{lastImport.job_id}: {lastImport.imported_files} nuevos,{" "}
                {lastImport.skipped_files} omitidos, {lastImport.failed_files} fallidos.
              </p>
            ) : null}
          </section>

          <section className="media-panel">
            <div className="section-heading-row">
              <div>
                <p className="section-label">Material original</p>
                <h2>{mediaItems.length} archivos importados</h2>
              </div>
              <button
                className="secondary-action"
                disabled={actionLoading || mediaItems.length === 0}
                onClick={handleProcessMetadata}
                type="button"
              >
                Procesar metadatos y miniaturas
              </button>
            </div>
            {lastMetadata ? (
              <p className="import-summary">
                Metadata job #{lastMetadata.metadata_job_id} y thumbnails job #
                {lastMetadata.thumbnail_job_id}: {lastMetadata.metadata_updated} metadatos,{" "}
                {lastMetadata.thumbnails_generated} miniaturas,{" "}
                {lastMetadata.metadata_failed + lastMetadata.thumbnail_failed} fallidos.
              </p>
            ) : null}
            <div className="media-table">
              {mediaItems.length === 0 ? (
                <article className="empty-state">
                  <h2>Sin material importado</h2>
                  <p>Escanea e importa una fuente para llenar esta seccion.</p>
                </article>
              ) : null}
              {mediaItems.map((media) => (
                <article className="media-row" key={media.id}>
                  <div className="media-thumb">
                    {media.thumbnail_url ? (
                      <img
                        alt={`Miniatura de ${media.filename}`}
                        loading="lazy"
                        src={thumbnailSrc(media.thumbnail_url)}
                      />
                    ) : (
                      <span>{media.media_type === "video" ? "VIDEO" : "IMG"}</span>
                    )}
                  </div>
                  <div className="media-main-cell">
                    <p className="metric-label">{media.media_type}</p>
                    <h2>{media.filename}</h2>
                    <code>{media.relative_path ?? media.original_path}</code>
                  </div>
                  <div>
                    <p className="metric-label">Tamano</p>
                    <strong>{formatBytes(media.file_size_bytes)}</strong>
                  </div>
                  <div>
                    <p className="metric-label">Fecha captura</p>
                    <strong>{formatDateTime(media.capture_datetime)}</strong>
                    <span>{formatDateSource(media.date_source)}</span>
                  </div>
                  <div>
                    <p className="metric-label">Datos tecnicos</p>
                    <strong>{formatDimensions(media.width, media.height)}</strong>
                    <span>{formatDuration(media.duration_seconds)}</span>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="jobs-panel">
            <p className="section-label">Jobs recientes</p>
            {jobs.slice(0, 5).map((job) => (
              <article className="job-row" key={job.id}>
                <strong>{job.job_type}</strong>
                <span>{job.status}</span>
                <span>{job.progress_percent}%</span>
                <span>
                  {job.processed_items}/{job.total_items} procesados
                </span>
                <span>{job.failed_items} fallidos</span>
              </article>
            ))}
            {jobs.length === 0 ? <p>No hay jobs registrados para este evento.</p> : null}
          </section>

          <section className="settings-actions">
            <button
              className="outline-action"
              disabled={actionLoading || event.status === "archived"}
              onClick={handleArchive}
              type="button"
            >
              Archivar evento
            </button>
            <button
              className="danger-action"
              disabled={actionLoading}
              onClick={handleLogicalDelete}
              type="button"
            >
              Dar de baja logica
            </button>
          </section>
        </>
      ) : null}
    </section>
  );
}

function formatBytes(value: number | null) {
  if (value === null) {
    return "Sin dato";
  }
  if (value < 1024) {
    return `${value} B`;
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function thumbnailSrc(value: string) {
  if (value.startsWith("http")) {
    return value;
  }
  return `${API_BASE_URL}${value}`;
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "Pendiente";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function formatDateSource(value: string | null) {
  if (!value) {
    return "Fuente pendiente";
  }
  const labels: Record<string, string> = {
    event_date: "Fecha del evento",
    file_modified_time: "Fecha de archivo"
  };
  return labels[value] ?? value;
}

function formatDimensions(width: number | null, height: number | null) {
  if (!width || !height) {
    return "Sin resolucion";
  }
  return `${width} x ${height}`;
}

function formatDuration(value: number | null) {
  if (value === null) {
    return "Sin duracion";
  }
  return `${value.toFixed(1)} s`;
}
