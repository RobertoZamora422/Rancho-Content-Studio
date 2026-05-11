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

## Alcance implementado hasta Fase 10

La base actual ya cubre estructura tecnica, healthcheck, SQLite inicial, layout desktop, configuracion local, eventos, importacion, metadatos/miniaturas, analisis visual de fotos, duplicados/similitud, curacion revisable, versiones mejoradas de fotos seleccionadas y mejora basica de videos seleccionados con FFmpeg opcional. Los modulos de piezas, copy, calendario y exportacion final quedan para fases posteriores.
