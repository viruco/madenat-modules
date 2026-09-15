# Auditoría — Extracción y vinculación de OC documental desde Guía y Packing

**Fecha:** 2026-08-21
**Modalidad:** Solo lectura. Sin modificar Python, XML, CSV, manifest, tests, datos ni contenedores.
**Alcance:** Producto (`lumber.reception`), Procesado (`madenat.guia.processing`), capa de entrada (`madenat_lumber_intake`), consola (`madenat.lumber.intake.console`), `purchase.order`.
**Caso real analizado:** Guía Procesados 19827 (id=483, proveedor Ferramenta, OC documental `MC - 2506 - 01`, estado "No encontrada").

---

## 1. Resumen ejecutivo

**La OC del caso 19827 SÍ fue extraída, SÍ fue almacenada, SÍ fue normalizada y SÍ se intentó vincular. La búsqueda falló porque la `purchase.order` `MC250601` no existe en el sistema.** El estado "No encontrada" es **correcto** para los datos actuales, no es un defecto de extracción ni de matching.

Evidencia de trazabilidad completa:

| Etapa | Resultado | Evidencia |
|---|---|---|
| Fuente de extracción | **Guía PDF** (prioridad 1 sobre Excel) | PDF contiene `(801) Orden de Compra MC - 2506 - 01`; Excel contiene `MC-2506-01` |
| Valor bruto detectado | `MC - 2506 - 01` | `madenat_guia_processing.py:2118-2145` (regex Fase A) |
| Campo de almacenamiento | `oc_reference_raw` | SQL: `SELECT oc_reference_raw FROM madenat_guia_processing WHERE id=483` → `MC - 2506 - 01` |
| Normalización | `MC250601` | SQL: `oc_reference_norm='MC250601'`; función `normalize_oc_key` (`utils_uom.py:214-230`) |
| Búsqueda ejecutada | Sí | `_match_purchase_order()` llamado desde `action_verify_data` (`madenat_guia_processing.py:1352`) |
| Dominio de búsqueda | `[('state','in',['draft','sent','purchase','done'])]` + `partner_id` si existe | `madenat_guia_processing.py:3220-3223` |
| Coincidencias | 0 | SQL: `SELECT id FROM purchase_order WHERE name ILIKE '%2506%' OR ... ` → 0 filas |
| Vínculo resultante | `order_id = NULL`, `oc_match_status='not_found'` | SQL guía 483 |
| Mensaje visible | "No se encontró una OC coincidente en el sistema." | `oc_match_note` guía 483; mostrado en `oc_match_note` (fachada Procesados XML línea 74) |

**Hallazgo adicional — Proveedor vacío (defecto real, de extracción):**

El proveedor "Ferramenta" SÍ está en el PDF (`RUT: 77066489-6` y `COMERCIALIZADORA Y DISTRIBUIDORA FERRAMENTA SPA`), pero **no se resolvió a `res.partner`**. Causas concatenadas:

1. El nombre del emisor en el PDF está en `lines[1]` (`COMERCIALIZADORA Y DISTRIBUIDORA FERRAMENTA SPA`); el parser toma `lines[0]` = `RUT: 77066489-6` y tras amputar el RUT el nombre queda vacío (`madenat_guia_processing.py:2341-2353`).
2. El partner existente `Ferramenta` (id=17) **no tiene VAT registrado** → `search([('vat','=','77066489-6')])` devuelve 0.
3. La rama de creación exige `supplier_name and len(supplier_name) > 2` → nunca se ejecuta porque el nombre es vacío (`madenat_guia_processing.py:1258-1269`).
4. Resultado: `partner_id = NULL` en la guía 483.

**Impacto del proveedor vacío en la OC:** En el caso 19827 no cambió el resultado final (la OC no existe de todos modos), pero en general la búsqueda de OC sin filtro de proveedor (`_match_purchase_order` línea 3221 solo filtra `if self.partner_id`) aumenta el riesgo de falsos positivos si un mismo `name` de OC se reutiliza entre proveedores.

**Veredicto a la pregunta central:**

> ¿La OC documental no se extrajo, se extrajo pero no se vinculó, o se vinculó incorrectamente?

Se **extrajo y no se vinculó**, con causa justificada: la OC no existe en `purchase.order` (ni por `name`, ni por `partner_ref`, ni normalizada, ni para el proveedor). No hay defecto de extracción, normalización ni dominio para la OC. El defecto real encontrado es la **no resolución del proveedor**, que es un problema de parser, no de matching de OC.

---

## 2. Mapa completo de datos OC

### 2.1 Flujo Procesados — `madenat.guia.processing`

| Campo técnico | Modelo | Etiqueta visible | Tipo | Es origen/documental | Es vínculo real | Quién lo escribe | Quién lo lee |
|---|---|---|---|---|---|---|---|
| `oc_reference_raw` | guia.processing | OC Documental | Char | **Sí** (documental) | No | `action_verify_data` | `_match_purchase_order`, `_compute_oc_reference_norm`, fachada Intake |
| `oc_reference_norm` | guia.processing | OC Normalizada (matching) | Char (compute store) | Derivada | No | Compute `_compute_oc_reference_norm` | `_match_purchase_order` |
| `oc_match_status` | guia.processing | Estado Match OC | Selection | No | Indicador | `_match_purchase_order`, creación manual | Fachada Intake, logs |
| `oc_match_note` | guia.processing | Nota de Match OC | Text | No | Indicador | `_match_purchase_order` | Fachada Intake |
| `order_id` | guia.processing | Orden de Compra | Many2one `purchase.order` | No | **Sí** | `_match_purchase_order`, `action_create_purchase_order_from_document` | Consola, `_obtener_precio_desde_oc`, pickings |
| `partner_id` | guia.processing | Proveedor / Transportista | Many2one `res.partner` | Parcial | No (criterio) | `action_verify_data` (desde PDF RUT) | Consola, `_match_purchase_order`, pickings, validación |
| `oc_pdf_file` / `oc_pdf_filename` | guia.processing | PDF Orden de Compra (OC) | Binary/Char | Documental OC | No | usuario | `_extract_po_draft_values_from_oc_pdf` |

### 2.2 Flujo Producto — `lumber.reception`

| Campo técnico | Modelo | Etiqueta visible | Tipo | Es origen/documental | Es vínculo real | Quién lo escribe | Quién lo lee |
|---|---|---|---|---|---|---|---|
| `supplier_id` | lumber.reception | Proveedor | Many2one `res.partner` | Parcial | No (criterio) | `_find_or_create_po_intelligent`, usuario | `_match_reception_purchase_order`, SQL view consola |
| `purchase_id` | lumber.reception | Orden de Compra | Many2one `purchase.order` | No | **Sí** | `_match_reception_purchase_order`, `_find_or_create_po_intelligent`, wizard PO link | Consola, reportes |
| `manual_po_name` | lumber.reception | N° Orden (Manual) | Char | Manual | No | `_find_or_create_po_intelligent`, usuario | `_compute_purchase_order_display`, alertas |
| `oc_reference_raw` | lumber.reception | OC Documental | Char (readonly) | **Sí** | No | `_find_or_create_po_intelligent` | `_match_reception_purchase_order`, display |
| `oc_reference_norm` | lumber.reception | Clave normalizada (matching) | Char (compute store) | Derivada | No | Compute (`parser.normalize_po_key`) | `_match_reception_purchase_order` |
| `oc_match_status` | lumber.reception | Estado Match OC | Selection | No | Indicador | `_match_reception_purchase_order`, wizard PO link | Fachada Producto |
| `oc_match_note` | lumber.reception | Nota de Match OC | Text | No | Indicador | `_match_reception_purchase_order`, wizard PO link | Fachada Producto |
| `purchase_order` | lumber.reception | Orden Compra (Visual) | Char (compute store) | No | Display | Compute `_compute_purchase_order_display` | SQL view consola |
| `purchase_order_name` | lumber.reception.line | OC canónica | Char (related) | No | Display | Related | líneas |

