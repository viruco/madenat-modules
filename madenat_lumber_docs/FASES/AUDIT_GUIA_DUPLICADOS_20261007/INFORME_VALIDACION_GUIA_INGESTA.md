# Validación de "guía ya ingresada" en la ingesta — auditoría focalizada y propuesta mínima

**Proyecto:** MADENAT Lumber — Odoo 18 CE (`/home/viruco/dev-stack/odoo/odoo-18-ce`)
**Alcance:** sólo investigación y propuesta. Sin cambios de código, datos, ACL ni doctrina.
**Base de lectura:** código de `custom_addons/` (rutas activas) + doctrina vigente `madenat_lumber_docs/CANON`.
**Fecha:** 2026-10-07.

> Distinción documental: se usó **CANON** (`00`, `03`, `04`, `12`) como doctrina **vigente**. `RAW/`,
> `LEGADO/`, `WIKI/06_SESIONES` e `_archive_*` se trataron como **histórico/propuesta**, no como política.

---

## 0. Resumen ejecutivo (una línea)

Ya existe un **validador compartido** de duplicados (`madenat.reception.parser._check_guide_duplicate`);
hoy **sólo la ruta de Recepción/Producto** lo invoca. La **brecha** es que **Procesado, Volúmenes y el
formulario directo de `madenat.guia.processing` NO lo ejecutan** y dependen sólo de `UNIQUE(name, partner_id)`
(ineficaz con `partner_id` nulo y sin detección entre modelos). La **intervención mínima** es reutilizarlo en el
**`write()` de `madenat.guia.processing`** (el punto donde **todas** las rutas de guía fijan el `name`).

---

## 1. Doctrina vigente pertinente (CANON)

| Tema | Fuente vigente | Qué fija |
|---|---|---|
| Discriminación de origen del lote | `CANON/12_FLUJOS_INGESTA.md` §2–5 | `stock.lot` usa **`reception_id`** (recepción) o **`guia_processing_id`** (procesado), mutuamente excluyentes. `guia_number` es **informativo**, no discriminador. |
| Dos flujos de ingesta | `CANON/12` §3–4 | Flujo 1 = `madenat.guia.processing` (servicio/procesado, y volumen). Flujo 2 = `lumber.reception` (recepción directa: Blank/S2S/métrica). |
| Validación de duplicados | `CANON/03_TESTS.md:129` (`test_duplicate_validation.py`, 2026-06-11) | Existe control **"validación temprana de duplicados"** probado: PDF, guía existente, staging y mensaje al operador. |
| Ciclo de vida de guía | `CANON/04_DECISION_LOG.md` AD-80; `CANON/12` §11.7; `CANON/13` §10 | Modos A–D; la guía cancelada conserva trazabilidad; el borrado es ruta aparte. |
| Corrección/relectura | `CANON/12` §11.5–11.8; AD-79/AD-87 | Relectura y corrección del **mismo** origen; volumen oficial único; imputación SV. |
| Sin unicidad global implícita | `CANON/12` §5.2 (prohibiciones) | No usar `guia_number` como clave; el número **comparte** valores entre documentos (recepción homónima ↔ guía). |

**Conclusión doctrinal:** la identidad de una guía se resuelve por **relaciones** (`reception_id` /
`guia_processing_id`) y por las **claves naturales** de cada cabecera; el número de guía **detecta**
coincidencias pero **no** atribuye documentos ajenos ni impone unicidad global.

---

## 2. Controles que YA existen (evidencia de código)

