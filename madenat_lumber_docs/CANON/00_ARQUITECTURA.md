# Arquitectura — MADENAT Lumber Core

**Módulo:** `madenat_lumber_core`
**Versión documental:** `7.17.0`
**Fecha de actualización:** 2026-10-02  <!-- actualizado: 2026-10-02 — §4.3: reapertura no bloqueante y trazable de guía procesada (G1): wizard, reversión nativa del consumo BT-04, conservación de historia física e imputación de advertencias no bloqueantes. G2 (vínculo persistente guía↔picking, `stock.picking.guia_processing_id`) y G3 (retorno automático del ingreso de producción atribuido por esa llave fuerte) IMPLEMENTADOS (ver §4.3) -->
**Estado:** ✅ Vigente — Se documenta la Gestión Operativa de Etiquetas SV (`madenat.sv.operation`, AD-79) en §4.8, el flujo de recepción a granel + Balance de Masa + consolidación administrativa (AD-65, diseño aprobado, pendiente de implementación) en §4.6, R1 — Detalle por Patio con `stock.quant` extendido en `madenat_lumber_reports` (AD-77, Programación 1) en §4.7, la interfaz operativa oficial de Intake (AD-78) y el entorno de desarrollo del «Modo A autoservicio» (`madenat.dev_cleanup_enabled`, que desacopla el autoservicio de `--test-enable`) en §4.9. Con cambios de código (`madenat_lumber_core`, `madenat_lumber_intake`).
**Compatibilidad objetivo:** Odoo 18 CE

---

## 1. Propósito

Este módulo implementa el flujo operativo de MADENAT para:
- Ingesta de documentos (Excel, PDF) vía `lumber.reception` y `madenat.guia.processing`.
- Staging documental en `lumber.reception.line` antes de cualquier escritura en inventario.
- Análisis comercial, cálculo volumétrico y validación por gates (0–3 + GB-1).
- Persistencia controlada a `stock.lot` exclusivamente a través de Gate 3 (AD-04).

---

## 2. Posición funcional

El módulo no opera en un pipeline vertical estricto: actúa como **núcleo de ingesta y staging** que alimenta a los módulos de dominio.

- **Upstream:** `madenat_lumber_purchasing` extiende `purchase.order` y enriquece el contexto de compra.
- **Consumidores:** `madenat_lumber_logistics` (contenedores/embarques), `madenat_lumber_costing` (costeo), `madenat_lumber_billing` (facturación), `madenat_lumber_reports` (reportes).
- **Dependencia funcional documentada:** `madenat_lumber_shipping_core` define modelos de motonaves/viajes/reservas pero los menús los construye `madenat_lumber_logistics`. Si logistics no está instalado, shipping_core es invisible en la UI. `shipping_core/__manifest__.py` tiene `shipping_menus.xml` comentado con nota "ELIMINADO - Menús migrados a logistics". `shipping_core` no declara `depends` sobre `logistics` → dependencia funcional, no técnica. Documentado como riesgo M-R2 en `02_CONTINUIDAD.md` y formalizado en `04_DECISION_LOG.md` AD-37.

---

## 3. Estado real de la arquitectura

**Modular parcial.** Se han extraído componentes del monolito original pero `lumber_reception.py` (~3118 líneas) todavía concentra `LumberReceptionLine`, `LumberReception`, computes de staging y normalizaciones.

### 3.1 Archivos clave desacoplados

| Archivo | Responsabilidad |
|---|---|
| `ingestion_gate.py` | Gates 0–3: PreUpload, DocumentReconciliation, CommercialAnalysis, PreCommit |
| `reception_parser.py` | Dispatcher multi-formato (Excel por perfil, PDF, CSV) |
| `reception_service.py` | Escritura a `stock.lot` vía `LumberReceptionService._create_lots_from_packing()` |
| `reception_workflow.py` | Clase de orquestación de estados vía import inline (`from .reception_workflow import LumberReceptionWorkflow` en lumber_reception.py:2694). No es un mixin de herencia Odoo. |
| `validation_checklist_mixin.py` | Mixin de checklist de validación para líneas de ingesta |
| `mixin_lumber_ingest.py` | Mixin de cálculo volumétrico (regla de oro compartida) + `find_or_create_lumber_subproducto` (Fase 2) |
| `stock_lot.py` | Extensión de `stock.lot`: `vol_shipment_m3`, `_compute_estado_trazabilidad`, `_compute_processing_loss` |
| `stock_lot_cost_line.py` | Extensión de `stock.lot.cost.line` con cálculos de costeo |
| `stock_picking.py` | Extensión de `stock.picking` para recepciones de lumber |
| `stock_move.py` | Extensión de `stock.move` con trazabilidad de movimientos de lumber |
| `product_product.py` | Extensión de `product.product` con atributos comerciales de lumber |
| `utils_uom.py` | Constantes y conversiones volumétricas + utilidad de parseo de fracciones imperiales compartida (`parse_fraction_to_decimal_inch`, AD-41) |
| `width_mapping.py` | Tabla Rough→S2S + helper `get_s2s_adjustment()` |
| `core_utils.py` | ❌ CÓDIGO MUERTO — 0 referencias, fuera de `__init__.py` (confirmado 2026-07-08). No fue archivado por AD-39 (ese AD solo cubrió el método `_cleanup_orphan_moves`). |
| `product_template.py` | ❌ HUÉRFANO NO ARCHIVADO — extensión de `product.template` nunca desplegada, pendiente de mover a `_archive/` (confirmado 2026-07-08). |
| `madenat_ingestion_engine` (módulo hermano) | Motor de extracción/normalización de documentos de ingreso (Excel/PDF) agnóstico del destino. Consumido por `madenat_lumber_intake` (`extract_document()` para preview/perfil; `_extract_pdf_text()` para auto-clasificación Producto/Procesado). Estado verificado: `installed` en `madenat_test` (18.0.1.0.0). Gaps: extracción PDF solo cabecera por regex (tablas con layout configurable NO cubiertas); `ingestion_column_profile.py` es esqueleto de 4 campos sin layout. Ver AD-63. |

### 3.2 Modelos persistentes (Fase 2 + Fase 3 — AD-29, AD-30)

El runtime actual incluye modelos para reglas de ingesta parametrizables con UI de mantenimiento:

