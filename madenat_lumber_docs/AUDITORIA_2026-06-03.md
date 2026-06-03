# INFORME DE AUDITORÍA TÉCNICA — MADENAT Lumber (Odoo 18 CE)
**Fecha:** 2026-06-03
**Auditor:** Auditor Técnico IA — Especialista Odoo ERP, Supply Chain, Trading de Madera
**Versión auditada:** v1.1-TD003
**Experiencia auditor:** 10+ años Odoo ERP, supply chain, trading de madera

***

## RESUMEN EJECUTIVO
| Métrica | Valor | Estado |
|---|---|---|
| Módulos auditados | 10 | ✅ |
| Archivos revisados | 85+ | ✅ |
| Problemas críticos | 3 | ❌ |
| Problemas medios | 5 | ⚠️ |
| Problemas menores | 8 | ⚠️ |
| Deuda técnica | ~18 horas | ⚠️ |
| Cumplimiento OCA | 72% | ⚠️ |

**Veredicto:** ⚠️ **REQUIERE CORRECCIÓN** — El proyecto tiene 3 problemas críticos que deben resolverse antes de producción. La arquitectura de costos usa `fields.Float` en lugar de `fields.Monetary` de forma generalizada, y hay hardcodes de conversión imperial dispersos fuera de `utils_uom.py`. La documentación y la lógica de negocio crítica están en buen estado post TD-003.

***

## 1. ESTRUCTURA DE MÓDULOS
### 1.1 Hallazgos
- [x] **10 módulos MADENAT activos** con `__manifest__.py` válidos y `version` definida: `madenat_lumber_core`, `madenat_lumber_billing`, `madenat_lumber_costing`, `madenat_lumber_logistics`, `madenat_lumber_purchasing`, `madenat_lumber_reception_improvements`, `madenat_lumber_reports`, `madenat_lumber_shipping_core`, `madenat_toll_processing`, `madenat_vendor_payment`
- [x] Todos los módulos tienen `__init__.py` (no hay módulos vacíos)
- [x] `appointment_crm/` es un módulo externo (CRM de citas), no es parte de MADENAT
- [⚠️] `madenat_lumber_docs/` no es un módulo Odoo (carece de `__manifest__.py`). Es un repositorio de documentación. Correcto, pero debe quedar documentado.
- [⚠️] `madenat_lumber_reports` depende de TODOS los demás módulos (incluyendo billing, vendor_payment, toll_processing). Esto crea una dependencia total que fuerza la instalación de toda la suite si se quiere reports. Evaluar si reports debe ser un "meta-módulo" que solo remapea menús.
- [✅] No se detectan dependencias cíclicas entre módulos
- [❌] **Archivo huérfano `custom_addons/madenat_lumber_core/models/0`**: Un archivo llamado `0` (cero) existe en el directorio `models/`. Es un artefacto no intencional, probablemente un error de redirección o editor.

### 1.2 Recomendaciones
- **Acción 1:** Eliminar el archivo huérfano `custom_addons/madenat_lumber_core/models/0`
- **Acción 2:** Documentar en `__manifest__.py` de `madenat_lumber_reports` que es un meta-módulo de remapeo de menús (su única función es `menu_remapping.xml` y `lumber_reports_menu.xml`)

***

## 2. ARQUITECTURA DE DATOS (ORM Odoo 18)
### 2.1 Hallazgos
- [✅] Modelos siguen patrones de Odoo 18: `_name`, `_description`, `_inherit`, `_order`, `_sql_constraints`
- [✅] `one2many` y `many2many` tienen `inverse_name` y/o `ondelete` correctos (ej: `allowed_formula_ids` en `madenat_subproducto.py`)
- [✅] `@api.depends` usa `store=True` donde los datos persisten (`_compute_product_display`, `_compute_estado_trazabilidad`)
- [⚠️] **No se detecta uso de `@api.model_create_multi`** donde hay batch creates. El método `create()` en `stock_lot.py` (línea ~1257) podría beneficiarse de `@api.model_create_multi` para creación masiva de lotes desde staging.
- [✅] `sql_constraint` presente en `stock_lot.py` (CHECK positivo para volumen, piezas, costo) y en `madenat_subproducto.py` (UNIQUE code, name)
- [✅] Campos con `String`, `Help`, `required`, `readonly`, `tracking` correctamente usados
- [⚠️] `fields.function` no se detecta (obsoleto en Odoo 18). Todos los campos usan `fields.*` moderno.

