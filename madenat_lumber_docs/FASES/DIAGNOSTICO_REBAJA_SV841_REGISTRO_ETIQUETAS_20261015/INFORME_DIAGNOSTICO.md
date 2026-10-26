# DIAGNÓSTICO FUNCIONAL — REGISTRO DE ETIQUETAS EN «REBAJA DE ETIQUETAS» (SV00000000841)

**Fecha:** 2026-10-15 · **Entorno:** LOCAL `madenat_test` · **Módulo:** `madenat_lumber_logistics` (+ `core`)
**HEAD:** `677294b7cdc3e0cfbe1cdaef441efcb2234f8681` (`feat/guia-correccion-documental-preservada-20261002`)
**Alcance:** **SOLO LECTURA** + reproducción en transacción **REVERTIDA** (`odoo shell`, `env.cr.rollback()`).
**Sin commit · sin push · sin cambios de código/datos/ACL/vistas · sin TEST remoto · sin `-u all` · sin reparación histórica.**
**No se tocó `IMP04823` ni `IMP02220`** (ni su estado, ni sus líneas, ni su clave).

---

## 0. Dictamen (resumen ejecutivo)

**El registro de etiquetas SÍ funciona** en un caso sano: se demostró (con rollback) una rebaja completa
(`draft → applied`, con firma SHA-256, reparto persistido y saldo documental actualizado en el SV).
En el caso reportado **no hay ninguna etiqueta registrada** y la causa queda **demostrada con código y datos**:
son **tres defectos encadenados**, todos **preexistentes** (ninguno introducido por las FASES 5–8 ni por el WIP):

| # | Defecto | Evidencia | Efecto operativo |
|---|---|---|---|
| **F1** | **`_i2_signature()` no incluye la SELECCIÓN de etiquetas** (solo los repartos SV) y `_i2_get_or_create()` busca por `documentary_key` **sin filtrar estado**; `documentary_key` es **UNIQUE** | `models/madenat_sv_imputation.py:445,462` · `wizards/…_wizard.py:586` · reproducción E1/E2/E3 | Para la **guía 1198** cualquier «Guardar» **sin reparto > 0** colisiona con el documento **APLICADO `IMP02220`** ⇒ `UserError: «La imputación IMP02220 ya no admite preparación (estado applied)»` ⇒ **las etiquetas nunca se registran** |
| **F2** | El campo «Trabajo en preparación» **no filtra por estado en el servidor** (el `domain` del O2M no se aplica al leer) y el **contador usa ese mismo campo** | `…:1450,1455,1559` · lectura ORM: el campo devuelve `[2733]` (`cancelled`) y `count = 1` (en transacción llegó a **2**: anulada + aplicada) | La sección lista y **cuenta** documentos **anulados/aplicados** como «trabajo en preparación» y ofrece **«Continuar»**, que falla con `UserError` (`…:901`) |
| **F3** | «Guardar borrador» **no exige ≥1 etiqueta** (solo `action_apply` lo exige) | `…_wizard.py:602-717` (sin guarda) vs `models/…:640` | Un documento **vacío** con `work_sv_lot_id` queda como «trabajo en preparación» **sin aviso**; es el estado exacto de `IMP04823` (0 líneas + vínculo al SV) |

**Reconstrucción de lo ocurrido (coherente con los datos):** se preparó un documento para la guía **1198** con
etiquetas y un **destino SV sin cantidad** (firma no vacía ⇒ clave distinta ⇒ documento nuevo **con líneas**,
`IMP04823`, creado 2026-10-11 02:27); después se guardó **sin ninguna etiqueta incluida** ⇒ las líneas se
eliminaron ⇒ documento **vacío pero vinculado** a `SV00000000841`; finalmente quedó **anulado** (sin metadata
ni bitácora ⇒ no fue `action_cancel`) y, por **F2**, sigue apareciendo en la sección con «Continuar».

