# MADENAT — Auditoría R2 Retorno Físico Total (FASE A)

- **Sub-bloque:** 4B — R2 (reversa física total de una rebaja validada).
- **Alcance de esta fase:** auditoría READ-ONLY + diseño técnico. **Sin implementación, sin UAT, sin movimiento de inventario.**
- **Fecha:** 2026-10-04.
- **Módulo foco:** `madenat_lumber_logistics` (helper), con dependencia `madenat_lumber_core` (ledger SV).
- **Regla de la fase:** no se editó ni ejecutó ningún helper, wizard, acción, servicio, SQL de escritura ni actualización de módulos. No se creó UAT. No se usaron ni modificaron los registros protegidos.

---

## 0. Resumen ejecutivo

El helper actual (`lumber.container.action_reverse_rebaja` →
`_reverse_rebaja_container` → `_reverse_rebaja_picking` + `sv_reverse_allocation`)
**es funcional para un retorno total simple y ya crea los movimientos con
`origin_returned_move_id`**, pero **no es todavía una R2 total robusta**:

1. **Idempotencia por TEXTO** (`origin='Return of <picking.name>'`) en lugar de
   por relación: riesgo de doble retorno o de retorno parcial.
2. **`_reverse_rebaja_picking` devuelve `False` silencioso** cuando el picking
   origen no está `done`; el contenedor y las líneas **igual se marcan como
   revertidos** → inconsistencia física/documental (stock sigue en Clientes,
   línea dice `reversed`, contenedor restaurado).
3. **No hay guarda de concurrencia** en la reversa física (solo la rama SV está
   parcialmente serializada por el lock del lote); dos usuarios simultáneos
   pueden duplicar el retorno.
4. **`_is_container_rebajado_fisico` sigue devolviendo `True` tras la reversa**
   (el picking OUT original permanece `done` y `rebaja_picking_id` no se limpia)
   → la clasificación de zarpe, la B-01 y la Entrega quedan alteradas.
5. **Sin gates B-01 / costos / facturación** en la reversa: revertir una rebaja
   de R1 no invalida el cierre `resolved`; revertir una rebaja con costos
   distribuidos/consolidación facturada no se bloquea.
6. **`stock.return.picking` nativo** aporta retorno total, lote, `return_id`
   relacional y `origin_returned_move_id`, pero **no valida** ni actualiza
   líneas/contenedor/SV/auditoría MADENAT (habría que añadir una capa).

**Dictamen: `APTO PARA IMPLEMENTAR R2 TOTAL` (opción R2-A), condicionado a cerrar
los P0 de esta auditoría.** Ver §11 y §13.

---

## 1. Identidad, precheck y conservación

### 1.1 Repositorio

| Ítem | Valor |
|---|---|
| Repo git | `custom_addons/` (raíz de git; **NO** es `odoo-18-ce/`) |
| Rama actual | `feat/guia-correccion-documental-preservada-20261002` |
| HEAD | `34c81272bb07d48db98d73a7734c81a2a8e384fa` |
| Último commit | `34c8127 fix(logistics): habilita reparto SV para Operaciones` |
| Working tree | **31 entradas** (23 ` M` + 8 `??`) — coincide con la línea base esperada |
| Diff acumulado | `23 files changed, 2355 insertions(+), 207 deletions(-)` |

Nota: el directorio de trabajo de la sesión (`/home/viruco/dev-stack/odoo/odoo-18-ce`)
**no** es la raíz git; la raíz es `custom_addons/`. El árbol de trabajo contiene
los artefactos de los sub-bloques 1–4A (Rolleo, Borrador, B-01, R1) ya UAT-aprobados.

### 1.2 Runtime y DB

| Ítem | Valor | Estado |
|---|---|---|
| Contenedor app | `odoo18_app` (imagen `odoo-18-ce-web`) | Up 3h |
| Contenedor DB | `odoo18_db` (postgres:15) | Up 3h (healthy) |
| DB | `madenat_test` (`db_filter = ^madenat_test$`) | OK |
| `addons_path` | `/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons` | OK |
| `madenat_lumber_logistics` | installed `18.0.1.6.0` (== `__manifest__.py`) | OK |
| `madenat_lumber_core` | installed `18.0.6.5.0` | OK |

### 1.3 Línea base global (lectura read-only)

| Tabla | Filas |
|---|---|
| `stock_move` | 143 (39 con `origin_returned_move_id`) |
| `stock_move_line` | 210 |
| `stock_picking` | 28 (5 con `origin LIKE 'Return of %'`, todas `incoming`, retornos de procesador) |
| `stock_lot` | 127 |
| `madenat_sv_operation` | **1** (`action_type=rebaja`, `state=applied`, id **5822**) |
| `madenat_audit_log` | 270 |

Auditorías relevantes: `rebaja`=4, `vessel_rollover`=2, `vessel_rollover_item`=4,
`b01_departure_exception`=2, `b01_regularization`=1, `b01_resolution`=1,
`shipment_return_to_draft`=1, `deviation`=2, `imputation`=1, `sv_operation`=1.
**No existe ningún `rebaja_reverse` en la DB ni ningún movimiento de retorno de
rebaja: la ruta R2 física nunca se ejecutó en runtime (solo en tests unitarios).**

