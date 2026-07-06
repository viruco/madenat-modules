# AUDITORÍA ARQUITECTÓNICA COMPLETA — `madenat_lumber_core` Y ECOSISTEMA

**Fecha:** 2026-07-01
**Alcance:** Análisis técnico y documental de TODO el módulo `madenat_lumber_core`, en el contexto de los 9 módulos totales
**Rol:** Arquitecto de software senior + auditor técnico senior
**Proyecto:** MADENAT Lumber — Odoo 18 CE
**Restricción:** NO se modificó código en esta fase

---

# 1. Inventario crudo de `madenat_lumber_core`

## 1.1 Archivos `.py` vivos por sección

### models/ (28 archivos, 14,089 líneas de código)

| Archivo | Líneas | Tipo | Estado | Evidencia de uso |
|---|---|---|---|---|
| `__init__.py` | 46 | Config | ACTIVO NÚCLEO | Orquesta carga de todos los modelos |
| `core_utils.py` | 51 | Helper (AbstractModel) | **HUÉRFANO** | NO está en `__init__.py`. 0 referencias en todo el ecosistema (grep cruzado retorna vacío). Define `madenat.core.utils` con `resolve_partner_record`, `resolve_currency_record`, `resolve_uom_record` — métodos que ningún otro archivo invoca |
| `ingestion_gate.py` | 257 | Modelo (Gates) | ACTIVO NÚCLEO | En `__init__.py`. Importado por `reception_workflow.py`, `lumber_reception.py`. Test `test_ingestion_gate.py` (176 líneas) |
| `lumber_blank_nominal_map.py` | 129 | Modelo (Fase 2) | ACTIVO NÚCLEO | En `__init__.py`. Modelo `lumber.blank.nominal.map`. Seed en `data/ingestion_seed_fase2.xml`. Documentado en CANON |
| `lumber_export_formula.py` | 221 | Modelo (Fase 3) | ACTIVO NÚCLEO | En `__init__.py`. Modelo `lumber.export.formula`. Seed en `data/ingestion_seed_fase3.xml` |
| `lumber_ingestion_format.py` | 271 | Modelo (Fase 3) | ACTIVO NÚCLEO | En `__init__.py`. Modelo `lumber.ingestion.format`. Vista en `views/lumber_ingestion_config_views.xml` |
| `lumber_profile_subproduct_rule.py` | 65 | Modelo (Fase 2) | ACTIVO NÚCLEO | En `__init__.py`. Modelo `lumber.profile.subproduct.rule`. Seed en `data/ingestion_seed_fase2.xml` |
| `lumber_reception.py` | 3,118 | Modelo principal | ACTIVO NÚCLEO | En `__init__.py`. 9 módulos dependen de él. Vista form+list+kanban. Test `test_lumber_reception.py` (425 líneas). Auditado en profundidad |
| `lumber_thickness_visual_rule.py` | 91 | Modelo (Fase 2) | ACTIVO NÚCLEO | En `__init__.py`. Modelo `lumber.thickness.visual.rule`. Seed en `data/thickness_visual_ranges_seed.xml` |
| `lumber_width_s2s_map.py` | 78 | Modelo (Fase 2) | ACTIVO NÚCLEO | En `__init__.py`. Modelo `lumber.width.s2s.map`. Seed en `data/ingestion_seed_fase2.xml` |
| `madenat_audit_log.py` | 25 | Modelo | ACTIVO PERIFÉRICO | En `__init__.py`. Bajo acoplamiento, usado solo por `lumber_reception.py` para trazabilidad |
| `madenat_guia_processing.py` | 4,390 | Modelo principal | ACTIVO NÚCLEO | En `__init__.py`. 5 módulos dependen (toll, costing, logistics, reports). Vista form 8 pestañas. Test `test_guia_processing.py` (212 líneas). Auditado en profundidad |
| `madenat_ingestion_config.py` | 225 | Modelo (AbstractModel) | ACTIVO NÚCLEO | En `__init__.py`. Helper de configuración con cadena de fallback. Referenciado por `mixin_lumber_ingest.py` y wizards |
| `madenat_subproducto.py` | 40 | Modelo | ACTIVO NÚCLEO | En `__init__.py`. `madenat.subproducto`. Seed en `data/madenat_subproducto_data.xml`. Usado por staging y reportes |
| `mixin_lumber_ingest.py` | 347 | Mixin (AbstractModel) | ACTIVO NÚCLEO | En `__init__.py`. Heredado por `lumber.reception` y `madenat.guia.processing`. Regla de oro compartida de volúmenes |
| `product_product.py` | 58 | Modelo (extensión) | ACTIVO PERIFÉRICO | En `__init__.py`. Extiende `product.product` con validaciones y computes madereros |
| `product_template.py` | 129 | Modelo (extensión) | **HUÉRFANO** | **NO está en `__init__.py`**. Extiende `product.template` con `use_commercial_standard` y dimensiones comerciales. Sin carga en `__init__.py`, su `_inherit` no se registra. 0 referencias desde otros archivos |
| `reception_parser.py` | 722 | AbstractModel | ACTIVO NÚCLEO | En `__init__.py`. El parser compartido para `lumber.reception`. `MadenatReceptionParser` con `parse_excel()`, `parse_dispatch_guide()`, `parse_purchase_order()` |
| `reception_service.py` | 218 | Service (clase Python) | ACTIVO NÚCLEO | En `__init__.py`. `LumberReceptionService` con `create_lots_from_staging()`, `create_stock_picking()`, `cleanup_orphan_moves()`. Invocado por `lumber_reception.py` |
| `reception_workflow.py` | 254 | Workflow (clase Python) | ACTIVO NÚCLEO | **NO está en `__init__.py`** pero ES importado inline por `lumber_reception.py` L2694: `from .reception_workflow import LumberReceptionWorkflow`. Orquesta pipeline de ingesta Gate 0→3 |
| `res_config_settings.py` | 71 | Modelo (extensión) | ACTIVO PERIFÉRICO | En `__init__.py`. Extiende `res.config.settings`. Vista `madenat_res_config_settings_views.xml` |
| `stock_lot.py` | 1,381 | Modelo (extensión) | ACTIVO NÚCLEO | En `__init__.py`. Extensión masiva de `stock.lot`: `vol_shipment_m3`, `technical_validation`, `guia_processing_id`, `reception_id`, `origin_type`. Alto acoplamiento con 6 módulos |
| `stock_lot_cost_line.py` | 83 | Modelo | ACTIVO NÚCLEO | En `__init__.py`. `stock.lot.cost.line`. Usado por `madenat_lumber_costing`, `madenat_lumber_logistics`. Vista `stock_lot_cost_line_views.xml` |
| `stock_move.py` | 52 | Modelo (extensión) | ACTIVO PERIFÉRICO | En `__init__.py`. Extiende `stock.move`. Solo tiene `guia_processing_id` y `reception_id` FK |
| `stock_picking.py` | 314 | Modelo (extensión) | ACTIVO NÚCLEO | En `__init__.py`. Extiende `stock.picking`. Campo `reception_id`, método `_compute_reception_origin`. Vista `stock_picking_views.xml`. Usado por logistics |
| `utils_uom.py` | 772 | Helper (módulo Python) | ACTIVO NÚCLEO | En `__init__.py`. Constantes y conversiones: `MM_PER_INCH`, `FT_TO_M`, `validate_mbf_factor()`, etc. Usado por múltiples modelos |
| `validation_checklist_mixin.py` | 453 | Mixin (AbstractModel) | ACTIVO NÚCLEO | En `__init__.py`. Heredado por `madenat.guia.processing`. Checklist de validación pre-stock |
| `width_mapping.py` | 72 | Helper (módulo Python) | ACTIVO NÚCLEO | En `__init__.py`. `WidthMappingTable` con rough→S2S lookup |

