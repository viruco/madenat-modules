# DIAGNÓSTICO SOLO LECTURA — `stock_quant_lot_id_fkey` (Odoo 18 CE)

**Fecha del diagnóstico:** 2026-10-12 · **Entorno:** LOCAL `madenat_test` (contenedores `odoo18_app`, `odoo18_db`).
**Naturaleza:** **SOLO LECTURA**. **No** se eliminó/modificó nada de `stock.lot`, `stock.quant`, `stock.move`,
documentos de rebaja/ingesta ni datos históricos. **Sin despliegue, sin tocar el TEST remoto, sin commit/push.**

---

## 1. Base afectada, usuario, fecha y acción
| Dato | Valor |
|---|---|
| Base de datos | **`madenat_test`** (única servida: `db_filter = ^madenat_test$`, `db_name = madenat_test`) |
| Usuario | **uid 8 = `cristhian.elguetag@gmail.com` (Cristhian Elgueta)** |
| Fecha/hora (servidor) | **2026-10-12 18:28:42–18:28:44** |
| Ruta HTTP | `POST /web/dataset/call_kw/stock.lot/unlink` → **200** (el bloqueo se devuelve como mensaje) |
| Acción | **Botón «Eliminar» sobre un registro de `stock.lot`** (borrado estándar del modelo, no una operación de negocio) |
| Registro objetivo | **`stock.lot` id = 10215 = `SV000000841`** |

## 2. Evidencia en logs (operación `unlink` + traza)
Log en vivo del contenedor `odoo18_app` (`docker logs`), ventana exacta:

```
2026-10-12 18:28:35,427 1 INFO madenat_test werkzeug: ... POST /web/dataset/call_kw/stock.lot/web_read HTTP/1.1 200
2026-10-12 18:28:42,860 1 INFO madenat_test odoo.models.unlink: User #8 deleted mail.message records with IDs: [84530]
2026-10-12 18:28:42,903 1 ERROR madenat_test odoo.sql_db: bad query: b'DELETE FROM "stock_lot" WHERE id IN (10215)'
ERROR: update or delete on table "stock_lot" violates foreign key constraint "stock_quant_lot_id_fkey" on table "stock_quant"
DETAIL:  Key (id)=(10215) is still referenced from table "stock_quant".

2026-10-12 18:28:44,325 1 WARNING madenat_test odoo.http: No se pudo completar la operación: otro modelo necesita el registro que está siendo eliminado. Si es posible, mejor archívelo.

Modelo: Quants (stock.quant)
Limitación: stock_quant_lot_id_fkey
```

Lectura de la traza: Odoo ejecutó `unlink` sobre `stock.lot` → primero borró el mensaje de chatter asociado
(`mail.message` 84530, el paso normal de `mail.thread.unlink`) → y al llegar al `DELETE` físico, **PostgreSQL
rechazó** la operación porque **existen filas en `stock.quant` que referencian el lote** (`ON DELETE RESTRICT`). Odoo
traduce la `ForeignKeyViolation` al mensaje funcional mostrado en pantalla («otro modelo necesita el registro…»).
**No hay excepción Python ni defecto de código: es un bloqueo de integridad referencial por existencias.**

## 3. Lote y ruta de origen
| Campo | Valor |
|---|---|
| `stock.lot.id` | **10215** |
| `name` | **`SV000000841`** (coincide con el patrón de etiqueta SV `^SV[0-9]{11}$`) |
| `product_id` | 166 (producto `tracking='lot'`, tipo `consu`) |
| `lot_flow_type` | **`volume`** → es una **etiqueta SV (etiqueta de volumen)** |
| `volumen_m3` / `volumen_restante_m3` | **40.315** / **40.315** |
| `estado_trazabilidad` | `recepcionado` |
| `guia_processing_id` / `guia_number` | **15326** / **4495589** |
| `sv_assignment_applied_count` / `sv_balance_stamp` | **0** / vacío (sin operaciones SV aplicadas) |
| `create_date` / `create_uid` | 2026-10-02 15:21:19 / uid 2 |
| `write_date` / `write_uid` | 2026-10-10 21:41:48 / uid 1 |

