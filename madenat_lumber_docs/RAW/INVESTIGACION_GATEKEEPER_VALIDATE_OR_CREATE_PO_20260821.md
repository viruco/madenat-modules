# Investigación del Gatekeeper `validate_or_create_po`

## Alcance y restricciones

Investigación estrictamente de solo lectura sobre `validate_or_create_po` en `madenat_lumber_purchasing` (purchase_order.py:289-494 y purchase_intake.py:118). Sin modificar archivos, datos ni ejecutar migraciones. Cada conclusión cita archivo:línea.

## Evidencia de implementación

El gatekeeper existe en DOS ubicaciones:

| Ubicación | Línea | Comportamiento |
|---|---|---|
| `PurchaseOrderLumber.validate_or_create_po(payload, policy)` (purchase_order.py) | 289-494 | Implementación completa: valida partner/líneas, busca PO existente, crea PO, crea líneas, retorna dict |
| `PurchaseIntake.validate_or_create_po(payload, policy)` (purchase_intake.py, AbstractModel) | 118 | Wrapper/contrato documentado (payload: partner_id, partner_ref, currency_id, lines[{product_id,name,qty,uom_id,price}]; policy: auto_create, provisional; retorna dict con status) |

**Sin llamadores externos** fuera de `purchase_intake.py` (el wrapper no ha sido invocado por guia_processing ni lumber_reception — `grep -rn "validate_or_create_po" custom_addons/` solo muestra las 2 definiciones + 1 log interno). El módulo `madenat_lumber_purchasing` aún no está integrado con los flujos core.

## Flujo técnico real

```text
validate_or_create_po(payload, policy)                                    [purchase_order.py:289]
├─ VALIDACIÓN 1: partner_id requerido → dict error si falta               [~313]
├─ REGLA ORO: _get_master_product_strict() (UserError si MADERA_GENERICA no existe) [~320, 671-697]
├─ VALIDACIÓN 2: búsqueda PO existente solo si (not auto_create) y partner_ref+partner_id
│   domain: partner_ref=, partner_id=, company_id=, limit=1             [~330-339]
├─ VALIDACIÓN 3: si creará nueva (auto_create o no existe) y sin lines → dict error [~345]
├─ RAMA 1 — CREAR: po_vals {partner_id, partner_ref, currency_id, date_order=now,
│   origin, ingestion_source_ref, state='draft' if provisional else 'sent', provisional} [~365-382]
│   self.create(po_vals) → _create_po_lines_with_validation(new_po, lines, policy) [498]
│   si lines_created==0 → new_po.unlink() + dict error                  [~410-425]
│   estado_final = 'created_provisional' | 'created' (+ advertencias parciales) [~430-470]
├─ RAMA 2 — VINCULAR: existing_po + estado 'linked'                      [~477-485]
└─ RETORNA: dict {success, po_id, state, message, po_name} | {success:False, error} [~495-521]
```

Efecto transaccional: sobre savepoint del caller (no hay savepoint interno). Excepciones posibles: UserError (producto master faltante), excepción genérica → `return {success:False, error}` (capturada, no relanzada). Riesgo funcional: `state='sent'` si `provisional=False` (posible si caller lo define).

## Contrato de entrada del payload

| Clave/campo | Obligatorio | Tipo | Fuente Procesados | Fuente Producto | Validación actual | Riesgo |
|---|---|---|---:|---|---|---|
| `partner_id` | Sí | int | guia.partner_id.id | reception.supplier_id.id | sí (dict error) | No verifica `active` ni VAT |
| `partner_ref` | Condicional (si auto_create=False) | str | oc_reference_raw | manual_po_name | sí (solo en búsqueda) | No se valida existencia |
| `currency_id` | No | int | guia.currency_id.id | reception.currency_id.id | no | default company |
| `date_order` | No | datetime | now (default gatekeeper) | now | no | siempre `fields.Datetime.now()` |
| `origin` | No | str | "Guía #{name}" | "Recepción #{name}" | no | trazabilidad débil si se omite |
| `ingestion_source_ref` | No | str | oc_reference_raw | oc_reference_raw | no | reutilizable (campo existe) |
| `company_id` | No | int | implícito env | implícito env | no | no se filtra en búsqueda |
| `lines` | Sí (para crear) | list[dict] | processing_line_ids | reception_line_ids | sí (0 líneas → error) | estructura por dict |
| `product_id` | No | int | product_id línea | product_id línea | `_resolve_product_with_fallback` | fallback nombre |
| `product_qty` (docstring `qty`) | Sí | float | vol_purchase_m3/shipment | vol_purchase_m3 | no | depende de UoM |
| `product_uom` (docstring `uom_id`) | No | int | (debe definirse m³) | (debe definirse m³) | no | ver auditoría UoM |
| `price_unit` (docstring `price`) | No | float | additional_cost/service_volume_m3 | 0/estimado | no | ver auditoría precio |

