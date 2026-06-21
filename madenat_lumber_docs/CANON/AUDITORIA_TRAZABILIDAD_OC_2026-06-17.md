# AUDITORÍA DE TRAZABILIDAD DE ORDEN DE COMPRA (OC)
## Integración madenat_lumber_purchasing ↔ madenat_guia_processing ↔ lumber.reception ↔ purchase.order

**Auditor: Cline (senior architect Odoo 18 CE)**
**Fecha: 2026-06-17**
**Versión del documento: 2.0 — Integración funcional y técnica completa**

---

# 1. HALLAZGOS CONFIRMADOS POR EVIDENCIA

## H1 — Vacío de persistencia de referencia documental en `madenat.guia.processing`

**Evidencia:**
- `madenat_guia_processing.py`, método `_parse_dispatch_pdf` (línea ~1977): extrae `orden_compra` del PDF y la retorna en el dict `pdf_data`. En `action_verify_data` (línea ~1297) solo persiste `additional_cost`, `rate_usd`, `service_*`, `volumen_comercial` y `name`. La clave `orden_compra` **nunca** se escribe en la BD.
- `madenat_guia_processing.py`, método `_find_oc_reference_in_excel` (línea ~2364): busca OC en las primeras 10 filas del Excel con regex `(?:OC|MC|Orden)[\s\.\-:]*([A-Z0-9]+(?:\s*[-]\s*[A-Z0-9]+)+)`. El resultado se asigna a `result['oc_reference']` (línea ~2004) dentro de `_parse_packing_excel`, pero esa clave solo vive en el dict local — **no se persiste** en el modelo.
- **Conclusión:** Ambos parsers extraen la referencia OC correctamente, pero el modelo `madenat.guia.processing` no tiene un campo para almacenarla.

## H2 — `manual_po_name` se sobrescribe al vincular OC

**Evidencia:**
- `lumber_reception.py` (core), `_find_or_create_po_intelligent` (líneas ~2198-2203): cuando existe match con `purchase.order`, escribe `manual_po_name = False`.
- `lumber_reception.py` (core), `_find_or_create_po_intelligent` (líneas ~2225-2231): cuando NO existe match, escribe `manual_po_name = po_ref`.
- `lumber_reception.py` (core), `create_po_from_oc_data` (líneas ~2213-2218): también escribe `manual_po_name = False` al crear OC desde datos del PDF.
- **Conclusión:** `manual_po_name` cumple rol de "referencia documental cruda" de facto pero se pierde al vincular. El modelo no diferencia entre "referencia original del documento" y "vínculo operativo a purchase.order".

## H3 — `madenat_lumber_purchasing` crea OC automáticamente sin supervisión humana

**Evidencia:**
- `purchasing/models/lumber_reception.py`, `_find_po_and_supplier` (líneas ~59-67): si `po_ref` no se encuentra en `purchase.order`, llama a `_create_po_from_guide` que ejecuta `po.button_confirm()` (línea ~121) sin intervención humana.
- `_create_po_from_guide` (líneas ~80-123): usa valores hardcode: `lumber_quality='col_a'`, `wood_type='pine'`, `treatment='kiln_dried'`, `thickness_mm=45.0`, `total_volume=1`.
- `purchasing/models/purchase_intake.py`, `validate_or_create_po` (líneas ~118-192): método separado que también puede crear OC con política `auto_create=True`.
- `purchasing/models/purchase_order.py`, `validate_or_create_po` (líneas ~288-496): Gatekeeper API que crea PO cuando `auto_create=True` y no encuentra existente.
- **Conclusión:** Existen al menos tres puntos de creación automática de OC, dos de los cuales son silenciosos y sin supervisión.

## H4 — Dos lógicas de matching inconsistentes entre `purchase_order.name` y `partner_ref`

**Evidencia:**
- `purchasing/models/lumber_reception.py`, `_find_po_and_supplier` (línea ~44): busca por `('name', '=ilike', po_ref)` + `partner_id`.
- `purchasing/models/purchase_order.py`, `validate_or_create_po` (líneas ~352-357): busca por `('partner_ref', '=', partner_ref)` + `partner_id`.
- `purchasing/models/purchase_intake.py`, `validate_or_create_po` (líneas ~152-155): busca por `partner_id` + `partner_ref`.
- `lumber_reception.py` (core), `_find_or_create_po_intelligent` (líneas ~2172-2180): busca por `partner_id` + `state`, luego filtra por `parser.normalize_po_key(p.partner_ref)` o `parser.normalize_po_key(p.name)`.
- **Conclusión:** No existe una clave canónica unificada. Un mismo documento podría hacer match en un flujo y fallar en otro.

