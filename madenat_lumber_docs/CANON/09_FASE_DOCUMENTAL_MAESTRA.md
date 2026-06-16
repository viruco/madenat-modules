# FASE DOCUMENTAL MAESTRA — Consolidación, Checklist y Mapa Operativo

**Proyecto:** MADENAT Lumber — Odoo 18 CE
**Versión documental:** 1.1.0  <!-- actualizado: 2026-06-16 -->
**Fecha:** 2026-06-04
**Última revisión:** 2026-06-16
**Estado:** ACTIVO — Documento canónico de gobernanza documental
**Propósito:** Mapa maestro, checklist reutilizable, índice único y guía de continuidad para todas las fases del proyecto

---

## 1. RESUMEN EJECUTIVO

El proyecto MADENAT Lumber cuenta con **10 módulos Odoo activos** + 1 repositorio documental (`madenat_lumber_docs`), con una base operativa sólida, auditorías recientes completas y documentación canónica estructurada.

**Fortalezas:**
- Documentación CANON activa con 9 archivos, todos actualizados en 2026
- WIKI técnica con 9 documentos detallados cubriendo modelos, gates, servicios y arquitectura
- 3 auditorías exhaustivas completadas (2026-06-03, 2026-06-04, y auditoría de costeo)
- 3 análisis integrales (inventario traders, pre-fase A, inventario residuos)
- Base funcional operativa validada con suite T01–T33

**Debilidades (actualizado 2026-06-16):**
- 2 módulos principales sin CHANGELOG (costing, billing)
- Arquitectura monetaria: Fase A completada (17 campos Monetary en core), pendientes ~12 Float en costing/vendor_payment
- `madenat_guia_processing.py` cuenta con `test_guia_processing.py` (15 tests) desde TD-008
- Documento canónico de costeo `08_COSTEO.md` CREADO (2026-06-05, revisado 2026-06-16)
- `test_cost_distribution.py`, `test_landed_cost_integration.py`, `test_module_compatibility.py` creados para costing

**Veredicto:** El proyecto avanzó significativamente desde 2026-06-04. Fase A monetaria y Fase C tests están parcialmente completadas. Pendiente: validación en staging, deduction_factor Blank, deploy a producción.
<!-- actualizado: 2026-06-16 -->

---

## 2. MAPA MAESTRO DE MÓDULOS

### 2.1 Clasificación por rol

| Módulo | Rol | Categoría | Prioridad |
|--------|-----|-----------|-----------|
| `madenat_lumber_core` | Núcleo funcional | **NÚCLEO** | P0 |
| `madenat_lumber_costing` | Costeo multi-nivel | **COSTEO** | P1 |
| `madenat_lumber_logistics` | Contenedores y logística | **LOGÍSTICA** | P1 |
| `madenat_lumber_billing` | Facturación y consolidación | **CONTABILIDAD** | P1 |
| `madenat_lumber_purchasing` | Extensión de compras | **SOPORTE** | P2 |
| `madenat_lumber_shipping_core` | Booking y estructura base | **INFRAESTRUCTURA** | P2 |
| `madenat_lumber_reception_improvements` | Mejoras UI de recepción | **SOPORTE** | P2 |
| `madenat_toll_processing` | Procesamiento externo (maquila) | **LOGÍSTICA** | P2 |
| `madenat_vendor_payment` | Pagos a proveedores | **CONTABILIDAD** | P3 |
| `madenat_lumber_reports` | Meta-módulo de menús | **INFRAESTRUCTURA** | P3 |
| `madenat_lumber_docs` | Documentación (no es módulo Odoo) | **DOCUMENTACIÓN** | P0 |

### 2.2 Matriz de completitud

| Módulo | README | CHANGELOG | CANON | WIKI | Tests | Auditoría |
|--------|--------|-----------|-------|------|-------|-----------|
| `madenat_lumber_core` | ✅ | ✅ | ✅ | ✅ (7+) | ✅ | ✅ (3) |
| `madenat_lumber_costing` | ✅ | ❌ | ❌ | ❌ | ✅ | ⚠️ |
| `madenat_lumber_logistics` | ✅ | ✅ | ✅ | ✅ | ❌ | ⚠️ |
| `madenat_lumber_billing` | ✅ | ❌ | ❌ | ❌ | ✅ | ⚠️ |

<!-- actualizado: 2026-06-16 — costing README y tests existen -->
| `madenat_lumber_purchasing` | ❌ | ⚠️ | ❌ | ❌ | — | ⚠️ |
| `madenat_lumber_shipping_core` | ❌ | ❌ | ❌ | ⚠️ | — | — |
| `madenat_lumber_reception_improvements` | ✅ | ❌ | ❌ | ❌ | — | — |
| `madenat_toll_processing` | ✅ | ❌ | ❌ | ❌ | — | — |
| `madenat_vendor_payment` | ✅ | ❌ | ❌ | ❌ | — | — |
| `madenat_lumber_reports` | ❌ | ❌ | ❌ | ❌ | — | — |
| `madenat_lumber_docs` | N/A | N/A | ✅ | ✅ | N/A | N/A |

