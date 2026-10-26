# INFORME FASE 9 — VERIFICACIÓN PREVIA DEL TEST REMOTO (SOLO LECTURA) — **NO-GO**

**Proyecto:** MADENAT — Odoo 18 CE · **Fecha:** 2026-10-15
**HEAD local:** `677294b` (rama `feat/guia-correccion-documental-preservada-20261002`)
**Expediente:** `FASE9_VERIFICACION_REMOTO_20261015/`
**Alcance ejecutado:** R1 (búsqueda del mecanismo de acceso) → **STOP** conforme a R1.
**No se ejecutó ningún comando contra el remoto** (ni de escritura ni de lectura): no se contactó en ningún
momento. **No se ejecutó nada fuera de la lista cerrada** (la sección 3 no llegó a iniciarse).

---

## 0. RESUMEN EJECUTIVO

**Dictamen: NO-GO** — **bloqueado por R1**: el **mecanismo de acceso al TEST remoto está documentado** en el
proyecto (CANON/02:1001: `ubuntu@<IP>` · `/opt/odoo18-test` · servicio `odoo18-test` · base `madenat_test`,
«inspección **solo lectura**»), pero **sus credenciales no están configuradas en este entorno**:

| Comprobación (interna; hosts y credenciales NO se reproducen) | Resultado |
|---|---|
| `~/.ssh/config` | **1 alias**; su `User` **no** es `ubuntu` y su `HostName` **no** es la IP documentada del TEST remoto ⇒ **no es el acceso del proyecto** |
| `~/.ssh/known_hosts` (8 hosts) citados en la documentación del proyecto | **0 de 8** |
| Claves privadas en `~/.ssh` | 2 (`id_ed25519`, `id_ed25519_viruco`); ninguna declarada para el usuario del remoto documentado |
| `~/.pgpass` / `pg_service.conf` | **no existen** |
| Scripts de despliegue con transporte | `deploy_production.sh` y `validate_production.sh` son **locales** (0 líneas con ssh/rsync/scp/git) |
| Remotos git del repo | **1** (`origin`, GitHub del proyecto) — no es el servidor de TEST |
| Variables de entorno de acceso | **ninguna** |

⇒ Conforme a **R1** («si ese mecanismo no existe **o exige credenciales que no están configuradas**, DETENERSE
e informar; no buscar ni improvisar accesos»), **no se intentó ninguna conexión**: no se ejecutó `ssh`, `scp`,
`rsync`, `psql` remoto ni ningún comando de la sección 3. **NO-GO** hasta que Mauricio provea el acceso.

---

## 1. R1 — BÚSQUEDA DEL MECANISMO DE ACCESO (evidencia)

**Definido en la documentación del proyecto (dentro del repo):**
* `madenat_lumber_docs/CANON/02_CONTINUIDAD.md:1001` — tabla de entornos: «**TEST remoto** | `ubuntu@<IP>` ·
  `/opt/odoo18-test` · servicio `odoo18-test` (**active**) · base `madenat_test` | *Inspección **solo
  lectura*** …» (IP ocultada, conforme a la restricción de no reproducir hosts).
* Bloque siguiente del mismo apartado: «**Correspondencia de código local ↔ TEST remoto (medida)**. Manifiesto
  SHA-256 de **314 archivos** `.py/.xml/.csv` de `madenat_lumber_core`, `madenat_lumber_intake`,
  `madenat_lumber_logistics` …» ⇒ **ya existe metodología de comparación** (manifiesto por archivos).
* Otras secciones de CANON/02 y `WIKI/05_INCIDENTES/INC-010…` mencionan correcciones aplicadas en el
  «TEST remoto» **vía SSH** ⇒ el canal histórico fue **SSH**.
* El `RUNBOOK_DESPLIEGUE_TEST_REMOTO.md` (FASE 6, actualizado en FASE 8) usa **marcadores** `<host>`,
  `<usuario>`, `<puerto>`, `<ruta_addons_remota>`: **no** contiene un acceso concreto.

**No disponible en este entorno:** ninguna entrada de configuración ni credencial que utilice ese acceso
(§0). Además, el propio `CANON/02` anota que en la sesión de aquella auditoría el servicio local «**NO** era
operativo desde esa distro (`docker` no disponible)» ⇒ era **otro entorno de trabajo**.

**Conclusión de R1:** el mecanismo es *conocido* pero **no utilizable** desde aquí ⇒ **DETENERSE e informar**.

---

## 2. LO QUE NO SE PUDO OBTENER (sección 3 A–E) — motivo único: falta de acceso