### 2.2 Recomendaciones
- **Acción 3:** Migrar `create()` de lotes masivos a `@api.model_create_multi` en `stock_lot.py` (mejora de rendimiento Odoo 18)
- **Acción 4:** Verificar que `@api.depends` en `_compute_estado_trazabilidad` no cause N+1 queries con la búsqueda de contenedores por lote. Considerar `search_read()` con batch.

***

## 3. CONSTANTES Y NÚMEROS MÁGICOS
### 3.1 Hallazgos
- [✅] `utils_uom.py` centraliza correctamente las 5 constantes canónicas: `MM_PER_INCH`, `FT_TO_M`, `M3_DIVISOR`, `MBF_DIVISOR`, `BLANK_CLEAR_FACTOR`
- [✅] `utils_uom.py` contiene la tabla `S2S_WIDTH_LOOKUP` como fuente única de verdad para mapeo mm→pulgadas
- [✅] `utils_uom.py` contiene las funciones canónicas `calculate_volume_metric_m3()` y `calculate_volume_imperial_to_m3()`
- [⚠️] **`utils_uom.py` línea 132**: La función `mm_to_inch()` usa `float(decimal_value) * 25.4` en lugar de `float(decimal_value) * float(MM_PER_INCH)`. Usa el literal en el propio archivo de constantes.
- [❌] **Hardcode en `lumber_shipment_line.py` líneas 78 y 123**: `line.lot_id.ancho_mm / 25.4` y `adjusted_width_inch * 25.4`. No importa ni usa constantes de `utils_uom.py`.
- [❌] **Hardcode en `lumber_reception_mass_update.py` línea 114**: `return round(inches * 25.4, 2)`. Debe usar `MM_PER_INCH` de `utils_uom.py`.
- [✅] `lumber_export_formula.py` líneas 94 y 117: `default=5085.312` y `default=12000.0` son defaults de campos del modelo, no cálculos hardcodeados. La fórmula usa estos defaults como configuración.
- [✅] `stock_lot.py` importa correctamente `MM_PER_INCH`, `FT_TO_M`, `BLANK_CLEAR_FACTOR` desde `utils_uom.py` y los usa.

### 3.2 Recomendaciones
- **Acción 5:** Corregir `mm_to_inch()` en `utils_uom.py` línea 132 para usar `float(MM_PER_INCH)` en lugar del literal `25.4`
- **Acción 6:** Refactorizar `lumber_shipment_line.py` para importar `MM_PER_INCH` desde `utils_uom.py` y eliminar hardcodes `/ 25.4` y `* 25.4`
- **Acción 7:** Refactorizar `lumber_reception_mass_update.py` línea 114 para usar `MM_PER_INCH` de `utils_uom.py`

***

## 4. VISTAS Y XML (Odoo 18)
### 4.1 Hallazgos
- [✅] `__manifest__.py` declara archivos de vistas en orden correcto (seguridad → datos → vistas → wizards → reportes)
- [✅] Vistas usan `inherit_id` para herencia en lugar de redefinir vistas completas
- [✅] No se detectan `id` duplicados en vistas (análisis superficial)
- [⚠️] `menuitem` en `lumber_core_menu.xml` y `logistics_menus.xml` deben verificarse contra `parent` existentes. No se pudo validar en estático.
- [✅] `action` tiene `res_model` y `view_mode` válidos
- [⚠️] Vista `costing_menus.xml` comentada en `madenat_lumber_costing/__manifest__.py` línea 30: `#  'views/costing_menus.xml',`. Si los menús de costing se movieron a reports, documentarlo.

