# Checklist y evidencias — Verificación probatoria P1–P4 (2026-10-12)

Entorno: `madenat_test` (LOCAL) · Sin commit/push/despliegue · TEST remoto intacto.

| # | Punto | Hipótesis auditada | Evidencia (reproducción) | Conclusión | Corrección | Prueba |
|---|---|---|---|---|---|---|
| **P1** | Concurrencia sobre la MISMA etiqueta retornada | «Dos operaciones compiten por capacidad insuficiente del mismo lote» | Harness con lote 10 compartido por 2 guías; A/B cancelados 6 m³; transactions independientes | **ACREDITADO** (advisory lock + revalidación de capacidad) | **Ninguna** (el mecanismo ya lo garantiza) | `test_sv_rebaja_reset_lot_capacity.py` (3) |
| **P2** | Recomputación real de intake | «Cambiar el detalle actualiza las métricas de la consola» | Probe: guía 5.0 vs **consola 0.0** (MISMO entorno) | **Defecto confirmado** (caché obsoleta) | Invalidación dirigida en `create/write/unlink` del detalle | `test_intake_metrics_recompute.py` (1) |
| **P3** | Saldos almacenados vs derechos del usuario | «Un usuario con visibilidad parcial no corrompe el saldo canónico» | Probe: `AccessError` en recompute bajo usuario sin ACL de imputaciones | **Defecto confirmado** | `compute_sudo=True` en los canónicos; `False` en la proyección por usuario | `test_sv_assignment_user_rights.py` (2) |
| **P4** | Aislamiento y limpieza de la autorización | «El token no identifica transacción → ventana reutilizable» | Auditoría: clave `(dbname, uid, id)` compartida entre transacciones | **Defecto confirmado** | Vía privada `_i2_write_protected_state` (sin estado global) | `test_sv_rebaja_reset_token.py` (7) |

## Evidencia por comando (logs)
- `logs/step1.log` — suites dirigidas previas (reset + concurrency + intake-depends): 21 tests, 0 fail, 0 warn.
- `logs/step2.log` — primera corrida P1–P4 (13 tests; 1 error P3 → ajustado).
- `logs/step3.log` — P1–P4 finales: **13 tests, 0 failed, 0 error, 0 warnings**.
- `logs/regression.log` — regresión amplia: **1230 tests, 6 failed, 4 error** (mismos que la base).
- `logs/regression_logistics.log` — regresión solo-logistics: comparación con la base (444/4).
- `logs/update_final.log` — actualización local de módulos afectados.

## Invariantes verificados (sin cambios)
Guardar/Aplicar/Volver en la misma ventana · persistencia/continuación desde SV · repartos a otros destinos ·
política de compromiso nominal · contrato de reparto positivo para aplicar · permisos y compañía ·
`cancelled → draft` controlado · `applied/reversed → draft` prohibidos · reversa con motivo · idempotencia ·
atomicidad · historia · ausencia de efectos físicos. No se reabrió IMP04823 ni se revirtió IMP02220.
