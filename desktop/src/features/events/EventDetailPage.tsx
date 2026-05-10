import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { eventSubdirectories } from "./eventFolders";
import { archiveEvent, deleteEvent, getEvent } from "../../services/eventService";
import type { ContentEvent } from "../../types/events";

export function EventDetailPage() {
  const navigate = useNavigate();
  const { eventId } = useParams();
  const numericEventId = Number(eventId);
  const [event, setEvent] = useState<ContentEvent | null>(null);
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

  useEffect(() => {
    void loadEvent();
  }, [numericEventId]);

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