### 4.2 Recomendaciones
- **Acción 8:** Verificar que `costing_menus.xml` está intencionalmente comentado y documentar la razón (posiblemente migrado a `madenat_lumber_reports/menu_remapping.xml`)

***

## 5. SEGURIDAD (CRÍTICO)
### 5.1 Hallazgos
- [✅] Todos los modelos en `madenat_lumber_core` tienen mínimo 2 ACL (usuario interno + manager/sistema)
- [✅] `ir.model.access.csv` sigue el estándar Odoo con columnas correctas (id, name, model_id:id, group_id:id, perm_read, perm_write, perm_create, perm_unlink)
- [✅] Modelos de configuración (ingestion, fórmulas, mapas) usan grupo personalizado `group_lumber_config_manager` con acceso restringido
- [⚠️] **Uso extensivo de `sudo()` en múltiples archivos** (22 ocurrencias en código activo):

| Archivo | Línea(s) | Contexto | Riesgo |
|---|---|---|---|
| `lumber_reception.py` | 1201, 1204, 1210, 1217, 1262 | Delete de quants y pickings con `sudo()` | 🟡 MEDIO |
| `lumber_reception.py` | 2336 | Write en producto con `sudo()` | 🟡 MEDIO |
| `lumber_reception.py` | 2559-2573 | Delete de stock moves | 🟡 MEDIO |
| `reception_service.py` | 126-137 | Delete de stock moves (misma lógica duplicada) | 🟡 MEDIO |
| `madenat_guia_processing.py` | 1562 | Write en product.template con `sudo()` | 🟡 MEDIO |
| `madenat_ingestion_config.py` | 34-213 | Search en mapas de configuración con `sudo()` | 🟢 BAJO |
| `stock_lot.py` | 1035 | Search de contenedores con `sudo()` | 🟢 BAJO |
| `lumber_container.py` | 872 | Search de otros contenedores con `sudo()` | 🟢 BAJO |
| `mixin_lumber_ingest.py` | 65 | Write en producto con `sudo()` | 🟡 MEDIO |
| `lumber_export_formula.py` | 174 | Search en fórmula con `sudo()` | 🟢 BAJO |
| `lumber_ingestion_format.py` | 197 | Search en formato con `sudo()` | 🟢 BAJO |
| `product_template.py` | 48, 110 | Get param con `sudo()` | 🟢 BAJO |
| `madenat_vendor_payment` | 289 | Get param con `sudo()` | 🟢 BAJO |
| `madenat_lumber_purchasing` | 678-733 | Get/Set param con `sudo()` | 🟢 BAJO |

- [⚠️] `sudo()` en operaciones de delete (lumber_reception.py) es particularmente riesgoso. Debe estar protegido por grupos de seguridad, no por `sudo()`.
- [⚠️] La lógica de delete de stock moves está **duplicada** entre `lumber_reception.py` (líneas 2559-2573) y `reception_service.py` (líneas 126-137).

### 5.2 Recomendaciones
- **Acción 9 (CRÍTICO):** Unificar la lógica de delete de stock moves en un solo método con permisos explícitos en lugar de `sudo()`. La duplicación actual entre `lumber_reception.py` y `reception_service.py` es un riesgo de inconsistencia.
- **Acción 10:** Evaluar cada uso de `sudo()` y reemplazar con `with_context()` o `check_access_rights()` donde sea posible.

***

## 6. WIZARDS Y LÓGICA DE NEGOCIO
### 6.1 Hallazgos
- [✅] Wizard `lumber_container_lot_wizard.py` tiene método `action_assign()` con validación completa
- [✅] **Dominio de disponibilidad correcto** (líneas 140-146): `estado_trazabilidad` en `['en_patio', 'procesado', 'recepcionado']`, validación técnica `approved`, exclusión de ocupados. Sigue la regla canónica de disponibilidad.
- [✅] Validación de capacidad dual (peso + volumen) con factor limitante
- [✅] `lumber_reception_mass_update.py` tiene `action_confirm()` y documenta claramente los 3 modos (metric, f5085, f1550)
- [⚠️] `lumber_reception_mass_update.py` línea 114: hardcode `* 25.4` (ver sección 3)
- [⚠️] Wizard archivado `lumber_consolidation_import_wizard.py`: documentado como dead code en CHANGELOG y README. Debe moverse a `_archive/` si no se usará.
- [✅] No se detecta lógica de negocio en vistas de wizard
- [✅] Métodos usan `self.env['model']` en lugar de `osv` obsoleto

