# T1 — Auditoría de fixtures de las suites con `commit()`/conexiones independientes (solo revisión)

**Alcance:** solo revisión + consulta empírica de solo lectura. **No** se corrigió ningún test.

| Suite | Clase / tipo | Qué crea fuera del rollback | Limpieza | Riesgo de residuo | Recomendación |
|---|---|---|---|---|---|
| `madenat_lumber_core/tests/test_sv_concurrency.py` | `SingleTransactionCase` | lotes/marks vía `_sv_test_mark`; `commit()` | `_sv_cleanup` → `_sv_test_cleanup(token)` + `commit` | **Bajo** | mantener (mecanismo sancionado) |
| `.../test_sv_rebaja_reset_concurrency.py` | `SingleTransactionCase` | guías/lotes/imputaciones/usuarios/proveedor; 2 conexiones | `tearDownClass` con `DELETE FROM` (users, product, partner, audit, mail_message, imputation, lot, guía) | **Bajo-Medio** (si el proceso muere) | mantener; verificar `finally` |
| `.../test_sv_rebaja_save_lock.py` | `TransactionCase` + `…Concurrency(SingleTransactionCase)` | guías/lotes/imputaciones | `tearDownClass` `DELETE FROM` | **Bajo-Medio** | mantener |
| `.../test_sv_rebaja_reset_lot_capacity.py` | `SingleTransactionCase` | guías/lotes/usuarios | `tearDownClass` `DELETE FROM` | **Bajo-Medio** | mantener |
| `.../test_sv_rebaja_save_lock_tx.py` | `TransactionCase` + `…Concurrency(SingleTransactionCase)` | guías/lotes/usuarios | `tearDownClass` `DELETE FROM` | **Bajo-Medio** | mantener |
| `.../test_intake_metrics_recompute.py` | `SingleTransactionCase` | guía + proveedor; 2ª conexión | `tearDownClass` `DELETE FROM` (guía, partner) | **Bajo-Medio** | mantener |
| **`.../test_guide_lifecycle_phase2.py`** | `TransactionCase` ×2 + **`TestDeleteConcurrency(SingleTransactionCase)`** | **socio + guía `DA2-CONC-GUIA`**, `commit()` + 2ª conexión | **`TestDeleteConcurrency` SIN `tearDownClass` ni `addCleanup`** | **ALTO** | **añadir limpieza** (REQUIERE_DECISIÓN) |

## Residuos observados (consulta empírica de solo lectura sobre `madenat_test`)
| Residuo | Cantidad | Origen probable |
|---|---|---|
| `res_partner` «**P Conc Fase 2**» | **7** (2026-10-10 y 2026-10-12) | `TestDeleteConcurrency` (sin limpieza) |
| `res_partner` «Proveedor TEST MADENAT» | 1 (ejecución antigua) | suite de intake |
| `res_users` `*@madenat.test` (inactivos) | 3 (`v3_concil_oper`, `v3_concil_jef`, `impl_sv_check`) | suites de concurrencia (limpieza no efectiva) |
| `madenat_audit_log` con «test» en descripción | 11 | pruebas |
| Guías/test con nombre de prueba (`V3-CONCIL`, `UAT-*`, `900001/900002`) | varias | fixtures históricos |
| Lotes con nombre «test» | **0** | — |

**Conclusión:** el riesgo de residuo está **caracterizado**; el caso **ALTO** es `TestDeleteConcurrency`
(7 socios acumulados). **No** se corrige en esta fase. **Recomendación:** añadir `tearDownClass` que borre el
socio+guía (o usar `_sv_test_mark`/`cleanup`), y para los residuos existentes: **dry-run + autorización**
(no ejecutado).