**Ruta de origen de la acción:** **no** provino de ningún menú, botón o método propio de MADENAT. Se ejecutó el
**método estándar `stock.lot.unlink()`** vía RPC de la interfaz web (`call_kw/stock.lot/unlink`), es decir el **botón
«Eliminar» del formulario/lista estándar de Lotes** (Inventario → Productos → Lotes/Números de serie). Evidencia:
- **No existe** ninguna `ir.actions.act_window` con `res_model="stock.lot"` ni `<menuitem>` propio hacia `stock.lot`
  en `madenat_lumber_core`, `madenat_lumber_logistics` ni `madenat_lumber_intake` (búsqueda en `*.xml` sin
  resultados). El acceso usado fue el **visor estándar de Odoo**.
- La secuencia previa (18:28:20 `stock.lot/web_read`, 18:28:35 `stock.lot/web_read`) es navegación de lectura del
  lote en el formulario estándar, seguida del intento de borrado.

## 4. Consultas en modo lectura

### 4.1 Existencias y ubicaciones (`stock.quant`)
| id | ubicación | cantidad | reservada | `in_date` | `inventory_date` | company |
|---|---|---|---|---|---|---|
| **7840** | 4 · `Partners/Vendors` | **−40.3150** | 0 | 2026-10-02 15:21:19 | — | — |
| **7841** | 8 · `WH/Stock` | **+40.3150** | 0 | 2026-10-02 15:21:19 | 2026-12-31 | 1 |

➡️ **El lote tiene existencia física real: +40.315 m³ en `WH/Stock`** (contrapartida −40.315 en la ubicación virtual
de proveedores del movimiento de entrada). Es la fila **7841** la que dispara `stock_quant_lot_id_fkey`.

### 4.2 Movimientos y líneas
| id | `reference` | estado | cantidad | origen → destino | fecha |
|---|---|---|---|---|---|
| `stock.move_line` **8826** | **EMB-02395** | `done` | 40.315 | 4 (`Vendors`) → 8 (`WH/Stock`) | 2026-10-02 15:21:19 |

| picking | nombre | estado | tipo | partner |
|---|---|---|---|---|
| `stock.picking` **4166** | **EMB-02395** | `done` | **Recepciones** | Maderas Arauco S.A. |

➡️ El lote nace de la **recepción EMB-02395** (`done`), movimiento `Vendors → WH/Stock` de 40.315 m³.

### 4.3 Relaciones con guías, SV, packing y rebajas
| Modelo / tabla | Filas que referencian el lote | `ON DELETE` |
|---|---|---|
| `stock.quant` | **2** | **RESTRICT ← bloqueante** |
| `stock.move.line` | 1 (`EMB-02395`) | `SET NULL` (rompería trazabilidad, **no** bloquea) |
| `madenat.guia.processing` ↔ `stock.lot` (rel) | **1** (guía **4495589**, id 15326, `validated`) | `CASCADE` (desasociaría la guía, **no** bloquea) |
| `madenat.sv.operation` (ledger SV) | **0** | RESTRICT |
| `madenat.sv.imputation.line` (`processed_lot_id`) | 0 | RESTRICT |
| `madenat.sv.imputation.sv.line` (`sv_lot_id`) | 0 | RESTRICT |
| `madenat.guia.processing.source.lot.line` | 0 | RESTRICT |
| `lumber.shipment.line` | 0 | RESTRICT |
| `stock.valuation.layer` | 0 | SET NULL |
| `stock.lot` hijos (`parent_lot_id`) | 0 | — |
| `stock.lot.cost.line` | 0 | CASCADE |
| `madenat.audit.log` (`batch_id='SV00000000841'`) | 0 | — |

➡️ **El único bloqueo duro es `stock.quant` (2 filas).** Los demás vínculos existen pero **no** bloquean (algunos se
borrarían o quedarían huérfanos si se forzara).

### 4.4 Estado activo/archivado
**No existe columna `active` en `stock_lot`** (verificado en `information_schema.columns`; tampoco la añade ningún
módulo MADENAT). ➡️ **`stock.lot` NO se puede archivar** en este sistema: el texto genérico de Odoo «mejor
archívelo» **no aplica** a lotes.