### 2.3 Consola — `madenat.lumber.intake.console` (vista SQL, readonly)

| Campo técnico | Modelo | Etiqueta visible | Tipo | Fuente SQL | Notas |
|---|---|---|---|---|---|
| `partner_id` | console | Proveedor | Many2one | `gp.partner_id` (Procesado) / `lr.supplier_id` (Producto) | Correctamente mapeado |
| `purchase_id` | console | OC vinculada | Many2one | `gp.order_id` / `lr.purchase_id` | Vínculo real |
| `purchase_reference` | console | OC documento | Char | `COALESCE(po.name,'')` (Procesado) / `lr.purchase_order` (Producto) | **No muestra `oc_reference_raw` de Procesados** |
| `oc_pending` | console | OC | Selection compute | `purchase_id` | 'linked'/'pending' |

### 2.4 `purchase.order` (Odoo estándar + módulo purchasing)

| Campo técnico | Modelo | Uso en conciliación |
|---|---|---|
| `name` | purchase.order | **Único campo comparado en Procesados** (`_match_purchase_order:3228-3230`) |
| `partner_ref` | purchase.order | Comparado SOLO en Producto (`_find_or_create_po_intelligent:2339`) |
| `partner_id` | purchase.order | Filtro de dominio en ambos flujos |
| `state` | purchase.order | Filtro `['draft','sent','purchase','done']` en ambos flujos |
| `origin` | purchase.order | **Nunca se usa en conciliación** |
| `company_id` | purchase.order | **Nunca se filtra en conciliación** (riesgo multi-compañía) |

**Distinción clave:**

- **Procesados**: `oc_reference_raw` es escritura automática del parser; `order_id` es el vínculo real; la conciliación compara **solo `name`**.
- **Producto**: `oc_reference_raw` es escritura del flujo inteligente; `purchase_id` es el vínculo real; la conciliación compara **`partner_ref` OR `name`**.

---

## 3. Flujo Procesados

Trazabilidad desde archivo hasta vínculo real:

```text
Wizard Intake (_route_procesado, intake_wizard.py:296-326)
  → create madenat.guia.processing {excel_file, excel_filename, tipo_recepcion='service',
       assignment_location_id, guide_pdf_file?, guide_pdf_filename?}
  → guia.action_verify_data()

action_verify_data (madenat_guia_processing.py:1112-1360)
  1. _parse_packing_excel(archivo_excel) (1128) → crea processing_line_ids (1132-1186)
  2. PDF presente → _parse_dispatch_pdf(archivo_pdf) (1208)
       → dict con 'orden_compra' (2368), 'rut_emisor', 'nombre_emisor' (2378-2379)
  3. Prioridad fuente OC: PDF (1282-1287) > Excel (1303-1309)
  4. Persistencia oc_reference_raw (1315-1338): regla "no sobrescribir" con mejoras
       si detected_norm más largo y contiene stored_norm
  5. self.write(update_vals) (1347)
  6. self._match_purchase_order() (1352)

_match_purchase_order (3178-3279)
  1. Sin oc_reference_raw → not_found (3190-3195)
  2. order_id existente → respetar, marcar 'manual' si estaba not_found (3197-3210)
  3. normalized_ref = oc_reference_norm (3212-3217)
  4. domain = [('state','in',['draft','sent','purchase','done'])]
          + [('partner_id','=',self.partner_id.id)] si partner_id (3220-3223)
  5. matches = POs donde normalize_oc_key(po.name) == normalized_ref (3226-3239)
  6. 1 → single_match + order_id (3241-3252)
  7. >1 → multi_match + order_id=False (3254-3267)
  8. 0 → not_found + order_id=False (3269-3279)

Consola (intake_console.py:152-189 UNION ALL)
  → gp.order_id AS purchase_id
  → COALESCE(po.name,'') AS purchase_reference
  → gp.partner_id AS partner_id
```

**Archivo/Método/Línea (evidencia):**

| Paso | Archivo | Método | Líneas |
|---|---|---|---|
| Entrada wizard | intake_wizard.py | `_route_procesado` | 296-326 |
| Parser Excel | madenat_guia_processing.py | `_parse_packing_excel` | 2386-2430 |
| Parser PDF | madenat_guia_processing.py | `_parse_dispatch_pdf` | 2069-2383 |
| Prioridad PDF→Excel | madenat_guia_processing.py | `action_verify_data` | 1282-1309 |
| Persistir raw | madenat_guia_processing.py | `action_verify_data` | 1315-1338 |
| Matching | madenat_guia_processing.py | `_match_purchase_order` | 3178-3279 |
| SQL view consola | intake_console.py | `init()` | 152-189 |

---

## 4. Flujo Producto

```text
Wizard Intake (_route_producto, intake_wizard.py:265-293)
  → create lumber.reception {pdf_file, pdf_filename, excel_file, excel_filename, ingestion_profile}
  → reception.action_process_documents()

action_process_documents (lumber_reception.py:2661-2670)
  → LumberReceptionWorkflow.run_ingestion_pipeline(self)

workflow (reception_workflow.py)
  → parsea guía/PDF (reception_parser) → dg_data
  → parsea Excel → oc_data
  → _find_or_create_po_intelligent(dg_data, oc_data) (lumber_reception.py:2251-2400)

_find_or_create_po_intelligent (2251-2400)
  1. po_ref_raw = dg_data.get('po_ref') o oc_data.get('po_ref_fallback') (2271-2275)
  2. normalize_po_display / normalize_po_key (2278-2279)
  3. Persistir oc_reference_raw si no existe (2284-2288)
  4. Bloqueo si no po_key o no supplier_rut (2291-2300)
  5. Resolver/crear partner por VAT (2312-2329)
  6. candidate_pos = purchase.order search [partner, state] (2332-2335)
  7. match por partner_ref normalizado OR name normalizado (2338-2341)
  8. hit → purchase_id + single_match (2357-2369)
  9. no hit → manual_po_name + not_found (2382-2390)

_validate_reception (workflow) → _match_reception_purchase_order (1875-1962) como refuerzo
  → domain [state] + supplier_id
  → compara SOLO name normalizado
```

**Diferencias confirmadas Producto vs Procesados:**

