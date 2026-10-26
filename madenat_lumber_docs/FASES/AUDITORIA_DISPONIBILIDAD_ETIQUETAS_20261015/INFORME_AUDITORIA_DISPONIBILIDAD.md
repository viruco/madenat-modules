# AUDITORÍA — DISPONIBILIDAD DE ETIQUETAS EN EL FORMULARIO DE IMPUTACIÓN (SOLO LECTURA)

**Fecha:** 2026-10-15 · **Entorno:** LOCAL `madenat_test` · **Módulo:** `madenat_lumber_logistics` (18.0.1.36.0)
**HEAD auditado:** `254e6d3e10a67a6c6323c8165e2cf73dc1851f50` (rama `feat/guia-correccion-documental-preservada-20261002`)
**Alcance:** auditoría de **sólo lectura** + reproducción en transacciones **REVERTIDAS** (`odoo shell`,
`env.cr.rollback()`). **Cero cambios** de código, vistas, ACL, datos o repositorio; sin commit, sin push, sin
remoto, sin `-u all`, sin tocar `IMP04823` ni `IMP02220`.

---

## 0. Dictamen

El síntoma **está reproducido exactamente** y **no es un defecto de cálculo**: `IMP02220` (aplicada, **sin ningún
reparto a SV**) consume documentalmente el nominal completo de las etiquetas `D7632` (3,263 m³) y `D7642`
(4,225 m³). El formulario, por diseño, **lista todas las etiquetas de la guía sin filtrar por disponibilidad** y
permite marcarlas (incluida «Seleccionar todas»); el resumen y la nota **sí informan** de la causa y **sí** ofrecen
el documento que la explica (botón «Ver documentos»), pero **el mensaje del servidor al Aplicar es genérico y no
nombra ni la etiqueta ni el documento**, y nada impide preparar la operación imposible.

---

## 1. Mapa del cálculo de disponibilidad (`archivo:línea`)

### 1.1 Fuente del cálculo (modelo `madenat.sv.imputation`)

| Magnitud | Definición | Ubicación |
|---|---|---|
| `I2_ACTIVE_STATES` = `('draft','pending','applied')` | estados que **ocupan** capacidad (techo duro) | `models/madenat_sv_imputation.py:32` |
| `I2_DOCUMENTAL_STATES` = `('applied',)` | estados que cuentan como **imputado documental** | `models/madenat_sv_imputation.py:34` |
| `_i2_lot_nominal_m3(lot)` | `volume_purchase_m3 or volumen_m3` | `models/…:232-234` |
| `_i2_lot_active_imputed_m3(lot, exclude)` | Σ `nominal_volume_m3` de las líneas de la etiqueta en estados **ACTIVOS** | `models/…:236-244` |
| `_i2_lot_reserved_m3(lot, exclude)` | Σ nominal de líneas en `draft`/`pending` | `models/…:260-273` |
| `_i2_lot_applied_m3(lot, exclude)` | Σ nominal de líneas en `applied` | `models/…:275-283` |
| `_i2_lot_available_for_m3(lot, exclude)` | **`nominal − Σ activos`** (puede ser 0/negativo) | `models/…:285-297` |
| `_i2_lot_documental_available_m3(lot)` | `nominal − Σ aplicados` | `models/…:254-258` |
| `_i2_sv_*` (nominal/asignado/disponible del SV) | ídem por SV; **magnitud documental propia** | `models/…:300-321` |

### 1.2 Proyección por fila del formulario (asistente)

| Columna del formulario | Campo | Cálculo | Ubicación |
|---|---|---|---|
| **Disponible (m³)** | `etiqueta_disponible_m3` | `_i2_lot_available_for_m3(lot, exclude_imputation=current)` | `wizards/madenat_sv_imputation_wizard.py:1179-1181` |
| (oculto) Aplicado | `etiqueta_aplicado_m3` | `_i2_lot_applied_m3(lot)` | `wizards/…:1174-1175` |
| (oculto) Reservado | `etiqueta_reservado_m3` | `_i2_lot_reserved_m3(lot, exclude=current)` | `wizards/…:1176-1178` |
| **Estado disponibilidad** | `disponibilidad_estado` | `available` si disp>0; si no, `applied` si aplicado>0; si no, `reserved` si reservado>0; si no, `no_capacity` si nominal≤0; si no, `other` | `wizards/…:1218-1234` (etiquetas del selection: `wizards/…:989-1001`) |
| **Causa del saldo** | `disponibilidad_detalle` | «Disponible: X de Y» o «Sin disponibilidad: consumida por **DOC (estado, m³)**» (lista los documentos ACTIVOS que la consumen) | `wizards/…:1245-1295` |
| Documentos que la consumen | `disponibilidad_imputacion_ids` / `_documentos_count` | M2M calculado (búsqueda de líneas en `draft/pending/applied`) | `wizards/…:1267-1275` |
| A asignar (m³) | `cantidad_asignar_m3` | Σ del reparto de **esta** etiqueta hacia el SV de trabajo (inverso `_inverse_cantidad_asignar`) | `wizards/…:1150-1157`, `1311-1344` |

