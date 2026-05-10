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
- Procesamiento futuro: OpenCV, Pillow, ImageHash, scikit-image, FFmpeg, ExifTool.

## Estado actual

Esta base cubre Fase 0, Fase 1, Fase 2 y Fase 3:

- Estructura de repositorio.
- Documentacion base en `docs/`.
- Backend FastAPI minimo con `GET /api/health`.
- SQLite local con PRAGMAs obligatorios.
- Modelos SQLAlchemy base para las tablas principales del sistema.
- Seed inicial idempotente de configuracion local, usuario admin, marca, perfil editorial y presets visuales.
- Frontend React con shell base, navegacion por rutas hash y healthcheck compartido.
- Configuracion local editable para carpeta raiz, FFmpeg y ExifTool.
- Scaffold Tauri preparado.

No incluye todavia importacion, analisis visual, curacion, mejoras, piezas ni exportacion final.

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
- Los endpoints REST completos de configuracion, eventos, importacion, jobs, curacion, mejoras, piezas, copy, biblioteca y calendario quedan para fases posteriores.
- Los modelos usan estados como strings simples; las reglas de transicion y validaciones de negocio se agregaran en servicios backend.
- No existe procesamiento multimedia aun.
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