Otras claves del docstring wrapper (purchase_intake.py:118): `name` (descripción), `price`.

## Auditoría de validaciones

| Regla | Implementado | Evidencia |
|---|---|---|
| Exige partner | Sí | purchase_order.py ~313 |
| Verifica partner.active | **No localizado** | sin `active` en la búsqueda/validación |
| Valida VAT | **No localizado** | sin chequeo VAT en gatekeeper |
| Valida líneas antes de crear | Sí | ~345 (sin lines → error) |
| Evita OC vacía | Sí | ~410-425 (unlink si 0 líneas) |
| Fuerza draft | **Parcial** | `state='draft' if provisional else 'sent'` (~380) — permite `sent` si caller pasa `provisional=False` |
| company_id/fiscal_position/picking | **No definido** | solo `company_id` implícito; no `fiscal_position_id` ni `picking_type_id` |

## Auditoría de líneas y UoM

`_create_po_lines_with_validation` (purchase_order.py:498-620):
- `product_id` → `_resolve_product_with_fallback` (645)
- `product_uom = line_data.get('product_uom')`; si no → `product.uom_po_id.id or product.uom_id.id` (555-558); se escribe en `purchase.order.line.product_uom` (597)

**Hallazgos UoM:**
1. **Unidad de compra propuesta:** depende del payload. Para MADERA_GENERICA (producto maestro con `uom_id`/`uom_po_id` = m³ según `ensure_master_product` en purchase_intake.py:22-40), si el payload omite `product_uom`, el gatekeeper usa la UoM del producto = m³ (correcto). Si el caller envía `product_uom_unit`, repite la inconsistencia.
2. **Campo almacenado** `purchase.order.line.product_uom` = la UoM resuelta (línea 597).
3. **Cantidad en `product_qty`:** no se normaliza; usa el valor del dict del payload tal cual.
4. **¿Mezcla m³ con product_uom_unit?** Solo si el **caller** envía `product_uom_unit` con qty m³ — exactamente lo que hace `_create_po_from_guide` DEPRECATED (lumber_reception.py:177: `product_uom=self.env.ref('uom.product_uom_unit').id` con `product_qty=total_volume` m³). **El gatekeeper no lo corrige** (acepta el `product_uom` del payload).
5. **Conversiones MBF↔m³:** `MBF_TO_M3 = Decimal('2.36')` (utils_uom.py:84), validada en utils_uom.py:510. **No hay conversión explícita en el gatekeeper ni en `_create_po_lines_with_validation`** — trabajo solo en m³ si el caller lo reparte.
6. **¿Es seguro sin corregir?** **No del todo**: seguro solo si el caller define explícitamente `product_uom` = uom m³ y cantidad en m³. Corre riesgo de repetir el error DEPRECATED si se omite o se envía unidad.
7. **Cambio mínimo sugerido:** en `_create_po_lines_with_validation`, normalizar `product_uom` a la UoM de compra del producto maestro (m³) cuando la cantidad es volumen, y convertir explícitamente MBF→m³ con `MBF_TO_M3` antes de escribir `product_qty`.

## Auditoría de precio provisional

- `price_unit` = valor del dict `line_data.get('price')`/`price_unit`; no hay **cálculo automático** en el gatekeeper. El precio lo decide el caller.
- `_create_po_from_guide` (DEPRECATED) calcula `unit_price = net_total / total_volume` (lumber_reception.py:141-142) — **precio estimado operativo** derivado del documento, no precio negociado. Riesgo de confundirlo con precio comercial pactado.
- **¿Puede `price_unit=0`?** Sí: el gatekeeper no valida precios. Odoo permite confirmar PO con líneas de precio 0 (hay warning de margen en UI, no bloqueo de ORM). El control de "precio pendiente" debe vivir en un campo/actividad de la PO provisional, no en el gatekeeper.

## Idempotencia y prevención de duplicados

| Estrategia | Presente | Evidencia | Nivel |
|---|---|---|---|
| `search(..., limit=1)` para PO existente | Sí (solo si not auto_create) | ~330-339 | Parcial |
| Constraint SQL `_sql_constraints` | **No localizado** en madenat_lumber_purchasing | grep sin `_sql_constraints` | Inexistente |
| Locks / FOR UPDATE | **No localizado** | sin `for_update` | Inexistente |
| `savepoint` interno | **No localizado** (depende del caller) | sin savepoint en gatekeeper | Parcial |
| `IntegrityError` handling | No (solo `except Exception`) | ~490 | Parcial |
| Camps `source_model`/`source_id` | **No localizados** en PO | solo `origin`, `ingestion_source_ref`, `lumber_reception_id(s)`, `reception_ids` | Inexistente |
| Guard `guide_id` desde callers | No (no hay callers) | — | Inexistente |
| Doble clic / doble llamada | **No protegido** | sin flag | Inexistente |

