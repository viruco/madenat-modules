# P7 — Inventario de Residuos Documentales y de Filesystem

**Proyecto:** MADENAT  
**Fase:** P7 — Catalogación y análisis (SOLO LECTURA)  
**Fecha ejecución:** 2026-06-02 18:43  
**Auditor:** Cline (auditor técnico-documental)  
**Estado:** INVENTARIO COMPLETO  
**Acciones destructivas ejecutadas:** NINGUNA

---

## A. Inventario LEGADO/

| # | Archivo | Tamaño | Fecha | Tipo | Prioridad | Justificación |
|---|---------|--------|-------|------|-----------|---------------|
| 1 | `04_DECISIONLOG.md` | 7.2 KB | 2026-05-28 18:39 | HISTORICO | REVISAR_MANUAL | Versión anterior de CANON/04_DECISION_LOG.md (171 vs 389 líneas). Faltan AD-25 en adelante. Nombre sin underscore. |
| 2 | `INDICE_DOCUMENTACION_OLD.md` | 5.9 KB | 2026-05-28 18:37 | HISTORICO | CANDIDATO_ELIMINACION | Índice antiguo que referencia estructura documental anterior. CANON/INDICE_DOCUMENTACION.md es la fuente vigente. |
| 3 | `RESUMEN_AUDITORIA_OLD.md` | 6.2 KB | 2026-05-12 20:51 | HISTORICO | REVISAR_MANUAL | Resumen de auditoría de mayo 2026. Podría contener contexto histórico no migrado a documentos activos. |

---

## B. Inventario RAW/legacy/

### B.1 Estructura general

```
RAW/legacy/
├── LEGADO/                          # 13 archivos históricos de auditorías y guías
│   ├── HISTORICOS_AUXILIARES/       # 1 archivo duplicado
│   └── HISTORICOS_SNAPSHOTS/        # vacío
├── LEGADO_EXTERNOS/                 # 4 archivos (2 pares duplicados byte a byte)
├── historico_actual/
│   ├── 20260513_210511/             # Snapshot 1: 20 archivos + Errores/
│   │   └── Errores/                 # 7 archivos (réplicas de LEGADO/)
│   └── 20260513_210842/             # Snapshot 2: 20 archivos + Errores/
│       └── Errores/                 # 7 archivos (réplicas de LEGADO/)
```

### B.2 Tabla de clasificación

#### RAW/legacy/LEGADO/ (13 archivos)

| # | Archivo | Tamaño | Tipo | Prioridad | Justificación |
|---|---------|--------|------|-----------|---------------|
| 1 | `AUDITORIA_2026_05_01.md` | 18.0 KB | HISTORICO | REVISAR_MANUAL | Auditoría técnica de código. Información histórica no presente en documentos activos. |
| 2 | `AUDITORIA_2026_05_02.md` | 12.5 KB | HISTORICO | REVISAR_MANUAL | Segunda auditoría. Complementa la anterior. |
| 3 | `DOCUMENTO_UNICO_REFERENCIA.md` | 4.6 KB | HISTORICO | CANDIDATO_ELIMINACION | Documento de referencia antiguo. Sin equivalente activo pero probablemente superado. |
| 4 | `ESTADO_MODULO.md` | 1.1 KB | HISTORICO | CANDIDATO_ELIMINACION | Muy breve (1KB). Estado puntual del módulo, ya obsoleto. |
| 5 | `GUIA_CONTINUIDAD_TECNICA.md` | 11.2 KB | HISTORICO | REVISAR_MANUAL | Guía técnica de continuidad. Podría tener información útil no migrada. |
| 6 | `GUIA_REFACTORIZACION_ESPECIFICA.md` | 34.9 KB | HISTORICO | REVISAR_MANUAL | La más grande. Guía detallada de refactorización. Valor potencial. |
| 7 | `INFORME_AUDITORIA_CODIGO.md` | 14.2 KB | HISTORICO | REVISAR_MANUAL | Informe de auditoría de código. Contexto histórico. |
| 8 | `MADENAT_ECOSYSTEM_MASTER.md` | 27.1 KB | HISTORICO | REVISAR_MANUAL | Documento grande con visión global del ecosistema. |
| 9 | `MANIFEST_ENTREGA.md` | 0.4 KB | HISTORICO | CANDIDATO_ELIMINACION | Muy breve. Manifiesto de entrega de snapshot. |
| 10 | `RESUMEN_AUDITORIA_Y_DOCUMENTACION.md` | 0.4 KB | HISTORICO | CANDIDATO_ELIMINACION | Muy breve. Resumen puntual. |
| 11 | `RESUMEN_EJECUTIVO.md` | 7.6 KB | HISTORICO | REVISAR_MANUAL | Resumen ejecutivo de auditoría. |
| 12 | `RESUMEN_VISUAL_PROBLEMAS.md` | 9.6 KB | HISTORICO | REVISAR_MANUAL | Resumen visual de problemas. |
| 13 | `ROADMAP.md` | 0.5 KB | HISTORICO | CANDIDATO_ELIMINACION | Muy breve. Roadmap puntual ya superado. |

