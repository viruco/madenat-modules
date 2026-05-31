# DEC-005 — Estrategia de Despliegue en Oracle Cloud

**Fecha:** 2026-05-02
**Estado:** Aceptada — pendiente de ejecución (julio 2026)
**Módulo afectado:** Infraestructura

## Contexto

MADENAT necesita entorno de producción estable con acceso remoto, backups y capacidad de migrar a Odoo 19 CE.

## Decisión tomada

Usar Oracle Cloud Free Tier (ARM Ampere: 4 vCPU, 24 GB RAM) con Odoo 19 CE en Docker sobre Ubuntu Server. PostgreSQL como servicio del sistema operativo para mejor I/O en producción.

## Impacto

- Migración planificada julio 2026.
- En producción `--db_host=localhost` (PostgreSQL nativo, no en container).
- Preparar script de migración de datos DEV → PROD.

## Criterio de revisión

Si Oracle cambia condiciones del Free Tier, evaluar Hetzner CX22 como alternativa.

## Referencias

- [[migracion_odoo19]]
- [[DEC-004_postgresql_docker]]
- [[backup_restauracion]]