## H5 — `madenat.guia.processing` no alimenta el control acumulado de `purchase.order`

**Evidencia:**
- `purchase_order.py` (purchasing), `_compute_reception_stats` (líneas ~235-264): solo computa desde `reception_ids` (One2many a `lumber.reception`). No lee `madenat.guia.processing`.
- `madenat_guia_processing.py`, `_compute_all_totals` (líneas ~900-953): calcula totales desde `processing_line_ids` y `lot_ids` pero **no actualiza** ningún campo en `purchase.order`.
- `madenat_guia_processing.py`, `_sync_purchase_order_lines` (líneas ~1131-1170): solo actualiza `order_line.product_qty` en la OC si `order_id` está seteado. No actualiza `received_volume_m3`.
- **Conclusión:** `purchase.order` solo refleja ingesta desde `lumber.reception`, no desde `madenat.guia.processing`. El control acumulado está incompleto.

## H6 — `madenat.guia.processing` no tiene lógica automática de matching con `purchase.order`

**Evidencia:**
- `madenat_guia_processing.py`, campo `order_id` (línea ~768): `fields.Many2one('purchase.order')`, sin `compute`, sin `domain`, sin `required`. Es 100% manual.
- `action_verify_data` (líneas ~1204-1361): no asigna `order_id`. Solo persiste datos financieros y de servicio.
- `action_process_from_staging` (líneas ~1366-1443): usa `self.order_id.name if self.order_id else self.name` como `oc_reference` en `packing_simulado` (línea ~1434), sin intentar buscar la OC automáticamente.
- `do_full_processing` (línea ~1000): `purchase_order = rec.order_id` — si es `False`, todo el flujo descendente queda sin OC.
- **Conclusión:** El vínculo OC en guías procesadas depende enteramente del operador humano, sin asistencia automática desde los parsers.

## H7 — Duplicación de lógica entre `purchase_order.py` y `purchase_intake.py`

**Evidencia:**
- Ambos archivos contienen un método llamado `validate_or_create_po`.
- `purchase_order.py` (línea ~288): retorna dict con claves `success`, `po_id`, `state`, `message`, `error`.
- `purchase_intake.py` (línea ~118): retorna dict con claves `status`, `po_id`, `reason`.
- Ambas implementan búsqueda por `partner_id` + `partner_ref`.
- `purchase_intake.py` también tiene `ensure_master_product` que puede CREAR el producto `MADERA_GENERICA` automáticamente.
- **Conclusión:** Lógica duplicada con semánticas ligeramente diferentes. Riesgo de divergencia en producción.

## H8 — `stock.lot` recibe `purchase_order_id` solo de guías procesadas, no de recepciones

**Evidencia:**
- `madenat_guia_processing.py`, `_create_or_get_lot` (líneas ~2596-2597): `vals['purchase_order_id'] = purchase_order.id` solo si `purchase_order` no es `None`.
- `reception_service.py`, `create_lots_from_staging` (líneas ~94-155): **no asigna** `purchase_order_id` en los valores del lote.
- `lumber_reception.py` (core), `_fill_staging_table` (líneas ~1880-1967): **no asigna** `purchase_id` en las líneas de staging.
- **Conclusión:** Los lotes creados desde `lumber.reception` no llevan `purchase_order_id`, solo los de `madenat.guia.processing` y solo si `order_id` está seteado manualmente.

## H9 — Formato visible canónico es `MC 1602-302` con espacios y guiones

**Evidencia:**
- `reception_parser.py`, `normalize_po_display` y `normalize_po_key`: la `_key` colapsa espacios y guiones, la `display` los preserva.
- `madenat_guia_processing.py`, `_parse_dispatch_pdf` (línea ~1869): `re.sub(r'\s*-\s*', '-', match.group(1))` preserva el guion.
- **Conclusión:** El formato funcional visible respeta espacios y guiones (`MC 1602-302`). La clave interna (key) los colapsa para matching exacto.

---

# 2. HIPÓTESIS PENDIENTES DE VALIDACIÓN

