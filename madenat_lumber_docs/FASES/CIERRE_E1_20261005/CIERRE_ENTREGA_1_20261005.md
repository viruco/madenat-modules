# MADENAT — Cierre Entrega 1 Operativa

```
Documento   : CIERRE_ENTREGA_1_20261005
Alcance     : Recepción · Inventario · Bodega · Logística · Embarque · Reportería
Plataforma  : Odoo 18 CE · madenat_test · odoo18_app · odoo18_db healthy · HTTP 200
Fecha        : 2026-10-05
Rama / HEAD  : feat/guia-correccion-documental-preservada-20261002 / 34c81272
Método       : RE-INT-4 (odoo shell, rollback) + auditoría READ-ONLY de reportería +
               validación final read-only. SIN update/install, SIN SQL de escritura,
               SIN uid 1 como actor de datos, SIN commit/push.
Fuera 1ª E   : Costeo C2 · Cost lines · Billing · Facturación · Vendor Payment · Pagos ·
               R3 · retorno parcial · cierre financiero · BT-04/Maquila · MRP.
```

---

## 1. Alcance oficial — Entrega 1 vs. Entrega 2

| Bloque | Entrega 1 (ESTE cierre) | Entrega 2 (diferida) |
|---|---|---|
| Recepción / Guías / Lotes | ✅ Operativo | — |
| Inventario / Bodega / Stock por ubicación | ✅ Operativo | — |
| Contenedores / Embarques / Motonaves / Viajes | ✅ Operativo | — |
| Rolleo / Rebaja / Zarpe / B-01 | ✅ Operativo | — |
| R1 (regularización B-01) / R2 (retorno total) | ✅ Operativo | — |
| Entrega (con/sin waiver) | ✅ Operativo | — |
| Backlog documental (no bloqueante) | ✅ Operativo | — |
| Seguridad / Roles / Escalamiento | ✅ Operativo | — |
| Reportería operativa mínima | ✅ Definida (§4) | Ampliaciones |
| Costeo C2 / Valorización / Cost lines | ⛔ Congelado | ✅ Entrega 2 |
| Facturación / Billing / Pagos / Vendor Payment | ⛔ Congelado | ✅ Entrega 2 |
| R3 / retorno parcial / cierre financiero | ⛔ Fuera | ✅ Entrega 2 |
| BT-04 / Maquila / MRP | ⛔ Fuera | ✅ Entrega 2 |

**Principio vinculante aplicado:** la documentación tardía **no bloquea** la operación física;
genera backlog/alertas/escalamiento. Costeo/Billing/Pagos son **posteriores** al Embarque/Zarpe
y **no** modifican retroactivamente stock, lotes, rebaja, zarpe, B-01, retorno ni Entrega.

---

## 2. Resultado INT-4 (Fase 1) — `APROBADO`, sin regresión

**Escenario re-ejecutado:** UAT-INT-4 (Seguridad de Ingreso/Recepción/Guías). Fuente:
`01_uat_int4.txt` / `01_uat_int4_raw.txt`. Actor autorizado **uid 8** (Operaciones+Jefatura,
`su=False`); actor bloqueado **uid 6 Leonardo Rodriguez** (sin Operaciones; *stock manager*).

| # | Caso (uid 6, sin Operaciones) | Vía | Resultado observado |
|---|---|---|---|
| B2 | Crear **Guía** | ORM/RPC | **AccessError** (guard operativo) |
| B3 | Editar campo **operativo** (`state`) | ORM/RPC | **AccessError** (guard) |
| B4 | **Validar** guía | ORM/RPC | **AccessError** (guard) |
| B5 | **Procesar / verificar** datos | ORM/RPC | **AccessError** (guard) |
| B6 | Procesar desde staging | ORM/RPC | **AccessError** (guard) |
| B7 | **Reabrir** a borrador | ORM/RPC | **AccessError** (guard) |
| B8 | **Cancelar** (force) | ORM/RPC | **AccessError** (guard) |
| B9 | **Wizard** corrección documental | ORM | **AccessError** (ACL) |
| B10 | **Contexto falso** (`allow_intake`, `force`, …) | ORM | **AccessError** (guard) |
| B11 | Crear **Recepción** | ORM/RPC | **AccessError** (guard) |
| B12 | Escribir Recepción (`state`) | ORM/RPC | **AccessError** (guard) |
| B13 | **Importación** (create en lote) | ORM | **AccessError** (guard) |
| B1 | Crear Consola/Wizard Intake | ACL | **AccessError** |
| B1 | `check_access_rights` create/write Guía | ACL | **AccessError** |