### 1.4 Registros protegidos — verificación de existencia (sin modificar)

Máximos de id **coinciden exactamente con el UAT R1** (`picking 7238`, `move 13973`,
`move_line 12417`, `lot 16312`, `container 1888`, `shipment 1885`, `audit 19945`,
`sv_op 5822`). Verificados como existentes (`count=1`): pickings 7065/7062/7238,
moves 13973, move_line 12417, lots 16312/15970, containers 1888/1509, shipments
1885/1537, sv_op 5822. Los UAT histórica/Rolleo/Borrador/B-01/R1 están **intactos**.

- **B-01:** 13 embarques `none`, **1 `open`** (shipment 1868, `UAT-B01-…-EXCEPTION`),
  **1 `resolved`** (shipment 1885, `UAT-R1-…-SHIP`). **No hay `resolved` adicional**
  fuera del UAT R1. ✅
- **Líneas/estados:** `rebaja_state` → `rebajado`=5, `pending`=1, `reversed`=**0**.
  Contenedores → `loaded`=5, `loading`=4, `rebajado`=4, `shipped`=3.
- **Helpers R2 instalados:** `action_reverse_rebaja`, `_reverse_rebaja_container`,
  `_reverse_rebaja_picking`, `lumber.container.rebaja.reverse.wizard` presentes.

**Precheck: OK.** No se detectaron movimientos, retornos, `rebaja_reverse`, SV ni
costos no explicados. No procede ninguna acción correctiva.

## 2. Flujo R2 actual (auditoría de código)

### 2.1 `lumber.container.action_reverse_rebaja` — `models/lumber_container.py:923-956`

| Aspecto | Detalle |
|---|---|
| Grupos | `_rebaja_require_group('…jefatura_operaciones', '…gerencia')` → Jefatura/Gerencia. Operaciones **no**. |
| Estado de entrada | No valida estado aquí; delega en `_reverse_rebaja_container` (exige `state=='rebajado'`). |
| Gates | `delivered` (shipment `delivered`) o `voyage_cancelled` (voyage `cancel`) → si el usuario **no** es Gerencia lanza `UserError`; si es Gerencia **abre el wizard** `lumber.container.rebaja.reverse.wizard`. |
| Writes | Ninguno directo. |
| Salida | `True` (reversa directa) o `ir.actions.act_window` (wizard override). |
| UI | Botón «Revertir rebaja» (`views/lumber_container_views.xml:237-243`), visible si `state=='rebajado'`. |
| RPC | Expuesto como método público `action_reverse_rebaja` (llamable por RPC por cualquier usuario con ACL de escritura sobre `lumber.container`). |

### 2.2 `lumber.container.rebaja.reverse.wizard` — `wizards/lumber_container_rebaja_reverse_wizard.py:11-36`

| Aspecto | Detalle |
|---|---|
| Modelo | `TransientModel`, `container_id` (req), `reason` (req). |
| ACL | `security/ir.model.access.csv:20` → **solo `group_madenat_gerencia`**. |
| Acción | `action_confirm_override()` → `container_id._reverse_rebaja_container(override_reason=reason)`; notificación y cierre. |
| Auditoría | La deja `_reverse_rebaja_container` (`_guard_deviation` «B-03/B-06» + `_rebaja_audit('rebaja_reverse')`). |

### 2.3 `lumber.container._reverse_rebaja_container` — `models/lumber_container.py:1069-1113`

Secuencia exacta:

1. `if self.state != 'rebajado'` → `UserError` («Solo se puede revertir un contenedor rebajado»).
2. Gates `delivered`/`voyage_cancelled`: si aplica y no hay `override_reason` **o** el usuario no es Gerencia → `UserError`. Con override de Gerencia → `_guard_deviation('B-03'|'B-06', hard=False, reason=…)`.
3. `lines = self.line_ids.filtered(rebaja_state == 'rebajado')`; si vacío → `UserError`.
4. `for picking in lines.mapped('rebaja_picking_id'): self._reverse_rebaja_picking(picking)` — **ignora el valor devuelto**.
5. `for line in lines.filtered('rebaja_sv_operation_id'): madenat.sv.operation.sv_reverse_allocation(line.lot_id, container=self, reason=…)`.
6. `lines.write({'rebaja_state': 'reversed'})`.
7. `self.write({'state': self.state_before_rebaja or 'loaded'})`.
8. `message_post` («↩️ Rebaja revertida») + `_rebaja_audit('rebaja_reverse')`.

No usa `savepoint`; todo ocurre en la **misma transacción** que el botón/RPC.
No bloquea filas (no `FOR UPDATE`).

### 2.4 `lumber.container._reverse_rebaja_picking` — `models/lumber_container.py:1115-1165`