| ID | Hipótesis | Evidencia a verificar | Riesgo si es errónea |
|----|-----------|-----------------------|----------------------|
| HIP-01 | `_find_po_and_supplier` en purchasing SOBRESCRIBE `_find_or_create_po_intelligent` en core cuando purchasing está instalado | Verificar orden de resolución MRO — el método en purchasing tiene mismo nombre `_find_po_and_supplier`, no `_find_or_create_po_intelligent`. ¿Se llama desde `run_ingestion_pipeline` o desde otro lado? | Si no hay override, purchasing podría estar ejecutándose en paralelo, creando OCs duplicadas |
| HIP-02 | El método `reception_parser.normalize_po_key` usa la misma lógica de colapso que `_match_purchase_order` propuesto | Leer `reception_parser.py` líneas de `normalize_po_key` y `normalize_po_display` | Si difieren, el matching dará falsos negativos |
| HIP-03 | `madenat.guia.processing` y `lumber.reception` pueden coexistir para la misma guía física | Verificar si hay lógica que prevenga duplicación entre ambos modelos | Podría haber doble ingesta del mismo documento |
| HIP-04 | El método `_find_po_and_supplier` en purchasing se llama desde `action_process_documents` o solo desde `action_test_processing` | Trazar call stack completo | Si no se llama en producción, el riesgo R2 es menor de lo estimado |
| HIP-05 | `purchase_intake.py` (`madenat.purchase.intake`) es usado por algún módulo externo (ej. logistics, toll_processing) | Buscar referencias a `madenat.purchase.intake` en todo el código | Si no se usa, se puede deprecar sin impacto |
| HIP-06 | El campo `ingestion_source_ref` en `purchase.order` se alimenta desde algún flujo en producción | Buscar writes a `ingestion_source_ref` en logs o código | Si no se usa, está disponible para el nuevo diseño |

---

# 3. MATRIZ DE ALINEAMIENTO FUNCIONAL

| Componente | Responsabilidad | Fuente de verdad | Observaciones |
|------------|----------------|-----------------|---------------|
| **Consola Compras Madera** | Gestión de OC, montos, estados, KPIs de compra, proveedores, especificaciones técnicas | `purchase.order` + campos extendidos de purchasing | La vista `view_purchase_order_form_lumber` ya extiende el formulario nativo. Mantener como consola de compras. |
| **Consola Recepciones (lumber.reception)** | Ingesta de madera bruta desde packing list + guía despacho. Desviación, tolerancia, staging→stock | `lumber.reception` + `lumber.reception.line` | Flujo consolidado con gates, staging, auditoría criptográfica. No debe incluir gestión de OC más allá de vinculación. |
| **Consola Guías Procesadas (madenat.guia.processing)** | Ingesta de madera procesada (servicios). Cálculo de exportación, dimensiones imperiales | `madenat.guia.processing` + `madenat.guia.processing.line` | Similar a recepción pero con dimensiones imperiales + costos de servicio. |
| **Capa compartida de matching** | Normalizar referencia documental, buscar/vincular `purchase.order`, registrar estado de match | NUEVO: `madenat.purchase.order.matcher` (AbstractModel) o método en mixin existente | Debe ser usada por ambos flujos de ingesta. |
| **Capa compartida de control acumulado** | Calcular y persistir `received_volume_m3`, `pending_volume_m3`, `percent_completed` desde ambos flujos | `purchase.order` (campos computed/stored) | Actualmente solo lee `lumber.reception`. Debe ampliarse para incluir `madenat.guia.processing`. |
| **Capa de trazabilidad documental** | Preservar referencia original del documento, registrar decisiones de matching | NUEVO: campos `oc_reference_raw`, `oc_match_status`, `oc_match_note` en ambos modelos de ingesta | Implementar principio Documental ↔ Operativa. |

---

# 4. MATRIZ TÉCNICA POR ARCHIVO

