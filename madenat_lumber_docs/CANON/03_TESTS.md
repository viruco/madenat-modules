# MADENAT — Matriz de Evidencia y Validación

**Versión documental:** 6.18.0
**Fecha de actualización:** 2026-10-10  <!-- actualizado: 2026-10-10 (1) — §14 **cierre funcional 2026-10-10**: corridas nuevas (no históricas) — dirigidas `TestGuiaProcessingExcelParser` + `TestVolumeUiHierarchy` + `TestVolumeOperationsScreen` = **0 failed, 0 error(s) of 34 tests**; regresión de módulo `madenat_lumber_intake` = **2 failed of 380** (ambas por el encabezado consolidado «📄 Evidencia documental»; constantes de prueba adaptadas → verde) + verificación con documento REAL de la Nota de Venta JCE (12/12 líneas, `4,9967` ≈ `VOL.` 4,997) y de la Consola (Ferramenta 57,840 / 48,009). Ver `02_CONTINUIDAD.md` §17.16. | 2026-10-08 (5) — §13.5–13.6 **reconstrucción de las pruebas con la biblioteca externa de muestras** (`muestras_documentos_ingreso`): relación **prueba ↔ etapa (A–F) ↔ resultado**, con **correspondencia declarada A–F ↔ V0–V3** (los niveles V0–V3 siguen vigentes y no se renombran); casos con evidencia localizada: Ferramenta **26270** (adjuntos + 17 lotes + picking + réplica en TEST remoto), Ferramenta **19846/19827/19826**, Arauco **4495589** (fixture byte-idéntico + motor real + registro + lote), JCE **95806** guía (Volúmenes) y su packing Nota de Venta (rechazo por diseño), Fátima **41994** y Byc **95083** (fixture derivado / formato equivalente a `39519`, sí ingresado); **fuerza de la evidencia** y **ausencias declaradas** (dónde se buscó y qué artefacto falta); **no** se ejecutó ninguna prueba en esta intervención. | 2026-10-08 (4) — §13 RELACIÓN REQUISITO → EVIDENCIA → RESULTADO de las solicitudes de Cristhian (R01–R16, 2026-09-02/07). §13.2 pasa revista a las pruebas **existentes** y su relación con cada requisito; **no se ejecutó ninguna prueba nueva** en esta intervención (el servicio local 8069 no es operativo desde esta distro y el TEST remoto se inspeccionó solo lectura). Se declaran explícitamente las ausencias de evidencia: los **10 adjuntos del correo del 7-sep** no aparecen como tales en ningún expediente; sí existen copias identificables en `muestras_documentos_ingreso/07-09-2026/` (15 archivos, 3 pares duplicados por hash). **5 de 5 proveedores** se identificaron documentalmente (Fátima/Ferramenta/Byc=Blocks & Cutstock/JCE/Arauco) pero **solo 2 tienen fixture automatizado** (`HLZF75_4495589.pdf` Arauco; `tests/fixtures/26270.txt` Ferramenta) y **ninguno** tiene evidencia de ingesta real en el TEST remoto (la tabla `madenat_guia_processing` del remoto contiene **1** registro: guía **26270**, Ferramenta, `validated`). Ver §13.3. | 2026-10-08 (3) — §12.6 A/B **aplicado en el desarrollo existente** (`madenat_test` / 8069) + reorganización de la UI de Ingreso de Madera; **88/88 dirigidas en verde sobre `madenat_test`** (misma nómina del gate, incl. Cristhian uid 8 `su=False`); aislamiento temporal **retirado**; **V3 (navegador) sigue pendiente**. | 2026-10-08 (2) — §12.5: entorno aislado **recreado** (autorizado; workcopy `:ro`, sin diffs) y filestore repoblado; **V3 sigue pendiente de evidencia manual**. | 2026-10-08 (1) — §12.5 retoma de SOLO LECTURA (2026-10-08): **V3 sigue sin ejecutarse** (entorno aislado no conservado tras el reinicio del host); integridad de A/B reverificada (SHA-256 = checkpoint; `patch --dry-run` limpio; A/B ausente del código activo y de `madenat_test`). Ver `02_CONTINUIDAD.md` §17.12. | 2026-10-07 (3) — §12.4: gate previo A/B sobre COPIA del árbol activo con cambios locales (byte a byte = workcopy; diffs sin docs), 88/88 dirigidas en verde incl. usuario real Cristhian (su=False), servidor aislado de navegador (pendiente V3). | 2026-10-07 (2) — §12: cobertura retorno de servicio / imputación posterior (AD-102). -->
<!-- actualizado: 2026-10-10 (2) — §15 relación de conciliación envío–retorno (Bloque A/B/C): suite nueva T1–T12 = 12/12; regresión `madenat_lumber_logistics` = 3 failed, 0 error of 265 (3 fallas PRE-EXISTENTES por aserción global de `deviation`; 0 fallas nuevas). Bloque D no implementado. Versión 03 6.17.0 → 6.18.0. Evidencia: CONCILIACION_ENVIO_RETORNO_20261010/. -->
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
  `IMPL_SERVICE_RETURN_AB_20261007/docs/GUION_VERIFICACION_NAVEGADOR.md`. **No** se declara
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
`APPLY_AB_UI_20261008/logs/tests_directed_madenat_test_20261008_093825.log`).

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
| Intake (regresión de módulo) | `--test-tags /madenat_lumber_intake` | **2 failed, 0 error(s) of 380** (→ corregidas) | `CIERRE_PENDIENTES_20261010/logs/tests_intake_20261010.log` |
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
| **Vínculo al reversar la imputación** | `models/madenat_sv_imputation.py::action_reverse` (**no** toca `return_link_ids`) | — | ⚠️ **NO acreditado**: la reversa de la imputación **no** revierte ni marca el vínculo; este conserva su estado. Efecto **pendiente de decisión** |
| **Estados elegibles del picking / exclusión de cancelados** | `models/madenat_processor_return_link.py::_eligible_shipment_pickings` (`state='done'` + `location_dest_id.processor_partner_id != False`) | T5 (no elegible), T12 (elegible) | ✅ Acreditado por dominio (`state='done'` excluye `cancel`); **sin** caso dedicado de cancelado |
| **Consistencia de compañía** | `company_id` related de `picking_id`; elegibilidad filtra compañía | — | ⚠️ **Parcial**: no hay restricción explícita que impida enlazar guía y envío de compañías distintas |
| **Permisos (ORM/RPC)** | `_link_check_apply_permission` / `_link_check_reverse_permission`; ACL 4 grupos (`security/ir.model.access.csv`) | T9; §15.4 (a) | ✅ Acreditado |
| **Doble contabilización N:M** | magnitudes por vínculo; **sin** reparto/prorrateo | T2/T3 (N:M) | ⚠️ **No aplica aún**: sin conciliación cuantitativa; `shipment_volume_m3` se repite por vínculo ⇒ **sumar vínculos duplicaría** el volumen. Reparto N:M = Bloque **D** (pendiente) |
