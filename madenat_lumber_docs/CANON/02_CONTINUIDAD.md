# MADENAT — Estado de Continuidad Técnica

**Versión documental:** 12.42.0
**Fecha de actualización:** 2026-10-18  <!-- actualizado: 2026-10-18 — Bloque 4H (AD-121): verificación de D4 (método de entrega sin git pull documentado pero no ejecutado), línea base fijada stock_lot (6667a4bd...), naturaleza real de Consulta B (hash MD5 volúmenes redondeados a 4 decimales: 5c2152...) y sumas complementarias. Versión 02 12.41.0 → 12.42.0. Sin push ni despliegue. -->
<!-- actualizado: 2026-10-18 — §18 **PROCEDIMIENTO OPERACIONAL DE DESPLIEGUE A TEST REMOTO (G9 AD-120 — BORRADOR, NO EJECUTADO)**: método de entrega sin git pull (transferencia por rsync/empaquetado según §17.14), actualización quirúrgica sin -u all según comparación de manifiestos, respaldo triple (BD, filestore, código), validación dual con pre_deploy_health_check.py (G3), hashes MD5 con consulta fijada (G4), impacto de noupdate="1", vectores planilla/blanks y checklist para Cristhian Elgueta. Versión 02 12.40.0 → 12.41.0. Sin push ni despliegue. | 2026-10-10 (1) — §17.16 **CIERRE FUNCIONAL DE PENDIENTES (P0–P4)** en el desarrollo existente `madenat_test` -->
<!-- actualizado: 2026-10-10 (2) — §17.16.8 aceptación visual (guía 19827, confirmada por Mauricio 2026-10-10) y §17.16.9 flujo de imputación SV confirmado en código (detalle en CANON/19 §19.10). Solo documentación; sin cambios de código, base ni servicios. -->
<!-- actualizado: 2026-10-10 (3) — §17.16.10 relación de conciliación envío–retorno (Bloque A/B/C): modelo `madenat.processor.return.link`, estados draft/linked/reversed, permisos por rol, append-only, auditoría aditiva, asistente de imputación reutilizado, pestañas y menú. Cierra la brecha (a) de CANON/19 §19.10. Bloque D (cuantitativo) NO implementado. Versión 02 12.17.0 → 12.18.0; 19 1.8.0 → 1.9.0. Sin commit/push. Evidencia: CONCILIACION_ENVIO_RETORNO_20261010/. -->
<!-- actualizado: 2026-10-10 (3) — §17.16.11 ajuste de integridad del vínculo envío–retorno (reversa vs. procedencia, reimputación, compañía+regla de registro, elegibilidad dura, volúmenes N:M referenciales). Módulo `madenat_lumber_logistics` **18.0.1.8.0**. Regresión: 275 pruebas, 4 fallas (3 preexistentes + 1 ambiental por evidencia V3 7973), 0 errores. Versión 02 12.18.0 → 12.19.0. Sin commit/push. -->
**Estado:** ESTABLE PARA CONTINUIDAD TÉCNICA Y REFACTORIZACIÓN ESTRUCTURAL CERRADA. La consolidación documental está completada. Persisten brechas funcionales/técnicas y validaciones UAT pendientes. **Último cierre técnico: `1466f24` (2026-08-20)** — robustecimiento del Core de perfiles de ingesta; el frente sigue **abierto en continuidad** aunque el técnico esté validado. Programación 1 (R1 — identificación operativa de lotes) queda implementada, desplegada en `madenat_test` y validada técnicamente; retoma en §13. La **Gestión Operativa de Etiquetas SV** queda implementada y validada (56 pruebas, 0 fallas, 0 errores) con retoma en §14.

---

## 1. Propósito

Este documento es el checkpoint técnico vivo del proyecto.
Debe permitir retomar el trabajo sin reconstruir el contexto desde cero.

---

## 2. Estado actual resumido

> **Fuente de verdad operativa:** `CANON/13_CONSOLIDACION_OPERATIVA.md` es la referencia canónica para flujos Producto/Procesados, stock, bajas, genealogía, trazabilidad, brechas (BT-01..BT-05) y pendientes UAT.

### Infraestructura
- Módulo: `madenat_lumber_core`.
- Target: Odoo 18 CE.
- Ambiente: Docker en WSL (`odoo18_app`, `db`).
- Arquitectura: modular parcial.
- **Puerta única de ingreso:** `madenat_lumber_intake` (menú `Ingreso de Madera`) es la única puerta visible para Operaciones. Es una fachada/orquestador que NO reemplaza parsers, NO duplica Gates y NO modifica lógica del core.

### Ingreso de Madera (`madenat_lumber_intake`) — reglas vigentes (AD-51)
1. **Puerta única visible:** Producto y Procesado se cargan desde `Ingreso de Madera`; el wizard deriva a `lumber.reception` (Producto) o `madenat.guia.processing` (Procesado).
2. **Dos dominios de parseo deliberados:** Producto usa `madenat.reception.parser.parse_excel()` solo como preview y delega a `lumber.reception.action_process_documents()` (Gate0/Gate1 nativos). Procesado entrega el Excel original crudo a `madenat.guia.processing.action_verify_data()`.
3. **Prohibición para Procesados:** no usar `parse_excel()` de Recepción ni `force_packing_data` (riesgo de perder filas huérfanas/forward-fill de `N° LOTE`).
4. **Volumen:** Intake no recalcula ni altera el M3 fuente; conserva el archivo/valor declarado por el proveedor.
5. **Auditoría de origen:** cada derivación exitosa genera exactamente un evento en `madenat.audit.log` (reutilizando contrato existente: `action_type='creation'`, `batch_id='intake:<wizard_id>'`), sin duplicar firmas ni guardar binarios.
6. **Riesgo residual documentado:** un mismo `N° LOTE` + `Código Interno` en varias filas puede causar overwrite en `_create_or_get_lot`; queda fuera de alcance de intake (ver AD-51).

### Política de precisión (vigente)
- **3 decimales** para campos volumétricos y dimensionales (`digits=(16, 3)`), conforme a correo Mauricio Navarrete 30-10-2025 y consistente con `utils_uom.r3` / `03_TESTS` T28. No es una política pendiente. La mención de "2 decimales" solo aplica a visualización de porcentaje de varianza, no a precisión volumétrica.

### Genealogía de trazabilidad (existente)
- La genealogía padre-hijo (`parent_lot_id` / `child_lot_ids` / `generation_level`, arquitectura Odoo estándar One2many/Many2one) es una **capacidad técnica existente**. Su validación operacional con datos de prueba **permanece pendiente** (no confundir con UAT ejecutada).

### Documentación (post-auditoría forense 2026-07-01)
- **Auditoría forense completa ejecutada** sobre TODO `custom_addons/` contra `madenat_lumber_docs/` como fuente canónica única.
- **CANON/INDICE_DOCUMENTACION.md v10.0.0:** 19 documentos CANON indexados. Versión de `02_CONTINUIDAD.md` corregida (8.1.0→9.0.0 match real).
- **WIKI/00_INDICE.md v2.0.0:** ~60 documentos WIKI indexados.
- **AD-26 ejecutado:** 33 archivos `.bak` removidos de módulos productivos → `LEGADO/backups_modulos/`.
- **Backup de módulo movido:** `madenat_lumber_core/backups/fase1_20260602_211431/` → `LEGADO/backups_modulos/`.
- **CHANGELOG cerrado:** `[Unreleased]` → `18.0.5.4.0` (fix UserError stock.moves, 2026-07-01).
- **Prueba de humo:** 86 módulos cargados en 4.71s, 0 errores, registry OK.
- **Punto de entrada:** `CANON/INDICE_DOCUMENTACION.md` → único mapa maestro.

### Verdad Funcional (Código)
1. **Naming de Largo:** Implementado vía `lengthinputraw` (preserva entrada) y `lengthuom` (unidad).
2. **Fuente de Verdad:** El campo `length` es la base normalizada en metros para todos los cálculos volumétricos.
3. **UI:** Estándar Odoo 18 verificado (uso de etiquetas `<list>` y componente `<chatter/>`).
4. **Registry:** El módulo instala y actualiza sin errores. El incidente de `@api.depends` está resuelto.
5. **Fix de Blanks (2026-06-02):** Corregido y validado en local. Ajuste volumétrico para blanks clear en `stock_lot.py` y `madenat_guia_processing.py` que evita la aplicación indebida del ajuste S2S en blanks. Ver AD-27.

---

## 3. Prioridades Actuales (2026-08-15)  <!-- actualizado: 2026-08-15 — según CANON/13 -->

1. ~~**BT-02:** Impedir sobrescritura/reutilización de lote notarizado o histórico~~ → **CERRADO (2026-08-16)**: `_create_or_get_lot()` en `madenat_guia_processing.py` excluye lotes con `reception_id` en la búsqueda inicial y en el fallback posterior a `IntegrityError` (`('reception_id', '=', False)`). Ver CHANGELOG 18.0.5.10.0.
2. ~~**BT-01:** Asegurar que todo write path hacia `stock.lot` cumpla Gate 3 y auditoría~~ → **CERRADO (2026-08-16)**: `action_validate()` firma snapshot SHA-256 (`Gate3PreCommit.generate_processing_signature`) antes del primer write a `stock.lot` y persiste un evento inmutable en `madenat.audit.log` (`guia_processing_id`, `audit_snapshot`, `audit_hash`, `action_type='validation_signature'`). Ver CHANGELOG 18.0.5.10.0.
3. ~~**BT-04:** Implementar y probar baja documentada de producto enviado a proceso~~ → **CERRADO (2026-08-16)**: salida controlada a `Virtual Locations/Production` solo para `service` (`_get_or_create_consumption_picking`), idempotente vía `consumption_picking_id`, reversible sin borrar historia (`_reverse_consumption_picking`), con evento `consumption` en `madenat.audit.log`. `compra` intacto. Ver CHANGELOG 18.0.5.11.0.
4. ~~**BT-03:** Extender bitácora de auditoría (`madenat.audit.log`) al flujo de procesados~~ → **CERRADO (2026-08-16)**: `lot_creation`/`lot_update`/`omission` enlazados a `guia_processing_id`. Ver CHANGELOG 18.0.5.10.0.
5. **UAT end-to-end** de Producto y Procesados (PASO 2).
6. ~~Confirmación de negocio de `deduction_factor = 0.0625` para Blank~~ → **CONFIRMADO por evidencia Excel** (tarjas MSC VIRGO `= (esp−1/16)×(ancho+1/8)×largo_ft×pzas/5085.312`).
7. **BT-05:** Parseo disperso de guías procesadas — abordar después de los controles de integridad (BT-01..BT-04).

*Las prioridades históricas (Fase C/D, deploy) permanecen como antecedente; el orden vigente lo fija `CANON/13`.*

---

## 4. Punto de retoma — 2026-07-06  <!-- actualizado: 2026-07-06 -->

**Último commit conocido:** e6a1fc1 — refactor(cleanup): consolidar reception_service hacia savepoint validado por tests A/B
**Rama:** main
**Checkpoint rollback:** d597703 (pre-consolidación, Tests A y B aprobados)
**Estado:** Fase 3 completada y validada. Consolidación de `reception_service.cleanup_orphan_moves()` hacia savepoint + force_delete aplicada. Estrategia de unlink homogeneizada entre ambos métodos sobrevivientes. Tests A y B pasando (0 failed, 0 error(s)). Auditoría documentada en `AUDITORIA_ASIMETRIA_DOCUMENTAL_20260706.md` secciones X, Y, Z, W. AD-39 actualizado con cierre funcional.
**Pendiente:** Auditoría documental canónica y revisión de deuda residual. Próximo sprint enfocado en documentación/continuidad, no en refactor funcional.
**Retomar desde e6a1fc1 con revisión documental canónica y pendientes residuales de auditoría; no reabrir refactors cerrados salvo hallazgo nuevo.**

### Cerrado en sesión 10-06-2026
- HOTFIX UX — Pestaña Comercial f5085: `thickness_visual` como columna principal, `thickness_nominal_frac` como opcional. Solo XML (lumber_reception_views.xml L372-380), 0 Python. Trazabilidad preservada vía columna opcional. Ver CHANGELOG.md.

### Cerrado en sesión 09-06-2026
- C1: Menú raíz renombrado "📥 Ingreso de Guías Dentro de Recepción" ✅
- _compute_visual_defaults para Blank (f5085): confirmado correcto, no requirió cambios ✅
- Diagnóstico completo flujos S2S vs Blank completado ✅
- SSH cuenta viruco configurado permanentemente en WSL2 ✅
- C2: Selector tipo producto operativo con labels (Madera Aserrada / Blank) ✅ — commit c6d8812 + 0cda416
- C3 (parcial): Reglas mapeo nominal 6/4, 5/4, 7/4, 8/4 en thickness_visual_ranges ✅ — commit 5732fd5
- C4: Restricción documental Packing/Guía por tipo producto ✅ — commit 0cda416
- C1 (bis): Eliminación IDs duplicados menu_remapping.xml + reorden Reportes (sequence 45) ✅ — commit 1438bb5

### Cerrado en sesión 11-06-2026
- Fix thickness_visual 6/4: max_thickness 42→46mm, 7/4 min_thickness 42→46mm ✅ — commit 3252c7e
- Migración 18.0.5.1.0 para thickness_visual 6/4 ✅ — commit 52ec1c7
- INC-010 + DEC-006 documentados ✅ — commit 7b3665f

### Cerrado en sesión 13-06-2026
- Fix R7 OC column y PDF footer colspan ✅ — commit 99545d9
- Fix R7/R8 group_by con purchase_order desde core ✅ — commit 3ba43575

### Nuevos features en staging (pendiente validación)  <!-- actualizado: 2026-06-16 -->
- Kanban, dashboards, wizard period_close, búsqueda OC — commit 8ce578b
- stock_landed_cost override y tests costing — commit 81c3373
- Restauración visibilidad PDF+Excel en todos los perfiles — commit 4372dec

### Bloqueado — esperando Cristhian  <!-- actualizado: 2026-08-15 — RESUELTO por evidencia Excel -->
- C3: `deduction_factor=0.0625` para blank_clear → **CONFIRMADO** por evidencia operativa primaria: el Excel `LISTADO Y TARJAS MN MSC VIRGO FA610R.xlsx` aplica `(espesor−1/16)×(ancho+1/8)×largo_ft×pzas/5085.312`, coincidiendo con código y configuración. Ya no es un bloqueo; solo queda alinear el test T13.

### Pendiente activo (próxima sesión)  <!-- actualizado: 2026-06-16 -->
- Máquina remota de test: validar commit 3ba43575 en staging
- Validar nuevos features (kanban, dashboards, period_close, landed_cost) en staging
- Auditoría documental canónica completada — ver INDICE_DOCUMENTACION.md para estado

### Contexto clave descubierto
- Flujo S2S: puede modificar nominal comercial, aplica f1550, recargo +1/8"
- Flujo Blank: producto final de compra, no sufre transformación nominal,
  solo conversión de unidades (pies→m), factor f5085 (5085.312)
- _compute_visual_defaults ya separa correctamente ambos mundos (línea 481)
- `deduction_factor=0.0625` en seed: **confirmado** por la "planilla real" (Excel MSC VIRGO). Ya no está sujeto a confirmación de negocio; solo queda la alineación del test T13 (fuera de esta tarea).

---

## 5. Riesgos activos

| Riesgo | Severidad | Estado |
|---|---|---|
| **BT-02** — Sobrescritura de lote notarizado (`_create_or_get_lot` limpia `reception_id`) | ~~Crítica~~ | ~~ABIERTO~~ **CERRADO (2026-08-16)** — `_create_or_get_lot()` excluye `reception_id`; ver CHANGELOG 18.0.5.10.0 |
| **BT-01** — Segundo write path a `stock.lot` sin Gate 3 ni auditoría | ~~Alta~~ | ~~ABIERTO~~ **CERRADO (2026-08-16)** — firma SHA-256 + bitácora `madenat.audit.log` vinculada a guía; ver CHANGELOG 18.0.5.10.0 |
| **BT-04** — Baja de producto enviado a proceso sin implementación | ~~Alta~~ | ~~ABIERTO~~ **CERRADO (2026-08-16)** — salida controlada solo `service` (idempotente y reversible); ver CHANGELOG 18.0.5.11.0 |
| **BT-03** — Bitácora `madenat.audit.log` sin cobertura de procesados | ~~Media~~ | ~~ABIERTO~~ **CERRADO (2026-08-16)** — `lot_creation`/`lot_update`/`omission` enlazados a guía; ver CHANGELOG 18.0.5.10.0 |
| **BT-05** — Parseo disperso en `madenat_guia_processing.py` (sin dispatcher) | Media | ABIERTO — posterior a integridad |
| `madenat_ingestion_engine` — módulo instalado con consumidor activo (`madenat_lumber_intake`) pero sin trazabilidad CANON/git; extracción PDF limitada a cabecera (tablas con layout configurable NO cubiertas) y `ingestion_column_profile.py` esqueleto | Media | ABIERTO — diagnóstico AD-63 (2026-09-12) |
| Costeo nativo desactivado (productos `consu`, sin método de costeo) + `wood_cost_usd` total sin prorrateo por consumo parcial de lote | Alta | ABIERTO — diagnóstico AD-64 (2026-09-12) |
| Recepción a granel + Balance de Masa + Consolidación administrativa | Alta | DISEÑO APROBADO, IMPLEMENTACIÓN PENDIENTE — AD-65 (2026-09-12) |
| Constraint `stock_lot_check_cost_positive` | Alta | ABIERTO (histórico) |
| Monolito parcial en `lumber_reception.py` (3,054 líneas, 5 responsabilidades, parseo desacoplado en reception_parser.py) | Media | ABIERTO (histórico) |
| Tolerancias no formalizadas | Media | ABIERTO (histórico) |
| T29–T32 sin evidencia formal | Media | PENDIENTE (no bloqueante para TEST) |

**Nota (2026-08-15):** Los riesgos BT-01..BT-05 provienen de `CANON/13_CONSOLIDACION_OPERATIVA.md` y son los frentes activos. Los riesgos históricos se conservan como referencia.

**Nota (2026-07-08):** La lógica de negocio S2S vs Blank está correctamente aislada en `_compute_vol_shipment_m3` (L476-538, bifurcación en L510-516) y NO debe tocarse ni fusionarse en ninguna intervención futura sobre el parseo disperso de `madenat_guia_processing.py`.

**Nota (2026-07-08):** Primer piloto de estrangulamiento incremental completado (AD-41, `_parse_fraction` → `utils_uom.py`). Validado con 12 tests unitarios, 0 impacto en negocio. Candidato para segundo piloto: `_parse_float_value` (11 callers, Categoría B — requiere evaluación de heurísticas de dominio antes de extraer, ver auditoría 2026-07-08).

---

## 6. AD-41 — CICLO DE ESTABILIDAD CERRADO (2026-07-08)

**Veredicto:** ESTABLE — habilitado inicio del segundo piloto (`_parse_float_value`).

### PASO 1 — Smoke test de arranque ✅
- `docker compose up -d`: containers healthy, registry cargado en 2.88s
- 86 módulos, 0 errores de parseo, 0 tracebacks relacionados con utils_uom/stock_lot/madenat_guia_processing
- `utils_uom` startup validations: MBF_TO_M3=2.36, factor imperial 1550.003, S2S_WIDTH_LOOKUP=16

### PASO 2 — Flujo end-to-end ⏸️
- Pendiente: requiere operador (Mauricio/Cristhian) para ejecutar recepción f5085 (Blank), recepción f1550 (S2S), y guía processing con fracciones imperiales en UI
- BD staging tiene 9 recepciones y 2 guías de datos históricos — disponibles para comparación post-ejecución

### PASO 3 — Verificación stock_lot.py ✅
- Wrapper `_parse_fraction_to_decimal` (L1136) delega correctamente en `parse_fraction_to_decimal_inch`
- 6 call sites activos: L893, L899, L906, L1150, L1151, L1153
- Datos existentes en BD: 15 lots muestreados con fracciones como "6/4", "4 5/8", "5 3/8", "3 5/8", "4 7/8", "2 5/8", "4 3/8" — todos con `volumen_mbf` y `vol_shipment_m3` coherentes
- 10 tests funcionales pasando: fracciones puras, números mixtos, vacío, "6/4", "5 5/8"

### PASO 4 — Ventana de observación ⏸️
- No iniciada formalmente. Se recomienda iniciar tras completar PASO 2.

### Decisión
AD-41 se declara ESTABLE a nivel de código. El wrapper en `stock_lot.py` funciona correctamente con datos reales. No se detectaron regresiones ni anomalías de parseo.

**Próxima sesión:** Iniciar segundo piloto (`_parse_float_value`), previa validación de PASO 2 end-to-end por operador.

---

## 7. AD-41 → AD-46: CICLO DE ESTABILIZACIÓN ESTRUCTURAL CERRADO (2026-07-08)

**Veredicto:** Ciclo de estabilización estructural cerrado. Los resultados de tests de esta etapa **no sustituyen la validación UAT funcional**, que permanece pendiente para los flujos de Producto y Procesados.

### Línea de tiempo

| AD | Acción | Impacto |
|----|--------|---------|
| AD-41 | `_parse_fraction` → `parse_fraction_to_decimal_inch` en `utils_uom.py` | +65 líneas, 12 call sites, 0 regresiones |
| AD-42 | `_parse_float_value` → `parse_float_value` en `utils_uom.py` | +53 líneas, 11 call sites, 0 regresiones |
| AD-43 | `_get_fraction_text` unificado → `decimal_inch_to_fraction_simple(value, denominator, tolerance)` | +55 líneas, elimina 2 copias divergentes, 0 regresiones |
| AD-44 | `_normalize_oc_key` unificado → `normalize_oc_key` en `utils_uom.py` | +16 líneas, elimina duplicación exacta, 0 regresiones |
| AD-45 | Eliminación quirúrgica de 6 métodos muertos | -62 líneas, 0 callers afectados |
| AD-46 | Validación end-to-end con 119 lots reales | **35/35 tests pasando**, 0 regresiones |

### Estado final de `utils_uom.py`

| Función | Origen | Propósito |
|---------|--------|-----------|
| `parse_fraction_to_decimal_inch` | AD-41 | Fracción imperial → decimal |
| `parse_float_value` | AD-42 | Texto sucio → float (CLP, mm) |
| `decimal_inch_to_fraction_simple` | AD-43 | Decimal → fracción (base-8 o base-16) |
| `normalize_oc_key` | AD-44 | Referencia OC → clave normalizada |

### Wrappers de compatibilidad preservados (5)

| Archivo | Wrapper | Delega en |
|---------|---------|-----------|
| `madenat_guia_processing.py` | `_parse_float_value` | `parse_float_value` |
| `madenat_guia_processing.py` | `_get_fraction_text` | `decimal_inch_to_fraction_simple(8, 0.05)` |
| `madenat_guia_processing.py` | `_normalize_oc_key` | `normalize_oc_key` |
| `lumber_reception.py` | `_get_fraction_text` | `decimal_inch_to_fraction_simple(16, None)` |
| `lumber_reception.py` | `_normalize_oc_key` | `normalize_oc_key` |

### Lo que NO se tocó (y por qué)

- **Duplicaciones parciales** (`_parse_smart_dimension` vs `parse_fraction_to_decimal_inch`, `_canonize_*`): reglas de negocio distintas, alto riesgo de regresión sin datos reales
- **Métodos ORM** (`_calculate_fractional_approximation`, `_get_nominal_dimension`): dependen de `self.env`, no son funciones puras

### Decisión de pausa

La etapa de consolidación estructural se cierra aquí. El sistema quedó con:
- 4 funciones puras concentradas en `utils_uom.py`
- 5 wrappers que preservan compatibilidad
- 62 líneas de código muerto eliminadas
- 0 regresiones funcionales detectadas (35/35 tests)

**Próximo paso:** El siguiente avance debe ser funcional u operativo, no estructural. Cualquier nuevo piloto deberá justificarse por una necesidad real detectada en producción.

---

## 8. `madenat_lumber_intake` — Puerta única y cabina previa a stock (2026-08-16)

**Hecho:** `madenat_lumber_intake` es la puerta única de ingreso global de MADENAT.
Unifica visualmente en una sola bandeja los ingresos de `lumber.reception`
(Producto) y `madenat.guia.processing` (Procesado), para que el operador revise
información, evidencia documental y estado operativo antes de enviarlos a stock.

- **Consola:** `madenat.lumber.intake.console`, fachada readonly sobre una vista SQL consolidada; no duplica ni persiste datos de negocio.
- **Validación previa:** la consola funciona como cabina de revisión; el envío a stock delega en `action_confirm_reception()` o `action_validate()` según el modelo origen.
- **No reemplaza ni reescribe** `lumber_reception.py` ni `madenat_guia_processing.py`, ni crea modelos paralelos de `stock.lot`, `stock.picking` o `stock.move`.
- **Wizard:** crea y enruta el ingreso hacia el modelo origen correspondiente, manteniendo la lógica de parsing, Gates y validación en el core.
- **Auditoría:** cada derivación exitosa registra el origen en `madenat.audit.log` con `action_type='creation'` y `batch_id='intake:<wizard_id>'`.

La documentación técnica detallada de la consola, la vista SQL y el flujo end-to-end
se mantiene en `custom_addons/madenat_lumber_intake/README.md`.

### Fachada de Producto (Intake)

- **Fachada ligera:** la fachada de Producto (`view_lumber_reception_intake_facade_form`) expone bloque "Orden de Compra" con `purchase_id`, `oc_reference_raw`, `manual_po_name`, `oc_match_status` y `oc_match_note` en readonly, sin reemplazar el form XXL del core.
- **Estado legible de OC:** el campo `oc_pending` de la consola es `Selection` con estados `linked` ("OC vinculada") y `pending` ("Pendiente de vinculación"), renderizado como badge con `decoration-success`/`decoration-warning`. Fuente de verdad: `purchase_id`.
- **Alerts informativas (no bloqueantes):**
  - `oc_pending_alert` (Html computado): alerta persistente cuando `purchase_id` está vacío y existen referencia documental, referencia manual o multi_match.
  - `supplier_pending_alert` (Html computado): alerta persistente cuando `supplier_id` está vacío.
- **Wizards de resolución:**
  - `madenat.lumber.intake.po.link` — asocia una `purchase.order` existente (validación server-side AD-52).
  - `madenat.lumber.intake.supplier.link` — valida/corrige `supplier_id` seleccionando un partner existente (sin crear proveedores).

**Política de OC pendiente (AD-52):**
- La OC pendiente **no bloquea** la ingesta preliminar ni el envío operativo inicial a stock.
- Operaciones puede revisar proveedor y resolver una OC existente cuando corresponda.
- La exigencia final de OC resuelta pertenece a **Costeo y Valorización / cierre financiero**, no a Operaciones.
- No se crea una OC automáticamente ni se inventan proveedores/productos/precios.

---

## 9. Diferencia intencional: Política de OC en Procesados vs Producto (AD-53)

**Procesados (core) — estado histórico previo a AD-54, superado el 2026-08-19:**
- Anteriormente `madenat.guia.processing.action_validate()` bloqueaba el envío a stock con `UserError` si existía `oc_reference_raw` (referencia documental detectada) y `order_id` (OC real vinculada) estaba vacío. AD-54 sustituyó ese bloqueo por una advertencia no bloqueante con registro en chatter.
- Evidencia histórica: `madenat_guia_processing.py:1552-1559` (y `:1420-1427` en `action_process_from_staging`).
- Mensaje operativo histórico: "Debe vincular una orden de compra válida antes de procesar" (referencia a botón "Crear/Vincular OC").
- La UI de Procesados ofrece el botón **"📄 Crear OC desde PDF"** (`action_create_purchase_order_from_document`), que crea una `purchase.order` en `draft` (no confirmada) con trazabilidad documental, sin crear líneas de compra ni tocar `madenat_lumber_purchasing`.

**Producto (Intake) — comportamiento real (AD-52):**
- La OC pendiente **no bloquea** la ingesta preliminar ni el envío operativo inicial a stock.
- La exigencia final de OC resuelta pertenece a Costeo/Valorización/cierre financiero.
- La vinculación manual de OC en Intake valida en servidor: proveedor obligatorio, `partner_id` de OC, `commercial_partner_id`, compañía, estado de OC, estado de recepción y no-sobrescritura silenciosa (AD-52).

**Conclusión de la diferencia — RESUELTA y COMPLETA por AD-54 (ampliado 2026-08-19):**
- La diferencia de política de OC entre Procesados y Producto fue **resuelta** mediante AD-54: se autoriza de forma puntual eliminar el bloqueo de OC en **ambos métodos** de `madenat.guia.processing`:
  - `action_validate()` (evidencia `madenat_guia_processing.py:1552-1559`) — validación final.
  - `action_process_from_staging()` (evidencia `madenat_guia_processing.py:1420-1427`) — etapa de borrador/staging previa.
  Ambos pasaron de `raise UserError` a **advertencia no bloqueante** (`_logger.warning` + `message_post`).
- **La homologación Producto/Procesados ahora es COMPLETA en ambas etapas** (staging y validación final): ambos modos comparten la política **"OC pendiente no bloquea"** la ingesta ni el envío a stock.
- AD-53 queda **superado** por AD-54 en cuanto a la diferencia de bloqueo; se conserva como referencia histórica.
- La excepción sigue siendo **puntual y autorizada explícitamente** (ahora sobre dos métodos específicos, no general); NO constituye precedente. La regla general de no modificar `madenat_lumber_core` sigue vigente para cualquier otro caso.
- `action_validate` conserva TODAS sus demás validaciones (nominales, subproductos, tipo de cambio, notarización BT-01) intactas; solo se removió el bloqueo específico de OC.
- La exigencia final de OC resuelta continúa perteneciendo exclusivamente a **Costeo/Valorización/cierre financiero**.

---

## 10. Homologación UX — "Modificar origen" (AD-55)

