# Changelog

Todos los cambios notables de este módulo se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [18.0.1.42.0] - 2026-10-29

### Changed
- **Matriz de permisos operativos y auditoría en modelos navieros (DISC-LOG-04, commit c621d1e)**:
  - **Cambio de comportamiento**: Operaciones (`madenat_lumber_core.group_madenat_operaciones`) cuenta con permisos de lectura en buques y creación/edición en viajes y reservas, pero **pierde el permiso de borrado (`unlink=0`)** en viajes (`shipping.voyage`) y reservas (`shipping.booking`). El borrado queda reservado a Jefatura (`group_madenat_jefatura`), Responsable de Inventario (`stock.group_stock_manager`) y Administrador de Envíos.
  - Auditoría (`madenat_lumber_core.group_madenat_auditoria`): solo lectura estricta (`1,0,0,0`) sobre buques, viajes y reservas navieras.
  - Se añade suite de pruebas `tests/test_shipping_access.py` (tag: `logistics_shipping_access`) validando Operaciones, Jefatura y Auditoría.
- **Búsqueda robusta de etiquetas en Asistente de Consolidación (DISC-OP-01, DISC-LOG-01, commit bd918ee)**:
  - Sustitución de `supplier_label` por `external_labels` en `lumber.consolidation.import.wizard`.
  - Estrategia de búsqueda en dos pasos: búsqueda exacta y fallback mediante `ilike` + token parsing case-insensitive por comas (`strip()`), evitando falsos positivos por subcadenas.
  - Control de ambigüedad: ante múltiples lotes coincidentes, la fila se envía a pendientes (`lumber.consolidation.import.pending`) sin enlazar.
  - Pruebas automatizadas en `tests/test_consolidation_import_wizard.py` (tag: `consolidation_external_labels`).

### Removed
- **Menú duplicado de conciliación de retornos (DISC-LOG-10, commit d1897a3)**:
  - Eliminación de la entrada redundante de menú `menu_processor_return_reconciliation` en `views/madenat_processor_return_link_views.xml:148-154`, idéntica a la definida en l.141-147.
- **Acción redundante de consolidación (DISC-LOG-12, commit 0910355)**:
  - Eliminación de la definición básica de `action_lumber_container_consolidation` en `views/lumber_actions.xml`, preservando la definición kanban completa en `views/lumber_container_views.xml:100` que coincide con el registro activo en base de datos.
- **Secuencia duplicada de embarques (DISC-LOG-11, commit 51c69c6)**:
  - Eliminación de la definición redundante de `seq_lumber_export_shipment` en `views/lumber_actions.xml`, preservando la definición en `data/sequences.xml` bajo `<data noupdate="1">` con prefijo canónico `EMB-` y `padding=5`, sin alterar contadores ni generar colisiones en base de datos.
- **Método obsoleto en lumber.container (DISC-LOG-03, commit 2d3ba2d)**:
  - Eliminación de la implementación errónea y redundante de `action_remove_lot_granular` en `lumber.container`. La acción canónica se mantiene intacta en `stock.lot` (`lumber_export_shipment.py`).

## [18.0.1.41.1] - 2026-10-28
- Actualizada documentación en README.md reflejando reactivación del asistente de consolidación de tarjas bajo AD-133.

## [18.0.1.41.0] - 2026-10-21

### Added
- **Bloque 7 (Fase 2 / AD-133) — Paridad de Tarja, Importador de Consolidación y Merma Dimensional R2**:
  - **7.1 Paridad de Tarja Exportador**: Generación XLSX de tarja por contenedor con doble bloque simétrico (cols 1-13 izq exportación, cols 15-27 der compra), totales por suma de filas con `round(..., 3)` y paridad con tarjas de referencia FA543R y FA610R.
  - **7.2 Asistente de Importación de Consolidación**: Wizard `lumber.consolidation.import.wizard` para lectura de doble bloque y modelo `lumber.consolidation.import.pending` para filas sin etiqueta, con informe de diferencias e invarianza de BD.
  - **7.3 Merma Dimensional y Rebaja R2**: Campo `total_merma_dimensional_m3` en contenedor y embarque, extinción total del quant nominal en `_rebajar_container()` registrando `rebaja_merma_m3`, y reversa limpia en `action_reverse_rebaja()`. Prueba dorada packing 40030 (compra 54,518 m³, exportación 44,713 m³, merma 9,805 m³).

## [18.0.1.39.0] - 2026-10-17

### Fixed
- **Robustez de disponibilidad en asistente SV**: cálculo de `no_availability_note` y `action_open_no_availability_docs()` alineado para considerar todas las etiquetas no asignables del asistente con independencia de su selección activa.

## [18.0.1.38.0] - 2026-10-17

### Added
- **WP-F (FASE 12 / AD-112) — P1–P5: Control y trazabilidad de disponibilidad en imputación documental SV**:
  - **P1**: Campo computado `asignable` en `madenat.sv.imputation.wizard.line` (`disponibilidad_estado == 'available'`). Toggle `selected` con `readonly="not asignable"` para impedir selección de etiquetas sin saldo documental.
  - **P2**: `action_select_all()` restringe la selección únicamente a etiquetas con saldo disponible (`asignable=True`). Muestra notificación de advertencia cliente detallando cuántas etiquetas fueron omitidas.
  - **P3**: Pestaña «Sin disponibilidad» (`unavailable_material`) en el formulario del asistente, visible si `not_assignable_line_count > 0`, con lista de solo lectura y botón «Ver documentos» (`action_open_consuming_documents`).
  - **P4**: Coherencia en resumen del asistente: campo `selectable_line_count` y desglose de etiquetas sin saldo en `assigned_summary`.
  - **P5**: Error nominativo detallado al validar techo duro o payload en `madenat.sv.imputation`: helper `_i2_lot_consuming_docs_detail(lot)` que lista los documentos y estados que causan el bloqueo.
  - Pruebas automatizadas en `tests/test_sv_imputation_availability_p1_p5.py`.

## [18.0.1.37.0] - 2026-10-17

### Changed
- **WP-B rótulos (FASE 12 / AD-111) — Unificación de rótulos de volumen en vistas de Embarque y Contenedor**:
  - Homologación canónica de rótulos de volumen:
    - «Vol. Compra (m³)» para el volumen de compra por etiqueta (`volume_purchase_m3`, `total_volume_purchase_m3`, `total_nominal_volume_m3`, `physical_volume_m3`).
    - «Vol. Export (m³)» para el volumen de exportación (`vol_shipment_m3`, `total_vol_shipment_m3`, `volume_m3`, `total_volume_m3`, `export_volume_m3`).
    - «Vol. Documental (m³)» claramente distinguido en las vistas de imputaciones documentales SV (`sv_assignment_nominal_m3`, `sv_ret_nominal_m3`).
  - Sustitución de `volumen_m3` ("Vol. Físico") en la grilla de lotes de contenedor y asistente por `volume_purchase_m3` («Vol. Compra (m³)») para reflejar el volumen de compra de la etiqueta.
  - Eliminación de etiquetas inconsistentes y ambiguas («Vol. Físico», «Vol. Emb.», «Vol. Nominal (m³)», «m³ Embarque», «Volumen Exportación (facturable)»).
  - Pruebas automatizadas en `tests/test_volume_labels_unification.py`.

## [18.0.1.36.0] - 2026-10-15

### Fixed
- **A-1/B-1 — El estado y las marcas de transición de la imputación SV sólo cambian por las acciones oficiales**
  (FASE 11; hallazgo ALTA `A-1` de `AUDITORIA_CICLO_VIDA_IMPUTACIONES_20261015`). La vía pública `write()` sólo
  protegía los estados terminales: con el documento en `draft`/`pending` aceptaba **cualquier** destino
  (`applied`, `cancelled`, `reversed`) ⇒ se podía fabricar un documento «aplicado» **sin firma, sin snapshot, sin
  ejecutor y sin bitácora** (es la huella exacta de `IMP04823`) saltándose techo duro, locks y validaciones.
  - `write()` (ORM/RPC) **rechaza** `state` y las MARCAS de transición (`I2_TRANSITION_MARK_FIELDS`: `audit_hash`,
    `snapshot_json`, ejecutor/fechas, motivos y metadata de anulación/reversa/reapertura y
    `reversed_imputation_id`) con un `UserError` de negocio; **también** con `sudo()` y `with_context(...)`
    (ninguna bandera de contexto es autorización).
  - `create()` **rechaza** nacer en un estado distinto de `draft` y cualquier marca fabricada.
  - Las acciones oficiales (`action_pending`, `action_back_to_draft`, `action_apply`, `action_cancel`,
    `action_reverse`, `action_reopen_to_draft` y el sello recíproco de la cadena) escriben por la **vía privada**
    `_i2_write_protected_state` (`super().write`), no invocable por RPC y sin token ni contexto.
  - El MOTIVO se captura en el campo libre `reason` (o como parámetro de la acción) y la acción lo **congela** en
    su campo de marca; en el formulario `reversal_reason`/`cancellation_reason`/`reopen_reason` pasan a **sólo
    lectura** y `reason` es la única entrada del motivo.
- **M-2 — La reversa toma los locks de capacidad y revalida el estado.** `action_reverse` adquiere los mismos
  advisory locks que `action_apply` (etiquetas ns 3 + SV ns 2, en orden determinista) y **revalida el estado tras
  el bloqueo**: dos sesiones no pueden reversar a la vez ni dejar marcas de «último gana» (usuario/fecha/firma
  sobrescritos). La otra conexión recibe un conflicto controlado, sin cambios ni bitácora.
- **M-4 — Cadena de corrección.** Al crear una imputación nueva cuya clave base está ocupada por una imputación
  **terminal** (reversada/anulada) del mismo alcance (misma guía/procesador/firma), el asistente fija
  `origin_imputation_id`; al aplicarse la nueva se sella el recíproco `reversed_imputation_id`. Los documentos
  existentes **no** se modifican y no hay migración de claves.
