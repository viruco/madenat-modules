# FASE 13 — SUBFASE 2E · Descarte de Fila de Totales Sin Etiqueta en Motor de Ingesta

**Proyecto:** MADENAT · Odoo 18 CE  
**Fecha:** 2026-10-27  
**Rama:** `fase13-2a-lectura`  
**Módulo modificado:** `madenat_ingestion_engine` (18.0.1.4.0 → 18.0.1.5.0)  
**Estado:** Etapa B completada y versionada localmente; Etapa C (documentación); **despliegue en BD (Etapa D) NO ejecutado** (pendiente de autorización).  
**Base usada para verificación:** `madenat_test` (solo lectura `SELECT` y validación en Python puro sin alterar registros ni esquemas).

---

## 0. Resumen Ejecutivo

| Dimensión | Hallazgo / Resultado | Evidencia |
|---|---|---|
| **Defecto corregido** | Doble conteo de volumen en documentos Excel con fila final de totales no etiquetada (ej. `40030.xls`, `41964.xls`, `41994.xls`). | 18 archivos de muestras presentaban el defecto; volumen extraído duplicaba el valor real. |
| **Causa raíz** | `_TOTALS_ROW_RE` exigía la presencia explícita de `total` o `subtotal`. Las filas de cierre numéricas puras no hacían match y eran parseadas como línea de detalle adicional (línea 13 en 40030). | `document_extractor.py:444`, `40030.xls` fila 25: celdas numéricas `46.15815`, `1362.847`, `54.518` sin texto. |
| **Solución aplicada** | **Regla V1:** en una pasada lineal (sin recursión), función `_is_unlabeled_total_row` descarta filas sin identificadores (sin paquete, piezas ni dimensiones) cuyo volumen numérico coincide con la suma acumulada de líneas aceptadas (`running_total_m3`) dentro de una tolerancia de `0.01` m³. | `madenat_ingestion_engine/services/document_extractor.py:77-113, 429, 492-502, 535-537` (commit `d6a780c`). |
| **Aislamiento de estado** | El descarte se ejecuta antes del forward-fill para no contaminar `forward_fill_state` ni propagar lotes sintéticos o emitir avisos espurios de lote heredado. | Test unitario caso 10 verificado. |
| **Pruebas unitarias** | Suite nueva `TestDocumentExtractorTotalsRow` con 10 pruebas sintéticas en memoria (XLSX y XLS), protegida ante falta de `xlwt`. | `tests/test_document_extractor_totals_row.py` (commit `5abee74`). 10/10 passed en 0.80 s. |
| **Matriz de regresión** | Ejecutada sobre los archivos válidos del corpus de ingreso (`muestras_documentos_ingreso` y filestore): 18 archivos con defecto corregidos (reducción exacta a la mitad, 1 fila descartada), 18 archivos sin defecto sin cambios, **0 filas de producto descartadas**. | Validación en Python puro con comparación byte-a-byte contra `HEAD`. |
| **Datos históricos en BD** | En `madenat_ingestion_document`, documentos `ING-00041` (id 41) e `ING-00052` (id 52) creados el 2026-09-02 tienen una línea fantasma histórica cada uno (ids 54 y 90). | Sin dependencias en tablas de negocio. Decisión: **no se limpian**. |

---

## 1. Causa Raíz e Investigación

### 1.1 El Defecto en Guía 40030
En la auditoría del documento `40030.xls` (25 filas × 17 columnas), la fila 25 contiene el cierre de totales del emisor con las celdas numéricas:
- Volumen m³: `46.15815`
- MBF: `1362.847`
- Compra nominal 45mm: `54.518`

Dicha fila no contiene ninguna palabra clave como "TOTAL" o "SUBTOTAL" (la celda de descripción está vacía o sin etiqueta textual). El motor `madenat_ingestion_engine` evaluaba únicamente:
```python
row_text = normalize_text(" ".join(str(cell) for cell in row if cell not in (None, "")))
if _TOTALS_ROW_RE.match(row_text):
    ...
    continue
```
Como `row_text` era `'46.15815 1362.847 54.518'`, la expresión regular `_TOTALS_ROW_RE` no coincidía. Por consiguiente:
1. La fila era aceptada como la **línea 13** de detalle.
2. Heredaba el lote sintético de las líneas precedentes vía forward-fill.
3. El volumen total extraído sumaba `46.15815 + 46.15815 = 92.3163` m³, duplicando exactamente el volumen físico de la guía.

