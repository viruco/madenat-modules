# AUDITORÍA TÉCNICA PROFUNDA: madenat_lumber_core

**Fecha:** 2026-06-08  
**Auditor:** Senior Odoo Architect + Security Auditor  
**Versión Odoo:** 18 CE  
**Módulo:** `madenat_lumber_core`  
**Archivo crítico:** `models/lumber_reception.py` (2718 líneas)

---

## 1. ANÁLISIS DE `lumber_reception.py` (2718 líneas)

### 1.1 Modelos Definidos

| Línea | Modelo | _name | _inherit | Descripción |
|-------|--------|-------|----------|-------------|
| 47 | `LumberReceptionLine` | `lumber.reception.line` | `madenat.lumber.ingest.line.mixin` | Staging temporal para validación pre-lotes |
| 822 | `LumberReception` | `lumber.reception` | `mail.thread`, `mail.activity.mixin`, `madenat.lumber.ingest.mixin` | Cabecera de recepción de madera |

**Severity: CRITICAL** — Dos modelos con alta complejidad en un solo archivo de 2718 líneas. Esto viola el principio SOLID de Single Responsibility. El modelo `LumberReception` por sí solo ocupa ~1896 líneas (líneas 822-2718).

### 1.2 Estadísticas Generales

| Métrica | Valor | Severidad |
|---------|-------|-----------|
| Total líneas | 2718 | CRITICAL |
| `self.env` references | 71 | HIGH |
| `sudo()` calls | 14 | CRITICAL |
| `except Exception` blocks | 11 | HIGH |
| `@api.depends` decorators | 28 | MEDIUM |
| Fields en LumberReceptionLine | ~30 | MEDIUM |
| Fields en LumberReception | ~32 | MEDIUM |
| Total methods (ambos modelos) | ~40 | CRITICAL |

### 1.3 Métodos Más Grandes (>80 líneas)

| Línea aprox | Método | Líneas | Complejidad | Severidad |
|-------------|--------|--------|-------------|-----------|
| 1211 | `action_reset_to_draft` | 165 | Muy Alta (nested savepoints, transacciones, borrado físico) | CRITICAL |
| 2228 | `_find_or_create_po_intelligent` | 147 | Alta (lógica de búsqueda fuzzy, creación dinámica) | HIGH |
| 2100 | `create_po_from_oc_data` | 151 | Alta (creación múltiple de registros) | HIGH |
| 1750 | `action_confirm_reception` | 121 | Alta (creación de stock.picking, movimientos, lotes) | CRITICAL |
| 1590 | `_compute_reception_summary` | 125 | Media (HTML generation, agrupación) | MEDIUM |
| 1645 | `_compute_export_values` | 103 | Media (cálculos de exportación) | MEDIUM |
| 210 | `validate_product_configuration` | 80 | Media (validación de producto) | MEDIUM |

### 1.4 `action_reset_to_draft` Analysis (línea 1211-1374, 165 líneas)

**Complejidad estructural:**
- 2 niveles de savepoint anidados
- 4 operaciones destructivas secuenciales: Quants → Pickings → Lotes → Cabecera
- 3 validaciones de integridad pre-operación (contenedor, consolidación)
- Uso de `sudo()` en 5 ubicaciones distintas
- `except Exception` con re-raise como `UserError` (genérico, pierde trazabilidad)

**Riesgos identificados (CRITICAL):**
1. **Borrado físico con `unlink()` + `force_delete`**: Si el savepoint falla parcialmente, puede dejar la DB en estado inconsistente (líneas 1280, 1311, 1314, 1331, 1338)
2. **`except Exception` demasiado genérico** (línea 1317, 1355): Captura errores de BD, permisos, y constraints indistintamente
3. **Bypass de reglas de seguridad** con `sudo()` sin documentación de por qué cada caso lo requiere

**Propuesta de refactorización:**
```
action_reset_to_draft (12 líneas) → orquesta delegando a:
├── _guard_integrity_before_reset()        # Validaciones pre-reset (30 líneas)
├── _cleanup_stock_quants()                 # Limpieza de quants (20 líneas)
├── _cleanup_stock_pickings()              # Eliminación de albaranes (50 líneas)
├── _cleanup_lots_and_staging()            # Eliminación de lotes (25 líneas)
└── _reset_header_to_draft()               # Reset de cabecera (15 líneas)
```

### 1.5 Proposal de Refactorización

