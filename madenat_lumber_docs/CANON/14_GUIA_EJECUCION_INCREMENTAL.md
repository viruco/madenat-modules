# CANON/14_GUIA_EJECUCION_INCREMENTAL — Guía de Ejecución por Fases y Commits
## Proyecto: MADENAT Lumber — Odoo 18 CE
## Fecha: 2026-06-05
## Estado: DOCUMENTO CANÓNICO — Orden exacto de construcción
## Ref: CANON/12, CANON/13, Código base

---

# 1. PRINCIPIO DE IMPLEMENTACIÓN

## 1.1 Regla operativa de tres niveles

| Nivel | Condición | Acción |
|-------|-----------|--------|
| **Existe** | El archivo, modelo, campo o vista ya está en el código | **Extender**: herencia XML, agregar `groups=`, agregar campos compute, sin borrar nada |
| **Falta** | El archivo, modelo, campo o vista no existe | **Implementar mínimo**: crear lo necesario con la estructura más simple que cumpla el requisito |
| **Bloquea** | Una restricción técnica impide avanzar | **Resolver en capa más baja**: si un permiso bloquea, ajustar CSV. Si un constraint bloquea, ajustar modelo. Nunca parchear en UI lo que se puede resolver en datos/seguridad |

## 1.2 Por qué no hacen falta más documentos estratégicos

CANON/12 define **qué** necesita cada perfil. CANON/13 define **cómo** se traduce a Odoo. Este documento (CANON/14) define **en qué orden exacto** se construye, archivo por archivo. La cadena documental está completa.

## 1.3 Enfoque de construcción incremental

1. Cada fase produce **un resultado verificable independientemente**.
2. Cada fase se cierra con un **criterio de aceptación binario** (pasa/no pasa).
3. Ninguna fase toca lógica de negocio a menos que sea estrictamente necesario.
4. Las primeras 3 fases (seguridad, menús, vistas) son **pura configuración XML** — no rompen nada.
5. Las fases 4-5 agregan código Python mínimo y acotado.

---

# 2. ORDEN DE ARCHIVOS Y FASES

## 2.1 Vista general

```
F1: SEGURIDAD  →  F2: MENÚS  →  F3: VISTAS  →  F4: KPIs  →  F5: GATES  →  F6: TRAZABILIDAD
    (1-2 días)      (1 día)       (2-3 días)     (2 días)     (2-3 días)     (1-2 días)

    └── Sin código ──┘            └── Mayormente XML ──┘  └── Código Python ──┘
```

## 2.2 Fase 1 — Seguridad y permisos

| Atributo | Valor |
|----------|-------|
| **Objetivo** | Crear los 4 grupos MADENAT y reescribir `ir.model.access.csv` con la matriz completa de permisos |
| **Dependencia** | Ninguna |
| **Archivos afectados** | 3 archivos (1 nuevo, 2 modificados) |
| **Criterio de cierre** | 4 grupos visibles en Settings → Users → Groups. Login con cada grupo: cada uno ve/edita solo lo que debe según la matriz |

### Archivos en orden de implementación

| # | Archivo | Acción | Contenido |
|---|---------|--------|-----------|
| 1 | `security/madenat_groups.xml` | **CREAR** | 4 `<record>` de `res.groups` + 1 `ir.module.category` |
| 2 | `security/ir.model.access.csv` | **REESCRIBIR** | 15 modelos × 4 grupos = 60 líneas con valores `perm_read,perm_write,perm_create,perm_unlink` |
| 3 | `__manifest__.py` | **MODIFICAR** | Agregar `'data': ['security/madenat_groups.xml', 'security/ir.model.access.csv']` |

## 2.3 Fase 2 — Menús por perfil

| Atributo | Valor |
|----------|-------|
| **Objetivo** | Reorganizar el menú raíz MADENAT en 4 submenús, uno por perfil |
| **Dependencia** | Fase 1 (los grupos deben existir para asignarlos a `groups=`) |
| **Archivos afectados** | 2 archivos (1 nuevo, 1 modificado) |
| **Criterio de cierre** | Cada usuario ve solo el submenú de su perfil. Gerencia ve los 4 submenús |

### Archivos en orden de implementación

| # | Archivo | Acción | Contenido |
|---|---------|--------|-----------|
| 1 | `views/madenat_menus_por_perfil.xml` | **CREAR** | 4 `<menuitem>` principales (`menu_madenat_ops`, `menu_madenat_costos`, `menu_madenat_contabilidad`, `menu_madenat_gerencia`) con `groups=` + acciones de ventana para las vistas que ya existen (recepciones, lotes, contenedores, embarques) |
| 2 | `views/lumber_core_menu.xml` | **MODIFICAR** | Agregar `groups=` a los menús existentes para que apunten a los nuevos grupos en lugar de `stock.group_stock_user`. **No eliminar ningún menú.** Los nuevos submenús de Fase 2 son wrappers; los menús existentes se reubican como hijos |

### Orden dentro del archivo `madenat_menus_por_perfil.xml`