| Aspecto | Detalle |
|---|---|
| Guarda | `if not picking or picking.state != 'done': return False` (**silencioso**). |
| Idempotencia | `search([('origin','=','Return of %s' % picking.name), ('state','=','done')], limit=1)` → **por texto**; si encuentra algo `done`, devuelve el existente y **no crea nada**. |
| Tipo de operación | `stock.picking.type` con `code='incoming'`, `warehouse_id = picking.picking_type_id.warehouse_id`, `active=True`; si no existe → `UserError`. |
| Picking retorno | `create({picking_type_id, origin='Return of <name>', location_id = picking.location_dest_id (Customers), location_dest_id = picking.location_id (interno)})`. |
| Movimiento | Por cada `move` del picking origen con `state=='done'`: `stock.move.create({name, product, product_uom_qty=move.quantity or product_uom_qty, picking_id, location_id=move.location_dest_id (Customers), location_dest_id=move.location_id (interno), origin_returned_move_id=move.id, to_refund=True})`. |
| Línea | Por cada `move_line` del move: `stock.move.line.create({move_id, picking_id, product, lot_id, quantity=line.quantity, uom, location_id=move.location_dest_id, location_dest_id=move.location_id})` — **mismo lote**. |
| Confirmación | `action_confirm()` → `action_assign()` → `button_validate()` (resultado **ignorado**). |
| Retorno | El picking de retorno. |

**Observaciones:** (a) `origin_returned_move_id` **sí** se setea por move (relación
correcta). (b) La idempotencia del *picking* depende solo del texto `origin`. (c) El
`button_validate()` puede devolver acción (backorder/confirmación inmediata) sin que
el código lo verifique. (d) `location_id` a nivel *picking* usa `plan[0][3]` (fuente
del primer lote) al crear el OUT; si el contenedor mezcla ubicaciones internas, el
destino a nivel picking puede diferir del destino real por move (los moves sí son
correctos).

### 2.5 `madenat.sv.operation.sv_reverse_allocation` — `madenat_lumber_core/models/madenat_sv_operation.py:957-981`

- Dominio: `lot_id`, `action_type='rebaja'`, `state='applied'`, `reversed_operation_id=False` (+ `destination_container_id=self` si aplica).
- Si no hay origen → `return self.browse()` (**idempotente/no-op**).
- Con `_sv_concurrency_guard()` (savepoint + traducción de `SerializationFailure`):
  `create({action_type='rebaja_reverse', origin_operation_id=origin, reason, requested_by_id})` → `action_apply()`.
- `action_apply` fija `rebaja_volume_m3`/`new_volume_m3` = volumen de la rebaja origen (reversa opuesta) y marca el origen `state='reversed', reversed_operation_id=self` (`_sv_apply_side_effects`, 704-723; `_sv_finalize_apply`, 750-760).

### 2.6 Rutas UI/RPC resumidas

| Origen | Modelo/método | Permiso efectivo |
|---|---|---|
| Botón contenedor | `action_reverse_rebaja` | Jefatura/Gerencia |
| Wizard override | `action_confirm_override` | Gerencia (ACL del wizard) |
| RPC directo | `action_reverse_rebaja` | Jefatura/Gerencia (server-side) |
| SV UI | `madenat.sv.operation.action_open_reverse_wizard` (+ `madenat.sv.rebaja.reverse.wizard`) | ruta **separada** del ledger SV |
| Nativo | `stock.return.picking` | ACL estándar de stock (no usado por R2 hoy) |

## 3. Integridad de movimientos / lotes / estados (criterio B)

| Garantía exigida | Estado actual | Evidencia / brecha |
|---|---|---|
| Retorno de la **cantidad total** salida | ⚠️ Parcial | `qty = move.quantity or product_uom_qty` — correcto en el caso normal; si el OUT se validó con backorder (salida parcial), `move.quantity` refleja lo hecho y el retorno sería parcial **sin avisar**. |
| **Mismo `lot_id`** | ✅ Sí | Se copia `line.lot_id` de cada `move_line` origen. |
| **Origen `Customers`** | ✅ Sí | `location_id = move.location_dest_id` (Customers). |
| **Destino = ubicación interna de salida** | ⚠️ A nivel move ✅ / a nivel picking ⚠️ | Move: `location_dest_id = move.location_id` (fuente real). Picking: `location_dest_id = picking.location_id` (= fuente del **primer** lote); contenedores multi-ubicación pueden quedar incoherentes a nivel cabecera. |
| **`origin_returned_move_id` por move** | ✅ Sí | `models/lumber_container.py:1148`. |
| **No duplicación de move/move_line** | ⚠️ Solo por texto | La deduplicación del picking es por `origin='Return of …'`; no se comprueba que cada move ya tenga su retorno. |
| **No retorno si la salida no está `done`** | ❌ No bloquea | `_reverse_rebaja_picking` retorna `False` **silencioso**; `_reverse_rebaja_container` **igual** marca `line.rebaja_state='reversed'` y restaura `container.state`. → stock sigue en Clientes, línea miente. |
| **No retorno si ya existe retorno `done`** | ⚠️ Solo por texto | Funciona si el retorno previo quedó `done`; si quedó `draft/assigned/confirmed/cancel`, se crea **otro** retorno. |
| **Reconstitución de quants** | ✅ (por movimiento nativo) | No se verifica explícitamente; se confía en `action_confirm/assign/button_validate`. |
| **`line.rebaja_state` coherente** | ⚠️ | Se marca `reversed` aun cuando el retorno físico no ocurrió (ver fila anterior). |
| **Restauración de `state_before_rebaja`** | ⚠️ | Se restaura `loaded/sealed`; si el contenedor ya estaba `shipped` (zarpe), **pierde `shipped`** sin recompensación. |
| **Auditoría/hash** | ✅ | `_rebaja_audit('rebaja_reverse')` con snapshot determinista + SHA-256 (`_rebaja_snapshot`, 1167-1199). |