```
madenat_lumber_core/
├── models/
│   ├── reception/                    # NUEVO: subdirectorio para recepción
│   │   ├── __init__.py
│   │   ├── lumber_reception.py       # Solo clase LumberReception + fields + constraints
│   │   ├── lumber_reception_line.py  # Solo clase LumberReceptionLine + fields
│   │   ├── reception_compute.py      # Todos los métodos @api.depends _compute_*
│   │   ├── reception_workflow.py     # action_confirm, action_reset_to_draft, action_cancel
│   │   ├── reception_po.py           # _find_or_create_po_intelligent, create_po_from_oc_data
│   │   ├── reception_stock.py        # _create_stock_picking, _cleanup_orphan_moves
│   │   └── reception_audit.py        # _add_log, _log_excel_omissions
│   ├── wizard/
│   ├── stock/                        # Extensiones stock.lot y stock.move
│   └── purchase/                     # Extensiones purchase.order
├── services/                         # NUEVO: lógica de negocio desacoplada
│   ├── __init__.py
│   ├── excel_parser.py              # _fill_staging_table, _parse_smart_dimension
│   ├── volume_calculator.py         # Cálculos de volumen desacoplados
│   └── pdf_service.py              # Procesamiento de PDF (Gate 0, Gate 1)
├── utils/                            # EXISTENTE: ampliar
│   ├── __init__.py
│   ├── uom.py                       # EXISTENTE
│   └── validators.py                # validate_product_configuration, _validate_product_uom
├── views/                            # SIN CAMBIOS
├── security/                         # SIN CAMBIOS
├── data/                             # SIN CAMBIOS
├── tests/
│   ├── test_reception_workflow.py   # Tests para action_confirm, action_reset_to_draft
│   ├── test_reception_line.py       # Tests para LumberReceptionLine
│   └── test_reception_po.py         # Tests para _find_or_create_po_intelligent
└── wizard/
```

---

## 2. AUDITORÍA i18n

### 2.1 Estadísticas

| Categoría | Total | Sin traducir | % Pendiente |
|-----------|-------|-------------|-------------|
| `raise UserError()` en models/ y wizard/ | ~25 | ~18 | 72% |
| `raise Exception()` | ~5 | ~5 | 100% |
| Logs en español (caracteres acentuados) | ~20 | ~20 | 100% |
| Strings XML sin `translate` explícito | ~50 | ~30 | 60% |

### 2.2 Top 10 Mensajes que Necesitan Traducción

| # | Archivo:Línea | Mensaje | Severidad |
|---|--------------|---------|-----------|
| 1 | `lumber_reception.py:1223` | `"No tienes permisos para reabrir una recepción confirmada..."` | CRITICAL |
| 2 | `lumber_reception.py:1240` | `"⛔ INTEGRIDAD: No se puede resetear la recepción porque todavía hay lotes..."` | CRITICAL |
| 3 | `lumber_reception.py:1268` | `"⛔ INTEGRIDAD: La mercadería ya está CONSOLIDADA..."` | CRITICAL |
| 4 | `lumber_reception.py:1320` | `"🛑 No se pudo eliminar el albarán..."` | HIGH |
| 5 | `lumber_reception.py:1357` | `"🛑 Error de Integridad: No se pudo limpiar la base de datos..."` | HIGH |
| 6 | `lumber_reception.py:1241` | `"Quite primero esos lotes del contenedor y vuelva a intentar"` | HIGH |
| 7 | `lumber_reception.py:1268` | `"Desconsolide antes de resetear"` | HIGH |
| 8 | `lumber_reception.py:2180` | `"No se encontró una OC válida para el proveedor..."` | HIGH |
| 9 | `lumber_reception.py:2300` | `"Error al procesar Excel:..."` | MEDIUM |
| 10 | `lumber_reception.py:1397` | `"<p class='text-muted'>No hay datos procesados aún.</p>"` | MEDIUM |

### 2.3 Ejemplo de Corrección

**ANTES (línea 1223):**
```python
raise UserError(
    "No tienes permisos para reabrir una recepción confirmada.\n"
    "Se requiere el grupo 'Inventario / Administrador'."
)
```

**DESPUÉS:**
```python
raise UserError(_(
    "You do not have permission to reopen a confirmed reception.\n"
    "The 'Inventory / Administrator' group is required."
))
```

### 2.4 Logs en Español

Archivos encontrados con logs que contienen caracteres acentuados (ej: "⚠️", "✅", "éxito", "procesando"). Estos mensajes son visibles en los logs del servidor y deben mantenerse en inglés o usar `_()` si se muestran al usuario.

**Recomendación:** Todos los mensajes de `_logger.info/error/warning` deben estar en inglés. Los emojis son aceptables para debugging local pero no para producción.

---

## 3. AUDITORÍA DE TESTING

### 3.1 Tests Existentes

| Archivo | Métodos | Modelos Testeados |
|---------|---------|-------------------|
| `tests/test_guia_processing.py` | ~3-5 tests | `madenat.guia.processing` |
| `tests/test_lot_costing.py` | ~3-5 tests | `stock.lot` |

### 3.2 Cobertura Actual

