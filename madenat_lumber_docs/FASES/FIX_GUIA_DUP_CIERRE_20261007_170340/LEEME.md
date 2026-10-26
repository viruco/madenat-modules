# FIX_GUIA_DUP_CIERRE_20261007_170340 — Cierre de validación de duplicados

Entrega **AISLADA** (copia de trabajo + bases de pruebas dedicadas). **NO aplicada** al árbol
activo `custom_addons` ni a `madenat_test`. Sin `commit`/`push`. Construcción **incremental**
sobre `FIX_GUIA_DUP_20261007_164415`.

## Contenido

| Ruta | Qué es |
|---|---|
| `docs/INFORME_CIERRE.md` | Informe + respuestas de CIERRE (1–5). |
| `docs/MATRIZ_ALINEACION.md` | Regla → fuente CANON → actual → propuesto → estado (+ conflictos). |
| `docs/MATRIZ_COMPORTAMIENTO.md` | Comportamiento antes → después (A–K). |
| `docs/RESULTADOS_PRUEBAS.md` | Resultados y cobertura. |
| `docs/00_BASELINE.md` | Baseline + explicación «45 vs 47 vs un archivo». |
| `docs/PLAN_APLICACION_REVERSION.md` | Aplicación/reversión + decisiones pendientes. |
| `patch/incremental/` | Diff vs el **parche previo**. |
| `patch/consolidado/` | Diff vs el **árbol activo** (listo para revisión). |
| `addons/` | Copia de trabajo parcheada (montada `:ro`). |
| `verify_unpatched/addons/` | Modelos del **parche previo** + pruebas nuevas (control negativo). |
| `logs/iso_run.log` | `0 failed, 0 error(s) of 38 tests`. |
| `logs/iso_run_unpatched.log` | `1 failed, 5 error(s)` (fallan las 6 de A/B/C). |
| `run_iso.sh`, `run_iso_unpatched.sh` | Ejecución aislada reproducible. |

## Reproducir

```bash
bash run_iso.sh            # ajustes A/B/C -> dupval2_iso_20261007
bash run_iso_unpatched.sh  # parche previo -> dupval2_neg_20261007
```

## Aplica solo con aprobación (no ejecutado)

Ver `docs/PLAN_APLICACION_REVERSION.md`. **Esta entrega no autoriza el despliegue.**
