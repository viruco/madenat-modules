# INFORME V2 — INVESTIGACIÓN D18 (5 archivos) Y P2-2 (menú de reports)

**FASE 6 · 2026-10-15 · SOLO LECTURA — no se ejecutó ninguna acción sobre estos archivos.**
**Base del análisis:** HEAD `ed42df5` + WIP local (16 entradas). Diff completo de cada archivo en `logs/d18_*.diff`.

> **Método:** hecho + evidencia (ruta y línea cuando aplica) + efecto en el HEAD limpio + riesgo.
> **No** se infiere autoría ni intención. Los archivos D18 son los 5 que el triaje de FASE 1 marcó
> `desconocido` (3 de ellos en `logistics`, 1 en `core` y 1 más en `logistics`).

---

## FICHA D18-1 — `madenat_lumber_core/tests/test_duplicate_validation.py`

| Dato | Valor |
|---|---|
| Estado | **Modificado** (trackeado), `+17 / −5` |
| mtime | **2026-10-07 17:33:27** |
| Último commit que lo tocó | `b0bf9df` (2026-08-29, BT-01..BT-04) |
| ¿Registrado en suites? | **Sí**, `madenat_lumber_core/tests/__init__.py:4` (línea pre-existente, no cambiada) |

**Qué hace el cambio.** Renombra `test_02_duplicate_in_guia_processing` → `test_02_homonym_guia_vs_reception`
y **invierte la expectativa**: un homónimo de número entre flujos (**guía procesada** vista desde la ruta de
**Recepción**) **NO** debe bloquear; sí debe bloquear la identidad natural **del mismo modelo**, invocando
`_check_guide_duplicate(..., exclude_model='madenat.guia.processing')`. Añade la nota «(2026-10-07):
expectativa derivada de la matriz documental… se corrige a la política simétrica» y cita *CANON/12 §5.2*.

**Evidencia de atribución (sí demostrada).**
1. **Documento canónico en el repo:** `madenat_lumber_docs/CANON/12_FLUJOS_INGESTA.md` §5.2 «Prohibiciones»:
   *«No usar `guia_number` como discriminador… no es confiable para distinguir origen»*; §6.2: *«La
   coincidencia por `guia_number` es un hallazgo operativo, pero no constituye el discriminador canónico»*.
   (La cita del test es algo laxa —§5.2 es «Prohibiciones»— pero el fondo está respaldado.)
2. **Código ya commiteado:** el parámetro que el test ejercita existe **solo** en el árbol nuevo:
   `exclude_model/cross_model` aparecen **0** veces en `b1d2d19` y **8** en el commit **②** (`0ef4388`).
3. **Ventana temporal coherente:** mtime 17:33 cae **2 minutos después** de `FIX_GUIA_DUP_FINAL_20261007_171740`
   (17:31) y dentro del bloque `AUDIT_GUIA_DUPLICADOS_20261007` (16:34) → `INCIDENTE_GUIA_15183_20261007`
   (18:28).

**Dependientes / efecto en el HEAD limpio.** Ningún archivo commiteado depende de él (es una suite). Pero el
**código commiteado sí invalida su versión antigua**: con `cross_model=False` por defecto, el test viejo
`test_02_duplicate_in_guia_processing` espera un `UserError` que **ya no se produce** ⇒ **falla** (falla
**nueva** respecto del baseline). *(Confirmado empíricamente en V1.)*

| Riesgo | Valoración |
|---|---|
| **Commitearlo** | **Bajo.** Alinea el test con el código y con CANON/12. Solo cambia expectativas de prueba |
| **No commitearlo** | **Medio.** El HEAD limpio queda con una suite en rojo que contradice la política canónica y el código entregado ⇒ falso positivo permanente en cualquier regresión futura |

**Recomendación:** `REQUIERE_DECISIÓN` — **incluir en el commit de cierre de `core`** (con el resto de la
intervención guías-dup). Sin implicaciones de producción (es una prueba).

---

## FICHA D18-5 — `madenat_lumber_logistics/tests/test_service_return_imputation_guard.py`