#### RAW/legacy/LEGADO/HISTORICOS_AUXILIARES/ (1 archivo)

| # | Archivo | Tamaño | Tipo | Prioridad | Justificación |
|---|---------|--------|------|-----------|---------------|
| 1 | `AUDITORIA_PROFUNDA_2026_05_07.md` | 11.7 KB | DUPLICADO_EXACTO | CANDIDATO_ELIMINACION | Byte a byte idéntico a los que están en ambos snapshots. Triplicado. |

#### RAW/legacy/LEGADO_EXTERNOS/ (4 archivos)

| # | Archivo | Tamaño | Tipo | Prioridad | Justificación |
|---|---------|--------|------|-----------|---------------|
| 1 | `02_CONTINUIDAD_v2.md` | 6.0 KB | VARIANTE_ACTIVA | REVISAR_MANUAL | Variante v2 de continuidad. Nombre sugiere segunda versión. Diferente de CANON/02_CONTINUIDAD.md. Podría contener ideas o decisiones no migradas. |
| 2 | `02_CONTINUIDAD_v2.md.bak` | 6.0 KB | DUPLICADO_EXACTO | CANDIDATO_ELIMINACION | Byte a byte idéntico al anterior. |
| 3 | `05_BACKLOG_v2.md` | 3.7 KB | VARIANTE_ACTIVA | REVISAR_MANUAL | Variante v2 del backlog. Diferente de CANON/05_BACKLOG.md. Podría contener items no migrados. |
| 4 | `05_BACKLOG_v2.md.bak` | 3.7 KB | DUPLICADO_EXACTO | CANDIDATO_ELIMINACION | Byte a byte idéntico al anterior. |

#### RAW/legacy/historico_actual/20260513_210511/ (20 archivos + Errores/)

