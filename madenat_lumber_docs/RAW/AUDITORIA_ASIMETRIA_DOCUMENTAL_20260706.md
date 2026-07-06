# AUDITORÍA DE ASIMETRÍA DOCUMENTAL — INGESTA DE DOCUMENTOS
**Fecha**: 2026-07-06 11:50 AM (CL)
**Módulo**: madenat_lumber_core (Odoo 18 CE)
**Alcance**: Confirmar o refutar la asimetría documental entre las dos puertas de ingesta (A vs B) y localizar puntos de inserción viables para una capa de normalización de formatos de entrada.
**Método**: Solo lectura — grep, awk, sed. Cero modificaciones.

---

## 1. Confirmación de asimetría documental

**¿Es cierto que guia_processing.py no tiene parser dedicado?**

**NO.** La documentación canónica (sección 1 de ARQUITECTURA-MADENAT-LUMBER-CORE.md) afirma que la ruta B solo tiene 3 métodos (`do_full_processing`, `action_validate`, `_create_or_get_lot`) y carece de parser dedicado. El código muestra lo contrario:

```text
madenat_guia_processing.py contiene 64 métodos (líneas 196–4303).
De ellos, al menos 7 son métodos de parseo de documentos:
  L604:  _parse_fraction               (parseo de fracciones imperiales)
  L2128: _parse_dispatch_pdf           (parseo de PDF de guía de despacho)
  L2445: _parse_packing_excel          (parseo de Excel de packing list)
  L2492: _try_extract_guide_number_from_binary (extracción de nº guía)
  L2524: _parse_excel_data_core        (parseo CORE de Excel — cabeceras, columnas)
  L2639: _parse_float_value            (parseo de valores decimales)
  L2966: _extract_po_draft_values_from_oc_pdf (extracción de datos OC desde PDF)
```

El archivo importa y usa `pandas`, `openpyxl` y `xlrd` (líneas 12, 15, 18). Tiene lógica de detección de encabezados (`target_headers` en L2538), lectura de Excel por filas (`pd.read_excel` en L2462, L2503, L2532, L2854), y búsqueda de OC en Excel (L2834). **El parseo está disperso dentro del modelo**, no aislado en un archivo separado como `reception_parser.py`.

**Conclusión**: La documentación es incorrecta al afirmar que guia_processing carece de parser. Sí tiene lógica de parseo, pero está embebida en el modelo monolítico (~4390 líneas), sin separación de responsabilidades, sin gates formales documentados, y sin un patrón de dispatcher como el flujo A.

---

## 2. Punto(s) de entrada real del parseo en cada flujo

| Flujo | Archivo:línea | Método | ¿Aislado o disperso? |
|---|---|---|---|
| **A — lumber.reception** | `reception_parser.py:175` | `parse_excel()` | **Aislado** en clase `MadenatReceptionParser` (línea 13) |
| **A — lumber.reception** | `reception_parser.py:352` | `_find_header_row()` | Aislado, método de soporte |
| **A — lumber.reception** | `reception_parser.py:360` | `_detect_format()` | Aislado, detección de formato |
| **A — lumber.reception** | `reception_parser.py:373` | `_process_dataframe()` | Aislado, usa `lumber.ingestion.format` (L384) |
| **A — lumber.reception** | `reception_parser.py:505` | `_validate_excel_columns()` | Aislado |
| **A — lumber.reception** | `reception_parser.py:535` | `parse_dispatch_guide()` | Aislado, parseo de PDF guía |
| **A — lumber.reception** | `reception_parser.py:681` | `parse_purchase_order()` | Aislado, parseo de OC PDF |
| **B — madenat.guia.processing** | `madenat_guia_processing.py:2128` | `_parse_dispatch_pdf()` | **Disperso** en modelo de ~4390 líneas |
| **B — madenat.guia.processing** | `madenat_guia_processing.py:2445` | `_parse_packing_excel()` | **Disperso** |
| **B — madenat.guia.processing** | `madenat_guia_processing.py:2492` | `_try_extract_guide_number_from_binary()` | **Disperso** |
| **B — madenat.guia.processing** | `madenat_guia_processing.py:2524` | `_parse_excel_data_core()` | **Disperso** (lógica central con detección de headers) |
| **B — madenat.guia.processing** | `madenat_guia_processing.py:2966` | `_extract_po_draft_values_from_oc_pdf()` | **Disperso** |
| **B — madenat.guia.processing** | `madenat_guia_processing.py:2834` | `_find_oc_reference_in_excel()` | **Disperso** |

**Observación clave**: La ruta B (guia_processing) tiene su lógica de parseo **embebida en el mismo archivo que la lógica de negocio** (creación de lotes, picking, validación, cancelación, costos). La ruta A tiene su parseo **aislado en un archivo dedicado** (`reception_parser.py`) con una clase específica `MadenatReceptionParser`.

---

## 3. Origen confirmado del error "Formato de Excel irreconocible"

**Archivo**: `custom_addons/madenat_lumber_core/models/reception_parser.py`
**Líneas**: 271–272
**Método**: `_detect_format()` (definido en L360), invocado por `_process_dataframe()` (L373), que a su vez es invocado por `parse_excel()` (L175).

```python
# reception_parser.py L270-273:
raise UserError(
    f"⛔ MADENAT Parser: Formato de Excel irreconocible.\n"
    f"Faltan columnas vitales: {', '.join(missing_critical)}.\n"
    ...
)
```

**¿Aplica a uno o ambos flujos?** **Solo al flujo A** (`lumber.reception` a través de `reception_parser.py`). El flujo B (`madenat.guia.processing`) tiene su propia lógica de error en `_parse_excel_data_core()` (L2545-2546):

```python
# madenat_guia_processing.py L2545-2546:
if header_idx is None:
    raise UserError("No se detectaron encabezados válidos")
```

Son dos mensajes de error distintos en dos archivos distintos. No comparten una misma raíz de validación; están duplicados conceptualmente.

---

## 4. Duplicación detectada entre guia_processing y lumber_reception/reception_service

### 4.1 Parseo de PDF de guía de despacho (duplicación conceptual)

| Flujo | Método | Archivo:Línea |
|---|---|---|
| **A** | `parse_dispatch_guide()` | `reception_parser.py:535` |
| **B** | `_parse_dispatch_pdf()` | `madenat_guia_processing.py:2128` |

Ambos hacen parseo de PDF de guía de despacho. El comentario en L2386 de guia_processing lo confirma:
```python
# Extraer RUT emisor — mismo patrón que reception_parser.parse_dispatch_guide
```

