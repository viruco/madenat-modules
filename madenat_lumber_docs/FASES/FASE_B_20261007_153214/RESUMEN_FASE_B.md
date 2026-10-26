# FASE B — Aplicación controlada del parche (RESUMEN DE CIERRE)

Caso: guía **15183 / `madenat.guia.processing` ID 33152**. MADENAT — Odoo 18 CE.
Fecha de ejecución: **2026-10-07** (UTC ≈ 18:33–18:40).
Autorización: **únicamente Fase B** (ver `APROBACIONES_Y_ALCANCE.md`).

## Preguntas de cierre y respuestas

1. **¿Parche aplicado?** **SÍ.** 3 diffs con `-p1` en orden 02→03→01 sobre
   `custom_addons` → base `madenat_test`. Hashes resultantes **idénticos** al artefacto
   probado (ver `EVIDENCIA_APLICACION_Y_ACTUALIZACION.md`).
2. **¿FK reparado?** **NO.**
3. **¿Guía eliminada?** **NO.**
4. **¿Se volvió a cancelar?** **NO.**
5. **Cadena 436→7813→7814:** **intacta** (ver `VERIFICACION_CADENA_MATERIAL.md`).
6. **Cambios no previstos:** **ninguno** observado (ver "Control de desviaciones").

## Resultado por criterio de validación

| Criterio | Resultado |
|---|---|
| Hashes resultantes == artefacto probado | ✔ 4/4 idénticos |
| Campo `attribution_notes` registrado | ✔ id 20664, `ttype=text` |
| Vista del asistente cargada | ✔ `…guide.lifecycle.form` (id 2069) usa `attribution_notes` |
| Logs sin errores atribuibles a la intervención | ✔ 0 ERROR/CRITICAL/Traceback desde el reinicio |
| Guía 15183 sigue existente y `cancelled` | ✔ |
| Picking 7813 sigue con `guia_processing_id=33152` | ✔ (no reparado) |
| Diagnóstico bloqueado por 7813 | ✔ (`… vínculo directo (guia_processing_id): EMB-04201`) |
| Picking 436 sin falso bloqueo textual | ✔ (clasificado `foreign`; no cuenta) |
| Cadena 436→7813→7814 sin alteraciones | ✔ |
| Cambios locales preexistentes preservados | ✔ (39 → 45; ninguna línea previa perdida) |

## Control de desviaciones

- No hubo deriva de código (hashes previos == auditados).
- El respaldo se completó y verificó antes de escribir.
- La actualización terminó limpia (0 errores).
- **No** se ejecutaron pruebas mutantes sobre `madenat_test`.
- **No** se pulsó "Eliminar definitivamente".

## Estado Git

- Raíz: `custom_addons`; rama `feat/guia-correccion-documental-preservada-20261002`.
- HEAD (sin cambios): `e302c488321c276af7e07f1abeecc8bc261a89f4`.
- `git status --porcelain`: **antes 39** → **después 45** entradas.
- Líneas previas perdidas: **ninguna**. Nuevas: las 4 modificadas + 2 no rastreadas del fix.
  (`git_status_before.txt` / `git_status_after.txt`.)
- Sin `commit`/`push`/`stash`/`reset`/`checkout`.

## Servicios y cron (estado final)

| Servicio | Estado |
|---|---|
| `odoo18_app` | **Up** (HTTP `/web/login` = 200; sin errores post-reinicio) |
| `odoo18_db` | Up (healthy) |
| cron de la intervención | `--max-cron-threads=0` en el proceso de actualización |
| Otros contenedores Odoo sobre `madenat_test` | ninguno |

## CORRECCIÓN de la afirmación de reversión

La afirmación previa "el parche no altera datos ni esquema persistente ⇒ `git apply -R`
basta" es **incorrecta**. La **actualización de módulos** (`-u`) **sí** puede modificar
metadatos y esquema (p. ej. nuevas `ir.model.fields`, vistas, y potenciales columnas
derivadas). Por tanto la reversión se descompone en **tres niveles distintos**:

1. **Reversión de archivos:** `git apply -R` de 01, 03, 02 (orden inverso). Devuelve el
   código, **pero no** deshace por sí sola lo aplicado en la base por la actualización.
2. **Re-registro de módulos:** volver a ejecutar `-u madenat_lumber_core,madenat_lumber_intake`
   para que el registro refleje el código revertido (puede dejar residuos como el campo
   `attribution_notes` salvo que se trate explícitamente).
3. **Restauración completa de base + filestore:** `pg_restore` del dump + reextración del
   filestore. Es la única vía que garantiza el retorno exacto al estado previo.

> `git apply -R` **no** recupera por sí solo todo el estado previo tras una actualización.
> Si una actualización fallara a mitad de camino, **detener** y evaluar la recuperación con
> el respaldo; **no** encadenar actualizaciones/restauraciones a ciegas.

## Limitaciones / pendientes (declaradas)

- **No** se realizó restauración de prueba del dump (solo verificación de índice).
- **No** se ejecutó tour de navegador (la validación de UI es de framework; la verificación
  real es de Fase D).
- **Concurrencia general** del producto sigue con ventana residual (los creadores de
  dependencias no toman el `pg_advisory_xact_lock`): no resuelta por este parche.
- **Datos de prueba 15183**: la corrección se validó por equivalencia en el entorno aislado;
  aquí solo se hizo diagnóstico de lectura sobre el registro real.

## Ficheros de esta entrega

- `RESUMEN_FASE_B.md` (este documento)
- `APROBACIONES_Y_ALCANCE.md`
- `EVIDENCIA_RESPALDO.md`
- `EVIDENCIA_APLICACION_Y_ACTUALIZACION.md`
- `VERIFICACION_CADENA_MATERIAL.md`
- `update.log` (actualización; saneado), `diagnostico_15183_readonly.txt`,
  `hashes_before.txt`, `hashes_after.txt`, `git_status_before.txt`, `git_status_after.txt`

No se incluyen secretos, dumps ni filestore en este paquete documental.
