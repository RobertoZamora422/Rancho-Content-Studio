# Rancho Content Studio

Aplicacion de escritorio local-first para organizar, analizar y preparar contenido de eventos sociales de Rancho Flor Maria.

El flujo principal es local:

1. El usuario copia o descarga fotos y videos a una carpeta local.
2. Rancho Content Studio selecciona esa carpeta desde la app de escritorio.
3. El backend local procesa el material sin modificar originales.
4. La app genera selecciones, versiones mejoradas, piezas y copies.
5. El usuario exporta una carpeta final lista para publicar o subir manualmente.

## Stack

- Desktop: Tauri.
- Frontend: React + Vite + TypeScript.
- Backend local: Python + FastAPI.
- Base de datos: SQLite.
- Procesamiento local inicial: Pillow para miniaturas/mejoras de fotos y FFmpeg opcional para video basico; futuro OpenCV, ImageHash y scikit-image.
- Metadatos: ExifTool cuando esta disponible, con fallback local.

## Estado actual

Esta base cubre Fase 0, Fase 1, Fase 2, Fase 3, Fase 4, Fase 5, Fase 6, Fase 7, Fase 8, Fase 9, Fase 10 y Fase 11:

- Estructura de repositorio.
- Documentacion base en `docs/`.
- Backend FastAPI minimo con `GET /api/health`.
- SQLite local con PRAGMAs obligatorios.
- Modelos SQLAlchemy base para las tablas principales del sistema.
- Seed inicial idempotente de configuracion local, usuario admin, marca, perfil editorial y presets visuales.
- Frontend React con shell base, navegacion por rutas hash y healthcheck compartido.
- Configuracion local editable para carpeta raiz, FFmpeg y ExifTool.
- Eventos locales: crear, listar, abrir, archivar y dar de baja logicamente.
- Generacion de estructura local de carpetas por evento.
- Importacion desde carpeta local hacia `01_Originales` sin modificar la fuente.
- Registro de fuentes, material original y jobs de escaneo/importacion.
- Procesamiento de metadatos y miniaturas sobre material importado.
- Lectura opcional con ExifTool y fallback local por fecha de archivo.
- Miniaturas locales para fotos y videos en `metadata/thumbnails`.
- Analisis visual local de fotos con puntajes de calidad y hash perceptual.
- Deteccion local de duplicados exactos y fotos visualmente similares.
- Curacion inteligente inicial con estados revisables y cambios manuales.
- Mejora local de fotos seleccionadas con presets basicos y versiones en `04_Mejorados`.
- Mejora local basica de videos seleccionados con FFmpeg cuando esta disponible, sin forzar verticalidad.
- Scaffold Tauri preparado.

No incluye todavia generacion de piezas ni exportacion final.

## Fase 1 implementada

La Fase 1 deja listo el backend local como base de datos y contrato tecnico interno:

- FastAPI inicializado con lifespan de arranque.
- SQLite configurado con:
  - `PRAGMA journal_mode=WAL`
  - `PRAGMA foreign_keys=ON`
  - `PRAGMA synchronous=NORMAL`
- SQLAlchemy crea las tablas principales:
  - `local_app_config`
  - `user`
  - `brand`
  - `editorial_profile`
  - `visual_style_preset`
  - `content_event`
  - `local_media_source`
  - `original_media`
  - `media_analysis`
  - `similarity_group`
  - `similarity_group_item`
  - `curated_media`
  - `enhanced_media`
  - `content_piece`
  - `content_piece_media`
  - `generated_copy`
  - `publishing_calendar_item`
  - `decision_log`
  - `processing_job`
  - `processing_job_log`
  - `export_package`
  - `export_package_item`
- Seed inicial:
  - Usuario admin: Roberto Zamora.
  - Marca: Rancho Flor Maria.
  - Perfil editorial base: calido, natural, cercano, profesional, emojis sutiles.
  - Presets visuales: `natural_premium`, `calido_elegante`, `color_vivo_fiesta`, `suave_bodas`, `brillante_xv`, `sobrio_corporativo`.

La Fase 1 no implementa todavia endpoints CRUD sobre estas tablas. Solo deja persistencia, relaciones y datos base listos para fases posteriores.

## Fase 2 implementada