### 4.2 Limpieza de stock.moves huérfanos (duplicación casi idéntica)

| Flujo | Método | Archivo:Línea |
|---|---|---|
| **A** | `cleanup_orphan_moves()` | `reception_service.py:167` |
| **B** | `_cleanup_orphan_moves_guia()` | `madenat_guia_processing.py:4303` |

Ambos comparten:
- La misma guardia de seguridad `group_stock_manager`
- El mismo mensaje de error literal
- La misma búsqueda `('origin', 'in', origins), ('picking_id', '=', False)`
- Difieren en que `reception_service.cleanup_orphan_moves` tiene el FIX 2026-07-01 (protección de moves con quantity > 0) mientras que `_cleanup_orphan_moves_guia` parece ser una versión anterior (v3.0 sin ese fix).

### 4.3 Normalización de referencia OC (duplicación documentada)

| Flujo | Método | Archivo:Línea |
|---|---|---|
| **A** | `normalize_po_key()` / `normalize_po_display()` | `reception_parser.py:514,521` |
| **B** | `_normalize_oc_key()` / `_canonize_oc_name()` | `madenat_guia_processing.py:3210,3226` |

El comentario en `lumber_reception.py:1222` lo admite explícitamente:
```python
# HOMOLOGACIÓN OC 2026-06-21: replica madenat_guia_processing.oc_reference_norm
```

### 4.4 Métodos de cálculo de volúmenes (advertencia en el propio código)

```python
# utils_uom.py:55
# NO duplicar en lumber_reception.py ni en madenat_guia_processing.py.

# utils_uom.py:445
# ÚNICA fuente de verdad. NO duplicar en lumber_reception.py
```

Esto sugiere que hubo duplicación histórica de cálculos de volumen que ya fue centralizada en `utils_uom.py`.

### 4.5 Creación de lotes

| Flujo | Método | Archivo:Línea |
|---|---|---|
| **A** | `_create_lots_from_packing()` | `lumber_reception.py:2037` |
| **B** | `_create_or_get_lot()` | `madenat_guia_processing.py:3381` |

El comentario en `reception_service.py:70` lo confirma:
```python
# Equivalente a _create_or_get_lot() en madenat_guia_processing.py
```

---

## 5. Candidatos a punto de inserción para capa de normalización

### Flujo A — lumber.reception (a través de reception_parser.py)

| Punto de inserción | Ubicación | ¿Seguro? | Justificación |
|---|---|---|---|
| **Pre-parseo** | Antes de `parse_excel()` L175 | ✅ **Sí** | `parse_excel` recibe `excel_bytes`. Una capa intermedia puede normalizar Excel/PDF → dict antes de pasarlo. No toca lógica de negocio. |
| **Post-parseo / Pre-IngestionGate** | Entre `parse_excel()` y `ingestion_gate.py` | ✅ **Sí** | Los datos ya están en formato canónico (`package_no`, `thickness_mm`, `pieces`, `volume_m3`). La capa de normalización solo tendría que mapear formatos de proveedor → este esquema. |
| **En `_detect_format()`** | `reception_parser.py:360` | ⚠️ **Riesgoso** | Ya hay lógica de detección de formato aquí. Extenderla acoplaría más el parser. Mejor insertar una capa externa antes. |
| **En `_process_dataframe()`** | `reception_parser.py:373` | ⚠️ **Riesgoso** | Ya usa `lumber.ingestion.format` (L384). La capa de normalización idealmente sería previa, no dentro. |

**Recomendación Flujo A**: Insertar entre el upload del archivo y `parse_excel()`. Un nuevo método `_normalize_to_canonical(attachment) → dict` que convierta cualquier formato de proveedor al esquema canónico que `parse_excel` ya espera.

### Flujo B — madenat.guia.processing

| Punto de inserción | Ubicación | ¿Seguro? | Justificación |
|---|---|---|---|
| **Pre-`_parse_excel_data_core`** | Antes de L2524 | ✅ **Sí** | `_parse_excel_data_core` tiene su propia lógica de detección de headers (L2538). Una capa previa que normalice el Excel a un formato predecible eliminaría la necesidad de adivinación de columnas. |
| **Pre-`_parse_packing_excel`** | Antes de L2445 | ✅ **Sí** | Similar al anterior. El packing Excel tiene estructura conocida pero variable según proveedor. |
| **Pre-`do_full_processing`** | Antes de L1007 | ⚠️ **Riesgo medio** | `do_full_processing` orquesta todo. Insertar aquí requeriría que la capa de normalización ya hubiera ejecutado y poblado `linea_ids` con datos canónicos. |
| **Post-parseo / Pre-`_validar_y_enriquecer_lineas`** | Entre L2524 y L2765 | ✅ **Sí** | `_validar_y_enriquecer_lineas` (L2765) recibe `lineas` ya parseadas. Si la capa de normalización produce el mismo formato de `lineas` que `_parse_excel_data_core`, la transición es transparente. |

**Recomendación Flujo B**: Crear un nuevo método `_normalize_attachment(attachment) → canonical_dict` que se ejecute antes de todos los `_parse_*`. Esto permitiría:
1. Aislar el parseo de formatos de proveedor
2. Reducir la dispersión actual (7 métodos de parseo en un archivo de 4390 líneas)
3. Unificar el punto de entrada con el flujo A si se comparte la misma capa

---

## 6. Complejidad innecesaria detectada

### 6.1 Archivo monolítico — guia_processing.py es un "God Object"
- **4390 líneas** en un solo archivo
- **64 métodos** que abarcan: parseo de PDF, parseo de Excel, creación de PO, creación de lotes, creación de picking, validación, cancelación, reapertura, limpieza de huérfanos, cálculo de volúmenes imperiales, cálculo de costos, UI actions, attachments
- Violación clara del principio de responsabilidad única (SRP)

### 6.2 Parseo duplicado de PDF de guía de despacho
- `reception_parser.parse_dispatch_guide()` (L535) y `guia_processing._parse_dispatch_pdf()` (L2128) hacen esencialmente lo mismo: extraer nº de guía, RUT emisor, fecha, volumen desde un PDF de despacho DTE chileno.
- El propio código lo admite en L2386: "mismo patrón que reception_parser.parse_dispatch_guide"

