# MAPA DE ELIMINACIÓN — rutas UI → métodos → permisos → dependencias → bloqueadores

Base: `madenat_test` (local). Caso: `madenat.guia.processing` id **33152** (`name=15183`, `cancelled`).
Rutas relativas a `custom_addons/`.

## 0. Cuatro rutas distintas (no son equivalentes)

| # | Ruta (UI) | Registro real | ¿Borra físicamente? |
|---|---|---|---|
| A | Menú estándar **Eliminar** de la lista/form de la Consola | `madenat.lumber.intake.console` (vista SQL) | No (ACL + `_auto=False`) |
| B | **Ciclo de vida de la guía → Modo A** | `madenat.guia.processing` (33152) | Sí, vía `unlink()` |
| C | **Ciclo de vida → Modo B** (Cancelar) | `madenat.guia.processing` | No (cancela y conserva) |
| D | **Ciclo de vida → Modo C** (Purga) | `madenat.guia.processing` + lote técnico | Sí, acotada |

---

## A. "Eliminar" del menú estándar (lista/form de la Consola)

- **Modelo real:** `madenat.lumber.intake.console` — **vista SQL** (`_auto = False`),
  `intake_console.py:41-43`; `init()` recrea la vista (`:513-518`).
- **Vista:** `view_madenat_lumber_intake_console_list` (`intake_console_views.xml:7-49`),
  form `:54`; **acción** `action_madenat_lumber_intake_console` (`:1007-1018`).
- **Método:** `unlink()` heredado de `BaseModel` — **no hay override** en `intake_console.py`.
- **ACL:** `access_madenat_lumber_intake_console_user` → **`perm_unlink = 0`**
  (`security/ir.model.access.csv:3`). Auditoría y Contabilidad: `1,0,0,0`.
- **Punto de rechazo:** (1) **ACL** niega `unlink` al grupo Operaciones → `AccessError`;
  (2) aunque existiera permiso, sobre una vista SQL el `DELETE` no es aplicable (modelo `_auto=False`).
- **Diferencia prevista vs. verificada:** en el XML no existe botón "Eliminar"; el borrado estándar
  (menú ⚙️ Acción → Eliminar) queda bloqueado por ACL + ser vista. **No** es la ruta que produjo el
  mensaje reportado.

## B. "Ciclo de vida de la guía" → Modo A (eliminación definitiva)

- **Origen UI:** botón `action_open_guide_lifecycle` en la Consola
  (`intake_console_views.xml:116-121`; visible si `ingestion_type in ('processed','volume')`).
- **Abre el asistente:** `MadenatLumberIntakeConsoleSv.action_open_guide_lifecycle()`
  (`intake_console_sv.py:284-306`) → devuelve `act_window` a `madenat.lumber.intake.guide.lifecycle`
  con `context = {'default_guia_processing_id': guia.id, 'default_console_id': self.id}`.
- **Ejecuta:** `action_run()` (`intake_guide_lifecycle_wizard.py:576-598`) → Modo A →
  `_run_delete_definitive()` (`:601-612`) → **`guia.unlink()`**.
- **Registro sobre el que actúa:** `madenat.guia.processing` (tabla real), **no** la vista de la Consola.
- **Precondición** (`_requirements_ok`, `:505-519`): `not _lifecycle_blockers(diag,'A')` **y**
  `acknowledge`.
  - `_lifecycle_blockers(...,'A')` (`:468-486`) = (estado ∉ {draft,cancelled}) + `_trace_blockers` (`:367-420`).
  - **Punto exacto de rechazo:** `action_run` lanza `UserError`
    `"El modo %(mode)s no cumple sus precondiciones:\n%(blockers)s"` (`:585-593`),
    **antes** de llamar a `unlink()`. El bloqueador del caso es `pickings` (`:390`).
- **Permisos/ACL:** wizard `model_madenat_lumber_intake_guide_lifecycle` (`perm_unlink=0`, irrelevante:
  es `TransientModel`); el borrado recae sobre `madenat.guia.processing` → **doble capa** (ver D.7).

## C. Modo B (Cancelar y conservar)

- `_run_cancel_and_keep()` (`intake_guide_lifecycle_wizard.py:617-633`): `message_post` + delega en el
  método canónico **`action_force_cancel()`** (`madenat_lumber_core/models/madenat_guia_processing.py:5091`).
- `action_force_cancel` **no borra**: revierte consumo BT-04 (`_reverse_consumption_picking`), retorna
  pickings `done` por ORM (`:5224-5298`), cancela pickings no-done (`:5316-5340`), desvincula lotes
  (`:5352-5363`) y fija `state='cancelled'` (`:5380-5393`).
- Exige rol operativo: `_require_intake_operational_group()` → `assert_intake_operational_user`
  (`mixin_lumber_ingest.py:87-94`).

## D. Modo C (Purga controlada)

