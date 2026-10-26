# FASE 8 — CIERRE DE LA INSTALACIÓN DESDE CERO DE LOGISTICS Y PRUEBA `-u` LIMPIA — INFORME

**Proyecto:** MADENAT — Odoo 18 CE · **Fecha:** 2026-10-15
**Repo:** `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons` · **Rama:**
`feat/guia-correccion-documental-preservada-20261002`
**HEAD inicial:** `2985768` · **HEAD final:** `677294b`
**Expediente (fuera del repo):** `FASE8_CIERRE_DR_20261015/`
**Entorno:** LOCAL (repo + bases locales). **Nada se ejecutó contra el remoto.**

**Resultado en una línea:** con **M1** (`logistics` instala desde cero) y **M2** (prueba de longitudes en verde),
los 4 módulos **instalan desde cero** (`exit 0`) y **se actualizan por `-u`** desde un estado anterior, con
**0 fallas nuevas atribuibles** ⇒ **DR demostrada** y HEAD **autosuficiente y actualizable**.

---

## 1. BASELINE Y RESPALDO (A1)

| Dato | Valor |
|---|---|
| `git status` inicial | **11 entradas** (10 de `costing` + el menú de `reports`) |
| HEAD / rama | `2985768930957e51069d6b7828b7361c273c0c45` / `feat/guia-correccion-documental-preservada-20261002` |
| SHA256 del WIP | 11 archivos → huella `8b2243257fd5…` |
| `madenat_test` (solo lectura) | guías **13** · recepciones **8** · usuarios **12** · lotes **151** · bitácora **327** · imputaciones **3** |
| Respaldo `pre/` | tar del árbol (`gzip -t` OK), `wip_tracked_HEAD.diff`, `repo_history_before.bundle`, `madenat_test_pre_fase8.dump`, `SHA256SUMS.txt` |

---

## 2. INVESTIGACIÓN M1 Y ALTERNATIVA ELEGIDA

**Hechos.** En `madenat_lumber_logistics/views/madenat_sv_imputation_views.xml` había **un solo**
`<record id="menu_madenat_sv_imputation" model="ir.ui.menu">` con `active=False` y **sin `name`**; su
`<menuitem>` (name «Imputaciones documentales SV», `parent=menu_lumber_logistics`,
`action=action_madenat_sv_imputation`, `sequence=19`) fue **retirado** en `ded5e89`.

**Evidencia de la intención (documental):**
* `FASES/UNIFY_SV_REBAJA_MENU_20261010/README.md`: «Menú `menu_madenat_sv_imputation`: **retirado de navegación**
  (`active=False`, **`record` posterior al `menuitem`** ⇒ no reaparece al reaplicar `-u`; reversible)»;
  «Menú retirado: `menu_madenat_sv_imputation` (id 542) → `ir.ui.menu.active = False`»; y «**Recuperación de
  navegación:** poner `active=True` en `menu_madenat_sv_imputation` y volver a `-u`».
* `CANON/02` §17.x: «menú … **retirado de navegación**»; `CANON/03` (NAV-02): «542 inactivo «Imputaciones
  documentales SV»; **acción 867 preservada**».
* Quién lo referencia: **solo** el propio record y el test `test_sv_rebaja_navigation.py:57`
  (`env.ref(...menu_madenat_sv_imputation)`) ⇒ el registro **debe existir**; la acción
  `action_madenat_sv_imputation` y el padre `menu_lumber_logistics` **existen** (mismo archivo y
  `logistics_menus.xml:10`).

**Alternativas y elección.** (a) **restituir el `<menuitem>`** conservando name/parent/action/sequence;
(b) eliminar el record huérfano; (c) añadir solo `<field name="name">`. Se elige **(a)** por ser la **mínima
coherente con la intención DOCUMENTADA** (el expediente describe exactamente ese mecanismo
`menuitem` + `record` posterior), porque mantiene el menú **existente e inactivo** y porque, además, deja
operativa la **recuperación documentada** (`active=True` + `-u`) **también en una instalación limpia** (con
(b) o (c) el menú no tendría padre/acción en un alta nueva).

**Barrido de la clase M1** (todos los módulos instalables, excluyendo comentarios XML e ids de otros módulos):
**0 casos restantes**. Los hallazgos aparentes eran `menu_shipping_*` y `menu_r*` **comentados** en el XML, y
`account.menu_finance` / `mail.channel_menu_root` (ids **de otros módulos**, es decir *updates*).

---

## 3. COMMITS DE CIERRE (3)

| # | Hash | Tipo/módulo | Archivos | Versión | Contenido |
|---|---|---|---|---|---|
| 1 | `7d277e9` | `fix(logistics)` | 3 | **18.0.1.28.0 → 18.0.1.29.0** | **M1**: `<menuitem>` restituido (+5 líneas) + manifest + CHANGELOG |
| 2 | `7c417ae` | `test(core)` | 1 | 18.0.6.9.0 (sin cambio, justificado) | **M2**: `product.product` en el helper (2 líneas, solo test) |
| 3 | `677294b` | `docs(canon)` | 3 | 04 **12.24.0** · 05 **8.29.0** · INDICE **12.35.0** | **AD-108** (M1/M2, método, resultados, D1) |

