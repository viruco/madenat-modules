# MADENAT — Matriz de Evidencia y Validación

**Versión documental:** 6.9.0
**Fecha de actualización:** 2026-09-28  <!-- actualizado: 2026-09-28 — Fase 2 (AD-80): cobertura de volumen oficial, bloque SV, reversa UI y ciclo de vida de guías (§10) -->
**Estado:** ACTIVO — Matriz canónica de validación operativa.

---

## 1. Propósito

Este documento es exclusivamente una matriz de evidencia, validación y criterios de aceptación. No dicta reglas de diseño ni estado vivo del proyecto. Sirve como repositorio de los casos de prueba operativos y de saneamiento.

---

## 2. Base Consolidada (T01 – T28)

*(Nota: La ejecución de las pruebas T01 a T28 ya ha sido validada exhaustivamente. Su estado "CERRADO" constituye evidencia histórica integral de la base operativa).*

### 2.1 Pruebas Operativas Core
| ID | Caso | Entrada | Esperado | Estado Documental |
|---|---|---|---|---|
| T01 | Suma m3 por línea | Packing estándar | Suma líneas = total recepción | CERRADO (Histórico) |
| T02 | Suma MBF por línea | Packing estándar | MBF consistente | CERRADO (Histórico) |
| T03 | Triple capa | Blanks | Visual, física y nominal correctas | CERRADO (Histórico) |
| T04 | Regla `metric` | Línea nacional | `vol_shipment_m3 = vol_physical_m3` | CERRADO (Histórico) |
| T05 | Regla `f1550` | Línea S2S | cálculo exacto con factor oficial | CERRADO (Histórico) |
| T06 | Regla `f5085` | Línea Blanks | cálculo exacto con factor oficial | CERRADO (Histórico) |
| T07 | Gate 2 nominal null | Staging incompleto | bloquea confirmación | CERRADO (Histórico) |
| T08 | Gate 2 producto inválido | producto inactivo | bloquea confirmación | CERRADO (Histórico) |
| T09 | Gate 2 volumen fuera tolerancia | diferencia excesiva | bloquea confirmación | CERRADO (Histórico) |
| T10 | Gate 3 commit | staging válido | crea stock y picking | CERRADO (Histórico) |
| T11 | Recall de lote | recepción cerrada | trazabilidad por lote/paquete | CERRADO (Histórico) |
| T12 | Conciliación comercial-bodega | recepción cerrada | lotes = líneas aprobadas | CERRADO (Histórico) |
| T13 | Standard + Blanks | recepción mixta | sin contaminación entre reglas | CERRADO (Histórico) |
| T14 | Edge cases volumen nulo | dimensiones inválidas | bloqueo | CERRADO (Histórico) |

### 2.2 Saneamiento Estructural
| ID | Caso | Objetivo | Estado Documental |
|---|---|---|---|
| T15 | Campos duplicados eliminados | evitar shadowing | CERRADO (Histórico) |
| T16 | `@api.depends` consolidados | eliminar duplicidad | CERRADO (Histórico) |
| T17 | Importaciones reparadas | estabilidad de parser | CERRADO (Histórico) |
| T18 | Variables indefinidas corregidas | flujo robusto | CERRADO (Histórico) |
| T19 | Métodos incompletos completados | base operativa | CERRADO (Histórico) |
| T20 | `WidthMappingTable` funcional | mapeo anchos | CERRADO (Histórico) |
| T21 | `LumberReceptionService` operativo | persistencia desacoplada | CERRADO (Histórico) |
| T22 | Validaciones de rango | calidad de datos | CERRADO (Histórico) |
| T23 | Validaciones de dimensiones | blindaje físico | CERRADO (Histórico) |
| T24 | Pruebas unitarias extendidas | cobertura adicional | CERRADO (Histórico) |
| T25 | Tests Docker | instalación controlada | CERRADO (Histórico) |
| T26 | Staging → stock.lot | persistencia real | CERRADO (Histórico) |
| T27 | Validaciones en create/write | integridad | CERRADO (Histórico) |
| T28 | Cálculos blindados | precisión 3 decimales | CERRADO (Histórico) |

---

## 3. Matriz de Validación Activa (T29 – T32)

Estos casos definen la validación funcional del ingreso de largo con unidad seleccionable. Existen tests automatizados en `test_length_uom_and_subproducto.py`. Pendiente ejecución formal con evidencia en ambiente staging.

