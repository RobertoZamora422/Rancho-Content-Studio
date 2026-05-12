import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { generateCopy, listCopies, updateCopy } from "../../services/copywritingService";
import { listEvents } from "../../services/eventService";
import { API_BASE_URL } from "../../services/apiClient";
import {
  exportPackage,
  generatePieces,
  listExportPackages,
  listContentPieces,
  openExportPackageFolder,
  updateContentPiece
} from "../../services/pieceService";
import type { GeneratedCopy } from "../../types/copywriting";
import type { ContentEvent } from "../../types/events";
import type {
  ContentPiece,
  ContentPieceMedia,
  ExportPackage,
  ExportPackageRunResponse,
  PieceGenerationResponse
} from "../../types/pieces";

const feedbackOptions = [
  { label: "Mas humano", value: "mas_humano" },
  { label: "Mas corto", value: "mas_corto" },
  { label: "Menos cursi", value: "menos_cursi" },
  { label: "Mas calido", value: "mas_calido" },
  { label: "Mas comercial", value: "mas_comercial" }
];

export function PiecesPage() {
  const [events, setEvents] = useState<ContentEvent[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);
  const [pieces, setPieces] = useState<ContentPiece[]>([]);
  const [selectedPieceId, setSelectedPieceId] = useState<number | null>(null);
  const [lastGeneration, setLastGeneration] = useState<PieceGenerationResponse | null>(null);
  const [exportPackages, setExportPackages] = useState<ExportPackage[]>([]);
  const [lastExport, setLastExport] = useState<ExportPackageRunResponse | null>(null);
  const [exportType, setExportType] = useState("ready_to_publish");
  const [includeCopies, setIncludeCopies] = useState(true);
  const [writeEventDateMetadata, setWriteEventDateMetadata] = useState(true);
  const [groupByType, setGroupByType] = useState(true);
  const [includeSummary, setIncludeSummary] = useState(true);
  const [draftTitle, setDraftTitle] = useState("");
  const [draftPurpose, setDraftPurpose] = useState("");
  const [draftPlatform, setDraftPlatform] = useState("");
  const [draftAspectRatio, setDraftAspectRatio] = useState("");
  const [copies, setCopies] = useState<GeneratedCopy[]>([]);
  const [selectedCopyId, setSelectedCopyId] = useState<number | null>(null);
  const [copyDraft, setCopyDraft] = useState("");
  const [copyLoading, setCopyLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const selectedPiece = useMemo(
    () => pieces.find((piece) => piece.id === selectedPieceId) ?? pieces[0] ?? null,
    [pieces, selectedPieceId]
  );

  const selectedCopy = useMemo(
    () => copies.find((copy) => copy.id === selectedCopyId) ?? copies[0] ?? null,
    [copies, selectedCopyId]
  );

  const approvedPieces = useMemo(
    () => pieces.filter((piece) => piece.status === "approved"),
    [pieces]
  );

  const approvedPieceMediaCount = useMemo(
    () => approvedPieces.reduce((total, piece) => total + piece.media_items.length, 0),
    [approvedPieces]
  );

  const latestPackage = lastExport?.package ?? exportPackages[0] ?? null;

  async function loadEvents() {
    setLoading(true);
    setError(null);
    try {
      const response = await listEvents(false);
      setEvents(response.items);
      if (response.items.length > 0 && selectedEventId === null) {
        setSelectedEventId(response.items[0].id);
      }
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudieron cargar eventos.");
    } finally {
      setLoading(false);
    }
  }

  async function loadPieces(eventId: number) {
    setError(null);
    try {
      const response = await listContentPieces(eventId);
      setPieces(response.items);
      setSelectedPieceId((current) => {
        if (current && response.items.some((piece) => piece.id === current)) {
          return current;
        }
        return response.items[0]?.id ?? null;
      });
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudieron cargar piezas.");
    }
  }

  async function loadExports(eventId: number) {
    setError(null);
    try {
      const response = await listExportPackages(eventId);
      setExportPackages(response.items);
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudieron cargar exportaciones.");
    }
  }

  async function loadPieceCopies(eventId: number, pieceId: number) {
    setError(null);
    setCopyLoading(true);
    try {
      const response = await listCopies(eventId, pieceId);
      setCopies(response.items);
      setSelectedCopyId((current) => {
        if (current && response.items.some((copy) => copy.id === current)) {
          return current;
        }
        return response.items[0]?.id ?? null;
      });
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudieron cargar copies.");
    } finally {
      setCopyLoading(false);
    }
  }

  useEffect(() => {
    void loadEvents();
  }, []);

  useEffect(() => {
    if (selectedEventId !== null) {
      void loadPieces(selectedEventId);
      void loadExports(selectedEventId);
      setLastExport(null);
    }
  }, [selectedEventId]);

  useEffect(() => {
    if (selectedEventId !== null && selectedPiece) {
      void loadPieceCopies(selectedEventId, selectedPiece.id);
    } else {
      setCopies([]);
      setSelectedCopyId(null);
    }
  }, [selectedEventId, selectedPiece?.id]);

  useEffect(() => {
    if (selectedPiece) {
      setDraftTitle(selectedPiece.title);
      setDraftPurpose(selectedPiece.purpose ?? "");
      setDraftPlatform(selectedPiece.target_platform ?? "");
      setDraftAspectRatio(selectedPiece.aspect_ratio ?? "");
    } else {
      setDraftTitle("");
      setDraftPurpose("");
      setDraftPlatform("");
      setDraftAspectRatio("");
    }
  }, [selectedPiece?.id]);

  useEffect(() => {
    setCopyDraft(selectedCopy?.body ?? "");
  }, [selectedCopy?.id]);

  async function handleGeneratePieces() {
    if (selectedEventId === null) {
      return;
    }

    setActionLoading(true);
    setError(null);
    setMessage(null);
    try {
      const result = await generatePieces(selectedEventId);
      setLastGeneration(result);
      setMessage(
        `Generacion completada: ${result.pieces_created} piezas nuevas, ${result.pieces_skipped} omitidas.`
      );
      await loadPieces(selectedEventId);
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudieron generar piezas.");
    } finally {
      setActionLoading(false);
    }
  }

  async function saveSelectedPiece(status?: string) {
    if (!selectedPiece || selectedEventId === null) {
      return;
    }

    setActionLoading(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await updateContentPiece(selectedEventId, selectedPiece.id, {
        aspect_ratio: draftAspectRatio,
        purpose: draftPurpose,
        status,
        target_platform: draftPlatform,
        title: draftTitle
      });
      setMessage("Pieza actualizada.");
      await loadPieces(selectedEventId);
      setSelectedPieceId(updated.id);
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudo actualizar la pieza.");
    } finally {
      setActionLoading(false);
    }
  }

  async function moveMediaItem(mediaItemId: number, direction: -1 | 1) {
    if (!selectedPiece || selectedEventId === null) {
      return;
    }
    const order = selectedPiece.media_items.map((item) => item.id);
    const index = order.indexOf(mediaItemId);
    const nextIndex = index + direction;
    if (index < 0 || nextIndex < 0 || nextIndex >= order.length) {
      return;
    }
    [order[index], order[nextIndex]] = [order[nextIndex], order[index]];

    setActionLoading(true);
    setError(null);
    setMessage(null);
    try {
      await updateContentPiece(selectedEventId, selectedPiece.id, {
        media_item_order: order
      });
      setMessage("Orden actualizado.");
      await loadPieces(selectedEventId);
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudo reordenar la pieza.");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleGenerateCopy(feedback?: string) {
    if (!selectedPiece || selectedEventId === null) {
      return;
    }

    setActionLoading(true);
    setError(null);
    setMessage(null);
    try {
      const result = await generateCopy(selectedEventId, selectedPiece.id, { feedback });
      setMessage(
        `Copy generado: ${result.copies_created} variantes en job #${result.job_id}.`
      );
      await loadPieceCopies(selectedEventId, selectedPiece.id);
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudo generar copy.");
    } finally {
      setActionLoading(false);
    }
  }

  async function saveSelectedCopy(status?: string) {
    if (!selectedPiece || !selectedCopy || selectedEventId === null) {
      return;
    }

    setActionLoading(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await updateCopy(selectedEventId, selectedPiece.id, selectedCopy.id, {
        body: copyDraft,
        status
      });
      setMessage("Copy actualizado.");
      await loadPieceCopies(selectedEventId, selectedPiece.id);
      setSelectedCopyId(updated.id);
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudo actualizar el copy.");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleExportPackage() {
    if (selectedEventId === null) {
      return;
    }

    setActionLoading(true);
    setError(null);
    setMessage(null);
    try {
      const result = await exportPackage(selectedEventId, {
        export_type: exportType,
        group_by_type: groupByType,
        include_copies: includeCopies,
        include_summary: includeSummary,
        write_event_date_metadata: writeEventDateMetadata
      });
      setLastExport(result);
      setMessage(
        `Exportacion completada: ${result.media_exported} medios, ${result.copies_exported} copies, ${result.failed_items} fallas.`
      );
      await loadExports(selectedEventId);
      await loadPieces(selectedEventId);
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudo exportar el paquete.");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleOpenExportFolder(packageId: number) {
    if (selectedEventId === null) {
      return;
    }

    setActionLoading(true);
    setError(null);
    setMessage(null);
    try {
      const response = await openExportPackageFolder(selectedEventId, packageId);
      setMessage(response.opened ? response.message : `${response.message} Ruta: ${response.path}`);
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudo abrir la carpeta final.");
    } finally {
      setActionLoading(false);
    }
  }

  return (
    <section className="pieces-view">
      <div className="page-heading">
        <p className="section-label">Produccion</p>
        <h1>Piezas de contenido</h1>
        <p>
          Genera propuestas revisables, aprueba copy y crea el paquete final en
          09_Listo_Para_Publicar sin modificar originales.
        </p>
      </div>

      {error ? <p className="inline-error">{error}</p> : null}
      {message ? <p className="inline-success">{message}</p> : null}

      <section className="pieces-toolbar">
        <label className="field-group">
          <span>Evento</span>
          <select
            disabled={loading || actionLoading || events.length === 0}
            onChange={(formEvent) => setSelectedEventId(Number(formEvent.target.value))}
            value={selectedEventId ?? ""}
          >
            {events.map((event) => (
              <option key={event.id} value={event.id}>
                {event.name}
              </option>
            ))}
          </select>
        </label>
        <button
          className="secondary-action"
          disabled={actionLoading || selectedEventId === null}
          onClick={handleGeneratePieces}
          type="button"
        >
          Generar piezas sugeridas
        </button>
        {selectedEventId !== null ? (
          <Link className="link-action" to={`/events/${selectedEventId}`}>
            Abrir evento
          </Link>
        ) : null}
      </section>

      {lastGeneration ? (
        <p className="import-summary">
          Job #{lastGeneration.job_id}: {lastGeneration.total_available_media} medios disponibles,{" "}
          {lastGeneration.pieces_created} piezas creadas y {lastGeneration.pieces_skipped} omitidas.
        </p>
      ) : null}

      <section className="export-panel">
        <div className="section-heading-row">
          <div>
            <p className="section-label">Exportacion final</p>
            <h2>Exportacion final</h2>
          </div>
          <strong>{latestPackage ? formatExportStatus(latestPackage.status) : "Sin paquete"}</strong>
        </div>

        <div className="export-summary-grid">
          <div>
            <span>Piezas aprobadas</span>
            <strong>{approvedPieces.length}</strong>
          </div>
          <div>
            <span>Medios en piezas</span>
            <strong>{approvedPieceMediaCount}</strong>
          </div>
          <div>
            <span>Ultimos paquetes</span>
            <strong>{exportPackages.length}</strong>
          </div>
        </div>

        <div className="export-options-grid">
          <label className="field-group">
            <span>Tipo de exportacion</span>
            <select
              disabled={actionLoading}
              onChange={(event) => setExportType(event.target.value)}
              value={exportType}
            >
              <option value="ready_to_publish">Listo para publicar en redes</option>
              <option value="full_event_package">Todo el evento</option>
              <option value="reels_only">Solo reels</option>
              <option value="carousel_only">Solo carruseles</option>
              <option value="stories_only">Solo historias</option>
              <option value="google_photos_upload_package">Paquete para Google Photos</option>
            </select>
          </label>
          <label className="toggle-row">
            <input
              checked={includeCopies}
              disabled={actionLoading}
              onChange={(event) => setIncludeCopies(event.target.checked)}
              type="checkbox"
            />
            Incluir copies en .txt
          </label>
          <label className="toggle-row">
            <input
              checked={writeEventDateMetadata}
              disabled={actionLoading}
              onChange={(event) => setWriteEventDateMetadata(event.target.checked)}
              type="checkbox"
            />
            Escribir fecha del evento
          </label>
          <label className="toggle-row">
            <input
              checked={groupByType}
              disabled={actionLoading}
              onChange={(event) => setGroupByType(event.target.checked)}
              type="checkbox"
            />
            Crear carpeta por tipo
          </label>
          <label className="toggle-row">
            <input
              checked={includeSummary}
              disabled={actionLoading}
              onChange={(event) => setIncludeSummary(event.target.checked)}
              type="checkbox"
            />
            Incluir resumen
          </label>
        </div>

        <div className="settings-actions">
          <button
            className="secondary-action"
            disabled={actionLoading || selectedEventId === null}
            onClick={handleExportPackage}
            type="button"
          >
            Exportar listo para publicar
          </button>
          {latestPackage ? (
            <button
              className="outline-action"
              disabled={actionLoading}
              onClick={() => handleOpenExportFolder(latestPackage.id)}
              type="button"
            >
              Abrir carpeta final
            </button>
          ) : null}
        </div>

        {latestPackage ? (
          <div className="export-result">
            <p className="import-summary">
              {formatExportType(latestPackage.export_type)}: {latestPackage.output_path}
            </p>
            <p className="import-summary">
              {latestPackage.items.length} archivos registrados. Ruta local:{" "}
              {latestPackage.absolute_output_path}
            </p>
          </div>
        ) : null}
      </section>

      {events.length === 0 && !loading ? (
        <article className="empty-state">
          <h2>No hay eventos activos</h2>
          <p>Crea un evento y genera medios mejorados antes de proponer piezas.</p>
        </article>
      ) : null}

      <section className="pieces-layout">
        <div className="piece-card-list">
          {pieces.length === 0 && selectedEventId !== null ? (
            <article className="empty-state">
              <h2>Sin piezas generadas</h2>
              <p>Genera piezas cuando existan medios mejorados completados o aprobados.</p>
            </article>
          ) : null}
          {pieces.map((piece) => (
            <button
              className={`piece-card ${selectedPiece?.id === piece.id ? "active" : ""}`}
              key={piece.id}
              onClick={() => setSelectedPieceId(piece.id)}
              type="button"
            >
              <span>{formatPieceType(piece.piece_type)}</span>
              <strong>{piece.title}</strong>
              <small>
                {piece.media_items.length} medios | {formatPieceStatus(piece.status)}
              </small>
            </button>
          ))}
        </div>

        {selectedPiece ? (
          <article className="piece-editor-panel">
            <div className="section-heading-row">
              <div>
                <p className="section-label">{formatPieceType(selectedPiece.piece_type)}</p>
                <h2>{selectedPiece.title}</h2>
              </div>
              <strong>{formatPieceStatus(selectedPiece.status)}</strong>
            </div>

            <div className="piece-editor-fields">
              <label className="field-group">
                <span>Titulo</span>
                <input value={draftTitle} onChange={(event) => setDraftTitle(event.target.value)} />
              </label>
              <label className="field-group">
                <span>Proposito</span>
                <input value={draftPurpose} onChange={(event) => setDraftPurpose(event.target.value)} />
              </label>
              <label className="field-group">
                <span>Plataforma</span>
                <input value={draftPlatform} onChange={(event) => setDraftPlatform(event.target.value)} />
              </label>
              <label className="field-group">
                <span>Formato</span>
                <input
                  value={draftAspectRatio}
                  onChange={(event) => setDraftAspectRatio(event.target.value)}
                />
              </label>
            </div>

            <div className="piece-media-list">
              {selectedPiece.media_items.map((item, index) => (
                <div className="piece-media-row" key={item.id}>
                  <div className="media-thumb">{renderPieceMedia(item)}</div>
                  <div>
                    <strong>{item.enhanced_media?.media.filename ?? `Medio #${item.id}`}</strong>
                    <span>{formatMediaRole(item.role)}</span>
                    <span>{item.enhanced_media?.output_path ?? "Sin ruta"}</span>
                  </div>
                  <div className="piece-order-actions">
                    <button
                      className="outline-action"
                      disabled={actionLoading || index === 0}
                      onClick={() => moveMediaItem(item.id, -1)}
                      type="button"
                    >
                      Subir
                    </button>
                    <button
                      className="outline-action"
                      disabled={actionLoading || index === selectedPiece.media_items.length - 1}
                      onClick={() => moveMediaItem(item.id, 1)}
                      type="button"
                    >
                      Bajar
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="settings-actions">
              <button
                className="outline-action"
                disabled={actionLoading || draftTitle.trim().length === 0}
                onClick={() => saveSelectedPiece("in_review")}
                type="button"
              >
                Guardar revision
              </button>
              <button
                className="secondary-action"
                disabled={actionLoading || selectedPiece.media_items.length === 0}
                onClick={() => saveSelectedPiece("approved")}
                type="button"
              >
                Aprobar pieza
              </button>
              <button
                className="danger-action"
                disabled={actionLoading}
                onClick={() => saveSelectedPiece("rejected")}
                type="button"
              >
                Rechazar pieza
              </button>
            </div>

            <section className="copywriting-panel">
              <div className="section-heading-row">
                <div>
                  <p className="section-label">Copywriting</p>
                  <h2>Copywriting</h2>
                </div>
                <strong>{copies.length} variantes</strong>
              </div>

              {selectedPiece.status !== "approved" ? (
                <p className="inline-error">
                  Aprueba la pieza antes de generar copy para mantener el control humano del flujo.
                </p>
              ) : null}

              <div className="settings-actions">
                <button
                  className="secondary-action"
                  disabled={actionLoading || copyLoading || selectedPiece.status !== "approved"}
                  onClick={() => handleGenerateCopy()}
                  type="button"
                >
                  Generar copy
                </button>
                {feedbackOptions.map((option) => (
                  <button
                    className="outline-action"
                    disabled={actionLoading || copyLoading || selectedPiece.status !== "approved"}
                    key={option.value}
                    onClick={() => handleGenerateCopy(option.value)}
                    type="button"
                  >
                    {option.label}
                  </button>
                ))}
              </div>

              {copies.length === 0 ? (
                <article className="empty-state">
                  <h2>Sin copies generados</h2>
                  <p>Genera variantes cuando la pieza este aprobada.</p>
                </article>
              ) : null}

              {copies.length > 0 ? (
                <div className="copy-editor-grid">
                  <div className="copy-list">
                    {copies.map((copy) => (
                      <button
                        className={`copy-card ${selectedCopy?.id === copy.id ? "active" : ""}`}
                        key={copy.id}
                        onClick={() => setSelectedCopyId(copy.id)}
                        type="button"
                      >
                        <span>{formatCopyType(copy.copy_type)}</span>
                        <strong>{copy.variant_label ?? `Copy #${copy.id}`}</strong>
                        <small>{formatCopyStatus(copy.status)}</small>
                      </button>
                    ))}
                  </div>

                  {selectedCopy ? (
                    <div className="copy-editor">
                      <label className="field-group">
                        <span>Texto</span>
                        <textarea
                          onChange={(event) => setCopyDraft(event.target.value)}
                          value={copyDraft}
                        />
                      </label>
                      {selectedCopy.warnings.length > 0 ? (
                        <p className="inline-error">
                          Advertencias: {selectedCopy.warnings.map(formatCopyWarning).join(", ")}
                        </p>
                      ) : null}
                      {selectedCopy.output_path ? (
                        <p className="import-summary">Archivo: {selectedCopy.output_path}</p>
                      ) : null}
                      <div className="settings-actions">
                        <button
                          className="outline-action"
                          disabled={actionLoading || copyDraft.trim().length === 0}
                          onClick={() => saveSelectedCopy()}
                          type="button"
                        >
                          Guardar edicion
                        </button>
                        <button
                          className="secondary-action"
                          disabled={actionLoading || copyDraft.trim().length === 0}
                          onClick={() => saveSelectedCopy("approved")}
                          type="button"
                        >
                          Aprobar copy
                        </button>
                        <button
                          className="danger-action"
                          disabled={actionLoading}
                          onClick={() => saveSelectedCopy("rejected")}
                          type="button"
                        >
                          Rechazar copy
                        </button>
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </section>
          </article>
        ) : null}
      </section>
    </section>
  );
}

function renderPieceMedia(item: ContentPieceMedia) {
  const enhanced = item.enhanced_media;
  if (!enhanced) {
    return <span>MEDIA</span>;
  }
  const source = thumbnailSrc(enhanced.output_url);
  if (enhanced.media.media_type === "video") {
    return <video muted preload="metadata" src={source} />;
  }
  return <img alt={enhanced.media.filename} loading="lazy" src={source} />;
}

function thumbnailSrc(value: string) {
  if (value.startsWith("http")) {
    return value;
  }
  return `${API_BASE_URL}${value}`;
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

function formatPieceStatus(value: string) {
  const labels: Record<string, string> = {
    approved: "Aprobada",
    draft: "Borrador",
    generated: "Generada",
    in_review: "En revision",
    rejected: "Rechazada"
  };
  return labels[value] ?? value;
}

function formatMediaRole(value: string | null) {
  if (value === "cover") {
    return "Portada sugerida";
  }
  if (value === "sequence") {
    return "Secuencia";
  }
  return value ?? "Medio";
}

function formatCopyType(value: string) {
  const labels: Record<string, string> = {
    caption: "Caption",
    cover_text: "Texto de portada",
    cta: "CTA",
    hashtags: "Hashtags",
    reel_short_copy: "Copy breve",
    story_text: "Historia"
  };
  return labels[value] ?? value;
}

function formatCopyStatus(value: string) {
  const labels: Record<string, string> = {
    approved: "Aprobado",
    archived: "Archivado",
    edited: "Editado",
    generated: "Generado",
    regenerated: "Regenerado",
    rejected: "Rechazado"
  };
  return labels[value] ?? value;
}

function formatCopyWarning(value: string) {
  const labels: Record<string, string> = {
    contiene_palabras_a_evitar: "contiene palabras a evitar",
    copy_largo: "copy largo",
    copy_vacio: "copy vacio",
    sin_hashtags: "sin hashtags"
  };
  return labels[value] ?? value;
}

function formatExportType(value: string) {
  const labels: Record<string, string> = {
    carousel_only: "Solo carruseles",
    full_event_package: "Todo el evento",
    google_photos_upload_package: "Paquete para Google Photos",
    ready_to_publish: "Listo para publicar",
    reels_only: "Solo reels",
    stories_only: "Solo historias"
  };
  return labels[value] ?? value;
}

function formatExportStatus(value: string) {
  const labels: Record<string, string> = {
    approved: "Aprobado",
    archived: "Archivado",
    failed: "Con errores",
    generated: "Generado",
    pending: "Pendiente"
  };
  return labels[value] ?? value;
}