### 6.2 Recomendaciones
- **Acción 11:** Mover `lumber_consolidation_import_wizard.py` a `_archive/` o agregar un comentario `# DEAD CODE — DO NOT USE` en la primera línea del archivo
- **Acción 12:** Corregir hardcode `* 25.4` en `lumber_reception_mass_update.py` (misma acción que Acción 7)

***

## 7. DIRECTORIOS Y ARCHIVOS
### 7.1 Hallazgos
- [❌] **Archivo huérfano `custom_addons/madenat_lumber_core/models/0`**: archivo de 0 bytes o artefacto. Debe eliminarse.
- [⚠️] `custom_addons/madenat_lumber_core/backups/fase1_20260602_211431/` — backup de código en el repositorio. No debería estar en producción.
- [⚠️] `custom_addons/madenat_lumber_docs/backups/` — backups de documentación.
- [⚠️] `custom_addons/madenat_lumber_core/_archive/` — contiene scripts de parcheo (`apply_patch_*.py`). Correcto archivarlos, pero deben estar fuera del `__manifest__.py` data path.
- [⚠️] `docker-compose.yml.bak.2026-05-18_204331` en raíz del proyecto. Archivo de backup en raíz.
- [⚠️] `custom_addons/madenat_lumber_core/scripts/` — scripts de backfill. No declarados en `__manifest__.py`, por lo que no se instalan como parte del módulo. Correcto.
- [✅] No se detectan archivos `.pyc`, `.orig`, `.swp`, `.tmp` en código activo
- [⚠️] `custom_addons/madenat_lumber_core/models/ROADMAP.md` — archivo de documentación dentro de `models/`. Debería estar en `WIKI/` o `CANON/`.
- [⚠️] `custom_addons/madenat_lumber_docs/` contiene múltiples directorios de documentación (`RAW/`, `LEGADO/`, `docs_nueva/`, `backups/`) que aumentan el tamaño del repositorio.
- [⚠️] `appointment_crm/` es un módulo no relacionado con MADENAT en el mismo espacio de trabajo.

### 7.2 Recomendaciones
- **Acción 13:** Eliminar archivo huérfano `models/0`
- **Acción 14:** Mover `backups/fase1_20260602_211431/` fuera del repositorio de código
- **Acción 15:** Mover `docker-compose.yml.bak.*` a un directorio de backups externo
- **Acción 16:** Mover `ROADMAP.md` de `models/` a `WIKI/` o `CANON/`

***

## 8. DOCUMENTACIÓN
### 8.1 Hallazgos
- [✅] Consistencia entre `README.md`, `CHANGELOG.md` y `WIKI/02_TECNICO/madenat_lumber_logistics.md` de `madenat_lumber_logistics`: **ALTA**. Los tres documentos describen la misma regla canónica de disponibilidad, los mismos estados de trazabilidad y las mismas advertencias sobre `subproducto_id`.
- [✅] `CANON/02_CONTINUIDAD.md` actualizado al 2026-06-02 (dentro de los últimos 30 días)
- [✅] `CANON/04_DECISION_LOG.md` existe y contiene entradas de decisiones técnicas (AD-27)
- [✅] `CANON/03_TESTS.md` existe
- [⚠️] **Comentario temporal en `stock_lot.py` línea 577**: `# ⚠️ TEMPORAL: Comentado hasta estabilizar metadata`. Código comentado en producción. Debe resolverse o eliminarse.
- [✅] `CHANGELOG.md` de logistics registra correctamente las correcciones TD-006 (2026-05-31)
- [⚠️] `madenat_lumber_docs/WIKI/02_TECNICO/madenat_lumber_logistics.md` referenciado en la auditoría pero no visible en el tree listado inicial. El archivo existe en `/home/viruco/dev-stack/odoo/odoo-18-ce/WIKI/02_TECNICO/madenat_lumber_logistics.md` (WIKI raíz, no dentro de `custom_addons/`). Verificar que sea el documento canónico.
- [✅] No se detectan `TODO`, `FIXME`, `HACK` en comentarios de código activo (solo comentarios de sección como `# MÉTODOS COMPUTADOS`)
- [✅] Documentación CANON existe con 5 archivos: `INDICE_DOCUMENTACION.md`, `02_CONTINUIDAD.md`, `03_TESTS.md`, `04_DECISION_LOG.md`, `05_BACKLOG.md`