| # | Control | Ubicación | Cobertura |
|---|---|---|---|
| C1 | **Validador compartido de duplicados** (busca en `lumber.reception` y en `madenat.guia.processing`; mensaje claro con datos del registro existente) | `madenat_lumber_core/models/reception_parser.py:33` `_check_guide_duplicate(guide_no, partner_id, exclude_id)` | Llamado **sólo** desde el pipeline de Recepción |
| C2 | **Invocación en el pipeline de Recepción** (antes de Gate 1, cabecera, staging y lotes) | `madenat_lumber_core/models/reception_workflow.py:97-113` (`parser._check_guide_duplicate(..., exclude_id=reception.id)`) | Recepción / Producto |
| C3 | **Constraint SQL** recepción | `lumber_reception.py:927-933` `UNIQUE(name)` | Recepción (Nombre global; NULL admitido en múltiples) |
| C4 | **Constraint SQL** guía procesada | `madenat_guia_processing.py:593-599` `UNIQUE(name, partner_id)` | Guía (por proveedor; **NULL no colisiona** → brecha) |
| C5 | **Guard anti-duplicado de materialización** (segunda revalidación física) | `madenat_guia_processing.py:1686` `_b1_assert_no_duplicate_revalidation` (usado en `:1140`, `:2515`) | Guía → impide **segundo** envío a stock |
| C6 | **Guard anti-duplicado de confirmación** (ya hay lotes → bloquea) | `lumber_reception.py:2892-2908` | Recepción |
| C7 | **Idempotencia del asistente** (wizard ya derivado → reabre el mismo destino) | `intake_wizard.py:576-580`, `_existing_target():640` (`target_model`/`target_res_id`) | Wizard (producto/volumen/procesado) |
| C8 | **Lectura del N° de guía** y su almacenamiento de preview | `intake_wizard.py:555` y `:399` (`preview_guide_no`); `madenat_guia_processing.py:1824/1928` | Wizard (producto/volumen) y core (procesado) |
| C9 | **Extracción temprana del N° al subir Excel en formulario directo** | `madenat_guia_processing.py:3319-3326` `write()` + `_try_extract_guide_number_from_binary():3286` | Formulario directo de guía |

**Lo esencial:** el control C1 **ya existe, ya tiene mensaje, ya está probado y ya se usa en una ruta**.
No hay que inventar validación: hay que **reutilizarla** en las rutas que hoy no la llaman.

---

## 3. Mapa del flujo por modalidad (archivo · método · líneas)

Todas las rutas del **asistente** (`madenat.lumber.intake.wizard`) desembocan en **dos** modelos destino:
`lumber.reception` (Producto/Recepción) o `madenat.guia.processing` (Procesado y Volumen).

| Modalidad | Entrada | Lectura | Identificación (N°) | Búsqueda de guía existente | create/write | Efectos posteriores |
|---|---|---|---|---|---|---|
| **Producto** (normal) | `intake_wizard.action_route_document():573` | `action_preview_document():475` / `_classify_normal_document():445` | `preview_guide_no` (wizard):555 | **C2** `reception_workflow.py:107` | `_route_producto():651` → `lumber.reception.create():656` → `action_process_documents():665` | header `_update_header_data():230`; **staging** `_fill_staging_table()`; **lotes/stock** en `action_confirm_reception():2875` |
| **Recepción** (core/form) | Formulario `lumber.reception` | `action_verify_data():2801` | `_update_header_data():236` | **C3** SQL `UNIQUE(name)`; **C1/C2** sólo vía pipeline | `create` (form) → `action_process_documents():2789` | idem Producto |
| **Procesado / Servicio Externo** | `action_route_document():573` → `_route_procesado():683` | Delegada al core: `madenat_guia_processing.action_verify_data():1703` | PDF `:1824-1825` / Excel `:1926-1928` | **NINGUNA** (sólo **C4** SQL al `write():1930`) | `madenat.guia.processing.create():698` → `action_verify_data()` | staging `madenat.guia.processing.line` `:1786-1787`; **lotes/stock** en `action_validate():2117` (con **C5**) |
| **Volúmenes** | `action_route_document():573` → `_route_granel():864` | `_read_volume_document()`/`_preview_volume():310` | `preview_guide_no` (wizard):399 y `header['guide_number']` | **NINGUNA** (sólo **C4** SQL en el `write` del header) | `madenat.guia.processing.create():940` → `guia.write(header_update)` (`name`) | detalle documental + volumen oficial; **lotes/stock** en `action_validate()` (con **C5**) |

**Métodos compartidos y rutas que NO pasan por ellos**

