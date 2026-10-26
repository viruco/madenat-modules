# Plan de aplicación y reversión (NO ejecutado)

## A. Archivos intervenidos (rutas relativas a `custom_addons/madenat_lumber_core/`)

**Código productivo** (agregado +74 / borrado −23 líneas vs el parche previo):
| Archivo | Diff incremental | Diff consolidado |
|---|---|---|
| `models/reception_parser.py` | `patch/incremental/models_reception_parser.py.diff` | `patch/consolidado/models_reception_parser.py.diff` |
| `models/madenat_guia_processing.py` | `patch/incremental/models_madenat_guia_processing.py.diff` | `patch/consolidado/models_madenat_guia_processing.py.diff` |

**Pruebas/documentación** (agregado +95 / borrado −16 líneas):
| Archivo | Diff incremental | Diff consolidado |
|---|---|---|
| `tests/test_guide_duplicate_ingest.py` | `patch/incremental/tests_test_guide_duplicate_ingest.py.diff` | `patch/consolidado/…` (nuevo) |
| `tests/test_duplicate_validation.py` | `patch/incremental/tests_test_duplicate_validation.py.diff` | `patch/consolidado/…` |
| `tests/__init__.py` | (sin cambio en esta entrega) | `patch/consolidado/tests___init__.py.diff` |

> El diff **consolidado** es respecto del **árbol activo** (`custom_addons`) e incluye el
> parche previo + esta entrega. El **incremental** es respecto del parche previo
> (`FIX_GUIA_DUP_20261007_164415`) y es el que debe revisarse aquí.

## B. Aplicación (tras aprobación)

1. Con `odoo18_app` detenido (o ventana operativa), aplicar el diff **consolidado** de
   `models/` y `tests/` sobre `custom_addons/madenat_lumber_core/`:
   ```
   patch -p4 < <carpeta>/patch/consolidado/models_reception_parser.py.diff
   patch -p4 < <carpeta>/patch/consolidado/models_madenat_guia_processing.py.diff
   patch -p4 < <carpeta>/patch/consolidado/tests_test_guide_duplicate_ingest.py.diff
   patch -p4 < <carpeta>/patch/consolidado/tests_test_duplicate_validation.py.diff
   patch -p4 < <carpeta>/patch/consolidado/tests___init__.py.diff
   ```
   (o aplicar el incremental si se parte del workcopy previo; ajustar `-p`).
2. `-u madenat_lumber_core` (contenedor one-shot `--no-http --max-cron-threads=0
   --stop-after-init`).
3. Reiniciar `odoo18_app`.
4. Repetir la suite (`TestGuideDuplicateIngest`, `TestDuplicateValidation`) → `0 failed`.

## C. Reversión

- Código: `patch -R` (orden inverso) o `git checkout` de los 2 modelos + los tests.
- Esquema/ACL: **sin cambios** (no hay campos, ACL ni constraints nuevos).
- Riesgo: **bajo** — sólo lógica de validación en `create()`/`write()` de la guía y firma
  de C1 (compatible hacia atrás: `raise_on_match=True`, `cross_model` presente).

## D. Decisiones necesarias antes de producción (separadas)

1. **Índice único parcial** para el residuo `partner_id` nulo (¿se aprueba? ¿con qué
   limpieza de datos históricos?). No incluido.
2. **Ratificación AD-88** del aviso pasivo (o convertir en desviación con motivo).
3. **Aviso en la ruta de Recepción** (simétrica): ¿se añade chatter también allí?