**Nivel global: PARCIAL.** El único mecanismo anti-duplicado es la búsqueda previa condicionada a `not auto_create`; si `auto_create=True` no se busca nada y se crea siempre. Riesgo alto de duplicados.

## Proveedor y estados de conciliación

- `partner_id` requerido (dict error si falta) — purchase_order.py:313.
- `partner.active`: **no verificado** por el gatekeeper.
- VAT: **no validado**.
- El gatekeeper **desconoce `oc_match_status`** (no lee el campo); cualquier caller puede crear PO independientemente del estado de match.
- Multi-match: no relevante para el gatekeeper (recibe un `partner_id` ya resuelto); el riesgo `[:1]` vive en la capa de matching de Producto, no aquí.

**Matriz de decisión propuesta (no implementada):**

| Estado de match | Partner resuelto | Acción permitida | Resultado esperado |
|---|---:|---|---|
| `single_match` | Sí | No crear | Vincular OC existente |
| `multi_match` | Sí | **Bloquear creación** | Resolución manual primero |
| `not_found` | Sí | Crear provisional | PO draft con trazabilidad |
| `not_found` | No | **Bloquear** | UserError "proveedor no resuelto" |
| `needs_review` | Sí | **Bloquear** | Revisar proveedor/OC antes |
| `manual` | Sí | No crear (vincular) | Usar flujo manual existente |

## Trazabilidad y ownership

Campos existentes reutilizables en `purchase.order` (purchase_order.py):
- `ingestion_source_ref` (Char, línea 49) — referencia documental.
- `partner_ref` (estándar) — referencia externa.
- `origin` (estándar) — origen.
- `provisional` (Boolean, línea 225) — indicador provisional.
- `lumber_reception_id/ids`, `reception_ids` (20/35/42) — vínculos de recepción.
- `create_uid`/`create_date` (estándar Odoo) — usuario/fecha de creación.

**No hay campo `source_model`/`source_id` en PO** (para distinguir guía vs recepción) — se reutilizaría `origin` ("Guía #..." / "Recepción #...") + `ingestion_source_ref`. Solo si `origin` se demuestra insuficiente debería proponerse campo nuevo. **El dueño de la lógica comercial es `madenat_lumber_purchasing`** (Regla de Oro purchase_order.py:289-298, purchase_intake.py:9-10).

## Reutilización Procesados y Producto

- **Reutilizable**: ambos flujos pueden construir el payload y llamar al wrapper `PurchaseIntake.validate_or_create_po`. El gatekeeper es agnóstico del origen.
- **Condición**: el llamador debe resolver `partner_id` inequívocamente antes (Procesados `_resolve_or_create_supplier`; Producto `_find_po_and_supplier`) y forzar `provisional=True`.

## Cobertura de pruebas existente

`custom_addons/madenat_lumber_purchasing/tests/` — **directorio no listado/vacío**: no hay tests de `madenat_lumber_purchasing`. No hay cobertura existente para `validate_or_create_po`, líneas, UoM, proveedor, duplicados ni trazabilidad.

## Matriz de brechas y riesgos

| Hallazgo | Severidad | Evidencia archivo:línea | Impacto | Cambio mínimo sugerido | ¿Bloquea implementación? |
|---|---|---|---|---|---|
| Permite `state='sent'` si `provisional=False` | **Alta** | purchase_order.py:~380 | OC confirmable sin revisión | Forzar `state='draft'` siempre (ignorar provisional para estado) | Sí |
| No verifica `partner.active` ni VAT | Media | purchase_order.py:~313 | OC con proveedor archivado | Validar `partner.active` en gatekeeper | Sí |
| UoM no normalizada (riesgo m³ en `product_uom_unit`) | **Crítica** | purchase_order.py:555-558,597; lumber_reception.py:177 | OCs con cantidades en UoM errónea | Normalizar UoM a m³ de producto maestro; convertir MBF→m³ con `MBF_TO_M3` | Sí |
| Sin protección anti-duplicado cuando `auto_create=True` | **Alta** | purchase_order.py:~330-355 | OCs duplicadas por doble clic | Guard por `origin`+`partner_ref`+`ingestion_source_ref` + chequear `order_id`/`purchase_id` del origen | Sí |
| No valida `price_unit` (acepta 0) | Media | gatekeeper sin chequeo | Precio no negociado sin aviso | Campo/actividad "precio pendiente"; no bloquear ORM | Sí (para política) |
| `fiscal_position_id`/`picking_type_id` no definidos | Baja | po_vals ~365-382 | PO sin F.P. | No bloquea; definir si multi-fiscal | No |
| Sin `source_model`/`source_id` | Baja | purchase_order.py (no localizado) | Trazabilidad vía `origin`+`ingestion_source_ref` | Reutilizar `origin`; solo agregar campo si se demuestra insuficiente | No |
| Sin tests en madenat_lumber_purchasing | Alta | tests/ vacío | Regresión sin cobertura | Crear test_po_creation_from_guide.py | Sí |
| Integración core↔purchasing inexistente (sin callers) | Media | grep `validate_or_create_po` (solo 2 defs) | Gatekeeper no conectado | Crear método delegador en guia_processing (3175) | Sí |

