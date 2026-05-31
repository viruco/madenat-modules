# INC-003 — [Errno 98] Address already in use

**Fecha detectado:** 2026-05-07
**Módulo afectado:** Infraestructura
**Severidad:** Medio
**Estado:** Resuelto

## Síntoma

```
OSError: [Errno 98] Address already in use
```

## Causa raíz

El container `odoo18_app` ya ocupaba el puerto 8069. Al intentar lanzar un segundo proceso Odoo, el puerto fue rechazado.

## Solución aplicada

```bash
docker ps | grep odoo18_app
docker stop odoo18_app
python odoo-bin -u madenat_lumber_core ...
```

## Prevención

Siempre `docker stop odoo18_app` antes de ejecutar `odoo-bin` directamente. Ver [[despliegue_modulo]].

## Relacionado

- [[entorno_wsl2_docker]]
- [[comandos_docker]]
- [[despliegue_modulo]]
