# Flujo de Dimensiones Comerciales: Recepción → Stock

**Módulo:** `madenat_lumber_core`  
**Versión:** 1.0  
**Fecha:** 2026-05-31  
**Estado:** ✅ Documentado y operativo  
**Autor:** Auditoría técnica TD-007

---

## 1. Propósito

Documentar el flujo completo de propagación de dimensiones comerciales (visuales y medidas de compra) desde la etapa de Recepción/Comercial hasta los lotes de stock (`stock.lot`), asegurando que Stock refleje los datos validados por el operador sin reinterpretarlos.

Este documento sirve como referencia única para desarrollo, QA y soporte funcional del sistema de ingesta de madera.

---

## 2. Alcance

### Cubierto por este documento
- Propagación de dimensiones visuales desde `lumber.reception.line` a `stock.lot` durante la confirmación de recepción.
- Backfill histórico para lotes creados antes del fix de propagación.
- Reglas de negocio que determinan qué datos se propagan y cuándo.

### No cubierto por este documento
- Flujo de guía procesada (`madenat_guia_processing`) — tiene su propia documentación.
- Cálculo de volúmenes de exportación (MBF, m³ S2S).
- Costeo y asignación de precios a lotes.
- Movimientos de stock (picking, transferencias).

---

## 3. Arquitectura del flujo

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO DE DIMENSIONES COMERCIALES              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Excel (packing list) ──┐                                       │
│                         ▼                                       │
│                  ┌───────────────┐                              │
│                  │    Parser     │  Extrae dimensiones crudas   │
│                  │  (reception_  │  del Excel                   │
│                  │   parser)     │                              │
│                  └───────┬───────┘                              │
│                          │                                      │
│                          ▼                                      │
│                  ┌───────────────┐                              │
│                  │    Staging    │  lumber.reception.line       │
│                  │ (Pestaña 1:   │  - thickness (mm) físico     │
│                  │  Físico)      │  - width (mm) físico         │
│                  │               │  - length (m) convertido     │
│                  │               │  - length_input_raw (valor)  │
│                  │               │  - lengthuom (ft/m/mm)       │
│                  │               │  - thickness_visual (texto)  │
│                  │               │  - width_visual (texto)      │
│                  └───────┬───────┘                              │
│                          │                                      │
│              Usuario valida y consolida                         │
│                          │                                      │
│                          ▼                                      │
│                  ┌───────────────┐                              │
│                  │   Comercial   │  MISMO modelo:               │
│                  │ (Pestaña 2:   │  lumber.reception.line       │
│                  │  Inventario)  │  - subproduct_id (usuario)   │
│                  │               │  - thickness_nominal (ajuste)│
│                  │               │  - width_nominal (ajuste)    │
│                  │               │                              │
│                  │  Campos visuales se recalculan               │
│                  │  automáticamente vía _compute_visual_defaults│
│                  └───────┬───────┘                              │
│                          │                                      │
│              Exportación lee de aquí (Pestaña 3)               │
│                          │                                      │
│                          ▼                                      │
│              ┌───────────────────────────┐                      │
│              │  Confirmar Recepción      │                      │
│              │  action_confirm_reception()│                      │
│              │    ↓                       │                      │
│              │  _create_lots_from_packing()│                     │
│              │    ↓                       │                      │
│              │  LumberReceptionService.   │                      │
│              │  create_lots_from_staging()│                      │
│              └───────────┬───────────────┘                      │
│                          │                                      │
│                          ▼                                      │
│                  ┌───────────────┐                              │
│                  │   Stock Lot   │  stock.lot                   │
│                  │ (Pestaña 4:   │  - espesor_mm (de thickness) │
│                  │  Stock        │  - ancho_mm (de width)       │
│                  │  Generado)    │  - largo_m (de length)       │
│                  │               │  - espesor_inch_frac ← visual│
│                  │               │  - ancho_inch_frac ← visual  │
│                  │               │  - thickness_visual ← visual │
│                  │               │  - width_visual ← visual     │
│                  │               │  - length_ft ← raw (si ft)   │
│                  └───────────────┘                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Principio rector:** Cada capa consume los datos de la capa anterior sin reinterpretarlos. Comercial es la fuente de verdad para todas las dimensiones visuales y nominales.

---

## 4. Modelos involucrados

