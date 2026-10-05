# 18 — Consolidación y Rebaja de Contenedores y Naves

**Versión documental:** 1.2.0
**Fecha de actualización:** 2026-10-01  <!-- 2026-10-01 (2): §7.5 (imputación SV fuera de la exportación, AD-87), visibilidad SV por defecto (D9), §14.6 clasificación de bloqueos (AD-88); AD-83 reemplazada; AD-82/AD-84 alineadas -->
**Estado:** 🟢 **EN IMPLEMENTACIÓN** — Especificación de la **consolidación** (vincular/reservar) y la **rebaja** (descontar) de contenedores y naves. La **rebaja por contenedor** y **por nave** está **implementada** (AD-82 y AD-84 **APROBADAS**; AD-83 **APROBADA EN PRINCIPIO** sin extraer módulo). Ver §14 «Estado de implementación». **No sustituye** a `00_ARQUITECTURA.md`, `04_DECISION_LOG.md`, `12_FLUJOS_INGESTA.md`, `13_CONSOLIDACION_OPERATIVA.md` ni `17_CONSTITUCION_VOLUMENES.md`; los referencia.
**Responsable revisión:** 2026-10-01 — Alta del documento canónico `18` a solicitud del usuario (ciclo AD-81: «Consolidación: por contenedor y rebaja por motonave»). Registro de AD-85 y AD-86 en estado PROPUESTA.

> **Este documento es una ESPECIFICACIÓN.** Originalmente no implementaba código; desde el **2026-10-01**
> la **rebaja por contenedor y por nave** fue **implementada** en `madenat_lumber_logistics` (rama
> `feat/rebaja-contenedor-20261001`, BD `madenat_test`). Ver §14. Las decisiones que dependen del usuario
> quedan en §11 «Preguntas abiertas» **sin decidir por él**.

---

## 1. Alcance y glosario

### 1.1 Alcance

Especificar el flujo físico-trazable de **exportación**: cómo se **consolida** carga en contenedores y
embarques (vincular y reservar, sin descontar) y cómo se **rebaja** (descontar inventario) por
**contenedor** y por **nave/viaje** (masiva), sobre los modelos vigentes de
`madenat_lumber_logistics` y `madenat_lumber_shipping_core`, reutilizando `stock.lot`, el ledger SV
(`madenat.sv.operation`) y los estados existentes. Quedan **fuera de alcance** (diferidos por AD-81): lo
contable, la auditoría y la facturación.

### 1.2 Los tres usos de «consolidación»

El término **consolidación** aparece en el proyecto con **tres significados distintos**. Este documento
trata **exclusivamente el uso (1)**.

| # | Uso de «consolidación» | Dónde vive | Este documento |
|---|---|---|---|
| 1 | **Consolidación de carga de contenedores** — vincular y reservar lotes a un contenedor/embarque sin descontar stock | `lumber.container`, `lumber.container.lot.wizard`, `lumber.export.shipment` | ✅ **Sí** (§3–§9) |
| 2 | **Consolidación operativa de ingesta** (CANON/13) — unificar el flujo Producto/Procesados y la «consolidación administrativa» (AD-65) de la recepción a granel | `CANON/13_CONSOLIDACION_OPERATIVA.md`, `12_FLUJOS_INGESTA.md` §11 | ❌ No (solo se referencia) |
| 3 | **Consolidación de facturación** — agrupar líneas facturables de un embarque | `lumber.billing.consolidation(.line)` (F5, `madenat_lumber_billing`) | ❌ No (diferida por AD-81) |

### 1.3 Glosario

| Término | Definición operativa (MADENAT) | Modelo/campo base |
|---|---|---|
| **Consolidar** | Vincular y **reservar** lotes a un contenedor/embarque. **No descuenta inventario.** | `lumber.container.lot.wizard.action_assign` → `lumber.container.lot_ids` / `lumber.shipment.line` |
| **Rebajar** | **Descontar inventario** (salida nativa de stock) de los lotes consolidados, por contenedor o por nave/viaje. Ocurre en la **acción explícita de rebaja**, no en el zarpe (A-1, AD-82). | `_action_reduce_stock` (hoy en zarpe) → propuesta: acción de rebaja |
| **Rematar / Zarpe** | Evento logístico/documental que marca la salida de la nave. **Bajo la regla objetivo, no descuenta stock** (solo estado y documentos). | `lumber.export.shipment.action_set_in_transit` (estados `confirmed → in_transit`) |
| **Rolleo** | Reasignar un contenedor a un **nuevo embarque** conservando la operación y **sin rehacerla**, con **trazabilidad** (origen/destino de embarque, nave, viaje, booking, motivo, fecha, costos). | `lumber.container.rollover.wizard` |
| **Tarja** | **Documento de carga** por contenedor: detalle por paquete, dos volúmenes (EXPORT/NOMINAL), cabecera con nave, viaje y reserva. | XLSX `action_export_packing_list_xlsx` / PDF `action_report_lumber_container_packing_list` |
| **Etiqueta** | Identificador visible de un bulto. Para lotes de tarja, la etiqueta física del proveedor (`stock.lot.ref`/`supplier_label`/`external_labels`); para lotes Volumen, la etiqueta SV (`SV`+11 dígitos). | `stock.lot.name` / `stock.lot.ref` |
| **Paquete** | Bulto físico (tarja). En el contenedor se cuentan **etiquetas únicas** (`ref`), no líneas. | `lumber.container.packages` |
| **Embarque** | Conjunto de contenedores con un destino comercial y documental. | `lumber.export.shipment` |
| **Viaje** | Trayecto de una nave (buque + referencia de viaje). | `shipping.voyage` |
| **Booking / Reserva** | Reserva de espacio otorgada por la naviera, ligada a un viaje. | `shipping.booking` |

---

## 2. Puntos ACORDADOS

> **Origen:** sesión del **2026-10-01** con el usuario (documentada en `16_AUDITORIA_20261001.md` §1 y
> `AD-81` PROPUESTA, orden de trabajo «Consolidación: por contenedor y rebaja por motonave») y reglas
> **ACORDADO** de `17_CONSTITUCION_VOLUMENES.md` §3 (A-1 con `AD-82`..`AD-84` PROPUESTA). Se citan la
> **fecha** y el **origen** de cada acuerdo. Estado: **ACORDADO (2026-10-01) — pendiente de implementación.**

