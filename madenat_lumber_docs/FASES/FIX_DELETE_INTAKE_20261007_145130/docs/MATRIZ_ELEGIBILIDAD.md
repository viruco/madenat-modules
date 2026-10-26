# MATRIZ DE ELEGIBILIDAD — eliminación (Modo A) de la guía

Criterio compartido por **diagnóstico y ejecución**: la atribución se resuelve por
**relaciones** (FK `guia_processing_id`, lotes propios, cadena documental) y no por
número textual. La coincidencia textual **sola** bloquea como *ambigua* (mensaje
específico), pero **no** atribuye concluyentemente cuando existe evidencia de pertenencia
a otro documento.

Clasificación de albaranes/movimientos (candidatos):

* **propios** → FK `guia_processing_id` **o** lote propio de la guía (`volume_source_guia_id`/`guia_processing_id`). `own_pickings`.
* **ambiguos** → `origin == guia.name`, sin FK ni lote propio, y **sin** evidencia de pertenencia a otro documento. `ambiguous_pickings`.
* **ajenos** → `origin == guia.name` pero **atribuidos positivamente a otro documento** (`reception_id` o lotes con `reception_id`). `foreign_pickings`.

## Casos

| # | Caso | Disposición | Fundamento / evidencia | Mensaje al usuario |
|---|---|---|---|---|
| **A** | Guía cancelada sin dependencias propias | **Se permite** | `state='cancelled'`, 0 lotes/pickings propios/movimientos/quants/ops/FK | (éxito) cierra el asistente y recarga la Consola |
| **B** | Documento ajeno con `origin` coincidente | **Se permite** (no bloquea) | El picking ajeno se atribuye a otra cabecera: `reception_id` set, o lotes con `reception_id` (auditoría F.3/F.4 del caso 436→recepción 1369) | Nota no bloqueante: «N albarán(es) … pertenecen a otro documento: no cuentan como dependencia» (`attribution_notes`) |
| **C** | Picking propio en borrador o cancelado | **Se bloquea** | Es un `stock.picking` vinculado a la guía (FK o lote); la doctrina exige «sin picking ni movimiento» en cualquier estado | `- N albarán(es) vinculados a la guía (vínculo directo o lote propio)…` |
| **D** | Movimiento propio realizado (aunque devuelto y saldo 0) | **Se bloquea** | El historial material no se destruye; el devuelto conserva `stock.move.line` con lote propio | `- N movimiento(s) de stock con lote propio de la guía` |
| **E** | Retorno propio directamente vinculado (FK) | **Se bloquea** | Vínculo directo `guia_processing_id` (cerrado el punto ciego: el retorno 7813 **ya no queda invisible**) | `· N por vínculo directo (guia_processing_id): EMB-… [estado]` |
| **F** | Vínculo directo aparentemente **contradictorio** (FK espurio) | **Se bloquea** + **requiere decisión de política** | El FK en el retorno se produce por fuga de contexto al crear el retorno (`default_guia_processing_id`), no porque el retorno sea un ingreso de producción | Igual que E (vínculo directo), con la corrección preventiva `02_preventive_return_fk.diff` |
| **G** | Lotes / reservas / valoración / costes / consolidación / embarque / contabilidad | **Se bloquea** (categorías materiales y financieras) | Reglas no negociables de AD-80 (CANON/04 §4.3) | `lote(s)`, `stock.quant`, `línea(s) de costo`, `capa(s) de valoración`, `consolidación(es)`, `embarque(s)`, `factura(s)` |
| **H** | Mensajes y adjuntos sin dependencias materiales | **Modo A (dev): NO bloquean**; **Modo C: bloquean** | Política documental vigente: `DEV_RELAXABLE_KEYS` solo en Modo A y solo en BD de test; la purga (C) exige sin evidencia | `attribution_notes` no aplica; en C: `mensaje(s) de chatter`, `adjunto(s) de evidencia` |

### Casos cruzados obligatorios

| Situación | Regla |
|---|---|
| Nº compartido guía ↔ recepción, con picking de la recepción | **B**: no bloquea (documento ajeno). Verificado: `test_b`, `test_k`. |
| Picking hallado por `origin` **y** por lote propio | **Cuenta una sola vez** (`test_k`). |
| Dependencia creada **después** del diagnóstico | **Bloquea en ejecución** por la revalidación inmediata (`test_h`). |
| Usuario sin `stock.group_stock_manager` | Bloqueado por las protecciones del core (`test_i`, `test_j`). No se debilita ningún permiso. |
| Sin confirmación (`acknowledge`) o sin motivo | Bloqueado (reglas vigentes del Modo A). |

## Frase «aún no está en stock»

Se verifica distinguiendo **saldo actual** (`stock.quant.quantity`), **reservas**
(`stock.move.line` con lote propio), **historial de movimientos** (`stock.move` con lote
propio), **retornos** (FK `guia_processing_id` + `origin` `Return of …`) y **valoración**
(`stock.valuation.layer`). Un saldo neto cero **no** implica ausencia de historial: el
caso D/específico lo trata de forma explícita.
