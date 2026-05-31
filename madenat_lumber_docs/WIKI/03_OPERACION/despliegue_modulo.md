# Flujo de Despliegue de Módulo

**Módulo:** madenat_lumber_core / madenat_lumber_billing
**Categoría:** Operación
**Estado:** Activo
**Última actualización:** 2026-05-28

---

## Propósito

Documentar el flujo completo y ordenado para desplegar cambios en módulos MADENAT sin romper el entorno ni la base de datos.

---

## Flujo estándar de despliegue

### Paso 1 — Verificar entorno

```bash
docker ps | grep odoo
```
Confirmar que `odoo18_db` y `odoo18_app` están corriendo.

### Paso 2 — Verificar que no hay errores de sintaxis

```bash
cd ~/dev-stack/odoo/odoo-18-ce
source venv/bin/activate
python -m py_compile custom_addons/madenat_lumber_core/models/*.py
```

### Paso 3 — Detener Odoo

```bash
docker stop odoo18_app
```

### Paso 4 — Actualizar módulo

```bash
python odoo-bin -u madenat_lumber_core \
  -d MADENAT_DEV \
  --db_host=odoo18_db \
  --db_port=5432 \
  --db_user=odoo \
  --db_password=odoo \
  --stop-after-init
```

### Paso 5 — Reiniciar Odoo

```bash
docker start odoo18_app
docker logs -f odoo18_app
```

### Paso 6 — Verificar en navegador

Abrir `http://localhost:8069` y verificar que el módulo cargó sin errores.

---

## Regla para cambios de modelo (nuevos campos o tablas)

Si el cambio agrega o modifica campos en modelos, el paso 4 es obligatorio con `-u`.
Si el cambio solo modifica vistas XML o datos, se puede forzar la actualización desde la interfaz Odoo en `Configuración → Aplicaciones`.

---

## Restricciones conocidas

- Si hay columna nueva en un modelo y no se ejecuta `-u`, Odoo lanza error de columna inexistente. Ver [[INC-004_column_inexistente]].
- Nunca hacer `-i` (install) sobre un módulo ya instalado en producción; usar siempre `-u` (update).

---

## Relacionado

- [[entorno_wsl2_docker]]
- [[comandos_odoo_dev]]
- [[INC-003_address_in_use]]
- [[INC-004_column_inexistente]]
