# 03 Modelo de Datos Logico

## Objetivo

Definir entidades locales para eventos, archivos, analisis, seleccion, versiones, piezas, copy, calendario, decisiones, jobs y exportaciones.

## Tablas objetivo

```text
local_app_config
user
brand
editorial_profile
visual_style_preset
content_event
local_media_source
original_media
media_analysis
similarity_group
similarity_group_item
curated_media
enhanced_media
content_piece
content_piece_media
generated_copy
publishing_calendar_item
decision_log
processing_job
processing_job_log
export_package
export_package_item
```

## Modelo Fase 1 implementado

La Fase 1 crea las tablas principales con SQLAlchemy para dejar lista la persistencia local. Aun no implementa endpoints CRUD ni reglas de negocio avanzadas sobre todo el modelo.

## Uso actual de analisis

En Fase 7, `media_analysis` ya se usa para guardar el analisis visual local de fotos. Cada registro apunta a un `original_media` y contiene puntajes normalizados, hash perceptual, version del algoritmo y mediciones crudas.

## Uso actual de similitud

En Fase 8, `similarity_group` y `similarity_group_item` se usan para agrupar duplicados exactos por checksum y fotos similares por hash perceptual. El grupo guarda un representante sugerido y cada item mantiene su rol dentro del grupo.

## Uso actual de curacion

En Fase 9, `curated_media` se usa para guardar seleccionados, alternativas, descartes logicos y medios en revision manual. Las decisiones manuales se marcan con `is_manual_override` para que una nueva curacion automatica no las reemplace.

## Uso actual de versiones mejoradas

En Fase 10, `enhanced_media` se usa para registrar versiones JPEG generadas desde fotos seleccionadas. En Fase 11, la misma entidad registra videos mejorados o segmentos simples generados desde videos seleccionados. Cada registro apunta al evento, al `original_media` fuente y, cuando aplica, al `curated_media` que lo habilito. La ruta guardada es relativa a la carpeta del evento y apunta a `04_Mejorados` o `05_Reels`; aprobar o rechazar una version cambia su estado sin eliminar archivos.

## Principios

- SQLite es la fuente de verdad local.
- Los paths apuntan a archivos locales.
- Los originales nunca se modifican.
- Los estados de descarte y aprobacion deben ser reversibles.
- Los jobs deben guardar progreso y logs.
