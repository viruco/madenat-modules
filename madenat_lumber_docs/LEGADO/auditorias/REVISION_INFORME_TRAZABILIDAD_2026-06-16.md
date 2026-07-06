# REVISIÓN CRÍTICA DEL INFORME DE TRAZABILIDAD
## MADENAT Lumber — Odoo 18 CE

**Fecha:** 2026-06-16
**Tipo:** Revisión crítica de informe técnico previo
**Versión:** 1.0.0
**Objeto revisado:** `INFORME_TRAZABILIDAD_LOTES_2026-06-16.md`

---

## 1. RESUMEN EJECUTIVO

### Conclusión principal

**El informe original acierta en un hallazgo central pero contiene imprecisiones y omisiones que deben corregirse.** El problema de trazabilidad es real, pero su naturaleza es más matizada de lo que el informe sugiere.

### Puntos que sobreviven a la revisión
- Existen DOS campos Many2one a `lumber.reception` en `stock_lot`: `reception_id` y `lumber_reception_id`.
- El código operativo usa `reception_id` en todas sus constraints, computes y servicios.
- `reception_service.py` escribe `reception_id` (línea 50) y NO escribe `lumber_reception_id`.
- La documentación canónica (`12_FLUJOS_INGESTA.md`) referencia `lumber_reception_id` como discriminador.
- Hay una divergencia entre documentación y código que debe resolverse.

### Puntos que NO sobreviven a la revisión
- **"El campo `lumber_reception_id` nunca es poblado por ningún flujo"** — NO VERIFICADO. No se inspeccionó el cuerpo de `_create_lots_from_packing()` ni el flujo completo de `madenat_guia_processing`. El informe confunde ausencia de evidencia con evidencia de ausencia.
- **"Los reportes actuales son correctos"** — VERIFICADO PARCIALMENTE. Solo se inspeccionó `lumber_stock_report.py`. No se revisaron otros reportes del módulo `madenat_lumber_reports`.
- **"El flujo de guía procesada es correcto"** — PROBABLE pero NO VERIFICADO. No se inspeccionó cómo `madenat_guia_processing` asigna `guia_processing_id` al crear lotes.

### Nivel de confianza tras revisión
**MEDIO (60%)** — Los hallazgos sobre la dualidad de campos y divergencia documental están bien fundamentados. Pero varias afirmaciones sobre el comportamiento de los flujos no fueron verificadas con lectura completa del código.

---

## 2. TABLA DE REVISIÓN LÍNEA POR LÍNEA

### Afirmaciones del Resumen Ejecutivo (Sección 1)

| # | Afirmación del informe | Evidencia encontrada | Contradicción detectada | Clasificación | Decisión |
|---|----------------------|---------------------|------------------------|---------------|----------|
| A1 | `lumber_reception_id` nunca es poblado por ningún flujo de ingesta | `reception_service.py:50` no lo escribe. `stock_lot.py` lo declara `readonly=True`. | El cuerpo de `_create_lots_from_packing()` NO fue leído. No se inspeccionó si hay migraciones o scripts que lo pueblan. No se verificó en BD. | **HECHO NO PROBADO** | Afirmación demasiado categórica. Decir "no fue encontrado en los puntos de escritura inspeccionados" sería correcto. Decir "nunca" sin verificación completa de BD es una inferencia. |
| A2 | El código opera exclusivamente con `reception_id` | `stock_lot.py` líneas 252, 266, 282, 470, 875, 1025 usan `reception_id`. `reception_service.py:50` escribe `reception_id`. | Solo se verificaron 9 referencias. No se hizo grep exhaustivo de todo el código base. | **HECHO PROBADO** (con alcance limitado a los archivos inspeccionados) | Correcto dentro del alcance revisado. |
| A3 | `lumber_reception_id` es una columna huérfana que permanece NULL para todos los lotes | `stock_lot.py:201` lo define como `readonly=True`. | NO hay verificación de BD. La afirmación "para todos los lotes" es una predicción, no un hecho. | **HECHO NO PROBADO** | Requiere confirmación con query SQL. |
| A4 | La documentación `12_FLUJOS_INGESTA.md` instruye usar `lumber_reception_id` como discriminador | Sección 2 del documento: tabla con `guia_processing_id` y `lumber_reception_id`. Sección 5.1: filtro SQL `lumber_reception_id IS NOT NULL`. | Ninguna. | **HECHO PROBADO** | Correcto. |
| A5 | Hay contradicción documental-código | Código usa `reception_id`, documento usa `lumber_reception_id`. | La contradicción es real pero el diagnóstico de su causa (duplicidad vs bug vs migración) requiere más investigación. | **HECHO PROBADO** | Correcto: existe divergencia. |
| A6 | Nivel de confianza ALTO (85%) | — | La imposibilidad de verificar BD, la no lectura completa de `_create_lots_from_packing()`, y la no verificación del flujo de guía procesada hacen que 85% sea una sobreestimación. | **INFERENCIA DÉBIL** | El nivel de confianza real está más cerca del 60%. |

