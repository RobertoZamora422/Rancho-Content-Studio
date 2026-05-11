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

La UI inicial incluye layout de escritorio, menu lateral y pantalla Inicio con estado del backend.

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
- marca videos como `No aplica en Fase 7`;
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
