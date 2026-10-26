# RUNBOOK FASE 11 — Despliegue de la integridad del ciclo de vida de las imputaciones SV

> **Estado:** PREPARADO, **NO ejecutado**. Sin push, sin conexión al remoto, sin despliegue.
> **Origen:** `INFORME_FASE11.md` · `AUDITORIA_CICLO_VIDA_IMPUTACIONES_20261015/`.
> **Alcance del despliegue:** **solo** `madenat_lumber_logistics` (versión **18.0.1.36.0**) + los 3 documentos
> canónicos. **Nada** de `costing` ni del menú de `reports`.

## 1. Commits a desplegar (rama `feat/guia-correccion-documental-preservada-20261002`)

| Orden | Hash | Contenido | Versión |
|---|---|---|---|
| 1 | `f597f75` | Código: A-1, B-1, M-2, M-4, B-2, B-3 (+ pruebas, vista y asistente) | 18.0.1.32.0 → **18.0.1.36.0** |
| 2 | `254e6d3` | Documentación: AD-110 (CANON/04, CANON/19 §19.35, índice) | — |

Base: `ee7b7c6`. **No** mezclar con el WIP de `costing` (10 archivos) ni con el menú de `reports` (1): desplegar
desde un árbol sin esos 11 cambios locales.

## 2. Pre-requisitos

1. Respaldo (mismo procedimiento de A1): dump de la base + `tar` del árbol + manifiesto SHA256.
2. Verificar `HEAD` local = `254e6d3` y `git status` con las **11** entradas conocidas (todas de
   `costing`/`reports`).
3. Confirmar que no hay corridas de Odoo activas contra la base destino.

## 3. Despliegue (LOCAL primero; remoto **solo** con autorización expresa)

```bash
docker exec odoo18_app odoo -d <BD_DESTINO> -u madenat_lumber_logistics \
  --stop-after-init --http-port=9995 --max-cron-threads=0

docker exec odoo18_app odoo -d <BD_DESTINO> -u madenat_lumber_logistics --test-enable \
  --test-tags=/madenat_lumber_logistics --stop-after-init --http-port=9995 --max-cron-threads=0
```

Esperado: **4 failed / 0 error** (mismo subconjunto del baseline) y **0 fallas nuevas**. Sin migración de datos ni
cambios de esquema (el módulo sólo cambia lógica de servidor, vista y pruebas).

## 4. Pruebas de humo tras desplegar (transiciones)

| # | Paso | Resultado esperado |
|---|---|---|
| H1 | Abrir un documento en **borrador**, intentar cambiar el estado por importación/ORM (`write({'state':'cancelled'})`) | **Rechazado** con mensaje de negocio («marcas de transición… usa las acciones oficiales»); el documento sigue en borrador |
| H2 | En el mismo borrador, pulsar **Dejar pendiente** y luego **Volver a borrador** | Funciona igual que antes (transiciones oficiales) |
| H3 | Seleccionar etiquetas, indicar m³ y pulsar **Aplicar** | Se aplica; el documento queda **aplicado** con firma, snapshot, ejecutor y fecha; el SV muestra «Rebajado documental» |
| H4 | En el aplicado, escribir el **motivo** en el campo «Motivo» y pulsar **Reversar** con Jefatura | Se reversa; el motivo queda congelado en «Motivo de reversa» (sólo lectura) y el SV libera el saldo |
| H5 | Intentar **Aplicar** sobre un documento **reversado** o **anulado** | **Bloqueado** (mensaje correcto) |
| H6 | **Anular** un borrador **sin** escribir el motivo | **Bloqueado**: «Indique el motivo de la anulación…» |
| H7 | **Anular** escribiendo el motivo | Se anula; el motivo aparece en «Motivo de anulación» (sólo lectura) y en el **chatter**; queda evento `imputation_cancel` con el texto |
| H8 | Con el documento **anulado**, intentar añadir/quitar **líneas** o **repartos** | **Bloqueado** (contenido inmutable); tras **Volver a borrador** (con motivo) sí se editan |
| H9 | Reversar y crear una **nueva** operación con la misma selección | La nueva nace con **«Imputación de origen»** = la reversada; al aplicarla, la reversada muestra «Reversada por» = la nueva |
| H10 | Reversar dos veces / concurrentemente (dos pestañas, motivo distinto) | Sólo una reversa se registra; la segunda recibe conflicto controlado **sin** sobrescribir usuario/fecha/firma |

**Chequeo de no-cambios:** `IMP02220` y `IMP04823` deben conservar estado, valores y clave
(`IMP-1198-E95825AAF94E58AD` y `IMP-1198-A87816E2021EC9AA`).

## 5. Reversión

* Revertir = volver a desplegar el árbol/base del respaldo (§2). No hay migración de datos ni cambios de esquema
  que deshacer.
* Los documentos creados con el flujo nuevo siguen siendo válidos y consultables (misma receta de clave).

## 6. Límites de este runbook

* **Sin** `-u all`; **sin** cambios en datos reales; **sin** tocar `IMP04823`/`IMP02220`/eventos `TX10`.
* Pendientes que **no** cubre: decisión de negocio sobre los datos heredados, **M-3**, granularidad de despliegue
  por concern (los 4 sub-lotes quedaron en 1 commit) y la verificación en el remoto.
