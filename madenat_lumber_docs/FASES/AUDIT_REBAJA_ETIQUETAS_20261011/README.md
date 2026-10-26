# AUDITORÍA INTEGRAL — CICLO DE REBAJA DE ETIQUETAS (MADENAT, Odoo 18 CE)

**Fecha:** 2026-10-11 · **Entorno:** `madenat_test` · contenedor `odoo18_app` (PostgreSQL `odoo18_db`)
**Módulo auditado:** `madenat_lumber_logistics` (**18.0.1.14.1 → 18.0.1.15.0**)
**Naturaleza:** expediente de **evidencia** (no doctrinal). La doctrina vive en
`custom_addons/madenat_lumber_docs/CANON/` (19 §19.14–19.19, 18 §7.3, 02 §17.16.x, 03, 05).
**Modo:** auditoría → correcciones de defectos demostrados → pruebas → actualización local →
documentación. **Sin commit, sin push, sin despliegue remoto, sin reparación histórica.**

---

## 1. Dictamen ejecutivo

**Dictamen: COMPLETO CON LÍMITES.**

El «ciclo de rebaja documental de etiquetas» (I2, `madenat.sv.imputation`) **existe, es
persistente y opera** sobre el mecanismo único (modelo + asistente + `action_apply`/`action_reverse`).
La auditoría **confirmó cuatro defectos reales** (uno de ellos explica la captura «disponibilidad 0,
sin reparto, aviso genérico») y se corrigieron con validación y pruebas. Se añadieron **7 pruebas**
(AUD-ETQ-01..05) y se ajustaron 5 archivos de pruebas existentes al motivo obligatorio de reversa.

**Límites declarados (no acreditados como correctos):**
- **Renderización real en navegador (V3)**: no hay navegador en el entorno. La verificación es por
  ORM + XML + pruebas; **no** se declara renderizado aprobado.
- **Concurrencia multi-cursor real**: la protección por advisory locks existe y está probada en una
  sesión que **retiene** el lock (existente `test_con_01`). Una prueba de dos transacciones
  *simultáneas* independientes no se ejecutó aquí → **pendiente**, no acreditada.
- **Reasignación tras aplicar**: se resuelve por **reversa + nueva imputación** (mecanismo existente).
  No se ejecutó el recorrido completo aplicado→revertido→reasignado→aplicado con datos **reales**
  (sí está cubierto por pruebas transaccionales: `test_processor_return_link.T15`, `test_sv_imputation_i2.T08`).
- **Reparación de datos históricos**: **no** ejecutada (no autorizada). Ver §17.

---

## 2. Baseline y respaldos reales

| Ítem | Valor |
| --- | --- |
| Repositorio | `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons` (git) |
| Rama | `feat/guia-correccion-documental-preservada-20261002` |
| HEAD | `b1d2d1911648f3264bf629c8eccf79a1c140eaf3` |
| `git status` (pre) | 43 modificados + 19 sin seguimiento (trabajo local previo) — `code/status_pre.txt` |
| Diff local previo | `code/wip_pre.diff` (7.648 líneas) — **preservado** |
| Base destino | `madenat_test` (122 MB) |
| Módulo | `madenat_lumber_logistics` `18.0.1.14.1` instalado |
| Contenedores | `odoo18_app` (monta `custom_addons` en `/mnt/extra-addons`), `odoo18_db` |

**Respaldos tomados ANTES de intervenir** (`db/` y `code/`; integridad comprobada):

| Respaldo | Comando | Tamaño | Comprobación |
| --- | --- | --- | --- |
| Código (`_logistics`, `_docs`, `_intake`) | `tar czf` | 2.502.416 B | `gzip -t` OK |
| Base `madenat_test` | `docker exec odoo18_db pg_dump -U odoo -Fc madenat_test` | 11.420.486 B | `pg_restore --list` OK (612 tablas, 13.401 entradas) |
| Filestore | `docker exec odoo18_app tar czf - -C /var/lib/odoo/filestore madenat_test` | 21.388.047 B | `gzip -t` OK |

**Recuperación:** código → `tar xzf code/modules_pre.tar.gz -C .../custom_addons`; base → restaurar
`db/madenat_test_pre.dump` sobre una **copia** (no sobre `madenat_test` en caliente); filestore →
extraer en `/var/lib/odoo/filestore`. **No** se afirma una restauración ejecutada: sólo se verificó la
**integridad** de los respaldos.

---

## 3. Mapa real del flujo (modelos, relaciones, acciones)

### 3.1 Modelos (nombres verificados en código)

