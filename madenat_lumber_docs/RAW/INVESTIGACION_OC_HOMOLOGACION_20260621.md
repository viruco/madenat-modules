# INVESTIGACIÓN: Homologación OC lumber_reception ↔ guia_processing
**Fecha:** 2026-06-21
**Auditor:** Cline — modo investigación (sin cambios)
**Versión:** 1.0

---

## I. Flujo `lumber_reception` — OC end-to-end

### I.1 Captura documental

**I.1.A — Regex de extracción de `poref` del PDF**

[HECHO PROBADO] Archivo: `reception_parser.py:584-597`. `parse_dispatch_guide` usa 3 patrones secuenciales:

```python
# Patrón 1 — con prefijo explícito "ORDEN DE COMPRA/OC/O/C/NRO/N°/Nº"
r'(?:ORDEN\s+DE\s+COMPRA|OC|O/C|NRO\.?|N°|Nº|Orden)\s*[:\-]?\s*([A-Z]{2,3}[\s\-]*\d{3,5}[\s\-]+\d{1,6})'

# Patrón 2 — formato suelto con 2 espacios/guiones
r'\b([A-Z]{2,3}[\s\-]+\d{3,5}[\s\-]+\d{1,6})\b'

# Patrón 3 — formato con guiones explícitos
r'\b([A-Z]{2,3}[\-]\d{3,5}[\-]\d{1,6})\b'
```

El valor raw se normaliza vía `_normalizar_oc()` (línea 548-554) y luego `normalize_po_display()` (línea 521-529). Este último espera patrón `PREFIJO + ESPACIO + 3-5 dígitos + ESPACIO/GUIÓN + 1-6 dígitos`.

**I.1.B — Fallback desde Excel para OC**

[HECHO PROBADO] **NO EXISTE** en `lumber_reception`. El método `_process_dataframe` (reception_parser.py:373-502) **NO** extrae ni busca referencia de OC. El Excel solo se usa para líneas de paquetes (piezas, volumen, dimensiones).

[INFERENCIA] En contraste, `guia_processing` SÍ tiene `_find_oc_reference_in_excel` (`madenat_guia_processing.py:2607-2647`) que busca patrones `MC/OC/Orden` en las primeras 10 filas del Excel.

**I.1.C — `oc_pdf_file`: ¿PDF de la OC o de la guía?**

[HECHO PROBADO] Archivo: `lumber_reception.py:1317-1318`. El campo se llama `oc_pdf_file` con help `Obligatorio solo si la OC no existe en Odoo` y label `📄 1. PDF Orden de Compra`. Es el PDF de la OC (no de la guía).

Se parsea en `reception_workflow.py:68-82`:
```python
if reception.oc_pdf_file:
    oc_bytes = base64.b64decode(reception.oc_pdf_file)
    oc_data = parser.parse_purchase_order(oc_bytes)
```
El resultado (`oc_data`) contiene `po_ref_fallback`, `unit_price_usd`, `total_volume_m3`, `quality`, `thickness_mm`.

### I.2 Matching y vinculación

**I.2.A — Flujo de `run_ingestion_pipeline` para la OC**

[HECHO PROBADO] Archivo: `reception_workflow.py:18-168`. El pipeline ejecuta en orden:

1. **Gate 0** — validación pre-parseo de archivos (extensión, tamaño)
2. **Parseo PDF Guía** → `dg_data` con `po_ref`, `supplier_rut`, etc.
3. **Parseo PDF OC** (opcional) → `oc_data` con `po_ref_fallback`, precios
4. **Parseo Excel** → `pl_data` (sin OC)
5. **Gate 1** — reconciliación documental; recibe `oc_id=reception.purchase_id.id` (línea 204) pero **NO** lo usa activamente — el parámetro `oc_id` en `Gate1DocumentReconciliation.validate` (ingestion_gate.py:140) está declarado pero nunca se lee en el cuerpo del método.
6. **Llenado del staging**
7. **`_find_or_create_po_intelligent(dg_data, oc_data)`** — línea 134 → retorna `(po, supplier)`
8. **Check de duplicados** por guía si hay PO
9. **Transición a `verified`**

**I.2.B — `_find_or_create_po_intelligent` en core vs purchasing**

[HECHO PROBADO] Existen **DOS** implementaciones:

| Módulo | Método | Línea | Estrategia |
|---|---|---|---|
| `lumber_reception.py` (core) | `_find_or_create_po_intelligent` | 2253-2404 | **Self-contained**: extrae, normaliza, busca, persiste `oc_reference_raw`, vincula o va a fallback manual. PATCH 2026-06-18 **desactivó** autocreación automática. |
| `purchasing/models/lumber_reception.py` | `_find_po_and_supplier` | 17-119 | **Override por herencia**: mismo patrón find-and-link. NO crea OC. |

**¿Cuál se ejecuta realmente?**

