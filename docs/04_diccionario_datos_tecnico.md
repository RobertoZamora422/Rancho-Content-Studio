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

## Convenciones futuras

- Usar claves foraneas explicitas.
- Registrar timestamps relevantes.
- Evitar estados inventados en frontend.
- Guardar razones explicables para decisiones automatizadas.