La Fase 2 deja lista la base de escritorio y frontend para construir los modulos reales por fases:

- React + Vite + TypeScript compila correctamente.
- Navegacion principal con rutas hash, compatible con el contenedor desktop de Tauri:
  - `#/`
  - `#/events`
  - `#/library`
  - `#/pieces`
  - `#/calendar`
  - `#/editorial-profile`
  - `#/visual-styles`
  - `#/settings`
- Shell de aplicacion con menu lateral persistente.
- Barra superior con estado del backend local, version de API y endpoint configurado.
- Pantalla Inicio conectada a `GET /api/health`.
- Paginas base preparadas para eventos, biblioteca, piezas, calendario, perfil editorial, estilos visuales y configuracion.
- Scaffold Tauri v2 en `desktop/src-tauri/`.

La Fase 2 no arranca automaticamente el backend desde Tauri todavia. Por ahora el backend se ejecuta manualmente con `python run_backend.py`.

## Fase 3 implementada

La Fase 3 agrega configuracion local persistida en SQLite:

- `GET /api/config`: lee carpeta raiz local, ruta FFmpeg y ruta ExifTool.
- `PUT /api/config`: guarda rutas locales candidatas.
- `POST /api/config/validate-tools`: valida carpeta raiz y disponibilidad de FFmpeg/ExifTool.
- Pantalla `#/settings` funcional en React:
  - Campo para carpeta raiz local.
  - Campo opcional para FFmpeg.
  - Campo opcional para ExifTool.
  - Guardado en SQLite.
  - Validacion de herramientas desde backend.

La validacion de FFmpeg y ExifTool funciona asi:

- Si se configura una ruta, el backend verifica que exista como archivo ejecutable y ejecuta el comando de version.
- Si no se configura ruta, el backend busca `ffmpeg` y `exiftool` en `PATH`.
- La ausencia de estas herramientas no rompe la app; se reporta como `No disponible` para fases posteriores.

La carpeta raiz local debe existir antes de validarla. En fases posteriores, los eventos se crearan dentro de esa raiz usando nombres seguros para Windows.

## Fase 4 implementada

La Fase 4 agrega gestion inicial de eventos:

- `GET /api/events`: lista eventos activos.
- `GET /api/events?include_archived=true`: incluye eventos archivados.
- `POST /api/events`: crea evento y genera carpetas locales.
- `GET /api/events/{id}`: abre detalle de evento.
- `PUT /api/events/{id}`: actualiza datos basicos sin renombrar carpetas existentes.
- `POST /api/events/{id}/archive`: archiva el evento.
- `DELETE /api/events/{id}`: baja logica en SQLite; no borra carpetas ni archivos.

Al crear un evento, el backend exige que `workspace.root` exista y genera una carpeta segura para Windows:

```text
2026-05-10_Boda_Ana_y_Luis/
  01_Originales/
  02_Seleccionados/
  03_Descartados_Logicos/
  04_Mejorados/
  05_Reels/
  06_Carruseles/
  07_Historias/
  08_Copies/
  09_Listo_Para_Publicar/
  10_Publicado/
  metadata/
```

La pantalla `#/events` permite crear y listar eventos. La ruta `#/events/{id}` muestra detalle, ruta local, carpetas creadas y acciones de archivo/baja logica.

## Fase 5 implementada

La Fase 5 agrega importacion local inicial:

- `POST /api/events/{id}/sources`: registra una carpeta fuente externa al evento.
- `GET /api/events/{id}/sources`: lista fuentes registradas.
- `POST /api/events/{id}/scan`: escanea archivos compatibles.
- `POST /api/events/{id}/import`: copia archivos compatibles a `01_Originales`.
- `GET /api/events/{id}/media/original`: lista material original importado.
- `GET /api/jobs/{id}` y `GET /api/events/{id}/jobs`: consultan jobs y logs.

Reglas aplicadas:

- La carpeta fuente debe existir.
- La carpeta fuente no puede estar dentro de la carpeta del evento.
- Los archivos fuente no se modifican ni se borran.
- La importacion copia archivos compatibles a `01_Originales`.
- La importacion es idempotente por checksum dentro del evento; si se ejecuta otra vez, omite archivos ya importados.
- Los errores por archivo se registran en `processing_job_log` y no detienen todo el proceso.