**Brecha estructural clave (P0):** `_is_container_rebajado_fisico`
(`lumber_export_shipment.py:557-564`) devuelve `True` si
`any(line.rebaja_picking_id.state == 'done')`. Como la reversa **no limpia**
`line.rebaja_picking_id` ni invalida el picking OUT, **un contenedor revertido
sigue clasificándose como «rebajado físicamente»** → afecta zarpe, B-01 y Entrega
(§6).

## 4. Idempotencia y concurrencia (criterio C)

### 4.1 Uso de `origin='Return of <picking.name>'`

El helper usa **texto** como única llave de idempotencia del picking de retorno
(`busca` por `origin` + `state='done'`). Comparado con alternativas relacionales
disponibles en Odoo 18:

| Mecanismo | Disponible | ¿Usado por el helper? | Comentario |
|---|---|---|---|
| `stock.move.origin_returned_move_id` | Sí (nativo, `stock_move.py:155`) | **Sí** (por move) | Corazón de la trazabilidad; no usado para deduplicar el picking. |
| `stock.move.returned_move_ids` | Sí (One2many inverso) | No | Permitiría detectar retornos parciales/totales por move. |
| `stock.picking.return_id` | Sí (`stock_picking.py:558`) | **No** (el helper no lo setea) | El nativo lo fija al copiar el picking; sería la llave relacional correcta. |
| `line.rebaja_picking_id` | Sí (custom) | Sí, pero no para idempotencia | Apunta al OUT, no al IN. |
| `madenat.sv.operation.reversed_operation_id` | Sí | Sí (rama SV) | Idempotencia SV correcta. |

### 4.2 Riesgos evaluados

| Escenario | Riesgo | Detalle |
|---|---|---|
| Colisión por texto | **Medio** | Dos contenedores con OUT homónimo generarían `origin` idéntico; poco probable (los `picking.name` son secuencia única) pero no imposible con datos legacy/purga. |
| Retorno duplicado parcial | **Alto** | Si el retorno previo **no** quedó `done`, el reintento crea un segundo picking IN → doble ingreso de stock. |
| Picking cancelado/incompleto | **Alto (P0)** | OUT no `done` → `return False` silencioso + línea marcada `reversed` (ver §3). |
| Reintento tras excepción | **Medio** | `button_validate()` puede lanzar (p. ej. reserva insuficiente en Clientes) → rollback total; pero si la excepción ocurre **después** de crear el picking IN (commit parcial no aplica en una sola transacción, sí hay rollback) el riesgo real es el no-`done`. |
| Dos usuarios simultáneos | **Alto** | Sin `FOR UPDATE` sobre `lumber.container`/`lumber.shipment.line`: dos transacciones REPEATABLE READ pueden leer `state='rebajado'` y ambas crear retorno. La rama **SV** mitiga parcialmente por el lock del `stock.lot` (`_sv_lock_operation_for_apply`, `_sv_concurrency_guard`), pero la rama **física (tarja)** queda sin serialización. |
| Lock del lote SV | **Mitigador existente** | `sv_reverse_allocation` usa savepoint + traducción de `SerializationFailure` → buena base reutilizable para R2. |

**Conclusión C:** la idempotencia actual **no es suficiente** para R2 total.
Debe migrarse a llave **relacional** (`stock.picking.return_id` +
`origin_returned_move_id`/`returned_move_ids`) y añadir **bloqueo de fila**
(`FOR UPDATE` sobre el contenedor) con reintento acotado.

---

## 5. SV y lotes `volume` (criterio D)

### 5.1 Elementos auditados

| Elemento | Ubicación | Comportamiento |
|---|---|---|
| `line.rebaja_sv_operation_id` | `lumber_shipment_line.py:230-233` | Se setea en la rebaja solo si el lote es `lot_flow_type='volume'` (`_rebaja_planned_lines`, 965-972). |
| `sv_reverse_allocation` | `madenat_sv_operation.py:957-981` | Crea `action_type='rebaja_reverse'` opuesta y revierte el origen. |
| `origin_operation_id` / `reversed_operation_id` | `madenat_sv_operation.py:164-178` | Trazabilidad 1-a-1; `ondelete='restrict'`. |
| `action_type='rebaja_reverse'` | `madenat_sv_operation.py:99` | Selección válida. |
| `lot.flow_type='volume'` | `stock_lot.py:358-366` (`lot_flow_type`) | Restringe la operación SV (`_check_sv_lot`, 246-253). |
| Saldo SV | `_sv_balance_values` (`madenat_sv_operation.py:1124-1148`) | `rebajado = Σ rebajas activas (excluye las ya reversadas)`; `available = baseline − rebajado`. La reversa **restituye** saldo. |

