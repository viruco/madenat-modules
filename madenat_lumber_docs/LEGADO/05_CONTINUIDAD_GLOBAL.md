# 05 — Continuidad Global: TD-003 a TD-006

**Versión:** 2.0.0
**Fecha:** 2026-06-03
**Estado:** ✅ LÍNEA BASE ESTABLE
**Tags:** v1.1-TD003 → v1.2-TD004 → v1.3-TD005 → v1.3.1-TD005.1 → v1.4-TD006

---

## Resumen Ejecutivo

5 Technical Deliveries (TDs) completados en sesión continua del 2026-06-03, estableciendo la **línea base técnica** de MADENAT Lumber Core.

| TD | Tag | Título | Tipo |
|----|-----|--------|------|
| TD-003 | `v1.1-TD003` | UOM + ingesta Many2many + logística lotes + limpieza estructural | feat |
| TD-004 | `v1.2-TD004` | Centralización constante física `25.4` → `MM_PER_INCH` | fix |
| TD-005 | `v1.3-TD005` | Clasificación y centralización reglas de negocio comercial | feat |
| TD-005.1 | `v1.3.1-TD005.1` | Documentación origen constante `1550.003096` | docs |
| TD-006 | `v1.4-TD006` | Investigación parametrización reglas → NO parametrizable | research |

---

## Decisiones Arquitectónicas Clave

### AD-06 (TD-006): Reglas comerciales NO parametrizables
Las constantes comerciales (`+1/8"`, `1550.003096`, `5085.312`) son **fijas** para todo MADENAT. Sin evidencia de variación por cliente, perfil o subproducto. Se mantienen como constantes en `utils_uom.py`.

### AD-05 (TD-005): Centralización de reglas de negocio
Todas las reglas de negocio comercial residen en **una sola fuente de verdad**: `madenat_lumber_core/models/utils_uom.py`.

### AD-04 (TD-004): Constantes físicas universales
`MM_PER_INCH = 25.4` es constante física NIST, centralizada como fuente única. No es regla de negocio.

### AD-03 (TD-003): Arquitectura de ingesta y logística
Modelo Many2many para formatos de ingesta, limpieza de código legacy, y estructura de modelos alineada con OCA best practices.

---

## Línea Base Técnica (v1.4-TD006)

### Módulos Activos
| Módulo | Versión | Estado |
|--------|---------|--------|
| `madenat_lumber_core` | 1.4-TD006 | ✅ Estable |
| `madenat_lumber_logistics` | 1.3-TD005 | ✅ Estable |
| `madenat_lumber_billing` | 1.5.0 | ✅ Estable |
| `madenat_lumber_costing` | — | ✅ Estable |
| `madenat_lumber_purchasing` | — | ✅ Estable |
| `madenat_lumber_reports` | — | ✅ Estable |
| `madenat_lumber_shipping_core` | — | ✅ Estable |
| `madenat_lumber_reception_improvements` | — | ✅ Estable |
| `madenat_toll_processing` | — | ✅ Estable |
| `madenat_vendor_payment` | — | ✅ Estable |

### Constantes Centralizadas (`utils_uom.py`)
| Constante | Valor | Tipo | Origen |
|-----------|-------|------|--------|
| `MM_PER_INCH` | `Decimal('25.4')` | Física universal | NIST |
| `INCH_SQ_METERS_TO_M3` | `Decimal('1550.003096')` | Comercial fija | Conversión dimensional |
| `BLANK_CLEAR_FACTOR` | `Decimal('5085.312')` | Comercial fija | Regla de negocio |
| `MBF_DIVISOR` | `Decimal('12000')` | Comercial fija | Estándar industria |
| `S2S_WIDTH_ADJUSTMENT_INCH` | `Decimal('0.125')` | Comercial fija | +1/8" ajuste S2S |
| `M3_DIVISOR` | `Decimal('1000000')` | Dimensional | mm²·m → m³ |

### Archivos Críticos
| Archivo | Responsabilidad |
|---------|----------------|
| `models/utils_uom.py` | Fuente única de verdad para constantes y fórmulas volumétricas |
| `models/madenat_ingestion_config.py` | Helper centralizado de configuración (AbstractModel) |
| `models/lumber_export_formula.py` | Fórmulas de exportación por perfil (Fase 3) |
| `models/lumber_ingestion_format.py` | Formatos de ingesta por perfil (Fase 3) |
| `models/stock_lot.py` | Cálculos volumétricos en lotes de inventario |
| `models/lumber_reception.py` | Recepciones y procesamiento de guías |
| `models/madenat_guia_processing.py` | Procesamiento de guías de embarque |
| `models/reception_parser.py` | Parser de formatos de ingesta |

### Volúmenes de Referencia (Golden Records)
| Lote | Volumen (m³) | Volumen Embarque (m³) |
|------|-------------|----------------------|
| A1M2605458 | 4.893 | 4.893 |
| A1M2602536 | 4.832 | 4.832 |

**Regla:** Cualquier cambio en código que altere estos volúmenes en >0.001 m³ es **regresión bloqueante**.

---

## Protocolo de Trabajo (Regla de Oro)

