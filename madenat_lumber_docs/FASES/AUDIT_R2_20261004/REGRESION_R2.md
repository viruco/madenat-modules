# MADENAT — Resultado Regresión Acotada R2

- **Sub-bloque:** 4B — R2 Retorno Físico Total robusto.
- **Fase:** C.1 — Validación de regresión acotada (gate UAT). **Sin UAT, sin datos persistentes, sin acciones de negocio, sin `-u`/`-i`.**
- **Fecha:** 2026-10-04.
- **Clases ejecutadas (6):** `TestRebajaReturnTotal`, `TestRebajaContenedor`,
  `TestShipmentB01Exception`, `TestB01Regularization`,
  `TestShipmentReturnToDraft`, `TestVesselRollover`.
- **Comando (sin `-u`/`-i`):**
  ```
  odoo --config /etc/odoo/odoo.conf --database madenat_test --test-enable \
    --test-tags /madenat_lumber_logistics:TestRebajaReturnTotal,\
  /madenat_lumber_logistics:TestRebajaContenedor,\
  /madenat_lumber_logistics:TestShipmentB01Exception,\
  /madenat_lumber_logistics:TestB01Regularization,\
  /madenat_lumber_logistics:TestShipmentReturnToDraft,\
  /madenat_lumber_logistics:TestVesselRollover \
    --stop-after-init --no-http --http-port=8899 --log-level=test
  ```

---

## 1. Precheck y línea base

| Ítem | Valor | Estado |
|---|---|---|
| Repo git | `custom_addons/` | ✅ |
| Rama | `feat/guia-correccion-documental-preservada-20261002` | ✅ |
| HEAD | `34c81272bb07d48db98d73a7734c81a2a8e384fa` | ✅ |
| Working tree | **33 entradas = 24 ` M` + 9 `??`** | ✅ coincide |
| Runtime | `odoo18_app` Up · `odoo18_db` Up (healthy) | ✅ |
| DB | `madenat_test` | ✅ |

**Conteos de línea base (antes = después):** `stock_move` 143 · `stock_move_line`
210 · `stock_picking` 28 · `stock_quant` 171 · `stock_lot` 127 ·
`lumber_export_shipment` 15 · `lumber_container` 16 · `lumber_shipment_line` 6 ·
`madenat_audit_log` 270 · `madenat_sv_operation` 1 · `madenat_sv_imputation` 1 ·
`stock_lot_cost_line` 53 · `lumber_shipment_cost_line` 0 · `account_move` 1 ·
`account_payment` 0 · `lumber_billing_consolidation` 0.

**Registros protegidos — intactos:** histórica; UAT Rolleo (audit 19699–19704,
`VESSEL-ROLLOVER-202610040352…`, uid 8); UAT Borrador; UAT B-01
(`b01_exception_state`: 13 `none` + 1 `open` + 1 `resolved`); UAT R1
(shipment 1885 `in_transit`/`resolved`, container 1888 `rebajado`,
lot 16312, picking 7238 `done`, move 13973 `done`, audit 19941/19945).

**Confirmaciones precheck:** no `rebaja_return_total` persistido; no
`rebaja_reverse` persistido; sin cambios de B-01 fuera de UAT R1; sin
código/configuración adicional desde el informe R2 (working tree idéntico).

## 2. Clases ejecutadas

6 clases · **94 tests** (12 + 31 + 12 + 13 + 16 + 10). Descubiertas **sin**
`-u`/`-i` (no fue necesario actualizar/instalar módulo).

## 3. Resultado individual por clase

Resultado global: **`89 PASS · 5 FAIL · 0 ERROR` (`of 94 tests`)** · 37.0 s ·
25 305 queries.

| Clase | Métodos | PASS | FAIL | Error |
|---|---|---|---|---|
| `TestRebajaReturnTotal` | 12 | **12** | 0 | 0 |
| `TestRebajaContenedor` | 31 | **31** | 0 | 0 |
| `TestShipmentB01Exception` | 12 | **12** | 0 | 0 |
| `TestB01Regularization` | 13 | **13** | 0 | 0 |
| `TestShipmentReturnToDraft` | 16 | **16** | 0 | 0 |
| `TestVesselRollover` | 10 | 5 | **5** | 0 |

**Detalle de los 5 fallos (`TestVesselRollover`):**

| Test | Línea | Assert | Encontrado |
|---|---|---|---|
| `test_01_rollover_success_without_destination_voyage` | 161 | `len(master) == 1` | **3** |
| `test_03_destination_voyage_other_vessel_blocked` | 206 | `assertFalse(search(vessel_rollover))` | `19699, 19702` |
| `test_06_in_transit_shipment_blocks_all` | 260 | `assertFalse(search(vessel_rollover))` | `19699, 19702` |
| `test_09_role_and_audit_blocked` | 337 | `assertFalse(search(vessel_rollover))` | `19699, 19702` |
| `test_10_integrity_only_planning_fields_change` | 371 | `len(master) == 1` | **3** |

**Causa raíz (única, común a los 5):** `tests/test_vessel_rollover.py` busca en
`madenat.audit.log` **globalmente** por `action_type='vessel_rollover'`
(`/ 'vessel_rollover_item'`) **sin filtrar por su propia operación/batch**,
por lo que contabiliza los **2 registros `vessel_rollover` + 4
`vessel_rollover_item` persistidos por la UAT Rolleo** (`UAT-VR-20261004`,
`create_date 2026-10-04 03:52`, uid 8), creados **antes** de la sesión R2.

- `test_01` / `test_10` → `2 (UAT) + 1 (propio) = 3` (esperaban 1).
- `test_03` / `test_06` / `test_09` → encuentran los `2` de UAT (esperaban 0).

