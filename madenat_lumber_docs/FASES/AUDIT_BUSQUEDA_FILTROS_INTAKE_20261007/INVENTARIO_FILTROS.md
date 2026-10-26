# INVENTARIO_FILTROS — Vista de búsqueda de "Ingreso de Madera"

**Acción:** `madenat_lumber_intake.action_madenat_lumber_intake_console` (id 802, name="Ingreso de Madera")
**Modelo:** `madenat.lumber.intake.console` (vista SQL, `_auto=False`)
**Vista lista:** `view_madenat_lumber_intake_console_list` (id 1865)
**Vista de búsqueda:** `view_madenat_lumber_intake_console_search` (id 1866) — **primary, sin herencias**
**Menú:** `menu_madenat_lumber_intake_wizard` (id 500, "Ingreso de Madera"), grupo `group_madenat_operaciones`

**Verificación de arquitectura efectiva:** el `arch_db` servido de la vista 1866 es **idéntico** al XML fuente; `ir_ui_view` no muestra ninguna vista con `inherit_id` sobre 1866 → **no hay herencias**. La acción no define `domain` ni `context` (context = `{}`), y **no hay `search_default_*`**. `ir_filters` para este modelo = **0 filas** → **ningún filtro guardado influye en la sesión**.

> Origen de cada columna de la vista SQL (`init()` de `intake_console.py:513`): Producto ← `lumber_reception`; Procesado/Volúmenes ← `madenat_guia_processing`.

---

## 1. Campos de búsqueda directa (barra "Buscar")

| # | Etiqueta | XML ID / name | Dominio/Contexto | Campo | Tipo de campo | Origen real | Resultado esperado | Resultado observado |
|---|---|---|---|---|---|---|---|---|
| F-01 | Guía | `field name="guide_name"` | búsqueda textual | `guide_name` | Char (columna) | `lr.name` / `gp.name` | Buscar por N° de guía | Coincide (texto). OK |
| F-02 | Proveedor | `field name="partner_id"` | búsqueda relacional | `partner_id` | Many2one `res.partner` (columna) | `lr.supplier_id` / `gp.partner_id` | Buscar por proveedor | Coincide, **pero** para Procesado `gp.partner_id` está rotulado en el core "Proveedor / Transportista" (emisor de la guía), no necesariamente el procesador. Ver H-06. |
| F-03 | **OC documento** | `field name="purchase_reference" string="OC documento"` | búsqueda textual | `purchase_reference` | Char (columna) | Producto: `lr.purchase_order` (compute: `purchase_id.name` -> `manual_po_name` -> `oc_reference_raw` -> `'SIN ORDEN'`). Procesado: `COALESCE(po.name, gp.oc_reference_raw, '')` | Buscar la **referencia documental de OC** | **ENGANOSO**: cuando hay OC vinculada muestra el **nombre de la OC vinculada**, no la referencia del documento. Ver H-01. |
| F-04 | OC vinculada | `field name="purchase_id" string="OC vinculada"` | búsqueda relacional | `purchase_id` | Many2one `purchase.order` (columna) | `lr.purchase_id` / `gp.order_id` | Buscar la OC interna vinculada | Coincide, pero hoy **0 de 18** filas tienen vinculo. Ver H-02. |
| F-05 | Referencia | `field name="display_reference"` | búsqueda textual | `display_reference` | Char (columna) | `'Recepcion '||lr.name` / `'Procesada '||gp.name` | Referencia legible | Informativo; no es un dato de negocio buscable. |

---

## 2. Filtros — modalidad de ingesta

| # | Etiqueta | XML ID | Dominio (fuente) | Campo | Tipo | Origen real | Esperado | Observado (madenat_test 2026-10-07) |
|---|---|---|---|---|---|---|---|---|
| T-01 | Producto | `type_product` | `[('ingestion_type','=','product')]` | `ingestion_type` | Selection/columna | Literal SQL `'product'` (rama `lumber_reception`) | Recepciones de Producto / Madera Bruta | **7 filas** OK (todas en `state=verified`) |
| T-02 | Procesado | `type_processed` | `[('ingestion_type','=','processed')]` | `ingestion_type` | columna | `'processed'` (guia `madenat.guia.processing` **con `tipo_recepcion <> 'granel'`**) | Guias Procesadas / Servicios | **6 filas** OK (5 `service` + 1 `compra`) |
| T-03 | Volumenes | `type_volume` | `[('ingestion_type','=','volume')]` | `ingestion_type` | columna | `'volume'` <=> `gp.tipo_recepcion='granel'` | Guias de Ingreso por Volumenes | **5 filas** OK |

> **Nota semantica:** "Procesado" (T-02) **excluye** a "Volumenes" (T-03) porque el SQL clasifica como `volume` toda guia `granel`. Un ingreso por volumen **no** aparece al filtrar "Procesado". Es correcto por diseno, pero el rotulo "Procesado" puede leerse como "todo lo procesado".

---

## 3. Filtros — estado

