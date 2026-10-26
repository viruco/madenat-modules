# INFORME FRENTE B — RECLASIFICAR TIPO DE INGRESO
### Auditoría técnica de solo lectura · MADENAT · Odoo 18 CE

| Dato | Valor |
|---|---|
| Fecha | 2026-10-23 |
| Objeto de estudio | `madenat.lumber.intake.reclassify.wizard` (AD-73) y sus dos modelos destino |
| Código del wizard | `madenat_lumber_intake/models/intake_reclassify_wizard.py` (153 líneas) |
| Vista | `madenat_lumber_intake/views/intake_reclassify_wizard_views.xml` (37 líneas) |
| Botones que lo abren | `intake_guia_processing_facade_views.xml:48-52`, `intake_reception_facade_views.xml:48-52`, `intake_console_views.xml:102-106` |
| Núcleo implicado (solo lectura) | `madenat_guia_processing.py:6699-6768` (`unlink`), `lumber_reception.py:3210-3252` (`unlink`) |
| Workspace | `/home/viruco/dev-stack/odoo/odoo-18-ce` (no es repo git) |
| Repo git real | `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons` — HEAD `e672fc4` |
| Base de datos | `madenat_test` (contenedor `odoo18_db`), acceso **solo SELECT** |
| Tests existentes | `madenat_lumber_intake/tests/test_intake_reclassify.py` (7 casos) |

**Reglas aplicadas:** toda afirmación lleva `[VERIFICADO]`, `[HIPÓTESIS]` o `[NO VERIFICABLE]`.
No se modificó ningún archivo de código, vista, dato ni manifiesto; no se ejecutaron upgrades, tests ni reinicios.
Las únicas escrituras son este informe y `INFORME_FRENTE_A.md`.

**Índice:** B0 · B1 · B2 · B3 · B4 · B5 · B6 · B7 · B8 · B9 · B10 · Cierre.

**Correspondencia hallazgo → sección** (los `B-n` son estables y no siguen el orden de lectura):

| Hallazgo | Se desarrolla en |
|---|---|
| B-1 | B2.1 / B2 (ruta Procesado → Producto) |
| B-2 | B2 (auditoría `cascade`) / B5.1 / B7.1 |
| B-3 | B2 (grupos y ACL) |
| B-4 | B10 / B3 (destino `granel`) |
| B-5 | B3 (ruta Producto → Procesado) / B4 |
| B-6 | B4 (`_check_no_lots`) |
| B-7 | B8 (fotografía de la base) |
| B-8 | B2 (orden de las guardas) |
| B2.2 | B2.2 (asimetría de blindaje guía vs. recepción) |

---

## B0 — Resumen ejecutivo

| # | Hallazgo | Evidencia | Severidad |
|---|---|---|---|
| **B-1** | **Ninguna de las 13 guías de la base es reclasificable**: las 4 `verified` mueren en `unlink` (sólo acepta `draft`/`cancelled`) y la única `draft` (32300) muere en `_check_no_lots` porque tiene un lote en `lot_ids` | `intake_reclassify_wizard.py:67,83` vs `madenat_guia_processing.py:6712` + consulta BD | 🔴 Bloqueante |
| **B-2** | **La evidencia de auditoría de la ruta Producto se autodestruye**: el evento se crea con `reception_id` y esa FK es `ON DELETE CASCADE` en la BD; al borrar la recepción, el evento desaparece | `:131` + `madenat_audit_log.py:48` + `pg_constraint.confdeltype='c'` | 🔴 Bloqueante |
| **B-3** | **Ningún rol cubre las dos rutas**: guía exige `Jefatura de Operaciones` (único grupo con `unlink`), recepción exige `MADENAT: Compras y Operaciones`; ese grupo **no** implica `Operaciones`, que es el que puede crear el wizard. Sólo **2 de 5** usuarios activos acumulan los tres grupos | `ir_model_access` (BD) + `res_groups_implied_rel` | 🟠 Alta |
| **B-4** | **`granel` es un destino ofrecido que no rutea**: el wizard nuevo nace con `intake_modality='normal'` y `tipo_ingreso='granel'`, combinación que termina en `UserError` | `:31` vs `intake_wizard.py:94-106`, `:697-710` | 🟠 Alta |
| **B-5** | **La reclasificación no corrige el tipo: destruye el registro y obliga a rehacerlo.** Se pierden líneas, patio, perfil, proveedor, OC, tipo de cambio y la lectura del documento | `:143-145` (sólo `tipo_ingreso`) | 🟠 Alta |
| **B-6** | **Las dos relaciones de lotes no coinciden**: `_check_no_lots` sólo mira el M2M `lot_ids`/`source_lot_ids`, el núcleo sólo mira la FK inversa `guia_processing_id`. Guía 32411: 2 lotes por FK inversa, 0 en `lot_ids` (el wizard dice «no hay lotes»); guía 32300: 0 por FK inversa, 1 en `lot_ids` (el wizard la bloquea aunque el núcleo no vería nada) | query BD + `:81-89` vs `:6636-6652`, `:6762-6766` | 🟡 Media |
| **B-7** | **Cero uso real**: 0 eventos `reclassification` en la bitácora; ninguna de las 13 guías y 8 recepciones existentes ha pasado nunca por el wizard | `SELECT count(*) … action_type='reclassification'` → 0 | 🟡 Media |
| **B-8** | Las guardas de negocio se evalúan **después** del ACL: un operador sin `unlink` recibe `AccessError` genérico en lugar del mensaje explicativo | `:122-123` en Python vs ACL aplicado por el ORM en `:141` | 🟡 Media |

`[VERIFICADO]` Los 8 hallazgos están **verificados** (código citado o consulta directa a `madenat_test`): ninguno es hipótesis. Las partes que sí requieren supuesto están marcadas `[HIPÓTESIS]` en su sección. `[NO VERIFICABLE]` El uso en producción real (fuera de `madenat_test`) no se pudo medir: la única base accesible es la de pruebas.

`[VERIFICADO]` Al margen de los 8 hallazgos numerados, **B2.2** documenta una asimetría estructural: la guía tiene 4 guardas de borrado (estado, grupo, dependencias, motivo) y la recepción sólo 2 (estado y lotes), más un salvoconducto `force_delete` que anula ambas. No se numera como hallazgo propio porque su efecto ya se recoge en B-3 y B-8; se documenta para que el diseño de B9.3 no repita la asimetría.

---

## B1 — Qué hace hoy `action_confirm_reclassify` (mapa exacto)

`[VERIFICADO]` El wizard tiene 153 líneas y **una sola acción**. Su secuencia real, en orden de ejecución:

| Paso | Línea | Qué ocurre | Efecto si falla |
|---|---|---|---|
| 1 | `:119` | `_get_source()` resuelve `env[source_model].browse(id).exists()` | `UserError` «El registro origen ya no existe» |
| 2 | `:122` | `_check_eligible()` — guarda de **estado** | `UserError` |
| 3 | `:123` | `_check_no_lots()` — defensa en profundidad | `UserError` |
| 4 | `:125-126` | exige `tipo_ingreso_correcto` | `UserError` |
| 5 | `:128` | `_old_tipo_label()` **infiere** el tipo viejo, no lo lee | nunca falla |
| 6 | `:131` | crea `madenat.audit.log` con `action_type='reclassification'` | `UserError` si el Selection no lo admite (sí lo admite, `madenat_audit_log.py:71`) |
| 7 | `:133-141` | `src.with_context(...).unlink()` con 2 claves de contexto | `UserError` del núcleo o `AccessError` del ACL |
| 8 | `:143-145` | crea `madenat.lumber.intake.wizard` con **un solo campo** | — |
| 9 | `:146-153` | devuelve `ir.actions.act_window` al wizard nuevo (`target='current'`) | — |

`[VERIFICADO]` Observaciones estructurales:

1. **`_old_tipo_label()` no lee el tipo anterior** (`:91-96`): para `lumber.reception` devuelve siempre `'producto'`; para guía, `'granel'` si `tipo_recepcion == 'granel'`, si no `'procesado'`. El tipo «incorrecto» es una **deducción del modelo**, no un dato. Si un modelo albergara dos tipos, la bitácora mentiría.
2. **No hay guarda de «mismo tipo»**: reclasificar una recepción a `producto` (su tipo actual) borra el registro y crea un wizard equivalente vacío. Cuenta como éxito.
3. **No hay comprobación de compañía, de autoría del ingreso ni de concurrencia**: dos reclasificaciones simultáneas del mismo origen no se bloquean de forma preventiva; la segunda muere en `_get_source` (`:59-61`).
4. **No hay `message_post` en ningún sitio**: ni en el origen (va a desaparecer) ni en el wizard nuevo. El chatter no conserva nada de la operación.
5. **No hay `savepoint` explícito**: la atomicidad depende de la transacción del RPC (ver B6).
6. **El snapshot readonly** (`source_display_name`, `source_create_date`, `:25-26`) es sólo para que el usuario vea qué va a borrar; **no se copia** al evento de auditoría ni al wizard nuevo.

`[VERIFICADO]` El modelo nuevo se crea con `{'tipo_ingreso': ...}` y nada más (`:143-145`). Todo lo demás lo aporta `default_get` del wizard de ingesta (`intake_wizard.py:126-133`): `intake_modality='normal'` (default del campo, `:101`), `ingestion_profile='metric'` (default, `:52`) y `assignment_location_id` resuelto con `resolve_patio_by_type('port')` porque la modalidad leída es `'normal'`. Es decir: **el destino hereda los valores por defecto del sistema, no los del ingreso original**.


---

## B2 — Tres capas de guardas que no coinciden

`[VERIFICADO]` Reclasificar atraviesa **tres** controles independientes. Ninguno conoce a los otros:

| Capa | Dónde | Qué mira |
|---|---|---|
| **1. Wizard** | `intake_reclassify_wizard.py:64-89` | `state` del origen + existencia de lotes |
| **2. `unlink` del núcleo** | `madenat_guia_processing.py:6711-6766` / `lumber_reception.py:3227-3247` | guía: estado (¡otra lista!), grupo, dependencias materiales, motivo obligatorio · recepción: estado y lotes (B2.2) |
| **3. ACL** | `ir_model_access` (BD) + `security/ir.model.access.csv` | permiso `unlink` del usuario sobre el modelo origen |

### B2.1 Matriz de estados: lo que cada capa acepta

| Modelo | Estado | Wizard (`_check_eligible`) | `_check_no_lots` | `unlink` del núcleo | ¿Resultado real? |
|---|---|---|---|---|---|
| `madenat.guia.processing` | `draft` | ✅ (`:67`) | ❌ si tiene algún lote en `lot_ids` (`:83`) | ✅ (`:6712`) | Funciona **sólo** sin lotes |
| `madenat.guia.processing` | `verified` | ✅ (`:67`) | ❌ si tiene lotes | ❌ **sólo `draft`/`cancelled`** (`:6712-6717`) | **Siempre falla** |
| `madenat.guia.processing` | `validated` | ❌ (`:67`) | — | ❌ | Falla en el wizard (correcto) |
| `madenat.guia.processing` | `cancelled` | ❌ (`:67`) | — | ✅ (`:6712`) | Falla en el wizard |
| `lumber.reception` | `draft` | ✅ (`:73`) | ❌ si tiene lotes | ✅ (`:3228`) | Funciona sin lotes |
| `lumber.reception` | `processing` | ✅ (`:73`) | ❌ si tiene lotes | ❌ **no está en `allowed_states`** (`:3228-3230`) | **Siempre falla** |
| `lumber.reception` | `verified` | ✅ (`:73`) | ❌ si tiene lotes | ✅ **sólo con la clave de contexto** (`:3224-3230`) | Funciona sin lotes |
| `lumber.reception` | `cancel` | ❌ (`:73`) | — | ✅ (`:3228`) | Falla en el wizard |

`[VERIFICADO]` La tabla se lee así: de las **8 combinaciones** estado-modelo que el wizard ofrece, **5 no pueden terminar nunca** (guía `verified`, guía `validated`, guía `cancelled`, recepción `processing`, recepción `cancel`) y las 3 restantes sólo funcionan si el origen **no tiene lotes**. El usuario rellena el formulario, pulsa «Confirmar Reclasificación» y recibe un error del núcleo con el nombre técnico del estado o un mensaje sobre lotes de inventario que nunca vio.

`[VERIFICADO]` Y en la base real **ninguna combinación llega al final**: la única guía `draft` (32300) tiene un lote en `lot_ids` y muere en `_check_no_lots`; las 4 `verified` mueren en `unlink` (B-1) y, aun corrigiendo esa lista, 2 de ellas morirían después en `_guia_deletion_blockers` (B-1); las 8 `validated` mueren en `_check_eligible`. Las únicas reclasificaciones posibles hoy son las 3 recepciones sin lotes (B3).

### B-1 · `[VERIFICADO]` La ruta Procesado → Producto está rota en el único estado que la UI ofrece

- El botón de la fachada se muestra con `invisible="state not in ('draft', 'verified')"` (`intake_guia_processing_facade_views.xml:52`).
- El wizard acepta `verified` (`:67`) y **sólo** `verified` es un caso realista: `draft` es una guía recién creada sin documentos leídos.
- `unlink` de la guía **no lee ninguna clave de contexto** que lo relaje: la lista de estados es literal y rígida (`:6711-6717`). La clave `madenat_reclassify_allow_verified_unlink` que el wizard pasa (`:134`) **sólo existe en `lumber_reception.py:3224`**; `grep -rn madenat_reclassify_allow_verified_unlink custom_addons` devuelve únicamente esa lectura.
- Consecuencia: **toda** reclasificación de una guía en `verified` termina en `UserError` «Sólo se pueden eliminar guías en estado 'Borrador' o 'Cancelado'». El evento de auditoría del paso 6 **no sobrevive** (rollback de la transacción), así que ni siquiera queda rastro del intento.
- `[VERIFICADO]` El test suite no lo detecta: `test_01` usa `state='draft'`; `test_05` prueba `verified` **sólo para recepción** (que sí honra la clave). No existe ningún caso «guía verified».
- `[VERIFICADO]` **Corolario empírico**: la única guía `draft` de la base (32300) tampoco sirve de escape, porque su M2M `lot_ids` tiene un lote (`UAT-SV-20261003-RET-01`, sin quants) y `_check_no_lots` la bloquea (`:83`). Es decir: **de las 13 guías existentes, ninguna es reclasificable por esta vía**, ni en `draft` ni en `verified`.
- `[VERIFICADO]` **Hasta dónde llegaría la corrección 1 de B9.3**, medida guía por guía (`stock_lot.guia_processing_id` vs. M2M `madenat_guia_processing_stock_lot_rel`):