### 5.2 Qué se revierte y cuándo

- **Cuándo:** tras el retorno físico, en el **paso 5** de `_reverse_rebaja_container`
  (después de iterar los pickings). Misma transacción.
- **Qué:** la **rebaja activa** de la etiqueta para ese contenedor
  (`destination_container_id=self`). Crea `rebaja_reverse` y marca el origen `reversed`.
- **Anti-duplicado:** el dominio exige `state='applied'` y `reversed_operation_id=False`;
  tras la primera reversa el origen pasa a `reversed`, por lo que un segundo intento
  es **no-op** (`return self.browse()`). **Este es el patrón correcto** que la rama
  física debería imitar.

### 5.3 Consistencia volumen ↔ ledger SV

- El saldo SV se **deriva del ledger** (no de un campo mutable), luego es
  consistente por construcción.
- **Pero** el retorno **físico** y la reversa SV pueden **divergir** en el escenario
  del §3 (OUT no `done`): el físico no vuelve y el ledger SV **sí** se revierte →
  discrepancia stock interno vs. saldo SV.
- **Dependencia de imputación I2:** `madenat.sv.operation` también alimenta la
  imputación SV (I2). R2 solo revierte `rebaja`; **no** revierte la imputación
  (`imputation`). Si un contenedor ya fue imputado (I2), revertir la rebaja deja la
  imputación desacoplada. Debe tratarse como **gate/evidencia** de R2 (§11 P1).

### 5.4 Evidencia mínima requerida para R2 total (rama SV)

1. `origin_operation_id` de la `rebaja_reverse` = `rebaja_sv_operation_id` de la línea.
2. `rebaja_volume_m3` de la reversa = `rebaja_volume_m3` del origen.
3. `origin.state == 'reversed'` y `origin.reversed_operation_id == reversal`.
4. `lot.sv_available_m3` restituido (Δ = volumen rebajado).
5. Exactamente **una** `rebaja_reverse` por rebaja origen (idempotencia).

## 6. Dependencias B-01 / R1 / Entrega (criterio E)

### 6.1 Lo EXISTENTE (verificado en código y DB)

- **B-01:** estados `none/open/resolved` (`lumber_export_shipment.py:131`).
  `open` bloquea zarpe y Entrega; `resolved` **no** bloquea Entrega
  (`_b01_blocks_delivery`, 1069-1075) y **no** permite un nuevo zarpe (584-588).
- **R1:** `lumber.b01.regularization.wizard` (solo Gerencia) rebaja físicamente
  contenedores pendientes y crea auditoría `b01_regularization`; **no** cierra la
  B-01. El cierre es `action_resolve_b01_exception` (solo Gerencia) → `b01_resolution`.
- **Clasificación de rebaja física:** `_is_container_rebajado_fisico` (557-564)
  considera rebajado si `container.state=='rebajado'` **o** alguna línea
  `rebaja_state=='rebajado'` **o** algún `rebaja_picking_id.state=='done'`.
- **Entrega:** `action_deliver` (1077-1101) bloquea si B-01 `open` **o** hay
  contenedores pendientes (según `_classify_departure_containers`).
- **DB actual:** shipment 1885 = `in_transit` + `resolved`; shipment 1868 =
  `in_transit` + `open`. No hay reversas.

### 6.2 Comportamiento del helper R2 frente a B-01/R1 (PROPUESTA vs. hallazgo)

| Pregunta de la fase | Hallazgo actual (código) | Implicación |
|---|---|---|
| ¿Revertir un contenedor de B-01 `resolved` debe bloquear/reabrir/crear excepción? | **No hace nada especial.** `action_reverse_rebaja` solo mira `delivered`/`voyage_cancel`. Revierte directo si el usuario es Jefatura/Gerencia. | **Riesgo P0:** el embarque queda `resolved` pero con un contenedor **sin** stock en Clientes (ya devuelto) — el cierre B-01 se vuelve ficticio. |
| ¿Una reversa de R1 invalida el cierre B-01? | **No.** No existe relación B-01↔reversa ni invalidación. | Falta un evento/estado que marque la reapertura o una nueva excepción. |
| ¿Entrega debe bloquearse con reversa en proceso? | **No hay noción de «reversa en proceso»** (todo es síncrono en una transacción). Tras la reversa, `_is_container_rebajado_fisico` **sigue `True`** (picking OUT permanece `done`) → **la Entrega NO se bloquea** aunque el stock no salió. | **Riesgo P0:** Entrega permitida con mercancía de vuelta en bodega. |
| ¿Qué campos/estados comprobar? | Deberían comprobarse: `container.state`, `line.rebaja_state`, `line.rebaja_picking_id.state`, existencia de retorno `done`, `shipment.b01_exception_state`, `cost_distribution_state`, consolidaciones. Hoy solo se comprueba el primero de forma implícita. | Base del gate de R2. |
| ¿El B-01 original necesita relación con R1/reversa? | Hoy la relación es implícita (`b01_exception_audit_id`, `b01_regularization` audit, `b01_resolution` audit). **No** hay relación con el retorno físico. | Para trazabilidad de R2 se propone enlazar el `rebaja_reverse` audit con el cierre B-01. |