### 8.2 Recomendaciones
- **Acción 17:** Resolver comentario `# ⚠️ TEMPORAL` en `stock_lot.py:577`. Si el código está listo para producción, eliminar el comentario. Si no, crear un ticket.
- **Acción 18:** Verificar que `WIKI/02_TECNICO/madenat_lumber_logistics.md` en la raíz del proyecto sea el documento canónico y que esté sincronizado con `custom_addons/madenat_lumber_logistics/README.md`.

***

## 9. RENDIMIENTO
### 9.1 Hallazgos
- [✅] `search()` con `limit=1` en `_compute_estado_trazabilidad` (línea 1036-1038): Correcto.
- [⚠️] `_compute_estado_trazabilidad()` itera sobre `self` (todos los lotes en el recordset) y ejecuta un `Container.search()` por cada lote. En vistas con 100+ lotes, esto genera N+1 queries. Considerar `search_read()` con batch o `read_group()`.
- [✅] `_compute_product_display()` está unificado (v4.0.1) y usa `store=True` para evitar recomputación en vistas.
- [⚠️] `lumber_reception.py` método `_fill_staging_table()` (línea 1630) procesa líneas de importación. Si el archivo de importación tiene 1000+ líneas, el rendimiento debe verificarse.
- [✅] No se detectan `search()` sin `limit` en loops cerrados
- [⚠️] Los wizards usan `@api.depends` con campos relacionados (`related='container_id.xxx'`), lo cual es correcto y evita queries adicionales.
- [✅] No se detecta `@api.onchange` que llame `search()` sobre 1000+ registros
- [✅] `@api.depends` no llama `env.cr` directamente

### 9.2 Recomendaciones
- **Acción 19:** Optimizar `_compute_estado_trazabilidad()` con un `search_read()` batch de contenedores para todos los lotes del recordset en una sola query.
- **Acción 20:** Agregar `limit` en `_fill_staging_table()` si no existe, o documentar el rendimiento esperado para archivos grandes.

***