| Archivo | Modelo | Método / Zona | Función actual | Problema | Cambio sugerido | Prioridad |
|---------|--------|---------------|---------------|----------|-----------------|-----------|
| `madenat_lumber_core/models/madenat_guia_processing.py` | `madenat.guia.processing` | campo `order_id` (línea ~768) | Many2one manual sin lógica automática | Sin asistencia de matching; OC queda vacía si operador no asigna | Añadir `oc_reference_raw`, `oc_match_status`, `oc_match_note`; añadir método `_match_purchase_order()` | **P0** |
| `madenat_lumber_core/models/madenat_guia_processing.py` | `madenat.guia.processing` | `action_verify_data` (~1204-1361) | Parsea PDF/Excel pero no persiste OC ni ejecuta matching | La referencia OC se extrae y se descarta | Persistir `pdf_data['orden_compra']` en `oc_reference_raw`; llamar `_match_purchase_order()` al final | **P0** |
| `madenat_lumber_core/models/madenat_guia_processing.py` | `madenat.guia.processing` | `action_process_from_staging` (~1366-1443) | Usa `order_id.name` o cae a `self.name` | Si no hay OC, la referencia es el número de guía (no una OC) | Usar `oc_reference_raw` como fallback; advertir si `oc_match_status='not_found'` | **P0** |
| `madenat_lumber_core/models/madenat_guia_processing.py` | `madenat.guia.processing` | `_create_basic_purchase_order` (~2449-2456) | Existe pero no se llama | Código muerto | Conectar a botón "Crear OC desde Guía" con `oc_match_status='created'` | **P2** |
| `madenat_lumber_core/models/madenat_guia_processing.py` | `madenat.guia.processing` | `_sync_purchase_order_lines` (~1131-1170) | Solo actualiza `order_line.product_qty` | No actualiza `received_volume_m3` en la OC | Añadir actualización de `received_volume_m3` vía `_compute_reception_stats` | **P1** |
| `madenat_lumber_core/models/lumber_reception.py` | `lumber.reception` | `_find_or_create_po_intelligent` (~2100-2243) | Busca OC por `partner_ref`/`name` normalizado; sobrescribe `manual_po_name` | Pierde referencia documental al vincular; busca por dos claves distintas | NO sobrescribir `manual_po_name`; usar nuevos campos `oc_reference_raw`/`oc_match_status`; unificar clave de búsqueda | **P0** |
| `madenat_lumber_core/models/lumber_reception.py` | `lumber.reception` | `create_po_from_oc_data` (~2247-2395) | Crea OC desde datos del PDF de compra | También sobrescribe `manual_po_name = False`; crea OC sin preguntar | Mantener pero con confirmación explícita del operador; setear `oc_match_status='created'` | **P1** |
| `madenat_lumber_core/models/lumber_reception.py` | `lumber.reception` | `_update_po_reception_stats` (~2465-2499) | Actualiza `received_volume_m3` en OC desde recepciones | Solo funciona para `lumber.reception` | Ampliar para que `purchase.order._compute_reception_stats` también lea `madenat.guia.processing` | **P1** |
| `madenat_lumber_core/models/lumber_reception.py` | `lumber.reception` | campos ~1126-1138 | `manual_po_name`, `purchase_order` (compute), `purchase_id` | Tres campos con semántica ambigua | Añadir `oc_reference_raw` (Char readonly), `oc_match_status` (Selection), `oc_match_note` (Text). Refactorizar `purchase_order` (compute) para usar `oc_reference_raw` como fallback en vez de `SIN ORDEN` | **P0** |
| `madenat_lumber_purchasing/models/lumber_reception.py` | `lumber.reception` | `_find_po_and_supplier` (~16-67) | Busca OC por `name =ilike po_ref`; si no existe, CREA OC automáticamente | **RIESGO CRÍTICO**: OC espurias, valores hardcode, sin supervisión humana | **ELIMINAR** rama `else` de creación automática (líneas 59-67). Reemplazar con estado `not_found` + `oc_reference_raw` preservado. | **P0** |
| `madenat_lumber_purchasing/models/purchase_order.py` | `purchase.order` | `_compute_reception_stats` (~235-264) | Calcula acumulados solo desde `reception_ids` (One2many a `lumber.reception`) | No incluye `madenat.guia.processing` → volumen acumulado incompleto | Ampliar dependencias `@api.depends` para incluir guías procesadas vinculadas, o añadir campo `total_received_all_sources` | **P1** |
| `madenat_lumber_purchasing/models/purchase_order.py` | `purchase.order` | `validate_or_create_po` (~288-496) | Gatekeeper API: busca por `partner_ref`, crea PO con `auto_create` | Búsqueda inconsistente (usa `partner_ref`, no `name`); crea PO silenciosamente si `auto_create=True` | Unificar clave de búsqueda con matcher común. Restringir `auto_create` a acción explícita del usuario. | **P1** |
| `madenat_lumber_purchasing/models/purchase_intake.py` | `madenat.purchase.intake` | `validate_or_create_po` (~118-192) | Segunda implementación de validación/creación de PO | **DUPLICADO** con `purchase_order.py`. Usa `status` en vez de `success` en retorno. | Consolidar en una sola implementación o deprecar la del AbstractModel si no tiene consumidores | **P1** |
| `madenat_lumber_purchasing/models/purchase_intake.py` | `madenat.purchase.intake` | `ensure_master_product` (~28-110) | Crea/valida producto `MADERA_GENERICA` | Puede CREAR producto automáticamente (línea ~45) | OK como fallback de configuración, pero loguear warning si crea | **P3** |
| `madenat_lumber_core/models/reception_service.py` | `LumberReceptionService` | `create_lots_from_staging` (~17-92) | Crea `stock.lot` desde staging | No asigna `purchase_order_id` en los lotes creados | Añadir `purchase_order_id` al dict `lot_vals` desde `reception.purchase_id` | **P1** |
| `madenat_lumber_core/models/reception_service.py` | `LumberReceptionService` | `create_stock_picking` (~94-155) | Crea albarán de recepción | Usa `reception.location_id` que puede ser `False` (ya no tiene `required=True`) | Sin cambios urgentes; el fallback `picking_type.default_location_dest_id` ya está implementado | **P3** |
| `madenat_lumber_purchasing/views/purchase_order_views.xml` | — | Vista formulario OC | Muestra campos de madera + seguimiento de recepción + pestaña trazabilidad | No muestra origen de guías procesadas (solo `reception_ids`) | Añadir pestaña o columna para guías procesadas vinculadas | **P2** |
| `madenat_lumber_core/views/guia_processing_views.xml` | — | Vista formulario guía procesada | Muestra `order_id` como Many2one estándar | No muestra `oc_reference_raw` ni estado de match | Añadir campo `oc_reference_raw` (readonly) + `oc_match_status` (badge) + botón "Buscar OC" | **P0** |
| `madenat_lumber_purchasing/views/lumber_reception_views.xml` | — | Vista formulario recepción | Muestra `purchase_id`, `manual_po_name`, `purchase_order` | `manual_po_name` desaparece al vincular | Añadir `oc_reference_raw` (readonly, preservado siempre) + `oc_match_status` | **P0** |
| `madenat_lumber_core/models/stock_lot.py` | `stock.lot` | N/A | Lotes con `purchase_order_id` y `reception_id`/`guia_processing_id` | `purchase_order_id` no siempre se asigna | Añadir `oc_reference_raw` (related a guía/recepción) para trazabilidad en lote | **P2** |