Extensiones iniciales compatibles:

- Imagen: `.jpg`, `.jpeg`, `.png`, `.webp`, `.tif`, `.tiff`, `.heic`.
- Video: `.mp4`, `.mov`, `.m4v`, `.avi`, `.mkv`, `.webm`, `.mts`, `.m2ts`.

La pantalla `#/events/{id}` permite registrar fuente, escanear, importar, ver material original y revisar jobs recientes.

## Fase 6 implementada

La Fase 6 agrega procesamiento local de metadatos y miniaturas:

- `POST /api/events/{id}/process-metadata`: ejecuta lectura de metadatos y generacion de miniaturas.
- `GET /api/media/original/{media_id}/thumbnail`: sirve la miniatura generada al frontend.
- Job `write_metadata`: actualiza `capture_datetime`, `date_source`, dimensiones, duracion cuando exista y `metadata_json`.
- Job `generate_thumbnails`: crea miniaturas JPEG en `metadata/thumbnails`.
- ExifTool se usa si esta configurado o disponible en `PATH`.
- Si ExifTool no esta disponible, se usa fallback local con fecha de archivo, tamano y dimensiones de imagen cuando Pillow puede leerlas.
- Para videos, si FFmpeg esta disponible se intenta extraer un frame; si no esta disponible o falla, se genera una miniatura local de respaldo tipo video.

Reglas aplicadas:

- Los originales importados no se modifican.
- Los errores por archivo se registran en `processing_job_log` y no detienen el procesamiento completo.
- La ruta guardada en `thumbnail_path` es relativa a la carpeta del evento.
- La UI de `Material original` usa el endpoint de miniaturas, muestra fecha de captura, fuente de fecha y datos tecnicos basicos.

## Fase 7 implementada

La Fase 7 agrega analisis visual local de fotos:

- `POST /api/events/{id}/analyze-photos`: analiza fotos importadas del evento.
- Job `analyze_media`: registra progreso, conteos y errores por archivo.
- Guarda o actualiza `media_analysis` por cada foto valida.
- Calcula puntajes normalizados de nitidez, brillo, contraste, ruido estimado, exposicion y calidad global.
- Genera `perceptual_hash` local tipo average hash para fases posteriores de duplicados.
- Guarda mediciones base en `raw_metrics_json` y version `local-pillow-basic-v1`.
- Omite videos en Fase 7 y los deja para el analisis de video posterior.
- La UI de `Material original` permite ejecutar `Analizar fotos` y muestra calidad, nitidez, brillo, contraste y exposicion.

Reglas aplicadas:

- Los originales importados no se modifican.
- El analisis es local y usa Pillow; no introduce dependencias cloud.
- Una imagen corrupta registra error por archivo y no detiene todo el job.

## Fase 8 implementada

La Fase 8 agrega deteccion local de duplicados y similares:

- `POST /api/events/{id}/detect-similarity`: recalcula grupos generados de similitud.
- `GET /api/events/{id}/similarity-groups`: lista grupos detectados y sus alternativas.
- Job `detect_similarity`: registra conteos y logs del proceso.
- Agrupa duplicados exactos por `checksum_sha256`.
- Agrupa fotos visualmente similares comparando `media_analysis.perceptual_hash`.
- Crea `similarity_group` y `similarity_group_item`.
- Define representante sugerido por mejor `overall_quality_score`.
- La UI de detalle muestra grupos, representante sugerido, alternativas, confianza y distancia.

Reglas aplicadas:

- No se borran ni modifican archivos originales.
- La deteccion recalcula solo grupos generados `checksum_duplicate` y `perceptual_hash`.
- Si faltan hashes perceptuales, se registra advertencia y se omiten esas fotos hasta ejecutar `Analizar fotos`.

## Fase 9 implementada

La Fase 9 agrega curacion inteligente y revision manual:

- `POST /api/events/{id}/curate-media`: crea o actualiza estados de curacion.
- `GET /api/events/{id}/curated-media`: lista medios curados con miniatura, analisis y motivo.
- `PATCH /api/events/{id}/curated-media/{curated_id}`: permite cambiar una decision manual.
- Job `curate_media`: registra progreso y motivos por archivo.
- Usa `media_analysis` y `similarity_group` para proponer seleccionados, alternativos, descartes logicos y revision manual.
- Conserva overrides manuales en ejecuciones posteriores.
- Registra decisiones automaticas y manuales en `decision_log`.
- La UI muestra columnas de seleccionados, alternativos, descartes logicos y revision manual.

