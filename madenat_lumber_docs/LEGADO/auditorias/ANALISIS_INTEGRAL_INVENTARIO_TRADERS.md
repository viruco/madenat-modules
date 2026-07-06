# Análisis Integral del Sistema de Inventario para Traders de Madera — Odoo 18 CE

**Proyecto**: MADENAT Lumber  
**Fecha**: 2026-06-04  
**Versión**: 1.0.0  
**Alcance**: Análisis basado en evidencia de código, documentación canónica, auditorías y modelos  
**Módulos auditados**: `madenat_lumber_core`, `madenat_lumber_costing`, `madenat_lumber_logistics`, `madenat_lumber_billing`, `madenat_lumber_purchasing`, `madenat_lumber_shipping_core`, `madenat_toll_processing`, `madenat_vendor_payment`, `madenat_lumber_reports`, `madenat_lumber_reception_improvements`

---

# 1. ESTADO ACTUAL DEL SISTEMA — MAPA GENERAL

## 1.1 Arquitectura de módulos

El ecosistema MADENAT se compone de **10 módulos activos** más documentación, organizados en capas:

```
madenat_lumber_shipping_core      ← Embarques y booking
         ↓
madenat_lumber_core                ← Núcleo: recepción, staging, lotes, guías, cálculos
         ↓
madenat_lumber_logistics           ← Contenedores y logística física
madenat_lumber_costing             ← Costeo multi-nivel y liquidación
madenat_lumber_billing             ← Facturación y consolidación
madenat_lumber_purchasing          ← Compras extendidas
madenat_toll_processing            ← Maquila / procesamiento externo
madenat_vendor_payment             ← Pagos a proveedores
madenat_lumber_reception_improvements ← Mejoras de recepción
madenat_lumber_reports             ← Meta-módulo de reportes
```

La arquitectura es **modular parcial**: se extrajeron componentes clave (parser, workflow, servicio) del monolito original, pero `lumber_reception.py` aún concentra `LumberReceptionLine` + `LumberReception` (2573 líneas), y `madenat_guia_processing.py` pesa 3465 líneas con las dos clases aún acopladas.

## 1.2 Modelos principales y sus responsabilidades

| Modelo | Archivo | Líneas | Rol |
|--------|---------|--------|-----|
| `stock.lot` (extendido) | `stock_lot.py` | 1392 | Lote con dimensiones, volúmenes, costos, genealogía, trazabilidad |
| `lumber.reception` + `.line` | `lumber_reception.py` | 2573 | Ingreso de madera bruta con staging, gates y validación |
| `madenat.guia.processing` + `.line` | `madenat_guia_processing.py` | 3465 | Recepción de madera procesada por servicio externo |
| `stock.lot.cost.line` | `stock_lot_cost_line.py` | 84 | Línea de costo por lote (modelo canónico) |
| `lumber.cost.distribution` + `.line` | `lumber_cost_distribution.py` | 315 | Expediente de liquidación de costos (landed costs) |
| `lumber.export.shipment` | logistics | — | Embarque / booking |
| `lumber.container` | logistics | — | Contenedor |
| `lumber.billing.consolidation` + `.line` | billing | — | Consolidación de facturación |
| `madenat.subproducto` | `madenat_subproducto.py` | — | Clasificación de subproducto (BLANK, RIP, S2S) |

## 1.3 Flujo operativo actual documentado

### 1.3.1 Flujo de recepción de madera bruta (`lumber.reception`)

```
1. Creación (draft) → carga PDF/Excel
2. Gate 0 + Gate 1: parseo y staging en lumber.reception.line
3. Gate 2: análisis comercial, visuales, nominales
4. Gate 3: generación de stock.lot + stock.move + stock.picking (WRITE REAL)
5. Validación: button_validate con autorreparación de productos
6. Estados: draft → processing → verified → done (o cancel/error)
```

**Maduro**: El flujo básico de staging → lotes está completo y funcional. Las dimensiones duales (físico/visual, métrico/imperial) están implementadas con precisión de 3 decimales.

### 1.3.2 Flujo de guía de procesamiento (`madenat.guia.processing`)

```
1. Creación (draft) → adjuntar PDF/Excel
2. action_verify_data: parseo → staging lines
3. action_assign_commercial_defaults: sugerir nominales
4. action_process_from_staging → do_full_processing: staging → lotes reales
5. action_validate: picking + stock.move + confirmación
6. Estados: draft → verified → processed → validated (terminal)
7. Cancelación segura con escudos logístico/financiero
```

**Funcional pero con deuda**: 3465 líneas, campos duplicados, métodos duplicados, sin tests unitarios.

### 1.3.3 Flujo de costeo (`lumber.cost.distribution`)

```
1. Crear expediente (draft)
2. Seleccionar scope: booking/container/reception/purchase/manual
3. Auto-detección de lotes con blindaje anti-basura (ref + volumen > 0)
4. Cargar documentos de gasto (cost_line_ids)
5. action_apply_costs: prorrateo por volumen_export/volumen_físico/peso/piezas/equitativo/container
6. Inyección en stock.lot.cost.line por cada lote
7. Estados: draft → applied → cancelled (reversible)
```

**Funcional**: El motor de prorrateo está implementado con 6 métodos de distribución, detección de contenedores únicos y soporte de costo por contenedor.

---

# 2. QUÉ YA ESTÁ SÓLIDO (MADURO)

## 2.1 Núcleo de trazabilidad de lotes

