# FASE 7 — CIERRE DE D18, REPARACIÓN DE INSTALACIÓN DESDE CERO Y RE-VERIFICACIÓN — INFORME

**Proyecto:** MADENAT — Odoo 18 CE · **Fecha:** 2026-10-15
**Repo:** `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons` · **Rama:**
`feat/guia-correccion-documental-preservada-20261002`
**HEAD inicial:** `ed42df5` · **HEAD final:** los 4 commits de cierre (ver §2)
**Expediente (fuera del repo):** `FASE7_CIERRE_D18_20261015/`
**Entorno:** LOCAL (repo + bases locales). **Nada se ejecutó contra el remoto.**

---

## 1. BASELINE Y RESPALDO PREVIO (A1)

| Dato | Valor |
|---|---|
| `git status` inicial | **16 entradas** (13 `M` + 3 `??`) |
| HEAD / rama | `ed42df54dab62beea0780337971d3657b4232ac1` / `feat/guia-correccion-documental-preservada-20261002` |
| `git stash` | vacío |
| SHA256 del WIP | 16 archivos → `pre/wip_sha256_before.txt`, huella `35e6808f91c8…` (**idéntica a la de la FASE 6** ⇒ el WIP no se movió) |
| `madenat_test` (solo lectura) | guías **13** · recepciones **8** · usuarios **12** · lotes **151** · bitácora **327** · imputaciones **3** |
| Respaldo `pre/` | tar del árbol (717 archivos, `gzip -t` OK), `wip_tracked_HEAD.diff`, `repo_history_before.bundle` (verify OK), `madenat_test_pre_fase7.dump` (11.5 MB, sin error de `pg_dump`), `SHA256SUMS.txt` |

---

## 2. COMMITS DE CIERRE (4)

| # | Hash | Tipo/módulo | Archivos | Versión | Contenido |
|---|---|---|---|---|---|
| 1 | `bfda876` | `fix(core)` | 1 | 18.0.6.9.0 (sin cambio) | **D18-1**: `tests/test_duplicate_validation.py` (contenido **idéntico** al WIP; verificado por SHA256) |
| 2 | `56405cb` | `feat(logistics)` | 6 | **18.0.1.27.0 → 18.0.1.28.0** | **D18-2/3/4/5** (contenido **idéntico** al WIP) + `__manifest__.py` (versión) + `CHANGELOG.md` (entrada 18.0.1.28.0) |
| 3 | `c4935ed` | `fix(intake)` | 1 | 18.0.0.15.0 (sin cambio) | **K2**: `views/intake_console_views.xml` — movimiento puro (+12/−12) |
| 4 | `docs(canon)` | `docs(canon)` | ver §2.1 | 04 → **12.23.0** · INDICE → **12.34.0** | **AD-107** (cierre D18, P2-2 fuera, hallazgos de instalación desde cero) |

**Sin cambios de versión en `core` e `intake` (K3):** en `core` el commit es **solo una prueba**; en `intake`
es una **reordenación de un archivo de datos ya declarado en el manifest**, que se recarga con el
`-u madenat_lumber_intake` del despliegue. En ambos casos no cambia modelo, datos, seguridad ni ACL ⇒ una
versión nueva **no es indispensable**.

**Exclusiones respetadas:** `madenat_lumber_costing` (10 archivos, D1) y
`madenat_lumber_reports/views/lumber_reports_menu.xml` (P2-2, por decisión) **no** se commitearon ni se
tocaron. El expediente de auditoría sigue fuera del repo (⑦ omitido).

---

## 3. K2 — DIFF EXACTO Y BARRIDO DE REFERENCIAS ADELANTADAS

### 3.1 Problema reproducido

`madenat_lumber_intake/views/intake_console_views.xml`: la acción se **usaba** en la línea 20 (botón
`name="%(action_madenat_lumber_intake_new)d"` dentro del `<field name="arch">` de
`view_madenat_lumber_intake_console_list`) y se **definía** en la línea 1116. Al instalar desde cero (FASE 6/V1):

