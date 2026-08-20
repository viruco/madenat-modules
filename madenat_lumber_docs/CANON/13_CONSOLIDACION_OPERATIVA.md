# 13 — Consolidación Operativa: Ingesta (Producto y Procesados), Reglas y Trazabilidad

**Versión documental:** 1.5.0
**Fecha de actualización:** 2026-08-19
**Estado:** ✅ Vigente — Documento canónico de consolidación operativa (no sustituye a `00`, `12` ni `04`; los referencia). Incluye blindaje de OC en Producto (Intake, AD-52), resolución completa de la diferencia de Procesados por AD-54, y nota de homologación UX "Modificar origen" (AD-55).

> Este documento consolida decisiones, flujos y brechas que ya existen en la documentación del
> proyecto. NO introduce funcionalidad, reglas, campos ni comportamientos nuevos. Cuando una regla
> proviene de un hallazgo de auditoría reciente y aún no estaba formalizada, se indica su origen
> explícitamente. Ante contradicción entre documentos, no se elige versión en silencio: se registra
> en la sección «Registro de contradicciones y vacíos».

---

## 1. Propósito y alcance

Consolidar, en una única fuente de referencia, el flujo operativo de ingesta para **Producto**
(madera comprada, perfiles Blank/S2S/aserrada) y **Procesados** (madera que retorna de servicio
externo/maquila), junto con:

- las reglas de negocio confirmadas,
- los controles obligatorios previos a la creación de stock,
- la política de trazabilidad documental e histórica,
- el estado (definido / verificado / pendiente / brecha / contradicción) de cada afirmación.

**Fuente de verdad ante contradicción** (según `CANON/INDICE_DOCUMENTACION.md` §8):
1. Documento canónico del tema (`00`, `12`, `04`).
2. `04_DECISION_LOG.md`.
3. `02_CONTINUIDAD.md`.
4. Código fuente (verdad funcional).
5. Histórico (contexto).

---

## 2. Fuentes documentales revisadas

| Fuente | Tipo | Relevancia |
|---|---|---|
| `CANON/00_ARQUITECTURA.md` | Canon | Gates, modelos, side effects, staging |
| `CANON/12_FLUJOS_INGESTA.md` | Canon | Discriminación Producto vs Procesados |
| `CANON/04_DECISION_LOG.md` | Canon | AD-04, AD-27, AD-29, AD-30, AD-39… |
| `CANON/03_TESTS.md` | Canon | Matriz T01–T33, precisión de decimales |
| `CANON/02_CONTINUIDAD.md` | Canon | Checkpoint vivo, riesgos |
| `WIKI/02_TECNICO/*` (arquitectura_ingesta_recepciones, modelo_lotes, validadores_checklist, flujo_dimensiones_comerciales, madenat_lumber_logistics) | WIKI | Detalle técnico derivado |
| `WIKI/04_DECISIONES/DEC-002_sin_procesamiento_fisico.md` | WIKI | Antecedente de decisión (superada) |
| Código `madenat_lumber_core/models/*.py` | CODE | Verdad funcional (reception_parser, reception_service, madenat_guia_processing, stock_lot, utils_uom) |

---

## 3. Flujo consolidado de Producto (ingesta de compra)

Confirmado en código y documentación (`00_ARQUITECTURA`, `12_FLUJOS_INGESTA` §4).

1. **Carga del documento fuente (Excel/PDF).**
   - `reception_parser.parse_excel()` / `parse_dispatch_guide()` / `parse_purchase_order()`.
   - Perfiles soportados: `f5085` (Blank), `f1550` (S2S), `metric`.
   - Gate 0 (`Gate0PreUpload`) valida archivo (tipo, tamaño). Sin efectos en stock. **CODE + CANON**
2. **Procesamiento/lectura del archivo.**
   - Dispatcher centralizado en `reception_parser.py`. **CODE**
