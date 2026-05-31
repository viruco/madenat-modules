# MADENAT Ecosystem — Arquitectura Maestra v2.0

**Fecha de auditoría original:** 8 de mayo de 2026
**Fecha de actualización:** 12 de mayo de 2026
**Auditor:** Arquitecto externo (Perplexity) + GitHub Copilot
**Método de verificación:** grep -Rni sobre repositorio real en `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/`
**Estado:** ✅ DOCUMENTACIÓN SINCRONIZADA CON CÓDIGO REAL — 12 mayo 2026

> **NOTA CRÍTICA:** La documentación de `madenat_lumber_core/docs/` (04_DECISION_LOG.md, ROADMAP.md, CHECKLIST_FINALIZACION.md, 05_BACKLOG.md, MANIFEST_ENTREGA.md) **estaba desactualizada**. Describía como "tarea pendiente" la creación de `lumber.billing.consolidation.line`, cuando ese modelo ya existe, está instalado y en producción. Este documento v2.0 refleja el estado real verificado por grep.

---

## 1. Inventario del Ecosistema

| # | Módulo | Versión | Estado DB | Tests | DTs |
|---|--------|---------|-----------|-------|-----|
| 1 | madenat_lumber_shipping_core | 18.0.1.0.0 | installed | 0 | 2 |
| 2 | madenat_lumber_core | 18.0.5.0.0 | installed | 30 | 2 |
| 3 | madenat_lumber_logistics | 18.0.1.2.0 | installed | 0 | 0 |
| 4 | madenat_lumber_costing | 18.0.1.0.0 | installed | 0 | 0 |
| 5 | madenat_lumber_billing | 18.0.1.0.0 | installed | 1 | 0 |
| 6 | madenat_vendor_payment | 18.0.1.2.0 | installed | 0 | 2 |
| 7 | madenat_lumber_purchasing | 18.0.2.2.0 | installed | 0 | 1 |
| 8 | madenat_toll_processing | 18.0.1.0.0 | installed | 0 | 0 |
| 9 | madenat_lumber_reception_improvements | 18.0.1.0.0 | installed | 0 | 0 |
| 10 | madenat_lumber_reports | 18.0.1.0.0 | installed | 0 | 0 |
| — | madenat_lumber_import_valuations | — | uninstalled | — | — |
| — | madenat_lumber_inventory | — | uninstalled | — | — |
| — | madenat_lumber_processing | — | uninstalled | — | — |

**Total tests activos:** 31 (30 en lumber_core + 1 en billing)
**Total DTs activas:** 7 items
**Módulos sin tests:** 9/10 (riesgo sistémico)

---

## 2. Verificación por Grep — Estado Real del Código (12 mayo 2026)

### Resumen de hallazgos críticos

| Elemento investigado | Grep | Resultado | Impacto en documentación |
|---|---|---|---|
| `action_generate_billing_consolidation` | No encontrado en ningún archivo `.py` | ❌ **NO EXISTE AÚN** | Fase 6 sigue pendiente — método puente no implementado |
| `lumber.billing.consolidation.line` (_name) | `madenat_lumber_billing/models/lumber_billing_consolidation_line.py:16` | ✅ **EXISTE** | Docs de lumber_core decían "crear" — **ERROR DOCUMENTAL** |
| `lumber.billing.consolidation.line` (imports) | `madenat_lumber_billing/models/__init__.py:3` | ✅ **IMPORTADO** | Modelo activo en registry |
| `lumber.billing.consolidation.line` (ACL) | `madenat_lumber_billing/security/ir.model.access.csv:4` | ✅ **CON ACL** | Modelo accesible a usuarios |
| `_compute_is_billed` con guardia | `stock_lot.py:797` → `if 'lumber.billing.consolidation.line' not in self.env:` | ✅ **FIX YA APLICADO** | **DT-001 RESUELTA** — docs decían que era pendiente |
| `wood_cost_usd` en stock.lot | `madenat_lumber_core/models/stock_lot.py:820` | ✅ **EXISTE** | Campo definido en lumber_core, no en costing |
| `container_ids` en lumber.export.shipment | `lumber_export_shipment.py:145` → `fields.One2many('lumber.container', 'shipment_id', ...)` | ✅ **EXISTE** | Prerrequisito Fase 6 confirmado |
| `shipment_id` en billing | `lumber_billing_consolidation.py:62` y `lumber_billing_consolidation_line.py:71` | ✅ **EXISTE Y RELATED** | Relación completa ya definida |
| Fallback silencioso vendor_payment | `lumber_shipment_cost.py:277` → `MIGRATION PATH (4 niveles de fallback)` | ⚠️ **EXISTE** | DT-NEW-VP-002 sigue vigente |
| security.xml vs ir.model.access | Grupos `group_shipping_user/manager` definidos pero ACL usa `base.group_user` | ⚠️ **DESCONECTADO** | DT-NEW-SC-001 sigue vigente |

