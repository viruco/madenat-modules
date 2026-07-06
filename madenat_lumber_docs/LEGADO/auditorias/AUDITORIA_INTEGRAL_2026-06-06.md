# AUDITORÍA TÉCNICA INTEGRAL — ECOSISTEMA MADENAT LUMBER

**Versión:** 1.0  
**Fecha:** 2026-06-06  
**Auditor:** Auditor Técnico Senior Odoo 18 CE  
**Alcance:** 10 módulos custom — core, logistics, shipping_core, costing, purchasing, toll_processing, billing, reports, reception_improvements, vendor_payment  
**Método:** Revisión estática de código (sin modificaciones)  
**Estado del proyecto:** Navegación funcional estabilizada, sin regresiones activas conocidas  

---

## 1. RESUMEN EJECUTIVO

El ecosistema MADENAT Lumber presenta una arquitectura modular bien concebida, con `madenat_lumber_core` como dueño único del root menu y la estructura de navegación principal. La migración a Odoo 18 está avanzada: todas las vistas usan `<list>` en lugar del deprecado `<tree>`, y los manifests están versionados correctamente.

**Fortalezas principales:**
- Root único y centralizado en `madenat_lumber_core` (evita guerras de menús)
- Sistema de grupos custom coherente (7 grupos con jerarquía de implied_ids bien definida)
- Matriz de ACLs consistente (patrón 4×modelo: ops/costos/contab/gerencia)
- Documentación CANON extensa (18 documentos numerados)
- Manifests con comentarios de orden de carga y propósitos

**Debilidades principales:**
- 4 acciones con `view_mode>tree,form` (deprecado en Odoo 18) — riesgo de rotura futura
- Ausencia total de record rules (ir.rule) — solo ACLs a nivel modelo
- Facturación (billing) no usa los grupos custom MADENAT — inconsistencia de seguridad
- Menú de Configuración restringido a `base.group_system` — demasiado restrictivo para operación
- Menús de Toll Processing semánticamente mal ubicados bajo "Control de Lotes"

**Veredicto general:** El proyecto está **operativamente sano** pero presenta **deuda técnica de seguridad y compatibilidad** que debe atenderse antes del próximo upgrade de Odoo o antes de exponer el sistema a usuarios no-admin. No se requieren refactors gigantes; los hallazgos son focalizados y remediables.

---

## 2. HALLAZGOS POR CATEGORÍA

### 2.1 ARQUITECTURA Y NAVEGACIÓN

#### Fortalezas

| # | Hallazgo | Evidencia |
|---|----------|-----------|
| A1 | **Root único centralizado.** `menu_madenat_root` (id=`madenat_lumber_core.menu_madenat_root`) es el único menú raíz. Todos los módulos cuelgan de él. | `lumber_core_menu.xml:101-104` |
| A2 | **Jerarquía de 6 ramas principales bien definida:** Operaciones, Exportaciones, Reportes, Costeo/Finanzas, Auditoría, Configuración + 2 ramas adicionales (Contabilidad, Gerencia) en `madenat_menus_por_perfil.xml`. | `lumber_core_menu.xml:110-139`, `madenat_menus_por_perfil.xml:12-60` |
| A3 | **Remapeo limpio en reports.** `menu_remapping.xml` reparenta `vendor_payment` bajo `menu_finance_payments` y conecta reportes bajo `menu_madenat_reports_main` sin duplicar definiciones. | `menu_remapping.xml:9-37` |
| A4 | **Acciones con domains semánticos correctos.** Ej: `action_lumber_reception_pending` filtra recepciones sin OC, `action_guia_processing_list` excluye raw con `tipo_recepcion != 'raw'`. | `lumber_core_menu.xml:13,39` |
| A5 | **Nombres visibles descriptivos con emojis** que facilitan la identificación visual en la UI. | Todo `lumber_core_menu.xml` |

#### Hallazgos de Riesgo