| Guía | Estado | Lotes FK / M2M | Otras dependencias que mira el núcleo | Con la guarda de estado corregida |
|---|---|---|---|---|
| 33151 `95806` | `verified` | 0 / 0 | ninguna (0 albaranes, 0 SV, 0 imputaciones, 0 conciliaciones) | ✅ **pasaría** el wizard y borraría |
| 33250 `95083` | `verified` | 0 / 0 | ninguna | ✅ **pasaría** |
| 33737 `V3-CONCIL` | `verified` | 0 / 0 | **1** `processor.return.link` | ❌ moriría en `_guia_deletion_blockers` (`:6673-6678`), sin que el wizard lo advierta |
| 32411 `UATRB-GUIA-01` | `verified` | **2** / 0 | ambos lotes con **`stock.quant`** | ❌ pasaría `_check_no_lots` y moriría en `_guia_deletion_blockers` (`:6642-6647`) — el punto ciego de B-6 |
| 32300 `UAT-SV-20261003-IMPG` | `draft` | 0 / **1** | **1** `sv.imputation` | ❌ moriría en `_check_no_lots`; y aunque se relajara, en la imputación (`:6667-6672`) |

Sólo **2 de 13** guías quedarían reclasificables arreglando únicamente la lista de estados. Y las tres que fallan por otro motivo lo hacen **después** de que el wizard ya dio el visto bueno (`_check_no_lots` sólo mira el M2M): el usuario ve «todo correcto», pulsa confirmar y recibe un `UserError` del núcleo que habla de quants, conciliaciones o imputaciones. `[VERIFICADO]` Ninguna de esas dependencias se comprueba en el wizard.

### B-2 · `[VERIFICADO]` El evento de auditoría de la ruta Producto se borra a sí mismo

Cadena completa, toda verificada:

1. `_audit_vals()` asigna `vals['reception_id'] = src.id` cuando el origen es una recepción (`:111-112`).
2. `madenat.audit.log.reception_id` se declara `ondelete='cascade'` (`madenat_audit_log.py:48`).
3. Odoo materializa esa política **en la base de datos**: `odoo/tools/sql.py:479` crea la FK con `ON DELETE <policy>`; no hay borrado en cascada por ORM.
4. En `madenat_test`: `madenat_audit_log_reception_id_fkey | confdeltype = 'c'`.

Por tanto, en el paso 7 (`:141`) el `DELETE` de la recepción arrastra, por FK, **el evento recién insertado en el paso 6** y todos los eventos históricos de esa recepción. El `write`/`unlink` prohibido de la bitácora (`madenat_audit_log.py:33-46`) **no interviene**: la guarda es Python y el borrado es SQL.

`[VERIFICADO]` Contraste con guías: `guia_processing_id` es `ondelete='set null'` (`:54-58`, `confdeltype='n'`), y `test_01` lo comprueba (`test_intake_reclassify.py:71`). **La asimetría está en el dato, no en el wizard.** Reparto actual de la bitácora: **328 filas**, de las cuales 38 cuelgan de una recepción (destruibles por esta vía), 95 de una guía (a salvo) y 195 no tienen FK (a salvo). Es decir, el 29 % de los eventos ligados a un ingreso es destruible por un borrado de recepción.

`[VERIFICADO]` El test suite **no lo detecta**: `test_04` y `test_05` verifican el borrado de la recepción y el wizard nuevo, pero **no** que el evento `reclassification` siga existiendo (a diferencia de `test_01`, que sí lo verifica para guía).

### B-3 · `[VERIFICADO]` Ningún rol recorre las dos rutas: los permisos están partidos en tres grupos disjuntos

Consulta a `ir_model_access` en `madenat_test`:

| Modelo | Grupo con `perm_unlink` | Resto de grupos |
|---|---|---|
| `lumber.reception` | **sólo** `MADENAT: Compras y Operaciones` (id 61) | Jefatura, Operaciones, Auditoría, Contable: `unlink = false` |
| `madenat.guia.processing` | **sólo** `Jefatura de Operaciones` (id 261) | Operaciones: `unlink = false` |
| `madenat.lumber.intake.reclassify.wizard` | — (el wizard no se borra) | **crear/leer/escribir: sólo `Operaciones`** (id 256) |

Y las implicaciones reales (`res_groups_implied_rel`):

| Grupo | Implica (según `res_groups_implied_rel`) |
|---|---|
| `Jefatura de Operaciones` (261) | `Operaciones` (256), `Internal User` (1) |
| `Operaciones` (256) | `Stock: User` (48) — **no** implica `Compras y Operaciones` |
| `MADENAT: Compras y Operaciones` (61) | **nada** (no aparece como `gid` en la tabla) |

Consecuencia operativa:

- **Ruta Procesado → Producto**: requiere 261. Como 261 implica 256, el usuario puede crear el wizard. ✅ ACL, aunque la operación no puede terminar (B-1, B-6).
- **Ruta Producto → Procesado**: requiere 61 **y** 256. Un usuario que sólo tenga 61 **ni siquiera puede abrir/crear el wizard** (ACL del wizard = 256); uno que sólo tenga 256 **puede rellenarlo pero no ejecutarlo** (AccessError al borrar la recepción).
- Sólo **2 usuarios activos** de la base tienen los tres grupos: id 2 (`mauricio.seo@gmail.com`, además `Settings`) e id 8 (`cristhian.elguetag@gmail.com`). `v3_concil_jef@` tiene guía (261+256) pero no recepción; `v3_concil_oper@` e `impl_sv_check@` sólo tienen Operaciones (pueden abrir el wizard y no ejecutar nada) y ambos están **inactivos**. De los 5 usuarios activos, 3 sólo tienen `MADENAT: Validación Contable (Auditoría)` (62): no ven la operación.

`[VERIFICADO]` El grupo `MADENAT: Compras y Operaciones` **no tiene xmlid** en `ir_model_data` (no lo declara ningún módulo instalado): es un grupo heredado/creado a mano. `[HIPÓTESIS]` Procede de una configuración previa del cliente, no del código; cualquier reinstalación limpia dejaría la ruta Producto sin ningún rol capaz de usarla.

### B2.2 `[VERIFICADO]` Asimetría de blindaje: la guía está protegida cuatro veces, la recepción dos

