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

---

## TD-005 — Clasificación y Parametrización de Reglas de Negocio Comercial

**Fecha:** 2026-06-03
**Estado:** ✅ Completado
**Tag:** v1.3-TD005

### Decisión Arquitectónica

Todas las reglas de negocio comercial YA estaban centralizadas en `utils_uom.py` desde TD-003.2 (2026-05-31). El inventario completo confirmó que no hay fugas significativas.

| Valor | Nombre en `utils_uom` | Tipo | Significado |
|---|---|---|---|
| `1000000` | `M3_DIVISOR` | Constante dimensional | mm²·m → m³ |
| `1550.003096` | `INCH_SQ_METERS_TO_M3` | Regla comercial fija | Factor embarque S2S (in²·m → m³) |
| `5085.312` | `BLANK_CLEAR_FACTOR` | Regla comercial fija | Factor blank clear (in²·ft → m³) |
| `12000` | `MBF_DIVISOR` | Regla comercial fija | Divisor MBF estándar |
| `0.125` | `S2S_WIDTH_ADJUSTMENT_INCH` | Regla comercial fija | +1/8" ajuste rough → S2S |

### Fugas encontradas y corregidas
- `lumber_shipment_line.py:131`: `1_000_000.0` literal → `float(M3_DIVISOR)` + import

### Fugas aceptadas (field defaults de Odoo — no son fórmulas de cálculo)
- `lumber_export_formula.py:94`: `default=5085.312` (valor almacenable en BD)
- `lumber_export_formula.py:117`: `default=12000.0` (valor almacenable en BD)
- `lumber_shipping_rule.py:24`: `default=0.125` (valor almacenable en BD)

Estos field defaults son configurables por el usuario desde la UI de Odoo. No requieren centralización porque son datos, no código de fórmula.

### Validación
- Volúmenes A1M2605458 y A1M2602536 idénticos vs Excel ✅
- Sintaxis compilada OK ✅
- Módulo carga sin errores de import ✅

### Próximos pasos
- TD-006: Evaluar si `S2S_WIDTH_ADJUSTMENT_INCH` debe ser configurable por cliente/perfil/subproducto (hoy es regla fija)