| Apartado | Qué quedó pendiente | Por qué |
|---|---|---|
| **A. Código desplegado** | Ruta de `custom_addons` remota, ¿es git?, rama/HEAD/`git status`/`git log -5`; o (si no es git) SHA-256 de los módulos; tabla módulo → versión remota vs `677294b`; existencia y versión de `costing` y de `reports` | Sin acceso al host remoto |
| **B. Base de datos** | `ir_module_module` (estado/`latest_version`), vista con `action_apply_c2` y columnas de costing-C2, `hatter/>` en `arch_db`, menú `menu_madenat_sv_imputation` (existencia/`active`/`name`), miembros de Jefatura, parámetros `madenat.*`, precisión decimal, tipo de operación interna, catálogo de productos, bitácora y ACL del grupo de sistema | Sin sesión SQL remota |
| **C. Cruce de vistas (§3.8)** | Extracción de botones/acciones/campos de las vistas **activas del remoto** y comparación contra `677294b` | Requiere leer el **registro del remoto** |
| **D. Entorno** | Versión de Odoo/Python, servicio, gestor de procesos, disco, logs y backups (fecha), carga actual | Sin acceso |
| **E. Entrega del código** | Confirmar el canal real (pull git / rsync / otra vía) y si los commits locales estarían en `origin` | Sin acceso y **sin `fetch`** autorizado |

---

## 3. LO QUE SÍ SE ENTREGÓ (preparación LOCAL del cruce §3.C, sin tocar el remoto)

**3.1 Cruce estático del CÓDIGO LOCAL (`677294b`)** — botones `type="object"` de las vistas de datos frente a
los métodos definidos en el módulo:

| Módulo | Métodos | Botones `object` | Sin método |
|---|---|---|---|
| `madenat_lumber_core` | 1002 | 22 | **0** |
| `madenat_lumber_logistics` | 972 | 60 | **0** |
| `madenat_lumber_intake` | 660 | 35 | **2 (falsos positivos)** |
| `billing` / `purchasing` / `toll_processing` / `ingestion_engine` / `shipping_core` / `costing` / `reports` | 41 / 46 / 28 / 144 / 6 / 83 / 53 | 7 / 6 / 10 / 1 / 1 / 5 / 0 | **0** |

* Los **2 aparentes** (`action_process_documents`, `action_verify_data` en
  `madenat_lumber_intake/views/intake_reception_facade_views.xml`) **sí existen**: están definidos en
  **`madenat_lumber_core`** (`lumber_reception.py:2789/2801` y `madenat_guia_processing.py:1723`) y las vistas
  fachada operan sobre esos modelos ⇒ **falso positivo** del análisis módulo-a-módulo.
  **Lección para el cruce remoto:** los métodos deben resolverse **por MODELO**, no por módulo.
* Conclusión local: **no hay botones `object` sin método** en el código a desplegar.

**3.2 Estado local intacto** (habilita la comparación posterior): `git status` **11 entradas**, HEAD
`677294b`, `stash` vacío, huella SHA-256 del WIP `8b2243257fd5…` (**idéntica al cierre de la FASE 8**) y
`madenat_test` con 13/8/12/151/327/3.

**3.3 Registro de comandos** de esta fase (sin salidas sensibles): `logs/comandos_fase9.log`.

---

## 4. CRUCE §3.C — PROCEDIMIENTO LISTO PARA EJECUTAR EN CUANTO HAYA ACCESO

*(Todo se ejecuta **en el remoto**, solo lectura; nada se ha ejecutado aquí.)*

1. **Leer las vistas activas** de los módulos MADENAT y extraer, por vista:
   `SELECT imd.module, imd.name, v.id, v.key, v.model, v.arch_db::text
    FROM ir_ui_view v JOIN ir_model_data imd ON imd.model='ir.ui.view' AND imd.res_id=v.id
    WHERE imd.module LIKE 'madenat%' AND v.active;`
2. **Extraer** de `arch_db` los `name="…"` de `<button type="object">`, los `type="action"` y los `<field name="…">`.
3. **Comparar contra el código local en `677294b`** con los mismos criterios que el cruce local de §3.1, pero
   **resolviendo los métodos por modelo** (y con el manifiesto SHA-256 de archivos que documenta CANON/02 para
   detectar además archivos distintos).
4. **Listar** los que no existan (esperado: vacío; si no lo está, **NO-GO** hasta revisar).

---

## 5. GO / NO-GO

| # | Condición | Estado | Responsable |
|---|---|---|---|
| 1 | Acceso de solo lectura al TEST remoto **configurado y probado** (usuario/clave o equivalente) | ❌ **PENDIENTE** (bloquea todo) | Mauricio |
| 2 | Verificación A–E del remoto ejecutada y documentada | ⛔ **no iniciada** (depende de 1) | Cline |
| 3 | Cruce §3.C remoto vs `677294b` completado | ⛔ **no iniciada** (depende de 1) | Cline |
| 4 | Decisión **D1 `costing`** | ⏳ pendiente | Mauricio |
| 5 | Decisión sobre el **menú de `reports` (P2-2)** | ✅ decidido: **fuera** | Mauricio |
| 6 | Respaldo remoto (dump + filestore + código) **antes** de tocar | ⏳ pendiente (ventana) | Mauricio/Cline |
| 7 | Ventana de mantenimiento acordada | ⏳ pendiente | Mauricio |
| 8 | Método de entrega del código decidido (sección E) | ⏳ pendiente (se propone en §6) | Mauricio |
| 9 | `VIEW-01/04` manual en navegador | ⏳ pendiente (checklist FASE 7) | Mauricio |
| 10 | Repo local y `madenat_test` sin cambios | ✅ **verificado** | Cline |

