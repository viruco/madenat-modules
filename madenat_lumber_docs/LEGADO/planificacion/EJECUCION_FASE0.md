# EJECUCIÓN FASE 0 — MADENAT Lumber
## Arranque inmediato + cierre DF-01 + control por checkpoints
### Derivado de GUIA_OPERATIVA_IMPLEMENTACION.md (2026-06-05)

**Fecha:** 2026-06-05
**Tipo:** Plan de trabajo inmediato para el equipo técnico en DEV
**Regla de ejecución:** Lo no bloqueado se hace ya. Lo bloqueado no se fuerza. Todo avance deja evidencia.
**Entorno:** DEV — madenat_test (Docker: odoo18_app + odoo18_db)

---

# 1. MAPA DE ARRANQUE INMEDIATO

## 1.1 Objetivo operativo de la Fase 0

Reducir deuda técnica, verificar configuraciones base y preparar el terreno para que —cuando DF-01 se resuelva— la Fase 1 (desbloqueo runtime) se ejecute sin fricción y en ~6h continuas.

## 1.2 Acciones ejecutables hoy

| # | Acción | Esfuerzo | Tipo | Depende de | Paralelizable |
|---|--------|----------|------|------------|---------------|
| A-17 | Hardcodes `25.4` → `MM_PER_INCH` | 1h | Código | Nada | Sí |
| A-13 | Verificar seed `lumber.export.formula` | 0.5h | SQL | Nada | Sí |
| A-09 | Agregar `account_id` a `stock.lot.cost.line` | 1.5h | Código | Nada | Sí |
| A-19 | Test suite `madenat_guia_processing` | 12h | Código | Nada | Sí (developer independiente) |
| A-11 | Verificar pipeline `vol_shipment_m3` | 3h | Diagnóstico | Datos de embarque existentes | Sí |

**Total Fase 0: 18h** (12h de A-19 pueden correr en paralelo completo).

## 1.3 Orden recomendado de ejecución

```
HOY ─── A-13 (0.5h) → A-17 (1h) → A-09 (1.5h)
           │
           └── A-19 (12h, en paralelo, otro developer)
           └── A-11 (3h, solo si hay contenedores con lotes)

BLOQUEADO ─── A-02 a A-07 (6 acciones, 6h) → requieren DF-01
```

## 1.4 Qué queda bloqueado por DF-01

| Bloqueado | Qué es | Por qué |
|-----------|--------|---------|
| A-02 | Asignar `wood_cost_usd > 0` | Sin definición del origen del dato, no se sabe qué valor asignar |
| A-03 | Crear booking + contenedor | Depende de A-02 |
| A-04 | Vincular booking a CD | Depende de A-03 |
| A-05 | `action_apply_costs()` | Depende de A-04 |
| A-06 | Verificar `stock.landed.cost` | Depende de A-05 |
| A-07 | `button_validate()` → `account.move` | Depende de A-06 |

**No forzar ninguna de estas 6 acciones.** Si se intenta sin DF-01, los valores serán arbitrarios y requerirán re-trabajo.

---

# 2. PLAN DE EJECUCIÓN DE FASE 0

## A-13 — Verificar seed data de `lumber.export.formula`

| Campo | Valor |
|-------|-------|
| **Propósito** | Confirmar 3 perfiles de fórmula activos (f5085, f1550, metric) |
| **Dependencia** | Ninguna |
| **Archivo/Modelo** | `lumber.export.formula` / seed: `ingestion_seed_fase3.xml` |
| **Tipo** | Validación SQL + carga manual si falta |
| **Esfuerzo** | 0.5h |

**Pasos concretos:**

1. Conectarse a PostgreSQL del contenedor:
```bash
docker exec odoo18_db psql -U odoo -d madenat_test
```

2. Ejecutar:
```sql
SELECT id, profile, formula_kind, active FROM lumber_export_formula ORDER BY profile;
```

3. Si hay 3 filas con `active=t` → **cierre inmediato.** No hacer nada más.

4. Si faltan, cargar desde Odoo shell:
```bash
docker exec -it odoo18_app odoo shell -d madenat_test
```
```python
formulas = [
    {'profile': 'f5085', 'formula_kind': 'blank_clear', 'unit_mode': 'imperial_feet',
     'principal_factor': 5085.312, 'deduction_factor': 0.0625, 's2s_adjustment_mode': 'none'},
    {'profile': 'f1550', 'formula_kind': 's2s_imperial', 'unit_mode': 'imperial_meters',
     'principal_factor': 1550.003, 'deduction_factor': 0.0, 's2s_adjustment_mode': 'per_width'},
    {'profile': 'metric', 'formula_kind': 'metric_direct', 'unit_mode': 'metric_mm',
     'principal_factor': 1000000.0, 'deduction_factor': 0.0, 's2s_adjustment_mode': 'none'},
]
for f in formulas:
    if not env['lumber.export.formula'].search([('profile', '=', f['profile'])]):
        env['lumber.export.formula'].create({**f, 'mbf_divisor': 12000.0, 'active': True})
env.cr.commit()
```

