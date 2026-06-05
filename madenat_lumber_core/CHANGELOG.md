## [Unreleased]

### Hotfix
- **[HOTFIX v4] — Búsqueda de lote tolera company_id=NULL (2026-06-04)**

  **Evidencia de BD:**
  ```sql
  SELECT id, name, product_id, company_id FROM stock_lot WHERE id = 1605;
  -- Resultado: company_id IS NULL, guia_processing_id IS NULL
  ```
  El lote `D7731 PCLAT04201253250 19846` existe en BD desde 2026-04-03 con `company_id=NULL`. Tanto la búsqueda primaria como el fallback usaban `('company_id', '=', 1)`, donde `NULL = 1` es falso en SQL — el lote nunca era encontrado. Esto forzaba la rama `create()` que disparaba la colisión UNIQUE, y el fallback repetía la misma búsqueda fallida.

  **Corrección (v4):**
  - Ambas búsquedas ahora usan `('company_id', 'in', [self.env.company.id, False])` con `order='company_id DESC'`. El `write(vals)` subsiguiente establece `company_id` correctamente, reparando lotes huérfanos.

  **Impacto:**
  - Sin cambios en `action_reopen_to_draft()`, `do_full_processing()`, `action_validate()`.
  - Sin `unlink()` de lotes — trazabilidad preservada.
  - Corrige datos legados (lotes huérfanos con company_id=NULL).

  **Validación:**
  - `py_compile` OK.
  - Pendiente: prueba funcional del ciclo completo.

- **[HOTFIX v3] — Savepoint en create() para limpiar transacción tras IntegrityError (2026-06-04)**

  **Hallazgo forense (logs 00:50–00:53):**
  - v2 sí entra al fallback: `⚠️ Colisión UNIQUE... reutilizando lote existente` aparece a las 00:53:10,980.
  - Pero 17 ms después (00:53:10,997) el error de unicidad **sigue propagándose** al usuario.
  - **Causa real:** psycopg2 requiere que una transacción que sufre `IntegrityError` haga rollback completo antes de cualquier otra operación. Aunque `except` capturaba la excepción, el cursor seguía tainted, y el `lot.search()` + `lot.write(vals)` del fallback fallaban silenciosamente, re-lanzando la misma `IntegrityError` al confirmar la transacción.

  **Corrección (v3):**
  - `_create_or_get_lot()` línea 2640: el `create()` ahora se ejecuta dentro de `with self.env.cr.savepoint():`. El savepoint aísla la colisión UNIQUE: si falla, solo se descarta ese sub-bloque y el cursor queda limpio para el fallback de re-búsqueda y `write()`.

  **Validación:**
  - `py_compile` OK.
  - Reinicio de Odoo OK.
  - Pendiente: prueba funcional del ciclo completo (procesar → reenviar a borrador → revalidar).

- **[HOTFIX v2] — _create_or_get_lot() ahora captura ValidationError (2026-06-04)**

  **Hallazgo de logs (post commit 09c870d):**
  - Las trazas muestran `✨ Creando lote D7731...` en cada reproceso, pero **nunca** aparece el log `⚠️ Colisión UNIQUE...` del fallback.
  - El error visible al usuario sigue siendo: `"Error de validación: La combinación de número de serie o lote y producto debe ser única..."`
  - **Causa real del bypass:** Odoo captura el `IntegrityError` de psycopg2 en la capa ORM (`_sql_constraints`) y lo re-lanza como `ValidationError`. Por lo tanto, nuestro `except IntegrityError` **nunca se ejecutaba** — el `create()` lanzaba `ValidationError` directamente al usuario, que es lo mismo que se veía antes del hotfix.

  **Corrección (v2):**
  - `_create_or_get_lot()` línea 2641: `except (IntegrityError, ValidationError):` — ahora captura ambas excepciones. El fallback de re-búsqueda y reutilización del lote existente se ejecutará correctamente ante colisiones UNIQUE de `_sql_constraints`.

  **Validación:**
  - `py_compile` OK.
  - Reinicio de Odoo OK.
  - Pendiente: prueba funcional del ciclo completo (procesar → reenviar a borrador → revalidar).

- **[HOTFIX v1] — _create_or_get_lot() tolera colisión de unicidad al reprocesar guía (2026-06-04)**

  **Causa raíz confirmada:**
  - `action_reopen_to_draft()` solo desvincula lotes de la guía (`guia_processing_id = False`) pero el `stock.lot` persiste en BD con su `name`, `product_id` y `company_id`.
  - Al reprocesar, `_create_or_get_lot()` hace `search(name, product_id, company_id)` — si por cualquier motivo no encuentra el lote existente, ejecuta `create()` y PostgreSQL lanza `IntegrityError` por la constraint `UNIQUE(name, product_id, company_id)` nativa de `stock.lot`.
  - Sin cambios en la lógica de `action_reopen_to_draft()` ni en `do_full_processing()` ni en `action_validate()`.

  **Cambio aplicado (v1):**
  - `_create_or_get_lot()` (línea ~2639): el `self.env['stock.lot'].create(vals)` ahora está envuelto en `try/except IntegrityError`. Si ocurre la colisión, el método invalida caché, re-busca el lote existente y lo reutiliza con `write(vals)`. Solo re-lanza la excepción si realmente no aparece.

  **Impacto:**
  - Sin cambios en `action_reopen_to_draft()`, `do_full_processing()`, `action_validate()`, ni `action_force_cancel()`.
  - Sin `unlink()` de lotes — los lotes permanecen en BD para trazabilidad.
  - Sin cambios en lógica de stock, pickings ni moves.
  - El método es ahora idempotente ante reproceso desde borrador.

  **Validación:**
  - `py_compile` OK.
  - Reinicio de Odoo OK.
  - Pendiente: prueba funcional del ciclo completo (procesar → reenviar a borrador → revalidar).