| ID | Título | Severidad | Módulo/Archivo | Evidencia | Impacto | Recomendación |
|----|--------|-----------|----------------|-----------|---------|---------------|
| **A-R1** | Toll Processing cuelga de "Control de Lotes" | **Medio** | `madenat_toll_processing/views/menus.xml:20` | `parent="madenat_lumber_core.menu_ops_inventory"` | Usuarios de operaciones no encontrarán Procesamiento Externo bajo Control de Lotes (confusión semántica). Control de Lotes es inventario; Toll Processing es manufactura externa. | Re-parent bajo `menu_ops_main` directamente (sequence 30) o crear rama "Manufactura" dedicada. **Requiere cambio futuro.** |
| **A-R2** | Billing usa `noupdate="1"` en menús | **Alto** | `madenat_lumber_billing/data/lumber_billing_menu_data.xml:3` | `<data noupdate="1">` | Los menús de billing no se actualizarán al hacer `--update madenat_lumber_billing`. Cambios futuros requerirán `--init` o borrado manual en BD. | Cambiar a `noupdate="0"` y verificar que no haya secuencias o datos que requieran noupdate. Si hay datos semilla, separarlos en otro archivo con noupdate=1. **Requiere cambio futuro.** |
| **A-R3** | Menús de Contabilidad y Gerencia sin acciones | **Medio** | `madenat_menus_por_perfil.xml:17-27,36-46` | `menu_contabilidad_conciliacion`, `menu_contabilidad_cierre`, `menu_gerencia_dashboard`, `menu_gerencia_trazabilidad` no tienen atributo `action` | Los menús aparecen pero no abren ninguna vista. El usuario hace clic y no pasa nada. Genera percepción de funcionalidad incompleta. | Agregar acciones window correspondientes o declararlos como categorías con `groups` apropiados. Si son placeholders, documentarlo explícitamente. **Requiere cambio futuro.** |
| **A-R4** | Configuración restringido a `base.group_system` | **Alto** | `lumber_core_menu.xml:138` | `groups="base.group_system"` en `menu_madenat_config_root` | Solo el superadmin ve Configuración. El grupo `group_lumber_config_manager` (creado para esto) no puede acceder porque `base.group_system` no implica los grupos custom. La Configuración de Ingesta queda inaccesible para el Configurador designado. | Agregar `group_lumber_config_manager` al atributo `groups` del menú: `groups="base.group_system,group_lumber_config_manager"`. O crear submenú visible para el configurador. **Requiere cambio futuro.** |
| **A-R5** | Menús sin atributo `groups` explícito | **Bajo** | `lumber_core_menu.xml:179-198` (varios), `logistics_menus.xml:9-65` (varios) | Muchos menús no tienen `groups` | Heredan visibilidad del padre. Si el padre es visible para todos los usuarios internos, estos menús también lo serán. No es necesariamente un bug, pero reduce la trazabilidad de quién ve qué. | Auditoría de visibilidad runtime para confirmar que los menús son visibles solo para quienes deben serlo. Documentar la herencia de visibilidad. **Solo documentación.** |

### 2.2 SEGURIDAD

#### Fortalezas

| # | Hallazgo | Evidencia |
|---|----------|-----------|
| S1 | **Siete grupos custom bien definidos** con jerarquía clara: `group_madenat_cost_auditor` → `group_madenat_admin` → `group_lumber_config_manager`, y en paralelo `group_madenat_gerencia` que implica ops+costos+contabilidad. | `madenat_security.xml:10-62` |
| S2 | **Matriz ACL 4×modelo consistente** en core, logistics y costing. Cada modelo tiene 4 reglas (ops/costos/contab/gerencia) con permisos granulares. | `ir.model.access.csv` de los 3 módulos principales |
| S3 | **Permisos de escritura correctamente asignados:** operaciones escribe en recepciones/lotes; costos escribe en líneas de costo; gerencia tiene delete en subproductos/guías processing. | `ir.model.access.csv` de core: líneas 2 vs 5, 10 vs 13, 26 vs 29 |
| S4 | **Configurador de ingesta aislado:** `group_lumber_config_manager` tiene CRUD total solo sobre modelos de configuración (mapas, tolerancias, reglas). Usuarios normales solo lectura. | `ir.model.access.csv` de core: líneas 46-63 |