| Modelo | Propósito | AD |
|---|---|---|
| `lumber.blank.nominal.map` | Mapa físico→nominal blanks (8 registros) | AD-29 |
| `lumber.width.s2s.map` | Tabla Rough→S2S (15 registros) | AD-29 |
| `lumber.thickness.visual.rule` | Rangos espesor→visual (4 reglas) | AD-29 |
| `lumber.profile.subproduct.rule` | Reglas perfil↔subproducto (7 reglas) | AD-29 |
| `lumber.export.formula` | Fórmulas exportación por perfil (3 registros: f5085, f1550, metric) | AD-30 |
| `lumber.ingestion.format` | Formatos ingesta/parsing por perfil (4 registros) | AD-30 |
| `madenat.ingestion.config` | Helper AbstractModel con cadena de fallback de 3 niveles + `get_default_product()` | AD-29, AD-ING-001 |
| `madenat.lumber.product.default` | Producto maestro por tipo de ingreso (perfil/compañía) | AD-ING-001 |

### 3.3 Componente aún concentrado

`models/lumber_reception.py` mantiene:
- `LumberReceptionLine` (modelo de staging)
- `LumberReception` (cabecera)
- computes de staging (`_compute_volume_purchase`, `_compute_export_values`, `_compute_visual_defaults`, etc.)
- normalizaciones y comportamiento UI

**Conclusión arquitectónica:** el refactor estructural está avanzado y funcional, pero no está completada la separación total de línea/cabecera a archivos independientes.

**⚠️ PARSEO DISPERSO en `madenat_guia_processing.py`:** 9 métodos de extracción de datos sin dispatcher equivalente a `reception_parser.py` tras extracción de `_parse_fraction` (AD-41) (`_parse_dispatch_pdf` L2128, `_parse_packing_excel` L2445, `_parse_excel_data_core` L2524, `_find_oc_reference_in_excel` L2834, `_parse_float_value` L2639, `_get_nominal_dimension` L2678, entre otros). El archivo concentra ~4,330 líneas y 8 responsabilidades con parseo disperso, frente a `reception_parser.py` que está desacoplado como dispatcher dedicado. `_parse_fraction` ahora vive como `parse_fraction_to_decimal_inch` en `utils_uom.py` (función pura compartida). Esta asimetría no estaba documentada en versiones previas. Confirmado en auditoría 2026-07-08. Ver riesgo relacionado en `02_CONTINUIDAD.md` sección 5.

**Regla de diseño a preservar:** La lógica de negocio S2S vs Blank está correctamente aislada en `_compute_vol_shipment_m3` (L476-538, bifurcación en L510-516), separada del parseo. Cualquier intervención futura sobre los 9 métodos de parseo restantes NO debe tocar ni fusionar esta lógica.

### 3.4 Regla de independencia de módulos base (T6, 2026-09-26)

Un módulo **base** no puede referenciar XML IDs declarados únicamente por un módulo que **depende** de él.
`madenat_lumber_logistics` (base respecto de `madenat_lumber_billing`) declaraba el botón «Crear
Consolidación» con `%(madenat_lumber_billing.action_create_consolidation_from_shipment)d` en su vista de
Embarque (`views/lumber_export_shipment_views.xml`), lo que abortaba la instalación limpia de Logistics sin
Billing (`Invalid xmlid … for button of type action`). La referencia se eliminó de Logistics y la
funcionalidad se conserva mediante una vista heredada **propiedad de Billing**
(`madenat_lumber_billing.view_lumber_billing_shipment_form_billing_button`, `mode=extension`) sobre
`madenat_lumber_logistics.view_lumber_export_shipment_form`.

**Criterio normativo:** cuando una acción o vista pertenece a un módulo superior, su punto de extensión se
declara en ese módulo superior (herencia de vista), nunca en el base. No se resuelve con dependencias
invertidas (Logistics → Billing) que crearían un ciclo.

---

## 4. Modelos funcionales

### 4.1 `lumber.reception.line`

Modelo de staging (`_name = 'lumber.reception.line'`, `_inherit = ['madenat.lumber.ingest.line.mixin']`).

**Propósito:** Reflejar la información cargada desde documentos antes de Gate 3. Preservar triple capa (visual, física, nominal). Superficie de corrección operativa previa a stock. Base para cálculos volumétricos.

**Campos funcionales (verificados contra código):**
- `reception_id` — Many2one → `lumber.reception`, cascade delete
- `lot_name` — Char, requerido
- `product_id` — Many2one → `product.product`
- `subproduct_id` — Many2one → `madenat.subproducto`
- `product_code`, `product_name` — Char
- `pieces` — Integer
- `thickness_visual`, `width_visual` — Char (representación imperial: "6/4", "5 5/8")
- `thickness_nominal`, `width_nominal` — Float (mm)
- `length` — Float (metros, fuente de verdad para cálculos volumétricos)
- `length_input_raw` — Float (valor crudo digitado por operador en la unidad `lengthuom`)
- `lengthuom` — Selection: `m` / `mm` / `ft`
- `vol_physical_m3` — Float, compute/store
- `vol_purchase_m3` — Float, compute/store, inverse habilitado (editable en staging)
- `vol_shipment_m3` — Float, compute/store (volumen de exportación)
- `vol_mbf` — Float, compute/store
- `export_calculation_rule` — Char
- `audit_snapshot` — Text, readonly, copy=False (JSON inmutable generado por Gate3)
- `audit_hash` — Char, SHA-256, readonly, copy=False

**Política de largo (AD-12 a AD-17):**
- `length` = valor normalizado en metros. Base de todo cálculo volumétrico.
- `length_input_raw` = valor de entrada del operador (preservado sin modificar).
- `lengthuom` = unidad de entrada. Desacoplada del perfil de ingesta (AD-14).
- Normalización: `_compute_lengthm` → `@api.depends('length_input_raw', 'lengthuom', 'length')`.
- Conversión: ft → `raw * FT_TO_M`, mm → `raw * 0.001`, m → valor directo.
- El naming correcto es `length_input_raw` (con underscores), consistente con el código.

### 4.2 `lumber.reception`

Cabecera del flujo (`_name = 'lumber.reception'`).

