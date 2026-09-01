# MADENAT — Matriz de Evidencia y Validación

**Versión documental:** 6.4.0
**Fecha de actualización:** 2026-06-16  <!-- actualizado: 2026-06-16 -->
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
