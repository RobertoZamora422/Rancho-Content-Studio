# 08 Plan Tecnico de Implementacion

## Fases

0. Repositorio, README, AGENTS y docs base.
1. Backend FastAPI + SQLite + modelos base + seed.
2. Tauri + React base + navegacion + healthcheck.
3. Configuracion local: carpeta raiz, FFmpeg, ExifTool.
4. Eventos: crear, listar, abrir, carpetas locales.
5. Importacion desde carpeta local.
6. Metadatos y miniaturas.
7. Analisis visual de fotos.
8. Duplicados y similares.
9. Curacion inteligente y revision manual.
10. Mejora de fotos.
11. Video basico.
12. Piezas de contenido.
13. Perfil editorial y copywriting.
14. Exportacion final.
15. Biblioteca y calendario.
16. Pulido, pruebas y empaquetado.

## Estado de esta implementacion

La base actual cubre Fase 0, Fase 1, Fase 2, Fase 3, Fase 4, Fase 5 y Fase 6. El backend local ya tiene modelos base, seed inicial, endpoints de configuracion, endpoints de eventos, importacion local inicial y procesamiento de metadatos/miniaturas. El frontend desktop ya tiene shell, rutas de navegacion, healthcheck visible, pantalla de configuracion local, gestion inicial de eventos, flujo de importacion desde carpeta local y vista de material original con miniaturas.

## Fase 6 implementada

- Endpoint `POST /api/events/{id}/process-metadata`.
- Job `write_metadata` para actualizar fecha de captura, fuente, dimensiones, duracion y `metadata_json`.
- Job `generate_thumbnails` para crear JPEGs en `metadata/thumbnails`.
- Endpoint `GET /api/media/original/{media_id}/thumbnail` para que la UI cargue miniaturas sin abrir rutas locales directas.
- ExifTool se usa si esta disponible; si no, se registra advertencia y se usa fallback local.
- Para videos se intenta extraer frame con FFmpeg; si falla o no esta disponible, se crea miniatura local de respaldo.
- La UI de `Material original` muestra miniatura, fecha, fuente y datos tecnicos basicos.

## Criterios por bloque

- Ejecuta sin errores criticos.
- Tiene instrucciones de prueba.
- Respeta reglas obligatorias.
- No introduce dependencias cloud.
- No rompe fases previas.
- Actualiza documentacion si corresponde.
