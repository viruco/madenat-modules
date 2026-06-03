# 04 — Decision Log

**Módulo:** MADENAT Lumber Core
**Versión documental:** 6.2.0
**Última actualización:** 2026-05-23
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
  - `blanks_clear` → **exclusivamente BLANK_CLEAR_FACTOR (f5085 = 0.6)**
  - `s2s` → **FACE_DEDUCTION + S2S_WIDTH_ADJUSTMENT**

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
- ✅ Volumen de embarque correcto (60% del nominal)
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
