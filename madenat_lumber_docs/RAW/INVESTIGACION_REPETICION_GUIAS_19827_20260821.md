# Investigación — Repetición de Guías “19827” en Navegación

## Resumen ejecutivo
El folio `19827` aparece una sola vez en la base **restaurada** (id=543, partner 676, state=verified, service, `MC - 2506 - 01`, `oc_match_status='not_found'`, create_date 2026-08-21 20:14:24, create_uid=2). Sin embargo, el histórico auditado en sesiones previas mostró 3 cabeceras con folio 19827 (guías 475/479/483) creadas por Intake el 2026-08-20 16:48/17:33/18:09, **todas con `partner_id` nulo**, y una con partner 664 (contaminación). La repetición visual se explica por: (a) folio documental externo `name` usado como única identidad visible (`display_name` = `name`), sin discriminar por proveedor/fecha/ID; y (b) múltiples registros con el mismo folio **permitidos por la constraint `UNIQUE(name, partner_id)` porque `partner_id` NULL no viola UNIQUE** (NULLs distintos). Es un **problema mixto**: hubo múltiples registros del mismo folio y la interfaz no los distingue.

## Alcance y restricciones
Solo lectura; no se modificaron datos, código, XML, tests ni contenedores. Todas las consultas ejecutadas son SELECT.

## Evidencia visual
Selector superior de guía Procesados mostró `19827` repetido. La guía visible (483 en auditoría previa; 543 en base restaurada) corresponde a `madenat.guia.processing`.

## Inventario de registros con folio 19827

| ID | Nombre | Proveedor | Fecha emisión | Tipo | Estado | Ubicación | OC vinculada | Estado OC | Creado por | Fecha creación |
|---:|---|---|---|---|---|---|---|---|---|---|
| 543 | 19827 | 676 (FERRAMENTA SPA) | 2025-10-02 | service | verified | 18 | — | not_found | 2 (Administrator) | 2026-08-21 20:14:24 |
| 475 (hist) | 19827 | NULL | — | procesado | — | — | — | — | 2 | 2026-08-20 16:48:15 |
| 479 (hist) | 19827 | NULL | — | procesado | — | — | — | — | 2 | 2026-08-20 17:33:24 |
| 483 (hist) | 19827 | NULL→664 | — | procesado | verified | — | — | not_found | 2 | 2026-08-20 18:09:13 |

(475/479/483 del historial de `madenat_audit_log`; no existen en la BD restaurada por dump post-limpieza)

## Patrón global de folios repetidos

```sql
-- SELECT aplicado en base restaurada
-- name, total_registros, primera, ultima
-- (0 filas) en madenat_test actual
```

En la base actual: **0 folios repetidos** (BD restaurada con dump). En el historial auditado persistieron 3 cabeceras `19827` el mismo día y por el mismo usuario (Intake, L475/479/483). Múltiples folios quedaron protegidos por la col «próximo folio» del diagnóstico, pero los registros `19827` quedaron repetidos por partner NULL.

## Adjuntos y huella documental
Consulta SELECT sobre `ir_attachment` (res_model='madenat.guia.processing') en BD restaurada: para id=543 no se listaron adjuntos relevantes en la consulta (la guía restaurada no tiene `pdf_attachment_id`/`excel_attachment_id` persistidos verificables; la auditoría previa vinculaba `FACTURAC...` en `madenat_audit_log`). Histórico: los 3 registros `19827` compartían nombre de Excel `FACTURAC...` según `madenat_audit_log` (intake:66/75/84), sugiriendo **carga repetida del mismo documento** con `partner_id` NULL.

Matriz:

| Guía ID | Archivo | Tipo | Checksum | Igual a otra | Conclusión |
|---:|---|---|---|---|---|
| 475 | FACTURAC... (hist) | Excel | n/d | sí | duplicado probable |
| 479 | FACTURAC... (hist) | Excel | n/d | sí | duplicado probable |
| 483 | FACTURAC... (hist) | Excel | n/d | sí | duplicado probable |

## Líneas, lotes, stock y OC

| Guía ID | Líneas | Lotes/tarjas | Picking | Movimientos | OC | Estado operativo | Riesgo |
|---:|---:|---:|---|---:|---|---|---|
| 543 | 0 verificables en BD | 0 | 0 | 0 | — | verified (sin stock) | bajo |
| 475/479/483 (hist) | según registro | 0 | 0 | 0 | — | — | alto si se llegan a procesar |

Sin lotes/picking/movimientos vinculados. Riesgo operativo **latente**: si dos de estas cabeceras llegaran a procesarse/validarse, generarían picking y stock por duplicado.