```
1. <menuitem id="menu_madenat_ops" name="🔧 Operaciones" parent="menu_madenat_root" groups="group_madenat_operaciones" sequence="10"/>
   1.1 Dashboard (action vacío — se completa en Fase 3)
   1.2 Recepciones (action existente)
   1.3 Lotes en Inventario (action existente)
   1.4 Contenedores (action de logistics)
   1.5 Embarques (action de logistics)

2. <menuitem id="menu_madenat_costos" name="💰 Costos" parent="menu_madenat_root" groups="group_madenat_costos" sequence="20"/>
   2.1 Dashboard Costos (action vacío — Fase 3)
   2.2 Asignar Costo Base (action vacío — Fase 3)
   2.3 Expedientes Liquidación (action de costing)
   2.4 Auditoría de Costos (action vacío — Fase 3)

3. <menuitem id="menu_madenat_contabilidad" name="📒 Contabilidad" parent="menu_madenat_root" groups="group_madenat_contabilidad" sequence="30"/>
   3.1 Panel Conciliación (action vacío — Fase 3)
   3.2 Landed Costs Contables (action de costing)
   3.3 Cierre de Período (action a wizard — Fase 5)

4. <menuitem id="menu_madenat_gerencia" name="📈 Gerencia" parent="menu_madenat_root" groups="group_madenat_gerencia" sequence="40"/>
   4.1 Dashboard Gerencial (action vacío — Fase 3)
   4.2 Rentabilidad (action existente en logistics, reenlazar)
   4.3 Trazabilidad 360 (action vacío — Fase 3)
```

## 2.4 Fase 3 — Vistas por perfil

| Atributo | Valor |
|----------|-------|
| **Objetivo** | Crear 7 vistas nuevas y extender 4 vistas existentes para exponer la información que cada perfil necesita |
| **Dependencia** | Fase 2 (las acciones de menú apuntan a estas vistas) |
| **Archivos afectados** | 11 archivos (7 nuevos, 4 modificados) |
| **Criterio de cierre** | Cada perfil navega su menú y ve las vistas con los campos y pestañas correctos. Campos monetarios solo editables por Costos. Campos físicos solo editables por Operaciones |

### 2.4.1 Vistas nuevas (CREAR)

| # | Archivo | XML ID | Modelo | Tipo | Perfil |
|---|---------|--------|--------|------|--------|
| 1 | `views/madenat_ops_dashboard.xml` | `dashboard_madenat_ops` | `lumber.reception` | kanban | Operaciones |
| 2 | `views/madenat_costing_dashboard.xml` | `dashboard_madenat_costing` | `stock.lot` | kanban + graph | Costos |
| 3 | `views/madenat_executive_dashboard.xml` | `dashboard_madenat_executive` | `lumber.export.shipment` | kanban | Gerencia |
| 4 | `views/madenat_cost_audit.xml` | `view_madenat_cost_audit` | `stock.lot` | tree + pivot + graph | Costos |
| 5 | `views/madenat_lot_cost_assignment.xml` | `view_lot_cost_assignment` | `stock.lot` | tree (editable bottom) | Costos |
| 6 | `views/madenat_accounting_views.xml` | `view_accounting_reconciliation` | `lumber.reception` | tree | Contabilidad |
| 7 | `views/madenat_traceability_360.xml` | `view_traceability_360` | `stock.lot` | form (readonly) | Gerencia |

### 2.4.2 Vistas existentes a extender (MODIFICAR con herencia XML)

| # | Archivo existente | Qué se agrega | Perfil |
|---|-------------------|---------------|--------|
| 1 | `views/stock_lot_views.xml` | Pestaña "Costos" (`<page string="Costos">` con `wood_cost_usd`, `total_cost_usd`, `cost_per_m3_usd`, `cost_per_mbf_usd`, `groups="group_madenat_costos"`). Pestaña "Trazabilidad" (recepción, guía, contenedor, embarque) | Operaciones + Costos |
| 2 | `madenat_lumber_logistics/views/lumber_export_shipment_views.xml` | Pestaña "Costos" (`<page string="Costos Logísticos">` con `cost_line_ids`, `total_shipment_costs_usd`, `cost_distribution_state`, `groups="group_madenat_costos"`) | Costos |
| 3 | `madenat_lumber_costing/views/lumber_cost_distribution_views.xml` | Pestaña "Contabilidad" (`<page string="Validación Contable">` con `validated_by_accounting`, `groups="group_madenat_contabilidad"`) | Contabilidad |
| 4 | `madenat_lumber_logistics/views/lumber_profitability_views.xml` | Agregar `groups="group_madenat_gerencia"` a la acción y vista pivot de rentabilidad | Gerencia |

### 2.4.3 Atributo `groups=` en campos de vistas

La restricción de edición por campo se logra con `groups=` en el `<field>` dentro de la vista:

```xml
<!-- Ejemplo en stock_lot_views.xml -->
<field name="wood_cost_usd" groups="madenat_lumber_core.group_madenat_costos"/>
<field name="volumen_m3" groups="madenat_lumber_core.group_madenat_operaciones"/>
```

## 2.5 Fase 4 — KPIs y campos calculados

| Atributo | Valor |
|----------|-------|
| **Objetivo** | Agregar 3 campos nuevos en modelos existentes para soportar KPIs que no pueden resolverse solo con vistas |
| **Dependencia** | Fase 3 (los dashboards ya existen y referencian estos campos) |
| **Archivos afectados** | 2 archivos Python (modificar) |
| **Criterio de cierre** | Los dashboards muestran los KPIs con datos reales. `reconciliation_state` aparece en el panel de conciliación |

