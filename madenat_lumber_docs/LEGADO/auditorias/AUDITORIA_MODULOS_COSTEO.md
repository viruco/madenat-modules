# AUDITORÍA DETALLADA — Módulos, Costeo y Documentación

**Proyecto**: MADENAT Lumber — Odoo 18 CE  
**Fecha**: 2026-06-04  
**Estado**: COMPLETO — 11 módulos auditados  
**Propósito**: Confirmar rol real, documentación, estado monetario y participación en costeo/contabilidad de cada módulo antes de iniciar Fase A.

---

# 1. `madenat_lumber_core` — NÚCLEO FUNCIONAL

## 1.1 Rol real
Núcleo operativo del sistema MADENAT. Contiene:
- **Recepción de madera bruta**: `lumber.reception` + `lumber.reception.line` (2573 líneas)
- **Guías de procesamiento**: `madenat.guia.processing` + `.line` (3334 líneas)
- **Lotes extendidos**: `stock.lot` (1392 líneas) con dimensiones, volúmenes, costos, genealogía
- **Líneas de costo**: `stock.lot.cost.line` (84 líneas) — modelo canónico de costos por lote
- **Extensiones de stock**: `stock.move`, `stock.picking`, `stock.quant`
- **Utilidades**: `utils_uom.py`, `width_mapping.py`
- **Configuración**: `madenat_ingestion_config.py`, `lumber_export_formula.py`, `lumber_ingestion_format.py`, `madenat_subproducto.py`
- **Componentes desacoplados**: `reception_parser.py`, `reception_service.py`, `reception_workflow.py`
- **Mixins**: `mixin_lumber_ingest.py`, `ingestion_gate.py`

## 1.2 Documentación

| Documento | Existe | Estado | Observación |
|-----------|--------|--------|-------------|
| `README.md` | ✅ | Actualizado | Correcto |
| `CHANGELOG.md` | ✅ | Actualizado (HOTFIX v4, 2026-06-04) | Correcto |
| `CANON/` | ✅ | 9 archivos | `00_ARQUITECTURA.md`, `02_CONTINUIDAD.md`, `04_DECISION_LOG.md`, `05_BACKLOG.md` cubren core |
| `WIKI/` | ✅ | 7+ archivos | `modelo_lotes.md`, `modelo_recepciones.md`, `gates_validacion.md`, `servicio_lotes.md`, `validadores_checklist.md`, `configuracion_ingesta.md`, `arquitectura_ingesta_recepciones.md` |
| Auditorías | ✅ | 2 | `AUDITORIA_2026-06-03.md` (267 líneas), `AUDITORIA_2026-06-04.md` (318 líneas) |
| `ROADMAP.md` | ⚠️ | En `models/` | **Ubicación incorrecta** — debería estar en `CANON/` o `WIKI/` |

**Veredicto documentación**: COMPLETA (con un hueco menor de ubicación de `ROADMAP.md`)

## 1.3 Base monetaria

| Archivo | Campos Float monetarios | Cantidad |
|---------|------------------------|----------|
| `stock_lot.py` | `purchase_price_usd_per_m3`, `purchase_exchange_rate`, `purchase_amount_usd`, `purchase_amount_clp`, `wood_cost_usd`, `purchase_cost_usd`, `lot_exchange_rate`, `total_cost_usd`, `cost_per_m3_usd`, `cost_per_mbf_usd`, `sale_price_usd_per_mbf`, `sale_amount_usd`, `margin_usd`, `margin_percent` | **14** |
| `lumber_reception.py` | `exchange_rate`, `total_amount_clp`, `total_amount_usd`, `price_per_m3_usd`, `average_price_m3`, `price_per_mbf_usd` | **6** |
| `stock_lot_cost_line.py` | `amount_usd` (sin `currency_id`) | **1** |

**Total**: 21 campos Float monetarios. **Ninguno** usa `fields.Monetary`.

**Veredicto monetario**: ❌ CRÍTICO — requiere migración completa a `fields.Monetary` con `currency_field`.

