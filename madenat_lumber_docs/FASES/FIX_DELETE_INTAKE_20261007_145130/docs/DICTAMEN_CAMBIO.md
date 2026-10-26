# DICTAMEN DEL CAMBIO — conflicto doctrinal y propuesta

## 1. Qué se corrigió (naturaleza del cambio)

La corrección es, en lo esencial, una **corrección de atribución** (defecto), con **dos
cambios de comportamiento acotados y explícitos**:

1. **Atribución por relaciones** en el diagnóstico y la ejecución del Modo A:
   `origin` textual deja de ser atribución concluyente; se usan el vínculo fuerte
   `stock.picking.guia_processing_id`, los lotes propios y la evidencia de pertenencia a
   otro documento. Efecto: un **documento ajeno** que comparte el número deja de bloquear.
2. **Cierre del punto ciego** del retorno: el vínculo directo por FK ahora **se detecta**
   (antes se ignoraba). Efecto: un retorno vinculado a la guía pasa a bloquear, con
   mensaje específico y explicable.

## 2. Conflicto con la doctrina vigente

CANON/`04_DECISION_LOG.md` §4.3 (tabla de los cuatro modos, ~líneas 1994-1998) fija como
precondición del **Modo A**: «`state in ('draft','cancelled')`; **sin picking ni
movimiento**; sin quant; …». La **redacción** admite dos lecturas:

* **L1 (literal/amplia):** bloquea ante **cualquier** `stock.picking`, en cualquier estado,
  con independencia de a qué documento pertenezca.
* **L2 (funcional):** bloquea ante cualquier picking/movimiento **de la guía** (evitar
  destruir la trazabilidad propia del ingreso).

La implementación previa usaba una **tercera** vía (`origin` textual), que **no** es
ninguna de las dos: producía **falsos positivos** (documentos ajenos) y **falsos
negativos** (el retorno por FK). El parche alinea la implementación con **L2** y hace
**visibles** los vínculos directos/ambiguos.

> **Estado:** esto es una **propuesta de precisión doctrinal**, NO una política vigente.
> **No** se modifica `CANON/` en esta entrega. Requiere aprobación (ver §4).

## 3. Lo que el parche NO hace (límites deliberados)

* Los vínculos directos **no** se ignoran ni se eliminan automáticamente (§3 del encargo).
* Los vínculos ambiguos **bloquean** con mensaje específico (no se fuerzan a “permitir”).
* **No** se usa `sudo()`, contexto oculto, `SQL DELETE` ni permisos globales. El único SQL
  introducido es `pg_advisory_xact_lock` (candado de transacción, **no** escritura).
* **No** se altera stock, retornos, valoraciones ni evidencia para “hacer pasar” el caso.
* **No** se habilita `perm_unlink` en la Consola ni se toca el Modo C (salvo el criterio de
  atribución compartido, que es de lectura).
* **No** se refactoriza nada ajeno al requerimiento.

## 4. Decisión de política pendiente (bloqueante para el caso 15183)

Para **15183** la corrección **no** habilita el borrado: queda **bloqueado por el vínculo
directo** del retorno (FK), que es un vínculo **real o contradictorio** (caso F). Hay que
decidir, **antes** de aplicar el parche en firme:

> **D-POL-1.** ¿Un `stock.picking` de retorno creado por la **propia cancelación** de la
> guía (documento *derivado*, `origin='Return of …'`), que porta `guia_processing_id` por
> **fuga de contexto** y **no** es un ingreso de producción, debe contar como
> “dependencia propia que bloquea el Modo A”?
>
> * **Opción 1 (estricta, actual):** sí bloquea. Consecuencia: 15183 **no** se puede
>   eliminar; solo cancelar/archivar (Modo B / backlog).
> * **Opción 2 (derivado):** no bloquear por retornos *derivados* de la cancelación
>   (únicamente por ingresos de producción con `FK` + lote propio). Consecuencia: 15183
>   podría eliminarse, **pero** se debe decidir el destino de la **cadena 436→7813→7814**
>   (qué pasa con retornos/devolución de un ingreso eliminado) — efecto de **política de
>   trazabilidad**, no cosmético.

El parche **no** decide esta política: entrega la **detección correcta** y la corrección
preventiva (§5) para que la decisión se tome con el dato exacto sobre la mesa.

## 5. Corrección preventiva del retorno (delimitada, separada)

`02_preventive_return_fk.diff` (solo `madenat_guia_processing.py`): al crear los retornos
(reversa de consumo BT-04, reversa SV y reversa del Modo B) se fuerza
`'guia_processing_id': False`. **Causa raíz reproducida** (`test_l`): `default_get`
inyecta `default_guia_processing_id` desde el contexto del asistente en **cualquier**
`stock.picking.create` (Odoo `models.py:1660-1665`). Forzar `False` neutraliza la fuga.

* No quita el FK del retorno real **7813** (no se tocan datos históricos).
* No reasigna documentos históricos.
* Es **independiente** del parche de eliminación (archivo distinto) y se puede aplicar sin
  él; su interacción se documenta en `PLAN_APLICACION_REVERSION.md`.

## 6. Dependencia con `IMPL_SERVICE_RETURN_20261006/`

`service_return_confirmation.diff` **no** se fusiona ni reemplaza. No hay solape de
archivos/funciones con `02_preventive_return_fk.diff` (este toca solo los `create` de
retorno de `_reverse_consumption_picking`, `_sv_reverse_*` y `action_force_cancel`).
Debe revisarse que la prueba de regresión de aquel trabajo (53/53) se repita **después**
de aplicar este parche, si ambos convergen.