### Archivos y campos

| # | Archivo | Campo | Tipo | Dependencias | Justificación |
|---|---------|-------|------|-------------|---------------|
| 1 | `models/lumber_reception.py` | `reconciliation_state` | `fields.Selection([('pending','Pendiente'),('done','Conciliado'),('difference','Diferencia')])` | Ninguna (campo independiente) | GB-5 y panel de conciliación |
| 2 | `models/lumber_reception.py` | `gate_duration_hours` | `fields.Float(compute='_compute_gate_duration', store=False)` | Fechas de Gate 0 y Gate 3 (existentes en lógica de recepción) | KPI tiempo staging→stock |
| 3 | `models/stock_lot.py` | `cost_assigned_date` | `fields.Datetime()` | Se asigna en `write()` cuando `wood_cost_usd` cambia de 0 a >0 | KPI tiempo asignación costo |

**Nota sobre los KPIs agregados restantes:** Los conteos (% lotes con costo, expedientes pendientes, lotes con margen negativo) se implementan con `search_count()` en los dashboards kanban (Fase 3), **no requieren campos nuevos en modelo**.

## 2.6 Fase 5 — Validaciones y Gates

| Atributo | Valor |
|----------|-------|
| **Objetivo** | Implementar 5 Gates de Negocio (GB-1, GB-2, GB-4, GB-5, GB-6) con validaciones Python |
| **Dependencia** | Fase 4 (GB-5 usa `reconciliation_state`, GB-2 usa `wood_cost_usd`) |
| **Archivos afectados** | 4 archivos (2 modificados, 2 nuevos) |
| **Criterio de cierre** | Cada gate bloquea la acción correspondiente si no se cumple la condición. El mensaje de error indica exactamente qué falta |

### Archivos y gates

| # | Archivo | Gate | Método | Acción bloqueada si falla |
|---|---------|------|--------|--------------------------|
| 1 | `models/lumber_reception.py` | GB-1 | `_check_lines_ready_for_gate3()` llamado en `action_confirm()` | Gate 3 (creación de stock.lot) |
| 2 | `models/lumber_container.py` | GB-2 | `_check_lots_have_cost()` en `write()` cuando se agregan `lot_ids` | Asignación de lote a contenedor |
| 3 | GB-3 | ✅ YA EXISTE en `lumber_export_shipment.action_set_in_transit()` (líneas 450-458) | Zarpe |
| 4 | `models/lumber_cost_distribution.py` | GB-4 | Campo `validated_by_accounting` (Boolean, default=False). Solo Contabilidad puede marcarlo True | Cierre de período |
| 5 | `models/lumber_reception.py` | GB-5 | Usa `reconciliation_state` (Fase 4). Solo Contabilidad puede cambiar a `done` | Cierre de período |
| 6 | `wizard/madenat_period_close.py` + `wizard/madenat_period_close.xml` | GB-6 | Nuevo wizard `madenat.period.close` con método `action_close_period()` que verifica GB-4 + GB-5 + lotes con costo > 0 | Cierre contable del período |

**Código mínimo para cada gate (pseudocódigo listo para implementar):**

```python
# GB-1 en lumber_reception.py
def _check_lines_ready_for_gate3(self):
    for rec in self:
        incomplete = rec.reception_line_ids.filtered(
            lambda l: not l.product_id or not l.subproduct_id 
                   or not l.thickness_nominal or not l.width_nominal
        )
        if incomplete:
            raise UserError(_(
                "Gate 3 bloqueado: %d líneas incompletas.\n"
                "Verifique producto, subproducto y dimensiones nominales."
            ) % len(incomplete))

# GB-2 en lumber_container.py
def _check_lots_have_cost(self):
    for container in self:
        sin_costo = container.lot_ids.filtered(
            lambda l: not l.wood_cost_usd or l.wood_cost_usd <= 0
        )
        if sin_costo:
            raise UserError(_(
                "No se puede agregar al contenedor. Los siguientes lotes "
                "no tienen costo base asignado:\n%s"
            ) % "\n".join(sin_costo.mapped('name')))
```

### Modelo `madenat.period.close` (nuevo)

```python
# wizard/madenat_period_close.py
class MadenatPeriodClose(models.TransientModel):
    _name = 'madenat.period.close'
    _description = 'Cierre de Período MADENAT'
    
    def action_close_period(self):
        # GB-4: embarques con costos distribuidos
        shipments_pending = self.env['lumber.export.shipment'].search([
            ('state', '=', 'in_transit'),
            ('cost_distribution_state', '=', 'pending')
        ])
        if shipments_pending:
            raise UserError(_(
                "%d embarques sin costos distribuidos: %s"
            ) % (len(shipments_pending), ", ".join(shipments_pending.mapped('name'))))
        
        # GB-5: recepciones conciliadas
        receptions_pending = self.env['lumber.reception'].search([
            ('reconciliation_state', '!=', 'done')
        ])
        if receptions_pending:
            raise UserError(_(
                "%d recepciones sin conciliar"
            ) % len(receptions_pending))
        
        # Lotes sin costo
        lots_sin_costo = self.env['stock.lot'].search([
            ('wood_cost_usd', '<=', 0)
        ])
        if lots_sin_costo:
            raise UserError(_(
                "%d lotes sin costo base asignado"
            ) % len(lots_sin_costo))
        
        # Cierre exitoso
        self.env['madenat.audit.log'].create({
            'name': 'Cierre de período ejecutado',
            'user_id': self.env.user.id,
            'description': 'Período cerrado exitosamente',
        })
        return {'type': 'ir.actions.client', 'tag': 'display_notification',
                'params': {'message': 'Período cerrado exitosamente', 'type': 'success'}}
```

