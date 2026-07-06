# CIERRE DE VALIDACIÓN FINAL — STAGING
## Release 18.0.5.3.0 — Migración de limpieza de columnas legacy

**Fecha:** 2026-06-16
**Tipo:** Informe de cierre pre-producción
**Ejecutor:** Auditoría técnica Cline — sesión 2026-06-16

---

## RESUMEN EJECUTIVO

Validación final de la release 18.0.5.3.0 que elimina columnas legacy huérfanas (`stock_lot.lumber_reception_id`, `stock_picking.lumber_reception_id`) de PostgreSQL. Se ejecutaron verificaciones exhaustivas a nivel de código fuente y se documentan los pasos pendientes que requieren acceso al entorno staging vivo para ser completados.

### Cambios aplicados en esta release

| # | Archivo | Cambio | Estado |
|---|---------|--------|--------|
| 1 | `migrations/18.0.5.3.0/pre-migrate.py` | Creado — 2 `DROP COLUMN IF EXISTS` | ✅ |
| 2 | `__manifest__.py` | Versión `18.0.5.2.0` → `18.0.5.3.0` | ✅ |
| 3 | `migrations/18.0.5.2.0/post-migrate.py` | Blindado — verifica existencia de columna antes de UPDATE | ✅ |
| 4 | `views/menu_remapping.xml` (madenat_lumber_reports) | 10 `<delete>` tags: `search+ref()` → `id` (idempotente) | ✅ |

---

## VERIFICACIONES A NIVEL DE CÓDIGO FUENTE (COMPLETADO)

### V1 — Migración 18.0.5.3.0/pre-migrate.py

✅ El archivo contiene exactamente 2 sentencias SQL:
```sql
ALTER TABLE stock_lot DROP COLUMN IF EXISTS lumber_reception_id;
ALTER TABLE stock_picking DROP COLUMN IF EXISTS lumber_reception_id;
```
✅ `IF EXISTS` en ambas sentencias garantiza idempotencia.
✅ Es `pre-migrate` — se ejecuta antes de que Odoo cargue los modelos Python.
✅ Sin UPDATE, DELETE, ni manipulación de datos.

### V2 — Campos canónicos `reception_id` intactos

| Modelo | Archivo | Línea | Definición | Estado |
|--------|---------|-------|-----------|--------|
| `stock.lot` | `stock_lot.py` | 200 | `reception_id = fields.Many2one('lumber.reception', ...)` | ✅ |
| `stock.picking` | `stock_picking.py` | 15 | `reception_id = fields.Many2one('lumber.reception', ...)` | ✅ |

✅ Ninguno define `lumber_reception_id` como campo.

### V3 — Ausencia de referencias productivas a `lumber_reception_id`

✅ Búsqueda exhaustiva en `.py`, `.xml`, `.csv` de `madenat_lumber_core` y módulos dependientes (excluyendo `backups/`, `_archive/`, `RAW/`, `LEGADO/`, `.git/`, `migrations/18.0.5.*`):

| Módulo | Tipo | Referencias a `lumber_reception_id` |
|--------|------|-------------------------------------|
| `madenat_lumber_core/models/stock_lot.py` | Python | 0 |
| `madenat_lumber_core/models/stock_picking.py` | Python | 0 |
| `madenat_lumber_core/models/reception_service.py` | Python | 0 |
| `madenat_lumber_core/views/` | XML | 0 |
| `madenat_lumber_core/reports/` | XML | 0 |
| `madenat_lumber_core/wizard/` | XML | 0 |
| `madenat_lumber_reports/` | Python + XML | 0 |
| `madenat_lumber_costing/` | Python + XML | 0 |
| `madenat_lumber_logistics/` | Python + XML | 0 |
| `madenat_lumber_billing/` | Python + XML | 0 |
| `madenat_lumber_shipping_core/` | Python + XML | 0 |
| `_audit_trazabilidad.py` | Python | 0 (v2.0 corregido) |
| `_audit_db_check.py` | Python | 0 |

⚠️ Única excepción documentada: `madenat_lumber_purchasing/models/purchase_order.py` tiene `lumber_reception_id` y `lumber_reception_ids` como campos legacy en la tabla `purchase_order` — tabla/modelo distinto, fuera del alcance de esta migración.

