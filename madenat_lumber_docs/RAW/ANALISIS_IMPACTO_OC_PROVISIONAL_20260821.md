# Análisis de Impacto — OC Provisional desde Guía

## Alcance
Validación de la implementación de creación manual de `purchase.order` desde `madenat.guia.processing`. Solo lectura; sin modificar código/datos.

## Cambios auditados
1. `purchase_order.py`: `state='draft'` forzado (~392), validación `partner.exists()+active` (342-345), rechazo `product_uom_unit` para volumen>0 (~572).
2. `madenat_guia_processing.py`: `action_create_purchase_order_from_document` (3175+) delegador al gatekeeper.
3. `guia_processing_views.xml`: botón "Crear OC provisional".
4. Tests nuevos (9) en `madenat_lumber_purchasing/tests/`.

## Inventario de dependencias
Callers de `validate_or_create_po`: `guia_processing:3264` (nuevo) + tests. Sin otras rutas.
Campos `order_id`, `ingestion_source_ref`, `provisional`, `oc_match_status`: ya existentes; sin cambios en vistas/menús fuera del botón.

## Compatibilidad del gatekeeper
- Nuevas POs siempre `draft`; sin ruta previa que dependa de `sent`.
- Partner archivado → dict error (no excepción); `partner.active` validado.
- Partner sin VAT → permitido (documentado en investigación previa).
- `product_uom_unit` solo bloqueado si `qty>0`; productos de servicio con qty en unidad legítima podrían verse afectados si no especifican `product_uom` (ver Riesgos).

## UoM y líneas
- Fuente cantidad: `processing_line_ids.vol_purchase_m3`/`vol_shipment_m3`.
- Destino: m³ (producto maestro) en el gatekeeper.
- No hay conversión MBF→m³ interna en el gatekeeper (diferida); tests validan con `MBF_TO_M3`.

## Idempotencia y concurrencia
- Capa A: `if order_id: return action_open_po()`.
- Capa B: `validate_or_create_po` busca por `partner_ref+partner_id+company_id` cuando `auto_create=False`; con `auto_create=True` **no hay guard anti-duplicado previo a `create`** (riesgo).
- No hay constraint SQL ni lock; ventana de concurrencia entre `search` y `create`.

## Interfaz y seguridad
- Botón visible solo si `oc_reference_raw and not order_id and oc_match_status=='not_found'`.
- Validación en servidor en el método (bloquea multi_match/needs_review, etc.).

## Resultados de regresión
| Suite | Comando | Resultado | Clasificación |
|---|---|---|---|
| TestPOCreationFromGuide | --test-tags=/madenat_lumber_purchasing:TestPOCreationFromGuide | 9/9 PASS | OK |
| TestSupplierResolution | --test-tags=/madenat_lumber_core:TestSupplierResolution | 3 FAIL | Preexistente (id 676 residual) |

## Verificación de datos
SELECT: 0 OCs provisionales, 0 duplicados por `ingestion_source_ref`, 0 no-draft. Datos limpios.

## Matriz de riesgos
| Hallazgo | Severidad | Evidencia | Impacto | Mitigación | Bloquea QA | Bloquea prod |
|---|---|---|---|---|---:|---:|
| Sin guard anti-duplicado con `auto_create=True` en gatekeeper | Media | purchase_order.py ~330-355 | Doble clic/concurrencia | Añadir search por `ingestion_source_ref` antes de create | No | Sí |
| `product_uom_unit` bloquea productos no-volumétricos si no definen `product_uom` | Moderada | ~572 | Servicios/fletes con qty en unidad podrían fallar | Enlazar `product_uom` a línea o excluir tipo servicio | No | No |
| Fallos TestSupplierResolution | Media | id 676 residual | Regresión en core | Limpiar base antes de runs CI | No | No |
| Sin constraint SQL en `ingestion_source_ref` | Baja | purchase_order.py | Duplicados por concurrencia | Documentado; mitigación futura | No | No |

## Clasificación de fallos
| Test/suite | Estado | Evidencia | Clasificación | Acción requerida |
|---|---|---|---|---|
| TestPOCreationFromGuide (9) | PASS | EXIT=0 | OK | — |
| TestSupplierResolution (3) | FAIL | id 676 residual (contaminación previa sin rollback) | Preexistente | Limpiar base |

## Veredicto de promoción
**Opción 2 — Apto condicionalmente para integración/QA.**

## Condiciones antes de producción
**Obligatorio:**
1. Añadir guard anti-duplicado por `ingestion_source_ref` antes de `create` (con `auto_create=True`).
**Recomendado:**
2. Ajustar la UoM para servicios/fletes (no usar `product_uom_unit` como válido sin excepción por tipo).
3. Limpiar base `madenat_test` (id 676 residual).
**Deuda técnica no bloqueante:**
4. Constraint SQL/función para idempotencia fuerte.