[HECHO PROBADO] `reception_workflow.py:134` llama a `reception._find_or_create_po_intelligent(dg_data, oc_data)`. Como `madenat_lumber_purchasing` hereda `lumber.reception`, y si el método `_find_po_and_supplier` NO es llamado explícitamente por `_find_or_create_po_intelligent`, entonces **la versión del core es la que se ejecuta** (no hay override del nombre del método).

[INFERENCIA] El método `_find_po_and_supplier` del módulo purchasing existe pero **no es invocado** desde el flujo principal actual. Es código potencialmente muerto o usado desde otro punto de entrada no detectado en esta auditoría.

**I.2.C — ¿Qué sucede si `madenatlumberpurchasing` NO está instalado?**

[HECHO PROBADO] El core `lumber_reception.py` tiene toda la lógica self-contained (parser, normalización, búsqueda, persistencia). El método `_find_or_create_po_intelligent` no depende del módulo purchasing. **El flujo funciona sin purchasing instalado.**

**I.2.D — Escritura de `purchaseid`**

[HECHO PROBADO] Se escribe vía `self.write()` en `_find_or_create_po_intelligent` (lumber_reception.py:2360-2365):
```python
self.write({
    'purchase_id': po.id,
    'supplier_id': supplier.id,
    'oc_match_status': 'single_match',
    'oc_match_note': f'Auto-match exacto por nombre con {po.name}.',
})
```
No es campo compute. Es Many2one con escritura directa.

### I.3 Persistencia y limpieza

**I.3.A — ¿`manual_po_name` se limpia al vincular `purchase_id`?**

[HECHO PROBADO] En `_find_or_create_po_intelligent` del core: **NO se limpia explícitamente**. En el write del caso exitoso (línea 2360-2365) no se toca `manual_po_name`. 

En el override de purchasing (`_find_po_and_supplier`, línea 84-90): **SÍ se limpia**:
```python
self.write({
    'purchase_id': po.id,
    'supplier_id': supplier.id,
    'oc_match_status': 'singlematch',
    'oc_match_note': f'Auto-match por nombre contra PO {po.name}',
    'manual_po_name': False,   # ← SE LIMPIA
})
```

[HECHO PROBADO] En el caso "no encontrada" del core (línea 2385-2392): se escribe `'manual_po_name': po_ref`, **sobrescribiendo** cualquier valor previo que pudiera tener.

**I.3.B — ¿Existe `oc_reference_raw` en `lumber_reception.py`?**

[HECHO PROBADO] **SÍ, EXISTE Y ESTÁ IMPLEMENTADO.** Archivo: `lumber_reception.py:1137-1143`:
```python
oc_reference_raw = fields.Char(
    string="OC Documental",
    readonly=True,
    copy=False,
    tracking=True,
    help="Referencia documental de OC extraída desde la guía/PDF. Nunca se sobrescribe."
)
```
Se persiste en `_find_or_create_po_intelligent` línea 2286-2290:
```python
if po_ref and not self.oc_reference_raw:
    self.write({'oc_reference_raw': po_ref})
```

**I.3.C — ¿Existe `oc_match_status` en `lumber_reception.py`?**

[HECHO PROBADO] **SÍ, EXISTE Y ESTÁ IMPLEMENTADO.** Archivo: `lumber_reception.py:1144-1150`:
```python
oc_match_status = fields.Selection([
    ('not_found', 'No encontrada'),
    ('single_match', 'Coincidencia exacta'),
    ('multi_match', 'Múltiples coincidencias'),
    ('manual', 'Vinculación manual'),
    ('created', 'Creada desde recepción'),
], string="Estado Match OC", default='not_found', tracking=True, copy=False)
```

**I.3.D — Campo `purchase_order` (Char compute)**

[HECHO PROBADO] Archivo: `lumber_reception.py:1194-1206`. Prioridad:
1. `purchase_id.name` → canonizado
2. `manual_po_name` → canonizado
3. `oc_reference_raw` → canonizado
4. `'SIN ORDEN'`

### I.4 Propagación a `stock.lot`

**I.4.A — ¿`create_lots_from_staging` escribe `purchase_order_id`?**

[HECHO PROBADO] Archivo: `reception_service.py:46-64`. El dict `lot_vals` **NO incluye** `purchase_order_id` ni `supplier_id`. Las claves escritas son: `name`, `ref`, `product_id`, `reception_id`, `subproducto_id`, `piezas`, `espesor_mm`, `ancho_mm`, `largo_m`, `volume_purchase_m3`, `volumen_m3`, `vol_shipment_m3`, `espesor_inch_frac`, `ancho_inch_frac`, `thickness_visual`, `width_visual`, `length_ft`.

[HECHO PROBADO] La asignación de `purchase_order_id` en `stock.lot` es 100% vía compute `_compute_purchase_info` (`stock_lot.py:839-866`).

