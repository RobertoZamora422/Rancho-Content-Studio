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

La base actual cubre Fase 0, Fase 1, Fase 2, Fase 3, Fase 4, Fase 5, Fase 6, Fase 7, Fase 8 y Fase 9. El backend local ya tiene modelos base, seed inicial, endpoints de configuracion, endpoints de eventos, importacion local inicial, procesamiento de metadatos/miniaturas, analisis visual local de fotos, deteccion de duplicados/similares y curacion inteligente revisable. El frontend desktop ya tiene shell, rutas de navegacion, healthcheck visible, pantalla de configuracion local, gestion inicial de eventos, flujo de importacion desde carpeta local, vista de material original con miniaturas/metricas, grupos similares y curacion manual.

## Fase 6 implementada

- Endpoint `POST /api/events/{id}/process-metadata`.
- Job `write_metadata` para actualizar fecha de captura, fuente, dimensiones, duracion y `metadata_json`.
- Job `generate_thumbnails` para crear JPEGs en `metadata/thumbnails`.
- Endpoint `GET /api/media/original/{media_id}/thumbnail` para que la UI cargue miniaturas sin abrir rutas locales directas.
- ExifTool se usa si esta disponible; si no, se registra advertencia y se usa fallback local.
- Para videos se intenta extraer frame con FFmpeg; si falla o no esta disponible, se crea miniatura local de respaldo.
- La UI de `Material original` muestra miniatura, fecha, fuente y datos tecnicos basicos.

## Fase 7 implementada

- Endpoint `POST /api/events/{id}/analyze-photos`.
- Job `analyze_media` para procesar solo fotos y omitir videos.
- Servicio local con Pillow para nitidez, brillo, contraste, exposicion, ruido estimado y hash perceptual.
- Persistencia en `media_analysis` con version `local-pillow-basic-v1`.
- Reanalizar una foto actualiza el registro existente en vez de duplicarlo.
- La UI de `Material original` muestra calidad global y metricas basicas por foto.
- Videos y categorias semanticas quedan fuera de Fase 7.

## Fase 8 implementada

- Endpoint `POST /api/events/{id}/detect-similarity`.
- Endpoint `GET /api/events/{id}/similarity-groups`.
- Job `detect_similarity` para recalcular grupos generados.
- Deteccion exacta por `checksum_sha256`.
- Deteccion visual por distancia Hamming entre `perceptual_hash`.
- Persistencia en `similarity_group` y `similarity_group_item`.
- Representante sugerido por mejor puntaje global de calidad.
- UI de grupos con representante, alternativas, distancia y confianza.

## Fase 9 implementada

- Endpoint `POST /api/events/{id}/curate-media`.
- Endpoint `GET /api/events/{id}/curated-media`.
- Endpoint `PATCH /api/events/{id}/curated-media/{curated_id}`.
- Job `curate_media` para crear estados explicables.
- Estados `selected`, `alternative`, `rejected_*`, `manual_review`, `user_selected` y `user_rejected`.
- Preserva decisiones manuales en nuevas ejecuciones.
- Registra decisiones automaticas y manuales en `decision_log`.
- UI con columnas de seleccionados, alternativos, descartes logicos y revision manual.

## Criterios por bloque

- Ejecuta sin errores criticos.
- Tiene instrucciones de prueba.
- Respeta reglas obligatorias.
- No introduce dependencias cloud.
- No rompe fases previas.
- Actualiza documentacion si corresponde.
