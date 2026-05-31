# Modelo de Lotes — stock.lot extendido

**Módulo:** madenat_lumber_core
**Categoría:** Técnico
**Estado:** Activo
**Última actualización:** 2026-05-28

---

## Propósito

Documentar la extensión del modelo `stock.lot` de Odoo para soportar los datos específicos de lotes de madera en MADENAT.

---

## Herencia usada

```python
class MadenatLote(models.Model):
    _inherit = 'stock.lot'
    _description = 'Lote de Madera MADENAT'
```

---

## Campos propios

| Campo | Tipo | Descripción |
|---|---|---|
| `madenat_proveedor_id` | Many2one → res.partner | Proveedor de origen del lote |
| `madenat_especie` | Selection | Especie de madera (pino, eucalipto, etc.) |
| `madenat_dimension` | Char | Dimensión en formato estándar (ej: 2x4x3.0) |
| `madenat_fecha_recepcion` | Date | Fecha de ingreso físico al sistema |
| `madenat_volumen_m3` | Float | Volumen total en metros cúbicos |
| `madenat_estado_lote` | Selection | activo / despachado / cerrado |
| `madenat_recepcion_id` | Many2one → madenat.recepcion | Recepción que originó el lote |

---

## Campos computados

| Campo | Depende de | Descripción |
|---|---|---|
| `madenat_stock_disponible` | stock.quant | Cantidad disponible actual del lote |
| `madenat_valor_inventario` | purchase.order.line | Valorización actual del lote |

---

## Restricciones conocidas

- `madenat_especie` y `madenat_dimension` son obligatorios al crear el lote.
- `madenat_estado_lote` no es modificable manualmente; cambia por lógica de negocio.
- No hay fusión de lotes; cada lote es una unidad independiente.

---

## Evidencia

- Archivo: `custom_addons/madenat_lumber_core/models/madenat_lote.py`
- Test: `CANON/03_TESTS.md`

---

## Relacionado

- [[reglas_lotes_trazabilidad]]
- [[modelo_recepciones]]
- [[campos_computados]]
- [[00_ARQUITECTURA]]