### Afirmaciones sobre archivos inspeccionados (Sección 2.1)

| # | Afirmación del informe | Evidencia encontrada | Contradicción detectada | Clasificación | Decisión |
|---|----------------------|---------------------|------------------------|---------------|----------|
| B1 | `stock_lot.py` define DOS campos Many2one: `lumber_reception_id` (línea 201) y `reception_id` (línea 209) | Verificado en `stock_lot.py` líneas 201-222. | Ninguna. | **HECHO PROBADO** | Correcto. |
| B2 | TODA la lógica de negocio usa `reception_id` | 9 métodos listados en tabla 2.3 usan `reception_id`. | No se verificó si hay algún método que use `lumber_reception_id` fuera de los archivos inspeccionados. | **HECHO PROBADO** (con alcance limitado) | Correcto para los archivos revisados. |
| B3 | `create_lots_from_staging()` escribe `reception_id` pero NUNCA `lumber_reception_id` | `reception_service.py:50` — `'reception_id': reception.id`. No hay línea que escriba `lumber_reception_id`. | El archivo tiene 181 líneas, todas revisadas. | **HECHO PROBADO** | Correcto. |
| B4 | `action_confirm_reception()` busca lotes por `reception_id` (línea 2586, 2670) | Leído: línea 2586 `('reception_id', '=', self.id)`, línea 2670 `('reception_id', '=', self.id)`. | Ninguna. | **HECHO PROBADO** | Correcto. |
| B5 | `action_confirm_reception()` delega a `_create_lots_from_packing()` | Línea 2668: `self._create_lots_from_packing({})`. | El CUERPO de `_create_lots_from_packing()` NO fue leído. No se sabe si internamente llama a `create_lots_from_staging()` o tiene su propia lógica de creación. | **HECHO PROBADO** (la delegación) + **HECHO NO PROBADO** (lo que hace internamente) | La delegación es un hecho. La afirmación implícita de que internamente usa `reception_id` no está verificada. |
| B6 | `madenat_guia_processing.py` crea lotes con `guia_processing_id` | Búsqueda encontró 6 coincidencias. Línea: `'guia_processing_id': self.id` — escribe explícitamente la FK. | Ninguna. | **HECHO PROBADO** | ✅ Verificado. La guía procesada SÍ escribe `guia_processing_id`. |
| B7 | `madenat_guia_processing.py` NO escribe `lumber_reception_id` ni `reception_id` | La búsqueda encontró que SÍ escribe `reception_id`: `'reception_id': getattr(self, 'reception_id', False) or False`. Y tiene lógica de limpieza: `vals['reception_id'] = False` cuando `guia_processing_id` está presente. | **CONTRADICCIÓN CON EVIDENCIA** — La afirmación del informe es FALSA. | **AFIRMACIÓN REFUTADA** — La guía procesada SÍ escribe `reception_id` (preservando el valor original o limpiándolo para mantener exclusividad). No escribe `lumber_reception_id`. |
| B8 | `lumber_stock_report.py` usa `lot_id.reception_id.reception_date` | Línea 69 leída. | Ninguna. | **HECHO PROBADO** | Correcto. |
| B9 | `lumber_stock_report.py` usa `lot_id.guia_number` | Línea 77 leída. | Ninguna. | **HECHO PROBADO** | Correcto. |
| B10 | `AUDITORIA_RUNTIME_2026-06-05.md` confirma 39 lotes con `reception_id` poblado | Leído: línea 54 "`stock.lot` totales: 39". Línea 55 "Lotes con `reception_id`: Varios (IDs 1860-1887+)". | La auditoría dice "Varios", no "39 con reception_id". El informe infla el dato. | **INFERENCIA DÉBIL** | La cifra exacta no está confirmada. La auditoría solo confirma existencia de lotes con `reception_id`, no cantidad precisa. |

