# Plan de aplicación y reversión (NO ejecutado)

## A. Lista de archivos intervenidos (rutas relativas a `custom_addons/madenat_lumber_core/`)

| Archivo | Tipo | Diff |
|---|---|---|
| `models/reception_parser.py` | modificado | `patch/models_reception_parser.py.diff` (236 líneas) |
| `models/madenat_guia_processing.py` | modificado | `patch/models_madenat_guia_processing.py.diff` (99 líneas) |
| `tests/test_guide_duplicate_ingest.py` | **nuevo** | `patch/tests_test_guide_duplicate_ingest.py.diff` |
| `tests/__init__.py` | modificado | `patch/tests___init__.py.diff` (9 líneas) |

Sin cambios de esquema, campos, ACL, grupos, doctrina, parser de lectura, constraints ni datos.

## B. Aplicación propuesta (tras aprobación)

1. Con `odoo18_app` detenido (o ventana operativa), aplicar los diffs sobre `custom_addons/`:
   desde `custom_addons/madenat_lumber_core/`:
   ```
   patch -p4 < <carpeta>/patch/models_reception_parser.py.diff
   patch -p4 < <carpeta>/patch/models_madenat_guia_processing.py.diff
   patch -p4 < <carpeta>/patch/tests___init__.py.diff
   patch -p4 < <carpeta>/patch/tests_test_guide_duplicate_ingest.py.diff
   ```
   (los diffs se generan contra `custom_addons/madenat_lumber_core/...`; ajustar `-p` según el prefijo).
2. `-u madenat_lumber_core` (contenedor one-shot `--no-http --max-cron-threads=0 --stop-after-init`).
3. Reiniciar `odoo18_app`.
4. Repetir la suite en la base de destino y verificar `0 failed`.

## C. Reversión

- Código: `patch -R` de los diffs (orden inverso) o `git checkout` de los 2 modelos y borrado del
  test nuevo + la línea del `tests/__init__.py`.
- Esquema: ninguno (no hay cambios de esquema). Reejecutar `-u madenat_lumber_core` si se desea.
- Riesgo: **bajo** — cambios acotados a `create()`/`write()` de la guía y a la firma de C1
  (compatible hacia atrás). No toca stock, valoración, contabilidad, ACL ni datos históricos.

## D. Prerrequisito de concurrency (propuesta separada, NO incluida)

Carrera real con `partner_id` nulo. Propuesta mínima a evaluar **aparte** (no aplicada):
índice único parcial `CREATE UNIQUE INDEX ... ON madenat_guia_processing (name)
WHERE partner_id IS NULL;` — requiere decisión de política y migración de datos existentes
(podría haber duplicados históricos). **No** se propone lock/serialización.

## E. Verificación ya realizada (en aislamiento)

- `logs/iso_run.log` → `0 failed, 0 error(s) of 34 tests` (parcheado).
- `logs/iso_run_unpatched.log` → `4 failed, 12 error(s) of 26 tests` (control negativo).
