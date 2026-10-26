# PLAN DE VALIDACIÓN — previo a cualquier implementación o despliegue
**NO ejecutar todavía.** Todas las pruebas se corren en **copia aislada** (BD clonada con nombre que
contenga `test` + código en carpeta aislada), nunca en `madenat_test` vivo ni en producción.

## Entorno y método sugerido
- Clonar BD (p. ej. `madenat_test_delclone`) y apuntar una instancia aislada a `custom_addons` copiado.
- Preferir **tests automatizados** (`TransactionCase`, `@tagged('post_install','-at_install')`) sobre clics
  manuales; cada test revierte su transacción.
- Habilitar el relax de Modo A con `ir.config_parameter('madenat.dev_cleanup_enabled')='True'` solo en la
  BD `*test*`, para reproducir el entorno del caso.
- Criterio transversal: **nunca** borrar movimientos/pickings/quants/lotes; verificar que el stock neto,
  la auditoría (`madenat.audit.log`) y el chatter no se destruyen sin registro.

## Casos mínimos

| ID | Objetivo | Precondiciones | Resultado esperado |
|---|---|---|---|
| **MS-01** Registrar elegible sin dependencias | Guía `draft`/`cancelled`, 0 lotes, 0 pickings, 0 quants, sin evidencia; `dev_cleanup_enabled=True` | Modo A **procede**; `unlink()` OK; evento `guia_delete_permanent` con snapshot+SHA-256 |
| **MS-02** Coincidencia textual con documento distinto (nº compartido guía↔recepción) | Guía `N` y `lumber.reception` con `guia_numero=N`; picking de la recepción con `origin=N`, guía sin FK | Documentar el comportamiento **actual** (bloquea Modo A). Comparar con el comportamiento **propuesto** (bloquear solo por FK/lotes) |
| **MS-03** Picking directamente vinculado por FK | Guía con `guia_processing_id` apuntando a un picking `done` | Modo A **bloquea** (traza material real); Modo B conserva |
| **MS-04** Retorno directamente vinculado | Retorno `done` con `guia_processing_id=guía.id` (origin `Return of …`) | Verificar si el guard lo detecta; documentar punto ciego (FK no consultado) |
| **MS-05** Cadena de devoluciones | original→retorno→devolución (`Return of` / `Devolución de`) | No duplicar retornos; idempotencia vía `return_id`/`origin_returned_move_id` |
| **MS-06** Usuario autorizado | Usuario con `group_madenat_operaciones` + `stock.group_stock_manager` | Modo A/B/C según precondiciones; sin `AccessError` |
| **MS-07** Usuario no autorizado | Usuario sin grupos operativos / sin `stock_manager` | `_require_intake_operational_group` → `AccessError`; `unlink` del core → `UserError` de permiso |
| **MS-08** Menú estándar vs Modo A | Consola (vista SQL) vs wizard Modo A | Estándar: bloqueado (ACL `unlink=0` + vista). Modo A: `UserError` de precondición. Confirmar que **no** son la misma ruta |
| **MS-09** Protección de stock | Guía con picking `done` con lotes/quants | Tras cualquier intento, el stock y los quants **no** cambian; lotes intactos |
| **MS-10** Protección de costes | Guía con `stock.lot.cost.line` (`Servicio <guía>`) | Modo A/C bloquean; `action_force_cancel` cierra por integridad contable sin borrar |
| **MS-11** Protección de evidencia y auditoría | Guía con `ir.attachment` + `mail.message` (no-creation) | En producción: bloqueo. En dev: relax ignora evidencia; verificar que `guia_delete_permanent` **conserva** el snapshot firmado |
| **MS-12** Cancelación sin atribuir ajenos ni duplicar retornos | Guía con nº compartido con recepción (`origin` coincide con documento ajeno) | Modo B revierte **solo** los pickings de la guía (no los de la recepción ajena) y **no** duplica retornos; verificar el FK del retorno (origen: contexto `default_guia_processing_id`) |

## Criterios de aceptación globales
1. **Idempotencia** de retornos (rerun no crea segundo retorno `done`).
2. **No-regresión de stock**: `stock.quant` netos y lotes idénticos antes/después.
3. **Trazabilidad**: cada borrado/cancelación deja `madenat.audit.log` (snapshot + SHA-256) y chatter.
4. **Aislamiento**: la cancelación de una guía **nunca** altera pickings/quants de documentos ajenos
   (recepción con nº compartido).
5. **Permisos**: ni `sudo()` ni bypass de ACL; los guards server-side se respetan en ORM/RPC/UI.

## Evidencia a capturar por caso
- Guía `id/name/state`; pickings con `origin`, `state`, `guia_processing_id`, `reception_id`;
  movimientos y `move_line.quantity`; lotes y quants; `madenat.audit.log`; chatter/adjuntos.
- Antes/después, en transacción aislada.

## Fuera de alcance de este plan (requieren decisión separada)
- Cambios de política AD-80 (guard de Modo A por FK vs `origin`).
- Archivado de guías (backlog `05_BACKLOG.md`).
- Cualquier despliegue o actualización de módulos en `madenat_test` vivo o producción.
