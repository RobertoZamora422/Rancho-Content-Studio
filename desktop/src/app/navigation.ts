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
  path: string;
  description: string;
};

export const navigationItems: NavigationItem[] = [
  {
    key: "dashboard",
    label: "Inicio",
    path: "/",
    description: "Resumen operativo y conexion con backend local."
  },
  {
    key: "events",
    label: "Eventos",
    path: "/events",
    description: "Creacion, listado y apertura de eventos locales."
  },
  {
    key: "library",
    label: "Biblioteca",
    path: "/library",
    description: "Consulta futura de material y piezas ya preparadas."
  },
  {
    key: "pieces",
    label: "Piezas de contenido",
    path: "/pieces",
    description: "Reels, carruseles, historias y publicaciones sugeridas."
  },
  {
    key: "calendar",
    label: "Calendario",
    path: "/calendar",
    description: "Planificacion manual de publicaciones."
  },
  {
    key: "editorialProfile",
    label: "Perfil editorial",
    path: "/editorial-profile",
    description: "Tono, frases y reglas de copy de la marca."
  },
  {
    key: "visualStyles",
    label: "Estilos visuales",
    path: "/visual-styles",
    description: "Presets locales para mejoras visuales futuras."
  },
  {
    key: "settings",
    label: "Configuracion",
    path: "/settings",
    description: "Backend local, herramientas y rutas de trabajo."
  }
];
