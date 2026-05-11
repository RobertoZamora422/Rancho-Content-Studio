# 05 Flujos Detallados

## Flujo operativo principal

```text
Crear evento -> Seleccionar carpeta -> Procesar -> Revisar -> Aprobar -> Exportar
```

## Flujo de configuracion local

1. El usuario abre Configuracion.
2. Define una carpeta raiz local existente.
3. Opcionalmente define rutas a FFmpeg y ExifTool.
4. La app guarda la configuracion en SQLite.
5. El backend valida si la carpeta existe y si las herramientas estan disponibles.
6. La ausencia de herramientas externas queda registrada como estado de configuracion, sin bloquear el resto de la app.

## Flujo de evento

1. El usuario crea un evento con fecha, nombre y tipo.
2. El sistema genera una carpeta local segura para Windows.
3. El usuario agrega una fuente local.
4. La app escanea, importa y registra archivos sin modificar originales.

## Flujo de eventos implementado en Fase 4

1. El usuario configura una carpeta raiz local.
2. El usuario crea un evento desde la pantalla Eventos.
3. El backend genera un nombre seguro para Windows con fecha y nombre del evento.
4. El backend crea la carpeta del evento y subcarpetas operativas.
5. El evento queda registrado en SQLite con estado `active`.
6. El usuario puede abrir el detalle, ver la ruta local, archivar o dar de baja logicamente.
7. Archivar o dar de baja no borra carpetas ni archivos.

## Flujo de importacion implementado en Fase 5

1. El usuario abre el detalle de un evento.
2. Registra una carpeta fuente local externa a la carpeta del evento.
3. El backend escanea la fuente y cuenta archivos compatibles/no compatibles.
4. El backend registra un job `scan_folder`.
5. El usuario ejecuta importacion.
6. El backend copia archivos compatibles a `01_Originales` sin modificar la fuente.
7. El backend registra `original_media`, checksum, tamano, tipo y fecha base por fecha de archivo.
8. El backend registra un job `import_media` y logs por archivo.
9. Repetir la importacion omite archivos ya importados por checksum.

## Flujo de metadatos y miniaturas implementado en Fase 6

1. El usuario importa material en un evento.
2. Desde el detalle del evento ejecuta `Procesar metadatos y miniaturas`.
3. El backend crea un job `write_metadata`.
4. Para cada archivo importado:
   - intenta leer metadatos con ExifTool si esta disponible,
   - usa fecha de archivo como fallback local,
   - usa fecha del evento si no puede obtener una fecha de archivo,
   - guarda `capture_datetime`, `date_source`, dimensiones, duracion cuando exista y `metadata_json`.
5. El backend crea un job `generate_thumbnails`.
6. Para fotos, genera una miniatura JPEG local con Pillow.
7. Para videos, intenta extraer un frame con FFmpeg; si no puede, genera una miniatura local de respaldo.
8. Guarda `thumbnail_path` relativo a la carpeta del evento.
9. Los errores por archivo se registran en `processing_job_log` y no detienen el procesamiento completo.
10. La UI muestra miniaturas, fecha de captura, fuente y datos tecnicos basicos.

## Flujo de analisis visual de fotos implementado en Fase 7

1. El usuario importa fotos en un evento.
2. Desde el detalle del evento ejecuta `Analizar fotos`.
3. El backend crea un job `analyze_media`.
4. El backend filtra `original_media.media_type = image` y omite videos.
5. Para cada foto:
   - abre la imagen con Pillow,
   - corrige orientacion EXIF si aplica,
   - calcula nitidez, brillo, contraste, ruido estimado y exposicion,
   - genera `perceptual_hash`,
   - calcula `overall_quality_score`,
   - guarda o actualiza `media_analysis`.
6. Los errores por archivo se registran en `processing_job_log`.
7. La UI muestra calidad global y metricas basicas.

## Flujo de duplicados y similares implementado en Fase 8

1. El usuario importa medios y ejecuta analisis visual de fotos.
2. Desde el detalle del evento ejecuta `Detectar duplicados y similares`.
3. El backend crea un job `detect_similarity`.
4. El backend elimina grupos generados previos de tipo `checksum_duplicate` y `perceptual_hash` para recalcular sin duplicarlos.
5. Agrupa duplicados exactos por `checksum_sha256`.
6. Agrupa fotos similares comparando `perceptual_hash` con distancia Hamming.
7. Define representante sugerido por mayor `overall_quality_score`.
8. Crea `similarity_group` y `similarity_group_item`.
9. Registra advertencias si hay fotos sin hash perceptual.
10. La UI muestra representante sugerido, alternativas, distancia y confianza.

## Flujo de curacion inteligente implementado en Fase 9

1. El usuario ejecuta analisis visual y deteccion de similitud.
2. Desde el detalle del evento ejecuta `Ejecutar curacion inteligente`.
3. El backend crea un job `curate_media`.
4. Para cada medio:
   - conserva decisiones manuales previas,
   - evalua calidad global, nitidez, brillo y exposicion,
   - usa grupos similares para seleccionar representante y marcar alternativas,
   - marca descartes logicos por duplicado, baja calidad, borroso u oscuro,
   - envia videos y casos sin analisis a `manual_review`.
5. Guarda o actualiza `curated_media`.
6. Registra motivos en `curated_media.reason`.
7. Registra decisiones automaticas y manuales en `decision_log`.
8. La UI permite seleccionar, enviar a revision o rechazar manualmente.

## Flujo de mejora de fotos implementado en Fase 10

