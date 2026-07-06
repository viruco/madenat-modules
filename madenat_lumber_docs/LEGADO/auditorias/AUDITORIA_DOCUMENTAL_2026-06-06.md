# AUDITORÍA DOCUMENTAL — ECOSISTEMA MADENAT LUMBER

**Versión:** 1.0  
**Fecha:** 2026-06-06  
**Auditor:** Arquitecto Técnico y Documental Senior  
**Base:** Auditoría Integral (AUDITORIA_INTEGRAL_2026-06-06.md) + Remediación Crítica (REMEDIACION_CRITICA_2026-06-06.md)  
**Método:** Inventario completo, clasificación, comparación con realidad del código, detección de obsolescencia  

---

## 1. RESUMEN EJECUTIVO

La documentación del ecosistema MADENAT Lumber es **extensa y bien estructurada** en sus capas CANON y WIKI, pero presenta **3 vacíos puntuales** y **1 documento activo que está desactualizado y contradice el código real**. No se requieren grandes reescrituras ni nuevos documentos masivos. Las correcciones necesarias son mínimas y focalizadas.

**Hallazgo crítico:** `WIKI/02_TECNICO/security_accesos.md` documenta solo 2 grupos y afirma que las ACLs no usan grupos custom. El código real tiene **7 grupos custom** y las ACLs **sí usan grupos custom**. Este documento debe actualizarse — es fuente de confusión para cualquier desarrollador nuevo.

**Recomendación principal:** 3 actualizaciones puntuales + 1 consolidación ligera. Cero documentos nuevos imprescindibles.

---

## 2. INVENTARIO DOCUMENTAL

### 2.1 Clasificación por propósito y vigencia

#### A) CANON — Documentación oficial de arquitectura (fuente de verdad)

| # | Documento | Propósito | Vigencia | Estado |
|---|-----------|-----------|----------|--------|
| 00 | `00_ARQUITECTURA.md` | Arquitectura general del ecosistema | Vigente | ✅ |
| 01 | `01_FLUJO_PACKING.md` | Flujo de packing/consolidación | Vigente | ✅ |
| 02 | `02_CONTINUIDAD.md` | Guía de continuidad para nuevos devs | Vigente | ✅ |
| 03 | `03_TESTS.md` | Estrategia y ejecución de tests | Vigente | ✅ |
| 04 | `04_DECISION_LOG.md` | Bitácora de decisiones | Vigente, pero incompleto | ⚠️ Falta apéndice estabilización Mayo-Junio 2026 |
| 05 | `05_BACKLOG.md` | Backlog de funcionalidades | Vigente | ✅ |
| 06 | `05_CONTINUIDAD_GLOBAL.md` | Continuidad global del proyecto | Vigente | ✅ |
| 07 | `06_CHECKLIST.md` | Checklist operativo | Vigente | ✅ |
| 08 | `07_TRABAJO_CON_IA.md` | Guía de trabajo con IA | Vigente | ✅ |
| 09 | `08_COSTEO.md` | Documentación de costeo | Vigente | ✅ |
| 10 | `09_FASE_DOCUMENTAL_MAESTRA.md` | Plan maestro documental | Vigente | ✅ |
| 11 | `10_AUDITORIA_MONETARIA_FASE_A.md` | Auditoría monetaria | Vigente | ✅ |
| 12 | `11_FASE_E_VALIDACION.md` | Validación final | Vigente | ✅ |
| 13 | `12_ARQUITECTURA_OPERATIVA_PERFILES.md` | Perfiles operativos | Vigente | ✅ |
| 14 | `13_ARQUITECTURA_TECNICA_IMPLEMENTACION.md` | Arquitectura técnica | Vigente | ✅ |
| 15 | `14_GUIA_EJECUCION_INCREMENTAL.md` | Guía de ejecución incremental | Vigente | ✅ |
| 16 | `15_DIAGNOSTICO_NAVEGACION_ACTUAL.md` | Diagnóstico de navegación | Vigente | ✅ |
| 17 | `INDICE_DOCUMENTACION.md` | Índice maestro | Vigente | ✅ |

**Veredicto CANON:** 18 documentos, todos vigentes. Solo `04_DECISION_LOG.md` requiere un apéndice con las decisiones de estabilización reciente.

#### B) WIKI — Documentación técnica y operativa de referencia