| ID | Caso | Entrada | Esperado | Estado Documental | Test automatizado |
|---|---|---|---|---|---|
| T29 | Conversión ft → m | `lengthinputraw` en pies | `length` normalizado a metros | PENDIENTE (Evidencia registrada, test `test_29_length_ft_to_m`) | ✅ |
| T30 | Conversión mm → m | `lengthinputraw` en mm | `length` normalizado a metros | PENDIENTE (test `test_30_length_mm_to_m`) | ✅ |
| T31 | Conversión m → m | `lengthinputraw` en m | `length` sin alteración | PENDIENTE (test `test_31_length_m_default_unchanged`) | ✅ |
| T32 | Quick-create subproducto | wizard mass update | alta rápida funcional | PENDIENTE (test `test_32_quickcreate_subproducto_desde_wizard`) | ✅ |

<!-- actualizado: 2026-06-16 — agregada columna de test automatizado -->

---

## 4. Evidencia — Fix de Blanks (2026-06-02)

### Caso: T33 — Fix de ajuste S2S indebido en blanks
- **Fecha:** 2026-06-02
- **Alcance:** `stock_lot.py`, `madenat_guia_processing.py`
- **Problema corregido:** El ajuste volumétrico S2S (cepillado) se aplicaba indebidamente a líneas de blanks clear, distorsionando el cálculo de volumen de embarque.
- **Solución:** Separación de rutas de cálculo (no son equivalentes):
  1. **`stock_lot._compute_vol_shipment_m3`** (post-Gate3): el lote con `largo_ft_frac` usa `(espesor_in × ancho_in × largo_ft × piezas) / 5085.312`, **sin** deducción de cara ni +1/8".
  2. **`lumber_reception._compute_export_values`** (staging / M3 comercial): la rama `blank_clear` usa `(espesor_in − 0.0625) × (ancho_in + 0.125) × largo_ft × piezas / 5085.312`, **con** deducción de cara (`FACE_DEDUCTION_INCH`) e incremento de ancho (`S2S_WIDTH_ADJUSTMENT_INCH`).
  - La evidencia Excel (tarjas MSC VIRGO, 2026-08-15) respalda la ruta **(2)**: los casos `1.5625"×2.625"×16ft×416 = 5.399` y `1.5625"×3.625"×16ft×286 = 5.062` solo se reproducen aplicando −1/16" al espesor y +1/8" al ancho.
- **Validación local:** Módulo actualiza sin error de registry. Cálculo volumétrico verificado en recepción con blanks.
- **Estado:** CERRADO (Evidencia local) — la afirmación previa "sin aplicar deducciones de cepillado" era válida únicamente para la ruta `stock_lot.py`, no para `lumber_reception.py`.

---

## 5. Caso Base Recomendado para Evidencia

Para ejecutar validaciones integrales, se recomienda utilizar la siguiente casuística documentada:
- **Guía:** `40597`
- **OC:** `MC2603-306`
- **Volumen PDF:** `55.665 m³`
- **Volumen Excel:** `55.821 m³`

---

## 6. Plantilla de Ejecución de Pruebas

Toda ejecución debe documentarse bajo este formato antes de cambiar el estado a "CERRADO":

```md
### Caso: TXX
- Fecha:
- Operador:
- Ambiente:
- Base de datos:
- Rama / commit:
- Input:
- Esperado:
- Real:
- Logs:
- Evidencia:
- Estado:
- Hallazgos:
```

---

## 7. Nuevas suites de test (post 2026-06-02)  <!-- actualizado: 2026-06-16 -->

Estas suites existen en código pero no tienen trazabilidad en la matriz documental T01–T33. Se registran aquí como inventario para futura integración formal.

