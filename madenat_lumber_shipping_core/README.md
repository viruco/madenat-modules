# MADENAT Shipping Core

Datos maestros de transporte marítimo para MADENAT.

## Propósito

Gestión de motonaves, viajes y reservas (bookings). Este módulo define los modelos base de transporte marítimo. Los menús y la navegación son provistos por `madenat_lumber_logistics`.

## Dependencias

- `base`
- `mail`

## Modelos principales

- `shipping.vessel` — Motonaves
- `shipping.voyage` — Viajes
- `shipping.booking` — Reservas

## Nota

Este módulo no define menús propios. La navegación hacia sus vistas se construye desde `madenat_lumber_logistics/views/logistics_menus.xml`.

## Documentación relacionada

- CANON/15_DIAGNOSTICO_NAVEGACION_ACTUAL.md
- WIKI/02_TECNICO/dependencias_modulos.md