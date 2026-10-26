# MADENAT — Matriz de Evidencia y Validación

**Versión documental:** 6.43.0
**Fecha de actualización:** 2026-10-26  <!-- actualizado: 2026-10-26 — **Consolidación documental FASE 2 (E1)**: sincronización de la cabecera con la fila del índice, que ya declaraba 6.43.0 / 2026-10-26 al registrar §34 (AD-134) en `1c14206`. Sin cambio de contenido. Sin push ni despliegue. | FASE 2. -->
<!-- actualizado: 2026-10-19 — §33 SUITE DE PRUEBAS BLOQUE 6 (AD-127): 26 pruebas unitarias nuevas distribuidas en core, intake e ingestion engine; referencia al script oficial madenat_lumber_core/scripts/run_regression.sh. Total suite acumulada: 1.565 + 26 = 1.591 pruebas. Versión 03 6.41.0 → 6.42.0. Sin commit/push. -->
<!-- actualizado: 2026-10-18 — §32 SUITE DE PRUEBAS BLOQUE 5 (AD-126): 14 pruebas unitarias (4 en test_lumber_thickness_real_map_5a, 5 en test_vol_physical_real_5b, 5 en test_volume_comparison_5c); desglose nominal de las 10 fallas preexistentes de regresión (6 en core, 4 en logistics); corrección de atribución errónea "de costing". Total esperado en suite: 1.551 + 14 = 1.565 pruebas. Versión 03 6.40.0 → 6.41.0. Sin commit/push. -->
<!-- actualizado: 2026-10-18 — §32 SUITE DE PRUEBAS BLOQUE 5 (AD-126): 13 pruebas unitarias nuevas en madenat_lumber_core (4 en test_lumber_thickness_real_map_5a, 5 en test_vol_physical_real_5b, 4 en test_volume_comparison_5c). Total acumulado esperado en suite: 1.551 + 13 = 1.564 pruebas. Versión 03 6.39.0 → 6.40.0. Sin commit/push. -->
<!-- actualizado: 2026-10-18 — §31 REGLA CANÓNICA DE ARNÉS DE REGRESIÓN: uso exclusivo de -u (nunca -i) sobre módulos requeridos (M1 / AD-125). Análisis Odoo loading.py / convert.py; erradicación de -i en scripts. Versión 03 6.38.0 → 6.39.0. Sin commit/push. -->
<!-- actualizado: 2026-10-10 (1) — §14 **cierre funcional 2026-10-10**: corridas nuevas (no históricas) — dirigidas `TestGuiaProcessingExcelParser` + `TestVolumeUiHierarchy` + `TestVolumeOperationsScreen` = **0 failed, 0 error(s) of 34 tests**; regresión de módulo `madenat_lumber_intake` = **2 failed of 380** (ambas por el encabezado consolidado «📄 Evidencia documental»; constantes de prueba adaptadas → verde) + verificación con documento REAL de la Nota de Venta JCE (12/12 líneas, `4,9967` ≈ `VOL.` 4,997) y de la Consola (Ferramenta 57,840 / 48,009). Ver `02_CONTINUIDAD.md` §17.16. | 2026-10-08 (5) — §13.5–13.6 **reconstrucción de las pruebas con la biblioteca externa de muestras** (`muestras_documentos_ingreso`): relación **prueba ↔ etapa (A–F) ↔ resultado**, con **correspondencia declarada A–F ↔ V0–V3** (los niveles V0–V3 siguen vigentes y no se renombran); casos con evidencia localizada: Ferramenta **26270** (adjuntos + 17 lotes + picking + réplica en TEST remoto), Ferramenta **19846/19827/19826**, Arauco **4495589** (fixture byte-idéntico + motor real + registro + lote), JCE **95806** guía (Volúmenes) y su packing Nota de Venta (rechazo por diseño), Fátima **41994** y Byc **95083** (fixture derivado / formato equivalente a `39519`, sí ingresado); **fuerza de la evidencia** y **ausencias declaradas** (dónde se buscó y qué artefacto falta); **no** se ejecutó ninguna prueba en esta intervención. | 2026-10-08 (4) — §13 RELACIÓN REQUISITO → EVIDENCIA → RESULTADO de las solicitudes de Cristhian (R01–R16, 2026-09-02/07). §13.2 pasa revista a las pruebas **existentes** y su relación con cada requisito; **no se ejecutó ninguna prueba nueva** en esta intervención (el servicio local 8069 no es operativo desde esta distro y el TEST remoto se inspeccionó solo lectura). Se declaran explícitamente las ausencias de evidencia: los **10 adjuntos del correo del 7-sep** no aparecen como tales en ningún expediente; sí existen copias identificables en `muestras_documentos_ingreso/07-09-2026/` (15 archivos, 3 pares duplicados por hash). **5 de 5 proveedores** se identificaron documentalmente (Fátima/Ferramenta/Byc=Blocks & Cutstock/JCE/Arauco) pero **solo 2 tienen fixture automatizado** (`HLZF75_4495589.pdf` Arauco; `tests/fixtures/26270.txt` Ferramenta) y **ninguno** tiene evidencia de ingesta real en el TEST remoto (la tabla `madenat_guia_processing` del remoto contiene **1** registro: guía **26270**, Ferramenta, `validated`). Ver §13.3. | 2026-10-08 (3) — §12.6 A/B **aplicado en el desarrollo existente** (`madenat_test` / 8069) + reorganización de la UI de Ingreso de Madera; **88/88 dirigidas en verde sobre `madenat_test`** (misma nómina del gate, incl. Cristhian uid 8 `su=False`); aislamiento temporal **retirado**; **V3 (navegador) sigue pendiente**. | 2026-10-08 (2) — §12.5: entorno aislado **recreado** (autorizado; workcopy `:ro`, sin diffs) y filestore repoblado; **V3 sigue pendiente de evidencia manual**. | 2026-10-08 (1) — §12.5 retoma de SOLO LECTURA (2026-10-08): **V3 sigue sin ejecutarse** (entorno aislado no conservado tras el reinicio del host); integridad de A/B reverificada (SHA-256 = checkpoint; `patch --dry-run` limpio; A/B ausente del código activo y de `madenat_test`). Ver `02_CONTINUIDAD.md` §17.12. | 2026-10-07 (3) — §12.4: gate previo A/B sobre COPIA del árbol activo con cambios locales (byte a byte = workcopy; diffs sin docs), 88/88 dirigidas en verde incl. usuario real Cristhian (su=False), servidor aislado de navegador (pendiente V3). | 2026-10-07 (2) — §12: cobertura retorno de servicio / imputación posterior (AD-102). -->
<!-- actualizado: 2026-10-10 (2) — §15 relación de conciliación envío–retorno (Bloque A/B/C): suite nueva T1–T12 = 12/12; regresión `madenat_lumber_logistics` = 3 failed, 0 error of 265 (3 fallas PRE-EXISTENTES por aserción global de `deviation`; 0 fallas nuevas). Bloque D no implementado. Versión 03 6.17.0 → 6.18.0. Evidencia: CONCILIACION_ENVIO_RETORNO_20261010/. -->
<!-- actualizado: 2026-10-10 (3) — §15.5 controles A/B/C **acreditados** (reversa/procedencia, reimputación, compañía+regla, elegibilidad dura, N:M presentación) y §15.6 ajuste de integridad (T13–T22 = 22/22; regresión 275 pruebas, 4 fallas: 3 preexistentes + 1 ambiental por evidencia V3 7973, 0 errores). Versión 03 6.18.0 → 6.19.0. -->
**Estado:** ACTIVO — Matriz canónica de validación operativa.

> **Nota de consolidación (FASE 2, 2026-10-26).** Los punteros a expedientes de fase se reescribieron a
> `FASES/<carpeta>/…`, ubicación consolidada dentro de `madenat_lumber_docs`. El texto, las fechas, las cifras
> y las conclusiones históricas **no se alteraron**: solo cambió el puntero. Los artefactos no versionados
> (`logs/`, `db/`, dumps, código de evidencia) se citan por nombre de archivo y carpeta de origen, y su copia
> íntegra está en los `.tar.gz` de D7 (`FASES/FASE13_20261023/evidencias/SHA256_BACKUPS_CONSOLIDACION.csv`).

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

---

## 11. Cobertura — Búsqueda, filtros y agrupaciones de la Consola de Intake (2026-10-07, AD-101)

### 11.1 Suite nueva

| Archivo | Clase | Casos | Cobertura |
|---|---|---|---|
| `madenat_lumber_intake/tests/test_search_console_oc_fecha_modality.py` | `TestIntakeSearchConsole` | 10 | OC documental no se sustituye por la OC vinculada (ambos orígenes); búsqueda y agrupación por OC documental/pendiente/no indicada (no un grupo vacío); `guide_date_kind` emisión/recepción; modalidades y su combinación por AND (dos modalidades ⇒ vacío); producto real por líneas de ambos modelos sin duplicar y sin elegir el primero; procesador por Orden de Procesamiento ≠ proveedor; registros incompletos + usuario operativo + navegación; sin duplicación de filas; la lista expone el origen de fecha |

### 11.2 Resultados de ejecución (aislado)

| Corrida | Alcance | Resultado |
|---|---|---|
| Clase nueva | `TestIntakeSearchConsole` | **10 pruebas, 0 fallas, 0 errores** |
| Ampliada (nueva + regresión) | + `TestVolumeOfficialVolume`, `TestIntakeModality`, `TestDocumentalConsole`, `TestIntakeConsoleActions`, `TestIntakeNavigationActions` | **66 pruebas, 0 fallas, 0 errores** (10 nuevas + 56 de regresión) |

- **Base:** aislada dedicada, clon de una base test *idle*; workcopy montado `:ro`; sin tocar
  `madenat_test`.
- **Identidad de ejecución:** la corrida automatizada se ejecutó por el proceso de test (env de
  superusuario); **no** se acredita un usuario operativo específico en la corrida. La verificación
  "con usuario operativo" se cubrió en las pruebas (lectura de la Consola por un usuario de
  `group_madenat_operaciones`) y en la comprobación ORM posterior (§11.3).

### 11.3 Verificación posterior a la aplicación (no destructiva, `madenat_test`)

| Comprobación | Resultado (2026-10-07) |
|---|---|
| Vista `madenat_lumber_intake_console` | existe; **14 columnas** (`id`,`source_model`,`source_res_id`,`ingestion_type`,`guide_name`,`guide_date`,`guide_date_kind`,`partner_id`,`purchase_id`,`purchase_reference`,`oc_documental`,`state`,`display_reference`,`processor_id`) |
| Filas vs IDs distintos | **18 = 18** (sin duplicación) |
| OC | documental **15** · vinculada **0** · pendiente **15** · no indicada **3** |
| Modalidades | product 7 · processed 6 · volume 5 |
| Origen de fecha | emission 17 · reception 1 |
| Producto real (búsqueda) | producto id 62 → 2 ingresos (ambos modelos), sin duplicar |
| Procesador | 0 filas con procesador en la base (guías sin Orden de Procesamiento) |
| Navegación | offset correcto (`id = res_id`; `900000000 + res_id`); `action_open_source` OK en ambos orígenes |
| Update del módulo | 0 ERROR; `Registry loaded in 11.6s`; servicio reiniciado; HTTP 200 |

> Las cifras corresponden a la **fecha de verificación** (2026-10-07) y a esa base; **no** son
> valores permanentes del sistema. **HTTP 200** acredita disponibilidad del servicio, **no** el
> comportamiento de los filtros; la **ausencia de errores** no es prueba de comportamiento UI.

### 11.4 Niveles de verificación

- **V1 — XML/estático:** revisado (diff documental/código coherente).
- **V2 — ORM/SQL:** **ejecutada** (pruebas + consultas de solo lectura).
- **V3 — Navegador:** **PENDIENTE** (ver guion de verificación en el expediente de aplicación).


---

## 12. Cobertura — Retorno de servicio (identificación no bloqueante) e imputación posterior (2026-10-07, AD-102)

**Base y aislamiento.** Base dedicada `srvretab_test_20261007` (clon lógico de `srvret_test_20261006`,
base **test** aislada). Addons del workcopy `IMPL_SERVICE_RETURN_AB_20261007/addons` montados `:ro`; el
árbol activo `custom_addons` **no** se tocó. `--workers=0 --no-http --max-cron-threads=0`;
`--stop-after-init`; sin SMTP. `su=False` en las acciones (usuarios de prueba por ACL real).

### 12.1 Suite nueva y modificada

| Suite | Clase | Pruebas |
|---|---|---|
| `madenat_lumber_intake` (nueva) | `TestServiceReturnConfirmation` | 13 |
| `madenat_lumber_logistics` (nueva) | `TestServiceReturnPendingFilter` | 9 |
| `madenat_lumber_logistics` (nueva) | `TestServiceReturnImputationGuard` | 8 |
| `madenat_lumber_logistics` (mod.) | `TestSvImputationI2` (fixture con destino «Sí») | 13 |
| `madenat_lumber_logistics` (mod.) | `TestSvImputationCandidatesI2` (fixture con destino «Sí») | 12 |

### 12.2 Resultados (aislado, 2026-10-07)

- **Corrida dirigida:** `0 failed, 0 error(s) of 85 tests` (`logs/iso_run1.log`): los 5 grupos
  anteriores + `TestGranelRouteCore` (14), `TestIntakeConsoleActions` (13),
  `TestIntakeDirectStock` (3).
- **Corrida completa** de las 3 suites (`logs/iso_full_run1.log`): `madenat_lumber_core` 486 ·
  `madenat_lumber_intake` 458 · `madenat_lumber_logistics` 290 = **1020** pruebas;
  `5 failed, 4 error(s)`. **Las 9 fallas son PREEXISTENTES:** se reproducen **idénticas** con el
  **código activo sin el cambio** (`logs/base_targeted.log`: `4 failed, 5 error(s) of 34`). **No hay
  regresión atribuible a AD-102.**

**Cobertura A (identificación no bloqueante).** Sí/No se conservan; vacío es pendiente y **≠** No;
**no** bloquea `action_send_to_stock`/`action_validate`; identificación posterior; permisos reales
(Operaciones escribe; sin grupo → `AccessError`); **sin** imputación automática; reintento **no**
duplica; fallo sin efectos parciales; proxy de consola **editable** por el usuario operativo.

