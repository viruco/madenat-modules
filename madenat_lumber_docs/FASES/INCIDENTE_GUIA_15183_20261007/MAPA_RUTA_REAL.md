# MAPA DE LA RUTA REAL — ingesta Procesado (guía 15183)

Reconstrucción del camino real ejecutado, con evidencia de archivo/línea.
Marcas: **[V]** verificado por código/config · **[L]** confirmado por log del
intervalo del incidente · **[I]** inferencia · **[U]** dato faltante.

## Secuencia (botón → control → notificación)

| # | Acción del usuario / paso | Código (archivo:línea) | Efecto |
|---|---|---|---|
| 1 | «Leer documento» | `intake_wizard.action_preview_document` (`intake_wizard.py:475`) | clasifica por glosa del PDF |
| 2 | Clasificación | `_classify_normal_document` (`:445-473`) → `tipo_ingreso='procesado'` | **[V]** por texto del PDF |
| 3 | Notificación «Ingreso Procesado» | `intake_wizard.py:499-514` (`sticky=True`) | **1 por clic** (ver DICTAMEN §8) |
| 4 | «Continuar ingreso» | `action_route_document` (`:573`) → `_guard_route_document` (`:600`) | exige ubicación + PDF + Excel |
| 5 | Rama Procesado | `_route_procesado` (`:683-706`) | crea guía + `action_verify_data` |
| 6 | **Create** guía | `guia = madenat.guia.processing.create(vals)` — **sin** `name`, **sin** `partner_id` | `name` default = `New` (`madenat_guia_processing.py:625`) |
| 7 | Guard create | `create()` (`:3411-3419`) → `_require_intake_operational_group` | rol operativo |
| 8 | Validación duplicado **en create** | `_check_guide_identity_duplicate_on_create` (`:3378-3409`) | **[V]** `name` ∈ (None, `New`) → **skip** (`:3391`), **no valida** |
| 9 | **action_verify_data** | `madenat_guia_processing.action_verify_data` (`:1703`) | lee Excel/PDF |
| 10 | Staging | unlink previas (`:1717`) → `line.create(lines_to_create)` (`:1786-1787`) | **13 líneas** de staging (efecto ya ocurrido) |
| 11 | Identidad + proveedor | `update_vals` (`:1795+`); `name`←PDF (`:1824-1825`); `partner_id`←RUT (`:1849-1855`) | número y proveedor **definitivos** |
| 12 | **write(update_vals)** | `:1930` → `write()` (`:3421-3438`) → `_check_guide_identity_duplicate` (`:3307`) | **punto de decisión** |
| 12a | Bloqueo dup confirmado | C1 `cross_model=False` (`:3358-3364`) | **[L]** `partner=1052 … cross_model=False` → «sin duplicados» → **no bloquea** |
| 12b | Aviso homónimo | C1 `cross_model=True, raise_on_match=False` (`:3367-3374`) | **[L]** encontró la Recepción → `_warn_guide_homonym` (`mixin_lumber_ingest.py:113`) → `message_post` |
| 13 | Match OC | `_match_purchase_order` (`:1935`) | **[L]** `not_found MC 1108-326` |
| 14 | Persistencia destino | `_persist_target` (`:1099`) + `_log_intake_origin` (`:1179`) | **[V]** `madenat_audit_log` 21744 `creation` |
| 15 | Pantalla automática | `_open_read_view_action` (`:1109-1138`) | act_window consola; `res_id = 900000000 + 33154` |

## Orden de datos (provisional → definitivo)

1. **Número provisional:** `New` (default) al crear la guía (paso 6). → sin control.
2. **Proveedor desconocido:** `partner_id = NULL` al crear (paso 6). → AJUSTE A.
3. **Líneas de staging:** creadas en el paso 10 (**antes** del control de identidad).
4. **Número definitivo + proveedor definitivo:** fijados juntos en el `write` (paso 12).
5. **Chequeos de duplicado:** sólo en el `write` (paso 12) — el bloqueo con
   `cross_model=False`; el aviso con `cross_model=True`.
6. **Notificación/mensajes:** «Ingreso Procesado» (step 3, cliente web) + aviso
   de homónimo en chatter (step 12b, `message_post`).

## Puntos clave verificados

- **[V]** La guía **nunca** pasa por un estado con identidad completa en `create()`;
  vive toda la lectura en `write()`.
- **[V]** El **control de duplicado corre DESPUÉS** de crear el staging (paso 10 < 12).
  Con el bloqueo activo, la transacción revertiría; sin bloqueo (hoy), el staging queda.
- **[V]** `_check_guide_identity_duplicate_on_create` sólo bloquea si `create()` trae
  `name` **y** `partner_id` — cosa que `_route_procesado` **no** hace.
- **[U]** No hay log de cliente web del doble clic que originó la doble notificación.

## Trazabilidad de la guía 15183 (evidencia de datos)

| Ingesta | id | create_date | Estado final | Destino |
|---|---|---|---|---|
| 1ª | 33152 | 2026-10-06 18:51:23 | cancelada → **eliminada** (`guia_delete_permanent`, 2026-10-07 19:23:40) | `madenat_audit_log` |
| 2ª | 33153 | 2026-10-07 19:23:09 | cancelada → eliminada | `madenat_audit_log` 21742-21743 |
| 3ª | 33154 | 2026-10-07 20:40:56 | **viva** (`verified`) | log de C1 en el intervalo |

**[V]** El módulo `madenat_lumber_core` se actualizó con el fix a `write_date`
`2026-10-07 20:34:57`; la 3ª ingesta (20:40:56) es **posterior** → el código
activo sigue permitiendo el duplicado.
