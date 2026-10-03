# INC-011 — Desalineación entre código y base `madenat_test`

**Fecha:** 2026-10-03  
**Estado:** Resuelto  
**Severidad:** Alta  
**Área:** Operación técnica / despliegue

## Síntoma

Tres pantallas de Logística mostraban error porque sus acciones apuntaban a
modelos que existían en la base de datos pero no estaban presentes en el código
montado por Odoo:

- `lumber.shipment.rebaja.wizard`
- `madenat.processor.shipment.wizard`
- `madenat.sv.imputation`

El login y el flujo de Ingreso de Madera permanecieron disponibles.

## Causa raíz

La base `madenat_test` había sido actualizada con una versión de Core y
Logística más reciente que el código posteriormente montado en
`/mnt/extra-addons`. El cambio de código dejó menús y acciones persistidos en
la base apuntando a modelos ausentes.

## Resolución

Se restauró el código compatible con la base, sin actualizar módulos, sin
modificar datos y sin reiniciar contenedores. Tras la recarga automática de
Odoo, los tres modelos volvieron a estar disponibles.

## Prevención

El directorio montado por Odoo para `madenat_test` se considera operativo y no
se utiliza para desarrollo. Cada validación se ejecuta con addons, base y
filestore temporales aislados, conforme a `CANON/11_FASE_E_VALIDACION.md`.

## Evidencia

El informe técnico de recuperación y sus logs se conservan temporalmente hasta
la autorización de higiene y limpieza correspondiente.