**«Aplicado» por etiqueta** = la etiqueta tiene líneas en documentos **`applied`** que suman ≥ su nominal
(`disponibilidad_estado='applied'`). En el caso reportado: `D7632` aplicado 3,263 = nominal 3,263 ⇒ disponible
0,000 y estado «Aplicado» (idéntico para `D7642`, 4,225).

### 1.3 De dónde sale la lista de etiquetas del formulario

`_onchange_guia_processing_id` (wizards/…:377-419): si **no** hay documento de trabajo para la guía, crea una
fila por **cada** etiqueta de la guía —`_i2_processed_lots(guia)` = `guia.lot_ids` con
`lot_flow_type != 'volume'` (wizards/…:422-425)— con `selected=False`
(wizards/…:417-419 y `_i2_line_vals` 459-462). **No hay ningún filtro por disponibilidad** ni por estado.

---

## 2. Causa de que las etiquetas no disponibles aparezcan y se puedan seleccionar

Es **intencional y explícito** en el diseño (CANON/19 §19.16, decisiones D4/D5): la lista muestra todas las
etiquetas de la retorno-guía para poder **dejar constancia** (con motivo) y porque la disponibilidad puede
cambiar dentro de la sesión. No hay ninguna restricción de UI ni de modelo para marcar una etiqueta sin saldo:

| Elemento | Comportamiento hoy | Ubicación |
|---|---|---|
| Columna «Incluir» | `selected` con `widget="boolean_toggle"`, **sin `readonly` ni dominio** | `wizards/…_views.xml:139-140` |
| **«Seleccionar todas»** | `wiz.line_ids.write({'selected': True})` → marca **todas**, incluidas las de disponible 0 | `wizards/…:491-499` |
| **«Preparar asignación»** | crea fila de reparto **volumen 0** por **cada** etiqueta seleccionada (no filtra por saldo) | `wizards/…:506-540` |
| **«Usar disponible»** | rellena `min(disponible, nominal)` ⇒ **0** para las consumidas (no avisa) | `wizards/…:542-572` |
| **«Proponer FIFO»** | propone destinos SV por **saldo del SV**, **no** mira el saldo de la etiqueta ⇒ puede generar un reparto imposible (falla después por «Techo duro de etiqueta») | `wizards/…:430-489` |
| **«Seleccionadas»** (`selected_line_count`) | cuenta **todas** las seleccionadas, sin distinguir si son asignables | `wizards/…:163-164` |
| **«Sin disponibilidad»** (`not_assignable_line_count`) | cuenta las **seleccionadas** con `disponible ≤ 0` | `wizards/…:195-200` |
| **Aviso** (`no_availability_note`) | **SÍ nombra** cada etiqueta y su causa: «…Causa: D7632 — Sin disponibilidad: consumida por IMP02220 (aplicada, 3.263 m³); D7642 — …» | `wizards/…:201-212`; se pinta en `wizards/…_views.xml:84-93` |

⇒ Las etiquetas aparecen y se pueden seleccionar **por diseño**; lo que falta es **restringir la selección por
defecto a lo asignable**, **limitar «Seleccionar todas»** y **nombrar el problema en el mensaje del servidor**.

---

## 3. Qué documento compromete `D7632` y `D7642`: hipótesis CONFIRMADA (SQL de sólo lectura)

