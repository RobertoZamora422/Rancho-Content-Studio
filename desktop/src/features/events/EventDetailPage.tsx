import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { eventSubdirectories } from "./eventFolders";
import { archiveEvent, deleteEvent, getEvent } from "../../services/eventService";
import { API_BASE_URL } from "../../services/apiClient";
import {
  addSource,
  analyzePhotos,
  curateMedia,
  detectSimilarity,
  enhancePhotos,
  enhanceVideos,
  importMedia,
  listCuratedMedia,
  listEnhancedMedia,
  listEventJobs,
  listOriginalMedia,
  listSimilarityGroups,
  listSources,
  processMetadataAndThumbnails,
  scanSources,
  updateCuratedMedia,
  updateEnhancedMedia
} from "../../services/importService";
import type { ContentEvent } from "../../types/events";
import type {
  CuratedMedia,
  CurationProcessResponse,
  EnhancedMedia,
  ImportResponse,
  MediaSource,
  MetadataProcessResponse,
  OriginalMedia,
  PhotoEnhancementResponse,
  ScanResponse,
  SimilarityDetectionResponse,
  SimilarityGroup,
  VideoEnhancementResponse,
  VisualAnalysisProcessResponse
} from "../../types/importing";
import type { ProcessingJob } from "../../types/jobs";

const enhancementPresets = [
  { label: "Natural premium", value: "natural_premium" },
  { label: "Calido elegante", value: "calido_elegante" },
  { label: "Color vivo fiesta", value: "color_vivo_fiesta" },
  { label: "Suave bodas", value: "suave_bodas" },
  { label: "Brillante XV", value: "brillante_xv" },
  { label: "Sobrio corporativo", value: "sobrio_corporativo" }
];

const videoProcessingModes = [
  { label: "Automatico", value: "auto" },
  { label: "Video completo", value: "full" },
  { label: "Segmento simple", value: "segment" }
];