**Evidencia esperada:** Output de `SELECT profile, active FROM lumber_export_formula` con 3 filas `active=t`.

**Criterio de aceptación:** 3 registros activos.

---

## A-17 — Reemplazar hardcodes `25.4` por `MM_PER_INCH`

| Campo | Valor |
|-------|-------|
| **Propósito** | Centralizar constantes de conversión imperial |
| **Dependencia** | Ninguna |
| **Archivos** | `lumber_shipment_line.py:78,123`, `lumber_reception_mass_update.py:114`, `utils_uom.py:132` |
| **Tipo** | Reemplazo de literales |
| **Esfuerzo** | 1h |

**Pasos concretos:**

1. **`lumber_shipment_line.py`** (`custom_addons/madenat_lumber_logistics/models/`):
   - Agregar import al inicio del archivo:
     ```python
     from odoo.addons.madenat_lumber_core.models.utils_uom import MM_PER_INCH
     ```
   - Línea ~78: `line.lot_id.ancho_mm / 25.4` → `line.lot_id.ancho_mm / MM_PER_INCH`
   - Línea ~123: `adjusted_width_inch * 25.4` → `adjusted_width_inch * MM_PER_INCH`

2. **`lumber_reception_mass_update.py`** (`custom_addons/madenat_lumber_core/wizard/`):
   - Agregar import:
     ```python
     from ..models.utils_uom import MM_PER_INCH
     ```
   - Línea ~114: `return round(inches * 25.4, 2)` → `return round(inches * MM_PER_INCH, 2)`

3. **`utils_uom.py`** (`custom_addons/madenat_lumber_core/models/`):
   - Línea ~132: `float(decimal_value) * 25.4` → `float(decimal_value) * float(MM_PER_INCH)`

4. Verificar limpieza:
```bash
grep -rn "25\.4" custom_addons/madenat_lumber_core/models/ custom_addons/madenat_lumber_logistics/models/
```
Debe aparecer **solo** `MM_PER_INCH = 25.4` en `utils_uom.py`.

5. Ejecutar tests de regresión:
```bash
docker exec odoo18_app odoo -d madenat_test -u madenat_lumber_core,madenat_lumber_logistics --test-enable --stop-after-init --log-level=test 2>&1 | grep -E "FAIL|ERROR"
```

**Troubleshooting:** Si el import `from odoo.addons.madenat_lumber_core.models.utils_uom import MM_PER_INCH` falla en `lumber_shipment_line.py`, usar ruta relativa al addon: `from odoo.addons.madenat_lumber_core.models.utils_uom import MM_PER_INCH`.

**Evidencia esperada:** Output del grep mostrando solo `MM_PER_INCH = 25.4`. Tests pasando.

**Criterio de aceptación:** Cero hardcodes `25.4` fuera de `utils_uom.py`. Tests sin FAIL.

---

## A-09 — Agregar `account_id` a `stock.lot.cost.line`

| Campo | Valor |
|-------|-------|
| **Propósito** | Permitir imputación contable por tipo de costo |
| **Dependencia** | Ninguna |
| **Archivo/Modelo** | `stock.lot.cost.line` — `custom_addons/madenat_lumber_core/models/stock_lot_cost_line.py` |
| **Tipo** | Patch de modelo + vista XML |
| **Esfuerzo** | 1.5h |

**Pasos concretos:**

1. Abrir `stock_lot_cost_line.py`. Agregar después de los campos existentes:
```python
account_id = fields.Many2one(
    'account.account',
    string='Cuenta Contable',
    help="Cuenta contable para imputar este costo. Si se deja vacío, Odoo usará "
         "la cuenta de inventario del producto (property_stock_account_input)."
)
```

2. Verificar si existe archivo de vista `stock_lot_cost_line_views.xml` en `custom_addons/madenat_lumber_core/views/`. Si existe, agregar el campo. Si no existe, heredar la vista nativa de Odoo:
```xml
<record id="view_stock_lot_cost_line_form_inherit" model="ir.ui.view">
    <field name="name">stock.lot.cost.line.form.inherit</field>
    <field name="model">stock.lot.cost.line</field>
    <field name="inherit_id" ref="stock_landed_costs.view_stock_lot_cost_line_form"/>
    <field name="arch" type="xml">
        <xpath expr="//field[@name='amount_usd']" position="after">
            <field name="account_id"/>
        </xpath>
    </field>
</record>
```