| Dato | Valor |
|---|---|
| Estado | **Modificado**, `+2 / −0` (2 líneas) |
| mtime | **2026-10-10 21:11:53** |
| Último commit que lo tocó | `573a164` (2026-10-10, «consolida ingreso, retorno de servicio e imputación SV») |

**Qué hace.** Antes de `imp.action_reverse()` asigna `imp.reversal_reason = 'Reversa de prueba (GUARD-06/09).'`
en los tests **06** y **09**.

**Evidencia de atribución (sí demostrada).** El **código commiteado** en ④ exige motivo de reversa:
`madenat_lumber_logistics/models/madenat_sv_imputation.py:1083-1087` → `if not ((rec.reversal_reason or
'').strip() or (rec.reason or '').strip()): raise UserError('Indique el motivo de la reversa…')`.
En `b1d2d19` ese guard **no existía** (el `action_reverse` antiguo reversaba sin motivo). El comentario del
código lo liga a **AUD-ETQ-02 / AUD-ETQ-06** y a *CANON/19 §19*. La ventana (2026-10-10, 21:11) coincide con
`CONCILIACION_ENVIO_RETORNO_20261010`, `IMPL_ASSIGN_SV_20261010_165247` y `FIX_SV_SELECCIONAR_TODAS_20261010`.

**Dependientes / efecto en el HEAD limpio.** Es una suite. Con el guard commiteado y el test **antiguo**, los
tests **06** y **09** lanzan `UserError` ⇒ **2 fallas nuevas** en el HEAD limpio. *(Confirmado en V1.)*

| Riesgo | Valoración |
|---|---|
| **Commitearlo** | **Muy bajo.** 2 líneas que adaptan el test a una regla de negocio ya entregada |
| **No commitearlo** | **Medio.** 2 fallas permanentes en la regresión de `logistics`, ajenas al código real |

**Recomendación:** `REQUIERE_DECISIÓN` — **incluir en el commit de cierre de `logistics`**.

---

## FICHA D18-2 — `madenat_lumber_logistics/wizards/lumber_shipment_rebaja_wizard.py`

| Dato | Valor |
|---|---|
| Estado | **Modificado**, `+380 / −50` (el mayor de los cinco) |
| mtime | **2026-10-03 23:54:37** |
| Último commit que lo tocó | `768306c` (2026-10-01, «B3/B4: wizard Rebajar por nave + zarpe sin descuento de stock») |
| Modelo | `lumber.shipment.rebaja.wizard` (**+ `lumber.shipment.rebaja.wizard.line`**, que **no existe** en la versión commiteada) |

**Qué agrega el diff.** El submodelo `.line`; campos `line_ids`, `excluded_container_ids`, `excluded_count`,
`selected_count`, `total_lots`, `voyage_available`, `result_message`, `eligible`, `exclusion_reason`,
`patio_names`, contadores de volumen (`total_export_m3`, `total_nominal_m3`, `total_sv_m3`, `rebaja_m3`…), y
los métodos `_rebaja_require_group`, `_scope_containers`, `_classify`, `_planned_lines_safe`,
`_container_metrics`, `_rebuild_lines`, `_get_selection_domain`, `_line_commands`, `_compute_*` y los
`create()`/`write()` de reconstrucción de líneas.

**Evidencia de atribución (sí demostrada — documental).**
1. **`CANON/18_CONSOLIDACION_Y_REBAJA.md` §7.3 «Rebajar por nave (masiva)»:** *«`lumber.export.shipment` +
   wizard nuevo `lumber.shipment.rebaja.wizard`. Selección: nave y viaje. Lista: contenedores consolidados
   pendientes… Datos que alimenta: selección múltiple de contenedores; por cada uno aplica la rebaja con
   idempotencia por (contenedor, lote). Resume volúmenes EXPORT/NOMINAL y saldos SV»* → **coincide campo a
   campo** con `excluded_container_ids`/`selected_count`/`total_export_m3`/`total_nominal_m3`/`total_sv_m3`.