### 6.3 Decisión pendiente (separar existente de propuesta)

> **EXISTENTE:** no hay política ni código que relacione R2 con B-01/R1/Entrega.
>
> **PROPUESTA (a definir con negocio):** toda R2 total sobre un contenedor de un
> embarque con B-01 `resolved` (o `open`) debe **bloquearse** salvo **override de
> Gerencia con motivo** y, además, obligar a **reabrir B-01** (`resolved → open`)
> o crear una **nueva excepción**, e invalidar el estado «rebajado físico» del
> contenedor para que la Entrega vuelva a bloquearse. Esto es una **decisión de
> política**, no un hecho actual.

## 7. Comparativo: helper actual vs. `stock.return.picking` nativo (criterio F)

Fuente nativa (Odoo 18 CE, imagen `odoo-18-ce-web`):
`stock/wizard/stock_picking_return.py` (`stock.return.picking`,
`stock.return.picking.line`) + `stock/models/stock_picking.py`
(`_can_return`, `return_id`, `return_picking_type_id`).

| Criterio | Helper actual | `stock.return.picking` | Decisión propuesta |
|---|---|---|---|
| **Retorno total** | Sí (itera todos los moves done del OUT). | Sí, vía `_create_return`/`action_create_returns_all` (calcula lo no retornado). | Reutilizar el cálculo nativo de «pendiente de retorno». |
| **Retorno parcial** | No soportado (siempre full por línea). | Sí (cantidad editable por línea). | R2 = **solo total**; bloquear parcial (o derivar a R2 parcial futuro). |
| **Lote** | Copia `line.lot_id` (correcto). | Copia move lines (lotes) vía `move_id.copy` (correcto). | Equivalente; mantener lote explícito. |
| **`origin_returned_move_id`** | Seteado por move. | Seteado por move en `_prepare_move_default_values`. | Equivalente. |
| **Idempotencia** | Por **texto** `origin` + `done`. | **Ninguna explícita** (nativo permite múltiples retornos; el control es de negocio). | Usar `return_id` + estado + `returned_move_ids` (mejor que ambos). |
| **Ubicación retorno** | `move.location_dest_id → move.location_id` (per-move). | `picking.location_dest_id → return_type.default_location_dest_id` o `picking.location_id`. | Mantener per-move (más preciso). |
| **Factura/refund** | `to_refund=True` pero sin impacto (moves manuales sin SO/factura). | `to_refund` + integración anglo-sajona y `sale.return` si hubiera SO. | Sin efecto contable en MADENAT; mantener explícito y documentado. |
| **Integración Odoo 18** | Camino nativo (`action_confirm/assign/button_validate`). | Nativo y soportado (`return_id`, `_can_return`). | El nativo aporta `_can_return` (guarda `state=='done'`). |
| **SV/auditoría MADENAT** | **Sí** (`rebaja_reverse`, snapshot+hash, `sv_reverse_allocation`). | **No** (nativo no conoce SV/auditoría MADENAT). | Capa MADENAT obligatoria sobre el nativo. |
| **Mensajería** | `message_post` simple. | `message_post_with_source('mail.message_origin_link')` (enlace al origen). | Adoptar el `origin_link` nativo. |

**Lectura:** el nativo **no cubre** SV, auditoría, líneas ni contenedor MADENAT;
el helper **no cubre** idempotencia relacional, retorno parcial controlado ni el
`return_id`. Una R2 robusta **combina** ambos.

---

## 8. Política R2 total — alternativas y recomendación

### 8.1 R2-A — Fortalecer el helper actual

- Validaciones **relacionales** (no por texto): usar `origin_returned_move_id`,
  `returned_move_ids` y un nuevo `return_id`/flag en la línea.
- Idempotencia por **moves** y por estado (`reversed`), con `FOR UPDATE` del contenedor.
- Bloqueo/concurrencia: reutilizar el patrón savepoint + `SerializationFailure` ya
  probado en SV.
- Auditoría explícita `rebaja_reverse` (ya existe) + enlace a B-01.
- Mantener **retorno total por Contenedor** (una unidad = un contenedor).
- **Pros:** mínimo cambio, conserva el contrato y la auditoría actuales, encaja con
  R1/B-01, sin dependencia de la UI nativa. **Contras:** hay que escribir a mano las
  guardas que el nativo ya trae.

### 8.2 R2-B — Usar `stock.return.picking` + capa MADENAT

- Wizard nativo para el retorno total (`action_create_returns_all`).
- Capa MADENAT que valide (gates B-01/costos/facturación), ejecute el wizard,
  valide el picking retorno, actualice líneas/contenedor y dispare
  `sv_reverse_allocation` + auditoría.
- **Pros:** reutiliza el motor nativo (lotes, `origin_returned_move_id`, `return_id`,
  `origin_link`), menos código propio. **Contras:** el wizard nativo **abre** el
  formulario y espera validación del usuario (dos pasos, no atómico en un botón);
  habría que invocarlo en modo programático y **forzar** la totalidad; además
  sobrescribe `origin` con su propio texto `"Return of …"` (compatible).