---

# 5. ARQUITECTURA MÍNIMA VIABLE

## 5.1 Principio rector: Separación Documental ↔ Operativa

```
┌──────────────────────────────────────────────────────────────────────┐
│                   CAPA COMPARTIDA DE MATCHING                        │
│            (mixin reutilizable en ambos modelos de ingesta)          │
│                                                                      │
│  _normalize_po_key(ref) → str                                        │
│  _find_po_candidates(ref, partner) → recordset                       │
│  _match_and_link(ref, partner) → dict{match_status, po, candidates}  │
│  _auto_match_or_defer(ref, partner) → actualiza oc_match_status      │
└──────────────────────────────────────────────────────────────────────┘
           ▲                              ▲
           │                              │
┌──────────┴────────────┐    ┌───────────┴─────────────┐
│ madenat.guia.         │    │ lumber.reception         │
│ processing            │    │                          │
│                       │    │ oc_reference_raw (Char)   │
│ oc_reference_raw      │    │ purchase_id (Many2one)    │
│ order_id (Many2one)   │    │ oc_match_status (Sel)     │
│ oc_match_status (Sel) │    │ oc_match_note (Text)      │
│ oc_match_note (Text)  │    │ manual_po_name (LEGACY)   │
└──────────┬────────────┘    └───────────┬──────────────┘
           │                             │
           └──────────┬──────────────────┘
                      ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       purchase.order                                 │
│                                                                      │
│  name (Char)           ← clave canónica de match (formato display)   │
│  partner_ref (Char)    ← clave secundaria de match                   │
│  ingestion_source_ref  ← se alimenta desde oc_reference_raw al crear │
│  reception_ids         ← One2many a lumber.reception                 │
│  guia_processing_ids   ← NUEVO: One2many a madenat.guia.processing   │
│  received_volume_m3    ← compute desde reception + guia_processing   │
│  pending_volume_m3     ← compute total_ordered - total_received_all  │
└──────────────────────────────────────────────────────────────────────┘
```

## 5.2 Contrato común de campos (ambos modelos de ingesta)

| Campo | Tipo | Propósito | Inmutable |
|-------|------|-----------|-----------|
| `oc_reference_raw` | `Char` | Referencia exacta del documento original (ej. `MC 1602-302`). Se llena en el parser. | ✅ Sí (readonly tras ingesta) |
| `oc_match_status` | `Selection` | `not_found`, `single_match`, `multi_match`, `manual`, `created` | ❌ No (cambia con acciones del operador) |
| `oc_match_note` | `Text` | Registro de auditoría: quién, cuándo, criterio | ❌ No (append-only recomendado) |
| `purchase_order_id` | `Many2one` | Vínculo operativo a `purchase.order` | ❌ No |

## 5.3 Capa común de matching

**Ubicación:** Nuevo método en `madenat.lumber.ingest.mixin` (AbstractModel ya heredado por ambos).