**Control positivo (uid 8):** crea → `verified` → `action_validate()` ⇒ **`validated`** + **lote
16702** creado y picking IN `done`. ⇒ El rol operativo **sí** opera; el no operativo **no**.

**Integridad del escenario bloqueado:** `BLOCKED_RESIDUE_DELTA` = **0** en
`madenat.guia.processing / .line`, `lumber.reception / .line`, `stock.lot`, `stock.picking`,
`stock.move(.line)`, `stock.quant`, `lumber.shipment.document`. La guía objetivo permaneció en
`verified` y la recepción en `draft`. **Rollback** ⇒ `FINAL_VS_BASE0` = **0** (nada persistió);
`UAT-INT-20261005-` residuo = **0**.

> **Residual R-1 (documentado, NO bloqueante):** `check_access_rights('create'|'write')` sobre
> `lumber.reception` **no** lanza error para uid 6 porque su grupo legacy
> **«MADENAT: Validación Contable (Auditoría)»** arrastra la fila ACL huérfana **827**. El
> **guard de servidor neutraliza** ese permiso (B11/B12 = AccessError), consistente con
> `T-REC-SEC-5`. Su saneamiento (borrado de las filas 802/827) requiere una migración fuera del
> set de archivos autorizado ⇒ **diferido a Entrega 2** (§10). Para guías, el bloqueo es completo
> (ACL mínimo privilegio **y** guard).

**No regresión:** el núcleo INT-1/2/3 permanece intacto (guía **32689** `validated`, lote
**16694**, quant interno **4.0 m³**, backlog doc **13420**) — ver §5 y §9. No se re-ejecutó
INT-1/2/3 (no fue necesario).

---

## 3. Matriz de reportería operativa (Fase 2 — READ-ONLY)

Fuente: `03_audit_reporteria.txt` (inventario real de acciones y datos). *Datos reales @2026-10-05.*

**Datos reales de referencia:** `stock.quant` 170 (internos>0 = 82) · `stock.lot` 133 (con guía
108) · guías 10 (draft 1 / verified 2 / validated 7) · recepciones 7 (done 5) · documentos 127
(backlog abiertos 126 / críticos 1) · embarques 21 (draft 8 / confirmed 3 / in_transit 8 /
delivered 2) · contenedores 22 (loading 4 / loaded 7 / shipped 7 / **rebajado 4**) · motonaves
9 · viajes 2 · `madenat.audit.log` 281 · SV operación 1 / imputación 1.

