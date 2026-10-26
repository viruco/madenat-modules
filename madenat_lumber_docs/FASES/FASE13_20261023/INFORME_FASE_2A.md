# FASE 13 — SUBFASE 2A · Informe de implementación acotada

**Proyecto:** MADENAT · Odoo 18 CE
**Fecha:** 2026-10-23
**Rama:** `fase13-2a-lectura` (creada desde `e672fc4`)
**Alcance ejecutado:** ítems 1–4 de la Subfase 2A, en `madenat_lumber_intake`.
**Estado:** código y documentación listos; **upgrade NO ejecutado** (prohibido por la tarea).
**Base usada para la prueba en seco:** `madenat_test` (solo `SELECT` y lectura de filestore).

---

## 0. Resumen ejecutivo

| Ítem | Resultado | Evidencia |
|---|---|---|
| 1. Clasificador robusto + migración | Implementado. Comparación por raíz, sin acentos y con abreviaturas sobre **señales relevantes**; se descarta el texto legal (SII). Migración `18.0.0.21.0`. | `models/intake_classifier.py`, `models/intake_wizard.py:582-680`, `migrations/18.0.0.21.0/post-migrate.py` |
| 2. Marca de advertencia | Implementada y **no bloqueante** (`reading_warning` / `has_reading_warning`), visible en formulario y lista; sin popups. | `models/intake_wizard.py:97-110,636-668`, `views/intake_wizard_views.xml:59-63,157-163,198` |
| 3. Totales del packing | `sum=` en volumen de compra, exportación, MBF, costo e importe de las fachadas de intake. | `views/intake_reception_facade_views.xml:169-173`, `views/intake_guia_processing_facade_views.xml:230-231,245,248`, `views/intake_console_views.xml:997,1017-1018,1031,1034` |
| 4. Documentación | README actualizado (señales, marca, requisitos reales, migración, riesgos y decisiones). | `README.md` §4, §8.1, §8.2, §12–§16, §18 |

- **Prueba en seco:** 21 documentos registrados (13 guías + 8 recepciones). **7 cambian de tipo**, todos `procesado → producto`, y **los 7 son eliminación de falsos positivos** (texto legal o adjetivo de artículo). **0 cambios injustificados** y **0 cambios hacia `procesado`**.
- **Núcleo intacto:** `git diff e672fc4..HEAD` solo contiene `madenat_lumber_intake/**` (11 archivos). `madenat_lumber_core` y `madenat_ingestion_engine` sin cambios.
- **Tests:** escritos y compilados; **no ejecutados** (requieren upgrade o escritura en BD, prohibidos). Validación alternativa documentada en §5.

### 0.1 Contradicciones detectadas y cómo se resolvieron

| ID | Hallazgo | Resolución |
|---|---|---|
| C-1 | El informe A3.2 proponía añadir `"cepillad"` (raíz) como keyword **decisiva**. La prueba en seco demuestra que «Madera … Cepillada» aparece igual en **compras S2S ya registradas como Producto**: tratarla como decisiva desvía 6 documentos sin justificación. | Se separó el vocabulario: `cepill`/`cep.` son **señal de artículo (débil)**, decisiva solo en nombre de archivo y título del documento; en glosa/producto solo generan advertencia. |
| C-2 | `madenat_lumber_core/tests/test_ingestion_keywords_seed.py` (T-KEY-01 y T-KEY-05) exige **igualdad exacta** entre `madenat.tipo_ingreso_keywords` y la lista legacy. El núcleo es solo lectura. | El vocabulario decisivo **no se modificó**. El vocabulario nuevo vive en el parámetro propio `madenat.tipo_ingreso_weak_keywords`. Riesgo registrado como R7 del README. |
| C-3 | La consola es una vista SQL (`_auto=False`) sobre tablas del núcleo; mostrar la marca exige una columna del núcleo. | Consola **no tocada**. Alternativa mínima: la marca se ve en el formulario/lista del wizard y viaja en la descripción de `madenat.audit.log`. |

> Ninguna de estas contradicciones afecta a los informes A/B en sus hechos verificados: A3.1(2) y A8.2 describían correctamente el clasificador anterior; lo que cambia es la **decisión de diseño** derivada de la prueba en seco.

---

## 1. Ítem 1 — Clasificador de tipo de ingreso

### 1.1 Qué cambió

**Nuevo módulo puro** `madenat_lumber_intake/models/intake_classifier.py` (440 líneas, sin ORM):