| Aspecto | Producto | Procesados |
|---|---|---|
| Parser | `reception_parser.parse_dispatch_guide` + workflow | `_parse_dispatch_pdf` (nativo core) |
| Campo vínculo | `purchase_id` | `order_id` |
| Referencia documental | `oc_reference_raw` | `oc_reference_raw` (mismo nombre pero escritura distinta) |
| Manual | `manual_po_name` | No existe; solo `order_id`/creación manual |
| Conciliación | `partner_ref` **OR** `name` | **SOLO `name`** |
| Match por archivo PDF | `dg_data.get('po_ref')` | `pdf_data.get('orden_compra')` |
| Match por Excel | — | `packing_data.get('oc_reference')` |

---

## 5. Extracción desde Guía PDF

**Procesados:**

```text
Método: _parse_dispatch_pdf (madenat_guia_processing.py:2069-2383)
Archivo: madenat_guia_processing.py
Líneas: 2112-2207 (extracción OC) ; 2325-2360 (emisor)
Entrada: texto plano extraído con pdfplumber (2073-2075), concatenado todas las páginas
Patrón de extracción (Fase A prioridad): 
  r'\b((?:MC|OC)\s*[:.\-]?\s*\d{2,4}[\s\-]+\d{2,4}(?:[\s\-]+\d{2,4}(?!\/|\d))*)'  (2118-2121)
  → elegir match más largo plausible (2131-2145)
  Fase A short: r'\b((?:MC|OC)\s*[:.\-]?\s*\d{2,4})' (2149-2152)
  Fase B fallback: r'((?:MC|OC|Orden)\s*[:.\-]?\s*[A-Z0-9]+(?:[\s\-][A-Z0-9]+)+)' y r'801[\s\.\-]*(\d+)' (2176-2179)
Valor extraído (caso 19827): 'MC - 2506 - 01' (desde '(801) Orden de Compra MC - 2506 - 01 02/10/2025')
Destino: oc_reference_raw (persistido en action_verify_data 1315-1338)
Fallback si no encuentra: oc_name=False → 'orden_compra': False (2368) → se rellena desde Excel (1303-1309)
```

**Validador de plausibilidad:** `_is_plausible_oc_reference` (2023-2067) — rechaza si longitud >50, sin dígitos, ≥3 palabras del vocabulario DTE (`_OC_HEADER_NOISE`, 2015-2021), >6 palabras, o sin token numérico.

**Producto:** el parser real es `reception_parser.parse_dispatch_guide` (no leído en profundidad porque no participó en el caso 19827; documentado por simetría en el informe: `_find_or_create_po_intelligent` usa `dg_data.get('po_ref')`).

**Limitaciones detectadas:**

1. **Confusión posible guía vs OC**: el patrón Fase A exige prefijo MC/OC, por lo que no confunde el número de guía (19827) — verificado en el caso: guía = 19827, OC = MC250601.
2. **El regex Fase A no captura `Orden de Compra` sin MC/OC**: si el PDF dijera solo `Orden de Compra 2506-01`, solo lo capturaría la Fase B (que sí incluye `Orden`).
3. **El nombre del emisor se amputa mal cuando `lines[0]` es solo RUT** (2341-2353): en el caso 19827, `lines[0]='RUT: 77066489-6'` → tras amputar queda vacío y el nombre real en `lines[1]` se pierde. **Este es el defecto confirmado para el proveedor.**

---

## 6. Extracción desde Packing Excel

**Procesados:**

```text
Método: _find_oc_reference_in_excel (madenat_guia_processing.py:2757-2797)
Archivo: madenat_guia_processing.py
Líneas: 2757-2797
Hoja/rango: lee SOLO la hoja activa (pd.read_excel, header=None, nrows=10) — 2777
Regla de extracción: 
  regex_lib.search(r'((?:MC|OC|Orden)\s*[:.\-]?\s*[A-Z0-9]+(?:[\s\-][A-Z0-9]+)+)', fila) (2785)
  sobre cada fila como string concatenada de celdas no vacías (2781)
  Devuelve el primer match; normaliza espacios (2787-2789)
Valor bruto (caso 19827): 'MC-2506-01' presente en C3/D3 (hoja Packing)
Destino: NO se persistió directamente; se usa como oc_reference_detected solo si el PDF no trajo OC (1303-1309)
Fallback si no encuentra: None (2797)
```

**Detalle del caso 19827 (Excel):**

| Celda | Valor |
|---|---|
| Packing!C3 | ORDEN DE COMPRA |
| Packing!D3 | MC-2506-01 |
| Packing!C4/D4 | Fecha: / 2025-10-02 |
| Packing!C5/D5 | Cliente: / MADENAT CHILE LIMITADA |
| Packing!C6/D6 | N° Guía de Despacho: / 19827 |

**El Excel NO contiene RUT ni nombre de proveedor/emisor** — solo Cliente MADENAT. Por tanto, en este caso la única fuente de proveedor posible era el PDF.

**Limitaciones:**

1. No define columnas explícitas (OC, Orden de Compra, N° OC, PO, Referencia, Documento): busca cualquier string que calce con el regex en las primeras 10 filas.
2. Solo lee 10 filas; una OC en fila >10 nunca se detecta.
3. No gestiona múltiples referencias: devuelve la primera; no advierte discrepancias con el PDF.
4. No hay auditabilidad de fuente ("OC obtenida desde guía" vs "OC obtenida desde packing"): no existe campo que registre el origen de `oc_reference_raw`.
5. **El parser de Procesados es distinto al de Producto** — Producto no extrae OC del Excel en este punto; usa `reception_parser` y `_find_or_create_po_intelligent`.

---

## 7. Prioridad y conflictos de fuente

**Regla efectiva en Procesados (evidencia `action_verify_data:1199-1309`):**

| Escenario | Fuente guía | Fuente packing | Resultado almacenado | Regla aplicada | Evidencia |
|---|---|---|---|---|---|
| OC solo en PDF | MC - 2506 - 01 | — | MC - 2506 - 01 | PDF prioridad 1 | Líneas 1282-1287 |
| OC solo en Excel | — | MC-2506-01 | MC-2506-01 | Fallback Excel (prioridad 2) | Líneas 1303-1309 |
| OC en ambos (caso 19827) | MC - 2506 - 01 | MC-2506-01 | MC - 2506 - 01 (PDF) | **PDF gana siempre**; no se compara contra Excel | Líneas 1282-1287; `oc_reference_raw='MC - 2506 - 01'` |
| PDF y Excel contradictorios | X | Y | X (PDF) | PDF sobrescribe silenciosamente al Excel; **no hay detección de discrepancia** | Líneas 1282-1309; no existe bloque ni log de conflicto |
| Valor manual del usuario | — | — | (según flujo) | Para Procesados no hay campo manual de referencia OC; `order_id` manual solo vía wizard/creación | `order_id` + `oc_match_status` |
| Sin OC documental | — | — | oc_reference_raw='' | `_match_purchase_order` → not_found con nota "No existe referencia documental" | Líneas 3190-3195 |
| Re-verificación con raw existente | MC 2506-01 (más corto) | MC - 2506 - 01 (más largo) | Se actualiza a más largo | Regla: detectado_norm más largo y contiene stored_norm | Líneas 1327-1332 |
| Re-verificación con raw distinto | A | B | Se conserva el existente | Regla: no sobrescribir si normalizados difieren | Líneas 1333-1338 |