### madenat_lumber_core
| Archivo | Clase | # Tests | Cobertura |
|---|---|---|---|
| `tests/test_lot_costing.py` | TestLotCosting | 6 | C1.1–C1.6: wood_cost, no doble conteo, margin, deprecación, cost_per_m3, cost_per_mbf |
| `tests/test_ingestion_gate.py` | TestGate0PreUpload | 5 | Gate 0: excel, pdf, extensión, vacío, tamaño |
| `tests/test_ingestion_gate.py` | TestGate1DocumentReconciliation | 10 | Gate 1: reconciliación, mismatch, duplicado, TC, volumen, OC |
| `tests/test_duplicate_validation.py` | TestDuplicateValidation | 8 | Duplicados PDF, guia_processing, staging, mensajes error |
| `tests/test_guia_processing.py` | TestMadenatGuiaProcessing | 13 | Creación, state machine, cancel, unlink, volúmenes, TD-007 duplicados |
| `tests/test_guia_processing.py` | TestCreateOrGetLotReceptionProtection | 2 | BT-02: protección de lote con `reception_id` + reutilización legítima de lote sin recepción |
| `tests/test_guia_processing.py` | TestGuiaProcessingValidationSignature | 4 | BT-01: firma SHA-256, persistencia del evento, bloqueo sin evento, supervivencia ante cancelación |
| `tests/test_guia_processing.py` | TestGuiaProcessingOperationalAudit | 4 | BT-03: lot_creation, lot_update, omission, coexistencia con validation_signature |
| `tests/test_guia_processing.py` | TestGuiaProcessingConsumptionBT04 | 5 | BT-04: salida única a proceso (service), revalidación sin duplicar, compra sin salida, reversión sin borrar historia, bloqueo sin lote |
| `tests/test_guia_processing.py` | TestMadenatGuiaProcessingLine | 2 | staging, vol_purchase |
| `tests/test_lumber_reception.py` | TestLumberReception | 14 | T01–T14: suma m3, mbf, triple capa, dedup, volúmenes, width map, gate 3, trazabilidad, edge cases |
| `tests/test_length_uom_and_subproducto.py` | TestLengthUomAndSubproducto | 4 | T29–T32: ft, mm, m, quick-create subproducto |

### madenat_lumber_costing
| Archivo | Clase | # Tests | Cobertura |
|---|---|---|---|
| `tests/test_cost_distribution.py` | TestCostDistribution | 5 | C2.1–C2.5: apply, account_id, total, landed_cost, reverse |
| `tests/test_landed_cost_integration.py` | TestLandedCostIntegration | 5 | C3.1–C3.5: picking, sin picking, account_id, reverse, doble apply |
| `tests/test_module_compatibility.py` | TestModuleCompatibility | 6 | C4.1–C4.6: billing, logistics, herencia, Monetary, purchase_cost, account_id |

### madenat_lumber_billing
| Archivo | Clase | # Tests | Cobertura |
|---|---|---|---|
| `tests/test_billing_consolidation.py` | TestBillingConsolidation | 3 | Flujo auditoría, no duplicar, server action rechaza |

**Total aprox.:** ~70 tests automatizados distribuidos en 9 archivos de test.
**Estado documental:** Inventariados. Pendiente integración formal en matriz T01–T33 con numeración T34 en adelante.

---

## 8. Criterios Globales de Aprobación Documental  <!-- renumerado por inserción de sección 7 -->

Un caso de prueba se considera formalmente aprobado y puede transicionar a estado CERRADO únicamente si cumple las siguientes condiciones de validación:
1. Existe una correlación demostrable entre el Input y el Resultado Real (Evidencia).
2. Los resultados matemáticos son reproducibles sin inconsistencias.
3. Se ha adjuntado la plantilla de ejecución completa con logs o capturas (Trazabilidad).
4. El resultado real coincide 100% con el escenario Esperado.

---

## 9. Diccionario de Fallos Comunes  <!-- renumerado -->

Para asistir en la validación y debugging:
| Si falla | Revisar |
|---|---|
| T01 / T02 | parser, unidades, sumatorias |
| T03 | staging y triple capa |
| T04 / T05 / T06 | reglas de exportación |
| T07 / T08 / T09 | Gate 2 y catálogo |
| T10 | Gate 3 y servicio stock |
| T11 / T12 | trazabilidad |
| T13 | dispatcher multi-formato |
| T14 | validaciones de edge |
| T29 / T30 / T31 | lógica de conversión y normalización de cálculos |
| T32 | wizard, domain y quick-create |
| T33 | `stock_lot.py`, `madenat_guia_processing.py`, condicional S2S vs blanks |

---

## Casos que requieren evidencia adicional

### Caso: T29
- Fecha: 2026-05-23
- Operador: Gemini Code Assist / Auditoría Técnica
- Ambiente: Docker odoo18_app
- Base de datos: madenattest
- Rama / commit: main / head
- Input: `lengthinputraw` = 12.0, `lengthuom` = 'ft'
- Esperado: `length` = 3.6576 (normalizado a 3.658 m)
- Real: `length` = 3.658
- Logs:
  `DEBUG: madenat.lumber.reception.line: _compute_lengthm triggered for line_id: 104`
  `DEBUG: values: input=12.0, uom=ft -> result=3.6576 -> stored=3.658`
