# MADENAT — Auditoría Zarpe con Excepción B-01

```
Documento : AUDITORIA_B01_FASE_A
Bloque    : Sub-bloque 3 — Zarpe con excepción B-01
Fase      : A — Auditoría read-only, definición de política y diseño
Entorno   : madenat_test (odoo18_app Up · odoo18_db healthy · HTTP 200)
Fecha     : 2026-10-04 (15:30 UTC)
Método    : lectura de código + ORM read-only + SELECT. CERO escrituras.
Alcance   : NO se modificó código, NO se creó UAT, NO se ejecutaron acciones de negocio.
Dictamen  : A. APTO PARA DECIDIR POLÍTICA E IMPLEMENTAR B-01
```

---

## 1. Identidad, precheck y conservación

- **Repo** `/custom_addons`; **rama** `feat/guia-correccion-documental-preservada-20261002`;
  **HEAD** `34c81272bb07d48db98d73a7734c81a2a8e384fa`; `git status --porcelain` = **25 entradas
  (21 M + 4 ??)**, sin cambios (Rolleo + Borrador Seguro).
- **Runtime**: `odoo18_app` Up, `odoo18_db` healthy (postgres:15), HTTP 200. Módulos `installed`:
  base, stock, account, madenat_lumber_core, madenat_lumber_logistics,
  madenat_lumber_shipping_core, madenat_lumber_costing, madenat_lumber_billing,
  madenat_vendor_payment.
- **Línea base (posterior a UAT Borrador Seguro — sin cambios nuevos):**

| Modelo | N | Modelo | N |
|---|---:|---|---:|
| stock.move | 142 | lumber.export.shipment | 11 |
| stock.move.line | 209 | lumber.container | 11 |
| stock.picking | 27 | lumber.shipment.line | 5 |
| stock.quant | 169 | shipping.vessel | 5 |
| stock.lot | 126 | shipping.voyage | 1 |
| madenat.audit.log | 263 | madenat.sv.operation | 1 |
| madenat.sv.imputation | 1 | stock.lot.cost.line | 53 |
| lumber.shipment.cost.line | 0 | lumber.billing.consolidation | 0 |
| account.move | 1 | account.payment | 0 |

- **Integridad protegida (verificada intacta):** Shipment 1537 `in_transit`; Container 1509
  `shipped` (2 líneas `rebajado`); Picking 7065 `done`; Líneas 1880/1881 `rebajado`; Lotes
  15970/15971 `internal=0`, `customers=+0.144`; Lotes 15892/15894; Shipment 1528; Container 1500
  `rebajado`; Picking 7062; SV op 5822; Imputación 492; Guías 32298/32300. UAT Rolleo: vessels
  619/620, voyage 565, shipments 1644/1645/1646, containers 1629/1630/1631, audits 19699–19704.
  UAT Borrador Seguro: shipments 1704–1707, containers 1678–1680, audit 19742.
- **Hallazgo de estado:** `madenat.audit.log` con `action_type='deviation'` = **0 filas** →
  **B-01 nunca se ha ejecutado en esta base** (no hay evidencia histórica que proteger).

---

## 2. Flujo actual de zarpe y entradas UI/RPC

### 2.1 `lumber.export.shipment.action_set_in_transit` (lumber_export_shipment.py:464)
- **Grupos autorizados:** NINGUNO (sin `has_group`).
- **Estados de entrada:** ninguno validado.
- **Validación:** `pending = container_ids.filtered(state != 'rebajado')`.
- **Writes:** ninguno propio; si `pending` → **abre** `lumber.shipment.zarpe.wizard`;
  si no → `_set_in_transit()`.
- **Stock/lot/quant/SV/costos:** ninguno desde aquí.
- **Chatter/auditoría:** ninguno.
- **Rutas:** UI botón «Rematar Nave (Zarpe)» (`lumber_export_shipment_views.xml:33`,
  `invisible=state!='confirmed'`) y botón «En Tránsito» (`logistics_views.xml:53`). RPC:
  público (sin guion bajo) → invocable por `call_kw`.

