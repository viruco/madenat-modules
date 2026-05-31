# DEC-004 — PostgreSQL en Contenedor Docker Separado

**Fecha:** 2026-03-01
**Estado:** Aceptada
**Módulo afectado:** Infraestructura

## Contexto

Se evaluó si PostgreSQL debía correr en WSL2 nativo o en container separado de Odoo.

## Decisión tomada

PostgreSQL corre en container `odoo18_db` separado de `odoo18_app`, comunicados por la red `odoo_network`. Host de conexión: siempre `odoo18_db`.

## Impacto

- Todos los comandos Odoo usan `--db_host=odoo18_db`.
- Nunca usar `localhost` como db_host en desarrollo.
- `odoo18_db` debe iniciarse siempre antes que `odoo18_app`.

## Criterio de revisión

En producción (Oracle Cloud) PostgreSQL correrá como servicio del sistema. Esta decisión aplica solo a entorno de desarrollo local.

## Referencias

- [[entorno_wsl2_docker]]
- [[comandos_odoo_dev]]
- [[INC-002_db_host_incorrecto]]