### 2.3 Participación monetaria

| Módulo | Campos Float | Campos Monetary | Estado | Acción requerida |
|--------|-------------|-----------------|--------|-----------------|
| `madenat_lumber_core` | 4 (tasas/%) | **17** | ✅ COMPLETADO (Fase A) | Migración realizada 2026-06-02 |
| `madenat_lumber_costing` | **9** | 0 | ⚠️ PARCIAL | Migrar a Monetary |

<!-- actualizado: 2026-06-16 — core migrado a 17 Monetary, 4 Float son tasas/porcentajes -->
| `madenat_lumber_billing` | 0 | 4 | ✅ CORRECTO | — |
| `madenat_lumber_logistics` | 0 | 2 | ✅ CORRECTO | — |
| `madenat_toll_processing` | 0 | 1 | ✅ CORRECTO | — |
| `madenat_vendor_payment` | 2 | 0 | ⚠️ PARCIAL | Migrar a Monetary |
| Otros módulos | 0 | 0 | N/A | — |

### 2.4 Participación en costeo/contabilidad

| Módulo | Define costos | Distribuye landed costs | Genera account.move | Genera stock.landed.cost |
|--------|--------------|------------------------|---------------------|--------------------------|
| `madenat_lumber_core` | ✅ | ❌ | ❌ | ❌ |
| `madenat_lumber_costing` | ✅ | ✅ | ❌ | ❌ |
| `madenat_lumber_billing` | ❌ | ❌ | ✅ | ❌ |
| `madenat_lumber_logistics` | ❌ | ⚠️ (deprecated) | ❌ | ❌ |
| Otros módulos | ❌ | ❌ | ❌ | ❌ |

---

## 3. ESTADO DOCUMENTAL

### 3.1 Documentación CANON (fuente de verdad)

| Archivo | Versión | Fecha | Estado | Verificado |
|---------|---------|-------|--------|------------|
| `INDICE_DOCUMENTACION.md` | 8.0.0 | 2026-06-02 | ACTIVO | ✅ Leído |
| `00_ARQUITECTURA.md` | 7.0.0 | 2026-05-28 | CANÓNICO | ✅ Leído |
| `02_CONTINUIDAD.md` | 8.0.0 | 2026-06-02 | ACTIVO | ✅ Leído |
| `03_TESTS.md` | 6.4.0 | 2026-06-02 | ACTIVO | ✅ Leído |
| `04_DECISION_LOG.md` | 6.2.0 | 2026-05-23 | CANÓNICO | ✅ Leído |
| `05_BACKLOG.md` | 6.3.0 | 2026-05-23 | ACTIVO | ✅ Leído |
| `06_CHECKLIST.md` | 4.1.0 | 2026-05-23 | ACTIVO | ✅ Leído |
| `07_TRABAJO_CON_IA.md` | 7.1.0 | 2026-05-28 | ACTIVO | ✅ Leído |

### 3.2 Documentos CANON referenciados pero no verificados en disco

| Archivo | Referenciado en | Estado |
|---------|----------------|--------|
| `01_FLUJO_PACKING.md` | `INDICE_DOCUMENTACION.md`, `07_TRABAJO_CON_IA.md` | ⚠️ No verificado |
| `05_CONTINUIDAD_GLOBAL.md` | VSCode tabs | ⚠️ Existe como archivo pero NO listado en `INDICE_DOCUMENTACION.md` |
| `08_COSTEO.md` | `AUDITORIA_MODULOS_COSTEO.md` (como faltante) | ✅ CREADO 2026-06-05, revisado 2026-06-16 |

<!-- actualizado: 2026-06-16 -->
| `GUIA_PRODUCCION_FINAL.md` | `07_TRABAJO_CON_IA.md` | ⚠️ No verificado |
| `HOJA_RUTA_EJECUTIVA.md` | `07_TRABAJO_CON_IA.md` | ⚠️ No verificado |
| `QUICK_START.md` | `07_TRABAJO_CON_IA.md`, `INDICE_DOCUMENTACION.md` | ⚠️ No verificado |

### 3.3 Documentación WIKI técnica

| Archivo | Estado | Verificado |
|---------|--------|------------|
| `modelo_lotes.md` | ✅ Completo (299 líneas) | ✅ Leído |
| `modelo_recepciones.md` | ✅ Completo | ⚠️ No leído (referenciado) |
| `gates_validacion.md` | ✅ Completo (439 líneas) | ✅ Leído |
| `servicio_lotes.md` | ✅ Completo (396 líneas) | ✅ Leído |
| `validadores_checklist.md` | ✅ Completo | ⚠️ No leído (referenciado) |
| `configuracion_ingesta.md` | ✅ Completo (331 líneas) | ✅ Leído |
| `arquitectura_ingesta_recepciones.md` | ✅ Completo | ⚠️ No leído (referenciado) |
| `herencia_odoo_modelos.md` | ✅ Completo | ⚠️ No leído (referenciado) |
| `dependencias_modulos.md` | ✅ Completo (228 líneas) | ✅ Leído |

