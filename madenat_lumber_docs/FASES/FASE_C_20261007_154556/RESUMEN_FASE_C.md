# FASE C — Reparación del FK espurio del retorno 7813 (RESUMEN DE CIERRE)

Caso: guía **15183 / `madenat.guia.processing` ID 33152**. MADENAT — Odoo 18 CE.
Fecha: **2026-10-07** (UTC ≈ 18:45). Autorización: **únicamente Fase C**.

## 1. Alcance ejecutado

Cambio **único**: `stock.picking(7813).guia_processing_id`: **33152 → False**, por ORM,
en transacción controlada, con auditoría antes/después. Vía `odoo shell` one-shot
(contenedor efímero, `--no-http --max-cron-threads=0`), **con `odoo18_app` detenido**
(sin otro proceso sobre `madenat_test`; solo la sesión `psql` administrativa propia).

## 2. Ejecutor y permisos

- **Usuario 8 — Cristhian Elgueta** (`base.group_user` + `stock.group_stock_manager`).
- `su = False` → **sin `sudo()`**, sin privilegios elevados.
- No se usó `SQL UPDATE`.

## 3. Precondiciones verificadas DENTRO de la transacción

| Precondición | Valor verificado |
|---|---|
| Picking 7813 existe | ✔ (bloqueado con `SELECT … FOR UPDATE`) |
| `guia_processing_id` = 33152 | ✔ |
| Guía 33152 = 15183 y `cancelled` | ✔ |
| Move 6420 → picking 436 | ✔ |
| Move 14542 → picking 7813, `origin_returned_move_id=6420` | ✔ |
| Move 14543 → picking 7814, `origin_returned_move_id=14542` | ✔ |
| Lotes 2614–2625 → `reception_id=1369` | ✔ (12/12) |
| Sin nuevas dependencias propias | ✔ `own_pickings == {7813}`, `own_lots` vacío |

**Efectos adicionales del `write`:** comprobado que **no** hay overrides que reaccionen:
`stock.picking` solo es heredado por `madenat_lumber_core/models/stock_picking.py` (sin
`def write`), y no existe `@api.depends/constrains/onchange` sobre `guia_processing_id`.

## 4. Evidencia de la reparación

**Antes (BEFORE):**
```json
{"picking_id": 7813, "picking_name": "EMB-04201", "state": "done",
 "origin": "Return of EMB-00227", "guia_processing_id": 33152,
 "reception_id": false, "move_14542_origin_returned_move_id": 6420,
 "lots_2614_2625": [2614,2615,2616,2617,2618,2619,2620,2621,2622,2623,2624,2625]}
```
**Después (AFTER):** `guia_processing_id = False`. `COMMIT_OK`.

**Auditoría** (`madenat.audit.log`, id **21739**, `action_type='deviation'`):
- `guia_processing_id = 33152` (vínculo `ondelete='set null'` → **sobrevive** al borrado de la guía).
- `user_id = 8`; `audit_hash = 0da380242edece69bef097450d8fcb4f74f8d8a6b7e8849682deb2f7e894905a`.
- Snapshot JSON antes/después + referencia **`FIX_DELETE_INTAKE_20261007_145130 / FASE_C`**.

## 5. Postcondiciones (verificadas en-transacción y por SQL independiente)

| Postcondición | Resultado |
|---|---|
| Picking 7813 `guia_processing_id` vacío | ✔ NULL |
| Guía 33152 existe y sigue `cancelled` | ✔ |
| Pickings 436 / 7813 / 7814 estado y datos | ✔ intactos (`done`) |
| Moves 6420 / 14542 / 14543 y relaciones | ✔ intactos |
| Lotes 2614–2625 → recepción 1369 | ✔ 12/12 |
| Mensajes / adjuntos de la guía | ✔ 5 / 4 (sin cambios) |
| Auditoría persistida | ✔ id 21739 |

Reversión si hubiera fallado: `rollback` total (el script hace `rollback` + `os._exit(3)`
ante cualquier desviación). No ocurrió.

## 6. Diagnóstico Modo A recalculado (solo lectura, sin eliminar)

```
GUIA 33152 15183 cancelled
OWN_PICKINGS []          FOREIGN_PICKINGS ['EMB-00227']
AMBIGUOUS_PICKINGS []    DIRECT_LINK_PICKINGS []
BLOCKERS_A []            REQUIREMENTS_OK_A True
LOTS_PROPIES 0  QUANTS 0  MOVES 0
```

- Documentos **propios**: ninguno. **Ajenos**: `EMB-00227` (436, de la recepción 1369).
  **Ambiguos**: ninguno. **Vínculo directo**: ninguno.
- **No quedan bloqueadores**; `REQUIREMENTS_OK_A = True` (entorno de desarrollo).

## 7. Tratamiento documental que correspondería al borrado posterior (Fase E)

- La guía tiene **5 `mail.message`** y **4 `ir.attachment`** en la BD
  (2 adjuntos de **campo binario**: `guide_pdf_file`, `excel_file`; 2 de **chatter**:
  `15183.xls`, `GUIA 15183 MADENAT 02-09-2026.pdf`).
- El asistente, en **Modo A y en entorno de test**, **relaja** las categorías documentales
  (`DEV_RELAXABLE_KEYS = ('messages','attachments')` + `_lifecycle_dev_environment_ok()`),
  por lo que **no bloquean** el borrado.
- El **snapshot firmado** publicado antes del `unlink()` (`guia_delete_permanent`) preserva
  metadatos de evidencia: **4 mensajes** (excluye el aviso automático de creación) y
  **2 adjuntos de chatter** (el `search` de `ir.attachment` **excluye los de campo binario**).
- **LIMITACIÓN a declarar:** el snapshot **no** registra los 2 adjuntos de **campo binario**
  (`guide_pdf_file`/`excel_file`). En **producción** (BD sin `test` o sin el parámetro),
  el Modo A **bloquearía** por evidencia y su tratamiento sería una decisión aparte.

## 8. Confirmaciones

- **Sólo** se reparó el FK autorizado (`guia_processing_id` de 7813) **y** su auditoría.
- **NO** se eliminó la guía 33152/15183.
- **NO** se volvió a cancelar.
- La cadena 436→7813→7814 permanece **intacta**.
- **NO** se modificaron movimientos, lotes, cantidades, ubicaciones, reservas, valoración ni
  contabilidad; **NO** se tocó producción, CANON ni `IMPL_SERVICE_RETURN_20261006/`; sin commit/push.
- Código **sin cambios** en Fase C: HEAD `e302c488…`; `git status` = 45 entradas (igual que al cierre de Fase B).

## 9. Servicios (estado final)

`odoo18_app` **Up** (HTTP `/web/login` = 200; **0** ERROR/CRITICAL/Traceback desde el reinicio)
· `odoo18_db` Up (healthy).

## 10. Límites / pendientes

- **UI real (navegador) pendiente** → Fase D.
- Ventana residual de concurrencia general del producto (no resuelta).
- El snapshot de borrado omite adjuntos de campo binario (ver §7).
