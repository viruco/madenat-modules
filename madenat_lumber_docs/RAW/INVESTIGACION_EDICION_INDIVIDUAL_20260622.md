# INVESTIGACIÓN: Edición Individual de Líneas
**Fecha:** 2026-06-21 22:30
**Auditor:** Cline — modo investigación (sin cambios)
**Referencia previa:** INVESTIGACION_NOMINALES_HOMOLOGACION_20260622.md

---

## I. Cómo funciona la edición individual en guia_processing

### I.1 Mecanismo de edición

| Pestaña | ¿Tree editable inline? | Atributo | create/delete |
|---|---|---|---|
| 📍 Recepción Física (Bodega) | SÍ | `editable="bottom"` | sin restricción |
| 💲 Análisis Comercial (OC) | SÍ | `editable="bottom"` | `create="0" delete="0"` |
| 🌎 Vista (Exportación) | SÍ | `editable="bottom"` | `create="0" delete="0"` |

- **¿Formulario de línea existe?** NO. No existe ningún `<form>` ni `<record>` con `res_model='madenat.guia.processing.line'` y `view_mode='form'`. Las líneas solo se editan inline en los trees de las pestañas del formulario padre.
  - Evidencia: búsqueda `grep -rn "madenat.guia.processing.line" ./custom_addons/madenat_lumber_core/views/` con filtro `form|view_type|res_model` → cero resultados.

- **Vista completa del tree "Análisis Comercial":**
  - Archivo: `./custom_addons/madenat_lumber_core/views/guia_processing_views.xml:557`
  - `<list string="Análisis Comercial" editable="bottom" create="0" delete="0">`

### I.2 Comportamiento por campo en tree "Análisis Comercial" (guia_processing)

| Campo | ¿Editable inline? | ¿readonly? | ¿onchange? | ¿compute? | Atributos en tree |
|---|---|---|---|---|---|
| **product_id** | SÍ | No | No | No | `options="{'no_open': True, 'no_create': True}"` |
| **subproducto_id** | SÍ | No | No | No | `optional="show" widget="badge" decoration-info="1"` |
| **espesor_nominal_mm** | SÍ | No | No | No | `decoration-info="1" class="fw-bold" width="80px"` (campo Float simple) |
| **ancho_nominal_mm** | SÍ | No | No | SÍ (`_compute_default_width`) | `decoration-info="1" class="fw-bold" width="80px"` (readonly=False, store=True, precompute=True) |
| **largo_nominal_m** | SÍ | No | No | SÍ (`_compute_default_length`) | `decoration-info="1" class="fw-bold" width="80px"` (readonly=False, store=True, precompute=True) |
| **pieces** | NO | `readonly="1"` | No | No | `class="text-end" width="80px"` |
| **vol_purchase_m3** | NO | `readonly="1"` | No | SÍ | `decoration-bf="1" class="text-end" width="100px" force_save="1" digits="[16, 3]"` |
| **thickness_visual** | N/A (column_invisible) | N/A | No | SÍ (`_compute_imperial_values`) | `column_invisible="1"` (oculto en esta pestaña; editable en pestaña Exportación) |

### I.3 Flujo completo al editar espesor individual

**Paso a paso cuando el usuario edita `espesor_nominal_mm` en el tree "Análisis Comercial":**

1. **Trigger:** El tree tiene `editable="bottom"`. El campo `espesor_nominal_mm` es un `fields.Float` simple (sin readonly, sin compute) definido en:
   - Archivo: `./custom_addons/madenat_lumber_core/models/madenat_guia_processing.py:105`
   - `espesor_nominal_mm = fields.Float("Espesor Nominal (mm)", digits=(10, 3), help="Espesor de compra para análisis comercial")`

2. **Al modificar el valor:** Como es un campo Float simple (sin compute, sin onchange propio), el valor se guarda directamente en la base de datos.

