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

## Convenciones futuras

- Usar claves foraneas explicitas.
- Registrar timestamps relevantes.
- Evitar estados inventados en frontend.
- Guardar razones explicables para decisiones automatizadas.
