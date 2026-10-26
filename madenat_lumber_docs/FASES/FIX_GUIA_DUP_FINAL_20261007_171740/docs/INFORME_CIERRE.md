# Informe — Cierre final de avisos y compatibilidad

**MADENAT — Odoo 18 CE** · 2026-10-07 · **Entrega AISLADA. NO desplegada.**
Base: `FIX_GUIA_DUP_CIERRE_20261007_170340/` (parche incremental previo). Sin reimplementación.

## Qué se cerró

1. **Aviso en Recepción** — `reception_workflow.LumberReceptionWorkflow._check_duplicate_and_warn`
   publica el aviso no bloqueante de homónimo en el chatter de la recepción (mecanismo existente,
   `mail.thread`), simétrico al de Procesado. Ambos sentidos verificados.
2. **Avisos sin repetición** — el aviso se emite **solo cuando la identidad cambia** en la
   operación (guía: cambio de `name`/`partner`; recepción: número ≠ almacenado). Sin campos
   nuevos ni deduplicación por texto traducido.
3. **Compatibilidad de C1** — inventario y verificación de contratos (`docs/LLAMADORES_C1.md`);
   intención **explícita** (`cross_model`, `exclude_model`, `raise_on_match`) en los llamadores.
4. **Plan exacto de aplicación** — `docs/PLAN_APLICACION_REVERSION.md`.

Cambios de código (todo en `madenat_lumber_core`): `mixin_lumber_ingest.py` (+`_warn_guide_homonym`),
`madenat_guia_processing.py` (gate de cambio; retira el aviso local duplicado),
`reception_workflow.py` (helper + args explícitos), `tests/test_guide_duplicate_warnings.py` (nuevo).

## Respaldos documentales

- Aviso no bloqueante (chatter) → `CANON/04 AD-88` (patrón «advertir») y `CANON/12 §5.2`/`§6.2`.
- Identidad `name`+`partner`; número no global → `CANON/12 §2`, `§5.2`.
- Captura incompleta → `CANON/00 §4.3`, `CANON/12 §11.5`.
- Filtro de origen por relaciones → `CANON/12 §5.1`. Sin cambios de CANON.

## CIERRE (respuestas directas)

1. **Aviso en ambos sentidos:** ✔. Guía→Recepción (`w1`, etiqueta «Recepción directa») y
   Recepción→guía (`w2`, etiqueta «Guía Procesada»). En ninguno bloquea por número, informa al
   usuario y no crea cabeceras adicionales.
2. **Repetición de avisos:** ✔ evitada. Criterio: **identidad sin cambios ⇒ sin nuevo aviso**
   (guía: `name`+`partner`; recepción: número ≠ almacenado). Sin campos nuevos ni clave por
   texto traducido. Atomicidad verificada (`w8`).
3. **Llamadores revisados:** 6 (1 de producción en el árbol activo + los del parche + tests).
   Contratos preservados; único cambio de comportamiento = simetría cross-model (buscada) y
   ahora **explícita**. Ver `LLAMADORES_C1.md`.
4. **Pruebas y alcance:** `0 failed, 0 error(s) of 48`; negativo `2 failed, 4 errors/10`.
   Acredita **cabecera y staging**; **no** acredita lotes/movimientos ni concurrencia.
5. **Límites pendientes:** concurrencia (propuesta separada), unicidad con identidad
   incompleta (`partner_id` nulo), aviso no probado en navegador, dedup del aviso de Recepción
   dependiente del número almacenado (caso menor documentado).
6. **Archivos y módulos a aplicar:** sólo **`madenat_lumber_core`** (5 archivos: 4 de código/tests
   + `tests/__init__.py`). No hay cambios en otros módulos; los dependientes (`madenat_lumber_intake`,
   `madenat_lumber_logistics`, `madenat_lumber_costing`, `madenat_toll_processing`) se recargan
   de forma transitiva con `-u madenat_lumber_core`.

## Solicitud de aprobación

> **¿Autorizas aplicar el cierre** (aviso no bloqueante en Recepción + prevención de repetición
> + compatibilidad de C1) **sobre el entorno activo**, mediante:
> (a) aplicación del diff **consolidado** en `custom_addons/madenat_lumber_core/` (4 archivos de
> código + `tests/`, sin cambios de esquema/ACL);
> (b) `-u madenat_lumber_core` en la base **`madenat_test`** en ventana controlada;
> (c) reinicio de `odoo18_app`;
> con respaldo previo de **código con cambios locales, base y filestore**, y con la suite de
> validación posterior (`0 failed`) — **sin** desplegar aún a producción?

**Detalles exactos en `PLAN_APLICACION_REVERSION.md`.** Este documento **no** autoriza el despliegue.