### 3.4 Auditorías y análisis

| Archivo | Líneas | Fecha | Estado |
|---------|--------|-------|--------|
| `AUDITORIA_2026-06-03.md` | 267 | 2026-06-03 | ✅ Leído — 10 módulos, 3 críticos, 5 medios, 8 menores |
| `AUDITORIA_2026-06-04.md` | 318 | 2026-06-04 | ✅ Leído — Deep dive `madenat_guia_processing` (3465 líneas) |
| `AUDITORIA_MODULOS_COSTEO.md` | 485 | 2026-06-04 | ✅ Leído — 11 módulos, matriz monetaria, gaps costeo |
| `ANALISIS_INTEGRAL_INVENTARIO_TRADERS.md` | — | — | ⚠️ No leído |
| `PRE_FASE_A_AUDITORIA_MODULOS.md` | — | — | ⚠️ No leído |
| `P7_INVENTARIO_RESIDUOS.md` | — | — | ⚠️ No leído |

### 3.5 Documentos huérfanos, duplicados o mal ubicados

| Archivo | Ubicación actual | Ubicación correcta | Acción |
|---------|-----------------|-------------------|--------|
| `ROADMAP.md` | `madenat_lumber_core/models/` | `CANON/` o `WIKI/` | Mover |
| `models/0` | `madenat_lumber_core/models/` | Eliminar | Archivo huérfano |
| `05_CONTINUIDAD_GLOBAL.md` | `CANON/` | Debe estar en `INDICE_DOCUMENTACION.md` | Agregar al índice |
| `backups/fase1_20260602_211431/` | `madenat_lumber_core/` | Fuera del repositorio | Mover |
| `docker-compose.yml.bak.*` | Raíz del proyecto | Fuera del repositorio | Mover |
| `costing_menus.xml` comentado | `madenat_lumber_costing/__manifest__.py` | Documentar razón | Agregar comentario |
| Código `# ⚠️ TEMPORAL` | `stock_lot.py:577` | Resolver o crear ticket | Acción |
| `lumber_consolidation_import_wizard.py` | `madenat_lumber_logistics/wizards/` | `_archive/` | Mover (dead code) |

---

## 4. CHECKLIST MAESTRO

Este checklist reemplaza y extiende el existente `06_CHECKLIST.md` (v4.1.0). Es el contrato interno de trabajo para cualquier sesión de ingeniería en el proyecto MADENAT.

### A. INVESTIGACIÓN

- [ ] A.1 Leer `CANON/02_CONTINUIDAD.md` para conocer estado actual y punto de retoma
- [ ] A.2 Leer `CANON/05_BACKLOG.md` para confirmar task activa y prioridad
- [ ] A.3 Revisar `git status` y `git diff` para entender cambios no commiteados
- [ ] A.4 Revisar `git log --oneline -10` para contexto de commits recientes
- [ ] A.5 Confirmar BD objetivo, rama, contenedores Docker activos
- [ ] A.6 Verificar que el módulo instala/actualiza sin errores de registry
- [ ] A.7 Leer documentación WIKI relevante al cambio (modelos, gates, servicios implicados)
- [ ] A.8 Leer auditorías relevantes para entender deuda técnica preexistente
- [ ] A.9 Identificar todos los archivos que toca el cambio (código, vistas, datos, tests, docs)
- [ ] A.10 Confirmar que el foco de la sesión es único (no abrir múltiples frentes mayores)

### B. DEPENDENCIAS

- [ ] B.1 Identificar qué módulos Odoo dependen del cambio (`__manifest__.py` → `depends`)
- [ ] B.2 Identificar qué modelos ORM son impactados (`_inherit`, `_name`, relaciones Many2one/One2many)
- [ ] B.3 Verificar `@api.depends` y campos `store=True` que puedan invalidarse
- [ ] B.4 Identificar vistas XML, wizards y acciones de ventana relacionados
- [ ] B.5 Verificar impacto en costeo (`stock.lot.cost.line`, `total_cost_usd`, `cost_per_m3_usd`)
- [ ] B.6 Verificar impacto en contabilidad (`account.move`, `stock.valuation.layer`)
- [ ] B.7 Verificar imports Python: solo imports relativos intra-addon (`from .utils_uom import ...`)
- [ ] B.8 Confirmar que no se introducen imports absolutos entre addons (regla HF-001)
- [ ] B.9 Revisar constantes: usar `utils_uom.py` como fuente única, nunca literales como `25.4`
- [ ] B.10 Verificar que no se duplica lógica existente en otro archivo/módulo

### C. IMPLEMENTACIÓN