| Elemento | Línea | Función |
|---|---|---|
| `TITLE_LINES = 3`, `MAX_PRODUCT_LINES = 200` | `:35,37` | cotas de la zona de título y del volumen de señales |
| `SOURCE_ORDER` / `SOURCE_LABELS` | `:39-48` | orden determinista y etiquetas para la evidencia |
| `KNOWN_UNITS` | `:51-54` | unidades de origen aceptadas (`mm`,`cm`,`m`,`in`,`inch`,`pulg`,`pies`,`ft`,`mt`,`mts`,`m3`,`m2`) |
| `DETECTED_PROFILE_CODES` | `:59-62` | perfil del motor → perfil de lectura del wizard |
| `STRONG_SOURCES`, `WEAK_KEYWORDS_DEFAULT` | `:72-73` | señales fuertes (`filename`, `pdf_title`) y vocabulario de artículo por defecto (`cepill`, `cep.`) |
| `_NOISE_RE` | `:77-88` | ruido institucional/legal: «impuestos internos», SII, RUT, timbraje, timbre electrónico, resolución, firma electrónica, URL, correo |
| `_ADMIN_RE` | `:96-99` | filas administrativas: transportista, chofer, patente, comuna, dirección, giro, vendedor, teléfono, correo |
| `_PRODUCT_HEADER_RE`, `_NUMBER_RE` | `:79-80` | cabecera de tabla y magnitudes numéricas |
| `strip_accents` / `normalize` | `:109-121` | NFKD sin diacríticos, minúsculas, puntuación → espacio |
| `_stem` / `keyword_variants` | `:124-144` | raíz morfológica de una pasada (`cepillado → cepill`), raíz mínima 4 letras |
| `_variant_pattern` | `:147-150` | regex de raíz **al inicio de palabra** (`(?<![0-9a-z])`) |
| `_dotted_abbreviations` / `match_keywords` | `:153-201` | abreviaturas punteadas (`CEP.`) como prefijo (≥3 letras) de una variante |
| `pdf_signals` | `:218-247` | título (3 primeras líneas útiles) + filas de producto (≥2 números o tras cabecera) |
| `collect_signals` | `:258-268` | mapa `source → texto` con las 4 señales |
| `classify` | `:271-319` | separa evidencia **decisiva** y **advisory** por fuente |
| `advisory_message` | `:332-340` | texto de la señal débil |
| `profile_message` | `:343-364` | perfil no detectable / no reconocido / distinto del elegido |
| `unit_stats` / `unit_message` | `:367-401` | dimensiones sin unidad y unidades desconocidas |
| `no_signal_message` | `:404-419` | ausencia de señal de tipo |
| `build_reading_warnings` | `:422-438` | composición de la marca (una línea por caso) |

**Wizard** (`models/intake_wizard.py`): `_classify_normal_document` (`:670-680`) ya no hace `in` de subcadena sobre el PDF completo; ahora:

| Método | Línea | Responsabilidad |
|---|---|---|
| `_reading_keywords` | `:582-607` | vocabulario decisivo (`get_tipo_ingreso_keywords('procesado')`) + débil (`madenat.tipo_ingreso_weak_keywords`, default de código) |
| `_extract_pdf_text_safe` | `:609-618` | texto del PDF, cadena vacía si no es legible |
| `_reading_signals` | `:620-634` | señales + `description`/`product_name_original` del Excel cuando ya se leyó |
| `_reading_analysis` | `:636-657` | clasifica y compone la marca |
| `_write_reading_result` | `:659-668` | persiste tipo + marca (sin popups) |
| `_classify_normal_document` | `:670-680` | punto de entrada; conserva el contrato (`tipo_ingreso`, `tipo_ingreso_auto_detectado`, `classification_result`) |
| enriquecimiento con Excel | `:744-757` | tras `extract_document` añade producto del Excel, perfil y unidades; solo puede **ascender** a Procesado, nunca degradar |
| una sola extracción de PDF | `:690-694` | `pdf_text` se calcula una vez y se reutiliza |



### 1.2 Señales usadas (y solo estas)

| Señal | Fuente | Fuerte/débil | Por qué |
|---|---|---|---|
| `filename` | `pdf_filename` + `excel_filename` sin extensión | fuerte | el operador o el archivo declara la naturaleza («… (cepillado) …», «SERVICIO …») |
| `pdf_title` | 3 primeras líneas útiles del PDF (tras descartar ruido y filas administrativas) | fuerte | el título del documento declara, no describe el artículo |
| `pdf_product` | líneas con ≥2 magnitudes numéricas, o las que siguen a `DESCRIPCIÓN/GLOSA/DETALLE/PRODUCTO/ESPECIE` | débil | la glosa describe el artículo: «madera cepillada» se compra **y** se maquila |
| `excel_product` | `description` / `product_name_original` de `extract_document` | débil | idem: el packing nombra el artículo, no el servicio |

