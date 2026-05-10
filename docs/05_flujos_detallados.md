# 05 Flujos Detallados

## Flujo operativo principal

```text
Crear evento -> Seleccionar carpeta -> Procesar -> Revisar -> Aprobar -> Exportar
```

## Flujo de evento

1. El usuario crea un evento con fecha, nombre y tipo.
2. El sistema genera una carpeta local segura para Windows.
3. El usuario agrega una fuente local.
4. La app escanea, importa y registra archivos sin modificar originales.

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