3. **Efecto cascada:** El método `_compute_imperial_values` (línea ~250-270) tiene `@api.depends('espesor_nominal_mm', 'espesor_mm', ...)`. Al cambiar `espesor_nominal_mm`, Odoo dispara el recompute:
   ```python
   # Archivo: madenat_guia_processing.py, línea ~257
   @api.depends('espesor_nominal_mm', 'espesor_mm',
                'ancho_nominal_mm', 'ancho_mm',
                'largo_nominal_m', 'largo_m')
   def _compute_imperial_values(self):
       for rec in self:
           # A. ESPESOR → thickness_visual
           val_thick_mm = rec.espesor_nominal_mm if rec.espesor_nominal_mm > 0 else rec.espesor_mm
           
           mapped_thick = None
           if val_thick_mm > 0:
               for std_mm, txt in LUMBER_DIMENSION_MAP.get('thickness', {}).items():
                   if abs(val_thick_mm - std_mm) <= 3:  # tolerancia 3mm
                       mapped_thick = txt
                       break
           
           if mapped_thick:
               rec.thickness_visual = mapped_thick
           elif val_thick_mm > 0 and not rec.thickness_visual:
               # Solo recalcula si NO hay valor manual previo
               rec.thickness_visual = self._get_fraction_text(val_thick_mm * MM_TO_INCH)
   ```

4. **Protección del valor manual:** La condición `not rec.thickness_visual` en la línea del else protege que si el usuario ya había editado manualmente `thickness_visual` en la pestaña Exportación, no se sobreescriba al cambiar `espesor_nominal_mm`.

5. **También recalcula `vol_purchase_m3`** (si está definido el método v2) y `vol_mbf` (depende de thickness_visual).

### I.4 Conversión fracciones → mm

- **Método en guia_processing:** `_get_fraction_text(value)` — definido en el modelo `MadenatGuiaProcessingLine` (línea ~340+). Convierte un valor decimal (pulgadas) a fracción en 16avos.
- **Mapa maestro:** `LUMBER_DIMENSION_MAP` contiene mapeos estándar mm ↔ fracción imperial.
  - thickness: tolerancia ±3mm
  - width: tolerancia ±2mm
- **Flujo inverso (fracción → mm):** NO existe un inverse en espesor_nominal_mm. Si el usuario edita `thickness_visual` en la pestaña Exportación, NO recalcula `espesor_nominal_mm`. Son flujos separados.

---

## II. Cómo funciona (o no) la edición individual en lumber_reception

### II.1 Mecanismo actual

| Pestaña | ¿Tree editable inline? | Atributo | Bloqueo por state |
|---|---|---|---|
| 1. 📋 Detalle Físico (Original) | NO | `readonly="1"` en field padre | N/A |
| 2. ✅ Validación Comercial | SÍ | `editable="bottom"` | `readonly="state == 'done'"` en field padre |
| 3. 🌍 EXPORTACIÓN | NO | `readonly="1"` en field padre | N/A |

- Archivo: `./custom_addons/madenat_lumber_core/views/lumber_reception_views.xml:372-373`
  ```xml
  <field name="reception_line_ids" readonly="state == 'done'">
      <list string="Validación Comercial" editable="bottom">
  ```

### II.2 Comportamiento por campo en tree "Validación Comercial" (lumber_reception)

| Campo | ¿Editable inline? | ¿readonly? | ¿onchange? | ¿compute? | Atributos en tree / Estado actual |
|---|---|---|---|---|---|
| **product_id** | **NO** | `readonly="1"` | No | No (del mixin) | `options="{'no_open': True, 'no_create': True}"` — **BLOQUEADO siempre** |
| **subproduct_id** | SÍ | No | No | No | `required="1"` + domain con lógica de perfil |
| **thickness_nominal** | SÍ (perfiles metric, f1550) | No | No | No (Float simple) | `column_invisible="parent.ingestion_profile == 'f5085'"` |
| **width_nominal** | SÍ (perfiles metric, f1550) | No | No | No (Float simple) | `column_invisible="parent.ingestion_profile == 'f5085'"` |
| **thickness_visual** | SÍ (perfiles f5085, f1550) | `readonly="0"` (explícito) | No | SÍ (`_compute_visual_defaults`) | `column_invisible="parent.ingestion_profile not in ('f5085', 'f1550')"` |
| **width_visual** | SÍ (perfiles f5085, f1550) | `readonly="0"` (explícito) | No | SÍ (`_compute_visual_defaults`) | `column_invisible="parent.ingestion_profile not in ('f5085', 'f1550')"` |
| **pieces** | NO | `readonly="1"` | No | No (del mixin) | `sum="Total Pzas"` |
| **vol_purchase_m3** | NO | No (pero compute con inverse) | No | SÍ | `sum="Total Ingreso" decoration-bf="1" digits="[16, 3]"` |

