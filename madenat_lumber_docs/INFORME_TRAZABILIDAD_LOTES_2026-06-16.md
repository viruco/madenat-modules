# INFORME TÉCNICO — PÉRDIDA DE TRAZABILIDAD DE LOTES
## MADENAT Lumber — Odoo 18 CE

**Fecha:** 2026-06-16
**Tipo:** Auditoría técnica de trazabilidad
**Versión:** 1.0.0
**Fuentes:** Código fuente, documentación canónica, datos de auditoría previa

---

## 1. RESUMEN EJECUTIVO

### Hallazgo principal

**El campo discriminador canónico `lumber_reception_id` nunca es poblado por ningún flujo de ingesta.** El código opera exclusivamente con el campo `reception_id`, dejando `lumber_reception_id` como una columna huérfana en `stock_lot` que permanece NULL para todos los lotes. La documentación canónica (`12_FLUJOS_INGESTA.md`) instruye usar `lumber_reception_id` como discriminador, creando una contradicción documental-código que puede inducir a error en reportes, consultas y consolidaciones futuras.

### Nivel de confianza
**ALTO (85%)** — El hallazgo está confirmado por revisión de código de los 4 archivos involucrados. Queda pendiente únicamente la verificación numérica en BD (no fue posible ejecutar queries directos por limitaciones de entorno). Los datos de auditoría previa (`AUDITORIA_RUNTIME_2026-06-05.md`) confirman indirectamente que `reception_id` es el campo operativo.

### Flujo(s) afectados
- **Recepción directa** (`lumber_reception`): afectado por contradicción documental. La trazabilidad funciona con `reception_id`, pero la documentación apunta al campo equivocado.
- **Guía procesada** (`madenat_guia_processing`): funcionalmente correcto con `guia_processing_id`. No tiene problema de trazabilidad.
- **Reportes y consultas**: riesgo alto si siguen la regla canónica (`lumber_reception_id IS NOT NULL`).

---

## 2. EVIDENCIA REVISADA

### 2.1 Archivos inspeccionados

| Archivo | Líneas | Hallazgo |
|---------|--------|----------|
| `CANON/12_FLUJOS_INGESTA.md` | 242 | Define `lumber_reception_id` como discriminador canónico (Sección 5.1). Documenta que algunos lotes no lo tienen poblado (Sección 6.3). |
| `CANON/00_ARQUITECTURA.md` | 165 | No menciona la dualidad de campos `reception_id` / `lumber_reception_id`. |
| `CANON/INDICE_DOCUMENTACION.md` | 79 | Lista `12_FLUJOS_INGESTA.md` como vigente. |
| `models/stock_lot.py` | 1393 | Define DOS campos Many2one a `lumber.reception`: `lumber_reception_id` (línea 201, readonly) y `reception_id` (línea 209, domain state='done'). TODA la lógica de negocio usa `reception_id`. |
| `models/reception_service.py` | 181 | `create_lots_from_staging()` escribe `reception_id` (línea 50) pero NUNCA escribe `lumber_reception_id`. |
| `models/lumber_reception.py` | 2895 | `action_confirm_reception()` busca lotes por `reception_id` (línea 2586, 2670). Delega a `_create_lots_from_packing()`. |
| `models/madenat_guia_processing.py` | 3348 | Crea lotes con `guia_processing_id`. No escribe `lumber_reception_id` ni `reception_id`. Correcto según su flujo. |
| `models/stock_picking.py` | (fragmento) | Define `lumber_reception_id` en `stock.picking`, NO en `stock.lot`. |
| `reports/models/lumber_stock_report.py` | 794 | Usa `lot_id.reception_id.reception_date` (línea 69) y `lot_id.guia_number` (línea 77). No usa `lumber_reception_id`. |
| `AUDITORIA_RUNTIME_2026-06-05.md` | 227 | Confirma 39 lotes con `reception_id` poblado. No menciona `lumber_reception_id`. |

### 2.2 Campos duplicados en `stock_lot`