- [ ] C.1 Aplicar el cambio mínimo necesario (regla AD-24: solución mínima antes que refactor amplio)
- [ ] C.2 No duplicar lógica de negocio (parser, cálculos, validaciones)
- [ ] C.3 No romper trazabilidad (snapshots SHA-256, audit_log, lot_name)
- [ ] C.4 No modificar `stock` core de Odoo sin necesidad extrema documentada
- [ ] C.5 No añadir dependencias a nuevos módulos Odoo sin justificación explícita
- [ ] C.6 Campos nuevos deben tener `string`, `help`, y tipo correcto (`Monetary` si es dinero)
- [ ] C.7 Usar `fields.Monetary(currency_field='currency_id')` para TODO campo de costo/precio/monto
- [ ] C.8 Mantener coherencia de naming entre Python, XML, tests y documentación (regla AD-17)
- [ ] C.9 Actualizar `__manifest__.py` si se agregan nuevos archivos (vistas, datos, security)
- [ ] C.10 Actualizar `security/ir.model.access.csv` si se crean nuevos modelos
- [ ] C.11 `length` siempre en metros como fuente de verdad. `lengthinputraw` preserva entrada humana
- [ ] C.12 Sin writes en Gate 0, Gate 1, Gate 2. Solo Gate 3 escribe inventario
- [ ] C.13 Sin fallback silencioso para tipo de cambio (regla AD-05)
- [ ] C.14 Sin SQL raw en producción

### D. VALIDACIÓN

- [ ] D.1 Probar flujo principal del cambio (happy path completo)
- [ ] D.2 Probar regresión visual (vistas XML sin errores, menús accesibles)
- [ ] D.3 Probar impacto en costeo (totales, cost_per_m3, cost_line_ids)
- [ ] D.4 Probar impacto en contabilidad (si aplica: account.move, valorización)
- [ ] D.5 Revisar logs del contenedor (`docker logs odoo18_app`) para warnings/errores
- [ ] D.6 Probar casos borde: nulos, vacíos, valores extremos, unidades mixtas
- [ ] D.7 Verificar que el módulo actualiza sin error de registry
- [ ] D.8 Si el cambio toca `utils_uom.py` → golden records: A1M2605458=4.893, A1M2602536=4.832
- [ ] D.9 Ejecutar tests existentes: `test_lumber_reception.py`, `test_billing_consolidation.py`
- [ ] D.10 Si se crearon nuevos tests, ejecutarlos y verificar que pasan

### E. DOCUMENTACIÓN

- [ ] E.1 Actualizar `CANON/04_DECISION_LOG.md` si el cambio constituye una decisión arquitectónica
- [ ] E.2 Actualizar `CANON/02_CONTINUIDAD.md` con nuevo estado, riesgos y punto de retoma
- [ ] E.3 Actualizar `CANON/03_TESTS.md` si se agregan/cierran casos de prueba
- [ ] E.4 Actualizar `CANON/05_BACKLOG.md` si se completa/agrega/reprioriza una tarea
- [ ] E.5 Actualizar `WIKI/` si el cambio afecta flujos técnicos documentados
- [ ] E.6 Actualizar `CHANGELOG.md` del módulo modificado (si no existe, considerar crearlo)
- [ ] E.7 Actualizar `CANON/00_ARQUITECTURA.md` si cambian modelos, campos, constraints o gates
- [ ] E.8 Actualizar `CANON/INDICE_DOCUMENTACION.md` si se crean/eliminan documentos canónicos
- [ ] E.9 Registrar deuda técnica, límites conocidos y riesgos en `02_CONTINUIDAD.md`
- [ ] E.10 No dejar documentación huérfana: todo doc nuevo debe estar enlazado desde el índice

### F. COMMIT Y DEPLOY

- [ ] F.1 Commit limpio: archivos relacionados en un solo commit, sin artefactos
- [ ] F.2 Mensaje de commit claro: `[Módulo] Descripción breve del cambio`
- [ ] F.3 Referencia a decisión/hotfix/fix en el mensaje si aplica (AD-XX, HF-XXX, TD-XXX)
- [ ] F.4 Verificar `git status` limpio (sin archivos huérfanos, backups, `.pyc`)
- [ ] F.5 Verificar que el árbol de dependencias no se rompe (módulo instala con `--stop-after-init`)
- [ ] F.6 Desplegar en ambiente TEST primero
- [ ] F.7 Validar en TEST: flujo funcional, regresión, logs limpios
- [ ] F.8 Si TEST pasa → deploy a PRODUCCIÓN
- [ ] F.9 Validación post-deploy: monitorear logs, verificar KPIs
- [ ] F.10 Actualizar `02_CONTINUIDAD.md` con resultado del deploy

---

## 5. HUECOS Y RIESGOS

### 5.1 Documentos faltantes (priorizados)