### II.3 ¿Qué bloquea la edición individual en lumber_reception?

**Causa raíz exacta para `product_id`:**

| # | Bloqueo | Archivo:Línea | Detalle |
|---|---------|---------------|---------|
| 1 | `readonly="1"` en tree | `lumber_reception_views.xml:378` | `<field name="product_id" string="Producto" options="{'no_open': True, 'no_create': True}" readonly="1"/>` |

**A diferencia de guia_processing donde `product_id` SÍ es editable:**
- `guia_processing_views.xml:559`: `<field name="product_id" string="Producto" options="{'no_open': True, 'no_create': True}"/>` — sin readonly

**Para `thickness_nominal` y `width_nominal`:** Son editables en los perfiles métricos (metric, f1550), pero están ocultos (`column_invisible`) en el perfil f5085. En f5085 se usan `thickness_visual`/`width_visual` (fracciones imperiales).

**Estado del documento:** El tree entero se bloquea cuando `state == 'done'` (atributo `readonly="state == 'done'"` en el field `reception_line_ids`, línea 372). Pero en estados draft/verified, el tree es editable.

### II.4 `_compute_visual_defaults` en lumber_reception.line

```python
# Archivo: lumber_reception.py, línea 555
def _compute_visual_defaults(self):
    for line in self:
        # Si ya hay valores fraccionarios manuales, copiarlos a visuales
        if line.thickness_nominal_frac and line.width_nominal_frac:
            line.thickness_visual = line.thickness_nominal_frac
            line.width_visual = line.width_nominal_frac
        else:
            # Calcular desde valores documentales
            t_doc_in = line._parse_smart_dimension(line.thickness_document_value)
            w_doc_in = line._parse_smart_dimension(line.width_document_value)
            if t_doc_in > 0:
                line.thickness_visual = line._get_fraction_text(t_doc_in)
                line.thickness_nominal_frac = line._get_fraction_text(t_doc_in)
            if w_doc_in > 0:
                line.width_visual = line._get_fraction_text(w_doc_in)
                line.width_nominal_frac = line._get_fraction_text(w_doc_in)
```

**Protección de edición manual:** Si `thickness_nominal_frac` ya tiene valor (escrito por wizard o manualmente), el compute copia ese valor a `thickness_visual` en vez de recalcular. Esto protege la edición manual.

---

## III. Mixin compartido: capacidades reutilizables

### III.1 Campos del mixin `LumberIngestLineMixin`

Archivo: `./custom_addons/madenat_lumber_core/models/mixin_lumber_ingest.py:261`

| Campo | Tipo | Atributos |
|---|---|---|
| `lot_name` | Char | required=True |
| `product_id` | Many2one('product.product') | required=True |
| `vol_shipment_m3` | Float | digits=(16,3) |
| `vol_purchase_m3` | Float | digits=(16,3) |
| `pieces` | Integer | |
| `raw_dims` | Char | |
| `calc_method` | Char | readonly=True |
| `is_modified` | Boolean | |
| `warning_msg` | Char | compute='_compute_warning', store=True |

**IMPORTANTE:** El mixin NO incluye campos nominales (thickness_nominal, width_nominal, espesor_nominal_mm, ancho_nominal_mm), ni subproducto, ni visuales. Estos están definidos **individualmente en cada modelo hijo**.

### III.2 Onchanges heredados del mixin

| Onchange | Dependencias | Descripción |
|---|---|---|
| `_on_change_volumes` | `vol_shipment_m3`, `vol_purchase_m3` | Maneja cambios de volumen |

**NO hay onchange en el mixin para conversión frac → mm.** Esta lógica está en cada modelo hijo.

### III.3 Herencia confirmada

| Modelo | Hereda de | Archivo:Línea |
|---|---|---|
| `madenat.guia.processing.line` | `['madenat.lumber.ingest.line.mixin']` | `madenat_guia_processing.py:67` |
| `lumber.reception.line` | `['madenat.lumber.ingest.line.mixin']` | `lumber_reception.py:54` |

### III.4 write/create override en mixin

