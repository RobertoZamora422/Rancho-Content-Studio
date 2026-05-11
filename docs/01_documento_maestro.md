# 01 Documento Maestro

## Vision

Rancho Content Studio transforma carpetas locales con fotos y videos de eventos en material organizado para redes sociales. El sistema debe reducir el tiempo de seleccion, mejora, redaccion y exportacion sin quitar control al usuario.

## Usuario principal

Administrador o editor de contenido de Rancho Flor Maria, responsable de preparar publicaciones despues de cada evento.

## Flujo principal

1. Crear evento.
2. Seleccionar carpeta local.
3. Procesar material.
4. Revisar seleccion.
5. Aprobar piezas y copy.
6. Exportar carpeta final.

## Reglas del producto

- La aplicacion es local-first.
- No modifica archivos originales.
- No borra archivos automaticamente.
- Todo descarte es logico y reversible.
- Las mejoras generan nuevas versiones.
- La conversion de formato es opcional.
- La IA externa es opcional.
- El sistema debe funcionar sin internet para el flujo local.

## Alcance implementado hasta Fase 14

La base actual ya cubre estructura tecnica, healthcheck, SQLite inicial, layout desktop, configuracion local, eventos, importacion, metadatos/miniaturas, analisis visual de fotos, duplicados/similitud, curacion revisable, versiones mejoradas de fotos seleccionadas, mejora basica de videos seleccionados con FFmpeg opcional, generacion de piezas sugeridas desde medios mejorados, copywriting local basado en perfil editorial y exportacion final local.

Las piezas se guardan en SQLite, conservan su orden de medios, pueden revisarse manualmente desde la UI y pueden aprobarse o rechazarse antes de copywriting/exportacion. Los copies se guardan en SQLite, se escriben como `.md` en `08_Copies` y pueden editarse/aprobarse/rechazarse. La exportacion crea paquetes versionados en `09_Listo_Para_Publicar`, copia medios finales, escribe copies `.txt`, intenta conservar/escribir fecha del evento y registra `export_package`. Los modulos de calendario editorial y biblioteca quedan para fases posteriores.