- **Implementación (2026-08-19, alineada al código actual):** la fachada ligera de Procesados (`view_madenat_guia_processing_intake_facade_form`) está implementada y operativa en `madenat_lumber_intake`. Detalles:
  - **Tabs visibles:** `Guía y comercial`, `Proceso`, `Packing` (renombrado desde `Detalle`). **No se expone `Trazabilidad`** en la fachada.
  - **Acciones visibles:** `Verificar Datos` (`action_verify_data`), `Volver a Ingreso de Madera` (`action_back_to_intake_console`), `⚡ Fijar Nominal Masivo` (acción window del core reutilizada). El **envío a stock queda centralizado en la consola** (`action_send_to_stock`), no en la fachada.
  - **Retorno:** `action_back_to_intake_console` abre el **registro concreto del hub** `madenat.lumber.intake.console` en vista form (`res_id=900000000+self.id`, `view_madenat_lumber_intake_console_form`), replicando el patrón de Producto. No abre lista filtrada.
- **Estado del frente:** implementado y alineado al código actual; **sujeto a validación funcional continua** (no se declara cerrado el frente Procesados/Intake).
- **Referencia:** `04_DECISION_LOG.md` AD-55 (implementación).

---

## 11. Cierre técnico 2026-08-20 — `1466f24 fix(core): restore ingestion profile safeguards and blanks catalog`

**Contexto:** Commit técnico `1466f24` cierra un ciclo de robustecimiento del Core de perfiles de ingesta. Fundamentado en auditoría de solo lectura (evidencia completa en `INDICE_DOCUMENTACION.md` / RAW 2026-08-20). Complementa los commits documentales previos `634cf76` (fachada Intake + política OC), `5f1048d` (edición de origen Procesados en Intake) y `699552a` (higiene Git).

### Estado tras el cierre técnico
- **Intake + Procesados reforzados:** `madenat.guia.processing` ahora tiene `ingestion_profile` (values idénticos a `lumber.reception`), reactivando el candado anti-mezcla comercial de `madenat_guia_mass_update` que antes era código muerto (`hasattr` siempre `False`). Existe cobertura de tests para existencia/default, bloqueo/permiso por perfil.
- **Catálogo `blanks` completado:** `lumber.blank.nominal.map`, `lumber.profile.subproduct.rule`, `lumber.export.formula` y `lumber.thickness.visual.rule` aceptan ahora `blanks`. El fallback ya no es silencioso: `lumber_export_formula._resolve_for_profile('blanks')` resuelve **intencionalmente** a la ruta S2S/imperial definida por el dominio (el parser mapea blanks → `export_rule_outcome='f1550'`), **no** a `metric`. Decisión documentada en código y probada.
- **Labels estandarizados:** se renombraron los labels visibles de los Selection (`f5085→'Madera Bruta — Grado Clear'`, `f1550→'Madera Aserrada S2S'`, `blanks→'Blanks — Legado (métrico/imperial híbrido)'`, `metric→'Madera Bruta — Sistema Métrico'`; `ingestion_profile` de recepción/guía con emojis conservados) **sin tocar values técnicos** — solo texto de UI, sin migración de datos. Objetivo: reducir confusión operativa.
- **Cobertura de tests:** clases `TestGuiaProcessingIngestionProfileLock` (5) y `TestBlankProfileCatalogComplete` (6) añadidas a `test_guia_processing.py`. Suite `madenat` **49/49 tests, 0 fallos, 0 errores** ejecutada sobre `madenat_test`.

### Limitación conocida diferida (deuda técnica explícita)
- **`origin_scope` pendiente:** el catálogo `lumber.profile.subproduct.rule` sigue indexado solo por `profile`, sin distinguir si la regla aplica a Producto (`lumber.reception`) o Procesados (`madenat.guia.processing`). Ambos flujos comparten el mismo universo de reglas por perfil. **No se implementó** la diferenciación por origen (campo `origin_scope` propagado vía `with_context` desde los wizards de origen) — queda como limitación conocida y pendiente, documentada en el encabezado del modelo y en `04_DECISION_LOG.md` AD-56.

**Retoma:** el frente sigue **abierto en continuidad**. El técnico está validado; quedan pendientes UAT end-to-end (CANON/13) y la decisión futura de `origin_scope`. No reabrir refactors cerrados salvo hallazgo nuevo.

---

## 12. Ingreso por Volúmenes — estado y retoma (2026-09-22)

### 12.1 Estado implementado
- **Tercera modalidad de ingreso:** `tipo_ingreso='granel'` del wizard ("Madera a granel / volumen total") → consola `ingestion_type='volume'` ("Ingreso por Volúmenes"). No es una cuarta modalidad. Producto y Procesado no se modifican.
- **Fuente documental:** PDF/Guía principal validada; Excel Packing List opcional. La ausencia de Excel no bloquea lectura documental, preview ni continuidad. Excel como única fuente queda **pendiente de validación**.
- **Extracción documental:** genérica y por estructura (no por proveedor/RUT/fixture): número de guía, fecha, proveedor documental + RUT, receptor + RUT, OC, pedido/origen, tipo de cambio, paquetes/piezas/importes/totales, volumen total y detalle de líneas cuando la tabla es reconstruible.
- **Volumen y detalle:** volumen PDF/documental, suma de detalle, volumen previsto para stock, diferencia (warning no bloqueante) y fuente. Sin cubicación geométrica (no se usa espesor/ancho/largo/piezas). Normalización de separadores decimales.
- **Detalle persistente:** `madenat.lumber.volume.detail.line` (documental y editable; fallback consolidado con warning; evidencia original conservada).
- **Proveedor documental vs partner asociado:** `supplier_name`/`supplier_rut`/`supplier_source`/`supplier_confidence` + `supplier_resolution_status` (incluye `resolved_manual`). Asignación manual vía wizard reutilizado `madenat.lumber.intake.supplier.link` + botón "Asignar proveedor" en consola. No bloquea el ingreso.
- **Consola:** `madenat.lumber.intake.console` es una vista SQL readonly (`_auto=False`); toda modificación se hace por ORM sobre el registro origen (`madenat.guia.processing`).

### 12.2 Retoma (próxima sesión)
1. Reejecutar `madenat_lumber_core` por ruta/clase (la ejecución por tags devolvió 0 tests por descubrimiento del entorno).
2. Validar **Excel sin PDF** como fuente única (escenario pendiente de prueba explícita).
3. Definir la regla final de **rebaja/registro físico de stock por Volúmenes** (siguiente hito; NO cerrado en este cambio).
4. Validar en producción la resolución de partner por nombre sin RUT y las etiquetas "Transporte" en membrete.

### 12.3 Validación conocida
- `madenat_lumber_intake`: **141 tests, 0 fallos, 0 errores** (incluye asignación manual: apertura de wizard, persistencia `resolved_manual` y chatter).
- `madenat_ingestion_engine`: **55 tests, 0 fallos** (incluye `test_pdf_parties`).
- `madenat_lumber_core`: ejecución por tags devolvió 0 tests; **pendiente de reejecución** por ruta/clase.

---

## 13. Programación 1 — R1: identificación operativa y trazabilidad visible de lotes (2026-09-25)

### 13.1 Estado implementado
- **Capa de presentación en R1:** cinco campos compute almacenados en `stock.quant`
  (`madenat_lumber_reports/models/lumber_stock_report.py`): `lot_operational_label`,
  `is_volume_lot`, `lot_entry_datetime`, `lot_entry_datetime_source`, `lot_origin_document`.
  Decisión canónica: `04_DECISION_LOG.md` AD-77; inventario de campos en `00_ARQUITECTURA.md` §4.7.
- **Nomenclatura:** el token técnico inicial `GRANEL` (nombre exacto `GRANEL` o prefijo `GRANEL `)
  identifica lote de volumen y se presenta como `Lote Volumen`. No se modificó `stock.lot.name`,
  `display_name`, `name_get` ni `name_search`.
- **Filtro técnico:** `Lotes Volumen` en la search view de R1 usa `[('is_volume_lot', '=', True)]`,
  no la etiqueta visible.
- **Sin cambios de inventario:** no se alteraron cantidades, quants, movimientos, recepciones ni
  guías.

### 13.2 Evidencia
- Upgrade de `madenat_lumber_reports` a `18.0.2.3.0` sobre `madenat_test` (solo ese módulo): código de
  salida `0`; log preservado en `/tmp/upgrade_madenat_lumber_reports_18_0_2_3_0.log` durante la sesión.
- Cinco columnas verificadas en `stock_quant`.
- Caso histórico verificado por consulta de solo lectura:

  ```text
  stock.lot(3753)
  Técnico: GRANEL 4495589
  Operativo: Lote Volumen 4495589
  is_volume_lot: true
  saldo: 0,000
  ```

### 13.3 Limitación de evidencia
- No existían lotes por volumen con cantidad positiva en ubicación interna.
- Por tanto, **queda pendiente la validación visual completa de R1 y del filtro `Lotes Volumen`** con
  una futura recepción/lote real, sin crear stock artificial. Programación 1 **no** se declara
  validada visualmente en R1.

### 13.4 Retoma
1. Validar R1 con el próximo Lote Volumen con saldo positivo.
2. Resolver el alcance de las exportaciones XLSX (hoy muestran el nombre técnico del lote).
3. Añadir test automatizado del token técnico, la etiqueta operativa y `is_volume_lot`.
4. Diseño de la rebaja controlada por volumen: **implementado** para Etiquetas SV (ver §14); la rebaja/registro físico de stock por Volúmenes fuera del flujo SV permanece sin implementar.

---

## 14. Gestión Operativa de Etiquetas SV — Estado de continuidad (2026-09-26)

### 14.1 Estado

- **Implementado y validado** en `madenat_test` (decisión y alcance en
  `04_DECISION_LOG.md` AD-79; arquitectura en `00_ARQUITECTURA.md` §4.8).
- Gestión SV: **56 pruebas, 0 fallas, 0 errores** (`03_TESTS.md` §9).
- Se mantiene la protección de datos históricos: no se modificaron Guía 4495589,
  SV00000000008, movimientos, pickings, quants, costos, facturas, consolidaciones ni la
  secuencia `madenat.volume.lot`.

### 14.2 Capacidades verificadas

- Renombre controlado de etiqueta con **alias histórico no reutilizable**.
- **Regularización documental** de volumen (baseline vigente) sin efecto retroactivo sobre stock,
  costos, valoración o facturas.
- **Rebaja** de volumen/piezas contra saldo disponible y **reversa** como evento opuesto enlazado.
- **Historial** persistente append-only (`madenat.sv.operation`) con snapshot y firma SHA-256,
  espejo en chatter y `madenat.audit.log`.
- **Escalamiento condicional**: Auditoría en alza de baseline documental; Contabilidad con costo,
  valoración, factura, consolidación facturada/cerrada o período cerrado.
- **Concurrencia fail-closed**: bloqueo transaccional, recálculo de saldo, rechazo del intento
  conflictivo sin saldo negativo ni registros parciales, con mensaje funcional al usuario.
- **Reversa de recepción por lote SV específico** (la devolución de una Guía de Volumen usa
  exclusivamente su lote SV).
- **Integración logística**: la asignación a contenedor/embarque registra rebaja explícita y su
  liberación genera reversa trazable.

### 14.3 Caso histórico conservado (no modificado)

- Guía `4495589` (`madenat.guia.processing` 6566) e identificación `SV00000000008`
  (`stock.lot` 3772).
- Volumen oficial PDF: **40,315 m³**; histórico operativo/detalle: **40,300 m³**;
  diferencia documental **0,015 m³**.
- La implementación de Gestión SV **no** modificó esos registros: `write_date` de la Guía
  (2026-09-25 18:13:59) y del lote (2026-09-26 06:14:57) son anteriores a las corridas SV, el
  lote no tiene marca de serialización SV ni operaciones SV asociadas, y la secuencia sigue en
  `number_next = 1`.
- Cualquier corrección futura debe ejecutarse como **operación SV formal con motivo y evidencia**
  (regularización documental); nunca por edición directa. No se ha ejecutado ninguna migración ni
  regularización histórica.

### 14.4 Límites actuales

- Hasta **dos aprobadores explícitos** por operación; no existe motor genérico de tres o más
  niveles de aprobación.
- La asignación logística usa un **monto escalar por operación del asistente**, no un monto
  individual por cada etiqueta seleccionada en una misma acción.
- Un conflicto concurrente exige **recargar la información y reintentar manualmente**; no existe
  reintento automático silencioso.
- Deuda técnica T1–T6 (ajena al alcance SV) **cerrada el 2026-09-26**, con causas raíz verificadas en runtime
  y pruebas focalizadas 72/72 PASS en `madenat_test` (T6 verificado además con instalación limpia en base
  desechable). La documentación se actualizó en `05_BACKLOG.md` (T1–T7 y nueva deuda T8–T11),
  `03_TESTS.md` §9.7, `12_FLUJOS_INGESTA.md` §11.5, `13_CONSOLIDACION_OPERATIVA.md` §9 y
  `00_ARQUITECTURA.md` §3.4.

### 14.5 Retoma

1. Evaluar con negocio si se requiere monto por etiqueta en la asignación logística múltiple.
2. Evaluar con negocio la generalización de aprobaciones a más de dos niveles, si aplica.
3. Deuda nueva T8–T11 detectada en el cierre (`05_BACKLOG.md`): referencia `contacts.menu_contacts` en
   `madenat_lumber_core` que bloquea instalaciones limpias mínimas (T8), test de Billing sin etiqueta de fase
   y sin guard anti-duplicado implementado (T9), archivo muerto con XML ID duplicado en Logistics (T10) y VAT
   fijo colisionante en fixtures de Intake (T11).

---

## 15. Fase 2 — UX de volumen oficial, bloque SV visible y ciclo de vida de guías (2026-09-28, AD-80)

### 15.1 Estado

- **Implementado y validado** en `madenat_test`: `madenat_lumber_intake` 18.0.0.6.0 y
  `madenat_lumber_core` 18.0.6.3.0 (upgrade con código de salida 0).
- Decisión y alcance: `04_DECISION_LOG.md` AD-80; arquitectura de la Consola:
  `12_FLUJOS_INGESTA.md` §11.7; cobertura: `03_TESTS.md` §10.
- **Regla derogada:** la prohibición de acciones SV en la Consola queda **sin efecto**, sustituida
  por aserciones positivas de las acciones autorizadas (`test_volume_official_volume.py`).

### 15.2 Capacidades verificadas

- Jerarquía de volumen: bloque oficial único primario (`VOLUMEN OFICIAL DE LA GUÍA` con la
  leyenda «Gobierna stock, conciliación y consolidación.»), secundarios con las etiquetas
  aprobadas (`M³ declarado por Operaciones (referencia)`, «No gobierna stock ni reemplaza el
  volumen oficial.», `Volumen operativo de referencia (no gobierna stock)`) y detalle
  exclusivamente en `Control documental interno (auditoría)`. Sin agregado `Volumen:` en el
  encabezado para Volumen.
- Bloque `ETIQUETA SV Y SALDO OPERATIVO` con etiqueta, volumen original, regularizado, rebajado,
  saldo, piezas (solo con piezas documentales positivas) y advertencia documental; sin lote,
  solo el placeholder `Se asignará al enviar a stock.`
- Acciones SV autorizadas en Consola y Guía (modificar etiqueta, regularizar volumen, rebajar,
  reversar rebaja y ver historial), todas por delegación a los wizards y al ledger.
- Reversa: botón solo para la rebaja aplicada y reversible; la segunda reversa la bloquea el
  ledger.
- Ciclo de vida Modos A–D con auditoría firmada (`guia_delete_permanent`, `guia_purged`,
  `guia_delete_blocked`) y cero eliminación en el Modo D.

### 15.3 Límites actuales

- El Modo C exige estrictamente **cero registros de `stock.quant`** y **cero operaciones SV
  rechazadas** (no se eliminan registros de inventario y el ledger no permite borrar rechazadas);
  si aparecen, el caso pasa a Modo D.
- **Evidencia documental:** con cualquier `ir.attachment` (PDF/Excel), mensaje de chatter con
  contenido o referencia genérica persistente por `(res_model, res_id)` sobre la guía, la purga
  (Modo C) y la eliminación definitiva (Modo A) quedan **bloqueadas**: Odoo destruye chatter y
  adjuntos al eliminar el registro. La ruta correcta es el Modo B o gestionar el documento antes
  de reintentar. Solo se excluyen el aviso automático de creación de `mail.thread` y el estado
  transitorio de UI (`mail.followers`, wizards) — ver `04_DECISION_LOG.md` (AD-80).
- El «revisan Auditoría/Contabilidad» del Modo C no abre un circuito de aprobación: cualquier
  traza financiera convierte el caso en Modo D y bloquea la purga.
- El archivado (`active`) queda diferido a una fase separada (`05_BACKLOG.md`).

### 15.4 Retoma

1. Diseñar la fase de archivado/consulta (campo `active`, filtro y efecto en la vista SQL de la
   Consola) si negocio lo aprueba.
2. Validar visualmente el bloque SV y el asistente de ciclo de vida con una recepción por
   Volumen real (no hay lote SV con historia material en `madenat_test`).
3. Evaluar si el diagnóstico de ciclo de vida debe exponerse también para `lumber.reception`
   (Producto), hoy fuera de alcance.

---

## 16. Búsqueda, filtros y agrupaciones de la Consola de Intake (2026-10-07, AD-101)

### 16.1 Estado

- **Aplicado en `madenat_test`**: `madenat_lumber_intake` **18.0.0.11.0**. **No** desplegado a
  producción. **Sin** cambios de ACL, ingesta ni stock en esta intervención.
- Se ajustaron la **vista SQL** de la Consola (3 columnas nuevas: `oc_documental`, `guide_date_kind`,
  `processor_id`), el campo de **solo búsqueda** `product_filter_id`, la **lista/form** y la
  **vista de búsqueda** (campos, filtros y agrupaciones). Ver `00_ARQUITECTURA.md` §4.10.
- **`HEAD` `e302c48` NO contiene esta intervención.** El código aplicado incluye **cambios locales
  sin commit** (3 archivos modificados + 1 test nuevo en `madenat_lumber_intake`), además de otros
  cambios locales preexistentes ajenos a este tema. **No** equiparar `HEAD` con el código ejecutado.

### 16.2 Comportamiento aplicado (resumen)

- **OC documental vs OC vinculada:** `oc_documental` (referencia del documento) separada de
  `purchase_id` (OC vinculada); columna, búsqueda y agrupaciones; filtros OC vinculada/pendiente/no
  indicada. `purchase_reference` se conserva por compatibilidad.
- **Fecha:** `guide_date_kind` (`emission`/`reception`) + columna «Origen fecha»; `guide_date` sin cambios.
- **Modalidades:** Producto/Procesado/Volúmenes por `ingestion_type` (dominios disjuntos, **no** radio;
  combinación por AND ⇒ vacío); filtros «Procesada (legacy)» y «Error»; Abiertos/Finalizados sin ampliar.
- **Producto real:** `product_filter_id` (solo búsqueda) por líneas de ambos orígenes, sin duplicar.
- **Procesador:** `processor_id` desde la Orden de Procesamiento (JOIN 1:1), nunca el proveedor.

### 16.3 Evidencia

- Pruebas y verificaciones: `03_TESTS.md` §11. Decisión: `04_DECISION_LOG.md` **AD-101**.
- **Integridad (MD5 de los archivos aplicados):** `intake_console.py` `923a6912…`;
  `intake_console_views.xml` `cf07b72a…`; `tests/__init__.py` `baf2f8ba…`;
  `test_search_console_oc_fecha_modality.py` `895b783b…`.
- **Respaldos (fuera de CANON, ubicación protegida):** `APPLY_BUSQUEDA_INTAKE_20261007/backup/`
  — código pre-cambio (`intake_module_pre.tar.gz`), volcado `pg_dump -Fc` de `madenat_test`
  (integridad verificada por índice TOC), filestore y `git_status_pre/post.txt`. Solo se realizaron
  **controles de integridad** (formato del volcado, índice TOC, checksums); la **restauración NO se
  probó**. Los expedientes externos (`AUDIT_/IMPL_/APPLY_BUSQUEDA_INTAKE_20261007/`) permanecen como
  **antecedentes**, no como fuentes documentales mantenidas.

### 16.4 Límites y retoma

1. **V3 (navegador) pendiente**: comprobar en UI OC documental/vinculada, fechas, producto real,
   procesador y combinaciones de filtros.
2. **Instalación en base limpia**: la vista de lista referencia `action_madenat_lumber_intake_new`
   definida más abajo en el mismo archivo (referencia hacia adelante preexistente); resolver en
   trabajo separado (reordenar sin semántica).
3. **Volumen numérico**, **otros orígenes de procesador** y **ampliación de Abiertos/Finalizados**
   quedan como decisiones pendientes. Ver `05_BACKLOG.md`.


---

## 17. Confirmación de retorno de servicio al enviar a stock — AUDITORÍA DE RETOMA (2026-10-07)

> **Naturaleza.** Sección de **auditoría de retoma** (solo lectura + registro). **No** autoriza
> modificar código, ACL ni datos, ni desplegar. La confirmación **NO está aplicada** en el código
> activo ni en ninguna base. Su especificación vive, como **antecedente técnico**, en el expediente
> externo `IMPL_SERVICE_RETURN_20261006/` (copia de trabajo aislada con su `diff` y logs); **no** es
> fuente documental mantenida ni versión aprobada.

### 17.1 Estado real (verificado en código activo)

- El código activo (`custom_addons/`; HEAD `e302c48`; rama
  `feat/guia-correccion-documental-preservada-20261002`) **no contiene** el campo
  `service_return_confirmation`, ni `_assert_service_return_confirmed`, ni los filtros de retorno de
  servicio, ni el proxy de consola. `grep` de `service_return` sobre `custom_addons/` = **0 coincidencias**.
- La documentación activa tampoco menciona «retorno de servicio»: el §11.9 de `12_FLUJOS_INGESTA.md`,
  el §19.9 de `19_IMPUTACION_SV_Y_PROCESADORES.md`, la entrada AD y el ítem de backlog existen **solo**
  en la copia documental del expediente, **no aplicada**.
- **Conclusión:** la confirmación existe **únicamente en la copia de trabajo aislada**
  (`IMPL_SERVICE_RETURN_20261006/addons`), validada en la base dedicada `srvret_test_20261006`
  (53/53 tests OK). **No implementado** en activo · **no registrado en la base** activa ·
  **no verificado en navegador**.

### 17.2 Punto de enganche real de «Enviar a stock» (código activo)

- Botón `Enviar a Stock` → `madenat_lumber_intake/views/intake_console_views.xml:71` →
  `action_send_to_stock` (`madenat_lumber_intake/models/intake_console.py:1740`) → para **Procesado**
  delega en `madenat.guia.processing.action_validate`
  (`madenat_lumber_core/models/madenat_guia_processing.py:2117`; la fachada
  `madenat_lumber_intake/models/intake_guia_processing.py:389` deriva `granel` a
  `_action_validate_volume_intake`).
- **Hoy no existe ningún guard de confirmación** en `action_validate`. El parche propone el punto
  servidor único `_assert_service_return_confirmed()` invocado al inicio del método (antes de crear
  lotes/movimientos), y una confirmación **inline** (radio en el formulario), no un asistente modal.

### 17.3 Aclaración de «retorno de servicio» (doctrina y diseño del parche)

- La condición la registra la **Guía de procesado** (`madenat.guia.processing`) en el campo
  `service_return_confirmation` (Selection `'yes'`/`'no'`, **sin default**; vacío = sin confirmar).
- **No** es una devolución de picking, ni una reversión de cancelación, ni la corrección de la guía
  15183. **No** se infiere por tipo Procesado/Cepillado ni por número de guía.
- **Imputaciones posteriores:** la confirmación **no** dispara imputación SV (I2, AD-87/AD-91);
  «imputación posterior» = acto declarativo independiente (etiqueta→SV) que sigue siendo un paso
  posterior. El filtro «Retornos pendientes de imputación» **no** evalúa cobertura parcial
  (identificación INCOMPLETA, declarado).

### 17.4 Componentes y estado (parche vs. código activo)

| Componente | Archivo/modelo (según parche) | Estado real |
|---|---|---|
| Campo `service_return_confirmation` (Selection, sin default) | `madenat.guia.processing` | No implementado en activo |
| Guard servidor `_assert_service_return_confirmed` | `action_validate` (core) | No implementado en activo |
| Proxy no almacenado (`service_return_in_scope` + inverse) | `madenat.lumber.intake.console` | No implementado en activo |
| Radio en 3 vistas (consola, fachada, form core) | XML de intake + core | No presente en activo |
| 3 filtros de búsqueda (retorno / no retorno / sin confirmar) | `guia_processing_list_search.xml` | No presentes en activo |
| Relación inversa `sv_imputation_ids` + filtro «pendientes de imputación» | `madenat.sv.imputation` (logistics) | No implementado en activo |
| Tests `test_service_return_confirmation` (15) / `test_service_return_pending_filter` (8) | intake / logistics | Solo en copia; base activa sin ellos |


### 17.5 Evidencia y pruebas

- **Acreditadas (copia aislada, base `srvret_test_20261006`):** `0 failed, 0 errors of 53 tests`
  (log `IMPL_SERVICE_RETURN_20261006/logs/iso_run4.log`). Incluye el flujo de consola
  (`action_send_to_stock` bloquea sin confirmar) y seguridad por rol **Operaciones**.
- **Pendientes (no acreditadas):** (a) prueba con el usuario real **Cristhian**
  (`cristhian.elguetag@gmail.com`) — en la base aislada no existía ⇒ **INCONCLUSO**; (b)
  **verificación en navegador**; (c) ejecución en una base con datos reales (`madenat_test`) —
  **no ejecutada**.
- **Artefactos:** `service_return_confirmation.diff` (sha256 `31b0bc73…`, md5 `c0de2335…`),
  copia `addons/`, logs `logs/iso_run*.log`. Permanecen como **antecedentes**; no se copian dumps,
  filestore ni secretos al módulo documental.

### 17.6 Decisión pendiente (no inventar)

- **Aprobación del diff** y **asignación del número AD**: pendientes de decisión del usuario (el
  expediente no inventa número). **No** se registra como decisión aprobada.

### 17.7 Compatibilidad del diff (verificada en copia desechable)

Aplicabilidad probada con `patch -p0 --dry-run` sobre una **copia temporal** de los archivos
**activos** (el árbol activo y el expediente **no** se modificaron):

- **Aplican limpio:** `madenat_guia_processing.py`, `guia_processing_views.xml`,
  `guia_processing_list_search.xml`, `test_granel_route.py`, `intake_guia_processing_facade_views.xml`,
  `madenat_sv_imputation.py`, `madenat_sv_imputation_views.xml`,
  `madenat_lumber_logistics/tests/__init__.py`, `12_FLUJOS_INGESTA.md`, `19_...PROCESADORES.md`.
- **Aplican con offset (deriva de líneas, sin conflicto):** `intake_console.py` (offsets +24/+45),
  `intake_console_views.xml` (+8), `04_DECISION_LOG.md` (fuzz de contexto).
- **Conflictos (2, de contexto — no de lógica):** `madenat_lumber_intake/tests/__init__.py` (la cola
  activa ya incluye `test_guia_delete_acl` / `test_search_console_oc_fecha_modality`) y
  `05_BACKLOG.md` (el backlog activo ya no termina en el contexto base). **Ajuste mínimo:**
  re-anclar el `import` al final del archivo y anexar la sección de backlog al final, sin semántica
  nueva. **No** fusionar diffs automáticamente.

### 17.8 Próxima intervención mínima

1. Aprobar/rechazar el diff y, si se aprueba, asignar el número **AD** según convención vigente.
2. Reaplicar resolviendo los **2 conflictos de contexto** (§17.7), sin cambios semánticos.
3. Actualizar módulos en una base **no productiva**; correr los tests en una base con el usuario
   **Cristhian**; **verificación en navegador**. Solo tras aprobación explícita.

### 17.9 Cierre de la auditoría

**Quedamos en** la confirmación de retorno de servicio **no aplicada**: existe y fue validada solo
en la copia de trabajo aislada del expediente `IMPL_SERVICE_RETURN_20261006/`, sin eco en el código
activo ni en la documentación canónica.
**El trabajo existente cubre** el diseño, el `diff` (`service_return_confirmation.diff`), la copia de
trabajo, los 2 archivos de test y los logs de 53/53 pruebas OK en base dedicada.
**Falta exactamente** aprobar el diff (y asignar AD), reaplicarlo resolviendo 2 conflictos de
contexto, actualizar en base no productiva y acreditar la prueba con el usuario Cristhian + la
verificación en navegador.
**La próxima intervención mínima es** la decisión de aprobación del diff; luego, la aplicación
trazable con esos 2 ajustes y las pruebas pendientes.
### 17.10 Intervención aprobada (2026-10-07) — identificación no bloqueante + imputación posterior

**Decisión del usuario (2026-10-07).** Se aprobó implementar y probar **en aislamiento** los
alcances **A** (identificación de retorno de servicio **no bloqueante**) y **B** (imputación
posterior **reutilizando el mecanismo SV/I2**), sin módulos nuevos:

1. `service_return_confirmation` **opcional, sin default**; *vacío* = pendiente (NO equivale a «No»);
   **no** bloquea la ingesta ni el envío a stock.
2. Con imputaciones **`applied`**, cambiar la identificación a «No» o vaciarla se **rechaza**
   (reversar primero).
3. Se mantiene el **filtro mínimo** «Retornos sin imputación aplicada» (no detecta cobertura parcial).
4. **Destino marcado «Sí» al APLICAR** (`action_apply`), no al guardar borrador; sin marcado automático.
5. Efectos de **I2 intactos** (documental; sin stock/ledger/costes I3/I5).