### 2.2 `lumber.export.shipment._set_in_transit(exception_reason=None)` (lumber_export_shipment.py:488)
- **Grupos:** NINGUNO. **Estados de entrada:** NINGUNO validado (corre desde cualquier estado).
- **Validación:** `pending = container_ids.filtered(state != 'rebajado')`.
- **Si `pending`:** `_guard_deviation('B-01', …, reason=exception_reason, hard=False,
  extra={'pending_containers': …})` → **blando** (exige motivo; crea `madenat.audit.log`
  `action_type='deviation'` + chatter; **NO bloquea**).
- **Writes (P0):**
  - **`self.container_ids.write({'state': 'shipped'})` → TODOS los contenedores, incluidos los
    `pending` sin rebaja física (línea 507).**
  - `self.write({'state': 'in_transit', 'actual_departure': now})` (línea 511).
- **Stock/picking/lot/quant/SV/costos:** NO toca stock.move/line/picking/quant ni SV/costos.
- **Chatter:** «🚢 Zarpe Confirmado…» + «📊 Rendimiento Final de Nave…».
- **RPC:** método privado (guion bajo) → Odoo bloquea `_set_in_transit` por `call_kw`; pero es
  alcanzable por las vías públicas `action_set_in_transit` y el wizard (abajo).
- **Estados resultantes:** Shipment `in_transit`; Contenedores `shipped` (todos); Viaje sin cambio.

### 2.3 `lumber.shipment.zarpe.wizard` (wizards/lumber_shipment_zarpe_wizard.py)
- **`action_rebajar_y_zarpar` (l.43):** por cada contenedor pendiente `container.action_rebajar()`
  (con `savepoint`), y si todos quedan `rebajado` → `_set_in_transit()`. Rebaja = física
  (picking OUT + moves + quants).
- **`action_zarpar_con_excepcion` (l.73):** exige `reason`; llama
  `_set_in_transit(exception_reason=reason)` → **zarpe B-01 blando**.
- **Grupos:** NINGUNO en el wizard. **Sin `sudo()`/SQL/contextos forzados** (salvo el `sudo` del
  audit append dentro del mixin de desviación, código aprobado).

### 2.4 Otros puntos de entrada (no zarpe directo, relevantes)
- `lumber.container.action_rebajar` (:784) — grupos Operaciones/Jefatura/Gerencia → `_rebajar_container`.
- `lumber.shipment.rebaja.wizard` (rebaja por motonave; grupos Oper/Jef/Ger).
- `lumber.container.rollover.wizard` (:125) y `lumber.vessel.rollover.wizard`.
- `action_deliver` (:536) — **sin grupo**, exige `state='in_transit'`, escribe `delivered`.

---

## 3. Validación del defecto P0 `shipped` sin rebaja

**VIGENTE (confirmado en código, `lumber_export_shipment.py:507`).** Tras un zarpe B-01 (blando),
`_set_in_transit` marca como `shipped` **todos** los contenedores, incluidos los que nunca
salieron de bodega. Un contenedor puede quedar `shipped` con `rebaja_state != 'rebajado'`.

- **Campos que distinguen «rebajado físico» de «pendiente»:**
  - `lumber.container.state` (`rebajado` vs. resto);
  - `lumber.shipment.line.rebaja_state` (`pending`/`rebajado`/`reversed`);
  - `lumber.shipment.line.rebaja_picking_id` + `stock.picking.state='done'`;
  - `stock.quant` en ubicación interna (debe quedar 0) vs. Customers (salida).
- **¿Existe hoy un `shipped` sin rebaja?** NO en datos (0 desviaciones; B-01 no ejecutado). Pero
  el camino B-01 lo produce por diseño. Nota: los fixtures UAT (`shipment 1646/container 1631`,
  `shipment 1707/container 1680`) muestran ya la combinación **`in_transit` + contenedor no
  rebajado** (por creación directa, no por `_set_in_transit`).