| # | Punto acordado | Origen |
|---|---|---|
| AC-1 | **Consolidar vincula y reserva, sin descontar.** Rebajar **descuenta** inventario. | Sesión 2026-10-01 |
| AC-2 | **Rebaja por contenedor** y **rebaja por nave/viaje** (masiva sobre los contenedores consolidados pendientes; la pantalla **lista contenedores y órdenes**). | Sesión 2026-10-01 (AD-81: «rebaja por motonave») |
| AC-3 | **La salida nativa ocurre al rebajar; el zarpe no descuenta.** | `17` §3 (A-1); AD-82 PROPUESTA |
| AC-4 | **Lotes SV con asignación parcial: sale exactamente el volumen asignado** (no `1`). | `17` §3 (A-2); AD-83 PROPUESTA |
| AC-5 | **La capacidad del contenedor se calcula en DISPONIBLE base nominal.** | `17` §3 (A-3) |
| AC-6 | **Volúmenes según CANON/17** (NOMINAL/DISPONIBLE/EXPORTACIÓN/OFICIAL). | `17_CONSTITUCION_VOLUMENES.md` §1 |
| AC-7 | **Rolleo = reasignar a un nuevo embarque con trazabilidad, sin rehacer la operación.** | Sesión 2026-10-01 |
| AC-8 | **Consignatarios: maestro con varios registros** (hoy solo Pinelli). | Sesión 2026-10-01 |

> **Nota de coherencia.** AC-3/AC-4/AC-5 son las reglas **A-1/A-2/A-3** ya registradas como **ACORDADAS**
> en `17` §3 y como **AD-82/AD-83/AD-84 PROPUESTA** en `04_DECISION_LOG.md`. Este documento **no las
> cambia**: las adopta como base y las aterriza en el modelo de consolidación/rebaja.


---

## 3. Modelo propuesto: flujo, estados, eventos de rolleo y campos nuevos

### 3.1 Flujo objetivo (reutilizando modelos existentes)

```
lotes en patio --consolidar--> contenedor CONSOLIDADO --rebajar--> contenedor REBAJADO
                                                        (salida nativa de stock en la rebaja)
                                                        |
                                   zarpe (rematar nave) +-->  ZARPADO --entregar--> ENTREGADO
                                                        |
                            rolleo (evento lateral) <---+---> nuevo embarque (traceable)
```

- **Consolidar** = vincular lotes a `lumber.container` (crea `lumber.shipment.line`), reservar
  disponibilidad, **sin** `stock.move`. Continúa usando `lumber.container.lot.wizard`.
- **Rebajar** = salida nativa de stock de los lotes del contenedor/embarque (acción nueva propuesta),
  con cantidad = volumen según tipo de lote (§4).
- **Zarpe** = `action_set_in_transit` deja de descontar (propuesta; hoy descuenta `1` por lote).
- **Rolleo** = evento lateral que reasigna el contenedor a otro embarque (§6), antes o después de rebajar.

### 3.2 Estados propuestos (mínima intervención sobre lo existente)

Se **reutilizan** los estados vigentes de `lumber.container.state`
(`empty, loading, loaded, sealed, shipped`, `lumber_container.py:238-250`) y de
`lumber.export.shipment.state` (`draft, confirmed, in_transit, delivered`), evitando crear un catálogo
paralelo:

| Estado de negocio (propuesto) | Estado técnico reutilizado | Cómo se alcanza |
|---|---|---|
| **consolidado** | `lumber.container.state = 'loaded'` | `action_complete_loading()` (hoy «Completado (Consolidado)», `lumber_export_shipment.py:457`) |
| *(opcional intermedio)* sellado | `lumber.container.state = 'sealed'` | `action_seal()` (existente) |
| **rebajado** | ⚠️ **estado propio** propuesto: `'rebajado'` — ver §11 (Q-06) | Nueva acción de rebaja (§4) |
| **zarpado** | `lumber.container.state = 'shipped'` + `lumber.export.shipment.state = 'in_transit'` | `action_set_in_transit()` (existente) |
| **entregado** | `lumber.export.shipment.state = 'delivered'` | `action_deliver()` (existente) |
| **rolleado** | ⚠️ **evento**, no estado lineal propuesto | Wizard de rolleo (§6) |

> **Decisión abierta (Q-06, §11):** si «rebajado» se materializa como estado nuevo del contenedor o como
> campo/fecha (`rebaja_date` + `rebaja_picking_id`). Este documento **no decide por el usuario**.


### 3.3 Eventos de rolleo (trazabilidad estructurada)

Hoy el rolleo **solo** deja constancia en el **chatter** del contenedor/embarque y **desvincula** el
contenedor del embarque (`lumber.container.rollover.wizard.action_confirm_rollover` →
`write({'seal_number': new_seal, 'state': 'loading', 'shipment_id': False, 'sealing_date': False})`,
`lumber_container_rollover_wizard.py:201-206`). No existe un registro consultable con origen/destino.

**Propuesta (mínima):** un registro **append-only** de rolleo (nuevo modelo `lumber.container.rollover`
o extensión estructurada del chatter) con, por cada evento:

| Campo propuesto | Tipo | Reutiliza |
|---|---|---|
| `container_id` | M2O `lumber.container` | existente |
| `event_date` / `user_id` | Datetime / M2O `res.users` | `fields.Datetime.now()` / `env.user` |
| `motive` / `other_motive` / `note` | Selection / Char / Text | **reutiliza** los del wizard |
| `origin_shipment_id` / `destination_shipment_id` | M2O `lumber.export.shipment` | existente |
| `origin_vessel_id` / `destination_vessel_id` | M2O `shipping.vessel` | existente |
| `origin_voyage_id` / `destination_voyage_id` | M2O `shipping.voyage` | existente |
| `origin_booking_id` / `destination_booking_id` | M2O `shipping.booking` | existente |
| `old_seal` / `new_seal` | Char | **reutiliza** los del wizard |
| `cost_snapshot` / `cost_impact_usd` | Text / Monetary | propuesto (§6.3) |

