# Tipos de Madera y Clasificación

**Módulo:** madenat_lumber_core
**Categoría:** Negocio
**Estado:** Borrador
**Última actualización:** 2026-05-30

---

## Propósito

Documentar cómo se codifica la clasificación de madera en MADENAT a través del catálogo `madenat.subproducto` y los campos de `stock.lot`.

A diferencia de un sistema con enumeraciones fijas, MADENAT usa un **catálogo libre**: los valores se configuran desde Odoo y no están hardcodeados en el código.

---

## Modelo madenat.subproducto

```python
class MadenatSubproducto(models.Model):
    _name = 'madenat.subproducto'
    _description = 'Catálogo de Sub-productos MADENAT'
    _order = 'sequence, name'
```

| Campo | Tipo | Descripción |
|---|---|---|
| `name` | Char (required, unique) | Nombre del subproducto (ej: "BLANK CLEAR", "BLANK PANELEADO") |
| `code` | Char (required, unique) | Código corto para reportes (ej: "BC", "BP") |
| `description` | Text | Descripción detallada del subproducto |
| `sequence` | Integer (default=10) | Orden de visualización |
| `active` | Boolean (default=True) | Si está activo o archivado |

**SQL constraints:**
- `code_unique`: el código debe ser único
- `name_unique`: el nombre debe ser único

**Validaciones:**
- `check_code_format`: el código solo permite letras, números, espacios y guiones (`[A-Za-z0-9 -]`)

---

## Restricciones del modelo

- `code` solo acepta letras, números, espacios y guiones — no caracteres especiales ni símbolos
- `name` y `code` son **únicos** a nivel de base de datos (SQL UNIQUE constraint)
- No hay campos `Selection` — el catálogo es completamente configurable por el administrador desde la interfaz de Odoo
- Los subproductos se ordenan por `sequence` y luego por `name`

---

## Relación con stock.lot

El campo `subproducto_id` en `stock.lot` apunta a este catálogo:

```python
subproducto_id = fields.Many2one(
    comodel_name='madenat.subproducto',
    string='Sub-producto',
    help="Categoría del producto terminado (ej: BLANK CLEAR, BLANK PANELEADO, RIP S2S)"
)
```

El subproducto define el **tipo comercial** del lote — qué clase de producto terminado representa (no la especie ni la dimensión).

---

## Nota sobre clasificación de madera

La clasificación completa de un lote de madera en MADENAT **no está centralizada en un solo campo** — se distribuye en varios campos de `stock.lot`:

| Dimensión de clasificación | Campo | Ejemplo |
|---|---|---|
| **Especie/Producto** | `product_id` → `product.template` | Pino Radiata, Eucalipto |
| **Dimensiones físicas** | `espesor_mm`, `ancho_mm`, `largo_m` | 45mm × 150mm × 3.0m |
| **Dimensiones fraccionarias** | `espesor_inch_frac`, `ancho_inch_frac`, `largo_ft_frac` | 1 3/4" × 5 7/8" × 10' |
| **Tipo comercial** | `subproducto_id` → `madenat.subproducto` | BLANK CLEAR, RIP S2S |
| **Calidad** | Implícita en `subproducto_id` | El subproducto define la calidad comercial |

**No existe un modelo de "calidades" separado.** La calidad se gestiona a través del subproducto: si un lote es "BLANK CLEAR", eso implica una calidad específica definida por el negocio en el catálogo.

---

## Restricciones conocidas

- El catálogo de subproductos es **libre**: no hay valores predefinidos en el código. Se configuran desde la interfaz de Odoo.
- Si se elimina un subproducto que tiene lotes referenciándolo, Odoo bloquea la eliminación (Foreign Key).
- El campo `subproducto_id` es uno de los 5 indicadores que determina si un lote está "procesado" (`_is_processed_lot` en `stock_lot.py`).
- La especie de madera se gestiona a través del `product_id` (producto maestro de Odoo), no a través de un campo propio de especie en el lote.

---

## Evidencia

- Archivo: `custom_addons/madenat_lumber_core/models/madenat_subproducto.py`
- Relación: `custom_addons/madenat_lumber_core/models/stock_lot.py` (`subproducto_id`)
- Datos semilla: `custom_addons/madenat_lumber_core/data/madenat_subproducto_data.xml`
- Test: `CANON/03_TESTS.md`

---

## Relacionado

- [[reglas_lotes_trazabilidad]]
- [[modelo_lotes]]
- [[flujo_recepcion_madera]]
- [[flujo_despacho_embarque]]