| Guarda en `unlink` | `madenat.guia.processing` (`:6699-6768`) | `lumber.reception` (`:3210-3252`) |
|---|---|---|
| Estado | ✅ literal `draft`/`cancelled` | ✅ literal `draft`/`cancel` (+`verified` con clave de contexto) |
| Grupo de usuario | ✅ `_guia_delete_group_ok()` → `GUIA_DELETE_GROUPS` = Jefatura + `base.group_system` (`:6610-6623`, usado en `:6721-6725`) | ❌ **ninguno**: sólo el ACL del modelo |
| Dependencias materiales | ✅ `_guia_deletion_blockers()` (lotes, quants, move lines, costes, albaranes, SV, imputaciones, conciliaciones) | ⚠️ sólo `stock.lot` por `reception_id` (`:3239-3247`); **no** mira pickings, moves, quants, costes ni OC |
| Motivo obligatorio | ✅ `madenat_guia_delete_reason`, si falta, `UserError` (`:6750-6758`) | ❌ **ninguno** |
| Salvoconducto | `madenat.sv.internal.marker._sv_test_cleanup_allowed` (sólo tests) | ⚠️ **`force_delete` en contexto salta todas las guardas** (`:3219-3221`) |

`[VERIFICADO]` Dos consecuencias directas:

1. La reclasificación pasa **dos claves de contexto distintas** (`:133-141`) y cada una la lee **un solo modelo**: `madenat_reclassify_allow_verified_unlink` sólo existe en `lumber_reception.py:3224`; `madenat_guia_delete_reason` sólo en `madenat_guia_processing.py:6750`. Ningún modelo lee las dos → la mitad del contrato es letra muerta en cada ruta.
2. El mensaje de error de `lumber.reception` está copiado del de guías: llama «guía» a la recepción y dice «'Borrador' o 'Cancelado'» aunque la lista real sea `draft`/`cancel` (`:3233-3237`). El operador que reclasifica una recepción en `processing` lee un mensaje que habla de otro modelo y de otros estados.

`[VERIFICADO]` Además, `force_delete` no lo usa el wizard, pero **sí los servicios internos** (`reception_service.py:314` para moves, `reception_workflow.py:125` para líneas) y **también anula la guarda de estado en `lumber_reception.py:883-884`**: cualquier código que pase esa clave puede borrar una recepción `verified` con 16 lotes sin pasar por estado, lotes ni grupo. La protección real de la ruta Producto es, por tanto, **una sola línea de ACL** (B-3).

### B-8 · `[VERIFICADO]` Un operador sin ACL recibe `AccessError`, no el mensaje de negocio

`_check_eligible()` y `_check_no_lots()` (`:122-123`) son guardas **de negocio** en Python; el ACL se evalúa en el ORM al ejecutar `unlink()` (`:141`). Para un usuario con sólo `Operaciones` (hoy los dos de prueba, ambos inactivos), el orden real es: formulario completo → `UserError` de negocio (si aplica) → **`AccessError` de Odoo** («No tiene permiso para eliminar…»). El mensaje útil de `_check_eligible` («use la cancelación formal») sólo lo ve quien ya tenía permiso para borrar.


---

## B3 — Ruta Producto → Procesado (recepción → guía)

`[VERIFICADO]` Es la única ruta que **hoy puede completarse** en la base (3 recepciones sin lotes: 1161, 1244, 7950). Lo que ocurre, en orden:

| Fase | Efecto | ¿Recuperable? |
|---|---|---|
| `unlink` de `lumber.reception` | Borra cabecera y, por FK, **sus `lumber_reception_line`** (`confdeltype='c'`) | ❌ No |
| ídem | Borra **sus eventos de `madenat.audit.log`** (`reception_id` es `cascade`) | ❌ No |
| ídem | `stock.picking.reception_id`, `purchase_order.lumber_reception_id`, `toll_processing_order.source_reception_id` → `SET NULL` | ⚠️ Quedan huérfanos silenciosos |
| `ir.attachment` (PDF + Excel) | **No se borran**: nadie los referencia por FK. Sobreviven como adjuntos con `res_model='lumber.reception'` y `res_id` inexistente | ⚠️ Binario muerto en filestore |
| `_cleanup_orphan_moves` (`lumber_reception.py:3220`, `:3250`) | Borra `stock.move` con `origin = <nombre de la recepción>` y sin picking | ⚠️ Por coincidencia de texto |
| Wizard nuevo (`:143-145`) | Nace `draft`, sin documentos, con patio/perfil por defecto | — |

`[VERIFICADO]` Medición en la base para las 3 recepciones elegibles:

| Recepción | Líneas | Adjuntos | Eventos de auditoría | Resultado de reclasificar |
|---|---|---|---|---|
| 1161 `39519` | 12 | 2 | 1 | 12 líneas + 1 evento destruidos; 2 adjuntos huérfanos |
| 1244 `97183` | 8 | 2 | 1 | 8 líneas + 1 evento; 2 adjuntos huérfanos |
| 7950 `41994` | 14 | 2 | 1 | 14 líneas + 1 evento; 2 adjuntos huérfanos |

Es decir: **34 líneas leídas del documento y 3 eventos de bitácora** se pierden para corregir una etiqueta. Las otras 5 recepciones `verified` (962, 1270, 1369, 1371, 7900) tienen entre 1 y 16 lotes: `unlink` las bloquea en `:3239-3247` **después** de que el wizard ya pasó sus propias guardas, con un mensaje distinto («ya ha generado N lotes») y sin mencionar la reclasificación.

### B-4 · `[VERIFICADO]` «Granel» se ofrece como tipo, pero no existe como ruta

- La selección del wizard incluye `('granel', 'Madera a granel / volumen total')` (`intake_reclassify_wizard.py:31`).
- Pero el router de ingesta **no conoce ese valor**: deriva a Granel por **modalidad**, no por tipo (`intake_wizard.py:697-698`: `if self.intake_modality == 'volume': return self._route_granel()`), y el tipo sólo se consulta para `producto` (`:701`) y `procesado` (`:703`).
- El wizard nuevo se crea sin `intake_modality` (`:143-145`), así que toma el default `'normal'` (`intake_wizard.py:101`). Con `tipo_ingreso='granel'` + `intake_modality='normal'` cae en el `UserError` de `:705-710`: «No se pudo determinar el tipo de ingreso (Producto o Procesado)…».
- Conclusión: **elegir «granel» garantiza el fallo** en el paso siguiente, con un mensaje que contradice la propia UI del wizard (que acaba de ofrecer granel como opción válida). La combinación que sí funciona (`intake_modality='volume'`) no la puede escribir el usuario desde el wizard de reclasificación: es una corrección que sólo se arregla copiando la modalidad al destino (B9.3, cambio 3).

### B-5 · `[VERIFICADO]` Lo que el wizard nuevo **no** hereda

