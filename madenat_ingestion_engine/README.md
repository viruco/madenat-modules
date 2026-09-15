# MADENAT Ingestion Engine

Motor de extracción y normalización de documentos de ingreso de madera (Excel/PDF), independiente del destino de negocio.

---

## 1. Objetivo del Módulo

Extraer y normalizar los datos declarados en los documentos de ingreso de madera (Excel/PDF) — cabecera y packing — en un contrato de datos único, configurable y agnóstico del destino final (Recepción Directa o Guía de Procesamiento), sin decidir clasificación de negocio, sin calcular costos, sin tocar stock, y sin reemplazar todavía los parsers actuales de `lumber.reception` ni `madenat.guia.processing`.

---

## 2. No-Objetivos Explícitos

Este módulo **NO** hace ninguno de lo siguiente (y debe fallar con error explícito si se intenta):

- **NO decide si el ingreso es Recepción Directa o Guía de Procesamiento** — ese es trabajo de la capa de interpretación de negocio.
- **NO calcula costos** — la extracción es agnóstica de valoración.
- **NO aplica reglas de volumen de exportación** — reporta lo que el documento dice, no lo que el negocio interpreta.
- **NO crea ni modifica `stock.lot`** — la persistencia es responsabilidad del consumidor.
- **NO reemplaza `lumber.reception` ni `madenat.guia.processing` todavía** — esta es fase 0, de esqueleto.
- **NO resuelve vinculación de OC ni proveedor** — solo extrae lo que el documento declara.
- **NO valida reglas de negocio** — solo reporta lo que encuentra; la validación es responsabilidad del consumidor.

---

## 3. Relación con el Resto del Sistema

### madenat_lumber_intake (Interfaz Visible)

`madenat_lumber_intake` sigue siendo la única puerta visible para Operaciones. Este motor (**madenat_ingestion_engine**) NO es una interfaz de usuario; es un servicio de backend agnóstico.

En fases futuras, `madenat_lumber_intake` **puede** consumir este motor como alternativa a los parsers actuales, pero de forma feature-flagged, sin eliminar los parsers legados hasta que haya un ciclo de uso real sin regresiones.

### lumber.reception y madenat.guia.processing (Destinos Actuales)

Estos módulos siguen siendo los únicos orquestadores de negocio. NO son modificados por este módulo en esta fase (Fase 0).

Cada dominio sigue invocando sus propios parsers:
- `lumber.reception` → `reception_parser.py`
- `madenat.guia.processing` → 9 métodos dispersos de parseo

El nuevo motor es **adicional**, no sustituyente.

### stock.lot (Núcleo Transaccional)

`stock.lot` sigue siendo el núcleo orquestador de trazabilidad e inventario. Este motor **nunca** escribe en `stock.lot`. Solo otros dominios autorizados lo hacen.

---

## 4. Estado Actual: FASE 2 — Extracción real implementada

`extract_document()` está implementada como función **pura** (sin `self.env`,
sin ORM) para Excel (perfiles métrico/imperial) y PDF (extracción de cabecera
por patrón/regex). Sin integración con `lumber.reception` ni
`madenat.guia.processing`.

### Implementado en Fase 2

- ✅ `column_matching.py` — scoring de alias (exacto=100, palabra=80, prefijo=60, substring=40)
- ✅ `ingestion_profiles.py` — perfiles como datos Python: `packing_metrico_aserrada` y `packing_imperial_blanks`
- ✅ `document_extractor.py` — `extract_document()` real con forward-fill, síntesis de `lot_number`, warnings por fila y autodetección de perfil
- ✅ Extracción de cabecera Excel (cliente, fecha, OC, guía, destino, chofer, patente; RUT/FONO/TRANS en imperial)
- ✅ Extracción de cabecera PDF por regex (guía, fecha, RUTs, OC, transportista, patente, montos)
- ✅ `destination_label`, `carrier_rut`, `carrier_phone`, `carrier_name` como campos opcionales
- ✅ UI standalone de documento de ingesta: `madenat.ingestion.document` (+ `.line` y `.warning`) con carga→extracción→revisión, inmutabilidad post-extracción (D2), advertencias inline y en pestaña, y menú propio independiente de `madenat_lumber_intake`

### Dependencia nueva (decisión de arquitectura)

Para reutilizar los grupos de seguridad nativos de Operaciones y Auditoría, el módulo ahora declara `depends: ['base', 'madenat_lumber_core']`. Es un acoplamiento real hacia `madenat_lumber_core` (solo para referenciar sus XML ID de `res.groups`), no una integración funcional con sus flujos.

### Limitaciones conocidas (decisiones de alcance, no olvidos)

- ⚠️ **P10:** solo se procesa la primera hoja / hoja activa de cada Excel (sin soporte multi-hoja).
- ⚠️ Los perfiles viven como **datos Python** (`ingestion_profiles.py`), no como registros del modelo ORM `madenat.ingestion.column.profile`. La integración con configuración persistente en BD es **Fase 3**.
- ⚠️ No se integra con `lumber.reception` ni `madenat.guia.processing` (Fase 4, feature-flagged).