3. **Ingreso a staging sin crear stock.**
   - Modelo `lumber.reception.line` (buffer). **CODE + CANON** (`00` §4.1)
4. **Asignación de nominales.**
   - `thickness_nominal`, `width_nominal`, `thickness_visual` vía `_apply_thickness_visual()` y wizard de asignación masiva. **CODE** (`lumber_reception.py:552`)
5. **Validación visual por el usuario.**
   - UI de staging (`lumber_reception_views.xml`), edición inline/masiva. **CODE + CANON**
6. **Validación mediante fórmulas y reglas aplicables.**
   - Gate 2 (`Gate2CommercialAnalysis`) y guardia GB-1 (staging completo) en `action_confirm_reception()`. **CODE** (`ingestion_gate.py`, `lumber_reception.py:2727`)
7. **Confirmación y envío a stock.**
   - Gate 3 (`Gate3PreCommit.generate_signature()`) genera `audit_snapshot` + `audit_hash` (SHA-256).
   - `LumberReceptionService.create_lots_from_staging()` crea/actualiza `stock.lot`.
   - `create_stock_picking()` crea `stock.picking`/`stock.move`/`stock.move.line`. **CODE + CANON**

---

## 4. Flujo consolidado de Procesados (guía de servicio/maquila)

Confirmado en código y documentación (`12_FLUJOS_INGESTA` §3, `00_ARQUITECTURA` §4.3).

1. **Carga del documento fuente (Excel/PDF de servicio).**
   - `madenat.guia.processing` (cabecera) + `madenat.guia.processing.line` (staging). **CODE**
   - Tipo de recepción `service` = "Servicio Externo (Cepillado/Procesamiento)". **CODE** (`madenat_guia_processing.py:605`)
2. **Procesamiento/lectura del archivo.**
   - Parseo disperso en `madenat_guia_processing.py` (`_parse_dispatch_pdf`, `_parse_packing_excel`, `_parse_excel_data_core`). **CODE** (sin dispatcher equivalente a `reception_parser`) — ver brecha.
3. **Ingreso a staging sin crear stock.**
   - `processing_line_ids` → `madenat.guia.processing.line`. **CODE**
4. **Asignación de nominales.**
   - `action_assign_commercial_defaults()` / "Fijar Nominal Masivo". **CODE** (`madenat_guia_processing.py:1048`, `1492`)
5. **Validación visual por el usuario.**
   - "tabla de verificación visual (Staging)" exigida por `do_full_processing()`. **CODE** (`madenat_guia_processing.py:863`)
6. **Validación mediante fórmulas y reglas aplicables.**
   - `action_validate()` blinda: estado, espesor nominal, subproducto, tipo de cambio, vínculo de OC. **CODE** (`madenat_guia_processing.py:1473-1546`)
   - **Blindaje de OC también aplica en Producto (Intake):** ver `02_CONTINUIDAD` §8 (Fachada de Producto) y `04_DECISION_LOG` AD-52. La asociación manual de OC en la fachada valida en servidor `supplier_id` obligatorio, `commercial_partner_id`, compañía, estado de OC y estado de recepción, sin sobrescribir silenciosamente `purchase_id`. **AD-52** (`madenat.lumber.intake.po.link.action_confirm_link`)
   - **Blindaje de OC en Procesados — RESUELTO COMPLETAMENTE por AD-54 (ampliado 2026-08-19):** los bloqueos previos de `madenat.guia.processing` (que lanzaban `UserError` con `oc_reference_raw` presente y `order_id` vacío, evidencia `madenat_guia_processing.py:1552-1559` en `action_validate()` y `:1420-1427` en `action_process_from_staging()`) fueron **autorizados como excepción puntual** para convertirse en **advertencia no bloqueante** (`_logger.warning` + `message_post`), homologando la política de Procesados con Producto/Intake (AD-52/AD-54) en **ambas etapas** (staging y validación final). Procesados NO ofrece wizards de vinculación manual de OC ni de corrección de proveedor; la UI ofrece el botón "📄 Crear OC desde PDF" (`action_create_purchase_order_from_document`) que crea una `purchase.order` en `draft`. La exigencia final de OC resuelta pertenece exclusivamente a Costeo/Valorización/cierre financiero para ambos modos de ingesta. La excepción AD-54 es puntual y autorizada explícitamente (ahora sobre dos métodos específicos); la regla general de no modificar `madenat_lumber_core` sigue vigente para cualquier otro caso.
