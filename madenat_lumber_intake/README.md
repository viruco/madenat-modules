# MADENAT Lumber Intake — Documentación de continuidad

> Módulo fachada de ingreso operacional. Documentación viva del módulo para que
> cualquier desarrollador pueda retomar el proyecto sin depender del historial de
> cambios ni de la memoria del último autor.
>
> **Estado consolidado:** 2026-08-29 · **Base verificada:** `madenat_test` (NO `madenattest`)
> **Versión del módulo:** `18.0.0.4.0` · **Estado:** `installed`

---

> **Cambios recientes (2026-08-29):**
> - Subproducto visible y aplicable también en el detalle de guías **Procesadas** (columna "Sub-producto").
> - Descarga de **Guía (PDF)** y **Packing list (Excel)** habilitada para ambos flujos (Producto y Procesado).
> - Guarda de estado en el botón **"Aplicar"** de Producto/Subproducto (bloquea guías ya cerradas/canceladas).
>
> **Cambio reciente (2026-09-02):**
> - Sugerencia asistida del **Perfil de lectura** (`metric` / `f5085` / `f1550`) analizando el Excel real con `madenat_ingestion_engine.extract_document()`. Es no determinista: el caso imperial sin palabra clave solo advierte y no cambia el valor.

## 1. Propósito y alcance

`madenat_lumber_intake` es la **puerta única de ingreso global** del sistema
MADENAT. Resuelve la dispersión operativa entre los ingresos de Producto y
Procesado mediante una sola bandeja de revisión, sin corromper, duplicar ni
reemplazar los flujos históricos existentes.

Consolida en una única bandeja ("Ingreso de Madera") dos fuentes operacionales reales:

1. **`lumber.reception`** — Recepciones de Producto / Madera Bruta → `ingestion_type='product'`.
2. **`madenat.guia.processing`** — Guías de Madera Procesada / Servicios → `ingestion_type='processed'`.

El operador sube documentos en un wizard, revisa información, evidencia documental
y estado operativo en la consola, y decide entre "Enviar a Stock" o "Modificar
origen". La consola `madenat.lumber.intake.console` es una fachada **readonly**
materializada sobre una vista SQL consolidada; funciona como cabina de validación
previa a stock. La validación definitiva **pertenece al core** y siempre se delega
a los métodos canónicos del origen.

---

## 2. Principio de aislamiento y no duplicación

- La **consola es readonly** y se materializa como una **vista SQL** (`_auto=False`),
  no como tabla. No persiste datos de negocio.
- El **wizard es el único mecanismo de creación**; no reinventa parsing ni gates:
  - Producto delega a `lumber.reception.action_process_documents()`.
  - Procesado delega a `madenat.guia.processing.action_verify_data()`.
- El envío a stock delega a:
  - Producto → `action_confirm_reception()`.
  - Procesado → `action_validate()`.
- La consola **no introduce bloqueos arbitrarios**: la falta de OC es una **advertencia
  controlada**, no un bloqueo de la consola.

---

## 3. Arquitectura del módulo

```
madenat_lumber_intake/
├── __manifest__.py                 # versión 18.0.0.3.0, depends=['madenat_lumber_core']
├── __init__.py                     # importa models
├── models/
│   ├── __init__.py                 # intake_wizard, intake_console
│   ├── intake_wizard.py            # madenat.lumber.intake.wizard (creación)
│   └── intake_console.py           # madenat.lumber.intake.console (SQL view readonly)
├── security/
│   ├── ir.model.access.csv         # ACL (operaciones: wizard RW, console R)
│   └── madenat_intake_security.xml # vacío (ir.rule pendiente para iteraciones futuras)
├── views/
│   ├── intake_console_views.xml    # list/form/search de la consola
│   ├── intake_wizard_views.xml     # form/list del wizard
│   └── intake_menus.xml            # menú principal + restricción de menús nativos
├── migrations/18.0.0.2.0/post-migrate.py
└── tests/test_intake_wizard.py
```

Orden de carga declarado en el manifest:

```
security/ir.model.access.csv
security/madenat_intake_security.xml
views/intake_wizard_views.xml
views/intake_console_views.xml
views/intake_menus.xml
```