### 3.4 Campos nuevos mínimos y justificación

| Campo propuesto | Dónde | Tipo | Justificación (mínima) |
|---|---|---|---|
| `voyage_id` directo | `lumber.container` | M2O `shipping.voyage` (related/store) | hoy el viaje es indirecto (`shipment_id.vessel_id`); la **rebaja por nave/viaje** y sus filtros lo requieren |
| `booking_id` | `lumber.export.shipment` | M2O `shipping.booking` | hoy solo existe `booking_reference` (Char, `lumber_export_shipment.py:119`); falta el vínculo estructurado para tarja, rolleo y listados |
| `consignatario_id` | `lumber.export.shipment` | M2O `res.partner` | hoy `customer_id` («Cliente/Consignatario», `:144`) es un único registro (solo Pinelli); AC-8 exige maestro con varios |
| `buyer_po_reference` (P.O. del comprador) | `lumber.container` (o línea) | Char | trazabilidad comercial del pedido del comprador por contenedor — ver Q-01 (§11) |
| `shipping_line_id` (armador/naviera) | `lumber.export.shipment` | M2O `res.partner` | reutiliza `shipping.booking.shipping_line_id`; hoy no está en el embarque — ver Q-03 (§11) |
| `tare_weight_override_kg` | `lumber.container` | Float | `tare_weight_kg` es **compute** por tipo (`lumber_container.py:476-481`), no editable; la tara real puede diferir |

### 3.5 Qué se reutiliza (explícitamente)

`lumber.export.shipment`, `lumber.container`, `lumber.shipment.line`, `stock.lot` (con `lot_flow_type`,
`volumen_restante_m3`, `vol_shipment_m3`), `madenat.sv.operation` (ledger SV), `shipping.vessel` /
`shipping.voyage` / `shipping.booking`, el wizard `lumber.container.lot.wizard` y el wizard
`lumber.container.rollover.wizard`, y los estados de §3.2. **No** se plantea un módulo nuevo en esta fase
(ver AD-83: extraer la rebaja SV **después** de probar).


---

## 4. Reglas de rebaja

### 4.1 Cantidad por tipo de lote

| Tipo de lote (`stock.lot.lot_flow_type`) | Cantidad a descontar | Fuente del dato |
|---|---|---|
| **Tarja / normal** (`'tarja'` o vacío) | **Disponible base nominal** del lote en el contenedor | `stock.lot.volumen_restante_m3` = Σ `stock.quant.quantity` interno (`stock_lot.py:1022-1026`); base **NOMINAL** (`17` §1) |
| **Volumen / SV** (`'volume'`) | **Exactamente el volumen asignado** a ese contenedor (rebaja SV) | `madenat.sv.operation.rebaja_volume_m3` de la rebaja `applied` activa para (lote, contenedor) |

> Regla objetivo **A-2 / AC-4**. Hoy `_action_reduce_stock` mueve `product_uom_qty = 1` y `quantity = 1`
> por lote (`lumber_export_shipment.py:571,582`). Se propone mover el **volumen** correspondiente
> (nominal disponible o volumen SV asignado según el tipo).

### 4.2 Idempotencia por (contenedor, lote)

- Cada par **(contenedor, lote)** debe producir **una sola** salida nativa. Una segunda ejecución de
  rebaja **no** debe duplicar el descuento.
- **Patrón reutilizable:** el ya usado en el consumo de procesados — campo puntero + reutilización
  (`madenat.guia.processing.consumption_picking_id`, `madenat_guia_processing.py:4394-4400`). Se propone
  análogo en el contenedor/embarque (p. ej. `rebaja_picking_id`, `copy=False`, `index=True`).
- La **causa única de descuento** (AD-84 §4) queda satisfecha: la salida de rebaja no puede solaparse con
  el consumo de procesados (§5) ni repetirse por (contenedor, lote).

### 4.3 Ubicación destino de la salida

- Hoy es fija: `stock.stock_location_customers`
  (`lumber_export_shipment.py:563,575,585`). Se propone **parametrizarla** (config) — ver Q-04 (§11).

### 4.4 Reversa

- **Retorno nativo** (picking entrante inverso) **+ contrapartida en el ledger** (operación
  `rebaja_reverse`) — mismo patrón que `_reverse_consumption_picking`
  (`madenat_guia_processing.py:4523-4600`) y que `sv_reverse_allocation`
  (`madenat_sv_operation.py:957-981`).
- La reversa **no borra** historia: la salida original permanece en estado `done`; se crea el retorno y
  la operación SV opuesta ligada por `origin_operation_id` / `reversed_operation_id`.

### 4.5 Ventana de reversa y bloqueo de viaje cerrado

- **Ventana de reversa** (Q-05, §11): se propone permitirla mientras el contenedor **no** esté zarpado
  (`state != 'shipped'`) y el **viaje no esté cerrado**.
- **Bloqueo de viaje cerrado:** si `shipping.voyage.state in ('departed','arrived','cancel')`
  (`shipping_voyage.py:44-50`) o `lumber.export.shipment.state in ('in_transit','delivered')`, se
  **bloquea** rebaja y reversa (coherente con el bloqueo financiero ya existente:
  `lumber_container.py:936-951`, `lumber_container_rollover_wizard.py:149-162`).


---

## 5. Vía SV (Lote Volumen)

### 5.1 Servicio de rebaja con dos destinos

Se propone **un mismo servicio de rebaja** (reutilizando `madenat.sv.operation`) con **dos destinos**:

| Destino | Qué descuenta | API / ruta vigente |
|---|---|---|
| **(a) Consumo en proceso** (maquila / Producción) | Materia prima enviada a proceso | `madenat.guia.processing._get_or_create_consumption_picking()` → picking `outgoing` a `Virtual Locations/Production` (`madenat_guia_processing.py:4381-4521`) |
| **(b) Asignación a contenedor** | Volumen SV asignado a un contenedor/embarque | `madenat.sv.operation.sv_create_rebaja(...)` invocado desde `lumber.container._sv_allocate_lots` (`lumber_container.py:421-446`) |

