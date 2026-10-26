# IMPL_SV_REBAJA_OPERATIVA_20261010 — Evidencia (operación y blindaje «Rebaja de etiquetas»)

**Fecha:** 2026-10-10 · **Entorno:** `madenat_test` / contenedor `odoo18_app` (PostgreSQL `odoo18_db`).
**Naturaleza:** expediente de **evidencia** (no doctrinal). La doctrina vive en
`custom_addons/madenat_lumber_docs/CANON/` (`19 §19.16`, `02 §17.16.14`, `03 §18`, `05`, `INDICE`).

## Objetivo
Mejorar de inicio a fin la operación existente **«Rebaja de etiquetas»** reutilizando el mecanismo I2
(único menú, modelo, asistente, apply/reverse). **No** se crea menú, wizard, documento, ledger ni
motor de saldos nuevos; sin recargar la ingesta; **Bloque D cuantitativo fuera de alcance**.

## Baseline
- Rama `feat/guia-correccion-documental-preservada-20261002`; HEAD **`b1d2d19`**.
- Cambios locales ajenos preservados (prior 18.0.1.10.0 + otros frentes). `code/git_status_pre.txt` /
  `code/git_status_after.txt`. **Sin** reset/clean/staging, **sin** commit/push.
- Versión inicial: `madenat_lumber_logistics` **18.0.1.10.0** → final **18.0.1.11.0**.

## Cambios (diff: `code/diff_sv_rebaja_operativa.diff`)
- **Bloque B — elegibilidad:** campo `guia_processing_id` del asistente con
  `domain=_i2_return_guide_domain()` (`service_return_confirmation='yes'` **y** `state!='cancelled'`);
  `_i2_guia_es_elegible`, `_i2_check_guia_is_eligible_return`; rechazo de selección forzada en
  `_onchange_guia_processing_id` y **antes** de `_i2_get_or_create` (sin documento parcial);
  `default_get` no preselecciona guía no elegible. Se conserva el control Sí en apply y la regla
  `pending` sin Sí.
- **Bloques A/C — listado/búsqueda:** columnas separadas (N° Guía, Proveedor, Fecha opcional,
  Producto, Procesador, magnitudes); agregados `sv_assignment_*` **`store=True`** (filtrables);
  filtros Con/Sin saldo, Con/Sin rebajas, Exceso; búsqueda Etiqueta SV / Guía·Proveedor / Producto;
  columnas opcionales de retorno en el listado de guías (`view_madenat_guia_processing_sv_return_list`)
  y filtros de retorno (`..._search`).
- **Bloque D — cantidades:** `_i2_lot_reserved_m3`, `_i2_lot_applied_m3`, `_i2_lot_available_for_m3`
  (excluyente del documento en curso); campos del asistente Nominal lote / Rebajado aplicado /
  Reservado / Disponible documental; `etiqueta_retorno` y `etiqueta_disponible_m3` en el reparto.
- **Bloque E/F — resumen y mensajes:** `previous_applied_total_m3`, `available_total_m3`; mensaje
  «Actualiza el saldo documental SV. No mueve stock ni modifica el ledger SV»; ayuda de no-guías y de
  no-etiquetas.
- **Bloque G — blindaje/concurrencia:** `_i2_lock_resources` (advisory locks de **etiqueta (ns 3)** y
  **SV (ns 2)** en orden global), adquiridos **antes** de revalidar techos; `_i2_lock_sv_lots` delega.
- **Pruebas:** `tests/test_sv_rebaja_operativa.py` (RET/UX/VOL/SEC/REV/PHY/CON) + registro en
  `tests/__init__.py`.

## Fórmulas documentales (verificadas en VOL-01/VOL-02/VOL-06)
- **Nominal** = `_i2_lot_nominal_m3` = `volume_purchase_m3` (o `volumen_m3`).
- **Rebajado/aplicado** = Σ `nominal_volume_m3` de líneas en `applied`.
- **Reservado** = Σ `nominal_volume_m3` de líneas en `draft`/`pending`.
- **Disponible documental** = nominal − Σ activos (`draft`/`pending`/`applied`) **excluyendo el
  documento en curso**. Techo duro etiqueta-side = Σ activos ≤ nominal.
- N:M: `nominal_total_m3` = Σ líneas; `imputed_total_m3` = Σ repartos (sin duplicar).

## Actualización en desarrollo
```
docker exec odoo18_app bash -lc "odoo --database=madenat_test --update=madenat_lumber_logistics \
  --stop-after-init --no-http --log-level=info"
```
- **Exit code 0** (`logs_op_update_final.log`), `Modules loaded`, sin errores de parseo/registro.
  Sin `-u all`. Sin despliegue remoto. Versión aplicada **18.0.1.11.0**.
- Menús sin cambios (545 «Rebaja de etiquetas» activo; 542 retirado) — `menu_metadata_after.txt`.

## Pruebas
- **Dirigidas** `--test-tags /madenat_lumber_logistics:TestSvRebajaOperativa`:
  **`0 failed, 0 error(s) of 20 tests`** (`logs_op_final_directed.log`; corrida previa en
  `logs_op_tests2.log`).
- **Regresión de módulo** `--test-tags /madenat_lumber_logistics`:
  **`4 failed, 0 error(s) of 318 tests`** (`logs_op_final_regression.log`). Las **4 fallas** son **las
  mismas** preexistentes (`test_processor_locations.test_09`, `test_processor_shipment_ad89.test_t1/t5/t6`)
  ⇒ **0 fallas nuevas, 0 errores**. Ningún test ajeno modificado. Datos 100 % transaccionales
  (`TransactionCase`, rollback) ⇒ **sin registros residuales** de prueba.

## Respaldos / recuperación
- `code/modules_pre.tar.gz` — `madenat_lumber_logistics` + `madenat_lumber_docs` pre-etapa.
- `db/madenat_test_pre.dump` — `pg_dump -Fc`. `db/filestore_pre.tar.gz` — filestore `madenat_test`.
- **Recuperación:** código → extraer `modules_pre.tar.gz`; esquema → `-u madenat_lumber_logistics`;
  base → restaurar `db/madenat_test_pre.dump`; filestore → extraer `db/filestore_pre.tar.gz`.

## Límites y pendientes mínimos
1. **V3 *pixel*** — navegador real no disponible; verificación por XML/ORM/SQL + pruebas. Guion:
   `docs/GUION_MANUAL_NAVEGADOR.md`. **No** se declara renderizado aprobado por `get_views`.
2. **Bloque D cuantitativo** — fuera de alcance (`19` §19.12).
3. Búsqueda por proveedor del listado SV: `filter_domain` combinado «Guía / Proveedor» (la ruta
   punteada `volume_source_guia_id.partner_id` no es válida como campo de búsqueda en Odoo 18).
4. Concurrencia: la protección por advisory lock (etiqueta + SV) está probada con una **sesión** que
   retiene el lock (CON-01); **no** se ejecutó un *race* real de dos procesos simultáneos.

## Propuesta de commit (NO ejecutado)
`feat(logistics): mejora y blinda la operación «Rebaja de etiquetas» (CANON/19 §19.16)` — módulo
`madenat_lumber_logistics` 18.0.1.11.0 + `tests/test_sv_rebaja_operativa.py` + docs CANON/02/03/05/19/INDICE.
**Mantener** los demás cambios locales ajenos fuera de este commit.