#### Hallazgos de Riesgo

| ID | Título | Severidad | Módulo/Archivo | Evidencia | Impacto | Recomendación |
|----|--------|-----------|----------------|-----------|---------|---------------|
| **S-R1** | **Sin record rules (ir.rule) en ningún módulo** | **Crítico** | Todos los módulos | Búsqueda `ir.rule` en todos los XML del proyecto devuelve 0 resultados | No hay seguridad a nivel de registros. Cualquier usuario del grupo "Operaciones" puede ver todos los lotes de todos los embarques, todas las recepciones, etc. Si en el futuro hay múltiples traders o plantas, no habrá segregación de datos. | Implementar record rules para modelos críticos: `stock.lot` (por shipment_id/planta), `lumber.reception` (por ubicación), `lumber.export.shipment` (por estado/viaje). **Requiere cambio futuro.** |
| **S-R2** | **Billing no usa grupos custom MADENAT** | **Alto** | `madenat_lumber_billing/security/ir.model.access.csv:2-4` | Usa `base.group_user` y `account.group_account_manager` en lugar de `group_madenat_operaciones`, `group_madenat_costos`, etc. | Todos los usuarios internos pueden leer y escribir consolidaciones de billing. La separación de responsabilidades (quién consolida vs quién audita vs quién factura) no está implementada. | Reemplazar `base.group_user` por `group_madenat_costos` o `group_madenat_contabilidad` según corresponda. Agregar reglas específicas para el flujo de billing: consolidación → auditoría → facturación. **Requiere cambio futuro.** |
| **S-R3** | **Menús con grupos nativos de Odoo en lugar de grupos custom** | **Medio** | `lumber_core_menu.xml:184,190,197,205,213,234,241` | `groups="stock.group_stock_user"` y `groups="stock.group_stock_manager"` en menús de core | Los grupos nativos no distinguen entre perfiles MADENAT. `stock.group_stock_user` es demasiado amplio — cualquier usuario de inventario ve estos menús, no solo el equipo de Operaciones MADENAT. | Reemplazar con `group_madenat_operaciones` donde corresponda. Mantener `stock.group_stock_user` solo si realmente se desea acceso universal a funcionalidad de stock. **Requiere cambio futuro.** |
| **S-R4** | **`stock_lot_cost_line` duplicado en ACL de core y costing** | **Medio** | `madenat_lumber_core/security/ir.model.access.csv:14-17` y `madenat_lumber_costing/security/ir.model.access.csv:10-13` | Ambos módulos definen accesos para `model_stock_lot_cost_line` con idénticos permisos | Riesgo de warning en carga si hay colisión de IDs. Odoo resuelve por orden de carga (gana el último), pero es frágil ante cambios de dependencia. | Dejar la definición en un solo módulo (preferiblemente core, que define el modelo). Eliminar la duplicada en costing. **Requiere cambio futuro.** |
| **S-R5** | **`stock_lot` accesos cross-module no unificados** | **Bajo** | `core/ir.model.access.csv:10-13` y `costing/ir.model.access.csv:14` | Core define accesos para ops/costos/contab/ger. Costing agrega una 5ª regla `access_stock_lot_user` para `group_madenat_costos` con permisos (1,0,1,0). | Duplicación parcial con permisos diferentes: en core costos tiene (1,0,1,0), en costing costos tiene (1,0,1,0) — mismos valores. No hay conflicto funcional pero es redundante. | Consolidar en core, eliminar la regla redundante de costing. **Requiere cambio futuro — Mejora.** |