- **Compartido hoy:** `_check_guide_duplicate` (C1) sólo lo usa el **pipeline de Recepción** (C2).
- **Rutas que NO lo usan:** **Procesado** y **Volúmenes** (ambas crean `madenat.guia.processing`) y el
  **formulario directo** de la guía. Se apoyan únicamente en el `UNIQUE(name, partner_id)` (C4).
- **Momento en que el dato está disponible:**
  - Producto: número conocido por el parser **dentro** del pipeline (C2 lo usa ahí).
  - Procesado: número conocido **dentro** de `action_verify_data()` (core), justo antes del `write():1930`.
  - Volúmenes: número conocido **en el asistente** (`_route_granel`), **antes** del `create():940`.
- **Momento anterior al primer efecto persistente de negocio:**
  - Producto: **C2** ya ocurre antes de cabecera/staging/lotes. ✔
  - Procesado: la **cabecera se crea antes** de leer el número (el `name` se fija por `write` posterior).
    El primer efecto "real" (lotes/stock) es **posterior** (`action_validate`). El staging (`:1787`) precede al `name`.
  - Volúmenes: la cabecera se crea con el `name` **en el mismo acto** (write inmediato tras `create`); antes del detalle y de lotes.
- **No confundir** los registros del **asistente** (`TransientModel`) ni el **staging** (`…processing.line`, reemplazable) con la **materialización** en `stock.lot`/`stock.quant`.

---

## 4. Qué significa "ya ingresada" (según doctrina + código)

- **Qué identifica una guía:** el **número** = `name` en `lumber.reception` y en `madenat.guia.processing`.
  El **tipo/emisor** = `partner_id` (guía) y `supplier_id` (recepción). La **fecha** = `date_emission`/`guia_fecha`.
- **Dónde buscar:** en **ambos** modelos (C1 ya lo hace). Un documento puede existir como recepción **o** como guía.
- **Documento existente vs número homónimo:** C1 compara por número y, en la guía, **además** por `partner_id`.
  El número **no es globalmente único** (CANON/12 §5.2): una recepción `15183` y una guía `15183` pueden coexistir
  siendo documentos **distintos**. Por eso **no** debe imponerse unicidad global del número.
- **Si falta proveedor/emisor:** C1 sólo filtra por `partner_id` cuando se conoce; si no, compara por número.
  La captura **incompleta debe seguir permitida** (C1 devuelve temprano si `guide_no` vacío).
- **Guías canceladas:** una guía `cancelled` **sigue existiendo** (`name` persistido) → C1 la detecta y
  ofrece editarla/reabrirla (coherente con el Modo B de AD-80), en vez de crear otra.
- **Relación PDF ↔ Excel de una misma guía:** el número se toma del PDF y, si falta, del Excel
  (`action_verify_data:1924-1928`); en Volúmenes, PDF y Excel se **concilian** (`_conciliate_documents`).
  El validador actúa sobre el número **resuelto**; **no** fusiona cabeceras.
- **Relectura / reintento:** el wizard ya derivado **reabre** su destino (C7) sin recrear; reabrir una guía
  cancelada reusa el **mismo** origen; una **lectura nueva** del mismo documento chocaría con C1/C3/C4 → se
  informa al operador del registro existente (reutiliza mensaje y acción).

---

## 5. Evaluación del punto más simple

Candidatos **existentes** comparados (sin crear nada nuevo):

| Punto | Cubre | Datos disponibles | Antes de efectos | ¿Duplica lógica? | Comentario |
|---|---|---|---|---|---|
| `action_preview_document` / `action_route_document` (wizard) | Sólo Producto y Volumen | N° en `preview_guide_no` | Sí (pre-create) | No (llama a C1) | **No cubre Procesado** (su N° no se conoce aquí). Deja 2 puntos. |
| `reception_workflow` (C2) | Recepción/Producto | Sí | Sí | No | **Ya lo hace.** No requiere cambio. |
| `action_verify_data` (guía, core) | Sólo Procesado | N° tras parsear PDF/Excel | Después del staging, antes de `write` | No | Toca core y **no** cubre Volumen. |
| `_route_granel` (wizard) | Sólo Volumen | N° antes del `create` | Sí (pre-create) | No | Toca intake y **no** cubre Procesado. |
| **`madenat.guia.processing.write()`** | **Procesado + Volumen + formulario directo** | `name` final + `partner_id` | En la fija del `name` (antes de lotes/stock) | No (llama a C1) | **Un solo cambio**; reutiliza el hook de `write` que **ya** extrae el N° (`:3319-3326`). |