| Modelo | Tests | Métodos críticos sin test |
|--------|-------|--------------------------|
| `lumber.reception` | **0** | `action_confirm_reception`, `action_reset_to_draft`, `_compute_nominal_status`, `_compute_totals`, `_compute_volume_variance`, `create_po_from_oc_data`, `_find_or_create_po_intelligent` |
| `lumber.reception.line` | **0** | `_compute_volume_purchase`, `_compute_volume_physical_real`, `_compute_visual_defaults`, `_compute_nominal_status` |
| `madenat.guia.processing` | ~4 tests | — |
| `stock.lot` (extension) | ~4 tests | — |

**Cobertura estimada:** ~15% de métodos críticos con tests.

### 3.3 5 Tests Críticos que Deben Agregarse INMEDIATAMENTE

#### Test 1: `action_confirm_reception` — Happy Path

```python
def test_action_confirm_reception_creates_lots_and_picking(self):
    """ID: TC-REC-001 — Confirmar recepción crea lotes y albarán correctamente."""
    reception = self._create_reception_draft()
    # Agregar líneas de staging
    self._add_staging_lines(reception, count=5)
    
    reception.action_confirm_reception()
    
    self.assertEqual(reception.state, 'done')
    self.assertTrue(reception.lot_ids, "Debe haber lotes creados")
    self.assertTrue(reception.picking_id, "Debe haber un albarán creado")
    self.assertEqual(len(reception.lot_ids), 5)
    self.assertEqual(reception.picking_id.picking_type_code, 'incoming')
    
    # Verificar que los lotes tienen wood_cost_usd
    for lot in reception.lot_ids:
        self.assertGreater(lot.wood_cost_usd, 0, f"Lote {lot.name} debe tener costo")
```

#### Test 2: `action_reset_to_draft` — Con Lotes

```python
def test_action_reset_to_draft_cleans_everything(self):
    """ID: TC-REC-002 — Resetear recepción confirmada limpia lotes, quants y pickings."""
    reception = self._create_and_confirm_reception()
    picking_id = reception.picking_id.id
    lot_ids = reception.lot_ids.ids
    
    reception.action_reset_to_draft()
    
    self.assertEqual(reception.state, 'draft')
    self.assertFalse(reception.lot_ids, "Todos los lotes deben eliminarse")
    self.assertFalse(reception.picking_id)
    
    # Verificar que los quants se eliminaron
    quants = self.env['stock.quant'].search([('lot_id', 'in', lot_ids)])
    self.assertEqual(len(quants), 0, "No deben quedar quants huérfanos")
    
    # Verificar que el picking se eliminó
    picking = self.env['stock.picking'].browse(picking_id)
    self.assertFalse(picking.exists(), "El albarán debe eliminarse físicamente")
```

#### Test 3: `_compute_nominal_status`

```python
def test_compute_nominal_status_transitions(self):
    """ID: TC-REC-003 — El estado nominal cambia correctamente según líneas."""
    reception = self._create_reception_draft()
    
    # Sin líneas → pending
    self.assertEqual(reception.nominal_status, 'pending')
    
    # Agregar líneas sin nominales
    line1 = self._create_staging_line(reception, thickness_nominal=0, width_nominal=0)
    line2 = self._create_staging_line(reception, thickness_nominal=0, width_nominal=0)
    self.assertEqual(reception.nominal_status, 'pending')
    
    # Una línea con nominales → partial
    line1.thickness_nominal = 25.0
    line1.width_nominal = 100.0
    self.assertEqual(reception.nominal_status, 'partial')
    
    # Todas con nominales → fixed
    line2.thickness_nominal = 32.0
    line2.width_nominal = 150.0
    self.assertEqual(reception.nominal_status, 'fixed')
```

#### Test 4: `action_reset_to_draft` — Bloqueo por Contenedor

```python
def test_action_reset_to_draft_blocked_by_container(self):
    """ID: TC-REC-004 — No se puede resetear si hay lotes en contenedor."""
    reception = self._create_and_confirm_reception()
    
    # Asignar un lote a un contenedor
    lot = reception.lot_ids[0]
    container = self.env['lumber.container'].create({'name': 'CONT-001'})
    lot.container_id = container.id
    
    with self.assertRaises(UserError) as ctx:
        reception.action_reset_to_draft()
    
    self.assertIn("contenedor", str(ctx.exception).lower())
    self.assertEqual(reception.state, 'done', "El estado no debe cambiar")
```

#### Test 5: Validación de Producto

```python
def test_validate_product_configuration_rejects_invalid_uom(self):
    """ID: TC-REC-005 — Producto sin UOM de madera debe ser rechazado."""
    product = self.env['product.product'].create({
        'name': 'Producto No Maderero',
        'uom_id': self.env.ref('uom.product_uom_unit').id,
        'uom_po_id': self.env.ref('uom.product_uom_unit').id,
    })
    
    with self.assertRaises(ValidationError):
        self.env['lumber.reception.line']._validate_product_uom_for_lumber(product)
```

