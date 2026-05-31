# Flujo de Despacho y Embarque

**Módulo:** madenat_lumber_core
**Categoría:** Negocio
**Estado:** Activo
**Última actualización:** 2026-05-28

---

## Propósito

Documentar el proceso de salida de madera desde bodega hacia puertos o clientes finales, con trazabilidad completa de lotes despachados.

---

## Contexto

El despacho es el evento de salida de inventario. MADENAT despacha a puertos (exportación) y a clientes locales. Todo despacho debe estar respaldado por una guía de despacho y un lote trazable.

---

## Regla actual

### Estados del despacho

| Estado | Descripción |
|---|---|
| Borrador | Despacho generado, pendiente de confirmar |
| Confirmado | Guía emitida, en espera de transporte |
| En tránsito | Carga en camino al destino |
| Entregado | Recepción confirmada por destinatario |
| Cancelado | Despacho anulado, stock devuelto |

### Pasos operativos

1. Se genera orden de venta o solicitud de despacho.
2. El sistema crea picking de salida con los productos y lotes disponibles.
3. El operador confirma los lotes a despachar.
4. Se genera la Guía de Despacho (documento `madenat_guia_processing`).
5. Se valida el picking → stock sale del inventario.
6. El lote queda marcado como despachado en su historial.

---

## Restricciones conocidas

- Todo despacho debe referenciar un lote activo y disponible en stock.
- La guía de despacho debe emitirse antes de la validación.
- El campo `name` en `madenat_guia_processing` fue auditado por duplicado: ver [[INC-001_campo_name_duplicado]].

---

## Evidencia

- Modelo: `madenat.guia.processing`, `stock.picking`
- Decisión: [[DEC-003_tracking_sin_chatter]]
- Incidente: [[INC-001_campo_name_duplicado]]

---

## Relacionado

- [[flujo_recepcion_madera]]
- [[modelo_despachos]]
- [[reglas_lotes_trazabilidad]]
