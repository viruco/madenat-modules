# Configuración de Ingesta — Arquitectura Fase 1 + Fase 2 + Fase 3

**Módulo:** MADENAT Lumber Core
**Versión documental:** 2.0.0
**Fecha:** 2026-06-02
**Estado:** CANONICAL — Cierre Fase 3

---

## Propósito

Documentar la arquitectura completa del sistema de configuración de reglas de negocio para la ingesta de recepciones de madera, cubriendo ambas fases de desacoplamiento de hardcodes.

---

## 1. Visión General

El sistema de ingesta de MADENAT requiere reglas de negocio parametrizables (mapeos de dimensiones, filtros de subproductos, rangos visuales) que originalmente estaban hardcodeadas en 14 puntos del código (H1–H14).

La solución se implementó en dos fases:

| Fase | Mecanismo | Estado |
|------|-----------|--------|
| **Fase 1** | `ir.config_parameter` (JSON) | COMPLETADA (AD-28) |
| **Fase 2** | Modelos persistentes Odoo con UI de mantenimiento | COMPLETADA (AD-29) |
| **Fase 3** | Parametrización H8, H9 + cierre brecha s2s_exclusion_widths | COMPLETADA (AD-30) |

---

## 2. Arquitectura de Lectura (Runtime)

El helper centralizado `madenat.ingestion.config` (AbstractModel) implementa una cadena de prioridad de 3 niveles para cada regla de negocio:

```
┌──────────────────────────────────────────┐
│  1. Modelo Persistente Fase 2            │  ← Mayor prioridad
│     (registros active=True en BD)        │
├──────────────────────────────────────────┤
│  2. ir.config_parameter Fase 1           │  ← Fallback de transición
│     (JSON en system parameters)          │
├──────────────────────────────────────────┤
│  3. Hardcode Legacy                      │  ← Último recurso
│     (valores originales en código)       │
└──────────────────────────────────────────┘
```

**Regla:** Ningún consumidor (parser, wizard, modelo) debe leer directamente los modelos Fase 2 ni `ir.config_parameter`. Todo debe pasar por `madenat.ingestion.config`.

---

## 3. Modelos Persistentes (Fase 2)

### 3.1 `lumber.blank.nominal.map` — Mapa Físico→Nominal Blanks

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `profile` | Selection | Perfil: f5085, f1550, metric |
| `physical_min` | Float | Mínimo físico (pulgadas) |
| `physical_max` | Float | Máximo físico (pulgadas) |
| `nominal` | Float | Valor nominal resultante (pulgadas) |
| `sequence` | Integer | Orden de evaluación |
| `active` | Boolean | Soft-delete |

**Constraints:**
- `UNIQUE(profile, physical_min)`
- `CHECK(physical_min > 0)`
- `CHECK(physical_max > physical_min)`
- `CHECK(nominal > 0)`
- Validación de no solape de rangos (`_check_no_overlap`)

**Seed Fase 2:** 8 registros para perfil `f5085` replicando exactamente el hardcode original.
**Consumidor:** `reception_parser._resolve_nominal()` vía `madenat.ingestion.config.get_blank_nominal_map()`

---

### 3.2 `lumber.width.s2s.map` — Tabla Rough→S2S

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `rough_mm` | Integer | Ancho bruto en mm |
| `s2s_decimal` | Float | Ancho S2S en pulgadas decimales |
| `s2s_label` | Char | Etiqueta fraccionaria (ej: "2 5/8") |
| `sequence` | Integer | Orden |
| `active` | Boolean | Soft-delete |

**Constraints:**
- `UNIQUE(rough_mm)`
- `CHECK(rough_mm > 0)`
- `CHECK(s2s_decimal > 0)`

**Seed Fase 2:** 15 registros replicando exactamente la tabla canónica del Excel ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx.
**Consumidores:** `width_mapping.py`, `utils_uom.py` vía `madenat.ingestion.config.get_width_s2s_map()`

---

