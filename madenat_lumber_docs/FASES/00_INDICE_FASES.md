# Índice de carpetas de fase consolidadas — `madenat_lumber_docs/FASES/`

**Versión documental:** 1.2.0
**Fecha:** 2026-10-26
**Origen:** consolidación documental FASE 2, etapas E4 (D4), E8 y D7; §4 añadida en FASE 4 (2026-10-26).

> **Nota de consolidación (FASE 2, 2026-10-26).** Las referencias a expedientes de fase se reescribieron a
> `FASES/<CARPETA>/…` en los documentos canónicos, en la WIKI y en las propias copias de `FASES/` (ver
> `FASES/00_VERIFICACION_E8.md`). El texto, las fechas y las cifras históricas no se alteraron: solo cambió el
> puntero. Los artefactos no versionados (`logs/`, `db/`, dumps, código de evidencia) se citan por nombre de
> archivo y carpeta de origen.

Cada carpeta de fase que vivía en la raíz del stack (`/home/viruco/dev-stack/odoo/odoo-18-ce/`,
fuera de git) tiene ahora una copia versionada en `madenat_lumber_docs/FASES/<CARPETA>/`,
restringida a documentación: `.md`, `.txt`, `.csv`, `.pdf`, `.xlsx`, `.xls` menores de 2 MB por archivo.
Los originales **siguen en su sitio** hasta que se autorice su borrado en el punto de control C1, y ya
están comprimidos y verificados en `/mnt/g/madenat_respaldos/consolidacion_20261026/<CARPETA>.tar.gz`
(94/94, D7: `FASE13_20261023/evidencias/SHA256_BACKUPS_CONSOLIDACION.csv`). Esa ruta está en la unidad `G:`
de Windows: **sin el disco montado no existe** (ver `CANON/02_CONTINUIDAD.md` §22.6).

**No versionado en git (por diseño del filtro):** `addons/`, `workcopy/`, `verify_*`, `respaldos/`,
`backups_*`, `*.dump`, `*.sql`, `*.tar*`, `*.log` de más de 1 MB y binarios de más de 2 MB.
Esos restos viajan íntegros en los `.tar.gz` de D7.

**Manifiestos de verificación:** `FASES/00_MANIFIESTO_CONSOLIDACION_ANTES.csv` (línea base completa)
y `FASES/00_MANIFIESTO_TANDA_1..8.csv` (sha256 origen vs copiado por tanda).

---

## 1. Carpetas consolidadas con documentación en git