| Modelo | Rol | Clave |
| --- | --- | --- |
| `madenat.guia.processing` | Guía de procesados (origen del retorno) | `service_return_confirmation='yes'` ⇒ retorno elegible |
| `madenat.guia.processing.line` | Línea de packing list | `lot_name`, `sku_original` (base del mapa lote↔packing) |
| `stock.lot` (`lot_flow_type`) | Etiqueta procesada (`tarja`/otro) y **Lote Volumen SV** (`volume`) | `volume_purchase_m3` = nominal |
| `madenat.sv.imputation` | **Cabecera** persistente por guía | `state`, `documentary_key`, inmutabilidad |
| `madenat.sv.imputation.line` | Etiqueta de retorno imputada | `processed_lot_id`, `nominal_volume_m3` |
| `madenat.sv.imputation.sv.line` | **Reparto N:M** etiqueta→SV | `sv_lot_id`, `imputed_volume_m3` |
| `madenat.sv.imputation.wizard` + `.line` + `.sv.line` | Asistente (transitorio) | no persiste el reparto; lo reconcilia al documento |
| `madenat.processor.return.link` | Conciliación envío↔retorno (I1/Bloque A-C) | se registra al aplicar |

### 3.2 Acciones y contrato

| Entrada UI | Método | Origen → Destino | Escribe | Efecto saldo |
| --- | --- | --- | --- | --- |
| Menú **Logística → Rebaja de etiquetas** | `action_madenat_sv_assignment` | — → `stock.lot` volumen | — | sólo lectura |
| **Registrar rebaja** (desde SV) | `action_madenat_sv_imputation_wizard` (`target=current`) | — → asistente | — | — |
| Selección de guía | `_onchange_guia_processing_id` | — | reconstruye líneas del **trabajo** (draft/pending) | — |
| **Seleccionar todas / Quitar selección** | `action_select_all` / `action_clear_selection` | transitorio | sólo `selected`/reparto transitorio | ninguno |
| **Preparar asignación** | `action_assign_selected` | transitorio | filas de reparto a volumen 0 | ninguno |
| **Usar disponible** | `action_use_available` | transitorio | rellena filas en cero | ninguno |
| **Guardar borrador** | `action_prepare` → `_i2_build_imputation` | asistente → **draft** | cabecera+line+sv.line (upsert) | **reserva** etiqueta |
| **Dejar pendiente** | `action_pending` | draft → **pending** | estado | mantiene reserva |
| **Revisar y aplicar** | `action_apply` (wizard) → `action_apply` (doc) | draft/pending → **applied** | estado+snapshot+firma+auditoría | **consume** una vez |
| **Aplicar** / **Reversar** (doc) | `action_apply` / `action_reverse` | applied → **reversed** | estado+motivo+usuario+fecha | restituye una vez |
| **Anular** (doc) | `action_cancel` | draft/pending → **cancelled** | estado | **libera reserva** |
| Ver documentos que explican el saldo | `action_open_consuming_documents` / `action_open_no_availability_docs` | — → `madenat.sv.imputation` (sólo lectura) | — | — |

**Fuente de verdad de cada cantidad (separación transitorio/persistente):**
- **Transitorio:** `sv.imputation.wizard.*` (se pierde al cerrar; se reconstruye desde el documento).
- **Persistente:** `madenat.sv.imputation(.line/.sv.line)`; el wizard **no** es fuente.

### 3.3 `create` / `write` / `unlink` / ORM-RPC (blindaje)

- `create`/`write`/`unlink` de línea y sv.line **bloquean** si la imputación está `applied`.
- `write` de cabecera `applied`: **corregido** (AUD-ETQ-01) — sólo `state→reversed` con usuario.
- `unlink` de `applied`/`reversed`: prohibido (historia append-only).
- `@api.constrains`: etiqueta∈guía (D10), Σ reparto ≤ nominal (D10/D11), una sola imputación de
  trabajo por guía (D-I2-15), reparto en la misma imputación que su línea.


---

## 4. Matriz de estados y transiciones (extraída del código, no supuesta)

`madenat.sv.imputation.state` ∈ `{draft, pending, applied, reversed, cancelled}`.

| Estado | Persiste | ¿Reserva capacidad de etiqueta? | Editable | Acciones | Salida |
| --- | --- | --- | --- | --- | --- |
| **draft (BORRADOR)** | cabecera+line+sv.line | **Sí** (`I2_ACTIVE_STATES`) | sí (líneas/reparto) | `action_pending`, `action_cancel`, `action_apply` | pending/cancelled/applied |
| **pending (PENDIENTE)** | ídem | **Sí** (mantiene la reserva) | sí | `action_back_to_draft`, `action_cancel`, `action_apply` | draft/cancelled/applied |
| **applied (APLICADO)** | ídem + snapshot+hash+auditoría | **Consume** (Σ activos; techo duro) | **inmutable** | `action_reverse` | reversed |
| **reversed (REVERSADO)** | historia intacta | **No** (libera) | **no** | sólo consulta | — |
| **cancelled (ANULADO)** | historia intacta | **No** (libera) | **no** | sólo consulta | — |