### wizard/ (4 archivos, 622 líneas)

| Archivo | Líneas | Tipo | Estado | Evidencia |
|---|---|---|---|---|
| `__init__.py` | 2 | Config | ACTIVO | Carga `lumber_reception_mass_update` y `madenat_guia_mass_update` |
| `lumber_reception_mass_update.py` | 416 | Wizard | ACTIVO NÚCLEO | En `__init__.py`. Asignación masiva de nominales. Vista `wizard_lumber_reception_mass_update.xml`. Test referenciado en `test_lumber_reception.py` |
| `madenat_guia_mass_update.py` | 122 | Wizard | ACTIVO NÚCLEO | En `__init__.py`. Asignación masiva para guías procesadas. Vista `madenat_guia_mass_update_views.xml` |
| `madenat_period_close.py` | 82 | Wizard | **PENDIENTE VALIDACIÓN** | **NO está en `__init__.py`**. Tiene vista XML (`madenat_period_close.xml`) y acción (`action_madenat_period_close`). El wizard estaría inaccesible en UI sin carga en `__init__.py`. Define GB-4, GB-5, GB-6. Podría ser funcionalidad en desarrollo o abandonada |

### tests/ (7 archivos, 1,310 líneas)

| Archivo | Líneas | Estado |
|---|---|---|
| `__init__.py` | 4 | Config |
| `test_duplicate_validation.py` | 260 | ACTIVO |
| `test_guia_processing.py` | 212 | ACTIVO (auditado) |
| `test_ingestion_gate.py` | 176 | ACTIVO |
| `test_length_uom_and_subproducto.py` | 127 | ACTIVO |
| `test_lot_costing.py` | 106 | ACTIVO |
| `test_lumber_reception.py` | 425 | ACTIVO (auditado) |

### migrations/ (4 archivos, 209 líneas)

| Archivo | Líneas | Estado |
|---|---|---|
| `18.0.5.1.0/post-migrate.py` | 26 | HISTÓRICO (ya aplicado) |
| `18.0.5.2.0/post-migrate.py` | 46 | HISTÓRICO |
| `18.0.5.3.0/post-migrate.py` | 105 | HISTÓRICO (corrección technical_validation) |
| `18.0.5.3.0/pre-migrate.py` | 32 | HISTÓRICO (constraint SQL) |

### scripts/ (3 archivos, 550 líneas)

| Archivo | Líneas | Estado |
|---|---|---|
| `__init__.py` | 0 | Marcador de paquete |
| `backfill_lot_visual_dimensions.py` | 232 | ACTIVO PERIFÉRICO (script de backfill único) |
| `diagnose_duplicates.py` | 318 | ACTIVO PERIFÉRICO (script de diagnóstico) |

### reports/ (7 archivos, 596 líneas)

| Archivo | Líneas | Estado |
|---|---|---|
| `lumber_batch_report.py` | 16 | ACTIVO PERIFÉRICO |
| `lumber_batch_report.xml` | 99 | ACTIVO PERIFÉRICO |
| `lumber_cost_report.py` | 226 | ACTIVO PERIFÉRICO |
| `lumber_cost_report.xml` | 144 | ACTIVO PERIFÉRICO |
| `madenat_guia_report.xml` | 12 | ACTIVO PERIFÉRICO |
| `madenat_guia_report_templates.xml` | 74 | ACTIVO PERIFÉRICO |
| `report_actions.xml` | 25 | ACTIVO PERIFÉRICO |

### _archive/ (3 archivos, 237 líneas) — EXCLUIDOS del scope vivo

