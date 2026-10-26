# G4 — Dry-run (solo lectura) de residuos de prueba en `madenat_test`

**Estado:** listado **sin eliminar**. La limpieza real **requiere autorización aparte** (no ejecutada).

## 1. Socios residuales
| Modelo | IDs | Nombre | Creado | Dependencias (guías/pickings/asientos) | ¿Borrado seguro? |
|---|---|---|---|---|---|
| `res.partner` | 14642, 17752, 18221, 19014, 19512, 19825, 20296 | «P Conc Fase 2» (×7) | 2026-10-10 … 2026-10-12 | **0 / 0 / 0** | **SÍ** (sin dependientes) |
| `res.partner` | 410 | «Proveedor TEST MADENAT» | 2026-06-05 | **0 / 0 / 0** | **SÍ** |

Origen probable: `test_guide_lifecycle_phase2.TestDeleteConcurrency` (los 7 «P Conc Fase 2», uno por
ejecución; **corregido en G2**) y una suite de intake antigua («Proveedor TEST MADENAT»).

## 2. Usuarios de prueba (inactivos)
| Modelo | IDs | Login | Activo | Grupos |
|---|---|---|---|---|
| `res.users` | 2974 | `v3_concil_oper@madenat.test` | **No** | 64 filas (residuos del alta) |
| `res.users` | 2975 | `v3_concil_jef@madenat.test` | **No** | ídem |
| `res.users` | 3109 | `impl_sv_check@madenat.test` | **No** | ídem |

Origen: suites de concurrencia/verificación. Están **inactivos**. Al borrarlos hay que limpiar también sus
filas en `res_groups_users_rel`.

## 2.b Socios `*_oper` (PREEVISTOS de suites de concurrencia, **ajenos a la Fase 3**)
| Modelo | IDs | Nombre | Origen (suite) | Dependencias |
|---|---|---|---|---|
| `res.partner` | 20581 | `conc_oper` | `test_sv_rebaja_reset_concurrency` | 0/0/0 |
| `res.partner` | 20583 | `p1_oper` | `test_sv_rebaja_reset_lot_capacity` | 0/0/0 |
| `res.partner` | 20600, 20676 | `v3_oper` (×2) | `test_sv_rebaja_save_lock_tx` | 0/0/0 |

Detectados **tras** la regresión de Fase 3, pero **no** causados por ella: se **demostró** ejecutando la suite
preexistente `TestSvRebajaSaveLockTxConcurrency` aislada, que deja **+1** socio por sí sola. Estos socios son el
`res.partner` de los usuarios de prueba creados en `setUpClass`; su `tearDownClass` no los elimina. **Propuesta**
(añadida al dry-run): borrarlos igual que los 8 anteriores (0 dependientes), y **corregir** las suites en una
intervención separada (no autorizada aquí).

## 3. Auditoría con motivo «test»
**11 filas** `madenat.audit.log` (ids 8812, 8815, 9088, 9445, 9447, 10228, 10400, 10404, 10491, 21743, 21745) cuyo
motivo declarado es «test» (deleted de guías 4495589 / 15183 desde la Consola). **Son HISTORIA** (bitácora
append-only) ⇒ **CONSERVAR**. No se proponen para borrado.

## 4. Guías con nombre de prueba
**6** guías con nombre tipo prueba (`UAT-*`, `DA2-*`, `V3-CONCIL`, `90000x`). **No** se proponen para borrado en
G4 (mix con documentos reales/legítimos); requiere análisis caso a caso.

## 5. Propuesta de script de limpieza (simulación, **NO ejecutado**)
```sql
-- DRY-RUN (solo lectura): qué se borraría (socios sin dependientes).
SELECT 'partner', id, name FROM res_partner
 WHERE name IN ('P Conc Fase 2','Proveedor TEST MADENAT')
   AND id NOT IN (SELECT partner_id FROM madenat_guia_processing WHERE partner_id IS NOT NULL)
   AND id NOT IN (SELECT partner_id FROM stock_picking WHERE partner_id IS NOT NULL)
   AND id NOT IN (SELECT partner_id FROM account_move WHERE partner_id IS NOT NULL);

-- DRY-RUN (solo lectura): usuarios @madenat.test inactivos.
SELECT 'user', id, login FROM res_users WHERE login LIKE '%@madenat.test' AND NOT active;
```
**Criterio de identificación seguro:** nombre exacto + `active=false` + **cero dependientes** (guías/pickings/
asientos). **Solo** esos 8 socios y 3 usuarios. **NO** tocar auditoría ni guías reales.

**Ejecución real (cuando Mauricio autorice):** `DELETE FROM res_groups_users_rel WHERE uid IN (…)` →
`res_users` → `res_partner`, con `pg_dump` previo. La variedad `mail_message`/`mail_followers` de esos socios se
borra en cascada por Odoo/`mail`.
