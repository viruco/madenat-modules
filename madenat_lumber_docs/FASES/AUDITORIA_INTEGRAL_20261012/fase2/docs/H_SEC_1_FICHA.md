# H-SEC-1 / D15 — Eliminación de `madenat.guia.processing` por Jefatura (ficha)

**Estado:** permiso **APROBADO como política** (Mauricio, 2026-10-12); **guardas PENDIENTES de decisión.**
**Regla:** este expediente **NO** implementa nada; analiza y propone. **No** se modificó ACL/vistas/código.

## PARTE A — análisis estático

### A.1 Cambio de ACL (archivo, línea, permiso, grupo, modelo)
- **Archivo:** `madenat_lumber_core/security/ir.model.access.csv`, **línea 28**.
- **Registro:** `access_madenat_guia_processing_manager`.
- **Grupo:** `madenat_lumber_core.group_madenat_jefatura_operaciones`. **Modelo:** `madenat.guia.processing`.
- **Permiso añadido:** `unlink` **0 → 1** (lectura/escritura/creación ya eran 1). Diff:
  `…,group_madenat_jefatura_operaciones,1,1,1,0` → `…,1,1,1,1`.
- **Naturaleza:** **modifica una línea previa** (no es fila nueva).

### A.2 Intervención asociada
Bloque **`intake/guias-dup-delete`** (Fase 2 de intake): evidencia en `FIX_DELETE_INTAKE_20261007_145130/`,
`AUDIT_DELETE_INTAKE_20261007_130559/`, `INCIDENTE_GUIA_15183_20261007/`, `tests/test_guia_delete_acl.py`,
`tests/test_guide_lifecycle*.py`, y el asistente `madenat.lumber.intake.guide.lifecycle`.

### A.3 Código del WIP que depende del permiso
`madenat_lumber_intake/models/intake_guide_lifecycle_wizard.py` (`action_run` → `_run_delete_definitive` /
`_run_controlled_purge`), sus vistas (`intake_guide_lifecycle_wizard_views.xml`,
`intake_console_views.xml`), y `madenat_guia_processing.unlink()` (core). **Pre-chequeo de UX:**
`_delete_access_blocker()` exige (1) `has_access('unlink')` y (2) `stock.group_stock_manager`.

### A.4 Qué ocurre al eliminar hoy (`unlink` de la guía)
`madenat_guia_processing.unlink()` (core, línea 6166): (0) bypass test-only por marcador; (1) **estado**
solo `draft`/`cancelled` (si no → `UserError` de negocio); (2) `_cleanup_orphan_moves_guia()` exige
`stock.group_stock_manager` (si no → `UserError`) y borra `stock.move` huérfanos (origin = guía, sin picking);
(3) `super().unlink()` → aplica las FK.

**FK entrantes a `madenat.guia.processing` (22, del esquema real):**
- **RESTRICT (`r`) — bloquean:** `stock_lot.volume_source_guia_id`, `madenat_sv_operation.guia_processing_id`,
  `madenat_sv_imputation.guia_processing_id`, `madenat_processor_return_link.guia_processing_id`.
- **CASCADE (`c`) — se borran con la guía:** `madenat_guia_processing_line.processing_id`,
  `..._stock_lot_rel`, `..._source_lot_rel`, `..._source_lot_line`, `validation_checklist_item.guia_id`,
  `madenat_lumber_volume_detail_line.guia_id`, `madenat_lumber_intake_guide_lifecycle.guia_processing_id`,
  y 4 wizards (`sv_imputation_wizard`, `reopen`, `historical_reverse`, `documental_correction`).
- **SET NULL (`n`) — sobreviven perdiendo el vínculo:** `madenat_audit_log.guia_processing_id`,
  `stock_lot.guia_processing_id`, `stock_picking.guia_processing_id`, `lumber_reception.origin_processing_id`,
  `lumber_cost_distribution(.wizard).reception_id`, `madenat_lumber_intake_supplier_link.guia_id`.

### A.5 Escenarios (definición)
(a) duplicada sin dependientes · (b) con líneas, sin lotes · (c) con lotes sin existencias · (d) con lotes con
`stock.quant`/movimientos · (e) con imputaciones/rebajas/links/envíos · (f) con costos/documentos contables ·
(g) con historial SV.

## PARTE B — comprobación dinámica (fixtures, rollback, usuarios reales sin sudo)

Script: `code/fase2_hsec1_dynamic.py`; log: `logs/hsec1_partB.log`. **Contadores previos y posteriores
idénticos** (`13/76/166`) ⇒ **0 residuo** (rollback verificado).