### 4.5 Documentos que dependen del lote
1. **Guía de Ingreso por Volúmenes 4495589** (`madenat.guia.processing` 15326, `validated`) — dueña de la etiqueta.
2. **Recepción EMB-02395** (`stock.picking` 4166) y su línea `stock.move.line` 8826.
3. **Existencias**: cuant 7841 (`WH/Stock`, +40.315) y cuant 7840 (`Vendors`, −40.315).

## 5. Acción esperada (eliminar / archivar / cancelar / revertir / corregir)
| Opción | ¿Procede? | Fundamento |
|---|---|---|
| **Eliminar el lote** | ❌ **NO** | Tiene existencia física (+40.315 m³ en `WH/Stock`) y es el ancla de trazabilidad de la guía 4495589 y de la recepción EMB-02395. |
| **Archivar el lote** | ❌ **NO disponible** | `stock.lot` no tiene campo `active`; la interfaz estándar no ofrece archivar y el mensaje «mejor archívelo» es texto genérico de Odoo. |
| **Cancelar** | ❌ | La recepción EMB-02395 está `done` y la guía `validated`; no hay estado «cancelado» de lote. |
| **Revertir / corregir (vía de negocio)** | ✅ **SÍ, si hay un error real** | La corrección de una etiqueta SV se hace **con una operación SV** (reversa/regularización/rebaja) o por el **ciclo de vida de la guía**, nunca borrando el lote. |
| **Dejar el lote como está (no hacer nada)** | ✅ **Recomendado si no hay error** | El sistema funcionó correctamente: **impidió destruir el historial**. |

➡️ **Conclusión:** la operación esperada **no era eliminar**. El borrado fue un **uso incorrecto** del visor estándar
de lotes; la protección de Odoo operó correctamente. Si el usuario cree que el lote es un error, el camino es
**revertir/corregir por negocio** (guía/SV), no el botón «Eliminar».

## 6. ¿El desarrollo ofrece alguna vía que intente eliminar lotes con existencias?
Revisión del código MADENAT:

| Ubicación | Qué hace | ¿Borra lotes con stock? |
|---|---|---|
| `madenat_lumber_core/models/stock_lot.py:1257` `StockLotExtended.unlink()` | Llama `_sv_guard_unlink()`; borra `cost_line_ids`; `super().unlink()` | **No** por diseño; **no comprueba existencias** (deja el bloqueo a PostgreSQL) |
| `madenat_lumber_core/models/madenat_sv_operation.py:1292` `_sv_guard_unlink()` | Bloquea **solo si `lot.sv_operation_ids`** (historial SV) | Este lote tenía **0** operaciones ⇒ **la guarda no se activó** |
| `reception_service.py` / `_archive/_cleanup_orphan_moves.py` | Borran `stock.move`/`stock.move.line` huérfanos | No tocan `stock.lot` |
| `madenat_guia_processing.py` (reversión) | Borra `move.move_line_ids` y `move` de borradores | No toca `stock.lot` |
| Wizards SV (`rename`, `volume_regularize`, `rebaja`) | Operan sobre el ledger, **sin** borrar lotes | No |
| XML de acciones/menús | **No hay** `ir.actions.act_window` ni menú propio sobre `stock.lot` | — |

➡️ **Ningún flujo del desarrollo intenta eliminar lotes con existencias.** La eliminación vino del **visor estándar
de lotes** (`stock.lot.unlink`). **La causa raíz NO es un defecto del desarrollo.**

**Hallazgo colateral (mejora, no causa):** `_sv_guard_unlink()` solo protege la etiqueta SV **cuando ya tiene
historial** (`sv_operation_ids`). Para una etiqueta SV **recién recepcionada, sin operaciones, pero con existencias**
(este caso), la guarda es silenciosa y el usuario recibe el mensaje técnico de PostgreSQL en lugar de un mensaje de
negocio. Es un **defecto de experiencia/robustez**, no la causa del bloqueo.

