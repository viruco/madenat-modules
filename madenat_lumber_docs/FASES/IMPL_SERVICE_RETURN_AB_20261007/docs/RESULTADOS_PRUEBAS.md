# RESULTADOS DE PRUEBAS — A/B Retorno de servicio (2026-10-07)

## Aislamiento

- **Base dedicada:** `srvretab_test_20261007` (`CREATE DATABASE … TEMPLATE srvret_test_20261006`),
  clon lógico de una base **test** aislada. `madenat_test` y producción **no** se tocaron.
- **Addons:** workcopy `IMPL_SERVICE_RETURN_AB_20261007/addons` montado `:ro` en
  `/mnt/extra-addons`. El árbol activo `custom_addons` **no** se modificó.
- `--workers=0 --no-http --max-cron-threads=0 --stop-after-init`; sin SMTP. Contenedor one-shot
  `--rm`; filestore efímero. `su=False` en las acciones (ACL real de los usuarios de prueba).

## 1. Corrida dirigida — `logs/iso_run1.log`

`0 failed, 0 error(s) of 85 tests`

| Clase | Suite | Nº |
|---|---|---|
| `TestServiceReturnConfirmation` | intake (nueva) | 13 |
| `TestServiceReturnPendingFilter` | logistics (nueva) | 9 |
| `TestServiceReturnImputationGuard` | logistics (nueva) | 8 |
| `TestSvImputationI2` | logistics (regresión I2) | 13 |
| `TestSvImputationCandidatesI2` | logistics (regresión I2) | 12 |
| `TestGranelRouteCore` | core (regresión) | 14 |
| `TestIntakeConsoleActions` | intake (regresión) | 13 |
| `TestIntakeDirectStock` | intake (regresión) | 3 |

## 2. Corrida completa de las 3 suites — `logs/iso_full_run1.log`

`madenat_lumber_core` 486 · `madenat_lumber_intake` 458 · `madenat_lumber_logistics` 290 =
**1020** pruebas. Resultado: **5 failed, 4 error(s)**.

### Las 9 fallas son PREEXISTENTES (no atribuibles a A/B)

Reproducidas **idénticas** con el **código activo SIN el cambio** (`logs/base_targeted.log`,
`4 failed, 5 error(s) of 34` sobre las mismas clases):

| Clase / prueba | Tipo |
|---|---|
| `test_guia_picking_link.TestGuiaPickingLink.test_t_g2_03_exclusion_retornos` | FAIL (drift de test sobre fuente) |
| `test_guia_processing.TestOrphanMoveCleanupSavepoint.test_partial_batch_failure_protected_moves_survive` | ERROR (savepoint/concurrencia) |
| `test_sv_concurrency.TestSvConcurrency` | ERROR (concurrencia: lock/serialize) |
| `test_sv_escalation_security.TestSvEscalationSecurity.test_02/03/04` | ERROR (`reason` NOT NULL en la base) |
| `test_processor_locations.TestProcessorLocations.test_09_auditoria_envio_normal` | FAIL (auditoría previa en la base) |
| `test_processor_shipment_ad89.TestProcessorShipmentAD89.test_t1/t5` | FAIL (auditoría previa en la base) |

## 3. Cobertura A (identificación no bloqueante)

Sí/No se conservan · vacío = pendiente y **≠** No · vacío **no** bloquea
`action_send_to_stock`/`action_validate` · el guard bloqueante **no existe** · identificación
posterior · permisos reales (Operaciones escribe; sin grupo → `AccessError`) · **sin** imputación
automática · reintento **no** duplica · fallo sin efectos parciales · **proxy de consola editable**
por el usuario operativo · fuera de alcance (compra/granel) no expone el campo.

## 4. Cobertura B (imputación posterior)

`action_apply` exige destino «Sí» (vacío/`no` → rechazo) · `action_pending` **no** lo exige ·
Sí→No/vaciar **rechazado** con imputación `applied` y **permitido** tras reversar (o con solo
borrador) · **sin** efectos de stock/ledger (`action_type='imputacion'` = 0) · regresiones I2 en
verde.

## 5. Límites declarados (no probados / no acreditados)

- **Navegador (V3):** **NO** ejecutado. No se afirma UI verificada.
- **Usuario real Cristhian:** **ACREDITADO** en el gate (§7; `su=False`, grupos intactos).
- **Filtro «sin imputación aplicada»:** **no** evalúa **cobertura parcial**.
- **Concurrencia** de las nuevas reglas (dos usuarios cambiando identidad/servicio simultáneos):
  **no** probada específicamente.
- **I3/I5** (salida nativa, ledger, costo) **no** implementados (fuera de alcance).

## 7. Gate previo sobre copia del árbol ACTIVO (2026-10-07) — `logs/gate_run2.log`

- Copia `/tmp/gate` = **árbol activo con sus cambios locales** + `A` + `B`; **byte a byte** igual al
  workcopy (`45/45` archivos). Los diffs **no** incluyen `madenat_lumber_docs/` (no sobrescriben la
  documentación ya actualizada).
- **Pruebas dirigidas repetidas:** `0 failed, 0 error(s) of 88 tests` sobre base aislada
  `srvretab_gate_20261007`.
- **Cristhian** (`cristhian.elguetag@gmail.com`): `test_14`/`test_15` (intake) y `test_09`
  (logistics) **ejecutadas y en verde** (`su=False`; grupos **no** modificados — aserción explícita).
- **Servidor aislado de navegador:** `http://127.0.0.1:8070`, base `srvretab_gate_20261007`,
  contenedor `srvretab_web` (no es el servicio activo). Login de Cristhian verificado por sesión
  (`uid=8`) con contraseña temporal **solo en la base aislada**. **V3 NO ejecutada** (sin navegador);
  guion: `docs/GUION_VERIFICACION_NAVEGADOR.md`.
- **Preexistentes/límites:** se mantienen las **9 fallas** (§2) y los límites de concurrencia (§5).