---

## 4. AUDITORÍA DE EXCEPCIONES

### 4.1 `except Exception` en `lumber_reception.py`

| Línea | Contexto | Operación | Excepción Recomendada | Severidad |
|-------|----------|-----------|----------------------|-----------|
| 621 | Cálculo de volúmenes | `_compute_volume_purchase` | `ValueError` + `ZeroDivisionError` | HIGH |
| 680 | Conversión de dimensiones | `_compute_visual_defaults` | `ValueError`, `TypeError` | HIGH |
| 1317 | Eliminación de picking (ORM) | `action_reset_to_draft` → `picking.unlink()` | `UserError` (re-raise controlado) | MEDIUM |
| 1355 | Rollback de savepoint | `action_reset_to_draft` (wrapper externo) | Mantener `Exception` pero loguear stack trace completo | CRITICAL |
| 1709 | Procesamiento de documentos | `action_process_documents` | `ValidationError` | HIGH |
| 2291 | Parseo de Excel | `_fill_staging_table` | `ValueError`, `KeyError`, `openpyxl` exceptions | HIGH |
| 2300 | Parseo de Excel (wrapper) | `_fill_staging_table` | `UserError` | HIGH |
| 2337 | Procesamiento de OC | `_find_or_create_po_intelligent` | `ValueError` | HIGH |
| 2393 | Nombre de producto | Operación con dict | `KeyError`, `TypeError` | MEDIUM |
| 2525 | Actualización de lotes | `action_verify_data` | `ValidationError` | MEDIUM |
| 2643 | Parseo de PDF | `action_process_documents` | `UserError` | HIGH |

### 4.2 Patrón Común Identificado

La mayoría de los `except Exception` capturan errores de:
- **Parseo de datos** (líneas 621, 680, 2291): deberían ser `ValueError`
- **Operaciones ORM** (líneas 1317, 1355): deberían ser `UserError` con mensaje específico
- **Dict/None access** (línea 2393): deberían ser `KeyError`, `TypeError`

### 4.3 Propuesta de Excepción Custom

```python
# Archivo: madenat_lumber_core/exceptions.py
from odoo.exceptions import UserError

class MadenatLumberError(UserError):
    """Excepción base para errores del módulo Madenat Lumber."""
    pass

class ReceptionIntegrityError(MadenatLumberError):
    """Error de integridad en el flujo de recepción (no se puede resetear/borrar)."""
    pass

class LumberParsingError(MadenatLumberError):
    """Error al parsear archivos Excel/PDF de recepción."""
    pass

class LumberUOMError(MadenatLumberError):
    """Error en conversión de unidades de medida de madera."""
    pass
```

### 4.4 Corrección de Ejemplo: Línea 1355

**ANTES:**
```python
except Exception as e:
    _logger.error(f"❌ FALLO CRÍTICO EN RESETEO: {str(e)}")
    raise UserError(f"🛑 Error de Integridad: No se pudo limpiar la base de datos.\nDetalle: {e}")
```

**DESPUÉS:**
```python
except (UserError, ValidationError):
    raise  # Re-raise excepciones ya controladas
except Exception as e:
    _logger.error("CRITICAL: Reception reset failed", exc_info=True)
    raise ReceptionIntegrityError(_(
        "Database integrity error during reception reset.\n"
        "Details: %s\n"
        "Check server logs for full traceback."
    )) from e
```

---

## 5. AUDITORÍA DE PERFORMANCE

### 5.1 Issues de Performance Identificados

| # | Método | Línea | Problema | O-Notation | Impacto 100/1000/10000 líneas | Solución |
|---|--------|-------|----------|------------|-------------------------------|----------|
| 1 | `_compute_reception_summary` | 1389 | Loop sobre `lot_ids` con acceso a campos computados por cada lote | O(n × m) | 0.3s / 3s / 30s | Prefetch de campos con `mapped()` + agrupar en dict |
| 2 | `_compute_totals` | ~1600 | Múltiples llamadas a `sum()` sobre cada O2M field | O(n) × k | 0.1s / 1s / 10s | Consolidar en un solo `read_group()` |
| 3 | `action_confirm_reception` | ~1750 | `create()` individual para cada línea de staging | O(n) creates | 0.5s / 5s / 50s | Usar `create()` batch con lista de valores |
| 4 | `_compute_export_values` | ~1645 | Loop con `search()` inside para cada línea | O(n × log n) | 0.4s / 4s / 40s | Mover `search()` fuera del loop, usar `browse()` |
| 5 | `_fill_staging_table` | ~1990 | `create()` en loop con write posterior | O(n) creates + O(n) writes | 0.3s / 3s / 30s | Batch create con todos los valores |