**Estado real (verificado en aislamiento).** Implementado en la copia de trabajo
`IMPL_SERVICE_RETURN_AB_20261007/addons`. **Gate previo (2026-10-07):** sobre una **copia del árbol
activo con sus cambios locales** + diffs A/B (`/tmp/gate`, byte a byte = workcopy; los diffs **no**
tocan la documentación ya actualizada), base aislada `srvretab_gate_20261007`: **0 failed, 0 error(s)
of 88 tests**, incluida la prueba con el **usuario real Cristhian** (`su=False`, grupos intactos).
Corrida completa previa de las 3 suites: **1020** pruebas, con **9 fallas PREEXISTENTES** (idénticas
con el código activo **sin** el cambio). **No aplicado** al entorno activo.

**Falta exactamente:** (a) **verificación en navegador** — servidor aislado
`http://127.0.0.1:8070` (base `srvretab_gate_20261007`); guion en
`IMPL_SERVICE_RETURN_AB_20261007/docs/GUION_VERIFICACION_NAVEGADOR.md`; **NO ejecutada** (sin
navegador). (b) Aprobar la aplicación y actualizar módulos en una base no productiva.
Detalle en `04_DECISION_LOG.md` **AD-102**.

**Corrección de estado «I2 pendiente».** El modelo I2 está **presente en el código**
(commit `2888745`); su «pendiente» previo era de **fase de diseño**, no de implementación.

### 17.11 Checkpoint de pausa (2026-10-07) — reanuda 2026-10-08

> **Naturaleza.** Registro de pausa. **No** autoriza aplicar A/B. Sin operaciones de código, base,
> servicios ni limpieza. **V3** y **aprobación de aplicación** quedan **pendientes**.

**Estado registrado.**
1. **A/B implementados únicamente en aislamiento** (workcopy `IMPL_SERVICE_RETURN_AB_20261007/addons`).
2. **Gate sobre copia del árbol activo con cambios locales:** artefacto reconstruido **byte a byte**,
   **45/45** archivos coincidentes (los diffs **no** incluyen `madenat_lumber_docs/`).
3. **Pruebas dirigidas: 88/88 aprobadas** (0 failed, 0 errors) sobre base aislada `srvretab_gate_20261007`.
4. **Cristhian (uid 8)** probado con **`su=False`, sin cambios de grupos** (39 filas de grupos = fuente).
5. **Navegador V3: pendiente** (no ejecutado; sin navegador).
6. **Código activo, `madenat_test` y producción:** **sin** aplicación de A/B.
7. **Nueve fallas preexistentes** conservadas en el registro (`03_TESTS.md` §12.2).
8. **Concurrencia específica** de las nuevas reglas: **no acreditada**.
9. **Filtro «sin imputación aplicada»:** **no** evalúa cobertura parcial.
10. **I3/I5** (salida nativa/ledger, costo): **fuera de alcance**.

**Artefactos — SHA-256 vigentes del gate.**

| DifF | SHA-256 |
|---|---|
| `IMPL_SERVICE_RETURN_AB_20261007/patch/A_identificacion_no_bloqueante.diff` | `3d5115e9eadf1ca72634609c88140a583d5255cad3dac2aab406bce18123799d` |
| `IMPL_SERVICE_RETURN_AB_20261007/patch/B_imputacion_posterior.diff` | `5d23ea02a37e9f9469b821ab9e0030f3fd79319fe4f809e91c40bc367479ee94` |
| `IMPL_SERVICE_RETURN_AB_20261007/patch/AB_completo.diff` | `a4131812b238ecb98cb393f27dc8502cc6375050cd6e46af57db1189a6aaa282` |

> **Versiones anteriores del diff (SUPERADAS, no vigentes):** `7d2d32fd…` (A), `0bc5c1b8…` (B),
> `f485a355…` (AB) — previas a incorporar las pruebas de Cristhian. **No aplicables.**

**Entorno aislado para verificación manual (conservado; estado no cambiado en la pausa).**
- URL `http://127.0.0.1:8070` · contenedor `srvretab_web` · base `srvretab_gate_20261007` · usuario
  Cristhian (uid 8).
- Guion: `IMPL_SERVICE_RETURN_AB_20261007/docs/GUION_VERIFICACION_NAVEGADOR.md`.
- Uso aislado; **no** se registra aquí ninguna credencial. **No** eliminar la base ni el contenedor.

**Secuencia para 2026-10-08.**
1. Leer este checkpoint y **AD-102**.
2. **Revalidar** estado Git, hashes, servicios y disponibilidad del entorno aislado (no asumir).
3. Ejecutar el guion de navegador **exclusivamente** en el puerto **8070**, confirmando la base antes
   de operar.
4. Registrar **V3** solo tras recibir **evidencia real**.
5. Presentar la **solicitud final de aplicación** con destino exacto **`madenat_test`** y respaldo de
   **código con cambios locales + base + filestore**.
6. **Esperar autorización expresa** antes de aplicar.

**Corrección del plan de reversión (obligatoria).** `patch -R` revierte **solo archivos de código**;
**no** constituye restauración completa: **no** revierte necesariamente (a) metadatos/esquema que el
`-u`/actualización de módulos pudo alterar ni (b) registros creados con posterioridad. Antes de
aplicar se distinguen tres cosas: **(1) reversión de código** (`patch -R`), **(2) actualización de
módulos** (`-u`, esquema), **(3) recuperación desde respaldo** (código + base + filestore). **No**
borrar clasificaciones ni imputaciones registradas para facilitar una reversión.

### 17.12 Retoma (2026-10-08) — revalidación de solo lectura y disponibilidad del entorno aislado

> **Naturaleza.** Retoma **de solo lectura**: no se aplicaron diffs, no se actualizaron módulos, no se
> reiniciaron servicios y **no** se limpió nada. **No** autoriza despliegue, `commit`/`push` ni
> eliminación de artefactos. **V3** y la **aprobación de aplicación** siguen **pendientes**.

**Revalidado sin diferencias respecto de §17.11.**

1. **Rama/HEAD/estado Git** (el repositorio es `custom_addons/`; la raíz del proyecto no es repo):
   `feat/guia-correccion-documental-preservada-20261002` · HEAD
   `e302c488321c276af7e07f1abeecc8bc261a89f4` — idénticos al checkpoint. `git status`: **55
   modificados** (44 de código/artefactos + 11 de documentación) y **11 sin seguimiento**; **sin**
   `stash`. **Ninguna escritura posterior al checkpoint** (`find … -newermt '2026-10-07 23:35'` =
   vacío). La diferencia 53→55 del recuento registrado en `PLAN_APLICACION_REVERSION.md` es
   **documental** (03/05/02/índice se escribieron después de ese plan); **ningún** archivo de código
   se tocó tras el checkpoint.
2. **SHA-256 de los artefactos = checkpoint:** `A` `3d5115e9eadf1ca72634609c88140a583d5255cad3dac2aab406bce18123799d`,
   `B` `5d23ea02a37e9f9469b821ab9e0030f3fd79319fe4f809e91c40bc367479ee94`,
   `AB` `a4131812b238ecb98cb393f27dc8502cc6375050cd6e46af57db1189a6aaa282`.
3. **Integridad del artefacto:** el workcopy `IMPL_SERVICE_RETURN_AB_20261007/addons` difiere del
   **árbol activo** **exactamente** en los **15** archivos de `AB_completo.diff` (12 modificados + 3
   nuevos); el resto de diferencias son `__pycache__/*.pyc`. `patch -p1 --dry-run` sobre una **copia
   de trabajo** de esos 15 archivos ⇒ **sin rechazos (exit 0)**. **No** se aplicó ningún diff: los 2
   conflictos de contexto de §17.7 pertenecían al **antecedente** `IMPL_SERVICE_RETURN_20261006/`.
4. **A/B ausente del entorno activo:** `service_return_confirmation` = **0** coincidencias en
   `custom_addons/**/*.py|*.xml`; en la base activa `madenat_test` la columna **no existe**.
5. **Expediente y gate conservados:** `IMPL_SERVICE_RETURN_AB_20261007/{addons,patch,logs,docs}` (logs
   `iso_run1`, `iso_full_run1`, `base_targeted`, `gate_run1`, `gate_run2` = `88/88`, 0 failed/0 errors).
   **Límites intactos:** 9 fallas preexistentes, concurrencia no acreditada, filtro **sin** cobertura
   parcial, I3/I5 fuera de alcance.
6. **Servicio activo intacto:** `odoo18_app` responde **HTTP 200** en `127.0.0.1:8069`
   (Odoo 18.0-20260817); **no** se reinició ni se modificó.

**DIFERENCIA — el entorno aislado NO se conservó (reinicio del host).**

- El host se **reinició** el 2026-10-08 (`uptime` ≈ 8 min; `odoo18_app` arrancado `11:52:22Z`,
  `odoo18_db` `11:49:09Z`).
- El contenedor **`srvretab_web` no existe** (ni en ejecución ni detenido) y **`127.0.0.1:8070` no
  escucha** ⇒ **V3 no puede ejecutarse** en este estado.
- **`/tmp/gate` existe pero está vacío** (0 archivos): el árbol de addons que montaba el servidor
  aislado se perdió con la limpieza de `/tmp` (el workcopy del expediente **sí** se conserva).
- **Se conserva la base aislada** `srvretab_gate_20261007` (76 MB; columna
  `service_return_confirmation`, 12 guías, imputación `IMP00946`); también `srvretab_base_20261007`,
  `srvretab_test_20261007` y `madenat_test`. **No** se eliminó ninguna base.

**V3 — sigue pendiente (no ejecutada).** Guion:
`IMPL_SERVICE_RETURN_AB_20261007/docs/GUION_VERIFICACION_NAVEGADOR.md`. Observaciones de solo lectura
útiles para ejecutarla sobre la base aislada existente:

- El radio «¿Es retorno de servicio?» es **editable** en la Consola cuando `review_state != 'sent'`
  (guías `validated` → `sent` ⇒ solo lectura) y en formulario cuando `state != 'validated'`.
- De las **6** guías `service` de la base aislada, la **única con fila editable en la Consola** es la
  guía **19827** (`verified`, fila de consola `900001198`); 19846, 19826, 26270 y 900002 están
  `validated` y **15183** está cancelada.
- La imputación existente `IMP00946` (aplicada, 2026-10-03, uid 8) pertenece a la guía **`granel`**
  `UAT-SV-20261003-IMPG` ⇒ **no** interfiere con las guías `service` (su radio no es visible).

**Recreación del entorno aislado — AUTORIZADA Y EJECUTADA (2026-10-08, solo aislamiento).** El usuario
autorizó expresamente la vía **(a)**: montar el workcopy **sin aplicar diffs**. Ejecutado:
`docker run -d --name srvretab_web --network odoo-18-ce_internal_backend -p 127.0.0.1:8070:8069
-v IMPL_SERVICE_RETURN_AB_20261007/addons:/mnt/extra-addons:ro -v srvretab_web_data:/var/lib/odoo
odoo-18-ce-web:latest odoo --db_host=db --db_user=odoo --db_password=odoo --db_port=5432
--database=srvretab_gate_20261007 --db-filter='^srvretab_gate_20261007$'
--addons-path=/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons --workers=0
--max-cron-threads=0` (**sin** `--test-enable`, **sin** `-u`, **sin** aplicar diffs).

- **Verificado:** `8070 → /web/login` **HTTP 200**; el selector de base lista **solo**
  `srvretab_gate_20261007`; A/B presente en el árbol montado (`service_return_confirmation` y
  `_i2_check_destination_is_service_return`); `Registry loaded` sin incidencias.
- **Filestore (hallazgo y corrección dentro del aislamiento):** la base aislada referenciaba **879**
  adjuntos y su filestore se perdió con `/tmp`. Se **pobló el volumen aislado**
  (`srvretab_web_data/filestore/srvretab_gate_20261007`, 1170 archivos, 101 MB) copiando desde el
  volumen del stack **en modo `:ro`**, aprovechando que los hashes de assets son idénticos
  (verificado: `web.assets_frontend.min.css` y `…_minimal.min.js` pasan de **500 → 200**).
  Cobertura: **844/879**; los **35** no resueltos son **9 ficheros distintos** y **todos** son
  imágenes de `res.partner` (avatares) ⇒ **cosmético**. **No** se modificó ninguna base ni el servicio
  activo; la escritura fue solo en el volumen del aislamiento.
- **Estado de datos aislados (sin cambios):** 12 guías, todas con `service_return_confirmation`
  vacío; 1 imputación `applied` (`IMP00946`, guía `granel`).
- **Servicio activo:** intacto (`8069` HTTP 200, `odoo18_app` sin reinicio). A/B sigue **ausente** del
  árbol activo y de `madenat_test`.
- **V3 sigue PENDIENTE de evidencia manual.** La contraseña temporal **no** se divulga; está en el
  guion (§Entorno aislado).

### 17.13 Implementación en el desarrollo existente (`madenat_test`), reorganización de la UI y retiro del aislamiento (2026-10-08)

**Destino.** La implementación se realizó **directamente en el entorno de desarrollo existente**
(`http://localhost:8069/`, base `madenat_test`, contenedor `odoo18_app`). **No** se crearon bases,
contenedores ni ramas nuevas. El aislamiento temporal A/B se **retiró** al finalizar (§17.13.4).

*Nota de transición:* hasta esta intervención A/B estaba **ausente** del código activo y de
`madenat_test` (ver §17.12); a partir de aquí queda **aplicado** en el desarrollo.

#### 17.13.1 Revalidación previa del estado real y respaldo

| Dato | Valor verificado |
|---|---|
| Repositorio | `custom_addons/` (la raíz del proyecto **no** es repositorio) |
| Rama | `feat/guia-correccion-documental-preservada-20261002` |
| HEAD | `e302c488321c276af7e07f1abeecc8bc261a89f4` |
| `git status` | 53 modificados + 12 sin seguimiento (cambios locales **preservados**) |
| Servicio Odoo 8069 | contenedor `odoo18_app` (imagen `odoo-18-ce-web:latest`) |
| PostgreSQL | contenedor `odoo18_db` (`postgres:15`) |
| Base destino | `madenat_test` |
| `addons_path` / `data_dir` | `/mnt/extra-addons` ← bind de `custom_addons`; `/var/lib/odoo` (volumen `odoo-18-ce_odoo-web-data`) |
| Expediente | `IMPL_SERVICE_RETURN_AB_20261007/` (workcopy `addons/`, `patch/AB_completo.diff`) |
| Documentación rectora | `custom_addons/madenat_lumber_docs/` (`CANON/`, `WIKI/`, `LEGADO/`, `RAW/`) |
| Integridad A/B/AB | SHA-256 = checkpoint (`3d5115e9…`, `5d23ea02…`, `a4131812…`) |
| Artefacto | **15** archivos (12 modificados + 3 nuevos); `patch -p1 --dry-run` ⇒ **0 rechazos** |
| Workcopy | **byte a byte** = árbol activo + los 15 archivos de `AB_completo.diff` (verificado) |
| Vistas responsables | Ingreso de Madera = `madenat.lumber.intake.console` (vista primaria `view_madenat_lumber_intake_console_form`, id 1867; **sin** vistas heredadas) |

**Diferencia respecto del reporte previo:** el reporte indicaba que el aislamiento ya no existía; en
la revalidación el entorno aislado **sí** estaba operativo (`srvretab_web` en `127.0.0.1:8070`, base
`srvretab_gate_20261007`). Se ajustó la implementación sin sobrescribir trabajo local.

**Respaldo recuperable (verificado):** `BACKUP_AB_APPLY_20261008/`
`code/custom_addons_full_20261008_092958.tar.gz` (25 MB, incluye `.git`),
`code/custom_addons_local_changes_antes.patch` (+ `git_status_antes.txt`, `HEAD.txt`),
`db/madenat_test_20261008_092958.dump` (11,3 MB; TOC 13.325 entradas; `pg_restore --list` OK),
`filestore/odoo-web-data_20261008_092958.tar.gz` (109 MB; 30.405 entradas; 722 archivos de
`filestore/madenat_test`), `config/config_20261008_092958/odoo.conf`. Ninguno vacío ni apuntando a
otra base. **No** se usó `git reset --hard`, `git clean`, `checkout` masivo ni limpieza global de
Docker.

#### 17.13.2 A/B aplicado en el código de desarrollo

- Fuente: `patch/AB_completo.diff` (autoritativo). **Aplicado una sola vez** con `patch -p1`, con copia
  `.pre_ab_20261008` de cada archivo movida **fuera** del árbol
  (`BACKUP_AB_APPLY_20261008/pre_patch_files/`). **No** se aplicaron A, B y AB por separado; **no** se
  copió el workcopy; **no** se trasladaron `.pyc` ni cachés.
- Los **15** archivos quedaron **byte a byte** idénticos al workcopy validado
  (`IDENTICAL=15 MISMATCH=0`).
- **Actualización controlada:** `odoo18_app` **detenido** durante el cambio de esquema; actualización en
  contenedor *one-shot* (`--rm`) **solo** contra `madenat_test`, con
  `-u madenat_lumber_core,madenat_lumber_intake,madenat_lumber_logistics --stop-after-init --no-http
  --max-cron-threads=0`. **Sin** `-u all` y **sin** `--test-enable`
  (`APPLY_AB_UI_20261008/logs/update_modules_20261008_093223.log`: `module upgrading`, `Modules
  loaded.`, **0 ERROR / 0 CRITICAL**).
- Resultado en `madenat_test`: columna `madenat_guia_processing.service_return_confirmation`
  (`character varying`) presente; vistas cargadas sin error; nueva vista
  `madenat.guia.processing.search.service.return` (id **2909**); campos
  `madenat.guia.processing.sv_imputation_ids`, `madenat.lumber.intake.console.service_return_confirmation`
  y `.service_return_in_scope` registrados.
- Comportamiento conforme al artefacto: **vacío = pendiente** (≠ No); **sin** guard
  `_assert_service_return_confirmed`; **sin** imputación automática al marcar «Sí»; `action_apply`
  exige destino «Sí»; con imputación `applied` se **rechaza** cambiar a «No» o vaciar; tras reversar
  se permite; `_i2_check_destination_is_service_return` preservado; permisos y grupos **intactos**.
- Nombres técnicos de los módulos tomados de sus `__manifest__.py`. **No** se creó módulo nuevo ni se
  amplió el alcance a otros modelos, estados o flujos.






#### 17.13.3 Reorganización de la UI de Ingreso de Madera

Archivo: `madenat_lumber_intake/views/intake_console_views.xml` (vista **primaria**; sin vistas
competidoras ni campos duplicados).

- **Resumen del ingreso** a todo el ancho y en **dos columnas** (un `<group>` con dos `<group>`):
  izquierda Producto / Fecha de guía / Proveedor / Procesador; derecha OC documental / OC vinculada /
  Estado de OC / Referencia. **«Aplicar cambios»** queda **debajo** de los campos, conservando acción,
  permisos, icono y condición de visibilidad. Debajo de ambas columnas, a todo el ancho, la **línea de
  identificación de retorno** (mismo campo, mismo `widget="radio"`, mismos `invisible`/`readonly`;
  **sin** cambio de comportamiento).
- **Evidencia documental**: un **único** bloque (se elimina la duplicación del encabezado: antes
  «Evidencia documental» aparecía **dos** veces) en **tres columnas** (`col="3"`):
  1) **Documentos** (Guía PDF, Packing list Excel);
  2) **Volúmenes y diferencias** (Vol. PDF/Guía, Suma líneas Packing, Vol. Packing, Δ Packing vs
     Líneas, Δ PDF vs Packing);
  3) **Packing y conciliación** (Paquetes Packing, Piezas Packing, Conciliación documental).
  Se preservan campos técnicos, unidades, precisión `digits="[16, 3]"`, badges, cálculos, permisos y
  visibilidad (`volume` oculta el bloque; las columnas 2 y 3 solo en `processed`).
- **Detalle del packing list**: se conserva **debajo** de Evidencia documental y a todo el ancho; **no**
  se cambiaron sus columnas, datos, cálculos, edición ni acciones.
- **Sin CSS global** (solo clases estándar de Odoo/Bootstrap ya usadas en el proyecto) y **sin**
  rediseñar otras pantallas.

Verificación estructural *read-only* sobre la vista efectiva compilada de `madenat_test`: resumen en 2
columnas, **un** encabezado `Evidencia documental`, `col="3"` con las tres columnas, `Aplicar cambios`,
`radio` e `in_scope` presentes, y **orden** de bloques `resumen → botón → radio → evidencia → packing`.

#### 17.13.4 Retiro del aislamiento temporal A/B

Ejecutado **después** de verificar la implementación y con los respaldos disponibles. Se dumpó la
información de las bases temporales a `APPLY_AB_UI_20261008/retired/db/` (3 × ~11,4 MB, `rc=0`) y se
copiaron `/tmp/iso_*.txt`, `/tmp/att_all.txt` y `/tmp/ab_dryrun` a `…/retired/tmp/`.

| Retirado | Detalle |
|---|---|
| Contenedor | `srvretab_web` (`docker stop` + `docker rm`) — publicación del puerto **8070** liberada |
| Volumen | `srvretab_web_data` (verificado antes: **solo** lo usaba `srvretab_web`) |
| Bases de datos | `srvretab_gate_20261007`, `srvretab_base_20261007`, `srvretab_test_20261007` (`DROP DATABASE … WITH (FORCE)`, nombres exactos resueltos) |
| Temporales | `/tmp/gate` (vacío), `/tmp/ab_dryrun`, `/tmp/iso_hashes.txt`, `/tmp/iso_missing.txt`, `/tmp/iso_missing_u.txt` |

**Preservado:** `madenat_test`; `odoo18_app` (8069); `odoo18_db`; volumen y filestore del desarrollo;
`custom_addons` con sus cambios locales; `madenat_lumber_docs`; expediente
`IMPL_SERVICE_RETURN_AB_20261007/`; parches, logs y evidencias históricas; respaldos. **No** se usó
`docker system prune`, `docker volume prune`, comodines amplios ni `docker compose down -v`.

**Límite registrado:** el directorio **vacío** `/tmp/gate` (propiedad de `root`) no pudo eliminarse sin
contraseña de `sudo`; no contiene archivos y desaparece al reiniciar el host.

**Estado final verificado:** 8069 operativo; `madenat_test` accesible; **8070 sin publicación**; 0 bases
`srvretab%`; volumen `srvretab_web_data` eliminado.

#### 17.13.5 Estado de V3 y pruebas

- Pruebas dirigidas del artefacto ejecutadas **sobre `madenat_test`**: **`0 failed, 0 error(s) of 88
  tests`** (misma nómina de 8 clases que el gate histórico; incluye las pruebas con **Cristhian uid 8**,
  `su=False`, grupos intactos). Log:
  `APPLY_AB_UI_20261008/logs/tests_directed_madenat_test_20261008_093825.log`.
  El **gate histórico de 88 pruebas** (2026-10-07, base aislada) se conserva como antecedente; la
  corrida de esta intervención es evidencia **nueva** sobre `madenat_test`.
- **V3 (navegador) SIGUE PENDIENTE.** Quien suscribe **no dispone de navegador**: no se declara
  completada. Guion manual actualizado a `http://localhost:8069` / `madenat_test` en
  `IMPL_SERVICE_RETURN_AB_20261007/docs/GUION_VERIFICACION_NAVEGADOR.md`.
- Se conservan las **9 fallas preexistentes** y los límites (concurrencia no acreditada, filtro sin
  cobertura parcial, I3/I5 fuera de alcance). Ver `03_TESTS.md` §12.6.


### 17.14 Auditoría de las solicitudes de Cristhian (2026-09-02 y 2026-09-07) — 2026-10-08

**Alcance.** Auditoría **de solo lectura**. Se contrastan **16 requisitos (R01–R16)** derivados de la
conversación del 2026-09-02 y del hilo «PRUEBA DE SISTEMA» (reportes del 2026-09-07) contra la
documentación rectora, el código vigente y las evidencias disponibles. **No** se modificó código, datos
ni servicios; **no** se ejecutaron pruebas nuevas; **no** se crearon bases, contenedores ni ramas;
**no** hubo commit ni push. Las correcciones necesarias quedan **identificadas y propuestas**
(§17.14.5), **no ejecutadas sin autorización**.

**Preservación de los reportes del usuario.** Las expresiones de Cristhian («operación no válida al
final», «calcula el volumen solo de embarque, no el del packing», «no lee el documento») se conservan
**como reportes**, sin atribuirles causa técnica: la causa se registra solo cuando hay evidencia
(§17.14.3).

#### 17.14.1 Entornos verificados en esta intervención

| Entorno | Ruta / servicio | Estado verificado | Qué se pudo verificar |
|---|---|---|---|
| Desarrollo **local** (código) | `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons` | Rama `feat/guia-correccion-documental-preservada-20261002`; HEAD `e302c488321c276af7e07f1abeecc8bc261a89f4`; `git status` = **62 modificados + 14 sin seguimiento** (76 entradas) | Lectura íntegra de código, vistas y tests; hashes SHA-256 |
| Desarrollo **local** (servicio) | `localhost:8069` / contenedor `odoo18_app` | **NO operativo desde esta distro**: `docker` no disponible (Docker Desktop sin integración WSL en esta distro) y `curl http://127.0.0.1:8069/web/login` → sin respuesta | **Ninguno**: no hubo consultas a la base local ni ejecución de pruebas locales |
| **TEST remoto** | `ubuntu@144.22.50.236` · `/opt/odoo18-test` · servicio `odoo18-test` (**active**) · base `madenat_test` | Inspección **solo lectura** por SSH (`sudo -u postgres psql`). `custom_addons` **no** es repositorio git; el repo git es `/opt/odoo18-test` y no es legible (git 2.25.1: `dubious ownership`) | Código desplegado (hashes), módulos instalados, esquema, vistas cargadas y contenido de `madenat_guia_processing` |
| Documentación rectora | `custom_addons/madenat_lumber_docs/` | Verificada. Versiones al inicio de la auditoría: **02 12.13.0 · 03 6.13.0 · 05 8.12.0 · índice 12.7.0** | Base documental del contraste |

**Correspondencia de código local ↔ TEST remoto (medida).** Manifiesto SHA-256 de **314 archivos**
`.py/.xml/.csv` de `madenat_lumber_core`, `madenat_lumber_intake`, `madenat_lumber_logistics` y
`madenat_ingestion_engine` (excluyendo `__pycache__`, `_archive`, `backups`): **0 discrepancias de
hash**, **0 archivos solo locales** y **39 archivos presentes solo en el remoto** (legado: `.bak/`,
`views.backup/`, `views/views.backup/`, `backups_20260819_*`, `lumber_reception_test.py`,
`scripts/migrate_reception_relations.py`, `views/lumber_reception_views_OLD.xml`,
`security/madenat_intake_security.xml`, `models/lumber_container_rollover_wizard.py`).

**Estado del TEST remoto (leído, no modificado).** Módulos `installed`: `madenat_lumber_core`
18.0.6.5.0 · `madenat_lumber_intake` 18.0.0.11.0 · `madenat_lumber_logistics` 18.0.1.6.0 ·
`madenat_ingestion_engine` 18.0.1.1.0. Columna `madenat_guia_processing.service_return_confirmation`
(`character varying`) **presente**; vistas `madenat.lumber.intake.console.form` (id 1660; contiene
`Aplicar cambios`, `Evidencia documental` y `service_return_confirmation`) y
`madenat.guia.processing.search.service.return` (id 1745) cargadas. La tabla
`madenat_guia_processing` contiene **un único registro**: **guía 26270** (id 17, `partner_id` 22 =
COMERCIALIZADORA Y DISTRIBUIDORA FERRAMENTA SPA, `tipo_recepcion='service'`, `state='validated'`,
creada 2026-09-08, última escritura 2026-10-06, `vol_comercial_pdf=57.840`, `vol_shipment_m3=48.009`,
`packing_volume_declared_m3` **vacío**, `sum_vol_documental_m3=0.000`,
`documental_conciliation_state='partial'`). Usuarios: uid 6 Leonardo Rodriguez, uid 7 María Victoria
Antonio, **uid 8 Cristhian Elgueta (activo)**, uid 9 Felipe Muñoz.

> **Advertencia de entorno (confirmada con datos).** Ambas bases se llaman `madenat_test` pero **no**
> son la misma base: en el TEST remoto **no existen** los partners de Arauco (RUT 96.510.970-6),
> Blocks & Cutstock (RUT 96.862.800-3), JCE (RUT 96.547.890-6) ni el `res_partner` id 2045 que
> `05_BACKLOG.md` (T11) cita para la base local. **No** se trasladan resultados locales al remoto.

#### 17.14.2 Matriz consolidada de requisitos (R01–R16)

**Estados permitidos:** CORREGIDO Y VERIFICADO · IMPLEMENTADO, PENDIENTE DE VALIDACIÓN · PARCIAL ·
PENDIENTE · NO ACREDITADO · NO REPRODUCIDO (indicando condiciones). **Ningún** requisito se declara
«cerrado» sin criterio de aceptación acreditado.