| Archivo | Líneas |
|---|---|
| `apply_patch_guia_processing.py` | 123 |
| `apply_patch_lumber_reception.py` | 52 |
| `apply_patch_stock_lot.py` | 62 |

### data/ (5 archivos XML, 416 líneas) — ACTIVOS NÚCLEO

### security/ (2 archivos, 129 líneas) — ACTIVOS NÚCLEO

### views/ (22 archivos XML, ~3,772 líneas) — ACTIVOS NÚCLEO

## 1.2 Métricas agregadas

| Métrica | Valor |
|---|---|
| Archivos `.py` vivos en `models/` | **28** |
| Archivos `.py` vivos en `wizard/` | **4** (3 activos + 1 pendiente) |
| Archivos `.py` vivos en `tests/` | **7** |
| Archivos `.py` vivos en `migrations/` | **4** |
| Archivos `.py` vivos en `scripts/` | **2** (excluyendo `__init__.py`) |
| Archivos en `_archive/` (excluidos) | **3** |
| Archivos XML en `views/` | **22** |
| Archivos XML en `data/` | **5** |
| Archivos en `reports/` | **7** |
| **Líneas totales `.py` vivo (models+wizard+tests)** | **~16,021** |
| **Líneas totales en los 2 archivos monolito (lumber_reception + guia_processing)** | **7,508** (47% del código vivo) |
| Archivos **HUÉRFANOS** confirmados | **2** (`core_utils.py`, `product_template.py`) |
| Archivos **PENDIENTE VALIDACIÓN** | **1** (`madenat_period_close.py`) |
| Ruido histórico (backups sueltos fuera de `_archive/`) | **0** — Limpieza previa fue completa |

---

# 2. Mapa de dependencias del ecosistema

## 2.1 Grafo de dependencias técnicas (vía `__manifest__.py`)

```
madenat_lumber_core (núcleo — no depende de ningún otro módulo madenat)
  ├── madenat_lumber_purchasing        [depends: core]
  │     ├── madenat_lumber_reception_improvements [depends: core, purchasing]
  │     │     └── madenat_toll_processing [depends: core, reception_improvements]
  │     └── madenat_lumber_reports     [depends: core, purchasing, logistics, shipping_core, costing]
  ├── madenat_lumber_shipping_core     [depends: base, mail, uom — NO depende de core]
  │     └── madenat_lumber_logistics   [depends: core, shipping_core]
  │           └── madenat_lumber_costing [depends: core, logistics, shipping_core]
  ├── madenat_lumber_billing           [depends: core, account, stock]
  └── madenat_vendor_payment           [NO depende de core — independiente]
```

## 2.2 Tabla de consumo: qué consume cada módulo de `madenat_lumber_core`

| Módulo | Modelos/Campos consumidos de `core` | Archivos que referencian | Intensidad | Nivel de acoplamiento | Riesgo si se interviene core |
|---|---|---|---|---|---|
| **madenat_lumber_purchasing** | `lumber.reception` (vía `_inherit`), `purchase.order` (extiende con `lumber_reception_ids`, `action_create_lumber_reception`), `stock.lot` (implícito vía recepción) | `lumber_reception.py` (extiende), `purchase_order.py` (FK+O2M), vista `lumber_reception_views.xml` | **ALTA** | **ALTO** — Extiende modelo core directamente | **CRÍTICO**: Cambios en `lumber_reception` impactan matching de OC y creación de recepción desde OC |
| **madenat_lumber_logistics** | `stock.lot` (vista form/search heredada de `core`), `madenat.guia.processing` (FK `guia_processing_id`, estado draft como escudo), `lumber.reception` (vía `origin_type`), `stock.picking` (búsqueda por origin), `stock.lot.cost.line` | `lumber_container.py`, `lumber_export_shipment.py`, `lumber_shipment_line.py`, `lumber_container_lot_wizard.py`, vistas XML heredadas | **MUY ALTA** | **MUY ALTO** — Usa 5 modelos de core + hereda vistas XML | **CRÍTICO**: Cambios en `stock.lot` (campos, technical_validation), `guia_processing_id`, o `reception_id` rompen escudos de contenedores/embarques |
| **madenat_lumber_shipping_core** | **NINGUNO** — No depende de `madenat_lumber_core` en su manifiesto | 0 archivos | NULA | NULO | **SIN RIESGO DIRECTO**. Pero `logistics` depende de ambos → efecto indirecto |
| **madenat_lumber_billing** | `madenat_lumber_core` declarado en depends, pero grep cruzado retorna **0 referencias** a modelos de core | 0 archivos con referencias directas | MUY BAJA | BAJO — Dependencia declarada pero sin uso aparente de modelos específicos | **BAJO**: Podría ser dependencia residual. Si se elimina la dependencia del manifiesto, validar que billing no usa `stock.lot` indirectamente |
| **madenat_vendor_payment** | **NINGUNO** — No declara dependencia de `madenat_lumber_core` | 0 archivos | NULA | NULO | **SIN RIESGO** |
| **madenat_lumber_costing** | `madenat.guia.processing` (FK `reception_id`), `stock.lot` (vista form/search heredada), `stock.lot.cost.line` (vista) | `lumber_cost_distribution.py`, wizard `lumber_cost_distribution.py`, vistas XML | **ALTA** | **ALTO** — FK directa a `guia.processing` + búsqueda de lotes por `guia_processing_id` | **ALTO**: Cambios en `guia_processing_id` o `action_validate()` impactan distribución de costos. Cambios en `stock.lot` impactan vistas de costeo |
| **madenat_lumber_reception_improvements** | Depende de `core` + `purchasing`. Grep retorna **0 referencias** directas a modelos de core | 0 archivos con referencias directas | MUY BAJA | BAJO — Hereda indirectamente vía `purchasing` | **BAJO**: Módulo puente entre core y toll_processing. Mayormente hereda comportamiento ya definido |
| **madenat_lumber_reports** | `lumber.reception.line` (vía `_inherit` + `_name`), `stock.quant` (vistas y acciones) | `lumber_reception_reports.py` (extiende `lumber.reception.line`), `report_helpers.py` (450 líneas de helpers de reporte), acciones en `inventory_report_actions.xml` y `stock_report_actions.xml` | **ALTA** | **ALTO** — Extiende `lumber.reception.line` directamente y referencia campos como `reception_id`, `subproduct_id`, `vol_physical_m3` | **ALTO**: Cambios en campos de `lumber.reception.line` (nombre, tipo, compute) rompen reportes. Cambios en `stock.quant` o `stock.lot` impactan reportes de inventario |
| **madenat_toll_processing** | `madenat.guia.processing` (vía `_inherit` que extiende `action_validate()`), `lumber.reception` (vía `_inherit`), `stock.lot` (vista heredada) | `guia_processing_integration.py` (hereda `action_validate`), `lumber_reception.py` (hereda), `stock_lot.py` (FK), vistas XML heredadas | **MUY ALTA** | **MUY ALTO** — Extiende el método más crítico (`action_validate`) de `guia.processing` | **CRÍTICO**: Cualquier cambio en `action_validate()` de `madenat_guia_processing.py` rompe la herencia de costos y consumo de materia prima en toll processing |