- **B-2 — Líneas y repartos inmutables fuera de preparación.** `create`/`write`/`unlink` de
  `madenat.sv.imputation.line` y `madenat.sv.imputation.sv.line` se bloquean también en `reversed` y `cancelled`
  (antes sólo en `applied`): no se puede alterar a posteriori lo que se aplicó o anuló. «Volver a borrador»
  devuelve el documento a preparación con su contenido íntegro.
- **B-3 — La anulación exige motivo.** `action_cancel` exige motivo no vacío (campo `reason` o parámetro), lo
  registra en `cancellation_reason` (metadata) y lo incorpora al evento firmado `imputation_cancel`. Sin cambio
  de grupos (se mantiene el ACL de escritura).

### Notes
- Nuevo `tests/test_sv_imputation_lifecycle_integrity.py` (**A-1/B-1/M-2/M-4/B-2/B-3**, 17 pruebas) y
  `TestSvImputationReverseLocks` (lock externo real sobre el SV/etiqueta, limpieza por IDs).
- Regresión del módulo `logistics` completa comparada **por nombre** con el baseline vigente: **4 failed /
  0 error** (mismo subconjunto; **0 fallas nuevas**). `IMP04823`/`IMP02220` intactos (estado, valores y hashes).
- **Datos heredados sin cambios:** `IMP02220` (aplicada sin reparto positivo) e `IMP04823` (anulada sin rastro)
  quedan como están; los eventos `TX10` no se tocan. **M-3** (régimen de acceso/`compute_sudo` de `stock.lot`)
  sólo se documenta. Expediente `FASE11_INTEGRIDAD_CICLO_IMPUTACIONES_20261015/`.

## [18.0.1.32.0] - 2026-10-15

### Fixed
- **S1 — Clave documental con las ETIQUETAS SELECCIONADAS y reglas de estado terminal (defecto F1, causa raíz).**
  `_i2_signature()` sólo incluía los **repartos SV**, no las etiquetas seleccionadas, y `_i2_get_or_create()`
  buscaba por `documentary_key` **sin filtrar estado** (la clave es UNIQUE). Cualquier preparación de la guía 1198
  **sin reparto** colisionaba con el documento **APLICADO `IMP02220`** ⇒
  `UserError: … ya no admite preparación (estado applied)`: las etiquetas nunca se registraban.
  - `_i2_signature()` incluye ahora las **etiquetas incluidas** (`_i2_included_lines()` ordenadas por
    `processed_lot_id`) con su volumen nominal —`L<id>:<nominal>`— **además** de los repartos SV y de forma
    determinista.
  - `_i2_get_or_create()` devuelve **sólo** documentos en estado de trabajo (`draft`/`pending`):
    - `applied` ⇒ mensaje claro («Esta rebaja ya se aplicó con esta misma selección…») y **sin duplicar**;
    - `reversed`/`cancelled` ⇒ documento **NUEVO** con clave **distinta y trazable** (discriminador determinista
      con el id del documento que ocupa la clave), sin alterar el documento terminal.
  - **Retrocompatibilidad total:** la receta **base** de la clave
    (`I2|guia|processor|signature` ⇒ `IMP-<guia>-<sha256[:16]>`) **no cambia**; `discriminator=''` produce el
    resultado histórico byte a byte ⇒ las claves y firmas de los documentos ya aplicados (p. ej. `IMP02220`,
    `IMP-1198-E95825AAF94E58AD`) siguen **idénticas y verificables**. **No hay migración de datos.**
  - Una sola implementación central: la receta de la clave y las reglas de reutilización viven en el modelo; el
    asistente sólo aporta la firma.

### Notes
- Nuevo `tests/test_sv_rebaja_documentary_key.py` (**DK-01..08**, T1/T4/T5 y E7 del diagnóstico): 9/9 en verde;
  incluye el perfil `IMP04823` (documento anulado con la clave base) y la clave histórica con `signature=''`.
- Regresión del módulo `logistics` completa: **4 failed de 528** (el MISMO subconjunto de 10 fallas del baseline;
  0 fallas nuevas por nombre). `IMP04823`/`IMP02220` intactos (hashes de fila/líneas/repartos idénticos).
  Expediente `FASE10_REBAJA_SV_ETIQUETAS_20261015/`.

## [18.0.1.31.0] - 2026-10-15

### Fixed
- **S3 — No persistir/borrar en silencio un documento de rebaja VACÍO (defecto F3).** «Guardar borrador»
  (`_i2_build_imputation`) **no** exigía ninguna etiqueta incluida: sólo `action_apply` lo comprobaba. Guardar
  sin seleccionar (o desmarcar todo lo ya registrado) dejaba o **borraba líneas en silencio**, produciendo el
  documento vacío vinculado al SV que explica `IMP04823`.
  - `_i2_build_imputation` comprueba ahora `_i2_included_lines()` **antes** de crear o actualizar el documento y
    lanza un `UserError` de negocio en español («No se puede guardar un documento de rebaja sin etiquetas.
    Selecciona al menos una etiqueta…») cuando no hay ninguna incluida.
  - Al rechazar **antes** de escribir, un guardado inválido no crea documento nuevo (ni vacío) y **no pierde**
    las líneas ya registradas. Los flujos legítimos (anular, «Volver a borrador», reabrir) no pasan por este
    camino y quedan intactos; el caso SAVE-05 (destino SV previsto con cantidad 0) sigue permitido; el techo duro
    y las validaciones de `action_apply` no cambian.

### Notes
- Nuevo `tests/test_sv_rebaja_empty_guard.py` (**SG-01..06**, T6 del diagnóstico): 6/6 en verde. Las pruebas
  comprueban los efectos reales (creación/borrado) con un `try/except` propio, **sin** el savepoint que Odoo
  interpone en `assertRaises` y que enmascararía esos efectos.
- Regresión del módulo `logistics` completa: **4 failed de 519** (el MISMO subconjunto de 10 fallas del baseline;
  0 fallas nuevas por nombre). Sin cambios en datos, firmas ni documentos históricos. Sin migración.
  Expediente `FASE10_REBAJA_SV_ETIQUETAS_20261015/`.

## [18.0.1.30.0] - 2026-10-15

### Fixed
- **S2 — «Trabajo en preparación»: filtro EFECTIVO por estado (defecto F2).** El campo
  `stock.lot.sv_assignment_work_imputation_ids` declaraba
  `domain="[('state','in',('draft','pending'))]"`, pero el ORM **no aplica** el `domain` de un
  `One2many` al leer: la sección «Trabajo en preparación (no aplicado)» de la ficha del SV
  **listaba y contaba** documentos ANULADOS/APLICADOS/REVERSADOS (caso `SV00000000841`: la
  anulada `IMP04823`) y ofrecía «Continuar», que terminaba en `UserError`.
  - El campo pasa a ser un `Many2many` **calculado y NO almacenado** (`store=False`; relación
    explícita `stock_lot_madenat_sv_imputation_work_rel`, sin tabla) que resuelve la lista con
    una **búsqueda explícita en el servidor** (`work_sv_lot_id` + `state in ('draft','pending')`),
    en línea con `sv_assignment_imputation_ids`. Conserva nombre y semántica; sin `sudo`
    (respeta compañía y reglas de registro).
  - `sv_assignment_work_count` y `sv_assignment_work_m3` se calculan con la MISMA búsqueda
    (antes `len(lot.sv_assignment_work_imputation_ids)`), de modo que el contador excluye los
    estados terminales.
  - `action_continue_preparation`: sobre un estado terminal ya **no** lanza un error técnico;
    devuelve una **notificación operativa** (`display_notification`): para un anulado, la ruta
    «Volver a borrador»; para un aplicado/reversado, la ruta de reversa. El botón «Continuar»
    sigue disponible sólo para `draft`/`pending`.

### Changed
- Se actualizan las aserciones previas que esperaban `UserError` al continuar un documento
  aplicado/anulado (`test_sv_rebaja_persistencia`, SAVE-13 y FLOW-02), coherentes con la ruta
  operativa aprobada.

### Notes
- Cero cambios en datos, en la firma/clave documental o en los documentos existentes
  (`IMP04823`/`IMP02220` intactos). Sin migración. Nuevo `tests/test_sv_rebaja_work_filter.py`
  (**WF-01..07**, T2/T3 del diagnóstico): 7/7 en verde.
- Regresión del módulo `logistics` completa: **4 failed de 513** (el MISMO subconjunto de 10
  fallas del baseline; 0 fallas nuevas por nombre). Expediente
  `FASE10_REBAJA_SV_ETIQUETAS_20261015/`.

## [18.0.1.29.0] - 2026-10-15

### Fixed
- **Instalación desde cero de `madenat_lumber_logistics` (defecto latente introducido en `ded5e89`).** En
  `views/madenat_sv_imputation_views.xml` el `<record id="menu_madenat_sv_imputation" model="ir.ui.menu">`
  quedo **sin `name`** al retirarse su `<menuitem>` (unificación de acceso, 2026-10-10): en una base existente
  el `-u` no falla (el menu ya esta creado y no se reescribe su nombre), pero al **instalar desde cero** el
  registro se crea sin nombre ⇒ `NotNullViolation: null value in column "name" of relation "ir_ui_menu"` ⇒
  `Failed to load registry`. Se **restituye el `<menuitem>`** (mismos `name`/`parent`/`action`/`sequence`)
  **antes** del `<record>`, que es exactamente el mecanismo documentado en el expediente
  `UNIFY_SV_REBAJA_MENU_20261010` («`record` posterior al `menuitem` ⇒ no reaparece al reaplicar `-u`;
  reversible»). El menu sigue **inactivo** y la recuperacion de navegacion (`active=True` + `-u`) vuelve a ser
  posible tambien en un alta limpia. Sin cambios de id, nombre, accion ni visibilidad.

### Notes
- Evidencia: FASE 8 (A-Paso 1: `-i` de los 4 modulos con **exit 0**; `madenat_lumber_logistics` carga en
  4.70 s) y FASE 7 (`NotNullViolation` detectado). Barrido de la misma clase en todos los modulos instalables:
  **0 casos restantes**.
- Sin cambios en modelos, datos, ACL ni `ir.rule`; no requiere scripts de migracion.

## [18.0.1.28.0] - 2026-10-15