## 1.4 Participación en costeo/contabilidad

| Componente | Estado |
|------------|--------|
| Define costo base de madera | ✅ `wood_cost_usd`, `purchase_amount_usd` |
| Define modelo canónico de línea de costo | ✅ `stock.lot.cost.line` |
| Calcula costo total | ✅ `total_cost_usd = wood_cost + purchase_cost + sum(cost_lines)` |
| Calcula costo por m³ | ✅ `cost_per_m3_usd` (incompleto — excluye `wood_cost`) |
| Genera `account.move` | ❌ |
| Genera `stock.landed.cost` | ❌ |
| Genera `stock.valuation.layer` | ❌ |

## 1.5 Huecos detectados

1. **`purchase_cost_usd` es código muerto**: default 0.0, nunca asignado en ningún módulo
2. **`wood_cost_usd` y `purchase_amount_usd` miden lo mismo**: dos campos para el mismo concepto
3. **`cost_per_m3_usd` excluye `wood_cost_usd`**: el costo por m³ está incompleto
4. **`total_cost_usd` es `store=False`**: no persiste, impide reportes históricos
5. **21 campos Float monetarios**: deben migrar a `fields.Monetary`
6. **`stock.lot.cost.line` sin `currency_id`**: requerido para `Monetary`
7. **`stock.lot.cost.line` sin `account_id`**: requerido para integración contable
8. **`stock_lot_check_cost_positive` constraint**: `CHECK(total_cost_usd >= 0)` — como `total_cost_usd` es compute no-store, esta constraint es inefectiva

## 1.6 Prioridad para Fase A

**PRIORIDAD 0** — Es el módulo que define la columna vertebral del costeo. Sin migrar sus campos a Monetary, ningún otro módulo puede tener consistencia monetaria. Cambios requeridos:
1. Agregar `currency_id` a `stock.lot`
2. Migrar 14 campos Float a Monetary
3. Unificar costo base como `cost_line` con `cost_type='wood'`
4. Corregir `cost_per_m3_usd` para incluir wood_cost

---

# 2. `madenat_lumber_costing` — COSTEO OPERATIVO

## 2.1 Rol real
Módulo de costeo multi-nivel. Contiene:
- **Expediente de liquidación**: `lumber.cost.distribution` (315 líneas) — wizard de landed costs con 6 métodos de prorrateo
- **Extensión de lote**: `stock_lot_costing.py` (196 líneas) — agrega `logistic_cost_usd`, `process_cost_usd`, `costing_state`, `exchange_rate`, y overrides de `_compute_total_cost_usd`
- **Extensión de línea de costo**: agrega `distribution_id` y `lot_name_clean` a `stock.lot.cost.line`

## 2.2 Documentación

| Documento | Existe | Estado | Observación |
|-----------|--------|--------|-------------|
| `README.md` | ❌ | **NO EXISTE** | Deuda documental |
| `CHANGELOG.md` | ❌ | **NO EXISTE** | Deuda documental |
| `CANON/` | ❌ | Sin entrada específica | `04_DECISION_LOG.md` menciona costing indirectamente en AD-10, AD-23 |
| `WIKI/` | ❌ | Sin entrada específica | Sin documento técnico del motor de distribución |
| Auditorías | ⚠️ | Parcial | `AUDITORIA_2026-06-03.md` menciona `fields.Float` en costing pero no profundiza |

**Veredicto documentación**: DEUDA — sin README, CHANGELOG ni documentación canónica propia.

## 2.3 Base monetaria

| Archivo | Campos Float monetarios | Cantidad |
|---------|------------------------|----------|
| `lumber_cost_distribution.py` | `amount_original`, `exchange_rate`, `amount_usd` (compute), `amount_total` | **4** |
| `stock_lot_costing.py` | `logistic_cost_usd` (compute, store), `process_cost_usd` (compute, store), `other_cost_usd` (compute, store), `total_cost_clp` (compute, store), `exchange_rate` | **5** |