| # | Documento | Propósito | Vigencia | Estado |
|---|-----------|-----------|----------|--------|
| 18 | `00_INDICE.md` | Índice general WIKI | Vigente | ✅ |
| 19 | `GUIA_PRODUCCION_FINAL.md` | Guía de producción | Vigente | ✅ |
| 20 | `HOJA_RUTA_EJECUTIVA.md` | Hoja de ruta ejecutiva | Vigente | ✅ |
| 21 | `QUICK_START.md` | Inicio rápido | Vigente | ✅ |
| 22 | `01_NEGOCIO/` (7 docs) | Flujos de negocio, actores, reglas | Vigente | ✅ |
| 23 | `02_TECNICO/modelo_lotes.md` | Modelo de lotes | Vigente | ✅ |
| 24 | `02_TECNICO/modelo_recepciones.md` | Modelo de recepciones | Vigente | ✅ |
| 25 | `02_TECNICO/herencia_odoo_modelos.md` | Herencia de modelos | Vigente | ✅ |
| 26 | `02_TECNICO/dependencias_modulos.md` | Dependencias entre módulos | Vigente | ✅ |
| 27 | `02_TECNICO/configuracion_ingesta.md` | Configuración de ingesta | Vigente | ✅ |
| 28 | `02_TECNICO/arquitectura_ingesta_recepciones.md` | Arquitectura de ingesta | Vigente | ✅ |
| 29 | `02_TECNICO/validadores_checklist.md` | Validadores checklist | Vigente | ✅ |
| 30 | `02_TECNICO/campos_computados.md` | Campos computados | Vigente | ✅ |
| 31 | `02_TECNICO/gates_validacion.md` | Gates de validación | Vigente | ✅ |
| 32 | `02_TECNICO/modulo_lumber_core.md` | Documentación del módulo core | Vigente | ✅ |
| 33 | `02_TECNICO/servicio_lotes.md` | Servicio de lotes | Vigente | ✅ |
| 34 | `02_TECNICO/tracking_mail_thread.md` | Tracking mail thread | Vigente | ✅ |
| 35 | `02_TECNICO/modelo_despachos.md` | Modelo de despachos | Vigente | ✅ |
| 36 | **`02_TECNICO/security_accesos.md`** | **Seguridad y accesos** | **DESACTUALIZADO** | 🔴 **Crítico — ver sección 3.1** |
| 37 | `03_OPERACION/` (8 docs) | Comandos Docker, Odoo, PostgreSQL, despliegue | Vigente | ✅ |
| 38 | `04_DECISIONES/` (5 docs) | Decisiones arquitectónicas (DEC-001 a 005) | Vigente | ✅ |
| 39 | `05_INCIDENTES/` (5 docs) | Incidentes resueltos (INC-001 a 005) | Vigente | ✅ |
| 40 | `06_SESIONES/` | Plantillas de sesión | Vigente | ✅ |

#### C) Auditorías y Remediaciones (capa de control)

| # | Documento | Propósito | Vigencia | Estado |
|---|-----------|-----------|----------|--------|
| 41 | `AUDITORIA_2026-06-03.md` | Auditoría inicial | Superada por #44 | 📦 Histórico |
| 42 | `AUDITORIA_2026-06-04.md` | Auditoría de seguimiento | Superada por #44 | 📦 Histórico |
| 43 | `AUDITORIA_RUNTIME_2026-06-05.md` | Auditoría runtime | Superada por #44 | 📦 Histórico |
| 44 | `AUDITORIA_INTEGRAL_2026-06-06.md` | **Auditoría integral definitiva** | Vigente | ✅ Fuente de verdad |
| 45 | `REMEDIACION_CRITICA_2026-06-06.md` | **Remediación aplicada** | Vigente | ✅ Fuente de verdad |
| 46 | `AUDITORIA_MODULOS_COSTEO.md` | Auditoría específica de costing | Parcialmente superada | 📦 Histórico |
| 47 | `PRE_FASE_A_AUDITORIA_MODULOS.md` | Pre-auditoría | Superada | 📦 Histórico |

#### D) Planes tácticos y documentos de gestión (artefactos de sprint)