| Carpeta | Fecha | Resumen (primer encabezado del informe) | Estado | Ruta nueva | No versionado (→ tar.gz en C1) |
|---|---|---|---|---|---|
| `ALINEACION_DOC_Y_PRE_DESPLIEGUE_20261012` | 2026-10-12 | ALINEACION_DOC_Y_PRE_DESPLIEGUE_20261012 — Alineación documental + inventario + inspección previa | Consolidada | `FASES/ALINEACION_DOC_Y_PRE_DESPLIEGUE_20261012/` (2 arch., 12,196 B) | — |
| `APPLY_AB_UI_20261008` | 2026-10-08 | APPLY_AB_UI_20261008 — Implementación A/B + reorganización de UI en `madenat_test` (2026-10-08) | Consolidada | `FASES/APPLY_AB_UI_20261008/` (6 arch., 49,471 B) | — |
| `APPLY_BUSQUEDA_INTAKE_20261007` | 2026-10-07 | APPLY_BUSQUEDA_INTAKE_20261007 — Aplicación en madenat_test | Consolidada | `FASES/APPLY_BUSQUEDA_INTAKE_20261007/` (9 arch., 22,887 B) | — |
| `AUDITORIA_CICLO_VIDA_IMPUTACIONES_20261015` | 2026-10-15 | AUDITORÍA FUNCIONAL — CICLO DE VIDA DE LAS IMPUTACIONES SV (SOLO LECTURA) | Consolidada | `FASES/AUDITORIA_CICLO_VIDA_IMPUTACIONES_20261015/` (1 arch., 31,556 B) | — |
| `AUDITORIA_DISPONIBILIDAD_ETIQUETAS_20261015` | 2026-10-15 | AUDITORÍA — DISPONIBILIDAD DE ETIQUETAS EN EL FORMULARIO DE IMPUTACIÓN (SOLO LECTURA) | Consolidada | `FASES/AUDITORIA_DISPONIBILIDAD_ETIQUETAS_20261015/` (1 arch., 18,046 B) | — |
| `AUDITORIA_INTEGRAL_20261012` | 2026-10-12 | FASE 2 LIMITADA (rev. 2) — ENTREGA FINAL (higiene + H-SEC-1/D15 formalizada) | Consolidada | `FASES/AUDITORIA_INTEGRAL_20261012/` (47 arch., 1,761,979 B) | — |
| `AUDIT_B01_20261004` | 2026-10-04 | MADENAT — Auditoría Zarpe con Excepción B-01 | Consolidada | `FASES/AUDIT_B01_20261004/` (1 arch., 23,788 B) | — |
| `AUDIT_BUSQUEDA_FILTROS_INTAKE_20261007` | 2026-10-07 | BASELINE — Auditoría de búsqueda, filtros y agrupaciones de Intake | Consolidada | `FASES/AUDIT_BUSQUEDA_FILTROS_INTAKE_20261007/` (6 arch., 52,674 B) | — |
| `AUDIT_COSTING_20261004` | 2026-10-04 | MADENAT — Auditoría Costeo y Valorización Post-Entrega | Consolidada | `FASES/AUDIT_COSTING_20261004/` (3 arch., 35,711 B) | — |
| `AUDIT_DELETE_INTAKE_20261007_130559` | 2026-10-07 | SNAPSHOT (copia histórica — NO es la fuente canónica) | Consolidada | `FASES/AUDIT_DELETE_INTAKE_20261007_130559/` (10 arch., 327,641 B) | — |
| `AUDIT_DELIVER_20261004` | 2026-10-04 | MADENAT — Auditoría Entrega y Cierre Seguro | Consolidada | `FASES/AUDIT_DELIVER_20261004/` (2 arch., 21,978 B) | — |
| `AUDIT_GUIA_DUPLICADOS_20261007` | 2026-10-07 | Validación de "guía ya ingresada" en la ingesta — auditoría focalizada y propuesta mínima | Consolidada | `FASES/AUDIT_GUIA_DUPLICADOS_20261007/` (1 arch., 22,087 B) | — |
| `AUDIT_R2_20261004` | 2026-10-04 | MADENAT — Resultado Corrección Aislamiento Rolleo y Regresión R2 | Consolidada | `FASES/AUDIT_R2_20261004/` (4 arch., 65,126 B) | — |
| `AUDIT_REBAJA_ETIQUETAS_20261011` | 2026-10-11 | AUDITORÍA INTEGRAL — CICLO DE REBAJA DE ETIQUETAS (MADENAT, Odoo 18 CE) | Consolidada | `FASES/AUDIT_REBAJA_ETIQUETAS_20261011/` (5 arch., 43,703 B) | — |
| `BACKUP_AB_APPLY_20261008` | 2026-10-08 | Sin encabezado H1 — archivos consolidados: `HEAD.txt`, `git_status_antes.txt` | Consolidada | `FASES/BACKUP_AB_APPLY_20261008/` (2 arch., 3,808 B) | — |
| `BLINDAJE_REBAJA_LOCAL_20261012` | 2026-10-12 | BLINDAJE LOCAL Y ESTABILIZACIÓN DEL FLUJO DE REBAJAS — ENTREGA (2026-10-12) | Consolidada | `FASES/BLINDAJE_REBAJA_LOCAL_20261012/` (9 arch., 35,694 B) | — |
| `BLINDAJE_SOBRESCRITURA_20261012` | 2026-10-12 | BLINDAJE DE BORRADORES — PROTECCIÓN CONTRA SOBRESCRITURA CONCURRENTE — ENTREGA (2026-10-12) | Consolidada | `FASES/BLINDAJE_SOBRESCRITURA_20261012/` (7 arch., 28,835 B) | — |
| `CIERRE_E1_20261005` | 2026-10-05 | MADENAT — Cierre Entrega 1 Operativa | Consolidada | `FASES/CIERRE_E1_20261005/` (10 arch., 224,747 B) | — |
| `CIERRE_PENDIENTES_20261010` | 2026-10-10 | CIERRE_PENDIENTES_20261010 — Evidencia del cierre funcional (P0–P4) | Consolidada | `FASES/CIERRE_PENDIENTES_20261010/` (1 arch., 2,219 B) | — |
| `CIERRE_SOBRESCRITURA_V123_20261012` | 2026-10-12 | CIERRE DE V1–V3 DEL BLINDAJE DE SOBRESCRITURA — ENTREGA (2026-10-12) | Consolidada | `FASES/CIERRE_SOBRESCRITURA_V123_20261012/` (10 arch., 37,247 B) | — |
| `CONCILIACION_ENVIO_RETORNO_20261010` | 2026-10-10 | CONCILIACION_ENVIO_RETORNO_20261010 — Evidencia (Bloque A/B/C) | Consolidada | `FASES/CONCILIACION_ENVIO_RETORNO_20261010/` (12 arch., 18,086 B) | — |
| `CONTRATO_APLICACION_20261011` | 2026-10-11 | CONTRATO DE APLICACIÓN (REBAJA A SV) — PROPUESTA PARA APROBACIÓN | Consolidada | `FASES/CONTRATO_APLICACION_20261011/` (4 arch., 14,031 B) | — |
| `DIAGNOSTICO_REBAJA_SV841_REGISTRO_ETIQUETAS_20261015` | 2026-10-15 | DIAGNÓSTICO — REGISTRO DE ETIQUETAS EN «REBAJA DE ETIQUETAS» (SV00000000841 / IMP04823) — 2026-10-15 | Consolidada | `FASES/DIAGNOSTICO_REBAJA_SV841_REGISTRO_ETIQUETAS_20261015/` (2 arch., 29,078 B) | — |
| `DIAGNOSTICO_SV000000841_20261012` | 2026-10-12 | CORRECCIÓN MÍNIMA Y PRUEBAS — guarda de eliminación de etiqueta SV (2026-10-12) | Consolidada | `FASES/DIAGNOSTICO_SV000000841_20261012/` (2 arch., 23,474 B) | — |
| `FASE10_REBAJA_SV_ETIQUETAS_20261015` | 2026-10-15 | INFORME FASE 10 — Corrección del registro de etiquetas en la rebaja SV (S2, S3, S1) | Consolidada | `FASES/FASE10_REBAJA_SV_ETIQUETAS_20261015/` (23 arch., 57,586 B) | — |
| `FASE11_INTEGRIDAD_CICLO_IMPUTACIONES_20261015` | 2026-10-15 | INFORME FASE 11 — Integridad del ciclo de vida de las imputaciones SV (A-1, B-1, M-2, M-4, B-2, B-3) | Consolidada | `FASES/FASE11_INTEGRIDAD_CICLO_IMPUTACIONES_20261015/` (21 arch., 31,690 B) | — |
| `FASE12_REQUERIMIENTOS_OPERACIONES_20261017` | 2026-10-17 | INFORME BLOQUE 1 — FASE 12 (WP-C y WP-B Rótulos) | Consolidada · mixta (documentación en git, código fuera) | `FASES/FASE12_REQUERIMIENTOS_OPERACIONES_20261017/` (10 arch., 131,877 B) | `respaldos/` |
| `FASE5_COMMITS_20261015` | 2026-10-15 | FASE 5 — COMMITS ORDENADOS (SOLO LOCAL) — INFORME DE CIERRE | Consolidada | `FASES/FASE5_COMMITS_20261015/` (20 arch., 86,838 B) | — |
| `FASE6_HEAD_CHECK_20261015` | 2026-10-15 | INFORME V2 — INVESTIGACIÓN D18 (5 archivos) Y P2-2 (menú de reports) | Consolidada | `FASES/FASE6_HEAD_CHECK_20261015/` (10 arch., 66,066 B) | — |
| `FASE7_CIERRE_D18_20261015` | 2026-10-15 | FASE 7 — CIERRE DE D18, REPARACIÓN DE INSTALACIÓN DESDE CERO Y RE-VERIFICACIÓN — INFORME | Consolidada | `FASES/FASE7_CIERRE_D18_20261015/` (21 arch., 42,030 B) | — |
| `FASE8_CIERRE_DR_20261015` | 2026-10-15 | FASE 8 — CIERRE DE LA INSTALACIÓN DESDE CERO DE LOGISTICS Y PRUEBA `-u` LIMPIA — INFORME | Consolidada | `FASES/FASE8_CIERRE_DR_20261015/` (21 arch., 42,852 B) | — |
| `FASE9_VERIFICACION_REMOTO_20261015` | 2026-10-15 | INFORME FASE 9 — VERIFICACIÓN PREVIA DEL TEST REMOTO (SOLO LECTURA) — **NO-GO** | Consolidada | `FASES/FASE9_VERIFICACION_REMOTO_20261015/` (1 arch., 12,973 B) | — |
| `FASE_B_20261007_153214` | 2026-10-07 | FASE B — Aplicación controlada del parche (RESUMEN DE CIERRE) | Consolidada | `FASES/FASE_B_20261007_153214/` (10 arch., 25,628 B) | — |
| `FASE_C_20261007_154556` | 2026-10-07 | FASE C — Reparación del FK espurio del retorno 7813 (RESUMEN DE CIERRE) | Consolidada | `FASES/FASE_C_20261007_154556/` (2 arch., 5,851 B) | — |
| `FASE_D_20261007_155057` | 2026-10-07 | GUION BREVE — Verificación de pantalla (Fase D) | Consolidada | `FASES/FASE_D_20261007_155057/` (4 arch., 12,327 B) | — |
| `FIX_ACL_GUIA_20261007_1630` | 2026-10-07 | FIX_ACL_GUIA_20261007_1630 — Fallo de acceso omitido en la eliminación (ACL) | Consolidada · mixta (documentación en git, código fuera) | `FASES/FIX_ACL_GUIA_20261007_1630/` (1 arch., 12,916 B) | `addons/`, `verify_unpatched/` |
| `FIX_DELETE_INTAKE_20261007_145130` | 2026-10-07 | FIX_DELETE_INTAKE_20261007_145130 — Eliminación robusta de ingresos cancelados | Consolidada · mixta (documentación en git, código fuera) | `FASES/FIX_DELETE_INTAKE_20261007_145130/` (10 arch., 42,527 B) | `addons/` |
| `FIX_GUIA_DUP_20261007_164415` | 2026-10-07 | INFORME — Validación efectiva de guías duplicadas en la ingesta | Consolidada · mixta (documentación en git, código fuera) | `FASES/FIX_GUIA_DUP_20261007_164415/` (6 arch., 21,597 B) | `addons/`, `verify_unpatched/` |
| `FIX_GUIA_DUP_CIERRE_20261007_170340` | 2026-10-07 | Informe — Cierre mínimo de validación de duplicados en la ingesta | Consolidada · mixta (documentación en git, código fuera) | `FASES/FIX_GUIA_DUP_CIERRE_20261007_170340/` (7 arch., 22,206 B) | `addons/`, `verify_unpatched/` |
| `FIX_GUIA_DUP_FINAL_20261007_171740` | 2026-10-07 | Informe — Cierre final de avisos y compatibilidad | Consolidada · mixta (documentación en git, código fuera) | `FASES/FIX_GUIA_DUP_FINAL_20261007_171740/` (8 arch., 26,818 B) | `addons/`, `verify_apply/`, `verify_unpatched/` |
| `FIX_SV_SELECCIONAR_TODAS_20261010` | 2026-10-10 | FIX_SV_SELECCIONAR_TODAS_20261010 — Evidencia (corrección «Seleccionar todas» + asignación explícita) | Consolidada | `FASES/FIX_SV_SELECCIONAR_TODAS_20261010/` (6 arch., 14,988 B) | — |
| `HOTFIX_OWL_CHATTER_OE_20261012` | 2026-10-12 | HOTFIX_OWL_CHATTER_OE_20261012 — Evidencia (OwlError al «Agregar una línea» en IMPxxxx) | Consolidada | `FASES/HOTFIX_OWL_CHATTER_OE_20261012/` (7 arch., 47,531 B) | — |
| `HOTFIX_OWL_COLUMN_INVISIBLE_20261010` | 2026-10-10 | HOTFIX_OWL_COLUMN_INVISIBLE_20261010 — Evidencia (OwlError al abrir «Registrar rebaja») | Consolidada | `FASES/HOTFIX_OWL_COLUMN_INVISIBLE_20261010/` (3 arch., 7,746 B) | — |
| `IMPL_ASSIGN_SV_20261010_165247` | 2026-10-10 | IMPL_ASSIGN_SV_20261010 — Evidencia (Operación manual de asignaciones centrada en SV) | Consolidada | `FASES/IMPL_ASSIGN_SV_20261010_165247/` (9 arch., 21,595 B) | — |
| `IMPL_B01_20261004` | 2026-10-04 | MADENAT — Resultado Implementación B-01 Documental Bloqueante | Consolidada | `FASES/IMPL_B01_20261004/` (1 arch., 11,647 B) | — |
| `IMPL_BUSQUEDA_INTAKE_20261007` | 2026-10-07 | IMPL_BUSQUEDA_INTAKE_20261007 — Mejora mínima de búsqueda/filtros/agrupación de Intake | Consolidada · mixta (documentación en git, código fuera) | `FASES/IMPL_BUSQUEDA_INTAKE_20261007/` (4 arch., 18,353 B) | `addons/` |
| `IMPL_DELIVER_D2_20261004` | 2026-10-04 | MADENAT — Resultado Implementación Entrega Segura D2 | Consolidada | `FASES/IMPL_DELIVER_D2_20261004/` (4 arch., 14,479 B) | — |
| `IMPL_DELIVER_D2_C1_20261004` | 2026-10-04 | MADENAT — Resultado Micro-Parche P0 Create Entrega D2 | Consolidada | `FASES/IMPL_DELIVER_D2_C1_20261004/` (5 arch., 11,014 B) | — |
| `IMPL_SEC_RECEPCION_20261004` | 2026-10-04 | MADENAT — Resultado Parche Integral Seguridad Recepción / Guías | Consolidada | `FASES/IMPL_SEC_RECEPCION_20261004/` (9 arch., 39,105 B) | — |
| `IMPL_SERVICE_RETURN_20261006` | 2026-10-06 | RESULTADO — Confirmación de retorno de servicio (2026-10-06) | Consolidada · mixta (documentación en git, código fuera) | `FASES/IMPL_SERVICE_RETURN_20261006/` (1 arch., 2,017 B) | `addons/` |
| `IMPL_SERVICE_RETURN_AB_20261007` | 2026-10-07 | IMPL_SERVICE_RETURN_AB_20261007 — Retorno de servicio (identificación no bloqueante) + imputación posterior | Consolidada · mixta (documentación en git, código fuera) | `FASES/IMPL_SERVICE_RETURN_AB_20261007/` (5 arch., 27,803 B) | `addons/` |
| `IMPL_SV_REBAJA_OPERATIVA_20261010` | 2026-10-10 | IMPL_SV_REBAJA_OPERATIVA_20261010 — Evidencia (operación y blindaje «Rebaja de etiquetas») | Consolidada | `FASES/IMPL_SV_REBAJA_OPERATIVA_20261010/` (7 arch., 16,807 B) | — |
| `INCIDENTE_GUIA_15183_20261007` | 2026-10-07 | COMPARACIÓN DOCUMENTAL — guía 15183 (Recepción 1369 vs Guía 33154) | Consolidada · mixta (documentación en git, código fuera) | `FASES/INCIDENTE_GUIA_15183_20261007/` (13 arch., 58,386 B) | `workcopy/` |
| `REDISENO_REGISTRAR_REBAJA_20261010` | 2026-10-10 | REDISENO_REGISTRAR_REBAJA_20261010 — Evidencia (rediseño operativo del asistente) | Consolidada | `FASES/REDISENO_REGISTRAR_REBAJA_20261010/` (6 arch., 15,636 B) | — |
| `RESET_REBAJA_20261011` | 2026-10-11 | VOLVER A BORRADOR Y REASIGNAR REBAJAS (RESET) — 2026-10-11 | Consolidada | `FASES/RESET_REBAJA_20261011/` (3 arch., 9,813 B) | — |
| `SAVE_REBAJA_20261011` | 2026-10-11 | PERSISTENCIA Y RECUPERACIÓN DEL TRABAJO DE REBAJA (SAVE) — 2026-10-11 | Consolidada | `FASES/SAVE_REBAJA_20261011/` (3 arch., 11,447 B) | — |
| `SIMPLE_REBAJA_20261011` | 2026-10-11 | SIMPLIFICACIÓN OPERATIVA DE LA REBAJA — 2026-10-11 | Consolidada | `FASES/SIMPLE_REBAJA_20261011/` (3 arch., 9,468 B) | — |
| `UAT_B01_20261004` | 2026-10-04 | MADENAT — Resultado UAT B-01 Documental Bloqueante | Consolidada | `FASES/UAT_B01_20261004/` (13 arch., 218,405 B) | — |
| `UAT_COSTING_C2_20261004` | 2026-10-04 | MADENAT — Resultado UAT Costeo C2 | Consolidada | `FASES/UAT_COSTING_C2_20261004/` (8 arch., 36,185 B) | — |
| `UAT_DELIVER_D2_20261004` | 2026-10-04 | MADENAT — Resultado UAT Entrega Segura D2 | Consolidada | `FASES/UAT_DELIVER_D2_20261004/` (9 arch., 327,480 B) | — |
| `UAT_DRAFT_20261004` | 2026-10-04 | MADENAT — Resultado UAT Borrador Seguro | Consolidada | `FASES/UAT_DRAFT_20261004/` (11 arch., 161,361 B) | — |
| `UAT_INTAKE_20261004` | 2026-10-04 | MADENAT — Resultado UAT Ingreso de Madera, Inventario y Bodega | Consolidada | `FASES/UAT_INTAKE_20261004/` (6 arch., 176,578 B) | — |
| `UAT_INT_20261003` | 2026-10-03 | Sin encabezado H1 — archivos consolidados: `UAT-INT-PROC-20261003-01_guia.pdf`, `UAT-INT-PROC-20261003-01_packing.xls`, `UAT-INT-PROC-20261003-01_packing.xlsx`, `UAT-INT-PROD-20261003-01_guia.pdf` (+1 más) | Consolidada | `FASES/UAT_INT_20261003/` (5 arch., 19,021 B) | — |
| `UAT_R1_20261004` | 2026-10-04 | MADENAT — Resultado UAT R1 y Cierre B-01 | Consolidada | `FASES/UAT_R1_20261004/` (9 arch., 47,899 B) | — |
| `UAT_R2_20261004` | 2026-10-04 | MADENAT — Resultado Habilitación Jefatura Operativa para UAT R2 | Consolidada | `FASES/UAT_R2_20261004/` (27 arch., 415,498 B) | — |
| `UAT_ROLLEO_EMBARQUE_20261005` | 2026-10-05 | Sin encabezado H1 — archivos consolidados: `02_exitcode.txt`, `03_uat_exit.txt` | Consolidada | `FASES/UAT_ROLLEO_EMBARQUE_20261005/` (2 arch., 20 B) | — |
| `UAT_VR_20261004` | 2026-10-04 | MADENAT — Resultado UAT Rolleo de Motonave | Consolidada | `FASES/UAT_VR_20261004/` (6 arch., 27,319 B) | — |
| `UI_LIMPIA_SV_20261010` | 2026-10-10 | UI_LIMPIA_SV_20261010 — Evidencia (interfaz clara y concisa de «Registrar rebaja») | Consolidada | `FASES/UI_LIMPIA_SV_20261010/` (2 arch., 8,529 B) | — |
| `UI_SAVE_REBAJA_20261011` | 2026-10-11 | ACCIONES VISIBLES DEL ASISTENTE «REGISTRAR REBAJA» (UI) — 2026-10-11 | Consolidada | `FASES/UI_SAVE_REBAJA_20261011/` (3 arch., 9,879 B) | — |
| `UNIFY_SV_REBAJA_MENU_20261010` | 2026-10-10 | UNIFY_SV_REBAJA_MENU_20261010 — Evidencia (único acceso «Rebaja de etiquetas») | Consolidada | `FASES/UNIFY_SV_REBAJA_MENU_20261010/` (8 arch., 19,996 B) | — |
| `VERIF_CUATRO_PUNTOS_20261012` | 2026-10-12 | VERIFICACIÓN PROBATORIA DE CUATRO PUNTOS DE BLINDAJE — ENTREGA (2026-10-12) | Consolidada | `FASES/VERIF_CUATRO_PUNTOS_20261012/` (8 arch., 35,656 B) | — |
| `incident_recovery_audit` | 2026-10-03 | INCIDENTE MADENAT — RECUPERACIÓN CÓDIGO ↔ DB | Consolidada | `FASES/incident_recovery_audit/` (8 arch., 162,311 B) | — |
| `madenat_dev_audit_20261003` | 2026-10-03 | ENTORNOS DE TRABAJO — MADENAT | Consolidada | `FASES/madenat_dev_audit_20261003/` (1 arch., 2,746 B) | — |
| `oracle_f31_audit` | 2026-10-03 | ORÁCULO INTEGRAL F3.1 — Cierre PRE-01 / PRE-02 | Consolidada | `FASES/oracle_f31_audit/` (4 arch., 20,490 B) | — |
| `pre02_audit` | 2026-10-03 | Sin encabezado H1 — archivos consolidados: `final_diff.stat.txt`, `final_sha256.txt` | Consolidada | `FASES/pre02_audit/` (2 arch., 434 B) | — |
| `pre02_formalization_audit` | 2026-10-03 | PRE-02 / F3.1 — Formalización Local y Validación Post-Commit | Consolidada | `FASES/pre02_formalization_audit/` (9 arch., 40,886 B) | — |
| `pre02_isolated_audit` | 2026-10-03 | Sin encabezado H1 — archivos consolidados: `00_summary.txt`, `cherry_pick_conflict.txt` | Consolidada | `FASES/pre02_isolated_audit/` (2 arch., 3,115 B) | — |
| `pre02_publish_audit` | 2026-10-03 | Sin encabezado H1 — archivos consolidados: `01_preflight_local_remote.txt`, `02_publish_and_pr.txt`, `CURRENT_TS.txt`, `pr_body.md` | Consolidada | `FASES/pre02_publish_audit/` (4 arch., 7,632 B) | — |

