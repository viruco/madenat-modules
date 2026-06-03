# Modelo de Lotes — stock.lot extendido

**Módulo:** `madenat_lumber_core.models.stock_lot`
**Clase:** `StockLotExtended`
**Herencia:** `_inherit = 'stock.lot'`
**Archivo:** `custom_addons/madenat_lumber_core/models/stock_lot.py`
**Categoría:** Técnico
**Estado:** Activo
**Última actualización:** 2026-06-02 (reescrito desde código real v4.0.1)

---

## Propósito

Documentar la extensión del modelo `stock.lot` de Odoo para soportar los datos específicos de lotes de madera en MADENAT, incluyendo dimensiones fraccionarias e imperiales, volumen dual (compra vs embarque), genealogía de lotes, trazabilidad de transformación, costeo multi-nivel y valorización en m³ y MBF.

---

## Clase y herencia

```python
class StockLotExtended(models.Model):
    _inherit = 'stock.lot'
```

---

## Restricciones SQL

| Constraint | Regla |
|---|---|
| `check_volumen_m3_positive` | `CHECK(volumen_m3 >= 0)` |
| `check_piezas_positive` | `CHECK(piezas >= 0)` |
| `check_cost_positive` | `CHECK(total_cost_usd >= 0)` |

---

## Sección 1: Trazabilidad de origen

| Campo | Tipo | Store | Descripción |
|---|---|---|---|
| `reception_id` | Many2one → `lumber.reception` | Sí | Recepción de compra. Domain: `[('state', '=', 'done')]`. Exclusivo para madera comprada. |
| `lumber_reception_id` | Many2one → `lumber.reception` | Sí | Recepción de origen (readonly). Enlace a la recepción donde se ingresó el paquete. |
| `guia_processing_id` | Many2one → `madenat.guia.processing` | Sí | Guía de procesamiento (readonly). Exclusivo para transformación interna. |
| `purchase_order_id` | Many2one → `purchase.order` | Compute (`store=True`) | OC origen. Computado desde `guia_processing_id.order_id` o `reception_id.purchase_id`. |
| `supplier_id` | Many2one → `res.partner` | Compute (`store=True`) | Proveedor. Computado junto con `purchase_order_id`. |
| `reception_type` | Selection: `raw` / `processed` | Compute (`store=True`) | `raw` si tiene `reception_id`; `processed` si tiene `guia_processing_id`. |
| `guia_number` | Char | Compute (`store=True`) | Número de guía según origen: `reception_id.name` o `guia_processing_id.name`. |

---

## Sección 2: Genealogía de lotes

| Campo | Tipo | Store | Descripción |
|---|---|---|---|
| `parent_lot_id` | Many2one → `stock.lot` | Sí | Lote padre del cual se originó este lote (procesamiento, división, etc.). `ondelete='set null'`. |
| `child_lot_ids` | One2many → `stock.lot` | — | Lotes derivados desde este lote por transformación. `inverse_name='parent_lot_id'`. |
| `generation_level` | Integer | Compute (`store=True`) | 0 = lote original, 1 = primera transformación, 2 = segunda, etc. Recursivo. |
| `external_labels` | Char | Sí | Códigos de proveedores externos separados por coma. |
| `origin_type` | Selection: `purchase` / `processing` / `split` / `merge` | Sí | Cómo se originó este lote. |

---

## Sección 3: Clasificación y etiquetado

| Campo | Tipo | Store | Descripción |
|---|---|---|---|
| `subproducto_id` | Many2one → `madenat.subproducto` | Sí | Categoría del producto terminado (ej: BLANK CLEAR, BLANK PANELEADO, RIP S2S). |
| `escuadria` | Char | Compute (`store=True`) | Dimensiones en formato original (ej: `1 1/4 x 4 x 10'`). |
| `escuadria_excel` | Char | Sí | Escuadría original del archivo Excel (no calculada) para trazabilidad exacta. |
| `product_code_only` | Char | Compute (`store=True`) | Código interno del producto (ej: `2X4`). |
| `product_name_only` | Char | Compute (`store=True`) | Nombre del producto sin código. |