| Modelo | Rol en el flujo | ¿Escribe? | ¿Lee? |
|---|---|---|---|
| `lumber.reception.line` | **Fuente de verdad** — staging + comercial consolidado | Parser, usuario, `_compute_visual_defaults` | Exportación, confirmación de recepción |
| `stock.lot` | **Consumidor** — persiste dimensiones para logística | `reception_service.create_lots_from_staging()` | Vistas de contenedor, Stock Generado |
| `madenat.guia.processing` | Fuente alternativa para lotes procesados (no reception) | `guia_processing._create_or_get_lot()` | — |
| `madenat.reception.parser` | Extractor de datos crudos del Excel | Parsea Excel → staging | — |

---

## 5. Campos y mapeo

### 5.1 Campos propagados desde `lumber.reception.line` a `stock.lot`

| Campo destino (`stock.lot`) | Campo origen (`lumber.reception.line`) | Tipo | Condición | Ejemplo |
|---|---|---|---|---|
| `espesor_mm` | `thickness` | Float (mm) | Siempre | `39.69` |
| `ancho_mm` | `width` | Float (mm) | Siempre | `92.07` |
| `largo_m` | `length` | Float (m) | Siempre | `4.88` |
| `espesor_inch_frac` | `thickness_visual` | Char (texto) | Si hay valor | `"1 9/16"` |
| `ancho_inch_frac` | `width_visual` | Char (texto) | Si hay valor | `"3 5/8"` |
| `thickness_visual` | `thickness_visual` | Char (texto) | Si hay valor | `"1 9/16"` |
| `width_visual` | `width_visual` | Char (texto) | Si hay valor | `"3 5/8"` |
| `length_ft` | `length_input_raw` | Float (pies) | Solo si `lengthuom == 'ft'` | `16.0` |

### 5.2 Campos NO propagados (existen en origen pero no se copian a lote)

| Campo en staging | Razón |
|---|---|
| `thickness_nominal` | Dimensión pactada en OC, no dimensión física del lote |
| `width_nominal` | Idem |
| `thickness_nominal_frac` | Derivado del nominal, solo visual en Comercial |
| `width_nominal_frac` | Derivado del nominal, solo visual en Comercial |
| `length_input_raw` (cuando uom != ft) | No tiene campo equivalente en lote |
| `lengthuom` | No existe campo equivalente en `stock.lot` |
| `length_nominal` | Dimensión comercial, no física del lote |
| `vol_purchase_m3` | Se copia como `volumen_m3` (stock real), no como purchase |

---

## 6. Reglas de negocio

1. **Comercial es la fuente de verdad.** Todas las dimensiones visuales que llegan al lote provienen de los datos consolidados en la pestaña Comercial de la recepción.

2. **Stock no reinterpreta.** `stock.lot` recibe y persiste los valores tal como están en la línea de staging consolidada. No aplica conversiones ni redondeos propios.

3. **No se sobrescriben valores existentes.** El backfill histórico solo rellena campos vacíos. Nunca modifica datos ya poblados.

4. **`length_ft` solo para perfiles imperiales.** El campo `length_ft` se propaga únicamente cuando `lengthuom == 'ft'` (perfil f5085 Blanks Clear). Para perfiles métricos permanece vacío.

5. **Los campos visuales son texto.** `thickness_visual` y `width_visual` son campos Char que almacenan la representación legible por humanos (ej: `"1 9/16"`, `"6/4"`). No son valores numéricos.

6. **`espesor_inch_frac` y `ancho_inch_frac` son redundantes con visuales.** Ambos apuntan al mismo origen (`thickness_visual` / `width_visual`). Se mantienen por compatibilidad con vistas y consultas existentes.

---

## 7. Casos normales (lotes nuevos, post-fix)

### Ejemplo: Recepción de Blanks Clear, guía 97183

1. **Excel ingresa:** Paquete A1M2605458 con espesor `1.5625"`, ancho `3.625"`, largo `16 ft`.
2. **Parser convierte:**
   - `thickness` = 39.69 mm (1.5625 × 25.4)
   - `width` = 92.07 mm (3.625 × 25.4)
   - `length` = 4.88 m (16 × 0.3048)
   - `length_input_raw` = 16.0, `lengthuom` = 'ft'
   - `thickness_visual` = "1 9/16", `width_visual` = "3 5/8"