**Cierre/cancelación del asistente (transitorio):** descartar el wizard **no** borra documentos ni
reservas persistidas; el reparto se reconstruye desde el documento en la próxima apertura
(`_i2_reconstruct_commands`). Cancelar el **documento** no aplicado (`action_cancel`) es distinto de
cerrar el formulario sin guardar y de corregir un aplicado (reversa).

---

## 5. Hallazgos (ID · severidad · causa · evidencia · impacto · solución · estado)

| ID | Sev. | Causa | Evidencia | Impacto | Solución | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| **AUD-ETQ-01** | Alta | `state` estaba en `I2_APPLIED_WRITABLE` ⇒ `write({'state':'draft'})` sobre `applied` liberaba capacidad y reescribía historia | `models/madenat_sv_imputation.py` (`I2_APPLIED_WRITABLE`, `write`) | Rompe append-only (AD-91); permite «des-aplicar» sin reversa | `state` fuera del conjunto libre; sólo `applied→reversed` con usuario; resto rechazado | ✅ Corregido + `test_aud_etq_01` |
| **AUD-ETQ-02** | Alta | `action_reverse` no exigía motivo (el modelo hermano `processor.return.link` sí) | `action_reverse`; comparación con `madenat_processor_return_link.py:540` | Reversa sin trazabilidad (§12/§16-R02) | Exigir `reversal_reason`/`reason` no vacío | ✅ Corregido + `test_aud_etq_02` |
| **AUD-ETQ-03** | Media | `_compute_packing_line` usaba `setdefault`: ante colisión elegía la 1.ª línea de packing | `_compute_packing_line` | Asociación arbitraria de material (§6/M01) | Clave colisionante = **ambigua** ⇒ asociación vacía | ✅ Corregido + `test_aud_etq_03` |
| **AUD-ETQ-04** | Alta | Aviso genérico «aplicado/reservado/sin capacidad» sin causa ni acceso a documentos | `no_availability_note`, `_compute_disponibilidad_estado`; captura de Mauricio | El usuario no puede explicar por qué una etiqueta no está disponible (§15) | `disponibilidad_detalle` concreta + `disponibilidad_imputacion_ids` + botones «Ver documentos» | ✅ Corregido + `test_aud_etq_04`/`04b` |
| **AUD-ETQ-05** | Baja | Verificación del contrato de cancelación | `action_cancel` + saldos | — | Acreditado (no era defecto) | ✅ Acreditado + `test_aud_etq_05`/`05b` |

**Hallazgo histórico (no reparado, §17):** etiquetas de la guía **19827** (id 1198) tienen
`stock.lot.lot_flow_type = NULL` (147 de 151 lotes de la base) y su imputación `IMP02220` (id 1189)
quedó **aplicada con 0 repartos SV**. **No** se repara (no autorizado); se documenta y se explican sus
consecuencias.


---

## 6. Auditoría de hardcodeo y supuestos ocultos

**Defectos confirmados:** AUD-ETQ-03 (reconstrucción de relación por **nombre concatenado** con
`setdefault` silencioso). Corregido (colisión ⇒ ambiguo).

**Dependencias frágiles (documentadas, NO cambiadas — fuera de alcance / política):**
- **Regla de promoción `name = lot_name + SKU + dígitos de la guía`** (`_i2_build_packing_map`): el
  mapa lote↔packing depende de que la promoción haya concatenado exactamente así. Datos que no sigan
  la regla quedan sin asociación (**comportamiento honesto**: se muestra vacío, no se inventa). Es una
  **dependencia frágil histórica**, no un ID fijo. **No** se cambia la promoción (fuera de alcance).
- **`_i2_processed_lots` = `guia.lot_ids` con `lot_flow_type != 'volume'`**: con `lot_flow_type=NULL`
  (147/151 lotes de la base) el predicado es **verdadero** (None ≠ 'volume'), por lo que la etiqueta
  **sí** se lista. Riesgo: si apareciera un `lot_flow_type` con valor distinto no previsto, también se
  listaría. Es tolerante, pero conviene normalizar el dato (ver §17).

**Constantes/valores legítimos (NO defectos):**
- Precisión `I2_VOLUME_PRECISION = 0.001` (alineada con `digits=(16,3)`).
- Namespaces de advisory lock `2` (SV) y `3` (etiqueta) — orden determinista deliberado.
- Grupos funcionales existentes (`group_madenat_operaciones/jefatura/gerencia`).
- `documentary_key = 'IMP-<guia_id>-<hash>'` — clave documental propia (sin `picking_id`), por diseño.

**No se hallaron** IDs fijos de lotes/guías/usuarios/compañías/ubicaciones en la lógica productiva del
flujo; tampoco SQL directo, commits manuales, `except: pass`, ni selección del «primer registro» como
fallback silencioso (salvo el `setdefault` corregido). No se hallaron parámetros de contexto que omitan
validaciones de negocio: el dominio de UI **no** sustituye la validación de modelo (elección de guía,
pertenencia etiqueta–guía y techo duro se revalidan en el modelo al aplicar).

