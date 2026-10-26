# G1 — Guardas de eliminación de guía: diseño y matriz antes/después

## 1. Investigación (4.1)
- **Único `unlink()` sobre la guía:** `madenat_lumber_core/models/madenat_guia_processing.py` (core). El resto de
  extensiones (`_inherit='madenat.guia.processing'` en 9 archivos) **no** lo sobrescriben.
- **Llamadores:** el asistente `madenat.lumber.intake.guide.lifecycle` (`_run_delete_definitive`,
  `_run_controlled_purge`) y las vías directas (botón de lista/form, RPC, tests).
- **FK entrantes (22):** RESTRICT (`sv_operation`, `sv_imputation`, `processor_return_link`,
  `stock_lot.volume_source_guia_id`), CASCADE (líneas/rels/wizards/checklist/volume_detail), SET NULL
  (lotes `guia_processing_id`, `stock_picking`, `lumber_reception.origin`, `madenat_audit_log`, supplier_link).
- **Bypass test-only:** `_sv_test_cleanup_allowed` (token + `--test-enable` real) — **inalterado** (inerte en
  producción).

## 2. Diseño (4.2) — guarda ÚNICA en `unlink()`
1. **Bypass test-only** (paso 0, sin cambios).
2. **Estado**: solo `draft`/`cancelled` (sin cambios).
3. **Pre-chequeo `_guia_deletion_blockers()` (NUEVO, D-G1):** bloquea si algún lote de la guía tiene
   `stock.quant`, `stock.move.line` o líneas de coste; si hay lotes SV de volumen (`volume_source_guia_id`),
   albaranes vinculados, operaciones SV, imputaciones SV o relaciones envío–retorno. **Mensaje de NEGOCIO**
   (D-G2) con nombre + motivos + **alternativas** (anular/corregir/revertir).
4. **Limpieza de moves huérfanos** (paso existente, exige `stock_manager`).
5. **Motivo + bitácora (NUEVO, D-G3):** `madenat.audit.log` (`guia_delete_permanent`) con usuario/motivo/estado
   **antes** de borrar; contexto `madenat_guia_delete_reason`. La vía directa usa un motivo por defecto
   documentado («sin motivo declarado») para **no romper** la compatibilidad (ver §Limitaciones).
6. **Borrado controlado de lotes vacíos (NUEVO):** los lotes vinculados **sin** dependencias se eliminan con la
   guía ⇒ **sin huérfanos** (comportamiento elegido).
7. **`super().unlink()`** (ACL + FK ondelete de la base).

**Asistente:** `_run_delete_definitive`/`_run_controlled_purge` pasan
`with_context(madenat_guia_delete_logged=True, madenat_guia_delete_reason=…)` ⇒ comparten la guarda y **no
duplican** la bitácora.

## 3. Matriz de escenarios antes/después
| Esc | Antes (pre-guarda, Fase 2 dinámica) | Después (G1) | Prueba |
|---|---|---|---|
| **a** duplicada vacía | éxito | éxito + **1 auditoría** | `test_a_…` |
| **b** con líneas | éxito (CASCADE) | éxito (CASCADE) | `test_b_…` |
| **c** lotes vacíos | éxito, **lote huérfano** (SET NULL) | éxito, **lote eliminado** (sin huérfano) | `test_c_…` |
| **d** lotes con existencias | **ÉXITO ⚠️ (borraba con stock)** | **UserError de negocio** | `test_d_…` |
| **e** envío/imputación | SET NULL / FK técnica | **UserError de negocio** | `test_e_…`, `test_e2_…` |
| **f** costos/documentos | no evaluado | blocker por `cost_line_ids` | (cobertura indirecta; ver §Limitaciones) |
| **g** historial SV (volumen) | **ForeignKeyViolation técnica** | **UserError de negocio** | `test_g_…` |
| **h** estado ≠ draft/cancelled | UserError negocio | UserError negocio (igual) | `test_h_…` |
| **i** usuario sin permiso | AccessError | **AccessError** (ACL) | `test_i_…` |
| **j** auditoría | sin auditoría | **1 exacta**; fallida = **0** | `test_j_…` |
| **k** concurrencia | n/a | exactamente **1 gana** (2 conexiones reales) | `test_k_…` |
| **l** efectos físicos | sin movimientos | sin movimientos | `test_l_…` |
| **m** directa ≡ asistente | mensajes distintos | **misma guarda** | `test_m_…` |

## 4. Limitaciones declaradas
- **`f` (costos/documentos):** se bloquea vía `stock.lot.cost_line_ids`; **no** se construyó una fixture de
  `lumber.shipment.cost.line` (modelo de `vendor_payment`, creación compleja) ⇒ cobertura **indirecta**; se
  propone una prueba dedicada si se autoriza.
- **Motivo en la vía directa:** D-G3 pide «motivo obligatorio»; el test **existente**
  `test_guia_delete_acl.test_07_authorized_direct_unlink_scope` espera que la vía directa borre **sin** contexto
  ⇒ se conserva un **motivo por defecto** («sin motivo declarado») para no romperlo. Endurecerlo (motivo
  estrictamente obligatorio) implica actualizar ese test ⇒ **decisión de Mauricio**.
- **`stock_manager` enmascara el ACL (H-SEC-1 i):** la guarda `_cleanup_orphan_moves_guia` se evalúa **antes**
  del ACL; un usuario sin jefatura *y* sin stock-manager recibe el mensaje de «Inventario/Administrador».
