# INFORME FRENTE A — LECTURA Y CONTINUACIÓN DEL INGRESO
### Auditoría técnica de solo lectura · MADENAT · Odoo 18 CE

| Dato | Valor |
|---|---|
| Fecha | 2026-10-23 |
| Alcance de estudio | `madenat_lumber_intake`, `madenat_ingestion_engine` |
| Núcleo (solo lectura, para trazar efectos) | `madenat_lumber_core` 18.0.6.24.0 |
| Workspace | `/home/viruco/dev-stack/odoo/odoo-18-ce` (no es repo git) |
| Repo git real | `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons` — HEAD `e672fc4`, rama `feat/guia-correccion-documental-preservada-20261002` |
| Base de datos | `madenat_test` (contenedor `odoo18_db`), acceso **solo SELECT** |
| Módulos instalados | `madenat_lumber_intake` 18.0.0.20.0 · `madenat_ingestion_engine` 18.0.1.4.0 · `madenat_lumber_core` 18.0.6.24.0 |
| Muestras usadas (solo lectura) | `muestras_documentos_ingreso/guias_pdf/Guia 40030.pdf`, `muestras_documentos_ingreso/excel_packing/40030.xls` |

**Reglas aplicadas:** toda afirmación lleva `[VERIFICADO]`, `[HIPÓTESIS]` o `[NO VERIFICABLE]`.
No se modificó ningún archivo de código, vista, dato ni manifiesto; no se ejecutaron upgrades ni reinicios.
Las únicas escrituras son este informe y `INFORME_FRENTE_B.md`.

**Índice:** A1 · A2 · A3 · A4 · A5 · A6 · A7 · A8 · A9 · Cierre.

---

## A1 — Mapa REAL de "Leer documento" y "Continuar ingreso" por tipo × perfil × modalidad

**Pregunta.** ¿Qué se lee, qué se guarda en el wizard, qué se pasa al destino y qué decide el núcleo, en cada combinación tipo (Producto/Procesado) × perfil (`metric`/`f5085`/`f1550`) × modalidad (normal/volumen)?

### A1.1 Hechos verificados — despacho general

- `action_preview_document` (`madenat_lumber_intake/models/intake_wizard.py:579`) bifurca por modalidad: `volume` → `_preview_volume()` (`:583-584`); normal → `_classify_normal_document()` (`:588`) y luego rama Producto/Procesado (`:594`).
- `action_route_document` (`:685`) ejecuta primero la idempotencia `_existing_target()` (`:690-692`, definida `:766-774`), después `_guard_route_document()` (`:694`) y finalmente deriva: `volume` → `_route_granel()` (`:697-698`), `producto` → `_route_producto()` (`:701-702`), `procesado` → `_route_procesado()` (`:703-704`). Si el tipo no está definido lanza `UserError` (`:706-710`).
- `_guard_route_document()` (`:712-764`) exige en **todas** las rutas: patio interno (`:715-723`); documentos (`:727-738`, normal exige PDF **y** Excel, volumen exige al menos uno); estado (normal/Producto exige `state='previewed'`, `:741-746`); y coherencia de perfil sólo en modalidad normal (`:753-764`).

### A1.2 Modalidad NORMAL / Producto

- **Lee**: el **texto del PDF** para clasificar (`_classify_normal_document`, `:549-577`: `_extract_pdf_text` en `:560-561`) y el **Excel** con el engine (`:622-624`) **sin `column_profile`**, es decir con autodetección.
- **Guarda**: `state='previewed'`, `preview_data` (texto con las 5 primeras líneas), `preview_line_count`, `preview_total_volume_m3`, `preview_guide_no`, `preview_warnings`, `error_message=False` (`:640-670`). **No guarda las líneas estructuradas**: `preview_data` es un `str`.
- **Pasa al destino**: crea `lumber.reception` con `pdf_file`, `pdf_filename`, `excel_file`, `excel_filename`, `ingestion_profile`, `location_id` (`:782-789`) y llama `reception.action_process_documents()` (`:791`).
- **Decide el núcleo**: `action_process_documents` → `reception_workflow.py:87` `parser.parse_excel(excel_bytes, ingestion_profile=reception.ingestion_profile)`. Aquí —y sólo aquí— el perfil tiene efecto de lectura: `_process_dataframe` (`reception_parser.py:224`, `:386-388`) resuelve `fmt = _resolve_for_profile(formato)` (`:433`) y toma `export_rule = fmt['export_rule_outcome']` (`:515`).

### A1.3 Modalidad NORMAL / Procesado

- **"Leer documento" no extrae nada**: escribe `preview_data=False`, `preview_line_count=0`, `preview_total_volume_m3=0.0`, `preview_guide_no=False`, `preview_warnings=False` (`:594-618`) y devuelve una notificación informativa.
- **Pasa al destino**: crea `madenat.guia.processing` con `tipo_recepcion='service'`, `intake_direct_stock=True`, `assignment_location_id`, `guide_pdf_file`, `guide_pdf_filename`, `excel_file`, `excel_filename`, `ingestion_profile` (`:814-823`) y llama `guia.action_verify_data()` (`:827`).
- **Decide el núcleo**: `action_verify_data` (`madenat_guia_processing.py:2141`) llama `_parse_packing_excel` (`:2158`) → `_parse_excel_data_core` (`:3923`, invocado `:3677`), que usa `detect_excel_table_across_sheets(sheets, flow='procesado')` (`:3930`) y **no recibe ni consulta `ingestion_profile`**. Sus únicas lecturas del perfil en toda la guía son: producto maestro (`:2161-2162`), F3 `vol_physical_real_m3`/`physical_status` (`:680-693`) y producto en guía granel (`:1750`, `:1805`).

### A1.4 Modalidad VOLUMEN (granel)

- `_preview_volume()` lee el PDF si existe, si no el Excel (`:440-445`) con `extract_document(source_bytes, source_filename)` (`:448`), **sin perfil**, y resuelve el volumen con `_resolve_granel_volume()` (`:450`); persiste `preview_*` y `detalle_aplicado`/`detalle_motivo` (`:504-523`).
- `_route_granel()` (`:991`) **vuelve a leer ambos documentos por separado** (`_read_volume_document`, `:997-998`, que llama `extract_document` sin perfil, `:843-858`), calcula `volume_pdf_m3`/`volume_excel_m3` (`:1004-1005`) con `_document_volume` (`:860-881`), concilia (`:1007-1008`), construye detalle documental (`:1011-1018`) y crea la guía con `tipo_recepcion='granel'`, `intake_direct_stock=False` (`:1047-1051`). **No envía `ingestion_profile`**: el `vals` de `:1047` no lo incluye.

### A1.5 El perfil: de dónde sale y adónde va

`[VERIFICADO]` El puente entre los códigos del engine y el selection del wizard existe **en un solo sentido**, engine → wizard:

- `_onchange_suggest_ingestion_profile` (`:231-293`) llama `extract_document(excel_bytes, rec.excel_filename)` **sin perfil** (`:259-261`), lee `result.detected_profile_code` (`:265`) y escribe el selection: `packing_metrico_aserrada` → `metric` (`:267-269`); `packing_imperial_blanks` → `f5085` si el nombre contiene `blank`/`clear`, `f1550` si contiene `s2s` (`:271-280`), y si no hay pista **advierte sin cambiar** (`:282-293`).
- El sentido inverso (selection → `column_profile`) **no existe** en ningún punto del módulo: `grep -n 'ingestion_profile' madenat_lumber_intake/models/intake_wizard.py` devuelve sólo las declaraciones (`:45`), la sugerencia (`:232-280`), la coherencia (`:321`, `:349`), la copia a recepción (`:787`) y a guía (`:822`). Ninguna llamada a `extract_document` recibe un dict de perfil (`grep -n 'extract_document' madenat_lumber_intake/models/intake_wizard.py` → `:259`, `:310`, `:448`, `:624`, `:856`; todas con dos argumentos).
- El engine no conoce los códigos `metric`/`f5085`/`f1550`: `DEFAULT_PROFILES = [PACKING_METRICO_ASERRADA, PACKING_IMPERIAL_BLANKS]` (`ingestion_profiles.py:107`) con `code`s `packing_metrico_aserrada` (`:36`) y `packing_imperial_blanks` (`:72`).
- Consecuencia: el perfil es hoy **una etiqueta de negocio derivada de la lectura**, no un parámetro de la lectura. Sólo tiene efecto de cálculo aguas abajo, y sólo en Producto.

### A1.6 Contradicciones con la documentación del módulo `[VERIFICADO]`

| # | Documento y afirmación | Código real |
|---|---|---|
| 1 | `madenat_lumber_intake/README.md`: al adjuntar se sugiere `procesado` si el nombre contiene `cepillado`/`servicio`/`proceso`/`maquila` | `_onchange_suggest_tipo_ingreso` (`:215-229`) **no clasifica por nombre**: sólo limpia indicadores (`:228-229`) y, en volumen, fija `granel` (`:222-225`). La clasificación ocurre al leer, por texto del PDF (`:549-577`) |
| 2 | README: «Excel obligatorio y PDF opcional» | En normal ambos son obligatorios (`:733-738`) |
| 3 | README: `ingestion_profile` = «solo preview de producto» | Se copia a Recepción (`:787`) y a Guía (`:822`); el preview **no** lo usa (`:622-624`) |
| 4 | README: `assignment_location_id` = «solo procesado» | Se exige en todas las rutas (`:715-723`) |
| 5 | Pista del encargo: «el perfil sólo aplicaría a Producto» | Cierto en el efecto aguas abajo; **incompleto**: tampoco en Producto el perfil gobierna la lectura, porque el preview autodetecta (`:622-624`) y el perfil se limita a `lumber.ingestion.format` (`reception_parser.py:433`, `:515`) |
| 6 | Pista del encargo: «en Procesado "Leer documento" no extrae nada» | **Confirmado** (`:594-618`) |

### A1.7 Hipótesis
- `[HIPÓTESIS]` La sugerencia por contenido (`:231-293`) se añadió después y **sustituyó** a la sugerencia por nombre, dejando el README desactualizado. Se confirmaría con `git log -S '_onchange_suggest_ingestion_profile'`, no ejecutado (fuera del alcance de solo lectura del informe).
- `[HIPÓTESIS]` El selection se concibió para el núcleo (producto maestro por perfil, `madenat_ingestion_config.py:439-481`) y no para el engine; de ahí que no exista traducción inversa.

### A1.8 Impacto en otros perfiles
`[VERIFICADO]` `extract_document` se invoca sin perfil en cuatro puntos del intake (preview Producto `:624`, coherencia `:310-312`, preview volumen `:448`, volumen `:856`) y en la sugerencia `:259`. Cualquier cambio en `column_aliases` o `source_units` de los dos perfiles del engine afecta a **todos** esos puntos a la vez, en las tres modalidades. `[HIPÓTESIS]` Los flujos de Blanks/Arauco/JCE/BYC que no pasan por el wizard no se ven afectados por el selection, pero sí por el engine si lo invocan sin perfil.

### A1.9 Conclusión
El mapa real es: **el perfil elegido no participa en ninguna lectura**. "Leer documento" en Producto autodetecta con el engine y guarda un resumen textual; en Procesado no lee; en Volumen lee ambos documentos por separado y concilia. El perfil viaja como dato a Recepción y Guía y sólo cambia el resultado en Producto (regla de exportación y producto maestro de la línea). La traducción `metric/f5085/f1550` → perfil del engine no existe en ninguna dirección salvo la sugerencia inversa.


---

## A2 — Trazabilidad del perfil elegido: dónde vive, a qué se copia y dónde se pierde

**Pregunta.** ¿Dónde vive el campo, a qué registros se copia, dónde se pierde? ¿Qué acepta el núcleo al crear la recepción o la guía?

### A2.1 Declaración y defaults `[VERIFICADO]`
- **Wizard**: `ingestion_profile = fields.Selection([('f1550',…),('f5085',…),('metric',…)], default='metric')` (`intake_wizard.py:45-54`).
- **Recepción**: mismo selection, `required=True, default='f5085', tracking=True` (`lumber_reception.py:975-981`).
- **Guía**: mismo selection, `required=True, default='f5085', tracking=True` (`madenat_guia_processing.py:989-994`).
- **Discrepancia de default**: el wizard propone `metric`, el núcleo `f5085`. En la ruta del wizard el default del núcleo no llega a aplicarse (el valor siempre viaja explícito en `create`), pero sí se aplica a registros creados por otras vías.