| # | Documento | Propósito | Vigencia | Estado |
|---|-----------|-----------|----------|--------|
| 48 | `PLAN_DEPURACION_PRIORIZADO.md` | Plan de depuración | Ejecutado | 📦 Histórico |
| 49 | `PLAN_ACCION_EJECUTABLE.md` | Plan de acción | Ejecutado | 📦 Histórico |
| 50 | `GUIA_OPERATIVA_IMPLEMENTACION.md` | Guía de implementación | Ejecutado | 📦 Histórico |
| 51 | `EJECUCION_FASE0.md` | Ejecución fase 0 | Ejecutado | 📦 Histórico |
| 52 | `MANDATO_EJECUCION.md` | Mandato de ejecución | Ejecutado | 📦 Histórico |
| 53 | `CIERRE_DF01_GUIA_REUNION.md` | Cierre de reunión | Puntual | 📦 Histórico |
| 54 | `ANALISIS_INTEGRAL_INVENTARIO_TRADERS.md` | Análisis de inventario | Vigente como referencia | ⚠️ Referencia |
| 55 | `P7_INVENTARIO_RESIDUOS.md` | Inventario de residuos | Vigente como referencia | ⚠️ Referencia |

#### E) Duplicados y respaldos (⚠️ riesgo de confusión)

| # | Ubicación | Contenido | Recomendación |
|---|-----------|-----------|---------------|
| 56 | `WIKI_BACKUP_20260530_1832/` | Copia completa de WIKI/ (≈60 archivos) | 🗑️ Archivar o eliminar — duplicado exacto |
| 57 | `RAW/legacy/LEGADO/` (12 docs) | Documentación legacy de auditorías anteriores | 🗑️ Ya archivado en RAW/ — mantener solo como referencia histórica |
| 58 | `RAW/legacy/LEGADO_EXTERNOS/` (2 docs) | Versiones antiguas de continuidad y backlog | 🗑️ Superado por CANON/ |
| 59 | `RAW/legacy/baks_modulos_activos_20260602/` | Backups de código (no documentación) | ⚠️ Fuera de lugar en docs/ — mover a _archive/ del módulo correspondiente |
| 60 | `LEGADO/` (3 docs) | Versiones antiguas de índice y decision log | 🗑️ Superado por CANON/ |
| 61 | `CONTEXT/` (2 docs) | Notas de contexto | ⚠️ Contenido mínimo — evaluar si aporta valor |
| 62 | `docs_nueva/` | Directorio vacío o con pocos archivos | 🗑️ Eliminar si está vacío |
| 63 | `backups/` (2 tar.gz) | Backups comprimidos | ✅ Mantener como respaldo |

---

## 3. VACÍOS DETECTADOS

### 3.1 🔴 CRÍTICO — `security_accesos.md` desactualizado

**Archivo:** `WIKI/02_TECNICO/security_accesos.md`

**Problema:**
El documento afirma:
- "La seguridad de MADENAT es minimalista: usa solo 2 grupos custom" → **Falso.** El código (`madenat_security.xml`) define 7 grupos: `group_madenat_cost_auditor`, `group_madenat_admin`, `group_lumber_config_manager`, `group_madenat_operaciones`, `group_madenat_costos`, `group_madenat_contabilidad`, `group_madenat_gerencia`.
- "No usan grupos custom; se basan en grupos estándar de Odoo" → **Falso.** El `ir.model.access.csv` de core, logistics y costing usa exclusivamente los grupos custom MADENAT (ops/costos/contab/gerencia).
- Las tablas de permisos por modelo muestran grupos nativos (`base.group_user`, `stock.group_stock_manager`) que ya no son los grupos reales en uso.

**Impacto:** Cualquier desarrollador nuevo o auditor que lea este documento tendrá una visión completamente errónea del modelo de seguridad real. Es el único documento de seguridad activo en WIKI.

**Recomendación:** Reescribir las secciones "Grupos de seguridad" y "Permisos de acceso" para reflejar el estado real del código. No requiere crear un documento nuevo — el archivo ya existe y tiene la estructura correcta; solo necesita actualización de contenido.

### 3.2 ⚠️ MEDIO — Sin mapa consolidado de navegación

**Problema:**
Los menús están distribuidos en 7 archivos XML (`lumber_core_menu.xml`, `logistics_menus.xml`, `costing_menus.xml`, `menu_remapping.xml`, `lumber_reports_menu.xml`, `lumber_purchase_menu.xml`, `toll_processing/menus.xml`, `lumber_billing_menu_data.xml`, `madenat_menus_por_perfil.xml`). No existe un solo documento que muestre el árbol completo de navegación con acciones, modelos y grupos.

`CANON/15_DIAGNOSTICO_NAVEGACION_ACTUAL.md` cubre el diagnóstico pero no incluye un mapa exhaustivo árbol-acción-grupo.

**Recomendación:** Agregar una sección "Mapa de Navegación" al final de `CANON/15_DIAGNOSTICO_NAVEGACION_ACTUAL.md` con el árbol indentado completo (no crear archivo nuevo). Este documento ya es el dueño natural del tema de navegación.

