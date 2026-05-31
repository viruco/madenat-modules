# tracking_mail_thread — Implementación y Errores

**Módulo:** madenat_lumber_core
**Categoría:** Técnico
**Estado:** Activo — resuelto
**Última actualización:** 2026-05-28

---

## Propósito

Documentar la implementación de `mail.thread` y `mail.activity.mixin` en los modelos de MADENAT, incluyendo el error de campo `name` duplicado detectado en auditoría.

---

## Implementación actual

```python
class MadenatRecepcion(models.Model):
    _name = 'madenat.recepcion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Recepción de Madera'

    name = fields.Char(
        string='Referencia',
        required=True,
        tracking=True
    )
```

---

## Error conocido: campo name duplicado

El modelo `madenat_guia_processing` definía el campo `name` dos veces: una como campo propio y otra heredada de `mail.thread`. Esto generaba un warning de Odoo al cargar el módulo.

**Resolución:** Eliminar la redefinición manual de `name` y dejar solo la declaración del campo propio con el nombre correcto. Ver [[INC-001_campo_name_duplicado]].

---

## Regla actual

- `mail.thread` se declara en `_inherit` como lista junto a `mail.activity.mixin`.
- Solo los campos que realmente necesitan tracking deben tener `tracking=True`.
- No redefinir campos heredados de `mail.thread` si ya existen en la clase padre.

---

## Restricciones conocidas

- Agregar `mail.thread` aumenta el peso de los modelos; usar solo donde el chatter es necesario para el negocio.
- Los warnings de tracking generan ruido en logs de producción si no se resuelven.

---

## Relacionado

- [[modulo_lumber_core]]
- [[INC-001_campo_name_duplicado]]
- [[herencia_odoo_modelos]]