- Evidencia: Registro verificado en tabla `lumber_reception_line` tras trigger de compute.
- Estado: PENDIENTE (Evidencia registrada)
- Hallazgos: El sistema aplica correctamente el factor 0.3048 y respeta la precisión de 3 decimales definida en T28.

---

## 5. Cobertura nueva — Cierre técnico 2026-08-20 (`1466f24`)

Commit `1466f24 fix(core): restore ingestion profile safeguards and blanks catalog` añade cobertura automatizada en `madenat_lumber_core/tests/test_guia_processing.py`:

| Clase | Cobertura | Tests |
|---|---|---|
| `TestGuiaProcessingIngestionProfileLock` | Candado de Procesados reactivado (`ingestion_profile` en `madenat.guia.processing`): existencia/default `f5085`, values coinciden con `lumber.reception`, bloqueo S2S en f5085, permiso en f1550, permiso en metric | 5 |
| `TestBlankProfileCatalogComplete` | Catálogo `blanks` aceptado en los 4 modelos hermanos, `_resolve_for_profile('blanks')` **no** resuelve `metric` sino S2S/imperial (decisión intencional), legacy de subproducto no vacío | 6 |

Suite `madenat` (Core + Intake) ejecutada sobre `madenat_test`: **49/49 tests, 0 fallos, 0 errores**. Esta cobertura automatizada complementa (no sustituye) las pruebas UAT end-to-end pendientes de `CANON/13`.

<!-- actualizado: 2026-08-20 — nota de cobertura automatizada para el candado de Procesados y catálogo 'blanks' (commit 1466f24) -->

---

## 6. Cobertura — Contrato Producto/Subproducto (Fase 2)

| Archivo | Clase | Cobertura | Tests |
|---|---|---|---|
| `madenat_lumber_core/tests/test_product_default.py` | `TestMadenatLumberProductDefault` | Resolución de producto maestro por tipo, perfil y compañía; `UserError` sin configuración; rechazo de reglas activas ambiguas | 5 |
| `madenat_lumber_core/tests/test_subproducto_contract.py` | `TestSubproductoContract` | Autocreación de subproducto desde Excel, reutilización sin duplicar, texto vacío, mapeo Bruta (`_fill_staging_table`) y Procesado (`action_verify_data`) | 6 |

**Validación de volumen (Intake):** `packing_volume_total` (Σ `vol_shipment_m3`) y `stock_volume_total` (Σ `vol_purchase_m3`) se presentan con 3 decimales; no se muestran totales numéricos sin etiqueta.

**Fallos ajenos:** los fallos existentes de `madenat_lumber_billing` (`TestBillingConsolidation.test_02_no_duplicar_consolidacion`) y `madenat_lumber_costing` (errores en `setUpClass`) son preexistentes y **no** autorizan modificar esos módulos dentro de este cierre.

<!-- actualizado: 2026-08-31 — cobertura Fase 2 contrato producto/subproducto y validación de volumen -->

---

## 7. Cobertura — Ingreso por Volúmenes y asignación manual de proveedor (2026-09-22)

| Archivo | Cobertura |
|---|---|
| `madenat_ingestion_engine/tests/test_pdf_parties.py` | Extracción de partes del PDF: emisor/receptor, asociación RUT-nombre por cercanía, confianza (`high/medium/low/none`), exclusión de transportista, membrete (8 tests). |
| `madenat_lumber_intake/tests/test_volume_extraction.py` | Volumen PDF, detalle documental, persistencia de proveedor, resolución por RUT, ambigüedad, confianza baja, no bloqueo, consola y asignación manual de proveedor. |

**Resultados de jornada (2026-09-22):**
- `madenat_lumber_intake`: **141 tests, 0 fallos, 0 errores** (incluye `test_action_assign_supplier_abre_wizard` y `test_asignar_proveedor_persiste_estado_y_chatter`).
- `madenat_ingestion_engine`: **55 tests, 0 fallos** (incluye `test_pdf_parties`).
- `madenat_lumber_core`: ejecución por tags devolvió **0 tests** por descubrimiento del entorno; debe reejecutarse por ruta/clase antes de afirmar cobertura total.

**Pendiente de validación:** Excel sin PDF como fuente única; rebaja/registro físico de stock por Volúmenes.

<!-- actualizado: 2026-09-22 — cobertura Ingreso por Volúmenes y asignación manual de proveedor -->

---

## 8. Cobertura — Programación 1: identificación operativa en R1 (2026-09-25)