---

## 7. Fórmulas reales e invariantes (verificadas en código)

| Magnitud | Fórmula (`@api.model`) | Estados que participan |
| --- | --- | --- |
| Nominal etiqueta | `_i2_lot_nominal_m3` = `volume_purchase_m3 or volumen_m3` | — |
| Activo etiqueta (techo duro) | `_i2_lot_active_imputed_m3` = Σ `nominal_volume_m3` de líneas | `draft`/`pending`/`applied` |
| Aplicado etiqueta | `_i2_lot_applied_m3` = Σ `nominal_volume_m3` | `applied` |
| Reservado etiqueta | `_i2_lot_reserved_m3` = Σ `nominal_volume_m3` | `draft`/`pending` |
| Disponible para esta operación | `_i2_lot_available_for_m3` = nominal − Σ activos (**excluye el documento en curso**) | activos |
| Saldo documental etiqueta | `_i2_lot_documental_available_m3` = nominal − Σ `applied` | `applied` |
| Nominal SV | `_i2_sv_nominal_m3` = `volume_purchase_m3 or volumen_m3` | — |
| Asignado SV | `_i2_sv_documental_assigned_m3` = Σ `imputed_volume_m3` | activos |
| Saldo documental SV | `_i2_sv_documental_available_m3` = nominal SV − Σ asignado activo | activos |
| Totales cabecera | `nominal_total_m3` = Σ líneas; `imputed_total_m3` = Σ repartos (N:M **sin** duplicar) | — |

**Caso obligatorio (nominal 5 m³, reparto 3 m³):** la etiqueta entra en un documento con
`nominal_volume_m3 = 5` (nominal **comprometido**), y su reparto al SV es 3 m³. Al **guardar** (draft) el
`nominal` **activo** de la etiqueta es **5** ⇒ `disponible = 0`: los **2 m³ restantes quedan
reservados** y **no** pueden usarse en otra operación mientras el documento esté activo. **Anular**
(`cancelled`) libera **los 5**; **revertir** (si estaba `applied`) restituye **los 5**. El reparto al SV
(3) es una magnitud **distinta** (SV-side) y no «devuelve» 2 m³ a la etiqueta. ⇒ `nominal comprometido
≠ reparto aplicado ≠ disponible`. (Es la política documentada §19.16.2; se aclara, no se cambia.)

**Invariantes acreditadas por pruebas:** sin exceso de capacidad (techo duro etiqueta-side; blando
SV-side con motivo); sin saldo negativo no justificado; sin doble consumo (idempotencia de `apply` y
`documentary_key`); sin doble liberación (transiciones de estado no repetibles); sin efecto aplicado
desde un `onchange` (el `onchange` sólo reconstruye/representa); sin acumulación por repetir botones
(`action_assign_selected` no duplica, `_i2_build_imputation` hace **upsert**); sin suma aditiva de
nominal/saldo del mismo SV por fila (totales desde `sv_line_ids`, N:M sin duplicar).

---

## 8. Ciclo completo de ejemplo (documentos y balances)

Sobre datos **transaccionales** de prueba (no históricos). Estados y saldos documentales:

| Paso | Documento | Estado | Σ activo etiqueta | Disponible etiqueta | Saldo documental SV |
| --- | --- | --- | --- | --- | --- |
| Inicio | — | — | 0 | 10.000 | 100.000 |
| Guardar borrador | IMP-n (draft) | draft | 10.000 (reserva) | **0.000** | 100.000 |
| Dejar pendiente | IMP-n | pending | 10.000 | 0.000 | 100.000 |
| Aplicar | IMP-n | applied | 10.000 | 0.000 | 90.000 (**−10**) |
| Reversar | IMP-n | reversed | 0 | 10.000 | 100.000 (+10) |
| Reasignar (nueva) | IMP-m | draft→applied | 10.000 | 0.000 | (según destino) |
| Anular borrador | IMP-x | cancelled | 0 | 10.000 | (sin cambio) |

Equivalencia verificada por pruebas existentes + nuevas: `test_sv_imputation_i2.T08` (reversa restituye),
`test_sv_rebaja_operativa.REV-01`, `test_processor_return_link.T14/T15` (reversa + reimputación),
`test_aud_etq_04/05` (causa y cancelación). **Aplicado→revertido→reasignado→aplicado** se explica con
documentos: el reversado conserva `line/sv.line`, y la nueva imputación es un documento nuevo que
referencia los mismos lotes (historia **append-only**; el original **no** se sobrescribe).


---

## 9. Cancelación, reservas y ciclo del asistente

- **Cerrar/cancelar el formulario sin guardar** (botón `special="cancel"` o descartar el wizard): no
  crea documento ni reserva; el transitorio se descarta. **No** equivale a anular el documento.