Hoy **(a)** mueve stock (nominal) y **(b)** **no** toca `stock.quant` (solo ledger,
`17` §2.8; `madenat_sv_operation.py:14,922-955`). La especificación unifica el criterio: **todo descuento
SV tiene efecto físico y trazable** (AD-83).

### 5.2 Invariante del ledger vs quant (CANON/17 §3 y AD-84)

Deben cumplirse, de forma verificable:

1. `stock.lot.volumen_restante_m3 = Σ stock.quant.quantity` (ubicaciones internas, base NOMINAL).
2. `stock.lot.sv_available_m3 = sv_regularized_baseline_m3 − Σ rebajas activas` (aplicadas menos reversas).
3. Σ rebajas SV por contenedor/embarque ≤ volumen oficial (NOMINAL) del lote.
4. **Causa única** de descuento: rebaja (AD-82), consumo de procesados (AD-83) o ajuste autorizado —
   sin dobles descuentos.
5. **Concurrencia fail-closed**: las escrituras del ledger conservan la guarda de concurrencia
   (`_sv_concurrency_guard`, `madenat_sv_operation.py:945,971`); nunca se aplica «a medias».

### 5.3 Qué cambia en el consumo de procesados

- Hoy el consumo mueve `qty = qty_to_consume` (parcial, AD-66) o, en fallback, `lot.volumen_m3`
  (`madenat_guia_processing.py:4457-4461`).
- Con la vía SV unificada, un lote SV **parcialmente asignado a contenedores** debe consumir a proceso
  **solo el saldo restante** (oficial − rebajado), no el total: la cantidad sale del **saldo del ledger**,
  no de `volumen_m3`.
- El **asiento** del ledger (`sv_create_rebaja` con `destination_reference='Producción'`) y el
  `stock.move` deben ser **atómicos** y quedar ligados (misma transacción), de modo que la causa única de
  AD-84 §4 se mantenga.

> **Sin extraer módulo todavía.** AD-83 (módulo propio para la rebaja SV) queda **diferido**: primero se
> prueba la regla de descuento dentro del alcance actual (AD-81); la extracción se decide después.


---

## 6. Rolleo

**Principio (AC-7):** reasignar el contenedor a un **nuevo embarque** conservando la operación y **sin
rehacerla**, con trazabilidad de origen y destino (embarque, nave, viaje, booking, motivo, fecha, costos).

### 6.1 Rolleo ANTES de rebajar

- No hay salida nativa de stock todavía → **sin impacto en inventario**.
- El wizard desvincula el contenedor del embarque origen y lo deja listo para reasignar
  (`shipment_id=False`, `state='loading'`, `sealing_date=False`;
  `lumber_container_rollover_wizard.py:201-206`).
- **Cambia:** origen y destino del embarque registrados en el evento de rolleo (§3.3), sello nuevo,
  totales del embarque origen y destino; chatter de ambos.
- **No cambia:** lotes, quants, ledger SV (la reserva/consolidación se mantiene o se re-consolida).

### 6.2 Rolleo DESPUÉS de rebajar

- La salida nativa **ya ocurrió**: el rolleo **no rehace la operación** ni vuelve a descontar.
- **Reto:** los lotes/volúmenes rebajados deben «seguir al contenedor» al nuevo embarque **sin** nuevo
  `stock.move`; la trazabilidad (y, si aplica, el ledger SV con `destination_shipment_id`) debe
  actualizarse al destino.
- **Documentos que se actualizan:** contenedor (`shipment_id`, sello, estado), embarque origen y destino
  (totales, chatter), tarja/packing (regenerar por contenedor), y el registro de rolleo (§3.3).
- **Bloqueo vigente a respetar:** si hay costos distribuidos (`stock.lot.cost.line`) en el embarque
  origen, el rolleo se **bloquea** (`lumber_container_rollover_wizard.py:149-162`).

### 6.3 Cómo se registran los costos

- Hoy el rolleo **no** registra costos estructurados: solo el motivo en chatter.
- **Propuesta mínima:** el evento de rolleo (§3.3) guarda un **snapshot** del estado de costos
  (`cost_snapshot`) y, opcionalmente, un `cost_impact_usd` informativo. La **redistribución/reaplicación**
  de costos de embarque al nuevo destino queda **fuera de alcance** (diferida; ver Q-09 §11 y AD-81).

> **Nota:** la regla de bloqueo por costos distribuidos protege la integridad financiera; cualquier
> reasignación con costos exige **revertir los costos primero** (mensaje vigente del wizard).


---

## 7. Pantallas

Todas las pantallas **reutilizan** vistas/acciones existentes y añaden lo mínimo. Datos que alimenta cada una:

### 7.1 Consolidar contenedor

- **Base reutilizada:** formulario `lumber.container` (`view_lumber_container_form`) + botón
  `action_assign_lots` → wizard `lumber.container.lot.wizard`.
- **Datos que alimenta:** `selected_lot_ids` (de `available_lot_ids`), `sv_rebaja_volume_m3` (etiquetas
  SV), `container_id`. **Escribe** `lumber.container.lot_ids` (⇒ crea `lumber.shipment.line`) y pasa el
  contenedor `empty → loading`. **No** descuenta stock.
- **Dominio de lotes disponibles** (verificado, `lumber_container_lot_wizard.py:150-160`):
  `estado_trazabilidad ∈ {en_patio, procesado, recepcionado}`, `technical_validation='approved'`, no en
  otros contenedores activos, producto `product/consu`, con `reception_id` **o** `guia_processing_id`
  (y guía no `draft`/`cancelled`).
  - **Visibilidad SV por defecto (D9, AD-87):** los lotes **SV** (`lot_flow_type='volume'`) se **ocultan
    por defecto** en este asistente (elección de UX; **no se impide** seleccionarlos). El SV **no se
    exporta** (`19` §10.3).

### 7.2 Rebajar contenedor

- **Base reutilizada:** formulario `lumber.container`; **acción nueva** `action_rebajar` (propuesta),
  botón visible cuando `state = 'loaded'` (consolidado) y **no** zarpado.
- **Datos que alimenta:** lotes del contenedor (`lot_ids`), cantidad por tipo de lote (§4.1), ubicación
  destino (§4.3). **Escribe** la salida nativa + el estado `rebajado` (§3.2) + la rebaja SV (lotes SV).