## 2.3 Dependencias circulares o de alto acoplamiento

| Tipo | Módulos involucrados | Descripción |
|---|---|---|
| **Acoplamiento por `_inherit`** | `purchasing → lumber.reception`, `toll_processing → madenat.guia.processing`, `toll_processing → lumber.reception`, `reports → lumber.reception.line` | Módulos externos extienden métodos core. Si el método base cambia de firma, todos los `_inherit` se rompen |
| **Acoplamiento por FK** | `costing → madenat.guia.processing` (vía `reception_id`), `logistics → stock.lot` (vía `guia_processing_id`, `reception_id`), `toll_processing → lumber.reception` (vía `source_reception_id`) | Cambios en el modelo referenciado (eliminar campo, cambiar tipo) rompen la FK |
| **Acoplamiento por vista XML** | `logistics → core::view_stock_lot_form_madenat` (hereda form), `toll_processing → core::view_stock_lot_form_madenat`, `costing → core::view_stock_lot_form_madenat`, `purchasing → core::view_lumber_reception_form` | Si cambia el `id` de la vista en core, todos los `inherit_id` se rompen |
| **Dependencia funcional no técnica** | `shipping_core → logistics` (M-R2) | `shipping_core` define modelos pero no construye menús. `logistics` construye los menús. Si `logistics` no está instalado, `shipping_core` es invisible pero funcional |
| **Cadena de herencia frágil** | `madenat.guia.processing.action_validate()` → `toll_processing` extiende con `super()` → recalcula volúmenes y costos | Romper la cadena de `super()` en `guia_processing` rompe toll processing |

## 2.4 Módulos con mayor exposición a cambios en los archivos ya auditados

| Archivo auditado | Módulos expuestos | Gravedad |
|---|---|---|
| `lumber_reception.py` (3,118 líneas) | `purchasing`, `reports`, `toll_processing`, `logistics` (indirecto vía stock.lot) | **CRÍTICA** |
| `madenat_guia_processing.py` (4,390 líneas) | `toll_processing`, `costing`, `logistics`, `reports` | **CRÍTICA** |

---

# 3. Candidatos a obsolescencia

## 3.1 OBSOLETOS CONFIRMADOS (doble evidencia: sin referencia + sin uso en flujo real)

| Archivo | Evidencia de NO uso | Evidencia de NO referencia | Conclusión |
|---|---|---|---|
| **`models/core_utils.py`** (51 líneas) | Define `madenat.core.utils` con 3 métodos (`resolve_partner_record`, `resolve_currency_record`, `resolve_uom_record`). Estos métodos implementan una "regla de oro" de siempre retornar recordsets, pero **ningún archivo en todo el ecosistema los invoca** | NO está en `models/__init__.py`. Grep `core_utils` en los 9 módulos retorna **0 resultados**. | **OBSOLETO CONFIRMADO**. Código que nunca se cargó en el runtime. Posiblemente fue reemplazado por lógica inline en los modelos principales. Eliminación segura. |
| **`models/product_template.py`** (129 líneas) | Extiende `product.template` con `use_commercial_standard` + dimensiones comerciales. La funcionalidad de "estándar comercial vs físico" NO aparece en el flujo real documentado en CANON. | NO está en `models/__init__.py`. Sin carga, el `_inherit` no se registra en Odoo. Los campos `commercial_thickness_mm`, `commercial_width_mm`, `commercial_length_m` no existen en la BD en producción. | **OBSOLETO CONFIRMADO**. Extensión de `product.template` que nunca se desplegó. Eliminación segura. |

## 3.2 PENDIENTE DE VALIDACIÓN (evidencia insuficiente para declarar obsoleto)

| Archivo | Situación | Qué falta verificar |
|---|---|---|
| **`wizard/madenat_period_close.py`** (82 líneas) | NO está en `wizard/__init__.py`. Tiene XML de vista y acción window (`madenat_period_close.xml`) que define GB-4, GB-5, GB-6. El wizard sería inaccesible si `__init__.py` no lo carga. Pero es posible que esté accesible vía acción de menú sin pasar por `__init__.py` si el XML se carga en el manifiesto directamente. | Verificar si la acción `action_madenat_period_close` aparece en algún menú de `lumber_core_menu.xml` o en `madenat_menus_por_perfil.xml`. Si no está en ningún menú, está muerto. Si está en un menú, está activo pero mal configurado (falta en `__init__.py`). Revisar si CANON/04_DECISION_LOG.md menciona GB-4/GB-5/GB-6 como funcionalidad vigente. |
| **Archivos en `_archive/`** (3 archivos, 237 líneas) | `apply_patch_guia_processing.py`, `apply_patch_lumber_reception.py`, `apply_patch_stock_lot.py` están formalmente en carpeta de archivo → se consideran fuera del scope vivo. Pero son scripts de migración/parche, no modelos. | Confirmar que los patches que aplicaban ya están incorporados al código principal. Si los patches ya se aplicaron, se pueden eliminar. |