Este orden es coherente: los menús referencian acciones definidas en el propio módulo
y XML IDs del core (`madenat_lumber_core`), que es dependencia declarada.

---

## 4. Requisitos comunes del wizard

Los requisitos **dependen de la modalidad** (`intake_modality`) y se validan en
`_guard_route_document()` **antes** de crear el registro destino:

| Modalidad | Documentos exigidos | Estado previo exigido |
|---|---|---|
| `normal` + Producto | Guía/PDF **y** Excel (Packing List) | `previewed` (hay que pulsar «Leer documento») |
| `normal` + Procesado | Guía/PDF **y** Excel | `draft` o `previewed` (no exige preview) |
| `volume` | Guía/PDF **o** Excel (al menos uno) | `draft` o `previewed` |

En todas: **Patio de Asignación** (`assignment_location_id`) interno, obligatorio.
Si falta algo, se levanta `UserError` y no se crea destino.

### Mapeo a destinos

| Campo Wizard | Destino: Recepción Directa | Destino: Guía Procesada |
|---|---|---|
| `excel_file`, `excel_filename` | `lumber.reception.excel_file`, `excel_filename` | `madenat.guia.processing.excel_file`, `excel_filename` |
| `pdf_file`, `pdf_filename` | `lumber.reception.pdf_file`, `pdf_filename` | `madenat.guia.processing.guide_pdf_file`, `guide_pdf_filename` |
| `assignment_location_id` | `lumber.reception.location_id` | `madenat.guia.processing.assignment_location_id` |

### Validación

La validación de estos tres requisitos se ejecuta en `_guard_route_document()` **antes** de crear
el registro destino. Si alguno falta, se levanta `UserError` bloqueando la derivación y sin crear
destino alguno. Esta regla aplica por igual a ambos flujos (Producto y Procesado).

---

## 5. Dependencias

- **`madenat_lumber_core`** y **`madenat_ingestion_engine`**.
- Preview de Producto usa `madenat_ingestion_engine.extract_document()`; reutiliza del
  core `madenat.audit.log` y los XML IDs de menú/grupo:
  - `madenat_lumber_core.menu_ops_reception_cat`
  - `madenat_lumber_core.menu_lumber_reception_pending`
  - `madenat_lumber_core.menu_guia_processing_root`
  - `madenat_lumber_core.menu_guia_processing_list`
  - `madenat_lumber_core.group_madenat_operaciones`
  - `madenat_lumber_core.group_madenat_admin`

---

## 6. Modelos y responsabilidades

### 5.1 `madenat.lumber.intake.console` (readonly)

- `_name = 'madenat.lumber.intake.console'`, `_auto = False`, `_rec_name = 'guide_name'`,
  `_order = 'guide_date desc, id desc'`.
- Modelo sobre la vista PostgreSQL `madenat_lumber_intake_console`.
- Campos homologados (readonly): `source_model`, `source_res_id`, `ingestion_type`,
  `guide_name`, `guide_date`, `partner_id`, `purchase_id`, `purchase_reference`, `state`,
  `display_reference`.
- Campos de resumen **compute no almacenados** (nunca persisten): `total_volume_m3`,
  `total_packages`, `total_lots`, `total_amount`, `currency_id`,
  `review_guide_document`, `review_excel_document`.
- Detalle de packing (Many2many compute no almacenados, sin inverse):
  `product_packing_line_ids`, `processed_packing_line_ids`, `packing_line_count`,
  `packing_volume_total`.
- Microestado `review_state` (compute): `ready`, `needs_review`, `sent`, `cancel`,
  `error`, `invalid`.

### 5.2 `madenat.lumber.intake.wizard` (creación)

- `_name = 'madenat.lumber.intake.wizard'`, **persistente** (no `TransientModel`).
  Persistencia deliberada para **evidencia e idempotencia**.
- Documentos: `excel_file` (required), `excel_filename`, `pdf_file`, `pdf_filename`.
- Destino: `tipo_ingreso` (`producto`/`procesado`), `ingestion_profile`
  (solo preview de producto), `assignment_location_id` (solo procesado).
- Estado: `draft` → `previewed` → `routed` / `error`.
- Idempotencia: `target_model`, `target_res_id`, `target_reference`, `error_message`.