- **[HOTFIX] — Duplicados al reenviar guía a borrador (2026-06-04)**

  **Causa raíz:**
  - `_get_or_create_picking_unified()` no excluía pickings en estado `done`, permitiendo reutilizar pickings cerrados como si fueran nuevos.
  - `action_reopen_to_draft()` realizaba cancel y rename en bloque, dejando el `origin` sin modificar si `action_cancel()` fallaba en algún picking.

  **Cambios aplicados:**
  1. `_get_or_create_picking_unified()` línea 1664: search excluye ahora `done` y `cancel` → `('state', 'not in', ['cancel', 'done'])`
  2. `action_reopen_to_draft()` línea 3170: iteración individual con try/except garantiza que el rename se ejecute aunque cancel falle.

  **Impacto:**
  - Sin cambios en lógica de lotes.
  - Sin cambios en flujo de stock confirmado.
  - Sin cambios en validación de duplicados reales.

  **Validación:**
  - py_compile OK.
  - Sin tocar lotes, `action_force_cancel()`, `_cleanup_orphan_moves_guia()`, `do_full_processing()` ni `_create_or_get_lot()`.

- Corregido error `unsupported operand type(s) for +: 'float' and 'decimal.Decimal'` en procesamiento Excel (2026-06-04). Causa raíz: `get_s2s_adjustment()` retorna `Decimal` pero se usaba en aritmética con `float` en dos sitios de `madenat_guia_processing.py` sin conversión. Solución mínima: `float(ajuste_s2s)` en `_validar_y_enriquecer_lineas:2290` y `float(recargo)` en `_compute_vol_shipment_m3:512`. Sin cambios en lógica de lotes, líneas de detalle, paquetes, volúmenes ni conteos. Sintaxis OK.

- Corregido `UnboundLocalError` por sombreado de constante importada `M_TO_FT` en guía processing (2026-06-04). Causa raíz: `M_TO_FT = float(M_TO_FT)` en dos métodos (`_compute_vol_mbf:413`, `_compute_imperial_values:263`) reasignaba localmente el nombre de la constante importada desde `utils_uom.py`, causando que Python la interpretara como variable local en todo el scope. Solución mínima: renombrar variable local a `m_to_ft` en ambas funciones. Sin cambios en lógica de negocio, lotes, líneas ni paquetes. Sintaxis y reinicio de Odoo OK.

### Refactored
- TD-009: Centralizar `LUMBER_DIMENSION_MAP` en `utils_uom.py` (2026-06-04). Dict movido sin modificaciones desde `madenat_guia_processing.py:22-61` a `utils_uom.py:733`. Import extendido en `guia_processing.py:63-75`. Preparatorio para TD-010 (migración a modelos ORM configurables). 43 líneas eliminadas de `guia_processing.py`. Comportamiento funcional idéntico.

### Research
- TD-006: Investigación de parametrización de reglas comerciales (`+1/8"`, `1550.003096`, `5085.312`) — conclusión: NO parametrizable. Las 6 fuentes de evidencia (código, git log, docs, modelo de configuración) confirman que las reglas son fijas para todo MADENAT. Sin evidencia de variación por cliente/perfil/subproducto. Documentado en WIKI y CANON con condiciones de reapertura.

### Documentation
- TD-005.1: Comentario explicativo expandido en `INCH_SQ_METERS_TO_M3 = 1550.003096` documentando origen dimensional exacto (NIST), fórmula de derivación, y uso en cubicación comercial de embarque. Nota complementaria en WIKI TD-005.

### Fixed
- TD-004: Centralización de constante física universal `25.4` → `MM_PER_INCH` en `lumber_reception_mass_update.py:114`
- TD-005: Clasificación y parametrización de reglas de negocio comercial. Documentado inventario completo de constantes: `M3_DIVISOR` (1000000), `FACTOR_EMBARQUE` (1550.003), `FACTOR_BLANK` (5085.312), `MBF_DIVISOR` (12000), `S2S_WIDTH_ADJUSTMENT_INCH` (0.125). Todas ya centralizadas en `utils_uom.py`. Corrección menor: `lumber_shipment_line.py:131` usaba `1_000_000.0` literal → `float(M3_DIVISOR)`.

## [1.5.0] - 2025-12-13
### Added
- **Trazabilidad:** Nuevo campo `source_shipment_cost_line_id` en `stock.lot.cost.line` para vincular costos con su origen en embarques.