**I.4.B — ¿Cómo se dispara `_compute_purchase_info` para lotes de `lumber_reception`?**

[HECHO PROBADO] El compute depende de `reception_id` y `guia_processing_id` (stock_lot.py:839). Cuando se crea/actualiza un lote con `reception_id`, Odoo **debería** reevaluar el compute automáticamente. La lógica (línea 860-863):
```python
for lot in remaining_lots.filtered(lambda l: l.reception_id):
    if lot.reception_id.purchase_id:
        lot.purchase_order_id = lot.reception_id.purchase_id
    lot.supplier_id = lot.reception_id.supplier_id or (...)
```
[INFERENCIA] El compute **depende de reception_id.purchase_id**, pero la dependencia declarada es solo `@api.depends('reception_id', 'guia_processing_id')`. Si `reception_id.purchase_id` cambia después de que el lote ya fue creado, el compute **no se re-ejecutará automáticamente** porque `purchase_id` del modelo `lumber.reception` no está en los depends del compute de `stock.lot`. Esto es una **brecha real**.

---

## II. Flujo `madenat.guia.processing` — OC end-to-end

### II.1 Captura documental

**II.1.A — ¿`action_verify_data` persiste `ordencompra` del PDF?**

[HECHO PROBADO] Archivo: `madenat_guia_processing.py:1357-1373`. **SÍ, AHORA LO HACE** (Patch 2026-06-18):
```python
if pdf_data.get('orden_compra'):
    oc_reference_detected = pdf_data['orden_compra']
    # ... luego en línea 1363-1373:
    if oc_reference_detected and not self.oc_reference_raw:
        update_vals['oc_reference_raw'] = oc_reference_detected
```

[INFERENCIA] Antes del Patch 2026-06-18, esto no se hacía. El contexto de la tarea mencionaba que "NO se persiste" — esto ya fue corregido por el patch reciente.

**II.1.B — ¿`_find_oc_reference_in_excel` se llama desde `action_verify_data`?**

[HECHO PROBADO] **NO directamente.** `action_verify_data` (línea 1227) no llama a `_find_oc_reference_in_excel`. Sin embargo, el método `_find_oc_reference_in_excel` existe (línea 2607) y está disponible para ser invocado. Busca con regex:
```python
r'((?:MC|OC|Orden)\s*[:.\-]?\s*[A-Z0-9]+(?:[\s\-][A-Z0-9]+)+)'
```
en las primeras 10 filas del Excel.

**II.1.C — ¿Se parsea `oc_pdf_file` para extraer OC?**

[HECHO PROBADO] Archivo: `madenat_guia_processing.py:2741-2765`. El método `_extract_po_draft_values` **SÍ** parsea `oc_pdf_file`:
```python
if not self.oc_pdf_file:
    return {}
pdf_bytes = base64.b64decode(self.oc_pdf_file)
```
Extrae valores para prellenado seguro de creación de PO.

### II.2 Matching y vinculación

**II.2.A — ¿`order_id` tiene compute o onchange?**

[HECHO PROBADO] Archivo: `madenat_guia_processing.py:768`. El campo es:
```python
order_id = fields.Many2one('purchase.order', string="Orden de Compra", tracking=True)
```
**Sin `compute`, sin `@api.onchange`, sin `@api.depends`.** Es completamente manual.

**II.2.B — ¿`_match_purchase_order` existe y se usa?**

[HECHO PROBADO] Archivo: `madenat_guia_processing.py:3030-3123`. Método `_match_purchase_order` implementado con la misma lógica que `lumber_reception._match_reception_purchase_order`. Busca por `oc_reference_raw` normalizado. Soporta estados `single_match`, `multi_match`, `not_found`.

**II.2.C — En `do_full_processing` → `_create_or_get_lot`: condición de `purchase_order_id`**

[HECHO PROBADO] Archivo: `madenat_guia_processing.py:1023`:
```python
purchase_order = rec.order_id
```
Se pasa a `_create_or_get_lot` (línea 1097). Dentro de `_create_or_get_lot` (línea 3271-3272):
```python
if purchase_order:
    vals['purchase_order_id'] = purchase_order.id
```
**Condición exacta: `if purchase_order:`** — sin condiciones adicionales. Si `order_id` está asignado en la guía, se propaga al lote. Si no, el campo no se toca en el vals y queda sujeto al compute `_compute_purchase_info`.

### II.3 Propagación a `stock.lot`

**II.3.A — Escritura directa vs compute**

[HECHO PROBADO] En `_create_or_get_lot`, **SÍ** se escribe `purchase_order_id` directamente en `vals` (línea 3272) si `purchase_order` está presente. Esto es una **escritura directa en el create/update del lote**, no dependiente del compute.

**II.3.B — ¿Se escribe `supplier_id` también?**

[HECHO PROBADO] En el caso de creación (línea 3316-3317):
```python
if getattr(self, 'partner_id', False):
    vals['supplier_id'] = self.partner_id.id
```
**SÍ**, desde `self.partner_id` de la guía.