### V4 — Migración 18.0.5.2.0/post-migrate.py idempotente

✅ Verifica `information_schema.columns` antes del UPDATE.
✅ Si la columna no existe, loguea skip y continúa.
✅ Si la columna existe, ejecuta el UPDATE original con guards WHERE.

### V5 — menu_remapping.xml sin `ref()` en deletes

✅ 10 tags `<delete>` migrados de `search="[('id','=',ref(...))]"` a `id="XML_ID"`.
✅ La nueva sintaxis es idempotente: si el External ID no existe, Odoo omite el delete sin error.

---

## VERIFICACIONES PENDIENTES — REQUIEREN STAGING VIVO

Las siguientes verificaciones requieren acceso a la base de datos PostgreSQL y al contenedor Odoo del entorno staging. El operador debe ejecutarlas manualmente y marcar cada casilla.

### Paso 1 — Lanzar upgrade del módulo

```bash
# Desde el host o dentro del contenedor odoo18_app:
docker exec odoo18_app odoo --config /etc/odoo/odoo.conf \
  --database madenat_test \
  --update madenat_lumber_core,madenat_lumber_reports \
  --stop-after-init
```

**Esperado:** El comando termina sin error (exit code 0). El log contiene:
- `Migration 18.0.5.3.0: dropped stock_lot.lumber_reception_id`
- `Migration 18.0.5.3.0: dropped stock_picking.lumber_reception_id`
- `Module madenat_lumber_core: loading...` sin tracebacks.

**Estado:** ☐ Pendiente

### Paso 2 — Verificar columnas legacy eliminadas

```sql
-- Debe devolver 0 filas
SELECT column_name FROM information_schema.columns
 WHERE table_schema = 'public' AND table_name = 'stock_lot'
   AND column_name = 'lumber_reception_id';

SELECT column_name FROM information_schema.columns
 WHERE table_schema = 'public' AND table_name = 'stock_picking'
   AND column_name = 'lumber_reception_id';
```

**Estado:** ☐ Pendiente

### Paso 3 — Verificar `reception_id` presente

```sql
SELECT column_name, data_type FROM information_schema.columns
 WHERE table_schema = 'public' AND table_name = 'stock_lot'
   AND column_name = 'reception_id';

SELECT column_name, data_type FROM information_schema.columns
 WHERE table_schema = 'public' AND table_name = 'stock_picking'
   AND column_name = 'reception_id';
```

**Esperado:** 1 fila con `data_type = 'integer'` en cada consulta.

**Estado:** ☐ Pendiente

### Paso 4 — Verificar constraints/índices residuales

```sql
SELECT conname, contype, conrelid::regclass AS table_name
  FROM pg_constraint WHERE conname ILIKE '%lumber_reception%';

SELECT indexname, tablename FROM pg_indexes
 WHERE indexname ILIKE '%lumber_reception%';
```

**Esperado:** 0 filas en ambas.

**Estado:** ☐ Pendiente

### Paso 5 — Verificar logs de Odoo sin errores

```bash
grep -iE "ERROR|CRITICAL|Traceback" /var/log/odoo/odoo.log \
  | grep -v "Expected error in test" | tail -20
```

**Esperado:** Sin errores nuevos atribuibles a la migración.

**Estado:** ☐ Pendiente

### Paso 6 — Verificar logs PostgreSQL sin errores de columna inexistente

```bash
grep -iE "lumber_reception_id|column.*does not exist" \
  /var/log/postgresql/postgresql-*.log | tail -10
```

**Esperado:** 0 líneas.

**Estado:** ☐ Pendiente

### Paso 7 — Verificar versión registrada del módulo

```sql
SELECT name, latest_version, state FROM ir_module_module
 WHERE name = 'madenat_lumber_core';
```

**Esperado:** `latest_version = '18.0.5.3.0'`, `state = 'installed'`.

**Estado:** ☐ Pendiente

### Paso 8 — Abrir las vistas principales en Odoo

Navegar manualmente en el UI de Odoo staging y verificar que cargan sin OwlError ni traceback:

- [ ] Inventario → Lotes/Números de serie → Vista lista
- [ ] Inventario → Lotes/Números de serie → Abrir un lote (formulario)
- [ ] Inventario → Recepciones → Vista lista
- [ ] Reportes MADENAT → Inventario Recepción → R1, R2, R5, R7, R9

**Estado:** ☐ Pendiente

### Paso 9 — Verificar reportes de trazabilidad

Ejecutar la auditoría de trazabilidad y confirmar que usa `reception_id`:

```bash
python3 /mnt/extra-addons/_audit_trazabilidad.py
cat /mnt/extra-addons/_audit_trazabilidad_result.json | python3 -m json.tool | head -40
```

**Estado:** ☐ Pendiente

### Paso 10 — Verificar vistas materializadas y reglas PostgreSQL

```sql
SELECT schemaname, viewname FROM pg_views
 WHERE definition ILIKE '%lumber_reception_id%';

SELECT rulename, tablename FROM pg_rules
 WHERE definition ILIKE '%lumber_reception_id%';
```

**Esperado:** 0 filas en ambas.

**Estado:** ☐ Pendiente

---

## HALLAZGOS DOCUMENTADOS (NO BLOQUEANTES)

| # | Hallazgo | Ubicación | Impacto | Acción |
|---|----------|-----------|---------|--------|
| H1 | `lumber_reception_id` y `lumber_reception_ids` existen en `purchase.order` | `madenat_lumber_purchasing/models/purchase_order.py:35-46` | Ninguno. Tabla distinta, no tocada por esta migración. | Backlog para limpieza futura |
| H2 | Archivos `.bak` residuales en `madenat_lumber_reports/` | `models/lumber_reception_reports.py.bak`, `reports/inventory_report_pdf.xml.bak`, `views/lumber_reports_menu.xml.bak.20260606_121330` | Ninguno. Archivos de backup, no leídos por Odoo. | Limpiar en próxima sesión de housekeeping |

---

## DICTAMEN FINAL

### Estado: CONDICIONALMENTE APROBADO

**Código fuente:** ✅ APROBADO — Todos los cambios son mínimos, seguros y verificados:
- Migración con solo 2 `DROP COLUMN IF EXISTS`
- Migración histórica blindada contra re-ejecución
- XML deletes idempotentes sin `ref()` quebradizo
- `reception_id` intacto como FK canónica única
- Cero referencias productivas a `lumber_reception_id` en `stock.lot` y `stock.picking`

**Staging vivo:** 🔄 PENDIENTE — Los pasos 1 a 10 de la sección anterior deben completarse antes de promocionar a producción. Ninguno de estos pasos requiere cambios de código; son verificaciones puramente observacionales.

### Recomendación

**APROBADO PARA PRODUCCIÓN** una vez que los pasos 1 a 10 sean ejecutados en staging y todos marquen ☐ → ✅ sin hallazgos bloqueantes.

### Procedimiento de promoción

1. Ejecutar pasos 1–10 en staging.
2. Si todos pasan → ejecutar en producción:
   ```bash
   docker exec odoo18_app odoo --config /etc/odoo/odoo.conf \
     --database madenat_prod \
     --update madenat_lumber_core,madenat_lumber_reports \
     --stop-after-init
   ```
3. Repetir pasos 2–6 en producción para confirmación post-deploy.
4. Si algún paso falla en producción → revisar logs, corregir causa raíz, re-ejecutar.

### Riesgos residuales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|------------|---------|------------|
| Script SQL externo que referencie `lumber_reception_id` por nombre de columna | Baja | Alto (rompe el script) | Auditoría de scripts externos antes de producción |
| Extensión third-party no auditada que use la columna legacy | Muy baja | Alto | Los módulos auditados están limpios. Si hay módulos no incluidos en este repo, auditarlos aparte. |
| `purchase_order.lumber_reception_id` causa confusión futura | Media | Bajo | Documentado en H1. Limpiar en release separada. |

---

**Documento generado:** 2026-06-16
**Ejecutado por:** Auditoría técnica Cline — sesión 2026-06-16
**Próximo paso:** Ejecutar pasos 1–10 en staging vivo.