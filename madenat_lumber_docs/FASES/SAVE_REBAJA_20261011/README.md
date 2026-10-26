# PERSISTENCIA Y RECUPERACIÓN DEL TRABAJO DE REBAJA (SAVE) — 2026-10-11

**Incidencia:** «Al preparar las asignaciones, estas no van quedando guardadas» (Mauricio).
**Entorno:** `madenat_test` · `odoo18_app`/`odoo18_db`. **Módulo:** `madenat_lumber_logistics`
**18.0.1.17.0 → 18.0.1.18.0**. **Sin commit/push/despliegue. Sin reparación histórica.**

## 1. Causa exacta (pérdida vs. falta de acceso)
Reproducido con registros de prueba (ver §8). Hay **dos causas separadas**:

- **C1 — Pérdida real en el guardado (P2 + P7, principal).** «Preparar asignación»
  (`action_assign_selected`) crea filas de reparto a **cantidad 0**. Al pulsar **«Guardar borrador»**
  (`action_prepare` → `_i2_build_imputation`), el código **lanzaba `UserError`** («Indique un volumen
  mayor que cero para la etiqueta … (o quite la asignación)») ante **cualquier** fila a 0 ⇒ **no se
  creaba/actualizaba el documento**. Evidencia: `REPRO-02`. La interfaz mostraba las filas
  «preparadas», lo que **parecía** trabajo guardado (P7).
- **C2 — Falta de acceso (P4).** Un borrador **sin reparto positivo** no se localizaba desde el SV:
  el dominio del historial (`action_open_sv_rebajas`) era `[('sv_line_ids.sv_lot_id','=', id)]`, que
  exige una fila de reparto; y al reabrir el asistente desde el SV **no se precargaba la guía**.

Lo que **sí** funcionaba (descartado con evidencia): con cantidades introducidas (por la pestaña
«Materiales» con `cantidad_asignar_m3` o por «Asignación a SV»), el guardado **persistía** y era
recuperable (`REPRO-01/03/04/05`). **No** se atribuyó el fallo a caché, cantidades cero *per se* ni a
error de usuario sin demostrarlo.

## 2. Mapa del guardado transitorio ↔ persistente
| Magnitud | Dónde vive | Persistente |
| --- | --- | --- |
| Selección de etiquetas (`selected`) | `…wizard.line` | transitorio (se reconstruye) |
| Filas de preparación (`sv.line` del asistente) | `…wizard.sv.line` | transitorio |
| Cantidad editable (`cantidad_asignar_m3`) | compute+inverse del asistente | transitorio → escribe el reparto |
| **Reparto con cantidad positiva** | `madenat.sv.imputation.sv.line` | **persistente** |
| **Etiqueta/línea** | `madenat.sv.imputation.line` | **persistente** |
| **Documento** | `madenat.sv.imputation` | **persistente** |
| Reserva documental (draft/pending) | derivada de `imputation.line` activos | — |
| SV de trabajo | **`madenat.sv.imputation.work_sv_lot_id`** (nuevo) | **persistente** |

Guardar el `TransientModel` **no** persiste una rebaja; la persiste `_i2_build_imputation` (documento).

## 3. Comportamiento de «Preparar» y «Guardar borrador»
- **Preparar asignación**: crea trabajo **no aplicado** (filas transitorias a 0). No guarda el documento,
  no aplica, no consume efecto aplicado.