### Alineación con AD-51 / AD-ING-001 / AD-ING-002

Este motor preserva la **fidelidad de datos** sin convertirlos ni resolverlos:

- **AD-51 punto 4 ("lo que se sube es lo que se ve"):** `extract_document()` no convierte unidades (pulgadas→mm, pies→m) ni evalúa fracciones; cada valor dimensional se captura como string tal cual (`thickness_value_raw`/`width_value_raw`/`length_value_raw`) junto con su unidad de origen declarada por el perfil (`thickness_unit`/`width_unit`/`length_unit`).
- **AD-ING-001 / AD-ING-002 (producto/subproducto sin hardcodeo):** `product_name_original` captura el texto exacto de la columna de producto, sin resolverlo contra `madenat.subproducto` ni derivar `product_id`/`subproducto_id`. No existe ningún literal de nombre de producto en el código.
- La conversión de unidades (`parse_fraction_to_decimal_inch`, AD-41) y la resolución de catálogo (`get_default_product` / `find_or_create_lumber_subproducto`) son responsabilidad de una integración futura, ya existentes en `madenat_lumber_core`, fuera de alcance de este módulo.

Nota sobre celdas numéricas: para celdas de texto/fracción, la
preservación es exacta. Para celdas numéricas nativas de Excel
(int/float), Excel no almacena el texto original tecleado por el
usuario, solo el valor binario más un formato de visualización; por lo
tanto no es técnicamente posible reproducir el número exacto de
decimales que el usuario vio. El extractor aplica una limpieza mínima
(redondeo a 6 decimales para eliminar ruido de punto flotante, y
eliminación del sufijo ".0" en enteros exactos) para evitar introducir
caracteres que el usuario nunca escribió, sin alterar el valor
dimensional real.

### Tests

```python
# test_document_extractor.py (fixtures sintéticos)
test_excel_complete_rows_no_warnings
test_excel_missing_lot_synthesized_and_forward_filled
test_excel_empty_row_skipped_without_warning
test_excel_no_header_raises
test_imperial_carrier_fields_in_header
test_metric_without_carrier_fields
test_auto_detection
test_explicit_profile_no_auto_detection
test_pdf_header_extraction
test_pdf_no_labels_general_warning
test_score_column_match
test_destination_label_absent_no_warning

# test_contract_placeholder.py (modelo)
test_column_profile_model_installable
test_column_profile_default_values
test_column_profile_can_be_deactivated
```

---

## 5. Plan de Integración Futuro

Documentado como **plan**, no como hecho realizado:

### Fase 0 (Esta Sesión)

- ✅ Módulo aislado, sin integración con sistemas existentes
- ✅ Modelo de configuración de perfiles de columnas
- ✅ Servicio placeholder
- ✅ Tests de placeholder

### Fase 1 (Sesión Posterior)

Diseño del contrato real de cabecera y líneas, **con evidencia de los formatos actuales de Excel/PDF**:

- Auditar `reception_parser.py` para confirmar estructura de cabecera (guide_no, partner, location, etc.)
- Auditar `reception_parser.py` para confirmar estructura de líneas (product_code, product_name, package_no, pieces, volume_m3, thickness_nominal, width_nominal, etc.)
- Auditar `madenat_guia_processing._parse_packing_excel()` para confirmar estructura de líneas (N° LOTE, Codigo, Cantidad, Volumen, Espesor, Ancho, Largo, etc.)
- Diseñar modelo ORM `madenat.ingestion.document.header` con cabecera completa
- Diseñar modelo ORM `madenat.ingestion.document.line` con líneas de packing
- Confirmar con producto la estructura exacta antes de implementar

### Fase 2 (Sesión Posterior)

Implementación real de `extract_document()` como función pura:

- Leer Excel con `pandas`, respetando formatos chilenos (decimales con coma, fracciones imperiales)
- Leer PDF con `pdfplumber`, extrayendo número de guía y OC
- Mapear columnas usando perfiles de configuración (sin hardcodear nombres)
- Validar estructura básica (no vacío, no formatos inválidos), pero NO validar reglas de negocio
- Retornar `DocumentExtractionResult` con header, lines y warnings

### Fase 3 (Sesión Posterior)

Pruebas de paridad contra los parsers actuales:

- Usar archivos reales de ingreso de madera (sanitizados si contienen datos sensibles)
- Ejecutar `lumber.reception.reception_parser.parse_excel()` en paralelo
- Ejecutar `madenat.guia.processing._parse_packing_excel()` en paralelo
- Ejecutar `madenat_ingestion_engine.extract_document()`
- Comparar resultados; documentar diferencias
- Refactorizar si hay divergencias funcionales

### Fase 4 (Sesión Posterior)

Consumo opcional (feature-flagged) desde los dominios existentes:

- Agregar parámetro `use_ingestion_engine=False` a `lumber.reception.action_process_documents()`
- Agregar parámetro `use_ingestion_engine=False` a `madenat.guia.processing.action_verify_data()`
- Si flag activo, usar `extract_document()` en vez del parser legado
- Mantener ambos parsers en paralelo; no eliminar código
- Ciclo de prueba en producción sin cambiar comportamiento por defecto

### Fase 5 (Sesión Posterior)

Evaluación de retiro de los parsers legados:

- Solo si Fase 4 alcanza N ciclos de uso real sin regresiones
- Análisis de cobertura de casos edge que el motor nuevo podría no manejar
- Decisión de negocio (no técnica) sobre mantener parsers legados o deprecarlos
- Migración controlada si se decide deprecar

---

## 6. Principio de Diseño: Separación de Responsabilidades

```
┌──────────────────┐
│  Extracción      │  ← Este módulo: "¿Qué dice el documento?"
│ (este módulo)    │     Función pura, sin ORM, reproducible
└──────────────────┘
         ↓ (DocumentExtractionResult)
┌──────────────────┐
│  Interpretación  │  ← lumber.reception / madenat.guia.processing
│ (negocio actual) │     "¿Qué significa para mi clasificación?"
└──────────────────┘
         ↓ (signos de negocio validados)
┌──────────────────┐
│  Persistencia    │  ← stock.lot, audit_log, etc.
│  (stock)         │     "¿Cómo se guarda?"
└──────────────────┘
```

Este módulo **solo cubre Extracción**. No toma decisiones de negocio. No persiste datos. Solo emite lo que el documento declara.

---

## 7. Nota sobre Seguridad

### Grupo de Acceso Usado

En `security/ir.model.access.csv`, se usó:
- `base.group_user` para lectura (cualquier usuario autenticado puede ver perfiles)
- `base.group_system` para escritura/creación/eliminación (solo administradores)

### Por Qué `base.group_system` (y no el grupo de configuración MADENAT)

SÍ existe un grupo de seguridad propio para configuración MADENAT: `madenat_lumber_core.group_lumber_config_manager` ("Configurador de Reglas de Ingesta"), usado en `madenat_lumber_core/security/ir.model.access.csv` para los modelos de configuración de reglas de ingesta, mapas de blanks, fórmulas de exportación, etc.

Sin embargo, **NO se usó en esta fase** porque referenciarlo en `security/ir.model.access.csv` obligaría a declarar `madenat_lumber_core` como dependencia del módulo, y esta sesión exige `depends` **únicamente** sobre `base` (restricción absoluta de aislamiento).

Por eso se usó el placeholder temporal:

- `base.group_user` → lectura (cualquier usuario interno autenticado).
- `base.group_system` → escritura/creación/eliminación (solo administración).

**Actualización (2026-09-02):** la condición se cumplió — el módulo ya declara `depends: ['base', 'madenat_lumber_core']`. La ACL de escritura de `madenat.ingestion.column.profile` fue migrada de `base.group_system` a `madenat_lumber_core.group_lumber_config_manager` ("Configurador de Reglas de Ingesta"), coherente con el uso de ese mismo grupo en los modelos de configuración de `madenat_lumber_core` (p. ej. `lumber.ingestion.format`). La lectura permanece en `base.group_user`.

### Riesgo documentado

Riesgo documentado: la autorización de "Auditoría" se apoya en
madenat_lumber_core.group_madenat_cost_auditor, un grupo marcado como
"legacy/base para auditoría de costos" en su propio código fuente. Si
ese grupo se renombra o archiva en una futura refactorización de Core,
la instalación de madenat_ingestion_engine fallará por referencia XML
rota. Revisar este acoplamiento si Core reestructura su capa de
seguridad.

---

## Notas Técnicas

### Dependencias

- `base` solamente (Odoo core)
- Sin dependencia en `madenat_lumber_core`, `madenat_lumber_intake`, ni ningún módulo lumber específico
- Librerías Python usadas en runtime: `pandas`, `openpyxl`, `pdfplumber` (ya disponibles en el entorno Docker; no se declaran en `__manifest__.py`, que sigue dependiendo solo de `base`).

### Instalación

```bash
cd ~/dev-stack/odoo/odoo-18-ce
docker compose run --rm web odoo -d madenat_test -i madenat_ingestion_engine --stop-after-init --workers=0
```

### Validación de Syntax

```bash
python -m py_compile madenat_ingestion_engine/models/*.py madenat_ingestion_engine/services/*.py madenat_ingestion_engine/tests/*.py
```

---

## Próximos Pasos

1. **Fase 1:** Auditar formatos reales de Excel/PDF con evidencia
2. **Fase 2:** Implementar `extract_document()` basado en contrato confirmado
3. **Fase 3:** Pruebas de paridad contra parsers actuales
4. **Fase 4:** Feature flag para consumo opcional desde dominios existentes
5. **Fase 5:** Evaluación de retiro de parsers legados (DECISIÓN DE NEGOCIO)

---

**Última actualización:** 2026-09-01  
**Estado del módulo:** FASE 2 — extracción real implementada (Excel/PDF), sin integración con dominios existentes  
**Versión:** 18.0.1.0.0