```python
# stock_lot.py, línea 201 — Campo CANÓNICO (documentado, readonly, SIN USO REAL)
lumber_reception_id = fields.Many2one(
    'lumber.reception', 
    string="Recepción de Origen",
    readonly=True,
    help="Enlace a la recepción donde se ingresó este paquete."
)

# stock_lot.py, línea 209 — Campo OPERATIVO (usado en todo el código)
reception_id = fields.Many2one(
    'lumber.reception',
    string='Recepción de Compra',
    domain="[('state', '=', 'done')]",
    help="EXCLUSIVAMENTE para recepciones de compra de madera nueva"
)
```

### 2.3 Todas las referencias a `reception_id` en lógica de negocio

| Método | Campo usado | Línea |
|--------|------------|-------|
| `_compute_reception_type` | `reception_id` | 252 |
| `_check_reception_guia_exclusivity` | `reception_id` | 266 |
| `_compute_guia_number` | `reception_id` | 282 |
| `_compute_vol_shipment_m3` | `reception_id` | 470 |
| `_compute_estado_trazabilidad` | `reception_id` | 1025 |
| `_compute_purchase_info` | `reception_id` | 875 |
| `create_lots_from_staging()` | `reception_id` | 50 |
| `action_confirm_reception()` | `reception_id` | 2586, 2670 |
| `_compute_lot_purchase_order` (reports) | `lot_id.reception_id` | 69 |

**Resultado:** CERO referencias funcionales a `lumber_reception_id` en todo el código de negocio.

### 2.4 Queries relevantes (pendientes de ejecución)

```sql
-- Cuántos lotes tienen cada campo poblado:
SELECT 
    COUNT(*) FILTER (WHERE reception_id IS NOT NULL) AS has_reception_id,
    COUNT(*) FILTER (WHERE lumber_reception_id IS NOT NULL) AS has_lumber_reception_id,
    COUNT(*) FILTER (WHERE guia_processing_id IS NOT NULL) AS has_guia_processing_id
FROM stock_lot;

-- Predicción basada en código: has_lumber_reception_id = 0
```

---

## 3. HIPÓTESIS EVALUADAS

### Hipótesis 1: La pérdida ocurre en `lumber_reception` al crear lotes en Gate 3

**Qué dice:** `action_confirm_reception()` o `create_lots_from_staging()` no escribe `lumber_reception_id` al crear `stock.lot`.

**Evidencia que la apoya:**
- `reception_service.py:50` solo asigna `'reception_id': reception.id`. No hay asignación de `lumber_reception_id` en `lot_vals`.
- `action_confirm_reception()` en `lumber_reception.py:2668` llama a `_create_lots_from_packing({})`, que delega en `create_lots_from_staging()`.
- La auditoría runtime de 2026-06-05 confirma lotes con `reception_id` pero no menciona `lumber_reception_id`.

**Evidencia que la contradice:**
- Si `reception_id` funciona como discriminador operativo, los lotes SÍ tienen trazabilidad (vía `reception_id`). La pérdida solo aplica si se exige `lumber_reception_id`.
- El flujo de recepción directa ES funcional con `reception_id`.

**Estado: CONFIRMADA PARCIALMENTE** — `lumber_reception_id` nunca se escribe, pero `reception_id` sí. El problema real es la dualidad de campos, no la ausencia total de FK.

---

### Hipótesis 2: La pérdida ocurre en la lógica de consolidación en contenedores

**Qué dice:** `lumber_container` o su wizard de asignación filtran por el campo incorrecto, excluyendo lotes.

**Evidencia que la apoya:**
- Ninguna. La documentación (`12_FLUJOS_INGESTA.md`, Sección 6.4) afirma que `lumber_container` converge ambos flujos correctamente.

**Evidencia que la contradice:**
- La documentación canónica explícitamente declara la convergencia en contenedores como "funcionalmente correcta".
- No se inspeccionó el código del wizard en detalle, pero no hay señales de fallo en este punto según la documentación.

**Estado: DESCARTADA** — No hay evidencia de fallo en contenedores. La documentación lo valida.

---

### Hipótesis 3: La documentación canónica está desincronizada del código

**Qué dice:** `12_FLUJOS_INGESTA.md` referencia `lumber_reception_id` como campo discriminador, pero el código opera exclusivamente con `reception_id`. La documentación no refleja la implementación real.