### 2.3 COMPATIBILIDAD ODOO 18

#### Fortalezas

| # | Hallazgo | Evidencia |
|---|----------|-----------|
| C1 | **Vistas usan `<list>` en lugar de `<tree>`.** Todas las vistas de tipo lista usan el tag correcto de Odoo 18. | Búsqueda `<tree` en XML: 0 resultados. |
| C2 | **Manifests versionados para Odoo 18:** todos los módulos principales declaran `version: 18.0.x.x`. | Todos los `__manifest__.py` revisados |
| C3 | **La mayoría de acciones usan `view_mode>list,form` correctamente.** | `lumber_core_menu.xml:12,24,37,46,79,92` — todos correctos |

#### Hallazgos de Riesgo

| ID | Título | Severidad | Módulo/Archivo | Evidencia | Impacto | Recomendación |
|----|--------|-----------|----------------|-----------|---------|---------------|
| **C-R1** | **`view_mode>tree,form` residual en 4 acciones** | **Crítico** | `logistics_menus.xml:70`, `madenat_traceability_360.xml`, `madenat_lot_cost_assignment.xml`, `purchase_tracking_views.xml` | `<field name="view_mode">tree,form</field>` en 4 ubicaciones | `tree` está deprecado desde Odoo 16. En Odoo 18 aún funciona por retrocompatibilidad, pero lanza warnings en el log y **puede ser eliminado en Odoo 19 o 20**. Causa que las vistas de lista no se rendericen correctamente si el fallback se rompe. | Cambiar a `<field name="view_mode">list,form</field>` en los 4 archivos. **Requiere cambio futuro.** |
| **C-R2** | **Sin etiquetas deprecadas en vistas XML** | — | — | No se detectaron `<tree>`, `<field widget="statusbar">` obsoleto, ni otros patrones deprecados. | **Fortaleza.** Confirmar revisión manual de vistas extendidas de stock. | Mantener vigilancia en próximos upgrades de Odoo. |
| **C-R3** | **Billing manifiest version** | **Bajo** | `madenat_lumber_billing/__manifest__.py:4` | `'version': '1.0.0'` en lugar de `18.0.x.x` | Inconsistencia con la convención del resto de módulos. No rompe funcionalidad pero complica el tracking de versiones. | Cambiar a `18.0.1.0.0` para seguir la convención del ecosistema. **Requiere cambio futuro — Mejora.** |
| **C-R4** | **Uso de `js_class` en vista lista** | **Bajo** | `lumber_core_menu.xml:61` | `js_class="inventory_report_list"` | Esta API puede cambiar en futuras versiones de Odoo. Funciona en 18 pero debe verificarse tras cada upgrade. | Documentar como punto de atención en guía de upgrade. Verificar que `inventory_report_list` esté definido en los assets del módulo. **Solo documentación.** |

### 2.4 MANIFESTS Y CARGA

#### Fortalezas

| # | Hallazgo | Evidencia |
|---|----------|-----------|
| M1 | **Core manifest con excelente orden de carga documentado:** seguridad → vistas → wizards → arquitectura → reportes → configuración → datos semilla. Con comentarios por fase. | `madenat_lumber_core/__manifest__.py:11-54` |
| M2 | **Logistics manifest con comentarios de precedencia:** wizards antes de vistas para que botones funcionen, reportes antes de acciones. | `madenat_lumber_logistics/__manifest__.py:27-59` |
| M3 | **Dependencias limpias y no circulares.** El grafo de dependencias es acíclico: core → (shipping_core, purchasing) → logistics → costing → reports. Reports depende de todos (correcto para remapeo). | Todos los manifests |
| M4 | **Costing corrigió bug de auto-dependencia:** `# 🛑 ELIMINADO: 'madenat_lumber_costing' (Un módulo no puede depender de sí mismo)` | `madenat_lumber_costing/__manifest__.py:23` |