```
stock_lot: 18368 | D7632 PCLAT04201252900 19827 | ref=D7632 | nominal 3.263
           18372 | D7642 PCLAT04201453700 19827 | ref=D7642 | nominal 4.225
           (guia 1198 = name 19827, service, confirmed=yes; 17 etiquetas; SV00000000841 nominal 40.315)

madenat_sv_imputation_line (por etiqueta):
  1189 IMP02220 applied | 18368 (D7632) nominal 3.263
  1189 IMP02220 applied | 18372 (D7642) nominal 4.225

repartos (madenat_sv_imputation_sv_line): 1 fila en TODA la base → 415: imp=492 (IMP00946), linea=512,
  sv=15892, 10.000 m³  ⇒ IMP02220 tiene 0 repartos.
```

**Invariante aplicado vs. reparto a SV (etiquetas con líneas en documentos `applied`):**

| etiqueta | nominal aplicado | repartos a SV | diferencia (sin destino) |
|---|---|---|---|
| `D7642` (18372) | 4,225 | **0,000** | **4,225** |
| `D7632` (18368) | 3,263 | **0,000** | **3,263** |
| `UAT-SV-20261003-RET-01` (15894, IMP00946) | 10,000 | 10,000 | 0,000 |

⇒ **`IMP02220` consumió `D7632` y `D7642` sin entregar nada a ningún SV** (en particular, nada a
`SV00000000841`). El «saldo documental del SV 40,315» del reporte es el **nominal del SV** (40,315 m³): el SV no
ha recibido nada. **Hipótesis confirmada.** Es un **dato de origen** (FASE 10/11 ya lo documentaron como
anomalía de dato, no de código) y la etiqueta `SV00000000841` no interviene en el consumo.

---

## 4. Reproducción A–D (transacción revertida) y caso real

Logs: `logs/audit_disponibilidad_A_D_v2.log` (A–D, `exit=0`, `ROLLBACK`),
`logs/audit_disponibilidad_real2.log` (caso real aislado, `exit=0`, `ROLLBACK`),
`logs/audit_disponibilidad_A_D.log` (primera pasada: artefacto de la réplica, ver §4.5).

### 4.1 Caso real (guía 1198 «19827» + `SV00000000841`) — acción exacta del usuario
Seleccionando **sólo** `D7632` y `D7642` (aislado):

```
[1] seleccionadas=2 no_asignables=2 m3_preparados=0.000 disponible_total=0.000
    - D7632  disp=0.000 apl=3.263 estado=applied asignar=0.000
             causa=Sin disponibilidad: consumida por IMP02220 (aplicada, 3.263 m³).
    - D7642  disp=0.000 apl=4.225 estado=applied asignar=0.000
             causa=Sin disponibilidad: consumida por IMP02220 (aplicada, 4.225 m³).
    NOTA: «2 de las etiquetas seleccionadas no tienen disponibilidad documental… Causa: D7632 — …; D7642 — …»
[2] Preparar asignación -> OK ; Usar disponible -> OK  (m3 preparados sigue 0.000; reparto 0)
[3] APLICAR -> UserError: «Las etiquetas seleccionadas no tienen disponibilidad.
              Consulta la operación que las compromete o selecciona material disponible.»
[4] «Ver documentos que explican el saldo» -> ids=[1189]
[5] Botón por fila -> D7632 -> ['IMP02220'] · D7642 -> ['IMP02220']
```
⇒ **El síntoma queda reproducido literalmente**, incluido «Seleccionadas 2», «preparado 0», «preparado para el
SV 0,000». El «saldo documental del SV 40,315» es el **nominal del SV** (no ha recibido nada).

### 4.2 Caso A — etiqueta disponible
1 fila, `disp=5.000`, estado `Disponible`; «Seleccionar todas» → seleccionadas=1; «Preparar asignación» +
«Usar disponible» → `m3 preparados=5.000`; **Aplicar → OK (aplicada)**. Camino sano intacto.

### 4.3 Caso B — etiqueta aplicada **con** reparto
`disp=0.000`, estado `Aplicado`, causa «consumida por IMP14191 (aplicada, 5.000 m³)»; «Usar disponible» no
rellena (0.000); **Aplicar → UserError «Las etiquetas seleccionadas no tienen disponibilidad…»**; el aviso nombra
la etiqueta y el documento; **el botón «Ver documentos» funciona** (IMP14191).

