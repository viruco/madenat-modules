# RESULTADO DE APLICACIÓN — `madenat_test` (2026-10-07)

Aplicación del artefacto `INCIDENTE_GUIA_15183_20261007/DIFF_MINIMO.patch` al entorno
local `madenat_test`, con gate previo, respaldo verificado y ventana controlada.

## 1. Gate — reconstrucción verificada (PASE)

Sobre una **copia limpia** del árbol activo (`/tmp/recon_gate_20261007`) se aplicó el
parche (`patch -p1`) y se copió el test nuevo. Resultado:
- `patch` aplicó **6 archivos sin rechazos** (`*.rej`/`*.orig` = ninguno).
- **`diff -rq` árbol reconstruido vs artefacto probado → IDÉNTICO** (excluyendo `__pycache__`).
- Los **7 archivos** (hash SHA-256) coinciden uno a uno con el artefacto que aprobó
  las 52 pruebas.

**Inventario (1 módulo · 7 archivos):**

| # | Archivo (`madenat_lumber_core/…`) | Origen |
|---|---|---|
| 1 | `models/reception_parser.py` | parche |
| 2 | `models/reception_workflow.py` | parche |
| 3 | `models/madenat_guia_processing.py` | parche |
| 4 | `tests/__init__.py` (import del test nuevo) | parche |
| 5 | `tests/test_guide_duplicate_ingest.py` | parche |
| 6 | `tests/test_guide_duplicate_warnings.py` | parche |
| 7 | `tests/test_guide_dup_regression_15183.py` | **nuevo** (no en el parche) |

**Módulos a actualizar:** sólo **`madenat_lumber_core`** (los dependientes
`madenat_lumber_intake`, `_logistics`, `_costing`, `madenat_toll_processing`
heredan sin cambios de código → **no** requieren `-u`).

## 2. Respaldo verificado (antes de escribir)

`backups/INCIDENTE_GUIA_15183_20261007_182354/`

| Artefacto | Tamaño | Verificación |
|---|---|---|
| `code_custom_addons.tar.gz` (código, incl. cambios locales) | 26 216 122 B | `gzip -t` **OK** |
| `madenat_test.dump` (`pg_dump -Fc`) | 11 355 196 B | magic `PGDMP` **OK**; `pg_restore --list` = 610 × `TABLE DATA` |
| `filestore_madenat_test.tar.gz` | 21 225 654 B | `gzip -t` **OK** |

SHA-256: `code…=0420096750b3c1ea…`, `filestore…=5938871cefe32f0c…`,
`dump…=47fb5ca160bb995f…`.

## 3. Hashes (antes → después)

| Archivo (`models/…`) | Antes (activo) | Después (= artefacto) |
|---|---|---|
| `reception_parser.py` | `816081f1d083f78e…` | `38eefa25f99e2a2e…` |
| `reception_workflow.py` | `3df39636518b68a5…` | `ec70f0c21d4848fb…` |
| `madenat_guia_processing.py` | `98a4caeaf5638b5b…` | `b8a0b55ac96be39c…` |

Los 7 archivos activos coinciden **exactamente** con el artefacto probado.

## 4. Actualización (ventana controlada)

1. `odoo18_app` detenido.
2. Parche + test aplicados al árbol activo (`custom_addons`).
3. One-shot `-u madenat_lumber_core` sobre `madenat_test`
   (`--no-http --workers=0 --max-cron-threads=0 --stop-after-init`): **exit 0**,
   `Modules loaded`, `Registry loaded in 33.5s`, **0 `ERROR/CRITICAL/Traceback`**.
4. `odoo18_app` reiniciado.

`ir_module_module`: `madenat_lumber_core` = `installed`, `18.0.6.5.0`,
`write_date 2026-10-07 21:25:27`. Dependientes: `installed` (4/4).
Log: `logs/update_madenat_test.log`.

## 5. Servicios

- `odoo18_app` **Up**; `GET /web/login` → **HTTP 200**.
- Log post-reinicio: sin `ERROR/CRITICAL` (sólo WARNING de plantillas `@t-esc`
  de Odoo, preexistentes).

## 6. Comprobaciones NO destructivas sobre el activo (`odoo shell`, rollback)

Sin escrituras (`env.cr.rollback()`); datos reales intactos.

| Comprobación | Resultado |
|---|---|
| Código cargado (`inspect.getsource`) contiene el nuevo guard | **True** |
| Firma/llamada canónica preservada | **True** |
| `_check_guide_duplicate('15183', partner=1052, cross_model=True, raise_on_match=False)` | `('lumber.reception', 1369)` — **encuentra la Recepción** |
| `raise_on_match=True` **sin emisor** (rama cruzada) | **no bloquea**, retorna `None` (identidad incompleta) |
| `raise_on_match=True` **mismo emisor** | **bloquea** (`UserError`) |

Las "pruebas mutantes" (suite de regresión) se mantienen **en aislamiento**; no se
ejecutaron contra `madenat_test`.

## 7. Estado Git

- Repo raíz: `custom_addons`. **HEAD `e302c488321c276af7e07f1abeecc8bc261a89f4`
  sin cambios** (no commit/push).
- Modificados (`M`): `models/madenat_guia_processing.py`, `models/reception_parser.py`,
  `models/reception_workflow.py`, `tests/__init__.py`.
- No rastreados (`??`): `tests/test_guide_dup_regression_15183.py`,
  `tests/test_guide_duplicate_ingest.py`, `tests/test_guide_duplicate_warnings.py`
  (estos dos últimos ya eran nuevos desde el fix previo).

## 8. Registros históricos

- Guía **33154**: `verified`, `partner 1052`, **13 líneas**, **0 lotes** — **intacta**.
- Recepción **1369**: `verified`, `supplier 1052` — **intacta**.
- ACL, CANON y datos históricos: **sin cambios**. Sin comparación por RUT; sin
  cambios de concurrencia.

## 9. Límites pendientes (declarados)

1. **Identidad por RUT (residual):** existe ≥1 emisor con dos `res.partner` del
   mismo RUT (`77066489-6` → `664`, `676`); la comparación por `partner_id` no los
   unifica. Requiere decisión separada.
2. **Momento de la comprobación en la ruta de Recepción:** el pipeline valida antes
   de resolver el proveedor; la confirmación cruzada Recepción→Guía aplica cuando el
   proveedor ya está poblado.
3. **Concurrencia real:** no cubierta (search secuencial).
4. **Actualización de CANON:** presentada aparte (`PROPUESTA_CANON_12_5_2.md`);
   **no** editada en esta intervención.
5. **Reversión:** restaurar los 6 archivos del `models/`/`tests/` desde el respaldo
   de código y `-u madenat_lumber_core`. Sin cambios de esquema.
