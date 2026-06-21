# CHECKLIST DE VALIDACIÓN POST-MIGRACIÓN — STAGING
## Migración 18.0.5.3.0 — Eliminación de columnas legacy `lumber_reception_id`

**Fecha:** 2026-06-16
**Tipo:** Checklist de validación pre-producción
**Alcance:** Solo staging — NO ejecutar en producción sin aprobación previa
**Migración asociada:** `custom_addons/madenat_lumber_core/migrations/18.0.5.3.0/pre-migrate.py`
**Objetivo:** Confirmar que la eliminación de columnas huérfanas no rompió nada y que `reception_id` permanece como única FK canónica

---

## RESUMEN EJECUTIVO

Esta migración ejecuta únicamente:
```sql
ALTER TABLE stock_lot DROP COLUMN IF EXISTS lumber_reception_id;
ALTER TABLE stock_picking DROP COLUMN IF EXISTS lumber_reception_id;
```

La validación debe confirmar que:
1. Las columnas fueron eliminadas físicamente de PostgreSQL.
2. `reception_id` sigue presente, poblado y funcional.
3. El módulo `madenat_lumber_core` y sus dependientes arrancan sin errores.
4. Vistas, reportes y flujos operativos funcionan sin regresiones.
5. No hay consultas huérfanas que referencien las columnas eliminadas.

---

## SECCIÓN 1 — VALIDACIÓN DE BASE DE DATOS

### 1.1 Confirmar eliminación de columna en `stock_lot`

**Qué revisar:** La columna `lumber_reception_id` ya no existe en la tabla `stock_lot`.

**Cómo revisarlo:**
```sql
SELECT column_name
  FROM information_schema.columns
 WHERE table_schema = 'public'
   AND table_name = 'stock_lot'
   AND column_name = 'lumber_reception_id';
```

**Resultado esperado:** **0 filas** (la columna no existe).

**Señal de alarma:** Si devuelve 1 fila, la migración no se ejecutó o falló silenciosamente. Revisar logs de Odoo al iniciar el módulo y verificar que la versión en `__manifest__.py` es `18.0.5.3.0`.

**Qué hacer si falla:** Ejecutar manualmente `ALTER TABLE stock_lot DROP COLUMN IF EXISTS lumber_reception_id;` y revisar el log de `ir_module_module` para confirmar que el estado del módulo es `installed` con versión `18.0.5.3.0`.

**Aprobado / No aprobado:** ☐

---

### 1.2 Confirmar eliminación de columna en `stock_picking`

**Qué revisar:** La columna `lumber_reception_id` ya no existe en la tabla `stock_picking`.

**Cómo revisarlo:**
```sql
SELECT column_name
  FROM information_schema.columns
 WHERE table_schema = 'public'
   AND table_name = 'stock_picking'
   AND column_name = 'lumber_reception_id';
```

**Resultado esperado:** **0 filas**.

**Señal de alarma:** Igual que 1.1.

**Qué hacer si falla:** Ejecutar manualmente `ALTER TABLE stock_picking DROP COLUMN IF EXISTS lumber_reception_id;`.

**Aprobado / No aprobado:** ☐

---

### 1.3 Confirmar que `reception_id` sigue presente en `stock_lot`

**Qué revisar:** La columna `reception_id` existe en `stock_lot`.

**Cómo revisarlo:**
```sql
SELECT column_name, data_type, is_nullable
  FROM information_schema.columns
 WHERE table_schema = 'public'
   AND table_name = 'stock_lot'
   AND column_name = 'reception_id';
```

**Resultado esperado:** 1 fila con `data_type = 'integer'` (FK a `lumber_reception`).

**Señal de alarma:** Si devuelve 0 filas, la columna canónica fue eliminada por error. **BLOQUEAR DESPLIEGUE A PRODUCCIÓN.**

**Aprobado / No aprobado:** ☐

---

### 1.4 Confirmar que `reception_id` sigue presente en `stock_picking`

**Qué revisar:** La columna `reception_id` existe en `stock_picking`.

**Cómo revisarlo:**
```sql
SELECT column_name, data_type, is_nullable
  FROM information_schema.columns
 WHERE table_schema = 'public'
   AND table_name = 'stock_picking'
   AND column_name = 'reception_id';
```