**II.3.C — Cuando NO hay `order_id` asignado: ¿qué pasa con `purchase_order_id` en el lote?**

[HECHO PROBADO] El compute `_compute_purchase_info` en `stock.lot` (línea 853-856) intenta resolver desde `guia_processing_id.order_id`. Si ambos son `False`, el campo queda `False`:
```python
for lot in existing_lots.filtered(lambda l: l.guia_processing_id and l.guia_processing_id.order_id):
    lot.purchase_order_id = lot.guia_processing_id.order_id
```
Si `order_id` no está asignado, el lote queda sin `purchase_order_id`.

---

## III. Análisis Comparativo

| Dimensión | `guia_processing` | `lumber_reception` |
|---|---|---|
| Campo OC en modelo | `order_id` (Many2one, manual) | `purchase_id` (Many2one, manual) |
| Extracción documental del PDF | `parse_dispatch_pdf` → clave `orden_compra` → persiste a `oc_reference_raw` en `action_verify_data` | `parse_dispatch_guide` → clave `po_ref` → persiste a `oc_reference_raw` en `_find_or_create_po_intelligent` |
| Persistencia referencia cruda | `oc_reference_raw` (Char, readonly) + `oc_reference_norm` (Char compute store) | `oc_reference_raw` (Char, readonly) |
| Matching automático | `_match_purchase_order` — busca por `oc_reference_raw` normalizado | `_find_or_create_po_intelligent` — busca por `po_key` normalizado + `_match_reception_purchase_order` — busca por `oc_reference_raw` |
| Creación automática de OC | `_extract_po_draft_values` extrae datos del PDF OC pero **NO crea automáticamente** (sin evidencia de llamado a `create_basic_purchase_order`) | **DESACTIVADA** (Patch 2026-06-18). `create_po_from_oc_data` existe pero no se invoca. |
| Escritura OC en `stock.lot.lotvals` | **SÍ** — directa en `_create_or_get_lot` (`vals['purchase_order_id'] = purchase_order.id`) | **NO** — `create_lots_from_staging` no incluye `purchase_order_id` en `lot_vals` |
| Campo OC en `stock.lot` (compute) | `_compute_purchase_info`: prioridad `guia_processing_id.order_id` → fallback `reception_id.purchase_id` | `_compute_purchase_info`: misma lógica |
| UI: campo para ref documental | `oc_reference_raw` + `order_id` (widget many2one) | `oc_reference_raw` + `purchase_id` (widget many2one) + `manual_po_name` (Char editable) |
| Riesgo de pérdida de referencia | **BAJO** — `oc_reference_raw` readonly, nunca se sobrescribe; `order_id` es asignación manual o vía `_match_purchase_order` | **MEDIO** — `manual_po_name` se sobrescribe en el caso "not_found"; pero `oc_reference_raw` ya protege la referencia documental |

---

## IV. Brechas Confirmadas

### B1 — `lumber_reception.action_verify_data` no persiste la referencia OC extraída del PDF

- **Estado:** [REFUTADA — YA CORREGIDA]
- **Evidencia:** `action_verify_data` (lumber_reception.py:2674-2727) es un método **diferente** al pipeline principal. Este método solo lee el Excel y crea staging lines; **no** parsea PDF. La extracción y persistencia de `oc_reference_raw` ocurre en `_find_or_create_po_intelligent` (línea 2286-2290), que es llamado desde `run_ingestion_pipeline` (reception_workflow.py:134).
- **Severidad:** N/A (la funcionalidad existe, solo que en método distinto al esperado)
- **Impacto funcional:** Ninguno — la referencia se persiste correctamente durante el pipeline de ingesta.

### B2 — `_find_or_create_po_intelligent` puede crear OCs espurias

- **Estado:** [REFUTADA — DESACTIVADA]
- **Evidencia:** lumber_reception.py:2373-2379:
  ```python
  # 🛑 PATCH 2026-06-18: DESACTIVADA autocreación automática de OC.
  # El flujo anterior llamaba a create_po_from_oc_data() si existía
  # oc_data y no había match. Esto generaba purchase.orders sin
  # supervisión humana...
  ```
  El método `create_po_from_oc_data` (línea 2408) existe pero **no es invocado** desde ningún punto del flujo principal.
- **Severidad:** N/A (corregido)
- **Impacto funcional:** Ninguno actual. El flujo ahora va a fallback manual (`manual_po_name = po_ref`, `oc_match_status = 'not_found'`).

### B3 — `manual_po_name` se limpia al vincular, perdiendo la referencia documental original