**Responsabilidades:** Gestionar estado del proceso, orquestar gates y transiciones, centralizar recepción documental, controlar cuándo una recepción puede procesarse/reabrirse/cancelarse, vincular staging → snapshot → inventario.

**Campos relevantes:**
- `reception_line_ids` — One2many → `lumber.reception.line`
- `state` — Selection: draft / processing / verified / done / cancel / error / pending_link
- `ingestion_profile` — Selection: f5085 / f1550 / metric (nota: `blanks_clear` es el rótulo semántico del flujo Blank; el valor real del selector es `f5085`. Diagnóstico 2026-08-15.)
- `audit_snapshot`, `audit_hash`
- `can_process_reception`, `can_reopen_reception`, `can_cancel_reception` (compute desde `reception_workflow.py`)
- `guia_numero` (Char), `guia_fecha` (Date)
- `supplier_id` — Many2one → `res.partner`
- `order_id` / `purchase_id` — Many2one → `purchase.order`
- `oc_reference_raw` — Char (readonly, copy=False): referencia documental de OC extraída de la Guía/PDF. Nunca se sobrescribe al vincular una `purchase.order`.
- `oc_reference_norm` — Char (compute, store): clave normalizada para matching (`parser.normalize_po_key`).
- `oc_match_status` — Selection: `not_found` / `single_match` / `multi_match` / `manual` / `created`. Estado de resolución de OC.
- `oc_match_note` — Text: bitácora de reconciliación de OC.
- `po_missing_alert` — Html (compute, sanitize=False): alerta visual de OC ausente o con referencia manual, NO bloqueante.

**Métodos arquitectónicos clave:**
- `action_confirm_reception()` → GB-1 → Gate2 → Gate3 → `LumberReceptionService._create_lots_from_packing()`.
- `action_reset_to_draft()` → **reapertura no bloqueante y trazable** (2026-10-02). Abre el asistente `lumber.reception.reset.wizard`; el **motivo** es obligatorio solo si existe **efecto físico**. Los pickings **done** atribuidos por `stock.picking.reception_id` se revierten con **return picking nativo** (conserva producto, lote, ubicaciones, compañía y cantidad; vínculo por `origin_returned_move_id`/`return_id`); los **no done** se desreservan/cancelan por API estándar; **sin picking atribuible** se ejecuta el reset documental conservando stock e historial y emitiendo advertencia. **Prohibido** borrar o escribir directamente `stock.quant`, lotes, pickings, movimientos o líneas de movimiento con historia física como mecanismo de reset, y **prohibido** usar `lot_id` aislado como criterio de reversión. Las advertencias **no bloquean** y no hay aprobación adicional; la reversión es **idempotente** (el reintento no duplica el retorno). Evidencia: `madenat.audit.log` (`action_type='deviation'`, snapshot + firma SHA-256, usuario, motivo, advertencias, origen y retorno) y chatter. **Límite (actualizado G1+G2+G3, 2026-10-02):** la reapertura de **guía** `madenat.guia.processing.action_reopen_to_draft` es **no bloqueante y trazable** (ver §4.3); **G2** (vínculo persistente guía↔picking, `stock.picking.guia_processing_id`) y **G3** (retorno automático del ingreso de producción atribuido por esa llave fuerte) están **implementados** (ver §4.3).

### 4.3 `madenat.guia.processing`

Flujo complementario para guías procesadas. Modelos:
- `madenat.guia.processing` (cabecera)
- `madenat.guia.processing.line` (líneas)

Métodos: `do_full_processing()`, `action_validate()`, `_create_or_get_lot()`, `action_reopen_to_draft()` / `_reopen_reextract_oc()` (reset a borrador que preserva lotes, desvincula pickings, **re-extrae la OC documental** del documento adjunto —fallback local «O/C», respaldo `_parse_dispatch_pdf()`, respaldo Excel— y **conserva el valor previo como resguardo** si no puede re-extraerla, sin re-vincular la OC — Tarea B-1, Opciones 2+3, 2026-09-28).

**Reapertura no bloqueante y trazable (G1 + G2 + G3, 2026-10-02).** `action_reopen_to_draft()` abre
el asistente `madenat.guia.processing.reopen.wizard` (motivo obligatorio solo con **efecto físico**);
la ejecución vive en el método privado `_reopen_to_draft_confirmed` (no invocable por RPC). Se
revierten automáticamente, con **retorno nativo idempotente**:

- **Consumo BT-04/Servicio** (`consumption_picking_id` en estado `done`) con
  `_reverse_consumption_picking()` (no se modifica).
- **Ingreso de producción NUEVO** (**G3**), atribuido **exclusivamente** por la **llave fuerte** de
  **G2** `stock.picking.guia_processing_id` → `madenat.guia.processing.id` (Many2one, `index=True`,
  `ondelete='set null'`, `copy=False`, `check_company=False` — el comodel no tiene `company_id`;
  asignada **solo** al crear el picking de ingreso en `_get_or_create_picking_unified`):
  `_attributed_production_pickings()` + `_reverse_production_picking()`. La atribución **nunca** usa
  `origin` textual ni `lot_id`. Idempotencia por la relación nativa `return_id` (no por `origin`); el
  retorno **no** porta `guia_processing_id` (exclusión G2).