| # | Archivo | Tamaño | Tipo | Prioridad | Justificación |
|---|---------|--------|------|-----------|---------------|
| 1 | `00_ARQUITECTURA.md` | 16.5 KB | SNAPSHOT_PUNTUAL | CANDIDATO_ELIMINACION | Versión snapshot de CANON/00_ARQUITECTURA.md. Diferente. Sin valor diferencial confirmado. |
| 2 | `01_FLUJO_PACKING.md` | 5.8 KB | SNAPSHOT_PUNTUAL | CANDIDATO_ELIMINACION | Versión snapshot de CANON/01_FLUJO_PACKING.md. |
| 3 | `02_CONTINUIDAD.md` | 8.1 KB | SNAPSHOT_PUNTUAL | CANDIDATO_ELIMINACION | Versión snapshot de CANON/02_CONTINUIDAD.md. |
| 4 | `03_TESTS.md` | 5.3 KB | SNAPSHOT_PUNTUAL | CANDIDATO_ELIMINACION | Versión snapshot de CANON/03_TESTS.md. |
| 5 | `04_DECISION_LOG.md` | 5.5 KB | SNAPSHOT_PUNTUAL | CANDIDATO_ELIMINACION | Versión snapshot de CANON/04_DECISION_LOG.md. |
| 6 | `05_BACKLOG.md` | 4.7 KB | SNAPSHOT_PUNTUAL | CANDIDATO_ELIMINACION | Versión snapshot de CANON/05_BACKLOG.md. |
| 7 | `06_CHECKLIST.md` | 1.2 KB | SNAPSHOT_PUNTUAL | CANDIDATO_ELIMINACION | Versión snapshot de CANON/06_CHECKLIST.md. |
| 8 | `07_TRABAJO_CON_IA.md` | 7.6 KB | SNAPSHOT_PUNTUAL | CANDIDATO_ELIMINACION | Versión snapshot de CANON/07_TRABAJO_CON_IA.md. |
| 9 | `INDICE_DOCUMENTACION.md` | 8.7 KB | SNAPSHOT_PUNTUAL | CANDIDATO_ELIMINACION | Versión snapshot de CANON/INDICE_DOCUMENTACION.md. |
| 10 | `AUDITORIA_PROFUNDA_2026_05_07.md` | 11.7 KB | DUPLICADO_EXACTO | CANDIDATO_ELIMINACION | Triplicado (LEGADO aux + ambos snapshots). |
| 11 | `CHECKLIST_FINALIZACION.md` | 39.8 KB | HUERFANO | REVISAR_MANUAL | El archivo más grande del snapshot (40KB). Checklist de finalización sin equivalente en CANON. |
| 12 | `ESTADO_MODULO.md` | 4.8 KB | HUERFANO | REVISAR_MANUAL | Estado del módulo diferente del que está en LEGADO/. Posible información única. |
| 13 | `GUIA_PRODUCCION_FINAL.md` | 4.7 KB | HUERFANO | REVISAR_MANUAL | Guía de producción final. No tiene equivalente activo conocido. |
| 14 | `HOJA_RUTA_EJECUTIVA.md` | 7.0 KB | HUERFANO | REVISAR_MANUAL | Hoja de ruta ejecutiva. Sin equivalente en CANON actual. |
| 15 | `INVENTARIO_REAL_20260512_195600.md` | 128.9 KB | DUPLICADO_EXACTO | REVISAR_MANUAL | El archivo más grande (129KB). Byte exacto en ambos snapshots. Inventario detallado de proyecto. Podría tener información no registrada en documentos vigentes. |
| 16 | `MANIFEST_ENTREGA.md` | 4.2 KB | HUERFANO | REVISAR_MANUAL | Manifiesto de entrega detallado (diferente del de LEGADO/). |
| 17 | `QUICK_START.md` | 1.6 KB | HUERFANO | CANDIDATO_ELIMINACION | Quick start antiguo. |
| 18 | `README_HISTORICO.txt` | 0.2 KB | SNAPSHOT_PUNTUAL | CANDIDATO_ELIMINACION | Solo 232 bytes. Nota de snapshot. |
| 19 | `ROADMAP.md` | 3.4 KB | HUERFANO | REVISAR_MANUAL | Roadmap diferente del de LEGADO/. |
| 20 | `INVENTARIO_ORIGINAL.txt` | 7.5 KB | HUERFANO | REVISAR_MANUAL | Inventario original. Diferente del otro inventario. |

#### Errores/ en 20260513_210511 (7 archivos) y 20260513_210842 (7 archivos)