| Prioridad | Documento | Justificación |
|-----------|-----------|---------------|
| **ALTA** | `CANON/08_COSTEO.md` | ✅ CREADO 2026-06-05 — Flujo canónico de costeo end-to-end documentado. Revisado 2026-06-16. |
| **ALTA** | `WIKI/02_TECNICO/costeo_distribucion.md` | El motor `lumber.cost.distribution` (315 líneas, 6 métodos de prorrateo) no tiene documentación técnica. |
| **ALTA** | `README.md` para `madenat_lumber_costing` | ✅ EXISTE — verificado en disco 2026-06-16. |
| **ALTA** | `CHANGELOG.md` para `madenat_lumber_costing` | Sin trazabilidad de cambios. |

<!-- actualizado: 2026-06-16 — 08_COSTEO creado, README costing existe -->
| **MEDIA** | `WIKI/02_TECNICO/flujo_devoluciones.md` | Sin documentación de devoluciones. |
| **MEDIA** | `WIKI/02_TECNICO/troubleshooting.md` | Sin guía de errores comunes y diagnóstico. |
| **MEDIA** | `README.md` para `madenat_lumber_shipping_core` | Infraestructura sin README. |
| **BAJA** | `README.md` para `madenat_lumber_purchasing` | Soporte sin README. |
| **BAJA** | `README.md` para `madenat_lumber_reports` | Meta-módulo sin README. |
| **BAJA** | `CHANGELOG.md` para `madenat_lumber_billing`, `toll_processing`, `reception_improvements`, `vendor_payment` | Sin trazabilidad de cambios. |

### 5.2 Documentos mal ubicados

| Documento | Ubicación actual | Ubicación correcta |
|-----------|-----------------|-------------------|
| `ROADMAP.md` | `madenat_lumber_core/models/` | `CANON/` o `WIKI/02_TECNICO/` |
| `05_CONTINUIDAD_GLOBAL.md` | `CANON/` (existe pero no indexado) | Indexar en `INDICE_DOCUMENTACION.md` |

### 5.3 Documentos duplicados o redundantes

No se detectó duplicación significativa entre documentos canónicos. Cada documento CANON tiene responsabilidad única (AD-18). La WIKI complementa sin solapar.

**Excepción:** La lógica de delete de stock moves está duplicada idénticamente entre `lumber_reception.py:2559-2573` y `reception_service.py:126-137`. Esto es deuda de código, no documental.

### 5.4 Riesgos activos consolidados

| ID | Riesgo | Severidad | Fuente | Acción |
|----|--------|-----------|--------|--------|
| R-01 | 30 campos Float monetarios sin migrar a Monetary | 🟡 MEDIO (Fase A completa en core) | Auditoría 06-03, Auditoría Costeo | Migrar costing + vendor_payment |
| R-02 | `madenat_guia_processing.py` sin tests (3465 líneas) | 🟡 MEDIO | Auditoría 06-04 | ✅ `test_guia_processing.py` creado (15 tests, TD-008) |
| R-03 | Campos duplicados en `MadenatGuiaProcessing` (4 campos shadowed) | 🟡 MEDIO | Auditoría 06-04 | Resuelto en TD-007 (duplicados eliminados) |

<!-- actualizado: 2026-06-16 — R-01 Fase A completa, R-02 tests existen, R-03 resuelto -->
| R-04 | Constraint `stock_lot_check_cost_positive` inefectiva | 🟡 MEDIO | CANON 02, Backlog | Revisar modelo |
| R-05 | `_deprecated_action_distribute_costs` bypassea `cost_line_ids` | 🟡 MEDIO | Auditoría Costeo | Redirigir a cost_line_ids |
| R-06 | Monolito parcial en `lumber_reception.py` | 🟡 MEDIO | CANON 00, Backlog | Refactor futuro |
| R-07 | Archivo huérfano `models/0` | 🟢 BAJO | Auditoría 06-03 | Eliminar |
| R-08 | Backups en repositorio | 🟢 BAJO | Auditoría 06-03 | Mover fuera |
| R-09 | `costing_menus.xml` comentado sin documentar | 🟢 BAJO | Auditoría 06-03 | Documentar |
| R-10 | Código `# ⚠️ TEMPORAL` en `stock_lot.py:577` | 🟢 BAJO | Auditoría 06-03 | Resolver |

---

## 6. ÍNDICE DOCUMENTAL RECOMENDADO

### Punto de entrada

```
CANON/INDICE_DOCUMENTACION.md  ←  ÚNICO PUNTO DE ENTRADA
```

Cualquier persona que llegue al proyecto debe empezar aquí. Este archivo referencia todos los demás.

### Estructura jerárquica

