# Investigación: 3 Alertas Preexistentes Post-Update
**Fecha:** 2026-06-21 20:53

---

## Alerta 1 — `madenat_lumber_reports.view_stock_lot_search_inventory`

- **Archivo origen del `<delete>`:** `custom_addons/madenat_lumber_reports/views/menu_remapping.xml:32`
- **¿La vista existe actualmente?:** **NO** — No hay ninguna definición XML con `id="view_stock_lot_search_inventory"` en ningún módulo del proyecto. Solo aparece en el propio `<delete>` de `menu_remapping.xml`.
- **¿Es código muerto?:** **SÍ** — La vista fue eliminada en una migración anterior (Fase 4 Limpieza, relacionada con mover `location_name` de `stock.lot` a `stock.quant`). Las otras 5 vistas del mismo bloque (líneas 27-31) probablemente ya también son código muerto, pero al menos una de ellas ya fue borrada de BD exitosamente. Esta (`view_stock_lot_search_inventory`) es la que falla porque Odoo intenta borrarla y ya no existe en `ir.ui.view`.
- **Causa raíz:** El `<delete>` se carga en cada upgrade del módulo (está en `data` del `__manifest__.py`, no en `migrations/`). Una vez que la vista fue eliminada de BD en la primera ejecución, los subsiguientes upgrades fallan porque Odoo intenta borrar un registro que ya no existe. El error no aborta la carga porque Odoo captura `ValueError` en `convert.py:_tag_delete` y loguea el warning.
- **Solución propuesta:** Eliminar la línea `<delete id="view_stock_lot_search_inventory" model="ir.ui.view"/>` de `menu_remapping.xml` (y evaluar si las otras 5 líneas de delete del mismo bloque también deben eliminarse, ya que comparten la misma naturaleza).
- **Riesgo de la solución:** **BAJO** — Es una línea de limpieza que ya cumplió su propósito. No hay dependencias. Eliminarla no afecta funcionalidad. La vista ya no existe en BD ni en código.
- **Ubicación exacta del fix:** `custom_addons/madenat_lumber_reports/views/menu_remapping.xml` línea 32

**Evidencia adicional:**
- Archivo: `menu_remapping.xml` (68 líneas, carga en cada update vía `data` en `__manifest__.py`)
- Módulo: `madenat_lumber_reports` version `18.0.2.2.0`
- El módulo tiene migración `18.0.2.2.0/pre-migrate.py` (backfill de `supplier_id`) — no relacionada con este delete
- Las 5 vistas hermanas (líneas 27-31) también están en el mismo estado — se eliminaron en la misma fase pero posiblemente aún no han lanzado error (o ya fueron eliminadas exitosamente en BD)

---

## Alerta 2 — UNIQUE `madenat_guia_processing`

- **¿Constraint nueva en este update?:** **SÍ** — Introducida en commit `05d1c2c` (2026-06-16): "feat(core): align reception flow with reception_id". **Confirmado por `git log -S`** — la constraint no existía antes de este commit.
- **Duplicados encontrados:** **0** — `SELECT name, partner_id, COUNT(*) ... GROUP BY name, partner_id HAVING COUNT(*) > 1` retorna 0 filas.
- **Totales:** 1 registro en `madenat_guia_processing` (name único, combinación name+partner_id única).
- **Estados de los duplicados:** N/A — no hay duplicados.
- **¿Son datos de test o producción?:** Es un entorno `madenat_test` con solo 1 registro en la tabla.
- **⚠️ CAUSA RAÍZ CRÍTICA:** La constraint `UNIQUE(name, partner_id, company_id)` referencia la columna `company_id`, pero **la tabla `madenat_guia_processing` NO tiene columna `company_id`**. Verificado con `\d madenat_guia_processing` en PostgreSQL — la columna no existe. El modelo tampoco define `company_id` como campo explícito, ni lo hereda de ningún mixin visible (hereda de `mail.thread`, `mail.activity.mixin`, `madenat.lumber.ingest.mixin`, `validation.checklist.mixin` — ninguno provee `company_id` como campo stored en esta tabla).
- **Constraint en PostgreSQL:** **NO EXISTE** — `SELECT ... FROM pg_constraint WHERE conrelid = 'madenat_guia_processing'::regclass AND conname LIKE '%unique%'` retorna 0 filas. Odoo no pudo crear la constraint porque la columna `company_id` no existe.
- **Solución propuesta:** **OPCIÓN A (recomendada):** Corregir la constraint para que use solo columnas que existen: `UNIQUE(name, partner_id)`. Esto mantiene la intención de evitar duplicados de guía para el mismo proveedor. **OPCIÓN B:** Agregar el campo `company_id` al modelo (más invasivo, requiere migración de datos).  
  También es necesario eliminar completamente la referencia a `company_id` del comentario y del constraint definition.