#### Hallazgos de Riesgo

| ID | Título | Severidad | Módulo/Archivo | Evidencia | Impacto | Recomendación |
|----|--------|-----------|----------------|-----------|---------|---------------|
| **M-R1** | **Orden de carga en core: vistas antes de arquitectura** | **Medio** | `madenat_lumber_core/__manifest__.py:17-38` | Las vistas de subproducto y stock se cargan (línea 17-21) antes de los menús de arquitectura base (línea 35-41). | Si una vista referencia un menú que aún no existe, Odoo lanzará error silencioso y el menú podría no renderizarse. Actualmente no hay error porque las vistas no referencian menús, pero es frágil. | Mover los archivos de arquitectura base (menús, dashboards) antes de las vistas que podrían referenciarlos. Orden ideal: seguridad → arquitectura/menús → vistas → wizards → datos. **Requiere cambio futuro — Mejora.** |
| **M-R2** | **`madenat_lumber_shipping_core` no define menús propios** | **Medio** | `madenat_lumber_shipping_core/__manifest__.py:11` | `# 'views/shipping_menus.xml',#ELIMINADO - Menús migrados a logistics` | Las vistas de motonaves/viajes/reservas existen pero solo son accesibles desde los menús que logistics les construye. Si logistics no está instalado, shipping_core es invisible en la UI. | Evaluar si shipping_core debe poder usarse standalone. Si no, documentar la dependencia funcional. El manifiest no declara dependencia de logistics, pero en la práctica la requiere para tener UI. **Recomendación: documentar, no requiere cambio de código.** |
| **M-R3** | **Múltiples backups `.bak` huérfanos en producción** | **Bajo** | `__manifest__.py.bak.20260606_121330` en core y costing, `lumber_billing_menu_data.xml.bak.20260606_121330` en billing | Archivos de respaldo con timestamp en el árbol de módulos | Odoo podría intentar cargar estos archivos si el patrón de descubrimiento de módulos los incluye. Además ensucian el repositorio. | Mover a `_archive/` o eliminar. Agregar `*.bak*` al `.gitignore`. **Requiere cambio futuro — Mejora.** |
| **M-R4** | **`data` en billing manifest pero archivo en `data/` vs `views/`** | **Bajo** | `madenat_lumber_billing/__manifest__.py:36` vs ubicación real | Menús en `data/lumber_billing_menu_data.xml` en lugar de `views/` | No es error pero es inconsistente con los demás módulos (todos ponen menús en `views/`). Complica el mantenimiento para nuevos desarrolladores. | Mover `lumber_billing_menu_data.xml` a `views/` o documentar la convención. **Requiere cambio futuro — Mejora.** |

### 2.5 DOCUMENTACIÓN

#### Inventario de Documentación Existente

| Tipo | Ubicación | Archivos | Estado |
|------|-----------|----------|--------|
| **CANON (documentación oficial)** | `madenat_lumber_docs/CANON/` | 18 documentos numerados (00-15 + INDICE) | ✅ Extenso y estructurado |
| **WIKI Técnico** | `madenat_lumber_docs/WIKI/02_TECNICO/` | 6 documentos sobre modelos, ingesta, dependencias | ✅ Cubre aspectos técnicos clave |
| **Auditorías previas** | `madenat_lumber_docs/` | AUDITORIA_2026-06-03.md, AUDITORIA_2026-06-04.md, AUDITORIA_RUNTIME_2026-06-05.md | ✅ 3 auditorías previas |
| **Análisis y planes** | `madenat_lumber_docs/` | ANALISIS_INTEGRAL_INVENTARIO_TRADERS.md, PLAN_DEPURACION_PRIORIZADO.md, PLAN_ACCION_EJECUTABLE.md, GUIA_OPERATIVA_IMPLEMENTACION.md, EJECUCION_FASE0.md, MANDATO_EJECUCION.md | ✅ Cobertura de gestión |
| **CHANGELOG** | `madenat_lumber_core/` | CHANGELOG.md | ✅ Core documentado |
| **CHANGELOG** | `madenat_lumber_logistics/` | CHANGELOG.md | ✅ Logistics documentado |
| **README** | Core, Logistics, Toll, Billing, Reception, Vendor | README.md en 6 módulos | ✅ Mayoría con README |
| **Decision Log** | `madenat_lumber_docs/CANON/04_DECISION_LOG.md` | Bitácora de decisiones | ✅ Arquitectura documentada |