```
madenat_lumber_docs/
│
├── CANON/                          ← FUENTE DE VERDAD (documentos que dictan reglas)
│   ├── INDICE_DOCUMENTACION.md     ← Mapa maestro de todos los documentos
│   ├── 00_ARQUITECTURA.md          ← Arquitectura, modelos, gates, campos, restricciones
│   ├── 01_FLUJO_PACKING.md         ← Flujo funcional de packing y estados
│   ├── 02_CONTINUIDAD.md           ← Checkpoint técnico vivo. Estado actual, riesgos, retoma
│   ├── 03_TESTS.md                 ← Matriz de validación funcional y técnica
│   ├── 04_DECISION_LOG.md          ← Decisiones de arquitectura, naming, cálculo, operación
│   ├── 05_BACKLOG.md               ← Backlog canónico priorizado por fases
│   ├── 06_CHECKLIST.md             ← Checklist operativo de sesión (LEGACY — ahora usar 09)
│   ├── 07_TRABAJO_CON_IA.md        ← Protocolo de trabajo con IA
│   ├── 08_COSTEO.md                ← [PENDIENTE CREAR] Flujo canónico de costeo end-to-end
│   └── 09_FASE_DOCUMENTAL_MAESTRA.md ← ESTE DOCUMENTO — Mapa maestro consolidado
│
├── WIKI/                           ← SOPORTE TÉCNICO (documentos que explican cómo)
│   └── 02_TECNICO/
│       ├── modelo_lotes.md         ← Documentación de stock.lot extendido
│       ├── modelo_recepciones.md   ← Documentación de lumber.reception
│       ├── gates_validacion.md     ← Pipeline de validación (Gate 0–3)
│       ├── servicio_lotes.md       ← LumberReceptionService
│       ├── validadores_checklist.md ← ValidationChecklistMixin (7 validadores)
│       ├── configuracion_ingesta.md ← Arquitectura Fase 1+2+3 de configuración
│       ├── arquitectura_ingesta_recepciones.md ← Flujo de ingesta de recepciones
│       ├── herencia_odoo_modelos.md ← Patrones de herencia en modelos Odoo
│       ├── dependencias_modulos.md  ← Árbol de dependencias entre módulos
│       └── [costeo_distribucion.md] ← [PENDIENTE] Motor de distribución de costos
│
├── AUDITORIA_2026-06-03.md         ← Auditoría general de 10 módulos
├── AUDITORIA_2026-06-04.md         ← Auditoría profunda de madenat_guia_processing
├── AUDITORIA_MODULOS_COSTEO.md     ← Auditoría de costeo y base monetaria (11 módulos)
├── ANALISIS_INTEGRAL_INVENTARIO_TRADERS.md ← Análisis integral de inventario
├── PRE_FASE_A_AUDITORIA_MODULOS.md ← Auditoría pre-Fase A
├── P7_INVENTARIO_RESIDUOS.md       ← Inventario de residuos
│
├── LEGADO/                         ← Material histórico (no usar como fuente principal)
├── RAW/                            ← Datos brutos de análisis
├── CONTEXT/                        ← Redirige a CANON (sin contenido canónico propio)
├── backups/                        ← Backups de documentación
└── docs_nueva/                     ← Documentación en migración
```

### Criterio de verdad ante contradicción

1. Documento canónico del tema en `CANON/`
2. `CANON/04_DECISION_LOG.md`
3. `CANON/02_CONTINUIDAD.md`
4. Código fuente (para verdad funcional)
5. Histórico solo como evidencia contextual

### Responsabilidad de cada tipo de documento

| Tipo | Propósito | Ejemplos | ¿Quién lo escribe? |
|------|-----------|----------|-------------------|
| **CANON** | Dicta reglas, decisiones, arquitectura | 00–09 | Arquitecto / Tech Lead |
| **WIKI** | Explica cómo funciona técnicamente | modelo_lotes, gates_validacion | Desarrollador / Tech Lead |
| **Auditoría** | Evidencia de revisión y hallazgos | AUDITORIA_*.md | Auditor (puede ser IA) |
| **Análisis** | Investigación profunda de un tema | ANALISIS_*.md | Ingeniero / Consultor |
| **README** | Onboarding rápido del módulo | README.md | Desarrollador del módulo |
| **CHANGELOG** | Trazabilidad de cambios del módulo | CHANGELOG.md | Desarrollador |
| **CONTEXT** | Redirige a CANON | — | Automático |
| **LEGADO** | Archivo histórico | — | Cualquiera (solo mover, no crear) |

---

## 7. ORDEN DE TRABAJO FUTURO

Basado en el análisis de lo que ya existe, el estado de cada módulo y las dependencias entre ellos, este es el orden recomendado para futuras fases:

### Fase A: Saneamiento monetario (PRIORIDAD 0) — PARCIALMENTE COMPLETADA

**Objetivo:** Unificar la base monetaria del proyecto migrando `fields.Float` → `fields.Monetary`.

1. ✅ `madenat_lumber_core` → Agregado `currency_id` a `stock.lot`. Migrados 17 campos Float a Monetary (Fase A, 2026-06-02). Corregido `cost_per_m3_usd`. Ver `08_COSTEO.md` sección 2.1.
2. ⏳ `madenat_lumber_costing` → 9 campos Float pendientes de migrar a Monetary. README existe. CHANGELOG pendiente.
3. ⏳ `madenat_lumber_logistics` → Redirigir `_deprecated_action_distribute_costs` a `cost_line_ids`.
4. ⏳ `madenat_lumber_billing` → Adaptar lectura de `wood_cost_usd` (ya compatible via Monetary).
5. ⏳ `madenat_vendor_payment` → Migrar `amount_total`, `amount_paid` a Monetary.
6. ✅ Crear `CANON/08_COSTEO.md` — CREADO 2026-06-05, revisado 2026-06-16.
7. ⏳ Crear `WIKI/02_TECNICO/costeo_distribucion.md` — pendiente.

