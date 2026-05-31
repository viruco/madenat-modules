# INC-004 — Columna inexistente por falta de actualización

**Fecha detectado:** 2026-05-07
**Módulo afectado:** madenat_lumber_core
**Severidad:** Alto
**Estado:** Resuelto

## Síntoma

```
ProgrammingError: column madenat_recepcion.madenat_nuevo_campo does not exist
```

## Causa raíz

Se agregó un campo nuevo al modelo Python pero no se ejecutó `-u` del módulo. El ORM cargó el modelo en memoria pero la tabla de PostgreSQL no tenía la columna nueva.

## Solución aplicada

```bash
python odoo-bin -u madenat_lumber_core \
  -d MADENAT_DEV \
  --db_host=odoo18_db \
  --db_port=5432 \
  --db_user=odoo \
  --db_password=odoo \
  --stop-after-init
```

## Prevención

Cualquier cambio en modelos Python requiere `-u` obligatorio. Ver [[despliegue_modulo]].

## Relacionado

- [[despliegue_modulo]]
- [[comandos_odoo_dev]]