**¿Existe un único punto común?** **No del todo.** El N° se conoce en momentos distintos por ruta
(wizard para Producto/Volumen; core para Procesado). Por eso **no** se fuerza un único punto en el wizard.
Sin embargo, existe **un único punto común en el modelo de destino**: la cabecera de guía fija su
`name` **siempre** vía `write()` (nunca en `create`), de modo que `madenat.guia.processing.write()` es el
**denominador común** de Procesado, Volumen y formulario directo.

**Punto elegido (mínima intervención):** ejecutar el **validador existente C1** dentro de
`madenat.guia.processing.write()`, **justo después** de resolver el `name` efectivo, y en `create()` si el
`name` real viniera en `vals`. Reglas del guard (mínimas y no intrusivas):

- Sólo actúa si el `name` **efectivo** cambia a un valor **real** (no vacío, `≠ 'New'`, `≠ name` previo).
- Excluye el propio registro (`exclude_id=self.id`) — ver §7.
- No actúa si falta número (**captura incompleta permitida**).

**Distinción explícita (los tres niveles):**

- **Aviso temprano al leer:** ya disponible en el wizard (`preview_guide_no`) para Producto/Volumen; puede
  mostrarse como advertencia **no bloqueante** al previsualizar. Es **opcional** (mejora de UX), no el control.
- **Control efectivo antes de persistir el negocio:** el guard en `write()` (**bloquea** antes de `action_validate`
  y de cualquier lote/stock/volumen), reutilizando el mensaje de C1.
- **Protección ante reintentos y concurrencia:** el guard **no** es concurrencia-segura por sí mismo (es un
  `search`). Ante reintentos, C7 (idempotencia del wizard) y los `UNIQUE` (C3/C4) actúan como respaldo.
  **No se promete** protección concurrente: dos ingestas simultáneas del mismo N° podrían pasar ambas por el
  `search` antes de comprometer; cerrarlo exigiría un índice único a nivel de BD o un lock — **no propuesto**
  (no hay brecha concurrente comprobada en esta auditoría).

---

## 6. Sin hardcodear (cumplimiento)

La propuesta **reutiliza** mecanismos existentes. **No** introduce: números de guía, IDs, nombres de BD,
excepciones para `15183`, listas de proveedores/tipos, ni parámetros nuevos. Usa **relaciones y campos**
existentes (`name`, `partner_id`, `company_id`) y el validador C1 ya vigente. No añade modelos, campos,
servicios, locks ni restricciones: la brecha se cubre con lo existente (una invocación del validador).

---

## 7. Información incompleta y duplicados — comportamiento mínimo propuesto

Reutilizando C1 (mensaje y datos del registro existente); **sin** fusionar, sobrescribir ni elegir el
primer candidato como acción automática:

| Escenario | Comportamiento mínimo |
|---|---|
| **Coincidencia exacta** (mismo modelo, misma clave) | **Bloquear** con el mensaje de C1 (registro existente + acción: editar ese mismo documento). |
| **Número coincidente con documento distinto** (otra cabecera / otro modelo / otro proveedor) | **Bloquear** con mensaje de C1 que **identifica** el documento existente (no asume que sea el mismo). *Decisión de política pendiente: ¿bloquear o advertir?* (ver H). |
| **Identidad incompleta** (sin N°) | **No bloquear**; permitir captura y completar después (C1 retorna temprano si no hay N°). |
| **Varias coincidencias** | **Bloquear** e informar; mejorar el mensaje para listar >1 candidato (mejora mínima del texto, no de la lógica). |
| **Relectura del mismo documento** (wizard ya derivado) | **Reabrir** el destino (C7), sin recrear. |
| **PDF y Excel complementarios** | Un solo N° **resuelto** (PDF y, si falta, Excel); **no** se crean dos cabeceras. |
| **Archivos contradictorios** (N° distinto PDF vs Excel) | Fuera del duplicado: ya existe **Gate 1** (recepción) y **conciliación** (Volumen). No se altera. |