<!-- actualizado: 2026-06-16 — Fase A completada en core -->

**Justificación:** Sin base monetaria unificada, cualquier integración contable futura (account.move, stock.landed.cost) será frágil e inconsistente. Core es P0 porque 8 de los 11 módulos dependen de él.

### Fase B: Estabilización técnica (PRIORIDAD 1)

**Objetivo:** Cerrar deuda técnica crítica identificada en auditorías.

1. Limpiar campos duplicados en `madenat_guia_processing.py` (4 campos shadowed).
2. Eliminar método duplicado `_validar_y_enriquecer_lineas`.
3. Eliminar archivo huérfano `models/0`.
4. Mover `ROADMAP.md` de `models/` a `CANON/`.
5. Resolver comentario `# ⚠️ TEMPORAL` en `stock_lot.py:577`.
6. Documentar `costing_menus.xml` comentado.
7. Corregir `mm_to_inch()` en `utils_uom.py` para usar `MM_PER_INCH`.
8. Refactorizar hardcodes `25.4` en `lumber_shipment_line.py` y `lumber_reception_mass_update.py`.

**Justificación:** Estos son bugs y artefactos que crecen con el tiempo. Resolverlos temprano evita que se conviertan en bloqueantes.

### Fase C: Cobertura de tests (PRIORIDAD 1) — PARCIALMENTE COMPLETADA

**Objetivo:** Crear tests unitarios para los módulos sin cobertura.

1. ✅ `test_guia_processing.py` → CREADO (15 tests, TD-008). Cubre state machine, cancel, unlink, volúmenes, TD-007 duplicados.
2. ✅ `test_cost_distribution.py` → CREADO (5 tests, C2.1–C2.5). Motor de prorrateo con tests.
3. ✅ `test_landed_cost_integration.py` → CREADO (5 tests, C3.1–C3.5).
4. ✅ `test_module_compatibility.py` → CREADO (6 tests, C4.1–C4.6).
5. ✅ `test_length_uom_and_subproducto.py` → CREADO (4 tests, T29–T32 automatizados). Pendiente evidencia formal en staging.
6. ⏳ `test_logistics.py` → Contenedores sin tests.

<!-- actualizado: 2026-06-16 — suites C2-C4 y guia_processing existen -->

**Justificación:** Sin tests automatizados, cualquier refactor o fix puede romper flujos críticos sin ser detectado hasta producción.

### Fase D: Integración contable (PRIORIDAD 2)

**Objetivo:** Extender la trazabilidad financiera hacia `account.move` y `stock.landed.cost`.

1. Integrar `cost_line_ids` → `stock.landed.cost` en `madenat_lumber_costing`.
2. Generar `stock.valuation.layer` para trazabilidad de valorización.
3. Vincular `lumber.billing.consolidation` → `account.move` con asientos contables correctos.
4. Extender `madenat_vendor_payment` para conciliación con `account.payment`.

**Justificación:** Esta fase depende de que la Fase A esté completa (Monetary). Sin Monetary, la integración contable producirá errores de precisión.

### Fase E: Refactor modular (PRIORIDAD 2)

**Objetivo:** Completar la separación del monolito.

1. Separar `MadenatGuiaProcessingLine` a archivo propio (~700 líneas).
2. Separar `LumberReceptionLine` a archivo propio (Fase 4 del backlog).
3. Unificar parseo Excel/PDF en `MadenatReceptionParser` (eliminar duplicación).
4. Migrar `LUMBER_DIMENSION_MAP` a modelos Fase 2.

**Justificación:** El refactor reduce riesgo de merge conflicts, facilita tests unitarios y mejora mantenibilidad. No es urgente pero sí necesario para escalar el equipo.

### Fase F: UX, reportes y documentación satélite (PRIORIDAD 3)

**Objetivo:** Pulir experiencia de usuario y completar documentación periférica.

1. Completar README + CHANGELOG en módulos faltantes.
2. Crear `WIKI/02_TECNICO/flujo_devoluciones.md`.
3. Crear `WIKI/02_TECNICO/troubleshooting.md`.
4. Limpiar `docs_nueva/` y `RAW/` (mover a LEGADO o eliminar).
5. Mover backups fuera del repositorio.
6. Indexar `05_CONTINUIDAD_GLOBAL.md` en `INDICE_DOCUMENTACION.md`.

---

## 8. RECOMENDACIONES FINALES

### 8.1 Gobernanza documental

