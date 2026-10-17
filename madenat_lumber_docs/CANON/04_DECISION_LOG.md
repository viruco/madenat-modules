# 04 — Decision Log

**Módulo:** MADENAT Lumber Core
**Versión documental:** 12.29.0
**Última actualización:** 2026-10-15  <!-- actualizado: 2026-10-15 (5) — alta **AD-110** (FASE 11 — integridad del ciclo de vida de las imputaciones SV): **A-1/B-1** `state` y las marcas de transición sólo cambian por las acciones OFICIALES (vía privada `_i2_write_protected_state`; `write`/`create` públicos los rechazan, también con `sudo()` y contexto: **sin bandera de contexto** por decisión de diseño); el motivo se captura en `reason` y la acción lo congela en su marca; **M-2** la reversa toma los locks de capacidad y revalida el estado; **M-4** cadena `origin_imputation_id`↔`reversed_imputation_id`; **B-2** líneas y repartos inmutables fuera de preparación; **B-3** anulación con motivo obligatorio en metadata y bitácora. **M-3** y los datos heredados (`IMP02220`, `IMP04823`, eventos TX10) quedan documentados y sin tocar. `madenat_lumber_logistics` 18.0.1.32.0 → **18.0.1.36.0**; 17 pruebas nuevas en verde; regresión por nombre con el mismo subconjunto del baseline; sin migraciones, sin push ni despliegue. Versión 04 12.25.0 → 12.26.0. | 2026-10-15 (4) — alta **AD-109** (FASE 10 — corrección del registro de etiquetas en la rebaja SV: defectos F1/F2/F3 del diagnostico `DIAGNOSTICO_REBAJA_SV841_REGISTRO_ETIQUETAS_20261015`; **S2** filtro efectivo de «Trabajo en preparacion» y «Continuar» operativo en estados terminales (`logistics`: campo O2M→M2M calculado no almacenado + `search` explicita; `logistics` 18.0.1.29.0 → 18.0.1.30.0, commit `19611d0`); **S3** bloqueo del guardado/aplicacion sin ninguna etiqueta incluida, sin borrado silencioso (`logistics` 18.0.1.30.0 → 18.0.1.31.0, commit `e2d6b64`); **S1** firma/clave documental con las etiquetas seleccionadas + reglas de estado terminal (applied ⇒ mensaje claro sin duplicar; reversed/cancelled ⇒ documento nuevo con clave distinta y trazable) y **retrocompatibilidad total** de la receta base de la clave (`logistics` 18.0.1.31.0 → 18.0.1.32.0); pruebas T1–T7 del informe en suites nuevas (WF/SG/DK) primero en rojo; regresion por nombre con el mismo conjunto del baseline; sin migraciones, sin cambios en `IMP04823`/`IMP02220`, sin push ni despliegue). Version 04 12.24.0 → 12.25.0. Sin push ni despliegue. | 2026-10-15 (3) — alta **AD-108** (FASE 8: M1 menú `menu_madenat_sv_imputation` sin `name` corregido —restitucion del `<menuitem>` antes del `<record>`; `logistics` 18.0.1.29.0—; M2 prueba de longitudes a `product.product`; método de verificacion en dos pasos + camino `-u` desde un dump anterior al WIP de costing; DR demostrada; 0 fallas nuevas atribuibles; configuracion no sembrada en el alta limpia; D1 `costing` caracterizado). Version 04 12.23.0 → 12.24.0. Sin push ni despliegue. | 2026-10-15 (2) — alta **AD-107** (cierre de D18: `bfda876` core y `56405cb` logistics 18.0.1.28.0; P2-2 fuera por decision; reparacion K2 de la instalacion desde cero de intake —movimiento puro verificado con exit 0—; HALLAZGO BLOQUEANTE abierto: `<record model="ir.ui.menu">` sin `name` en `madenat_sv_imputation_views.xml` → no instala `logistics` desde cero; hallazgo de despliegue: no mezclar «BD con WIP» y «codigo sin WIP» por la vista de `costing`). Version 04 12.22.0 → 12.23.0. Sin push ni despliegue. | 2026-10-15 (1) — alta **AD-106** (supuesto de **UNA sola compañía**: no se implementa `company_id` ni `ir.rule` de compañía en `madenat.guia.processing`, con condición de reapertura; se **conservan** los 3 usuarios inactivos `@madenat.test`). Versión 04 12.21.0 → 12.22.0. Commit local ① (FASE 5); sin push ni despliegue. | 2026-10-12 (3) — alta **AD-105** (H1 motivo obligatorio por cualquier vía; H2 rol jefatura/sistema en lugar del grupo técnico `stock.group_stock_manager`; H3/**H-SEC-5** bitácora APPEND-ONLY por ORM con bypass test-only inerte y **límite SQL/DBA declarado**; H4 escenario (f) de costos; H6 fixtures `*_oper`). Core 18.0.6.8.0 → 18.0.6.9.0; intake 18.0.0.14.0 → 18.0.0.15.0; logistics 18.0.1.26.0 → 18.0.1.27.0. Versión 04 12.20.0 → 12.21.0. Expediente `AUDITORIA_INTEGRAL_20261012/fase4/`. Sin commit/push. | 2026-10-12 (2) — alta **AD-104** (guardas G1 de eliminación de guía D-G1..D-G4 + fixture G2). Core 18.0.6.7.0 → 18.0.6.8.0; intake 18.0.0.13.0 → 18.0.0.14.0. H-SEC-5 SIGUE PENDIENTE. Versión 04 12.19.0 → 12.20.0. Sin commit/push. | 2026-10-12 (1) — alta **AD-103** (jefatura puede eliminar `madenat.guia.processing` por higiene de la base; permiso como POLÍTICA; no autoriza borrado de datos reales; guardas de integridad/trazabilidad **pendientes**). Versión 04 12.18.0 → 12.19.0. Sin commit/push. | 2026-10-07 (2) — alta AD-102 (retorno de servicio: identificación no bloqueante + reglas de imputación I2; implementado/probado en copia aislada `IMPL_SERVICE_RETURN_AB_20261007/`, NO aplicado). Ver 12 §11.9, 19 §19.9, 03 §12, 05, 02 §17.10. | 2026-10-07 — alta AD-101 (búsqueda, filtros y agrupaciones de la Consola de Intake: OC documental vs OC vinculada; `guide_date_kind`; modalidades; producto real por líneas; procesador por Orden de Procesamiento; aplicado en `madenat_test`). Ver 00 §4.10 y 03 §11. | 2026-10-02 (4) — alta AD-90 (semántica de inventario en procesador y pendiente de consolidación documental). Complementa AD-87/AD-88/AD-89. Ver CANON/19 §2/§3/§5.4/§7.3/§16; (5) — corrección AD-89 D-I1-03/D-I1-04 IMPLEMENTADA (feat/procesadores-guardas-20261002): parcial manual sin motivo, físico/reservado/libre y backorder nativo; (6) — alta AD-91 (modelo documental de imputación SV por guía procesada, I2): modelo aditivo `madenat.sv.imputation`/`.line`/`.sv.line`; I2 documental sin efecto en stock; salida nativa + ledger `action_type='imputacion'` a I3; saldo físico / `sv_available_m3` / saldo documental separados; cabecera por guía, inmutabilidad y reversa; idempotencia por clave documental propia (no `picking_id`); severidad dura etiqueta-side / blanda SV-side; costo a I5; merma/cierre posterior. Resuelve C-1/C-2/C-3. Ver CANON/19 §2/§4/§5/§6/§7/§13.2/§16. Solo documentación; (7) — precisa la reserva documental temporal de capacidad nominal de etiqueta (I2_ACTIVE_STATES) y el saldo documental aplicado de SV (I2_DOCUMENTAL_STATES). Ver CANON/19 §6/§7.3; (8) — precisa el alcance del principio de no-borrado: aplica también a la corrección/reset de recepción (`lumber.reception.action_reset_to_draft`, 00 §4.2), que revierte por movimientos nativos y nunca borra/escribe `stock.quant`, lotes, pickings ni movimientos; límite explícito: el reset de guía `action_reopen_to_draft` permanece PENDIENTE; (9) — G1: reapertura de guía no bloqueante y trazable (wizard + reversión nativa del consumo BT-04; conservación de historia física sin vínculo fuerte; sin escribir/borrar `stock.quant` ni mutar `origin`; auditoría `deviation` + chatter). G2 (llave fuerte `stock.picking.guia_processing_id`) y G3 (reversión nativa automática del ingreso de producción por esa llave) IMPLEMENTADOS. Ver 00 §4.3. -->
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
  4. **Ausencia de wizards (actualizado AD-75, 2026-09-22):** no existía wizard de vinculación manual de OC ni de corrección de proveedor para `madenat.guia.processing`. AD-75 extiende `madenat.lumber.intake.supplier.link` con contexto de guía (`guia_id`) para cubrir la corrección manual de proveedor en Volúmenes; `madenat.lumber.intake.po.link` sigue siendo exclusivo de Producto/`lumber.reception`.
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
- **Ampliación 2026-10-01 (AD-87, D4):** la brecha alcanza también al **SV (Lote Volumen)**: los lotes `lot_flow_type='volume'` **no tienen costo** (`wood_cost_usd`/`purchase_price_usd_per_m3` vacíos; costeo nativo desactivado), por lo que una **etiqueta de retorno** no puede heredar costo de madera. **Fuente propuesta:** derivar el costo del SV de su guía de **Recepción por Volumen**/OC (`total_amount_usd / official_volume_m3` o precio unitario de la OC) y propagarlo en la **imputación** (`19` §5.5, fase I5).

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
- **Alineación 2026-10-01 (AD-87, D2/D10):** el mecanismo **declarado** del vínculo volumen comprado (SV) ↔ etiqueta de retorno es la **imputación** (`CANON/19`), que **no** usa genealogía. En consecuencia, `parent_lot_id` **deja de ser necesario** para el retorno procesado y pasa a **opcional** en un **paso futuro controlado** (I6); el §1.6 se mantiene (el retorno es stock nuevo e independiente) y gana la vía SV explícita.

---

## 2026-09-20 — Diseño validado: consumo parcial de lote/pool para salida a proceso (resuelve gap AD-64)

### AD-66 — Modelo de línea `source_lot_line_ids` para consumo parcial en `_get_or_create_consumption_picking` (implementado y validado)

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

### Implementación y validación (2026-09-20)

- **Commit:** `4ae406f` en `main` (`viruco/madenat-modules`), 7 archivos, 265 inserciones / 10 eliminaciones. Incluye modelo nuevo `madenat_guia_processing_source_lot_line.py`, modificación de `madenat_guia_processing.py`, ACL, `CHANGELOG.md` y tests. Push confirmado a `origin/main` (`869502a..4ae406f`).
- **Validación de rango implementada exactamente como se exigió en el punto 1 de Ajustes obligatorios:** `_check_qty_to_consume_range()` en el modelo nuevo bloquea `qty_to_consume <= 0` y `qty_to_consume > lot_id.volumen_m3`.
- **Cobertura de tests ejecutada en runtime real (Odoo 18.0-20260817, puerto 8069, `docker compose run --service-ports`), 13/13 verdes, 0 failed, 0 errors:**
  - `TestGuiaProcessingConsumptionBT04` (5 tests) — comportamiento legacy sin regresión, confirmando la rama de fallback.
  - `TestGuiaProcessingConsumptionPartialAD66` (5 tests) — bloqueo por cantidad cero/negativa, bloqueo por exceso, consumo parcial con cantidad exacta en el `stock.move`, fallback sin líneas, reversión exacta.
  - `TestIntakeDirectStock` (3 tests) — override de `madenat_lumber_intake` verificado sin regresión cruzada, confirmando el aislamiento señalado en el hallazgo colateral de esta misma decisión.
- **Sin cambios fuera del alcance declarado:** el diff tocó únicamente `madenat_lumber_core`, tal como se limitó en "Alcance y límites de esta decisión".

### Hallazgo colateral registrado durante la validación (no forma parte de AD-66, pendiente de diseño futuro)

La ruta Procesado del wizard de intake (`madenat_lumber_intake/models/intake_wizard.py:413`) fija `intake_direct_stock=True`, lo que hace que `_get_or_create_consumption_picking()` sea saltado por completo (ver override en `intake_guia_processing.py:17-27`). El flujo de "granel → patio → envío a proceso por Balance de Masa" de AD-65 §1.6 necesitará una tercera vía de derivación en el wizard que no fije ese flag. Registrado como pendiente en `05_BACKLOG.md` v7.1.0.

### Alcance y límites de esta decisión

- No se modifica `_reverse_consumption_picking()`, `action_force_cancel()`, Gates 0-3, `reception_parser.py`, ni la lógica interna de `madenat_toll_processing` (solo verificación de compatibilidad).
- No se resuelve en esta decisión el prorrateo de costo por consumo parcial, ni la tercera derivación de intake, ni el diagnóstico de `reception_id` no poblado.
- **Módulos afectados (implementación futura):** `madenat_lumber_core` (modelo nuevo, método modificado, ACL, tests). Sin cambios en `madenat_lumber_intake`, `madenat_toll_processing`, `madenat_lumber_costing` en esta etapa.

### Corrección documental asociada (registrada en la misma sesión)

AD-63 (2026-09-12) afirmaba que `madenat_ingestion_engine` era "directorio untracked, nunca commiteado". Esa afirmación quedó obsoleta desde el commit `843ed0d` (2026-09-15), que trackeó los 22 archivos del módulo. AD-63 se mantiene como registro histórico válido para la fecha en que fue escrita; esta nota deja constancia de que el hecho que describía ya cambió. La brecha de trazabilidad canónica (entrada propia del módulo en CANON) sigue abierta, distinta de la trazabilidad git ya resuelta.

---

## 2026-09-21 — Diseño e implementación: volumen remanente físico tras consumo parcial (alcance Logística/Inventario)

### AD-67 — Campo `volumen_restante_m3` como fuente de verdad física, reporte de inventario corregido (implementado y validado)

- **Fecha:** 2026-09-21
- **Tipo:** corrección preventiva de inconsistencia de inventario, derivada de investigación de impacto downstream de AD-66. Alcance limitado a Logística/Inventario; el costeo de consumo parcial queda explícitamente fuera de esta decisión (ver "Fuera de alcance").
- **Problema de origen:** `stock.lot.volumen_m3` es documental (no se ajusta tras consumo parcial vía AD-66); `lumber_stock_report.py` mostraba m³ documental mientras filtraba existencia por `quantity` física, generando inconsistencia visible en el reporte de inventario.
- **Decisión:** se agrega `stock.lot.volumen_restante_m3` (Float, compute store=True, depende de `quant_ids.quantity` en ubicaciones internas) como fuente de verdad de volumen físico disponible. `volumen_m3` se conserva sin cambios como volumen documental de origen. El reporte de inventario expone ambas columnas, claramente etiquetadas.
- **Fundamento de la fuente de verdad física:** el producto maestro usa `uom_id`/`uom_po_id` = `uom.product_uom_cubic_meter` (m³ nativo, `madenat_lumber_product_default_data.xml:15-16`), confirmando que `stock.quant.quantity` es una medida física real en m³, no una unidad distinta que requiera conversión.
- **No se modifica `estado_trazabilidad`:** se evaluó y descartó agregar un valor nuevo a este Selection, porque se usa en un `domain` operativo real (`lumber_container_views.xml:362`, filtro de asignación a contenedor). Un valor nuevo excluiría silenciosamente lotes parcialmente consumidos de la asignación a embarque.
- **Fuera de alcance (diferido a AD-70 (renumerado desde el placeholder original AD-68, que fue reasignado a la ruta granel el 2026-09-21), pendiente de revisión con Costeo/Auditoría):** el prorrateo de `wood_cost_usd`/`total_cost_usd`/`cost_per_m3_usd` ante consumo parcial. Los precios de compra provienen directamente de las guías de proceso/producto (USD o CLP) durante la ingesta, con advertencias no bloqueantes si faltan (patrón ya existente); la corrección de costeo específica para consumo parcial se diseñará por separado.
- **Tests:** 13/13 verdes (0 failed, 0 errors) ejecutados en runtime real (Odoo 18, puerto 8069, `docker compose run --service-ports`): `TestGuiaProcessingConsumptionBT04` (5), `TestGuiaProcessingConsumptionPartialAD66` (5), `TestVolumenRestante` (3).
- **Módulos afectados:** `madenat_lumber_core` (campo nuevo, vista), `madenat_lumber_reports` (modelo y vista de reporte).

### AD-68 (2026-09-21) — Ruta "Granel" en wizard de intake
Nuevo tipo_recepcion='granel' en madenat.guia.processing para recepción por
volumen total sin desglose de piezas (AD-65 §1.6). Producto maestro 'bruta'.
Línea sintética en processing_line_ids con volumen extraído del header del
PDF vía madenat_ingestion_engine.extract_document() (sin cambios al motor).
Detección por keywords migrada a madenat.ingestion.config (cascada
config→hardcode). 3 candados de excel_file relajados condicionalmente
(campo, vista, action_preview_document). additional_cost/
_assign_costs_to_generated_lots excluido para granel (exclusivo de
'service'/maquila). 14 tests nuevos, suite completa en verde.

### AD-69 (2026-09-21) — Fix: BT-04 no dispara automático para granel
Corrección post-AD-68: el disparo automático de _get_or_create_consumption_
picking() en action_validate() vuelve a ser exclusivo de tipo_recepcion==
'service'. Una guía granel debe poder validar y quedar como stock de patio
sin origen/destino de proceso asignado; el consumo ocurre después, como
acción independiente, cuando una guía service declare ese lote como origen
(source_lot_line_ids, AD-66). Guard de contrato de
_get_or_create_consumption_picking() sigue aceptando 'granel' sin cambios.
3 tests nuevos (granel puro sin bloqueo, service sigue bloqueando sin
origen, integración granel→service con descuento de volumen verificado).

### AD-71 (2026-09-21) — Motor de mejor esfuerzo en cascada para detalle PDF
Implementa el ítem de "Tareas de implementación de AD-65" (05_BACKLOG.md
línea 56): _extract_pdf() en madenat_ingestion_engine/services/
document_extractor.py deja de depender exclusivamente de regex de cabecera
para total_volume_m3. Cascada de 4 niveles, función pura (sin self.env,
sin ORM): Nivel 1, tabla con bordes reales vía pdfplumber.extract_tables()
+ mapeo de columnas por perfil (build_column_mapping, min_score=40,
mismo mecanismo que Excel). Nivel 2, tabla sin bordes reconstruida por
clustering de palabras (extract_words(), tolerancias nombradas
_WORD_CLUSTER_X_TOLERANCE=8.0pt / _WORD_CLUSTER_Y_TOLERANCE=5.0pt,
agrupación por fila (top) antes que por columna (x0)). Nivel 3, suma de
volume_m3 de las líneas extraídas en Nivel 1/2 (derivado, no función
aparte). Nivel 4, regex de cabecera preexistente (r"(\d{2,4})\s*M3"),
usado solo si 1/2/3 no producen líneas con volumen.

Prioridad: la suma de líneas de detalle (Nivel 1/2/3) siempre prevalece
sobre el regex de cabecera (Nivel 4) cuando ambos están disponibles;
discrepancias se registran como warning de auditoría sin lanzar excepción
(P5/P6). Nunca lanza DocumentExtractionError por ausencia de tabla —
degrada de nivel con warning explícito (P3).

Extensibilidad multi-proveedor: clave opcional `pdf_table_strategy` en
ingestion_profiles.py ('lines'/'word_cluster'/'none'/autodetección),
documentada pero sin uso obligatorio en los 2 perfiles existentes
(ambos usan autodetección Nivel 1 → Nivel 2).

_route_granel() en madenat_lumber_intake no se modifica: sigue leyendo
result.header.get('total_volume_m3'), ahora resuelto por la cascada de
forma transparente. Test de regresión de integración granel→service
(AD-68/AD-69) verificado sin cambios.

Tests: 49/49 verdes (0 failed, 0 errors) — 21 preexistentes de
TestDocumentExtractor + 6 nuevos de TestPdfDetailCascade (Nivel 1 métrico,
Nivel 2 clustering con resultado idéntico a Nivel 1, Nivel 4 solo regex,
discrepancia suma-vs-regex con priorización de suma, perfil imperial,
regresión solo-regex).

Deuda técnica anotada (no bloqueante): el test de Nivel 2 usa una grilla
de palabras sintética perfectamente regular (espaciado muy superior a las
tolerancias de clustering), validando el mecanismo pero no la robustez
frente a PDFs reales de proveedores con columnas desalineadas. Pendiente
validar Nivel 2 contra al menos un PDF real sin bordes antes de considerar
el motor probado en producción para todos los proveedores.

Módulos afectados: madenat_ingestion_engine (services/document_extractor.py,
services/ingestion_profiles.py, tests/test_document_extractor.py). Sin
cambios en madenat_lumber_intake ni madenat_lumber_core.

### AD-72 (2026-09-21) — Selección manual de detalle en recepción Granel
Cierra el ítem "Implementar selección manual de tipo de detalle (línea por
línea vs. agregado) en el wizard de intake" (05_BACKLOG.md línea 57).

Desde AD-71 el motor PDF puede devolver result.lines con detalle real por
fila (incluyendo lot_number por línea, _LINE_KEYS). AD-72 expone esa vía al
operador: campo nuevo tipo_detalle_granel en el wizard ('agregado' default /
'linea_por_linea'), visible solo cuando tipo_ingreso == 'granel'.

Método _create_granel_detail_lines() en madenat.guia.processing, hermano de
_create_granel_summary_line(): crea en batch (una sola llamada create()) una
línea real por cada línea del PDF con volume_m3 > 0, preservando lot_number
(fallback 'GRANEL'), subproducto resuelto desde product_name_original
(fallback 'GRANEL'), pieces (fallback 1) y los tres volúmenes igualados a
volume_m3. Dimensiones físicas 0 y nominales placeholder (espesor_nominal_mm
=1.0), producto maestro 'bruta'. Líneas sin volumen válido se excluyen sin
excepción (P3); si ninguna es creable, UserError sugiriendo el modo agregado.

_route_granel() bifurca: 'linea_por_linea' con result.lines → detail lines;
si no hay líneas (cascada AD-71 Nivel 4), degrada a resumen agregado con
mensaje visible en el chatter de la guía. 'agregado' (default) conserva el
comportamiento previo sin cambios.

Riesgo residual heredado de AD-51 (no resuelto aquí): si dos líneas del PDF
granel comparten lot_number, la colisión en _create_or_get_lot() es la misma
que ya existe para Excel. No se agrega prorrateo de costo por línea (AD-70,
diferido a Costeo/Auditoría).

Tests: 38/38 verdes (8 nuevos de AD-72: 5 en madenat_lumber_core +
3 en madenat_lumber_intake; regresión AD-66/67/68/69 sin cambios).

Módulos afectados: madenat_lumber_core (método _create_granel_detail_lines),
madenat_lumber_intake (campo tipo_detalle_granel, rama en _route_granel,
vista). Sin cambios en madenat_ingestion_engine.

### AD-73 (2026-09-21) — Wizard de reclasificación de tipo de ingreso (pre-Gate-3)
Cierra el ítem "Implementar wizard intake.tipo_ingreso.reclassify.wizard con
registro en madenat.audit_log, disponible solo antes de Gate 3" (05_BACKLOG.md
línea 58).