## 2.7 Fase 6 — Trazabilidad

| Atributo | Valor |
|----------|-------|
| **Objetivo** | Integrar `madenat.audit.log` en todos los eventos críticos. Extender el modelo con `event_type` |
| **Dependencia** | Fase 5 (los gates ya están generando eventos que deben registrarse) |
| **Archivos afectados** | 2 archivos (1 modificado, 1 nuevo) |
| **Criterio de cierre** | Todo gate rechazado, gate pasado, asignación de costo y zarpe genera una entrada en `madenat.audit.log` |

### Archivos

| # | Archivo | Acción |
|---|---------|--------|
| 1 | `models/madenat_audit_log.py` | Agregar campo `event_type` (Selection: `gate_rejected`, `gate_passed`, `cost_assigned`, `cost_distributed`, `shipment_sailed`, `forced_reopen`, `period_closed`) |
| 2 | `models/lumber_reception.py`, `lumber_container.py`, `lumber_export_shipment.py`, `wizard/madenat_period_close.py` | Agregar `self.env['madenat.audit.log'].create(...)` en cada evento definido en CANON/12 sección 5.4 |

---

# 3. ARCHIVO DETALLADO: SEGURIDAD Y PERMISOS

## 3.1 `security/madenat_groups.xml` — Contenido exacto

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">

        <record id="module_category_madenat" model="ir.module.category">
            <field name="name">MADENAT Lumber</field>
            <field name="sequence">10</field>
        </record>

        <record id="group_madenat_operaciones" model="res.groups">
            <field name="name">Operaciones</field>
            <field name="category_id" ref="module_category_madenat"/>
            <field name="implied_ids" eval="[(4, ref('stock.group_stock_user'))]"/>
        </record>

        <record id="group_madenat_costos" model="res.groups">
            <field name="name">Costos y Auditoría</field>
            <field name="category_id" ref="module_category_madenat"/>
            <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
        </record>

        <record id="group_madenat_contabilidad" model="res.groups">
            <field name="name">Contabilidad</field>
            <field name="category_id" ref="module_category_madenat"/>
            <field name="implied_ids" eval="[(4, ref('account.group_account_invoice'))]"/>
        </record>

        <record id="group_madenat_gerencia" model="res.groups">
            <field name="name">Gerencia</field>
            <field name="category_id" ref="module_category_madenat"/>
            <field name="implied_ids" eval="[
                (4, ref('base.group_user')),
                (4, ref('group_madenat_operaciones')),
                (4, ref('group_madenat_costos')),
                (4, ref('group_madenat_contabilidad'))
            ]"/>
        </record>

    </data>