7. **Confirmación y envío a stock.**
   - `action_validate()` → firma snapshot SHA-256 (`Gate3PreCommit.generate_processing_signature`) **antes** del primer write a `stock.lot`, y persiste un evento inmutable en `madenat.audit.log` (`guia_processing_id`, `audit_snapshot`, `audit_hash`, `action_type='validation_signature'`). **CODE** — BT-01 CERRADO.
   - `do_full_processing()` → `_create_or_get_lot()` escribe `stock.lot`; `_create_picking_and_lines()` crea movimientos. **CODE**

> **Nota operativa — "Modificar origen" en Procesados (AD-55):** desde la consola de Intake, el botón "Modificar origen" (`action_open_source`) debe abrir una **fachada ligera de `madenat.guia.processing` definida en `madenat_lumber_intake`**, equivalente al patrón de Producto (`view_lumber_reception_intake_facade_form`), **no la vista estándar del core** (que hoy se usa porque `action_open_source` no asigna `view_id` en el flujo Procesados). Este cambio es exclusivo de Intake (vista XML + selección de `view_id`); el core queda fuera de alcance. Ver `04_DECISION_LOG.md` AD-55.

---

## 5. Reglas de negocio confirmadas

| Regla | Estado | Fuente / evidencia |
|---|---|---|
| Política de precisión volumétrica y dimensional | **CONFIRMADA** (3 decimales) | Correo Mauricio Navarrete 30-10-2025 (`digits=(16, 3)`); código `utils_uom.r3`; `03_TESTS` T28 |
| Lectura general/global de documentos de ingreso (multi-proveedor) | **Definida de negocio, sin implementación** | Mandato/hallazgo de auditoría; sin doc previa ni código (grep vacío) |
| Producto enviado a proceso se da de baja con histórico (documento, fecha, motivo, movimiento) | **Implementada para `service` (BT-04 CERRADO 2026-08-16)** | Salida controlada a `Virtual Locations/Production` (`_get_or_create_consumption_picking`), idempotente y reversible; evidencia `consumption` en `madenat.audit.log` |
| Lote histórico de producto no se reutiliza/renombra/sobrescribe desde Procesados | **Implementada (BT-02 CERRADO 2026-08-16)** | `_create_or_get_lot()` excluye lotes con `reception_id` de la búsqueda y del fallback posterior a `IntegrityError` (`('reception_id', '=', False)`) |
| Procesado ingresa como entidad independiente | **Configurado** | `_create_or_get_lot()` genera lote con nombre propio (lot_name + sku + guia_suffix) |
| No crear vínculo artificial lote origen → lote procesado salvo evidencia explícita | **Vínculo ya existente (excepción aplica)** | `stock.lot.parent_lot_id` + `child_lot_ids` + `generation_level` (stock_lot.py:301-311, 984) |
| Trazabilidad por documentos, guías, movimientos, fechas y motivos | **Parcial** | `reception_id`/`guia_processing_id` discriminadores + `parent_lot_id` + `consumption_picking_id`; motivo explícito de baja aún ausente |

---

## 6. Controles obligatorios ANTES de creación de stock

