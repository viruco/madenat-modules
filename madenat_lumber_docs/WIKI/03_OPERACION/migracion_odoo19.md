# Migración Odoo 18 → 19 — Planificación

**Módulo:** Infraestructura
**Categoría:** Operación
**Estado:** Borrador
**Última actualización:** 2026-05-30

---

## Propósito

Documento de planificación para la migración futura de Odoo 18 CE a Odoo 19 CE. Este documento establece el inventario de módulos, el checklist de preparación y los riesgos identificados.

> **Estado actual:** EN PREPARACIÓN — Odoo 19 aún no tiene fecha oficial de release. Los cambios documentados aquí son **PRELIMINARES** y deben confirmarse con el changelog oficial.

---

## Inventario de módulos custom a migrar

### Módulos principales

| Módulo | Archivos .py | Líneas estimadas | Dependencias externas | Prioridad |
|---|---|---|---|---|
| `madenat_lumber_core` | 21 | ~8000 | Ninguna (extiende stock, purchase, account) | **Crítica** |
| `madenat_lumber_logistics` | 8 | ~3000 | `madenat_lumber_shipping_core` | Alta |
| `madenat_lumber_shipping_core` | pendiente | pendiente | `uom` | Alta (prerequisito) |
| `madenat_lumber_costing` | pendiente | pendiente | `account`, `logistics`, `shipping_core` | Media |
| `madenat_lumber_reports` | pendiente | pendiente | Ninguna (solo vistas) | Baja |

### Mixins y utilidades compartidas

| Modelo/Clase | Ubicación | Complejidad |
|---|---|---|
| `madenat.lumber.ingest.mixin` | `mixin_lumber_ingest.py` | Alta — usado por recepción y guía processing |
| `validation_checklist_mixin` | `validation_checklist_mixin.py` | Media |
| `utils_uom` | `utils_uom.py` | Media — factores de conversión críticos |
| `width_mapping` | `width_mapping.py` | Baja — tabla de mapeo |

### Wizards

| Wizard | Módulo | Complejidad |
|---|---|---|
| `lumber.reception.mass_update` | core | Baja |
| `madenat.guia.mass_update` | core | Baja |
| `lumber.container.lot.wizard` | logistics | Media |
| `lumber.container.rollover.wizard` | logistics | Media |

---

## Cambios conocidos Odoo 18 → 19 (PRELIMINAR)

> ⚠️ **PENDIENTE DE CONFIRMACIÓN** — verificar cuando se publique el changelog oficial de Odoo 19.

### Áreas a verificar

| Área | Qué verificar | Impacto estimado |
|---|---|---|
| **Python ORM** | Cambios en `@api.depends`, `@api.constrains`, `@api.onchange` | Alto — 50+ métodos computados en core |
| **JavaScript/OWL** | Migración de componentes custom, widgets | Medio — módulos MADENAT usan vistas estándar principalmente |
| **PostgreSQL schema** | Cambios de schema en módulos base (`stock`, `purchase`, `account`) | Alto — MADENAT extiende estos modelos extensivamente |
| **Reportes QWeb** | Cambios en plantillas PDF | Medio — `madenat_lumber_reports` y reportes de logistics |
| **Security** | Cambios en `ir.model.access`, `ir.rule`, grupos | Bajo — MADENAT usa grupos mínimos |
| **mail.thread** | Cambios en herencia de chatter | Bajo — MADENAT usa `mail.thread` como mixin estándar |

### Modelos base de alto riesgo

MADENAT extiende estos modelos de Odoo — verificar cambios de schema en Odoo 19:

| Modelo base | Archivos MADENAT que lo extienden |
|---|---|
| `stock.lot` | `stock_lot.py` (1386 líneas) |
| `stock.picking` | `stock_picking.py` |
| `stock.move` | `stock_move.py` |
| `purchase.order` | `lumber_reception.py` (2506 líneas) |
| `account.move` | Referenciado en `lumber_reception.py` |
| `product.template` / `product.product` | `product_template.py`, `product_product.py` |
| `res.partner` | Referenciado en múltiples modelos |

---

## Checklist pre-migración

- [ ] Backup completo de `madenat_test` + filestore + volumen Docker
- [ ] Inventario completo de todos los módulos custom y sus dependencias
- [ ] Tests unitarios pasando al 100% en Odoo 18
- [ ] Revisar changelog oficial de Odoo 19 (cuando se publique)
- [ ] Crear ambiente de prueba separado para migración (no usar `madenat_test`)
- [ ] Validar que `madenat_lumber_shipping_core` sea compatible con Odoo 19
- [ ] Verificar compatibilidad de `openpyxl`, `pdfplumber`, `pandas`, `xlsxwriter` (dependencias Python)
- [ ] Documentar todos los campos computed y sus dependencias (ya hecho en [[campos_computados]])
- [ ] Documentar todas las transiciones de estado (ya hecho en [[modelo_recepciones]], [[modelo_despachos]])
- [ ] Verificar que PostgreSQL 15 sea compatible con Odoo 19 (o plan de upgrade a PG 16/17)

---

## Checklist post-migración

- [ ] `-u all` sin errores en el log
- [ ] Flows críticos funcionando:
  - [ ] Recepción de madera: PDF + Excel → staging → lotes
  - [ ] Guía de procesamiento: Excel → líneas → lotes procesados
  - [ ] Embarque: crear → confirmar → cargar → sellar → zarpar
  - [ ] Distribución de costos logísticos
- [ ] Campos computados recalculados correctamente (verificar `vol_shipment_m3`, `volumen_m3`, `vol_mbf`)
- [ ] Seguridad y accesos verificados (grupos `madenat_admin`, `madenat_cost_auditor`)
- [ ] Reportes PDF generando correctamente (packing list, guía report)
- [ ] Vistas tree/form/pivot sin errores OWL
- [ ] Wizards abriendo y funcionando (mass update, container lot, rollover)
- [ ] Backup post-migración completo
- [ ] Comparar conteo de registros pre/post migración

---

## Riesgo estimado

**Nivel: ALTO**

### Factores de riesgo

| Factor | Impacto | Mitigación |
|---|---|---|
| Volumen de código custom (~11000+ líneas en core + logistics) | Alto | Migración incremental módulo por módulo |
| Mixin propio (`madenat.lumber.ingest.mixin`) | Alto | Verificar que el ORM no rompa herencia múltiple |
| Dependencia de `madenat_lumber_shipping_core` | Medio | Verificar compatibilidad primero |
| Factores de conversión UoM (`utils_uom.py`) | Medio | Tests de precisión numérica post-migración |
| Múltiples `@api.depends` complejos | Medio | Verificar que las dependencias no se rompan |
| Código que usa `self.env.cr.execute()` (SQL directo) | Bajo | Verificar que el schema no cambie en tablas base |
| Herencia de `mail.thread` y `mail.activity.mixin` | Bajo | Verificar que la API no cambie |

### Estrategia recomendada

1. **Primero:** migrar `madenat_lumber_shipping_core` (el más simple, prerequisito de otros)
2. **Segundo:** migrar `madenat_lumber_core` (el más crítico, base de todo)
3. **Tercero:** migrar `madenat_lumber_logistics` (depende de core + shipping_core)
4. **Cuarto:** migrar módulos restantes (`costing`, `reports`, etc.)
5. **Final:** validación completa del flujo end-to-end

---

## Relacionado

- [[backup_restauracion]]
- [[comandos_postgresql]]
- [[despliegue_modulo]]
- [[dependencias_modulos]]
- [[campos_computados]]
- [[DEC-005_oracle_cloud_prod]]
