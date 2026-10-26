# RESULTADOS DE IMPLEMENTACIÓN (aislada) — control de guía ya ingresada cross-model

> Implementado y probado **exclusivamente en aislamiento**. El entorno activo y la
> guía 33154 **NO** se modificaron.

## 1. Alcance e integridad

| Elemento | Valor |
|---|---|
| Árbol modificado | **Sólo** `INCIDENTE_GUIA_15183_20261007/workcopy/addons` (copia, montada `:ro`) |
| Árbol activo `custom_addons/` | **Sin cambios** (hashes abajo) |
| Base de pruebas | `repro_inc_15183_20261007` (aislada) |
| Contenedor | one-shot `--no-http --workers=0 --max-cron-threads=0`, salida `0` |

Hashes del árbol **activo** (idénticos a los del diagnóstico):
`reception_parser.py 816081f1…`, `reception_workflow.py 3df39636…`,
`madenat_guia_processing.py 98a4caea…`.

Hashes del árbol **corregido** (workcopy):
`reception_parser.py 38eefa25…`, `reception_workflow.py ec70f0c2…`,
`madenat_guia_processing.py b8a0b55a…`.

## 2. Cambio (diff mínimo: ver `DIFF_MINIMO.patch`)

**`reception_parser.py` — `_check_guide_duplicate`** (punto único): la búsqueda de
`lumber.reception` y de `madenat.guia.processing` ahora distingue **modelo propio**
(`exclude_model`) vs **cruzado**. En el ámbito **cruzado**:
- exige **emisor conocido** (`partner_id`) y lo compara (`supplier_id` en Recepción,
  `partner_id` en Guía): bloquea sólo si coincide (identidad = número + emisor);
- si el emisor se **desconoce**, **no** bloquea cross-model (captura incompleta
  conservada; se revalida al completar).

**`madenat_guia_processing.py`** — los dos llamadores de **bloqueo**
(`_check_guide_identity_duplicate` y `_check_guide_identity_duplicate_on_create`)
pasan `cross_model=True` (ya pasan `partner_id`).

**`reception_workflow.py`** — `_check_duplicate_and_warn` (bloqueo) pasa
`cross_model=True` y `partner_id=reception.supplier_id.id or None`.

Recordatorios preservados: AJUSTE A (captura incompleta), revalidación al completar
identidad, exclusión por **modelo+registro** (`exclude_id`/`exclude_model`), aviso
no bloqueante de homónimo (emisor distinto).

## 3. Correspondencia `supplier_id` ↔ `partner_id` (comprobada)

- Ambas FK apuntan a `res.partner` por `id` (recepción `supplier_id`, guía
  `partner_id`); en el incidente idénticas (`1052`). La comparación es por `id`.
- **Registros distintos del mismo emisor:** **[V]** se detectó un caso real de
  **dos `res.partner` con el mismo RUT** `77066489-6` → ids `664` y `676`
  (`SELECT vat, count(*) … GROUP BY vat HAVING count(*)>1`).
  → **Riesgo residual documentado:** si el mismo emisor se resuelve a dos
  `res.partner` distintos entre flujos, la comparación por `partner_id` **no**
  confirmaría la identidad. **No** se añadió coincidencia por RUT (sería una regla
  nueva); se propone como decisión separada (ver `PLAN_APLICACION.md §D`).

## 4. Pruebas (52 tests, `0 failed, 0 error(s)`, contenedor `exit 0`)

| Suite | Qué cubre | Resultado |
|---|---|---|
| `TestGuideDuplicateRegression15183` (nueva) | `E1` (filas reales), `NG1` (emisor distinto), **`R1`/`R2` (deben pasar)** | **PASS** |
| `TestGuideDuplicateIngest` (corregida) | `test_03` (cross-model mismo emisor **bloquea**), `test_28` (ambos sentidos), `test_08b` (exclusión por modelo), `test_29` (aviso homónimo) | **PASS** |
| `TestGuideDuplicateWarnings` (corregida) | `w1`–`w10` (avisos, no repetición, atomicidad, contrato) | **PASS** |
| `TestDuplicateValidation` | 8 pruebas históricas de C1 (recepción) | **PASS** |

### Escenarios exigidos
- **Ambos órdenes:** Sentido 1 (Recepción→Procesado) y Sentido 2 (Procesado→
  Recepción vía C1 con identidad) — `test_03`, `test_28`.
- **Cabecera/staging sin stock:** `R1`/`R2` (draft/verified, sin lotes) y `E1`.
- **Relectura:** `test_15` (relectura del propio documento) y `w5` (no repite aviso).
- **Emisor distinto permitido:** `NG1`, `test_03`, `test_28`, `test_04`.
- **Usuario operativo sin superusuario:** acciones bajo prueba con
  `with_user(u_ops)` (grupo `group_madenat_operaciones`).

### Pruebas corregidas (antes asumían «homónimo por modelo»)
- `test_03_cross_model_homonym_not_blocked` → `test_03_cross_model_same_issuer_blocks`.
- `test_28_cross_model_symmetric_not_blocked` → `..._blocks_same_issuer`.
- `test_08b` (emisores distintos para poder coexistir) y `test_29` (emisor distinto
  en el homónimo), `w2`/`w5`/`w8` (emisor distinto). **No** se cambiaron expectativas
  salvo lo exigido por la corrección ratificada.

Logs: `logs/iso_run_fixed.log`, `logs/iso_run_fixed_summary.txt`.

## 5. Reproducir

```bash
bash INCIDENTE_GUIA_15183_20261007/run_iso.sh
```
`run_iso.sh` ejecuta las 4 suites contra `repro_inc_15183_20261007` con el workcopy `:ro`.
