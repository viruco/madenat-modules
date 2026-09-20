# 04 — Decision Log

**Módulo:** MADENAT Lumber Core
**Versión documental:** 12.2.0
**Última actualización:** 2026-09-12  <!-- actualizado: 2026-09-12 — AD-64 (costeo real: AVCO desactivado, sin prorrateo parcial) y AD-65 (diseño aprobado: recepción a granel + Balance de Masa + consolidación administrativa) -->
**Estado:** Canonical / activo

---

## Propósito

Registrar las decisiones técnicas que gobiernan arquitectura, flujo funcional, trazabilidad, validación y continuidad.
Este archivo no contiene tareas pendientes ni evidencia de ejecución; solo decisiones que pasan a ser regla del sistema o de la documentación.

---

## 2026-04-08 — Cimentación

### AD-01 — Base documental canónica única
Se define una base documental central para evitar versiones parciales incompatibles.

### AD-02 — Foco en flujo integral y matemática reproducible
La validación del módulo se centra en que documento, staging, exportación y stock puedan reconciliarse matemáticamente.

### AD-03 — Regla de menús
Los menús viven en árbol principal; las vistas describen interiores.

### AD-04 — Gate 3 como único write real
Gate 3 es el único punto autorizado para escribir inventario real.

### AD-05 — Tipo de cambio explícito
Se prohíben fallbacks silenciosos para tipo de cambio.

### AD-06 — Protocolo de colaboración con IA
La continuidad se apoya en cápsulas breves y actualización dirigida de archivos canónicos.

---

## 2026-05-03 — Modularización y estabilidad

### AD-07 — Desacoplamiento parcial del monolito
Se extrae parser, workflow, servicio y helpers, pero se acepta temporalmente que `lumber_reception.py` siga concentrando clases principales.

### AD-08 — Lógica compartida en mixins/helpers
Se consolida reutilización de cálculos y utilidades para evitar reglas divergentes.

### AD-09 — Base T01–T14 como núcleo estable
La suite T01–T14 se adopta como el corazón funcional validado del proyecto.

### AD-10 — Fase 6 financiera como siguiente frente mayor
Una vez estabilizada la base operativa, el siguiente frente mayor es `lumber.billing.consolidation.line`.

---

## Compatibilidad Odoo 18

### AD-11 — Uso de `<list>`
En Odoo 18 las vistas de lista deben declararse con `<list>`.

---

## 2026-05-13 — Largo con unidad de ingreso

### AD-12 — `length` en metros como fuente de verdad
`length` se define formalmente como el valor interno canónico para cálculos.

### AD-13 — lengthinputraw como preservación de entrada humana
Se agrega el identificador canónico para el valor crudo de ingreso.

### AD-14 — lengthuom desacoplado del perfil de ingesta
La unidad de largo no debe confundirse con el perfil de cálculo; son conceptos distintos.

### AD-15 — Los cálculos deben leer valor normalizado
Todos los computes volumétricos deben basarse en `length` ya convertido a metros.

### AD-16 — Estabilidad nominal de campos
Toda referencia a la entrada de largo debe utilizar exactamente lengthinputraw para asegurar la estabilidad del registry.

### AD-17 — La incoherencia de naming es bug crítico
Toda discrepancia entre:
- nombre de campo,
- nombre usado en vista,
- nombre usado en `@depends`,
- nombre usado en tests,

se considera bug de primer nivel porque rompe instalación o produce cómputos erróneos.

---

## 2026-05-23 — Gobernanza documental y cierre técnico

### AD-18 — Separación estricta por tipo de documento
Cada documento canónico debe tener una responsabilidad única:
- `02_CONTINUIDAD.md` = estado vivo y punto de retoma.
- `03_TESTS.md` = evidencia y criterios de validación.
- `04_DECISION_LOG.md` = reglas y decisiones permanentes.
- `05_BACKLOG.md` = trabajo pendiente y prioridades activas.
- `06_CHECKLIST.md` = operación de sesión y cierre.

### AD-19 — El backlog no debe mezclar reglas ni evidencia
Si un contenido ya es regla permanente, debe pasar a decision log.
Si ya es estado confirmado, debe pasar a continuidad.
Si ya tiene evidencia, debe vivir en tests.

### AD-20 — La continuidad debe reflejar estado real, no teoría
`02_CONTINUIDAD.md` se define como checkpoint técnico operativo.
Debe permitir retomar trabajo sin reabrir análisis histórico innecesario.

### AD-21 — Las pruebas no se cierran por percepción
Un caso de prueba solo puede cerrarse si existe esperado explícito, resultado real, evidencia y actualización documental coherente.

### AD-22 — La validación de largo/unidades sigue abierta hasta evidencia formal
Aunque el error de `Wrong @depends` fue resuelto, el frente de largo/unidades no se considera cerrado hasta ejecutar y documentar T29, T30, T31 y T32.

### AD-23 — Fase 6 requiere cierre funcional completo
La implementación técnica de `shipment -> consolidation` no basta por sí sola.
La fase solo puede considerarse cerrada con validación UI, confirmación de creación real de registros y trazabilidad documental completa.

### AD-24 — Solución mínima antes que refactor amplio
Ante incidencias activas, primero se investiga, se mapean dependencias y se aplica la corrección mínima segura antes de abrir refactors mayores.

### AD-25 — La documentación se actualiza antes del cierre de sesión
Si cambia naming, cálculo, gates, flujo financiero o criterio de validación, la sesión no se considera cerrada hasta dejar actualizados continuidad, backlog, decision log y tests cuando corresponda.

### AD-26 — Higiene del Repositorio
**Decisión:** Se prohíbe la permanencia de carpetas `.backup` o archivos `.bak` dentro de los módulos de Odoo.
**Motivo:** Evitar colisiones de carga de vistas y mantener la limpieza del empaquetado del módulo.
**Impacto:** Los backups deben residir exclusivamente en `LEGADO/` dentro del repositorio documental.

---

## 2026-06-02 — FASE 3: Parametrización H8, H9 + Cierre Brecha s2s_exclusion_widths

### AD-30 — Fase 3 Parametrización de Fórmulas de Exportación, Formatos de Ingesta y Cierre de Brecha Helper

**Decisión:** Parametrizar los hardcodes de negocio puro H8 (`_compute_export_values`) y H9 (`_process_dataframe`) mediante modelos persistentes especializados, y cerrar la brecha de lectura directa de `madenat.s2s_exclusion_widths` unificándola en el helper centralizado.

**Contexto:** La auditoría post-Fase 2 identificó tres prioridades:
1. Documentación desalineada con el estado real del sistema
2. `madenat.s2s_exclusion_widths` leído directamente sin wrapper en el helper
3. H8 y H9 son los hardcodes de negocio más volátiles — cambian con operación, no son constantes técnicas

**Alcance quirúrgico:** Esta fase no rediseña la ingesta, no expande alcance a otros hardcodes, no crea rule engine genérico. Solo cierra las tres prioridades identificadas.

**Modelos creados:**

| Modelo | Tabla | Registros seed | Hardcode |
|--------|-------|---------------|----------|
| `lumber.export.formula` | Fórmulas de exportación por perfil | 3 (f5085, f1550, metric) | H8 |
| `lumber.ingestion.format` | Formatos de ingesta/parsing por perfil | 4 (f5085, f1550, blanks, metric) | H9 |

**Helper extendido:**
- `madenat.ingestion.config.get_s2s_exclusion_widths()` — nuevo método
- `get_s2s_adjustment()` en `utils_uom.py` ahora delega al helper (antes leía `ir.config_parameter` directamente)
- Eliminada la duplicidad de parseo CSV entre `utils_uom.py` y `madenat_guia_processing.py`

**Integración con consumidores:**
- `lumber_reception._compute_export_values()` → resuelve fórmula desde `lumber.export.formula._resolve_for_profile()`
- `reception_parser._process_dataframe()` → resuelve formato desde `lumber.ingestion.format._resolve_for_profile()`
- Ambos mantienen fallback exacto al comportamiento anterior si no hay registros Fase 3

**Fallback:**
- H8: si no hay registro activo en `lumber.export.formula` → constantes canónicas de `utils_uom`
- H9: si no hay registro activo en `lumber.ingestion.format` → hardcode legacy exacto
- s2s_exclusion_widths: ir.config_parameter → hardcode legacy [150,160,170,180,200]

**Archivos creados/modificados:**

| Archivo | Acción |
|---------|--------|
| `models/lumber_export_formula.py` | CREADO — modelo H8 |
| `models/lumber_ingestion_format.py` | CREADO — modelo H9 |
| `models/madenat_ingestion_config.py` | MODIFICADO — +get_s2s_exclusion_widths() |
| `models/utils_uom.py` | MODIFICADO — get_s2s_adjustment delega al helper |
| `models/lumber_reception.py` | MODIFICADO — _compute_export_values usa lumber.export.formula |
| `models/reception_parser.py` | MODIFICADO — _process_dataframe usa lumber.ingestion.format |
| `models/__init__.py` | MODIFICADO — +2 imports Fase 3 |
| `security/ir.model.access.csv` | MODIFICADO — +4 reglas acceso |
| `views/lumber_ingestion_config_views.xml` | MODIFICADO — +vistas H8/H9 + menús |
| `data/ingestion_seed_fase3.xml` | CREADO — 7 registros seed |
| `__manifest__.py` | MODIFICADO — +1 línea carga seed |

**Documentación actualizada:**
- `WIKI/02_TECNICO/configuracion_ingesta.md` — actualizado a v2.0.0 con Fase 3
- `CANON/04_DECISION_LOG.md` — esta entrada (AD-30)

**Lo que NO se parametrizó — con justificación explícita:**

| Ítem | Motivo |
|------|--------|
| H6, H12 | Requieren análisis de impacto estructural. Fuera del alcance de Fase 3. |
| H7 (MBF_TO_M3 = 2.36) | Constante de ingeniería, no de negocio. Cambiarla sin auditoría formal rompería todos los cálculos. Documentada como tal. |
| Fórmulas matemáticas | Regla de oro: no se tocan sin auditoría formal. |
| Workflow | No se modifica en ninguna fase. |
| Otros hardcodes (H3, etc.) | Fuera del alcance quirúrgico de Fase 3. |

**Impacto:**
- H8 y H9 ahora son editables desde UI por el administrador funcional sin tocar código
- `madenat.s2s_exclusion_widths` tiene fuente única de verdad en el helper
- Documentación refleja exactamente el estado real del sistema
- Cero regresión: fallbacks garantizan comportamiento idéntico si no hay registros Fase 3
- Fase 1 y Fase 2 intactas

**Riesgos:**
- Ninguno identificado. La arquitectura de fallback asegura que siempre hay una fuente de verdad disponible.
- El UNIQUE(profile, active) impide duplicados accidentales.

**Regla derivada:**
Todo hardcode de negocio que cambie con la operación (fórmulas, heurísticas de parsing) debe modelarse como registro persistente con UI de mantenimiento. Las constantes de ingeniería estables (como factores de conversión NIST) se documentan pero no se parametrizan.

---

## Riesgos registrados

| ID | Riesgo | Mitigación |
|---|---|---|
| R-01 | Integración financiera incompleta | cerrar Fase 6 con validación funcional y documental |
| R-02 | Warnings XML | limpieza progresiva |
| R-03 | Tolerancias matemáticas no formalizadas | parametrización futura |
| R-04 | Monolito parcial | refactor posterior |
| R-05 | Incoherencia de naming | resuelto el 23-mayo-2026 (lengthinputraw) |

---

## Prioridad actual

### Prioridad 0
Mantener consistencia del feature de largo/unidades hasta cerrar T29–T32.

### Prioridad 1
Revalidar y documentar formalmente T29–T32.

### Prioridad 2
Cerrar validación funcional de Fase 6 financiera.

### Prioridad 3
Reducir documentación satélite y fortalecer solo el núcleo canónico.

---

## Regla de mantenimiento

Toda decisión que cambie:
- naming de campos,
- política de cálculo,
- gates,
- flujo financiero,
- o arquitectura documental,

debe reflejarse aquí el mismo día.

## 2026-05-23 - Reglas de Calidad y Escalabilidad

### DEC-2026-05-23-PERF-01
**Decisión:** el endurecimiento de calidad técnica y la optimización de performance para altos volúmenes de datos pasan a ser un requisito de diseño permanente (regla arquitectónica), no un ítem aislado del backlog.
**Impacto:** cualquier desarrollo futuro (como la integración contable) debe diseñarse considerando volúmenes de producción masivos.

---

## 2026-05-23 - Consolidación documental y limpieza de ruido histórico

### DEC-2026-05-23-DOC-01
**Decisión:** consolidar la documentación activa en un núcleo canónico único por tema y mover inventarios, auditorías históricas, snapshots, dashboards auxiliares y variantes externas a `LEGADO/` o `LEGADO_EXTERNOS/`.

**Motivo:** existía ruido documental, duplicidad de contexto y referencias obsoletas que dificultaban la continuidad técnica y elevaban el riesgo de retomar trabajo desde una fuente incorrecta.

**Impacto:**
- Se fortalece `INDICE_DOCUMENTACION.md` como mapa maestro.
- Se reduce ambigüedad sobre qué documento editar.
- Se separa explícitamente documentación vigente de material histórico.
- Se mejora onboarding, continuidad y gobernanza documental.

**Regla operativa derivada:** no crear documentos paralelos para temas ya cubiertos por un archivo canónico; actualizar el documento dueño del tema y registrar la decisión si el cambio afecta arquitectura, operación o proceso documental.

---

## 2026-06-02 — Correcciones de bugs técnicos

### DEC-2026-06-02-BUG-01
**Decisión:** Corregir inconsistencia de normalización PO en `_find_or_create_po_intelligent()`.

**Problema:** 
El método `lumber_reception.py:1903–1904` llamaba a `self._po_key(value)` que no existe, causando:
```
AttributeError: 'lumber.reception' object has no attribute '_po_key'
```

El código había migrado parcialmente a usar `parser.normalize_po_key()` (línea 1852), pero la búsqueda tolerante aún usaba el helper inexistente.

**Causa raíz:** 
Migración incompleta del helper de normalización local hacia `reception_parser.py`. El código mezclaba nuevo enfoque (parser) con enfoque viejo (método inexistente en modelo).

**Solución aplicada:**
Reemplazar:
```python
# ANTES (líneas 1903–1904)
po = candidate_pos.filtered(
    lambda p: self._po_key(p.partner_ref or '') == po_key
        or self._po_key(p.name or '') == po_key
)[:1]
```

por:
```python
# DESPUÉS (líneas 1903–1904)
po = candidate_pos.filtered(
    lambda p: parser.normalize_po_key(p.partner_ref or '') == po_key
        or parser.normalize_po_key(p.name or '') == po_key
)[:1]
```

**Cambios:**
- Archivo: `custom_addons/madenat_lumber_core/models/lumber_reception.py`
- Líneas afectadas: 1903–1904 (2 referencias reemplazadas)
- Método: `_find_or_create_po_intelligent()`