**Cobertura B (imputación posterior).** `action_apply` exige destino marcado «Sí» (vacío/`no` →
rechazo); `action_pending` **no** lo exige; cambio Sí→No/vaciar **rechazado** con imputación
`applied` y **permitido** tras reversar (o con solo borrador); **sin** efectos de stock/ledger
(`action_type='imputacion'` = 0). Regresiones I2 en verde.

### 12.3 Niveles de verificación

- **V1 — XML/estático:** revisado (XML bien formado; `py_compile` OK).
- **V2 — ORM/SQL:** **ejecutada** (85/85 dirigidas; 1020 completa).
- **V3 — Navegador:** **PENDIENTE** (no acreditada; guion manual en §12.4).
- **Usuario real Cristhian:** **ACREDITADO** en la corrida del gate (§12.4; base que lo contiene).


### 12.4 Gate previo sobre copia del árbol ACTIVO (con cambios locales) — 2026-10-07

- **Copia del gate:** `/tmp/gate` = **árbol activo con sus cambios locales** + `A` + `B` (diffs).
  Verificado **byte a byte** contra el workcopy `IMPL_SERVICE_RETURN_AB_20261007/addons`
  (**45/45** archivos). Los diffs **no** tocan `madenat_lumber_docs/` (no sobrescriben la
  documentación ya actualizada) ni otras mejoras locales (verificado: 0 archivos de docs en A/B).
- **Pruebas dirigidas repetidas** sobre esa copia, base aislada `srvretab_gate_20261007`:
  **`0 failed, 0 error(s) of 88 tests`** (`logs/gate_run2.log`). Incluye las **3 pruebas con
  Cristhian** (`su=False`, permisos reales; grupos **no** modificados): `test_14`/`test_15` (intake)
  y `test_09` (logistics).
- **Servidor aislado de verificación:** `http://127.0.0.1:8070` (base `srvretab_gate_20261007`,
  contenedor `srvretab_web`); login de Cristhian verificado por sesión (`uid=8`). **No** es el
  servicio activo (`odoo18_app`, 8069).
- **Navegador (V3): PENDIENTE.** **No ejecutado** (sin navegador). Guion manual:
  `FASES/IMPL_SERVICE_RETURN_AB_20261007/docs/GUION_VERIFICACION_NAVEGADOR.md`. **No** se declara
  completado.
- **Preexistentes/límites:** se mantienen las **9 fallas** de §12.2 y los **límites de concurrencia**
  no probados.


### 12.5 Retoma 2026-10-08 — V3 **no ejecutada** (entorno aislado no disponible)

- **Solo lectura:** no se aplicaron diffs, no se actualizaron módulos, no se reiniciaron servicios.
- **Integridad reverificada (idéntica al gate):** SHA-256 de `A`/`B`/`AB` = checkpoint; el workcopy
  `IMPL_SERVICE_RETURN_AB_20261007/addons` difiere del árbol activo **exactamente** en los **15**
  archivos de `AB_completo.diff` (12 modificados + 3 nuevos); `patch -p1 --dry-run` sobre copia de
  trabajo ⇒ **0 rechazos**; **A/B ausente** del código activo y de `madenat_test` (columna
  inexistente).
- **Bloqueo de V3 (no es un fallo del artefacto):** el host se reinició (2026-10-08) y el entorno
  aislado **no se conservó**: contenedor `srvretab_web` inexistente, `127.0.0.1:8070` cerrado,
  `/tmp/gate` vacío. La base `srvretab_gate_20261007` **sí** se conserva (columna nueva, 12 guías).
- **V3 sigue PENDIENTE.** **No** se declara «navegador verificado». **No** se acepta HTTP 200 ni prueba
  de framework como evidencia de V3. La contraseña temporal **no** se divulga.
- **Entorno aislado RECREADO (autorizado 2026-10-08, solo aislamiento):** `srvretab_web` en
  `127.0.0.1:8070` con el **workcopy montado `:ro`** (**sin** aplicar diffs, **sin** `-u`, **sin**
  `--test-enable`); selector limitado a `srvretab_gate_20261007`; filestore del aislamiento repoblado
  desde el volumen del stack (`:ro`) — assets de **500 → 200**; los 35 adjuntos no resueltos son solo
  avatares de `res.partner`. Escritura **solo** en el volumen del aislamiento. **V3 = pendiente de
  evidencia manual** (fecha, usuario y capturas).
- **Sin cambios en los límites:** 9 fallas preexistentes (§12.2), concurrencia no acreditada, filtro
  sin cobertura parcial, I3/I5 fuera de alcance. Ver `02_CONTINUIDAD.md` §17.12.

### 12.6 A/B aplicado en `madenat_test` + reorganización de UI (2026-10-08)

**Entorno (desarrollo, no producción).** `http://localhost:8069/` · base **`madenat_test`** ·
contenedor `odoo18_app`. El código evaluado es el **efectivamente cargado** en ese servicio
(`custom_addons` montado en `/mnt/extra-addons`). **No** se presentan capturas ni resultados del
entorno 8070 como evidencia de esta implementación (ese aislamiento se retiró; ver §12.6.4).

#### 12.6.1 Preparación previa a la ejecución de pruebas

- Las suites de A/B son `TransactionCase` con `@tagged('post_install','-at_install', …)`: se ejecutan en
  el **post-install** de un proceso *one-shot* con `--test-enable --test-tags=… --stop-after-init`.
  Cada prueba **revierte su transacción**: no persiste registros existentes de forma irreversible y
  **no** activa integraciones externas (sin SMTP; `--max-cron-threads=0 --workers=0 --no-http`).
- `--test-tags` limita la corrida a las **8 clases dirigidas** (y excluye `at_install`), de modo que la
  suite completa de Odoo **no** se ejecuta.

#### 12.6.2 Pruebas ejecutadas en esta implementación (evidencia nueva, sobre `madenat_test`)

`0 failed, 0 error(s) of 88 tests when loading database 'madenat_test'` (`odoo.tests.result`; log
`FASES/APPLY_AB_UI_20261008/` (artefacto `tests_directed_madenat_test_20261008_093825.log` en `logs/`, fuera de git)).

| Suite | Clase | Rol | Resultado |
|---|---|---|---|
| `madenat_lumber_intake` (nueva) | `TestServiceReturnConfirmation` | A/B (incl. `test_14`/`test_15` con **Cristhian uid 8**, `su=False`) | ✅ |
| `madenat_lumber_logistics` (nueva) | `TestServiceReturnPendingFilter` | A/B (filtro «Retornos sin imputación aplicada») | ✅ |
| `madenat_lumber_logistics` (nueva) | `TestServiceReturnImputationGuard` | A/B (exigencia destino «Sí» + guard Sí→No) | ✅ |
| `madenat_lumber_logistics` (reg.) | `TestSvImputationI2` | regresión I2 | ✅ |
| `madenat_lumber_logistics` (reg.) | `TestSvImputationCandidatesI2` | regresión I2 | ✅ |
| `madenat_lumber_core` (reg.) | `TestGranelRouteCore` | regresión core | ✅ |
| `madenat_lumber_intake` (reg.) | `TestIntakeConsoleActions` | regresión consola | ✅ |
| `madenat_lumber_intake` (reg.) | `TestIntakeDirectStock` | regresión envío a stock | ✅ |

**Sin `skip`:** ninguna prueba fue omitida (incluidas las de Cristhian). **0 fallas nuevas y 0
regresiones** atribuibles a A/B ni al ajuste de UI.

Separación de evidencias:

| Evidencia | Qué es | Estado |
|---|---|---|
| **Gate histórico 88/88** (`logs/gate_run2.log`, 2026-10-07) | Antecedente sobre copia aislada; **no** es evidencia de esta instalación | Conservado como histórico |
| **Dirigidas 88/88 sobre `madenat_test`** (2026-10-08) | Pruebas **realmente ejecutadas** en esta implementación | ✅ Ejecutada |
| **9 fallas preexistentes** | `iso_full_run1.log` + `base_targeted.log`; idénticas **sin** el cambio | Preexistentes, conservadas |
| **Regresiones nuevas** | — | **0** |

#### 12.6.3 Verificación técnica y estructural (sin navegador)

- Actualización de módulos finalizada: `Modules loaded.` con **0 ERROR / 0 CRITICAL**; única advertencia
  de vista = `A <i> with fa class … must have title` (**preexistente**: aparece también antes del
  cambio).
- Esquema: `madenat_guia_processing.service_return_confirmation` = `character varying` en
  `madenat_test`.
- Vistas cargadas: `madenat.lumber.intake.console.form` (id 1867) recompilada sin error; nueva vista
  `madenat.guia.processing.search.service.return` (id 2909).
- Estructura efectiva de la consola (*read-only*): resumen en 2 columnas; **un** encabezado «Evidencia
  documental»; `col="3"` con «Documentos», «Volúmenes y diferencias» y «Packing y conciliación»;
  `Aplicar cambios`; campo y proxy del radio presentes; orden `resumen → botón → radio → evidencia →
  packing`.
- Registro de desarrollo identificado para la verificación manual: guía **19827** (id 1198,
  `tipo_recepcion='service'`, `state='verified'`), con fila de consola `ingestion_type='processed'`,
  `service_return_in_scope=True` y confirmación **vacía**. **No** se forzaron estados ni se modificaron
  permisos.

#### 12.6.4 Límites y pendientes conservados

- **V3 (navegador): PENDIENTE.** No ejecutada (sin navegador disponible): **no** se declara verificada.
  Guion actualizado a `http://localhost:8069` / `madenat_test`.
- **9 fallas preexistentes** (§12.2), **concurrencia no acreditada**, **filtro sin cobertura parcial** e
  **I3/I5 fuera de alcance**: sin cambios.
- **No** se ejecutó la suite completa de los 3 módulos sobre `madenat_test` (solo las 8 clases
  dirigidas) para no introducir ruido de fallas preexistentes no relacionadas.
- **Retiro del aislamiento:** contenedor `srvretab_web` (:8070), volumen `srvretab_web_data`, bases
  `srvretab_gate_20261007` / `srvretab_base_20261007` / `srvretab_test_20261007` y
  `/tmp/{gate,ab_dryrun,iso_*}` eliminados (dumps de las 3 bases conservados en
  `APPLY_AB_UI_20261008/retired/db/`). Ver `02_CONTINUIDAD.md` §17.13.4.
- **Ingreso de Madera (UI):** verificación **visual** en navegador **pendiente** junto con V3; la
  verificación estructural del §12.6.3 **no** sustituye la observación del operador.


## 13. Relación requisito → evidencia → resultado — Solicitudes de Cristhian (2026-09-02 / 2026-09-07) — auditoría 2026-10-08

**Alcance.** Registra la relación entre cada requisito (R01–R16) y la **evidencia de prueba existente**.
**No se ejecutó ninguna prueba nueva en esta intervención**: el servicio local `8069` no era operativo
desde la distro del entorno de trabajo y el TEST remoto se inspeccionó **solo lectura** (no autorizado
para pruebas). La **matriz consolidada** (criterio de aceptación, evidencia de código, entorno y estado)
vive en `02_CONTINUIDAD.md` **§17.14.2**; los hallazgos, en **§17.14.3**.

### 13.1 Niveles de verificación aplicados

| Nivel | Qué es | ¿Ejecutado en esta auditoría? |
|---|---|---|
| **V0 — documental** | Lectura de los archivos originales o de copias identificables (con hash) | **Sí** (15 archivos de `muestras_documentos_ingreso/07-09-2026/`) |
| **V1 — estático** | XML bien formado, campos existentes en el modelo, búsquedas literales de mensajes | **Sí** (local y remoto) |
| **V2 — ORM/SQL** | Pruebas automatizadas | **No** en esta intervención (solo se citan corridas previas) |
| **V3 — navegador** | Observación en interfaz | **No** ejecutada (sin navegador) |
| **Remoto** | Lectura de hash de código, `ir_module_module`, `information_schema`, `ir_ui_view`, `madenat_guia_processing` | **Sí**, solo lectura |

### 13.2 Pruebas existentes por requisito

