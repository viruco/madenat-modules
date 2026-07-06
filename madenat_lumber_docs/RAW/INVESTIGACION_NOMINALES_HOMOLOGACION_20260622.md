# INVESTIGACIÓN: Homologación Asignación Masiva + Nominales + Producto
**Fecha:** 2026-06-22 21:32
**Auditor:** Cline — modo investigación (sin cambios de código)
**Versión:** 1.0

---

## I. ASIGNACIÓN MASIVA en madenat_guia_processing

### I.1 Localización
- **Mecanismo:** WIZARD (TransientModel)
- **Modelo del wizard:** `madenat.guia.mass.update`
- **Archivo del wizard:** `custom_addons/madenat_lumber_core/wizard/madenat_guia_mass_update.py`
- **Vista XML del wizard:** `custom_addons/madenat_lumber_core/wizard/madenat_guia_mass_update_views.xml`
- **Método de acción:** `action_apply` (línea 58)
- **Invocación en vista:** `<button type="action" name="%(madenat_lumber_core.action_madenat_guia_mass_update)d"/>` en `guia_processing_views.xml`

### I.2 Qué hace exactamente (action_apply, líneas 58-123)
- **Campos que lee:**
  - `new_thickness_mm` (Float, opcional) — Espesor Nominal (mm)
  - `subproducto_id` (Many2one → madenat.subproducto, opcional)
  - `product_id` (Many2one → product.product, opcional)
  - `guia.processing_line_ids` (One2many → madenat.guia.processing.line)

- **Campos que escribe en las líneas de staging (`madenat.guia.processing.line`):**
  - `espesor_nominal_mm` ← `self.new_thickness_mm` (línea 100)
  - `thickness_visual` ← calculado por `_get_nominal_dimension()` (línea 105)
  - `subproducto_id` ← `self.subproducto_id.id` (línea 111)
  - `product_id` ← `self.product_id.id` (línea 116)

- **Campos que escribe en stock.lot:** **NO escribe directamente.** La propagación a stock.lot ocurre en `_create_or_get_lot()` (línea ≈3272) al procesar la guía.

- **¿Asigna product_id?:** **SÍ** — `madenat_guia_mass_update.py` línea 116: `lines.write({'product_id': self.product_id.id})`

- **¿Asigna subproducto_id?:** **SÍ** — `madenat_guia_mass_update.py` línea 111: `lines.write({'subproducto_id': self.subproducto_id.id})`

- **¿Fija espesor_nom?:** **SÍ** — Campo exacto en staging: `espesor_nominal_mm` (línea 100)

- **¿Fija ancho_nom?:** **NO** — El wizard de guia_processing NO tiene campo de ancho nominal ni lo escribe. Solo espesor, subproducto y producto.

### I.3 Vista XML del NÚCLEO DE INVENTARIO
- **Campo One2many:** `processing_line_ids` → `madenat.guia.processing.line`
- **Archivo de vista:** `custom_addons/madenat_lumber_core/views/guia_processing_views.xml`
- **Columnas de la tabla (NÚCLEO DE INVENTARIO):**
  - `lot_name` (Lote/Etiqueta)
  - `product_id` (Producto) — con opciones `no_open, no_create`
  - `subproducto_id` (Sub-Producto) — opcional
  - `espesor_nominal_mm` (Espesor Nominal mm)
  - `ancho_nominal_mm` (Ancho Nominal mm)
  - `largo_nominal_m` (Largo Nominal m)
  - `pieces` (Piezas)
  - `vol_purchase_m3` (Vol. Compra m³)
- **¿Tiene columna Producto?:** **SÍ** — field name: `product_id`, string="Producto"
- **¿Tiene columna Subproducto?:** **SÍ** — field name: `subproducto_id`, string="Sub-Producto"

---

## II. Fijar Nominal Masivo en lumber_reception

### II.1 Localización
- **Mecanismo:** WIZARD (TransientModel)
- **Modelo del wizard:** `lumber.reception.mass.update`
- **Archivo del wizard:** `custom_addons/madenat_lumber_core/wizard/lumber_reception_mass_update.py`
- **Vista XML del wizard:** `custom_addons/madenat_lumber_core/wizard/lumber_reception_mass_update_views.xml`
- **Método de acción:** `action_apply` (línea 279)
- **Invocación en vista:** Botón `<button type="action" name="%(madenat_lumber_core.action_lumber_reception_mass_update)d"/>` en `lumber_reception_views.xml`

