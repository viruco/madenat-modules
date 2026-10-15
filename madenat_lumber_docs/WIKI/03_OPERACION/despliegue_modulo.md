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

## Registro de correcciones de despliegue (2026-10-06)

La actualización remota de `madenat_lumber_logistics` falló primero por un **registro obsoleto** y luego por un **atributo inválido en una vista lista**. Corregido en el código local (DEV):

| # | Error remoto | Archivo | Corrección |
|---|---|---|---|
| A | `Cannot update missing record: madenat_lumber_shipping_core.menu_shipping_booking` | `madenat_lumber_logistics/views/logistics_menus.xml` | **Eliminado** el bloque `<record id="madenat_lumber_shipping_core.menu_shipping_booking" model="ir.ui.menu"><field name="active" eval="False"/></record>` (apuntaba a un registro de Shipping inexistente). Se **conserva** el `menuitem id="menu_shipping_booking"` ("Reservas") definido en Logistics (acción, padre y secuencia intactos). |
| B | `Invalid attribute help for element field` (vista `lumber.shipment.document.backlog.list`) | `madenat_lumber_logistics/views/lumber_document_checklist_views.xml` | `<field name="backlog_note" optional="show" help="…"/>` → `<field name="backlog_note" optional="show"/>`. Se conservan header, botones (Escalar/Cerrar/Exonerar), `groups`/`invisible`/`confirm` y decoraciones. **No** se toca `<field name="help" type="html">` de la acción. |

**Actualización remota:** tras aplicar ambas correcciones, terminó con `Modules loaded`, `Registry loaded` y **resultado 0** (reportado por el usuario).

**Validación local efectivamente realizada:** XML **bien formado** en ambos archivos (`xml.dom.minidom`); bloque obsoleto ausente; `menuitem` de Reservas presente; `backlog_note` con `optional="show"` y sin `help`.

**Límites:** no se ejecutó Odoo ni `-u` localmente; **no** se declara "validado por Odoo en local". XML bien formado ≠ validación completa de vistas por Odoo.

**Pendientes existentes (fuera de alcance, sin modificar):** avisos de grupos no encontrados; dependencias de `volume_detail_line_ids`; ACL eliminadas durante la actualización; menús por perfil; edición de etiquetas/lotes/packing; estados/guards/métodos de negocio.

**Paquete:** si existe `madenat_addons.tar.gz`, debe **regenerarse** para incluir estas correcciones; el paquete anterior **no** está actualizado.

---

## Paquete ACUMULADO pendiente para TEST remoto (2026-10-12) — **NO EJECUTADO**

| Módulo | Versión local vigente | Nota |
|---|---|---|
| `madenat_lumber_logistics` | **18.0.1.26.0** | HOTFIX OWL chatter (`div.oe_chatter` → `<chatter/>`) + WIP de rebaja |
| `madenat_lumber_core` | 18.0.6.7.0 | WIP previo (audit log / guarda FK etiqueta SV) |
| `madenat_lumber_intake` | 18.0.0.13.0 | WIP previo |
| `madenat_lumber_costing` | 18.0.1.0.0 | WIP previo |

- **Comando (por módulo, NUNCA `-u all`):**
  `odoo -d <db> -u madenat_lumber_core,madenat_lumber_intake,madenat_lumber_logistics --stop-after-init --no-http`
- **TEST remoto:** **NO inspeccionado ni modificado** en esta intervención; Cristhian usa la **versión anterior**.
  Leer en **solo lectura** la versión instalada antes de desplegar.
- **Detalle y rollback:** expediente `HOTFIX_OWL_CHATTER_OE_20261012/docs/PLAN_DESPLIEGUE_ACUMULADO.md`.

## Relacionado

- [[entorno_wsl2_docker]]
- [[comandos_odoo_dev]]
- [[INC-003_address_in_use]]
- [[INC-004_column_inexistente]]