**Campos ya migrados a Monetary**: `additional_cost` en `madenat.guia.processing`, `service_unit_price_clp`.

**Veredicto monetario**: ⚠️ PARCIAL — 9 campos Float monetarios. El módulo tiene `currency_id` declarado pero no lo usa consistentemente.

## 2.4 Participación en costeo/contabilidad

| Componente | Estado |
|------------|--------|
| Motor de distribución de landed costs | ✅ `action_apply_costs()` con 6 métodos |
| Distribución por booking/contenedor | ✅ |
| Reversibilidad de costos | ✅ `action_reverse_costs()` |
| Blindaje anti-basura | ✅ Filtra lotes sin `ref` o volumen 0 |
| Trazabilidad de distribución | ✅ `distribution_id` en `stock.lot.cost.line` |
| Genera `account.move` | ❌ |
| Genera `stock.landed.cost` | ❌ |
| Genera `stock.valuation.layer` | ❌ |

## 2.5 Huecos detectados

1. **Sin documentación**: el motor de distribución más importante del sistema no tiene README ni WIKI
2. **`amount_original` es Float**: debe ser `Monetary` con `currency_field='currency_id'`
3. **`_compute_total_cost_usd` override**: en `stock_lot_costing.py` suma `logistic_cost_usd` al total del core, pero `logistic_cost_usd` ya es parte de `cost_line_ids` — posible doble conteo
4. **`costing_menus.xml` comentado** en `__manifest__.py` sin documentar por qué
5. **Sin tests**: el motor de prorrateo no tiene cobertura de tests

## 2.6 Prioridad para Fase A

**PRIORIDAD 1** — Es el segundo módulo en urgencia. Cambios requeridos:
1. Migrar `amount_original`, `amount_usd`, `exchange_rate` a Monetary
2. Verificar `_compute_total_cost_usd` override (posible doble conteo)
3. Agregar `journal_id` opcional para generar `stock.landed.cost`
4. Crear `README.md` y documentación WIKI

---

# 3. `madenat_lumber_billing` — FACTURACIÓN

## 3.1 Rol real
Consolidación de facturación de madera. Contiene:
- **Consolidación**: `lumber.billing.consolidation` + `.line` — agrupa lotes para facturar
- **Wizard de factura**: `lumber_billing_invoice_wizard.py` — genera `account.move`

## 3.2 Documentación

| Documento | Existe | Estado |
|-----------|--------|--------|
| `README.md` | ✅ | Correcto |
| `CHANGELOG.md` | ❌ | Sin changelog |
| `CANON/` | ❌ | Sin entrada específica |
| `WIKI/` | ❌ | Sin entrada específica |

**Veredicto documentación**: PARCIAL — README existe pero falta CHANGELOG y WIKI.

## 3.3 Base monetaria

✅ **YA MIGRADO A MONETARY**:
- `wood_cost_usd` = `fields.Monetary(currency_field='currency_id')`
- `real_wood_cost_usd` = `fields.Monetary`
- `estimated_wood_cost_usd` = `fields.Monetary`
- `variance_wood_cost_usd` = `fields.Monetary`

**Veredicto monetario**: ✅ CORRECTO — sin cambios requeridos en Fase A.

## 3.4 Participación en costeo/contabilidad

| Componente | Estado |
|------------|--------|
| Lee costos de lotes | ✅ `getattr(self.lot_id, 'wood_cost_usd', 0.0)` |
| Calcula variaciones | ✅ `variance = real - estimated` |
| Genera `account.move` | ✅ `lumber_billing_invoice_wizard.py` |
| Único módulo con integración contable real | ✅ |

## 3.5 Huecos detectados

1. **Sin CHANGELOG**: cambios no documentados
2. **Sin tests consolidados**: solo `test_billing_consolidation.py`
3. **Lee `wood_cost_usd` directamente del lote**: si el core migra a `cost_line_ids`, billing debe adaptarse (cambio menor)

## 3.6 Prioridad para Fase A

**PRIORIDAD 3** — Ya está migrado a Monetary. Solo necesita adaptarse cuando el core migre `wood_cost_usd` a `cost_line_ids`. Sin urgencia.