3. **Usuario valida en Comercial:** Asigna subproducto "Rough", revisa nominales.
4. **Confirmar recepción:** `create_lots_from_staging()` crea el lote con todos los campos propagados.
5. **Resultado en `stock.lot`:**

   | Campo | Valor |
   |---|---|
   | `espesor_mm` | 39.69 |
   | `ancho_mm` | 92.07 |
   | `largo_m` | 4.88 |
   | `espesor_inch_frac` | "1 9/16" |
   | `ancho_inch_frac` | "3 5/8" |
   | `thickness_visual` | "1 9/16" |
   | `width_visual` | "3 5/8" |
   | `length_ft` | 16.0 |

### Perfiles métricos (f1550, metric)

El flujo es idéntico pero `length_ft` permanece vacío porque `lengthuom != 'ft'`. Las dimensiones visuales siguen propagándose normalmente.

---

## 8. Casos históricos (lotes pre-fix)

### Situación

Los lotes creados por `reception_service.create_lots_from_staging()` **antes del commit d59e33b** (2026-05-31) no recibieron los campos visuales. El código original solo propagaba dimensiones físicas (mm/m):

```python
# ANTES (gap):
lot_vals = {
    'espesor_mm': line.thickness,
    'ancho_mm': line.width,
    'largo_m': line.length,
    # ❌ Faltaban: espesor_inch_frac, ancho_inch_frac,
    #             thickness_visual, width_visual, length_ft
}
```

### Síntoma

En la pestaña "Stock Generado" de recepciones históricas, las columnas E (espesor fracción), A (ancho fracción) y L (ft) aparecían vacías, aunque los datos existían correctamente en `lumber.reception.line`.

### Resolución

Los lotes pre-fix se recuperan mediante el script de backfill (sección 9). Los lotes nuevos **no requieren backfill** — el flujo actual propaga correctamente todos los campos.

---

## 9. Backfill histórico

### Propósito

Rellenar los campos visuales vacíos en lotes pre-fix, usando como fuente los datos consolidados en `lumber.reception.line`.

### Ubicación

`madenat_lumber_core/scripts/backfill_lot_visual_dimensions.py`

### Campos que rellena

| Campo destino (`stock.lot`) | Fuente (`lumber.reception.line`) |
|---|---|
| `espesor_inch_frac` | `thickness_visual` |
| `ancho_inch_frac` | `width_visual` |
| `thickness_visual` | `thickness_visual` |
| `width_visual` | `width_visual` |
| `length_ft` | `length_input_raw` (solo si `lengthuom == 'ft'`) |

### Criterio de operación

- **Solo rellena campos vacíos** (NULL, `''` o `0.0`). Nunca sobrescribe valores existentes.
- **Solo procesa lotes de recepción** (`reception_id != False` y `guia_processing_id == False`).
- **Requiere línea de staging matching** — si no encuentra una línea con el mismo `lot_name` y `reception_id`, omite el lote con warning.

### Ejecución

```bash
# Preview (sin escritura)
docker exec -it odoo18_app python3 -c "
import odoo; odoo.tools.config.parse_config(['-d','<DB>','--stop-after-init'])
env = odoo.api.Environment(odoo.registry('<DB>').cursor(), odoo.SUPERUSER_ID, {})
import sys; sys.path.insert(0, '/mnt/extra-addons/madenat_lumber_core/scripts')
from backfill_lot_visual_dimensions import preview_backfill
candidates = preview_backfill(env)
env.cr.close()
print(f'Candidatos pendientes: {len(candidates)}')
"

# Aplicar cambios
docker exec -it odoo18_app python3 -c "
import odoo; odoo.tools.config.parse_config(['-d','<DB>','--stop-after-init'])
registry = odoo.registry('<DB>')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    import sys; sys.path.insert(0, '/mnt/extra-addons/madenat_lumber_core/scripts')
    from backfill_lot_visual_dimensions import backfill_lot_visual_dimensions
    result = backfill_lot_visual_dimensions(env, dry_run=False)
    cr.commit()
    print(result)
"
```

### Idempotencia

El script es idempotente: puede ejecutarse múltiples veces sin efecto adverso, ya que solo escribe campos vacíos.

---

## 10. Validaciones y pruebas

### En UI

1. Abrir una recepción confirmada (`lumber.reception`).
2. Ir a la pestaña "Stock Generado".
3. Verificar que las columnas **E** y **A** muestran fracciones (ej: "1 9/16", "3 5/8") para lotes f5085.
4. Activar la columna opcional **L (ft)** desde el selector de columnas y verificar que muestra el valor en pies para lotes f5085.
5. Ir a la pestaña "Exportación" y verificar que las columnas **Espesor (Trader)** y **Ancho (Trader)** coinciden con las de Stock Generado.