---

## Sección 4: Dimensiones fraccionarias (entrada de usuario)

| Campo | Tipo | Store | Descripción |
|---|---|---|---|
| `espesor_inch_frac` | Char | Sí | Espesor en formato fraccional (ej: `1 1/4`, `3/4`, `2`). |
| `ancho_inch_frac` | Char | Sí | Ancho en formato fraccional (ej: `4`, `3 1/2`, `5/8`). |
| `largo_ft_frac` | Char | Sí | Largo en pies, formato fraccional (ej: `10`, `8 1/2`, `12`). |

---

## Sección 5: Dimensiones métricas (calculadas)

| Campo | Tipo | Store | Descripción |
|---|---|---|---|
| `espesor_mm` | Float | Compute (`store=True`, inverse) | Espesor en mm calculado desde fracciones o asignado directamente. |
| `ancho_mm` | Float | Compute (`store=True`, inverse) | Ancho en mm calculado desde fracciones o asignado directamente. |
| `largo_m` | Float | Compute (`store=True`, inverse) | Largo en metros calculado desde fracciones o asignado directamente. |
| `espesor_nominal_mm` | Float | Sí | Espesor comercial de compra (ej: 55mm). |
| `ancho_nominal_mm` | Float | Sí | Ancho comercial de compra. 0 = No aplica (RW - Random Width). |
| `piezas` | Integer | Sí | Cantidad de piezas en el lote. |

---

## Sección 6: Dimensiones visuales persistentes

| Campo | Tipo | Store | Descripción |
|---|---|---|---|
| `thickness_visual` | Char | Sí | Espesor comercial (ej: `6/4`). |
| `width_visual` | Char | Sí | Ancho comercial (ej: `5 5/8`, `RW`). |

---

## Sección 7: Trazabilidad imperial

| Campo | Tipo | Store | Descripción |
|---|---|---|---|
| `reception_thickness_in` | Float | Sí | Espesor en pulgadas al momento de la recepción. |
| `reception_width_in` | Float | Sí | Ancho en pulgadas al momento de la recepción. |
| `reception_length_ft` | Float | Sí | Largo en pies al momento de la recepción. |
| `reception_board_feet` | Float | Sí | Board Feet origen. |
| `length_ft` | Float | Sí | Largo procesado en pies (exportación). |

---

## Sección 8: Volumen dual (compra vs embarque)

| Campo | Tipo | Store | Descripción |
|---|---|---|---|
| `volume_purchase_m3` | Float | Sí | Volumen original al momento de compra (dimensiones brutas, pre-cepillado). |
| `vol_shipment_m3` | Float | Sí (`readonly=False`) | Volumen de embarque calculado según regla comercial. Usa `BLANK_CLEAR_FACTOR` (5085.312) si tiene `largo_ft_frac`, o `INCH_SQ_METERS_TO_M3` (1550.003) para métrico con overmeasure S2S. |

### Lógica de `_compute_vol_shipment_m3`

```
1. Si reception_id existe y vol_shipment_m3 > 0.001 → preservar (no recalcular)
2. Determinar dimensiones base: espesor_nominal_mm > commercial_thickness_mm > espesor_mm
3. Si faltan dimensiones o piezas → asignar nominal (volume_purchase_m3 o volumen_m3)
4. Convertir espesor y ancho a pulgadas (división por MM_PER_INCH)
5. Calcular overmeasure: 0 si usa nominal o is_std, sino get_s2s_adjustment()
6. Bifurcación:
   - Si largo_ft_frac presente → vol = (espesor_in × ancho_in × largo_ft × piezas) / BLANK_CLEAR_FACTOR
     NOTA: NO se aplica overmeasure ni deducciones de cepillado en esta rama
   - Si largo métrico → vol = (espesor_in × ancho_calculo × largo_m × piezas) / INCH_SQ_METERS_TO_M3
7. Redondear a 3 decimales (r3). Si resultado ≤ 0 → usar nominal.
```

