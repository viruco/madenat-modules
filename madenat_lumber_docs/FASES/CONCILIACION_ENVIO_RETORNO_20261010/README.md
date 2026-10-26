# CONCILIACION_ENVIO_RETORNO_20261010 — Evidencia (Bloque A/B/C)

**Fecha:** 2026-10-10 · **Entorno:** `madenat_test` / contenedor `odoo18_app` (PostgreSQL `odoo18_db`).

**Naturaleza:** expediente de **evidencia** (no doctrinal). La doctrina vive en
`custom_addons/madenat_lumber_docs/CANON/` (`19 §19.11`, `02 §17.16.10`, `03 §15`, `05`, `INDICE`).

## Baseline
- Rama `feat/guia-correccion-documental-preservada-20261002`; HEAD **previo** a esta etapa:
  `573a164b6ddba01af751c6d9bd618e29e6b0d7cf`.
- **Commit local creado en esta etapa:** `d2a0d2f239139ce8d8ea20488ed377790ca9e39b`
  — `feat(logistics): vincular envíos a procesador con retornos e imputaciones SV` (20 archivos).
  **Sin push ni despliegue remoto.**
- Cambios locales **ajenos a esta etapa preservados** (el commit no los incluye; siguen sin staged).
- Estado previo: `code/HEAD_pre.txt`, `code/git_status_pre.txt`, `code/wip_uncommitted_pre.diff`.

## Respaldo / recuperación
- `code/modules_pre.tar.gz` — módulos `madenat_lumber_logistics` + `madenat_lumber_core` **antes** de esta etapa.
- `db/madenat_test_pre_20261010.dump` — `pg_dump -Fc` (~11,3 MB).
- `filestore_pre.tar.gz` — volumen `odoo-18-ce_odoo-web-data` (~110 MB).
- `code/changes_20261010.diff` — cambio de código de esta etapa; `docs/canon_changes_20261010.diff` — documentación.
- **Recuperación:** (1) código → extraer `modules_pre.tar.gz` sobre `custom_addons`
  (o `patch -R` de `changes_20261010.diff`); (2) esquema → `odoo -u madenat_lumber_core,madenat_lumber_logistics`;
  (3) base → restaurar `db/madenat_test_pre_20261010.dump`; (4) filestore → restaurar `filestore_pre.tar.gz`.
  **No** restaurar el dump sobre trabajo posterior sin advertir el impacto.

## Cambios
- **Nuevos:** `models/madenat_processor_return_link.py`,
  `views/madenat_processor_return_link_views.xml`, `tests/test_processor_return_link.py`.
- **Modificados (logistics):** `models/__init__.py`, `wizards/madenat_sv_imputation_wizard.py`,
  `wizards/madenat_sv_imputation_wizard_views.xml`, `views/madenat_sv_imputation_views.xml`,
  `security/ir.model.access.csv`, `data/sequences.xml`, `__manifest__.py`, `tests/__init__.py`.
- **Modificado (core):** `models/madenat_audit_log.py` (2 valores **aditivos** del `Selection`).
- **Documentación:** `CANON/19` (§19.11 y §19.12, v1.9.0), `CANON/02` (§17.16.10, v12.18.0),
  `CANON/03` (§15 y §15.4, v6.18.0), `CANON/05` (v8.17.0), `CANON/INDICE` (v12.12.0).
- **Cierre versionado:** `madenat_lumber_logistics` **18.0.1.6.0 → 18.0.1.7.0**;
  `madenat_lumber_core` **18.0.6.5.0 → 18.0.6.6.0** (CHANGELOG de ambos actualizado).

## Evidencia web — clasificada en tres niveles
- **(a) Integración web/RPC con sesión autenticada — EJECUTADA.** Mismos endpoints del cliente web
  (`/web/session/authenticate`, `/web/webclient/load_menus`, `/web/dataset/call_kw`), sesión real de
  Operaciones: menú visible; acceso a datos; **registrar OK**; **reversa por Operaciones DENEGADA**;
  **reversa por Jefatura OK**; auditoría. Artefactos en `v3/`.
- **(b) Lectura de arquitecturas de vistas y metadatos — VERIFICADA.** `get_views` (form/lista) y
  `fields_get`.