### 8.1 Evidencia de despliegue y estructura

| Verificación | Resultado | Naturaleza |
|---|---|---|
| Upgrade de `madenat_lumber_reports` a `18.0.2.3.0` sobre `madenat_test` (solo ese módulo) | Código de salida `0`; módulo cargado y vistas parseadas | Ejecutado |
| Cinco columnas instaladas en `stock_quant`: `lot_operational_label`, `is_volume_lot`, `lot_entry_datetime`, `lot_entry_datetime_source`, `lot_origin_document` | Existen | Verificado por consulta de solo lectura |
| Lote histórico `stock.lot(3753)` | Técnico `GRANEL 4495589`; operativo `Lote Volumen 4495589`; `is_volume_lot = true`; saldo `0,000` | Verificado por consulta de solo lectura |

### 8.2 Matriz de la regla de token técnico (`GRANEL`)

| Nombre técnico | Es Lote Volumen | Etiqueta esperada |
|---|---:|---|
| `GRANEL 4495589` | Sí | `Lote Volumen 4495589` |
| `GRANEL` | Sí | `Lote Volumen` |
| `  GRANEL  4495589  ` | Sí | `Lote Volumen 4495589` |
| `GRANELITO 123` | No | Sin cambio |
| `MAD-001 GRANEL` | No | Sin cambio |
| `granel 4495589` | No | Sin cambio |

### 8.3 Naturaleza y límites de la evidencia
- Las pruebas de la regla de token fueron **estáticas/aisladas** (ejecución de la lógica del helper
  extraída del propio archivo, con aserciones de ida y vuelta).
- La evidencia de datos fue por **consulta de solo lectura** (estructura de `stock_quant` y caso
  histórico 3753); no se creó ni modificó stock.
- **No existe prueba automatizada** dentro de `madenat_lumber_reports/tests/` para el token técnico,
  la etiqueta operativa ni `is_volume_lot`: queda pendiente.
- **La prueba visual de R1 queda pendiente** por ausencia de lote volumétrico con saldo positivo en
  ubicación interna. Esta matriz **no** declara validada visualmente la vista R1.

<!-- actualizado: 2026-09-25 — Programación 1: cobertura de identificación operativa de lotes en R1 (§8) -->

---

## 9. Cobertura — Gestión Operativa de Etiquetas SV (2026-09-26)

### 9.1 Base de validación

- **Base objetivo:** `madenat_test`.
- **Comando:** `odoo -d madenat_test --test-enable --test-tags 'sv' --stop-after-init`.
- **Resultado:** **56 pruebas, 0 fallas, 0 errores.**
- Módulos cubiertos: `madenat_lumber_core` (6 clases) y `madenat_lumber_logistics` (1 clase).

### 9.2 Matriz de cobertura (clases de la suite `sv`)

| Clase | Casos | Cobertura verificada |
|---|---:|---|
| `TestSvOperationLedger` | 5 | Ledger append-only: evento firmado, inmutabilidad de operación aplicada (sin edición ni borrado), transiciones de estado controladas, motivo obligatorio y exigencia de lote SV, historial múltiple cronológico |
| `TestSvRename` | 6 | Renombre válido que conserva alias y no altera nada más; alias histórico no reutilizable; etiqueta vigente de otro lote no reutilizable; formatos inválidos y motivo obligatorio; escritura directa bloqueada; lote SV con historial no eliminable |
| `TestSvVolumeRegularization` | 6 | Regularización con historial; evidencia y motivo obligatorios; regularización bajo el rebajado bloqueada; volumen no positivo bloqueado; escalamiento a Auditoría solo al alza; sin pickings ni costos creados |
| `TestSvRebaja` | 9 | Rebaja válida (saldo y ledger); rebajas inválidas sin operación; reversa que restaura saldo sin borrar el original; segunda reversa bloqueada; sobreconsumo bloqueado con saldo final correcto; bloqueo transaccional del lote SV; saldo cero permitido sin borrar etiqueta; piezas no habilitadas por paquetes ni placeholder; piezas documentales habilitadas y limitadas |
| `TestSvReversalLotSpecific` | 3 | Cancelación que devuelve solo el lote SV; reversa idempotente sin segunda devolución; sin saldo SV se bloquea con mensaje exacto |
| `TestSvEscalationSecurity` | 5 | Operación rutinaria directa por Operaciones; costo exige Contabilidad; alza de baseline exige Auditoría; Auditoría y Contabilidad por dos personas; bypass ORM/ACL del historial bloqueado |
| `TestSvRpcBypass` | 14 | Escritura directa bloqueada; contexto booleano forjado bloqueado; `operation_id` forjado bloqueado; operación correcta con etiqueta distinta bloqueada; permiso interno consumido y replay bloqueado; asistente que renombra una sola vez sin dejar permiso remanente; infraestructura interna no expuesta; fallo posterior revierte todo y no reutiliza; marca técnica de serialización (escritura directa, contexto forjado, actualización por rebaja/reversa/regularización, replay y no exposición) |
| `TestSvConcurrency` | 2 | **Concurrencia real con dos transacciones independientes** (`db_connect` + conexión propia, no `TestCursor`): saldo 40,315 → A aplica 25,000, B intenta 20,000 → A aplicada, B no aplicada, saldo final 15,315, sin saldo negativo, sin operación/auditoría parcial de B, mensaje funcional aprobado y sin error técnico PostgreSQL expuesto; además verifica que no quedan registros de prueba persistentes |
| `TestSvAllocation` (logística) | 6 | Asignación que crea rebaja vinculada; tope acumulado bloqueado; una etiqueta SV en varios embarques con trazabilidad; un embarque con varias etiquetas SV; liberación que revierte la rebaja; lotes no-SV sin cambios funcionales |