---

## Sección 9: Volúmenes calculados

| Campo | Tipo | Store | Descripción |
|---|---|---|---|
| `volumen_m3` | Float | Compute (`store=True`) | Volumen para distribución de costos. Prioridad: volume_purchase_m3 > cálculo desde dimensiones métricas. |
| `volumen_mbf` | Float | Compute (`store=True`) | Volumen en MBF (Thousand Board Feet). 1 MBF ≈ 2.36 m³. |

---

## Sección 10: Dimensiones post-procesamiento

| Campo | Tipo | Store | Descripción |
|---|---|---|---|
| `thickness_final_inch` | Float | Sí | Espesor después de cepillado/procesamiento en pulgadas. |
| `width_final_inch` | Float | Sí | Ancho después de cepillado/procesamiento en pulgadas. |
| `processing_loss_pct` | Float | Compute (`store=True`) | Porcentaje de pérdida: `(vol_purchase − vol_shipment) / vol_purchase × 100`. |

---

## Sección 11: Estado y trazabilidad

| Campo | Tipo | Store | Descripción |
|---|---|---|---|
| `estado_trazabilidad` | Selection: `recepcionado` / `en_patio` / `procesado` / `consolidado` / `embarcado` | Compute (`store=True`) | Estado en el flujo operativo. Detecta procesamiento vía `_is_processed_lot()` (guía, parent_lot_id, dimensiones finales, o diferencia volumen compra/embarque). Luego consulta contenedor y embarque para `consolidado`/`embarcado`. |
| `location_id` | Many2one → `stock.location` | Sí | Ubicación física actual del lote en almacén. |

### Método `_is_processed_lot()` (5 indicadores)

1. `guia_processing_id` poblado → procesado
2. `parent_lot_id` poblado → procesado
3. `thickness_final_inch > 0` o `width_final_inch > 0` → procesado
4. `vol_shipment_m3 > 0` y `volume_purchase_m3 > 0` y `vol_shipment_m3 ≠ volume_purchase_m3` → procesado
5. Ninguno de los anteriores → no procesado

NOTA: `subproducto_id` por sí solo NO indica procesamiento. Es clasificación comercial.

---

## Sección 12: Valorización de compra (USD/CLP)

| Campo | Tipo | Store | Descripción |
|---|---|---|---|
| `purchase_price_usd_per_m3` | Float | Sí | Precio unitario pagado al proveedor en USD/m³. |
| `purchase_exchange_rate` | Float | Sí | Tasa CLP/USD al momento de la compra. |
| `purchase_amount_usd` | Float | Compute (`store=True`) | `volumen_m3 × purchase_price_usd_per_m3`. |
| `purchase_amount_clp` | Float | Compute (`store=True`) | `purchase_amount_usd × purchase_exchange_rate`. |

---

## Sección 13: Valorización de venta (USD/MBF)

| Campo | Tipo | Store | Descripción |
|---|---|---|---|
| `sale_price_usd_per_mbf` | Float | Sí | Precio de venta por MBF. |
| `sale_amount_usd` | Float | Compute (`store=True`) | `volumen_mbf × sale_price_usd_per_mbf`. |

---

## Sección 14: Márgenes

| Campo | Tipo | Store | Descripción |
|---|---|---|---|
| `margin_usd` | Float | Compute (`store=True`) | `sale_amount_usd − total_cost_usd`. |
| `margin_percent` | Float | Compute (`store=True`) | `(margin_usd / sale_amount_usd) × 100`. |

---

## Sección 15: Gestión de costos

