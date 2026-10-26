# PROCEDIMIENTO DE REPARACIÓN DEL FK ESPURIO (NO EJECUTAR — requiere autorización)

> Acción **separada** y **autorizada**. **No** se ejecuta en esta fase. **No** es un cambio
> de política: es la corrección de un dato mal atribuido por un defecto de código ya
> corregido (`02` + `03`).

## Alcance

Corregir el `guia_processing_id` **espurio** de los retornos de cancelación creados por
`action_force_cancel` mientras el asistente llevaba `default_guia_processing_id` en el
contexto. Caso identificado: `stock.picking` **7813** (`guia_processing_id = 33152`).

## Precondiciones

* Parche `02_preventive_return_fk.diff` **aplicado** (evita nuevos casos).
* Confirmación (por evidencia) de que el retorno **no** es un ingreso de producción de la
  guía: su `origin_returned_move_id` apunta a un picking ajeno, y sus lotes pertenecen a
  otra cabecera (recepción). Ver `REPRODUCCION_CADENA_436_7813_7814.md`.
* Autorización escrita del responsable de datos/operaciones.

## Detección (solo lectura) — candidatos

Retornos (`origin` `Return of %`) con FK a una guía cuya cadena material NO es de la guía:

```sql
SELECT p.id, p.name, p.origin, p.guia_processing_id,
       c.name AS origen_returned_picking,
       c.reception_id AS origen_reception
FROM stock_picking p
JOIN stock_move m ON m.picking_id = p.id AND m.origin_returned_move_id IS NOT NULL
JOIN stock_move c ON c.id = m.origin_returned_move_id
WHERE p.guia_processing_id IS NOT NULL
  AND p.origin LIKE 'Return of %'
  AND (c.reception_id IS NOT NULL OR c.guia_processing_id IS NULL);
```

## Reparación (por ORM, transaccional y auditada)

```python
# Ejecutar SOLO con autorización, en la base objetivo, por el responsable de datos.
# 1. Snapshot previo (evidencia).
pick = env['stock.picking'].browse(7813)
antes = {'id': pick.id, 'name': pick.name,
         'guia_processing_id': pick.guia_processing_id.id}
# 2. Reparación mínima: quitar SOLO el FK espurio. NO se toca origin, moves, lotes,
#    ubicaciones, cantidades ni el histórico material.
pick.with_context(madenat_fk_repair=True).write({'guia_processing_id': False})
# 3. Auditoría firmada (snapshot + SHA-256), convención BT-01.
env['madenat.audit.log'].sudo().create({
    'action_type': 'deviation',
    'description': 'Reparación de FK espurio en retorno de cancelación %s '
                   '(pertenece a la cadena de la recepción, no a la guía).' % pick.name,
    'guia_processing_id': False,
    'audit_snapshot': json.dumps({'antes': antes, 'despues': {'guia_processing_id': False}}),
})
env.cr.commit()
```

> Nota: el `write` debe ser del FK **de retorno**, no de un ingreso de producción. No se
> usa `sudo()` para saltar permisos: se ejecuta con un usuario autorizado.

## Verificación posterior

1. El retorno 7813 conserva `origin`, `move` (14542) y sus 12 líneas de lote (2614–2625).
2. La cadena 436 → 7813 → 7814 sigue íntegra.
3. Para 33152: `_lifecycle_diagnosis()` ya no reporta bloqueadores materiales →
   `requirements_ok('A')` verdadero (en entorno de desarrollo).

## Reversión del procedimiento

* Volver a fijar `guia_processing_id` al valor del snapshot (requiere re-autorización).
* No hay migración de esquema; es un único `write` auditado.

## Si NO se autoriza la reparación

15183 permanece **bloqueada** (Opción B sin ejecutar). Es el estado seguro por defecto:
el parche **no** elimina nada con un FK vigente.