### Added
- **Rebaja por nave — asistente `lumber.shipment.rebaja.wizard` (cierre de D18).** Se incorpora al historial el
  asistente documentado en `CANON/18` **§7.3** («Rebajar por nave (masiva)»: selección de nave/viaje, lista de
  contenedores consolidados pendientes, idempotencia por (contenedor, lote), resumen de volúmenes
  EXPORT/NOMINAL y saldos SV) y **§14.1** («rebaja masiva con **savepoint por contenedor** e informe de
  éxitos/fallos», y «rechazo en servidor» con `_rebaja_require_group`). Incluye el submodelo
  `lumber.shipment.rebaja.wizard.line`, su vista y las pruebas de contenedor/rolleo/zarpe (`§14.5`).

### Fixed
- **`action_reverse()` exige motivo de reversa (AUD-ETQ-02 / CANON/19 §19).** Se adaptan las pruebas
  `test_service_return_imputation_guard` (casos 06 y 09), que reversaban sin motivo, al guard ya entregado en
  la versión 18.0.1.27.0.

### Notes
- **Motivo del commit.** El asistente quedó **fuera del historial** en la FASE 5 (triaje `desconocido` = D18).
  Al commitearse su ACL (`security/ir.model.access.csv`, commit `ded5e89`) sin el modelo, el módulo
  **no cargaba**: FASE 6/V1 reprodujo `Failed to load registry` con
  `No matching record found for external id 'model_lumber_shipment_rebaja_wizard_line'`.
- **Evidencia:** `CANON/18` §7.3/§14.1/§14.5; expediente `AUDIT_B01_20261004` (que ya analizaba
  `_classify` en este estado del árbol); re-verificación de instalación desde cero de la FASE 7.
- El contenido de los 4 archivos incorporados es **idéntico** al del WIP previo (verificado por SHA256).
- Sin cambios en modelos persistentes, datos, ACL ni `ir.rule`; no requiere scripts de migración.

## [18.0.1.27.0] - 2026-10-12

### Fixed
- **H6 (FASE 4) — fixtures `test_sv_rebaja_*` sin residuo de socios `*_oper`.** `res.users.create` genera un
  `res.partner` homónimo que **no** se elimina al borrar el usuario; las tres suites con limpieza de clase
  (`test_sv_rebaja_reset_concurrency`, `test_sv_rebaja_reset_lot_capacity`, `test_sv_rebaja_save_lock_tx`)
  capturan ahora el `partner_id` de sus usuarios de prueba y lo eliminan **por IDs explícitos** en
  `_cleanup_class` (misma técnica que T1). Verificado con dos ejecuciones consecutivas: conteo idéntico.

## [18.0.1.26.0] - 2026-10-12

### Fixed
- **HOTFIX OWL — «Agregar una línea» en el documento de rebaja (`madenat.sv.imputation`).**
  Odoo 18 CE ya **no compila** el marcado heredado `div.oe_chatter`: el compilador de formularios registra el
  selector `chatter` sobre el elemento **`<chatter/>`** (ver `mail/static/src/chatter/web/form_compiler.js`).
  Al quedar sin efecto el chatter, los campos `message_follower_ids` y `message_ids` se renderizaban como
  **listas o2m editables por defecto** (`mail.followers` → Nombre del modelo del documento relacionado / ID del
  documento relacionado / Contacto relacionado; `mail.message` → Fecha / Asunto / Autor / Modelo de documento
  relacionado / ID del documento relacionado), mostrando el botón **«Agregar una línea»** y provocando un
  `OwlError` (`TypeError: Cannot read properties of undefined (reading 'includes')` en
  `Many2OneField.get urlRelation`) al interactuar con la columna `res_id` (`many2one_reference` sin modelo
  determinable).
- Cambio **mínimo** en vistas, **sin** tocar modelos, datos, permisos ni `mail`:
  - `views/madenat_sv_imputation_views.xml` (`madenat.sv.imputation.form`): `div.oe_chatter` → `<chatter/>`.
  - `views/madenat_processor_return_link_views.xml` (`madenat.processor.return.link.form`): `div.oe_chatter` → `<chatter/>`.

### Notes
- **Local** (`madenat_test`); **sin commit/push/despliegue**. Expediente de evidencia
  `HOTFIX_OWL_CHATTER_OE_20261012/`. **VIEW-01/04 (navegador) PENDIENTE** (sin navegador; guion en
  `docs/GUION_MANUAL_NAVEGADOR.md`).
- **Hallazgo (no corregido, fuera de alcance):** `madenat_vendor_payment/views/lumber_shipment_cost_views.xml`
  conserva un `div.oe_chatter` (módulo no instalado en `madenat_test`); mismo riesgo si se instala.

## [18.0.1.25.0] - 2026-10-12

### Added
- **V1 — Cobertura de la EDICIÓN DIRECTA del documento (matriz C1–C8).** El formulario persistente
  (`madenat.sv.imputation`) es editable en `draft`/`pending`; ahora envía `edit_version` con **`force_save="1"`** y
  `write()` la compara de forma **atómica** (`_i2_assert_edit_version`) ⇒ **rechaza** la edición basada en una
  versión obsoleta. Reutiliza `edit_version`; **no** usa `write_date`, ni flags de contexto, ni memoria global; **no**
  ofrece sobrescritura forzada. **No** retira permisos ni oculta campos (los campos siguen editables).
- **V3 — pruebas TX-01..13** (`tests/test_sv_rebaja_save_lock_tx.py`): transacción, `SerializationFailure`, orden de
  bloqueos, rollback y cursor utilizable.

### Tests
- `tests/test_sv_rebaja_save_lock_direct.py` (**C1–C8** + residual + positivo) y `tests/test_sv_rebaja_save_lock_tx.py`
  (**TX-01..13**). Suites conjuntas ⇒ **0 failed / 0 error**.

### Notes
- **Local** (`madenat_test`); **sin commit/push/despliegue**. **V2 (navegador) PENDIENTE** (sin navegador; guion en
  `CIERRE_SOBRESCRITURA_V123_20261012/docs/GUION_V2_CLIENTE.md`). **Límite residual:** escritura ORM/RPC **sin**
  `edit_version` no se compara.

## [18.0.1.24.0] - 2026-10-12

### Added
- **BLINDAJE DE BORRADORES (LOCK) — protección contra sobrescritura concurrente** (autorizado por Mauricio).
  - Campo `edit_version` (entero monotónico) en `madenat.sv.imputation`: versión lógica del documento. La
    cabecera (guía, procesador, motivo, `work_sv_lot_id`, `state`) y las **líneas/repartos**
    (`create`/`write`/`unlink`) la elevan; los campos de **trazabilidad/historia** y el **chatter** no
    (`I2_VERSION_NEUTRAL_FIELDS`), evitando conflictos falsos.
  - **Guard del documento** `_i2_assert_edit_version` (asistente): `pg_try_advisory_xact_lock` (namespace **1**) +
    comparación de `expected_edit_version`. Integrado con los locks de capacidad (namespaces 2/3) en orden
    determinista (1→2→3). `_i2_guarded_build` fuerza el **flush** dentro de la transacción y traduce un
    `SerializationFailure` al mismo mensaje operativo.
  - Campo `expected_edit_version` en el asistente, capturado al abrir/reconstruir y actualizado solo tras una
    operación exitosa.
  - Botón **«Recargar versión actual»** (`action_reload_current`) en el asistente: descarta los cambios no
    guardados (con confirmación) y reconstruye desde el documento vigente.
  - Si el asistente se abrió sin documento y otra sesión creó trabajo para la misma guía, **no** se adopta ni
    sobrescribe: se muestra la referencia del trabajo existente.

### Security
- Guardar y Aplicar rechazan de forma **controlada** una edición basada en una versión obsoleta (no sobrescriben
  ni fusionan). Sin «forzar guardado» ni «última escritura gana». Sin memoria global para autorizar escrituras.

### Tests
- Nuevo `tests/test_sv_rebaja_save_lock.py` (**LOCK-01..19**, FLOW-01..03, PHY-01) + reproducción del defecto
  original. LOCK-16 con transacciones independientes (barrera/eventos). ⇒ **0 failed / 0 error**.

### Notes
- **Local** (`madenat_test`); **sin commit/push/despliegue**. **Límite declarado:** la edición simultánea de dos
  formularios persistentes directos (sin asistente) sigue el comportamiento ORM estándar de Odoo (pendiente).

## [18.0.1.23.0] - 2026-10-12

### Security
- **P4 — vía privada de transición (AUD-ETQ-09).** Se **elimina** el registro global `_I2_REOPEN_TOKENS`
  (clave `(dbname, uid, id)`, que **no** distinguía transacción y dejaba una ventana de autorización
  reutilizable). La autorización de las transiciones protegidas se resuelve con el método **privado**
  `_i2_write_protected_state` (`_`-prefijado → **no** invocable por RPC; escribe con `super().write`). La
  guarda pública `write()` rechaza **toda** transición protegida: `cancelled → draft`, `applied → reversed` y
  cualquier cambio sobre `reversed`. `action_reopen_to_draft` y `action_reverse` usan la vía privada. **Sin
  estado compartido**: seguro entre transacciones, hilos y procesos.

### Changed
- **P3 — saldos almacenados canónicos (AUD-ETQ-10).** Los agregados `sv_assignment_nominal_m3`,
  `sv_assignment_applied_m3`, `sv_assignment_applied_count` y `sv_assignment_documental_balance_m3` pasan a
  `compute_sudo=True`: son **canónicos** (el MISMO valor para todos los usuarios, independiente de quién
  dispare el recompute) y **no** provocan `AccessError` a usuarios con acceso al lote pero sin acceso a las
  imputaciones. La proyección NO almacenada (`sv_assignment_imputation_ids`, `sv_assignment_processor_id`)
  mantiene `compute_sudo=False` (por usuario). El cómputo lee únicamente las relaciones propias del lote
  (company-scoped): **sin** exposición entre compañías.