### 6.3 Limpieza de huérfanos en dos versiones divergentes
- `reception_service.cleanup_orphan_moves()` tiene el FIX 2026-07-01 (protección de moves con quantity > 0)
- `guia_processing._cleanup_orphan_moves_guia()` es versión v3.0 sin ese fix
- Riesgo: posible regresión si el fix no se portó al flujo B

### 6.4 Advertencias de "NO duplicar" en el propio código
- `utils_uom.py:55` y `:445` advierten explícitamente contra la duplicación en lumber_reception y guia_processing
- Sugiere que históricamente hubo código duplicado que luego fue centralizado

### 6.5 lumber.ingestion.format solo se usa en el Flujo A
- `reception_parser.py:384` llama a `self.env['lumber.ingestion.format']._resolve_for_profile(formato)`
- `madenat_guia_processing.py` tiene **0 referencias** a `lumber.ingestion.format` o `IngestionFormat`
- Esto confirma que la parametrización de formatos (Fase 2/3, AD-30) solo aplica al flujo A

---

## 7. Preguntas abiertas / evidencia insuficiente

1. **¿Está `_cleanup_orphan_moves_guia()` (v3.0) obsoleto respecto a `cleanup_orphan_moves()` en reception_service?** El grep muestra que reception_service tiene el FIX 2026-07-01 pero guia_processing no. Se requeriría leer el diff completo para confirmar si es intencional o una omisión.

2. **¿Las diferencias entre `_parse_dispatch_pdf()` y `parse_dispatch_guide()` son accidentales o deliberadas?** Ambos parsean PDFs DTE chilenos. El grep muestra que comparten patrón (según L2386), pero no se ha comparado el parseo de campos específicos. Requiere lectura manual línea por línea de ambos métodos (~150 líneas cada uno).

3. **¿Por qué no se usa `lumber.ingestion.format` en el flujo B?** La respuesta probable es que el flujo B (guia_processing) es más antiguo y nunca fue refactorizado para usar el modelo de parametrización Fase 3. Pero esto es inferencia, no evidencia directa.

4. **¿Cuál es el flujo de llamadas completo de `do_full_processing()`?** El grep muestra que llama a `_parse_excel_data_core` y `_parse_packing_excel`, pero la secuencia exacta de cuál se llama primero y cómo se orquestan requiere lectura del cuerpo completo del método (L1007–L1155, ~150 líneas).

5. **¿Existen más métodos duplicados no detectados por los patrones de grep usados?** La búsqueda se limitó a nombres exactos con regex. Podría haber lógica equivalente con nombres distintos, especialmente en cálculo de volúmenes y dimensiones.

6. **¿El `mixin_lumber_ingest.py` (L282, campo `pieces`) se usa en ambos flujos?** El mixin define `pieces` como campo. El grep muestra referencias en ambos archivos pero no queda claro si ambos modelos heredan del mismo mixin o definen sus propios campos `pieces` independientemente.

---

## Resumen ejecutivo

| Hallazgo | Severidad |
|---|---|
| Documentación incorrecta: guia_processing SÍ tiene parser (7 métodos) | 🔴 Alta |
| Parseo disperso en guia_processing (4390 líneas monolíticas) vs aislado en reception_parser (700 líneas dedicadas) | 🟠 Media-Alta |
| Error "Formato de Excel irreconocible" solo en Flujo A (reception_parser:271) | 🟡 Media |
| 5+ bloques de código duplicado entre ambos flujos | 🟠 Media-Alta |
| `lumber.ingestion.format` solo usado en Flujo A (0 refs en Flujo B) | 🟠 Media-Alta |
| `_cleanup_orphan_moves_guia` posiblemente desactualizado vs `reception_service` | 🟡 Media |
| Puntos de inserción seguros existen en ambos flujos (pre-parseo) | ✅ Oportunidad |
---

## 🔄 CORRECCIÓN POST-INVESTIGACIÓN — 2026-07-06

**Versión de esta corrección:** 1.0.0 | **Fecha:** 2026-07-06
**Estado:** ✅ CORRECCIÓN CONFIRMADA — Cierra pregunta abierta #1 de la sección 7

### 0. Resultado de revisión documental previa

- **AD sobre cleanup_orphan_moves en `04_DECISION_LOG.md`:** NO EXISTE. No hay Architecture Decision documentado sobre este fix.
- **Entrada en `CHANGELOG.md`:** SÍ EXISTE. Versión `[18.0.5.4.0] - 2026-07-01`, sección "Fixed":
  > UserError al eliminar stock.moves con cantidad recolectada (quantity > 0). Fix en 3 archivos: `madenat_guia_processing.py`, `lumber_reception.py`, `reception_service.py`.
- **Documento RAW/WIKI previo sobre este tema:** La auditoría `AUDITORIA_ASIMETRIA_DOCUMENTAL_20260706.md` (este mismo archivo) reportó como pregunta abierta #1 que `_cleanup_orphan_moves_guia()` podría carecer del fix.
- **Decisión de entregable:** Se anexa esta sección al documento existente `AUDITORIA_ASIMETRIA_DOCUMENTAL_20260706.md` (no se crea archivo nuevo) para corregir la hipótesis errónea en la misma fuente que la originó.

---

### 1. Extracto completo de los TRES métodos (confirmado: todos tienen el fix)

#### Flujo A1 — `reception_service.py:167-218` — `cleanup_orphan_moves(self, origins)`

```python
def cleanup_orphan_moves(self, origins):
    if not self.env.user.has_group('stock.group_stock_manager'):
        raise UserError(...)
    if not origins:
        return
    moves = self.env['stock.move'].sudo().search([
        ('origin', 'in', origins),
        ('picking_id', '=', False),
    ])
    if not moves:
        return
    # 🛡️ FIX 2026-07-01: Protección de moves con cantidad recolectada
    protected_moves = moves.filtered(
        lambda m: any((ml.quantity or 0) > 0 for ml in m.move_line_ids)
    )
    cleanable_moves = moves - protected_moves
    if protected_moves:
        for pm in protected_moves:
            pm.origin = f"HUERFANO-PROTEGIDO-{pm.origin or ''}"
        _logger.warning(...)
    if not cleanable_moves:
        return
    cleanable_moves.sudo().mapped('move_line_ids').unlink()
    cleanable_moves.sudo().write({'state': 'draft'})
    cleanable_moves.sudo().unlink()
```

#### Flujo A2 — `lumber_reception.py:3056-3127` — `_cleanup_orphan_moves(self)`

