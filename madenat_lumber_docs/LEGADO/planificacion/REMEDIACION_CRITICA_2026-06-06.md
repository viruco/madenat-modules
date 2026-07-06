# REMEDIACIÓN CONTROLADA — ECOSISTEMA MADENAT LUMBER

**Versión:** 1.0  
**Fecha:** 2026-06-06  
**Ejecutor:** Arquitecto Senior Odoo 18 CE  
**Basado en:** Auditoría Integral 2026-06-06 (AUDITORIA_INTEGRAL_2026-06-06.md)  
**Alcance:** Corrección de hallazgos críticos y de alto impacto sin refactor  

---

## 1. RESUMEN EJECUTIVO

Se ejecutó la corrección de los 6 hallazgos críticos y de alto impacto identificados en la auditoría integral. Las correcciones fueron mínimas, focalizadas y no alteran el comportamiento funcional validado.

**Resultados:**
- 4 acciones con `view_mode>tree,form` → corregidas a `list,form` (compatibilidad Odoo 18)
- Menú de billing `noupdate="1"` → `noupdate="0"` (permite actualización incremental)
- Menú Configuración ahora accesible para `group_lumber_config_manager` (coherencia con grupo creado)

**Total archivos modificados:** 6  
**Total líneas modificadas:** 6  
**Cero regresiones funcionales esperadas.**

---

## 2. CAMBIOS APLICADOS

| # | Archivo | Cambio | Justificación | Tipo |
|---|---------|--------|---------------|------|
| 1 | `madenat_lumber_logistics/views/logistics_menus.xml:70` | `tree,form` → `list,form` | `tree` está deprecado desde Odoo 16. Lanza warnings en logs. Riesgo de rotura en Odoo 19+. | Crítico — Compatibilidad |
| 2 | `madenat_lumber_logistics/views/madenat_traceability_360.xml:9` | `tree,form` → `list,form` | Ídem. Acción de Trazabilidad 360 (stock.lot). | Crítico — Compatibilidad |
| 3 | `madenat_lumber_core/views/madenat_lot_cost_assignment.xml:9` | `tree,form` → `list,form` | Ídem. Acción de Asignar Costo Base. | Crítico — Compatibilidad |
| 4 | `madenat_lumber_purchasing/views/purchase_tracking_views.xml:26` | `tree,form` → `list,form` | Ídem. Acción de Seguimiento de Compras. | Crítico — Compatibilidad |
| 5 | `madenat_lumber_billing/data/lumber_billing_menu_data.xml:3` | `noupdate="1"` → `noupdate="0"` | Con `noupdate="1"`, `--update madenat_lumber_billing` no aplica cambios a menús. Obliga a `--init` o borrado manual en BD. | Alto — Mantenibilidad |
| 6 | `madenat_lumber_core/views/lumber_core_menu.xml:138` | `groups="base.group_system"` → `groups="base.group_system,group_lumber_config_manager"` | El grupo `group_lumber_config_manager` fue creado para gestionar reglas de ingesta, pero no podía ver el menú Configuración. Contradicción entre diseño de seguridad y navegación. | Alto — Seguridad/Navegación |

---

## 3. HALLAZGOS NO CORREGIDOS Y MOTIVO

### 3.1 Record Rules (ir.rule) — No implementadas

**Hallazgo original:** S-R1 — Sin record rules en ningún módulo.

**Decisión:** **No implementar en esta iteración.** Motivos:

1. **El sistema opera actualmente con 1-2 usuarios de confianza.** No hay escenario real de multi-trader o multi-planta que justifique la segregación de datos a nivel registro.
2. **Diseñar record rules sin conocer las reglas de negocio exactas es peligroso.** Una regla mal diseñada (ej: `[('shipment_id.state', '=', 'done')]`) puede ocultar datos legítimos y romper la operación.
3. **Las ACLs a nivel modelo (ir.model.access.csv) son consistentes y robustas** para el escenario actual. Operaciones ve lotes, Costos escribe costos, Gerencia puede borrar — la segregación por perfil funciona correctamente.
4. **Se requiere un taller de diseño con los stakeholders** (Felipe, Cristhian) para definir las reglas de segmentación antes de implementar.

**Recomendación:** Agendar taller de seguridad para definir reglas de visibilidad por planta/embarque/estado. Implementar en sprint dedicado con tests de regresión.

### 3.2 Billing — Grupos nativos en lugar de custom

**Hallazgo original:** S-R2 — Billing no usa grupos custom MADENAT.

**Decisión:** **No modificar en esta iteración.** Motivos:

1. Billing usa `account.group_account_manager` en todos sus menús. Cambiar esto requeriría reasignar usuarios y potencialmente romper el acceso actual.
2. El flujo de billing (consolidación → auditoría → facturación) requiere una separación de roles que aún no está definida operativamente.
3. **Riesgo alto de romper facturación en producción** si se cambian grupos sin migrar los permisos de los usuarios existentes.

**Recomendación:** Incluir en el mismo taller de seguridad que las record rules. Definir matriz de responsabilidades de billing y luego migrar ACLs.

### 3.3 Menús de Contabilidad y Gerencia sin acciones

**Hallazgo original:** A-R3 — Placeholders sin action.