| # | Archivos (presentes en ambos snapshots) | Tipo | Prioridad | Justificación |
|---|------------------------------------------|------|-----------|---------------|
| 1-7 | `AUDITORIA_2026_05_01.md`, `AUDITORIA_2026_05_02.md`, `ESTADO_MODULO.md`, `GUIA_CONTINUIDAD_TECNICA.md`, `GUIA_REFACTORIZACION_ESPECIFICA.md`, `INFORME_AUDITORIA_CODIGO.md`, `RESUMEN_EJECUTIVO.md`, `RESUMEN_VISUAL_PROBLEMAS.md` | DUPLICADO_EXACTO | CANDIDATO_ELIMINACION | Todos son byte a byte idénticos a sus equivalentes en RAW/legacy/LEGADO/. Duplicados triples (LEGADO + Errores/211511 + Errores/210842). |

#### RAW/legacy/historico_actual/20260513_210842/ (20 archivos)

Misma estructura que 210511 pero con diferencias en archivos CANON-like. Los archivos no-CANON tienen hash propio que difiere del snapshot 210511 para la mayoría de casos.

| # | Archivos CANON-like (9) | Tipo | Prioridad | Justificación |
|---|--------------------------|------|-----------|---------------|
| 1-9 | `00` a `07` + `INDICE` | SNAPSHOT_PUNTUAL | CANDIDATO_ELIMINACION | Segunda versión de snapshot del mismo día. Difiere del snapshot 210511 y del CANON actual. |

| # | Archivos no-CANON (11) | Tipo | Prioridad | Justificación |
|---|--------------------------|------|-----------|---------------|
| 1-11 | `AUDITORIA_PROFUNDA`, `CHECKLIST_FINALIZACION`, `ESTADO_MODULO`, `GUIA_PRODUCCION_FINAL`, `HOJA_RUTA_EJECUTIVA`, `INVENTARIO_REAL`, `MANIFEST_ENTREGA`, `QUICK_START`, `RESUMEN_AUDITORIA_Y_DOCUMENTACION`, `ROADMAP`, `INVENTARIO_ORIGINAL` | DUPLICADO_EXACTO o VARIANTE | VER NOTA | Algunos idénticos al snapshot 210511 (AUDITORIA_PROFUNDA, INVENTARIO_REAL). Otros difieren. Ver sección E. |

### B.3 Resumen RAW/legacy/

| Métrica | Valor |
|---------|-------|
| Total archivos | 75 |
| Total tamaño | 1.1 MB |
| Candidatos a eliminación estimados | ~55 archivos (~800 KB) |
| Archivos a revisar manualmente | ~20 archivos (~300 KB) |
| Duplicados exactos detectados | 30+ relaciones (ver sección E) |

---

## C. Inventario docs_nueva/

| Estado | Detalle |
|--------|---------|
| **VACÍO** | Directorio existe pero no contiene archivos. Creado el 2026-05-23. |

---

## D. Inventario Backups de Módulo

| Nombre | Tipo | Tamaño | Contenido | Recomendación |
|--------|------|--------|-----------|---------------|
| `madenat_lumber_core_BACKUP_20260530_2023/` | BACKUP_MODULO | 2.1 MB, 115 archivos | Copia completa del módulo madenat_lumber_core al 2026-05-30 20:23. Incluye modelos, vistas, tests, wizard, `.bak/` interno con 3 snapshots fechados (20260513_195041, 20260513_195527, 20260513_195553), `views.backup/` con 12 archivos de vista antiguos, `views/views.backup/` (anidado). Contiene archivos `.bak` que violan AD-26. | CONSERVAR como backup histórico del módulo. Revisar si los `.bak/` internos y `views.backup/` deben limpiarse según AD-26. **No eliminar sin validación.** |

### D.2 Backups tar.gz en docs/backups/