**Respuestas directas:**

1. **¿La Guía tiene prioridad sobre el Packing?** Sí, en Procesados (PDF prioridad 1, Excel prioridad 2).
2. **¿El Packing sobre la Guía?** No.
3. **¿Se comparan y registra discrepancia?** No. El fallback solo se usa si PDF no trajo OC; no hay comparación ni log de conflicto.
4. **¿Una fuente sobrescribe silenciosamente a la otra?** Sí: el PDF sobrescribe al Excel sin rastro si la re-verificación coincide normalizado; si el normalizado difiere, se conserva el previo con solo un `_logger.info` (1333-1338), no visible al usuario.
5. **¿El valor manual del usuario tiene prioridad?** En Procesados no existe `manual_po_name`. `order_id` asignado manualmente se respeta (`_match_purchase_order:3197-3210`).
6. **¿La referencia documental puede quedar vacía aunque un documento la contenga?** Sí: si el PDF falla con excepción interna (bloque try 1201-1300 captura `Exception` con `_logger.warning` y continúa) y el Excel no la contiene o el regex no la detecta.
7. **¿Existe auditabilidad de fuente?** **No.** No hay campo `oc_source` ni log de "OC obtenida desde guía/packing". Solo `_logger.info` (1284-1287, 1306-1309).

---

## 8. Normalización

**Función única:** `normalize_oc_key(value)` en `utils_uom.py:214-230`:

```python
if not value:
    return ''
return re.sub(r'[^A-Z0-9]+', '', (value or '').upper())
```

Reglas efectivas: mayúsculas, eliminar todo lo que no sea A-Z0-9 (espacios, guiones, puntos, dos puntos), sin trim de prefijos.

**Tabla de casos solicitada:**

| Referencia original | Normalización aplicada | Valor usado para búsqueda | Método/función | Riesgo |
|---|---|---|---|---|
| `MC - 2506 - 01` | re.sub no A-Z0-9, upper | `MC250601` | normalize_oc_key | Bajo |
| `MC-2506-01` | idem | `MC250601` | normalize_oc_key | Bajo |
| `MC 2506 01` | idem | `MC250601` | normalize_oc_key | Bajo |
| `MC-2506 -01` | idem | `MC250601` | normalize_oc_key | Bajo |
| `OC MC-2506-01` | idem, NO elimina prefijo OC | `OCMC250601` | normalize_oc_key | **Alto: no matchearía MC250601** |
| `Orden de Compra MC - 2506 - 01` | idem → `ORDENDECOMPRAMC250601` | `ORDENDECOMPRAMC250601` | normalize_oc_key | **Alto: no matchearía MC250601** |

**Respuestas directas:**

1. ¿Elimina espacios? Sí.
2. ¿Elimina guiones? Sí.
3. ¿Convierte a mayúsculas? Sí.
4. ¿Elimina prefijos OC/PO/Orden de Compra? **No.** `OC MC-2506-01` → `OCMC250601`, no `MC250601`.
5. ¿Conserva formato original? Sí, en `oc_reference_raw`; la normalización es solo paralela (`oc_reference_norm`).
6. ¿Normalización distinta para extracción y búsqueda? La extracción del PDF normaliza espacios (`re.sub(r'\s+',' ',...)` 2134) pero conserva guiones; la búsqueda usa la clave técnica sin separadores. Para el matching ambas convergen.
7. ¿Falsos positivos? Riesgo de colisión: `MC-2506-01` y `MC 2506 01` y `MC250601` colapsan iguales (deseable); pero `MC2506-01` vs `MC-250601` también colapsan a `MC250601` (indeseable, aunque improbable).
8. ¿Coincidencia exacta, ilike, normalizada o parcial? **Exacta sobre normalizada**: `candidate_oc_norm == normalized_ref` (3230).
9. ¿Función reutilizable? Sí: `normalize_oc_key` (utils_uom.py:214-230); usada por ambos modelos vía wrapper `_normalize_oc_key`.
10. ¿Reglas distintas Producto/Procesados? La normalización base es la misma; la **diferencia está en el campo comparado**: Procesados compara solo `name`; Producto compara `partner_ref` **o** `name`.

**Riesgo detectado (caso 19827):** el PDF trae `MC - 2506 - 01` en la guía y `Orden: S09496` como número de orden de despacho. El regex Fase A eligió correctamente el texto con MC. Sin embargo, si un PDF trajera `Orden de Compra MC - 2506 - 01`, la Fase A lo capturaría igual porque usa `\b(?:MC|OC)...` con `\b`, que encuentra la subcadena `MC - 2506 - 01` dentro del texto más largo.

---

## 9. Búsqueda en `purchase.order`

| Flujo | Método de búsqueda | Dominio | Campo vínculo | Momento de ejecución | Resultado no encontrado | Resultado múltiple |
|---|---|---|---|---|---|---|
| **Procesados** | `_match_purchase_order` (`madenat_guia_processing.py:3178-3279`) | `[('state','in',['draft','sent','purchase','done'])]` + `[('partner_id','=',x)]` si partner_id | `order_id` | Al verificar (`action_verify_data` → línea 1352) | `order_id=False`, `oc_match_status='not_found'`, nota "No se encontró una OC coincidente en el sistema." | `order_id=False`, `oc_match_status='multi_match'`, nota "Se encontraron N OCs coincidentes" |
| **Producto** | `_find_or_create_po_intelligent` (`lumber_reception.py:2251-2400`) + `_match_reception_purchase_order` (1875-1962) | `[('partner_id','=',supplier.id),('state','in',['draft','sent','to approve','purchase','done'])]` | `purchase_id` | Dentro del workflow `action_process_documents` | `purchase_id=False` + `manual_po_name` + not_found | Solo evalúa el primero (`[:1]`) en el flujo inteligente |

**Respuestas directas:**

1. Método y archivo: ver tabla.
2. Dominio exacto: ver tabla.
3. Campo de `purchase.order` consultado: **Procesados: solo `name`**; **Producto: `partner_ref` OR `name`**.
4. `partner_ref`: usado solo en Producto.
5. Filtro por proveedor: Sí en ambos, pero condicional (`if self.partner_id` / `if self.supplier_id`).
6. Filtro por compañía: **No** en ninguno. Riesgo si hubiera multi-compañía.
7. Filtro por estado: Sí, `['draft','sent','purchase','done']` (Procesados) y `['draft','sent','to approve','purchase','done']` (Producto). Nota: `to approve` no existe en Odoo 18 CE estándar (estados válidos: draft, sent, purchase, done, cancel).
8. `limit=1`: No en Procesados (itera todos); Producto inteligente usa `[:1]` (2341) — **riesgo de vínculo arbitrario si hay varias coincidencias**.
9. Múltiples coincidencias: Procesados → `multi_match` sin vínculo (correcto). Producto → toma la primera (`[:1]`) (riesgo).
10. Sin coincidencia: not_found (ambos); Producto adicionalmente guarda `manual_po_name`.
11. Campo Many2one: `order_id` (Procesados) / `purchase_id` (Producto).
12. Estado y observación visible: `oc_match_status` + `oc_match_note`; en consola solo se proyectan `purchase_id` y `purchase_reference`; la observación solo es visible en la fachada.
13. Momento de ejecución: **Al verificar datos** (`action_verify_data` / workflow). No ocurre al abrir consola ni al enviar a stock.