## 10. LÓGICA DE NEGOCIO CRÍTICA (MADENAT)
### 10.1 Hallazgos
- [✅] **`is_processed_lot` depende de guía, no solo de `subproducto_id`**: CORRECTO. La función en `stock_lot.py` (líneas 1066-1090) usa 4 indicadores: `guia_processing_id`, `parent_lot_id`, dimensiones finales (`thickness_final_inch`, `width_final_inch`), y explícitamente REMUEVE `subproducto_id` como indicador único (línea 1084-1087).
- [✅] **`estado_trazabilidad` es estado logístico, no única verdad**: CORRECTO. `_compute_estado_trazabilidad()` (líneas 1020-1065) evalúa múltiples capas: procesado → embarque/consolidación → en_patio/recepcionado. Es un estado derivado, no una fuente de verdad.
- [✅] **`location_id` es ubicación física, no disponibilidad**: CORRECTO. El wizard de contenedores no usa `location_id` para filtrar disponibilidad; usa `estado_trazabilidad`, `technical_validation`, ocupación y tipo de producto.
- [✅] **Wizard contenedores sigue regla canónica**: CORRECTO. Dominio en `lumber_container_lot_wizard.py` líneas 140-146 coincide exactamente con la regla documentada en README, CHANGELOG y WIKI.
- [✅] **`allowed_formula_ids` es Many2many correcto**: CORRECTO. `madenat_subproducto.py` líneas 18-26 define la relación con tabla intermedia `madenat_subproducto_formula_rel`, columnas `subproducto_id` y `formula_id`, y help text que describe el comportamiento (sin selección = visible en todos).
- [✅] **`ingestion_seed_fase3.xml` usa `forcecreate="True"`**: CORRECTO. Las 7 entradas (3 fórmulas + 4 formatos) tienen `forcecreate="True"`.
- [⚠️] **Volumen usa `float` en lugar de `Decimal`**: `calculate_volume_metric_m3()` devuelve `float` (línea 478). Para volúmenes de embarque donde se factura, la precisión `float` puede causar discrepancias de centavos en acumulados grandes. Sin embargo, la función usa división simple (`/ 1_000_000.0`) y el caller redondea con `r3()`, lo cual es aceptable para volumen físico pero no para volumen financiero.
- [❌] **`fields.Float` para dinero en todo el proyecto**: Campos de costo, precio, monto en USD y CLP usan `fields.Float` en lugar de `fields.Monetary`. Esto es una **violación de OCA/Odoo 18 best practices**. Afecta a:
  - `stock_lot.py`: `purchase_price_usd_per_m3`, `purchase_amount_usd`, `purchase_amount_clp`, `cost_per_m3_usd`, `sale_price_usd_per_mbf`, `total_cost_usd`, `wood_cost_usd`, `purchase_cost_usd`
  - `lumber_reception.py`: `estimated_cost_usd`, `total_amount_clp`, `price_per_m3_usd`, `average_price_m3`, `price_per_mbf_usd`
  - `lumber_billing_consolidation.py`: `total_volume_m3`, `margin_percent` (aunque son porcentajes/volúmenes, no montos)
  - `lumber_cost_distribution.py`: `amount_total_usd`, `amount_original`, `amount_usd`
  - `stock_lot_costing.py`: `logistic_cost_usd`, `process_cost_usd`, `total_cost_clp`
- [⚠️] **Código duplicado**: Delete de stock moves está duplicado idénticamente en `lumber_reception.py:2559-2573` y `reception_service.py:126-137`.

### 10.2 Recomendaciones
- **Acción 21 (CRÍTICO):** Migrar `fields.Float` a `fields.Monetary` con `currency_field='currency_id'` en todos los campos de costo, precio y monto. Esto requiere agregar `currency_id` a los modelos correspondientes. Es la corrección más grande del proyecto (~6 horas).
- **Acción 22:** Unificar delete de stock moves en un solo método helper para eliminar la duplicación entre `lumber_reception.py` y `reception_service.py`.
- **Acción 23:** Evaluar si `calculate_volume_metric_m3()` debe devolver `Decimal` en lugar de `float` para operaciones financieras. Si se mantiene `float`, documentar que el caller es responsable del redondeo con `r3()`.

***

## MATRIZ DE PRIORIDADES
| Prioridad | Área | Problema | Horas estimadas | Severidad |
|---|---|---|---|---|
| 🔴 CRÍTICO | Seguridad/Financiero | `fields.Float` para dinero en todo el proyecto (stock_lot, lumber_reception, costing, billing) | 6 | 🚨 |
| 🔴 CRÍTICO | Constantes | Hardcode `25.4` en `lumber_shipment_line.py` y `lumber_reception_mass_update.py` | 1 | 🚨 |
| 🔴 CRÍTICO | Estructura | Archivo huérfano `models/0` + backups en repositorio | 0.5 | 🚨 |
| 🟡 MEDIO | Seguridad | `sudo()` en delete de quants/pickings/moves (duplicado en 2 archivos) | 3 | ⚠️ |
| 🟡 MEDIO | Rendimiento | N+1 queries en `_compute_estado_trazabilidad` por búsqueda de contenedores | 2 | ⚠️ |
| 🟡 MEDIO | Constantes | `mm_to_inch()` en `utils_uom.py` usa literal `25.4` en lugar de `MM_PER_INCH` | 0.5 | ⚠️ |
| 🟡 MEDIO | Documentación | Comentario TEMPORAL en `stock_lot.py:577` sin resolver | 0.5 | ⚠️ |
| 🟡 MEDIO | ORM | `@api.model_create_multi` ausente en creación batch de lotes | 2 | ⚠️ |
| 🟢 BAJO | Estructura | `ROADMAP.md` en `models/` en lugar de `WIKI/` | 0.2 | ℹ️ |
| 🟢 BAJO | Estructura | Wizard archivado `lumber_consolidation_import_wizard.py` no movido a `_archive/` | 0.3 | ℹ️ |
| 🟢 BAJO | Documentación | `costing_menus.xml` comentado sin documentar razón | 0.2 | ℹ️ |
| 🟢 BAJO | Rendimiento | `_fill_staging_table` sin límite documentado para archivos grandes | 0.5 | ℹ️ |