| ID | Origen | Proveedor / alcance | Síntoma o necesidad original | Criterio de aceptación | Evidencia documental | Evidencia de código (ruta · método) | Evidencia de prueba | Entorno verificado | Estado | Limitación / siguiente acción |
|---|---|---|---|---|---|---|---|---|---|---|
| **R01** | 02-sep (conversación) | Ingreso de Madera (general) | «Había eliminado elementos innecesarios del ingreso» y «retiraría los mensajes de prueba» que le impedían ingresar la guía y el packing | El ingreso se completa sin diálogos que interrumpan el flujo y sin mensajes de prueba; se conservan las validaciones legítimas | Sin entrada canónica específica | `intake_wizard_views.xml:48` (`tipo_ingreso invisible="1"`); `intake_wizard.py` `_onchange_suggest_tipo_ingreso` (186-201) y `_onchange_suggest_ingestion_profile` (203-262) — **devuelve `{'warning': …}` «Verifique el perfil de lectura antes de continuar» (251-262)** | `test_intake_wizard.py:537-543` (asertan el `warning` y su texto «no bloquea»); `test_intake_apply_changes.py` | Código (local = remoto, hash) | **PARCIAL** | En Odoo un `warning` devuelto por un método **interrumpe** la acción hasta pulsar «OK»; ese mensaje **sigue vigente** en el código activo. Falta identificar con Cristhian el aviso exacto (candidatos en §17.14.3 H-2) y reproducirlo en navegador |
| **R02** | 02-sep | Ingreso (general) | «Había quitado la selección entre procesados y compra de madera» | El operador no elige manualmente Producto/Procesado; la ruta la decide el contenido del documento | `04_DECISION_LOG.md` **AD-61** (2026-09-08) | `intake_wizard_views.xml:48` (campo oculto); clasificación por contenido en `_onchange_suggest_tipo_ingreso` («la clasificación Producto/Procesado ocurre al ejecutar *Leer documento*»); AD-61: «nunca por proveedor» | `test_intake_tipo_ingreso_content.py` (clasificación por contenido, no por RUT/historial) | Código (local = remoto, hash) | **CORREGIDO Y VERIFICADO** (en código) | El campo técnico sigue existiendo (oculto) y existe wizard de reclasificación (AD-73); **V3 (navegador) no ejecutada** |
| **R03** | 02-sep | Subproducto (general) | «Había corregido el subproducto» | El texto de producto del documento se resuelve a `madenat.subproducto` sin bloquear la ingesta y sin crear `product.product` | `04_DECISION_LOG.md` **AD-ING-001 / AD-ING-002** (2026-08-31) | `mixin_lumber_ingest.py:273-297` `find_or_create_lumber_subproducto` (normaliza → busca por `code` → luego por `name =ilike` → autocrea); asignación por línea en `madenat_guia_processing.py:1761,1778`; **bloqueo al enviar a stock si hay líneas sin subproducto** (`:2194-2203`) | Cobertura de subproducto en `test_guia_processing.py`; sin prueba del caso reportado | Código (local = remoto, hash) | **IMPLEMENTADO, PENDIENTE DE VALIDACIÓN** | La corrección documentada es **anterior** (2026-08-31) al reporte del 02-sep: **no se acreditó** que el defecto reportado fuese éste, ni el caso concreto. El bloqueo `:2194-2203` produce un rechazo **al final** (al enviar a stock) y es candidato a revisar |
| **R04** | 02-sep | Packing (Procesado) | «Estaba trabajando en mostrar el packing en fracciones» | El packing se presenta en fracciones **sin** alterar los valores usados en el cálculo (sin conversiones dobles ni cambio de unidades) | Sin entrada canónica específica | `utils_uom.decimal_inch_to_fraction_simple`; wrapper `madenat_guia_processing.py:512-514` `_get_fraction_text` (`denominator=8`); constraint de octavos `_check_imperial_fractions` (`:520-577`, **solo escribe en log**, no bloquea); nominales `_get_nominal_dimension` (`:3594+`) | Cobertura de utilidades de fracción (`parse_fraction_to_decimal_inch`); **no existe** prueba de la presentación del packing en fracciones en la Consola | Código (local = remoto, hash) | **PARCIAL** | La conversión y la presentación existen para dimensiones nominales/visuales, pero **no se acreditó** en la Consola. `_check_imperial_fractions` no emite señal visible al operador (solo `_logger.warning`) |
| **R05** | 07-sep (correo) | **Fátima** · RUT 77.245.870-3 | «Al final dice operación no válida» | El documento se lee; guía y packing se asocian; se extraen los datos exigidos; el ingreso avanza sin el rechazo reportado | Copias identificables: `muestras_documentos_ingreso/07-09-2026/Guia 41994.pdf` + `41994.xls` (packing `SUB PRODUCTO / ESPESOR / ANCHO / LARGO mm / FILAS / COLUMNAS / PIEZAS / VOLUMEN M3`; 14 partidas; total declarado **50,495625 m³**, guía **50,496 m³**) | `_parse_excel_data_core` (`:3488+`) → `_validar_y_enriquecer_lineas`; sin regla específica de proveedor (por diseño) | **Sin prueba con el archivo real**: no hay fixture de Fátima; el par guía+packing no se usa en ningún test | Documental (archivos) + código | **NO ACREDITADO** | No hay registro de esta guía en el TEST remoto (0 registros de Fátima). Falta: (a) confirmar que los archivos del 7-sep son éstos; (b) reproducción autorizada del par guía+packing y captura del mensaje literal |
| **R06** | 07-sep (correo) | **Ferramenta** · RUT 77066489-6 | «Dice operación no válida al final» | Ídem R05 sobre el par guía 26270 + packing de cepillado | Copias identificables: `07-09-2026/26270.pdf` (servicio de cepillado, **57,8400 m³**) + `26270.xlsx` = `FACTURACION PACKING LIST 03-09-2026 MADENAT (cepillado) 47 (1).xlsx` (mismo hash md5; total **57,839556 m³**, 3201 piezas). `CANON` sin entrada específica | `_parse_packing_excel` (`:3251-3304`) → `_parse_excel_data_core`; `_check_guide_duplicate` (`reception_parser.py:32+`) lanza UserError de **guía duplicada**; `find_or_create_lumber_subproducto` | Fixture textual `madenat_lumber_core/tests/fixtures/26270.txt` + `test_supplier_resolution.py` / `test_reception_supplier_rut_extraction.py` (RUT/región, **no** el packing real). La corrida dirigida 88/88 (AD-102) **no cubre** este par | Código + documental + **TEST remoto** (único registro real: guía 26270 `validated`) | **NO ACREDITADO** | El único registro real del TEST remoto es esta guía, ya `validated` el 2026-10-06, con `vol_comercial_pdf=57.840` y `vol_shipment_m3=48.009`: **no** hay evidencia de que un ingreso nuevo del par se complete sin rechazo. La guía se reenvió el 7-sep tras haber sido reportada el 2-sep: la **guía duplicada** es un candidato (§17.14.3 H-2). Reproducción autorizada pendiente |
| **R07** | 07-sep (correo) | **Ferramenta** · guía 26270 | «Calcula el volumen solo de embarque, no el del packing; **deben ir los dos volúmenes**» | Se identifican y muestran por separado: volumen de guía, volumen de packing y volumen de embarque, con su diferencia | Medición documental: guía **57,8400 m³** vs packing **57,839556 m³** (Δ 0,000444); el registro del TEST remoto tiene `vol_shipment_m3=48.009` (ni guía ni packing) | Campos en `madenat.guia.processing`: `vol_comercial_pdf` («Vol. Guía PDF»), `packing_volume_declared_m3`, `sum_vol_documental_m3`, `vol_shipment_m3`, `diff_pdf_packing_m3`, `diff_packing_lineas_m3`, `documental_conciliation_state` (computes `:1005-1072`); espejo en `intake_console.py:218-230, 792-797`; **mostrados** en la Consola («Volúmenes y diferencias», `intake_console_views.xml:273-281`) | `test_parse_excel_core.py::test_packing_declared_totals_persisted` (**42,132 m³ / 2244 pzs / 8 paq.** = valores del packing de la guía 95083); `::test_vol_documental_m3_written`; `::test_sum_vol_documental_m3` | Código + TEST remoto (lectura) | **IMPLEMENTADO, PENDIENTE DE VALIDACIÓN** | El mecanismo existe y está probado a nivel unitario, **pero** el único registro real del remoto tiene `packing_volume_declared_m3` **vacío**, `sum_vol_documental_m3 = 0` y `documental_conciliation_state='partial'` (creado 2026-09-08, antes de estas columnas). **No** se acreditó con un documento Ferramenta real. Falta ejecutar el par en la Consola y decidir qué volumen es «operativo» |
| **R08** | 07-sep (correo) | **Byc** = Blocks & Cutstock S.A. (BC-LUMBER) · RUT 96.862.800-3 | «Operación no válida» | Ídem R05 | Copias identificables: `07-09-2026/95083 .pdf` (guía; `TOTAL VOLUMEN 42,132` · 2244 piezas · 8 paquetes) + `95083 Final.xls` / `95083 (1) (1).xls` (PACKING LIST con `Nº Ticket … Esp. / Anc. / Lar. / Pzas Paq. / Volumen Paq. / Cantidad Paquetes`) | `_parse_excel_data_core` (detección genérica de cabecera) + `_persist_packing_declared_totals` | `test_parse_excel_core.py::test_xls_blanks_abbreviated_headers` (**reproduce este formato**: cabecera abreviada + decimales con coma → 1 línea, `Volumen 5.226`, `Espesor 31,75`, `Ancho 146,1`, `Largo 4,877`); `::test_packing_declared_totals_persisted` usa **42,132 / 2244 / 8** (totales reales de esta guía) | Código (local = remoto, hash) | **IMPLEMENTADO, PENDIENTE DE VALIDACIÓN** | El detector y la persistencia de totales están cubiertos con la **estructura** del archivo (fixture sintético), **no con el archivo de Byc**. No hay registro de esta guía en el TEST remoto; **V3** no ejecutada |
| **R09** | 07-sep (correo) | **JCE** · RUT 96.547.890-6 | «No lee el documento» | El documento se lee y produce líneas utilizables (o un diagnóstico explícito y accionable) | Copias identificables: `07-09-2026/GDE 95806.pdf` (= `2026-08-21T10_47_21_T52F95806 .pdf`, mismo md5; guía de despacho 95806, BLANKS 5/4X5.3/8, 59,964 m³, 12 paq., 2772 pzs) + `GDE 95806.xls` / `NVTA881333 (2).xls` («NOTA DE VENTA INTERNA/…», Nº 881333; cabecera `Etiqueta / Cat.Certific. / Esc. Fact / Pzas / VOL. / Producto / Est. / Orden / Item / Marca / Precio / Moneda`; total 12 paq. / 2772 pzs / **59,964 m³**) | `_parse_excel_data_core` **sí lee** el documento y expone `dimensions_raw`; la línea se **rechaza** después en `_validar_y_enriquecer_lineas` con la regla `REQUIERE_DIMENSIONES_SEPARADAS` y se construye diagnóstico (`_build_rejection_diagnostic`) | `test_parse_excel_core.py::test_nota_venta_dimensions_raw_rejected_with_diagnostic` — **confirmado por prueba**: 1 línea leída, `Espesor/Ancho/Largo = 0`, `validas = []`, `rechazos[0]['rule'] = 'REQUIERE_DIMENSIONES_SEPARADAS'`, mensaje con «No se creó ninguna línea». PDF genérico: `madenat_ingestion_engine::test_generic_pdf_table` (`test_tabla_una_fila_volumen` reproduce este documento: 59,964 m³, `MC-0523-140`) | Código (local = remoto, hash) | **NO ACREDITADO** (documento leído, **0 líneas creadas por diseño**) | **Evidencia fuerte**: el formato «Nota de Venta / dimensiones combinadas» está **explícitamente rechazado** (Opción C) y no se promueve a líneas ⇒ el síntoma «no lee el documento» es reproducible en la práctica. **Requisito abierto**: o se normaliza `Esc. Fact` a espesor/ancho/largo, o se informa al usuario que ese packing no es ingerible. **Decisión no tomada** |
| **R10** | 07-sep (correo) | **JCE** · RUT 96.547.890-6 | «Operación no válida» | Ídem R05 | Ídem R09 | El rechazo se materializa como `UserError` desde `_parse_packing_excel` (`:3284-3287`) con el diagnóstico de rechazo | Ídem R09 | Código (local = remoto, hash) | **NO ACREDITADO** | Mismo bloqueo que R09. La expresión «operación no válida» **no** existe literalmente en el código ni en las traducciones desplegadas (§17.14.3 H-1) |
| **R11** | 07-sep (correo) | **Arauco** (Maderas Arauco S.A.) · RUT 96.510.970-6 | «Operación no válida» | Ídem R05, incluyendo el packing | Copias identificables: `07-09-2026/HLZF75_4495589.pdf` (guía de despacho electrónica Nº 4495589) + `PACKING HLZF75 (1).pdf` (**packing en PDF**, no Excel). **Réplica del fixture** `madenat_lumber_intake/tests/fixtures/HLZF75_4495589.pdf` (mismo archivo dentro del repo de tests) | Extractor genérico de tablas PDF `_extract_generic_pdf_table` + `document_extractor.extract_document`. El flujo **Normal (Procesado)** exige **packing Excel** (`_parse_packing_excel` → `pd.read_excel`); el **packing PDF** se procesa por la ruta de **Volúmenes** (`HLZF75_4495589.pdf` se usa en `test_intake_volume_detail_pieces.py` y `test_reopen_oc_reextraction.py`) | `test_generic_pdf_table.py::test_tabla_12_filas_lotes_mixtos` (refs `3540383149`, `PK45738`, 12 líneas, 40,300 m³ — estructura del packing real de Arauco); `test_no_hardcodeo_documentos_known` (el código no contiene los números de documento); intake: fixtures reales de la guía 4495589 | Código (local = remoto, hash) | **NO ACREDITADO** | **Ambigüedad de modalidad**: una guía de Arauco con packing PDF no encaja en el flujo Normal (Excel obligatorio) y sí en Volúmenes; el mensaje que ve el usuario depende de la modalidad. No hay registro de esta guía en el TEST remoto. Requiere decisión funcional y reproducción |
| **R12** | 07-oct (AD-102) | Retorno de servicio (Procesado) | Confirmación Sí/No/vacío **no bloqueante** + imputación posterior | El campo persiste Sí, No y vacío (vacío = pendiente ≠ No) y **no** bloquea el envío a stock | `04_DECISION_LOG.md` **AD-102**; `12_FLUJOS_INGESTA.md` §11.9; `19_IMPUTACION_SV_Y_PROCESADORES.md` §19.9 | `madenat_guia_processing.service_return_confirmation`; proxy `intake_console.py` (compute+inverse) y `service_return_in_scope`; radio en `intake_console_views.xml:238-245` (`invisible="not service_return_in_scope"`); **guard bloqueante eliminado** (`_assert_service_return_confirmed` ya no existe) | `madenat_lumber_intake/tests/test_service_return_confirmation.py` (**13** pruebas): Sí/No conservados, vacío≠No, vacío no bloquea, permisos reales, sin imputación automática, proxy editable. Ejecutado **88/88 sobre `madenat_test`** (2026-10-08) | Código + prueba V2 (**no** V3) | **IMPLEMENTADO, PENDIENTE DE VALIDACIÓN** (V3) | **V3 (navegador) NO ejecutada** (`GUION_VERIFICACION_NAVEGADOR.md`, guía 19827). Prueba física (radio y persistencia en pantalla) pendiente |
| **R13** | 07-oct (AD-102) | Imputación SV (I2) | Reglas de aplicación y reversa de la imputación documental | `action_apply` exige destino «Sí»; `action_pending` no; Sí→No/vaciar rechazado con imputación `applied` y permitido tras reversar; sin efectos de stock/ledger | `04_DECISION_LOG.md` AD-102; `19_IMPUTACION_SV_Y_PROCESADORES.md` §4/§5 | `madenat_lumber_logistics/models/madenat_sv_imputation.py`: `_i2_check_destination_is_service_return` + llamada en `action_apply`; relación inversa `sv_imputation_ids`; regla Sí→No | `test_service_return_imputation_guard.py` (**8**), `test_service_return_pending_filter.py` (**9**), regresiones `test_sv_imputation_i2.py` (13) y `test_sv_imputation_candidates.py` (12); **88/88** sobre `madenat_test` | Código + prueba V2 | **IMPLEMENTADO, PENDIENTE DE VALIDACIÓN** (V3) | **Límites conservados**: concurrencia **no** acreditada; filtro **sin** cobertura parcial; **V3** no ejecutada; **I3/I5** fuera de alcance |
| **R14** | 08-oct | Ingreso de Madera (UI) | Resumen en 2 columnas; Evidencia documental en 3 columnas; packing a todo el ancho; «Aplicar cambios» debajo | La disposición se observa en pantalla sin romper campos, unidades ni permisos | `APPLY_AB_UI_20261008/RESUMEN.md`; `02_CONTINUIDAD.md` §17.13.3; `03_TESTS.md` §12.6.3 | `intake_console_views.xml`: resumen 2 columnas; `group string="📄 Evidencia documental" col="3"` (`:260`); columnas «Documentos» / «Volúmenes y diferencias» / «Packing y conciliación»; detalle del packing a todo el ancho | Verificación **estructural read-only** (archivo + vista cargada: id **1867** en la base local, id **1660 en el TEST remoto**, con `Aplicar cambios` y `Evidencia documental`) | Código + TEST remoto (vista cargada) | **PARCIAL** (estructura verificada, **visual pendiente**) | La observación **visual** (`UI-1..UI-6`, incl. responsive) **no** se ejecutó en ninguna base: la verificación estructural **no** sustituye la observación del operador **ni** se reemplaza por SQL |
| **R15** | posterior al despliegue | Consola (navegador) | `UncaughtPromiseError > OwlError` · `TypeError: Cannot read properties of undefined (reading 'includes')` en `get urlRelation` · `Many2OneField.template`; URL mostrada `localhost:8069` | El formulario de la Consola abre y renderiza sin excepción de cliente | Sin entrada canónica | `urlRelation` pertenece al cliente web de Odoo (**no** existe en `custom_addons`: búsqueda sin resultados). **Comprobación estática ejecutada**: en las vistas de la Consola (`intake_console*.xml`) **no** hay ningún `<field>` sin campo correspondiente en el modelo, y `intake_sv_reversible_rebaja_id` **sí** está definido en `madenat.guia.processing` (`intake_console_sv.py:309-318`) ⇒ **no se halló** un campo huérfano que explique el fallo | **Ninguna**: no hay navegador y el servicio local 8069 no es operativo desde esta distro | Código (estático) | **NO REPRODUCIDO** · causa **NO confirmada** | Condiciones para reproducir: navegador, base, usuario, acción/menú de entrada, campo y registro. **Hipótesis NO confirmadas** (a verificar, no documentar como causa): (a) assets/caché de vista desactualizados tras la actualización de módulos; (b) metadatos de relación no cargados por módulo ausente; (c) widget incompatible con el campo. **No** se borran assets ni se modifica JavaScript global como medida preventiva |
| **R16** | 08-oct | Despliegue TEST remoto vs desarrollo local | «Actualización del TEST remoto con carga de módulos finalizada y código de salida 0» | Lo validado localmente corresponde a lo desplegado | `02_CONTINUIDAD.md` §17.13 (aplicación en el desarrollo) | Manifiesto SHA-256 de **314** archivos: **0 discrepancias**; el remoto tiene los mismos 4 módulos `installed` (core 18.0.6.5.0, intake 18.0.0.11.0, logistics 18.0.1.6.0, ingestion_engine 18.0.1.1.0); columna `service_return_confirmation` y vistas nuevas **presentes** | **No** se ejecutaron pruebas en el remoto (no autorizado); de solo lectura se confirma esquema y vistas cargadas | Código (hash) + TEST remoto (esquema/vistas) | **PARCIAL** | **Sí** corresponden los archivos de código y el esquema; **no** está acreditado que el remoto pase las pruebas (la corrida 88/88 fue **local**). Además `custom_addons` **no** es repositorio git en el remoto (sin trazabilidad de versión) y hay **39 archivos legado** solo allí. **No** se declara el remoto «validado por traslado» |

#### 17.14.3 Hallazgos y contradicciones (resueltas o pendientes)

**H-1 — «Operación no válida» no existe como texto del sistema (resuelto).** Búsqueda literal en
`custom_addons` (`.py/.xml/.po`) y, en el TEST remoto, sobre `/opt/odoo18-test/odoo` y
`/opt/odoo18-test/addons` (`-i`, patrón tolerante `no v.lida`): **0 coincidencias** en el código
MADENAT; en el núcleo solo aparecen cadenas distintas («Acción no válida» en `board` y
`point_of_sale`; «Acción no válida para generar una URL» en `mail_group`; «…no válida» de vistas,
pagos, etc.). **Conclusión:** la expresión es una **paráfrasis del usuario**; **no** puede
documentarse como mensaje del sistema ni usarse para atribuir causa técnica.

**H-2 — Mensajes reales que el usuario pudo ver «al final» (candidatos, causa NO confirmada).**
Verificados por lectura de código; ninguno se declara causa hasta tener el texto literal o la captura:
1. **Guía duplicada** — `reception_parser._check_guide_duplicate` (`:32-151`) y la búsqueda en
   `madenat.guia.processing` (`:153-200`): «⚠️ La guía N° X ya fue registrada en el sistema (Guías
   Procesadas). No se permite subirla nuevamente…». **Relevante**: los archivos del 7-sep ya se
   habían intentado el 2-sep.
2. **Rechazo del packing** — `REQUIERE_DIMENSIONES_SEPARADAS` + «No se creó ninguna línea»
   (`_build_rejection_diagnostic`, `madenat_guia_processing.py:3284-3287`). Aplica a Nota de Venta /
   dimensiones combinadas (JCE).
3. **Subproducto faltante al enviar a stock** — «Hay N línea(s) sin subproducto asignado … antes de
   aprobar el ingreso a stock» (`:2194-2203`): rechazo **al final**, tras completar el packing.
4. **Estado inválido** — «❌ Estado inválido. Verifique la guía antes de procesar.» (`:1152`).
5. **Sin volumen válido en el PDF** — «⛔ Ninguna línea del PDF tiene volumen válido (> 0)» (`:1434`).
6. **Aviso de perfil de lectura** — `intake_wizard.py:251-262` (**no** es rechazo, pero en Odoo un
   `warning` devuelto por un método **interrumpe** la acción hasta pulsar «OK»).
**Acción requerida:** obtener de Cristhian el **texto literal o la captura** del mensaje por proveedor.
Sin eso, R05/R06/R08/R10/R11 **no** pueden cerrarse.

**H-3 — Contradicción documental sobre los adjuntos (resuelta parcialmente).** El correo del 7-sep
reporta **10 adjuntos**; **no** existe expediente que los contenga como tales (no hay `*.eml`). Sí
existen **copias identificables** en `muestras_documentos_ingreso/07-09-2026/` (**15** archivos, con
**duplicados por hash**: `GDE 95806.pdf` = `2026-08-21T10_47_21_T52F95806 .pdf`; `26270.xlsx` =
`FACTURACION PACKING LIST 03-09-2026 MADENAT (cepillado) 47 (1).xlsx`; y `95083 (1) (1).xls` frente a
`95083 Final.xls` / `Copia de 95083 (1) (1).xls`, con hashes **distintos**), con fechas de descarga
2026-09-07/08/12. Se usan como **copias identificables**, **no** como sustitutos silenciosos: queda
pendiente que Cristhian **confirme el juego exacto**. **No** se pide su reenvío por defecto.

**H-4 — «Ambos volúmenes» (R07): mecanismo implementado, dato real ausente (parcial).** El modelo y la
UI ya separan `vol_comercial_pdf` (guía), `packing_volume_declared_m3` (packing),
`sum_vol_documental_m3` (líneas) y `vol_shipment_m3` (embarque), con `diff_pdf_packing_m3`,
`diff_packing_lineas_m3` y `documental_conciliation_state`, y hay pruebas unitarias. **Pero** el único
registro real del TEST remoto (guía 26270) tiene el **volumen de packing vacío** y la **suma de líneas
en 0**, con estado `partial`: **no** se puede afirmar que «el packing ya funciona». Medición del par
Ferramenta: guía **57,8400** vs packing **57,839556** (Δ **0,000444** m³); el valor almacenado como
«Vol. Embarque» es **48,009 m³** y **no coincide con ninguno de los dos**. **Causa del 48,009 NO
determinada**: `_compute_vol_shipment_m3` (`:448-506`) cae a `vol_purchase_m3` (nominal) cuando no hay
geometría; el desvío observado exige revisar las **líneas reales** de esa guía.

**H-5 — Ambigüedad de modalidad con packings PDF (pendiente).** El flujo **Normal** exige **packing
Excel** (`_parse_packing_excel` → `pd.read_excel(attachment…)`); el **packing PDF** se procesa por la
ruta de **Volúmenes** (extractor genérico de tablas PDF). La guía de Arauco del 7-sep trae su packing
**en PDF**. **No** hay evidencia de que el usuario eligiera la modalidad correcta ni de que el sistema
lo guíe. **No** se documenta como defecto del parser.

**H-6 — Entornos (limitaciones confirmadas).** (a) El servicio **8069 no era operativo** desde la
distro del entorno de trabajo ⇒ **no** se reprodujeron pruebas locales. (b) `custom_addons` en el TEST
remoto **no** es repositorio git ⇒ **sin trazabilidad de versión**; además hay **39 archivos legado**
que no existen en local, **dos de ellos muertos y no referenciados** (verificado:
`madenat_lumber_logistics/models/lumber_container_rollover_wizard.py` **no** se importa —el import vive
en `wizards/__init__.py`— y `madenat_lumber_intake/security/madenat_intake_security.xml` **no** figura
en el `__manifest__.py`). **No** se elimina nada: su retiro requiere autorización.

**H-7 — Afirmaciones previas: corrección de estatus (no se perpetúan como hechos).**

| Afirmación previa | Estatus tras la auditoría |
|---|---|
| «Todos los formatos están corregidos» | **NO ACREDITADO.** 5 de 5 proveedores identificados, **0** con ingesta real acreditada (R05–R11) |
| «El packing ya funciona en fracciones» | **PARCIAL.** Existe conversión/presentación y wrapper `_get_fraction_text`; **no** acreditada en la Consola (R04) |
| «No son fallos, sólo advertencias» | **No verificable en general.** Hay `UserError` **bloqueantes** en el flujo (H-2 nº 1/2/3/4/5); el aviso del perfil **sí** interrumpe hasta pulsar «OK» |
| «No llegaron los adjuntos» | **Refutable por evidencia documental**: hay copias identificables (H-3) |
| «El sistema está listo para probar» | **Sólo parcialmente.** El TEST remoto tiene el código y el esquema, pero **V3 no está ejecutada** y **R15 sigue abierto**: **no** debe invitarse a probar un flujo que puede estar bloqueado |
| «El OwlError ya está resuelto» | **Sin evidencia** (R15: NO REPRODUCIDO, causa NO confirmada) |

#### 17.14.4 Límites conservados (sin cambios)

Se mantienen **intactos** y **no** se actualizan sin evidencia nueva: **9 fallas preexistentes**
(`03_TESTS.md` §12.2 y §12.6.4), **concurrencia no acreditada**, **filtro «Retornos sin imputación
aplicada» sin cobertura parcial**, **I3/I5 fuera de alcance**, **V3 (navegador) pendiente** e
**instalación en base limpia pendiente**. Ninguno se elimina ni se reescribe en esta intervención.

#### 17.14.5 Acciones propuestas (identificadas, NO ejecutadas)

Prioridad **P0** = bloquea cualquier cierre; **P1** = habilita el cierre de un requisito;
**P2** = orden y trazabilidad. **Todas** requieren autorización explícita.

| # | Acción | Alcance concreto | Requisitos que habilita |
|---|---|---|---|
| **P0.1** | Obtener el **texto literal** (o la captura) del mensaje que ve Cristhian, **por proveedor** | Sin cambios técnicos; se pide a Cristhian | R05, R06, R08, R10, R11 |
| **P0.2** | Confirmar el **juego exacto** de los 10 adjuntos del 7-sep | cotejo contra `muestras_documentos_ingreso/07-09-2026/` (15 archivos, hashes md5 ya calculados) | R05–R11 |
| **P0.3** | Reproducir **R15 (OwlError)** con condiciones mínimas registradas | navegador + base + usuario + acción/menú + campo + registro + captura de consola; **no** borrar assets ni tocar JS global | R15 (bloquea invitar a probar la Consola) |
| **P1.1** | Reproducción **autorizada** del par **Ferramenta** (26270.pdf + 26270.xlsx) en base de pruebas | crea registros; medir los 3 volúmenes y explicar el origen de `vol_shipment_m3 = 48,009` revisando las líneas reales | R06, R07 |
| **P1.2** | Reproducción **autorizada** de **Fátima** (41994.pdf + 41994.xls) y **Byc** (95083 .pdf + 95083 Final.xls) | ídem; verificar armado guía↔packing y totales declarados | R05, R08 |
| **P1.3** | **Decisión funcional** sobre Nota de Venta (JCE) | normalizar `Esc. Fact` (`5/4x5.3/8x16` → espesor/ancho/largo) **o** mensaje explícito «packing no ingerible» (hoy el usuario ve un rechazo) | R09, R10 |
| **P1.4** | **Decisión funcional** sobre **packing PDF** (Arauco) | exigir Excel / aceptar la ruta de Volúmenes / añadir lectura de packing PDF en el flujo Normal | R11 |
| **P2.1** | Ejecutar **V3** completo del guion (`GUION_VERIFICACION_NAVEGADOR.md`) sobre `8069` / `madenat_test` | incluye UI-1..UI-6, A-1..A-6 y B-1..B-5 | R04, R12, R13, R14 |
| **P2.2** | Retirar/archivar los **39 archivos legado** del TEST remoto | **requiere autorización**; no se elimina nada sin ella | R16 |
| **P2.3** | Dar **control de versión** a `custom_addons` del TEST remoto | hoy sin trazabilidad (git solo del repo `/opt/odoo18-test`, ilegible) | R16 |
| **P2.4** | Cerrar los pendientes de **concurrencia** y del **filtro sin cobertura parcial** | ya catalogados en `05_BACKLOG.md` | R13 |

**No** se propone, y no debe hacerse: desactivar validaciones legítimas para hacer desaparecer un
mensaje; borrar assets o modificar JavaScript global como medida preventiva; ni reinstalar/actualizar
módulos del TEST remoto para esta auditoría.

> **Nota de vigencia:** los estados de la matriz §17.14.2 y los hallazgos §17.14.3 quedan
> **parcialmente sustituidos** por §17.15 (revalidación con la biblioteca de muestras). La historia se
> conserva; las correcciones se registran en §17.15.6.

