# MADENAT — Manual Operativo Entrega 1
## Recepción, Inventario, Bodega, Logística, Embarque y Reportería (Odoo 18 CE)

```
Documento : MANUAL_OPERATIVO_ENTREGA_1
Versión   : 1.0 (2026-10-05)
Alcance   : Entrega 1 — Operación física y logística completa.
Fuera     : Costeo, Valorización, Facturación, Pagos, cierre financiero (Entrega 2).
Base      : madenat_test · odoo18_app · Odoo 18 CE · madenat_lumber_core 18.0.6.5.0
```

> **Principio operativo.** La realidad física se gobierna por **stock nativo, lotes,
> ubicaciones, pickings, movimientos y trazabilidad logística**. La documentación tardía
> genera **backlog, alertas, responsable y escalamiento**; **no bloquea** la operación
> física/logística. Costeo, Billing y Pagos son **posteriores** al Embarque/Zarpe y **no**
> modifican retroactivamente stock, lotes, rebaja, zarpe, B-01, retorno ni Entrega.

---

## 1. Roles y perfiles (quién es quién)

| Rol (grupo MADENAT) | Hereda | Puede operar (Entrega 1) |
|---|---|---|
| **Operaciones** (`group_madenat_operaciones`) | `stock.group_stock_user` | Crear/procesar/validar guías y recepciones, ingreso de madera, stock, contenedores, embarques, rebaja, zarpe. |
| **Jefatura de Operaciones** (`group_madenat_jefatura_operaciones`) | `group_madenat_operaciones` | Todo lo de Operaciones + supervisión, catálogos, tableros de recepción y listados de guías procesadas. |
| **Gerencia** (`group_madenat_gerencia`) | Operaciones + Costos + Contabilidad | Supervisión global, dashboard gerencial, **regularización B-01 (R1)** y **waiver de Entrega**. |
| **Auditoría** (`group_madenat_auditoria`) | `base.group_user` | **Solo lectura** de trazabilidad/backlog; **no** crea/valida/procesa. |
| **Costos** (`group_madenat_costos`) | `base.group_user` | Fuera de alcance Entrega 1 (costeo). |
| **Contabilidad** (`group_madenat_contabilidad`) | Costos + `account.group_account_manager` | Fuera de alcance Entrega 1 (billing/pagos). |
| **Usuario interno** (`base.group_user`, sin grupos MADENAT) | — | **Lectura general**; **bloqueado** para crear/editar/validar/procesar/reabrir/cancelar guías y recepciones. |

> **Regla dura (Fase C.1).** El rol operativo efectivo es
> **Operaciones / Jefatura de Operaciones / Gerencia**. Cualquier otro usuario interno
> recibe `AccessError` ante cualquier operación de ingreso/recepción/guía — **incluido
> RPC/ORM directo, importación, wizard y contexto forzado**.

---

## 2. Inicio de sesión por rol

1. Abrir el navegador en `http://<host>:8069/web/login`.
2. Iniciar sesión con el usuario corporativo asignado.
3. La aplicación **MADENAT Lumber** aparece en el lanzador de apps.
4. La barra superior expone, según el rol:
   - **Operaciones** → menú `📦 Operaciones` (entrada operativa: **Ingreso de Madera**).
   - **Logística** → menú `Logística Exportación` (Embarques, Consolidación, Contenedores, Rebaja).
   - **Jefatura** → además `📥 Ingreso de Guías`, `Guías Procesadas`, **Tablero de Recepciones**.
   - **Gerencia** → `📈 Gerencia` (Dashboard Gerencial, Trazabilidad 360).
   - **Todos** → `📊 Reportes y Listados` y `⚖️ Auditoría → Trazabilidad 360°` (según grupos).

> Un usuario sin rol MADENAT operativo **no verá** los menús de ingreso ni podrá ejecutar
> sus acciones, aunque conozca la URL (el control es de servidor, no de UI).

