# INFORME DE VALIDACIÓN POST-MIGRACIÓN — STAGING
## Migración 18.0.5.3.0 — Eliminación de columnas legacy `lumber_reception_id`

**Fecha:** 2026-06-16
**Tipo:** Informe de validación pre-producción (parcial — código fuente verificado, entorno staging pendiente)
**Ejecutor:** Auditoría técnica automatizada (Cline — sesión 2026-06-16)
**Migración:** `custom_addons/madenat_lumber_core/migrations/18.0.5.3.0/pre-migrate.py`

---

## RESUMEN EJECUTIVO

| Área | Estado | Detalle |
|------|--------|---------|
| Migración `pre-migrate.py` | ✅ CORRECTO | 2 `DROP COLUMN IF EXISTS` exactamente como se espera |
| `__manifest__.py` versión | ✅ ACTUALIZADO | `18.0.5.2.0` → `18.0.5.3.0` |
| `reception_id` en `stock_lot.py` | ✅ PRESENTE | Línea 200: `fields.Many2one('lumber.reception', ...)` |
| `reception_id` en `stock_picking.py` | ✅ PRESENTE | Línea 15: `fields.Many2one('lumber.reception', ...)` |
| `lumber_reception_id` en `stock_lot.py` | ✅ AUSENTE | 0 referencias |
| `lumber_reception_id` en `stock_picking.py` | ✅ AUSENTE | 0 referencias |
| `lumber_reception_id` en XML (todo `madenat_lumber_core`) | ✅ AUSENTE | 0 referencias |
| `lumber_reception_id` en CSV (todo `madenat_lumber_core`) | ✅ AUSENTE | 0 referencias |
| `_audit_trazabilidad.py` | ✅ ACTUALIZADO | Usa `reception_id`, no referencia legacy |
| `reception_service.py` | ✅ CANÓNICO | Usa `reception_id` (línea 32) |
| `lumber_reception_id` en `madenat_lumber_purchasing` | ⚠️ NOTA | Existe en `purchase.order` (tabla distinta, fuera de alcance) |
| DB PostgreSQL | 🔄 PENDIENTE | Entorno staging no accesible desde esta terminal |
| Arranque Odoo | 🔄 PENDIENTE | Requiere staging vivo |
| Vistas / Reportes / Flujos | 🔄 PENDIENTE | Requiere staging vivo |

---

## SECCIÓN 1 — VALIDACIÓN DE BASE DE DATOS

### 1.1 Confirmar eliminación de columna en `stock_lot`

**Resultado:** 🔄 PENDIENTE ENTORNO STAGING
**SQL a ejecutar:**
```sql
SELECT column_name
  FROM information_schema.columns
 WHERE table_schema = 'public'
   AND table_name = 'stock_lot'
   AND column_name = 'lumber_reception_id';
```
**Esperado:** 0 filas.

---

### 1.2 Confirmar eliminación de columna en `stock_picking`

**Resultado:** 🔄 PENDIENTE ENTORNO STAGING
**SQL a ejecutar:**
```sql
SELECT column_name
  FROM information_schema.columns
 WHERE table_schema = 'public'
   AND table_name = 'stock_picking'
   AND column_name = 'lumber_reception_id';
```
**Esperado:** 0 filas.

---

### 1.3 Confirmar que `reception_id` sigue presente en `stock_lot`

**Resultado:** ✅ VERIFICADO EN CÓDIGO FUENTE — `stock_lot.py` línea 200:
```python
reception_id = fields.Many2one(
    'lumber.reception',
    string='Recepción de Compra',
    ...
)
```
**SQL de confirmación en staging:**
```sql
SELECT column_name, data_type, is_nullable
  FROM information_schema.columns
 WHERE table_schema = 'public'
   AND table_name = 'stock_lot'
   AND column_name = 'reception_id';
```
**Esperado:** 1 fila con `data_type = 'integer'`.

---

### 1.4 Confirmar que `reception_id` sigue presente en `stock_picking`

