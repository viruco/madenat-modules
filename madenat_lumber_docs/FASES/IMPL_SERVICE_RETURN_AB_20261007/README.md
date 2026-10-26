# IMPL_SERVICE_RETURN_AB_20261007 — Retorno de servicio (identificación no bloqueante) + imputación posterior

Entrega de los alcances **A** y **B** aprobados el **2026-10-07** (AD-102).

> ## Estado 2026-10-08 — **APLICADO EN EL DESARROLLO EXISTENTE (`madenat_test` / 8069)**
>
> El artefacto `patch/AB_completo.diff` se aplicó **una sola vez** sobre `custom_addons` (15 archivos
> byte a byte = workcopy) y se actualizaron de forma controlada `madenat_lumber_core`,
> `madenat_lumber_intake` y `madenat_lumber_logistics` **solo** en `madenat_test`
> (`0 ERROR / 0 CRITICAL`). Se **reorganizó la UI de Ingreso de Madera** (resumen en 2 columnas,
> «Aplicar cambios» debajo, línea de retorno a todo el ancho, Evidencia documental en 3 columnas con
> encabezado único, packing list a todo el ancho). Pruebas dirigidas **88/88** en verde **sobre
> `madenat_test`** (incl. Cristhian uid 8, `su=False`). El **aislamiento temporal A/B se retiró**
> (`srvretab_web` :8070, volumen `srvretab_web_data`, bases `srvretab_*_20261007`, `/tmp/gate`,
> `/tmp/ab_dryrun`, `/tmp/iso_*`; dumps de las bases en `APPLY_AB_UI_20261008/retired/db/`).
> **V3 (navegador) SIGUE PENDIENTE** — guion actualizado a `http://localhost:8069` / `madenat_test` en
> `docs/GUION_VERIFICACION_NAVEGADOR.md`. Detalle: `docs/PLAN_APLICACION_REVERSION.md` y
> `CANON/02_CONTINUIDAD.md` §17.13 / `CANON/03_TESTS.md` §12.6.
>
> El contenido siguiente describe el **estado previo** (entrega aislada, 2026-10-07) y se conserva como
> historia; leerlo junto con el bloque anterior.

## Contenido

```
IMPL_SERVICE_RETURN_AB_20261007/
├── addons/                     Workcopy (montado :ro en las pruebas). Base = activo + A/B.
├── patch/
│   ├── A_identificacion_no_bloqueante.diff   Alcance A
│   ├── B_imputacion_posterior.diff           Alcance B (depende de A)
│   └── AB_completo.diff                       Ambos (autoritativo)
├── logs/
│   ├── iso_run1.log            Dirigida: 0 failed, 0 errors of 85 tests
│   ├── iso_full_run1.log       Completa 3 suites: 1020 tests (9 fallas PREEXISTENTES)
│   └── base_targeted.log       Baseline (activo SIN cambio): mismas 9 fallas ⇒ preexistentes
├── run_iso.sh / run_iso_full.sh / run_base_targeted.sh
├── docs/
│   ├── DICTAMEN_ALCANCE_AB.md          Qué se reutilizó, módulos, decisión «módulo nuevo»
│   ├── RESULTADOS_PRUEBAS.md           Pruebas, resultados y límites
│   └── PLAN_APLICACION_REVERSION.md    Aplicación, reversión, aceptación
└── README.md
```

## Qué cambia

**Alcance A — identificación de retorno de servicio (no bloqueante).**
- Campo `service_return_confirmation` (Selection `yes`/`no`, **sin default**) en
  `madenat.guia.processing`. *Vacío* = pendiente de identificación (≠ `no`).
- **No** bloquea la ingesta ni el envío a stock. Se **elimina** el guard bloqueante del
  antecedente `IMPL_SERVICE_RETURN_20261006/`.
- Editable desde la Consola de Intake por **proxy no almacenado** (compute + inverse) con el
  usuario operativo; radio inline en Consola, fachada y formulario core; 3 filtros de búsqueda.
- Con imputaciones SV **`applied`**, cambiar a «No» o vaciar se **rechaza** (regla en
  `madenat_lumber_logistics`); la corrección exige **reversar** primero.

**Alcance B — imputación posterior (reutiliza I2).**
- `action_apply` exige que la guía destino esté marcada «Sí» (al **aplicar**, no al guardar
  borrador). No marca la guía automáticamente.
- Relación inversa de **solo lectura** `sv_imputation_ids` + filtro **«Retornos sin imputación
  aplicada»** (no evalúa cobertura parcial).
- **I2 intacto:** sin movimientos de stock, sin ledger `imputacion` (I3), sin costes (I5).

## Módulos afectados (sin módulo nuevo)

`madenat_lumber_core`, `madenat_lumber_intake`, `madenat_lumber_logistics` (dependencia
**core ← logistics**; **sin** dependencia core→logistics ni circular).

## Resultado

- **85/85** pruebas dirigidas en verde (0 failed, 0 errors) — primera corrida.
- **1020** pruebas (3 suites completas); las **9 fallas** son **preexistentes** (idénticas con el
  código activo sin el cambio).

## Gate previo (2026-10-07) — sobre copia del árbol ACTIVO (con cambios locales)

- Copia `/tmp/gate` = **árbol activo con sus cambios locales** + `A` + `B`; **byte a byte** igual al
  workcopy (`45/45`). Los diffs **no** tocan la documentación.
- **Pruebas dirigidas repetidas sobre esa copia:** `0 failed, 0 error(s) of 88 tests`
  (`logs/gate_run2.log`), incluida la prueba con el **usuario real Cristhian** (`su=False`, grupos
  intactos).
- **Navegador (V3): PENDIENTE** — servidor aislado `http://127.0.0.1:8070` (base
  `srvretab_gate_20261007`); guion en `docs/GUION_VERIFICACION_NAVEGADOR.md`. **NO ejecutada**.

Ver `docs/RESULTADOS_PRUEBAS.md`. **NO aplicado** al entorno activo; queda por acreditar el navegador.