---

## 10. Análisis del caso real 19827

### Consultas ejecutadas (solo lectura)

**10.1 Registro de guía:**

```sql
SELECT id, name, order_id, oc_reference_raw, oc_reference_norm, oc_match_status,
       oc_match_note, partner_id, date_emission, state, excel_filename,
       guide_pdf_filename, tipo_recepcion
FROM madenat_guia_processing
WHERE name = '19827';
```

| Campo | Valor |
|---|---|
| id | 483 |
| name | 19827 |
| order_id | NULL |
| oc_reference_raw | MC - 2506 - 01 |
| oc_reference_norm | MC250601 |
| oc_match_status | not_found |
| oc_match_note | No se encontró una OC coincidente en el sistema. |
| partner_id | NULL |
| date_emission | 2025-10-02 |
| state | verified |
| excel_filename | FACTURACION PACKING LIST 02-10-2025 (2) MADENAT (cepillado) (1).xlsx |
| guide_pdf_filename | GDE Guía de Despacho 19827.pdf |
| tipo_recepcion | service |

**10.2 Attachments asociados (id 483):**

| Attachment id | Nombre | MIME | Tamaño | store_fname |
|---|---|---|---|---|
| 1563 | guide_pdf_file | PDF | 56.100 B | 62/62a174c4… |
| 1564 | excel_file | XLSX | 20.903 B | 7d/7d04c7e0… |
| 1565 | FACTURACION PACKING LIST…(cepillado) (1).xlsx | XLSX | 20.903 B | 7d/7d04c7e0… |
| 1566 | GDE Guía de Despacho 19827.pdf | PDF | 56.100 B | 62/62a174c4… |

**10.3 Auditoría (madenat.audit_log):**

`id=1664`, `guia_processing_id=483`, `batch_id='intake:84'`, `user_id=2`, `create_date=2026-08-20 18:09:13`, descripción: "Registro creado desde Ingreso Global (madenat_lumber_intake). Tipo de ingreso: procesado. Destino: madenat.guia.processing #483 (19827). Excel: FACTURACION PACKING…xlsx. PDF: GDE Guía de Despacho 19827.pdf. Guía detectada: (sin guía detectada)".

Nota: en el wizard la guía aún no estaba detectada al momento del log; el nombre 19827 se asignó después del `_parse_dispatch_pdf` (`update_vals['name']`, líneas 1223-1224).

**10.4 Contenido del PDF (extraído del binario, sin modificar):**

```
RUT: 77066489-6
GUÍA DE DESPACHO ELECTRÓNICA
COMERCIALIZADORA Y DISTRIBUIDORA FERRAMENTA SPA
… Nº: 19827
Fecha: 02/10/2025
Cliente: MADENAT CHILE LIMITADA … RUT: 76103087-6
Orden: S09496
REFERENCIAS A OTROS DOCUMENTOS
TIPO DE DOCUMENTO FOLIO FECHA MOTIVO
(801) Orden de Compra MC - 2506 - 01 02/10/2025
SFABR00017 SERVICIO DE CEPILLADO MADENAT 43,361000 Metros Cúbicos 19184.00 $ 831.829
Conductor: MARCO PURAN ACIV
Subtotal Neto $ 831.829 / IVA 19% $ 158.048 / Total $ 989.877
T/C U$ 959,19
VOLUMEN TOTAL 36,616 M3
```

**Origen del valor `MC - 2506 - 01`:** el PDF, no el Excel. La línea "(801) Orden de Compra MC - 2506 - 01 02/10/2025" es capturada por el regex Fase A (`madenat_guia_processing.py:2118-2121`), que aísla `MC - 2506 - 01`. El Excel trae `MC-2506-01` (D3), pero nunca se usó porque el PDF tiene prioridad (1282-1287).

**10.5 Búsqueda de `purchase.order`:**

```sql
SELECT id, name, state, partner_id, company_id, partner_ref, origin, date_order
FROM purchase_order
WHERE name ILIKE '%2506%' OR partner_ref ILIKE '%2506%'
   OR regexp_replace(upper(name),'[^A-Z0-9]+','','g') = 'MC250601'
   OR regexp_replace(upper(partner_ref),'[^A-Z0-9]+','','g') = 'MC250601';
```
→ **0 filas**

```sql
SELECT id, name, state, partner_id, company_id, partner_ref, origin, date_order, create_date
FROM purchase_order
WHERE partner_id = 17;  -- Ferramenta
```
→ **0 filas**

```sql
SELECT id, name, vat, is_company, supplier_rank, active
FROM res_partner
WHERE vat ILIKE '%77066489%' OR name ILIKE '%FERRAMENTA%';
```
→ **1 fila:** id=17, name='Ferramenta', **vat=NULL**, is_company=f, supplier_rank=1, active=t

**10.6 Respuestas a las preguntas G:**

1. ID técnico: **483**.
2. Valores de campos OC: ver 10.1.
3. Attachments: ver 10.2.
4. Nombre PDF: **GDE Guía de Despacho 19827.pdf**.
5. Nombre Excel: **FACTURACION PACKING LIST 02-10-2025 (2) MADENAT (cepillado) (1).xlsx**.
6. Texto/celda origen: PDF línea "(801) Orden de Compra **MC - 2506 - 01**"; Excel Packing!D3="MC-2506-01". El persistido proviene del **PDF**.
7. ¿Existe PO con nombre igual/normalizado/Ferramenta? **No en ninguna variante** (0 filas).
8. ¿OCs actuales de Ferramenta (id=17)? **0**.
9. ¿Valores de POs? No aplica (no existen).
10. ¿Orden eliminada o nunca existió? **Nunca existió en esta base** (no hay registro histórico visible en `purchase_order`; 0 filas). No se puede afirmar con esta evidencia si existió y fue eliminada en una limpieza anterior — eso requeriría un backup previo; con los datos actuales es correcto decir que "no existe".
11. ¿Mensaje "No encontrada" correcto? **Sí, correcto** para los datos actuales. La búsqueda se ejecutó, el dominio se aplicó y 0 coincidencias.

**Proveedor — tabla final solicitada:**

