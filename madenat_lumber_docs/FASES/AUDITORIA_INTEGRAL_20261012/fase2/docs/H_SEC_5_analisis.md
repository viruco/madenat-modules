# H-SEC-5 — Inmutabilidad de `madenat.audit.log` (análisis SOLO LECTURA + propuesta)

**Alcance:** autorizado **solo en lectura**. No se cambió nada.

## 1. ACL por grupo (`madenat_lumber_core/security/ir.model.access.csv`)
| id | grupo | read | write | create | unlink |
|---|---|---|---|---|---|
| `access_madenat_audit_log_user` | `base.group_user` (cualquier usuario interno) | 1 | **0** | 1 | 0 |
| `access_madenat_audit_log_manager` | `base.group_system` | 1 | **1** | 1 | **1** |
| `access_madenat_audit_log_auditoria` | `group_madenat_auditoria` | 1 | 0 | 0 | 0 |

**No hay ninguna `ir.rule`** sobre `madenat.audit.log` (grep en `*/security/*.xml` = vacío).

## 2. ¿Bloquea el modelo `write`/`unlink`?
**No.** `madenat_audit_log.py` define solo campos (sin `def write` ni `def unlink`). ⇒ Cualquier usuario con
`write` puede modificar filas; cualquiera con `unlink` puede borrarlas.

## 3. Quién puede alterar/borrar hoy
- **Alterar (write):** `base.group_system` (**incluye a los administradores**). El flujo normal escribe con
  `sudo()` en servicios/asistentes, pero el ACL **no** impide que un admin (o cualquier proceso con write)
  module una fila existente.
- **Borrar (unlink):** **`base.group_system`** (y `base.group_user` no puede por ORM; sí por SQL directo fuera
  del ORM, que queda fuera del alcance del ACL).
- **Leer:** todos los anteriores y `group_madenat_auditoria` (solo lectura).

## 4. Quién escribe en la bitácora
**34 llamadas `create`** a `madenat.audit.log` en `madenat_lumber_core/logistics/intake` (servicios de guía
procesada, ledger SV, wizards de reversa/reapertura, B-01, D2/C2, backlog documental, conciliación
envío–retorno, y `_lifecycle_log` de intake). Los `action_type` están declarados como `Selection` (44+ valores
aditivos). **Evidencia:** `grep -rn "madenat.audit.log" --include=*.py | grep create`.

## 5. Afirmaciones documentales que se apoyan en la bitácora
- **AD-47** (CANON/04 §«AD-47»): «El evento `madenat.audit.log` es la **fuente de verdad inmutable** de la
  evidencia (`audit_snapshot` + `audit_hash`), enlazado relacionalmente a la guía».
- **AD-79 / D-I2-15** (CANON/04): «ledger **append-only**»; «la imputación `applied` es **inmutable**».
- **CANON/19 §19.32** y `stock_lot.unlink`: la guarda de lote invoca la **inmutabilidad del historial**.
- **AUDIT_REBAJA_ETIQUETAS** habla de «inmutabilidad/reversa … cerrados con pruebas».

⇒ Existen varias afirmaciones canónicas de **bitácora inmutable / append-only**, **pero** el modelo
`madenat.audit.log` **no** las garantiza técnicamente (write/unlink permitidos por ACL; sin `ir.rule`; sin guarda
de modelo). La inmutabilidad del **ledger SV** sí está protegida por **guardas de estado** en
`madenat.sv.operation` (no por ACL de la bitácora).

## 6. Pruebas que cubren su inmutabilidad
Hay **10** suites que **mencionan** `madenat.audit.log` (`test_guia_documental_correction`,
`test_guia_processing`, `test_guia_historical_reverse`, `test_guia_reopen_traceable`, `test_sv_operation_ledger`,
`test_deviation_guard`, `test_sv_concurrency`, `test_sv_rpc_bypass`, `test_reception_security`,
`test_guia_processing_security`), pero **ninguna** verifica que **write/unlink** sobre una fila de bitácora
**fallen** (no hay una prueba de inmutabilidad del registro). **No** hay cobertura directa del `unlink` prohibido.

## 7. Propuesta (SIN implementar)
1. **Bloquear `write` y `unlink` en el modelo** `madenat.audit.log` (excepciones controladas / test-only).
2. **Retirar permisos**: `write` para usuarios finales (ya es 0 en `group_user`, mantener); quitar `unlink` a
   `base.group_system` salvo mantenimiento explícito; **añadir `ir.rule`** de solo-lectura.
3. **Matizar** los enunciados «inmutable/append-only» allí donde se refieran a la bitácora (hoy equivalen a una
   intención de diseño, no a una garantía técnica).
4. **Impacto en pruebas/limpiezas:** varias suites borran bitácora por **SQL crudo** en `tearDownClass`
   (bypassa ORM/ACL) ⇒ bloquear el ORM **no** rompe esas limpiezas; otras usan `sudo()` (create, no
   write/unlink) ⇒ sin impacto. **Migración:** riesgo bajo (solo restringe).
5. **Pruebas necesarias:** que `write`/`unlink` sobre una fila existente levanten `AccessError`/`UserError`
   (salvo la excepción test-only), y que `create` siga funcionando.