---

## 7. Fuentes consolidadas

La vista SQL `madenat_lumber_intake_console` ejecuta `UNION ALL` sobre:

| Columna | Producto (`lumber.reception`) | Procesado (`madenat.guia.processing`) |
|---|---|---|
| `id` | `lr.id` (positivo) | `900000000 + gp.id` |
| `source_model` | `'lumber.reception'` | `'madenat.guia.processing'` |
| `source_res_id` | `lr.id` | `gp.id` |
| `ingestion_type` | `'product'` | `'processed'` |
| `guide_name` | `lr.name` | `gp.name` |
| `guide_date` | `COALESCE(lr.guia_fecha, lr.reception_date::date)` | `gp.date_emission` |
| `partner_id` | `lr.supplier_id` | `gp.partner_id` |
| `purchase_id` | `lr.purchase_id` | `gp.order_id` |
| `purchase_reference` | `lr.purchase_order` | `COALESCE(po.name, gp.oc_reference_raw, '')` (LEFT JOIN `purchase_order`) |
| `state` | `lr.state` | `CASE WHEN gp.state='cancelled' THEN 'cancel' ELSE gp.state END` |
| `display_reference` | `('Recepción ' \|\| COALESCE(lr.name,''))` | `('Procesada ' \|\| COALESCE(gp.name,''))` |

La vista se crea/reemplaza en `init()` con `tools.drop_view_if_exists` +
`CREATE OR REPLACE VIEW`.

---

## 7. Regla de identidad SQL y offset

- **Producto:** `id = lumber_reception.id` (entero positivo).
- **Procesado:** `id = CONSOLE_ID_OFFSET + madenat_guia_processing.id` (offset fijo).

`CONSOLE_ID_OFFSET` se define en `models/intake_constants.py` como fuente única de
verdad del offset y es importada por `intake_console.py`, `intake_wizard.py` e
`intake_guia_processing.py` (no repetir el valor numérico en otro lugar).

El offset evita colisión entre las dos fuentes en la misma vista UNION ALL.
Asunción implícita: los IDs de `lumber_reception` no alcanzan `CONSOLE_ID_OFFSET`
en la práctica.

---

## 8. Flujo funcional end-to-end

1. Operario abre **"Ingreso de Madera"** (`menu_madenat_lumber_intake_wizard` →
   `action_madenat_lumber_intake_console`, consola readonly).
2. **"Nuevo Ingreso"** lanza el wizard (`action_madenat_lumber_intake_new`, target=new).
3. El operario carga **Excel** y **PDF** (obligatorios en modalidad normal).
4. Adjuntar archivos **no clasifica**: sólo limpia los indicadores previos
   (`_onchange_suggest_tipo_ingreso`). La clasificación ocurre al pulsar
   «Leer documento» (ver §8.1).
5. `action_preview_document`:
   - **Producto** → prelectura con `madenat_ingestion_engine.extract_document()`
     (resumen informativo; sin conversión de unidades ni descarte de filas) y
     enriquecimiento de la clasificación con los nombres de producto del Excel.
   - **Procesado** → no usa `extract_document()`; informa que el flujo nativo
     interpretará el documento.
6. `action_route_document` (idempotente vía `_existing_target`):
   - **Producto** → crea `lumber.reception` (pdf/excel/ingestion_profile) y llama
     `action_process_documents()`.
   - **Procesado** → crea `madenat.guia.processing` (`tipo_recepcion='service'` +
     `assignment_location_id`) y llama `action_verify_data()`.
7. `_persist_target` marca `state='routed'` y guarda `target_model/res_id/reference`.
8. `_log_intake_origin` crea `madenat.audit.log` (`action_type='creation'`,
   `batch_id='intake:<wizard_id>'`, link `reception_id` o `guia_processing_id`) e
   incluye la marca de advertencia de lectura en la descripción.
9. El wizard abre el registro origen creado.
10. La consola muestra el registro consolidado (trazabilidad `source_model` +
    `source_res_id`, resumen y evidencia).
11. El operario revisa evidencia, OC, líneas, volumen y estado.
12. El operario decide **"Enviar a Stock"** o **"Modificar origen"**.
13. `action_send_to_stock` valida y delega en:
    - Producto → `action_confirm_reception()`.
    - Procesado → `action_validate()`.