**Subtotal:** 78 carpetas, 568 archivos, 5,627,119 bytes (5.37 MB).

## 2. Carpetas sin documentación versionable

| Carpeta | Estado | Ruta nueva | No versionado (→ tar.gz en C1) |
|---|---|---|---|
| `_archive_pre_cleanup_20260822` | Sin documentación (0 archivos del filtro) | — | `backups_20260819_093933/`, `backups_20260819_121900/`, `backups_20260819_2105/`, `backups_20260819_2156/`, `backups_20260819_2218/`, `backups_20260819_2236/` |
| `appointment_crm` | Sin documentación (0 archivos del filtro) | — | carpeta completa |
| `backups_20260821_20260821_091540` | Sin documentación (0 archivos del filtro) | — | carpeta completa |
| `backups_20260821_20260821_092634` | Sin documentación (0 archivos del filtro) | — | carpeta completa |
| `backups_fix_proveedor_20260821_102851` | Sin documentación (0 archivos del filtro) | — | carpeta completa |
| `backups_provider_total_20260821_094139` | Sin documentación (0 archivos del filtro) | — | carpeta completa |
| `config` | Sin documentación (0 archivos del filtro) | — | carpeta completa |
| `postgresql.conf` | Sin documentación (0 archivos del filtro) | — | carpeta completa |