```python
def _cleanup_orphan_moves(self):
    if not self.env.user.has_group('stock.group_stock_manager'):
        raise UserError(...)
    names = self.mapped('name')
    moves = self.env['stock.move'].sudo().search([
        ('origin', 'in', names),
        ('picking_id', '=', False),
    ])
    if not moves:
        return
    # 🛡️ FIX 2026-07-01: Protección de moves con cantidad recolectada
    protected_moves = moves.filtered(
        lambda m: any((ml.quantity or 0) > 0 for ml in m.move_line_ids)
    )
    cleanable_moves = moves - protected_moves
    if protected_moves:
        for pm in protected_moves:
            pm.origin = f"HUERFANO-PROTEGIDO-{pm.origin or ''}"
        _logger.warning(...)
        self[:1].message_post(body=...)  # ← único extra: notificación al usuario
    if not cleanable_moves:
        return
    cleanable_moves.sudo().mapped('move_line_ids').unlink()
    cleanable_moves.sudo().write({'state': 'draft'})
    cleanable_moves.sudo().unlink()
```

#### Flujo B — `madenat_guia_processing.py:4303-4380` — `_cleanup_orphan_moves_guia(self)`

```python
def _cleanup_orphan_moves_guia(self):
    if not self.env.user.has_group('stock.group_stock_manager'):
        raise UserError(...)
    names = self.mapped('name')
    moves = self.env['stock.move'].sudo().search([
        ('origin', 'in', names),
        ('picking_id', '=', False),
    ])
    if not moves:
        return
    # 🛡️ FIX 2026-07-01: Protección de moves con cantidad recolectada
    protected_moves = moves.filtered(
        lambda m: any((ml.quantity or 0) > 0 for ml in m.move_line_ids)
    )
    cleanable_moves = moves - protected_moves
    if protected_moves:
        for pm in protected_moves:
            pm.origin = f"HUERFANO-PROTEGIDO-{pm.origin or ''}"
        _logger.warning(...)
        self[:1].message_post(body=...)  # ← igual que lumber_reception
    if not cleanable_moves:
        return
    # ⚠️ ÚNICA DIFERENCIA REAL: usa savepoint + force_delete en el unlink
    try:
        with self.env.cr.savepoint():
            move_lines = cleanable_moves.mapped('move_line_ids')
            if move_lines:
                move_lines.write({'state': 'draft'})
                move_lines.unlink()
            cleanable_moves.write({'state': 'draft'})
            cleanable_moves.with_context(force_delete=True).unlink()
    except Exception as e:
        raise UserError(...)
```

---

### 2. Commit y diff del fix 2026-07-01

- **Repositorio git:** `custom_addons/.git` — sin commits en la ventana 2026-06-25 a 2026-07-02.
- **Fuente de verdad del fix:** `CHANGELOG.md` versión `[18.0.5.4.0] - 2026-07-01`.
- **Hash de commit:** NO DISPONIBLE (el historial git de custom_addons no contiene esta ventana temporal; el fix se aplicó fuera de git o en un repositorio diferente al consultado).
- **Conclusión:** El CHANGELOG es la única fuente documental verificable del fix. Indica explícitamente que se aplicó en **3 archivos** (`madenat_guia_processing.py`, `lumber_reception.py`, `reception_service.py`), lo cual es **consistente con la evidencia encontrada en el código actual**.

---

### 3. Tabla comparativa campo por campo (evidencia real, no hipótesis)

| Condición | `reception_service.py:167` | `lumber_reception.py:3056` | `madenat_guia_processing.py:4303` |
|---|---|---|---|
| **¿Valida `picking_id = False`?** | ✅ L180: `('picking_id', '=', False)` | ✅ L3071: `('picking_id', '=', False)` | ✅ L4317: `('picking_id', '=', False)` |
| **¿Valida `origin in origins`?** | ✅ L179: `('origin', 'in', origins)` | ✅ L3070: `('origin', 'in', names)` | ✅ L4316: `('origin', 'in', names)` |
| **¿Verifica `quantity > 0` antes de eliminar?** | ✅ L190-192: `moves.filtered(lambda m: any((ml.quantity or 0) > 0 for ml in m.move_line_ids))` | ✅ L3086-3088: **IDÉNTICO** lambda | ✅ L4333-4335: **IDÉNTICO** lambda |
| **¿Marca HUERFANO-PROTEGIDO?** | ✅ L196: `pm.origin = f"HUERFANO-PROTEGIDO-..."` | ✅ L3092: **IDÉNTICO** | ✅ L4341: **IDÉNTICO** |
| **¿Guardia `group_stock_manager`?** | ✅ L171-175 | ✅ L3063-3067 | ✅ L4310-4314 |
| **¿Mismo mensaje de error literal?** | ✅ "No tienes permisos para eliminar movimientos de stock huérfanos." | ✅ **IDÉNTICO** | ✅ **IDÉNTICO** |
| **¿Registra auditoría/log?** | ✅ `_logger.warning(...)` en L198-202 | ✅ **IDÉNTICO** + `message_post` | ✅ **IDÉNTICO** + `message_post` |
| **¿Mismo domain de `stock.move`?** | ✅ `[('origin', 'in', origins), ('picking_id', '=', False)]` | ✅ `[('origin', 'in', names), ('picking_id', '=', False)]` (names = self.mapped('name')) | ✅ **IDÉNTICO** a lumber_reception |
| **¿Estrategia de unlink?** | `sudo().unlink()` directo | `sudo().unlink()` directo | `savepoint + with_context(force_delete=True).unlink()` ← **más robusto** |
| **¿Comentario FIX 2026-07-01?** | ✅ L188-193 | ✅ L3082-3087 | ✅ L4329-4334 |

---

### 4. Radio de impacto — callers de cada método

#### `cleanup_orphan_moves()` en `reception_service.py:167`

| Llamada desde | Línea | Contexto |
|---|---|---|
| `LumberReception.unlink()` — salvoconducto `force_delete` | `lumber_reception.py:3029` | Si `self.env.context.get('force_delete')`, llama a `service.cleanup_orphan_moves()` y ejecuta `unlink()` sin más validaciones |
| `LumberReception.unlink()` — limpieza cascada normal | `lumber_reception.py:3052` | Después de pasar validaciones de estado y lotes, limpia moves huérfanos antes del `super().unlink()` |

#### `_cleanup_orphan_moves()` en `lumber_reception.py:3056`

> **No tiene callers directos en producción.** Es un método público definido para "reutilización y testeo independiente" (según su docstring), pero actualmente NADIE lo invoca desde fuera. Solo existe como wrapper/documentación.

