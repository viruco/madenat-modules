# ACCIONES VISIBLES DEL ASISTENTE «REGISTRAR REBAJA» (UI) — 2026-10-11

**Incidencia:** Mauricio no ve acciones para guardar ni un recorrido claro para mantener las rebajas.
**Entorno:** `madenat_test`. **Módulo:** `madenat_lumber_logistics` **18.0.1.18.0 → 18.0.1.19.0**.
**Sin commit/push/despliegue. Sin reparación histórica.**

## 1. Causa exacta de las acciones ausentes
El asistente se abre como **formulario amplio** (`action_madenat_sv_imputation_wizard`, `target = current`)
pero sus operaciones estaban **sólo** dentro de un **`<footer>`**. En Odoo, un `<footer>` de vista form
**se renderiza únicamente en diálogos** (`target="new"`); en un formulario de **página completa**
(`target="current"`) **no se muestra**. La vista **no tenía `<header>`**.

**Evidencia del arch efectivo (vista id 2889):**

| Comprobación | Valor |
| --- | --- |
| `arch_db->>'en_US' like '%<header%'` | **false** |
| `... like '%<footer%'` | **true** |
| `... like '%action_prepare%'` / `'%action_apply%'` | true / true |
| `ir_act_window.target` (view_id 2889) | **current** |

⇒ «Guardar borrador», «Revisar y aplicar», «Dejar pendiente», «Proponer FIFO» y «Cancelar» **no eran
visibles** en el recorrido real (sí existían como métodos). Descartado: caché, grupos, estado del
registro, acción que abre un formulario incompleto y botones ocultos por estados.

## 2. Vista/acción efectiva antes y después
- **Antes:** form `madenat.sv.imputation.wizard.form` con `<footer>` (acciones) y **sin** `<header>`;
  action `target=current`.
- **Después:** el **mismo** form con **`<header>` nativo** (acciones operativas) y **sin `<footer>`**;
  action `target=current` (sin cambios). Sin vista/acción nueva.

## 3. Ubicación y método de cada botón (header)
| Botón | Método | Visibilidad |
| --- | --- | --- |
| **Guardar borrador** | `action_prepare` | oculto si `imputation_state ∈ {applied, reversed, cancelled}` |
| **Revisar y aplicar** | `action_apply` | igual + `groups=` (Operaciones/Jefatura/Gerencia) |
| **Abrir documento** | `action_open_document` | visible sólo si hay `imputation_id` |
| **Dejar pendiente** | `action_pending` | oculto en estados no editables |
| **Proponer FIFO** | `action_propose_fifo` | oculto en estados no editables |
| **Descartar y volver** | `action_discard_changes` | siempre (vuelve al SV) |

Todos son `type="object"` (procesan los cambios del cliente antes de ejecutar y respetan permisos/estados);
el backend valida además (permisos, contrato de reparto, inmutabilidad).

## 4. Guardado persistente y confirmación
`action_prepare` → `_i2_build_imputation()` (crea/actualiza el **documento**) → `save_result` con la
**referencia real y el estado** («Documento IMP… guardado (estado: draft). No se ha aplicado la rebaja. Las
etiquetas seleccionadas mantienen la reserva documental prevista.») → **permanece** en el asistente
(recarga el propio registro, no navega al documento). «Abrir documento» abre el persistente cuando se
desea. Guardar el `TransientModel` **no** persiste la rebaja; la persiste `_i2_build_imputation`.

## 5. Recuperación desde el SV
Panel **«Trabajo en preparación (no aplicado)»** en el formulario del SV con **Continuar**
(`action_continue_preparation`, mismo formulario amplio) y **Abrir documento**; historial
(`action_open_sv_rebajas`) ampliado con `work_sv_lot_id`. Borradores/pendientes **separados** de lo aplicado
(`sv_assignment_work_*` ≠ `sv_assignment_applied_*`).