## 7. Corrección propuesta (tras demostrar la causa)
> **Alcance:** sólo se corrigen *mensaje y previsibilidad*. **No** se autoriza borrar el lote ni tocar sus datos.

### Opción 1 — Mensaje claro (mínima, riesgo bajo, recomendada)
En `StockLotExtended.unlink()` (`madenat_lumber_core/models/stock_lot.py`), traducir la violación de integridad a un
mensaje de negocio, **sin cambiar qué se puede borrar**:

```python
def unlink(self):
    """Limpiar líneas de costo antes de eliminar lotes."""
    self._sv_guard_unlink()                      # guarda SV existente
    for lot in self:
        if lot.cost_line_ids:
            lot.cost_line_ids.unlink()
    try:
        return super(StockLotExtended, self).unlink()
    except psycopg2.errors.ForeignKeyViolation:
        lot = self[:1]
        raise UserError(_(
            'La etiqueta/lote %s tiene existencias o documentos que lo '
            'referencian y no puede eliminarse. Use la reversa/regularización '
            'de la guía o la operación SV correspondiente.'
        ) % (lot.name or lot.id))
```

- **Ventaja:** el invariante lo sigue garantizando la BD; sólo mejora el mensaje.
- **Riesgo de regresión:** muy bajo (no altera ningún flujo; sólo convierte el error).

### Opción 2 — Bloqueo proactivo (completa, requiere validación de suite)
Extender `_sv_guard_unlink()` para bloquear **antes** de llegar a la BD, **sólo** para etiquetas SV de volumen con
filas en `stock.quant` (mismo criterio exacto con que falla la FK):

```python
if (lot.lot_flow_type == 'volume' and self.env['stock.quant'].sudo().search_count(
        [('lot_id', '=', lot.id)])):
    raise ValidationError(_(
        'La etiqueta SV %s tiene existencias (%.3f m³ en stock) y no puede '
        'eliminarse. Es el ancla de trazabilidad de la guía %s. Registre una '
        'operación SV de reversa/regularización.'
    ) % (lot.name or lot.id, lot.volumen_restante_m3,
         lot.guia_number or lot.guia_processing_id.id))
```

- Nota técnica: la FK bloquea por **existencia de fila** en `stock.quant` (aunque la cantidad sea 0), por eso el
  criterio es `search_count([('lot_id','=',lot.id)])` y **no** `quantity != 0`.
- Se limita a `lot_flow_type == 'volume'` (concepto propio MADENAT) para acotar el impacto; el bypass test-only
  (`_sv_test_cleanup_allowed`) se conserva intacto.
- **Riesgo de regresión:** medio — cambia el comportamiento de `unlink` para etiquetas SV con quants; exige correr la
  suite completa antes de aceptar.

### Pruebas propuestas (ambas opciones)
1. `test_unlink_sv_volume_lot_con_existencias_bloquea_con_mensaje_de_negocio`: etiqueta SV de volumen con quant y
   `sv_operation_ids == 0` → `unlink()` falla con mensaje de negocio (no con la traza `stock_quant_lot_id_fkey`).
2. `test_unlink_sv_volume_lot_sin_existencias_permitido`: etiqueta SV sin quants ni historial → `unlink()` procede.
3. `test_unlink_cleanup_test_only_intacto`: el bypass `madenat.sv.internal.marker` sigue permitiendo el borrado en
   entorno de test estricto.
4. **Regresión:** corrida completa `core+intake+logistics` comparando contra la línea base (mismo conjunto de fallos).

**Implementación:** ninguna opción se ha aplicado (diagnóstico de solo lectura). Requiere autorización explícita
para editar código y correr la suite.

---

## ENTREGABLES

