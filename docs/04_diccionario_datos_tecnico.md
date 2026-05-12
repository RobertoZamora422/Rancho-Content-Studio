# 04 Diccionario de Datos Tecnico

## Tabla inicial: local_app_config

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| id | integer | Identificador local autoincremental. |
| key | string | Clave unica de configuracion. |
| value | text nullable | Valor serializado como texto. |
| description | string nullable | Descripcion de la configuracion. |
| created_at | datetime | Fecha de creacion. |
| updated_at | datetime | Fecha de ultima actualizacion. |

## Seeds implementados

La Fase 1 crea datos iniciales idempotentes:

- Usuario admin: Roberto Zamora.
- Marca: Rancho Flor Maria.
- Perfil editorial base: calido, natural, cercano, profesional, emojis sutiles.
- Presets visuales: `natural_premium`, `calido_elegante`, `color_vivo_fiesta`, `suave_bodas`, `brillante_xv`, `sobrio_corporativo`.

## Tablas base Fase 1

La implementacion actual crea las tablas principales definidas en el modelo logico. Los campos se mantienen practicos para las primeras fases: identificadores enteros, claves foraneas, rutas locales, estados como texto, timestamps y campos JSON serializados como texto cuando aun no hay contrato final de detalle.

## Campos usados en Fase 6

`original_media` guarda los resultados de metadatos y miniaturas:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| capture_datetime | datetime nullable | Fecha de captura normalizada. |
| date_source | string nullable | Fuente de fecha: ExifTool, fecha de archivo o fecha del evento. |
| width | integer nullable | Ancho detectado cuando esta disponible. |
| height | integer nullable | Alto detectado cuando esta disponible. |
| duration_seconds | float nullable | Duracion de video cuando se puede leer. |
| thumbnail_path | string nullable | Ruta relativa de la miniatura dentro de la carpeta del evento. |
| metadata_json | text nullable | Metadatos tecnicos extraidos y advertencias serializadas como JSON. |

La columna `metadata_json` se agrega de forma incremental en bases SQLite existentes hasta introducir migraciones Alembic.

## Campos usados en Fase 7

`media_analysis` guarda los resultados del analisis visual local de fotos:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| original_media_id | integer | Foto analizada. Es unico para evitar duplicados por reanalisis. |
| sharpness_score | float nullable | Nitidez normalizada de 0 a 100. |
| brightness_score | float nullable | Brillo promedio normalizado de 0 a 100. |
| contrast_score | float nullable | Contraste normalizado de 0 a 100. |
| noise_score | float nullable | Estimacion local de limpieza/ruido de 0 a 100. |
| exposure_score | float nullable | Exposicion estimada de 0 a 100. |
| overall_quality_score | float nullable | Puntaje global ponderado de 0 a 100. |
| perceptual_hash | string nullable | Hash perceptual local para fases de duplicados. |
| analysis_version | string | Version del algoritmo usado. |
| raw_metrics_json | text nullable | Mediciones crudas y metodo serializados como JSON. |
| analyzed_at | datetime | Fecha del analisis mas reciente. |

## Campos usados en Fase 8

`similarity_group` guarda grupos recalculados de duplicados o similitud:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| event_id | integer | Evento al que pertenece el grupo. |
| group_type | string | `checksum_duplicate` o `perceptual_hash`. |
| representative_media_id | integer nullable | Medio sugerido como representante. |
| confidence_score | float nullable | Confianza estimada de 0 a 100. |
| reason | text nullable | Explicacion del agrupamiento. |

`similarity_group_item` guarda los medios dentro del grupo:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| group_id | integer | Grupo de similitud. |
| original_media_id | integer | Medio agrupado. |
| distance_score | float nullable | Distancia frente al representante, 0 si es duplicado exacto. |
| role | string | `representative`, `duplicate` o `alternative`. |
| reason | text nullable | Motivo de inclusion. |

## Campos usados en Fase 9

`curated_media` guarda el estado revisable de curacion:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| event_id | integer | Evento al que pertenece la decision. |
| original_media_id | integer | Medio curado. |
| selection_status | string | Estado de seleccion, alternativa, descarte logico o revision. |
| reason | text nullable | Motivo de seleccion o descarte. |
| score | float nullable | Puntaje usado para ordenar o justificar. |
| selected_by | string | `system` o `user`. |
| is_manual_override | boolean | Indica si el usuario cambio la decision automatica. |

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

## Campos usados en Fase 10 y Fase 11

