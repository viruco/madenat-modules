# INFORME TÉCNICO DE INVESTIGACIÓN: RESIDUOS DE LOTES POST-REVERSA DE GUÍA

**Fecha:** 2026-06-18  
**Versión:** 1.0  
**Alcance:** `madenat.guia.processing` — flujo de reversión `action_reopen_to_draft` y `action_force_cancel`

---

## 1. RESUMEN EJECUTIVO

La reversa de una guía de procesamiento (`action_reopen_to_draft`) **no elimina los `stock.lot`** creados durante el procesamiento. Solo les quita el `guia_processing_id` y los marca con `technical_validation='rejected'`. Sin embargo, los `stock.quant` (existencias físicas) permanecen intactos con `quantity > 0`, y los reportes de logística (`lumber_stock_report.py`) **no filtran por `technical_validation`**. El resultado es que los lotes revertidos siguen apareciendo en todas las vistas de inventario y reportes de logística como si fueran stock válido, cuando en realidad son residuos de una operación anulada.

**El problema es de doble naturaleza: residuo de datos en BD (`stock.quant` activos) + filtro ausente en reportes.**

---

## 2. TABLA DE HALLAZGOS

| Archivo | Método | Línea aprox. | Efecto sobre lotes/stock | Riesgo |
|---|---|---|---|---|
| `madenat_guia_processing.py` | `do_full_processing()` | 1013–1161 | Crea `stock.lot`, `stock.move`, `stock.move.line`, vincula lotes a guía vía `lot_ids`, crea `stock.picking` y lo confirma → genera `stock.quant` | ALTO — Produce el stock que luego queda residual |
| `madenat_guia_processing.py` | `_get_or_create_picking_unified()` | 1760–1928 | Crea `stock.picking` con `stock.move` que al confirmarse (`action_confirm` + `action_assign`) generan `stock.quant` | ALTO — Genera quants que nunca se eliminan en reversa |
| `madenat_guia_processing.py` | `_create_picking_and_lines()` | 3339–3380 | Crea `stock.move` y `stock.move.line` explícitamente vinculados al picking | MEDIO — move_lines no se limpian en reversa |
| `madenat_guia_processing.py` | `_create_or_get_lot()` | 3123–3321 | Crea/actualiza `stock.lot` con `guia_processing_id=self.id` y `volumen_m3` | CRÍTICO — El lote nace con FK y volumen que persisten tras reversa |
| `madenat_guia_processing.py` | `action_reopen_to_draft()` | 3783–3941 | **FASE 3 (línea 3869–3884):** `rec.lot_ids.write({guia_processing_id: False, technical_validation: 'rejected'})` + `lot_ids: [(5,0,0)]`. **NO llama a `unlink()` sobre `stock.lot`. NO elimina `stock.quant`. NO elimina `stock.move.line`.** Cancela pickings draft pero no limpia quants. | **CRÍTICO** — Esta es la causa raíz directa |
| `madenat_guia_processing.py` | `action_force_cancel()` | ~3702–3780 | Igual que `reopen_to_draft`: `guia_processing_id=False` + desvincula lotes. **NO elimina `stock.lot` ni `stock.quant`.** Revierte pickings done vía `_create_return_picking` (genera movimientos inversos), pero los quants del procesamiento original permanecen. | ALTO — Mismo patrón, distinta ruta |
| `madenat_guia_processing.py` | `_cleanup_orphan_moves_guia()` | 3994–4043 | Elimina `stock.move.line` y `stock.move` huérfanos (sin picking). **Solo se invoca desde `unlink()`** (línea 3990), no desde las reversas. | MEDIO — Existe pero no se usa donde se necesita |
| `lumber_stock_report.py` | `LumberStockReport` (modelo) | 1–642 | Extiende `stock.quant`. **Filtro de existencia: `quantity > 0 AND location_id.usage = 'internal'`** (línea 8-10). **NO filtra por `lot_id.technical_validation`.** | **CRÍTICO** — Muestra lotes revertidos como stock válido |
| `report_helpers.py` | Múltiples helpers | todo el archivo | Lee datos de `stock.quant → lot_id` sin filtrar por `technical_validation` | ALTO — Todos los reportes heredan la visibilidad de lotes revertidos |
| `madenat_guia_processing.py` | `_compute_all_totals()` | 932–985 | Calcula totales desde `lot_ids` o `processing_line_ids`. Tras reversa, `lot_ids` queda vacío y `processing_line_ids` eliminado → totales en 0 (correcto). | BAJO — Funciona bien, pero no limpia el stock subyacente |
| `_audit_reversion_residuos.py` | Sección 2C | ~86–100 | Detecta lotes `rejected` con `stock.quant` activo. Confirma que el residuo existe en BD. | INFO — Herramienta de auditoría existente |

