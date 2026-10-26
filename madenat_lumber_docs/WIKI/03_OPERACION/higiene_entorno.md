# Higiene del Entorno — Intervención de limpieza acotada

**Módulo:** Infraestructura / entorno de desarrollo
**Categoría:** Operación
**Estado:** Activo
**Última actualización:** 2026-10-07

> **Nota de consolidación (FASE 2, 2026-10-26).** Los punteros a expedientes de fase se reescribieron a
> `FASES/<carpeta>/…`, ubicación consolidada dentro de `madenat_lumber_docs`. El texto, las fechas, las cifras
> y las conclusiones históricas **no se alteraron**: solo cambió el puntero. Los artefactos no versionados
> (`logs/`, `db/`, dumps, código de evidencia) se citan por nombre de archivo y carpeta de origen, y su copia
> íntegra está en los `.tar.gz` de D7 (`FASES/FASE13_20261023/evidencias/SHA256_BACKUPS_CONSOLIDACION.csv`).

---

## Propósito

Registrar la limpieza **acotada** (con aprobación) de residuos de auditorías,
implementaciones y pruebas en el entorno de desarrollo, preservando
`madenat_lumber_docs` como **fuente documental única** y dejando trazabilidad de lo
eliminado, lo conservado y lo reconstruible. **No** es una limpieza general.

---

## Contexto

- **Fase 1 — inventario (solo lectura):** se inventariaron carpetas externas de
  intervención, temporales, Docker, bases de prueba, respaldos y estado del repo. El
  inventario y la propuesta se entregaron en la sesión del **2026-10-07** (no se creó
  expediente externo de cierre).
- **Fase 2 — ejecución:** solo se ejecuta una **lista concreta aprobada**.
- Criterio rector: *investigar → clasificar → comprobar dependencias → proponer mínimo →
  aprobar → limpiar → verificar*. "Antiguo"/"ocupa espacio" **no** son razones.
- El entorno **no** tenía presión de espacio (≈ 929 GB libres); el objetivo fue **orden**,
  no liberar disco.

---

## Alcance aprobado (Fase 2)

**Autorizado y ejecutado:**
1. Eliminar la copia **dry-run** `IMPL_BUSQUEDA_INTAKE_20261007/gate/`.
2. Eliminar la **base aislada** `busqintake_iso_20261007`.

**No autorizado (permanece intacto):** bloque B (bases `dupval*`, `delint_test`,
`aclf_test`, `repr_test`, `srvret_test`), workcopies `addons/`/`verify_*`/`workcopy/`
de `FIX_*`/`IMPL_*`, expedientes (`AUDIT_*/IMPL_*/UAT_*/…`), respaldos (`backups/`,
`APPLY…/backup/`), contenedores, imágenes, redes y volúmenes.

---

## Comprobaciones previas (todas superadas)

| Elemento | Comprobación | Resultado |
|---|---|---|
| `IMPL_BUSQUEDA_INTAKE_20261007/gate/` | ruta real = `…/IMPL_BUSQUEDA_INTAKE_20261007/gate` | OK |
| | ¿enlace simbólico? / enlaces internos | **NO** / **0** |
| | contenido | 72 archivos, todos bajo `madenat_lumber_intake/` |
| | ¿archivos únicos? (`diff -r` vs artefacto **y** vs código activo) | **IDÉNTICO a ambos** ⇒ sin contenido único |
| | ¿resultados conservados? | **Sí** — `FASES/APPLY_BUSQUEDA_INTAKE_20261007/docs/VERIFICACION_POST_APLICACION.md` §1 |
| `busqintake_iso_20261007` | nombre exacto / `datallowconn` | OK / `t` |
| | conexiones activas | **0** |
| | ¿en `docker-compose.yml` / contenedores? | **No** / **ninguno** |
| | scripts y logs de prueba | **conservados** (`IMPL_BUSQUEDA_INTAKE_20261007/run_iso.sh`, `logs/`) |