### II.2 Qué hace exactamente (action_apply, líneas 279-403)
- **Campos que lee:**
  - `thickness_nominal_frac` (Char) — input visual en fracciones imperiales o mm directos
  - `width_nominal_frac` (Char) — input visual en fracciones imperiales o mm directos
  - `thickness_nominal` (Float, computed) — resultado en mm
  - `width_nominal` (Float, computed) — resultado en mm
  - `subproduct_id` (Many2one → madenat.subproducto)
  - `apply_to` (Selection: selected/all)
  - `reception_id` (Many2one → lumber.reception)

- **Campos que escribe en las líneas de staging (`lumber.reception.line`):**
  - `thickness_nominal` ← `self.thickness_nominal` (línea 348)
  - `thickness_nominal_frac` ← `self.thickness_nominal_frac` (línea 350)
  - `width_nominal` ← `self.width_nominal` (línea 353)
  - `width_nominal_frac` ← `self.width_nominal_frac` (línea 355)
  - `subproduct_id` ← `self.subproduct_id.id` (línea 357)

- **Campos que escribe en stock.lot:** **NO escribe directamente.** La propagación ocurre en `LumberReceptionService.create_lots_from_staging()` (reception_service.py).

- **¿Asigna product_id?:** **NO** — El wizard `lumber.reception.mass.update` **NO** tiene campo `product_id`. Evidencia:
  - Wizard fields (líneas 28-274): NO incluye `product_id`
  - `action_apply` (líneas 279-403): NO escribe `product_id` en las líneas
  - Vista XML (líneas 1-180): NO muestra campo `product_id`

- **¿Asigna subproducto_id?:** **SÍ** — `lumber_reception_mass_update.py` línea 357: `vals['subproduct_id'] = self.subproduct_id.id`

- **¿Fija espesor_nom?:** **SÍ** — Campo exacto en staging: `thickness_nominal` (NO "espesor_nominal_mm" como en guia_processing)

- **¿Fija ancho_nom?:** **SÍ** — Campo exacto en staging: `width_nominal`

### II.3 Vista XML de la pestaña Análisis Comercial
- **Campo One2many:** `reception_line_ids` → `lumber.reception.line`
- **Archivo de vista:** `custom_addons/madenat_lumber_core/views/lumber_reception_views.xml`
- **Columnas de la tabla (Validación Comercial):**
  - `lot_name` (Etiqueta/Lote)
  - `product_id` (Producto) — con contexto `display_default_code: False`
  - `subproduct_id` (Grado)
  - `thickness_nominal` (Espesor Nom. mm)
  - `width_nominal` (Ancho Nom. mm)
  - `length_nominal` (Largo Nom. m)
  - `pieces` (Piezas)
  - `vol_purchase_m3` (Vol. Compra m³)
- **¿Tiene columna Producto?:** **SÍ** — field name: `product_id`, string="Producto"
- **¿Tiene columna Subproducto?:** **SÍ** — field name: `subproduct_id`, string="Grado"

---

## III. Tabla Comparativa

| Dimensión | guia_processing | lumber_reception | Gap |
|---|---|---|---|
| Mecanismo (wizard/directo) | WIZARD | WIZARD | ✅ Ambos usan wizard |
| Asigna product_id | **SÍ** | **NO** | ❌ GAP CRÍTICO |
| Asigna subproducto_id | SÍ | SÍ | ✅ Igual |
| Fija espesor_nom | SÍ (`espesor_nominal_mm`) | SÍ (`thickness_nominal`) | Nombres diferentes |
| Fija ancho_nom | **NO** | SÍ (`width_nominal`) | ❌ GAP INVERSO |
| Nombre campo espesor_nom en líneas | `espesor_nominal_mm` | `thickness_nominal` | ❌ NOMBRES DIFERENTES |
| Nombre campo ancho_nom en líneas | `ancho_nominal_mm` | `width_nominal` | ❌ NOMBRES DIFERENTES |
| Nombre campo espesor_nom en stock.lot | `espesor_nominal_mm` | `(no se llena)` | ❌ GAP PROPAGACIÓN |
| Propaga a stock.lot directamente | Vía `_create_or_get_lot()` | Vía `LumberReceptionService` | ❌ Service no copia nominales |
| Columna Producto en tabla UI | SÍ (`product_id`) | SÍ (`product_id`) | ✅ Igual |
| Columna Subproducto en tabla UI | SÍ (`subproducto_id`) | SÍ (`subproduct_id`) | ✅ Igual pero nombre de campo difiere |