| Reporte requerido | Existe | Acción / Menú | Modelo / fuente | Rol | Brecha | Prioridad |
|---|---:|---|---|---|---|---|
| **A. Stock por ubicación/patio** | Sí | R1 `action_r1_stock_detail_patio` · R2 `action_r2_stock_summary_patio` (📊 Reportes y Listados → 📦 Inventario Recepción) | `stock.quant` (`quantity>0`, `usage=internal`, group_by ubicación) | Todos (lectura) + XLSX | Sin restricción de rol; sin columna de **disponibilidad** | Media |
| **A. Disponibilidad (qty − reservado)** | Parcial | (no dedicada) | `stock.quant` (`reserved_quantity`) | Operaciones/Jefatura | Falta columna/filtro explícito | Media |
| **A. Lotes** | Sí | Listado 2 `action_madenat_list_physical` · R1 detalle incluye campos de lote | `stock.lot` | Todos | — | Baja |
| **A. vol_shipment_m3 / volumen_m3** | Sí | Listado 3 `action_madenat_list_export` · Listado 2 | `stock.lot` (`vol_shipment_m3`, `volumen_m3`) | Todos | — | Baja |
| **A. Producto** | Sí | R9 `action_r9_stock_detail_product` | `stock.quant`→`stock.lot.product_id` | Todos | — | Baja |
| **A. Proveedor** | Sí | R5 `action_r5_stock_detail_partner` | `stock.quant`→lote proveedor | Todos | — | Baja |
| **A. Guía** | Parcial | R1 detalle (`lot_guia_number`) · Listado 3 | `stock.lot.guia_number` | Todos | No hay columna de guía en R2/R5/R9 | Baja |
| **A. Patio / quants** | Sí | R1/R2 + `action_madenat_inventory_adjustments` (ajustes) | `stock.quant`, `stock.location` | Todos / Jefe stock (ajustes) | — | Baja |
| **B. Guías por estado** | Sí | Consola `action_lumber_reception_pending` · Guías `action_guia_processing_list` | `madenat.guia.processing` | Jefatura | Filtro por estado depende del buscador | Media |
| **B. Recepciones por estado** | Sí | Consola + `action_lumber_reception_kanban` | `lumber.reception` (kanban por estado) | Jefatura | — | Baja |
| **B. Pendientes documentales** | Sí | `action_lumber_shipment_document_backlog` | `lumber.shipment.document` | Operaciones | — | Baja |
| **B. Backlog crítico/vencido** | Sí | idem (filtro «Críticos» + `backlog_overdue`) | `lumber.shipment.document` | Operaciones | Falta KPI/tablero resumen | Media |
| **B. Proveedor y OC documental** | Parcial | campos en guía/recepción (sin reporte) | `madenat.guia.processing` (`oc_reference_raw`, OC) | Jefatura | Sin reporte dedicado OC-documental | Media |
| **C. Contenedores por estado** | Parcial | `action_lumber_container` · Consolidación | `lumber.container` (list,form) | Todos | Sin **pivot/agrupación por estado** | Media |
| **C. Embarques por estado** | Sí | `action_lumber_export_shipment` (list,form,**pivot**) | `lumber.export.shipment` | Todos | — | Baja |
| **C. Motonaves / Viajes / Reservas** | Sí | Configuración → Motonaves / Viajes / Reservas | `shipping.vessel/voyage/booking` | Todos | — | Baja |
| **C. Rolleo** | Parcial | wizards rollover vessel/contenedor | `lumber.export.shipment`, `lumber.container` | Operaciones | Sin bitácora/reporte de rolleo | Media |
| **C. B-01 open/resolved** | Parcial | `b01_exception_state` + audit «Desviación Aceptada» | `lumber.export.shipment`, `madenat.audit.log` | Gerencia/Jefatura | Sin vista filtrada dedicada B-01 | Media |
| **C. Rebajas** | Parcial | `rebaja_state` contenedor + audit «Rebaja de Contenedor» | `lumber.container`, audit | Operaciones | Sin reporte dedicado de rebajas | Media |
| **C. R1 (regularización B-01)** | Parcial | `lumber.b01.regularization.wizard` + audit | `lumber.export.shipment`, audit | Gerencia | Sin reporte R1 | Media |
| **C. R2 (retorno total)** | Parcial | retorno total + audit + estado contenedor | `lumber.container`, audit | Operaciones/Gerencia | Sin reporte R2 | Media |
| **C. Entregas** | Parcial | `state=done` + `delivery_waiver_state` (Embarques) | `lumber.export.shipment` | Jefatura/Gerencia | Sin vista/filtro «Entregas» | Baja |
| **D. Trazabilidad / auditoría 360°** | Sí | `action_madenat_audit_logs` (⚖️ Auditoría) | `madenat.audit.log` | Stock mgr · Auditoría · Jefatura · Gerencia | — | Baja |
| **D. Quién ve cada reporte** | Sí (parcial) | menús por grupo (ver §6) | `ir.ui.menu.groups_id` | — | Varios reportes en «Todos» (sin acotar rol) | Media |
| **D. Leonardo (lectura)** | Sí | lectura general | — | Interno común | Operación **bloqueada** (INT-4 OK) | — |
| **D. Operaciones/Jefatura (ejecución)** | Sí | menús operativos + XLSX | — | Operaciones/Jefatura | — | — |
| **D. Auditoría (lectura)** | Sí | Trazabilidad 360° + Backlog (lectura ACL) | `madenat.audit.log` | Auditoría | — | — |

> **Hallazgo H-1:** la acción **«Tarja por Lote»** (`madenat_lumber_core.action_report_lumber_batch`)
> **NO existe en runtime**: `reports/report_actions.xml`, `lumber_batch_report.xml` y
> `lumber_cost_report.xml` **no están en** el `data` de `madenat_lumber_core/__manifest__.py`. El
> reporte PDF de guía (`madenat_guia_report`) **sí** está operativo. Impacto bajo ⇒ §10.

---

## 4. Reportería mínima definida para Entrega 1 (Fase 3)

Solo lo **imprescindible**; sin rentabilidad, costeo, facturación ni pagos.