#### Vacíos Documentales Detectados

| ID | Documento Faltante | Severidad | Impacto | Recomendación |
|----|--------------------|-----------|---------|---------------|
| **D-V1** | **Matriz de grupos y permisos** | **Alto** | Sin este documento, un auditor de seguridad o un nuevo desarrollador no puede verificar rápidamente quién tiene acceso a qué. La información existe en los CSV pero está dispersa en 5 módulos. | Crear `docs/SEGURIDAD_permisos_matriz.md` con tabla consolidada: Modelo × Grupo × (R,W,C,D). Incluir los grupos de billing que usan grupos nativos. |
| **D-V2** | **Mapa visual de menús y navegación** | **Alto** | El árbol de menús está distribuido en 7 archivos XML. Sin un mapa, es difícil para QA o nuevos desarrolladores verificar la integridad de la navegación. | Crear `docs/NAVEGACION_mapa_menus.md` con árbol ASCII/indentado de todos los menús, su módulo de origen, acción asociada y grupo requerido. |
| **D-V3** | **README técnico en costing, purchasing, shipping_core, reports** | **Medio** | 4 de 10 módulos no tienen README.md. Un desarrollador nuevo no tiene punto de entrada documental para entender el propósito del módulo. | Crear README.md mínimo en cada módulo con: propósito, dependencias, modelos principales, flujo de negocio que cubre. |
| **D-V4** | **Guía de troubleshooting de errores conocidos** | **Alto** | Los errores ya enfrentados (menús invisibles por grupos, view_mode tree, actions vacías) no están documentados como guía de diagnóstico rápido. Si recurren, el equipo pierde tiempo rediagnosticando. | Crear `docs/TROUBLESHOOTING.md` con síntomas, causas raíz conocidas y soluciones para los errores ya vistos durante la estabilización. |
| **D-V5** | **Guía de upgrade/restart/update** | **Medio** | No hay documentación de cómo hacer un update de módulo seguro, qué orden seguir, ni qué validar post-update. | Crear `docs/GUIA_UPGRADE.md` con: orden de update de módulos, flags recomendados (`--stop-after-init`, `--log-level`), smoke tests post-update. |
| **D-V6** | **Bitácora de decisiones de estabilización** | **Medio** | CANON/04_DECISION_LOG.md existe pero no incluye las decisiones tomadas durante la estabilización reciente (cambios de tree→list, reparenting de menús, domains ajustados). | Actualizar CANON/04_DECISION_LOG.md con un apéndice "Estabilización Mayo-Junio 2026" detallando cada decisión y su justificación. |

---

## 3. RIESGOS PRIORITARIOS

### Críticos (requieren acción inmediata o en próxima iteración)

| # | ID | Título | Módulo |
|---|----|-------|--------|
| 1 | **C-R1** | 4 acciones con `view_mode>tree,form` | logistics, core, purchasing |
| 2 | **S-R1** | Sin record rules en ningún módulo | Todos |

### Altos (requieren acción planificada)