| Control | Producto | Procesados | Fuente |
|---|---|---|---|
| Gate 0 (validación de archivo) | ✅ | ⚠️ parcial (parseo disperso) | `ingestion_gate.py` |
| Staging sin stock | ✅ `lumber.reception.line` | ✅ `madenat.guia.processing.line` | CODE |
| Gate 1 (reconciliación) | ✅ | ⚠️ no formalizado como gate | `ingestion_gate.py` |
| Gate 2 (análisis comercial) | ✅ | ⚠️ blindajes inline en `action_validate` | CODE |
| GB-1 (staging completo) | ✅ | ✅ (exige processing_line_ids + blindajes) | CODE |
| Firma previa a stock (`audit_snapshot` + `audit_hash`) | ✅ Gate 3 | ✅ `generate_processing_signature` en `action_validate` | `ingestion_gate.py` / BT-01 CERRADO |

---

## 7. Trazabilidad documental e histórica

- **Discriminadores de origen** (mutuamente excluyentes): `reception_id` ↔ `guia_processing_id`; `reception_type` = `raw`/`processed`. **CODE + CANON** (`12` §2).
- **Notarización criptográfica**: flujo Producto (`audit_snapshot`/`audit_hash` por Gate 3) y flujo Procesados (`audit_snapshot`/`audit_hash` en `madenat.audit.log` vía `action_validate`). BT-01 CERRADO.
- **Genealogía**: `parent_lot_id`/`child_lot_ids`/`generation_level` permiten rastrear Lote Original → Procesado. **CODE** (`stock_lot.py:301, 984`) — evidencia de vínculo ya existente.
- **Bitácora**: `madenat.audit.log` tiene `reception_id` (flujo Producto, ondelete cascade) y `guia_processing_id` (flujo Procesados). Cubre firma de validación (`validation_signature`, BT-01) y eventos operativos (`lot_creation`, `lot_update`, `omission`, BT-03; `consumption`, BT-04).
- **Baja por envío a proceso**: implementada solo para guías `service` (salida controlada a `Virtual Locations/Production`, idempotente y reversible). BT-04 CERRADO.

---

## 8. Matriz de estado

| Tema | Estado |
|---|---|
| Flujo ingesta Producto (7 pasos) | Confirmado en código |
| Flujo ingesta Procesados (7 pasos) | Confirmado en código |
| Política de decimales (3 decimales) | Confirmado documentalmente y consistente con código |
| Parser global multi-proveedor | Definido de negocio, sin implementación (brecha) |
| Baja de producto enviado a proceso | Implementado para `service` (salida a Production) — BT-04 CERRADO; mermas reales (yield) sin modelar |
| Lote histórico no reutilizable por Procesados | Implementado en código (BT-02 CERRADO 2026-08-16) |
| Ingreso de procesado como entidad independiente | Confirmado en código |
| Vínculo de genealogía (parent_lot_id) | Confirmado en código (excepción a "no vínculo artificial") |
| Notarización (firma previa a stock) | Producto (Gate 3) y Procesados (`action_validate`) — BT-01 CERRADO |
| Ciclo logístico (stock / baja / exportación / contenedor) | Parcial (baja `service` implementada; mermas reales sin modelar) |

---

## 9. Brechas técnicas verificables

