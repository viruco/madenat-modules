# RUNBOOK — DESPLIEGUE AL TEST REMOTO (MADENAT · Odoo 18 CE)

**Versión:** 1.0 · **Fecha:** 2026-10-15 · **Redactado por:** FASE 6 (solo redacción — **NO ejecutado**)
**Origen:** HEAD local `ed42df5` (rama `feat/guia-correccion-documental-preservada-20261002`)
**Estado:** BORRADOR REVISABLE. No ejecutar sin completar §1 y §2.

> Este runbook es un **procedimiento genérico**: usa marcadores `<...>` para hosts, rutas, usuarios y
> puertos. **No** contiene credenciales, **no** se ha probado contra el remoto y **no** autoriza por sí
> mismo ninguna acción.

---

## 0. ESTADO REAL TRAS LA FASE 8 (leer antes de nada)

Actualizado el **2026-10-15** con los resultados de la FASE 8 (M1/M2 + verificación A/B). Sustituye a los
estados de FASE 6 y FASE 7.

**Commits a desplegar (rama `feat/guia-correccion-documental-preservada-20261002`):**

| Commit | Tipo | Qué aporta |
|---|---|---|
| `bfda876` | `fix(core)` | Alinea la prueba de duplicados con la identidad por modelo (**D18-1**). Solo test |
| `56405cb` | `feat(logistics)` | Asistente de rebaja por nave + motivo de reversa (**D18-2/3/4/5**); **18.0.1.28.0** |
| `c4935ed` | `fix(intake)` | Orden de la acción «Nuevo Ingreso» (**K2**): habilita la instalación desde cero de `intake` |
| `2985768` | `docs(canon)` | **AD-107** |
| **`7d277e9`** | `fix(logistics)` | **M1**: `<menuitem>` del menú de imputaciones restituido ⇒ **instalación desde cero de `logistics`**; **18.0.1.29.0** |
| **`7c417ae`** | `test(core)` | **M2**: la prueba de longitudes usa `product.product` |
| **`677294b`** | `docs(canon)` | **AD-108** |

**Estado verificado el 2026-10-15 (FASE 8):**

1. **Instalación desde cero: DEMOSTRADA (DR).** `-i madenat_lumber_shipping_core,madenat_lumber_core,madenat_lumber_logistics,madenat_lumber_intake`
   en base limpia ⇒ **`exit 0`**; los 4 módulos cargan (`logistics` 4.70 s). *(En la FASE 7 `logistics` fallaba
   con `NotNullViolation … ir_ui_menu`: era el defecto M1, ya corregido.)*
2. **Camino `-u`: funciona.** `-u` de los 4 módulos con el código entregado ⇒ `Registry loaded`, sin errores de
   carga, `1 failed + 4 error de 1314` de los cuales **4 son del baseline** y 1 depende de datos del dump.
   En conjunto (A∩B): **4 fallas del baseline y 0 nuevas atribuibles** al código entregado.
3. **Hallazgo nuevo y relevante para el despliegue: la configuración NO se reproduce en un alta limpia.**
   Una base nueva no trae la precisión decimal (`Product Unit of Measure` 2 vs **4**; `Product Price` 2 vs **3**),
   el catálogo de productos ni los parámetros `madenat.*` (`allow_product_creation`, `allow_subproduct_creation`,
   `omission_threshold`, umbrales de varianza) de `madenat_test`. **Declarar/seedear el juego mínimo** antes de
   dar por buena una base nueva (afecta a cálculos y a varias suites).
4. **D1 `costing` y P2-2 (menú de `reports`): FUERA** por decisión. `costing` está **bloqueado** para commit y
   despliegue; `reports` depende de él ⇒ no se despliega.
5. **Prueba dependiente del destino:** `TestServiceReturnImputationGuard.test_09…` exige que el usuario real
   Cristhian tenga Jefatura/Gerencia; si no la tiene, falla con `AccessError`.
6. **Despliegue sobre una base con estado-WIP: PRECAUCIÓN** (sigue vigente §3.8): si el destino tiene la vista de
   `costing` guardada con `action_apply_c2` (solo existe en el WIP, **no commiteado**), el `-u` falla con
   `ParseError`. **Comprobar antes** (§3.8).




