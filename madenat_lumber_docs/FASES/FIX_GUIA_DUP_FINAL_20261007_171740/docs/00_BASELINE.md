# 00 — Baseline y aislamiento (cierre de avisos y compatibilidad)

**Fecha:** 2026-10-07 · Entrega **AISLADA**. **NO aplicada.**

## Estado Git registrado

| Dato | Valor |
|---|---|
| Raíz Git | `custom_addons/.git` |
| Rama | `feat/guia-correccion-documental-preservada-20261002` |
| HEAD | `e302c488321c276af7e07f1abeecc8bc261a89f4` (sin cambios) |
| `git status --short` | **47 entradas** (conteo global; 41 `M` + 6 `??`) |
| Reset/checkout/commit/push/stash | **NO** ejecutados (`git stash list` vacío) |

> El conteo **global** del árbol sigue siendo 47 (estado pre-existente de intervenciones
> previas autorizadas). Se separa del **conteo filtrado** por los archivos del alcance
> (que se listan abajo). No se alteró ningún cambio preexistente.

Hashes del árbol activo relevantes (antes): 

```
eaccfd9df77ed23d2a87b07d1f2dd651c82ff9bf22b850c866ca2d375a3b1420  models/reception_parser.py
5d69049256522f5014098aa57e4273acf43bcc29496153feb594987bd9496ae2  models/madenat_guia_processing.py
231f9dc683d33b2d66501cf5d215f3b5e7cbb9ff9910d1980f0bce12d6ac2fc0  models/reception_workflow.py
86ff5c3715aa13cfe27c587e005b0abe8b2a88a86280330fb73a7b7bc0aca252  models/lumber_reception.py
70511480c97c7b9be468e13fdf4aff8ac4389d2497f613b3ce82be7b4e95a174  models/mixin_lumber_ingest.py
```

## Aislamiento

| Elemento | Valor |
|---|---|
| Copia de trabajo | `FIX_GUIA_DUP_FINAL_20261007_171740/addons` (copia del workcopy **CIERRE** previo, montada `:ro`) |
| Base aislada (positivo) | `dupval3_iso_20261007` (clon de `aclf_test_20261007`) |
| Base aislada (negativo) | `dupval3_neg_20261007` |
| Imagen / red | `odoo-18-ce-web:latest` / `odoo-18-ce_internal_backend` |
| Contenedores | one-shot `--rm` (`dupval3_iso`, `dupval3_neg`), sin HTTP/cron |
| Servicios activos / `madenat_test` | **no tocados** |

## Fuentes documentales leídas

`CANON/12_FLUJOS_INGESTA.md` (§2, §3.3, §5.2, §6.2, §11.5–11.7), `CANON/04_DECISION_LOG.md`
(AD-80, **AD-88**), `CANON/00_ARQUITECTURA.md` (§4.2/§4.3/§4.5), `CANON/17_CONSTITUCION_VOLUMENES.md`
(§1.4). Documentos de la entrega previa: `MATRIZ_ALINEACION.md`, `00_BASELINE.md`,
`RESULTADOS_PRUEBAS.md`, `PLAN_APLICACION_REVERSION.md`, `patch/`. **No** se modificó CANON.