**Resultado:** ✅ VERIFICADO EN CÓDIGO FUENTE — `stock_picking.py` línea 15:
```python
reception_id = fields.Many2one(
    'lumber.reception',
    'Recepción de Guía MADENAT',
    ...
)
```
**SQL de confirmación en staging:**
```sql
SELECT column_name, data_type, is_nullable
  FROM information_schema.columns
 WHERE table_schema = 'public'
   AND table_name = 'stock_picking'
   AND column_name = 'reception_id';
```
**Esperado:** 1 fila con `data_type = 'integer'`.

---

### 1.5 Integridad de datos: FK huérfanas en `stock_lot.reception_id`

**Resultado:** 🔄 PENDIENTE ENTORNO STAGING
**SQL a ejecutar:**
```sql
SELECT sl.id, sl.name, sl.reception_id
  FROM stock_lot sl
  LEFT JOIN lumber_reception lr ON lr.id = sl.reception_id
 WHERE sl.reception_id IS NOT NULL
   AND lr.id IS NULL;
```
**Esperado:** 0 filas.

---

### 1.6 Integridad de datos: FK huérfanas en `stock_picking.reception_id`

**Resultado:** 🔄 PENDIENTE ENTORNO STAGING
**SQL a ejecutar:**
```sql
SELECT sp.id, sp.name, sp.reception_id
  FROM stock_picking sp
  LEFT JOIN lumber_reception lr ON lr.id = sp.reception_id
 WHERE sp.reception_id IS NOT NULL
   AND lr.id IS NULL;
```
**Esperado:** 0 filas.

---

### 1.7 Constraints/índices residuales sobre columnas legacy

**Resultado:** 🔄 PENDIENTE ENTORNO STAGING
**SQL a ejecutar:**
```sql
SELECT conname, contype, conrelid::regclass AS table_name
  FROM pg_constraint
 WHERE conname ILIKE '%lumber_reception%';

SELECT indexname, tablename
  FROM pg_indexes
 WHERE indexname ILIKE '%lumber_reception%';
```
**Esperado:** 0 filas en ambas.

---

## SECCIÓN 2 — VALIDACIÓN DE ARRANQUE DEL MÓDULO

### 2.1 Versión registrada del módulo en `ir_module_module`

**Resultado:** 🔄 PENDIENTE ENTORNO STAGING
**SQL a ejecutar:**
```sql
SELECT name, latest_version, state
  FROM ir_module_module
 WHERE name = 'madenat_lumber_core';
```
**Esperado:** `latest_version = '18.0.5.3.0'`, `state = 'installed'`.

---

### 2.2 Errores al iniciar Odoo

**Resultado:** 🔄 PENDIENTE ENTORNO STAGING
**Comando a ejecutar (dentro del contenedor o en el host):**
```bash
grep -iE "lumber_reception_id|madenat_lumber_core.*error|madenat_lumber_core.*traceback" \
  /var/log/odoo/odoo.log | tail -50
```
**Esperado:** 0 líneas de error relevantes.

---

### 2.3 Módulos dependientes

**Resultado:** 🔄 PENDIENTE ENTORNO STAGING
**SQL a ejecutar:**
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
**Esperado:** Todos con `state = 'installed'`.

---

### 2.4 Migración en historial

**Resultado:** 🔄 PENDIENTE ENTORNO STAGING
**Comando a ejecutar:**
```bash
grep "Migration 18.0.5.3.0" /var/log/odoo/odoo.log
```
**Esperado:** Líneas con `dropped stock_lot.lumber_reception_id` y `dropped stock_picking.lumber_reception_id`.

---

## SECCIÓN 3 — VISTAS Y ACCIONES

### 3.1–3.5 Vistas de `stock.lot`, `stock.picking`, `lumber.reception`

**Resultado:** 🔄 PENDIENTE ENTORNO STAGING
**Validación:** Navegar en Odoo a cada vista y verificar que cargan sin traceback. Verificar que `reception_id` aparece en los formularios.

---

## SECCIÓN 4 — REPORTES