- ✅ **Unicidad de lotes**: `stock.lot` con `reception_id` y `guia_processing_id` mutuamente excluyentes (constraint validado)
- ✅ **Genealogía**: `parent_lot_id` → `child_lot_ids` → `generation_level` recursivo
- ✅ **Estados de trazabilidad**: `recepcionado → en_patio → procesado → consolidado → embarcado` con 5 indicadores de procesamiento
- ✅ **Origen dual**: `reception_type` (raw/processed) computado automáticamente
- ✅ **Guía number**: `guia_number` computado desde `reception_id.name` o `guia_processing_id.name`
- ✅ **Conexión con OC**: `purchase_order_id` + `supplier_id` computados desde la guía o recepción

## 2.2 Sistema de dimensiones y volúmenes

- ✅ **Dimensiones fraccionarias**: `espesor_inch_frac`, `ancho_inch_frac`, `largo_ft_frac` con parser bilingüe (mm/pulgadas)
- ✅ **Conversión automática**: fracciones → métrico (`espesor_mm`, `ancho_mm`, `largo_m`)
- ✅ **Volumen dual**: `volume_purchase_m3` (bruto) + `vol_shipment_m3` (comercial) con lógica condicional por perfil
- ✅ **Factor 5085 vs 1550**: bifurcación correcta por `largo_ft_frac` (presencia de pies → blanks, ausencia → métrico)
- ✅ **Fix de blanks (AD-27)**: blanks clear ahora usan exclusivamente `BLANK_CLEAR_FACTOR`, sin overmeasure S2S
- ✅ **Precisión**: `r3()` para redondeo a 3 decimales, `Decimal` para operaciones financieras en `_compute_export_values`
- ✅ **MBF**: cálculo dual (desde m³ vía ÷2.36 y desde fracciones imperiales vía board_feet/1000)
- ✅ **Salvavidas**: `nominal` como fallback cuando el cálculo geométrico da 0 o falla

## 2.3 Constantes y parametrización

- ✅ **Fase 1 (AD-28)**: 7 hardcodes movidos a `ir.config_parameter` con fallback exacto
- ✅ **Fase 2 (AD-29)**: 4 modelos persistentes con UI de mantenimiento + helper centralizado (`madenat.ingestion.config`)
- ✅ **Fase 3 (AD-30)**: `lumber.export.formula` y `lumber.ingestion.format` parametrizados
- ✅ **Cadena de fallback**: Modelo Fase 2 → ir.config_parameter Fase 1 → hardcode legacy
- ✅ **Constantes de ingeniería**: `MM_PER_INCH`, `FT_TO_M`, `BLANK_CLEAR_FACTOR`, `INCH_SQ_METERS_TO_M3` blindadas como constantes canónicas (no parametrizables — TD-006)
- ✅ **Validaciones de integridad**: UNIQUE, CHECK, no solapes en modelos Fase 2

## 2.4 Infraestructura de staging y gates

- ✅ **3 Gates documentados**: Gate 1 (staging) → Gate 2 (verificación) → Gate 3 (validación = único write real)
- ✅ **Auditoría criptográfica**: `audit_snapshot` (JSON) + `audit_hash` (SHA-256) en líneas de staging
- ✅ **Checklist de validación**: `ValidationChecklistMixin` con 7 validadores de integridad
- ✅ **Mixin de ingesta**: `MadenatLumberIngestMixin` compartido entre recepción y guías

## 2.5 Documentación canónica

- ✅ **Sistema CANON**: 9 archivos canónicos activos con versionado y reglas de actualización
- ✅ **Decision Log**: 749 líneas con entradas desde AD-01 hasta AD-30, meta-entradas, bugs y hotfixes
- ✅ **Continuidad**: checkpoint técnico vivo actualizado al 2026-06-02
- ✅ **Backlog**: fases priorizadas con criterios de salida
- ✅ **Tests**: matriz de validación funcional (T01-T33)
- ✅ **WIKI**: 7+ documentos técnicos detallados (modelo_lotes, gates, servicio, validadores, ingesta, dependencias, herencia)
- ✅ **Auditorías**: 2 auditorías técnicas exhaustivas (2026-06-03, 2026-06-04)

---

# 3. QUÉ FALTA COMPLETAR — HUECOS IDENTIFICADOS

## 3.1 Funcional

| Hueco | Severidad | Evidencia | Ubicación |
|-------|-----------|-----------|-----------|
| `madenat_guia_processing` sin tests unitarios | **ALTA** | 3465 líneas, 0 tests específicos. Riesgo máximo de regresión | `AUDITORIA_2026-06-04 §5` |
| Campos duplicados en `MadenatGuiaProcessing` | **ALTA** | `vol_total_m3`, `vol_comercial`, `vol_fisico`, `can_process` definidos 2 veces cada uno. Solo la última definición gana → código muerto | `madenat_guia_processing.py:906-982` |
| Métodos duplicados en guía processing | **MEDIA** | `_validar_y_enriquecer_lineas` en 2 lugares (`:2297` y `:2405`), `_compute_vol_purchase_m3` en 2 lugares (`:301` y `:424`) | `madenat_guia_processing.py` |
| `LUMBER_DIMENSION_MAP` hardcodeado sin migrar a Fase 2 | **MEDIA** | Diccionario de 48 líneas con dimensiones que ya deberían consultar `lumber_blank_nominal_map` | `madenat_guia_processing.py:25-73` |
| Parseo Excel/PDF duplicado entre guía y parser | **MEDIA** | `_parse_dispatch_pdf` y `_parse_packing_excel` viven en la cabecera de guía, pero `MadenatReceptionParser` (AbstractModel) ya tiene lógica equivalente | `madenat_guia_processing.py:1929-2110` vs `reception_parser.py` |
| `costing_menus.xml` comentado sin documentar | **BAJA** | Línea 30 de `madenat_lumber_costing/__manifest__.py` comentada sin razón documentada | `__manifest__.py` |
| Wizard archivado `lumber_consolidation_import_wizard.py` no movido a `_archive/` | **BAJA** | Documentado como dead code pero aún en `wizards/` activo | `madenat_lumber_logistics/wizards/` |
| Flujo de devoluciones no documentado formalmente | **MEDIA** | No hay documento canónico que describa el flujo completo de devolución: picking → stock.move inverso → estado de lote | — |