| RQ | Prueba / evidencia existente | Qué demuestra realmente | Resultado | Nivel | ¿Cubre el requisito? |
|---|---|---|---|---|---|
| R01 | `test_intake_wizard.py:537-543` (asertan el `warning` y el texto «no bloquea») | que el aviso de perfil de lectura se emite y se declara no bloqueante | verde (histórico) | V2 | **No** (el aviso sigue vigente y en Odoo interrumpe hasta «OK») |
| R02 | `test_intake_tipo_ingreso_content.py` | que la clasificación es por **contenido**, no por RUT ni historial | verde (histórico) | V2 | **Sí** (en código); V3 pendiente |
| R03 | Cobertura de subproducto en `test_guia_processing.py` | resolución/autocreación de `madenat.subproducto` | verde (histórico) | V2 | **No**: no reproduce el defecto reportado el 02-sep |
| R04 | Utilidades de fracción (`parse_fraction_to_decimal_inch`, `decimal_inch_to_fraction_simple`) | conversión decimal↔fracción | verde (histórico) | V2 | **No**: no hay prueba de la **presentación** del packing en la Consola |
| R05 | — (no hay fixture de Fátima) | — | — | V0 (medición documental: guía **50,496** vs packing **50,495625**) | **No** |
| R06 | `tests/fixtures/26270.txt` + `test_supplier_resolution.py` / `test_reception_supplier_rut_extraction.py` | RUT y nombre del proveedor en texto de la guía; **no** el packing | verde (histórico) | V2 | **No** |
| R07 | `test_parse_excel_core.py::test_packing_declared_totals_persisted` (**42,132 / 2244 / 8**), `::test_vol_documental_m3_written`, `::test_sum_vol_documental_m3` | persistencia de los totales de packing y de la conciliación | verde (histórico) | V2 | **Parcial**: el dato real de la guía Ferramenta no está poblado |
| R08 | `test_parse_excel_core.py::test_xls_blanks_abbreviated_headers` + `::test_packing_declared_totals_persisted` | lectura de la **estructura** del packing de Byc (cabecera abreviada, decimales con coma) y sus totales (42,132 / 2244 / 8) | verde (histórico) | V2 | **Parcial**: fixture sintético, no el archivo de Byc |
| R09 | `test_parse_excel_core.py::test_nota_venta_dimensions_raw_rejected_with_diagnostic`; `madenat_ingestion_engine::test_generic_pdf_table::test_tabla_una_fila_volumen` | que el documento **se lee** y que su línea se **rechaza** con `REQUIERE_DIMENSIONES_SEPARADAS` y «No se creó ninguna línea» | verde (histórico) — **resultado negativo por diseño** | V2 | **Sí** acredita que **no** se crean líneas (es la causa probable del síntoma) |
| R10 | Ídem R09 | Ídem | verde (histórico) | V2 | **Parcial** |
| R11 | `test_generic_pdf_table.py::test_tabla_12_filas_lotes_mixtos` (12 líneas, 40,300 m³, refs `3540383149`/`PK45738`) + `test_intake_volume_detail_pieces.py` / `test_reopen_oc_reextraction.py` (fixture real `HLZF75_4495589.pdf`) | que la **guía real** de Arauco se procesa en la ruta de **Volúmenes** y que el extractor genérico reproduce su packing | verde (histórico) | V2 | **No** cubre el par del correo en modalidad Normal (packing PDF) |
| R12 | `test_service_return_confirmation.py` (**13**) | Sí/No/vacío, vacío≠No, no bloquea, permisos reales | **88/88 verde (2026-10-08) sobre `madenat_test`** | V2 | **Sí** en V2; **V3 pendiente** |
| R13 | `test_service_return_imputation_guard.py` (**8**), `test_service_return_pending_filter.py` (**9**), regresiones `test_sv_imputation_i2.py` / `_candidates.py` | reglas de aplicar/reversar y filtro | ídem anterior | V2 | **Sí** en V2; **V3 pendiente** |
| R14 | Verificación estructural §12.6.3 + vista cargada en el TEST remoto (id 1660) | estructura (columnas, encabezado único, orden), **no** apariencia | verde (estructural) | V1 | **No**: falta la observación visual |
| R15 | — | — | **no reproducido** | — | **No** |
| R16 | Manifiesto SHA-256 de **314** archivos + esquema y vistas del remoto | correspondencia de **código** y **esquema** | **0 discrepancias** | V1 + lectura remota | **Parcial**: no acredita que el remoto pase pruebas |

### 13.3 Ausencias de evidencia declaradas (no se inventan resultados)

1. **Adjuntos del correo del 7-sep:** **no** existe el correo ni los 10 adjuntos como expediente
   (no hay `*.eml`). Se trabaja con **copias identificables** de
   `muestras_documentos_ingreso/07-09-2026/` (**15** archivos; **3** pares duplicados por hash md5),
   declaradas como tales. **No** se usan archivos distintos como sustitutos silenciosos.
2. **Ningún proveedor tiene prueba de ingesta real:** **0 de 5**. La única guía real existente en el
   TEST remoto es la **26270** (Ferramenta), `validated` desde el 2026-10-06.
3. **Fixtures:** solo **2 de 5** proveedores tienen archivo asociado en tests
   (`madenat_lumber_intake/tests/fixtures/HLZF75_4495589.pdf` y
   `madenat_lumber_core/tests/fixtures/26270.txt`), y **ninguno** con el **par guía+packing completo**.
4. **V3 (navegador):** no ejecutada ni antes ni en esta auditoría.
5. **La corrida 88/88 es de la base local** `madenat_test` (desarrollo): **no** se traslada al TEST
   remoto.
6. **No se ejecutaron pruebas que creen o modifiquen registros** (prohibido sin autorización
   específica), ni integraciones, ni actualizaciones de módulos, ni reinicios de servicios.

### 13.4 Criterio de aceptación por formato de proveedor (recordatorio normativo)

Para considerar un formato de proveedor **corregido** deben cumplirse **todos**:
el documento original o un equivalente **explícitamente identificado** se lee; guía y packing se asocian
correctamente cuando corresponde; se extraen los datos exigidos; el ingreso se guarda y avanza hasta el
punto acordado; y **no** aparece el rechazo reportado, o el nuevo mensaje corresponde a una validación
legítima y accionable. **No** se desactivan validaciones válidas para hacer desaparecer «operación no
válida». Complementos: para volúmenes (R07) deben identificarse y mostrarse **por separado** el volumen
de guía, el de packing y el de embarque, con su diferencia, unidades, fórmula, precisión y redondeo; para
fracciones (R04) deben distinguirse **valor original del documento**, **valor normalizado para cálculo**
y **valor mostrado**, comprobando que el cambio de presentación **no** altera el volumen.

### 13.5 Reconstrucción de pruebas con la biblioteca de muestras (2.ª pasada, 2026-10-08)

**Antecedente.** Mauricio confirma que **se probaron todos los ingresos** y que los formatos probados
están en la **biblioteca externa** `muestras_documentos_ingreso` (fuera de `custom_addons`). La
reconstrucción y su evidencia están en `02_CONTINUIDAD.md` **§17.15**; aquí se resume la **relación
prueba ↔ etapa ↔ resultado**.

**Niveles de esta revisión (A–F) y su correspondencia con V0–V3:** A lectura → V0/V1; B interpretación →
V2 + V1; C integración documental → V2; D flujo de ingreso → V2 + registro persistente; E stock → V2 +
datos de stock; F interfaz → **V3**. Los niveles **V0–V3 siguen vigentes** y no se renombran.

| Caso (proveedor · guía) | Muestra real | Prueba / artefacto localizado | Etapa | Resultado |
|---|---|---|---|---|
| **Ferramenta · 26270** | `26270.pdf` + `26270.xlsx` | Adjuntos en `guia.processing` 1728 · **17 lotes** con los M3 del packing · 1 picking · `validated` · replicado en **TEST remoto** · transcripción `fixtures/26270.txt` | **A–E** | **Ingreso completo hasta stock** (los tres volúmenes explicados) |
| **Ferramenta · 19846 / 19827 / 19826** | `GDE Guía de Despacho 198xx.pdf` + `FACTURACION PACKING LIST …xlsx` | Adjuntos con **esos nombres** · **19/17/17 lotes** · pickings · `validated`/`verified` · golden record 19846 en `test_guia_processing.py` | **A–E** | Ingreso + materialización en stock |
| **Fátima · 41994** | `Guia 41994.pdf` + `41994.xls` | Fixture **derivado** (`test_excel_table_detection.py::test_two_row_header`: misma cabecera de 2 filas y 1.ª línea `0000000134008`) · **formato idéntico** a `39519 (1).xls` (**ingresado**, `lumber.reception` 1161, `verified`) | **A–B** (+D por equivalencia) | Formato legible/ingerible; **sin ingreso propio de 41994** |
| **Byc · 95083** | `95083 .pdf` + `95083 Final.xls` | `excel_table_detection.py` («investigación 95083») · `test_excel_table_detection.py` («Estructura tipo 95083», valores reales de la 1.ª fila) · `test_parse_excel_core.py` («tipo 95083») · `test_packing_declared_totals_persisted` (42,132/2244/8) | **A–B** | Estructura e interpretación acreditadas; **sin ingreso registrado** |
| **JCE · 95806 (guía)** | `GDE 95806.pdf` | Registro **33151** `granel`/`verified` 59,964 · adjuntos del wizard (2026-10-06) · fixtures derivados (`test_document_format.py`, `test_generic_pdf_table.py`) | **A,B,D** | **Guía leída e ingresada** por Volúmenes |
| **JCE · packing Nota de Venta** | `GDE 95806.xls` / `NVTA881333 (2).xls` | `test_nota_venta_dimensions_raw_rejected_with_diagnostic` (fixture derivado con **cabecera y valores reales**) | **A–B** | Se lee; **rechazo por diseño** (`REQUIERE_DIMENSIONES_SEPARADAS`) |
| **Arauco · 4495589** | `HLZF75_4495589.pdf` (**fixture byte-idéntico**) + `PACKING HLZF75 (1).pdf` | `test_intake_volume_detail_pieces.py` (**motor real**) y `test_reopen_oc_reextraction.py` · registro **15326** `granel`/`validated` 40,315 · lote `GRANEL 4495589` · pickings `EMB-01768` `[PURGADO-TEST]` + reversa · estructura del packing en `test_generic_pdf_table` | **A–D** (E con purga) | **Guía leída, ingresada y validada** |
| Fátima · ejercicio (39519, 41471, 41964) | Guías y packings del «Ejercicio Completo…» | `lumber.reception` 1161/962/1371 `verified` con **esos archivos** | **D–E** | Ingresos por Producto |
| Regresión (97183, 15183, 100006) | `GD 97183.pdf`+`42.50 Kb.xls`, `15183.xls`, `Packing GD 100006 - W.xls` | `lumber.reception` 1244/1369/1270 `verified`; expedientes `INCIDENTE_GUIA_15183_20261007/` | **D–E** | Ingresos reales; 15183 con incidente propio |

### 13.6 Fuerza de la evidencia y ausencias declaradas (2.ª pasada)

- **Lo más fuerte:** ejecuciones registradas con adjuntos de **nombre original**, estado final, **lotes**
  y **pickings**; + **fixture byte-idéntico** de Arauco ejercitado por el motor real; + **fixtures
  derivados** con cabecera/valores verificados contra el documento.
- **Sin registro persistente localizado:** `41994` (Fátima) y `95083` (Byc) **como ingreso**. Se declara
  dónde se buscó: base local (dump 2026-10-08), **9 respaldos de base** del proyecto, TEST remoto,
  `ir_attachment`, `madenat_guia_processing`, `lumber_reception`, `stock_lot`, `stock_picking`, y todo el
  árbol de texto del proyecto (grep por número y por nombre de archivo). **Artefacto que falta**: un
  registro de ingreso (o ejecución de prueba) con esas dos guías.
- **Fixtures reales vs derivados vs sintéticos (corregido respecto de §13.3):** **1 real** (Arauco,
  byte-idéntico) + **1 transcripción** (`26270.txt`) + **4 familias derivadas** (Byc, Fátima,
  JCE-Nota de Venta, JCE-guía) + **estructura** del packing de Arauco. El resto de las suites usa
  fixtures **sintéticos** declarados como tales.
- **Evidencia histórica vs ejecución nueva:** **todo** lo reconstruido es **histórico** (ago–oct 2026).
  En esta intervención **no** se ejecutó ninguna prueba; las lecturas fueron sobre **archivos de respaldo**
  (dump) y **no** sobre bases vivas.
- **Capturas de navegador:** **no existen** en ningún expediente inspeccionado ⇒ **V3 sigue sin
  acreditación** y el `OwlError` sigue **abierto y no reproducido**.




## 14. Cierre funcional 2026-10-10 — corridas nuevas

**Alcance.** Ejecución en el desarrollo existente `madenat_test` (contenedor
`odoo18_app`, PostgreSQL `odoo18_db`), con el servicio detenido durante la
actualización de módulos. Corridas **nuevas** (no históricas); ver
`02_CONTINUIDAD.md` §17.16. No se ejecutó la suite completa de los 3 módulos ni
concurrencia ni instalación en base limpia (fuera de alcance).

### 14.1 Corridas

| Corrida | Alcance | Resultado | Log |
|---|---|---|---|
| Intake (regresión de módulo) | `--test-tags /madenat_lumber_intake` | **2 failed, 0 error(s) of 380** (→ corregidas) | `FASES/CIERRE_PENDIENTES_20261010/` (artefacto `tests_intake_20261010.log` en `logs/`, fuera de git) |
| Dirigidas (P1/P4) | `TestGuiaProcessingExcelParser` + `TestVolumeUiHierarchy` + `TestVolumeOperationsScreen` | **1 failed of 34** → **0 failed, 0 error(s) of 34** | `.../tests_p4_p1_20261010.log`, `.../tests_p4_p1_run2_20261010.log` |
| Documento real JCE | `GDE 95806.xls` por el parser core real | 12 válidas / 0 rechazadas; `4,9967` ≈ `VOL.` 4,997; Σ `59,960` ≈ guía 59,964 | §17.16.4 |
| Consola Ferramenta | id 900001728 | guía/packing 57,840 · embarque 48,009 | §17.16.2 |

### 14.2 Clasificación de fallas

- **Nuevas de esta intervención: 0.** La única falla de la corrida dirigida fue
  `TestGuiaProcessingExcelParser.test_documentary_lines_collected_not_dropped`,
  causada por el propio cambio P4 (un caso antes documental ahora se normaliza);
  se **adaptó** el caso a un patrón no acreditable (`5/4x5.3/8`) ⇒ verde.
- **No atribuibles a esta intervención:** `TestVolumeOperationsScreen.test_02_...`
  y `TestVolumeUiHierarchy.test_03_...` fallaron por el encabezado de UI
  consolidado («📄 Evidencia documental») aplicado el 2026-10-08; constantes
  adaptadas ⇒ verde.
- **Skips / no ejecutadas:** concurrencia, base limpia y suite completa de los 3
  módulos — fuera de alcance.

### 14.3 Pruebas nuevas añadidas

- `madenat_lumber_core/tests/test_parse_excel_core.py`:
  `test_nota_venta_dimensions_raw_normalized_and_create` (nueva) y
  `test_dimensiones_combinadas_ambiguas_siguen_rechazadas` (nueva). El test
  histórico de rechazo **no se eliminó**: se reprueba el patrón ambiguo y se
  conserva la verificación del diagnóstico `REQUIERE_DIMENSIONES_SEPARADAS`.

### 14.4 Aceptación visual (2026-10-10) — guía 19827

**Nivel V3 (navegador), caso único observado.** Mauricio confirmó el **2026-10-10**, mediante captura y
mensaje, que la **guía 19827** (Ferramenta, `service`, `verified`) se presenta correctamente. Se registra
como **aceptación visual** de la presentación observada:

| Elemento observado | Resultado |
|---|---|
| Formulario abierto satisfactoriamente (caso observado) | ✅ |
| Resumen del ingreso en **dos columnas** | ✅ |
| Evidencia documental en **tres columnas** | ✅ |
| Identificación de retorno **visible** | ✅ |
| Detalle del packing a **todo el ancho** | ✅ |