```python
def _match_purchase_order(self, oc_reference_raw):
    """
    Busca y vincula purchase.order desde referencia documental.
    Aplica niveles de matching progresivo.
    Retorna dict con match_status y po (o None).
    """
    # Nivel 1: Match exacto por nombre normalizado
    key = self._normalize_po_key(oc_reference_raw)
    po = self.env['purchase.order'].search([
        ('partner_id', '=', self.partner_id.id),
        ('state', 'in', ['draft', 'sent', 'purchase', 'done']),
    ]).filtered(lambda p: self._normalize_po_key(p.name) == key)

    if len(po) == 1:
        return {'match_status': 'single_match', 'po': po}
    elif len(po) > 1:
        return {'match_status': 'multi_match', 'po': None, 'candidates': po}

    # Nivel 2: Match por partner_ref
    po = self.env['purchase.order'].search([
        ('partner_id', '=', self.partner_id.id),
        ('state', 'in', ['draft', 'sent', 'purchase', 'done']),
    ]).filtered(lambda p: self._normalize_po_key(p.partner_ref or '') == key)

    if len(po) == 1:
        return {'match_status': 'single_match', 'po': po}

    # Nivel 3: Sin match
    return {'match_status': 'not_found', 'po': None}
```

## 5.4 Control acumulado por OC

**Objetivo:** `purchase.order` debe reflejar el volumen ingerido total desde **ambos flujos** (`lumber.reception` + `madenat.guia.processing`).

**Estrategia:**
1. Añadir campo `guia_processing_ids = One2many('madenat.guia.processing', 'order_id')` en `purchase.order`.
2. Modificar `_compute_reception_stats` para sumar `received_volume_m3` = Σ(`reception_ids.physical_volume_m3`) + Σ(`guia_processing_ids.vol_fisico`).
3. O alternativamente: crear un método `_compute_total_received_all_sources` que consolide ambas fuentes.

## 5.5 Reglas para evitar creación automática silenciosa

| Regla | Implementación |
|-------|---------------|
| **Nunca** crear `purchase.order` desde parser sin acción explícita del usuario | Eliminar `_create_po_from_guide` automático en purchasing. Reemplazar con estado `not_found` + preservación de referencia. |
| **Nunca** sobrescribir `oc_reference_raw` | El campo es `readonly=True` tras la ingesta. Solo el parser escribe. |
| **Siempre** preservar referencia documental | `oc_reference_raw` es inmutable post-ingesta. `manual_po_name` se mantiene como legacy hasta migración completa. |
| **Siempre** registrar decisión de matching | `oc_match_note` recibe timestamp + usuario + criterio. |

## 5.6 Estrategia de UI separada

| Consola | Módulo | Menú | Vista principal |
|---------|--------|------|----------------|
| **Compras Madera** | `madenat_lumber_purchasing` | Compras → Órdenes de Compra Madera | `view_purchase_order_form_lumber` (extiende formulario nativo) |
| **Recepciones** | `madenat_lumber_core` | Inventario → Recepciones → Guías de Despacho | `lumber.reception` formulario con pestañas Staging/Comercial/Trazabilidad |
| **Guías Procesadas** | `madenat_lumber_core` | Inventario → Recepciones → Guías Procesadas | `madenat.guia.processing` formulario con pestañas Staging/Exportación |

---

# 6. PLAN DE IMPLEMENTACIÓN POR ETAPAS

## Etapa 1 — Saneamiento mínimo (P0, riesgo BAJO)

**Objetivo:** Eliminar creación automática de OC y preservar referencia documental. Sin nuevos campos.

| Archivo | Cambio | Riesgo | Prueba |
|---------|--------|--------|--------|
| `purchasing/models/lumber_reception.py` | Desactivar rama `else` en `_find_po_and_supplier` (líneas 59-67). Reemplazar con `return False, supplier` + log warning. | **Bajo**: solo cambia comportamiento de fallback | CP-06: procesar recepción con OC inexistente, verificar que NO se crea purchase.order |
| `core/models/lumber_reception.py` | En `_find_or_create_po_intelligent`, NO sobrescribir `manual_po_name` a `False`. Mantener el valor original como trazabilidad. | **Bajo**: `manual_po_name` ya existía; solo se deja de limpiar | CP-04: verificar que `manual_po_name` persiste tras vincular OC |
| `core/models/lumber_reception.py` | En `create_po_from_oc_data`, NO sobrescribir `manual_po_name` a `False`. | **Bajo**: igual que arriba | Verificar tras crear OC desde PDF |

**Rollback:** Revertir los tres cambios (son eliminación de writes a `False`).

