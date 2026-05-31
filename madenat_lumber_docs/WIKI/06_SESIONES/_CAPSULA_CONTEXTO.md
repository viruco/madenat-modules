# 🪵 CÁPSULA DE CONTEXTO — MADENAT LUMBER DOCS

**Fecha de última actualización:** 2026-05-30 18:35

---

## Proyecto
- Odoo 18 CE custom — industria maderera (Chile)
- Dev en WSL2 Ubuntu + Docker
- Containers: `odoo18_app` (8069), `odoo18_db` (postgres:15, interno)
- DB real: `madenat_test` | Usuario: `odoo`

## Módulos custom (todos en `custom_addons/`)
- `madenat_lumber_core` — 21 .py, ~8000 líneas (el más crítico)
- `madenat_lumber_logistics` — 8 .py, ~3000 líneas
- `madenat_lumber_costing` — pendiente de inventario
- `madenat_lumber_shipping_core` — dependencia externa
- `madenat_lumber_reports` — pendiente de inventario

## WIKI — Estado actual (2026-05-30)
- 43 archivos .md verificados contra código real
- 0 archivos fantasma / 0 campos inventados
- Respaldo: `WIKI_BACKUP_20260530_1832`
- Ubicación: `custom_addons/madenat_lumber_docs/WIKI/`

## Archivos técnicos clave (verificados)
- `02_TECNICO/modelo_recepciones.md` — lumber.reception completo
- `02_TECNICO/modelo_despachos.md` — 8 modelos logistics verificados
- `02_TECNICO/campos_computados.md` — @api.depends reales por modelo
- `02_TECNICO/security_accesos.md` — 2 grupos custom reales
- `02_TECNICO/dependencias_modulos.md` — árbol de dependencias real

## Modelos principales verificados
- `lumber.reception`: 7 estados, 15 computed, `madenat.lumber.ingest.mixin`
- `lumber.export.shipment`: 5 estados, flujo draft→delivered
- `lumber.container`: 5 estados, status_color kanban
- `stock.lot`: extendido, `vol_shipment_m3`, `escuadria`, `generation_level`
- `madenat.subproducto`: catálogo libre (no enum)
- `madenat.guia.processing`: procesamiento de guías de despacho

## Seguridad real
- Solo 2 grupos custom: `group_madenat_admin`, `group_madenat_cost_auditor`
- Sin `ir.rule` (no existen en el código)
- Permisos base: `base.group_user` + `stock.group_stock_manager`

## Stack técnico real
- Puerto Odoo: `127.0.0.1:8069` (solo local)
- Traefik: `odoo18.localhost`, `pgadmin.localhost`
- Redes: `web_network` (external), `internal_backend` (bridge)
- Volúmenes: `odoo-web-data`, `odoo-db-data`
- Memoria: Odoo 2G, PostgreSQL 1G

## Pendientes próxima sesión
1. `git init` en `madenat_lumber_docs` (primer commit histórico)
2. Inventariar `madenat_lumber_costing`
3. Inventariar `madenat_lumber_reports`
4. Completar `herencia_odoo_modelos.md` con `madenat.lumber.ingest.mixin`

## Regla de oro del WIKI
⚠️ **NUNCA documentar sin verificar contra el código real.**
Todo campo, modelo o grupo debe leerse del `.py` antes de escribirse.