| # | Reporte mínimo | Soporte existente | Estado | Acción de cierre (baja complejidad) |
|---|---|---|---|---|
| 1 | **Stock por ubicación y lote** | R1/R2 (`stock.quant`) | ✅ Listo | (opcional) acotar rol + columna disponibilidad |
| 2 | **Lotes / volumen / disponibilidad** | Listado 2/3 + R1 | 🟡 Parcial | añadir **disponibilidad** (qty − reservado) |
| 3 | **Guías y recepciones pendientes** | Consola + Guías Procesadas + Tablero | ✅ Listo | — |
| 4 | **Contenedores y Embarques por estado** | Embarques (pivot) + Contenedores | 🟡 Parcial | agrupación por estado en Contenedores |
| 5 | **B-01 y desviaciones** | audit.log (filtro deviation) + campos B-01 | 🟡 Parcial | filtro dedicado B-01 en Embarques |
| 6 | **Backlog documental (criticidad/responsable/vencimiento)** | Backlog Documental | ✅ Listo | — |
| 7 | **Rebajas, R1 y R2** | estados/auditoría (contenedor/embarque) | 🟡 Parcial | vista única «Rebajas y retornos» |

**Conclusión Fase 3:** **4 de 7** bloques están **listos para uso**; **3** son «parciales» y su
cierre es de **baja complejidad** (columnas/filtros/agrupaciones sobre datos ya existentes). El
dato **ya está en sistema** y es consultable; las 3 brechas **NO bloquean** la operación. Quedan
priorizadas para micro-ajustes (§10).

---

## 5. Estado de Inventario / Bodega / Logística

| Dominio | Estado | Evidencia |
|---|---|---|
| **Inventario / Stock real** | ✅ Operativo | `stock.quant`: 170 (internos>0 = 82); fuente de verdad física por ubicación interna. |
| **Bodega / Ubicaciones / Patios** | ✅ Operativo | 8 lotes con guía; 133 lotes; ajustes físicos disponibles (perfil jefe stock). |
| **Lotes / Trazabilidad** | ✅ Operativo | `stock.lot` 133 (con `guia_number` 108); prov/guía/ubicación/volumen persistidos (UAT-INT-1). |
| **Recepción / Guías** | ✅ Operativo | guías 10 (validated 7); recepciones 7 (done 5); picking IN `done`, quants internos positivos. |
| **Contenedores** | ✅ Operativo | 22 (loading 4 / loaded 7 / shipped 7 / **rebajado 4**); estados coherentes. |
| **Embarques** | ✅ Operativo | 21 (draft 8 / confirmed 3 / in_transit 8 / delivered 2). |
| **Motonaves / Viajes** | ✅ Operativo | 9 motonaves · 2 viajes · reservas; rolleo de motonave y contenedor. |
| **Rebaja / Zarpe / B-01** | ✅ Operativo | contenedor `rebajado` 4; excepción B-01 (`open/resolved`) con auditoría; zarpe con guard de rol. |
| **R1 / R2 / Entrega** | ✅ Operativo | R1 regularización (Gerencia) · R2 retorno total/reversa · Entrega con/sin waiver y auditoría. |
| **Backlog documental** | ✅ Operativo (no bloqueante) | `lumber.shipment.document` 127 (abiertos 126); edición/escalamiento por Operaciones. |
| **Auditoría / Trazabilidad 360°** | ✅ Operativo | `madenat.audit.log` 281; filtros por tipo de acción (deviation, rebaja, imputación, …). |

> **Congelados financieros (Entrega 2):** `cost_distribution_state=distributed` = 0 ·
> `lumber.cost.distribution.is_c2=True` = 0 · `lumber.shipment.cost.line` = 0 ·
> `account.payment` = 0 · `lumber.billing.consolidation` = 0 · 53 líneas de costo de lote
> históricas **sin cambio**. Nada financiero se activó en este cierre.

---

## 6. Estado de seguridad y roles

**Grupos (jerarquía real):**
`Usuario interno` → `Operaciones` (⇒ `stock user`) → `Jefatura de Operaciones`;
`Gerencia` ⇒ Operaciones + Costos + Contabilidad; `Auditoría` (solo lectura operativa);
`Costos` / `Contabilidad` (Entrega 2); `Administrador Madenat` / `Configurador`.

**ACL efectiva (runtime, post-parche Fase C.1):**

