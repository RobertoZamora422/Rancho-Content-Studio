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

## Modelo inicial implementado

La base inicial solo crea `local_app_config` para soportar configuracion local y validar la conexion SQLite. El resto del modelo se implementara por fases.

## Principios

- SQLite es la fuente de verdad local.
- Los paths apuntan a archivos locales.
- Los originales nunca se modifican.
- Los estados de descarte y aprobacion deben ser reversibles.
- Los jobs deben guardar progreso y logs.