- ~~**BT-01 — Segundo write path sin Gate 3.**~~ **CERRADO (2026-08-16).** `action_validate()` firma un snapshot determinista de guía (SHA-256) antes del primer write a `stock.lot` y persiste la evidencia en `madenat.audit.log` (`guia_processing_id`, `audit_snapshot`, `audit_hash`). Revalidación genera evento nuevo; cancelar/reabrir no borra eventos previos. Ver CHANGELOG 18.0.5.10.0.
- ~~**BT-02 — Sobrescritura de lote notarizado.**~~ **CERRADO (2026-08-16).** `_create_or_get_lot()` excluye lotes con `reception_id` en la búsqueda inicial y en el fallback posterior a `IntegrityError` (`('reception_id', '=', False)`). Un lote originado en recepción no puede reutilizarse ni sobrescribirse desde guía processing aunque coincidan nombre, producto y compañía. Cobertura en `TestCreateOrGetLotReceptionProtection`; suite `madenat_lumber_core`, 46 tests, 0 fallos, 0 errores.
- ~~**BT-03 — Bitácora operativa sin cobertura de Procesados.**~~ **CERRADO (2026-08-16).** `_create_or_get_lot()` emite `lot_creation`/`lot_update` y `_validar_y_enriquecer_lineas()` emite `omission`, todos enlazados a `guia_processing_id`. Un único evento por outcome confirmado. La baja formal de lotes/etiquetas sigue fuera de alcance (pendiente de módulo futuro). Ver CHANGELOG 18.0.5.10.0.
- ~~**BT-04 — Baja de producto a proceso sin implementación.**~~ **CERRADO (2026-08-16).** Guías `service` generan exactamente una salida de stock hacia `Virtual Locations/Production` (`_get_or_create_consumption_picking`, idempotente vía `consumption_picking_id`), reversible sin borrar historia (`_reverse_consumption_picking`) y con evidencia `consumption` en `madenat.audit.log`. `compra` queda intacto. Ver CHANGELOG 18.0.5.11.0. (Las mermas reales del proceso — yield — siguen sin modelar como scrap: deuda separada).
- **BT-05 — Parseo disperso de guía procesada.** `madenat_guia_processing.py` concentra parseo sin dispatcher equivalente a `reception_parser`. **CODE + CANON** (`00` §3.3).

---

## 10. Pendientes de UAT / evidencia

- UAT-01: PASO 2 end-to-end (recepción f5085/f1550 + guía processing con fracciones) — pendiente de operador (Mauricio/Cristhian). **CANON** (`02`)
- UAT-02: TS29–TS32 (conversión largo ft/mm/m + quick-create subproducto) — tests existentes, pendiente evidencia staging. **CANON** (`03` §3)
- UAT-03: Validación UAT de precisión de cálculo/volumen y costo unitario con datos reales (3 decimales) — pendiente; no es decisión de negocio.
- UAT-04: `deduction_factor = 0.0625` (Blank) — pendiente de confirmación de negocio (Cristhian). **CANON** (`02` §4)
- ~~UAT-05: Evidencia de que un lote `raw` no se reasigna a procesado (cierre de BT-02)~~ → **CERRADO (2026-08-16)** por test `test_reception_lot_never_reused` en `TestCreateOrGetLotReceptionProtection`.

---

## 11. Historial de decisiones reemplazadas o evolucionadas

- **DEC-002 — «No Modelar Procesamiento Físico de Madera» (2026-04-15):** **SUPERADA/EVOLUCIONADA.** La decisión original (no `mrp`, flujo lineal sin transformación) coexistió con la posterior aparición del flujo de **Procesados** (`madenat.guia.processing`, `tipo_recepcion='service'`), el módulo `madenat_toll_processing` y la genealogía `parent_lot_id`. La decisión original se mantiene como antecedente; el alcance actual exige distinguir **maquila/servicio externo** (soportado) de **manufactura interna MRP** (no instalado). Fuente: `WIKI/04_DECISIONES/DEC-002`, `madenat_guia_processing.py`, `stock_lot.py`.
- **TD-004/TD-005 (centralización de constantes):** vigentes y confirmadas en `utils_uom.py`; no reemplazadas. **WIKI** (`02_TECNICO/arquitectura_ingesta_recepciones.md`).

---

## Parte B — Matriz de trazabilidad de hallazgos