### 3.3 `lumber.thickness.visual.rule` — Rangos Espesor→Visual

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `profile` | Selection | Perfil: f5085, f1550, metric |
| `min_thickness` | Float | Espesor mínimo (mm) |
| `max_thickness` | Float | Espesor máximo (mm) |
| `visual_value` | Float | Valor visual (pulgadas decimales) |
| `visual_label` | Char | Etiqueta (ej: "4/4", "6/4") |
| `sequence` | Integer | Orden |
| `active` | Boolean | Soft-delete |

**Constraints:**
- `UNIQUE(profile, min_thickness)`
- `CHECK(min_thickness >= 0)`
- `CHECK(max_thickness > min_thickness)`
- Validación de no solape (`_check_no_overlap`)

**Seed Fase 2:** 4 registros para perfil `f5085` (4/4, 5/4, 6/4, 8/4).
**Consumidores:** `lumber_reception._compute_visual_defaults()`, `lumber_reception._compute_reception_summary()` vía `madenat.ingestion.config.get_thickness_visual_rules()`

---

### 3.4 `lumber.profile.subproduct.rule` — Reglas Perfil↔Subproducto

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `profile` | Selection | Perfil: f5085, f1550, metric |
| `rule_type` | Selection | allowed / forbidden / forbidden_in_lock |
| `keyword` | Char | Palabra clave (ej: S2S, RIP, ROUGH) |
| `active` | Boolean | Soft-delete |

**Constraints:**
- `UNIQUE(profile, rule_type, keyword)`
- `keyword` no vacío (`_check_keyword_not_empty`)

**Seed Fase 2:** 7 registros replicando la matriz original:
- f5085 → forbidden: S2S, RIP | forbidden_in_lock: S2S, RIP
- f1550 → allowed: S2S | forbidden_in_lock: ROUGH, BLANK
- metric → sin reglas

**Consumidores:** `lumber_reception_mass_update._get_profile_subproduct_filters()`, `madenat_guia_mass_update._get_profile_subproduct_filters()` vía `madenat.ingestion.config.get_profile_subproduct_rules()`

---

## 4. Helper Centralizado: `madenat.ingestion.config`

**Archivo:** `models/madenat_ingestion_config.py`
**Tipo:** `AbstractModel` (no crea tabla, solo expone métodos)

### Métodos expuestos

| Método | Retorna | Fuentes (en orden) |
|--------|---------|-------------------|
| `get_blank_nominal_map(profile)` | `[(physical, nominal), ...]` | lumber.blank.nominal.map → ir.config_parameter → hardcode |
| `get_nominal_tolerance()` | `float` | ir.config_parameter → hardcode (0.08) |
| `get_width_s2s_map()` | `{rough_mm: (s2s_decimal, s2s_label)}` | lumber.width.s2s.map → ir.config_parameter → hardcode |
| `get_thickness_visual_rules(profile)` | `[[min, max, value, label], ...]` | lumber.thickness.visual.rule → ir.config_parameter → hardcode |
| `get_profile_subproduct_rules(profile, rule_type)` | `[keyword, ...]` | lumber.profile.subproduct.rule → ir.config_parameter → hardcode |
| `get_s2s_exclusion_widths()` (Fase 3) | `[float, ...]` | ir.config_parameter → hardcode legacy |

### Patrón de fallback

Cada método sigue el mismo patrón:
```python
# Fuente 1: Modelo Fase 2
records = self.env['modelo.fase2'].sudo().search([...])
if records:
    return procesar(records)

# Fuente 2: ir.config_parameter Fase 1
try:
    raw = param_obj.get_param('clave', '')
    if raw:
        return parsear(raw)
except Exception: pass

# Fuente 3: Hardcode legacy
return valor_hardcodeado
```

---

## 5. Seed de Datos

### 5.1 Fase 1: `data/ingestion_config.xml`

Archivo de datos Odoo estándar (`noupdate="0"`) que crea 5 `ir.config_parameter`:
- `madenat.blanks_nominal_map`
- `madenat.nominal_tolerance`
- `madenat.width_s2s_map`
- `madenat.thickness_visual_ranges`
- `madenat.profile_subproduct_filters`