### A2.2 Copia a los destinos `[VERIFICADO]`
| Destino | ¿Se copia? | Evidencia |
|---|---|---|
| `lumber.reception` (Producto) | Sí, en `create` | `intake_wizard.py:787` |
| `madenat.guia.processing` (Procesado) | Sí, en `create` | `intake_wizard.py:822` |
| Guía granel (Volumen) | **No** | `_route_granel` `:1047-1051` no incluye la clave; la guía nace con el default del núcleo `f5085` (`madenat_guia_processing.py:993`) |

`[VERIFICADO]` El núcleo lo acepta sólo como campo de creación/escritura: no hay parámetro de perfil en `action_process_documents()` ni en `action_verify_data()`; el parser lo lee del propio registro (`reception_workflow.py:87`).

### A2.3 Efectos reales del perfil en el núcleo

| # | Efecto | Evidencia | ¿Afecta a Procesado? |
|---|---|---|---|
| 1 | **Validación documental por perfil**: `f1550` exige Excel; `f5085` exige PDF; `metric` sin restricción | `lumber_reception.py:983-1011` (`_check_required_documents`, sólo al salir de `draft`) | No |
| 2 | **Regla de exportación por línea** (`_resolve_for_profile` → `export_rule_outcome`) | `reception_parser.py:433`, `:515` → `lumber_reception.py:2207` | No |
| 3 | **Producto maestro de la línea** | `madenat_guia_processing.py:2161-2162`, `:1750`, `:1805`; regla en `madenat_ingestion_config.py:439-481` | **Sí** |
| 4 | **F3 — volumen físico real** sólo `f5085` con `length_ft > 0.1` | `madenat_guia_processing.py:680-693` | **Sí** |
| 5 | **Espejo documental** (fracción vs crudo) | `lumber_reception.py:159-176` | No |
| 6 | Patio de asignación | No depende del perfil (`intake_wizard.py:715-723`) | Sí, por patio |

### A2.4 El sincronizador perfil → regla de exportación está muerto `[VERIFICADO]`
- `_onchange_ingestion_profile_to_export_rule` está definido en **`lumber.reception.line`** (`lumber_reception.py:114-139`) y **no lleva decorador `@api.onchange`** (el campo `export_calculation_rule` termina en `:112` y el `def` arranca en `:114`).
- Además lee `self.ingestion_profile` (`:129`, `:139`), campo que **no existe en la línea**: vive en la cabecera (`:975`) y la línea lo referencia como `reception_id.ingestion_profile` (`:159`, `:163`, `:490`, `:524`, `:570`, `:831`).
- Por tanto no lo invoca la UI (no es onchange) ni el ORM (no es compute/constraint). El valor efectivo lo escribe el staging: `'export_calculation_rule': item.get('export_rule', 'metric')` (`lumber_reception.py:2207`), con `item['export_rule']` = `fmt['export_rule_outcome']` (`reception_parser.py:515`).
- **Riesgo asociado**: si `lumber.ingestion.format` no resuelve regla para el formato detectado, el fallback es `'metric'` (`:2207`) con independencia del perfil elegido. El valor efectivo por recepción se mide en A9.

### A2.5 Dónde se pierde el perfil en Procesado (caso 40030) `[VERIFICADO]`
- El espesor nominal se toma del propio espesor físico si no hay columna nominal: `'espesor_nominal_mm': row.get('espesor_nominal_mm', 0.0) or row.get('Espesor', 0.0)` (`madenat_guia_processing.py:2210`).
- El perfil `f1550` (S2S, nominal 45 mm) **no interviene** en esa asignación, ni la glosa del PDF («…Cepillada Calidad Col A de 45mm…»). El nominal queda igual al físico (38.0 mm en la guía 40030) y con él se calculan volumen de compra y MBF.



### A2.6 Separación (a) resoluble en intake/engine vs (b) dependencia del núcleo

| # | Necesidad | ¿Dónde se resuelve? | Evidencia |
|---|---|---|---|
| 1 | Traducir el perfil elegido a `column_profile` para la lectura | **(a)** intake: el engine ya acepta `column_profile` (`document_extractor.py:1510`, `:1516-1517`, `:1537`) | `intake_wizard.py:259-261`, `:310-312`, `:448`, `:624`, `:856` |
| 2 | Que Procesado lea con el engine/perfil en lugar de un parser paralelo | **(a)** intake + **(b)** núcleo: hoy el wizard sólo llama `action_verify_data()` sin parámetros (`:827`) | `madenat_guia_processing.py:2141-2168`, `:3923-3930` |
| 3 | Que `export_calculation_rule` siga al perfil | **(b)** núcleo: el onchange está muerto (`lumber_reception.py:114-139`) y el staging sobrescribe (`:2207`) | `:2207`, `reception_parser.py:515` |
| 4 | Que Volumen transporte perfil | **(a)** intake: añadir clave en `_route_granel` | `:1047-1051` |
| 5 | Que Procesado aplique nominal de compra desde perfil/glosa | **(b)** núcleo: la asignación está en `:2210`; intake podría reescribir el campo post-verificación, pero el cálculo ya se ejecutó | `:2210` |

### A2.7 Hipótesis
- `[HIPÓTESIS]` El onchange se escribió cuando `ingestion_profile` vivía en la línea y se movió a la cabecera sin ajustar el decorador ni la referencia. Confirmable con `git log -S '_onchange_ingestion_profile_to_export_rule'` (no ejecutado: el hecho verificable es la ausencia de decorador y de campo).
- `[HIPÓTESIS]` El default `metric` del wizard (mayoría de guías métricas) convive con el `f5085` del núcleo por razones históricas.

### A2.8 Impacto en otros perfiles
`[VERIFICADO]` El perfil gobierna cálculos de línea en Producto para **los cuatro perfiles** (`lumber_reception.py:490`, `:506-524`, `:561-570`, `:820-831`). Cualquier cambio en la semántica del selection (valores, defaults) altera volumen físico, volumen de exportación y espejo documental de todo el flujo Producto. En Procesado el impacto se limita a producto maestro y F3.

### A2.9 Conclusión
El perfil se copia bien a Recepción y Guía, no se copia en Volumen, y su efecto se reparte en tres planos: validación documental (sólo Recepción), lectura/regla de exportación (sólo Producto) y producto maestro/F3 (Procesado). El sincronizador perfil→regla no se ejecuta nunca y el default difiere entre wizard y núcleo.

---

## A3 — Clasificador de tipo: nombre de archivo vs texto del PDF

**Pregunta.** ¿Hay dos mecanismos? ¿Qué señales usa cada uno? ¿Cuál es el valor vigente de `madenat.tipo_ingreso_keywords` y qué pasa con «Cepillada», «CEPILLADO», «PINO CEP. SECO LATERAL» y «SERVICIO CEPILLADO»?

### A3.1 Hechos verificados

**(1) Ya NO existe clasificación por nombre de archivo** `[VERIFICADO]`
- `_onchange_suggest_tipo_ingreso` (`intake_wizard.py:215-229`) se dispara con `excel_filename`, `pdf_filename`, `pdf_file` y `excel_file` (`:215`) pero **no clasifica**: en modalidad volumen fija `granel` (`:222-225`); en normal sólo limpia `tipo_ingreso_auto_detectado` y `classification_result` (`:228-229`). El docstring lo declara (`:217-220`).
- El único uso del nombre de archivo que queda es el desempate del **perfil** imperial (`blank`/`clear`/`s2s`, `:271-280`), no del tipo de ingreso.

**(2) El clasificador vigente es por texto del PDF, por subcadena** `[VERIFICADO]`
- `_classify_normal_document` (`:549-577`): extrae el texto del PDF (`:557-563`), lo pasa a `casefold()` (`:565`) y decide `procesado` si **alguna keyword está contenida como subcadena** (`:566`). Escribe `tipo_ingreso`, `tipo_ingreso_auto_detectado` y `classification_result` (`:567-577`). No asigna `granel` (docstring `:550-551`).
- Se ejecuta siempre al pulsar "Leer documento" en modalidad normal (`:588`), por lo que **pisa** cualquier selección manual previa de `tipo_ingreso`.

**(3) Valor vigente del parámetro en BD** `[VERIFICADO]`
```
SELECT key, value FROM ir_config_parameter WHERE key='madenat.tipo_ingreso_keywords';
{"procesado": ["cepillado", "servicio", "proceso", "maquila"],
 "granel": ["granel", "volumen total", "a granel", "sin desglose"]}
```
- Lector: `get_tipo_ingreso_keywords(tipo_ingreso)` (`madenat_ingestion_config.py:486-…`), cascada `ir.config_parameter` → hardcode legacy (`:492-495`).
- `[VERIFICADO]` La lista `granel` **no se consume** en `_classify_normal_document`, que sólo distingue `producto`/`procesado` (`:550-551`, `:566-577`).

**(4) Comportamiento con las cuatro cadenas** `[VERIFICADO]` — por lectura de `:565-566` y ejecución en Python puro de la misma comparación:

```
'Cepillada'                                                -> Producto   ([])
'CEPILLADO'                                                -> Procesado  (['cepillado'])
'PINO CEP. SECO LATERAL'                                   -> Producto   ([])
'SERVICIO CEPILLADO'                                       -> Procesado  (['cepillado', 'servicio'])
'Madera de Pino Radiata Cepillada Calidad Col A de 45mm'   -> Producto   ([])
```

| Cadena | ¿Coincide con la lista vigente? | Clasificación |
|---|---|---|
| `Cepillada` | No: `cepillada` no contiene `cepillado` | **Producto** |
| `CEPILLADO` | Sí (`cepillado`) | Procesado |
| `PINO CEP. SECO LATERAL` | No: `cep.` no contiene `cepillado` ni `servicio`/`proceso`/`maquila` | **Producto** |
| `SERVICIO CEPILLADO` | Sí (`servicio` + `cepillado`) | Procesado |

- **Texto real del PDF 40030** (extraído con `pdfplumber` de `Guia 40030.pdf`): `3322 M3 54,518 Madera de Pino Radiata Cepillada Calidad Col A de 45mm …` ⇒ se clasifica **Producto**.
- **Sin normalización de tildes, abreviaturas ni raíces**: sólo `casefold()` (`:565`).

### A3.2 Qué es configurable y qué no
`[VERIFICADO]` El **vocabulario** es configurable (`ir.config_parameter`). La **forma de comparar** no: subcadena sobre `casefold()`, en código (`:566`). Añadir `"cepillad"` (raíz) al parámetro resolvería los cuatro casos sin tocar código. `[HIPÓTESIS]` Un cambio a comparación por token/raíz en código sería más robusto, con riesgo bajo de falsos positivos porque las keywords actuales ya son raíces (`proceso` coincide con `procesado`).

### A3.3 Hipótesis
- `[HIPÓTESIS]` Las guías de MADENAT escriben «Cepillada» (concordando con «Madera») mientras la keyword está en masculino («cepillado»): causa raíz más probable de que guías de servicio caigan en Producto.
- `[HIPÓTESIS]` «PINO CEP. SECO LATERAL» aparece en el `product_name` del Excel (subproducto 570 en BD), no en la glosa del PDF; si el PDF no dice «servicio»/«maquila», el tipo será Producto.

### A3.4 Impacto en otros perfiles
`[VERIFICADO]` El clasificador elige entre dos modelos destino distintos (`lumber.reception` ↔ `madenat.guia.processing`) y no distingue perfiles. Cambiar keywords desvía guías entre flujos con campos y cálculos diferentes (A2). `[HIPÓTESIS]` Riesgo medio para Blanks/Arauco/JCE/BYC si sus glosas contienen «servicio» o «proceso».

### A3.5 Conclusión
Hoy existe **un solo** mecanismo de clasificación: texto del PDF por subcadena, con `casefold()` y sin normalización morfológica. Con el parámetro vigente, «Cepillada» y «PINO CEP. SECO LATERAL» se clasifican **Producto**; «CEPILLADO» y «SERVICIO CEPILLADO», Procesado. La sugerencia por nombre de archivo que describe el README ya no existe en el código.

---

## A4 — Engine: `extract_document` y perfiles de columnas

**Pregunta.** ¿Qué extrae (cabecera, líneas, unidades de origen, glosa, M3 declarado, columna M.B.F.)? ¿Cómo maneja «3.250», «2.575», coma decimal y varias líneas por lote? ¿Qué devuelve y qué consume el intake?