### En base de datos

```sql
-- Verificar lotes con campos visuales vacíos (deberían ser 0 post-backfill)
SELECT l.name, l.espesor_inch_frac, l.ancho_inch_frac, l.length_ft,
       rl.thickness_visual, rl.width_visual, rl.length_input_raw, rl.lengthuom
FROM stock_lot l
LEFT JOIN lumber_reception_line rl ON rl.reception_id = l.reception_id AND rl.lot_name = l.name
WHERE l.reception_id IS NOT NULL
  AND l.guia_processing_id IS NULL
  AND (l.espesor_inch_frac IS NULL OR l.espesor_inch_frac = ''
       OR l.ancho_inch_frac IS NULL OR l.ancho_inch_frac = '');

-- Verificar coherencia entre staging y lote (guía específica)
SELECT l.name,
       l.espesor_inch_frac AS lote_E, rl.thickness_visual AS staging_E,
       l.ancho_inch_frac AS lote_A, rl.width_visual AS staging_A,
       l.length_ft AS lote_Lft, rl.length_input_raw AS staging_Lraw
FROM stock_lot l
JOIN lumber_reception_line rl ON rl.reception_id = l.reception_id AND rl.lot_name = l.name
WHERE l.reception_id = <reception_id>
ORDER BY l.name;
```

---

## 11. Riesgos y consideraciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| El backfill no encuentra línea de staging para un lote | Baja | Medio (lote queda sin visuales) | El script omite con warning; revisar manualmente |
| Un lote tiene visuales incorrectos en staging | Baja | Alto | El backfill no corrige datos erróneos, solo rellena vacíos |
| Nueva recepción con profile f5085 y lengthuom != 'ft' | Muy baja | Bajo | `length_ft` quedará vacío; es comportamiento correcto |
| El operador modifica visuales en staging después de confirmar | Baja | Alto | El snapshot inmutable (Gate 3) captura el estado al momento de confirmar |

---

## 12. Criterios de aceptación

Para considerar el flujo de dimensiones como operativo:

- [ ] Todo lote nuevo creado por `action_confirm_reception()` tiene `espesor_inch_frac`, `ancho_inch_frac`, `thickness_visual`, `width_visual` poblados (si el staging los tenía).
- [ ] Todo lote nuevo f5085 tiene `length_ft` poblado con el valor de `length_input_raw`.
- [ ] Todo lote nuevo con `lengthuom != 'ft'` tiene `length_ft` vacío (False/NULL).
- [ ] La pestaña Stock Generado muestra E y A con fracciones para lotes f5085.
- [ ] Los lotes pre-fix fueron backfilleados y no tienen campos visuales vacíos (o tienen justificación documentada).
- [ ] El script de backfill es idempotente y puede ejecutarse sin efecto adverso.

---

## 13. Checklist de mantenimiento futuro

| Tarea | Frecuencia | Responsable |
|---|---|---|
| Ejecutar preview de backfill en producción para detectar lotes pendientes | Mensual | Soporte |
| Verificar que nuevas recepciones propagan visuales correctamente | Cada release | QA |
| Revisar logs de backfill para detectar lotes sin línea de staging matching | Después de cada ejecución | Soporte |
| Actualizar este documento si se agregan nuevos campos al mapeo | Según cambio | Desarrollo |

---

## Lo que este sistema NO hace

- **No convierte** dimensiones entre sistemas de unidades al propagar. Si el staging tiene `lengthuom == 'ft'`, `length_ft` recibe el valor raw sin conversión. No se crea `length_ft` para perfiles métricos.
- **No recalcula** visuales en el lote. Los campos `thickness_visual` y `width_visual` en `stock.lot` son stored text, no computed. Su valor es el que tenía staging al momento de confirmar.
- **No propaga** nominales (`thickness_nominal`, `width_nominal`) al lote. Esos campos existen en `stock.lot` (`espesor_nominal_mm`, `ancho_nominal_mm`) pero nunca se llenan desde el flujo de recepción.
- **No sincroniza** cambios posteriores en staging hacia lotes ya creados. El snapshot es unidireccional: staging → lote, una sola vez al confirmar.
- **No aplica** a lotes creados por guía procesada (`madenat_guia_processing`). Ese flujo tiene su propia lógica de propagación.