14. Se postea en el chatter del origen "Enviado a stock desde la consola Ingreso de Madera."

### 8.1 Clasificador de tipo de ingreso (Fase 2A)

`_classify_normal_document()` (`models/intake_wizard.py`) usa **sólo** estas
señales, extraídas por `models/intake_classifier.py`:

| Señal | Origen | Naturaleza |
|---|---|---|
| `filename` | nombre del PDF y del Excel (sin extensión) | **fuerte** (el operador/el archivo declara el tipo) |
| `pdf_title` | primeras 3 líneas útiles del PDF **que no son filas de producto** | **fuerte** (título del documento) |
| `pdf_product` | filas de producto del PDF: ≥ 2 magnitudes numéricas, **unidad + cantidad** (`3322 M3`, `M3 54,518`, `38,1 mm`), o las que siguen a una cabecera `DESCRIPCIÓN/GLOSA/DETALLE/PRODUCTO` | débil |
| `excel_product` | `description` / `product_name_original` de `extract_document` | débil |

- Se **descarta** el texto legal/institucional antes de comparar (SII, RUT,
  timbraje, resolución, firma electrónica, URLs): evita que «Servicio de
  Impuestos Internos» clasifique como Procesado.
- Comparación: minúsculas, **sin acentos**, por **raíz al inicio de palabra**
  (`cepill` coincide con `Cepillada`) y **abreviaturas punteadas** (`CEP.` es
  prefijo de `cepillado`).
- **Dos vocabularios configurables**:
  - Decisivo: `madenat.tipo_ingreso_keywords` (parámetro del núcleo, sin cambios)
    → `["cepillado","servicio","proceso","maquila"]`.
  - De artículo (débil): `madenat.tipo_ingreso_weak_keywords` (parámetro propio,
    por defecto `["cepill","cep."]`). Sólo es decisivo en `filename`/`pdf_title`;
    en glosa o nombre de producto **no cambia el tipo**, sólo marca advertencia.
    Motivo (prueba en seco 2A): «Madera … Cepillada» aparece igual en compras
    S2S de Producto y en servicios de cepillado.
- El tipo sólo se decide en «Leer documento»; adjuntar archivos no lo cambia.

### 8.2 Marca de advertencia de lectura (no bloqueante)

Campos `reading_warning` (texto) y `has_reading_warning` (booleano) del wizard,
visibles en el formulario (icono ⚠ + texto) y en la lista. Se generan cuando:

| Caso | Mensaje (extracto) |
|---|---|
| Sin señal de tipo | «Sin señal de tipo en las señales revisadas … Se conserva el tipo por defecto» |
| Señal de artículo (débil) | «Posible servicio (señal de artículo, no de servicio) … NO se cambió el tipo» |
| Perfil no detectable o distinto del elegido | «Perfil de lectura no detectable …» / «El perfil detectado (X) no coincide con el elegido (Y)» |
| Unidad no reconocida | «Unidad no reconocida: unidades no reconocidas … / N dimensión(es) sin unidad de origen» |

- **Nunca bloquea** ni abre popups: es información persistida en el wizard.
- En la rama **Procesado** el wizard no lee el Excel (por diseño), por lo que
  perfil/unidad sólo se evalúan en la prelectura de **Producto**.
- La consola es una vista SQL de solo lectura sobre tablas del núcleo: **no se
  tocó** para mostrar la marca. Alternativa mínima implementada: la advertencia
  viaja en la descripción de `madenat.audit.log` (`_log_intake_origin`) y en el
  formulario/lista del wizard.

### 8.3 Espesor nominal declarado por el documento (Fase 2B, Paso 2)

El packing S2S trae el espesor **físico** del embarque (6/4 = 38,1 mm) y la
guía el espesor **nominal** de compra («… de 45mm»). La compra se cubica con
el nominal (`V = t · w · l · pzas / 10⁶`), así que sin este paso quedaba igual
al embarque.

Al derivar a **Producto** con perfil `f1550`, tras `action_process_documents()`
el wizard ejecuta `_apply_document_nominal_thickness()` (`models/intake_wizard.py`),
que usa el módulo puro `models/intake_nominal.py`:

| Fuente | Regla |
|---|---|
| Glosa del PDF | `de NNmm` (valor único; dos valores distintos → sin evidencia) |
| Aritmética | `t = total_volume_m3 · 10⁶ / Σ(w · l · pzas)` |
| Coherencia | glosa ↔ aritmética dentro de **±2 mm** |
| Límites | `nominal ≥ espesor físico`; volumen declarado entre **1,0×** y **1,4×** el del packing |

- **Nunca bloquea**: sin evidencia coherente se conserva lo leído y se añade una
  línea a `reading_warning` («Espesor nominal no resuelto desde el documento…»).
- **El valor del operador prevalece**: si `thickness_nominal != thickness` en
  alguna línea, el método no actúa.
- Se lee `total_volume_m3` y **no** `declared_volume_m3` (este último puede
  capturar el código de material: guía 40030 → 3322,0).
- Solo escribe `thickness_nominal` en el staging de la recepción **recién
  creada**; no toca registros históricos.
- Resultado en la guía 40030: compra **54.518 m³** (antes 46.158), embarque
  **44.713 m³** sin cambios.

---

## 9. Estados y transición de revisión

### Estado homologado (columna `state` de la vista)

Declarado en `madenat.lumber.intake.console.state`:

```
draft, processing, verified, done, validated, processed, cancel, error, pending_link
```

- `pending_link` y `error` provienen de `lumber.reception` (son estados históricos del core).
- Procesado `cancelled` se normaliza a `cancel` en la vista SQL (`CASE`).

### Microestado `review_state` (derivado, readonly)

| Estado fuente | Producto | Procesado |
|---|---|---|
| `done` | `sent` | — |
| `validated` | — | `sent` |
| `verified` | `ready` | `ready` |
| `processed` | — | `ready` |
| `cancel` | `cancel` | `cancel` |
| `error` | `error` | `error` |
| *otro* | `needs_review` | `needs_review` |

> ⚠️ El valor `review_state='invalid'` está declarado en el Selection pero **no es
> alcanzable** con el compute actual (`_review_state_for_state` nunca lo retorna).
> Ver sección 16 (R2).

---

## 10. Validaciones: bloqueos, advertencias y delegación al core

`_get_ready_for_stock_diagnostics` (consola) separa explícitamente:

- **Errores (bloqueantes):**
  - Sin origen vinculado o registro origen inexistente.
  - Falta número de guía, fecha documental, proveedor o tipo de ingreso.
  - Producto: falta PDF de guía, sin líneas de staging, ya `done`, o no `verified`.
  - Procesado: falta documento (PDF/Excel), sin líneas, ya `validated`, o estado no
    `verified`/`processed`.
- **Advertencias (no bloqueantes):**
  - Sin `purchase_id` y sin `purchase_reference` → se avisa que valide antes de enviar.

**Reglas delegadas al core (no replicadas por intake):**
- Producto: `lumber.reception.action_process_documents` (Gate0/Gate1) y
  `action_confirm_reception`.
- Procesado: `madenat.guia.processing.action_verify_data` y `action_validate`
  (incluye la exigencia real de OC documental sin vínculo).

### Reglas implementadas pero con matiz de riesgo (ver R1)

La condición de advertencia para Producto usa `purchase_reference` que proviene de
`lumber.reception.purchase_order`. Este compute devuelve la cadena literal `'SIN ORDEN'`
cuando no hay OC vinculada ni manual, por lo que la advertencia puede **no dispararse**
para Producto sin OC. No es un bloqueo, pero es un comportamiento divergente respecto a
la intención declarada.

---

## 11. Seguridad, roles y navegación

### ACL (`ir.model.access.csv`)

| Modelo | Grupo | read | write | create | unlink |
|---|---|---|---|---|---|
| `madenat.lumber.intake.wizard` | `madenat_lumber_core.group_madenat_operaciones` | 1 | 1 | 1 | 0 |
| `madenat.lumber.intake.console` | `madenat_lumber_core.group_madenat_operaciones` | 1 | 0 | 0 | 0 |

Coherente con "consola readonly" y "wizard de creación".

### Permisos y reglas