export function EventDetailPage() {
  const navigate = useNavigate();
  const { eventId } = useParams();
  const numericEventId = Number(eventId);
  const [event, setEvent] = useState<ContentEvent | null>(null);
  const [sources, setSources] = useState<MediaSource[]>([]);
  const [mediaItems, setMediaItems] = useState<OriginalMedia[]>([]);
  const [similarityGroups, setSimilarityGroups] = useState<SimilarityGroup[]>([]);
  const [curatedItems, setCuratedItems] = useState<CuratedMedia[]>([]);
  const [enhancedItems, setEnhancedItems] = useState<EnhancedMedia[]>([]);
  const [jobs, setJobs] = useState<ProcessingJob[]>([]);
  const [sourcePath, setSourcePath] = useState("");
  const [enhancementPreset, setEnhancementPreset] = useState("natural_premium");
  const [videoEnhancementPreset, setVideoEnhancementPreset] = useState("natural_premium");
  const [videoProcessingMode, setVideoProcessingMode] = useState("auto");
  const [lastScan, setLastScan] = useState<ScanResponse | null>(null);
  const [lastImport, setLastImport] = useState<ImportResponse | null>(null);
  const [lastMetadata, setLastMetadata] = useState<MetadataProcessResponse | null>(null);
  const [lastAnalysis, setLastAnalysis] = useState<VisualAnalysisProcessResponse | null>(null);
  const [lastSimilarity, setLastSimilarity] = useState<SimilarityDetectionResponse | null>(null);
  const [lastCuration, setLastCuration] = useState<CurationProcessResponse | null>(null);
  const [lastEnhancement, setLastEnhancement] = useState<PhotoEnhancementResponse | null>(null);
  const [lastVideoEnhancement, setLastVideoEnhancement] =
    useState<VideoEnhancementResponse | null>(null);
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
      const [
        sourceResponse,
        mediaResponse,
        similarityResponse,
        curatedResponse,
        enhancedResponse,
        jobResponse
      ] = await Promise.all([
        listSources(currentEventId),
        listOriginalMedia(currentEventId),
        listSimilarityGroups(currentEventId),
        listCuratedMedia(currentEventId),
        listEnhancedMedia(currentEventId),
        listEventJobs(currentEventId)
      ]);
      setSources(sourceResponse);
      setMediaItems(mediaResponse.items);
      setSimilarityGroups(similarityResponse.items);
      setCuratedItems(curatedResponse.items);
      setEnhancedItems(enhancedResponse.items);
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

  async function handleAnalyzePhotos() {
    if (!event) {
      return;
    }

    setActionLoading(true);
    setError(null);
    setMessage(null);

    try {
      const result = await analyzePhotos(event.id);
      setLastAnalysis(result);
      setMessage(
        `Analisis visual completado: ${result.analyzed_photos} fotos analizadas, ${result.failed_photos} fallidas.`
      );
      await loadImportState(event.id);
    } catch (currentError) {
      setError(
        currentError instanceof Error
          ? currentError.message
          : "No se pudo ejecutar el analisis visual."
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function handleDetectSimilarity() {
    if (!event) {
      return;
    }

    setActionLoading(true);
    setError(null);
    setMessage(null);

    try {
      const result = await detectSimilarity(event.id);
      setLastSimilarity(result);
      setMessage(
        `Deteccion completada: ${result.exact_groups} grupos exactos y ${result.similar_groups} grupos similares.`
      );
      await loadImportState(event.id);
    } catch (currentError) {
      setError(
        currentError instanceof Error
          ? currentError.message
          : "No se pudo detectar duplicados y similares."
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function handleCurateMedia() {
    if (!event) {
      return;
    }

    setActionLoading(true);
    setError(null);
    setMessage(null);

    try {
      const result = await curateMedia(event.id);
      setLastCuration(result);
      setMessage(
        `Curacion completada: ${result.selected} seleccionados, ${result.alternative} alternativos, ${result.rejected} descartes logicos.`
      );
      await loadImportState(event.id);
    } catch (currentError) {
      setError(
        currentError instanceof Error
          ? currentError.message
          : "No se pudo ejecutar la curacion inteligente."
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function handleEnhancePhotos() {
    if (!event) {
      return;
    }

    setActionLoading(true);
    setError(null);
    setMessage(null);

    try {
      const result = await enhancePhotos(event.id, enhancementPreset);
      setLastEnhancement(result);
      setMessage(
        `Mejora completada: ${result.enhanced} versiones nuevas, ${result.skipped} omitidos, ${result.failed} fallidos.`
      );
      await loadImportState(event.id);
    } catch (currentError) {
      setError(
        currentError instanceof Error
          ? currentError.message
          : "No se pudieron generar las versiones mejoradas."
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function handleEnhanceVideos() {
    if (!event) {
      return;
    }

    setActionLoading(true);
    setError(null);
    setMessage(null);

    try {
      const result = await enhanceVideos(event.id, {
        clip_duration_seconds: 30,
        max_full_duration_seconds: 90,
        preset_slug: videoEnhancementPreset,
        processing_mode: videoProcessingMode
      });
      setLastVideoEnhancement(result);
      setMessage(
        result.ffmpeg_available
          ? `Video basico completado: ${result.enhanced} versiones nuevas, ${result.skipped} omitidos, ${result.failed} fallidos.`
          : "FFmpeg no esta disponible; se registro el job y no se modifico ningun video."
      );
      await loadImportState(event.id);
    } catch (currentError) {
      setError(
        currentError instanceof Error
          ? currentError.message
          : "No se pudieron generar las versiones de video."
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function handleManualCuration(
    curatedId: number,
    selectionStatus: string,
    reason: string
  ) {
    if (!event) {
      return;
    }

    setActionLoading(true);
    setError(null);
    setMessage(null);

    try {
      await updateCuratedMedia(event.id, curatedId, {
        reason,
        selection_status: selectionStatus
      });
      setMessage("Decision manual guardada.");
      await loadImportState(event.id);
    } catch (currentError) {
      setError(
        currentError instanceof Error
          ? currentError.message
          : "No se pudo actualizar la decision de curacion."
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function handleEnhancedDecision(enhancedId: number, statusValue: string, reason: string) {
    if (!event) {
      return;
    }

    setActionLoading(true);
    setError(null);
    setMessage(null);

    try {
      await updateEnhancedMedia(event.id, enhancedId, {
        reason,
        status: statusValue
      });
      setMessage("Decision sobre la version mejorada guardada.");
      await loadImportState(event.id);
    } catch (currentError) {
      setError(
        currentError instanceof Error
          ? currentError.message
          : "No se pudo actualizar la version mejorada."
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

  const curationGroups = groupCuratedItems(curatedItems);
  const selectedPhotoCount = curatedItems.filter(
    (item) =>
      ["selected", "user_selected"].includes(item.selection_status) &&
      item.media.media_type === "image"
  ).length;
  const selectedVideoCount = curatedItems.filter(
    (item) =>
      ["selected", "user_selected"].includes(item.selection_status) &&
      item.media.media_type === "video"
  ).length;

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
              Carpeta local creada para importar, procesar, revisar y exportar
              material sin modificar originales.
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
              <button
                className="outline-action"
                disabled={actionLoading || mediaItems.every((media) => media.media_type !== "image")}
                onClick={handleAnalyzePhotos}
                type="button"
              >
                Analizar fotos
              </button>
              <button
                className="outline-action"
                disabled={actionLoading || mediaItems.length < 2}
                onClick={handleDetectSimilarity}
                type="button"
              >
                Detectar duplicados y similares
              </button>
              <button
                className="secondary-action"
                disabled={actionLoading || mediaItems.length === 0}
                onClick={handleCurateMedia}
                type="button"
              >
                Ejecutar curacion inteligente
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
            {lastAnalysis ? (
              <p className="import-summary">
                Analisis job #{lastAnalysis.job_id}: {lastAnalysis.analyzed_photos} fotos,{" "}
                {lastAnalysis.failed_photos} fallidas, {lastAnalysis.skipped_non_images} videos u
                otros medios omitidos.
              </p>
            ) : null}
            {lastSimilarity ? (
              <p className="import-summary">
                Similitud job #{lastSimilarity.job_id}: {lastSimilarity.exact_groups} exactos,{" "}
                {lastSimilarity.similar_groups} similares, {lastSimilarity.grouped_items} medios
                agrupados.
              </p>
            ) : null}
            {lastCuration ? (
              <p className="import-summary">
                Curacion job #{lastCuration.job_id}: {lastCuration.selected} seleccionados,{" "}
                {lastCuration.alternative} alternativos, {lastCuration.rejected} descartes,{" "}
                {lastCuration.manual_review} en revision.
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
                  <div>
                    <p className="metric-label">Calidad</p>
                    <strong>{formatScore(media.analysis?.overall_quality_score)}</strong>
                    <span>{qualityLabel(media.analysis?.overall_quality_score, media.media_type)}</span>
                  </div>
                  <div className="analysis-metrics">
                    <p className="metric-label">Analisis visual</p>
                    <span>Nitidez {formatScore(media.analysis?.sharpness_score)}</span>
                    <span>Brillo {formatScore(media.analysis?.brightness_score)}</span>
                    <span>Contraste {formatScore(media.analysis?.contrast_score)}</span>
                    <span>Exposicion {formatScore(media.analysis?.exposure_score)}</span>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="similarity-panel">
            <div className="section-heading-row">
              <div>
                <p className="section-label">Duplicados y similares</p>
                <h2>{similarityGroups.length} grupos detectados</h2>
              </div>
            </div>
            {similarityGroups.length === 0 ? (
              <article className="empty-state">
                <h2>Sin grupos detectados</h2>
                <p>
                  Ejecuta Analizar fotos y luego Detectar duplicados y similares para revisar
                  alternativas.
                </p>
              </article>
            ) : null}
            <div className="similarity-list">
              {similarityGroups.map((group) => (
                <article className="similarity-group" key={group.id}>
                  <div className="similarity-summary">
                    <div>
                      <p className="metric-label">{formatGroupType(group.group_type)}</p>
                      <h2>Grupo #{group.id}</h2>
                      <span>{group.reason ?? "Sin motivo registrado"}</span>
                    </div>
                    <strong>{formatConfidence(group.confidence_score)}</strong>
                  </div>
                  <div className="similarity-strip">
                    {group.items.map((item) => (
                      <div className="similarity-item" key={item.id}>
                        <div className="media-thumb">
                          {item.media.thumbnail_url ? (
                            <img
                              alt={`Miniatura de ${item.media.filename}`}
                              loading="lazy"
                              src={thumbnailSrc(item.media.thumbnail_url)}
                            />
                          ) : (
                            <span>{item.media.media_type === "video" ? "VIDEO" : "IMG"}</span>
                          )}
                        </div>
                        <div>
                          <strong>{item.media.filename}</strong>
                          <span>{formatSimilarityRole(item.role)}</span>
                          <span>Calidad {formatScore(item.media.analysis?.overall_quality_score)}</span>
                          <span>Distancia {formatDistance(item.distance_score)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="curation-panel">
            <div className="section-heading-row">
              <div>
                <p className="section-label">Curacion inteligente</p>
                <h2>{curatedItems.length} medios con estado</h2>
              </div>
            </div>
            {curatedItems.length === 0 ? (
              <article className="empty-state">
                <h2>Sin curacion ejecutada</h2>
                <p>Ejecuta la curacion inteligente para crear estados revisables.</p>
              </article>
            ) : null}
            {curatedItems.length > 0 ? (
              <div className="curation-columns">
                {curationGroups.map((group) => (
                  <article className="curation-column" key={group.key}>
                    <p className="section-label">{group.label}</p>
                    <h2>{group.items.length}</h2>
                    <div className="curation-list">
                      {group.items.map((item) => (
                        <div className="curation-card" key={item.id}>
                          <div className="media-thumb">
                            {item.media.thumbnail_url ? (
                              <img
                                alt={`Miniatura de ${item.media.filename}`}
                                loading="lazy"
                                src={thumbnailSrc(item.media.thumbnail_url)}
                              />
                            ) : (
                              <span>{item.media.media_type === "video" ? "VIDEO" : "IMG"}</span>
                            )}
                          </div>
                          <div className="curation-card-body">
                            <strong>{item.media.filename}</strong>
                            <span>{formatCurationStatus(item.selection_status)}</span>
                            <span>Calidad {formatScore(item.score)}</span>
                            <p>{item.reason ?? "Sin motivo"}</p>
                            {item.is_manual_override ? <span>Decision manual</span> : null}
                            <div className="curation-actions">
                              <button
                                className="outline-action"
                                disabled={actionLoading}
                                onClick={() =>
                                  handleManualCuration(
                                    item.id,
                                    "user_selected",
                                    "Seleccionado manualmente para la siguiente fase."
                                  )
                                }
                                type="button"
                              >
                                Seleccionar
                              </button>
                              <button
                                className="outline-action"
                                disabled={actionLoading}
                                onClick={() =>
                                  handleManualCuration(
                                    item.id,
                                    "manual_review",
                                    "Enviado a revision manual."
                                  )
                                }
                                type="button"
                              >
                                Revisar
                              </button>
                              <button
                                className="danger-action"
                                disabled={actionLoading}
                                onClick={() =>
                                  handleManualCuration(
                                    item.id,
                                    "user_rejected",
                                    "Rechazado manualmente sin borrar el archivo."
                                  )
                                }
                                type="button"
                              >
                                Rechazar
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
            ) : null}
          </section>

          <section className="enhancement-panel">
            <div className="section-heading-row">
              <div>
                <p className="section-label">Mejoras visuales</p>
                <h2>{enhancedItems.length} versiones generadas</h2>
              </div>
              <div className="enhancement-controls">
                <label className="field-group compact-field">
                  <span>Preset fotos</span>
                  <select
                    disabled={actionLoading}
                    onChange={(formEvent) => setEnhancementPreset(formEvent.target.value)}
                    value={enhancementPreset}
                  >
                    {enhancementPresets.map((preset) => (
                      <option key={preset.value} value={preset.value}>
                        {preset.label}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  className="secondary-action"
                  disabled={actionLoading || selectedPhotoCount === 0}
                  onClick={handleEnhancePhotos}
                  type="button"
                >
                  Mejorar fotos
                </button>
                <label className="field-group compact-field">
                  <span>Preset videos</span>
                  <select
                    disabled={actionLoading}
                    onChange={(formEvent) => setVideoEnhancementPreset(formEvent.target.value)}
                    value={videoEnhancementPreset}
                  >
                    {enhancementPresets.map((preset) => (
                      <option key={preset.value} value={preset.value}>
                        {preset.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field-group compact-field">
                  <span>Modo video</span>
                  <select
                    disabled={actionLoading}
                    onChange={(formEvent) => setVideoProcessingMode(formEvent.target.value)}
                    value={videoProcessingMode}
                  >
                    {videoProcessingModes.map((mode) => (
                      <option key={mode.value} value={mode.value}>
                        {mode.label}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  className="secondary-action"
                  disabled={actionLoading || selectedVideoCount === 0}
                  onClick={handleEnhanceVideos}
                  type="button"
                >
                  Mejorar videos
                </button>
              </div>
            </div>
            {lastEnhancement ? (
              <p className="import-summary">
                Mejora job #{lastEnhancement.job_id}: {lastEnhancement.enhanced} versiones,{" "}
                {lastEnhancement.skipped} omitidos, {lastEnhancement.failed} fallidos con preset{" "}
                {formatPreset(lastEnhancement.preset_slug)}.
              </p>
            ) : null}
            {lastVideoEnhancement ? (
              <p className="import-summary">
                Video job #{lastVideoEnhancement.job_id}: {lastVideoEnhancement.enhanced} versiones,{" "}
                {lastVideoEnhancement.skipped} omitidos, {lastVideoEnhancement.failed} fallidos
                con preset {formatPreset(lastVideoEnhancement.preset_slug)}. FFmpeg{" "}
                {lastVideoEnhancement.ffmpeg_available ? "disponible" : "no disponible"}.
              </p>
            ) : null}
            {selectedPhotoCount === 0 && selectedVideoCount === 0 ? (
              <article className="empty-state">
                <h2>Sin medios seleccionados para mejorar</h2>
                <p>Marca fotos o videos como seleccionados en la curacion antes de generar versiones.</p>
              </article>
            ) : null}
            {enhancedItems.length === 0 && (selectedPhotoCount > 0 || selectedVideoCount > 0) ? (
              <article className="empty-state">
                <h2>Sin versiones mejoradas</h2>
                <p>Procesa medios seleccionados para crear versiones locales nuevas.</p>
              </article>
            ) : null}
            <div className="enhancement-list">
              {enhancedItems.map((item) => (
                <article className="enhancement-card" key={item.id}>
                  <div className="comparison-strip">
                    <div>
                      <p className="metric-label">Original</p>
                      <div className="comparison-image">
                        {item.media.thumbnail_url ? (
                          <img
                            alt={`Original ${item.media.filename}`}
                            loading="lazy"
                            src={thumbnailSrc(item.media.thumbnail_url)}
                          />
                        ) : (
                          <span>IMG</span>
                        )}
                      </div>
                    </div>
                    <div>
                      <p className="metric-label">Mejorado</p>
                      <div className="comparison-image">
                        {isVideoEnhanced(item) ? (
                          <video controls preload="metadata" src={thumbnailSrc(item.output_url)} />
                        ) : (
                          <img
                            alt={`Version mejorada de ${item.media.filename}`}
                            loading="lazy"
                            src={thumbnailSrc(item.output_url)}
                          />
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="enhancement-card-body">
                    <div>
                      <strong>{item.media.filename}</strong>
                      <span>{formatPreset(item.preset_slug)}</span>
                      <span>{formatEnhancedStatus(item.status)}</span>
                      <span>{formatDimensions(item.width, item.height)}</span>
                      <span>{formatDuration(item.duration_seconds)}</span>
                    </div>
                    <p>{formatEnhancementNotes(item.notes)}</p>
                    <code>{item.output_path}</code>
                    <div className="curation-actions">
                      <button
                        className="outline-action"
                        disabled={actionLoading || item.status === "approved"}
                        onClick={() =>
                          handleEnhancedDecision(
                            item.id,
                            "approved",
                            "Version mejorada aprobada manualmente."
                          )
                        }
                        type="button"
                      >
                        Aprobar
                      </button>
                      <button
                        className="danger-action"
                        disabled={actionLoading || item.status === "rejected"}
                        onClick={() =>
                          handleEnhancedDecision(
                            item.id,
                            "rejected",
                            "Version mejorada rechazada manualmente sin borrar archivo."
                          )
                        }
                        type="button"
                      >
                        Rechazar
                      </button>
                    </div>
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

function formatScore(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "--";
  }
  return `${Math.round(value)}/100`;
}

function qualityLabel(value: number | null | undefined, mediaType: string) {
  if (mediaType !== "image") {
    return "Analisis solo para fotos";
  }
  if (value === null || value === undefined) {
    return "Pendiente";
  }
  if (value >= 75) {
    return "Alta";
  }
  if (value >= 50) {
    return "Media";
  }
  return "Baja";
}

function formatGroupType(value: string) {
  const labels: Record<string, string> = {
    checksum_duplicate: "Duplicado exacto",
    perceptual_hash: "Similar visual"
  };
  return labels[value] ?? value;
}

function formatConfidence(value: number | null) {
  if (value === null) {
    return "Confianza pendiente";
  }
  return `${Math.round(value)}% confianza`;
}

function formatSimilarityRole(value: string) {
  const labels: Record<string, string> = {
    alternative: "Alternativa",
    duplicate: "Duplicado",
    representative: "Representante sugerido"
  };
  return labels[value] ?? value;
}

function formatDistance(value: number | null) {
  if (value === null) {
    return "--";
  }
  return value.toFixed(0);
}

function groupCuratedItems(items: CuratedMedia[]) {
  const selected = items.filter((item) =>
    ["selected", "user_selected"].includes(item.selection_status)
  );
  const alternatives = items.filter((item) => item.selection_status === "alternative");
  const manualReview = items.filter((item) => item.selection_status === "manual_review");
  const rejected = items.filter((item) =>
    item.selection_status.startsWith("rejected_") || item.selection_status === "user_rejected"
  );

  return [
    { items: selected, key: "selected", label: "Seleccionados" },
    { items: alternatives, key: "alternative", label: "Alternativos" },
    { items: rejected, key: "rejected", label: "Descartes logicos" },
    { items: manualReview, key: "manual_review", label: "Revision manual" }
  ];
}

function formatCurationStatus(value: string) {
  const labels: Record<string, string> = {
    alternative: "Alternativo",
    manual_review: "Revision manual",
    rejected_blurry: "Descartado por borroso",
    rejected_dark: "Descartado por oscuro",
    rejected_duplicate: "Descartado por duplicado",
    rejected_low_quality: "Descartado por baja calidad",
    rejected_similar: "Descartado por similitud",
    selected: "Seleccionado",
    user_rejected: "Rechazado por usuario",
    user_selected: "Seleccionado por usuario"
  };
  return labels[value] ?? value;
}

function formatPreset(value: string | null) {
  if (!value) {
    return "Preset pendiente";
  }
  const preset = enhancementPresets.find((item) => item.value === value);
  return preset?.label ?? value;
}

function formatEnhancedStatus(value: string) {
  const labels: Record<string, string> = {
    approved: "Aprobado",
    completed: "Pendiente de aprobacion",
    generated: "Generado",
    rejected: "Rechazado"
  };
  return labels[value] ?? value;
}

function isVideoEnhanced(item: EnhancedMedia) {
  return item.media.media_type === "video" || item.enhancement_type.startsWith("video_");
}

function formatEnhancementNotes(value: string | null) {
  if (!value) {
    return "Sin notas de procesamiento.";
  }
  try {
    const payload = JSON.parse(value) as {
      format_status?: string;
      metadata_status?: string;
      plan?: string;
    };
    const details = [];
    if (payload.metadata_status) {
      details.push(`Metadatos: ${formatMetadataStatus(payload.metadata_status)}`);
    }
    if (payload.plan) {
      details.push(`Plan: ${formatVideoPlan(payload.plan)}`);
    }
    if (payload.format_status) {
      details.push(`Formato: ${formatVideoFormatStatus(payload.format_status)}`);
    }
    if (details.length > 0) {
      return `${details.join(". ")}.`;
    }
  } catch {
    return value;
  }
  return value;
}

function formatMetadataStatus(value: string) {
  if (value === "file_mtime_and_exif_written") {
    return "fecha escrita con ExifTool y fecha de archivo";
  }
  if (value === "file_mtime_written_exiftool_unavailable") {
    return "fecha de archivo ajustada; ExifTool no disponible";
  }
  if (value.startsWith("file_mtime_written_exiftool_failed")) {
    return "fecha de archivo ajustada; ExifTool fallo";
  }
  if (value === "file_mtime_written_exiftool_timeout") {
    return "fecha de archivo ajustada; ExifTool excedio el tiempo";
  }
  return value;
}

function formatVideoPlan(value: string) {
  const labels: Record<string, string> = {
    full_video: "video completo",
    suggested_clip: "segmento sugerido"
  };
  return labels[value] ?? value;
}

function formatVideoFormatStatus(value: string) {
  if (value === "original_container_preserved") {
    return "contenedor original conservado";
  }
  if (value.startsWith("normalized_to")) {
    return `normalizado a ${value.replace("normalized_to", "")}`;
  }
  return value;
}