### 5.2 Fase 2: `data/ingestion_seed_fase2.xml`

Archivo de datos Odoo con `noupdate="1"` y `forcecreate="False"` en cada registro:
- 8 registros `lumber.blank.nominal.map`
- 15 registros `lumber.width.s2s.map`
- 4 registros `lumber.thickness.visual.rule`
- 7 registros `lumber.profile.subproduct.rule`

**Idempotencia:** Si los registros ya existen (por XML o creación manual), no se duplican. Si no existen, se crean con los valores canónicos de Fase 1.

---

## 6. Consumidores

| Consumidor | Reglas que consume | Vía |
|------------|-------------------|-----|
| `reception_parser._resolve_nominal()` | blank_nominal_map, nominal_tolerance | `madenat.ingestion.config` |
| `width_mapping.get_value()` | width_s2s_map | `madenat.ingestion.config` |
| `lumber_reception._compute_visual_defaults()` | thickness_visual_rules | `madenat.ingestion.config` |
| `lumber_reception._compute_reception_summary()` | thickness_visual_rules | `madenat.ingestion.config` |
| `lumber_reception_mass_update._get_profile_subproduct_filters()` | profile_subproduct_rules | `madenat.ingestion.config` |
| `madenat_guia_mass_update._get_profile_subproduct_filters()` | profile_subproduct_rules | `madenat.ingestion.config` |

---

## 7. Seguridad y Permisos

Los 4 modelos Fase 2 tienen reglas de acceso en `security/ir.model.access.csv` para el grupo `madenat_lumber_core.group_madenat_user`.

El helper `madenat.ingestion.config` usa `.sudo()` en todas las lecturas para garantizar que los consumidores (que pueden ejecutarse en contextos sin usuario) siempre tengan acceso de lectura a las configuraciones.

---

## 8. Workflow de Modificación de Reglas

1. Administrador accede al menú **Configuración → Ingesta** en Odoo
2. Selecciona el modelo a modificar (Blank Nominal Map, Width S2S Map, etc.)
3. Crea/edita/desactiva registros según necesidad
4. El cambio es inmediato: la siguiente lectura desde cualquier consumidor tomará el nuevo valor
5. Si se desactivan todos los registros de un tipo, el sistema hace fallback automático a Fase 1 y luego a hardcode legacy

---

## 9. Trazabilidad

| Decisión | Descripción |
|----------|-------------|
| AD-28 | Fase 1: Desacoplamiento de hardcodes vía ir.config_parameter |
| AD-29 | Fase 2: Modelos persistentes con UI de mantenimiento + helper centralizado |

---

## 10. Fase 3 — Modelos Adicionales (AD-30)

### 10.1 `lumber.export.formula` — Fórmulas de Exportación (H8)