- **Estado:** [CONFIRMADA — PARCIALMENTE MITIGADA]
- **Evidencia:** 
  - En el override de purchasing (`_find_po_and_supplier`, línea 89): `'manual_po_name': False` — se limpia explícitamente.
  - En el core (`_find_or_create_po_intelligent`, línea 2385-2392): se sobrescribe con el nuevo `po_ref` si no hay match.
  - **PERO** `oc_reference_raw` (línea 2286-2290) **NO se sobrescribe nunca** gracias al guard `if po_ref and not self.oc_reference_raw`.
- **Severidad:** BAJA (mitigada por `oc_reference_raw`)
- **Impacto funcional:** Si un usuario había escrito algo en `manual_po_name` antes de procesar, ese valor se pierde al ejecutar el pipeline. La referencia documental verdadera está protegida en `oc_reference_raw`.

### B4 — `create_lots_from_staging` no escribe `purchase_order_id` en `lot_vals`

- **Estado:** [CONFIRMADA]
- **Evidencia:** reception_service.py:46-64 — el dict `lot_vals` no contiene `purchase_order_id` ni `supplier_id`.
- **Severidad:** MEDIA
- **Impacto funcional:** Los lotes de `lumber_reception` dependen 100% del compute `_compute_purchase_info` para recibir `purchase_order_id`. Si el compute no se dispara (ej: por caché de Odoo o porque `purchase_id` se asigna después del create del lote), el lote queda sin OC vinculada.
- **¿Ya existe infraestructura parcial?** El compute en `stock_lot.py:839-866` existe y funciona. Solo falta agregar `purchase_order_id` y `supplier_id` al `lot_vals` en `create_lots_from_staging` como escritura directa (defensa en profundidad).

### B5 — No existe campo equivalente a `oc_reference_raw` en `lumber_reception`

- **Estado:** [REFUTADA — YA EXISTE]
- **Evidencia:** lumber_reception.py:1137-1143 — `oc_reference_raw` está definido, implementado y poblado.
- **Severidad:** N/A

### B6 — `guia_processing.action_verify_data` tampoco persiste la referencia OC del PDF

- **Estado:** [REFUTADA — YA CORREGIDA]
- **Evidencia:** madenat_guia_processing.py:1357-1373 — el Patch 2026-06-18 agregó la persistencia de `orden_compra` del PDF hacia `oc_reference_raw`.
- **Severidad:** N/A

### B7 — `order_id` en `guia_processing` no tiene ningún mecanismo de sugerencia automática

- **Estado:** [CONFIRMADA]
- **Evidencia:** madenat_guia_processing.py:768 — campo Many2one sin compute, sin onchange. Existe `_match_purchase_order` (línea 3030) pero no se invoca automáticamente desde ningún botón del flujo estándar (`action_verify_data` no lo llama, `action_process_from_staging` no lo llama).
- **Severidad:** MEDIA
- **Impacto funcional:** El usuario debe asignar `order_id` manualmente o invocar `_match_purchase_order` explícitamente. Si no lo hace, `purchase_order_id` en `stock.lot` queda `False`.

### B8 — Las dos implementaciones de `validate_or_create_po` difieren

- **Estado:** [CONFIRMADA]
- **Evidencia:**

| Aspecto | `purchase_order.py:289-495` | `purchase_intake.py:118-192` |
|---|---|---|
| Retorno | `{success, po_id, state, message, po_name, error}` | `{status, po_id, reason}` |
| Búsqueda existente | Por `partner_ref` + `partner_id` | Por `partner_ref` + `partner_id` |
| Creación automática | Policy `auto_create` + requiere `lines` no vacías | Policy `auto` + crea con `order_line` |
| Validación de producto | `_resolve_product_with_fallback` → `MADERA_GENERICA` | `ensure_master_product` → busca/configura `MADERA_GENERICA` |
| Manejo de errores en líneas | Acumula, continúa, reporta fallos parciales | No tiene manejo robusto de errores por línea |
| Complejidad | 206 líneas, producción | 74 líneas, ¿legacy/alternativo? |

- **Severidad:** ALTA (dos APIs divergentes para la misma operación)
- **Impacto funcional:** Comportamiento inconsistente según qué método se llame. `purchase_order.validate_or_create_po` es más robusto. `purchase_intake.validate_or_create_po` es más simple pero menos defensivo.

---

## V. Infraestructura Existente Reutilizable