### 17.15 Revalidación con la biblioteca de muestras y reconstrucción de las pruebas (2026-10-08, 2.ª pasada)

**Antecedente incorporado (declaración expresa de Mauricio).** «Se hicieron pruebas con **todos** los
ingresos y los formatos probados están en `muestras_documentos_ingreso`, **fuera** de `custom_addons`.»
Esta declaración se registra como **antecedente explícito** y **no** como aprobación automática: lo que
sigue reconstruye **qué se probó, con qué archivo, en qué versión y entorno, hasta qué etapa y con qué
resultado**.

**Principio metodológico aplicado.** *Evidencia no localizada ≠ prueba no realizada*; *archivo presente
≠ prueba aprobada*; *prueba de lectura ≠ ingreso completo*; *resultado histórico local ≠ resultado
actual remoto*. La primera pasada (§17.14) declaró «NO ACREDITADO» varios casos **por una búsqueda
incompleta** (limitada a `custom_addons` y sin inspección de respaldos de base). Esa conclusión se
**corrige** aquí con evidencia localizada.

#### 17.15.1 Ruta real de la biblioteca y del resto de fuentes

| Fuente | Ruta real | Verificación |
|---|---|---|
| Raíz del proyecto | `/home/viruco/dev-stack/odoo/odoo-18-ce` | **No** es repositorio git (`fatal: not a git repository`) |
| Repositorio | `…/odoo-18-ce/custom_addons` | Rama `feat/guia-correccion-documental-preservada-20261002`, HEAD `e302c48…` |
| Documentación rectora | `…/custom_addons/madenat_lumber_docs` | `CANON/`, `WIKI/`, `LEGADO/`, `RAW/` |
| **Biblioteca de muestras** | **`…/odoo-18-ce/muestras_documentos_ingreso`** (fuera de `custom_addons`, hermana de `custom_addons`) | **63 archivos**, **52 únicos por SHA-256**, en 4 subdirectorios: `07-09-2026/` (15), `Ejercicio Completo Cristhian Elgueta/` (31), `excel_packing/` (9), `guias_pdf/` (8) — hay **3 pares duplicados exactos** y **4 archivos de bloqueo de Office** (`~$…`, 165 B, idénticos entre sí) |
| Expedientes de prueba | `AUDIT_*`, `UAT_*`, `IMPL_*`, `FIX_*`, `FASE_*`, `CIERRE_*`, `INCIDENTE_*`, `APPLY_*`, `pre02_*`, `madenat_dev_*`, `oracle_f31_*`, `f31_test_*`, `backups/`, `_archive_*` | Inspeccionados: **54 directorios de primer nivel** |
| Respaldos de base (evidencia persistente) | `BACKUP_AB_APPLY_20261008/db/madenat_test_20261008_092958.dump` (**base local**, 2026-10-08 09:29); `APPLY_AB_UI_20261008/retired/db/srvretab_{base,gate,test}_20261007.dump`; `backups/**/madenat_test*.dump` (6 más); `APPLY_BUSQUEDA_INTAKE_20261007/backup/madenat_test_pre.dump` | Inspeccionados **con `pg_restore` en solo lectura sobre el archivo** (sin restaurar, sin crear bases) |
| Dump SQL histórico | `madenat_test_antes_limpieza.sql` (2026-08-20) | Solo **1** cabecera de guía (24356) ⇒ las pruebas de septiembre son **posteriores** |

**Limitación declarada:** el **correo electrónico original y sus 10 adjuntos** no existen como
expediente (no hay `*.eml`); lo que existe es la **biblioteca** con copias identificables y los
**registros de base** que prueban su uso.

#### 17.15.2 Inventario de la biblioteca (resumen: pares y variantes por CONTENIDO)

| Proveedor | Guía | Guía (archivo · SHA-256 abreviado) | Packing (archivo · SHA-256) | Documento de servicio |
|---|---|---|---|---|
| **Fátima** (RUT 77.245.870-3) | 41994 | `07-09-2026/Guia 41994.pdf` · `4d8e0e8b63ea1382` | `07-09-2026/41994.xls` · `99fe59fffb896a60` (2 filas de cabecera, `SUB PRODUCTO`, `FILAS/COLUMNAS/PIEZAS/VOLUMEN M3`, total **50,495625**) | guía declara **50,496 m³** |
| **Ferramenta** (RUT 77066489-6) | 26270 | `07-09-2026/26270.pdf` = `26270.pdf` (raíz) · `04226af88ca8ae0d` | `07-09-2026/26270.xlsx` = `FACTURACION PACKING LIST 03-09-2026 MADENAT (cepillado) 47 (1).xlsx` = `26270.xlsx` · `0f843ece8b1b0c8d` | servicio de cepillado **57,8400 m³**; packing **57,839556 m³** (3201 piezas) |
| **Byc = Blocks & Cutstock S.A.** (BC-LUMBER, RUT 96.862.800-3) | 95083 | `07-09-2026/95083 .pdf` · `b581a283d227bead` | `95083 Final.xls` · `b5c474ae69a69ddf` y `95083 (1) (1).xls` · `191161be055d117e` (**variantes no idénticas**) | guía `TOTAL VOLUMEN 42,132` · 2244 pzs · 8 paq. |
| **JCE** (RUT 96.547.890-6) | 95806 | `07-09-2026/GDE 95806.pdf` = `2026-08-21T10_47_21_T52F95806 .pdf` · `17a57189c8361233` | `GDE 95806.xls` · `a9049815e7ed0b1e` y `NVTA881333 (2).xls` · `ec064c4bbaecf5ea` (ambos «NOTA DE VENTA INTERNA/…» **Nº 881333**, 12 paq. / 2772 pzs / **59,964 m³**) | guía 95806: BLANKS 5/4X5.3/8, `VOL.TOT. 59,964`, OC `MC-0523-140`, T.C. 923,23 |
| **Arauco** (Maderas Arauco S.A., RUT 96.510.970-6) | 4495589 | `07-09-2026/HLZF75_4495589.pdf` · `98382981de062b1b` | `07-09-2026/PACKING HLZF75 (1).pdf` · `1fcebe7f814873ac` (**packing en PDF**) | guía 4495589 (HLZF75), 07-sep-2026 |
| **Ferramenta** (ejercicio) | 19820/19826/19827/19846 | `Ejercicio Completo…/GDE Guía de Despacho 19820/19826/19827/19846.pdf` | `FACTURACION PACKING LIST 06-10-2025 (1)…(02-10-2025 (2))…(02-10-2025 (1))…(01-10-2025 (2))…xlsx` | servicios de cepillado |
| **Fátima** (ejercicio) | 39485/39491/39493/39500/39509/39510/39519/39522 | `Ejercicio Completo…/Guia 39485/39491/39493/39500/39509/39510/39519/39522.pdf` | `39491/39493/39500/39509/39510/39519/39522 (1).xls` | ingreso por Producto |
| Otros (regresión) | 97183, 40030, 40040, 40597 | `guias_pdf/GD 97183.pdf` (= `293.49 Kb.pdf`), `Guia 40030.pdf`, `Guia 40040.pdf`, `Guia 40597.pdf` (= `120.13 Kb.pdf` = `Guia 40597 (1).pdf`) | `excel_packing/42.50 Kb.xls`, `Packing GD 97183 - W (1).xls`, `40030.xls`, `40040.xls`, `40597.xls`, `65.50 Kb.xls` | **40597 = «caso base recomendado»** del plan de pruebas embebido en `madenat_lumber_core/regen_docs_madenat.sh` (PDF 55.665 vs Excel 55.821 m³) |

**Duplicados exactos (no se borran, se clasifican):** `26270.pdf`×2 · `26270.xlsx`×3 · `GDE 95806.pdf` =
`2026-08-21T10_47_21_T52F95806 .pdf` · `293.49 Kb.pdf` = `GD 97183.pdf` · `Guia 40040 (1).pdf` =
`Guia 40040.pdf` · `120.13 Kb.pdf` = `Guia 40597.pdf` = `Guia 40597 (1).pdf` · 4 archivos `~$…`.

**Copia dentro del proyecto (búsqueda por hash de los 52 únicos):** **solo 1** archivo tiene copia
byte-idéntica dentro de `custom_addons`: **`HLZF75_4495589.pdf`**, promovido a **fixture real** en
`madenat_lumber_intake/tests/fixtures/HLZF75_4495589.pdf`. Los demás **no** se convirtieron en fixture:
su evidencia es la **biblioteca + los registros de base** y, en varios casos, **fixtures derivados**.

**Fixtures derivados del documento real (no byte-idénticos, pero con cabecera/valores del original):**

| Fixture | Documento de origen | Correspondencia verificada |
|---|---|---|
| `madenat_lumber_core/tests/fixtures/26270.txt` | `26270.pdf` (Ferramenta) | Transcripción del texto: `RUT: 77066489-6`, `GUÍA DE DESPACHO ELECTRÓNICA`, `Nº: 26270`, `Fecha: 03/09/2026`, cliente MADENAT |
| `_build_xls_blanks_bytes()` en `test_parse_excel_core.py` («tipo 95083») y `_packing_list_blanks_rows()` en `test_excel_table_detection.py` («Estructura tipo 95083») | `95083 Final.xls` (Byc) | Misma cabecera abreviada (`Nº Ticket / Esp. / Anc. / Lar. / Pzas Paq. / Volumen Paq. / Cantidad Paquetes / CERTFOR / Defecto`) y **mismos valores de la 1.ª fila real**: 31,75 · 146,1 · 4,877 · 231 · 5,226 · 1 · NO CERTIFICADO · S/D |
| `test_excel_table_detection.py::test_two_row_header` | `41994.xls` (Fátima) | Cabecera de 2 filas idéntica (`N°/CODIGOS/…/VOLUMEN` + `PQTE./mm./mm/mm/ M3`) y **misma 1.ª línea**: `0000000134008`, 45, 125, 4.0, 25, 8, 200, 4.5 |
| `_build_xls_nota_venta_bytes()` en `test_parse_excel_core.py` | `GDE 95806.xls` / `NVTA881333 (2).xls` (JCE) | Cabecera **idéntica** a la real (`Etiqueta / Cat.Certific. / Esc. Fact / Pzas / VOL. / Producto / Est. / Orden / Item / Marca / Precio / Moneda`) y **mismos valores reales**: `5/4x5.3/8x16`, `BLANKS 5/4X5.3/8`, 231, 4.997, ORDEN 21176, item 4, 430, `US$/M3` |
| `test_document_format.py::test_extract_pdf_con_nombre_xls` y `test_generic_pdf_table.py::test_tabla_una_fila_volumen` | `GDE 95806.pdf` (JCE) | Mismos datos de cabecera reales: `95806`, `2026-08-21`, `MC-0523-140`, `59.964`, `TOT.PAQ.:12`, `TOT PZAS.:2772`, T.C. `923.23` |
| `test_generic_pdf_table.py::test_tabla_12_filas_lotes_mixtos` | `PACKING HLZF75 (1).pdf` (Arauco) | 12 líneas, `40.300 m³`, refs `3540383149` / `PK45738` (lotes reales del packing); el módulo declara que reproduce «la estructura de los documentos reales de regresión» y que **no** hardcodea documento (`test_no_hardcodeo_documentos_known`) |

#### 17.15.3 Pruebas REALMENTE ejecutadas (localizadas en los respaldos de base)

Fuente: `BACKUP_AB_APPLY_20261008/db/madenat_test_20261008_092958.dump` = **base local `madenat_test`,
2026-10-08 09:29** (leído con `pg_restore`, sin restaurar). Todas las filas son **ejecuciones reales
registradas**, con archivo, fecha y resultado persistidos.

| # | Caso | Muestra (archivo real) | Registro persistente | Evidencia material | Etapa alcanzada |
|---|---|---|---|---|---|
| 1 | **Ferramenta · guía 26270** (servicio/cepillado) | `26270.pdf` + `26270.xlsx` | `madenat.guia.processing` id **1728**, `service`, `validated`, 2026-09-08 05:14 | **Adjuntos** `26270.pdf` y `26270.xlsx` (res_id 1728) · **17 `stock.lot`** `D<ref> <SKU> 26270` con los M3 del packing (p. ej. `D8828 PCLAT03301253700 26270` → 4,518) · **1 `stock.picking`** con `origin=26270` · `vol_comercial_pdf=57.840`, `vol_shipment_m3=48.009` | **D/E** (guardado → lotes y picking) |
| 2 | **Ferramenta · guía 19846** | `GDE Guía de Despacho 19846.pdf` + `FACTURACION PACKING LIST 06-10-2025 (1) MADENAT (cepillado) (2).xlsx` | id **1196**, `service`, `validated`, 2026-08-31 22:23 | Adjuntos con **esos nombres exactos** · **19 lotes** `… 19846` (2026-09-02) · 1 picking · **golden record** en `test_guia_processing.py::test_13_golden_record_19846_intacto` | **D/E** |
| 3 | **Ferramenta · guía 19827** | `GDE Guía de Despacho 19827.pdf` + `FACTURACION PACKING LIST 02-10-2025 (2) MADENAT (cepillado) (1).xlsx` | id **1198**, `service`, `verified`, 2026-09-01 | Adjuntos con esos nombres · **17 lotes** · 2 pickings · es la guía del **guion V3** (§12.6.3) y de `test_guia_processing_display_name.py` | **D/E** |
| 4 | **Ferramenta · guía 19826** | `GDE Guía de Despacho 19826.pdf` + `FACTURACION PACKING LIST 02-10-2025 (1) MADENAT (cepillado) (1).xlsx` | id **1256**, `service`, `validated`, 2026-09-02 | Adjuntos con esos nombres · **17 lotes** · 1 picking · citada en el código («guía de Felipe (19826)», bypass métrico) | **D/E** |
| 5 | **Arauco · guía 4495589** | `HLZF75_4495589.pdf` (**y como fixture real**) | id **15326**, `granel`, `validated`, 2026-10-01 12:50 (`vol 40.315 = 40.315`) | Lote `GRANEL 4495589` (id 3753, 2026-09-25) · pickings `EMB-01768` con `origin='4495589 [PURGADO-TEST]'` **y su reversa** (2026-09-30) · fixture **byte-idéntico** usado por `test_intake_volume_detail_pieces.py` (**motor real**) y `test_reopen_oc_reextraction.py` | **A/B/C/D** (+ E con historia de purga y reingesta) |
| 6 | **JCE · guía 95806** | `GDE 95806.pdf` | id **33151**, `granel`, `verified`, 2026-10-06 18:47 (`59.964 = 59.964`), `guide_pdf_filename='GDE 95806.pdf'` | Adjuntos del wizard de intake de 2026-10-06 (res_id 13654/13655) · fixtures derivados con los datos reales del documento | **A/B/D** (por la ruta de **Volúmenes**) |
| 7 | **Fátima · guía 39519** (ejercicio) | `Guia 39519.pdf` + `39519 (1).xls` | `lumber.reception` id **1161**, proveedor **12 = Fátima**, `verified`, 2026-08-31 22:21 | Adjuntos con esos nombres en `lumber.reception` | **D/E** (flujo Producto) |
| 8 | **Fátima · otras guías** | `Guia 41471.pdf`+`41471 (1).xls` (id 962), `Guia 41964.pdf`+`41964.xls` (id 1371) | `lumber.reception` `verified` (2026-08-29 y 2026-09-03) | Adjuntos | **D** |
| 9 | **Otros (regresión)** | `GD 97183.pdf`+`42.50 Kb.xls` (id **1244**), `Packing GD 100006 - W.xls`+`GD 100006.pdf` (id 1270), `15183.xls`+`GUIA 15183 MADENAT 02-09-2026.pdf` (id **1369**) | `lumber.reception` `verified` (sep-2026) | Adjuntos; **97183** y **15183** tienen expediente propio (`INCIDENTE_GUIA_15183_20261007/`) | **D/E** |
| 10 | Ingresos UAT (2026-10-03/05) | Archivos `UAT-INT-*` (no de la biblioteca) | `UAT-INT-PROC-20261003-01`, `UAT-INT-20261004-*`, `UAT-SV-20261003-*`, `900001`, `900002` | Adjuntos y lotes | **D/E** (evidencia de la suite UAT, no de los 5 proveedores) |

**Casos SIN registro persistente localizado** (ni en la base local, ni en el remoto, ni en los 9
respaldos inspeccionados): **`41994`** (Fátima) y **`95083`** (Byc) **como guía ingresada**. Su
evidencia es de **otro nivel**: fixture **derivado** (§17.15.2) y, en el caso de Fátima, **formato
equivalente ya ingresado** — `39519 (1).xls` (caso 7) tiene **exactamente la misma estructura** que
`41994.xls` (verificado campo a campo: `CLIENTE/FECHA/ORDEN COMPRA/GUIA DESPACHO` + cabecera de 2 filas
`N°|CODIGOS|SUB PRODUCTO|ESPESOR|ANCHO|LARGO|FILAS|COLUMNAS|PIEZAS|VOLUMEN|M.B.F.` + segunda fila
`PQTE.|mm.|mm|mm|M3`, y `M.B.F. 1362.847` en ambos). **No se atribuye** el resultado de `39519` a
`41994` como si fuera la misma ejecución: se declara **equivalencia de formato**, no identidad de prueba.

#### 17.15.4 Ferramenta 26270 — conciliación POR LÍNEA y significado de los tres volúmenes

Análisis de las **17 líneas** del registro 1728 (base local) contra el packing `26270.xlsx`:

- **`vol_purchase_m3` (total 57,840)** = Σ `pieces × espesor_mm × ancho_mm × largo_m` (geometría real).
  Coincide con: **guía PDF 57,8400 m³** y **packing 57,839556 m³** (desvío 0,000444 m³ por redondeo de
  los M3 declarados fila a fila). **Los 17 lotes** llevan el N° de LOTE del packing (`D8828…D8840`) y su
  M3 declarado ⇒ **el packing SÍ se interpretó y se usó**.
- **`vol_shipment_m3` (total 48,009)** = volumen de **EMBARQUE**, calculado por `_compute_vol_shipment_m3`
  (`madenat_guia_processing.py:448-506`) con **espesor NOMINAL** (`thickness_visual`, p. ej. `5/4"` =
  31,75 mm en lugar de los 37 mm reales) y **ancho + 1/8"** (`get_s2s_adjustment`, rama S2S/RIP):
  `vol = (e_in × (a_in + 0,125) × largo × piezas) / 1550,003096`.
  **Verificación exacta**: línea 5127 (264 pzs · 5/4" · 4 5/8" · 3,70 m) → 1,25 × 4,75 × 3,70 × 264 /
  1550,003096 = **3,742** = valor almacenado; factor implícito observado 0,82824–0,85799 según ancho,
  coherente con la fórmula. **No hay error de lectura ni de cálculo.**
- **Conclusión:** los tres valores son **correctos y de distinta naturaleza**: guía/packing/físico =
  **57,840** (real) y embarque = **48,009** (nominal comercial). La observación de Cristhian («calcula el
  volumen solo de embarque, no el del packing») se explica porque **el volumen dominante en pantalla era
  el de embarque** y porque `packing_volume_declared_m3` **no existía** cuando se creó el registro
  (2026-09-08): en la base figura **vacío** y `sum_vol_documental_m3 = 0`. **Estado: PENDIENTE DE
  PRESENTACIÓN/DECISIÓN FUNCIONAL**, no de cálculo.
- **Corrección de la 1.ª pasada:** se había declarado «causa del 48,009 NO determinada» y «no se
  acreditó que el packing funcione». **Ambas afirmaciones se rectifican**: la causa está determinada
  (fórmula de embarque) y el packing **sí** se interpretó (17 lotes con sus M3).

#### 17.15.5 Correspondencia local ↔ TEST remoto (revisada)

| Elemento | Base **local** `madenat_test` (dump 2026-10-08 09:29) | **TEST remoto** `madenat_test` (144.22.50.236, leído hoy) |
|---|---|---|
| `madenat.guia.processing` | **11** filas (19846, 19827, 19826, **26270**, **4495589**, **95806**, UAT y otros) | **1** fila: **26270** (id 17, `validated`, `57.840` / `48.009`, `26270.pdf` + `26270.xlsx`) |
| `lumber.reception` | **7** filas (97183, 41471, **39519**, 100006, 15183, 41964, 900001) | **4** filas (**100006, 100107, 100176, 15183**), todas `done` con `GD *.pdf` + `Packing GD * - W.xls` |
| `stock.lot` de la guía 26270 | **17** lotes con los M3 del packing | **17** lotes (misma composición) |
| Adjuntos de esos casos | `26270.pdf`/`26270.xlsx` + las 3 parejas del ejercicio | **solo** `26270.pdf`/`26270.xlsx` |
| Módulos/esquema | (código idéntico por hash) | `core 18.0.6.5.0`, `intake 18.0.0.11.0`, `logistics 18.0.1.6.0`, `ingestion_engine 18.0.1.1.0`; `service_return_confirmation` y vistas nuevas presentes |

**Lecturas correctas (evitando extrapolaciones):**
- **«Ferramenta 26270» está replicado en el remoto** (mismo registro, mismos 17 lotes, mismos volúmenes)
  ⇒ para **ese** caso, la evidencia **sí** cruza a TEST remoto.
- **Arauco 4495589, JCE 95806, el «Ejercicio Completo» (19846/19827/19826/39519) y Fátima/Byc** tienen
  evidencia **únicamente LOCAL**: **no** se trasladan al remoto.
- La comparación previa («314 archivos, 0 discrepancias») se mantiene **pero acotada**: midió
  `.py/.xml/.csv` de 4 módulos, con exclusiones declaradas (`__pycache__`, `_archive`, `backups`), y los
  **39 archivos solo-remoto** son legado. **No** equivale a «todo el despliegue es idéntico y validado».

#### 17.15.6 Correcciones a la 1.ª pasada (§17.14) — qué se rectifica, por qué y con qué evidencia

| # | Afirmación de §17.14 | Corrección | Evidencia |
|---|---|---|---|
| C1 | «Ninguno de los cinco formatos fue probado» / «R05–R11 NO ACREDITADO» | **Rectificado.** Hay **pruebas reconstruidas**: 6 casos con **archivo real** y registro persistente (§17.15.3) + **fixtures derivados** del documento real (§17.15.2). La 1.ª pasada buscó **sólo** en `custom_addons` y **no** inspeccionó la biblioteca externa ni los respaldos de base. «No localizado» **no** equivalía a «no realizado» | Dump local 2026-10-08 (`ir_attachment`, `madenat_guia_processing`, `stock_lot`, `stock_picking`); biblioteca con 63 archivos |
| C2 | «La expresión “operación no válida” es una paráfrasis del usuario» (H-1) | **Retirado.** La búsqueda literal **no la localizó**, pero eso **no demuestra** cómo la formuló el usuario. Se reclasifica como **texto reportado cuyo origen no fue identificado**, hasta localizar el mensaje o reconstruir su contexto | Búsqueda literal en `custom_addons` + `/opt/odoo18-test/{odoo,addons}` (0 coincidencias) |
| C3 | «No llegaron los adjuntos» / «no existe expediente con los adjuntos» (H-3) | **Rectificado.** Existen: **biblioteca externa** (63 archivos, 52 únicos) y **adjuntos subidos** en la base local (`26270.pdf`, `26270.xlsx`, `GDE Guía de Despacho 19826/19827/19846.pdf` + sus packings). **No** debe reutilizarse la frase «no llegaron los adjuntos» | `ir_attachment` del dump local, con `create_date` 2026-08-31/09-08 |
| C4 | «El 48,009 de Ferramenta es incorrecto» / «causa NO determinada» (H-4) | **Rectificado.** **No es un error**: es el volumen de **embarque** con espesor nominal y ancho +1/8" (`_compute_vol_shipment_m3`). Guía/packing/físico = **57,840**; embarque = **48,009**. Y el packing **sí** se interpretó (17 lotes con sus M3) | §17.15.4 con la fórmula y su verificación numérica exacta |
| C5 | «JCE: NO ACREDITADO (0 líneas por diseño)» (R09/R10) | **Precisado por ruta.** La **guía 95806 se ingirió** por la ruta de **Volúmenes** (`granel`, `verified`, 59,964 m³, 2026-10-06). El **packing Nota de Venta** se lee y se **rechaza por diseño**. La correspondencia fixture↔documento real **queda demostrada** (cabecera idéntica y mismos valores) ⇒ **sí** se puede atribuir al documento real | Registro 33151; `test_nota_venta_dimensions_raw_rejected_with_diagnostic`; `test_document_format.py` |
| C6 | «Arauco: NO ACREDITADO / exige Excel» (R11) | **Rectificado.** La ruta de **Volúmenes** existe y **se usó con el PDF real** (`validated`, 40,315 m³, 2026-10-01); el PDF es **fixture byte-idéntico** y se ejercita con el **motor real**. Brecha concreta y acotada: **packing PDF en el flujo Normal** | Registro 15326; lote `GRANEL 4495589`; `test_intake_volume_detail_pieces.py` |
| C7 | Atribución del `OwlError` (R15) | **Corregido:** fue **compartido por Mauricio**, **no** consta como reporte de Cristhian. Se conserva como incidencia **abierta y no reproducida** | Enunciado de la orden de trabajo; sin artefacto de reporte del usuario |
| C8 | «Fixtures: sólo 2 de 5 proveedores» (§13.3) | **Rectificado:** **1 fixture real** (Arauco, byte-idéntico) + **1 transcripción** (`26270.txt`) + **4 familias de fixtures derivados** (Byc, Fátima, JCE-Nota de Venta, JCE-guía) + estructura del packing de Arauco | §17.15.2 |
| C9 | «Servicio local no operativo ⇒ no se pudo verificar nada del entorno local» (§17.14.1) | **Matizado:** el **servicio HTTP** no responde desde esta distro, pero el **estado de la base local sí se verificó** leyendo su respaldo del 2026-10-08 con `pg_restore` (sin restaurar). La limitación queda acotada a «no hubo consultas en vivo ni ejecución de pruebas» | `BACKUP_AB_APPLY_20261008/db/madenat_test_20261008_092958.dump` |
| C10 | «R06/R07: sin evidencia de ingreso completo» | **Rectificado:** hay ingreso **completo hasta stock** (17 lotes + picking) con los archivos reales, replicado en el TEST remoto | §17.15.3 caso 1 y §17.15.5 |

**Lo que NO cambia:** R15 sigue **abierto y no reproducido**; V3 (navegador) sigue **pendiente**; las
validaciones legítimas **no** se desactivan; y **no** se aprueba ningún caso sólo por existir el archivo.

#### 17.15.7 Matriz R01–R16 — versión revalidada (sustituye los estados de §17.14.2)

Estados adaptados a la nomenclatura vigente: **VERIFICADO CON MUESTRA REAL · VERIFICADO
HISTÓRICAMENTE; REVALIDACIÓN ACTUAL PENDIENTE · IMPLEMENTADO Y PROBADO EN ALCANCE PARCIAL · PRUEBA
REALIZADA SEGÚN MAURICIO; EVIDENCIA DETALLADA NO LOCALIZADA · INCIDENCIA REPRODUCIDA/ABIERTA ·
EVIDENCIA CONTRADICTORIA (resuelta) · PENDIENTE FUNCIONAL**.

