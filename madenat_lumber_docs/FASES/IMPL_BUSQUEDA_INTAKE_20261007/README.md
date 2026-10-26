# IMPL_BUSQUEDA_INTAKE_20261007 — Mejora mínima de búsqueda/filtros/agrupación de Intake

Entrega de la mejora mínima de la búsqueda de "Ingreso de Madera"
(`madenat.lumber.intake.console`). Basado en
`AUDIT_BUSQUEDA_FILTROS_INTAKE_20261007` (auditoría previa de solo lectura).

> **Estado:** el artefacto fue **probado en aislamiento** y luego **APLICADO en
> `madenat_test`** (ver `APPLY_BUSQUEDA_INTAKE_20261007/`). **Sin** commit/push y
> **sin** desplegar a producción.

## Contenido

```
IMPL_BUSQUEDA_INTAKE_20261007/
├── addons/                     Workcopy aislado (se monta :ro en las pruebas)
│   └── madenat_lumber_intake/  ÚNICO módulo modificado (model + views + tests)
├── patch/
│   ├── 01_console_model.diff   intake_console.py (campos + SQL init())
│   ├── 02_console_views.diff   intake_console_views.xml (lista/form/búsqueda)
│   └── 03_tests.diff           tests/__init__.py + test nuevo
├── docs/
│   ├── DISENO_CAMBIO.md        Qué se cambió, por categoría (A/B/C/D), y por qué
│   ├── RESULTADOS_PRUEBAS.md   Comandos, resultados (66 tests) y evidencia SQL
│   └── LIMITES.md              Límites, decisiones pendientes y lo NO hecho
├── logs/
│   ├── iso_run.log             Corrida de la clase nueva: 8/8 (0 failed, 0 errors)
│   └── iso_regression.log      Corrida ampliada: 66 tests, 0 failed, 0 errors
├── run_iso.sh                  Lanzador de la prueba aislada
└── README.md
```

## Resumen

- **Solo se modificó `madenat_lumber_intake`** (2 archivos de código + 1 test).
  Los otros 11 módulos del workcopy son **byte-idénticos** al árbol activo.
- **10 pruebas nuevas** (`TestIntakeSearchConsole`) verdes; **66 tests** ejecutados
  en total (10 + 56 de regresión) con **0 failed, 0 errors**.
- Sin cambios en ACL, ingesta, stock, CANON ni datos históricos.

### Ajustes previos a la aplicación (autorizados)
- **Fecha visible en la lista:** se añadió la columna "Origen fecha"
  (`guide_date_kind`, badge) → distingue **Emisión vs Recepción** fila a fila
  (no solo por `help`). Prueba `test_10_lista_muestra_origen_de_fecha`.
- **Modalidad (corrección de descripción):** los filtros **NO son mutuamente
  excluyentes**; se pueden marcar varios y se combinan por **AND** (dos modalidades
  → intersección vacía). Verificado por `test_09_combinacion_modalidad_por_and`.
  Descripción corregida en XML y docs.

## Aislamiento

- Base **nueva dedicada** `busqintake_iso_20261007`, recreada desde una **plantilla
  test idle** (`delint_test_20261007`, 0 conexiones). NO se tocó `madenat_test`.
- Addons del **workcopy** montados en `/mnt/extra-addons:ro`.
- Contenedor **one-shot** (`--rm`), sin HTTP, sin workers, cron deshabilitado.

## Cómo se corre

```bash
cd /home/viruco/dev-stack/odoo/odoo-18-ce/IMPL_BUSQUEDA_INTAKE_20261007
bash run_iso.sh          # actualiza madenat_lumber_intake en la base aislada y corre tests
```

## Estado

- **Implementado y probado en aislamiento.** **NO aplicado.** Pendiente de autorización.
- Ver `docs/LIMITES.md` (incluye el límite de "radio" en filtros y lo diferido).