- `_run_controlled_purge()` (`:636-660`). Requiere `confirmation == 'PURGAR'` **y** grupo Jefatura
  (`GROUP_JEFATURA = 'madenat_lumber_core.group_madenat_jefatura_operaciones'`, `:27`).
- Bloqueadores de purga `_purge_blockers` (`:422-466`: historia material, quants, evidencia, etc.).

## Otras rutas de la Consola (contexto)

- **Cancelar preliminar:** `action_madenat_lumber_intake_cancel` (`intake_cancel_wizard_views.xml:34`)
  → wizard `madenat.lumber.intake.cancel` → `action_confirm_cancel` (`intake_cancel_wizard.py:24-47`),
  actúa sobre **`lumber.reception`** (no la guía); rechaza si `state=='done'`/hay `lot_ids`/`picking_id`.

---

## E. Dependencias del borrado de `madenat.guia.processing` (doble capa)

**Capa 1 — asistente (Modo A):** `_requirements_ok` bloqueará si hay cualquier traza material
(§ bloqueadores). Es donde se detiene el caso reportado.

**Capa 2 — override `unlink()` del core** (`madenat_guia_processing.py:5887-5910`):
1. Excepción **test-only** `_sv_test_cleanup_allowed('madenat.guia.processing', ids)`
   (`:5894-5896`) — exige marcador ESTRICTO (`--test-enable` + BD con `test`), **no** el parámetro de dev.
2. `state in ('draft','cancelled')` o `UserError` "SEGURIDAD MADENAT" (`:5898-5905`).
3. `_cleanup_orphan_moves_guia()` (`:5912-…`) exige **`stock.group_stock_manager`** (`:5918-5922`) y
   elimina `stock.move` huérfanos (`origin in names`, `picking_id=False`), protegiendo los que tienen
   `quantity>0` (los renombra `HUERFANO-PROTEGIDO-…`).

> Conclusión de dependencias: aunque el Modo A pasara sus precondiciones, `unlink()` **además** exige
> `stock.group_stock_manager`. Ninguno de estos guards se ejecutó en el caso (el rechazo fue antes, en `action_run`).

## F. Atribución de la guía 33152 ↔ documentos

| Vinculación | Evidencia (solo lectura) | Exclusiva de la guía 33152 |
|---|---|---|
| **1. Textual por `origin`** | `stock_picking` **436** `origin='15183'` == `guia.name` | **NO** — '15183' es también `lumber.reception.guia_numero` |
| **2. FK `guia_processing_id`** | 436 → **NULL**; 7813 → **33152** | 436 **no**; el retorno sí |
| **3. `reception_id`** | 436 → `reception_id=1369` (`lumber.reception` name 15183) | Apunta a la recepción, no a la guía |
| **4. Lotes / movimientos** | 436: move 6420 + **13 move lines** en lotes **2614-2625** (pertenecen a `reception_id=1369`, no a la guía) | **NO** (la guía no tiene `stock.lot` con su FK) |
| **5. Cadena de retornos** | 436 (EMB-00227) → **7813** (EMB-04201, *Return of EMB-00227*, FK=33152) → **7814** (WH/OUT/02754, *Devolución de EMB-04201*) | Parcial (el retorno sí porta FK) |
| **6. Evidencia/auditoría** | Guía: **4 adjuntos** (PDF/Excel) + **5 mensajes**; `madenat.audit.log` 1 evento `creation`. Costes=0, valoraciones=0, consolidaciones=0, embarques=0, genéricas=0 | La evidencia es **de la guía** |

### F.1 Por qué el retorno 7813 quedó vinculado a la guía (atribución)

`action_force_cancel` crea el retorno **sin** `guia_processing_id` (`:5225-5231`). Sin embargo 7813 lo
tiene = 33152. **Causa raíz (inferencia de alta confianza):** el asistente se abre con
`context['default_guia_processing_id'] = guia.id` (`intake_console_sv.py:302-304`); ese *default* lo lleva
el `env` del wizard y, al ejecutarse `guia.action_force_cancel()` con el mismo `env`, Odoo inyecta
`guia_processing_id` en **cualquier** `stock.picking` creado dentro de ese contexto (el campo existe en
`stock.picking`, `stock_picking.py:45-54`). El retorno de cancelación se crea con ese `env` → **el FK se
"filtra" al retorno**. No existe override de `create` ni default declarado en `stock_picking.py`.

- **Verificación posible:** que el retorno porte un FK que el código no asigna explícitamente es
  consistente con el mecanismo `default_*` de Odoo. **No** pudo confirmarse por ejecución (prohibido
  ejecutar métodos). Se clasifica como **inferencia** (ver `DICTAMEN.md` §3).
- **Consecuencia:** el retorno de una cancelación hecha **desde el wizard** queda marcado con la guía;
  una cancelación desde el botón de formulario de la guía (`guia_processing_views.xml:155`, sin ese
  contexto) **no** lo marcaría. Diferencia relevante para el diagnóstico (el guard de Modo A **no** mira
  `guia_processing_id`; mira `origin` textual y lotes — ver §B).