- **Muestra:** capacidad/ocupación en **DISPONIBLE** (AC-5), volúmenes según `17`.

### 7.3 Rebajar por nave (masiva)

- **Base reutilizada:** `lumber.export.shipment` (nave/viaje) + **wizard nuevo** propuesto
  `lumber.shipment.rebaja.wizard`.
- **Selección:** **nave** (`shipping.vessel`) y **viaje** (`shipping.voyage`).
- **Lista:** **contenedores consolidados pendientes** de rebaja (filtrados por esa nave/viaje, estado
  `loaded`/no rebajado) **y sus órdenes** (P.O. del comprador — Q-01).
- **Datos que alimenta:** selección múltiple de contenedores; por cada uno aplica la **rebaja** (§4) con
  idempotencia por (contenedor, lote). Resume volúmenes EXPORT/NOMINAL y saldos SV.

### 7.4 Tarja por contenedor (documento de carga)

- **Base reutilizada:** XLSX `action_export_packing_list_xlsx` y PDF
  `action_report_lumber_container_packing_list` (`lumber_container_views.xml:218-229`).
- **Contenido requerido:**
  - **Detalle por paquete:** una fila por lote/etiqueta con sus dimensiones y piezas.
  - **Dos volúmenes:** EXPORT a la izquierda y NOMINAL a la derecha (conforme `17` §2).
  - **Cabecera:** nave, viaje y reserva (booking) — datos hoy dispersos (viaje en `shipment.voyage_id`,
    reserva solo como `booking_reference` Char; de ahí el campo `booking_id` propuesto, §3.4).

### 7.5 Imputación SV (procesados) — fuera de la exportación (AD-87)

- **El SV (Lote Volumen) no se exporta.** La consolidación/rebaja de este documento (§3–§9) opera sobre
  lotes de **tarja**; los lotes SV **no** son objeto de contenedor de exportación.
- El vínculo del SV con la madera procesada que retorna del procesador es la **imputación declarada**
  etiqueta→SV, cuya pantalla es el **Asistente de Imputación** al recibir la guía de procesados (no una
  pantalla de este documento). Norma y UX: `19_IMPUTACION_SV_Y_PROCESADORES.md` §6, §10.
- La **salida nativa del quant del SV** ocurre en la imputación (no en la rebaja de contenedor). Alinea
  AD-82 y **reemplaza AD-83** (`19` §4.4).


---

## 8. Permisos

### 8.1 Estado vigente (verificado)

- **No existe** un grupo funcional **«Logística»**. Las ACL de `madenat_lumber_logistics`
  (`security/ir.model.access.csv`) usan `base.group_user` y `stock.group_stock_manager`.
- Grupos MADENAT vigentes (`madenat_lumber_core/security/madenat_security.xml`):
  `group_madenat_operaciones`, `group_madenat_jefatura_operaciones`, `group_madenat_costos`,
  `group_madenat_contabilidad`, `group_madenat_gerencia`, `group_madenat_auditoria`,
  `group_madenat_admin`, `group_madenat_cost_auditor`.
- `lumber.shipment.cost.line` tiene **dos** ACL (mismo modelo, módulos distintos):
  `madenat_lumber_logistics` (`base.group_user` RWC / `stock.group_stock_manager` RWCD) y
  `madenat_vendor_payment` (`base.group_user` RWC / `base.group_system` RWCD).

### 8.2 Propuesta: grupo funcional «Logística»

- Crear `group_madenat_logistica` (categoría `module_category_madenat`), con
  `implied_ids` desde `group_madenat_operaciones` (o `stock.group_stock_user`), y su **jefatura**
  (`group_madenat_logistica_jefatura`) reutilizando el patrón de `group_madenat_jefatura_operaciones`.
- Migrar las ACL de logística de `base.group_user` / `stock.group_stock_manager` a los nuevos grupos
  (usuario/jefatura), **sin** otorgar costos, contabilidad ni auditoría.

### 8.3 Matriz de autorización propuesta

| Acción | Logística (usuario) | Jefatura Logística | Gerencia | Auditoría |
|---|---|---|---|---|
| Consolidar contenedor | ✅ | ✅ | ✅ | Lectura |
| Rebajar contenedor | ✅ | ✅ | ✅ | Lectura |
| Rebajar por nave/viaje (masiva) | ⚠️ (según Q-07 §11) | ✅ | ✅ | Lectura |
| Rolleo (antes de rebajar) | ✅ | ✅ | ✅ | Lectura |
| Rolleo (después de rebajar) | ⚠️ | ✅ | ✅ | Lectura |
| Reversa de rebaja | ❌ | ✅ | ✅ | Lectura |
| Bloquear/reabrir viaje cerrado | ❌ | ✅ | ✅ | Lectura |

> **ACL de `lumber.shipment.cost.line`:** se propone **unificar** la matriz (una sola ACL efectiva por
> modelo) usando los grupos `group_madenat_logistica` / `_jefatura` y `group_madenat_gerencia`, evitando
> la duplicidad actual entre `madenat_lumber_logistics` y `madenat_vendor_payment`.

> **Nota:** la propuesta de grupo y matriz se registra como **AD-86 PROPUESTA** (no aprobada).

> **Imputación SV (AD-87):** los roles de la **imputación** (Operaciones prepara/aplica/deja pendiente;
> Jefatura/Costos editan costo; Auditoría revisa desviaciones) se especifican en `19` §9. Reutiliza los
> grupos vigentes; no crea grupo nuevo.


---

## 9. Plan de pruebas

Ejecutable a nivel **RPC/HTTP** (Odoo 18 CE), con **aserciones de `stock.quant` antes y después**. Se
apoya en las suites vigentes de logística y SV como referencia de aislamiento
(p. ej. `madenat_lumber_logistics/tests/test_sv_allocation.py`,
`madenat_lumber_core/tests/test_volumen_restante.py`, `test_sv_rebaja.py`).