**No extendida** a operaciones no observadas: persistencia Sí/No/vacío en pantalla; aplicación y reversa
de imputaciones; resolución global del `OwlError`. Estado del `OwlError` (R15): «No reproducido en la
apertura manual observada; causa no confirmada» (`02_CONTINUIDAD.md` §17.16.1). Esta aceptación cierra la
**presentación observada**; los pendientes funcionales independientes permanecen. Detalle:
`02_CONTINUIDAD.md` §17.16.8; flujo de imputación confirmado: `19_IMPUTACION_SV_Y_PROCESADORES.md` §19.10.

## 15. Relación de conciliación envío–retorno (Bloque A/B/C, 2026-10-10)

**Alcance.** Nueva evidencia en el desarrollo existente `madenat_test` (contenedor `odoo18_app`).
Módulos actualizados: `madenat_lumber_core` (valores **aditivos** en `madenat.audit.log.action_type`) y
`madenat_lumber_logistics` (modelo, asistente, vistas, ACL, secuencia). Evidencia:
`CONCILIACION_ENVIO_RETORNO_20261010/`.

### 15.1 Suite nueva — `madenat_lumber_logistics/tests/test_processor_return_link.py` (T1–T12)

| ID | Caso | Resultado |
|---|---|---|
| T1 | Envío con un retorno (registro + 1 evento) | ✅ |
| T2 | Envío con varios retornos parciales | ✅ |
| T3 | Retorno asociado a varios envíos | ✅ |
| T4 | Procesador incorrecto ⇒ rechazo | ✅ |
| T5 | Envío no elegible ⇒ rechazo y no propuesto | ✅ |
| T6 | Relación duplicada ⇒ rechazo; `_get_or_create_link` idempotente | ✅ |
| T7 | Doble aplicación ⇒ sin duplicar auditoría | ✅ |
| T8 | Reversa append-only: `reversed`, no eliminable; Operaciones no reversa | ✅ |
| T9 | Permisos por ORM/RPC (sin grupo ⇒ AccessError; auditoría read-only) | ✅ |
| T10 | Sin movimientos de stock (quants/pickings/moves idénticos) | ✅ |
| T11 | Históricos sin asociación (`no_return`, sin crear nada) | ✅ |
| T12 | Asistente de imputación aplica + registra relación | ✅ |

**Resultado:** `0 failed, 0 error(s) of 12 tests` (`logs/tests_processor_return_link_run2.log`).

### 15.2 Regresión de módulo `madenat_lumber_logistics`

- Corrida: `--test-tags madenat_lumber_logistics` → **3 failed, 0 error(s) of 265 tests**
  (`logs/tests_logistics_regression.log`).
- **Las 3 fallas son PRE-EXISTENTES y ajenas a esta etapa.** Corresponden a aserciones **globales**
  frágiles `assertFalse(AuditLog.search([('action_type','=','deviation')]))` en
  `test_processor_locations.test_09` y `test_processor_shipment_ad89.test_t1/test_t5`. La base ya
  contiene **5** eventos `deviation` históricos (ids 19889/19941/20342/20381/21739, fechas
  **2026-10-04/05/07**, **anteriores** a esta intervención); esos tests **no** se modificaron.
- **0 fallas nuevas; 0 errores.** Las suites de imputación SV (`TestSvImputationI2`,
  `TestSvImputationCandidates`, `TestServiceReturnImputationGuard`) permanecen **verdes**.
- Los tests son **transactionales**: no se persistió ninguna fila `processor_return_link` en la base
  (verificado por SQL: `0 rows`).

### 15.3 Comprobaciones ORM / no cubierto

- **ORM:** creación/registro/reversa, unicidad, permisos y ausencia de stock verificados por tests.
- **No ejecutado (fuera de alcance):** navegador (V3); concurrencia; instalación en base limpia; la
  conciliación **cuantitativa** (Bloque **D**).


### 15.4 Verificación de integración web/RPC — sesión autenticada (2026-10-10)

**Clasificación de la evidencia (tres niveles — NO se presentan como equivalentes):**

| Nivel | Alcance | Estado |
|---|---|---|
| **(a) Integración web/RPC con sesión autenticada** | `POST /web/session/authenticate`, `GET /web/webclient/load_menus`, `POST /web/dataset/call_kw/<model>/<method>` (create/read/search_read/fields_get/action_link/action_reverse) | ✅ **EJECUTADA** |
| **(b) Lectura de arquitecturas de vistas y metadatos** | `get_views` (arch compilado) y `fields_get` | ✅ **VERIFICADA** |
| **(c) Renderizado e interacción en navegador real** | *pixel rendering*, clics de UI | ⏳ **PENDIENTE** (no hay navegador en el entorno) |

> **La verificación (a)+(b) NO sustituye a (c).** No se presenta como V3 ni se declara V3 acreditada.

**Método (a)+(b):** sesión real de Operaciones (`v3_concil_oper@madenat.test`). Artefactos:
`CONCILIACION_ENVIO_RETORNO_20261010/v3/`.

| Verificación | Nivel | Resultado |
|---|---|---|
| Menú «Conciliación Envío–Retorno» | (a) | ✅ |
| `get_views` form/lista `madenat.processor.return.link` | (b) | ✅ sin faltantes |
| `get_views` form guía / picking / imputación / asistente | (b) | ✅ |
| Acceso a datos (`search_read`, `fields_get`) | (a) | ✅ |
| **Operativo:** crear + «Registrar conciliación» (Operaciones) | (a) | ✅ `linked` |
| **Operativo:** reversa por Operaciones | (a) | ✅ **DENEGADA** (solo Jefatura/Gerencia) |
| **Operativo:** reversa por Jefatura | (a) | ✅ `reversed` |
| Auditoría `processor_return_link` + `..._reverse` | (a) | ✅ |

**Registros de prueba creados (identificados; sin eliminar):** procesador `V3 Planta (temp)` (14785),
guía `V3-CONCIL` (33737), envío picking `7973`, lote `V3-LOT` (18003), relación `REL00030`
(`reversed`). Usuarios `v3_concil_oper` (2974) y `v3_concil_jef` (2975) **desactivados** al cierre.

### 15.5 Controles del vínculo envío–retorno — acreditación (2026-10-10)

> Cada control se acredita con **código** y, cuando existe, **prueba**. Lo **no** acreditado se declara;
> **no** se inventa su cierre.

| Control | Referencia de código | Prueba | Estado |
|---|---|---|---|
| **Atomicidad** imputación + registro del vínculo | `wizards/madenat_sv_imputation_wizard.py::action_apply` (`_i2_build_imputation()` → `imp.action_apply()` → `imp.action_link_return_links()`), en la **misma transacción** RPC | T12 | ✅ Acreditado (una transacción; sin commit intermedio) |
| **Reversa de imputación vs. procedencia** | `madenat_processor_return_link.py::_compute_documentary_status` + `madenat_sv_imputation.py::action_reverse` (no toca `return_link_ids`) | T13, T14, T16 | ✅ Acreditado (procedencia se conserva; vigencia pasa a `reversed`; reversa del vínculo independiente) |
| **Reimputación** | `_get_or_create_link` + `_link_note_imputation_change`; `previous_imputation_id` | T15 | ✅ Acreditado (sin duplicar activos; historia preservada; rastro) |
| **Elegibilidad del picking / exclusión de cancelados** | `_eligible_shipment_pickings` + `_check_shipment_is_processor_shipment` (`state='done'`, `picking_type_id.code='internal'`) | T5, T12, T19, T20, T21 | ✅ Acreditado (draft/cancel/assigned **rechazados** por ORM; done elegible) |
| **Consistencia de compañía** | `_check_company_consistency` + `security/madenat_processor_return_link_rules.xml` (`ir.rule`) | T17, T18 | ✅ Acreditado (mismatch rechazado; aislamiento multi-compañía por regla) |
| **Permisos (ORM/RPC)** | `_link_check_apply_permission` / `_link_check_reverse_permission`; ACL 4 grupos (`security/ir.model.access.csv`) | T9; §15.4 (a) | ✅ Acreditado |
| **Doble contabilización N:M (presentación)** | `aggregator=False` en `shipment_volume_m3`/`return_nominal_m3` + ayuda | T22 | ✅ **Mitigado en presentación** (sin sum/avg/pivot/`read_group`); el **reparto cuantitativo** sigue siendo Bloque **D** |

### 15.6 Ajuste de integridad A/B/C (2026-10-10) — T13–T22 y regresión

**Nuevas pruebas dirigidas** (mismo archivo `test_processor_return_link.py`): **T13** vigencia aplicada ·
**T14** reversa conserva la procedencia · **T15** reimputación (sin duplicar activos; historia) · **T16**
reversa del vínculo independiente de la vigencia · **T17** compañía incompatible rechazada · **T18**
regla de registro multi-compañía (aislamiento) · **T19/T20/T21** envío `draft`/`cancel`/`assigned`
rechazado por ORM · **T22** volúmenes referenciales sin agregación.
**Resultado: `0 failed, 0 error(s) of 22 tests`** (`logs/tests_integridad_link_run2.log`).

**Regresión de módulo (corrida nueva):** `madenat_lumber_logistics` =
**`4 failed, 0 error(s) of 275 tests`** (`logs/tests_integridad_regression.log`). **No** es una suite
completamente verde. Las **4 fallas**:
1. **3 preexistentes** (aserción global `deviation`, eventos históricos 2026-10-04/05/07):
   `test_processor_locations.test_09_auditoria_envio_normal`,
   `test_processor_shipment_ad89.test_t1_envio_manual_parcial_sin_motivo`,
   `test_processor_shipment_ad89.test_t5_desviacion_real_no_aplica_en_i1`.
2. **1 ambiental atribuible a la evidencia V3** (no al código de esta intervención):
   `test_processor_shipment_ad89.test_t6_idempotencia` busca globalmente
   `origin like 'Envío a procesador'` y el picking de **evidencia V3 7973**
   (`Envío a procesador: V3 Planta (temp)`, committed) colisiona (2 en lugar de 1).
   **No** se modificó el test ajeno ni se borró el registro de evidencia.

**Suites afectadas verdes:** `TestProcessorReturnLink`, `TestSvImputationI2`,
`TestSvImputationCandidates`, `TestServiceReturnImputationGuard`, `TestServiceReturnPendingFilter`.

**No ejecutado (fuera de alcance):** navegador real (V3 *pixel*); concurrencia real; base limpia;
Bloque **D** cuantitativo.

---

## 16. Operación manual de asignaciones centrada en SV (2026-10-10) — T-MAN

Suite nueva `madenat_lumber_logistics/tests/test_sv_imputation_manual.py` (**T-MAN-01..12**),
100 % transaccional. Cubre los bloques A–G de `CANON/19` §19.14:

| Prueba | Cubre |
|---|---|
| T-MAN-01 | Contexto SV: `default_get` fija `sv_lot_id` y **no** auto-incluye guía/líneas |
| T-MAN-02 | Selección explícita: sin selección «Proponer FIFO» falla; «Seleccionar todas»/«Quitar» |
| T-MAN-03 | Selección de **subconjunto**: aplica sólo la etiqueta marcada |
| T-MAN-04 | Reapertura (default_get → create): conserva selección y reparto; no duplica |
| T-MAN-05 | Criterio de aceptación: **dos guías, un SV** mediante dos documentos |
| T-MAN-06 | Integridad etiqueta–guía (D10): etiqueta ajena rechazada por ORM |
| T-MAN-07 | Reparto > nominal rechazado; varias líneas no lo eluden |
| T-MAN-08 | Reparto **parcial** admitido (D11) |
| T-MAN-09 | Edición del nominal no elude la capacidad; techo duro de lote conservado |
| T-MAN-10 | Documento multi-SV: reabrir desde un SV no pierde el reparto a otros SV |
| T-MAN-11 | Sin efecto en `stock.quant`/`stock.move` ni en el ledger `madenat.sv.operation` |
| T-MAN-12 | Reapertura por `onchange` (guía con imputación de trabajo) reproduce el borrador |

**Resultado de la suite dirigida:** `0 failed, 0 error(s) of 12 tests`.

**Regresión de módulo (corrida nueva):** `madenat_lumber_logistics` =
**`4 failed, 0 error(s) of 286 tests`**. Las **4 fallas** son las **mismas preexistentes/ambientales**
documentadas en §15.6 (aserción global `deviation` sobre eventos históricos
19889/19941/20342/20381/21739, 2026-10-04/05/07) ⇒ **0 fallas nuevas, 0 errores**. **No** se
modificó ningún test existente ni se borró evidencia (la nueva suite pasó sin adaptar los tests
previos del asistente, porque la inclusión explícita convive con el reparto creado por ORM).

**Integración web/RPC (no V3, no sustituye al navegador):** sesión autenticada de Operaciones;
menú **«Asignaciones SV»** visible; `default_get` del asistente con `active_model='stock.lot'`
devuelve `sv_lot_id`. **V3 *pixel* pendiente** (guion manual en
`FASES/IMPL_ASSIGN_SV_20261010_165247/docs/GUION_MANUAL_NAVEGADOR.md`).

**No ejecutado (fuera de alcance):** navegador real (V3); concurrencia real; base limpia; Bloque D.

---

## 17. Unificación de acceso «Rebaja de etiquetas» (NAV-01..12, 2026-10-10)

Suite nueva `tests/test_sv_rebaja_navigation.py` (`TestSvRebajaNavigation`). Datos **100 %
transaccionales** (`TransactionCase`, rollback); no crea ni borra datos. Los casos **NAV-01..05, 10,
11, 12** verifican **metadatos** (menús/acciones/vistas vía ORM); **NAV-06..09** verifican
comportamiento reutilizando el asistente/modelo existentes.