| Componente | Ubicación | Estado | Reutilizable para homologación |
|---|---|---|---|
| `oc_reference_raw` (Char, readonly) | `lumber_reception.py:1137`, `madenat_guia_processing.py:775` | ✅ IMPLEMENTADO en ambos | **Sí** — columna vertebral de trazabilidad documental |
| `oc_match_status` (Selection) | `lumber_reception.py:1144`, `madenat_guia_processing.py:789` | ✅ IMPLEMENTADO en ambos | **Sí** — estados consistentes entre módulos |
| `_match_reception_purchase_order` | `lumber_reception.py:1877` | ✅ IMPLEMENTADO | **Sí** — mismo patrón que `_match_purchase_order` en guia |
| `_match_purchase_order` | `madenat_guia_processing.py:3030` | ✅ IMPLEMENTADO | **Sí** — espejo del de lumber_reception |
| `normalize_po_key` / `normalize_po_display` | `reception_parser.py:514-529` | ✅ IMPLEMENTADO | **Sí** — ya unifica formato de matching |
| `ingestion_source_ref` en `purchase.order` | `purchase_order.py:49` | ✅ IMPLEMENTADO | **Sí** — trazabilidad de qué ingesta creó la OC |
| `create_basic_purchase_order` | `madenat_guia_processing.py:2449-2456` (referenciado en task) | ❓ NO ENCONTRADO con ese nombre exacto en líneas 2449-2456. El método `_create_po_from_oc_data` existe en lumber_reception.py:2408 pero está deprecado. | **No directamente** — requeriría refactor |
| Mixin / AbstractModel `madenat.purchase.intake` | `purchase_intake.py` | ✅ EXISTE como `madenat.lumber.purchase.intake` model | **Sí** — puede ser base para unificación |
| Escritura directa de `purchase_order_id` en lot vals | `madenat_guia_processing.py:3272` | ✅ IMPLEMENTADO en guia | **Sí** — patrón a replicar en `reception_service.py` |

---

## VI. Queries SQL de Verificación en BD

```sql
-- Q1: Lotes sin purchase_order_id pese a tener reception_id o guia_processing_id
SELECT COUNT(*) AS total, 
       COUNT(*) FILTER (WHERE reception_id IS NOT NULL) AS con_recepcion,
       COUNT(*) FILTER (WHERE guia_processing_id IS NOT NULL) AS con_guia
FROM stock_lot
WHERE purchase_order_id IS NULL
  AND (reception_id IS NOT NULL OR guia_processing_id IS NOT NULL);

-- Q2: Recepciones con manual_po_name poblado Y purchase_id también poblado
SELECT id, name, manual_po_name, purchase_id, oc_reference_raw, state
FROM lumber_reception
WHERE manual_po_name IS NOT NULL 
  AND manual_po_name != ''
  AND purchase_id IS NOT NULL;

-- Q3: purchase.order creadas automáticamente sin líneas (posible efecto B2 legacy)
SELECT po.id, po.name, po.partner_id, po.state, po.create_date,
       (SELECT COUNT(*) FROM purchase_order_line pol WHERE pol.order_id = po.id) AS lineas
FROM purchase_order po
WHERE po.provisional = true
  AND NOT EXISTS (SELECT 1 FROM purchase_order_line pol WHERE pol.order_id = po.id);

-- Q4: Guías procesadas con order_id NULL
SELECT id, name, state, order_id, oc_reference_raw, oc_match_status
FROM madenat_guia_processing
WHERE state IN ('processed', 'validated', 'done')
  AND order_id IS NULL;

-- Q5: Distribución de oc_match_status (si el campo existe en BD)
-- lumber_reception
SELECT oc_match_status, COUNT(*) AS total
FROM lumber_reception
GROUP BY oc_match_status
ORDER BY total DESC;

-- madenat_guia_processing
SELECT oc_match_status, COUNT(*) AS total
FROM madenat_guia_processing
GROUP BY oc_match_status
ORDER BY total DESC;

-- Q6: Recepciones con purchase_id NULL y manual_po_name poblado (OC sólo documental)
SELECT id, name, manual_po_name, oc_reference_raw, supplier_id, state
FROM lumber_reception
WHERE purchase_id IS NULL 
  AND manual_po_name IS NOT NULL 
  AND manual_po_name != '';

-- Q7: Lotes con reception_type = 'raw' y purchase_order_id NULL
SELECT COUNT(*) AS total
FROM stock_lot
WHERE reception_type = 'raw' 
  AND purchase_order_id IS NULL;

-- Q8: Lotes donde reception_id.purchase_id != lot.purchase_order_id (desincronización)
SELECT sl.id, sl.name, sl.reception_id, sl.purchase_order_id AS lot_po,
       lr.purchase_id AS reception_po
FROM stock_lot sl
JOIN lumber_reception lr ON sl.reception_id = lr.id
WHERE sl.purchase_order_id != lr.purchase_id
   OR (sl.purchase_order_id IS NULL AND lr.purchase_id IS NOT NULL)
   OR (sl.purchase_order_id IS NOT NULL AND lr.purchase_id IS NULL);
```

---

## VII. Conclusiones y Precondiciones para Homologación

### 1. Gap real mínimo a cerrar para que `lumber_reception` tenga el mismo nivel de trazabilidad de OC que `guia_processing`

El gap es **mínimo**. Ambos módulos ya comparten:
- Campo `oc_reference_raw` para preservar la referencia documental
- Campo `oc_match_status` para trazabilidad del matching
- Método de matching automático por nombre normalizado
- Lógica de normalización de OC compartida (`normalize_po_key`/`normalize_po_display`)

