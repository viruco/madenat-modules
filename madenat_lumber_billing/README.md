# MADENAT Lumber Billing

## Descripción

`madenat_lumber_billing` es un módulo de Odoo 18 CE diseñado para gestionar el proceso de facturación de embarques de madera en un flujo controlado de auditoría y facturación.

## Instalación

1. Colocar el módulo en la ruta de `addons` de Odoo.
2. Reiniciar el servidor Odoo.
3. Actualizar la lista de aplicaciones.
4. Instalar `madenat_lumber_billing`.

## Flujo de Trabajo

El proceso principal del módulo sigue este ciclo:

1. `draft`
2. `ready_audit`
3. `in_audit`
4. `audit_approved`
5. `ready_billing`
6. `billed`

## Modelos

- `lumber.billing.consolidation`
- `lumber.billing.consolidation.line`

## Permisos

Se agregaron permisos para los TransientModel del wizard de facturación.

- `access_lumber_billing_invoice_wizard` — `lumber.billing.invoice.wizard` — `base.group_user` — `1,1,1,1`
- `access_lumber_billing_invoice_wizard_line` — `lumber.billing.invoice.wizard.line` — `base.group_user` — `1,1,1,1`

## Integración

- `lumber.export.shipment` integra con la facturación nativa de Odoo.
- El wizard `lumber.billing.invoice.wizard` genera registros en `account.move`.

## Notas Técnicas

- Versión: `v18.0.1.0.0`
- El wizard de facturación es un TransientModel que construye la factura en `account.move`.
- La lógica respeta el flujo de auditoría antes de emitir la factura.
- Se agregó el permiso necesario en `security/ir.model.access.csv` para habilitar el wizard y su línea a usuarios base.