| Caso | Verifica |
| --- | --- |
| NAV-01 | Sólo un enlace operativo visible «Rebaja de etiquetas» en Logística Exportación |
| NAV-02 | «Asignaciones SV» e «Imputaciones documentales SV» no son accesos paralelos |
| NAV-03 | El enlace abre el listado SV existente (`stock.lot`, volumen) — no un modelo nuevo |
| NAV-04 | Desde un SV se accede a sus documentos de imputación |
| NAV-05 | El historial completo sigue disponible dentro del recorrido |
| NAV-06 | Consultar/navegar no crea documentos ni altera saldos |
| NAV-07 | Registrar usa el asistente y modelo existentes |
| NAV-08 | Guardar y reabrir conserva selección y reparto |
| NAV-09 | Aplicar/reversar mantienen permisos (Operaciones no reversa) |
| NAV-10 | El menú retirado no se reactiva (estado resultante acreditado en test; 2.ª `-u` fuera del test) |
| NAV-11 | «Rebajar por Motonave» y «Consolidación» no cambian |
| NAV-12 | La ingesta no recibe nuevas pantallas ni pasos |

**Resultado dirigido (corrida nueva):** `0 failed, 0 error(s) of 11 tests`.

**Regresión de módulo (corrida nueva):** `madenat_lumber_logistics` = **`4 failed, 0 error(s) of 298
tests`**. Las **4 fallas** son **exactamente** las mismas preexistentes/ambientales de
`test_processor_locations.test_09_auditoria_envio_normal` y
`test_processor_shipment_ad89.test_t1/t5/t6` (aserción global `deviation` sobre eventos históricos
19889/19941/20342/20381/21739 + idempotencia de pickings), ya presentes en la línea base 18.0.1.9.0
⇒ **0 fallas nuevas, 0 errores**.

**Actualización en desarrollo:** `odoo --database=madenat_test --update=madenat_lumber_logistics
--stop-after-init --no-http --log-level=info` (sin `-u all`), **exit 0**; ejecutada **dos veces**
para acreditar NAV-10 (el menú retirado **no** reaparece). Metadatos reales: `ir.ui.menu` 545 activo
«Rebaja de etiquetas»; 542 inactivo «Imputaciones documentales SV»; acción 867 preservada
(«Historial de rebajas»).

**Diferencia XML/metadatos/RPC vs. navegador.** La verificación es de **XML/carga de módulo**,
**metadatos ORM/SQL** y **pruebas transaccionales**; **no** hay navegador real
(Playwright/Selenium/Chromium) en el entorno ⇒ **V3 *pixel* pendiente** y **no** se sustituye por lo
anterior.

<!-- actualizado: 2026-10-10 (7) — §17 NAV-01..12 unificación «Rebaja de etiquetas»: dirigidas 11/11;
regresión 298 pruebas, 4 fallas preexistentes, 0 errores; 2.ª `-u` sin reaparición del menú. Versión
03 6.20.0 → 6.21.0. Sin commit/push. -->

---

## 18. Operación y blindaje «Rebaja de etiquetas» (RET/UX/VOL/SEC/REV/PHY/CON, 2026-10-10)

Suite nueva `tests/test_sv_rebaja_operativa.py` (`TestSvRebajaOperativa`). Datos **100 %
transaccionales** (`TransactionCase`, rollback).

| Caso | Verifica |
| --- | --- |
| RET-01 | El dominio canónico y el dominio del campo del asistente sólo admiten `yes` (y no cancelada) |
| RET-02 | Guías No/vacía/cancelada no son candidatas |
| RET-03 | Selección forzada por ORM rechazada y **sin crear documento** |
| RET-04 | Históricos siguen consultables tras dejar de ser candidatos |
| UX-01 | Búsqueda por número de guía encuentra el retorno |
| UX-02 | Búsqueda por etiqueta (interna y `external_labels`) |
| UX-03 | Seleccionar guía **no** incluye etiquetas automáticamente |
| UX-04 | Seleccionar todas / subconjunto |
| UX-05 | Guardar y reabrir conserva selección y reparto |
| VOL-01 | Semántica nominal/aplicado/reservado/disponible |
| VOL-02 | El documento en curso no se cuenta dos veces |
| VOL-03 | Reparto parcial permitido |
| VOL-04 | Exceso contra la capacidad equivalente rechazado |
| VOL-05 | Varios documentos no eluden el techo duro |
| VOL-06 | Repartos N:M no duplican totales |
| SEC-01 | Permisos (Operaciones aplica; sin grupo → AccessError) y compañía |
| SEC-02 | Aplicación inválida sin estado parcial (guía no elegible entre preparar y aplicar) |
| REV-01 | Reversa conserva historia y restituye el saldo documental |
| PHY-01 | Sin movimientos de stock, `sv_available_m3` intacto, sin ledger `imputacion` |
| CON-01 | Advisory lock de la etiqueta serializa la aplicación (otra sesión) |

**Resultado dirigido (corrida nueva):** `0 failed, 0 error(s) of 20 tests`.

**Regresión de módulo (corrida nueva):** `madenat_lumber_logistics` = **`4 failed, 0 error(s) of 318
tests`**. Las **4 fallas** son **las mismas** preexistentes/ambientales
(`test_processor_locations.test_09`, `test_processor_shipment_ad89.test_t1/t5/t6`) ⇒ **0 fallas
nuevas, 0 errores**.

**Actualización en desarrollo:** `odoo --database=madenat_test --update=madenat_lumber_logistics
--stop-after-init --no-http --log-level=info`, **exit 0** (sin `-u all`). **Diferencia XML/metadatos
vs. navegador:** verificación por XML/ORM/SQL y pruebas; **V3 *pixel* pendiente**.

<!-- actualizado: 2026-10-10 (8) — §18 RET/UX/VOL/SEC/REV/PHY/CON: dirigidas 20/20; regresión 318
pruebas, 4 fallas preexistentes, 0 errores. Versión 03 6.21.0 → 6.22.0. Sin commit/push. -->

---

## 19. Corrección de «Seleccionar todas» y asignación explícita (ERR/ASG/…, 2026-10-10)

Suite nueva `tests/test_sv_rebaja_seleccion_asignacion.py`
(`TestSvRebajaSeleccionAsignacion`). Datos **100 % transaccionales** (rollback). Los casos **ERR**
usan el **ciclo de formulario** (apertura → elección de guía → acción), no sólo registros
pre-persistidos.

| Caso | Verifica |
| --- | --- |
| ERR-01 | La vista fuerza el envío del identificador (`processed_lot_id` con `force_save="1"`) |
| ERR-02 | Apertura nueva → elegir guía → «Seleccionar todas» (sin guardar antes) conserva el id |
| ERR-03 | Guardar, reabrir y «Seleccionar todas» |
| ERR-04 | Cambiar la selección no pierde `processed_lot_id` |
| ASG-01 | «Asignar seleccionadas» crea filas (volumen 0) y «Usar disponible» las completa |
| ASG-02 | Sin selección → rechazo comprensible |
| ASG-03 | Sin cantidad válida → preparación incompleta clara y sin documento |
| ASG-04 | Repetir «Asignar» no duplica filas |
| ASG-05 | Se conserva el reparto a otros SV |
| ASG-06 | Asignar no aplica ni altera saldos aplicados |
| VOL-01 | Caso parcial: nominal 5, SV 3 → pendiente 2; totales lado etiqueta (5) y lado SV (3) |
| VOL-02 | Exceso contra el nominal comprometido rechazado |
| PER-01 | Guardar/reabrir conserva selección, cantidades y reparto |
| SEC-01 | Dominio canónico, elegibilidad forzada por ORM rechazada sin documento |
| SEC-02 | Sin permiso no aplica (AccessError) |
| PHY-01 | Sin movimientos de stock ni cambio en `sv_available_m3` |

**Resultado dirigido (corrida nueva):** `0 failed, 0 error(s) of 16 tests`.

**Regresión de módulo (corrida nueva):** `madenat_lumber_logistics` = **`4 failed, 0 error(s) of 334
tests`** — las **4 fallas** son las mismas preexistentes (`test_processor_locations.test_09`,
`test_processor_shipment_ad89.test_t1/t5/t6`) ⇒ **0 nuevas, 0 errores**.

**Límite de navegador:** causa y corrección se verifican por **fuente del cliente** (`record.js`) +
**arch de la vista** + **ciclo de formulario** ORM; **V3 *pixel* pendiente**.

<!-- actualizado: 2026-10-10 (9) — §19 ERR/ASG/VOL/PER/SEC/PHY: dirigidas 16/16; regresión 334
pruebas, 4 fallas preexistentes, 0 errores. Versión 03 6.22.0 → 6.23.0. Sin commit/push. -->

---

## 20. Rediseño operativo del asistente «Registrar rebaja» (MAP/GRAN/SEM/AMT/ARCH, 2026-10-10)

Suite nueva `tests/test_sv_rebaja_material.py` (`TestSvRebajaMaterial`). Datos **100 % transaccionales**.

| Caso | Verifica |
| --- | --- |
| MAP-01 | Etiqueta (`ref`), SKU origen, dimensiones, piezas y volumen del material |
| MAP-02 | Etiqueta repetida ⇒ **lotes distintos**, sin deduplicar |
| MAP-03 | Sin línea de packing ⇒ SKU/declaradas vacías (ausencia honesta), datos del lote presentes |
| MAP-04 | El volumen documental **no** se recalcula desde dimensiones |
| GRAN-01 | Disponibilidad por lote, **sin doble conteo** (2 lotes × 5 = 10) |
| SEM-01 | «Cantidad preparada» = 3 y «Pendiente de reparto» = 2 (nominal 5) |
| AMT-01 | Cantidad cero/negativa rechazada; exceso > nominal rechazado |
| ARCH-01 | Formulario amplio (`o_xxl_form_view`) y `target=current` del mismo action |

**Resultado dirigido (corrida nueva):** `0 failed, 0 error(s) of 8 tests`.

**Regresión de módulo (corrida nueva):** `madenat_lumber_logistics` = **`4 failed, 0 error(s) of 342
tests`** — las **4 fallas** son las mismas preexistentes (`test_processor_locations.test_09`,
`test_processor_shipment_ad89.test_t1/t5/t6`) ⇒ **0 nuevas, 0 errores**.

**Mapeo real (solo lectura, guía 19827):** 17 lotes → 17 líneas de packing, **17/17** coincidencias
(etiqueta/SKU/dimensiones/piezas/volumen), incluidas etiquetas repetidas (D7670, D7717, D7719, D7720,
D7721) con distinto largo. **V3 *pixel* pendiente** (interfaz rechazada por Mauricio; rediseño
operativo entregado para nueva revisión).

<!-- actualizado: 2026-10-10 (10) — §20 MAP/GRAN/SEM/AMT/ARCH: dirigidas 8/8; regresión 342 pruebas,
4 fallas preexistentes, 0 errores. Versión 03 6.23.0 → 6.24.0. Sin commit/push. -->

## 21. Interfaz clara y concisa del asistente «Registrar rebaja» (CAB/EDIT/MED/ETQ/SIN/USE/MULTI/ARCH, 2026-10-10)

Suite nueva `test_sv_rebaja_ui_limpia.py` (13 casos). Datos 100 % transaccionales.

| Caso | Verifica |
| --- | --- |
| CAB-01 | Seleccionadas ≠ con reparto preparado ≠ total; totales de origen con unidad |
| EDIT-01 | «A asignar» editable crea/actualiza la fila del SV de trabajo |
| EDIT-02 | Volumen 0 elimina SÓLO la fila del SV de trabajo; conserva otros SV |
| MED-01 | Medidas legibles «45 × 125 mm · 2,900 m» |
| ETQ-01/02 | Etiqueta limpia (packing), no el nombre concatenado; fallback a `ref` |
| ETQ-03 | Etiqueta repetida distinguida por medidas (sin deduplicar) |
| SIN-01 | Causa real del cero: Disponible/Aplicado/Reservado/Sin capacidad |
| SIN-02 | «Seleccionar todas» informa cuántas no son asignables |
| USE-01 | «Usar disponible» no sobrescribe cantidad editada |
| MULTI-01 | `multi_sv`; subtotal del SV de trabajo ≠ total general |
| ARCH-01/02 | Columnas/botones/textos; saldo del SV no repetido por fila |

**Resultado dirigido (corrida nueva):** `0 failed, 0 error(s) of 13 tests`.

**Regresión de módulo (corrida nueva):** `madenat_lumber_logistics` = **`4 failed, 0 error(s) of 355
tests`** — las 4 fallas son las mismas preexistentes (`test_processor_locations.test_09`,
`test_processor_shipment_ad89.test_t1/t5/t6`) ⇒ **0 nuevas, 0 errores**.

**V3 *pixel* pendiente** (sin navegador en el entorno).

<!-- actualizado: 2026-10-10 (11) — §21 CAB/EDIT/MED/ETQ/SIN/USE/MULTI/ARCH: dirigidas 13/13; regresión
355 pruebas, 4 fallas preexistentes, 0 errores. Versión 03 6.24.0 → 6.25.0. Sin commit/push. -->


## 22. HOTFIX OwlError de «Registrar rebaja» — `column_invisible` fuera de contexto (OWL, 2026-10-10)

Suite `test_sv_rebaja_ui_limpia.py::TestSvRebajaOwlColumnInvisible` (7 casos). Datos 100 % transaccionales.

| Caso | Verifica |
| --- | --- |
| OWL-01 | La vista efectiva: ningún `column_invisible` referencia `wizard_id` |
| OWL-02 | El formulario padre carga `<field name="multi_sv" invisible="1"/>` |
| OWL-03 (A) | Apertura sin líneas de reparto → `multi_sv` False (columna oculta) |
| OWL-04 (B) | Reparto sólo al SV de trabajo → `multi_sv` False |
| OWL-05 (C) | Reparto a varios SV → `multi_sv` True con destinos correctos |
| OWL-06 (D) | 1 SV → varios → 1 SV: visibilidad y reparto se conservan |
| OWL-07 (E) | Guardar/reabrir conserva datos y visibilidad (`multi_sv`) |

---

## 23. Auditoría integral y blindaje del ciclo de rebaja de etiquetas (AUD-ETQ-01..05, 2026-10-11)

**Suite nueva:** `madenat_lumber_logistics/tests/test_sv_rebaja_blindaje.py` (7 pruebas).

