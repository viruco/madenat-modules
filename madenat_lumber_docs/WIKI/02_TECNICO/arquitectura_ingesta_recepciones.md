# Arquitectura de Ingesta de Recepciones

## TD-004 — Centralización de Constantes Físicas Universales

**Fecha:** 2026-06-03
**Estado:** ✅ Completado
**Tag:** v1.2-TD004

### Decisión Arquitectónica
- `25.4` (mm/pulgada) es **constante física universal**, no regla de negocio MADENAT
- Centralizada en `utils_uom.MM_PER_INCH` como fuente única de verdad
- `0.125` (+1/8"), `1550`, `5085.312` son **reglas de negocio** — se centralizarán en TD-005 con parametrización

### Archivos modificados
- `madenat_lumber_logistics/models/lumber_shipment_line.py` (líneas 78, 123): reemplazar `25.4` → `MM_PER_INCH`
- `madenat_lumber_core/wizard/lumber_reception_mass_update.py` (línea 114): reemplazar `25.4` → `MM_PER_INCH`

### Validación
- Volúmenes A1M2605458 y A1M2602536 idénticos vs Excel ✅
- Carga de módulo exitosa sin errores de import ✅
- Cero errores de sintaxis ✅

### Próximos pasos
- TD-005: Parametrización de reglas de negocio (`0.125`, `1550`, `5085.312`)