- `security/ir.model.access.csv` otorga al grupo Operaciones acceso a los modelos
  de intake. La consola `madenat.lumber.intake.console` tiene `perm_write=1` para
  permitir el guardado de los campos no-almacenados `product_id`/`subproduct_id`
  (cuyo `inverse` delega en los wizards del core). Es seguro: la consola es una
  vista SQL (`_auto=False`) no editable y el resto de campos son `readonly=True`,
  por lo que no se puede persistir nada en ella.
- No hay reglas de registro (`ir.rule`); el aislamiento operativo se apoya en el
  grupo `group_madenat_operaciones`.

### Navegación

- Menú principal "Ingreso de Madera" (`menu_madenat_lumber_intake_wizard`) cuelga de
  `madenat_lumber_core.menu_ops_reception_cat`, visible solo para
  `group_madenat_operaciones`.
- Los accesos nativos `menu_lumber_reception_pending`, `menu_guia_processing_root` y
  `menu_guia_processing_list` se restringen a `base.group_system` +
  `group_madenat_admin`. Es una **decisión UX intencional** (puerta única): no se
  eliminan menús ni se modifica la acción subyacente; es reversible.

---

## 12. Acciones, botones y vistas

### Consola (`view_madenat_lumber_intake_console_list/form/search`)

- **List:** columnas `guide_name`, `guide_date`, `partner_id`, `purchase_reference`,
  `state`, `ingestion_type`, `review_state`, `display_reference`. Botón cabecera
  "Nuevo Ingreso".
- **Form (create=false, edit=false):**
  - Header: `Enviar a Stock` (invisible salvo `review_state='ready'`), `Modificar origen`
    (invisible si `invalid`), indicadores de lotes/total/revisión.
  - Resumen: fecha, proveedor, OC documental, OC vinculada, referencia.
  - Evidencia: nombre de PDF y Excel.
  - Detalle del packing según `ingestion_type`.
- **Search:** campos textuales y relacionales; filtros por tipo/estado; agrupaciones.

### Wizard (`view_madenat_lumber_intake_wizard_form/list`)

- Botones: `Leer documento` (`action_preview_document`), `Continuar ingreso`
  (`action_route_document`), `Abrir registro creado` (`action_open_intake_target`).
- Vista previa solo visible en estado `previewed` para producto.
- Marca de advertencia de lectura: aviso ⚠ + `reading_warning` en el formulario
  y columna `has_reading_warning` en la lista (nunca popup ni bloqueo).

---

## 13. Estrategia de pruebas

`tests/test_intake_wizard.py` (`post_install`, tag `madenat_lumber_intake`):

| Test | Cubre |
|---|---|
| T1 | Producto — preview usa `madenat_ingestion_engine.extract_document()` |
| T2 | Procesado — preview NO invoca `extract_document()` |
| T3 | Producto — derivación canónica (crea `lumber.reception` + `action_process_documents`) |
| T4 | Procesado — deriva bytes al parser nativo (`action_verify_data`) |
| T5 | Idempotencia (doble clic → único destino y único evento de origen) |
| T6 | Error conocido → sin destino ni evento de origen |
| T2A-1 | Clasificación por raíz/tildes/abreviaturas (`Cepillada`, `CEPILLADO`, `PINO CEP. SECO LATERAL`, `SERVICIO CEPILLADO`), **comprobando la fuente** (`pdf_title`) de la coincidencia |
| T2A-2 | Sin señal de tipo → default Producto + `has_reading_warning` |
| T2A-3 | «Servicio de Impuestos Internos» + madera aserrada → no Procesado |
| T2A-4 | «Cepillada» en glosa = señal débil (no cambia el tipo) |
| T2A-5 | Perfil distinto del elegido + unidad no reconocida → advertencia |
| T2A-6 | Fix 2A-1b: con cabeceras de **1, 2 y 3 líneas** la fila de producto nunca es título |
| T2A-7 | Fila de producto con **unidad + cantidad** (`M3 54,518`) fuera del título |
| T2B-N1..N3 | Helpers puros del nominal: glosa `de NNmm`, aritmética `V/Σ(w·l·pzas)` y coherencia ±2 mm |
| T2B-N4 | Guía 40030: escribe nominal 45 → compra **54.518 m³** con embarque **44.713 m³** |
| T2B-N5..N8 | Packing que ya trae 45 (sin cambios), sin evidencia (marca), valor del operador, glosa incoherente |