### A4.1 Contrato de salida `[VERIFICADO]`
- Firma: `extract_document(file_bytes, filename, column_profile=None)` (`document_extractor.py:1510`). El **formato binario** decide el parser (`detect_document_format`, `:1527`); el nombre es sólo diagnóstico (`:1515`, `:1525-1526`).
- Retorna `DocumentExtractionResult(header, lines, warnings, detected_profile_code, sheet_name_used)` y lanza `DocumentExtractionError` sólo ante fallo catastrófico (`:1519-1523`, `:1549-1551`).
- Claves de línea: `_LINE_KEYS = [package_no, product_code, product_name_original, thickness_value_raw, width_value_raw, length_value_raw, rows, columns, pieces, volume_m3, lot_number]` (`:64-68`) más `thickness_unit`/`width_unit`/`length_unit` (`_UNIT_KEYS`, `:69`) y `source_row_number` (`:393`).
- **No existen** claves para `declared_mbf`, `nominal_thickness`, `subproducto`, `grade`, `price` ni `currency`.

### A4.2 Unidades de origen `[VERIFICADO]`
- Se copian **del perfil**, nunca de la celda: `line[key] = source_units.get(key)` (`:432-435`).
- `packing_metrico_aserrada`: `mm/mm/m` (`ingestion_profiles.py:62-66`). `packing_imperial_blanks`: `inch/inch/ft` (`:98-102`).
- Consecuencia: si el perfil autodetectado no coincide con el documento, las unidades quedan mal etiquetadas sin advertencia.

### A4.3 Cabecera `[VERIFICADO]`
- **Excel**: etiquetas `label:value` de `_CORE_HEADER_LABELS` (`:78-86`: cliente→`customer_name`, fecha→`guide_date`, orden compra→`oc_reference`, guia despacho→`guide_number`, destino→`destination_label`, chofer→`carrier_name`, patente→`license_plate`) y `_EXTRA_HEADER_LABELS` (`:87-91`: rut/fono/trans), aplicadas en `_extract_excel_header` (`:1539`).
- **PDF**: regex de la Fase 1 (`_extract_pdf_header`, `:809`), que incluye `guide_number`, `supplier_rut`, `oc_reference` y el total declarado.
- **`declared_volume_m3`** no es una extracción propia: es un **alias** creado en `_extract_pdf` a partir de `header['total_volume_m3']` antes de la cascada de detalle (`:1482-1484`). Sólo existe en PDF; en Excel la clave **no** se genera.

### A4.4 M.B.F. y volumen a 45 mm: presentes en el documento, invisibles para el engine `[VERIFICADO]`

Volcado real de `40030.xls` con pandas (0-based; 25 filas × 17 columnas):

| Fila | Contenido relevante |
|---|---|
| 6-9 | cabecera `label:value` (CLIENTE, CHOFER, FECHA, PATENTE, ORDEN COMPRA, DESTINO, GUIA DESPACHO 40030) |
| 10 | cabecera de tabla en columnas **4-14**: `N° / CODIGOS / PRODUCTO / ESPESOR / ANCHO / LARGO / FILAS / COLUMNAS / PIEZAS / VOLUMEN / **M.B.F.**` |
| 11 | fila de unidades: `PQTE. / mm. / mm / mm / M3` |
| 12-23 | **12 líneas** de detalle |
| 24 | **fila de totales SIN etiqueta**: col 13 = `46.15815`, col 14 = `1362.847`, **col 16 = `54.518`** |

- **`M.B.F.` no se extrae**: ningún perfil declara alias para ella y `grep -rniE 'mbf|\.b\.f' madenat_ingestion_engine/services/` no devuelve **ninguna** coincidencia. El valor `1362.847` se repite idéntico en las 12 líneas y en la fila de totales (`[VERIFICADO]` por volcado), señal de fórmula con referencia absoluta o de dato arrastrado: **no es un MBF por línea**.
- **`54.518` (volumen a 45 mm) está en la columna 16**, fuera de la tabla (que termina en la 14) y sin encabezado: ni el engine por alias ni el parser del núcleo pueden verlo. La relación es exacta: `46.15815 × 45 / 38.1 = 54.518` (`[VERIFICADO]` con los valores del archivo), es decir, el Excel **declara explícitamente** el volumen comercial a nominal 45 mm además del físico a 38.1 mm.
- El engine sólo ve `46.15815` porque cae en la columna de `VOLUMEN`.

### A4.5 Defecto reproducido: la fila de totales sin etiqueta se cuenta como línea `[VERIFICADO]`

- `_TOTALS_ROW_RE` exige que la fila **empiece** por `total`/`subtotal` (`:1118-1121`), y el filtro se aplica sobre el texto concatenado de la fila (`:402-409`).
- La fila 24 de `40030.xls` no trae etiqueta: su texto empieza por `46.15815`, así que **no coincide** y se parsea como línea de datos.
- Ejecución real del engine (código del contenedor `odoo18_app`, mismo commit, sin ORM) sobre el archivo:
```
PROFILE packing_metrico_aserrada   SHEET Hoja1
HEADER {'customer_name': 'Madenat Chile Ltda.', 'carrier_name': 'Sergio Diaz',
        'guide_date': '2026-01-06 00:00:00', 'license_plate': 'KRZX 68 / HXFP 31',
        'oc_reference': 'MC-1812-248', 'destination_label': 'Bodega Tepornac',
        'guide_number': 40030}
NLINES 13              <-- 12 reales + 1 fila de totales
SUM_VOL 92.3163        <-- exactamente 2 × 46.15815
SUM_PIEZAS 2425
última línea: {'package_no': None, ..., 'volume_m3': 46.15815,
               'lot_number': 'LOTE-0000000095950', 'source_row_number': 25}
```
- **Impacto directo**: el preview de Producto muestra `92.316 m³` para una guía de `46.158 m³` (100 % inflado), y cualquier ruta que use la suma de líneas del engine (`_build_volume_detail_vals`, `intake_wizard.py:1011-1018`) arrastra el doble conteo si el Excel no trae etiqueta de totales.
- **Advertencia ausente**: el engine no emite ningún warning por esta fila; sólo advirtió de la fila de unidades (12) y del forward-fill de lotes (13-25).

### A4.6 Formatos numéricos `[VERIFICADO]`

`parse_localized_decimal` (`:130-166`) aplica, en este orden: (1) con coma y punto, el separador **más a la derecha** es el decimal (`:155-159`); (2) sólo coma ⇒ decimal (`:160-161`); (3) sólo punto ⇒ decimal (`:139`); (4) sin separador ⇒ directo. `_coerce_value` (`:198-207`) usa `_to_int` para `rows/columns/pieces` (`_INT_FIELDS`, `:70`), `_to_float` para `volume_m3` (`_FLOAT_FIELDS`, `:71`) y texto crudo para las dimensiones (`_RAW_TEXT_FIELDS`, `:72-75`).

Reproducción en Python puro de las funciones reales:

| Entrada | `parse_localized_decimal` / `_to_float` | `_to_int` (pieces/rows/columns) |
|---|---|---|
| `"3.250"` | `3.25` | `3` |
| `"2.575"` | `2.575` | **`3`** |
| `"3,250"` | `3.25` | `3` |
| `"2,575"` | `2.575` | **`3`** |
| `"1.234,56"` | `1234.56` | `1235` |
| `"40,315"` | `40.315` | `40` |

- **Riesgo material**: `"2.575"` como piezas (2 575 unidades con punto de miles) se convierte en **3 piezas**. El redondeo `int(round(f))` (`:173-177`) no distingue «2.575 como miles» de «2.575 como decimal».
- **Asimetría deliberada pero insuficiente**: `_to_money_float` sí trata los grupos de 3 como miles (`:180-195`), pero se aplica **sólo** a importes, no a piezas ni volumen.
- `[HIPÓTESIS]` En los packings reales (40030, 19846) las celdas son numéricas de Excel, no texto, por lo que el bug no se dispara; se dispararía con celdas de texto o exportaciones CSV. Reproducción pendiente con un packing sintético.

### A4.7 Varias líneas por lote (Item / N° LOTE) `[VERIFICADO]`

- `forward_fill_fields = ["lot_number"]` (`ingestion_profiles.py:52`, `:88`) y `synthesis_rule = {'field': 'lot_number', 'template': 'LOTE-{product_code}'}` (`:53-56`, `:89-92`).
- En `_build_lines` (`:384-480`): si `lot_number` viene vacío se hereda de la fila anterior (`:451-459`); si no hay anterior se sintetiza `LOTE-<product_code>` (`:460-470`); si tampoco, se advierte (`:471-475`). El estado se actualiza con el valor final (`:476-479`).
- **Defecto reproducido con datos reales**: en `40030.xls` ninguna línea trae lote. La primera sintetiza `LOTE-0000000095950` (`:461`) y **las 11 siguientes lo heredan** (`:454-455`), aunque tengan **product_code distinto**:
```
LOTES     ['LOTE-0000000095950']        # 1 solo lote para 13 líneas
PRODUCTOS 13                            # 13 códigos distintos (12 reales + fila de totales)
```
- Consecuencia: 12 productos diferentes comparten el mismo nombre de lote aguas abajo, lo que explica la clase de incidencias «lotes repetidos» documentada en los reportes del repositorio (`REPORTE_INVESTIGACION_LOTES_REPETIDOS_RECEPCION_VS_PROCESADOS.md`). El forward-fill está pensado para *un lote con varias líneas de producto*; aplicado a *varios lotes con líneas sin lote declarado*, colapsa la identidad.
- En el flujo Procesado, el forward-fill **no lo hace el engine** sino `_parse_excel_data_core` con su propia lógica (`current_explicit_lot`, `madenat_guia_processing.py:3937`, `:3955-3960`).

### A4.8 Qué consume el intake del resultado `[VERIFICADO]`

| Consumidor | Qué usa | Evidencia |
|---|---|---|
| Preview Producto | `result.lines` (5 primeras, formateadas a texto), `sum(volume_m3)`, `result.warnings`, `header['guide_number']`; **no persiste líneas** | `intake_wizard.py:638-670` |
| Coherencia de perfil | `length_value_raw`, `length_unit`, `width_value_raw`, `width_unit`; usa `float(l_raw)` directo (`:331`) | `:320-355` |
| Volumen | `header['declared_volume_m3']`/`total_volume_m3` o suma de líneas, y `line['volume_m3']` para el detalle | `:860-881`, `:1011-1018` |
| Procesado | **nada**: usa el parser del núcleo | `:594-618`, `madenat_guia_processing.py:2141-2168` |

- **Defecto adicional**: en `_check_profile_coherence` el largo se convierte con `float(l_raw)` (`:331`) en lugar de `parse_localized_decimal`. Un largo `"3,25"` lanza `ValueError` y se descarta **silenciosamente** (`except (ValueError, TypeError): pass`, `:335-336`): la coherencia de perfil no ve esos largos.

### A4.9 Hipótesis
- `[HIPÓTESIS]` La fila de totales sin etiqueta es habitual en los packings de MADENAT (Excel generados a mano), por lo que el doble conteo podría afectar a más guías de las detectadas. Prueba: recorrer `muestras_documentos_ingreso/excel_packing/*` con `extract_document` y comparar `sum(volume_m3)` con el total del archivo.
- `[HIPÓTESIS]` El `1362.847` de `M.B.F.` es una fórmula arrastrada con referencia absoluta (idéntica en 12 filas y en el total). No se pudo leer la fórmula porque el archivo es `.xls` binario y xlrd devuelve el valor cacheado; `[NO VERIFICABLE]` sin abrir el archivo en LibreOffice.

### A4.10 Impacto en otros perfiles
`[VERIFICADO]` `_LINE_KEYS`, `_INT_FIELDS`, `parse_localized_decimal`, `_TOTALS_ROW_RE` y el forward-fill son **globales al engine**: cualquier corrección afecta a todos los perfiles y a todas las modalidades que usan `extract_document` (preview Producto, coherencia, preview y ruta de Volumen). Los flujos que no usan el engine (Procesado vía `_parse_excel_data_core`, y las rutas propias del core para Blanks/Arauco/JCE/BYC) no se ven afectados, pero tampoco se benefician.

### A4.11 Conclusión
El engine extrae cabecera, líneas con unidades declaradas por perfil, dimensiones crudas, piezas, volumen y lote; **no extrae** M.B.F., espesor nominal, subproducto ni el volumen a 45 mm del Excel. Tres defectos quedan reproducidos con datos reales: (1) la fila de totales sin etiqueta se cuenta como línea y duplica el volumen (`92.3163` vs `46.15815`); (2) todas las líneas colapsan en un único lote sintético `LOTE-<primer código>`; (3) `"2.575"` en piezas se convierte en 3. Además, el volumen comercial a 45 mm (`54.518`) existe en el archivo pero está fuera de toda tabla reconocible.





