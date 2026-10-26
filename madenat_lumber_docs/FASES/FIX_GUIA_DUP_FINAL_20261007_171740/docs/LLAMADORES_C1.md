# Llamadores de `_check_guide_duplicate` (C1) y verificación de contratos

Firma final de C1 (`reception_parser.py`):

```python
def _check_guide_duplicate(self, guide_no, partner_id=None, exclude_id=None,
                           exclude_model='lumber.reception',
                           cross_model=False,       # default CAMBIÓ True→False
                           raise_on_match=True):    # NUEVO
```

## Inventario de llamadores

| # | Ubicación | Llamada | Posicionales | Nombrados | `exclude_model` | `cross_model` | `raise_on_match` | Retorno esperado | Excepción esperada |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `reception_workflow.py` `_check_duplicate_and_warn` | confirmado | `guide_no` | `exclude_id` | `'lumber.reception'` | `False` (explícito) | `True` (default) | `None` | `UserError` si confirmado |
| 2 | `reception_workflow.py` `_check_duplicate_and_warn` | homónimo | `guide_no` | `partner_id=None, exclude_id` | `'lumber.reception'` | `True` (explícito) | `False` (explícito) | `(modelo, registro)` o `None` | — |
| 3 | `madenat_guia_processing.py` `_check_guide_identity_duplicate` | confirmado | `name` | `partner_id, exclude_id` | `'madenat.guia.processing'` | `False` (explícito) | `True` (default) | `None` | `UserError` si confirmado |
| 4 | `madenat_guia_processing.py` `_check_guide_identity_duplicate` | homónimo | `name` | `partner_id=None, exclude_id` | `'madenat.guia.processing'` | `True` (explícito) | `False` (explícito) | `(modelo, registro)` o `None` | — |
| 5 | `madenat_guia_processing.py` `_check_guide_identity_duplicate_on_create` | confirmado | `name` | `partner_id` | `'madenat.guia.processing'` | `False` (explícito) | `True` (default) | `None` | `UserError` si confirmado |
| 6 | `tests/*` | directas | `guía` | mixto | por defecto / explícito | explícito | explícito | `None`/tupla | `UserError` |

**Único llamador de PRODUCCIÓN del árbol activo:** `reception_workflow.py` (fila 1, hoy sin
`cross_model` explícito). El resto de llamadores de producción existen sólo con el parche.

## Verificación de compatibilidad

- **Argumentos:** todos los llamadores usan `guide_no`/`name` **posicional** y el resto
  **nombrado** → el añadido de `raise_on_match` y el cambio de default de `cross_model` **no**
  alteran el enlace posicional.
- **`cross_model` default True→False:** SÍ cambia el comportamiento de las rutas que **no**
  pasaban el argumento (efecto buscado del AJUSTE B: simetría). Se eliminó la dependencia
  implícita: los llamadores de producción ahora pasan `cross_model` **explícito**.
- **`exclude_id` + `exclude_model`:** la exclusión sigue siendo por **modelo y registro**; un
  ID igual en otra tabla **no** se oculta (ver `test_08b`).
- **`raise_on_match`:** por defecto `True` → comportamiento histórico (lanza). Los avisos usan
  `False` → devuelve `(modelo, registro)`; nunca lanza.
- **Retorno/excepciones:** con `raise_on_match=True` retorna `None`/lanza `UserError`
  (igual que antes); con `False` retorna tupla o `None`.
- **Lotes y acceso:** compatible con `create`/`write` múltiples; el `search` interno usa
  `sudo()` **pre-existente** (no se añadió); los avisos **no** exponen datos de otro registro
  (sólo el N° y la categoría).

Conclusión: **contratos preservados**; la única modificación de comportamiento es la buscada
(simetría cross-model) y quedó **explícita** en los llamadores.
