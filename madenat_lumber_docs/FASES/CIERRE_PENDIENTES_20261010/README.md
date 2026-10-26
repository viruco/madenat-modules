# CIERRE_PENDIENTES_20261010 — Evidencia del cierre funcional (P0–P4)

**Fecha:** 2026-10-10 · **Entorno:** `madenat_test` / `http://localhost:8069`
(contenedor `odoo18_app`, PostgreSQL `odoo18_db`) · **Biblioteca de muestras:**
`muestras_documentos_ingreso`.

**Naturaleza:** expediente de **evidencia** (no es fuente doctrinal). La doctrina
vive en `custom_addons/madenat_lumber_docs/CANON/` (`02 §17.16`, `03 §14`,
`05`, `INDICE`).

## Baseline

- Rama `feat/guia-correccion-documental-preservada-20261002`;
  HEAD `e302c488321c276af7e07f1abeecc8bc261a89f4`.
- `git status`: **62 modificados + 14 sin seguimiento** (76), **0 staged**.
- **Sin** commit/push, **sin** correos, **sin** despliegue remoto.

## Respaldo / recuperación

- `db/madenat_test_pre_20261010.dump` (`pg_dump -Fc`, 11,3 MB) — estado previo a
  las escrituras de prueba.
- `code/cierre_p0_p4_changes_20261010.diff` — diff de los archivos modificados
  (código + pruebas) vs HEAD.
- `code/p1_labels_diff_20261010.diff` — diff intermedio (P1).
- Recuperación por bloque: (1) código → `patch -R` del diff; (2) actualización de
  módulos → `-u madenat_lumber_core,madenat_lumber_intake`; (3) datos de prueba →
  borrar/archivar los registros creados (reception 7950, guía 33250) o restaurar
  el dump; (4) base/filestore → restaurar el dump.
- **No** restaurar el dump sobre trabajo posterior sin advertir el impacto.

## Logs

- `logs/update_20261010.log` — actualización de módulos (P1), servicio detenido
  durante la operación; `HTTP 200` posterior.
- `logs/tests_intake_20261010.log` — regresión `madenat_lumber_intake`
  (2 failed of 380; causa UI consolidada, corregida).
- `logs/tests_p4_p1_20261010.log`, `logs/tests_p4_p1_run2_20261010.log` —
  dirigidas 34 (final **0 failed, 0 error(s)**).

## Resultado por bloque

Ver `02_CONTINUIDAD.md` §17.16 (P0 OwlError; P1 volúmenes; P3 41994/95083;
P4-JCE; P4-Arauco) y `03_TESTS.md` §14.

## Datos de prueba creados (no eliminados)

- `lumber.reception` **7950** — guía `41994` (Fátima), `verified`, 14 líneas.
- `madenat.guia.processing` **33250** — guía `95083` (Byc), `verified`, 8 líneas.
- **Alcance sin stock** (sin movimientos/pickings).