### 4.4 Caso C — etiqueta aplicada **sin** reparto (réplica `IMP02220`)
Comportamiento de UI **idéntico** al caso B (estado `Aplicado`, `disp 0.000`, causa con el documento, mismo
mensaje genérico al Aplicar). El dato heredado de `IMP02220` **no genera un comportamiento distinto**: el
formulario no puede anticipar que el documento «aplicado» no entregó nada a ningún SV.

### 4.5 Caso D — mezcla disponible + no disponible con «Seleccionar todas»
`seleccionadas=2` (la disponible `D001` y la consumida `D002`), `no_asignables=1`, `disponible_total=5.000`.
- **Aplicar sin cantidades** → «**Indica los m³ a rebajar en las etiquetas seleccionadas.**» (la rama del mensaje
  depende de si **alguna** etiqueta de la selección tiene saldo: `models/…:818-825`).
- Tras «Preparar asignación» + «Usar disponible» → `m3 preparados=5.000` (sólo `D001`); **Aplicar → «Techo duro de
  etiqueta superado: la etiqueta D002 … 8.000 m³ (activos) frente a 4.000 m³»** (`models/…:831-848`).
- **«Proponer FIFO» → OK** pero propone destinos por el **saldo del SV**, no por el de la etiqueta (ver §2), por lo
  que puede dejar el reparto en un estado que **fallará al aplicar** por techo duro.

> **Artefacto declarado (primera pasada, `…_A_D.log`):** al replicar el caso C borrando el reparto con **SQL**
> detrás del ORM, quedó una fila obsoleta en caché y el `flush` del asistente lanzó
> `MissingError: El registro no existe o fue eliminado` (`stock.lot._compute_sv_assignment`), abortando el script
> antes del caso D. Se corrigió replicando el perfil heredado por la **vía privada del modelo**
> (`_i2_write_protected_state`) en la segunda pasada. **No es un defecto del producto**: en la aplicación real los
> repartos se borran por el ORM. La primera pasada dejó el log como evidencia y **no persistió nada** (rollback del
> shell por excepción).

---

## 5. Propuesta MÍNIMA de comportamiento (SIN implementar)

| # | Cambio | Archivo:línea | Detalle |
|---|---|---|---|
| P1 | **Asignable por fila** | `wizards/…:989-1001` + vista `wizards/…_views.xml:139-140` | Campo calculado `asignable = (disponibilidad_estado == 'available')`; columna «Incluir» con `readonly="not asignable"`. |
| P2 | **«Seleccionar todas» limitado a disponibles** | `wizards/…:491-499` | `wiz.line_ids.filtered('asignable').write({'selected': True})` + `display_notification` «N etiquetas omitidas por falta de saldo documental (ver sección «Sin disponibilidad»)». |
| P3 | **Sección de sólo lectura con documento y enlace** | `wizards/…_views.xml` (nueva `<page>` de sólo lectura; reutiliza `disponibilidad_detalle`, `disponibilidad_imputacion_ids` y el botón ya existente `action_open_consuming_documents`) | Las filas no asignables se listan ahí, con su causa y su(s) documento(s). **No** se crea modelo nuevo. |
| P4 | **Resumen que cuenta sólo seleccionables** | `wizards/…:159-222` | Añadir `selectable_line_count` y reescribir `assigned_summary`: «X seleccionables (Y sin saldo) · Z con reparto · W m³ → SV». Mantener `not_assignable_line_count`. |
| P5 | **Mensaje que nombre etiquetas y documento** | `models/…:814-829` + helper en el modelo (p. ej. `_i2_lot_consuming_docs(lot)`, reutilizando la búsqueda de `wizards/…:1267-1272`) | «Las etiquetas seleccionadas no tienen disponibilidad documental: D7632 (3,263 m³, aplicada por IMP02220); D7642 (4,225 m³, aplicada por IMP02220). Revierta la operación que las compromete o seleccione material disponible.» |
| P6 | *(Opcional)* **FIFO consciente del saldo de la etiqueta** | `wizards/…:430-489` | Limitar la propuesta a `min(saldo SV, saldo etiqueta, nominal)` para que FIFO no proponga un reparto imposible. |