- **Guardar borrador**: crea/**actualiza** el documento persistente (upsert por etiqueta y por
  (línea,SV)), fija `work_sv_lot_id`, **no aplica**, **no duplica** por repetición. Devuelve/abre el
  documento.
- **No** se introduce autosave documental silencioso ni se cambió «Preparar» para que guarde.

## 4. Documento persistente y relación con el SV
`madenat.sv.imputation` en `draft`/`pending` con `work_sv_lot_id` + líneas + repartos. Localizable
desde el SV por: historial (`action_open_sv_rebajas`, ahora incluye `work_sv_lot_id`) y panel «Trabajo
en preparación» del formulario del SV, con **Continuar** (`action_continue_preparation`).

## 5. Cantidades cero
Un destino previsto sin cantidad **se conserva como etiqueta/línea**, pero **no** se persiste como
reparto (el reparto exige volumen > 0 y el `constraint` sigue vigente). **No** se elimina la selección
ni se crean filas inválidas. Límite documentado: el modelo **no** puede guardar «destino previsto sin
cantidad» en `sv.line` (no se crea otra fuente de verdad).

## 6. Identidad, reapertura y duplicados
`documentary_key` con firma; `_i2_find_work_for_guia` reutiliza el trabajo y `_check_single_work_per_guia`
impide 2 borradores por guía ⇒ **actualizar, no recrear**. No se usa «último/primero» como identidad. Un
aplicado **no** se reutiliza (ni IMP02220 por coincidencia de clave).

## 7. Reservas y atomicidad
`draft`/`pending` **reservan** el nominal (política vigente, sin cambios); el fallo de guardado **no**
deja documento parcial ni reserva huérfana (validación antes de escribir; `REPRO`/SAVE‑10). Cancelar
libera; revertir restituye; sin commits manuales ni `sudo` en pruebas.

## 8. Evidencia de reproducción (antes de editar)
`logs/repro.log` (clase temporal, borrada): `REPRO-01` guarda ✔ · **`REPRO-02` EXCEPCIÓN al guardar**
(«Indique un volumen mayor que cero…») ✗ · `REPRO-03` descubrimiento+reapertura ✔ · `REPRO-04/05`
persistencia por pestaña Materiales ✔.

## 9. Pruebas y regresión
Suite nueva `tests/test_sv_rebaja_persistencia.py` (**SAVE‑01..14, FLOW‑01..03, PHY‑01 = 18 pruebas**),
recorriendo los **métodos reales** de guardado y reapertura (no creando el estado final directamente).

| ID | Acredita |
| --- | --- |
| SAVE‑01 | preparar → cantidad → guardar ⇒ documento+reparto persistentes (releído de base) |
| SAVE‑02 | salir → localizar desde el SV → reabrir con mismos datos |
| SAVE‑03 | modificar borrador → guardar ⇒ **actualiza** (mismo id), sin duplicar |
| SAVE‑04 | guardar dos veces ⇒ sin duplicados ni efectos adicionales |
| SAVE‑05 | cantidad cero / trabajo incompleto ⇒ **se guarda sin error**; se conserva la selección; no se persiste reparto inválido |
| SAVE‑06 | dos SV con repartos ⇒ conservación completa; descubrible desde ambos |
| SAVE‑07 | poner a cero **sólo** el SV de trabajo ⇒ otros repartos intactos |
| SAVE‑08 | descartar cambios posteriores ⇒ permanece el último guardado |
| SAVE‑09 | limpieza del transitorio ⇒ documento recuperable |
| SAVE‑10 | fallo intermedio ⇒ atomicidad; borrador previo conservado |
| SAVE‑11 | usuario sin permiso y otra compañía ⇒ `AccessError` (sin `sudo`) |
| SAVE‑12 | dos sesiones sobre el mismo borrador ⇒ sin duplicación (política: última escritura gana) |
| SAVE‑13 | aplicado ⇒ no reabrible como borrador editable |
| SAVE‑14 | firma vacía/cambios de firma ⇒ sin colisión ni reutilización indebida |
| FLOW‑01 | guardar → reabrir → aplicar → consultar |
| FLOW‑02 | cancelar borrador ⇒ reservas liberadas y trazabilidad |
| FLOW‑03 | aplicar → revertir → reasignar → guardar → reabrir → aplicar |
| PHY‑01 | guardar/recuperar sin efectos físicos |

**Comandos y resultados (base `madenat_test`):**
```
odoo -d madenat_test -u madenat_lumber_logistics --test-enable --stop-after-init --no-http \
     --http-port=8071 --test-tags /madenat_lumber_logistics:TestSvRebajaPersistencia
# → 0 failed, 0 error(s) of 18 tests  (EXIT=0)   [logs/save.log]

odoo -d madenat_test -u madenat_lumber_logistics --test-enable --stop-after-init --no-http \
     --http-port=8071 --test-tags /madenat_lumber_logistics
# → logs/regression.log  (mismas fallas preexistentes; ver §14)
```

## 10. Evidencia de navegador
**Sin navegador en el entorno** ⇒ límite declarado; **no** se sustituye por ORM/XML. Guion exacto
entregado (`docs/GUION_NAVEGADOR_SAVE.md`). Aceptación operativa **pendiente de Mauricio**.

## 11. Versión instalada
`madenat_lumber_logistics` **18.0.1.18.0** en `madenat_test` (actualización `-u` sólo de este módulo).

## 12. Archivos y cambios ajenos preservados
Modificados por esta intervención: `models/madenat_sv_imputation.py`,
`wizards/madenat_sv_imputation_wizard.py`, `views/madenat_sv_imputation_views.xml`,
`tests/__init__.py`, `__manifest__.py`, `CHANGELOG.md`, y **nuevo**
`tests/test_sv_rebaja_persistencia.py`. WIP local ajeno **intacto** (sin `reset`/`clean`/`stash`).

## 13. Pendientes y decisiones requeridas
1. **Aceptación en navegador** (guion A–I) — pendiente de Mauricio.
2. **Conflicto de dos sesiones (borradores)**: política actual = **última escritura gana**, sin bloqueo
   optimista. Si se desea detección de sobrescritura, **requiere autorización** (política nueva).
3. **¿«Preparar» debe guardar también?** No se cambió en silencio; si se desea, presentar el efecto
   sobre reservas para autorización.
4. `IMP02220` y `lot_flow_type` histórico: **sin tocar** (regularización pendiente de autorización).