**Hipótesis descartadas con prueba:** (a) la lista incluye anuladas «por dominio mal escrito» → el dominio es
correcto, pero **no lo evalúa el servidor**; (b) la guía no tiene lotes/saldo → tiene **17 lotes candidatos**
con volumen; (c) falta de procesador → **no** bloquea (llega al `UserError` de estado); (d) regresión de FASE 5–8
→ las funciones implicadas son **idénticas en HEAD y en el WIP** (diff vacío) y existen desde el commit `2888745`
(2026-10-02, I2/AD-91); `ded5e89` se commiteó el 2026-10-15 10:55.


---

## 1. Baseline y garantía de no-cambios

**Antes y después de TODO el trabajo (idéntico):**

```
rama=feat/guia-correccion-documental-preservada-20261002  HEAD=677294b7cdc3e0cfbe1cdaef441efcb2234f8681
git status --porcelain → 11 entradas · stash → 0
huella sha256 del WIP (11 archivos) → 90d42406807ce615cd9f48abbe5fd22e823f44f8d8381cce230027a0810f1b22
madenat_test → guia=13 recep=8 users=12 lots=151 audit=327 imput=3 lineas=3 repartos=1
IMP04823 → state=cancelled lineas=0 write=2026-10-12 19:43:36.45072
stock.lot 10215 → quants 7840=-40.3150 (loc 4), 7841=+40.3150 (loc 8)  [intactos]
```

Las reproducciones se ejecutaron dentro de una transacción y terminaron con `env.cr.rollback()`; el `diff` de la
huella del WIP y los conteos confirman **cero residuos** (no quedaron documentos, líneas ni repartos).

---

## 2. Estado real de los datos (§3.A)

### 2.1 `IMP04823` — `madenat.sv.imputation` id **2733**

| Campo | Valor |
|---|---|
| `name` / `state` | `IMP04823` / **`cancelled`** |
| `documentary_key` | `IMP-1198-A87816E2021EC9AA` |
| `guia_processing_id` | **1198** (guía «19827») |
| `work_sv_lot_id` | **10215 = `SV00000000841`** ⇒ por eso aparece en la ficha de ese SV |
| `processor_id` / `processor_location_id` | vacíos |
| `line_ids` / `sv_line_ids` | **0 / 0** ⇒ «Etiquetas», «Reparto SV» y «Envíos» **sin registros** |
| `executed_by_id` / `execution_date` | vacíos (nunca aplicada) |
| `reversed_by_id` / `reversal_date` | vacíos |
| `cancelled_by_id` / `cancellation_date` / `cancellation_reason` | **vacíos** ⇒ **no** pasó por `action_cancel` (`models/…:789-806`) |
| `reopened_by_id` / `reopen_date` / `reopen_reason` | vacíos (nunca se reabrió) |
| `snapshot_json` / `audit_hash` | vacío / vacío |
| `edit_version` | 1 |
| `create_date` / `write_date` | 2026-10-11 02:27:56 / **2026-10-12 19:43:36** (uid 8) |

### 2.2 Guía **1198** (`madenat.guia.processing`, «19827», `validated`, tipo `service`)

* **17 lotes** procesados (`18362…18378`), todos con **`lot_flow_type` NULL** y quants **netos 0**
  (+X en una ubicación y −X en otra) ⇒ no hay «saldo» físico, pero **sí son candidatos** del asistente:
  `_i2_processed_lots` filtra en **Python** (`l.lot_flow_type != 'volume'` ⇒ `None` **se incluye**)
  → `wizards/madenat_sv_imputation_wizard.py:423-425`.
  *(Un dominio SQL `[('lot_flow_type','!=','volume')]` — el de los Many2one, p. ej. `…_wizard.py:929` —
  **excluiría** los NULL; aquí no se usa para poblar líneas, por eso hay 17 candidatas.)*
* **2 imputaciones** sobre esta guía: `IMP02220` (aplicada) e `IMP04823` (anulada).

### 2.3 `SV00000000841` — `stock.lot` id **10215**