La **única diferencia material** que queda es:
- **`guia_processing` escribe `purchase_order_id` directamente en el vals del lote** (línea 3272 de `_create_or_get_lot`)
- **`lumber_reception` NO lo hace** (reception_service.py:46-64 — `lot_vals` sin `purchase_order_id`)

Cerrar este gap requiere **una sola línea adicional** en `create_lots_from_staging`:
```python
lot_vals['purchase_order_id'] = reception.purchase_id.id if reception.purchase_id else False
lot_vals['supplier_id'] = reception.supplier_id.id if reception.supplier_id else False
```

### 2. Qué existe ya en el código que puede reutilizarse sin duplicar

- ✅ `oc_reference_raw` + `oc_match_status` en ambos modelos — estructura idéntica
- ✅ `_match_reception_purchase_order` y `_match_purchase_order` — mismo patrón
- ✅ `normalize_po_key` / `normalize_po_display` en `reception_parser.py` — usado por ambos
- ✅ `_compute_purchase_info` en `stock_lot.py` — ya resuelve ambas ramas (reception + guia)
- ✅ `ingestion_source_ref` en `purchase.order` — trazabilidad de origen
- ✅ `madenat.lumber.purchase.intake` como AbstractModel — base para unificación futura

### 3. Riesgo de romper flujos funcionales si se homologa

**Riesgo BAJO.** Los cambios necesarios son aditivos (agregar campos al dict `lot_vals`), no sustractivos. No se modifica ninguna lógica de matching existente. La defensa en profundidad (compute + escritura directa) solo mejora la robustez.

Puntos de atención:
- Si `reception.purchase_id` es `False`, `purchase_order_id` será `False` (igual que ahora vía compute)
- La escritura directa en `lot_vals` no interfiere con el compute `_compute_purchase_info` — este último re-evalúa y sobrescribiría si es necesario (el compute tiene prioridad sobre la escritura directa porque se ejecuta después en la transacción)
- Agregar `supplier_id` al `lot_vals` de `create_lots_from_staging` podría generar conflicto con la asignación en `_compute_purchase_info` — **verificar orden de ejecución**

### 4. Tres acciones de mayor ROI (menor riesgo, mayor ganancia de trazabilidad)

| # | Acción | ROI | Riesgo | Esfuerzo |
|---|---|---|---|---|
| 1 | Agregar `purchase_order_id` y `supplier_id` al `lot_vals` en `create_lots_from_staging` | ALTO — cierra la brecha principal de trazabilidad | BAJO — cambio aditivo de 2 líneas | MÍNIMO |
| 2 | Unificar `_find_po_and_supplier` (purchasing) con `_find_or_create_po_intelligent` (core) — actualmente hay dos implementaciones divergentes no conectadas | MEDIO — elimina código muerto y confusión | MEDIO — requiere verificar que `_find_po_and_supplier` no se llama desde otro flujo | MEDIO |
| 3 | Agregar `purchase_id` a los `@api.depends` de `_compute_purchase_info` en `stock_lot` para que los cambios tardíos en `reception_id.purchase_id` disparen el compute | ALTO — corrige brecha de sincronización | BAJO — solo se agrega una dependencia | MÍNIMO |

---

## Apéndice: Snippets de Código Clave

### A.1 — `_find_or_create_po_intelligent` (lumber_reception.py:2253-2404)

```python
def _find_or_create_po_intelligent(self, dg_data, oc_data):
    self.ensure_one()
    parser = self.env['madenat.reception.parser']
    
    supplier_rut = (dg_data.get('supplier_rut') or '').strip()
    po_ref_raw = dg_data.get('po_ref') or ''
    
    # Fallback desde PDF de OC
    if not po_ref_raw and oc_data:
        po_ref_raw = oc_data.get('po_ref_fallback') or ''
    
    po_ref = parser.normalize_po_display(po_ref_raw)
    po_key = parser.normalize_po_key(po_ref_raw)
    
    # Persistir referencia documental (NUNCA sobrescribir)
    if po_ref and not self.oc_reference_raw:
        self.write({'oc_reference_raw': po_ref})
    
    if not po_key:
        raise UserError("⚠️ No se detectó referencia de OC en el PDF...")
    if not supplier_rut:
        raise UserError("⚠️ No se detectó RUT del proveedor en el PDF...")
    
    # Gestión de proveedor...
    supplier = self.env['res.partner'].search([('vat', '=', supplier_rut)], limit=1)
    # ...
    
    # Búsqueda de OC
    candidate_pos = self.env['purchase.order'].search([
        ('partner_id', '=', supplier.id),
        ('state', 'in', ['draft', 'sent', 'to approve', 'purchase', 'done'])
    ])
    po = candidate_pos.filtered(
        lambda p: parser.normalize_po_key(p.partner_ref or '') == po_key
            or parser.normalize_po_key(p.name or '') == po_key
    )[:1]
    
    if po:
        self.write({
            'purchase_id': po.id,
            'supplier_id': supplier.id,
            'oc_match_status': 'single_match',
            'oc_match_note': f'Auto-match exacto por nombre con {po.name}.',
        })
        return po, supplier
    
    # 🛑 PATCH 2026-06-18: DESACTIVADA autocreación automática.
    # Fallback manual
    self.write({
        'state': 'processing',
        'purchase_id': False,
        'manual_po_name': po_ref,
        'supplier_id': supplier.id,
        'oc_match_status': 'not_found',
        'oc_match_note': f'OC {po_ref} no encontrada...',
    })
    return None, supplier
```

