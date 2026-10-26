# Propuesta de borrado en dos tandas (C2) — sin ejecutar

**Versión documental:** 1.0.0
**Fecha:** 2026-10-26
**Base:** `FASES/00_CANDIDATOS_BORRADO_C1.csv` (94 carpetas) + D7 (94 `.tar.gz` verificados) + E8 (citas reescritas).

Ninguna carpeta se ha borrado. Esta lista solo se ejecuta con autorización expresa.

> **CORRECCIÓN DE FASE 4 (2026-10-26) — leer antes de ejecutar.** La medición de `config` de esta propuesta era
> errónea: `config/` **es la configuración viva** del stack (`./config:/etc/odoo` en `docker-compose.yml:17` y
> `--config /etc/odoo/odoo.conf` en `odoo18_app`, con sha256 idéntico host ↔ contenedor), por lo que queda
> **excluida**. `FASE12_REQUERIMIENTOS_OPERACIONES_20261017` queda **postergada** hasta aplicar el fix de
> `run_regression.sh`. La lista ejecutable es de **92 carpetas** (59 de la Tanda A y 33 de la Tanda B) y se
> materializa en `FASES/00_CUARENTENA_20261026.py`; el dry-run verificado está en
> `FASES/00_DRY_RUN_CUARENTENA_F4.txt`. Ver `FASES/00_INFORME_FASE4.md` §2 y §6.

## Resumen

| Tanda | Criterio | Carpetas | Tamaño | Copia íntegra verificada |
|---|---|---|---|---|
| **A** | no citadas en `CANON/`, `WIKI/` ni `RAW/` (`grep -w`) | **59** | 484.9 MB | 94/94 en D7 |
| **B** | citadas al menos una vez | **35** | 993.0 MB | 94/94 en D7 |
| | **total** | **94** | **1477.8 MB** | |

> **Discrepancia declarada.** El encargo hablaba de «45 no citadas + 33 citadas». La medición estricta
> (`grep -rlw <carpeta>` sobre `CANON/`, `WIKI/` y `RAW/`) da **59 + 35**. Los «33» provienen de contar solo
> las carpetas con **citas de ruta en backticks** (31) más 2 menciones sueltas; al contar también las
> menciones en prosa aparecen `config` (13 archivos) y `FASE13_INTAKE_ENGINE_20261023` (2 archivos).

## Tanda A — no citadas (borrado sin impacto documental)