| Dato del origen | ¿Se copia? | Dónde se demuestra |
|---|---|---|
| `partner_id` | ❌ | `:143-145` sólo envía `tipo_ingreso` |
| `purchase_id` (OC) | ❌ | ídem (y la FK de OC quedó en `SET NULL`) |
| `ingestion_profile` | ❌ (nace `metric`) | `intake_wizard.py:52` |
| Patio de asignación | ❌ (nace el patio de tipo `port`) | `intake_wizard.py:126-133` |
| Fechas y tipo de cambio (`guia_fecha` `:1104`, `exchange_rate_date` `:1309` / `date_emission` `:982`, `rate_date` `:1112`) | ❌ | `:143-145` |
| Líneas y volúmenes leídos | ❌ | `preview_data` es `fields.Text`, no estructuras (`intake_wizard.py:176`) |
| PDF / Excel | ❌ | No hay copia de `ir.attachment`; la vista lo advierte (`intake_reclassify_wizard_views.xml:9-14`) |
| `oc_reference_raw` (`:1147`), `tipo_recepcion` | ❌ | ídem |

`[VERIFICADO]` La advertencia de la vista (`:9-14`) es honesta pero **incompleta**: dice que hay que volver a adjuntar documentos; no dice que se pierden líneas, patio, perfil, proveedor, OC ni el evento de auditoría.

---

## B4 — Ruta Procesado → Producto (guía → recepción)

`[VERIFICADO]` **Hoy no puede completarse en ningún estado** (B-1: `verified` cae en el `unlink` del núcleo, `draft` cae en `_check_no_lots`). Si se corrigieran ambas guardas, esto es lo que ocurriría:

| Fase | Efecto | Riesgo |
|---|---|---|
| Paso 6: evento `reclassification` con `guia_processing_id` | Sobrevive (`SET NULL`) | ✅ correcto, pero se duplica con el `guia_delete_permanent` del paso 7 (B7.1) |
| Paso 7: `unlink` de la guía | Exige grupo `Jefatura` (`:6721-6725`) | ✅ |
| `_guia_deletion_blockers` (`:6625-6679`) | Bloquea si hay lotes SV, quants, move lines, costes, albaranes, operaciones SV, imputaciones o conciliaciones envío–retorno | ✅ mensaje de negocio |
| Paso 7, motivo obligatorio (`:6750-6758`) | El wizard lo aporta (`:138-140`) | ✅ único punto donde el wizard satisface al núcleo |
| Paso 7 (sin bloqueos) | Borra líneas, M2M, detalle de volumen (`madenat_lumber_volume_detail_line`, `cascade`) y **el ciclo de vida de la guía** (`madenat_lumber_intake_guide_lifecycle`, `cascade`) | ⚠️ Se pierde el histórico del propio ciclo de vida |
| Paso 7, `:6762-6766` | Borra **todos** los `stock.lot` con `guia_processing_id = rec.id` | ⚠️ Ver B-6 |
| Paso 7, `:6741` → `_cleanup_orphan_moves_guia` | Borra `stock.move` huérfanos por `origin = guía.name`; los que ya tienen cantidad los **renombra** `HUERFANO-PROTEGIDO-…` y publica un `message_post` en `self[:1]`… **que es la guía que se está borrando** | ⚠️ El aviso al usuario se destruye con el registro |

### B-6 · `[VERIFICADO]` `_check_no_lots` tiene un punto ciego

`_check_no_lots` (`:81-89`) mira `src.lot_ids` (M2M) y, para guías, `src.source_lot_ids`. **No mira `stock.lot.guia_processing_id`**, que es la relación inversa real que usa el núcleo (`stock_lot_guia_processing_id_fkey`, `SET NULL`).

Caso real en `madenat_test` — las dos relaciones apuntan en sentidos distintos y **no coinciden**:

| Guía | Estado | `stock.lot` con `guia_processing_id` | Filas en `madenat_guia_processing_stock_lot_rel` (`lot_ids`) | Qué ve el wizard | Qué ve el núcleo |
|---|---|---|---|---|---|
| 32411 `UATRB-GUIA-01` | `verified` | **2** (`UATRB-LOT-OK` 4 uds, `UATRB-LOT-EX` 3 uds) | **0** | «no hay lotes» → deja pasar | 2 lotes con quant → **bloquea** |
| 32300 `UAT-SV-20261003-IMPG` | `draft` | **0** | **1** (`UAT-SV-20261003-RET-01`, 0 quants) | «hay un lote» → **bloquea** | 0 lotes por FK inversa → no bloquearía |

`[VERIFICADO]` Los dos lotes de 32411 tienen quant (4 y 3 unidades) y el segundo no tiene move line; los `_guia_deletion_blockers` (`:6636-6652`) los detectan por `guia_processing_id` y por quant, así que la guía queda protegida. Pero el **orden** es: el wizard dice «no hay lotes» → el núcleo dice «hay dependencias». Si esos lotes estuvieran sin quant, sin move line y sin coste (el caso «lote creado y no usado», `_guia_deletion_blockers` devolvería lista vacía), `:6762-6766` los borraría **en silencio** y la reclasificación habría destruido inventario sin que ninguna guarda lo advirtiera.

`[VERIFICADO]` Y el caso inverso también existe: el lote `UAT-SV-20261003-RET-01` está en `lot_ids` de la guía 32300 pero su `guia_processing_id` es `NULL`. Si esa guía llegara a borrarse por otra vía, el lote **sobreviviría huérfano** (no lo toca `:6762-6766`, que busca por la FK inversa) y la única huella de a qué guía perteneció sería una fila de tabla relacional que el `cascade` del M2M borra.


---

## B5 — Efectos en stock, picking, move y quant: matriz real de la base

`[VERIFICADO]` El wizard no escribe ni una sola fila de stock: **todo** el efecto lo produce el `unlink` del núcleo. Lo que ocurra con el inventario depende exclusivamente de las políticas `ON DELETE` de las FK, consultadas en `pg_constraint` de `madenat_test` (`c` = cascade, `n` = set null, `r` = restrict):

### B5.1 Hijos de `lumber.reception`

| Tabla hija | Política | Efecto de reclasificar |
|---|---|---|
| `lumber_reception_line` | `c` | Líneas del documento borradas |
| `madenat_audit_log` | `c` | **Histórico destruido** (B-2) |
| `validation_checklist_item` | `c` | Checklist borrada |
| `madenat_lumber_intake_po_link` | `c` | Vínculo con OC borrado |
| `lumber_reception_reset_wizard` | `c` | Wizards transitorios borrados |
| `stock_lot.reception_id` | `n` | Inalcanzable: `unlink` bloquea si hay lotes (`:3239-3247`) |
| `stock_lot.origin_reception_id` | `n` | Puede quedar un lote «sin origen» si existiera sin estar en `reception_id` |
| `stock_picking.reception_id` | `n` | **Albarán huérfano** (sin bloqueo previo: `unlink` de recepción no consulta pickings) |
| `purchase_order.lumber_reception_id` | `n` | OC sin recepción vinculada |
| `toll_processing_order.source_reception_id` | `n` | **Orden de procesamiento sin su recepción de origen** |
| `madenat_lumber_intake_cancel.reception_id` | `n` | Registro de cancelación huérfano |
| `madenat_lumber_intake_supplier_link.reception_id` | `n` | Vínculo de proveedor huérfano |
| `lumber_reception_mass_update.reception_id` | `n` | Wizard de actualización masiva huérfano |