| ID | Tema | Regla/Hallazgo | Fuente documental | Evidencia código | Estado | Acción requerida |
|---|---|---|---|---|---|---|
| H-01 | Decimales | Política vigente = 3 decimales en campos volumétricos y dimensionales | Correo Mauricio Navarrete, 30-10-2025 | `digits=(16, 3)`, `utils_uom.r3`, `03_TESTS` T28 y WIKI usan 3 decimales | Confirmado documentalmente y consistente con código | Validar mediante UAT con datos reales |
| H-02 | Parser global | Lectura general/global multi-proveedor como estrategia (no solo normalización por proveedor) | Mandato | Sin doc ni código (grep vacío); antecedente = `reception_parser` por perfil + `lumber_ingestion_format` (4 formatos) | Definido de negocio, sin implementación | Formalizar como requisito; no diseñar sin baseline |
| H-03 | Flujo Producto | 7 pasos: carga→lectura→staging→nominales→validación visual→fórmulas→stock | `00`, `12` §4 | `reception_parser`, `ingestion_gate`, `reception_service` | Confirmado en código | Mantener |
| H-04 | Flujo Procesados | 7 pasos comparables, separado de Producto | `12` §3, `00` §4.3 | `do_full_processing`, `action_validate`, `_create_or_get_lot` | Confirmado en código | Mantener |
| H-05 | Baja al proceso | Producto enviado a proceso se da de baja con historial | Mandato | `_get_or_create_consumption_picking` (salida a Production, solo `service`) | Implementado (BT-04 CERRADO 2026-08-16); mermas reales sin scrap | Modelar merma/yield como scrap (deuda separada) |
| H-06 | Lote no reutilizable | Lote histórico de producto no se renombra/reescribe desde Procesados | Mandato | `_create_or_get_lot` excluye `reception_id` (L3245, L3390) | Implementado en código | ~~Cerrar BT-02~~ → CERRADO (2026-08-16) |
| H-07 | Trazabilidad sin vínculo artificial | Evitar campo directo origen→procesado salvo evidencia | Mandato | `parent_lot_id` ya existe (genealogía) | Confirmado en código (excepción aplica) | Mantener; no duplicar |
| H-08 | Ciclo logístico | Permanencia o salida (exportación/contenedor/baja) coherente | `12`, WIKI | `lumber.container`, `lumber_export_shipment`; baja `service` implementada | Parcial (mermas reales sin scrap) | Modelar merma/yield como scrap |
| H-09 | Gate 3 | Único write path (Producto) | `00` §5, AD-04 | `action_confirm_reception` → Gate3 | Confirmado (Producto) | Aclarar excepción Procesados |
| H-10 | Nominales | Asignación previa a stock en ambos flujos | `00`, `12` | `_apply_thickness_visual`, `action_assign_commercial_defaults` | Confirmado en código | Mantener |

---

## Parte C — Registro de contradicciones y vacíos

### C-01 — Política de decimales — RESUELTA DOCUMENTALMENTE (2026-08-15)
- **Resolución:** La política vigente es **3 decimales** para campos volumétricos y dimensionales, conforme a `digits=(16, 3)`.
- **Evidencia primaria:** Correo de Mauricio Navarrete, 30-10-2025, asunto "Actualización de Avance Módulos MADENAT y Plan preparación para UAT": *"Todos los campos de volumen y dimensionales se ejecutaron pero no se muestran en las vistas ya que respetan (digits=(16, 3))."*
- **Consistencia con código:** utilidades `r3` (`utils_uom.py:441`) y documentación `03_TESTS` T28 ("precisión 3 decimales"), WIKI "%.3f".
- **Antecedente:** la afirmación previa de "2 decimales" se conserva como error de interpretación de la auditoría/consolidación anterior, no como política vigente. Sin brecha de definición.

### C-02 — DEC-002 vs flujo de Procesados
- **Qué se contradice:** DEC-002 (2026-04-15) declara "no modelar procesamiento físico, no `mrp`"; el ecosistema actual incorpora `madenat.guia.processing` (procesados), `madenat_toll_processing` y `parent_lot_id`.
- **Documentos involucrados:** `WIKI/04_DECISIONES/DEC-002_sin_procesamiento_fisico.md`, `CANON/12_FLUJOS_INGESTA.md`, `CANON/00_ARQUITECTURA.md`.
- **Riesgo de no resolver:** lectura errónea del alcance (creer que "no hay procesados" cuando sí los hay).
- **Responsable sugerido:** Arquitecto.
- **Acción mínima:** marcar DEC-002 como superada (ya registrado en §11).