## Etapa 2 — Matching común (P0, riesgo MEDIO)

**Objetivo:** Añadir campos de trazabilidad documental en ambos modelos de ingesta + lógica de matching unificado.

| Archivo | Cambio | Riesgo | Prueba |
|---------|--------|--------|--------|
| `core/models/madenat_guia_processing.py` | Añadir campos `oc_reference_raw`, `oc_match_status`, `oc_match_note` | **Medio**: nuevos campos (migración Odoo necesaria) | CP-01, CP-02, CP-03 |
| `core/models/madenat_guia_processing.py` | Modificar `action_verify_data`: persistir `pdf_data['orden_compra']` en `oc_reference_raw` | **Medio**: toca flujo principal de verificación | CP-01: subir PDF con OC conocida |
| `core/models/madenat_guia_processing.py` | Añadir método `_match_purchase_order()` | **Medio**: nueva lógica, sin side effects en datos existentes | CP-01, CP-02, CP-03 |
| `core/models/lumber_reception.py` | Añadir campos `oc_reference_raw`, `oc_match_status`, `oc_match_note` | **Medio**: nuevos campos | CP-01, CP-02 |
| `core/models/lumber_reception.py` | Modificar `_find_or_create_po_intelligent`: usar `oc_reference_raw` en vez de `manual_po_name` para trazabilidad | **Medio**: cambio en flujo de matching | CP-01, CP-04 |
| `core/views/guia_processing_views.xml` | Añadir `oc_reference_raw` + `oc_match_status` a la vista | **Bajo**: solo UI | Verificar visualización |
| `purchasing/views/lumber_reception_views.xml` | Añadir `oc_reference_raw` + `oc_match_status` a la vista | **Bajo**: solo UI | Verificar visualización |

**Rollback:** Eliminar nuevos campos (son aditivos, no destructivos). Revertir `action_verify_data` a versión anterior.

## Etapa 3 — Control acumulado por OC (P1, riesgo MEDIO)

**Objetivo:** `purchase.order` refleja volumen ingerido desde ambos flujos.

| Archivo | Cambio | Riesgo | Prueba |
|---------|--------|--------|--------|
| `purchasing/models/purchase_order.py` | Añadir `guia_processing_ids = One2many('madenat.guia.processing', 'order_id')` | **Medio**: nueva relación | Verificar que el campo aparece en la OC |
| `purchasing/models/purchase_order.py` | Modificar `_compute_reception_stats` para incluir `guia_processing_ids` | **Medio**: cambia valores de `received_volume_m3`, `pending_volume_m3` | Verificar con OC que tenga ambos tipos de ingesta |
| `core/models/madenat_guia_processing.py` | En `_sync_purchase_order_lines` o `do_full_processing`: gatillar `_compute_reception_stats` en la OC vinculada | **Bajo**: solo añade refresh | Verificar que OC refleja volumen de guías procesadas |
| `core/models/reception_service.py` | Añadir `purchase_order_id` al dict `lot_vals` en `create_lots_from_staging` | **Bajo**: campo ya existe en stock.lot | Verificar que lotes nuevos tienen OC |

**Rollback:** Revertir cambios en `_compute_reception_stats` y eliminar `guia_processing_ids`. Los datos de volumen en OC volverían a mostrar solo recepciones.

## Etapa 4 — Ajustes de consola y reportabilidad (P2, riesgo BAJO)

**Objetivo:** Refinar UI, consolidar lógica duplicada, añadir reportes de trazabilidad.

| Archivo | Cambio | Riesgo | Prueba |
|---------|--------|--------|--------|
| `purchasing/views/purchase_order_views.xml` | Añadir pestaña/sección para `guia_processing_ids` | **Bajo**: solo UI | Verificar que guías procesadas aparecen en la OC |
| `purchasing/models/purchase_order.py` | Unificar `validate_or_create_po` de `purchase_order.py` y `purchase_intake.py` | **Medio**: consolidación de lógica | Verificar que ambos callers siguen funcionando |
| `purchasing/models/purchase_intake.py` | Deprecar `validate_or_create_po` si no tiene consumidores activos | **Bajo**: si HIP-05 confirma que no se usa | Verificar que ningún módulo llama al AbstractModel |
| `core/models/stock_lot.py` | Añadir `oc_reference_raw` (related) | **Bajo**: campo relacionado | Verificar visibilidad en vista de lote |

**Rollback:** Revertir vistas y quitar related field. La lógica consolidada se mantiene con ambas firmas (retrocompatible).

---

# 7. DECISIONES QUE DEBO TOMAR COMO DUEÑO FUNCIONAL