- **Anular un documento no aplicado** (`action_cancel`, draft/pending): pasa a `cancelled` ⇒ **libera
  exactamente su reserva** (Σ activos baja). Repetir `action_cancel` **no** produce efecto adicional
  (rechaza; el saldo no cambia). Acreditado por `test_aud_etq_05`.
- **Corregir un documento aplicado**: **sólo por reversa** (`action_reverse`, Jefatura/Gerencia). El
  aplicado **no** vuelve a borrador (AUD-ETQ-01). Acreditado por `test_aud_etq_05b`.
- **Reservas persistentes vs. transitorias:** la reserva vive en `madenat.sv.imputation(.line)` en
  estados `draft`/`pending`; el wizard **no** es reserva. La limpieza del `TransientModel` **no** borra
  rebajas aplicadas, no deja reservas huérfanas y no pierde repartos persistentes.
- **Reconstrucción sin duplicados:** `_i2_reconstruct_commands` + `create()` que fija `wizard_id` a los
  repartos huérfanos evita relaciones huérfanas; `_i2_build_imputation` reconcilia por
  `processed_lot_id` y `(línea, SV)` (**upsert**), sin borrar-y-recrear.
- **`cantidad_asignar_m3` (compute/inverse):** la cantidad principal representa el **SV de trabajo**;
  poner a cero **sólo** borra la fila de ese SV y **no** toca repartos a otros SV
  (`_inverse_cantidad_asignar`). Acreditado por `test_asg_05`, `test_edit_02`.

---

## 10. Concurrencia, seguridad e idempotencia

- **Idempotencia:** `action_apply` sobre `applied` es **no-op** (no duplica cabecera/líneas/auditoría).
  `documentary_key` evita duplicar el documento de trabajo. Doble clic/repetición no crea segunda rebaja.
- **Atomicidad:** las validaciones de `action_apply` (permiso, destino Sí, payload, techo duro) se
  ejecutan **antes** de escribir estado; un error deja el documento en `draft` sin snapshot ni fecha
  (acreditado `RET-SEC02`). No hay commits manuales; no hay `except` que continúe con documento parcial.
- **Concurrencia:** `_i2_lock_resources` toma advisory locks **de transacción** (`pg_try_advisory_xact_lock`)
  en orden global determinista (etiqueta ns=3, SV ns=2) **antes** de revalidar techos; si otra
  transacción posee el lock, falla de forma **controlada**. Probado reteniendo el lock en una sesión
  (`test_con_01`). **Prueba con dos cursores simultáneos: PENDIENTE** (no acreditada aquí).
- **Seguridad (backend, no sólo UI):** `action_apply` exige Operaciones/Jefatura/Gerencia
  (`AccessError` demostrado `I2-T10`, `SEC-02`); `action_reverse` exige Jefatura/Gerencia (`NAV-09`).
  `action_cancel`/`action_pending`/`action_back_to_draft` se apoyan en el **ACL** (sólo Oper/Jef/Ger
  tienen `write`; contabilidad/auditoría lectura). Escritura/unlink directos sobre `applied` están
  bloqueados por el modelo. **Sin reglas de registro multi-compañía** para `madenat.sv.imputation`
  (sólo por grupo): ver §16 (pendiente de decisión).

---

## 11. Ausencia de efectos físicos

Clasificación previa de campos: `sv_available_m3` y el ledger `madenat.sv.operation` **no** participan
en I2 (magnitud documental propia). Medido antes/después en las pruebas `PHY-01` (existentes) y en la
regresión: `stock.move`, `stock.move.line`, `stock.quant` y `stock.picking` **no cambian** al
guardar/aplicar/cancelar/revertir. I2 **no** crea movimientos físicos (diseño D-I2-12). No se ampliaron
pruebas a flujos físicos ajenos.

---

## 12. Pruebas y regresión

| Conjunto | Comando (contenedor `odoo18_app`, base `madenat_test`) | Resultado |
| --- | --- | --- |
| **Dirigidas AUD-ETQ** | `odoo -d madenat_test -u madenat_lumber_logistics --test-enable --stop-after-init --no-http --http-port=8071 --test-tags /madenat_lumber_logistics:TestSvRebajaBlindaje` | **0 failed / 0 errors of 7** (`logs/test_blindaje.log`, EXIT=0) |
| **Regresión de módulo** | ídem con `--test-tags /madenat_lumber_logistics` | **4 failed / 0 errors of 369** (`logs/regression.log`, EXIT=1) |

Las **4 fallas** son **exactamente** las preexistentes declaradas en
`FASES/IMPL_SV_REBAJA_OPERATIVA_20261010/README.md` (corrida de referencia: `4 failed, 0 error(s) of 318`):
`test_processor_locations.test_09_auditoria_envio_normal`,
`test_processor_shipment_ad89.test_t1_envio_manual_parcial_sin_motivo`,
`...test_t5_desviacion_real_no_aplica_en_i1`, `...test_t6_idempotencia` ⇒ **0 fallas nuevas, 0 errores**.
El conteo pasó de 318→369 por el trabajo local intermedio (FIX_SV_SELECCIONAR_TODAS, UI_LIMPIA_SV,
HOTFIX_OWL) + **7 pruebas nuevas** de esta intervención.