### Added
- **P1 (AUD-ETQ-11).** `tests/test_sv_rebaja_reset_lot_capacity.py`: concurrencia sobre la capacidad de la
  **MISMA etiqueta retornada** (dos guías sobre un mismo lote de 10 m³; A/B cancelados de 6 m³), con
  transacciones independientes, los DOS órdenes y revalidación de capacidad tras el bloqueo. RESET-17 se
  conserva como caso adicional (saldo del SV).
- **P3.** `tests/test_sv_assignment_user_rights.py`: semántica canónico vs por-usuario, recompute bajo usuario
  restringido sin `AccessError` ni corrupción, proyección por usuario sin filtración y sin exposición entre
  compañías.
- **P4.** `tests/test_sv_rebaja_reset_token.py` (**TOK-01..09**): sin residual, documento intacto ante
  excepción, sin autorización cruzada, multi-registro/repetición, identidad del entorno, sin estado compartido.

### Tests
- `TestSvRebajaReset` actualizado (los agregados almacenados son `compute_sudo=True`). Suites dirigidas
  **0 failed / 0 error** (P1 3 + P2 1 + P3 2 + P4 7).

### Notes
- **Local** (`madenat_test`); **sin commit/push/despliegue**. Backups en `VERIF_CUATRO_PUNTOS_20261012/`.

## [18.0.1.22.0] - 2026-10-12

### Security
- **AUD-ETQ-07 — vía directa de `write` para `cancelled → draft` RECHAZADA.** La autorización de la
  reapertura deja de aceptar una **identidad suministrada por el cliente** (`reopened_by_id` +
  `reopen_reason` en la misma escritura). Se sustituye por un **token efímero de PROCESO** (set en memoria,
  clave `(dbname, uid, imputation_id)`) que `action_reopen_to_draft` añade justo antes de su `write` y que
  la guarda consume. Es **inmune a `with_context(...)`** (no es un flag de contexto) y `sudo()` directo
  tampoco elude la guarda. `applied → draft` y `reversed → draft` siguen **prohibidos**. El usuario y la
  fecha se derivan **siempre** del entorno de ejecución de la acción controlada.

### Fixed
- **AUD-ETQ-08 — advertencias de cálculo de `stock.lot` (`sv_assignment_*`).** Se **separan** los compute
  que compartían método: `_compute_sv_assignment` (agregados `store=True`) y `_compute_sv_assignment_live`
  (`sv_assignment_imputation_ids`, `sv_assignment_processor_id`, no almacenados). Se fija
  `compute_sudo=False` **explícito** en los campos almacenados (por defecto sería `True`), de modo que el
  compute **nunca** corre como superusuario, **respeta reglas de registro y compañía** y **no** expone
  documentos/datos de otra compañía. Elimina los avisos `inconsistent 'store'` e `inconsistent
  'compute_sudo'`. **Sin** cambio de valores (antes/después equivalentes).

### Tests
- Nuevo `tests/test_sv_rebaja_reset_concurrency.py` — **concurrencia REAL RESET-16/17** con transacciones
  PostgreSQL **independientes** (`db_connect`), coordinadas por eventos/barrera y timeouts:
  RESET-16 (dos reaperturas del mismo anulado ⇒ una sola transición, sin doble reserva ni doble auditoría;
  la perdedora rechazada por advisory lock con mensaje funcional) y RESET-17 (reapertura ∥ consumo de la
  misma capacidad del SV ⇒ sin sobreconsumo, rollback íntegro de la perdedora). Prueba de limpieza
  test-only («sin registros de prueba persistentes»).
- Ampliado `tests/test_sv_rebaja_reset.py`: **AUD-ETQ-07** (write directo con campos+contexto RECHAZADO;
  la acción controlada sí reabre) y **AUD-ETQ-08** (coherencia de `store`/`compute_sudo` de los campos
  `sv_assignment_*`).

### Notes
- **Intervención LOCAL** (`madenat_test`). **Sin commit/push/despliegue**; **TEST remoto intacto**;
  **sin reparación histórica**. `IMP02220`/`IMP04823` e históricos intactos. Backups en
  `BLINDAJE_REBAJA_LOCAL_20261012/` (código, base y filestore). Política de reservas y contrato de
  aplicación **sin cambios**. **Sobrescritura concurrente de borradores:** propuesta registrada, **pendiente**
  de autorización de Mauricio (no se activa).

## [18.0.1.21.0] - 2026-10-11

### Added
- **«Volver a borrador» — transición controlada `cancelled → draft`** (autorizada expresamente por
  Mauricio). Método `madenat.sv.imputation.action_reopen_to_draft`: exige **motivo** (no vacío tras
  `strip`), **permisos** (Operaciones/Jefatura/Gerencia), **guía elegible**, **ausencia de otro trabajo
  activo** de la guía y **capacidad suficiente** (el borrador vuelve a **reservar** su nominal). Bloquea
  y revalida con advisory locks; registra historia y no aplica la rebaja.
- Campos de trazabilidad: `cancelled_by_id`, `cancellation_date`, `cancellation_reason`,
  `reopened_by_id`, `reopen_date`, `reopen_reason`; botón «Volver a borrador» en el documento (estado
  `cancelled`) y en el asistente (`action_wizard_reopen`), con motivo; mensajes en el chatter y auditoría
  `imputation_cancel` / `imputation_reopen`.
- `madenat_lumber_core` (audit log): valores **aditivos** `imputation_cancel` e `imputation_reopen`.

### Fixed
- **Incidencia IMP04823** («ya no admite preparación (estado cancelled)»): el asistente quedaba ligado a
  un documento anulado sin acción de reapertura. Ahora el mensaje es operativo («El documento IMP… fue
  anulado. Vuelve a borrador para continuar, si su capacidad sigue disponible») y existe la salida
  «Volver a borrador».

### Security
- `write({'state': 'draft'})` sobre `cancelled` **no** elude la transición: exige usuario y motivo en la
  misma escritura **y** revalida permisos; `reversed → draft` y `applied → draft` siguen **prohibidos**.
  Un flag de contexto **no** autoriza.

### Tests
- Nuevo `tests/test_sv_rebaja_reset.py` (**RESET-01..15, 18, PHY-01**): reapertura conservando referencia e
  historia; reservas; repetición sin duplicar; capacidad consumida; conflicto de trabajo activo;
  permisos/compañía/motivo; write directo; applied/reversed; asistente desactualizado; corregir/continuar;
  reasignar/aplicar; varios SV; atomicidad; sin efectos físicos. Concurrencia RESET-16/17 **declarada
  pendiente** (no acreditada).
- Actualizada `test_sv_rebaja_simple.test_simple_01` (la botonera ahora incluye «Volver a borrador», visible
  sólo en estado anulado). Sin debilitar aserciones.

### Notes
- Sin modelos/wizard/menú/ledger nuevos; sin autosave; contrato de aplicación y política de reservas sin
  cambios. IMP04823 e IMP02220 **intactos** (no se reabren ni revierten en pruebas). Sin commit/push.

## [18.0.1.20.0] - 2026-10-11

### Changed
- **Simplificación operativa (solicitud expresa de Mauricio).** La ventana del asistente pasa a un
  recorrido de **DOS acciones**: **[Guardar]** (persistir para continuar) y **[Aplicar]** (ejecutar la
  rebaja), más **[Volver]** (navegación). **Ya no se exige** «Preparar asignación», ni Guardar antes de
  Aplicar, ni abrir el documento.
  - `action_apply`: crea/actualiza el documento, aplica y **permanece** en la misma ventana mostrando
    `apply_result` («Rebaja IMP… aplicada · X,XXX m³ hacia SV…»). No navega al documento.
  - `action_prepare`: permanece y muestra `save_result` («Borrador IMP… guardado… reserva documental
    prevista»).
  - **Opciones avanzadas** agrupadas en «Más opciones (avanzado)»: Abrir documento, Dejar pendiente,
    Proponer FIFO (métodos conservados; «Preparar asignación» sigue disponible en la tabla de Materiales
    como control avanzado).
  - **Volver** con `confirm` (evita pérdida inadvertida) y semántica clara: no cancela el documento ni
    libera reservas.
  - Tablas en **sólo lectura** tras aplicar (sin apariencia de borrador editable).

### Added
- Mensajes según el problema real al aplicar sin reparto positivo: «Indica los m³ a rebajar en las
  etiquetas seleccionadas.» (hay disponibilidad) o «Las etiquetas seleccionadas no tienen
  disponibilidad…» (consumidas por otra operación).

### Tests
- Nuevo `tests/test_sv_rebaja_simple.py` (**SIMPLE-01..17** + **CLIENT-01..03**): dos acciones, aplicar sin
  guardar ni preparar, guardar en la misma ventana, continuar, repetir sin duplicar, cero/negativo/exceso,
  sin disponibilidad, otros SV, «Usar disponible», descartar, resultado/bloqueo, permisos/compañía,
  reversión, sin efectos físicos.
- Actualizadas 2 pruebas al nuevo recorrido: `test_sv_rebaja_ui_limpia.test_arch_01` (etiquetas
  Guardar/Aplicar/Volver + opciones avanzadas) y `test_sv_rebaja_ui_acciones.test_ui_02` (botonera
  principal de dos acciones). Sin debilitar aserciones.
- Actualizadas 4 pruebas que leían el documento desde `res['res_id']` de `action_apply` (que ahora
  **permanece** en el asistente): `test_processor_return_link.test_t12`, `test_sv_imputation_i2.test_t_i2_13`,
  `test_sv_imputation_manual.test_man_03`, `test_sv_rebaja_navigation.test_nav_09` — ahora usan
  `wiz.imputation_id`. Mismas aserciones sobre el estado/saldos; sólo cambia de dónde se obtiene el
  documento.

### Notes
- Sin modelo/wizard/menú/ledger nuevos; sin autosave; sin auto-aplicar al seleccionar/editar; política de
  reservas y contrato de aplicación **sin cambios**; permisos **sin ampliar**. IMP02220 y `lot_flow_type`
  histórico intactos. **Sobrescritura concurrente de borradores: sigue como riesgo pendiente.** Sin
  commit/push.

## [18.0.1.19.0] - 2026-10-11