- **Consumidores que interpretan `shipped` como rebaja (impacto del defecto):**
  1. `lumber_container._assert_rollover_eligible` (:760) → `rebaja_applied = state in
     ('rebajado','shipped')` → **bloquea Rolleo** (mensaje «ya tiene una rebaja física aplicada»).
  2. `lumber.vessel.rollover.wizard._container_block_reason` (:207) → **aborta el rolleo strict**
     («con rebaja física o ya embarcado»).
  3. `lumber.shipment.rebaja.wizard._classify` (:209) → trata el contenedor como «ya rebajado».
  4. **Borrador Seguro** `_return_to_draft_evidence` (:859) → `state in ('rebajado','shipped')` =
     evidencia física.
  5. `lumber_container.py:1378` dominio `('state','!=','shipped')` (contenedores «activos»).
- **Reportes:** contenedor `shipped` se contabiliza como embarcado aunque el stock no salió.
- **Disparo por UI y RPC:** SÍ — botón «Rematar Nave» (UI) y `action_zarpar_con_excepcion`
  (wizard, UI/RPC) sobre un embarque con pendientes.

---

## 4. Modelo de desviaciones B-01 y trazabilidad

- **No hay modelo dedicado.** El único soporte es `madenat.audit.log` + el mixin
  `madenat.deviation.mixin` (`madenat_lumber_core/models/madenat_deviation.py`).
- **`_guard_deviation(code, message, reason, hard=False, extra=None)` (l.31):**
  - `hard=True` o código en `DEVIATION_HARD_CODES` → `UserError` (bloquea).
  - **Blando (B-01 actual):** exige `reason`; crea `madenat.audit.log` con
    `action_type='deviation'`, `description='[B-01] … | Motivo: …'`,
    `batch_id=','.join(str(id) de self)` (= **id del Embarque**), `audit_snapshot` JSON
    `{code,message,reason,model,ids,extra,user,timestamp}`, `audit_hash` SHA-256, `user_id`;
    además publica **chatter** en el registro. **NO bloquea.**
- **Campos reales de una desviación:** sólo indirectos vía audit.log (action_type, description,
  batch_id, audit_snapshot, audit_hash, user_id, timestamp). **No** hay estado open/closed,
  aprobador, ni campos dedicados. La relación con Embarque/Contenedor/Motonave/Viaje es
  **sólo por `batch_id` (texto) y snapshot JSON**, no relacional.
- **Familia B-xx (embebida en comentarios/description, no en un modelo):** B-01 (zarpe con
  pendientes), B-03 (reversa con embarque entregado), B-06 (reversa con viaje cancelado),
  B-07 (costos distribuidos en rolleo).
- **Detección de B-01 por Borrador Seguro** (`lumber_export_shipment.py:900-904`):
  `action_type='deviation'` **y** `'[B-01]' in description` **y** `str(id) in batch_id.split(',')`.
  - **Fiabilidad:** por **texto** (frágil) + `batch_id`. Cualquier cambio de redacción del
    mensaje rompería la detección. `sudo()` de lectura para ver la bitácora.
  - **Sin estado:** una vez creada, la desviación es **permanente** → Borrador Seguro queda
    bloqueado para siempre (no hay forma de «cerrar» la B-01).
- **Consultar desviaciones por Embarque:** sólo por búsqueda sobre audit.log
  (description/batch_id). No existe acción/vista dedicada.
- **Aprobador/anexos:** no hay aprobador; anexos no ligados (ir.attachment aparte).

---

## 5. Matriz de estados y semántica