`[VERIFICADO]` El `unlink` de recepción **no comprueba pickings, movimientos ni quants** en ningún momento (`lumber_reception.py:3210-3252`): sólo estado y `stock.lot` por `reception_id` — ni siquiera exige grupo (B2.2). Es la única guarda material de la ruta Producto.

### B5.2 Hijos de `madenat.guia.processing`

| Tabla hija | Política | Efecto de reclasificar |
|---|---|---|
| `madenat_guia_processing_line` | `c` | Líneas borradas |
| `madenat_lumber_volume_detail_line` | `c` | **Detalle de volumen borrado** (guías por volumen) |
| `madenat_lumber_intake_guide_lifecycle` | `c` | **Ciclo de vida borrado** |
| `madenat_guia_processing_source_lot_line` / `_rel` | `c` | Trazabilidad de lotes origen borrada |
| `madenat_guia_processing_stock_lot_rel` | `c` | M2M `lot_ids` borrado |
| `madenat_audit_log` | `n` | Bitácora preservada ✅ |
| `stock_lot.guia_processing_id` | `n` | **Borrado explícito por `:6762-6766`** si existen |
| `stock_lot.volume_source_guia_id` | `r` | RESTRICT: el borrado falla en BD si hay lote SV (además lo detecta `:6639-6641`) |
| `stock_picking.guia_processing_id` | `n` | Bloqueado antes por `:6657-6660` ✅ |
| `madenat_sv_operation` / `madenat_sv_imputation` / `madenat_processor_return_link` | `r` | RESTRICT: bloqueado antes por `:6661-6672` ✅ |
| `lumber_reception.origin_processing_id` | `n` | Recepción «sin origen procesado» |
| `lumber_cost_distribution.reception_id` | `n` | Costeo huérfano — **el campo se llama `reception_id` pero la FK apunta a la guía** (`lumber_cost_distribution_reception_id_fkey` → `madenat_guia_processing`) |
| `lumber_cost_distribution_wizard.reception_id` | `n` | Ídem: wizard de costeo huérfano |
| `madenat_lumber_intake_supplier_link.guia_id` | `n` | Vínculo de proveedor huérfano |
| `madenat_guia_processing_reopen_wizard` / `_historical_reverse_wizard` / `_documental_correction_wizard` | `c` | Wizards auxiliares borrados (no hay bloqueo: son `TransientModel` de sesiones pasadas) |
| `madenat_sv_imputation_wizard` | `c` | Wizard de imputación SV borrado |

`[VERIFICADO]` Conclusión de la matriz: **la ruta Producto es la más frágil** (cascadea la bitácora y deja albaranes/OC/órdenes sin vínculo) y **la ruta Procesado está mejor protegida** (bloqueos explícitos + RESTRICT), pero es la que no se puede ejecutar (B-1).

### B5.3 `_cleanup_orphan_moves_*`: limpieza por coincidencia de texto

`[VERIFICADO]` Ambas ramas localizan movimientos huérfanos por **nombre**, no por identidad:

```python
moves = self.env['stock.move'].sudo().search([('origin', 'in', names), ('picking_id', '=', False)])
```
(`madenat_guia_processing.py:6784-6787`; `reception_service.cleanup_orphan_moves` recibe `self.mapped('name')`, `lumber_reception.py:3250`)

Si otro documento (de otro modelo, de otro año o creado a mano) tiene el mismo `origin`, sus movimientos se borran o se renombran `HUERFANO-PROTEGIDO-…` sin relación con la guía reclasificada. No es explotable con los datos actuales, pero es un efecto colateral no acotado por compañía, fecha ni modelo.


---

## B6 — Atomicidad

`[VERIFICADO]` Todo el wizard corre en **una sola transacción de RPC**: el `create` de auditoría (`:131`), el `unlink` (`:141`) y el `create` del wizard nuevo (`:143-145`) no abren savepoints. Consecuencias:

| Escenario | Estado final de la base | Traza que queda |
|---|---|---|
| Falla la guarda de estado (B-1) | Nada cambia | **Ninguna** (el evento del paso 6 ni se crea: falla antes) |
| Falla `unlink` por dependencias (B5.2) | Nada cambia | **Ninguna** (el evento del paso 6 se revierte con la transacción) |
| Falla el `create` del wizard nuevo | **Nada cambia** (rollback del `unlink`) | Ninguna |
| Éxito en guía | Origen borrado + wizard vacío | **Dos** eventos: `reclassification` (wizard `:131`) **y** `guia_delete_permanent` (núcleo `:6685-6697`) |
| Éxito en recepción | Ídem | Un evento `reclassification`… **que la propia transacción borra** (B-2) |

`[VERIFICADO]` Es decir: la atomicidad **es correcta** (no hay estados a medias) y a la vez **es el problema de auditoría**: como el evento se inserta en la misma transacción que el borrado, **todo intento fallido desaparece sin rastro**. Un usuario puede intentar reclasificar diez veces una guía `verified` (B-1) y la bitácora seguirá en 0 — que es exactamente lo que muestra hoy la base.

`[VERIFICADO]` El comentario del código («Auditoría ANTES del unlink: el origen debe existir para popular la FK», `:130`) describe una **necesidad de orden**, no una garantía de persistencia. La única forma de conservar el intento fallido sería un savepoint + commit parcial, o registrar el evento en una transacción separada — y ninguna de las dos existe.

---

## B7 — Auditoría, chatter y evidencia

### B7.1 Lo que se registra

`[VERIFICADO]` `_audit_vals` (`:98-115`) construye un evento con **4 campos**:

| Campo | Valor | Observación |
|---|---|---|
| `action_type` | `'reclassification'` | Valor aditivo correcto (`madenat_audit_log.py:71`) |
| `description` | texto multilínea con nombre, modelo, tipo viejo y tipo nuevo | El tipo viejo es **inferido** (B1, punto 1) |
| `user_id` | usuario actual | — |
| `reception_id` / `guia_processing_id` | FK al origen | **`reception_id` cascadea** (B-2) |

`[VERIFICADO]` Campos que el resto de la bitácora sí usa y este evento **no**:

| Campo | Uso en otros eventos | Valor aquí |
|---|---|---|
| `batch_id` | Nombre de la guía (p. ej. `_guia_log_deletion:6687`) | `NULL` |
| `audit_snapshot` | Snapshot JSON determinista (BT-01, AD-93, AD-98…) | `NULL` |
| `audit_hash` | Firma SHA-256 | `NULL` |

`[VERIFICADO]` Consecuencia: el evento de reclasificación es **uno de los pocos eventos de ingreso sin firma ni snapshot**. No se puede probar qué se borró (ni el número de líneas, ni el volumen, ni los documentos) más allá de un texto libre.

`[VERIFICADO]` **En guías se escriben dos eventos por cada reclasificación**:

| # | Origen | `action_type` | `batch_id` | Motivo |
|---|---|---|---|---|
| 1 | wizard `:131` | `reclassification` | `NULL` | descripción libre |
| 2 | núcleo `:6699-6761` → `_guia_log_deletion` | `guia_delete_permanent` | **nombre de la guía** | el mismo texto de reclasificación, vía `madenat_guia_delete_reason` |

`[VERIFICADO]` Efectos: (a) la bitácora registra la operación como **eliminación permanente** (`guia_delete_permanent`), no como reclasificación, porque el núcleo no distingue el motivo; (b) el evento que sí tiene `batch_id` y conteos (líneas, lotes) es el del núcleo; el del wizard —el único que dice «reclassification»— no los tiene; (c) quien consulte «cuántas guías se eliminaron permanentemente» obtendrá también las reclasificadas. En recepción no existe este segundo evento porque `lumber.reception.unlink` no llama a `_guia_log_deletion` ni equivalente: sólo tiene el evento del wizard, que cascadea (B-2).

### B7.2 Chatter

`[VERIFICADO]` Ni `lumber.reception` (`lumber_reception.py:906`) ni `madenat.guia.processing` (`:921`) sobreviven al borrado con su chatter: los `mail.message` asociados quedan con `res_id` inexistente. `[VERIFICADO]` El wizard de ingesta **no hereda `mail.thread`** (`intake_wizard.py:17-22`): el registro nuevo no tiene chatter donde dejar constancia.

`[VERIFICADO]` El único `message_post` de toda la ruta está en `_cleanup_orphan_moves_guia` (`:6817-6827`) y se publica en la guía que se está borrando: **se destruye con ella**.

### B7.3 Trazabilidad del wizard nuevo

`[VERIFICADO]` El wizard nuevo es un `models.Model` persistente pese al nombre (`intake_wizard.py:18-19`, sin `_transient`), con estado `draft`. Pero **no guarda ningún puntero al origen**: no hay `reclassified_from_model`, `reclassified_from_id`, ni `reclassification_audit_id`. La única relación posible es la descripción de texto del evento de auditoría, que se busca por `ilike` del nombre (`test_intake_reclassify.py:66-69`). Si dos documentos comparten nombre (habitual: una guía reenviada), la evidencia es ambigua.

---

## B8 — Estado real de la base (fotografía)

`[VERIFICADO]` Consultas de sólo lectura sobre `madenat_test`:

### B-7 · `[VERIFICADO]` Cero uso real

`SELECT count(*) FROM madenat_audit_log WHERE action_type='reclassification'` → **0**. El wizard nunca se ha completado con éxito en esta base. Y no es porque falte actividad: la misma tabla tiene **38 eventos ligados a recepciones** y **95 ligados a guías** (validaciones, cancelaciones, firmas). La reclasificación es el único acto del ciclo de ingreso que no tiene ni una sola fila. (Coincide con el patrón del FRENTE A: funcionalidad implementada sin uso empírico.)

**Guías (13):**

| Estado | n | Lotes | Pickings | Líneas | ¿Reclasificable hoy? |
|---|---|---|---|---|---|
| `draft` | 1 (`32300 UAT-SV-20261003-IMPG`) | 0 por FK inversa / **1 en `lot_ids`** | 0 | 0 | ❌ **no**: `_check_no_lots` la bloquea |
| `verified` | 4 | 0–2 | 0 | 0–8 | ❌ **no** (B-1) |
| `validated` | 8 | 1–19 | 0–2 | 0–19 | ❌ no (correcto por diseño) |

Detalle de las 4 `verified`: `32411` (2 lotes, 0 líneas), `33151` (0 lotes, 1 línea, 1 adjunto), `33250` (0 lotes, 8 líneas, 4 adjuntos), `33737` (0 lotes, 0 líneas). **Las candidatas ideales** —sin lotes, con documento leído— son exactamente las que el wizard no puede procesar; y de ellas sólo 33151 y 33250 sobrevivirían además a `_guia_deletion_blockers`, porque 32411 tiene dos lotes con `stock.quant` y 33737 una conciliación envío–retorno (B-1).

**Recepciones (8, todas `verified`):**

| Recepción | Lotes | Líneas | Adjuntos | Eventos de auditoría | ¿Reclasificable hoy? |
|---|---|---|---|---|---|
| 962 `41471` | 16 | 16 | 2 | 2 | ❌ bloqueada por lotes |
| 1161 `39519` | 0 | 12 | 2 | 1 | ✅ sí (`delete` destruiría 12 líneas + 1 evento) |
| 1244 `97183` | 0 | 8 | 2 | 1 | ✅ sí (8 líneas + 1 evento) |
| 1270 `100006` | 8 | 8 | 2 | 2 | ❌ bloqueada por lotes |
| 1369 `15183` | 12 | 13 | 2 | 14 | ❌ bloqueada por lotes (serían 14 eventos) |
| 1371 `41964` | 12 | 12 | 2 | 14 | ❌ bloqueada por lotes (serían 14 eventos) |
| 7900 `900001` | 1 | 1 | 2 | 3 | ❌ bloqueada por lotes |
| 7950 `41994` | 0 | 14 | 2 | 1 | ✅ sí (14 líneas + 1 evento) |

`[VERIFICADO]` Las 8 recepciones tienen **2 adjuntos cada una** (PDF y Excel): reclasificar cualquiera deja 2 binarios huérfanos en el filestore. Las que hoy se pueden reclasificar dejarían **6 adjuntos** sin registro padre.

**Consola:** `madenat.lumber.intake.console` es una **vista SQL** (`intake_console.py:17-27`, `_auto = False`), no una tabla. `[VERIFICADO]` El `id` se deriva del origen (`id = reception.id` para Producto; `CONSOLE_ID_OFFSET + guia.id` para Procesado, `:24-27`). Consecuencia: al borrar el origen **la tarjeta desaparece de la consola sin dejar hueco ni aviso**, y vuelve a aparecer recién cuando el wizard nuevo crea su destino. No hay tarjeta «zombi», pero tampoco hay tarjeta «reclasificándose»: el operador ve el ingreso evaporarse.


---

## B9 — Diseño propuesto

### B9.1 El problema de fondo

`[VERIFICADO]` «Tipo de ingreso» **no es un campo**: es el **modelo** en el que vive el registro.

| Tipo | Modelo | Quién lo decide |
|---|---|---|
| Producto | `lumber.reception` | `_route_producto()`, invocado en `intake_wizard.py:701` |
| Procesado | `madenat.guia.processing` | `_route_procesado()`, invocado en `:703` |
| Granel | `madenat.guia.processing` con `tipo_recepcion='granel'` | `_route_granel()` |

Por eso «reclasificar» se implementó como «borrar y volver a empezar». Mientras el tipo sea el modelo, **cualquier corrección será una migración de datos**, no un `write`.

### B9.2 Tres caminos, con su coste real