---

## 3. EXPLICACIÓN DETALLADA DE POR QUÉ LOS LOTES REAPARECEN

### 3.1. Flujo normal de procesamiento

```
do_full_processing()
  └─ _create_or_get_lot()         → Crea stock.lot (guia_processing_id = self.id, volumen_m3 = X)
  └─ _create_picking_and_lines()  → Crea stock.picking, stock.move, stock.move.line
  └─ picking.action_confirm()     → Genera stock.quant (quantity = X, lot_id = lote)
  └─ lot_ids = [(6, 0, [...])]    → Vincula lotes a la guía (campo many2many)
```

Resultado: `stock.lot` con FK a guía + `stock.quant` con existencia positiva en ubicación interna.

### 3.2. Flujo de reversa (`action_reopen_to_draft`) — LÍNEA 3869–3884

```python
# Línea 3879-3884 de madenat_guia_processing.py
rec.lot_ids.write({
    'guia_processing_id': False,          # ← desvincula FK
    'estado_trazabilidad': 'recepcionado', # ← resetea estado
    'technical_validation': 'rejected',    # ← marca como rechazado
})
rec.write({'lot_ids': [(5, 0, 0)]})       # ← desvincula relación many2many
```

Lo que **NO hace**:
- ❌ No llama a `stock.lot.unlink()` — los lotes siguen existiendo en BD
- ❌ No elimina `stock.quant` — la existencia física sigue en `quantity > 0`
- ❌ No elimina `stock.move` ni `stock.move.line` — los movimientos del picking cancelado quedan
- ❌ No llama a `_cleanup_orphan_moves_guia()` — ese método solo se invoca en `unlink()` de la guía

### 3.3. Por qué los reportes los muestran

`lumber_stock_report.py` extiende `stock.quant` (línea 40-41):
```python
_name = 'stock.quant'
_inherit = ['stock.quant', 'report.helper.mixin']
```

Su filtro de existencia (documentado en línea 8-10):
```
quantity > 0 AND location_id.usage = 'internal'
```

**No existe ningún filtro por `lot_id.technical_validation != 'rejected'`.** Por tanto, todo `stock.quant` con `quantity > 0` en bodega aparece en los reportes, independientemente de que su lote haya sido marcado como `rejected` por una reversa.

El campo `lot_guia_number` (línea 76-82) se resuelve por `related='lot_id.guia_number'`, que a su vez deriva de `guia_processing_id.name`. Al desvincular `guia_processing_id`, el número de guía desaparece de la vista, pero el lote y su volumen permanecen visibles como stock anónimo (sin guía).

---

## 4. JERARQUÍA DE CAUSAS

### Causa Raíz Primaria (CR1): `action_reopen_to_draft` no elimina `stock.quant`

**Evidencia:** Líneas 3869–3884. El método solo modifica atributos del lote (`guia_processing_id=False`, `technical_validation='rejected'`) y desvincula la relación many2many. En ningún punto itera sobre `stock.quant` para eliminar o poner en cero las existencias generadas por el `stock.picking` asociado.

**Impacto:** `stock.quant.quantity > 0` persiste. El inventario físico muestra stock que no debería existir.

### Causa Raíz Secundaria (CR2): Reportes de logística no filtran `technical_validation='rejected'`

**Evidencia:** `lumber_stock_report.py` línea 8-10 y todos los helpers de `report_helpers.py`. El ecosistema B (`stock.quant → lot_id`) no aplica ningún filtro documental sobre el estado de validación técnica del lote.

**Impacto:** Aunque el lote esté marcado como `rejected`, cualquier reporte que lea `stock.quant` lo mostrará como stock disponible.

### Causa Contribuyente (CC1): `action_force_cancel` tiene el mismo defecto

**Evidencia:** Líneas 3734–3745. Misma lógica de desvinculación sin eliminación de quants.