---

## 3. Recepción e ingreso (Ingreso de Madera)

**Ruta:** `📦 Operaciones → Abastecimiento → 📥 Gestión de Entradas → Ingreso de Madera`.

1. Pulsar **Nuevo ingreso** (abre `madenat.lumber.intake.wizard`).
2. Registrar **proveedor** y **número de guía**; adjuntar **PDF de guía** y **Packing (Excel)**.
3. El sistema **parsea el Packing** y crea las líneas/lotes con volúmenes:
   - `vol_purchase_m3` (nominal/compra), `vol_shipment_m3` (exportación), `vol_documental_m3`
     (declarado en packing) y dimensiones.
4. Revisar y ajustar (si procede) en la **consola de Ingreso de Madera**
   (`madenat.lumber.intake.console`, solo lectura consolidada).
5. **Procesar** y **Validar** la guía (`action_validate`): el sistema crea **lote/tarja**,
   **picking IN** en estado `done`, **movimientos** y **quants internos** positivos.
6. La **trazabilidad** (proveedor, guía, ubicación/patio, volumen) queda registrada.

**Regla:** la falta de un documento (factura/OC) **no bloquea** la validación física; se
registra como pendiente documental (§6) y se resuelve aguas abajo.

---

## 4. Bodega, stock y lotes

- **Fuente de verdad física:** `stock.quant` con `quantity > 0` en ubicaciones internas.
- **Capa de negocio del lote:** nombre, guía, proveedor, OC, subproducto, dimensiones,
  volúmenes (nominal/embarque/documental).
- **Ubicaciones/Patios:** `Configuración → 🏗️ Patios de Recepción` (ubicaciones internas).
- **Ajustes físicos:** `📦 Operaciones → Control de Lotes → ⚖️ Ajustes Físicos (Stock)`
  (requiere perfil de jefe de stock). Registra el conteo físico y la diferencia.

---

## 5. Guías y corrección documental (CDP-V1)

- **Guías Procesadas** (Jefatura): `📦 Operaciones → 📥 Gestión de Entradas → 🏭 Guías Procesadas`.
- **Corrección documental preservada (CDP-V1):** corrige datos **documentales** (p. ej. adjunto
  de guía, número de OC documental) **sin alterar el stock** ni reabrir la realidad física.
  Se registra como **desviación auditada** (hash SHA-256 + snapshot before/after).
- La guía **permanece validada**; lotes, pickings y quants **no cambian**.

**Cuándo NO usar CDP-V1:** si hay que corregir **realidad física** (volumen físico, piezas,
lote), usar la **reapertura trazable** (Jefatura/Operaciones) que revierte/asiste el efecto
físico y queda auditada.

---

## 6. Backlog documental (no bloqueante)

**Ruta:** `Logística Exportación → Backlog Documental` (grupo Operaciones).

- Modelo: `lumber.shipment.document` (`domain: state != verified`).
- Campos de gestión: **Responsable**, **Criticidad** (medium/high/critical), **Fecha objetivo
  (due_date)**, **Estado de backlog** (open / in_progress / completed / waived).
- Alertas visuales: **vencido** (`backlog_overdue`, rojo) y **atención**
  (`backlog_attention`, ámbar = vencido o criticidad high/critical).
- Acción **Escalar**: asigna responsable y fecha; **no** bloquea la operación física.
- Agrupaciones disponibles: Responsable, Criticidad, Estado, Embarque.

> Escalamiento: al vencer o ser crítico, la fila se marca y escala; se documenta avance con
> `action_backlog_escalate` / `action_backlog_complete`. La operación (rebaja/zarpe/B-01/
> R1/R2/Entrega) **continúa** aunque el documento siga pendiente.

---

## 7. Contenedores y Embarques

**Ruta:** `Logística Exportación`.
- **Embarques** (`lumber.export.shipment`), estados: `draft → confirmed → in_transit → done`
  (y `canceled`). Botones en el formulario: Confirmar, En Tránsito, Completar, Cancelar, Reabrir.