### 4.1 Reporte de inventario PDF

**Resultado:** 🔄 PENDIENTE ENTORNO STAGING

### 4.2 Trazabilidad

**Resultado:** ✅ VERIFICADO EN AUDITORÍA — `_audit_trazabilidad.py` v2.0 ya usa `reception_id` como FK canónica única (línea 11-12). No referencia `lumber_reception_id`.

**SQL de trazabilidad canónica (ejecutar en staging):**
```sql
SELECT sl.name AS lot_name, lr.name AS reception_name, sp.name AS picking_name
  FROM stock_lot sl
  JOIN lumber_reception lr ON lr.id = sl.reception_id
  LEFT JOIN stock_picking sp ON sp.reception_id = lr.id
 WHERE sl.reception_id IS NOT NULL
 LIMIT 10;
```
**Esperado:** Ejecuta sin error, devuelve datos si existen.

---

## SECCIÓN 5 — FLUJOS OPERATIVOS

### 5.1–5.4 Flujos de lotes, pickings, validación y métricas

**Resultado:** ✅ VERIFICADO EN CÓDIGO FUENTE:
- `reception_service.py` usa `reception_id` en todos sus métodos (línea 32: `('reception_id', '=', reception.id)`)
- `stock_picking.py` método `action_open_lumber_lots` usa `reception_id` (línea 236: `('reception_id', '=', self.reception_id.id)`)
- `stock_lot.py` usa `reception_id` como FK canónica (línea 200)
- `stock_picking.py` campo relacionado `lumber_lot_ids` es `related='reception_id.lot_ids'` (línea 23-26)
- Métricas agregadas en `stock_picking` computan desde `lumber_lot_ids` → `reception_id` → lotes

🔄 **PENDIENTE ENTORNO STAGING:** Confirmar funcionalidad con pruebas manuales/API.

---

## SECCIÓN 6 — LOGS Y ERRORES

### 6.1 Log de Odoo

**Resultado:** 🔄 PENDIENTE ENTORNO STAGING

### 6.2 Log de PostgreSQL

**Resultado:** 🔄 PENDIENTE ENTORNO STAGING
**Comando:**
```bash
grep -iE "lumber_reception_id|column.*does not exist" /var/log/postgresql/postgresql-*.log | tail -20
```
**Esperado:** 0 líneas.

---

## SECCIÓN 7 — AUSENCIA DE REFERENCIAS LEGACY

### 7.1 Búsqueda en código fuente: `lumber_reception_id`

**Resultado:** ✅ VERIFICADO — Búsqueda exhaustiva en todos los archivos `.py`, `.xml`, `.csv` del proyecto, excluyendo `backups/`, `_archive/`, `RAW/`, `LEGADO/`, `.git/` y `migrations/18.0.5.*`:

| Ubicación | Archivo | ¿Referencia productiva? |
|-----------|---------|------------------------|
| `madenat_lumber_core/models/stock_lot.py` | — | ❌ 0 referencias |
| `madenat_lumber_core/models/stock_picking.py` | — | ❌ 0 referencias |
| `madenat_lumber_core/models/reception_service.py` | — | ❌ 0 referencias |
| `madenat_lumber_core/views/` | — | ❌ 0 referencias |
| `madenat_lumber_core/reports/` | — | ❌ 0 referencias |
| `madenat_lumber_core/wizard/` | — | ❌ 0 referencias |
| `madenat_lumber_reports/` | — | ❌ 0 referencias |
| `madenat_lumber_costing/` | — | ❌ 0 referencias |
| `madenat_lumber_logistics/` | — | ❌ 0 referencias |
| `madenat_lumber_billing/` | — | ❌ 0 referencias |
| `madenat_lumber_shipping_core/` | — | ❌ 0 referencias |
| `madenat_lumber_purchasing/models/purchase_order.py` | `purchase.order` | ⚠️ LEGACY (ver sección 7.4) |
| `_audit_trazabilidad.py` | script auditoría | ✅ v2.0 actualizado, no usa legacy |
| `_audit_db_check.py` | script auditoría | ✅ No referencia legacy |
| `run_audit_trazabilidad.py` | wrapper | ✅ No referencia legacy |