La **producción/legado sin vínculo fuerte** (históricos sin FK) **no** se retorna automáticamente: se
conserva stock, lotes, pickings, movimientos y líneas, con **advertencia** de atribución
insuficiente. Contenedor, quant externo, costos y albaranes externos generan **advertencias no
bloqueantes**, nunca bloqueos. **No** se escribe ni borra `stock.quant`, no se anula
`_cleanup_orphan_moves_guia` ni se muta `origin`. Evidencia: `madenat.audit.log`
(`action_type='deviation'`, snapshot + SHA-256, usuario, motivo, warnings, lotes, consumo origen y
retorno, producción y retornos) y chatter.
**H1 — Reversión física ASISTIDA de producción histórica (2026-10-02).** Complemento **aditivo** de
G1 para la **producción histórica sin llave fuerte** (pickings sin `guia_processing_id`),
**no-granel** y **sin** consumo BT-04. Se abre desde el botón secundario **«🧭 Reversión histórica
asistida»** (`action_open_historical_reverse_wizard`), nunca desde el contrato de G1. **No hay
atribución automática**: `origin`, `lot_id`, producto, proveedor, texto y fecha son **señales** de
propuesta, no llaves. Un wizard separado
(`madenat.guia.processing.historical.reverse.wizard` + líneas
`madenat.guia.processing.historical.reverse.candidate`) clasifica candidatos **A** (origen exacto +
**cobertura total de lotes** de la guía + `incoming`/`done` + sin retorno ⇒ preseleccionado), **B**
(una sola señal media / evidencia parcial ⇒ visible, **no** preseleccionado, selección explícita) y
**C** (excluido: prefijo histórico `REVERTIDO-/ANULADO-/PURGADO-`, retorno previo, granel/SV, sin
evidencia, compañía ajena, no-`done`, no-`incoming`, FK G2, recepción normal). La **primera versión
solo permite retorno TOTAL por picking** seleccionado (`_h1_reverse_picking_total`): salida inversa
**nativa** (picking/move/move.line) preservando producto, UoM, lote, ubicaciones, `owner_id`,
`package_id`/`result_package_id`, compañía y las relaciones `origin_returned_move_id`/`return_id`.
Es **idempotente** (retorno previo ⇒ ni se propone ni se permite; el reintento **reutiliza**). El
operador **no queda bloqueado**: puede no seleccionar ninguno (sin efecto físico); el motivo es
obligatorio **solo** con efecto físico; los warnings nunca bloquean. **Nunca** se escribe/borra
`stock.quant`, ni se borran/desvinculan lotes, pickings, moves, move lines o `lot_ids` (**preserva
la historia**); **no** se invoca la reapertura de G1 (que limpia `lot_ids`), de modo que H1 no
cambia el estado de la guía —la reapertura documental sigue siendo responsabilidad exclusiva de
G1—. Evidencia: `madenat.audit.log` (`action_type='deviation'`, snapshot + SHA-256, usuario,
motivo, selección, retornos, omitidos, warnings, lotes) y chatter. Cobertura:
`TestGuiaHistoricalReverse` (T-H1-01..11).



**Interfaz operativa (AD-78):** el formulario clásico de la Guía no es la pantalla operativa de Operaciones; la operación se realiza en `madenat_lumber_intake` (ver «Interfaz operativa oficial de Intake»). Los campos declarados de Recepción por Volumen (`anchos_variables`, `largos_variables`, `espesor_nominal_texto`, `piezas_declaradas`, `volumen_declarado_m3`, `volume_lot_id`) persisten en este modelo y se gestionan en Intake.

### 4.4 `stock.lot` extendido (`StockLotExtended` en `stock_lot.py`)

Extensión post-Gate3 de `stock.lot`. Campos y computes:
- `vol_shipment_m3` — Volumen de embarque con bifurcación blanks vs S2S (AD-27).
- `volume_purchase_m3` — Volumen nominal de compra.
- `_compute_estado_trazabilidad()` — Batch query de trazabilidad.
- `_compute_processing_loss()` — Pérdida entre compra y embarque.

### 4.5 Contrato Producto Maestro / Subproducto (AD-ING-001, AD-ING-002)

**Producto maestro** (`madenat.lumber.product.default`):
- Configuración persistente que resuelve `product_id` por tipo de ingreso (`bruta`/`procesado`), refinable por perfil y compañía.
- Único punto de resolución: `madenat.ingestion.config.get_default_product(tipo_ingreso, profile=None)`.
- El producto maestro **no** se deriva del texto del Excel ni se hardcodea en Python.

**Subproducto** (desde el Excel):
- La columna `Producto`/`Descripción`/`Especie`/`Subproducto` se asigna a:
  - Procesado: `subproducto_id` (`madenat.guia.processing.line`);
  - Bruta: `subproduct_id` (`lumber.reception.line`).
- Si no existe, se **autocrea** en `madenat.subproducto` (`find_or_create_lumber_subproducto`).
- Trazabilidad del texto original: `product_name_original` (Procesado) / `excel_product_name` (Bruta).

### 4.6 Recepción a Granel + Balance de Masa + Consolidación Administrativa (AD-65 — diseño aprobado, pendiente de implementación)

Flujo de diseño aprobado (no implementado) para madera que llega por **volumen total** a un patio sin desglose de piezas, destinada a procesamiento externo:

- **Extracción (AD-63/AD-65):** un único motor (extensión de `madenat_ingestion_engine`) degrada en cascada: tabla PDF de columnas fijas configurables → subtotales por grupo → total de encabezado (mínimo garantizado). Nunca bloquea; genera `ingestion_document_warning` no bloqueante.
- **Patio:** `stock.location` nativo (`location_id` en `lumber.reception`); se crea bajo demanda, nunca se elimina con stock. Sin modelo propio.
- **Envío a proceso (Balance de Masa, ISO 22095):** se resta una **cantidad** del pool de volumen del patio (no un lote completo) y el retorno se registra como stock nuevo independiente, **sin** genealogía `parent_lot_id`/`child_lot_ids` (alineado con DEC-002). Requiere extender `_get_or_create_consumption_picking` para consumo parcial (gap AD-64).
- **Consolidación administrativa:** manual y opcional; granularidad adaptativa (etiqueta/paquete/volumen) con volumen como denominador común. Complementa, no reemplaza, los discriminadores `reception_id`/`guia_processing_id` (ver `12_FLUJOS_INGESTA.md` §11).
- **Prohibición normativa:** no se valida correspondencia de detalle entre envío y retorno; la relación es balance agregado (texto íntegro en AD-65 §1.7).
- **Costeo:** fuera de esta etapa; el valor se entrega a Costeo/Auditoría.
- **Reporte de conciliación:** extensión de `madenat_lumber_reports`, informativo, factor de rendimiento configurable; uso exclusivo de Auditoría.

**Nominales:**
- Procesado: `espesor_mm` se usa como fallback de `espesor_nominal_mm` cuando el Excel no informa nominal.
- Bruta: conserva los defaults existentes desde dimensiones físicas. No hay lookup automático de ancho.

**Volúmenes (presentación):**
- `Volumen total (m³)` = Σ `vol_shipment_m3`.
- `Volumen stock (m³)` = Σ `vol_purchase_m3`.
- Toda salida volumétrica usa 3 decimales; no se muestran totales numéricos sin etiqueta.