---

## 13. Evidencia de navegador o límite explícito

**No hay navegador en el entorno.** No se declara renderizado aprobado. La verificación del asistente
es **ORM + XML + pruebas** (incl. `test_owl_*` y `test_arch_*`, que leen el `arch` de las vistas). La
aceptación operativa final (recorrido «seleccionar → asignar → guardar → reabrir → revisar → aplicar →
consultar → cancelar/revertir → reasignar») queda **pendiente de la validación de Mauricio en navegador**.


---

## 14. Correcciones, archivos y diff

| Archivo | Cambio |
| --- | --- |
| `models/madenat_sv_imputation.py` | AUD-ETQ-01 (`I2_APPLIED_WRITABLE` sin `state` + `write` con transición controlada); AUD-ETQ-02 (motivo obligatorio en `action_reverse`) |
| `wizards/madenat_sv_imputation_wizard.py` | AUD-ETQ-03 (`_i2_build_packing_map`, colisión ambigua); AUD-ETQ-04 (`disponibilidad_detalle`, `disponibilidad_imputacion_ids`, `disponibilidad_documentos_count`, `action_open_consuming_documents`, `action_open_no_availability_docs`, nota concreta, `@api.depends`); related `disponibilidad_detalle` en `.sv.line` |
| `wizards/madenat_sv_imputation_wizard_views.xml` | columna «Causa del saldo» + botón «Ver documentos» por fila; botón «Ver documentos que explican el saldo» en el alert; causa en pestaña Asignación a SV |
| `tests/test_sv_rebaja_blindaje.py` | **Nuevo** (AUD-ETQ-01..05, 7 pruebas) |
| `tests/__init__.py` | registro del test nuevo |
| `tests/test_sv_imputation_i2.py`, `test_sv_imputation_candidates.py`, `test_service_return_imputation_guard.py`, `test_processor_return_link.py`, `test_sv_rebaja_operativa.py` | motivo de reversa en los llamados existentes a `action_reverse` (política corregida) |
| `__manifest__.py` | versión `18.0.1.14.1 → 18.0.1.15.0` |
| `CHANGELOG.md` | entrada `[18.0.1.15.0]` |

Diff **neto de esta intervención**: `code/net_aud_etq.diff` (diff contra el snapshot previo
`code/modules_pre.tar.gz`; 12 archivos). El diff local acumulado del módulo (incluye WIP previo
preservado) está en `code/diff_aud_etq.diff`. Sin `reset`, `clean`, `stash`, `add`, `commit` ni `push`.
Cambios locales ajenos **preservados** (`code/status_pre.txt` / `code/status_after.txt`).

---

## 15. Versión local y documentación

- Módulo actualizado **sólo** `madenat_lumber_logistics` en `madenat_test`:
  `odoo -d madenat_test -u madenat_lumber_logistics --stop-after-init --no-http` → EXIT=0,
  «Modules loaded» (`logs/update.log`). Versión aplicada: **18.0.1.15.0**. Sin `-u all`.
- Documentación actualizada en `madenat_lumber_docs/CANON/` (19 §19.20 nueva; 02; 03; 05; índice).
- Evidencia centralizada en este expediente, sin crear una segunda fuente canónica: la doctrina sigue
  en `CANON/`.


---

## 16. Rastreo del caso reportado (captura: disponibilidad 0) y anomalías históricas

**Lectura real de `madenat_test` (sólo lectura):**
- `madenat.sv.imputation`: **2** documentos.
  - `492 / IMP00946` — guía `32300` — **applied** (2026-10-03), 1 línea (lote 15894, nominal 10) y
    reparto a `SV00000001175` (10).
  - `1189 / IMP02220` — guía **`1198 / «19827»`** — **applied** (2026-10-10 22:30:45), **2 líneas**
    (lotes `18368` nominal 3.263; `18372` nominal 4.225) y **0 repartos SV**.
- `stock.lot`: `D7632 PCLAT04201252900 19827`, `D7642 PCLAT04201453700 19827`, con
  `lot_flow_type = NULL` (¡no `'tarja'`!).
- `madenat_audit_log`: `imputation` para IMP00946 e IMP02220 (usuario 8); **sin** `imputation_reverse`.

**Causa concreta de la captura (demostrada):** la etiqueta pertenece a la guía **19827**, cuya
capacidad ya fue **consumida** por la imputación **aplicada IMP02220**. Al reabrir el asistente no hay
documento de trabajo (draft/pending) ⇒ las líneas se listan sin selección y con `disponible = 0`. El
aviso era **genérico**. Con AUD-ETQ-04, la interfaz ahora **nombra** el documento
(`IMP02220 (aplicada, 3.263 m³)`) y **enlaza** al documento que explica el saldo. La captura era
**saldo correcto con explicación insuficiente** — el defecto corregido.