3. Actualizar módulo:
```bash
docker exec odoo18_app odoo -d madenat_test -u madenat_lumber_core --stop-after-init
```

4. Verificar en BD:
```sql
SELECT column_name FROM information_schema.columns
WHERE table_name='stock_lot_cost_line' AND column_name='account_id';
```

**Evidencia esperada:** Captura del formulario de `stock.lot.cost.line` mostrando el campo `account_id`. Query SQL confirmando la columna.

**Criterio de aceptación:** Columna `account_id` existe en BD. Campo visible en UI.

---

## A-19 — Test suite para `madenat_guia_processing`

| Campo | Valor |
|-------|-------|
| **Propósito** | Cobertura de tests para modelo de 3465 líneas actualmente sin tests |
| **Dependencia** | Ninguna |
| **Archivo** | Nuevo: `custom_addons/madenat_lumber_core/tests/test_guia_processing.py` |
| **Tipo** | Desarrollo de tests |
| **Esfuerzo** | 12h |

**Casos mínimos (12):**

| TC | Caso | Qué valida |
|----|------|------------|
| TC01 | Crear guía en `draft` | Estado inicial correcto |
| TC02 | `action_verify_data()` | Parseo de staging |
| TC03 | `action_assign_commercial_defaults()` | Nominales asignados |
| TC04 | `action_process_from_staging()` | Staging → lotes |
| TC05 | `do_full_processing()` | `stock.lot` con dimensiones |
| TC06 | `action_validate()` | Picking + movimientos |
| TC07 | Flujo `draft → verified → processed → validated` | State machine completo |
| TC08 | `action_force_cancel()` | Cancelación segura |
| TC09 | `unlink()` restringe a `draft`/`cancelled` | Protección de borrado |
| TC10 | Cálculo `vol_comercial`, `vol_fisico`, diferencias | Precisión de volúmenes |
| TC11 | `_sync_purchase_order_lines()` | Sincronización OC |
| TC12 | `_get_or_create_picking_unified()` | No duplica pickings |

**Registro en `tests/__init__.py`:**
```python
from . import test_guia_processing
```

**Ejecución:**
```bash
docker exec odoo18_app odoo -d madenat_test -u madenat_lumber_core --test-enable --stop-after-init --log-level=test 2>&1 | grep -E "test_guia|FAIL"
```

**Nota:** Esta acción puede asignarse a un developer independiente y correr en paralelo con TODO el resto del plan. No tiene dependencia alguna.

**Evidencia esperada:** Output con 12 tests PASS.

**Criterio de aceptación:** ≥ 12 tests, todos PASS. Archivo en el repositorio.

---

## A-11 — Verificar pipeline `vol_shipment_m3`

| Campo | Valor |
|-------|-------|
| **Propósito** | Confirmar cálculo de volumen de embarque en lotes |
| **Dependencia** | Requiere contenedores con lotes asignados |
| **Archivos** | `stock_lot.py`, `lumber_shipment_line.py` |
| **Tipo** | Diagnóstico SQL |
| **Esfuerzo** | 3h (incluyendo posible fix) |

**Precheck:**
```sql
SELECT lc.id, lc.name, COUNT(lclr.stock_lot_id) AS lotes
FROM lumber_container lc
JOIN lumber_container_lot_rel lclr ON lc.id = lclr.lumber_container_id
GROUP BY lc.id, lc.name;
```

- Si `lotes = 0` para todos → **acción no ejecutable aún.** Cerrar como "pendiente de datos" y retomar tras A-03.
- Si `lotes > 0` → continuar.

**Diagnóstico:**
```sql
SELECT sl.id, sl.name, sl.vol_shipment_m3, sl.volumen_m3
FROM stock_lot sl
JOIN lumber_container_lot_rel lclr ON sl.id = lclr.stock_lot_id
WHERE sl.vol_shipment_m3 IS NULL OR sl.vol_shipment_m3 = 0;
```

Si hay filas, revisar `_compute_vol_shipment_m3` en `lumber_shipment_line.py`:
- Verificar `@api.depends`
- Verificar que las dimensiones de embarque (`ancho_embarque`, `largo_embarque`) están pobladas en `lumber.shipment.line`

**Evidencia esperada:** Query mostrando `vol_shipment_m3 > 0` para lotes en contenedores.

**Criterio de aceptación:** Lotes en embarque tienen `vol_shipment_m3 > 0`. Si no hay datos, documentar como pendiente.