### Fixed
- **Acciones de guardado invisibles en el asistente (UI).** Incidencia de Mauricio: el asistente se abre
  como formulario amplio (`target="current"`) y sus acciones estaban **sólo** en un `<footer>`, que Odoo
  **no renderiza fuera de un diálogo** ⇒ «Guardar borrador», «Revisar y aplicar», «Dejar pendiente»,
  «Proponer FIFO» y «Cancelar» quedaban **invisibles**. Evidencia del arch efectivo: vista 2889 con
  `<header>` ausente y `<footer>` presente. **Corrección:** acciones movidas al **`<header>` nativo** y
  retiro del `<footer>`.

### Added
- **`action_open_document`** («Abrir documento», visible cuando hay documento persistente) y
  **`action_discard_changes`** («Descartar y volver», vuelve al SV sin borrar el borrador guardado ni
  liberar reservas).
- **Confirmación con referencia real**: `action_prepare`/`action_pending` **permanecen** en el asistente
  (recargan el propio registro) y muestran `save_result` («Documento IMP… guardado (estado: …). No se ha
  aplicado la rebaja. Las etiquetas seleccionadas mantienen la reserva documental prevista.»).
- `imputation_state` (related) para visibilidad coherente por estado; `save_result` (confirmación).
- «Continuar preparación» usa el mismo formulario amplio (target del action) para que el `<header>` esté
  siempre visible.

### Notes
- Sin modelo/wizard/menú/ledger nuevos; sin autosave documental; sin cambios de política de aplicación ni
  de reservas; sin ampliar permisos (el botón «Revisar y aplicar» conserva `groups=` y la validación
  backend). IMP02220 y `lot_flow_type` histórico intactos. Sin commit/push.

### Tests
- Nuevo `tests/test_sv_rebaja_ui_acciones.py` (**UI-01..05** + confirmación con referencia).
- Actualizada 1 prueba que asumía el `<footer>`: `test_sv_rebaja_ui_limpia.test_arch_01` — ahora exige los
  botones del **`<header>`** y la **ausencia** de `<footer>`; «Cancelar» se sustituye por
  **«Descartar y volver»** (destino claro al SV). No se debilitó ninguna aserción.

## [18.0.1.18.0] - 2026-10-11

### Fixed
- **Persistencia del trabajo de rebaja (SAVE).** Mauricio: «al preparar las asignaciones, estas no van
  quedando guardadas». **Causa demostrada:** «Preparar asignación» crea filas de reparto con cantidad 0 y
  «Guardar borrador» (`_i2_build_imputation`) **fallaba** con `UserError` («Indique un volumen mayor que
  cero…») si existía **alguna** fila a 0, de modo que **no se creaba/actualizaba el documento**. Ahora el
  destino previsto sin cantidad **no bloquea** el guardado: se conserva la etiqueta/línea y el resto de
  repartos; **no** se persiste un reparto inválido (el reparto sigue exigiendo volumen > 0).

### Added
- **`madenat.sv.imputation.work_sv_lot_id`** (SV de trabajo): relación de trabajo con la etiqueta SV de
  origen, fijada al guardar. Permite **localizar el borrador/pendiente desde el SV** aunque todavía no
  tenga reparto positivo (brecha de descubrimiento). No es fuente de saldo ni ledger.
- **`stock.lot.sv_assignment_work_imputation_ids` / `..._work_count` / `..._work_m3`**: trabajo **NO
  aplicado** del SV, **separado** de los agregados aplicados (no se suma a «Rebajado documental»).
- **`action_continue_preparation`** (en el documento y botón «Continuar» en el SV): reabre el asistente
  con la guía y el SV precargados para continuar el mismo trabajo (no aplica, no duplica).
- Descubrimiento ampliado: `action_open_sv_rebajas` incluye `work_sv_lot_id`; panel «Trabajo en
  preparación (no aplicado)» en el formulario del SV; columna «Trabajo en prep.» en el listado.

### Tests
- Nuevo `tests/test_sv_rebaja_persistencia.py` (**SAVE-01..14, FLOW-01..03, PHY-01**; 18 pruebas):
  persistencia, localización desde el SV, reapertura, actualización sin duplicar, cantidades cero,
  multi-SV, atomicidad, permisos/compañía, dos sesiones, aplicado no reabrible, firma sin colisión,
  cadenas completas y ausencia de efectos físicos.
- **3 pruebas existentes actualizadas** a la conducta corregida (codificaban la anterior): 
  `test_sv_rebaja_material.test_amt_01_cero_negativo_y_exceso` (cero ya **no** bloquea; el **negativo**
  sigue rechazándose), `test_sv_rebaja_navigation.test_nav_04_05_documentos_dentro_del_recorrido`
  (dominio del historial ahora incluye `work_sv_lot_id`) y
  `test_sv_rebaja_seleccion_asignacion.test_asg_03_sin_cantidad_guarda_trabajo_incompleto` (guardar sin
  cantidad **no** falla; queda borrador con la etiqueta y sin reparto). No se modificaron aserciones
  ajenas al cambio; no se debilitaron constraints.

### Notes
- Misma mecánica (`madenat.sv.imputation` + asistente + acciones/estados); sin modelo, ledger, wizard,
  menú ni mecanismo de guardado alternativo. Contrato de aplicación (18.0.1.17.0) **sin cambios**.
  IMP02220 y `lot_flow_type` histórico **intactos**. Sin commit/push.

## [18.0.1.17.0] - 2026-10-11

### Changed
- **Contrato de aplicación (APROBADO por Mauricio 2026-10-11).** **Aplicar** ahora exige **al menos un
  reparto válido con cantidad positiva hacia un SV autorizado** (`lot_flow_type='volume'`). Sin reparto,
  el documento **sólo** puede permanecer en un estado **no aplicado**; una fila de volumen cero no
  satisface el requisito. Validación en `madenat.sv.imputation._i2_validate_payload()` (se ejecuta en
  `action_apply` **antes** de locks, techos y escritura ⇒ cubre interfaz, ORM y RPC sin efectos
  parciales). Mensaje: «No se puede aplicar la rebaja: asigna una cantidad positiva a un SV. Puedes
  guardar el documento sin aplicarlo.»
- **`NO_SV_CANDIDATE` deja de ser excepción de aplicación.** El flag se conserva como **informativo** en
  listados/filtros; ya no permite aplicar sin destino mediante un motivo.
- **Sin cambios** en: preparación/guardado de trabajo incompleto (`action_prepare`/`action_pending`),
  política de reservas, reparto parcial y a varios SV, inmutabilidad del aplicado, reversa con motivo,
  idempotencia, concurrencia y ausencia de efectos físicos.

### Tests
- Nuevo `tests/test_sv_rebaja_contrato.py` (**POL-01..08**): sin reparto→rechazo · cero→rechazo ·
  positivo→permitido · parcial→pendiente explícito · guardar/reabrir incompleto→conserva sin aplicar ·
  ORM/RPC directo→rechazo · repetición tras rechazo→sin efectos · aplicar→revertir→reasignar→aplicar.
- Actualizadas 4 pruebas que acreditaban la conducta anterior de aplicación sin reparto
  (`test_sv_imputation_i2.T-I2-06`, `test_sv_imputation_candidates.CAND-07/08/09`), alineadas a la
  política aprobada (ahora exigen **rechazo** y estado **no aplicado**).

### Notes
- Contrato aprobado y probado; **aceptación operativa pendiente (navegador)**. IMP02220 permanece
  **sin reparar**. Estado: `madenat_lumber_logistics` **18.0.1.17.0**. Sin commit/push.

## [18.0.1.16.0] - 2026-10-11

### Added
- **AUD-ETQ-07 — regla de registro multi-compañía de la imputación documental SV.**
  Nuevo `security/madenat_sv_imputation_rules.xml`: regla **global** de compañía para
  `madenat.sv.imputation`, `.line` y `.sv.line`, con el mismo patrón que la relación hermana
  `madenat.processor.return.link` y `stock.lot`
  (`['|', ('company_id','in',company_ids), ('company_id','=',False)]`). Antes, la cabecera declaraba
  `company_id` obligatorio pero **no** aislaba por compañía: un usuario de otra compañía podía
  leer/escribir/aplicar documentos ajenos (sólo ACL por grupo). Sin impacto para el uso
  mono-compañía vigente; se suma a los permisos por rol.

### Fixed
- **AUD-ETQ-06 — motivo de reversa no vacío tras `strip`.** `action_reverse` aceptaba un motivo
  formado sólo por espacios. Ahora exige texto no vacío tras `strip()`.

### Tests
- Nuevo `tests/test_sv_rebaja_cierre.py` (AUD-ETQ-06..10): inmutabilidad profunda (write/unlink de
  líneas y repartos del aplicado), motivo de reversa (vacío/espacios/contexto/sin permiso/repetida/
  trazabilidad), aislamiento multi-compañía sin `sudo`, ciclos completos A (cancelar→liberar→
  reasignar→aplicar) y B (aplicar→revertir→restituir→reasignar→aplicar) con dos SV, compromiso
  parcial 5/3 y ausencia de efectos físicos.
- Sonda de concurrencia real (`AUDIT_REBAJA_ETIQUETAS_20261011/evidence/concurrency_probe.py`):
  cursores independientes + `threading.Barrier`; Q1 doble aplicación (1 aplicado, sin sobreconsumo),
  Q2 doble reversa (una restitución/auditoría), Q3 aplicar∥cancelar (techo duro). `RESULTADO GLOBAL: OK`.

### Notes
- Cierre probatorio de la auditoría 18.0.1.15.0. **IMP02220** (guía 19827, aplicada sin reparto SV) se
  diagnosticó como **documento válido según el código pero funcionalmente incompleto**; **no** se
  reparó (requiere decisión/autorización). Ver `CANON/19` §19.22. Sin efectos físicos; sin commit/push.

## [18.0.1.15.0] - 2026-10-11