```
ParseError: while parsing .../intake_console_views.xml:7, somewhere inside
ValueError: External ID not found in the system: madenat_lumber_intake.action_madenat_lumber_intake_new
```

### 3.2 Corrección aplicada (mínima)

Se **mueve** el bloque completo (comentario `ACCIÓN: NUEVO INGRESO` + `<record …>`) al inicio del archivo,
por delante de su primer uso. **Verificaciones de que es un movimiento puro:**

| Verificación | Resultado |
|---|---|
| Diff | **+12 / −12** líneas (mismo bloque movido) |
| Multiset de líneas no vacías | **idéntico** |
| Conjunto de `<record id="…">` | **idéntico** (5 ids, mismo orden) |
| XML | **bien formado** (`ElementTree`) |
| Posición definición → uso | 1116/20 ⇒ **7/32** (la definición precede al uso) |
| Ids/nombres/modelos/campos | **sin cambios** |

### 3.3 Barrido general de referencias adelantadas (todos los módulos instalables)

Script que recorre el orden de `data` de cada manifest y detecta usos (`%(id)d`, `ref="id"`, `ref('id')`)
resueltos **después** de su definición (mismo archivo o archivo posterior):

* **Antes de K2: 1** referencia adelantada en todo el repositorio (la de `intake_console_views.xml`).
* **Después de K2: 0.**