## Rutas de creación e idempotencia
Callers de `create` sobre `madenat.guia.processing`:
| Caller | Archivo:línea | Disparador | Puede reintentar | Control anti-duplicado | Riesgo |
|---|---|---|---|---|---|
| Intake Wizard | `intake_wizard.py:311` | acción manual de consola | sí (botón) | none local; constraint UNIQUE(name, partner_id) con NULL bypass | media-alto |
| `action_verify_data` | parsing PDF/Excel | no crea cabecera | — | — | — |

El campo `name` se toma desde el documento (PDF/Excel) y puede repetirse. La constraint `UNIQUE(name, partner_id)` no bloquea los duplicados con `partner_id` NULL (comportamiento SQL: NULLs no colisionan). No existe token de idempotencia documental (checksum) ni `ingestion_source_ref` vinculante en creación.

## Identidad y display_name en Odoo
- `_rec_name`: **no definido** en `madenat.guia.processing` → Odoo usa `name`.
- `name = fields.Char(string='Número de Guía', ..., required=True, index=True, tracking=True)` (línea 618).
- No hay overrides de `name_get`/`_compute_display_name`/`name_search` en el modelo.
- `display_name` = `name` → el selector superior muestra solo `19827`; no discrimina proveedor/fecha/ID.
- No se modifica ninguna referencia de negocio si se ajusta solo la etiqueta visible de presentación.

## Controles actuales de deduplicación
| Control | ¿Existe? | Evidencia |
|---|---|---|
| `_sql_constraints` | ✔ | `unique_guia_processing_name_per_partner` (UNIQUE(name, partner_id)) — L587-588; presente en pg_constraint |
| `@api.constrains` | ✖ | no localizado |
| create override con deduplicación | ✖ | no localizado |
| checksum de documento | ✖ | no localizado para guías |
| `ingestion_source_ref` vinculante | ✖ | solo en PO/purchasing |

Clave: `UNIQUE(name, partner_id)` es insuficiente para bloquear folios repetidos cuando `partner_id` es NULL (case de L475/479/483). Una constraint simple `UNIQUE(name)` no debe proponerse sin validar casos legítimos (mismo folio en otro proveedor u otro canal).

## Alternativas de mejora
| Alternativa | Resuelve UX | Evita duplicados reales | Impacto técnico | Riesgo de regresión | Recomendación |
|---|---:|---:|---|---|---|
| A — display_name enriquecido (proveedor · fecha · ID) | ✔ | ✖ | bajo | bajo | ✔ (primera) |
| B — nombre técnico interno con secuencia (GP/2025/000543) | ✔ | ✔ | alto (integración) | alto | ✖ hoy |
| C — campo visible separado usado como display_name | ✔ | parcial | medio | medio | opcional |
| D — deduplicación por (folio, proveedor, fecha, checksum) | ✖ | ✔ | medio | medio-moderado | ✔ (después de validación) |

## Matriz de riesgos
| Hallazgo | Severidad | Evidencia | Impacto operativo | Impacto financiero | Impacto stock | Impacto UX | Acción recomendada |
|---|---|---|---|---|---|---|---|
| 3 folios 19827 históricos con partner NULL permitidos por UNIQUE(name, partner_id) | Alta | historial audit_log + constraint NULL bypass | operar registro incorrecto | — | duplicado potencial | alta ambigüedad | remediación + deduplicación por clave compuesta |
| display_name = folio sin discriminador | Media | `_rec_name` ausente; `name` folio | abre guía equivocada | — | — | alta | display_name enriquecido |

## Veredicto
**Opción 3 — Problema mixto**: hubo registros con el mismo folio (3 en historial; 1 en BD actual) y la interfaz no los distingue (`display_name` = solo folio).

## Próximos pasos propuestos
1. (Correctiva/UX) Enriquecer `display_name`/etiqueta de navegación con proveedor · fecha · tipo · ID **(sin tocar `name`)**, resolución de ambigüedad visual.
2. (Preventiva futura) Evaluar clave compuesta de deduplicación (folio + proveedor + fecha + checksum de adjunto) en wizard Intake, con fallback de advertencia.
3. Revisar `intake_wizard.py:311` para incorporar `partner_id` y token documental antes del `create`, y para advertir si el folio ya existe (sin bloquear casos legítimos).
4. Documentar criterio de negocio sobre si el folio es único global o por proveedor, antes de agregar cualquier UNIQUE(name).

## Anexo — consultas SELECT ejecutadas
- `SELECT ... FROM madenat_guia_processing WHERE name='19827' ...` → 1 fila (id 543).
- `SELECT name, COUNT(*) ... GROUP BY name HAVING COUNT(*)>1` → 0 filas (BD restaurada).
- `SELECT conname, pg_get_constraintdef ... WHERE conrelid='madenat_guia_processing'::regclass` → UNIQUE(name, partner_id) y FKs.
- `grep` de `_rec_name`/`name_get` → ausentes en core; `_rec_name='guide_name'` solo en intake_console.