| Esc | Fixture | Resultado (usuario Jefatura + stock-manager) | Mensaje / naturaleza |
|---|---|---|---|
| **a** | guía desnuda (draft) | **ÉXITO** (eliminada) | — |
| **b** | guía + línea | **ÉXITO** (línea CASCADE) | — |
| **c** | guía + lote (`guia_processing_id`), sin quant | **ÉXITO** (lote sobrevive, vínculo NULL) | — |
| **d** | guía + lote (`guia_processing_id`) + **quant** | **ÉXITO** ⚠️ | el lote **sobrevive con existencias** y pierde el vínculo a la guía (**SET NULL**) |
| **e** | guía + lote volumen (`volume_source_guia_id`) | **ForeignKeyViolation** | **error técnico** (`stock_lot_volume_source_guia_id_fkey`), sin traducción a negocio |
| **f** | como (e) + `madenat.sv.operation` | **ForeignKeyViolation** | ídem (bloquea por la misma FK) |
| **g** | guía desnuda (cancelled) | **ÉXITO** | — |
| **h** | guía `verified` (ni draft ni cancelled) | **UserError (negocio)** | «No puede eliminar la guía … estado 'verified'» ✅ |
| **i** | guía desnuda, usuario **sin jefatura ni stock** | **UserError (negocio)** | «…eliminar movimientos de stock huérfanos. Se requiere el grupo Inventario/Administrador» (la guarda de stock-manager **enmascara** el ACL) |
| **i2** | guía desnuda, **stock-manager y SIN jefatura** | **UserError (negocio)** | «No puede eliminar registros 'Recepción de Guías Procesadas'… permitida para los siguientes grupos…» ⇒ **el ACL rechaza correctamente** ✅ |
| **j** | guía + lote + `stock.move` huérfano (origin=guía, sin picking) | **ÉXITO** | la guarda `_cleanup_orphan_moves_guia` borra el move huérfano |

**Conclusión B:** el permiso `unlink` de jefatura **es efectivo y delimitado** (i2 sin él → rechazo de negocio);
las guardas de **estado** y de **stock-manager** funcionan; **pero** (1) la guarda de stock-manager se evalúa
**antes** del ACL y da un mensaje engañoso, (2) un `unlink()` **directo** (vía RPC, ya permitido) **no** pasa por
el asistente ⇒ **puede borrar una guía con lotes con existencias** (escenario **d**) y (3) con lote de volumen
(escenarios **e/f**) produce un **error técnico de FK** sin mensaje de negocio.

## PARTE C — trazabilidad
- **Vía asistente:** `_run_delete_definitive`/`_run_controlled_purge` escriben `madenat.audit.log`
  (`guia_delete_permanent` / `guia_purged`) **con snapshot firmado**.
- **Vía `unlink()` directa (RPC):** **NO** escribe ninguna entrada de bitácora (la sobreescritura de
  `madenat_guia_processing.unlink` no audita) ⇒ **brecha de trazabilidad**.
- `madenat_audit_log.guia_processing_id` es **SET NULL** ⇒ aunque el asistente registre, el vínculo al documento
  borrado se pierde (queda el snapshot en el propio registro).
- **Relación con H-SEC-5:** como la bitácora es **escribible/borrable** por ACL (ver `H_SEC_5_analisis.md`), la
  eliminación de guías **no garantiza** reconstruir «qué se eliminó y quién lo hizo».

## PARTE D — ficha de guardas (propuesta; **REQUIERE_DECISIÓN**; NO implementada)

| Esc | Resultado actual | Riesgo | Guarda sugerida (REQUIERE_DECISIÓN) |
|---|---|---|---|
| a/g | OK | — | mantener (estado draft/cancelled) |
| b | OK (CASCADE) | bajo (líneas se borran) | confirmar explícita |
| c | OK | medio (lote sobrevive sin vínculo) | confirmación + nota de trazabilidad |
| **d** | **OK (¡borra con existencias!)** | **ALTO** | **bloquear** si algún lote vinculado tiene `stock.quant` (incluye cantidad 0) o `stock.move` |
| **e/f** | **FK técnica** | medio (UX) | **traducir** la `ForeignKeyViolation` a mensaje de negocio + pre-chequeo |
| i | negocio (engañoso) | bajo | reordenar: ACL primero o mensaje conjunto |
| directo | sin auditoría | **ALTO** | registrar en bitácora la eliminación directa (o exigir el asistente) |

**Propuesta mínima (sin implementar):** (1) permitir borrar **solo** guías sin lotes con existencias ni
documentos dependientes; (2) **mensajes de negocio** en lugar de errores de FK; (3) **exigir motivo** y
**registrar la eliminación en la bitácora** también en la vía directa; (4) ofrecer alternativas (anular,
corregir, revertir) cuando existan dependientes.
**Impacto:** pruebas existentes (`test_guia_delete_acl`, `test_guide_lifecycle*`) y limpiezas de test
(dependen del permiso/raw-SQL). **Pruebas necesarias:** por escenario a–g con resultado esperado (negocio),
y una que asegure **auditoría** de la eliminación directa.

> **ESTADO:** permiso **aprobado como política**; **guardas pendientes de decisión de Mauricio.** Hasta
> aprobarlas, el cambio de ACL **NO** debe ir al TEST remoto sin documentar el riesgo residual.
