# Backup y Restauración — Procedimiento

**Módulo:** Infraestructura
**Categoría:** Operación
**Estado:** Borrador
**Última actualización:** 2026-05-30

---

## Propósito

Documentar el procedimiento completo de backup y restauración de la base de datos y filestore de MADENAT, con comandos verificados del entorno real.

---

## Estrategia de backup

Tres niveles de respaldo, cada uno con propósito diferente:

| Nivel | Tipo | Qué respalda | Para qué |
|---|---|---|---|
| 1 | `pg_dump` (lógico) | Estructura + datos de `madenat_test` | Restauración granular, más frecuente |
| 2 | Volumen Docker (`odoo-db-data`) | Snapshot binario completo de PostgreSQL | Recuperación total del estado del disco |
| 3 | Filestore Odoo (`odoo-web-data`) | Archivos adjuntos (`ir.attachment`) | Imágenes, PDFs, binarios que no están en tablas |

---

## Backup manual (pg_dump)

### Formato comprimido (recomendado)

```bash
mkdir -p ~/backups

docker exec odoo18_db pg_dump -U odoo -F c madenat_test \
  > ~/backups/madenat_test_$(date +%Y%m%d_%H%M).dump
```

### Formato SQL plano

```bash
docker exec odoo18_db pg_dump -U odoo madenat_test \
  > ~/backups/madenat_test_$(date +%Y%m%d_%H%M).sql
```

### Solo estructura (sin datos)

```bash
docker exec odoo18_db pg_dump -U odoo --schema-only madenat_test \
  > ~/backups/schema_$(date +%Y%m%d).sql
```

### Verificar integridad del backup

```bash
# Verificar tamaño del archivo (no debe ser 0)
ls -lh ~/backups/madenat_test_*.dump

# Listar contenido del dump comprimido
pg_restore -l ~/backups/madenat_test_*.dump | head -20
```

---

## Restauración desde `.dump` (formato comprimido)

```bash
# Restaurar sobre la BD existente (sobrescribe datos)
docker exec -i odoo18_db pg_restore -U odoo -d madenat_test \
  --clean --no-owner < ~/backups/madenat_test_20260530_1200.dump
```

> `--clean` elimina tablas existentes antes de restaurar. `--no-owner` evita errores de permisos.

---

## Restauración desde `.sql` (formato plano)

```bash
cat ~/backups/madenat_test_20260530_1200.sql | \
  docker exec -i odoo18_db psql -U odoo -d madenat_test
```

---

## Recrear base de datos desde cero

```bash
# 1. Detener Odoo para evitar escrituras durante la restauración
docker stop odoo18_app

# 2. Eliminar la BD existente
docker exec odoo18_db dropdb -U odoo madenat_test

# 3. Crear BD nueva
docker exec odoo18_db createdb -U odoo madenat_test

# 4. Restaurar desde backup
cat ~/backups/madenat_test_20260530_1200.sql | \
  docker exec -i odoo18_db psql -U odoo -d madenat_test

# 5. Reiniciar Odoo
docker start odoo18_app

# 6. Verificar logs
docker logs -f odoo18_app
```

---

## Backup del filestore (adjuntos)

Los archivos adjuntos de Odoo (imágenes, PDFs, binarios) se almacenan en el filesystem, **no** en la base de datos:

```bash
# Copiar filestore del container al host
docker cp odoo18_app:/var/lib/odoo/filestore \
  ~/backups/filestore_$(date +%Y%m%d)
```

### Restaurar filestore

```bash
# Detener Odoo
docker stop odoo18_app

# Eliminar filestore actual
docker exec odoo18_app rm -rf /var/lib/odoo/filestore

# Copiar filestore de vuelta
docker cp ~/backups/filestore_20260530 \
  odoo18_app:/var/lib/odoo/filestore

# Reiniciar Odoo
docker start odoo18_app
```

---

## Backup del volumen Docker (snapshot completo)

> ⚠️ **El volumen `odoo-db-data` no se puede copiar con el container corriendo.**

```bash
# Detener PostgreSQL
docker stop odoo18_db

# Crear backup del volumen
docker run --rm \
  -v odoo-db-data:/source:ro \
  -v ~/backups:/backup \
  alpine tar czf /backup/odoo-db-data_$(date +%Y%m%d).tar.gz -C /source .

# Reiniciar PostgreSQL
docker start odoo18_db
```

### Restaurar volumen Docker

```bash
docker stop odoo18_db

docker run --rm \
  -v odoo-db-data:/target \
  -v ~/backups:/backup \
  alpine tar xzf /backup/odoo-db-data_20260530.tar.gz -C /target

docker start odoo18_db
```

---

## Frecuencia recomendada

| Escenario | Frecuencia | Tipo | Retención |
|---|---|---|---|
| Antes de cada sesión de desarrollo | Cada vez | `pg_dump` comprimido | Últimas 5 sesiones |
| Semanal | Domingo 02:00 | `pg_dump` + filestore | 4 semanas |
| Antes de `-u` (upgrade) | Manual obligatorio | `pg_dump` + filestore | Hasta validación |
| Antes de migración | Manual obligatorio | Dump + filestore + volumen | Permanente |

### Automatización simple (crontab)

```bash
# Backup diario a las 02:00
0 2 * * * docker exec odoo18_db pg_dump -U odoo -F c madenat_test > /home/viruco/backups/madenat_test_$(date +\%Y\%m\%d).dump
```

---

## Advertencias

- `--clean` en `pg_restore` **elimina tablas** antes de restaurar. Siempre verificar el backup antes de ejecutar.
- El volumen `odoo-db-data` **no se puede copiar con el container corriendo** — debe detenerse primero.
- Siempre detener Odoo antes de restaurar: `docker stop odoo18_app` — evita escrituras concurrentes.
- Un backup de base de datos **no incluye el filestore** — deben respaldarse por separado.
- Si se restaura un backup en una BD con schema diferente, ejecutar `-u all` para actualizar módulos.
- El archivo `.sql` plano puede ser muy grande (varios GB) — preferir formato comprimido (`.dump`) para backups regulares.
- La BD real es `madenat_test` — no confundir con `odoo` (que es la BD por defecto del container PostgreSQL).

---

## Relacionado

- [[comandos_postgresql]]
- [[comandos_docker]]
- [[entorno_wsl2_docker]]
- [[variables_entorno]]
- [[despliegue_modulo]]
- [[INC-004_column_inexistente]]