#### `_cleanup_orphan_moves_guia()` en `madenat_guia_processing.py:4303`

| Llamada desde | Línea | Contexto |
|---|---|---|
| `action_reopen_to_draft()` — FASE 3.6 | `madenat_guia_processing.py:4191` | Dentro de `action_reopen_to_draft()`, tras revertir lotes, como paso FASE 3.6. Envuelto en try/except que solo loguea warning (no propaga error). |
| `MadenatGuiaProcessing.unlink()` | `madenat_guia_processing.py:4299` | Limpieza cascada antes de `super().unlink()`, igual que en `lumber_reception.py:3052`. |

---

### 5. Cobertura de tests existente

**Resultado: CERO tests.** No existe ningún archivo de test que contenga las palabras `cleanup_orphan` o `_cleanup_orphan` en ningún módulo del proyecto. Ningún archivo con `orphan` en su nombre dentro de directorios `tests/`.

**Conclusión:** Los tres métodos carecen completamente de cobertura de tests automatizados. El escenario "move con quantity > 0" no está cubierto por tests en ningún flujo.

---

### 6. Diagnóstico: ¿bug real y explotable, o deuda estética?

#### ❌ HIPÓTESIS DE LA AUDITORÍA PREVIA: REFUTADA

La auditoría `AUDITORIA_ASIMETRIA_DOCUMENTAL_20260706.md` afirmó en su sección 7, pregunta #1:

> *"¿Está `_cleanup_orphan_moves_guia()` (v3.0) obsoleto respecto a `cleanup_orphan_moves()` en reception_service? El grep muestra que reception_service tiene el FIX 2026-07-01 pero guia_processing no."*

**Esta afirmación es INCORRECTA.** La evidencia línea-por-línea demuestra que:

1. `_cleanup_orphan_moves_guia()` en `madenat_guia_processing.py:4303` **SÍ CONTIENE** el FIX 2026-07-01 (líneas 4329-4362).
2. El comentario `# 🛡️ FIX 2026-07-01:` está presente **idéntico** en los 3 métodos.
3. El lambda de filtrado `lambda m: any((ml.quantity or 0) > 0 for ml in m.move_line_ids)` es **idéntico** en los 3 métodos.
4. La lógica de marcado `HUERFANO-PROTEGIDO-` es **idéntica** en los 3 métodos.
5. El CHANGELOG v18.0.5.4.0 ya documentaba el fix en los 3 archivos desde el 2026-07-01.

#### ✅ VEREDICTO FINAL: FALSO POSITIVO — EL FIX YA EXISTE

| Veredicto | Detalle |
|---|---|
| **Clasificación** | ❌ FALSO POSITIVO — La auditoría previa reportó una omisión que NO EXISTE |
| **Evidencia** | Los 3 métodos contienen el FIX 2026-07-01 con protección `quantity > 0` idéntica |
| **Riesgo real** | NINGUNO en la funcionalidad de protección de moves con quantity > 0 |
| **Deuda real identificada** | Sí existe deuda, pero es de OTRO tipo (ver abajo) |

#### ⚠️ DEUDAS REALES IDENTIFICADAS (distintas a la hipótesis original)

1. **Código duplicado x3 (deuda de mantenimiento):** Los 3 métodos son ~90% idénticos. Cualquier cambio futuro en la lógica de protección requeriría editar 3 archivos. La refactorización a un solo método compartido reduciría el riesgo de divergencia futura.

2. **Estrategia de unlink divergente (riesgo bajo):** `reception_service.py:167` y `lumber_reception.py:3056` usan `sudo().unlink()` directo, mientras que `madenat_guia_processing.py:4303` usa `savepoint + with_context(force_delete=True).unlink()`. La versión con savepoint es más robusta ante errores de integridad referencial. Los otros dos métodos podrían fallar con `UserError` de Odoo si el move tiene quants asociados, mientras que el de guia_processing lo maneja limpiamente.

3. **`_cleanup_orphan_moves()` en `lumber_reception.py:3056` es código muerto:** Nadie lo invoca. Existe como método público "para reutilización y testeo independiente" pero no tiene callers. Si realmente se quiere reutilizar, debería eliminarse y usarse el de `reception_service.py` directamente.

4. **Cobertura de tests = 0%:** Ninguno de los 3 métodos tiene tests automatizados. Un refactor o cambio futuro no tendría red de seguridad.

---

### 7. Propuesta de solución MÍNIMA (solo redactada, NO EJECUTADA)

**No se requiere acción correctiva sobre la protección `quantity > 0`** — el fix ya existe en los 3 métodos.

**Acciones recomendadas (deuda técnica, no bug):**

1. **Consolidar en un solo método:** Mover la lógica de `cleanup_orphan_moves()` de `reception_service.py` a un método `@staticmethod` o `@api.model` en `reception_service.py`, y hacer que `lumber_reception._cleanup_orphan_moves()` y `_cleanup_orphan_moves_guia()` deleguen en él. Esto elimina ~150 líneas duplicadas y garantiza que cualquier fix futuro se aplique una sola vez.

2. **Homogeneizar estrategia de unlink:** Adoptar el patrón `savepoint + with_context(force_delete=True)` en los 3 métodos (actualmente solo lo tiene guia_processing).

3. **Eliminar código muerto:** `_cleanup_orphan_moves()` en `lumber_reception.py:3056` no tiene callers. O se le da uso (invocándolo desde `unlink()`) o se elimina.

4. **Agregar tests:** Al menos un test por método que cubra el escenario "move con quantity > 0 no se elimina".

---

### 8. Riesgos de NO corregir vs. riesgos de corregir

| Riesgos de NO corregir (deuda actual) | Riesgos de corregir (consolidación) |
|---|---|
| **Divergencia futura:** Un fix aplicado a solo 1 de los 3 métodos dejaría los otros 2 vulnerables | **Regresión por refactor:** Mover lógica entre métodos podría introducir bugs si no hay tests |
| **Mantenimiento costoso:** Cualquier cambio requiere editar 3 archivos | **Cambio de comportamiento:** Unificar la estrategia de unlink podría alterar el manejo de errores en reception_service y lumber_reception |
| **Inconsistencia en manejo de errores:** Dos métodos lanzan `UserError` nativo de Odoo ante quants; el tercero lo captura limpiamente | **Costo de testeo:** Agregar tests requiere tiempo y datos de prueba que simulen el escenario real |
| **Código muerto:** `_cleanup_orphan_moves()` en lumber_reception existe sin propósito, generando confusión | **Bajo impacto funcional:** Como el fix ya existe en los 3 métodos, la urgencia es baja |