## A5 — El parser del núcleo: `_parse_excel_data_core` frente al engine

**Pregunta.** ¿Cómo lee el núcleo el mismo packing? ¿Dónde están las diferencias reales con el engine (forward-fill de lote, detección de totales, prioridad de volumen) y qué parte es configurable?

### A5.1 Cadena de lectura del núcleo `[VERIFICADO]`

| Paso | Método | Evidencia |
|---|---|---|
| 1. Detección de formato | `detect_document_format(primeros bytes)` | `madenat_guia_processing.py:3901-3903` |
| 2. Lectura por formato | `xlrd` si `xls`, `openpyxl` si `xlsx`; **nunca** openpyxl sobre OLE2 | `:3904-3919` |
| 3. Detección de tabla | `detect_excel_table_across_sheets(sheets, flow='procesado')` | `:3930` |
| 4. Normalización de filas | bucle `:3938-3998` | `:3936-3998` |

- El detector es un **helper puro sin ORM ni pandas** (`excel_table_detection.py:1-24`: «Este helper es PURO: no usa `self.env`, no escribe en BD y no lanza excepciones de negocio»). Su fuente de verdad son alias semánticos (`CANONICAL_ALIASES`), **no un perfil de columnas**: el `ingestion_profile` **no participa** en la lectura del Excel.
- Confianza y diagnóstico se devuelven por fila de encabezado: en `40030.xls` el diagnóstico es `['Encabezado en fila(s) [11, 12] (8 columna(s) semántica(s), 12 línea(s)).']`, `confidence = high` (`[VERIFICADO]` ejecutando el helper puro sobre el archivo real, A5.5).

### A5.2 Detección de totales: tres filtros, ninguno depende de la etiqueta de fila `[VERIFICADO]`

```python
if not code or len(code) < 3:                                   continue   # :3947-3948
if any(x in code.lower() for x in ('nan','none','total','subtotal','totales')): continue  # :3949-3950
if any(x in prod_name.lower() for x in ('total','subtotal')):   continue   # :3951-3952
```

- La fila de totales de `40030.xls` (fila 25) **no tiene etiqueta**: sus celdas numéricas son `46.15815`, `1362.847`, `54.518`. El núcleo la descarta porque `code` queda vacío (`len('') < 3`), no porque diga «TOTAL». El engine, en cambio, sólo la detecta si la fila **empieza** por `total|subtotal` (`_TOTALS_ROW_RE`), de ahí el doble conteo de A4.5.
- El detector añade una tercera barrera independiente: «Totales/subtotales/notas excluidos por keyword, independiente de columna» (`excel_table_detection.py:19`).
- **Riesgo latente** `[INFERENCIA]`: el filtro del núcleo es estructural (código vacío o <3 caracteres). Una fila de totales que **sí** traiga un código válido y una descripción sin la palabra «total» pasaría como línea. No se observó en las muestras, pero el criterio no es semántico.

### A5.3 Forward-fill de lote: el núcleo **no colapsa** identidades `[VERIFICADO]`

```python
if lote_raw and lote_raw.lower() not in ('nan','none'):
    current_explicit_lot = lote_raw; lot = lote_raw        # :3959-3961
elif current_explicit_lot:
    lot = current_explicit_lot                            # :3962-3963
elif code:
    lot = "LOTE-%s" % code                                # :3964-3965
```

- El comentario del propio código lo explicita (`:3956-3958`): *«Identidad por línea: separa lote explícito (forward-fill válido para celdas fusionadas) del lote sintético derivado del código (solo para ESA fila, nunca se propaga)»*.
- El lote sintético es **por fila**; el forward-fill sólo propaga un lote **explícito**. Es exactamente la semántica que el engine no implementa (A4.7: propaga también el sintético).
- En `40030.xls` el núcleo obtiene **12 lotes distintos** (`1`…`12`, columna `N° LOTE`), mientras el engine obtiene uno solo.


### A5.4 Prioridad de volumen y dimensiones `[VERIFICADO]`

- `vol = volume_m3` declarado; si `<= 0`, se recalcula `(esp/1000)*(anc/1000)*lar*qty` (`:3972-3981`).
- `vol_documental_m3` se conserva aparte (`:3993`) y se arrastra a la línea (`:2202`).
- Dimensiones nominales: `_get_nominal_dimension(45,'thickness') → '6/4'`, `_get_nominal_dimension(125,'width') → '4 5/8'` (`:3985-3986`); en el perfil `metric` esto convierte milímetros físicos en fracciones comerciales **sin preguntar**.
- `6/4` es notación en **cuartos de pulgada** (`6/4" = 1.5"`). `parse_fraction_to_decimal_inch` la resuelve como división (`1.5`), que aquí coincide porque numerador y denominador son consistentes; **no hay validación de que el denominador sea 4**. `[INFERENCIA]` Un `"5/8"` en la columna de espesor daría 0.625" (7/8" de descuento) sin aviso.

### A5.5 Misma guía, dos lecturas — ejecución real sobre `40030.xls` `[VERIFICADO]`

Ejecución de **sólo lectura** (helper puro + réplica literal del bucle `:3936-3998`, sin ORM ni escritura) sobre el archivo del repositorio:

| Magnitud | Núcleo (`_parse_excel_data_core`) | Engine (`extract_document`) |
|---|---|---|
| Líneas | **12** | **13** |
| Piezas | **2 425** (suma de las 12 líneas) | 2 425 + 3 (`"2.575"` → 3, A4.6) `[INFERENCIA]` |
| Volumen | **46.1581 m³** (columna `VOLUMEN` del Excel) | **92.3163 m³** (doble conteo) |
| Lotes únicos | **12** (`1`…`12`, columna `N° LOTE`) | **1** (`LOTE-0000000095950`) |
| Columnas semánticas | 8 (`product_code`, `description`, `lot_or_package`, `thickness`, `width`, `length`, `pieces`, `volume_m3`) | perfil `packing_metrico_aserrada` |

- **El engine y el núcleo coinciden línea a línea en las 12 líneas reales** (mismos códigos, mismas piezas, mismas dimensiones, mismo volumen documental). Todas las diferencias son de **identidad y de fila de totales**, no de aritmética de línea.
- El total `46.15815` del Excel coincide exactamente con la suma de las 12 líneas: el documento es internamente consistente y el núcleo lo respeta.
- Detalle de las 12 líneas leídas por el núcleo (código · lote · piezas · mm × mm × m · m³ documental): `0000000095950·1·150·38.1×170×4.00·3.8862`, `0000000096579·2·150·38.1×170×4.00·3.8862`, `0000000095951·3·175·38.1×150×4.00·4.0005`, `0000000096550·4·175·38.1×150×4.00·4.0005`, `0000000095952·5·200·38.1×125×4.00·3.8100`, `0000000095992·6·200·38.1×125×4.00·3.8100`, `0000000095953·7·200·38.1×125×4.00·3.8100`, `0000000096580·8·200·38.1×125×4.00·3.8100`, `0000000096554·9·200·38.1×125×4.00·3.8100`, `0000000096549·10·200·38.1×125×4.00·3.8100`, `0000000096555·11·250·38.1×100×4.00·3.8100`, `0000000096582·12·325·38.1×75×4.00·3.7148`.

### A5.6 Qué es configurable y qué no `[VERIFICADO]`

| Elemento | ¿Configurable? | Dónde |
|---|---|---|
| Alias de encabezados | **No** (código) | `excel_table_detection.py:CANONICAL_ALIASES` |
| Columnas por perfil | **No existen** en el núcleo | — |
| Unidades por perfil | Sólo en el engine | `ingestion_profiles.py:62-102` |
| Filtro de totales | **No** | `madenat_guia_processing.py:3947-3952` |
| Forward-fill de lote | **No** | `:3955-3967` |
| Mapeo espesor/ancho nominal | **Sí** (tablas) | `lumber.width.s2s.map`, `lumber.thickness.real.map` |

### A5.7 Hipótesis
- `[HIPÓTESIS]` El detector puro tolera mejor los packings reales que el engine porque combina alias semánticos + descarte por keyword + descarte por código vacío; el engine, al exigir etiqueta al inicio de fila, sólo acierta con totales etiquetados. Prueba: correr ambos sobre todas las muestras de `muestras_documentos_ingreso/excel_packing/` y comparar líneas y suma de volumen.
- `[HIPÓTESIS]` La ausencia de perfil en el núcleo explica que `40030` se lea bien incluso con perfil `metric`: el perfil no cambia la lectura, sólo la interpretación posterior (producto maestro, subproducto, regla de exportación).

### A5.8 Impacto en otros perfiles
`[VERIFICADO]` El parser del núcleo es **común a todas las guías procesadas** (`madenat.guia.processing`), con independencia de `ingestion_profile`. Cambiar el filtro de totales o el forward-fill afecta a `metric`, `f5085` y `f1550` por igual. El engine, en cambio, es sólo de la ruta de ingreso; sus defectos **no** alcanzan a Procesado (que no lo usa, A4.8).

### A5.9 Conclusión
El núcleo lee `40030.xls` correctamente: 12 líneas, 2 425 piezas, 46.1581 m³ y 12 lotes distintos. La diferencia con el engine no es de fórmula sino de **reglas de identidad y de exclusión de totales**: el núcleo nunca propaga un lote sintético y descarta la fila de totales por estructura (código vacío), mientras el engine propaga el lote y exige etiqueta para descartar totales. Cualquier motor nuevo debe **adoptar las dos reglas del núcleo**, no reimplementarlas.


## A6 — Ruta Procesado de punta a punta y diferencias con Producto

**Pregunta.** ¿Qué ocurre exactamente al derivar a Procesado? ¿En qué se diferencia de Producto y dónde se pierde información en cada rama?

### A6.1 Recorrido real de la rama Procesado `[VERIFICADO]`

| # | Paso | Evidencia |
|---|---|---|
| 1 | `action_route_document` → `_guard_route_document` → `_route_procesado` | `intake_wizard.py:685-710`, `:712-764`, `:809-840` |
| 2 | Crea `madenat.guia.processing` con `tipo_recepcion='service'`, `intake_direct_stock=True`, `assignment_location_id`, ambos archivos y `ingestion_profile` | `:814-825` |
| 3 | Llama **inmediatamente** `guia.action_verify_data()` dentro del `savepoint` | `:827` |
| 4 | `action_verify_data`: `unlink()` de las líneas previas, guarda adjuntos, `_parse_packing_excel` | `madenat_guia_processing.py:2155-2158` |
| 5 | `_parse_packing_excel` → `_parse_excel_data_core` → `_validar_y_enriquecer_lineas` → normaliza `lineas`, `lineas_documentales`, `total_volumen`, `total_volumen_mbf` | `:3669-3720` |
| 6 | Crea las `madenat.guia.processing.line` con producto maestro fijo, subproducto desde la descripción y nominal visual | `:2169-2225` |
| 7 | PDF: **sólo** costos, T/C, fecha, `vol_comercial_pdf` y `name`; no toca volúmenes ni dimensiones | `:2233-2265` |
| 8 | Estado final `verified` | `:2233` |

- El comentario del wizard afirma «Parser nativo de Guía Processing (**forward-fill N° LOTE**)» (`intake_wizard.py:826`). **Contradicción verificada**: el parser del núcleo no propaga lotes sintéticos (A5.3); sólo propaga los explícitos. La documentación interna describe un comportamiento que el código no tiene.

### A6.2 Qué escribe el paso 6 y qué se recalcula después `[VERIFICADO]`

```python
'vol_physical_m3': vol_raw, 'vol_shipment_m3': vol_raw, 'vol_purchase_m3': vol_raw,  # :2199-2201
'espesor_nominal_mm': row.get('espesor_nominal_mm', 0.0) or row.get('Espesor', 0.0),   # :2210
'thickness_visual': txt_nom_esp, 'width_visual': txt_nom_anc,                          # :2213-2214
```