**NO hay** `def write` ni `def create` en `LumberIngestLineMixin`. Solo métodos helpers `@api.model`. Los overrides de write/create están en:
- `LumberReceptionLine.write()` → `lumber_reception.py:253-267` (solo sanitiza lot_name + valida dimensiones físicas)
- `LumberReceptionLine.create()` → `lumber_reception.py:236-250`

---

## IV. Gaps para edición individual (nuevos)

| # | Gap | Archivo:Línea | Severidad |
|---|-----|---------------|-----------|
| 1 | `product_id` tiene `readonly="1"` en tree lumber_reception, bloqueando edición individual | `lumber_reception_views.xml:378` | **ALTA** — Es la diferencia principal con guia_processing |
| 2 | `thickness_nominal` y `width_nominal` en lumber_reception son campos Float simples (sin compute), mientras en guia_processing `ancho_nominal_mm` tiene compute+precompute para pre-llenado automático | `lumber_reception.py:168-173` vs `madenat_guia_processing.py:108-122` | MEDIA — El pre-llenado automático desde dimensiones físicas no existe en lumber_reception |
| 3 | `thickness_nominal` en lumber_reception NO tiene `@api.depends` ni `onchange` que actualice `thickness_visual` al cambiar, a diferencia de guia_processing donde `_compute_imperial_values` depende de `espesor_nominal_mm` | `lumber_reception.py:168` | **ALTA** — Editar thickness_nominal en lumber_reception NO actualiza thickness_visual automáticamente |
| 4 | La lógica de conversión mm→fracción existe en ambos modelos pero con métodos diferentes (`_compute_imperial_values` vs `_compute_visual_defaults`) y fuentes de datos diferentes (nominal_mm vs document_value) | Ambos modelos | MEDIA — Arquitectura no homologada |
| 5 | `subproducto_id` en guia_processing NO tiene domain/restricción; en lumber_reception tiene domain complejo por perfil | `guia_processing_views.xml:561` vs `lumber_reception_views.xml:382` | BAJA |

---

## V. Propuesta de homologación (solo diseño)

### Cambios mínimos necesarios para que lumber_reception tenga la misma experiencia de edición individual que guia_processing:

1. **Quitar `readonly="1"` de `product_id`** en el tree "Validación Comercial" de lumber_reception:
   - Archivo: `lumber_reception_views.xml:378`
   - Cambio: eliminar `readonly="1"`

2. **Agregar `@api.depends` a `_compute_visual_defaults` para que incluya `thickness_nominal` y `width_nominal`** (o crear un onchange):
   - Actualmente `_compute_visual_defaults` no tiene `@api.depends` visible que incluya thickness_nominal
   - Se necesita que al editar `thickness_nominal` (mm), se recalcule `thickness_visual` (fracción)

3. **Agregar pre-llenado automático** de `thickness_nominal` y `width_nominal` desde dimensiones físicas (equivalente a `_compute_default_width`/`_compute_default_length` de guia_processing)

4. **Evaluar si se necesita inverse** para thickness_visual → thickness_nominal (en guia_processing no existe este inverse, son flujos independientes)

---

## VI. Tabla comparativa final

| Aspecto | guia_processing | lumber_reception | ¿Homologado? |
|---|---|---|---|
| Tree editable inline | SÍ (`editable="bottom"`) | SÍ (`editable="bottom"`) | ✅ |
| product_id editable | SÍ | **NO** (`readonly="1"`) | ❌ GAP |
| subproducto_id editable | SÍ | SÍ | ✅ |
| Espesor nominal editable | SÍ (`espesor_nominal_mm`) | SÍ (`thickness_nominal`, perfiles métricos) | ✅ |
| Ancho nominal editable | SÍ (`ancho_nominal_mm`) | SÍ (`width_nominal`, perfiles métricos) | ✅ |
| Espesor visual editable | SÍ (pestaña Exportación) | SÍ (`thickness_visual`, perfiles imperiales) | ✅ |
| Ancho visual editable | SÍ (pestaña Exportación) | SÍ (`width_visual`, perfiles imperiales) | ✅ |
| Pre-llenado nominal desde físico | SÍ (`_compute_default_width`) | **NO** | ❌ GAP |
| Nominal→Visual automático | SÍ (`_compute_imperial_values`) | **NO** (depende de document_value, no de nominal) | ❌ GAP |
| Formulario de línea | NO | NO | ✅ |
| write() override restrictivo | NO | Solo sanitiza lot_name | ✅ |
