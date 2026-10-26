# FIX_GUIA_DUP_20261007_164415 — Validación efectiva de guías duplicadas

Entrega AISLADA (copia de trabajo + base de pruebas dedicada). **NO aplicada** al árbol activo
`custom_addons` ni a `madenat_test`. Sin `commit`/`push`.

## Contenido

| Ruta | Qué es |
|---|---|
| `docs/INFORME_FIX_GUIA_DUP.md` | Informe + CIERRE EXIGIDO (6 respuestas). |
| `docs/MATRIZ_IDENTIDAD.md` | Matriz de identidad (resolución de D1). |
| `docs/RESULTADOS_PRUEBAS.md` | Resultados y cobertura de las 26 pruebas. |
| `docs/PLAN_APLICACION_REVERSION.md` | Plan de aplicación y reversión (no ejecutado). |
| `docs/00_BASELINE.md` | HEAD, hashes, aislamiento. |
| `patch/*.diff` | Diff mínimo (2 modelos + tests + `__init__`). |
| `addons/` | Copia de trabajo parcheada (montada `:ro`). |
| `verify_unpatched/addons/` | Copia con modelos SIN parche (control negativo). |
| `logs/iso_run.log` | `0 failed, 0 error(s) of 34 tests` (parcheado). |
| `logs/iso_run_unpatched.log` | `4 failed, 12 error(s) of 26 tests` (sin parche). |
| `run_iso.sh`, `run_iso_unpatched.sh` | Comandos de ejecución aislada. |

## Reproducir

```bash
bash run_iso.sh            # positivo (parcheado)  -> dupval_iso_20261007
bash run_iso_unpatched.sh  # negativo (sin parche) -> dupval_neg_20261007
```

## Aplica solo con aprobación (no ejecutado)

Ver `docs/PLAN_APLICACION_REVERSION.md`.
