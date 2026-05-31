# Comandos Odoo — Desarrollo MADENAT

**Módulo:** Infraestructura
**Categoría:** Operación
**Estado:** Activo
**Última actualización:** 2026-05-28

---

## Propósito

Centralizar los comandos exactos para actualizar, reiniciar, debuggear y trabajar con Odoo 18 en el entorno local de MADENAT.

---

## Actualizar módulo (más usado)

```bash
# Actualizar madenat_lumber_core
python odoo-bin -u madenat_lumber_core \
  -d MADENAT_DEV \
  --db_host=odoo18_db \
  --db_port=5432 \
  --db_user=odoo \
  --db_password=odoo \
  --stop-after-init

# Actualizar ambos módulos en secuencia correcta
python odoo-bin -u madenat_lumber_core,madenat_lumber_billing \
  -d MADENAT_DEV \
  --db_host=odoo18_db \
  --db_port=5432 \
  --db_user=odoo \
  --db_password=odoo \
  --stop-after-init
```

---

## Iniciar Odoo (modo desarrollo)

```bash
python odoo-bin \
  -d MADENAT_DEV \
  --db_host=odoo18_db \
  --db_port=5432 \
  --db_user=odoo \
  --db_password=odoo \
  --dev=all
```

---

## Instalar módulo desde cero

```bash
python odoo-bin -i madenat_lumber_core \
  -d MADENAT_DEV \
  --db_host=odoo18_db \
  --db_port=5432 \
  --db_user=odoo \
  --db_password=odoo \
  --stop-after-init
```

---

## Ejecutar tests

```bash
python odoo-bin -u madenat_lumber_core \
  --test-enable \
  --test-tags madenat \
  -d MADENAT_TEST \
  --db_host=odoo18_db \
  --db_port=5432 \
  --db_user=odoo \
  --db_password=odoo \
  --stop-after-init
```

---

## Verificar logs en tiempo real

```bash
docker logs -f odoo18_app
```

---

## Restricciones conocidas

- SIEMPRE `--db_host=odoo18_db`, nunca `localhost` ni nombre de base de datos.
- Si el puerto 8069 está ocupado, el container ya está corriendo. Ver [[INC-003_address_in_use]].
- En base de datos de producción (`MADENAT_PROD`) nunca usar `--dev=all`.

---

## Relacionado

- [[entorno_wsl2_docker]]
- [[comandos_docker]]
- [[despliegue_modulo]]
- [[INC-002_db_host_incorrecto]]
- [[INC-003_address_in_use]]
- [[INC-004_column_inexistente]]