---

## 3. Estado Real de la Deuda Técnica (Post-grep)

| ID | Módulo | Severidad | Estado Real | Descripción | Acción |
|----|--------|-----------|-------------|-------------|--------|
| DT-001 | lumber_core | ✅ **RESUELTA** | Fix aplicado en `stock_lot.py:797` | Guardia de registry implementada | Actualizar docs que la marcan como pendiente |
| DT-002 | shipping_core | 🟢 BAJA | Pendiente | `shipping_models.py` no importado | `rm shipping_models.py` — safe delete |
| DT-NEW-SC-001 | shipping_core | 🟡 MEDIA | **Vigente** | `security.xml` define grupos no enlazados a ACL | Enlazar `group_shipping_user` a `ir.model.access.csv` |
| DT-NEW-LC-002 | lumber_core | 🟡 MEDIA | **Activable ahora** | T08 omitido — `lumber.billing.consolidation.line` YA EXISTE | Eliminar `_logger.warning` y activar T08 |
| DT-NEW-VP-001 | vendor_payment | 🟡 MEDIA | **Vigente** | Métodos LEGACY marcados como deprecados en `lumber_shipment_cost.py` | Revisar en sprint vendor_payment |
| DT-NEW-VP-002 | vendor_payment | 🔴 CRÍTICA | **Vigente** | Fallback a 4 niveles con cuentas hardcodeadas — solo warning, no error | Convertir a `UserError` |
| DT-NEW-PU-001 | purchasing | 🟡 MEDIA | **Vigente** | Comentarios LEGACY en `purchase_order.py` | Revisar en sprint purchasing |

### Cambio importante en DT-NEW-LC-002

Dado que `lumber.billing.consolidation.line` ya existe e instalado, el test T08 en `test_lumber_reception.py:201` puede activarse **ahora mismo** sin cambios de modelo. Solo requiere eliminar el bloque de warning que lo omite.

```python
# ANTES (test_lumber_reception.py:201) — REMOVER ESTE BLOQUE:
_logger.warning("Test 08 omitido temporalmente: falta modelo lumber.billing.consolidation.line")

# DESPUÉS: dejar que el test corra normalmente
# El modelo ya existe: madenat_lumber_billing/models/lumber_billing_consolidation_line.py:16
```

---

## 4. Mapa de Modelos por Módulo

### madenat_lumber_shipping_core
| Modelo | Tipo | Archivo |
|--------|------|---------|
| shipping.vessel | _name | shipping_vessel.py |
| shipping.voyage | _name | shipping_voyage.py |
| shipping.booking | _name | shipping_booking.py |
| shipping_models.py | CÓDIGO MUERTO | no importado en __init__.py |

