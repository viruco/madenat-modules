# DISENO_CAMBIO — Mejora mínima de búsqueda de Intake

Alcance aprobado: (1) OC documental vs OC vinculada (columna/búsqueda/agrupación
coherentes); (2) significado real de Fecha; (3) diferenciar modalidad
Producto/Procesado/Volúmenes; (4) propuesta mínima de Producto real y Procesador.
Sin ACL, ingesta, stock, CANON ni datos. No se altera `id` ni `source_res_id`.

Categorías: **A**=solo XML · **B**=campo ya disponible · **C**=existe en origen pero no en Consola (extensión acotada).

## 1. OC documental vs OC vinculada (A + B/C)

**Hallazgo corregido:** la columna/búsqueda "OC documento" (`purchase_reference`)
mostraba `COALESCE(po.name, oc_reference_raw)` (Producto: prioriza `purchase_id.name`),
y la agrupación "OC" agrupaba por `purchase_id` (vacío en las 18 filas) → grupo vacío.

**Cambio:**
- **Nueva columna real `oc_documental`** en la vista SQL = `NULLIF(<origen>.oc_reference_raw,'')`
  (Producto y Procesado). Se almacena **NULL** cuando no hay referencia → los dominios
  `= False` / `!= False` funcionan como en Odoo.
- **Campo** `oc_documental` (Char, readonly) en el modelo. Columna, búsqueda y
  agrupación leen el **mismo dato**.
- **Lista:** "OC documental" = `oc_documental` (ya no `purchase_reference`).
- **Búsqueda:** `<field name="oc_documental"/>` + `purchase_id` ("OC vinculada").
- **Agrupaciones:** "OC documental" (`group_by oc_documental`) y "OC vinculada" (`group_by purchase_id`).
- **Filtros de estado OC** (XML puro sobre columnas reales):
  `OC vinculada` `[('purchase_id','!=',False)]`,
  `OC pendiente de vinculación` `[('purchase_id','=',False),('oc_documental','!=',False)]`,
  `OC no indicada` `[('purchase_id','=',False),('oc_documental','=',False)]`.
- **Se conserva** `purchase_reference` y los proxies `oc_reference_documental`/
  `oc_documentary_status`/`oc_pending` (no se rompe nada; test existente intacto).

## 2. Significado real de Fecha (A + B)

`guide_date` es heterogénea: Producto = `COALESCE(guia_fecha, reception_date::date)`;
Procesado/Volumen = `date_emission`.

**Cambio:**
- **Nueva columna real `guide_date_kind`** (text): `'emission'` (fecha documental de
  emisión; Procesado y Producto con `guia_fecha`) / `'reception'` (Producto sin
  `guia_fecha`, fecha de recepción).
- **Campo** `guide_date_kind` (Selection, readonly) + `help` en `guide_date`.
- **Lista/form:** "Fecha" → **"Fecha de guía"**; se muestra "Origen de fecha" en el
  bloque Documento (Volumen).
- **Agrupación** "Fecha de guía" (`guide_date:day`) y "Origen de fecha" (`guide_date_kind`).
- **Lista:** se añadió la columna **"Origen fecha"** (`guide_date_kind`, badge) para que
  la distinción **Emisión (documento) vs Recepción (sistema)** sea **visible fila a fila**
  (no se depende solo del `help`). Cubierto por `test_10_lista_muestra_origen_de_fecha`.
- No se hardcodean fechas; se conserva el orden `guide_date desc, id desc`.

## 3. Diferenciar modalidad Producto / Procesado / Volúmenes (A)

- Los tres filtros tienen **dominios disjuntos** (`ingestion_type`), es decir, cada
  ingreso cae en exactamente uno de los tres.
- **CORRECCIÓN IMPORTANTE (verificada en aislamiento):** los filtros **NO son
  mutuamente excluyentes en la UI**. El usuario **puede marcar varios a la vez**; Odoo
  los combina por **AND**, de modo que marcar dos modalidades distintas produce
  **intersección vacía (0 resultados)**. La verificación aislada
  `test_09_combinacion_modalidad_por_and` confirma este comportamiento (producto∧volumen = 0).
- **LIMITACIÓN DE PLATAFORMA:** el RNG de Odoo 18 **no admite `group=` en `<filter>`**,
  así que NO se pueden forzar como "radio" (`<rng:attribute name="group">` solo existe
  en `<field>`). Por eso se mantienen como toggles independientes. Ver `LIMITES.md`.
- Se añaden filtros de estado que antes no existían: **"Procesada (legacy)"**
  (`state='processed'`) y **"Error"** (`state='error'`), cubriendo estados huérfanos.

## 4. Producto real — búsqueda sin duplicar ni elegir el primero (C, mínima)

Reutiliza las relaciones existentes `lumber.reception.line.product_id` /
`madenat.guia.processing.line.product_id`.

- **Campo de solo búsqueda** `product_filter_id` (Many2one product.product, `store=False`)
  con `search='_search_product_filter_id'`. El `search` devuelve un dominio sobre
  `(source_model, source_res_id)` para los ingresos cuyas **líneas contienen** el
  producto. **No hay JOIN en la vista SQL** → no multiplica filas ni pierde registros.
- **No** se elige el primer producto: el valor mostrado (`_compute_product_filter_id`)
  replica el producto común (`product_id`) y queda **vacío** si las líneas difieren.

## 5. Procesador — relación existente, sin usar el proveedor (C, mínima)

- **Columna real `processor_id`** en la vista SQL: para Procesado/Volumen,
  `tpo.processor_id` con `LEFT JOIN toll_processing_order tpo ON tpo.id = gp.toll_order_id`
  (relación **1:1** → no multiplica filas). Para Producto, `NULL`.
- **Campo** `processor_id` (Many2one res.partner, readonly) → búsqueda y agrupación nativas.
- **Nunca** se usa `partner_id`/`supplier_id` como procesador.

## 6. Volúmenes — NO implementado (decisión)

No se añade búsqueda numérica de volumen. Campo oficial identificado para una fase
posterior: **`official_volume_m3`** (jerarquía PDF>Excel>Packing; expuesto como
`official_volume_effective_m3`), **unidad m³**. No se expone hasta aprobación.

## 7. Archivos modificados (workcopy)

| Archivo | Cambio |
|---|---|
| `madenat_lumber_intake/models/intake_console.py` | +3 campos reales (oc_documental, guide_date_kind, processor_id), + `product_filter_id` (search), + `init()` (3 columnas y LEFT JOIN 1:1) |
| `madenat_lumber_intake/views/intake_console_views.xml` | lista, form y vista de búsqueda (campos, filtros, agrupaciones) |
| `madenat_lumber_intake/tests/test_search_console_oc_fecha_modality.py` | nuevo (10 pruebas) |
| `madenat_lumber_intake/tests/__init__.py` | registrar el test |

## 8. Pruebas de impacto (resumen; detalle en `RESULTADOS_PRUEBAS.md`)

10 pruebas nuevas (OC documental/vinculada, Fecha, modalidad, producto real,
procesador, incompletos+usuario operativo+navegación, sin duplicación) +
56 de regresión = **66 tests, 0 failed, 0 errors**.
