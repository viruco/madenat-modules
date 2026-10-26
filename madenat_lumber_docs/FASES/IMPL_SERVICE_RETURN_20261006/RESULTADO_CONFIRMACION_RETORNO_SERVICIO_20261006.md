# RESULTADO — Confirmación de retorno de servicio (2026-10-06)

Copia de trabajo aislada: `IMPL_SERVICE_RETURN_20261006/addons` (NO es el código
activo `custom_addons`). Diff: `service_return_confirmation.diff`.

## Dictamen
**A. IMPLEMENTADO Y VALIDADO EN COPIA** — 53/53 tests OK (0 failed, 0 errors).

## Aislamiento verificado
- Base dedicada `srvret_test_20261006` (clon lógico de `madenat_test`); la base
  activa y TEST remoto NO se tocaron.
- Addons del workcopy montados `:ro` en `/mnt/extra-addons` (código activo intacto).
- Filestore interno efímero del contenedor one-shot (`--rm`).
- `--max-cron-threads=0 --workers=0 --no-http --stop-after-init`; sin SMTP/integraciones.
- Comando: `run_iso.sh`; log: `logs/iso_run4.log`.

## Resultado de pruebas (log iso_run4)
`0 failed, 0 error(s) of 53 tests` · `madenat_lumber_core: 16` ·
`madenat_lumber_intake: 37` · `madenat_lumber_logistics: 10`.
- `TestServiceReturnConfirmation` (15): bloqueo sin respuesta sin efectos; Sí/No
  pasan el guard; validación directa no omite; histórico validado legible sin
  backfill; compra/granel fuera de alcance; persistencia; seguridad (Operaciones
  y **Cristhian por login** → CONFIRMADO); sin efectos colaterales; filtros;
  proxy de consola; vista carga el campo.
- `TestServiceReturnPendingFilter` (8): sin imputación / borrador / anulada /
  reversada ⇒ pendiente; `applied` ⇒ no pendiente; `no`/sin confirmar/`compra`
  fuera. (Operador `not any`: incluye correctamente la relación vacía.)
- Regresión: `TestGranelRouteCore` (14), `TestIntakeConsoleActions` (13),
  `TestIntakeDirectStock` (3) — sin romper contratos.

## Notas
- `test_08b_cristhian_por_login`: Cristhian existe en el clon y pudo guardar con
  sus permisos actuales (no se tocaron grupos/ACL/reglas).
- Limitación declarada: el filtro «pendientes de imputación» no evalúa cobertura
  parcial.
- Ningún cambio en `tipo_recepcion`/`tipo_ingreso`, stock, costes, BT-04, toll,
  I2/I3, packing, lotes ni menús/grupos.