| Nombre | Tamaño | Tipo | Prioridad | Justificación |
|--------|--------|------|-----------|---------------|
| `docs_backup_20260523_121420.tar.gz` | 37.7 KB | SNAPSHOT_PUNTUAL | CANDIDATO_ELIMINACION | Backup comprimido de docs al 2026-05-23. Probablemente redundante con WIKI_BACKUP. |
| `docs_backup_20260523_130547.tar.gz` | 310.2 KB | SNAPSHOT_PUNTUAL | REVISAR_MANUAL | Backup más grande (310KB). Podría contener documentos no preservados en otros backups. |
| `madenat_docs_20260523_121222.tar.gz` | 37.7 KB | DUPLICADO_EXACTO | CANDIDATO_ELIMINACION | Byte a byte idéntico a docs_backup_20260523_121420.tar.gz (mismo md5). |

### D.3 WIKI_BACKUP_20260530_1832/

| Nombre | Tipo | Tamaño | Prioridad | Justificación |
|--------|------|--------|-----------|---------------|
| `WIKI_BACKUP_20260530_1832/` | SNAPSHOT_PUNTUAL | 288 KB, 46 archivos | REVISAR_MANUAL | Copia de WIKI/ al 2026-05-30 18:32. NO es byte a byte idéntico a WIKI actual (0 de 46 coincidencias exactas). WIKI actual tiene documentos adicionales (gates_validacion.md, servicio_lotes.md, validadores_checklist.md). Varios documentos técnicos difieren. Puede ser útil para comparar evolución de documentos. |

### D.4 tar.gz en raíz del proyecto

| Nombre | Tamaño | Tipo | Prioridad | Justificación |
|--------|--------|------|-----------|---------------|
| `madenat_addons.tar.gz` (custom_addons/) | — | BACKUP_MODULO | REVISAR_MANUAL | Empaquetado de addons. |
| `madenat_patch.tar.gz` | — | BACKUP_MODULO | REVISAR_MANUAL | Parche empaquetado. |
| `madenat_full_sync_2026-06-01.tar.gz` | — | BACKUP_MODULO | REVISAR_MANUAL | Sincronización completa 1-jun. |
| `madenat_full_test_sync.tar.gz` | — | BACKUP_MODULO | REVISAR_MANUAL | Sincronización de test. |
| `madenat_addons_20260602_123038.tar.gz` | — | BACKUP_MODULO | REVISAR_MANUAL | Empaquetado de addons 2-jun. |
| `madenat_addons.tar.gz` (raíz) | — | BACKUP_MODULO | REVISAR_MANUAL | Empaquetado de addons en raíz. |
| `madenat_lumber_logistics.tar.gz` | — | BACKUP_MODULO | REVISAR_MANUAL | Empaquetado de logistics. |

---

## E. Duplicados Exactos Detectados

### E.1 Pares byte a byte en RAW/legacy/

| Grupo | Archivos | MD5 |
|-------|----------|-----|
| D01 | `LEGADO_EXTERNOS/02_CONTINUIDAD_v2.md` = `LEGADO_EXTERNOS/02_CONTINUIDAD_v2.md.bak` | `77908e2dc26c82997f60463e67fede71` |
| D02 | `LEGADO_EXTERNOS/05_BACKLOG_v2.md` = `LEGADO_EXTERNOS/05_BACKLOG_v2.md.bak` | `bd67435191cba1d3657bc758624902d1` |
| D03 | `LEGADO/ESTADO_MODULO.md` = `20260513_210842/ESTADO_MODULO.md` | `3a0313822613cbe8138570f83dafbbad` |
| D04 | `LEGADO/MANIFEST_ENTREGA.md` = `20260513_210842/MANIFEST_ENTREGA.md` | `44079821d480ede4138f09d00245a897` |
| D05 | `LEGADO/RESUMEN_AUDITORIA_Y_DOCUMENTACION.md` = `20260513_210842/RESUMEN_AUDITORIA_Y_DOCUMENTACION.md` | `741acf76bd43617063953b9bccd0a25b` |
| D06 | `LEGADO/AUDITORIA_PROFUNDA` (auxiliar) = `210511/AUDITORIA_PROFUNDA` = `210842/AUDITORIA_PROFUNDA` | `cc5d9f7cf60825d6c1355f5534d9b6ff` |
| D07 | `210511/INVENTARIO_REAL` = `210842/INVENTARIO_REAL` | `024c4433641810ab3de3afa4182829f3` |
| D08 | Todos los archivos de `Errores/` en ambos snapshots = equivalentes en `LEGADO/` | Ver sección B.2 |
| D09 | `backups/docs_backup_20260523_121420.tar.gz` = `backups/madenat_docs_20260523_121222.tar.gz` | Ambos 37,243 bytes |