| Modelo | Usuario interno | Operaciones | Jefatura | Auditoría | Otros |
|---|---|---|---|---|---|
| `madenat.guia.processing` | **read-only** | rwc | rwc | — | — |
| `madenat.guia.processing.line` | **read-only** | rwc | rwc | — | — |
| `lumber.reception` | **read-only** | rwc | rwc | read-only | *legacy 802 (rwcu) / 827 (rwc)* |
| `lumber.reception.line` | **read-only** | rwc | rwc | — | — |
| Wizards guía (reopen / CDP / historical) | read-only | rwc | rwc | — | — |

`ir.rule` sobre guía/recepción = **0** ⇒ el control es **ACL + guard de servidor**.

**Guard de servidor canónico** (`_require_intake_operational_group` /
`_check_intake_operational_write` en `mixin_lumber_ingest.py`) aplicado a `create`,
`write` operativo y a las acciones de proceso/validación/reapertura/cancelación y wizards de
`madenat.guia.processing` y `lumber.reception`. Cubre **UI, RPC, ORM, importación y contexto**.

**Resultado INT-4:** ✅ **APROBADO** — Operaciones/Jefatura/Gerencia operan; cualquier interno sin
Operaciones recibe `AccessError` (incl. ORM/RPC/import/wizard/contexto falso);
**Δ0** de residuos; rollback limpio. **Residual R-1** (legacy ACL 802/827) neutralizado por el
guard (§2, §10).

---

## 7. Backlog documental

| Aspecto | Estado |
|---|---|
| Modelo / fuente | `lumber.shipment.document` (127 registros; abiertos 126; críticos/high 1). |
| Naturaleza | **No bloqueante**: la operación (recepción/validez física, rebaja, zarpe, B-01, R1/R2, Entrega) **continúa**. |
| Gestión | Responsable, Criticidad (medium/high/critical), Fecha objetivo, Estado de backlog (open/in_progress/completed/waived). |
| Alertas | `backlog_overdue` (vencido) y `backlog_attention` (vencido o criticidad high/critical). |
| Escalamiento | `action_backlog_escalate`/`action_backlog_complete`; visible a Operaciones. |
| Evidencia UAT | INT-2: doc 13420 creado, escalado, completado ⇒ `RECEPTION_VALIDATED_WITH_PENDING_DOCS = True`. |

---

## 8. Manual Operativo Entrega 1

Entregado como documento independiente y **verificado**:
`./MANUAL_OPERATIVO_ENTREGA_1_20261005.md`.

Contenido: (1) roles y perfiles · (2) inicio de sesión por rol · (3) recepción e ingreso ·
(4) bodega/stock/lotes · (5) guías y corrección documental (CDP-V1) · (6) backlog no bloqueante ·
(7) contenedores/embarques · (8) motonaves/viajes/rolleo · (9) rebaja · (10) zarpe/B-01 ·
(11) R1/R2 · (12) entrega · (13) reportes · (14) roles/permisos/escalamiento ·
(15) **qué NO corresponde a Operaciones**.

> El manual **no** documenta Costeo/Billing/Pagos como operativos en Entrega 1 (solo se declaran
> fuera de alcance).

---

## 9. UAT / Evidencias

Carpeta: `./CIERRE_E1_20261005/`.

| Archivo | Contenido |
|---|---|
| `00_git_runtime.txt` | Snapshot git (rama/HEAD/working tree) y runtime (contenedores/HTTP). |
| `00_precheck_cierre.py` / `00_precheck_raw.txt` / `00_precheck_cierre.txt` | Precheck **read-only** (usuarios/roles, baseline, congelados, integridad INT-1/2/3, módulos, grupos). |
| `_uat_int4.py` / `01_uat_int4_raw.txt` / `01_uat_int4.txt` | **Re-ejecución INT-4**: escenario positivo (uid 8) + 14 casos negativos (uid 6) + Δ0 + rollback. |
| `02_final_validation.txt` | Validación final read-only post-corrida (integridad y congelados). |
| `_audit_reporteria.py` / `03_audit_reporteria_raw.txt` / `03_audit_reporteria.txt` | Auditoría de reportería read-only (acciones/menús/modelo/rol + datos reales). |
| `CIERRE_ENTREGA_1_20261005.md` | Este informe. |
| `MANUAL_OPERATIVO_ENTREGA_1_20261005.md` | Manual Operativo Entrega 1. |

**Integridad de la corrida (`02_final_validation.txt`, idéntico al baseline):**