## 3. Carpetas espejo íntegras (D7 — se archivan en `.tar.gz`, no se versionan)

| Carpeta | Contenido | Estado |
|---|---|---|
| `_archive_pre_cleanup_20261003` | copia completa de módulos/`madenat_lumber_docs` (32 archivos) | Espejo → `/home/viruco/dev-stack/backups/_archive_pre_cleanup_20261003.tar.gz` (C1) |
| `f31_test_20261003_1410` | copia completa de módulos/`madenat_lumber_docs` (570 archivos) | Espejo → `/home/viruco/dev-stack/backups/f31_test_20261003_1410.tar.gz` (C1) |
| `madenat_dev_p0r_20261003` | copia completa de módulos/`madenat_lumber_docs` (570 archivos) | Espejo → `/home/viruco/dev-stack/backups/madenat_dev_p0r_20261003.tar.gz` (C1) |
| `oracle_f31_20261003_165538` | copia completa de módulos/`madenat_lumber_docs` (570 archivos) | Espejo → `/home/viruco/dev-stack/backups/oracle_f31_20261003_165538.tar.gz` (C1) |
| `pre02_isolated_20261003` | copia completa de módulos/`madenat_lumber_docs` (546 archivos) | Espejo → `/home/viruco/dev-stack/backups/pre02_isolated_20261003.tar.gz` (C1) |
| `pre02_postcommit_test_20261003_173746` | copia completa de módulos/`madenat_lumber_docs` (569 archivos) | Espejo → `/home/viruco/dev-stack/backups/pre02_postcommit_test_20261003_173746.tar.gz` (C1) |
| `pre02_test_20261003_1541` | copia completa de módulos/`madenat_lumber_docs` (570 archivos) | Espejo → `/home/viruco/dev-stack/backups/pre02_test_20261003_1541.tar.gz` (C1) |