⇒ No hay más casos de esta clase. (`logistics` carga el asistente de rebaja en `data` #8 y el menú que lo
referencia en #18 ⇒ orden correcto; su ACL va en #1 y los modelos vienen de Python, cargado antes de los datos.)

---

## 4. K7 — FICHA `test_length_uom_and_subproducto` (SOLO LECTURA, sin corregir)

| Dato | Valor |
|---|---|
| Síntoma | 4 `ERROR` (`test_29`…`test_32`) **solo en instalación limpia**: `MissingError: Record does not exist or has been deleted. (Record: product.product(607,))` |
| Punto de fallo | `madenat_lumber_core/models/lumber_reception.py:258-259` → `env['product.product'].browse(vals['product_id']).name` |
| Causa raíz | El test hace `self.Product = self.env['product.template']` y `self.product = self.Product.search([], limit=1)`, y pasa **`self.product.id`** (id de **plantilla**) al campo `product_id` de `lumber.reception.line`, que es `Many2one('product.product')` (`models/mixin_lumber_ingest.py:415`). En una base limpia los espacios de id de `product_template` y `product_product` **divergen** ⇒ `browse()` apunta a una variante inexistente |
| Por qué pasa en `madenat_test` | Allí los ids coinciden para el producto que devuelve el `search`, por lo que el defecto queda **oculto** |
| ¿Lo introdujo la FASE 5/7? | **No.** El archivo del test **no** está modificado en el WIP y el comportamiento es idéntico en `b1d2d19` |
| Naturaleza | **Defecto de la prueba** (no del código de producción): mezcla `product.template` con `product.product` |
| Recomendación (`REQUIERE_DECISIÓN`) | Cambiar el helper del test a `self.env['product.product']` (o usar `self.product.product_variant_id.id`): 1–2 líneas, solo **test**. **No autorizado** en esta fase |

---

## 5. K5 — RE-VERIFICACIÓN DEL HEAD LIMPIO

### 5.0 Cambio de método (documentado)

En el primer intento se lanzó la instalación desde cero **con `--test-enable`**, y el framework arrastró los
tests de los **módulos de Odoo** (base, web, mail, product, analytic…): a los ~3.000 tests iniciados los de
MADENAT aún no habían empezado. Ese volumen no aporta evidencia sobre nuestros módulos, así que el
procedimiento se separó en **dos pasos** (documentado en `logs/k5b_interrupcion.txt`):

1. **INSTALABILIDAD** — instalación desde cero **sin `--test-enable`** (`--without-demo=all`, `--stop-after-init`,
   orden de `depends`) ⇒ demuestra DR/alta limpia sin ruido.
2. **SUITES** — ya instalada la base, `-u` de los módulos MADENAT con `--test-enable` y
   `--test-tags` **limitado a ellos** (nombres técnicos verificados en los manifests:
   `madenat_lumber_core`, `madenat_lumber_intake`, `madenat_lumber_logistics`), sin `-u all`.

Clon `--no-hardlinks` del HEAD `c4935ed` (previo al commit ④ de docs): `status = 0`, **sin el WIP de costing**
(los 3 archivos nuevos ausentes y los modificados iguales al commit) y **sin** `active="0"` en el menú de
`reports`. Base temporal `madenat_head_check2_test` (el gate `_sv_test_enable_strict()` exige «test» en el
nombre). `--addons-path` = clon + core de Odoo (**sin** el `custom_addons` de trabajo).

### 5.1 Paso 1 — INSTALABILIDAD (sin tests)

| Orden | Módulo | ¿Instala? | Evidencia |
|---|---|---|---|
| 26/71 | `madenat_lumber_shipping_core` | **SÍ** | `loaded in 0.60s, 288 queries` |
| 58/71 | `madenat_lumber_core` | **SÍ** | `loaded in 5.74s, 2679 queries` |
| 65-66/71 | `madenat_ingestion_engine`, `madenat_lumber_purchasing` | **SÍ** | `loaded` |
| **69/71** | **`madenat_lumber_logistics`** | **NO** | **`NotNullViolation: null value in column "name" of relation "ir_ui_menu"`** ⇒ `Failed to load registry` (exit 255) |
| 70/71 | `madenat_lumber_intake` | no alcanzado en ese pase | — |

**El ACL de D18 ya carga sin error** (el log pasa de `security/ir.model.access.csv` a
`madenat_sv_imputation_rules.xml`, `sequences.xml` y los datos). El fallo es **posterior y distinto**:
el `<record id="menu_madenat_sv_imputation" model="ir.ui.menu"><field name="active" eval="False"/></record>`
de `views/madenat_sv_imputation_views.xml:215` **no tiene `name`**, y el `<menuitem>` que lo definía fue
retirado en `ded5e89`. En una base **existente** el `-u` no falla (el menú ya existe), por lo que el defecto
era **latente**. *(Bloqueante abierto → AD-107 §4; su corrección queda fuera de K2, no autorizada.)*

### 5.2 Paso 2a — INSTALABILIDAD de `intake` (sin `logistics`)

`-i madenat_lumber_intake` (no depende de `logistics`): **exit 0**;
`Module madenat_lumber_intake loaded in 1.18s, 450 queries`. ⇒ **K2 verificado de extremo a extremo**: la
reordenación del bloque de la acción habilita la instalación desde cero.

### 5.3 Paso 2b — SUITES (core + intake), camino `-u`

`-u madenat_lumber_core,madenat_lumber_intake --test-enable --test-tags=/madenat_lumber_core,/madenat_lumber_intake`
⇒ actualización correcta (`Registry loaded in 15.19s`, `button_upgrade on ['MADENAT Lumber Core','MADENAT Lumber Intake']`)
y **`2 failed + 51 error de 808`**:

| Causa | Nº | Detalle | ¿Nueva vs baseline? |
|---|---|---|---|
| `KeyError: 'lumber.billing.consolidation.line'` (y 1 `'lumber.export.shipment'`) | **32** | El asistente de ciclo de vida enumera modelos por nombre y **`madenat_lumber_billing` / `madenat_lumber_logistics` no están instalados** en esta base ⇒ **artefacto de alcance** | No |
| `TestGuiaPickingLink.test_t_g2_03_exclusion_retornos` (FAIL) | 1 | **Está en el baseline** (10) | No |
| `TestSvEscalationSecurity.test_02/03/04` (ERROR) | 3 | **Están en el baseline** (10) | No |
| `TestGuiaProcessingIngestionProfileLock.test_03/04/05` | 3 | `DETAIL: Failing row contains (…)` — comportamiento de alta limpia | a revisar |
| `TestGranelRouteCore.test_08` | 1 | `UserError: You cannot validate a transfer if no quantities are reserved…` | a revisar |
| `TestIntakeVolumeDeclaredGridRpc` (5), `TestVolumeOfficialVolume.test_05` (40.32 vs 40.315) y otros | ~13 | RPC/`AccessError` y diferencia de volumen propias de base limpia | a revisar |

**D18-1 VERIFICADO EN VERDE:** `TestDuplicateValidation.test_02_homonym_guia_vs_reception` (el nombre nuevo)
**se ejecutó sin fallo** — la FASE 6 lo reproducía como `FAIL: …test_02_duplicate_in_guia_processing`. Las 8
pruebas de esa clase pasaron.

### 5.4 Camino `-u` sobre una base existente (copia de `madenat_test`)

Se creó `madenat_test_fase7_test` restaurando el **dump previo a la fase** (11.5 MB, `pg_restore` sin errores;
conteos idénticos: guías 13, bitácora 327; filestore copiado y `chown odoo:odoo`) — **`madenat_test` nunca se
modificó** (solo lectura). Resultado del `-u` de los 4 módulos: **FALLA** (`Failed to load registry`) con
`ParseError` al re-validar `madenat_lumber_costing/views/lumber_cost_distribution_views.xml` →
`action_apply_c2 no es una acción válida en lumber.cost.distribution`.

**Causa:** la BD de origen procede de la era-WIP, donde la vista de `costing` quedó guardada **con**
`action_apply_c2`, método que existe **solo** en el WIP de `costing` (**D1, no commiteado por decisión**). Al
actualizar, Odoo re-valida **todas** las vistas cargadas ⇒ cualquier `-u` sobre una base cuyo estado no
corresponda al código entregado fallará ahí. **No es un defecto del código commiteado** (la vista del HEAD no
menciona `action_apply_c2`: 0 referencias) sino de **mezclar estado-WIP con código-sin-WIP**.
⇒ **Precondición de despliegue:** comprobar en el destino que ninguna vista almacenada referencia métodos
ausentes del código a entregar (y resolver D1 o el WIP correspondiente).

### 5.5 Veredicto de K5

| Módulo | Instala desde cero | Camino `-u` | Suites | Fallas nuevas atribuibles a los commits |
|---|---|---|---|---|
| `madenat_lumber_shipping_core` | **SÍ** | **SÍ** | — | ninguna |
| `madenat_lumber_core` | **SÍ** | **SÍ** (verificado) | 808 (con intake) | **ninguna** (D18-1 en verde; 4 del baseline) |
| `madenat_lumber_intake` | **SÍ** (K2) | **SÍ** (verificado) | ídem | las de arriba (artefactos de alcance) |
| `madenat_lumber_logistics` | **NO** (menú sin `name`; bloqueante abierto) | no evaluable en base limpia | no evaluable | — |

⇒ Los 4 commits de la FASE 7 **eliminan el bloqueo de D18** y hacen reconstruibles desde cero
`shipping_core`, `core` e `intake`. La **reconstrucción total (DR) sigue pendiente** del defecto del menú de
`logistics` (hallazgo abierto, requiere decisión) y el despliegue a una base con estado-WIP requiere la
comprobación de §5.4.

---

## 6. VALIDACIÓN FINAL E INTEGRIDAD DE LA FASE

| Comprobación | Resultado |
|---|---|
| `git status` inicial → final | **16** → **11** entradas = **exactamente** los 10 de `costing` + el menú de `reports` |
| Hashes de esos 11 | **0 cambios** (comparados con el manifiesto previo) |
| Entradas finales no esperadas | **ninguna** |
| HEAD / rama | `2985768` / `feat/guia-correccion-documental-preservada-20261002` (misma rama) |
| `git stash` | vacío · **reflog: solo 4 `commit`** (sin amend/reset/checkout) |
| Archivos D18 commiteados | **idénticos** al WIP previo (SHA256 comparado antes de cada commit) |
| Cambio de contenido nuevo | **solo K2** (mostrado en §3.2) + versión/CHANGELOG de `logistics` + los 3 `.md` de docs |
| `madenat_test` | **sin cambios**: guías 13 · recepciones 8 · usuarios 12 · lotes 151 · bitácora 327 · imputaciones 3 |
| Bases temporales | **0** restantes (`madenat_head_check2_test`, `madenat_test_fase7_test` eliminadas) |
| Clones temporales | **eliminados** (host `FASE7_CIERRE_D18_20261015/clone` y contenedor `/tmp/fase7_clone`) |
| Remoto | **no contactado** (sin fetch/push/ls-remote) |

---

## 7. RIESGOS RESIDUALES Y DECISIONES PARA MAURICIO

| # | Asunto | Decisión requerida |
|---|---|---|
| 1 | **BLOQUEANTE — `logistics` no instala desde cero** (`<record model="ir.ui.menu">` sin `name` en `madenat_sv_imputation_views.xml`, introducido por `ded5e89`) | Autorizar la corrección mínima: **(a)** restituir el `<menuitem>` antes del `<record>` (lo que el comentario afirma) o **(b)** añadir `<field name="name">Imputaciones documentales SV</field>` |
| 2 | **Despliegue sobre base con estado-WIP** (`action_apply_c2` en la vista de `costing`) | Decidir D1 (`costing`) o limpiar/ajustar esa vista en el destino antes del `-u` |
| 3 | **D1 `costing`** (10 archivos) sigue fuera del historial | Mantener bloqueado (decisión vigente) |
| 4 | **P2-2** (menú de `reports`) | Fuera por decisión; se reabre solo con decisión expresa |
| 5 | **K7** `test_length_uom_and_subproducto` (`product.template` vs `product.product`) | Autorizar el arreglo de la prueba (1–2 líneas, solo test) |
| 6 | **3 fallas de alta limpia a revisar** (`TestGuiaProcessingIngestionProfileLock.test_03/04/05`, `TestGranelRouteCore.test_08`, `TestVolumeOfficialVolume.test_05`) | Decidir si se investigan (no bloquean: no aparecen en el camino `-u` de `madenat_test`) |
| 7 | **VIEW-01/04 en navegador** | Pendiente de ejecución manual (checklist entregada) |
| 8 | Trigger/hash de bitácora · suites con `commit()` (D5) · 10 fallas preexistentes (D10) · commit ⑦ del expediente | Pendientes ya conocidos |

---

## 8. PROPUESTA DE COMMITS DE CIERRE (**NO ejecutada**)

1. **`fix(logistics): define el nombre del menú de imputaciones antes de inactivarlo (instalación desde cero)`**
   * `madenat_lumber_logistics/views/madenat_sv_imputation_views.xml` (opción (a) o (b) de §7-1; cambio mínimo)
   * Desbloquea la **instalación desde cero / DR** y cierra el último bloqueante detectado.
2. **`fix(core): usa product.product en el helper de la prueba de longitudes (K7)`**
   * `madenat_lumber_core/tests/test_length_uom_and_subproducto.py` *(si se aprueba)*
3. **`docs(canon): AD-108 — cierre de instalación desde cero y reconciliación de costing`**
   * `04` (versión monótona), `INDICE`, `05` según lo decidido en §7-1/§7-2.
4. **Commit ⑦ (expediente de auditoría)**: sigue **fuera del repo** (177 MB); decisión aparte.