### Fixed
- **AUD-ETQ-01 — inmutabilidad real de una imputación aplicada.** `madenat.sv.imputation.write`
  permitía escribir libremente `state` (estaba en `I2_APPLIED_WRITABLE`), de modo que una imputación
  **aplicada** podía volver a `draft`/`pending`/`cancelled` por ORM/RPC, liberando capacidad y
  reescribiendo la historia (contradice AD-91). Ahora `state` ya **no** es libre: la única transición
  admitida sobre `applied` es `→ reversed` y **sólo** mediante `action_reverse` (exige usuario de
  reversa). Cualquier otra transición se rechaza en el modelo.
- **AUD-ETQ-02 — la reversa exige motivo.** `madenat.sv.imputation.action_reverse` no exigía motivo
  (`reversal_reason`/`reason`); la relación hermana `madenat.processor.return.link.action_reverse` sí.
  Ahora exige motivo no vacío (trazabilidad, §12/§16-R02).
- **AUD-ETQ-03 — el mapa lote↔packing no elige arbitrariamente.** `_compute_packing_line` usaba
  `mapping.setdefault(...)`: ante una **colisión** de clave (dos líneas de packing con el mismo
  `lot_name` + SKU + dígitos de guía) asociaba la primera. Ahora la clave colisionante se marca
  **ambigua** y la asociación queda vacía (no se elige al azar). Lógica extraída a
  `_i2_build_packing_map`.
- **AUD-ETQ-04 — causa del saldo concreta y trazable.** La disponibilidad cero se explicaba con un
  aviso genérico («aplicado, reservado o sin capacidad»). El asistente ahora muestra por etiqueta la
  **causa concreta** (`disponibilidad_detalle`: documento(s) y volumen que la consumen) y ofrece
  **acceso a los documentos** que la explican (`disponibilidad_imputacion_ids`,
  `action_open_consuming_documents` por fila y `action_open_no_availability_docs` global). Derivado de
  los saldos documentales reales; sin crear ni modificar documentos.

### Tests
- Nuevo `tests/test_sv_rebaja_blindaje.py` (AUD-ETQ-01..05) + registro en `tests/__init__.py`.
- Ajustados los llamados existentes a `action_reverse` de `madenat.sv.imputation` para fijar el motivo
  obligatorio (`test_sv_imputation_i2`, `test_sv_imputation_candidates`,
  `test_service_return_imputation_guard`, `test_processor_return_link`, `test_sv_rebaja_operativa`);
  comportamiento acreditado, no cosmético.

### Notes
- Auditoría integral del ciclo de rebaja de etiquetas (2026-10-11). Sin cambios de política salvo los
  defectos demostrados; sin nuevo mecanismo/menú/ledger; sin efectos físicos de stock. Expediente de
  evidencia: `AUDIT_REBAJA_ETIQUETAS_20261011/`.

## [Unreleased]

### Fixed
- **Despliegue (2026-10-06):** eliminado el `<record ... madenat_lumber_shipping_core.menu_shipping_booking ... active=False>` en `views/logistics_menus.xml` (registro inexistente; el menú "Reservas" se define localmente en Logistics). Quitado el atributo inválido `help` del campo `backlog_note` (vista `lumber.shipment.document.backlog.list`) en `views/lumber_document_checklist_views.xml`. Corrige `Cannot update missing record` e `Invalid attribute help for element field`. Actualización remota OK (resultado 0). Validación local: XML bien formado (no se ejecutó Odoo/`-u`).

## [18.0.1.14.1] - 2026-10-10

### Fixed
- **HOTFIX BLOQUEANTE — OwlError al abrir «Registrar rebaja» (`column_invisible` fuera de contexto).**
  El error real reportado por Mauricio en el navegador fue:
  `EvalError: Can not evaluate python expression: (bool(not wizard_id.multi_sv))` —
  `Name 'wizard_id' is not defined`, originado en `ListRenderer.evalColumnInvisible`.
  **Causa demostrada:** en Odoo 18 `column_invisible` se evalúa con el **contexto del formulario
  contenedor** (`list_renderer.js::evalColumnInvisible` usa `this.props.list.evalContext`), donde sólo
  se expone `parent` (el registro del formulario padre) y **no** los campos de cada fila. Por eso
  `wizard_id` (campo de las filas `madenat.sv.imputation.wizard.sv.line`) no está definido.
  Corrección: `column_invisible="not parent.multi_sv"` (patrón canónico de Odoo core, p. ej.
  `account.move.line` → `parent.move_type`), y **carga explícita** de `<field name="multi_sv"
  invisible="1"/>` en el formulario padre para que `parent.multi_sv` esté disponible. **No** se añadió
  `wizard_id` como columna, **no** se eliminó la condición, **no** se capturó la excepción, **no** se
  tocó Owl ni assets del core. Sin cambios de negocio: se preservan cantidad editable desde Materiales,
  reparto como fuente de verdad, repartos a otros SV, identidad/descripción del material,
  `processed_lot_id` obligatorio y `force_save`, disponibilidad, reservas, aplicación, reversa, permisos,
  atomicidad e idempotencia.

### Notes
- **Origen y límites:** el fallo **apareció en la comprobación real del navegador** (no fue detectado por
  las pruebas XML/ORM previas: una validación de arch no demuestra la evaluación de la expresión en el
  cliente). Estado: **«Incidencia bloqueante de renderización; aceptación pendiente»**. Sin navegador en
  el entorno → **renderización pendiente de comprobación manual**. Sin commit/push ni despliegue remoto.

## [18.0.1.14.0] - 2026-10-10

### Changed
- **Interfaz clara y concisa de «Registrar rebaja» en AMBAS pestañas (CANON/19 §19.19).** La cabecera es
  **única** (SV de trabajo, guía, saldo documental del SV, seleccionadas, **con reparto preparado**,
  **preparado para el SV**); ya **no** se repite el nominal ni el saldo completo del mismo SV en cada
  fila. Se distingue **seleccionadas ≠ con reparto preparado ≠ total en m³** (no se presenta «17
  etiquetas» como 17 asignaciones válidas si todas siguen en cero).
- **Totales con nombre y unidad:** Piezas de origen, Volumen documental de origen (≠ volumen a imputar),
  Disponible documental de las seleccionadas (agregable sin doble conteo) y Preparado para el SV. Con
  varios SV se separa el **subtotal del SV de trabajo** del **total general**.
- **Materiales del retorno:** columnas Etiqueta limpia · SKU origen · Producto · Espesor · Ancho · Largo
  · Piezas · Vol. documental · Disponible · **A asignar (m³) — EDITABLE**. «A asignar» se integra con el
  mismo reparto (`sv_line_ids`): crea/actualiza/elimina sólo la fila de esa etiqueta hacia el SV de
  trabajo (sin saldo paralelo, sin borrar repartos a otros SV). Subproducto, dimensiones declaradas y
  código técnico quedan como información secundaria (columnas opcionales).
- **Asignación a SV:** para un solo SV, tabla **Etiqueta · Medidas · Disponible (m³) · A asignar (m³)**;
  el SV destino se muestra en la cabecera y la columna **«SV destino»** aparece sólo con varios SV
  (`column_invisible` ligado a `multi_sv`). La identificación material es la misma en ambas pestañas
  (etiqueta limpia + medidas), sin cambiar `display_name`.
- **Etiqueta limpia y medidas:** la etiqueta es el `lot_name` del packing (etiqueta de proveedor), no el
  `stock.lot.name` concatenado; las medidas se presentan como «45 × 125 mm · 2,900 m» para distinguir
  lotes con etiqueta repetida.
- **Acciones:** etiquetas breves (Seleccionar todas · Quitar selección · **Preparar asignación** · Usar
  disponible); «Preparar asignación» aclara «prepara el reparto al SV de trabajo; no aplica la rebaja».
  «Usar disponible» tiene el MISMO alcance en ambas pestañas (filas del SV de trabajo con etiqueta
  seleccionada) y **no sobrescribe cantidades editadas** (sólo rellena filas aún en cero). Footer:
  Guardar borrador · **Revisar y aplicar** · Cancelar; FIFO y Dejar pendiente como `btn-link`.
- **Ayuda breve:** una línea («Selecciona el material, indica los m³ y prepara la asignación. Sólo
  Aplicar registra la rebaja.») y el aviso «Rebaja documental: no mueve stock físico.»; se retiran los
  párrafos con explicaciones de implementación.
- **Filas sin disponibilidad:** estado por fila derivado de los saldos reales (Disponible · Aplicado ·
  Reservado · Sin capacidad documental) y aviso de cuántas etiquetas seleccionadas carecen de
  disponibilidad al usar «Seleccionar todas»; no se tratan como asignables ni se borran reservas.

### Notes
- **Sin cambios de negocio**: disponibilidad, reservas, reparto, aplicación, reversa, idempotencia y
  atomicidad intactos. El volumen documental **no** se recalcula desde dimensiones. Sin nuevos
  menús/wizard/documento/ledger. **Aceptación visual de Mauricio pendiente.**

## [18.0.1.13.0] - 2026-10-10

### Changed
- **Rediseño operativo del asistente «Registrar rebaja» (CANON/19 §19.18).** La tabla principal pasa a
  presentar el **material del packing list** en columnas separadas: **Etiqueta** (`stock.lot.ref`),
  **SKU origen**, **Producto**, **Subproducto**, **Espesor/Ancho/Largo técnicos (mm/m)**, **Piezas** y
  **Volumen documental (m³)**, más **Disponible para esta operación** y **Cantidad preparada (m³)**.
- **Identidad y SKU sin cortar nombres:** el SKU de origen y las dimensiones **declaradas** se toman de
  la línea de packing (`madenat.guia.processing.line.sku_original`, `espesor_nominal_mm`,
  `ancho_nominal_mm`, `largo_nominal_m`) asociada al lote por la **misma regla de promoción**
  (`stock.lot.name = etiqueta + SKU + dígitos de la guía`). Si no hay coincidencia, se muestra vacío
  («—»); **no** se recorta el nombre ni se inventan valores. Verificado sobre la guía real 19827:
  **17/17** lotes mapeados.
- **Granularidad:** una fila = un `stock.lot` (unidad asignable real). Una **etiqueta repetida**
  corresponde a **lotes distintos** (p. ej. D7719 ×2 con largos distintos) y **no** se deduplica; la
  disponibilidad es por lote (`_i2_lot_available_for_m3`) ⇒ sin doble conteo.