- **Riesgo de la solución:** **BAJO** para Opción A (cambio de 1 línea). **MEDIO** para Opción B (requiere agregar columna, migración, y posiblemente tocar métodos que usan `self.env.company.id` en el modelo).
- **Ubicación exacta del fix:** `custom_addons/madenat_lumber_core/models/madenat_guia_processing.py` línea 734

---

## Alerta 3 — UNIQUE `lumber_reception`

- **¿Constraint nueva en este update?:** **SÍ** — Introducida en el mismo commit `05d1c2c` (2026-06-16). **Confirmado por `git log -S`**.
- **Duplicados encontrados:** **0** — `SELECT name, COUNT(*) ... GROUP BY name HAVING COUNT(*) > 1` retorna 0 filas.
- **Totales:** 6 registros, todos con name único.
- **Estados de los duplicados:** N/A — no hay duplicados.
- **¿Son datos de test o producción?:** Entorno `madenat_test` con 6 registros.
- **⚠️ CAUSA RAÍZ CRÍTICA:** **IDÉNTICO problema que Alerta 2.** La constraint `UNIQUE(name, company_id)` referencia la columna `company_id`, pero **la tabla `lumber_reception` NO tiene columna `company_id`**. Verificado con `\d lumber_reception` — la columna no existe. El modelo usa `name` como Char (no Many2one a company), y hereda de `mail.thread`, `mail.activity.mixin`, `madenat.lumber.ingest.mixin` — ninguno provee `company_id` como campo stored.
- **Constraint en PostgreSQL:** **NO EXISTE** — `SELECT ... FROM pg_constraint WHERE conrelid = 'lumber_reception'::regclass AND conname LIKE '%unique%'` retorna 0 filas. Odoo no pudo crear la constraint.
- **Solución propuesta:** **OPCIÓN A (recomendada):** Cambiar la constraint a `UNIQUE(name)` ya que ni `company_id` ni otra columna de agrupación existe. Esto es más restrictivo pero fiel a la intención: no permitir dos recepciones con el mismo número de guía. **OPCIÓN B:** Agregar `company_id` al modelo.  
  Si se elige Opción A, considerar si una constraint `UNIQUE(name)` es demasiado restrictiva para el negocio (¿puede haber dos recepciones con el mismo número de guía en distintas compañías? Con Opción A no se podría). Si se necesita soporte multi-compañía en el futuro, entonces Opción B es necesaria.
- **Riesgo de la solución:** **BAJO** para Opción A. **MEDIO** para Opción B.
- **Ubicación exacta del fix:** `custom_addons/madenat_lumber_core/models/lumber_reception.py` línea 936

---

## Matriz de decisión

| Alerta | Causa raíz | Solución | Archivos a tocar | Riesgo |
|---|---|---|---|---|
| A1 | `<delete>` de vista que ya no existe en BD, se ejecuta en cada upgrade | Eliminar línea 32 de `menu_remapping.xml` | `madenat_lumber_reports/views/menu_remapping.xml` | BAJO |
| A2 | `_sql_constraints` referencia columna `company_id` que no existe en la tabla | Cambiar `UNIQUE(name, partner_id, company_id)` → `UNIQUE(name, partner_id)` | `madenat_lumber_core/models/madenat_guia_processing.py:734` | BAJO |
| A3 | `_sql_constraints` referencia columna `company_id` que no existe en la tabla | Cambiar `UNIQUE(name, company_id)` → `UNIQUE(name)` | `madenat_lumber_core/models/lumber_reception.py:936` | BAJO |

---

## Veredicto

1. **¿Se puede resolver en un solo PR?:** **SÍ** — Son 3 archivos, 3 líneas de cambio. Todos son fixes mínimos, no rompen funcionalidad existente, y corrigen errores que actualmente son warnings no bloqueantes pero que se ejecutan en cada upgrade.

2. **¿Alguna alerta afecta a producción (`madenat_prod`) o solo a `madenat_test`?:** El comportamiento sería **idéntico en producción**:
   - A1: El `<delete>` fallaría igual en prod si la vista ya fue eliminada
   - A2: La constraint no se crearía en prod porque la columna `company_id` tampoco existe allí (mismo modelo, misma estructura de tabla)
   - A3: Ídem — la columna `company_id` no existe en `lumber_reception` en prod

3. **Observación importante para A2 y A3:** Ambas constraints fueron agregadas en el commit `05d1c2c` del 2026-06-16. El desarrollador asumió que `company_id` existía como campo en ambas tablas (probablemente por analogía con `stock.lot` que sí lo tiene), pero ninguna de las dos tablas tiene esa columna. Esto es un **error de diseño** en el commit original, no un problema de datos.

4. **Recomendación adicional:** Revisar si las otras 5 líneas de `<delete>` en `menu_remapping.xml:27-31` también deben limpiarse, ya que comparten la misma naturaleza (vistas `stock.lot` huérfanas que ya fueron eliminadas en BD).