**Separación de responsabilidades:**
- Core: configuración, mapeo y creación de catálogos.
- Intake: fachada, revisión operativa y presentación.
- Sin cambios en BT-04, Toll, `action_validate` e `intake_direct_stock`.
- La hipótesis de una ingesta unificada queda como investigación futura, fuera de alcance.

---

### 4.7 R1 — Detalle por Patio: `stock.quant` extendido en `madenat_lumber_reports`

**Responsabilidad documental explícita (AD-77).** Esta sección es el dueño canónico del inventario de
campos de la capa de presentación de R1.

- **Modelo de lectura:** R1 "Detalle por Patio — Stock Real" (`action_r1_stock_detail_patio`, vista
  `view_stock_quant_tree_r1_detail_patio`) lee `stock.quant`. Alcance: cantidad positiva en
  ubicaciones internas (`quantity > 0`, `location_id.usage = 'internal'`) agrupado por
  patio/ubicación. Search view: `view_stock_quant_search_inventory`.
- **Propiedad de la capa:** `madenat_lumber_reports` es dueño de la presentación y el reporting de
  R1 (`models/lumber_stock_report.py`, `models/report_helpers.py`).
- **Frontera con Core (sin duplicidad de dominio):** `madenat_lumber_core` sigue siendo dueño del
  gemelo digital de lote (campos base de `stock.lot` y flujos de creación por recepción y guía). R1
  solo añade campos derivados de lectura.
- **Campos de Programación 1 en `stock.quant`** (compute almacenado, solo lectura):

| Campo | Objetivo | Fuente real | Limitación |
|---|---|---|---|
| `lot_operational_label` | Etiqueta operativa que presenta `Lote Volumen` en lugar del token técnico `GRANEL` | `stock.lot.name` | Etiqueta sintética de UI; no reemplaza el nombre técnico ni participa de las búsquedas técnicas |
| `is_volume_lot` | Criterio técnico del flujo por volumen (indexado) | `stock.lot.name` normalizado | Solo clasifica; no implica stock ni volumen disponibles |
| `lot_entry_datetime` | Fecha/hora de ingreso del lote | Recepción documental; fallback creación del lote cuando existe guía de procesamiento sin recepción | Puede quedar vacío de forma legítima; el fallback no es fecha documental de recepción |
| `lot_entry_datetime_source` | Distinguir la fuente de la fecha de ingreso | Idem `lot_entry_datetime` | — |
| `lot_origin_document` | Documento de origen enlazado al lote | Recepción de compra o guía de procesamiento | Vacío si no hay documento enlazado; puede coincidir con el N° de guía en orígenes por guía |

- **Regla de presentación:** el token técnico inicial `GRANEL` (nombre exacto `GRANEL` o prefijo
  `GRANEL `) identifica lote de volumen y se presenta como `Lote Volumen`. No se modifica
  `stock.lot.name`, `display_name`, `name_get` ni `name_search`; la búsqueda por el nombre técnico se
  mantiene por `lot_id`.
- **Disponibilidad:** sigue siendo responsabilidad del inventario estándar (`stock.quant.quantity` y
  movimientos). Los cinco campos son de presentación y **no** alteran stock.
- **Deuda arquitectónica declarada:** la normalización definitiva de las múltiples fuentes de fecha
  de ingreso en `stock.quant` queda **pendiente**; no es funcionalidad implementada.

### 4.8 Gestión Operativa de Etiquetas SV (`madenat.sv.operation`)

Propietario técnico: `stock.lot`. Etiqueta vigente: `stock.lot.name`. Identidad de flujo
Volumen: `lot_flow_type = 'volume'` + `volume_source_guia_id`.

**Formato.** `SV` + 11 dígitos (`^SV[0-9]{11}$`), por ejemplo `SV00000000008`. La creación del
lote consume la secuencia única `madenat.volume.lot`; los renombres **no** consumen ni reservan
secuencia.

**Volumen oficial.** Primer valor estrictamente positivo de `volume_pdf_m3` (Guía PDF) →
`volume_excel_m3` (Packing Excel) → `packing_volume_declared_m3` (Packing declarado). Sin fuente
positiva no existe volumen oficial. Regla funcional completa en `12_FLUJOS_INGESTA.md` §11.5.

**Ledger (append-only).** `madenat.sv.operation` registra las operaciones de etiqueta SV. Tipos:
`rename`, `regularize_volume`, `rebaja`, `rebaja_reverse`; estados `draft / applied / reversed /
rejected`. Cada operación aplicada conserva snapshot y firma SHA-256 (`snapshot_json`,
`audit_hash`) y referencia el lote, la Guía, el contenedor y el embarque cuando aplica; se refleja
en chatter y en `madenat.audit.log` (`action_type = 'sv_operation'`). Una corrección es una
operación nueva: la historia aplicada no se edita ni se elimina (escritura y borrado restringidos
por el modelo).

**Saldo.** Baseline original (`volume_purchase_m3 or volumen_m3`); si existe, la última
regularización aplicada define el baseline regularizado. Rebajado activo = rebajas aplicadas menos
las reversas válidas. Saldo disponible = baseline regularizado − rebajado activo. El saldo es un
cálculo derivado del ledger, no un valor editado a mano.

**Piezas (opcionales).** Solo son balanceables si la Guía declara piezas documentales positivas
(`piezas_declaradas` o `packing_pieces_declared`). Nunca se infieren de paquetes, de líneas PDF, de
la fila sintética GRANEL ni del placeholder técnico `stock.lot.piezas = 1`.

**Seguridad.** Los campos SV protegidos de `stock.lot` (etiqueta, volúmenes, piezas y la marca
técnica de serialización) no admiten escritura directa: una guarda ORM exige una operación SV
validada, autorizada y aplicada atómicamente en servidor, mediante un permiso interno de un solo
uso ligado a actor, lote, operación y valores esperados. Decisión y alcance en
`04_DECISION_LOG.md` AD-79.

**Concurrencia (fail-closed).** Toda operación que altere saldo bloquea la fila del lote y la de la
operación y recalcula el saldo dentro de la misma transacción. Ante conflicto concurrente se
rechaza la operación sin saldo negativo y sin registros parciales (ledger, alias, chatter,
auditoría, marca de serialización), con mensaje funcional al usuario y sin reintento automático
silencioso. Decisión en AD-79; evidencia en `03_TESTS.md` §9.