---

# 4. `madenat_lumber_logistics` — LOGÍSTICA

## 4.1 Rol real
Gestión de contenedores y logística física. Contiene:
- **Embarques**: `lumber.export.shipment`
- **Contenedores**: `lumber.container`
- **Costeo de embarque**: `lumber_shipment_costing.py` (261 líneas)

## 4.2 Documentación

| Documento | Existe | Estado |
|-----------|--------|--------|
| `README.md` | ✅ | Correcto |
| `CHANGELOG.md` | ✅ | Actualizado |
| `WIKI/02_TECNICO/madenat_lumber_logistics.md` | ✅ | Documento canónico de reglas de disponibilidad |

**Veredicto documentación**: COMPLETA.

## 4.3 Base monetaria

✅ **YA MIGRADO A MONETARY**:
- `total_shipment_costs_usd` = `fields.Monetary(currency_field='currency_id')`
- `total_cost_per_m3` = `fields.Monetary(currency_field='currency_id')`
- `currency_id` declarado correctamente

**Veredicto monetario**: ✅ CORRECTO — sin cambios requeridos en Fase A.

## 4.4 Participación en costeo/contabilidad

| Componente | Estado |
|------------|--------|
| Distribución de costos de embarque | ✅ `_deprecated_action_distribute_costs()` |
| Suma costos por booking | ✅ `_compute_cost_totals()` |
| Genera `account.move` | ❌ |
| Genera `stock.landed.cost` | ❌ |

## 4.5 Huecos detectados

1. **`_deprecated_action_distribute_costs` bypassea `cost_line_ids`**: escribe directo a `logistic_cost_usd` en `stock.lot` en lugar de inyectar `stock.lot.cost.line`. Esto rompe la arquitectura de fuente única de verdad.
2. **Sin tests**: el módulo no tiene tests

## 4.6 Prioridad para Fase A

**PRIORIDAD 2** — Ya migrado a Monetary. El método `_deprecated_action_distribute_costs` debe redirigirse para usar `cost_line_ids` en lugar de escribir directo al lote. Sin urgencia inmediata.

---

# 5. `madenat_lumber_purchasing` — COMPRAS

## 5.1 Rol real
Extensión del módulo `purchase` de Odoo para intake de datos de compra. Modelos: `purchase_intake.py`.

## 5.2 Documentación

| Documento | Existe | Estado |
|-----------|--------|--------|
| `README.md` | ❌ | Sin README |
| `CHANGELOG.md` | ⚠️ | Solo `CHANGELOG_FIX4_20241204.md` (antiguo) |
| `CANON/` | ❌ | Sin entrada |
| `WIKI/` | ❌ | Sin entrada |

**Veredicto documentación**: DEUDA.

## 5.3 Base monetaria

No define campos monetarios propios. Usa los de `purchase.order` de Odoo estándar.

**Veredicto monetario**: N/A — no aplica.

## 5.4 Participación en costeo/contabilidad

❌ No participa directamente. Es un módulo de intake de datos, no de costeo.

## 5.5 Prioridad para Fase A

**NO APLICA** — sin cambios requeridos en Fase A.

---

# 6. `madenat_lumber_shipping_core` — EMBARQUES BASE

## 6.1 Rol real
Booking y estructura base de embarques. Dependencia de `madenat_lumber_logistics`.

## 6.2 Documentación

| Documento | Existe | Estado |
|-----------|--------|--------|
| `README.md` | ❌ | Sin README |
| `CHANGELOG.md` | ❌ | Sin CHANGELOG |
| `docs/` | ⚠️ | Directorio existe pero sin contenido canónico |

**Veredicto documentación**: DEUDA.

## 6.3 Base monetaria

No define campos monetarios propios.

**Veredicto monetario**: N/A.

## 6.4 Participación en costeo/contabilidad

❌ No participa directamente. Es infraestructura.

## 6.5 Prioridad para Fase A

**NO APLICA** — sin cambios requeridos en Fase A.