| RQ | Muestra real · hash | Evidencia de que se realizó | Entorno | Etapa | Resultado | Vigencia vs código actual | Estado | Pendiente exacto |
|---|---|---|---|---|---|---|---|---|
| **R01** | n/a (aplica a los 11 ingresos reales) | 11 ingresos ejecutados ago–oct sin registros de bloqueo por mensaje de perfil; el aviso de perfil sigue en el código | Código + base local | n/a | No se localizó artefacto del mensaje concreto | `intake_wizard.py:251-262` **vigente** | **PRUEBA REALIZADA SEGÚN MAURICIO; EVIDENCIA DETALLADA NO LOCALIZADA** | Captura o texto exacto del aviso; reproducir en navegador |
| **R02** | Las **11 guías reales** | Clasificación **por contenido** verificada en los datos: `19846/19827/19826/26270/900002 → service`; `4495589/95806/UAT-SV → granel`; `UAT-INT-20261004 → compra`, **sin selección manual** | Base local (+remoto) | **D** | Coherente en el 100 % de los casos reales | AD-61 vigente; `intake_wizard_views.xml:48` (campo oculto) | **VERIFICADO CON MUESTRA REAL** | Ninguno funcional; V3 visual pendiente |
| **R03** | Guías **26270, 19846, 19826, 4495589, 95806** | **Subproducto asignado en todas las líneas**: 17/17, 19/19, 17/17, 1/1, 1/1; **1 solo `product_id` maestro por guía** | Base local | **D** | Resolución/autocreación de subproducto **correcta en datos reales** | AD-ING-001/002 vigentes; `find_or_create_lumber_subproducto` | **VERIFICADO CON MUESTRA REAL** | Revisar si el reporte original era otro defecto (no localizado) |
| **R04** | Líneas de **26270/19846/19826** | `thickness_visual`/`width_visual` reales (`5/4`, `4 5/8`, `3 5/8`, `150mm`) **se usan** en `_compute_vol_shipment_m3` (verificado numéricamente) ⇒ la conversión funciona | Base local + código | **B/D** | Conversión OK; **mezcla de notaciones** presente (`150mm` junto a fracciones) | `_get_fraction_text`, `_check_imperial_fractions` (solo log) vigentes | **IMPLEMENTADO Y PROBADO EN ALCANCE PARCIAL** | Presentación del packing en fracciones **en la Consola** (V3) |
| **R05** | `Guia 41994.pdf` (`4d8e0e8b…`) · `41994.xls` (`99fe59ff…`) | Fixture **derivado** `test_two_row_header` (misma cabecera 2 filas y 1.ª línea `0000000134008`); **formato idéntico** a `39519 (1).xls`, que **sí se ingresó** (id 1161, `verified`) | Código + base local | **A/B** (+D por equivalencia de formato) | Formato **legible e ingerible** por equivalencia | `excel_table_detection.py` vigente (alias semánticos únicos) | **IMPLEMENTADO Y PROBADO EN ALCANCE PARCIAL** | Ingreso real de **41994** (o decisión de aceptar la equivalencia con 39519) |
| **R06** | `26270.pdf` (`04226af8…`) + `26270.xlsx` (`0f843ece…`) | **Adjuntos** en guia.processing 1728 · **17 lotes** con los M3 del packing · 1 picking · `validated` (2026-09-08) · **replicado en el TEST remoto** (id 17, 17 lotes) · transcripción `fixtures/26270.txt` | **Local y remoto** | **A,B,C,D,E** | **Ingreso completo hasta lotes/picking** | `_parse_packing_excel` vigente; detector vigente | **VERIFICADO CON MUESTRA REAL** | Presentación conjunta de volúmenes (ver R07) |
| **R07** | idem R06 | Σ líneas: `vol_purchase` **57,840** = guía **57,8400** = packing **57,839556**; `vol_shipment` **48,009** = fórmula de embarque con espesor nominal y ancho +1/8" | Local y remoto | **D/E** | **Los tres volúmenes son correctos y de distinta naturaleza**; `packing_volume_declared_m3` **vacío** porque el campo es **posterior** al registro | `_compute_vol_shipment_m3:448-506`; campos de conciliación (`:1005-1072`) | **VERIFICADO CON MUESTRA REAL (cálculo) · PENDIENTE FUNCIONAL (presentación)** | Mostrar/rotular **ambos** volúmenes y su semántica en la Consola; decidir cuál es «operativo» |
| **R08** | `95083 .pdf` (`b581a283…`) · `95083 Final.xls` (`b5c474ae…`) / `95083 (1) (1).xls` (`191161be…`) | `excel_table_detection.py` («**investigación 95083**»); `test_excel_table_detection.py` («Estructura tipo 95083») y `_build_xls_blanks_bytes` con **valores de la 1.ª fila real** (31,75·146,1·4,877·231·5,226·1); `test_packing_declared_totals_persisted` con **42,132/2244/8** | Código | **A/B** | Estructura e interpretación **acreditadas** | Detector vigente | **IMPLEMENTADO Y PROBADO EN ALCANCE PARCIAL** | Ingreso real de **95083** (no hay registro en ninguna base) |
| **R09** | `GDE 95806.pdf` (`17a57189…`, = `2026-08-21T10_47_21_T52F95806 .pdf`) | Registro **33151**: `granel`, `verified`, `59.964 = 59.964`, `guide_pdf_filename='GDE 95806.pdf'` (2026-10-06) · adjuntos del wizard (res_id 13654/13655) · fixtures derivados con los datos reales (`95806`, `MC-0523-140`, `59.964`, `12 paq.`, `2772 pzs`, T.C. `923.23`) | Base local | **A,B,D** | **La guía SÍ se leyó y se ingresó** (ruta de Volúmenes) | `document_extractor.extract_document` + extractor PDF genérico vigentes | **VERIFICADO CON MUESTRA REAL** (guía) | Ninguno para la guía; ver R10 para el packing |
| **R10** | `GDE 95806.xls` (`a9049815…`) / `NVTA881333 (2).xls` (`ec064c4b…`) | `test_nota_venta_dimensions_raw_rejected_with_diagnostic` con fixture **derivado** (cabecera real idéntica y valores reales `5/4x5.3/8x16`, `231`, `4.997`, `21176`, `4`, `430`, `US$/M3`) ⇒ correspondencia **demostrada** | Código | **A,B** (C/D **no**) | Se **lee**; se **rechaza por diseño** (`REQUIERE_DIMENSIONES_SEPARADAS`, «No se creó ninguna línea») | Regla vigente en `_validar_y_enriquecer_lineas` | **EVIDENCIA CONTRADICTORIA (resuelta) → PENDIENTE FUNCIONAL** | Decidir: normalizar `Esc. Fact` a E/A/L **o** mensaje explícito «packing no ingerible» |
| **R11** | `HLZF75_4495589.pdf` (`98382981…`, **fixture byte-idéntico** en `madenat_lumber_intake/tests/fixtures/`) + `PACKING HLZF75 (1).pdf` (`1fcebe7f…`) | Registro **15326**: `granel`, `validated`, `40.315 = 40.315` (2026-10-01) · lote `GRANEL 4495589` (2026-09-25) · pickings `EMB-01768` `origin='4495589 [PURGADO-TEST]'` **y su reversa** (2026-09-30) · `test_intake_volume_detail_pieces.py` (**motor real**) y `test_reopen_oc_reextraction.py` · estructura del packing en `test_tabla_12_filas_lotes_mixtos` | Base local + código | **A,B,C,D** (+E con purga/reingesta) | **Guía leída, ingerida y validada**; hubo purga y reingesta | Extractor PDF genérico vigente | **VERIFICADO CON MUESTRA REAL** | **Pendiente funcional acotado**: packing **PDF** en el flujo **Normal** |
| **R12** | n/a (función) | `test_service_return_confirmation.py` (13) → **88/88** sobre `madenat_test` (2026-10-08) | Local | **D** | Sí/No/vacío persistente y **no** bloqueante | AD-102 vigente | **IMPLEMENTADO Y PROBADO EN ALCANCE PARCIAL** | **V3** en navegador (guiar 19827) |
| **R13** | n/a (función) | `test_service_return_imputation_guard.py` (8) + `..._pending_filter.py` (9) + regresiones I2 | Local | **D** | Aplicar exige destino «Sí»; reversa permite cambiar | AD-102 vigente | **IMPLEMENTADO Y PROBADO EN ALCANCE PARCIAL** | V3; concurrencia y cobertura parcial abiertas |
| **R14** | n/a (UI) | Vista cargada en `madenat_test` (id 1867 local / **1660 remoto**) con `Aplicar cambios` y `Evidencia documental`; estructura verificada | Local + remoto | **F (solo estructura)** | Disposición verificada **estáticamente** | `intake_console_views.xml` vigente | **IMPLEMENTADO Y PROBADO EN ALCANCE PARCIAL** | Observación **visual** (`UI-1..UI-6`) |
| **R15** | n/a | Búsqueda estática: **no** hay campo huérfano en las vistas de la Consola; `urlRelation` pertenece al cliente web | Código | — | **No reproducido** | Sin cambios | **INCIDENCIA ABIERTA (no reproducida)** | Reproducir con navegador/base/usuario/registro y capturar; **reportado por Mauricio** |
| **R16** | `26270` (local y remoto) | Manifiesto SHA-256 de **314** archivos `.py/.xml/.csv` (4 módulos): **0 discrepancias**; módulos/esquema/vistas presentes; **26270 replicado con sus 17 lotes** | Local + remoto | **D** | Correspondencia de **código** y **esquema**; réplica del caso 26270 | — | **VERIFICADO CON MUESTRA REAL · ALCANCE PARCIAL** | Replicar/validar en TEST remoto los demás casos (hoy sólo locales); dar versión a `custom_addons` del remoto |

#### 17.15.8 Niveles de esta revisión, fuerza de la evidencia y pendientes mínimos

**Correspondencia A–F ↔ V0–V3 (no se renombran los niveles existentes):** los niveles **A–F** son
categorías **de esta revisión** y se mapean así: **A** (lectura) → V0/V1 con ejecución real;
**B** (interpretación) → V2 (pruebas del parser/detector) + V1; **C** (integración documental) → V2;
**D** (flujo de ingreso) → V2 + **registro persistente**; **E** (stock) → V2 + datos de stock;
**F** (interfaz) → **V3** (navegador). Los niveles **V0–V3** de `03_TESTS.md` **siguen vigentes** y no
se sustituyen.

**Fuerza de la evidencia localizada (lo más fuerte primero):**
1. **Ejecución registrada con resultado** (§17.15.3 casos 1–10): adjuntos con nombre original + estados
   `verified`/`validated` + lotes y pickings.
2. **Fixture byte-idéntico del archivo real** (Arauco) ejercitado por el **motor real**.
3. **Fixtures derivados del documento real** con cabecera y valores verificados (Fátima, Byc, JCE ×2).
4. **Transcripción** del texto real (`fixtures/26270.txt`).
5. **Prueba automatizada existente sin ejecución localizada** en esta intervención (la mayoría de las
   suites citadas; **no** se ejecutaron aquí).
6. **Declaración de prueba por Mauricio** (antecedente explícito de esta sección).
7. **Referencia documental sin artefacto**: `regen_docs_madenat.sh` propone la guía **40597** como
   «caso base» (PDF 55.665 vs Excel 55.821 m³) y la biblioteca **tiene** `Guia 40597.pdf` + `40597.xls`;
   **no** se localizó registro de ese ingreso.
8. **Capturas de navegador: NO existen** en ningún expediente inspeccionado.

**Pendientes mínimos (con acción concreta; ninguno ejecutado):**

| # | Pendiente | Acción concreta | ¿Requiere autorización? |
|---|---|---|---|
| **Q1** | **R07** — presentación y semántica de los volúmenes | Decidir y etiquetar en la Consola: *Vol. Guía/Packing* (57,840) vs *Vol. Embarque* (48,009) — hoy `packing_volume_declared_m3` está vacío por ser campo posterior al registro | Sí (cambio de UI) |
| **Q2** | **R10** — Nota de Venta (JCE) | Decidir: normalizar `Esc. Fact` (`5/4x5.3/8x16`) a espesor/ancho/largo **o** mensaje explícito «packing no ingerible» | Sí (cambio de código) |
| **Q3** | **R11** — packing PDF en flujo Normal (Arauco) | Decidir: exigir Excel / derivar a Volúmenes / leer packing PDF en Normal | Sí (decisión + eventual código) |
| **Q4** | **R05 / R08** — ingresos reales de `41994` y `95083` | Ejecutar el par en una base de pruebas con los archivos de la biblioteca (o aceptar formalmente la equivalencia con `39519`) | **Sí** (crea registros) |
| **Q5** | **V3 (navegador)** — R01, R12, R13, R14 | Ejecutar `GUION_VERIFICACION_NAVEGADOR.md` sobre `8069`/`madenat_test` (guía 19827) | No (observación), salvo escrituras de prueba |
| **Q6** | **R15** — OwlError | Reproducir con navegador + base + usuario + registro y **capturar**; sin borrar assets ni tocar JS global | No (diagnóstico) |
| **Q7** | **R16** — réplica en TEST remoto | Decidir la carga de los casos locales en el remoto y **dar control de versión** a su `custom_addons` | Sí |
| **Q8** | Regresión | Promover a **fixtures** las muestras ya probadas (§17.15.2) para que la regresión no dependa de la biblioteca externa | Sí (añade archivos al repo) |

**No se propone, y no debe hacerse:** crear una base nueva; recrear el aislamiento retirado; enviar a
stock guías existentes sólo para completar una prueba; desactivar validaciones legítimas; ejecutar
scripts desconocidos sin inspeccionarlos; ni borrar/limpiar recursos legado en esta intervención.






### 17.16 Cierre funcional de pendientes (P0–P4) — 2026-10-10

**Naturaleza.** IMPLEMENTACIÓN Y VERIFICACIÓN sobre el desarrollo existente
(`madenat_test`, `localhost:8069`, contenedor `odoo18_app`, PostgreSQL
`odoo18_db`). Sin nuevas bases, contenedores ni ramas; sin commit/push; sin
correos; **sin despliegue remoto**. Biblioteca de muestras:
`muestras_documentos_ingreso`.

**Baseline confirmado.** Rama `feat/guia-correccion-documental-preservada-20261002`,
HEAD `e302c488321c276af7e07f1abeecc8bc261a89f4`, `git status` = **62 modificados
+ 14 sin seguimiento** (76 entradas), **0 staged**. Respaldo previo a las
escrituras: `CIERRE_PENDIENTES_20261010/db/madenat_test_pre_20261010.dump`
(`pg_dump -Fc`, 11,3 MB).

#### 17.16.1 P0 — OwlError `Many2OneField.urlRelation` (R15 / Q6)

**Punto de fallo** (cliente web de Odoo 18; **no** existe en `custom_addons`):
`many2one_field.js` → `get urlRelation() { if (!this.relation.includes(".")) }`
con `get relation() { return this.props.relation ||
this.props.record.fields[this.props.name].relation; }`. El error exige un
`Many2OneField` cuyo campo **carece de `relation`** en los metadatos.

**Diagnóstico estático ejecutado (servicio 8069 operativo):**

| Comprobación | Resultado |
|---|---|
| `madenat.lumber.intake.console`: 9 campos `many2one`, con `relation` faltante | **0** |
| Vistas de la Consola (`list`/`form`/`search`) con `widget="many2one*"` | **0** incidencias |
| `ir.model.fields` `ttype='many2one'` con `relation` vacío (`madenat_test`) | **0** |
| `ir.model.fields` `ttype in ('one2many','many2many')` con `relation` vacío | **0** |
| Campos con `widget="many2one"`/`many2one_avatar*` en vistas propias | todos sobre `many2one` reales |
| JS propio que altere `Many2OneField`/`urlRelation` | **ninguno** |
| Diff A/B (15 archivos) | sólo añade `widget="radio"` (`Selection`) |
| `docker logs odoo18_app` (48 h) con el error | **ninguno** |

**Resultado: NO REPRODUCIDO BAJO ESTAS CONDICIONES** (sin navegador disponible
en el entorno de trabajo). **No** se parchea el cliente global ni se borran
assets. **Paso manual concreto para Mauricio:** con navegador en
`http://localhost:8069`, base `madenat_test`, usuario afectado (no admin), abrir
la acción/menú y el registro que falló y capturar: URL completa, pestaña
Console (traceback Owl completo) y Network (última respuesta `/web/dataset/...`),
indicando el **modelo y campo** resaltados. Sin esa captura, R15 permanece
**abierto**. Hipótesis conservadas, **no confirmadas**: (a) assets/caché de
vista desactualizados; (b) metadatos de relación no cargados; (c) widget
incompatible.

#### 17.16.2 P1 — Nomenclatura y presentación de volúmenes (R07 / Q1)

Implementado en el desarrollo existente:

- Modelo `madenat.lumber.intake.console`: proxies read-only `vol_compra_m3`
  («Vol. compra (m³)», Σ `vol_purchase_m3` de las líneas) y `vol_embarque_m3`
  («Vol. embarque (m³)», Σ `vol_shipment_m3`); calculan sin escribir y no
  alteran fórmula, unidad, precisión ni valores históricos.
- Vista `madenat.lumber.intake.console.form`: ambos campos añadidos al grupo
  «Volúmenes y diferencias» (junto a «Vol. PDF/Guía (m³)» y «Vol. Packing (m³)»);
  se conservan el resumen en 2 columnas, la evidencia en 3 columnas, el radio a
  todo el ancho y el packing a todo el ancho.
- `madenat_lumber_core/views/guia_processing_views.xml`: rótulos inequívocos
  `vol_purchase_m3` → «Vol. compra (m³)» y `vol_shipment_m3` → «Vol. embarque
  (m³)» (columna y subtotal), eliminando «Vol. m³», «Vol (m³)» y «Vol. Físico
  (m³)» sobre el campo de embarque.

**Verificación (Ferramenta 26270, consola id 900001728):** `vol_comercial_pdf`
**57,840** · `packing_volume_declared_m3` 0,000 (campo posterior al registro) ·
`vol_compra_m3` **57,840** · `vol_embarque_m3` **48,009**. Se conserva la
explicación de magnitudes distintas (guía/packing/físico vs. embarque). Módulos
actualizados (`-u madenat_lumber_core,madenat_lumber_intake`, servicio detenido
durante la actualización) y `HTTP 200` posterior. Pendiente: **observación en
navegador** (V3).

#### 17.16.3 P3 — Ingresos reales Fátima 41994 y Byc 95083 (R05/R08 / Q4)

Ejecutado con los archivos **reales** de la biblioteca, por la fachada de
ingreso (`madenat.lumber.intake.wizard`, modalidad `normal`):

| Caso | Documentos | Destino | Estado | Líneas | Volumen | Clasificación |
|---|---|---|---|---|---|---|
| Fátima **41994** | `Guia 41994.pdf` + `41994.xls` | `lumber.reception` **7950** (`name=41994`) | `verified` | 14 | Σ `vol_purchase_m3` = **50,497** (guía PDF 50,496) | Producto (auto, sin selección manual) |
| Byc **95083** | `95083 .pdf` + `95083 Final.xls` | `madenat.guia.processing` **33250** (`name=95083`) | `verified` | 8 | `5,226`/línea (Σ 41,808) · guía **42,132** | Procesado (auto; keyword «servicio») |

- **Alcance: SIN stock.** Ambos casos se detuvieron en `verified`; **no** se
  envió a stock ni se crearon movimientos/pickings.
- Byc: `31,75 × 146,1 × 4,877 m` × `231 pzas` × 8 líneas, con subproducto por
  línea; Fátima: 14 líneas con `subproduct_id` y `lengthuom='m'`, `Σ vol_purchase
  = 50,497` vs. guía 50,496 (Δ 0,001 = redondeo).
- La guía de Byc se clasificó automáticamente como **Procesado** por la palabra
  clave «servicio» presente en el PDF; se registra como **observación de
  clasificación** (R02: clasificación por contenido), **no** como defecto.

#### 17.16.4 P4 — JCE dimensiones combinadas (`Esc. Fact`) (R10 / Q2)