| Campo | Valor |
|---|---|
| `lot_flow_type` | `volume` (etiqueta SV autorizada) · producto 166 |
| Origen | `guia_processing_id = volume_source_guia_id = 15326` (guía 4495589) · `volume_purchase_m3 = volumen_m3 = 40.315` |
| `sv_assignment_nominal_m3` | 40.315 |
| **`sv_assignment_applied_m3`** | **0.000** |
| **`sv_assignment_applied_count`** | **0** |
| `sv_assignment_documental_balance_m3` | 40.315 (**saldo intacto**) |
| Quants | 7840 = −40.315 (loc 4) · 7841 = +40.315 (loc 8) |
| `sv_assignment_sv_line_ids` (histórico) | **0** ⇒ **ninguna rebaja registrada** |

### 2.4 Otras imputaciones, bitácora y wizards

* `IMP02220` (id **1189**): `applied`, clave `IMP-1198-E95825AAF94E58AD`, guía 1198, **2 líneas**
  (`18368` 3.263 m³ + `18372` 4.225 m³), **0 repartos**, sin procesador, aplicada 2026-10-10 22:30:45 (uid 8).
  Su clave **coincide exactamente** con `_i2_build_documentary_key(guia=1198, processor=None, signature='')`
  (comprobado en este diagnóstico y ya documentado en CANON §19.22.1).
* `IMP00946` (id 492): guía 32300, `applied`, 1 línea, 1 reparto (ajena a este caso).
* **`madenat_audit_log`**: único evento de la guía 1198 = `imputation` (2026-10-10 22:30:45, `IMP02220`).
  **No hay** evento de creación ni de anulación (`imputation_cancel`) de `IMP04823`
  ⇒ su anulación (y su vaciado) **no** pasaron por el código actual.
* Wizards transitorios de rebaja (`lumber_shipment_rebaja_wizard(_line)`, `madenat_sv_rebaja_wizard`,
  `rebaja_wiz_selected_rel`): **0 filas** ⇒ la «rebaja SV00000000841» **no tiene líneas** persistidas.

---

## 3. Mapa del flujo de registro de etiquetas y sus condiciones (§3.B)

### 3.1 Del SV a la sección «Trabajo en preparación» (lo que Mauricio ve)

| Paso | Código | Observación |
|---|---|---|
| Menú «Rebaja de etiquetas» | `views/madenat_sv_imputation_views.xml:485-489` → acción `res_model=stock.lot`, dominio `[('lot_flow_type','=','volume')]` | Lista de etiquetas SV |
| Ficha del SV | `views/…:437-443` `<group string="Trabajo en preparación (no aplicado)">` → campo `sv_assignment_work_imputation_ids` + botón **`action_continue_preparation`** («Continuar») | Es la sección reportada |
| Campo | `models/madenat_sv_imputation.py:1450-1453` `One2many('madenat.sv.imputation','work_sv_lot_id', domain="[('state','in',('draft','pending'))]")` | **Dominio solo declarativo**: el ORM **no** lo aplica al leer (ver E4) |
| Contador | `…:1454-1456` + `_compute_sv_assignment_work` (`…:1558-1567`): `len(lot.sv_assignment_work_imputation_ids)` | **Cuenta lo mismo que el campo** ⇒ incluye anulados/aplicados |
| Botón | `models/…:901-919` `action_continue_preparation` → **exige** `state in ('draft','pending')`; si no, `UserError` | Con un documento anulado devuelve **error**, no «Volver a borrador» |

### 3.2 Del asistente al documento (construcción de etiquetas)