### madenat_lumber_core
| Modelo | Tipo | Archivo |
|--------|------|---------|
| madenat.guia.processing | _name | madenat_guia_processing.py |
| madenat.guia.processing.line | _name | madenat_guia_processing.py |
| lumber.reception | _name | lumber_reception.py |
| lumber.reception.line | _name | lumber_reception.py |
| madenat.lumber.ingest.mixin | mixin | mixin_lumber_ingest.py |
| madenat.lumber.ingest.line.mixin | mixin | mixin_lumber_ingest.py |
| validation.checklist.mixin | mixin | validation_checklist_mixin.py |
| LumberReceptionWorkflow | mixin | reception_workflow.py |
| madenat.subproducto | _name | madenat_subproducto.py |
| madenat.audit.log | _name | madenat_audit_log.py |
| stock.lot | _inherit | stock_lot.py |
| stock.quant | _inherit | stock_lot.py |
| stock.picking | _inherit | stock_picking.py |
| stock.move | _inherit | stock_move.py |
| product.product | _inherit | product_product.py |

**Campos clave en stock.lot (lumber_core):**
- `wood_cost_usd` → `fields.Float` definido en `stock_lot.py:820` — **CONFIRMADO POR GREP**
- `purchase_cost_usd` → campo par de wood_cost_usd
- `total_cost_usd` → computado desde `wood_cost_usd + purchase_cost_usd + cost_line_ids.amount_usd` (línea 831)
- `is_billed` → computado con guardia de registry (línea 783-802) — **DT-001 YA RESUELTA**

### madenat_lumber_logistics
| Modelo | Tipo | Archivo |
|--------|------|---------|
| lumber.export.shipment | _name | lumber_export_shipment.py |
| lumber.shipment.cost.line | _name | lumber_export_shipment.py:871 |
| lumber.container | _name | lumber_container.py |
| lumber.shipment.line | _name | lumber_shipment_line.py |
| lumber.document.checklist | _name | lumber_document_checklist.py |
| lumber.shipment.document | _name | lumber_shipment_document.py |
| lumber.shipping.rule | _name | lumber_shipping_rule.py |
| lumber.export.shipment | _inherit (docs) | lumber_document_checklist.py:64 |
| lumber.export.shipment | _inherit (costs) | lumber_shipment_costing.py:9 |
| stock.lot | _inherit | stock_lot_logistics.py |

**Campos clave verificados por grep:**
- `container_ids` → `fields.One2many('lumber.container', 'shipment_id', 'Contenedores')` en `lumber_export_shipment.py:145` — **CONFIRMADO**
- `container_ids.lot_ids` → accesible vía `.mapped('lot_ids')` en múltiples métodos

### madenat_lumber_billing
| Modelo | Tipo | Archivo |
|--------|------|---------|
| madenat.billing.common | _name | billing_common.py |
| lumber.billing.consolidation | _name | lumber_billing_consolidation.py |
| lumber.billing.consolidation.line | _name | lumber_billing_consolidation_line.py |

**Estado verificado por grep — TODOS LOS COMPONENTES EXISTEN:**
- `_name = 'lumber.billing.consolidation.line'` → `lumber_billing_consolidation_line.py:16`
- `models/__init__.py:3` → `from . import lumber_billing_consolidation_line`
- `ir.model.access.csv:4` → ACL definida para `base.group_user`
- `lumber_billing_consolidation.py:114` → One2many a `lumber.billing.consolidation.line`
- `lumber_billing_invoice_wizard.py:277` → Many2one a `lumber.billing.consolidation.line`
- `billing_workflows.xml:120` → creación automática de líneas
- `wood_cost_usd` → definido en `lumber_billing_consolidation_line.py:130`
- `shipment_id` en consolidation → `lumber_billing_consolidation.py:62` (Many2one, required=True)
- `shipment_id` en line → `lumber_billing_consolidation_line.py:71` (related desde consolidation)

**Estados del workflow:** draft → ready_audit → billed / cancelled

---

## 5. Cadena de Valor — Flujo Financiero Completo