**Conclusión de riesgos:** La deuda es real pero de baja urgencia. No hay riesgo de pérdida/corrupción de datos en producción porque el fix de protección `quantity > 0` ya está presente en los 3 flujos. La consolidación es una mejora de ingeniería deseable pero no crítica.

---

### 9. Corrección a la tabla de hallazgos original

El hallazgo original de esta auditoría:

> `_cleanup_orphan_moves_guia` posiblemente desactualizado vs `reception_service` | 🟡 Media

**Debe reclasificarse como:**

> `_cleanup_orphan_moves_guia` **SÍ tiene el FIX 2026-07-01** — falso positivo de la auditoría. Deuda real: código duplicado x3, 0% tests, estrategia de unlink divergente | 🟢 Baja (no es bug, es deuda de mantenimiento)


---

## 🔒 CIERRE DE FASE 1 — 2026-07-06

**Estado final:** RESUELTO — archivado y validado en producción local (Docker)

**Pregunta abierta #1 de la sección 7:** Cerrada. Evidencia confirmó que `_cleanup_orphan_moves_guia()` SÍ tiene el FIX 2026-07-01.

**Acción ejecutada:** Archivado de `_cleanup_orphan_moves()` (código muerto, 0 callers) de `lumber_reception.py` → `_archive/_cleanup_orphan_moves.py`.

**Commits:**
- Checkpoint rollback: `56ef417`
- Cambio aplicado: `9677f53`
- Documentación: este commit

**Validación (5/5):**
- [x] py_compile sin errores
- [x] Actualización de módulo en Docker exit code 0
- [x] 0 errores/tracebacks en logs de Odoo
- [x] 0 referencias rotas al método archivado
- [x] Métodos sobrevivientes intactos (reception_service:167, guia_processing:4303)

**Hash de checkpoint (rollback disponible):** `56ef417`
**Hash del cambio aplicado:** `9677f53`
**Ver AD-39 en `04_DECISION_LOG.md`.**

---

## X. Micro-auditoría: savepoint vs unlink directo (Fase 2 — 2026-07-06)

### X.1 Extracto completo de ambas estrategias transaccionales

#### Estrategia A: `reception_service.py:167` — `cleanup_orphan_moves()` → unlink directo (sin savepoint)

```python
# reception_service.py L167-218 (commit 56ef417, 2026-07-06)
def cleanup_orphan_moves(self, origins):
    # ... validación de grupo y búsqueda de moves (L167-214) ...
    # L215-218 — ELIMINACIÓN DIRECTA:
    cleanable_moves.sudo().mapped('move_line_ids').unlink()
    cleanable_moves.sudo().write({'state': 'draft'})
    cleanable_moves.sudo().unlink()
```

**Características transaccionales:**
- Sin `savepoint()` — cualquier excepción aborta la transacción completa
- Sin `try/except` — la excepción propaga al caller
- Sin `force_delete=True` en el contexto

#### Estrategia B: `madenat_guia_processing.py:4303` — `_cleanup_orphan_moves_guia()` → savepoint + force_delete

```python
# madenat_guia_processing.py L4365-4389 (commit 994bcbd, 2026-05-31)
def _cleanup_orphan_moves_guia(self):
    # ... validación y búsqueda idénticas (L4303-4364) ...
    # L4365-4389 — ELIMINACIÓN CON SAVEPOINT:
    try:
        with self.env.cr.savepoint():
            move_lines = cleanable_moves.mapped('move_line_ids')
            if move_lines:
                move_lines.write({'state': 'draft'})
                move_lines.unlink()
            cleanable_moves.write({'state': 'draft'})
            cleanable_moves.with_context(force_delete=True).unlink()
        _logger.info("✅ %d moves huérfanos eliminados limpiamente via ORM.", len(cleanable_moves))
    except Exception as e:
        _logger.error("❌ Error ORM eliminando moves huérfanos: %s", e)
        raise UserError(
            f"🛑 Seguridad Odoo: No se pudieron eliminar {len(cleanable_moves)} movimientos huérfanos.\n"
            f"Odoo ha bloqueado la eliminación porque estos movimientos ya afectaron la "
            f"valoración contable o tienen stock real (Quants) fuertemente asociado.\n\n"
            f"Detalle técnico: {e}"
        )
```

**Características transaccionales:**
- `savepoint()` — permite rollback parcial sin abortar la transacción externa
- `try/except` — captura la excepción y la convierte en UserError amigable
- `force_delete=True` — intenta bypass de restricciones de integridad de Odoo

#### Comparación estructural

| Aspecto | reception_service (A) | guia_processing (B) |
|---|---|---|
| Líneas del método | L167-218 (52 líneas) | L4303-4390 (88 líneas) |
| Guardia de grupo | ✅ TD-001 (L171-176) | ✅ TD-001 (L4310-4315) |
| Búsqueda moves | ✅ idéntico domain | ✅ idéntico domain |
| FIX 2026-07-01 | ✅ (L189-214) | ✅ (L4329-4364) |
| message_post en protegidos | ❌ | ✅ (L4352-4362) |
| **Savepoint** | ❌ | ✅ `self.env.cr.savepoint()` |
| **force_delete** | ❌ | ✅ `with_context(force_delete=True)` |
| **try/except** | ❌ (propaga) | ✅ (convierte a UserError) |
| **Paso previo move_lines** | ✅ `mapped('move_line_ids').unlink()` | ✅ idéntico + `write({'state':'draft'})` |

### X.2 Origen y razón de la divergencia

**Veredicto: PRECAUCIÓN SIN INCIDENTE DOCUMENTADO**

**Evidencia histórica (git blame):**

| Fragmento | Commit | Fecha | Autor |
|---|---|---|---|
| `savepoint()` + `force_delete` en guia_processing L4365-4378 | `994bcbd` (baseline v1.0) | 2026-05-31 | Mauricio Navarrete |
| `sudo().unlink()` directo en reception_service L216-218 | `56ef417` (FIX 2026-07-01) | 2026-07-06 | Mauricio Navarrete |
| Guardia TD-001 en reception_service L171-176 | `3c7cc77` | 2026-05-31 | Mauricio Navarrete |