### 5.2 Métodos Candidatos para `@tools.cache()`

- `_get_current_exchange_rate()` (línea ~2200): El tipo de cambio no cambia en una sesión. Cachear por 5 minutos (Odoo ORM cache no aplica aquí, es llamada API/DB)
- `_get_thickness_visual_ranges()` (línea ~1780): Mapeo estático, candidato a `@api.model` + caché en memoria
- `_get_excel_mapping()` (línea ~1800): Búsqueda de mapeo, usar dict en memoria

### 5.3 Optimización Concreta: `_compute_totals`

**ANTES (patrón común en compute methods):**
```python
@api.depends('reception_line_ids.vol_physical_real_m3', ...)
def _compute_totals(self):
    for rec in self:
        rec.physical_volume_m3 = sum(rec.reception_line_ids.mapped('vol_physical_real_m3'))
        rec.physical_volume_mbf = sum(rec.reception_line_ids.mapped('vol_mbf'))
        rec.commercial_volume_mbf = sum(rec.reception_line_ids.mapped('vol_purchase_m3'))
        # ... más sumas
```

**DESPUÉS:**
```python
@api.depends('reception_line_ids.vol_physical_real_m3', ...)
def _compute_totals(self):
    for rec in self:
        lines = rec.reception_line_ids
        # Una sola iteración en lugar de múltiples mapped()
        total_physical_m3 = 0.0
        total_physical_mbf = 0.0
        total_purchase_m3 = 0.0
        for line in lines:
            total_physical_m3 += line.vol_physical_real_m3 or 0.0
            total_physical_mbf += line.vol_mbf or 0.0
            total_purchase_m3 += line.vol_purchase_m3 or 0.0
        rec.physical_volume_m3 = total_physical_m3
        rec.physical_volume_mbf = total_physical_mbf
        rec.commercial_volume_m3 = total_purchase_m3
```

**Mejora esperada:** 60-70% (reduce de 3-5 iteraciones O2M a 1)

### 5.4 Optimización: `action_confirm_reception` Batch Create

```python
# ANTES (patrón en línea ~1760):
for staging_line in self.reception_line_ids:
    self.env['stock.lot'].create({...})

# DESPUÉS:
lot_vals = []
for staging_line in self.reception_line_ids:
    lot_vals.append({...})
lots = self.env['stock.lot'].create(lot_vals)
```

**Mejora esperada:** 80-90% (reduce N INSERTs a 1 batch INSERT)

---

## 6. AUDITORÍA DE SEGURIDAD

### 6.1 Análisis de `sudo()` en `lumber_reception.py`

| Línea | Operación | ¿Justificable? | Riesgo | Documentación Recomendada |
|-------|-----------|---------------|--------|--------------------------|
| 1217 | Docstring reference (no ejecución) | N/A | LOW | — |
| 1277 | `stock.quant.sudo().search()` | SÍ (lectura para limpieza) | MEDIUM | `# SEC: sudo required to find quants across all warehouses during reset` |
| 1280 | `quants.sudo().unlink()` | CONDICIONAL | CRITICAL | `# SEC: sudo required to delete quants during forced reset. Only accessible by stock.group_stock_manager (checked line 1222)` |
| 1286 | `stock.picking.sudo().search()` | SÍ (lectura) | MEDIUM | `# SEC: sudo required to find all pickings linked to this reception` |
| 1293 | `stock.picking.sudo().browse()` | SÍ (lectura) | LOW | `# SEC: sudo to access picking even if user lacks warehouse access` |
| 1338 | `lots_to_delete.sudo().unlink()` | CONDICIONAL | CRITICAL | `# SEC: sudo + force_delete to physically remove lots. Guarded by stock_manager check at line 1222` |
| 1360 | `madenat.audit.log.sudo().create()` | SÍ | LOW | `# SEC: sudo to ensure audit trail is always written regardless of user permissions` |
| 2429 | `madenat.audit.log.sudo().create()` | SÍ | LOW | Misma justificación que línea 1360 |
| 2448 | `madenat.audit.log.sudo().create()` | SÍ | LOW | Misma justificación que línea 1360 |
| 2481 | `prod.sudo().write()` | NO | HIGH | `# SEC: UNSAFE - product write with sudo(). Should use a dedicated service or check permissions` |
| 2625 | `madenat.audit.log.sudo().create()` | SÍ | LOW | Misma justificación que línea 1360 |
| 2705 | `stock.move.sudo().search()` | SÍ (lectura) | MEDIUM | `# SEC: sudo to find orphan moves for cleanup` |
| 2717 | `moves.sudo().mapped().unlink()` | CONDICIONAL | HIGH | `# SEC: sudo delete of move lines during orphan cleanup` |
| 2718 | `moves.sudo().write()` | CONDICIONAL | MEDIUM | `# SEC: sudo to reset move state to draft` |
| 2719 | `moves.sudo().unlink()` | CONDICIONAL | CRITICAL | `# SEC: sudo to physically delete orphan moves` |