**Impacto:**
- Cierra bug de `AttributeError` que bloqueaba búsqueda tolerante de OC
- Alinea código con arquitectura: `parser.normalize_po_key()` es fuente única de verdad
- Mantiene comportamiento funcional idéntico (misma normalización, mismo resultado)
- Validado: sintaxis correcta, cero referencias residuales a `self._po_key`

**Riesgos:**
Ninguno identificado. Cambio es quirúrgico, mínimo y coherente con arquitectura.

**Regla derivada:** 
Toda normalización de datos debe residir en `reception_parser.py` y ser callable desde cualquier modelo. No crear helpers locales que repliquen lógica ya existente.

---

### AD-27 — Corrección de Aplicación Indebida de Factor S2S en Blanks Clear

**Decisión:** Corregir la aplicación errada del ajuste volumétrico S2S (cepillado) en líneas de blanks clear.

**Problema:**
En el cálculo de `vol_shipment_m3` para lotes con perfil `blanks_clear`, el sistema aplicaba indebidamente:
- Deducciones de cepillado (`FACE_DEDUCTION_INCH`)
- Ajustes de ancho S2S (`S2S_WIDTH_ADJUSTMENT_INCH`)

Esto causaba que blanks clear utilizara **2 factores simultáneamente** (f5085 + ajustes S2S), distorsionando el volumen de embarque.

**Causa raíz:**
- Código de decisión condicional incompleto en `stock_lot.py` → `@computed_field vol_shipment_m3`
- La lógica no distinguía claramente entre:
  - `blanks_clear` → **exclusivamente BLANK_CLEAR_FACTOR (f5085 = 5085.312)**
  - `s2s` → **S2S_WIDTH_ADJUSTMENT** (la deducción de cara `FACE_DEDUCTION_INCH` = 0.0625 es propia del flujo `blank_clear`, no de `s2s`)

**Solución aplicada:**
Refactorización de la lógica condicional en:
1. `stock_lot.py` → `@computed_field vol_shipment_m3` (líneas ~250-350)
   - Agregar rama explícita: `if profile == 'blanks_clear': use BLANK_CLEAR_FACTOR only`
   - Garantizar que NO se apliquen deducciones de cepillado

2. `madenat_guia_processing.py` → método `_compute_volumes()` (líneas ~400-500)
   - Sincronizar lógica de cálculo con stock_lot.py
   - Preservar trazabilidad: blanks_clear siempre → f5085, nunca S2S

**Cambios técnicos:**

La corrección opera en el método `_compute_vol_shipment_m3` de `StockLotExtended` (`stock_lot.py`).
La bifurcación real NO usa campo `profile` ni constantes `FACE_DEDUCTION_INCH`/`S2S_WIDTH_ADJUSTMENT_INCH` (esas constantes se usan en `lumber_reception.py`).
La detección del caso blanks se hace por presencia/ausencia de `largo_ft_frac`:

```python
# stock_lot.py → _compute_vol_shipment_m3 (líneas 448-543)

for lot in self:
    nominal = lot.volume_purchase_m3 or lot.volumen_m3 or 0.0

    # 1. Protección: si reception_id existe y vol_shipment_m3 > 0.001, preservar
    if lot.reception_id and lot.vol_shipment_m3 > 0.001:
        continue

    # 2. Determinar dimensiones base (nominal > commercial_standard > físico)
    is_std = lot.product_id.use_commercial_standard
    e_mm = (lot.espesor_nominal_mm if lot.espesor_nominal_mm > 0
            else (lot.product_id.commercial_thickness_mm if is_std else lot.espesor_mm))
    a_mm = (lot.ancho_nominal_mm if lot.ancho_nominal_mm > 0
            else (lot.product_id.commercial_width_mm if is_std else lot.ancho_mm))

    if not e_mm or not a_mm or not lot.piezas:
        lot.vol_shipment_m3 = nominal  # ← Salvavidas
        continue

    # 3. Conversión a pulgadas y cálculo de overmeasure
    espesor_in = e_mm / float(MM_PER_INCH)
    ancho_in = a_mm / float(MM_PER_INCH)
    using_nominal = (lot.espesor_nominal_mm > 0 or lot.ancho_nominal_mm > 0)
    overmeasure = 0.0 if (is_std or using_nominal) else float(get_s2s_adjustment(self.env, a_mm))
    ancho_calculo = ancho_in + overmeasure

    # 4. Bifurcación real:
    if lot.largo_ft_frac:
        # ← RAMA BLANKS: SIN overmeasure, SIN deducciones S2S
        largo_ft = float(lot.largo_ft_frac.replace("'", "").strip())
        vol_gold = (espesor_in * ancho_in * largo_ft * lot.piezas) / float(BLANK_CLEAR_FACTOR)
    else:
        # ← RAMA MÉTRICA: CON overmeasure S2S aplicado en ancho_calculo
        l_m = lot.product_id.commercial_length_m if is_std else lot.largo_m
        if not l_m:
            lot.vol_shipment_m3 = nominal
            continue
        vol_gold = (espesor_in * ancho_calculo * l_m * lot.piezas) / float(INCH_SQ_METERS_TO_M3)

    # 5. Redondeo y salvavidas final
    calculado = r3(vol_gold)
    lot.vol_shipment_m3 = calculado if calculado > 0 else nominal
```

**Diferencia clave con el fix documentado anteriormente:**
- No existe campo `profile` en `stock.lot`. La bifurcación es por `largo_ft_frac` (presencia de pies → fórmula imperial blanks).
- `BLANK_CLEAR_FACTOR` = 5085.312 (no 0.6).
- `INCH_SQ_METERS_TO_M3` = 1550.003 (factor métrico, no 1/1_000_000).
- Las constantes `FACE_DEDUCTION_INCH` y `S2S_WIDTH_ADJUSTMENT_INCH` se usan en `lumber_reception.py._compute_volumes()`, no en `stock_lot.py._compute_vol_shipment_m3()`.

**Impacto:**
- ✅ Blanks clear ahora usan **f5085 exclusivamente**
- ✅ Volumen de embarque correcto conforme a la fórmula `blank_clear`
- ✅ Sincronización entre stock.lot y guía de procesamiento
- ✅ Sin regresión: S2S y otros perfiles mantienen comportamiento idéntico

**Validación:**
- ✅ Módulo actualiza sin error de registry
- ✅ Cálculo volumétrico verificado en local
- ✅ Recepción con blanks procesada exitosamente (guía referencia: 40597)

**Regla derivada:**
Toda rama condicional en cálculos volumétricos debe estar explícitamente documentada en código con comentario que indique:
- Perfil aplicable (blanks_clear, s2s, metric, etc.)
- Factor/constante usado
- Por qué ese perfil NO puede aplicar el factor contrario

---

## 2026-06-02 — Actualización de Documentación Viva

### META-ENTRADA: Cambios Documentales del 2-jun

**Decisión:** Registrar formalmente los cambios en documentación viva realizados hoy para preservar trazabilidad.

**Cambios ejecutados:**

1. **02_CONTINUIDAD.md** (mod 2026-06-02 12:03:36)
   - Registrada AD-27 (Fix de blanks clear) en Prioridades Actuales
   - Actualización del punto de retoma
   - Prioridades alineadas a deploy a TEST

2. **03_TESTS.md** (mod 2026-06-02 12:06:51)
   - Agregado caso T33: "Fix de ajuste S2S indebido en blanks"
   - T33 estado: CERRADO (Evidencia local)
   - Verificación: módulo instala, cálculo validado

3. **04_DECISION_LOG.md** (mod 2026-06-02 16:39:02 y posterior)
   - DEC-2026-06-02-BUG-01: Bug _po_key() → normalize_po_key()
   - AD-27: Fix de blanks clear (registro posterior a continuidad)
   - Documentación técnica de 2 Gates y 1 Service (creada por auditoría)