| Etapa | Valor de proveedor/tercero | Fuente | Campo técnico | Resultado |
|---|---|---|---|---|
| Documento | COMERCIALIZADORA Y DISTRIBUIDORA FERRAMENTA SPA / RUT 77066489-6 | PDF (líneas 1-2) | texto raw | Presente en PDF |
| Extracción PDF | RUT detectado (77066489-6); nombre amputado a vacío | `_parse_dispatch_pdf` 2325-2353 | `rut_emisor`, `nombre_emisor` | RUT OK; nombre vacío |
| Resolución partner | Busca VAT 77066489-6 → 0; partner 17 existe sin VAT | `action_verify_data` 1245-1275 | `partner_id` | No resuelto |
| Persistencia | partner_id = NULL | guía 483 | `partner_id` | Vacío |
| Consola | partner_id NULL → campo vacío | SQL view `gp.partner_id` | console.partner_id | Vacío (correcto dado origen NULL) |
| Impacto en OC | Sin filtro de proveedor en `_match_purchase_order` | 3221-3222 | — | Búsqueda solo por estado (aun así 0 coincidencias) |

---

## 10A. Auditoría de proveedor / tercero — Procesados

### 10A.1 Mapa de campos de proveedor en Procesados

| Campo técnico | Modelo | Etiqueta visible | Tipo | Significado | Fuente esperada | Quién lo escribe | Quién lo muestra |
|---|---|---|---|---|---|---|---|
| `partner_id` | guia.processing | Proveedor / Transportista | Many2one res.partner | Proveedor comercial / emisor documental (rol no diferenciado) | PDF (RUT/nombre emisor) | `action_verify_data` o manual | Consola, fachada, pickings |
| `rut_emisor` | — (dict parser) | — | str | RUT emisor de la guía | PDF | `_parse_dispatch_pdf` | — (solo log) |
| `nombre_emisor` | — (dict parser) | — | str | Nombre emisor de la guía | PDF | `_parse_dispatch_pdf` | — (solo log) |
| `Cliente` en Excel | — | — | celda | MADENAT (receptor) | Excel | — | — |
| `CONDUCTOR` en PDF | — | — | texto | Transportista (persona) | PDF | parser (no extraído) | — |
| `partner_id` (pickings) | stock.picking | Destinatario | Many2one | Copia `partner_id` de la guía | guía | flujo stock | pickings |

**Clasificación:** el modelo **no distingue** proveedor de origen, prestador de servicio, contratista, transportista, emisor documental ni proveedor comercial de OC. Todo colapsa en `partner_id` con etiqueta "Proveedor / Transportista".

### 10A.2 Extracción desde Guía PDF

```text
Archivo: madenat_guia_processing.py
Método: _parse_dispatch_pdf
Líneas: 2325-2360
Texto inspeccionado: texto plano del PDF (todo concatenado)
Patrón RUT (2328-2331):
  r'R[\.\s]*U[\.\s]*T[\.\s]*[:\s]*(\d{1,2}\.\d{3}\.\d{3}-[\dkK])'   (con puntos)
  r'R[\.\s]*U[\.\s]*T[\.\s]*[:\s]*(\d{7,8}-[\dkK])'                   (sin puntos)
  Excluye 76.103.087 (RUT MADENAT) (2335)
Patrón nombre (2341-2353):
  lines = texto.split('\n')
  potential_name = lines[0]
  Si lines[0] contiene GUIA/ELECTRONICA/FACTURA → lines[1]
  Amputa RUT: re.split(r'R\.?U\.?T\.?|[\d]{1,2}\.[\d]{3}\.', ...)
Valor bruto caso 19827: RUT='77066489-6'; nombre='' (amputado de lines[0])
Campo destino: dict 'rut_emisor'/'nombre_emisor' → update_vals['partner_id']
Fallback: si no rut → nada; si rut sin nombre → warning log; si rut+nombre → crea partner
```

**Defecto confirmado:** en el PDF 19827, `lines[0]='RUT: 77066489-6'` y `lines[1]='GUÍA DE DESPACHO ELECTRÓNICA'`; la evaluación `any(x in potential_name.upper() for x in ['GUIA','ELECTRONICA',...])` NO se aplica sobre lines[0] (que es RUT), por lo que toma lines[0], la amputa → vacío. La condición `clean_name and len(clean_name) > 2` (2352) nunca se cumple. Además `lines[2]` (el nombre real) nunca se consulta.

### 10A.3 Extracción desde Packing Excel

El parser de Procesados (`_parse_packing_excel` / `_find_oc_reference_in_excel`) **no busca proveedor/RUT/contratista/planta**. El Excel 19827 solo contiene Cliente=MADENAT (receptor), sin RUT ni emisor. No existe lógica de proveedor desde Excel.

### 10A.4 Resolución a `res.partner`

```text
Método: action_verify_data (1245-1275), usando _parse_dispatch_pdf
Criterio: search([('vat','=','77066489-6')], limit=1)
Normalización: ninguna (RUT tal como viene)
Cero coincidencias: si supplier_name válido → crea partner; si no → NO crea y deja NULL
Múltiples coincidencias: limit=1 toma la primera
Evidencia 19827: partner 17 existe sin VAT → search por VAT = 0 → creación falla por nombre vacío → NULL
```

### 10A.5 Proyección a la consola

```text
madenat.guia.processing.partner_id (NULL en 19827)
→ SQL view (intake_console.py:184): gp.partner_id AS partner_id   [mapeo directo, SIN bug]
→ madenat.lumber.intake.console.partner_id
→ XML consola (intake_console_views.xml:146): <field name="partner_id" string="Proveedor"/>
```

**Conclusión:** la consola **no tiene bug**: el mapeo es correcto. El vacío en consola es reflejo fiel del NULL en origen. El defecto está en la extracción→resolución del proveedor en el core.

### 10A.6 Diagnóstico proveedor (10 casos)

| Caso | Respuesta |
|---|---|
| 1. ¿Existe en PDF pero parser no lo extrae? | **Sí, parcialmente**: extrae RUT, no extrae nombre (`lines[1]`/`lines[2]` no se usan). El RUT sí se extrajo. |
| 2. ¿Existe en Excel pero parser no lo extrae? | N/A — el Excel no contiene proveedor. |
| 3. ¿Se extrae pero no se persiste? | No aplica: no se extrae nombre; sin nombre no se crea/resuelve partner. |
| 4. ¿Se persiste pero no se proyecta? | No aplica (persistido NULL). |
| 5. ¿Consola con compute/SQL defectuoso? | **No** — SQL view correcta. |
| 6. ¿Extraído como texto pero no resuelto a res.partner? | **Sí**: RUT detectado pero 0 match por VAT (partner 17 sin VAT); sin nombre no se crea. |
| 7. ¿Resuelto pero dominio/permiso/active_test lo oculta? | No. |
| 8. ¿Campo equivocado en la consola? | No; el mismo campo `partner_id`. |
| 9. ¿Dato no viene y no hay captura manual? | El dato SÍ viene en PDF. La captura manual existe en la fachada (campo editable `partner_id`). |
| 10. ¿Regla de negocio distingue roles? | **No existe**: un único `partner_id` "Proveedor / Transportista". |

---

## 10B. Relación entre proveedor y vinculación de OC