### 9.3 Resultado funcional verificado en la prueba de concurrencia

- Saldo inicial **40,315 m³**; A aplica **25,000 m³**; B (asistente de rebaja, segunda conexión)
  intenta **20,000 m³**.
- Resultado: A aplicada; B no aplicada; saldo final **15,315 m³**; ningún saldo negativo; ninguna
  operación ni auditoría parcial de B; B recibe el mensaje funcional
  «Otro usuario modificó esta etiqueta SV mientras se procesaba la operación. La operación no fue
  aplicada. Actualice la información y vuelva a intentarlo.» y **no** recibe el error técnico de
  serialización de PostgreSQL.
- El intento conflictivo se revierte de forma segura (savepoint) sin reintento automático.

### 9.4 Suite amplia relevante — límite explícito

- Ejecución de la suite relevante (`madenat_lumber_core` + `madenat_lumber_intake` +
  `madenat_lumber_logistics`): **442 pruebas, 6 fallas y 4 errores**.
- Estas incidencias **no** se atribuyen a Gestión Operativa de Etiquetas SV según línea base
  reproducible (base limpia auxiliar `madenat_sv_baseline`: los mismos casos fallan sin datos de
  negocio, y los archivos/ líneas afectados no forman parte del cambio SV; el resto son
  dependientes de datos compartidos de `madenat_test`).
- Se registran como **T1–T6/T7 en `05_BACKLOG.md`**. Esta matriz **no** declara limpia la suite
  amplia.

### 9.5 Validaciones estáticas de la entrega SV

- Compilación Python (`py_compile`) de modelos, wizards y pruebas: OK.
- Validación XML (`xmllint --noout`) de las vistas/wizards/seguridad/data SV: OK.
- `git diff --check` en el repositorio `custom_addons`: OK (sin errores de whitespace).
- Sin `git add`/`commit`; cambios presentes solo en el árbol de trabajo.

### 9.6 Protección de datos históricos

Verificado por consulta de solo lectura al cierre de la corrida: Guía `4495589`
(`madenat.guia.processing` 6566, `write_date` 2026-09-25 18:13:59) y etiqueta `SV00000000008`
(`stock.lot` 3772, `volumen_m3` 40,300, sin marca de serialización, `write_date` 2026-09-26
06:14:57) sin modificación; secuencia `madenat.volume.lot` con `number_next = 1`; ledger SV,
permisos internos y marcadores de prueba en 0 filas.

<!-- actualizado: 2026-09-26 — Gestión Operativa de Etiquetas SV: cobertura de la suite `sv` (§9, AD-79) -->

### 9.7 Cobertura — Cierre de la deuda técnica T1–T6 (2026-09-26)

Base de validación: **`madenat_test`** (base principal, con datos de negocio). Fase de ejecución: **post-install**
(registro completo). Comando: un único proceso Odoo con `--test-enable` y selección por clase.