- **Fuera de señal:** todo el resto del texto del PDF (condiciones legales, timbraje, pie de página). Esto elimina el falso positivo de «Servicio de Impuestos Internos» y de «mercaderías o servicio(s) prestado(s)».
- El vocabulario de **servicio** (`servicio`, `maquila`, `proceso`) sigue siendo decisivo en **cualquier** señal; el de **artículo** (`cepill`, `cep.`) solo en `filename`/`pdf_title`.

### 1.3 Vocabulario y migración

- **Decisivo:** `madenat.tipo_ingreso_keywords` — **sin cambios** (`["cepillado","servicio","proceso","maquila"]`). Se sigue leyendo por `madenat.ingestion.config.get_tipo_ingreso_keywords('procesado')` (fuente única, con fallback del núcleo).
- **Débil (nuevo):** `madenat.tipo_ingreso_weak_keywords` — `["cepill","cep."]`, con `WEAK_KEYWORDS_DEFAULT` como valor por defecto del código si el parámetro falta o es inválido.
- **Migración** `migrations/18.0.0.21.0/post-migrate.py` (118 líneas):
  - crea `madenat.tipo_ingreso_weak_keywords` **solo si no existe** (nunca pisa personalizaciones);
  - del parámetro vigente solo normaliza cuando su contenido normalizado es **exactamente** el seed canónico (misma lista y orden); cualquier personalización se registra en log y se deja intacta;
  - idempotente y sin ORM (`cr` directo, mismo patrón que `18.0.0.2.0`);
  - manifest `18.0.0.20.0 → 18.0.0.21.0`.

### 1.4 Por qué

A8 demostró que la decisión más importante del flujo se toma con la evidencia más débil: cuatro subcadenas sobre el texto completo del PDF, sin normalizar tildes. Con el vocabulario vigente, `Cepillada` y `PINO CEP. SECO LATERAL` caían en **Producto** (femenino vs. masculino; abreviatura `CEP.`), mientras el texto legal del SII hacía caer en **Procesado** guías de compra. La comparación por raíz + abreviaturas resuelve la morfología; las señales resuelven el ruido.

### 1.5 Riesgo

| Riesgo | Nivel | Mitigación |
|---|---|---|
| Falso negativo: servicio real descrito **solo** como «cepillada» en la glosa queda en Producto | Medio | queda **marcado** («Posible servicio…»); el operador puede corregir el tipo antes de «Continuar ingreso» |
| Falso positivo por «servicio» en texto administrativo | Bajo | `_NOISE_RE` + `_ADMIN_RE`; verificado contra 21 documentos reales |
| Personalización futura del vocabulario débil | Bajo | parámetro JSON validado, con default de código |
| Coste de lectura | Bajo | una sola extracción de PDF por «Leer documento» (antes: una) y una de Excel (preexistente) |
| Retrocompatibilidad del contrato | Bajo | `classification_result` sigue devolviendo `Procesado`/`Producto`; T-KEY-01/02/05 del núcleo siguen siendo válidos |



### 1.6 Prueba en seco (solo lectura) contra los documentos ya registrados

**Método.** Script externo `/tmp/fase13_2a_dryrun.py` (no forma parte del repositorio):

1. `SELECT` sobre `madenat_guia_processing` (13) y `lumber_reception` (8) en `madenat_test`.
2. Lectura del adjunto desde filestore con `docker exec odoo18_app cat` (sin escritura).
3. Texto del PDF con `pdfplumber` (misma función que `_extract_pdf_text`); nombres de producto con `extract_document` del motor.
4. Comparación: **ANTES** (subcadena sobre PDF en `casefold`) vs. **AHORA** (señales + raíz + abreviaturas + enriquecimiento con Excel).
5. Vocabularios usados: decisivo `["cepillado","servicio","proceso","maquila"]`; débil `["cepill","cep."]`.

**Resultado global: 21 documentos → 7 cambian de tipo (33 %); 0 cambian hacia Procesado; 0 sin justificación.**