## 3.2 Técnico

| Hueco | Severidad | Evidencia |
|-------|-----------|-----------|
| `fields.Float` para dinero en todo el proyecto | **CRÍTICO** | Todos los campos de costo/precio/monto (USD, CLP) usan Float en lugar de Monetary. Viola OCA/Odoo 18 best practices. ~18 horas de corrección. |
| Hardcodes `25.4` en `lumber_shipment_line.py` y `lumber_reception_mass_update.py` | **CRÍTICO** | No usan `MM_PER_INCH` de `utils_uom.py`. Riesgo de inconsistencia si cambia la constante. |
| `mm_to_inch()` en `utils_uom.py` usa literal `25.4` en vez de `MM_PER_INCH` | **MEDIO** | La propia función de utilidad no referencia su propia constante. |
| `sudo()` en deletes de quants/pickings/moves | **ALTO** | 22 ocurrencias de `sudo()` en código activo. Las de delete (`lumber_reception.py:1201-1262, 2559-2573` y `reception_service.py:126-137`) son particularmente riesgosas. |
| Lógica de delete de stock moves duplicada | **MEDIO** | `lumber_reception.py:2559-2573` es idéntico a `reception_service.py:126-137`. |
| N+1 queries en `_compute_estado_trazabilidad` | **MEDIO** | Cada lote ejecuta `Container.search()` individual. En vistas con 100+ lotes, performance degrada. |
| `@api.model_create_multi` no usado en creación batch de lotes | **MEDIO** | `create()` en `stock_lot.py` podría beneficiarse. |
| Archivo huérfano `models/0` | **BAJA** | Artefacto de 0 bytes. |
| `ROADMAP.md` en `models/` en lugar de `WIKI/` | **BAJA** | Documentación en ubicación incorrecta. |
| Backups en repositorio activo (`backups/fase1_20260602_211431/`) | **BAJA** | Viola higiene. |
| `.bak` en módulos activos (violan AD-26) | **BAJA** | 6 archivos `.bak` en módulos activos. |
| Código comentado `# ⚠️ TEMPORAL` en `stock_lot.py:577` | **BAJA** | `processing_order_id` comentado sin resolver. |

## 3.3 Contable

| Hueco | Severidad | Evidencia |
|-------|-----------|-----------|
| Sin integración contable real (`account.move`) | **ALTA** | Fase 7 solo tiene una línea en el backlog. El sistema opera con costos en `stock.lot` pero no genera asientos contables. |
| Sin valuation layers automáticos | **ALTA** | `stock.valuation.layer` no recibe los landed costs automáticamente. El costo existe en el lote pero no en la contabilidad de inventario de Odoo. |
| `cost_per_m3_usd` y `cost_per_mbf_usd` solo suman `cost_line_ids`, excluyen `wood_cost_usd` | **MEDIA** | `_compute_cost_per_m3` (línea 1126-1134 de `stock_lot.py`) no incluye `wood_cost_usd` ni `purchase_cost_usd`. El costo por m³ reflejado es incompleto. |
| Sin cuenta contable en `stock.lot.cost.line` | **MEDIA** | El modelo de línea de costo no tiene campo `account_id` para mapear a cuentas contables. |
| Tipo de cambio manual, no integrado con Odoo rates | **BAJA** | `exchange_rate` en `stock_lot_costing.py` es un Float manual. `_get_default_exchange_rate` consulta `res.currency` pero el campo puede ser sobreescrito sin trazabilidad. |

## 3.4 UX / UI

| Hueco | Severidad | Evidencia |
|-------|-----------|-----------|
| `madenat_guia_processing` con 55+ campos en la cabecera | **MEDIA** | Abrumador para el usuario de bodega. Los campos están agrupados conceptualmente pero la vista formulario carga todo. |
| Columnas de medidas no estandarizadas entre vistas | **MEDIA** | `lumber.reception.line` usa `thickness_visual`/`width_visual`; `stock.lot` usa `espesor_inch_frac`/`ancho_inch_frac` + `thickness_visual`/`width_visual`. Dos sistemas de naming para el mismo concepto. |
| Navegación entre guía → lotes → movimientos no unificada | **MEDIA** | No hay smart buttons que crucen de `madenat.guia.processing` a `stock.picking` directamente en algunas vistas. |
| Sin panel de control de costos por guía | **BAJA** | El costo de servicio de la guía (`service_unit_price_clp`) está en la cabecera pero no hay una vista que muestre costo total por guía = servicio + costo de madera distribuido. |
| Reportes de inventario valorizado ausentes | **MEDIA** | `madenat_lumber_reports` solo remapea menús; no tiene reportes financieros de inventario valorizado por lote. |

