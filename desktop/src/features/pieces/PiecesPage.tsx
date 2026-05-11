import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { listEvents } from "../../services/eventService";
import { API_BASE_URL } from "../../services/healthService";
import {
  generatePieces,
  listContentPieces,
  updateContentPiece
} from "../../services/pieceService";
import type { ContentEvent } from "../../types/events";
import type { ContentPiece, ContentPieceMedia, PieceGenerationResponse } from "../../types/pieces";

export function PiecesPage() {
  const [events, setEvents] = useState<ContentEvent[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);
  const [pieces, setPieces] = useState<ContentPiece[]>([]);
  const [selectedPieceId, setSelectedPieceId] = useState<number | null>(null);
  const [lastGeneration, setLastGeneration] = useState<PieceGenerationResponse | null>(null);
  const [draftTitle, setDraftTitle] = useState("");
  const [draftPurpose, setDraftPurpose] = useState("");
  const [draftPlatform, setDraftPlatform] = useState("");
  const [draftAspectRatio, setDraftAspectRatio] = useState("");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const selectedPiece = useMemo(
    () => pieces.find((piece) => piece.id === selectedPieceId) ?? pieces[0] ?? null,
    [pieces, selectedPieceId]
  );

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

  useEffect(() => {
    void loadEvents();
  }, []);

  useEffect(() => {
    if (selectedEventId !== null) {
      void loadPieces(selectedEventId);
    }
  }, [selectedEventId]);

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

  return (
    <section className="pieces-view">
      <div className="page-heading">
        <p className="section-label">Fase 12</p>
        <h1>Piezas de contenido</h1>
        <p>
          Genera propuestas revisables usando medios mejorados completados o aprobados. Las piezas
          quedan listas para copywriting, no para exportacion final todavia.
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