| ID | Acredita |
| --- | --- |
| AUD-ETQ-01 | `applied` **no** vuelve a draft/pending/cancelled por `write`; `applied→reversed` sólo por `action_reverse` (con usuario) |
| AUD-ETQ-02 | `action_reverse` exige motivo; audita `imputation_reverse`; reversa repetida no duplica |
| AUD-ETQ-03 | colisión del mapa lote↔packing ⇒ asociación vacía (no elige arbitrariamente); mapa normal sigue |
| AUD-ETQ-04 / 04b | causa concreta del saldo (`disponibilidad_detalle`), documentos (`disponibilidad_imputacion_ids`) y acciones de acceso; casos aplicado/reservado/sin-capacidad; nota concreta con el nombre del documento |
| AUD-ETQ-05 / 05b | cancelar borrador libera la reserva; repetir no altera; una aplicada no se anula |

**Comandos y resultados (base `madenat_test`, contenedor `odoo18_app`):**
```
odoo -d madenat_test -u madenat_lumber_logistics --test-enable --stop-after-init --no-http \
     --http-port=8071 --test-tags /madenat_lumber_logistics:TestSvRebajaBlindaje
# → 0 failed, 0 error(s) of 7 tests  (EXIT=0)

odoo -d madenat_test -u madenat_lumber_logistics --test-enable --stop-after-init --no-http \
     --http-port=8071 --test-tags /madenat_lumber_logistics
# → 4 failed, 0 error(s) of 369 tests (EXIT=1)
#   las 4 fallas son las MISMAS preexistentes de test_processor_locations / test_processor_shipment_ad89
```
Evidencia: `AUDIT_REBAJA_ETIQUETAS_20261011/logs/{test_blindaje.log,regression.log}`.

**Ajuste de pruebas existentes:** motivo de reversa en los llamados a `action_reverse` de
`test_sv_imputation_i2`, `test_sv_imputation_candidates`, `test_service_return_imputation_guard`,
`test_processor_return_link`, `test_sv_rebaja_operativa` (política corregida, no cosmética).

**Límites:** sin navegador (renderización pendiente); concurrencia multi-cursor simultánea pendiente
(advisory locks probados reteniendo el lock); sin reparación histórica.

<!-- actualizado: 2026-10-11 (1) — §23 AUD-ETQ-01..05: dirigidas 7/7 en verde; regresión 369 pruebas,
4 fallas preexistentes, 0 errores. Versión 03 6.26.0 → 6.27.0. Sin commit/push. -->


**Resultado dirigido (corrida nueva):** `0 failed, 0 error(s) of 20 tests` (clase UI + clase OWL).

**Regresión de módulo (corrida nueva):** `madenat_lumber_logistics` = **`4 failed, 0 error(s) of 362
tests`** — las 4 fallas son las mismas preexistentes (`test_processor_locations.test_09`,
`test_processor_shipment_ad89.test_t1/t5/t6`) ⇒ **0 nuevas, 0 errores**.

**Límite:** la **renderización real** (eval de la expresión en el cliente Owl) queda **pendiente de
comprobación manual**: no hay navegador. El fallo **apareció** en la comprobación real del navegador y
**no** fue detectado por las validaciones XML/ORM previas.

<!-- actualizado: 2026-10-10 (12) — §22 HOTFIX OwlError de «Registrar rebaja»: casos A–E + invariantes
de arch; dirigidas 20/20; regresión 362 pruebas, 4 fallas preexistentes, 0 errores. Renderización real
pendiente (sin navegador). Versión 03 6.25.0 → 6.26.0. Sin commit/push. -->


---

## 24. Cierre probatorio del ciclo de rebaja de etiquetas (AUD-ETQ-06..10, 2026-10-11)

**Suite nueva:** `madenat_lumber_logistics/tests/test_sv_rebaja_cierre.py` (8 pruebas).

| ID | Acredita |
| --- | --- |
| AUD-ETQ-08 | inmutabilidad profunda: `write`/`unlink`/`create` sobre líneas y repartos de un aplicado y `unlink` del aplicado ⇒ `UserError` |
| AUD-ETQ-06 | reversa: motivo vacío/espacios ⇒ `UserError`; trazabilidad (usuario/fecha/motivo/auditoría); repetida sin doble efecto; sin permiso y contexto forzado ⇒ `AccessError` |
| AUD-ETQ-07 | multi-compañía sin `sudo`: usuario de otra compañía no ve/edita/aplica/reversa el documento ajeno; contexto no autoriza; lotes ajenos bloqueados |
| AUD-ETQ-09a | ciclo A: preparar→guardar→reabrir→cancelar(libera)→reasignar→aplicar (2 SV) |
| AUD-ETQ-09b | ciclo B: preparar→aplicar→revertir(restituye)→reasignar→aplicar; historia append-only |
| AUD-ETQ-10 | parcial 5/3: nominal comprometido; los 2 m³ no reutilizables; los libera anular/revertir |
| AUD-ETQ-09c | ciclos sin efectos físicos (stock.move/move.line/picking) |

**Concurrencia real (sonda externa, cursores independientes + `threading.Barrier`):**
`FASES/AUDIT_REBAJA_ETIQUETAS_20261011/` (artefacto `concurrency_probe.py` en `evidence/`, fuera de git) → Q1/Q2/Q3 OK, sin sobreconsumo, una sola
reversa, sin efectos físicos, 0 residuos. **RESULTADO GLOBAL: OK** (`logs_cierre/concurrency.log`).

**Comandos y resultados (base `madenat_test`, contenedor `odoo18_app`):**
```
odoo -d madenat_test -u madenat_lumber_logistics --test-enable --stop-after-init --no-http \
     --http-port=8071 --test-tags /madenat_lumber_logistics:TestSvRebajaCierre
# → 0 failed, 0 error(s) of 8 tests  (EXIT=0)

odoo -d madenat_test -u madenat_lumber_logistics --test-enable --stop-after-init --no-http \
     --http-port=8071 --test-tags /madenat_lumber_logistics
# → mismas 4 fallas preexistentes (test_processor_locations / test_processor_shipment_ad89)
```

**Límite:** renderización/navegador (V3) pendiente.

<!-- actualizado: 2026-10-11 (2) — §24 AUD-ETQ-06..10: dirigidas 8/8 en verde; concurrencia real OK;
regresión con las mismas 4 fallas preexistentes. Versión 03 6.27.0 → 6.28.0. Sin commit/push. -->


---

## 25. Contrato de aplicación — POL-01..08 (aprobado 2026-10-11)

**Política aprobada:** Aplicar exige ≥ 1 reparto válido con cantidad positiva hacia un SV autorizado; sin
reparto el documento sólo queda **no aplicado**; el parcial mantiene el compromiso nominal con **pendiente
explícito**. `NO_SV_CANDIDATE` pasa a **informativo** (no excepción de aplicación).

**Suite nueva:** `madenat_lumber_logistics/tests/test_sv_rebaja_contrato.py` (8 pruebas).

| ID | Acredita |
| --- | --- |
| POL-01 | sin filas de reparto ⇒ `UserError`; estado `draft`; sin snapshot; capacidad intacta |
| POL-02 | fila con cantidad 0 ⇒ `ValidationError`; sin reparto ⇒ aplicación rechazada |
| POL-03 | reparto positivo válido ⇒ `applied` |
| POL-04 | parcial 5/3 ⇒ `nominal_total=5`, `imputed_total=3`, `etiqueta_pendiente_m3=2`, disponible 0 |
| POL-05 | guardar/reabrir incompleto ⇒ `draft` conservado, sin reparto, sin aplicación |
| POL-06 | ORM/RPC directo sin reparto ⇒ mismo rechazo |
| POL-07 | repetición tras rechazo ⇒ sin documento parcial, sin consumo extra |
| POL-08 | aplicar→revertir→reasignar→aplicar con balances e historia |

**Pruebas actualizadas (conducta anterior):** `test_sv_imputation_i2.T-I2-06`,
`test_sv_imputation_candidates.CAND-07/08/09` — antes aplicaban sin reparto con motivo; ahora **exigen
rechazo** y estado no aplicado (política aprobada). No se alteró ninguna otra aserción.

**Comandos y resultados (base `madenat_test`):**
```
odoo -d madenat_test -u madenat_lumber_logistics --test-enable --stop-after-init --no-http \
     --http-port=8071 --test-tags /madenat_lumber_logistics:TestSvRebajaContratoAplicacion
# → 0 failed, 0 error(s) of 8 tests  (EXIT=0)

odoo -d madenat_test -u madenat_lumber_logistics --test-enable --stop-after-init --no-http \
     --http-port=8071 --test-tags /madenat_lumber_logistics
# → 4 failed, 0 error(s) of 385 tests  (mismas 4 preexistentes)
```
Evidencia: `FASES/CONTRATO_APLICACION_20261011/` (artefacto `logs_pol.log`, fuera de git), `logs_regression.log`.

**Límite:** aceptación en navegador pendiente (guion A–I).

<!-- actualizado: 2026-10-11 (3) — §25 contrato de aplicación: POL-01..08 en verde (8/8); regresión 385
pruebas con las mismas 4 fallas preexistentes; 4 pruebas previas actualizadas a la política aprobada.
Versión 03 6.28.0 → 6.29.0. Sin commit/push. -->


---

## 26. Persistencia y recuperación del trabajo de rebaja (SAVE/FLOW/PHY, 2026-10-11)

**Incidencia:** «al preparar las asignaciones, estas no van quedando guardadas».
**Causa demostrada:** «Preparar asignación» crea filas de reparto a **cantidad 0** y «Guardar borrador»
(`_i2_build_imputation`) **lanzaba `UserError`** ante cualquier fila a 0 ⇒ no se guardaba el documento
(reproducido: `REPRO-02`). Además (C2): un borrador sin reparto positivo no era localizable desde el SV.

**Suite nueva:** `madenat_lumber_logistics/tests/test_sv_rebaja_persistencia.py` (18 pruebas).

| ID | Acredita |
| --- | --- |
| SAVE-01..05 | preparar+cantidad→guardar persistente; localizar desde SV y reabrir; actualizar sin duplicar; guardar dos veces; **cero no bloquea** el guardado |
| SAVE-06..09 | dos SV; cero sólo en el SV de trabajo; descartar cambios; limpieza del transitorio |
| SAVE-10..14 | atomicidad ante fallo; permisos/compañía sin `sudo`; dos sesiones sin duplicar; aplicado no reabrible; firma sin colisión |
| FLOW-01..03 | guardar→reabrir→aplicar; cancelar (reservas); aplicar→revertir→reasignar→guardar→reabrir→aplicar |
| PHY-01 | guardar/recuperar sin efectos físicos |

**Pruebas existentes actualizadas (conducta anterior):**
`test_sv_rebaja_material.test_amt_01` (cero ya no bloquea; negativo sí),
`test_sv_rebaja_navigation.test_nav_04_05` (dominio del historial incluye `work_sv_lot_id`),
`test_sv_rebaja_seleccion_asignacion.test_asg_03` (guardar sin cantidad no falla; queda borrador).

**Comandos y resultados (base `madenat_test`):**
```
odoo -d madenat_test -u madenat_lumber_logistics --test-enable --stop-after-init --no-http \
     --http-port=8071 --test-tags /madenat_lumber_logistics:TestSvRebajaPersistencia
# → 0 failed, 0 error(s) of 18 tests  (EXIT=0)

odoo -d madenat_test -u madenat_lumber_logistics --test-enable --stop-after-init --no-http \
     --http-port=8071 --test-tags /madenat_lumber_logistics
# → mismas 4 fallas preexistentes (test_processor_locations / test_processor_shipment_ad89)
```
Evidencia: `SAVE_REBAJA_20261011/logs/{repro.log,save.log,regression.log}`.

**Límite:** aceptación en navegador pendiente (guion A–I). Política de conflicto de dos sesiones de
borrador: **última escritura gana** (sin bloqueo optimista; cambio requeriría autorización).

<!-- actualizado: 2026-10-11 (4) — §26 persistencia/recuperación (SAVE-01..14, FLOW-01..03, PHY-01);
dirigidas 18/18; regresión con las mismas 4 fallas preexistentes; 3 pruebas previas actualizadas.
Versión 03 6.29.0 → 6.30.0. Sin commit/push. -->


---

## 27. Acciones visibles del asistente «Registrar rebaja» (UI-01..05, 2026-10-11)

**Causa:** el asistente (formulario amplio, `target="current"`) tenía sus acciones **sólo** en un
`<footer>`, que Odoo **no renderiza** fuera de un diálogo ⇒ «Guardar borrador» / «Revisar y aplicar» /
«Descartar» **invisibles**. Evidencia del arch efectivo (vista 2889): `<header>` ausente, `<footer>`
presente, `target=current`. **Corrección:** acciones en el **`<header>` nativo** + `<footer>` retirado.

**Suite nueva:** `tests/test_sv_rebaja_ui_acciones.py`.

| ID | Acredita |
| --- | --- |
| UI-01 | la entrada (SV → Registrar rebaja) abre la vista correcta (`res_model`, `view_mode`, `target`, `view_id`) |
| UI-02 | acciones en `<header>` y **sin** `<footer>`; `groups=` en «Revisar y aplicar»; `invisible` por estado |
| UI-03 | los botones llaman a **métodos de negocio**: guardar crea el documento persistente; Abrir documento lo abre; Descartar y volver regresa al SV sin borrarlo |
| UI-04/05 | visibilidad coherente; sin expresiones de fila/`wizard_id`/`parent.` (proxy de OwlError) |
| CONF | confirmación con **referencia real y estado**; `action_open_document` exige documento |

**Comandos y resultados (base `madenat_test`):**
```
odoo -d madenat_test -u madenat_lumber_logistics --test-enable --stop-after-init --no-http \
     --http-port=8071 --test-tags /madenat_lumber_logistics
# → mismas 4 fallas preexistentes (test_processor_locations / test_processor_shipment_ad89)
```
Evidencia: `FASES/UI_SAVE_REBAJA_20261011/` (artefacto `regression.log` en `logs/`, fuera de git).

**Límite:** evidencia de navegador pendiente (guion `docs/GUION_NAVEGADOR_UI.md`); no se declara
«verificado en pantalla».

<!-- actualizado: 2026-10-11 (5) — §27 acciones del asistente en `<header>`; UI-01..05 + confirmación.
Versión 03 6.30.0 → 6.31.0. Sin commit/push. -->


---

## 28. Simplificación operativa: recorrido de dos acciones (SIMPLE/CLIENT, 2026-10-11)