**Anomalías históricas (NO reparadas — requieren autorización):**
1. `IMP02220` aplicada con **0 repartos SV**: consumió la capacidad de 2 etiquetas sin destino SV.
   *(Política vigente: `NO_SV_CANDIDATE` sólo se marca si NO hay candidato; con candidatos y sin
   asignación no se advierte. → decisión pendiente.)*
2. `lot_flow_type = NULL` en 147/151 lotes.

**Propuesta de reparación (dry-run, idempotente, NO ejecutada):** normalizar `lot_flow_type` NULL y,
para IMP02220, **reversa trazable** (acción existente, con motivo) + nueva imputación con reparto,
**sólo con respaldo y autorización de Mauricio**. Separar **corrección de código** (hecha) de
**reparación de datos** (pendiente).

---

## 17. Pendientes y decisiones que requieren autorización

1. **¿Una imputación aplicada con etiquetas pero SIN reparto SV debe advertir/bloquear cuando SÍ hay
   candidatos SV?** Hoy se permite en silencio. Política ambigua → **no** se cambió. Propuesta:
   desviación blanda `I2-LABELS-WITHOUT-REPARTO` (motivo + auditoría).
2. **Reglas de registro multi-compañía** para `madenat.sv.imputation` (hoy sólo ACL por grupo).
3. **Motivo obligatorio de reversa:** se aplicó el criterio del hermano `processor.return.link`. Si la
   política de I2 difiere, revertir (afecta 5 archivos de pruebas).
4. **Prueba de concurrencia real** con dos cursores simultáneos.
5. **Renderización/navegador (V3)** y recorrido de aceptación de Mauricio.
6. **Reparación histórica** (§16): dry-run + respaldo + aprobación.

---

## 18. Propuesta de commit (NO ejecutado)

```
feat(sv-rebaja): blindaje del ciclo documental de etiquetas (AUD-ETQ-01..05)

- AUD-ETQ-01: inmutable real applied (state sólo -> reversed vía action_reverse)
- AUD-ETQ-02: reversa exige motivo (trazabilidad, AD-91)
- AUD-ETQ-03: mapa lote<->packing sin elección arbitraria ante colisión
- AUD-ETQ-04: causa del saldo concreta + acceso a los documentos que la explican
- tests: test_sv_rebaja_blindaje (7) + reason en llamados de reversa existentes
- version 18.0.1.14.1 -> 18.0.1.15.0
```

**Sin COMMIT · sin PUSH · sin despliegue remoto · sin reparación histórica no autorizada.**


---

# CIERRE PROBATORIO (2026-10-11, 2.ª sesión) — AUD-ETQ-06..10

**Dictamen final: COMPLETO TÉCNICAMENTE; ACEPTACIÓN DEL USUARIO PENDIENTE.**
Concurrencia real, seguridad multi-compañía, inmutabilidad/reversa, ciclos con balances y diagnóstico de
IMP02220 cerrados con pruebas. Queda **bloqueada por decisión de negocio** una única cuestión (contrato de
«aplicación sin reparto», §CI-3) y **pendiente V3 (navegador)**. Módulo **18.0.1.15.0 → 18.0.1.16.0**.

## CI-1. Baseline y respaldo
- Rama `feat/guia-correccion-documental-preservada-20261002`, HEAD `b1d2d19`; WIP local preservado.
- Respaldo real antes de esta sesión: `code_cierre/modules_pre_cierre.tar.gz` (`gzip -t` OK) y
  `db_cierre/madenat_test_pre_cierre.dump` (`pg_restore` OK, `-Fc`).

## CI-2. IMP02220 — diagnóstico documental (NO reparado)
`id=1189`, guía **1198/«19827»**, aplicado por usuario 8 el **2026-10-10 22:30:45** (una transacción),
2 líneas (`18368` 3.263 + `18372` 4.225 = **7.488 m³** nominal), **0 repartos SV**, sin reversa.
`documentary_key = IMP-1198-E95825AAF94E58AD` == `_i2_build_documentary_key(1198, None, '')` ⇒ creado por
el **camino normal del asistente** con **firma vacía** (sin asignación a SV al aplicar); sin auditoría
`deviation`.

| Pregunta | Respuesta verificada |
| --- | --- |
| **A. ¿Modalidad válida?** | El código **la tolera** pero **no hay regla explícita**; `NO_SV_CANDIDATE` sólo actúa si **no hay** candidato (aquí sí había: SV…1175 saldo 30.315 y SV…841 saldo 40.315) ⇒ **tolerada, no documentada** |
| **B. ¿Rebajó saldo SV?** | **No** (Σ reparto = 0) |
| **C. ¿Comprometió capacidad sin destino?** | **Sí** (7.488 m³ nominales; disponible 0 en 2 etiquetas) |
| **D. ¿Válido/incompleto/anomalía?** | **Válido según el código, funcionalmente incompleto** (sin destino SV), **no corrupción**; **sin evidencia** de reparto borrado |