La autodetección de tipo_ingreso en el wizard de intake puede clasificar mal un
documento. AD-73 agrega un wizard TransientModel
madenat.lumber.intake.reclassify.wizard que corrige el tipo ANTES de Gate 3:
elimina el destino mal clasificado (lumber.reception o madenat.guia.processing),
registra evidencia en madenat.audit.log, y reabre un wizard de ingesta nuevo en
draft con el tipo correcto. No copia excel_file/pdf_file del wizard anterior
(binarios efímeros): el operador re-adjunta los documentos.

Guardia de elegibilidad (pre-Gate-3): madenat.guia.processing en state
('draft', 'verified'); lumber.reception en state ('draft', 'processing').
Defensa en profundidad: bloquea si existe stock.lot vinculado (lot_ids/
source_lot_ids) aunque el state sea nominalmente pre-Gate-3. El evento de
auditoría usa action_type='reclassification' (valor nuevo en madenat_audit_log),
se crea ANTES del unlink (para popular reception_id o guia_processing_id); en
guia, guia_processing_id es ondelete='set null' y el evento persiste tras el
unlink (la descripción conserva nombre/referencia del registro eliminado).

Puerta única: el botón "Reclasificar Tipo de Ingreso" vive en la consola
(madenat_lumber_intake.console) y las fachadas ligeras de intake
(intake_reception_facade_views, intake_guia_processing_facade_views), NUNCA en
los formularios nativos del core (madenat_lumber_core/views/*). El wizard
orquesta (unlink + audit_log + reabrir wizard de intake) sin reimplementar Gates
ni crear un segundo camino de escritura a stock.lot.

Tests: 94/94 verdes (6 nuevos de AD-73 en test_intake_reclassify.py; suite
completa de madenat_lumber_intake y TestGranelRouteCore de madenat_lumber_core
sin regresiones).

Módulos afectados: madenat_lumber_intake (modelo + vista + botones en consola y
fachadas + ACL), madenat_lumber_core (valor 'reclassification' en
madenat_audit_log.action_type). Sin cambios en madenat_lumber_core/views/.

### AD-74 (2026-09-22) — Ingreso por Volúmenes: flujo documental PDF, proveedor y detalle persistente
Cierra el hito "Ingreso por Volúmenes" de la recepción a granel (AD-65/AD-71/AD-72):
la vía `tipo_ingreso='granel'` del wizard de intake ("Madera a granel / volumen
total") se materializa en la consola como `ingestion_type='volume'` ("Ingreso por
Volúmenes"). Es la tercera modalidad de ingreso (Producto, Procesado, Volúmenes);
**no** se crea una cuarta modalidad.

Fuente documental: el PDF/Guía es la fuente principal validada; el Excel Packing
List es opcional y complementario. La ausencia de Excel no bloquea la lectura
documental, el preview ni la continuidad del ingreso. Excel como única fuente
queda **pendiente de prueba explícita**.

Extracción documental (`document_extractor._extract_pdf_parties()` +
`_extract_pdf_header()`): genérica, acumulativa y basada en estructura documental
(etiquetas Cliente/Señor(es)/Receptor + Emisor/Proveedor + membrete, exclusión de
transportista, asociación RUT-nombre por cercanía contextual, confianza
high/medium/low/none), no por reglas por proveedor/RUT/archivo/fixture. Extrae,
cuando está disponible: número de guía, fecha, proveedor documental y RUT,
receptor y RUT, OC, pedido/origen, tipo de cambio, paquetes/piezas/importes/totales,
volumen total declarado y detalle de líneas cuando la tabla PDF es reconstruible
con confianza. `_extract_pdf_header()` ya no usa "primer RUT" como proveedor.

Volumen y detalle: se distinguen volumen PDF/documental, suma de detalle, volumen
previsto/visible para stock, diferencia y fuente. La diferencia entre total de
cabecera y suma de detalle es warning documental no bloqueante. No se usa
espesor/ancho/largo/piezas para recalcular volumen en Volúmenes. Se soporta
normalización de separadores decimales locales.

**Consolidación de precedencia (2026-09-26, AD-79).** La precedencia canónica del
**volumen oficial** es: Guía PDF (`volume_pdf_m3`) → Packing Excel (`volume_excel_m3`) →
Packing declarado (`packing_volume_declared_m3`); se toma el **primer valor estrictamente
positivo** y, si ninguna fuente es positiva, **no existe volumen oficial** para el flujo.
No son fallbacks del volumen oficial: `volume_detail_m3` (y la suma de líneas PDF),
`volume_operational_m3`, `volumen_declarado_m3`, `vol_comercial_pdf`, `vol_comercial`,
`vol_fisico`, `vol_total_m3`, ni valores derivados de stock, conciliación o costeo. La regla
funcional completa vive en `12_FLUJOS_INGESTA.md` §11.5 y el bloqueo operativo de la rama de
Volumen (`action_validate`) exige volumen oficial disponible.

Detalle persistente: modelo `madenat.lumber.volume.detail.line` (documental y
editable, sin cubicación geométrica; fallback consolidado con warning cuando no
hay tabla reconocible; evidencia original conservada). La grilla de la consola
expone el detalle como Many2many computado con inverse hacia el origen.

La consola `madenat.lumber.intake.console` es una vista SQL readonly (`_auto=False`):
no escribe directamente; toda modificación se hace por ORM sobre el registro
origen (`madenat.guia.processing`).

Tests: `test_pdf_parties.py` (madenat_ingestion_engine) + `test_volume_extraction.py`
(madenat_lumber_intake); ver `03_TESTS.md`.

Módulos afectados: madenat_ingestion_engine (services/document_extractor.py),
madenat_lumber_core (resolución `_resolve_or_create_supplier`), madenat_lumber_intake
(wizard `_route_granel`, modelos `volume_detail_line`/`intake_console`, vistas de
consola).

### AD-75 (2026-09-22) — Asignación manual de proveedor en Volúmenes (reutilización de supplier.link)
Distingue proveedor documental (nombre/RUT que proviene del documento) de partner
asociado (`partner_id`, registro maestro existente en Odoo). Campos documentales:
`supplier_name`, `supplier_rut`, `supplier_source`, `supplier_confidence`.
Estados de resolución: resuelto automáticamente (RUT/nombre/auto-creado), requiere
asignación manual (`needs_manual`), múltiples coincidencias (`multi_match`) y
resuelto manualmente (`resolved_manual`, valor nuevo en `supplier_resolution_status`).

La asignación manual reutiliza el wizard existente `madenat.lumber.intake.supplier.link`
(sin crear wizard ni modelo nuevo): se le agrega `guia_id` (contexto de guía)
conservando `reception_id` (contexto de recepción); `default_get` prellena desde
`default_guia_id`/`default_reception_id`; `action_confirm_link` despacha a
`_link_guia()` (persiste `partner_id`, `supplier_resolution_status='resolved_manual'`,
nota y evidencia en chatter de la guía) o `_link_reception()` (comportamiento
Producto sin cambios).

Consola: cuando `partner_id` está vacío, el botón "Asignar proveedor"
(`action_assign_supplier`, solo `ingestion_type='volume'`) abre el wizard prellenado
con la guía origen. El operador selecciona un partner existente; no se crea partner
desde la consola; un proveedor pendiente no bloquea el ingreso documental. La
evidencia chatter queda en `madenat.guia.processing`, no en la consola.

Corrige AD-53 #4: `supplier.link` ya no es exclusivo de Producto/`lumber.reception`.

Tests: apertura de wizard, persistencia de estado (`resolved_manual`) y chatter
(`test_action_assign_supplier_abre_wizard`,
`test_asignar_proveedor_persiste_estado_y_chatter`).

Módulos afectados: madenat_lumber_core (valor `resolved_manual` en
`supplier_resolution_status`), madenat_lumber_intake (`intake_supplier_link_wizard.py`,
`intake_console.py` `action_assign_supplier`, vistas `intake_console_views.xml` e
`intake_supplier_link_wizard_views.xml`).

### AD-76 (2026-09-24) — Contrato operativo de Ingreso por Volúmenes (evidencia independiente, conciliación y volumen operativo)

Cierra las brechas del contrato funcional de Volúmenes sin crear una modalidad nueva
ni un flujo de stock paralelo:

1. **PDF/Excel independientes**: en `intake_modality == 'volume'` el wizard acepta
   PDF solo, Excel solo o ambos (`_guard_route_document` / `_preview_volume` /
   `_route_granel`); se leen por separado (`_read_volume_document`). Sin documentos →
   bloqueado.
2. **Evidencia original persistente**: campos `volume_pdf_m3`, `volume_excel_m3` y
   `volume_detail_m3` (suma calculada de `volume_detail_line_ids`) en
   `madenat.guia.processing` vía herencia en Intake. No se sobrescriben por edición.
3. **Conciliación documental**: `_conciliate_documents()` compara Nº guía, RUT,
   OC y volumen; estados `not_compared`/`auto_matched`/`matched_with_differences`/
   `needs_manual_review`/`incompatible`/`manual_confirmed`. Bloquea stock solo si
   `incompatible` o `needs_manual_review` sin confirmación manual
   (`action_confirm_conciliation` con motivo, chatter y `madenat.audit.log`).
4. **Volumen operativo editable**: `volume_operational_m3` (prellenado desde la fuente
   de mayor confianza) con `volume_operational_source`/`_note`/`_user_id`/`_date`;
   `set_volume_operational()` exige fuente y motivo ante cambio manual, deja chatter y
   bitácora, y nunca pisa PDF/Excel/detalle.
5. **Rama de validación sin geometría**: `action_validate` despacha
   `tipo_recepcion == 'granel'` a `_action_validate_volume_intake()` (Intake), que NO
   exige espesor nominal ni subproducto, no ejecuta cubicación ni salida automática a
   proceso, crea/reutiliza un lote sintético consolidado (`_get_or_create_volume_synthetic_lot`)
   y un picking incoming en m³ vía `_get_or_create_picking_unified()`. Stock usa solo
   `volume_operational_m3`; idempotente por estado `validated`.

Tests: `test_volume_operational.py` (14 escenarios) + ajuste de `test_granel_route.py`
(core) para evidencia/fecha en guías granel legacy. `madenat_lumber_intake` corre 154
tests verdes.

Módulos afectados: madenat_lumber_core (`madenat_audit_log.py` nuevos `action_type`),
madenat_lumber_intake (`intake_guia_processing.py`, `intake_wizard.py`,
`intake_console.py`, `volume_detail_line.py`, vistas de consola).

---

## 2026-09-25 — Programación 1: identificación operativa y trazabilidad visible de lotes en R1

### AD-77 (2026-09-25) — Identificación operativa y trazabilidad visible de lotes en R1 (Programación 1)

**Problema observado:** la vista R1 "Detalle por Patio — Stock Real" (`stock.quant`, agrupada por
patio/ubicación) exponía el nombre técnico del lote. En flujos por volumen ese nombre puede ser
`GRANEL 4495589`, ilegible para operación masiva y sin origen visible (guía, proveedor, fecha/hora
de ingreso, documento origen).

**Decisión:**

1. **Token técnico vs. nomenclatura operativa.** `GRANEL` se mantiene como token técnico interno
   del flujo por volumen. La interfaz de R1 presenta `Lote Volumen`. `GRANEL` no es nomenclatura de
   negocio.
2. **Sin tocar la identidad del lote.** No se modifica `stock.lot.name`, `display_name`, `name_get`
   ni `name_search`. La búsqueda histórica por `GRANEL 4495589` (y por `4495589`) sigue operando por
   el campo técnico `lot_id`, conservado en la search view y como columna opcional de R1.
3. **Capa de presentación en `madenat_lumber_reports`.** Cinco campos compute almacenados en
   `stock.quant` (`models/lumber_stock_report.py`), de solo lectura, sin escritura de datos:
   - `lot_operational_label` (Char): etiqueta operativa. Si el nombre normalizado es `GRANEL` o
     comienza con `GRANEL `, se sustituye el token inicial por `Lote Volumen`; en cualquier otro
     caso se devuelve el nombre técnico intacto, sin reemplazos parciales (`GRANELITO 123` y
     `MAD-001 GRANEL` no se alteran). Fuente: `stock.lot.name`; sin lote o sin nombre → vacío.
   - `is_volume_lot` (Boolean, indexado): criterio **técnico** del flujo por volumen. `True` solo si
     `stock.lot.name` normalizado es exactamente `GRANEL` o comienza con `GRANEL `; `False` si no
     hay lote, no hay nombre o el nombre comienza con otro token. Es la **única fuente de
     detección**, compartida con la etiqueta mediante el helper `_is_volume_lot_name()`.
   - `lot_entry_datetime` (Datetime): fecha/hora de ingreso. Prioridad: (1) fecha documental de
     recepción de compra; (2) si no hay recepción y el lote tiene guía de procesamiento, fecha de
     creación del lote **como fallback distinguible**; (3) sin ninguna fuente → vacío. El fallback
     nunca se presenta como fecha documental de recepción.
   - `lot_entry_datetime_source` (Selection `reception` / `lot_creation`): distingue el origen de la
     fecha anterior para que el fallback sea auditable en UI.
   - `lot_origin_document` (Char): documento real enlazado (recepción de compra o guía de
     procesamiento). Sin documento enlazado → vacío; no se generan textos de relleno.
4. **Filtro técnico, no textual.** El filtro `Lotes Volumen` de R1 usa
   `[('is_volume_lot', '=', True)]`, no la etiqueta visible: un cambio futuro de la nomenclatura
   operativa no altera el criterio funcional.
5. **Sin efectos sobre inventario.** Los cinco campos son de lectura y no tocan
   `stock.quant.quantity`, `stock.move`, `stock.move.line` ni `stock.lot`; el dominio de R1 sigue
   siendo cantidad positiva en ubicaciones internas con agrupación por patio/ubicación. Sigue
   vigente la prohibición de modificar stock operativo con SQL directo.

**Evidencia de despliegue:** actualización de `madenat_lumber_reports` a `18.0.2.3.0` sobre
`madenat_test` (`docker exec odoo18_app odoo -d madenat_test -u madenat_lumber_reports
--stop-after-init`), código de salida `0`, sin actualización de otros módulos y sin SQL manual. Las
cinco columnas existen en `stock_quant`. Caso histórico verificado por consulta de solo lectura:
`stock.lot(3753)` técnico `GRANEL 4495589` → operativo `Lote Volumen 4495589`,
`is_volume_lot = true`, saldo `0,000`. Detalle de comandos y evidencia en
`RAW/IMPLEMENTACION_IDENTIFICACION_OPERATIVA_LOTES_R1_20260925.md` y en `03_TESTS.md` §8.

**Limitación de evidencia (explícita):** no existían lotes por volumen con cantidad positiva en
ubicación interna, por lo que R1 y el filtro `Lotes Volumen` **no** quedaron validados visualmente
con stock. La validación cubre upgrade, estructura, cálculo y consulta de solo lectura.

**Riesgos y deuda declarados:**
- Las exportaciones XLSX (R1/R2/R5/R7/R9) usan el helper canónico de reporte, que devuelve el
  nombre técnico del lote: **aún no** presentan `Lote Volumen`.
- Conviven múltiples fuentes de fecha de ingreso en `stock.quant`; la normalización definitiva queda
  pendiente como decisión arquitectónica.
- No existe test automatizado para el token técnico, la etiqueta operativa ni `is_volume_lot`.
- Registros históricos pueden quedar legítimamente vacíos en los campos nuevos (sin origen
  asociado); no se pueblan datos.
- Cinco campos `store=True` más un índice booleano de baja cardinalidad sobre `stock.quant`:
  observar rendimiento si el volumen de quants crece.
- La rebaja/registro físico de stock por volumen **no** está implementada y no forma parte de AD-77.

Módulos afectados: madenat_lumber_reports, madenat_lumber_docs

---

## 2026-09-25 — Interfaz operativa oficial de Intake

### AD-78 (2026-09-25) — Intake como interfaz operativa oficial de Operaciones; el formulario de la Guía queda para consulta y auditoría

**Contexto:** el flujo de Recepción por Volumen (`tipo_recepcion = 'granel'`, AD-65/AD-71/AD-72/AD-74/AD-76)
se opera desde `madenat_lumber_intake` (wizard, consola y fachada ligera de AD-55), mientras que el
formulario clásico de `madenat.guia.processing` concentra la superficie de datos. Sin una regla explícita,
la propiedad de la interfaz operativa quedaba ambigua.

**Decisión:**

1. **Intake es la interfaz operativa oficial de Operaciones.** El formulario clásico de
   `madenat.guia.processing` no debe considerarse la pantalla operativa final para Operaciones.
   `madenat_lumber_intake` concentra wizard, consola, carga documental, revisión, captura y ajustes de
   datos de recepción por volumen, y validación del flujo.
2. **El modelo sigue siendo el propietario persistente.** `madenat.guia.processing` es el registro
   persistente de la Guía y de su trazabilidad documental, comercial, física y logística; su formulario
   clásico queda destinado a consulta, soporte administrativo, auditoría y trazabilidad técnica.
3. **Contrato de Recepción por Volumen:** Intake → 1 Guía → 1 Etiqueta SV → 1 `stock.lot` volume → 1
   picking incoming. Los datos RW (`anchos_variables`), RL (`largos_variables`), espesor nominal
   (`espesor_nominal_texto`), piezas declaradas (`piezas_declaradas`), M³ declarado (`volumen_declarado_m3`)
   y la etiqueta SV (`volume_lot_id`, solo lectura) deben presentarse y gestionarse en Intake. El modelo
   `madenat.guia.processing` sigue siendo el propietario persistente de esos valores, pero no la interfaz
   operativa principal.

---

## 2026-09-26 — Gestión Operativa de Etiquetas SV

### AD-79 (2026-09-26) — Gestión Operativa de Etiquetas SV (ledger append-only, autonomía y escalamiento)

**Contexto:** Operaciones requiere autonomía profesional sobre la identidad y el volumen
documental de las Etiquetas SV del Ingreso por Volúmenes, sin renunciar a la trazabilidad ni
a la protección de datos históricos. El sistema debe validar y documentar sin burocracia
innecesaria, reservando la aprobación adicional para impactos financieros o documentales
relevantes; hasta ahora no existía una regla explícita de quién puede modificar la etiqueta o
el baseline documental, cómo se corrige un error ni cómo se evita el sobre-consumo de saldo.

**Decisión:**

1. **Ledger único append-only.** Las operaciones sobre Etiquetas SV se registran en
   `madenat.sv.operation` con tipos `rename`, `regularize_volume`, `rebaja` y `rebaja_reverse`
   (labels «Modificación de etiqueta SV», «Regularización de volumen», «Rebaja de etiqueta»,
   «Reversa de rebaja») y estados `draft / applied / reversed / rejected`. La historia aplicada
   no se edita ni se elimina; toman snapshot y firma SHA-256 y se reflejan en chatter y en
   `madenat.audit.log`.
2. **Renombre controlado en sitio con alias histórico no reutilizable.** El renombre cambia
   únicamente el identificador vigente (`stock.lot.name`); no crea un lote nuevo, no consume la
   secuencia `madenat.volume.lot` y no altera volumen, piezas, producto, Guía, movimientos,
   pickings, costos, facturas, valoración, consolidación ni estado. La etiqueta anterior queda
   como alias histórico y ni la etiqueta actual ni las históricas pueden reutilizarse.
3. **Regularización documental sin efecto retroactivo.** La regularización define el baseline
   documental vigente del lote; no modifica retroactivamente movimientos, quants, pickings,
   costos, valoración, facturas ni consolidaciones. Exige motivo y evidencia documental,
   volumen estrictamente positivo y no por debajo del rebajado activo.
4. **Rebaja y reversa.** La rebaja consume saldo disponible y no puede dejar saldo negativo; la
   reversa crea un evento opuesto enlazado a la rebaja original y nunca la edita ni la elimina.
   Cada rebaja admite una sola reversa completa.
5. **Piezas solo con fuente documental positiva.** El balance de piezas se habilita únicamente
   si la Guía declara `piezas_declaradas > 0` o `packing_pieces_declared > 0`; nunca desde
   paquetes, líneas PDF, fila sintética GRANEL ni `stock.lot.piezas = 1`.
6. **Volumen oficial.** Precedencia Guía PDF → Packing Excel → Packing declarado (primer valor
   estrictamente positivo); sin fuente positiva no existe volumen oficial. Consolidado en AD-74.
7. **Autonomía y escalamiento.** Operaciones ejecuta las acciones rutinarias sin aprobación
   adicional cuando no hay impacto financiero ni documental relevante. **Auditoría** aprueba el
   alza del baseline documental y las excepciones de trazabilidad de etiquetas SV.
   **Contabilidad** aprueba cuando existe costo, valoración, factura, consolidación facturada o
   cerrada, o período financiero cerrado afectado. La aprobación se registra en la propia
   operación (`approved_by_id`) y no como simple visibilidad de botón.
8. **Guardas server-side.** Los campos SV protegidos de `stock.lot` no admiten escritura directa;
   solo el flujo interno autorizado de una operación SV validada puede escribir la etiqueta, el
   volumen, las piezas y la marca técnica de serialización, mediante un permiso interno de un
   solo uso ligado a actor, lote, operación y valores esperados.
9. **Concurrencia fail-closed.** Bloqueo de la fila del lote y de la operación, recálculo del
   saldo dentro de la misma transacción y rechazo del intento conflictivo sin saldo negativo ni
   registros parciales. El usuario recibe el mensaje funcional aprobado: «Otro usuario modificó
   esta etiqueta SV mientras se procesaba la operación. La operación no fue aplicada. Actualice
   la información y vuelva a intentarlo.» No hay reintento automático silencioso.
10. **Reversa por lote SV específico.** La cancelación/devolución de una Guía de Volumen usa
    exclusivamente el lote SV vinculado; no sustituye lotes de terceros y evita retornos
    duplicados mediante relaciones técnicas de retorno.
11. **Sin corrección retrospectiva por write directo.** Toda corrección de etiqueta, baseline o
    saldo se realiza mediante una operación SV nueva, con motivo (y evidencia cuando aplique).
12. **Límite técnico actual de aprobaciones.** La implementación soporta como máximo **dos
    aprobadores explícitos** por operación (`approved_by_id` y `approved_by_id_secondary`). No
    existe todavía un motor genérico de aprobaciones de tres o más niveles.

**No objetivos:** no modificar automáticamente movimientos históricos; no reescribir quants,
pickings, costos, facturas, valoración, consolidaciones ni la secuencia SV; no modificar
históricamente la Guía 4495589 ni la etiqueta SV00000000008; no introducir un flujo de stock
paralelo al de inventario estándar.

**Consecuencias:** mayor trazabilidad y autonomía controlada de Operaciones; cada cambio queda
registrado de forma append-only con evidencia y auditoría; el saldo SV se vuelve determinista y
auditable; la deuda técnica T1–T7 documentada en `05_BACKLOG.md` permanece **fuera** del alcance
de esta decisión.

**Evidencia:** suite `sv` en `madenat_test` — 56 pruebas, 0 fallas, 0 errores (`03_TESTS.md` §9).
Casos históricos verificados por consulta de solo lectura: Guía 4495589 y SV00000000008 sin
modificación; secuencia `madenat.volume.lot` sin cambios; ledger, capacidades y marcadores de
prueba en 0 filas.

**Caso histórico documentado (no modificado):** Guía `4495589` (`madenat.guia.processing` 6566)
con volumen oficial PDF 40,315 m³ e histórico operativo/detalle 40,300 m³ (diferencia 0,015 m³).
La implementación SV **no** modificó la Guía ni la etiqueta. Cualquier corrección futura debe
realizarse mediante una operación SV formal con motivo y evidencia (regularización documental),
nunca por edición directa.

Módulos afectados: madenat_lumber_core (`madenat_sv_operation.py`, `madenat_sv_internal.py`,
`stock_lot.py`, `madenat_guia_processing.py`, seguridad y vistas/wizards SV),
madenat_lumber_logistics (asignación/liberación SV), madenat_lumber_docs.

4. **Naturaleza de los datos declarados.** Los seis campos son opcionales, editables, no calculados y no
   bloqueantes; el detalle de líneas no es requisito operativo de Volumen.
5. **Sin cambios de comportamiento.** La decisión es de propiedad de interfaz: no altera gates, validación,
   identidad F3.1 de la etiqueta SV, movimientos de inventario, pickings ni datos históricos.

**Alcance y límites:** registro documental de la decisión; sin cambios de código en esta sesión. La
exposición de los seis campos en las pantallas de Intake no forma parte de esta decisión. No se renumera ni
se reasigna ningún AD previo (AD-70 sigue reservado al costeo por consumo parcial).

Módulos afectados: madenat_lumber_intake, madenat_lumber_core, madenat_lumber_docs

---

### AD-80 (2026-09-28) — UX de volumen oficial, bloque SV visible y ciclo de vida controlado de guías

**Decisión.** Se implementa la Fase 2 del frente de Recepción por Volumen: jerarquía del
volumen oficial en la Consola de Ingreso de Madera, bloque SV visible con las acciones
autorizadas y un ciclo de vida controlado de guías (Modos A–D).

#### 1. Derogación expresa (reemplaza una regla anterior)

La regla **«sin acciones SV en la Consola»** queda **derogada**. Se reemplaza por aserciones
positivas que verifican las acciones autorizadas. Desde la Consola y desde el formulario de la
Guía, Operaciones puede abrir —cuando existe un lote SV real (`volume_lot_id` /
`declared_sv_lot_id`)—:

- Modificar etiqueta SV;
- Regularizar volumen;
- Rebajar etiqueta;
- Reversar rebaja (únicamente sobre una rebaja `applied` aún no reversada);
- Ver historial SV.

Ninguna acción escribe directamente `stock.lot.name`, el volumen ni el saldo: todas delegan en
los wizards del Programa SV y, por tanto, en el ledger append-only, la capacidad interna de un
solo uso, las guardas server-side, el control de saldo, la concurrencia fail-closed y el
escalamiento ya implementados (AD-79). Sin lote SV el bloque muestra solo
`Se asignará al enviar a stock.` y no expone ningún botón de mutación.

#### 2. Jerarquía del volumen oficial (único volumen primario)

- **Primario:** `VOLUMEN OFICIAL DE LA GUÍA` (`official_volume_m3` + `official_volume_source`)
  con la leyenda «Gobierna stock, conciliación y consolidación.». Es el primer bloque de la
  Recepción por Volumen y no contiene ningún volumen competidor.
- **Secundarios (no gobiernan):** `M³ declarado por Operaciones (referencia)` con la nota «No
  gobierna stock ni reemplaza el volumen oficial.» y `Volumen operativo de referencia (no
  gobierna stock)`.
- **Detalle (solo control interno):** `Control documental interno (auditoría)` con `Total de
  líneas del detalle PDF (control interno)` y `Diferencia vs volumen oficial`.
- **Encabezado:** para `ingestion_type = 'volume'` no se muestra el cuarto agregado
  competitivo `Volumen:`. El indicador de volumen total queda oculto para Volumen
  (`invisible="ingestion_type == 'volume'"`).

#### 3. Bloque SV visible (solo lectura)

Bloque `ETIQUETA SV Y SALDO OPERATIVO`, visible únicamente con lote SV real, con etiqueta SV,
volumen documental original, volumen regularizado, volumen rebajado, saldo disponible, piezas
disponibles solo si `sv_pieces_enabled` es verdadero, advertencia documental solo si existe, y
las cinco acciones autorizadas. Prohibido usar `stock.lot.piezas = 1`, paquetes, líneas PDF o
filas sintéticas como piezas documentales. Los campos del bloque son proxies **no almacenados**
(la Consola es una vista SQL `_auto = False`).

#### 4. Ciclo de vida controlado (cuatro modos)

| Modo | Precondiciones | Acción | Auditoría | Bloqueos duros |
|---|---|---|---|---|
| **A. Eliminar definitivamente** | `state in ('draft','cancelled')`; sin `stock.lot` con `volume_source_guia_id`; sin picking ni movimiento; sin quant; sin operación SV; sin costo, valoración, factura, consolidación, contenedor, embarque ni período cerrado; motivo y confirmación explícita | `unlink()` canónico de la guía | `madenat.audit.log` `guia_delete_permanent` (snapshot + SHA-256) | Cualquier traza detectada |
| **B. Cancelar y conservar** | Motivo obligatorio | `action_force_cancel()` (semántica intacta) | Chatter del origen con el motivo | Los escudos propios del método canónico |
| **C. Purgar de forma controlada** | Guía `draft`/`cancelled`; lote SV técnico sin historia material; sin movimientos ni pickings en ningún estado; sin registros de `stock.quant`; operaciones SV solo en borrador (eliminables legalmente); sin trazas financieras; **sin evidencia documental** (adjuntos, chatter con contenido o referencias genéricas); motivo, confirmación escrita literal `PURGAR` y Jefatura de Operaciones | borra operaciones SV en borrador → lote técnico → guía | `madenat.audit.log` `guia_purged` | Aplicadas/reversadas, rechazadas, quants, movimientos, pickings, costo, valoración, factura, consolidación, contenedor, embarque, período cerrado, **evidencia documental** |
| **D. Bloquear y escalar** | Siempre disponible | no elimina nada; lista completa de bloqueadores y rutas correctas | `madenat.audit.log` `guia_delete_blocked` | — |

Reglas no negociables aplicadas: si existe cualquier movimiento, retorno, picking, cuant,
rebaja aplicada, reversa aplicada, costo, valoración, factura, consolidación, contenedor,
embarque o período cerrado, la purga queda **bloqueada**. La purga del Modo C exige además que
**no exista ningún registro de `stock.quant`** (lectura estricta de la regla no negociable: la
purga no elimina registros de inventario) y que no haya operaciones SV rechazadas, porque el
ledger append-only no permite eliminarlas.

**Precisión (2026-10-02) — alcance del principio de no-borrado.** El mismo principio rige la
corrección de recepción: `lumber.reception.action_reset_to_draft` **no** borra ni escribe
directamente `stock.quant`, lotes, pickings, movimientos ni líneas de movimiento con historia
física. Abre el asistente `lumber.reception.reset.wizard` (motivo obligatorio solo ante **efecto
físico**), revierte los pickings `done` atribuidos por `stock.picking.reception_id` con *return
picking* nativo y cancela/desreserva los no `done`, con idempotencia por movimiento origen y
evidencia en `madenat.audit.log` (`action_type='deviation'`, snapshot + SHA-256) y chatter
(ver `00_ARQUITECTURA.md` §4.2).

**Actualización G1 (2026-10-02) — reapertura de guía.** La reapertura
`madenat.guia.processing.action_reopen_to_draft` ya es **no bloqueante y trazable**: abre wizard
(motivo solo con efecto físico), revierte el **consumo BT-04** con retorno nativo idempotente
(`_reverse_consumption_picking`, sin modificar) y, **sin vínculo fuerte**, **conserva**
stock/lotes/pickings/movimientos con advertencia de atribución insuficiente; no escribe/borra
`stock.quant` ni muta `origin` (ver `00_ARQUITECTURA.md` §4.3).

**Actualización G2 + G3 (2026-10-02) — vínculo fuerte y retorno de producción.** **G2** añade la
**llave fuerte** `stock.picking.guia_processing_id` → `madenat.guia.processing.id` (Many2one,
`index=True`, `ondelete='set null'`, `copy=False`, `check_company=False`), asignada **solo** al crear
el picking de ingreso de producción en `_get_or_create_picking_unified`; nunca se propaga a consumo,
retornos, recepción, rebaja, contenedor, exportación ni inventario, y **nunca** infiere históricos.
**G3** añade la **reversión física automática, nativa, trazable e idempotente** de ese ingreso de
producción al reabrir la guía (flujo G1): `_attributed_production_pickings()` +
`_reverse_production_picking()`. La atribución es **exclusiva por FK** (nunca `origin` textual ni
`lot_id`); la idempotencia usa la relación nativa `return_id`; el retorno **no** porta
`guia_processing_id` (exclusión G2); la producción/legado **sin** FK se conserva con **advertencia**
de atribución insuficiente. No se escribe/borra `stock.quant` ni se muta `origin`. Ver
`00_ARQUITECTURA.md` §4.3.

**Regla de evidencia documental (Modo C y Modo A).** Odoo destruye la evidencia al eliminar un
registro: `mail.thread.unlink` borra los `mail.message` y `BaseModel.unlink` borra los
`ir.attachment` con `res_model`/`res_id`. Por tanto, la purga (Modo C) y la eliminación
definitiva (Modo A) **quedan bloqueadas si existe evidencia**: cualquier `ir.attachment`
(documentos PDF/Excel), cualquier mensaje de chatter con contenido —comentario, correo,
notificación de negocio o mensaje con adjuntos— y cualquier referencia genérica persistente por
`(res_model, res_id)` sobre la guía (p. ej. `mail.activity`, `product.document`,
`quotation.document`). Se excluye únicamente el aviso automático de creación de `mail.thread`
(`_('%s created', …)`, sin adjuntos y sin otro contenido) y el estado transitorio de UI
(`ir.actions.act_window`, `mail.followers`, `mail.wizard.invite`, `payment.link.wizard`,
`portal.share`, `privacy.lookup.wizard.line`, `sms.composer`), que no son evidencia y que Odoo
elimina con el propio registro. Con evidencia presente, la ruta correcta es el Modo B (cancelar
conservando trazabilidad) o la gestión formal del documento antes de reintentar la purga.
Nunca se usa SQL de escritura, nunca `ON DELETE
CASCADE`, nunca se borran movimientos/pickings históricos ni operaciones SV
aplicadas/reversadas, y nunca se nulifica ni reasigna `volume_source_guia_id` sobre un lote
sobreviviente (el lote técnico se elimina junto con la guía).


#### 5. Archivado diferido (sin campo `active`)

No se agrega campo `active`, archivado ni filtro de archivado en la Consola en esta fase: la
vista SQL de la Consola no filtra `active` y agregarlo sin el diseño completo produciría
inconsistencias. El archivado queda como **fase posterior separada** (registrado en
`05_BACKLOG.md`).

#### 6. Autoría y escalamiento

- **Jefatura de Operaciones** ejecuta la purga controlada (Modo C).
- **Auditoría/Contabilidad** revisan solo cuando el diagnóstico detecta trazas financieras;
  esas trazas convierten el caso en **Modo D** y bloquean la purga (no se abre una revisión
  sobre un registro que igualmente debe bloquearse).

#### No objetivos

No se modifica `action_force_cancel()`, `action_reopen_to_draft()`, el ledger SV, la capacidad
interna, las guardas de `stock.lot`, la concurrencia, las secuencias ni las guardas del
Programa SV. No se edita directamente `stock.lot.name`, volumen o saldo. No se toca la Guía
4495589 ni la etiqueta SV00000000008. No se usan SQL `INSERT/UPDATE/DELETE`. No se modifican
movimientos, pickings, quants, costos, facturas, consolidaciones ni embarques históricos.

#### Evidencia

- Suite nueva de Intake: `TestIntakeConsoleSvActions` (7), `TestVolumeUiHierarchy` (4),
  `TestGuideLifecycle` (14) → **25 pruebas, 0 fallas, 0 errores**.
- Suite nueva de Core: `TestSvReverseUi` (3) → **3 pruebas, 0 fallas, 0 errores**.
- Regresión Intake completa: **233 pruebas, 0 fallas, 0 errores** (incluye volumen oficial
  AD-74/AD-79 reescrito a aserciones positivas de acciones SV autorizadas).
- Regresión Core (tag `sv` + F3.1 + ruta granel + volumen restante): **81 pruebas, 0 fallas, 0
  errores**.
- Upgrade de `madenat_lumber_core` (18.0.6.3.0) y `madenat_lumber_intake` (18.0.0.6.0) sobre
  `madenat_test`: código de salida 0, sin errores; los avisos preexistentes de vistas/grupos no
  aumentan con este cambio.
- Contraste histórico (consulta de solo lectura): Guía 4495589 (`id` 6566, `write_date`
  2026-09-27 02:32:39, anterior a esta sesión), etiqueta `SV00000000008` (`stock.lot` 3772,
  `write_date` 2026-09-26 06:14:57, sin marca de serialización y sin operaciones SV), secuencia
  `madenat.volume.lot` con `number_next = 1` y ledger SV en 0 filas. Cero filas de datos de
  prueba persistidas y cero eventos de auditoría nuevos de los tipos `guia_delete_*` /
  `guia_purged`.

Módulos afectados: `madenat_lumber_intake` (bloque SV de la Consola, ciclo de vida, vistas,
ACL, tests), `madenat_lumber_core` (`action_type` de `madenat.audit.log`, vistas SV de la Guía
y del ledger, test de UI de reversa) y `madenat_lumber_docs`.

---

### AD-81 (2026-10-01) — PROPUESTA: orden de trabajo vigente (ingreso a stock → consolidación → mantenimiento → logística; contable/auditoría/facturación diferidos)

> **Estado: PROPUESTA — NO APROBADA.** Registrada el 2026-10-01 a solicitud del usuario. **No constituye regla vigente** hasta su aprobación explícita.

**Propuesta.** Se propone fijar el siguiente **orden de trabajo** para el ciclo actual:

1. **Ingreso a stock** (Operaciones): recepción, guías, lotes, envío a stock.
2. **Consolidación**: por contenedor y **rebaja por motonave**.
3. **Módulo de mantenimiento**.
4. **Logística y exportación**.

Quedan **diferidos** (fuera del ciclo actual, sin fecha): lo **contable**, la **auditoría** y la **facturación**.

**Motivo.** El usuario determina que el valor inmediato está en cerrar el flujo físico-trazable (de la recepción al embarque) antes de abordar los frentes contable/financiero. Los hallazgos de esas áreas se **registran** pero **no se abordan** en este ciclo.

**Consecuencias documentales.**

- La auditoría del 2026-10-01 (`16_AUDITORIA_20261001.md`) clasifica los pendientes por área conforme a este orden; los de Contabilidad/Auditoría/Facturación quedan marcados como *diferidos por el usuario*.
- `05_BACKLOG.md` incorpora la sección «Auditoría 2026-10-01 — pendientes por área» con el mismo encuadre.

**No objetivos.** Esta decisión **no** modifica AD-65, AD-77, AD-79 ni AD-80; **no** altera reglas de negocio, valorización, costeo ni estados; **no** autoriza cambios de código, datos ni parámetros. Es exclusivamente un **orden de prioridad**.

**Estado de aprobación:** ⏳ **pendiente de aprobación del usuario**. Mientras no se apruebe, el orden anterior (frente principal AD-65 / Programación 1) permanece como referencia operativa.

**Evidencia:** registro de la sesión de auditoría del 2026-10-01; `16_AUDITORIA_20261001.md` §1.

---

### AD-82 (2026-10-01) — PROPUESTA: salida única de stock al rebajar contenedor/nave

> **Estado: PROPUESTA — NO APROBADA.** Registrada el 2026-10-01 a solicitud del usuario. **No constituye regla vigente** hasta su aprobación explícita. Base: `17_CONSTITUCION_VOLUMENES.md` §3 (A-1) y §7. **No autoriza cambios de código, datos ni parámetros.**
>
> **Actualización 2026-10-01 — ✅ APROBADA e IMPLEMENTADA.** El **zarpe ya no descuenta** stock (`action_set_in_transit` exige contenedores en estado `rebajado`); la salida nativa ocurre en la acción **Rebajar contenedor** (`_rebajar_container`) y en el asistente **Rebajar por nave**. `_action_reduce_stock` fue **eliminado**.
>
> **Alineación 2026-10-01 (AD-87).** Esta regla rige la **exportación de lotes de tarja**. El **SV (Lote Volumen) no se exporta**: su salida nativa única ocurre en la **imputación** (AD-87, `CANON/19` §4.4).

**Propuesta.** La **salida nativa de stock** (picking de descuento de existencias) se ejecuta en la acción explícita de **rebajar** el contenedor o la nave. El **zarpe deja de descontar** stock y pasa a ser un evento de estado documental/logístico.

**Motivo.** Hoy el descuento ocurre en el zarpe (`action_set_in_transit` → `_action_reduce_stock`, `madenat_lumber_logistics/models/lumber_export_shipment.py:461,479`) y mueve `quantity = 1` por lote (`:571,582`), lo que deja stock residual y desacopla el hecho físico del movimiento. Concentrar la salida en la rebaja da un **único punto de descuento trazable**.

**Alcance propuesto.** Un solo origen de descuento de stock (la rebaja); el zarpe cambia estados y documentos sin mover quants. Los documentos (tarja, packing, BL) siguen usando el volumen de EXPORTACIÓN (documental) según `17` §2.

**No objetivos.** No modifica AD-04 (Gate 3), ni las reglas de ingesta, valorización ni costeo; no altera el ledger SV (ver AD-83/AD-84). Es exclusivamente el **punto de salida de stock**.

**Estado de aprobación:** ⏳ **pendiente de aprobación del usuario**. Hasta su aprobación rige el comportamiento vigente (`17` §2, F-01 en §6).

**Evidencia:** informe de auditoría de volúmenes del 2026-10-01; `17_CONSTITUCION_VOLUMENES.md` §3, §6, §7.

---

### AD-83 (2026-10-01) — PROPUESTA: módulo propio para la rebaja SV con descuento por procesados

> **Estado: PROPUESTA — NO APROBADA.** Registrada el 2026-10-01 a solicitud del usuario. **No constituye regla vigente** hasta su aprobación explícita. Base: `17_CONSTITUCION_VOLUMENES.md` §3 (A-2) y §7. **No autoriza cambios de código, datos ni parámetros.**
>
> **Actualización 2026-10-01 — ✅ APROBADA EN PRINCIPIO (sin extraer módulo ahora).** La rebaja de un lote SV descuenta **exactamente el volumen asignado** (no `1`); el módulo propio de rebaja SV **no se extrae** en este ciclo (implementación dentro de `madenat_lumber_logistics`, reutilizando el ledger `madenat.sv.operation`). El momento del ledger SV **no cambia** (sigue registrándose al asignar).
>
> **Actualización 2026-10-01 (2) — ⛔ REEMPLAZADA por AD-87.** Con la decisión D1 (el SV **nunca se exporta**) y D3 (la imputación etiqueta→SV es la que descuenta el quant del SV), esta AD **deja de regir**: (a) no se extrae módulo propio de rebaja SV; (b) el «descuento por procesados» se materializa como **imputación** (AD-87); (c) la asignación SV a contenedor de exportación **no aplica** (solo tarja). El principio «descontar exactamente el volumen asignado (no `1`)» se conserva y queda cubierto por AD-82 (tarja) y AD-87 (SV). Ver `CANON/19` §4.4 y §13.2 (CR-19-05).

**Propuesta.** Extraer la **rebaja SV** a un **módulo propio** (ledger `madenat.sv.operation` desacoplado) que contemple el **descuento por procesados**, de modo que:
- la **asignación parcial** a contenedores descuente **exactamente el volumen asignado** (no `1`);
- el **stock acompañe al ledger** (cada rebaja con efecto físico y trazable), en coordinación con AD-82.

**Motivo.** Hoy la rebaja SV sólo mueve el ledger y **no toca `stock.quant`** (`madenat_lumber_core/models/madenat_sv_operation.py:14,923-950`), mientras la salida nativa mueve `1` por lote (`lumber_export_shipment.py:571,582`). Un lote SV asignado parcialmente a varios contenedores queda con saldo y stock desalineados.

**Alcance propuesto.** Módulo/ledger con descuento por volumen asignado y por procesados; reglas de captura de procesados dentro del alcance del ciclo actual (AD-81).

**No objetivos.** No modifica AD-79/AD-80 (ledger SV vigente) salvo lo estrictamente necesario para el descuento por procesados; no altera la ingesta ni el volumen oficial (`12_FLUJOS_INGESTA.md` §11.5). Es una **extracción de módulo y regla de descuento**.

**Estado de aprobación:** ⏳ **pendiente de aprobación del usuario**. Hasta su aprobación rige el comportamiento vigente (`17` §2.8, F-02/F-03 en §6).

**Evidencia:** informe de auditoría de volúmenes del 2026-10-01; `17_CONSTITUCION_VOLUMENES.md` §2.8, §3, §7.


---

### AD-84 (2026-10-01) — PROPUESTA: regla de invariantes del ledger SV y del stock

> **Estado: PROPUESTA — NO APROBADA.** Registrada el 2026-10-01 a solicitud del usuario. **No constituye regla vigente** hasta su aprobación explícita. Base: `17_CONSTITUCION_VOLUMENES.md` §1 y §7. **No autoriza cambios de código, datos ni parámetros.**
>
> **Actualización 2026-10-01 — ✅ APROBADA e IMPLEMENTADA (parcial).** Se aplicaron la **idempotencia por (contenedor, lote)** (restricción única en `lumber.shipment.line`) y la **causa única de descuento** (salida nativa solo en la rebaja). Los invariantes del ledger SV y del stock se verifican por tests de `stock.quant`. La concurrencia fail-closed del ledger se mantiene (no modificada).
>
> **Ampliación 2026-10-01 (AD-87).** El saldo SV resta **también** las **imputaciones activas** (procesados): `sv_available_m3 = sv_regularized_baseline_m3 − Σ rebajas activas − Σ imputaciones activas`. La **causa única de descuento del SV** pasa a ser la **imputación**; la rebaja rige solo para lotes de **tarja** en export. Ver AD-87 y `CANON/19` §7.3.

**Propuesta.** Fijar como **invariantes** verificables del sistema de volúmenes:

1. **DISPONIBLE = stock nominal:** `stock.lot.volumen_restante_m3 = Σ stock.quant.quantity` en ubicaciones internas (base nominal, m³).
2. **Saldo SV:** `stock.lot.sv_available_m3 = sv_regularized_baseline_m3 − Σ rebajas activas` (rebajas `applied` menos reversas válidas).
3. **Cota por destino:** la suma de rebajas SV por contenedor/embarque ≤ volumen oficial (nominal) del lote.
4. **Causa única de descuento:** todo decremento de stock tiene **una sola causa trazable** — rebaja (AD-82), consumo de procesados (AD-83) o ajuste autorizado — sin dobles descuentos.
5. **Concurrencia fail-closed:** las escrituras del ledger mantienen guarda de concurrencia; ante carrera, se bloquea (nunca se aplica a medias).

**Motivo.** Hoy el invariante (1) se cumple mayormente (77/78 lotes en `madenat_test` al 2026-10-01), pero (2)/(3)/(4) no están garantizados por una regla explícita y la salida nativa mueve `1` (`lumber_export_shipment.py:571,582`), rompiendo (4).

**Alcance propuesto.** Regla de invariantes + guardas; su verificación debería exponerse en el reporte de inventario y en el ledger SV.

**No objetivos.** No modifica AD-79/AD-80 salvo lo necesario para verificar los invariantes; no altera valorización, costeo ni facturación (diferidos por AD-81). Es una **regla de consistencia**, no una migración de datos.

**Estado de aprobación:** ⏳ **pendiente de aprobación del usuario**. Hasta su aprobación rigen los invariantes observados en `17` §2.9.

**Evidencia:** informe de auditoría de volúmenes del 2026-10-01; `17_CONSTITUCION_VOLUMENES.md` §1, §2.9, §7.


---

### AD-85 (2026-10-01) — PROPUESTA: especificación de consolidación y rebaja de contenedores y naves (documento `18`)

> **Estado: PROPUESTA — NO APROBADA.** Registrada el 2026-10-01 a solicitud del usuario. **No constituye regla vigente** hasta su aprobación explícita. Base: `18_CONSOLIDACION_Y_REBAJA.md`; `17_CONSTITUCION_VOLUMENES.md` §3 (A-1..A-3); AD-81, AD-82, AD-83, AD-84. **No autoriza cambios de código, datos ni parámetros.**

**Propuesta.** Adoptar `CANON/18_CONSOLIDACION_Y_REBAJA.md` (BORRADOR/PROPUESTA) como **especificación canónica** de la consolidación y la rebaja de contenedores y naves, fijando:

- la **separación** consolidar (vincular/reservar, sin descontar) vs rebajar (descontar) (AC-1);
- la **rebaja por contenedor** y **por nave/viaje** (masiva sobre contenedores consolidados pendientes) (AC-2);
- los **estados de negocio** (consolidado/rebajado/zarpado/entregado/rolleado) **mapeados** a los estados vigentes, reutilizando `lumber.container.state` y `lumber.export.shipment.state` (con «rebajado» como decisión abierta Q-06);
- los **eventos de rolleo** con trazabilidad estructurada de origen/destino (embarque, nave, viaje, booking, motivo, fecha, costos) (AC-7);
- los **campos nuevos mínimos**: `voyage_id` directo en contenedor, `booking_id`, consignatario, P.O. del comprador, armador/naviera y tara editable (§3.4).

**Motivo.** El flujo físico-trazable de exportación (recepción → consolidación → rebaja → zarpe → entrega) requiere un único punto de descuento (AD-82), cantidad por volumen (AD-83) e invariantes verificables (AD-84). Hoy el descuento ocurre en el zarpe moviendo `1` por lote (`lumber_export_shipment.py:461,479,571,582`) y el rolleo solo deja rastro en chatter (`lumber_container_rollover_wizard.py:201-206`).

**Alcance propuesto.** Especificación documental reutilizando `lumber.export.shipment`, `lumber.container`, `lumber.shipment.line`, `stock.lot`, `madenat.sv.operation`, `shipping.vessel/voyage/booking` y los wizards existentes. Las diferencias (~15) quedan en §11 del documento **sin decidir por el usuario**.

**No objetivos.** No modifica AD-79/AD-80/AD-82/AD-83/AD-84; no altera valorización, costeo, facturación ni auditoría (diferidos por AD-81). Es una **especificación**, no una implementación.

**Estado de aprobación:** ⏳ **pendiente de aprobación del usuario**. Hasta su aprobación rige el comportamiento vigente (`17` §2).

**Evidencia:** `18_CONSOLIDACION_Y_REBAJA.md`; `17_CONSTITUCION_VOLUMENES.md` §3; código verificado (archivo:línea en `18` §13).


---

### AD-86 (2026-10-01) — PROPUESTA: grupo funcional «Logística» y matriz de autorización de consolidación/rebaja

> **Estado: PROPUESTA — NO APROBADA.** Registrada el 2026-10-01 a solicitud del usuario. **No constituye regla vigente** hasta su aprobación explícita. Base: `18_CONSOLIDACION_Y_REBAJA.md` §8. **No autoriza cambios de código, datos ni parámetros.**
>
> **Actualización 2026-10-01 (implementación): sigue PROPUESTA.** No se creó el grupo «Logística»; la rebaja usa los **grupos existentes** (`Operaciones`/`Jefatura de Operaciones`/`Gerencia`) con **ACL explícitas** y **rechazo en servidor** (`_rebaja_require_group`).

**Propuesta.** Crear el grupo funcional **«Logística»** `group_madenat_logistica` (categoría `module_category_madenat`), con su jefatura `group_madenat_logistica_jefatura` siguiendo el patrón de `group_madenat_jefatura_operaciones`, y:

- migrar las ACL de `madenat_lumber_logistics` (hoy `base.group_user` / `stock.group_stock_manager`) a usuario/jefatura de Logística;
- **unificar** la matriz de `lumber.shipment.cost.line` (hoy **duplicada** entre `madenat_lumber_logistics` y `madenat_vendor_payment`);
- fijar la **matriz de autorización** de consolidar / rebajar / rebajar por nave / rollear (antes y después de rebajar) / reversar, con Gerencia y Auditoría en lectura.

**Motivo.** Hoy **no existe** un grupo «Logística»; las ACL de logística usan grupos genéricos de Stock, y `lumber.shipment.cost.line` tiene **dos** ACL en módulos distintos (`madenat_lumber_logistics/security/ir.model.access.csv` y `madenat_vendor_payment/security/ir.model.access.csv`). La especificación `18` necesita una matriz explícita (p. ej. reversa y bloqueo de viaje cerrado no deben quedar al alcance del usuario raso).

**Alcance propuesto.** Alta de grupos + reasignación de ACL + matriz. Aplicable también a la revisión de permisos de la Consola (H-01, `16_AUDITORIA_20261001.md`).

**No objetivos.** No otorga permisos de Costos, Contabilidad ni Auditoría; no modifica las reglas de negocio ni los modelos; no cambia la gestión de grupos existentes fuera de Logística.

**Estado de aprobación:** ⏳ **pendiente de aprobación del usuario**. Hasta su aprobación rigen los grupos y ACL vigentes.

**Evidencia:** `18_CONSOLIDACION_Y_REBAJA.md` §8; `madenat_lumber_core/security/madenat_security.xml`; `madenat_lumber_logistics/security/ir.model.access.csv`; `madenat_vendor_payment/security/ir.model.access.csv`.

---

### AD-87 (2026-10-01) — Imputación declarada etiqueta→SV (procesados) y saldo por procesador

> **Estado: ✅ APROBADA (decisión del usuario del 2026-10-01).** Registra las decisiones **D1–D7** y **D9–D10**. Norma completa y modelo de datos: `19_IMPUTACION_SV_Y_PROCESADORES.md`. **No autoriza cambios de código, datos ni parámetros** en esta pasada (especificación).

**Contexto (D1).** MADENAT es **trader**: compra **volumen (SV)** y **madera procesada con etiquetas y dimensionada bruta con tarjas**. El SV puede estar en **bodega** o **directo en el procesador**, y **nunca se exporta**.

**Decisión.**
1. **La imputación etiqueta→SV es el vínculo oficial** entre el retorno procesado y el volumen comprado. La unidad de captura es la **etiqueta**, con su **volumen NOMINAL editable**, contra **uno o varios SV** (D3).
2. **Sin genealogía física** para procesadores externos (alineado con AD-65 §1.6 y DEC-002): el retorno es **stock nuevo e independiente**; el vínculo SV↔etiqueta es una **imputación declarada** (D2).
3. **Efecto físico único:** la imputación registra el **ledger SV** (`madenat.sv.operation`, nuevo tipo `imputacion`) y **genera la salida nativa del quant del SV** (AD-82/AD-84). Es el **único** descuento del SV (D3).
4. **Costo (D4):** costo por m3 **editable** en la imputación; **promedio ponderado** de los SV elegidos; se refleja en `stock.lot.cost.line` (`cost_type='wood'`). **Brecha declarada:** hoy el **SV no tiene costo**; se propone derivarlo de la guía de Recepción por Volumen/OC (ver `19` §5.5).
5. **«En poder del procesador X» (D5):** `stock.location` **interna** por procesador (`usage='internal'`) bajo un padre **`Procesadores`**; **el inventario sigue siendo de MADENAT**.
6. **Momento (D6):** al **recibir la guía de procesados**, con opción explícita de **dejarla pendiente**. Operaciones opera; Auditoría revisa desviaciones.
7. **Merma (D7):** **evento documental**, sin `stock.scrap` automático, con **costo residual visible**.
8. **UX (D9):** los **lotes SV se ocultan por defecto** en el asistente de contenedores (sin impedir su selección).
9. **`parent_lot_id`** pasa a **opcional** en un **paso futuro controlado** (I6, D10).

**Relación con AD-82/AD-83/AD-84/AD-64/AD-65.** Alinea AD-82 (el SV no se exporta; su salida es la imputación), **reemplaza AD-83** (ver su última actualización), **amplía AD-84** (el saldo SV resta imputaciones activas) y **extiende AD-64** (costo del SV). Detalle: `19` §4.4, §13.2.

**No objetivos.** No modifica C2 (compra de procesado con etiquetas/tarjas, flujo `12`/`13`); no altera valorización/facturación (diferidas por AD-81); no toca el ledger SV vigente salvo la adición del tipo `imputacion` y del vínculo `imputation_id`; no migra datos históricos.

**Evidencia:** `19_IMPUTACION_SV_Y_PROCESADORES.md` (§2–§7, §11–§16); decisiones D1–D10 de la sesión 2026-10-01; `madenat_sv_operation.py` (`action_type`); `res_partner.py` (`is_processor`).

---

### AD-88 (2026-10-01) — Principio rector «advertir, motivar, auditar» con helper común

> **Estado: ✅ APROBADA (decisión del usuario, D8).** Principio transversal del sistema MADENAT. Norma y clasificación de bloqueos: `19_IMPUTACION_SV_Y_PROCESADORES.md` §7 y §14.

**Decisión (D8).** **El sistema nunca bloquea al profesional.** Se **advierte**, se **exige motivo** cuando el usuario se desvía de la propuesta y se **audita** la decisión. Permanecen **duros**:
1. los **permisos por rol** (rechazo en servidor);
2. la **integridad técnica** (p. ej. `stock.quant` nunca negativo; guardas de inventario/trazabilidad);
3. las **reglas financieras** (tipo de cambio explícito, cierre de período, UoM).

**Helper común (contrato documentado, sin implementar en esta pasada).** Centralizar la decisión blando/duro y la auditoría en **un único punto** reutilizable (mixin propuesto, p. ej. `MadenatDeviationMixin._guard_deviation(...)`), con el contrato:

```
_guard_deviation(code, message, *, reason=None, hard=False, extra=None)
  · hard=False  → registra advertencia + exige `reason` no vacío + `deviation_flags` + chatter
                  + `madenat.audit.log` (snapshot/firma) y CONTINÚA.
  · hard=True   → lanza UserError con mensaje profesional (permisos, integridad, finanzas).
  · `code`      → identificador estable (AL-xx / B-xx) para reporte y auditoría.
```

**Motivo.** Hoy las guardas están **dispersas** (bloqueos `UserError` mezclados con advertencias no bloqueantes). Un helper común evita regresiones, hace homogénea la política (AD-52/AD-54 ya la anticiparon) y da trazabilidad uniforme.

**Aplicación inmediata (clasificación de bloqueos).** Ver `19` §14: pasan a **advertencia con motivo** el **zarpe** (B-01) y el **saldo SV** (B-04); permanecen **duros** la **rebaja sin disponible** (B-02, integridad), los **permisos** (B-05), el **viaje cerrado** (B-06), los **costos distribuidos** (B-07) y el **duplicado de lote** (B-08); la **reversa con embarque entregado** (B-03) queda dura salvo **override de Gerencia con motivo** (a decidir, Q-19-5).

**No objetivos.** No cambia permisos, presupuestos financieros ni reglas de inventario; no introduce tres o más niveles de aprobación; no modifica datos históricos.

**Evidencia:** `19_IMPUTACION_SV_Y_PROCESADORES.md` §7 y §14; decisiones D8 (y la clasificación de bloqueos de la rama `feat/rebaja-contenedor-20261001`); patrón vigente AD-52/AD-54 (advertencia no bloqueante).

---

### AD-89 (2026-10-02) — Saldo por procesador: fuente física y dos niveles; envío parcial y disponibilidad (bloque I1)

> **Estado: ✅ APROBADA (decisión del usuario del 2026-10-02).** Refina **AD-87** (saldo por procesador) y **AD-88** (advertir/motivar/auditar) para el bloque **I1**. Norma: `19_IMPUTACION_SV_Y_PROCESADORES.md` §16. **No autoriza cambios de código, datos ni parámetros** en esta pasada (documental).

**Contexto.** El **I1 canónico** (ubicaciones `Procesadores/<X>`, saldo por procesador, evento «Envío a procesador») quedó **implementado** en la rama `feat/procesadores-ubicaciones-20261001` (commit `1b25a4c`). El usuario **aprueba I1** y fija cuatro decisiones (**D-I1-01..D-I1-04**).

**Decisión.**
1. **D-I1-01 — Fuente física de verdad, sin modelo de balance.** **No** se crea ahora `madenat.processor.balance`. **`stock.quant` + las ubicaciones internas** `Procesadores/<X>` son la **fuente física de verdad**. Un modelo de saldo **persistente** queda **diferido a BI/cierre** (si se requieren snapshots, conciliación físico-documental, rendimiento o KPI históricos).
2. **D-I1-02 — Saldo por procesador en dos niveles.** (a) **Resumen físico agregado** desde `stock.quant` *(implementado)*; (b) **detalle por lote** con **nominal, disponible, ubicación/procesador, tipo de lote, fecha de ingreso, antigüedad en procesador, guía, proveedor y OC** — **planificado para la fase posterior a la imputación SV→etiqueta** (no implementar aún).
3. **D-I1-03 — Envío parcial no es automáticamente desviación.** El **motivo obligatorio** aplica **solo** si la cantidad ejecutada difiere de una **propuesta, planificación, reserva o cantidad previamente indicada**. Un **envío manual parcial sin propuesta previa es válido** y se audita como **operación normal**. **Nunca** se permite exceder la **disponibilidad física** (integridad dura). **Nota:** el código de I1 **aún** exige motivo ante todo envío parcial ⇒ **corrección pendiente**.
4. **D-I1-04 — Riesgo pre-producción.** Validar la **disponibilidad física frente a reservas de otros pickings/backorders** antes de producción (hoy la validación mide el quant de la ubicación de origen y no descuenta reservas de terceros).

**Estado de implementación (2026-10-02, rama `feat/procesadores-guardas-20261002`).** **D-I1-03 corregido:** el asistente **no** exige motivo ni registra `deviation` sin una **referencia previa persistida y verificable** (inexistente en I1 ⇒ no se inventa propuesta; `_get_deviation_reference` ⇒ `None`). **D-I1-04 resuelto:** se distingue y muestra **físico / reservado por otro / libre** (APIs nativas `stock.quant`), se **rechaza** si solicitado > libre (mensaje con los cuatro valores) sin alterar reservas ajenas, y se preserva el **backorder nativo** de Odoo (documentado por T7). Auditoría `processor_shipment` **idempotente** (`picking_id`). Sin cambios de ACL; el fallback previo de I1 (commit `1b25a4c`) queda superado.

**Relación con AD-87/AD-88.** Refina **AD-87** (§5.4: la **vista sobre `stock.quant`** es la forma aprobada del saldo; **sin** modelo persistente) y precisa **AD-88** (el envío parcial **deja de ser** desviación por defecto; el motivo se reserva a la diferencia frente a una propuesta).

**No objetivos.** No modifica código, datos ni parámetros en esta pasada; no crea modelos, vistas, ACL ni migraciones; no toca `madenat_guia_processing.py`, costeo, valorización ni `madenat.dev_cleanup_enabled`.

**Evidencia:** `19_IMPUTACION_SV_Y_PROCESADORES.md` §16 (bloque I1 y decisiones D-I1-01..04); `05_BACKLOG.md` (I1); rama `feat/procesadores-ubicaciones-20261001` (commit `1b25a4c`).

---

### AD-90 (2026-10-02) — Semántica de inventario en procesador y pendiente de consolidación documental

> **Estado: ✅ APROBADA (decisión del usuario del 2026-10-02).** Fija la **semántica** de la ubicación interna `Procesadores/<Procesador>` y del **SV pendiente de consolidación documental** con productos procesados. **Complementa AD-87, AD-88 y AD-89.** Norma: `19_IMPUTACION_SV_Y_PROCESADORES.md` (§2, §3, §5.4, §7.3, §16). **No autoriza cambios de código, datos ni parámetros** en esta pasada (documental); **no crea modelos, vistas, ACL ni migraciones**.

**Contexto.** MADENAT es **trader**: compra **madera por volumen (SV)**, **madera procesada con etiquetas** y **madera dimensionada bruta con tarjas**. La **ingesta por volumen/SV** y el **envío a un procesador externo** (Ferramenta u otros) se **homologan** como **inventario de MADENAT bajo custodia operativa del procesador**, **pendiente de consolidación documental** con los productos procesados. Un SV **sigue siendo stock de MADENAT**; puede recibirse **directamente** en `Procesadores/<Procesador>` o llegar primero a **bodega** y transferirse internamente a esa ubicación. **Nunca** es venta, exportación, rebaja, salida a cliente, consumo físico automático ni genealogía padre-hijo.

**Decisión.**
1. La ubicación interna **`Procesadores/<Procesador>`** representa **inventario propiedad de MADENAT bajo custodia operativa de un procesador**.
2. Un **SV** en esa ubicación se clasifica operativamente como **pendiente de consolidación documental** con productos procesados.
3. La **recepción directa en procesador** y la **transferencia interna desde bodega** son **rutas físicas equivalentes** para el **saldo físico**.
4. El **envío al procesador** **no** es venta, exportación, rebaja, consumo, merma ni genealogía física.
5. La futura **consolidación/imputación etiqueta→SV** es **declarada, editable, por volumen nominal**, puede usar **uno o varios SV** y **no exige** una relación **física lote-a-lote**.
6. El **registro de etiquetas procesadas** y la **consolidación** pueden ocurrir en **distinto orden temporal**; el sistema **controla pendientes y alerta**, **sin bloquear** la operación normal.
7. Mantener la distinción entre: (a) **saldo físico** en `stock.quant`; (b) **saldo documental pendiente de consolidación**; (c) **productos procesados pendientes de imputar**; (d) **productos procesados ya imputados/consolidados**.
8. Esta decisión **complementa AD-87, AD-88 y AD-89**; **no cambia el alcance actual de I1** ni **implementa todavía I2**.

**Relación con AD-87/AD-88/AD-89.** **Complementa AD-87** (la **imputación declarada** etiqueta→SV es el mecanismo de consolidación; sin genealogía física), **precisa AD-88** (la **coexistencia** de SV y etiquetas procesadas —y su distinto orden temporal— es **operación normal**: advierte y audita, **no bloquea**) y **se apoya en AD-89** (el **saldo físico** sigue siendo `stock.quant` + ubicaciones internas `Procesadores/<X>`, en **dos niveles**). Detalle: `19` §2, §3, §5.4, §7.3, §16.

**Impacto.** Aclara que `Procesadores/<X>` es **custodia operativa** (no consignación ni propiedad de terceros); fija el término **«pendiente de consolidación documental»**; **separa** explícitamente las **cuatro categorías de saldo** y habilita la **coexistencia temporal** de SV y etiquetas procesadas. Es **base semántica** de **I2** (consolidación/imputación documental), que **sigue pendiente**.

**No objetivos.** No crea modelos, vistas, ACL ni migraciones; **no implementa I2** ni modifica el alcance de **I1**; no altera costeo, valorización, facturación ni el ledger SV vigente; no migra datos históricos.

**Criterios de aceptación documentales.**
- `19_IMPUTACION_SV_Y_PROCESADORES.md` integra la semántica en glosario, ciclo operativo, reglas de ubicación/procesador y de saldo.
- Se distinguen explícitamente las **cuatro categorías de saldo** y los **dos órdenes temporales** válidos (etiquetas→consolidación y consolidación→etiquetas).
- **I2** permanece **pendiente** (no declarado como implementado).
- Sin contradicciones abiertas con AD-82/AD-83/AD-84/AD-87/AD-88/AD-89.

**Riesgos.** (R-19-05) confundir la **custodia operativa** con **consignación/propiedad ajena**; confundir **saldo físico** (`stock.quant`) con **saldo documental pendiente**; que la **coexistencia** de SV y etiquetas sin consolidar se interprete como error y se **bloquee** (mitigado por AD-88).

**Preguntas abiertas.** Se mantienen Q-19-3, Q-19-4, Q-19-6 y Q-19-7 (`19` §17); esta decisión **no** decide tolerancias, umbrales de alerta, retorno a granel sin etiquetas ni el paso `parent_lot_id` opcional (I6).

**Evidencia:** `19_IMPUTACION_SV_Y_PROCESADORES.md` (§2, §3, §5.4, §7.3, §16); **AD-87**, **AD-88**, **AD-89**; `05_BACKLOG.md` (decisiones post-I1 y refinamiento de I2); `18_CONSOLIDACION_Y_REBAJA.md` §7.5.

---

### AD-91 (2026-10-02) — Modelo documental de imputación SV por guía procesada (I2)

> **Estado: ✅ APROBADA (decisiones del usuario D-I2-11..D-I2-19 del 2026-10-02).** Fija el **alcance documental** de la fase **I2**: la **consolidación/imputación declarada** etiqueta→SV se materializa en un **modelo documental aditivo** y **sin efecto en stock**. **Prevalencia:** esta AD **prevalece** sobre `19` §4.3/§5.3/§7.3 en todo lo relativo al **alcance de I2** (efecto físico, saldo `sv_available_m3` e idempotencia), y **complementa** AD-87/AD-88/AD-89/AD-90. Norma: `19_IMPUTACION_SV_Y_PROCESADORES.md` §2, §4, §5, §6, §7, §13.2, §16. **No autoriza cambios de código, datos, parámetros, vistas, ACL ni migraciones** en esta pasada (documental).

**Contexto.** AD-87 especificó la imputación como **vínculo oficial** etiqueta→SV y su **efecto físico** (ledger `imputacion` + salida nativa del quant del SV). La **investigación I2** documentó tres contradicciones (**C-1**, **C-2**, **C-3**) entre ese diseño y el reparto de fases de §16: (C-1) el **efecto físico** se atribuía a **I2**; (C-2) `sv_available_m3` absorbía las **imputaciones** mezclándose con el **saldo documental**; (C-3) la **idempotencia** dependía de `picking_id` y la **severidad** no distinguía **etiqueta-side** de **SV-side**. El usuario **acota I2 a lo documental** y **reasigna** el efecto físico a **I3**, el costo a **I5** y la merma/cierre a fases **posteriores**.

**Decisión.**
1. **D-I2-11 — Modelo documental aditivo.** Se adopta la **Alternativa A**: modelos nuevos `madenat.sv.imputation`, `madenat.sv.imputation.line` y `madenat.sv.imputation.sv.line`. **No** se extiende el **ledger actual** (`madenat.sv.operation`) como **cabecera**.
2. **D-I2-12 — I2 no toca stock.** I2 **no** modifica `stock.quant`, `stock.picking` ni `stock.move`, y **no** genera **salida nativa**. **No** se añade `action_type='imputacion'` al ledger SV y **no** se altera `_sv_balance_values`/`sv_available_m3` en I2.
3. **D-I2-13 — Saldo documental propio.** El **saldo documental de consolidación** se calcula **exclusivamente** desde **imputaciones activas/aplicadas no revertidas** del **modelo nuevo**. Es **distinto** de: (a) **saldo físico** (`stock.quant`); (b) **`sv_available_m3`** del ledger vigente; (c) **merma documental**, que **no** se registra automáticamente.
4. **D-I2-14 — Ubicación del módulo.** I2 vive en **`madenat_lumber_logistics`**. **Depende de I1**: procesador, `processor_location_id`, saldo físico y ubicación interna. Consume `stock.lot` y `madenat.guia.processing` existentes **sin moverlos de core**.
5. **D-I2-15 — Organización por guía de procesados.** (a) una guía puede contener **muchas etiquetas**; (b) una etiqueta puede **distribuir** su **volumen nominal editable** entre **varios SV**; (c) un SV puede intervenir en imputaciones de **varias guías**; (d) una guía solo puede tener **una** imputación de trabajo **`draft`/`pending`**; (e) las imputaciones **`applied`/`reversed`** quedan como **historia**; (f) una imputación **`applied` es inmutable**: se corrige con **reversa + nueva imputación**, nunca editando ni borrando historia.
6. **D-I2-16 — Integridad.** (a) **duro (etiqueta-side):** una **etiqueta** no puede exceder su **volumen nominal editable** al sumar imputaciones activas/aplicadas no revertidas; (b) **blando (SV-side):** un **SV** puede superar su **saldo documental disponible**; se **advierte**, se **exige motivo** y se **audita `deviation`**, pero **se permite aplicar**; (c) **no** se inventan tolerancias ni reglas `AL-01..AL-07` en I2.
7. **D-I2-17 — Idempotencia.** Clave **documental propia**; **no** se usa `picking_id`. El reintento **no duplica** cabecera, líneas, auditorías ni consumo documental.
8. **D-I2-18 — Costos fuera de I2.** Los costos corresponden a **I5**: **no** se crean campos de costo, reglas de prorrateo ni `stock.lot.cost.line` ahora.
9. **D-I2-19 — Saldo SV abierto.** **No** se registra **merma automática**. **Cierre, regularización o merma explícita** son **fases posteriores**.

**Alcance (I2 documental).** Modelos `madenat.sv.imputation` + `.line` + `.sv.line`; cabecera **por guía** (`guia_processing_id`) con **una** imputación de trabajo `draft`/`pending` por guía; estados `draft`/`pending`/`applied`/`reversed`/`cancelled`; reparto **N:M** etiqueta↔SV con **volumen nominal editable**; regla **dura** etiqueta-side y **blanda** SV-side (motivo + `deviation`); **idempotencia** por clave documental propia; **inmutabilidad** de `applied` con **reversa + nueva**; **saldo documental** derivado de imputaciones activas/aplicadas no revertidas.

**No alcance.** Sin efecto en `stock.quant`/`stock.move`/`stock.picking`; sin salida nativa; sin `action_type='imputacion'` ni cambios en `_sv_balance_values`/`sv_available_m3`; sin costo (`cost_per_m3_usd`/`stock.lot.cost.line`/prorrateo) — **I5**; sin merma automática, cierre ni regularización — fases **posteriores**; sin genealogía (`parent_lot_id` opcional sigue en **I6**); sin migración de datos históricos; sin modelos, vistas, ACL ni migraciones en esta pasada documental.

**Invariantes (documentales, I2).**
1. Una **etiqueta** no excede su **volumen nominal editable** (Σ imputaciones activas/aplicadas no revertidas) — **duro**.
2. Un **SV** puede exceder su **saldo documental disponible** con **advertencia + motivo + `deviation`** — **blando**, permite aplicar.
3. **Una** imputación de trabajo (`draft`/`pending`) por **guía**.
4. La imputación **`applied` es inmutable**; toda corrección es **reversa + nueva imputación**.
5. La **idempotencia** usa **clave documental propia** (no `picking_id`); el reintento **no duplica**.
6. El **saldo documental de consolidación** se computa **solo** desde imputaciones activas/aplicadas **no revertidas** del modelo nuevo, y es **distinto** de `stock.quant` y de `sv_available_m3`.
7. **Sin** efecto en stock y **sin** merma automática en I2.

**Estados I2 y reserva documental temporal de etiqueta (precisión aditiva, 2026-10-02).** Se distinguen **dos conceptos** que no deben confundirse:
- **(a) Reserva documental temporal de capacidad nominal de etiqueta** — cuenta con `I2_ACTIVE_STATES = ('draft', 'pending', 'applied')`. Materializa el **techo DURO** por etiqueta: mientras exista un trabajo `draft`/`pending` o una imputación `applied` no revertida, la suma de volúmenes nominales de esa etiqueta no puede exceder su **volumen nominal editable**. `draft`/`pending` **reservan** capacidad documental **temporalmente** —previenen que dos trabajos paralelos sobre-imputen la misma etiqueta— sin producir efecto alguno.
- **(b) Saldo documental aplicado de SV** — cuenta con `I2_DOCUMENTAL_STATES = ('applied',)`. Solo las imputaciones **`applied`** consolidan el saldo documental del SV; `draft`/`pending` **no** lo consolidan (solo reservan la capacidad nominal de la etiqueta). La alerta **blanda** de exceso SV-side (`19` §7.2) evalúa el compromiso en estados **activos** como advertencia temprana.

`reversed`/`cancelled` **no** cuentan para ninguno de los dos conceptos. `draft`/`pending` **no** mueven stock, **no** alteran `sv_available_m3`, **no** modifican el ledger y **no** crean reserva física ni descuento documental del SV (el descuento del SV, si corresponde, es **I3**). `pending` deja el trabajo **preparado** y **mantiene la reserva documental temporal de la etiqueta** hasta **aplicar**, **cancelar** o **reversar** según corresponda. **Sin cambio funcional.**

**Relación con AD-87/AD-88/AD-89/AD-90.** **AD-87** define el **modelo objetivo** (imputación declarada etiqueta→SV, sin genealogía); **AD-91 acota la fase I2 a lo documental** y **reasigna el efecto físico** (ledger + salida nativa) a **I3**. **AD-88** rige la **severidad blanda** (advertir, motivar, auditar); **AD-91 precisa** que en I2 la severidad es **dura solo etiqueta-side** y **blanda SV-side**. **AD-89** aporta el **saldo físico** (`stock.quant` + `Procesadores/<X>`, sin modelo persistente) y **AD-90** la **semántica** de custodia operativa y las **cuatro categorías de saldo**; **AD-91 añade** el **saldo documental** como categoría **propia y computada**. Prevalencia: **AD-91 prevalece sobre `19` §4.3/§5.3/§7.3** en el **alcance de I2**; AD-87/AD-89/AD-90 permanecen vigentes para el modelo objetivo y las fundaciones.

**Impacto.** Fija **I2 como documental sin efecto en stock**; **separa** `stock.quant` (físico), `sv_available_m3` (ledger, **intacto en I2**) y **saldo documental** (modelo nuevo); habilita **cabecera por guía**, **inmutabilidad/reversa** e **idempotencia documental**; confirma **costo en I5** y **merma/cierre posterior**.

**Riesgos.** (R-19-04) imputación declarada sin evidencia física (por diseño; mitigado por motivo + auditoría). (R-19-06) exceso de volumen: **duro** etiqueta-side, **blando** SV-side. Confundir las **tres fuentes de saldo** (físico / `sv_available_m3` / documental). Reabrir historia **aplicada** en lugar de **reversar**. Duplicación por reintento si la **clave documental** no es estable.

**Criterios de aceptación documentales.**
- `19` §4/§5/§6/§7/§13.2/§16 declaran **I2 documental sin efecto en stock** y la **salida nativa/ledger en I3**.
- Se distinguen **saldo físico**, **`sv_available_m3`** y **saldo documental** (computado del modelo nuevo).
- **C-1/C-2/C-3** resueltas y registradas en `19` §13.2 (prevalencia explícita, sin borrar historia).
- **I2 permanece PENDIENTE**; sin contradicciones abiertas con AD-87..AD-90.

**Evidencia:** `19_IMPUTACION_SV_Y_PROCESADORES.md` (§2, §4, §5, §6, §7, §13.2, §16); **AD-87**, **AD-88**, **AD-89**, **AD-90**; `05_BACKLOG.md` (I2 con alcance cerrado); evidencia de código de `19` §18 (`madenat_sv_operation.py`, `stock_lot.py`, `madenat_guia_processing.py`, `res_partner.py`).

---

---

## 2026-10-05 — Entrega 1: Rolleo centrado en Embarque

### AD-92 (2026-10-05) — Rolleo centrado en Embarque

**Estado:** ✅ IMPLEMENTADO (Entrega 1 — Operación Física y Logística). Módulos
afectados: `madenat_lumber_logistics`, `madenat_lumber_shipping_core`.

**Decisión.** El rolleo marítimo se inicia desde un **Embarque individual**
(`lumber.export.shipment`) y reasigna **solamente** la planificación marítima de
ese Embarque a una **Motonave** destino y, cuando aplique, a un **Viaje** destino.
El asistente `lumber.vessel.rollover.wizard` recibe `shipment_id` **obligatorio**;
`origin_vessel_id`/`origin_voyage_id` son **derivados** (sólo lectura) del Embarque.
El punto de entrada operativo es `Logística Exportación → Embarques → (abrir Embarque)
→ «Rollover de Embarque»` (`action_open_shipment_rollover_wizard`).

**Motivo.** Una Motonave (`shipping.vessel`) es un **maestro histórico reutilizable**
(muchos viajes y Embarques de meses distintos); no constituye por sí misma una salida
concreta ni un **conjunto seguro de cargas afectadas**. El asistente previo (Fase C,
2026-10-04) operaba por Motonave origen (+ Viaje opcional) y reasignaba **en masa**
todos los Embarques planificables del alcance, con riesgo de incluir Embarques que no
pertenecían al incidente operativo.

**Invariantes.**
1. La unidad de negocio es **exactamente un** Embarque.
2. Sólo se escriben `shipment.vessel_id` y `shipment.voyage_id`.
3. No modifica stock, lotes, quants, movimientos, pickings, contenedores (como
   pertenencia), costos, Rebaja, Zarpe, B-01, R1, R2, Entrega ni finanzas.
4. No altera **otros** Embarques ni Embarques históricos.
5. No opera post-zarpe (sólo `draft`/`confirmed`; `in_transit`/`delivered`/`cancelled`
   bloqueados en UI y en servidor).
6. Conserva origen, destino, motivo, observación, actor y fecha; mantiene **auditoría
   SHA-256** (`vessel_rollover` maestro + `vessel_rollover_item`) y **chatter**.
7. Genera un pendiente **documental NO bloqueante** reutilizando `lumber.shipment.document`
   (sin crear tipos maestros, modelos ni migraciones).
8. Modo `strict`: una exclusión (Embarque o cualquiera de sus Contenedores bloqueado)
   aborta la operación sin cambios (atomicidad).

**Consecuencia.** El acceso desde Motonave se **depreca como ejecución**: el botón de la
ficha de `shipping.vessel` pasa a ser **consulta** (`action_open_vessel_shipments` → abre
la lista de Embarques filtrada por esa Motonave). No se ejecuta reasignación masiva desde
Motonave. El Rolleo de Contenedor (`lumber.container.rollover.wizard`) es un flujo
**independiente** y no fue modificado.

**Evidencia.** `madenat_lumber_logistics/wizards/lumber_vessel_rollover_wizard.py`
(`_scope_shipments` = `self.shipment_id`; `_ensure_documentary_backlog`);
`madenat_lumber_logistics/views/lumber_export_shipment_views.xml` (botón «Rollover de
Embarque»); `madenat_lumber_shipping_core/models/shipping_vessel.py`
(`action_open_vessel_shipments`); pruebas `test_vessel_rollover.py` (RL-01..RL-23).

---

## 2026-10-05 — Entrega 1: Borrador Seguro autónomo

### AD-93 (2026-10-05) — Borrador Seguro autónomo

**Estado:** ✅ IMPLEMENTADO (Entrega 1 — Operación Física y Logística).
Módulos afectados: `madenat_lumber_logistics`, `madenat_lumber_core`.

**Decisión.** El retorno de un Embarque desde `confirmed` a `draft` se permite
**sólo** cuando no existe evidencia física/histórica de salida, viaje terminal ni
cierre financiero. Sólo Jefatura de Operaciones y Gerencia pueden ejecutarlo. La
única escritura es `{'state': 'draft', 'actual_departure': False}`.

**No depende** de `b01_exception_state`, R1 ni R2.

**Motivo.** Permite versionar y operar el gate sin acoplarlo a sub-bloques
posteriores de Zarpe/B-01/regularización.

**Invariantes.**
1. No altera stock/lotes/pickings/movimientos ni `stock.quant`.
2. No deshace rebajas ni zarpes.
3. No toca documentos/backlog.
4. No toca costos/facturas/pagos.
5. Auditoría SHA-256 (`shipment_return_to_draft`) + chatter; no borra auditoría previa.
6. Guard server-side contra RPC/context: `write({'state':'draft'})` exige un token
   efímero de proceso acuñado sólo por `action_draft()`.

**Evidencia.** `madenat_lumber_logistics/models/lumber_export_shipment.py`
(`action_draft`, `_assert_can_return_to_draft`, `_return_to_draft_evidence`,
`_assert_draft_write_authorized`, `_return_to_draft_snapshot`,
`_audit_return_to_draft`); `views/lumber_export_shipment_views.xml` (botón
«Volver a Borrador»); `madenat_lumber_core/models/madenat_audit_log.py`
(`shipment_return_to_draft` = «Retorno Seguro a Borrador»); pruebas
`test_shipment_return_to_draft.py` (T-D1..T-D22 / BSD-01..BSD-13).

---

## 2026-10-05 — Entrega 1: Zarpe con excepción B-01

### AD-94 (2026-10-05) — Zarpe con excepción B-01 bloqueante

**Estado:** IMPLEMENTADO. Módulos: `madenat_lumber_logistics`,
`madenat_lumber_core`.

**Decisión.** Un Embarque puede zarpar de `confirmed` a `in_transit`. Si existen
Contenedores pendientes de rebaja física, puede hacerlo **sólo** mediante
excepción **B-01 `open`**, con motivo (≥ 20 caracteres), actor, fecha y
evidencia auditada.

**B-01:**
- **no** rebaja stock;
- **no** modifica lotes/movimientos/quants/pickings;
- **no** crea costos/facturas/pagos;
- mantiene los pendientes en su **estado físico real** (nunca `shipped`/
  `rebajado`);
- **bloquea la Entrega** mientras esté `open` (`_b01_blocks_delivery()`);
- **R1/R4** se definen **después** y **no** pertenecen a AD-94.

**Invariantes.**
1. El Zarpe puro **no** ejecuta Rebaja (`_set_in_transit` no mueve stock; sólo
   `state` + `actual_departure` y marca `shipped` los ya físicamente rebajados).
2. La Rebaja es un flujo **separado** (`_rebajar_container`).
3. B-01 **no** oculta el Backlog Documental (no es gate de Zarpe/B-01).
4. Los campos B-01 están protegidos server-side por **token de proceso**
   (`_B01_WRITE_TOKENS`, no falsificable por `with_context`/RPC).
5. Snapshot determinista **SHA-256** (`b01_departure_exception`) y chatter
   obligatorios.
6. Clasificador **local** de rebaja física (sin dependencia de R2/retornos).

**Evidencia.** `madenat_lumber_logistics/models/lumber_export_shipment.py`
(`action_set_in_transit`, `_set_in_transit`, `_assert_departure_context`,
`_classify_departure_containers`, `_container_rebaja_classification`,
`_b01_snapshot`, `_create_b01_exception_audit`);
`wizards/lumber_shipment_zarpe_wizard.py`;
`madenat_lumber_core/models/madenat_audit_log.py`
(`b01_departure_exception` = «Zarpe con excepción B-01»); pruebas
`test_shipment_b01_exception.py` (T-B01-1..T-B01-17 / ZB-01..ZB-15).

---

## 2026-10-05 — Entrega 2: Regularización y cierre B-01 (R1/R4)

### AD-95 (2026-10-05) — R1: regularización física extemporánea de B-01

**Estado:** IMPLEMENTADO. Módulos: `madenat_lumber_logistics`,
`madenat_lumber_core`.

**Propósito.** Cerrar la brecha física de una excepción **B-01 `open`**: ejecutar
la **rebaja** que faltaba al zarpe, con **fecha efectiva actual** (no
retroactiva), dejando evidencia auditada. **R1 no cierra la excepción.**

**Roles.** Sólo **Gerencia** abre y confirma R1 (guard de servidor + ACL del
asistente). Operaciones/Jefatura/Auditoría pueden visualizar, no confirmar.

**Invariantes.**
1. Sólo Embarque `in_transit` con **B-01 `open`**; sólo Contenedores
   **pendientes elegibles** del propio Embarque (`loaded`/`sealed`, con stock),
   sin rebaja física previa.
2. Motivo y aprobación ≥ 20 caracteres.
3. Usa el **motor nativo de Rebaja** (`_rebajar_container`: `stock.picking` OUT ·
   `stock.move`/`stock.move.line` · lote real · `button_validate`);
   **savepoint por Contenedor** y **rollback total** ante cualquier fallo (sin
   rebaja parcial).
4. **No** cambia `shipment.state` ni `actual_departure` (no retrofecha el Zarpe).
5. **No** cierra B-01 (`open` permanece); **no** entrega; **no** crea
   costos/facturas/pagos.
6. Registra `b01_regularization` (snapshot determinista **SHA-256** + chatter).

**Separación.** **R1 ≠ R2**: R1 es rebaja extemporánea; R2 es el **retorno físico
total** de la reversa. R1 no usa retorno ni `origin_returned_move_id`.

**Evidencia.** `lumber_export_shipment.py` (`_create_b01_regularization_audit`,
`_b01_regularization_snapshot`, `_b01_regularization_container_snapshot`,
`action_open_b01_regularization_wizard`); `lumber_container.py`
(`_assert_can_regularize_b01_rebaja`); `wizards/lumber_b01_regularization_wizard.py`;
`madenat_lumber_core/models/madenat_audit_log.py` (`b01_regularization`); pruebas
`test_b01_regularization.py` (T-R1-1..9).

### AD-96 (2026-10-05) — R4: cierre administrativo de B-01

**Estado:** IMPLEMENTADO. Módulo: `madenat_lumber_logistics`.

**Propósito.** Cerrar administrativamente la excepción **open → resolved**
**después** de que R1 dejó evidencia suficiente. **R4 no genera Rebaja ni stock.**

**Roles.** Sólo **Gerencia**.

**Invariantes.**
1. Sólo `in_transit` con B-01 `open`; exige **cero pendientes** y **al menos una
   auditoría `b01_regularization`** (evidencia R1).
2. Sólo escribe `b01_exception_state='resolved'`, `b01_exception_resolved_at`,
   `b01_exception_resolved_by_id`, `b01_exception_resolution_audit_id`.
3. **No** toca stock/lote/move/move line/picking/quant/Contenedores; **no**
   cambia `state` ni `actual_departure`; **no** ejecuta Rebaja; **no** crea
   costos/facturas/pagos.
4. Registra `b01_resolution` (snapshot determinista **SHA-256** + chatter).
5. **Idempotente** (reintento bloqueado); `write` directo y `with_context(...)`
   falsos bloqueados por **token de proceso** (`_B01_RESOLVE_TOKENS`, no
   falsificable por RPC).
6. **Libera sólo** el gate B-01 de la Entrega (`_b01_blocks_delivery()`);
   **Backlog** y demás gates se conservan. **R4 ≠ Entrega.**

**Evidencia.** `lumber_export_shipment.py` (`_assert_can_resolve_b01_exception`,
`_b01_resolution_snapshot`, `_create_b01_resolution_audit`,
`action_resolve_b01_exception`, `_assert_b01_write_authorized`);
`madenat_lumber_core/models/madenat_audit_log.py` (`b01_resolution`); pruebas
`test_b01_regularization.py` (T-R4-1..12).

**No alcance.** Sin R2 (retorno físico), sin Entrega, sin Costeo/Billing/Pagos y
sin Backlog como feature. El cierre de R4 se apoya en **Rebaja aplicada**, nunca
en retorno.

---

## 2026-10-05 — Entrega 3: Retorno físico total de Rebaja (R2)

### AD-97 (2026-10-05) — R2: retorno físico total de Rebaja

**Estado:** IMPLEMENTADO. Módulos: `madenat_lumber_logistics`,
`madenat_lumber_core`.

**Propósito.** Anular FÍSICAMENTE una **Rebaja** ya ejecutada, restaurando el
material al **inventario interno de origen** con trazabilidad completa, mediante
un **retorno físico TOTAL** (nunca por escritura directa de stock).

**Roles.** Sólo **Gerencia** (guard `_assert_can_reverse_rebaja_total`).
Operaciones, Jefatura, Auditoría y Contabilidad → `AccessError` (Δ0).

**Invariantes.**
1. Sólo Contenedor **rebajado** con OUT (`rebaja_picking_id`) `done`, moves,
   move lines y lotes íntegros, destino **Clientes**, y sin retorno total previo.
2. **Motor físico de retorno** (no `_rebajar_container`): picking IN con
   `return_id = OUT.id`, `origin = "Return of <OUT>"`, un `stock.move` por move
   OUT con `origin_returned_move_id` y cantidad exacta, y `stock.move.line` por
   lote real; exigir `return_picking.state == 'done'`.
3. **Totalidad obligatoria** (lotes/cantidades exactos; sin parciales ni
   sobre-retorno) — verificada DESPUÉS de la validación.
4. **Lock** por Contenedor (`SELECT … FOR UPDATE NOWAIT`) + transacción lógica
   única; cualquier fallo ⇒ **rollback total** (sin picking `done` parcial, sin
   enlaces parciales, sin estados/auditoría/chatter).
5. **Idempotencia relacional** (`origin_returned_move_id` / `return_id`): si el
   retorno total ya existe → **no-op** (sin segundo retorno/auditoría/SV).
6. **Clasificación** `none | active | compensated | inconsistent`;
   `_assert_no_rebaja_inconsistency()` bloquea Zarpe/Entrega/Waiver si hay
   `inconsistent`.
7. **B-01:** `open` bloquea R2 (incluso Gerencia); `resolved` exige Gerencia +
   motivo ≥ 20. R2 **no** escribe campos B-01 ni crea `b01_regularization`/
   `b01_resolution` (sólo los lee en el snapshot).
8. **Auditoría** `rebaja_return_total` (SHA-256) + chatter. **No** Entrega, **no**
   Costeo/Billing/Pagos; interacción SV limitada a `sv_reverse_allocation` de la
   rebaja de asignación.

**Separación.** **R1 ≠ R2** (R1 = rebaja tardía; R2 = retorno físico total).
**R2 ≠ R4** (R2 no cierra B-01). **R2 ≠ Entrega**.

**Evidencia.** `lumber_container.py` (motor + guards + snapshot/audit);
`lumber_export_shipment.py` (`_container_rebaja_classification`,
`_assert_no_rebaja_inconsistency`); `wizards/lumber_container_rebaja_reverse_wizard.py`;
`madenat_lumber_core/models/madenat_audit_log.py` (`rebaja_return_total`);
`tests/test_rebaja_return_total.py` (T-R2-1..13).

---

## 2026-10-05 — Entrega 4: Entrega Segura de Embarque (D2)

### AD-98 (2026-10-05) — Entrega Segura de Embarque (D2)

**Estado:** IMPLEMENTADO. Módulos: `madenat_lumber_logistics`,
`madenat_lumber_core`.

**Propósito.** La **Entrega** es un **hito LOGÍSTICO** (`in_transit →
delivered`). NO es un cierre financiero ni físico.

**Roles.** Sólo **Jefatura de Operaciones** y **Gerencia** (guard
`_assert_delivery_group`, `DELIVERY_GROUPS`).

**Invariantes.**
1. Única transición `in_transit → delivered`; `delivered` bloquea repetición;
   write/create directos bloqueados por **token de proceso**
   (`_DELIVERY_WRITE_TOKENS`, no falsificable por `with_context`/RPC).
2. **B-01:** `open` bloquea; `none`/`resolved` permiten. D2 **no** escribe campos
   B-01 ni crea `b01_regularization`/`b01_resolution` (sólo lectura).
3. **R2:** `inconsistent` bloquea; `compensated` permite; un Contenedor
   físicamente pendiente bloquea. Clasificación R2 sólo lectura.
4. **Viaje terminal** (`cancel`/`departed`/`arrived`) bloquea.
5. **Documentación (B2):** evidencia **informativa**, no gate; se registra vía
   `_document_status_summary()`. **Sin waiver.**
6. Persiste `delivery_at`, `delivery_by_id` y `delivery_audit_id`.
7. **Auditoría** `shipment_delivery` (snapshot determinista **SHA-256**) +
   chatter.
8. **NO** mueve stock, **NO** ejecuta Rebaja/R2, **NO** crea Costeo/Billing/
   Pagos ni SV; **NO** cambia `actual_departure`, Motonave ni Viaje.

**Evidencia.** `lumber_export_shipment.py` (`action_deliver`,
`_assert_can_deliver`, `_assert_delivery_group`, `_delivery_snapshot`,
`_audit_delivery`, `_assert_delivery_write_authorized`);
`madenat_lumber_core/models/madenat_audit_log.py` (`shipment_delivery`);
`tests/test_shipment_delivery_safe.py` (T-D2-01..20).

**No alcance.** Sin stock, Rebaja, Retorno R2, Zarpe, Costeo, Billing, Pagos ni
SV; sin Backlog; sin waiver. **AD-99** queda reservado para C2.

---

## Nota técnica B2 (2026-10-05) — Fuente única de estado documental

**Estado:** IMPLEMENTADO (corrección técnica; **no** es una decisión nueva).
Módulo: `madenat_lumber_logistics`. **No crea AD nueva**; **AD-98 se reserva a
D2** (Entrega Segura).

**Motivo.** El cómputo de `document_status` estaba **duplicado** entre
`lumber_export_shipment.py` y `lumber_document_checklist.py`, con `Selection`
`pending/partial/complete`, y el compute efectivo escribía el valor
**inválido** `incomplete` (fuera del `Selection`). B2 fija una **fuente única**
y elimina el defecto.

**Decisión técnica.**
1. `document_status` pasa a `not_configured | missing | pending | partial |
   attached | verified` (informativo; se eliminan `complete`/`incomplete`).
2. El único compute es `lumber_document_checklist.py::_compute_document_status`
   (documentos con `checklist_id.active`; universo = requeridos activos; si no
   hay requeridos, todos los activos).
3. Se añaden contadores almacenados `document_verified_count`,
   `document_missing_count`, `document_pending_count`; se conserva
   `document_completion`.
4. Se elimina del Embarque el compute duplicado y el método muerto
   (`_compute_document_completion`, `_compute_document_status`).
5. `lumber.shipment.document.state` pasa a `readonly=False` para que el estado
   `verified` sea alcanzable con las ACL actuales (sin ACL nuevas).

**Invariantes.**
- **Nunca** es gate de operación física (rebaja/zarpe/B-01/R1/R2/Entrega).
- **D2** (futuro) consumirá el resumen B2 (`_document_status_summary`) **sólo**
  para auditoría informativa.
- El **Backlog** documental conserva su workflow separado.
- No toca stock, costeo, B-01, R1/R2/R4, D2 ni menús P2.

**Evidencia.** `lumber_document_checklist.py` (`_compute_document_status`);
`lumber_export_shipment.py` (`document_status`, contadores,
`_document_status_summary`); `tests/test_document_status_b2.py` (T-B2-01..11).

---

## 2026-10-05 — Backlog Documental No Bloqueante

### AD-100 (2026-10-05) — Backlog Documental No Bloqueante

**Estado:** IMPLEMENTADO. Módulos: `madenat_lumber_logistics`,
`madenat_lumber_core`.

**Propósito.** El **Backlog Documental** gestiona **trabajo pendiente
documental** sobre `lumber.shipment.document`. **NO** es gate físico ni
financiero: no bloquea la operación ni D2, no cambia B2 y no toca
stock/B-01/R1/R2/R4/Costeo/Billing/Pagos/SV.

**Estados.** `open → in_progress → completed` (o `waived`, estado terminal
alternativo).

**Roles.**
1. **Operaciones** gestiona datos: `criticality`, `responsible_id`,
   `due_date`, `backlog_note`.
2. **Jefatura de Operaciones** y **Gerencia** **escalan** (`open →
   in_progress`; sello `escalated_at`/`escalated_by_id`).
3. **Gerencia** **cierra** (`→ completed`) o **exonera** (`→ waived`).

**Invariantes.**
1. **Guard server-side** por rol (`_assert_backlog_operations_group`,
   `_assert_backlog_escalate_group`, `_assert_backlog_close_group`); falta de
   permiso ⇒ `AccessError`. `backlog_state`, `escalated_at` y `escalated_by_id`
   son campos de **workflow**: su write directo se bloquea (`UserError`).
2. **Token de proceso anti-RPC** (`_BACKLOG_ESCALATE_TOKENS`,
   `_BACKLOG_CLOSE_TOKENS`, `_BACKLOG_WAIVE_TOKENS`; clave
   `(dbname, uid, document_id)`), no eludible por `with_context`. El
   superusuario (`env.su`, código interno/tests) conserva la vía de escape
   estándar (patrón MADENAT).
3. **Idempotencia:** `completed`/`waived` son no-op; `in_progress` no reescribe
   `escalated_*`; un no-op no genera auditoría ni chatter.
4. **Exoneración:** motivo obligatorio (>= 20 caracteres tras `strip()`),
   tomado de `backlog_note`; `completed` no se exonera (`UserError`); la nota
   previa se **conserva** y el motivo se anexa de forma trazable.
5. **Auditoría** `documentary_backlog_escalation`/`_completion`/`_waiver`
   (snapshot determinista **SHA-256**) + **chatter**. Rollback total si falla
   la creación de auditoría o el write (savepoint).
6. **B2 se lee, no se escribe:** el snapshot registra `document_status` como
   evidencia; nunca se escriben `document_status`/`document_completion` ni los
   contadores.
7. **D2 no se bloquea ni se altera:** el backlog no invoca `action_deliver` ni
   toca `state`, `actual_departure`, viaje/motonave, B-01 ni campos `delivery_*`.
8. **Sin** stock, B-01, R1/R2/R4, Costeo, Billing, Pagos ni SV.

**Evidencia.** `madenat_lumber_logistics/models/lumber_document_checklist.py`
(`write`, `_assert_backlog_*`, `action_backlog_escalate`,
`action_backlog_complete`, `action_backlog_waive`, `_backlog_snapshot`,
`_create_backlog_audit`, `_backlog_message_post`);
`views/lumber_document_checklist_views.xml` (botones Escalar/Cerrar/Exonerar);
`madenat_lumber_core/models/madenat_audit_log.py` (nuevos `action_type`);
`tests/test_documentary_backlog.py` (T-DOC-1..6 + BL-01..BL-18).

**No alcance.** Sin stock, Rebaja, Retorno R2, Zarpe, B-01, R1/R2/R4, Costeo,
Billing, Pagos ni SV; sin wizards nuevos; sin menús P2 ni vistas D2/B2.
**AD-99 queda reservado para C2.**

---

## 2026-10-07 — Búsqueda, filtros y agrupaciones de la Consola de Intake

### AD-101 (2026-10-07) — Búsqueda, filtros y agrupaciones de la Consola de Intake

**Estado:** IMPLEMENTADO y APLICADO en `madenat_test` (módulo `madenat_lumber_intake`,
18.0.0.11.0). **No** desplegado a producción.

**Contexto.** La vista de búsqueda de la Consola de Ingreso de Madera
(`madenat.lumber.intake.console`) presentaba: (a) una columna/etiqueta «OC documento»
que mostraba `COALESCE(po.name, oc_reference_raw)` (Procesado) / `purchase_order` (Producto)
—mezcla con la OC vinculada— y una agrupación «OC» que agrupaba por `purchase_id`, vacío en
las filas reales ⇒ **un único grupo vacío**; (b) una «Fecha» con semántica mixta
(emisión/recepción) sin distinción visible; (c) ausencia de filtros/agrupaciones para
**producto real** y **procesador**.

**Decisión.**
1. **OC documental vs OC vinculada.** Se expone la columna real `oc_documental`
   (`NULLIF(<origen>.oc_reference_raw,'')`; referencia documental pura, nunca sustituida por
   el nombre de la OC vinculada), separada de `purchase_id` (OC vinculada). Columna,
   búsqueda y agrupaciones **«OC documental»** y **«OC vinculada»**; filtros **OC vinculada**,
   **OC pendiente de vinculación** y **OC no indicada**. `purchase_reference` y los proxies
   previos se **conservan** por compatibilidad (no se reescriben ni eliminan).
2. **Fecha.** Se añade `guide_date_kind` (`emission` / `reception`) y la columna «Origen fecha»;
   `guide_date` **no** cambia. Todas las filas **no** son emisión documental.
3. **Modalidades.** Producto/Procesado/Volúmenes por `ingestion_type` (dominios disjuntos, pero
   **NO** radio buttons: combinables por **AND**, dos modalidades ⇒ intersección vacía). Se añaden
   filtros de estado **«Procesada (legacy)»** y **«Error»**; **Abiertos/Finalizados no se amplían**.
4. **Producto real.** `product_filter_id` (campo de **solo búsqueda**) resuelve a las **líneas**
   de ambos orígenes (`lumber.reception.line.product_id` / `madenat.guia.processing.line.product_id`),
   **sin** JOIN en la vista SQL (no duplica filas), **sin** elegir el primer producto; **sin** agrupación.
5. **Procesador.** `processor_id` (columna real) proviene **exclusivamente** de
   `toll.processing.order.processor_id` vía `toll_order_id` (`LEFT JOIN` **1:1**); **nunca** el
   proveedor/emisor; vacío en Producto y sin orden toll.

**Invariantes.** `id` y `source_res_id` **intactos**; **sin** cambios en ACL, ingesta, stock,
costes ni contabilidad; **sin** `sudo`; **sin** normalizar ni fusionar referencias históricas de OC.

**No implementado (pendiente).** Búsqueda numérica de volumen (campo oficial identificado:
`official_volume_m3` / `official_volume_effective_m3`, m³); otros orígenes de procesador;
ampliación de Abiertos/Finalizados; **V3 (navegador)**; instalación en base limpia
(referencia hacia adelante preexistente en la vista de lista). Ver `05_BACKLOG.md`.

**Evidencia.** `00_ARQUITECTURA.md` §4.10; `03_TESTS.md` §11; código y pruebas en
`madenat_lumber_intake` (`models/intake_console.py`, `views/intake_console_views.xml`,
`tests/test_search_console_oc_fecha_modality.py`). Registros de aplicación (fuera de CANON):
`IMPL_BUSQUEDA_INTAKE_20261007/`, `APPLY_BUSQUEDA_INTAKE_20261007/`.

### AD-102 (2026-10-07) — Identificación no bloqueante de retorno de servicio + reglas de imputación (I2)

**Estado:** IMPLEMENTADO Y PROBADO EN **COPIA DE TRABAJO AISLADA**
(`IMPL_SERVICE_RETURN_AB_20261007/`, base `srvretab_test_20261007`) — **PENDIENTE DE APROBACIÓN**
para aplicar al entorno activo. Módulos: `madenat_lumber_core`, `madenat_lumber_intake`,
`madenat_lumber_logistics`. **No** se aplica al entorno activo ni a producción; **no** se modifican
datos históricos.

**Contexto.** El antecedente `IMPL_SERVICE_RETURN_20261006/` exigía la confirmación
(`service_return_confirmation`) **bloqueando** el envío a stock. La decisión vigente **separa
identificación de imputación**: la identificación es informativa y **no bloqueante**; la
imputación posterior **reutiliza el mecanismo SV (I2, AD-91)**.

**Decisión.**
1. **Campo** `service_return_confirmation` en `madenat.guia.processing`: Selection `yes`/`no`,
   **sin default**; *vacío* = **pendiente de identificación** (NO equivale a `no`).
2. **No bloqueante.** Se **elimina** el guard `_assert_service_return_confirmed` (la identificación
   **no** impide la ingesta ni el envío a stock). Se **conservan** íntegras las demás validaciones
   (permisos, dimensiones, producto, tipo de cambio, trazabilidad, protección anti-duplicado).
3. **Editable desde la Consola de Intake** por proxy no almacenado (compute + inverse) con el
   **usuario operativo** (Operaciones); la Guía es la propietaria del dato (no se duplica).
4. **Con imputaciones SV `applied`**, cambiar la identificación a «No» o vaciarla se **rechaza**
   (regla en `madenat_lumber_logistics`, donde existe el modelo I2); la corrección exige
   **reversar** primero las imputaciones. No se eliminan relaciones en silencio.
5. **Destino marcado «Sí» al APLICAR** (`action_apply`), **no** al guardar borrador/pendiente; **no**
   se marca la guía automáticamente.
6. **Relación inversa `sv_imputation_ids`** (One2many de solo lectura) + filtro **«Retornos sin
   imputación aplicada»** (no evalúa cobertura parcial). Residen en `madenat_lumber_logistics`
   (sin dependencia **core→logistics** ni circular).
7. **I2 intacto:** ninguna regla añade movimientos de stock, ledger (`action_type='imputacion'`,
   I3) ni costes (I5). Efectos de I2 = documentales (D-I2-12).

**Límites declarados.** El filtro «sin imputación aplicada» **no** detecta **cobertura parcial**.
I3/I5 no implementados. Verificación en **navegador** no realizada. No se crea módulo nuevo:
se reutiliza el mecanismo I2 existente.

**Evidencia.** `12_FLUJOS_INGESTA.md` §11.9; `19_IMPUTACION_SV_Y_PROCESADORES.md` §19.9;
`03_TESTS.md` §12; `05_BACKLOG.md`; `02_CONTINUIDAD.md` §17. Copia y pruebas (fuera de CANON) en
`IMPL_SERVICE_RETURN_AB_20261007/`.

<!-- actualizado: 2026-10-07 — alta AD-102 (identificación no bloqueante de retorno de servicio + reglas de imputación I2: destino «Sí» al aplicar, regla Sí→No con imputaciones aplicadas, relación inversa `sv_imputation_ids`, filtro «Retornos sin imputación aplicada»). Implementado/probado en copia aislada `IMPL_SERVICE_RETURN_AB_20261007/`; NO aplicado. Ver 12 §11.9, 19 §19.9, 03 §12, 05, 02 §17. Solo documentación. -->


<!-- actualizado: 2026-10-02 (4) — alta AD-90 (semántica de inventario en procesador y pendiente de consolidación documental). Complementa AD-87/AD-88/AD-89. Ver CANON/19 §2/§3/§5.4/§7.3/§16. Solo documentación. -->
<!-- actualizado: 2026-10-02 (6) — alta AD-91 (modelo documental de imputación SV por guía procesada, I2): modelos `madenat.sv.imputation`/`.line`/`.sv.line`; I2 sin efecto en stock; salida nativa + ledger a I3; tres saldos separados; cabecera por guía; inmutabilidad/reversa; idempotencia por clave documental propia (no `picking_id`); severidad dura etiqueta-side / blanda SV-side; costo I5; merma/cierre posterior. Resuelve C-1/C-2/C-3. Ver CANON/19 §2/§4/§5/§6/§7/§13.2/§16. Solo documentación. -->
<!-- actualizado: 2026-10-02 (7) — precisa en I2 la reserva documental temporal de capacidad nominal de etiqueta (I2_ACTIVE_STATES: draft/pending/applied, techo duro) frente al saldo documental aplicado de SV (I2_DOCUMENTAL_STATES: applied); pending mantiene la reserva temporal hasta aplicar/cancelar/reversar; sin cambio funcional. Ver CANON/19 §6/§7.3. Solo documentación. -->

### AD-103 (2026-10-12) — Jefatura de Operaciones puede eliminar `madenat.guia.processing` (higiene de la base)

**Decisión (autor: Mauricio, 2026-10-12).** El grupo **Jefatura de Operaciones** puede eliminar registros de
`madenat.guia.processing`, con el fin de **higiene de la base de datos y limpieza del sistema**.

**Alcance.** Aprueba que el permiso `unlink` de jefatura sobre ese modelo **exista como política** (el cambio de
ACL vive en el WIP de `madenat_lumber_core`/`madenat_lumber_intake`). **No** autoriza borrar ningún dato real en
esta fase ni modificar ACL/vistas/código en el marco de esta decisión.

**Condición (pendiente).** Guardas de integridad y trazabilidad **por decidir**; ficha de análisis y matriz de
escenarios en `AUDITORIA_INTEGRAL_20261012/fase2/docs/H_SEC_1_FICHA.md`.
**Estado:** permiso **aprobado**; guardas **pendientes**.

**Riesgo residual declarado.** Hasta que Mauricio apruebe las guardas, el cambio de ACL **NO** debe incluirse en
ningún despliegue al TEST remoto sin documentar expresamente el riesgo.

<!-- actualizado: 2026-10-12 (1) — alta AD-103 (jefatura puede eliminar `madenat.guia.processing` por higiene de la base; permiso como política, sin autorizar borrado de datos reales; guardas de integridad/trazabilidad PENDIENTES). Ver `AUDITORIA_INTEGRAL_20261012/fase2/docs/H_SEC_1_FICHA.md`. Solo documentación. -->

### AD-104 (2026-10-12) — Guardas de eliminación de guía (G1) y saneamiento de fixtures (G2)

**Decisiones aprobadas por Mauricio (FASE 3):**
- **D-G1.** Se **bloquea** el borrado si algún lote de la guía tiene `stock.quant`, movimientos, historial SV,
  imputaciones o return-links.
- **D-G2.** Los errores técnicos de FK se convierten en **mensajes de negocio** que sugieren **anular, corregir o
  revertir**.
- **D-G3.** Toda eliminación (**vía directa o asistente**) **exige motivo** y deja registro en
  `madenat.audit.log`.
- **D-G4.** El bloqueo de la bitácora (**H-SEC-5**) **NO** se implementa en esta fase.

**Implementación (mínima):** guarda **única** en `madenat.guia.processing.unlink()` (`madenat_lumber_core`
**18.0.6.7.0 → 18.0.6.8.0**): pre-chequeo `_guia_deletion_blockers`, motivo + bitácora (`_guia_log_deletion`) y
**borrado controlado de lotes vacíos** (sin huérfanos). El asistente (`madenat_lumber_intake`
**18.0.0.13.0 → 18.0.0.14.0**) comparte la guarda y **no duplica** la bitácora. Se **corrige** la fixture
`test_guide_lifecycle_phase2.TestDeleteConcurrency` (limpieza por ID) y se añade
`test_guia_delete_guards.py` (escenarios a–m).

**Limitaciones declaradas.** (1) El **motivo** en la vía directa usa un valor por defecto documentado
(«sin motivo declarado») para no romper un test existente; endurecerlo requiere decisión. (2) **H-SEC-5 sigue
pendiente**: mientras la bitácora pueda alterarse, el registro de eliminaciones **no es inmutable por garantía
técnica** — brecha declarada. (3) La cobertura de **costos** (escenario f) es indirecta.

**Evidencia:** `AUDITORIA_INTEGRAL_20261012/fase3/` (diseño, matriz a–m, pruebas, regresión, dry-run de residuos).

<!-- actualizado: 2026-10-12 (2) — alta AD-104 (guardas G1 de eliminación de guía D-G1..D-G4 + saneamiento de fixture G2). Core 18.0.6.7.0 → 18.0.6.8.0; intake 18.0.0.13.0 → 18.0.0.14.0. H-SEC-5 (bloqueo de bitácora) SIGUE PENDIENTE. Ver `AUDITORIA_INTEGRAL_20261012/fase3/`. Solo documentación. -->

### AD-105 (2026-10-12) — Motivo obligatorio, rol de jefatura y bitácora APPEND-ONLY (FASE 4)

**Decisiones aprobadas por Mauricio (FASE 4):**
- **H1 — Motivo obligatorio en TODA vía.** Se retira el valor por defecto de la vía directa (cierre del desvío
  D-G3 de la FASE 3): sin `madenat_guia_delete_reason` no vacío, `unlink()` **se bloquea** con un `UserError`
  que guía al asistente. La eliminación nativa de la interfaz (lista/formulario) queda **bloqueada con mensaje**
  —opción elegida por ser la que **menos cambia las vistas** (sin tocar botones, acciones ni formularios)—. Las
  vías legítimas (asistente de ciclo de vida, Modo A y **reclasificación AD-73**) aportan su **propio motivo de
  negocio**.
- **H2 — Rol autorizado = «Jefatura de Operaciones» (o sistema).** `_guia_delete_group_ok()` (constante
  `GUIA_DELETE_GROUPS`) sustituye la exigencia del grupo técnico `stock.group_stock_manager` en `unlink()` y en
  `_cleanup_orphan_moves_guia()`, y es la **única** comprobación reutilizada por el modelo y el asistente.
  **No** se amplían permisos de stock ni se crean grupos. Operaciones, Auditoría y usuarios internos **no**
  pueden eliminar; `stock_manager` **sin** jefatura tampoco.
- **H3 — H-SEC-5 mínimo IMPLEMENTADO.** `madenat.audit.log` pasa a ser **APPEND-ONLY**: `write()` y `unlink()`
  lanzan `UserError` de **negocio** —incluso con `sudo()` y para el grupo de sistema—; la ACL del grupo de
  sistema pasa de `1,1,1,1` a **`1,0,1,0`** (se conservan `create`/`read`). Única excepción: la limpieza
  **test-only** (token vivo `madenat_sv_test_cleanup_token` + `--test-enable` **real** + BD de test), inerte sin
  `--test-enable`. Las correcciones se registran como **eventos NUEVOS**, nunca editando.
- **H4/H6 — Cobertura y fixtures.** Prueba dedicada del escenario **(f)** de costos; fixtures de las suites
  `test_sv_rebaja_*` saneadas (sin residuo de socios `*_oper`).
- **H5 — Saneamiento LOCAL** de residuos de prueba en `madenat_test`, con **simulación previa** y borrado por
  **IDs explícitos** uno a uno.

**Afirmación ajustada («bitácora inmutable»).** Lo garantizado es **inmutabilidad por ORM**: `write`/`unlink`
bloqueados sin excepción para `sudo` ni para el grupo de sistema, salvo el bypass de pruebas **inerte**. **NO**
se garantiza inmutabilidad frente a **SQL directo** ni frente a un **administrador de base de datos**.

**Límite persistente y defensa propuesta (NO implementada).** Trigger de base de datos que rechace
`UPDATE`/`DELETE` sobre `madenat_audit_log`, o **hash encadenado** por registro. Requiere decisión de Mauricio.

**Evidencia:** `AUDITORIA_INTEGRAL_20261012/fase4/` (diseño, matriz antes/después, pruebas, regresión,
simulación y ejecución del saneamiento, diff y hashes).

<!-- actualizado: 2026-10-12 (3) — alta AD-105 (H1 motivo obligatorio en toda vía; H2 rol jefatura/sistema en lugar de stock_manager; H3/H-SEC-5 bitácora APPEND-ONLY por ORM con bypass test-only inerte y límite SQL/DBA declarado; H4 escenario f; H6 fixtures *_oper). Core 18.0.6.8.0 → 18.0.6.9.0; intake 18.0.0.14.0 → 18.0.0.15.0; logistics 18.0.1.26.0 → 18.0.1.27.0. Ver `AUDITORIA_INTEGRAL_20261012/fase4/`. Solo documentación. -->

### AD-106 (2026-10-15) — Supuesto de una sola compañía y conservación de los usuarios de prueba inactivos

**Contexto.** La auditoría integral del 2026-10-12 dejó **abierta** la pregunta de si `madenat.guia.processing`
debe aislarse por compañía (`company_id` + `ir.rule`), porque hoy **no** declara `company_id` **ni** tiene regla
de registro de compañía (fase4, §9 y §10). La imputación documental SV (`madenat.sv.imputation`, `AUD-ETQ-07`)
**sí** tiene `company_id` obligatorio y su regla de registro multi-compañía en
`madenat_lumber_logistics/security/madenat_sv_imputation_rules.xml`; esta decisión **no** la modifica.

**Decisión (aprobada por Mauricio — FASE 5, C-3).**

- **Supuesto vigente:** MADENAT opera con **UNA sola compañía**.
- **No** se implementa `company_id` **ni** `ir.rule` de compañía en `madenat.guia.processing` (tampoco se
  cambian sus permisos por este motivo). El control de acceso vigente es **por rol** (jefatura / operaciones /
  auditoría), según AD-103, AD-104 y AD-105.
- **Condición de reapertura:** si en el futuro existe **más de una compañía**, esta decisión debe **reabrirse**
  antes de operar guías compartidas entre compañías.
- **Riesgo residual declarado (no ocultado):** un usuario **con jefatura de otra compañía** podría ver o
  eliminar guías; hoy es inocuo porque sólo hay una compañía (la FASE 4 probó que **sin** jefatura la
  eliminación se bloquea).

**Conservación de datos de prueba.** Los **3 usuarios inactivos** `@madenat.test` (`v3_concil_oper@`,
`v3_concil_jef@`, `impl_sv_check@`) se **conservan**: no se eliminan ni se anonimizan. El saneamiento H5 de la
FASE 4 borró los residuos de socios y de bitácora y dejó estos usuarios explícitamente documentados; esta AD
formaliza la decisión. El pendiente **D7** de la FASE 1 queda **DECIDIDO = CONSERVAR**.

**Evidencia.** `AUDITORIA_INTEGRAL_20261012/` — README §4.3 (H-DATA-1) y §7 (D7); `fase4/README.md` §7, §9 y §10.

<!-- actualizado: 2026-10-15 (1) — alta AD-106 (supuesto de una sola compañía: sin `company_id` ni `ir.rule` de compañía en `madenat.guia.processing`, con condición de reapertura declarada; y conservación de los 3 usuarios inactivos `@madenat.test`, D7 = CONSERVAR). Versión 04 12.21.0 → 12.22.0. Registrado en el commit local ① de la FASE 5 (commits ordenados, solo local); sin push ni despliegue. -->

### AD-107 (2026-10-15) — Cierre de D18, P2-2 fuera y hallazgos de instalación desde cero (FASE 7)

**1. D18 — CERRADO.** Los 5 archivos que el triaje de FASE 1 marcó `desconocido` se incorporan al historial
**sin modificar su contenido** (verificado por SHA256), cada uno en el commit de su módulo:

- `madenat_lumber_core/tests/test_duplicate_validation.py` (D18-1) → `bfda876` `fix(core)`.
- `madenat_lumber_logistics/wizards/lumber_shipment_rebaja_wizard.py` y `..._views.xml`
  (D18-2/D18-3) + `tests/test_rebaja_contenedor.py` (D18-4) + `tests/test_service_return_imputation_guard.py`
  (D18-5) → `56405cb` `feat(logistics)`, con **18.0.1.27.0 → 18.0.1.28.0** y CHANGELOG.

**Atribución documental:** CANON/18 §7.3/§14.1/§14.5 (asistente de rebaja por nave), expediente
`AUDIT_B01_20261004`, CANON/12 §5.2/§6.2 (el número de guía no es discriminador) y los guards AUD-ETQ-02/06 ya
commiteados en `ded5e89`. La FASE 6 demostró que la exclusión previa dejaba el historial **no desplegable**
(`madenat_lumber_logistics` no cargaba: `No matching record found for external id
'model_lumber_shipment_rebaja_wizard_line'`). Incorporados los archivos, **el CSV de ACL carga sin error**.

**2. P2-2 — FUERA (decisión).** `madenat_lumber_reports/views/lumber_reports_menu.xml` (inactiva el menú vacío
«📈 Reportes MADENAT») **no se commitea ni se despliega**: su origen no está demostrado («P2-2» solo aparece en
el comentario del propio cambio) y el módulo depende de `madenat_lumber_costing` (D1 bloqueado).
**Reabrir** solo con decisión expresa de Mauricio.

**3. Reparación de instalación desde cero (K2) — APLICADA.** `madenat_lumber_intake/views/intake_console_views.xml`
definía la acción `action_madenat_lumber_intake_new` **después** de usarla (uso en la línea 20; definición en
la 1116) ⇒ `ValueError: External ID not found …` al instalar. Se corrige con un **movimiento puro** del bloque
(ids, nombres y contenido intactos; +12/−12). **Verificado:** instalación desde cero de `madenat_lumber_intake`
en base limpia **exit 0**. Barrido de referencias adelantadas en todos los módulos instalables: era la **única**.

**4. HALLAZGO ABIERTO Y BLOQUEANTE (requiere decisión).** `madenat_lumber_logistics` **no instala desde cero**:
`views/madenat_sv_imputation_views.xml:215` contiene `<record id="menu_madenat_sv_imputation" model="ir.ui.menu">
<field name="active" eval="False"/></record>` **sin `name`**, y el `<menuitem>` que lo definía fue **retirado**
en `ded5e89` (④) pese a que su propio comentario afirma que se conserva «para instalaciones nuevas» ⇒ al crear
el registro desde cero: `NotNullViolation: null value in column "name" of relation "ir_ui_menu"` ⇒
`Failed to load registry`. En una base **existente** el `-u` no falla (el menú ya existe y no se reescribe el
nombre), por lo que el defecto quedó **latente**. **No se corrigió** (queda fuera de K2): opciones mínimas
`(a)` restituir el `<menuitem>` antes del `<record>` —lo que el comentario dice— o `(b)` añadir
`<field name="name">Imputaciones documentales SV</field>` al `<record>`.

**5. HALLAZGO (despliegue) — no mezclar «BD con WIP» y «código sin WIP».** Al actualizar (`-u`) sobre una base
cuyo estado proviene de la era-WIP, Odoo re-valida **todas** las vistas cargadas y falla en
`madenat_lumber_costing/views/lumber_cost_distribution_views.xml` con
`action_apply_c2 no es una acción válida en lumber.cost.distribution`: esa acción existe **solo** en el WIP de
`costing` (**D1, no commiteado**). ⇒ Antes de desplegar hay que comprobar en el destino que ninguna vista
almacenada referencia métodos ausentes del código a entregar (y resolver D1 o el WIP correspondiente).

**6. Defecto de prueba pendiente (K7).** `test_length_uom_and_subproducto` pasa un id de **`product.template`**
a un campo `Many2one('product.product')` (`mixin_lumber_ingest.py:415`) ⇒ `MissingError` en base limpia.
Es un defecto **de la prueba** (no introducido por la FASE 5/7); recomendación: buscar en `product.product`.

**7. Regla operativa vigente.** El despliegue al TEST remoto se hace por **`-u`** de los módulos indicados
(no `-u all`). La capacidad de **instalación desde cero / DR** queda **pendiente** del hallazgo 4.

**Evidencia:** expedientes `FASE6_HEAD_CHECK_20261015/` y `FASE7_CIERRE_D18_20261015/`.

<!-- actualizado: 2026-10-15 (2) — alta AD-107 (cierre de D18 en 2 commits: `bfda876` core y `56405cb` logistics 18.0.1.28.0; P2-2 fuera por decisión; reparación K2 de la instalación desde cero de intake —movimiento puro del bloque de la acción, verificado con exit 0—; HALLAZGO BLOQUEANTE abierto: el `<record model="ir.ui.menu">` sin `name` en `madenat_sv_imputation_views.xml` impide instalar `logistics` desde cero (`NotNullViolation`), introducido por `ded5e89` al retirar su `<menuitem>`; hallazgo de despliegue: no mezclar «BD con WIP» y «código sin WIP» por la vista de `costing` (`action_apply_c2`); defecto de prueba K7 pendiente). Versión 04 12.22.0 → 12.23.0. Commits locales de la FASE 7 (solo local); sin push ni despliegue. -->

### AD-108 (2026-10-15) — Instalación desde cero de `logistics` (M1/M2), método de verificación y estado de D1 (FASE 8)

**1. M1 — CERRADO: menú `menu_madenat_sv_imputation` sin `name`.** El `<record id="menu_madenat_sv_imputation"
model="ir.ui.menu">` de `madenat_lumber_logistics/views/madenat_sv_imputation_views.xml` quedó **sin `name`**
cuando en `ded5e89` se retiró su `<menuitem>` (unificación de acceso 2026-10-10): al **instalar desde cero** el
registro se crea sin nombre ⇒ `NotNullViolation … ir_ui_menu` ⇒ `Failed to load registry`; en una base
existente el `-u` no fallaba (defecto **latente**). Se **restituye el `<menuitem>`** (mismos
`name`/`parent`/`action`/`sequence`) **antes** del `<record>`, que es el mecanismo documentado en el expediente
`UNIFY_SV_REBAJA_MENU_20261010` y en CANON/02 §17.x + CANON/03 (NAV-02). El menú sigue **inactivo**;
id/nombre/acción/visibilidad no cambian. → commit `7d277e9`; `madenat_lumber_logistics` **18.0.1.28.0 →
18.0.1.29.0**.
**Barrido de la clase M1** (records/menuitems de menú sin los campos obligatorios en todos los módulos
instalables): **0 casos restantes** (los demás hallazgos eran ids de otros módulos o XML comentado).

**2. M2 — CERRADO: helper de la prueba de longitudes.** `tests/test_length_uom_and_subproducto.py` usaba
`self.env['product.template']` y pasaba ese id a `lumber.reception.line.product_id`, que es
`Many2one('product.product')` (`mixin_lumber_ingest.py:415`) ⇒ `MissingError` en base limpia. Se cambia a
`product.product` (solo la prueba; sin tocar producción). → commit `7c417ae`, **sin cambio de versión**
(18.0.6.9.0): es una corrección de test.

**3. Método de verificación (FASE 8).** (A) **Instalación desde cero** en dos pasos —(1) INSTALABILIDAD sin
`--test-enable`; (2) SUITES con `-u` de los módulos MADENAT y `--test-tags` acotado a ellos, evitando los tests
de los módulos de Odoo— sobre una base temporal con «test» en el nombre; (B) **camino `-u` desde un estado
anterior**, restaurando el dump de 2026-10-02 (`backups/procesadores_guardas_20261002/`), elegido por ser el
más reciente **sin** la vista de `costing` con `action_apply_c2`.

**4. Resultados.** (A) `-i shipping_core,core,logistics,intake` ⇒ **exit 0** (los 4 instalan;
`logistics` en 4.70 s) ⇒ **reconstrucción desde cero (DR) DEMOSTRADA**. Suites (A): `3 failed + 47 error de
1314`; (B) `1 failed + 4 error de 1314`. Comparación **por nombre**: la intersección A∩B son **4 fallas del
baseline** (`TestGuiaPickingLink.test_t_g2_03_exclusion_retornos` + `TestSvEscalationSecurity.test_02/03/04`);
45 fallas aparecen **solo en A** (artefactos de una base limpia sin configuración: precisión decimal
`Product Unit of Measure` 2 vs 4, `Product Price` 2 vs 3; 1 producto vs 20; parámetros `madenat.*` no
sembrados —`allow_product_creation`, `allow_subproduct_creation`, `omission_threshold`, umbrales de varianza—;
y pruebas RPC/`AccessError`); 1 falla aparece **solo en B**
(`TestServiceReturnImputationGuard.test_09…`, dependiente de datos: el usuario real Cristhian del dump **no
tiene** Jefatura/Gerencia). ⇒ **0 fallas nuevas atribuibles a M1/M2**, y `TestLengthUomAndSubproducto` **en
verde**.
**Hallazgo para el despliegue (DR/config):** una instalación limpia **no reproduce** la configuración de
`madenat_test` (precisión decimal, parámetros `madenat.*`, catálogo de productos). Debe declararse el juego
mínimo de configuración requerido, o los cálculos y varias suites diferirán.

**5. D1 — `costing` (10 archivos del WIP): estado y recomendación (`REQUIERE_DECISIÓN`).** Lo que aporta el WIP:
`models/lumber_cost_distribution.py` (+377), `models/lumber_shipment_costing.py` (+400), **nuevo**
`models/stock_lot_cost_line.py`, `views/lumber_cost_distribution_views.xml` (+54, con el botón
`action_apply_c2`), **nueva** `views/lumber_shipment_costing_views.xml`, **nuevo** `tests/test_shipment_costing_c2.py`,
`security/ir.model.access.csv` (+16), `models/__init__.py`, `tests/__init__.py` y `__manifest__.py` (+1).
**Coherencia:** en el HEAD la vista **no** menciona `action_apply_c2` y el modelo **no** lo define (0/0);
en el WIP ambos lo incorporan (1/1) ⇒ **HEAD y WIP son coherentes por separado**, y lo que rompe es la
**mezcla** (vista-WIP guardada en la BD + código HEAD: FASE 7, `ParseError … action_apply_c2 no es una acción
válida en lumber.cost.distribution`). **Versión:** `18.0.1.0.0` en HEAD **y** en WIP (sin subir) y CHANGELOG
**sin entrada** para el C2 ⇒ si se consolida, debe subirse la versión y registrar el cambio (**D1**).
**Dependencias:** `madenat_lumber_reports` depende de `costing` (por eso `reports` no puede instalarse ni
actualizarse sin resolver antes `costing`); `billing` y `vendor_payment` **no** dependen de él.
**Recomendación (a decidir):** (a) **commitear `costing`** con versión + CHANGELOG (p. ej. 18.0.1.1.0) y
desplegarlo junto a `reports`; (b) **mantenerlo fuera** (estado actual: el HEAD es coherente y desplegable sin
`reports`); o (c) **revertir el WIP en la base local** (`madenat_test`) para que su estado vuelva a
corresponder al código entregado. **No ejecutado.**

**6. P2-2 — sigue FUERA.** `madenat_lumber_reports/views/lumber_reports_menu.xml` (menú vacío «📈 Reportes
MADENAT», origen no demostrado) no se commitea ni se despliega; se reabre solo con decisión expresa (y, en su
caso, tras resolver `costing`).

**7. Riesgos residuales de la FASE 8.** Defecto de datos dependiente del estado del destino (prueba con el
usuario real Cristhian sin Jefatura); configuración no sembrada en el alta limpia (punto 4); D1 y P2-2 según lo
anterior; `VIEW-01/04` en navegador sigue pendiente de ejecución manual.

**Evidencia:** expediente `FASE8_CIERRE_DR_20261015/` (`logs/a_p1_install.log`, `logs/a_p2b_suites.log`,
`logs/b_update.log`, `logs/ab_comparison.txt`, `logs/a_p2b_classification.txt`).

<!-- actualizado: 2026-10-15 (3) — alta AD-108 (FASE 8): **M1 cerrado** (menú `menu_madenat_sv_imputation` sin `name`: se restituye su `<menuitem>` antes del `<record>`; `logistics` 18.0.1.29.0; barrido de la clase: 0 casos) y **M2 cerrado** (prueba de longitudes a `product.product`, solo test); **método de verificación** en dos pasos (instalabilidad sin tests / suites con `--test-tags`) + **camino `-u` desde un dump anterior al WIP de costing**; **DR demostrada** (`-i` de los 4 módulos con exit 0); fallas A∩B = 4 del baseline y **0 nuevas atribuibles a M1/M2**; hallazgo de configuración no sembrada en el alta limpia (precisión decimal 2 vs 4, 1 producto vs 20, parámetros `madenat.*`); **D1 `costing` caracterizado** con recomendación (coherente por separado HEAD/WIP; rompe la mezcla); P2-2 sigue fuera. Versión 04 12.23.0 → 12.24.0. Commits locales de la FASE 8 (solo local); sin push ni despliegue. -->



### AD-109 (2026-10-15) — Registro de etiquetas en la rebaja SV: defectos F1/F2/F3 y correcciones S2/S3/S1 (FASE 10)

**Origen.** Diagnóstico `DIAGNOSTICO_REBAJA_SV841_REGISTRO_ETIQUETAS_20261015/INFORME_DIAGNOSTICO.md` sobre
`SV00000000841` (guía 1198): **el registro de etiquetas SÍ funciona en el caso sano** (E7), pero en el caso
reportado no quedaba ninguna etiqueta registrada por **tres defectos encadenados preexistentes** (ninguno
introducido por las FASES 5–8 ni por el WIP; las cinco funciones implicadas son idénticas en HEAD y en el WIP y
existen desde `2888745`, 2026-10-02, I2/AD-91):

| # | Defecto | Causa | Efecto operativo |
|---|---|---|---|
| **F1** | `_i2_signature()` no incluía la **selección de etiquetas** (sólo los repartos SV) y `_i2_get_or_create()` buscaba por `documentary_key` **sin filtrar estado** (`documentary_key` es UNIQUE) | `models/madenat_sv_imputation.py` (`_i2_build_documentary_key`, `_i2_get_or_create`) y `wizards/madenat_sv_imputation_wizard.py` (`_i2_signature`) | Para la guía 1198 cualquier «Guardar» **sin reparto** colisionaba con el documento **APLICADO `IMP02220`** ⇒ `UserError: … ya no admite preparación (estado applied)` ⇒ **las etiquetas nunca se registraban** |
| **F2** | `sv_assignment_work_imputation_ids` declaraba `domain=[('state','in',('draft','pending'))]` sobre un `One2many`: **el ORM no aplica el `domain` declarativo al leer**; el contador usaba ese mismo campo | `models/…` (`sv_assignment_work_imputation_ids`, `_compute_sv_assignment_work`, `action_continue_preparation`) | La sección «Trabajo en preparación» **listaba y contaba** documentos ANULADOS/APLICADOS/REVERSADOS (la anulada `IMP04823`) y ofrecía «Continuar», que fallaba con `UserError` |
| **F3** | «Guardar borrador» (`_i2_build_imputation`) **no exigía ≥1 etiqueta incluida** (sólo `action_apply` lo hacía); `_i2_included_lines()` = `selected or sv_alloc_ids` y las candidatas se abrían con `selected=False` | `wizards/…` (`_i2_build_imputation`, borrado de líneas no incluidas) | Guardar sin seleccionar (o desmarcar todo) dejaba o **borraba líneas en silencio**: es el estado exacto de `IMP04823` (0 líneas + vínculo al SV) |


**1. S2 — «Trabajo en preparación» con filtro EFECTIVO (defecto F2).** (`logistics` 18.0.1.29.0 → **18.0.1.30.0**;
commit `19611d0`)
`stock.lot.sv_assignment_work_imputation_ids` pasa de `One2many` con `domain` declarativo a **`Many2many`
calculado y NO almacenado** (`store=False`; relación explícita
`stock_lot_madenat_sv_imputation_work_rel`, sin tabla) que resuelve la lista con **búsqueda explícita en el
servidor** (`work_sv_lot_id` + `state in ('draft','pending')`), en línea con `sv_assignment_imputation_ids`;
conserva nombre y semántica y **no** usa `sudo` (respeta compañía y reglas de registro). El contador
(`sv_assignment_work_count`) y `sv_assignment_work_m3` se calculan con la MISMA búsqueda.
`action_continue_preparation` sobre un estado **terminal** ya no lanza un error técnico: devuelve una
**notificación operativa** (`display_notification`) con la ruta disponible («Volver a borrador» para un anulado;
reversa para un aplicado/reversado). El botón «Continuar» sigue disponible sólo para `draft`/`pending`.
**Pruebas:** `tests/test_sv_rebaja_work_filter.py` (**WF-01..07**, T2/T3), primero en rojo (WF-02..06 fallaban);
se actualizan SAVE-13 y FLOW-02 (esperaban `UserError` al continuar un aplicado/anulado) a la ruta operativa.

**2. S3 — Bloqueo del documento de rebaja VACÍO (defecto F3).** (`logistics` 18.0.1.30.0 → **18.0.1.31.0**;
commit `e2d6b64`)
`_i2_build_imputation` comprueba `_i2_included_lines()` **antes** de crear o actualizar el documento; sin ninguna
etiqueta incluida lanza un `UserError` de negocio en español («No se puede guardar un documento de rebaja sin
etiquetas. Selecciona al menos una etiqueta…»). Al rechazar **antes** de escribir, un guardado inválido no crea
documento (ni vacío) y **no pierde** las líneas ya registradas. Se conservan los flujos legítimos (anular,
«Volver a borrador», reabrir), el caso SAVE-05 (destino SV previsto con cantidad 0) y el techo duro.
**Evidencia de independencia:** `action_cancel` / `action_reopen_to_draft` / `action_reverse` **no** pasan por
`_i2_build_imputation` (se invocan desde el documento, no desde el asistente) ⇒ ninguno depende de «guardar
vacío». **Pruebas:** `tests/test_sv_rebaja_empty_guard.py` (**SG-01..06**, T6), primero en rojo (SG-01/SG-03).
Las pruebas evitan el **savepoint que Odoo interpone en `assertRaises`** (revierte los efectos del bloque y

**3. S1 — Clave documental con las etiquetas seleccionadas (defecto F1 · causa raíz).**
(`logistics` 18.0.1.31.0 → **18.0.1.32.0**)
* `_i2_signature()` incluye ahora las **etiquetas incluidas** (`_i2_included_lines()` ordenadas por
  `processed_lot_id`) con su volumen nominal —prefijo `L<id>:<nominal>`— **además** de los repartos SV. La firma
  sólo se usa para construir claves NUEVAS.
* `_i2_get_or_create()` devuelve **sólo** documentos en estado de trabajo (draft/pending). Ante coincidencia de
  clave con un documento terminal: **`applied`** ⇒ mensaje claro («Esta rebaja ya se aplicó con esta misma
  selección…») y **sin duplicar**; **`reversed`/`cancelled`** ⇒ documento NUEVO con clave **distinta y trazable**
  (`discriminator` = id del documento que ocupaba la clave, encadenado si hiciera falta), de forma determinista.
* **Una sola implementación central**: la receta de la clave y las reglas de reutilización viven en el modelo; el
  asistente sólo aporta la firma.

**4. Retrocompatibilidad (regla dura).** La receta **base** de la clave —`I2|guia|processor|signature` ⇒
`IMP-<guia>-<sha256[:16]>`— **no cambia**: con `discriminator=''` (valor por defecto) el resultado es
**byte a byte** el histórico. Por eso la **clave de `IMP02220`** (`IMP-1198-E95825AAF94E58AD`) y la de cualquier
documento aplicado existente siguen siendo idénticas y verificables; **no se migra ni se reescribe ninguna clave
ni firma histórica**. La firma de los documentos ya aplicados (p. ej. `IMP02220`) se mantiene intacta: la
verificación de firmas de documentos históricos funciona exactamente igual. `documentary_key` sigue siendo
UNIQUE; la clave nueva nunca colisiona porque el discriminador produce un material distinto.

**5. Riesgo residual específico.** La reutilización de claves se apoya en `documentary_key` UNIQUE + el
condicional `_check_single_work_per_guia` + el bloqueo de recursos de `action_apply`; la comprobación de
concurrencia real (dos transacciones simultáneas) sigue cubierta por la suite `test_sv_rebaja_save_lock_tx`
existente (no modificada).

**6. Resultado de la validación (LOCAL).** TDD por corrección (rojo → verde). Regresión del módulo `logistics`
completa tras cada commit, **comparada por NOMBRE** con el baseline vigente (FASE 5, HEAD `677294b`):
**4 failed + 0 error** en las tres corridas (el mismo subconjunto logístico de las 10 fallas del baseline:
`TestProcessorLocations.test_09_auditoria_envio_normal` y `TestProcessorShipmentAD89.test_t1/t5/t6`) ⇒
**0 fallas nuevas**. Sin `-u all`, sin cambios en datos reales, sin tocar `IMP04823`/`IMP02220` (hashes de fila,
líneas y repartos idénticos antes/después).

**7. Pendientes (fuera del alcance de esta fase).** (a) **Decisión sobre `IMP04823`** (anulada, vacía, con
vínculo al SV): es un dato de origen, no un defecto del flujo; opciones: conservarla como historia anulada o
reabrir/rehacer la rebaja de la guía 1198 con una selección válida (ninguna de las dos se ejecutó). (b) **Cómo
resolver la rebaja de `SV00000000841` en datos reales** con el nuevo flujo (preparar la selección correcta).
(c) **Verificación en el remoto** del comportamiento corregido (esta fase es local). (d) **Trigger de bitácora**:
`IMP04823` no tiene evento de creación ni de anulación en `madenat_audit_log` (su anulación no pasó por el
código) — se mantiene como hallazgo abierto. (e) **D1 (`costing`)** sigue fuera, según AD-108.
(f) `VIEW-01/04` (navegador) sigue pendiente de confirmación manual.

**Evidencia:** expediente `FASE10_REBAJA_SV_ETIQUETAS_20261015/` (`pre/`: respaldo del árbol, dump de
`madenat_test`, SHA256 de los 11 archivos del WIP, conteos y hashes de `IMP02220`/`IMP04823`; `logs/`:
`*_tdd_before.log`, `*_after.log`, `s*_logistics_full.log`, listas de fallas por nombre; `evidence/`: scripts de
comprobación; `INFORME_FASE10.md`). Fuera del alcance: `costing` y el menú de `reports` (P2-2/D1).

<!-- actualizado: 2026-10-15 (4) — alta AD-109 (FASE 10): corrección del registro de etiquetas en la rebaja SV.
**F1/F2/F3** documentados con archivo:línea y reproducción; **S2** = campo de trabajo calculado no almacenado con
búsqueda explícita + contador coherente + «Continuar» operativo (18.0.1.30.0, `19611d0`); **S3** = `UserError` de
negocio sin ninguna etiqueta incluida, comprobado ANTES de escribir (18.0.1.31.0, `e2d6b64`); **S1** = firma con
etiquetas seleccionadas + reglas de estado terminal (applied ⇒ mensaje claro; reversed/cancelled ⇒ documento nuevo
con clave distinta y trazable) con **retrocompatibilidad byte a byte** de la receta base (18.0.1.32.0); pruebas
nuevas WF-01..07, SG-01..06 y DK-01..08 primero en rojo; regresión por nombre con el mismo subconjunto del
baseline (0 nuevas); sin migraciones, sin cambios en `IMP04823`/`IMP02220`, sin push ni despliegue.
Versión 04 12.24.0 → 12.25.0. -->

enmascararía la creación/borrado real) usando un `try/except` propio.


### AD-110 (2026-10-15) — Integridad del ciclo de vida de las imputaciones SV: A-1, B-1, M-2, M-4, B-2 y B-3 (FASE 11)

**Origen.** Auditoría de sólo lectura `AUDITORIA_CICLO_VIDA_IMPUTACIONES_20261015/INFORME_AUDITORIA.md`
(§1.2 matriz de transiciones, §7 propuestas) sobre `madenat.sv.imputation` (`logistics` 18.0.1.32.0, HEAD
`ee7b7c6`). Dictamen: la vía OFICIAL del ciclo está bien construida (métodos propios, permisos por rol,
validaciones, locks y bitácora firmada), pero la **vía pública `write()`** permitía, con el documento en
`draft`/`pending`, fijar `state` a CUALQUIER destino, y `create()` permitía nacer en estado terminal.

**1. Decisión A-1/B-1 — `state` y las marcas de transición sólo cambian por las acciones OFICIALES.**
- Se define `I2_TRANSITION_MARK_FIELDS` = `state`, `audit_hash`, `snapshot_json`, `executed_by_id`,
  `execution_date`, `reversed_by_id`, `reversal_date`, `reversal_reason`, `reversed_imputation_id`,
  `cancelled_by_id`, `cancellation_date`, `cancellation_reason`, `reopened_by_id`, `reopen_date`,
  `reopen_reason`.
- `write()` público (ORM/RPC) **rechaza** cualquier intersección con esas marcas con un `UserError` de negocio;
  **no** hay excepción para `sudo()` ni para `with_context(...)`. Se conserva la inmutabilidad previa del
  `applied` (`I2_APPLIED_WRITABLE`), ahora reducida a la ENTRADA del motivo (`reason`), el token de concurrencia
  (`edit_version`) y el chatter.
- `create()` normaliza `state='draft'` y **rechaza** cualquier otro estado y cualquier marca fabricada.
- Las acciones oficiales (`action_pending`, `action_back_to_draft`, `action_apply`, `action_cancel`,
  `action_reverse`, `action_reopen_to_draft`) y el **sello recíproco** de la cadena
  (`origin.reversed_imputation_id`) escriben por la **vía privada** `_i2_write_protected_state`
  (`super().write` + bump de `edit_version`), método `_`-prefijado **no invocable por RPC**.
- **Decisión de diseño explícita: NO se usa una bandera de contexto.** El contexto de una llamada RPC lo controla
  el cliente y es falsificable (las suites ya probaban `with_context(i2_reopen=True)`); la autorización es la del
  propio método oficial (permiso + estado + validaciones) y la escritura base no es alcanzable por RPC.
- **Entrada del motivo.** El motivo se captura en el campo libre `reason` (o como parámetro de la acción, p. ej.
  desde el asistente) y la acción lo **congela** en su campo de marca. En el formulario,
  `reversal_reason`/`cancellation_reason`/`reopen_reason` pasan a **sólo lectura** (y `origin_imputation_id`
  también: la cadena la gestiona el sistema). Razón: esos campos eran a la vez ENTRADA (cliente) y MARCA
  (historia), y esa ambigüedad era la puerta por la que la escritura directa podía falsificar la historia.
- **Invariante de cierre:** no se puede fabricar un `applied` sin firma (`audit_hash` + `snapshot_json` +
  `executed_by_id` + `execution_date`) ni un `cancelled` sin rastro (`cancelled_by_id` + `cancellation_date` +
  motivo + evento `imputation_cancel`).

**2. Decisión M-2 — la reversa toma los locks de capacidad y revalida el estado.** `action_reverse` adquiere los
mismos advisory locks que `action_apply` (`_i2_lock_resources`: etiquetas ns 3 + SV ns 2, orden determinista) y
**revalida el estado tras el bloqueo**. Si otra conexión tiene el lock, o el documento dejó de estar `applied`, se
rechaza de forma CONTROLADA (mensaje funcional, sin cambios parciales, sin bitácora y sin «último gana»). No se
añade reintento automático: el mensaje permite reintentar tras actualizar la información (mismo patrón que
`action_apply`/`action_reopen_to_draft`).

**3. Decisión M-4 — cadena de corrección automática.** En `_i2_get_or_create`, cuando la clave base está ocupada
por una imputación TERMINAL (mismo alcance: misma guía/procesador/firma), la operación nueva nace con
`origin_imputation_id` apuntando al último eslabón terminal de la cadena; al aplicarse, `action_apply` sella el
recíproco `reversed_imputation_id` en el origen (vía privada). **No** se tocan documentos existentes ni claves.

**4. Decisión B-2 — el contenido sólo se edita en preparación.** Líneas y repartos (`madenat.sv.imputation.line`,
`madenat.sv.imputation.sv.line`) sólo admiten `create`/`write`/`unlink` con el padre en `draft`/`pending`
(`I2_CHILD_EDITABLE_STATES`); en `applied`, `reversed` y `cancelled` fallan con mensaje de negocio. Los caminos
oficiales («Reversar», «Volver a borrador») devuelven el documento a preparación antes de permitir tocar el
contenido, de modo que lo reabierto conserva su contenido íntegro y no se altera a posteriori lo aplicado/anulado.

**5. Decisión B-3 — la anulación exige motivo.** `action_cancel` exige motivo no vacío (tras `strip`), lo registra
en `cancellation_reason` (metadata) y lo incorpora al payload firmado del evento `imputation_cancel`
(`{'motivo': …}`). Sin cambio de grupos: se mantiene el ACL de escritura vigente.

**6. M-3 (documentado, NO corregido).** Los agregados canónicos de `stock.lot` (`sv_assignment_nominal_m3`,
`sv_assignment_applied_m3`, `sv_assignment_applied_count`, `sv_assignment_documental_balance_m3`) son
`store=True, compute_sudo=True`, mientras la proyección viva (`sv_assignment_imputation_ids` y el trabajo) es
`store=False` con `compute_sudo` implícito `False`: un usuario sin ACL sobre `madenat.sv.imputation` obtiene
`AccessError` al leerla. Es una incoherencia de RÉGIMEN DE ACCESO (no de exactitud) y queda como **hallazgo
abierto**, con la recomendación de decidir el régimen (excluir de la vista, documentar el `AccessError` o `sudo`
acotado a compañía) en una fase propia.

**7. Datos heredados (NO se modifican).** `IMP02220` (aplicada con 0 repartos positivos) e `IMP04823` (anulada sin
metadata, sin bitácora y sin firma) son DATO DE ORIGEN: se conservan tal cual, igual que los 8 eventos
`imputation` de guías `TX10` sin `guia_processing_id`. Regularizarlos es una decisión de negocio **pendiente** y
fuera del alcance de esta fase.

**8. Alcance y límites.** Sólo `madenat_lumber_logistics` (nunca `-u all`); no se tocan `costing` ni el menú de
`reports` (WIP local preexistente). Sin migración de datos, sin cambios de esquema y sin cambios en las claves
documentales históricas (`_i2_build_documentary_key` intacta). Los recomputes de `stock.lot` siguen
disparándose con las transiciones.

**9. Validación (LOCAL).** TDD: la suite nueva `tests/test_sv_imputation_lifecycle_integrity.py` (A-1/B-1/M-2/
M-4/B-2/B-3; 17 pruebas, con matriz por grupos operaciones/jefatura/gerencia/auditoría/sin grupo, invariantes
documentales y `TestSvImputationReverseLocks` con lock externo real y limpieza por IDs) quedó en **verde**;
regresión del módulo `logistics` completa comparada **por nombre** con el baseline vigente: **4 failed / 0 error**
(el mismo subconjunto; **0 fallas nuevas**). `IMP04823`/`IMP02220` sin cambios (estado, valores y hashes).
`madenat_lumber_logistics` **18.0.1.32.0 → 18.0.1.36.0**.

**Evidencia:** expediente `FASE11_INTEGRIDAD_CICLO_IMPUTACIONES_20261015/` (`pre/`: respaldo del árbol, dump de
`madenat_test`, SHA256 del WIP y hashes de los documentos reales; `logs/`: baseline, suite nueva y regresión
completa; `INFORME_FASE11.md`, `RUNBOOK_FASE11.md`, `CHECKLIST_MANUAL_MAURICIO.md`).

### AD-111 (2026-10-17) — Operaciones Bloque 1: Consola e Ingresos por Volúmenes (WP-C) y Unificación de Rótulos de Volumen (WP-B)

**1. Contexto y Aprobación.** En la Compuerta E2 de la FASE 12 (requerimientos de Operaciones / Cristhian), Mauricio
aprobó la ejecución inmediata del Bloque 1:
- WP-C: filtro y menú "Ingresos por Volúmenes" con búsqueda por guía, proveedor y estado. Incluye investigación de la guía 95806 (JCE) con proveedor "S.I.I. - LOS ANGELES" (D-E0-3) y propuesta de corrección sin alterar datos existentes.
- WP-B rótulos: unificar rótulos de volumen en las vistas de embarque y contenedor: "Vol. Compra (m³)" para el volumen de compra por etiqueta, "Vol. Export (m³)" para el de exportación, y "Vol. Documental (m³)" claramente distinguido.

**2. WP-C (Consola y Menú 'Ingresos por Volúmenes').**
- Se incorpora el campo `<field name="state" string="Estado"/>` en la vista de búsqueda `view_madenat_lumber_intake_console_search` de `madenat_lumber_intake`.
- Se actualiza el rótulo del filtro `type_volume` a «Ingresos por Volúmenes» con dominio `[('ingestion_type', '=', 'volume')]`.
- Se crea la acción de ventana dedicada `action_madenat_lumber_intake_console_volume` sobre `madenat.lumber.intake.console`, con dominio pre-filtrado `ingestion_type = 'volume'` y contexto `'search_default_type_volume': 1`.
- Se añade el submenú `menu_madenat_lumber_intake_volume` bajo la rama canónica `madenat_lumber_core.menu_ops_reception_cat` (Gestión de Entradas), con secuencia 2 y permiso para `madenat_lumber_core.group_madenat_operaciones`.
- Suite TDD en `madenat_lumber_intake/tests/test_volume_console_search_menu.py` (4 pruebas en verde).

**3. Causa Raíz D-E0-3 (Guía 95806 / JCE -> "S.I.I. - LOS ANGELES").**
- Hallazgo: En `GDE 95806.pdf`, el membrete del emisor (JCE) es una imagen gráfica vectorial/raster en la cabecera izquierda (`Im1`), carente de capa de texto seleccionable.
- En el recuadro DTE superior derecho (timbre electrónico de guía), se ubican: RUT (`96.547.890-6`), tipo y folio (`Nº 95806`) y la oficina tributaria del SII: `S.I.I. - LOS ANGELES`.
- `_find_emitter_company_name()` en `madenat_guia_processing.py` descartó encabezados estándar (`GUÍA`, `DESPACHO`, `ELECTRÓNICA`), pero la cadena `S.I.I. - LOS ANGELES` fue evaluada como razón social válida por no pertenecer `ANGELES` al set de palabras reservadas.
- Al no existir previamente el RUT `96.547.890-6` en la base de datos, `_resolve_or_create_supplier()` ejecutó `auto_create` creando el `res.partner` ID 2417 con nombre «S.I.I. - LOS ANGELES». Al procesar la guía 95806, el resolver por VAT asignó dicho partner.
- No se modificaron los datos en la base de datos (requisito explícito). Se presentan opciones operativas a Mauricio.

**4. WP-B rótulos (Unificación de Rótulos de Volumen).**
- Homologación completa de vistas XML en `madenat_lumber_logistics`:
  - Contenedor (`lumber_container_views.xml`): lista (`total_vol_shipment_m3` -> «Vol. Export (m³)», `total_volume_purchase_m3` -> «Vol. Compra (m³)»); formulario (labels homónimos en grupo Volúmenes y Rendimiento); grilla de lotes asignados (`volume_purchase_m3` -> «Vol. Compra (m³)», `vol_shipment_m3` -> «Vol. Export (m³)`).
  - Asistente de selección de lotes (`lumber_container_lot_wizard_views.xml`): lotes para exportación (`vol_shipment_m3` -> «Vol. Export (m³)»); grilla de selección (`volume_purchase_m3` -> «Vol. Compra (m³)», `vol_shipment_m3` -> «Vol. Export (m³)`).
  - Embarque (`lumber_export_shipment_views.xml`): pivot (`total_nominal_volume_m3` -> «Vol. Compra (m³)», `total_volume_m3` -> «Vol. Export (m³)»); totales KPIs (`total_volume_m3` -> «Vol. Export (m³)», `total_nominal_volume_m3` -> «Vol. Compra (m³)»); pestaña contenedores (`total_volume_purchase_m3` -> «Vol. Compra (m³)», `volume_m3` -> «Vol. Export (m³)»); auditoría de cálculo (`physical_volume_m3` -> «Vol. Compra (m³)», `export_volume_m3` -> «Vol. Export (m³)»); lista de embarques (`total_volume_m3` -> «Vol. Export (m³)`).
  - Imputación documental SV (`madenat_sv_imputation_views.xml`): `sv_assignment_nominal_m3` y `sv_ret_nominal_m3` claramente etiquetados como «Vol. Documental (m³)».
- Suite TDD en `madenat_lumber_logistics/tests/test_volume_labels_unification.py` (5 pruebas en verde).

**5. Versiones e Impacto.**
- `madenat_lumber_intake`: 18.0.0.15.0 -> 18.0.0.16.0
- `madenat_lumber_logistics`: 18.0.1.36.0 -> 18.0.1.37.0
- CHANGELOG actualizado en ambos módulos.
- Sin cambios en costing, reports, bitácora ni datos de negocio reales (`IMP04823`, `IMP02220`).

<!-- actualizado: 2026-10-17 — alta AD-111 (FASE 12 / Bloque 1): WP-C búsqueda y menú Ingresos por Volúmenes, causa raíz D-E0-3 JCE/S.I.I., y WP-B unificación canónica de rótulos de volumen (Vol. Compra (m³), Vol. Export (m³), Vol. Documental (m³)). `intake` 18.0.0.15.0 → 18.0.0.16.0; `logistics` 18.0.1.36.0 → 18.0.1.37.0. Versión 04 12.26.0 → 12.27.0. -->

### AD-112 (2026-10-17) — Operaciones Bloque 2: Disponibilidad Documental SV (WP-F P1–P5), Plantilla Estándar Métrica (WP-E) y Alineación Documental (WP-G)

**1. Contexto y Aprobación.**
En cumplimiento de la aprobación de Mauricio para el Bloque 2 de la FASE 12 (Requerimientos de Operaciones / Cristhian), se implementan los paquetes de trabajo WP-F (P1–P5), WP-E y WP-G en el orden estricto autorizado, bajo metodología TDD y preservando el WIP preexistente.

**2. WP-F (P1–P5) — Control de disponibilidad de etiquetas en imputación documental SV.**
Derivado de la auditoría de disponibilidad de etiquetas (`AUDITORIA_DISPONIBILIDAD_ETIQUETAS_20261015`):
- **P1 (Bloqueo preventivo de selección):** Se incorpora el campo booleano computado `asignable` en `madenat.sv.imputation.wizard.line` (`disponibilidad_estado == 'available'`). En la vista XML del asistente, la columna se oculta (`column_invisible="True"`) y el control toggle `selected` aplica `readonly="not asignable"`, impidiendo que el operador seleccione accidentalmente etiquetas sin saldo documental para una nueva operación.
- **P2 (Seleccionar todas seguro):** En `action_select_all()`, el asistente escribe `selected=True` exclusivamente sobre `line_ids.filtered('asignable')`. Si existen etiquetas omitidas por falta de saldo, se retorna una acción cliente `display_notification` de tipo advertencia (`warning`): `"%d etiqueta(s) omitida(s) por falta de saldo documental (ver pestaña «Sin disponibilidad»)"`.
- **P3 (Pestaña 'Sin disponibilidad'):** En el formulario del asistente, se añade la pestaña `<page string="Sin disponibilidad" name="unavailable_material" invisible="not_assignable_line_count == 0">` que lista en modo sólo lectura las etiquetas sin saldo documental del retorno, su causa trazable (`disponibilidad_detalle`) y el botón nativo `action_open_consuming_documents` para auditar los documentos causantes.
- **P4 (Coherencia de resumen y conteo):** Se agrega el campo `selectable_line_count` en el asistente. Se actualiza el cálculo de `not_assignable_line_count` (`available_line_count - selectable_line_count`) y se desglosa en `assigned_summary` (`"%(sel)s seleccionadas (%(unavail)s sin saldo) · %(prep)s etiquetas con reparto preparado · %(vol).3f m³ → %(sv)s"`).
- **P5 (Error nominativo al aplicar sin saldo):** En `madenat.sv.imputation`, se implementa el helper `_i2_lot_consuming_docs_detail(lot)` que consulta los documentos vigentes (borrador/pendiente/aplicada) que comprometen la capacidad de la etiqueta. Al validar el techo duro en `_i2_validate_hard_cap()` y payload en `_i2_validate_payload()`, se emite un `UserError` nominativo detallando la referencia/nombre de la etiqueta, su nominal y los documentos con sus estados y volúmenes causantes del bloqueo.
- **Cobertura TDD:** Suite `madenat_lumber_logistics/tests/test_sv_imputation_availability_p1_p5.py` (5 pruebas en verde).

**3. WP-E — Plantilla estándar PACKING_METRICO_ASERRADA y guía de llenado.**
Para proveedores sin integración automática (Arauco, JCE, BYC, Fátima, etc.) o ingreso asistido por Operaciones:
- Se crea el archivo Excel modelo `PLANTILLA_PACKING_METRICO_ASERRADA.xlsx` en `madenat_ingestion_engine/data/templates/`, con cabecera de metadatos (`CLIENTE`, `GUIA DESPACHO`, `FECHA`, `ORDEN COMPRA`), columnas homologadas al perfil `packing_metrico_aserrada` (`N°`, `CODIGO`, `PRODUCTO`, `LOTE`, `ESPESOR`, `ANCHO`, `LARGO`, `FILAS`, `COLUMNAS`, `PIEZAS`, `VOLUMEN`), formato numérico y ejemplos prácticos.
- Se implementa el script generador `data/templates/generate_packing_template.py`.
- Se redacta la guía operativa completa `madenat_ingestion_engine/docs/GUIA_LLENADO_PACKING_METRICO.md`.
- Se implementa la suite de pruebas automatizadas `madenat_ingestion_engine/tests/test_packing_metrico_template.py` (3 pruebas en verde) validando detección de perfil, metadatos y normalización de líneas.

**4. WP-G — Alineación documental y reconciliación de discrepancias heredadas.**
- **Reconciliación D-E0-1:** Se actualiza `madenat_lumber_docs/WIKI/06_SESIONES/_CAPSULA_CONTEXTO.md` declarando que las Fases 10 y 11 están implementadas y probadas en local, pendientes de verificación manual de Mauricio y de despliegue al TEST (precisando el estado real frente al desfase histórico del 70%).
- **Reconciliación D-E0-2:** Se actualiza `madenat_lumber_docs/WIKI/HOJA_RUTA_EJECUTIVA.md` sincronizándola con las decisiones AD-110, AD-111 y AD-112.
- Se actualiza `madenat_lumber_docs/CANON/05_BACKLOG.md` registrando el avance del Bloque 1 y Bloque 2 de la FASE 12.

**5. Versiones e Impacto.**
- `madenat_lumber_logistics`: 18.0.1.37.0 → 18.0.1.38.0
- `madenat_ingestion_engine`: 18.0.1.1.0 → 18.0.1.2.0
- CHANGELOG actualizado en ambos módulos.
- Sin cambios en costing, reports, bitácora ni datos de negocio reales (`IMP04823`, `IMP02220`).

<!-- actualizado: 2026-10-17 — alta AD-112 (FASE 12 / Bloque 2): WP-F P1–P5 disponibilidad documental y trazabilidad en imputación SV; WP-E plantilla estándar PACKING_METRICO_ASERRADA y guía de llenado; WP-G alineación documental (D-E0-1, D-E0-2). `logistics` 18.0.1.37.0 → 18.0.1.38.0; `ingestion` 18.0.1.1.0 → 18.0.1.2.0. Versión 04 12.27.0 → 12.28.0. -->