**Solicitud:** «sólo aplicar o guardar lo seleccionado; no obligar a abrir el documento».

**Suite nueva:** `tests/test_sv_rebaja_simple.py` (17 + CLIENT).

| ID | Acredita |
| --- | --- |
| SIMPLE-01 | botonera de dos acciones en `<header>` (Guardar/Aplicar) + Volver; sin `<footer>` |
| SIMPLE-02 | seleccionar → m³ (inverse) → **Aplicar sin Guardar ni Preparar**; una sola rebaja correcta |
| SIMPLE-03 | seleccionar → m³ → **Guardar**; documento persistente, no aplicado, misma ventana |
| SIMPLE-04 | Guardar → salir → Continuar; datos y referencia recuperados |
| SIMPLE-05 | borrador → **Aplicar desde el asistente** (sin Abrir documento) |
| SIMPLE-06/07 | repetir Guardar/Aplicar no duplica ni consume dos veces |
| SIMPLE-08/09 | cero permite Guardar (no Aplicar); negativo/exceso rechazados sin efectos |
| SIMPLE-10 | etiquetas sin disponibilidad → mensaje concreto |
| SIMPLE-11/12 | repartos a otros SV conservados; «Usar disponible» no sobrescribe |
| SIMPLE-13/14 | descartar conserva el último guardado; tras aplicar, resultado y sólo lectura |
| SIMPLE-15 | permisos y compañía rechazados en backend (sin `sudo`) |
| SIMPLE-16 | aplicar → revertir → nueva asignación → aplicar (historia) |
| SIMPLE-17 | sin efectos físicos |
| CLIENT-01/02/03 | cantidad editada llega al reparto; acciones visibles en `target=current`; sin expresiones fuera de contexto |

**Comandos y resultados (base `madenat_test`):**
```
odoo -d madenat_test -u madenat_lumber_logistics --test-enable --stop-after-init --no-http \
     --http-port=8071 --test-tags /madenat_lumber_logistics
# → mismas 4 fallas preexistentes (test_processor_locations / test_processor_shipment_ad89)
```
Evidencia: `FASES/SIMPLE_REBAJA_20261011/` (artefacto `regression.log` en `logs/`, fuera de git).

**Límite:** evidencia de navegador pendiente (guion `docs/GUION_NAVEGADOR_SIMPLE.md`).

<!-- actualizado: 2026-10-11 (6) — §28 recorrido simplificado Guardar/Aplicar; SIMPLE-01..17 + CLIENT.
Versión 03 6.31.0 → 6.32.0. Sin commit/push. -->


---

## 29. Volver a borrador y reasignar (RESET, 2026-10-11)

**Suite nueva:** `tests/test_sv_rebaja_reset.py` (RESET-01..15, 18 + PHY-01).

| ID | Acredita |
| --- | --- |
| RESET-01/03 | draft → anular → reabrir: misma referencia y `documentary_key`; auditoría cancel+reopen; reserva restablecida |
| RESET-02 | pending → anular → reabrir con reservas correctas |
| RESET-04 | repetir reapertura no duplica auditoría ni reserva |
| RESET-05 | capacidad consumida por otro documento ⇒ rechazo; A sigue cancelado y B aplicado intacto |
| RESET-06 | otro trabajo activo de la guía ⇒ conflicto claro sin sobrescritura |
| RESET-07/10 | permisos/compañía rechazados (sin `sudo`); motivo vacío/espacios rechazado |
| RESET-08 | `write({'state':'draft'})` directo **no** elude la transición (ni con contexto forzado) |
| RESET-09 | `applied`/`reversed` **no** vuelven a borrador |
| RESET-11 | asistente abierto + cancelación externa ⇒ mensaje operativo y salida «Volver a borrador» |
| RESET-12/13 | reabrir → corregir → Guardar → Continuar; reabrir → reasignar → Aplicar |
| RESET-14/18 | varios SV conservados; nueva apertura no reutiliza el cancelado |
| RESET-15 | fallo intermedio (guía no elegible) ⇒ atomicidad |
| RESET-16/17 | **concurrencia REAL** (transacciones independientes): dos reaperturas del mismo anulado y reapertura ∥ consumo de la misma capacidad (SV) ⇒ una sola transición, sin sobreconsumo, sin doble reserva ni doble auditoría; rollback de la perdedora. `test_sv_rebaja_reset_concurrency.py` (2026-10-12) |
| AUD-ETQ-07 | `write` directo (incl. `reopened_by_id`+motivo+fecha+contexto) **RECHAZADO**: exige la acción controlada (token de proceso) |
| AUD-ETQ-08 | computes `sv_assignment_*` (`store`/`compute_sudo` coherentes, **sin sudo**) y consola de intake sin proxy virtual no buscable |
| P1 (AUD-ETQ-11) | concurrencia sobre la **misma etiqueta retornada**: A/B cancelados (6 m³ c/u, lote 10) → advisory lock rechaza a la perdedora; revalidación de capacidad tras el bloqueo. `test_sv_rebaja_reset_lot_capacity.py` |
| P2 (AUD-ETQ-08) | recomputación REAL de la consola de intake en el **MISMO** entorno y en **transacción nueva** tras create/write/unlink del detalle. `test_intake_metrics_recompute.py` |
| P3 (AUD-ETQ-10) | saldo almacenado **canónico** (`compute_sudo=True`) independiente del usuario; proyección por usuario; sin AccessError ni exposición entre compañías. `test_sv_assignment_user_rights.py` |
| P4 / TOK-01..09 | vía privada de transición; sin residual, sin autorización cruzada, identidad del entorno, sin estado compartido. `test_sv_rebaja_reset_token.py` |
| LOCK-01..19 | **sobrescritura concurrente**: `edit_version` + guard del documento (advisory ns 1 + comparación + flush) rechaza la edición obsoleta en Guardar/Aplicar; líneas/repartos y edición directa invalidan; «Recargar versión actual»; sin adopción silenciosa. `test_sv_rebaja_save_lock.py` |
| FLOW-01..03 / PHY-01 | recorrido sencillo, Aplicar sin Guardar previo, multi-SV conserva destinos, sin movimientos físicos |
| V1 / C1–C8 | **edición directa**: `force_save` de `edit_version` + guard atómico en `write()` ⇒ rechazo de la edición obsoleta en los 8 cruces (asistente↔asistente, directo↔asistente, form↔form, línea→padre, directo→aplicar, asistente→estado, transición→contenido). `test_sv_rebaja_save_lock_direct.py` |
| V3 / TX-01..13 | **transacción y bloqueos**: rollback íntegro, cursor utilizable, sin reintento automático, sin auditoría de transición fallida, rechazo por VERSIÓN (lock libre) y por LOCK (ocupado), orden `1→2→3` sin deadlock. `test_sv_rebaja_save_lock_tx.py` |
| PHY-01 | sin efectos físicos en todo el ciclo (anular→reabrir→aplicar) |
| ~~RESET-16/17~~ | **SUPERADO** (2026-10-12): concurrencia real acreditada — ver filas RESET-16/17 |

**Comandos y resultados (base `madenat_test`):**
```
odoo -d madenat_test -u madenat_lumber_core,madenat_lumber_logistics --test-enable --stop-after-init \
     --no-http --http-port=8071 --test-tags /madenat_lumber_logistics
# → mismas 4 fallas preexistentes (test_processor_locations / test_processor_shipment_ad89)
```
Evidencia: `RESET_REBAJA_20261011/logs/{reset.log,regression.log}`.

<!-- actualizado: 2026-10-11 (7) — §29 RESET: transición cancelled → draft; 14 pruebas + regresión con las
mismas 4 fallas preexistentes; concurrencia RESET-16/17 pendiente. Versión 03 6.32.0 → 6.33.0. -->

<!-- actualizado: 2026-10-12 (1) — §29 RESET: **concurrencia RESET-16/17 acreditada** (transacciones
PostgreSQL independientes, advisory lock + revalidación, barrera/timeout; sin sobreconsumo, sin doble reserva
ni doble auditoría; limpieza test-only verificada) y **AUD-ETQ-07** (write directo rechazado: token de
proceso). Nuevas pruebas: `test_sv_rebaja_reset_concurrency.py` (RESET-16/17 + limpieza) y
`test_intake_console_compute_depends.py` (AUD-ETQ-08). Suites dirigidas ⇒ 0 failed / 0 error. Versión 03
6.33.0 → **6.34.0**. Sin commit/push. -->

<!-- actualizado: 2026-10-12 (2) — §29 RESET: **verificación probatoria P1–P4**. P1 `test_sv_rebaja_reset_lot_capacity.py`
(3), P2 `test_intake_metrics_recompute.py` (1), P3 `test_sv_assignment_user_rights.py` (2), P4
`test_sv_rebaja_reset_token.py` (7) ⇒ **0 failed / 0 error**. Versión 03 6.34.0 → **6.35.0**. Sin commit/push. -->

<!-- actualizado: 2026-10-12 (3) — §29+ **BLINDAJE DE BORRADORES (LOCK-01..19, FLOW, PHY)**. `edit_version` +
guard del documento (advisory ns 1 + comparación + flush); rechazo controlado de la edición obsoleta en Guardar
y Aplicar; «Recargar versión actual»; líneas/repartos y edición directa elevan la versión; LOCK-16 con
transacciones independientes (barrera). `test_sv_rebaja_save_lock.py` ⇒ **0 failed / 0 error**. Versión 03
6.35.0 → **6.36.0**. Sin commit/push. -->

## 30. HOTFIX OWL — «Agregar una línea» en el documento de rebaja (VIEW-01..05, 2026-10-12)

**Causa:** Odoo 18 CE ya no compila `div.oe_chatter` (compilador por selector de nodo ⇒ `<chatter/>`); los
campos del chatter (`message_ids`/`message_follower_ids` de `mail.thread`) quedaban como listas o2m editables
por defecto (`mail.message`/`mail.followers`) con «Agregar una línea» ⇒ `OwlError` en `get urlRelation`
(`res_id` = `many2one_reference` sin relación determinable). Ver `19` §19.33.

**Corrección:** `div.oe_chatter` → `<chatter/>` en `view_madenat_sv_imputation_form` y
`view_madenat_processor_return_link_form`. Módulo `madenat_lumber_logistics` 18.0.1.25.0 → **18.0.1.26.0**.

**Pruebas de servidor** (`tests/test_hotfix_owl_chatter.py`, `TestHotfixOwlChatter`):

```
--test-tags madenat_lumber_logistics:TestHotfixOwlChatter
# → 0 failed, 0 error(s) of 5 tests   (EXIT=0)
#   VIEW-01 (proxy) get_view resuelve form+chatter; VIEW-02/03/04 no hay campos de
#   chatter filtrados ni «Agregar una línea»; VIEW-05 arch efectivo sin many2one
#   sin relación (ni many2one_reference sin su model_field).
```

**Regresión:**

```
--test-tags madenat_lumber_logistics
# → 4 failed, 0 error(s) of 506 tests  (mismas 4 preexistentes; baseline 4/444 ⇒ 0 nuevas)

--update=madenat_lumber_core,madenat_lumber_intake,madenat_lumber_logistics \
  --test-tags madenat_lumber_core,madenat_lumber_intake,madenat_lumber_logistics
# → 6 failed, 4 error(s) of 1284 tests  (mismo conjunto que el baseline 6/1217 ⇒ 0 nuevas)
```

**Límite:** VIEW-01/02/03/04/06/07 en **cliente** (navegador) **PENDIENTES** (sin navegador; guion
`FASES/HOTFIX_OWL_CHATTER_OE_20261012/docs/GUION_MANUAL_NAVEGADOR.md`). Una validación XML/ORM **no** demuestra la
evaluación en Owl.

<!-- actualizado: 2026-10-12 (4) — §30 HOTFIX OWL chatter: VIEW 5/5; logistics 4/506 (0 nuevas);
core+intake+logistics 6/4 de 1284 (0 nuevas). Versión 03 6.37.0 → **6.38.0** (cabecera alineada: estaba
6.33.0, por debajo de 6.37.0 ya registrado por entregas previas). §30 es consecutiva (§29 → §30, sin
duplicado). Sin commit/push. -->

## 31. REGLA CANÓNICA DE ARNÉS DE REGRESIÓN: USO EXCLUSIVO DE -u (NUNCA -i) (AD-125 / M1)

**Regla de Oro de Ejecución de Regresiones:**
Todo arnés de pruebas automatizadas o regresión completa sobre bases de datos persistentes (`madenat_test`) debe ejecutarse exclusivamente con el flag `-u` (o `--update`) sobre la nómina explícita de módulos requeridos, o alternativamente con `--test-tags`. Queda **estrictamente prohibido el uso del flag `-i` (o `--init`)**.

### 31.1 Causa Técnica y Mecánica en el Core de Odoo 18 CE
El comportamiento de `-i` frente a `-u` está determinado en dos puntos críticos del cargador de Odoo:
1. `odoo/modules/loading.py:199-200`:
   ```python
   mode = 'update'
   if hasattr(package, 'init') or package.state == 'to install':
       mode = 'init'
   ```
   Cuando se pasa `-i`, el paquete entra en modo `init`. Cuando se pasa `-u`, permanece en modo `update`.
2. `odoo/tools/convert.py:347` y `447`:
   ```python
   if self.noupdate and self.mode != 'init':
       if record := env['ir.model.data']._load_xmlid(xid):
           self.idref[rec_id] = record.id
           return None
   ...
   record = model._load_records([data], self.mode == 'update')
   ```
   En modo `init` (`-i`), la condición `self.mode != 'init'` se evalúa como `False`, de modo que Odoo **ignora por diseño la directiva `noupdate="1"`** de los archivos XML de datos y procede a sobreescribir todos los registros (`ir.config_parameter`, configuraciones, semillas) con los valores literales del XML.
3. Consecuencia en Bloque 4K: La invocación de `run_reg_4k.sh` con `-i` forzó la recarga de `data/ingestion_config.xml`, sobreescribiendo el parámetro `madenat.out_of_table_behavior` de `'direct'` a `'warning'`.

