export type NavigationKey =
  | "dashboard"
  | "events"
  | "library"
  | "pieces"
  | "calendar"
  | "editorialProfile"
  | "visualStyles"
  | "settings";

export type NavigationItem = {
  key: NavigationKey;
  label: string;
};

export const navigationItems: NavigationItem[] = [
  { key: "dashboard", label: "Inicio" },
  { key: "events", label: "Eventos" },
  { key: "library", label: "Biblioteca" },
  { key: "pieces", label: "Piezas de contenido" },
  { key: "calendar", label: "Calendario" },
  { key: "editorialProfile", label: "Perfil editorial" },
  { key: "visualStyles", label: "Estilos visuales" },
  { key: "settings", label: "Configuracion" }
];