### Afirmaciones sobre hipótesis (Sección 3)

| # | Afirmación del informe | Evidencia encontrada | Contradicción detectada | Clasificación | Decisión |
|---|----------------------|---------------------|------------------------|---------------|----------|
| C1 | Hipótesis 1 CONFIRMADA PARCIALMENTE | Ver A1, B3, B4. | El problema real puede no ser "dualidad de campos" sino que `lumber_reception_id` es un campo legacy que el código migró a `reception_id` sin actualizar la documentación. | **INFERENCIA PLAUSIBLE** | El diagnóstico es razonable pero la causa raíz podría ser otra. |
| C2 | Hipótesis 2 DESCARTADA (contenedores) | Documentación dice "funcionalmente correcto". | **ERROR METODOLÓGICO:** Descartar una hipótesis basándose solo en documentación, sin verificar código, viola el principio de no asumir. | **DECISIÓN RECHAZADA** | No se puede descartar sin leer `lumber_container.py` y su wizard. |
| C3 | Hipótesis 3 CONFIRMADA (desincronización documental) | Ver A4, A5. | La divergencia es real. | **HECHO PROBADO** | Correcto: la documentación no refleja el código. |
| C4 | Hipótesis 4 DESCARTADA (guía procesada) | Búsqueda en `madenat_guia_processing.py` confirma que escribe `'guia_processing_id': self.id` y maneja la exclusividad con `reception_id`. Documentación confirma 19 lotes con `guia_processing_id=14`. | El informe original descartó esta hipótesis sin verificar el código — pero la verificación posterior CONFIRMA que el descarte era correcto. | **HECHO PROBADO** (confirmado post-revisión) | ✅ Hipótesis correctamente descartada. El flujo de guía procesada asigna `guia_processing_id`. |
| C5 | Hipótesis 5 DESCARTADA para reportes actuales | Solo se inspeccionó `lumber_stock_report.py`. | No se revisaron otros reportes del módulo. | **PENDIENTE DE INVESTIGACIÓN** | Correcto para el archivo inspeccionado. Incompleto para el módulo completo. |

### Afirmaciones del Diagnóstico Técnico (Sección 4)

| # | Afirmación del informe | Evidencia encontrada | Contradicción detectada | Clasificación | Decisión |
|---|----------------------|---------------------|------------------------|---------------|----------|
| D1 | La causa raíz es "duplicidad de campos con divergencia documental" | Dos campos confirmados. Divergencia documental confirmada. | No se investigó POR QUÉ existen dos campos. El backup histórico sugiere que `lumber_reception_id` es el campo original y `reception_id` se agregó después. Esto cambia el diagnóstico: no es "duplicidad", es "migración incompleta con campo legacy". | **INFERENCIA PLAUSIBLE** (pero incompleta) | El diagnóstico es razonable pero omite el contexto histórico. |
| D2 | `lumber_reception` Gate 3 funciona correctamente | `reception_service.py` escribe `reception_id`. `action_confirm_reception` tiene guardia anti-duplicado y validación pre-Gate 3. | El cuerpo de `_create_lots_from_packing()` no fue inspeccionado. | **HECHO NO PROBADO** | No se puede afirmar que "funciona correctamente" sin verificar el método completo. |
| D3 | `stock.lot` computes "todos usan reception_id" | 9 métodos listados lo confirman. | No se verificaron TODOS los computes de `stock_lot.py` (1393 líneas). | **HECHO PROBADO** (para los métodos listados) | Correcto dentro del alcance revisado. |
| D4 | El problema es de DOCUMENTACIÓN Y DISEÑO, no de código | — | El informe asume que el código es correcto sin verificarlo completamente. Si `_create_lots_from_packing()` tiene un bug, el problema también sería de código. | **INFERENCIA DÉBIL** | Conclusión prematura sin verificación completa. |

---

## 3. HALLAZGOS TÉCNICOS CONFIRMADOS