### 3.3 ⚠️ MEDIO — Sin guía de troubleshooting de errores conocidos

**Problema:**
Los errores ya enfrentados y resueltos durante la estabilización (menús invisibles por grupos, view_mode tree, actions vacías por domain/context, error de auto-dependencia en costing) no están documentados como guía de diagnóstico rápido. La WIKI tiene `05_INCIDENTES/` pero solo cubre 5 incidentes antiguos de infraestructura.

**Recomendación:** Agregar incidentes a `WIKI/05_INCIDENTES/` siguiendo la plantilla existente (`INC-006` a `INC-009`). No crear un archivo nuevo de troubleshooting — usar la infraestructura de incidentes ya establecida.

### 3.4 ℹ️ BAJO — README ausentes en 4 módulos

**Problema:**
`madenat_lumber_costing`, `madenat_lumber_purchasing`, `madenat_lumber_shipping_core`, `madenat_lumber_reports` no tienen README.md.

**Recomendación:** Crear README.md mínimo (5-10 líneas) en cada módulo con: propósito, dependencias, modelos principales. No es bloqueante.

---

## 4. RECOMENDACIONES DE COMPLEMENTO MÍNIMO

| # | Acción | Donde | Qué | Esfuerzo |
|---|--------|-------|-----|----------|
| 1 | **Actualizar seguridad** | `WIKI/02_TECNICO/security_accesos.md` | Reescribir secciones de grupos (7 en lugar de 2) y tabla de ACLs (grupos custom en lugar de nativos). Agregar nota sobre ausencia intencional de record rules y plan de taller pendiente. | 30 min |
| 2 | **Agregar mapa de navegación** | `CANON/15_DIAGNOSTICO_NAVEGACION_ACTUAL.md` (al final) | Árbol indentado con: menú → módulo → acción → modelo → grupos | 45 min |
| 3 | **Registrar incidentes de estabilización** | `WIKI/05_INCIDENTES/INC-006_tree_form.md` a `INC-009` | INC-006: view_mode tree en Odoo 18, INC-007: menú Configuración inaccesible, INC-008: noupdate en billing, INC-009: auto-dependencia costing | 30 min |
| 4 | **Actualizar Decision Log** | `CANON/04_DECISION_LOG.md` (apéndice) | Agregar sección "Estabilización Mayo-Junio 2026" con decisiones de remediación | 20 min |
| 5 | **READMEs pendientes** | 4 módulos sin README | README.md mínimo (propósito + dependencias + modelos) | 30 min |

**Total estimado:** ~3 horas. Cero documentos nuevos. Todo son actualizaciones sobre archivos existentes.

---

## 5. DOCUMENTOS QUE DEBEN CONSOLIDARSE

| Consolidación | Acción |
|---------------|--------|
| Auditorías 03, 04, runtime-05 → Integral 06 | Las 3 auditorías previas son iteraciones que culminaron en la integral. **Etiquetar como históricas** (agregar `[HISTÓRICO]` al inicio de cada una) y referenciar la integral como fuente definitiva. No eliminar — son trazabilidad. |
| Planes tácticos (PLAN_DEPURACION, PLAN_ACCION, GUIA_OPERATIVA, EJECUCION_FASE0, MANDATO_EJECUCION) | Fueron artefactos del sprint de estabilización. **Etiquetar como `[HISTÓRICO]`** y referenciar `REMEDIACION_CRITICA_2026-06-06.md` como cierre formal del ciclo. |

---

## 6. DOCUMENTOS QUE DEBEN MANTENERSE COMO HISTÓRICOS

| Documento | Motivo |
|-----------|--------|
| `AUDITORIA_2026-06-03.md` | Superada por integral |
| `AUDITORIA_2026-06-04.md` | Superada por integral |
| `AUDITORIA_RUNTIME_2026-06-05.md` | Superada por integral |
| `AUDITORIA_MODULOS_COSTEO.md` | Superada por integral |
| `PRE_FASE_A_AUDITORIA_MODULOS.md` | Superada por integral |
| `PLAN_DEPURACION_PRIORIZADO.md` | Sprint ejecutado |
| `PLAN_ACCION_EJECUTABLE.md` | Sprint ejecutado |
| `GUIA_OPERATIVA_IMPLEMENTACION.md` | Sprint ejecutado |
| `EJECUCION_FASE0.md` | Sprint ejecutado |
| `MANDATO_EJECUCION.md` | Sprint ejecutado |
| `CIERRE_DF01_GUIA_REUNION.md` | Evento puntual |

