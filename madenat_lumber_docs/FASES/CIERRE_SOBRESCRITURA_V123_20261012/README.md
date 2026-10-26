# CIERRE DE V1–V3 DEL BLINDAJE DE SOBRESCRITURA — ENTREGA (2026-10-12)

**Entorno:** `madenat_test` **LOCAL** · **Docs:** `madenat_lumber_docs`.
**Regla cumplida:** **SIN COMMIT · SIN PUSH · SIN DESPLIEGUE · SIN REPARACIÓN HISTÓRICA · TEST remoto intacto.**

---

## 1. Dictamen por verificación
| Verificación | Dictamen |
|---|---|
| **V1** — cobertura de cruces con edición directa | **CORREGIDA Y ACREDITADA** (matriz C1–C8; límite residual ORM-sin-versión declarado) |
| **V2** — comportamiento real del cliente | **PENDIENTE** (sin navegador/herramienta; guion entregado; no se sustituye por ORM) |
| **V3** — transacción, SerializationFailure y orden de bloqueos | **ACREDITADA** (TX-01..13) |

## 2. Baseline y respaldos
- Repo `custom_addons/.git`; rama `feat/guia-correccion-documental-preservada-20261002`; **HEAD `b1d2d19`**; base
  **LOCAL** `madenat_test`. Versiones previas: logistics `18.0.1.24.0`, intake `18.0.0.13.0`, core `18.0.6.6.0`.
- Respaldos: `CIERRE_SOBRESCRITURA_V123_20261012/{code,db,filestore}` (diff + pre-copias, `pg_dump -Fc`, filestore).
- Expediente previo leído: `BLINDAJE_SOBRESCRITURA_20261012/` (+ propuesta de sobrescritura). WIP propio/ajeno
  inventariado (`code/wip_status.txt`).

## 3. V1 — Cobertura de cruces con EDICIÓN DIRECTA
**Formulario persistente:** `madenat.sv.imputation`, abierto por `action_madenat_sv_imputation` (menú e historial
desde el SV) y `action_open_imputation`. **Es editable** en `draft`/`pending` (guía, procesador, motivo, líneas
con nominal, repartos con volumen). **No es de sólo lectura** (verificado en vista/ORM).

**Decisión:** **Alternativa A** (mínima, sin cambiar la funcionalidad): reutilizar `edit_version`; el formulario la
envía con **`force_save="1"`** (atributo nativo Odoo 18) y `write()` la compara de forma **atómica**
(`_i2_assert_edit_version`) ⇒ **rechaza** la edición obsoleta. No usa `write_date`/flags/memoria global; no ofrece
sobrescritura forzada. **No** se retiran permisos ni se ocultan campos (Alternativa B no aplicada).

**Matriz C1–C8** (detalle en `docs/MATRIZ_C1_C8.md`; pruebas `tests/test_sv_rebaja_save_lock_direct.py`):
| # | Cruce | Resultado |
|---|---|---|
| C1 | asistente A → asistente B obsoleto | **rechazado** (B) |
| C2 | formulario directo → asistente obsoleto | **rechazado** |
| C3 | asistente → formulario directo obsoleto | **rechazado** |
| C4 | formulario A → formulario B obsoleto | **rechazado** (B) |
| C5 | edición directa de línea → padre obsoleto | **rechazado** |
| C6 | edición directa → asistente obsoleto que aplica | **no aplica** |
| C7 | asistente guarda → formulario obsoleto cambia estado | **rechazado** |
| C8 | transición de estado → formulario obsoleto edita | **rechazado** |

**Límite residual declarado (no oculto):** una escritura **ORM/RPC sin `edit_version`** (script/cliente
programático) **no** se compara (se aplica, pero la versión avanza y todo formulario/asistente abierto lo detecta
después). Cerrarlo exigiría exigir la versión en **toda** escritura de contenido (refactor no «mínimo»), no
implementado sin decisión.

## 4. V2 — Comportamiento real del cliente (PENDIENTE)
**No hay navegador ni herramienta de automatización utilizable** en el entorno local (sin
`chromium`/`chrome`/`firefox`/`chromedriver`/`geckodriver`/`playwright`/`selenium`; sin evidencia de navegador en el
repo). **No** se sustituye por ORM/XML ni se fabrican capturas. **Guion exacto** entregado en
`docs/GUION_V2_CLIENTE.md` (dos pestañas; Guardar/Aplicar/Dejar pendiente; capturas del mensaje, de la conservación
de las ediciones locales, del documento intacto, de la confirmación de recarga y del guardado posterior; cancelar
el diálogo; cerrar la ventana). A nivel ORM, `LOCK-14` acredita que el rechazo **no** adopta la versión ajena en
silencio; **la conservación de las ediciones en el navegador sólo la prueba V2.**

## 5. V3 — Transacción, SerializationFailure y orden de bloqueos (ACREDITADA)
Análisis en `docs/ANALISIS_TX_V3.md`; pruebas `tests/test_sv_rebaja_save_lock_tx.py` (**TX-01..13 → 0 failed/0
error**). Puntos clave: `_i2_guarded_build` fuerza `flush_all()` dentro de la transacción y traduce
`SerializationFailure` al mensaje operativo; **sin** `commit` manual; **sin** continuar con el cursor tras error
PG; **sin** reintento que sobrescriba. **Orden de bloqueos determinista** `1 (documento) → 2 (SV) → 3 (etiqueta)`;
las rutas sin documento (reabrir/revertir/cancelar) toman solo 2/3 ⇒ **sin deadlock**. **Rechazo por VERSIÓN con el
lock LIBRE** (TX-07) y por LOCK ocupado (TX-08); rollback íntegro (TX-01/06/13); sin auditoría de transición
fallida (TX-05).