`enhanced_media` guarda versiones mejoradas de fotos seleccionadas y videos seleccionados:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| event_id | integer | Evento al que pertenece la version. |
| original_media_id | integer | Foto o video original importado usado como fuente. |
| curated_media_id | integer nullable | Decision de curacion que origino la mejora. |
| output_path | string | Ruta relativa del archivo generado dentro de `04_Mejorados` o `05_Reels`. |
| enhancement_type | string | Tipo de mejora local: `photo_basic`, `video_basic` o `video_clip_basic`. |
| preset_slug | string nullable | Preset visual aplicado. |
| status | string | Estado de la version: `completed`, `approved` o `rejected`. |
| width | integer nullable | Ancho de la version generada. |
| height | integer nullable | Alto de la version generada. |
| duration_seconds | float nullable | Duracion de video o segmento generado cuando aplica. |
| notes | text nullable | Detalles serializados como JSON, incluyendo estado de metadatos. |
| approved_at | datetime nullable | Fecha de aprobacion manual. |
| rejected_at | datetime nullable | Fecha de rechazo manual. |

Decisiones de aprobacion/rechazo de versiones mejoradas se registran en `decision_log` con `entity_type = enhanced_media`.

Notas de Fase 11:

- Los videos completos se guardan normalmente en `04_Mejorados`.
- Los segmentos simples sugeridos se guardan en `05_Reels`.
- `notes` incluye modo de procesamiento, plan, estado de formato, estado de metadata y miniatura generada cuando existe.
- El estado de error por archivo vive en `processing_job_log`; no se crea `enhanced_media` falso cuando FFmpeg falta o falla.

## Campos usados en Fase 12

`content_piece` guarda piezas sugeridas para redes sociales:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| event_id | integer | Evento al que pertenece la pieza. |
| piece_type | string | Tipo: `reel`, `carousel`, `story`, `single_post` o `promo_piece`. |
| title | string | Titulo editable de la pieza. |
| purpose | string nullable | Proposito recomendado, por ejemplo `ambiente` o `resumen_evento`. |
| target_platform | string nullable | Plataforma recomendada. |
| aspect_ratio | string nullable | Formato recomendado; no obliga conversion vertical. |
| status | string | Estado: `draft`, `generated`, `in_review`, `approved` o `rejected`. |
| metadata_json | text nullable | Motivo de recomendacion, firma de medios y origen de la regla. |
| approved_at | datetime nullable | Fecha de aprobacion manual. |
| rejected_at | datetime nullable | Fecha de rechazo manual. |

`content_piece_media` guarda los medios ordenados de cada pieza:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| piece_id | integer | Pieza a la que pertenece. |
| original_media_id | integer nullable | Medio original asociado como referencia. |
| enhanced_media_id | integer nullable | Version mejorada usada en la pieza. |
| position | integer | Orden dentro de la pieza. |
| role | string nullable | `cover` para portada sugerida o `sequence` para secuencia. |
| notes | text nullable | Motivo o nota de asociacion. |

## Campos usados en Fase 13

`editorial_profile` se usa como contrato de estilo para copywriting:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| tone | string | Tono general de la marca. |
| emotional_level | string | Nivel emocional: `bajo`, `moderado` o `alto`. |
| formality_level | string | Formalidad: `casual`, `semi_formal` o `formal`. |
| emoji_style | string | Estilo de emojis: `sin_emojis`, `sutil`, `moderado` o `expresivo`. |
| hashtags_base | text nullable | Hashtags base usados por el generador local. |
| preferred_phrases | text nullable | Frases o palabras preferidas. |
| words_to_avoid | text nullable | Palabras o frases que impiden aprobar un copy si aparecen. |
| approved_examples | text nullable | Ejemplos aprobados, alimentados por aprobaciones manuales. |
| rejected_examples | text nullable | Ejemplos rechazados, alimentados por rechazos manuales. |
| copy_rules | text nullable | Reglas editoriales adicionales. |

`generated_copy` guarda variantes de texto:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| piece_id | integer | Pieza asociada. |
| editorial_profile_id | integer nullable | Perfil usado para generar o editar. |
| copy_type | string | `caption`, `reel_short_copy`, `cover_text`, `story_text`, `hashtags` o `cta`. |
| variant_label | string nullable | Etiqueta visible de la variante. |
| body | text | Texto del copy. |
| hashtags_json | text nullable | Hashtags sugeridos serializados como JSON. |
| cta | text nullable | Llamado a la accion sugerido. |
| style_notes | text nullable | Notas de estilo del perfil. |
| status | string | `generated`, `edited`, `approved`, `rejected`, `regenerated` o `archived`. |
| generation_mode | string | `local_template` en Fase 13. |
| prompt_context | text nullable | Contexto local usado para la plantilla. |
| user_feedback | string nullable | Feedback rapido aplicado. |
| output_path | string nullable | Ruta relativa del `.md` en `08_Copies`. |

