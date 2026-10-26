# CORRECCIÓN MÍNIMA Y PRUEBAS — guarda de eliminación de etiqueta SV (2026-10-12)

**Origen:** diagnóstico `stock_quant_lot_id_fkey` (`READONLY_DIAGNOSTICO.md`).
**Alcance:** robustez/mensaje (**no** la causa raíz). **No** se autoriza borrar el lote ni tocar datos.
**Entorno:** LOCAL `madenat_test`. **Sin despliegue, sin tocar el TEST remoto, sin commit/push.**

---

## 1. Decisión implementada
Se implementan **las dos opciones** acordadas (una no excluye la otra: la Opción 2 da el mensaje de negocio
*antes* de tocar la BD para el caso reportado; la Opción 1 cubre **cualquier** lote y cualquier FK).

## 2. Opción 2 — guarda proactiva (`stock.lot._sv_guard_unlink()`)
Archivo: `madenat_lumber_core/models/madenat_sv_operation.py`.

Se añade, **después** de la comprobación de historial existente y **solo** para la etiqueta SV de volumen, el
mismo criterio exacto que aplica PostgreSQL (existencia de fila en `stock.quant`, aunque la cantidad sea 0):

```python
if lot.lot_flow_type == 'volume' and self.env['stock.quant'].sudo(
        ).search_count([('lot_id', '=', lot.id)]):
    raise ValidationError(_(
        'La etiqueta SV %s tiene existencias en stock y no puede '
        'eliminarse. Es el ancla de trazabilidad de la Guía %s. '
        'Registre una operación SV de reversa/regularización.'
    ) % (lot.name or lot.id,
         lot.guia_number or lot.guia_processing_id.id))
```

Garantías:
- **Se conserva intacto** el bypass test-only por marcador (`_sv_test_cleanup_allowed`) — el `return` temprano
  sigue primero.
- **No** afecta a lotes no-SV ni a la comprobación de historial previa.
- Es un **mensaje de negocio**; el invariante (no se borra) es el mismo.

## 3. Opción 1 — traducción del error de integridad (`stock.lot.unlink()`)
Archivo: `madenat_lumber_core/models/stock_lot.py`.

Se envuelve el `super().unlink()` en un **`savepoint`** (para dejar la transacción utilizable) y se traduce la
`ForeignKeyViolation` a un mensaje de negocio:

```python
try:
    with self.env.cr.savepoint():
        return super(StockLotExtended, self).unlink()
except psycopg2_errors.ForeignKeyViolation as err:
    lot = self[:1]
    raise ValidationError(_(
        'La etiqueta/lote %s tiene existencias o documentos que lo '
        'referencian y no puede eliminarse. Use la reversión o la '
        'regularización de la guía/etiqueta SV correspondiente '
        '(\u00abRebajar etiqueta SV\u00bb / \u00abRegularizar volumen de '
        'etiqueta SV\u00bb) en lugar de eliminar el registro.'
    ) % (lot.name or lot.id)) from err
```

Notas de diseño:
- Se usa **`ValidationError`** (misma familia que la traducción estándar de Odoo en `odoo/service/model.py`)
  para **no romper** aserciones existentes que esperan `ValidationError`.
- **`savepoint`**: sin él, la transacción quedaría abortada tras el error de PostgreSQL y no podría ni siquiera
  construirse el mensaje.
- **No** cambia *qué* se puede borrar: sólo el mensaje.

## 4. Pruebas
Archivo nuevo: `madenat_lumber_core/tests/test_sv_lot_unlink_guard.py` (+ alta en `tests/__init__.py`).

| # | Prueba | Qué acredita |
|---|---|---|
| 1 | `test_01_lote_sv_volumen_con_existencias_bloquea` | Opción 2: con quant → `ValidationError` de negocio (contiene «existencias») **antes** de la BD; lote y quant intactos |
| 2 | `test_02_lote_sv_volumen_sin_existencias_permitido` | El caso legítimo (sin quant ni historial) **sigue** eliminándose |
| 3 | `test_03_cleanup_test_only_intacto_con_existencias` | El bypass por marcador (`_sv_test_cleanup`) limpia lote **y** quant sin bloqueo |
| 4 | `test_04_lote_no_sv_con_existencias_traduce_el_mensaje` | Opción 1: un lote **no‑SV** con quant choca con la FK y recibe el **mensaje de negocio** |

Todas usan datos aislados (`TransactionCase` + `SvTestCommon`); no tocan la Guía 4495589 ni el lote 10215.

## 5. Versiones y metadatos
- `madenat_lumber_core` **18.0.6.6.0 → 18.0.6.7.0** (`__manifest__.py`) + entrada en `CHANGELOG.md`.
- `madenat_lumber_intake` y `madenat_lumber_logistics`: **sin cambios**.

## 6. Resultados
| Suites | Resultado |
|---|---|
| Dirigida `TestSvLotUnlinkGuard` | **4 tests → 0 failed / 0 error** (`EXIT=0`) |
| Regresión `core+intake+logistics` | **1279 tests → 6 failed / 4 error** (`EXIT=1`) |

### 6.1 Comparación con la línea base (misma corrida amplia)
| Métrica | Línea base | Con la corrección | Δ |
|---|---|---|---|
| Total | 1275 | **1279** | **+4** (las pruebas nuevas) |
| `failed` | 6 | **6** | 0 |
| `error(s)` | 4 | **4** | 0 |
| Conjunto de 10 fallos | `TestOrphanMoveCleanupSavepoint`, `TestSvEscalationSecurity` ×3, `TestGuiaPickingLink`, `TestProcessorLocations`, `TestProcessorShipmentAD89` ×3, `TestSvConcurrency` | **el MISMO** | **diff vacío ⇒ idéntico** |
| `madenat_lumber_intake` | 467 / 0 fallos | 467 / **0** | 0 |

➡️ **Cero regresiones atribuibles a la corrección**; los 10 fallos son **preexistentes** y ajenos al cambio
(limpieza de movimientos huérfanos, seguridad de escalamiento SV, vínculo de picking, ubicaciones de procesador y
concurrencia SV real). Las pruebas nuevas (`TestSvLotUnlinkGuard`, 4) **corrieron y pasaron** dentro de la regresión.

### 6.2 No mutación de datos
Verificado tras la regresión: el lote **10215 (`SV000000841`)** conserva su `write_date` (2026-10-10 21:41:48) y sus
dos quants (**7840** −40.315 / **7841** +40.315); **sin** residuos de prueba (0 marcadores, 0 lotes de prueba).
**No** se modificó ningún dato histórico.

## 7. Riesgo residual
- La Opción 2 se limita a `lot_flow_type == 'volume'`; la Opción 1 aplica a **cualquier** lote, pero **no** cambia
  *qué* se puede borrar (sólo el mensaje), por lo que el invariante es el mismo.
- Sigue vigente el comportamiento estándar de Odoo: **no hay archivado de lotes** (no existe `active`). La vía
  correcta ante un error real es la **reversión/regularización de negocio** (guía o operación SV).

## 8. Estado
- **Módulo:** `madenat_lumber_core` **18.0.6.7.0** instalado en `madenat_test`.
- **Sin commit/push/despliegue**; `madenat_lumber_intake` y `madenat_lumber_logistics` **intactos**; TEST remoto
  **sin tocar**.