## 6. Mapa de escritores (actualizado)
| Entrada | Método | Escritura | Versión | Guard |
|---|---|---|---|---|
| Guardar/Aplicar/Dejar pendiente | `action_prepare/pending/apply` → `_i2_guarded_build` → `_i2_build_imputation` | doc + líneas + repartos | +1 por contenido | estado + **versión (ns 1)** |
| Edición directa (formulario) | `write()` | doc (+ líneas/repartos) | +1 | **versión si el cliente envía `edit_version`** |
| Edición directa de líneas/repartos | `.line`/`.sv.line` create/write/unlink | hijos | **eleva el padre** | inmutabilidad applied |
| Cancelar / Reabrir / Revertir | `action_cancel/reopen_to_draft/reverse` | doc (state) | +1 | permisos/estado; locks 2/3 |
| Reconstruir/Continuar/Recargar | `_i2_reconstruct_commands`, `action_reload_current` | — (lee) | 0 | — |

## 7. Correcciones, archivos y diff
- **Modelo** `models/madenat_sv_imputation.py`: guard de versión en `write()` para la edición directa
  (bloque `if 'edit_version' in vals …` → `_i2_assert_edit_version` + bump). (El resto del LOCK ya existía.)
- **Vista** `views/madenat_sv_imputation_views.xml`: `<field name="edit_version" force_save="1" invisible="1"/>` en
  el formulario.
- **Pruebas nuevas:** `tests/test_sv_rebaja_save_lock_direct.py` (V1), `tests/test_sv_rebaja_save_lock_tx.py` (V3);
  `tests/__init__.py`.
- **Metadata/docs:** `__manifest__.py` (18.0.1.25.0), `CHANGELOG.md`, CANON 19/02/03/índice.
- **Sin** cambios en permisos, menús, modelos de negocio, wizard, ledger ni políticas.

## 8. Pruebas y regresión (cifras exactas)
- **Dirigidas LOCK/V1/V3:** **45 tests → 0 failed / 0 error** (`v13_run2.log`); V1 9 + V3 13 + LOCK 23.
- **Logistics (comparable con la base):** **501 tests → 4 failed / 0 error** — las **mismas 4** preexistentes
  (baseline `444/4`). `+57 tests` (P1–P4 12 + LOCK 23 + V1 9 + V3 13), **0 fallas nuevas**.
- **Amplia** (`core+intake+logistics`): **1275 tests → 6 failed / 4 error** — el **mismo conjunto exacto** de 10
  fallas que la base (baseline `1217 → 6 failed / 4 error`). `intake` **467/0**; `+22 tests` (V1+V3) todos verde,
  **0 fallas nuevas**.
- **Sin debilitar pruebas**; se actualizaron sólo aserciones de política/UI ya justificadas en la entrega previa.

## 9. Versiones locales e instalación
`madenat_lumber_logistics` **18.0.1.24.0 → 18.0.1.25.0**; `madenat_lumber_core` **18.0.6.6.0** (sin cambios);
`madenat_lumber_intake` **18.0.0.13.0** (sin cambios). `-u` solo del módulo afectado.

## 10. Documentación actualizada
`CANON/19 §19.31` (1.29.0), `CANON/02 §17.16.29` (12.38.0), `CANON/03 §29` (6.37.0), `CANON/INDICE`;
`CHANGELOG.md`. Docs de expediente: `docs/MATRIZ_C1_C8.md`, `docs/GUION_V2_CLIENTE.md`, `docs/ANALISIS_TX_V3.md`,
`docs/PLAN_DESPLIEGUE.md`. Una sola fuente canónica; evidencia before/after conservada.

## 11. WIP ajeno preservado
Solo se tocaron archivos de `madenat_lumber_logistics` y `madenat_lumber_docs`; `HEAD` sin cambios (sin commit).
Nuevos en WIP: los dos test files V1/V3.

## 12. Pendientes y autorizaciones necesarias
1. **V2 (cliente/navegador): PENDIENTE** — requiere navegador; guion entregado.
2. **Límite residual:** escritura ORM/RPC **sin** `edit_version` no se compara (cerrarlo exige exigir la versión en
   toda escritura de contenido → decisión).
3. **Multi-worker real**: no ejecutado (guard no depende del proceso).
4. Aceptación de Cristhian (TEST remoto intacto).

## 13. Plan de despliegue (PREPARADO, NO EJECUTADO)
`docs/PLAN_DESPLIEGUE.md`: módulo `madenat_lumber_logistics 18.0.1.25.0`; migración aditiva; comando
`-u madenat_lumber_logistics` (no `-u all`); respaldos; smoke test (incluye guion V2); rollback. **Requiere
autorización independiente de Mauricio.**

---
**SIN CAMBIOS EN TEST REMOTO · SIN COMMIT · SIN PUSH · SIN DESPLIEGUE · SIN REPARACIÓN HISTÓRICA.**