## 6. Matriz de mantenimiento por estado
| Estado | Acciones |
| --- | --- |
| draft/pending | consultar · **Continuar preparación** · **Aplicar** (si cumple contrato) · **Cancelar** · Abrir documento |
| applied | consultar resultado · historia · **Revertir** con motivo (Jefatura/Gerencia) · **no** editable ni eliminable |
| reversed/cancelled | consultar historia · preparar **nueva** operación (mecanismo existente) · no sobrescribe el original |
| reasignación | antes de aplicar: reparto editable; después: **reversa + nueva operación** trazable |

## 7. Descartar / cancelar / revertir (efectos)
- **Descartar y volver** (`action_discard_changes`): descarta los cambios **no guardados** y vuelve al
  **SV**; **no** elimina el documento guardado ni libera reservas (el asistente es transitorio).
- **Cancelar** (documento persistente, `action_cancel`): sólo draft/pending; **libera** su reserva;
  conserva historia.
- **Revertir** (`action_reverse`): sólo applied; **motivo obligatorio**; restituye **una vez**; historia
  preservada; no reabre como borrador.
- No se usa un único «Cancelar» ambiguo: son acciones distintas en sitios distintos.

## 8. Pruebas y regresión
| Conjunto | Resultado |
| --- | --- |
| `TestSvRebajaUiAcciones` (UI‑01..05 + conf.) | ver `logs/regression.log` |
| `TestSvRebajaPersistencia` (SAVE/FLOW/PHY) | 18/18 previo |
| Regresión de módulo | mismas fallas preexistentes |

`tests/test_sv_rebaja_ui_acciones.py`: UI‑01 entrada abre la vista correcta · UI‑02 acciones en `<header>`
y **sin** `<footer>` (+ `groups` en aplicar y `invisible` por estado) · UI‑03 los botones llaman a
métodos de **negocio** (crea el documento, abre el documento, descarta sin borrar) · UI‑04/05 visibilidad
coherente y sin expresiones fuera de contexto (proxy Owl) · confirmación con referencia real.

## 9. Evidencia de navegador
**Sin navegador en el entorno** ⇒ límite declarado; **no** se afirma «acciones verificadas en pantalla».
Guion exacto en `docs/GUION_NAVEGADOR_UI.md`. Aceptación operativa **pendiente de Mauricio**.

## 10. Versión instalada
`madenat_lumber_logistics` **18.0.1.19.0** en `madenat_test` (sólo este módulo; sin `-u all`).

## 11. Documentación
CANON `19` §19.25, `02` §17.16.23, `03` §27, índice. Este expediente.

## 12. Archivos afectados y cambios ajenos
`wizards/madenat_sv_imputation_wizard.py`, `wizards/madenat_sv_imputation_wizard_views.xml`,
`models/madenat_sv_imputation.py` (`action_continue_preparation` sin `target='new'`),
`tests/__init__.py`, `__manifest__.py`, `CHANGELOG.md`, nuevo `tests/test_sv_rebaja_ui_acciones.py`.
WIP ajeno **preservado** (sin reset/clean/stash).

## 13. Pendientes
1. **Aceptación en navegador** (guion UI).
2. **Conflicto de dos sesiones** de borrador: «última escritura gana» (sin bloqueo optimista) — protección
   contra sobrescritura **pendiente de autorización**.
3. IMP02220 y `lot_flow_type` histórico: intactos.

## 14. Propuesta de commit (NO ejecutado)
```
fix(sv-rebaja): acciones operativas del asistente en <header> nativo (UI 18.0.1.19.0)

- Causa: acciones sólo en <footer> no renderizado en target=current
- <header> con Guardar borrador / Revisar y aplicar / Abrir documento /
  Dejar pendiente / Proponer FIFO / Descartar y volver
- Confirmación con referencia real (save_result) y permanencia en el asistente
- action_open_document / action_discard_changes; imputation_state
- tests UI-01..05 + confirmación
```

**Sin commit · sin push · sin despliegue remoto · sin reparación histórica.**