- Los tres volúmenes nacen **iguales al volumen documental** y luego los `compute` los sobrescriben: `vol_shipment_m3` pasa al cálculo imperial (`:600-674`) y `vol_purchase_m3` se queda con el documental/métrico. Es el origen de que la misma línea tenga dos volúmenes con bases distintas.
- El docstring del método dice «DEJA LIMPIO el Nominal de Compra (si no viene en Excel) para asignación manual posterior» (`:2146`), pero el código **rellena el nominal con el espesor leído** (`:2210`). En `19846` las 19 líneas tienen `espesor_nominal_mm = 45.000` (`min = max = 45`, `avg = 45.00`, 0 nulos, 0 ceros) e `espesor_mm = 45`, de modo que **no hay forma de distinguir si el nominal vino del Excel o del fallback**: el campo nunca queda vacío para asignación manual, contra lo que promete el docstring.
- `vol_documental_m3` se conserva aparte (`:2202`), pero en la guía `19846` (id 1196) **está vacío en las 19 líneas** (`sum(vol_documental_m3)` es `NULL`), pese a que el Excel declara `VOLUMEN`. `[VERIFICADO]` por SQL: el campo no se está poblando en la práctica.

### A6.3 Al validar: los lotes son otra fuente de verdad `[VERIFICADO]`

- `action_validate` (`:2555`) crea los `stock.lot` y los asigna a `lot_ids` (`:1710`).
- En el lote se escribe `'vol_shipment_m3': v_stock_real` y `'volumen_m3': item.vol_purchase_m3` (`:1675-1678`); el `volumen_mbf` del lote lo calcula el propio `stock.lot` (derivado de `volumen_m3`).
- En la guía `19846`/id 1196, **cabecera y lotes coinciden entre sí** (`vol_comercial = vol_fisico = Σ volumen_m3 de lotes = 47.152`; `vol_shipment_m3 = 37.809`; `volumen_mbf = 19.979`) y **ninguno coincide con las líneas** (`vol_shipment` 36.816, `vol_mbf` 15.604). Ver A7.6.


### A6.4 Procesado vs Producto, lado a lado `[VERIFICADO]`

| Aspecto | Producto | Procesado |
|---|---|---|
| Destino | `lumber.reception` (`:782-789`) | `madenat.guia.processing` (`:814-825`) |
| Disparador de lectura | `reception.action_process_documents()` → `LumberReceptionWorkflow.run_ingestion_pipeline` (`lumber_reception.py:2810-2820`) | `guia.action_verify_data()` directo (`:827`) |
| Parser del pipeline | workflow del núcleo (no el engine) | `_parse_excel_data_core` (núcleo) |
| Motor nuevo (`extract_document`) | **sólo** en el preview del wizard (`intake_wizard.py:638-670`); no persiste | **no se usa** |
| Tipo de recepción | el que corresponda a la modalidad | fijado `'service'` + `intake_direct_stock=True` |
| Perfil | se copia al destino (`:787`) | se copia al destino (`:822`) |
| Estado tras derivar | el que fije el workflow | `verified` |
| Tercer lector visible | `lumber_reception.action_verify_data` (`:2822-2850`): **columnas fijas A/B/C/D y sólo `openpyxl`** | — |

- **Hallazgo colateral verificado**: el botón `action_verify_data` de Recepción (`lumber_reception_views.xml:96`) lee por **posición de columna** (`A=lote, B=producto, C=cantidad, D=volumen`) y usa `load_workbook(...).active` sin detección de formato; con un `.xls` (formato de las muestras) **no puede abrir el archivo** y con cualquier packing con otro orden de columnas leería valores equivocados. Es un cuarto lector, independiente de los otros tres, alcanzable por UI.

### A6.5 Diferencias funcionales relevantes

| Diferencia | Producto | Procesado | Consecuencia |
|---|---|---|---|
| Identidad de lote | la decide cada lector | `lot_name = lote_fisico or code` (`:2192`) | Procesado **nunca** colapsa lotes |
| Producto | producto maestro por perfil (`:2161-2162`) | igual (`:2161-2162`) | mismo criterio; el SKU del Excel queda en `sku_original` |
| Subproducto | desde texto del Excel | `find_or_create_lumber_subproducto(prod_name)` (`:2179`) | crea subproductos al vuelo desde la descripción |
| Nominal de compra | `espesor_nominal_mm` del lector | se fuerza al físico si falta (`:2210`) | el «nominal» no es independiente del físico |
| Volumen a 45 mm del Excel | no se lee | no se lee (A4.4) | ambos flujos pierden `54.518` |

### A6.6 Hipótesis
- `[HIPÓTESIS]` El botón legacy de Recepción (`action_verify_data`) ya no se usa en el camino feliz, pero sigue accesible y es el único lector que falla con `.xls`; quien lo pulse tras subir el packing obtendrá un error de formato, no una lectura degradada. Prueba: pulsarlo sobre una recepción con `.xls` en una BD de pruebas (requiere escritura, fuera del alcance de esta auditoría).
- `[HIPÓTESIS]` El `vol_documental_m3` vacío en `19846` indica que las líneas se crearon por otra vía o con una versión anterior del código. `[NO VERIFICABLE]` sin histórico de versiones ni logs del 2026-08-31.

### A6.7 Impacto en otros perfiles
`[VERIFICADO]` Las diferencias A6.4/A6.5 son **estructurales de la rama**, no del perfil: afectan igual a `metric`, `f5085` y `f1550`. Dependen del perfil, en cambio:

| Efecto | Depende de perfil | Evidencia |
|---|---|---|
| Producto maestro | sí | `get_default_product('procesado', profile=...)` `:2161-2162` |
| F4 — volumen de exportación (`vol_shipment_m3`) | **no** | `_compute_vol_shipment_m3` `:600-674` no lee `ingestion_profile` |
| F3 — volumen físico real (`vol_physical_real_m3`) | **sí** | `f5085` + `length_ft > 0.1` ⇒ `0.0` / `'no_aplica'` `:690-694` |
| Candado anti-mezcla comercial | sí | `madenat_guia_mass_update.py:80-84` (citado en `:987-988`) |
| Filtros de subproducto | sí | `madenat.profile_subproduct_filters` |

- `[VERIFICADO]` en `19846` (`ingestion_profile = 'f5085'`, `tipo_recepcion = 'service'`) **las 19 líneas** tienen `physical_status = 'no_aplica'` y `Σ vol_physical_real_m3 = 0.000`: la fórmula F3 **nunca se ejecutó**, por la regla `f5085 + pies`. El «volumen físico real» que el usuario ve es `vol_physical_m3` (otro campo, el documental), no F3.

### A6.8 Conclusión
Procesado es la rama **mejor leída** del sistema: usa el parser semántico del núcleo, conserva identidad de lote por línea y coincide con el total declarado del Excel. Sus pérdidas no están en la lectura sino en la **interpretación posterior**: el nominal se confunde con el físico, el volumen a 45 mm del documento no se lee, `vol_documental_m3` no llega a poblarse y la fórmula física F3 se anula por perfil. Producto, en cambio, tiene tres lectores distintos y uno de ellos (el botón legacy) es posicional y sólo `.xlsx`.



## A7 — Verificación numérica: de dónde sale cada cifra

**Pregunta.** ¿Se sostienen `18.512 MBF`, `44.713 m³` de exportación, `54.518 m³` de compra y el nominal `38.0` frente a `45 mm`? ¿Qué campos reales los contienen y con qué fórmula?

### A7.1 Los cuatro números de `40030`, uno por uno `[VERIFICADO]`

| Cifra | ¿Reproducida? | Cómo |
|---|---|---|
| **54.518 m³ compra** | **Exacta: 54.5175** | `Σ 45 × ancho_rough × 4 m × piezas / 1e6` sobre las 12 líneas |
| **18.512 MBF** | **Exacta: 18.5138** | `Σ 1.5" × ancho_s2s × 13.1232 ft × piezas / 12 000` (ancho comercial, sin +1/8) |
| **46.15815 m³ físico** | **Exacta** | `Σ 38.1 × ancho_rough × 4 × piezas / 1e6` = columna `VOLUMEN` del Excel |
| **44.713 m³ export** | **No exacta** | Con `+1/8"` da **44.8610**; sin `+1/8"` da **43.6877**. `44.713` queda **entre** ambas (−0.33 % de la primera) |

- `54.518` **no es un cálculo del sistema**: está impreso en la guía PDF — texto extraído: `3322 M3 54,518 Madera de Pino Radiata Cepillada Calidad Col A de 45mm` — y repetido en la celda oculta del Excel (A4.4). El sistema lo **ignora** por ambas vías.
- `18.512` sí es un cálculo reproducible con la fórmula canónica del núcleo aplicada a los anchos **comerciales S2S** y espesor `6/4`. Que coincida al 0.01 % valida la fórmula y, a la vez, demuestra que **el MBF no usa los 45 mm**.
- La relación `44.713 / 18.512 = 2.4154` es prácticamente la que produce la regla de **anchos partidos** (`m³ con +1/8"` / `MBF con ancho nominal`), que para esta mezcla de anchos vale **2.4231**. `[INFERENCIA]` Los dos números atribuidos a `40030` provienen de una misma corrida con esa regla; la diferencia de 0.33 % restante no es atribuible sin el registro de origen.
- `40030` **no existe como registro** en la BD auditada: `SELECT … FROM madenat_guia_processing WHERE name IN ('40030','19846')` devuelve **sólo `19846` (id 1196)**, y `lumber_reception` no tiene `40030` ni `origin_processing_id = 1196`. Por tanto las cifras de `40030` son **de documento**, no de registro, y `[NO VERIFICABLE]` su origen exacto.

### A7.2 Nominal 38.0 vs 45 mm: no es un error de lectura, es una regla configurada `[VERIFICADO]`

- `madenat.thickness_visual_ranges = {"ranges": [[37, 46, 1.5, "6/4"], …], "default_format": "{q}/4"}`: **todo espesor entre 37 y 46 mm se interpreta como `6/4"` (38.1 mm)**. El `45 mm` físico se convierte en `1.5"` por configuración, no por aritmética.
- Consecuencia aritmética exacta: `45/38.1 = 1.1811`. Los dos volúmenes del mismo material difieren **18.1 %** (`54.518` vs `46.158`) porque uno usa el espesor físico y el otro el comercial. El MBF (`18.512`) usa el comercial; la compra (`54.518`) usa el físico.
- El motor de ingreso **no ve** ninguno de los dos explícitamente: lee `38.1` de la columna `ESPESOR` del Excel y no tiene campo para el «45 mm» que declara el PDF.


### A7.3 Verificación con una guía real: `19846` (id 1196) `[VERIFICADO]`

Campos leídos por SQL (`SELECT` directo, sin ORM):

| Campo | Valor |
|---|---|
| `state` / `tipo_recepcion` / `ingestion_profile` | `validated` / `service` / (vacío) |
| `vol_comercial` | **47.152** |
| `vol_fisico` | **47.152** |
| `vol_comercial_pdf` | **39.817** |
| `vol_shipment_m3` (cabecera) | **37.809** |
| `vol_total_m3` (cabecera) | **37.809** |
| `vol_total_mbf` / `vol_fisico_mbf` | **19.979** / **19.979** |
| `vol_comercial_mbf` | 0.000 |
| Líneas | 19 · Σ`vol_purchase` **47.152** · Σ`vol_shipment` **36.816** · Σ`vol_mbf` **15.604** · Σ`pieces` **2 575** |
| Lotes (`stock.lot` vía `lot_ids`) | 19 · Σ`volumen_m3` **47.152** · Σ`volumen_mbf` **19.979** · Σ`vol_shipment_m3` **37.809** |

Comprobación línea a línea (primer registro, lote `D7731`, 200 piezas, 45 × 125 mm, 3.25 m, `thickness_visual='6/4'`, `width_visual='4 5/8'`):

| Fórmula | Cálculo | Resultado | Campo |
|---|---|---|---|
| Compra (métrico) | `0.045 × 0.125 × 3.25 × 200 / 1e6` | **3.65625 → 3.656** | `vol_purchase_m3` ✅ |
| MBF comercial | `1.5 × 4.625 × 10.663 × 200 / 12 000` | **1.2329 → 1.233** | `vol_mbf` ✅ |
| Export con `+1/8"` (sin sobreancho) | `1.5 × 4.625 × 3.25 × 200 / 1550.003` | **2.9092 → 2.909** | `vol_shipment_m3` ✅ |
| Export con sobreancho vigente | `1.5 × 4.75 × 3.25 × 200 / 1550.003` | **2.9879 → 2.988** | *(ninguno)* |

