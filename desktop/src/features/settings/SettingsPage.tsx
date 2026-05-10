import { useEffect, useMemo, useState } from "react";

import { getConfig, updateConfig, validateTools } from "../../services/configService";
import type { AppConfigUpdate, ConfigValidation, ToolValidationResult } from "../../types/config";

type FormState = {
  workspaceRoot: string;
  ffmpegPath: string;
  exiftoolPath: string;
};

const emptyForm: FormState = {
  workspaceRoot: "",
  ffmpegPath: "",
  exiftoolPath: ""
};

function toNullablePath(value: string): string | null {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function buildPayload(form: FormState): AppConfigUpdate {
  return {
    workspace_root: toNullablePath(form.workspaceRoot),
    ffmpeg_path: toNullablePath(form.ffmpegPath),
    exiftool_path: toNullablePath(form.exiftoolPath)
  };
}

export function SettingsPage() {
  const [form, setForm] = useState<FormState>(emptyForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validation, setValidation] = useState<ConfigValidation | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadConfig() {
      setLoading(true);
      setError(null);
      try {
        const config = await getConfig(controller.signal);
        setForm({
          workspaceRoot: config.workspace_root ?? "",
          ffmpegPath: config.ffmpeg_path ?? "",
          exiftoolPath: config.exiftool_path ?? ""
        });
      } catch (currentError) {
        setError(
          currentError instanceof Error
            ? currentError.message
            : "No se pudo cargar la configuracion local."
        );
      } finally {
        setLoading(false);
      }
    }

    void loadConfig();

    return () => controller.abort();
  }, []);

  const canSubmit = useMemo(() => !loading && !saving, [loading, saving]);

  async function handleSave() {
    setSaving(true);
    setMessage(null);
    setError(null);
    setValidation(null);

    try {
      const config = await updateConfig(buildPayload(form));
      setForm({
        workspaceRoot: config.workspace_root ?? "",
        ffmpegPath: config.ffmpeg_path ?? "",
        exiftoolPath: config.exiftool_path ?? ""
      });
      setMessage("Configuracion guardada en SQLite local.");
    } catch (currentError) {
      setError(
        currentError instanceof Error
          ? currentError.message
          : "No se pudo guardar la configuracion."
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleValidate() {
    setValidating(true);
    setMessage(null);
    setError(null);

    try {
      setValidation(await validateTools());
      setMessage("Validacion de herramientas completada.");
    } catch (currentError) {
      setError(
        currentError instanceof Error
          ? currentError.message
          : "No se pudo validar la configuracion."
      );
    } finally {
      setValidating(false);
    }
  }

  return (
    <section className="settings-view">
      <div className="page-heading">
        <p className="section-label">Configuracion</p>
        <h1>Configuracion local</h1>
        <p>
          Define la carpeta raiz de trabajo y las rutas opcionales de FFmpeg y
          ExifTool. La app sigue funcionando localmente y sin depender de la nube.
        </p>
      </div>

      {error ? <p className="inline-error">{error}</p> : null}
      {message ? <p className="inline-success">{message}</p> : null}

      <section className="settings-panel">
        <label className="field-group">
          <span>Carpeta raiz local</span>
          <input
            disabled={loading}
            onChange={(event) =>
              setForm((current) => ({ ...current, workspaceRoot: event.target.value }))
            }
            placeholder="C:\\Rancho Content Studio"
            value={form.workspaceRoot}
          />
        </label>

        <label className="field-group">
          <span>Ruta FFmpeg</span>
          <input
            disabled={loading}
            onChange={(event) =>
              setForm((current) => ({ ...current, ffmpegPath: event.target.value }))
            }
            placeholder="ffmpeg en PATH o C:\\tools\\ffmpeg\\bin\\ffmpeg.exe"
            value={form.ffmpegPath}
          />
        </label>

        <label className="field-group">
          <span>Ruta ExifTool</span>
          <input
            disabled={loading}
            onChange={(event) =>
              setForm((current) => ({ ...current, exiftoolPath: event.target.value }))
            }
            placeholder="exiftool en PATH o C:\\tools\\exiftool.exe"
            value={form.exiftoolPath}
          />
        </label>

        <div className="settings-actions">
          <button
            className="secondary-action"
            disabled={!canSubmit}
            onClick={handleSave}
            type="button"
          >
            {saving ? "Guardando" : "Guardar configuracion"}
          </button>
          <button
            className="outline-action"
            disabled={loading || saving || validating}
            onClick={handleValidate}
            type="button"
          >
            {validating ? "Validando" : "Validar herramientas"}
          </button>
        </div>
      </section>

      <section className="validation-grid">
        <ValidationCard
          label="Carpeta raiz"
          ok={validation?.workspace_root_exists ?? null}
          detail={
            validation
              ? validation.workspace_root_error ?? "Carpeta disponible."
              : "Pendiente de validacion."
          }
        />
        <ToolValidationCard label="FFmpeg" result={validation?.ffmpeg ?? null} />
        <ToolValidationCard label="ExifTool" result={validation?.exiftool ?? null} />
      </section>
    </section>
  );
}

type ValidationCardProps = {
  label: string;
  ok: boolean | null;
  detail: string;
};

function ValidationCard({ label, ok, detail }: ValidationCardProps) {
  return (
    <article className="validation-card">
      <p className="metric-label">{label}</p>
      <strong className={ok === null ? "pending" : ok ? "available" : "missing"}>
        {ok === null ? "Pendiente" : ok ? "Disponible" : "Requiere atencion"}
      </strong>
      <p>{detail}</p>
    </article>
  );
}

type ToolValidationCardProps = {
  label: string;
  result: ToolValidationResult | null;
};

function ToolValidationCard({ label, result }: ToolValidationCardProps) {
  return (
    <article className="validation-card">
      <p className="metric-label">{label}</p>
      <strong className={result === null ? "pending" : result.available ? "available" : "missing"}>
        {result === null ? "Pendiente" : result.available ? "Disponible" : "No disponible"}
      </strong>
      <p>{result?.version ?? result?.error ?? "Pendiente de validacion."}</p>
      {result?.resolved_path ? <code>{result.resolved_path}</code> : null}
    </article>
  );
}