| Ítem | Clase(s) | Resultado | Causa raíz verificada |
|---|---|---:|---|
| T1 | `TestReceptionSupplierRutExtraction` | 11/11 PASS | El flujo bloqueaba en captura por RUT ausente; ahora difiere la resolución del proveedor y bloquea en `action_confirm_reception` |
| T2 | `TestGranelRouteCore` | 14/14 PASS | Doble causa: gate dimensional aplicado al flujo Volumen (runtime core) y fixture sin volumen oficial documental + aserción sobre `lot_ids` (runtime Intake) |
| T3 | `TestVolumeGuideHeader` | 5/5 PASS | Odoo 18 no expone `Float.digits`; se usa `get_digits(env)` |
| T4 | `TestSupplierResolution` / `TestGuiaProcessingValidationSignature` | 8/8 y 6/6 PASS | VAT/nombre fijos colisionaban con datos reales; el escenario de nominal 0 era rellenado por el hook de Intake al crear la línea |
| T5 | `TestLumberReception` | 21/21 PASS | La clase corría en `at_install` (sin etiquetas de fase) sobre un registro parcial sin el campo `conciliation_status` de Intake ⇒ `NotNullViolation` |
| T6 | `TestShipmentViewModuleIndependence` / `TestShipmentBillingButton` | 3/3 y 3/3 PASS | Referencia cruzada de Logistics al XML ID de Billing; se aporta por vista heredada de Billing |

**Total focalizado: 72 pruebas, 0 fallos, 0 errores.**

Suites amplias de los módulos afectados (`madenat_lumber_core`, `madenat_lumber_intake`,
`madenat_lumber_logistics`, `madenat_lumber_billing`, todas las fases): **457 pruebas, 1 fallo, 0 errores**. El
único fallo es **preexistente y ajeno a T1–T6**: `TestBillingConsolidation.test_02_no_duplicar_consolidacion`
(clase sin etiqueta de fase; el modelo `lumber.billing.consolidation` no implementa guard anti-duplicado).
Registrado como **T9** en `05_BACKLOG.md`; reproducido también en aislamiento
(`--test-tags=/madenat_lumber_billing:TestBillingConsolidation` → 1 fallo de 3).

**Instalación limpia (T6)** — base desechable `madenat_clean_install_test` (creada y eliminada en la misma
sesión; `madenat_test` no se usó para esta verificación):

| Paso | Resultado |
|---|---|
| `-i madenat_lumber_logistics` (sin Billing) | El set mínimo aborta por una referencia **preexistente y distinta** (`contacts.menu_contacts`, T8). Reejecutado con `contacts` instalado explícitamente: Logistics instala y carga sin errores |
| Verificación Logistics-only | `madenat_lumber_billing` sin datos (0 XML IDs), 0 vistas con token de Billing; `get_view` de la vista de Embarque renderiza y valida |
| `-i madenat_lumber_billing` después | Instala y carga sin errores |
| Verificación Billing | Vista heredada presente (`mode=extension`), 1 botón «Crear Consolidación» `type=action`, `invisible="state != 'delivered'"`, `name` ya resuelto al **ID numérico** de la acción y resolviendo exactamente a `madenat_lumber_billing.action_create_consolidation_from_shipment`; acción vinculada al modelo y ejecutable (rechaza embarques no entregados con el mensaje documentado) |

**Contraste histórico preservado:** Guía 4495589 (`madenat.guia.processing` 6566) y etiqueta `SV00000000008`
(`stock.lot` 3772) no fueron leídas ni modificadas en esta sesión; la secuencia `madenat.volume.lot` y el ledger
SV no se tocaron.

---

## 10. Cobertura — Fase 2: volumen oficial, bloque SV y ciclo de vida de guías (2026-09-28, AD-80)

### 10.1 Suite nueva y modificada