### 8.3 Recomendación para la **primera entrega**

> **R2-A (fortalecer el helper actual)**, con dos “préstamos” acotados del nativo:
> (1) la guarda `_can_return`/`state=='done'` y (2) el `return_id` relacional.
>
> **Justificación:** R2 es **total por contenedor**, con requisitos MADENAT fuertes
> (SV, B-01, auditoría, idempotencia) que el nativo no cubre; el helper ya está
> instalado, auditado y probado en su camino básico. R2-B quedaría como evolución
> posterior si se requiriera retorno parcial o integración con SO/factura.

## 9. Roles (criterio H)

Propuesta de política (a confirmar con negocio). **Estado actual entre paréntesis.**

| Rol | Facultad propuesta | Estado actual |
|---|---|---|
| **Operaciones** | Solicita el retorno; **no** ejecuta. | `action_reverse_rebaja` **no** está disponible (exige Jefatura/Gerencia). El botón no es visible. **Alineado** salvo la “solicitud” (no existe flujo de solicitud explícito). |
| **Jefatura** | Ejecuta el retorno **total** si el Embarque **no** es terminal. | Hoy Jefatura ejecuta en cualquier estado salvo `delivered`/`voyage cancel` (donde solo Gerencia). **Falta** gate B-01 (`open`/`resolved`). |
| **Gerencia** | Aprueba retorno post-zarpe / B-01 / entregado / cancelado; aprueba cualquier cambio de estado B-01 asociado. | Hoy Gerencia usa el wizard para `delivered`/`voyage cancel`. **Falta** gate B-01 y cambio de estado B-01. |
| **Auditoría** | Lectura de la cadena salida → retorno → SV/auditoría. | No hay ACL de lectura específica del retorno; los `madenat.audit.log` son legibles según su ACL. **Parcial**. |
| **Contabilidad** | Valida impacto factura/pago **antes** del retorno si aplica. | **No existe** gate de facturación en la reversa (sí existe en zarpe/R1). **Brecha**. |

**Conclusión H:** los permisos actuales cubren «quién ejecuta», pero **no** los gates
de contexto (B-01, facturación, reapertura) que la política R2 total exige.

---

## 10. Lista mínima de archivos potenciales (implementación futura — NO ahora)

| Archivo | Rol previsto |
|---|---|
| `custom_addons/madenat_lumber_logistics/models/lumber_container.py` | Fortalecer `action_reverse_rebaja`, `_reverse_rebaja_container`, `_reverse_rebaja_picking` (idempotencia relacional, `FOR UPDATE`, guardas B-01/costos, gates). |
| `custom_addons/madenat_lumber_logistics/models/lumber_shipment_line.py` | Posible campo relacional `rebaja_return_picking_id` / `rebaja_reversed` para idempotencia. |
| `custom_addons/madenat_lumber_logistics/models/lumber_export_shipment.py` | `_is_container_rebajado_fisico` (invalidar tras reversa), política B-01↔reversa, Entrega. |
| `custom_addons/madenat_lumber_logistics/wizards/lumber_container_rebaja_reverse_wizard.py` (+ `_views.xml`) | Ampliar motivo/tipo de override y auditoría. |
| `custom_addons/madenat_lumber_core/models/madenat_sv_operation.py` | Reutilizar/afinar `sv_reverse_allocation` (idempotencia ya correcta). |
| `custom_addons/madenat_lumber_logistics/security/ir.model.access.csv` | ACL del wizard de reversa si cambia el rol. |
| `custom_addons/madenat_lumber_logistics/views/lumber_container_views.xml` | Visibilidad del botón según política. |
| `custom_addons/madenat_lumber_logistics/tests/test_rebaja_contenedor.py` (+ posible `test_r2_return.py`) | Tests T-R2-1..T-R2-10. |

---

## 11. Riesgos P0 / P1 / P2

### P0 (bloquean una R2 total)

1. **No-`done` silencioso:** `_reverse_rebaja_picking` retorna `False` pero la línea
   se marca `reversed` y el contenedor se restaura → estados inconsistentes con el
   stock real. (`lumber_container.py:1117, 1108-1109`).
2. **Borrado de la evidencia de rebaja:** tras la reversa, `_is_container_rebajado_fisico`
   sigue `True` (picking OUT `done`, `rebaja_picking_id` no limpiado) → clasificación
   errónea de zarpe, B-01 y **Entrega no bloqueada**. (`lumber_export_shipment.py:557-564`).
3. **Concurrencia:** sin `FOR UPDATE` sobre el contenedor → doble retorno posible
   con dos usuarios simultáneos (rama tarja).
4. **Gates ausentes:** reversa sin gate B-01 (`open`/`resolved`), sin gate de costos
   distribuidos ni de consolidación facturada → impacto financiero no controlado.

### P1 (deben resolverse en la primera entrega)

5. **Idempotencia por texto** en lugar de `return_id`/`returned_move_ids`.
6. **Restauración de estado** `state_before_rebaja` pierde `shipped` si el embarque
   ya zarpó.
