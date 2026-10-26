# DICTAMEN — eliminación del ingreso (guía 33152 / documento 15183)

Clasificación de cada afirmación:
**[V]** hecho verificado (archivo+línea o consulta de lectura) · **[R]** dato del informe previo
(confirmado en esta auditoría salvo que se indique) · **[I]** inferencia · **[U]** incertidumbre.

## 1. ¿Existe borrado físico desde Intake y por qué ruta?
**[V]** Sí, dos rutas de borrado físico:
- **Modo A** (`_run_delete_definitive` → `guia.unlink()`), `intake_guide_lifecycle_wizard.py:601-612`.
- **Modo C** (purga controlada de guía + lote técnico), `:636-660`.
La ruta **"Eliminar" estándar** de la Consola **no** borra (ACL `perm_unlink=0` + modelo vista SQL) — §A del mapa.

## 2. ¿Qué bloquea exactamente la operación reportada?
**[V]** El diagnóstico del **Modo A** cuenta como traza **material** un `stock.picking` con
`origin == guia.name` **en cualquier estado** (`_lifecycle_diagnosis` `:160-164`; etiqueta `:390`;
`_trace_blockers` `:367-420`). Existe **`stock.picking` id 436** `origin='15183'`, `state='done'`.
Por tanto `_requirements_ok('A')` (`:505-519`) devuelve **False** y `action_run` (`:585-593`) lanza:
`"El modo A no cumple sus precondiciones:\n- 1 albarán(es) con origin de la guía, en cualquier estado"`.
**[V]** No es un problema de permisos: el usuario 8 tiene `group_madenat_operaciones` **y**
`stock.group_stock_manager` (los dos guards relevantes pasarían).

## 3. ¿Qué ocurre si se usa el menú estándar "Eliminar"?
**[V]** La Consola (`madenat.lumber.intake.console`) es **vista SQL** (`_auto=False`, `intake_console.py:41-43`)
y su ACL del grupo Operaciones es **`perm_unlink=0`** (`security/ir.model.access.csv:3`). La acción
`action_madenat_lumber_intake_console` (`intake_console_views.xml:1007`) no habilita borrado.
→ [I] el cliente mostrará error de acceso/borrado; **[U]** el texto exacto en UI (no hubo clic auditado).
Es una ruta **distinta** del Modo A; el mensaje reportado provino del **Modo A**.

## 4. ¿El vínculo del retorno 7813 queda cubierto por las guardas?
**[V]** El guard de Modo A **no consulta `guia_processing_id`**. El retorno 7813
(`origin='Return of EMB-00227'`, FK=33152) **no** coincide con `origin == guia.name` (`'15183'`) ni con
lotes de la guía → **no cuenta como bloqueador**. El retorno solo queda "cubierto" indirectamente
porque el **picking original 436** sí coincide por texto.
→ **Punto ciego confirmado:** existe un vínculo fuerte guía↔retorno (FK) que el diagnóstico **ignora**,
y a la vez bloquea por un vínculo débil textual (`origin`) que **no es exclusivo** de la guía.
**[V]** El FK del retorno es `ondelete='set null'` (`stock_picking.py:49`): borrar la guía **no**
borraría ni colisionaría con el retorno; el FK no impide el borrado (solo quedaría a NULL).

## 5. ¿La atribución por origin puede confundir documentos?
**[V]** Sí. `'15183'` es **compartido**: `madenat.guia.processing.name='15183'` **y**
`lumber.reception.name/guia_numero='15183'`. El picking 436 pertenece a la **recepción 1369**
(`reception_id=1369`) con `guia_processing_id=NULL`. El guard lo captura **solo por texto**; sus 13
líneas de movimiento y sus lotes (2614-2625) no pertenecen a la guía. La coincidencia textual **no**
equivale a relación exclusiva con la guía.

## 6. ¿Qué permisos efectivos están verificados y cuáles no?
**[V] Verificado por código:** ACL consola Operaciones sin `unlink` (`ir.model.access.csv:3`); override
`unlink` del core exige `state in ('draft','cancelled')` y `stock.group_stock_manager`
(`madenat_guia_processing.py:5898-5922`); `action_force_cancel` y Modo C exigen rol operativo/Jefatura
(`mixin_lumber_ingest.py:87-94`; `GROUP_JEFATURA`).
**[V] Verificado por lectura de datos:** usuario 8 (Cristhian Elgueta) **tiene**
`group_madenat_operaciones`, `group_madenat_jefatura_operaciones`, `group_madenat_costos` y
`stock.group_stock_manager`.
**[U] No verificado:** los grupos efectivos del usuario **que realmente hará clic** en otra sesión/máquina
(aquí se verificó el usuario creador/cancelador id 8). No se ejecutó acción alguna.