## 3.5 Documental

| Hueco | Severidad | Evidencia |
|-------|-----------|-----------|
| Sin documento canónico de flujo de costeo end-to-end | **MEDIA** | El costeo está documentado en código y en `lumber_cost_distribution.py`, pero no existe un documento CANON que explique: dónde entra el costo, cómo se distribuye, cómo se refleja en el lote, y cómo se conecta con contabilidad. |
| Sin mapa de dependencias entre módulos | **BAJA** | `dependencias_modulos.md` existe en WIKI pero no está actualizado post-Fase 3. |
| Sin guía de troubleshooting | **BAJA** | `AUDITORIA_2026-06-03.md` y `AUDITORIA_2026-06-04.md` identifican problemas pero no hay un documento de errores conocidos y soluciones. |
| Sin documentación del flujo de devoluciones | **MEDIA** | No documentado formalmente. |
| P7_INVENTARIO_RESIDUOS no ejecutado (limpieza) | **BAJA** | El inventario está completo pero las acciones recomendadas no se han ejecutado (6 `.bak`, duplicados, snapshots). |

---

# 4. FOCO ESPECIAL: COSTEO

## 4.1 ¿Cómo funciona el costeo actual?

El sistema MADENAT tiene **tres capas de costo** implementadas en diferentes archivos:

### Capa 1: Costo de madera (en `stock.lot` — core)

```python
# stock_lot.py:649-672
purchase_price_usd_per_m3 = Float   # Precio unitario proveedor
purchase_amount_usd = volumen_m3 × purchase_price_usd_per_m3   # Monto total compra
purchase_amount_clp = purchase_amount_usd × purchase_exchange_rate

# stock_lot.py:802-804
wood_cost_usd = Float                # Costo madera USD (alternativo)
purchase_cost_usd = Float            # Costo compra USD (alternativo)

# stock_lot.py:806-824
total_cost_usd = wood_cost_usd + purchase_cost_usd + sum(cost_line_ids.amount_usd)
```

**Problema detectado**: Hay **dos campos redundantes** (`wood_cost_usd` + `purchase_cost_usd`) que representan esencialmente lo mismo (costo de la madera comprada). El `total_cost_usd` es `store=False` (calculado al vuelo) y no persiste en BD, lo cual es correcto para evitar desincronización pero impide reportes históricos.

### Capa 2: Costos adicionales por lote (`stock.lot.cost.line` — core)

```python
# stock_lot_cost_line.py
lot_id → stock.lot                    # Lote asociado
cost_type → Selection (19 opciones)   # wood, logistic, processing, freight, port, customs...
amount_usd → Float                    # Monto en USD
partner_id → res.partner              # Proveedor del servicio
date → Date                           # Fecha contable
```

**Funciona como "libreta de costos" del lote**: cualquier módulo puede inyectar líneas aquí. El módulo `madenat_lumber_costing` agrega `distribution_id` para trazabilidad del origen.

### Capa 3: Expediente de liquidación (`lumber.cost.distribution` — costing)

```python
# lumber_cost_distribution.py
target_model → booking/container/reception/purchase/manual
cost_line_ids → One2many de lumber.cost.distribution.line
  ├── cost_type → freight, ocean_freight, port, customs, processing, insurance, other
  ├── amount_usd → Monto en USD (calculado desde amount_original con exchange_rate)
  └── distribution_method → volume_export, volume_physical, weight, pieces, equal, container

action_apply_costs():
  1. Determinar base_amount (si container → multiplicar por unique_containers)
  2. Para cada lot → calcular factor según distribution_method
  3. Inyectar stock.lot.cost.line con amount_usd = base_amount × factor
```

**Funcional y bien diseñado**: El wizard de liquidación soporta múltiples bases de reparto y tiene blindaje anti-basura (filtra lotes sin `ref` o con volumen 0). Es reversible (`action_reverse_costs`).

## 4.2 ¿Dónde debería vivir el costo base?

### Diagnóstico

Actualmente el costo base de la madera vive en **dos lugares simultáneamente**:

1. `purchase_price_usd_per_m3` + `purchase_amount_usd` en `stock.lot` (core)
2. `wood_cost_usd` / `purchase_cost_usd` también en `stock.lot` (core, campos legacy)

Y el costo de servicio de la guía vive en:
3. `service_unit_price_clp` en `madenat.guia.processing` (cabecera de guía)
4. `additional_cost` en `madenat.guia.processing` (campo genérico)

**Esto crea fragmentación**: el costo total real de un lote requiere sumar campos de 3 fuentes distintas (lote + líneas de costo + cabecera de guía), y el cálculo no está unificado.

### Recomendación arquitectónica

El costo base de la madera debe vivir **exclusivamente** en `stock.lot.cost.line` como una línea con `cost_type='wood'`, inyectada automáticamente al momento de la recepción desde `purchase_price_usd_per_m3 × volumen_m3`. Esto:

- Unifica la fuente de verdad de costos en un solo lugar (`cost_line_ids`)
- Hace que `total_cost_usd` sea simplemente `sum(cost_line_ids.amount_usd)` sin necesitar campos separados
- Permite que `cost_per_m3_usd` y `cost_per_mbf_usd` reflejen el costo completo (actualmente excluyen `wood_cost_usd`)
- Simplifica el modelo de datos (se pueden deprecar `wood_cost_usd`, `purchase_cost_usd`, `purchase_amount_usd` como campos de costo)