**Pruebas mínimas (TDD, primero en rojo):** DISP-01 «Seleccionar todas» no marca las no asignables; DISP-02 la
sección de sólo lectura lista etiqueta + documento y el botón devuelve el dominio con el id; DISP-03 selección
forzada por ORM con una etiqueta no asignable ⇒ mensaje que contiene la etiqueta **y** el documento; DISP-04 caso
sano (A) intacto; DISP-05 `action_use_available` sobre una consumida no escribe y no lanza; regresión de
`RESET`/`LOCK`/`SIMPLE`/`DK`/`SG`/`WF` y de la suite de FASE 11.

**Riesgos:** (a) `readonly` en «Incluir» **elimina** la posibilidad de «dejar constancia» de una etiqueta sin saldo
(D4/D5) ⇒ si el negocio la necesita, conservar el toggle pero exigir **motivo** (patrón de desviación blanda);
(b) cambia el hábito de «Seleccionar todas» (mitigar con el aviso y la sección readonly); (c) los mensajes que
citan documentos deben respetar la compañía del usuario (la búsqueda del asistente ya está acotada; para el modelo
conviene `sudo` acotado a compañía o construir el texto sólo desde `self.line_ids`); (d) P6 cambia el resultado
actual de FIFO; (e) hay pruebas existentes que seleccionan etiquetas sin saldo (p. ej. `AUD-ETQ-04b`, reservada por
otro borrador) que habría que revisar.

---

## 6. Opciones de negocio para `IMP02220` (SIN ejecutar)

| Opción | Qué implica | Efectos verificados |
|---|---|---|
| **A. Documentar como excepción histórica** | No tocar nada; operar la guía 1198 con las otras **15** etiquetas (disponible total **35,872 m³**) hacia `SV00000000841` | `D7632`/`D7642` quedan «quemadas» documentalmente (7,488 m³ sin destino SV); no hay riesgo técnico |
| **B. Reversa OFICIAL con motivo** (Jefatura/Gerencia) y nueva imputación con reparto | `action_reverse(reason=…)` sobre `IMP02220` → libera `D7632` (3,263) y `D7642` (4,225); después, nueva operación con destino a `SV00000000841`, que queda **enlazada** (`origin_imputation_id=IMP02220` y recíproco al aplicar, M-4) | **Sólo documental**: `IMP02220` tiene **0 repartos** ⇒ la reversa **no** altera el saldo de ningún SV (no hay nada que devolver); deja bitácora `imputation_reverse` + chatter; la guía 1198 baja su «rebajado aplicado» en 7,488 m³ |
| **C. Híbrido (recomendado si se quiere el histórico limpio)** | A + B: documentar el origen y regularizar con reversa puntual + nueva imputación | Requiere fase propia con TDD, respaldo y verificación; reversible en el sentido de que la nueva operación puede volver a reversarse |

**No ejecutado.** Cualquier opción B/C exige autorización expresa, respaldo previo y ventana; en esta auditoría no
se ha tocado `IMP02220` (hashes de fila idénticos, ver §7).

---

## 7. Evidencia de que nada cambió

```
HEAD = 254e6d3e10a67a6c6323c8165e2cf73dc1851f50   (idéntico antes/después)
rama = feat/guia-correccion-documental-preservada-20261002
git status --porcelain -> 11 entradas (10 costing + 1 menu de reports)   [idénticas antes/después]

madenat_test -> guia=13 recep=8 users=12 lots=151 audit=327 imput=3 lineas=3 repartos=1 sv_op=1
md5(filas 1189+2733) = 987223f30299a910fd49653dafe77c20    (idéntico)
md5(lineas)          = fcd56adec11b20e0417fb39b4be4f01a    (idéntico)
IMP02220 applied · IMP04823 cancelled · IMP00946 applied   (estado, firma y clave intactos)
```

* Todas las reproducciones corrieron con `env.cr.rollback()` (y una de ellas abortó por excepción → rollback del
  shell): **cero residuos**. Los logs terminan con «ROLLBACK (sin cambios persistidos)» o con la traza del
  artefacto declarado.
* **Sin** escrituras de negocio fuera de la transacción revertida; sin `-u`, `-u all`, `--test-enable`, sin cambios
  en vistas/ACL/secuencias/parámetros y sin tocar `IMP04823`/`IMP02220` (sólo lectura).
* Los scripts y logs viven en `AUDITORIA_DISPONIBILIDAD_ETIQUETAS_20261015/`, **fuera** del repositorio git
  (`custom_addons/`), por lo que `git status` sigue con **11** entradas.