---

## IV. Causa Raíz: Esp. Nom = 0,000 en lumber_reception

### Cadena de causas (de arriba hacia abajo):

1. **Origen de datos (parser → staging):** `_fill_staging_table()` (lumber_reception.py:2113) crea líneas con `thickness_nominal: item.get('thickness_nominal', 0.0)`. Si el parser no trae nominales, el valor por defecto es `0.0`.

2. **El wizard `lumber.reception.mass.update` SÍ puede fijar `thickness_nominal` en las líneas** (línea 348 del wizard), pero el valor escrito es en `lumber.reception.line`, NO en `stock.lot`.

3. **`LumberReceptionService.create_lots_from_staging()` (reception_service.py:46-69) NO propaga `line.thickness_nominal` → `stock.lot.espesor_nominal_mm`.**  
   Evidencia en línea 48-69: los `lot_vals` incluyen:
   - `espesor_mm` ← `line.thickness` (físico)  ✅
   - `ancho_mm` ← `line.width` (físico)       ✅
   - `espesor_inch_frac` ← `line.thickness_visual` ✅
   - `thickness_visual` ← `line.thickness_visual`  ✅
   - **NO incluye:** `espesor_nominal_mm` ← `line.thickness_nominal`  ❌
   - **NO incluye:** `ancho_nominal_mm` ← `line.width_nominal`        ❌

4. **`stock.lot.espesor_nominal_mm` se inicializa en 0.0** (no hay default explícito en la definición del campo en stock_lot.py) y **nunca es escrito desde el flujo de lumber_reception**, por lo que permanece en 0.000.

5. **En guia_processing, esto funciona** porque el wizard escribe `espesor_nominal_mm` directamente en las líneas de staging, y luego `_create_or_get_lot()` en madenat_guia_processing.py propaga ese valor a `stock.lot.espesor_nominal_mm`.

### Conclusión:
- **Causa raíz principal:** `reception_service.py` (línea 46-69) omite copiar `line.thickness_nominal` → `espesor_nominal_mm` al crear/actualizar `stock.lot`.
- **Causa raíz secundaria:** Los nombres de campo son diferentes entre ambos módulos (`thickness_nominal` vs `espesor_nominal_mm`), lo que impide una propagación automática por convención.

---

## V. Gaps Confirmados para Homologación

| # | Gap | Archivo:Línea | Impacto | Severidad |
|---|-----|---------------|---------|-----------|
| 1 | Wizard `lumber.reception.mass.update` NO tiene campo `product_id` | `wizard/lumber_reception_mass_update.py:11-274` | Usuario no puede asignar Producto masivamente en lumber_reception | **ALTO** |
| 2 | `LumberReceptionService` NO propaga `thickness_nominal` → `stock.lot.espesor_nominal_mm` | `reception_service.py:46-69` | Esp. Nom = 0,000 en stock.lot de lumber_reception | **CRÍTICO** |
| 3 | `LumberReceptionService` NO propaga `width_nominal` → `stock.lot.ancho_nominal_mm` | `reception_service.py:46-69` | Ancho Nom = 0,000 en stock.lot de lumber_reception | **CRÍTICO** |
| 4 | Nombre de campo espesor nominal difiere: `thickness_nominal` (lumber) vs `espesor_nominal_mm` (guia) | `lumber_reception.py` vs `madenat_guia_processing.py` | Confusión en mantenimiento, incompatibilidad de APIs | **MEDIO** |
| 5 | Nombre de campo ancho nominal difiere: `width_nominal` (lumber) vs `ancho_nominal_mm` (guia) | `lumber_reception.py` vs `madenat_guia_processing.py` | Confusión en mantenimiento, incompatibilidad de APIs | **MEDIO** |
| 6 | Wizard guia_processing NO fija ancho nominal (solo espesor) | `madenat_guia_mass_update.py:58-123` | Ancho nominal no se puede asignar masivamente en guia_processing | **MEDIO** |
| 7 | Nombre campo subproducto difiere: `subproduct_id` (lumber) vs `subproducto_id` (guia) | Ambos modelos | Inconsistencia de naming | **BAJO** |

