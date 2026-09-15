# MADENAT — Estado de Continuidad Técnica

**Versión documental:** 12.2.0
**Fecha de actualización:** 2026-09-12  <!-- actualizado: 2026-09-12 — AD-64 (costeo real, sin prorrateo parcial) y AD-65 (diseño aprobado recepción a granel + Balance de Masa + consolidación) registrados como frentes activos. -->
**Estado:** ESTABLE PARA CONTINUIDAD TÉCNICA Y REFACTORIZACIÓN ESTRUCTURAL CERRADA. La consolidación documental está completada. Persisten brechas funcionales/técnicas y validaciones UAT pendientes. **Último cierre técnico: `1466f24` (2026-08-20)** — robustecimiento del Core de perfiles de ingesta; el frente sigue **abierto en continuidad** aunque el técnico esté validado.

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
