# FIX_DELETE_INTAKE_20261007_145130 — Eliminación robusta de ingresos cancelados

Entrega **aislada** de la corrección de atribución para la eliminación (Modo A) de guías
canceladas desde el asistente «Ciclo de vida de la guía» (Intake). **No** se aplica al
árbol activo; **no** se toca `madenat_test`.

## Contenido

```
FIX_DELETE_INTAKE_20261007_145130/
├── addons/                       Workcopy aislado (montado :ro en las pruebas)
│   ├── madenat_lumber_intake/    (wizard + vista + tests nuevos)
│   └── madenat_lumber_core/      (corrección preventiva del retorno)
├── patch/
│   ├── 01_delete_attribution.diff      Atribución por relaciones + revalidación + UI (Fase 1)
│   ├── 02_preventive_return_fk.diff     Corrección preventiva (fuga de contexto) [Fase 1]
│   └── 03_modo_b_selection.diff         Modo B no revierte documentos ajenos [Fase 2]
├── docs/
│   ├── IDENTIDAD_REVISION.md      Qué cambió desde la auditoría; aislamiento; hashes
│   ├── MATRIZ_ELEGIBILIDAD.md     Matriz A–H (permite/bloquea/política/evidencia/mensaje)
│   ├── DICTAMEN_CAMBIO.md         Conflicto doctrinal + propuesta + decisión D-POL-1
│   ├── REPRODUCCION_CADENA_436_7813_7814.md  Atribución material de la cadena [Fase 2]
│   ├── REVISION_DIFF_PREVENTIVO.md  Revisión por ruta de los 3 create + Modo B [Fase 2]
│   ├── D_POL_1_PROPUESTA.md       Cierre de D-POL-1 (Opción B) + respuesta exacta [Fase 2]
│   ├── PROCEDIMIENTO_REPARACION_FK_7813.md  Reparación del FK espurio (NO ejecutar) [Fase 2]
│   ├── RESULTADOS_PRUEBAS.md      Resultados reales + caso 15183 + pendientes
│   └── PLAN_APLICACION_REVERSION.md  Aplicación, reversión, riesgos, aceptación
├── logs/
│   ├── iso_run4.log              ✅ 0 failed, 0 errors of 39 tests (definitivo, Fase 1+2)
│   ├── iso_run3.log              39 tests, 1 fallo de test (corregido)
│   ├── iso_run2.log              ✅ 0 failed, 0 errors of 31 tests (Fase 1)
│   └── iso_run.log               1ª iteración (2 fallos de test, corregidos)
├── run_iso.sh                    Lanzador de la prueba aislada
└── README.md
```

## Resumen (1.–4.)

1. **Qué corregí.** (Fase 1) La atribución de albaranes/movimientos del Modo A: de `origin`
   textual a **relaciones** (FK `guia_processing_id`, lotes propios, evidencia de
   pertenencia a otro documento). Un **documento ajeno** con número coincidente deja de
   bloquear; un **retorno con vínculo directo** (antes invisible) **ahora bloquea** con
   mensaje específico. Se añadió **revalidación inmediata**, un **candado de concurrencia**
   y el campo `attribution_notes`. (Fase 2) El **Modo B** ya **no revierte documentos
   ajenos** (`03_modo_b_selection.diff`); y la **corrección preventiva** del FK del retorno
   (`02`) se revisó ruta por ruta.
2. **Qué pruebas ejecuté.** `run_iso.sh` sobre la base aislada `delint_test_20261007`:
   **39/39 verdes** (20 `TestGuideLifecycle` sin regresión + 11 `TestDeleteAttribution` +
   4 `TestReturnAttribution` + 1 UI `Form` + 3 `TestDeleteConcurrency`). Ver
   `docs/RESULTADOS_PRUEBAS.md`.
3. **¿Puede eliminarse 15183?** La cadena **436→7813→7814 pertenece a la recepción 1369**
   (no a la guía); la guía 33152 **no tiene ninguna dependencia material propia**. El
   **único** bloqueador es el **FK espurio** del retorno 7813. Con D-POL-1 = **Opción B**,
   **sí** es eliminable **tras reparar ese FK** (procedimiento separado, no ejecutado).
4. **Qué falta exactamente.** → **“Para eliminar 15183 falta exactamente** la **reparación
   autorizada del FK espurio de `stock.picking` 7813** (`guia_processing_id = NULL`) y la
   autorización operativa del borrado. **No es una decisión de política abstracta:** la
   atribución ya está comprobada (Opción B).

## Aislamiento

Base **nueva** `delint_test_20261007` (clon que contiene la cadena real 436/7813/7814, solo
**lectura**); código del workcopy `:ro`; contenedor one-shot; sin HTTP/cron/SMTP.
`madenat_test`, el árbol activo, producción, CANON e `IMPL_SERVICE_RETURN` **intactos**.

## Aislamiento

Base **nueva** `delint_test_20261007` (clon); código del workcopy `:ro`; contenedor
one-shot; sin HTTP/cron/SMTP. `madenat_test`, el árbol activo y producción **intactos**.