| Paso | Código | Condición / efecto |
|---|---|---|
| Abrir con guía | `wizard:378-421` `_onchange_guia_processing_id` | Si hay **trabajo** (`_i2_find_work_for_guia`, draft/pending) lo reutiliza y reconstruye sus líneas; si no, lista **todas** las candidatas con **`selected=False`** (no se incluye nada por defecto) |
| Candidatas | `wizard:423-425` `_i2_processed_lots` → `guia.lot_ids.filtered(lambda l: l.lot_flow_type != 'volume')` | **17** en la guía 1198 (los NULL entran) |
| Firma | `wizard:586-594` `_i2_signature` → `'|'.join('%s:%s:%.3f' % (lote, SV, volumen))` **solo de los repartos** | **La selección de etiquetas NO influye** en la firma ni en la clave (F1) |
| Clave | `models/…:445-452` `IMP-<guia>-sha256('I2\|guia\|processor\|signature')[:16]` · `_sql_constraints` `models/…:196-200` (**UNIQUE**) | Dos operaciones distintas sin reparto comparten clave |
| Reutilización | `models/…:462-480` `_i2_get_or_create`: (1) trabajo draft/pending; (2) **búsqueda por clave SIN filtro de estado**; (3) `create` | Devuelve documentos **aplicados/anulados** con la misma clave |
| Guardar borrador | `wizard:757-761` `action_prepare` → `_i2_guarded_build` (`:740`) → `_i2_build_imputation` (`:602-717`) | Exige `state in draft/pending`; si el documento es `cancelled` → «…fue anulado. Vuelve a borrador…»; si es `applied` → «…ya no admite preparación (estado applied)» |
| Qué se persiste | `wizard:596-600` `_i2_included_lines` = líneas **`selected` O con reparto**; `:669-714` upsert; `:715-717` **borra** las líneas no incluidas | **No exige mínimo de líneas** ⇒ documento vacío permitido (F3) |
| Repartos | `wizard:690-712` (SAVE-05) | Una fila con cantidad **0** **no** se persiste (pero **sí** entra en la firma) |
| Aplicar | `models/…:640-676` | Exige **≥1 etiqueta** y **≥1 reparto > 0** a un SV `volume`; además techo duro por etiqueta (`:707`) y permisos Operaciones/Jefatura (`:756`) |
| Anular | `models/…:789-806` | Exige draft/pending; escribe metadata + mensaje + `_i2_audit('imputation_cancel')`; **no** limpia `work_sv_lot_id` ⇒ el anulado **sigue** vinculado al SV |
| Reabrir | `models/…:819-…` `_i2_validate_reopen` · `:863` `action_reopen_to_draft` | `cancelled → draft` con permiso, motivo, guía elegible, sin otro trabajo activo y **capacidad** (RESET, 18.0.1.21.0) |

---

## 4. Reproducción controlada (§3.C) — todo con `env.cr.rollback()`

Scripts: `evidence/repro_1…repro_7` · salida literal: `logs/reproduccion.log` · baseline: `logs/baseline.log`
Entorno de ejecución: `odoo shell -d madenat_test --no-http` (lectura + transacción revertida; **nunca** `commit`).

| Esc. | Escenario | Resultado observado | Lectura |
|---|---|---|---|
| **E1** | Abrir el asistente para **guía 1198** + SV 10215 (operación nueva) | **17 líneas** candidatas, **0 seleccionadas**; «Guardar borrador» ⇒ `UserError: «La imputación IMP02220 ya no admite preparación (estado applied)»` | La clave calculada **sin reparto** es la de `IMP02220` (aplicada) ⇒ **F1** |
| **E2** | `_i2_get_or_create(guia=1198, processor=None, signature='')` | Devuelve **`1189` = `IMP02220`** (`applied`) | El «get_or_create» **adopta un documento aplicado** |
| **E3** | Clave de `(1198, None, '')` vs claves existentes | `(1198,None,'')` → `IMP-1198-E95825AAF94E58AD` = **`IMP02220`**; la de `IMP04823` (`A87816E2021EC9AA`) **no se recalcula** con el código actual | Seleccionar etiquetas **no** cambia la clave; la de `IMP04823` se generó con **firma no vacía** de cantidad 0 |
| **E4** | Lectura del campo de la sección: `lot.sv_assignment_work_imputation_ids` / `sv_assignment_work_count` (SV 10215) | **`[2733]`** y **`count = 1`** con dominio declarado `state in ('draft','pending')` ⇒ el documento **anulado se lista y se cuenta** | **F2** demostrado en el **ORM** |
| **E5** | Caso con **destino SV cantidad 0** (SAVE-05): 2-3 etiquetas seleccionadas + fila 0 | Firma `'18368:10215:0.000'` ⇒ **clave nueva** ⇒ documento **nuevo** (`IMP11716` en la última pasada; el id varía por ejecución) **con 2-3 líneas** y **0 repartos** ⇒ y el contador del SV pasa a **2** (nuevo + anulado) | Perfil exacto de `IMP04823` + F2 (cuenta lo no-trabajo) |
| **E6** | Vaciado: sobre ese documento, quitar el reparto 0 y **desmarcar** las etiquetas ⇒ Guardar | `LINEAS tras guardar: 0` (**documento vacío**), sigue `draft`, sigue en la sección del SV | **F3**: se puede dejar/persistir un documento vacío **sin aviso** |
| **E7** | **Caso sano**: 1 etiqueta seleccionada + destino SV con cantidad `1.781` (> 0) | Líneas **1**, repartos **1**, `action_apply` ⇒ **`applied`** con firma SHA-256; el SV muestra la asignación y `Rebajado documental = 1.781` | **El registro de etiquetas funciona** cuando hay selección + reparto > 0 |
| **E8** | Control negativo: intentar imputar otra vez la etiqueta `D7632` (ya consumida por `IMP02220`) | `UserError: Techo duro… acumula 6.526 m³ frente a 3.263 m³ (D-I2-16a)` | Las guardas de capacidad **sí** funcionan (no es un fallo del flujo) |

