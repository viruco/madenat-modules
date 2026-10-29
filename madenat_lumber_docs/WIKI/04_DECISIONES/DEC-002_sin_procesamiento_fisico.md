# DEC-002 — No Modelar Procesamiento Físico de Madera

**Fecha:** 2026-04-15 (Actualizada: 2026-10-29)
**Estado:** ⚠️ Superada por CANON/13 (Procesamiento Externo / Tolling)
**Módulo afectado:** madenat_lumber_core, madenat_toll_processing

## Contexto

Se evaluó si MADENAT necesitaba modelar transformaciones físicas de madera (corte, cepillado, secado). El negocio compra madera ya procesada en aserraderos y la revende sin transformación propia.

## Decisión tomada

MADENAT no modela procesamiento físico interno ni instala el módulo `mrp`. El flujo comercial base es: compra → recepción → stock → despacho → venta.

## Evolución (Octubre 2026)

Esta decisión fue parcialmente superada con la creación del módulo `madenat_toll_processing` (documentado en CANON/13). Dicho módulo gestiona la **maquila externa (toll processing / servicios de terceros)** para dimensionado y tratamiento de paquetes sin requerir manufactura interna (`mrp`), mediante órdenes de servicio, consumo de lotes origen y alta de lotes resultantes.

## Impacto

- No se instala `mrp`.
- Procesamiento externo tercerizado gestionado vía `madenat_toll_processing`.
- Lotes trazables entre insumos entregados al maquilador y productos terminados recibidos.

## Criterio de revisión

Revisada y complementada en octubre de 2026 con `madenat_toll_processing` bajo CANON/13.

## Referencias

- [[reglas_lotes_trazabilidad]]
- [[flujo_recepcion_madera]]
- [[00_ARQUITECTURA]]
- `madenat_lumber_docs/CANON/13_FLUJOS_PROCESAMIENTO_EXTERNO.md`