| # | Decisión | Opciones | Impacto | Recomendación |
|---|----------|----------|---------|---------------|
| **D1** | ¿Eliminar definitivamente `_create_po_from_guide` en purchasing o mantenerlo como acción explícita con botón? | A) Eliminar toda creación automática. B) Convertir en botón "Crear OC desde Guía" con confirmación. | Si se elimina, el operador debe crear la OC manualmente en Compras. Si se convierte en botón, hay que implementar la UI. | **Opción B**: mantener capacidad pero como acción explícita. El botón ya existe semánticamente (`action_link_to_existing_po` está como placeholder). |
| **D2** | ¿Unificar `manual_po_name` y `oc_reference_raw` o mantener ambos? | A) Mantener ambos (legacy + nuevo). B) Migrar `manual_po_name` a `oc_reference_raw` y deprecar el primero. | `manual_po_name` tiene datos históricos. | **Opción A** en etapa 1-2, **Opción B** en etapa 4 tras validar que todos los consumidores usan `oc_reference_raw`. |
| **D3** | ¿La capa de matching debe estar en el mixin `madenat.lumber.ingest.mixin` o en un nuevo AbstractModel `madenat.purchase.order.matcher`? | A) Mixin existente (ya heredado por ambos). B) Nuevo AbstractModel (más limpio, desacoplado). | El mixin ya tiene ~1500 líneas. Un nuevo modelo sería más mantenible pero añade otra herencia. | **Opción A** para etapa 2 (mínimo viable). **Opción B** como refactor futuro si el mixin crece demasiado. |
| **D4** | ¿Cómo manejar el control de volumen acumulado: un solo campo `received_volume_m3` que sume ambas fuentes, o dos campos separados? | A) Campo unificado `received_volume_m3` = recepciones + guías. B) Campos separados `received_from_reception` + `received_from_guia_processing`. | Si se unifica, no se puede distinguir el origen. Si se separa, se duplican KPIs. | **Opción A** con filtro por origen en la vista (group_by implícito). Añadir campo `received_from_guia_processing` solo si el negocio requiere distinguir. |
| **D5** | ¿El matching automático debe ejecutarse al subir documentos (action_verify_data) o solo bajo demanda (botón)? | A) Automático al verificar. B) Manual con botón "Buscar OC". C) Ambos: automático + posibilidad de re-ejecutar. | Automático puede dar falsos positivos si hay OCs con nombres similares. | **Opción C**: automático en `action_verify_data`, con botón "Reintentar Matching" para correcciones. |
| **D6** | ¿Qué hacer con las OCs existentes que se crearon automáticamente por `_create_po_from_guide`? | A) Auditarlas manualmente y fusionar duplicadas. B) Dejarlas como están y aplicar nuevas reglas solo hacia adelante. | Puede haber OCs duplicadas con la misma referencia. | **Opción A**: ejecutar SQL Check 3 + Check 4 para identificar duplicadas y decidir caso a caso. |
| **D7** | ¿El formato visible `MC 1602-302` debe ser el valor exacto de `oc_reference_raw` o se debe normalizar al persistir? | A) Persistir exactamente como aparece en el documento. B) Normalizar (trim, uppercase) al persistir. | Si se normaliza, se pierde el formato original del documento para auditoría. | **Opción A**: persistir tal cual. La normalización se aplica solo en la clave de matching (`_normalize_po_key`), no en el campo visible. |

---

## Resumen de dependencias entre etapas

```
Etapa 1 (Saneamiento)
  │
  ▼
Etapa 2 (Matching común) ← requiere Etapa 1 completada
  │
  ▼
Etapa 3 (Control acumulado) ← requiere Etapa 2 completada (necesita oc_reference_raw + match_status)
  │
  ▼
Etapa 4 (Ajustes UI + Reportes) ← requiere Etapa 3 completada
```

## Riesgos globales

| Riesgo | Mitigación |
|--------|------------|
| Migración de campos nuevos requiere script pre/post-migrate | Todos los campos nuevos son aditivos (no modifican datos existentes). `manual_po_name` se preserva como legacy. |
| Romper flujo de producción durante la implementación | Implementar por etapas, cada una independiente y con rollback simple. |
| Inconsistencia temporal entre `received_volume_m3` antes/después de Etapa 3 | El valor aumentará (porque ahora incluye guías procesadas). Comunicar a operadores antes del deploy. |
| `_find_po_and_supplier` en purchasing puede tener callers no detectados | Buscar exhaustivamente `_find_po_and_supplier` en todo el código antes de modificar. |

---

**Fin del documento de decisión.**