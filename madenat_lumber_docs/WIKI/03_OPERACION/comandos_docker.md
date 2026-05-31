# Comandos Docker — MADENAT

**Módulo:** Infraestructura
**Categoría:** Operación
**Estado:** Activo
**Última actualización:** 2026-05-28

---

## Propósito

Centralizar los comandos de gestión de contenedores Docker para el entorno de desarrollo MADENAT.

---

## Estado del entorno

```bash
# Ver todos los containers
docker ps -a

# Ver solo los de MADENAT
docker ps | grep odoo
```

---

## Iniciar entorno completo

```bash
# Iniciar PostgreSQL primero
docker start odoo18_db

# Iniciar Odoo después
docker start odoo18_app
```

---

## Detener entorno

```bash
docker stop odoo18_app
docker stop odoo18_db
```

---

## Reiniciar Odoo (después de cambios)

```bash
docker restart odoo18_app
```

---

## Ver logs

```bash
# Logs Odoo en tiempo real
docker logs -f odoo18_app

# Últimas 100 líneas
docker logs --tail 100 odoo18_app

# Logs PostgreSQL
docker logs --tail 50 odoo18_db
```

---

## Entrar al container

```bash
# Shell en container Odoo
docker exec -it odoo18_app bash

# Shell en container PostgreSQL
docker exec -it odoo18_db bash
```

---

## Red Docker

```bash
# Ver redes
docker network ls

# Inspeccionar red de Odoo
docker network inspect odoo_network
```

---

## Restricciones conocidas

- Siempre iniciar `odoo18_db` antes que `odoo18_app`.
- Si el container ya está corriendo y se intenta iniciar de nuevo, falla con error de puerto. Ver [[INC-003_address_in_use]].

---

## Relacionado

- [[entorno_wsl2_docker]]
- [[comandos_odoo_dev]]
- [[comandos_postgresql]]
- [[INC-003_address_in_use]]
