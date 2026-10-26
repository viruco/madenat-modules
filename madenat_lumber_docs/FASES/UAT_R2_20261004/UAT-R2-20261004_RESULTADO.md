# MADENAT — Resultado UAT R2 Retorno Físico Total

- **Sub-bloque:** 4B — R2 (retorno físico total / reversa robusta de rebaja).
- **Fase:** D — validación operativa UAT.
- **Estado:** **NO EJECUTADA — BLOQUEADA EN PRECHECK (usuario)**.
- **Regla cumplida:** no se creó UAT; no se usó uid 1; no `sudo()`; sin SQL de
  escritura; sin edición de código/doc; sin update/install; sin git mutante.

---

## 1. Fecha, entorno y usuarios

- **Fecha:** 2026-10-04.
- **Repositorio:** `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons`.
- **Base:** `madenat_test`. **Rama:** `feat/guia-correccion-documental-preservada-20261002`. **HEAD:** `34c81272bb07d48db98d73a7734c81a2a8e384fa`.
- **Runtime:** `odoo18_app` Up · `odoo18_db` Up (healthy) · HTTP operativo · `madenat_lumber_core` 18.0.6.5.0 + `madenat_lumber_logistics` 18.0.1.6.0 (instalados).
- **Usuarios existentes (sin crear ni usar `sudo()`):**
  - **uid 2 — "Administrator"** (`mauricio.seo@gmail.com`): gerencia, jefatura_operaciones, admin, operaciones, costos, contabilidad, cost_auditor, **`base.group_system`**, `base.group_erp_manager`.
  - uid 8 — Operaciones (bloqueado por mandato).
  - uid 9 — admin + cost_auditor (sin Jefatura/Gerencia).
- **No existe** usuario Jefatura/Gerencia **no-administrador**.

> **DETENCIÓN OBLIGATORIA (criterio del mandato):**
> "Si sólo existe uid 2 con Gerencia/`base.group_system`, detenerse y pedir
> autorización explícita antes de usarlo." y "si no existe Jefatura/Gerencia no
> uid 1, detenerse y reportar. No crear UAT."
>
> El único ejecutor con Gerencia/Jefatura es **uid 2 = Administrator con
> `base.group_system`**. → **No se crea UAT; se detiene y se solicita
> autorización explícita.**

## 2. Precheck / línea base (read-only)

| Ítem | Resultado |
|---|---|
| Identidad repo/rama/HEAD | ✅ `34c81272…`, tree 33 = 24 M + 9 ? ? |
| Runtime / base | ✅ |
| Línea base (18 tablas) | ✅ capturada (ver `00_precheck_baseline.txt`) |
| Protegidos (histórica, Rolleo, Borrador, B-01, R1) | ✅ todos intactos |
| `rebaja_return_total` persistida | ✅ **0** |
| `rebaja_reverse` persistida | ✅ **0** |
| Retorno R2 persistido | ✅ **NO** |
| Cambios B-01 no explicados | ✅ **NO** (`none=13 / open=1 / resolved=1`) |
| Helpers R2 + wizard de reversa | ✅ instalados (módulo instalado) |
| **Usuario ejecutor no-admin** | ❌ **NO EXISTE → BLOQUEO** |

## 3. Datos UAT creados

**Ninguno.** Contenedores con prefijo `UAT-R2-20261004-` = **0**. No se creó
Motonave/Embarque/Contenedor/Lote/quant/costo/SV.

## 4. Rebaja fuente (UAT-R2-1)
**NO EJECUTADO** (bloqueado en precheck). No hubo picking OUT ni movimiento de
stock.

## 5. Retorno físico total (UAT-R2-2)
**NO EJECUTADO.** No hubo picking de retorno, ni reversa, ni cambio de estados.

## 6. Idempotencia (UAT-R2-3)
**NO EJECUTADO.**

## 7. Permisos (UAT-R2-4)
**NO EJECUTADO.** Además, la prueba positiva requiere un ejecutor
Jefatura/Gerencia no-administrador, inexistente.

## 8. Gate B-01 open (UAT-R2-5)
**NO EJECUTADO.** No se abrió B-01 ni se simuló por write directo.