---

# 3. CIERRE DE DF-01

## 3.1 Enfoque para resolver la decisión

DF-01 es la **única decisión que bloquea la Fase 1.** Resolverla es la acción de mayor impacto en todo el plan.

## 3.2 Información a recopilar

| Dato | Fuente | Pregunta |
|------|--------|----------|
| ¿Existe `purchase.order` por cada recepción? | `SELECT reception_id, order_id FROM lumber_reception WHERE state='done'` | ¿Siempre hay OC vinculada? |
| ¿El `price_unit` de la OC refleja el costo real? | `purchase.order.line` → `price_unit` | ¿El precio de compra es confiable como costo base? |
| ¿Se parsea el costo desde el PDF de guía de despacho? | `madenat_guia_processing._parse_dispatch_pdf` | ¿El parser ya extrae datos financieros? |
| ¿El operador conoce el costo y puede ingresarlo manualmente? | Preguntar a Operaciones | ¿Hay capacidad operativa para ingreso manual? |

## 3.3 Criterios de decisión

| Opción | Fuente | Ventaja | Desventaja | Cuándo elegirla |
|--------|--------|---------|------------|-----------------|
| A | `purchase.order.line.price_unit × volumen_m3` | Automático, sin intervención manual | Puede no reflejar costos adicionales en origen | Si toda recepción tiene OC y el precio unitario es el costo real |
| B | PDF de guía de despacho parseado | Dato documental, trazable | Requiere que el parser funcione y los PDFs estén disponibles | Si los PDFs ya se adjuntan y contienen datos financieros |
| C | Ingreso manual por operador | Control total del valor | Depende de disciplina operativa | Si el costo varía por lote y no hay fuente automática confiable |

**Recomendación técnica:** Empezar con Opción A (automático desde OC) como default, con posibilidad de override manual. Esto permite avanzar hoy y refinar después.

## 3.4 Cómo documentar la decisión

1. Agregar entrada en `CANON/08_COSTEO.md` §1.2:
```markdown
### 1.2 Fuente de verdad para wood_cost_usd (DF-01 — resuelto 2026-06-XX)

**Decisión:** [Opción elegida]
**Fundamento:** [Razón]
**Implementación:** El script de asignación (A-02) tomará el dato de [fuente].
**Excepciones:** [Si aplica]
```

2. Agregar entrada en `CANON/04_DECISION_LOG.md`:
```markdown
### AD-XX — Origen de wood_cost_usd (DF-01)
- **Fecha:** 2026-06-XX
- **Decisión:** [Opción]
- **Impacto:** Desbloquea Fase 1 (6 acciones). Define fuente de verdad para costo base en reporte de valorización.
```

## 3.5 Acciones que desbloquea

Una vez resuelta DF-01, se desbloquean **6 acciones en cascada** que se ejecutan en ~6h continuas:

```
A-02 (1h) → A-03 (1.5h) → A-04 (0.5h) → A-05 (0.5h) → A-06 (0.5h) → A-07 (0.5h)
                                                                                      │
                                                                          HITO H1: account.move posted
```

---

# 4. CHECKPOINTS DE CONTROL DE CALIDAD

Los checkpoints son puertas de decisión. **No se avanza sin evidencia.**

## 4.1 Checkpoints de Fase 0

| CP | Tras | Evidencia requerida | Si falta | Acción |
|----|------|---------------------|----------|--------|
| **CP-0.1** | A-13 | `SELECT profile, active FROM lumber_export_formula` → 3 activos | < 3 activos | Ejecutar script de carga manual |
| **CP-0.2** | A-17 | `grep -rn "25\.4"` → solo `MM_PER_INCH = 25.4` | Otros hardcodes | Corregir el archivo faltante |
| **CP-0.3** | A-09 | `SELECT column_name FROM information_schema.columns WHERE table_name='stock_lot_cost_line' AND column_name='account_id'` → 1 fila | Columna no existe | Revisar actualización del módulo |
| **CP-0.4** | A-19 | ≥ 12 tests PASS | Tests FAIL | Corregir tests antes de continuar |
| **CP-0.5** | A-11 | `vol_shipment_m3 > 0` en lotes con contenedor O documentación de "pendiente de datos" | Datos no disponibles | Marcar como pendiente, no bloquea |

## 4.2 Checkpoint de transición Fase 0 → Fase 1

**CP-TRANSICION:** Todos los CP-0.1 a CP-0.5 cerrados + DF-01 documentada en CANON.

