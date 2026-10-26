# MAPA_CAMPOS_Y_ORIGENES — De la etiqueta visible al dato real

**Vista SQL:** `madenat_lumber_intake_console` (creada por `intake_console.py::init()`, `madenat_lumber_intake`).
**Fuentes:** `lumber_reception` (rama Producto) UNION ALL `madenat_guia_processing` (ramas Procesado/Volumen).
**Id sintético:** `id = lr.id` (Producto) / `id = 900000000 + gp.id` (Procesado/Volumen, `CONSOLE_ID_OFFSET`).

---

## 1. Mapa columna SQL → campo del origen → significado

| Columna vista (etiqueta UI) | Producto → `lumber_reception` | Procesado/Volumen → `madenat_guia_processing` | Significado real |
|---|---|---|---|
| `id` | `lr.id` | `900000000 + gp.id` | Identidad única de la fila de consola (no es `id` de negocio) |
| `source_model` / `source_res_id` | `'lumber.reception'` / `lr.id` | `'madenat.guia.processing'` / `gp.id` | Trazabilidad al registro origen (`action_open_source`) |
| `ingestion_type` ("Tipo") | `'product'` (literal) | `'volume'` si `tipo_recepcion='granel'`, si no `'processed'` | **Modalidad de ingesta**, no producto |
| `guide_name` ("Guía") | `lr.name` | `gp.name` | N° de guía/documento |
| `guide_date` ("Fecha") | `COALESCE(lr.guia_fecha, lr.reception_date::date)` | `gp.date_emission` | Fecha (semántica mixta — ver §3) |
| `partner_id` ("Proveedor") | `lr.supplier_id` | `gp.partner_id` (core: "Proveedor / Transportista") | Emisor/proveedor del documento (no el procesador) |
| `purchase_id` ("OC vinculada") | `lr.purchase_id` | `gp.order_id` | OC interna **vinculada** (Many2one `purchase.order`) |
| `purchase_reference` ("OC documento") | `lr.purchase_order` (compute) | `COALESCE(po.name, gp.oc_reference_raw, '')` | **Texto de OC mostrado** (mezcla vínculo + documento — ver §2) |
| `state` ("Estado") | `lr.state` | `gp.state` con `cancelled`->`cancel` | Estado del origen, homologado |
| `display_reference` ("Referencia") | `'Recepción '||lr.name` | `'Procesada '||gp.name` | Referencia legible |

### Columnas que la vista SQL NO tiene (y por eso no son consultables)

`product_id`, `subproduct_id`, `oc_reference_documental`, `oc_documentary_status`, `review_state`, `total_volume_m3`, `official_volume_effective_m3`, `declared_lines_volume_m3`, `volume_operational_m3`, `packing_*`, `total_amount`, `*_lines_*`. Todas son **campos compute `store=False`** del modelo de consola → existen en el ORM (form), pero **no** son columnas de la vista → **no se pueden buscar, filtrar ni agrupar con el mecanismo nativo**.

---

## 2. OC: documento vs vinculada (dos conceptos, un rótulo)

| Concepto | Dónde vive | Campo | Uso en la consola |
|---|---|---|---|
| **OC documental** (referencia extraída del PDF/Excel, "nunca se sobrescribe") | `madenat.guia.processing.oc_reference_raw` ("OC Documental") y `lumber.reception.oc_reference_raw` | `oc_reference_raw` (Char, readonly, tracking) | Proyectada como proxy `oc_reference_documental` (compute, lee **solo** `oc_reference_raw`). **NO forma columna SQL.** |
| **OC vinculada** (relación operativa a una `purchase.order`) | `lr.purchase_id` / `gp.order_id` | Many2one `purchase.order` | Columna `purchase_id` + agrupación "OC" (G-01). |
| **Texto mostrado en la columna "OC documento"** | `lr.purchase_order` / `COALESCE(po.name, gp.oc_reference_raw,'')` | columna `purchase_reference` | **Mezcla**: prioriza el nombre de la OC vinculada sobre la referencia documental. |

