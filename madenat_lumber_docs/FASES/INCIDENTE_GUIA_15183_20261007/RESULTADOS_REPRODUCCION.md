# RESULTADOS DE REPRODUCCIÓN (aislada)

## Identidad del entorno de reproducción

| Elemento | Valor |
|---|---|
| Código | Copia de trabajo `INCIDENTE_GUIA_15183_20261007/workcopy/addons` (bind `:ro`), **byte-idéntica** al árbol activo (verificado por SHA-256) |
| Hash `reception_parser.py` | `816081f1d083f78ee7d93b83468895aa203c6731fba84500a5e6814fb8af549b` (activo) |
| Hash `madenat_guia_processing.py` | `98a4caeaf5638b5be27f6e76c00a5078c2a2e92135fd03506e07666ec05b2075` |
| Hash `reception_workflow.py` | `3df39636518b68a526526886cfd84995bec413a1cc707dfcf67297a245e3f017` |
| Hash `mixin_lumber_ingest.py` | `40fbc5dfee1140a8f2ebf2c12f68d49f7cee4e08ffd30d9e478c042a2c762215` |
| Base de datos | `repro_inc_15183_20261007` (**copia** restaurada de `madenat_test`; el activo **no** se tocó) |
| Contenedor | `repro_inc_15183` (`odoo-18-ce-web:latest`), `--no-http --workers=0 --max-cron-threads=0`, red `odoo-18-ce_internal_backend` |
| Usuario | Administrador (setup) + **usuario operativo real** `gdup15183_ops` para las acciones bajo prueba (**su=False**) |
| Efectos externos | Ninguno (sin HTTP, sin cron, sin correo, sin integraciones) |

> **[V]** El árbol activo `custom_addons/` **no** fue modificado: la prueba se
> añadió **sólo** en la copia y se montó `:ro`. `madenat_test` sólo recibió `SELECT`
> y un `pg_dump` de lectura.

## Comando reproducible

```bash
docker run --rm --name repro_inc_15183 \
  --network odoo-18-ce_internal_backend \
  -v .../INCIDENTE_GUIA_15183_20261007/workcopy/addons:/mnt/extra-addons:ro \
  odoo-18-ce-web:latest \
  odoo --db_host=db --db_user=odoo --db_password=odoo --db_port=5432 \
  --database=repro_inc_15183_20261007 \
  --addons-path=/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons \
  -u madenat_lumber_core --max-cron-threads=0 --workers=0 \
  --test-enable --test-tags=/madenat_lumber_core:TestGuideDuplicateRegression15183 \
  --stop-after-init --no-http --log-level=test
```

## Resultado

```
odoo.tests.result: 2 failed, 0 error(s) of 4 tests when loading database 'repro_inc_15183_20261007'
```

| Test | Qué prueba | Esperado | Resultado |
|---|---|---|---|
| `E1_exact_incident_real_rows` | Sobre las **filas reales** (Recepción 1369 + excluir guía 33154): `cross_model=False` **no** ve la Recepción; `cross_model=True` **sí** | PASA (evidencia del mecanismo) | **PASS** |
| `NG1_distinct_issuer_same_number_not_blocked` | Mismo número, emisor **distinto** ⇒ homónimo: **no** bloquea | PASA (no sobre-bloqueo) | **PASS** |
| `R1_same_document_across_models_blocks_on_create` | Recepción `REPRO-15183` (emisor E) + crear Procesado mismo nº/emisor ⇒ **debe bloquear** | falla con el código actual | **FAIL** (`UserError not raised`) |
| `R2_same_document_across_models_blocks_on_write` | Ruta fachada (incompleto→completo) ⇒ **debe bloquear** | falla con el código actual | **FAIL** (`UserError not raised`) |

- **[V]** `R1`/`R2` **fallan** ⇒ se **confirma la brecha**: el código activo **no**
  bloquea el mismo documento (`número+emisor`) entre flujos.
- **[V]** `E1` reproduce el log real: `cross_model=False` → «sin duplicados»;
  `cross_model=True` → halla `lumber.reception` id 1369.
- **[V]** `NG1` confirma que un homónimo legítimo (emisor distinto) **sigue sin
  bloquear** ⇒ la corrección propuesta **no** debe romperlo.

Logs: `logs/iso_run_regression.log`, `logs/iso_run_summary.txt`,
`logs/incidente_window_log.txt`. Prueba: `PRUEBA_REGRESION_test_guide_dup_regression_15183.py`.

## Cobertura de los escenarios solicitados (A–G)

| Caso | Estado | Nota |
|---|---|---|
| A. Recepción existente (staging, sin stock) → leer como Procesado | **Reproducido** (`E1` real + `R1`) | la Recepción existe `verified`, sin lotes propios de la guía |
| B. Caso inverso (guía existente → ingreso por Recepción) | **Cubierto por simetría** | ambas rutas usan `cross_model=False`; la Recepción no vería la guía |
| C. Documento distinto con número homónimo | **Reproducido** (`NG1`) | emisor distinto ⇒ no bloquea |
| D. Número conocido antes que proveedor | **Cubierto** | `write({'name'})` → AJUSTE A no bloquea |
| E. Proveedor conocido antes que número | **Cubierto por AJUSTE A** | revalida al completar |
| F. Relectura del propio ingreso | **Cubierto** | `exclude_id`+`exclude_model` (self-exclusion) |
| G. Documento existente ya materializado en stock | **Comparación** | la recepción 1369 **tiene** picking 436/lotes; el bloqueo es igualmente indiferente al stock |

> **[I]** Los escenarios `B`, `E`, `F` se apoyan en el mismo contrato de
> `_check_guide_duplicate` verificado en `E1`/`DOC`; no requieren fixture adicional.
> **No** se llama «reproducción exacta» a ningún fixture: `E1` usa las **filas
> reales** del incidente (número `15183`, emisor `1052`).
