import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { createEvent, listEvents } from "../../services/eventService";
import type { ContentEvent, EventCreate } from "../../types/events";

type EventFormState = {
  name: string;
  eventType: string;
  eventDate: string;
  notes: string;
};

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

const initialForm: EventFormState = {
  name: "",
  eventType: "",
  eventDate: todayIsoDate(),
  notes: ""
};

function toPayload(form: EventFormState): EventCreate {
  return {
    name: form.name.trim(),
    event_type: form.eventType.trim() || null,
    event_date: form.eventDate,
    notes: form.notes.trim() || null
  };
}

export function EventsPage() {
  const navigate = useNavigate();
  const [events, setEvents] = useState<ContentEvent[]>([]);
  const [includeArchived, setIncludeArchived] = useState(false);
  const [form, setForm] = useState<EventFormState>(initialForm);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const canCreate = useMemo(
    () => form.name.trim().length > 0 && form.eventDate.length > 0 && !creating,
    [creating, form.eventDate, form.name]
  );

  async function refreshEvents() {
    setLoading(true);
    setError(null);
    try {
      const response = await listEvents(includeArchived);
      setEvents(response.items);
    } catch (currentError) {
      setError(
        currentError instanceof Error
          ? currentError.message
          : "No se pudieron cargar los eventos."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refreshEvents();
  }, [includeArchived]);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canCreate) {
      return;
    }

    setCreating(true);
    setError(null);
    setMessage(null);

    try {
      const createdEvent = await createEvent(toPayload(form));
      setMessage("Evento creado con estructura local de carpetas.");
      setForm(initialForm);
      await refreshEvents();
      navigate(`/events/${createdEvent.id}`);
    } catch (currentError) {
      setError(
        currentError instanceof Error ? currentError.message : "No se pudo crear el evento."
      );
    } finally {
      setCreating(false);
    }
  }

  return (
    <section className="events-view">
      <div className="page-heading">
        <p className="section-label">Eventos</p>
        <h1>Eventos</h1>
        <p>
          Crea eventos locales y genera la estructura de carpetas donde se
          organizara el material sin modificar archivos originales.
        </p>
      </div>

      {error ? <p className="inline-error">{error}</p> : null}
      {message ? <p className="inline-success">{message}</p> : null}

      <form className="event-form" onSubmit={handleCreate}>
        <label className="field-group">
          <span>Nombre del evento</span>
          <input
            onChange={(formEvent) =>
              setForm((current) => ({ ...current, name: formEvent.target.value }))
            }
            placeholder="Boda Ana y Luis"
            value={form.name}
          />
        </label>
        <label className="field-group">
          <span>Tipo</span>
          <input
            onChange={(formEvent) =>
              setForm((current) => ({ ...current, eventType: formEvent.target.value }))
            }
            placeholder="Boda, XV, corporativo"
            value={form.eventType}
          />
        </label>
        <label className="field-group">
          <span>Fecha</span>
          <input
            onChange={(formEvent) =>
              setForm((current) => ({ ...current, eventDate: formEvent.target.value }))
            }
            type="date"
            value={form.eventDate}
          />
        </label>
        <label className="field-group span-3">
          <span>Notas</span>
          <input
            onChange={(formEvent) =>
              setForm((current) => ({ ...current, notes: formEvent.target.value }))
            }
            placeholder="Detalles internos del evento"
            value={form.notes}
          />
        </label>
        <div className="settings-actions span-3">
          <button className="secondary-action" disabled={!canCreate} type="submit">
            {creating ? "Creando" : "Crear evento"}
          </button>
          <button
            className="outline-action"
            disabled={loading}
            onClick={() => void refreshEvents()}
            type="button"
          >
            Actualizar lista
          </button>
        </div>
      </form>

      <div className="list-toolbar">
        <div>
          <p className="metric-label">Eventos registrados</p>
          <strong>{loading ? "Cargando" : events.length}</strong>
        </div>
        <label className="toggle-row">
          <input
            checked={includeArchived}
            onChange={(event) => setIncludeArchived(event.target.checked)}
            type="checkbox"
          />
          <span>Mostrar archivados</span>
        </label>
      </div>

      <section className="event-list">
        {!loading && events.length === 0 ? (
          <article className="empty-state">
            <h2>No hay eventos registrados</h2>
            <p>Configura una carpeta raiz y crea el primer evento.</p>
          </article>
        ) : null}

        {events.map((event) => (
          <article className="event-row" key={event.id}>
            <div>
              <p className="metric-label">{event.event_date ?? "Sin fecha"}</p>
              <h2>{event.name}</h2>
              <p>{event.event_type ?? "Tipo no definido"}</p>
            </div>
            <div>
              <p className="metric-label">Estado</p>
              <strong>{event.status}</strong>
            </div>
            <div className="event-path-cell">
              <p className="metric-label">Carpeta</p>
              <code>{event.folder_name ?? "Pendiente"}</code>
            </div>
            <Link className="link-action" to={`/events/${event.id}`}>
              Abrir
            </Link>
          </article>
        ))}
      </section>
    </section>
  );
}