### E.2 Resumen de duplicados

- Total archivos duplicados (contando cada copia): ~35 archivos
- Espacio ocupado por duplicados: ~450 KB en RAW/legacy/ + 37.7 KB en backups/

---

## F. Política de Retención Propuesta (BORRADOR)

### F.1 Contexto

**AD-26 existe** (CANON/04_DECISION_LOG.md línea 125):
> "Se prohíbe la permanencia de carpetas `.backup` o archivos `.bak` dentro de los módulos de Odoo. Los backups deben residir exclusivamente en `LEGADO/` dentro del repositorio documental."

Sin embargo, **no existe una política formal de retención documental** que defina tiempos, scope o criterios de eliminación. AD-26 solo aborda ubicación de backups de código, no gobernanza documental.

### F.2 Política propuesta: RET-DOC-001

#### Principios
1. **Fuente única de verdad:** CANON/ y WIKI/ son los únicos directorios activos.
2. **Preservación del linaje:** Se conserva al menos una snapshot completa por mes calendario.
3. **Eliminación segura:** Solo se eliminan duplicados byte a byte confirmados y snapshots intermedios sin valor diferencial.
4. **Revisión humana obligatoria:** Toda eliminación requiere aprobación explícita del responsable del proyecto.

#### Reglas de retención

| Tipo de residuo | Acción | Plazo |
|----------------|--------|-------|
| DUPLICADO_EXACTO | Eliminar tras confirmación | Inmediato |
| SNAPSHOT_PUNTUAL (mismo mes, múltiples) | Conservar 1 por mes, eliminar resto | Revisión mensual |
| HISTORICO con equivalente activo | Mover a LEGADO/ y marcar como superado | 6 meses de gracia |
| VARIANTE_ACTIVA | Revisar contenido, migrar lo útil, luego archivar | Sin plazo fijo |
| BACKUP_MODULO | Conservar último y penúltimo; eliminar anteriores | Rotación cada 2 releases |
| HUERFANO sin valor | Eliminar tras revisión | 3 meses |

#### Directorios de respaldo permitidos
- `LEGADO/`: documentos superados con equivalente activo
- `RAW/legacy/`: snapshots históricas de documentación
- `backups/`: archivos comprimidos de respaldo
- **Prohibido:** `.bak`, `.backup`, `_BACKUP_` dentro de módulos Odoo (según AD-26)

#### Propuesta de AD-27 (nueva)
> **AD-27 — Política de Retención Documental**  
> Se adopta RET-DOC-001 como política de retención documental.  
> Se establece revisión trimestral de residuos documentales.  
> Toda eliminación debe registrarse en CANON/04_DECISION_LOG.md.

---

## G. Resumen Ejecutivo

### G.1 Totales inventariados

| Alcance | Archivos | Tamaño |
|---------|----------|--------|
| LEGADO/ | 3 | 19.5 KB |
| RAW/legacy/ | 75 | 1.1 MB |
| docs_nueva/ | 0 | 0 |
| Backups módulo | 1 dir (115 archivos) | 2.1 MB |
| WIKI_BACKUP | 1 dir (46 archivos) | 288 KB |
| Backups tar.gz | 3 | 386 KB |
| .bak activos (violan AD-26) | 6 | 792 KB |
| tar.gz raíz | 7 | pendiente |
| **TOTAL** | **~255 archivos** | **~4.7 MB** |