## 4.3 ¿Se debe usar landed cost de Odoo, costo de servicio, o propio?

### Análisis

| Enfoque | Pros | Contras | Veredicto |
|---------|------|---------|-----------|
| **Landed Cost de Odoo** (`stock.landed.cost`) | Integración nativa con valuation layers y account.move. Cumple OCA. | Diseñado para pickings individuales, no para distribuciones masivas por booking/contenedor. No soporta distribución por MBF. Requiere reimplementar el wizard de Felipe. | **NO recomendado como reemplazo total** |
| **Costo de servicio** (`madenat.guia.processing.service_unit_price_clp`) | Captura el costo real del servicio externo. | Solo aplica a guías de procesamiento, no a recepciones de compra directa. No se conecta con contabilidad. | **Mantener como entrada de datos, no como destino final** |
| **Sistema propio actual** (`lumber.cost.distribution` + `stock.lot.cost.line`) | Diseñado exactamente para el negocio MADENAT. Soporta booking/container/recepción. 6 métodos de prorrateo. Reversible. Blindaje anti-basura. | No genera valuation layers ni account.move. Los costos quedan "informativos" en el lote sin impacto contable. | **Mantener como núcleo de distribución, extender para integración contable** |

### Recomendación

**Estrategia híbrida**:

1. **Mantener** `lumber.cost.distribution` como la interfaz de usuario para liquidación de costos (donde Felipe y equipo operan)
2. **Mantener** `stock.lot.cost.line` como el repositorio canónico de costos por lote
3. **Extender** `action_apply_costs()` para que, además de inyectar `stock.lot.cost.line`, genere automáticamente un `stock.landed.cost` de Odoo con sus `stock.valuation.layer` correspondientes, tomando como base el picking asociado a cada lote
4. **Migrar** `fields.Float` → `fields.Monetary` con `currency_id` en todos los modelos de costo
5. **Agregar** `account_id` a `stock.lot.cost.line` para mapeo contable automático

Esto preserva la lógica de negocio de MADENAT (distribución por booking/contenedor, factores de prorrateo específicos) mientras se cierra la brecha contable con Odoo estándar.

## 4.4 ¿Cómo se distribuye el costo entre los lotes?

El sistema actual soporta 6 métodos (implementados en `lumber_cost_distribution.py:138-215`):

| Método | Base | Fórmula | Uso típico |
|--------|------|---------|------------|
| `volume_export` | `vol_shipment_m3` | `lote.vol_shipment_m3 / total_export` | Flete marítimo, THC |
| `volume_physical` | `volumen_m3` | `lote.volumen_m3 / total_fisico` | Costos de compra |
| `weight` | `peso_neto` | `lote.peso_neto / total_peso` | Transporte terrestre |
| `pieces` | `piezas` | `lote.piezas / total_piezas` | Costos por pieza |
| `equal` | — | `1 / n_lotes` | Costos fijos administrativos |
| `container` | `vol_shipment_m3` × n_containers | Multiplica costo × contenedores, luego prorratea por m³ | Fletes por contenedor |

**Correcto para el negocio**: El costo de servicio de la guía (`service_unit_price_clp`) actualmente se distribuye en `_assign_costs_to_generated_lots()` (línea 2596 de `madenat_guia_processing.py`) pero este método no está documentado en detalle en CANON.

## 4.5 ¿Cómo se refleja en valuation layers y contabilidad?

**Actualmente NO se refleja**. El costo vive en:
- `stock.lot.total_cost_usd` (compute, no store)
- `stock.lot.cost_line_ids` (líneas de costo)

Pero **no existe**:
- `stock.valuation.layer` con el costo actualizado
- `account.move` con el asiento de ajuste de inventario
- `stock.quant` con costo unitario actualizado

Esto significa que:
- El **inventario valorizado** de Odoo (`stock.valuation.layer`) muestra solo el costo de compra original, no el costo landed completo
- Los **reportes financieros** estándar de Odoo no reflejan el costo real
- El **margen** calculado en `stock.lot` (`margin_usd`, `margin_percent`) es correcto pero **no contable**

## 4.6 ¿Qué falta para costo real confiable por lote y por guía?

| Ítem | Estado | Acción |
|------|--------|--------|
| Costo de madera unificado en `cost_line_ids` | ❌ | Migrar `wood_cost_usd` a línea `cost_type='wood'` automática |
| `cost_per_m3_usd` incluyendo wood_cost | ❌ | Modificar `_compute_cost_per_m3` para sumar wood_cost de `cost_line_ids` con `cost_type='wood'` |
| Integración con `stock.landed.cost` | ❌ | Extender `action_apply_costs()` para generar landed costs de Odoo |
| `fields.Monetary` en todos los campos de costo | ❌ | Migración completa (~6 horas) |
| `account_id` en `stock.lot.cost.line` | ❌ | Agregar campo Many2one → `account.account` |
| Documento canónico de flujo de costeo | ❌ | Crear `CANON/08_COSTEO.md` |
| Trazabilidad de ajustes de costo | ✅ | `distribution_id` en `stock.lot.cost.line` ya existe |

---

# 5. TRAZABILIDAD

## 5.1 Diagnóstico

La trazabilidad actual es **robusta a nivel de lote individual pero parcial a nivel de flujo completo**:

| Trazabilidad | Estado | Evidencia |
|-------------|--------|-----------|
| Guía → Lotes | ✅ Completa | `reception_id` / `guia_processing_id` en `stock.lot`. Mutuamente excluyentes. |
| Lotes → Movimientos | ✅ Completa | `stock.move` / `stock.move.line` con `lot_id`. |
| Movimientos → Pickings | ✅ Completa | `stock.picking` con `move_ids` y `move_line_ids`. |
| Pickings → Quants | ✅ Completa | `stock.quant` con `lot_id` como related. |
| Quants → Ubicación | ✅ Completa | `location_id` en `stock.quant`. |
| Lote → Padre/Hijo | ✅ Completa | `parent_lot_id` + `child_lot_ids` + `generation_level`. |
| Guía → Costos | ✅ Completa | `stock.lot.cost.line` con `distribution_id`. |
| Guía → Contenedor → Embarque | ✅ Parcial | `container_id` → `shipment_id` en `stock.lot` (costing), pero no en core. |
| Devoluciones | ⚠️ Parcial | No hay documento canónico. El picking de devolución existe en Odoo pero no está mapeado en la trazabilidad MADENAT. |
| Historial de cambios de estado | ✅ Completa | `tracking=True` en campos de estado, `mail.thread` en modelos principales. |
| Trazabilidad financiera (costos → contabilidad) | ❌ Inexistente | Sin `account.move` generado. |
| Trazabilidad de auditoría (snapshot SHA-256) | ✅ Completa | `audit_snapshot` + `audit_hash` en líneas de staging. |

## 5.2 ¿Se puede reconstruir el ciclo real de cada guía desde BD?

**Sí**, con las siguientes queries (no ejecutadas — Docker no disponible):

```sql
-- Desde guía → lotes
SELECT l.name, l.ref, l.volumen_m3, l.vol_shipment_m3, l.estado_trazabilidad
FROM stock_lot l
WHERE l.reception_id = <reception_id> OR l.guia_processing_id = <guia_id>;

-- Desde lote → picking → ubicación
SELECT sm.name, sm.state, sp.name AS picking, sl.complete_name AS location
FROM stock_move_line sml
JOIN stock_move sm ON sml.move_id = sm.id
JOIN stock_picking sp ON sm.picking_id = sp.id
JOIN stock_location sl ON sml.location_dest_id = sl.id
WHERE sml.lot_id = <lot_id>;

-- Desde lote → costos
SELECT scl.name, scl.cost_type, scl.amount_usd, lcd.name AS expediente
FROM stock_lot_cost_line scl
LEFT JOIN lumber_cost_distribution lcd ON scl.distribution_id = lcd.id
WHERE scl.lot_id = <lot_id>;
```

## 5.3 Smart buttons, reportes y vistas faltantes

| Elemento | Estado | Prioridad |
|----------|--------|-----------|
| Smart button: Guía → Lotes | ✅ Existe (`lot_ids` Many2many) | — |
| Smart button: Lote → Guía | ✅ Existe (`reception_id` / `guia_processing_id`) | — |
| Smart button: Guía → Picking | ⚠️ No verificado | MEDIA |
| Smart button: Guía → Costos | ❌ No existe | ALTA |
| Smart button: Lote → Contenedor | ✅ Existe (`container_id`) | — |
| Reporte: Inventario valorizado por lote | ❌ No existe | ALTA |
| Reporte: Costo por guía | ❌ No existe | ALTA |
| Reporte: Trazabilidad completa (guía → lote → picking → contenedor → embarque → costo) | ❌ No existe | MEDIA |
| Vista: Panel de costo de guía (servicio + costos distribuidos) | ❌ No existe | MEDIA |

---

# 6. INVENTARIO Y ALMACENES

## 6.1 Estructura actual

El sistema utiliza la infraestructura estándar de Odoo para inventario:

- `stock.location`: ubicaciones (PATIO, ALMACÉN SECO, etc.)
- `stock.picking` + `stock.move` + `stock.move.line`: movimientos
- `stock.quant`: cantidades por ubicación
- `stock.lot`: trazabilidad por lote

Con extensiones MADENAT:
- `stock.quant` extendido con `reception_name`, `supplier_id`, `subproducto_id`, `volumen_sistema_m3` (related a `quantity`)
- `stock.move` extendido (ver `stock_move.py`)
- `stock.picking` extendido (ver `stock_picking.py`)

## 6.2 Lo que está bien modelado

- ✅ **Picking unificado por guía**: `_get_or_create_picking_unified` garantiza 1 guía = 1 albarán, sin duplicados
- ✅ **Backorder**: `button_validate` con manejo de wizard de backorder
- ✅ **Cancelación segura**: `action_force_cancel` con escudos logístico (contenedores activos) y financiero (costos comprometidos)
- ✅ **Autorreparación**: productos consumibles forzados a almacenables en `action_validate`

## 6.3 Lo que depende de ajustes manuales

- ⚠️ **Stock negativo**: sin protección explícita para evitar stock negativo en lotes (depende de la configuración de Odoo)
- ⚠️ **Reservas**: sin lógica de reserva específica para madera (depende de Odoo estándar)
- ⚠️ **Valorización**: sin `stock.valuation.layer` actualizado con landed costs → valorización manual

## 6.4 Automatizaciones faltantes