**Reversa de Guía por Volumen.** La cancelación/devolución usa exclusivamente el lote SV vinculado
a la Guía (las líneas de retorno conservan el `lot_id` SV), no sustituye lotes de terceros, evita
retornos duplicados mediante relaciones técnicas de retorno y bloquea antes de devolver cuando el
saldo propio es insuficiente. Los flujos Producto, Servicio y Tarja **no** fueron rediseñados en
esta corrección.

---

## 5. Gates y política de side effects

El sistema opera bajo 4 gates formales (`ingestion_gate.py`) + 1 guardia inline:

1. **Gate 0 — PreUpload** (`Gate0PreUpload`): Validación temprana de archivos (tipo, tamaño ≤20MB, estructura). Sin efectos en BD.
2. **Gate 1 — DocumentReconciliation** (`Gate1DocumentReconciliation`): Conciliación de líneas de packing vs guía. Sin efectos en BD.
3. **Gate 2 — CommercialAnalysis** (`Gate2CommercialAnalysis`): Análisis de nominales, tolerancias y reglas comerciales. Sin efectos en BD.
4. **GB-1** (inline en `action_confirm_reception()`): Guardia pre-Gate3 que verifica staging completo antes de permitir el commit.
5. **Gate 3 — PreCommit** (`Gate3PreCommit`): Notario criptográfico. Genera `audit_snapshot` (JSON) + `audit_hash` (SHA-256). **Único punto autorizado de escritura en inventario** (AD-04).

**Regla operativa:** Gates 0–2 + GB-1 son sin efectos en stock. Gate 3 es el único write autorizado a `stock.lot` y `stock.move`.

---

## 6. Wizards

- `lumber.reception.mass.update` — Asignación masiva de espesores/anchos/subproductos. Lee reglas desde `madenat.ingestion.config`.
- `madenat.guia.mass.update` — Ídem para guías de procesamiento.
- `madenat.period.close` — Cierre de período (staging, pendiente validación completa).

---

## 7. Criterio de alineación documental

Este documento se rige por la jerarquía de verdad definida en `INDICE_DOCUMENTACION.md` sección 8:
1. Documento canónico del tema en `CANON/`.
2. `04_DECISION_LOG.md`.
3. `02_CONTINUIDAD.md`.
4. Código fuente (verdad funcional).

Si el código cambia en: layout de largo, campos de staging, gates, modularización, modelos Fase 2/3, o política de side effects, este archivo debe actualizarse en la misma sesión (AD-25).

---

## Interfaz operativa oficial de Intake

El formulario clásico de `madenat.guia.processing` no debe considerarse
la pantalla operativa final para Operaciones.

`madenat_lumber_intake` es la interfaz operativa oficial de Operaciones:
wizard, consola, carga documental, revisión, captura y ajustes de datos
de recepción por volumen, y validación del flujo.

`madenat.guia.processing` es el registro persistente de la Guía y de su
trazabilidad documental, comercial, física y logística. Su formulario
clásico queda destinado a consulta, soporte administrativo, auditoría y
trazabilidad técnica.

Para Recepción por Volumen:

Intake → 1 Guía → 1 Etiqueta SV → 1 `stock.lot` volume → 1 picking incoming.

Los datos RW, RL, espesor nominal, piezas declaradas, M³ declarado y la
etiqueta SV deben presentarse y gestionarse en Intake. El modelo
`madenat.guia.processing` sigue siendo el propietario persistente de esos
valores, pero no la interfaz operativa principal.

---

### 4.9 Bloque SV visible y ciclo de vida controlado de guías (AD-80, 2026-09-28)

**Superficie de Operaciones.** La Consola de Ingreso de Madera (`madenat.lumber.intake.console`)
expone, para la Recepción por Volumen, un bloque **read-only** `ETIQUETA SV Y SALDO OPERATIVO`
(visible solo con lote SV real) con proxies **no almacenados** sobre las guardas de `stock.lot`
(`sv_original_volume_m3`, `sv_regularized_baseline_m3`, `sv_rebajado_m3`, `sv_available_m3`,
`sv_pieces_enabled`, `sv_available_pieces`, `sv_documentary_warning`) y sobre el ledger
(`madenat.sv.operation`). Las cinco acciones autorizadas (modificar etiqueta, regularizar
volumen, rebajar etiqueta, reversar rebaja y ver historial) se exponen también en el formulario
de la Guía de la fachada Intake y en el grupo `🏷️ Etiqueta SV` del formulario estándar de
`madenat.guia.processing`; todas delegan en los wizards del Programa SV (§4.8) y ninguna escribe
`stock.lot.name`, volumen ni saldo.

**Ciclo de vida.** Asistente `madenat.lumber.intake.guide.lifecycle` con diagnóstico único de
trazas (lotes, pickings, movimientos, líneas de movimiento, quants, operaciones SV, costo,
valoración, consolidación, factura, contenedor, embarque y período cerrado) y cuatro modos:
A (eliminación definitiva sin trazas, `unlink()` canónico), B (cancelación conservando
trazabilidad, `action_force_cancel()` sin cambios), C (purga controlada de guía y lote SV técnico,
con confirmación escrita y Jefatura de Operaciones) y D (bloqueo y escalamiento). La evidencia se
registra en `madenat.audit.log` (nuevos `action_type`: `guia_delete_blocked`,
`guia_delete_permanent`, `guia_purged`) con snapshot y firma SHA-256.

**Frontera de propiedad.** `stock.lot` sigue siendo el propietario del saldo y `madenat.sv.operation`
el del historial; la Consola y el asistente solo leen y delegan. No se introduce SQL de escritura,
`ON DELETE CASCADE`, ni borrado de movimientos, pickings, quants u operaciones SV
aplicadas/reversadas. Decisión completa en `04_DECISION_LOG.md` (AD-80).

**Entorno de desarrollo del Modo A (2026-09-28).** La relajación DOCUMENTAL del Modo A (chatter,
adjuntos y referencias genéricas) exige `_lifecycle_dev_environment_ok()`, que delega en
`madenat.sv.internal.marker._sv_test_environment_ok()`. Ese método admite **dos vías** y su
invariante común, inviolable en ambas, es que **el nombre de la base de datos contenga `test`**:

| Vía | Método | Condición | Consumidores |
|---|---|---|---|
| **ESTRICTA** | `_sv_test_enable_strict()` | `--test-enable` real **y** BD de test | `_sv_test_cleanup_allowed()`, `_sv_test_mark()` y `_sv_test_cleanup()` — mecanismos que tocan el ledger SV |
| **ALTERNATIVA** (solo desarrollo) | `_sv_dev_cleanup_enabled()` | `ir.config_parameter('madenat.dev_cleanup_enabled') == 'True'` **y** BD de test | «Modo A autoservicio» vía `_lifecycle_dev_environment_ok()` |
| **SUMA** | `_sv_test_environment_ok()` | ESTRICTA **o** ALTERNATIVA | Modo A autoservicio y pruebas automatizadas |

`--test-enable` **nunca** debe activarse en el servidor persistente: en Odoo 18
(`odoo/modules/loading.py`) hace que se ejecute la suite completa de todos los módulos instalados
dentro del mismo proceso que atiende HTTP, con un único `Registry.test_cr` compartido, y las
peticiones reales son rechazadas con `400 Bad Request: Trying to open a test cursor…`
(incidente real del 2026-09-28). La vía alternativa existe precisamente para desacoplar el
autoservicio de desarrollo de ese flag.

El parámetro solo se **lee** desde MADENAT (nunca se escribe desde el código): se activa en
**Ajustes → Técnico → Parámetros del Sistema → `madenat.dev_cleanup_enabled = True`**, escritura
restringida por ACL nativa al grupo `Settings` (`base.group_system`). Valor admitido:
exactamente `True` (fail-closed: cualquier otro valor desactiva la vía). Los mecanismos del ledger
SV **no** se relajan por parámetro en ningún caso.

*Propagación entre procesos:* `ir.config_parameter.create/write/unlink` limpia la caché del proceso
que escribe y, al confirmar la transacción por el path de request/RPC, emite la señal
(`Registry.signal_changes()`, `odoo/service/model.py`), de modo que activar o desactivar **desde la
propia UI del servidor** surte efecto sin reinicio. Un cambio hecho desde **fuera** del servidor
(p. ej. `odoo shell`) no emite esa señal y el servidor puede conservar el valor cacheado
(`@ormcache` en `_get_param`): en ese caso, `docker compose restart web`.

---

## Rolleo marítimo centrado en Embarque (AD-92, 2026-10-05)

La planificación marítima de un Embarque (`lumber.export.shipment`) se reprograma
**desde el propio Embarque**, no desde la Motonave. Una Motonave (`shipping.vessel`)
es un **maestro histórico reutilizable** (muchos viajes y Embarques de meses
distintos); no es una salida concreta ni un conjunto seguro de cargas afectadas.

- **Unidad de negocio:** exactamente un Embarque.
- **Campos escritos:** sólo `vessel_id` y `voyage_id` de ese Embarque.
- **Alcance del asistente** (`lumber.vessel.rollover.wizard`): `_scope_shipments()`
  devuelve el `shipment_id` seleccionado; `origin_vessel_id`/`origin_voyage_id` son
  derivados (sólo lectura) del Embarque.
- **Sin efectos laterales:** no mueve stock, lotes, quants, movimientos, pickings,
  contenedores (como pertenencia), costos, Rebaja, Zarpe, B-01, R1, R2, Entrega ni
  finanzas. Auditoría SHA-256 + chatter. Pendiente documental **no bloqueante** vía
  `lumber.shipment.document`.
- **Estados:** sólo `draft`/`confirmed` (post-zarpe bloqueado en UI y servidor).
- **Roles:** Operaciones / Jefatura de Operaciones / Gerencia (guard de servidor).
- **Motonave:** el botón de la ficha pasa a **consulta** (`action_open_vessel_shipments`),
  sin reasignación masiva desde la Motonave.

Norma detallada: `04_DECISION_LOG.md` **AD-92**.

---

## 8. Historial de versiones