- `length_ft = 10.663` = `3.25 m × 3.28084`, exacto.
- **Conclusión de la comprobación**: los tres campos almacenados son reproducibles con las fórmulas del código **usando sobreancho 0.0**; con el parámetro vigente (`0.125`) el mismo `compute` produciría `2.988`. Ver A7.5.

### A7.4 El sobreancho no está en los datos: está en un parámetro global `[VERIFICADO]`

| Fuente | Valor | ¿Dónde se usa? |
|---|---|---|
| `lumber.width.s2s.map` (15 filas, 75…155 mm) | `overwidth_inches = 0.0000` en **todas** | `resolve_export_width_details` paso 3 (`madenat_ingestion_config.py:270-283`) |
| `ir.config_parameter madenat.s2s_overwidth_inches` | `0.125` (modificado 2026-10-18) | fallback cuando la fila trae 0 (`:274`, `get_s2s_overwidth_inches` `:149-158`) |
| `madenat.direct_width_min_mm` | `170.0` | umbral «fuera de tabla» (`:259`, `:290`) |
| `madenat.width_s2s_map` (parámetro) | `{…, "170": 170.0}` | **ningún lector** (grep repo-wide) |
| `madenat.s2s_exclusion_widths` | **no existe** | citado en la descripción de la fórmula `s2s_imperial` (`lumber_export_formula.py:102`) |

- Por el orden de resolución (`:270-283`), una fila con `overwidth = 0` **siempre** cae al global `0.125`: `calc_width = s2s_decimal + 0.125`. Es decir, **todo ancho en tabla lleva +1/8" en el volumen de exportación**, por diseño.
- `170 mm` no está en la tabla (máximo 155) ⇒ `calc_width = 170/25.4 = 6.6929"` sin +1/8 y `is_out_of_table = True`; con `out_of_table_behavior = 'warning'` sólo registra aviso.
- **Trampa de datos** `[VERIFICADO]`: el parámetro `madenat.width_s2s_map` contiene `"170": 170.0` (cien veces el valor correcto, `6.6929`). Hoy **no lo lee nadie**, pero el docstring de `lumber_width_s2s_map.py:10` lo declara «fallback (Fase 1)» de la tabla. Si alguien implementa ese fallback tal como está documentado, `170 mm` pasaría a cubicar `170"`.
- El docstring del modelo también afirma «Editar un registro SOLO afecta calculos NUEVOS; no recalcula registros historicos» (`lumber_width_s2s_map.py:19-20`) — coherente con lo observado en A7.5, pero **también** aplica al parámetro global, que no está documentado como histórico.

### A7.5 Prueba forense: cabecera recalculada, líneas congeladas `[VERIFICADO]`

Suma de `vol_shipment_m3` de las líneas de `19846` por ancho, y la misma suma recalculada con `+1/8"` (anchos 75/100/120/125/140/145 → `2.625/3.625/4.375/4.625/4.875/5.375`):

| Ancho | Líneas | Σ almacenada | Σ con `+1/8"` |
|---|---|---|---|
| 75 | 1 | 2.064 | 2.162 |
| 100 | 2 | 2.698 | 2.791 |
| 120 | 2 | 2.730 | 2.808 |
| 125 | 3 | 5.801 | 5.958 |
| 140 | 4 | 8.242 | 8.453 |
| 145 | 7 | 15.281 | 15.636 |
| **Total** | **19** | **36.816** | **37.808** |

- La cabecera y los lotes guardan **37.809**; las líneas, **36.816**. La reconstrucción con `+1/8"` da **37.808** (diferencia de 0.001 por redondeo a 3 decimales por línea).
- Interpretación `[INFERENCIA]` (alta confianza): las **líneas** se calcularon cuando el sobreancho era `0.0`; cabecera y **lotes** se recalcularon después del cambio de parámetro del **2026-10-18** (`write_date` del parámetro; la guía tiene `write_date = 2026-10-21`). No hay `@api.depends` sobre `ir.config_parameter`, así que cada campo se congela en el momento en que se calculó: **la guía contiene dos verdades numéricas simultáneas**.
- Corolario operativo: cualquier acción que fuerce el recálculo de las líneas (editar `pieces`, `ancho_mm`, `length_ft`, o el perfil) moverá `vol_shipment_m3` de `36.816` a `37.809`, **+2.70 %**, sin que nadie haya tocado el documento.

### A7.6 Cuatro volúmenes para el mismo material `[VERIFICADO]`