**Rollback verificado tras cada escenario** (mismos conteos y misma huella de WIP; ver §7). No se creó ningún
registro persistente; `IMP04823` / `IMP02220` nunca se abrieron en modo escritura.

---

## 5. Causa raíz y clasificación (§3.D)

### 5.1 Causa raíz demostrada

**F1 — Colisión de clave documental (bloquea el guardado de la rebaja de la guía 1198).**
La clave se compone con `(guía, procesador, firma)` y la **firma solo contiene los repartos SV**
(`_i2_signature`), no las etiquetas **seleccionadas**. Como `_i2_get_or_create` busca por clave **sin filtrar
estado** y `documentary_key` es **UNIQUE**, cualquier preparación de la guía 1198 **sin reparto** apunta al
documento **aplicado** `IMP02220` ⇒ `UserError: «La imputación IMP02220 ya no admite preparación (estado
applied)»` ⇒ **no se registra ninguna etiqueta**. *Evidencia:* E1, E2, E3 + `models/…:445,462,196` + `wizard:586`.

**F2 — Filtro de estado solo declarativo en la sección del SV.**
`sv_assignment_work_imputation_ids` declara `domain="[('state','in',('draft','pending'))]"`, pero el ORM **no
aplica el `domain` de un `One2many` al leer** (E4: devuelve el documento `cancelled`); el contador
`sv_assignment_work_count` se calcula **con ese mismo campo** ⇒ cuenta anulados (y aplicados, E5: llegó a 2).
El botón «Continuar» existe pero **falla** en ese estado (`action_continue_preparation` exige draft/pending).
*Evidencia:* `models/…:1450-1456,1558-1567,901-919` + E4/E5. *(El cliente web renderiza la lista embebida con
los registros leídos del servidor —el `domain` del campo se aplica a la relación/diálogo—, coherente con lo
observado por Mauricio: **aparece** con `Continuar`. Verificación en navegador: pendiente, VIEW-01/04.)*

**F3 — «Guardar borrador» permite documentos sin etiquetas.**
`_i2_build_imputation` **no** exige ≥1 línea incluida (solo `action_apply` exige ≥1 etiqueta y ≥1 reparto > 0);
`_i2_included_lines` = `selected or sv_alloc_ids`, y las candidatas se abren con `selected=False`. Guardar sin
seleccionar ⇒ documento **vacío** persistido **con** `work_sv_lot_id` y **sin aviso**; guardar desmarcando lo
ya registrado ⇒ **borra** las líneas (`:715-717`). *Evidencia:* E6 + `wizard:596,602-717` vs `models/…:640`.