| Versión | Fecha | Cambio |
|---|---|---|
| 7.1.0 | 2026-06-30 | Auditoría documental. Consolidación post-limpieza. |
| 7.2.0 | 2026-07-01 | Validación cruzada contra código. Corrección de naming (`length_input_raw`), gates reales (0–3 + GB-1), modelos Fase 2/3 agregados, `stock_lot.py` y `ingestion_gate.py` documentados, wizards listados, cadena funcional ajustada a grafo horizontal. |
| 7.3.0 | 2026-07-08 | Corrección de vigencia post-auditoría: `core_utils.py` y `product_template.py` marcados como huérfanos/muertos, archivos faltantes agregados a tabla 3.1 (`validation_checklist_mixin`, `stock_lot_cost_line`, `stock_picking`, `stock_move`, `product_product`), parseo disperso de `madenat_guia_processing.py` documentado en sección 3.3. Sin cambios de código. |
| 7.5.0 | 2026-08-19 | Alineación con código: estados reales de `lumber.reception` (`draft/processing/verified/done/cancel/error/pending_link`) y campos canónicos de OC documentados en §4.2 (`oc_reference_raw`, `oc_reference_norm`, `oc_match_status`, `oc_match_note`, `po_missing_alert`). Sin cambios de código. |
| 7.6.0 | 2026-09-12 | Se documenta `madenat_ingestion_engine` (módulo consumido por `madenat_lumber_intake`) en §3.1: estado real verificado (`installed` 18.0.1.0.0) y gaps (extracción PDF de tablas no cubierta; perfil de columnas esqueleto). Sin cambios de código. |
| 7.7.0 | 2026-09-12 | Se documenta el flujo de recepción a granel + Balance de Masa + consolidación administrativa (AD-65, diseño aprobado, pendiente de implementación) en §4.6. Sin cambios de código. |
| 7.8.0 | 2026-09-25 | Se documenta R1 — Detalle por Patio (`stock.quant` extendido en `madenat_lumber_reports`) en §4.7: campos de Programación 1, regla de token técnico `GRANEL` → presentación `Lote Volumen`, frontera de propiedad con Core y deuda de fuentes de fecha (AD-77). Sin cambios de código. |
| 7.9.0 | 2026-09-25 | Se documenta la interfaz operativa oficial de Intake (AD-78) en la sección «Interfaz operativa oficial de Intake»: wizard, consola, carga documental y captura de datos de Recepción por Volumen como superficie de Operaciones; el formulario clásico de `madenat.guia.processing` queda para consulta, soporte administrativo, auditoría y trazabilidad técnica. Sin cambios de código. |
| 7.10.0 | 2026-09-26 | Se documenta la Gestión Operativa de Etiquetas SV (`madenat.sv.operation`, AD-79) en §4.8: identidad y formato SV, secuencia `madenat.volume.lot`, volumen oficial, ledger append-only con snapshot/firma, fórmula de saldo, piezas opcionales, guardas ORM con permiso interno de un solo uso, concurrencia fail-closed y reversa de Guía por lote SV específico. Sin cambios de código. |
| 7.11.0 | 2026-09-26 | Se documenta en §3.4 la regla de independencia de módulos base (T6): el botón de Consolidación de Facturación se aporta desde una vista heredada propiedad de `madenat_lumber_billing`, no desde `madenat_lumber_logistics`. |
| 7.12.0 | 2026-09-28 | Se documenta en §4.9 el bloque SV visible de la Consola (proxies no almacenados), las acciones SV autorizadas en Consola y Guía, la jerarquía del volumen oficial y el ciclo de vida controlado de guías (Modos A–D, AD-80). Con cambios de código (`madenat_lumber_intake` 18.0.0.6.0, `madenat_lumber_core` 18.0.6.3.0). |
| 7.13.0 | 2026-09-28 | Se documenta en §4.9 el **entorno de desarrollo del «Modo A autoservicio»**: vía ESTRICTA (`_sv_test_enable_strict()`, única admitida por el ledger SV) vs. vía ALTERNATIVA por `ir.config_parameter('madenat.dev_cleanup_enabled')`, con el candado `'test' in dbname` inviolable en ambas vías. Desacopla el autoservicio de desarrollo de `--test-enable`, que en un servidor persistente ejecuta la suite completa de todos los módulos en el mismo proceso HTTP (incidente del 2026-09-28). Con cambios de código en `madenat_lumber_core` (`models/madenat_sv_internal.py`, `tests/test_sv_dev_cleanup_param.py` + `tests/__init__.py`) y `madenat_lumber_intake` (`tests/test_guide_lifecycle.py`, tests 19–20). Sin bump de versión de manifiesto (fuera del alcance aprobado). |
| 7.14.0 | 2026-10-02 | Se documenta en §4.2 la **política de corrección/reset de recepción no bloqueante y trazable** (ver historial anterior). |
| 7.15.0 | 2026-10-02 | Se documenta en §4.3 la **reapertura no bloqueante y trazable de guía procesada (G1)**: `action_reopen_to_draft` abre wizard (motivo solo con efecto físico), revierte el **consumo BT-04** con retorno nativo idempotente y, sin vínculo fuerte, **conserva** stock/lotes/pickings/movimientos con advertencia; sin escribir/borrar `stock.quant` ni mutar `origin`, con auditoría `deviation` + chatter. G2/G3 pendientes. Con cambios de código (`madenat_lumber_core`: `madenat_guia_processing.py`, wizard `madenat.guia.processing.reopen.wizard`). |
| 7.16.0 | 2026-10-02 | Se documenta en §4.3 **G2 + G3**: **G2** añade la **llave fuerte** `stock.picking.guia_processing_id` → `madenat.guia.processing.id` (Many2one, `index=True`, `ondelete='set null'`, `copy=False`, `check_company=False`), asignada **solo** al crear el picking de ingreso de producción en `_get_or_create_picking_unified` (nunca propaga a consumo, retornos, recepción, rebaja, contenedor, exportación ni inventario; nunca infiere históricos). **G3** añade la **reversión física automática, nativa, trazable e idempotente** del ingreso de producción atribuido por esa FK en la reapertura G1: `_attributed_production_pickings()` + `_reverse_production_picking()`; atribución **exclusiva** por FK (nunca `origin` textual ni `lot_id`); idempotencia por `return_id`; el retorno **no** porta `guia_processing_id`; la producción/legado **sin** FK se conserva con advertencia. Con cambios de código (`madenat_lumber_core`: `models/stock_picking.py`, `models/madenat_guia_processing.py`, wizard `madenat.guia.processing.reopen.wizard`, tests `test_guia_picking_link.py` / `test_guia_production_reverse.py`). |
| 7.17.0 | 2026-10-02 | Se documenta en §4.3 **H1 — reversión física ASISTIDA de producción histórica** (complemento aditivo de G1, `madenat_lumber_core`): wizard separado `madenat.guia.processing.historical.reverse.wizard` (+ líneas candidatas) abierto desde el botón «🧭 Reversión histórica asistida» (`action_open_historical_reverse_wizard`), sin tocar el contrato G1/G2/G3/BT-04. Alcance: guías no-granel, sin consumo BT-04 y sin producción atribuida por la llave fuerte G2 (`_h1_is_historical_production` / `can_historical_reverse`). **Sin atribución automática**: `origin`/`lot_id`/producto/proveedor/texto/fecha son señales de propuesta; categorías A (origen exacto + cobertura total de lotes + incoming/done + sin retorno ⇒ preseleccionado), B (evidencia parcial ⇒ visible, selección explícita) y C (excluido/no proponible). **Solo retorno TOTAL por picking** (`_h1_reverse_picking_total`), nativo, idempotente (`return_id`/`origin_returned_move_id`), preservando producto/UoM/lote/ubicaciones/owner/paquete/compañía; nunca escribe/borra `stock.quant` ni borra/desvincula lotes, pickings, moves, move lines o `lot_ids`; **no** invoca el reset de G1 (que limpia `lot_ids`). Auditoría `deviation` (snapshot + SHA-256) + chatter. Cobertura: `test_guia_historical_reverse.py` (T-H1-01..11). Con cambios de código (`madenat_lumber_core`: `models/madenat_guia_processing_historical.py`, wizard `madenat.guia.processing.historical.reverse.wizard`, `views/guia_processing_views.xml`, ACL). |