| ID | Escenario | Antes | Acción | Aserción (después) |
|---|---|---|---|---|
| T-01 | **Quants antes/después** (tarja) | `Σ qty` internos = D | Rebajar contenedor | `Σ qty` = D − disponible nominal rebajado |
| T-02 | **Idempotencia por (contenedor, lote)** | D | Rebajar contenedor 2 veces | `Σ qty` baja **una sola vez**; 2ª ejecución reutiliza/sale sin efecto |
| T-03 | **SV parcial** | saldo SV = S | Asignar/rebajar volumen V < S a un contenedor | sale **exactamente V**; `sv_available_m3` = S − V; quant −V |
| T-04 | **Contenedor mixto** (varias plantas y guías) | D_total | Rebajar contenedor | suma de descuentos = Σ por lote (tarja nominal + SV asignado); sin doble descuento |
| T-05 | **Rolleo antes de rebajar** | D | Rollear a nuevo embarque | sin cambio de quants; evento de rolleo con origen/destino; lotes intactos |
| T-06 | **Rolleo después de rebajar** | D−x | Rollear a nuevo embarque | quants **sin** nuevo descuento; trazabilidad del nuevo embarque; documentos actualizados |
| T-07 | **Reversa** | D−x | Reversar la rebaja | retorno nativo repone quant a D; ledger `rebaja_reverse` ligada; historia intacta |
| T-08 | **Varios consignatarios** | — | Crear embarques con consignatarios distintos | selección válida de `consignatario_id`; tarja con el consignatario correcto |
| T-09 | **Capacidad con DISPONIBLE** | disponible ≠ nominal | Consolidar hasta el límite | el asistente valida contra **DISPONIBLE base nominal** (AC-5), no export ni nominal bruto |
| T-10 | **Permisos** | — | Usuario sin grupo Logística intenta rebajar/rollear | `AccessError`/bloqueo según §8.3 |
| T-11 | **Rebaja por nave (masiva)** | D_total nave | Seleccionar nave+viaje y rebajar | descuenta cada contenedor pendiente; no toca ya rebajados; resumen correcto |
| T-12 | **Bloqueo de viaje cerrado** | viaje `departed` | Intentar rebaja/reversa | bloqueada (§4.5) |

**Invariantes a aseverar en cada test (AD-84):** `volumen_restante_m3 = Σ quant` interno;
`sv_available_m3 = baseline − rebajado activo`; Σ rebajas por destino ≤ oficial; causa única de descuento.

**Herramientas:** `HttpCase`/`TransactionCase` (RPC) y consultas de solo lectura a `stock.quant` para
fijar el estado inicial. Los tests deben declarar su **fase** explícitamente
(`@tagged('post_install', '-at_install', …)`, `INDICE_DOCUMENTACION.md` §9 / T5).

**Imputación SV (AD-87):** los escenarios de la vía SV (imputación etiqueta→SV, saldo por procesador,
merma documental) se detallan en `19` §15 (T-01..T-12); no duplican los T-01..T-12 de este documento.


---

## 10. Migración y compatibilidad

### 10.1 Datos existentes

- **Contenedores ya embarcados** (`state='shipped'`): su zarpe **ya descontó** `1` por lote
  (comportamiento vigente, §4.1). No se reprocesan. El `state='shipped'` se conserva como «zarpado».
- **Contenedores consolidados sin zarpar** (`loading`/`loaded`/`sealed`): no tienen descuento nativo; son
  candidatos directos a la nueva **rebaja** (§4/§7).
- **Lotes SV** con rebaja aplicada en el ledger pero **sin** efecto en `stock.quant`
  (`17` §2.8): quedan con saldo SV descontado y stock intacto. **Reencuadre 2026-10-01 (AD-87):** ese
  comportamiento correspondía a la **asignación SV a contenedor de exportación**, que **deja de aplicar**
  (el SV **no se exporta**); para **procesados**, la **imputación** sí descuenta el quant del SV
  (`19`, `17` §2.8). La nueva vía no reescribe historia; la alineación se resuelve en **nuevas**
  operaciones/ajustes autorizados (no por migración masiva de datos).

### 10.2 El zarpe actual

- `action_set_in_transit` **hoy** valida contenedores (`empty`/`loading` bloquean) y llama a
  `_action_reduce_stock` (`lumber_export_shipment.py:451-461`).
- **Compatibilidad propuesta:** bajo AC-3/AD-82, el zarpe **deja de descontar**. Para no romper embarques
  ya en curso, se propone una **transición controlada**: mantener el descuento en zarpe **solo** si el
  contenedor no pasó por la nueva acción de rebaja (bandera `rebaja_picking_id`/estado `rebajado`), y
  **desaconsejar** ese camino para datos nuevos. La eliminación definitiva del descuento en zarpe queda
  condicionada a la aprobación de AD-82 (Q-08 §11).

### 10.3 El asistente de rebaja SV

- El asistente vigente de rebaja/reversa de etiqueta SV (`madenat.sv.rebaja.*`, ledger `applied/reversed`)
  **se conserva**. La propuesta **no** lo reemplaza: lo **complementa** con el **efecto físico** (AD-83)
  y con la **idempotencia por (contenedor, lote)** (§4.2).
- Se mantienen las guardas de `stock.lot` protegidas (`SV_PROTECTED_FIELDS`,
  `madenat_sv_operation.py:994-1003`) y el campo de serialización `sv_balance_stamp`.

### 10.4 Compatibilidad de modelos y estados

- **Sin renombres.** Solo **añadidos** (§3.4) y, en su caso, un estado nuevo `rebajado` (§3.2, Q-06).
- Los campos propuestos son **opcionales** (no `required`) para no bloquear registros históricos.
- `lumber.shipment.cost.line` no cambia de estructura (solo su ACL, §8), por lo que costeo/facturación
  diferidos (AD-81) no se ven afectados.


---

## 11. PREGUNTAS ABIERTAS (sin decidir por el usuario)

> Ninguna de estas preguntas se responde en este documento. Se dejan **explícitas** para decisión del
> usuario; su resolución deberá registrarse como AD (aprobación) y actualizar este documento.