**Dato de origen (no defecto del flujo):** que `IMP04823` esté **vacío y anulado** es la combinación de F3
(documento vacío admitido) con una **anulación que no pasó por el código actual** (sin `cancelled_by_id`/
`cancellation_date`/`cancellation_reason`, sin `imputation_cancel` en `madenat_audit_log`) — el mismo estado ya
se documentó el 2026-10-11 en `FASES/RESET_REBAJA_20261011/README.md` §1 y CANON §19.27 («caso A+D»).

### 5.2 ¿Regresión de una intervención reciente?

**No.** Las cinco funciones implicadas son **idénticas en HEAD y en el WIP** (`git diff` vacío para
`_i2_build_documentary_key`, `_i2_get_or_create`, `_i2_signature`, `_i2_included_lines`, `_i2_processed_lots`),
y `git log -S` las sitúa en:
`2888745` «feat(logistics): I2 imputacion documental SV por guia (AD-91)» (2026-10-02) y
`ded5e89` «…rebaja de etiquetas, H6, chatter…» (**commiteado 2026-10-15 10:55**, posterior a los hechos de
10-11/10-12). El campo de la sección y su dominio provienen de `ded5e89`; el comportamiento es **preexistente**.
Tampoco hay intervención de FASE 5–8 que toque estos puntos (los 7 commits `bfda876…677294b` no modifican estas
líneas; `git diff HEAD` de esos archivos ya estaba en el baseline de 11 entradas).

### 5.3 Hipótesis descartadas (con prueba)

| Hipótesis | Veredicto | Prueba |
|---|---|---|
| «El dominio está mal escrito y por eso entra la anulada» | **Descartada** (parcial) | El dominio es correcto; **no lo evalúa** el servidor: `domain` declarado vs. `[2733]` devuelto (E4) |
| «La guía no tiene lotes con saldo ⇒ no hay nada que registrar» | **Descartada** | 17 candidatas con volumen; en el caso sano se registran (E5/E7) |
| «Falta el procesador y por eso no se registra» | **Descartada** | Sin procesador se llega al guardado; el bloqueo es de **estado** (E1) |
| «Una intervención reciente rompió la clave» | **Descartada** | HEAD ≡ WIP en esas funciones; receta de clave idéntica desde el 10-02 (5.2) |
| «El asistente reutiliza el documento anulado» | **Descartada** como causa actual | Con la clave de `IMP04823` no se reutiliza (no se recalcula); la colisión **real** es con el **aplicado** (E3) |
| «Los repartos se borraron por el guardado» | **Descartada** (en el caso sano) | Al reabrir, el asistente reconstruye las líneas **seleccionadas** y el guardado las conserva (E5/E6) |

---

## 6. Propuesta de solución MÍNIMA (sin implementar) — §4.5

> Nada de esto se ha aplicado. Requiere aprobación de Mauricio. Orden sugerido: **S2** (visual, riesgo bajo) →
> **S1** (causa raíz, riesgo medio, exige tests) → **S3** (defensivo, riesgo bajo).

### S2 — Que «Trabajo en preparación» solo muestre y cuente trabajo (F2)

1. `models/madenat_sv_imputation.py` · `_compute_sv_assignment_work` (`:1559-1567`): sustituir
   `len(lot.sv_assignment_work_imputation_ids)` por
   `search_count([('work_sv_lot_id','=',lot.id),('state','in',('draft','pending'))])`
   (respetando compañía/ACL; sin `sudo`).
2. `models/…:1450-1453` (`sv_assignment_work_imputation_ids`): hacer el filtro **efectivo en el servidor**
   (campo computado `store=False` con `search([...])`, en línea con `_compute_sv_assignment_live`), **o** dejar
   el O2M y añadir el filtro del punto 1 allí donde se consume (contador y acciones).
3. `models/…:901-919` (`action_continue_preparation`): si el estado no es trabajo, devolver una **notificación
   operativa** con la acción disponible (`cancelled` → `action_reopen_to_draft`; `applied/reversed` → abrir el
   documento), en lugar del `UserError` genérico.
