# RUNBOOK FASE 10 — Despliegue de S2/S3/S1 (registro de etiquetas en la rebaja SV)

> **Estado:** PREPARADO, **NO ejecutado**. Sin push, sin conexión al remoto, sin despliegue.
> **Origen:** `INFORME_FASE10.md` · `DIAGNOSTICO_REBAJA_SV841_REGISTRO_ETIQUETAS_20261015/`.
> **Alcance del despliegue:** **solo** `madenat_lumber_logistics` (versión **18.0.1.32.0**). Nada de `costing`
> ni del menú de `reports`.

## 1. Commits a desplegar (rama `feat/guia-correccion-documental-preservada-20261002`)

| Orden | Hash | Contenido | Versión |
|---|---|---|---|
| 1 | `19611d0` | S2 — lista/contador de «Trabajo en preparación» + «Continuar» operativo | 18.0.1.29.0 → 18.0.1.30.0 |
| 2 | `e2d6b64` | S3 — bloqueo del guardado sin etiquetas (sin borrado silencioso) | 18.0.1.30.0 → 18.0.1.31.0 |
| 3 | `7ac1fcb` | S1 — firma/clave con las etiquetas seleccionadas + reglas de estado terminal | 18.0.1.31.0 → 18.0.1.32.0 |
| 4 | `ee7b7c6` | docs(canon) AD-109 (CANON/04, 19, 05, INDICE) | — |

Base: `677294b`. **No** mezclar con el WIP de `costing` (10 archivos) ni con el menú de `reports` (1 archivo):
el despliegue debe partir de un árbol **sin** esos 11 cambios locales (o con ellos claramente excluidos).

## 2. Pre-requisitos

1. **Respaldo**: dump de la base + `tar` del árbol desplegado (mismo procedimiento de A1 usado en esta fase:
   `pre/custom_addons_worktree.tar.gz`, `pre/madenat_test_pre_fase10.dump.gz`, con `gzip -t`).
2. **Verificar HEAD local** = `ee7b7c6` y `git status` = las **11** entradas conocidas de `costing`/`reports`.
3. Confirmar que **no** hay ninguna corrida de Odoo activa contra la base destino.

## 3. Despliegue (LOCAL primero, luego remoto **solo con autorización expresa**)

```bash
# 3.1 Actualizar SOLO logistics (sin -u all)
docker exec odoo18_app odoo -d <BD_DESTINO> \
  -u madenat_lumber_logistics \
  --stop-after-init --http-port=9995 --max-cron-threads=0

# 3.2 Suites del flujo corregido (deben quedar en verde)
docker exec odoo18_app odoo -d <BD_DESTINO> \
  -u madenat_lumber_logistics --test-enable \
  --test-tags=/madenat_lumber_logistics:TestSvRebajaWorkFilter,/madenat_lumber_logistics:TestSvRebajaEmptyGuard,/madenat_lumber_logistics:TestSvRebajaDocumentaryKey \
  --stop-after-init --http-port=9995 --max-cron-threads=0
```

**Comprobación de retrocompatibilidad (clave histórica):** en consola de Odoo,

```python
g = env['madenat.guia.processing'].browse(1198)
env['madenat.sv.imputation']._i2_build_documentary_key(g, None, '')
# debe devolver IMP-1198-E95825AAF94E58AD  (clave histórica de IMP02220, sin cambios)
```

## 4. Pruebas de humo (tras desplegar)

| # | Paso | Resultado esperado |
|---|---|---|
| H1 | Abrir «Rebaja de etiquetas», elegir un SV con documentos anulados (p. ej. `SV00000000841`) | La sección «Trabajo en preparación» **no** muestra el documento anulado y el contador «Trabajo en prep.» es **0** |
| H2 | Abrir el asistente y pulsar **Guardar** **sin** seleccionar ninguna etiqueta | **Bloqueado** con mensaje en español pidiendo seleccionar al menos una etiqueta; **no** se crea documento |
| H3 | Seleccionar 1–2 etiquetas y **Guardar** (sin cantidades) sobre una guía que ya tiene un documento **aplicado** | Se crea un documento **nuevo** y **las etiquetas quedan registradas**; **no** aparece «ya no admite preparación (estado applied)» |
| H4 | Repetir el mismo Guardar (misma selección) | Reutiliza el **mismo** borrador (no duplica) |
| H5 | Sobre un documento **anulado** de la misma guía, preparar la **misma** selección | Se crea un documento **nuevo** (clave distinta); el anulado queda **intacto** y sin «Volver a borrador» forzado |
| H6 | Aplicar una selección y volver a preparar **la misma selección** | Mensaje claro «ya se aplicó con esta misma selección»; **no** se duplica |
| H7 | Documento **aplicado**: botón «Continuar» | Mensaje operativo (no error técnico); el aplicado no se reabre |
| H8 | Anular un borrador y luego «Volver a borrador» con motivo | Sigue funcionando (RESET intacto) |
| H9 | Regresión funcional de la rebaja normal (seleccionar → cantidad → Aplicar) | Igual que antes («Rebajado documental» correcto) |

**Chequeo de no-cambios:** `IMP02220` y `IMP04823` deben conservar estado, valores y clave
(`IMP-1198-E95825AAF94E58AD` y `IMP-1198-A87816E2021EC9AA`).

## 5. Reversión

* Revertir = volver a desplegar el árbol/base del respaldo (§2). **No** hay migración de datos ni cambios de
  esquema que deshacer.
* Las claves creadas por el flujo nuevo son válidas y consultables; un documento creado con discriminador no
  interfiere con los documentos existentes.

## 6. Límites de este runbook

* **Sin** `-u all`; **sin** cambios en datos reales; **sin** tocar `IMP04823`/`IMP02220`; **sin** migrar claves
  históricas.
* Pendientes que **no** cubre: decisión sobre `IMP04823`, resolución de `SV00000000841` en datos reales,
  verificación en el remoto, trigger/bitácora, `VIEW-01/04`, D1 (`costing`) y P2-2.
