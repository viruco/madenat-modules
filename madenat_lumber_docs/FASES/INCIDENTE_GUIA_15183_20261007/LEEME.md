# LEEME — Incidente guía 15183 (MADENAT · Odoo 18 CE · 2026-10-07)

Fases: **diagnóstico** → **reproducción aislada** → **corrección en aislamiento** →
**aplicación autorizada a `madenat_test`** (gate de reconstrucción, respaldo verificado,
ventana controlada). **Sin** commit/push ni despliegue a producción. ACL, CANON y datos
históricos intactos; guía 33154 y recepción 1369 **no** modificadas.

## Contenido

| Archivo | Qué es |
|---|---|
| `DICTAMEN_INCIDENTE.md` | Respuestas directas (9 preguntas) + cierre. |
| `MAPA_RUTA_REAL.md` | Ruta real botón→control→notificación y orden de datos. |
| `COMPARACION_DOCUMENTAL.md` | Identidad documental (números, emisor, checksums, líneas). |
| `RESULTADOS_REPRODUCCION.md` | Reproducción aislada (hallazgo), comandos y resultados. |
| `PROPUESTA_MINIMA.md` | Corrección mínima + conflicto doctrinal. |
| `DIFF_MINIMO.patch` | Diff mínimo de la corrección (3 modelos + 3 pruebas). |
| `RESULTADOS_IMPLEMENTACION.md` | Corrección **implementada en aislamiento** + resultados (52 tests). |
| `PLAN_APLICACION.md` | Plan de aplicación (ejecutado el 2026-10-07). |
| `APPLICACION_RESULTADO.md` | **Resultado de la aplicación** a `madenat_test` (hashes, respaldo, update, servicios, git). |
| `PROPUESTA_CANON_12_5_2.md` | Interpretación de §5.2 para ratificación (sin editar CANON). |
| `PRUEBA_REGRESION_test_guide_dup_regression_15183.py` | Prueba de regresión (falla con el código actual). |
| `workcopy/addons/` | Copia del código con la corrección aplicada (bind `:ro`). |
| `logs/iso_run_regression.log` | Log de la reproducción (antes del fix): `2 failed, 0 error(s) of 4`. |
| `logs/iso_run_fixed.log` | Log de la corrección: `0 failed, 0 error(s) of 52`. |
| `logs/update_madenat_test.log` | Log de la actualización `-u madenat_lumber_core` en `madenat_test` (0 ERROR). |
| `logs/incidente_window_log.txt` | Extracto del log del intervalo del incidente. |

## Reproducir

```bash
bash INCIDENTE_GUIA_15183_20261007/run_iso.sh
```

## Resultado en una línea

**Antes del fix (reproducción):** crear un Procesado `15183` (emisor `1052`) con la
Recepción `15183` del **mismo** emisor **no se bloqueaba** (cross-model no
inspeccionado; sólo aviso). **Tras el fix (aislado):** bloquea (identidad número +
emisor), y el **emisor distinto** sigue permitido. Suite: `0 failed, 0 error(s) of 52`.

## Seguridad y límites

- Base de reproducción **aislada** `repro_inc_15183_20261007` (copia de `madenat_test`).
- `madenat_test` sólo recibió **lecturas** (`SELECT`) y un `pg_dump` de lectura.
- El árbol activo `custom_addons/` **no** fue modificado (copia montada `:ro`).
- **[U]** No hay log de cliente web que pruebe el doble clic de la notificación.
- **[U]** La revisión exacta en memoria del proceso activo no es verificable sin
  reiniciar (prohibido); se usó el árbol activo identificado por **hashes**.

## Cierre

> **La ingesta pasó porque** la comprobación de duplicado confirmado de la ruta
> Procesado sólo inspecciona su propio modelo (`cross_model=False`); la Recepción
> homónima del **mismo emisor** quedó invisible al bloqueo.
> **El control sobre staging/cabecera** no depende de stock (sí busca cabeceras),
> pero **excluye por modelo**: encontró la Recepción sólo en la llamada de aviso
> no bloqueante.
> **La intervención mínima propuesta es** comparar por **identidad (`name` +
> emisor)** a través de **ambos** flujos en el **punto único**
> `madenat_lumber_core/models/reception_parser.py::_check_guide_duplicate`
> (+ `cross_model=True` en los llamadores de bloqueo), en
> `madenat_lumber_core/models/reception_parser.py`.
> **Los registros reales no fueron modificados.**