## Veredicto arquitectónico

**Opción B — `validate_or_create_po` puede reutilizarse como base, pero requiere correcciones previas obligatorias.**

El gatekeeper ya cubre: partner requerido, líneas requeridas, unlink si 0 líneas, retorno dict estructurado, RAMA vincular, trazabilidad por `ingestion_source_ref`+`provisional`. Sin embargo NO es seguro hoy tal cual por: (1) riesgo de `sent`, (2) UoM no normalizada (heredable del error DEPRECATED), (3) sin anti-duplicado con `auto_create=True`, (4) sin validación `partner.active`, (5) sin tests.

## Decisiones que requieren aprobación humana

1. **Wizard vs botón/método directo:** recomendación método en `PurchaseOrderLumber` + botón en guía (menos UI, mismo gatekeeper).
2. **UoM de líneas:** m³ (UoM del producto maestro MADERA_GENERICA) como única permitida para cantidades de volumen; convertir MBF→m³ en el caller con `MBF_TO_M3` (utils_uom.py:84). No usar `product_uom_unit`.
3. **Precio provisional:** permitir `price_unit=0` con campo/actividad "precio pendiente"; opcionalmente derivar `additional_cost/service_volume_m3` como estimado operativo solo si documentado.
4. **Estados de conciliación que permiten crear:** solo `not_found` con partner inequívoco (matriz de la sección Proveedor). Bloquear `multi_match`/`needs_review`.
5. **Estrategia anti-duplicado:** guard: si `order_id`/`purchase_id` ya definido en origen → no crear; si existe PO con `partner_ref`+`partner_id`+`ingestion_source_ref` → vincular.
6. **Trazabilidad:** reusar `origin` + `ingestion_source_ref` + nota chatter; no agregar campos nuevos salvo evidencia contraria.

## Plan posterior condicionado

**Cambios obligatorios antes de implementar:**
1. Forzar `state='draft'` en `validate_or_create_po` (purchase_order.py:~365-382).
2. Normalizar UoM en `_create_po_lines_with_validation` (555-558,597) al m³ del maestro y convertir MBF→m³.
3. Guard anti-duplicado por `origin`/`partner_ref`/`ingestion_source_ref` + chequeo `order_id`/`purchase_id` del origen.
4. Validar `partner.active` en gatekeeper.
5. Crear tests en `madenat_lumber_purchasing/tests/` (no existe).

**Cambios recomendados no bloqueantes:**
- Definir `fiscal_position_id`/`picking_type_id` si aplica.
- Actividad "precio pendiente" cuando `price_unit=0`.

**Archivos previsiblemente involucrados:**
- `madenat_lumber_purchasing/models/purchase_order.py` (gatekeeper/po_vals/líneas).
- `madenat_lumber_purchasing/models/purchase_intake.py` (wrapper docstring/validación).
- `madenat_lumber_core/models/madenat_guia_processing.py` (delegar action_create_purchase_order_from_document 3175 al gatekeeper).
- `madenat_lumber_purchasing/models/po_creation_guide.py` (nuevo, método `_create_po_from_guia`).
- `madenat_lumber_purchasing/views/po_creation_guide_views.xml` (botón en guía).
- `madenat_lumber_purchasing/views/` (botón en recepción si aplica).
- `madenat_lumber_purchasing/tests/test_po_creation_from_guide.py` (nuevo).

**Tests mínimos obligatorios (futura implementación):**
- `test_create_po_with_partner_resolved_creates_draft` (draft + líneas + `created_provisional`).
- `test_create_po_without_partner_blocks` (dict error, sin PO).
- `test_create_po_multiple_lines_maps_1to1`.
- `test_double_call_no_duplicate_po` (guard).
- `test_po_always_draft` (incluso con `provisional=False`).
- `test_lines_use_m3_uom` (product_uom m³, no unidad).
- `test_mbf_converted_to_m3` (si payload en MBF).
- `test_partner_inactive_blocks`.
- `test_ingestion_source_ref_preserved`.