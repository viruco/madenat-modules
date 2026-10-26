# VERIFICACIÓN DE LA CADENA MATERIAL (post Fase B)

Solo lectura, contra `madenat_test`. Comparado con el estado "antes" de la revalidación:
**sin cambios**.

## Pickings

| id | name | origin | state | guia_processing_id | reception_id |
|---|---|---|---|---|---|
| 436 | EMB-00227 | 15183 | done | (NULL) | 1369 |
| 7813 | EMB-04201 | Return of EMB-00227 | done | **33152** | (NULL) |
| 7814 | WH/OUT/02754 | Devolución de EMB-04201 | done | (NULL) | (NULL) |

## Movimientos

| id | picking_id | origin_returned_move_id | quantity |
|---|---|---|---|
| 6420 | 436 | (NULL) | 50.8630 |
| 14542 | 7813 | 6420 | 50.8630 |
| 14543 | 7814 | 14542 | 50.8630 |

## Lotes y evidencia

| Indicador | Valor |
|---|---|
| Lotes 2614–2625 con `reception_id=1369` | 12 (todos) |
| `mail.message` guía 33152 | 5 |
| `ir.attachment` guía 33152 | 4 |
| Estado guía 33152 | `cancelled` |

## Diagnóstico del asistente (código nuevo, solo lectura, sin escrituras)

Ejecutado con `.new()` + `rollback` (proceso one-shot, `odoo18_app` detenido):

```
GUIA_EXISTS True
GUIA 33152 15183 cancelled service
OWN_PICKINGS        ['EMB-04201']
FOREIGN_PICKINGS    ['EMB-00227']      # 436: atribuido a otra cabecera, NO bloquea
AMBIGUOUS_PICKINGS  []
DIRECT_LINK_PICKINGS['EMB-04201']      # vínculo directo por FK
BLOCKERS_A ['- 1 albarán(es) vinculados a la guía (vínculo directo o lote propio) o con
             atribución textual ambigua pendiente',
            '  · 1 por vínculo directo (guia_processing_id): EMB-04201 [done]']
REQUIREMENTS_OK_A False
P436_FK   False
P7813_FK  33152                        # intacto, NO reparado
P7814_FK  False
ROLLBACK_OK
```

**Lectura del resultado:**
- El **único** bloqueador es el **vínculo directo `guia_processing_id` del 7813** (EMB-04201).
- El picking **436** ya **no** produce falso bloqueo por coincidencia textual (queda clasificado
  como **ajeno**: `foreign_pickings`).
- La guía **sigue existiendo** y `cancelled`; el FK **no** fue reparado; nada se borró.
- Cadena 436 → 7813 → 7814 **íntegra**.