**Diffs exactos:** M1 = `+5` líneas (el `<menuitem>` con sus 5 atributos originales, antes del `<record>`);
M2 = `-self.Product = self.env['product.template']` / `+self.env['product.product']` y el texto de la aserción.
**Únicos cambios de contenido nuevos** de la fase (el resto es versión/CHANGELOG/documentación).

---

## 4. VERIFICACIÓN — A) INSTALACIÓN DESDE CERO

Clon `--no-hardlinks` (`git apply` de M1+M2 sobre HEAD; sin el WIP de `costing` ni el menú de `reports`), copiado
al contenedor y usado como `--addons-path` (junto al core de Odoo, **sin** el `custom_addons` de trabajo). Base
temporal `madenat_dr_check_test`, puerto 9995.

**Paso 1 — INSTALABILIDAD (sin `--test-enable`):** `-i shipping_core,core,logistics,intake` ⇒ **`exit 0`**.

| Orden | Módulo | ¿Instala? | Evidencia |
|---|---|---|---|
| 26/71 | `madenat_lumber_shipping_core` | **SÍ** | `loaded in 0.64s` |
| 58/71 | `madenat_lumber_core` | **SÍ** | `loaded in 3.76s, 2679 queries` |
| 65-68/71 | `ingestion_engine`, `purchasing`, `reception_improvements` | **SÍ** | `loaded` |
| **69/71** | **`madenat_lumber_logistics`** | **SÍ** (antes fallaba) | `loaded in 4.70s, 1996 queries` |
| 70-71/71 | `toll_processing`, **`madenat_lumber_intake`** | **SÍ** | `loaded` |

⇒ **M1 confirmado**: el `NotNullViolation … ir_ui_menu` de la FASE 7 **desaparece** y **la reconstrucción desde
cero (DR) queda DEMOSTRADA** para los 4 módulos.

**Paso 2a:** `-i madenat_lumber_billing` (depende de `core`+`logistics`, **no** de `costing`) ⇒ `exit 0`, para
evitar artefactos de alcance en las suites.

**Paso 2b — SUITES** (`-u` de los 4 módulos + `--test-enable --test-tags=/madenat_lumber_core,/madenat_lumber_intake,/madenat_lumber_logistics`):
`Registry loaded in 20.989s` y **`3 failed + 47 error de 1314`**.

| Causa (A) | Nº | Detalle | ¿Nueva vs baseline? |
|---|---|---|---|
| `UserError: No se encontró un tipo de operación de traslado interno…` y `null value in column "picking_type_id"` | **34** | **Artefacto de alta limpia**: el asistente busca un `stock.picking.type` interno de la compañía; en la base nueva el escenario no está configurado como en `madenat_test` | No |
| `JsonRpcException / AccessError` (RPC de la consola) | **8** | Pruebas `HttpCase`/RPC (incl. `TestIntakeVolumeDeclaredGridRpc`) y las 3 `TestSvEscalationSecurity` (del baseline) | 3 del baseline + 5 artefacto |
| `null value in column "product_id"` en `madenat_guia_processing_line` | **3** | **Artefacto**: base limpia con **1 producto** frente a **20**, y sin sembrar `madenat.allow_product_creation` / `allow_subproduct_creation` | No |
| `AssertionError` de redondeo (`40.32 != 40.315`, `4.36 != 4.358`) | **2** | **Artefacto de configuración**: `decimal_precision` `Product Unit of Measure` **2 vs 4** y `Product Price` **2 vs 3** | No |
| `UserError` de picking sin cantidades reservadas (`TestGranelRouteCore.test_08`) y otros | **3** | Alta limpia / orden | No |
| `TestGuiaPickingLink.test_t_g2_03_exclusion_retornos` (FAIL) | 1 | **Está en el baseline** | No |

**M2 VERIFICADO EN VERDE:** `TestLengthUomAndSubproducto` — los **4 tests** se ejecutaron y **ninguno falló**
(en la FASE 7 el mismo caso daba `MissingError: product.product(607)`).

---

## 5. VERIFICACIÓN — B) CAMINO `-u` DESDE UN ESTADO ANTERIOR

**Dump elegido:** `backups/procesadores_guardas_20261002/madenat_test_pre_guardas.dump` (2026-10-02), verificado
**sin** la vista de `costing` con `action_apply_c2` (0 coincidencias sobre `pg_restore --data-only -t ir_ui_view`)
y por ser el **más reciente** con esa condición. Restaurado en `madenat_u_check_test` (**sin errores**;
`res_users=9`, guías 5, bitácora 243), con su filestore creado y `chown odoo:odoo`. `madenat_test` **no se tocó**.

**`-u` de los 4 módulos** (mismo `--addons-path` del clon y `--test-tags` acotado): `button_upgrade` sobre los
4, **sin errores de carga** y **`1 failed + 4 error de 1314`**.