7. **Desacople con imputación I2** (la reversa de rebaja no revierte la imputación).
8. **Reversión simultánea SV+físico** puede divergir si el físico falla (aunque la
   transacción única lo mitiga, el caso no-`done` la expone).

### P2 (mejoras)

9. `location_id` a nivel picking (primer lote) vs. per-move en contenedores multi-ubicación.
10. `button_validate()` sin verificación de resultado (backorder/acción).
11. `message_post` sin `origin_link` nativo.
12. Falta cobertura de test del camino SV (rebaja SV → reversa de contenedor).

## 12. Diseño de tests y UAT futura (criterio I)

### 12.1 Tests automatizados (a implementar en fase posterior)

| ID | Objetivo | Aserción núcleo |
|---|---|---|
| **T-R2-1** | Rebaja real total → retorno total. | Quant interno repuesto (0 → 3.0), Customers reducido (3.0 → 0), mismo `lot_id`. |
| **T-R2-2** | `origin_returned_move_id` correcto. | Cada move retorno apunta al move OUT; `move.returned_move_ids` coherente. |
| **T-R2-3** | Reintento no duplica. | Segundo `action_reverse_rebaja` → 0 pickings/moves/quants nuevos; 0 `rebaja_reverse` nuevas. |
| **T-R2-4** | Usuario no autorizado. | `AccessError` para Operaciones/plano (ya cubierto por `test_08`; ampliar a RPC y wizard). |
| **T-R2-5** | Origen no `done`/cancelado. | Debe **bloquear** (hoy no); sin cambios en línea/contenedor. |
| **T-R2-6** | B-01 `open`/`resolved` + retorno. | Política definida (bloqueo con override Gerencia / reapertura) testeada. |
| **T-R2-7** | Lote `volume` + SV rebaja. | Exactamente una `rebaja_reverse`; ledger consistente; `sv_available_m3` restituido. |
| **T-R2-8** | Error parcial → transacción íntegra. | Con excepción simulada, no quedan estados inconsistentes (rollback total). |
| **T-R2-9** | No usar texto `origin` como única prueba. | Con `origin` manipulado, la idempotencia **relacional** sigue evitando duplicados. |
| **T-R2-10** | Sin impacto fuera de gates. | `cost_distribution_state`, `account.move`, `account.payment`, `lumber.billing.consolidation` en delta 0; Entrega respeta gate. |

Base reutilizable: `tests/test_rebaja_contenedor.py` (fábricas `_make_guia`,
`_make_lot`, `_rebajable_container`, `_quant_of`, `_assert_audit_signed`) y
`sv_test_common`/`test_sv_reverse_ui` para el lado SV.

### 12.2 UAT futura (NO crear en esta fase)

```
- un lote UAT nuevo y stock interno nuevo (NO usar UAT R1: lot 16312 / container 1888 / shipment 1885);
- rebaja UAT real (picking OUT done → Customers);
- retorno total UAT (picking IN done → interna exacta);
- validación quant interno / Customers;
- cadena move origen → move retorno (origin_returned_move_id);
- lote, Container, Línea (rebaja_state), SV/auditoría (`rebaja_reverse`);
- idempotencia (reintento sin duplicados);
- permisos (Operaciones no ejecuta; Jefatura/Gerencia sí);
- no usar UAT histórica ni R1.
```

---

## 13. Dictamen

### Dictamen: **A. `APTO PARA IMPLEMENTAR R2 TOTAL`**

Con las siguientes **condiciones de entrada** (P0 de §11) que la implementación
debe cerrar y las que ya están resueltas:

**Ya resuelto por el helper actual (base válida):**
- Salida nativa por contenedor ya implementada y UAT-aprobada (R1/rebaja).
- Lote y `origin_returned_move_id` presentes en el retorno.
- Auditoría determinista `rebaja_reverse` con hash.
- Idempotencia y concurrencia **de la rama SV** correctas (`reversed_operation_id`,
  savepoint + `SerializationFailure`).
- Permisos de ejecución (Jefatura/Gerencia) y override de Gerencia para
  `delivered`/`voyage cancel`.

**Condiciones de entrada obligatorias (P0) antes de considerar «R2 total robusta»:**
1. Convertir el no-`done` silencioso en **bloqueo** (o reconciliación atómica).
2. Invalidar la evidencia de rebaja física tras la reversa (`rebaja_picking_id`
   y/o `_is_container_rebajado_fisico`) para no permitir Entrega con stock devuelto.
3. Idempotencia **relacional** (`return_id`/`returned_move_ids`) + `FOR UPDATE`.
4. Gates B-01/costos/facturación y decisión de reapertura B-01.

**No se detectó ninguna dependencia externa faltante** que impida avanzar
(`stock.return.picking` está disponible; ledger SV disponible; runtime y DB sanos;
línea base intacta). Por ello **no se declara `BLOQUEADO`**; el diseño propuesto
(R2-A) es ejecutable tal cual.

> **Recordatorio de alcance de esta fase:** aquí termina FASE A. No se implementó
> nada, no se creó UAT y no se movió inventario. No se usaron ni modificaron los
> registros protegidos (histórica, Rolleo, Borrador, B-01, R1).

---

*Fin del informe FASE A — R2.*