| Objeto | Estados actuales | Estado normal de zarpe | Estado B-01 actual | Problema semántico | Propuesta mínima |
|---|---|---|---|---|---|
| Shipment | draft, confirmed, in_transit, delivered, cancelled | `in_transit` (tras rebajar todos) | `in_transit` (blando, igual) | B-01 y zarpe normal son **indistinguibles** por `state` | Marcar condición excepcional (p. ej. contenedores pendientes visibles) sin nuevo estado |
| Container rebajado | empty→loading→loaded→sealed→**rebajado**→shipped | `rebajado`→`shipped` | n/a (no debería) | — | Mantener |
| Container pendiente | empty…sealed (+ **shipped** por P0) | n/a | **`shipped` sin rebaja** | `shipped` **miente**: implica salida de stock | NO forzar `shipped`; dejar estado consolidado + marca de pendiente |
| Voyage | draft, confirmed, departed, arrived, cancel | sin cambio | sin cambio | Viaje puede quedar no-terminal con pendientes | No cambia en Fase A |
| Deviation/Audit | (sin estado) action_type='deviation' | n/a | `deviation` (blando) | Sin ciclo open/closed; bloqueo permanente | Añadir semántica de estado/código estable **documental** (diseño) |

> No se introducen estados nuevos en esta fase; sólo propuestas mínimas a decidir.

---

## 6. Consistencia física actual vs. deseada

Para un **contenedor no rebajado** incluido en un zarpe B-01 (hoy):

| Concepto | Hoy (código actual) | Debería (A) | Debería (B) | Debería (C) |
|---|---|---|---|---|
| stock.quant interno | se mantiene | se mantiene (bloqueo previo) | se mantiene | se mantiene hasta regularizar |
| stock.quant Customers | 0 (no sale) | 0 | 0 | 0 (hasta rebaja extemporánea) |
| lot.volumen_restante_m3 | se mantiene | se mantiene | se mantiene | se mantiene/recomputa en regularización |
| line.rebaja_state | `pending` (se mantiene) | `pending` | `pending` | `pending`→`rebajado` al regularizar |
| line.rebaja_picking_id | vacío | vacío | vacío | se crea en regularización |
| container.state | **`shipped` (BUG P0)** | sigue consolidado; **no zarpa** | **no cambia a shipped/rebajado** | no cambia; luego rebaja |
| shipment.state | `in_transit` | `confirmed` (bloqueado) | `in_transit` con marca excepción | `in_transit`/`delivered` según corte |
| voyage.state | sin cambio | sin cambio | sin cambio | sin cambio |
| auditoría | chatter zarpe (+deviation) | bloqueo | `deviation` firmada | `deviation` + regularización |
| documentos | packing/BL normales | n/a | packing con marca excepcional | idem |
| costos | no se toca | n/a | **bloquea costeo** | requiere control de corte |
| factura/pago | no se toca | n/a | **bloquea** | condicionado |
| SV | no se toca | n/a | **bloquea retorno/imputación** | coordinar con Retorno SV |

---

## 7. Dependencias y gates

| Proceso | Código existente (real) | Reacción deseada ante B-01 |
|---|---|---|
| **Borrador Seguro** | Bloquea si `state!='confirmed'` y detecta B-01 por texto en audit.log (:900) | Correcto: B-01 (in_transit) ya no es 'confirmed'; y la desviación fuerza bloqueo permanente — **a decidir** semántica |
| **Rolleo de Motonave** | `_container_block_reason` (:207) bloquea `shipped`/`rebajado`; strict aborta todo | Deseado: bloquear B-01. **Pero** hoy bloquea por el `shipped` espurio del P0 (motivo equivocado) |
| **Rebaja / Reversa** | `_assert_rollover_eligible` (:760) y rebaja wizard (:209) tratan `shipped` como rebaja aplicada | Debe distinguir «pendiente» real; habilitar regularización |
| **Retorno físico / SV** | No ligado a zarpe | Debe coordinarse con Política C |
| **Entrega/Cierre** | `action_deliver` (:536) **sin guard de pendientes**; `period.close` GB-4 sólo mira costos `pending` en `in_transit` (:18) | Debe **bloquear** Entrega/Cierre si hay contenedores pendientes |
| **Costeo** | `action_distribute_costs` (:542) | Debe bloquear si hay pendientes (B-01) |
| **Facturación** | `lumber.billing.consolidation` | Bloquear si pendiente |
| **Pagos** | `madenat_vendor_payment` | Bloquear si pendiente |
| **Reportes** | Packing/Tarja usan `container.state` y lotes | Mostrar marca de excepción; no contar como exportado |