**Acción:** Agregar `[HISTÓRICO]` como prefijo en el título de cada uno o mover a un subdirectorio `historico/`. No eliminar.

---

## 7. DOCUMENTOS REDUNDANTES O FUERA DE LUGAR

| Documento/Ubicación | Problema | Recomendación |
|---------------------|----------|---------------|
| `WIKI_BACKUP_20260530_1832/` | Duplicado exacto de WIKI/ (~60 archivos) | Mover a `backups/` o eliminar. No aporta valor tener dos copias idénticas activas. |
| `RAW/legacy/baks_modulos_activos_20260602/` | Backups de código en directorio de documentación | Mover a `custom_addons/_archive/` |
| `LEGADO/` (raíz de docs) | Índices y resúmenes viejos | Mover a `RAW/legacy/` para consolidar todo el legado en un solo lugar |
| `docs_nueva/` | Directorio vacío o casi vacío | Eliminar si está vacío |
| `.bak` huérfanos en código | `__manifest__.py.bak.*`, `lumber_billing_menu_data.xml.bak.*` | Mover a `_archive/` o eliminar |

---

## 8. VEREDICTO SOBRE SI HACE FALTA CREAR NUEVA DOCUMENTACIÓN

**No hace falta crear ningún documento nuevo.**

La infraestructura documental existente (CANON 18 documentos + WIKI ~40 documentos) cubre todos los aspectos del proyecto. Los vacíos detectados se resuelven **actualizando documentos existentes**, no creando nuevos. La creación de nuevos documentos para seguridad, navegación o troubleshooting sería redundante porque ya existen los archivos contenedores correctos (`security_accesos.md`, `15_DIAGNOSTICO_NAVEGACION_ACTUAL.md`, `05_INCIDENTES/`).

**Lo único que falta es mantener actualizado lo que ya existe.**

---

## 9. PRÓXIMO PASO DOCUMENTAL RECOMENDADO

1. **Inmediato (hoy):** Actualizar `WIKI/02_TECNICO/security_accesos.md` para reflejar los 7 grupos reales y las ACLs con grupos custom. Es el vacío más peligroso porque induce a error técnico.
2. **Esta semana:** Agregar mapa de navegación a `CANON/15` + incidentes a `WIKI/05_INCIDENTES/` + apéndice a `CANON/04_DECISION_LOG.md`.
3. **Este mes:** Etiquetar documentos históricos, limpiar duplicados (`WIKI_BACKUP`, `LEGADO/`, `.bak`).
4. **Mantenimiento continuo:** Cada vez que se modifique un XML de seguridad, menús o acciones, actualizar el documento correspondiente en WIKI o CANON.

---

## 10. ESTRUCTURA DOCUMENTAL FINAL RECOMENDADA

```
madenat_lumber_docs/
├── CANON/                          ← Fuente de verdad arquitectónica (18 docs)
│   ├── 00_ARQUITECTURA.md
│   ├── ...
│   ├── 04_DECISION_LOG.md          ← Actualizar con apéndice estabilización
│   ├── 15_DIAGNOSTICO_NAVEGACION_ACTUAL.md ← Agregar mapa de menús al final
│   └── INDICE_DOCUMENTACION.md
├── WIKI/                           ← Referencia técnica y operativa
│   ├── 02_TECNICO/
│   │   └── security_accesos.md     ← ACTUALIZAR (crítico)
│   ├── 05_INCIDENTES/              ← Agregar INC-006 a INC-009
│   └── ...
├── AUDITORIA_INTEGRAL_2026-06-06.md    ← Fuente de verdad de auditoría
├── REMEDIACION_CRITICA_2026-06-06.md   ← Fuente de verdad de remediación
├── AUDITORIA_DOCUMENTAL_2026-06-06.md  ← Este documento
├── historico/                      ← Auditorías previas y planes ejecutados
│   ├── AUDITORIA_2026-06-03.md
│   ├── AUDITORIA_2026-06-04.md
│   ├── PLAN_DEPURACION_PRIORIZADO.md
│   └── ...
├── backups/                        ← Backups comprimidos
├── RAW/                            ← Material crudo y legacy (no activo)
└── CONTEXT/                        ← Notas efímeras (evaluar eliminación)
```

---

*Auditoría documental generada el 2026-06-06. No se crearon documentos nuevos. Todas las recomendaciones son actualizaciones sobre archivos existentes.*