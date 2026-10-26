# BASELINE — Auditoría de búsqueda, filtros y agrupaciones de Intake

**Proyecto:** MADENAT Lumber — Odoo 18 CE
**Fecha de la auditoría:** 2026-10-07
**Tipo:** Investigación de SOLO LECTURA (código + base activa). Sin escrituras, sin update de módulos, sin reinicio de servicios.
**Alcance:** Vista/acción "Ingreso de Madera" → `madenat.lumber.intake.console` (list/search) y los campos OC, Fecha, Producto, Procesador y Volúmenes.

---

## 1. Raíz, rama y HEAD

| Dato | Valor |
|---|---|
| Raíz Git | `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons` (el `.git` vive **dentro** de `custom_addons`; la raíz del workspace **no** es un repo) |
| Rama | `feat/guia-correccion-documental-preservada-20261002` |
| HEAD | `e302c488321c276af7e07f1abeecc8bc261a89f4` |
| Últimos commits | `e302c48 fix(core): desacopla vista core de contacts`, `c799bc2 feat(logistics): agrega backlog documental AD-100`, `357e8b3 feat(logistics): agrega entrega segura D2` |

> No se ejecutó commit, push ni cambio de rama. El árbol se inspeccionó tal cual.

## 2. Estado global y cambios preexistentes (NO modificados por esta auditoría)

`git status --porcelain` → **55 entradas**: 46 modificados (` M`) + 9 no rastreados (`??`). Son intervenciones de sesiones anteriores (guía duplicada 15183, costeo C2, lifecycle de guías, ACL, logistics). **No se alteraron.**

Archivos modificados relevantes al alcance de esta auditoría (ya estaban así antes de empezar):

- `madenat_lumber_core/models/madenat_guia_processing.py` (M)
- `madenat_lumber_core/models/lumber_reception.py` (M)
- `madenat_lumber_intake/views/intake_menus.xml` (M)
- `madenat_lumber_intake/models/intake_guide_lifecycle_wizard.py` (M)

## 3. Hashes de archivos pertinentes (MD5 de la copia de trabajo activa)

| Archivo | MD5 |
|---|---|
| `madenat_lumber_intake/views/intake_console_views.xml` | `b7440974471207b0d53988b279de6d70` |
| `madenat_lumber_intake/models/intake_console.py` | `ac1b0dac978709453e06c9570a803dfa` |
| `madenat_lumber_intake/models/intake_constants.py` | `a2778cdfc74f2b2da80a9417ad8e64d2` |
| `madenat_lumber_intake/views/intake_menus.xml` | `a619d9de58c39f63ddc9cf1e572161e1` |
| `madenat_lumber_core/models/lumber_reception.py` | `9d3d20d3d1648f175a39d9266b9cd8c8` |
| `madenat_lumber_core/models/madenat_guia_processing.py` | `7b3d0a9a82f94cabf16532e905438dcb` |
| `madenat_toll_processing/models/guia_processing_integration.py` | `ae1d79ccc45ccd12a0ef77b9fa0026f0` |

## 4. Base y servicio inspeccionados

| Elemento | Valor |
|---|---|
| Contenedor app | `odoo18_app` (imagen `odoo-18-ce-web`, Up) |
| Contenedor DB | `odoo18_db` (imagen `postgres:15`, healthy) |
| Base activa | **`madenat_test`** (confirmada; **no** `madenattest`) |
| Módulo consola | `madenat_lumber_intake` → `state=installed`, `latest_version=18.0.0.11.0` (== `__manifest__.py`) |
| Vista SQL | `madenat_lumber_intake_console` existe, 11 columnas, 18 filas |
| Acceso usado para inspección | sentencias `SELECT` de solo lectura (psql) + lectura de código fuente |

Todos los recuentos de este informe salen de `SELECT` sobre la vista/tablas reales en `madenat_test` el 2026-10-07.

## 5. Documentación consultada (CANON vigente vs propuestas/legado)

**CANON vigente (usado como fuente de verdad):**
- `CANON/12_FLUJOS_INGESTA.md` v1.7.0 — discriminación Producto/Procesados, volumen oficial §11.5, SV §11.8.
- `CANON/13_CONSOLIDACION_OPERATIVA.md` — flujos consolidados, OC en Producto (AD-52/AD-54), modos de ciclo de vida (AD-80).
- `CANON/17_CONSTITUCION_VOLUMENES.md` v1.2.0 — definición NOMINAL/DISPONIBLE/EXPORTACIÓN/OFICIAL y reglas por proceso.
- `CANON/19_IMPUTACION_SV_Y_PROCESADORES.md` v1.6.2 — rol **Procesador** (`res.partner.is_processor`), SV, imputación.
- `CANON/04_DECISION_LOG.md` — AD-50 (fachada/puerta única), AD-51, AD-52, AD-54, AD-65, AD-79, AD-80, AD-87.
- `CANON/15_DIAGNOSTICO_NAVEGACION_ACTUAL.md` — navegación de menús (estado 2026-06-05).
- `WIKI/01_NEGOCIO/actores_y_roles.md`, `WIKI/01_NEGOCIO/tipos_madera_clasificacion.md`.
- `madenat_lumber_intake/README.md` — documentación viva del módulo.

**Distinción aplicada:** este informe usa únicamente el CANON vigente y el código de la copia de trabajo. Se **ignoraron** como fuente las carpetas de propuestas/histórico/backup del árbol (`*_audit`, `_archive_*`, `backups*`, `pre02_*`, `oracle_*`, `INCIDENTE_*`, `FIX_*`, `LEGADO/`) salvo para contrastar; los `oc_reference_raw`/estados se verificaron **contra la base activa**, no contra documentos.

---

## 6. Método

1. Código → acción → vista → modelo → SQL (`init()`).
2. Base → arquitectura efectiva (`ir_act_window`, `ir_ui_view.arch_db`, `ir_ui_menu_group_rel`, ACL, `ir_filters`).
3. Datos → recuentos por `ingestion_type`/`state` y por vínculo OC.
4. Doctrina → significado pretendido de cada campo/etiqueta.

Separación explícita de categorías de verificación (usada en `PLAN_PRUEBAS.md`):
- **V1 Estática (XML/código).**
- **V2 ORM/SQL (psql sobre la base activa).**
- **V3 Navegador (UI real).** — *no ejecutada en esta auditoría*.
