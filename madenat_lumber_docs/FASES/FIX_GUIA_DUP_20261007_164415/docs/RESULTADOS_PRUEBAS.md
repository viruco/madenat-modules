# Resultados de pruebas en aislamiento

## Comandos ejecutados

- **Positivo (parcheado):** `run_iso.sh` → contenedor `dupval_iso` sobre `dupval_iso_20261007`
  (`logs/iso_run.log`).
- **Negativo (sin parche):** `run_iso_unpatched.sh` → contenedor `dupval_neg` sobre
  `dupval_neg_20261007` (`logs/iso_run_unpatched.log`).

Ambos: `-u madenat_lumber_core`, `--test-enable`, usuario operativo real
(`new_test_user` con `group_madenat_operaciones`) en las acciones bajo prueba, **sin superusuario**.

## Resultado global

| Corrida | Resultado |
|---|---|
| **Parcheado** (26 nuevos + 8 de regresión = 34) | **`0 failed, 0 error(s) of 34 tests`** |
| **Negativo sin parche** (26) | **`4 failed, 12 error(s) of 26 tests`** |

Los `12 error(s)` del negativo son `unique constraint "madenat_guia_processing_
unique_guia_processing_name_per_partner"` (el backstop SQL C4 disparando como `IntegrityError`
crudo al no existir el control de aplicación) y `4 failed` son los `assertRaises(UserError)`
que **no** se cumplen (incluye el caso `partner_id` nulo, donde el SQL **no** protege: la brecha).

## Cobertura por caso (mapea a las 26 pruebas obligatorias)

Leyenda: ✔ verificado por framework (test unitario Odoo). Ø = fuera del alcance de la ruta
(unidad), documentado.

| # | Caso | Test | Verificado |
|---|---|---|---|
| 1 | Documento nuevo | `test_01_new_guide_passes` | ✔ |
| 2 | Duplicado confirmado (mismo modelo) | `test_02_..._create`, `test_02b_..._write` | ✔ |
| 3 | Coincidencia entre modelos | `test_03_cross_model_homonym_not_blocked` | ✔ |
| 4 | Número homónimo, documento distinto | `test_04_same_number_distinct_supplier_not_blocked` | ✔ |
| 5 | Identidad incompleta | `test_05_incomplete_capture_preserved` | ✔ |
| 6 | Identidad completada revela duplicado | `test_06_...`, `test_06b_...` | ✔ |
| 7 | Documento cancelado | `test_07_cancelled_existing_still_blocks` | ✔ |
| 8 | Exclusión propia por modelo e id | `test_08_...`, `test_08b_exclusion_is_model_scoped` | ✔ |
| 9 | create individual | `test_01` | ✔ |
| 10 | create múltiple con duplicado en el lote | `test_10_batch_create_intra_lote_duplicate_blocks` | ✔ |
| 11 | write individual | `test_02b` | ✔ |
| 12 | write sobre varios registros | `test_12_write_multi_intra_lote_duplicate_blocks` | ✔ |
| 13 | Escritura de campo ajeno a la identidad | `test_13_write_unrelated_field_not_validated` | ✔ |
| 14 | Extracción que asigna el número tras create | `test_14_extraction_assigns_number_blocks_on_duplicate` | ✔ |
| 15 | Relectura del propio documento | `test_15_reread_own_document_no_block` | ✔ |
| 16 | PDF y Excel complementarios | `test_16_complementary_documents_no_second_header` | ✔ (idempotencia) |
| 17 | PDF y Excel contradictorios | — | Ø (lo cubre Gate 1 / conciliación existentes; no se altera) |
| 18 | Procesado | `test_18_procesado_route_write_blocks` | ✔ (ruta = write de identidad) |
| 19 | Volúmenes | `test_19_volumen_route_write_blocks` | ✔ (ruta = write de identidad) |
| 20 | Formulario directo | `test_20_direct_form_write_blocks` + `test_14` | ✔ |
| 21 | Recepción/Producto (regresión) | `test_21_reception_path_regression` + `TestDuplicateValidation` (8) | ✔ |
| 22 | Reintento / doble ejecución | `test_22_retry_double_execution` | ✔ |
| 23 | Sin duplicación de líneas/efectos | `test_23_no_partial_header_or_lines_after_block` | ✔ (cabecera; ver límites) |
| 24 | Rollback completo ante rechazo | `test_24_rollback_on_rejection` | ✔ |
| 25 | Usuario autorizado y visibilidad | `test_25_authorized_and_unauthorized_users` | ✔ |
| 26 | Dos transacciones concurrentes | `test_26_concurrency_backstop_is_sql_constraint` | **NO** (sólo se documenta el backstop SQL) |

### Qué NO se probó (y por qué)

- **Concurrencia real (26):** no se simuló dos cursores simultáneos. El `search` previo
  protege el caso **secuencial**; **no** se declara blindaje concurrente.
- **Duplicación de productos/lotes/movimientos (23):** sólo se verificó la **cabecera** y sus
  líneas de staging; no se probó la no-duplicación de lotes/movimientos (no se alcanza: el
  bloqueo ocurre antes de materializar).
- **PDF/Excel contradictorios (17):** fuera de alcance; ya existe Gate 1 / conciliación.
- **Navegador/UI:** no se probó por navegador; las rutas afectadas convergen en `write()`.