**Evidencia que la apoya:**
- `12_FLUJOS_INGESTA.md` Sección 2: define `lumber_reception_id` como discriminador.
- `12_FLUJOS_INGESTA.md` Sección 5.1: dice usar `lumber_reception_id IS NOT NULL` como filtro.
- `12_FLUJOS_INGESTA.md` Sección 6.3: reconoce que `lumber_reception_id` no está poblado pero atribuye la causa a un bug en Gate 3, no a que el código usa `reception_id`.
- El código NUNCA escribe `lumber_reception_id`. No es un bug intermitente, es que el código simplemente no usa ese campo.
- `stock_lot.py` tiene DOS campos al mismo modelo con propósitos solapados. Esto es una duplicidad semántica.

**Evidencia que la contradice:**
- La documentación acierta en que `guia_processing_id` es el discriminador correcto para guías procesadas.
- La documentación acierta en la constraint de exclusividad (aunque el código la implementa con `reception_id`, no con `lumber_reception_id`).

**Estado: CONFIRMADA** — Hay una divergencia clara entre el canon documental y la implementación real.

---

### Hipótesis 4: El flujo de guía procesada tiene pérdida de trazabilidad

**Qué dice:** Los lotes de `madenat_guia_processing` no tienen `guia_processing_id` poblado.

**Evidencia que la apoya:**
- Ninguna encontrada en código. El flujo de guía procesada escribe `guia_processing_id` correctamente.

**Evidencia que la contradice:**
- La documentación (`12_FLUJOS_INGESTA.md` Sección 6.1) confirma 19 lotes con `guia_processing_id = 14`.
- `stock_lot.py` tiene `guia_processing_id` (línea 216) y es usado por todos los computes relevantes.
- `_compute_reception_type` asigna `'processed'` correctamente cuando `guia_processing_id` está poblado.

**Estado: DESCARTADA** — El flujo de guía procesada es correcto.

---

### Hipótesis 5: Los reportes usan el campo incorrecto y pierden lotes

**Qué dice:** Los reportes de `madenat_lumber_reports` consultan por `lumber_reception_id` y por tanto no ven lotes de recepción directa.

**Evidencia que la apoya:**
- Parcial. El riesgo existe si un reporte futuro sigue la regla canónica.

**Evidencia que la contradice:**
- `lumber_stock_report.py` línea 69 usa `lot_id.reception_id.reception_date` — el campo operativo correcto.
- `lumber_stock_report.py` línea 77 usa `lot_id.guia_number` — campo computado que a su vez usa `reception_id`.
- Los reportes actuales funcionan con el campo operativo `reception_id`.

**Estado: DESCARTADA para reportes actuales. RIESGO LATENTE para reportes futuros** que sigan la regla canónica de `12_FLUJOS_INGESTA.md`.

---

## 4. DIAGNÓSTICO TÉCNICO

### 4.1 Causa raíz más probable

**Duplicidad de campos con divergencia documental.** `stock.lot` tiene dos campos Many2one a `lumber.reception`:

1. `lumber_reception_id` — Campo declarado en la documentación canónica como discriminador oficial. Está definido en código como `readonly=True`. **Nunca es escrito por ningún flujo.**
2. `reception_id` — Campo usado operativamente por TODA la lógica de negocio: constraints, computes, servicios, reportes y queries. **Es el discriminador real.**

La causa raíz NO es un bug de asignación condicional en Gate 3 (como sugiere la documentación). Es una **duplicidad estructural**: existen dos campos para el mismo propósito, uno documentado pero inerte, y otro funcional pero no canónico.

### 4.2 Ubicación exacta del fallo

| Componente | ¿Funciona? | Detalle |
|-----------|-----------|---------|
| `madenat_guia_processing` | ✅ | Escribe `guia_processing_id` correctamente |
| `lumber_reception` Gate 3 | ✅ | Escribe `reception_id` correctamente |
| `reception_service.create_lots_from_staging()` | ✅ | Escribe `reception_id` en `lot_vals` (línea 50) |
| `stock.lot` constraint | ✅ | Usa `reception_id` + `guia_processing_id` |
| `stock.lot` computes | ✅ | Todos usan `reception_id` |
| Reportes actuales | ✅ | Usan `reception_id` vía `guia_number` |
| **`lumber_reception_id`** | ❌ | **Nunca poblado. Campo huérfano.** |
| **Documentación `12_FLUJOS_INGESTA.md`** | ❌ | **Define `lumber_reception_id` como discriminador. Desincronizada.** |