| # | ID | Título | Módulo |
|---|----|-------|--------|
| 3 | **S-R2** | Billing no usa grupos custom MADENAT | billing |
| 4 | **A-R2** | Billing usa `noupdate="1"` en menús | billing |
| 5 | **A-R4** | Configuración restringido a `base.group_system` | core |
| 6 | **D-V1** | Falta matriz de grupos/permisos | docs |
| 7 | **D-V4** | Falta guía de troubleshooting | docs |
| 8 | **D-V2** | Falta mapa de menús y navegación | docs |

### Medios (requieren acción en backlog)

| # | ID | Título | Módulo |
|---|----|-------|--------|
| 9 | **A-R1** | Toll Processing mal ubicado bajo Control de Lotes | toll_processing |
| 10 | **A-R3** | Menús de Contabilidad/Gerencia sin acciones | core |
| 11 | **S-R3** | Menús usan grupos nativos en lugar de custom | core, billing |
| 12 | **S-R4** | stock_lot_cost_line duplicado en ACL core+costing | core, costing |
| 13 | **M-R1** | Orden de carga en core: vistas antes de arquitectura | core |
| 14 | **M-R2** | shipping_core sin menús propios (depende de logistics) | shipping_core |
| 15 | **D-V3** | Sin README en costing, purchasing, shipping_core, reports | docs |

### Bajos / Mejoras (pueden esperar)

| # | ID | Título | Módulo |
|---|----|-------|--------|
| 16 | **A-R5** | Menús sin atributo `groups` explícito | varios |
| 17 | **S-R5** | stock_lot accesos redundantes en costing | costing |
| 18 | **C-R3** | Billing manifiest version no sigue convención | billing |
| 19 | **C-R4** | js_class en vista de inventario (punto de upgrade) | core |
| 20 | **M-R3** | Backups .bak huérfanos | varios |
| 21 | **M-R4** | Menús de billing en data/ en lugar de views/ | billing |
| 22 | **D-V5** | Falta guía de upgrade/restart/update | docs |
| 23 | **D-V6** | Bitácora de decisiones no actualizada con estabilización reciente | docs |

---

## 4. RECOMENDACIONES PRIORIZADAS (Plan de Acción)

### Sprint 1 — Correcciones de Compatibilidad y Seguridad (1-2 días)

1. **Corregir `view_mode>tree,form` → `list,form`** en 4 archivos:
   - `madenat_lumber_logistics/views/logistics_menus.xml:70`
   - `madenat_lumber_logistics/views/madenat_traceability_360.xml`
   - `madenat_lumber_core/views/madenat_lot_cost_assignment.xml`
   - `madenat_lumber_purchasing/views/purchase_tracking_views.xml`

2. **Cambiar `noupdate="1"` → `noupdate="0"`** en `madenat_lumber_billing/data/lumber_billing_menu_data.xml:3`

3. **Agregar `group_lumber_config_manager` al menú Configuración** en `lumber_core_menu.xml:138`:
   ```
   groups="base.group_system,group_lumber_config_manager"
   ```

### Sprint 2 — Seguridad (3-5 días)

4. **Refactorizar ACL de billing** para usar grupos custom MADENAT en lugar de `base.group_user` / `account.group_account_manager`

5. **Reemplazar `stock.group_stock_user` por `group_madenat_operaciones`** en menús de core donde corresponda

6. **Eliminar duplicación de `stock_lot_cost_line`** entre core y costing

7. **Diseñar e implementar record rules** para modelos críticos (al menos `stock.lot` y `lumber.reception`)

### Sprint 3 — Documentación (1-3 días)

8. **Crear `docs/SEGURIDAD_permisos_matriz.md`** — consolidar todos los ir.model.access.csv en una tabla

9. **Crear `docs/NAVEGACION_mapa_menus.md`** — árbol completo de menús con acciones y grupos

10. **Crear `docs/TROUBLESHOOTING.md`** — síntomas y soluciones de errores ya enfrentados

11. **Crear README.md** en costing, purchasing, shipping_core, reports (mínimo viable)

12. **Actualizar `CANON/04_DECISION_LOG.md`** con decisiones de estabilización Mayo-Junio 2026

