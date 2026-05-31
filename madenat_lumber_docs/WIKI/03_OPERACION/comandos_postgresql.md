# Comandos PostgreSQL — MADENAT

**Módulo:** Infraestructura
**Categoría:** Operación
**Estado:** Borrador
**Última actualización:** 2026-05-30

---

## Propósito

Centralizar los comandos de PostgreSQL para acceso, diagnóstico y mantenimiento de la base de datos MADENAT dentro del entorno Docker.

---

## Acceso a PostgreSQL

### Desde el host (vía docker exec)

```bash
# Entrar al container y conectar a la BD por defecto
docker exec -it odoo18_db psql -U odoo -d odoo

# Conectar a la BD de test de Odoo
docker exec -it odoo18_db psql -U odoo -d madenat_test

# Conectar directamente sin shell interactivo
docker exec -it odoo18_db psql -U odoo -d madenat_test -c "SELECT version();"
```

### Desde dentro del container

```bash
# Entrar al container
docker exec -it odoo18_db bash

# Conectar a psql
psql -U odoo -d madenat_test
```

---

## Queries de diagnóstico frecuentes

### Recepciones por estado

```sql
SELECT state, count(*) as total
FROM lumber_reception
GROUP BY state
ORDER BY total DESC;
```

### Lotes por recepción

```sql
SELECT r.name as recepcion, count(l.id) as lotes, r.state
FROM lumber_reception r
LEFT JOIN stock_lot l ON l.lumber_reception_id = r.id
GROUP BY r.name, r.state
ORDER BY lotes DESC;
```

### Embarques activos con contenedores

```sql
SELECT s.name, count(c.id) as contenedores, s.state
FROM lumber_export_shipment s
LEFT JOIN lumber_container c ON c.shipment_id = s.id
WHERE s.state NOT IN ('delivered', 'cancelled')
GROUP BY s.name, s.state
ORDER BY contenedores DESC;
```

### Lotes asignados a contenedores

```sql
SELECT c.name as contenedor, c.state, count(sl.lot_id) as lotes
FROM lumber_container c
LEFT JOIN lumber_shipment_line sl ON sl.container_id = c.id
GROUP BY c.name, c.state
ORDER BY lotes DESC;
```

### Contar registros por modelo MADENAT

```sql
SELECT 'lumber_reception' as modelo, count(*) FROM lumber_reception
UNION ALL
SELECT 'lumber_reception_line', count(*) FROM lumber_reception_line
UNION ALL
SELECT 'stock_lot', count(*) FROM stock_lot WHERE lumber_reception_id IS NOT NULL
UNION ALL
SELECT 'lumber_export_shipment', count(*) FROM lumber_export_shipment
UNION ALL
SELECT 'lumber_container', count(*) FROM lumber_container
UNION ALL
SELECT 'lumber_shipment_line', count(*) FROM lumber_shipment_line
UNION ALL
SELECT 'madenat_subproducto', count(*) FROM madenat_subproducto
UNION ALL
SELECT 'madenat_guia_processing', count(*) FROM madenat_guia_processing
UNION ALL
SELECT 'madenat_guia_processing_line', count(*) FROM madenat_guia_processing_line;
```

### Últimas entradas de auditoría

```sql
SELECT a.id, a.reception_id, r.name as recepcion,
       a.action_type, a.message, a.create_date
FROM madenat_audit_log a
LEFT JOIN lumber_reception r ON r.id = a.reception_id
ORDER BY a.create_date DESC
LIMIT 20;
```

### Recepciones con omisiones

```sql
SELECT r.name, r.state, r.omitted_count, r.reception_date
FROM lumber_reception r
WHERE r.omitted_count > 0
ORDER BY r.omitted_count DESC;
```

---

## Mantenimiento

### Ver tamaño de tablas del módulo

```sql
SELECT
    relname AS tabla,
    pg_size_pretty(pg_total_relation_size(relid)) AS tamano_total,
    pg_size_pretty(pg_relation_size(relid)) AS tamano_datos,
    n_live_tup AS filas_vivas
FROM pg_stat_user_tables
WHERE relname LIKE 'lumber_%'
   OR relname LIKE 'madenat_%'
ORDER BY pg_total_relation_size(relid) DESC;
```

### Ver índices de tablas MADENAT