Doctrina aplicable: `madenat_guia_processing.oc_reference_raw` "NUNCA se sobrescribe al vincular una `purchase.order`" (`madenat_guia_processing.py:643`). Sin embargo, la vista SQL (`intake_console.py:528,545`) **`COALESCE` hacia `po.name`**, de modo que la etiqueta "OC documento" puede mostrar el **nombre de la OC vinculada**.

**Evidencia en la base activa (2026-10-07, 18 filas):**

- Filas con `purchase_id` (OC vinculada): **0**.
- Filas con referencia documental y **sin** vínculo ("pending"): **15**.
- Filas sin OC informada ("not_informed"): **3**.
- Ejemplos de `purchase_reference` mostrado: `MC - 2506 - 01`, `MC - 1106 - 11`, `OC 9000`, `UAT-INT-20261004-OC-CORREGIDA`, `OC - 90001 - 123`.

**Consecuencia:** la agrupación "OC" (G-01, `group_by purchase_id`) devuelve **un único grupo vacío** para las 18 filas, mientras la columna "OC documento" muestra 15 referencias. Es exactamente el caso "agrupar por un campo vacío mientras la columna muestra otro dato".

---

## 3. Fecha: qué mide `guide_date`

| Origen | Expresión SQL | Semántica |
|---|---|---|
| Producto (`lumber_reception`) | `COALESCE(lr.guia_fecha, lr.reception_date::date)` | **Fecha de emisión de la guía** si existe (`guia_fecha`, `lumber_reception.py:1087`); si no, **fecha/hora de recepción truncada a día** (`reception_date`, Datetime `:1101`) |
| Procesado/Volumen (`madenat.guia.processing`) | `gp.date_emission` | **Fecha de emisión de la guía** (`date_emission`, Date `:626`, default hoy) |

**No es una única "Fecha":**
- Producto puede mostrar fecha de recepción (operativa) cuando falta la fecha documental; Procesado siempre muestra la fecha documental de emisión.
- Producto usa una fuente **Datetime** (truncada); Procesado una **Date** pura → no hay zona horaria aplicada salvo el `::date`.
- La agrupación "Fecha" (G-03) usa `guide_date:day` (día), compatible con Date. El rango nativo del panel funciona sobre `guide_date`.

---

## 4. Producto: modalidad vs producto real vs productos de línea

| Concepto | Dónde vive | Campo | En la consola |
|---|---|---|---|
| A. "Producto" como **modalidad** | `ingestion_type='product'` | columna SQL | Filtro "Producto" (T-01). **No es un producto.** |
| B. **Producto real de cabecera** | `product_id` del producto común a todas las líneas | `intake_console.product_id` (compute `_compute_header_product_id`, `store=False`, `intake_console.py:1424`) | Se **muestra en el form** ("Resumen del ingreso"), **NO** es columna SQL → **no buscable/agrupable**. Muestra valor **solo si TODAS las líneas comparten el mismo `product_id`**; si hay mezcla queda vacío. |
| C. **Productos de las líneas** | `lumber.reception.line.product_id` (`lumber_reception.py`), `madenat.guia.processing.line.product_id` (`madenat_guia_processing.py:80`) | líneas | No expuestos como filtro; sí en el detalle de packing (Many2many compute `product_packing_line_ids` / `processed_packing_line_ids`, `store=False`). |

**Riesgo señalado en el enunciado:** no elegir el primer producto de las líneas como representativo del ingreso; no multiplicar filas de la consola. La consola **ya evita** esto: `_compute_header_product_id` exige coincidencia total (si no, vacío) y el detalle es Many2many compute (no multiplica filas de la vista SQL). Cualquier búsqueda por producto real debería hacerse **sobre las líneas** o sobre un campo de cabecera **sin duplicar** filas de consola.

---

## 5. Procesador vs "Procesado"