| # | Carpeta | MB | Archivos | sha256 del `.tar.gz` (16) |
|---|---|---|---|---|
| A1 | `FIX_GUIA_DUP_FINAL_20261007_171740` | 99.9 | 12.323 | `103427c56b04c4a1` |
| A2 | `FIX_GUIA_DUP_CIERRE_20261007_170340` | 66.6 | 8.213 | `f66b2612c37a0e86` |
| A3 | `FIX_GUIA_DUP_20261007_164415` | 66.5 | 8.206 | `95bd4e227d085ba8` |
| A4 | `incident_recovery_audit` | 39.1 | 9 | `5e0ddecd7b341b89` |
| A5 | `REDISENO_REGISTRAR_REBAJA_20261010` | 36.2 | 15 | `8c7acf73aeffd2a6` |
| A6 | `IMPL_SV_REBAJA_OPERATIVA_20261010` | 34.7 | 17 | `c8d22356d40ff1f3` |
| A7 | `FIX_SV_SELECCIONAR_TODAS_20261010` | 34.2 | 14 | `c6915ec0b69b616f` |
| A8 | `FIX_ACL_GUIA_20261007_1630` | 32.6 | 1.709 | `838f7f89be0a073d` |
| A9 | `FASE5_COMMITS_20261015` | 21.7 | 36 | `394f5328b53b2af4` |
| A10 | `FIX_DELETE_INTAKE_20261007_145130` | 6.1 | 506 | `78fc221beb33baec` |
| A11 | `oracle_f31_20261003_165538` | 5.4 | 570 | `2ab6234b3712b39a` |
| A12 | `madenat_dev_p0r_20261003` | 5.4 | 570 | `e573a4b96403d9da` |
| A13 | `pre02_test_20261003_1541` | 5.4 | 570 | `9b68e31cb3efdc0c` |
| A14 | `pre02_postcommit_test_20261003_173746` | 5.4 | 569 | `2f5ef33cf73e5471` |
| A15 | `f31_test_20261003_1410` | 5.4 | 570 | `1ca6f73f0b516554` |
| A16 | `pre02_isolated_20261003` | 5.0 | 546 | `487cabd18c2ba2d0` |
| A17 | `AUDIT_DELETE_INTAKE_20261007_130559` | 1.9 | 57 | `d0b7803fa96adeae` |
| A18 | `HOTFIX_OWL_COLUMN_INVISIBLE_20261010` | 1.4 | 15 | `533bf0390cc65b16` |
| A19 | `_archive_pre_cleanup_20261003` | 1.3 | 32 | `bd529639062cbb1a` |
| A20 | `UI_LIMPIA_SV_20261010` | 1.1 | 12 | `68a30bb0456047b9` |
| A21 | `DIAGNOSTICO_SV000000841_20261012` | 1.1 | 4 | `27bacbd2547f99f5` |
| A22 | `pre02_audit` | 1.0 | 51 | `bce0c8883cffc744` |
| A23 | `IMPL_SEC_RECEPCION_20261004` | 0.7 | 11 | `8b4e7764ea10b8cd` |
| A24 | `oracle_f31_audit` | 0.6 | 32 | `4dfb345dd492622c` |
| A25 | `IMPL_DELIVER_D2_20261004` | 0.6 | 6 | `167564b57633cbbd` |
| A26 | `IMPL_B01_20261004` | 0.5 | 3 | `3c9b96e194e8bc15` |
| A27 | `UAT_R2_20261004` | 0.4 | 37 | `853e744428fcd116` |
| A28 | `IMPL_DELIVER_D2_C1_20261004` | 0.4 | 7 | `b075d8fa9f836a44` |
| A29 | `_archive_pre_cleanup_20260822` | 0.4 | 53 | `9c5e09c1c341b7ed` |
| A30 | `UAT_DELIVER_D2_20261004` | 0.4 | 13 | `ba016b2b9807636f` |
| A31 | `UAT_ROLLEO_EMBARQUE_20261005` | 0.4 | 10 | `8cf77befb217b499` |
| A32 | `FASE_B_20261007_153214` | 0.4 | 11 | `8cc0f45b3c0360e8` |
| A33 | `pre02_formalization_audit` | 0.3 | 32 | `eba2264278756a22` |
| A34 | `backups_provider_total_20260821_094139` | 0.3 | 3 | `16dad401a5c0e0b2` |
| A35 | `backups_20260821_20260821_091540` | 0.3 | 3 | `b845e60445869cae` |
| A36 | `backups_fix_proveedor_20260821_102851` | 0.3 | 6 | `d8cfa1393a37bbd8` |
| A37 | `ALINEACION_DOC_Y_PRE_DESPLIEGUE_20261012` | 0.3 | 13 | `7a5b3fe17de1c300` |
| A38 | `CIERRE_E1_20261005` | 0.2 | 13 | `de5848ad2fa892d3` |
| A39 | `UAT_B01_20261004` | 0.2 | 13 | `204fdb6ed41148cc` |
| A40 | `UAT_INTAKE_20261004` | 0.2 | 8 | `ff2704138c5d7ccf` |
| A41 | `UAT_DRAFT_20261004` | 0.2 | 11 | `979f2a7f8b7a816a` |
| A42 | `UAT_R1_20261004` | 0.1 | 19 | `eacb5f556d06bedf` |
| A43 | `FASE_C_20261007_154556` | 0.1 | 3 | `96faf39f06a89c93` |
| A44 | `AUDIT_R2_20261004` | 0.1 | 4 | `2c05ad14b96a6888` |
| A45 | `AUDIT_BUSQUEDA_FILTROS_INTAKE_20261007` | 0.1 | 6 | `6b3cd41d4be813d3` |
| A46 | `FASE_D_20261007_155057` | 0.0 | 6 | `ddbd01ee59588d7b` |
| A47 | `AUDIT_COSTING_20261004` | 0.0 | 4 | `57704aee8d4f7ccb` |
| A48 | `UAT_COSTING_C2_20261004` | 0.0 | 8 | `1282ba3481170af7` |
| A49 | `UAT_VR_20261004` | 0.0 | 6 | `18413f92b96960d7` |
| A50 | `AUDIT_DELIVER_20261004` | 0.0 | 3 | `f94a60cd60afdcee` |
| A51 | `backups_20260821_20260821_092634` | 0.0 | 1 | `98d53681858f0438` |
| A52 | `AUDIT_GUIA_DUPLICADOS_20261007` | 0.0 | 1 | `2f52d6468abac65c` |
| A53 | `UAT_INT_20261003` | 0.0 | 5 | `a188aa83f2c0ee0a` |
| A54 | `FASE9_VERIFICACION_REMOTO_20261015` | 0.0 | 2 | `bf89577179fcdcd6` |
| A55 | `pre02_publish_audit` | 0.0 | 4 | `78dda14efdddbdd8` |
| A56 | `pre02_isolated_audit` | 0.0 | 2 | `0e881a8f5436f8f6` |
| A57 | `madenat_dev_audit_20261003` | 0.0 | 1 | `93a364acbe728eed` |
| A58 | `appointment_crm` | 0.0 | 2 | `2f2659950d397fec` |
| A59 | `postgresql.conf` | 0.0 | 0 | `95f9024f5aeab9b7` |

