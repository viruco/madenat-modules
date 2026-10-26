# MADENAT — Resultado Corrección Aislamiento Rolleo y Regresión R2

- **Sub-bloque:** 4B — R2. **Fase:** C.2 — corrección de aislamiento de test + regresión verde previa a UAT.
- **Archivo modificado (único, autorizado):** `madenat_lumber_logistics/tests/test_vessel_rollover.py`.
- **Sin cambios productivos, sin UAT, sin datos persistentes, sin `-u`/`-i`.**
- **Fecha:** 2026-10-04.

---

## 1. Precheck e invariantes

| Ítem | Valor | Estado |
|---|---|---|
| Repo | `custom_addons/` | ✅ |
| Rama | `feat/guia-correccion-documental-preservada-20261002` | ✅ |
| HEAD | `34c81272bb07d48db98d73a7734c81a2a8e384fa` | ✅ |
| Working tree (pre) | **33 = 24 ` M` + 9 `??`** | ✅ |
| DB / runtime | `madenat_test` · `odoo18_app` Up · `odoo18_db` healthy | ✅ |

**UAT Rolleo intacta:** vessels **619** (`UAT-VR-20261004-ORIG-VESSEL`) / **620**
(`…DEST-VESSEL`) · voyage **565** (`UAT-VR-20261004-DEST-VOY-01`) · shipments
**1644/1645/1646** · containers **1629/1630/1631** · audits **19699–19704**
(`vessel_rollover` 19699, 19702 · `vessel_rollover_item` 19700, 19701, 19703,
19704). **UAT Borrador / B-01 / R1 intactas** (B-01: 13 `none` + 1 `open` + 1
`resolved`). Línea base de inventario/finanzas/SV sin variación.

## 2. Causa raíz de los cinco fallos

Los 5 fallos (`test_01`, `test_03`, `test_06`, `test_09`, `test_10`) usaban
**búsquedas de auditoría GLOBALES** sin acotar al fixture:

| Test | Consulta original | Aserción | Resultado |
|---|---|---|---|
| test_01 | `search([('action_type','=','vessel_rollover')])` y `…_item` | `len==1` / `len==2` | 3 / 6 (contaminado) |
| test_03 | `assertFalse(search([('action_type','=','vessel_rollover')]))` | sin auditoría | encuentra 19699/19702 |
| test_06 | ídem | sin auditoría | encuentra 19699/19702 |
| test_09 | ídem | sin auditoría | encuentra 19699/19702 |
| test_10 | `search([('action_type','=','vessel_rollover')])` y `…_item` | `len==1` / `len==2` | 3 / 6 |

**No eran fallos funcionales** de R2 ni del Rolleo: la tabla `madenat.audit.log`
contiene **UAT persistida** (`UAT-VR-20261004`, 2026-10-04 03:52), previa a la
sesión, que inflaba los conteos globales.

## 3. Cambio de aislamiento implementado

Sólo en `tests/test_vessel_rollover.py`. Se añadieron dos helpers privados y se
actualizaron **únicamente** las consultas/aserciones de auditoría de los 5 tests:

```python
def _audit_ids_before(self):
    """Set de IDs de `madenat.audit.log` existentes ANTES de la operación."""
    return set(self.AuditLog.search([]).ids)

def _new_audits(self, audit_ids_before, action_type=None):
    """Auditorías creadas después del baseline (opcionalmente por tipo)."""
    domain = [('id', 'not in', list(audit_ids_before))]
    if action_type:
        domain.append(('action_type', '=', action_type))
    return self.AuditLog.search(domain)
```

Cada test captura `audits_before = self._audit_ids_before()` **inmediatamente
antes** de su operación y consulta con `self._new_audits(audits_before, <tipo>)`.
Criterio aplicado (opción 3 del mandato, declarada como la más robusta por el
propio mandato): aislamiento por **IDs nuevos post-baseline**, sin presuponer el
formato de `batch_id`/snapshot, **sin** `limit=1`, **sin** filtro por fecha, **sin**
borrar UAT y **sin** suprimir aserciones. En tests con múltiples operaciones se
captura baseline antes de cada acción. Se conservan **todas** las aserciones
funcionales (reasignación nave/viaje, modo strict, bloqueos, auditoría+hash,
invariantes de stock, permisos).