**Resultado esperado:** 1 fila con `data_type = 'integer'`.

**Señal de alarma:** Si devuelve 0 filas, **BLOQUEAR DESPLIEGUE A PRODUCCIÓN.**

**Aprobado / No aprobado:** ☐

---

### 1.5 Confirmar integridad de datos: `stock_lot.reception_id` poblado donde existía `lumber_reception_id`

**Qué revisar:** Los lotes que estaban vinculados a recepciones antes de la migración 18.0.5.2.0 mantienen su `reception_id`.

**Cómo revisarlo:**
```sql
-- Cuenta total de lotes vinculados a recepción
SELECT COUNT(*) AS total_lots_with_reception
  FROM stock_lot
 WHERE reception_id IS NOT NULL;

-- Verifica que no haya lotes con reception_id roto (FK a registro inexistente)
SELECT sl.id, sl.name, sl.reception_id
  FROM stock_lot sl
  LEFT JOIN lumber_reception lr ON lr.id = sl.reception_id
 WHERE sl.reception_id IS NOT NULL
   AND lr.id IS NULL;
```

**Resultado esperado:**
- `total_lots_with_reception` ≥ 0 (depende de los datos de staging).
- Segunda consulta: **0 filas** (sin FK huérfanas).

**Señal de alarma:** Si la segunda consulta devuelve filas, hay `reception_id` apuntando a registros borrados. Esto es un problema de datos preexistente, no de esta migración, pero debe documentarse.

**Aprobado / No aprobado:** ☐

---

### 1.6 Confirmar integridad de datos: `stock_picking.reception_id` poblado

**Qué revisar:** Los pickings vinculados a recepciones mantienen su `reception_id`.

**Cómo revisarlo:**
```sql
SELECT COUNT(*) AS total_pickings_with_reception
  FROM stock_picking
 WHERE reception_id IS NOT NULL;

-- FK huérfanas
SELECT sp.id, sp.name, sp.reception_id
  FROM stock_picking sp
  LEFT JOIN lumber_reception lr ON lr.id = sp.reception_id
 WHERE sp.reception_id IS NOT NULL
   AND lr.id IS NULL;
```

**Resultado esperado:** Segunda consulta: **0 filas**.

**Aprobado / No aprobado:** ☐

---

### 1.7 Verificar que no hay constraints residuales sobre las columnas legacy

**Qué revisar:** Ningún constraint, índice o FK reference `lumber_reception_id`.

**Cómo revisarlo:**
```sql
-- Buscar constraints que mencionen lumber_reception_id
SELECT conname, contype, conrelid::regclass AS table_name
  FROM pg_constraint
 WHERE conname ILIKE '%lumber_reception%';

-- Buscar índices residuales
SELECT indexname, tablename
  FROM pg_indexes
 WHERE indexname ILIKE '%lumber_reception%';
```

**Resultado esperado:** **0 filas** en ambas consultas.

**Señal de alarma:** Si aparece algún constraint o índice, fue creado fuera de Odoo y debe eliminarse manualmente antes de producción.

**Aprobado / No aprobado:** ☐

---

## SECCIÓN 2 — VALIDACIÓN DE ARRANQUE DEL MÓDULO

### 2.1 Confirmar versión registrada del módulo

**Qué revisar:** Odoo registró la nueva versión `18.0.5.3.0` para `madenat_lumber_core`.

**Cómo revisarlo:**
```sql
SELECT name, latest_version, state
  FROM ir_module_module
 WHERE name = 'madenat_lumber_core';
```

**Resultado esperado:**
- `latest_version = '18.0.5.3.0'`
- `state = 'installed'`

**Señal de alarma:** Si `latest_version` es `18.0.5.2.0` o anterior, la migración no se ejecutó. Revisar `ir_module_module_dependency` y forzar upgrade con `-u madenat_lumber_core`.

**Aprobado / No aprobado:** ☐

---

### 2.2 Confirmar que no hay errores al iniciar Odoo

**Qué revisar:** El log de arranque de Odoo no contiene errores relacionados con `madenat_lumber_core` ni con `lumber_reception_id`.