*Riesgo:* bajo. *Pruebas:* T2, T3 (abajo).

### S1 — Que la clave documental identifique la operación real (F1 · causa raíz)

1. `wizards/madenat_sv_imputation_wizard.py:586-594` (`_i2_signature`): incluir también **las etiquetas
   incluidas** (`_i2_included_lines()` ordenadas por `processed_lot_id`) además de los repartos ⇒ la clave
   distingue «qué etiquetas se están registrando», no solo «a qué SV».
2. `models/…:462-480` (`_i2_get_or_create`): acotar la reutilización a **trabajo** (`_i2_find_work_for_guia` ya
   lo hace) y **no** devolver documentos en `applied/reversed/cancelled` por coincidencia de clave: si la clave
   está tomada por un documento no-trabajo, la operación es **nueva** ⇒ construir la clave con el
   discriminador del punto 1 (que diferirá si cambió la selección). *(No tocar la clave de los documentos
   existentes: no hay migración de datos; `documentary_key` sigue siendo UNIQUE.)*
3. Opcional (compatibilidad UX): cuando la clave ampliada **sí** coincida con un documento histórico y este sea
   `cancelled`, ofrecer «Volver a borrador» (ya existe `action_reopen_to_draft`, RESET 18.0.1.21.0).
*Riesgo:* **medio**. Consecuencias a cubrir con tests: (a) un reintento legítimo del **mismo** documento en
borrador sigue siendo idempotente (lo garantiza `_i2_find_work_for_guia`); (b) no se crean documentos
duplicados para una misma operación; (c) las claves históricas se conservan y siguen siendo consultables.
*Pruebas:* T1, T4, T5.

### S3 — No persistir/borrar en silencio un documento vacío (F3)

`wizards/…:602-717` (`_i2_build_imputation`): si `_i2_included_lines()` está **vacío**, o bien exigir al menos
una etiqueta (mensaje claro «Seleccione las etiquetas que forman parte de la rebaja o asigne un destino SV»), o
bien exigir confirmación/motivo explícito cuando el documento ya tiene líneas (evita el **borrado silencioso**
de `:715-717`). *Riesgo:* bajo (puede afectar a un caso de uso legítimo de «reservar sin etiquetas», que hoy no
reserva nada porque la capacidad se toma de las líneas).
*Pruebas:* T6.

### Pruebas necesarias (ninguna ejecutada; propuesta)

| ID | Prueba | Esperado |
|---|---|---|
| T1 | Guía con documento **aplicado** previo + preparación **sin reparto** con etiquetas nuevas | Se **crea** documento nuevo y **registra** las etiquetas (no adopta el aplicado) |
| T2 | SV con documento **anulado** vinculado (`work_sv_lot_id`) | La sección y el contador **no** lo muestran (filtro en servidor) |
| T3 | `action_continue_preparation` sobre `cancelled` | Mensaje operativo con ruta a «Volver a borrador» (sin `UserError`) |
| T4 | Reintento del mismo borrador (misma selección/reparto) | **Idempotente**: mismo documento, sin duplicar líneas ni repartos |
| T5 | Preparación con **conjuntos distintos** de etiquetas para la misma guía | Claves distintas ⇒ documentos distintos, sin colisión |
| T6 | Guardar sin ninguna etiqueta incluida / desmarcando todo | Aviso o exigencia de motivo; **no** borrado silencioso |
| T7 | Regresión de las suites I2/RESET (`/madenat_lumber_logistics:TestSvRebaja*`, `test_sv_rebaja_reset`) | 0 failed (las claves y los escenarios existentes siguen verdes) |

---

## 7. Evidencia de que nada cambió (§4.7)