**Conclusión:** **Cero referencias productivas** a `lumber_reception_id` en `stock.lot` y `stock.picking` fuera de migrations. Los únicos usos de `lumber_reception_id` y `lumber_reception_ids` están en `purchase.order` de `madenat_lumber_purchasing`, que es una tabla completamente distinta y no es objetivo de esta migración.

✅ **Aprobado.**

---

### 7.2 Vistas materializadas o reglas en PostgreSQL

**Resultado:** 🔄 PENDIENTE ENTORNO STAGING
**SQL:**
```sql
SELECT schemaname, viewname FROM pg_views WHERE definition ILIKE '%lumber_reception_id%';
SELECT rulename, tablename FROM pg_rules WHERE definition ILIKE '%lumber_reception_id%';
```
**Esperado:** 0 filas.

---

### 7.3 `reception_id` como FK canónica en modelos Python

**Resultado:** ✅ VERIFICADO:

| Modelo | Archivo | Línea | Definición |
|--------|---------|-------|-----------|
| `stock.lot` | `stock_lot.py` | 200 | `reception_id = fields.Many2one('lumber.reception', ...)` |
| `stock.picking` | `stock_picking.py` | 15 | `reception_id = fields.Many2one('lumber.reception', ...)` |

Ninguno define `lumber_reception_id` como campo. ✅ **Aprobado.**

---

### 7.4 HALLAZGO: Campos `lumber_reception_id` y `lumber_reception_ids` en `purchase.order` (madenat_lumber_purchasing)

**Archivo:** `custom_addons/madenat_lumber_purchasing/models/purchase_order.py`
**Líneas:** 35-46

```python
# LEGACY: Mantener compatibilidad
lumber_reception_ids = fields.One2many(
    'lumber.reception',
    'purchase_id',
    string='Recepciones de Guía (Legacy)',
    readonly=True
)

lumber_reception_id = fields.Many2one(
    'lumber.reception',
    'Recepción Asociada (Legacy)',
    readonly=True
)
```

**Análisis:**
- Estos campos están en la tabla `purchase_order`, **NO** en `stock_lot` ni `stock_picking`.
- Usan `purchase_id` como inverse (One2many) y apuntan a `lumber.reception`, no a `stock.lot`.
- El módulo también tiene el campo canónico `reception_ids` (línea 20-26) con la misma definición.
- Están explícitamente marcados como `LEGACY` en comentarios y `string`.

**Impacto en esta migración: NINGUNO.** La migración 18.0.5.3.0 solo ejecuta `DROP COLUMN IF EXISTS` en `stock_lot` y `stock_picking`. Estas tablas no se tocan.

**Riesgo:** Estos campos legacy en `purchase.order` generan columnas físicas en PostgreSQL (`purchase_order.lumber_reception_id`). Si en el futuro se eliminan del modelo Python, requerirán su propia migración de limpieza. No son parte del alcance actual.

**Dictamen:** ⚠️ **FUERA DE ALCANCE.** Documentar para backlog, no para esta release. No bloquea la promoción a producción.

---

## SECCIÓN 8 — CRITERIOS DE APROBACIÓN PARA PRODUCCIÓN

### 8.1 Condiciones obligatorias