| Campo | Tipo | Store | Descripción |
|---|---|---|---|
| `cost_line_ids` | One2many → `stock.lot.cost.line` | — | Desglose detallado de costos asociados al lote. |
| `cost_per_m3_usd` | Float | Compute (`store=True`) | Suma de costos / `volumen_m3`. |
| `cost_per_mbf_usd` | Float | Compute (`store=True`) | Suma de costos / `volumen_mbf`. |
| `wood_cost_usd` | Float | Sí | Costo madera USD. |
| `purchase_cost_usd` | Float | Sí | Costo compra USD. |
| `total_cost_usd` | Float | Compute (`store=False`) | `wood_cost_usd + purchase_cost_usd + sum(cost_line_ids.amount_usd)`. |
| `lot_exchange_rate` | Float | Sí | Tipo de cambio del lote. |

---

## Sección 16: Sistema de validación

| Campo | Tipo | Store | Descripción |
|---|---|---|---|
| `technical_validation` | Selection: `pending` / `approved` / `rejected` | Sí | Aprobación de calidad/especificaciones. Default: `pending`. |
| `financial_validation` | Selection: `pending` / `approved` / `rejected` | Sí | Autorización de pago. Default: `pending`. |
| `is_billed` | Boolean | Compute (`store=False`) | Indica si el lote está incluido en una consolidación facturada (`consolidation_id.state == 'billed'`). |

### Acciones

- `action_approve_technical()` → `technical_validation = 'approved'`
- `action_reject_technical()` → `technical_validation = 'rejected'`
- `action_approve_financial()` → `financial_validation = 'approved'`
- `action_reject_financial()` → `financial_validation = 'rejected'`
- `action_view_lot_genealogy()` → Vista de árbol genealógico (padres, hijos, descendientes recursivos)

---

## Sección 17: Restricciones adicionales

| Campo | Regla |
|---|---|
| `reception_id` + `guia_processing_id` | Exclusividad: un lote no puede tener ambos simultáneamente (`_check_reception_guia_exclusivity`). |
| `volumen_mbf` | No puede ser negativo (`_check_mbf_positive`). |
| `purchase_price_usd_per_m3` | Debe ser > 0 si `purchase_amount_usd > 0` (`_check_purchase_price`). |
| Modificación de costos | Bloqueada si `is_billed == True` (`_check_cost_modification_if_billed`). |

---

## Sección 18: Extensión stock.quant

La clase `StockQuant` (mismo archivo) extiende `stock.quant` con:

| Campo | Tipo | Store | Descripción |
|---|---|---|---|
| `reception_name` | Char (related → `lot_id.reception_id.name`) | No | N° de Guía. |
| `reception_date` | Datetime (related → `lot_id.reception_id.reception_date`) | No | Fecha Guía. |
| `supplier_id` | Many2one (related → `lot_id.supplier_id`) | No | Proveedor. |
| `volumen_sistema_m3` | Float (related → `quantity`) | No | Volumen real del sistema. |
| `subproducto_id` | Many2one (related → `lot_id.subproducto_id`) | No | Subproducto. |
| `etiqueta_limpia` | Char (related → `lot_id.ref`) | No | Etiqueta Lote. |

---

## Dependencias de imports

```python
from .utils_uom import (
    INCH_SQ_METERS_TO_M3,
    get_s2s_adjustment,
    r3, r4,
    BLANK_CLEAR_FACTOR,
    MM_PER_INCH,
    FT_TO_M,
    M_TO_FT,
)
```

---

## Evidencia

- Archivo: `custom_addons/madenat_lumber_core/models/stock_lot.py` (1392 líneas, v4.0.1)
- Tests: `CANON/03_TESTS.md`

---

## Relacionado

- [[servicio_lotes]] — `LumberReceptionService` que crea `stock.lot` desde staging
- [[gates_validacion]] — Gates que validan antes del commit a stock
- [[validadores_checklist]] — `ValidationChecklistMixin` con 7 validadores de integridad
- [[reglas_lotes_trazabilidad]]
- [[modelo_recepciones]]
- [[campos_computados]]