## 7. ¿Qué requisitos cumple o incumple la guía 33152?
| Requisito Modo A | Estado del caso |
|---|---|
| `state in ('draft','cancelled')` | **[V] Cumple** (`cancelled`) |
| Sin lote con `volume_source_guia_id`/`guia_processing_id` | **[V] Cumple** (0 lotes de la guía) |
| **Sin picking ni movimiento** | **[V] INCUMPLE** (picking 436 `done`, `origin='15183'`) |
| Sin quant / operación SV / costo / valoración / consolidación / factura / contenedor / embarque | **[V] Cumple** (todos 0) |
| Sin período cerrado | **[I] Cumple** (no hay lock que cubra `2026-10-06`; no verificado a fondo) |
| Sin evidencia documental (chatter/adjuntos/genéricas) | **[V] INCUMPLE en producción**: 4 adjuntos (PDF/Excel) + 5 mensajes; **ignorados en dev** por el relax de Modo A (`DEV_RELAXABLE_KEYS`, `:65`; `madenat.dev_cleanup_enabled=True` + BD con `test`) |

## 8. ¿Qué queda pendiente antes de autorizar una eliminación?
1. **Decisión de política (AD-80):** el Modo A exige "sin picking ni movimiento"
   (`04_DECISION_LOG.md:1996`). Determinar si, para depuración en dev, el guard debe seguir siendo
   **textual** (`origin`) o apoyarse en el **vínculo fuerte** (`guia_processing_id`) / lotes de la guía.
2. **Objetivo real:** ¿depuración de datos de prueba en `madenat_test` o eliminación operativa en
   producción? Determina si aplica Modo A/C (dev) o Modo B (ya ejecutado).
3. **Permisos del usuario que ejecutará** (confirmar en su sesión).
4. **Tratamiento de evidencia** (PDF/Excel de la guía) y de la **cadena de retornos** (436→7813→7814).

---

## 9. Solución mínima propuesta (solo tras la evidencia)

> Regla observada: **no** se presenta un cambio de política como si fuera una corrección de etiqueta.

- **No se propone cambiar el guard de Modo A en esta fase.** El bloqueo es el comportamiento **diseñado**
  (AD-80: "sin picking ni movimiento"). Aflojarlo es **cambio de política**, no una corrección cosmética.
- **Corrección estrictamente cosmética viable (no altera comportamiento):** en `_trace_blockers`
  (`:388-404`) la etiqueta `'albarán(es) con origin de la guía'` (`:390`) **no refleja** el dominio real
  (`origin` **o** relación por lote, `:160-164`). Podría precisarse el texto para no inducir a error.
  Esto **no** desbloquea el caso y **no** cambia semántica.
- **Cambio funcional (requiere aprobación de política):** que Modo A (solo en entorno de dev) cuente
  pickings por el **vínculo fuerte** `guia_processing_id` y/o por lotes de la guía, en lugar de
  `origin` textual. Permitiría depurar guías cuyo albarán pertenece a **otro** documento (recepción),
  **sin** tocar stock. **No** se implementa ahora.
- **Ruta recomendada hoy:** ya se ejecutó **Modo B** (guía `cancelled`, trazabilidad conservada, retorno
  creado). Si el objetivo es "quitar el ingreso de la vista", corresponde evaluar archivado (backlog),
  no borrado de trazabilidad.

## 10. Límites de evidencia

- **U:** revisión exacta de código cargada en memoria (no verificable sin reiniciar; `--dev=reload`).
- **U:** texto exacto mostrado por el cliente Odoo para la ruta "Eliminar" estándar (sin sesión de UI).
- **I:** la causa del FK=33152 en el retorno 7813 (filtrado de `default_guia_processing_id`), consistente
  con el mecanismo de Odoo pero no confirmada por ejecución.
- **R→V:** los datos del informe previo (guía 33152, picking 436, retorno 7813, devolución 7814,
  Modo B ejecutado) **fueron re-verificados** por lectura en esta auditoría salvo lo señalado como [U]/[I].
- **Alcance de datos:** solo lectura, solo `madenat_test`, consultas `SELECT` acotadas al caso. Sin dumps.