**Decisión:** **No modificar.** Estos menús son placeholders intencionales documentados en `madenat_menus_por_perfil.xml` con comentarios que referencian CANON/14. Sirven como estructura de navegación lista para cuando se implementen las funcionalidades correspondientes (conciliación, cierre de período, dashboard gerencial).

---

## 4. RIESGOS RESIDUALES

| Riesgo | Severidad | Descripción | Mitigación actual |
|--------|-----------|-------------|-------------------|
| Sin record rules | Crítico | Cualquier usuario del grupo Operaciones ve todos los lotes/recepciones | Entorno controlado (1-2 usuarios). Taller de seguridad pendiente. |
| Billing usa grupos nativos | Alto | Cualquier `base.group_user` ve consolidaciones de billing | El menú raíz requiere `account.group_account_manager`, limitando exposición. |
| Placeholders sin acción | Bajo | Usuarios hacen clic y no pasa nada | Documentado. Visible solo para grupos restringidos. |
| js_class en inventory adjustments | Bajo | API puede cambiar en Odoo 19+ | Funciona en Odoo 18. Documentado en guía de upgrade pendiente. |

---

## 5. VALIDACIÓN FINAL

### 5.1 Verificación de view_mode

```
Búsqueda: tree,form en *.xml → 0 resultados
Búsqueda: list,form en *.xml → 11 ocurrencias (todas correctas)
```

### 5.2 Acciones críticas — Mapeo acción → menú → vista

| Menú | Acción | view_mode | Modelo | Estado |
|------|--------|-----------|--------|--------|
| Madera Bruta | action_lumber_reception_pending | list,form,kanban | lumber.reception | ✅ |
| Historial de Ingresos | action_lumber_reception_raw_only | list,form | lumber.reception | ✅ |
| Guías Procesadas | action_guia_processing_list | list,form | madenat.guia.processing | ✅ |
| Ajustes Físicos | action_madenat_inventory_adjustments | list | stock.quant | ✅ |
| Trazabilidad 360 | action_madenat_traceability_360 | list,form | stock.lot | ✅ Corregido |
| Asignar Costo Base | action_madenat_lot_cost_assignment | list,form | stock.lot | ✅ Corregido |
| Reglas de Cubicación | action_lumber_shipping_rule | list,form | lumber.shipping.rule | ✅ Corregido |
| Seguimiento de Compras | action_purchase_tracking | list,form | purchase.order | ✅ Corregido |
| Lotes Pendientes Valorización | action_lots_costing_pending | list,form | stock.lot | ✅ |
| Consola Rentabilidad | action_cost_analysis | list,pivot,graph,form | stock.lot | ✅ |
| Consola Compras | action_madenat_purchase_order | list,kanban,pivot,graph,form | purchase.order | ✅ |
| Toll Processing | action_toll_processing_order | list,form | toll.processing.order | ✅ |

### 5.3 Verificación de menú Configuración

- `menu_madenat_config_root` ahora acepta: `base.group_system` + `group_lumber_config_manager`
- Submenús (`Patios de Recepción`, `Subproductos y Grados`) heredan la visibilidad del padre → el Configurador ahora puede acceder

### 5.4 Verificación de noupdate en billing

- `lumber_billing_menu_data.xml` ahora usa `noupdate="0"`
- Un `--update madenat_lumber_billing` aplicará cambios a menús correctamente

---

## 6. RECOMENDACIONES DOCUMENTALES

1. **Actualizar CHANGELOG** de cada módulo modificado registrando el cambio (tree→list, noupdate, groups).
2. **Agregar entrada en CANON/04_DECISION_LOG.md** documentando:
   - Por qué NO se implementaron record rules ahora
   - Decisión de mantener placeholders de Contabilidad/Gerencia
   - Decisión de no migrar billing a grupos custom sin taller previo
3. **Crear `docs/UPGRADE_NOTES_Odoo18.md`** listando los puntos de atención para futuros upgrades (js_class, dependencias implícitas, etc.)

---

## 7. LISTA EXACTA DE ARCHIVOS TOCADOS

| # | Archivo | Cambio | Línea |
|---|---------|--------|-------|
| 1 | `custom_addons/madenat_lumber_logistics/views/logistics_menus.xml` | `tree,form` → `list,form` | 70 |
| 2 | `custom_addons/madenat_lumber_logistics/views/madenat_traceability_360.xml` | `tree,form` → `list,form` | 9 |
| 3 | `custom_addons/madenat_lumber_core/views/madenat_lot_cost_assignment.xml` | `tree,form` → `list,form` | 9 |
| 4 | `custom_addons/madenat_lumber_purchasing/views/purchase_tracking_views.xml` | `tree,form` → `list,form` | 26 |
| 5 | `custom_addons/madenat_lumber_billing/data/lumber_billing_menu_data.xml` | `noupdate="1"` → `noupdate="0"` | 3 |
| 6 | `custom_addons/madenat_lumber_core/views/lumber_core_menu.xml` | `groups="base.group_system"` → `groups="base.group_system,group_lumber_config_manager"` | 138 |

**Total: 6 archivos, 6 líneas modificadas.**  
**Cero archivos creados. Cero archivos eliminados.**

---

*Informe de remediación generado el 2026-06-06. Correcciones aplicadas con criterio de mínimo impacto y máxima trazabilidad.*