### Backlog (cuando haya disponibilidad)

13. Re-parent Toll Processing bajo `menu_ops_main`
14. Agregar acciones a menús placeholder de Contabilidad y Gerencia
15. Normalizar versión de billing manifest a `18.0.1.0.0`
16. Mover menús de billing a `views/`
17. Limpiar archivos `.bak` huérfanos
18. Reordenar data list del manifest de core (arquitectura antes de vistas)
19. Documentar dependencia funcional de shipping_core en logistics
20. Crear `docs/GUIA_UPGRADE.md`

---

## 5. LISTA DE DOCUMENTACIÓN MÍNIMA A CREAR O ACTUALIZAR

| # | Documento | Prioridad | Contenido esperado |
|---|-----------|-----------|--------------------|
| 1 | `docs/SEGURIDAD_permisos_matriz.md` | **Alta** | Tabla consolidada de todos los modelos × grupos × permisos de los 10 módulos |
| 2 | `docs/NAVEGACION_mapa_menus.md` | **Alta** | Árbol jerárquico completo de menús con: ID, nombre, parent, acción, grupos, módulo de origen |
| 3 | `docs/TROUBLESHOOTING.md` | **Alta** | Síntomas → Causa → Solución para: menús invisibles, view_mode tree, actions vacías, errores de carga, campos no encontrados |
| 4 | `madenat_lumber_costing/README.md` | **Media** | Propósito, dependencias, modelos, flujo de costeo multi-nivel |
| 5 | `madenat_lumber_purchasing/README.md` | **Media** | Propósito, dependencias, modelo de compras especializado |
| 6 | `madenat_lumber_shipping_core/README.md` | **Media** | Propósito, dependencias, modelos de transporte marítimo |
| 7 | `madenat_lumber_reports/README.md` | **Media** | Propósito como módulo de remapeo, dependencia de todos los módulos |
| 8 | `docs/GUIA_UPGRADE.md` | **Media** | Orden de update, flags, smoke tests, rollback |
| 9 | `CANON/04_DECISION_LOG.md` (actualizar) | **Media** | Apéndice: Estabilización Mayo-Junio 2026 |

---

## 6. VEREDICTO GENERAL DEL ESTADO ACTUAL DEL PROYECTO

### Estado: OPERATIVO CON DEUDA TÉCNICA CONTROLADA

**Lo que está bien:**
- La arquitectura de módulos es sólida, con un root centralizado y dependencias acíclicas bien definidas.
- La migración a Odoo 18 está completada al 95% (solo 4 view_mode tree residuales).
- El sistema de grupos y permisos a nivel modelo es consistente y bien granular.
- La documentación CANON es extensa y cubre decisiones arquitectónicas, flujos de negocio y guías de ejecución.
- Los domains y contexts de las acciones están correctamente ajustados para mostrar registros reales.
- La navegación ya fue estabilizada funcionalmente (confirmado por el contexto del proyecto).

**Lo que preocupa:**
- La ausencia de record rules es una vulnerabilidad de seguridad latente que debe atenderse antes de producción multi-usuario real.
- Billing es un módulo aislado del modelo de seguridad del resto del ecosistema.
- Los menús placeholder sin acciones (Contabilidad, Gerencia) generan una experiencia de usuario incompleta.
- La restricción `base.group_system` en Configuración contradice la existencia del grupo `group_lumber_config_manager`.

**Juicio final:** El proyecto está listo para uso interno controlado (admin + 1-2 usuarios de confianza). Para producción con múltiples roles reales (operaciones, costos, contabilidad, gerencia), se requiere completar los Sprints 1 y 2 definidos en las Recomendaciones Prioritarias. La deuda documental (Sprint 3) es importante pero no bloqueante para la operación.

---

*Informe generado por auditoría estática de código el 2026-06-06. No se realizaron modificaciones al código fuente.*