> Distinción: hoy sólo existen las guardas indicadas (varias motivadas por el `shipped` espurio);
> el resto es **comportamiento deseado** a diseñar.

---

## 8. Roles y segregación propuesta

**Actual (auditado):**

| Acción | Grupos actuales |
|---|---|
| `action_set_in_transit` / `_set_in_transit` / wizard de zarpe | **Ninguno** (cualquier usuario interno) |
| `action_deliver` | **Ninguno** |
| `action_rebajar` | Operaciones, Jefatura, Gerencia |
| `action_reverse_rebaja` | Jefatura, Gerencia |
| Rolleo (contenedor y motonave) | Operaciones, Jefatura, Gerencia |
| `action_draft` (Borrador Seguro) | Jefatura, Gerencia |

**Propuesta (diseño, no implementar):**

| Rol | B-01 |
|---|---|
| Operaciones | **Solicita/inicia** el zarpe con pendientes (motivo operativo). |
| Jefatura de Operaciones | **Valida** la evidencia operativa (contenedores pendientes justificados). |
| Gerencia | **Aprueba** la excepción si la política lo exige (p. ej. Política C con impacto financiero). |
| Auditoría | **Lectura/revisión** de la desviación firmada. |
| Contabilidad | **Informada** sólo si hay impacto financiero (Política C). |

Brecha a cerrar: hoy **cualquier** usuario interno puede zarpar (normal o B-01) sin grupo.

---

## 9. Comparativo de políticas A / B / C

### Política A — Prohibir B-01
Si hay cualquier contenedor no rebajado → **bloquear zarpe**; no crear desviación de éxito;
forzar rebaja o regularización previa.
- Pros: máxima seguridad de stock; semántica limpia (nada `shipped` sin salida).
- Contras: rigidez operativa; el negocio ya pidió «no bloquear al profesional» (D8).
- Impacto: anula `_set_in_transit` en pendientes; el wizard sólo ofrecería «Rebajar y zarpar».

### Política B — B-01 documental bloqueante
Permitir registrar el Embarque/Motonave como **excepción**, pero:
- **NO** cambiar `container.state` a `shipped`/`rebajado`;
- **NO** mover stock;
- crear **desviación B-01 firmada**;
- marcar **condición excepcional explícita**;
- **bloquear** Borrador Seguro, Rolleo, Entrega/Cierre y Costeo;
- permitir **sólo regularización posterior**.
- Pros: separa semántica (no miente el estado); trazabilidad fuerte; cumple «regla de seguridad».
- Contras: exige columna/registro de condición excepcional y gates nuevos.

### Política C — B-01 con regularización posterior
Incluye B y además define el **mecanismo autorizado** de rebaja extemporánea o retorno
(fecha efectiva, control de corte, costeo), coordinado con **Retorno SV**, **Costeo** y
**Entrega/Cierre**.
- Pros: cubre el caso real (rebajar después del zarpe) con control.
- Contras: mayor complejidad; depende de bloques aún no diseñados (Retorno SV, Cierre).

---

## 10. Matriz de decisión y recomendación

| Política | Seguridad de stock | Operación | Trazabilidad | Complejidad | Dependencias | Riesgo residual | Recomendación |
|---|---|---|---|---|---|---|---|
| **A. Prohibir** | Alta | Baja (rígida) | Media (no hay excepción) | Baja | Baja | Fuerza procedimientos externos al sistema | No preferida (contradice D8) |
| **B. Documental bloqueante** | Alta | Media | **Alta** (firmada + gates) | Media | Media (gates nuevos) | Requiere condición excepcional explícita | **RECOMENDADA** |
| **C. Regularización posterior** | Media-Alta | Alta | Alta | Alta | Alta (Retorno SV, Costeo, Cierre) | Ventana de inconsistencia si falla la regularización | Fase posterior (tras estabilizar Retorno SV) |