---

## 2. Mapa de Llamadores e Impacto

| Llamador | Modelo / Método | Impacto de la Corrección |
|---|---|---|
| **Vista previa de Producto** | `madenat_lumber_intake/models/intake_wizard.py` (`action_preview_document`) | Cuando se adjuntan PDF y Excel, la vista previa invoca `extract_document()`. La corrección previene que la tabla de previsualización muestre 13 líneas y 92,316 m³; ahora muestra **12 líneas y 46,158 m³**, alineado con la realidad del packing. |
| **Volúmenes con Excel** | `madenat_lumber_intake/models/intake_wizard.py` (`_read_volumes_modalidad`) | En modalidad Volúmenes cuando se aporta Excel, las líneas y el volumen total provienen de `extract_document()`. La corrección elimina la línea espuria de cierre y evita falsas alarmas de discrepancia con el PDF. |
| **Ingesta Standalone** | `madenat_ingestion_engine/models/ingestion_document.py` (`action_extract`) | Al procesar documentos de ingreso desde el módulo standalone, se omite la línea final y se emite la advertencia estructurada `Fila N: fila de totales sin etiqueta omitida...` con visibilidad en auditoría. |

---

## 3. Solución Implementada — Regla V1

### 3.1 Diseño Algorítmico (Lineal, Sin Recursión)
Se implementó en [document_extractor.py](file:///home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_ingestion_engine/services/document_extractor.py):

1. **Constante de tolerancia:** `TOTAL_ROW_TOLERANCE_M3 = 0.01` (10 litros / 0.01 m³).
2. **Acumulador dinámico:** `running_total_m3 = 0.0` inicializado al inicio de `_build_lines()`. Se incrementa con `line['volume_m3']` **únicamente** cuando una línea es definitivamente aceptada.
3. **Predicado de detección (`_is_unlabeled_total_row`):**
   - **Criterio 1 (Sin identificadores):** `package_no`, `pieces`, `thickness_value_raw`, `width_value_raw`, `length_value_raw`, `thickness`, `width`, `length` deben estar todos vacíos o `None`.
   - **Criterio 2 (Volumen positivo):** `line['volume_m3']` numérico > 0.
   - **Criterio 3 (Acumulador previo positivo):** `running_total_m3 > 0` (la primera fila de un documento nunca puede ser un cierre de totales acumulado).
   - **Criterio 4 (Coincidencia con tolerancia):** `|volume_m3 - running_total_m3| <= TOTAL_ROW_TOLERANCE_M3`.
4. **Punto de inserción:**
   - Inmediatamente posterior al descarte de encabezados de unidades (`_is_unit_label_row`).
   - **Previo al forward-fill:** Evita contaminar `forward_fill_state` con lotes o productos y previene la emisión de advertencias espurias `"Fila N: 'lot_number' no informado, heredado..."`.
5. **Formato estricto de advertencia:**
   `"Fila {source_row_number}: fila de totales sin etiqueta omitida (volumen {v_disp} ≈ suma acumulada {s_disp})"` compatible con el patrón `^Fila (\d+):` consumido por `ingestion_document.py`.

---

## 4. Cobertura de Pruebas Unitarias

Clase `TestDocumentExtractorTotalsRow` en [madenat_ingestion_engine/tests/test_document_extractor_totals_row.py](file:///home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_ingestion_engine/tests/test_document_extractor_totals_row.py) con decorador `@tagged('post_install', '-at_install', 'madenat', 'madenat_ingestion_engine')`:

| Caso | Propósito del Test | Resultado |
|---|---|:---:|
| **test_01** | 12 paquetes sintéticos + fila de cierre sin etiqueta (volumen = suma) → 12 líneas, 46.15815 m³ y advertencia en XLSX y XLS (con skip si falta `xlwt`). | [VERIFICADO] |
| **test_02** | Fila de totales etiquetada `"TOTAL:"` → sigue descartada por `_TOTALS_ROW_RE` con aviso exacto (`'total: 46.15815'`) sin generar aviso nuevo. | [VERIFICADO] |
| **test_03** | Documento normal sin fila de totales → no se descarta ninguna línea ni emite advertencias. | [VERIFICADO] |
| **test_04** | Fila con solo `package_no` cuyo volumen coincide con la suma → NO se descarta (preserva línea de producto). | [VERIFICADO] |
| **test_05** | Fila con solo `pieces` cuyo volumen coincide con la suma → NO se descarta. | [VERIFICADO] |
| **test_06** | Primera fila del documento sin identificadores (`running_total_m3 == 0`) → NO se descarta. | [VERIFICADO] |
| **test_07** | Frontera de tolerancia (0.01 m³): diferencia de 0.009 m³ se descarta; diferencia de 0.011 m³ se conserva. | [VERIFICADO] |
| **test_08** | Dos filas de cierre consecutivas sin etiqueta con el mismo volumen → ambas descartadas. | [VERIFICADO] |
| **test_09** | Formato de advertencia cumple `^Fila (\d+):` para trazabilidad de fila en el modelo de ingesta. | [VERIFICADO] |
| **test_10** | Fila descartada no contamina el estado de forward-fill ni emite aviso de lote heredado. | [VERIFICADO] |

---

## 5. Matriz de Regresión

Se contrastó la salida del extractor antes (`git show HEAD:services/document_extractor.py`) y después en Python puro sobre los documentos válidos de la biblioteca de muestras de ingreso (`muestras_documentos_ingreso` y filestore).

> [!NOTE]
> **Alcance del corpus:** Se consideraron los documentos de detalle de ingreso (Excel y PDF tabulares de packing). Se excluyó 1 archivo del directorio de muestras por corresponder a otro tipo documental ajeno al circuito de ingreso.

### 5.1 18 Archivos con Defecto Corregido
En los 18 archivos afectados, la corrección descartó exactamente **1 fila de totales espuria**, reduciendo el volumen a la mitad real y eliminando el doble conteo:

| Archivo | Líneas antes | Líneas después | Suma m³ antes | Suma m³ después | Filas descartadas |
|---|:---:|:---:|:---:|:---:|:---:|
| `40030.xls` | 13 | **12** | 92.3163 | **46.1581** | 1 |
| `40030 (1).xls` | 13 | **12** | 92.3163 | **46.1581** | 1 |
| `41964.xls` *(filestore)* | 13 | **12** | 104.0220 | **52.0110** | 1 |
| `41994.xls` | 15 | **14** | 100.9913 | **50.4956** | 1 |
| `39491 (1).xls` | 13 | **12** | 101.6280 | **50.8140** | 1 |
| `39493 (1).xls` | 13 | **12** | 105.2100 | **52.6050** | 1 |
| `39500 (1).xls` | 13 | **12** | 111.1950 | **55.5975** | 1 |
| `39509 (1).xls` | 13 | **12** | 105.7500 | **52.8750** | 1 |
| `39510 (1).xls` | 13 | **12** | 105.4800 | **52.7400** | 1 |
| `39519 (1).xls` | 13 | **12** | 103.7430 | **51.8715** | 1 |
| `39522 (1).xls` | 13 | **12** | 100.4310 | **50.2155** | 1 |
| `40040 (1).xls` | 15 | **14** | 91.8972 | **45.9486** | 1 |
| `40597.xls` | 13 | **12** | 94.2598 | **47.1299** | 1 |
| `42.50 Kb.xls` | 9 | **8** | 79.7606 | **39.8796** | 1 |
| `65.50 Kb (1).xls` | 13 | **12** | 111.6423 | **55.8212** | 1 |
| `65.50 Kb.xls` | 13 | **12** | 108.4792 | **54.2396** | 1 |
| `Packing GD 97183 - W (1).xls` | 9 | **8** | 79.7606 | **39.8796** | 1 |
| `1° SELLOS ... FA543R ... .xlsx` | 11 | **10** | 673.1100 | **336.5550** | 1 |

### 5.2 18 Archivos Sin Defecto (Sin Cambios)
En los 18 archivos sin fila de cierre sin etiqueta, el comportamiento fue 100% neutro (**0 filas descartadas**, número de líneas y volumen idénticos antes y después):
`26270.xlsx` (17 líneas, 0.0 m³), `95083 (1) (1).xls` (8 líneas, 42.1320 m³), `95083 Final.xls` (8 líneas, 42.1320 m³), `Copia de 95083 (1) (1).xls` (8 líneas, 42.1320 m³), `GDE 95806.xls` (15 líneas, 0.0 m³), `NVTA881333 (2).xls` (15 líneas, 0.0 m³), `FACTURACION PACKING LIST 03-09-2026 MADENAT 47 (1).xlsx` (17 líneas, 0.0 m³), `FACTURACION PACKING LIST 01-10-2025 (2) MADENAT.xlsx` (15 líneas, 0.0 m³), `FACTURACION PACKING LIST 02-10-2025 (1) MADENAT.xlsx` (17 líneas, 0.0 m³), `FACTURACION PACKING LIST 02-10-2025 (2) MADENAT.xlsx` (17 líneas, 0.0 m³), `FACTURACION PACKING LIST 06-10-2025 (1) MADENAT.xlsx` (19 líneas, 0.0 m³), `PACKING HLZF75 (1).pdf` (17 líneas, 40.3150 m³), `HLZF75_4495589.pdf` (12 líneas, 40.3000 m³), `95083 .pdf` (5 líneas, 42.1320 m³), `26270.pdf` (3 líneas, 57.8400 m³), `Guia 41994.pdf` (2 líneas, 50.4960 m³), `GD 97183.pdf` (5 líneas, 39.8800 m³), `Guia 40030.pdf` (2 líneas, 54.5180 m³).

**Total de filas de producto descartadas:** **0** en todo el corpus.

---

## 6. Auditoría de Datos Históricos en Base de Datos

En la base `madenat_test`, se auditó el contenido del modelo `madenat.ingestion.document` (5 registros totales) mediante consultas `SELECT` de solo lectura:

1. **Documentos afectados:**
   - `ING-00041` (id 41, archivo `39491 (1).xls`, guía `39491`): línea ID 54 (fila origen 25) con volumen `50.814` m³ frente a la suma del resto de líneas de `50.818` m³ (diferencia de `0.004` m³).
   - `ING-00052` (id 52, archivo `42.50 Kb.xls`, guía `97183`): línea ID 90 (fila origen 23) con volumen `39.881` m³ frente a la suma del resto de líneas de `39.881` m³ (diferencia de `0.000` m³).
2. **Dependencias:**
   - Ambos registros fueron creados el `2026-09-02` por `Administrator` (`mauricio.seo@gmail.com`).
   - Estado: `extracted`, `total_volume_m3 = 0.000` (no confirmados ni migrados a recepción).
   - **0 claves foráneas** desde tablas operativas (`lumber_reception`, `stock_picking`, etc.).
3. **Decisión:** **No se limpian.** Se conservan como evidencia histórica inocua en la base de pruebas.

---

## 7. Commits Realizados en Etapa B

1. **`d6a780c`** — `fix(ingestion): descarte de fila de totales de cierre sin etiqueta (Regla V1)`
   - Archivo: `madenat_ingestion_engine/services/document_extractor.py` (+58 líneas, 0 eliminaciones).
2. **`5abee74`** — `test(ingestion): 10 pruebas sinteticas de descarte de fila de totales (Regla V1)`
   - Archivos: `madenat_ingestion_engine/tests/__init__.py` y `madenat_ingestion_engine/tests/test_document_extractor_totals_row.py` (+236 líneas).
3. **`7e28228`** — `chore(ingestion): version 18.0.1.5.0, changelog y readme con regla V1`
   - Archivos: `madenat_ingestion_engine/__manifest__.py`, `madenat_ingestion_engine/CHANGELOG.md`, `madenat_ingestion_engine/README.md`.

---

## 8. Límites Conocidos

1. **Volumen de cierre discordante:** Si un documento trae una fila de cierre sin etiqueta cuyo volumen difiere de la suma de las líneas previas en más de 0.01 m³ (por ejemplo por error de cálculo del proveedor o fila de totales parcial), el motor no la descartará automáticamente.
2. **Tolerancia absoluta fija:** La tolerancia está fijada en `0.01` m³ absolutos. En documentos de gran extensión (cientos de líneas), la deriva acumulativa de redondeo de punto flotante en el Excel origen podría exceder este límite.

---

## 9. Pendientes Registrados

1. **Despliegue en `madenat_test` (Etapa D):** [COMPLETADO el 2026-10-27]. Ver §10.
2. **Prueba funcional en UI con Guía 40030 (Checklist usuario):** Verificar en pantalla la visualización de 12 líneas y 46,158 m³ en el asistente de Ingreso de Madera.
3. **Mejora futura de consistencia:** Implementar chequeo de consistencia entre lo previsualizado en el wizard y lo generado por el parser final de Producto (`reception_parser.py` vs `extract_document()`).
4. **Mejora futura de volumen nominal:** Evaluar el uso de la columna de volumen nominal de la fila de cierre exclusivamente como dato de contraste y auditoría.

---

## 10. Despliegue en madenat_test (Etapa D — 2026-10-27)

### 10.1 Respaldo Previo
- **Archivo:** `/home/viruco/dev-stack/backups/madenat_test_pre_2e_20261027.dump`
- **Tamaño:** 12 MB (formato `pg_dump -Fc` binario)
- **SHA-256:** `2234d969cd666f8ad36d1e0c5f9c417f07547cc9bb0166b56d059844ad0ac4fe`
- **Verificación:** Catálogo TOC con 13.555 entradas verificado mediante `pg_restore -l`.

### 10.2 Línea Base de Datos (Invarianza Verificada)
- **Hashes de negocio (11 columnas):**
  - `lumber_reception_line` (id ≤ 7707): `45ad15888e36dfbc6d53ea9d54c05ab3` (antes == después)
  - `stock_lot` (id ≤ 49837): `02d6284d3209f5f6e0dc70e00a8ec4e7` (antes == después)
- **Conteos de tablas clave (antes == después):**
  - `lumber_reception`: 9
  - `lumber_reception_line`: 96
  - `stock_lot`: 152
  - `madenat_guia_processing`: 13
  - `madenat_lumber_intake_wizard`: 113
  - `madenat_ingestion_document`: 5
  - `madenat_ingestion_document_line`: 42

### 10.3 Despliegue y Suites de Pruebas
- **Comando:**
  ```bash
  docker compose run --rm -T web odoo -d madenat_test -u madenat_ingestion_engine,madenat_lumber_intake --test-tags /madenat_ingestion_engine,/madenat_lumber_intake --stop-after-init
  ```
- **Código de salida:** `0` (exitoso).
- **Log de evidencia:** `evidencias/2e_upgrade.log` (310 KB).
- **Resultados de las suites:**
  - `madenat_ingestion_engine`: **123 tests** ejecutados (incluidas las 10 pruebas nuevas de `TestDocumentExtractorTotalsRow`), 0 fallas, 0 errores.
  - `madenat_lumber_intake`: **541 tests** ejecutados (100% idéntico a la línea base de la Fase 2D), 0 fallas, 0 errores.
  - Total reporte general: `0 failed, 0 error(s) of 546 tests`.
  - Cero WARNINGs o ERRORs nuevos introducidos.

### 10.4 Prueba Funcional en Odoo Shell (Rollback Garantizado)
- **Script ejecutado:** `evidencias/script_prueba_funcional_40030.py` sobre `madenat_test` (salida en `evidencias/2e_funcional_shell.log`).
- **Caso 40030 (`40030.xls`, Guía `40030.pdf`):**
  - **Líneas previsualizadas:** **12** (antes 13).
  - **Volumen total previsualizado:** **46.15815 m³** (antes 92.3163 m³).
  - **Aviso generado:** `Fila 25: fila de totales sin etiqueta omitida (volumen 46.15815 ≈ suma acumulada 46.15815)`.
  - **Eliminación del defecto:** Se omitió la fila de cierre sin generar línea de producto ni forward-fill contaminante.
- **Caso 95083 (`95083.xls` sin fila de cierre numérico puro):**
  - **Líneas previsualizadas:** **8** (invariante).
  - **Volumen total previsualizado:** **42.132 m³** (invariante).
  - **Aviso de totales:** `Fila 27: se omitió una fila de totales ('total 2244 42.132 8')`.
- **Integridad de datos:** `env.cr.rollback()` ejecutado al finalizar; ningún registro fue persistido en la base de datos.
- **Servicio Web:** Contenedor `odoo18_app` restablecido y respondiendo con HTTP `200` en `/web/login`.

