# Flujo de Recepción de Madera

**Módulo:** madenat_lumber_core
**Categoría:** Negocio
**Estado:** Activo
**Última actualización:** 2026-05-28

---

## Propósito

Documentar el proceso exacto de recepción física de madera desde el aserradero, con asignación de lotes, validación de volúmenes y registro en Odoo.

---

## Contexto

La recepción es el evento central del flujo de negocio de MADENAT. Toda la trazabilidad de lotes comienza aquí. Un error en la recepción afecta inventario, reportes, despachos y facturación.

---

## Regla actual

### Estados del proceso

| Estado | Descripción |
|---|---|
| Borrador | Recepción creada, pendiente de iniciar |
| En proceso | Madera llegando, lotes siendo asignados |
| Validada | Stock actualizado, lotes confirmados |
| Cancelada | Recepción anulada, stock revertido |

### Pasos operativos

1. Operador abre el picking de entrada vinculado a la OC.
2. Registra cantidades reales recibidas (pueden diferir de OC).
3. Asigna número de lote a cada línea. El lote es obligatorio.
4. Si hay diferencia con la OC, se documenta en el chatter.
5. Se valida el picking → movimiento de stock confirmado.
6. El sistema genera el tracking de lote en `stock.lot`.

---

## Restricciones conocidas

- Sin lote asignado, la validación falla.
- Recepciones parciales generadas en backorders deben mantener el mismo lote raíz.
- No se puede modificar una recepción validada; se debe revertir con inventario manual.

---

## Evidencia

- Modelo: `madenat.recepcion`, `stock.picking`, `stock.lot`
- Archivo: `custom_addons/madenat_lumber_core/models/`
- Test: `CANON/03_TESTS.md`

---

## Relacionado

- [[flujo_compra_madera]]
- [[flujo_despacho_embarque]]
- [[modelo_lotes]]
- [[modelo_recepciones]]
- [[reglas_lotes_trazabilidad]]