1. El usuario ejecuta curacion y deja fotos en `selected` o `user_selected`.
2. Desde el detalle del evento elige un preset visual y ejecuta `Procesar / reprocesar seleccionados`.
3. El backend crea un job `enhance_photos`.
4. Para cada foto seleccionada:
   - valida que el original importado exista,
   - omite videos y otros medios no fotograficos,
   - abre la imagen con Pillow y corrige orientacion EXIF si aplica,
   - aplica ajustes basicos de brillo, contraste, color y nitidez,
   - guarda un JPEG versionado en `04_Mejorados`,
   - registra `enhanced_media` con ruta relativa, preset, dimensiones, estado y notas,
   - ajusta la fecha de archivo de la version generada,
   - intenta escribir fechas EXIF si ExifTool esta disponible.
5. Los errores por archivo se registran en `processing_job_log` y el job continua.
6. La UI muestra comparador original vs mejorado.
7. El usuario aprueba o rechaza cada version; la decision se guarda en `decision_log`.
8. Reprocesar genera una nueva version y no sobrescribe versiones anteriores.

## Flujo de video basico implementado en Fase 11

1. El usuario deja videos en `selected` o `user_selected` desde la curacion manual.
2. Desde `Mejoras visuales` elige preset y modo de video: `auto`, `full` o `segment`.
3. El backend crea un job `enhance_videos`.
4. El backend valida FFmpeg desde configuracion local o `PATH`.
5. Si FFmpeg no esta disponible:
   - registra error en el job,
   - marca los videos como fallidos del job,
   - no modifica originales ni crea versiones falsas.
6. Si FFmpeg esta disponible, para cada video seleccionado:
   - valida que el archivo original exista,
   - lee metadata basica con FFmpeg,
   - decide video completo o segmento simple segun modo/duracion,
   - aplica ajuste basico de luz, contraste, saturacion y nitidez,
   - conserva contenedor original para `.mp4`, `.mov` y `.m4v`,
   - guarda video completo en `04_Mejorados` o segmento en `05_Reels`,
   - genera una miniatura de respaldo del video mejorado,
   - ajusta fecha de archivo y usa ExifTool si esta disponible,
   - registra `enhanced_media`.
7. Los errores por archivo se registran en `processing_job_log` y el job continua.
8. La UI permite reproducir el resultado, aprobarlo o rechazarlo.

## Flujo de generacion de piezas implementado en Fase 12

1. El usuario genera o aprueba medios mejorados en un evento.
2. Desde `Piezas de contenido`, elige el evento y ejecuta `Generar piezas sugeridas`.
3. El backend crea un job `generate_pieces`.
4. Filtra `enhanced_media` con estado `completed` o `approved` y archivo existente.
5. Separa fotos y videos.
6. Genera propuestas segun disponibilidad:
   - reel con videos mejorados,
   - carrusel principal con fotos suficientes,
   - historias destacadas con seleccion corta,
   - publicacion individual destacada,
   - pieza promocional si hay fotos y video.
7. Para cada propuesta:
   - define tipo, titulo, proposito, plataforma y formato recomendado,
   - asocia medios en `content_piece_media`,
   - marca el primer medio como portada sugerida,
   - guarda razon en `metadata_json` y `decision_log`.
8. Evita duplicar piezas si ya existe una pieza del mismo tipo con los mismos medios.
9. La UI permite cambiar titulo, proposito, plataforma, formato y orden.
10. El usuario puede aprobar o rechazar la pieza.

## Flujo de copywriting implementado en Fase 13

1. El usuario edita o confirma el perfil editorial en `Perfil editorial`.
2. El usuario aprueba una pieza de contenido.
3. Desde `Piezas de contenido`, ejecuta `Generar copy` o un feedback rapido.
4. El backend crea un job `generate_copy`.
5. Obtiene evento, pieza, medios asociados y perfil editorial.
6. Construye contexto local con tipo de evento, proposito, plataforma, tono, hashtags, palabras a evitar y reglas.
7. Genera variantes locales:
   - caption principal,
   - copy breve,
   - texto de portada,
   - texto para historia,
   - hashtags.
8. Guarda cada variante en `generated_copy`.
9. Escribe cada variante como `.md` en `08_Copies`.
10. El usuario puede editar, aprobar o rechazar una variante.
11. No se permite aprobar copy vacio ni copy con palabras/frases a evitar.
12. Aprobar o rechazar copy alimenta ejemplos del perfil editorial.

## Flujo de exportacion final implementado en Fase 14

1. El usuario aprueba una pieza y, si aplica, aprueba un copy.
2. Desde `Piezas de contenido`, elige tipo de exportacion y opciones.
3. El backend crea un job `export_package`.
4. Crea registro `export_package` en estado `pending`.
5. Crea carpeta unica en `09_Listo_Para_Publicar`.
6. Para cada pieza aprobada incluida:
   - copia medios finales desde `enhanced_media`,
   - ordena nombres por pieza y posicion,
   - exporta copies aprobados como `.txt`,
   - ajusta fecha de archivo a la fecha del evento,
   - intenta escribir metadata con ExifTool si esta disponible,
   - registra cada salida en `export_package_item`.
7. Si hay medios mejorados aprobados sin pieza y el tipo de paquete lo permite, los exporta en `Medios_Aprobados`.
8. Si un archivo falla, registra `processing_job_log` y `export_package_item.error_message`; el resto continua.
9. Escribe `resumen_exportacion.txt` cuando la opcion esta activa.
10. Marca el paquete como `generated` o `failed` y registra `decision_log`.
11. La UI muestra ruta local, conteos y accion para abrir carpeta final.

## Flujo de procesamiento futuro

1. Planificar en calendario.
2. Consultar biblioteca historica.

## Jobs

Cada job debe registrar:

- Estado.
- Porcentaje de progreso.
- Total de items.
- Items procesados.
- Items fallidos.
- Fechas de inicio y fin.
- Mensaje de error general.
- Logs por archivo.

Los errores por archivo no deben detener todo el evento.
