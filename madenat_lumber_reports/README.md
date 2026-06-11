# MADENAT Lumber Reports

Cerebro de gestión y remapeo de navegación para MADENAT.

## Propósito

Módulo de nivel superior que depende de todos los módulos del ecosistema. Su función principal es:
- Remapear la navegación (menús y acciones) de todo el ecosistema MADENAT bajo un árbol unificado
- Proveer reportes y listados consolidados (comercial, físico, exportación)

## Dependencias

- `madenat_lumber_core`
- `madenat_lumber_purchasing`
- `madenat_lumber_logistics`
- `madenat_lumber_shipping_core`
- `madenat_lumber_costing`
- `madenat_toll_processing`
- `madenat_vendor_payment`
- `madenat_lumber_billing`

## Archivos clave

- `views/menu_remapping.xml` — Remapeo central de navegación
- `views/lumber_reports_menu.xml` — Submenú de reportes

## Documentación relacionada

- CANON/15_DIAGNOSTICO_NAVEGACION_ACTUAL.md (mapa de navegación consolidado)
- AUDITORIA_INTEGRAL_2026-06-06.md