| Condición | Estado |
|-----------|--------|
| A-13 cerrado | ☐ |
| A-17 cerrado | ☐ |
| A-09 cerrado | ☐ |
| A-19 ≥ 12 tests (o en progreso con avance documentado) | ☐ |
| A-11 cerrado o documentado como pendiente | ☐ |
| DF-01 documentada en `CANON/08_COSTEO.md` y `CANON/04_DECISION_LOG.md` | ☐ |

**Si todas las casillas están marcadas → Fase 1 autorizada.**

## 4.3 Qué falla detiene el avance

| Falla | Detiene | Hasta que |
|-------|---------|-----------|
| A-17 introduce error en tests | Fase 0 | Tests pasen de nuevo |
| A-09 no crea la columna en BD | Fase 0 | Se verifique migración del módulo |
| DF-01 sin respuesta | Fase 1 completa | Negocio responda o se adopte default técnico |
| A-19 con tests FAIL | Fase 1 (si afecta módulo core) | Tests corregidos |

---

# 5. GESTIÓN DE RIESGO

## 5.1 Riesgos de avanzar sin DF-01

| Riesgo | Nivel | Consecuencia | Tolerable |
|--------|-------|-------------|-----------|
| `wood_cost_usd` se asigna con criterio equivocado | Alto | Reporte muestra costos que no reflejan la realidad del negocio | **No.** Requiere reasignación y recálculo |
| Se fuerza A-02 con valor arbitrario | Alto | El `account.move` se genera con montos incorrectos | **Solo si se documenta como temporal y se recalcula después** |
| El negocio decide otra fuente después de Fase 1 | Medio | Reasignar `wood_cost_usd` + re-ejecutar A-05 a A-07 (~2h) | **Sí**, si se acepta el re-trabajo |

**Regla:** No avanzar A-02 sin DF-01 resuelta o default técnico explícitamente aceptado y documentado.

## 5.2 Riesgos técnicos de Fase 0

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|------------|---------|------------|
| A-17 rompe imports cross-addon | Baja | Medio — `lumber_shipment_line.py` en logistics importando desde core | Probar import en shell antes de commit: `docker exec odoo18_app odoo shell -d madenat_test -c "from odoo.addons.madenat_lumber_core.models.utils_uom import MM_PER_INCH; print(MM_PER_INCH)"` |
| A-09 vista XML con xpath incorrecto | Media | Bajo — el campo no se muestra pero sí existe en BD | Verificar vista tras update. Si no aparece, ajustar xpath |
| A-19 tests lentos (3465 líneas a cubrir) | Alta | Bajo — no bloquea otras acciones | Priorizar 6 tests核心 (TC01, TC04, TC05, TC06, TC07, TC08). El resto puede completarse en siguientes iteraciones |

## 5.3 Riesgos tolerables vs no tolerables

| Riesgo | Tolerable | Razón |
|--------|-----------|-------|
| A-11 no ejecutable por falta de datos | ✅ Sí | No bloquea nada. Se retoma tras A-03 |
| A-19 incompleto (< 12 tests) | ✅ Sí | 6 tests核心 son suficientes para continuar |
| DF-01 sin respuesta > 48h | ⚠️ Con condiciones | Solo si se adopta Opción A como default técnico documentado |
| A-17 rompe tests existentes | ❌ No | Debe corregirse antes de continuar |
| A-09 no persiste en BD | ❌ No | Indica error de migración del módulo |

---

# 6. CONCLUSIÓN EJECUTIVA

## 6.1 ¿La Fase 0 puede comenzar de inmediato?

**Sí.** Las 4 acciones principales (A-13, A-17, A-09, A-19) no tienen dependencias y pueden ejecutarse hoy. A-11 requiere datos que pueden no existir aún; se diagnostica y se documenta.

## 6.2 Siguiente paso más importante

**Cerrar DF-01.** Es la única decisión que desbloquea la Fase 1 y el 31% de las acciones del plan. Sin ella, el sistema no puede generar valores monetarios reales. Se recomienda:

1. **Hoy:** Enviar las preguntas de §3.2 al negocio.
2. **Mañana:** Reunión de 30 min para decidir.
3. **Tras decisión:** Documentar en CANON y ejecutar A-02 a A-07 en secuencia.

## 6.3 Criterio para pasar a Fase 1

Todos los checkpoints CP-0.1 a CP-0.5 cerrados + DF-01 documentada en CANON.

## 6.4 Regla de ejecución

> **Lo no bloqueado se hace ya. Lo bloqueado no se fuerza. Todo avance deja evidencia.**

---

*Documento generado: 2026-06-05 — basado en GUIA_OPERATIVA_IMPLEMENTACION.md*
*Alcance: Fase 0 + cierre DF-01 + control por checkpoints*