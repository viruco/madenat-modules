# H4 / H5 / H6 — Pruebas, saneamiento y fixtures (FASE 4)

## H4 — Escenario (f): línea de coste sobre lote de la guía

Prueba dedicada en `madenat_lumber_intake/tests/test_guia_delete_guards.py::test_f_cost_lines_blocked`:

1. Guía `G4-F` + lote vinculado + `stock.lot.cost.line` (`name`, `lot_id`, `amount_usd`, `cost_type`).
2. `unlink()` con motivo ⇒ **bloqueo** `UserError` con «No se puede eliminar la guía … coste» (mensaje de
   negocio; el bloqueo **no** deja bitácora).
3. Control positivo: guía `G4-F2` con lote **sin** costes ⇒ se elimina.

Resultado: incluida en el bloque de 36 pruebas ⇒ **0 failed / 0 error**.

## H5 — Saneamiento local (solo `madenat_test`)

- Script: `docs/H5_saneamiento_script.py`. `H5_MODE=dry` (por defecto) simula cada borrado dentro de un
  `savepoint` y revierte; `H5_MODE=exec` borra **uno a uno** con verificación y conteos.
- Candidatos por **IDs explícitos**: 8 socios nombrados + 40 socios `*_oper`. Resultado: **48 eliminados**,
  ninguno con dependientes (verificado en la simulación). Guías con nombre de prueba: **0 candidatas**.
- **Conservado:** 3 usuarios `@madenat.test` inactivos (documentados) y las 11 auditorías con «test».
- Residuo adicional detectado durante la propia verificación: 5 filas `guia_delete_permanent` / `batch_id=G3-CONC`
  de ejecuciones previas (fuga de la fixture anterior, ya corregida) ⇒ limpiadas por la fixture reparada.
- Datos no tocados: guías 13→13, recepciones 8→8, usuarios 12→12, lotes 151→151.

## H6 — Fixtures sin residuo `*_oper`

Causa raíz: `res.users.create` crea un `res.partner` homónimo que **no** se elimina al borrar el usuario.

Corrección (misma técnica que T1, por IDs explícitos) en `_cleanup_class` de
`test_sv_rebaja_reset_concurrency` y `test_sv_rebaja_reset_lot_capacity`, y en `_cleanup_class` +
`_cleanup_run` de `test_sv_rebaja_save_lock_tx`:

```python
cr.execute('SELECT partner_id FROM res_users WHERE id = ANY(%s)', (cls._user_ids,))
user_partner_ids = [r[0] for r in cr.fetchall() if r[0]]
...
if user_partner_ids:
    cr.execute('DELETE FROM mail_message WHERE author_id = ANY(%s)', (user_partner_ids,))
    cr.execute('DELETE FROM res_partner WHERE id = ANY(%s)', (user_partner_ids,))
```

Además, la bitácora de la propia ejecución se limpia por `batch_id` (nombre de guía / clave documental), porque
la FK `guia_processing_id` queda a `NULL` al borrar la guía y el borrado por FK no encontraba el registro.
Mismo arreglo en `TestGuiaDeleteConcurrency.tearDownClass` (limpieza por `batch_id = 'G3-CONC'`).

**Demostración (dos ejecuciones consecutivas, 4 clases con COMMIT real):**

| Ejecución | Resultado | Socios `*_oper` | Bitácora |
|-----------|-----------|-----------------|----------|
| A | 0 failed / 0 error of 10 | 40 → **0** | 332 → 327 (5 residuo previo `G3-CONC`) |
| B | 0 failed / 0 error of 10 | **0** (sin cambio) | 327 (sin cambio) |

⇒ **no se crean residuos nuevos** y la historia (11 auditorías «test») permanece intacta.