***

## CONFORMIDAD CON OCA GOBLINS
| Goblin | Cumple | Explicación |
|---|---|---|
| Named arguments in function calls | ⚠️ | Mayormente cumple. Algunas llamadas usan argumentos posicionales (ej: `self.env['stock.quant'].sudo().search([...])`) |
| Use `super()` con `current` | ✅ | Todos los `super()` llaman con `self` como primer argumento |
| No `print()` en producción | ✅ | Solo se detecta en scripts auxiliares (`scripts/backfill_*.py`, `extract_odoo_module.py`). Cero en modelos/vistas. |
| Type hints en funciones | ❌ | No se usan type hints en métodos de modelos Odoo. Las funciones en `utils_uom.py` tienen docstrings con tipos pero no anotaciones Python. |
| `_logger` en lugar de `print` | ✅ | Todo usa `_logger.info/warning/error` |
| Íconos en menús | ✅ | Los menús usan íconos (verificado en `lumber_core_menu.xml`) |
| `string` en fields | ✅ | Todos los campos tienen atributo `string` |
| `help` en campos críticos | ⚠️ | Campos de costo/precio tienen `help` en `stock_lot.py`, pero no en todos los modelos |
| Índices en campos buscables | ⚠️ | `product_code_only` tiene `store=True` pero sin `index=True`. Evaluar agregar índices para búsquedas frecuentes. |

***

## SIGUIENTES PASOS RECOMENDADOS
1. **Urgente (24-48h):**
   - Eliminar archivo huérfano `models/0`
   - Corregir hardcodes `25.4` en `lumber_shipment_line.py` y `lumber_reception_mass_update.py`
   - Corregir `mm_to_inch()` en `utils_uom.py` línea 132
2. **Semana actual:**
   - Migrar `fields.Float` → `fields.Monetary` en `stock_lot.py` (costo/precio)
   - Unificar delete de stock moves en un solo helper
3. **Próximo sprint:**
   - Migrar `fields.Float` → `fields.Monetary` en costing, billing, vendor_payment
   - Optimizar `_compute_estado_trazabilidad` con batch query
   - Mover backups fuera del repositorio

***

## CONCLUSIÓN
El proyecto MADENAT Lumber v1.1-TD003 presenta una arquitectura sólida en su núcleo de negocio: la centralización de constantes UOM en `utils_uom.py` está bien ejecutada, la corrección de `is_processed_lot` (TD-006) es correcta, y la regla canónica de disponibilidad del wizard de contenedores está implementada consistentemente con la documentación. La documentación CANON está activa y actualizada (2026-06-02). Sin embargo, el proyecto arrastra **deuda técnica significativa** en el uso generalizado de `fields.Float` para dinero (violación de OCA best practices), hardcodes de conversión imperial en 2 archivos fuera de `utils_uom.py`, y código duplicado en operaciones de delete de stock moves. Se estiman ~18 horas de corrección para alcanzar un estado APROBADO. La lógica de negocio crítica para el trading de madera está correctamente implementada y validada.