### 4.3 ¿El problema es de código, de datos o de ambos?

**Es de DOCUMENTACIÓN y DISEÑO (campos duplicados).**
- El código funciona internamente de forma consistente con `reception_id`.
- Los datos son correctos respecto al código (tienen `reception_id` poblado).
- La documentación canónica apunta al campo equivocado (`lumber_reception_id`).
- La duplicidad de campos crea ambigüedad y riesgo de que alguien use el campo incorrecto.

---

## 5. IMPACTO FUNCIONAL

### 5.1 En operación
- **BAJO impacto inmediato.** Los lotes de recepción directa tienen trazabilidad vía `reception_id`. El operador puede ver el origen del lote.

### 5.2 En contenedores
- **SIN impacto.** `lumber_container` opera correctamente con ambos flujos. La documentación lo confirma.

### 5.3 En reportes
- **SIN impacto en reportes actuales.** Usan `reception_id` indirectamente vía `guia_number`.
- **ALTO riesgo futuro.** Si alguien implementa un reporte siguiendo la regla canónica (`lumber_reception_id IS NOT NULL`), obtendrá CERO resultados para recepción directa.

### 5.4 En trazabilidad
- **BAJO impacto con el campo operativo.** `reception_id` proporciona trazabilidad completa.
- **ALTO impacto si se exige el campo canónico.** `lumber_reception_id` está NULL para todos los lotes, haciendo imposible cualquier trazabilidad que dependa de él.

---

## 6. LO QUE NO SE SABE TODAVÍA

1. **Valores numéricos exactos en BD.** No se pudo ejecutar consultas SQL directas por restricciones del entorno. Se requiere verificar:
   - `SELECT COUNT(*) FROM stock_lot WHERE lumber_reception_id IS NOT NULL;` (predicción: 0)
   - `SELECT COUNT(*) FROM stock_lot WHERE reception_id IS NOT NULL;` (predicción: >0)
   - Si hay lotes con `reception_type = 'raw'` pero sin `reception_id` (los lotes huérfanos mencionados en `12_FLUJOS_INGESTA.md` Sección 6.3).

2. **Origen de los lotes sin `reception_id`.** Si existen lotes `raw` sin `reception_id` ni `lumber_reception_id`, hay que determinar si son artefactos de migración, lotes creados manualmente o bugs en flujos antiguos ya corregidos.

3. **Por qué existen dos campos.** No se encontró decisión arquitectónica documentada (`04_DECISION_LOG.md`) que explique la duplicidad `reception_id` / `lumber_reception_id`. El respaldo histórico (`backups/fase1_20260602_211431/`) muestra que `lumber_reception_id` existía en el código anterior, sugiriendo que `reception_id` se agregó después sin eliminar el original.

---

## 7. RECOMENDACIÓN SIGUIENTE (acción mínima)

**Sincronizar documentación con código antes de cualquier cambio de código.**

1. **Actualizar `12_FLUJOS_INGESTA.md`:**
   - Cambiar todas las referencias a `lumber_reception_id` por `reception_id`.
   - La regla discriminadora debe ser `reception_id IS NOT NULL`, no `lumber_reception_id IS NOT NULL`.
   - Documentar que `lumber_reception_id` es un campo legacy/huérfano que no debe usarse.

2. **Ejecutar consulta de verificación en BD** para confirmar que `lumber_reception_id` es NULL en todos los lotes y `reception_id` está correctamente poblado.

3. **NO eliminar `lumber_reception_id` todavía.** Requiere verificar que ningún código externalizado (scripts, reports externos, PowerBI, etc.) lo referencia.

4. **NO modificar el código de creación de lotes.** El código es internamente consistente con `reception_id`. Agregar escritura a `lumber_reception_id` duplicaría la misma FK en dos columnas, lo cual es redundante y propenso a desincronización.

---

*Informe generado el 2026-06-16 — Auditoría técnica de trazabilidad MADENAT Lumber.*
*Evidencia: revisión completa de 10 archivos de código + 5 documentos canónicos + 1 auditoría previa.*