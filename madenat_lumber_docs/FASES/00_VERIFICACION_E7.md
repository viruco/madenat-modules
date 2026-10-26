# Verificación global E7 — Consolidación documental FASE 2

**Versión documental:** 1.0.0
**Fecha:** 2026-10-26
**Alcance:** verificación previa al punto de control C1. Todo lo afirmado aquí se midió con los comandos
indicados; los scripts viven fuera del repositorio (`/tmp/check_links.py`, `/tmp/check_paths.py`) y se
describen para poder reproducirlos.

## (a) Enlaces relativos en CANON, WIKI, RAW y FASES

| Comprobación | Resultado |
|---|---|
| Enlaces Markdown (texto → destino) revisados | **3** |
| Enlaces Markdown **rotos** | **2** |
| Rutas en backticks con extensión, revisadas | **2.299** |
| Resueltas dentro de `madenat_lumber_docs/` o `custom_addons/` | 1.725 |
| Resueltas **solo** en la raíz del stack (original aún presente) | 160 |
| No encontradas en ningún sitio | 414 |

**Los 2 enlaces rotos** (`NO CORREGIDOS`, según la regla de detenerse y reportar):

| Archivo | Línea | Destino | Causa |
|---|---|---|---|
| `FASES/DIAGNOSTICO_REBAJA_SV841_REGISTRO_ETIQUETAS_20261015/README.md` | 4 | `evidence` | El filtro de E4 no copia `.py`; los 7 `repro_*.py` siguen solo en la raíz del stack |
| `FASES/DIAGNOSTICO_REBAJA_SV841_REGISTRO_ETIQUETAS_20261015/README.md` | 4 | `logs` | El filtro no copia `.log`; `reproduccion.log` y `baseline.log` siguen solo en la raíz |

**Composición de las 414 rutas no encontradas** (ninguna es una ruta nueva de `FASES/`):

- `logs/*.log` y `db/*.dump`: artefactos deliberadamente fuera de git (histórico de corridas).
- `...`, `logs/step1..5.log`, `.py/.xml/.csv`: elipsis y globs usados como prosa, no como rutas.
- `shipping_core/...`, `madenat_lumber_shipping_core/...`: módulo previo al refactor modular.
- `odoo/modules/loading.py`, `odoo/service/model.py`: rutas del core de Odoo, fuera del repositorio.

**Conclusión (a):** la consolidación **no introdujo** rutas rotas nuevas; las 2 rotas son consecuencia
esperada del filtro de tipos y quedan documentadas para decisión en C1.

## (b) sha256 de todo lo movido contra el manifiesto

| Grupo | Filas | Idénticos | Diferencia esperada | Faltantes |
|---|---|---|---|---|
| `E3` + `D5` (FASE13 y evidencia 2D) | 26 | 22 | 3 (rutas de referencia actualizadas) | 1 |
| `E4` (carpetas de fase) | 568 | 568 | 0 | 0 |
| `E5` (scripts sueltos) | 11 | 11 | 0 | 0 |
| **Total comprobado** | **605** | **601** | **3** | **1** |

- Diferencias esperadas: `FASES/FASE13_20261023/INFORME_FASE_2B.md`, `.../PROMPT_2D.md` y
  `.../evidencias/fase13_md5_vs_csv_compare.py` (E3 exigía actualizar sus rutas).
- Falta esperada: `.../scripts/fase13_md5_vs_csv_compare.py` → **no se copió**: es duplicado byte a byte del
  de `evidencias/` (sha256 `d208f361…` en ambos), y se dejó una sola copia para no tener dos dueños.
- `D5-FUERA-GIT`: el dump `madenat_test_pre_2d_20261026_0956.dump` (11.679.364 B, sha256 `279f466c…`) está en
  `/home/viruco/dev-stack/backups/`, anotado en `FASE13_20261023/evidencias/SHA256_FUERA_DE_GIT.csv`.

## (c) Rutas y nombres antiguos tras la consolidación

| Cadena buscada | Ocurrencias | Naturaleza |
|---|---|---|
| `FASE13_INTAKE_ENGINE_20261023` | 3 | Todas **descriptivas**: la copia del prompt, la nota de riesgo de AD-135 y la tabla §22 de `02_CONTINUIDAD.md`. **0 citas operativas** |
| `05_AUDITORIA_XML_IDS` | 6 | 5 notas de renumeración (04, 02, índice, prompt de fase) + 1 línea histórica del índice (`2026-06-30`). **0 citas operativas** |
| Nombres de las carpetas de fase en `CANON/WIKI/RAW` | 78 pares (33 carpetas distintas) | Citas narrativas del tipo «ver `CARPETA/`». **Resuelven hoy** porque el original sigue en la raíz |

**Riesgo abierto R-E7-1:** si se autoriza borrar los originales de la raíz (C1), esas 78 citas de 33 carpetas
quedarán apuntando a rutas inexistentes. Opciones: (i) no borrar; (ii) reescribirlas a `FASES/<CARPETA>/`
en una etapa E8 autorizada; (iii) dejar el original de las 33 carpetas citadas y borrar solo las otras 45.

## (d) Estado del repositorio

```
$ git status --porcelain            # 11 líneas, todas ajenas a la consolidación
 M madenat_lumber_costing/__manifest__.py
 M madenat_lumber_costing/models/__init__.py
 M madenat_lumber_costing/models/lumber_cost_distribution.py
 M madenat_lumber_costing/models/lumber_shipment_costing.py
 M madenat_lumber_costing/security/ir.model.access.csv
 M madenat_lumber_costing/tests/__init__.py
 M madenat_lumber_costing/views/lumber_cost_distribution_views.xml
 M madenat_lumber_reports/views/lumber_reports_menu.xml
?? madenat_lumber_costing/models/stock_lot_cost_line.py
?? madenat_lumber_costing/tests/test_shipment_costing_c2.py
?? madenat_lumber_costing/views/lumber_shipment_costing_views.xml
```

- Rama `fase13-2a-lectura`, base `1c14206`. Ningún archivo de `madenat_lumber_costing` ni
  `lumber_reports_menu.xml` fue tocado por esta fase.
- Sin `git add -A` en ningún momento: cada commit se armó con `git add` por ruta explícita.
- `git add -f` se usó **solo** para los 4 logs de `FASES/FASE13_20261023/logs/` (`.gitignore:33` = `*.log`),
  por exigencia de D5.

## Commits de la fase

| Etapa | Commit | Contenido |
|---|---|---|
| E0 | `7356ac7` | Manifiesto de línea base (612 filas con sha256) |
| E1 | `96963d4` | Cabeceras 02/03/04/12, fecha del índice, WIKI v2.1.0 |
| E2 | `4337630` | `05_AUDITORIA_XML_IDS` → `20_AUDITORIA_XML_IDS`, huecos reservados |
| E3 | `7d57772` | `FASES/FASE13_20261023/` (27 archivos, 1,1 MB) + 4 referencias |
| E4 | `15d5597`, `9bfafb1`, `688104c`, `2c3d0b9`, `8dd29e7`, `f3c5cd0`, `ba4b94d`, `7309c01`, `cb189d9` | 8 tandas (568 archivos) + índice de fases |
| E5 | `3b5a9af` | 11 scripts en `LEGADO/auditorias/scripts/` + README |
| E6 | `b01e9a1` | Índice RAW, anexo §11, AD-135, §22 de continuidad |
| E7 | (este archivo) | Verificación global |