- ❌ **Ajuste automático de valorización**: al aplicar landed costs, no se actualiza `stock.valuation.layer`
- ❌ **Recepción sin staging**: no hay modo rápido para recepción directa sin pasar por staging (útil para operaciones simples)
- ❌ **Alerta de stock bajo**: sin notificaciones automáticas de stock bajo por subproducto
- ❌ **Conciliación de inventario**: sin wizard de conciliación entre `stock.quant` y volúmenes MADENAT

---

# 7. RIESGOS ESTRUCTURALES PENDIENTES

| Riesgo | Severidad | Estado | Plan de mitigación |
|--------|-----------|--------|-------------------|
| `stock_lot_check_cost_positive` constraint | **ALTA** | ABIERTO | Investigar si `total_cost_usd` (store=False) o `cost_line_ids` puede violar la constraint. La constraint fue definida cuando `total_cost_usd` era store=True. |
| `fields.Float` para dinero | **CRÍTICO** | ABIERTO | Migración a `fields.Monetary` en todos los modelos de costo (~6 horas) |
| Sin tests en `madenat_guia_processing` | **ALTA** | ABIERTO | Crear `test_guia_processing.py` con 12 casos mínimos (TD-008) |
| Campos duplicados en guía | **ALTA** | ABIERTO | TD-007: limpiar definiciones shadowed |
| Sin integración contable | **ALTA** | ABIERTO | Fase 7: diseño de integración con `account.move` |
| `sudo()` en deletes | **ALTO** | ABIERTO | Unificar en helper con permisos explícitos |
| Monolito parcial en `lumber_reception.py` | **MEDIO** | ABIERTO | Fase 4: separar `LumberReceptionLine` a archivo propio |
| N+1 queries en trazabilidad | **MEDIO** | ABIERTO | Batch query en `_compute_estado_trazabilidad` |
| Sin documento de flujo de costeo | **MEDIO** | ABIERTO | Crear `CANON/08_COSTEO.md` |
| Hardcodes `25.4` huérfanos | **CRÍTICO** | ABIERTO | Acción 6 y 7 de auditoría 06-03 |
| Sin política de retención documental | **BAJA** | PROPUESTA | RET-DOC-001 en P7_INVENTARIO_RESIDUOS |

---

# 8. HOJA DE RUTA PRIORIZADA

## FASE A — Base contable y costeo (Prioridad 0)
**Objetivo**: Que el costo en `stock.lot` sea contablemente útil y auditable

1. **A.1** Migrar `fields.Float` → `fields.Monetary` en todos los campos de costo (stock_lot, costing, billing, purchasing)
2. **A.2** Unificar costo base de madera como `cost_line` con `cost_type='wood'` automática
3. **A.3** Corregir `cost_per_m3_usd` y `cost_per_mbf_usd` para incluir `wood_cost_usd`
4. **A.4** Agregar `account_id` a `stock.lot.cost.line`
5. **A.5** Extender `action_apply_costs()` para generar `stock.landed.cost` y `stock.valuation.layer`
6. **A.6** Crear `CANON/08_COSTEO.md` — documento canónico de flujo de costeo end-to-end

**Esfuerzo estimado**: 12-16 horas

## FASE B — Trazabilidad robusta (Prioridad 1)
**Objetivo**: Cobertura total de tests y eliminación de deuda técnica estructural

7. **B.1** Crear `test_guia_processing.py` con 12 casos mínimos (TD-008)
8. **B.2** Limpiar campos duplicados en `MadenatGuiaProcessing` (TD-007)
9. **B.3** Unificar delete de stock moves en un solo helper sin `sudo()` (Acción 9 + 22)
10. **B.4** Migrar `LUMBER_DIMENSION_MAP` a modelos Fase 2 (TD-009)
11. **B.5** Unificar parseo Excel/PDF en `MadenatReceptionParser` (TD-010)

**Esfuerzo estimado**: 10-14 horas

## FASE C — Limpieza operativa (Prioridad 2)
**Objetivo**: Eliminar riesgo de inconsistencias y facilitar mantenimiento

12. **C.1** Corregir hardcodes `25.4` en `lumber_shipment_line.py`, `lumber_reception_mass_update.py` y `utils_uom.py` (Acciones 5, 6, 7)
13. **C.2** Resolver constraint `stock_lot_check_cost_positive`
14. **C.3** Optimizar `_compute_estado_trazabilidad` con batch query (Acción 19)
15. **C.4** Limpiar backups, `.bak`, archivo huérfano `models/0` (Acciones 1, 13, 14, 15)
16. **C.5** Ejecutar limpieza documental P7 (duplicados, snapshots)

**Esfuerzo estimado**: 6-8 horas

## FASE D — UX y reportes (Prioridad 3)
**Objetivo**: Que el sistema sea operable por bodega y traders sin fricción

17. **D.1** Agregar smart buttons: Guía → Costos, Guía → Picking
18. **D.2** Crear vista de panel de costo por guía (servicio + costos distribuidos)
19. **D.3** Crear reporte de inventario valorizado por lote
20. **D.4** Estandarizar naming de columnas de medidas entre vistas
21. **D.5** Simplificar vista formulario de `madenat.guia.processing`

**Esfuerzo estimado**: 8-12 horas

## FASE E — Integración contable completa (Prioridad 4)
**Objetivo**: Que el sistema genere `account.move` automáticamente