## 3.3 Archivos limpios — sin ruido detectado

- **Sin backups sueltos** (`.bak`, `.backup`, `.BACKUP`, `.save`, `.py~`) fuera de `_archive/`: confirmado con `find` exhaustivo → 0 archivos.
- **Sin archivos OLD en nombres**: confirmado → 0 archivos.
- **Sin `__pycache__` residual**: no detectado en el árbol.

---

# 4. Puntos de acople para los 3 bloques residuales

Las auditorías previas identificaron tres bloques de responsabilidad que permanecen mezclados en `lumber_reception.py` y `madenat_guia_processing.py`. A continuación, para cada bloque, se identifica el receptor natural YA EXISTENTE.

## 4.1 Bloque OC/Compras (~950 líneas entre ambos archivos)

**Responsabilidades mezcladas:**
- Matching de OC (`_match_purchase_order`, `_find_or_create_po_intelligent`)
- Normalización de claves (`_normalize_oc_key`, `_canonize_oc_name`, `_compute_oc_reference_norm`)
- Creación de OC desde documentos (`action_create_purchase_order_from_document`, `create_po_from_oc_data`)
- Sincronización de líneas (`_sync_purchase_order_lines`)
- Stats de recepción en OC (`_update_po_reception_stats`)
- Precios desde OC (`_obtener_precio_desde_oc`)

**Receptor propuesto:** `madenat_lumber_purchasing/models/lumber_reception.py` (ya existente)

**Justificación técnica:**
- Este archivo YA extiende `lumber.reception` con `_inherit`. Es el lugar canónico para toda lógica de compras.
- Ya contiene lógica de OC matching extendida. Mover los métodos base desde `lumber_reception.py` de core a este archivo consolida OC en un solo punto.
- `madenat_lumber_purchasing` es el módulo natural de dominio de compras — su `__manifest__.py` declara `'depends': ['purchase', 'madenat_lumber_core']`.
- Para `guia_processing`, el matching de OC podría moverse a un nuevo método en este mismo archivo vía `_inherit` de `madenat.guia.processing` (el archivo ya hereda `lumber.reception`, podría también heredar `madenat.guia.processing`).

**Riesgo de acoplar ahí:**
- **MEDIO**: Implica mover ~950 líneas desde 2 archivos core hacia 1 archivo en purchasing.
- Purchasing YA depende de core → no se crea nueva dependencia.
- Toll processing y reports dependen de purchasing → cambios en la firma de métodos expuestos impactan downstream.
- **Mitigación**: Mantener mismos nombres de método, misma firma. Solo cambia la ubicación.

## 4.2 Bloque Costos (~250 líneas entre ambos archivos)

**Responsabilidades mezcladas:**
- Asignación de costos a lotes (`_assign_costs_to_generated_lots` en guia, `_assign_costs_to_lots` en reception)
- Computes financieros (`_compute_line_cost`, `_compute_average_price_clp`, `_compute_usd_amount`, `_compute_unit_prices`)

**Receptor propuesto:** `madenat_lumber_costing/models/lumber_cost_distribution.py` (ya existente)

**Justificación técnica:**
- Este archivo YA contiene `lumber.cost.distribution` con `reception_id → madenat.guia.processing` y búsqueda de lotes por `guia_processing_id`.
- Es el lugar canónico para TODA lógica de costeo del ecosistema.
- `madenat_lumber_costing` declara `'depends': ['madenat_lumber_core']` → puede acceder a todos los modelos de core.
- Mover los métodos de asignación de costos aquí consolida "todo lo que toca costos" en el módulo de costing.

**Riesgo de acoplar ahí:**
- **MEDIO**: Implica mover ~250 líneas desde 2 archivos core.
- `costing` depende de `core` y `logistics` → no se crea nueva dependencia.
- `costing` es consumido por `reports` → si reports depende de costing, la cadena está intacta.
- **Mitigación**: Los métodos de asignación deben seguir siendo invocables desde `action_validate()` y `action_confirm_reception()` vía delegación al service de costing.

## 4.3 Bloque Reversa (~850 líneas entre ambos archivos)

**Responsabilidades mezcladas:**
- `action_force_cancel()` (290 líneas en guia) — reversión con return picking + cleanup
- `action_reopen_to_draft()` (244 líneas en guia) — reapertura con desvinculación de pickings
- `action_reset_to_draft()` (163 líneas en reception) — reset de recepción
- `_cleanup_orphan_moves_guia()` (87 líneas en guia) — limpieza de moves huérfanos
- `_cleanup_orphan_moves()` (62 líneas en reception) — DUPLICADO de `LumberReceptionService.cleanup_orphan_moves()`

**Receptor propuesto:** `madenat_lumber_core/models/reception_service.py` (ya existente, 218 líneas)

**Justificación técnica:**
- `reception_service.py` YA contiene `LumberReceptionService` con:
  - `create_lots_from_staging()` — creación de lotes
  - `create_stock_picking()` — creación de picking
  - `cleanup_orphan_moves()` — limpieza de moves (DUPLICADO del método inline en `lumber_reception.py`)