**Nota de reutilización de mensajes/acciones:** el texto de C1 ya indica al operador revisar/editar el
registro existente; es el comportamiento correcto y no requiere redacción nueva salvo el caso "varias
coincidencias".

---

## 8. Validación de impacto propuesta (pruebas acotadas)

Todas en **base aislada** (clon) y con **usuario operativo sin superusuario** (`with_user`, `su=False`).
**No** ejecutar pruebas mutantes en la base activa. **No** validar la ingesta probando sólo el parser.

1. **Por modalidad (guía nueva):** Producto, Procesado, Volumen y Recepción crean su cabecera normalmente
   (sin falso bloqueo) cuando el N° **no** existe.
2. **Guía repetida:** reintentar el mismo N° en cada modalidad → **bloqueo** con el mensaje de C1; **no** se
   crea segunda cabecera ni (si aplica) segunda línea.
3. **Número homónimo (documento distinto):** N° existente en el **otro** modelo (recepción ↔ guía) y/o con
   **otro** `partner_id` → comportamiento según decisión D1 (§H); verificar que **no** se atribuye ni fusiona.
4. **Datos incompletos:** sin N° en el documento → **no** bloquea; el ingreso continúa y puede completarse.
5. **Relectura / doble ejecución:** volver a derivar el mismo wizard (C7) → **reabre** el destino, sin duplicar;
   doble clic en "Ejecutar" → sin segunda cabecera.
6. **PDF/Excel coincidentes y contradictorios:** mismo N° en ambos → una cabecera; N° distinto → reconciliación
   existente (Gate 1 / conciliación), sin duplicado silencioso.
7. **Usuario operativo sin superusuario:** el guard se evalúa con identidad real (no `sudo`) y aplica igual.
8. **Ausencia de duplicación:** `search_count` de cabeceras y de líneas = 1 tras cada intento.
9. **Conservación de correcciones legítimas:** renombrar/editar **el mismo** documento con un N° que **no**
   colisiona (o que colisiona consigo mismo, excluido por `exclude_id`) → **no** bloquea indebidamente.
10. **Concurrencia (si la ruta puede ser simultánea):** documentar que el `search` **no** la cubre; verificar
    que el `UNIQUE` existente (C3/C4) sigue siendo el respaldo y anotar el caso `partner_id` nulo.

---

## 9. Entrega (A–H)

**A. Qué controles ya existen.** C1 (`_check_guide_duplicate`, compartido, probado), C2 (invocación en el
pipeline de Recepción), C3/C4 (constraints SQL), C5/C6 (anti-duplicado de materialización/confirmación),
C7 (idempotencia del wizard), C9 (extracción temprana de N° en el formulario). Ver §2.

**B. Qué brecha está comprobada.** Las rutas de **Procesado**, **Volúmenes** y el **formulario directo** de
`madenat.guia.processing` **no invocan C1**. Sólo cuentan con `UNIQUE(name, partner_id)` (C4), que
(a) **no detecta** coincidencias **entre modelos** (recepción ↔ guía) y (b) **no colisiona** cuando
`partner_id` es nulo. El N° se fija por `write()` posterior al `create`, sin verificación de duplicado.

**C. Dónde colocar la validación mínima (archivo · método · momento).**
`madenat_lumber_core/models/madenat_guia_processing.py` → `write()` (línea **3313**), **inmediatamente
después** de resolver el `name` efectivo (extendiendo lo que ya hace `:3319-3326`) y **antes** de
`super().write()`; y en `create()` (**3307**) si el `name` real viniera en `vals`. Invoca
`self.env['madenat.reception.parser']._check_guide_duplicate(name, partner_id=…, exclude_id=self.id)`.
Ajuste necesario en C1: aplicar `exclude_id` **también** a la búsqueda en `madenat.guia.processing`
(hoy sólo excluye en la búsqueda de `lumber.reception`, `reception_parser.py:78-79`).