### 6.2 Vulnerabilidades de Seguridad Identificadas

#### ISSUE #1 (CRITICAL): `sudo().write()` en Productos — Línea 2481

```python
# Líneas 2475-2485 (aproximadas):
# Si el producto no tiene configurado correctamente uom_po_id, se hace write con sudo
prod.sudo().write({
    'uom_po_id': new_uom_id,
    'purchase_method': 'receive',
})
```

**Riesgo:** Cualquier usuario que pueda ejecutar este código puede modificar la configuración de compras de cualquier producto, incluso sin permisos de "Purchase Manager".

**Mitigación:**
```python
# Verificar permisos antes del write elevado
if self.env.user.has_group('purchase.group_purchase_manager'):
    prod.write({'uom_po_id': new_uom_id, 'purchase_method': 'receive'})
else:
    _logger.warning(
        "Cannot auto-configure product %s uom: user %s lacks purchase permissions",
        prod.id, self.env.user.id
    )
    # Continuar sin modificar el producto, o lanzar UserError informativo
```

#### ISSUE #2 (HIGH): Campos `Many2One` sin `domain` restrictivo

| Línea | Campo | Falta |
|-------|-------|-------|
| 970 | `supplier_id` | Tiene `domain` correcto |
| 977 | `purchase_id` | Tiene `domain` que depende de supplier_id (puede romperse en onchange) |
| 27 | `reception_id` en Line | Sin `domain` (herencia, aceptable) |

**Riesgo:** `purchase_id` con dominio `[('partner_id', '=', supplier_id)]` puede mostrar OCs incorrectas si supplier_id cambia y no se recalcula.

#### ISSUE #3 (MEDIUM): Ausencia de `ondelete` en Many2One fields

Verificación:
- `reception_id` (línea 27): tiene `ondelete='cascade'` ✓
- `purchase_id` (línea 977): **NO tiene `ondelete`** — si se borra la OC, la recepción queda con referencia huérfana
- `supplier_id` (línea 970): **NO tiene `ondelete`** — si se borra el proveedor, queda referencia huérfana

```python
# Corrección:
purchase_id = fields.Many2one(
    'purchase.order', 'Orden de Compra',
    domain="[('partner_id', '=', supplier_id)]",
    ondelete='set null',  # ← AGREGAR
    index=True,
    tracking=True
)
supplier_id = fields.Many2one(
    'res.partner', 'Proveedor',
    domain=['|', ('is_company', '=', True), ('parent_id', '!=', False)],
    ondelete='restrict',  # ← AGREGAR (no se debe borrar proveedor si tiene recepciones)
    tracking=True
)
```

### 6.3 Reglas de Acceso (`ir.model.access.csv`)

Verificar acceso a modelos del módulo. Basado en la estructura del archivo:
- Modelos `lumber.reception`, `lumber.reception.line`, `madenat.guia.processing` deben tener reglas de acceso definidas
- Los 14 `sudo()` documentados en sección 6.1 indican que posiblemente hay brechas de permisos que se están resolviendo con elevación de privilegios en lugar de reglas de acceso adecuadas

**Recomendación:** Crear grupos de seguridad específicos:
- `group_lumber_reception_user`: Lectura + creación de recepciones
- `group_lumber_reception_manager`: Confirmación + edición de recepciones
- `group_lumber_stock_reset`: Permiso exclusivo para `action_reset_to_draft` (actualmente usa `stock.group_stock_manager`)

---

## 7. PLAN DE REFACTORIZACIÓN

### 7.1 Estructura Propuesta