**Cómo revisarlo:**
```bash
grep -iE "lumber_reception_id|madenat_lumber_core.*error|madenat_lumber_core.*fail|madenat_lumber_core.*traceback" \
  /var/log/odoo/odoo.log | tail -50
```

**Resultado esperado:** **0 líneas** de error relevantes.

**Señal de alarma:** Cualquier `Traceback`, `ERROR` o `CRITICAL` relacionado con el módulo requiere análisis antes de continuar.

**Aprobado / No aprobado:** ☐

---

### 2.3 Confirmar que todos los módulos dependientes cargan correctamente

**Qué revisar:** Los módulos que dependen de `madenat_lumber_core` están en estado `installed`.

**Cómo revisarlo:**
```sql
SELECT name, state, latest_version
  FROM ir_module_module
 WHERE name IN (
    'madenat_lumber_reports',
    'madenat_lumber_costing',
    'madenat_lumber_logistics',
    'madenat_lumber_purchasing',
    'madenat_lumber_billing',
    'madenat_lumber_shipping_core'
 );
```

**Resultado esperado:** Todos los módulos presentes en staging con `state = 'installed'`. Si alguno no existe en staging, ignorar.

**Señal de alarma:** Si algún módulo está en `uninstalled` o `to upgrade` sin razón, requiere upgrade manual.

**Aprobado / No aprobado:** ☐

---

### 2.4 Verificar que la migración aparece en el historial de migraciones ejecutadas

**Qué revisar:** El registry de migraciones de Odoo registró la ejecución de `18.0.5.3.0`.

**Cómo revisarlo:**
```sql
SELECT name, version
  FROM ir_module_module_version
 WHERE name = 'madenat_lumber_core'
 ORDER BY id DESC
 LIMIT 3;
```

O alternativamente revisar el log:
```bash
grep "Migration 18.0.5.3.0" /var/log/odoo/odoo.log
```

**Resultado esperado:** Al menos una línea con `Migration 18.0.5.3.0: dropped stock_lot.lumber_reception_id` y `Migration 18.0.5.3.0: dropped stock_picking.lumber_reception_id`.

**Señal de alarma:** Si no aparece, la migración no se ejecutó. Revisar que el archivo `pre-migrate.py` esté presente en el directorio correcto y que el nombre del directorio coincida exactamente con la versión en `__manifest__.py`.

**Aprobado / No aprobado:** ☐

---

## SECCIÓN 3 — VALIDACIÓN DE VISTAS Y ACCIONES

### 3.1 Vista de lista de `stock.lot` (lotes)

**Qué revisar:** La vista de lista/kanban de lotes carga sin errores.

**Cómo revisarlo:** Navegar en Odoo a **Inventario → Productos → Lotes/Números de serie**, o alternativamente:
```bash
curl -s -o /dev/null -w "%{http_code}" \
  "http://localhost:8069/web/dataset/search_read?model=stock.lot&fields=name,reception_id&limit=5"
```

**Resultado esperado:** HTTP 200, la vista carga. El campo `reception_id` aparece en la respuesta.

**Señal de alarma:** HTTP 500 o traceback en logs. Revisar si alguna vista XML referencia `lumber_reception_id`.

**Aprobado / No aprobado:** ☐

---

### 3.2 Vista de formulario de `stock.lot`

**Qué revisar:** Abrir un lote existente no produce errores.

**Cómo revisarlo:**
```sql
-- Obtener un ID de lote válido
SELECT id, name FROM stock_lot WHERE reception_id IS NOT NULL LIMIT 1;
```
Luego navegar a ese lote en Odoo o vía API:
```bash
curl -s -o /dev/null -w "%{http_code}" \
  "http://localhost:8069/web/dataset/search_read?model=stock.lot&fields=name,reception_id,espesor_mm,ancho_mm,largo_m,volumen_m3&domain=[('id','=',<LOT_ID>)]"
```

**Resultado esperado:** HTTP 200, todos los campos canónicos devuelven datos.

**Aprobado / No aprobado:** ☐

---

### 3.3 Vista de lista de `stock.picking` (albaranes/recepciones)

**Qué revisar:** La vista de albaranes de recepción carga sin errores.

