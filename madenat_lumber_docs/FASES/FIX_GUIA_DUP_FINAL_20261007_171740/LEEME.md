# FIX_GUIA_DUP_FINAL_20261007_171740 — Cierre de avisos y compatibilidad

Entrega **AISLADA** (copia de trabajo + bases de pruebas). **NO aplicada** al árbol activo ni a
`madenat_test`. Sin `commit`/`push`. Construcción **incremental** sobre
`FIX_GUIA_DUP_CIERRE_20261007_170340`.

## Contenido

| Ruta | Qué es |
|---|---|
| `docs/INFORME_CIERRE.md` | Informe + respuestas de CIERRE + solicitud de aprobación. |
| `docs/LLAMADORES_C1.md` | Inventario de llamadores de C1 + verificación de contratos. |
| `docs/AVISOS_Y_DEDUP.md` | Descripción de avisos y criterio anti-repetición. |
| `docs/RESULTADOS_PRUEBAS.md` | Resultados y cobertura. |
| `docs/00_BASELINE.md` | Hashes, estado Git (47) y aislamiento. |
| `docs/PLAN_APLICACION_REVERSION.md` | Plan exacto (archivos, orden, respaldos, reversión). |
| `patch/incremental/` | Diff vs parche CIERRE. |
| `patch/consolidado/` | Diff vs árbol activo. |
| `addons/` | Copia de trabajo del cierre (montada `:ro`). |
| `verify_unpatched/addons/` | Modelos del parche CIERRE + pruebas nuevas (control negativo). |
| `logs/iso_run.log` | `0 failed, 0 error(s) of 48 tests`. |
| `logs/iso_run_unpatched.log` | `2 failed, 4 error(s)` (los 6 casos del cierre). |
| `run_iso.sh`, `run_iso_unpatched.sh` | Ejecución aislada reproducible. |

## Reproducir

```bash
bash run_iso.sh            # cierre aplicado -> dupval3_iso_20261007
bash run_iso_unpatched.sh  # parche CIERRE -> dupval3_neg_20261007
```

## APLICACIÓN (2026-10-07) — ejecutada en `madenat_test`

La solución consolidada **fue aplicada** al entorno local `madenat_test` tras el gate de
verificación (reconstrucción byte-idéntica + 48/48 tests). Registro completo, hashes antes/después,
respaldos y comprobaciones no destructivas en **`docs/APLICACION_20261007.md`**.
Respaldo: `backups/DUPFIX_20261007_173118/` (código + base + filestore).
**No** desplegado a producción. **No** commit/push. `HEAD` sin cambios (`e302c488…`).


## Aplica solo con aprobación (no ejecutado)

Ver `docs/PLAN_APLICACION_REVERSION.md`. **Esta entrega no autoriza el despliegue.**
