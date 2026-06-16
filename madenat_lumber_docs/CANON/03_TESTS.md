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
- **Solución:** Corrección en la lógica condicional para que las líneas con perfil `blanks_clear` usen exclusivamente `BLANK_CLEAR_FACTOR` (f5085), sin aplicar deducciones de cepillado (`FACE_DEDUCTION_INCH`, `S2S_WIDTH_ADJUSTMENT_INCH`).
- **Validación local:** Módulo actualiza sin error de registry. Cálculo volumétrico verificado en recepción con blanks.
- **Estado:** CERRADO (Evidencia local)

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