---

# 7. `madenat_lumber_reports` — REPORTES

## 7.1 Rol real
Meta-módulo que remapea menús y agrupa reportes bajo un solo árbol de navegación. Depende de TODOS los demás módulos.

## 7.2 Documentación

| Documento | Existe | Estado |
|-----------|--------|--------|
| `README.md` | ❌ | Sin README |

**Veredicto documentación**: DEUDA.

## 7.3 Base monetaria

No define modelos propios. Solo `menu_remapping.xml` y `lumber_reports_menu.xml`.

**Veredicto monetario**: N/A.

## 7.4 Participación en costeo/contabilidad

❌ No participa. Es solo UI de menús.

## 7.5 Prioridad para Fase A

**NO APLICA** — sin cambios requeridos en Fase A.

---

# 8. `madenat_lumber_reception_improvements` — MEJORAS RECEPCIÓN

## 8.1 Rol real
Extensiones de UI y flujo para mejorar la experiencia de recepción. Modelos ligeros.

## 8.2 Documentación

| Documento | Existe | Estado |
|-----------|--------|--------|
| `README.md` | ✅ | Correcto |

**Veredicto documentación**: PARCIAL — tiene README pero falta CHANGELOG.

## 8.3 Base monetaria

No define campos monetarios propios.

**Veredicto monetario**: N/A.

## 8.4 Participación en costeo/contabilidad

❌ No participa.

## 8.5 Prioridad para Fase A

**NO APLICA**.

---

# 9. `madenat_toll_processing` — MAQUILA

## 9.1 Rol real
Procesamiento externo de madera (toll processing / maquila). Extiende `madenat.guia.processing`.

## 9.2 Documentación

| Documento | Existe | Estado |
|-----------|--------|--------|
| `README.md` | ✅ | Correcto |

**Veredicto documentación**: PARCIAL — README existe pero falta CHANGELOG y WIKI.

## 9.3 Base monetaria

✅ **YA MIGRADO A MONETARY**:
- `process_cost_per_m3` = `fields.Monetary(currency_field='currency_id')`
- `currency_id` declarado correctamente

**Veredicto monetario**: ✅ CORRECTO.

## 9.4 Participación en costeo/contabilidad

| Componente | Estado |
|------------|--------|
| Costo de proceso por m³ | ✅ `process_cost_per_m3` |
| Extiende guía de procesamiento | ✅ |

## 9.5 Prioridad para Fase A

**NO APLICA** — ya migrado a Monetary.

---

# 10. `madenat_vendor_payment` — PAGOS

## 10.1 Rol real
Gestión de pagos a proveedores. Modelos de pago, reportes de pago.

## 10.2 Documentación

| Documento | Existe | Estado |
|-----------|--------|--------|
| `README.md` | ✅ | Correcto |

**Veredicto documentación**: PARCIAL.

## 10.3 Base monetaria

⚠️ **USA FLOAT** para montos de pago:
- `amount_total` = `fields.Float`
- `amount_paid` = `fields.Float`

**Veredicto monetario**: ⚠️ PARCIAL — requiere migración a Monetary.

## 10.4 Participación en costeo/contabilidad

⚠️ Indirecta — gestiona pagos pero no participa en el flujo de costeo de inventario.

## 10.5 Prioridad para Fase A

**PRIORIDAD 3** — Requiere migración a Monetary pero no es bloqueante para la base contable del inventario.

---

# 11. `madenat_lumber_docs` — DOCUMENTACIÓN

## 11.1 Rol real
Repositorio de documentación canónica y técnica. **NO es un módulo Odoo** (carece de `__manifest__.py`).

## 11.2 Contenido

