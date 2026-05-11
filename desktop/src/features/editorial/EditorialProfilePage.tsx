import { useEffect, useMemo, useState } from "react";

import {
  getDefaultEditorialProfile,
  updateDefaultEditorialProfile
} from "../../services/editorialService";
import type { EditorialProfile } from "../../types/editorial";

type EditorialForm = {
  name: string;
  tone: string;
  emotionalLevel: string;
  formalityLevel: string;
  emojiStyle: string;
  description: string;
  hashtagsBase: string;
  preferredPhrases: string;
  wordsToAvoid: string;
  approvedExamples: string;
  rejectedExamples: string;
  copyRules: string;
};

const emptyForm: EditorialForm = {
  name: "",
  tone: "",
  emotionalLevel: "moderado",
  formalityLevel: "semi_formal",
  emojiStyle: "sutil",
  description: "",
  hashtagsBase: "",
  preferredPhrases: "",
  wordsToAvoid: "",
  approvedExamples: "",
  rejectedExamples: "",
  copyRules: ""
};

function profileToForm(profile: EditorialProfile): EditorialForm {
  return {
    name: profile.name,
    tone: profile.tone,
    emotionalLevel: profile.emotional_level,
    formalityLevel: profile.formality_level,
    emojiStyle: profile.emoji_style,
    description: profile.description ?? "",
    hashtagsBase: profile.hashtags_base ?? "",
    preferredPhrases: profile.preferred_phrases ?? "",
    wordsToAvoid: profile.words_to_avoid ?? "",
    approvedExamples: profile.approved_examples ?? "",
    rejectedExamples: profile.rejected_examples ?? "",
    copyRules: profile.copy_rules ?? ""
  };
}

function nullableText(value: string): string | null {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

export function EditorialProfilePage() {
  const [form, setForm] = useState<EditorialForm>(emptyForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadProfile() {
      setLoading(true);
      setError(null);
      try {
        const profile = await getDefaultEditorialProfile();
        setForm(profileToForm(profile));
      } catch (currentError) {
        setError(
          currentError instanceof Error
            ? currentError.message
            : "No se pudo cargar el perfil editorial."
        );
      } finally {
        setLoading(false);
      }
    }

    void loadProfile();
  }, []);

  const canSave = useMemo(
    () => !loading && !saving && form.name.trim().length > 0 && form.tone.trim().length > 0,
    [form.name, form.tone, loading, saving]
  );

  async function handleSave() {
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      const profile = await updateDefaultEditorialProfile({
        approved_examples: nullableText(form.approvedExamples),
        copy_rules: nullableText(form.copyRules),
        description: nullableText(form.description),
        emoji_style: form.emojiStyle,
        emotional_level: form.emotionalLevel,
        formality_level: form.formalityLevel,
        hashtags_base: nullableText(form.hashtagsBase),
        name: form.name,
        preferred_phrases: nullableText(form.preferredPhrases),
        rejected_examples: nullableText(form.rejectedExamples),
        tone: form.tone,
        words_to_avoid: nullableText(form.wordsToAvoid)
      });
      setForm(profileToForm(profile));
      setMessage("Perfil editorial guardado en SQLite local.");
    } catch (currentError) {
      setError(
        currentError instanceof Error
          ? currentError.message
          : "No se pudo guardar el perfil editorial."
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="editorial-view">
      <div className="page-heading">
        <p className="section-label">Fase 13</p>
        <h1>Perfil editorial</h1>
        <p>
          Define el tono, reglas y referencias que usara el generador local de copy. La IA externa
          no es obligatoria para esta fase.
        </p>
      </div>

      {error ? <p className="inline-error">{error}</p> : null}
      {message ? <p className="inline-success">{message}</p> : null}

      <section className="settings-panel editorial-form">
        <label className="field-group">
          <span>Nombre del perfil</span>
          <input
            disabled={loading}
            onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
            value={form.name}
          />
        </label>
        <label className="field-group">
          <span>Tono</span>
          <input
            disabled={loading}
            onChange={(event) => setForm((current) => ({ ...current, tone: event.target.value }))}
            value={form.tone}
          />
        </label>
        <label className="field-group">
          <span>Nivel emocional</span>
          <select
            disabled={loading}
            onChange={(event) =>
              setForm((current) => ({ ...current, emotionalLevel: event.target.value }))
            }
            value={form.emotionalLevel}
          >
            <option value="bajo">Bajo</option>
            <option value="moderado">Moderado</option>
            <option value="alto">Alto</option>
          </select>
        </label>
        <label className="field-group">
          <span>Formalidad</span>
          <select
            disabled={loading}
            onChange={(event) =>
              setForm((current) => ({ ...current, formalityLevel: event.target.value }))
            }
            value={form.formalityLevel}
          >
            <option value="casual">Casual</option>
            <option value="semi_formal">Semi formal</option>
            <option value="formal">Formal</option>
          </select>
        </label>
        <label className="field-group">
          <span>Emojis</span>
          <select
            disabled={loading}
            onChange={(event) =>
              setForm((current) => ({ ...current, emojiStyle: event.target.value }))
            }
            value={form.emojiStyle}
          >
            <option value="sin_emojis">Sin emojis</option>
            <option value="sutil">Sutil</option>
            <option value="moderado">Moderado</option>
            <option value="expresivo">Expresivo</option>
          </select>
        </label>
        <label className="field-group span-3">
          <span>Descripcion</span>
          <textarea
            disabled={loading}
            onChange={(event) =>
              setForm((current) => ({ ...current, description: event.target.value }))
            }
            value={form.description}
          />
        </label>
        <label className="field-group span-3">
          <span>Hashtags base</span>
          <textarea
            disabled={loading}
            onChange={(event) =>
              setForm((current) => ({ ...current, hashtagsBase: event.target.value }))
            }
            value={form.hashtagsBase}
          />
        </label>
        <label className="field-group span-3">
          <span>Frases preferidas</span>
          <textarea
            disabled={loading}
            onChange={(event) =>
              setForm((current) => ({ ...current, preferredPhrases: event.target.value }))
            }
            value={form.preferredPhrases}
          />
        </label>
        <label className="field-group span-3">
          <span>Palabras o frases a evitar</span>
          <textarea
            disabled={loading}
            onChange={(event) =>
              setForm((current) => ({ ...current, wordsToAvoid: event.target.value }))
            }
            value={form.wordsToAvoid}
          />
        </label>
        <label className="field-group span-3">
          <span>Ejemplos aprobados</span>
          <textarea
            disabled={loading}
            onChange={(event) =>
              setForm((current) => ({ ...current, approvedExamples: event.target.value }))
            }
            value={form.approvedExamples}
          />
        </label>
        <label className="field-group span-3">
          <span>Ejemplos rechazados</span>
          <textarea
            disabled={loading}
            onChange={(event) =>
              setForm((current) => ({ ...current, rejectedExamples: event.target.value }))
            }
            value={form.rejectedExamples}
          />
        </label>
        <label className="field-group span-3">
          <span>Reglas adicionales</span>
          <textarea
            disabled={loading}
            onChange={(event) =>
              setForm((current) => ({ ...current, copyRules: event.target.value }))
            }
            value={form.copyRules}
          />
        </label>

        <div className="settings-actions span-3">
          <button className="secondary-action" disabled={!canSave} onClick={handleSave} type="button">
            {saving ? "Guardando" : "Guardar perfil editorial"}
          </button>
        </div>
      </section>
    </section>
  );
}