**Recomendación:** adoptar **Política B** como base inmediata, **corrigiendo primero el defecto
P0** (jamás forzar `shipped` sobre pendientes) y añadiendo: (1) una marca de **condición
Excepcional** en el Embarque/Contenedor; (2) **gates** explícitos que bloqueen Borrador Seguro,
Rolleo, Entrega/Cierre, Costeo, Facturación y Pagos mientras exista pendiente; (3) una
desviación B-01 **estable y consultable** (código estructurado + vínculo relacional). Diseñar la
**Política C** una vez exista **Retorno SV / Cierre**, sin improvisar rebaja extemporánea.

> La decisión final es **humana**; esta recomendación no se implementa en Fase A.

---

## 11. Lista mínima de archivos potenciales (para fases siguientes)

| Archivo | Cambio potencial (NO en Fase A) |
|---|---|
| `madenat_lumber_logistics/models/lumber_export_shipment.py` | Corregir `_set_in_transit` (no forzar `shipped`); gate de pendientes; marca de excepción; gates de Entrega/Costeo |
| `madenat_lumber_logistics/models/lumber_container.py` | `_assert_rollover_eligible` / estado; distinguir pendiente real |
| `madenat_lumber_logistics/wizards/lumber_shipment_zarpe_wizard.py` | Política A/B/C; marcar condición; no cerrar excepción en falso |
| `madenat_lumber_logistics/models/lumber_shipment_line.py` | Semántica `rebaja_state` vs. estado del contenedor |
| `madenat_lumber_core/models/madenat_deviation.py` | Desviación estructurada (código/estado/consulta), no sólo texto |
| `madenat_lumber_core/models/madenat_audit_log.py` | (Opcional) índices/consulta por Embarque; posible `event_type` (ver P2) |
| `madenat_lumber_logistics/wizards/lumber_vessel_rollover_wizard.py` | Gate B-01 en rolleo |
| `madenat_lumber_logistics/views/lumber_export_shipment_views.xml` | Visibilidad/botones/grupos; indicador de excepción |
| `madenat_lumber_core/security/madenat_security.xml` + ACL | Grupos por rol para zarpe/B-01 |
| Tests `madenat_lumber_logistics/tests/test_rebaja_contenedor.py` y nuevos | T-B01-1..10 |

---

## 12. Riesgos P0 / P1 / P2

**P0 (bloqueante)**
1. **`_set_in_transit` fuerza `container.state='shipped'` sobre todos los contenedores, incluidos
   los no rebajados** (`lumber_export_shipment.py:507`). Viola la regla de seguridad de B-01
   («nunca debe cambiar a shipped un Contenedor no rebajado»). Produce estados que **mienten**
   sobre la salida de inventario y contaminan Rolleo/Rebaja/Borrador/Reportes.

**P1 (alto)**
2. **Zarpe sin control de rol:** `action_set_in_transit`, `_set_in_transit`, el wizard de zarpe y
   `action_deliver` **no exigen grupo** ni validan estado de entrada → cualquier usuario interno
   puede zarpar (normal o B-01) y entregar.
3. **B-01 sin estado (no cerrable):** la desviación vive sólo como texto en `audit.log`; no puede
   abrirse/cerrarse. Como Borrador Seguro la detecta por texto, un B-01 **bloquea
   permanentemente** el retorno a borrador (sin remedio).
4. **Entrega/Cierre sin guard de pendientes:** `action_deliver` y `period.close` no bloquean por
   contenedores sin rebajar.
5. **Detección por texto:** `'[B-01]' in description` es frágil ante cambios de redacción.