| Volumen | 19846 | 40030 | Base |
|---|---|---|---|
| Compra física (mm reales) | 47.152 | 46.1581 | `mm × mm × m × pzas / 1e6` |
| Compra comercial (45 mm) | — (no hay 45 separado) | **54.518** | declarada en PDF/Excel |
| Export con +1/8" | 37.809 (cabecera/lotes) | 44.713 | `1.5" × (s2s + 1/8") × L_ft × pzas / 5085.312` |
| MBF comercial | 19.979 (lotes) / 15.604 (líneas) | **18.512** | `m³/2.36` (lotes) vs `1.5" × s2s × L_ft × pzas / 12 000` (líneas) |

- En `19846`, la diferencia de MBF entre lotes y líneas es **+28.0 %** (`19.979` vs `15.604`): el lote deriva el MBF de `volumen_m3` a 45 mm con el factor `2.36` (`m³ → MBF` como si todo el volumen fuera volumen de pies tablares), mientras la línea lo calcula con `6/4`. **Ambos son «el MBF» de la misma madera.**
- En `40030` esa misma ambigüedad explica que `18.512` (6/4) conviva con un volumen declarado de `54.518` a 45 mm.


### A7.7 Caso testigo: una sola línea, dos volúmenes `[VERIFICADO]`

Línea `4861` de `19846` (100 mm, 124 piezas, 2.90 m, `6/4`, `width_visual='3 5/8'`) y su lote `D7602 PCLAT04201003250 19846`:

| Objeto | Fórmula con `w` | Resultado | Campo |
|---|---|---|---|
| Línea | `1.5 × 3.625 × 9.514 × 124 / 5085.312` | **1.261** | `vol_shipment_m3` |
| Lote | `1.5 × 3.750 × 9.514 × 124 / 5085.312` | **1.305** | `vol_shipment_m3` |
| Línea | `1.5 × 3.625 × 9.514 × 124 / 12 000` | **0.535** | `vol_mbf` |
| Lote | `1.618 / 2.36` | **0.686** | `volumen_mbf` |

- Misma madera, misma geometría, **mismo campo** (`vol_shipment_m3`) y valores distintos: `1.261` vs `1.305` (**+3.45 %**). La única diferencia es `w = 3.625` vs `w = 3.750`.
- En MBF la brecha es **+28.2 %** (`0.535` vs `0.686`) porque el lote no usa `6/4` sino `m³/2.36`.
- `[VERIFICADO]` `Σ volumen_m3 / Σ volumen_mbf` del conjunto de lotes = **2.3601**: el factor `2.36` se aplica por diseño, no por redondeo.

### A7.8 El sistema ya detecta la brecha… y la deja pasar `[VERIFICADO]`

| Indicador | Valor en `19846` | ¿Bloquea? |
|---|---|---|
| `warning_msg` | **19/19** líneas: «Diferencia significativa (25.4 % – 33.5 %)» | no |
| `vol_diff_pct` | 19/19 con valores entre **−25.13 %** y **−20.26 %** | no |
| `is_export_greater_nominal` | 0/19 | — |
| `reconciliation_status` | 19/19 = `none` | no |
| `technical_validation` (línea) | 19/19 = `pending` | **no** (guía en `validated`) |
| `technical_validation` (lote) | `approved` al validar (`:2849`) | — |
| `calc_method` | **0/19** (`NULL`) | — |
| `is_out_of_table` / `out_of_table_status` | 19/19 `false` / `in_table` | — |

- El aviso «Diferencia significativa» y `vol_diff_pct` son **recíprocos** de la misma razón: para la línea `4867`, `2.742 / 2.064 − 1 = 32.8 %` (aviso) y `2.064 / 2.742 − 1 = −24.73 %` (`vol_diff_pct`). Es el mismo hecho descrito en dos direcciones.
- `action_validate` **no consulta** ninguno de estos campos: sus guardas son `state`, líneas documentales pendientes, `espesor_nominal_mm`, `subproducto_id`, `rate_usd` y OC (`:2573-2668`). Por eso una guía con **19/19 líneas advertidas y `technical_validation='pending'`** termina en `validated`.
- Las líneas quedan `pending` para siempre mientras los lotes se marcan `approved` (`:2849`): dos objetos del mismo ingreso con estados técnicos contradictorios.

### A7.9 Hipótesis
- `[HIPÓTESIS]` El `warning_msg` se calculó con la base antigua (`w` sin `+1/8`) y no se recalcula al cambiar `madenat.s2s_overwidth_inches`; si se recalculara con la base vigente la brecha bajaría a ≈ 21–30 %. Prueba: recalcular una línea en una BD de pruebas.
- `[HIPÓTESIS]` `44.713` de `40030` proviene de la misma corrida que `18.512` con un mapa de anchos ligeramente distinto (p. ej. `150 → 5.75` o `170` redondeado a `6.75`); ninguna combinación probada reproduce el valor exacto. `[NO VERIFICABLE]` sin el registro de origen.

### A7.10 Conclusión de A7
Los cuatro números de `40030` se separan en dos clases: **exactos y reproducibles** (`54.518` compra a 45 mm, `46.158` físico a 38.1 mm, `18.512` MBF a `6/4`) y **no reproducibles** (`44.713`, entre la base con y sin sobreancho). En la BD, el mismo material tiene **cuatro volúmenes simultáneos** (compra física, compra comercial, exportación con `+1/8`, exportación sin `+1/8`) más **dos MBF** (`6/4` y `m³/2.36`). Ninguna de esas seis cifras está marcada como «la oficial»: el sistema detecta la brecha, la escribe en `warning_msg` y permite validar igualmente.


## A8 — Guardas y control previo a la derivación

**Pregunta.** ¿Qué impide que un documento mal leído o mal clasificado avance? ¿Dónde está el último punto de control antes de que los números entren al stock?

### A8.1 Las seis guardas de `_guard_route_document` `[VERIFICADO]`

| # | Guarda | Condición de bloqueo | Mensaje | Evidencia |
|---|---|---|---|---|
| G1 | Patio de asignación | `not assignment_location_id` | «Seleccione el Patio de Asignación…» | `intake_wizard.py:715-718` |
| G2 | Patio interno | `usage != 'internal'` | «El Patio debe ser una ubicación interna» | `:720-723` |
| G3 | Documentos (modalidad) | `volume`: ni PDF ni Excel · `normal`: falta PDF o falta Excel | «Debe adjuntar…» | `:727-738` |
| G4 | Estado por rama | `normal + producto` exige `state == 'previewed'`; el resto, `draft` o `previewed` | «Debe leer el documento (preview)…» | `:741-750` |
| G5 | Coherencia de perfil | `_check_profile_coherence()` devuelve texto y `not confirm_profile_mismatch` | «⚠️ ADVERTENCIA DE COHERENCIA DE PERFIL…» | `:752-764` |
| G6 | Idempotencia (previa a G1–G5) | `_existing_target()` no nulo ⇒ **retorna sin evaluar nada** | — | `:688-694` |

- **G6 anula a G1–G5.** Si el wizard ya tiene `target_model`/`target_res_id` y el registro existe, `action_route_document` abre el destino y **no vuelve a validar** patio, archivos, estado, perfil ni confirmación. Como `_existing_target` sólo comprueba existencia (`:766-774`), cambiar el Excel/PDF o el perfil **después** de la primera derivación y volver a pulsar «Continuar ingreso» **no** dispara ninguna guarda: el usuario aterriza en el destino antiguo sin aviso.
- **G4 deja pasar Procesado sin preview.** Con `state='draft'` y `tipo_ingreso='procesado'` se puede derivar sin haber leído el documento; el único requisito es que el PDF y el Excel estén adjuntos.
- **G5 es el único control semántico** y es **no bloqueante con confirmación**: guarda el texto en `profile_warning_message` y exige `confirm_profile_mismatch=True`.


### A8.2 G5 en detalle: el clasificador mira el PDF, no el Excel `[VERIFICADO]`

`_classify_normal_document` (`:549-577`) lee **sólo el PDF** (`_extract_pdf_text`), lo pasa a `casefold()` y busca cuatro palabras: `get_tipo_ingreso_keywords('procesado')` = `["cepillado", "servicio", "proceso", "maquila"]` (`ir.config_parameter`, verificado en BD). Si no hay coincidencia, escribe `tipo_ingreso='producto'`.

Prueba con el texto real de `Guia 40030.pdf` (1 352 caracteres extraídos):

| Palabra | ¿Presente? |
|---|---|
| `cepillado` | **No** |
| `servicio` / `proceso` / `maquila` | No / No / No |
| `cepillada` (lo que el documento dice) | **Sí** — «Madera de Pino Radiata **Cepillada** Calidad Col A de 45mm» |

- **Consecuencia verificada**: `40030` se clasifica **Producto** por el algoritmo, aunque su glosa describe material cepillado (servicio). El sustantivo del documento es `cepillada` (femenino, concuerda con «madera») y la palabra clave es `cepillado` (masculino): el `in` de subcadena falla por una vocal.
- Peor: `action_preview_document` **llama siempre** a `_classify_normal_document()` (`:588`) y ésta **sobrescribe** `tipo_ingreso` con `write`. Un usuario que corrija manualmente a «Procesado» y vuelva a pulsar «Leer documento» **pierde la corrección** sin aviso.

### A8.3 Lo que el sistema NO comprueba antes de derivar `[VERIFICADO]`

| Comprobación ausente | Dato que la delata | Dónde debería estar |
|---|---|---|
| Volumen declarado en el documento vs volumen de las líneas | `54.518` (PDF/celda oculta) vs `46.158` (líneas) | `preview` / `_guard_route_document` |
| MBF declarado vs calculado | `18.512` no se lee en ningún campo | ídem |
| Perfil vs tipo de recepción | `19846`: `f5085` + `service` (perfil de madera bruta en un servicio) | `:752` (G5 sólo mira largos) |
| `technical_validation` de las líneas | `19846`: 19/19 `pending` con guía `validated` | `action_validate:2573` |
| `reconciliation_status` | `19846`: 19/19 `none` | `action_validate` |
| `vol_diff_pct` > umbral | `19846`: 19/19 entre −25 % y −20 %; umbral **10 % hardcodeado** (`mixin_lumber_ingest.py:478`) | `action_validate` |
| Guía duplicada | no hay guarda de `name` único por proveedor | `_guard_route_document` |
| Sobreancho aplicado al export | `0.125"` global, invisible en la línea | `preview` |

### A8.4 Diseño de marca de advertencia propuesto (no implementado)

Objetivo: que la discrepancia **se vea y se firme**, sin bloquear el flujo. Todo con campos existentes salvo un indicador de cabecera.

| Nivel | Elemento | Regla propuesta |
|---|---|---|
| Línea | `warning_msg` (ya existe) | mantener; añadir el valor declarado y el calculado: `Declarado 3.750 m³ / Calculado 3.104 m³ (21.0 %)` |
| Línea | `is_export_greater_nominal` (ya existe, hoy 0/19 útil) | marcar también cuando `|vol_diff_pct| > tolerance` (no sólo cuando export > nominal) |
| Cabecera | nuevo `volume_discrepancy_pct` + `volume_discrepancy_state` (`ok` / `warning` / `critical`) | `critical` si `|Σ declarado − Σ calculado| / Σ declarado > madenat.volume_discrepancy_tolerance` (**parámetro nuevo**; el 10 % de hoy está hardcodeado) |
| Wizard | `preview_warnings` (ya existe) | incluir la discrepancia en el preview, antes de derivar |
| Validación | `action_validate` | si `volume_discrepancy_state == 'critical'` exigir `reconciliation_status != 'none'`; **no** bloquear por defecto, sí exigir confirmación explícita (patrón G5) |
| Auditoría | `message_post` | registrar «Ingreso con discrepancia X % aceptada por …» (ya se usa este patrón en `:2639-2670`) |

- El dato para calcularlo **ya está en memoria** en `_parse_packing_excel` (`total_volumen` del documento) y en las líneas (`Σ vol_purchase_m3`): no hace falta releer nada.
- `madenat.nominal_tolerance = 0.08` **no sirve** para este control: es la tolerancia de **espesor nominal** (`reception_parser._resolve_nominal:215-221`), no de volumen. El umbral de hoy (`10`) está hardcodeado en `mixin_lumber_ingest.py:478` con un comentario que dice «Umbral de tolerancia parametrizable» — el comentario promete algo que el código no hace.

### A8.5 Hipótesis e impacto
- `[HIPÓTESIS]` El override manual de `tipo_ingreso` se usa en la práctica para corregir el fallo de `cepillada/cepillado`; cada nuevo preview lo revierte. Prueba: revisar `tipo_ingreso_auto_detectado` en guías `service` creadas desde el wizard.
- `[VERIFICADO]` `[IMPACTO]` G6 (idempotencia) + G4 (Procesado sin preview) + clasificador por PDF significan que **la decisión más importante del flujo —a qué rama va el documento— se toma con la evidencia más débil**: cuatro palabras clave sobre la glosa del PDF, sin mirar el Excel que sí tiene las dimensiones.

### A8.6 Conclusión de A8
Las guardas de derivación son **operativas, no semánticas**: comprueban que haya archivos, patio y estado, y como mucho advierten del perfil. Ninguna compara lo que el documento declara con lo que el sistema calcula, y la clasificación Producto/Procesado depende de una coincidencia literal de género gramatical. El único control realmente útil (`vol_diff_pct`) se calcula **después**, se escribe en la línea y no se consulta nunca.


## A9 — Recálculo cruzado, cobertura y cierre

### A9.1 `40030` por las dos rutas `[VERIFICADO]`

| Magnitud | Núcleo (`_parse_excel_data_core`) | Motor (`extract_document`) | Diferencia |
|---|---|---|---|
| Líneas leídas | **12** | **13** (incluye la fila de totales) | +1 fila fantasma |
| Piezas | **2 425** | 2 425 | 0 |
| Lotes distintos | **12** | **1** | −11 |
| Volumen documental (col. `VOLUMEN`) | **46.1581** | **92.3163** (exactamente ×2) | +100 % |
| Volumen a 45 mm declarado | no se lee | no se lee | — |
| MBF 6/4 calculado | 18.5138 (reproducido aparte) | no lo calcula | — |
| Export `+1/8"` calculado | 44.8610 | no lo calcula | — |

- El motor **duplica el volumen** por incluir la fila de totales y **colapsa los lotes** por no propagar el `N° LOTE` sintético; el núcleo hace lo contrario. Ninguna de las dos conductas es «la correcta»: son dos convenciones incompatibles de la misma lectura (A5).
- **Ninguna de las dos rutas lee** los `54.518` ni los `18.512`: el dato que el documento considera oficial queda fuera del sistema por ambos caminos.

### A9.2 `19846` recalculada desde sus propios datos `[VERIFICADO]`

| Magnitud | Almacenado | Recalculado con el código vigente | Δ |
|---|---|---|---|
| Compra (mm reales) | 47.152 | **47.152** | 0 |
| Export cabecera/lotes | 37.809 | **37.808** | −0.001 (redondeo) |
| Export líneas | 36.816 | 37.808 | **+2.70 %** |
| MBF lotes | 19.979 | (factor 2.3601 sobre `volumen_m3`) | 0 |
| MBF líneas (base `6/4`) | 15.604 | **15.602** (recalculado `1.5" × s2s × L_ft × pzas / 12 000`) | **−0.01 %** (redondeo) |
| F3 físico real | 0.000 (`no_aplica`) | 0.000 (`no_aplica`) | 0 |

### A9.3 El patrón se repite en todas las guías con líneas `[VERIFICADO]`

| Guía | Perfil/tipo | Cabecera `vol_shipment` | Σ líneas | Δ | MBF cab. | MBF líneas |
|---|---|---|---|---|---|---|
| `19846` | f5085 / service | 37.809 | 36.816 | **+2.70 %** | 19.979 | 15.604 |
| `19827` | f5085 / service | 35.359 | 34.561 | **+2.31 %** | 18.373 | 14.646 |
| `19826` | f5085 / service | 38.943 | 39.639 | **−1.76 %** | 20.245 | 20.246 |
| `26270` | f5085 / service | 47.893 | 48.009 | **−0.24 %** | 24.507 | 24.514 |
| `4495589` | f5085 / granel | 40.315 | 40.315 | 0 | 17.083 | **0.000** |

- `19846` y `19827` divergen **en el mismo sentido** (+2.3 % / +2.7 %), compatible con el cambio de sobreancho del 2026-10-18 sobre cabecera/lotes y no sobre líneas. `19826` y `26270` divergen en sentido contrario: conviven **cuatro** combinaciones distintas de cabecera/líneas.
- `4495589` (granel) pierde **todo** el MBF en las líneas (`0.000`) mientras la cabecera conserva `17.083`: 1 línea, `n=1`, cabecera con MBF y línea sin él.

### A9.4 Tamaño del problema en la BD auditada `[VERIFICADO]`

| Métrica | Valor |
|---|---|
| Líneas de guía totales | **82** |
| Líneas con `|vol_diff_pct| > 8 %` (tolerancia configurada) | **79 (96.3 %)** |
| Líneas con `|vol_diff_pct| > 25 %` | **6 (7.3 %)** |
| `vol_diff_pct` promedio | **−18.86 %** |
| Líneas con F3 `no_aplica` / `calculado` / `sin_mapeo` | **39 / 43 / 0** |
| Guías con perfil `f1550` | **0** |
| Guías con perfil `metric` | **1** (granel, 0 líneas) |
| Guías con rama F4 (`length_ft > 0.1`) | **3** (37 líneas) |

- **El 96 % de las líneas de la base está fuera del umbral del 10 %** y **ninguna** fue detenida: el umbral está hardcodeado en `mixin_lumber_ingest.py:478`, sólo alimenta `warning_msg`, y no tiene efecto sobre la validación.
- **`f1550` no tiene ni un solo caso** en esta BD: cualquier conclusión sobre ese perfil es **arquitectural, no empírica** `[NO VERIFICABLE]`.

### A9.5 Núcleo vs motor: veredicto de la comparación
`[VERIFICADO]` Sobre `40030`, las 12 líneas reales coinciden **exactamente** en piezas, dimensiones y volumen documental entre el motor nuevo y el núcleo. Las tres divergencias son: (1) el motor incluye la **fila de totales** como línea, (2) el motor **no propaga lotes sintéticos**, (3) el motor **no calcula** exportación ni MBF. La aritmética no es el problema; la **identidad de línea y de lote** y la **selección de la cifra oficial** sí.

### A9.6 Lo que esta auditoría no pudo verificar
- `[NO VERIFICABLE]` El origen exacto de `44.713` (ninguna combinación de sobreancho reproduce el valor; el par `18.512/44.713` sólo es coherente en la *razón*, no en el nivel).
- `[NO VERIFICABLE]` `40030` como registro: no existe guía, recepción ni línea con ese nombre en la BD auditada.
- `[NO VERIFICABLE]` El comportamiento de `f1550` en producción: sin casos en la BD.
- `[NO VERIFICABLE]` Qué escribió `vol_documental_m3` en su momento: hoy está `NULL` en **73 de 82** líneas (9 sí tienen valor) y el código lo escribe (`:2202`); en `19846` las 19 están vacías. Persiste la duda de si esa ruta no se ejecutó o si el campo se vació después.
- `[NO VERIFICABLE]` El impacto en costeo/valorización: requeriría leer `lumber.cost.distribution` y los asientos, fuera del alcance de FRENTE A.


---

# CIERRE FRENTE A

## C1 — Tabla de cobertura

| Pregunta | Sección | Estado | Evidencia principal |
|---|---|---|---|
| ¿Qué lee y qué guarda cada combinación tipo × perfil × modalidad? | A1 | `[VERIFICADO]` | `intake_wizard.py:440-1051`, `reception_parser.py:433-515` |
| ¿Qué hace exactamente el botón «Leer documento»? | A2 | `[VERIFICADO]` | `action_preview_document:579-680` |
| ¿Cómo se decide Producto vs Procesado? | A3, A8.2 | `[VERIFICADO]` con fallo | 4 palabras clave sobre el PDF; `40030` → Producto por «cepillada» vs «cepillado» |
| ¿Se lee el volumen a 45 mm declarado? | A4 | `[VERIFICADO]`: no | PDF `54,518` + celda oculta, ningún campo |
| ¿Cómo lee el núcleo y en qué se diferencia del motor? | A5 | `[VERIFICADO]` | 12 líneas idénticas; divergen totales y lotes |
| ¿Qué pasa al derivar a Procesado? | A6 | `[VERIFICADO]` | `:814-825` → `action_verify_data` inmediato |
| ¿De dónde sale cada cifra (18.512 / 44.713 / 54.518 / 38 vs 45)? | A7 | `[VERIFICADO]` 3 de 4 | `18.512` y `54.518` exactos; `44.713` no reproducible |
| ¿Qué guardas protegen la derivación? | A8 | `[VERIFICADO]` | 6 guardas, ninguna semántica; G6 anula G1-G5 |
| ¿Se sostiene el conjunto en la BD real? | A9 | `[VERIFICADO]` | 79/82 líneas fuera de tolerancia, 0 bloqueos |
| ¿Por qué hay dos volúmenes para la misma madera? | A7.5-A7.7 | `[INFERENCIA]` alta | parámetro `0.125` posterior a las líneas; prueba aritmética |
| Origen exacto de `44.713` | A7.9 | `[NO VERIFICABLE]` | sin registro de origen |
| Comportamiento real de `f1550` | A9.4 | `[NO VERIFICABLE]` | 0 casos en la BD |


## C2 — Causa raíz

**Una sola frase:** el sistema **no tiene una definición única de «volumen del documento»**, y por eso cada capa elige una distinta: el PDF declara `54.518` a 45 mm, el Excel declara `46.158` a 38.1 mm, la línea calcula exportación con y sin `+1/8"`, el lote deriva el MBF con `2.36` y la cabecera recalcula cuando cambia un parámetro global.

**Cadena causal `[VERIFICADO]`, en orden:**

| Eslabón | Qué ocurre | Consecuencia numérica |
|---|---|---|
| 1 | El clasificador sólo lee el PDF y busca `cepillado` (masculino) | `cepillada` no coincide → documento de servicio clasificado como Producto |
| 2 | El override manual se sobrescribe en cada `action_preview_document` | la corrección del usuario no persiste |
| 3 | Ni el núcleo ni el motor leen el volumen a 45 mm del PDF/celda oculta | `54.518` y `18.512` nunca entran al sistema |
| 4 | El espesor se normaliza por rango (`37-46 → 6/4`) | `45 mm` se convierte en `38.1 mm` para el MBF → −18.1 % |
| 5 | La exportación usa `s2s + 1/8"` tomado de un parámetro global, no de la línea | líneas guardan `w` sin `1/8`, lotes/cabecera con `1/8` → +2.7 % |
| 6 | El MBF se calcula con dos bases distintas (línea `6/4`, lote `m³/2.36`) | 15.604 vs 19.979 → +28.0 % |
| 7 | La discrepancia se detecta (`warning_msg`, `vol_diff_pct`) pero ninguna guarda la consulta | 79/82 líneas fuera de tolerancia, 0 bloqueos |

**Consecuencia de negocio:** el ingreso es correcto en **piezas y dimensiones** e incorrecto (o al menos no único) en **volumen y MBF**. Todo lo que se derive de esos dos campos —costeo, mermas, liquidación, reportes de exportación— hereda la ambigüedad.

## C3 — Matriz de dependencias (quién consume qué)

| Campo | Lo escribe | Lo consume | Si cambia, se rompe |
|---|---|---|---|
| `vol_purchase_m3` (línea) | `_parse_packing_excel` `:2199-2201` + compute métrico | `vol_physical_m3`, lotes `volumen_m3`, costeo | valorización de compra |
| `vol_shipment_m3` (línea) | compute F4 `:600-674` | lotes `vol_shipment_m3`, reportes de exportación | conciliación de embarque |
| `vol_mbf` (línea) | compute `6/4` | reportes MBF, comparativas con proveedor | control de rendimiento |
| `volumen_mbf` (lote) | `stock.lot` desde `volumen_m3` (`:1675-1678`) | cabecera `vol_total_mbf`, costeo por pie | informe de compra |
| `vol_comercial` / `vol_fisico` (guía) | compute de líneas | pantalla de la guía, validación comercial | cuadre con PDF (`vol_comercial_pdf`) |
| `vol_comercial_pdf` | parser PDF `:2233-2265` | comparativa visual | — |
| `warning_msg` | compute por línea | **nadie** (sólo UI) | — |
| `vol_diff_pct` | compute | **nadie** (sólo UI) | — |
| `technical_validation` | `pending` al crear (`:2216`), `approved` en lote (`:2849`) | filtros de UI | — |

- `[VERIFICADO]` Los tres campos que gobiernan dinero (`vol_purchase_m3`, `volumen_m3`, `volumen_mbf`) se calculan en **tres lugares distintos** con **tres bases distintas**; los dos campos que detectan el problema (`warning_msg`, `vol_diff_pct`) **no son leídos por ningún método** (`grep` de ambos nombres en `madenat_lumber_core` devuelve sólo sus computes y las vistas).

## C4 — Solución mínima (propuesta, sin implementar)

Ordenada por relación coste/beneficio. Ninguna requiere migrar datos.

| # | Cambio | Dónde | Riesgo | Efecto |
|---|---|---|---|---|
| 1 | Leer y guardar el **volumen declarado** (PDF y celda oculta) en `vol_documental_m3` | `_parse_packing_excel` `:2185-2202` | bajo | da una referencia contra la que comparar; activa `vol_diff_pct` con base real |
| 2 | **Un único dueño del volumen de exportación**: que el lote lea `vol_shipment_m3` de la línea, no lo recalcule | `:1675-1678` | medio | elimina la contradicción línea/lote (1.261 vs 1.305) |
| 3 | **Fijar la base del `+1/8` en la línea** (`overwidth_inches` copiado a la línea al crear) en vez de leer el parámetro en cada compute | `:600-674` + campo | medio | congela el valor; los históricos dejan de moverse al cambiar el parámetro |
| 4 | **Gate de discrepancia en `action_validate`**: si `|vol_diff_pct| > 10` (hoy hardcodeado en `mixin_lumber_ingest.py:478`) exigir `reconciliation_status != 'none'` (patrón G5: confirmación explícita) | `:2573-2668` | bajo | convierte un aviso decorativo en control firmado |
| 5 | Corregir el clasificador: normalizar género/plural (`cepillad`) o leer también el Excel | `:549-577` | bajo | `40030` deja de clasificarse como Producto |
| 6 | No sobrescribir `tipo_ingreso` si el usuario lo cambió a mano (guardar `tipo_ingreso_manual`) | `:566-577` | bajo | la corrección del usuario persiste |

- `[HIPÓTESIS]` 1 + 4, por sí solos, habrían detenido `19846` (19/19 líneas con discrepancia > 20 % respecto del declarado) sin tocar ninguna fórmula.


## C5 — DEPENDENCIAS DEL NÚCLEO (lo que no se puede tocar a ciegas)

Lo que el motor nuevo (y cualquier FRENTE futuro) **hereda o puede romper** del módulo `madenat_lumber_core`:

| Dependencia | Dónde vive | Naturaleza | Qué pasa si cambia |
|---|---|---|---|
| `_parse_excel_data_core` | `madenat_guia_processing.py:3669+` | Lector semántico único del núcleo | Lo usan Procesado y (vía workflow) Producto; el engine **no** lo usa |
| `detect_excel_table_across_sheets` | `excel_table_detection.py:1-24` | Helper puro, sin ORM | Base de la detección de tabla; el engine tiene su propio detector |
| `MixinLumberIngest` (`warning_msg`, `reconciliation_status`, `vol_diff_pct`) | `mixin_lumber_ingest.py:452-483` | Campos compartidos línea/lote | Cualquier cambio afecta a **todas** las líneas históricas |
| `resolve_export_width_details` | `madenat_ingestion_config.py:245-340` | Fuente única del ancho de exportación | Cambia F4 de toda la base y de los históricos que se recalculen |
| `madenat.width_s2s_map` (modelo) | `lumber_width_s2s_map.py` | 15 filas, `overwidth=0` | Es la tabla real; el parámetro homónimo **no** se lee |
| Parámetros `madenat.s2s_overwidth_inches` / `direct_width_min_mm` / `out_of_table_behavior` | `ir.config_parameter` | Configuración global sin historial | Cambian cálculos nuevos; los viejos quedan inconsistentes con la cabecera |
| `Gate3PreCommit` (firma SHA-256) | `action_validate:2666-2670` | Notarización del ciclo | Cambiar líneas después de validar rompe la huella |
| `stock.lot.volumen_mbf` | `stock_lot.py:876-891` | Derivado `m³/2.36` | Base del MBF de cabecera |
| `technical_validation` (línea vs lote) | `:2216` vs `:2849` | Estados contradictorios | Cualquier gate futuro debe decidir **cuál** de los dos manda |

- `[VERIFICADO]` El motor nuevo **no depende** de ninguno de ellos: `extract_document` es independiente y no escribe en el núcleo. La dependencia es **unidireccional**: el motor puede evolucionar sin tocar el núcleo, pero **mientras el núcleo siga siendo quien persiste**, todo cambio de fórmula en el núcleo redefine el significado de los datos del motor.

## C6 — Diseño de marca de advertencia (especificación consolidada)

Ver A8.4 para la justificación. Especificación mínima, sin implementar:

| Elemento | Tipo | Contenido | Origen del dato |
|---|---|---|---|
| `rate_discrepancy_pct` | `Float` (línea) | `(declarado − calculado) / declarado × 100` | `vol_documental_m3` vs `vol_purchase_m3` |
| `volume_discrepancy_state` | `Selection` (cabecera) | `ok` / `warning` / `critical` | `|Σ declarado − Σ calculado| / Σ declarado` vs `madenat.volume_discrepancy_tolerance` |
| `discrepancy_ack_user_id` / `discrepancy_ack_date` | `Many2one`/`Datetime` (cabecera) | quién y cuándo aceptó | `action_validate` |
| Marca visual | badge en la línea y en la cabecera | 🟢 / 🟡 / 🔴 con el porcentaje | `volume_discrepancy_state` |
| Mensaje | `warning_msg` (ya existe) | `Declarado 3.750 m³ / Calculado 3.104 m³ (20.9 %)` | nueva fórmula |
| Registro | `message_post` | «Ingreso con discrepancia 20.9 % aceptada por …» | `action_validate` |

- Regla de oro: **la marca nunca inventa el «volumen oficial»**; sólo hace visible que hay dos y obliga a que alguien lo firme.

## C7 — PREGUNTAS ABIERTAS (para negocio, no para el código)

1. **¿Cuál es el volumen oficial de un ingreso: el declarado por el proveedor o el cubicado por el sistema?** Hoy conviven ambos y ninguno está marcado como tal.
2. **¿El espesor comercial de la madera cepillada es 45 mm o 6/4"?** El PDF dice 45 mm, el sistema factura a 38.1 mm; la diferencia es 18.1 %.
3. **¿El `+1/8"` debe aplicarse al volumen de exportación?** Está configurado en `0.125` desde el 2026-10-18 y afecta a toda la base, pero las líneas guardadas no lo tienen.
4. **¿El MBF de una guía debe calcularse con `6/4` o con `m³/2.36`?** Líneas y lotes usan bases distintas para el mismo campo.
5. **¿«Cepillada» es un servicio (Procesado) o un producto?** El clasificador dice Producto por una vocal; el negocio decidió Procesado al usar el wizard.
6. **¿Se acepta validar con discrepancia > 10 %?** Si la respuesta es sí, hace falta registrar quién lo autoriza; si es no, hace falta el gate.
7. **¿Qué debe pasar con `f1550`?** No hay ningún caso en la BD: ¿es un perfil en desuso, pendiente de estreno o roto y nadie lo ha usado?
8. **¿Los históricos deben recalcularse?** `19846`, `19827`, `19826` y `26270` tienen cabecera y líneas con bases distintas; recalcular cambia cifras ya validadas y firmadas (Gate3).

## C8 — Frase final

> **El sistema lee bien el documento y no sabe cuál de sus propios números es el del documento; mientras eso siga así, cada capa elige uno distinto y ninguna lo firma.**

*(Frase de cierre exacta del FRENTE A. Cierra el arco A1→A9: la lectura —el parser, los tres filtros, la identidad de lote— está resuelta; lo que falta es una decisión de negocio sobre qué cifra es la oficial y un control que la haga cumplir.)*

---

**Fin del FRENTE A.** Este informe no modificó código, vistas, datos ni manifiestos; no se ejecutaron upgrades ni reinicios. Todas las consultas a la BD fueron `SELECT`. Las únicas escrituras son este archivo y `INFORME_FRENTE_B.md`.