`lot_flow_type=NULL` (147/151 lotes) = **anomalía de datos independiente**, **sin relación causal
demostrada** con IMP02220. **No** se modifica IMP02220 ni `lot_flow_type`.

## CI-3. Contrato de «aplicación sin reparto» — BLOQUEADO (decisión requerida)
No está definido (canon ni código) si aplicar etiquetas sin destino SV **existiendo candidatos** debe
rechazarse, advertirse con motivo, o permitirse como compromiso. Alternativas: (a) rechazar; (b) desviación
blanda `I2-LABELS-WITHOUT-REPARTO` (motivo + auditoría); (c) permitir y documentar el cierre posterior.
**No se adopta regla silenciosa**; requiere decisión de Mauricio.

## CI-4. Concurrencia REAL (cursores independientes + barrera)
Sonda `evidence/concurrency_probe.py` (2 transacciones simultáneas por caso con `threading.Barrier`):

| Caso | Resultado tx | Efecto final |
| --- | --- | --- |
| **Q1** doble aplicación misma etiqueta | A=OK, B=`UserError` (advisory lock) | **1** aplicado; Σ activo 10 = nominal (**sin sobreconsumo**) |
| **Q2** doble reversa mismo aplicado | A=OK, B=serialization failure | estado `reversed`; **1** auditoría (sin doble restitución) |
| **Q3** aplicar ∥ cancelar reserva | A=OK, B=`UserError` (techo duro) | Σ activo ≤ nominal (**sin sobreconsumo**) |

`stock.move/move.line/picking/quant` **sin cambios**; **0 residuos**. **RESULTADO GLOBAL: OK** (EXIT=0).
Evidencia: `logs_cierre/concurrency.log`.

## CI-5. Seguridad multi-compañía (sin `sudo`)
Exposición confirmada: **no existía** `ir.rule` para `madenat.sv.imputation*` (sólo ACL por grupo).
Corrección dentro de la política vigente (patrón del hermano `madenat.processor.return.link` y de
`stock.lot`): nueva `security/madenat_sv_imputation_rules.xml` (3 reglas globales de compañía). Probado con
usuario no administrador de otra compañía: `search` no expone; `read/write/unlink/apply/cancel/reverse` →
`AccessError`; contexto forzado **no** autoriza; lotes ajenos bloqueados. `test_aud_etq_07`.

## CI-6. Inmutabilidad y reversa
Inmutabilidad profunda (`write`/`unlink`/`create` sobre líneas y repartos del aplicado y `unlink` del
aplicado) → `UserError` (`test_aud_etq_08`). Reversa: motivo vacío/espacios → `UserError` (corregido:
`strip`); trazabilidad usuario/fecha/motivo/auditoría; repetida sin doble efecto; sin permiso y contexto
forzado → `AccessError` (`test_aud_etq_06`/`06b`).

## CI-7. Ciclos con balances (datos de prueba)
- **A**: preparar→guardar→reabrir→cancelar (libera)→reasignar→aplicar (2 SV) — `test_aud_etq_09a`.
- **B**: preparar→aplicar→revertir (restituye)→reasignar→aplicar; original `reversed` + nuevo `applied`
  — `test_aud_etq_09b`.
- **Parcial 5/3**: nominal comprometido (disponible 0); los 2 m³ **no** reutilizables; los libera
  anular/revertir — `test_aud_etq_10`. Sin efectos físicos — `test_aud_etq_09c`.

## CI-8. Regresión y pruebas
- Dirigidas `TestSvRebajaCierre`: **0 failed / 0 errors of 8** (`logs_cierre/test_cierre.log`, EXIT=0).
- Regresión módulo: **4 failed / 0 errors of 377** (`logs_cierre/regression.log`, EXIT=1); las 4 son las
  **mismas** preexistentes (`test_processor_locations.test_09`,
  `test_processor_shipment_ad89.test_t1/t5/t6`) ⇒ **0 fallas nuevas**. Baseline comparable declarado
  (corridas previas del expediente: 318 y 369 pruebas).

## CI-9. Cambios
`security/madenat_sv_imputation_rules.xml` (nuevo), `models/madenat_sv_imputation.py` (strip motivo),
`tests/test_sv_rebaja_cierre.py` (nuevo), `tests/__init__.py`, `__manifest__.py` (16.0), `CHANGELOG.md`;
docs CANON/19 §19.22, 02 §17.16.20, 03 §24, índice. Diff neto: `code_cierre/net_cierre.diff`.
**Sin commit / push / despliegue / reparación histórica.**