| Concepto | Dónde vive | Campo | En la consola |
|---|---|---|---|
| "Procesado" **modalidad** | `ingestion_type='processed'` | columna SQL | Filtro "Procesado" (T-02). **No dice quién procesó.** |
| **Procesador** (planta externa: cepillado/secado/tratamiento) | `res.partner.is_processor` (maestro de partners); `toll.processing.order.processor_id`; `madenat.sv.imputation.processor_id` | `is_processor` (Boolean), `processor_id` (Many2one), `processor_location_id` | **No existe** en la consola. |
| Enlace guía→orden de proceso | `madenat.guia.processing.toll_order_id` → `toll.processing.order` (`guia_processing_integration.py:15`) | `toll_order_id.processor_id` | No expuesto en la consola. |
| `partner_id` de la consola | `gp.partner_id` (core: "Proveedor / Transportista") | Many2one | **No es el procesador** por definición de campo. Puede coincidir con el procesador cuando hay orden toll (onchange `_onchange_toll_order` copia `processor_id` a `partner_id`), pero **no es evidencia** de ese rol. |

Doctrina: `CANON/19_IMPUTACION_SV_Y_PROCESADORES.md §2` ("Procesador = planta externa... se marca en el maestro de partners, `res.partner.is_processor`"); AD-87/AD-89/AD-90 (ubicación interna `Procesadores/<X>`, saldo por procesador).

**Conclusión:** no usar `partner_id`/`supplier_id` como procesador sin evidencia. El procesador **no** está disponible como dato de búsqueda hoy (gap de tipo C/D).

---

## 6. Volúmenes: modalidad vs medida

| Concepto | Dónde vive | Campo | En la consola |
|---|---|---|---|
| A. Modalidad "Ingreso por Volúmenes" | `tipo_recepcion='granel'` -> `ingestion_type='volume'` | columna SQL | Filtro "Volúmenes" (T-03). El SQL incluye **exactamente** las guías `granel` de `madenat.guia.processing`. |
| B. Volumen **documental** (oficial de la guía) | `official_volume_m3` / volumen PDF-Excel-Packing | `madenat.guia.processing` | Proxy `official_volume_effective_m3` (compute `store=False`) en el form. **No** es columna SQL. |
| C. Volumen **calculado**/operativo | `total_volume_m3`, `volume_operational_m3`, `declared_lines_volume_m3` | compute del modelo consola | Solo form; `store=False`. |
| D. Otros volúmenes (NOMINAL/EXPORTACIÓN) | `stock.lot.volume_purchase_m3`, `vol_shipment_m3` (CANON/17) | stock.lot | Fuera de la consola. |

**No hay búsqueda numérica por volumen:** ningún campo de volumen es columna de la vista → no se puede filtrar `total_volume_m3 > X` ni agrupar por rangos con el mecanismo nativo. Distinguir volumen documental de calculado en búsqueda **no es posible hoy**. No se cambian cálculos ni conversiones (fuera de alcance).

---

## 7. Estados y traducción a la consola

| Fuente | Estados nativos | Traducción a la vista consola |
|---|---|---|
| `lumber.reception` (`lumber_reception.py:947`) | `draft, processing, verified, done, cancel, error, pending_link` | Igual (salvo que el modelo consola también declara `processed`/`validated`, que **product nunca usa**) |
| `madenat.guia.processing` (`madenat_guia_processing.py:617`) | `draft, verified, processed, validated, cancelled` | `cancelled` -> `cancel`; el resto igual |

**Selección `state` del modelo consola** (`intake_console.py:127`): `draft, processing, verified, done, validated, processed, cancel, error, pending_link` → es la **unión** de ambos orígenes. Consecuencia: un mismo rótulo de filtro ("Recibido"=`done`, "Validado"=`validated`) **solo** casa con uno de los dos orígenes.

| Microestado `review_state` (columna "Revisión") | Mapeo `_review_state_for_state` |
|---|---|
| Listo para stock (`ready`) | product `verified`; guia `verified`/`processed` |
| Enviado a stock (`sent`) | product `done`; guia `validated` |
| Requiere revisión (`needs_review`) | default (p. ej. `draft`, `processing`, `pending_link`) |
| Pendiente documental (`documental_pending`) | guia `processed` con todas las líneas documentales pendientes |
| Cancelado/Error/Sin origen | `cancel`/`error`/sin origen |

**"Estado" ≠ "Revisión":** la lista muestra **ambos** (`state` y `review_state`). Solo `state` es filtrable/agrupable; `review_state` es `store=False`.