| # | Modelo | ID | Nombre | Rama actual | ANTES | AHORA | Motivo del cambio |
|---|---|---|---|---|---|---|---|
| 1 | guía | 1196 | 19846 | service | Procesado | Procesado | sin cambio (archivo «… (cepillado)…» + glosa «servicio») |
| 2 | guía | 1198 | 19827 | service | Procesado | Procesado | sin cambio |
| 3 | guía | 1256 | 19826 | service | Procesado | Procesado | sin cambio |
| 4 | guía | 1728 | 26270 | service | Procesado | Procesado | sin cambio (glosa «servicio») |
| 5 | guía | 15326 | 4495589 | granel | Procesado | **Producto** | antes: «prestación de todo tipo de **servicios**» (texto legal). Es guía granel: la modalidad no usa el clasificador |
| 6 | guía | 32298 | UAT-SV-20261003-01 | granel | Procesado | **Producto** | ídem #5 (mismo PDF) |
| 7 | guía | 32300 | UAT-SV-20261003-IMPG | granel | Producto | Producto | sin documentos: sin cambio |
| 8 | guía | 32346 | 900002 | service | Producto | Producto | «MADERA SECA CEPILLADA» en Excel = señal débil → solo advertencia |
| 9 | guía | 32411 | UATRB-GUIA-01 | granel | Producto | Producto | sin documentos |
| 10 | guía | 32689 | UAT-INT-20261004-RECEPTION | compra | Producto | Producto | sin PDF legible; sin cambio |
| 11 | guía | 33151 | 95806 | granel | Procesado | **Producto** | antes: «SERVICIOS(S) PRESTADO(S) HA(N) SIDO RECIBIDO(S)» (pie legal) |
| 12 | guía | 33250 | 95083 | service | Procesado | **Producto** | antes: «mercaderías o **servicio(s)**» (pie legal). Ver nota ⚠ |
| 13 | guía | 33737 | V3-CONCIL | service | Producto | Producto | sin documentos |
| 14 | recepción | 962 | 41471 | producto | Producto | Producto | «Madera … **Cepillada**» en glosa = señal débil → advertencia |
| 15 | recepción | 1161 | 39519 | producto | Producto | Producto | ídem #14 |
| 16 | recepción | 1244 | 97183 | producto | Procesado | **Producto** | antes: `cepillado` como subcadena decisiva; ahora es señal de artículo → advertencia |
| 17 | recepción | 1270 | 100006 | producto | Procesado | **Producto** | ídem #16 |
| 18 | recepción | 1369 | 15183 | producto | Procesado | **Producto** | antes: «entrega de mercaderías o **servicio(s)** prestado(s)» (pie legal) |
| 19 | recepción | 1371 | 41964 | producto | Producto | Producto | «Cepillada» en glosa = señal débil |
| 20 | recepción | 7900 | 900001 | producto | Producto | Producto | «MADERA SECA CEPILLADA» en Excel = señal débil |
| 21 | recepción | 7950 | 41994 | producto | Producto | Producto | «Cepillada» en glosa = señal débil |

