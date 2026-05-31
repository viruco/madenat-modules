# Entorno WSL2 + Docker + PostgreSQL

**Módulo:** Infraestructura
**Categoría:** Operación
**Estado:** Activo
**Última actualización:** 2026-05-28

---

## Propósito

Documentar el stack completo de desarrollo local de MADENAT para reproducir o recuperar el entorno de trabajo sin ambigüedad.

---

## Stack actual

| Componente | Versión / Nombre |
|---|---|
| OS Host | Windows 11 |
| WSL2 Distro | Ubuntu (viruco@viruco) |
| Docker Engine | Docker CE en WSL2 |
| Container Odoo | `odoo18_app` |
| Container PostgreSQL | `odoo18_db` |
| Red Docker | `odoo_network` |
| Puerto Odoo | 8069 |
| Puerto PostgreSQL | 5432 |
| Directorio custom_addons | `~/dev-stack/odoo/odoo-18-ce/custom_addons/` |
| Virtualenv Python | `(venv)` en `~/dev-stack/odoo/odoo-18-ce/` |

---

## Reglas de conexión

- `--db_host` SIEMPRE es `odoo18_db` (nombre del container PostgreSQL en la red Docker).
- `--db_user` SIEMPRE es `odoo`.
- `--db_password` SIEMPRE es `odoo`.
- NUNCA usar `localhost` como db_host cuando se trabaja desde dentro de Docker.
- NUNCA usar el nombre de la base de datos como db_host (error INC-002).

---

## Rutas críticas

```bash
# Custom addons
~/dev-stack/odoo/odoo-18-ce/custom_addons/

# Módulos MADENAT
~/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_core/
~/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_billing/

# Documentación canónica
~/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_docs/
```

---

## Restricciones conocidas

- Si el container `odoo18_app` ya está corriendo, el comando de inicio falla con `[Errno 98] Address already in use`. Ver [[INC-003_address_in_use]].
- PostgreSQL debe estar corriendo antes de iniciar Odoo. Verificar con `docker ps`.

---

## Relacionado

- [[comandos_odoo_dev]]
- [[comandos_docker]]
- [[comandos_postgresql]]
- [[variables_entorno]]
- [[INC-002_db_host_incorrecto]]
- [[INC-003_address_in_use]]