`tests/test_intake_wizard_view.py` protege el contrato XML: campos de la marca
visible y `sum=` en las columnas numéricas de las fachadas de intake.

Los tests de preview ejercitan `extract_document()` real con Excel sintético; los de
derivación mockean `action_process_documents` y `action_verify_data` para aislar el
comportamiento del intake (no verifican parser ni gates, que son del core).

### Gaps de cobertura (no cubiertos)

- La **consola** no tiene tests: `search_count`, `review_state`, `action_send_to_stock`,
  `action_open_source`, ni el SQL view con offset.
- No hay test que valide la asimetría de la advertencia de OC (`purchase_reference='SIN ORDEN'`).

---

## 14. Migraciones

- `migrations/18.0.0.2.0/post-migrate.py`: limpia el menú raíz huérfano
  "Ingreso Global" (`parent_id IS NULL` y sin hijos). **Idempotente** (DELETE acotado).
- `migrations/18.0.0.21.0/post-migrate.py`: crea
  `madenat.tipo_ingreso_weak_keywords` (`["cepill","cep."]`) **sólo si no
  existe** (nunca pisa personalizaciones) y normaliza
  `madenat.tipo_ingreso_keywords` únicamente cuando su contenido normalizado es
  exactamente el seed canónico (misma lista y orden). Idempotente.
- Versión actual del módulo: `18.0.0.21.0`.
- **Pendiente de ejecución**: la migración se aplica en el upgrade
  (`-u madenat_lumber_intake`), que requiere aprobación explícita.

---

## 15. Estado actual confirmado de instalación

Verificado en **`madenat_test`** (base activa de la instancia, 2026-10-23):

- `madenat_lumber_intake` → `state=installed`, `latest_version=18.0.0.20.0`
  (el código ya está en `18.0.0.21.0`, pendiente de upgrade aprobado).
- Vista PostgreSQL `madenat_lumber_intake_console` existe.
- Conteos: `lumber_reception=8`, `madenat_guia_processing=13`.
- Consola consolida 21 filas de origen con documentos registrados.

> **No confundir con `madenattest`:** la base activa del contenedor es `madenat_test`.
> La validación final de este módulo debe hacerse en `madenat_test`.

---

## 16. Riesgos, límites y pendientes

| ID | Severidad | Riesgo | Evidencia |
|---|---|---|---|
| R1 | Alta | Producto sin OC puede no mostrar advertencia (regla 7 anulada para product) | `intake_console.py:349-352` + `lumber_reception.py:1194-1206` (`'SIN ORDEN'`) |
| R2 | Media | `review_state='invalid'` declarado pero inalcanzable | `intake_console.py:201-222` |
| R3 | Media | `ir.rule` vacío; sin aislamiento por fila en consola/wizard | `security/madenat_intake_security.xml` |
| R4 | Media | Ejecución delegada depende del ACL del core sobre `lumber.reception`, `madenat.guia.processing`, `madenat.audit.log` (no verificado) | `action_send_to_stock` / `_log_intake_origin` |
| R5 | Baja | Compute por fila (`_compute_review_metrics`, `_compute_packing_lines`) puede generar N+1 | `intake_console.py:227-288` |
| R6 | Resuelto | Backups internos (`backups_20260819_*`, `*.bak_*`) movidos a `_archive_pre_cleanup_20260822/` (2026-08-22) | limpieza de addons path |
| R7 | Info | `madenat_lumber_core/tests/test_ingestion_keywords_seed.py` (T-KEY-01/T-KEY-05) exige igualdad exacta del parámetro con la lista legacy; el vocabulario nuevo vive en un parámetro aparte para no romperlo | `madenat_ingestion_config.py:487` vs `tests/test_ingestion_keywords_seed.py:43-53` |
| R8 | Info | La marca de advertencia no se muestra en la consola (vista SQL sobre tablas del núcleo): se consulta en el wizard y en `madenat.audit.log` | `intake_console.py:600` (`init`) |

