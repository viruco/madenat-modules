# Herencia de Modelos Odoo en MADENAT

**Módulo:** madenat_lumber_core
**Categoría:** Técnico
**Estado:** Activo
**Última actualización:** 2026-05-28

---

## Propósito

Documentar los patrones de herencia usados en los modelos de MADENAT para mantener consistencia y evitar errores comunes.

---

## Tipos de herencia usados

### Herencia por extensión (_inherit sin _name nuevo)
Se usa para agregar campos o métodos a modelos existentes de Odoo.

```python
class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_processor = fields.Boolean(string='Es Procesador', default=False)
    processor_location = fields.Char(string='Ubicación Planta')
```

> **Nota:** Esta extensión reside en `madenat_lumber_reception_improvements/models/res_partner.py`.

### Herencia de delegación (modelos propios con _name nuevo)
Se usa para crear modelos propios de MADENAT que tienen lógica independiente.

```python
class LumberReception(models.Model):
    _name = 'lumber.reception'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'madenat.lumber.ingest.mixin']
    _description = '📦 RECEPCIÓN DE MADERA BRUTA DESDE PROVEEDOR'
    _order = 'reception_date desc'
```

---

## Reglas de convención

- Los modelos de infraestructura transversal usan prefijo `madenat.` (ej: `madenat.audit.log`, `madenat.subproducto`, `madenat.guia.processing`).
- Los modelos de dominio maderero usan prefijo `lumber.` (ej: `lumber.reception`, `lumber.reception.line`).
- Los mixins abstractos usan `madenat.lumber.*.mixin` (ej: `madenat.lumber.ingest.mixin`, `madenat.lumber.ingest.line.mixin`, `validation.checklist.mixin`).
- `stock.lot`, `stock.picking`, `stock.move`, `stock.quant` y `product.template` se extienden por `_inherit` sin crear modelo nuevo.

---

## Anti-patrones detectados

- No redefinir campos que ya existen en la clase padre (ver [[tracking_mail_thread]]).
- No usar `_inherit` y `_name` con el mismo valor si no es necesario crear un nuevo modelo.

---

## Mixins transversales

| Mixin | Archivo | Usado por |
|---|---|---|
| `madenat.lumber.ingest.mixin` | `mixin_lumber_ingest.py` | `lumber.reception` |
| `madenat.lumber.ingest.line.mixin` | `mixin_lumber_ingest.py` | `lumber.reception.line` |
| `validation.checklist.mixin` | `validation_checklist_mixin.py` | `lumber.reception`, `madenat.guia.processing` |

---

## Relacionado

- [[modulo_lumber_core]]
- [[modelo_recepciones]]
- [[tracking_mail_thread]]
- [[campos_computados]]