```
[RECEPCIÓN]
lumber.reception + lumber.reception.line
    │ stock.picking (via madenat_lumber_core)
    ▼
[INVENTARIO]
stock.lot (extendido por: lumber_core, logistics, costing, toll_processing)
    │ lumber_core escribe:
    │   wood_cost_usd (stock_lot.py:820) ← DEFINIDO EN CORE, no en costing
    │ madenat_lumber_costing escribe (vía _inherit):
    │   logistic_cost_usd, process_cost_usd, other_cost_usd, total_cost_clp
    ▼
[EMBARQUE]
lumber.export.shipment (definido en logistics)
    │ container_ids = One2many('lumber.container', ...) ← CONFIRMADO :145
    │   └── container.lot_ids → stock.lot
    │ lumber.shipment.cost.line (extendido por vendor_payment)
    │     └── vendor.payment.order → account.move (pagos a proveedor)
    ▼
[FACTURACIÓN] ← MODELO YA EXISTE — solo falta action_generate_billing_consolidation()
lumber.billing.consolidation (shipment_id REQUIRED, :62)
    └── lumber.billing.consolidation.line (_name confirmado :16)
            ├── lot_id → stock.lot (lee wood_cost_usd desde core)
            ├── container_id → lumber.container
            ├── shipment_id → related desde consolidation (:74)
            ├── wood_cost_usd → Monetary (:130), poblado desde lot_id.wood_cost_usd (:273)
            ├── cost_usd = wood + logistic + process + other (:216-225)
            ├── price_usd = quantity × price_unit_usd
            └── margin_usd / margin_percent (computados)
```

---

## 6. Cadena de Herencia — stock.lot

`stock.lot` es el modelo más extendido del ecosistema:

| Módulo | Archivo | Campos agregados | Estado |
|--------|---------|-----------------|--------|
| lumber_core | stock_lot.py | `wood_cost_usd` (:820), `is_billed` (:783), dimensiones, genealogía, trazabilidad | ✅ Confirmado |
| lumber_core | stock_lot_cost_line.py | `cost_line_ids` (One2many a stock.lot.cost.line) | ✅ Confirmado |
| logistics | stock_lot_logistics.py | `export_shipment_id`, `container_id` | ✅ Confirmado |
| costing | stock_lot_costing.py | `logistic_cost_usd`, `process_cost_usd`, `other_cost_usd`, `total_cost_clp` | ✅ Confirmado |
| toll_processing | stock_lot_toll.py | `toll_order_ids` | ✅ Confirmado |

**Orden crítico de carga en Odoo:** `lumber_core → logistics → costing → toll_processing`

### Jerarquía de costos en stock.lot

```
wood_cost_usd       (lumber_core, stock_lot.py:820)     ← precio compra madera
purchase_cost_usd   (lumber_core, stock_lot.py)          ← costo adicional compra
cost_line_ids       (lumber_core)                        ← líneas de costo granular
logistic_cost_usd   (costing, stock_lot_costing.py)      ← costo logístico distribuido
process_cost_usd    (costing, stock_lot_costing.py)      ← costo procesamiento
other_cost_usd      (costing, stock_lot_costing.py)      ← otros costos
total_cost_usd      (lumber_core, computed :831)         ← wood + purchase + cost_lines
total_cost_clp      (costing, computed)                  ← total en CLP
```

---

## 7. Deuda Técnica Consolidada — Estado Actualizado

