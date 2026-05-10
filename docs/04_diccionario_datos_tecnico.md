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

## Seeds objetivo

Para Fase 1 ampliada se deben crear datos iniciales:

- Usuario admin: Roberto Zamora.
- Marca: Rancho Flor Maria.
- Perfil editorial base: calido, natural, cercano, profesional, emojis sutiles.
- Presets visuales: `natural_premium`, `calido_elegante`, `color_vivo_fiesta`, `suave_bodas`, `brillante_xv`, `sobrio_corporativo`.

## Convenciones futuras

- Usar claves foraneas explicitas.
- Registrar timestamps relevantes.
- Evitar estados inventados en frontend.
- Guardar razones explicables para decisiones automatizadas.