- **(c) Renderizado e interacción en navegador real — PENDIENTE.** No hay navegador en el entorno.
- **(a)+(b) NO sustituyen a (c); V3 no acreditada.**
- **Registros de prueba (identificados):** `V3 Planta (temp)` 14785 · guía `V3-CONCIL` 33737 ·
  picking 7973 · lote `V3-LOT` 18003 · `REL00030` (`reversed`). Usuarios 2974/2975 **desactivados**.

## Pendientes mínimos
1. **Bloque D** — conciliación cuantitativa (decisión de etapa: **opción 3**, no implementado; diseño
   requerido en `19` §19.12).
2. **Navegador real (V3 *pixel*)** — evidencia con navegador, no disponible en el entorno.
3. Regularización de **históricos** (fuera de alcance; procedimiento separado si se autoriza).

## Pruebas
- `logs/tests_processor_return_link_run2.log` — **0 failed, 0 error(s) of 12 tests** (T1–T12).
- `logs/tests_logistics_regression.log` — regresión `madenat_lumber_logistics`: **3 failed, 0 error(s) of 265**.
  Las **3 fallas son PRE-EXISTENTES**: aserciones globales
  `assertFalse(AuditLog.search([('action_type','=','deviation')]))` contra **5** eventos `deviation`
  históricos (ids 19889/19941/20342/20381/21739; fechas **2026-10-04/05/07**, anteriores a esta etapa).
  **0 fallas nuevas; 0 errores.**
- `logs/update_20261010.log` — actualización de módulos sin errores.
- **Comprobación ORM/SQL:** **0** filas `processor_return_link` / `..._reverse` persistidas por los tests
  (transactionales ⇒ rollback).
- **No ejecutado (fuera de alcance):** navegador real (*pixel*); concurrencia; base limpia; Bloque **D** (cuantitativo).

## Ajuste de integridad (2026-10-10, tanda 2) — commit base `d2a0d2f`

- **Controles implementados** (`CANON/19` **§19.13**): reversa de imputación **no** revierte la
  procedencia (vigencia `documentary_status`/`requires_reimputation` derivadas); reimputación con
  `previous_imputation_id` + rastro; **consistencia de compañía** (constraint + `ir.rule`);
  **elegibilidad dura** `state='done'`/tipo interno; **volúmenes N:M referenciales** (`aggregator=False`).
- **Módulo:** `madenat_lumber_logistics` **18.0.1.7.0 → 18.0.1.8.0** (CHANGELOG actualizado).
- **Nuevo archivo:** `security/madenat_processor_return_link_rules.xml` (regla de registro).
- **Pruebas:** `logs/tests_integridad_link_run2.log` → **22/22** (T1–T22);
  `logs/tests_integridad_regression.log` → **275 pruebas, 4 fallas, 0 errores** (3 **preexistentes** +
  **1 ambiental** por la evidencia V3 picking `7973`). **No** se declara la regresión completamente verde.
- **Verificación ORM/arch (integración, NO V3):** `v3/orm_integrity_report.txt`.
- **Guion manual de navegador (PENDIENTE):** `docs/GUION_MANUAL_NAVEGADOR.md`.
- **Trazabilidad de 2 reimputaciones sucesivas (confirmada):** `v3/reimputation_chain_report.txt`
  (A→B→C; `previous_imputation_id` = inmediatamente anterior; cadena completa en auditoría; 1 activo).
- **Alcance multi-compañía (preciso):** `link.company_id` ← `picking_id.company_id` ←
  **`picking_type_id.company_id`**; imputación con `company_id` propio/requerido; guía sin `company_id`;
  rama `company_id = False` = registros compartidos/neutros (0 pickings nulos en la base).
- **Recuperación:** código → `git` (HEAD `d2a0d2f`) o `code/integridad_changes_20261010.diff`;
  base → `db/madenat_test_post_integridad_20261010.dump` (post) o
  `db/madenat_test_pre_20261010.dump` (pre). Cambio de esquema **aditivo** (nuevos campos + regla).
- **Sin commit/push** (la propuesta de commit se entrega para autorización).

