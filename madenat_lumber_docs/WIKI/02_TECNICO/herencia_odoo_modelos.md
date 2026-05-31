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
class ResPartnerMadenat(models.Model):
    _inherit = 'res.partner'

    madenat_es_aserradero = fields.Boolean(string='Es Aserradero')
    madenat_especie_preferente = fields.Char(string='Especie preferente')
```

### Herencia de delegación (modelos propios con _name nuevo)
Se usa para crear modelos propios de MADENAT que tienen lógica independiente.

```python
class MadenatRecepcion(models.Model):
    _name = 'madenat.recepcion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Recepción de Madera MADENAT'
```

---

## Reglas de convención

- Todos los campos propios de MADENAT tienen prefijo `madenat_`.
- Todos los modelos propios tienen nombre con prefijo `madenat.`.
- Ningún modelo propio de MADENAT hereda directamente de `stock.picking`; se trabaja con métodos y referencias.

---

## Anti-patrones detectados

- No redefinir campos que ya existen en la clase padre (ver [[tracking_mail_thread]]).
- No usar `_inherit` y `_name` con el mismo valor si no es necesario crear un nuevo modelo.

---

## Relacionado

- [[modulo_lumber_core]]
- [[tracking_mail_thread]]
- [[campos_computados]]