**No atribuible a R2** (evidencia):
1. El asistente de rolleo (`wizards/lumber_vessel_rollover_wizard.py`) **no
   invoca** ningún método/auditoría R2 (`grep` → `NONE`).
2. R2 sólo agrega audits `rebaja_return_total`/`rebaja_reverse`; las aserciones
   fallidas cuentan audits `vessel_rollover`, que R2 no produce.
3. Los registros “sobrantes” (19699/19702) son de UAT Rolleo, con fecha anterior
   a la sesión R2 y `batch_id` `VESSEL-ROLLOVER-202610040352…`.
4. La funcionalidad de rolleo **sí operó** (test_01 cambia `vessel_id`);
   falla únicamente la verificación de conteo de auditoría global.

**Avisos:** `UserWarning` preexistentes de `madenat.lumber.intake.console`
(ajenas a R2); sin otros.

## 4. Validación de flujos afectados

| Flujo | Cubierto por | Resultado |
|---|---|---|
| R2: retorno total, idempotencia, clasificación compensada, SV `volume` | `TestRebajaReturnTotal` (T-R2-1…12) | ✅ PASS |
| Rebaja estándar, zarpe, B-01, permisos, conservación de stock | `TestRebajaContenedor` (31) | ✅ PASS |
| Pendiente no `shipped`, B-01 `open`, gates Entrega y RPC | `TestShipmentB01Exception` (12) | ✅ PASS |
| R1, `open→resolved`, composición congelada, gate Entrega | `TestB01Regularization` (13) | ✅ PASS |
| Guard físico/terminal/financiero, write directo bloqueado | `TestShipmentReturnToDraft` (16) | ✅ PASS |
| Planificación marítima strict y preservación física | `TestVesselRollover` (10) | ⚠️ 5/10 (lógica OK; conteo de auditoría global afectado por UAT Rolleo) |

**Conclusión:** ningún flujo **funcional** de R2 ni de los flujos adyacentes de
rebaja/zarpe/B-01/R1/Borrador presenta fallo. El único fallo es de **verificación
de conteo de auditoría** en `TestVesselRollover`, por contaminación con datos
**UAT Rolleo** (aislamiento de test preexistente), no por comportamiento R2.

## 5. Comparación de conteos antes/después

| Tabla | Antes | Después |
|---|---|---|
| `stock_move` | 143 | **143** |
| `stock_move_line` | 210 | **210** |
| `stock_picking` | 28 | **28** |
| `stock_quant` | 171 | **171** |
| `stock_lot` | 127 | **127** |
| `lumber_export_shipment` | 15 | **15** |
| `lumber_container` | 16 | **16** |
| `lumber_shipment_line` | 6 | **6** |
| `madenat_audit_log` | 270 | **270** |
| `madenat_sv_operation` | 1 | **1** |
| `madenat_sv_imputation` | 1 | **1** |
| `stock_lot_cost_line` | 53 | **53** |
| `lumber_shipment_cost_line` | 0 | **0** |
| `account_move` | 1 | **1** |
| `account_payment` | 0 | **0** |
| `lumber_billing_consolidation` | 0 | **0** |

**Delta = 0** en todas las tablas: fixtures revertidos (TransactionCase). No
`rebaja_return_total` persistido; no `rebaja_reverse` persistido; no B-01
`resolved` adicional; no stock/picking/move/quant/lote adicional; no
costo/factura/pago/SV/imputación adicional.

## 6. Integridad de UAT / histórica

Revalidados **sin cambios**: histórica; **UAT Rolleo** (19699–19704,
`VESSEL-ROLLOVER-202610040352…`); UAT Borrador; **UAT B-01**
(13 `none` + 1 `open` + 1 `resolved`); **UAT R1** (shipment 1885
`in_transit`/`resolved`, container 1888 `rebajado`/`sealed`, lot 16312,
picking 7238 `done`, move 13973 `done`, audit 19941/19945).

## 7. Estado Git

Rama `feat/guia-correccion-documental-preservada-20261002` · HEAD `34c81272…` ·
working tree **33 entradas (24 ` M` + 9 `??`)** — idéntico a la línea base de esta
fase · **`git diff --check` CLEAN** · sin commit/push/PR/stash. Sin escritura SQL
ni update/install.

## 8. Dictamen

### **B. `REGRESIÓN FALLIDA` — PARCIAL, NO ATRIBUIBLE A R2**

**Resultado:** 89/94 PASS · 5 FAIL · 0 ERROR. Los 5 fallos son exclusivos de
`TestVesselRollover` y comparten una única causa raíz **preexistente /
ambiental**: su búsqueda global de auditorías `vessel_rollover` cuenta los
registros de la **UAT Rolleo** (`UAT-VR-20261004`), persistidos antes de esta
sesión. **R2 queda exonerado** (no toca el rolleo; sólo agrega audits
`rebaja_return_total`).

**Acción recomendada (fuera de alcance R2; requiere autorización):**
1. Corregir el aislamiento de `tests/test_vessel_rollover.py`: filtrar por
   `batch_id`/ids de la operación propia (o `madenat.audit.log` con el
   `batch_id` generado por el asistente) en lugar de `action_type` global.
2. **No** eliminar ni alterar los datos UAT Rolleo.
3. Reintentar el gate.

**Salvedad de gate:** todos los flujos **R2** y los flujos adyacentes de
**rebaja estándar, zarpe, B-01, R1 y Borrador** están **100% verdes**; ningún
fallo es de R2. Por tanto, si el defecto de aislamiento de `TestVesselRollover`
(preexistente) se excluye del alcance de R2, la regresión **R2** es
**APROBADA** y **apta para solicitar UAT R2**.

*No se creó UAT. No se ejecutó R2 persistente. No se avanzó a R3 ni
Entrega/Cierre. Fin del informe.*