22. **E.1** Diseñar mapping: `cost_type` → `account.account`
23. **E.2** Implementar generación de `account.move` al aplicar costos
24. **E.3** Implementar reversión contable en `action_reverse_costs`
25. **E.4** Validar con contabilidad (balances, IVA, retenciones)

**Esfuerzo estimado**: 16-24 horas (depende de requisitos contables Chile)

## FASE F — Documentación consolidada (Prioridad 5)
**Objetivo**: Eliminar dependencia de memoria tribal

26. **F.1** Crear `CANON/08_COSTEO.md`
27. **F.2** Crear `WIKI/02_TECNICO/flujo_devoluciones.md`
28. **F.3** Actualizar `dependencias_modulos.md` post-Fase 3
29. **F.4** Crear `WIKI/02_TECNICO/troubleshooting.md` con errores conocidos y soluciones
30. **F.5** Mover `ROADMAP.md` de `models/` a `CANON/`

**Esfuerzo estimado**: 4-6 horas

---

# 9. RECOMENDACIÓN FINAL PRIORIZADA

## Orden de ejecución recomendado

```
SEMANA 1-2:  FASE A (Base contable y costeo) → crítico, sin esto el sistema no es contablemente útil
SEMANA 3:    FASE C (Limpieza operativa) → eliminar riesgos estructurales que bloquean producción
SEMANA 4-5:  FASE B (Trazabilidad robusta) → tests + deuda técnica, habilita refactors seguros
SEMANA 6-7:  FASE D (UX y reportes) → usabilidad para operadores reales
SEMANA 8:    FASE F (Documentación) → consolidación para onboarding
MES 3+:      FASE E (Integración contable) → requiere diseño detallado con contabilidad
```

## Principios rectores

1. **No tocar fórmulas matemáticas** sin auditoría formal (AD-30, regla derivada)
2. **No romper la regla de exclusividad** `reception_id` XOR `guia_processing_id`
3. **No eliminar trazabilidad** — toda migración de datos debe preservar el historial
4. **No introducir `import` entre addons** sin pasar por `madenat_lumber_utils` (HF-001 / AD-07)
5. **Documentar antes de codificar** cuando el cambio afecte arquitectura, cálculo o flujo financiero (AD-25)
6. **Mantener cadena de fallback** en toda parametrización nueva (Fase 2, AD-29)

## Nivel de confianza del sistema actual

| Área | Confianza | Nota |
|------|-----------|------|
| Ingesta y staging | **ALTA** | Funcional, validado, con tolerancia a errores |
| Cálculo volumétrico | **ALTA** | Preciso, dual (compra/embarque), reglas correctas post-AD-27 |
| Creación de lotes | **ALTA** | Unicidad, genealogía, trazabilidad de origen |
| Flujo de pickings | **MEDIA-ALTA** | Motor unificado funcional, cancelación segura, sin tests |
| Costeo operativo | **MEDIA** | Distribución funcional, sin integración contable |
| Costeo contable | **BAJA** | Sin valuation layers, sin account.move, sin fields.Monetary |
| UX operativa | **MEDIA** | Funcional pero abrumadora para bodega, naming inconsistente |
| Documentación | **ALTA** | CANON completo y actualizado, WIKI detallada, auditorías recientes |
| Cobertura de tests | **BAJA** | Solo `lumber.reception` tiene tests; `guia.processing` = 0 tests |

---

# 10. EVIDENCIA DOCUMENTAL CONSULTADA

| Documento | Líneas | Fecha | Aporte al análisis |
|-----------|--------|-------|-------------------|
| `CANON/00_ARQUITECTURA.md` | 165 | 2026-05-28 | Arquitectura de módulos, gates, modelos principales |
| `CANON/02_CONTINUIDAD.md` | 63 | 2026-06-02 | Estado actual, riesgos, punto de retoma |
| `CANON/04_DECISION_LOG.md` | 749 | 2026-06-02 | 30+ decisiones técnicas, bugs, hotfixes, reglas derivadas |
| `CANON/05_BACKLOG.md` | 75 | 2026-05-23 | Fases pendientes, riesgos, criterios de salida |
| `stock_lot.py` | 1392 | 2024-12-04 | Modelo completo de lotes con 18 secciones |
| `stock_lot_cost_line.py` | 84 | — | Modelo canónico de línea de costo |
| `lumber_cost_distribution.py` | 315 | — | Motor de prorrateo de landed costs |
| `stock_lot_costing.py` | 196 | — | Extensión de costing en lote |
| `lumber_reception.py` | 2573 | — | Recepción de madera bruta con staging |
| `AUDITORIA_2026-06-03.md` | 267 | 2026-06-03 | 23 hallazgos, 3 críticos, matriz de prioridades |
| `AUDITORIA_2026-06-04.md` | 318 | 2026-06-04 | Auditoría profunda de `madenat_guia_processing` |
| `P7_INVENTARIO_RESIDUOS.md` | 316 | 2026-06-02 | Inventario de residuos documentales y .bak |
| `WIKI/02_TECNICO/modelo_lotes.md` | 299 | 2026-06-02 | Documentación detallada del modelo stock.lot |
| `INDICE_DOCUMENTACION.md` | 59 | 2026-06-02 | Mapa maestro de documentación canónica |
| `madenat_lumber_costing/__manifest__.py` | 35 | — | Declaración de dependencias del módulo costing |

---

*Informe generado el 2026-06-04. Basado en evidencia de código, documentación canónica y auditorías técnicas.*  
*Cero modificaciones de código durante este análisis.*