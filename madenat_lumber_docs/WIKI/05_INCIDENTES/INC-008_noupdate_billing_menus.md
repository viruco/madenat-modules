# INC-008: `noupdate="1"` en menús de billing impide actualización incremental

**ID:** INC-008
**Fecha:** 2026-06-06
**Estado:** RESUELTO
**Severidad:** Alta (mantenibilidad)
**Módulo afectado:** madenat_lumber_billing

---

## Síntoma

Los menús de billing no se actualizaban al ejecutar `--update madenat_lumber_billing`. Cualquier cambio en la definición de menús (nuevo submenú, cambio de nombre, cambio de parent) requería `--init` o borrado manual del registro en base de datos.

## Causa raíz

`lumber_billing_menu_data.xml` usaba `<data noupdate="1">`, lo que le dice a Odoo que no reimporte estos registros durante `--update`. Esto es correcto para datos semilla (secuencias, workflows, registros de negocio), pero incorrecto para menús (que son estructurales y deben actualizarse con el módulo).

## Solución

Cambiar a `<data noupdate="0">`. Las secuencias y workflows de billing están en archivos separados (`billing_sequences.xml`, `billing_workflows.xml`) y no se ven afectados.

## Archivos modificados

`madenat_lumber_billing/data/lumber_billing_menu_data.xml` — línea 3

## Verificación

Un `--update madenat_lumber_billing` ahora aplica cambios a menús correctamente.

## Relacionado

- REMEDIACION_CRITICA_2026-06-06.md — Cambio #5
- AUDITORIA_INTEGRAL_2026-06-06.md — Hallazgo A-R2