### 31.2 Comando Canónico Oficial de Regresión
La suite completa de módulos para regresión comprende:
- `madenat_lumber_core`
- `madenat_lumber_intake`
- `madenat_lumber_logistics`
- `madenat_ingestion_engine`
- `madenat_lumber_purchasing`
- `madenat_lumber_costing`
- `madenat_lumber_billing`

**Comando canónico:**
```bash
docker exec odoo18_app odoo \
    -d madenat_test \
    -u madenat_lumber_core,madenat_lumber_intake,madenat_lumber_logistics,madenat_ingestion_engine,madenat_lumber_purchasing,madenat_lumber_costing,madenat_lumber_billing \
    --test-enable \
    --stop-after-init \
    --http-port=8079 > "$LOG_FILE" 2>&1
```

<!-- actualizado: 2026-10-18 — §31 REGLA CANÓNICA DE ARNÉS: prohibición estricta de -i; justificación técnica Odoo loading.py:199 y convert.py:347; fijación de comando oficial con -u y 7 módulos. Versión 03 6.38.0 → 6.39.0. Sin commit/push. -->

---

## 32. PRUEBAS DEL BLOQUE 5 — VOLUMEN REAL FÍSICO Y COMPARATIVO (AD-126)

Se incorporan 13 pruebas unitarias nuevas distribuidas en 3 suites especializadas en `madenat_lumber_core`, registradas en `tests/__init__.py`:

### 32.1 Suite 5A: `test_lumber_thickness_real_map_5a.py` (4 pruebas)
- `test_01_seed_records_exist_and_match_canonical`: Verifica que los registros semilla canónicos (4/4, 5/4, 6/4, 7/4, 8/4) existen con sus valores exactos en mm y `noupdate="1"`.
- `test_02_coherence_validation_success_and_failure`: Valida que el constraint de coherencia nominal $\le 0.001"$ acepte valores correctos y rechace discrepancias.
- `test_03_getter_resolution_and_anti_hardcode`: Verifica que `get_thickness_real_mm` resuelva desde BD dinámicamente y no desde constantes en código (D6).
- `test_04_security_access_rights`: Comprueba que usuarios de auditoría y base lean pero no editen, y que config manager mantenga CRUD.

### 32.2 Suite 5B: `test_vol_physical_real_5b.py` (5 pruebas)
- `test_01_canonical_vector_250_pieces`: Vector $38.1 \times 100 \times 4.05 \times 250 / 1.000.000 = 3.858\text{ m}^3$ con redondeo `r3()`.
- `test_02_canonical_vector_single_piece_comparison`: Vector de planilla ($45\text{ mm}$ rough, $4.0\text{ m}$, 1 pza, 6/4): Real físico $0.015\text{ m}^3$ frente a exportación $0.015\text{ m}^3$ y compra $0.018\text{ m}^3$.
- `test_03_blanks_direct_to_stock_no_physical_real`: Comprueba que Blanks directo a stock (`f5085`) asigna `vol_physical_real_m3 = 0.0`.
- `test_04_anti_hardcode_table_modification_changes_new_calculation`: Modificar la tabla en BD altera el cálculo de un registro nuevo.
- `test_05_stock_lot_vol_physical_real_computation`: Cálculo automático de `vol_physical_real_m3` en `stock.lot`.

### 32.3 Suite 5C / 5D: `test_volume_comparison_5c.py` (5 pruebas)
- `test_01_metrics_computation_and_percentages`: Cálculo de `% Dif.Vol` $((\text{Export} - \text{Compra}) / \text{Compra}) \times 100$.
- `test_02_resaltado_excepcion_exportacion_mayor_que_nominal`: Señal `is_export_greater_nominal = True` cuando exportación $>$ compra.
- `test_03_view_definitions_and_actions_load`: Carga exitosa de vistas lista (`list`), pivote (`pivot`), búsqueda (`search`) y acción readonly.
- `test_04_menu_permissions_and_hierarchy`: Comprueba existencia del menú bajo Control de Lotes y grupos de Operaciones, Auditoría y Contabilidad.
- `test_05_physical_status_and_empty_percentage_when_not_calculated` (5D): Verificación de campo `physical_status` (`calculado`, `sin_mapeo`, `no_aplica`) en lotes y líneas de guía, porcentaje `% Dif.Vol` vacío cuando el estado no es calculado, y preservación intacta de vectores previos.

**Total pruebas acumuladas esperadas:** 1.551 (previas) + 14 = **1.565 pruebas**.

### 32.4 Lista Nominal de Fallas Históricas de la Regresión (10 Pruebas Conocidas)
Se rectifica la atribución errónea "de costing": las 10 fallas preexistentes pertenecen a `madenat_lumber_core` (6 fallas) y `madenat_lumber_logistics` (4 fallas), documentadas desde fases previas:
1. `madenat_lumber_core`: `TestGuiaPickingLink.test_t_g2_03_exclusion_retornos` (FAIL)
2. `madenat_lumber_core`: `TestOrphanMoveCleanupSavepoint.test_partial_batch_failure_protected_moves_survive` (ERROR)
3. `madenat_lumber_core`: `TestSvConcurrency.test_01_dos_transacciones_no_sobreconsumen` (FAIL)
4. `madenat_lumber_core`: `TestSvEscalationSecurity.test_02_costo_exige_contabilidad` (ERROR)
5. `madenat_lumber_core`: `TestSvEscalationSecurity.test_03_alza_de_baseline_exige_auditoria` (ERROR)
6. `madenat_lumber_core`: `TestSvEscalationSecurity.test_04_auditoria_y_contabilidad_por_dos_personas` (ERROR)
7. `madenat_lumber_logistics`: `TestProcessorLocations.test_09_auditoria_envio_normal` (FAIL)
8. `madenat_lumber_logistics`: `TestProcessorShipmentAD89.test_t1_envio_manual_parcial_sin_motivo` (FAIL)
9. `madenat_lumber_logistics`: `TestProcessorShipmentAD89.test_t5_desviacion_real_no_aplica_en_i1` (FAIL)
10. `madenat_lumber_logistics`: `TestProcessorShipmentAD89.test_t6_idempotencia` (FAIL)

---

## 33. PRUEBAS DEL BLOQUE 6 — PATIOS, VISIBILIDAD, ETIQUETAS Y PACKING ESTÁNDAR (AD-127)

Se incorporan 26 pruebas unitarias nuevas distribuidas en `madenat_lumber_core`, `madenat_lumber_intake` y `madenat_ingestion_engine`, registradas en sus respectivos `tests/__init__.py`:

### 33.1 Script Canónico de Regresión de los 7 Módulos (A4 / AD-127)
- **Ruta Oficial:** `madenat_lumber_core/scripts/run_regression.sh`
- **Comportamiento:** Ejecuta `odoo` exclusivamente con el flag `-u` sobre los 7 módulos del núcleo (`madenat_lumber_core`, `madenat_lumber_intake`, `madenat_lumber_logistics`, `madenat_ingestion_engine`, `madenat_lumber_purchasing`, `madenat_lumber_costing`, `madenat_lumber_billing`), con `--test-enable`, `--stop-after-init` y `--http-port=8079`.
- **Registro:** Salida redirigida a archivo de log fechado con timestamp en `FASE12_REQUERIMIENTOS_OPERACIONES_20261017/logs/regresion_7_modulos_<TIMESTAMP>.log` y código de salida en archivo `.exit`.

### 33.2 Suite 6A / 6B (Patios e Inventario): `test_patios_f7.py` (10 pruebas en `madenat_lumber_core`)
- `test_01_patio_type_field_and_selection`: Campo `patio_type` (`service`, `port`) en `stock.location`.
- `test_02_resolve_patio_by_type_exact`: Resolución unívoca de patio por tipo sin nombres hardcodeados.
- `test_03_resolve_patio_by_type_warning_when_multiple`: Advertencia en log cuando existen múltiples patios activos del mismo tipo.
- `test_04_resolve_patio_by_type_none_when_empty`: Retorno None sin excepción cuando no hay patios configurados del tipo.
- `test_05_reception_port_auto_assignment`: Asignación automática a patio tipo `port` en recepciones marítimas/puerto.
- `test_06_guia_processing_service_auto_assignment`: Asignación automática a patio tipo `service` en guías de procesamiento y volumen.
- `test_07_manual_override_respected`: Respeto estricto de patio explícito o asignación manual.
- `test_08_no_blocking_without_patio`: Creación y procesamiento no bloqueante cuando no hay patio disponible (advertencia en log y chatter).
- `test_09_quant_patio_fields_and_read_access`: Proyección de campos en `stock.quant` (`lot_piezas`, `vol_nominal_m3`, `is_patio`, `patio_type`) y lectura para Operaciones, Auditoría y Contabilidad.
- `test_10_historical_records_untouched`: Garantía de cero escritura o recálculo sobre lotes históricos (D3).

### 33.3 Suite 6B (Consola de Ingresos): `test_volume_console_search_menu.py` (5 pruebas en `madenat_lumber_intake`)
- Búsqueda y filtrado por patio en la Consola Global de Ingresos.
- Filtro "Sin patio asignado" (`filter_sin_patio`) y localización de guías Arauco 4495589 y JCE 95806 sin alterar su registro histórico.

### 33.4 Suite 6C (Etiquetas de Volumen): `test_volume_labels_6c.py` (4 pruebas en `madenat_lumber_core`)
- `test_01_stock_lot_views_labels`: Rótulos "Vol. Compra (m³)" y "Vol. Export (m³)" en lista y formulario de `stock.lot`.
- `test_02_guia_processing_views_labels`: Rótulos en análisis comercial y de exportación de guías.
- `test_03_lumber_reception_views_labels`: Rótulos en recepción y stock generado.
- `test_04_lot_volume_purchase_and_export_accessible`: Accesibilidad y coherencia analítica de ambos volúmenes por etiqueta.

### 33.5 Suite 6D (Packing Estándar MADENAT): `test_packing_estandar_madenat_6d.py` (7 pruebas en `madenat_ingestion_engine`)
- `test_01_template_generation_and_validation`: Generación de `PLANTILLA_PACKING_ESTANDAR_MADENAT.xlsx` con listas desplegables (DataValidation) de producto, subproducto y perfil.
- `test_02_roundtrip_arauco_synthetic`: Ingesta de datos sintéticos normalizados de Arauco (guía 4495589).
- `test_03_roundtrip_jce_synthetic_separate_dimensions`: Ingesta de datos sintéticos de JCE (guía 95806 con espesor, ancho y largo en columnas separadas).
- `test_04_roundtrip_byc_fatima_synthetic`: Ingesta de datos sintéticos de BYC y Fátima.
- `test_05_three_decimal_rounding`: Redondeo estricto a 3 decimales (ej: 57,839556 m³ → 57,840 m³).
- `test_06_format_registration_noupdate`: Verificación del formato `standard_madenat` registrado en `lumber.ingestion.format` con `noupdate="1"`.
- `test_07_console_download_action`: Verificación de la acción de descarga y adjunto desde la Consola de Ingreso.

**Total pruebas acumuladas esperadas en suite:** 1.565 + 26 = **1.591 pruebas**.

---

## 34. PRUEBAS DE LA FASE 13/2D — PROCEDENCIA DEL PERFIL Y VIGENCIA DE LA LECTURA (AD-134)

Suite nueva `madenat_lumber_intake/tests/test_intake_profile_provenance.py` (9 pruebas, `post_install`).

| Prueba | Contrato verificado | Estado |
|---|---|---|
| `test_t2d_1_sugerencia_no_pisa_eleccion_del_operador` | Con `profile_origin='chosen'`, la sugerencia sólo se registra en `profile_suggested`; el aviso nombra la sugerencia y la elección | [VERIFICADO] |
| `test_t2d_2_sugerencia_se_aplica_sin_eleccion_previa` | Sin elección (`default`), la sugerencia se aplica y la procedencia pasa a `suggested`; sin aviso | [VERIFICADO] |
| `test_t2d_3_coincidencia_no_es_eleccion` | Coincidir con la sugerencia no marca `chosen`; elegir otro perfil sí lo marca y activa el aviso | [VERIFICADO] |
| `test_t2d_4_cambio_de_entrada_invalida_lectura` | Cambiar el perfil tras leer devuelve el wizard a `draft` y limpia preview, guía, marca y huella | [VERIFICADO] |
| `test_t2d_5_vals_identico_no_invalida` | Escribir los mismos valores conserva `previewed` y la huella | [VERIFICADO] |
| `test_t2d_6_derivacion_sin_lectura_bloquea_en_tres_modalidades` | Sin lectura, las tres modalidades lanzan `UserError` y no crean destino; tras leer, las tres quedan en `previewed` con huella | [VERIFICADO] |
| `test_t2d_7_lectura_rancia_bloquea_y_preview_renueva` | Datos mutados por vía baja (`_write`) ⇒ bloqueo «cambiaron después de la lectura»; volver a leer permite derivar | [VERIFICADO] |
| `test_t2d_8_preview_sin_documentos_no_escribe_nada` | Falta PDF, falta Excel y Volúmenes sin documentos: `UserError` y wizard intacto (sin tipo detectado, sin marcas, sin huella) | [VERIFICADO] |
| `test_t2d_9_documentos_requeridos_y_contrato_de_vista` | `has_required_documents` por modalidad; botón «Leer documento» condicionado; campos de procedencia y aviso presentes en el formulario | [VERIFICADO] |

**Utilidad de pruebas:** `tests/intake_reading_helpers.py::mark_previewed` deja el wizard en `previewed`
con huella coherente sin ejecutar el motor; la usan las suites de derivación
(`test_intake_wizard`, `test_granel_route`, `test_intake_modality`, `test_intake_profile_coherence`,
`test_volume_extraction`, `test_volume_operational`, `test_intake_volume_detail_pieces`) para no
depender de la extracción real.

**Ajuste de expectativa por H2:** `test_intake_wizard.test_t2_procesado_preview_does_not_invoke_extract_document`
ahora espera `state == 'previewed'` (antes `'draft'`) y exige huella de lectura.

**Resultado de la suite del módulo (madenat_test, 2026-10-26):** `541 tests` ejecutados
(`445 post-tests`), **0 failed, 0 error**. Los `ERROR` de `pg_advisory_xact_lock` en el log pertenecen a
`TestDeleteConcurrency.test_01`, prueba que provoca el timeout de bloqueo a propósito.

