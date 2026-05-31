# Flujo de Compra de Madera

**Módulo:** madenat_lumber_core
**Categoría:** Negocio
**Estado:** Activo
**Última actualización:** 2026-05-28

---

## Propósito

Documentar el ciclo completo desde que se genera una orden de compra de madera hasta que la mercancía queda recepcionada y trazada con lote en el sistema.

---

## Contexto

MADENAT compra madera a aserraderos proveedores. No realiza procesamiento físico. El flujo va desde la negociación y emisión de OC hasta la recepción física y registro de lotes en Odoo.

---

## Regla actual

1. Se genera Orden de Compra en Odoo (módulo Purchase) con proveedor y productos maderable.
2. Se confirma OC → queda en estado `purchase`.
3. Al llegar la madera, el operador crea una Recepción (Picking de tipo entrada).
4. Se asigna número de lote a cada línea de producto.
5. Se valida la recepción → stock queda actualizado.
6. La factura del proveedor se enlaza a la OC validada.

---

## Restricciones conocidas

- MADENAT no procesa físicamente la madera: no hay transformación de producto en el sistema.
- El lote es obligatorio en todo movimiento de madera. Sin lote no se valida ninguna recepción.
- Los productos de madera siempre deben tener tracking configurado en `by_lot`.

---

## Evidencia

- Modelo: `stock.picking`, `stock.move`, `stock.lot`
- Decisión: [[DEC-002_sin_procesamiento_fisico]]
- Flujo: [[flujo_recepcion_madera]]

---

## Relacionado

- [[flujo_recepcion_madera]]
- [[reglas_lotes_trazabilidad]]
- [[modelo_recepciones]]
- [[00_ARQUITECTURA]]