| ID | Módulo | Severidad | Estado | Archivo | Descripción | Acción |
|----|--------|-----------|--------|---------|-------------|--------|
| DT-001 | lumber_core | ✅ RESUELTA | Fix en prod | stock_lot.py:797 | Guardia de registry ya aplicada | Actualizar docs en lumber_core |
| DT-002 | shipping_core | 🟢 BAJA | Pendiente | shipping_models.py | Código muerto no importado | `rm shipping_models.py` |
| DT-NEW-SC-001 | shipping_core | 🟡 MEDIA | Vigente | security/ | Grupos `group_shipping_user/manager` definidos pero ACL usa `base.group_user` | Enlazar grupos a ACL |
| DT-NEW-LC-002 | lumber_core | 🟡 MEDIA | **Activable YA** | tests/test_lumber_reception.py:201 | T08 omitido — modelo ya existe | Eliminar warning, activar T08 |
| DT-NEW-VP-001 | vendor_payment | 🟡 MEDIA | Vigente | lumber_shipment_cost.py | Métodos LEGACY explícitamente deprecados | Eliminar en sprint vendor_payment |
| DT-NEW-VP-002 | vendor_payment | 🔴 CRÍTICA | Vigente | lumber_shipment_cost.py:277 | 4 niveles de fallback — nivel 3 usa cuentas hardcodeadas sin error | Convertir a `UserError` |
| DT-NEW-PU-001 | purchasing | 🟡 MEDIA | Vigente | purchase_order.py | Comentarios LEGACY | Revisar en sprint purchasing |

**Prioridad de resolución:**
1. 🔴 DT-NEW-VP-002 — Asientos contables silenciosamente incorrectos (4 niveles fallback, último genérico sin error)
2. 🟡 DT-NEW-LC-002 — Activar T08 inmediatamente (costo: eliminar 1 línea de warning)
3. 🟡 DT-NEW-SC-001 — Seguridad permisiva en shipping_core
4. 🟡 DT-NEW-VP-001 — Código LEGACY en vendor_payment
5. 🟢 DT-002 — Safe delete cuando haya ventana de mantenimiento
6. ~~DT-001~~ — **YA RESUELTA**, solo falta actualizar documentación interna

---

## 8. Tests del Ecosistema

| Módulo | Archivo | Tests | Cobertura estimada |
|--------|---------|-------|--------------------|
| lumber_core | test_ingestion_gate.py | 16 | Gate 1-3 ingestion |
| lumber_core | test_lumber_reception.py | 14 | Recepción completa (T08 omitido — activar) |
| lumber_billing | test_billing.py | 1 | Flujo auditoría/aprobación |
| **TOTAL** | | **31** | |
| shipping_core | — | 0 | ❌ Sin cobertura |
| logistics | — | 0 | ❌ Sin cobertura |
| costing | — | 0 | ❌ Sin cobertura |
| vendor_payment | — | 0 | ❌ Sin cobertura |
| purchasing | — | 0 | ❌ Sin cobertura |
| toll_processing | — | 0 | ❌ Sin cobertura |

**Acción inmediata sobre T08:**

```python
# test_lumber_reception.py:201
# ANTES — ELIMINAR:
_logger.warning("Test 08 omitido temporalmente: falta modelo lumber.billing.consolidation.line")

# El modelo YA EXISTE en:
# madenat_lumber_billing/models/lumber_billing_consolidation_line.py:16
# El test puede correr si madenat_lumber_billing está en depends del test
```

---

## 9. Fase 6 — Estado Real y Trabajo Pendiente

### Qué existe (verificado por grep)

- ✅ `lumber.billing.consolidation` — modelo instalado, `shipment_id` required
- ✅ `lumber.billing.consolidation.line` — modelo instalado, `_name` en `:16`
- ✅ `wood_cost_usd` en `stock.lot` — campo Float en lumber_core `:820`
- ✅ `container_ids` en `lumber.export.shipment` — One2many confirmado `:145`
- ✅ `billing_workflows.xml` — ya itera `shipment.container_ids` y crea líneas (`:118-128`)
- ✅ Guardia de registry en `_compute_is_billed` — DT-001 resuelta `:797`

### Qué falta

- ❌ `action_generate_billing_consolidation()` en `lumber_export_shipment.py` — método de UI no encontrado por grep
- ❌ Botón en vista XML de `lumber.export.shipment` para disparar la acción
- ❌ Tests T15-T17 para cubrir el flujo shipment → consolidation

### Implementación pendiente