Parametriza el motor `_compute_export_values` en `lumber_reception.py`.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `profile` | Selection | f5085, f1550, metric |
| `active` | Boolean | Soft-delete |
| `sequence` | Integer | Orden |
| `description` | Char | Nombre legible |
| `formula_kind` | Selection | blank_clear / s2s_imperial / metric_direct |
| `unit_mode` | Selection | imperial_feet / imperial_meters / metric_mm |
| `principal_factor` | Float | Factor volumétrico (5085.312 / 1550.003 / 1000000) |
| `deduction_factor` | Float | Deducción de cara en pulgadas (ej: 0.0625 = -1/16") |
| `s2s_adjustment_mode` | Selection | none / standard / per_width |
| `mbf_divisor` | Float | Divisor MBF (estándar: 12000) |
| `threshold_note` | Char | Nota documental |
| `notes` | Text | Documentación funcional |

**Constraints:** UNIQUE(profile, active). CHECK positivos.
**Seed Fase 3:** 3 registros (f5085, f1550, metric).
**Consumidor:** `lumber_reception._compute_export_values()` vía `lumber.export.formula._resolve_for_profile()`.

### 10.2 `lumber.ingestion.format` — Formatos de Ingesta (H9)

Parametriza `_process_dataframe` en `reception_parser.py`.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `profile` | Selection | f5085, f1550, blanks, metric |
| `active` | Boolean | Soft-delete |
| `sequence` | Integer | Orden |
| `description` | Char | Nombre legible |
| `source_format` | Char | Tipo de archivo (excel) |
| `thickness_unit_heuristic` | Selection | auto_lt10_inch / always_mm / always_inch |
| `width_unit_heuristic` | Selection | auto_lt10_inch / always_mm / always_inch |
| `length_unit_heuristic` | Selection | auto_gt10_ft / always_m / always_ft |
| `conversion_mode` | Selection | inches_to_mm / feet_to_m / identity |
| `export_rule_outcome` | Selection | f5085 / f1550 / metric |
| `thickness_threshold` | Float | Umbral para heurística auto (< umbral → pulgadas) |
| `length_threshold` | Float | Umbral para heurística auto (> umbral → pies) |
| `column_mapping_json` | Text | Mapeo override de columnas Excel (JSON) |
| `notes` | Text | Documentación funcional |

**Constraints:** UNIQUE(profile, active). JSON válido en column_mapping_json.
**Seed Fase 3:** 4 registros (f5085, f1550, blanks, metric).
**Consumidor:** `reception_parser._process_dataframe()` vía `lumber.ingestion.format._resolve_for_profile()`.

### 10.3 Cierre de brecha `madenat.s2s_exclusion_widths`

**Problema:** `madenat.s2s_exclusion_widths` se leía directamente desde `ir.config_parameter` en:
- `utils_uom.py` → `get_s2s_adjustment()`
- Duplicado en `madenat_guia_processing.py`

**Solución Fase 3:**
- Nuevo método `get_s2s_exclusion_widths()` en `madenat.ingestion.config`
- `get_s2s_adjustment()` en `utils_uom.py` delega al helper centralizado
- Eliminada la duplicidad: ambos consumidores usan el mismo helper

**Prioridad de fuentes:**
1. `ir.config_parameter` 'madenat.s2s_exclusion_widths'
2. Hardcode legacy: [150, 160, 170, 180, 200]

---

## 11. Resumen de Cobertura

| Hardcode | Descripción | Fase | Mecanismo |
|----------|-------------|------|-----------|
| H1 | blanks_nominal_map | Fase 1+2 | `lumber.blank.nominal.map` |
| H2, H4 | profile_subproduct_filters | Fase 1+2 | `lumber.profile.subproduct.rule` |
| H5, H13 | thickness_visual_ranges | Fase 1+2 | `lumber.thickness.visual.rule` |
| H10, H11 | width_s2s_map | Fase 1+2 | `lumber.width.s2s.map` |
| H7 | CONSTANTE TÉCNICA | N/A | Se considera constante de ingeniería estable. Documentada, no parametrizada. |
| **H8** | **_compute_export_values** | **Fase 3** | `lumber.export.formula` |
| **H9** | **_process_dataframe** | **Fase 3** | `lumber.ingestion.format` |
| `s2s_exclusion_widths` | **Brecha de lectura directa** | **Fase 3** | `madenat.ingestion.config.get_s2s_exclusion_widths()` |
| H6, H12 | Pendientes | Futuro | Requieren análisis adicional |

---

## 12. Pendientes Deliberados

- **H6, H12:** No parametrizados. Requieren análisis de impacto estructural que excede el alcance de Fase 3.
- **H7:** Constante técnica estable (MBF_TO_M3 = 2.36). Documentada como regla de ingeniería, no como regla de negocio. No justifica modelo de mantenimiento.
- **Fórmulas matemáticas:** No se tocan sin auditoría formal.
- **Workflow:** No se modifica.
- **Otros hardcodes (H3, etc.):** Fuera del alcance quirúrgico de Fase 3.