---

## 5. ¿FALTAN `unlink()` O UN CLEANUP FÍSICO?

**Sí, faltan ambas cosas:**

1. **Falta `unlink()` de `stock.lot`** — o al menos forzar `quantity = 0` en los `stock.quant` asociados. La reversa debería:
   - Localizar los `stock.quant` vinculados a los lotes de la guía
   - Ejecutar un movimiento de salida (tipo `inventory`) para llevar `quantity` a 0
   - O alternativamente, eliminar los quants vía `unlink()` (requiere permisos avanzados)

2. **Falta invocar `_cleanup_orphan_moves_guia()` desde `action_reopen_to_draft`** — Actualmente este método solo se llama desde `unlink()` de la guía (línea 3990), que es una operación de eliminación total, no de reversa.

3. **Falta filtro en reportes** como capa de defensa adicional: `lot_id.technical_validation != 'rejected'`.

---

## 6. ¿HAY UN PROCESO POSTERIOR QUE REINYECTA LOS LOTES?

**No.** No se detecta ningún proceso automático que reasigne `guia_processing_id` o reactive lotes con `technical_validation='rejected'`. El problema es puramente **residual pasivo**: los datos quedan en BD y los reportes los muestran porque no hay filtro que los excluya.

Las únicas vías por las que un lote revertido podría volver a tener `guia_processing_id` son:
- Un nuevo `do_full_processing()` (reprocesamiento manual explícito)
- Una edición manual del usuario sobre el registro `stock.lot`

Ninguna de estas es automática ni inadvertida.

---

## 7. PARCHE MÍNIMO RECOMENDADO

### 7.1. Fix en `action_reopen_to_draft()` (archivo: `madenat_guia_processing.py`, línea ~3884)

Insertar **después** de la limpieza de lotes (línea 3884) y **antes** de la FASE 4 (línea 3890):

```python
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧹 FASE 3.5: LIMPIEZA DE STOCK RESIDUAL (quants)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if rec.lot_ids:
    quants_to_clear = self.env['stock.quant'].sudo().search([
        ('lot_id', 'in', rec.lot_ids.ids),
        ('quantity', '>', 0),
        ('location_id.usage', '=', 'internal'),
    ])
    if quants_to_clear:
        _logger.info(
            f"🧹 Limpiando {len(quants_to_clear)} quants residuales "
            f"de guía revertida {rec.name}"
        )
        quants_to_clear.write({'quantity': 0.0})
        rec.message_post(
            body=f"🧹 Se pusieron en cero {len(quants_to_clear)} "
                 f"existencias (quants) de lotes revertidos."
        )
```

### 7.2. Fix en reportes como capa de defensa adicional

En `lumber_stock_report.py`, agregar al domain de las vistas tree/search que usan `stock.quant`:

```xml
<field name="domain">
  [('quantity', '>', 0),
   ('location_id.usage', '=', 'internal'),
   ('lot_id.technical_validation', '!=', 'rejected')]
</field>
```

### 7.3. Opcional: Invocar `_cleanup_orphan_moves_guia()` desde reversa

Agregar al final de FASE 3 de `action_reopen_to_draft`:

```python
rec._cleanup_orphan_moves_guia()
```

**Precaución:** Este método requiere permisos `stock.group_stock_manager` (línea 4000). Si se invoca desde la reversa, debe wrappearse con `sudo()` o verificar permisos antes.

---

## 8. CONCLUSIÓN

| Aspecto | Conclusión |
|---|---|
| ¿La reversa elimina `stock.lot`? | **NO.** Solo desvincula `guia_processing_id` y marca `technical_validation='rejected'` |
| ¿La reversa elimina `stock.quant`? | **NO.** Los quants quedan con `quantity > 0` |
| ¿La reversa elimina `stock.move` / `stock.move.line`? | **NO.** Solo se cancelan pickings vía ORM; los moves quedan en estado `cancel` |
| ¿Es residual visual o de datos? | **Ambos.** Datos reales en BD (quants > 0) + filtro ausente en reportes |
| ¿Hay reinyección automática? | **NO.** Es persistencia pasiva, no reactivación |
| ¿Fix mínimo seguro? | Poner `quantity = 0` en los `stock.quant` de los lotes revertidos + filtro en reportes |