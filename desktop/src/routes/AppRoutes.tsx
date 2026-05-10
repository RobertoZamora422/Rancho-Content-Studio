import { Navigate, Route, createHashRouter, createRoutesFromElements } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { ModulePage } from "../components/ModulePage";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { SettingsPage } from "../features/settings/SettingsPage";

export const router = createHashRouter(
  createRoutesFromElements(
    <Route element={<AppShell />}>
      <Route index element={<DashboardPage />} />
      <Route
        path="events"
        element={
          <ModulePage
            label="Eventos"
            title="Eventos"
            description="Base preparada para listar, crear y abrir eventos locales en la Fase 4."
            nextPhase="Fase 4"
          />
        }
      />
      <Route
        path="library"
        element={
          <ModulePage
            label="Biblioteca"
            title="Biblioteca"
            description="Vista reservada para consultar material y piezas exportadas cuando existan eventos procesados."
            nextPhase="Fase 15"
          />
        }
      />
      <Route
        path="pieces"
        element={
          <ModulePage
            label="Piezas de contenido"
            title="Piezas de contenido"
            description="Modulo preparado para reels, carruseles, historias y publicaciones sugeridas."
            nextPhase="Fase 12"
          />
        }
      />
      <Route
        path="calendar"
        element={
          <ModulePage
            label="Calendario"
            title="Calendario"
            description="Base para planificar publicaciones y marcar piezas como publicadas manualmente."
            nextPhase="Fase 15"
          />
        }
      />
      <Route
        path="editorial-profile"
        element={
          <ModulePage
            label="Perfil editorial"
            title="Perfil editorial"
            description="Seccion futura para tono, frases preferidas, palabras a evitar y hashtags base."
            nextPhase="Fase 13"
          />
        }
      />
      <Route
        path="visual-styles"
        element={
          <ModulePage
            label="Estilos visuales"
            title="Estilos visuales"
            description="Base para exponer presets locales de mejora visual definidos en SQLite."
            nextPhase="Fase 10"
          />
        }
      />
      <Route
        path="settings"
        element={<SettingsPage />}
      />
      <Route path="*" element={<Navigate replace to="/" />} />
    </Route>
  )
);