Las columnas nuevas de `editorial_profile` y `generated_copy` se agregan de forma incremental en bases SQLite existentes hasta introducir migraciones Alembic.

## Campos usados en Fase 14

`export_package` registra cada paquete final:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| event_id | integer | Evento exportado. |
| name | string | Nombre de la carpeta del paquete. |
| export_type | string | `ready_to_publish`, `full_event_package`, `reels_only`, `carousel_only`, `stories_only` o `google_photos_upload_package`. |
| output_path | string | Ruta relativa a la carpeta del evento, dentro de `09_Listo_Para_Publicar`. |
| status | string | `pending`, `generated` o `failed` en la implementacion actual. |
| finished_at | datetime nullable | Fecha de finalizacion del paquete. |

`export_package_item` registra cada archivo incluido o fallido:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| package_id | integer | Paquete al que pertenece. |
| content_piece_id | integer nullable | Pieza asociada cuando aplica. |
| generated_copy_id | integer nullable | Copy exportado cuando aplica. |
| enhanced_media_id | integer nullable | Medio exportado cuando aplica. |
| item_type | string | `media`, `standalone_media`, `copy` o `summary`. |
| output_path | string | Ruta relativa final del archivo o ruta intentada si fallo. |
| item_order | integer nullable | Orden dentro del paquete. |
| metadata_written | boolean | Indica si se escribio fecha de archivo/metadata en medio exportado. |
| metadata_status | string nullable | Resultado de metadata, por ejemplo `file_mtime_written_exiftool_unavailable`. |
| error_message | text nullable | Error por item sin detener el paquete completo. |

Las columnas `export_package.export_type` y `export_package_item.item_order` se agregan de forma incremental en bases SQLite existentes hasta introducir migraciones Alembic.

## Campos usados en Fase 15

La biblioteca no agrega tablas nuevas. Consulta registros existentes de:

- `original_media`
- `curated_media`
- `enhanced_media`
- `content_piece`
- `generated_copy`

Endpoints de biblioteca:

| Endpoint | Descripcion |
| --- | --- |
| `GET /api/library/media` | Lista medios originales, curados y mejorados con filtros y rutas locales. |
| `GET /api/library/pieces` | Lista piezas de contenido con conteos de medios/copies y miniatura de referencia. |
| `GET /api/library/copies` | Lista copies generados con vista previa y ruta `.md` cuando existe. |
| `GET /api/library/search` | Busqueda unificada sobre medios, piezas y copies. |

`publishing_calendar_item` se usa para calendario manual:

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| event_id | integer nullable | Evento asociado. En la implementacion actual se deriva de la pieza. |
| piece_id | integer nullable | Pieza aprobada asociada al item. |
| title | string | Titulo visible del item de calendario. |
| platform | string nullable | Plataforma manual: `instagram`, `facebook`, `tiktok`, `whatsapp_business`, `google_photos`, `multiple` u `other`. |
| scheduled_for | datetime nullable | Fecha y hora planificada combinadas. |
| status | string | Estado de publicacion: `not_scheduled`, `scheduled`, `ready_to_publish`, `published` o `cancelled`. |
| published_at | datetime nullable | Fecha en que el usuario marco la publicacion como realizada. |
| published_url | string nullable | URL publicada opcional registrada manualmente. |
| notes | text nullable | Notas del usuario. |

La columna `publishing_calendar_item.published_url` se agrega de forma incremental en bases SQLite existentes.

Endpoints de calendario:

| Endpoint | Descripcion |
| --- | --- |
| `GET /api/calendar` | Lista publicaciones planificadas con filtros. |
| `POST /api/calendar/items` | Crea item asociado a una pieza aprobada. |
| `PUT /api/calendar/items/{id}` | Actualiza programacion, estado, plataforma, URL y notas. |
| `POST /api/calendar/items/{id}/mark-published` | Marca publicacion manualmente como publicada. |
| `DELETE /api/calendar/items/{id}` | Cancela logicamente la programacion. |

## Convenciones futuras

- Usar claves foraneas explicitas.
- Registrar timestamps relevantes.
- Evitar estados inventados en frontend.
- Guardar razones explicables para decisiones automatizadas.
