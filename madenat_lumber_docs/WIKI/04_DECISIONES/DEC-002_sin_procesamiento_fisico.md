# DEC-002 — No Modelar Procesamiento Físico de Madera

**Fecha:** 2026-04-15
**Estado:** Aceptada
**Módulo afectado:** madenat_lumber_core

## Contexto

Se evaluó si MADENAT necesitaba modelar transformaciones físicas de madera (corte, cepillado, secado). El negocio compra madera ya procesada en aserraderos y la revende sin transformación propia.

## Decisión tomada

MADENAT no modela procesamiento físico. El flujo es: compra → recepción → stock → despacho → venta. No se instala el módulo `mrp`.

## Impacto

- No se instala `mrp`.
- Los lotes no se transforman ni fusionan.
- Flujo lineal sin manufactura.

## Criterio de revisión

Si MADENAT incorpora proceso de transformación o maquila, esta decisión se revisa e implica agregar `mrp`.

## Referencias

- [[reglas_lotes_trazabilidad]]
- [[flujo_recepcion_madera]]
- [[00_ARQUITECTURA]]