- **Documental avanzada** (Capacidad nominal, Nominal comprometido, Rebajado etiqueta aplicado,
  Reservas, Pendiente de reparto, Lote interno, dimensiones declaradas, volumen de embarque) se mueve a
  **columnas opcionales** que no se intercalan con la descripción de la madera.
- **Ancho:** el asistente se abre como **formulario amplio** (`o_xxl_form_view`, mismo wizard, sin
  crear otro) en lugar del modal estrecho; `target` del mismo action `new → current`.
- **Cabecera compacta:** SV de trabajo, guía, **saldo documental del SV**, seleccionadas, total
  preparado y resumen «X etiquetas · Y m³ preparados para SV…».
- **Jerarquía de acciones:** «Asignar seleccionadas al SV de trabajo» y «Usar disponible» junto a la
  tabla; «Proponer FIFO (propuesta)» y «Dejar pendiente» pasan a `btn-link` (menor jerarquía).

### Notes
- **Sin cambios de negocio**: mismas reglas de disponibilidad, reservas, reparto, aplicación y reversa.
  El volumen documental **no** se recalcula desde dimensiones. La «Cantidad preparada» de la tabla
  principal es **solo lectura** y refleja el reparto real de «Asignación a SV» (mismo mecanismo; sin
  saldo paralelo).
- Sin nuevos menús, wizard, documento, ledger ni motor de saldos. Sin cambios en ingesta. Bloque D
  fuera de alcance. **Aceptación visual de Mauricio pendiente.**

## [18.0.1.12.0] - 2026-10-10

### Fixed
- **«Seleccionar todas» fallaba al abrir el asistente desde el navegador (CANON/19 §19.17).** Causa
  **demostrada** en el cliente Odoo 18
  (`web/static/src/model/relational_model/record.js::_getChanges`): un subcampo `readonly` de una
  x2many **no se envía** al servidor salvo `force_save="1"`. El campo `processed_lot_id` del listado
  del asistente era `readonly="1"` **sin** `force_save`, por lo que los comandos CREATE de las filas
  llegaban sin el identificador y el `create` de `madenat.sv.imputation.wizard.line` fallaba con
  *processed_lot_id required*. Corrección: `force_save="1"` en `processed_lot_id`. **No** se quitó
  `required`, **no** se añadió etiqueta ficticia, **no** se capturó la excepción ni se usó `sudo`.

### Added
- **Acción explícita «Asignar seleccionadas al SV de trabajo»** (`action_assign_selected`): crea una
  fila de reparto por etiqueta seleccionada con el SV de trabajo y **volumen 0** (el usuario
  introduce el volumen o usa **«Usar disponible»**). No aplica, no mueve stock, no crea otro
  documento, no duplica filas, no sobrescribe cantidades y **no borra repartos a otros SV**.
- **«Usar disponible»** (`action_use_available`): acción **explícita** que rellena el volumen con
  `min(disponible documental de la etiqueta, nominal comprometido)`. Nunca se rellena solo.
- **Resumen breve** `assigned_summary` («X etiquetas · Y m³ preparados para SV…») y **«Pendiente de
  reparto»** (`etiqueta_pendiente_m3` = nominal comprometido − reparto de este documento).

### Changed
- **Listado «Etiquetas del retorno» simplificado:** columnas primarias Seleccionar · Etiqueta
  proveedor · Lote interno · Disponible para esta operación · Nominal comprometido; secundarias como
  columnas **opcionales** (Capacidad nominal, Rebajado etiqueta aplicado, Reservado, Pendiente de
  reparto). Se aclara en la vista que **Seleccionar ≠ asignar ≠ aplicar**.
- **Semántica de rótulos:** se distingue **Nominal comprometido** (lado etiqueta, techo duro) de
  **Rebajado etiqueta aplicado** (lado etiqueta) y del **volumen asignado al SV** (tabla de
  asignación). Un reparto parcial (nominal 5, SV 3) ya no se presenta como «5 rebajado».
- **«Proponer FIFO»** deja de borrar todo el reparto: sólo rehace las etiquetas **seleccionadas**,
  conservando el reparto de las no seleccionadas (p. ej. a otros SV).
- **Asignación a SV:** el listado pasa a `create="false"` (las filas se crean con la acción
  explícita), evitando filas nuevas sin `wizard_line_id`.

### Notes
- Sin nuevos menús, wizard, documento, ledger ni motor de saldos. Sin cambios en la ingesta. Bloque D
  cuantitativo fuera de alcance. **Aceptación visual de Mauricio pendiente.**

## [18.0.1.11.0] - 2026-10-10

### Added
- **Operación y blindaje de «Rebaja de etiquetas» (CANON/19 §19.16).**
  - **Elegibilidad de retorno (Bloque B):** el selector de «Guía de retorno» usa el dominio canónico
    `service_return_confirmation='yes'` **y** `state!='cancelled'` (el mismo que exige el apply, más
    la exclusión de canceladas). Se rechaza la selección forzada (No/vacío/cancelada) en el `onchange`
    y **antes** de construir el documento (`_i2_build_imputation`), sin estados parciales. Los
    **históricos** siguen consultables.
  - **Semántica de magnitudes documentales (Bloque D):** nuevos ayudantes de modelo
    `_i2_lot_reserved_m3`, `_i2_lot_applied_m3`, `_i2_lot_available_for_m3` y columnas del asistente
    **Nominal lote / Rebajado aplicado / Reservado borrador-pend. / Disponible documental**,
    calculadas **excluyendo el documento en curso** para no contarse dos veces al editarlo.
  - **Listado SV y búsqueda (Bloques A/C):** columnas separadas N° Guía, Proveedor, Fecha (opcional),
    Producto, Procesador y las tres magnitudes; filtros documentales **Con/Sin saldo**, **Con/Sin
    rebajas aplicadas** y **Exceso documental**; búsqueda por Etiqueta SV, Guía/Proveedor y Producto.
    Los agregados SV (`sv_assignment_*`) pasan a `store=True` para ser filtrables sin dominios
    inventados sobre campos no buscables. Columnas opcionales de retorno en el listado de guías
    (usadas por «Buscar más») y filtros de retorno.
  - **Resumen previo (Bloque E):** «Aplicado previo» y «Disponible documental» del alcance
    seleccionado, sin doble conteo; mensaje breve «Actualiza el saldo documental SV. No mueve stock
    ni modifica el ledger SV».

### Fixed
- **Concurrencia entre documentos (CON-01):** `_i2_lock_resources` toma advisory locks de transacción
  en un **orden global determinista**, incluyendo la **etiqueta de retorno** (namespace 3) además del
  SV (namespace 2). Cierra el riesgo de que dos documentos apliquen a la MISMA etiqueta hacia SV
  distintos superando su techo duro. Se adquieren **antes** de revalidar los techos.
- **Revalidación de elegibilidad al aplicar:** un cambio de estado/confirmación de la guía entre la
  apertura y la aplicación se rechaza de forma comprensible y sin estados parciales (guía cancelada
  incluida).

### Changed
- Cuatro campos agregados de `stock.lot` (`sv_assignment_nominal_m3`, `_applied_m3`,
  `_applied_count`, `_documental_balance_m3`) pasan de `store=False` a **`store=True`** (sólo lectura)
  para habilitar los filtros documentales del listado. Sin cambios de dominio de negocio.

### Notes
- Sin cambios en la ingesta, en «Rebajar por Motonave» ni en «Consolidación». Sin nuevas bases,
  contenedores, ramas, menús, wizard, documento, ledger ni motor de saldos. Bloque D cuantitativo
  fuera de alcance.

## [18.0.1.10.0] - 2026-10-10

### Changed
- **Unificación de acceso — «Rebaja de etiquetas» (CANON/19 §19.15).** La asignación documental SV
  queda con **un único enlace operativo** en Logística Exportación:
  - El menú `menu_madenat_sv_assignment` se renombra de «Asignaciones SV» a **«Rebaja de etiquetas»**
    y sigue apuntando a la acción sobre `stock.lot` (`lot_flow_type='volume'`). La acción también se
    renombra a «Rebaja de etiquetas»; el listado/formulario dedicado pasa a **«Etiquetas SV» /
    «Etiqueta SV»** con encabezados **Volumen documental / Rebajado documental / Saldo documental**.
  - Se añade una **búsqueda dedicada** (Etiqueta SV, Guía de procedencia, Producto) sin el panel
    técnico heredado; «En stock» queda como **filtro opcional removible** (existencia física; **no**
    es el saldo documental) y **no** es condición obligatoria.
  - **Navegación interna del recorrido:** en la ficha del SV, «Registrar rebaja» (asistente existente),
    «Historial de rebajas» (documentos que asignan a ese SV) y «Ver historial completo». Se conserva
    la lista de asignaciones con «Abrir documento». El historial distingue **vigentes** de
    **históricos** (filtros Borrador/Pendiente/Aplicada/Reversada/Anulada).

### Removed
- **«Imputaciones documentales SV» retirado de la navegación.** El menú `menu_madenat_sv_imputation`
  se desactiva (`ir.ui.menu.active = False`) mediante un `record` posterior a su `menuitem`
  (mecanismo **reproducible y reversible**): al reaplicar `-u` el `menuitem` no vuelve a fijar
  `active`, por lo que **no reaparece**. **No** se borran modelos, documentos ni acciones; la acción
  `action_madenat_sv_imputation` se conserva y se rotula **«Historial de rebajas»** para el acceso
  interno.

### Fixed
- **Duplicidad de navegación:** «Asignaciones SV» e «Imputaciones documentales SV» dejaban de ser dos
  accesos paralelos a la misma operación documental. La operación se ejecuta en **un solo lugar**;
  los documentos de imputación son **detalle/historial** del mismo mecanismo. Sin cambios en modelo,
  asistente, `action_apply`/`action_reverse`, saldos, permisos, auditoría ni en «Rebajar por
  Motonave»/«Consolidación»/ingesta.

## [18.0.1.9.0] - 2026-10-10

