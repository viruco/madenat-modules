# D13 — Restitución de los cuerpos §17.16.19…§17.16.29 en `CANON/02` (verificación)

**Resultado:** **CORREGIDA**. Se insertaron los **11 cuerpos literales**, **sin** modificar ninguna línea
existente (solo el encabezado de versión, por mandato).

## Mapeo sección → expediente fuente (literal)
| Sección | Título | Expediente fuente (ruta exacta) | § de la fuente |
|---|---|---|---|
| 17.16.19 | Auditoría integral y blindaje (AUD-ETQ-01..05) | `FASES/AUDIT_REBAJA_ETIQUETAS_20261011/README.md` | §1 (dictamen) |
| 17.16.20 | Cierre probatorio (AUD-ETQ-06..10) | `FASES/AUDIT_REBAJA_ETIQUETAS_20261011/README.md` | §«CIERRE PROBATORIO» |
| 17.16.21 | Contrato de aplicación sin reparto | `FASES/CONTRATO_APLICACION_20261011/README.md` | §1 |
| 17.16.22 | Persistencia y recuperación (SAVE) | `FASES/SAVE_REBAJA_20261011/README.md` | §1 |
| 17.16.23 | Acciones visibles del asistente (UI) | `FASES/UI_SAVE_REBAJA_20261011/README.md` | §1 |
| 17.16.24 | Simplificación operativa (SIMPLE) | `FASES/SIMPLE_REBAJA_20261011/README.md` | §1 |
| 17.16.25 | Volver a borrador y reasignar (RESET) | `FASES/RESET_REBAJA_20261011/README.md` | §1/§2 |
| 17.16.26 | Blindaje local y estabilización (AUD-ETQ-07/08) | `FASES/BLINDAJE_REBAJA_LOCAL_20261012/README.md` | §0/§1/§2 |
| 17.16.27 | Verificación probatoria P1–P4 | `FASES/VERIF_CUATRO_PUNTOS_20261012/README.md` | §1 |
| 17.16.28 | Blindaje de borradores (LOCK) | `FASES/BLINDAJE_SOBRESCRITURA_20261012/README.md` | §1 |
| 17.16.29 | Cierre V1–V3 del blindaje | `FASES/CIERRE_SOBRESCRITURA_V123_20261012/README.md` | §1 |

**Ninguna sección quedó sin fuente** ⇒ no se emitió ningún «cuerpo pendiente: fuente no localizada».

## Verificación reproducible (`code/fase2_d13_verify.py` → `logs/d13_verify.log`)
```
secciones 17.16.19..29 -> presentes: 11/11
referencias a 17.16.19..29: {19:7, 20:2, 21:4, 22:2, 23:2, 24:2, 25:2, 26:2, 27:2, 28:2, 29:5} (total 32)
  sin resolver: ninguna
versión 02: cabecera=12.40.0  máx.declarada=12.38.0  OK
marcadores 02: <!--=30 -->=30 OK
RESULTADO D13: OK
```
- **11/11** secciones presentes y **únicas**.
- **0** referencias cruzadas sin resolver (las **26** originales + las que añadir el propio cuerpo → **32**).
- **Versión monótona**: `02` 12.39.0 → **12.40.0**; **índice** 12.29.0 → **12.30.0**. No se reutilizó numeración.
- **Marcadores balanceados** (30/30).
- **Diff de la sesión** (`logs/diff_session_docs.diff`): **solo AÑADIDOS**, salvo las líneas de versión/fecha
  (5 líneas) exigidas por el mandato; **ninguna** línea de contenido existente cambió.
- **Posición numérica:** los cuerpos se insertaron entre `§17.16.18` y `§17.16.30` (orden 18 → 19…29 → 30).

**Fuente única:** todo vive en `custom_addons/madenat_lumber_docs` (canónico). **No** se creó ningún documento
paralelo.
