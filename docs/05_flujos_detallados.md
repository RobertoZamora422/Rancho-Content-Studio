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

## Flujo de procesamiento futuro

1. Analizar calidad visual.
2. Detectar duplicados y similares.
3. Crear curacion sugerida.
4. Permitir revision manual.
5. Crear versiones mejoradas.
6. Sugerir piezas.
7. Generar o editar copy.
8. Exportar.

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