Estados usados:

- `selected`
- `alternative`
- `rejected_duplicate`
- `rejected_similar`
- `rejected_low_quality`
- `rejected_blurry`
- `rejected_dark`
- `manual_review`
- `user_selected`
- `user_rejected`

Reglas aplicadas:

- Todo descarte es logico y reversible.
- La curacion no borra ni modifica archivos originales.
- Los videos quedan en revision manual hasta implementar analisis avanzado de video.

## Fase 10 implementada

La Fase 10 agrega mejora local de fotos seleccionadas:

- `POST /api/events/{id}/enhance-photos`: genera versiones mejoradas de fotos con estado `selected` o `user_selected`.
- `GET /api/events/{id}/enhanced-media`: lista versiones mejoradas con foto original, preset, estado y ruta local.
- `PATCH /api/events/{id}/enhanced-media/{enhanced_id}`: permite aprobar o rechazar una version sin borrar archivos.
- `GET /api/media/enhanced/{enhanced_id}/file`: sirve la version mejorada al frontend.
- Job `enhance_photos`: registra progreso, conteos y errores por archivo.
- Las salidas se escriben como JPEG en `04_Mejorados` con nombres versionados para no sobrescribir versiones anteriores.
- Usa presets locales: `natural_premium`, `calido_elegante`, `color_vivo_fiesta`, `suave_bodas`, `brillante_xv`, `sobrio_corporativo`.
- Preserva EXIF existente cuando Pillow puede conservarlo y ajusta la fecha de archivo de la version generada.
- Si ExifTool esta disponible, intenta escribir `DateTimeOriginal`, `CreateDate` y `ModifyDate` en la version generada.
- La UI muestra el panel `Mejoras visuales`, comparador original vs mejorado, selector de preset y acciones de aprobar/rechazar.

Reglas aplicadas:

- Los originales importados no se modifican.
- La mejora de Fase 10 solo procesa fotos seleccionadas; los videos se atienden en Fase 11.
- Reprocesar genera una nueva version en lugar de sobrescribir la anterior.
- La aprobacion o rechazo es manual y queda registrada en `decision_log`.

## Fase 11 implementada

La Fase 11 agrega analisis/mejora basica de videos seleccionados:

- `POST /api/events/{id}/enhance-videos`: procesa videos con estado `selected` o `user_selected`.
- Reusa `GET /api/events/{id}/enhanced-media` para listar versiones de fotos y videos.
- Reusa `PATCH /api/events/{id}/enhanced-media/{enhanced_id}` para aprobar o rechazar resultados.
- Reusa `GET /api/media/enhanced/{enhanced_id}/file` y sirve el tipo MIME real del archivo generado.
- Job `enhance_videos`: registra disponibilidad de FFmpeg, progreso, conteos y errores por archivo.
- Valida FFmpeg desde la configuracion local o `PATH`; si no esta disponible, crea job con error controlado y no modifica archivos.
- Aplica ajustes basicos con FFmpeg: luz, contraste, saturacion y nitidez moderada.
- Mantiene el contenedor original por defecto para `.mp4`, `.mov` y `.m4v`; otros contenedores se normalizan a `.mp4`.
- No redimensiona ni convierte obligatoriamente a vertical.
- Modo `auto`: procesa video completo si es corto y crea un segmento simple en `05_Reels` si supera el limite configurado.
- Modo `full`: procesa el video completo en `04_Mejorados`.
- Modo `segment`: crea un clip simple centrado en `05_Reels`.
- Intenta generar miniatura del video mejorado en `metadata/thumbnails`.
- Ajusta fecha de archivo y usa ExifTool si esta disponible para escribir fechas en la version generada.
- La UI permite elegir preset, modo de video, ejecutar mejora y comparar/reproducir el resultado.

Reglas aplicadas:

- Los videos originales no se modifican.
- Los errores de video se registran por archivo y no rompen el evento.
- Reprocesar genera una nueva version y no sobrescribe versiones anteriores.
- El usuario aprueba o rechaza cada resultado manualmente.

## Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run_backend.py
```

Healthcheck:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

Configuracion:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/config
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/config/validate-tools
```

Eventos:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/events
```

Fuentes e importacion:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/events/1/sources
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/events/1/scan
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/events/1/import
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/events/1/process-metadata
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/events/1/analyze-photos
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/events/1/detect-similarity
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/events/1/curate-media
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/events/1/enhance-photos -ContentType "application/json" -Body '{"preset_slug":"natural_premium"}'
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/events/1/enhance-videos -ContentType "application/json" -Body '{"preset_slug":"natural_premium","processing_mode":"auto","max_full_duration_seconds":90,"clip_duration_seconds":30}'
Invoke-RestMethod http://127.0.0.1:8000/api/events/1/media/original
Invoke-RestMethod http://127.0.0.1:8000/api/events/1/similarity-groups
Invoke-RestMethod http://127.0.0.1:8000/api/events/1/curated-media
Invoke-RestMethod http://127.0.0.1:8000/api/events/1/enhanced-media
```

Pruebas:

```powershell
cd backend
pytest
```

## Frontend / Desktop

```powershell
cd desktop
npm install
npm run dev
```

Por defecto el frontend consulta:

```text
http://127.0.0.1:8000/api/health
```

Build web:

```powershell
cd desktop
npm run build
```

Tauri dev:

```powershell
cd desktop
npm run tauri dev
```

Tauri requiere Rust y dependencias del sistema instaladas.

## Limitaciones pendientes

- No hay migraciones Alembic todavia; durante estas primeras fases el esquema se crea con `Base.metadata.create_all`.
- Hay un ajuste incremental minimo para agregar `original_media.metadata_json` en bases existentes hasta introducir Alembic.
- Los endpoints de piezas, copy, biblioteca y calendario quedan para fases posteriores.
- Los modelos usan estados como strings simples; las reglas de transicion y validaciones de negocio se agregaran en servicios backend.
- El analisis visual de Fase 7 es basico y local; no detecta rostros, composicion semantica ni categorias automaticas todavia.
- El analisis semantico avanzado de videos queda pendiente; Fase 11 solo aplica mejora local basica y segmento simple.
- La similitud visual de Fase 8 usa average hash y un umbral fijo; casos dudosos deben revisarse manualmente.
- La importacion actual omite duplicados exactos por checksum, asi que los grupos exactos apareceran sobre datos existentes o registros creados antes de esa regla.
- La curacion de Fase 9 usa reglas iniciales de calidad/similitud; todavia no clasifica diversidad semantica como protagonistas, comida o baile.
- La mejora de Fase 10 aplica ajustes basicos con Pillow; no hay retoque avanzado, mascaras, restauracion de rostros ni reduccion de ruido profesional.
- La mejora de video de Fase 11 requiere FFmpeg real para generar archivos; en esta maquina FFmpeg no esta disponible en `PATH`, por lo que se probo el manejo controlado de ausencia de herramienta, no la codificacion real.
- La estabilizacion avanzada queda pendiente; Fase 11 no usa filtros `vidstab`.
- La escritura EXIF completa en versiones mejoradas depende de ExifTool. Sin ExifTool, se conserva EXIF existente si Pillow puede hacerlo y se ajusta la fecha de archivo.
- Si ExifTool no esta disponible, la fecha usa fallback local y la precision puede ser limitada.
- Si FFmpeg no esta disponible o el video no es legible, la miniatura de video es un respaldo local, no un frame real.
- La UI todavia no abre carpetas en el explorador del sistema; muestra la ruta local para uso manual.
- La seleccion de carpeta todavia es manual por texto; el selector nativo Tauri queda pendiente.
- No se ha validado `npm run tauri dev` porque requiere Rust/Cargo y dependencias Tauri del sistema.

## Variables utiles

Backend:

```text
RANCHO_STUDIO_DB_PATH=C:\ruta\local\rancho_content_studio.sqlite3
```

Frontend:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Validacion de Fase 2

Con backend levantado en `127.0.0.1:8000`:

```powershell
cd backend
python run_backend.py
```

En otra terminal:

```powershell
cd desktop
npm run dev
```

Abrir:

```text
http://127.0.0.1:5173/#/
```