| Archivo | Clase | Casos | Cobertura |
|---|---|---|---|
| `madenat_lumber_intake/tests/test_intake_console_sv_actions.py` | `TestIntakeConsoleSvActions` | 7 | Bloque SV con y sin lote; piezas solo documentales (paquetes y líneas PDF no habilitan); delegación de las cuatro acciones en los wizards canónicos; reversa visible solo para rebaja aplicada reversible, vínculo `rebaja_reverse` y segunda reversa bloqueada; proxies read-only no almacenados; arquitectura del bloque (campos y botones) |
| `madenat_lumber_intake/tests/test_volume_ui_hierarchy.py` | `TestVolumeUiHierarchy` | 4 | Volumen oficial único primario y primero en orden documental; etiquetas exactas de secundarios; detalle/diferencia solo en control interno; ausencia del agregado competidor `Volumen:` y ocultamiento de `total_volume_m3` para Volumen |
| `madenat_lumber_intake/tests/test_guide_lifecycle.py` | `TestGuideLifecycle` | 17 | Modo A (draft sin trazas, motivo/confirmación/auditoría, bloqueo por lote, por estado y por evidencia); Modo B (`action_force_cancel` conserva pickings, movimientos, lotes y chatter); Modo C (lote técnico, confirmación escrita `PURGAR`, operaciones en borrador eliminadas, bloqueo por aplicadas/reversadas y rechazadas, y bloqueo por evidencia: adjunto PDF, chatter con contenido y referencia genérica `mail.activity`); Modo D (bloqueadores reales de lote, movimiento, picking, quant y operación SV; contenedor, embarque y consolidación; lista completa de categorías incl. factura, período cerrado y evidencia; cero eliminaciones; snapshot de auditoría con inventario de evidencia); diagnóstico de solo lectura; apertura desde la Consola |
| `madenat_lumber_core/tests/test_sv_reverse_ui.py` | `TestSvReverseUi` | 3 | Botón de reversa con la condición exacta en el ledger; acciones SV en el formulario de la Guía condicionadas a `volume_lot_id`; reversa funcional ligada y segunda reversa bloqueada |
| `madenat_lumber_intake/tests/test_volume_official_volume.py` | `TestVolumeOfficialVolume` | 9 | **Reescrito:** las aserciones que prohibían acciones SV en la Consola se reemplazan por aserciones positivas de los cinco botones autorizados, su ubicación en el bloque SV y la ausencia de botones sin lote |

### 10.2 Resultados de ejecución (2026-09-28, base `madenat_test`)

| Corrida | Alcance | Resultado |
|---|---|---|
| `-u madenat_lumber_intake` con `TestIntakeConsoleSvActions`, `TestVolumeUiHierarchy`, `TestGuideLifecycle`, `TestVolumeOfficialVolume` | Suites de la Fase 2 en Intake | **38 pruebas, 0 fallas, 0 errores** (RC=0) |
| `-u madenat_lumber_core` con `TestSvReverseUi` | Suite nueva de Core | **3 pruebas, 0 fallas, 0 errores** (RC=0) |
| `-u madenat_lumber_intake --test-tags /madenat_lumber_intake` | Regresión completa del módulo | **237 pruebas, 0 fallas, 0 errores** (RC=0) |
| `-u madenat_lumber_core,madenat_lumber_logistics --test-tags sv,/madenat_lumber_core:TestVolumeGuideHeader,/madenat_lumber_core:TestGranelRouteCore,/madenat_lumber_core:TestVolumenRestante,/madenat_lumber_core:TestSvReverseUi` | Gestión SV + F3.1 + ruta granel + volumen restante | **81 pruebas, 0 fallas, 0 errores** (RC=0) |
| Upgrade `-u madenat_lumber_core,madenat_lumber_intake` | Carga de módulos | RC=0, sin errores; sin avisos nuevos de campos o grupos por este cambio |

### 10.3 Contraste histórico y estado de la base

- Guía 4495589 (`madenat.guia.processing` 6566): `write_date` 2026-09-27 02:32:39, **anterior** a
  las corridas de esta fase; no modificada.
- Etiqueta `SV00000000008` (`stock.lot` 3772): `write_date` 2026-09-26 06:14:57, `volumen_m3`
  40,300, sin marca de serialización y sin operaciones SV; no modificada.
- Secuencia `madenat.volume.lot`: `number_next = 1` (sin cambios). Ledger `madenat.sv.operation`:
  0 filas.
- Sin datos de prueba persistidos (0 guías `LC-*`/`SV-CONS-*`, 0 lotes de prueba, 0 adjuntos
  `LC-C-*`) y sin eventos nuevos de auditoría de los tipos `guia_delete_blocked`,
  `guia_delete_permanent` ni `guia_purged`.
- **Evidencia huérfana preexistente (ajena a esta fase):** la base `madenat_test` contiene
  **55 `mail.message` y 18 `ir.attachment`** de `madenat.guia.processing` apuntando a guías ya
  inexistentes, todos con `create_date` entre 2026-06-30 y 2026-07-08 (borrados históricos por
  SQL de sesiones anteriores). Verificado que **no se creó ningún mensaje/adjunto huérfano**
  durante esta fase: 0 registros con `create_date` de la sesión y 0 residuos de prueba. La regla
  de evidencia del Modo A/C evita que se sigan produciendo huérfanos por vía ORM y obliga a
  preservar la evidencia viva (Modo B).