1. **Adoptar este documento (`09_FASE_DOCUMENTAL_MAESTRA.md`) como checklist canónico.** El `06_CHECKLIST.md` v4.1.0 queda como referencia legacy; este documento lo reemplaza en la práctica.
2. **Actualizar `INDICE_DOCUMENTACION.md`** para incluir: `05_CONTINUIDAD_GLOBAL.md` (si se confirma que es canónico), `08_COSTEO.md` (cuando se cree), `09_FASE_DOCUMENTAL_MAESTRA.md`.
3. **No crear documentos paralelos.** Si un tema ya tiene dueño canónico, actualizar ese archivo (regla AD-19, DEC-2026-05-23-DOC-01).
4. **Cerrar cada sesión con documentación actualizada** (regla AD-25).

### 8.2 Reglas de ingeniería no negociables

1. **NUNCA** usar `from madenat_lumber_core.models...` desde otro addon (HF-001).
2. **NUNCA** usar literales para constantes de conversión (`25.4`, `0.3048`). Usar `utils_uom.py`.
3. **NUNCA** dejar `fields.Float` para dinero. Usar `fields.Monetary(currency_field='currency_id')`.
4. **NUNCA** escribir inventario fuera de Gate 3.
5. **NUNCA** hacer fallback silencioso para tipo de cambio.

### 8.3 Prioridad de ejecución

Si solo se puede hacer UNA cosa en la próxima fase:
→ **Migrar `stock.lot` a `fields.Monetary`** (Fase A, paso 1).

Es el cambio de mayor impacto y habilita todas las integraciones contables futuras. Todo lo demás puede esperar.

---

## 9. ARCHIVOS CREADOS O ACTUALIZADOS

| Archivo | Acción | Descripción |
|---------|--------|-------------|
| `CANON/09_FASE_DOCUMENTAL_MAESTRA.md` | **CREADO** | Documento consolidado con mapa maestro, checklist canónico, huecos, riesgos, índice documental recomendado y orden de trabajo futuro |

---

## 10. COMMIT(S) REALIZADOS

*Esta sección se completa al hacer commit de este documento.*

```bash
git add custom_addons/madenat_lumber_docs/CANON/09_FASE_DOCUMENTAL_MAESTRA.md
git commit -m "[DOCS] Fase Documental Maestra: consolidación, checklist y mapa operativo

- Creado CANON/09_FASE_DOCUMENTAL_MAESTRA.md v1.0.0
- Mapa maestro de 11 módulos con roles, completitud y estado monetario
- Checklist maestro canónico con 6 secciones (A-F) y 49 ítems
- Identificados 10 documentos faltantes priorizados
- Identificados 10 riesgos activos consolidados
- Índice documental jerárquico recomendado
- Orden de trabajo futuro: Fase A (monetario) → F (UX/docs)
- Basado en lectura completa de: 8 CANON, 9 WIKI, 3 auditorías, manifiesto core"
```

---

## APÉNDICE A: Referencias rápidas

### Comandos esenciales

```bash
# Update de módulo con tests
docker exec -it odoo18_app bash -lc "odoo -u madenat_lumber_core -d madenattest --db_host=db --db_user=odoo --db_password=odoo --xmlrpc-port=8072 --test-enable --stop-after-init --log-level=test"

# Verificar git status
git status && git log --oneline -10

# Buscar hardcodes de constantes
grep -rn "25\.4" custom_addons/ --include="*.py" | grep -v utils_uom.py | grep -v "# ver utils_uom"
grep -rn "0\.3048" custom_addons/ --include="*.py" | grep -v utils_uom.py

# Buscar imports absolutos entre addons (HF-001)
grep -rn "from madenat_lumber_" custom_addons/ --include="*.py"

# Buscar fields.Float para dinero (potencial deuda Monetary)
grep -rn "fields\.Float.*usd\|fields\.Float.*clp\|fields\.Float.*cost\|fields\.Float.*price\|fields\.Float.*amount" custom_addons/ --include="*.py"
```

### Documentos que DEBEN leerse al inicio de cada sesión

1. `CANON/02_CONTINUIDAD.md` — Estado actual y punto de retoma
2. `CANON/05_BACKLOG.md` — Tarea activa y prioridad
3. `CANON/09_FASE_DOCUMENTAL_MAESTRA.md` — Este documento (checklist y reglas)

### Documentos que DEBEN actualizarse al cierre de cada sesión

1. `CANON/02_CONTINUIDAD.md` — Nuevo estado y próximos 3 pasos
2. `CANON/04_DECISION_LOG.md` — Si se tomó una decisión arquitectónica
3. `CANON/05_BACKLOG.md` — Si se completó/agregó una tarea
4. `CHANGELOG.md` del módulo modificado

---

*Documento generado el 2026-06-04 como parte de la Fase Documental Maestra.*
*Basado en lectura y análisis de 8 documentos CANON, 9 documentos WIKI, 3 auditorías, manifiestos de 10 módulos y árbol de dependencias.*