2. **CANON/18 §14.1 «Resuelto y verificado»:** *«Rebaja por nave (asistente): selección nave/viaje, lista de
   contenedores pendientes por embarque, rebaja masiva con **savepoint por contenedor** e informe de
   éxitos/fallos»* y *«Permisos: grupos existentes… con rechazo en servidor (**`_rebaja_require_group`**)»* →
   son **exactamente** los añadidos del diff.
3. **`FASES/AUDIT_B01_20261004/AUDITORIA_B01_FASE_A.md`** (2026-10-04) analiza el estado **ya modificado**: cita
   `lumber.shipment.rebaja.wizard._classify` (:209) y la rama `feat/rebaja-contenedor-20261001`. `_classify`
   **no existe** en la versión commiteada ⇒ ese estado ya estaba en el árbol el 2026-10-04.
4. **`WIKI/05_INCIDENTES/INC-011…20261003.md`** menciona el modelo en el incidente de desalineación
   código/BD del **2026-10-03** (mismo día del mtime).

**Dependientes commiteados (¡bloqueo duro!).**
- `security/ir.model.access.csv` (**commiteado en ④**) contiene **3 filas** que apuntan a
  `model_lumber_shipment_rebaja_wizard_line` (líneas 51-53) — modelo que **solo** declara este archivo.
  Escaneo estático del HEAD: **es la única incoherencia ACL→modelo** del repo ⇒ en el **HEAD limpio**
  `madenat_lumber_logistics` **no puede instalar ni actualizar** (*External ID not found*).
  *(Confirmado empíricamente en V1.)*
- `views/logistics_menus.xml:39` (commiteado) apunta a `action_lumber_shipment_rebaja_wizard`, definido en
  `lumber_shipment_rebaja_wizard_views.xml` (D18-3). Como el archivo antiguo **sigue trackeado y listado en el
  manifest**, la acción **sí** se resuelve ⇒ no hay error de carga por el menú, pero el asistente abre la
  versión **antigua** (sin selección múltiple, sin métricas, sin resumen).
- `tests/test_rebaja_contenedor.py` (D18-4) usa los campos nuevos ⇒ depende de este archivo.

| Riesgo | Valoración |
|---|---|
| **Commitearlo** | **Bajo-medio.** Es la pieza que falta para que el commit ④ sea coherente; el diseño está documentado en CANON/18 §7.3/§14.1. Añade un transitorio nuevo (`.line`) y ACL ya presentes. Requiere `-u` de `logistics` y humo del asistente |
| **No commitearlo** | **ALTO (bloqueante).** El commit ④ tal cual **no carga** en un entorno limpio (ACL huérfana) ⇒ el despliegue al TEST remoto **falla** en `madenat_lumber_logistics` |

**Recomendación:** `REQUIERE_DECISIÓN` — **incluir en el commit de cierre de `logistics`** (único camino que
hace desplegable el HEAD sin retirar la ACL ya commiteada). *Alternativa* (peor): revertir las 3 filas de ACL
del commit ④ y dejar el asistente antiguo operativo — perdería la funcionalidad documentada.

---

## FICHA D18-3 — `madenat_lumber_logistics/wizards/lumber_shipment_rebaja_wizard_views.xml`

| Dato | Valor |
|---|---|
| Estado | **Modificado**, `+51 / −10` |
| mtime | **2026-10-03 23:55:15** (36 s después de D18-2) |
| Último commit | `768306c` (2026-10-01) |
| Listado en manifest | **Sí** (`__manifest__.py:45`) |

**Qué hace.** Rehace el formulario del asistente (lista de contenedores con `line_ids`,
`eligible`/`exclusion_reason`, métricas y `result_message`) y **define la acción**
`action_lumber_shipment_rebaja_wizard` (`:76`) que usa el menú commiteado.

**Evidencia de atribución.** Misma que D18-2 (CANON/18 §7.3/§14.1 + mtime gemelo 2026-10-03). El diff **no**
contiene marcadores AD/AUD/fecha propios.

**Dependientes / HEAD limpio.** El archivo antiguo define la misma acción ⇒ la carga **no** se rompe; el
asistente muestra la interfaz vieja. Escaneo del HEAD: `voyage_available`, `excluded_container_ids`,
`_rebuild_lines`, `_scope_containers` = **0** referencias fuera de los archivos D18.

