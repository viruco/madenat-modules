# 00 — Baseline y explicación del estado Git

**Fecha:** 2026-10-07 · Entrega **AISLADA** (no aplicada).

## 1. Estado actual registrado

| Dato | Valor |
|---|---|
| Raíz Git | `custom_addons/.git` (raíz del repo = `custom_addons/`) |
| Rama | `feat/guia-correccion-documental-preservada-20261002` |
| HEAD | `e302c488321c276af7e07f1abeecc8bc261a89f4` (sin cambios) |
| `git status --short` | **47 entradas** = 41 modificadas (`M`) + 6 sin seguimiento (`??`) |
| `git stash list` | vacío |
| Reset/checkout/commit/push | **NO** ejecutados |

Hashes de los archivos pertinentes (árbol activo, antes del parche):

```
eaccfd9df77ed23d2a87b07d1f2dd651c82ff9bf22b850c866ca2d375a3b1420  models/reception_parser.py
5d69049256522f5014098aa57e4273acf43bcc29496153feb594987bd9496ae2  models/madenat_guia_processing.py
231f9dc683d33b2d66501cf5d215f3b5e7cbb9ff9910d1980f0bce12d6ac2fc0  models/reception_workflow.py
```

## 2. Explicación de «45 entradas» vs «un único archivo sucio»

**Evidencia:**

- `FASE_C_20261007_154556/RESUMEN_FASE_C.md:104` registra literalmente:
  > «Código sin cambios en Fase C: HEAD `e302c488…`; `git status` = **45 entradas**
  > (igual que al cierre de Fase B)».
- Hoy el conteo es **47** (41 `M` + 6 `??`). La diferencia de 2 corresponde a
  **archivos sin seguimiento** añadidos por intervenciones autorizadas posteriores
  (p. ej. `madenat_lumber_intake/tests/test_guia_delete_acl.py`,
  `madenat_lumber_intake/tests/test_guide_lifecycle_*.py`).
- La entrega previa (`FIX_GUIA_DUP_20261007_164415/docs/00_BASELINE.md`) declaraba
  «sucio (pre-existente): `M … madenat_guia_processing.py`». Esa frase era una
  **vista ACOTADA al archivo de identidad** (se obtuvo filtrando el `git status`
  por los nombres relevantes a la intervención: `reception_parser|guia_processing|
  guide_duplicate`). **No** era el conteo global del árbol.

**Conclusión:** no hay pérdida de cambios. El árbol activo lleva un conjunto
**pre-existente de ~45–47 entradas sucias** provenientes de intervenciones
previas autorizadas (Fase B/C/D, FIX_ACL_GUIA aplicado, FIX_DELETE_INTAKE,
IMPL_SERVICE_RETURN, logística D2/B2, costeo C2…). La mención de «un único
archivo» fue una lectura **filtrada**, no el estado global. Procedencia
reconstruible: HEAD y rama idénticos; hashes de los archivos del alcance
coinciden con el baseline; stash vacío.

## 3. Aislamiento de esta intervención

| Elemento | Valor |
|---|---|
| Copia de trabajo | `FIX_GUIA_DUP_CIERRE_20261007_170340/addons` (copia del workcopy **ya parcheado** de `FIX_GUIA_DUP_20261007_164415`, montada `:ro`) |
| Base aislada (parcheado) | `dupval2_iso_20261007` (clon de `aclf_test_20261007`) |
| Base aislada (negativo) | `dupval2_neg_20261007` |
| Imagen / red | `odoo-18-ce-web:latest` / `odoo-18-ce_internal_backend` |
| Contenedores | one-shot `--rm` (sin HTTP, sin cron, `--stop-after-init`) |
| Servicios activos / `madenat_test` | **no tocados** |

Construcción **incremental**: se parte del workcopy parcheado previo y se aplican
solo los ajustes A/B/C (no hay reimplementación).