**Cómo revisarlo:** Navegar a **Inventario → Recepciones** y verificar que la lista carga. O vía API:
```bash
curl -s -o /dev/null -w "%{http_code}" \
  "http://localhost:8069/web/dataset/search_read?model=stock.picking&fields=name,reception_id&domain=[('reception_id','!=',False)]&limit=5"
```

**Resultado esperado:** HTTP 200.

**Aprobado / No aprobado:** ☐

---

### 3.4 Vista de formulario de `stock.picking`

**Qué revisar:** Abrir un picking vinculado a recepción no produce errores.

**Cómo revisarlo:**
```sql
SELECT id, name FROM stock_picking WHERE reception_id IS NOT NULL LIMIT 1;
```
Verificar vía API que el registro es legible.

**Resultado esperado:** HTTP 200, `reception_id` devuelto con valor.

**Aprobado / No aprobado:** ☐

---

### 3.5 Vista de recepciones (`lumber.reception`)

**Qué revisar:** La vista canónica de recepciones carga correctamente.

**Cómo revisarlo:** Navegar a la vista de recepciones MADENAT en Odoo o:
```bash
curl -s -o /dev/null -w "%{http_code}" \
  "http://localhost:8069/web/dataset/search_read?model=lumber.reception&fields=name,state&limit=5"
```

**Resultado esperado:** HTTP 200.

**Aprobado / No aprobado:** ☐

---

## SECCIÓN 4 — VALIDACIÓN DE REPORTES

### 4.1 Reporte de inventario PDF

**Qué revisar:** El reporte de inventario se genera sin errores.

**Cómo revisarlo:** Desde Odoo, ejecutar el reporte de inventario o:
```bash
# Verificar que el action del reporte existe y es accesible
curl -s "http://localhost:8069/web/dataset/search_read?model=ir.actions.report&fields=name,report_name&domain=[('model','=','stock.lot')]"
```

**Resultado esperado:** El action existe y es accesible. Al generar el PDF no hay traceback.

**Señal de alarma:** Si el reporte referencia `lumber_reception_id` en su definición QWeb o en consultas SQL custom, fallará.

**Aprobado / No aprobado:** ☐

---

### 4.2 Reporte de trazabilidad

**Qué revisar:** Consultas de trazabilidad de lotes funcionan con `reception_id`.

**Cómo revisarlo:** Ejecutar una consulta de trazabilidad típica:
```sql
-- Trazabilidad: lote → recepción → picking
SELECT
    sl.name AS lot_name,
    lr.name AS reception_name,
    sp.name AS picking_name
  FROM stock_lot sl
  JOIN lumber_reception lr ON lr.id = sl.reception_id
  LEFT JOIN stock_picking sp ON sp.reception_id = lr.id
 WHERE sl.reception_id IS NOT NULL
 LIMIT 10;
```

**Resultado esperado:** La consulta ejecuta sin error y devuelve datos si existen.

**Señal de alarma:** Si falla con `column sl.lumber_reception_id does not exist`, hay una vista materializada, reporte QWeb o script externo que aún referencia la columna legacy.

**Aprobado / No aprobado:** ☐

---

## SECCIÓN 5 — VALIDACIÓN DE FLUJOS OPERATIVOS

### 5.1 Flujo: Crear un lote vinculado a recepción

**Qué revisar:** Es posible crear un `stock.lot` con `reception_id` asignado.

**Cómo revisarlo:** Desde la interfaz de Odoo, crear un lote manual y asignarle una recepción existente. O verificar que el modelo acepta la operación:
```python
# Desde Odoo shell o script de validación
lot = env['stock.lot'].search([('reception_id', '!=', False)], limit=1)
assert lot.reception_id, "El lote no tiene reception_id"
print(f"OK: Lote {lot.name} vinculado a recepción {lot.reception_id.name}")
```

**Resultado esperado:** El lote se crea/lee sin errores. `reception_id` es funcional.

**Aprobado / No aprobado:** ☐

---

### 5.2 Flujo: Navegar de picking a sus lotes (`lumber_lot_ids`)

**Qué revisar:** El campo relacionado `lumber_lot_ids` en `stock.picking` sigue funcionando.