---

## VI. Infraestructura Existente Reutilizable

1. **Wizard `lumber.reception.mass.update`** (lumber_reception_mass_update.py): ya tiene la estructura completa, solo falta agregar `product_id`.
2. **Wizard `madenat.guia.mass.update`** (madenat_guia_mass_update.py): referencia completa de cómo debe verse — tiene `product_id`, `subproducto_id`, y `new_thickness_mm`.
3. **Campos nominales en `stock.lot`** (stock_lot.py): `espesor_nominal_mm` y `ancho_nominal_mm` ya existen y son usados por los cálculos de volumen.
4. **`LumberReceptionService.create_lots_from_staging()`** (reception_service.py:17-97): punto único de propagación staging → stock.lot, solo necesita agregar 2 campos al diccionario `lot_vals`.
5. **Mixin `LumberIngestLineMixin`** (mixin_lumber_ingest.py:261-348): ambos modelos de líneas heredan `product_id` y `subproducto_id` de este mixin (línea 273).
6. **Vista XML del wizard lumber_reception** (lumber_reception_mass_update_views.xml): ya tiene espacio para `subproduct_id` en el grupo "Clasificación MADENAT", se puede agregar `product_id` en el mismo grupo.

---

## VII. Propuesta de Cambios Mínimos (solo diseño, sin implementar)

### Cambio 1: Agregar `product_id` al wizard `lumber.reception.mass.update`
- **Archivo:** `wizard/lumber_reception_mass_update.py`
- **Agregar campo:** `product_id = fields.Many2one('product.product', string='Producto')`
- **Agregar en action_apply:** `vals['product_id'] = self.product_id.id` (solo si tiene valor)
- **Agregar en vista XML:** campo `product_id` en grupo "Clasificación MADENAT"

### Cambio 2: Propagar nominales en `LumberReceptionService`
- **Archivo:** `models/reception_service.py`
- **Agregar a lot_vals (línea ~59):**
  ```python
  'espesor_nominal_mm': line.thickness_nominal or 0.0,
  'ancho_nominal_mm': line.width_nominal or 0.0,
  ```

### Cambio 3 (opcional): Agregar `ancho_nominal_mm` al wizard de guia_processing
- **Archivo:** `wizard/madenat_guia_mass_update.py`
- **Agregar campo:** `new_width_mm = fields.Float(string="Ancho Nominal (mm)")`
- **Agregar en action_apply:** `lines.write({'ancho_nominal_mm': self.new_width_mm})`

---

## VIII. Anexo: Archivos y líneas de referencia

| Concepto | Archivo | Líneas |
|---|---|---|
| Wizard guia mass update (modelo) | `wizard/madenat_guia_mass_update.py` | 1-123 |
| Wizard guia mass update (vista) | `wizard/madenat_guia_mass_update_views.xml` | 1-49 |
| Wizard lumber mass update (modelo) | `wizard/lumber_reception_mass_update.py` | 1-403 |
| Wizard lumber mass update (vista) | `wizard/lumber_reception_mass_update_views.xml` | 1-180 |
| Líneas guia staging | `models/madenat_guia_processing.py` | 42-348 (class MadenatGuiaProcessingLine) |
| Líneas lumber staging | `models/lumber_reception.py` | class LumberReceptionLine (hereda mixin) |
| Mixin línea ingesta | `models/mixin_lumber_ingest.py` | 261-348 (product_id línea 273) |
| stock.lot modelo | `models/stock_lot.py` | espesor_nominal_mm, ancho_nominal_mm |
| Reception service | `models/reception_service.py` | 17-97 (create_lots_from_staging) |
| Fill staging table | `models/lumber_reception.py` | 2051-2138 (_fill_staging_table) |
| Vista guia NÚCLEO | `views/guia_processing_views.xml` | tabla processing_line_ids |
| Vista lumber Análisis Comercial | `views/lumber_reception_views.xml` | tabla reception_line_ids |