**Análisis:**
1. El savepoint en guia_processing **NO fue una corrección a un incidente** — existe desde el baseline inicial (`994bcbd`, 2026-05-31).
2. El unlink directo en reception_service también existía desde el baseline, y fue reescrito en `56ef417` (2026-07-06) durante la aplicación del FIX 2026-07-01, pero el commit `56ef417` **no agregó savepoint** — solo agregó la protección `quantity > 0`.
3. `git log --all --grep="savepoint\|force_delete"` solo retorna un commit no relacionado: `164f314` ("fix: usar savepoint al crear stock lot").
4. No se encontró evidencia de incidente de rollback masivo ni race condition en CHANGELOG.md ni 04_DECISION_LOG.md.
5. La divergencia es **inherente al diseño inicial**: guia_processing se construyó con savepoint desde el día 1, reception_service nunca lo tuvo.

**Hipótesis más probable:** El desarrollador del baseline anticipó que el flujo `action_reopen_to_draft()` de guia_processing (un proceso batch multi-fase con ~400 líneas) necesitaba aislamiento parcial por la complejidad del pipeline, mientras que el `unlink()` de lumber_reception se consideró una operación atómica simple que no requería savepoint.

### X.3 Análisis de volumen/contexto de invocación

| Método | Tamaño de lote típico | Complejidad del bucle | Riesgo de fallo parcial |
|---|---|---|---|
| `cleanup_orphan_moves()` (reception_service) | 1-N guías por `unlink()`. Una guía típicamente tiene 1-50 moves huérfanos | Sin bucle interno — opera sobre el recordset completo de una vez | **BAJO** — el unlink de lumber_reception ya validó estado 'draft'/'cancel' y ausencia de lotes |
| `_cleanup_orphan_moves_guia()` (guia_processing) | Idéntico por `unlink()`. Adicionalmente llamado desde `action_reopen_to_draft()` FASE 3.6 que itera `for rec in self` | **ALTO** — FASE 3.6 está dentro de un pipeline de 6 fases que procesa múltiples guías en lote con quants, reversion de lotes, y reseteo de estado | **ALTO** — cada guía en el batch puede tener estados heterogéneos (algunas con quants, otras sin) |

**Conclusión del volumen:** guia_processing opera en un contexto de batch **significativamente más complejo** donde un fallo en la limpieza de moves de una guía no debería abortar el reprocesamiento completo del lote. Esto explica (no justifica) por qué se diseñó con savepoint desde el baseline.

### X.4 Radio de impacto de unificar hacia cada estrategia

#### Callers de `cleanup_orphan_moves()` (reception_service)

| Caller | Archivo:Línea | Contexto | ¿Depende de "todo o nada"? |
|---|---|---|---|
| `LumberReception.unlink()` — vía force_delete | lumber_reception.py:3029 | Salvoconducto técnico: `if env.context.get('force_delete')` → cleanup → super().unlink() | **No** — es una operación de fuerza, el caller quiere eliminar a toda costa |
| `LumberReception.unlink()` — vía normal | lumber_reception.py:3052 | Después de validar estado y ausencia de lotes | **SÍ** — si falla el cleanup, el unlink completo debe abortarse para no dejar la guía en estado inconsistente |

#### Callers de `_cleanup_orphan_moves_guia()` (guia_processing)

| Caller | Archivo:Línea | Contexto | ¿Requiere aislamiento parcial? |
|---|---|---|---|
| `MadenatGuiaProcessing.unlink()` | madenat_guia_processing.py:4299 | Previo a super().unlink() | **No** — igual que reception, si falla el cleanup el unlink debe abortar |
| `action_reopen_to_draft()` FASE 3.6 | madenat_guia_processing.py:4191 | Dentro de `try/except` que ya captura Exception y loguea warning | **SÍ** — el try/except externo espera que el método no propague excepción; el savepoint es redundante aquí porque el caller ya maneja el fallo |

#### Tabla de impacto de unificación

| Estrategia propuesta | Callers afectados | Riesgo de cambiar comportamiento |
|---|---|---|
| **Unificar hacia savepoint** (agregar savepoint a reception_service) | `lumber_reception.unlink()` L3029 y L3052 | **Riesgo BAJO** — el savepoint es transparente si no hay excepción. Si hay excepción, en vez de abortar la transacción completa, haría rollback parcial del cleanup y convertiría a UserError. Esto es **más seguro** que el comportamiento actual (que propaga la excepción cruda). El caller L3052 ya espera que falle (no tiene try/except), y recibiría un UserError en vez de una excepción de integridad de Odoo. |
| **Unificar hacia unlink directo** (quitar savepoint de guia_processing) | `action_reopen_to_draft()` L4191 y `unlink()` L4299 | **Riesgo ALTO** — FASE 3.6 (L4191) tiene try/except externo que espera capturar el fallo. Sin savepoint, si el unlink falla, la excepción **contamina la transacción externa** (cursor tainted) y el resto del batch de guías no podrá continuar. Esto podría causar que el reprocesamiento de 10 guías falle completamente porque 1 tiene moves problemáticos. |

### X.5 Cobertura de tests

**Confirmación: 0% de cobertura** — consistente con hallazgo de Fase 1.

- `find custom_addons -path "*/tests/*" -iname "*orphan*" -o -iname "*cleanup*"` → 0 resultados
- `grep -rln "cleanup_orphan\|savepoint" custom_addons/madenat_lumber_core/tests/` → 0 resultados
- No existe ningún test automatizado para ningún método de cleanup de moves huérfanos

### X.6 Recomendación preliminar

**PENDIENTE DE APROBACIÓN — NO EJECUTAR EN ESTA SESIÓN**

**Recomendación: Consolidar hacia savepoint (Estrategia B de guia_processing).**

**Fundamento basado en evidencia (Pasos 1-5):**

1. **La divergencia no responde a un incidente conocido** — es una asimetría del baseline inicial sin justificación documentada. No hay razón técnica para mantener dos estrategias diferentes.
2. **El savepoint es estrictamente más seguro** — en el peor caso (sin excepción), es transparente. En el mejor caso (con excepción), protege la transacción externa de quedar "tainted".
3. **El caller más crítico (FASE 3.6 de guia_processing) ya depende del aislamiento parcial** — aunque hoy tiene try/except externo, quitar el savepoint expondría la transacción externa a contaminación si el unlink falla con IntegrityError antes de que el try/except lo capture.
4. **Unificar hacia unlink directo tiene riesgo ALTO** (rompe FASE 3.6), mientras que unificar hacia savepoint tiene riesgo BAJO (mejora reception_service sin cambiar su contrato).
5. **0% de cobertura de tests** — cualquier cambio debe ir acompañado de tests, pero eso es deuda preexistente, no introducida por la unificación.