## 4. Evidencia de que UAT persistida no fue tocada

- Auditorías `19699–19704` siguen presentes con **id/action_type/batch_id
  idénticos** tras las dos corridas de test.
- No se ejecutó `unlink`/escritura SQL sobre `madenat.audit.log`; el aislamiento
  es sólo de **lectura** (`id not in baseline`).
- `_new_audits` únicamente excluye del **conteo del test** los IDs previos; no los
  modifica.

## 5. Resultado completo de TestVesselRollover

`--test-tags /madenat_lumber_logistics:TestVesselRollover` →
**`0 failed, 0 error(s) of 10 tests`** · 4.28 s · 1 486 queries · **EXIT=0**.
(Los 10 métodos: T1…T10 — incluidos los 5 antes fallidos.)

## 6. Resultado de regresión acotada: 94/94

`--test-tags` de las 6 clases (sin `-u`/`-i`) →
**`0 failed, 0 error(s) of 94 tests`** · 36.9 s · 25 321 queries · **EXIT=0**.

| Clase | Nº | PASS | FAIL |
|---|---|---|---|
| `TestRebajaReturnTotal` | 12 | 12 | 0 |
| `TestRebajaContenedor` | 31 | 31 | 0 |
| `TestShipmentB01Exception` | 12 | 12 | 0 |
| `TestB01Regularization` | 13 | 13 | 0 |
| `TestShipmentReturnToDraft` | 16 | 16 | 0 |
| `TestVesselRollover` | 10 | 10 | 0 |
| **Total** | **94** | **94** | **0** |

## 7. Conteos antes/después

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

**Delta = 0** en las 16 tablas (fixtures revertidos, TransactionCase). No hay
`rebaja_reverse` ni `rebaja_return_total` persistidos (0 filas); no hay B-01
`resolved` adicional (13 `none` + 1 `open` + 1 `resolved`); sin nuevos
stock/picking/quant/lote/costo/factura/pago/SV/imputación.

## 8. Integridad de UAT / histórica

Revalidados sin cambios: histórica; **UAT Rolleo** (vessels 619/620, voyage 565,
shipments 1644/1645/1646, containers 1629/1630/1631, audits 19699–19704);
UAT Borrador; **UAT B-01**; **UAT R1** (shipment 1885, container 1888,
lot 16312, picking 7238, move 13973, audit 19941/19945).

## 9. Estado Git

| Ítem | Valor |
|---|---|
| Rama | `feat/guia-correccion-documental-preservada-20261002` |
| HEAD | `34c81272…` |
| Working tree | **33 = 24 ` M` + 9 `??`** (sin entradas nuevas; `test_vessel_rollover.py` ya era `??`) |
| Cambios de esta fase | **sólo** `madenat_lumber_logistics/tests/test_vessel_rollover.py` (verificado por `mtime`: 15:18 vs R2 14:4x–14:5x) |
| `git diff --check` | **CLEAN** |
| Commit/push/PR/stash/checkout/reset/rebase | **no ejecutado** |
| Update/install, SQL de escritura | **no ejecutado** |

## 10. Dictamen

### **A. `REGRESIÓN R2 Y ROLLEO APROBADA — APTO PARA SOLICITAR UAT R2`**

- Los 5 fallos previos eran de **aislamiento de test** (búsqueda global de
  auditoría vs. UAT Rolleo persistida), **no** funcionales de R2 ni de Rolleo.
- Corrección aplicada **sólo** en `tests/test_vessel_rollover.py`, mediante
  baseline de IDs (`id not in baseline`), sin debilitar aserciones, sin
  `limit=1`, sin filtros ambiguos, sin tocar UAT.
- **`TestVesselRollover` 10/10** y **regresión acotada 94/94** (0 failures,
  0 errors); conteos persistidos **idénticos** a la línea base; UAT histórica,
  Rolleo, Borrador, B-01 y R1 intactas; working tree sólo incorpora el cambio
  autorizado de test; `git diff --check` limpio.

*No se creó UAT R2. No se ejecutó R2 persistente. No se avanzó a R3 ni
Entrega/Cierre. Fin del informe.*