### Orden de Operaciones (OBLIGATORIO)
1. **INVESTIGAR** — grep, logs, estructura, git history
2. **MAPEAR** — dependencias, quién usa qué
3. **ENTENDER** — el problema raíz, no los síntomas
4. **APLICAR** — solución mínima, quirúrgica
5. **VALIDAR** — impacto: ¿rompe otras cosas? ¿altera golden records?
6. **DOCUMENTAR** — WIKI + CANON + CHANGELOG + comentario en código
7. **DEPLOY** — commit claro + tag + push

### Mini-Protocolo para Cambios
```bash
# 1. Estado actual
git status && git log --oneline -3

# 2. Cambio quirúrgico
#    (editar solo lo necesario)

# 3. Validación
python3 -m py_compile <archivo_modificado.py>
#    Verificar golden records si aplica

# 4. Documentar
#    - CHANGELOG.md: entrada en sección correspondiente
#    - CANON/04_DECISION_LOG.md: si es decisión arquitectónica
#    - WIKI/: si afecta documentación técnica

# 5. Commit + Tag + Push
git add <archivos>
git commit -m "tipo: TD-XXX descripcion" -m "Detalle..."
git tag -a vX.Y-TDXXX -m "TD-XXX — YYYY-MM-DD"
git push origin main --tags
```

### Convención de Commits
- `feat:` — Nueva funcionalidad
- `fix:` — Corrección de bug
- `docs:` — Solo documentación
- `refactor:` — Reestructuración sin cambio funcional
- `test:` — Tests
- `research:` — Investigación (sin cambios de código)

### Convención de Tags
- `v{major}.{minor}-TD{xxx}` — Ej: `v1.4-TD006`
- `v{major}.{minor}-TD{xxx}.{patch}` — Ej: `v1.3.1-TD005.1`
- `v{major}.{minor}-{DESCRIPTOR}` — Hitos mayores: `v2.0-CONTINUIDAD`

---

## Próximos Frentes

### TD-007: Validación Integral de Tests
- Ejecutar suite completa de tests (T01–T33+)
- Validar golden records contra Excel de referencia
- Documentar resultados en `CANON/03_TESTS.md`

### TD-008: Deploy a Producción
- Preparar `deploy_production.sh`
- Backup pre-deploy
- Migración de BD si aplica
- Smoke test post-deploy

### TD-009: Documentación de Usuario Final
- Manual de operación para administradores
- Guía de configuración de reglas de ingesta
- Troubleshooting común

---

## Auditoría y Trazabilidad

### Tags por TD
| Tag | Commit | Fecha |
|-----|--------|-------|
| `v1.1-TD003` | `a87c576` | 2026-06-03 |
| `v1.2-TD004` | `d6d6a8a` | 2026-06-03 |
| `v1.3-TD005` | `53927a6` | 2026-06-03 |
| `v1.3.1-TD005.1` | `ea8bb14` | 2026-06-03 |
| `v1.4-TD006` | `3c0e2a7` | 2026-06-03 |
| `v2.0-CONTINUIDAD` | *(este commit)* | 2026-06-03 |

### CHANGELOGs
- `madenat_lumber_core/CHANGELOG.md` — Principal (TD-003 a TD-006)
- `madenat_lumber_logistics/CHANGELOG.md` — Logística

### Documentación CANON
| Archivo | Propósito |
|---------|-----------|
| `CANON/INDICE_DOCUMENTACION.md` | Mapa maestro de documentación |
| `CANON/02_CONTINUIDAD.md` | Punto de retoma operativo |
| `CANON/03_TESTS.md` | Evidencia y criterios de validación |
| `CANON/04_DECISION_LOG.md` | Decisiones arquitectónicas (AD-01 a AD-06) |
| `CANON/05_CONTINUIDAD_GLOBAL.md` | Este documento — resumen global TD-003 a TD-006 |

### Documentación WIKI
| Archivo | Propósito |
|---------|-----------|
| `WIKI/02_TECNICO/arquitectura_ingesta_recepciones.md` | TD-004, TD-005, TD-006 |
| `WIKI/02_TECNICO/configuracion_ingesta.md` | Fase 1, Fase 2, Fase 3 |
| `WIKI/02_TECNICO/modelo_lotes.md` | Modelo de lotes extendido |
| `WIKI/02_TECNICO/modelo_recepciones.md` | Modelo de recepciones |
| `WIKI/02_TECNICO/dependencias_modulos.md` | Dependencias entre módulos |
| `WIKI/02_TECNICO/herencia_odoo_modelos.md` | Herencia de modelos |
| `WIKI/02_TECNICO/validadores_checklist.md` | Validadores y checklist |
| `WIKI/02_TECNICO/flujo_dimensiones_comerciales.md` | Flujo de dimensiones |

---

## Estado Actual

| Indicador | Estado |
|-----------|--------|
| Línea base técnica | ✅ ESTABLE |
| Tests | Pendiente validación completa (TD-007) |
| Deploy a producción | Listo para TD-008 |
| Documentación | ✅ Completa |
| Trazabilidad | ✅ Completa (5 TDs con tags, commits, docs) |
| Deuda técnica | 0 (investigación documentada previene trabajo innecesario) |

---

*Última actualización: 2026-06-03 14:00 CLST*
*Próximo punto de retoma: TD-007 — Validación Integral de Tests*