| Riesgo | Valoración |
|---|---|
| **Commitearlo** | **Bajo.** Solo vistas del asistente; **necesita** el `.py` (D18-2) para sus campos |
| **No commitearlo** | **Medio (funcional).** El menú «Rebaja por nave» queda con UI antigua y sin el resumen de éxitos/fallos documentado |

**Recomendación:** `REQUIERE_DECISIÓN` — **incluir junto con D18-2**. Separarlos es inviable: los campos que
pinta solo existen en D18-2, y la UI nueva sin el `.py` daría error de campo inexistente.

---

## FICHA D18-4 — `madenat_lumber_logistics/tests/test_rebaja_contenedor.py`

| Dato | Valor |
|---|---|
| Estado | **Modificado**, `+382 / −14` |
| mtime | **2026-10-05 15:31:58** |
| Último commit | `7cab34a` (2026-10-05, «retorno físico total de Rebaja R2») |
| Registrado en suites | **Sí** (`tests/__init__.py`, línea pre-existente) |
| Clase | `TestRebajaContenedor` — **citada en CANON/18 §14.5** («Suite madenat_lumber_logistics: 32 pruebas… `TestRebajaContenedor`…») |

**Qué hace.** Amplía la suite del contenedor/rebaja: escenarios de **rolleo seguro** post-rebaja/post-zarpe,
**zarpe con excepción con motivo** (I1.6/B-01), retorno físico R2 y las nuevas reglas de
`lumber.shipment.rebaja.wizard` (usa `line_ids` ×6, `voyage_available`, `result_message`, `excluded_count`,
`selected_count`, `eligible`, `exclusion_reason`).

**Evidencia de atribución (parcial, por documento canónico).** CANON/18 §14.5 cita la suite
`TestRebajaContenedor` como evidencia de la rama `feat/rebaja-contenedor-20261001`; el comentario interno
«*Rebaja Inteligente por Motonave — asistente operativo (2026-10-03)*» y «*P0 (2026-10-03) — Guarda de rolleo
seguro*» fechan el trabajo. **No** hay entrada de CHANGELOG, AD ni expediente que documente **estas** nuevas
aserciones concretas ⇒ atribución **de la suite a la intervención rebaja-contenedor (sí)**, de **cada
expectativa nueva (no demostrada caso por caso)**.

**Dependientes / HEAD limpio.** Es una suite. Su versión commiteada (antigua) corresponde al asistente antiguo
⇒ **debería seguir pasando** en el HEAD limpio (a verificar en V1). La versión del WIP depende de D18-2:
commitearla **sin** D18-2 daría errores de campo inexistente.

| Riesgo | Valoración |
|---|---|
| **Commitearlo** | **Bajo-medio**, pero **solo junto con D18-2/3** (dependencia dura de campos) |
| **No commitearlo** | **Bajo.** El HEAD conserva la suite antigua, coherente con el asistente antiguo |

**Recomendación:** `REQUIERE_DECISIÓN` — incluir **junto con D18-2/3** si se cierra D18; si se decide
**no** cerrar D18, **dejarlo fuera** (es coherente con el estado actual).

---

## FICHA P2-2 — `madenat_lumber_reports/views/lumber_reports_menu.xml`

| Dato | Valor |
|---|---|
| Estado | **Modificado**, `+7 / −2` |
| mtime | **2026-10-03 22:37:24** (mismo día que el trabajo rebaja-motonave, ~1 h antes de D18-2) |
| Último commit | `994bcbd` (2026-05-31, baseline v1.0) |
| Módulo | `madenat_lumber_reports` **18.0.2.3.0** (instalado en `madenat_test`) |

**Qué hace.** Añade `active="0"` al único `<menuitem>` del archivo (`menu_lumber_reports_root`,
«📈 Reportes MADENAT», `parent="madenat_lumber_logistics.menu_lumber_logistics"`, `sequence=98`) y un
comentario que lo explica. El menú **no declara `action`** ni tiene hijos.