**D. Qué rutas cubre y cuáles no.**
- **Cubre:** Procesado (`action_verify_data` → `write`), Volúmenes (`_route_granel` → `write`) y
  formulario directo (C9 → `write`).
- **No cambia (ya cubiertas):** Recepción/Producto (C2, pipeline).
- **Fuera de alcance de este punto:** detección **concurrente** verdadera; reconciliación PDF/Excel (ya existe);
  la semántica de "abolir" un duplicado (no se propone).

**E. Qué comportamiento verá el usuario.** Al fijar el N° de una guía que **ya existe** (en cualquiera de los
dos modelos, según la clave), el asistente/formulario **bloquea** con el **mensaje existente de C1**, mostrando
N° guía, proveedor, fecha, estado e ID del registro encontrado y la acción ("revise/edite ese mismo documento").
En captura **sin** N°, no cambia nada. Con un N° **nuevo**, el ingreso sigue igual.

**F. Qué archivos sería necesario cambiar y por qué.**
- `madenat_lumber_core/models/madenat_guia_processing.py` — `write()`/`create()`: **invocar** el validador
  existente (mínima intervención, reusa el hook que ya extrae el N°).
- `madenat_lumber_core/models/reception_parser.py` — `_check_guide_duplicate`: aceptar/aplicar
  `exclude_id` en **ambas** búsquedas (para que no se bloquee a sí mismo al reusarlo desde la guía).
- *(Opcional, sólo UX)* `madenat_lumber_intake/models/intake_wizard.py` — advertir en el preview con
  `preview_guide_no` (no bloqueante). No es el control.
- **No** se toca: ACL, parser de lectura, constraints SQL, doctrina, ni el asistente para bloquear.

**G. Pruebas e impacto esperado.** Ver §8. Impacto: **una** cabecera por N° (por proveedor/modelo), **cero**
duplicados silenciosos, captura incompleta **preservada**, relectura idempotente. Riesgo de falso bloqueo si
`_check_guide_duplicate` se aplica sin `exclude_id` (por eso el ajuste de F).

**H. Riesgos y decisiones pendientes.**
- **D1 (política):** ante **número homónimo de documento distinto** (p. ej. recepción `15183` ↔ guía `15183`,
  CANON/12 §5.2): ¿**bloquear** (como hoy en Recepción) o **advertir y permitir**? La doctrina **prohíbe** la
  unicidad global, pero C1 **bloquea** en coincidencia. **Decidir** antes de implementar. Recomendación:
  **bloquear + mensaje que identifique el documento** (consistente con lo vigente), revisable.
- **D2:** caso `partner_id` nulo en C4 — el validador lo cubre por número; no se cambia el constraint.
- **D3:** concurrencia real — **no** cubierta; no se propone índice/lock sin brecha comprobada.
- **Riesgo operativo:** falso bloqueo en edición legítima → mitigado por `exclude_id` y por "sólo si el N°
  cambia a valor real ≠ 'New'".
- **Riesgo de regresión:** el `write()` es central; acotar el guard a cambios de `name` y probar
  `madenat_lumber_core` y `madenat_lumber_intake` (módulos de la corrección).

---

## Recomendación directa

> **La intervención mínima es invocar el validador ya existente
> `madenat.reception.parser._check_guide_duplicate()` en el `write()` de
> `madenat.guia.processing` (al fijar el `name`), con un ajuste mínimo de `exclude_id` en ese validador,
> porque cubre Procesado + Volúmenes + formulario directo con un solo punto,
> sin modificar el modelo de datos, las ACL, el parser de lectura, el asistente ni la doctrina vigente.**

Cierre: investigación, mapa y propuesta entregados. **No** se implementó nada. La implementación se
aprobará tras revisar el punto elegido (C) y resolver D1.


