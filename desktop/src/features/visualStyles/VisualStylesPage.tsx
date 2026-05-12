import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listVisualStylePresets } from "../../services/visualStyleService";
import type { VisualStylePreset } from "../../types/visualStyles";

export function VisualStylesPage() {
  const [presets, setPresets] = useState<VisualStylePreset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadPresets() {
      setLoading(true);
      setError(null);
      try {
        const response = await listVisualStylePresets();
        setPresets(response.items);
      } catch (currentError) {
        setError(
          currentError instanceof Error
            ? currentError.message
            : "No se pudieron cargar los estilos visuales."
        );
      } finally {
        setLoading(false);
      }
    }

    void loadPresets();
  }, []);

  return (
    <section className="visual-styles-view">
      <div className="page-heading">
        <p className="section-label">Estilos visuales</p>
        <h1>Estilos visuales</h1>
        <p>
          Presets locales disponibles para mejorar fotos y videos seleccionados.
          Elige el estilo desde el detalle del evento antes de generar versiones.
        </p>
      </div>

      {error ? <p className="inline-error">{error}</p> : null}

      <section className="visual-style-summary">
        <div>
          <span>Presets activos</span>
          <strong>{loading ? "Cargando" : presets.length}</strong>
        </div>
        <Link className="link-action" to="/events">
          Abrir eventos
        </Link>
      </section>

      {!loading && presets.length === 0 ? (
        <article className="empty-state">
          <h2>Sin presets activos</h2>
          <p>Reinicia el seed base para restaurar los estilos visuales iniciales.</p>
        </article>
      ) : null}

      <section className="visual-style-grid">
        {presets.map((preset) => (
          <article className="visual-style-card" key={preset.id}>
            <p className="section-label">{preset.is_active ? "Activo" : "Inactivo"}</p>
            <h2>{preset.name}</h2>
            <p>{preset.description ?? "Sin descripcion registrada."}</p>
            <code>{preset.slug}</code>
          </article>
        ))}
      </section>
    </section>
  );
}