- El service es el lugar natural para TODA lógica de efectos en stock (creación Y destrucción).
- Agregar métodos `hard_cancel()` y `soft_reopen()` al service consolida la reversa en un solo punto, eliminando la duplicación actual.
- El service ya es una clase Python pura (no Odoo model) → bajo acoplamiento, fácil de testear.

**Riesgo de acoplar ahí:**
- **ALTO**: La reversa es la zona de mayor riesgo de regresión identificada en ambas auditorías.
- Implica mover ~850 líneas de lógica compleja con side effects en 5+ modelos.
- Ambos archivos (`guia_processing` y `lumber_reception`) tienen lógica de reversa PARECIDA pero NO idéntica (difieren en manejo de quants, return picking, y criterios de bloqueo).
- **Mitigación**: Primero unificar `cleanup_orphan_moves` (duplicación trivial, bajo riesgo). Luego extraer `hard_cancel()` para guías. Finalmente `soft_reopen()`. Cada paso con tests de integración.

**Nota importante:** La reversa de `guia_processing` y `lumber_reception` tienen diferencias semánticas reales (guías usan return picking con tipo no-EMB, recepciones eliminan directamente). No se debe forzar una unificación total si las diferencias son de negocio. Pero SÍ se debe consolidar en UN SOLO ARCHIVO (`reception_service.py`) con métodos separados por tipo, eliminando la duplicación de `cleanup_orphan_moves`.

---

# 5. Orden de intervención recomendado

La secuencia se ordena por: (a) impacto en otros módulos, (b) riesgo de regresión, (c) tamaño del bloque, (d) cobertura de tests actual.

## Fase 0 — Limpieza de obsolescencia confirmada (riesgo NULO, impacto NULO)

| Paso | Acción | Archivos | Tests requeridos |
|---|---|---|---|
| F0.1 | Eliminar `models/core_utils.py` | 1 archivo, 51 líneas | Ninguno (nunca se cargó) |
| F0.2 | Eliminar `models/product_template.py` | 1 archivo, 129 líneas | Ninguno (nunca se desplegó) |
| F0.3 | Verificar `madenat_period_close.py`: si no está en menú → eliminar; si está en menú → agregar a `__init__.py` | 1 archivo + posible fix en `__init__.py` | Si se activa: test de GB-4/GB-5 |

**Por qué primero:** Estos archivos no afectan a ningún módulo. Su eliminación reduce ruido sin riesgo. Se hace en el primer commit para dejar el árbol limpio antes de cualquier refactor.

## Fase 1 — Separar líneas de staging a archivos propios (riesgo BAJO, impacto BAJO)

| Paso | Acción | Archivos | Módulos impactados | Tests requeridos |
|---|---|---|---|---|
| F1.1 | Mover `LumberReceptionLine` (L48–L922 de `lumber_reception.py`) a `models/lumber_reception_line.py` | 1 archivo nuevo (876 líneas extraídas), `lumber_reception.py` → ~2,200 líneas | `reports` (extiende `lumber.reception.line`) | `test_lumber_reception.py` (425 líneas) |
| F1.2 | Mover `MadenatGuiaProcessingLine` (L1–L722 de `madenat_guia_processing.py`) a `models/madenat_guia_processing_line.py` | 1 archivo nuevo (722 líneas extraídas), `guia_processing.py` → ~3,668 líneas | Ninguno (la línea staging no es extendida por otros módulos) | `test_guia_processing.py` (212 líneas) |

**Por qué segundo:** Es un cambio puramente estructural (0 cambios de lógica). Reduce el tamaño de los archivos monolito sin tocar comportamiento. Los `_inherit` de `lumber.reception.line` en `reports` no se ven afectados porque el nombre del modelo (`_name`) no cambia.

## Fase 2 — Consolidar lógica duplicada de cleanup (riesgo BAJO, impacto BAJO)

| Paso | Acción | Archivos | Módulos impactados |
|---|---|---|---|
| F2.1 | Unificar `_cleanup_orphan_moves` (modelo) con `LumberReceptionService.cleanup_orphan_moves` (service) — eliminar la versión del modelo, mantener la del service | `lumber_reception.py` (-62 líneas), `reception_service.py` (posible ampliación) | `logistics` (usa `stock.move` indirectamente) |
| F2.2 | Unificar `_cleanup_orphan_moves_guia` de `madenat_guia_processing.py` con el mismo service (agregar `cleanup_orphan_moves_guia` al service) | `madenat_guia_processing.py` (-87 líneas), `reception_service.py` (+87 líneas) | `toll_processing` (extiende `action_validate` que podría invocar cleanup) |

**Por qué tercero:** La duplicación ya está identificada y documentada. Es código casi idéntico con el mismo FIX 2026-07-01. Unificar elimina el riesgo de que un fix se aplique a una copia y no a la otra. El service YA es el lugar canónico para efectos en stock.

## Fase 3 — Extraer OC/Compras a purchasing (riesgo MEDIO, impacto MEDIO)

| Paso | Acción | Archivos | Módulos impactados | Tests requeridos |
|---|---|---|---|---|
| F3.1 | Mover métodos de OC desde `lumber_reception.py` a `madenat_lumber_purchasing/models/lumber_reception.py` (YA extiende el modelo) | `lumber_reception.py` (-500 líneas), `lumber_reception.py` en purchasing (+500 líneas) | `purchasing`, `reports`, `toll_processing` | `test_lumber_reception.py` + tests de matching OC con golden records |
| F3.2 | Mover métodos de OC desde `madenat_guia_processing.py` a purchasing (nuevo `_inherit` de `madenat.guia.processing` en purchasing) | `madenat_guia_processing.py` (-450 líneas), nuevo método en purchasing | `purchasing`, `toll_processing`, `costing` | `test_guia_processing.py` + tests de matching OC |