**Cómo revisarlo:**
```sql
-- Verifica que la relación picking → lotes vía reception_id funciona
SELECT sp.name AS picking,
       COUNT(sl.id) AS lot_count
  FROM stock_picking sp
  JOIN stock_lot sl ON sl.reception_id = sp.reception_id
 WHERE sp.reception_id IS NOT NULL
 GROUP BY sp.name
 LIMIT 5;
```

**Resultado esperado:** La consulta devuelve conteos > 0 donde hay recepciones con lotes.

**Señal de alarma:** Si `lot_count = 0` para todos los pickings con recepción, los lotes pueden no estar vinculados correctamente.

**Aprobado / No aprobado:** ☐

---

### 5.3 Flujo: Validación técnica y financiera de lotes

**Qué revisar:** Los campos `technical_validation` y `financial_validation` en `stock.lot` y sus agregados en `stock.picking` (`reception_technical_validation`, `reception_financial_validation`) se computan sin errores.

**Cómo revisarlo:**
```sql
SELECT DISTINCT reception_technical_validation, reception_financial_validation
  FROM stock_picking
 WHERE reception_id IS NOT NULL;
```

**Resultado esperado:** Valores `pending`, `approved` o `rejected`. Sin NULLs inesperados donde hay recepción.

**Aprobado / No aprobado:** ☐

---

### 5.4 Flujo: Métricas agregadas por recepción

**Qué revisar:** Los campos `total_volume_m3`, `total_pieces`, `total_wood_cost_usd` en `stock.picking` se computan.

**Cómo revisarlo:**
```sql
SELECT name, total_volume_m3, total_pieces, total_wood_cost_usd
  FROM stock_picking
 WHERE reception_id IS NOT NULL
 LIMIT 5;
```

**Resultado esperado:** Valores numéricos (pueden ser 0 si no hay lotes con dimensiones completas, pero no NULL por error de cómputo).

**Aprobado / No aprobado:** ☐

---

## SECCIÓN 6 — VALIDACIÓN DE LOGS Y ERRORES

### 6.1 Log de Odoo: errores post-migración

**Qué revisar:** No hay errores nuevos en el log después de la migración.

**Cómo revisarlo:**
```bash
grep -iE "ERROR|CRITICAL|Traceback" /var/log/odoo/odoo.log \
  | grep -v "Expected error in test\|WARNING.*test" \
  | tail -30
```

**Resultado esperado:** Sin errores nuevos atribuibles a `madenat_lumber_core` o a `reception_id`.

**Señal de alarma:** Cualquier `Traceback` con `stock.lot`, `stock.picking`, `lumber_reception_id` o `reception_id` en el stack trace.

**Aprobado / No aprobado:** ☐

---

### 6.2 Log de PostgreSQL

**Qué revisar:** No hay errores de columna inexistente en los logs de PostgreSQL.

**Cómo revisarlo:**
```bash
grep -iE "lumber_reception_id|column.*does not exist" /var/log/postgresql/postgresql-*.log \
  | tail -20
```

**Resultado esperado:** **0 líneas** que mencionen `lumber_reception_id`.

**Señal de alarma:** Si PostgreSQL registró `column lumber_reception_id does not exist`, algo está intentando leer la columna legacy. Requiere investigación inmediata.

**Aprobado / No aprobado:** ☐

---

## SECCIÓN 7 — VALIDACIÓN DE AUSENCIA DE REFERENCIAS LEGACY

### 7.1 Búsqueda en código fuente: `lumber_reception_id`

**Qué revisar:** No quedan referencias productivas a `lumber_reception_id` en el código fuente (fuera de migrations históricas y backups).

**Cómo revisarlo:**
```bash
grep -r "lumber_reception_id" custom_addons/madenat_lumber_core/ \
  --include="*.py" --include="*.xml" --include="*.csv" \
  | grep -v "migrations/" \
  | grep -v "backups/" \
  | grep -v "_archive/"
```

**Resultado esperado:** **0 líneas**.

**Señal de alarma:** Cualquier resultado indica una referencia perdida que debe eliminarse antes de producción.

**Aprobado / No aprobado:** ☐

---

### 7.2 Búsqueda en base de datos: vistas materializadas o reglas

**Qué revisar:** PostgreSQL no tiene vistas o reglas que referencien `lumber_reception_id`.