| Opción | Qué implica | Ventaja | Coste / riesgo |
|---|---|---|---|
| **A. Conversión preservada** (recomendada) | Crear el registro destino copiando todos los campos y **reutilizando los adjuntos**; el origen pasa a `cancelled` + `active=False` (no se borra) | Nada se pierde; la auditoría y el chatter sobreviven; reversible | Implementar el mapeo campo a campo en los dos sentidos; decidir qué hacer con lotes (bloquear si existen) |
| **B. Borrado con las 7 correcciones** | Mantener el diseño actual y arreglar lo que se rompe (B9.3) | Cambio pequeño, un solo archivo + 2 del núcleo | Sigue siendo destructivo: el usuario rehace el ingreso; la evidencia documental se re-adjunta a mano |
| **C. Retirar el botón** | Ocultar `action_reclassify` hasta que exista A | Riesgo cero inmediato | El error de clasificación se corrige con cancelación formal (`action_force_cancel`), más pesada y post-Gate-3 |

`[VERIFICADO]` La opción C es hoy la única que **no produce pérdida de datos** sin escribir código: el botón se ofrece en estados donde la operación no puede completarse (guía `verified`) o destruye evidencia (recepción). `[HIPÓTESIS]` Retirarlo no rompe nada porque la bitácora demuestra 0 usos.

### B9.3 Las 7 correcciones mínimas si se elige B

| # | Cambio | Archivo / línea | Hallazgo que cierra |
|---|---|---|---|
| 1 | Una sola lista de estados: que `unlink` de guía lea `madenat_reclassify_allow_verified_unlink` igual que recepción, **o** que `_check_eligible` deje de aceptar `verified` | `madenat_guia_processing.py:6711-6717` + `intake_reclassify_wizard.py:67` | B-1 |
| 2 | El evento de auditoría **no** debe usar `reception_id` (FK `cascade`): escribir el origen en `batch_id` + `description`, o añadir `source_model`/`source_res_id` a `madenat.audit.log` | `intake_reclassify_wizard.py:111-114` | B-2 |
| 3 | Copiar al wizard nuevo lo que se conoce: `partner_id`, `assignment_location_id`, `ingestion_profile`, y `intake_modality='volume'` si el destino es `granel` | `:143-145` | B-4, B-5 |
| 4 | `_check_no_lots` debe mirar también `stock.lot.guia_processing_id` | `:81-89` | B-6 |
| 5 | Declarar `groups=` en el modelo o en los botones para que sólo quien puede borrar vea la acción; o comprobar el ACL en `_check_eligible` con mensaje de negocio | `intake_reclassify_wizard.py` + 3 vistas | B-3, B-8 |
| 6 | Tests que hoy faltan: guía `verified`; el evento de auditoría **después** de reclasificar una recepción; destino `granel` | `test_intake_reclassify.py` | B-1, B-2, B-4 |
| 7 | Igualar el blindaje de la recepción al de la guía: comprobar `_guia_delete_group_ok`-equivalente y exigir motivo antes del `unlink`, y dejar de usar `force_delete` como bypass de guardas | `lumber_reception.py:3210-3252` | B2.2, B-3, B-8 |

`[VERIFICADO]` Ninguno de los 7 cambios toca fórmulas, volúmenes, lotes ni el motor de lectura: son guardas, copia de contexto y evidencia. El 2 y el 4 son los únicos que rozan el núcleo (una FK de auditoría y una búsqueda de lotes); el 7 vive en un solo método de `lumber_reception.py`; el resto vive en `madenat_lumber_intake`.

### B9.4 Regla de oro propuesta

> Reclasificar **no debe borrar nada que el usuario no pueda volver a producir con un clic**. Hoy borra líneas, lectura, patio, perfil y bitácora, y le pide re-adjuntar los PDF a mano. Mientras eso sea así, la operación no es «corregir una etiqueta»: es **rehacer el ingreso**.


---

## B10 — Preguntas abiertas (para negocio)

1. **¿El tipo de ingreso se puede corregir después de leer el documento?** Si la respuesta es sí, ¿qué se conserva del ingreso original: los documentos, las líneas, el patio, la OC?
2. **¿Una guía `verified` puede cambiar de tipo, o el estado `verified` ya es un compromiso?** Hoy el wizard dice que sí y el núcleo dice que no (B-1).
3. **¿Quién es el dueño de la corrección?** Hoy hacen falta dos grupos distintos para las dos direcciones y sólo 2 de los 5 usuarios activos tienen ambos perfiles (B-3).
4. **¿«Granel» es un tipo de ingreso o una modalidad?** El wizard lo ofrece como tipo; el de ingesta lo trata como modalidad (`intake_modality='volume'`) y con modalidad `normal` no rutea (B-4).
5. **¿Se acepta que el evento de auditoría de una reclasificación de Producto desaparezca con el registro?** Si no, hay que cambiar la FK o el destino del vínculo (B-2).
6. **¿La consola debe mostrar el ingreso mientras se reclasifica?** Hoy la tarjeta desaparece y reaparece sólo cuando el wizard nuevo crea el destino (B8).
7. **¿Los 38 eventos de auditoría ligados a recepciones son evidencia a preservar?** Si sí, la FK `cascade` es un riesgo latente para cualquier borrado de recepción, no sólo para este wizard.

---

## Cierre

`[VERIFICADO]` El FRENTE B no encontró un problema de lectura ni de cálculo: encontró un **problema de identidad**. El wizard promete «corregir el tipo» y lo que hace es **destruir el registro y pedirle al usuario que lo rehaga**, con tres capas de guardas que no se hablan entre sí: la que decide qué se puede pedir, la que decide qué se puede borrar y la que decide quién puede hacerlo.

`[VERIFICADO]` Los extremos del arco:

- La ruta **Procesado → Producto** está bloqueada en **todos** los estados: `verified` por el `unlink` del núcleo (B-1), `draft` por los lotes del M2M (B-6). Y su evidencia de auditoría moriría con el registro si se desbloqueara sin corregir la FK (B-2). Corregir sólo la guarda de estado dejaría pasar **2 de 13** guías (33151, 33250): las otras tres seguirían cayendo en bloqueos del núcleo que el wizard no anticipa.
- La ruta **Producto → Procesado** funciona, pero destruye 34 líneas leídas y 3 eventos de bitácora en los 3 casos reales que hoy existen (B3, B-2), y deja 6 adjuntos y los pickings/OC huérfanos (B5).
- Ninguna de las dos se usó nunca: **0 eventos `reclassification`** en una base con 38 eventos de recepción y 95 de guía (B8).

### Frase de cierre del FRENTE B

> **El sistema permite corregir el tipo de un ingreso sólo borrándolo, y ni siquiera puede hacerlo en el estado en que el ingreso realmente se equivoca.**

`[VERIFICADO]` Síntesis del arco B1→B10: el wizard no falla por un bug aislado; falla porque el «tipo» **es** el modelo, y porque las tres capas que debían protegerlo —estado, dependencias materiales y rol— se escribieron por separado y nunca se probaron juntas. La ruta que funciona es la destructiva; la ruta que no destruye evidencia es la que no puede ejecutarse.

---

**Fin del FRENTE B.** Este informe no modificó código, vistas, datos ni manifiestos; no se ejecutaron upgrades, tests ni reinicios. Todas las consultas a la BD fueron `SELECT`. Las únicas escrituras son este archivo y `INFORME_FRENTE_A.md`.

