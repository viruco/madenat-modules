# INC-002 — Error por db_host incorrecto

**Fecha detectado:** 2026-05-07
**Módulo afectado:** Infraestructura
**Severidad:** Alto
**Estado:** Resuelto

## Síntoma

```
could not translate host name "madenat_test" to address: Name or service not known
```

## Causa raíz

El parámetro `--db_host` usaba el nombre de la base de datos (`madenat_test`) en lugar del nombre del container PostgreSQL (`odoo18_db`).

## Solución aplicada

```bash
# INCORRECTO
python odoo-bin -u madenat_lumber_core --db_host=madenat_test

# CORRECTO
python odoo-bin -u madenat_lumber_core --db_host=odoo18_db
```

## Prevención

Regla permanente: `--db_host` SIEMPRE es `odoo18_db`. Ver [[entorno_wsl2_docker]].

## Relacionado

- [[entorno_wsl2_docker]]
- [[comandos_odoo_dev]]
- [[DEC-004_postgresql_docker]]