| Métrica | Valor |
|---|---|
| Guía UAT-INT-1/2/3 | **32689** `validated` · lote **16694** · quant interno **4.0 m³** · doc **13420** — **intacta** |
| Residuo UAT INT-4 (`UAT-INT-20261005-`) | **0** |
| Counts | guías 10 · recepciones 7 · pickings 31 · quants 170 · lotes 133 · moves 146 |
| Congelados | distributed **0** · C2 **0** · cost lines **0/53** · payments **0** |
| Git | HEAD `34c81272` sin cambio; **sin** commit/push |
| Runtime | `odoo18_app` Up · `odoo18_db` healthy · HTTP **200** |

**Antecedentes (referencia, no re-ejecutados):** UAT-INT-1/2/3 + CDP-V1 `APROBADO`
(`UAT_INTAKE_20261004/`); parche de seguridad Fase C.1 con `TestGuiaProcessingSecurity`
(T-INT-SEC-1..8) + `TestReceptionSecurity` (T-REC-SEC-1..5) = **13/13** (`IMPL_SEC_RECEPCION_20261004/`).

---

## 10. Brechas diferidas a Entrega 2

| ID | Brecha | Impacto | Acción propuesta | Entrega |
|---|---|---|---|---|
| **R-1** | Filas ACL **huérfanas 802/827** (`lumber.reception`) conceden create/write nominal al grupo legacy «Validación Contable (Auditoría)». **Neutralizadas por el guard** (probado). | Bajo (funcional bloqueado) | Migración de limpieza de `ir.model.access` (fuera del set de archivos autorizado actual). | 2 |
| **M-1** | Reportería: **disponibilidad** (qty − reservado) no expuesta en R1/R2. | Bajo | Columna/filtro en `stock.quant` (R1/R2). | 2 (micro) |
| **M-2** | **Contenedores**: sin agrupación/pivot por estado. | Bajo | Vista pivot (datos existentes). | 2 (micro) |
| **M-3** | **B-01**: sin vista filtrada dedicada (hoy vía audit + campo). | Bajo | Filtro/dominio dedicado en Embarques. | 2 (micro) |
| **M-4** | **Rebajas / R1 / R2**: sin reporte único dedicado. | Bajo | Vista «Rebajas y retornos» (contenedor). | 2 (micro) |
| **H-1** | Reporte PDF **«Tarja por Lote»** no cargado (archivos fuera del `__manifest__`). | Bajo | Declarar `reports/report_actions.xml` (+ templates) en el manifest, si se requiere. | 2 |
| **H-2** | Varios reportes operativos con menú en «**Todos**» (sin acotar grupo) — solo lectura. | Bajo | Acotar `groups` de menús/acciones a Operaciones/Jefatura/Gerencia + Auditoría lectura. | 2 |
| **E2** | Costeo C2 · Billing · Facturación · Pagos · R3 · retorno parcial · cierre financiero · BT-04/Maquila · MRP. | — | Entrega 2 completa. | 2 |

> **Ninguna** brecha de §10 **bloquea** la operación física/logística de la Entrega 1.

---

## 11. Dictamen

> ## ✅ A. `ENTREGA 1 OPERATIVA CERRADA — LISTA PARA USO`
>
> El escenario **INT-4** quedó **APROBADO** (Operaciones/Jefatura/Gerencia operan; cualquier
> interno sin Operaciones es bloqueado —create/editar/validar/procesar/reabrir/cancelar/wizard/
> RPC/ORM/importación/contexto falso— con **Δ0** de residuos y rollback limpio). La **reportería
> mínima** queda **definida** (4/7 listas, 3/7 con micro-ajustes no bloqueantes sobre datos ya
> existentes) y el **Manual Operativo Entrega 1** está entregado. Inventario/Bodega/Logística
> operan con stock nativo, lotes, ubicaciones, pickings, movimientos y trazabilidad; el **backlog
> documental es no bloqueante**; y **Costeo/Billing/Pagos permanecen congelados** (posteriores al
> Embarque/Zarpe). **Sin regresión** (UAT-INT-1/2/3 y finanzas intactos; sin commit/push).
>
> **Condición de go-live:** las brechas de §10 (todas de impacto **bajo**) se gestionan como
> backlog de Entrega 2 **sin** impedir el uso operativo.

**Firmas / responsables sugeridos:** Operaciones (Cristhian), Jefatura/Admin (Mauricio),
Auditoría/Gerencia (Felipe), según §6 del Manual.



