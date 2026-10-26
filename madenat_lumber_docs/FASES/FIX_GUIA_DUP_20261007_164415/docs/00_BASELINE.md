# 00 — Baseline y aislamiento

**Fecha:** 2026-10-07 · **Proyecto:** MADENAT Lumber — Odoo 18 CE
(`/home/viruco/dev-stack/odoo/odoo-18-ce`) · **Entrega AISLADA. NO aplicada.**

## 1. Estado inicial registrado

| Dato | Valor |
|---|---|
| Repositorio Git | `custom_addons/.git` (raíz del repo: `custom_addons/`) |
| HEAD | `e302c488321c276af7e07f1abeecc8bc261a89f4` |
| Rama | `feat/guia-correccion-documental-preservada-20261002` |
| Árbol de trabajo | **sucio** (pre-existente): `M madenat_lumber_core/models/madenat_guia_processing.py` (cambios de atribución de retornos, *no* relacionados con esta intervención) |

## 2. Hashes de los archivos fuente (activos, antes del parche)

```
eaccfd9df77ed23d2a87b07d1f2dd651c82ff9bf22b850c866ca2d375a3b1420  models/reception_parser.py
5d69049256522f5014098aa57e4273acf43bcc29496153feb594987bd9496ae2  models/madenat_guia_processing.py
231f9dc683d33b2d66501cf5d215f3b5e7cbb9ff9910d1980f0bce12d6ac2fc0  models/reception_workflow.py
50385938cdc093300e1b984db7a01a46bf1c05ff59f1c109256384304385c96c  tests/test_duplicate_validation.py
```

## 3. Aislamiento

| Elemento | Valor |
|---|---|
| Copia de trabajo | `/home/viruco/dev-stack/odoo/odoo-18-ce/FIX_GUIA_DUP_20261007_164415/addons` (copia de `custom_addons`, montada `:ro`) |
| Control negativo | `.../verify_unpatched/addons` (modelos del **árbol activo**, sin parche) |
| Base aislada (parcheado) | `dupval_iso_20261007` (clon de `aclf_test_20261007`) |
| Base aislada (negativo) | `dupval_neg_20261007` (clon de `aclf_test_20261007`) |
| Imagen | `odoo-18-ce-web:latest` |
| Red | `odoo-18-ce_internal_backend` |
| Contenedores | one-shot `--rm` (`dupval_iso`, `dupval_neg`): `--no-http --max-cron-threads=0 --workers=0 --stop-after-init` |
| Servicios activos | `odoo18_app`, `odoo18_db` — **no tocados**; `madenat_test` — **no tocada** |

**Comprobación de aislamiento previa a mutar:** red e imagen presentes; único servicio con
conexión viva a PostgreSQL era `madenat_test` (la app); todas las demás bases estaban ociosas
y se usaron como plantilla de clonación. **No** se reinició ningún servicio ni se actualizó
módulo en el entorno activo.