**Límites conocidos:**
- Sin aislamiento multiempresa en la vista SQL (módulo single-company).
- La vista SQL no tiene índices propios (es una vista; el coste recae en las tablas
  fuente subyacentes).

---

## 17. Guía para futuros cambios

### Qué inspeccionar primero

1. `models/intake_console.py` → vista SQL y método `init()`.
2. `models/intake_wizard.py` → flujo de creación y delegación.
3. `views/intake_menus.xml` → navegación y restricción de menús nativos.
4. `security/ir.model.access.csv` → permisos.
5. Referencias al core: `madenat_guia_processing.py` y `lumber_reception.py`.

### Cuándo es justificable un upgrade

- Cambios en vistas, modelos, seguridad o migraciones del módulo.
- Después de modificar el manifest (versión/datos) o agregar migraciones.
- **Comando correcto (base activa):**

```bash
docker exec odoo18_app odoo -c /etc/odoo/odoo.conf \
  --database madenat_test -u madenat_lumber_intake --stop-after-init
```

### Qué nunca actualizar automáticamente

- No ejecutar upgrade sobre `madenattest` esperando impacto en la UI (base distinta).
- No replicar en intake las validaciones definitivas del core (`action_validate` /
  `action_confirm_reception`); siempre delegar.
- No reintroducir la autocreación de OC (decisión histórica de core/purchasing).

### Cómo validar que la UI usa el módulo correcto

```bash
docker exec odoo18_db psql -U odoo -d madenat_test \
  -c "SELECT name, state, latest_version FROM ir_module_module WHERE name='madenat_lumber_intake';"

docker exec odoo18_db psql -U odoo -d madenat_test \
  -c "SELECT table_name FROM information_schema.views WHERE table_name='madenat_lumber_intake_console';"
```

Comprobar que el menú "Ingreso de Madera" abre `madenat.lumber.intake.console` y que la
acción "Nuevo Ingreso" lanza `madenat.lumber.intake.wizard`.

---

## 18. Historial de decisiones consolidadas

| Fecha | Decisión | Estado |
|---|---|---|
| 2026-08-16 | `assignment_location_id` editable en wizard (no inventar ubicación por defecto) | Implementado |
| 2026-08-16 | `_log_intake_origin` reutiliza `madenat.audit.log` con `action_type='creation'` sin nuevos campos | Implementado |
| 2026-08-17 | Menú principal abre la consola; wizard queda como mecanismo de creación | Implementado |
| 2026-08-17 | Restricción de menús nativos (`reception`/`guia.processing`) a admin/system (UX puerta única) | Implementado |
| 2026-08-17 | Consola readonly como vista SQL (`_auto=False`), no duplica datos | Implementado |
| 2026-08-17 | Auditoría: confirmada instalación en `madenat_test` (18.0.0.3.0); riesgos R1–R7 registrados | Documentado |
| 2026-10-23 | Clasificador por **señales relevantes** (archivo, título, glosa, producto Excel); se descarta texto legal (SII) | Implementado |
| 2026-10-23 | Comparación por **raíz + sin acentos + abreviaturas**; las keywords siguen en `madenat.tipo_ingreso_keywords` | Implementado |
| 2026-10-23 | «Cepillada/cepillado» = vocabulario de **artículo** (`madenat.tipo_ingreso_weak_keywords`): decisivo sólo en archivo/título; en glosa sólo advierte | Implementado |
| 2026-10-23 | Marca de advertencia **no bloqueante** (`reading_warning`/`has_reading_warning`) en wizard; consola intacta (vista SQL) | Implementado |
| 2026-10-23 | `sum=` en volumen de compra/exportación, MBF e importe de las vistas de fachada de intake | Implementado |
| 2026-10-23 | **2A-1b**: el título del PDF excluye filas de producto (≥2 magnitudes o unidad + cantidad). Con cabeceras de 1–3 líneas la glosa entraba en la ventana de título y «Cepillada» se promovía a señal fuerte | Implementado |
| 2026-10-23 | **2B Paso 2**: el espesor nominal de compra se toma del documento (glosa `de NNmm` + aritmética con `total_volume_m3`), se escribe en el staging S2S y el valor del operador prevalece | Implementado |