| Falla | ¿En el baseline? | Causa |
|---|---|---|
| `TestGuiaPickingLink.test_t_g2_03_exclusion_retornos` | **SÍ** | Preexistente |
| `TestSvEscalationSecurity.test_02/03/04` | **SÍ** | Preexistentes |
| `TestServiceReturnImputationGuard.test_09_cristhian_aplica_revierte_y_cambia_no` | No | **Dependiente de datos del dump**: el usuario real Cristhian existe pero **no** tiene Jefatura/Gerencia en ese estado ⇒ `AccessError: Solo Jefatura de Operaciones o Gerencia pueden reversar…` |

**Comparación por nombre A∩B:** **4 fallas del baseline**. **45 fallas aparecen solo en A** (base sin
datos/configuración) y **1 solo en B** (datos del dump) ⇒ **0 fallas nuevas atribuibles a M1/M2 ni al código
entregado**.

---

## 6. FICHA M5 — D1 `costing` (solo lectura)

| Aspecto | Hecho |
|---|---|
| Archivos del WIP | `models/lumber_cost_distribution.py` (+377), `models/lumber_shipment_costing.py` (+400); **nuevos** `models/stock_lot_cost_line.py`, `views/lumber_shipment_costing_views.xml`, `tests/test_shipment_costing_c2.py`; `views/lumber_cost_distribution_views.xml` (+54), `security/ir.model.access.csv` (+16), `models/__init__.py`, `tests/__init__.py`, `__manifest__.py` (+1) |
| Versión | `18.0.1.0.0` **en HEAD y en el WIP** (sin subir) · CHANGELOG **sin entrada** del C2 |
| `action_apply_c2` | **HEAD:** vista 0 / método 0. **WIP:** vista 1 / método 1 (`def action_apply_c2` en `lumber_cost_distribution.py:349`) |
| Coherencia | **HEAD y WIP son coherentes por separado**; lo que rompe es la **mezcla** (vista-WIP guardada en la BD + código HEAD) ⇒ `ParseError` al re-validar en un `-u` (FASE 7) |
| Atribución | WIP datado 2026-10-03/04; expedientes `AUDIT_COSTING_20261004`, `UAT_COSTING_C2_20261004`; `CANON/08_COSTEO.md` |
| Dependencias | **`madenat_lumber_reports` depende de `costing`** (por eso `reports` no puede instalarse ni actualizarse sin resolverlo); `billing` y `vendor_payment` **no** dependen |
| **Recomendación (`REQUIERE_DECISIÓN`)** | (a) **commitear** con versión + CHANGELOG y desplegar con `reports`; (b) **mantenerlo fuera** (estado actual: HEAD coherente y desplegable sin `reports`); (c) **revertir el WIP en la base local**. **No ejecutado.** |

---

## 7. HALLAZGOS, RIESGOS Y VALIDACIÓN

1. **Configuración no sembrada en el alta limpia (nuevo):** una base nueva **no** reproduce la de
   `madenat_test` (precisión decimal, catálogo de productos, parámetros `madenat.*`). Explica la mayor parte de
   las fallas «solo en A». **Declarar el juego mínimo de configuración** para altas/DR (si no, los cálculos y
   varias suites diferirán en el destino).
2. **Prueba dependiente de datos:** `TestServiceReturnImputationGuard.test_09…` exige que el usuario real
   Cristhian tenga Jefatura.
3. **D1 `costing`** y **P2-2** (menú de `reports`) siguen **fuera** por decisión.
4. **VIEW-01/04 en navegador:** pendiente de ejecución manual (checklist de la FASE 7 **reafirmada**).
5. Pendientes conocidos: trigger/hash de bitácora, suites con `commit()` (D5), 10 fallas preexistentes (D10),
   commit ⑦ del expediente de auditoría.

| Validación final | Resultado |
|---|---|
| `git status` inicial → final | **11 → 11** (los mismos 10 de `costing` + el menú de `reports`) |
| Hashes de esos 11 | **0 cambios** |
| Entradas finales no esperadas | **ninguna** |
| HEAD / rama / stash / reflog | `677294b` / misma rama / vacío / **solo 3 `commit`** (sin amend/reset) |
| `madenat_test` | **sin cambios**: 13/8/12/151/327/3 |
| Bases y clones temporales | **eliminados** (0 bases `*_check_test`, clones host y contenedor) |
| Remoto | **no contactado** (sin fetch/push) |

---

## 8. PRERREQUISITOS RESTANTES PARA EL TEST REMOTO (sin ejecutarlo)

1. **Verificar §3.8 del runbook** en el destino (vistas con métodos ausentes del código a entregar) y decidir
   **D1** si aplica.
2. **Declarar el juego mínimo de configuración** (precisión decimal, parámetros `madenat.*`) para el entorno de
   destino — hallazgo de esta fase.
3. Respaldo remoto (dump + filestore + código) verificado y ventana acordada.
4. Entregar los **6 commits** de las FASES 5-8 (o al menos `2985768`..`677294b`) y hacer `-u` de los 4 módulos
   en orden de `depends`, **sin** `-u all`.
5. Humo funcional §7 del runbook + **VIEW-01/04 manual** (Mauricio).
6. `P2-2` y `costing` permanecen **fuera**.


