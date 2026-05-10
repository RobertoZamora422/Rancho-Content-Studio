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

## Flujo de procesamiento futuro

1. Generar miniaturas.
2. Leer metadatos.
3. Analizar calidad visual.
4. Detectar duplicados y similares.
5. Crear curacion sugerida.
6. Permitir revision manual.
7. Crear versiones mejoradas.
8. Sugerir piezas.
9. Generar o editar copy.
10. Exportar.

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