**P2 (medio/bajo)**
6. **Semántica de `shipped` sobrecargada** (rebajado+embarcado vs. embarcado sin rebaja).
7. **Sin vínculo relacional de la desviación** con Embarque/Contenedor/Motonave/Viaje (sólo
   `batch_id`/JSON).
8. **Observación fuera de alcance:** `madenat.period.close.action_close_period`
   (`madenat_period_close.py:66`) escribe `event_type` en `madenat.audit.log`, campo que **no
   existe** en el modelo → ese flujo de cierre fallaría. No es B-01; reportar para backlog.
9. **`lumber_shipment_line._compute_export_volume` (:101)** compara `shipment_id.state` contra
   `['done','sealed','shipped']`, valores que el Embarque nunca toma → protección inerte.

---

## 13. Diseño de tests / UAT futura (no implementar todavía)

### Tests objetivo (T-B01-x)
| ID | Propósito | Esperado |
|---|---|---|
| T-B01-1 | Zarpe normal, todos rebajados | `in_transit`; contenedores quedan `shipped` legítimamente; 0 desviación |
| T-B01-2 | Pendiente + Política A | `UserError`; sin estado ni desviación |
| T-B01-3 | Pendiente + Política B | Contenedor pendiente **NO** pasa a `shipped`/`rebajado`; crea desviación firmada; 0 stock |
| T-B01-4 | B-01 bloquea Borrador Seguro | `UserError`; sin auditoría de retorno |
| T-B01-5 | B-01 bloquea Rolleo | `UserError`/strict abort; sin cambios |
| T-B01-6 | B-01 bloquea Entrega/Cierre | `UserError` |
| T-B01-7 | Permisos Operaciones/Jefatura/Gerencia/Auditoría | Según contrato de grupo |
| T-B01-8 | RPC no elude el guard | `AccessError`/`UserError`; sin cambios |
| T-B01-9 | Sin movimientos físicos/financieros | Δ0 en stock.move/line/picking/quant/lot/costos/facturas/SV |
| T-B01-10 | Regularización (sólo Política C) | Rebaja extemporánea autorizada y trazada |

### UAT aislada propuesta (diseño)
- **Embarque UAT normal** `UAT-B01-2026xxxx-OK` con **todos** los contenedores rebajados.
- **Embarque UAT B-01** `UAT-B01-2026xxxx-EXC` con **un contenedor pendiente** (fixture de estado,
  **sin** rebaja física ni stock).
- Verificar: estado de Shipment/Container/Voyage, `stock.quant` interno y Customers, `line.rebaja_state`,
  auditoría (deviation firmada + hash), permisos, y **gates** (Borrador/Rolleo/Entrega/Costeo).
- **Sin usar** registros históricos/UAT existentes; **sin alterar stock** en el escenario B-01
  documental.
- Usuarios existentes por rol (Jefatura/Gerencia para ejecutar; Operaciones para iniciar;
  Auditoría para leer). No crear usuarios.

---

## 14. Dictamen

> **A. `APTO PARA DECIDIR POLÍTICA E IMPLEMENTAR B-01`.**
>
> La auditoría read-only está completa: flujo de zarpe y entradas UI/RPC mapeados; **defecto P0
> confirmado** (`_set_in_transit` fuerza `shipped` sobre contenedores no rebajados,
> `lumber_export_shipment.py:507`); modelo de desviación B-01 auditado (blando, sin estado,
> detección por texto); estados/semántica, consistencia física, dependencias y roles documentados;
> y tres políticas A/B/C comparadas. **Recomendación: Política B** (documental bloqueante)
> corrigiendo primero el P0 y añadiendo marca de excepción + gates, dejando C para una fase
> posterior dependiente de Retorno SV/Cierre.
>
> No hay bloqueo de datos: histórica, UAT Rolleo y UAT Borrador Seguro intactas; línea base sin
> cambios; B-01 nunca se ha ejecutado en la base (0 desviaciones).

---

**Fin del informe. No se implementó nada, no se creó UAT, no se modificaron datos,
no se inició B-01.**