```
madenat_lumber_core/
├── models/
│   ├── __init__.py                          # Actualizar imports
│   ├── reception/
│   │   ├── __init__.py                      # NUEVO
│   │   ├── lumber_reception.py              # REFACTORIZADO: solo clase + fields + constraints
│   │   ├── lumber_reception_line.py         # NUEVO: extraído de lumber_reception.py (líneas 1-820)
│   │   ├── reception_compute.py             # NUEVO: todos los _compute_* methods
│   │   ├── reception_workflow.py            # NUEVO: action_confirm, action_reset_to_draft, action_cancel
│   │   ├── reception_po.py                  # NUEVO: create_po_from_oc_data, _find_or_create_po_intelligent
│   │   ├── reception_stock.py               # NUEVO: _create_stock_picking, _cleanup_orphan_moves
│   │   └── reception_audit.py               # NUEVO: _add_log, _log_excel_omissions
│   ├── common/                              # NUEVO
│   │   ├── __init__.py
│   │   └── exceptions.py                    # NUEVO: MadenatLumberError y subclases
│   ├── lumber_export_formula.py             # EXISTENTE (sin cambios)
│   ├── lumber_ingestion_format.py           # EXISTENTE (sin cambios)
│   ├── lumber_blank_nominal_map.py          # EXISTENTE (sin cambios)
│   ├── lumber_width_s2s_map.py              # EXISTENTE (sin cambios)
│   ├── madenat_subproducto.py               # EXISTENTE (sin cambios)
│   ├── madenat_ingestion_config.py          # EXISTENTE (sin cambios)
│   ├── madenat_guia_processing.py           # EXISTENTE (sin cambios)
│   ├── madenat_audit_log.py                 # EXISTENTE (sin cambios)
│   ├── reception_service.py                 # EXISTENTE (sin cambios)
│   ├── reception_parser.py                  # EXISTENTE (sin cambios)
│   ├── ingestion_gate.py                    # EXISTENTE (sin cambios)
│   ├── stock_lot.py                         # EXISTENTE (sin cambios)
│   ├── stock_lot_cost_line.py               # EXISTENTE (sin cambios)
│   ├── width_mapping.py                     # EXISTENTE (sin cambios)
│   ├── utils_uom.py                         # EXISTENTE (sin cambios)
│   └── res_config_settings.py               # EXISTENTE (sin cambios)
├── views/                                   # SIN CAMBIOS
├── security/                                # ACTUALIZAR: agregar grupos específicos
│   ├── ir.model.access.csv
│   └── madenat_security.xml
├── data/                                    # SIN CAMBIOS
├── tests/
│   ├── __init__.py
│   ├── test_guia_processing.py              # EXISTENTE
│   ├── test_lot_costing.py                  # EXISTENTE
│   ├── test_reception_workflow.py           # NUEVO
│   ├── test_reception_line.py               # NUEVO
│   └── test_reception_po.py                 # NUEVO
└── wizard/                                  # SIN CAMBIOS
```

### 7.2 Mapeo: Método Actual → Archivo Nuevo

| Método Actual | Línea | Archivo Destino |
|--------------|-------|-----------------|
| `LumberReceptionLine` (clase completa) | 47-820 | `reception/lumber_reception_line.py` |
| `LumberReception` (clase + fields + constraints) | 822-1100 | `reception/lumber_reception.py` |
| `_compute_nominal_status` | 871 | `reception/reception_compute.py` |
| `_compute_can_process_reception` | 1002 | `reception/reception_compute.py` |
| `_compute_can_reopen_reception` | 1007 | `reception/reception_compute.py` |
| `_compute_can_cancel_reception` | 1012 | `reception/reception_compute.py` |
| `_compute_gate_duration_hours` | 1017 | `reception/reception_compute.py` |
| `_compute_purchase_order_display` | 1029 | `reception/reception_compute.py` |
| `_compute_commercial_mbf_from_m3` | ~1133 | `reception/reception_compute.py` |
| `_compute_totals` | ~1551 | `reception/reception_compute.py` |
| `_compute_volume_variance` | ~1560 | `reception/reception_compute.py` |
| `_compute_tolerance_status` | ~1578 | `reception/reception_compute.py` |
| `_compute_unit_prices` | ~1600 | `reception/reception_compute.py` |
| `_compute_export_values` | ~1645 | `reception/reception_compute.py` |
| `action_confirm_reception` | ~1750 | `reception/reception_workflow.py` |
| `action_reset_to_draft` | 1211 | `reception/reception_workflow.py` |
| `action_cancel` | 1376 | `reception/reception_workflow.py` |
| `action_verify_data` | ~1480 | `reception/reception_workflow.py` |
| `action_suggest_nominal_defaults` | ~1521 | `reception/reception_workflow.py` |
| `action_process_documents` | ~1670 | `reception/reception_workflow.py` |
| `_fill_staging_table` | ~1990 | `reception/reception_workflow.py` |
| `create_po_from_oc_data` | ~2100 | `reception/reception_po.py` |
| `_find_or_create_po_intelligent` | ~2228 | `reception/reception_po.py` |
| `_update_po_reception_stats` | ~2375 | `reception/reception_po.py` |
| `_create_stock_picking` | ~2550 | `reception/reception_stock.py` |
| `_create_lots_from_packing` | ~2600 | `reception/reception_stock.py` |
| `_cleanup_orphan_moves` | 2700 | `reception/reception_stock.py` |
| `_add_log` | ~950 | `reception/reception_audit.py` |
| `_log_excel_omissions` | ~1050 | `reception/reception_audit.py` |
| `_compute_reception_summary` | 1389 | `reception/reception_compute.py` |
| `validate_product_configuration` | ~210 | `utils/validators.py` |
| `_validate_product_uom_for_lumber` | ~264 | `utils/validators.py` |

### 7.3 Plan de Migración Paso a Paso