```python
# En madenat_lumber_logistics/models/lumber_export_shipment.py
# O en madenat_lumber_billing/models/lumber_billing_consolidation.py

def action_generate_billing_consolidation(self):
    """Genera consolidación de facturación desde el embarque."""
    self.ensure_one()

    # Verificar que no exista ya una consolidación para este embarque
    existing = self.env['lumber.billing.consolidation'].search([
        ('shipment_id', '=', self.id),
        ('state', 'not in', ['cancelled'])
    ], limit=1)
    if existing:
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'lumber.billing.consolidation',
            'res_id': existing.id,
            'view_mode': 'form',
        }

    # Crear la consolidación
    consolidation = self.env['lumber.billing.consolidation'].create({
        'shipment_id': self.id,
        'state': 'draft',
    })

    # Por cada lote en los contenedores del embarque
    for container in self.container_ids:
        for lot in container.lot_ids:
            self.env['lumber.billing.consolidation.line'].create({
                'consolidation_id': consolidation.id,
                'lot_id': lot.id,
                'container_id': container.id,
                # shipment_id viene por related desde consolidation_id.shipment_id
                'volume_m3': lot.volumen_m3,
                'wood_cost_usd': lot.wood_cost_usd or 0.0,
                'logistic_cost_usd': getattr(lot, 'logistic_cost_usd', 0.0),
                'process_cost_usd': getattr(lot, 'process_cost_usd', 0.0),
                'other_cost_usd': getattr(lot, 'other_cost_usd', 0.0),
            })

    return {
        'type': 'ir.actions.act_window',
        'res_model': 'lumber.billing.consolidation',
        'res_id': consolidation.id,
        'view_mode': 'form',
    }
```

**Nota sobre `volume_m3`:** en `stock.lot` el campo de origen es `volumen_m3` (con v española), definido como `fields.Float` en `stock_lot.py:614` y usado en cálculos de costo en `stock_lot.py` (líneas 1114, 1118, 1138, 1143-1144). En `lumber.billing.consolidation.line` el campo receptor es `volume_m3` (definido en `lumber_billing_consolidation_line.py:105`) y no es un alias del campo de `stock.lot`.

**Nota adicional:** `logistic_cost_usd`, `process_cost_usd` y `other_cost_usd` existen en `madenat_lumber_costing/models/stock_lot_costing.py` (líneas 90, 98 y 106) y son los valores que corresponden transferir desde `lot` a la línea de consolidación.

**Estimación:** 0.5 día de desarrollo + 0.5 día de tests (T15-T17)

---

## 10. Hoja de Ruta — Estado Actualizado

### Fases completadas

| Fase | Descripción | Estado |
|------|-------------|--------|
| 1-4 | Arquitectura modular, recepción, guías, refactor | ✅ Completo |
| 5 | Módulo billing con modelos base | ✅ **Completo** (verificado por grep) |

### Fases pendientes

| Fase | Descripción | Prerrequisito | Estimación |
|------|-------------|---------------|------------|
| 6 | `action_generate_billing_consolidation()` + botón XML + T15-T17 | DT-001 resuelta ✅ | 1 día |
| 6b | Activar T08 en test_lumber_reception | Fase 6 completa | 30 min |
| 7 | Tests para logistics, costing, vendor_payment | Fase 6 completa | 3-5 días |
| 8 | Eliminar métodos LEGACY en vendor_payment, fix DT-NEW-VP-002 | Tests Fase 7 | 1 día |
| 9 | Dashboard de reconciliación en reports | Fase 6 completa | 2-3 días |

---

## 11. Documentación Interna a Actualizar

Los siguientes archivos de `madenat_lumber_core/docs/` contienen información **desactualizada** y deben ser corregidos:

| Archivo | Problema | Corrección requerida |
|---------|----------|----------------------|
| `04_DECISION_LOG.md:68,87,97` | Dice "crear `lumber.billing.consolidation.line`" | Cambiar a "modelo ya existe en madenat_lumber_billing" |
| `ROADMAP.md:36` | "Acción Inmediata: Creación del modelo" | Cambiar a "Fase 6: implementar método puente `action_generate_billing_consolidation()`" |
| `CHECKLIST_FINALIZACION.md` (múltiples líneas) | "Crear modelo" como pendiente | Marcar como completado, actualizar checklist |
| `05_BACKLOG.md:65,110` | Facturación como tarea de creación | Actualizar a "conexión automática shipment → consolidation" |
| `MANIFEST_ENTREGA.md:40` | `[ ]` checkbox sin marcar para billing.line | Marcar como `[x]` |
| `00_ARQUITECTURA.md:280` | DT-NEW-LC-002 implica que el modelo falta | Actualizar: modelo existe, solo activar T08 |

---

## 12. Comandos de Referencia Rápida

### Verificar ambiente

```bash
docker ps | grep odoo18
# Esperado: odoo18_app (Up), odoo18_db (Up)

docker exec odoo18_db psql -U odoo -d madenat_test \
  -c "SELECT name, state, latest_version FROM ir_module_module WHERE name LIKE 'madenat%' ORDER BY name;"
```

### Ejecutar todos los tests de lumber_core

```bash
docker exec odoo18_app python -m pytest \
  /mnt/extra-addons/madenat_lumber_core/tests/ -v
# Esperado: 30 PASSED (16 ingestion_gate + 14 reception)
```

### Confirmar nombre del campo volumen en stock.lot

```bash
grep -Rni "volumen_m3\|volume_m3" \
  /home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_core/models/stock_lot.py
```

### Fix DT-NEW-VP-002 — eliminar fallback silencioso

```python
# En lumber_shipment_cost.py, Nivel 3/4 (~línea 306+)
# ANTES:
account_id = HARDCODED_ACCOUNT_ID  # warning silencioso (f"[FALLBACK GENÉRICO]...")

# DESPUÉS:
raise UserError(_(
    "No se encontró configuración contable para la categoría %s. "
    "Configure las cuentas en Ajustes > MADENAT > Mapeo de Gastos."
) % category)
```

### Desplegar módulo en producción

```bash
docker exec odoo18_app odoo \
  -u madenat_lumber_billing \
  -d MADENAT_PROD \
  --db_host=odoo18_db --db_user=odoo --db_password=<password> \
  --stop-after-init
```

---

## 13. Cápsula de Contexto IA — Actualizada

**Copia este bloque al inicio de cualquier sesión nueva con cualquier agente:**