---

## 1. PRECONDICIONES

| # | Precondición | Criterio de cumplimiento |
|---|---|---|
| 1.1 | **D18 cerrado** (commit de cierre de `logistics`: `wizards/lumber_shipment_rebaja_wizard.py{,_views}.xml` + las 2 pruebas D18) y **verificado en clon limpio** | `-i`/`-u` de `madenat_lumber_logistics` sin error de XML-ID |
| 1.2 | **P2-2 decidido** (menú `menu_lumber_reports_root`): desplegar, mantener fuera o revertir | Decisión escrita de Mauricio |
| 1.3 | HEAD verificado (instalación desde cero + suites en base temporal) | Informe de FASE 6 · V1 |
| 1.4 | Respaldo **del entorno remoto** ejecutado y verificado (§2) | Dump restaurable + filestore + código |
| 1.5 | Ventana de mantenimiento acordada y **usuario final avisado** | Ventana `<fecha y hora>` |
| 1.6 | Responsable de la ejecución y del rollback designados | `<persona>` / `<persona>` |
| 1.7 | Navegador disponible para la validación manual VIEW-01/04 | `<estación>` |

**Fuera de alcance del despliegue (ver §10).**

---

## 2. RESPALDO PREVIO DEL ENTORNO REMOTO

Ejecutar **en el host remoto**, dentro de la ventana, antes de tocar código:

1. **Base de datos** (formato personalizado, comprimido):
   ```bash
   pg_dump -Fc -h <host> -p <puerto> -U <usuario> <base_remota> \
     > <ruta_respaldos>/<base_remota>_pre_<AAAAMMDD_HHMM>.dump
   pg_restore --list <ruta_respaldos>/<base_remota>_pre_<AAAAMMDD_HHMM>.dump | wc -l   # > 0
   ```
2. **Filestore** (adjuntos): empaquetar el directorio de datos de la instancia
   ```bash
   tar -czf <ruta_respaldos>/filestore_pre_<AAAAMMDD_HHMM>.tar.gz -C <data_dir>/filestore <base_remota>
   gzip -t <ruta_respaldos>/filestore_pre_<AAAAMMDD_HHMM>.tar.gz
   ```
3. **Código desplegado** (lo que se va a sustituir):
   ```bash
   git -C <ruta_addons_remota> rev-parse HEAD > <ruta_respaldos>/head_remoto_pre.txt
   tar -czf <ruta_respaldos>/addons_pre_<AAAAMMDD_HHMM>.tar.gz -C <ruta_addons_remota> madenat_lumber_core madenat_lumber_intake madenat_lumber_logistics madenat_lumber_shipping_core
   ```
4. **Manifiesto de integridad** (`sha256sum` de los 3 artefactos) y verificación `gzip -t` / `pg_restore --list`.
5. **Registrar** en `<ruta_respaldos>/README_<AAAAMMDD>.md`: fecha, autor, HEAD previo, rutas y hashes.

---

## 3. VERIFICACIÓN EN REMOTO **ANTES** DE ACTUALIZAR (solo lectura)