**Notación descifrada de forma determinista** (no por intuición). El archivo
real `GDE 95806.xls` / `NVTA881333 (2).xls` (Nota de Venta Nº 881333, JCE) trae
`Esc. Fact = 5/4x5.3/8x16`, `Pzas = 231` y `VOL. = 4,997 m³`. Con espesor
nominal `5/4"` (1,25"), ancho nominal `5 3/8"` (5,375") **+ ajuste S2S `1/8"`**
(5,5") y largo `16 ft`: `1,25 × 5,5 × 16 × 231 / 12³ = 4,997 m³` **exacto** ⇒
`5.3/8` = `5 3/8`. La propia columna `VOL.` del documento es la prueba.

**Implementado** en `madenat_lumber_core/models/madenat_guia_processing.py`:
nuevo `_normalize_combined_dimensions(raw)` + enganche en
`_validar_y_enriquecer_lineas` (solo cuando faltan dimensiones separadas).
Normaliza la forma acreditada `E x A x L` (3 tokens; separador `x`/`X`/`*`;
fracción/mixto/entero; largo en pies) a `(espesor_mm, ancho_mm, largo_m)`.
Los patrones **no** acreditados (nº de tokens ≠ 3, token no numérico o fuera de
rango) siguen rechazándose con `REQUIERE_DIMENSIONES_SEPARADAS`; **no** se
inventan dimensiones ni se asumen unidades.

**Verificación con el documento REAL** (`GDE 95806.xls`, parser core real):

| Métrica | Resultado |
|---|---|
| Líneas válidas / rechazadas | **12 / 0** |
| Dimensiones normalizadas por línea | `31,75 mm × 136,525 mm × 4,8768 m` |
| `vol_shipment_m3` por línea | **4,9967** (documento `VOL.` = 4,997) |
| Σ `vol_shipment_m3` | **59,960** (guía PDF `GDE 95806.pdf` = 59,964) |

El test que esperaba el rechazo **no se eliminó**: se adaptó
(`test_nota_venta_dimensions_raw_normalized_and_create`) y se añadió
`test_dimensiones_combinadas_ambiguas_siguen_rechazadas`.

#### 17.16.5 P4 — Arauco packing PDF (R11 / Q3)

**Decisión funcional (reutilizando capacidad existente).** El packing de Arauco
llega en **PDF** (`PACKING HLZF75 (1).pdf`). El motor real extrae su estructura
(17 líneas; `total_volume_m3` = **40,315**) pero **sin detalle determinista por
línea** (piezas/volumen por línea ausentes) ⇒ no procede forzar el flujo Normal
(que exige packing **Excel**).

- **Ruta recomendada:** **Ingreso por Volúmenes** (guía PDF), ya acreditada con
  el PDF real `HLZF75_4495589.pdf` (registro **15326** `granel`/`validated`,
  `official_volume_m3` **40,315**, lote `GRANEL 4495589`).
- **Alcance:** volumen total de la guía/packing; **no** se afirma haber obtenido
  detalle inexistente.
- **Efecto operativo:** sin lector nuevo; el packing PDF se aporta como
  evidencia y su volumen se concilia; el flujo Normal permanece reservado a
  packings con dimensiones separadas.

#### 17.16.6 Evidencia, entornos y regresiones

**Muestras usadas (SHA-256 completos, `muestras_documentos_ingreso/07-09-2026/`):**

| Documento | SHA-256 |
|---|---|
| `Guia 41994.pdf` | `c0031051000b8eb92caeaa7d37741dbd42d91192ff75d468e324a4d2fa6fbf9f` |
| `41994.xls` | `e4cdfd20aae34183f4f34bd072991212171e212170b9ed85523674baf832262f` |
| `95083 .pdf` | `f53769652f5b5e52d4bb0adb1dd3334c3f9c697ee64d37dc43d579f06f95e770` |
| `95083 Final.xls` | `93c129a041ca9da3ff8c1a61528612467ac43249100b12cad76e09a64d7017f7` |
| `GDE 95806.xls` | `722d725a0207e0981ffe7143128539dc794c8ae31eac9a6a21153058d6592273` |
| `NVTA881333 (2).xls` | `ba1f83414812355f6be8a8e49371fabae7e1c090547f106a654a8e8ad9f62b94` |
| `PACKING HLZF75 (1).pdf` | `df2ddca1689804c183a4bb81047983d76343443c52201a62e95558f52a5b870e` |
| `HLZF75_4495589.pdf` | `98382981de062b1b0d2b289f5fee0e6de0339e35c63401c080063a6d11c19155` |

**Regresiones (corridas nuevas, `madenat_test`):**

| Corrida | Alcance | Resultado |
|---|---|---|
| Dirigidas (nuevo) | `TestGuiaProcessingExcelParser` + `TestVolumeUiHierarchy` + `TestVolumeOperationsScreen` | **0 failed, 0 error(s) of 34 tests** |
| Regresión de módulo | `madenat_lumber_intake` (`--test-tags /madenat_lumber_intake`) | **2 failed of 380** → **corregidas** |
| Documento real JCE | `GDE 95806.xls` (motor core real) | 12/12 líneas · `4,9967` ≈ `VOL.` 4,997 |
| Consola Ferramenta | id 900001728 | guía 57,840 · embarque 48,009 |

> **Rectificación honesta de las 2 fallas.** Pertenecen a
> `madenat_lumber_intake` y su causa **no** es esta intervención: la
> reorganización de UI aplicada (2026-10-08) consolidó el encabezado
> «Evidencia documental» en uno solo («📄 Evidencia documental»), y esas dos
> pruebas (sin modificar) aún esperaban el texto sin emoji. Los diffs de la
> implementación A/B **no** contienen esa consolidación; ésta vive en el árbol
> activo. Se **adaptó la constante** de ambas pruebas al encabezado vigente
> (sin eliminar ninguna aserción) ⇒ verde. **No** se declaró «todo cerrado»:
> se corrigen la atribución y el conteo.

**Límites conservados (sin cambios):** V3 (navegador) **pendiente**;
R16 (réplica/control de versión del TEST remoto) **pendiente**; concurrencia
**no acreditada**; filtro «sin imputación aplicada» **sin cobertura parcial**;
I3/I5 **fuera de alcance**; instalación en base limpia **pendiente**.

#### 17.16.7 Estado Q1–Q8 tras el cierre (2026-10-10)

| # | Pendiente | Estado 2026-10-10 |
|---|---|---|
| **Q1** | R07 — presentación/semántica de volúmenes | **CERRADO EN DESARROLLO** (V3 navegador pendiente) |
| **Q2** | R10 — Nota de Venta (JCE) `Esc. Fact` | **CERRADO EN DESARROLLO** (normalización + pruebas + documento real) |
| **Q3** | R11 — packing PDF Arauco | **PENDIENTE DE DECISIÓN FUNCIONAL** → **propuesta:** ruta de Volúmenes (ejecutable ya; ver §17.16.5) |
| **Q4** | R05/R08 — ingresos reales 41994/95083 | **CERRADO EN DESARROLLO** (sin stock; ver §17.16.3) |
| **Q5** | V3 (navegador) | **PENDIENTE** (sin navegador en el entorno) |
| **Q6** | R15 — OwlError | **NO REPRODUCIDO BAJO CONDICIONES REGISTRADAS** (paso manual §17.16.1) |
| **Q7** | R16 — réplica/control de versión remoto | **PENDIENTE** (requiere autorización) |
| **Q8** | Regresión/fixtures | **PARCIAL** (fixtures reales ya usados por pruebas; promoción pendiente) |

**Diferencia local ↔ remoto.** Todo lo anterior es **LOCAL (`madenat_test`)**.
**No** se desplegó, actualizó ni reinició el TEST remoto. Lista para despliegue
posterior autorizado: `madenat_lumber_intake` (modelo `intake_console.py`, vista
`intake_console_views.xml`, tests `test_volume_ui_hierarchy.py`,
`test_volume_operations_screen.py`) y `madenat_lumber_core`
(`models/madenat_guia_processing.py`, `views/guia_processing_views.xml`, tests
`test_parse_excel_core.py`).

#### 17.16.8 Aceptación visual (2026-10-10) — guía 19827

Mauricio confirmó el **2026-10-10**, mediante captura y mensaje, que la **guía 19827** (Ferramenta,
`service`, `verified`) se presenta correctamente. Se registra como **aceptación visual** de la
presentación observada (nivel V3, caso único):

- Formulario abierto satisfactoriamente en el caso observado.
- **Resumen del ingreso** en **dos columnas**.
- **Evidencia documental** en **tres columnas**.
- **Identificación de retorno** visible.
- **Detalle del packing** a todo el ancho.

**No se extiende** esta aceptación a operaciones **no observadas**: persistencia Sí/No/vacío en
pantalla; aplicación y reversa de imputaciones; resolución global del `OwlError`. Estado del
`OwlError`, salvo evidencia adicional: **«No reproducido en la apertura manual observada; causa no
confirmada»** (§17.16.1). La validación visual permite cerrar la **presentación observada**; los
pendientes funcionales independientes permanecen identificados, **sin** volver a bloquear toda la
etapa. Evidencia de prueba: `03_TESTS.md` §14.4; estado del pendiente: `05_BACKLOG.md`.

#### 17.16.9 Flujo de imputación SV — confirmado en código (2026-10-10)

Respuesta a la pregunta funcional «¿cómo se imputan los volúmenes enviados a proceso a las guías de
procesados que retornan?». La **secuencia operativa** y la **tabla de controles** (origen · destino ·
volumen · saldo · aplicación · reversa · permisos) tienen dueño único en
**`19_IMPUTACION_SV_Y_PROCESADORES.md` §19.10**; **no** se duplican aquí.

Síntesis: el **origen** es la **etiqueta procesada** de la guía de retorno (el **envío a proceso** I1 es
una transferencia interna **separada**, sin vínculo automático); el **destino** es la **guía de
procesados** marcada **«Sí»** (se exige **al aplicar**, no al guardar); la imputación es **documental**
(I2, AD-91), **sin** efecto en stock; se **aplica** (Operaciones/Jefatura/Gerencia) y se **reversa**
(Jefatura/Gerencia) con historia **append-only**. **No** hay cálculo de **rendimiento ni merma**
(implementación pendiente) y **I3/I5 siguen fuera de alcance**.



#### 17.16.10 Relación de conciliación envío–retorno (Bloque A/B/C, 2026-10-10)

**Etapa nueva, acotada.** Se cierra la brecha **(a)** de `CANON/19` §19.10 («sin vínculo automático
envío↔imputación») con una **relación persistente y documental** entre el **envío a procesador**
(A, transferencia interna I1), el **retorno** (B, guía de procesados) y la **imputación documental SV**
(C, I2). Dueño funcional del detalle: `19_IMPUTACION_SV_Y_PROCESADORES.md` **§19.11**; **no** se duplica
aquí.

- **Modelo nuevo:** `madenat.processor.return.link` (enlaza el **picking** —no el wizard transitorio—,
  la guía y la imputación). Estados `draft`/`linked`/`reversed`; N:M (varios retornos por envío y
  viceversa); unicidad por par en estados activos; append-only.
- **Separación estricta:** **no** crea movimientos de stock ni ledger; **no** calcula conciliación
  cuantitativa (Bloque **D** pendiente); **no** sustituye la imputación SV.
- **Asistente reutilizado:** el asistente de imputación I2 incorpora la pestaña «Envíos a procesador
  (retorno)»; al aplicar registra las relaciones. No se crea un segundo asistente.
- **Trazabilidad:** pestaña en la guía y en el picking, pestaña en la imputación y menú de Logística
  «Conciliación Envío–Retorno».
- **Históricos:** **sin** asociación automática; permanecen `no_return` hasta declaración explícita.
- **Pruebas:** `test_processor_return_link.py` **12/12** (T1–T12); regresión
  `madenat_lumber_logistics` **265** dirigidas (3 fallas **pre-existentes** por aserción global de
  `deviation`; 0 fallas nuevas, 0 errores). Ver `03_TESTS.md` **§15**.
- **Evidencia web (2026-10-10) — clasificada en tres niveles (`03_TESTS.md` §15.4):** **(a) integración
  web/RPC con sesión autenticada — EJECUTADA** (registrar OK; reversa por Operaciones **DENEGADA**;
  reversa por Jefatura OK; auditoría) · **(b) lectura de arquitecturas de vistas y metadatos —
  VERIFICADA** (`get_views`, `fields_get`) · **(c) renderizado e interacción en navegador real —
  PENDIENTE** (sin navegador en el entorno). **(a)+(b) NO sustituyen a (c); V3 no acreditada.**
- **Controles (acreditación, `03_TESTS.md` §15.5):** atomicidad imputación+vínculo ✅ · elegibilidad
  `state='done'` ✅ · permisos ✅ · **reversa de imputación sobre el vínculo: NO acreditado** ·
  **consistencia de compañía: parcial** · **reparto N:M: Bloque D (pendiente)**.
- **Cierre versionado:** `madenat_lumber_logistics` **18.0.1.6.0 → 18.0.1.7.0** y
  `madenat_lumber_core` **18.0.6.5.0 → 18.0.6.6.0** (CHANGELOG actualizado).
- **Bloque D (cuantitativo):** **NO implementado** — decisión de etapa «opción 3»; `linked` =
  **vínculo registrado**, no «envío conciliado». Diseño requerido en `19` **§19.12**.
- **Entorno:** `madenat_test` (contenedor `odoo18_app`); respaldo previo verificado
  (`CONCILIACION_ENVIO_RETORNO_20261010/`). **Sin** commit/push ni despliegue remoto.

**Pendiente declarado:** Bloque **D** (conciliación cuantitativa) requiere magnitudes y reglas no
aprobadas; **no** se implementa «saldo de proceso», rendimiento ni merma.

#### 17.16.11 Ajuste de integridad del vínculo envío–retorno (2026-10-10)

Continuación de §17.16.10; cierra los controles pendientes de A/B/C (`CANON/19` **§19.13**):

- **Reversa vs. procedencia:** `state` (procedencia) ≠ vigencia documental. Reversar la imputación
  **no** revierte el vínculo; la vigencia se **deriva** (`documentary_status`, `requires_reimputation`).
- **Reimputación:** `previous_imputation_id` conserva la imputación reemplazada + rastro (chatter y
  auditoría); sin duplicar vínculos activos.
- **Compañía:** constraint de consistencia envío↔imputación + **regla de registro** multi-compañía
  (las ACL por grupo no sustituyen reglas). `madenat.guia.processing` no tiene `company_id`.
- **Elegibilidad dura por ORM/RPC:** `state='done'` y tipo interno; `draft`/`cancel`/`assigned`
  **rechazados** aunque se fuerce la selección.
- **Volúmenes N:M referenciales:** `aggregator=False` (sin agregación engañosa) + ayuda; **sin** reparto.
- **Pruebas:** T1–T22 = **22/22**; regresión `madenat_lumber_logistics` = **275 pruebas, 4 fallas**
  (3 preexistentes + 1 **ambiental** por el picking de evidencia V3 `7973`), **0 errores**. Ver
  `03_TESTS.md` §15.6.
- **Versión:** `madenat_lumber_logistics` **18.0.1.8.0**. **Sin** commit/push ni despliegue remoto.

#### 17.16.12 Operación manual de asignaciones centrada en SV (2026-10-10)

Continuación de §17.16.11; implementa los bloques A–G de `CANON/19` **§19.14**:

- **Entrada/consulta (A):** acción **Logística → Asignaciones SV** sobre `stock.lot`
  (`lot_flow_type='volume'`) con **vistas dedicadas** (`view_madenat_sv_assignment_list/_form`);
  sin modelo persistente nuevo ni alteración de otras vistas de lotes. Cabecera con guía de
  procedencia, procesador, nominal, total imputado **aplicado** y **saldo documental I2**; detalle
  con imputación/guía/etiqueta/volumen/estado/fecha/usuario y acceso al documento.
- **Alta desde el SV (B):** botón **«Asignar retorno»** abre el asistente existente con `sv_lot_id`
  en contexto (orienta; no genera reparto ni aplica). Reutiliza la imputación de trabajo de la guía
  si ya existe.
- **Selección explícita (C):** booleano `selected` + «Seleccionar todas»/«Quitar selección»; una
  operación nueva **no** auto-incluye etiquetas.
- **Conservación del borrador (D):** `_i2_build_imputation` reconcilia (**upsert**) por
  `processed_lot_id` y `(línea, SV)`; reabrir reproduce selección y reparto; cambio de guía de una
  imputación de trabajo **bloqueado**. **No** es el Bloque D cuantitativo (§19.12), fuera de alcance.
- **Integridad etiqueta–guía (E, D10):** constraint `_check_label_belongs_to_guia` +
  `_i2_validate_payload`; históricos inspeccionados (sólo lectura): **0** inconsistencias.
- **Coherencia de volumen (F, D10/D11):** constraints `_check_reparto_within_nominal` y
  `_check_within_line_nominal` (`0 < Σ reparto ≤ nominal`); parciales admitidos; techo duro
  etiqueta-side y exceso blando SV-side conservados.
- **Pruebas:** `test_sv_imputation_manual.py` (T-MAN-01..12) = **12/12**; regresión
  `madenat_lumber_logistics` = **286 pruebas, 4 fallas** (las **mismas** preexistentes/ambientales
  del `deviation` histórico: ids 19889/19941/20342/20381/21739), **0 errores**. Ver `03_TESTS.md` §15.7.
- **Integración web/RPC (no V3):** menú «Asignaciones SV» visible para Operaciones y `default_get`
  del asistente con contexto SV OK. **V3 *pixel* pendiente.**
- **Versión:** `madenat_lumber_logistics` **18.0.1.9.0**; `19` 1.10.0 → **1.11.0**.
  **Sin** commit/push ni despliegue remoto.

#### 17.16.13 Corrección de duplicidad de accesos — «Rebaja de etiquetas» (2026-10-10)

- **Duplicidad corregida:** «Asignaciones SV» e «Imputaciones documentales SV» eran dos accesos
  paralelos a la **misma** operación documental. Queda **UN ÚNICO** enlace operativo: **«Rebaja de
  etiquetas»**.
- **Registros/acciones afectados:** menú `menu_madenat_sv_assignment` (renombrado «Rebaja de
  etiquetas»); menú `menu_madenat_sv_imputation` **retirado de navegación**
  (`ir.ui.menu.active = False`, con `record` posterior para que **no reaparezca** al reaplicar `-u`);
  acción `action_madenat_sv_assignment` («Rebaja de etiquetas», `stock.lot`); acción
  `action_madenat_sv_imputation` («Historial de rebajas», `madenat.sv.imputation`, **preservada**);
  acción/asistente `madenat_sv_imputation_wizard` («Registrar rebaja»).
- **Documentos/acciones preservados:** modelos `madenat.sv.imputation[.line|.sv.line]`, asistente,
  `action_apply`/`action_reverse`, saldos documentales, permisos, auditoría e historial **intactos**.
- **Navegación interna:** desde el SV, «Registrar rebaja», «Historial de rebajas» (por SV) y «Ver
  historial completo»; **sin** segundo enlace de menú.
- **Resultado real (metadatos/SQL):** `ir.ui.menu` **545** «Rebaja de etiquetas» activo (acción 874 →
  `stock.lot`); `ir.ui.menu` **542** «Imputaciones documentales SV» **inactivo** (acción 867
  preservada como «Historial de rebajas»); tras una **segunda** actualización `542` **permanece
  inactivo** y `545` activo. Sin navegador real: comprobación de metadatos/SQL; **V3 *pixel*
  pendiente**.
- **Pruebas:** nueva suite `test_sv_rebaja_navigation.py` (NAV-01..12) = **11/11**; regresión
  `madenat_lumber_logistics` = **298 pruebas, 4 fallas** (las **mismas** preexistentes/ambientales
  del `deviation` histórico), **0 errores**.
- **Versión:** `madenat_lumber_logistics` **18.0.1.10.0**; `19` 1.11.0 → **1.12.0**. **Sin**
  commit/push ni despliegue remoto.

<!-- actualizado: 2026-10-10 (7) — §17.16.13 unificación de acceso «Rebaja de etiquetas» (único
punto de entrada; retiro reproducible del menú «Imputaciones documentales SV»; historial interno).
Módulo `madenat_lumber_logistics` 18.0.1.10.0. Versión 02 12.20.0 → 12.21.0. Sin commit/push. -->

#### 17.16.14 Operación y blindaje de «Rebaja de etiquetas» (2026-10-10)

- **Elegibilidad (Bloque B):** el selector de guía ofrece sólo `service_return_confirmation='yes'` y
  `state!='cancelled'`; el modelo rechaza selección forzada No/vacío/cancelada en `onchange` y antes
  de construir el documento (`_i2_build_imputation`), sin estados parciales. Históricos consultables.
- **Magnitudes (Bloque D):** ayudantes `_i2_lot_reserved_m3` / `_i2_lot_applied_m3` /
  `_i2_lot_available_for_m3` (nominal = `_i2_lot_nominal_m3`); disponible y aplicado previo **excluyen
  el documento en curso** (sin doble conteo). Columnas del asistente: Nominal lote / Rebajado aplicado
  / Reservado borrador-pend. / Disponible documental.
- **Listado/Búsqueda (A/C):** columnas separadas (N° Guía, Proveedor, Fecha opcional, Producto,
  Procesador, magnitudes); agregados `sv_assignment_*` **`store=True`** para filtros documentales
  buscables (Con/Sin saldo, Con/Sin rebajas, Exceso); «En stock» opcional; columnas opcionales de
  retorno en el listado de guías.
- **Concurrencia (CON-01):** `_i2_lock_resources` bloquea **etiqueta de retorno (ns 3)** y **SV
  (ns 2)** en orden global determinista, antes de revalidar techos; fallo controlado sin estados
  parciales.
- **Pruebas:** nueva suite `test_sv_rebaja_operativa.py` (RET/UX/VOL/SEC/REV/PHY/CON) = **20/20**;
  regresión `madenat_lumber_logistics` = **318 pruebas, 4 fallas** (las mismas preexistentes), **0
  errores**.
- **Versión:** `madenat_lumber_logistics` **18.0.1.11.0**; `19` 1.12.0 → **1.13.0**. **Sin** commit/push.

<!-- actualizado: 2026-10-10 (8) — §17.16.14 operación y blindaje «Rebaja de etiquetas»: elegibilidad
de retorno, semántica de magnitudes, filtros buscables, resumen sin doble conteo, concurrencia.
Módulo 18.0.1.11.0. Versión 02 12.21.0 → 12.22.0. Sin commit/push. -->

#### 17.16.15 Corrección de «Seleccionar todas» y asignación explícita (2026-10-10)

- **Error manual reportado por Mauricio:** al pulsar «Seleccionar todas» en una apertura nueva,
  `madenat.sv.imputation.wizard.line` faltaba el campo obligatorio `processed_lot_id`.
- **Causa demostrada (no supuesta):** el cliente Odoo 18
  (`web/static/src/model/relational_model/record.js::_getChanges`) **omite** los subcampos `readonly`
  de una x2many salvo `force_save="1"`; el campo era `readonly="1"` sin `force_save`.
- **Corrección real:** `force_save="1"` en `processed_lot_id`; `create="false"` en el listado de
  asignación. No se quitó `required`, no se añadió etiqueta ficticia, no se capturó la excepción, no
  se usó `sudo`, no se exigió guardar antes.
- **Asignación explícita:** `action_assign_selected` (fila por etiqueta con SV de trabajo y volumen 0)
  y `action_use_available` (`min(disponible, nominal)`); resumen `assigned_summary`; «Pendiente de
  reparto». No aplica, no mueve stock, no duplica, no borra reparto a otros SV.
- **Semántica:** «Nominal comprometido» (lado etiqueta) ≠ «Rebajado etiqueta aplicado» ≠ «volumen
  asignado al SV». Caso parcial (nominal 5, SV 3) ya no se lee como «5 rebajado».
- **Pruebas:** nueva suite `test_sv_rebaja_seleccion_asignacion.py` (ERR/ASG/VOL/PER/SEC/PHY) =
  **16/16**; regresión `madenat_lumber_logistics` = **334 pruebas, 4 fallas** (las mismas
  preexistentes), **0 errores**.
- **Versión:** `madenat_lumber_logistics` **18.0.1.12.0**; `19` 1.13.0 → **1.14.0**. **Aceptación
  visual de Mauricio pendiente.**

<!-- actualizado: 2026-10-10 (9) — §17.16.15 corrección de «Seleccionar todas» (causa force_save) y
asignación explícita al SV. Módulo 18.0.1.12.0. Versión 02 12.22.0 → 12.23.0. Sin commit/push. -->

#### 17.16.16 Rediseño operativo del asistente «Registrar rebaja» (2026-10-10)

- **Motivo:** la presentación fue **rechazada por Mauricio** (encabezados truncados, etiqueta vacía,
  lote concatenado, exceso de indicadores, recorrido poco evidente).
- **Mapeo de material:** etiqueta = `stock.lot.ref`; SKU y dimensiones declaradas =
  `madenat.guia.processing.line` asociada por la **regla de promoción** (nombre = etiqueta + SKU +
  dígitos de la guía); producto/subproducto/dimensiones técnicas/piezas/volumen = `stock.lot`. Guía
  real 19827: **17/17** mapeados, sin cortar nombres.
- **Granularidad:** una fila = un lote; etiqueta repetida ⇒ lotes distintos (no dedup); disponibilidad
  por lote (sin doble conteo).
- **Vista:** tabla de material con columnas separadas + avanzadas **opcionales**; asistente como
  **formulario amplio** (`o_xxl_form_view`, `target=current`); cabecera compacta con saldo documental
  del SV; acciones principales junto a la tabla y FIFO/pendiente en menor jerarquía.
- **Cantidades:** «Cantidad preparada» solo lectura (reparto real); edición en «Asignación a SV».
- **Pruebas:** nueva suite `test_sv_rebaja_material.py` (MAP/GRAN/SEM/AMT/ARCH) = **8/8**; regresión
  `madenat_lumber_logistics` = **342 pruebas, 4 fallas** (las mismas preexistentes), **0 errores**.
- **Versión:** `madenat_lumber_logistics` **18.0.1.13.0**; `19` 1.14.0 → **1.15.0**. **Aceptación
  visual de Mauricio pendiente.**

<!-- actualizado: 2026-10-10 (10) — §17.16.16 rediseño del asistente «Registrar rebaja» (material del
packing list, granularidad, formulario amplio). Módulo 18.0.1.13.0. Versión 02 12.23.0 → 12.24.0.
Sin commit/push. -->


<!-- actualizado: 2026-10-08 (2) — §17.12bis entorno aislado RECREADO con autorización expresa (vía «montar el workcopy `:ro`», sin aplicar diffs): `srvretab_web` en `127.0.0.1:8070`, selector limitado a `srvretab_gate_20261007`, filestore del aislamiento repoblado desde el volumen del stack (`:ro`; assets 500→200, faltantes solo avatares de `res.partner`); ninguna base ni el servicio activo modificados; **V3 pendiente de evidencia manual**. | 2026-10-08 — §17.12 retoma de solo lectura (revalidación conforme: rama/HEAD Git, SHA-256 = checkpoint, workcopy = activo + 15 archivos de `AB_completo.diff`, `--dry-run` limpio, A/B ausente del código activo y de `madenat_test`; **entorno aislado no conservado** por reinicio del host: `srvretab_web` inexistente, puerto 8070 cerrado, `/tmp/gate` vacío, base `srvretab_gate_20261007` intacta; **V3 sigue pendiente**; recrear el aislamiento pendiente de autorización). Sin cambios de código, base ni servicios. | 2026-10-07 (2) — §17.11 checkpoint de pausa (reanuda 2026-10-08): A/B solo en aislamiento; gate 45/45; dirigidas 88/88 incl. Cristhian (uid 8, su=False); V3 pendiente; A/B no aplicados; hashes vigentes; reversión no equivale a restauración completa. | 2026-10-07 — §17: auditoría de retoma de la confirmación de retorno de servicio (no aplicada; especificación solo en el antecedente `IMPL_SERVICE_RETURN_20261006/`). Sin cambios de código ni datos. Solo documentación. -->
### 17.16.17 Interfaz clara y concisa de «Registrar rebaja» — ambas pestañas (2026-10-10)

- **Cabecera única:** SV de trabajo, guía, **saldo documental del SV**, **seleccionadas**, **con reparto
  preparado** y **preparado para el SV (m³)**; no se repite el nominal/saldo del SV por fila.
- **Totales con unidad:** Piezas de origen, Volumen documental de origen (≠ volumen a imputar), Disponible
  documental de las seleccionadas (sin doble conteo) y Preparado para el SV; con varios SV se separa el
  subtotal del SV de trabajo del total general.
- **«A asignar (m³)» editable** en «Materiales del retorno», integrado con el MISMO reparto
  (`sv_alloc_ids`); sin saldo paralelo y sin borrar repartos a otros SV.
- **Etiqueta limpia + medidas** («45 × 125 mm · 2,900 m»): distingue etiquetas repetidas sin cambiar
  `display_name`; SKU y código técnico como información secundaria.
- **Asignación a SV:** con un solo SV, **Etiqueta · Medidas · Disponible (m³) · A asignar (m³)** con el SV
  destino en la cabecera; «SV destino» sólo con varios SV.
- **Acciones:** Seleccionar todas · Quitar selección · **Preparar asignación** · Usar disponible (mismo
  alcance; no sobrescribe lo editado); footer Guardar borrador · **Revisar y aplicar** · Cancelar;
  FIFO/pendiente en `btn-link`.
- **Disponibilidad cero:** estado real por fila (Disponible/Aplicado/Reservado/Sin capacidad) y aviso de no
  asignables; no se borran reservas.
- **Pruebas:** `test_sv_rebaja_ui_limpia.py` (CAB/EDIT/MED/ETQ/SIN/USE/MULTI/ARCH) = **13/13**; regresión
  `madenat_lumber_logistics` = **355 pruebas, 4 fallas** (las mismas preexistentes), **0 errores**.
- **Versión:** `madenat_lumber_logistics` **18.0.1.14.0**; `19` 1.15.0 → **1.16.0**. **Aceptación visual
  de Mauricio pendiente.**

<!-- actualizado: 2026-10-10 (11) — §17.16.17 interfaz limpia de ambas pestañas del asistente «Registrar
rebaja». Módulo 18.0.1.14.0. Versión 02 12.24.0 → 12.25.0. Sin commit/push. -->


### 17.16.18 HOTFIX bloqueante — OwlError al abrir «Registrar rebaja» (2026-10-10)

- **Error real del navegador (Mauricio):** `EvalError: Can not evaluate python expression:
  (bool(not wizard_id.multi_sv))` — `Name 'wizard_id' is not defined` (`ListRenderer.evalColumnInvisible`).
- **Causa:** `column_invisible` se evalúa con el contexto del **formulario padre** (`parent`), no con los
  campos de cada fila ⇒ `wizard_id` no existe. **No** fue caché.
- **Corrección:** `column_invisible="not parent.multi_sv"` + carga explícita
  `<field name="multi_sv" invisible="1"/>` en el padre. Sin tocar Owl/assets/core; sin capturar la
  excepción; sin eliminar la condición.
- **Preservado:** cantidad editable, reparto como fuente de verdad, repartos a otros SV, identidad del
  material, `processed_lot_id` + `force_save`, disponibilidad/reservas/aplicación/reversa, permisos,
  atomicidad e idempotencia.
- **Pruebas:** casos A–E e invariantes de arch (ningún `column_invisible` con `wizard_id`; `multi_sv`
  cargado en el padre) = **20/20** en `test_sv_rebaja_ui_limpia.py`; regresión **362 pruebas, 4 fallas
  preexistentes, 0 errores**.
- **Límite:** **renderización real pendiente** (sin navegador). Estado: **«Incidencia bloqueante de
  renderización; aceptación pendiente»**. Módulo **18.0.1.14.1**.

<!-- actualizado: 2026-10-10 (12) — §17.16.18 HOTFIX OwlError de «Registrar rebaja» (`column_invisible`
fuera de contexto). Módulo 18.0.1.14.1. Versión 02 12.25.0 → 12.26.0. Sin commit/push. -->


<!-- actualizado: 2026-10-11 (1) — §17.16.19 AUDITORÍA INTEGRAL Y BLINDAJE DEL CICLO DE REBAJA DE ETIQUETAS
(AUD-ETQ-01..05). Cuatro defectos demostrados y corregidos sobre el mecanismo I2 existente:
**AUD-ETQ-01** inmutabilidad real del aplicado (`state` fuera de `I2_APPLIED_WRITABLE`; única transición
`applied → reversed` vía `action_reverse`); **AUD-ETQ-02** reversa con motivo obligatorio (paridad con
`madenat.processor.return.link`); **AUD-ETQ-03** mapa lote↔packing sin elección arbitraria ante colisión
(`_i2_build_packing_map`); **AUD-ETQ-04** causa del saldo concreta y trazable (`disponibilidad_detalle` +
acceso a los documentos que la explican). **Caso reportado explicado:** la etiqueta de la guía `19827` no
estaba disponible porque la imputación aplicada `IMP02220` (guía 1198) consumió su nominal; `lot_flow_type`
NULL en 147/151 lotes y `IMP02220` aplicada con 0 repartos SV = anomalías históricas **NO reparadas**
(propuesta dry-run + autorización). Suite nueva `test_sv_rebaja_blindaje.py` **0 failed / 0 errors of 7**;
regresión `madenat_lumber_logistics` **4 failed / 0 errors of 369** (mismas 4 preexistentes). **V3
(navegador) y concurrencia multi-cursor simultánea PENDIENTES. Sin reparación histórica.** Módulo
`madenat_lumber_logistics` **18.0.1.14.1 → 18.0.1.15.0**; `19` 1.17.0 → **1.18.0**; `03` 6.26.0 →
**6.27.0**; `02` 12.26.0 → **12.27.0**. Expediente: `AUDIT_REBAJA_ETIQUETAS_20261011/`. Sin commit/push. -->


<!-- actualizado: 2026-10-11 (2) — §17.16.20 CIERRE PROBATORIO DEL CICLO DE REBAJA DE ETIQUETAS
(AUD-ETQ-06..10): diagnóstico de IMP02220 (guía 19827: aplicada sin reparto SV; **válida según el código,
funcionalmente incompleta**; no reparada), contrato de «aplicación sin reparto» **BLOQUEADO** (decisión de
Mauricio), **concurrencia real OK** (cursores independientes + barrera: Q1/Q2/Q3, sin sobreconsumo, una
sola reversión, sin efectos físicos, 0 residuos), **seguridad multi-compañía** (nueva `ir.rule` para
`madenat.sv.imputation*`), motivo de reversa con `strip`, y ciclos A/B con balances (incl. nominal 5 /
reparto 3). Suite `test_sv_rebaja_cierre.py` **0 failed/0 errors of 8**; regresión `madenat_lumber_logistics`
**4 failed/0 errors of 377** (mismas 4 preexistentes). Módulo `madenat_lumber_logistics`
**18.0.1.15.0 → 18.0.1.16.0**; `19` 1.18.0 → **1.19.0**; `03` 6.27.0 → **6.28.0**; `02` 12.27.0 →
**12.28.0**. **V3 (navegador) PENDIENTE. Sin reparación histórica.** Expediente:
`AUDIT_REBAJA_ETIQUETAS_20261011/`. Sin commit/push. -->


<!-- actualizado: 2026-10-11 (3) — §17.16.21 CONTRATO DE APLICACIÓN SIN REPARTO: **propuesta de política
pendiente de aprobación** (Aplicar exige ≥1 reparto positivo a un SV autorizado; sin reparto sólo estado
no aplicado; el parcial mantiene el compromiso nominal con pendiente explícito), **validación backend
prevista** (`_i2_validate_payload`, no implementada), mensaje operativo, pruebas POL-01..08 (borrador no
registrado), **dry-run de IMP02220** (conservar con clasificación vs revertir y reasignar; NO ejecutado) y
**guion de navegador A–I**. Expediente `CONTRATO_APLICACION_20261011/`; `19` §19.23. **Contrato NO
modificado; BLOQUEADO por decisión de negocio.** Módulo `madenat_lumber_logistics` **18.0.1.16.0** (sin
cambio de versión). `19` 1.19.0 → **1.20.0**; `02` 12.28.0 → **12.29.0**. Sin commit/push. -->


<!-- actualizado: 2026-10-11 (4) — §17.16.21 **CONTRATO DE APLICACIÓN: POLÍTICA APROBADA POR MAURICIO E
IMPLEMENTADA**. Aplicar exige ≥1 reparto con cantidad positiva hacia un SV autorizado (validado en
`_i2_validate_payload`, antes de locks/techos/escritura; cubre interfaz/ORM/RPC sin efectos parciales);
sin reparto sólo estado **no aplicado**; parcial con **pendiente explícito** (`etiqueta_pendiente_m3`);
`NO_SV_CANDIDATE` pasa a **informativo**. Suite `test_sv_rebaja_contrato.py` **POL-01..08 = 0 failed/0
errors of 8**; regresión `madenat_lumber_logistics` **4 failed/0 errors of 385** (mismas 4 preexistentes).
4 pruebas previas actualizadas (T-I2-06, CAND-07/08/09). **IMP02220 sin reparar.** Módulo
`madenat_lumber_logistics` **18.0.1.16.0 → 18.0.1.17.0**; `19` 1.20.0 → **1.21.0**; `03` 6.28.0 →
**6.29.0**; `02` 12.29.0 → **12.30.0**. **Aceptación en navegador pendiente (guion A–I).** Expediente
`CONTRATO_APLICACION_20261011/`. Sin commit/push. -->


<!-- actualizado: 2026-10-11 (5) — §17.16.22 **PERSISTENCIA Y RECUPERACIÓN DEL TRABAJO (SAVE)**.
Incidencia «las asignaciones preparadas no se guardan»: **causa C1** (filas de reparto a **cantidad 0**
creadas por «Preparar asignación» hacían **fallar** «Guardar borrador» con `UserError`) + **C2** (un
borrador sin reparto positivo no se localizaba desde el SV). Corrección mínima en la **misma mecánica**:
el destino previsto a 0 **no bloquea** el guardado (no se persiste reparto inválido; el negativo sí se
rechaza); nuevo **`madenat.sv.imputation.work_sv_lot_id`** y panel «Trabajo en preparación» +
**`action_continue_preparation`** (Continuar) para localizar/continuar desde el SV; dominio del historial
ampliado. Suite `test_sv_rebaja_persistencia.py` (**SAVE-01..14, FLOW-01..03, PHY-01**) **18/18**;
3 pruebas previas actualizadas; regresión con las mismas 4 fallas preexistentes. Módulo
`madenat_lumber_logistics` **18.0.1.17.0 → 18.0.1.18.0**; `19` 1.21.0 → **1.22.0**; `03` 6.29.0 →
**6.30.0**; `02` 12.30.0 → **12.31.0**. **Aceptación en navegador pendiente.** Contrato de aplicación y
política de reservas **sin cambios**; IMP02220 y `lot_flow_type` histórico **intactos**. Sin commit/push. -->


<!-- actualizado: 2026-10-11 (6) — §17.16.23 **ACCIONES VISIBLES DEL ASISTENTE «REGISTRAR REBAJA»**.
Causa: el asistente (formulario amplio, `target="current"`) tenía sus acciones **sólo** en un `<footer>`
(no renderizado fuera de diálogo) ⇒ «Guardar borrador»/«Revisar y aplicar»/«Descartar» **invisibles**.
Corrección mínima: acciones en el **`<header>` nativo**, `<footer>` retirado, «Abrir documento»
(`action_open_document`), «Descartar y volver» (`action_discard_changes`) y confirmación con referencia
(`save_result`); «Continuar preparación» usa el mismo formulario amplio. Suite
`test_sv_rebaja_ui_acciones.py` (UI-01..05 + confirmación). Módulo `madenat_lumber_logistics`
**18.0.1.18.0 → 18.0.1.19.0**; `19` 1.22.0 → **1.23.0**; `03` 6.30.0 → **6.31.0**; `02` 12.31.0 →
**12.32.0**. **Aceptación en navegador pendiente.** Sin cambio de política; IMP02220 y `lot_flow_type`
histórico intactos. Sin commit/push. -->


<!-- actualizado: 2026-10-11 (7) — §17.16.24 **SIMPLIFICACIÓN OPERATIVA (recorrido de DOS acciones)**.
Solicitud de Mauricio: «sólo aplicar o guardar lo seleccionado; no obligar a abrir el documento». La
ventana pasa a **[Guardar] [Aplicar] [Volver]**; ya **no** se exige «Preparar asignación» ni Guardar antes
de Aplicar ni abrir el documento. `action_apply` sincroniza (vía `_i2_build_imputation`), aplica y
**permanece** (`apply_result`); `action_prepare` **permanece** (`save_result`); opciones avanzadas en «Más
opciones» (Abrir documento / Dejar pendiente / Proponer FIFO); tablas en sólo lectura tras aplicar;
mensajes según problema real (falta de cantidad vs. sin disponibilidad). Suite
`test_sv_rebaja_simple.py` (**SIMPLE-01..17** + **CLIENT-01..03**); 2 pruebas de UI y 4 de `res['res_id']`
actualizadas (mismas aserciones). Módulo `madenat_lumber_logistics` **18.0.1.19.0 → 18.0.1.20.0**; `19`
1.23.0 → **1.24.0**; `03` 6.31.0 → **6.32.0**; `02` 12.32.0 → **12.33.0**. **Aceptación en navegador
pendiente.** Contrato de aplicación y política de reservas **sin cambios**; permisos **sin ampliar**;
**sobrescritura concurrente de borradores sigue pendiente de autorización**; IMP02220 y `lot_flow_type`
histórico intactos. Sin commit/push. -->


<!-- actualizado: 2026-10-11 (8) — §17.16.25 **VOLVER A BORRADOR Y REASIGNAR (RESET)**. Autorización expresa
de Mauricio: `cancelled → draft` **controlada** (`action_reopen_to_draft`: motivo, permisos, guía, sin
trabajo activo, capacidad; locks + revalidación; idempotente). `write()` no elude la transición;
`applied`/`reversed → draft` prohibidos. Trazabilidad de anulación/reapertura + chatter + auditoría
`imputation_cancel`/`imputation_reopen` (core aditivo). Incidencia **IMP04823** diagnosticada (A+D) y
mensaje operativo. Suite `test_sv_rebaja_reset.py` **14/14**; regresión con las mismas 4 fallas
preexistentes. **Concurrencia RESET-16/17 pendiente.** Módulos `madenat_lumber_logistics`
**18.0.1.20.0 → 18.0.1.21.0** (+ `madenat_lumber_core` audit log); `19` 1.24.0 → **1.25.0**; `03` 6.32.0 →
**6.33.0**; `02` 12.33.0 → **12.34.0**. IMP04823/IMP02220 intactos. Sin commit/push. -->

---

<!-- actualizado: 2026-10-12 (1) — §17.16.26 **BLINDAJE LOCAL Y ESTABILIZACIÓN (AUD-ETQ-07/08)**. (a) Reapertura
`cancelled → draft`: autorización por **token de PROCESO** (no acepta identidad del cliente ni flag de
contexto); la **vía directa de `write` se rechaza**; `applied`/`reversed → draft` siguen prohibidos. (b)
**Concurrencia REAL RESET-16/17** acreditada con transacciones independientes (advisory lock + revalidación):
una sola transición, sin sobreconsumo, sin doble reserva ni doble auditoría; limpieza test-only verificada.
(c) Advertencias de cálculo **eliminadas**: `stock.lot` `sv_assignment_*` (separación de computes + 
`compute_sudo=False`) y consola de intake `volume_detail_line_ids` (dependencia corregida a la identidad del
origen). Suites: `TestSvRebajaReset` (14) + `TestSvRebajaResetConcurrency` (3) + `TestIntakeConsoleComputeDepends`
(2) ⇒ **0 failed / 0 error**. Módulos `madenat_lumber_logistics` **18.0.1.21.0 → 18.0.1.22.0**;
`madenat_lumber_intake` **18.0.0.11.0 → 18.0.0.12.0**; `19` 1.25.0 → **1.26.0**; `03` 6.33.0 → **6.34.0**;
`02` 12.34.0 → **12.35.0**. **Sobrescritura de borradores**: propuesta registrada, **pendiente** de
autorización de Mauricio. **Sin commit/push/despliegue; TEST remoto y datos históricos intactos.** -->

---

<!-- actualizado: 2026-10-12 (2) — §17.16.27 **VERIFICACIÓN PROBATORIA DE CUATRO PUNTOS (P1–P4)**. P1:
concurrencia sobre la capacidad de la MISMA etiqueta retornada (dos guías sobre un mismo lote; advisory lock +
revalidación de capacidad; **sin cambio de código**). P2: recomputación REAL de las métricas de intake en el
MISMO entorno (defecto + corrección por invalidación dirigida en el detalle del volumen). P3: saldos
almacenados **canónicos** (`compute_sudo=True`) vs proyección por usuario (`compute_sudo=False`); sin
AccessError ni exposición entre compañías. P4: **vía privada de transición** `_i2_write_protected_state`
(elimina el registro global de tokens; sin ventana de autorización reutilizable). Suites dirigidas
**0 failed / 0 error** (P1 3 + P2 1 + P3 2 + P4 7). Módulos `madenat_lumber_logistics` **18.0.1.22.0 →
18.0.1.23.0**; `madenat_lumber_intake` **18.0.0.12.0 → 18.0.0.13.0**; `19` 1.26.0 → **1.27.0**;
`03` 6.34.0 → **6.35.0**; `02` 12.35.0 → **12.36.0**. Sin commit/push/despliegue; TEST remoto intacto. -->

---

<!-- actualizado: 2026-10-12 (3) — §17.16.28 **BLINDAJE DE BORRADORES (LOCK)**. Contrato de concurrencia
**APROBADO por Mauricio**: `edit_version` (versión lógica del documento) + **guard del documento**
(`pg_try_advisory_xact_lock` ns 1 + comparación de `expected_edit_version` + flush) → Guardar/Aplicar basados en
una versión obsoleta se **rechazan** (no sobrescriben ni fusionan); botón **«Recargar versión actual»**;
líneas/repartos y edición directa **elevan** la versión; sin adopción silenciosa del primer borrador ajeno;
mensaje operativo sin error técnico. Recorrido sencillo intacto. Suite `test_sv_rebaja_save_lock.py`
(**LOCK-01..19**, FLOW-01..03, PHY-01) + reproducción del defecto ⇒ **0 failed / 0 error**. **Límite declarado:**
form-vs-form directo (sin asistente) sigue el ORM estándar (pendiente). Módulo `madenat_lumber_logistics`
**18.0.1.23.0 → 18.0.1.24.0**; `19` 1.27.0 → **1.28.0**; `03` 6.35.0 → **6.36.0**; `02` 12.36.0 → **12.37.0**.
Sin commit/push/despliegue; TEST remoto intacto. -->

---

<!-- actualizado: 2026-10-12 (4) — §17.16.29 **CIERRE V1–V3 del blindaje de borradores**. V1: cobertura de la
EDICIÓN DIRECTA — Alternativa A (`force_save` reutilizando `edit_version`; guard atómico en `write`) ⇒ matriz
**C1–C8 ACREDITADA** (asistente↔asistente, directo↔asistente, form↔form, línea→padre, directo→aplicar,
asistente→estado, transición→contenido); sin retirar permisos; límite residual: escritura ORM/RPC **sin**
`edit_version`. V2: evidencia de **cliente** **PENDIENTE** (sin navegador; guion entregado). V3: transacción y
bloqueos **ACREDITADA** (TX-01..13; orden determinista `1→2→3`; rechazo por VERSIÓN con lock libre y por LOCK
ocupado; sin reintento automático; rollback íntegro). Módulo `madenat_lumber_logistics` **18.0.1.24.0 →
18.0.1.25.0**; `19` 1.28.0 → **1.29.0**; `03` 6.36.0 → **6.37.0**; `02` 12.37.0 → **12.38.0**. Sin
commit/push/despliegue; TEST remoto intacto. -->

#### 17.16.19 Auditoría integral y blindaje del ciclo de rebaja de etiquetas (AUD-ETQ-01..05, 2026-10-11)

> **Dictamen: COMPLETO CON LÍMITES.**
> El «ciclo de rebaja documental de etiquetas» (I2, `madenat.sv.imputation`) **existe, es persistente y opera** sobre el mecanismo único (modelo + asistente + `action_apply`/`action_reverse`). La auditoría **confirmó cuatro defectos reales** (uno de ellos explica la captura «disponibilidad 0, sin reparto, aviso genérico») y se corrigieron con validación y pruebas. Se añadieron **7 pruebas** (AUD-ETQ-01..05) y se ajustaron 5 archivos de pruebas existentes al motivo obligatorio de reversa.

**Fuente (literal):** `AUDIT_REBAJA_ETIQUETAS_20261011/README.md` §1. Módulo `madenat_lumber_logistics` **18.0.1.14.1 → 18.0.1.15.0**.

#### 17.16.20 Cierre probatorio del ciclo de rebaja de etiquetas (AUD-ETQ-06..10, 2026-10-11)

> **Dictamen final: COMPLETO TÉCNICAMENTE; ACEPTACIÓN DEL USUARIO PENDIENTE.** Concurrencia real, seguridad multi-compañía, inmutabilidad/reversa, ciclos con balances y diagnóstico de IMP02220 cerrados con pruebas. Queda **bloqueada por decisión de negocio** una única cuestión (contrato de «aplicación sin reparto», §CI-3) y **pendiente V3 (navegador)**. Módulo **18.0.1.15.0 → 18.0.1.16.0**.

**Fuente (literal):** `AUDIT_REBAJA_ETIQUETAS_20261011/README.md` §«CIERRE PROBATORIO (2026-10-11, 2.ª sesión)».

#### 17.16.21 Contrato de aplicación sin reparto (política aprobada e implementada, 2026-10-11)

> En la rebaja a SV, «Aplicar» requiere al menos un reparto válido con cantidad positiva hacia un SV autorizado. Sin reparto, el documento sólo puede permanecer en un estado no aplicado. El reparto parcial mantiene la política vigente de compromiso nominal, mostrando expresamente la cantidad que queda comprometida sin repartir.

**Estado (literal):** POLÍTICA APROBADA POR MAURICIO (2026-10-11) e IMPLEMENTADA en `madenat_lumber_logistics` **18.0.1.17.0**. **Aceptación operativa (navegador) pendiente.**
**Fuente (literal):** `CONTRATO_APLICACION_20261011/README.md` §1.

#### 17.16.22 Persistencia y recuperación del trabajo de rebaja (SAVE, 2026-10-11)

> **Incidencia:** «Al preparar las asignaciones, estas no van quedando guardadas» (Mauricio).
> **C1 — Pérdida real en el guardado.** «Preparar asignación» (`action_assign_selected`) crea filas de reparto a **cantidad 0**. Al pulsar **«Guardar borrador»** (`action_prepare` → `_i2_build_imputation`), el código **lanzaba `UserError`** ante **cualquier** fila a 0 ⇒ **no se creaba/actualizaba el documento**.
> **C2 — Falta de acceso.** Un borrador **sin reparto positivo** no se localizaba desde el SV: el dominio del historial (`action_open_sv_rebajas`) era `[('sv_line_ids.sv_lot_id','=', id)]`, que exige una fila de reparto.

**Fuente (literal):** `SAVE_REBAJA_20261011/README.md` §1. Módulo `madenat_lumber_logistics` **18.0.1.17.0 → 18.0.1.18.0**.

#### 17.16.23 Acciones visibles del asistente «Registrar rebaja» (UI, 2026-10-11)

> **Incidencia:** Mauricio no ve acciones para guardar ni un recorrido claro para mantener las rebajas.
> El asistente se abre como **formulario amplio** (`action_madenat_sv_imputation_wizard`, `target = current`) pero sus operaciones estaban **sólo** dentro de un **`<footer>`**. En Odoo, un `<footer>` de vista form **se renderiza únicamente en diálogos** (`target="new"`); en un formulario de **página completa** (`target="current"`) **no se muestra**. La vista **no tenía `<header>`**.

**Fuente (literal):** `UI_SAVE_REBAJA_20261011/README.md` §1. Módulo `madenat_lumber_logistics` **18.0.1.18.0 → 18.0.1.19.0**.

#### 17.16.24 Simplificación operativa: recorrido de dos acciones (SIMPLE, 2026-10-11)

> **Solicitud expresa de Mauricio:** «sólo aplicar o guardar lo seleccionado; no complicar el flujo ni obligar a abrir el documento para aplicar».
> **Elegir guía → seleccionar material → indicar m³ → [Guardar] o [Aplicar]**, y **[Volver]** para navegar. No se exige «Preparar asignación», ni Guardar antes de Aplicar, ni abrir el documento, ni cambiar de pestaña. La simplificación afecta la **interacción**, no las validaciones ni la trazabilidad.

**Fuente (literal):** `SIMPLE_REBAJA_20261011/README.md` §1. Módulo `madenat_lumber_logistics` **18.0.1.19.0 → 18.0.1.20.0**.

#### 17.16.25 Volver a borrador y reasignar (RESET, 2026-10-11)

> **Solicitud expresa de Mauricio:** si una rebaja está **cancelada**, poder **volverla a borrador**, corregir sus asignaciones y continuar.
> `IMP04823` (id **2733**) existe con **`state = cancelled`** y `guia_processing_id = 1198` (guía «19827»). El asistente quedaba **ligado** al documento cuando era borrador; al **cancelarse**, `Guardar`/`Aplicar` invocaban `_i2_build_imputation`, que lanzaba «La imputación IMP04823 ya no admite preparación (estado cancelled)».
> **Contrato de «Volver a borrador»:** transición **controlada** `cancelled → draft` (autorizada). **Precondiciones**: estado `cancelled`; permiso (Operaciones/Jefatura/Gerencia); compañía autorizada (regla de registro); guía elegible vigente; **ausencia** de trabajo activo sobre la guía.

**Fuente (literal):** `RESET_REBAJA_20261011/README.md` §1/§2. Módulos `madenat_lumber_logistics` **18.0.1.20.0 → 18.0.1.21.0** y `madenat_lumber_core` (audit log, 2 valores aditivos).

#### 17.16.26 Blindaje local y estabilización (AUD-ETQ-07/08, 2026-10-12)

> 1. **Vía directa de `write` (`cancelled → draft`)**: `write()` autorizaba la transición aceptando una **identidad suministrada por el cliente** (`reopened_by_id` + `reopen_reason`), **sin** ejecutar las mismas garantías que `action_reopen_to_draft` (no corría `_i2_validate_reopen`, ni locks, ni auditoría).
> 2. **Advertencia `stock.lot` `sv_assignment_*`**: 6 campos compartían `_compute_sv_assignment` con `store` mixto (4 con `store=True`, 2 con `store=False`) ⇒ Odoo advertía `inconsistent 'store'` e `inconsistent 'compute_sudo'`.

**Correcciones (literal):** AUD-ETQ-07 (logistics, `madenat_sv_imputation.py`: token efímero de PROCESO), AUD-ETQ-08a (logistics: separación `_compute_sv_assignment`/`_compute_sv_assignment_live`) y AUD-ETQ-08b (intake, `intake_console.py`: dependencia de `_compute_review_metrics`).
**Versiones antes (literal):** logistics `18.0.1.21.0`, intake `18.0.0.11.0`, core `18.0.6.6.0`.
**Fuente (literal):** `BLINDAJE_REBAJA_LOCAL_20261012/README.md` §0/§1/§2.

#### 17.16.27 Verificación probatoria de cuatro puntos de blindaje (P1–P4, 2026-10-12)

> | Punto | Dictamen | Resumen |
> |---|---|---|
> | **P1** — concurrencia sobre la MISMA etiqueta retornada | **ACREDITADO** | El mecanismo (advisory lock + revalidación de capacidad) ya lo garantiza; **sin cambio de código**. |
> | **P2** — recomputación real de intake | **CORREGIDO Y ACREDITADO** | Defecto confirmado (caché obsoleta en el MISMO entorno) → corrección por invalidación dirigida. |
> | **P3** — saldos almacenados vs derechos del usuario | **CORREGIDO Y ACREDITADO** | Defecto confirmado (`compute_sudo=False` → `AccessError`/dependencia del usuario) → `compute_sudo=True` en los canónicos. |
> | **P4** — aislamiento y limpieza de la autorización | **CORREGIDO Y ACREDITADO** | Defecto confirmado (token global sin identidad de transacción) → vía privada de transición. |

**Fuente (literal):** `VERIF_CUATRO_PUNTOS_20261012/README.md` §1.

#### 17.16.28 Blindaje de borradores: protección contra sobrescritura concurrente (LOCK, 2026-10-12)

> **CORREGIDO Y ACREDITADO.** El riesgo «la última escritura gana» queda resuelto para el **recorrido del asistente** (Guardar/Aplicar/Dejar pendiente): una edición basada en una versión obsoleta se **rechaza de forma controlada**; no se sobrescribe ni se fusiona; se puede **recargar** la versión vigente. **Límite declarado:** la edición simultánea de dos **formularios persistentes directos** (form-vs-form, sin asistente) queda **pendiente** (comportamiento ORM estándar de Odoo).

**Fuente (literal):** `BLINDAJE_SOBRESCRITURA_20261012/README.md` §1. **Autorización:** Mauricio.

#### 17.16.29 Cierre V1–V3 del blindaje de borradores (2026-10-12)

> | Verificación | Dictamen |
> |---|---|
> | **V1** — cobertura de cruces con edición directa | **CORREGIDA Y ACREDITADA** (matriz C1–C8; límite residual ORM-sin-versión declarado) |
> | **V2** — comportamiento real del cliente | **PENDIENTE** (sin navegador/herramienta; guion entregado; no se sustituye por ORM) |
> | **V3** — transacción, SerializationFailure y orden de bloqueos | **ACREDITADA** (TX-01..13) |

**Fuente (literal):** `CIERRE_SOBRESCRITURA_V123_20261012/README.md` §1.

#### 17.16.30 HOTFIX OWL — «Agregar una línea» en el documento de rebaja (`div.oe_chatter`, 2026-10-12)

**Incidencia:** en `madenat.sv.imputation` (p. ej. `IMP04823`), «Agregar una línea» en dos tablas del
formulario ⇒ `OwlError: TypeError: Cannot read properties of undefined (reading 'includes') at get
urlRelation at Many2OneField.template`.

**Causa demostrada:** Odoo 18 CE (`18.0-20260817`) **no compila** el marcado heredado `div.oe_chatter` (el
compilador registra `selector: "chatter"` ⇒ `<chatter/>`; `oe_chatter` no existe en los assets). Al no haber
chatter, `message_ids`/`message_follower_ids` se renderizaban como **listas o2m editables** por defecto
(`mail.message`/`mail.followers`) con «Agregar una línea»; la columna `res_id` (`many2one_reference`) sin
relación determinable dispara el TypeError.

**Corrección mínima:** `div.oe_chatter` → `<chatter/>` en `view_madenat_sv_imputation_form` y
`view_madenat_processor_return_link_form`. Sin cambios de modelo/datos/permisos. Ver `19` §19.33.

**Pruebas:** VIEW-01..05 de servidor 5/5 (`tests/test_hotfix_owl_chatter.py`); `madenat_lumber_logistics`
4 failed/0 error de 506 (mismas 4 preexistentes; baseline 4/444 ⇒ 0 nuevas); core+intake+logistics 6/4 de
1284 (mismo conjunto que el baseline 6/1217 ⇒ 0 nuevas). **Navegador PENDIENTE** (sin navegador; guion).
Módulo `madenat_lumber_logistics` **18.0.1.25.0 → 18.0.1.26.0**. Sin commit/push; TEST remoto intacto.

<!-- actualizado: 2026-10-12 (5) — §17.16.30 HOTFIX OWL chatter (`div.oe_chatter` → `<chatter/>`) en
`sv_imputation`/`processor_return_link`. Versión 02 12.38.0 → **12.39.0** (cabecera alineada: estaba 12.34.0,
por debajo de 12.38.0 ya registrado por entregas previas). **Numeración corregida:** esta sección se había
rotulado `17.16.19` (ya reservada por la entrega AUD-ETQ-01..05) → renumerada a **17.16.30**. **Hallazgo (NO
corregido aquí):** los changelog citan §17.16.19..§17.16.29, pero esas secciones de cuerpo NO existen en 02
(solo comentarios; su contenido vive en los expedientes `AUDIT_REBAJA_ETIQUETAS_20261011/`,
`RESET_REBAJA_20261011/`, `SIMPLE_REBAJA_20261011/`, `UI_SAVE_REBAJA_20261011/`, `SAVE_REBAJA_20261011/`,
`CONTRATO_APLICACION_20261011/`, `BLINDAJE_REBAJA_LOCAL_20261012/`, `CIERRE_SOBRESCRITURA_V123_20261012/`).
No se reconstruyen de memoria. Nota: no existía entrada (5) de 2026-10-12 (el cierre §19.32 no registró entrada
en 02). Sin commit/push/despliegue. -->

<!-- actualizado: 2026-10-12 (6) — D13 (FASE 2 limitada): **restituidos los CUERPOS de §17.16.19…§17.16.29**
(antes sólo citados). Transcripción **LITERAL** desde los expedientes (`AUDIT_REBAJA_ETIQUETAS_20261011`,
`CONTRATO_APLICACION_20261011`, `SAVE_REBAJA_20261011`, `UI_SAVE_REBAJA_20261011`, `SIMPLE_REBAJA_20261011`,
`RESET_REBAJA_20261011`, `BLINDAJE_REBAJA_LOCAL_20261012`, `VERIF_CUATRO_PUNTOS_20261012`,
`BLINDAJE_SOBRESCRITURA_20261012`, `CIERRE_SOBRESCRITURA_V123_20261012`), con su fuente en cada sección. **No**
se modificó ninguna línea existente; **sólo** se insertaron cuerpos en su posición numérica (§17.16.19..29
entre §17.16.18 y §17.16.30). **26/26 referencias cruzadas resueltas**; versiones **monótonas**; marcadores
balanceados. Versión 02 12.39.0 → **12.40.0**; **índice 12.29.0 → 12.30.0**. Sin commit/push/despliegue. -->

---

## 18. Procedimiento Operacional de Despliegue a TEST Remoto (G9 AD-120 — Borrador, No Ejecutado)

> **ESTADO FORMAL: BORRADOR, NO EJECUTADO.**
> Este procedimiento define los pasos exactos para una futura entrega y despliegue hacia el servidor TEST remoto (`144.22.50.236` / `/opt/odoo18-test`).
> En cumplimiento estricto de **D4 / R6**, este procedimiento **NO ha sido ejecutado** en esta intervención y permanece como diseño canónico aprobado para cuando se autorice formalmente la ventana de despliegue.

### 18.1 Método de Entrega y Transferencia (Sin Git Pull)
- **Constatación de Entorno (§17.14):** En el servidor TEST remoto (`144.22.50.236`), la carpeta `/opt/odoo18-test/custom_addons` **no es un repositorio Git clonado** conectado a la rama de desarrollo `feat/guia-correccion-documental-preservada-20261002`, y el repositorio `/opt/odoo18-test` presenta restricciones de propiedad (`dubious ownership` en git 2.25.1).
- **Método Canónico de Entrega:** Se prohíbe asumir `git pull`. La entrega de código debe realizarse exclusivamente mediante:
  1. Empaquetado de artefactos o sincronización dirigida vía `rsync` sobre SSH (`rsync -avz --exclude '__pycache__' --exclude '.git' ./custom_addons/madenat_lumber_core/ usuario@144.22.50.236:/opt/odoo18-test/custom_addons/madenat_lumber_core/`).
  2. O aplicación de un paquete de cambios `.tar.gz` o `git archive` generado localmente desde el commit de cierre 4G.
  3. No se tocan carpetas legadas (`.bak/`, `views.backup/`) existentes en el remoto.

### 18.2 Módulos a Actualizar (Determinación Quirúrgica, Nunca `-u all`)
- **Regla Estricta:** Queda terminantemente prohibido ejecutar `-u all` (violación de R6).
- **Comparación de Manifiestos:**
  - `madenat_lumber_core`: Versión local 18.0.6.16.0 frente a 18.0.6.15.0 instalada. **REFIERE ACTUALIZACIÓN OBLIGATORIA** (`-u madenat_lumber_core`).
  - `madenat_lumber_intake`: 18.0.0.18.0 (idéntica en manifiesto y BD remota). No requiere `-u` a menos que se hayan modificado vistas.
  - `madenat_lumber_billing`: En caso de que la salud previa (G3) reporte discrepancia de versión (instalada `18.0.1.0.0` vs manifiesto `1.0.0`), se puede incluir `-u madenat_lumber_billing`.
  - Comando canónico previsto:
    ```bash
    odoo -c /etc/odoo/odoo.conf -d madenat_test --no-http --stop-after-init -u madenat_lumber_core
    ```

### 18.3 Respaldo Previo Obligatorio (Base de Datos, Filestore y Código)
Antes de tocar cualquier archivo en el servidor remoto:
1. **Base de Datos PostgreSQL:**
   ```bash
   sudo -u postgres pg_dump -Fc madenat_test > /opt/backups/madenat_test_pre_4g_$(date +%Y%m%d_%H%M%S).dump
   ```
2. **Filestore de Odoo:**
   ```bash
   sudo tar -czf /opt/backups/filestore_madenat_test_$(date +%Y%m%d_%H%M%S).tar.gz /var/lib/odoo/.local/share/Odoo/filestore/madenat_test
   ```
3. **Snapshot de Código Remoto:**
   ```bash
   sudo tar -czf /opt/backups/custom_addons_pre_4g_$(date +%Y%m%d_%H%M%S).tar.gz /opt/odoo18-test/custom_addons
   ```

### 18.4 Script de Salud Pre-Deploy (G3) — Ejecución Previa y Posterior
1. **Ejecución Previa (Lectura Inocua):**
   ```bash
   odoo shell -c /etc/odoo/odoo.conf -d madenat_test --no-http < /opt/odoo18-test/custom_addons/madenat_lumber_core/scripts/pre_deploy_health_check.py
   ```
   - Debe arrojar **0 CRÍTICOS** (código de salida 0).
   - Registra advertencias conocidas (D1: `out_of_table_behavior = 'direct'`, D2: `is_patio = False`).
2. **Ejecución Posterior:** Tras el `-u madenat_lumber_core`, se reejecuta el script G3. Si el script arroja código de salida 1 (CRÍTICO), se detiene el proceso y se inicia reversa.

### 18.5 Medición Dual de Integridad MD5 (Consulta Fijada G4 / H1 / H4 AD-121)
En el propio servidor remoto, ejecutar la consulta canónica fijada antes y después del despliegue:
```sql
SELECT 'stock_lot' AS tbl, COUNT(*) AS cnt,
  md5(string_agg(id::text || COALESCE(write_date::text,'') || COALESCE(name::text,''), ',' ORDER BY id)) AS hash
FROM stock_lot
UNION ALL
SELECT 'madenat_guia_processing_line', COUNT(*),
  md5(string_agg(id::text || COALESCE(write_date::text,'') || COALESCE(vol_shipment_m3::text,''), ',' ORDER BY id))
FROM madenat_guia_processing_line
UNION ALL
SELECT 'lumber_shipment_line', COUNT(*),
  md5(string_agg(id::text || COALESCE(write_date::text,'') || COALESCE(export_volume_m3::text,''), ',' ORDER BY id))
FROM lumber_shipment_line;
```
- **Línea Base Canónica Fijada:**
  - `stock_lot` (152 filas): `6667a4bd9f3aeff24a8588d32da23ed2` (Línea base auditada y fijada al 2026-10-18; referencia previa Bloque 4: `3871c02145712833e3ad9eea526405c5`).
  - `madenat_guia_processing_line` (82 filas): `b43a26b6fd072ff96ed075ca1e2f585e` (100% Invariante).
  - `lumber_shipment_line` (11 filas): `b048f9428859b4c960b83b9ddf1cc701` (100% Invariante).
- **Consulta B (Hash MD5 de Volúmenes Redondeados a 4 decimales):**
  - `stock_lot`: `5c2152193194066e5585b383ffe3673a` (100% Invariante).
  - `madenat_guia_processing_line`: `356e70066083febd59645c1212e11ece` (100% Invariante).
  - `lumber_shipment_line`: `bb5863f5850244b06b9235c2c595709b` (100% Invariante).
  - Suma de volúmenes complementaria al 2026-10-18: 531.2920 m³ (lotes), 295.8210 m³ (guías) y 53.6030 m³ (embarques).
- **Criterio de Parada:** Cualquier discrepancia en los hashes de `madenat_guia_processing_line` o `lumber_shipment_line`, o en los hashes de volúmenes de la Consulta B aborta inmediatamente el despliegue.

### 18.6 Efecto de `noupdate="1"` sobre Datos y Parámetros
- Los 15 anchos de la tabla S2S y los parámetros del sistema declarados en `data/lumber_width_s2s_data.xml` y `data/ir_config_parameter_data.xml` están marcados con `noupdate="1"`.
- **Efecto operativo:** El comando `-u madenat_lumber_core` **no sobreescribe** valores ya existentes en la BD remota (respeta D1: `out_of_table_behavior = 'direct'` y ediciones manuales de Cristhian). Solo creará registros si sus XML IDs no existen aún en la base de datos.

### 18.7 Verificación Posterior de Solo Lectura (Vectores Canónicos)
Una vez actualizado Odoo, se verifican en `odoo shell`:
1. **15 Anchos Canónicos S2S:** Mapeo de 115 mm resuelve a 4.375" (etiqueta '4 3/8') + sobreancho 0.125" = 4.500" (volumen 1.742 m³ en 100 pzas).
2. **Vectores de Blanks (registro real `f5085` ID 1):**
   - 100 mm: 16 ft × 250 = 4.425 m³; × 270 = 4.778 m³.
   - 140 mm: 16 ft × 250 = 5.899 m³; × 270 = 6.371 m³.
3. **Preservación de Volumen Documental:** Lotes con `vol_documental_m3 > 0` conservan su volumen sin recálculo.

### 18.8 Criterios de Parada y Plan de Reversa (Rollback)
- **Criterios de Parada Inmediata:**
  - Falla de sintaxis o error de carga durante `-u madenat_lumber_core`.
  - Discrepancia en los hashes MD5 históricos de `madenat_guia_processing_line` o `lumber_shipment_line`.
  - Script G3 arroja código de salida 1 (CRÍTICO).
- **Procedimiento de Reversa:**
  1. Detener servicio Odoo (`sudo systemctl stop odoo18-test`).
  2. Restaurar dump de base de datos (`dropdb madenat_test && createdb madenat_test && pg_restore -d madenat_test /opt/backups/madenat_test_pre_4g_*.dump`).
  3. Restaurar snapshot de código anterior en `/opt/odoo18-test/custom_addons`.
  4. Reiniciar servicio (`sudo systemctl start odoo18-test`).

### 18.9 Lista de Validación Funcional para Cristhian Elgueta (UAT)
1. **Configuración > Anchos S2S (`lumber.width.s2s.map`):**
   - Confirmar visibilidad de los 15 anchos activos (75 a 155 mm).
   - Verificar que 115 mm muestre 4.375" decimal y fracción "4 3/8".
   - Probar edición de una etiqueta/decimal y comprobar que el chatter registra el cambio con usuario y fecha.
   - Comprobar que si se intenta guardar una etiqueta incoherente (ej. '4 3/8' con 4.125), el sistema rechaza el guardado con mensaje claro de coherencia.
2. **Recepción de Madera (Blanks):**
   - Ingresar lote de Blanks con perfil `f5085` y verificar cálculo de volumen con espesor 1.5" y ancho S2S + 1/8".
   - Confirmar que lotes con volumen documental declarado conservan su valor.
3. **Patios y Ubicaciones:**
   - Confirmar que los filtros de patio operan normalmente (D2 mantiene pendientes documentados).