### C-03 — Estrategia de parser global (vacío de implementación)
- **Qué falta:** no existe requisito formalizado ni código de "lectura general/global multi-proveedor".
- **Documentos involucrados:** ninguno (grep vacío); antecedente técnico `reception_parser.py` + `lumber_ingestion_format`.
- **Riesgo de no resolver:** depender de normalización proveedor por proveedor sin estrategia global.
- **Responsable sugerido:** Arquitecto/Tech Lead.
- **Acción mínima:** formalizar la estrategia como decisión de negocio (registrar en AD), sin diseñar implementación todavía.

### C-04 — Baja de producto a proceso — CERRADA (2026-08-16)
- **Resolución:** se implementó salida controlada a `Virtual Locations/Production` solo para guías `service` (`_get_or_create_consumption_picking`), con idempotencia (`consumption_picking_id`) y reversión sin borrar historia (`_reverse_consumption_picking`). No se usa `stock.scrap`. El material que se destruye realmente (merma/yield) aún no se modela como scrap — deuda separada.
- **Documentos involucrados:** `04_DECISION_LOG.md` (AD-49), CHANGELOG 18.0.5.11.0, `madenat_guia_processing.py`.
- **Cobertura:** `TestGuiaProcessingConsumptionBT04` (5 casos).

### C-05 — Sobrescritura de lote notarizado (BT-02) — CERRADA (2026-08-16)
- **Resolución:** `_create_or_get_lot()` aplica exclusión dura: las búsquedas inicial y de fallback posterior a `IntegrityError` incluyen `('reception_id', '=', False)`, de modo que un lote originado en recepción no puede reutilizarse ni sobrescribirse desde guía processing.
- **Documentos involucrados:** `00_ARQUITECTURA` §5 (AD-04), `_create_or_get_lot` (L3245, L3390), CHANGELOG 18.0.5.10.0.
- **Cobertura:** `test_reception_lot_never_reused` (protección) + `test_lot_without_reception_reused` (idempotencia de lote sin recepción). Suite `madenat_lumber_core`, 46 tests, 0 fallos, 0 errores.

---

## Resumen de consolidación

- **Documentos revisados:** 8 CANON, 18 WIKI/02_TECNICO, 1 WIKI/04_DECISIONES, código core (reception_parser, reception_service, madenat_guia_processing, stock_lot, utils_uom, ingestion_gate).
- **Documento creado:** `CANON/13_CONSOLIDACION_OPERATIVA.md` (este archivo).
- **Reglas consolidadas:** flujo Producto (7 pasos), flujo Procesados (7 pasos), controles pre-stock, discriminadores de origen, genealogía `parent_lot_id`.
- **Contradicciones detectadas:** C-02 (DEC-002 superada). C-01 (decimales 2 vs 3) fue **resuelta documentalmente** (evidencia 30-10-2025: 3 decimales).
- **Brechas técnicas abiertas:** ~~BT-01 (segundo write path sin Gate 3)~~ **CERRADO (2026-08-16)**, ~~BT-02 (sobrescritura de lote notarizado)~~ **CERRADO (2026-08-16)**, ~~BT-03 (bitácora operativa sin Procesados)~~ **CERRADO (2026-08-16)**, ~~BT-04 (baja sin implementación)~~ **CERRADO (2026-08-16)**, BT-05 (parseo disperso).
- **Pendientes de UAT/evidencia:** PASO 2 end-to-end, T29–T32, validación UAT de precisión (3 decimales), `deduction_factor`. ~~cierre de BT-02~~ (cerrado por test automatizado).