| # | Qué mirar | Cómo | Qué se espera |
|---|---|---|---|
| 3.1 | Rama/commit desplegado | `git -C <ruta_addons_remota> rev-parse HEAD` y `--abbrev-ref HEAD` | Distinto de `ed42df5` ⇒ habrá cambios que entregar |
| 3.2 | Versiones de módulos instaladas | `SELECT name, latest_version, state FROM ir_module_module WHERE name LIKE 'madenat%' ORDER BY name;` | `core 18.0.6.x`, `logistics 18.0.1.x`, `intake 18.0.0.x`, `shipping_core 18.0.1.0.0` |
| 3.3 | Vistas de `shipping_core` (posible XML corrupto heredado) | `SELECT arch_db FROM ir_ui_view WHERE id = (SELECT res_id FROM ir_model_data WHERE module='madenat_lumber_shipping_core' AND name='view_shipping_vessel_form');` | Buscar el literal **`hatter/>`**; si aparece, el remoto arrastra el defecto y el commit ③ lo corrige |
| 3.4 | Módulos instalados | `SELECT name FROM ir_module_module WHERE state='installed' AND name LIKE 'madenat%';` | Confirmar que `madenat_lumber_reports` / `costing` **no** entrarán en el `-u` |
| 3.5 | ¿Existe `costing`? | `SELECT state, latest_version FROM ir_module_module WHERE name='madenat_lumber_costing';` | Instalado ⇒ **no** actualizarlo (D1 bloqueado) |
| 3.6 | Usuarios y grupos de prueba | `SELECT login, active FROM res_users WHERE login LIKE '%@madenat.test';` | 3 inactivos (decisión AD-106: conservar) |
| 3.7 | Cron / jobs activos | `SELECT count(*) FROM ir_cron WHERE active;` | Anotar para el humo post-actualización |
| **3.8** | **Vistas almacenadas que referencian métodos ausentes del código a entregar** (crítico tras la FASE 7) | `SELECT id, key FROM ir_ui_view WHERE arch_db::text LIKE '%action_apply_c2%';` (y, en general, buscar en `arch_db` los `name="action_…"` que el código a desplegar **no** defina) | **0 filas** esperadas. Si hay filas: la vista llegó del WIP de `costing` (D1) y el `-u` **fallará**; hay que resolver D1 o ajustar la vista en el destino **antes** de actualizar |

**No** modificar nada en este paso.

---

## 4. ENTREGA DEL CÓDIGO

1. **Comparar** lo desplegado con `ed42df5` (o con el HEAD de cierre que resulte de D18):
   `git -C <ruta_addons_remota> log --oneline -5` + `diff -rq` de los 4 módulos.
2. **Mecanismo de sincronización** (elegir uno, documentado):
   - `git fetch` desde el remoto de trabajo **solo si** está autorizado y el remoto tiene la rama; o
   - copia controlada (`rsync`/`tar`) del árbol **desde el commit verificado**, nunca desde el árbol de trabajo local con WIP.
3. **Exclusiones explícitas** (no copiar): `madenat_lumber_costing/**`, el menú de `reports`
   (`madenat_lumber_reports/views/lumber_reports_menu.xml`), y cualquier archivo del WIP local.
4. **Verificar** tras la copia: `sha256sum` de los 4 módulos contra el manifiesto del commit; y
   `git status` limpio en `<ruta_addons_remota>` (sin WIP).

---

## 5. ACTUALIZACIÓN DE MÓDULOS

**Orden por grafo de `depends`** (no alterar):

```
shipping_core  →  core  →  logistics  →  intake
```

Comando (adaptar host/contenedor; **sin** `-u all`):

```bash
<odoo> -d <base_remota> \
  -u madenat_lumber_shipping_core,madenat_lumber_core,madenat_lumber_logistics,madenat_lumber_intake \
  --stop-after-init --max-cron-threads=0 \
  --logfile=<ruta_logs>/update_<AAAAMMDD_HHMM>.log
```

Notas:
- **Dependientes que correspondan:** `madenat_toll_processing`, `madenat_ingestion_engine`,
  `madenat_lumber_purchasing` y `madenat_lumber_reception_improvements` se actualizan automáticamente si
  el grafo lo exige; **no** añadir a mano los que no estén instalados.
- **`--max-cron-threads=0`** evita que los cron corran a mitad de la actualización.
- Si el entorno remoto usa contenedor: `<docker> exec <contenedor> odoo -d <base_remota> -u ...`.
- **Espera:** entre 2 y 6 minutos para estos 4 módulos en una base comparable a `madenat_test`.
- **Vigilar el log:** `ERROR`, `CRITICAL`, `External ID not found`, `ParseError`, `Failed to load`.
- **OBLIGATORIO: esta actualización es un `-u` sobre la base existente.** Una **instalación desde cero** no es
  posible en el HEAD actual (ver §0): fallaría en `madenat_lumber_logistics` (ACL, D18) y en
  `madenat_lumber_intake` (orden del XML, pre-existente). Tampoco es una vía válida para un DR.

**Resultado esperado en el log:** las 4 actualizaciones registradas y el proceso terminando con
`Initiating shutdown`. **No** se esperan errores de carga de vistas ni de ACL.