### Added
- **Operación manual de asignaciones centrada en SV (CANON/19 §19.14).**
  - **Bloque A — entrada y consulta:** acción **Logística → Asignaciones SV** sobre
    `stock.lot` (`lot_flow_type='volume'`) con **vistas dedicadas** (no altera otras
    vistas de lotes y no crea modelo persistente nuevo). Cabecera con etiqueta SV,
    guía de procedencia, producto, procesador, nominal documental, total imputado
    **aplicado** y **saldo documental I2**; aviso «La imputación no modifica stock ni
    saldo del ledger SV». Detalle con imputación, guía, etiqueta, volumen, estado,
    fecha, usuario y acceso al documento.
  - **Bloque B — alta desde el SV:** botón **«Asignar retorno»** que abre el asistente
    existente con `sv_lot_id` en contexto (orienta; **no** genera reparto, cantidades
    ni aplica nada).
  - **Bloque C — selección explícita de etiquetas:** booleano `selected` por línea +
    «Seleccionar todas» / «Quitar selección» e indicadores seleccionadas/disponibles.
    Una operación nueva **no** incluye etiquetas automáticamente.
- **Bloque D — conservación del borrador:** `_i2_build_imputation` pasa de borrar/recrear
  a **upsert** por `processed_lot_id` y `(línea, SV)`; al abrir/reabrir se reproduce la
  selección y el reparto guardados del documento de trabajo; cambio de guía bloqueado en
  imputaciones de trabajo ya vinculadas.

### Fixed
- **Bloque E — integridad etiqueta–guía (D10):** constraint de modelo
  `_check_label_belongs_to_guia` (creación/escritura/apply/ORM/RPC). Inspección de
  históricos en sólo lectura: **0** inconsistencias detectadas.
- **Bloque F — coherencia de volumen (D10/D11):** constraints de modelo
  `_check_reparto_within_nominal` (línea) y `_check_within_line_nominal` (reparto):
  `0 < Σ reparto ≤ nominal autorizado`; se conserva el techo duro etiqueta-side existente
  y se admiten asignaciones **parciales**. No se toca `sv_available_m3` ni el ledger.

### Changed
- Asistente `madenat.sv.imputation.wizard`: nombres de pestañas («Etiquetas del retorno»,
  «Asignación a SV», «Envíos relacionados», «Motivo / reversa»), mensaje de efecto
  documental y `sv_lot_id`. «Proponer FIFO» opera sólo sobre la selección explícita.

## [18.0.1.8.0] - 2026-10-10

### Added
- **Ajuste de integridad del vínculo envío–retorno (CANON/19 §19.13).**
  - **Reversa de imputación vs. procedencia:** `state` = **procedencia** (envío↔retorno);
    nuevos campos **`documentary_status`** (vigencia documental derivada del estado real de la
    imputación) y **`requires_reimputation`**. Reversar la imputación **no** revierte la procedencia.
  - **Reimputación:** `previous_imputation_id` conserva la imputación reemplazada; se deja rastro
    (chatter + auditoría `processor_return_link`, descripción «reimputación») sin sobrescribir en
    silencio ni duplicar vínculos activos.
  - **Consistencia de compañía** (`_check_company_consistency`) y **regla de registro multi-compañía**
    (`security/madenat_processor_return_link_rules.xml`). `madenat.guia.processing` no tiene
    `company_id` (documento): no se compara.
  - **Elegibilidad dura por modelo/ORM/RPC:** sólo envíos validados (`state='done'`) y de tipo interno
    (`picking_type_id.code='internal'`). Dominio y validación alineados.
  - **Volúmenes N:M referenciales:** `aggregator=False` en `shipment_volume_m3`/`return_nominal_m3`
    (sin agregación engañosa en pivot/graph/`read_group`) + ayuda explícita. Sin reparto ni resta.
  - Vistas: badge de vigencia documental, filtro «Requiere reimputación» y grupo por vigencia.
  - Pruebas: `test_processor_return_link.py` **T1–T22** (22/22).

## [18.0.1.7.0] - 2026-10-10

### Added
- **Bloque A/B/C (CANON/19 §19.11) — Relación de conciliación envío–retorno (procesador).**
  - Nuevo modelo persistente `madenat.processor.return.link` (enlaza el **envío** `stock.picking`
    —no el wizard transitorio—, la **guía** de retorno y la **imputación** documental SV). Estados
    `draft` → `linked` → `reversed`; N:M; unicidad por par en estados activos; inversos en
    `stock.picking`, `madenat.guia.processing` y `madenat.sv.imputation`.
  - Magnitudes **separadas** (sin resta): `shipment_volume_m3` y `return_nominal_m3`. **No** calcula
    saldo de proceso, rendimiento ni merma (Bloque D pendiente).
  - Permisos por ORM/RPC (registrar: Operaciones/Jefatura/Gerencia; reversar: Jefatura/Gerencia);
    append-only con motivo, evidencia firmada (SHA-256) y auditoría aditiva
    `processor_return_link` / `processor_return_link_reverse`.
  - Asistente de imputación **reutilizado**: pestaña «Envíos a procesador (retorno)» (envíos
    elegibles del mismo procesador); al aplicar registra las relaciones.
  - Pestañas de trazabilidad en guía y picking; menú de Logística «Conciliación Envío–Retorno».
  - Pruebas: `tests/test_processor_return_link.py` T1–T12 (12/12). Ver `03_TESTS.md` §15.


## [HF-001] — 2026-06-03 — Hotfix: Revertir imports inválidos entre addons

### Fixed
- **CRÍTICO:** Revertidos imports Python absolutos `from madenat_lumber_core.models.utils_uom import MM_PER_INCH, M3_DIVISOR`
  que rompían el mecanismo de carga del registry de Odoo 18 CE en Docker.
  Evidencia: `AssertionError: Invalid import of madenat_lumber_core.models.reception_parser.MadenatReceptionParser,
  it should start with 'odoo.addons'`
  - Línea 79: `ancho_mm / MM_PER_INCH` → `ancho_mm / 25.4  # HF-001`
  - Línea 124: `adjusted_width_inch * MM_PER_INCH` → `adjusted_width_inch * 25.4  # HF-001`
  - Línea 131: `/ float(M3_DIVISOR)` → `/ 1_000_000.0  # HF-001`
  - Restricción documentada en `utils_uom.py` para futuros desarrolladores

### Deuda Técnica
- TD-004B pendiente: diseñar arquitectura correcta para constantes compartidas entre addons
  (módulo utils puro sin modelos ORM)

### Validado
- HTTP 200 en `/web/health`
- Golden records inalterados: A1M2605458=4.893, A1M2602536=4.832

---

## [Unreleased]

### Fixed
- TD-004: Centralización de constante física universal `25.4` → `MM_PER_INCH` en `lumber_shipment_line.py:78,123`
- TD-005: Centralización de divisor métrico `1_000_000.0` → `M3_DIVISOR` en `lumber_shipment_line.py:131`. Agregado import `M3_DIVISOR` desde `utils_uom`.
- Wizard de asignación de lotes: corregido el dominio de disponibilidad para incluir lotes con `estado_trazabilidad = 'procesado'` y `'recepcionado'`, además de `'en_patio'`. Anteriormente solo se mostraban lotes con estado `'en_patio'`, lo que excluía lotes válidos de guía procesada y recepciones en curso.
- Clasificación de lotes: corregido `_is_processed_lot()` en `stock_lot.py` para que `subproducto_id` por sí solo no marque un lote como procesado. El subproducto es clasificación comercial, no indicador de procesamiento. Solo `guia_processing_id`, `parent_lot_id` o dimensiones finales indican procesamiento real.

### Added

- Documentación técnica completa del módulo: README, arquitectura y reglas de disponibilidad.
- Definición formal de la regla canónica de disponibilidad para asignación de lotes a contenedores.
- Tabla de semántica de estados de trazabilidad (`estado_trazabilidad`).

### Changed

- UX de consolidación de contenedores alineada con dimensiones comerciales: wizard de asignación muestra E"/A"/L(ft) como principales, mm/m como opcionales. Pestaña "Lotes Asignados" del contenedor prioriza L(ft) sobre L(m).
- Wizard `lumber.consolidation.import.wizard` archivado como dead code documentado. El archivo existe en `wizards/lumber_consolidation_import_wizard.py` pero no está integrado (sin import, sin vista XML, sin acción). Su lógica era incompatible con el modelo actual (escribe campos inexistentes en `stock.lot`). El flujo canónico de asignación a contenedores es `lumber.container.lot.wizard`.
- Documentación del dominio del wizard para reflejar la regla de disponibilidad canónica.
- Comentario en `_is_processed_lot()` para documentar que `subproducto_id` no es indicador de procesamiento.

## [2026-05-31]

### Fixed

- Parche TD-006: corrección en dos pasos de la clasificación de lotes y disponibilidad para contenedor.
- Lotes de recepción con `subproducto_id` ahora se clasifican correctamente como `'en_patio'` en lugar de `'procesado'`.
- Wizard de contenedores muestra lotes de ambos orígenes (recepción y guía procesada) sin exclusión incorrecta.

## [2026-05-30]

### Fixed

- Campo `ref` en `stock.lot` ahora se escribe desde `lumber.reception` al crear lotes desde staging. El wizard de contenedores ahora muestra correctamente la etiqueta/código del lote.
- Campo `subproducto_id` en `stock.lot` ahora se escribe desde `lumber.reception.line.subproduct_id` al crear lotes desde staging. El wizard de contenedores ahora muestra correctamente el subproducto.
- Data migration: 20 lotes existentes actualizados con `ref` y `subproducto_id` desde las líneas de recepción correspondientes.

## [2.4.0] - 2025-12-13

### Added

- **Constraint Inteligente:** `_check_shipment_change_with_distributed_costs` para proteger integridad financiera.
- **Trazabilidad de Costos:** Campos `is_distributed` y lógica de distribución detallada.

### Changed

- **Distribución de Costos:** Reingeniería de `action_distribute_costs` para soportar escritura en `stock.lot.cost.line` y campos legacy (Dual Write).
- **Estándar:** Alineación con arquitectura de costos SAP/Oracle.
