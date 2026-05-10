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
- Genera un hash perceptual local tipo average hash para la futura Fase 8.
- Los videos se omiten en Fase 7 y se analizaran en una fase posterior.

## Implementacion local de Fase 8

- La deteccion vive en `services/similarity_service.py`.
- Los duplicados exactos se agrupan por `checksum_sha256`.
- Las fotos similares se agrupan por distancia Hamming entre `perceptual_hash`.
- El representante sugerido se elige por `overall_quality_score`.
- Los grupos se recalculan en SQLite y no modifican archivos locales.