```sql
SELECT
    t.relname AS tabla,
    i.relname AS indice,
    ix.indisunique AS es_unico,
    pg_size_pretty(pg_relation_size(i.oid)) AS tamano
FROM pg_index ix
JOIN pg_class t ON t.oid = ix.indrelid
JOIN pg_class i ON i.oid = ix.indexrelid
WHERE t.relname LIKE 'lumber_%'
   OR t.relname LIKE 'madenat_%'
ORDER BY pg_relation_size(i.oid) DESC;
```

### VACUUM / ANALYZE

```sql
-- Actualizar estadísticas del planner (rápido, seguro en producción)
ANALYZE VERBOSE;

-- Limpiar tuplas muertas de tablas específicas
VACUUM VERBOSE lumber_reception;
VACUUM VERBOSE lumber_reception_line;
VACUUM VERBOSE stock_lot;
VACUUM VERBOSE lumber_export_shipment;
VACUUM VERBOSE lumber_container;

-- VACUUM FULL (reconstruye tablas — bloquea escritura, usar con precaución)
-- VACUUM FULL lumber_reception;
```

---

## Backup manual desde container

### Backup completo (SQL plano)

```bash
docker exec odoo18_db pg_dump -U odoo madenat_test > backup_$(date +%Y%m%d_%H%M).sql
```

### Backup comprimido (formato custom)

```bash
docker exec odoo18_db pg_dump -U odoo -Fc madenat_test > backup_$(date +%Y%m%d_%H%M).dump
```

### Backup solo estructura (sin datos)

```bash
docker exec odoo18_db pg_dump -U odoo --schema-only madenat_test > schema_$(date +%Y%m%d).sql
```

### Backup de una sola tabla

```bash
docker exec odoo18_db pg_dump -U odoo -t lumber_reception madenat_test > backup_recepcion_$(date +%Y%m%d).sql
```

---

## Restauración

### Desde archivo SQL plano

```bash
# Opción 1: Restaurar sobre la BD existente (sobrescribe datos)
docker exec -i odoo18_db psql -U odoo -d madenat_test < backup_20260530_1200.sql

# Opción 2: Recrear la BD desde cero
docker exec -it odoo18_db dropdb -U odoo madenat_test
docker exec -it odoo18_db createdb -U odoo madenat_test
docker exec -i odoo18_db psql -U odoo -d madenat_test < backup_20260530_1200.sql
```

### Desde formato comprimido (.dump)

```bash
docker exec -i odoo18_db pg_restore -U odoo -d madenat_test --clean --if-exists backup_20260530_1200.dump
```

> **Advertencia:** `pg_restore --clean` elimina objetos existentes antes de restaurar. Solo usar en desarrollo o con backup previo.

### Después de restaurar

```bash
# Reiniciar Odoo para que reconozca los cambios
docker restart odoo18_app

# Ver logs para confirmar que carga sin errores
docker logs -f odoo18_app
```

---

## Conexión desde psql externo

El puerto 5432 de PostgreSQL **no está expuesto al host** — solo es accesible desde dentro del container o desde otros containers en la red `internal_backend`.

```bash
# ✅ Correcto: vía docker exec
docker exec -it odoo18_db psql -U odoo -d madenat_test

# ❌ No funciona: puerto no expuesto al host
psql -h localhost -p 5432 -U odoo -d madenat_test

# ✅ Alternativa: conectar desde el container de Odoo
docker exec -it odoo18_app bash
# Dentro del container:
psql -h db -U odoo -d madenat_test
```

---

## Restricciones conocidas

- NUNCA ejecutar `DROP DATABASE` en producción; el usuario `odoo` no debería tener permisos de superusuario.
- Los backups manuales no reemplazan el procedimiento automatizado. Ver [[backup_restauracion]].
- Si la base de datos está corrupta, no ejecutar `REINDEX` sin backup previo.
- El `pg_restore --clean` elimina tablas existentes — siempre verificar antes de ejecutar.
- La base de datos por defecto del compose es `odoo`, pero Odoo usa `--database madenat_test` — los datos de la app están en `madenat_test`.

---

## Relacionado

- [[entorno_wsl2_docker]]
- [[comandos_docker]]
- [[comandos_odoo_dev]]
- [[backup_restauracion]]
- [[variables_entorno]]
- [[INC-002_db_host_incorrecto]]