| ID | Pregunta abierta | Opciones (no decididas) |
|---|---|---|
| Q-01 | **P.O. del comprador** | ¿Es el P.O. **del comprador** (buyer PO)? ¿Guarda relación **1:1 con el contenedor** o con la línea/embarque? |
| Q-02 | **Nivel de detalle de etiquetas por paquete** | ¿Una etiqueta por lote, por paquete (`ref`), o varias etiquetas por lote? |
| Q-03 | **Armador/naviera** | ¿Se modela como `res.partner` en el embarque, reutilizando `shipping.booking.shipping_line_id`, o como catálogo propio? |
| Q-04 | **Ubicación destino de la salida** | ¿Fija `stock.stock_location_customers` o parametrizable (cliente/producción/tránsito)? |
| Q-05 | **Ventana de reversa** | ¿Hasta qué hito se permite reversar (antes de zarpe / antes de entregar / por período)? |
| Q-06 | **Estado «rebajado» propio** | ¿Estado nuevo en `lumber.container.state` o campo/fecha (`rebaja_date` + `rebaja_picking_id`)? |
| Q-07 | **Rebaja por nave: permiso y alcance** | ¿La ejecuta Logística usuario o solo Jefatura? ¿Incluye siempre todos los contenedores o selección manual? |
| Q-08 | **Recálculo de `vol_shipment_m3`** | ¿Se cablea el compute huérfano (`17` §6, F-03) o se conserva como copia congelada? |
| Q-09 | **Regla de los anchos 170/180 mm** | **Diferida** (no se especifica aquí); impacta la conversión documental/export. |
| Q-10 | **Facturación** | **Diferida por AD-81**; este documento no la aborda (uso (3) de «consolidación», §1.2). |

> **Nota Q-09:** la regla de los anchos 170/180 mm se registra como **diferida**, sin decidir su alcance;
> queda pendiente de especificación propia.

> **Imputación SV (AD-87):** las preguntas del frente de **imputación** (costo del SV, `action_type`,
> tolerancias, retorno a granel, umbrales de alerta) se registran en `19` §17 (Q-19-1..Q-19-8). Nota:
> Q-04 (ubicación destino) y Q-05 (ventana de reversa) aplican a la rebaja de **tarja**; su equivalente SV
> está especificado en `19`.


---

## 12. Riesgos y alternativas descartadas

### 12.1 Riesgos

| ID | Riesgo | Mitigación propuesta |
|---|---|---|
| R-01 | **Doble descuento** al rebajar y luego zarpar | Idempotencia por (contenedor, lote) §4.2; zarpe no descuenta (AC-3) |
| R-02 | **Stock residual** por movimiento de `1` por lote | Cantidad = volumen por tipo de lote §4.1 (A-2) |
| R-03 | **Desalineación ledger ⟷ quant** en lotes SV | Invariantes §5.2 (AD-84) + efecto físico atómico (AD-83) |
| R-04 | **Rolleo sin trazabilidad** post-rebaja | Evento de rolleo estructurado §3.3/§6 |
| R-05 | **Capacidad sobreestimada** (export vs disponible) | Validar en DISPONIBLE base nominal §7.1 (A-3) |
| R-06 | **Ambigüedad de «consolidación»** | Glosario de tres usos §1.2 |
| R-07 | **Pérdida de historia** si se «migran» datos | Solo nuevas operaciones; sin reescritura de historia §10 |
| R-08 | **Duplicidad de ACL** de `lumber.shipment.cost.line` | Unificación propuesta §8.3 (AD-86) |
| R-09 | **SV exportado por error** (tratar un lote SV como tarja) | El SV **no se exporta**; oculto por defecto en el asistente (§7.1/D9); su salida es la imputación (`19`) |
| R-10 | **Doble descuento del SV** (imputación + rebaja) | Causa única de descuento del SV = imputación; invariantes AD-84 ampliados (`19` §7.3) |

### 12.2 Alternativas descartadas (y por qué)

- **Mantener el descuento en el zarpe** — descartada: rompe la causa única de descuento (AD-82/AD-84);
  deja stock residual y desacopla hecho físico de movimiento.
- **Descontar `1` por lote** — descartada: no refleja el volumen y desalinea SV parcial (A-2/AD-83).
- **Escribir `stock.quant` por SQL** — descartada: viola las guardas de inventario y trazabilidad
  (`00_ARQUITECTURA`, AD-04); todo movimiento debe ser nativo y trazable.
- **Calcular capacidad con EXPORT o nominal bruto** — descartada: sobreestima disponibilidad
  (`17` §6, F-02); se usa DISPONIBLE base nominal (A-3/AC-5).
- **Extraer el módulo de rebaja SV ahora** — **diferida**, no descartada (AD-83: extraer **después** de
  probar la regla de descuento).

---

## 13. Mantenimiento y evidencia

- **Alcance:** documental. Esta sesión **no** modificó código, datos ni parámetros; no hubo commit ni push
  de código.
- **Efecto en otros documentos (ejecutado en la misma sesión documental):** alta de `18` en
  `INDICE_DOCUMENTACION.md`; alta de **AD-85** y **AD-86** (estado PROPUESTA) en `04_DECISION_LOG.md`.
- **Fuente de verdad ante contradicción:** `CANON/INDICE_DOCUMENTACION.md` §8 (`18` cede ante el documento
  canónico del tema y ante `04_DECISION_LOG.md`).
- **Nomenclatura:** español, con términos técnicos en inglés entre paréntesis, conforme a las convenciones
  del vault.
- **Actualización 2026-10-01 (AD-87/AD-88):** se añaden §7.5 (imputación SV fuera de la exportación), la
  nota de visibilidad SV por defecto (D9) y la **clasificación de bloqueos** (§14.6); AD-83 **reemplazada**
  por AD-87; AD-82/AD-84 **alineadas**. Referencias al frente de imputación: `19`.

**Evidencia (verificación de código realizada en esta sesión):**
- `madenat_lumber_logistics/models/lumber_container.py` (estados `238-250`; `_inverse_lot_ids` `330-405`;
  `_sv_allocate_lots` `421-446`; rebaja SV vía ledger; capacidad `484-496`; `unlink` `989-1004`).
- `madenat_lumber_logistics/models/lumber_export_shipment.py` (estados/acciones `424-600`;
  `_action_reduce_stock` `479-594`, movimiento `1` `571,582`; `customer_id` `144`; `voyage_id` `130`).
- `madenat_lumber_logistics/models/lumber_shipment_line.py`,
  `wizards/lumber_container_lot_wizard.py` (`action_assign` `311-427`),
  `wizards/lumber_container_rollover_wizard.py` (`action_confirm_rollover` `125-242`).
