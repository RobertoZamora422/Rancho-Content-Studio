# AGENTS.md

## Proposito del proyecto

Rancho Content Studio es una aplicacion de escritorio local-first para automatizar la preparacion de contenido para redes sociales a partir de fotos y videos de eventos sociales. El usuario principal trabaja con eventos de Rancho Flor Maria y necesita importar material local, analizarlo, revisarlo, mejorarlo, generar piezas y exportar carpetas listas para publicar.

## Stack tecnico

- Desktop: Tauri.
- Frontend: React + Vite + TypeScript.
- Backend local: Python + FastAPI.
- Base de datos: SQLite.
- ORM: SQLAlchemy.
- Procesamiento futuro de imagen: OpenCV, Pillow, ImageHash, scikit-image.
- Procesamiento futuro de video: FFmpeg, OpenCV, PySceneDetect opcional.
- Metadatos: ExifTool cuando este disponible.
- IA externa: opcional y bajo demanda solo para copywriting o analisis puntual.

## Estructura del repositorio

```text
README.md
AGENTS.md
docs/
backend/
  app/
    api/
    core/
    models/
    repositories/
    schemas/
    services/
    workers/
    utils/
  tests/
desktop/
  src-tauri/
  src/
samples/
```

## Comandos de instalacion y ejecucion

Backend:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run_backend.py
```

Frontend:

```powershell
cd desktop
npm install
npm run dev
```

Desktop Tauri:

```powershell
cd desktop
npm run tauri dev
```

## Comandos de pruebas

Backend:

```powershell
cd backend
pytest
```

Frontend:

```powershell
cd desktop
npm run build
```

## Convenciones de codigo

- Mantener la logica de negocio en servicios del backend.
- Mantener React como capa de presentacion y control de flujo de UI.
- Usar TypeScript estricto en frontend.
- Usar esquemas Pydantic para contratos de API.
- Usar SQLAlchemy para acceso a SQLite.
- Mantener funciones pequenas y nombres explicitos.
- No introducir dependencias cloud para resolver funciones locales.
- Registrar errores por archivo en jobs, no ocultarlos.

## Reglas obligatorias del sistema

- No convertir el sistema en una app cloud.
- No introducir Google Drive como dependencia.
- No modificar originales.
- No borrar archivos automaticamente.
- No forzar videos a 9:16.
- Mantener SQLite como base local.
- Mantener FastAPI como backend local.
- Mantener Tauri + React + TypeScript para escritorio.
- Los trabajos largos deben reportar progreso.
- Los errores por archivo deben registrarse y no detener todo el proceso.
- Antes de implementar cambios grandes, crear plan breve.
- Despues de implementar, indicar como probar.

## Restricciones importantes

- Google Photos no tiene integracion directa en esta etapa.
- Google Drive solo puede mencionarse como respaldo manual opcional.
- La app debe funcionar sin internet para importacion, analisis local, curacion, mejora basica y exportacion.
- Toda mejora debe generar una nueva version.
- Todo descarte debe ser logico y reversible.
- Todo copy aprobado debe guardarse en SQLite y exportarse como `.txt` o `.md`.
- La UI debe mantener control humano visible.

## Que significa terminado

Un bloque se considera terminado cuando:

1. El codigo compila o ejecuta sin errores criticos.
2. Hay instrucciones para probar.
3. Se respetan reglas obligatorias.
4. No se introducen dependencias cloud innecesarias.
5. No se rompen fases anteriores.
6. README, AGENTS o docs se actualizan si corresponde.
7. Se indican archivos modificados.
8. Se mencionan limitaciones pendientes.

## Como validar cada cambio

- Backend: ejecutar `pytest` y, cuando aplique, probar el endpoint local.
- Frontend: ejecutar `npm run build` y revisar la pantalla afectada.
- SQLite: validar PRAGMAs `journal_mode=WAL`, `foreign_keys=ON`, `synchronous=NORMAL`.
- Jobs futuros: comprobar progreso, conteo de items, errores por archivo y reintento.
- Archivos locales: confirmar que originales no se modifican ni se eliminan.