---

## 6. MIGRACIONES

| Cambio | ¿Requiere script? | Justificación |
|---|---|---|
| ACL de la bitácora (`access_madenat_audit_log_manager` `1,1,1,1` → `1,0,1,0`) | **No** | Solo cambia el CSV de seguridad; se re-aplica en el `-u` |
| Grupos de eliminación de guía (`GUIA_DELETE_GROUPS`, `_guia_delete_group_ok()`) | **No** | Constantes/funciones de código; **no** se crean grupos ni se amplían permisos de stock |
| `ir.rule` multi-compañía de la imputación SV (`security/madenat_sv_imputation_rules.xml`) | **No** | Datos XML nuevos (declarados en el manifest) |
| Inmutabilidad de `madenat.audit.log` (APPEND-ONLY) | **No** | Solo modelo + ACL. **No** borra ni reescribe bitácora existente |
| Versiones de módulo (`18.0.6.9.0` / `18.0.1.27.0` / `18.0.0.15.0`) | **No** | Sin scripts de migración en estos commits |
| `costing` / menú de `reports` | **N/A** | **No se despliegan** (ver §10) |

**Verificación post-`-u`:** `SELECT count(*) FROM madenat_audit_log;` debe ser **igual o mayor** que antes
(nunca menor) y `latest_version` debe coincidir con los manifests entregados.

---

## 7. HUMO FUNCIONAL (orden recomendado, ~20 min)

| # | Prueba | Resultado esperado |
|---|---|---|
| 7.1 | Abrir **Motonave** y **Viaje** (formularios con chatter) | Formulario abre sin `OwlError`; el botón «Ver Embarques de esta Motonave» solo **consulta** |
| 7.2 | Ingresar una guía **duplicada** por Procesado / Volúmenes / formulario | Aviso/bloqueo según política (homónimo entre flujos **no** bloquea; mismo modelo **sí**) |
| 7.3 | Eliminar una guía (botón nativo de lista/formulario) | **Bloqueado con mensaje** que guía al asistente |
| 7.4 | Eliminar una guía desde el **asistente de ciclo de vida** con motivo | Elimina y deja **registro** en la bitácora |
| 7.5 | Eliminar guía con usuario **Operaciones / Auditoría / `stock_manager` sin jefatura** | **Rechazado** (rol) |
| 7.6 | Eliminar guía con **Jefatura de Operaciones** (o sistema) y motivo | Permitido |
| 7.7 | Intentar borrar una guía con **lotes con existencias** (escenarios d/e/f/g) | **Bloqueado con mensaje de negocio** (sin error técnico de FK) |
| 7.8 | Rebaja de etiquetas SV: abrir «Registrar rebaja», aplicar y **reversar** | Sin `OwlError`; exige **motivo de reversa**; estado correcto |
| 7.9 | **Rebaja por nave** (si D18 se cerró y entró en el commit) | Selección nave/viaje + contenedores pendientes; resumen de éxitos/fallos |
| 7.10 | Modificar/borrar una fila de `madenat.audit.log` (ORM **y** `sudo`) | **Bloqueado** (`UserError` APPEND-ONLY) |
| 7.11 | **VIEW-01/04 en navegador:** «Agregar una línea» en el documento de imputación | Sin `OwlError`; «Mensajes/Seguidores» estándar |
| 7.12 | Menú de reportes: 📊 **Reportes y Listados** y acciones R1–R9 | Accesibles (el menú vacío 📈 queda como esté decidido en P2-2) |

**Evidencia:** captura de pantalla / log por cada punto; anotar hora y usuario.

---

## 8. CRITERIOS DE ABORTO Y REVERSA

### 8.1 Abortar el `-u` (no continuar / revertir de inmediato) si:

| # | Señal | Acción |
|---|---|---|
| A1 | `External ID not found` / `ParseError` en el log de actualización | **Detener**; restaurar código y base (§8.2) |
| A2 | `Failed to load registry` o el servicio no arranca | **Detener**; restaurar |
| A3 | Vistas clave (Motonave/Viaje, imputación) no abren | **Detener**; restaurar (probable caché de assets: reintentar tras reinicio limpio) |
| A4 | La bitácora aparece con **menos** filas que antes | **Detener** (viola APPEND-ONLY): restaurar base |
| A5 | Algún usuario queda sin acceso a menús operativos | **Detener**; evaluar P2-2 / grupos |
| A6 | Pérdida de datos operativos (guías/recepciones/lotes/imputaciones) | **Detener**; restaurar base |