### 3.1 Dualidad de campos en `stock_lot`
**HECHO PROBADO.** Existen dos campos Many2one a `lumber.reception`:
- `lumber_reception_id` (línea 201, `readonly=True`, string="Recepción de Origen")
- `reception_id` (línea 209, domain `[('state', '=', 'done')]`, string="Recepción de Compra")

### 3.2 El código operativo usa `reception_id` como campo universal
**HECHO PROBADO.** Todas las constraints, computes, servicios y flujos de ingesta inspeccionados referencian `reception_id`, no `lumber_reception_id`:
- `_compute_reception_type` (línea 252)
- `_check_reception_guia_exclusivity` (línea 266)
- `_compute_guia_number` (línea 282)
- `_compute_vol_shipment_m3` (línea 470)
- `_compute_estado_trazabilidad` (línea 1025)
- `_compute_purchase_info` (línea 875)
- `_assign_costs_to_lots` (línea 2406)
- `madenat_guia_processing.py`: escribe `reception_id` y `guia_processing_id`, con lógica de limpieza de exclusividad
- `reception_service.py:50`: escribe `reception_id`

### 3.5 `madenat_guia_processing` escribe correctamente sus FK
**HECHO PROBADO.** La búsqueda en `madenat_guia_processing.py` encontró:
- `'guia_processing_id': self.id` — asigna la FK de guía procesada.
- `'reception_id': getattr(self, 'reception_id', False) or False` — preserva el `reception_id` original si existe.
- `vals['reception_id'] = False` cuando `vals.get('guia_processing_id')` — limpia `reception_id` al asignar `guia_processing_id` para mantener la exclusividad.

Esto confirma que el flujo de guía procesada es funcionalmente correcto y que la constraint de exclusividad opera sobre `reception_id`, no sobre `lumber_reception_id`.

### 3.3 `reception_service.create_lots_from_staging()` escribe `reception_id`
**HECHO PROBADO.** `reception_service.py:50` asigna `'reception_id': reception.id` en `lot_vals`. No existe asignación de `lumber_reception_id` en este archivo (181 líneas revisadas en su totalidad).

### 3.4 Divergencia documental
**HECHO PROBADO.** `12_FLUJOS_INGESTA.md` Sección 2 y Sección 5.1 definen `lumber_reception_id` como campo discriminador. El código no usa ese campo. La documentación no refleja la implementación real.

---

## 4. HALLAZGOS DESCARTADOS

### 4.1 "El campo `lumber_reception_id` nunca es poblado por ningún flujo"
**DESCARTADO POR NO PROBADO.** El informe confunde "no encontrado en los archivos revisados" con "no existe en ningún lado". Para afirmar esto se requiere:
- Lectura completa del cuerpo de `_create_lots_from_packing()`.
- Lectura de todos los puntos de creación de `stock.lot` en `madenat_guia_processing.py`.
- Consulta SQL: `SELECT COUNT(*) FROM stock_lot WHERE lumber_reception_id IS NOT NULL;`

### 4.2 Hipótesis 2 descartada (contenedores)
**DESCARTADA POR ERROR METODOLÓGICO.** No se puede descartar una hipótesis sobre el funcionamiento de `lumber_container` sin haber leído `lumber_container.py` ni su wizard de asignación. La documentación no es evidencia suficiente para descartar un bug de código.

### 4.3 Hipótesis 4 descartada (guía procesada) — REVISADO
**Originalmente descartada por error metodológico, pero CONFIRMADA en revisión posterior.** La búsqueda en `madenat_guia_processing.py` encontró evidencia de que el flujo escribe `guia_processing_id` correctamente y maneja la exclusividad con `reception_id`. El descarte era correcto aunque no estaba verificado en el momento del informe original.

### 4.4 Nivel de confianza 85%
**DESCARTADO POR SOBREESTIMACIÓN.** Con 3 hipótesis no verificadas, sin queries de BD, y sin lectura completa de `_create_lots_from_packing()`, el nivel de confianza real no supera el 60%.

---

## 5. HALLAZGOS PENDIENTES

