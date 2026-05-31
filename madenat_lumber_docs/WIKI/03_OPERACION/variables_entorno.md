# Variables de Entorno — Stack MADENAT

**Módulo:** Infraestructura
**Categoría:** Operación
**Estado:** Borrador
**Última actualización:** 2026-05-30

---

## Propósito

Documentar la configuración real del stack de desarrollo MADENAT según el `docker-compose.yml`, incluyendo servicios, puertos, credenciales, redes y volúmenes.

---

## Servicios del stack

| Servicio | Container | Imagen | Puerto Host | URL Local |
|---|---|---|---|---|
| Odoo (web) | `odoo18_app` | Build local (`../custom_addons/Dockerfile`) | `127.0.0.1:8069:8069` | `http://127.0.0.1:8069` o `http://odoo18.localhost` |
| PostgreSQL (db) | `odoo18_db` | `postgres:15` | No expuesto (solo red interna) | — |
| pgAdmin | `odoo18_pgadmin` | `dpage/pgadmin4` | No expuesto (vía Traefik) | `http://pgadmin.localhost` |

---

## Variables de entorno

### Servicio web (Odoo)

| Variable | Valor | Descripción |
|---|---|---|
| `HOST` | `db` | Host de PostgreSQL dentro de la red Docker |
| `USER` | `odoo` | Usuario de conexión a PostgreSQL |
| `PASSWORD` | `odoo` | Contraseña de conexión a PostgreSQL |

### Servicio db (PostgreSQL)

| Variable | Valor | Descripción |
|---|---|---|
| `POSTGRES_DB` | `odoo` | Base de datos por defecto (Odoo usa `--database madenat_test` en el comando) |
| `POSTGRES_USER` | `odoo` | Usuario PostgreSQL |
| `POSTGRES_PASSWORD` | `odoo` | Contraseña PostgreSQL |
| `POSTGRES_INITDB_ARGS` | `--data-checksums` | Argumento de inicialización (checksums para integridad de datos) |

### Servicio pgadmin

| Variable | Valor | Descripción |
|---|---|---|
| `PGADMIN_DEFAULT_EMAIL` | `admin@madenat.com` | Usuario de login de pgAdmin |
| `PGADMIN_DEFAULT_PASSWORD` | `admin` | Contraseña de login de pgAdmin |

---

## Redes y volúmenes

### Redes Docker

| Red | Tipo | Propósito |
|---|---|---|
| `web_network` | External | Red pública para Traefik (Odoo y pgAdmin expuestos vía reverse proxy) |
| `internal_backend` | Bridge (auto) | Red interna privada (PostgreSQL + Odoo se comunican sin exposición externa) |

> **Nota:** PostgreSQL solo está en `internal_backend` — no es accesible desde fuera del stack.

### Volúmenes Docker

| Volumen | Montaje | Contenido |
|---|---|---|
| `odoo-web-data` | `/var/lib/odoo` | Filestore de Odoo (adjuntos, imágenes, datos binarios) |
| `odoo-db-data` | `/var/lib/postgresql/data` | Datos de PostgreSQL (tablas, índices, WAL) |

### Volúmenes bind (directorio host → container)

| Host | Container | Propósito |
|---|---|---|
| `./custom_addons` | `/mnt/extra-addons` | Módulos MADENAT (desarrollo local) |
| `./config/odoo.conf` | `/etc/odoo/odoo.conf` | Configuración de Odoo |

---

## Límites de memoria

| Servicio | Reserva | Límite |
|---|---|---|
| `odoo18_app` | 512M | 2G |
| `odoo18_db` | 256M | 1G |
| `odoo18_pgadmin` | — | 512M |

---

## Acceso local

### Odoo
- **Directo:** `http://127.0.0.1:8069`
- **Vía Traefik:** `http://odoo18.localhost` (requiere entrada DNS local o hosts file)

### pgAdmin
- **Vía Traefik:** `http://pgadmin.localhost`
- **Login:** `admin@madenat.com` / `admin`

### PostgreSQL directo
- **No accesible desde el host** — el puerto 5432 no está expuesto
- Acceso solo vía `docker exec`:
  ```bash
  docker exec -it odoo18_db psql -U odoo -d odoo
  ```

---

## Comando de inicio de Odoo

```yaml
command: >
  --config /etc/odoo/odoo.conf
  --database madenat_test
  --dev=reload,qweb,werkzeug
```

> **Nota:** La base de datos por defecto es `madenat_test`, no `odoo` (que es la DB de PostgreSQL por defecto).

---

## Advertencias

- Las credenciales (`odoo`/`odoo`, `admin`/`admin`) son **SOLO para desarrollo local**. Nunca usar en producción.
- **No existe archivo `.env` separado** — toda la configuración está en `docker-compose.yml`.
- El puerto 8069 solo escucha en `127.0.0.1` (no en `0.0.0.0`) — no es accesible desde otros hosts de la red.
- La red `web_network` es **external** — debe crearse manualmente antes de levantar el stack:
  ```bash
  docker network create web_network
  ```
- Si se elimina el volumen `odoo-db-data`, se pierden todos los datos de PostgreSQL irreversiblemente.
- `POSTGRES_INITDB_ARGS=--data-checksums` solo se aplica en la primera inicialización del contenedor.

---

## Relacionado

- [[entorno_wsl2_docker]]
- [[comandos_docker]]
- [[comandos_postgresql]]
- [[backup_restauracion]]
- [[INC-002_db_host_incorrecto]]