### 8.2 Reversa (tiempo estimado: **10–25 min**)

1. **Código:** devolver los 4 módulos a lo respaldado
   `tar -xzf <ruta_respaldos>/addons_pre_<AAAAMMDD_HHMM>.tar.gz -C <ruta_addons_remota>` y confirmar
   `rev-parse HEAD` = `head_remoto_pre.txt`.
2. **Base:** si hubo corrupción funcional,
   `pg_restore --clean --if-exists -d <base_remota> <ruta_respaldos>/<base_remota>_pre_<AAAAMMDD_HHMM>.dump`.
3. **Filestore:** restaurar solo si faltan adjuntos.
4. **Reiniciar** el servicio y repetir §7.1/§7.4 para confirmar el retorno al estado previo.
5. **Registrar** en el informe: hora de aborto, señal detectada, artefactos usados.

> **Nota:** la actualización de módulos **no revierte** automáticamente los cambios de datos XML
> (`ir.rule`, ACL). Si se restaura solo el código sin la base, esas filas quedan aplicadas; por eso la
> reversa incluye el `pg_restore` cuando el fallo es funcional.

---

## 9. REGISTRO DE EVIDENCIA POSTERIOR

1. Logs íntegros del `-u` (sin credenciales) → `<ruta_logs>/`.
2. Salida de la verificación de versiones (§6).
3. Resultado de §7 con capturas (una por punto).
4. `SELECT name, latest_version FROM ir_module_module WHERE name LIKE 'madenat%';` (antes/después).
5. `SELECT count(*) FROM madenat_audit_log;` (antes/después) y `SELECT count(*) FROM madenat_guia_processing;`.
6. `git -C <ruta_addons_remota> rev-parse HEAD` (debe coincidir con el commit entregado).
7. Informe corto `<ruta_logs>/POST_DESPLIEGUE_<AAAAMMDD>.md` con: ventana, autor, resultado por punto,
   incidentes y pendientes.

---

## 10. LO QUE **NO** SE DESPLIEGA (lista explícita)

1. **`madenat_lumber_costing`** (D1/C2 bloqueado: versión sin subir, sin CHANGELOG; y su `.line` nuevo).
   *(Ojo: `reports` depende de `costing`; si el destino tiene `costing` con estado-WIP, ver §3.8.)*
2. **`madenat_lumber_reports/views/lumber_reports_menu.xml`** (P2-2 sin atribución documental).
3. **Cualquier archivo del WIP local** no commiteado (los 16 archivos del `git status` de trabajo).
4. **`madenat_lumber_billing`** y **`madenat_vendor_payment`** (sin cambios atribuidos a esta entrega;
   `vendor_payment` conserva `div.oe_chatter` en una vista **no** listada en su manifest).
5. **`madenat_lumber_core/_archive/**`** y `madenat_lumber_docs/LEGADO/**` (cuarentena; A2/A3 no aprobadas).
6. **Respaldos, dumps, filestore, `.tar.gz`, `__pycache__`** (nunca al repositorio ni al servidor de addons).
7. **Cambios de core de Odoo** (ninguno existe en esta entrega).

---

## 11. CHECKLIST RESUMIDA

- [ ] D18 cerrado y verificado en clon limpio · [ ] P2-2 decidido
- [ ] Respaldo remoto (dump + filestore + código) verificado
- [ ] Verificación previa remota (§3) registrada (incl. `hatter/>` en vistas heredadas)
- [ ] Código entregado **sin** costing y **sin** el menú de reports
- [ ] `-u shipping_core,core,logistics,intake` (sin `-u all`) ejecutado y log revisado
- [ ] Humo §7 completo, con evidencia
- [ ] Bitácora con filas ≥ antes · versiones = manifests entregados
- [ ] Informe posterior registrado (§9) · [ ] Pendientes traspasados