## Tanda B — citadas (borrado con reescritura ya aplicada en E8)

| # | Carpeta | MB | Archivos | Citas (archivos) | sha256 del `.tar.gz` (16) | Riesgo |
|---|---|---|---|---|---|---|
| B1 | `AUDITORIA_INTEGRAL_20261012` | 175.8 | 97 | 2 | `28d38617bac1c9d3` |  |
| B2 | `BACKUP_AB_APPLY_20261008` | 140.4 | 23 | 2 | `8519a7460aeb3cfa` |  |
| B3 | `CONCILIACION_ENVIO_RETORNO_20261010` | 131.4 | 42 | 4 | `0e1857ce0ff01d73` |  |
| B4 | `AUDIT_REBAJA_ETIQUETAS_20261011` | 49.4 | 24 | 4 | `47c723b24ad3b281` |  |
| B5 | `FASE12_REQUERIMIENTOS_OPERACIONES_20261017` | 36.4 | 94 | 1 | `5fc98a00593af450` | **POSTERGADA (FASE 4)**: `run_regression.sh:11` escribe sus logs aquí (hace `mkdir -p`, no falla, pero el script escribiría en una carpeta de fase). No mover hasta aplicar el diff de `FASES/00_INFORME_FASE4.md` §3 |
| B6 | `INCIDENTE_GUIA_15183_20261007` | 34.1 | 4.119 | 2 | `d3fa4dee2dd97e2b` |  |
| B7 | `APPLY_AB_UI_20261008` | 34.0 | 27 | 3 | `5ec7c02aa9f6c851` |  |
| B8 | `BLINDAJE_SOBRESCRITURA_20261012` | 33.6 | 18 | 1 | `9e944e8f58b3ad31` |  |
| B9 | `BLINDAJE_REBAJA_LOCAL_20261012` | 33.6 | 22 | 2 | `6ff4e598536d5de4` |  |
| B10 | `VERIF_CUATRO_PUNTOS_20261012` | 33.6 | 19 | 1 | `271f8614d4f272b7` |  |
| B11 | `CIERRE_SOBRESCRITURA_V123_20261012` | 33.1 | 19 | 1 | `36a955dd4759ff94` |  |
| B12 | `APPLY_BUSQUEDA_INTAKE_20261007` | 31.8 | 17 | 4 | `e9acbb0b125001ec` |  |
| B13 | `FASE11_INTEGRIDAD_CICLO_IMPUTACIONES_20261015` | 31.5 | 64 | 2 | `8cca41ddc1327af9` |  |
| B14 | `FASE7_CIERRE_D18_20261015` | 23.7 | 49 | 1 | `69ddd7f1ce88e47b` |  |
| B15 | `FASE8_CIERRE_DR_20261015` | 23.6 | 43 | 1 | `88c4572fbab7a7b3` |  |
| B16 | `FASE10_REBAJA_SV_ETIQUETAS_20261015` | 16.5 | 41 | 3 | `5e4e771ad9cd0228` |  |
| B17 | `IMPL_ASSIGN_SV_20261010_165247` | 14.7 | 22 | 2 | `774b6ada92c5a7ac` |  |
| B18 | `UNIFY_SV_REBAJA_MENU_20261010` | 14.1 | 17 | 1 | `1651b0df127ad113` |  |
| B19 | `SAVE_REBAJA_20261011` | 14.0 | 8 | 4 | `a7a326d31d4519de` |  |
| B20 | `RESET_REBAJA_20261011` | 13.8 | 7 | 4 | `81da5fb1f90a9d39` |  |
| B21 | `SIMPLE_REBAJA_20261011` | 13.8 | 7 | 4 | `b5d37c191680383d` |  |
| B22 | `UI_SAVE_REBAJA_20261011` | 13.5 | 6 | 4 | `61c20841c1570ea6` |  |
| B23 | `CIERRE_PENDIENTES_20261010` | 12.1 | 8 | 2 | `4cf2914845b8bd53` |  |
| B24 | `HOTFIX_OWL_CHATTER_OE_20261012` | 9.2 | 17 | 3 | `b7ff6a635f5b127c` |  |
| B25 | `IMPL_SERVICE_RETURN_20261006` | 8.9 | 686 | 3 | `9967c5e4e45bc366` |  |
| B26 | `IMPL_SERVICE_RETURN_AB_20261007` | 7.7 | 524 | 5 | `4f0739cde86a1187` |  |
| B27 | `IMPL_BUSQUEDA_INTAKE_20261007` | 5.2 | 504 | 2 | `fb018b510dc189ee` |  |
| B28 | `FASE6_HEAD_CHECK_20261015` | 2.1 | 23 | 1 | `c91054d8d58416bf` |  |
| B29 | `CONTRATO_APLICACION_20261011` | 0.8 | 7 | 4 | `4e2804b8ecced23d` |  |
| B30 | `FASE13_INTAKE_ENGINE_20261023` | 0.3 | 8 | 2 | `89af9e9fba29b0f1` |  |
| B31 | `AUDITORIA_DISPONIBILIDAD_ETIQUETAS_20261015` | 0.1 | 8 | 1 | `f106c6b813edc6b1` |  |
| B32 | `AUDITORIA_CICLO_VIDA_IMPUTACIONES_20261015` | 0.1 | 15 | 1 | `728d2bfd87ae8330` |  |
| B33 | `DIAGNOSTICO_REBAJA_SV841_REGISTRO_ETIQUETAS_20261015` | 0.0 | 11 | 2 | `9c29223a512913f7` |  |
| B34 | `AUDIT_B01_20261004` | 0.0 | 1 | 1 | `b4820da3b17e84fe` |  |
| B35 | `config` | 0.0 | 1 | 13 | `dce264820c588547` | **EXCLUIDA (FASE 4)**: es la configuración viva (`./config:/etc/odoo` + `--config /etc/odoo/odoo.conf`); moverla deja el contenedor sin `odoo.conf` |