La barra superior debe mostrar `Conectado` y version `0.1.0`.

Para validar Fase 3, abrir:

```text
http://127.0.0.1:5173/#/settings
```

Guardar rutas locales y ejecutar `Validar herramientas`.

Para validar Fase 4:

1. Configurar una carpeta raiz existente en `#/settings`.
2. Abrir `http://127.0.0.1:5173/#/events`.
3. Crear un evento.
4. Abrir el detalle y confirmar la ruta local generada.

Para validar Fase 5:

1. Abrir el detalle de un evento en `#/events/{id}`.
2. Registrar una carpeta fuente local con archivos de prueba.
3. Ejecutar `Escanear`.
4. Ejecutar `Importar a 01_Originales`.
5. Confirmar que los archivos aparecen en `Material original` y que la carpeta fuente queda intacta.

Para validar Fase 6:

1. Importar material en un evento.
2. En `#/events/{id}`, ejecutar `Procesar metadatos y miniaturas`.
3. Confirmar que `Material original` muestra miniaturas, fecha de captura, fuente de fecha y datos tecnicos.
4. Revisar que `metadata/thumbnails` exista dentro de la carpeta del evento.
5. Consultar los jobs `write_metadata` y `generate_thumbnails` en `GET /api/events/{id}/jobs`.

Para validar Fase 7:

1. Importar fotos en un evento.
2. En `#/events/{id}`, ejecutar `Analizar fotos`.
3. Confirmar que las fotos muestran `Calidad` y metricas de nitidez, brillo, contraste y exposicion.
4. Confirmar que los videos quedan como `No aplica en Fase 7`.
5. Consultar `GET /api/events/{id}/jobs` y verificar el job `analyze_media`.

Para validar Fase 8:

1. Importar fotos en un evento.
2. Ejecutar `Analizar fotos`.
3. Ejecutar `Detectar duplicados y similares`.
4. Confirmar que aparece la seccion `Duplicados y similares`.
5. Consultar `GET /api/events/{id}/similarity-groups` y verificar representantes y alternativas.
6. Consultar `GET /api/events/{id}/jobs` y verificar el job `detect_similarity`.

Para validar Fase 9:

1. Ejecutar Fase 7 y Fase 8 sobre un evento con fotos.
2. Ejecutar `Ejecutar curacion inteligente`.
3. Confirmar que aparece la seccion `Curacion inteligente`.
4. Cambiar un medio con `Seleccionar`, `Revisar` o `Rechazar`.
5. Ejecutar de nuevo la curacion y confirmar que la decision manual se conserva.
6. Consultar `GET /api/events/{id}/jobs` y verificar el job `curate_media`.

Para validar Fase 10:

1. Ejecutar curacion sobre un evento con fotos.
2. Marcar una o mas fotos como `Seleccionar`.
3. En `Mejoras visuales`, elegir preset de fotos y ejecutar `Mejorar fotos`.
4. Confirmar que se crean archivos versionados en `04_Mejorados`.
5. Aprobar o rechazar una version y verificar el estado en `GET /api/events/{id}/enhanced-media`.
6. Consultar `GET /api/events/{id}/jobs` y verificar el job `enhance_photos`.

Para validar Fase 11:

1. Configurar FFmpeg en `#/settings` o dejarlo sin configurar para validar el error controlado.
2. Ejecutar curacion sobre un evento con videos.
3. Marcar un video como `Seleccionar`.
4. En `Mejoras visuales`, elegir preset y modo de video.
5. Ejecutar `Mejorar videos`.
6. Si FFmpeg esta disponible, confirmar archivo nuevo en `04_Mejorados` o `05_Reels`.
7. Si FFmpeg no esta disponible, confirmar que aparece un job `enhance_videos` con error por archivo y que no se modifico el original.

## Reglas centrales

- No convertir el sistema en una app cloud.
- No introducir Google Drive como dependencia.
- No modificar archivos originales.
- No borrar archivos automaticamente.
- No forzar videos a 9:16.
- Mantener SQLite como base local.
- Mantener FastAPI como backend local.
- Mantener Tauri + React + TypeScript para escritorio.
- Los trabajos largos deben reportar progreso.
- Los errores por archivo deben registrarse y no detener todo el proceso.
