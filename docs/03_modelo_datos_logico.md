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

## Uso actual de piezas de contenido

En Fase 12, `content_piece` se usa para registrar propuestas de reels, carruseles, historias, posts individuales y piezas promocionales. `content_piece_media` mantiene los medios mejorados asociados y su orden dentro de cada pieza. Aprobar o rechazar una pieza cambia su estado sin exportar archivos finales ni modificar medios.

## Uso actual de perfil editorial y copy

En Fase 13, `editorial_profile` guarda tono, nivel emocional, formalidad, reglas de emojis, hashtags, frases preferidas, palabras a evitar, ejemplos aprobados/rechazados y reglas editoriales. `generated_copy` guarda variantes generadas o editadas para una pieza aprobada. Cada copy puede aprobarse o rechazarse, se escribe como `.md` en `08_Copies` y queda disponible para la exportacion final.

## Uso actual de exportaciones

En Fase 14, `export_package` registra paquetes finales creados para un evento y guarda tipo de exportacion, ruta relativa de salida, estado y fecha de finalizacion. `export_package_item` registra cada medio, copy o resumen incluido, su orden, ruta relativa final, estado de metadata y error por archivo si existio. Los paquetes se crean dentro de `09_Listo_Para_Publicar` y no modifican originales ni versiones mejoradas fuente.

## Principios

- SQLite es la fuente de verdad local.
- Los paths apuntan a archivos locales.
- Los originales nunca se modifican.
- Los estados de descarte y aprobacion deben ser reversibles.
- Los jobs deben guardar progreso y logs.
