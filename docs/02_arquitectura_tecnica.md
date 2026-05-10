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