</odoo>
```

## 3.2 `security/ir.model.access.csv` — Matriz completa

**Regla:** El CSV actual tiene 31 líneas contra `base.group_user` y `stock.group_stock_manager`. Se reemplaza completamente. Cada modelo tiene 4 líneas (una por grupo MADENAT).

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_lumber_reception_ops,lumber.reception.ops,model_lumber_reception,group_madenat_operaciones,1,1,1,0
access_lumber_reception_costos,lumber.reception.costos,model_lumber_reception,group_madenat_costos,1,0,0,0
access_lumber_reception_contab,lumber.reception.contab,model_lumber_reception,group_madenat_contabilidad,1,0,1,0
access_lumber_reception_ger,lumber.reception.ger,model_lumber_reception,group_madenat_gerencia,1,0,1,0
access_lumber_reception_line_ops,lumber.reception.line.ops,model_lumber_reception_line,group_madenat_operaciones,1,1,1,0
access_lumber_reception_line_costos,lumber.reception.line.costos,model_lumber_reception_line,group_madenat_costos,1,0,0,0
access_lumber_reception_line_contab,lumber.reception.line.contab,model_lumber_reception_line,group_madenat_contabilidad,1,0,0,0
access_lumber_reception_line_ger,lumber.reception.line.ger,model_lumber_reception_line,group_madenat_gerencia,1,0,0,0
access_stock_lot_ops,stock.lot.ops,model_stock_lot,group_madenat_operaciones,1,1,1,0
access_stock_lot_costos,stock.lot.costos,model_stock_lot,group_madenat_costos,1,0,1,0
access_stock_lot_contab,stock.lot.contab,model_stock_lot,group_madenat_contabilidad,1,0,0,0
access_stock_lot_ger,stock.lot.ger,model_stock_lot,group_madenat_gerencia,1,0,1,0
access_stock_lot_cost_line_ops,stock.lot.cost.line.ops,model_stock_lot_cost_line,group_madenat_operaciones,1,0,0,0
access_stock_lot_cost_line_costos,stock.lot.cost.line.costos,model_stock_lot_cost_line,group_madenat_costos,1,1,1,1
access_stock_lot_cost_line_contab,stock.lot.cost.line.contab,model_stock_lot_cost_line,group_madenat_contabilidad,1,0,0,0
access_stock_lot_cost_line_ger,stock.lot.cost.line.ger,model_stock_lot_cost_line,group_madenat_gerencia,1,0,0,0
access_lumber_cost_distribution_ops,cost.dist.ops,model_lumber_cost_distribution,group_madenat_operaciones,1,0,0,0
access_lumber_cost_distribution_costos,cost.dist.costos,model_lumber_cost_distribution,group_madenat_costos,1,1,1,1
access_lumber_cost_distribution_contab,cost.dist.contab,model_lumber_cost_distribution,group_madenat_contabilidad,1,0,1,0
access_lumber_cost_distribution_ger,cost.dist.ger,model_lumber_cost_distribution,group_madenat_gerencia,1,0,0,0
access_lumber_cost_dist_line_ops,cost.dist.line.ops,model_lumber_cost_distribution_line,group_madenat_operaciones,1,0,0,0
access_lumber_cost_dist_line_costos,cost.dist.line.costos,model_lumber_cost_distribution_line,group_madenat_costos,1,1,1,1
access_lumber_cost_dist_line_contab,cost.dist.line.contab,model_lumber_cost_distribution_line,group_madenat_contabilidad,1,0,0,0
access_lumber_cost_dist_line_ger,cost.dist.line.ger,model_lumber_cost_distribution_line,group_madenat_gerencia,1,0,0,0
access_lumber_container_ops,container.ops,model_lumber_container,group_madenat_operaciones,1,1,1,0
access_lumber_container_costos,container.costos,model_lumber_container,group_madenat_costos,1,0,0,0
access_lumber_container_contab,container.contab,model_lumber_container,group_madenat_contabilidad,1,0,0,0
access_lumber_container_ger,container.ger,model_lumber_container,group_madenat_gerencia,1,0,1,0
access_lumber_export_shipment_ops,shipment.ops,model_lumber_export_shipment,group_madenat_operaciones,1,1,1,0
access_lumber_export_shipment_costos,shipment.costos,model_lumber_export_shipment,group_madenat_costos,1,0,1,0
access_lumber_export_shipment_contab,shipment.contab,model_lumber_export_shipment,group_madenat_contabilidad,1,0,0,0
access_lumber_export_shipment_ger,shipment.ger,model_lumber_export_shipment,group_madenat_gerencia,1,0,1,0
access_shipment_cost_line_ops,ship.cost.line.ops,model_lumber_shipment_cost_line,group_madenat_operaciones,1,0,0,0
access_shipment_cost_line_costos,ship.cost.line.costos,model_lumber_shipment_cost_line,group_madenat_costos,1,1,1,1
access_shipment_cost_line_contab,ship.cost.line.contab,model_lumber_shipment_cost_line,group_madenat_contabilidad,1,0,0,0
access_shipment_cost_line_ger,ship.cost.line.ger,model_lumber_shipment_cost_line,group_madenat_gerencia,1,0,0,0
access_billing_consolidation_ops,billing.cons.ops,model_lumber_billing_consolidation,group_madenat_operaciones,1,0,0,0
access_billing_consolidation_costos,billing.cons.costos,model_lumber_billing_consolidation,group_madenat_costos,1,0,0,0
access_billing_consolidation_contab,billing.cons.contab,model_lumber_billing_consolidation,group_madenat_contabilidad,1,0,1,0
access_billing_consolidation_ger,billing.cons.ger,model_lumber_billing_consolidation,group_madenat_gerencia,1,0,0,0
access_madenat_audit_log_ops,audit.log.ops,model_madenat_audit_log,group_madenat_operaciones,1,0,1,0
access_madenat_audit_log_costos,audit.log.costos,model_madenat_audit_log,group_madenat_costos,1,0,1,0
access_madenat_audit_log_contab,audit.log.contab,model_madenat_audit_log,group_madenat_contabilidad,1,0,1,0
access_madenat_audit_log_ger,audit.log.ger,model_madenat_audit_log,group_madenat_gerencia,1,0,0,0
access_export_formula_ops,formula.ops,model_lumber_export_formula,group_madenat_operaciones,1,0,0,0
access_export_formula_costos,formula.costos,model_lumber_export_formula,group_madenat_costos,1,1,1,0
access_export_formula_contab,formula.contab,model_lumber_export_formula,group_madenat_contabilidad,1,0,0,0
access_export_formula_ger,formula.ger,model_lumber_export_formula,group_madenat_gerencia,1,0,0,0
access_ingestion_format_ops,ingest.ops,model_lumber_ingestion_format,group_madenat_operaciones,1,0,0,0
access_ingestion_format_costos,ingest.costos,model_lumber_ingestion_format,group_madenat_costos,1,1,1,0
access_ingestion_format_contab,ingest.contab,model_lumber_ingestion_format,group_madenat_contabilidad,1,0,0,0
access_ingestion_format_ger,ingest.ger,model_lumber_ingestion_format,group_madenat_gerencia,1,0,0,0
access_subproducto_ops,subproducto.ops,model_madenat_subproducto,group_madenat_operaciones,1,0,0,0
access_subproducto_costos,subproducto.costos,model_madenat_subproducto,group_madenat_costos,1,0,0,0
access_subproducto_contab,subproducto.contab,model_madenat_subproducto,group_madenat_contabilidad,1,0,0,0
access_subproducto_ger,subproducto.ger,model_madenat_subproducto,group_madenat_gerencia,1,1,1,1
```

