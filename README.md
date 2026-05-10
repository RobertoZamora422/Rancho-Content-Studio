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

Esta base cubre la inicializacion tecnica:

- Estructura de repositorio.
- Documentacion base en `docs/`.
- Backend FastAPI minimo con `GET /api/health`.
- SQLite inicial con PRAGMAs obligatorios.
- Frontend React minimo con layout base y healthcheck.
- Scaffold Tauri preparado.

No incluye todavia importacion, analisis visual, curacion, mejoras, piezas ni exportacion final.

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

## Variables utiles

Backend:

```text
RANCHO_STUDIO_DB_PATH=C:\ruta\local\rancho_content_studio.sqlite3
```

Frontend:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

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