## 4. Punteros a artefactos fuera de git (FASE 4, punto 7)

Las **26 citas** de E8 que conservan un artefacto **no versionado** ya dicen en prosa la carpeta de origen; esta
sección añade el `.tar.gz` de D7 que lo contiene, para que el artefacto siga siendo localizable aunque el
original de la raíz esté en cuarentena. Ruta completa del respaldo (unidad `G:`, requiere el disco montado):
`/mnt/g/madenat_respaldos/consolidacion_20261026/<CARPETA>.tar.gz`.

Verificado con `tar -tzf` (rutas y bytes dentro del archivo): **16 artefactos distintos en 26 citas, 16/16
presentes**. Correspondencia cita por cita en `FASES/00_PUNTEROS_ARTEFACTOS_F4.csv`.

| Carpeta de fase | Artefacto dentro del `.tar.gz` | `.tar.gz` de D7 | Citas |
|---|---|---|---|
| `APPLY_AB_UI_20261008/` | `logs/tests_directed_madenat_test_20261008_093825.log` | `APPLY_AB_UI_20261008.tar.gz` | 3 |
| `APPLY_AB_UI_20261008/` | `logs/update_modules_20261008_093223.log` | `APPLY_AB_UI_20261008.tar.gz` | 2 |
| `APPLY_BUSQUEDA_INTAKE_20261007/` | `backup/madenat_test_pre.dump` | `APPLY_BUSQUEDA_INTAKE_20261007.tar.gz` | 2 |
| `AUDIT_REBAJA_ETIQUETAS_20261011/` | `evidence/concurrency_probe.py` | `AUDIT_REBAJA_ETIQUETAS_20261011.tar.gz` | 2 |
| `BACKUP_AB_APPLY_20261008/` | `db/madenat_test_20261008_092958.dump` | `BACKUP_AB_APPLY_20261008.tar.gz` | 4 |
| `BLINDAJE_REBAJA_LOCAL_20261012/` | `logs/regression.log` | `BLINDAJE_REBAJA_LOCAL_20261012.tar.gz` | 3 |
| `BLINDAJE_REBAJA_LOCAL_20261012/` | `logs/regression_logistics.log` | `BLINDAJE_REBAJA_LOCAL_20261012.tar.gz` | 1 |
| `CIERRE_PENDIENTES_20261010/` | `db/madenat_test_pre_20261010.dump` | `CIERRE_PENDIENTES_20261010.tar.gz` | 1 |
| `CIERRE_PENDIENTES_20261010/` | `logs/tests_intake_20261010.log` | `CIERRE_PENDIENTES_20261010.tar.gz` | 1 |
| `CONTRATO_APLICACION_20261011/` | `evidence/POL_contrato_tests_draft.py` | `CONTRATO_APLICACION_20261011.tar.gz` | 1 |
| `CONTRATO_APLICACION_20261011/` | `logs_pol.log` | `CONTRATO_APLICACION_20261011.tar.gz` | 1 |
| `IMPL_SERVICE_RETURN_20261006/` | `logs/iso_run4.log` | `IMPL_SERVICE_RETURN_20261006.tar.gz` | 1 |
| `IMPL_SERVICE_RETURN_AB_20261007/` | `logs/gate_run2.log` | `IMPL_SERVICE_RETURN_AB_20261007.tar.gz` | 1 |
| `SIMPLE_REBAJA_20261011/` | `logs/regression.log` | `SIMPLE_REBAJA_20261011.tar.gz` | 1 |
| `UI_SAVE_REBAJA_20261011/` | `logs/regression.log` | `UI_SAVE_REBAJA_20261011.tar.gz` | 1 |
| `oracle_f31_audit/` | `20261003_165538/oracle_f31.py` | `oracle_f31_audit.tar.gz` | 1 |

**Carpetas afectadas por estas citas:** 12 de las 94 (`APPLY_AB_UI_20261008`, `APPLY_BUSQUEDA_INTAKE_20261007`,
`AUDIT_REBAJA_ETIQUETAS_20261011`, `BACKUP_AB_APPLY_20261008`, `BLINDAJE_REBAJA_LOCAL_20261012`,
`CIERRE_PENDIENTES_20261010`, `CONTRATO_APLICACION_20261011`, `IMPL_SERVICE_RETURN_20261006`,
`IMPL_SERVICE_RETURN_AB_20261007`, `SIMPLE_REBAJA_20261011`, `UI_SAVE_REBAJA_20261011`, `oracle_f31_audit`).
Todas están en la Tanda B y todas tienen su `.tar.gz` verificado en D7.

> **Nota para el verificador.** Los nombres de la columna «Artefacto» son **rutas internas del `.tar.gz`**, no
> rutas del árbol de trabajo: por eso `check_paths` las cuenta como «no encontradas» (16 apariciones en esta
> tabla). No son enlaces y no deben resolverse en disco; la comprobación correcta es `tar -tzf`, que sí se hizo
> (16/16).

