# Aplicación en `madenat_test` (2026-10-07) — registro

**Autorizada por el usuario** (entorno local, `madenat_test`, respaldo previo, ventana
controlada, `-u madenat_lumber_core`, reinicio de `odoo18_app`). **Sin producción. Sin commit/push.**

## 1. Verificación de inventario (gate previo)

- `diff -rq` árbol activo vs artefacto probado: **exactamente 8 archivos** (6 modificados + 2 nuevos).
  `reception_parser.py` **SÍ está incluido** (la mención de «cinco archivos» era el cierre
  *incremental*; el **consolidado** abarca las tres entregas).
- Parche consolidado `patch/consolidado/00_ALL.diff` (1138 líneas) → aplicado sobre **copia** del
  árbol activo → los 8 archivos quedaron **byte-idénticos** al artefacto probado (`RESULT=1`).
- Suite sobre la copia reconstruida (base `dupval4_verify_20261007`): **`0 failed, 0 error(s) of 48 tests`**.

## 2. Respaldo verificado (antes de escribir)

`backups/DUPFIX_20261007_173118/`:

| Artefacto | Tamaño | Integridad |
|---|---|---|
| `code_custom_addons.tar.gz` (código, incl. cambios locales) | 26 207 781 B | `gzip -t` OK |
| `madenat_test.dump` (pg_dump -Fc) | 11 353 311 B | magic `PGDMP` OK |
| `filestore_madenat_test.tar.gz` (filestore) | 21 226 392 B | `gzip -t` OK; 724 entradas |
| `apply_update.log` (log de la actualización) | — | — |

## 3. Archivos aplicados (antes → después)

| Archivo (`madenat_lumber_core/…`) | Antes (sha256) | Después (sha256) |
|---|---|---|
| `models/reception_parser.py` | `eaccfd9d…` | `816081f1d083f78ee7d93b83468895aa203c6731fba84500a5e6814fb8af549b` |
| `models/madenat_guia_processing.py` | `5d690492…` | `98a4caeaf5638b5be27f6e76c00a5078c2a2e92135fd03506e07666ec05b2075` |
| `models/mixin_lumber_ingest.py` | `70511480…` | `40fbc5dfee1140a8f2ebf2c12f68d49f7cee4e08ffd30d9e478c042a2c762215` |
| `models/reception_workflow.py` | `231f9dc6…` | `3df39636518b68a536526886cfd84995bec413a1cc707dfcf67297a245e3f017` |
| `tests/__init__.py` | `db05f45e…` | `955daddf85ad90073b132fa22c15820c9314d89468a9b6543c1999f9ebb161d2` |
| `tests/test_duplicate_validation.py` | `50385938…` | `5ac4e7cadbe08ac48dfb337831df622c1c01de2e0964486663ee5ba7df6a3704` |
| `tests/test_guide_duplicate_ingest.py` | (no existía) | `744155637a571ac6fdd9dd6310a7659efb3abf28c221165f40d49d3785514b62` |
| `tests/test_guide_duplicate_warnings.py` | (no existía) | `29182e521e870afbff8af4f6d7bfa8d00d06f5200026d057e85734889373ea99` |

Los 8 «después» coinciden con el artefacto probado (`APPLIED_MATCHES_TESTED=1`).

## 4. Actualización y servicios

- **Ventana controlada:** `odoo18_app` detenido → parche aplicado → `-u madenat_lumber_core`
  (one-shot `--no-http --max-cron-threads=0 --workers=0 --stop-after-init`) sobre `madenat_test`
  → `odoo18_app` reiniciado.
- **Resultado `-u`:** `madenat_lumber_core` = `installed`, `write_date` 2026-10-07 20:34:57;
  dependientes (`madenat_lumber_intake`, `..._logistics`, `..._costing`, `..._toll_processing`)
  `installed`; log **sin** líneas `ERROR`/`CRITICAL` ni traceback real.
- **Servicio:** `odoo18_app` **Up**; `GET /web/login` → **HTTP 200**.
- **Logs post-reinicio:** 0 líneas de nivel `ERROR`/`CRITICAL`.

## 5. Comprobaciones NO destructivas sobre `madenat_test`

- **Carga:** registry carga; app operativa.
- **Métodos (vía `odoo shell`, solo lectura, `env.cr.rollback()`):**
  `_check_guide_duplicate(guide_no, partner_id=None, exclude_id=None, exclude_model='lumber.reception', cross_model=False, raise_on_match=True)`;
  `_warn_guide_homonym` en **guía y recepción**; `_check_guide_identity_duplicate(_on_create)`
  en guía; `_check_duplicate_and_warn` en el workflow; `message_post` en ambos modelos.
- **`CANON`, ACL, `security/*.csv`, XML: NO tocados** (el parche sólo modifica `models/` y `tests/`).
- **Datos históricos:** `madenat_guia_processing` sigue con **11** filas (no se crearon guías).
- **Git:** `HEAD` `e302c488…` sin cambios; entradas pasaron de **47 → 54** (5 `M` nuevos + 2 `??`);
  **sin commit/push**.

## 6. Límites explícitos

- Se acredita **cabecera y staging**; **NO** lotes/movimientos ni protección **concurrente**.
- La **visualización del aviso en navegador** queda como **comprobación manual pendiente**
  (probado a nivel servidor/chatter).