### A.2 — `create_lots_from_staging` (reception_service.py:46-64) — NÓTESE AUSENCIA de `purchase_order_id`

```python
lot_vals = {
    'name': lot_name,
    'ref': lot_name,
    'product_id': product_id,
    'reception_id': reception.id,
    'subproducto_id': line.subproduct_id.id if line.subproduct_id else False,
    'piezas': line.pieces,
    'espesor_mm': line.thickness,
    'ancho_mm': line.width,
    'largo_m': line.length,
    'volume_purchase_m3': line.vol_purchase_m3,
    'volumen_m3': line.vol_purchase_m3,
    'vol_shipment_m3': line.vol_shipment_m3,
    'espesor_inch_frac': line.thickness_visual or '',
    'ancho_inch_frac': line.width_visual or '',
    'thickness_visual': line.thickness_visual or '',
    'width_visual': line.width_visual or '',
    'length_ft': line.length_input_raw if line.lengthuom == 'ft' else False,
}
# ⚠️ NO INCLUYE: purchase_order_id, supplier_id
```

### A.3 — `_compute_purchase_info` (stock_lot.py:839-866)

```python
@api.depends('reception_id', 'guia_processing_id')
def _compute_purchase_info(self):
    for lot in self:
        lot.purchase_order_id = False
        lot.supplier_id = False
    
    existing_lots = self.filtered(lambda l: l.id)
    if not existing_lots:
        return
    
    try:
        # PRIORIDAD: Guía de procesamiento
        for lot in existing_lots.filtered(lambda l: l.guia_processing_id and l.guia_processing_id.order_id):
            lot.purchase_order_id = lot.guia_processing_id.order_id
            lot.supplier_id = lot.guia_processing_id.order_id.partner_id
        
        # FALLBACK: Recepción directa
        remaining_lots = existing_lots.filtered(lambda l: not l.purchase_order_id)
        for lot in remaining_lots.filtered(lambda l: l.reception_id):
            if lot.reception_id.purchase_id:
                lot.purchase_order_id = lot.reception_id.purchase_id
            lot.supplier_id = lot.reception_id.supplier_id or (...)
    except Exception as e:
        _logger.warning("Error en _compute_purchase_info: %s", str(e))
```

### A.4 — `_create_or_get_lot` — escritura directa de OC en guia_processing (línea 3268-3272)

```python
# ═══════════════════════════════════════════════════════
# CAMPOS OPCIONALES (Solo si existen)
# ═══════════════════════════════════════════════════════
if purchase_order:
    vals['purchase_order_id'] = purchase_order.id
```

### A.5 — `_find_po_and_supplier` en purchasing (línea 84-90) — limpia `manual_po_name`

```python
if po:
    self.write({
        'purchase_id': po.id,
        'supplier_id': supplier.id,
        'oc_match_status': 'singlematch',
        'oc_match_note': f'Auto-match por nombre contra PO {po.name}',
        'manual_po_name': False,   # ← SE LIMPIA
    })
```

### A.6 — `oc_reference_raw` y `oc_match_status` en lumber_reception (línea 1132-1155)

```python
# ══════════════════════════════════════════════════════════════════════════════
# 🏷️ TRAZABILIDAD DOCUMENTAL DE OC (Patch 2026-06-18)
# Separación referencia documental vs vínculo operativo.
# oc_reference_raw NUNCA se sobrescribe al vincular una purchase.order.
# ══════════════════════════════════════════════════════════════════════════════
oc_reference_raw = fields.Char(
    string="OC Documental",
    readonly=True,
    copy=False,
    tracking=True,
    help="Referencia documental de OC extraída desde la guía/PDF. Nunca se sobrescribe."
)
oc_match_status = fields.Selection([
    ('not_found', 'No encontrada'),
    ('single_match', 'Coincidencia exacta'),
    ('multi_match', 'Múltiples coincidencias'),
    ('manual', 'Vinculación manual'),
    ('created', 'Creada desde recepción'),
], string="Estado Match OC", default='not_found', tracking=True, copy=False)
oc_match_note = fields.Text(
    string="Nota de Match OC",
    copy=False,
    help="Bitácora de reconciliación de OC."
)
```

---

**FIN DEL INFORME**