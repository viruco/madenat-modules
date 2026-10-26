# BACKUP_APLICACION — Respaldo previo (ventana controlada)

Respaldo tomado **antes** de escribir el árbol activo y de actualizar el módulo.

## 1. Artefactos de respaldo

| Archivo | Contenido | Tamaño |
|---|---|---|
| `backup/intake_module_pre.tar.gz` | Código pre-cambio del módulo `custom_addons/madenat_lumber_intake` | ~306 KB |
| `backup/wip_uncommitted.diff` | `git diff HEAD` de los cambios locales previos (no míos) | ~245 KB |
| `backup/git_status_pre.txt` | `git status --porcelain` antes (55 entradas) | 3.1 KB |
| `backup/git_status_post.txt` | `git status --porcelain` después (58 entradas) | 3.1 KB |
| `backup/madenat_test_pre.dump` | Volcado PostgreSQL `-Fc` de `madenat_test` (TOC 13325) | ~11 MB |
| `backup/filestore_madenat_test_pre.tgz` | Filestore `/var/lib/odoo/filestore/madenat_test` | ~21 MB |

## 2. Comandos usados

```bash
# Código
tar czf backup/intake_module_pre.tar.gz -C custom_addons madenat_lumber_intake
( cd custom_addons && git diff HEAD > ../APPLY.../backup/wip_uncommitted.diff )
# Base
docker exec odoo18_db pg_dump -U odoo -Fc madenat_test > backup/madenat_test_pre.dump
docker exec -i odoo18_db pg_restore --list < backup/madenat_test_pre.dump | wc -l   # 13336
# Filestore
docker exec odoo18_app tar czf - -C /var/lib/odoo/filestore madenat_test > backup/filestore_madenat_test_pre.tgz
```

## 3. Restauración (si se requiriese revertir)

> **NO ejecutar** salvo decisión expresa. Requiere parar el servicio.

```bash
# 1) Código: reponer el módulo pre-cambio
tar xzf backup/intake_module_pre.tar.gz -C custom_addons

# 2) Base: recrear desde el volcado (¡destruye la base actual!)
docker exec -d odoo18_db psql -U odoo -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='madenat_test';"
docker exec odoo18_db dropdb -U odoo madenat_test
docker exec odoo18_db createdb -U odoo madenat_test
docker exec -i odoo18_db pg_restore -U odoo -d madenat_test --no-owner < backup/madenat_test_pre.dump

# 3) Filestore: reponer
docker exec odoo18_app sh -c 'rm -rf /var/lib/odoo/filestore/madenat_test && tar xzf - -C /var/lib/odoo/filestore'

# 4) Reiniciar servicio y actualizar el módulo (según procedimiento habitual)
docker compose restart web
```

## 4. Notas

- El volcado y el filestore son **consistentes** con el momento del respaldo.
- No se modificaron ACL, CANON, ingesta, stock, datos históricos ni otros módulos.