1. **¿La conciliación filtra por partner?** Sí, condicionalmente (`_match_purchase_order:3221-3222`): `if self.partner_id: domain.append(('partner_id','=',...))`.
2. **¿Partner vacío provoca automáticamente "Pendiente"?** No directamente. Con partner NULL se busca **todas** las POs en estados permitidos y se compara por `name` normalizado. En el caso 19827 eso dio 0 coincidencias. Si la OC existiera y su `name` coincidiera, se vincularía SIN filtro de proveedor.
3. **¿Se puede vincular sin proveedor la OC?** Sí, si el `name` de la PO coincide con el normalizado. Riesgo: si dos proveedores usan el mismo `name` de OC, la selección es arbitraria (se vincularía una sola).
4. **¿Debe permitirse coincidencia documental sin partner marcada para revisión?** Es una decisión de negocio; hoy el sistema vincula directamente (single_match) sin exigir partner. Recomendación: exigir partner para auto-match, y si no hay partner, dejar `not_found`/`needs_review` (ver solución).
5. **¿Riesgo de vincula rOC equivocada al eliminar filtro?** **Sí**, en multi-proveedor con nombres de OC repetidos (`MC250601` podría existir para dos proveedores). El código Procesados maneja bien multi_match (no vincula), pero si solo existe UNA PO con ese name y es de otro proveedor, la vincularía igual.
6. **¿La solución debe separar extracción de referencia OC, extracción de proveedor, conciliación y advertencia?** Sí. Hoy están acopladas: la resolución de proveedor depende del parser PDF y de la creación de partner; la conciliación depende de `partner_id`. Separarlas reduce riesgo y permite advertencias diferenciadas.

---

## 11. Matriz de diagnóstico

| Situación detectada | Evidencia | Impacto | Severidad | Corrección potencial |
|---|---|---|---|---|
| OC extraída correctamente | `oc_reference_raw='MC - 2506 - 01'`; `_parse_dispatch_pdf` 2118-2145 | Ninguno — funciona | Baja | Sin corrección |
| OC normalizada correctamente | `oc_reference_norm='MC250601'`; `utils_uom.py:214-230` | Ninguno — funciona | Baja | Sin corrección |
| OC no vinculada porque no existe | 0 filas en `purchase_order` para MC250601/2506/Ferramenta | Correcto para datos actuales | Informativa | Crear la OC real o importarla; NO autocrear |
| Búsqueda OC sin filtro de proveedor cuando partner NULL | `_match_purchase_order:3221-3222` | Riesgo de falsos positivos multi-proveedor | **Media** | Exigir partner para auto-match o marcar `needs_review` |
| Proveedor no resuelto (DEFECTO) | PDF trae RUT 77066489-6 + nombre; parser amputa nombre a vacío; partner 17 sin VAT; `partner_id=NULL` | Trazabilidad, consola vacía, sin filtro OC, sin partner en pickings/costeo | **Alta** | Corregir lectura del nombre emisor y resolución por nombre+RUT |
| nombre del emisor mal extráido (lines[0]) | `madenat_guia_processing.py:2341-2353` | Causa raíz del proveedor vacío | **Alta** | Saltar a lines[1] cuando lines[0] sea solo RUT |
| Partner existe sin VAT | `res_partner id=17 name='Ferramenta' vat=NULL` | Impide emparejamiento por RUT | Media | Complementar VAT en maestro o buscar por nombre normalizado |
| Sin auditabilidad de fuente de OC (guía/packing) | No existe campo `oc_source` ni log visible | No se puede saber después qué documento aportó la OC | Media | Añadir campo/log de fuente en persistencia |
| Discrepancia PDF vs Excel silenciosa | `action_verify_data:1282-1309` no compara | Puede enmascarar errores de fuente | Media | Comparar y registrar advertencia si normalizados difieren |
| Conciliación solo por `name` en Procesados | `_match_purchase_order:3228-3230` | POs con OC en `partner_ref` no se encuentran | Media | Añadir `partner_ref` al matching (como Producto) |
| Sin filtro `company_id` en conciliación | dominio 3220-3223 | En multi-compañía podrían vincularse OCs de otra empresa | Media | Añadir `company_id` |
| Consola no expone `oc_reference_raw` de Procesados | SQL view `COALESCE(po.name,'')` (183) | "OC documento" vacío aunque exista referencia documental | Media | COALESCE(po.name, gp.oc_reference_raw) |
| Nota de match no visible en consola | `oc_match_note` solo en fachada | Operador en consola no ve el porqué del estado | Baja | Exponer nota o tooltip |
| Producto inteligente toma primera OC con `[:1]` | `lumber_reception.py:2338-2341` | Vínculo arbitrario si múltiples coincidencias | Media | Contar coincidencias → `multi_match` |

---

## 12. Solución recomendada

**Principal (única):** corregir la **resolución de proveedor en Procesados** y, como consecuencia, endurecer la conciliación de OC. No crear parser universal, no autocrear OCs.

### Qué archivos cambiaría

1. `custom_addons/madenat_lumber_core/models/madenat_guia_processing.py` — método `_parse_dispatch_pdf` (líneas 2341-2353) y `action_verify_data` (líneas 1245-1275).

### Qué métodos cambiaría

1. **`_parse_dispatch_pdf` (extracción del nombre emisor):** cuando `lines[0]` sea exclusivamente RUT (o tras amputación quede vacío), usar `lines[1]`, y si `lines[1]` es "GUÍA DE DESPACHO ELECTRÓNICA", usar `lines[2]`. Es decir, buscar la primera línea que contenga una razón social (≥2 palabras, sin keywords GUIA/ELECTRONICA/FACTURA/REFERENCIAS) en las primeras 5 líneas.
2. **`action_verify_data` (resolución de partner):** 
   - Buscar por VAT normalizado.
   - Si no existe, buscar por **nombre normalizado** del emisor (`icontains` sobre `name` con limpieza).
   - Si tampoco, crear partner con `name` (de la nueva extracción) + `vat` + `is_company=True` + `supplier_rank=1` — **mantiene la regla MADENAT de no inventar OCs, pero sí resuelve el tercero documental que es trazable**.
   - Si el partner existe pero sin VAT y encontramos el VAT en el PDF, actualizar `vat` (operación de completitud de maestro, no creación).
3. **`_match_purchase_order` (conciliación endurecida, sin romper Intake):**
   - Mantener `oc_reference_raw` intacto (nunca se sobrescribe).
   - Comparar **`name` OR `partner_ref`** normalizados (alinear con Producto).
   - Si `partner_id` está resuelto: filtrar por él (sigue la regla).
   - Si `partner_id` está vacío: **no auto-vincular**; marcar `oc_match_status='not_found'` (o nuevo estado `needs_review`) con nota explícita "Proveedor no resuelto; revisar manualmente". Esto evita falsos positivos multi-proveedor.
   - No usar `limit=1`; mantener lógica single/multi/not-found.

### Cómo preserva fuente documental

`oc_reference_raw` conserva `MC - 2506 - 01` tal cual viene del PDF. La solución no toca esa escritura.

### Cómo normaliza sin falsos positivos

Mantiene `normalize_oc_key` (AD-44) para el matching, pero añade `partner_ref` como segundo criterio y exige proveedor para auto-match. Esto reduce falsos positivos porque el filtro de proveedor se vuelve obligatorio.

### Cómo diferencia extracción, conciliación y advertencia

