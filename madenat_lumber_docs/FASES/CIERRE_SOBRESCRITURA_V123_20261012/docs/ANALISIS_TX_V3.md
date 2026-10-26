# V3 — Análisis de TRANSACCIÓN, SerializationFailure y ORDEN de bloqueos

**Fecha:** 2026-10-12 · **Pruebas:** `tests/test_sv_rebaja_save_lock_tx.py` (TX-01..13).

## 1. Mapa del guard
- **`_i2_guarded_build`** (asistente): envuelve `_i2_build_imputation`, **fuerza `flush_all()`** dentro de la
  transacción y traduce `psycopg2.errors.SerializationFailure` al **mismo** mensaje operativo.
- **`_i2_assert_edit_version(expected)`**: `pg_try_advisory_xact_lock(1, doc_id)` (namespace **1** = documento) +
  `invalidate_recordset(['edit_version'])` + comparación. Rechaza si el lock está ocupado o la versión difiere.
- **`_i2_build_imputation`**: (1) elegibilidad, (2) **estado**, (3) **guard de versión (ns 1)**, (4) escrituras,
  (5) `_sync_return_links`. La versión se eleva en cada escritura de contenido (cabecera e hijos).
- **`write()`**: guard de transiciones (applied/cancelled/reversed) + **guard de versión para la edición directa**
  (`edit_version` en vals → `_i2_assert_edit_version` + bump).
- **Sin `commit` manual**, **sin capturar y continuar** con el cursor tras un error de PostgreSQL, **sin
  reintento** que sobrescriba. `invalidate_recordset` sólo cache.

## 2. Orden de bloqueos (determinista, sin deadlock)
| Ruta | Adquisición |
|---|---|
| Guardar / Aplicar / Dejar pendiente (ns 1 primero) | **1 (documento)** → 2 (SV) → 3 (etiqueta) en `_i2_lock_resources` (orden creciente `sorted`) |
| Reabrir / Revertir / Cancelar | solo 2/3 (no toman ns 1) → **no** invierten el orden |
| Edición directa (form) | 1 (documento) |
| TX-12 (dos documentos) | 1(doc1) + 1(doc2): ids distintos, orden no relevante (se serializa por documento) |

Como ninguna ruta adquiere 2/3 **antes** de 1, no hay ciclo de espera ⇒ **sin deadlock**. `_i2_lock_resources` usa
`pg_try_advisory_xact_lock` (no bloqueante) ⇒ rechazo inmediato y controlado en vez de espera indefinida.

## 3. Resultados TX (0 failed / 0 error)
| TX | Verificación | Resultado |
|---|---|---|
| TX-01 | Fallo simulado tras escritura ⇒ rollback íntegro (doc, líneas, repartos, versión) | ✔ |
| TX-02 | Cursor **utilizable** tras el conflicto controlado (sin error PG pendiente) | ✔ |
| TX-03 | Reintento **humano** con la versión vigente ⇒ funciona | ✔ |
| TX-04 | **Sin** reintento automático que sobrescriba (datos intactos) | ✔ |
| TX-05 | **Sin** auditoría de una transición fallida (`imputation_reopen`=0) | ✔ |
| TX-06 | Fallo **después del flush** ⇒ versión/estado sin avance indebido | ✔ |
| TX-07 | **Rechazo por VERSIÓN con el lock LIBRE** (A ya confirmó) | ✔ |
| TX-08 | Lock **OCUPADO** por A ⇒ rechazo controlado, sin escrituras de A | ✔ |
| TX-09 | Guardado secuencial repetido ⇒ sin falso conflicto | ✔ |
| TX-10 | A **aplica** y confirma; B obsoleto ⇒ rechazo | ✔ |
| TX-11 | Cancelar + edición obsoleta ⇒ rechazo | ✔ |
| TX-12 | Dos documentos (guards independientes) ⇒ sin deadlock | ✔ |
| TX-13 | Fallo en operación multietapa ⇒ sin documento ni reserva parcial | ✔ |

## 4. Efectos laterales no transaccionales
`message_post`/auditoría se ejecutan **después** de las escrituras exitosas; en un fallo previo **no** se emiten
(TX-05). Sin colas ni archivos. **No** se captura `SerializationFailure` y se continúa con el mismo cursor: se
relanza como `UserError` (transacción abortada → rollback por Odoo).

## 5. Riesgo residual
- Bajo **REPEATABLE READ**, la carrera entre comparación y escritura la cubre el **flush** dentro de la
  transacción (traducido). Verificado por construcción y por TX-06 (fallo tras flush).
- Multi-worker: no se levantaron dos procesos; el guard **no** depende del proceso que atiende (usa advisory
  locks de BD + columna persistente). **Límite declarado.**
