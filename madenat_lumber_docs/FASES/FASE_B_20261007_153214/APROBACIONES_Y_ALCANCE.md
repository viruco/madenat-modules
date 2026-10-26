# APROBACIONES Y ALCANCE — Fase B

## Autorización vigente

"AUTORIZACIÓN CONDICIONADA — ÚNICAMENTE FASE B" (2026-10-07).

- Repositorio: `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons`
- Base: `madenat_test`
- Servicio: `odoo18_app`
- PostgreSQL: `odoo18_db`

## Incluido (ejecutado)

1. Respaldo del código (árbol de trabajo completo + historial Git).
2. Respaldo coherente de base + filestore + configuración.
3. Aplicación de los 3 diffs con `-p1`, en orden 02 → 03 → 01.
4. Actualización `-u madenat_lumber_core,madenat_lumber_intake` contra `madenat_test`.
5. Reinicio del servicio normal.
6. Validaciones de solo lectura.

## NO incluido (no ejecutado)

- Reparar `guia_processing_id` del picking 7813.
- Eliminar la guía 33152 / 15183.
- Volver a cancelar la guía.
- Modificar producción, CANON, `IMPL_SERVICE_RETURN_20261006/` ni su diff.
- `commit`/`push`, `stash`, `reset`, `checkout`, SQL `DELETE`, `sudo()` de bypass.
- Pruebas mutantes sobre `madenat_test`.

## Regla

Esta autorización NO es válida para la reparación del FK (Fase C) ni para la
eliminación (Fase E). Cada una requiere autorización expresa y separada.