- **Extracción** → `_parse_dispatch_pdf` (campo `oc_reference_raw`, `rut_emisor`, `nombre_emisor`).
- **Concilación** → `_match_purchase_order` (estado `oc_match_status` + `oc_match_note`).
- **Advertencia** → se mantiene la alerta HTML no bloqueante en consola/fachada, y se agrega a la matriz de diagnósticos un nuevo sub-estado `needs_review` distinguible de `not_found` (OC existe como referencia documental pero no se pudo conciliar con seguridad).

### Cómo mantiene Intake flexible

Intake (consola/wizard) no cambia: sigue mostrando `partner_id`, `purchase_id`, `purchase_reference`, `oc_pending`. Solo se mejora la fuente de datos (proveedor resuelto) y se expone la nota de match en la consola para trazabilidad.

### Cómo evita crear OCs automáticamente

No se toca `_create_basic_purchase_order` ni `action_create_purchase_order_from_document`; la autocreación permanece desactivada (como en el patch 2026-06-18). La solución solo resuelve el **partner documental**, que es un tercero trazable del PDF, no una OC.

### Cómo protege Producto y Procesados sin forzar parsers idénticos

La solución se limita a Procesados (`_parse_dispatch_pdf` + `action_verify_data` + `_match_purchase_order`). Producto conserva `reception_parser` + `_find_or_create_po_intelligent`. El único punto compartido es `normalize_oc_key` (ya existente, AD-44).

### Impacto y rollback

- **Impacto:** la guía 19827 (y todas las guías Procesados nuevas o re-verificadas) resolvería `partner_id=17` (Ferramenta) con VAT 77066489-6, la consola mostraría el proveedor, y `_match_purchase_order` filtraría por Ferramenta. Como no existe la PO, seguiría `not_found`, pero ahora con trazabilidad correcta.
- **Rollback:** revertir exactamente los dos métodos en `madenat_guia_processing.py` (los cambios son locales y reversibles); no hay cambios de esquema, migración ni datos.

---

## 13. Alternativas descartadas

1. **Parser universal completo (un solo parser Producto/Procesados).**
   Motivo técnico: los dos flujos tienen estructuras documentales, campos (`purchase_id` vs `order_id`, `manual_po_name` vs nulla), reglas de matching (name vs name+partner_ref) y momentos de ejecución distintos (workflow vs action_verify_data). Unificar obligaría a refactorizar `madenat_lumber_core` sin evidencia suficiente y con alto riesgo de regresión; viola la regla de no tocar core sin evidencia.

2. **Autocreación de la OC detectada (crear purchase.order automática cuando no existe).**
   Motivo técnico: el propio código la desactivó explícitamente (patch 2026-06-18, `lumber_reception.py:2372-2377`) por generar OCs sin supervisión, con valores hardcode y sin trazabilidad. Además viola la regla MADENAT "el sistema no debe inventar ni crear automáticamente una OC sin trazabilidad suficiente". Para el caso 19827 no habría datos suficientes (sin `partner_id` resuelto no se puede crear la PO de Ferramenta).

---

## 14. Plan mínimo de implementación

*No implementar todavía. Orden de ejecución cuando se apruebe:*

1. **Cambiar `_parse_dispatch_pdf`** en `madenat_guia_processing.py` para lectura robusta del nombre emisor (saltar líneas RUT/GUIA/ELECTRONICA).
2. **Cambiar `action_verify_data`** para resolver/crear partner por VAT→nombre→creación, y completar VAT faltante.
3. **Cambiar `_match_purchase_order`** para comparar `name`+`partner_ref` y exigir proveedor para auto-match.
4. **Tests requeridos:**
   - `test_guia_processing.py`: nuevos casos para parser con lines[0]=RUT (simular PDF 19827) y con emisor en lines[1]/[2].
   - Test de `_match_purchase_order`: con partner NULL → no auto-vincular; con partner → filtrar; con name y partner_ref; multi-match.
   - Test de normalización: `MC - 2506 - 01`/`MC-2506-01`/`MC 2506 01` → `MC250601`.
5. **Pruebas con guía y packing reales:** re-ejecutar `action_verify_data` sobre una copia de la guía 19827 (o una nueva guía de prueba) con el PDF/Excel reales y verificar `partner_id=17` y `oc_match_status`.
6. **Prueba de OC existente:** crear (solo en entorno de prueba, no producción) una `purchase.order` con `name='MC - 2506 - 01'` y partner 17 → debe auto-vincular `single_match`.
7. **Prueba de OC inexistente:** con los datos actuales → `not_found` con nota correcta.
8. **Prueba de formatos equivalentes:** PO con name `MC-2506-01` debe matchear la referencia `MC250601`.
9. **Prueba de fuentes contradictorias:** PDF `MC - 2506 - 01` vs Excel `MC-9999-99` → debe persistir la del PDF y registrar advertencia si se implementa la detección de discrepancia.
10. **Prueba sin OC documental:** guía sin OC → `not_found` con nota "No existe referencia documental de OC para buscar."
11. **Rollback:** revertir los cambios de los 3 métodos; los tests de regresión existentes (`test_guia_processing.py`, `test_lumber_reception.py`) deben pasar intactos.

---

## 15. Decisiones fuera de alcance

Explícitamente NO son parte de esta auditoría ni se proponen aquí:

- Rediseño de la consola global (`madenat.lumber.intake.console`).
- Cambios de navegación lectura/modificación (fachadas Intake).
- Parser universal completo para Producto y Procesados.
- Creación automática de `purchase.order`.
- Costeo, valorización, pagos o cierre financiero.
- Cambios en el envío a stock (`action_send_to_stock`, `action_validate`, `action_confirm_reception`).
- Modificaciones a `madenat_lumber_core` más allá de los 3 métodos citados en la solución (y solo con evidencia aprobada).
- La definición formal de roles separados (proveedor de madera, prestador de servicio, transportista, proveedor comercial de OC) queda pendiente de una decisión de negocio con datos de costeo; no se crean campos ni modelos nuevos en esta auditoría.

---

## Anexo: evidencia de consultas SQL ejecutadas (solo lectura)

1. Guía 19827 (id=483) — campos OC y proveedor. Resultado: ver sección 10.1.
2. `purchase_order` con `2506`/`MC250601` — 0 filas.
3. `purchase_order WHERE partner_id=17` — 0 filas.
4. `res_partner` con `77066489`/`FERRAMENTA` — 1 fila (id=17, vat=NULL).
5. `ir_attachment WHERE res_model='madenat.guia.processing' AND res_id=483` — 4 filas (ver 10.2).
6. `madenat_audit_log WHERE guia_processing_id=483` — 1 fila (ver 10.3).
7. Inspección del binario PDF (56.100 B) y Excel (20.903 B) extraídos del filestore — textos citados en secciones 10.4 y 6.
8. `_check_19846.sh`/`_check_19846.py` revisados para confirmar patrón de consultas (no modificados).

**Limpieza:** los binarios temporales `/tmp/gde_19827.pdf` y `/tmp/packing_19827.xlsx` son copias locales de solo lectura para auditoría; pueden eliminarse sin afectar la base.