**Nota sobre modelos de guía y otros:** Los modelos `madenat.guia.processing`, `madenat.guia.processing.line`, `madenat.guia.mass.update` y `lumber.reception.mass.update` mantienen sus permisos actuales (solo lectura para todos excepto `stock.group_stock_user` que ya es implied de `group_madenat_operaciones`). No requieren líneas adicionales en el CSV porque `group_madenat_operaciones` hereda de `stock.group_stock_user`.

## 3.3 Herencia de grupos

```
stock.group_stock_user ──► group_madenat_operaciones ──┐
base.group_user ────────► group_madenat_costos ────────┤
account.group_account_invoice ► group_madenat_contabilidad ─┤
                                                         │
        ┌────────────────────────────────────────────────┘
        ▼
group_madenat_gerencia (hereda de los 3 anteriores + base.group_user)
```

## 3.4 Modelos protegidos primero

Los modelos más críticos desde el punto de vista de seguridad monetaria:

1. **`stock.lot.cost.line`** — Solo Costos puede crear/editar/eliminar. Operaciones y Contabilidad solo lectura. Gerencia solo lectura.
2. **`lumber.cost.distribution`** — Solo Costos CRUD. Contabilidad puede editar (solo `validated_by_accounting`). Operaciones solo lectura.
3. **`stock.lot`** — Operaciones RW (datos físicos), Costos RW (datos monetarios), Contabilidad R, Gerencia R.

## 3.5 Validación mínima antes de continuar a Fase 2

1. `docker compose restart odoo18_app && docker compose logs odoo18_app | grep -i error`
2. Login como usuario en grupo Operaciones → ver menú MADENAT.
3. Login como usuario en grupo Costos → ver el mismo menú (por ahora, hasta Fase 2).
4. Verificar que un usuario sin grupo MADENAT no ve el menú MADENAT.
5. Intentar crear un `stock.lot.cost.line` como Operaciones → debe fallar (error de permisos).

---

# 4. MENÚS, ACCIONES Y VISTAS — SECUENCIA DE IMPLEMENTACIÓN

## 4.1 Orden dentro de Fase 2 (Menús)

```
1. Crear views/madenat_menus_por_perfil.xml
   1.1 Definir 4 <menuitem> principales con groups=
   1.2 Dentro de cada uno, crear <menuitem> hijos con action= apuntando a XML IDs existentes
   1.3 Para acciones que no existen aún (dashboards), usar action="ir.actions.act_window" vacío con res_model correcto

2. Modificar views/lumber_core_menu.xml
   2.1 Cambiar groups="stock.group_stock_user" → groups="group_madenat_operaciones"
   2.2 Cambiar groups="stock.group_stock_manager" → groups="group_madenat_gerencia"
   2.3 No eliminar nada. No cambiar estructura. Solo groups=

3. Modificar logistics/views/logistics_menus.xml
   3.1 Agregar groups="group_madenat_operaciones" a menu_lumber_logistics

4. Modificar costing/views/costing_menus.xml
   4.1 Agregar groups="group_madenat_costos" a los menús de costing
```

## 4.2 Orden dentro de Fase 3 (Vistas)

```
1. CREAR vistas de dashboard (sin lógica, solo estructura):
   1.1 views/madenat_ops_dashboard.xml
   1.2 views/madenat_costing_dashboard.xml
   1.3 views/madenat_executive_dashboard.xml

2. CREAR vistas funcionales:
   2.1 views/madenat_cost_audit.xml (pivot + graph)
   2.2 views/madenat_lot_cost_assignment.xml (tree editable)
   2.3 views/madenat_accounting_views.xml (tree)
   2.4 views/madenat_traceability_360.xml (form readonly)

3. EXTENDER vistas existentes:
   3.1 stock_lot_views.xml → pestañas Costos + Trazabilidad
   3.2 lumber_export_shipment_views.xml → pestaña Costos
   3.3 lumber_cost_distribution_views.xml → pestaña Contabilidad
   3.4 lumber_profitability_views.xml → groups= en acción

4. ACTUALIZAR madenat_menus_por_perfil.xml con las acciones ahora existentes
```

## 4.3 Criterio de aceptación por fase

| Fase | Criterio |
|------|----------|
| F2 completada | 4 usuarios (uno por perfil) inician sesión y solo ven su submenú |
| F3 completada | Cada perfil navega sus vistas. Campos monetarios readonly para Operaciones. Pestaña Costos visible para Costos. Pestaña Contabilidad visible para Contabilidad |

---

# 5. KPIS Y DASHBOARDS

## 5.1 Momento de implementación

Los KPIs se dividen en dos momentos:

| Momento | Qué | Fase |
|---------|-----|------|
| **Fase 3 (vistas)** | KPIs que ya tienen campo en el modelo (10 de 28). Se exponen en dashboards kanban y vistas pivot. **Sin código Python.** | 3 |
| **Fase 4 (campos)** | KPIs que requieren campo nuevo (3 de 28). Se agregan como `fields.Selection`, `fields.Float(compute)`, `fields.Datetime`. **Código Python mínimo.** | 4 |

Los 15 KPIs restantes son agregaciones (conteos, promedios) que Odoo resuelve nativamente con vistas `pivot` y `graph`. No requieren campos nuevos ni código.

## 5.2 Resolución por mecanismo

| Mecanismo | KPIs | Ejemplo |
|-----------|------|---------|
| **Campo existente + vista** | 10 | `yield_efficiency_pct` en gráfico de dashboard |
| **Campo nuevo (compute/store)** | 3 | `reconciliation_state`, `gate_duration_hours`, `cost_assigned_date` |
| **Vista pivot nativa** | 8 | Top 5 clientes: pivot sobre `customer_id` con medida `gross_margin_usd` |
| **Vista graph nativa** | 5 | Tendencia márgenes: graph línea sobre `gross_margin_pct` por mes |
| **Dashboard kanban `search_count()`** | 2 | Lotes sin costo: `<t t-set="sin_costo" t-value="env['stock.lot'].search_count([('wood_cost_usd','=',0)])"/>` |

## 5.3 Entregable mínimo por fase

| Fase | Entregable |
|------|------------|
| F3 | Dashboard Operaciones muestra conteo de recepciones por estado. Dashboard Costos muestra conteo de lotes sin costo. Dashboard Gerencia muestra revenue del mes actual |
| F4 | Panel de conciliación muestra columna `reconciliation_state`. Campo `cost_assigned_date` se registra automáticamente al asignar `wood_cost_usd` |

---

# 6. GATES Y TRAZABILIDAD

## 6.1 Cuándo implementar gates

**Después de Fase 4.** Los gates GB-2 y GB-5 dependen de campos que se crean en Fase 4 (`wood_cost_usd` ya existe, `reconciliation_state` es nuevo). GB-1 puede implementarse antes (Fase 3) si se desea, porque solo valida campos existentes.

## 6.2 Validaciones que deben existir antes

Antes de implementar cualquier gate, verificar:

1. El permiso de escritura sobre el modelo que ejecuta la validación es correcto (Fase 1).
2. El usuario que ejecuta la acción tiene el grupo correcto (Fase 2).
3. Los campos que el gate valida existen y son visibles en la vista (Fase 3).

## 6.3 Dónde se registra la trazabilidad

| Evento | Archivo que registra | Método |
|--------|---------------------|--------|
| Gate rechazado | Mismo archivo del gate | `madenat.audit.log.create()` justo antes del `raise UserError` |
| Gate pasado | Mismo archivo del gate | `madenat.audit.log.create()` justo después de pasar la validación |
| Asignación de costo | `stock_lot.py` `write()` | Si `wood_cost_usd` cambia de 0 a >0 |
| Zarpe | `lumber_export_shipment.py` `action_set_in_transit()` | Después del `write({'state': 'in_transit'})` |
| Cierre de período | `wizard/madenat_period_close.py` | Al final de `action_close_period()` |

## 6.4 Qué sucede si un gate falla

1. Se lanza `raise UserError` con mensaje descriptivo en español.
2. El mensaje incluye: nombre del gate, cantidad de registros que fallan, lista de IDs o nombres.
3. Se registra `madenat.audit.log` con `event_type='gate_rejected'`.
4. El usuario corrige el problema y reintenta la acción.
5. Si el usuario no tiene permisos para corregir (ej: Operaciones ve GB-2 rechazado por falta de costo), el mensaje indica "Contacte al equipo de Costos".

---

# 7. ESTRATEGIA DE COMMITS PEQUEÑOS

## 7.1 Regla de commit

Cada commit debe:
- Tocar **un solo propósito** (seguridad, menús, una vista, un gate).
- Ser **independientemente revertible**.
- Tener un mensaje descriptivo en español: `[F1] Crear grupos de seguridad MADENAT`.

## 7.2 Secuencia de commits