- **Consolidación**: contenedores no zarpados (`state != shipped`).
- **Contenedores** (`lumber.container`), estados: `empty → loading → loaded → sealed → shipped`
  (+ `rebajado`).

**Asignación de lotes a contenedor:** desde Consolidación/Contenedor, agregar lotes (tarja),
verificando peso/volumen. El **rollee** mueve lotes entre contenedores antes del zarpe.

---

## 8. Motonaves, Viajes y Rolleo

- **Motonaves** (`shipping.vessel`) y **Viajes** (`shipping.voyage`), **Reservas** (booking):
  `Logística Exportación → Configuración`.
- **Rolleo / reprogramación de salida marítima (AD-92, 2026-10-05):** se inicia
  **desde un Embarque**: `Logística Exportación → Embarques → (abrir EMB-XXXX) →
  «Rollover de Embarque»`. Disponible para Operaciones/Jefatura/Gerencia y sólo en
  **Borrador/Confirmado**. La **Motonave/Viaje de origen** se muestran **sólo lectura**
  (se derivan del Embarque); se elige **Motonave destino** y, opcionalmente, **Viaje
  destino**. Sólo cambian `vessel_id`/`voyage_id` **de ese Embarque**; no mueve stock,
  lotes, quants, pickings, contenedores como pertenencia, costos, Rebaja, Zarpe, B-01 ni
  finanzas. Deja **auditoría SHA-256**, **chatter** y un **pendiente documental no
  bloqueante**. Asistente técnico: `lumber.vessel.rollover.wizard` (alcance = 1 Embarque).
- **Motonave** (`shipping.vessel`): el botón de la ficha **ya no ejecuta** rolleo masivo;
  sólo abre la **lista de Embarques filtrada** por esa Motonave (consulta). El rolleo se
  ejecuta desde el Embarque.
- **Rolleo de contenedor** (`lumber.container.rollover.wizard`): flujo **independiente**;
  no fue modificado por AD-92.

---

## 9. Rebaja

- **Rebajar por Motonave** (grupo Operaciones): `Logística Exportación → Rebajar por Motonave`
  (`lumber.shipment.rebaja.wizard`). Genera la **salida física (OUT)** de los lotes del
  contenedor y deja el contenedor en estado **`rebajado`**.
- Cada línea de contenedor tiene `rebaja_state` (`rebajado` / `reversed`) y `rebaja_picking_id`.
- La rebaja queda **auditada** (firma SHA-256) y es **revertible** con la **reversa de rebaja**
  (`lumber.container.rebaja.reverse.wizard`).

> La **documentación tardía no bloquea** la rebaja; solo requiere motivo cuando aplique
> política de excepción (registrado como desviación).

---

## 10. Zarpe y B-01

- **Zarpe:** asistente `lumber.shipment.zarpe.wizard` desde el Embarque. Marca el embarque en
  tránsito/embarcado. Requiere rol operativo (Operaciones/Jefatura).
- **Excepción B-01** (`b01_exception_state`: `open → resolved`): permite zarpar con un
  contenedor **sin rebaja física completa**. Registra **motivo**, apertura y cierre, con
  auditoría dedicada. **No** falsificable por RPC.
- **Bloqueo coherente:** un embarque con B-01 **abierta** **no** puede completar Entrega hasta
  resolverse o regularizarse (§11).

---

## 11. R1 y R2 (regularización y retorno)

- **R1 — Rebaja extemporánea (regularización B-01):** **solo Gerencia**. Asistente
  `lumber.b01.regularization.wizard`, sobre un Embarque **embarcado** y Contenedores
  **Cargado / Rebajado**, siempre que **no** existan costos, facturación, pagos ni
  consolidaciones (congelado Entrega 2). Cierra la excepción B-01 con auditoría.