4. **WIKI/02_TECNICO/** (NUEVA)
   - gates_validacion.md (439 líneas) — Documentación de 4 Gates
   - servicio_lotes.md (396 líneas) — Documentación de LumberReceptionService

**Motivo:**
La documentación viva (CONTINUIDAD, TESTS) debe siempre reflejarse en decisiones formales (DECISION_LOG). Esto preserva trazabilidad y permite archaeology futura.

**Regla derivada:**
Toda modificación a documentos vivos (02_CONTINUIDAD.md, 03_TESTS.md) que afecte decisiones arquitectónicas, validaciones, o flujos de negocio debe:
1. Registrarse en DECISION_LOG con fecha y descripción
2. Incluir cambio técnico exacto
3. Vincular a archivos técnicos (WIKI/) si aplica
4. Ejecutarse en la MISMA sesión (no dejar sesiones sin cierre documental)

---

## 2026-06-02 — FASE 1: Desacoplamiento de Hardcodes (Parametrización)

### AD-28 — Fase 1 Desacoplamiento de Constantes de Negocio

**Decisión:** Mover 7 hardcodes de negocio a `ir.config_parameter` manteniendo fallback exacto al comportamiento actual, sin modificar fórmulas matemáticas, workflow ni esquema de modelos.

**Contexto:** Investigación previa identificó 14 hardcodes (H1-H14). Esta Fase 1 ataca solo aquellos parametrizables sin riesgo estructural.

**Hardcodes resueltos:**

| Hardcode | Parámetro | Tipo | Archivo(s) |
|---|---|---|---|
| H1 | `madenat.blanks_nominal_map` | JSON | `reception_parser.py` |
| H1 | `madenat.nominal_tolerance` | float | `reception_parser.py` |
| H10+H11 | `madenat.width_s2s_map` | JSON | `width_mapping.py`, `utils_uom.py` |
| H5 | `madenat.thickness_visual_ranges` | JSON | `lumber_reception.py` (ambos sitios) |
| H13 | `madenat.thickness_visual_ranges` | JSON | `lumber_reception.py._compute_reception_summary` |
| H2 | `madenat.profile_subproduct_filters` | JSON | `lumber_reception_mass_update.py` |
| H4 | `madenat.profile_subproduct_filters` | JSON | `lumber_reception_mass_update.py._action_apply` |
| H14 | `madenat.profile_subproduct_filters` | JSON | `madenat_guia_mass_update.py._action_apply` |

**Criterio de fallback:** Toda lectura de parámetro usa try/except + warning log + retorno del valor hardcodeado actual.

**Archivos técnicos modificados:** 8 archivos (ver detalle abajo).

**Archivos documentales tocados:**
- `CANON/04_DECISION_LOG.md` — esta entrada + META-ENTRADA
- `data/ingestion_config.xml` — nuevo (5 parámetros seed)

**Excluido para Fase 2:**
- H6, H7, H8, H9, H12 — requieren modelo de mantenimiento o cambios estructurales
- Modelo de mantenimiento no implementado
- No se tocaron fórmulas matemáticas
- No se modificó workflow

**Validación:** Chequeo estructural: 5/5 parámetros válidos, 6/6 archivos con lectores correctos, S2S_WIDTH_LOOKUP preservado.

### Cambios por archivo — Fase 1

| Archivo | Cambios | Hardcodes |
|---|---|---|
| `data/ingestion_config.xml` | CREADO — 5 parámetros seed | H1,H2,H4,H5,H10,H11,H13,H14 |
| `__manifest__.py` | +1 línea (carga de ingestion_config.xml) | — |
| `models/reception_parser.py` | `_get_blanks_nominal_map()`, `_get_nominal_tolerance()`, `import json` | H1 |
| `models/width_mapping.py` | `_get_mapping_from_param()`, `env=None` en `get_value()` | H10, H11 |
| `models/lumber_reception.py` | `_get_thickness_visual_ranges()`, `_apply_thickness_visual()`, `import json` | H5, H13 |
| `wizard/lumber_reception_mass_update.py` | `_get_profile_subproduct_filters()`, guardias parametrizadas | H2, H3, H4 |
| `wizard/madenat_guia_mass_update.py` | `_get_profile_subproduct_filters()`, guardia parametrizada | H14 |

**Nota:** `S2S_WIDTH_LOOKUP` en `utils_uom.py` se preserva como fallback canónico. `WidthMappingTable.MAPPING` también se preserva.

### Hardcodes pendientes para Fase 2

| Hardcode | Motivo exclusión |
|---|---|
| H6, H7, H8, H9 | Requieren modelo de mantenimiento + UI de configuración |
| H12 | Depende de resolución de H10+H11 consolidada |
| Fórmulas matemáticas | Regla de oro: NO tocar en ninguna fase sin auditoría formal |
| Workflow | No se modifica en Fase 1 ni Fase 2 |

---

## 2026-06-02 — FASE 2: Modelos Persistentes + Helper Centralizado

### AD-29 — Fase 2 Migración a Modelos Persistentes con Helper Centralizado

**Decisión:** Crear 4 modelos Odoo persistentes con UI de mantenimiento para las reglas de ingesta, unificando toda lectura bajo un helper centralizado (`madenat.ingestion.config`) con cadena de fallback de 3 niveles.

**Contexto:** La Fase 1 (AD-28) movió 5 reglas de negocio a `ir.config_parameter`. Esto resolvió el desacoplamiento inicial pero dejó pendiente:
- Sin UI de mantenimiento (editar JSON en settings técnicas)
- Sin validación de integridad (solapes, duplicados)
- Sin trazabilidad de cambios (quién cambió qué, cuándo)

**Modelos creados:**

| Modelo | Tabla | Registros seed |
|--------|-------|---------------|
| `lumber.blank.nominal.map` | Mapa físico→nominal blanks | 8 (f5085) |
| `lumber.width.s2s.map` | Tabla Rough→S2S | 15 |
| `lumber.thickness.visual.rule` | Rangos espesor→visual | 4 (f5085) |
| `lumber.profile.subproduct.rule` | Reglas perfil↔subproducto | 7 |

**Helper centralizado:**
- `madenat.ingestion.config` (AbstractModel) — 5 métodos públicos
- Cadena de prioridad: Modelo Fase 2 → ir.config_parameter Fase 1 → Hardcode legacy
- Usa `.sudo()` en todas las lecturas para garantizar acceso desde cualquier contexto

**Wizards actualizados:**
- `lumber.reception.mass.update` — `_get_profile_subproduct_filters()` lee desde helper
- `madenat.guia.mass.update` — `_get_profile_subproduct_filters()` lee desde helper

**Parser actualizado:**
- `reception_parser._get_blanks_nominal_map()` y `_get_nominal_tolerance()` delegados al helper

**Archivos creados/modificados:**

| Archivo | Acción | Contenido |
|---------|--------|-----------|
| `models/lumber_blank_nominal_map.py` | CREADO | Modelo con constraints y validación de solapes |
| `models/lumber_width_s2s_map.py` | CREADO | Modelo con UNIQUE(rough_mm) |
| `models/lumber_thickness_visual_rule.py` | CREADO | Modelo con validación de solapes |
| `models/lumber_profile_subproduct_rule.py` | CREADO | Modelo con UNIQUE(profile, rule_type, keyword) |
| `models/madenat_ingestion_config.py` | CREADO | Helper AbstractModel con 5 métodos + fallback 3 niveles |
| `data/ingestion_seed_fase2.xml` | CREADO | 34 registros seed con forcecreate="False" |
| `models/__init__.py` | MODIFICADO | +5 imports |
| `__manifest__.py` | MODIFICADO | +1 línea carga seed XML |
| `security/ir.model.access.csv` | MODIFICADO | +4 reglas de acceso |
| `models/reception_parser.py` | MODIFICADO | Delegación a helper |
| `wizard/lumber_reception_mass_update.py` | MODIFICADO | Delegación a helper |
| `wizard/madenat_guia_mass_update.py` | MODIFICADO | Delegación a helper |

**Validaciones de integridad en modelos:**
- `lumber.blank.nominal.map`: No solape de rangos, CHECK constraints
- `lumber.width.s2s.map`: UNIQUE rough_mm, CHECK positivos
- `lumber.thickness.visual.rule`: No solape de rangos, CHECK positivos
- `lumber.profile.subproduct.rule`: UNIQUE compuesto, keyword no vacío

**Idempotencia del seed:**
- `forcecreate="False"` en todos los registros XML
- `noupdate="1"` en el bloque de datos
- Si los registros ya existen (creados manualmente o por XML previo), no se duplican

**Impacto:**
- ✅ Administradores pueden mantener reglas sin tocar código ni JSON
- ✅ Validación de integridad en BD (no solapes, no duplicados)
- ✅ Trazabilidad completa (campos estándar Odoo: create_uid, write_date)
- ✅ Soft-delete vía campo `active` en los 4 modelos
- ✅ Cadena de fallback garantiza cero disrupción en producción
- ✅ Si se desactivan todos los registros, el sistema sigue funcionando con Fase 1 → hardcode

**Riesgos:**
- Ninguno identificado. La arquitectura de fallback asegura que siempre hay una fuente de verdad disponible.
- Los modelos Fase 2 son aditivos: no reemplazan, se anteponen.

**Regla derivada:**
Todo nuevo parámetro de negocio debe modelarse como registro persistente antes que como `ir.config_parameter`. Usar `ir.config_parameter` solo para valores transitorios o de sistema. La UI de mantenimiento es requisito para reglas editables por usuario de negocio.

**Cierre documental:**
- `WIKI/02_TECNICO/configuracion_ingesta.md` creado (documentación completa Fase 1 + Fase 2)
- `CANON/04_DECISION_LOG.md` — esta entrada (AD-29)
- `CANON/02_CONTINUIDAD.md` — actualizar punto de retoma

---

## 2026-06-02 — Corrección de bugs post-Fase 3

### DEC-2026-06-02-BUG-02

**Decisión:** Corregir NameError enmascarado `FACTOR_METROS` no definido en `_compute_vol_shipment_m3()`.

**Problema:**
En la rama `else` del método `_compute_vol_shipment_m3()` de `MadenatGuiaProcessingLine` (línea 580), se usaba la variable `FACTOR_METROS` que nunca fue definida. Esto producía un `NameError` que era silenciado por el `except Exception` genérico de la línea 588, causando que todas las guías S2S/RIP con `length_ft <= 0.1` usaran el `fallback_vol` (volumen nominal de compra) en lugar del volumen geométrico real calculado con ajuste de cepillado (+1/8").

**Causa raíz:**
La variable `FACTOR_PIES` se define correctamente al inicio del método (`FACTOR_PIES = float(BLANK_CLEAR_FACTOR)`), pero en la rama métrica se referenció erróneamente `FACTOR_METROS` (nombre no definido) en lugar de usar `INCH_SQ_METERS_TO_M3`, que ya estaba importado desde `utils_uom` (línea 64 del mismo archivo).

**Solución aplicada:**
Reemplazar en `madenat_guia_processing.py:580`:
```python
# ANTES
vol = (e_in * width_calc * largo_uso * line.pieces) / FACTOR_METROS

# DESPUÉS
vol = (e_in * width_calc * largo_uso * line.pieces) / float(INCH_SQ_METERS_TO_M3)
```

**Cambios:**
- Archivo: `custom_addons/madenat_lumber_core/models/madenat_guia_processing.py`
- Línea afectada: 580 (1 línea reemplazada)
- Método: `_compute_vol_shipment_m3()`

**Impacto:**
- Volúmenes de embarque ahora se calculan correctamente para guías S2S/RIP cuando `length_ft <= 0.1`
- Se elimina el `NameError` enmascarado que forzaba fallback silencioso al volumen nominal
- Las líneas S2S/RIP ahora aplican correctamente el ajuste de cepillado +1/8" en el cálculo geométrico real

**Riesgos:**
Ninguno identificado. `INCH_SQ_METERS_TO_M3` ya estaba importado (línea 64) y es usado consistentemente en otras partes del mismo archivo (líneas 2335, 2454). El cast `float()` es coherente con el uso de `FACTOR_PIES = float(BLANK_CLEAR_FACTOR)` en la rama superior.

**Regla derivada:**
Toda variable usada en cálculos volumétricos debe estar:
1. Definida explícitamente antes de su uso
2. Validada con el mismo tipo de cast que sus pares en el mismo método
3. No crear variables locales con nombres que sugieran constantes no definidas


### DEC-2026-06-03-TD006 — AD-06: Reglas comerciales NO son parametrizables por cliente/perfil/subproducto

**Fecha:** 2026-06-03
**Tag:** v1.4-TD006
**Estado:** Decisión firme — NO parametrizar

**Pregunta de investigación:**
¿Las reglas comerciales (`+1/8"`, `1550.003096`, `5085.312`) varían por cliente, perfil o subproducto?

**Decisión:**
NO se parametrizan. Las reglas comerciales son **fijas** para todo MADENAT y se mantienen como constantes en `utils_uom.py`.

**Evidencia (6 fuentes independientes):**

| # | Fuente | Hallazgo |
|---|--------|----------|
| 1 | `get_s2s_adjustment()` en utils_uom | Solo varía por `width_mm` (lista de exclusiones); retorna SIEMPRE `Decimal('0.125')` o `Decimal('0.0')`. Sin condicional por `partner_id`, `subproducto_id`, perfil, ni país |
| 2 | `calculate_volume_imperial_to_m3()` | Acepta booleano `apply_s2s_adjustment` pero SIEMPRE usa la constante fija `S2S_WIDTH_ADJUSTMENT_INCH` cuando es True |
| 3 | `lumber_export_formula.py` fallbacks | Los 3 perfiles (f5085, f1550, metric) usan las mismas constantes fijas de `utils_uom` |
| 4 | `madenat_ingestion_config.py` | AbstractModel sin campos para reglas comerciales. No hay campo `embarque_width_adjustment`, `factor_embarque`, ni `factor_blank` |
| 5 | Git log | Cero commits sobre variación por cliente. Solo 2 commits relacionados: TD-004 y TD-005.1 |
| 6 | Documentación Excel | No se encontraron archivos xlsx/xls/csv en el repositorio con evidencia de variación |

**Hipótesis refutadas:**
- ❌ `+1/8"` → `+1/4"` para clientes premium
- ❌ `1550.003096` → `1550` exacto para ciertos mercados
- ❌ `5085.312` varía según tipo de Blank (Rough vs S2S)

**Consecuencias arquitectónicas:**
- Sin cambios de código — no se crean campos, no se modifican fórmulas
- Sin riesgo de regresión — volúmenes A1M2605458 y A1M2602536 permanecen inalterados
- Sin nueva UI — no se agregan vistas de configuración
- Deuda técnica cero — la investigación documentada previene futuras re-parametrizaciones innecesarias

**Condiciones de reapertura:**
TD-006 se reabrirá SOLO si:
1. Cliente requiere fórmula diferente (caso específico documentado, no hipotético)
2. Mercado de exportación cambia regulaciones que afectan los factores
3. Stakeholder confirma cambio de regla de negocio con evidencia documental

**Regla derivada:**
Antes de parametrizar cualquier regla de negocio en `madenat_ingestion_config`:
1. Debe existir evidencia funcional concreta de variación (no hipótesis)
2. La evidencia debe ser específica: qué cliente, qué valor, qué fecha
3. Si no hay evidencia, mantener como constante fija documentada

---

## 2026-06-13 — Fix: campo purchase_order inexistente en lumber.reception.line

### DEC-2026-06-13-BUG-03 / AD-31

**Decisión:** Revertir `purchase_order` → `purchase_id` en vistas de reportes R7/R8.

**Problema:**
El archivo `madenat_lumber_reports/views/inventory_report_views.xml` referenciaba el campo `purchase_order` en dos lugares:
1. `<field name="purchase_order" optional="show"/>` en `view_lumber_reception_line_tree_detail` (línea 28)
2. `context="{'group_by': 'purchase_order'}"` en el filtro `group_purchase` (línea 118)

Esto causaba un `ParseError` de Odoo:
```
El campo "purchase_order" no existe en el modelo "lumber.reception.line"
```

**Causa raíz:**
| Campo | Modelo | ¿Existe? | Tipo |
|-------|--------|----------|------|
| `purchase_order` | `lumber.reception` (cabecera) | ✅ Sí | `Char` (compute, store=True) |
| `purchase_id` | `lumber.reception` (cabecera) | ✅ Sí | `Many2one('purchase.order')` |
| `purchase_id` | `lumber.reception.line` (vía `_inherit` en `lumber_reception_reports.py`) | ✅ Sí | `Many2one` related a `reception_id.purchase_id` |
| `purchase_order` | `lumber.reception.line` | ❌ **NO EXISTE** | — |

`purchase_order` es un campo `Char` computado que solo existe en el modelo cabecera `lumber.reception`. En `lumber.reception.line`, el campo correcto es `purchase_id` (defined en `LumberReceptionLineReport` que hereda de `lumber.reception.line`, línea 50 de `lumber_reception_reports.py`).

**Solución aplicada:**
- Eliminar `<field name="purchase_order" optional="show"/>` → reemplazar por `<field name="purchase_id" optional="show"/>`
- Cambiar `group_by: 'purchase_order'` → `group_by: 'purchase_id'`

**Cambios:**
- Archivo: `custom_addons/madenat_lumber_reports/views/inventory_report_views.xml`
- Líneas afectadas: 27-28 y 116-118 (2 bloques modificados)
- Vistas afectadas: `view_lumber_reception_line_tree_detail` y `view_lumber_reception_line_search_inventory`

**Impacto:**
- ✅ Cierra `ParseError` que bloqueaba la carga de vistas de reportes
- ✅ El campo `purchase_id` (Many2one) muestra el nombre de la OC automáticamente en la UI
- ✅ El filtro "Orden de Compra" agrupa correctamente por `purchase_id`
- ✅ Sin cambios en modelos, solo vistas

**Riesgos:**
Ninguno. `purchase_id` ya existía como campo relacionado en `lumber.reception.line` desde `lumber_reception_reports.py` línea 50.

**Regla derivada:**
Antes de agregar un campo a una vista XML, verificar:
1. ¿El campo existe en el modelo base?
2. ¿El campo existe en algún `_inherit` del modelo?
3. ¿El campo es `related` o `compute` de otro modelo? Si es `related`, usar el campo del modelo heredado, no el de la cabecera.

---

## 2026-06-03 — HF-001: Restricción de imports Python entre addons Odoo 18 CE

### DEC-2026-06-03-HF001 / AD-07

**Decisión:** Revertir imports Python absolutos entre addons Odoo 18 CE

**Contexto:**
- TD-004 y TD-005 introdujeron `from madenat_lumber_core.models.utils_uom import MM_PER_INCH, M3_DIVISOR`
  en `madenat_lumber_logistics/models/lumber_shipment_line.py`
- El import rompe el mecanismo de carga del registry de Odoo 18 CE en Docker
- Evidencia directa del contenedor:
  ```
  AssertionError: Invalid import of madenat_lumber_core.models.reception_parser.MadenatReceptionParser,
  it should start with 'odoo.addons'
  ```
  Odoo requiere que todos los módulos se importen bajo el namespace `odoo.addons.*`,
  no como paquete Python absoluto.
- Causa raíz: `/mnt/extra-addons` NO está en `sys.path` del contenedor Python
  (solo `/usr/lib/python3.12`, `/usr/lib/python3/dist-packages`, etc.)
  Odoo gestiona sus propios imports internamente usando `load_openerp_module()`.
- Impacto: HTTP 500, sistema completamente caído, `KeyError: 'madenat_test'` en LRU cache

**Decisión:**
- Revertir imports a literales en `lumber_shipment_line.py`: `25.4` y `1_000_000.0`
- Agregar restricción documentada en `utils_uom.py` como guard-rail para futuros desarrolladores
- Abrir TD-004B para arquitectura correcta de constantes compartidas

**Alternativas descartadas:**
- `sys.path` manipulation → frágil, no portable entre entornos
- Instalar addons como paquetes Python (`setup.py`) → overhead innecesario, anti-patrón Odoo
- `odoo.addons.madenat_lumber_core.models.utils_uom` → no probado en caliente, riesgo de romper otros módulos
- Dejar imports rotos → sistema inoperable, no es opción

**Regla derivada (canónica):**
1. NUNCA usar `from madenat_lumber_core.models...` desde otro addon
2. Las constantes compartidas deben duplicarse con comentario de referencia `# ver utils_uom.py TD-004B`
3. La arquitectura correcta para compartir constantes entre addons será un módulo `madenat_lumber_utils`
   sin modelos ORM, solo con constantes/funciones puras (pendiente TD-004B)

**Estado:** ✅ Aplicado
**Tag:** v2.1-HF001
**Golden records validados:** A1M2605458=4.893, A1M2602536=4.832 (inalterados)

---

## 2026-06-09 — C2/C4: Selector tipo producto + Restricción documental Packing/Guía

### AD-32 — Selector operativo de tipo producto con restricción documental por perfil

**Decisión:** Agregar selector de tipo producto (Madera Aserrada / Blank) con labels operativos en Recepción, y restringir la documentación requerida (Packing/Guía) según el tipo de producto configurado por perfil de ingesta.

**Contexto:** Observaciones C2 y C4 de Cristhian (2026-06-09). El operador necesitaba identificar visualmente el tipo de producto en la recepción y el sistema debía validar qué documentos eran obligatorios según el perfil.

**Cambios:**
- `lumber_reception_views.xml`: Agregado selector tipo producto con labels operativos
- Restricción documental: Packing requerido solo para perfiles que lo usan, Guía requerida solo para perfiles que la necesitan
- Commits: `c6d8812` (C2), `0cda416` (C2+C4 amend)

**Impacto:**
- ✅ Operador identifica tipo producto sin ambigüedad en la UI
- ✅ Validación documental adaptativa por perfil (no se pide Packing para blanks, no se pide Guía para métrico)
- ✅ Sin cambios en cálculos, workflow ni flujo financiero

**Regla derivada:**
Toda regla de validación documental debe ser específica por perfil de ingesta. No asumir que todos los perfiles requieren los mismos documentos.

---

## 2026-06-09 — C3: Parseo fracciones imperiales + Separación flujos S2S/Blank

### AD-33 — Parseo robusto de fracciones imperiales y espejo documental S2S/Blank

**Decisión:** Implementar parseo robusto de fracciones imperiales (ej: "1 1/2" → 1.5) y formalizar la separación de flujos de cálculo entre S2S y Blank, documentando cada factor en espejo documental (`thickness_nominal_frac` como espejo exacto de `thickness_visual`).

**Contexto:** Observación C3 de Cristhian. El sistema debía interpretar correctamente fracciones imperiales mixtas y mantener un espejo documental entre la representación visual (cuartos comerciales) y la nominal exacta (fracción base 16).

**Cambios:**
- Parseo de fracciones imperiales: soporte para formato mixto (entero + fracción) y formato simple (solo fracción)
- `_compute_visual_defaults`: `thickness_nominal_frac` como espejo exacto de `thickness_visual`
- Separación explícita de flujos S2S (f1550) y Blank (f5085) en documentación y código
- Commits: `4b2d802` (C3 parseo), `525af85` (CHANGELOG)

**Impacto:**
- ✅ Fracciones imperiales parseadas correctamente (1 1/2" = 6/4 comercial)
- ✅ Trazabilidad completa: nominal exacto preservado como columna opcional
- ✅ Separación S2S/Blank documentada como regla arquitectónica

**Regla derivada:**
1. `thickness_nominal_frac` SIEMPRE debe ser espejo computacional de `thickness_visual`. No se editan independientemente.
2. Todo parseo de unidades imperiales debe soportar formato mixto (entero + fracción) y formato simple.
3. La separación S2S vs Blank es arquitectónica: S2S puede modificar nominal comercial (f1550, recargo +1/8"), Blank es producto final sin transformación.

---

## 2026-06-11 — thickness_visual 6/4 range + Migración 18.0.5.1.0

### AD-34 — Corrección de rango thickness_visual 6/4 y patrón de migración post-módulo

**Decisión:** Corregir el rango de clasificación thickness_visual: 6/4 max_thickness 42→46mm, 7/4 min_thickness 42→46mm, para que 45mm S2S clasifique correctamente como 6/4 (nominal canónico 1.5"). Establecer patrón de migración `18.0.5.1.0` para cambios de datos semilla que requieren `post-migrate`.

**Contexto:** INC-010. El rango 6/4 terminaba en 42mm, causando que 45mm S2S (espesor nominal 1.5" = 6/4 canónico) se clasificara erróneamente como 7/4.

**Cambios:**
- `thickness_visual_ranges_seed.xml`: 6/4 max 42→46mm, 7/4 min 42→46mm
- `migrations/18.0.5.1.0/`: Script de migración automática con `post-migrate`
- Commits: `3252c7e` (fix), `52ec1c7` (migration), `7b3665f` (docs INC-010 + DEC-006)

**Impacto:**
- ✅ 45mm S2S ahora clasifica correctamente como 6/4
- ✅ Migración automática en upgrade sin intervención manual
- ✅ Patrón `post-migrate` documentado para futuros cambios de datos semilla

**Regla derivada:**
1. Todo cambio en datos semilla (XML) que afecte registros existentes DEBE incluir script de migración con versión semántica.
2. Rangos de clasificación visual deben validarse contra casos reales de producción antes de publicarse.
3. INC y DEC deben documentarse en la misma sesión que el fix.

---

## 2026-06-13 — R7/R8: Alineación reportes inventory con purchase_order de core

### AD-35 — Campo purchase_id como fuente única en reportes de inventario R7/R8

**Decisión:** Unificar el campo de orden de compra en reportes R7 y R8 usando `purchase_id` (Many2one relacionado desde `lumber.reception.line` vía `reception_id.purchase_id`) como fuente única, eliminando referencias al campo inexistente `purchase_order` (Char computado que solo existe en la cabecera `lumber.reception`).

**Contexto:** DEC-2026-06-13-BUG-03 (AD-31) resolvió el ParseError inicial. Esta decisión complementaria formaliza la alineación de group_by y columnas en R7/R8 con la arquitectura de core.

**Cambios:**
- `inventory_report_views.xml`: `purchase_order` → `purchase_id` en tree y search
- PDF footer colspan corregido para alineación de columnas
- Commit: `99545d9` (R7 OC column fix), `3ba43575` (R7/R8 group_by alignment)

**Impacto:**
- ✅ Reportes R7 y R8 cargan sin ParseError
- ✅ Filtro "Agrupar por OC" funcional en inventory reports
- ✅ PDF footer colspan consistente con número real de columnas
- ✅ Sin cambios en modelos — solo vistas

**Regla derivada (refuerza AD-31):**
Al extender vistas de reportes sobre `lumber.reception.line`, usar SIEMPRE `purchase_id` (related field definido en `lumber_reception_reports.py`), NUNCA `purchase_order` (campo exclusivo de la cabecera). Verificar existencia del campo en el modelo concreto antes de referenciarlo en XML.
---

## 2026-07-01 — Auditoría forense documental + Ejecución AD-26

### AD-36 — Ejecución de higiene documental: AD-26, cierre CHANGELOG, alineación CANON

**Decisión:** Ejecutar la limpieza de residuos documentales decretada en AD-26 (2026-05-23) que permanecía sin ejecutar, y alinear la documentación canónica con el estado real del repositorio.

**Problema:**
- 33 archivos `.bak` en 7 módulos productivos violando AD-26 activamente.
- `backups/fase1_20260602_211431/` dentro de `madenat_lumber_core/`.
- `CHANGELOG.md` con sección `[Unreleased]` abierta desde 2026-07-01 sin cierre documental (viola AD-25).
- `INDICE_DOCUMENTACION.md` declaraba `02_CONTINUIDAD.md` v8.1.0 cuando el archivo real es v9.0.0.
- `madenat_lumber_core/models/ROADMAP.md` en ubicación incorrecta (models/ en lugar de WIKI/).

**Ejecutado (Fase A — Higiene):**
- Snapshot de seguridad pre-limpieza: `~/madenat_pre_cleanup_20260701_170707.tar.gz` (13MB).
- 33 archivos `.bak` movidos de módulos productivos → `LEGADO/backups_modulos/` preservando estructura y timestamps.
- `backups/fase1_20260602_211431/` movido → `LEGADO/backups_modulos/`.
- `docker-compose.yml.bak.2026-05-18_204331` eliminado (sin valor histórico).
- `docs_backup_20260523_121420.tar.gz` eliminado (duplicado exacto confirmado por P7).
- Prueba de humo: 86 módulos cargados en 4.71s, 0 errores, registry OK.

**Ejecutado (Fase B — Alineación canónica):**
- `INDICE_DOCUMENTACION.md`: versión `02_CONTINUIDAD.md` corregida 8.1.0→9.0.0.
- `CHANGELOG.md`: sección `[Unreleased]` cerrada → `[18.0.5.4.0] - 2026-07-01`.
- `02_CONTINUIDAD.md` actualizado a v9.1.0 con checkpoint post-auditoría.
- `ROADMAP.md` movido de `models/` → `WIKI/02_TECNICO/roadmap_core.md`.

**Impacto:**
- AD-26 finalmente ejecutado: 0 archivos `.bak` en módulos productivos.
- 0 directorios `backups/` en módulos productivos.
- Documentación canónica alineada: versiones reales coinciden con el índice.
- CHANGELOG cerrado y versionado formalmente.
- Trazabilidad preservada: los 33 .bak permanecen accesibles en LEGADO para referencia histórica.

**Regla derivada (refuerza AD-26 y AD-25):**
1. AD-26 no es declarativo: se audita y se ejecuta. El find `.bak` debe correrse al cierre de cada sesión que toque archivos.
2. AD-25 se extiende: ninguna sección `[Unreleased]` puede permanecer abierta más de 24h sin registro en CANON.
3. Toda discrepancia entre INDICE_DOCUMENTACION.md y archivos reales se considera bug documental de prioridad alta.


---

## 2026-07-01 — Desactivación de autoridad documental duplicada en shipping_core

### AD-37 — Degradación de `shipping_core/docs/00_ARQUITECTURA.md` a histórico

**Decisión:** Archivar `madenat_lumber_shipping_core/docs/00_ARQUITECTURA.md` como documento histórico y eliminar su autoridad como fuente arquitectónica activa, consolidando la verdad en `CANON/00_ARQUITECTURA.md`.

**Problema:**
- El documento `shipping_core/docs/00_ARQUITECTURA.md` (132 líneas, auditoría 2026-05-08) competía con `CANON/00_ARQUITECTURA.md` como fuente de verdad arquitectónica.
- Declaraba una cadena funcional `Odoo Core → [shipping_core] → madenat_lumber_core` que contradice los `__manifest__.py` reales (core no depende de shipping_core).
- Contenía documentación verificable de los modelos `shipping.vessel`, `shipping.voyage`, `shipping.booking` no presente en CANON.

**Ejecutado:**
1. Contenido verificable de modelos de shipping extraído a `CANON/00_ARQUITECTURA.md` sección 2 (dependencia funcional shipping_core → logistics).
2. Documento original archivado en `LEGADO/auditorias/shipping_core_arquitectura_20260508.md` (valor histórico preservado).
3. Directorio `shipping_core/docs/` eliminado (vacío tras archivo).
4. `shipping_core/README.md` actualizado con referencia explícita a `CANON/INDICE_DOCUMENTACION.md` y `CANON/00_ARQUITECTURA.md`.
5. Dependencia funcional `shipping_core → logistics` documentada formalmente: `shipping_core` no declara `depends` sobre `logistics` pero sus menús son construidos por `logistics` (`shipping_menus.xml` comentado en manifest).

**Impacto:**
- 0 autoridad arquitectónica duplicada en `shipping_core/`.
- CANON/00_ARQUITECTURA.md es la única fuente de verdad arquitectónica del ecosistema.
- Trazabilidad histórica preservada en LEGADO.

**Regla derivada:**
Ningún módulo puede mantener un directorio `docs/` con documentos que compitan con CANON como fuente de verdad. Si un módulo requiere documentación de sus modelos, esta debe residir en CANON o en el README del módulo con referencia explícita a CANON.


---

## 2026-07-01 — Desalineación monetaria documentada: `wood_cost_usd` es `Float`, no `Monetary`

### AD-38 — Trazabilidad de desalineación entre CANON/08_COSTEO y código real

**Decisión:** Documentar que `stock.lot.wood_cost_usd` está implementado como `fields.Float` en el código actual, mientras que `CANON/08_COSTEO.md` sección 2.1 lo declara como `Monetary`. Esta diferencia no es un bug productivo sino un **pendiente de alineación arquitectónica** para cuando el módulo de costeo se retome.

**Problema:**
- `CANON/08_COSTEO.md` sección 2.1 lista `wood_cost_usd` como tipo `Monetary`.
- El código real en `stock_lot.py` lo define como `fields.Float(string='Costo Madera USD', default=0.0)`.
- La migración Float→Monetary documentada en Fase A (`10_AUDITORIA_MONETARIA_FASE_A.md`) no alcanzó a materializarse en todos los campos.

**Ejecutado:**
1. Sección 8 de `CANON/08_COSTEO.md` reformulada como criterio normativo alineado con código real. Eliminada la regla "Monetary siempre" de esa sección.
2. La obligación de migrar a Monetary se mantiene como objetivo arquitectónico en las secciones 1-4 de `CANON/08_COSTEO.md` y en `10_AUDITORIA_MONETARIA_FASE_A.md`.
3. Esta entrada registra la desalineación como **pendiente no bloqueante**, dado que el módulo de costeo está en construcción y el campo funciona correctamente como Float.

**Impacto:**
- La documentación canónica ahora refleja el estado real del código (sección 8).
- La intención arquitectónica monetaria se preserva como objetivo futuro (secciones 1-4 y Fase A).
- Ningún cambio en código.
- Sin riesgo productivo: `wood_cost_usd` funciona correctamente como Float.

**Regla derivada:**
Al documentar migraciones arquitectónicas (como Float→Monetary), el CANON debe distinguir entre:
1. **Objetivo de diseño** (lo que se quiere lograr) — expresado en secciones de arquitectura.
2. **Estado real del código** (lo que está implementado) — verificado contra código antes de afirmarlo como regla operativa.
3. **Pendiente de alineación** (la brecha entre 1 y 2) — registrado aquí, sin considerarlo bug.

<!-- actualizado: 2026-07-01 — AD-38 agregado (desalineación monetaria wood_cost_usd) -->


### AD-40 — Corrección de vigencia documental — arquitectura 7.2.0→7.3.0 y riesgo de parseo disperso en madenat_guia_processing.py

**Decisión:** Actualizar la documentación canónica para reflejar discrepancias de vigencia confirmadas en auditoría de solo lectura (2026-07-08), sin modificar código.

**Cambios documentales ejecutados:**
- `CANON/00_ARQUITECTURA.md` 7.2.0→7.3.0: `core_utils.py` marcado como código muerto, `product_template.py` como huérfano no archivado, `reception_workflow.py` corregido (no es mixin Odoo), 5 archivos activos en `__init__.py` agregados a tabla 3.1 (`validation_checklist_mixin`, `stock_lot_cost_line`, `stock_picking`, `stock_move`, `product_product`), parseo disperso de `madenat_guia_processing.py` documentado en sección 3.3.
- `CANON/02_CONTINUIDAD.md` 9.1.0→9.2.0: riesgo "Parseo disperso en `madenat_guia_processing.py`" (Alta, ABIERTO) agregado a sección 5. Nota de preservación S2S/Blank explícita.

**Impacto:**
- 0 archivos de código modificados.
- 3 documentos canónicos actualizados (`00_ARQUITECTURA.md`, `02_CONTINUIDAD.md`, `04_DECISION_LOG.md`).
- `INDICE_DOCUMENTACION.md` actualizado con nuevas versiones.
- Hallazgos ya confirmados por auditoría previa, esta sesión solo los registra.

**Regla derivada:**
Las discrepancias de vigencia documental detectadas en auditoría deben corregirse en la misma sesión de detección. La documentación canónica es la única fuente de verdad arquitectónica y no puede desalinearse del código.

---

### AD-39 — Archivado de `_cleanup_orphan_moves()` en `lumber_reception.py` (código muerto confirmado)

- **Contexto:** Auditoría `AUDITORIA_ASIMETRIA_DOCUMENTAL_20260706.md` identificó 3 métodos de cleanup de stock.moves huérfanos con ~90% de código duplicado. Los 3 contienen el FIX 2026-07-01 (protección quantity > 0). Uno de ellos, `_cleanup_orphan_moves()` en `lumber_reception.py:3056`, no tiene callers — fue definido para "reutilización y testeo independiente" pero nunca invocado.
- **Evidencia:** grep exhaustivo en todo `custom_addons/` confirma 0 invocaciones. Los 2 métodos sobrevivientes (`reception_service.cleanup_orphan_moves()` y `_cleanup_orphan_moves_guia()`) cubren toda la funcionalidad necesaria.
- **Decisión:** Archivar el método en `_archive/_cleanup_orphan_moves.py` con documentación de procedencia, eliminarlo de `lumber_reception.py`.
- **Commit del cambio:** `9677f53`
- **Commit checkpoint rollback:** `56ef417`
- **Resultado de validación (5/5):**
  1. [x] py_compile sin errores
  2. [x] Actualización de módulo `madenat_lumber_core` en Docker termina con exit code 0
  3. [x] 0 errores/tracebacks en logs de Odoo (solo WARNINGs preexistentes de UI)
  4. [x] 0 referencias rotas al método archivado en `lumber_reception.py`
  5. [x] Los 2 métodos sobrevivientes (`reception_service`, `guia_processing`) siguen presentes y sin modificar
- **Criterio de reversión:** `git reset --hard 56ef417` restaura el estado pre-archivado.
- **Deuda remanente original:** Los otros 2 métodos siguen duplicados (código duplicado x2). Estrategia de unlink divergente (savepoint en guia_processing vs directo en reception_service). 0% cobertura de tests en cualquier método de cleanup.

### Cierre funcional — 2026-07-06 (Fases 2, 3a, 3)

- **Investigación (Fase 2):** La divergencia savepoint vs unlink directo existe desde el baseline inicial (`994bcbd`, 2026-05-31). No responde a un incidente conocido — es una asimetría de diseño sin justificación documentada. Ver sección X de `AUDITORIA_ASIMETRIA_DOCUMENTAL_20260706.md`.
- **Tests pre-consolidación (Fase 3a):**
  - Test A (`d597703`): Valida filtro `protected_moves` + savepoint implícito sobre `cleanable_moves`. ✅ PASS.
  - Test B (`f72d9e9`): Valida aislamiento transaccional del cursor externo cuando el unlink falla dentro del savepoint. ✅ PASS.
- **Consolidación (Fase 3 — `e6a1fc1`):** `reception_service.cleanup_orphan_moves()` unificado al patrón `savepoint + with_context(force_delete=True).unlink()` de `guia_processing._cleanup_orphan_moves_guia()`. Ambos métodos usan ahora la misma estrategia transaccional.
  - **Veredicto:** Asimetría transaccional eliminada. Cobertura de tests: 0% → 2 tests funcionales. Ver sección W de `AUDITORIA_ASIMETRIA_DOCUMENTAL_20260706.md`.

---

### AD-41 — Extracción de `_parse_fraction` a utilidad compartida `parse_fraction_to_decimal_inch` en `utils_uom.py`

- **Contexto:** `_parse_fraction` en `madenat_guia_processing.py:604` era un método de instancia cuasi-puro (sin uso de `self`, solo dependiente de `MM_PER_INCH` y `_logger`) con 5 callers internos confinados a cálculo de volumen. Auditoría del 2026-07-08 confirmó que era el mejor candidato piloto para estrangulamiento incremental del parseo disperso documentado en `00_ARQUITECTURA.md` sección 3.3 y `02_CONTINUIDAD.md` sección 5 (riesgo Alta). Adicionalmente se detectó duplicación del ~90% en `stock_lot._parse_fraction_to_decimal`.
- **Evidencia de idoneidad como piloto:** Categoría A. Función determinista, 0 dependencias de negocio, 0 relación con S2S/Blank, 5 callers de bajo riesgo (cálculo de volumen), validable con 12 casos de prueba unitaria.
- **Decisión:** Extraer a `utils_uom.py` como `parse_fraction_to_decimal_inch(fraction_str)`, función a nivel de módulo. Reemplazar los 5 call sites en `madenat_guia_processing.py`. Consolidar `stock_lot._parse_fraction_to_decimal` como wrapper de 1 línea delegando a la utilidad compartida.
- **Archivos modificados (3):**
  - `models/utils_uom.py` — nueva función pura compartida (~60 líneas)
  - `models/madenat_guia_processing.py` — import añadido, 5 call sites reemplazados, `_parse_fraction` eliminado (~60 líneas netas removidas)
  - `models/stock_lot.py` — import añadido, método delegado a wrapper de 1 línea (~50 líneas removidas)
- **Validación:**
  1. [x] py_compile sin errores en los 3 archivos
  2. [x] 0 referencias huérfanas a `self._parse_fraction` en todo `custom_addons/`
  3. [x] 12 casos de prueba unitaria ALL PASSED (fracción mixta, pura, simple, mm, vacío, heurística >24)
  4. [x] Sin impacto en: `_parse_float_value`, `_compute_vol_shipment_m3`, reglas S2S/Blank, `ingestion_profile`, `reception_parser.py`
- **Resultado neto:** ~110 líneas eliminadas entre los 2 archivos de modelo, duplicación consolidada. Comportamiento semánticamente idéntico.
- **Deuda remanente:** Quedan 9 métodos de parseo disperso en `madenat_guia_processing.py`. Candidato para segundo piloto: `_parse_float_value` (11 callers, Categoría B — requiere evaluación de heurísticas de dominio CLP/espesor/ancho antes de extraer). No ejecutado en esta intervención.
- **Sin impacto en:** `_parse_float_value`, `_compute_vol_shipment_m3`, reglas S2S/Blank, `ingestion_profile`.

---

### AD-47 — Notarización y bitácora inmutable para guía processing (BT-01 CERRADO)

- **Contexto:** BT-01 identificaba que `madenat.guia.processing._create_or_get_lot()` (segundo write path a `stock.lot`) creaba/actualizaba lotes sin Gate 3 ni evidencia de auditoría equivalente a recepción. La bitácora `madenat.audit.log` solo tenía FK `reception_id`.
- **Decisión:**
  1. Cada ciclo exitoso de `action_validate()` firma un snapshot determinista específico de guía mediante SHA-256, **antes** del primer write a `stock.lot`.
  2. El evento `madenat.audit.log` es la **fuente de verdad inmutable** de la evidencia (`audit_snapshot` + `audit_hash`), enlazado relacionalmente a la guía.
  3. `action_reopen_to_draft()` y `action_force_cancel()` no borran ni alteran eventos previos; una revalidación genera un evento nuevo.
  4. No se retro-notarizan los 19 lotes ni guías históricas; protege flujos nuevos.
  5. `madenat.audit.log` gana `guia_processing_id` (Many2one, `ondelete='set null'`) + `audit_snapshot` + `audit_hash` + `action_type='validation_signature'`. `reception_id` no se vuelve obligatorio.
- **Cambios (3 archivos):**
  - `models/ingestion_gate.py` — `Gate3PreCommit.generate_processing_signature(guia, processing_lines)` (método nuevo; `generate_signature()` de recepción intacto).
  - `models/madenat_audit_log.py` — `guia_processing_id`, `audit_snapshot`, `audit_hash`, valor `validation_signature`.
  - `models/madenat_guia_processing.py` — `action_validate()` genera la firma antes del procesamiento y persiste el evento al final (misma transacción → rollback evita eventos huérfanos).
- **Cobertura nueva:** `TestGuiaProcessingValidationSignature` (firma, persistencia, bloqueo sin evento, supervivencia ante cancelación).
- **Validación:** `py_compile` OK; selector BT-01 4/4 passing; suite `madenat_lumber_core` 50 tests, 0 fallos, 0 errores.
- **Sin impacto en:** recepción, Gate 3 existente, `lumber_reception.py`, `reception_service.py`, `stock_lot.py`, BT-02, fórmulas S2S/Blank, UoM, volúmenes, XML, seeds, Docker.
- **Riesgo residual:** los 19 lotes históricos y 2 guías ya procesadas quedan sin firma retroactiva (decisión explícita: no fabricar evidencia histórica). BT-03 (bitácora de recepción con `reception_id` ondelete cascade ampliada solo con columna nueva, sin cubrir aún el ciclo de vida completo de procesados) permanece como deuda separada.

---

### AD-48 — Bitácora operativa de lotes en guía processing (BT-03 CERRADO)

- **Contexto:** BT-03 identificaba que `madenat.audit.log` registraba eventos operativos (`lot_creation`, `lot_update`, `omission`) solo vía recepción; el flujo de Procesados no dejaba evidencia de creaciones, reutilizaciones ni omisiones.
- **Decisión:**
  1. `_create_or_get_lot()` emite `lot_creation` (create real) o `lot_update` (reutilización idempotente de lote sin `reception_id`, tanto en la rama normal como en la posterior a colisión UNIQUE), enlazados a `guia_processing_id`.
  2. `_validar_y_enriquecer_lineas()` emite `omission` para líneas del Excel descartadas antes de estaging (sin código interno / cantidad <= 0 / dimensiones no numéricas o <= 0), reutilizando la semántica de recepción.
  3. Un único evento por outcome confirmado; los `write()` de complemento de `do_full_processing` no duplican `lot_update`.
  4. Se usa `batch_id` para registrar el lote/línea; no se añadieron más columnas relacionales (evita expandir el modelo sin necesidad).
  5. La baja formal de lotes/etiquetas queda **fuera de alcance** (módulo inexistente); no se modelan eventos de "baja" ni "desvinculación histórica".
- **Cambios (2 archivos):**
  - `models/madenat_guia_processing.py` — helper `_register_lot_audit()` + emisión de `lot_creation`/`lot_update` en `_create_or_get_lot()` y `omission` en `_validar_y_enriquecer_lineas()`.
- **Cobertura nueva:** `TestGuiaProcessingOperationalAudit` (A creación, B reutilización única, C omisión, D coexistencia con `validation_signature`).
- **Validación:** `py_compile` OK; selector BT-03 4/4 passing; suite `madenat_lumber_core` 54 tests, 0 fallos, 0 errores.
- **Sin impacto en:** recepción, Gate 1/2/3, `lumber_reception.py`, `reception_service.py`, `stock_lot.py`, BT-01, BT-02, fórmulas S2S/Blank, UoM, XML, seeds, Docker.
- **Riesgo residual:** la bitácora cubre la evidencia operativa del flujo actual; la baja formal requiere un módulo futuro y sigue como BT-04.

---

### AD-49 — Salida controlada a proceso para guías service (BT-04 CERRADO)

- **Contexto:** BT-04 identificaba que `madenat.guia.processing` trataba `compra` y `service` con el mismo write path entrante. En `service` (maquila sobre madera propia) los lotes crudos de origen nunca salían de stock, sin evidencia documental de la salida. `stock_scrap` se descartó semánticamente (el producto no se destruye: se transforma y retorna).
- **Decisión:**
  1. `compra` permanece intacta: sin salida de stock.
  2. `service` genera **exactamente una** salida controlada hacia `Virtual Locations/Production` (picking `outgoing` con `stock.move` + `stock.move.line` por lote crudo), reutilizando el patrón de `madenat_toll_processing._create_consumption_picking`. No se usa `stock.scrap`.
  3. Idempotencia vía `consumption_picking_id` (Many2one `stock.picking`, `copy=False`, `index=True`): una revalidación reutiliza la salida existente, no duplica el descuento.
  4. Trazabilidad informativa (no genealogía contable): `source_lot_ids` (M2M) referencia los lotes crudos; no se fuerza `parent_lot_id`.
  5. Reversión sin borrar historia: `_reverse_consumption_picking()` crea un retorno entrante inverso (`Return of …`) que repone el quant del lote crudo copiando las `move_line` originales. El picking original permanece en `done`.
  6. Bloqueo de validación `service` sin lote crudo identificable (aborta la transacción completa, sin ingreso huérfano).
  7. Evidencia auditiva: nuevo `action_type='consumption'` en `madenat.audit.log`, coherente con BT-03.
- **Cambios (3 archivos):**
  - `models/madenat_guia_processing.py` — campos `source_lot_ids`/`consumption_picking_id`; `_get_or_create_consumption_picking()`; `_reverse_consumption_picking()`; hook `action_validate()` (service); reversión en `action_force_cancel()` y `action_reopen_to_draft()`.
  - `models/madenat_audit_log.py` — valor `consumption` en `action_type`.
  - `tests/test_guia_processing.py` — clase `TestGuiaProcessingConsumptionBT04`.
- **Cobertura nueva:** `TestGuiaProcessingConsumptionBT04` (A salida única, B revalidación sin duplicar, C compra sin salida, D reversión preservando historia, E bloqueo sin lote).
- **Validación:** `py_compile` OK; selector `guia_processing` 46 tests, 0 fallos, 0 errores; suite `madenat_lumber_core` 79 tests, 0 fallos, 0 errores.
- **Sin impacto en:** `compra`, Gate 1/2/3, `lumber_reception.py`, `reception_service.py`, `stock_lot.py`, BT-01/BT-02/BT-03, fórmulas S2S/Blank, UoM, XML, seeds, Docker.
- **Riesgo residual:** las mermas reales del proceso (diferencia de yield) no se modelan como scrap; se documenta como deuda separada. No se retro-aplica la salida a las 2 guías `service` históricas ya validadas.

---

### AD-50 — `madenat_lumber_intake` como fachada de ingreso global (nombre + dependencia), no núcleo paralelo

- **Fecha:** 2026-08-16
- **Decisión:** Crear el módulo `madenat_lumber_intake` como **puerta única de ingreso global** (fachada), dependiente de `madenat_lumber_core`, sin lógica de negocio en su primera iteración. No reemplaza ni reescribe `lumber.reception` ni `madenat.guia.processing`; solo reutilizará sus Gates y piezas cuando se implemente el enrutamiento.
- **Nombre técnico:** `madenat_lumber_intake` (coherente con el prefijo `madenat_lumber_*` del ecosistema y con la semántica de ingreso).
- **Dependencia:** `madenat_lumber_core` como única dependencia directa. No depende de `madenat_lumber_logistics`, `costing`, `purchasing`, `billing` ni `vendor_payment`.
- **Límites de la iteración actual (esqueleto):** solo un modelo mínimo `madenat.lumber.intake.wizard` (validación de instalación), vistas (form/list), acción y menú. **Sin** campos de archivo, parseo, Gates, firma ni relación con `lumber.reception` / `madenat.guia.processing`.
- **Acceso:** ACL ligada a `madenat_lumber_core.group_madenat_operaciones` (r/w/c, sin unlink). Reglas de registro vacías hasta iteraciones futuras.
- **Regla derivada:** `madenat_lumber_intake` es fachada, no un núcleo paralelo. Cualquier ingesta nueva debe delegar en los modelos/Gates existentes del core; se prohíbe duplicar modelos paralelos de `stock.lot`, `stock.picking` o `stock.move`.
- **Validación:** instala limpio en `madenat_test` (87 módulos, 0 errores, 0 tracebacks). Ver `CANON/02_CONTINUIDAD.md` §8.

---

### AD-51 — Dos dominios de parseo deliberados en la puerta única de ingreso (Producto vs Procesado)

- **Fecha:** 2026-08-16
- **Decisión:** `madenat_lumber_intake` expone una sola puerta visible (Ingreso de Madera) pero implementa **dos dominios de parseo deliberadamente distintos**, sin estructura de datos única entre ambos flujos:
  - **Producto / Madera Bruta / Compra** → `lumber.reception` vía `action_process_documents()` (Gate0/Gate1 nativos). La prelectura usa exclusivamente `madenat.reception.parser.parse_excel(bytes, profile)` como preview informativo; el core vuelve a procesar el archivo con su método canónico.
  - **Procesado / Servicio / Maquila** → `madenat.guia.processing` vía `action_verify_data()` con el **Excel original** (sin prelectura ni preparseo). El parser nativo `_parse_excel_data_core()` es el único que implementa forward-fill de `N° LOTE`.
- **Prohibición estricta (riesgo de pérdida de filas huérfanas):** para Procesados queda PROHIBIDO llamar `madenat.reception.parser.parse_excel()` (dropna package_no/pieces/volume_m3 elimina filas sin lote explícito), usar `force_packing_data`, traducir `lines`→`lineas` o inyectar datos preparseados.
- **Volumen:** Intake nunca recalcula M3. El M3 fuente del Excel se conserva en Producto (flujo existente) y en Procesado (archivo fuente + reglas nativas de validación posteriores). No se implementan fórmulas, conversiones ni ajustes de volumen en intake.
- **Costo de procesado:** `additional_cost` / `service_*` es costo de servicio/maquila; el core lo registra con `cost_type='processing'`. Intake NO mapea precio, costo, additional_cost, rate_usd ni service_unit_price_clp.
- **Auditoría de origen:** cada derivación exitosa genera exactamente un evento en `madenat.audit.log`, reutilizando el contrato existente (sin action_type ni campos nuevos): `action_type='creation'`, `description` con tipo/modelo/id/archivos/guía, `batch_id='intake:<wizard_id>'`. No se duplica `validation_signature`, `lot_creation`, `lot_update` ni `omission`, ni se guardan binarios/hashes.
- **Campos exigidos por Guía Procesado:** `tipo_recepcion='service'` (decisión funcional) y `assignment_location_id` expuesto como selector editable en el wizard (no se inventa un patio por defecto).
- **Riesgo residual (fuera de alcance de intake):** un mismo `N° LOTE` + `Código Interno` repetido en varias filas puede causar overwrite en `_create_or_get_lot` del core.

---

### AD-52 — Blindaje server-side de vinculación de OC en Intake

- **Fecha:** 2026-08-19
- **Decisión:** La asociación manual de una `purchase.order` en la fachada de Producto (`madenat.lumber.intake`) queda blindada en servidor dentro de `madenat.lumber.intake.po.link.action_confirm_link()`, **antes** de escribir `purchase_id`. El dominio XML del selector es solo ayuda de UX; la barrera definitiva es la validación server-side (no eludible por RPC/contexto manipulado).
- **Validaciones obligatorias (en orden):**
  1. **Proveedor obligatorio:** la recepción debe tener `supplier_id`. Si falta, el wizard bloquea con: "Primero debe validar o corregir el proveedor de la recepción antes de vincular una Orden de Compra." (La ingesta preliminar NO queda bloqueada; solo la resolución manual de OC.)
  2. **Proveedor de la OC:** la OC seleccionada debe tener `partner_id`. Una OC sin proveedor se rechaza.
  3. **Coincidencia por `commercial_partner_id`:** se compara `reception.supplier_id.commercial_partner_id` vs `po.partner_id.commercial_partner_id`, soportando empresa matriz/sucursal sin comparar solo IDs directos.
  4. **Compañía activa:** si `po.company_id` y `self.env.company` existen y difieren, se rechaza la OC de otra compañía (compatible single-company, sin hardcodear).
  5. **Estado de OC:** solo `draft`, `sent`, `purchase`, `done`; se rechazan canceladas y archivadas (`active=False` si el campo existe).
  6. **Estado de recepción:** se bloquea en `done`, `cancel`, `error` y cuando existen `lot_ids` o `picking_id` (avance real a stock).
  7. **No sobrescritura silenciosa:** si la recepción ya tiene `purchase_id`, se bloquea el reemplazo automático; se exige una operación trazable para desvincular antes de vincular otra.
- **Trazabilidad:** al vincular una OC válida, `message_post` registra OC asociada, proveedor validado y origen "vinculación manual desde Intake (Producto)". `oc_reference_raw` y `manual_po_name` no se sobrescriben. `oc_match_status='manual'` y `oc_match_note` conservan la referencia documental.
- **Política de OC pendiente:** la OC pendiente **no bloquea** la ingesta preliminar ni el envío operativo inicial a stock. La exigencia final de OC resuelta pertenece a **Costeo y Valorización / cierre financiero**, no a Operaciones.
- **Prohibido:** no se crea `purchase.order` automáticamente; no se crean proveedores, productos, precios, cantidades o referencias; no se toca stock, volúmenes, costos, lotes, pickings ni Procesado.

---

### AD-53 — Diferencia de política de OC: Procesados vs Producto

- **Fecha:** 2026-08-19
- **Contexto:** Tras auditoría de solo lectura del flujo real de Procesados (`madenat_guia_processing.py`, 4.549 líneas) se confirmó que la política de OC de Procesados es **intencionalmente distinta** de la política vigente de Producto (Intake, AD-52). La documentación previa (CANON 08 §9) no distinguía este comportamiento.
- **Decisión (documental, sin cambio de código):**
  1. **Procesados (core) bloqueaba en `action_validate` — ESTADO HISTÓRICO, superado por AD-54 (2026-08-19):** si `madenat.guia.processing.oc_reference_raw` existía y `order_id` estaba vacío, `action_validate()` (y `action_process_from_staging()`) lanzaba `UserError` impidiendo el envío a stock. Evidencia histórica: `madenat_guia_processing.py:1420-1427` y `1552-1559`. AD-54 sustituyó ese bloqueo por una advertencia no bloqueante con registro en chatter. El core ofrece el botón "📄 Crear OC desde PDF" (`action_create_purchase_order_from_document`) como vía explícita de creación de `purchase.order` en `draft`.
  2. **Producto (Intake) no bloquea por OC pendiente:** la fachada expone `oc_pending`/`oc_pending_alert` como estado no bloqueante y la vinculación manual valida en servidor (AD-52).
  3. **Ausencia de blindaje en Procesados:** Procesados **no** valida en servidor `commercial_partner_id`, compañía, estados de OC, ni impide sobrescritura silenciosa de `order_id`; tampoco deja trazabilidad en chatter al vincular manualmente una OC (solo al crear una PO nueva vía `action_create_purchase_order_from_document`, que sí usa `message_post`).
  4. **Ausencia de wizards:** no existen wizards de vinculación manual de OC ni de corrección de proveedor para `madenat.guia.processing` (los existentes `madenat.lumber.intake.po.link`/`supplier.link` son exclusivos de Producto/lumber.reception).
  5. **La política de Intake (AD-52) NO aplica directamente a Procesados:** AD-52 gobierna exclusivamente la vinculación manual del flujo Producto.
- **Reglas derivadas:**
  - Esta diferencia es **intencional** y **no debe alterarse en `madenat_lumber_core`**.
  - La exigencia final de OC resuelta **sigue perteneciendo a Costeo/Valorización/cierre financiero** (ver `08_COSTEO` §9), pero Procesados tiene un blindaje adicional más temprano en el core.
  - Cualquier ajuste futuro de la política de OC en Procesados debe venir de la **fachada Intake**, no del core.
- **Fuente:** `madenat_guia_processing.py` (bloqueos L1420-1427, L1552-1559; creación de PO L2972-3074); `madenat_lumber_intake` (wizards Producto); `CANON/02_CONTINUIDAD` §9.
- **Validación:** investigación de solo lectura; sin cambios de código. La diferencia queda registrada para evitar que se confunda con un defecto o una desalineación accidental.

---

### AD-54 — Excepción puntual autorizada: eliminación del bloqueo de OC pendiente en Procesados (core)

- **Fecha:** 2026-08-19
- **Autorizado por:** el responsable del proyecto (autorización explícita de fecha 2026-08-19). **Excepción puntual; no constituye precedente.**
- **Contexto (evidencia) — antecedente histórico superado por esta decisión:** antes de AD-54, `madenat.guia.processing.action_validate()` bloqueaba el envío a stock con `UserError` si `oc_reference_raw` existía y `order_id` estaba vacío (`madenat_guia_processing.py:1552-1559`). Ese comportamiento diferenciaba a Procesados de Producto (Intake), donde la OC pendiente no bloquea (AD-52). AD-54 sustituyó el bloqueo por una advertencia no bloqueante con registro en chatter.
- **Decisión:** se autoriza modificar **exclusivamente** este bloqueo específico dentro de `madenat_lumber_core`, en `action_validate()`, para convertirlo en **advertencia no bloqueante** (OC pendiente no impide el envío a stock), homologando así la política entre Producto y Procesados.
- **Justificación:** alinear con la política global "OC pendiente no bloquea la ingesta ni el envío a stock" (AD-52), manteniendo la exigencia final de OC resuelta en Costeo/Valorización/cierre financiero (08_COSTEO §9).
- **Alcance de la excepción — AMPLIADO 2026-08-19 (ÚNICAMENTE estos 2 métodos):**
  - Bloqueo de OC en `action_validate` de `madenat.guia.processing` (L1552-1559).
  - Bloqueo de OC en `action_process_from_staging` de `madenat.guia.processing` (L1420-1427).
  - Sustitución por advertencia no bloqueante (log/warning + `message_post`), sin escribir stock.
- **Justificación de la ampliación (2026-08-19):** `action_process_from_staging` es una etapa de borrador/staging previa a la validación final (`action_validate`); mantener el bloqueo ahí sería más restrictivo que la puerta final y rompería la homologación completa. Ambas vías hacia `do_full_processing()` deben compartir la política "OC pendiente no bloquea". `action_validate` conserva TODAS sus demás validaciones (nominales, subproductos, tipo de cambio, notarización BT-01) intactas; solo se remueve el bloqueo específico de OC en ambos métodos.
- **Fuera del alcance (NO se toca):** BT-01/02/03/04, Gate 3, `do_full_processing`, `_create_or_get_lot`, `_create_picking_and_lines`, otras partes de `madenat.guia.processing`, stock, lotes, pickings, movimientos, volúmenes ni Procesado.
- **Naturaleza:** excepción puntual y autorizada explícitamente. **No** deroga la regla general "prohibido modificar `madenat_lumber_core`".
- **Regla general vigente:** sigue prohibido modificar `madenat_lumber_core` en cualquier otro caso no cubierto por esta excepción. Cualquier futura modificación del core requiere nueva autorización explícita.
- **Relación con AD-53:** AD-53 (diferencia intencional de política Procesados vs Producto) queda **superado** por AD-54 en cuanto a la diferencia de bloqueo; se conserva como referencia histórica de la decisión previa.

---

### AD-55 — Homologación de "Modificar origen" para Procesados mediante fachada ligera en Intake

- **Fecha:** 2026-08-19
- **Contexto (evidencia):** en `madenat_lumber_intake/models/intake_console.py:417-451`, `action_open_source()` abre el registro origen real en formulario. Para Producto (`ingestion_type == 'product'`) asigna `view_id` explícito a `madenat_lumber_intake.view_lumber_reception_intake_facade_form` (fachada ligera dedicada "Modificar origen — Producto"). Para Procesados (`ingestion_type != 'product'`) **no asigna `view_id`**, por lo que Odoo abre la vista por defecto de `madenat.guia.processing`, que es el form estándar pesado del core (`guia_processing_views.xml`).
- **Decisión:** crear una **vista de formulario ligera de `madenat.guia.processing` en `madenat_lumber_intake`** (equivalente en planteamiento a `view_lumber_reception_intake_facade_form`) y hacer que `action_open_source()` la seleccione cuando el flujo sea Procesados (`ingestion_type != 'product'`), manteniendo `terminal = src.state == 'validated'`.
- **Alcance (ÚNICAMENTE Intake):**
  - Nueva vista XML en `madenat_lumber_intake/views/` para `madenat.guia.processing` (fachada ligera).
  - Ajuste de `action_open_source()` (Python en intake) para asignar el `view_id` de la nueva fachada en el flujo Procesados.
- **Exclusiones explícitas:**
  - NO tocar `madenat_lumber_core` para esta mejora (AD-54 aplica solo al desbloqueo de OC, no a vistas).
  - NO modificar la vista estándar `guia_processing_views.xml` ni `guia_processing_list_search.xml`.
  - NO crear wizard nuevo (la fachada es una vista, no un TransientModel).
  - NO alterar lógica de negocio, stock, lotes, pickings, movimientos ni volúmenes.
- **Justificación:** la diferencia reportada es **exclusivamente de UX/vista** (no de lógica de negocio): Procesados cae en la vista por defecto del core porque `action_open_source` no le asigna un `view_id` propio. Homologar la experiencia de usuario de "Modificar origen" entre Producto y Procesados requiere una fachada ligera propia en Intake, sin tocar la arquitectura del core.
- **Regla derivada:** toda ventana de "Modificar origen" de flujos de ingesta debe abrir una vista ligera definida en `madenat_lumber_intake` (fachada), nunca la vista estándar completa del core. La vista estándar del core permanece como fallback/operación completa.
- **Implementación (2026-08-19, alineada al código actual):** la fachada ligera de Procesados (`view_madenat_guia_processing_intake_facade_form`) fue implementada y alineada al patrón de Producto:
  - Se abre desde `action_open_source` (consola) asignando `view_id` de la fachada en el flujo Procesados.
  - Tabs visibles: `Guía y comercial`, `Proceso`, `Packing` (renombrado desde `Detalle`). No se expone `Trazabilidad` en la fachada.
  - Acciones visibles: `Verificar Datos` (`action_verify_data`), `Volver a Ingreso de Madera` (`action_back_to_intake_console`), `⚡ Fijar Nominal Masivo` (acción window del core reutilizada). No se expone envío a stock (queda centralizado en la consola vía `action_send_to_stock`).
  - `action_back_to_intake_console` abre el **registro concreto del hub** `madenat.lumber.intake.console` en vista form (`res_id=900000000+self.id`, `view_madenat_lumber_intake_console_form`), no una lista filtrada.
- **Estado del frente:** implementado y alineado al código actual; **sujeto a validación funcional continua** (no se declara cerrado el frente Procesados/Intake).
- **Validación:** verificación estática y funcional en base aislada `madenat_test` (tabs, retorno al hub, botones, upgrade 87 módulos sin errores); pruebas visuales definitivas pendientes de entorno con fixture `validated`.

<!-- actualizado: 2026-08-19 — AD-55 registrado (homologación UX de 'Modificar origen' para Procesados via fachada ligera en Intake) — implementado y alineado, frente no cerrado -->

---

## 2026-08-20 — Robustecimiento del Core de perfiles de ingesta (commit `1466f24`)

### AD-56 — Reactivación del candado anti-mezcla comercial en Procesados vía `ingestion_profile`

- **Decisión:** `madenat.guia.processing` incorpora `ingestion_profile` Selection con los mismos values de `lumber.reception` (`f1550`, `f5085`, `metric`; default `f5085`), visible/editable en el form del core. Con esto, el candado de `madenat_guia_mass_update` (`hasattr(guia, 'ingestion_profile')` + `forbidden_in_lock`) deja de ser código muerto y protege contra mezcla comercial real.
- **Motivo:** auditoría confirmó que `madenat.guia.processing` no tenía el campo, por lo que el candado nunca se ejecutaba.
- **Consecuencia práctica:** perfiles `f5085` vuelven a bloquear subproductos S2S/RIP en el candado; `f1550`/`metric` conservan su semántica. Cobertura de tests: `TestGuiaProcessingIngestionProfileLock`.

### AD-57 — Completar catálogo `blanks` en los modelos hermanos y helper centralizado

- **Decisión:** `lumber.blank.nominal.map`, `lumber.profile.subproduct.rule`, `lumber.export.formula` y `lumber.thickness.visual.rule` aceptan ahora el value `blanks` (antes solo lo tenía `lumber.ingestion.format`). `madenat.ingestion_config.get_profile_subproduct_rules` gana entrada legacy explícita para `blanks`.
- **Motivo:** el fallback silencioso a Fase 1/hardcode legacy no dejaba warning ni registro visible al operador.
- **Consecuencia práctica:** la selección de perfil `blanks` ya no cae a un vacío sin control; se documenta y prueba que `lumber_export_formula._resolve_for_profile('blanks')` resuelve **intencionalmente** a la ruta S2S/imperial definida por el dominio (el parser mapea blanks → `export_rule_outcome='f1550'`), **no** a `metric`. Cobertura de tests: `TestBlankProfileCatalogComplete`.

### AD-58 — Renombrado de labels de Selection sin alterar values técnicos

- **Decisión:** se renombraron únicamente los labels visibles de los Selection de perfiles en los módulos Core/Intake (`f5085→'Madera Bruta — Grado Clear'`, `f1550→'Madera Aserrada S2S'`, `blanks→'Blanks — Legado (métrico/imperial híbrido)'`, `metric→'Madera Bruta — Sistema Métrico'`; `ingestion_profile` de recepción/guía con emojis conservados).
- **Motivo:** reducir confusión operativa entre profiles.
- **Consecuencia práctica:** PostgreSQL solo persiste la key (`f5085`, `f1550`, `metric`, `blanks`); ninguna vista, dominio, filtro ni comparación depende del string del label (verificado por grep). **No requiere migración de datos.** Ningún value técnico cambió.

### AD-59 — Gap diferido: `origin_scope` para diferenciar reglas por origen (Producto vs Procesados)

- **Decisión:** NO se implementa `origin_scope` en esta iteración. El catálogo `lumber.profile.subproduct.rule` sigue indexado solo por `profile`, por lo que Producto (`lumber.reception`) y Procesados (`madenat.guia.processing`) comparten el mismo universo de reglas por perfil.
- **Motivo:** la diferenciación por origen es una mejora estructural que requiere propagar un campo nuevo vía `with_context` desde los wizards de origen y extender el helper centralizado; se difiere para no ampliar el alcance del cierre técnico.
- **Consecuencia práctica:** el cruce de reglas de subproducto sigue existiendo por diseño (limitación conocida). Queda documentada como deuda técnica explícita en el encabezado de `lumber_profile_subproduct_rule.py`, en `02_CONTINUIDAD.md` §11 y en esta entrada. Frente abierto en continuidad.

---

## 2026-09-08 — Asimetría de regex de RUT entre Producto y Procesado (Defecto A, BT-05)

### AD-60 — Ampliación del regex de RUT del proveedor en `reception_parser` (patrón "sin puntos")

- **Fecha:** 2026-09-08
- **Problema (contexto):** el flujo Producto (`reception_parser.parse_dispatch_guide`) usaba un único regex de RUT que solo admitía formato **con puntos** (`\d{1,2}\.\d{3}\.\d{3}-[\dkK]`), mientras que el flujo Procesado (`madenat_guia_processing._parse_dispatch_pdf`, L2372-2375) ya soportaba **con y sin puntos** (`\d{7,8}-[\dkK]`). Esta asimetría (BT-05, parseo disperso) hizo que la guía real 26270 —cuyo RUT de proveedor es `77066489-6` (sin puntos)— fallara la extracción y, aguas abajo, `lumber_reception._find_or_create_po_intelligent` lanzara "No se detectó RUT del proveedor en el PDF".
- **Decisión:** ampliar el regex en `reception_parser.py` (L565) agregando el patrón "sin puntos" (`\d{7,8}-[\dkK]`) como alternativa OR, **conservando intacto** el patrón "con puntos" existente. Se normaliza también el filtro de exclusión del RUT MADENAT (L569) para operar contra ambos formatos: se compara el cuerpo del RUT sin puntos (`76103087`) sobre `found_rut.replace('.', '')`, sin hardcodear un segundo literal.
- **Alcance explícito:** cubre **únicamente el Defecto A (regex)**. NO se modifica el `raise UserError` de `lumber_reception._find_or_create_po_intelligent` (L2302-2306). El **Defecto B** (bloqueo ante RUT ausente / caso legítimo "PDF sin RUT") permanece **abierto** y pendiente de decisión de producto, identificado como **Defecto B (bloqueo UserError)**.
- **Evidencia:** la sesión previa de tests de aislamiento registró 4 failed / 8 tests (`rut_sin_puntos`, `fixture_regresion_26270`, `sin_rut_visible_no_crashea`, `sin_rut_no_bloquea`). Tras el fix: **6 PASS / 2 FAIL** — los 2 fallos restantes son exclusivamente del Defecto B (`sin_rut_visible_no_crashea`, `sin_rut_no_bloquea`). Suite completa del módulo sin regresiones atribuibles a este cambio (los fallos residuales de `test_supplier_resolution` y `test_guia_processing` son data preexistente en la BD dev, no relacionados).
- **Módulos afectados:** `madenat_lumber_core` (`models/reception_parser.py`).
- **Relación con BT-05:** cierra la divergencia puntual del regex de RUT entre Producto y Procesado, sin abordar aún la unificación estructural del parseo disperso (deuda de mediano plazo).

---

## 2026-09-08 — Clasificación de tipo de ingreso por contenido (routing Intake)

### AD-61 — Clasificación de `tipo_ingreso` por contenido del documento, con fallback manual visible

- **Fecha:** 2026-09-08
- **Problema (contexto):** el routing Producto/Procesado del wizard de Intake se decidía por el **nombre de archivo** (`_onchange_suggest_tipo_ingreso` solo inspeccionaba `excel_filename`/`pdf_filename`), con `default='producto'` silencioso y el campo `tipo_ingreso` oculto (`invisible="1"`). La guía real 26270 —cuya glosa es "SERVICIO DE CEPILLADO"— cayó a Producto porque el nombre de archivo (`26270.pdf`) no traía keyword. Confirmado por tests de aislamiento (4 failed / 5 tests contra el código previo).
- **Decisión:** clasificar por el **CONTENIDO del documento** (texto extraído del PDF con `document_extractor._extract_pdf_text`, reutilizada sin duplicar lógica), conservando el nombre de archivo como señal adicional (OR). Se agrega `tipo_ingreso_auto_detectado` (Boolean). Si hay match → `tipo_ingreso='procesado'` y `auto_detectado=True`. Si **no** hay match → `auto_detectado=False` + `warning` visible, y el campo `tipo_ingreso` se vuelve editable (`invisible="tipo_ingreso_auto_detectado"`). **No** se fuerza `tipo_ingreso` silenciosamente.
- **Regla de clasificación (NUNCA por proveedor):** la clasificación es **por documento**, nunca por `supplier_id`/`partner_id`/RUT. Evidencia: el proveedor `77066489-6` (FERRAMENTA) tiene 3 guías Procesado y puede emitir también guías de venta de madera (Producto); usar el RUT forzaría un flujo único y erróneo.
- **Evidencia:** `test_intake_tipo_ingreso_content.py` (5 tests) pasa **5/5**. Suite completa `madenat_lumber_intake`: **63 tests, 0 failed, 0 errors**. Suite `madenat_lumber_core`: sin regresiones cruzadas.
- **Módulos afectados:** `madenat_lumber_intake` (`models/intake_wizard.py`, `views/intake_wizard_views.xml`).
- **Relación con BT-05:** reduce otra arista del parseo disperso (la clasificación de flujo ahora se basa en el texto extraído, no en metadata del archivo). La unificación estructural del parseo sigue como deuda de mediano plazo.
- **Decisión de UX (Product Owner, confirmada 2026-09-08):** el campo `tipo_ingreso` permanece **SIEMPRE oculto** (`invisible='1'`), priorizando velocidad operativa y la visión de reducir fricción del operador (objetivo a futuro: prescindir de doble ingesta manual). Se investigó exhaustivamente el repositorio (WIKI, decisiones, minutas, git log/stash/reflog) sin encontrar respaldo documental de esta política previa a esta fecha — se deja registrada aquí formalmente para que futuras sesiones no repitan la incertidumbre. La mitigación de riesgo para el caso 'sin keyword detectada' es el warning emergente (no bloqueante) más la mejora de detección por CONTENIDO (no por nombre de archivo), que reduce significativamente la tasa de fallos silenciosos observada en el caso real de la guía 26270, aunque no la elimina al 100% para redacciones no cubiertas por las 4 keywords actuales.

---

## 2026-09-08 — Tipo de cambio no registrado no bloquea el ingreso a stock (guías service)

### AD-62 — `rate_usd=1.0` como marca de "no registrado" (aviso no bloqueante)

- **Fecha:** 2026-09-08
- **Problema:** guías de servicio sin tipo de cambio impreso en el PDF (caso real: guía 26270, PDF completo verificado, sin línea "T/C U$") bloqueaban el ingreso a stock con `rate_usd=1.0` mediante `UserError` en `action_process_from_staging` (L1463) y `action_validate` (L1605), impidiendo la operación diaria pese a que el dato simplemente no existe en el documento origen del proveedor.
- **Decisión:** `rate_usd=1.0` se mantiene como marca de "no registrado en la guía" (valor imposible de confundir con un T/C real, que en los casos reales del sistema ronda 959-963). Se reemplaza el `raise UserError` bloqueante por un aviso no bloqueante, usando exactamente el mecanismo ya implementado y probado:
  ```python
  _logger.warning(
      "Tipo de cambio no registrado en la guía %s (rate_usd=1.0). "
      "Aviso no bloqueante: verificar antes del cierre de costeo.",
      self.name,
  )
  self.message_post(
      body=_(
          "⚠️ Tipo de cambio no registrado en la guía (rate_usd=1.0). "
          "Verificar antes del cierre de costeo."
      ),
      message_type='notification',
  )
  ```
  Se preserva intacto el bloqueo de `rate_usd <= 0` (campo realmente vacío/inválido, distinto del default 1.0).
- **Alcance explícito:** la responsabilidad de completar/verificar el tipo de cambio se traslada al cierre de Costeo (Fase 4) y Auditoría, no a Operaciones en el punto de ingreso. PENDIENTE (fuera de esta sesión): agregar filtro/columna visible en `madenat_lumber_reports` o en `lumber.shipment.cost.line` para que Costeo detecte fácilmente estas guías antes del cierre financiero, filtrando por `rate_usd=1.0` AND `tipo_recepcion='service'`.
- **Evidencia:** simulación real vía odoo shell con savepoint (rollback) confirmó procesamiento completo sin bloqueo y advertencia visible en chatter (3 mensajes registrados). Suite completa `madenat_lumber_core`: 114 tests, 6 failed — los mismos 6 fallos preexistentes/esperados ya documentados en AD-60/AD-61 (Defecto B + data residual dev), 0 regresiones nuevas atribuibles a este cambio.
- **Relación con BT-05 / Defecto B:** aplica el mismo principio de "no bloquear operación por dato ausente, marcar y resolver aguas abajo" ya recomendado para el Defecto B (RUT ausente en flujo Producto), que sigue ABIERTO y pendiente de implementación — no confundir ambos defectos, son independientes.
- **Módulos afectados:** `madenat_lumber_core` (`models/madenat_guia_processing.py`).

---

## 2026-08-31 — Contrato Producto Maestro / Subproducto (Fase 2)

### AD-ING-001 — Producto maestro configurable por tipo de ingreso

- **Fecha:** 2026-08-31
- **Contexto:** el valor extraído del Excel/guía se trataba como `product_id`, generando un producto distinto por guía.
- **Decisión:** `product_id` es una categoría general mantenible resuelta desde `madenat.lumber.product.default` por tipo de ingreso (`bruta`/`procesado`), refinable por perfil y compañía. Único punto de resolución: `madenat.ingestion.config.get_default_product(...)`. No se hardcodea ni se deriva del Excel.
- **Consecuencias:** cada línea de ingesta recibe un producto maestro estable; la clasificación comercial vive en el subproducto.
- **Módulos afectados:** `madenat_lumber_core` (modelo + helper), `madenat_lumber_intake` (presentación).

### AD-ING-002 — Texto Excel como subproducto con autocreación controlada

- **Fecha:** 2026-08-31
- **Contexto:** la columna `Producto`/`Descripción`/`Especie`/`Subproducto` del Excel representa la clasificación comercial, no el producto.
- **Decisión:** el texto se asigna a `subproducto_id` (Procesado) / `subproduct_id` (Bruta). Si no existe, se autocrea en `madenat.subproducto` vía `find_or_create_lumber_subproducto`. Se conserva el texto original (`product_name_original`/`excel_product_name`) para trazabilidad.
- **Consecuencias:** no hay bloqueo de ingesta por subproducto inexistente; el catálogo crece de forma controlada desde el Excel.
- **Módulos afectados:** `madenat_lumber_core` (mixin + mapeos), `madenat_lumber_intake` (vistas).

### AD-INT-001 — Precisión volumétrica estándar de tres decimales

- **Fecha:** 2026-08-31
- **Contexto:** el total de la columna "Vol. Stock" se mostraba con 2 decimales (`51,87` en vez de `51,874`).
- **Decisión:** toda salida de volumen se muestra con exactamente 3 decimales. `Volumen total (m³)` = Σ `vol_shipment_m3`; `Volumen stock (m³)` = Σ `vol_purchase_m3`. No se muestran totales numéricos sin etiqueta. No se modifica cálculo ni datos almacenados.
- **Consecuencias:** claridad visual y consistencia con la política documentada de 3 decimales.
- **Módulos afectados:** `madenat_lumber_intake` (`intake_console`).

---

## 2026-09-12 — Diagnóstico de `madenat_ingestion_engine` (módulo sin trazabilidad CANON)

### AD-63 — Estado real y brechas de `madenat_ingestion_engine` (registro de diagnóstico, sin diseño)

- **Fecha:** 2026-09-12
- **Naturaleza:** diagnóstico de solo lectura (sin cambios de código, BD ni configuración). Registra una brecha de trazabilidad y alcance; **no** decide una solución ni un diseño.
- **Hechos verificados:**
  - `madenat_ingestion_engine` está `installed` en `madenat_test` (`ir_module_module`: `18.0.1.0.0`, write_date 2026-09-08) y tiene un consumidor activo real: `madenat_lumber_intake` declara `depends` sobre él e invoca `extract_document()` (preview/perfil) y `_extract_pdf_text()` (auto-clasificación Producto/Procesado) en `intake_wizard.py`.
  - El contenido es código funcional, no stubs: extracción Excel con perfiles métrico/imperial, scoring de columnas, forward-fill, síntesis de lote y warnings por fila. Excepción: `ingestion_column_profile.py` es un esqueleto explícito de 4 campos (`name`, `sequence`, `active`, `notes`), sin campos de layout/posiciones/regex/unidades.
  - La extracción PDF hoy solo cubre cabecera por regex: `extract_document()` sobre PDF devuelve `lines=[]`; no hay extracción de tablas con layout configurable.
  - El módulo no tiene historial en CANON ni en git (directorio untracked, nunca commiteado). Su documentación vive solo en su propio `README.md`/`docs/`, con inconsistencias internas (declara "fase 0 esqueleto / sin integración" pese a estar integrado y activo).
  - Superposición de responsabilidad con `reception_parser.py` (ambos parsean Excel/PDF con pandas/openpyxl/pdfplumber); hoy complementarios por consumidor distinto, con duplicación latente.
  - Los tests del módulo no fueron ejecutados en este diagnóstico (la restricción de solo lectura evita `--test-enable`); solo hay evidencia indirecta de compilación (`.pyc` presentes, módulo instalado sin error).
- **Brechas pendientes (sin propuesta de diseño):** (1) extracción de tablas PDF con layout configurable no cubierta; (2) "recepción a granel sin detalle de piezas" no modelada en ningún esquema actual (todo asume línea por línea); (3) trazabilidad CANON/git del módulo pendiente.
- **Criterio registrado (diagnóstico de viabilidad, no diseño):** la evidencia indica que extender el motor existente (reutilizando perfiles, `column_matching`, `DocumentExtractionResult` y warnings) es más barato que reconstruir desde cero; el escenario "granel sin detalle" requiere modelado nuevo, no solo configuración.
- **Módulos afectados:** `madenat_ingestion_engine` (estado documentado), `madenat_lumber_intake` (consumidor).

---

## 2026-09-12 — Método de costeo real verificado (AVCO desactivado, `wood_cost_usd` total, sin prorrateo parcial)

### AD-64 — Estado real del costeo y brecha de consumo parcial de lote (diagnóstico)

- **Fecha:** 2026-09-12
- **Naturaleza:** diagnóstico de solo lectura (sin cambios de código). Registra el estado real del costeo frente a `CANON/08_COSTEO.md` y una brecha estructural.
- **Hechos verificados:**
  - **Costeo nativo de Odoo desactivado de facto para madera:** `property_cost_method` es `NULL` en las 4 categorías de producto; 11 de 12 productos de madera son `type='consu'`; el producto maestro de ingesta (`madenat_lumber_product_default`, tanto `bruta` como `procesado`) resuelve a `product_template 215` (`consu`). Consumible ⇒ sin valorización automática (sin `stock.valuation.layer`/COGS).
  - **`wood_cost_usd` es `fields.Float` (AD-38 vigente) y un costo TOTAL del lote, no unitario:** `action_calculate_wood_cost` computa `wood_cost_usd = volumen_m3 × (reception.total_amount_usd / physical_volume_m3)`.
  - **`total_cost_usd`** = `wood_cost_usd + purchase_cost_usd + Σ(cost_line_ids.amount_usd)` (+ logistic/process/other desde `madenat_lumber_costing`), `store=False`.
  - **Sin prorrateo por salida parcial:** `_get_or_create_consumption_picking` consume `qty = lot.volumen_m3` completo (todo-o-nada); `wood_cost_usd`/`volumen_m3` son documentales estáticos, no ligados a `stock.move`/`stock.quant`.
- **Brecha registrada:** el sistema **no soporta consumo parcial de un lote agregado con prorrateo de costo correcto** (severidad equivalente a BT-01/BT-02). Sin resolverla, una salida parcial dejaría el costo total intacto y `cost_per_m3_usd` inconsistente con el stock físico.
- **Módulos afectados:** `madenat_lumber_core` (`stock_lot.py`, `madenat_guia_processing.py`), `madenat_lumber_costing`.

---

## 2026-09-12 — Diseño aprobado: Recepción a Granel + Balance de Masa + Consolidación Administrativa

### AD-65 — Diseño de recepción a granel, envío a proceso por Balance de Masa y consolidación administrativa (APROBADO, implementación pendiente)

- **Fecha:** 2026-09-12
- **Tipo:** diseño aprobado en sesión (Mauricio, Arquitecto/Tech Lead). **Pendiente de implementación** (esta pasada no escribe código).
- **Problema de origen (1.1):** (a) proveedores con packing list en PDF de tabla de columnas fijas; (b) madera que llega por volumen total a un patio sin desglose de piezas, destinada a procesamiento externo.
- **Principio rector (1.2) — motor de mejor esfuerzo, no dos features:** un único motor (extensión de `madenat_ingestion_engine`) con degradación en cascada: tabla completa (columnas fijas configurables, no hardcodeadas) → subtotales por grupo → total de encabezado (guía, fecha, volumen, especie, patio — mínimo garantizado). Nunca bloquea; cualquier dato no hallado genera `ingestion_document_warning` no bloqueante.
- **Selección de detalle manual (1.3):** el operador elige explícitamente en el wizard si el documento es detalle línea por línea o agregado; no se infiere (mismo criterio ya aplicado a Producto/Procesado).
- **Reclasificación auditada (1.4):** wizard nuevo `intake.tipo_ingreso.reclassify.wizard`, disponible solo mientras el lote no esté notarizado por Gate 3; cada uso se registra en `madenat.audit_log`.
- **Patio = stock.location nativo (1.5):** `location_id` ya existe en `lumber.reception`; se crea bajo demanda y nunca se elimina con stock (comportamiento nativo Odoo, cero desarrollo). Sin modelo propio de patios.
- **Envío a proceso por Balance de Masa (1.6):** se descarta genealogía lote a lote (`parent_lot_id`/`child_lot_ids`) para procesadores externos (mezcla física real); el envío resta una **cantidad** del pool de volumen del patio (no un lote completo) y el retorno se registra como stock nuevo independiente (alineado con DEC-002). Gap técnico a resolver: `_get_or_create_consumption_picking` hoy consume `qty = lot.volumen_m3` completo → debe soportar consumo de una cantidad parcial del pool (ver AD-64).
- **Prohibición NO NEGOCIABLE (1.7):**
  > **El sistema no debe validar, exigir, ni asumir correspondencia de detalle (volumen, piezas, paquetes) entre lo enviado a proceso y lo retornado procesado. La relación es de balance agregado administrativo (Mass Balance), nunca de igualdad ni de correspondencia física o numérica exacta. Cualquier factor de rendimiento en reportes de conciliación es informativo, jamás bloqueante ni validante de una asignación individual.**
- **Consolidación administrativa (1.8):** manual, opcional, disponible en cualquier momento (al registrar o después). Granularidad adaptativa (etiqueta individual / paquete-fardo / volumen total) con el volumen como denominador común. Una sola pantalla: lista de guías candidatas (cronológica, filtrable por proveedor/producto), saldo disponible en la unidad correspondiente, asignación con un clic, reparto entre varias guías (patrón visual de `lumber_cost_distribution.py`). Aviso no bloqueante si excede saldo. Funciona incluso sin guías de origen candidatas.
- **Costeo fuera de esta etapa (1.9):** el valor extraído se entrega tal cual a Costeo/Auditoría; ninguna valorización/prorrateo se resuelve en ingesta/consolidación.
- **Reporte de conciliación (1.10):** extensión de `madenat_lumber_reports` (no módulo nuevo), informativo, por procesador/período, contra un factor de rendimiento configurable; uso exclusivo de Auditoría; nunca valida asignaciones individuales (ver 1.7).
- **Menú Toll para Operaciones (1.11):** campo opcional "Enviar a proceso" con selección de procesador (patio↔procesador es N:M, no se automatiza; se sugiere el procesador más frecuente, editable); un solo botón genera lote + orden Toll (`create_toll_order_wizard` existente, sin modificar su lógica); se ajusta `ir.model.access.csv` de `madenat_toll_processing` para Operaciones.
- **No se modifica (1.12):** Gates 0-3, `reception_parser.py` (sin ramas nuevas), lógica interna de `madenat_toll_processing`, esquema de `stock.lot` más allá de lo estrictamente necesario para consumo parcial de pool (1.6); ningún módulo nuevo.
- **Módulos afectados (implementación futura):** `madenat_lumber_core`, `madenat_ingestion_engine`, `madenat_lumber_reports`, `madenat_lumber_intake`, `madenat_toll_processing` (solo ACL).

---

## 2026-09-20 — Diseño validado: consumo parcial de lote/pool para salida a proceso (resuelve gap AD-64)

### AD-66 — Modelo de línea `source_lot_line_ids` para consumo parcial en `_get_or_create_consumption_picking` (diseño auditado y aprobado, implementación pendiente)

- **Fecha:** 2026-09-20
- **Tipo:** diseño técnico validado mediante auditoría de código independiente (Cline/DeepSeek), sobre propuesta previa de sesión de arquitectura (2026-09-15). Resuelve el prerequisito bloqueante documentado en AD-64. Pendiente de implementación (esta pasada no escribe código).
- **Problema de origen (AD-64):** `_get_or_create_consumption_picking()` (`madenat_lumber_core/models/madenat_guia_processing.py:3852`) consume `qty = lot.volumen_m3` completo por cada lote en `source_lot_ids`, sin soporte de cantidad parcial. Esto bloquea la implementación de AD-65 (Balance de Masa), que requiere restar una cantidad del pool de volumen del patio, no un lote completo.
- **Decisión de diseño:** agregar un modelo de línea nuevo y aditivo, `madenat.guia.processing.source.lot.line` (`guia_processing_id` M2O cascade, `lot_id` M2O `stock.lot` required, `qty_to_consume` Float `digits=(16,3)` required), expuesto como `source_lot_line_ids` (One2many) en `madenat.guia.processing`. El campo `source_lot_ids` (Many2many) existente no se elimina ni se reemplaza; coexiste como fallback.
- **Rama condicional en `_get_or_create_consumption_picking()`:** si `source_lot_line_ids` tiene datos, usar `qty_to_consume` por línea (flujo nuevo, consumo parcial); si está vacío, usar el comportamiento actual `qty = lot.volumen_m3` (flujo legacy, cero regresión).
- **`_reverse_consumption_picking()` y `action_force_cancel()` no requieren cambios:** verificado por auditoría de código que ambos leen `qty = move.quantity or move.product_uom_qty` (líneas ~4026 y ~4313 respectivamente) — la cantidad real movida en el `stock.move`, sin recalcular desde `lot.volumen_m3`. Ambos son agnósticos a si el consumo fue total o parcial.

### Validación por auditoría de código (Cline/DeepSeek, 2026-09-20)

- **Mapeo de dependencias confirmado:** no hay vistas XML de `madenat.guia.processing` que referencien su campo `source_lot_ids` (las referencias XML a un campo homónimo pertenecen a `toll.processing.order` en `toll_processing_order_views.xml:59,86`); el único consumidor productivo cross-módulo del campo de la guía es `madenat_toll_processing` (`guia_processing_integration.py:37-40` lo escribe; `stock_lot.py:62` lo lee en un dominio de vista). El fallback preserva esta dependencia sin requerir cambios en `madenat_toll_processing`.
- **Compatibilidad con tests confirmada por lectura línea a línea:** los 5 tests de `TestGuiaProcessingConsumptionBT04` en `test_guia_processing.py` (líneas 1006-1084) no pueblan `source_lot_line_ids`, por lo que caen en el fallback y preservan su comportamiento exacto. Los 3 tests de `test_intake_direct_stock.py` ejercitan el override de `madenat_lumber_intake`, no el método core.
- **Sin duplicación de modelos existentes:** se verificaron `lumber.shipment.line`, `stock.lot.cost.line`, `lumber.cost.distribution.line`, `madenat.guia.processing.line` y `stock.move.line` — ninguno ofrece una relación editable "lote + cantidad a consumir" equivalente. El modelo nuevo está justificado, no es una duplicación.
- **Sin consumo parcial preexistente en el repo:** `madenat_toll_processing/models/toll_processing_order.py:369` también consume `volumen_m3` completo; ningún módulo del repo resuelve hoy este problema.
- **Re-verificación de citas (2026-09-20):** las 10 referencias de archivo:línea usadas en este diseño fueron confirmadas exactas contra el estado real del repo, sin corrimientos de línea. Working tree limpio al momento de la verificación.

### Ajustes obligatorios incorporados al diseño (no opcionales)

1. **Validación de rango:** la nueva rama debe exigir `0 < qty_to_consume <= lot.volumen_m3`.
2. **Doble fuente de verdad documentada como transitoria:** `source_lot_ids` (legacy/fallback) y `source_lot_line_ids` (vía nueva) coexistirán deliberadamente.
3. **Separación de responsabilidad respecto al costeo:** este diseño resuelve el consumo parcial a nivel de `stock.move`/`stock.lot` (volumen físico). El prorrateo de `wood_cost_usd`/`total_cost_usd` sigue siendo una brecha distinta, ya diferida a Costeo por AD-65 §1.9.

### Hallazgo colateral registrado durante la validación (no forma parte de AD-66, pendiente de diseño futuro)

La ruta Procesado del wizard de intake (`madenat_lumber_intake/models/intake_wizard.py:413`) fija `intake_direct_stock=True`, lo que hace que `_get_or_create_consumption_picking()` sea saltado por completo (ver override en `intake_guia_processing.py:17-27`). El flujo de "granel → patio → envío a proceso por Balance de Masa" de AD-65 §1.6 necesitará una tercera vía de derivación en el wizard que no fije ese flag. Registrado como pendiente en `05_BACKLOG.md` v7.1.0.

### Alcance y límites de esta decisión

- No se modifica `_reverse_consumption_picking()`, `action_force_cancel()`, Gates 0-3, `reception_parser.py`, ni la lógica interna de `madenat_toll_processing` (solo verificación de compatibilidad).
- No se resuelve en esta decisión el prorrateo de costo por consumo parcial, ni la tercera derivación de intake, ni el diagnóstico de `reception_id` no poblado.
- **Módulos afectados (implementación futura):** `madenat_lumber_core` (modelo nuevo, método modificado, ACL, tests). Sin cambios en `madenat_lumber_intake`, `madenat_toll_processing`, `madenat_lumber_costing` en esta etapa.

### Corrección documental asociada (registrada en la misma sesión)

AD-63 (2026-09-12) afirmaba que `madenat_ingestion_engine` era "directorio untracked, nunca commiteado". Esa afirmación quedó obsoleta desde el commit `843ed0d` (2026-09-15), que trackeó los 22 archivos del módulo. AD-63 se mantiene como registro histórico válido para la fecha en que fue escrita; esta nota deja constancia de que el hecho que describía ya cambió. La brecha de trazabilidad canónica (entrada propia del módulo en CANON) sigue abierta, distinta de la trazabilidad git ya resuelta.