### A. Causa exacta y evidencia
**Causa:** el usuario **Cristhian (uid 8)** ejecutó el **borrado estándar de un lote** (`stock.lot.unlink`) sobre
**`SV000000841` (id 10215)** desde el visor estándar de lotes. El lote **tiene existencia física** (+40.315 m³ en
`WH/Stock`), por lo que PostgreSQL **rechazó** el `DELETE` con la FK **`stock_quant_lot_id_fkey`** (que es
`ON DELETE RESTRICT`). Odoo tradujo la violación al mensaje en pantalla.
**Evidencia:** log `docker logs odoo18_app` (2026-10-12 18:28:42–44) con `bad query: DELETE FROM "stock_lot" WHERE
id IN (10215)`, `violates foreign key constraint "stock_quant_lot_id_fkey"`, `POST …/stock.lot/unlink`, y la
consulta de `stock.quant` (2 filas, una con +40.315 en `WH/Stock`).
**Clasificación:** **operación de interfaz (uso incorrecto del visor de lotes) → protección correcta del sistema.**
**NO** es un defecto del desarrollo. Sí existe un **defecto colateral de mensaje** (§6, §7).

### B. Lote y documentos relacionados
- **Lote:** `stock.lot` 10215 = **`SV000000841`** (etiqueta SV de volumen, producto 166, 40.315 m³).
- **Guía:** `madenat.guia.processing` **15326 = 4495589** (`validated`).
- **Recepción:** `stock.picking` **4166 = EMB-02395** (`done`, Recepciones, Maderas Arauco S.A.) + `stock.move.line`
  8826.
- **Existencias:** `stock.quant` 7841 (`WH/Stock`, +40.315) y 7840 (`Vendors`, −40.315).
- **Ledger SV / imputación / packing / rebaja / envíos:** **0** referencias.

### C. Efecto sobre trazabilidad y existencias
- **Efecto actual:** **ninguno** — la operación fue **bloqueada**; lote, existencias y documentos quedaron intactos.
- **Si se hubiera forzado:** se habrían eliminado las 2 filas de `stock.quant` (pérdida de los 40.315 m³ de
  `WH/Stock` y su contrapartida), se habría puesto a **NULL** el lote en la línea histórica 8826 (ruptura de la
  recepción EMB-02395) y se habría **cascada** la desasociación de la guía 4495589. En resumen: **pérdida de stock y
  destrucción de trazabilidad**, sin posibilidad de reparación histórica.

### D. Acción operativa correcta
1. **No eliminar** el lote (no es una acción válida ni disponible).
2. Si **no hay error**: **no hacer nada** (el sistema hizo lo correcto).
3. Si **hay un error real**: usar la vía de negocio —
   - **Guía de Ingreso por Volúmenes 4495589** → reversa/corrección documental según el ciclo de vida, o
   - **Operación SV** sobre la etiqueta (revertir/regularizar/rebajar volumen) desde **«Rebajar etiqueta SV» /
     «Regularizar volumen de etiqueta SV»**.
4. Escalar a desarrollo si el mensaje en pantalla resulta confuso (ver §7, Opción 1).

### E. Riesgo si se forzara la eliminación
**Alto e irreversible.** Borrar el lote con `stock.quant` **viola el invariante de inventario** (desaparecen los
40.315 m³), **rompe la trazabilidad** (movimiento y guía) y contraviene el enfoque del Programa SV (ledger
append-only). **No se debe ejecutar** ningún `DELETE`/`TRUNCATE` ni `ALTER … DROP CONSTRAINT`.

### F. Corrección mínima y pruebas (si procede)
**Procede** como mejora de robustez/mensaje (no de la causa raíz) — ver §7:
- **Opción 1 (recomendada, riesgo bajo):** traducir la `ForeignKeyViolation` a un mensaje de negocio en
  `StockLotExtended.unlink()`; **no** cambia el invariante.
- **Opción 2 (completa, riesgo medio):** bloquear proactivamente la etiqueta SV de volumen con filas en
  `stock.quant` en `_sv_guard_unlink()`, con el mismo criterio exacto de la FK.
- **Pruebas:** 3 pruebas nuevas + regresión `core+intake+logistics` contra la línea base (ver §7).

> **Estado:** diagnóstico **solo lectura** completo. **Nada modificado** (ni `stock.lot`, ni `stock.quant`, ni
> `stock.move`, ni documentos, ni datos históricos). **Sin despliegue, sin commit/push, TEST remoto intacto.**




