# 02 Arquitectura Tecnica

## Tipo de aplicacion

Aplicacion de escritorio local-first con backend local.

## Stack

- Desktop: Tauri.
- Frontend: React + Vite + TypeScript.
- Backend local: Python + FastAPI.
- Base de datos: SQLite.
- Imagen: OpenCV, Pillow, ImageHash, scikit-image.
- Video: FFmpeg, OpenCV, PySceneDetect opcional.
- Metadatos: ExifTool.
- IA externa: opcional y bajo demanda.

## Capas backend

```text
models/          Modelos SQLAlchemy
schemas/         Esquemas Pydantic
repositories/    Acceso a datos
services/        Logica de negocio
api/             Rutas FastAPI
workers/         Jobs locales
utils/           Utilidades de archivos, hashes, imagen, video y exif
```

## Flujo de archivos

```text
Google Photos / telefono / camara
Usuario descarga o copia archivos a carpeta local
Rancho Content Studio procesa localmente
La app exporta resultados a carpetas locales
Usuario sube manualmente a Google Photos o redes
```

## SQLite

La base local debe usar:

```sql
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA synchronous = NORMAL;
```

## Dependencias externas

Google Drive no es dependencia del flujo principal. Google Photos no tiene integracion directa en esta etapa.

## Implementacion local de Fase 6

- ExifTool se resuelve desde configuracion local o `PATH`.
- La ausencia de ExifTool no bloquea el procesamiento; se usa fecha de archivo y metadatos locales.
- Pillow genera miniaturas de fotos y miniaturas locales de respaldo para videos.
- FFmpeg se usa solo si esta disponible para extraer frames de video.
- Las miniaturas viven dentro de la carpeta del evento en `metadata/thumbnails`.
- El frontend consume miniaturas mediante FastAPI, no mediante rutas locales directas.

## Implementacion local de Fase 7

- El analisis visual de fotos vive en `services/visual_analysis_service.py`.
- Usa Pillow para abrir imagenes, corregir orientacion EXIF y calcular metricas basicas.
- Guarda resultados en `media_analysis` sin modificar archivos originales.
- Genera un hash perceptual local tipo average hash para la deteccion de duplicados y similares.
- Los videos se omiten en Fase 7 y se analizaran en una fase posterior.

## Implementacion local de Fase 8

- La deteccion vive en `services/similarity_service.py`.
- Los duplicados exactos se agrupan por `checksum_sha256`.
- Las fotos similares se agrupan por distancia Hamming entre `perceptual_hash`.
- El representante sugerido se elige por `overall_quality_score`.
- Los grupos se recalculan en SQLite y no modifican archivos locales.

## Implementacion local de Fase 9

- La curacion vive en `services/curation_service.py`.
- Usa `media_analysis` y `similarity_group` como entradas.
- Guarda estados reversibles en `curated_media`.
- Mantiene overrides manuales y registra cambios en `decision_log`.
- No modifica ni elimina archivos originales.

## Implementacion local de Fase 10

- La mejora de fotos vive en `services/enhancement_service.py`.
- Usa `curated_media` como entrada y procesa solo fotos con estado `selected` o `user_selected`.
- Aplica presets locales con Pillow y guarda versiones JPEG en `04_Mejorados`.
- Cada salida se registra en `enhanced_media` con ruta relativa, preset, estado y notas tecnicas.
- El archivo original importado queda intacto; reprocesar genera un nuevo nombre versionado.
- ExifTool es opcional para escribir fechas EXIF en la version generada; si falta, se conserva EXIF posible y se ajusta la fecha de archivo.
- El frontend consume las versiones mediante FastAPI, no mediante rutas locales directas.

## Implementacion local de Fase 11

- La mejora basica de video se integra en `services/enhancement_service.py`.
- Usa videos en `curated_media` con estado `selected` o `user_selected`.
- Requiere FFmpeg local configurado o disponible en `PATH` para generar versiones.
- Si FFmpeg falta, se registra job/log controlado y no se generan archivos falsos.
- Aplica filtros simples de luz, contraste, saturacion y nitidez moderada.
- No redimensiona ni fuerza salida vertical 9:16.
- Conserva contenedor original para `.mp4`, `.mov` y `.m4v`; otros contenedores se normalizan a `.mp4`.
- Video completo se guarda en `04_Mejorados`; segmentos simples se guardan en `05_Reels`.
- Las versiones se registran en `enhanced_media` y se sirven por FastAPI con MIME detectado.

## Implementacion local de Fase 12

- La generacion de piezas vive en `services/content_piece_service.py`.
- Usa `enhanced_media` con estado `completed` o `approved` y archivo local existente.
- Crea entidades `content_piece` y `content_piece_media`; no exporta archivos finales.
- Las reglas iniciales son deterministicas y locales.
- Evita duplicar piezas con la misma combinacion de tipo y medios.
- La UI `#/pieces` permite generar, revisar, reordenar y aprobar/rechazar piezas.
- Las piezas quedan listas para Fase 13 de copywriting.

## Implementacion local de Fase 13

- El perfil editorial vive en `editorial_profile` y se edita desde `#/editorial-profile`.
- La generacion de copy vive en `services/copywriting_service.py`.
- La API expone `GET/PUT /api/editorial-profile/default`.
- La API expone generacion/listado/edicion de copies bajo cada `content_piece`.
- El motor de Fase 13 es local y deterministico; no usa IA externa obligatoria.
- Solo genera copy para piezas aprobadas.
- Cada variante se guarda en `generated_copy` y como archivo `.md` dentro de `08_Copies`.
- Las decisiones de generacion, edicion, aprobacion o rechazo se registran en jobs y `decision_log`.

## Implementacion local de Fase 14

- La exportacion final vive en `services/export_service.py`.
- La API expone `POST /api/events/{id}/export-package`.
- La API expone `GET /api/events/{id}/export-packages`.
- La API expone `POST /api/events/{id}/export-packages/{package_id}/open-folder`.
- Usa piezas aprobadas, copies aprobados y medios mejorados aprobados como entradas.
- Crea una carpeta unica dentro de `09_Listo_Para_Publicar`; no sobrescribe paquetes anteriores.
- Copia archivos finales con `shutil.copy2`, manteniendo originales y versiones fuente intactos.
- Escribe copies finales como `.txt` y un `resumen_exportacion.txt`.
- Ajusta fecha de archivo a la fecha del evento y usa ExifTool si esta disponible.
- Registra `export_package`, `export_package_item`, job `export_package` y `decision_log`.
- La UI `#/pieces` concentra generacion, aprobacion, copy y exportacion para mantener el flujo humano visible.

## Implementacion local de Fase 15

- La biblioteca vive en `services/library_service.py` y expone consultas historicas sin duplicar archivos.
- El calendario vive en `services/calendar_service.py` y reutiliza `publishing_calendar_item`.
- La UI consume miniaturas y archivos servidos por FastAPI; no abre rutas locales pesadas directamente.
- La planificacion es manual y no publica en redes ni Google Photos.

## Implementacion local de Fase 16

- Los estilos visuales se exponen con `GET /api/visual-styles` desde la tabla `visual_style_preset`.
- El frontend centraliza `API_BASE_URL` y parseo de errores en `services/apiClient.ts`.
- El reset operativo vive en `services/reset_service.py` y se ejecuta con `scripts/reset_local_demo.py`.
- El reset elimina solo registros operativos de SQLite y no borra archivos fisicos.
- La preparacion Tauri mantiene rutas hash y `devUrl` en `http://127.0.0.1:5173`.
