# VOLVER A BORRADOR Y REASIGNAR REBAJAS (RESET) — 2026-10-11

**Solicitud expresa de Mauricio:** si una rebaja está **cancelada**, poder **volverla a borrador**,
corregir sus asignaciones y continuar. Entorno `madenat_test`.
**Módulos:** `madenat_lumber_logistics` **18.0.1.20.0 → 18.0.1.21.0** y `madenat_lumber_core` (audit log,
2 valores aditivos). **Sin commit/push/despliegue. Sin reparación histórica. WIP ajeno preservado.**

## 1. Causa exacta de la referencia cancelada
`IMP04823` (id **2733**) existe con **`state = cancelled`** y `guia_processing_id = 1198` (guía «19827»).
El asistente quedaba **ligado** al documento cuando era borrador; al **cancelarse** (desde el documento u
otra sesión), `Guardar`/`Aplicar` invocaban `_i2_build_imputation`, que lanzaba
«La imputación IMP04823 ya no admite preparación (estado cancelled)» — **caso A+D**: referencia correcta a
un cancelado, **sin acción de reapertura** y con mensaje no operativo. **No** era una búsqueda que
reutilizara un cancelado (B) ni un estado obsoleto del cliente (C) en el caso reproducido.

## 2. Contrato de «Volver a borrador»
Transición **controlada** `cancelled → draft` (autorizada). **Precondiciones**: estado `cancelled`; permiso
(Operaciones/Jefatura/Gerencia); compañía autorizada (regla de registro); guía elegible vigente; **ausencia
de otro trabajo activo** de la guía; **capacidad suficiente** para las reservas que `draft` genera;
coherencia de líneas/repartos; **motivo** no vacío. **No** aplica la rebaja. `applied`/`reversed` **no**
pueden volver a borrador. «Puede consultarse» ≠ «puede reactivarse».

## 3. Método y validaciones backend
`madenat.sv.imputation.action_reopen_to_draft()` con `_i2_check_reopen_permission()` y
`_i2_validate_reopen()` (conflicto + guía + **capacidad**: `_i2_validate_reopen` compara
`otros_activos + nominal_propio ≤ nominal` y nombra etiquetas y documentos que explican el conflicto).
Adquiere **advisory locks** (`_i2_lock_resources`) y **revalida tras el bloqueo**. Idempotente (si ya está
`draft`, no repite efectos). `write()` **bloquea** `state` libre sobre `cancelled`/`reversed`/`applied`.

## 4. Efecto sobre reservas y saldos
`cancelled → draft` **restablece la reserva** de borrador (nominal comprometido) — no se declara «sin
efecto sobre disponibilidad». **No** aplica efecto sobre el saldo del SV (no hay reparto aplicado). Si la
capacidad fue consumida por otra operación mientras estaba cancelado, **se rechaza** sin cambios parciales
y nombrando el conflicto; **no** se liberan reservas ajenas ni se reduce el nominal.

## 5. Historia conservada
Campos `cancelled_by_id`/`cancellation_date`/`cancellation_reason` y
`reopened_by_id`/`reopen_date`/`reopen_reason`; `message_post` y auditoría `imputation_cancel` /
`imputation_reopen`. La referencia (`name`) y el `documentary_key` **se conservan**. Repetir la reapertura
**no** duplica auditoría ni reservas.

## 6. Botones por estado
- **draft/pending:** [Guardar] [Aplicar] [Volver].
- **cancelled:** [Volver a borrador] [Volver] (+ aviso «Documento anulado… reabrir vuelve a activar las
  reservas previstas» y campo **Motivo de reapertura**). Guardar/Aplicar **ocultos**.
- **applied:** resultado en sólo lectura; reversa según permisos.
- **reversed:** historia; **sin** «Volver a borrador».

## 7. Reasignación y persistencia
Reabierto como `draft` conserva etiquetas y reparto; se pueden cambiar cantidades/destinos; Guardar
**actualiza el mismo documento** (sin duplicar) y Aplicar usa las cantidades actuales (una sola vez). Los
repartos a otros SV se conservan. Sólo tras aplicar, tablas en sólo lectura.