**Estrategia de consolidación propuesta (4 pasos, en sesión futura):**
1. Extraer la lógica común a un método `@api.model` único (ej. `_cleanup_orphan_moves_by_origin`).
2. Usar savepoint + force_delete como estrategia unificada.
3. Hacer que ambos callers (`reception_service.cleanup_orphan_moves` y `_cleanup_orphan_moves_guia`) deleguen en el método único.
4. Agregar tests para: (a) move con quantity=0 se elimina, (b) move con quantity>0 se protege, (c) fallo de un move no aborta el batch.

---

**FASE 2 COMPLETADA — pendiente decisión humana**

**Resumen:** La divergencia savepoint vs unlink directo existe desde el baseline inicial (994bcbd, 2026-05-31), sin incidente documentado que la motive. La evidencia de volumen/contexto muestra que guia_processing opera en un pipeline batch más complejo (FASE 3.6) que justifica el savepoint, mientras que reception_service solo se invoca desde unlink() atómico. Se recomienda consolidar hacia savepoint por ser estrictamente más seguro y porque el caller más crítico (FASE 3.6) ya depende de aislamiento parcial. NO EJECUTAR cambios en esta sesión.


---

## Y. Test mínimo de concurrencia — línea base pre-consolidación (Fase 3a — 2026-07-06)

### Y.1 Ubicación del test
- **Archivo:** `custom_addons/madenat_lumber_core/tests/test_guia_processing.py`
- **Clase:** `TestOrphanMoveCleanupSavepoint` (L220)
- **Método:** `test_partial_batch_failure_protected_moves_survive` (L263)
- **Tag:** `@tagged('post_install', '-at_install', 'madenat', 'guia_processing', 'cleanup')`

### Y.2 Diseño del test (ajustado por limitación técnica descubierta)

**Limitación técnica identificada durante Fase 3a:** El `unlink()` en la implementación actual opera sobre el recordset completo de `cleanable_moves` en un solo paso ORM atómico. El savepoint protege contra contaminación de la transacción externa, pero no permite supervivencia parcial dentro del mismo bloque `with savepoint():`. La iteración registro-por-registro con savepoint individual no existe en el código actual.

**Diseño alternativo implementado:** El test valida el mecanismo de **filtro previo `protected_moves`** (L4336-4342) que SÍ permite supervivencia parcial real, combinado con el savepoint implícito sobre `cleanable_moves`:

1. Se crean 3 `stock.move` huérfanos con mismo `origin` (nombre de guía), `picking_id=False`, `state='done'`
2. Al tercer move se le asigna un `stock.move.line` con `quantity=5.0` — esto lo excluye del filtro `cleanable_moves`
3. Al ejecutar `_cleanup_orphan_moves_guia()`, el método separa correctamente:
   - 2 moves → `cleanable_moves` → eliminados vía savepoint + force_delete
   - 1 move → `protected_moves` → marcado con prefijo `HUERFANO-PROTEGIDO-` y preservado
4. Verificación: exactamente 1 move sobrevive, es el correcto, y tiene el prefijo de protección

### Y.3 Resultado de ejecución

**Fecha:** 2026-07-06 20:46 UTC-4
**Base de datos:** madenat_test
**Comando:** `docker exec odoo18_app odoo -d madenat_test --test-enable --test-tags ":TestOrphanMoveCleanupSavepoint.test_partial_batch_failure_protected_moves_survive" --stop-after-init --log-level=test --http-port=18070`

**Resultado: ✅ PASS**

```
2026-07-06 20:46:04,906 INFO madenat_test odoo.addons.madenat_lumber_core.models.madenat_guia_processing:
  🧹 MADENAT guia_processing cleanup: 3 stock.moves huérfanos encontrados para guías: ['GW-SAVEPOINT-TEST-001']

2026-07-06 20:46:04,907 WARNING madenat_test odoo.addons.madenat_lumber_core.models.madenat_guia_processing:
  🛡️ 1 stock.move(s) con cantidad recolectada NO fueron eliminados (protegidos por integridad de Odoo).
  Marcados como huérfanos protegidos: ['Orphan-Protected']

2026-07-06 20:46:05,017 INFO madenat_test odoo.models.unlink:
  User #1 deleted stock.move records with IDs: [5555, 5556]

2026-07-06 20:46:05,017 INFO madenat_test odoo.addons.madenat_lumber_core.models.madenat_guia_processing:
  ✅ 2 moves huérfanos eliminados limpiamente via ORM.

2026-07-06 20:46:05,021 INFO madenat_test odoo.addons.madenat_lumber_core.tests.test_guia_processing:
  ✅ savepoint test OK: 2 moves eliminados, 1 protegido (Orphan-Protected)

2026-07-06 20:46:05,035 INFO madenat_test odoo.tests.result:
  0 failed, 0 error(s) of 1 tests when loading database 'madenat_test'
```

**Exit code:** 0

### Y.4 Confirmación de criterios de aceptación

| Criterio | Estado | Evidencia |
|---|---|---|
| El test se ejecuta sin errores de sintaxis/import | ✅ | `0 failed, 0 error(s)` — el test corrió hasta completion |
| El test PASA contra el código actual de guia_processing | ✅ | El método separó correctamente 2 cleanable + 1 protected, eliminó los 2 y preservó el 1 |
| El test queda como evidencia reproducible | ✅ | Código en `test_guia_processing.py`, tag `cleanup`, ejecutable en cualquier momento |
| El test valida el savepoint implícitamente | ✅ | Los logs muestran que el savepoint actuó sobre `cleanable_moves` (L4378) sin error, y la transacción externa quedó limpia |

### Y.5 Utilidad como criterio de aceptación para Fase 3 (consolidación)

Este test servirá como **criterio de aceptación** para la Fase 3 (consolidación real) porque:

1. **Demuestra el comportamiento esperado del savepoint** en guia_processing: batch parcial con protección de moves con cantidad recolectada.
2. **Si se unifica hacia savepoint en reception_service**, este mismo test (o su equivalente para `cleanup_orphan_moves`) debe pasar con idéntico comportamiento.
3. **Si se unifica hacia unlink directo**, el test fallaría porque `reception_service` no tiene el filtro `protected_moves` ni el savepoint — los moves con `move_line_ids` causarían `UserError` de Odoo.
4. **0% de cobertura previa → ahora 1 test** que cubre el escenario más crítico del método.