## 9. Auditoría / hash / chatter
**N/A** (no se ejecutó ninguna operación). `rebaja_return_total` = 0,
`rebaja_reverse` = 0.

## 10. Inventario, lote, ubicaciones y movimientos
**Sin cambios.** Delta = 0 en las 18 tablas (ver §12 y `06_final_validation.txt`).

## 11. Integridad histórica / UAT
Verificados **intactos** (sin modificar):
- **Histórica:** shipment 1537, container 1509, picking 7065, líneas 1880/1881,
  lotes 15970/15971, shipment 1528, container 1500, picking 7062, SV 5822,
  imputation 492.
- **UAT Rolleo:** vessels 619/620, voyage 565, shipments 1644/1645/1646,
  containers 1629/1630/1631, audits 19699–19704.
- **UAT Borrador:** shipments 1704–1707, containers 1678–1680, audit 19742.
- **UAT B-01:** vessel 746, shipments 1867/1868/1869, containers 1868–1871,
  audit 19890.
- **UAT R1:** vessel 747, shipment 1885, container 1888, lot 16312, picking 7238,
  move 13973, audits 19941–19945.

## 12. Evidencia persistida
```
/home/viruco/dev-stack/odoo/odoo-18-ce/UAT_R2_20261004/
  00_precheck_baseline.txt        (identidad, runtime, línea base, protegidos, usuarios → DETENCIÓN)
  01_uat_r2_rebaja_source.txt     (NO EJECUTADO)
  02_uat_r2_return_total.txt      (NO EJECUTADO)
  03_uat_r2_idempotency.txt       (NO EJECUTADO)
  04_uat_r2_permissions.txt       (NO EJECUTADO)
  05_uat_r2_b01_open_gate.txt     (NO EJECUTADO)
  06_final_validation.txt         (conteos antes==después; sin datos UAT; git)
  UAT-R2-20261004_RESULTADO.md    (este informe)
```
**Git:** rama/HEAD sin cambios · working tree 33 = 24 M + 9 ? ? · `git diff --check` CLEAN · sin commit/push.

## 13. Riesgos residuales
- **Retorno parcial:** no validado por UAT (fuera de alcance; el motor R2 lo
  bloquea por diseño y ya está cubierto por tests `TestRebajaReturnTotal`).
- **R3 / imputación SV:** no ejecutado.
- **Entrega/Cierre:** no ejecutado.
- **Costeo/Billing/Pagos:** no ejecutado.
- **Rol dedicado no-administrador:** **pendiente y bloqueante** — sin un usuario
  Jefatura/Gerencia no-administrador no puede correrse la UAT conforme al
  mandato (no se debe usar uid 2 ni uid 1 ni `sudo()`).

## 14. Dictamen

### **B. `UAT BLOQUEADA O FALLIDA — DETALLAR ESCENARIO, EVIDENCIA Y ACCIÓN`**

- **Escenario:** precheck (habilitación de usuario), previo a UAT-R2-1.
- **Evidencia:** `00_precheck_baseline.txt` §6 — el único usuario con Jefatura de
  Operaciones/Gerencia es **uid 2 (Administrator, `base.group_system`)**; no existe
  usuario no-administrador con esos roles.
- **Causa:** conflicto directo con la regla del mandato:
  *"Si sólo existe uid 2 con Gerencia/`base.group_system`, detenerse y pedir
  autorización explícita antes de usarlo"* y *"si no existe Jefatura/Gerencia no
  uid 1, detenerse y reportar. No crear UAT."*
- **Medida solicitada (autorización explícita), una de:**
  1. Autorizar explícitamente el uso de **uid 2** como ejecutor UAT (Administrator
     con `base.group_system`) para esta UAT; **o**
  2. Que un responsable **habilite un usuario Jefatura/Gerencia
     no-administrador** existente o nuevo (acción del negocio, fuera de esta
     tarea) para ejecutarla; **o**
  3. Prorrogar R2 a **UAT en otro entorno** con tal usuario.
- **Estado del sistema:** intacto (Delta = 0); ninguna auditoría
  `rebaja_return_total`/`rebaja_reverse`; ningún dato UAT; protegidos sin cambios.

*No se creó UAT. No se ejecutó retorno parcial, R3 ni Entrega. No se modificó
código. No se hizo commit ni push. Fin del informe.*