**Cómo revisarlo:**
```sql
-- Vistas que mencionan lumber_reception_id
SELECT schemaname, viewname, definition
  FROM pg_views
 WHERE definition ILIKE '%lumber_reception_id%';

-- Reglas
SELECT rulename, tablename, definition
  FROM pg_rules
 WHERE definition ILIKE '%lumber_reception_id%';
```

**Resultado esperado:** **0 filas** en ambas consultas.

**Aprobado / No aprobado:** ☐

---

### 7.3 Verificación de `reception_id` como FK canónica en modelos Python

**Qué revisar:** Ambos modelos definen `reception_id` como campo y no tienen alias `lumber_reception_id`.

**Cómo revisarlo:**
```bash
grep -n "reception_id\|lumber_reception" \
  custom_addons/madenat_lumber_core/models/stock_lot.py \
  | grep -v "guia_processing_id\|_compute_reception_type\|_compute_reception_totals\|reception_type\|_check_reception_guia"
```

```bash
grep -n "reception_id\|lumber_reception" \
  custom_addons/madenat_lumber_core/models/stock_picking.py \
  | grep -v "lumber_lot_ids\|_compute_reception_totals\|reception_technical\|reception_financial\|reception_id.id"
```

**Resultado esperado:**
- `stock_lot.py`: línea ~200 define `reception_id = fields.Many2one(...)`
- `stock_picking.py`: línea ~15 define `reception_id = fields.Many2one(...)`
- Ninguna línea con `lumber_reception_id` como definición de campo.

**Aprobado / No aprobado:** ☐

---

## SECCIÓN 8 — CRITERIOS DE APROBACIÓN PARA PRODUCCIÓN

### 8.1 Condiciones obligatorias (todas deben cumplirse)

| # | Condición | Estado |
|---|-----------|--------|
| C1 | Secciones 1.1 y 1.2: columnas legacy eliminadas de ambas tablas | ☐ |
| C2 | Secciones 1.3 y 1.4: `reception_id` presente en ambas tablas | ☐ |
| C3 | Sección 1.7: sin constraints/índices residuales sobre columnas legacy | ☐ |
| C4 | Sección 2.1: versión del módulo = `18.0.5.3.0` | ☐ |
| C5 | Sección 2.2: sin errores de arranque | ☐ |
| C6 | Sección 3.1–3.5: todas las vistas cargan sin errores | ☐ |
| C7 | Sección 5.1–5.4: flujos operativos funcionales | ☐ |
| C8 | Sección 6.2: sin errores de columna inexistente en PostgreSQL | ☐ |
| C9 | Sección 7.1: sin referencias a `lumber_reception_id` en código productivo | ☐ |

**Regla:** Si **cualquiera** de C1–C9 falla, **NO promover a producción** sin resolver la causa raíz.

---

### 8.2 Condiciones de advertencia (no bloquean, pero requieren documentación)

| # | Condición | Acción |
|---|-----------|--------|
| W1 | Sección 1.5/1.6: FK huérfanas en `reception_id` | Documentar IDs afectados en el informe de staging |
| W2 | Sección 2.3: módulo dependiente en estado inesperado | Upgrade manual y re-verificar |
| W3 | Sección 6.1: errores no relacionados en log | Documentar y confirmar que son preexistentes |

---

### 8.3 Procedimiento de cierre

1. Ejecutar todas las verificaciones de las secciones 1 a 7.
2. Marcar cada ☐ como ✅ (aprobado) o ❌ (falló).
3. Si alguna verificación falla, documentar causa raíz y acción correctiva en este mismo documento (sección 9).
4. Si todas las condiciones C1–C9 están ✅, firmar la aprobación abajo.
5. Adjuntar logs relevantes y resultados de queries SQL como evidencia.

---

## SECCIÓN 9 — REGISTRO DE HALLAZGOS Y ACCIONES CORRECTIVAS

| # | Verificación | Hallazgo | Acción | Estado |
|---|-------------|----------|--------|--------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

---

## APROBACIÓN FINAL

| Rol | Nombre | Fecha | Firma |
|-----|--------|-------|-------|
| Auditor Técnico | | | |
| Líder de Desarrollo | | | |
| Operaciones (Staging) | | | |

---

**Documento generado:** 2026-06-16
**Próxima revisión:** Posterior a la ejecución de esta checklist en staging