**DICTAMEN: NO-GO** — ninguna condición de despliegue está habilitada mientras no exista acceso (1).

---

## 6. PROCEDIMIENTO DE ENTREGA PROPUESTO (sin ejecutar)

A partir de lo **observado** (repo local con `origin` git; documentación que cita SSH y `/opt/odoo18-test`) y de
la sección E, se proponen **dos vías**, a elegir por Mauricio:

**Vía 1 — Git (recomendada si el remoto puede alcanzar el `origin`):**
1. `origin` (remoto del proyecto) es el canal: los commits `bfda876`, `56405cb`, `c4935ed`, `2985768`,
   `7d277e9`, `7c417ae`, `677294b` de la rama `feat/guia-correccion-documental-preservada-20261002`
   deberían estar publicados allí (requiere **push** — **no autorizado** en esta fase y **no ejecutado**).
2. En el remoto: `git -C <ruta_addons_remota> fetch && git -C <ruta_addons_remota> status` (solo lectura) para
   comparar; el paso de actualización (`git checkout`/merge) se hace **solo** en la ventana y con respaldo hecho.

**Vía 2 — Copia controlada por SSH/rsync (si el remoto no alcanza el `origin`):**
1. `rsync -av --dry-run <ruta_local_addons>/{madenat_lumber_core,madenat_lumber_intake,madenat_lumber_logistics,madenat_lumber_shipping_core}/ <usuario>@<host>:<ruta_addons_remota>/<modulo>/`
   (**excluir** `madenat_lumber_costing/**` y `madenat_lumber_reports/**`).
2. Verificación por hash (`sha256sum`) en ambos extremos.

En ambos casos: **precedido** de respaldo remoto (dump `-Fc` + filestore + tar del código), y **seguido** de
`-u` de los 4 módulos en orden de `depends` (**sin** `-u all`) y del humo funcional del runbook §7.

---

## 7. AJUSTES NECESARIOS AL RUNBOOK

1. **Nuevo prerequisito 1.0 (bloqueante):** «**Acceso al TEST remoto**: usuario, host, puerto, clave/agente y
   método (SSH) **configurados y probados** desde la estación de trabajo». Hoy **no** existe ⇒ el runbook debe
   declararlo como **condición de entrada** y no asumirlo.
2. **§0:** reemplazar el aviso genérico por: «el TEST remoto se accede por SSH con el usuario documentado en
   `CANON/02` (ruta `/opt/odoo18-test`, servicio `odoo18-test`, base `madenat_test`); **credenciales no
   incluidas** en el repositorio».
3. **§3.A/B:** añadir el **manifiesto SHA-256 de 314 archivos** que ya documenta CANON/02 como método de
   comparación de código (o `git rev-parse HEAD` si el remoto es git).
4. **§3.C:** precisar que el cruce de métodos se hace **por MODELO** (ver §3.1 de este informe: los botones de
   las vistas fachada de `intake` resuelven métodos definidos en `core`).
5. **§7 (humo):** añadir «confirmar que el menú «Imputaciones documentales SV» **existe e está inactivo**»
   (tras M1) y «confirmar que `TestLengthUomAndSubproducto` no falla en el remoto si se ejecutan suites».

*(Estos ajustes se anotan aquí; su aplicación al fichero del runbook queda a decisión de Mauricio para no
alterar un documento ya entregado sin su visto bueno.)*

---

## 8. DECISIONES PARA MAURICIO

| # | Decisión | Por qué ahora |
|---|---|---|
| 1 | **Proveer el acceso** al TEST remoto (o autorizar una prueba puntual de conectividad) | Desbloquea R2–R4 (toda la verificación) |
| 2 | **D1 `costing`**: commitear+desplegar / mantener fuera / revertir el WIP local | Determina si `reports` puede desplegarse y si §3.8 pasa |
| 3 | **Método de entrega** del código (vía 1 o vía 2) | Determina los comandos exactos de la ventana |
| 4 | **Ventana** de mantenimiento y **respaldo remoto** | Requisito del runbook §2 |
| 5 | **VIEW-01/04 manual** (checklist FASE 7) | Única verificación de renderizado pendiente |
| 6 | **Juego mínimo de configuración** a sembrar en el destino (precisión decimal, parámetros `madenat.*`) | Hallazgo de la FASE 8 |

---

## 9. VALIDACIÓN FINAL DE LA FASE 9

| Comprobación | Resultado |
|---|---|
| ¿Se ejecutó algo fuera de la lista cerrada? | **No** (§3 no se inició); log en `logs/comandos_fase9.log` |
| ¿Se contactó el remoto? | **No** (ni lectura ni escritura; no se intentó conexión) |
| ¿Cambió el remoto? | **No aplica**: no hubo contacto (por tanto, sin cambios por construcción) |
| Repo local | `git status` **11 entradas**, HEAD **`677294b`**, `stash` vacío, huella del WIP `8b2243257fd5…` **idéntica a FASE 8** |
| `madenat_test` | **13/8/12/151/327/3** (sin cambios) |
| Escrituras locales | Solo creación del expediente `FASE9_VERIFICACION_REMOTO_20261015/` (**fuera del repo**) |