```
# Repositorio (custom_addons/)
rama   = feat/guia-correccion-documental-preservada-20261002
HEAD   = 677294b7cdc3e0cfbe1cdaef441efcb2234f8681
git status --porcelain → 11 entradas   (inicial = 11)
git stash list → 0
sha256(WIP 11 archivos) = 90d42406807ce615cd9f48abbe5fd22e823f44f8d8381cce230027a0810f1b22
                          == inicial (diff vacío, byte a byte)

# Base de datos madenat_test
guia=13 recep=8 users=12 lots=151 audit=327 imput=3 lineas=3 repartos=1
IMP02220 (1189): applied, 2 líneas, 0 repartos, write_date = create_date (2026-10-10 22:30:45)  [intacta]
IMP04823 (2733): cancelled, 0 líneas, 0 repartos, clave IMP-1198-A87816E2021EC9AA,
                 write_date = 2026-10-12 19:43:36.45072                                              [intacta]
stock.lot 10215: quants 7840=-40.3150, 7841=+40.3150 · sv_assignment_applied_m3=0.000            [intactos]
```

* Todos los escenarios de §4 corrieron con `env.cr.rollback()` y **nunca** `commit` ⇒ **cero residuos**
  (los conteos y la huella de WIP del baseline se reprodujeron **después** de cada ejecución).
* **Sin** `-u`, sin `--test-enable`, sin escrituras de negocio, sin SQL de escritura, sin tocar vistas/ACL/
  secuencias/parámetros. Ninguna consulta `UPDATE/DELETE/INSERT` fuera de la transacción revertida.
* Este informe y sus anexos se crean en `DIAGNOSTICO_REBAJA_SV841_REGISTRO_ETIQUETAS_20261015/`, **fuera** del
  repositorio git (`custom_addons/`), por lo que `git status` sigue con **11 entradas**.

---

## 8. Anexo — cómo reproducir (comandos exactos)

```bash
# 1) Datos (solo lectura)
docker exec odoo18_db psql -U odoo -d madenat_test -x \
  -c "SELECT id,name,state,documentary_key,guia_processing_id,work_sv_lot_id,\
      cancelled_by_id,cancellation_date,create_date,write_date FROM madenat_sv_imputation WHERE id IN (1189,2733)"

# 2) Reproducción controlada (transacción revertida; NUNCA commit)
docker exec -i odoo18_app odoo shell -d madenat_test --no-http < evidence/repro_1_abrir_y_guardar_sin_seleccion.py
docker exec -i odoo18_app odoo shell -d madenat_test --no-http < evidence/repro_2_lectura_campo_claves.py
docker exec -i odoo18_app odoo shell -d madenat_test --no-http < evidence/repro_3_clave_y_get_or_create.py
docker exec -i odoo18_app odoo shell -d madenat_test --no-http < evidence/repro_4_cantidad0_perfil_y_seccion.py
docker exec -i odoo18_app odoo shell -d madenat_test --no-http < evidence/repro_5_vaciado_documento.py
docker exec -i odoo18_app odoo shell -d madenat_test --no-http < evidence/repro_6_caso_sano_apply.py

# 3) Baseline (antes y después)
cd custom_addons && git status --porcelain | wc -l && git rev-parse HEAD
```

**Archivos de evidencia:** `evidence/repro_1…repro_7*.py` (scripts ejecutados) · `logs/reproduccion.log`
(salida literal de los 7) · `logs/baseline.log` (baseline del repositorio y de la base).
Correspondencia con los escenarios de §4: repro_1→E1 · repro_2→E4 · repro_3→E2/E3 · repro_4→E5 · repro_5→E6 ·
repro_6→E7 · repro_7→E8 (control negativo del techo duro).

---

## 9. Cierre (criterio de la solicitud)

| Criterio | Estado |
|---|---|
| Causa demostrada con datos y código (no supuesta) | ✅ F1/F2/F3 con reproducción E1–E6 y referencias `archivo:línea` |
| Se sabe si el registro funciona en un caso sano y por qué falla en este | ✅ E7 (sano: aplica y persiste) vs E1/E6 (caso reportado) |
| Solución mínima propuesta y lista para aprobación | ✅ §6 (S1/S2/S3 + T1–T7), **sin implementar** |
| Cero cambios en datos, código y repositorio | ✅ §7 (11 entradas, huella WIP idéntica, conteos idénticos) |
| Sin commit / push / despliegue / `-u all` / remoto | ✅ |