## Condiciones previas a ejecutar cualquiera de las dos tandas

1. D7 verificado: 94/94 `.tar.gz` con conteo y bytes idénticos al original (`FASE13_20261023/evidencias/SHA256_BACKUPS_CONSOLIDACION.csv`) y bundle `git bundle verify` = completo.
2. E8 aplicado: 0 enlaces rotos y 0 citas en backticks que resuelvan solo en la raíz para carpetas de fase.
3. Decisión sobre `FASE12_REQUERIMIENTOS_OPERACIONES_20261017`: o se conserva la carpeta, o se acepta que
   `run_regression.sh` cree el directorio de logs de nuevo (hace `mkdir -p`; no falla).
4. `config/` **excluida** de ambas tandas: es la configuración viva del stack (`./config:/etc/odoo` +
   `--config /etc/odoo/odoo.conf`), no una carpeta de fase. Ver `FASES/00_INFORME_FASE4.md` §2.1.

## Orden propuesto

1. **Cuarentena reversible** (no borrado): `python3 FASES/00_CUARENTENA_20261026.py --tanda A` (simulación ya
   verificada: 59 aptas, 0 bloqueadas) y, tras el OK, `--ejecutar --tanda A`. El script verifica `.tar.gz`,
   rutas/bytes, procesos y bind mounts antes de cada `mv`, y deja diario con reversión.
2. **Tanda B** (33 carpetas ejecutables; `config` excluida y `FASE12_…` postergada): reejecutar `check_links` /
   `check_paths` después; si algún documento vuelve a citar una ruta de raíz, corregirlo antes de seguir.
3. Nunca borrar los `.tar.gz` de D7 en la misma operación.