### G.2 Distribución por tipo

| Tipo | Cantidad estimada | % |
|------|-------------------|---|
| DUPLICADO_EXACTO | ~42 | 16% |
| SNAPSHOT_PUNTUAL | ~28 | 11% |
| HISTORICO | ~23 | 9% |
| HUERFANO | ~14 | 6% |
| VARIANTE_ACTIVA | 4 | 2% |
| BACKUP_MODULO | ~130 | 51% |
| COPIA_ACTIVO | 0 | 0% |
| SIN_REFERENCIA | ~3 | 1% |

### G.3 Candidatos a eliminación

| Categoría | Archivos | Espacio estimado |
|-----------|----------|-----------------|
| Duplicados byte a byte | ~35 | ~490 KB |
| Snapshots puntuales redundantes | ~20 | ~400 KB |
| .bak en módulos activos (violan AD-26) | 6 | ~730 KB |
| Backup tar.gz duplicado | 1 | 37.7 KB |
| **TOTAL candidatos** | **~62** | **~1.7 MB** |

### G.4 Riesgo de pérdida si se eliminan candidatos

| Nivel de riesgo | Descripción |
|-----------------|-------------|
| **BAJO** | Duplicados exactos y snapshots con equivalente en CANON: riesgo nulo, son redundantes. |
| **MEDIO** | HUERFANOS como CHECKLIST_FINALIZACION (40KB) o INVENTARIO_REAL (129KB): podrían contener información no migrada. Requieren revisión manual antes de eliminar. |
| **ALTO** | BACKUP_MODULO de madenat_lumber_core: contiene código fuente histórico completo de un punto en el tiempo. No debe eliminarse sin backup externalizado. |

---

## H. Veredicto

**INVENTARIO COMPLETO**

Se han catalogado todos los residuos documentales y de filesystem del proyecto MADENAT:
- LEGADO/ (3 archivos)
- RAW/legacy/ (75 archivos en estructura de snapshots)
- docs_nueva/ (vacío)
- Backups de módulo (1 directorio + 3 tar.gz + WIKI_BACKUP)
- Backups raíz (7 tar.gz)
- Archivos .bak en módulos activos (6 archivos que violan AD-26)

**Hallazgos notables:**
1. AD-26 existe pero se está violando: hay 6 archivos `.bak` en módulos activos y el backup de módulo contiene `.bak/` internos.
2. La estructura RAW/legacy/ contiene 75 archivos con triplicación significativa (LEGADO + Errores/211511 + Errores/210842).
3. Dos snapshots del mismo día (210511 y 210842) con diferencias entre sí pero ambos obsoletos respecto a CANON.
4. INVENTARIO_REAL_20260512_195600.md (129KB) es el archivo más grande y está duplicado en ambos snapshots — podría contener información valiosa no migrada.
5. No existe política de retención documental formal (más allá de AD-26 para código).

**Acciones inmediatas recomendadas (NO automatizar — revisión manual):**
1. [ ] Mover/eliminar los 6 `.bak` de módulos activos a LEGADO/ (según AD-26)
2. [ ] Revisar INVENTARIO_REAL (129KB) y CHECKLIST_FINALIZACION (40KB) por si contienen información no migrada a CANON/WIKI
3. [ ] Limpiar RAW/legacy/ eliminando duplicados byte a byte (30+ archivos redundantes)
4. [ ] Conservar solo 1 snapshot por mes en RAW/legacy/historico_actual/
5. [ ] Revisar LEGADO_EXTERNOS/02_CONTINUIDAD_v2.md y 05_BACKLOG_v2.md por información diferencial
6. [ ] Aprobar política RET-DOC-001 como AD-27
7. [ ] Limpiar `views.backup/` y `.bak/` internos del backup de módulo

---

*Informe generado el 2026-06-02 18:45 (UTC-4) por auditor P7.*  
*Cero archivos modificados, movidos o eliminados durante esta auditoría.*