| # | Condición | Estado | Evidencia |
|---|-----------|--------|-----------|
| C1 | Columnas legacy eliminadas de `stock_lot` y `stock_picking` | 🔄 PENDIENTE STAGING | Requiere ejecutar SQL 1.1 y 1.2 |
| C2 | `reception_id` presente en ambas tablas | ✅ CÓDIGO | `stock_lot.py:200`, `stock_picking.py:15` |
| C3 | Sin constraints/índices residuales sobre columnas legacy | 🔄 PENDIENTE STAGING | Requiere SQL 1.7 |
| C4 | Versión del módulo = `18.0.5.3.0` | ✅ CÓDIGO | `__manifest__.py` línea 4 |
| C5 | Sin errores de arranque | 🔄 PENDIENTE STAGING | Requiere logs de Odoo |
| C6 | Todas las vistas cargan sin errores | 🔄 PENDIENTE STAGING | Requiere navegación Odoo |
| C7 | Flujos operativos funcionales | ✅ CÓDIGO | `reception_service.py`, `stock_picking.py` verificados |
| C8 | Sin errores de columna inexistente en PostgreSQL | 🔄 PENDIENTE STAGING | Requiere logs PostgreSQL |
| C9 | Sin referencias a `lumber_reception_id` en código productivo | ✅ VERIFICADO | 0 referencias en `stock_lot`, `stock_picking` y dependientes |

---

### 8.2 Condiciones de advertencia

| # | Condición | Estado |
|---|-----------|--------|
| W1 | FK huérfanas en `reception_id` | 🔄 PENDIENTE STAGING |
| W2 | Módulo dependiente en estado inesperado | 🔄 PENDIENTE STAGING |
| W3 | Errores no relacionados en log | 🔄 PENDIENTE STAGING |

---

## SECCIÓN 9 — REGISTRO DE HALLAZGOS Y ACCIONES CORRECTIVAS

| # | Verificación | Hallazgo | Acción | Estado |
|---|-------------|----------|--------|--------|
| 1 | 7.1 | `lumber_reception_id` y `lumber_reception_ids` existen en `purchase.order` (madenat_lumber_purchasing) | Documentado — fuera de alcance de esta migración. Tabla distinta. No bloquea. | ⚠️ BACKLOG |
| 2 | 7.1 | `_audit_trazabilidad.py` v2.0 ya actualizado a `reception_id` | Ninguna requerida | ✅ |

---

## SECCIÓN 10 — DICTAMEN FINAL

### Estado actual: CONDICIONAL — PENDIENTE VERIFICACIÓN EN STAGING VIVO

**Lo que está confirmado (código fuente):**
- La migración `pre-migrate.py` es correcta: solo 2 `DROP COLUMN IF EXISTS`.
- `reception_id` es la FK canónica única en `stock.lot` y `stock.picking`.
- No hay referencias productivas a `lumber_reception_id` en `stock.lot`, `stock.picking` ni en ningún modelo/view/reporte/wizard del ecosistema `madenat_lumber_core`.
- Los scripts de auditoría (`_audit_trazabilidad.py`, `_audit_db_check.py`) ya están actualizados.
- Los servicios operativos (`reception_service.py`) usan `reception_id` exclusivamente.

**Lo que falta confirmar (entorno staging vivo):**
- Que PostgreSQL efectivamente eliminó las columnas (C1).
- Que no hay constraints/índices residuales (C3).
- Que Odoo arranca sin errores y registra la versión 18.0.5.3.0 (C4, C5).
- Que vistas, reportes y flujos operativos funcionan (C6, C7 runtime).
- Que no hay errores de columna inexistente en logs PostgreSQL (C8).

### Recomendación

**APROBADO PARA STAGING** — Ejecutar la migración en el entorno de staging y completar las verificaciones C1, C3, C4, C5, C6, C8 pendientes usando el checklist `CHECKLIST_POST_MIGRACION_18_0_5_3_0.md`.

**NO PROMOVER A PRODUCCIÓN** hasta que todas las condiciones C1–C9 estén verificadas como ✅ en staging.

### Hallazgo de backlog

El módulo `madenat_lumber_purchasing` mantiene campos legacy `lumber_reception_id` y `lumber_reception_ids` en `purchase.order` que están duplicando funcionalidad con el campo canónico `reception_ids`. Se recomienda planificar su limpieza en una release futura, con su propia migración.

---

**Documento generado:** 2026-06-16
**Ejecutado por:** Auditoría técnica Cline — sesión 2026-06-16
**Próximo paso:** Completar verificaciones C1–C9 en staging vivo y actualizar este informe.