- `madenat_lumber_core/models/madenat_sv_operation.py` (`sv_create_rebaja` `922-955`;
  `sv_reverse_allocation` `957-981`; saldos `1005-1078`).
- `madenat_lumber_core/models/madenat_guia_processing.py` (`_get_or_create_consumption_picking` `4381`;
  `_reverse_consumption_picking` `4523`); `stock_lot.py` (`lot_flow_type` `358-366`;
  `volumen_restante_m3` `1022-1026`).
- `madenat_lumber_shipping_core/models/shipping_voyage.py`, `shipping_booking.py`, `shipping_vessel.py`.
- Documentos: `17_CONSTITUCION_VOLUMENES.md`, `16_AUDITORIA_20261001.md`,
  `13_CONSOLIDACION_OPERATIVA.md`, `04_DECISION_LOG.md` (AD-79..AD-84), `00_ARQUITECTURA.md`.


---

## 14. Estado de implementación (2026-10-01)

**Rama:** `feat/rebaja-contenedor-20261001` (desde `wip/ux-intake-acl-20261001`), BD `madenat_test`.
**Módulos tocados:** `madenat_lumber_logistics` (núcleo), `madenat_lumber_core` (tipos de auditoría + etiquetas).

### 14.1 Resuelto y verificado
- **AC-1 / AC-3** (consolidar no descuenta; el zarpe no descuenta; la salida ocurre al rebajar):
  `lumber.container.action_rebajar` → `_rebajar_container`; `lumber.export.shipment.action_set_in_transit`
  **ya no** llama a `_action_reduce_stock` (método **eliminado**) y **exige** contenedores `rebajado`.
- **AC-4** (SV parcial sale exactamente el volumen asignado): cantidad = `rebaja_volume_m3` de la operación
  SV `applied` ligada al contenedor.
- **AC-5** (capacidad en DISPONIBLE base nominal): `lumber.container.lot.wizard` usa `volumen_restante_m3`
  y excluye lotes sin disponible.
- **Estado propio `rebajado`** del contenedor y **persistencia por (contenedor, lote)** en
  `lumber.shipment.line` con **restricción única** (idempotencia).
- **Reversa**: retorno nativo + contrapartida SV (`sv_reverse_allocation`); **bloqueada** si el embarque
  está entregado o el viaje cancelado.
- **Auditoría**: `madenat.audit.log` con `action_type` `rebaja` / `rebaja_reverse` (aditivo).
- **Permisos**: grupos **existentes** (Operaciones / Jefatura / Gerencia) con **rechazo en servidor**
  (`_rebaja_require_group`); **no** se creó grupo nuevo (AD-86 sigue PROPUESTA).
- **Rebaja por nave** (asistente): selección nave/viaje, lista de contenedores pendientes por embarque,
  rebaja masiva **con savepoint por contenedor** e informe de éxitos/fallos.

### 14.2 Diferido / fuera de alcance (por decisión del usuario)
Facturación; regla +1/8" (anchos 170/180 mm); **P.O. del comprador**; consignatarios; `booking_id`;
armador/naviera; rolleo como evento; tarja por paquete; extracción del módulo SV.

### 14.3 Punto que requiere decisión
- **Q-07 (permiso/alcance de la rebaja por nave)**: sin decisión formal; se implementó como acción de
  **Jefatura de Operaciones / Gerencia** (provisional).

### 14.4 Hallazgo de implementación (requiere revisión)
- La restricción **`_check_lot_duplication`** de `lumber.container` impide que **un mismo lote** esté en
  **dos contenedores activos a la vez**. Por ello la prueba «mismo lote SV parcial en dos contenedores
  simultáneos» **no es representable**; se cubre con **dos etiquetas SV parciales** en dos contenedores
  (venta exacta por rebaja). Si el negocio requiere un lote en varios contenedores, debe resolverse antes
  de ampliar el flujo.

### 14.5 Evidencia
- Suite `madenat_lumber_logistics`: **32 pruebas, 0 fallas, 0 errores** (`TestRebajaContenedor`,
  `TestContainerLotWizardDisponible`, `TestConsolidationActionDomain`, `TestSvAllocation`).
- Regresión `madenat_lumber_core` (308), `madenat_lumber_intake` (395), `madenat_lumber_costing`,
  `madenat_lumber_billing`, `madenat_ingestion_engine`: **sin regresiones nuevas** (ver informe de sesión).

### 14.6 Clasificación de bloqueos (2026-10-01, AD-88)

Bajo el principio «**advertir, motivar, auditar**» (AD-88), se clasifican los bloqueos vigentes de esta rama.
Detalle consolidado en `19` §14.

| # | Bloqueo | Clasificación propuesta |
|---|---|---|
| B-01 | Zarpe con contenedores no rebajados | **B-01 bloqueante** (AD-94): excepción documental trazable; `open` hasta regularización posterior; no altera stock; bloquea Entrega; no equivale a Rebaja. R1/R4 posteriores |
| B-02 | Rebaja sin disponible (descontar más que el quant) | **Duro** (integridad técnica; quant nunca negativo). El exceso *nominal* sobre el saldo SV es advertencia + motivo |
| B-03 | Reversa con embarque entregado / viaje cancelado | **Duro**, con **override de Gerencia con motivo** como opción a decidir (Q-19-5) |
| B-04 | Saldo SV (Σ > saldo) | **Advertencia con motivo**; duro en el techo del quant |
| B-05 | Rol insuficiente | **Duro** (permisos por rol) |
| B-06 | Viaje cerrado | **Duro** (regla financiera) |
| B-07 | Costos distribuidos impiden rolleo | **Duro** (revertir costos primero) |
| B-08 | Lote duplicado en dos contenedores | **Duro** (técnico; H-N1) |

**Síntesis:** B-01 pasa a **B-01 bloqueante** (AD-94) y B-04 a **advertencia con motivo**; permanecen **duros** B-02, B-05, B-06, B-07, B-08;
B-03 queda duro con override de Gerencia sujeto a decisión. Los casos con motivo se registran en
`madenat.audit.log` (snapshot + firma).