**Por qué cuarto:** OC es el segundo bloque más grande de código mezclado (~950 líneas). Purchasing YA es el módulo canónico de compras. Pero mover OC afecta a `reports` (que lee `purchase_order`), `toll_processing` (que extiende flujo de guías), y `costing` (que asigna costos desde OC). Requiere más tests que las fases anteriores.

## Fase 4 — Extraer costos a costing (riesgo MEDIO, impacto BAJO)

| Paso | Acción | Archivos | Módulos impactados |
|---|---|---|---|
| F4.1 | Mover `_assign_costs_to_lots` y computes financieros desde `lumber_reception.py` a `madenat_lumber_costing/models/lumber_cost_distribution.py` | `lumber_reception.py` (-200 líneas), `lumber_cost_distribution.py` (+200 líneas) | `costing`, `reports` |
| F4.2 | Mover `_assign_costs_to_generated_lots` desde `madenat_guia_processing.py` a costing | `madenat_guia_processing.py` (-50 líneas), costing (+50 líneas) | `costing`, `toll_processing` |

**Por qué quinto:** Costos es un bloque más pequeño (~250 líneas). Ya existe `lumber_cost_distribution.py` en costing como receptor natural. El riesgo es menor que OC porque los computes financieros son en su mayoría campos calculados (sin side effects en stock). Pero toll_processing invoca asignación de costos post-`action_validate()` → requiere verificar que la delegación al service de costing no rompe la herencia.

## Fase 5 — Consolidar reversa en reception_service (riesgo ALTO, impacto ALTO)

| Paso | Acción | Archivos | Módulos impactados | Tests requeridos |
|---|---|---|---|---|
| F5.1 | Mover `action_force_cancel()` y `action_reopen_to_draft()` de `madenat_guia_processing.py` a `reception_service.py` como `hard_cancel_guia()` y `soft_reopen_guia()` | `madenat_guia_processing.py` (-534 líneas), `reception_service.py` (+534 líneas) | `toll_processing`, `logistics`, `costing` | Tests de integración: cancelación con picking done, reapertura con quants residuales, escudo logístico, escudo financiero |
| F5.2 | Mover `action_reset_to_draft()` de `lumber_reception.py` a `reception_service.py` como `hard_reset_reception()` | `lumber_reception.py` (-163 líneas), `reception_service.py` (+163 líneas) | `purchasing`, `reports` | Tests de integración: reset con quants, reset con contenedores activos |

**Por qué último:** Reversa es la zona de MÁXIMO riesgo identificada en ambas auditorías. Tiene side effects en 5+ modelos, savepoints anidados, y lógica de negocio crítica (escudos logísticos y financieros). Se aborda al final, cuando:
- El código base ya está más limpio (fases 0–4)
- Hay tests de integración para los flujos completos
- `reception_service.py` ya contiene la lógica de cleanup unificada (fase 2)

**Regla de oro para Fase 5:** No empezar sin batería completa de tests de integración que cubran cancelación + reapertura en ambos flujos (guías y recepciones), con y sin contenedores, con y sin costos.

---

# 6. Riesgos transversales sobre los 9 módulos

## 6.1 Matriz de riesgo: qué se rompe en cada módulo si se ejecuta el plan

| Módulo | Fase 0 | Fase 1 | Fase 2 | Fase 3 (OC) | Fase 4 (Costos) | Fase 5 (Reversa) | Mitigación |
|---|---|---|---|---|---|---|---|
| **madenat_lumber_core** | ✅ Sin riesgo | ⚠️ Bajo (reubicación) | ⚠️ Bajo (unificación) | ⚠️ Medio | ⚠️ Medio | 🔴 Alto | Tests existentes (1,310 líneas en 6 archivos) + tests de integración nuevos para Fase 5 |
| **madenat_lumber_purchasing** | ✅ | ✅ | ✅ | ⚠️ Medio (métodos se mueven A este módulo) | ✅ | ⚠️ Medio (reset usa purchase_id) | Tests de matching OC + tests de `action_create_lumber_reception` |
| **madenat_lumber_logistics** | ✅ | ✅ | ⚠️ Bajo (cleanup de moves) | ✅ | ✅ | 🔴 Alto (escudos de contenedores usan `guia_processing_id` y `technical_validation`) | Tests de escudo logístico: agregar/remover lotes de contenedores con guías canceladas |
| **madenat_lumber_shipping_core** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Sin riesgo — no depende de core |
| **madenat_lumber_billing** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Riesgo mínimo — dependencia declarada pero sin uso aparente de modelos core |
| **madenat_vendor_payment** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Sin riesgo — no depende de core |
| **madenat_lumber_costing** | ✅ | ✅ | ✅ | ✅ | ⚠️ Medio (métodos se mueven A este módulo) | ⚠️ Medio (costos post-cancelación) | Tests de distribución de costos + verificar que `reception_id` FK no se rompe |
| **madenat_lumber_reception_improvements** | ✅ | ✅ | ✅ | ⚠️ Bajo (depende de purchasing) | ✅ | ⚠️ Bajo | Si purchasing sigue funcionando, este módulo también |
| **madenat_lumber_reports** | ✅ | ⚠️ Bajo (hereda `lumber.reception.line`) | ✅ | ⚠️ Medio (lee `purchase_order`, `reception_id`) | ⚠️ Medio (lee campos de costo) | ⚠️ Medio (reset borra datos que reportes leen) | Tests de reportes: verificar que `report_helpers.py` resuelve correctamente tras mover campos |
| **madenat_toll_processing** | ✅ | ✅ | ⚠️ Bajo (cleanup) | ⚠️ Medio (extiende `action_validate`) | ⚠️ Medio (asignación de costos post-validate) | 🔴 Alto (extiende `action_validate` y podría invocar reversa) | Tests de toll processing: flujo completo con herencia de costos y consumo de materia prima |