```
CONTEXTO: MADENAT Lumber Core — Ecosistema Odoo 18 CE
VERSIÓN DOCUMENTO: v2.0 — 12 mayo 2026 — SINCRONIZADO CON CÓDIGO REAL

AMBIENTE: Docker (odoo18_app, odoo18_db), PostgreSQL, Ubuntu
BASE: /home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/

MÓDULOS INSTALADOS (10 activos):
madenat_lumber_core v18.0.5.0.0 — núcleo: recepción, guías, stock.lot
madenat_lumber_logistics v18.0.1.2.0 — embarques, contenedores, costos de envío
madenat_lumber_costing v18.0.1.0.0 — distribución de costos a stock.lot
madenat_lumber_billing v18.0.1.0.0 — consolidación de facturación (YA INSTALADO Y FUNCIONAL)
madenat_vendor_payment v18.0.1.2.0 — pagos a proveedor vía account.move
madenat_lumber_purchasing v18.0.2.2.0 — vincula OC con recepciones
madenat_toll_processing v18.0.1.0.0 — procesa peajes/guías de despacho
madenat_lumber_shipping_core v18.0.1.0.0 — datos maestros navieros
madenat_lumber_reports v18.0.1.0.0 — reportes QWeb (solo vistas)
madenat_lumber_reception_improvements v18.0.1.0.0 — mejoras en res.partner

TESTS ACTIVOS: 31 (16 en test_ingestion_gate.py + 14 en test_lumber_reception.py + 1 en billing)

ESTADO REAL DEL CÓDIGO (verificado por grep 12 mayo 2026):
✅ lumber.billing.consolidation.line YA EXISTE — _name en lumber_billing_consolidation_line.py:16
✅ DT-001 YA RESUELTA — guardia de registry aplicada en stock_lot.py:797
✅ wood_cost_usd en stock.lot — definido en lumber_core/models/stock_lot.py:820
✅ container_ids en lumber.export.shipment — One2many confirmado en lumber_export_shipment.py:145
❌ action_generate_billing_consolidation() — NO EXISTE aún — es la tarea pendiente de Fase 6

DEUDA TÉCNICA CRÍTICA VIGENTE:
DT-NEW-VP-002: lumber_shipment_cost.py:277 — fallback contable a 4 niveles con último nivel silencioso
  Fix: convertir f"[FALLBACK GENÉRICO]" a UserError o ValidationError

DOCUMENTACIÓN DESACTUALIZADA (NO USAR como referencia de estado):
  - madenat_lumber_core/docs/04_DECISION_LOG.md — dice "crear billing.line" (ya existe)
  - madenat_lumber_core/docs/ROADMAP.md — dice "crear billing.line" (ya existe)
  - madenat_lumber_core/docs/CHECKLIST_FINALIZACION.md — múltiples referencias obsoletas
  - madenat_lumber_core/docs/05_BACKLOG.md — billing como tarea de creación (ya existe)

FASE ACTUAL: Fase 6 — implementar action_generate_billing_consolidation()
  Los modelos base YA EXISTEN. Solo falta el método puente y el botón XML.
  Ver Sección 9 de este documento para código completo.
  Pendiente confirmar: ¿volumen_m3 o volume_m3 en stock.lot?

PATRÓN ESTÁNDAR DEL ECOSISTEMA:
  - Guardia de registry: if 'model.name' in self.env: antes de cualquier acceso a modelo opcional
  - Separación: _name en logistics, _inherit en módulos superiores
  - Costos: wood_cost_usd definido en lumber_core, logistic/process/other en costing, billing lee desde lot_id
  - shipment_id en billing.line viene por related desde consolidation_id.shipment_id (no es campo directo)
```

---

## 14. Transferencia de Conocimiento

### Tiempo de onboarding: 1.5 horas

1. Leer este documento completo (30 min)
2. Ejecutar `pytest` en lumber_core → verificar 30 PASSED (10 min)
3. Confirmar nombre campo volumen: `grep -Rni "volumen_m3\|volume_m3" .../stock_lot.py` (5 min)
4. Abrir `madenat_lumber_billing/models/lumber_billing_consolidation.py` (15 min)
5. Abrir `madenat_lumber_logistics/models/lumber_export_shipment.py` — agregar método puente (30 min)
6. **NO leer** `madenat_lumber_core/docs/CHECKLIST_FINALIZACION.md` ni `ROADMAP.md` como referencia de estado — están desactualizados

### Archivos principales por módulo

| Módulo | Archivo crítico | Por qué |
|--------|----------------|---------|
| lumber_core | models/stock_lot.py | Modelo más extendido, DT-001 resuelta aquí |
| lumber_core | models/lumber_reception.py | Workflow principal |
| lumber_core | models/madenat_guia_processing.py | Parser (~2800 líneas) |
| logistics | models/lumber_export_shipment.py | Base de embarques — aquí va el método puente Fase 6 |
| billing | models/lumber_billing_consolidation.py | Destino de Fase 6 — ya funcional |
| billing | models/lumber_billing_consolidation_line.py | Línea de consolidación — ya funcional |
| vendor_payment | models/lumber_shipment_cost.py | DT-NEW-VP-002 aquí — fallback silencioso |

---

**Documento generado:** 12 de mayo de 2026 (actualización de v1.0 del 8 de mayo de 2026)
**Próxima revisión:** Al completar Fase 6
**Repositorio:** /home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/