**Hechos verificados.**
1. **«P2-2» no existe en ningún otro lugar:** búsqueda en `CANON/**`, `CHANGELOG*`, `*.py`, `*.xml`, `*.csv`,
   `git log --grep` y el historial del archivo ⇒ **única aparición: el comentario del propio cambio**.
   Sufijo «P2-2» sugiere un listado de prioridades, **no localizado**. ⇒ **origen no demostrado**.
2. **Es una carpeta vacía:** `grep -rn 'menu_lumber_reports_root'` devuelve **solo su definición**;
   ningún otro XML lo usa como `parent`.
3. **La entrada oficial sí existe y está commiteada:** `madenat_lumber_core.menu_madenat_reports_main`
   («📊 Reportes y Listados», `lumber_core_menu.xml:249`), con las acciones R1–R9/Listados/Packing accesibles.
4. **Quién pierde acceso:** nadie pierde **reportes**; solo desaparece un **ítem de menú vacío** (visible para
   los usuarios que ven el menú de Logística, del que hereda la visibilidad). Impacto **cosmético**.
5. **Cautela de dependencias:** `madenat_lumber_reports.depends` incluye `madenat_lumber_costing` (D1
   bloqueado), más `madenat_vendor_payment` y `madenat_lumber_billing`. Un `-u madenat_lumber_reports`
   **no obliga** a actualizar costing, pero arrastra el riesgo de tocar un módulo cuyo grafo está congelado.

| Riesgo | Valoración |
|---|---|
| **Commitearlo / desplegarlo** | **Muy bajo funcional** (oculta una carpeta vacía); **medio de proceso**: sin AD ni expediente que lo atribuya, y dentro de un módulo cuyo grafo depende de `costing` bloqueado |
| **No commitearlo** | **Muy bajo.** Se conserva un ítem de menú vacío (ruido de navegación). La FASE 3 ya había registrado que el menú vacío id 376 era «candidato a inactivar» |

**Recomendación:** `REQUIERE_DECISIÓN` — **mantenerlo fuera del despliegue** hasta que exista una **AD** que
registre la decisión («inactivar la carpeta vacía 📈 Reportes MADENAT») y se acuerde el momento de despliegue
de `madenat_lumber_reports`. *(Alternativa aceptable y de coste cero: dejarlo como está — no hay pérdida
funcional.)*

---

## RESUMEN V2 — RECOMENDACIONES (todas `REQUIERE_DECISIÓN`, sin ejecutar nada)

| Ficha | Archivo | Atribución | Efecto en el HEAD limpio (V1) | Recomendación |
|---|---|---|---|---|
| **D18-1** | `core/tests/test_duplicate_validation.py` | **Demostrada** (CANON/12 §5.2/§6.2 + commit ②) | Suite no ejecutada en V1 (el registro aborta antes); por análisis: **1 falla** | **Incluir** en el commit de cierre de `core` |
| **D18-2** | `logistics/wizards/lumber_shipment_rebaja_wizard.py` | **Demostrada** (CANON/18 §7.3/§14.1 + `AUDIT_B01_20261004`) | **BLOQUEANTE**: `madenat_lumber_logistics` no carga (ACL → modelo inexistente) | **Incluir** en el commit de cierre de `logistics` (cierra D18) |
| **D18-3** | `.../lumber_shipment_rebaja_wizard_views.xml` | **Demostrada** (idem D18-2) | La acción antigua resuelve; UI antigua | **Incluir junto con D18-2** |
| **D18-4** | `logistics/tests/test_rebaja_contenedor.py` | **Parcial** (CANON/18 §14.5 cita la suite; expectativas nuevas no documentadas una a una) | Suite antigua coherente con el asistente antiguo | **Incluir junto con D18-2/3** si se cierra D18 |
| **D18-5** | `logistics/tests/test_service_return_imputation_guard.py` | **Demostrada** (guard commiteado + AUD-ETQ-02/06 + CANON/19) | No evaluable empíricamente (logistics no carga); por análisis: **2 fallas** | **Incluir** en el commit de cierre de `logistics` |
| **P2-2** | `reports/views/lumber_reports_menu.xml` | **No demostrada** («P2-2» sin rastro) | Irrelevante (módulo fuera del despliegue) | **Mantener fuera** hasta que exista AD |


