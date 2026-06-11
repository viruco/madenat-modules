# MADENAT Lumber Costing

Sistema de costeo multi-nivel para lotes de madera en MADENAT.

## Propósito

Costeo completo de madera (compra, logístico, proceso) con distribución automática de costos y valorización de inventario.

## Dependencias

- `madenat_lumber_core`
- `madenat_lumber_logistics`
- `madenat_lumber_shipping_core`
- `account`

## Modelos principales

- `lumber.cost.distribution` — Distribución de costos
- `lumber.cost.distribution.line` — Líneas de distribución
- `stock.lot.cost.line` — Líneas de costo por lote

## Documentación relacionada

- CANON/08_COSTEO.md
- security_accesos.md