**Justificación de los 7 cambios:** los 7 alinean el clasificador con la rama real del documento (Producto) y eliminan falsos positivos:
- 4 por **texto legal** (#5, #6, #11, #12, #18: «servicios prestados», «mercaderías o servicio(s)», «prestación de todo tipo de servicios»);
- 3 por **adjetivo de artículo** (#16, #17: `cepillado` en la glosa de compras imperiales/clear).
- Ningún documento pasó de Producto a Procesado: la dirección peligrosa (desviar compras al flujo de servicio) **no se produce**.

> ⚠ **Nota sobre #12 (guía 33250, `tipo_recepcion=service`)**: su PDF solo contiene el pie legal; no hay señal de servicio en archivo, título ni glosa. El clasificador anterior la marcaba Procesado por ese pie legal. **No se modifica el registro** (la prueba en seco no escribe); si en el futuro se reintroduce el mismo documento, quedará en Producto **con advertencia**. Es el único caso que conviene confirmar con negocio (ver §7, pregunta abierta).

**Casos de control (clasificador puro, ejecutado):**

| Texto | Resultado | Marca |
|---|---|---|
| `Cepillada` | Procesado | — |
| `CEPILLADO` | Procesado | — |
| `PINO CEP. SECO LATERAL` | Procesado | — |
| `SERVICIO CEPILLADO` | Procesado | — |
| `MADERA ASERRADA BRUTA 2 X 4 X 3.2 100 1.234` | Producto | «Sin señal de tipo…» |
| PDF con «Servicio de Impuestos Internos» + aserrado bruto | Producto | «Sin señal de tipo…» |
| `MADERA SECA CEPILLADA` (Excel/glosa) | Producto | «Posible servicio (señal de artículo…)» |
| `SERVICIO Y TRANSPORTES SAEZ LTDA 13956258-5` | Producto | — (fila administrativa) |

---


## 2. Ítem 2 — Marca de advertencia de lectura

### 2.1 Qué cambió

| Archivo:línea | Cambio |
|---|---|
| `models/intake_wizard.py:97-110` | campos `reading_warning` (Text, readonly, `copy=False`) y `has_reading_warning` (Boolean, readonly, default `False`) |
| `models/intake_wizard.py:636-668` | `_reading_analysis` compone la marca; `_write_reading_result` la persiste junto al tipo |
| `models/intake_wizard.py:744-757` | enriquecimiento con el Excel ya leído (perfil y unidades) |
| `models/intake_wizard.py:1450-1466` | `_log_intake_origin` añade «Advertencia de lectura: …» a la descripción de `madenat.audit.log` |
| `views/intake_wizard_views.xml:59-63` | indicador ⚠ + texto corto en el bloque «Destino del ingreso» |
| `views/intake_wizard_views.xml:157-163` | alerta `alert-warning` con icono `fa-exclamation-triangle` y el texto completo |
| `views/intake_wizard_views.xml:198` | columna `has_reading_warning` en la lista (opcional) |

### 2.2 Casos cubiertos

| Caso | Cuándo | Mensaje | ¿Cambia el tipo? |
|---|---|---|---|
| **Sin señal de tipo** | no hay coincidencia decisiva ni advisory | «Sin señal de tipo en las señales revisadas (…). Se conserva el tipo por defecto» | No: se mantiene `producto` (default) |
| **Señal de artículo** | `cepill`/`cep.` en glosa o nombre de producto | «Posible servicio (señal de artículo, no de servicio): … NO se cambió el tipo» | No |
| **Perfil no detectable** | `extract_document` no devuelve `detected_profile_code` | «Perfil de lectura no detectable…» | No |
| **Perfil distinto** | el detectado no está entre los compatibles con el elegido | «El perfil detectado (X) no coincide con el elegido (Y)» | No |
| **Unidad no reconocida** | dimensión con valor y sin unidad, o unidad fuera de `KNOWN_UNITS` | «Unidad no reconocida: …» | No |

- **Nunca bloquea**: ningún `UserError`, ningún `raise`, ningún popup nuevo. La marca es informativa y persistida.
- El flujo **«Leer documento» → «Continuar ingreso»** no gana pasos: la marca aparece en la misma pantalla.
- La rama **Procesado** no parsea el Excel (por diseño, T2): allí solo se evalúan señal de tipo y artículo. Perfil/unidad se evalúan en la prelectura de **Producto**, que es donde el motor lee el packing.

### 2.3 Consola (vista SQL) — alternativa mínima reportada

La consola `madenat.lumber.intake.console` es `_auto=False` y su `init()` construye una vista PostgreSQL sobre tablas del núcleo (`models/intake_console.py:600`). Mostrar `reading_warning` exigiría **una columna nueva en el núcleo** (prohibido) o reescribir la vista SQL añadiendo una subconsulta a la tabla del wizard (cambio mayor y con coste por fila). Se eligió la alternativa mínima:

1. marca visible en el formulario y la lista del wizard (antes de derivar);
2. marca persistida en la descripción de `madenat.audit.log` al derivar (consultable en el chatter del destino y en Auditoría).

La consola **no se tocó** (confirmado en §6).

### 2.4 Riesgo

| Riesgo | Nivel | Comentario |
|---|---|---|
| Ruido de advertencias en documentos sin señal | Bajo | es informativo y no bloquea; el operador decide |
| Doble extracción del Excel en Producto | Bajo | `_check_profile_coherence` ya extraía; no se añade una tercera |
| La marca no se ve en la consola | Bajo | alternativa en wizard + auditoría (R8 del README) |

---


## 3. Ítem 3 — Totales en el packing (`sum=`)

### 3.1 Qué cambió

| Vista (propiedad de intake) | Línea | Campo | Etiqueta del total |
|---|---|---|---|
| `views/intake_reception_facade_views.xml` | `:169` | `vol_purchase_m3` | Total volumen de compra (m³) |
| | `:170` | `vol_shipment_m3` | Total volumen de exportación (m³) |
| | `:171` | `vol_mbf` | Total MBF |
| | `:173` | `cost_clp_unit` (monetary) | Total costo (CLP) |
| `views/intake_guia_processing_facade_views.xml` | `:230` | `vol_purchase_m3` | Total volumen de compra (m³) |
| | `:231` | `vol_shipment_m3` | Total volumen de exportación (m³) |
| | `:245` | `volume_m3` (detalle documental) | Total volumen (m³) |
| | `:248` | `line_amount` (detalle documental) | Total importe |
| `views/intake_console_views.xml` | `:997` | `vol_purchase_m3` (packing Producto) | Total volumen de compra (m³) |
| | `:1017` | `vol_purchase_m3` (packing Procesado) | Total volumen de compra (m³) |
| | `:1018` | `vol_shipment_m3` | Total volumen de exportación (m³) |
| | `:1031` | `volume_m3` (detalle documental) | Total volumen (m³) |
| | `:1034` | `line_amount` | Total importe |

Notas:
- `intake_volume_detail_line_views.xml` solo define un **formulario** (sin lista): no admite `sum=` y no se tocó.
- El campo `cost_clp_unit` es costo unitario; su `sum=` es el **importe agregado de la columna**, etiquetado explícitamente como «Total costo (CLP)» para no confundirlo con un costo unitario.
- No se añadió `sum=` a columnas que no son de packing (totales de cabecera, `official_volume_m3`, grilla declarada), para no duplicar cifras ya totalizadas.

### 3.2 ¿Alguna vista del núcleo?

No. Las tres vistas afectadas se declaran en `madenat_lumber_intake/views/*.xml` sin `inherit_id` (verificado con `grep -n 'inherit_id'`), es decir, son **registros propios del módulo intake**. No se modificó ninguna vista de `madenat_lumber_core`. Dependencia del núcleo: solo los campos (`vol_purchase_m3`, `vol_shipment_m3`, `vol_mbf`, `cost_clp_unit`, `volume_m3`, `line_amount`), consumidos en modo lectura.

### 3.3 Riesgo

| Riesgo | Nivel | Comentario |
|---|---|---|
| `sum=` sobre campo monetario sin `currency_id` visible en la lista | Bajo | el importe se muestra como número; no altera datos ni cálculos |
| Listas con cientos de líneas | Bajo | el total lo calcula el cliente sobre las filas cargadas (paginación estándar de Odoo) |

---

## 4. Ítem 4 — Documentación

`madenat_lumber_intake/README.md` actualizado:

| Sección | Cambio |
|---|---|
| §4 Requisitos | reemplazada la regla «tres requisitos siempre» por la **matriz real** modalidad × documentos × estado (normal/Producto, normal/Procesado, volume) |
| §8 Flujo | paso 3–4 corregidos (adjuntar **no** clasifica; la clasificación ocurre en «Leer documento»); paso 8 incluye la marca en auditoría |
| §8.1 (nueva) | señales del clasificador, tabla fuerte/débil, ruido descartado, comparación por raíz/abreviaturas, los dos vocabularios |
| §8.2 (nueva) | marca de advertencia: campos, casos, «nunca bloquea», límite de la rama Procesado y alternativa para la consola |
| §12 Wizard | mención del aviso ⚠ y de la columna de lista |
| §13 Pruebas | T2A-1…T2A-5 y tests de contrato XML |
| §14 Migraciones | migración `18.0.0.21.0`, versión actual y «pendiente de upgrade» |
| §15 Estado | conteos reales (8 recepciones, 13 guías) y versión instalada vs. código |
| §16 Riesgos | R7 (paridad de keywords del núcleo) y R8 (marca no visible en la consola) |
| §18 Decisiones | 5 decisiones nuevas fechadas 2026-10-23 |

---

## 5. Pruebas

### 5.1 Tests añadidos

`tests/test_intake_wizard.py` (T1–T6 intactos):

| Test | Cubre |
|---|---|
| `test_t2a_raiz_tildes_y_abreviaturas` | `Cepillada`, `CEPILLADO`, `PINO CEP. SECO LATERAL`, `SERVICIO CEPILLADO` → Procesado, sin marca |
| `test_t2a_sin_senal_mantiene_default_y_marca` | producto sin señal → Producto + `has_reading_warning` y texto «Sin señal de tipo» |
| `test_t2a_texto_legal_sii_no_clasifica_procesado` | PDF con «Servicio de Impuestos Internos» + aserrado bruto → Producto |
| `test_t2a_cepillada_en_glosa_es_senal_debil` | glosa real de compra → Producto + «Posible servicio» |
| `test_t2a_perfil_y_unidad_en_marca_de_advertencia` | perfil detectado ≠ elegido + unidad `yard`/sin unidad → tres mensajes |

`tests/test_intake_wizard_view.py`:

| Test | Cubre |
|---|---|
| `test_marca_advertencia_visible_en_formulario` | `reading_warning` y `has_reading_warning` presentes en el formulario |
| `test_totales_packing_en_vistas_de_fachada` | `sum=` en ≥1 lista de cada fachada (recepción, guía, consola) |

### 5.2 Idempotencia (T5) y error conocido (T6)

Sin cambios en el código que los gobierna: `_existing_target`/`_persist_target` y el manejo de `UserError` en `_route_producto`/`_route_procesado` no se tocaron. T5 (doble clic → un destino y un evento) y T6 (error conocido → sin destino ni evento) siguen aplicando tal cual.

### 5.3 Ejecución

- **No ejecutados.** La tarea prohíbe `-u`, reiniciar servicios y escribir en la base; los tests de Odoo requieren instalación/upgrade del módulo o una BD de test.
- **Validaciones alternativas ejecutadas:**
  - `python3 -m py_compile` sobre los 5 archivos Python modificados/creados → OK;
  - `lxml.etree.parse` sobre las 4 vistas modificadas → XML bien formado;
  - ejecución del clasificador puro con los 8 casos de control (§1.6) → OK;
  - prueba en seco completa contra 21 documentos reales (§1.6) → 7 cambios justificados.

### 5.4 Compatibilidad con la suite existente

| Suite | Efecto esperado | Verificación |
|---|---|---|
| `tests/test_intake_tipo_ingreso_content.py` (5 tests) | **sin cambios**: `SERVICIO DE CEPILLADO` → Procesado; venta sin keyword → Producto; «SECADO DE MADERA A TERCEROS» → Producto (sin keyword); guía 26270 → Procesado | análisis del flujo + reglas del clasificador; los PDF sintéticos caen en `pdf_title` |
| `tests/test_granel_route.py` T04/T05/T06 | **sin cambios**: el onchange de adjuntar no clasifica (la clasificación sigue ocurriendo solo en «Leer documento») | `_onchange_suggest_tipo_ingreso` no se tocó |
| `tests/test_intake_profile_coherence.py` T04/T05 | **sin cambios**: la marca de lectura se antepone a `preview_warnings`; `profile_warning_message` sigue apareciendo en el preview | `reading_warning + '\n' + warnings` (§2.1) |
| `madenat_lumber_core/tests/test_ingestion_keywords_seed.py` T-KEY-01/02/05 | **sin cambios**: el parámetro decisivo no se modifica y `classification_result` conserva `Procesado` | §1.3 + C-2 |


---


## 6. Núcleo y otros perfiles — confirmación

```
$ git diff --name-only e672fc4..HEAD
madenat_lumber_intake/README.md
madenat_lumber_intake/__manifest__.py
madenat_lumber_intake/migrations/18.0.0.21.0/post-migrate.py
madenat_lumber_intake/models/intake_classifier.py
madenat_lumber_intake/models/intake_wizard.py
madenat_lumber_intake/tests/test_intake_wizard.py
madenat_lumber_intake/tests/test_intake_wizard_view.py
madenat_lumber_intake/views/intake_console_views.xml
madenat_lumber_intake/views/intake_guia_processing_facade_views.xml
madenat_lumber_intake/views/intake_reception_facade_views.xml
madenat_lumber_intake/views/intake_wizard_views.xml
```

- **`madenat_lumber_core`: 0 archivos.** No se tocaron modelos, vistas, datos ni tests del núcleo. El clasificador solo **lee** `madenat.ingestion.config.get_tipo_ingreso_keywords()`.
- **`madenat_ingestion_engine`: 0 archivos.** Se consume `extract_document`/`_extract_pdf_text` sin modificarlos.
- **Otros perfiles (Blanks/Arauco/JCE/BYC, Proveedores, Costing, Reports): 0 cambios.** Los cambios previos ajenos en `madenat_lumber_costing` y `madenat_lumber_reports` siguen **sin stage ni commit**.
- **Consola SQL:** sin cambios en `models/intake_console.py`; solo se añadió `sum=` a columnas de sus listas.
- **Sin hardcode** de proveedor, guía, ancho, largo ni espesor: el vocabulario es un parámetro y las señales son estructurales.
- **Sin popups ni bloqueos nuevos:** la marca es informativa; no se añadió ningún `raise`.
- **Sin upgrade ni escritura en BD:** la prueba en seco y las validaciones usaron `SELECT` y lectura de filestore.

---

## 7. Observaciones y preguntas abiertas

1. **Guía 33250 (id 33250, `tipo_recepcion=service`):** el clasificador anterior la marcaba Procesado solo por el pie legal «mercaderías o servicio(s)». Con la corrección queda Producto **con advertencia**. ¿Es un servicio real que debería llevar la palabra «servicio» en la glosa/archivo? Si negocio confirma que es servicio, la acción es corregir el dato de entrada (archivo/nombre), no reintroducir el falso positivo.
2. **«Cepillada» como artículo:** la compra de madera cepillada (S2S/clear) y el servicio de cepillado comparten glosa. La marca de advertencia es hoy el único discriminante cuando el archivo/título no lo declara. ¿Se puede exigir al proveedor que el nombre del archivo o la glosa indiquen «servicio» o «maquila»? (Recomendación, no implementación.)
3. **Paridad de keywords del núcleo (R7):** si en una fase posterior se desea añadir `cepill` al parámetro decisivo, hay que actualizar antes `madenat_lumber_core/tests/test_ingestion_keywords_seed.py` (T-KEY-01/T-KEY-05) en un cambio autorizado del núcleo.

---

## 8. Commits

| # | Hash | Mensaje |
|---|---|---|
| 1 | `c9dcaa6` | `feat(intake): clasificador por senales relevantes y migracion de vocabulario (2A-1)` |
| 2 | `7aa30e3` | `feat(intake): clasificación por señales y marca de advertencia de lectura (2A-1/2A-2)` |
| 3 | `d2bf650` | `feat(intake): totales del packing con sum= en las vistas de fachada (2A-3)` |
| 4 | `d349dd2` | `test(intake): cobertura de clasificación, marca de advertencia y totales (2A)` |
| 5 | `d25a32e` | `docs(intake): señales del clasificador, marca de advertencia y requisitos reales (2A-4)` |
| 6 | `5c52d9c` | `fix(intake): mensaje de perfil con perfil elegido vacío (2A)` |

Rama: `fase13-2a-lectura`, creada desde `e672fc4`. Sin `git add -A`: cada commit usó rutas explícitas.

---

## 9. `git status` (post-commits)

```
$ git status --porcelain
 M madenat_lumber_costing/__manifest__.py
 M madenat_lumber_costing/models/__init__.py
 M madenat_lumber_costing/models/lumber_cost_distribution.py
 M madenat_lumber_costing/models/lumber_shipment_costing.py
 M madenat_lumber_costing/security/ir.model.access.csv
 M madenat_lumber_costing/tests/__init__.py
 M madenat_lumber_costing/views/lumber_cost_distribution_views.xml
 M madenat_lumber_reports/views/lumber_reports_menu.xml
?? madenat_lumber_costing/models/stock_lot_cost_line.py
?? madenat_lumber_costing/tests/test_shipment_costing_c2.py
?? madenat_lumber_costing/views/lumber_shipment_costing_views.xml
```

Solo aparecen los cambios **preexistentes y ajenos** a esta tarea. `madenat_lumber_intake` está limpio (todo commiteado).

---

## 10. Diff resumido (`e672fc4..HEAD`)

```
 madenat_lumber_intake/README.md                       | 117 +++++---
 madenat_lumber_intake/__manifest__.py                 |   2 +-
 madenat_lumber_intake/migrations/18.0.0.21.0/post-migrate.py | 118 +++++++
 madenat_lumber_intake/models/intake_classifier.py     | 440 ++++++++++++++++
 madenat_lumber_intake/models/intake_wizard.py         | 184 +++++--
 madenat_lumber_intake/tests/test_intake_wizard.py     |  95 +++++
 madenat_lumber_intake/tests/test_intake_wizard_view.py|  28 ++
 madenat_lumber_intake/views/intake_console_views.xml  |  10 +-
 madenat_lumber_intake/views/intake_guia_processing_facade_views.xml | 8 +-
 madenat_lumber_intake/views/intake_reception_facade_views.xml | 8 +-
 madenat_lumber_intake/views/intake_wizard_views.xml   |  14 +
 11 files changed, 962 insertions(+), 62 deletions(-)
```

---

FASE 2A COMPLETADA — A LA ESPERA DE APROBADO UPGRADE