| # | Commit | Archivos | Riesgo | Validación |
|---|--------|----------|--------|------------|
| **C1** | `[F1] Crear madenat_groups.xml con 4 grupos` | `security/madenat_groups.xml` (nuevo) | Bajo | `docker compose restart` sin errores |
| **C2** | `[F1] Reescribir ir.model.access.csv con matriz 15×4` | `security/ir.model.access.csv` (reescritura) | **Medio** — puede romper acceso si hay error de sintaxis | Login con cada grupo. Verificar acceso a modelos |
| **C3** | `[F1] Actualizar __manifest__.py para cargar seguridad` | `__manifest__.py` (modificar) | Bajo | Los grupos aparecen en UI |
| **C4** | `[F2] Crear madenat_menus_por_perfil.xml` | `views/madenat_menus_por_perfil.xml` (nuevo) | Bajo | Menú principal muestra submenús |
| **C5** | `[F2] Migrar groups= en menús existentes` | `lumber_core_menu.xml`, `logistics_menus.xml`, `costing_menus.xml` | Bajo | Los menús existentes siguen funcionando |
| **C6** | `[F3] Crear dashboard de Operaciones` | `views/madenat_ops_dashboard.xml` (nuevo) | Bajo | Dashboard visible con datos reales |
| **C7** | `[F3] Crear dashboard de Costos` | `views/madenat_costing_dashboard.xml` (nuevo) | Bajo | Dashboard visible |
| **C8** | `[F3] Crear dashboard Gerencial` | `views/madenat_executive_dashboard.xml` (nuevo) | Bajo | Dashboard visible |
| **C9** | `[F3] Crear vistas funcionales (auditoría, asignación, conciliación, trazabilidad)` | 4 archivos nuevos | Bajo | Vistas accesibles desde menú |
| **C10** | `[F3] Extender stock_lot_views con pestañas Costos y Trazabilidad` | `stock_lot_views.xml` (extender) | Bajo | Pestañas visibles con groups= correcto |
| **C11** | `[F3] Extender shipment_views con pestaña Costos` | `lumber_export_shipment_views.xml` (extender) | Bajo | Pestaña visible |
| **C12** | `[F3] Extender cost_distribution_views con pestaña Contabilidad` | `lumber_cost_distribution_views.xml` (extender) | Bajo | Pestaña visible |
| **C13** | `[F3] Agregar groups= a vistas de rentabilidad` | `lumber_profitability_views.xml` | Bajo | Solo Gerencia ve rentabilidad |
| **C14** | `[F4] Agregar reconciliation_state a lumber_reception` | `models/lumber_reception.py` (campo nuevo) | Bajo | Campo visible en panel de conciliación |
| **C15** | `[F4] Agregar gate_duration_hours a lumber_reception` | `models/lumber_reception.py` (compute) | Bajo | KPI visible en dashboard |
| **C16** | `[F4] Agregar cost_assigned_date a stock_lot` | `models/stock_lot.py` (campo + write override) | **Medio** — toca write() del modelo | Fecha se asigna automáticamente |
| **C17** | `[F5] Implementar GB-1 en lumber_reception` | `models/lumber_reception.py` (validación) | Medio — modifica action_confirm() | Gate 3 bloqueado si líneas incompletas |
| **C18** | `[F5] Implementar GB-2 en lumber_container` | `models/lumber_container.py` (validación) | Medio — modifica write() | Asignación a contenedor bloqueada sin costo |
| **C19** | `[F5] Agregar validated_by_accounting a cost_distribution` | `models/lumber_cost_distribution.py` (campo) | Bajo | Campo visible en pestaña Contabilidad |
| **C20** | `[F5] Crear wizard madenat_period_close (GB-6)` | `wizard/madenat_period_close.py` + `.xml` | Medio — nuevo modelo Transient | Cierre de período con validaciones |
| **C21** | `[F6] Extender madenat_audit_log con event_type` | `models/madenat_audit_log.py` (campo) | Bajo | Campo event_type en audit log |
| **C22** | `[F6] Integrar audit.log en todos los gates` | 4 archivos Python (modificar) | Bajo | Cada evento genera entrada en audit log |

## 7.3 Commits que pueden adelantarse

Los commits C6-C13 (vistas) pueden comenzar en paralelo con C4-C5 (menús) si hay más de un desarrollador. La restricción real es:
- C1-C3 deben ser secuenciales y primero.
- C4-C5 dependen de C3.
- C6-C13 dependen de C5.
- C14-C22 dependen de C13.

---

# 8. CIERRE EJECUTIVO

## 8.1 Siguiente acción concreta

**Commit C1:** crear `custom_addons/madenat_lumber_core/security/madenat_groups.xml` con el contenido exacto de la sección 3.1.

```bash
# Después del commit:
docker compose restart odoo18_app && docker compose logs odoo18_app | grep -E "(error|Error|ERROR|madenat)"
```

Si el módulo carga sin errores, proceder con C2. Si hay error, resolver antes de continuar.

## 8.2 Por qué este orden es el correcto

1. **Seguridad primero:** sin grupos, los menús no tienen a quién filtrar. Sin CSV, los permisos de escritura no existen.
2. **Menús después:** sin menús, los dashboards no tienen dónde anclarse.
3. **Vistas después:** sin vistas, los KPIs no tienen dónde mostrarse.
4. **Gates al final:** los gates validan datos que ya se están ingresando por las vistas. Implementarlos antes dejaría validaciones huérfanas.
5. **Trazabilidad cierra:** la auditoría solo tiene sentido cuando los eventos ya están ocurriendo.

## 8.3 Regla de continuidad

> Cada commit debe poder revertirse sin afectar commits anteriores. Si un commit toca lógica de negocio, debe estar aislado en un método nuevo o una validación acotada. No se mezclan cambios de seguridad con cambios de UI en el mismo commit. El orden F1→F6 es rígido; dentro de cada fase, los commits pueden reordenarse si no hay dependencia interna.

---

*Documento creado: 2026-06-05*
*Versión: 1.0.0*
*Autor: Arquitectura MADENAT — CANON/14*
*Próximo paso: Ejecutar Commit C1*