**Fase 0: Preparación (1 día)**
1. Crear branch `refactor/reception-split` desde `main`
2. Ejecutar test suite actual y guardar resultados como baseline
3. Crear estructura de directorios `models/reception/`, `models/common/`

**Fase 1: Extraer LumberReceptionLine (1 día)**
4. Crear `models/reception/lumber_reception_line.py` con líneas 47-820
5. Actualizar `models/__init__.py` para importar desde `reception/`
6. Ejecutar tests, verificar que todo funciona
7. Commit: `refactor: extract LumberReceptionLine to separate file`

**Fase 2: Extraer Métodos Compute (2 días)**
8. Crear `models/reception/reception_compute.py`
9. Mover todos los métodos `_compute_*` uno por uno, testeando entre cada movimiento
10. Commit: `refactor: extract compute methods to reception_compute.py`

**Fase 3: Extraer Workflow (2 días)**
11. Crear `models/reception/reception_workflow.py`
12. Mover `action_confirm_reception`, `action_reset_to_draft`, `action_cancel`, `action_verify_data`, `_fill_staging_table`
13. **Refactorizar `action_reset_to_draft`** en sub-métodos (ver sección 1.4)
14. Commit: `refactor: extract workflow methods + split action_reset_to_draft`

**Fase 4: Extraer PO y Stock (1 día)**
15. Crear `models/reception/reception_po.py` y `reception_stock.py`
16. Mover métodos correspondientes
17. Commit: `refactor: extract PO and Stock methods`

**Fase 5: Crear Excepciones Custom (0.5 días)**
18. Crear `models/common/exceptions.py`
19. Reemplazar `except Exception` genéricos (sección 4)
20. Commit: `refactor: add custom exceptions + replace generic except Exception`

**Fase 6: Agregar Tests (2 días)**
21. Crear `tests/test_reception_workflow.py` con 5 tests de sección 3.3
22. Crear `tests/test_reception_line.py`
23. Ejecutar test suite completa, verificar que el baseline se mantiene o mejora
24. Commit: `test: add comprehensive reception tests`

**Fase 7: Auditoría Final y Deploy (1 día)**
25. Ejecutar todas las herramientas de linting
26. Actualizar `CHANGELOG.md`
27. Merge a `main` y deploy en staging
28. Pruebas de humo en staging con datos reales

**Tiempo total estimado:** 9.5 días hábiles

---

## 8. CHECKLIST FINAL

### Estado Actual del Módulo

- [ ] Archivo `lumber_reception.py` refactorizado (<300 líneas por archivo)
- [ ] Tests añadidos para `action_confirm_reception` y `action_reset_to_draft`
- [ ] Todos los `UserError` con `_()` para traducción
- [ ] Todos los logs en inglés sin caracteres especiales
- [ ] `except Exception` reemplazados por excepciones específicas
- [ ] Excepciones custom creadas (`MadenatLumberError`)
- [ ] `sudo()` documentados con comentarios `# SEC:`
- [ ] `sudo().write()` en productos (línea 2481) corregido con verificación de permisos
- [ ] `ondelete` agregado a `purchase_id` y `supplier_id`
- [ ] Grupos de seguridad específicos de lumber creados
- [ ] `_compute_totals` optimizado (una sola iteración)
- [ ] `action_confirm_reception` usando batch `create()`
- [ ] Cobertura de tests > 60% para métodos críticos

### Resumen de Severidades

| Severidad | Cantidad | Items |
|-----------|----------|-------|
| CRITICAL | 8 | Refactorización, `action_reset_to_draft`, `sudo().write()` en productos, falta de tests, archivo 2718 líneas |
| HIGH | 15 | i18n, excepciones genéricas, performance, `ondelete` faltantes |
| MEDIUM | 12 | Logs en español, `_compute_reception_summary`, campos sin domain |
| LOW | 5 | Caché de métodos, documentación de auditoría |

### Recomendación Final

El módulo `madenat_lumber_core` tiene una base sólida en cuanto a lógica de negocio pero requiere **refactorización estructural urgente** para ser mantenible a largo plazo. Los issues de seguridad relacionados con `sudo()` y `except Exception` deben abordarse antes del próximo deploy a producción. La deuda técnica estimada es de **9.5 días hábiles** siguiendo el plan de la sección 7.3.

**Prioridad de ejecución:**
1. Tests (Sección 3) — 2 días — CRITICAL
2. Excepciones (Sección 4) — 0.5 días — HIGH
3. i18n (Sección 2) — 0.5 días — HIGH
4. Seguridad (Sección 6) — 1 día — CRITICAL
5. Performance (Sección 5) — 1 día — HIGH
6. Refactorización (Sección 7) — 4.5 días — MEDIUM (post-deploy)

---

*Reporte generado por Auditoría Técnica Profunda — 2026-06-08*
*Odoo 18 CE — madenat_lumber_core v4.0.0*