# INC-006: view_mode `tree,form` deprecado en Odoo 18

**ID:** INC-006
**Fecha:** 2026-06-06
**Estado:** RESUELTO
**Severidad:** Media (compatibilidad)
**Módulos afectados:** logistics, core, purchasing

---

## Síntoma

Warnings en logs de Odoo 18 al usar acciones con `view_mode="tree,form"`. Aunque Odoo 18 mantiene retrocompatibilidad, el tag `tree` está deprecado desde Odoo 16 y será eliminado en versiones futuras.

## Causa raíz

4 acciones definidas con `<field name="view_mode">tree,form</field>`:
1. `logistics_menus.xml` — acción `action_lumber_shipping_rule`
2. `madenat_traceability_360.xml` — acción `action_madenat_traceability_360`
3. `madenat_lot_cost_assignment.xml` — acción `action_madenat_lot_cost_assignment`
4. `purchase_tracking_views.xml` — acción `action_purchase_tracking`

## Solución

Reemplazar `<field name="view_mode">tree,form</field>` por `<field name="view_mode">list,form</field>` en los 4 archivos.

## Archivos modificados

| Archivo | Cambio |
|--------|--------|
| `madenat_lumber_logistics/views/logistics_menus.xml` | tree→list (línea 70) |
| `madenat_lumber_logistics/views/madenat_traceability_360.xml` | tree→list (línea 9) |
| `madenat_lumber_core/views/madenat_lot_cost_assignment.xml` | tree→list (línea 9) |
| `madenat_lumber_purchasing/views/purchase_tracking_views.xml` | tree→list (línea 26) |

## Verificación

Búsqueda `tree,form` en `*.xml` del proyecto → 0 resultados. Confirmado 2026-06-06.

## Relacionado

- REMEDIACION_CRITICA_2026-06-06.md — Cambio #1-4
- AUDITORIA_INTEGRAL_2026-06-06.md — Hallazgo C-R1