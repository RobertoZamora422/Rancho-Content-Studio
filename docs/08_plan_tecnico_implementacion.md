# 08 Plan Tecnico de Implementacion

## Fases

0. Repositorio, README, AGENTS y docs base.
1. Backend FastAPI + SQLite + modelos base + seed.
2. Tauri + React base + navegacion + healthcheck.
3. Configuracion local: carpeta raiz, FFmpeg, ExifTool.
4. Eventos: crear, listar, abrir, carpetas locales.
5. Importacion desde carpeta local.
6. Metadatos y miniaturas.
7. Analisis visual de fotos.
8. Duplicados y similares.
9. Curacion inteligente y revision manual.
10. Mejora de fotos.
11. Video basico.
12. Piezas de contenido.
13. Perfil editorial y copywriting.
14. Exportacion final.
15. Biblioteca y calendario.
16. Pulido, pruebas y empaquetado.

## Estado de esta implementacion

La base actual cubre Fase 0, Fase 1, Fase 2, Fase 3 y Fase 4. El backend local ya tiene modelos base, seed inicial, endpoints de configuracion y endpoints de eventos. El frontend desktop ya tiene shell, rutas de navegacion, healthcheck visible, pantalla de configuracion local y gestion inicial de eventos.

## Criterios por bloque

- Ejecuta sin errores criticos.
- Tiene instrucciones de prueba.
- Respeta reglas obligatorias.
- No introduce dependencias cloud.
- No rompe fases previas.
- Actualiza documentacion si corresponde.