| Directorio | Contenido | Estado |
|-----------|-----------|--------|
| `CANON/` | 9 archivos: `00_ARQUITECTURA`, `01_FLUJO_PACKING`, `02_CONTINUIDAD`, `03_TESTS`, `04_DECISION_LOG`, `05_BACKLOG`, `06_CHECKLIST`, `07_TRABAJO_CON_IA`, `INDICE_DOCUMENTACION` | ✅ ACTIVO |
| `WIKI/02_TECNICO/` | `modelo_lotes.md`, `modelo_recepciones.md`, `gates_validacion.md`, `servicio_lotes.md`, `validadores_checklist.md`, `configuracion_ingesta.md`, `arquitectura_ingesta_recepciones.md`, `herencia_odoo_modelos.md`, `dependencias_modulos.md` | ✅ COMPLETO |
| Auditorías | `AUDITORIA_2026-06-03.md`, `AUDITORIA_2026-06-04.md` | ✅ RECIENTE |
| Análisis | `ANALISIS_INTEGRAL_INVENTARIO_TRADERS.md`, `PRE_FASE_A_AUDITORIA_MODULOS.md`, `P7_INVENTARIO_RESIDUOS.md` | ✅ NUEVO |

## 11.3 Documentación FALTANTE en CANON/WIKI

| Documento | Prioridad | Justificación |
|-----------|-----------|---------------|
| `CANON/08_COSTEO.md` | **ALTA** | Sin documento canónico de flujo de costeo end-to-end |
| `WIKI/02_TECNICO/costeo_distribucion.md` | **ALTA** | Sin documento técnico del motor `lumber.cost.distribution` |
| `WIKI/02_TECNICO/flujo_devoluciones.md` | **MEDIA** | Sin documentación de devoluciones |
| `WIKI/02_TECNICO/troubleshooting.md` | **MEDIA** | Sin guía de errores conocidos |
| `WIKI/02_TECNICO/dependencias_modulos.md` | **BAJA** | Existe pero no actualizado post-Fase 3 |

---

# RESUMEN EJECUTIVO

## Módulos que requieren cambios en Fase A

| Prioridad | Módulo | Cambio | Esfuerzo |
|-----------|--------|--------|----------|
| **0** | `madenat_lumber_core` | Migrar 21 campos Float → Monetary en `stock.lot` + `lumber.reception` + `stock.lot.cost.line` | 6-8h |
| **1** | `madenat_lumber_costing` | Migrar 9 campos Float → Monetary en `lumber.cost.distribution` + `stock_lot_costing` | 3-4h |
| **2** | `madenat_lumber_logistics` | Redirigir `_deprecated_action_distribute_costs` a `cost_line_ids` | 1-2h |
| **3** | `madenat_lumber_billing` | Adaptar lectura de `wood_cost_usd` cuando core migre | 0.5h |
| **3** | `madenat_vendor_payment` | Migrar `amount_total`, `amount_paid` a Monetary | 1-2h |

## Módulos sin cambios requeridos en Fase A

- `madenat_lumber_purchasing` — no define costos
- `madenat_lumber_shipping_core` — infraestructura
- `madenat_lumber_reports` — solo menús
- `madenat_lumber_reception_improvements` — solo UI
- `madenat_toll_processing` — ya migrado a Monetary

## Documentación a crear en Fase A

1. `CANON/08_COSTEO.md` — flujo canónico de costeo end-to-end
2. `WIKI/02_TECNICO/costeo_distribucion.md` — documentación del motor de distribución
3. `README.md` para `madenat_lumber_costing`
4. `CHANGELOG.md` para `madenat_lumber_costing`

## Veredicto final

La base funcional y operativa está sólida. La base monetaria está **fragmentada**: 3 módulos ya migraron a Monetary (billing, logistics, toll), 2 módulos requieren migración urgente (core con 21 campos, costing con 9 campos), y 1 módulo tiene deuda menor (vendor_payment). La documentación canónica es excelente pero falta el documento de costeo, que es crítico para la Fase A. Sin `stock.landed.cost` ni `stock.valuation.layer` en ningún módulo — esto es el entregable principal de la Fase A.

---

*Auditoría generada el 2026-06-04. Basada en evidencia de código de 19 archivos modelo, 12+ vistas XML, 9 documentos CANON, 7+ documentos WIKI, 2 auditorías recientes.*