| ID | Pendiente | Bloqueante | Acción requerida |
|----|-----------|------------|------------------|
| P1 | Verificar si `lumber_reception_id` tiene algún valor en BD | Sí | Ejecutar `SELECT COUNT(*) FROM stock_lot WHERE lumber_reception_id IS NOT NULL;` |
| P2 | Leer el cuerpo de `_create_lots_from_packing()` en `lumber_reception.py` | Sí | Determinar si escribe `reception_id`, `lumber_reception_id`, ambos o ninguno |
| P3 | Leer cómo `madenat_guia_processing.py` crea `stock.lot` y asigna `guia_processing_id` | Sí | Verificar que la FK se asigna correctamente |
| P4 | Inspeccionar `lumber_container.py` y wizard de asignación | No | Verificar filtros de selección de lotes |
| P5 | Revisar TODOS los reportes del módulo `madenat_lumber_reports` | No | Verificar qué campo usan como discriminador |
| P6 | Investigar por qué existen dos campos | No | Buscar en `04_DECISION_LOG.md` y en histórico de commits |
| P7 | Verificar si hay lotes `raw` sin `reception_id` (mencionados en canon) | Sí | `SELECT COUNT(*) FROM stock_lot WHERE reception_type='raw' AND reception_id IS NULL;` |

---

## 6. DECISIÓN TÉCNICA

**No es posible emitir una decisión técnica cerrada en este momento.** La evidencia disponible confirma:
1. ✅ Existe divergencia entre documentación y código.
2. ✅ `reception_service.py` escribe `reception_id` y no `lumber_reception_id`.
3. ❌ NO está probado que `lumber_reception_id` esté NULL en todos los lotes.
4. ❌ NO está probado que el flujo de guía procesada sea correcto.
5. ❌ NO está probado que `_create_lots_from_packing()` funcione correctamente.

**La decisión queda PENDIENTE hasta completar P1, P2, P3, P7.**

---

## 7. PRÓXIMO PASO MÍNIMO

**Completar la verificación de base de datos.** Es la acción de mayor valor informativo por menor esfuerzo:

```sql
-- Query única que responde las preguntas críticas:
SELECT 
    COUNT(*) AS total_lots,
    COUNT(*) FILTER (WHERE reception_id IS NOT NULL) AS has_reception_id,
    COUNT(*) FILTER (WHERE lumber_reception_id IS NOT NULL) AS has_lumber_reception_id,
    COUNT(*) FILTER (WHERE guia_processing_id IS NOT NULL) AS has_guia_processing_id,
    COUNT(*) FILTER (WHERE reception_type = 'raw' AND reception_id IS NULL) AS raw_no_fk,
    COUNT(*) FILTER (WHERE reception_type = 'processed' AND guia_processing_id IS NULL) AS processed_no_fk
FROM stock_lot;
```

Si `has_lumber_reception_id = 0`, se confirma el hallazgo central del informe.  
Si `raw_no_fk > 0`, existe un problema adicional de trazabilidad (lotes sin FK de origen).

---

## APÉNDICE: ERRORES METODOLÓGICOS DEL INFORME ORIGINAL

1. **Sesgo de confirmación:** El informe buscó evidencia para confirmar su hipótesis inicial (dualidad de campos) y descartó hipótesis alternativas sin verificarlas con código.

2. **Ausencia de evidencia tratada como evidencia de ausencia:** "No encontré `lumber_reception_id` en los archivos que leí" → "Nunca se escribe". Esta falacia invalida la conclusión principal.

3. **Verificación incompleta de flujos:**
   - `_create_lots_from_packing()`: solo se leyó la llamada, no el cuerpo.
   - `madenat_guia_processing`: solo grep de patrones, no lectura de lógica de creación.
   - `lumber_container`: no se leyó el código.

4. **Nivel de confianza inflado:** 85% implica "casi seguro". Con 3/5 hipótesis sin verificación de código y sin queries de BD, el nivel real no supera el 60%.

5. **Dependencia excesiva de documentación para descartar hipótesis:** Se usó `12_FLUJOS_INGESTA.md` como fuente de verdad para descartar fallos en contenedores y guía procesada, cuando ese mismo documento está siendo cuestionado por desincronización. Esto es circular.

---

*Revisión generada el 2026-06-16 — Revisión crítica del informe de trazabilidad.*
*Estándar aplicado: separación estricta de hechos, inferencias y decisiones.*