# 06 Diseno UI UX

## Principio de UX

La interfaz debe hacer visible el control humano: el sistema sugiere, el usuario revisa y aprueba.

## Navegacion principal

```text
Inicio
Eventos
Biblioteca
Piezas de contenido
Calendario
Perfil editorial
Estilos visuales
Configuracion
```

## Pantallas objetivo

1. Configuracion inicial.
2. Inicio / Dashboard.
3. Lista de eventos.
4. Nuevo evento.
5. Detalle de evento.
6. Resumen del evento.
7. Seleccionar carpeta local.
8. Progreso de procesamiento.
9. Material original.
10. Analisis visual.
11. Curacion inteligente.
12. Mejoras visuales.
13. Comparador original vs mejorado.
14. Piezas sugeridas.
15. Editor de pieza.
16. Editor de copy.
17. Exportacion / Listo para publicar.
18. Biblioteca.
19. Calendario.
20. Perfil editorial.
21. Estilos visuales.
22. Configuracion.

## Base implementada

La UI incluye layout de escritorio, menu lateral, rutas hash, pantalla Inicio operativa y estado del backend.

## Fase 6 implementada en UI

La pantalla de detalle de evento incluye una seccion `Material original` que:

- ejecuta `Procesar metadatos y miniaturas`;
- muestra miniatura por archivo usando el endpoint local de backend;
- muestra fecha de captura, fuente de fecha, tamano, resolucion y duracion cuando existe;
- mantiene estado vacio cuando no hay material importado;
- conserva control humano visible sin modificar originales.

## Fase 7 implementada en UI

La seccion `Material original` tambien:

- ejecuta `Analizar fotos`;
- muestra calidad global por foto;
- muestra nitidez, brillo, contraste y exposicion;
- marca videos como fuera del analisis de fotos;
- mantiene el analisis como soporte tecnico para revision humana, no como decision automatica final.

## Fase 8 implementada en UI

El detalle de evento incluye una seccion `Duplicados y similares` que:

- ejecuta `Detectar duplicados y similares`;
- muestra cantidad de grupos detectados;
- separa duplicados exactos y similares visuales;
- muestra representante sugerido, alternativas, calidad, distancia y confianza;
- permite revisar alternativas sin borrar ni descartar automaticamente.

## Fase 9 implementada en UI

El detalle de evento incluye una seccion `Curacion inteligente` que:

- ejecuta `Ejecutar curacion inteligente`;
- muestra columnas de seleccionados, alternativos, descartes logicos y revision manual;
- muestra miniatura, calidad y motivo de cada decision;
- permite cambiar manualmente a seleccionar, revisar o rechazar;
- conserva decisiones manuales para la siguiente ejecucion.

## Fase 10 implementada en UI

El detalle de evento incluye una seccion `Mejoras visuales` que:

- muestra cuantas versiones mejoradas existen;
- permite elegir un preset visual local para fotos;
- ejecuta procesamiento o reprocesamiento de fotos seleccionadas;
- compara miniatura original contra JPEG mejorado servido por backend local;
- muestra preset, estado, dimensiones, ruta relativa y estado de metadatos;
- permite aprobar o rechazar cada version sin borrar archivos;
- mantiene estados vacios cuando no hay fotos seleccionadas o versiones generadas.

## Fase 11 implementada en UI

La seccion `Mejoras visuales` tambien:

- permite elegir preset visual para videos;
- permite elegir modo `Automatico`, `Video completo` o `Segmento simple`;
- ejecuta mejora de videos seleccionados;
- muestra aviso cuando FFmpeg no esta disponible;
- reproduce versiones de video generadas con controles nativos;
- muestra duracion, formato/plan en notas, ruta relativa y estado;
- reutiliza aprobar/rechazar sin borrar archivos.

## Fase 12 implementada en UI

La pantalla `Piezas de contenido` deja de ser placeholder e incluye:

- selector de evento activo;
- accion `Generar piezas sugeridas`;
- cards de piezas con tipo, titulo, cantidad de medios y estado;
- editor basico de titulo, proposito, plataforma y formato recomendado;
- lista ordenada de medios con portada sugerida;
- acciones `Subir` y `Bajar` para reordenar medios;
- acciones para guardar revision, aprobar o rechazar pieza.

## Fase 13 implementada en UI

La pantalla `Perfil editorial` deja de ser placeholder e incluye:

- edicion de nombre, tono, nivel emocional, formalidad y estilo de emojis;
- campos para descripcion, hashtags base, frases preferidas y palabras a evitar;
- campos para ejemplos aprobados, ejemplos rechazados y reglas adicionales;
- guardado en SQLite mediante backend local.

La pantalla `Piezas de contenido` agrega un editor de copy:

- generacion de copy solo para piezas aprobadas;
- feedback rapido para regenerar variantes;
- lista de variantes por tipo de copy;
- textarea para editar manualmente;
- advertencias visuales;
- acciones para guardar edicion, aprobar o rechazar copy;
- muestra la ruta `.md` generada en `08_Copies`.

## Fase 14 implementada en UI

La pantalla `Piezas de contenido` agrega una seccion `Exportacion final`:

- resumen de piezas aprobadas, medios incluidos y paquetes anteriores;
- selector de tipo de exportacion;
- opciones para incluir copies `.txt`, escribir fecha del evento, agrupar por tipo y crear resumen;
- accion `Exportar listo para publicar`;
- resultado con ruta local del paquete en `09_Listo_Para_Publicar`;
- accion `Abrir carpeta final` cuando el backend local puede solicitarlo al sistema operativo;
- manejo visible de errores sin ocultar fallas por archivo.

## Fase 15 implementada en UI

La pantalla `Biblioteca` deja de ser placeholder e incluye:

- filtros por evento, tipo de evento, fecha desde/hasta, tipo, estado, origen y busqueda textual;
- vistas para medios, piezas, copies y busqueda global;
- cards con miniatura cuando existe, nombre, evento, estado y ruta local;
- panel de detalle con relacion al evento, ruta local, estado y existencia de archivo;
- enlace al evento de origen;
- estados de carga, error y sin resultados.

La pantalla `Calendario` deja de ser placeholder e incluye:

- filtros por busqueda, evento, estado, plataforma y rango de fechas;
- agenda agrupada por fecha con piezas planificadas;
- formulario para elegir pieza aprobada, fecha, hora, plataforma y estado;
- campos para URL publicada opcional y notas;
- acciones para guardar, marcar como publicado y cancelar programacion;
- enlace al evento de origen;
- estados vacios y errores visibles.

La UI mantiene planificacion manual: no publica automaticamente en redes sociales ni en Google Photos.

## Fase 16 implementada en UI

La pantalla `Inicio` se ajusta como centro operativo del flujo completo:

- muestra estado del backend local;
- muestra pasos principales del flujo de evento;
- ofrece accesos directos a eventos, biblioteca, piezas y calendario.

La pantalla `Estilos visuales` deja de ser placeholder:

- carga presets activos desde backend;
- muestra cards con nombre, descripcion y slug;
- incluye estados de carga, error y vacio;
- enlaza hacia eventos para aplicar presets desde el detalle.