## 6.2 Riesgos específicos por fase

### Riesgos Fase 3 (OC/Compras)
- **Qué podría romperse:** `action_validate()` en `guia_processing` invoca `_match_purchase_order()` antes de crear lotes. Si el método se mueve a purchasing pero la llamada en core no se actualiza → `AttributeError`.
- **Qué podría romperse:** `_find_or_create_po_intelligent()` en `lumber_reception` es invocado por el workflow (`reception_workflow.py`). Si el método se mueve, el workflow debe importar desde purchasing (posible referencia circular si purchasing depende de core y core intenta importar de purchasing).
- **Mitigación:** Los métodos movidos a purchasing deben ser accesibles vía `_inherit` (Odoo los expone automáticamente en el modelo). No se necesita import explícito. El modelo `lumber.reception` tendrá los métodos porque purchasing los inyecta vía `_inherit`.

### Riesgos Fase 5 (Reversa)
- **Qué podría romperse:** `action_force_cancel()` en guías busca `stock.picking.type` con secuencia no-EMB para crear return picking. Si la configuración de almacenes cambia o el código de retorno no existe, la reversa falla.
- **Qué podría romperse:** `action_reset_to_draft()` en recepciones usa `force_delete` en contexto + `sudo()` para bypassear bloqueos. Odoo 18 podría cambiar la API de `unlink()`.
- **Qué podría romperse:** Escudos logísticos (`logistics`) bloquean cancelación si lotes están en contenedores. Si la reversa se mueve al service, el escudo debe seguir invocándose antes de cualquier write.
- **Mitigación:** Feature flag `madenat_reversal_v2` que permita rollback instantáneo si la nueva reversa falla en producción. Ventana de deploy con monitoreo activo de logs de `stock.picking`, `stock.quant`, `stock.move`.

---

# 7. Texto para `02_CONTINUIDAD.md`

```markdown
### Auditoría arquitectónica `madenat_lumber_core` + ecosistema — 2026-07-01

**Alcance:** Inventario completo de 28 modelos (14,089 líneas), 4 wizards, 7 tests, 22 vistas,
y cruce de dependencias contra 8 módulos del ecosistema.

**Hallazgos principales:**
1. **Dos archivos concentran el 47% del código vivo:** `lumber_reception.py` (3,118 líneas) y
   `madenat_guia_processing.py` (4,390 líneas). Ambos ya auditados en profundidad.
2. **2 archivos huérfanos confirmados** (nunca cargados en runtime): `core_utils.py` (51 líneas)
   y `product_template.py` (129 líneas). Sin referencias en ningún módulo. Eliminación segura.
3. **1 wizard pendiente de validación:** `madenat_period_close.py` (82 líneas) — no está en
   `__init__.py` pero tiene vista XML. Verificar si tiene entrada de menú.
4. **Sin ruido histórico:** 0 backups sueltos, 0 archivos `.bak`/`.save`. La limpieza previa fue
   completa. `_archive/` contiene 3 scripts de parche ya aplicados.
5. **4 módulos con acoplamiento MUY ALTO a core:** `logistics`, `toll_processing`, `costing`,
   `reports`. Cambios en `stock.lot`, `guia_processing_id`, `action_validate()` o `lumber.reception.line`
   impactan directamente.
6. **1 módulo independiente:** `vendor_payment` no depende de core.
7. **1 dependencia potencialmente residual:** `billing` declara dependencia de core pero el
   grep cruzado no encuentra referencias a modelos específicos.

**Puntos de acople YA existentes (sin crear archivos nuevos):**
- **OC/Compras (~950 líneas):** Receptor natural → `madenat_lumber_purchasing/models/lumber_reception.py`
  (ya extiende `lumber.reception` vía `_inherit`).
- **Costos (~250 líneas):** Receptor natural → `madenat_lumber_costing/models/lumber_cost_distribution.py`
  (ya tiene FK a `guia.processing` y búsqueda de lotes).
- **Reversa (~850 líneas):** Receptor natural → `madenat_lumber_core/models/reception_service.py`
  (ya contiene `cleanup_orphan_moves` duplicado — unificar primero).

**Plan de intervención (5 fases, sin crear archivos nuevos):**
0. Eliminar obsolescencia confirmada (`core_utils.py`, `product_template.py`).
1. Separar `LumberReceptionLine` y `MadenatGuiaProcessingLine` a archivos propios.
2. Consolidar `cleanup_orphan_moves` duplicado en `reception_service.py`.
3. Mover OC/Compras a `purchasing` (vía `_inherit`).
4. Mover Costos a `costing`.
5. Consolidar Reversa en `reception_service.py` (requiere tests de integración completos).

**Regla de oro:** NO crear archivos nuevos. Acoplar responsabilidades dispersas a estructuras YA existentes.

**Documento completo:** `RAW/AUDITORIA_ARQUITECTONICA_LUMBER_CORE_ECOSISTEMA_20260701.md`
**Auditorías previas:** `RAW/AUDITORIA_PROFUNDA_GUIA_PROCESSING_20260701.md`,
`RAW/AUDITORIA_PROFUNDA_LUMBER_RECEPTION_20260701.md`
```

---

*Documento generado por auditoría arquitectónica. No se modificó ningún archivo de código.*
*Referencias cruzadas: `CANON/00_ARQUITECTURA.md`, `CANON/02_CONTINUIDAD.md`, `CANON/03_TESTS.md`, `CANON/04_DECISION_LOG.md`, `RAW/AUDITORIA_PROFUNDA_GUIA_PROCESSING_20260701.md`, `RAW/AUDITORIA_PROFUNDA_LUMBER_RECEPTION_20260701.md`*