---

## Acciones realizadas

1. `rm -r /home/viruco/dev-stack/odoo/odoo-18-ce/IMPL_BUSQUEDA_INTAKE_20261007/gate`
   → verificado ausente. `IMPL_BUSQUEDA_INTAKE_20261007/` conserva
   `README.md`, `addons/`, `docs/`, `logs/`, `patch/`, `run_iso.sh`.
2. `DROP DATABASE "busqintake_iso_20261007"` (sin `FORCE`, sin terminar conexiones)
   → verificado: 0 bases con ese nombre.

No se usaron `git clean/reset/stash`, `docker … prune`, `DROP DATABASE` por patrón,
`rm -rf` con comodines, GC de filestore, ni borrado masivo de logs/adjuntos.

---

## Espacio recuperado

| Elemento | Espacio | Medición |
|---|---|---|
| `gate/` | ≈ **1.2 MB** | `du -sh` |
| `busqintake_iso_20261007` | ≈ **77 MB** | `pg_database_size` |
| **Total** | ≈ **78 MB** | lógico (el disco ya tenía holgura) |

---

## Límites de reconstrucción

- **`gate/`:** reconstruible re-aplicando `patch/01..03` sobre una copia del módulo (o
  copiando el artefacto); el resultado (`gate == artifact`) ya está documentado. **No**
  contenía datos ni evidencia única.
- **`busqintake_iso_20261007`:** recreable clonando una plantilla test *idle* y
  `-u madenat_lumber_intake`; procedimiento en `APPLY_BUSQUEDA_INTAKE_20261007/run_iso.sh`.
  **Scripts y logs conservados.** No contenía datos operativos ni evidencia única.
- **Respaldos sensibles:** permanecen **fuera** de `madenat_lumber_docs`, en ubicación
  protegida (`APPLY_BUSQUEDA_INTAKE_20261007/backup/`, `backups/`). No se copiaron aquí.

---

## Conservado (no tocado)

`madenat_test` y datos operativos, código activo y cambios locales, ACL, filestore,
contenedores/servicios, respaldos, evidencia de incidentes/eliminación y **todas** las
workcopies y expedientes no aprobados.

---

## Pendientes (no ejecutados)

- **Bloque B:** bases de prueba recreables (`dupval*`, `delint_test`, `aclf_test`,
  `repr_test`, `srvret_test`) y workcopies de `FIX_*`/`IMPL_*`.
- **Archivado (C):** expedientes históricos (`AUDIT_*/IMPL_*/UAT_*/pre02_*/oracle_*/…`).
- **Retención (D):** `backups/`, `backups_20260821_*`, `madenat_test_antes_limpieza.sql`,
  tarballs raíz, `madenat_lumber_docs/backups/`.
- **Decisión:** volúmenes anónimos (~882 MB "reclaimable"), contenedores Exited
  (`odoo18_ui_work`, `odoo18_level1_val`, `odoo18_pgadmin`), binds `/tmp/madenat_*`,
  DBs `repro_inc_15183`/`madenat_sv_baseline`/`madenat_l0a_validation`/`madenat_ops_level1_validation`.

---

## Evidencia

- Comandos y resultados de esta intervención: sesión **2026-10-07**.
- Contexto de la intervención de Intake: `CANON/04_DECISION_LOG.md` **AD-101**;
  respaldos en `APPLY_BUSQUEDA_INTAKE_20261007/`.

---

## Relacionado

- [[comandos_docker]]
- [[backup_restauracion]]
- [[despliegue_modulo]]
- [[00_INDICE]]

---

## Historial de cambios

| Fecha | Cambio | Responsable |
|---|---|---|
| 2026-10-07 | Creación — limpieza acotada aprobada (`gate/` + base aislada `busqintake_iso_20261007`); inventario fase 1 y pendientes registrados | Intervención IA (aprobada por usuario) |