| # | Etiqueta | XML ID | Dominio | Campo | Origen real | Esperado | Observado |
|---|---|---|---|---|---|---|---|
| S-01 | Borrador | `filter_state_draft` | `[('state','=','draft')]` | `state` | `lr.state` / `gp.state` (con `cancelled`->`cancel`) | Registros en borrador | **1 fila** (volume) |
| S-02 | Verificado | `filter_state_verified` | `[('state','=','verified')]` | `state` | ambos origenes tienen `verified` | Registros verificados | **10 filas** |
| S-03 | **Recibido** | `filter_state_done` | `[('state','=','done')]` | `state` | **solo `lumber.reception`** tiene `done`; `madenat.guia.processing` **no** tiene `done` | Recepciones recibidas | **0 filas** en la base; y por diseno **nunca** aplica a Procesado/Volumenes. Ver H-08. |
| S-04 | **Validado** | `filter_state_validated` | `[('state','=','validated')]` | `state` | **solo `madenat.guia.processing`** tiene `validated`; `lumber.reception` **no** tiene `validated` | Guias validadas | **7 filas** (5 processed + 2 volume); **nunca** aplica a Producto. Ver H-08. |
| S-05 | Cancelado | `filter_state_cancelled` | `[('state','=','cancel')]` | `state` | `cancel` (product) / `cancelled`->`cancel` (guia) | Registros cancelados | **0 filas** |

### Combinados abierto/cerrado

| # | Etiqueta | XML ID | Dominio | Observado |
|---|---|---|---|---|
| C-01 | Abiertos | `filter_open` | `[('state','in',('draft','processing','verified','pending_link'))]` | **11 filas** |
| C-02 | Finalizados | `filter_done` | `[('state','in',('done','validated'))]` | **7 filas** |

> **Estados que quedan sin cobertura:** la guia `state='processed'` ("Procesada (legacy)", en la seleccion del modelo `state`) y `state='error'` (Producto) **no** caen en ningun filtro especifico de estado ni en C-01/C-02. Ver H-08.


---

## 4. Agrupaciones ("Agrupar por")

| # | Etiqueta | XML ID | Contexto | Campo | Tipo | Origen real | Esperado | Observado |
|---|---|---|---|---|---|---|---|---|
| G-01 | **OC** | `group_purchase` | `{'group_by':'purchase_id'}` | `purchase_id` | Many2one `purchase.order` (columna) | `lr.purchase_id` / `gp.order_id` | Agrupar por Orden de Compra | **TODAS las 18 filas caen en el grupo vacio "(No definido)"** porque **0 tienen `purchase_id`**, mientras la columna "OC documento" **si** muestra referencias. Ver H-02 (caso central). |
| G-02 | Proveedor | `group_partner` | `{'group_by':'partner_id'}` | `partner_id` | Many2one `res.partner` | `lr.supplier_id` / `gp.partner_id` | Agrupar por proveedor | Funciona (todas las filas tienen `partner_id`). OK |
| G-03 | Fecha | `group_date` | `{'group_by':'guide_date:day'}` | `guide_date` | Date (columna) | Producto: `COALESCE(lr.guia_fecha, lr.reception_date::date)`; Procesado/Volumen: `gp.date_emission` | Agrupar por fecha (dia) | Funciona, **pero la semantica de `guide_date` es heterogenea entre origenes**. Ver H-04. |
| G-04 | Tipo | `group_type` | `{'group_by':'ingestion_type'}` | `ingestion_type` | columna (`product`/`processed`/`volume`) | Literal SQL | Agrupar por modalidad | Funciona (3 grupos). OK |
| G-05 | Estado | `group_state` | `{'group_by':'state'}` | `state` | Selection/columna | Estado homologado del origen | Agrupar por estado | Funciona. OK |

---

## 5. Ausencias relevantes (controles que NO existen)

| Elemento ausente | Que se querria | Estado del dato |
|---|---|---|
| Filtro/agrupacion por **Producto real** | "Producto" del ingreso (T-01 es modalidad, no producto) | `product_id` existe en la consola **pero `store=False`** (compute) y solo en el form -> **no filtrable/agrupable**. Ver H-05. |
| Filtro/agrupacion por **Procesador** | Quien proceso (planta externa) | No hay campo en la consola. El dato real vive en `toll.processing.order.processor_id` y `res.partner.is_processor`. Ver H-06. |
| Filtro/agrupacion por **Volumen (numerico)** | Rangos de m3 declarado/calculado | Volumenes son `store=False` (compute) -> **no consultables**. Ver H-07. |
| Filtro por **Revision** (`review_state`) | Listo para stock / Requiere revision / Pendiente documental | `review_state` es `store=False` (compute) -> **no filtrable/agrupable** pese a mostrarse en la lista. Ver H-09. |
| Filtro por **OC documental / estado OC** (`oc_documentary_status`) | Vinculada / Pendiente / No indicada | `store=False` (compute) -> **no filtrable/agrupable**. Ver H-01/H-02. |

---

## 6. Combinacion de filtros (comportamiento)

- Todos los filtros de estado y modalidad son **toggles independientes** (no definen atributo `group`), por lo que Odoo los compone por **AND**. Seleccionar simultaneamente **"Producto" + "Procesado"** produce `ingestion_type='product' AND ingestion_type='processed'` -> **interseccion vacia** (0 resultados), no una union.
- Cruzar modalidad y estado (p. ej. **Producto + Verificado**) si es coherente y devuelve la interseccion.
- El dominio final efectivo de cada filtro esta **aislado por categoria** (cada boton aporta un unico criterio); no hay OR implicito entre botones de la misma columna.
- *Pendiente de confirmacion en navegador (V3):* comportamiento visual exacto de seleccion multiple en el panel de filtros. Ver `PLAN_PRUEBAS.md`.