- **R2 — Retorno físico TOTAL y reversa robusta:** valida el **retorno físico total** antes de
  revertir lógicamente la rebaja; reconcilia la contrapartida SV. Gates de B-01 y terminalidad
  con override de Gerencia; gates financieros. Idempotente y verificado.

---

## 12. Entrega

- **Entrega** del embarque (`action_done` / waiver `delivery_waiver_state`): marca el embarque
  como entregado/completado.
- **Waiver de Entrega** (`delivery_waiver_state`): permite cerrar la Entrega con pendientes
  **documentales**, dejando **motivo**, aprobador y **auditoría**. Los documentos siguen en el
  **Backlog** (§6) y **no** revierten la Entrega.
- La Entrega **no** ejecuta Costeo/Billing/Pagos.

---

## 13. Reportes

Ver la **Matriz de Reportería** en `CIERRE_ENTREGA_1_20261005.md` (§3 y §4). Acceso:
`📊 Reportes y Listados`.

- **Stock real:** R1 (detalle por patio), R2 (resumen por patio), R5 (por proveedor),
  R7 (por OC), R9 (por producto) — con export **XLSX**.
- **Listados de lotes:** 1 Comercial (compra), 2 Medidas Reales (físico), 3 De Embarque.
- **Recepción:** Consola de Recepciones, Tablero (kanban), Historial de Ingresos, Guías
  Procesadas.
- **Logística:** Embarques, Contenedores, Consolidación, Backlog Documental.
- **Auditoría:** Trazabilidad 360° (`madenat.audit.log`, filtros por tipo de acción).

---

## 14. Roles, permisos y escalamiento (resumen operativo)

| Acción | Operaciones | Jefatura | Gerencia | Auditoría | Interno común |
|---|---:|---:|---:|---:|---:|
| Crear/editar/validar Guía | ✔ | ✔ | ✔ | ✖ | ✖ |
| Crear/editar/confirmar Recepción | ✔ | ✔ | ✔ | ✖ | ✖ |
| Reabrir / Cancelar guía-recepción | ✔ | ✔ | ✔ | ✖ | ✖ |
| Corrección documental CDP-V1 | ✔ | ✔ | ✔ | ✖ | ✖ |
| Rebaja / Zarpe | ✔ | ✔ | ✔ | ✖ | ✖ |
| Regularización B-01 (R1) | ✖ | ✖ | ✔ | ✖ | ✖ |
| R2 (retorno total / reversa) | ✔* | ✔* | ✔ | ✖ | ✖ |
| Entrega / Waiver | ✖ | ✔* | ✔ | ✖ | ✖ |
| Backlog documental (editar/escalar) | ✔ | ✔ | ✔ | ✖ | ✖ |
| Trazabilidad 360° | ✖ | ✔ | ✔ | ✔ | ✖ |

`*` supeditado a los gates de servidor (estado/terminalidad/financiero) del modelo.

**Escalamiento:** el backlog documental (`criticality`, `due_date`, `responsible_id`) alerta y
escala sin bloquear. Las excepciones operativas (B-01) y las regularizaciones (R1) tienen
**aprobador** y **auditoría**.

---

## 15. Qué NO corresponde a Operaciones (Entrega 2)

No forma parte de la Entrega 1 y **no debe ejecutarse** en operación:

- **Costeo C2 / valorización** y **líneas de costo** (`stock.lot.cost.line`,
  `lumber.shipment.cost.line`, `lumber.cost.distribution`).
- **Facturación / Billing** y **consolidación de facturación**.
- **Pagos / Vendor Payment** (`account.payment`).
- **R3**, **retorno parcial**, **cierre financiero**, **Auditoría de costos**.
- **BT-04 / Maquila** y **MRP**.

> Estos procesos son **posteriores** al Embarque/Zarpe y **no** modifican retroactivamente
> stock, lotes, rebaja, zarpe, B-01, retorno ni Entrega.