## 8. Conflictos y concurrencia
Conflicto si ya existe `draft/pending` para la guía → «Ya existe trabajo en preparación para esta guía:
[referencia]…». **Concurrencia RESET-16/17 (dos reaperturas; reapertura ∥ consumo): declaradas
PENDIENTES** — la protección por advisory locks existe y se revalida tras el bloqueo, pero la prueba con
dos transacciones simultáneas no se ejecutó en esta intervención.

## 9. Seguridad e inmutabilidad
`write({'state':'draft'})` sobre `cancelled` **no** elude la transición (exige `reopened_by_id` + motivo no
vacío en la misma escritura **y** revalida permisos); **un flag de contexto no autoriza**. `applied →
draft` y `reversed → draft` **prohibidos**. Sin `sudo` para eludir controles.

## 10. Pruebas y regresión
Suite nueva `tests/test_sv_rebaja_reset.py` (**RESET-01..15, 18, PHY-01**; 14 pruebas) — **0 failed /
0 errors**. Cubre: referencia e historia; reservas; repetición sin duplicar; capacidad consumida (A
cancelado, B aplicado, ambos intactos); conflicto de trabajo activo; permisos/compañía/motivo; `write`
directo; `applied`/`reversed`; asistente desactualizado; corregir/continuar; reasignar/aplicar; varios SV;
RESET-18 (nueva apertura no reutiliza el cancelado); atomicidad; sin efectos físicos.

```
odoo -d madenat_test -u madenat_lumber_core,madenat_lumber_logistics --test-enable --stop-after-init \
     --no-http --http-port=8071 --test-tags /madenat_lumber_logistics:TestSvRebajaReset
# → 0 failed, 0 error(s) of 14  (EXIT=0)

odoo -d madenat_test -u madenat_lumber_core,madenat_lumber_logistics --test-enable --stop-after-init \
     --no-http --http-port=8071 --test-tags /madenat_lumber_logistics
# → ver logs/regression.log
```

## 11. Evidencia de navegador
**Sin navegador** ⇒ límite declarado; no se afirma verificación de interacción. Guion en
`docs/GUION_NAVEGADOR_RESET.md`. Aceptación **pendiente de Mauricio**.

## 12. Versión instalada
`madenat_lumber_logistics` **18.0.1.21.0** y `madenat_lumber_core` (audit log aditivo) en `madenat_test`.

## 13. Documentación
CANON `19` §19.27, `02` §17.16.25, `03` §29, índice.

## 14. Archivos afectados y WIP ajeno
`models/madenat_sv_imputation.py`, `wizards/madenat_sv_imputation_wizard.py`,
`wizards/madenat_sv_imputation_wizard_views.xml`, `views/madenat_sv_imputation_views.xml`,
`tests/test_sv_rebaja_reset.py` (nuevo), `tests/__init__.py`, `__manifest__.py` (21.0), `CHANGELOG.md`;
`madenat_lumber_core/models/madenat_audit_log.py` (2 valores aditivos). WIP ajeno **preservado**.

## 15. Pendientes
1. **Concurrencia RESET-16/17** (dos reaperturas simultáneas; reapertura ∥ consumo): **pendiente**, no
   acreditada (locks advisory + revalidación implementados).
2. **Aceptación en navegador** (guion RESET).
3. **Sobrescritura concurrente de borradores**: riesgo previo, sin cambios.
4. `IMP04823`: **inspeccionado en lectura**, **no reabierto** en pruebas. `IMP02220`: **intacto**.

## 16. Propuesta de commit (NO ejecutado)
```
feat(sv-rebaja): «Volver a borrador» — transición controlada cancelled→draft (18.0.1.21.0)

- action_reopen_to_draft: motivo + permisos + conflicto + capacidad + locks + revalidación
- write() no elude la transición; applied/reversed→draft prohibidos
- trazabilidad cancelled_by_id/…, reopened_by_id/…; chat + auditoría imputation_cancel/reopen
- botones por estado (documento y asistente); mensaje operativo ante cancelación externa
- core: valores aditivos al Selection de madenat.audit.log
- tests RESET-01..15,18 + PHY-01; concurrencia RESET-16/17 declarada pendiente
```

**Sin commit · sin push · sin despliegue remoto · sin reparación histórica automática.**

