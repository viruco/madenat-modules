# 19 — Imputación SV (etiqueta→SV) y Saldo por Procesador

**Proyecto:** MADENAT Lumber — Odoo 18 CE
**Versión documental:** 1.10.0
**Fecha de creación:** 2026-10-01
**Estado:** ✅ Vigente — Documento canónico de la **imputación declarada** entre la etiqueta de madera procesada y una o varias etiquetas SV (Lote Volumen), y del **saldo por procesador**. **No sustituye** a `00_ARQUITECTURA.md`, `04_DECISION_LOG.md`, `12_FLUJOS_INGESTA.md`, `13_CONSOLIDACION_OPERATIVA.md`, `17_CONSTITUCION_VOLUMENES.md` ni `18_CONSOLIDACION_Y_REBAJA.md`; los referencia y los alinea.
**Responsable revisión:** Arquitecto / Tech Lead — Alta del documento a solicitud del usuario (decisiones D1–D10 del 2026-10-01); **Fase A 2026-10-01:** renumeración de fases (bloque **I0** = ya hecho en `feat/imputacion-sv-i1-20261001`; **I1** canónico pendiente con alcance ampliado); **Fase B 2026-10-02:** **I1 canónico IMPLEMENTADO** en `feat/procesadores-ubicaciones-20261001`; **post-I1 2026-10-02:** decisiones **D-I1-01..D-I1-04** (AD-89), solo documentación; **AD-90 2026-10-02:** semántica de inventario en procesador y **pendiente de consolidación documental** (complementa AD-87/88/89; **I2 sigue pendiente**); **AD-91 2026-10-02:** **I2 acotado a documental sin efecto en stock** (modelo aditivo `madenat.sv.imputation`/`.line`/`.sv.line`), **salida nativa + ledger `imputacion` a I3**, **tres saldos separados**, **idempotencia documental propia**, **severidad dura etiqueta-side / blanda SV-side**, **costo I5**, **merma/cierre posterior**; resuelve **C-1/C-2/C-3**.
**Fuente de verdad ante contradicción:** `CANON/INDICE_DOCUMENTACION.md` §8. Ante contradicción entre documentos, **no se elige versión en silencio**: se registra y se declara (ver §13).

> **Alcance de esta versión.** Este documento es **especificación y diseño**. **No** autoriza ni contiene cambios de código, datos ni parámetros. Las reglas marcadas **[DISEÑO]** son objetivos; las marcadas **[VIGENTE]** describen comportamiento ya implementado y verificado en código (rama `feat/rebaja-contenedor-20261001`, BD `madenat_test`).

---

## 1. Propósito y alcance

Fijar, como fuente única de verdad, **cómo se vincula** la madera procesada que retorna del procesador (con **etiquetas** y dimensionada bruta con **tarjas**) con el **volumen comprado (SV)** que la originó, sin genealogía física, y **cómo se controla el saldo de SV que queda en poder de cada procesador**.

Incluye: glosario, ciclo completo por tipo de compra, modelo de datos mínimo, estados, reglas, alertas, roles, UX propuesta, casos límite, migración, riesgos, clasificación de bloqueos y plan de pruebas. El **backlog por fases I1..I6** se detalla en §16 y se refleja en `05_BACKLOG.md`.

**Fuera de alcance:** valorización contable, facturación y auditoría financiera (diferidas por AD-81); la consolidación/rebaja de contenedores y naves para **exportación** (documento `18`, aplicable a lotes de **tarja**).

---

## 2. Glosario

| Término | Definición operativa (MADENAT) | Modelo/campo base |
|---|---|---|
| **Trader** | Rol de MADENAT: **compra** madera (volumen o procesada) y la **revende**; no transforma físicamente. La transformación la ejecuta un **procesador externo**. | — |
| **SV (Lote Volumen / etiqueta SV)** | Lote de **volumen comprado** sin desglose de piezas. Identidad `SV` + 11 dígitos (`stock.lot.name`, secuencia `madenat.volume.lot`), `lot_flow_type='volume'`. Es la **base de stock y valorización** (NOMINAL). **Nunca se exporta.** | `stock.lot`, `madenat.sv.operation` |
| **Etiqueta (de retorno)** | Identificador de un bulto de **madera procesada** que retorna del procesador: etiqueta física del proveedor (`stock.lot.ref` / `supplier_label` / `external_labels`) o etiqueta del procesado. Es un **lote nuevo e independiente** (`lot_flow_type='tarja'` o vacío). | `stock.lot` |
| **Tarja** | Documento/unidad de **madera dimensionada bruta** recibida o despachada (piezas con dimensiones). Vive en lotes de **tarja**. | `stock.lot`, documentos de tarja |
| **Imputación (declarada)** | Acto administrativo que **declara** qué etiqueta(s) de retorno corresponden a qué SV. **No es genealogía física**: es la relación **volumen nominal declarado** etiqueta→SV. **En I2 es un acto exclusivamente documental** (sin efecto en stock); el **ledger `imputacion`** y la **salida nativa** se ejecutan en **I3** (§4.3, §16; **AD-91**). | propuesto: `madenat.sv.imputation` |
| **Procesador** | Planta externa (cepillado, secado, tratamiento, …) que transforma el SV. Se marca en el maestro de partners. | `res.partner.is_processor` |
| **En poder del procesador X** | **Ubicación interna** de stock por procesador (`stock.location`, `usage='internal'`) bajo un padre **`Procesadores`**. Representa **inventario propiedad de MADENAT bajo custodia operativa** del procesador (no es consignación ni propiedad ajena). **AD-90.** | `stock.location` |
| **SV en procesador / pendiente de consolidación documental** | Un **SV** (o saldo) que reside en `Procesadores/<X>` se clasifica operativamente como **pendiente de consolidación documental** con los **productos procesados** que retornan de ese procesador. **No** implica venta, exportación, rebaja, consumo, merma ni genealogía física. **AD-90.** | `stock.quant`, `stock.lot` |
| **Saldo por procesador (físico)** | **Saldo físico** (nominal/disponible) que **permanece** en la ubicación del procesador; es una **vista sobre `stock.quant`** (sin modelo persistente), agrupable por procesador/producto/tipo de lote. **AD-89/AD-90.** | `stock.quant` (vista `madenat.processor.balance`) |
| **Saldo documental pendiente de consolidación** | Volumen **declarado** aún **no consolidado** (etiqueta→SV). Es **distinto** del saldo físico: convive con él y alimenta las **alertas de pendientes** (AD-90; §7.3, §8). | propuesto: consolidación (fase I2) |
| **Merma** | Diferencia entre el volumen SV enviado y el volumen de retorno **imputado**. Es un **evento documental**: no dispara `stock.scrap` automático (§7, §11). | propuesto: evento de merma con costo residual |
| **Ledger SV** | Registro **append-only** de operaciones sobre etiquetas SV. | `madenat.sv.operation` |

### 2.1 Los dos tipos de compra (D1)

| # | Tipo de compra | Producto recibido | ¿Genera SV? | ¿Se imputa? |
|---|---|---|---|---|
| **C1** | **Compra de volumen** | Volumen total (m³) sin desglose de piezas | **Sí** (etiqueta SV) | **Sí** (objeto de este documento) |
| **C2** | **Compra de madera procesada** | Madera procesada con **etiquetas** y dimensionada bruta con **tarjas** | No | No (flujo normal de ingesta; `12`/`13`) |

**Regla [DISEÑO]:** el **SV nunca se exporta**. La exportación opera exclusivamente sobre lotes de **tarja** (documento `18`). El vínculo SV↔etiqueta de retorno (C1) es siempre una **imputación declarada**, nunca genealogía física.

---

## 3. Ciclo completo por tipo de compra (D1)

### 3.1 Compra de volumen (C1) — núcleo del documento

```
COMPRA DE VOLUMEN (SV)
   │  Recepción por Volumen: se crea la etiqueta SV (nominal = oficial = export)
   │
   ├── (v1) SV en BODEGA MADENAT (patio = stock.location interno)
   │        └── se envía a procesar ──► transferencia interna a  Procesadores/<X>
   │
   └── (v2) SV DIRECTO AL PROCESADOR (nunca ingresa físicamente a bodega MADENAT)
            └── el SV queda en  Procesadores/<X>  (inventario MADENAT)

   … el procesador transforma (sin trazabilidad física de mezcla) …

RETORNO DE MADERA PROCESADA  (guía de procesados: etiquetas + tarjas, dimensionada bruta)
   │  Se recibe la guía de procesados  ──►  ASISTENTE DE IMPUTACIÓN
   │        · propuesta automática por proveedor / producto / antigüedad (§10)
   │        · Operaciones confirma o deja PENDIENTE (§6)
   │
   ▼
IMPUTACIÓN DECLARADA (etiqueta → uno o varios SV)
   │  I2 · registro DOCUMENTAL (madenat.sv.imputation/.line/.sv.line) — SIN efecto en stock
   │  I3 · registra el ledger SV  (madenat.sv.operation, tipo `imputación`)
   │     · genera la SALIDA NATIVA del quant del SV (AD-82/AD-84)  ◄── único punto de salida del SV
   │  I5 · escribe/actualiza el costo de la etiqueta (stock.lot.cost.line, cost_type='wood')
   │  post · si hay merma, registra el evento documental de merma (§7, §11)
   ▼
ETIQUETA PROCESADA (stock nuevo e independiente, lot_flow_type='tarja'/vacío)
   └── sigue el flujo normal (ingesta / consolidación / exportación de `18`)
```

**Claves [DISEÑO]:**
- La imputación es **la vía única** por la que el volumen SV "sale" del stock (su quant se descuenta en el momento de imputar). No hay descuento del SV vía contenedor de exportación (el SV no se exporta).
- **Reparto de fases (AD-91):** en **I2** la imputación es **documental y sin efecto en stock**; la **salida nativa** y el **ledger `imputacion`** se ejecutan en **I3**; el **costo**, en **I5**; la **merma**, en fase **posterior**. La imputación sigue siendo la **vía única** de salida del SV, materializada en **I3**.
- El **retorno es stock nuevo e independiente** (AD-65 §1.6; alineado con DEC-002). El vínculo con el SV es **declarado**, no físico (D2).
- **Semántica de inventario en procesador (AD-90):** mientras el SV está en `Procesadores/<X>` se clasifica como **pendiente de consolidación documental**; es **inventario de MADENAT bajo custodia operativa** del procesador. La **recepción directa** (v2) y la **transferencia interna desde bodega** (v1) son **rutas físicas equivalentes** para el saldo físico. El envío al procesador **no** es venta, exportación, rebaja, consumo, merma ni genealogía.
- **Órdenes temporales válidos (AD-90):** (a) **etiquetas primero → consolidación después** (caso de §3.1); (b) **consolidación declarada primero → etiquetas registradas después**. Ambos son válidos y pueden **coexistir** etiquetas sin consolidar con el SV en procesador; el sistema **controla pendientes y alerta**, **sin bloquear** (AD-88).

### 3.2 Compra de madera procesada (C2) — flujo normal

No hay SV ni imputación: la madera llega procesada con etiquetas/tarjas y se ingesta por los flujos vigentes (`12_FLUJOS_INGESTA.md` §3 y §4; `13_CONSOLIDACION_OPERATIVA.md` §3–§4). Aplica la genealogía `parent_lot_id` **solo cuando el usuario la declare** (opcional, §5.6, D10).

### 3.3 Variante de ubicación del SV

| Variante | Dónde vive el SV al comprarlo | Salida nativa al imputar |
|---|---|---|
| **v1 — Bodega** | Ubicación interna de patio MADENAT | Desde la ubicación vigente del SV (patio o `Procesadores/<X>` si ya se envió) a `Virtual Locations/Production` (o a la ubicación del procesador si aún no se movió). |
| **v2 — Directo a procesador** | `Procesadores/<X>` (nunca toca bodega) | Desde `Procesadores/<X>` a `Virtual Locations/Production`. |

Ambas variantes usan la **misma** imputación y el **mismo** ledger; solo cambia la ubicación de origen del `stock.move`.

**Equivalencia física (AD-90).** Para el **saldo físico** las dos variantes son **equivalentes**: el quant del SV queda en `Procesadores/<X>` tanto si llegó por **recepción directa** como si llegó por **transferencia interna** desde bodega. La ruta es una **decisión operativa** y **no** cambia la semántica, el saldo documental pendiente ni los estados de productos procesados.

---

## 4. Qué es (y qué no es) la imputación

### 4.1 Definición [DISEÑO]

La **imputación** es un registro administrativo que declara la correspondencia **de volumen** entre:
- **un conjunto de etiquetas de retorno** (madera procesada recibida), y
- **uno o varios SV** (etiquetas SV compradas).

**Unidad de captura:** la **etiqueta** (D3), con su **volumen NOMINAL editable**. La etiqueta se imputa contra **uno o varios SV**; un SV puede recibir imputaciones de **varias** etiquetas mientras tenga saldo.

> **Prevalencia AD-91 (alcance de I2).** En la fase **I2** la imputación es un **acto exclusivamente documental** (sin efecto en `stock.quant`). El **ledger `imputacion`** y la **salida nativa** descritos en §4.3 pertenecen a **I3**; el **costo**, a **I5** (§16). Esta prevalencia **acota el alcance de I2** y **no** deroga el **modelo objetivo** de §4.3, que rige **desde I3**.

### 4.2 La imputación NO es genealogía física (D2)

- No se crea vínculo lote-a-lote padre/hijo (`parent_lot_id`/`child_lot_ids`) por la imputación.
- El procesador externo **mezcla** físicamente el material: la correspondencia real es desconocida. La imputación es una **declaración profesional** con motivo y auditoría, consistente con `AD-65 §1.6`.
- El retorno es **stock nuevo e independiente** (alineado con DEC-002).

### 4.3 Efectos (D3) — materializados en I3/I5, **no** en I2

> **Alcance de fase (AD-91).** Los efectos que siguen describen el **modelo objetivo** y se ejecutan **fuera de I2**: (1) ledger y (2) salida nativa, en **I3**; (3) costo, en **I5**. En **I2** la imputación **no** produce efecto alguno en stock ni en el ledger.

1. **Ledger (I3):** una o más operaciones en `madenat.sv.operation` con `action_type = 'imputacion'` (§5.3), motivo obligatorio y firma (política AD-79/AD-80).
2. **Salida nativa (I3):** un `stock.move`/picking **outgoing** que descuenta la **cantidad imputada** del quant del SV, desde su ubicación vigente hacia `Virtual Locations/Production`. Es el **único** descuento del SV (AD-82/AD-84).
3. **Costo (I5):** escribe la línea de costo de madera de la etiqueta (`stock.lot.cost.line`, `cost_type='wood'`) con el **costo promedio ponderado** de los SV elegidos (§5.5).

### 4.4 Relación con AD-82 / AD-83 / AD-84

| AD | Estado previo | Efecto de este documento |
|---|---|---|
| **AD-82** (salida única de stock al rebajar) | Aprobada e implementada (contenedores/naves) | **Se alinea:** AD-82 rige la **exportación de tarja**; el SV **no** se exporta; su salida única es la **imputación** (§3.1). |
| **AD-83** (módulo propio rebaja SV + descuento por procesados) | Aprobada **en principio** | **REEMPLAZADA por AD-87** (ver §13 y `04_DECISION_LOG.md`): el "descuento por procesados" se materializa como **imputación**; no se extrae módulo propio de rebaja SV; la asignación SV a contenedor de **exportación** deja de ser el caso de uso (el SV no se exporta). |
| **AD-84** (invariantes) | Aprobada e implementada (parcial) | **Se amplía:** el saldo SV resta **también** las imputaciones activas (§5.3, §7); la causa única de descuento del SV es la imputación. La ampliación de `sv_available_m3` se materializa en **I3**; **en I2 el ledger no se altera** (AD-91). |

---

## 5. Modelo de datos mínimo [DISEÑO]

Reutiliza el máximo de lo existente (`stock.lot`, `madenat.sv.operation`, `res.partner`, `stock.location`, `stock.lot.cost.line`). Solo se proponen **añadidos**; **sin renombres**.

### 5.1 Cabecera — `madenat.sv.imputation` (modelo nuevo propuesto)

| Campo | Tipo | Requerido | Notas |
|---|---|---|---|
| `name` | Char (secuencia `madenat.sv.imputation`) | ✔ | Identificador de la imputación |
| `date` | Date | ✔ | Fecha de la imputación |
| `company_id` | M2O `res.company` | ✔ | Patrón del ledger SV |
| `guia_processing_id` | M2O `madenat.guia.processing` | ✔ | Guía de procesados que origina el retorno (momento D6) |
| `processor_id` | M2O `res.partner` (`is_processor`) | ✔ | Procesador (retorno) |
| `processor_location_id` | M2O `stock.location` | ✔ | Ubicación `Procesadores/<X>` (origen o destino del SV) |
| `line_ids` | O2M `madenat.sv.imputation.line` | ✔ | Etiquetas imputadas (§5.2) |
| `sv_line_ids` | O2M `madenat.sv.imputation.sv.line` | ✔ | SV consumidos (§5.2) |
| `state` | Selection (`draft`/`pending`/`applied`/`reversed`/`cancelled`) | ✔ | §6 |
| `cost_per_m3_usd` | Float, digits (16, 4) | ✔ | **Editable** (D4); por defecto, promedio ponderado de los SV (§5.5) |
| `total_cost_usd` | Float (compute, store=False) | — | Σ líneas |
| `reason` | Text | condicional | Obligatorio si hay desviación de la propuesta o alerta (§7, §8) |
| `deviation_flags` | Char/Text (compute) | — | Marca las desviaciones registradas (auditoría) |
| `sv_operation_ids` | O2M `madenat.sv.operation` | — | **I3**: ledger generado (una op. `imputacion` por SV afectado); en I2 no se genera |
| `documentary_key` | Char (`copy=False`, unique) | ✔ | **Idempotencia documental de I2** (clave propia; **no** `picking_id`) |
| `picking_id` | M2O `stock.picking` (`copy=False`) | — | **I3**: la salida nativa se ejecuta una sola vez |
| `executed_by_id` / `execution_date` | M2O `res.users` / Datetime | — | Autoría (política AD-79) |
| `snapshot_json` / `audit_hash` | Text / Char | — | Evidencia firmada (política AD-79/AD-80) |

> **Organización por guía (AD-91, D-I2-15).** La cabecera se organiza **por guía de procesados** (`guia_processing_id`): una guía puede tener **muchas etiquetas** y una etiqueta puede **repartir** su **volumen nominal editable** entre **varios SV** (`.line`/`.sv.line`). Una guía admite **una sola** imputación de trabajo (`draft`/`pending`); `applied`/`reversed` son **historia inmutable** (inmutabilidad/reversa, §6). El **ledger no es cabecera** (D-I2-11). El campo `cost_per_m3_usd` pertenece a **I5** (en I2 no se usan campos de costo, D-I2-18).

### 5.2 Líneas

**`madenat.sv.imputation.line`** (una por **etiqueta de retorno**):

| Campo | Tipo | Notas |
|---|---|---|
| `imputation_id` | M2O `madenat.sv.imputation` | — |
| `processed_lot_id` | M2O `stock.lot` | Etiqueta de retorno (stock nuevo independiente) |
| `nominal_volume_m3` | Float, digits (16, 3) | **Volumen NOMINAL editable** (D3) |
| `pieces` | Integer | Opcional (si la etiqueta trae piezas) |
| `product_id` / `subproducto_id` | M2O | Del retorno |
| `sv_allocation_ids` | O2M `madenat.sv.imputation.sv.line` | Reparto (N:M) etiqueta↔SV |

**`madenat.sv.imputation.sv.line`** (una por par **etiqueta↔SV**):

| Campo | Tipo | Notas |
|---|---|---|
| `imputation_id` / `imputation_line_id` | M2O | — |
| `sv_lot_id` | M2O `stock.lot` (`lot_flow_type='volume'`) | SV origen |
| `sv_available_m3` | Float (related) | Saldo del ledger SV (**no alterado en I2**, AD-91) |
| `imputed_volume_m3` | Float, digits (16, 3) | Porción imputada desde ese SV |
| `cost_per_m3_usd` | Float, digits (16, 4) | Costo unitario del SV origen (§5.5) |
| `amount_usd` | Float (compute) | `imputed_volume_m3 × cost_per_m3_usd` |
| `sv_operation_id` | M2O `madenat.sv.operation` | Operación `imputacion` generada |

### 5.3 Tipo de acción del ledger (D3)

> **Alcance (AD-91).** El valor `'imputacion'` y el vínculo `imputation_id` corresponden a **I3**. En **I2** el ledger `madenat.sv.operation` **no** se modifica (no se añade `action_type='imputacion'` ni se altera `sv_available_m3`).

- Se **añade** el valor `'imputacion'` al Selection `madenat.sv.operation.action_type` (hoy: `rename`, `regularize_volume`, `rebaja`, `rebaja_reverse`). Etiqueta propuesta: **«Imputación a procesados»**.
- Campos de la operación reutilizados: `lot_id` (SV), `rebaja_volume_m3` (volumen imputado), `destination_reference='Imputación <procesador>'`, `reason` (obligatorio), `state='applied'` al ejecutar, `snapshot_json`/`audit_hash`.
- **Nuevo** vínculo propuesto: `imputation_id` (M2O → `madenat.sv.imputation`) en `madenat.sv.operation`, análogo a `destination_shipment_id`/`destination_container_id` ya existentes en Logistics.
- **Alternativa (si se prefiere cero cambio de Selection):** reutilizar `action_type='rebaja'` con `destination_reference='Imputación <procesador>'`. Se registra como **pregunta abierta** (§17, Q-19-1); la recomendación de este documento es el valor propio `imputacion` (trazabilidad y reporte inequívocos).
- **Saldo SV ampliado (D3, I3):** `sv_available_m3 = sv_regularized_baseline_m3 − Σ rebajas activas − Σ imputaciones activas` (§7, alinea AD-84). **En I2 `sv_available_m3` permanece intacto** (AD-91).

---

### 5.4 Ubicaciones — «En poder del procesador X» (D5)

- **Padre:** `stock.location` **`Procesadores`**, `usage='internal'` (p. ej. bajo `WH/Stock/Procesadores`). Nativo Odoo: **cero desarrollo de modelo**; se crea bajo demanda y **nunca se elimina con stock** (mismo criterio que el patio, AD-65 §1.5).
- **Hijas:** una ubicación por procesador — **`Procesadores/<PROCESADOR>`** — creada bajo demanda al enviar/registrar SV en poder de ese procesador.
- **Propiedad:** `usage='internal'` ⇒ **el inventario es de MADENAT** (no consignación). El saldo por procesador es el Σ de quants de esa ubicación.
- **Saldo por procesador:** vista/reporte de solo lectura propuesto `madenat.processor.balance` (o reporte de `madenat_lumber_reports`) agrupando `stock.quant` por ubicación bajo `Procesadores`, con nominal/disponible y antigüedad.
- **Semántica [APROBADA] (AD-90):** `Procesadores/<X>` es **inventario de MADENAT bajo custodia operativa** del procesador (**no** consignación ni propiedad ajena); un **SV** allí está **pendiente de consolidación documental** con productos procesados. El **envío al procesador** **no** es venta, exportación, rebaja, consumo, merma ni genealogía física. La **recepción directa** en `Procesadores/<X>` y la **transferencia interna** desde bodega son **rutas físicas equivalentes** para el saldo físico.
- **Saldo físico vs. documental (AD-90):** el **saldo físico** = Σ `stock.quant` en `Procesadores/<X>` (fuente de verdad, AD-89); el **saldo documental pendiente** = volumen declarado aún **no consolidado**. **Coexisten** sin bloquear la operación normal; un SV puede convivir temporalmente con etiquetas procesadas recibidas del mismo procesador aunque la consolidación documental todavía no se aplique.

### 5.5 Costo (D4) — **I5** (fuera de I2)

> **Alcance (AD-91, D-I2-18).** Todo lo de esta sección corresponde a **I5**. **En I2 no se crean** campos de costo, reglas de prorrateo ni líneas `stock.lot.cost.line`. El campo `cost_per_m3_usd` de §5.1 solo se usa a partir de **I5**.

- **Brecha documentada:** hoy el **SV no tiene costo** — `wood_cost_usd`/`purchase_price_usd_per_m3` vacíos para lotes `lot_flow_type='volume'` y el costeo nativo de Odoo desactivado de facto (`08_COSTEO.md` §1.4, AD-64). Sin costo del SV, la etiqueta de retorno **no puede** heredar costo de madera.
- **Costo por m3 editable** en la imputación (`cost_per_m3_usd`, D4). Por defecto se propone el **promedio ponderado** de los SV elegidos:
  `costo_prom = Σ(imputed_volume_m3 × cost_sv_m3) / Σ(imputed_volume_m3)`.
- **Fuente propuesta para el costo del SV:** derivarlo de la **guía de Recepción por Volumen** de origen (OC/guía asociada), como `total_amount_usd / official_volume_m3` (si la compra es por m³) o desde el precio unitario de la OC. **A construir en la fase I5** (§16); **pregunta abierta** Q-19-2 (§17).
- **Destino del costo:** `stock.lot.cost.line` con `cost_type='wood'`, `partnerid = processor_id`, `date = date`, `amount_usd = nominal_volume_m3 × cost_per_m3_usd`. El **total** de la imputación debe cuadrar con Σ `imputed_volume_m3 × costo` (merma ⇒ §7, §11).

### 5.6 `parent_lot_id` opcional (D10 — paso futuro controlado)

- Hoy la genealogía (`parent_lot_id`/`child_lot_ids`) es **físico-trazable** y aplica a procesados declarados. Con la imputación (que **no** usa genealogía), `parent_lot_id` **pasa a ser opcional** en un **paso futuro controlado** (fase I6): migración de la restricción/`required` y de los consumidores (`madenat_toll_processing`). **No se ejecuta en esta fase documental** (§12, §16).

---

## 6. Estados de la imputación (D6)

| Estado | Significado | Efectos | Quién |
|---|---|---|---|
| `draft` | En preparación por el asistente | Sin efectos; se guarda la propuesta | Operaciones |
| `pending` | **Dejada pendiente** al recibir la guía (opción explícita, D6) | Sin descuento de SV; **alerta** de pendiente (§8) | Operaciones |
| `applied` | Ejecutada — **inmutable** | **I2:** solo documento; **I3:** ledger `imputación` + **salida nativa**; **I5:** costo | Operaciones |
| `reversed` | Reversada | **I3:** contrapartida (retorno nativo + op. SV opuesta ligada) | Jefatura / Gerencia |
| `cancelled` | Anulada sin efecto | No hubo salida | Operaciones / Jefatura |

**Regla [DISEÑO]:** una guía de procesados puede validarse con su imputación en `pending`; el sistema **no bloquea** (D8). La pendiente se **audita** y alimenta las alertas de saldo por procesador.

**Cabecera por guía e inmutabilidad (AD-91, D-I2-15).** La imputación se organiza **por guía de procesados**: una guía admite **una sola** imputación de **trabajo** (`draft`/`pending`). Al pasar a **`applied`** queda **inmutable** y pasa a **historia** junto con `reversed`/`cancelled`; toda corrección se hace por **reversa + nueva imputación**, nunca editando ni borrando historia. En **I2** los estados describen **solo** el ciclo documental: **ninguno** produce efecto en stock (el ledger y la salida nativa son **I3**).

**Reserva documental temporal de etiqueta vs. saldo documental aplicado de SV (precisión AD-91, 2026-10-02).** Se distinguen **dos conceptos** que no deben confundirse:
- **(a) Reserva documental temporal de capacidad nominal de etiqueta** — `I2_ACTIVE_STATES = ('draft', 'pending', 'applied')`. Materializa el **techo DURO** por etiqueta (§7.1): `draft` y `pending` **reservan temporalmente** la capacidad nominal de la etiqueta (impiden que **dos trabajos paralelos** sobre-imputen la misma etiqueta) **sin efecto alguno**; `applied` la consume de forma definitiva mientras no se revierta. `reversed`/`cancelled` **no** cuentan.
- **(b) Saldo documental aplicado de SV** — `I2_DOCUMENTAL_STATES = ('applied',)`. Solo las imputaciones **`applied`** consolidan el saldo documental del SV; `draft`/`pending` **no** lo consolidan (solo reservan la capacidad nominal de la etiqueta). La comprobación **blanda** de exceso SV-side (§7.2) evalúa el compromiso en estados **activos** como advertencia temprana.

**Efecto por estado (I2 documental).** `draft`/`pending` **no** mueven stock, **no** alteran `sv_available_m3`, **no** modifican el ledger `madenat.sv.operation` y **no** crean reserva física ni descuento documental del SV (el descuento del SV, si corresponde, es **I3**). `pending` deja el trabajo **preparado** y **mantiene la reserva documental temporal de la etiqueta** hasta **aplicar**, **cancelar** o **reversar** según corresponda. **Sin cambio funcional.**

---

## 7. Reglas

### 7.1 Reglas duras (integridad técnica / financiera)

- **[DISEÑO — duro, I2]** El **volumen nominal editable** de una **etiqueta** es un **techo duro**: Σ imputaciones **activas/aplicadas no revertidas** de esa etiqueta **no** puede excederlo (D-I2-16a).
- **[VIGENTE — I3]** Ningún `stock.move` puede dejar `stock.quant` **negativo**. La salida nativa del SV nunca excede el disponible del quant (techo técnico).
- **[VIGENTE]** Los **permisos por rol** se validan en servidor (patrón `_rebaja_require_group`, AD-86/16).
- **[VIGENTE]** **Reglas financieras**: tipo de cambio, cierre de período y UoM (m³, `digits=(16,3)`) permanecen **duras**.
- **[DISEÑO — I3]** La salida nativa del SV ocurre **una sola vez** por imputación (idempotencia por `picking_id`, causa única AD-84); **en I2 no aplica** (el ledger no se altera).
- **[DISEÑO]** Los **invariantes** de AD-84 se mantienen verificables (§7.3).

### 7.2 Reglas blandas (D8: advertir, motivar, auditar)

- **SV-side (blando, I2):** si el volumen imputado **supera el saldo documental disponible** de un SV → **advertencia**, se exige **motivo**, se **audita `deviation`** y **se permite aplicar** (D-I2-16b). El techo **técnico** del quant rige solo en **I3** (en I2 no hay salida nativa).
- **Etiqueta-side es DURO, no blando:** exceder el **volumen nominal editable** de una etiqueta **no** es advertencia; se **rechaza** (§7.1, D-I2-16a).
- **Sin tolerancias ni `AL-01..AL-07` en I2** (D-I2-16c): no se inventan umbrales; los de diseño quedan para fases posteriores.
- Si el volumen nominal de la etiqueta **difiere** de la propuesta automática más allá de una tolerancia (por decidir, §17 Q-19-4) → **advertencia + motivo**.
- Si el **costo por m3** está fuera de rango (respecto del histórico del producto/SV) → **advertencia + motivo**.
- Si el procesador no está marcado `is_processor` o no existe ubicación `Procesadores/<X>` → **advertencia**; se ofrece crearla (nativo).
- **[DISEÑO]** Todo lo anterior se registra en `deviation_flags` y en el snapshot de auditoría.

### 7.3 Invariantes (alineados con AD-84, ampliados)

1. `stock.lot.volumen_restante_m3 = Σ stock.quant.quantity` (ubicaciones internas, base NOMINAL).
2. **Saldo SV ampliado (I3):** `stock.lot.sv_available_m3 = sv_regularized_baseline_m3 − Σ rebajas activas − Σ imputaciones activas`. **En I2 `sv_available_m3` (`_sv_balance_values`) permanece intacto** (D-I2-12); la ampliación se materializa en **I3**.
3. **Cota por destino (I3):** Σ (rebajas + imputaciones) por SV ≤ volumen oficial (NOMINAL) del lote.
4. **Causa única de descuento del SV:** **imputación** (procesados) o ajuste autorizado; la rebaja aplica solo a lotes de **tarja** en export (AD-82). Sin dobles descuentos.
5. **Concurrencia fail-closed** del ledger (guarda `_sv_concurrency_guard`).
6. **Cuatro categorías de saldo (AD-90), sin mezclarlas:**
   - (a) **saldo físico** en `stock.quant` (ubicaciones internas, incluida `Procesadores/<X>`) — única **fuente física de verdad** (AD-89);
   - (b) **saldo documental pendiente de consolidación** (volumen declarado aún **no** consolidado etiqueta→SV);
   - (c) **productos procesados pendientes de imputar** (etiquetas de retorno sin imputación activa);
   - (d) **productos procesados ya imputados/consolidados** (vínculo declarado a un SV explícito).
   (b) y (c) **alimentan las alertas** (§8) y **no bloquean** la operación (AD-88); un SV en `Procesadores/<X>` puede **coexistir** con etiquetas procesadas sin consolidar.
7. **Saldo documental (I2) — dos magnitudes distintas (§6).** (a) **reserva documental temporal de capacidad nominal de etiqueta** = Σ imputaciones **activas/aplicadas no revertidas** (`I2_ACTIVE_STATES`), techo **duro**; (b) **saldo documental aplicado de SV** = Σ imputaciones **`applied`** (`I2_DOCUMENTAL_STATES`). Ambas son **distintas** de: (i) saldo **físico** (`stock.quant`); (ii) **`sv_available_m3`** del ledger; (iii) **merma documental** (no automática). **Duro** etiqueta-side (techo nominal, §7.1) y **blando** SV-side (advertir + motivo + auditar, permitir aplicar; §7.2) (D-I2-13, D-I2-16). **Sin merma automática** (D-I2-19).

---

## 8. Alertas

> **Alcance (AD-91).** Las alertas `AL-01..AL-07` son **diseño** para **fases posteriores**; **no se implementan en I2**, que **no** define tolerancias ni umbrales (§7.2, D-I2-16c). En I2 solo aplican la **regla dura** etiqueta-side y la **blanda** SV-side (§7.1/§7.2).

| ID | Alerta | Disparador | Destino |
|---|---|---|---|
| AL-01 | **Imputación pendiente** | Imputación en `pending` > umbral de días (a decidir) | Operaciones |
| AL-02 | **Saldo por procesador ≠ 0 al cierre** | Σ quant en `Procesadores/*` > 0 al cierre de período | Operaciones / Auditoría |
| AL-03 | **SV sin retorno** | SV con antigüedad > umbral sin imputación | Operaciones |
| AL-04 | **Desviación de volumen** | `abs(nominal − propuesta) > tolerancia` | Auditoría |
| AL-05 | **Costo fuera de rango** | `cost_per_m3_usd` fuera del histórico | Costos / Auditoría |
| AL-06 | **Merma sin documento** | Diferencia SV enviado − retorno imputado sin evento de merma | Auditoría |
| AL-07 | **Procesador/ubicación no registrados** | `is_processor=False` o sin ubicación hija | Operaciones |

Las alertas son **informativas** (patrón de advertencia no bloqueante) y quedan en el reporte de saldo por procesador / chatter / `madenat.audit.log`.

---

## 9. Roles y autorización (D6, D8)

| Acción | Operaciones | Jefatura Oper. | Costos | Auditoría | Gerencia |
|---|---|---|---|---|---|
| Preparar imputación (asistente) | ✅ | ✅ | ❌ | Lectura | Lectura |
| **Dejar pendiente** | ✅ | ✅ | ❌ | Lectura | Lectura |
| **Aplicar imputación** | ✅ | ✅ | ❌ | Lectura | Lectura |
| Reversar imputación | ❌ | ✅ | ❌ | Lectura | ✅ |
| Editar costo por m3 | ❌ | ✅ | ✅ | Lectura | Lectura |
| Revisar desviaciones (AL-04/05/06) | ❌ | Lectura | Lectura | ✅ | Lectura |

**Regla [DISEÑO]:** los permisos por rol son **duros** (rechazo en servidor). El **resto** de las validaciones de negocio son **blandas** (advertir + motivo + auditar, D8). Reutiliza los grupos vigentes (`group_madenat_operaciones`, `_jefatura_operaciones`, `_costos`, `_auditoria`, `_gerencia`); **no** crea grupo nuevo (AD-86 sigue PROPUESTA).

---

## 10. UX propuesta

### 10.1 Momento (D6)

Al **recibir la guía de procesados**, el flujo abre el **Asistente de Imputación** con la propuesta automática ya calculada. El operador puede:
- **Confirmar** (aplica),
- **Ajustar** volúmenes/etiquetas/SV y confirmar (con motivo si se desvía),
- **Dejar pendiente** (`pending`) y continuar con la guía (no bloquea).

### 10.2 Propuesta automática (proveedor / producto / antigüedad)

Para cada etiqueta de retorno, el asistente propone la distribución de su **volumen NOMINAL** contra los SV candidatos, con esta prioridad:

1. **Proveedor / procesador** — SV enviados al mismo `processor_id` (`Procesadores/<X>`).
2. **Producto / subproducto** — SV de la misma familia comercial.
3. **Antigüedad** — **FIFO** (SV más antiguos primero), hasta agotar el nominal de la etiqueta.

Reparto resultante: la etiqueta se **desglosa** en una o varias asignaciones etiqueta↔SV (`madenat.sv.imputation.sv.line`) que suman su nominal. El operador puede editar el reparto, el nominal y el costo.
**Elegibilidad de candidato SV (I2 — precisión 2026-10-02, AD-91).** Se considera **candidato SV** de una imputación el lote `lot_flow_type='volume'` que cumple: (a) **visibilidad multi-company estándar** (compañía operativa **o** `company_id=False`); (b) **saldo documental I2 estrictamente positivo** — `_i2_sv_documental_available_m3 > 0` = nominal SV − Σ imputaciones en estados **activos** (`draft`/`pending`/`applied`; `reversed`/`cancelled` **no** consumen); (c) si la imputación tiene `processor_location_id`, **quant interno positivo** en esa ubicación o su árbol. Si **no** hay procesador configurado, **no** se excluye. Proveedor/producto **no** son filtros duros: solo **prioridad** (procesador → producto → antigüedad **FIFO**, desempate `create_date`/`id`). El flag blando `NO_SV_CANDIDATE` existe solo si la imputación **tiene etiquetas, no tiene `sv_line_ids` y no tiene candidato elegible**; el mismo dominio lo comparten la propuesta FIFO (`_i2_propose_fifo`, sin fallback al nominal) y el guard previo a aplicar. **No** se usa `sv_available_m3` del ledger ni el stock físico como sustituto del saldo documental (D-I2-13).



### 10.3 Asistente de contenedores — ocultar SV por defecto (D9)

En el asistente de asignación a contenedor (`lumber.container.lot.wizard`) los **lotes SV (`lot_flow_type='volume'`) se ocultan por defecto** (filtro de visibilidad). **No se impide** seleccionarlos: el filtro es una elección de UX (el SV no se exporta), reversible por el usuario. Alineado con §2.1 (SV nunca se exporta).

### 10.4 Trazabilidad visible

- Bloque «Imputación» en la guía de procesados y en la Consola: SV origen, volumen imputado, saldo restante, costo, motivo y desviaciones.
- Saldo por procesador visible (reporte `madenat.processor.balance`).
- Historial del ledger SV (append-only) y `madenat.audit.log` con firma.

---

## 11. Casos límite

> **Alcance (AD-91).** Las referencias a **salida nativa**, **reversa con retorno nativo** y **quant** describen el **modelo objetivo (I3)**. En **I2** el caso se resuelve **documentalmente**, sin efecto en stock.

| # | Caso | Tratamiento propuesto |
|---|---|---|
| L-01 | **Etiqueta imputada a varios SV** | Permitido: la etiqueta se desglosa en N asignaciones que suman su nominal (§10.2). |
| L-02 | **Varias etiquetas a un SV** | Permitido mientras haya saldo (Σ imputado ≤ saldo SV); si excede → advertencia + motivo (§7.2), nunca quant negativo. |
| L-03 | **SV parcialmente en bodega y parcialmente en procesador** | La salida nativa toma el disponible desde la ubicación vigente del SV; el saldo por procesador refleja solo lo enviado. |
| L-04 | **Merma** (retorno imputado < SV enviado) | **Evento documental** de merma (§5.5, AD-64/AD-65 deuda): no dispara `stock.scrap` automático; deja el **costo residual visible**. Requiere documento/motivo (AL-06). |
| L-05 | **Devolución del procesador** (retorno parcial o rechazo) | Reversa de imputación (`reversed`): retorno nativo + op. SV opuesta; no borra historia. |
| L-06 | **SV directo a procesador** (v2, §3.3) | Misma imputación; origen del `stock.move` = `Procesadores/<X>`. |
| L-07 | **`parent_lot_id` opcional** (D10) | Paso futuro controlado (I6). Hasta entonces, la imputación **no** escribe genealogía. |
| L-08 | **Imputación pendiente y período cerrado** | La imputación pendiente **no** cruza el cierre financiero: al cerrar, las pendientes se alertan (AL-01/AL-02); su aplicación posterior respeta el período (regla financiera dura). |
| L-09 | **Procesador no registrado / sin ubicación** | Advertencia (AL-07); se ofrece crear `Procesadores/<X>` bajo demanda. |
| L-10 | **Retorno sin SV disponible** | Advertencia + motivo; si no hay quant, se bloquea por techo técnico (§7.1). |
| L-11 | **Guía de procesados sin etiquetas** (granel de retorno) | Fuera de alcance de esta versión; se registra como **pregunta abierta** Q-19-3 (§17). |

---

## 12. Migración y compatibilidad

### 12.1 Datos existentes

- **Lotes SV históricos sin imputación:** **no se reescriben**. La imputación se resuelve en **nuevas** operaciones (mismo criterio que `18` §10.1 y AD-79 §14.3: corrección solo por operación formal con motivo, nunca por edición directa).
- **Lotes de tarja existentes:** sin cambio. La genealogía `parent_lot_id` **se conserva** hasta el paso controlado I6.
- **Guías de procesados ya validadas:** no se reprocesan; su imputación queda `pending`/`draft` si se desea regularizar, con motivo.

### 12.2 Ubicaciones

- **`Procesadores` y `Procesadores/<X>`:** se crean **bajo demanda**; **nunca** se eliminan con stock (nativo Odoo). Mismo patrón que el patio (AD-65 §1.5).
- **Reubicación del SV:** mover el quant del SV entre patio y `Procesadores/<X>` es una **transferencia interna nativa** (no un ajuste). No altera nominal ni valorización.

### 12.3 Modelo y estados

- Solo **añadidos**: modelo `madenat.sv.imputation(.line,.sv.line)`, valor de `action_type='imputacion'`, campos opcionales en `madenat.sv.operation` (`imputation_id`) y `res.partner`/`stock.lot` según §5. **Sin renombres.** En **I2** solo se añaden los **modelos documentales** y los apoyos `res.partner`/`stock.lot`; el valor `action_type='imputacion'` y `imputation_id` en `madenat.sv.operation` son **I3** (AD-91).
- Campos nuevos **no `required`** sobre registros históricos.

### 12.4 `parent_lot_id` opcional (I6)

- Paso **controlado y separado**: revisar consumidores (`madenat_toll_processing`, `12`/`13`) antes de relajar `required`/restricción. **No** en esta fase.

---

## 13. Riesgos y contradicciones

### 13.1 Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| R-19-01 | **Doble descuento del SV** (imputación + rebaja de export) | SV nunca se exporta (§2.1); causa única = imputación (§7.3.4); idempotencia por clave documental propia (**I2**) y por `picking_id` en la salida nativa (**I3**). |
| R-19-02 | **Saldo SV ⟷ quant desalineado** | Invariante §7.3.2; salida nativa atómica con el ledger. |
| R-19-03 | **Costo del SV inexistente** | Brecha declarada (§5.5); costo por m3 editable + fuente propuesta; fase I5. |
| R-19-04 | **Imputación declarada sin evidencia física** | Por diseño (D2); motivo obligatorio + auditoría + snapshot firmado. |
| R-19-05 | **Uso indebido de ubicación interna** (confundir con consignación) | `usage='internal'` documentado (§5.4); el inventario es MADENAT. |
| R-19-06 | **Exceso de volumen** sobre el saldo | **Duro** etiqueta-side (techo nominal, rechazo, §7.1); **blando** SV-side (advertencia + motivo + `deviation`, permite aplicar, §7.2). |
| R-19-07 | **Pendientes que cruzan el cierre** | AL-01/AL-02 + regla financiera dura (§7.1, L-08). |

### 13.2 Contradicciones resueltas por este documento

| # | Contradicción | Resolución |
|---|---|---|
| CR-19-01 | `17` §2.8 / AD-83: la rebaja SV **solo** mueve el ledger **sin** efecto en `stock.quant` vs. D3 (el SV sale del quant al imputar). | **Reencuadre:** para el caso **procesados**, la imputación **sí** tiene efecto nativo (salida del quant SV) — materializado en **I3**; **en I2 la imputación es documental** (AD-91). La rebaja de contenedores del `18` (sin efecto en quant del SV) deja de aplicar al SV (el SV no se exporta). Se actualiza `17` §2.8 y `18`. |
| CR-19-02 | `18` §1.3/§5: «rebajar» el SV a contenedor (export) vs. D1 (SV nunca se exporta). | **Resuelto:** la consolidación/rebaja de export aplica solo a lotes de **tarja**; se actualiza `18` §1.3/§5/§7. |
| CR-19-03 | AD-65 §1.6 usa `parent_lot_id`/genealogía de forma condicional vs. D2 (imputación declarada, sin genealogía). | **Alineado:** la imputación **no** usa genealogía; `parent_lot_id` pasa a opcional en I6 (D10). |
| CR-19-04 | AD-64 registra la brecha de costo pero no el caso SV (SV sin costo) vs. D4. | **Ampliado:** AD-64 se extiende con el costo del SV y su fuente propuesta (§5.5). |
| CR-19-05 | AD-83 (módulo propio rebaja SV) vs. D3 (imputación sin módulo nuevo). | **AD-83 REEMPLAZADA por AD-87** (§4.4, §16). |
| **C-1** (CR-19-06) | §4.3/§5.3 asignaban a la **imputación (I2)** el **ledger** (`action_type='imputacion'`) y la **salida nativa** del quant del SV. | **Prevalencia AD-91 (D-I2-12):** I2 es **documental y sin efecto en stock**; el **ledger `imputacion`** y la **salida nativa** se ejecutan en **I3**. No se añade `action_type='imputacion'` ni se toca `stock.quant`/`picking`/`move` en I2. |
| **C-2** (CR-19-07) | §5.3/§7.3.2 ampliaban `sv_available_m3`/`_sv_balance_values` con las **imputaciones activas**, mezclándolo con el **saldo documental**. | **Prevalencia AD-91 (D-I2-12/13):** `sv_available_m3` **no se altera en I2**; el **saldo documental de consolidación** es una magnitud **propia**, computada solo desde imputaciones activas/aplicadas no revertidas del **modelo nuevo**, distinta de `stock.quant`, de `sv_available_m3` y de la merma documental (no automática). La ampliación del ledger rige **desde I3**. |
| **C-3** (CR-19-08) | §5.1/§7 usaban `picking_id` como **idempotencia** y no distinguían **severidad** etiqueta-side de SV-side; `AL-01..AL-07` quedaban ambiguos. | **Prevalencia AD-91 (D-I2-16/17):** **idempotencia por clave documental propia** (no `picking_id`; el reintento no duplica cabecera/líneas/auditorías/consumo); **duro** etiqueta-side (Σ imputaciones ≤ volumen nominal editable, rechazo) y **blando** SV-side (advertir + motivo + `deviation`, permitir aplicar); **sin tolerancias ni `AL-01..AL-07` en I2**. |

### 13.3 Contradicciones/deudas abiertas (sin decidir)

- **Costo del SV** (fuente exacta) — Q-19-2.
- **Valor de `action_type`** (`imputacion` vs. reutilizar `rebaja`) — Q-19-1.
- **Tolerancias** de desviación de volumen/costo — Q-19-4.
- **Retorno a granel sin etiquetas** — Q-19-3.
- **Rol que reversa** y ventana de reversa — Q-19-5.

---

## 14. Clasificación de bloqueos de la rama de rebaja (D8)

> Entrega 4. Clasifica los **bloqueos vigentes** de la rama `feat/rebaja-contenedor-20261001` y define, bajo el principio «advertir, motivar, auditar» (D8), **cuáles pasan a advertencia con motivo** y cuáles **permanecen duros** (permisos por rol, integridad técnica, reglas financieras).

| # | Bloqueo (vigente) | Dónde | Clasificación propuesta | Fundamento |
|---|---|---|---|---|
| B-01 | **Zarpe** con contenedores sin rebaja física | `lumber.export.shipment.action_set_in_transit` (`18` §14.1) | **B-01 bloqueante (AD-94)** | Excepción documental **trazable**: exige **motivo**, abre **B-01 `open`**, **bloquea la Entrega** hasta regularización posterior, **no descuenta stock** ni equivale a Rebaja. R1/R4 son posteriores. |
| B-02 | **Rebaja sin disponible** (intentar descontar más que el quant) | salida nativa (`stock.move`) | **Duro (integridad técnica)** | Odoo prohíbe quant negativo. Se acompaña de mensaje profesional que indica ajustar volumen/nominal o dejar la etiqueta sin rebajar. El **exceso nominal** sobre el saldo SV (antes del quant) es **advertencia + motivo** (§7.2). |
| B-03 | **Reversa con embarque entregado** (o viaje cancelado) | `_rev...` / `action_reverse` (`18` §4.5, §14.1) | **Duro** por defecto; **override de Gerencia con motivo** como opción a decidir | Toca **historia** y potencial **período cerrado** (regla financiera dura). Se propone mantenerlo duro y habilitar excepción solo por Gerencia, con motivo y auditoría. **Pregunta abierta** Q-19-5. |
| B-04 | **Saldo SV** (Σ rebajas/imputaciones > saldo) | ledger + invariantes (`18` §5.2, `17` §3) | **Advertencia con motivo** (contable), **duro** en el techo del quant | Cumple D8: se advierte la desviación, se exige motivo y se audita. El límite físico (quant) sigue duro. |
| B-05 | **Rol insuficiente** para consolidar/rebajar/rebajar por nave/reversar | `_rebaja_require_group` (`18` §8) | **Duro** | Permisos por rol son duros (D8). |
| B-06 | **Viaje cerrado** (`shipping.voyage.state ∈ departed/arrived/cancel`) | `shipping_voyage.py`, `18` §4.5 | **Duro** | Regla financiera/período cerrado. |
| B-07 | **Costos distribuidos** impiden rolleo | `lumber_container_rollover_wizard.py:149-162` | **Duro** (con ruta: revertir costos primero) | Integridad financiera. |
| B-08 | **Duplicado de lote** en dos contenedores activos (`_check_lot_duplication`) | `lumber.container` (`18` §14.4, H-N1) | **Duro** (técnico) | Evita doble imputación de un mismo lote. **Pregunta abierta** H-N1 (¿el negocio requiere un lote en varios contenedores?). |

**Síntesis:** **B-01 (zarpe)** pasa a **B-01 bloqueante (AD-94)**; **B-04 (saldo SV)** a **advertencia con motivo**. Permanecen **duros**: **B-02, B-05, B-06, B-07, B-08**. **B-03** queda duro con **override de Gerencia**. Todos los casos con motivo se registran en `madenat.audit.log` (snapshot + firma) y en `deviation_flags`.

**Estado de implementación — bloque I0 (2026-10-01, rama `feat/imputacion-sv-i1-20261001`):**
- **B-01 — ✅ IMPLEMENTADO (AD-94):** el zarpe **no descuenta stock**; con contenedores pendientes exige excepción **B-01 bloqueante** `open` (motivo + auditoría SHA-256) que **bloquea la Entrega** hasta R1/R4 (posteriores).
- **B-03 / B-06 — ✅ IMPLEMENTADO:** la reversa con embarque entregado o viaje cancelado exige **override de Gerencia con motivo** (`lumber.container.action_reverse_rebaja` + `lumber.container.rebaja.reverse.wizard`).
- **B-02 (integridad), B-05 (permisos), B-07 (costos), B-08 (duplicado) — permanecen DUROS.**
- **B-04 (saldo SV) — ⏳ NO implementado** (va en I3; fuera del alcance de I0/I1 por instrucción).
- **Helper común AD-88:** `madenat.deviation.mixin._guard_deviation(code, message, reason, hard)` con snapshot + SHA-256.

**Estado de implementación — bloque 4A (2026-10-05, R1/R4):**
- **B-01 → R1 → R4 → Entrega (AD-95/AD-96):** la excepción **B-01 `open`** se resuelve en **dos acciones separadas** de Gerencia. **R1** = **rebaja extemporánea** por el motor nativo (no retrofecha Zarpe; no cierra B-01; no toca Costeo/Finanzas). **R4** = **cierre administrativo** `open → resolved` (exige cero pendientes + evidencia R1; no mueve stock; libera **sólo** el gate B-01 de la Entrega).
- **R1 ≠ R2:** R1 es rebaja extemporánea; R2 es **retorno físico total** de la reversa. **R4 ≠ Entrega:** R4 sólo habilita; la Entrega conserva sus demás gates y el Backlog se preserva.
- **R2 (AD-97) — Retorno físico total (Gerencia):** devuelve los lotes de Clientes al interno de origen enlazando `origin_returned_move_id`/`return_id`. Interacción SV **limitada** a `sv_reverse_allocation` de la rebaja de asignación; **no** crea imputación, Costeo ni Pagos. B-01 `open` bloquea; R2 no reabre/cierra B-01.

---

## 15. Plan de pruebas T-01..T-12 [DISEÑO]

> **Alcance por fase (AD-91).** La aceptación de **I2** usa **T-01..T-03 y T-06**; los casos con **salida nativa/quant/ledger** (**T-04, T-05, T-07, T-11**) y la **merma** (**T-10**) pertenecen a **I3**/fases posteriores.

Ejecutable a nivel **RPC/HTTP** (Odoo 18 CE), con **aserciones de `stock.quant` y del ledger SV antes/después**. Cada clase declara su fase explícitamente (`@tagged('post_install', '-at_install', …)`, `INDICE_DOCUMENTACION.md` §9).

| ID | Escenario | Antes | Acción | Aserción (después) |
|---|---|---|---|---|
| T-01 | **Imputación simple** (1 etiqueta → 1 SV) | SV con saldo S; quant S | Imputar etiqueta nominal V ≤ S | quant del SV = S − V; ledger `imputacion` `applied`; costo escrito |
| T-02 | **Etiqueta → varios SV** | SV-A saldo a, SV-B saldo b | Imputar etiqueta nominal V = v1+v2 | cada SV baja su parte; Σ = V; sin doble descuento |
| T-03 | **Varias etiquetas → 1 SV** | SV saldo S | Imputar 2 etiquetas (Σ ≤ S) | saldo = S − Σ; una op. por afectación |
| T-04 | **Exceso sobre saldo SV** | SV saldo S | Imputar V > S | **advertencia + motivo**; quant nunca negativo; auditoría |
| T-05 | **Idempotencia** | aplicada | Reintentar aplicar | no se duplica el `stock.move`; reutiliza `picking_id` |
| T-06 | **Pendiente** | — | Dejar `pending` y validar guía | sin descuento; guía válida; alerta AL-01 |
| T-07 | **Reversa** | aplicada (quant S−V) | Reversar | retorno nativo reposiciona quant; op. SV `reversed` ligada; historia intacta |
| T-08 | **Costo / promedio ponderado** | 2 SV con costos distintos | Imputar | `cost_per_m3_usd` = promedio ponderado; `stock.lot.cost.line` `wood` cuadra |
| T-09 | **Saldo por procesador** | SV en `Procesadores/<X>` | Consultar reporte | Σ quant por procesador correcto; nominal/disponible |
| T-10 | **Merma documental** | SV enviado E; retorno imputado R < E | Registrar merma | evento documental; **sin** `stock.scrap`; costo residual visible; AL-06 |
| T-11 | **SV directo a procesador (v2)** | SV en `Procesadores/<X>` | Imputar | salida nativa desde la ubicación del procesador |
| T-12 | **Permisos** | usuario sin rol | Intentar aplicar/reversar | `AccessError` según §9 |

**Invariantes a aseverar en cada test (AD-84 ampliado):** `volumen_restante_m3 = Σ quant` interno; `sv_available_m3 = baseline − rebajas activas − imputaciones activas`; Σ (rebajas+imputaciones) ≤ oficial; causa única de descuento.

---

## 16. Backlog por fases I0..I6 (D10, Entregas 4–5)

> Fases **incrementales** del frente de imputación. Cada fase declara **dependencias**, **riesgos** y **criterios de aceptación**. El detalle se refleja en `05_BACKLOG.md`.
>
> **Numeración (decisión del usuario, 2026-10-01).** Manda la numeración de este §16. El **bloque I0** agrupa lo **ya hecho** en la rama `feat/imputacion-sv-i1-20261001` (endurecimiento de la rebaja + helper AD-88 + zarpe blando + reversa con override + SV oculto). **I1** es el bloque **canónico de cimientos** (ubicaciones de procesadores, saldo por procesador y marcado de procesadores) — ✅ **IMPLEMENTADO (2026-10-02)**, con el alcance ampliado de abajo. **I2** (consolidación/imputación documental, `madenat.sv.imputation`) **sigue pendiente** y **no se implementa todavía**; su definición queda **refinada por AD-90** (2026-10-02).

### I0 — Endurecimiento de rebaja y principio AD-88 — ✅ IMPLEMENTADO (2026-10-01)
- **Alcance:** endurecimiento de la rebaja (rolleo, correo, auditoría con snapshot + SHA-256, costing `skip` con razón); helper común AD-88 `madenat.deviation.mixin._guard_deviation(code, message, reason, hard)`; **B-01 zarpe** como advertencia con motivo; **B-03/B-06 reversa** con override de Gerencia y motivo; **D9 SV oculto** por defecto en el asistente de contenedores.
- **No incluye:** B-04 (saldo SV), imputación ni `action_type='imputacion'` (van en I2/I3).
- **Dependencias:** rama de rebaja `feat/rebaja-contenedor-20261001`.
- **Aceptación:** suites en verde; bloqueos reclasificados sin regresión.

### I1 — Cimientos: ubicaciones y saldo por procesador — ✅ IMPLEMENTADO (2026-10-02; **corrección D-I1-03/D-I1-04 ✅ IMPLEMENTADA el 2026-10-02**)
- **Alcance base:** `stock.location` `Procesadores` (**interna**) + hijas internas bajo demanda; reporte `madenat.processor.balance`; marcar procesadores (`res.partner.is_processor`).
- **Ampliaciones aprobadas (2026-10-01):**
  1. **Evento «Envío a procesador»:** asistente desde lotes que crea una **transferencia interna nativa** de la bodega a la ubicación del procesador, con `lot_id` por línea; cantidad **editable hacia abajo**, sin exceder el disponible real; **motivo** si se desvía (AD-88 `_guard_deviation`) y evento en `madenat.audit.log` (**tipo aditivo**).
  2. **Recepción directa en la ubicación del procesador:** verificar que SV, procesados y compras la aceptan; corregir solo lo imprescindible y documentar.
  3. **Contenedores con lotes en ubicaciones de procesador:** verificar y probar que el asistente de contenedores toma lotes ubicados en ubicaciones de procesador.
- **Dependencias:** AD-65 §1.5 (patrón patio); `is_processor` (ya existe en `madenat_lumber_reception_improvements`); helper AD-88 (I0).
- **Riesgos:** R-19-05 (mal uso de ubicación interna).
- **Aceptación:** T-09; ubicaciones creadas bajo demanda e **idempotentes** (sin duplicados); saldo cuadra con Σ quant; envío parcial y rechazo por exceso de disponible; recepción directa aceptada; lote en procesador asignado en contenedor; ACL para Operaciones/Jefatura/Gerencia **sin grupos nuevos**.

**Estado de implementación (2026-10-02, rama `feat/procesadores-ubicaciones-20261001`; commit `1b25a4c`):**
- **Ubicaciones:** `res.partner.processor_location_id` + `res.partner._get_or_create_processor_location()` (idempotente) crean `WH/Stock/Procesadores/<PROCESADOR>` (`usage='internal'`, inventario MADENAT) bajo demanda; `stock.location.processor_partner_id` como vínculo inverso; botón «Crear / actualizar ubicación en planta» en `res.partner`.
- **Saldo por procesador:** vista de **solo lectura** (`list` + `pivot`) **sobre `stock.quant`**, agrupable por procesador / producto / tipo de lote (`stock.quant.madenat_processor_id`, `stock.quant.madenat_lot_flow_type`); acción y **menú en Logística** («Saldo por Procesador»).
- **Evento «Envío a procesador»:** asistente `madenat.processor.shipment.wizard` que crea una **transferencia interna nativa** (`stock.picking` tipo interno) con `lot_id` por línea; cantidad **editable hacia abajo**. **Techo = disponibilidad LIBRE real** (físico − reservado por otros movimientos) con **rechazo duro** si se excede (D-I1-04). Evento **aditivo** `processor_shipment` en `madenat.audit.log` (snapshot + SHA-256) **siempre** e idempotente; **motivo/`deviation` solo si hay desviación real** frente a una referencia previa persistida — inexistente en I1 (D-I1-03).
- **Recepción directa:** verificada con albarán nativo `incoming` hacia `Procesadores/<X>` (SV/volumen). **Sin cambios de código**: el destino interno es aceptado; procesados y compras comparten el mismo mecanismo.
- **Contenedores:** verificado que `lumber.container.lot.wizard` toma lotes ubicados en `Procesadores/<X>` (el dominio de disponibilidad no filtra por ubicación).
- **ACL:** `madenat.processor.shipment.wizard` y `.line` para Operaciones / Jefatura / Gerencia; **sin grupos nuevos**.
- **Pruebas:** `madenat_lumber_logistics/tests/test_processor_locations.py` (9 casos) + `test_processor_shipment_ad89.py` (T1–T8: parcial sin motivo, máximo libre, reserva ajena, disponible libre, desviación real N/A, idempotencia, backorder nativo, permisos). Suite `madenat_lumber_logistics`: **61**, 0 fallas (post-corrección AD-89).

**Decisiones del usuario sobre I1 (D-I1-01..D-I1-04, 2026-10-02) — registradas en AD-89 (`04_DECISION_LOG.md`):**
- **D-I1-01 (sin `madenat.processor.balance`):** **no** se crea ahora un modelo de saldo persistente. `stock.quant` + las ubicaciones internas `Procesadores/<X>` son la **fuente física de verdad**. Un modelo persistente queda **diferido a BI/cierre** (si se requieren snapshots, conciliación físico-documental, rendimiento o KPI históricos).
- **D-I1-02 (saldo en dos niveles):** (a) **resumen físico agregado** desde `stock.quant` — *es lo implementado*; (b) **detalle por lote** que exponga **nominal, disponible, ubicación/procesador, tipo de lote, fecha de ingreso, antigüedad en procesador, guía, proveedor y OC** — **planificado para la fase posterior a la imputación SV→etiqueta** (no implementar aún).
- **D-I1-03 (envío parcial ≠ desviación):** el **motivo obligatorio** aplica **solo** si la cantidad ejecutada difiere de una **propuesta, planificación, reserva o cantidad previamente indicada**. Un **envío manual parcial sin propuesta previa es válido** y se audita como **operación normal**. **Nunca** se permite exceder la disponibilidad física. ✅ **CORREGIDO (2026-10-02, rama `feat/procesadores-guardas-20261002`):** el asistente **no** persiste ninguna referencia previa (`_get_deviation_reference` ⇒ `None`, sin propuesta artificial), por lo que el parcial manual **no exige motivo** ni genera `deviation`.
- **D-I1-04 (riesgo pre-producción):** validar la **disponibilidad física frente a reservas de otros pickings/backorders** antes de producción. ✅ **RESUELTO (2026-10-02):** el asistente distingue y muestra **físico / reservado por otros / libre** (`stock.quant.quantity`, `reserved_quantity` y `_get_available_quantity(..., strict=True)`), rechaza si **solicitado > libre** (mensaje con los cuatro valores) y **no cancela, libera ni reasigna** reservas ajenas. El **backorder** conserva la **semántica nativa** de Odoo (el asistente no forma backorder porque `quantity == demand`; un picking interno nativo con entrega parcial sí lo forma) — ver T7.

**Efecto sobre las desviaciones previas (2026-10-02):** D-I1-01 **resuelve** la desviación n.º 1 (se aprueba la vista sobre `stock.quant`, sin modelo SQL). D-I1-02 **reencuadra** la desviación n.º 2 (nominal/antigüedad) como **trabajo planificado**, no deuda. D-I1-03 **contradice** la desviación n.º 3, **corregida el 2026-10-02**. D-I1-04 añade un **riesgo, resuelto el 2026-10-02**.

**Corrección AD-89 (2026-10-02, rama `feat/procesadores-guardas-20261002`):** `madenat.processor.shipment.wizard` calcula **físico / reservado por otros / libre** con APIs nativas de `stock.quant` y comparación consciente del redondeo UoM; el **libre** es el techo del envío; la **desviación** (motivo + **un único** evento `deviation`) se reserva a una diferencia frente a una **referencia previa persistida** (inexistente en I1). Auditoría `processor_shipment` **idempotente** (campo `picking_id`; reintentar no duplica picking/movimientos/auditoría). Comportamiento de **backorder** reproducido y documentado (T7).

### I2 — Consolidación / imputación documental (etiquetas procesadas → SV) — ⏳ PENDIENTE
- **Alcance cerrado (AD-91, D-I2-11..D-I2-19):** modelo **documental aditivo** `madenat.sv.imputation` (+`.line`, +`.sv.line`) en **`madenat_lumber_logistics`**; **cabecera por guía de procesados** (`guia_processing_id`), **una** imputación de trabajo `draft`/`pending` por guía; reparto **N:M** etiqueta↔SV con **volumen nominal editable**; estados `draft/pending/applied/reversed/cancelled`; motivo/`deviation_flags`; **idempotencia por clave documental propia** (no `picking_id`); **inmutabilidad** de `applied` (reversa + nueva). **Sin** efecto en `stock.quant`/`stock.picking`/`stock.move`; **sin** ledger `imputacion` ni cambio a `sv_available_m3`; **sin** costo; **sin** merma automática; **sin** genealogía.
- **Integridad (D-I2-16):** **duro** etiqueta-side (Σ imputaciones activas/aplicadas no revertidas ≤ volumen nominal editable, rechazo); **blando** SV-side (saldo documental superado ⇒ advertencia + motivo + `deviation`, permite aplicar). **Sin tolerancias ni `AL-01..AL-07` en I2.**
- **Saldos (D-I2-13):** el **saldo documental de consolidación** se computa solo desde imputaciones activas/aplicadas no revertidas del modelo nuevo, **distinto** de `stock.quant` (físico) y de `sv_available_m3` (ledger).
- **Dependencias:** I1 (procesador, `processor_location_id`, ubicación interna, saldo físico); `madenat.guia.processing` y `stock.lot` (**sin moverlos de core**); semántica **AD-90** (§2, §3, §5.4, §7.3). **No** depende del ledger.
- **Riesgos:** R-19-04; complejidad de la relación N:M; confundir las tres fuentes de saldo (físico / `sv_available_m3` / documental).
- **Aceptación:** T-01..T-03, T-06; CRUD con seguridad por rol; **sin efectos en stock**; **cuatro categorías de saldo** distinguibles (físico / documental pendiente / procesados pendientes de imputar / procesados ya imputados) más el **saldo documental** computado; válidos los **dos órdenes temporales** (etiquetas→consolidación y consolidación→etiquetas) sin bloqueo; **dura** etiqueta-side verificada; **blanda** SV-side con motivo + `deviation`; **idempotencia** por clave documental propia; **inmutabilidad/reversa** de `applied`.
- **Estado:** **PENDIENTE** (no implementado). **AD-90/AD-91 no lo declaran implementado.**

### I3 — Salida nativa del SV + ledger `imputacion` + invariantes
> **Único punto de salida nativa del SV (AD-91):** el efecto físico (ledger `action_type='imputacion'` + `stock.quant`) se materializa **aquí**, no en I2.
- **Alcance:** valor `action_type='imputacion'`; vínculo `imputation_id`; `stock.move` hacia `Virtual Locations/Production`; idempotencia `picking_id`; invariantes §7.3.
- **Dependencias:** I2; AD-82/AD-84; patrón `_get_or_create_consumption_picking`.
- **Riesgos:** R-19-01/R-19-02 (doble descuento / desalineación).
- **Aceptación:** T-01..T-05, T-07, T-11; invariantes en verde; sin regresión en `madenat_lumber_core`/`_logistics`.

### I4 — UX: asistente de imputación + propuesta automática
- **Alcance:** asistente al recibir la guía de procesados; propuesta por proveedor/producto/antigüedad; ocultar SV por defecto en el asistente de contenedores (D9); motivo obligatorio ante desviación.
- **Dependencias:** I2/I3; Consola/Guía (AD-80).
- **Riesgos:** UX sobre carga; falsos positivos de la propuesta.
- **Aceptación:** T-06; el operador puede confirmar/ajustar/dejar pendiente; SV ocultos por defecto pero seleccionables.

### I5 — Costo
- **Alcance:** costo por m3 editable; promedio ponderado de SV; `stock.lot.cost.line` (`wood`); **fuente del costo del SV** (brecha §5.5).
- **Dependencias:** I3; `madenat_lumber_costing`/`08_COSTEO.md`.
- **Riesgos:** R-19-03 (SV sin costo); doble conteo (N-02).
- **Aceptación:** T-08; costo cuadra salvo merma; sin efecto en valorización nativa (diferida).

### I6 — `parent_lot_id` opcional + auditoría/alertas + cierre de bloqueos
- **Alcance:** `parent_lot_id` opcional (paso controlado, D10); alertas §8; clasificación de bloqueos §14 (zarpe/saldo SV → advertencia con motivo).
- **Dependencias:** I1..I5; `madenat_toll_processing`; AD-86 (o su no-extracción).
- **Riesgos:** consumidores de genealogía; permisos.
- **Aceptación:** T-10, T-12; alertas operativas; bloqueos reclasificados sin regresión.

**Orden:** I1 → I2 → I3 → I4/I5 (paralelizables tras I3) → I6.

---

## 17. Preguntas abiertas (sin decidir por el usuario)

| ID | Pregunta | Opciones (no decididas) |
|---|---|---|
| Q-19-1 | **Valor de `action_type` del ledger** | ✅ **RESUELTA (2026-10-01):** se usa un **valor nuevo** `'imputacion'` (aditivo al Selection). |
| Q-19-2 | **Fuente del costo del SV** | ✅ **RESUELTA (2026-10-01):** el costo del SV se toma del **precio de la OC por m³**, **editable**; se **alerta** si falta. |
| Q-19-3 | **Retorno a granel sin etiquetas** | ⏳ Abierta: ¿cómo se imputa un retorno sin detalle de etiquetas (por volumen agregado)? |
| Q-19-4 | **Tolerancias** de desviación | ⏳ Abierta: ¿umbral de volumen (m³/%) y de costo para disparar advertencia? |
| Q-19-5 | **Reversa y rol** (B-03/B-06) | ✅ **RESUELTA (2026-10-01):** **override de Gerencia con motivo y auditoría** (implementado en el bloque I0). |
| Q-19-6 | **Umbrales de alerta** | ⏳ Abierta: ¿días para AL-01 (pendiente) y AL-03 (SV sin retorno)? |
| Q-19-7 | **`parent_lot_id` opcional (I6)** | ⏳ Abierta: ¿se mantiene `required` hasta I6? ¿Aplica a C2? |
| Q-19-8 | **H-N1** (lote en dos contenedores) | ✅ **RESUELTA (2026-10-01):** se **mantiene** `_check_lot_duplication` (un lote no puede estar en dos contenedores activos). |

> **Resueltas en la rama `feat/imputacion-sv-i1-20261001`:** Q-19-1 (valor `imputacion`), Q-19-2 (costo = precio de la OC por m³, editable, alerta si falta), Q-19-5 (override de Gerencia con motivo), Q-19-8 (se mantiene `_check_lot_duplication`). Las restantes (Q-19-3, Q-19-4, Q-19-6, Q-19-7) **siguen abiertas**.

---

## 18. Mantenimiento y evidencia

- **Alcance de esta versión:** documental. **No** se modificó código, datos ni parámetros; **no** hubo push.
- **Renumeración de fases (2026-10-01, Fase A):** manda la numeración de §16. El trabajo **ya hecho** en `feat/imputacion-sv-i1-20261001` (endurecimiento de rebaja + AD-88 + zarpe/reversa + SV oculto) se registra como **bloque I0**; **I1** queda **PENDIENTE** como bloque canónico de cimientos, con **alcance ampliado** (envío a procesador, recepción directa, contenedores con lotes en procesador); **I2** sin cambios. Ver §14 y §17 (Q-19-5).
- **I1 canónico implementado (2026-10-02, Fase B):** rama `feat/procesadores-ubicaciones-20261001` (commit `1b25a4c`). Ubicaciones `Procesadores/<X>` idempotentes desde `res.partner`; saldo por procesador (vista de solo lectura sobre `stock.quant`, menú Logística); evento «Envío a procesador» (transferencia interna nativa + AD-88 + tipo aditivo `processor_shipment`); ACL Operaciones/Jefatura/Gerencia sin grupos nuevos. Suite `madenat_lumber_logistics`: **51** (40 baseline + 11 nuevos), 0 fallas. Desviaciones/dudas en §16.
- **Decisiones D-I1-01..D-I1-04 (2026-10-02, AD-89) — solo documentación, sin cambios de código:** (01) **sin** modelo persistente `madenat.processor.balance` (diferido a BI/cierre; fuente física = `stock.quant` + ubicaciones internas); (02) saldo en **dos niveles** — resumen agregado *implementado* y **detalle por lote planificado** para después de la imputación SV→etiqueta; (03) **envío parcial ≠ desviación** (motivo solo ante diferencia con propuesta/planificación/reserva; **corrección del código pendiente**); (04) **riesgo pre-producción**: validar disponibilidad frente a reservas/backorders. Ver §16 y AD-89.
- **Decisión AD-90 / D-I1-05 (2026-10-02) — solo documentación, sin cambios de código:** semántica de inventario en procesador — `Procesadores/<X>` es **inventario MADENAT bajo custodia operativa** (no consignación); un **SV** allí está **pendiente de consolidación documental**; **recepción directa** y **transferencia interna** son **rutas físicas equivalentes**; el **envío** no es venta/exportación/rebaja/consumo/merma/genealogía; se distinguen **cuatro categorías de saldo** (§7.3) y **dos órdenes temporales** válidos; **I1 sin cambio de alcance** y **I2 sigue PENDIENTE**. Ver §2, §3, §5.4, §7.3, §16 y AD-90.
- **Efecto en otros documentos (ejecutado en la misma sesión documental):** alta de `19` en `INDICE_DOCUMENTACION.md`; alta de **AD-87** y **AD-88** y ajuste de **AD-83** (reemplazada) + **AD-82/AD-84** (alineadas) en `04_DECISION_LOG.md`; reescritura de secciones afectadas de `12`, `13`, `17` §2.8 y `18` (§7–§14); actualización de `05_BACKLOG.md`.
- **Registro de contradicciones:** §13.2 (resueltas) y §13.3 (abiertas). No se elige versión en silencio.
- **Nomenclatura:** español, con términos técnicos en inglés entre paréntesis.

**Evidencia (verificación de código, solo lectura):**
- `madenat_lumber_core/models/madenat_sv_operation.py` (`action_type` `94-104`; estados `105-116`; rebaja `146-148`; reversa ligada `172-178`; whitelist/transiciones `209-226`; constraint flujo Volumen `246-253`).
- `madenat_lumber_core/models/stock_lot.py` (`lot_flow_type` `358-366`).
- `madenat_lumber_core/models/stock_lot_cost_line.py` (`cost_type` `34-50`).
- `madenat_lumber_logistics/models/lumber_export_shipment.py` (`destination_shipment_id`/`destination_container_id` `945-958`).
- `madenat_lumber_reception_improvements/models/res_partner.py` (`is_processor` `22-31`).
- Documentos: `17_CONSTITUCION_VOLUMENES.md` §1/§2.8/§3; `18_CONSOLIDACION_Y_REBAJA.md` §1.3/§4/§5/§14; `12_FLUJOS_INGESTA.md` §11; `13_CONSOLIDACION_OPERATIVA.md` §4; `08_COSTEO.md` §1.4; `04_DECISION_LOG.md` (AD-64/AD-65/AD-82..AD-84).

<!-- creado: 2026-10-01 — CANON/19 Imputación SV (etiqueta→SV) y saldo por procesador. Decisiones D1–D10 del usuario. Especificación, sin cambios de código/datos/parámetros. -->
<!-- actualizado: 2026-10-01 (2, Fase A) — numeración §16 (manda la de CANON/19): trabajo hecho = bloque I0; I1 canónico pendiente con alcance ampliado (envío a procesador, recepción directa, contenedores con lotes en procesador); I2 sin cambios. §14/§17 alineados. -->
<!-- actualizado: 2026-10-02 (4) — AD-90: semántica de inventario en procesador (custodia operativa MADENAT, pendiente de consolidación documental); recepción directa y transferencia interna equivalentes; dos órdenes temporales válidos; cuatro categorías de saldo; I2 refinado a consolidación/imputación documental y sigue PENDIENTE. Complementa AD-87/88/89. Solo documentación. -->
<!-- actualizado: 2026-10-02 (6) — precisa el nombre del campo de clave documental de I2: `documentary_key` (implementado en madenat_lumber_logistics, AD-91). Solo documentación. -->
<!-- actualizado: 2026-10-02 (7) — precisa la semántica de estados de I2: reserva documental temporal de capacidad nominal de etiqueta (I2_ACTIVE_STATES: draft/pending/applied, techo duro) y saldo documental aplicado de SV (I2_DOCUMENTAL_STATES: applied); pending mantiene la reserva temporal; draft/pending sin efecto en stock/ledger/sv_available_m3. Ver §6/§7.3. Sin cambio funcional. Solo documentación. -->

---

### 19.9 Estado de I2 y reglas de identificación de retorno (2026-10-07)

> **Corrección de estado («I2 pendiente»).** El **modelo documental de I2 está IMPLEMENTADO en el
> árbol de código** (commit `2888745`, 2026-10-02), con suites acreditadas. Las menciones previas
> «I2 sigue PENDIENTE» de las versiones anteriores del documento describían la **fase de diseño**;
> a la fecha debe leerse así:
> - **Código presente (I2):** `madenat.sv.imputation` / `.line` / `.sv.line`, asistente, vistas,
>   ACL, secuencia y pruebas (`tests/test_sv_imputation_i2.py` — 13; `tests/test_sv_imputation_candidates.py`
>   — 12) en `madenat_lumber_logistics`.
> - **I3/I5 NO implementados:** salida nativa + ledger `action_type='imputacion'` (I3) y costo (I5)
>   continúan **fuera de alcance**. I2 es **documental**: sin efecto en `stock.quant`, ledger ni
>   `sv_available_m3` (D-I2-12).
> - **Aplicación al entorno activo:** decisión operativa **separada** (no implícita en el código
>   presente).

**Reglas de identificación incorporadas (2026-10-07; copia aislada, AD-102).** No alteran los
efectos de I2.
- **Destino marcado «Sí» al aplicar.** `action_apply` exige que la guía destino
  (`guia_processing_id`) esté marcada como retorno de servicio (`service_return_confirmation ==
  'yes'`). Se comprueba **al aplicar** (no al guardar borrador/pendiente) y **no** marca la guía
  automáticamente. `action_pending` no lo exige.
- **Relación inversa `sv_imputation_ids`** en `madenat.guia.processing` (One2many de **solo
  lectura** → `madenat.sv.imputation.guia_processing_id`), en `madenat_lumber_logistics` (donde
  existe el modelo I2): respeta la dependencia **core ← logistics** y **no** introduce dependencia
  **core→logistics** ni circular.
- **Filtro «Retornos sin imputación aplicada»** (Logística): retorno confirmado `yes` **sin**
  ninguna imputación `applied` (borrador/pendiente/anulada/reversada no cuentan — D-I2-13). **NO**
  evalúa **cobertura parcial** (limitación declarada).
- **Inmutabilidad/reversa intactas** (§6): con imputaciones `applied`, cambiar la identificación de
  la guía a «No» o vaciarla se **rechaza**; se exige reversar primero.

---

### 19.10 Flujo operativo de imputación SV confirmado en código (2026-10-10)

> **Naturaleza.** Confirmación **de solo lectura** del flujo **implementado** (I2, AD-91; reglas de
> identificación AD-102) en el árbol activo. **No** se aplicaron ni reversaron imputaciones reales;
> **no** se crearon movimientos de stock. Rige lo ya establecido: I2 es **documental** (sin efecto en
> `stock.quant`, `stock.picking`, `stock.move`, ledger `madenat.sv.operation` ni `sv_available_m3`).
> **I3** (salida nativa + ledger `action_type='imputacion'`) e **I5** (costo) **siguen fuera de alcance**.

**Secuencia operativa (ruta real del código).** El **envío a proceso** y la **imputación** son dos
actos **separados**: el envío (I1) es una transferencia interna; la imputación (I2) es el vínculo
documental del retorno. **No** existe vínculo automático entre ambos.

| # | Paso | Menú / botón | Modelo / acción | Dato necesario | Validación | Resultado esperado |
|---|---|---|---|---|---|---|
| 1 | Identificar el **envío a proceso** | Logística → **Envío a Procesador** | `madenat.processor.shipment.wizard.action_send` | Procesador (`is_processor`), origen interno, lotes y cantidad | Cantidad > 0 y ≤ **libre** (físico − reservado ajeno) del lote en el origen (AD-89) | Transferencia interna nativa al `Procesadores/<X>` (la madera sigue siendo de MADENAT) + auditoría `processor_shipment` (SHA-256) |
| 2 | Consultar **volumen y saldo** en poder del procesador | Logística → **Saldo por Procesador** | `stock.quant` (lista/pivot por `madenat_processor_id`) | Procesador / producto / lote | — | Saldo físico en poder del procesador (**solo lectura**) |
| 3 | **Ingresar la guía de retorno** | Ingreso de Madera (Consola) o Guía Procesados | `madenat.lumber.intake.console` / `madenat.guia.processing` | Documento de guía/packing | Clasificación por contenido (servicio → Procesado) | Guía con sus **etiquetas procesadas** (`stock.lot`, `lot_flow_type != 'volume'`) |
| 4 | **Marcar «¿Es retorno de servicio?»** | Formulario de guía / Consola (`widget="radio"`) | campo `service_return_confirmation` (`yes`/`no`/vacío) | Decisión del operador | **No bloqueante**; vacío ≠ `no` (AD-102) | Campo persistido; **no** dispara la imputación |
| 5 | **Abrir el asistente** de imputación | Guía → botón **«Imputación documental SV»**; o Logística → **Imputaciones documentales SV** | acción `action_madenat_sv_imputation_wizard` → `madenat.sv.imputation.wizard` | Guía destino | — | Asistente con las etiquetas de la guía y la propuesta **FIFO editable** |
| 6 | **Seleccionar origen y destino** | Asistente: pestañas «Etiquetas» (retorno) y «Reparto SV» | `wizard.line_ids` (etiquetas) y `wizard.sv_line_ids` (SV) | Etiqueta procesada (origen) y etiqueta **SV** (destino) | SV candidatos = `lot_flow_type='volume'`, saldo documental > 0 (y quant interno en la ubicación del procesador si hay procesador) | Reparto editable; **«Proponer FIFO»** lo autocompleta |
| 7 | **Completar volumen y campos** | Asistente: `nominal_volume_m3` (etiqueta) e `imputed_volume_m3` (SV) | `madenat.sv.imputation.wizard` | Volumen nominal (m³) e imputado (m³); `reason` si hay desviación | **Techo DURO** etiqueta: Σ activos ≤ nominal editable; exceso SV-side = **blando** (motivo) | Documento en borrador |
| 8 | **Guardar y revisar** | **«Guardar borrador»** / **«Dejar pendiente»** | `action_prepare` / `action_pending` → `madenat.sv.imputation` | — | Una sola imputación de trabajo por guía (draft/pending) | Cabecera + líneas (idempotente por `documentary_key`) |
| 9 | **Aplicar** | **«Aplicar»** | `madenat.sv.imputation.action_apply` | Guía destino marcada **«Sí»** | Permiso Operaciones/Jefatura/Gerencia; destino = retorno; payload válido; techo duro; advisory lock por SV | Estado `applied` + `executed_by_id`/`execution_date` + snapshot/SHA-256; auditoría `imputation` |
| 10 | **Consultar resultado y saldo** | Lista/formulario de imputación; saldos en el asistente | `nominal_total_m3`, `imputed_total_m3`, `etiqueta_saldo_documental_m3`, `sv_saldo_documental_m3` | — | — | Saldo **documental** actualizado (magnitud propia; **no** cambia stock ni `sv_available_m3`) |
| 11 | **Reversar** para corregir | **«Reversar»** | `madenat.sv.imputation.action_reverse` | `reversal_reason` | Solo Jefatura/Gerencia; solo estado `applied` | Estado `reversed`; historia **append-only** conservada; auditoría `imputation_reverse` |

**Tabla de controles.**

| Dimensión | Regla vigente (código) |
|---|---|
| **Origen** | Etiqueta **procesada** (`stock.lot`, `lot_flow_type != 'volume'`) de la guía destino. El **volumen enviado a proceso** vive en el envío I1 (`madenat.processor.shipment.wizard` → transferencia interna); **no** hay vínculo automático envío↔imputación. |
| **Destino** | Guía de procesados (`madenat.guia.processing`) que debe estar `service_return_confirmation == 'yes'`; se exige **al aplicar**, no al guardar. No se marca la guía automáticamente. |
| **Volumen** | `imputed_volume_m3` (m³) por reparto, **editable**; `nominal_volume_m3` de la etiqueta (por defecto el de compra). Admite **varios SV** por etiqueta (N:M). |
| **Saldo** | Etiqueta: techo **duro** Σ activos ≤ nominal editable (**rechaza**). SV: exceso sobre el saldo documental = **blando** (motivo + `SV_EXCESS`). Saldo documental I2 = nominal − imputado **aplicado no revertido**; **no** es `sv_available_m3` ni el físico. |
| **Aplicación** | `action_apply`: permiso + destino «Sí» + payload + techo duro + desviaciones blandas + advisory lock + snapshot/auditoría. **Documental** (sin movimientos de stock). **Idempotente**. |
| **Reversa** | `action_reverse`: solo `applied`; **Jefatura/Gerencia**; conserva historia (`reversed`, `origin_imputation_id`/`reversed_imputation_id`). Con `applied`, cambiar la identificación de la guía a «No»/vacío se **rechaza**. |
| **Permisos** | Aplicar: **Operaciones/Jefatura/Gerencia**. Reversar: **Jefatura/Gerencia**. Trazabilidad: `madenat.audit.log` (tipos aditivos `imputation`, `imputation_reverse`) + chatter (`mail.thread`). |

**Ejemplo numérico ilustrativo (NO es una operación real).** Retorno de una guía con una etiqueta procesada
de nominal **5,000 m³**; dos SV candidatos con saldo documental **3,000** y **4,000**. Reparto FIFO:
**3,000** al primer SV + **2,000** al segundo (Σ = **5,000** = nominal, sin exceso). Al aplicar, el saldo
documental del primer SV pasa a **0,000** y el del segundo a **2,000**; la etiqueta queda con saldo
**0,000**. Es un ejemplo: **no** se ejecutó sobre ninguna base.

**Rendimiento y merma — no implementados en I2.** No hay cálculo de rendimiento (enviado vs. retornado),
ni merma automática, ni costo (I5), ni cierre. La imputación es un **vínculo documental por volumen**;
**no** compara magnitudes equivalentes (p. ej. volumen de compra vs. de embarque). Ver §13 y
`05_BACKLOG.md`.

**Brechas declaradas (sin implementar en esta etapa).** (a) **vínculo automático envío↔imputación**;
(b) **cobertura parcial** del filtro «Retornos sin imputación aplicada»; (c) **rendimiento/merma**
(comparación de magnitudes equivalentes); (d) **I3** (salida nativa + ledger) e **I5** (costo);
(e) **concurrencia**: existe *advisory lock* por SV, pero la acreditación de concurrencia sigue pendiente.

### 19.11 Relación de conciliación envío–retorno (Bloque A/B/C, 2026-10-10)

> **Naturaleza.** Implementación **acotada y DOCUMENTAL** que cierra la brecha **(a)** declarada en
> §19.10 («vínculo automático envío↔imputación»). **No** sustituye la imputación documental SV (C),
> **no** crea ni modifica `stock.quant`/`stock.move`/`picking` ni el ledger `madenat.sv.operation`, y
> **no** implementa la conciliación **cuantitativa** (Bloque D, **pendiente**).

**Qué resuelve.** Operaciones puede declarar **qué envío a procesador atiende cada retorno** y
consultar el vínculo, sus referencias y su estado, manteniendo separadas las cuatro capas:

| Capa | Nombre operativo | Registro persistente | Dueño |
|---|---|---|---|
| A | **Envío a procesador** (material enviado) | transferencia interna `stock.picking` con destino `Procesadores/<X>` (`location_dest_id.processor_partner_id`) + `madenat.audit.log('processor_shipment')` | `madenat_lumber_logistics` (I1) |
| B | **Guía de retorno / etiqueta procesada** | `madenat.guia.processing` + etiquetas `stock.lot` (`lot_flow_type != 'volume'`) | `madenat_lumber_core` |
| C | **Imputación documental SV** (etiqueta SV imputada) | `madenat.sv.imputation` (+ `.line` / `.sv.line`) | `madenat_lumber_logistics` (I2) |
| D | **Relación de conciliación** | **`madenat.processor.return.link`** (nuevo) | `madenat_lumber_logistics` (esta etapa) |

> **El asistente de envío es transitorio.** `madenat.processor.shipment.wizard` **no** persiste un
> registro propio: su resultado persistente es el **`stock.picking`**. La relación de conciliación
> enlaza **el picking**, nunca el wizard (evita depender de un `TransientModel`).

**Modelo `madenat.processor.return.link`** (cabecera por par envío↔retorno).

| Campo | Tipo | Notas |
|---|---|---|
| `name` | Char (secuencia `madenat.processor.return.link`, prefijo `REL`) | Identificador |
| `picking_id` | M2O `stock.picking` (`ondelete='restrict'`) | **Envío a procesador** (A) |
| `guia_processing_id` | M2O `madenat.guia.processing` (`ondelete='restrict'`) | **Retorno** (B) |
| `imputation_id` | M2O `madenat.sv.imputation` (`ondelete='set null'`) | Imputación SV (C), opcional |
| `processor_id` | M2O `res.partner` (related store del destino del picking) | Procesador |
| `state` | Selection `draft`/`linked`/`reversed` | §Estados |
| `shipment_volume_m3` | Float, digits (16, 3) (compute) | Σ cantidades del envío (**magnitud física, separada**) |
| `return_nominal_m3` | Float, digits (16, 3) (compute) | Σ nominal de etiquetas del retorno (**magnitud documental, separada**) |
| `shipment_date` / `return_date` | Datetime / Date (related) | Referencias temporales |
| `reason` / `note` | Text | Observaciones |
| `linked_by_id` / `linked_date` | M2O `res.users` / Datetime | Autoría |
| `reversed_by_id` / `reversal_date` / `reversal_reason` | M2O / Datetime / Text | Reversa |
| `origin_link_id` / `reversed_link_id` | M2O self | Cadena **append-only** |
| `snapshot_json` / `audit_hash` | Text / Char | Evidencia firmada (AD-79/AD-80) |


**Cardinalidades (reglas propuestas, §5/§19.11).** **N:M** — un envío admite **varios retornos
parciales**; un retorno admite **varios envíos**. Unicidad por par envío↔retorno en estados
**activos** (`draft`/`linked`); `reversed` libera el par. La selección se limita al **mismo
procesador** (salvo excepción definida fuera de este documento). Sólo se proponen **envíos
elegibles** (picking `done` con destino de procesador).

**Estados.** `draft` (**Propuesta**, sin registrar) → `linked` (**Conciliación registrada**) →
`reversed` (**Revertida**). «Conciliación registrada» declara **el vínculo**, **no** una igualdad
cuantitativa: no se declara «conciliado» sólo porque exista una imputación aplicada.

**Magnitudes (§6).** Se muestran **separadas** el volumen **enviado** (físico, Σ `move_line`) y el
nominal **retornado** (documental, Σ nominal de etiquetas). **No** se restan magnitudes no
equivalentes, **no** hay saldo de proceso, rendimiento ni merma (Bloque D; §7 y Q-19-3/Q-19-4).

**Reglas y controles.**
- **Envío elegible:** picking `done` con `location_dest_id.processor_partner_id`; dominio único y
  compartido por la propuesta y el asistente.
- **Procesador correspondiente:** rechazo si el procesador del envío ≠ procesador del retorno.
- **Retorno de servicio:** `action_link` exige la guía marcada `service_return_confirmation == 'yes'`.
- **Permisos por ORM/RPC (no sólo botones):** registrar = Operaciones/Jefatura/Gerencia; reversar =
  Jefatura/Gerencia; Auditoría = lectura. Grupos existentes (sin grupos nuevos).
- **Append-only:** `linked`/`reversed` no se editan ni eliminan; la corrección se hace por **reversa**
  con motivo + evidencia firmada. No se elimina una relación aplicada sin rastro.
- **Auditoría:** tipos aditivos `processor_return_link` y `processor_return_link_reverse`
  (`madenat.audit.log`, snapshot + SHA-256).
- **Idempotencia:** registrar dos veces no duplica ni la relación ni la auditoría.

**Experiencia de Operaciones (flujo corto, §7).** 1) Abrir la guía de retorno → 2) el asistente de
imputación (reutilizado, no duplicado) → 3) pestaña **«Envíos a procesador (retorno)»**: consultar
envíos elegibles del procesador y seleccionar → 4) completar etiquetas/SV y **Aplicar**. Al aplicar se
registran las relaciones (`draft` → `linked`). Toda propuesta es **visible y editable**; nada se aplica
en silencio. La selección queda en estado propuesto mientras no se aplique.

**Históricos.** No se crean asociaciones automáticas ni se infieren por volumen/fecha. Los envíos y
retornos existentes permanecen en estado **`no_return`** hasta que Operaciones declare la relación.
No se reescribe ni se recalcula ningún registro histórico.

**Límites declarados (acreditación 2026-10-10).** Se declaran **sin cierre** (detalle en `03_TESTS.md`
**§15.5**): (a) la **reversa de la imputación** **no** revierte ni marca el vínculo (este conserva su
estado) — efecto **pendiente de decisión**; (b) **no** hay restricción explícita de **consistencia de
compañía** entre envío y retorno; (c) las magnitudes **no** se reparten en N:M (`shipment_volume_m3` se
repite por vínculo ⇒ sumar vínculos **duplicaría** el volumen); el reparto es **Bloque D**. La
**exclusión de envíos cancelados** se garantiza por el dominio `state='done'` (sin caso de prueba
dedicado). Evidencia web: **integración web/RPC con sesión — ejecutada**; **lectura de arquitecturas de
vistas y metadatos — verificada**; **renderizado e interacción en navegador real — pendiente** (la
verificación web/RPC **no** sustituye al navegador real).

**Bloque D — pendiente (no implementado).** Conciliación cuantitativa (enviado vs retornado vs
imputado) sin magnitudes comunes aprobadas. No se calculan saldo de proceso, rendimiento ni merma.

**Dónde se ve.** Pestaña «Conciliación Envío–Retorno» en la **guía**; pestaña «Retornos (procesador)»
en el **picking**; pestaña «Envíos a procesador (retorno)» en la **imputación**; y menú de Logística
**«Conciliación Envío–Retorno»**.

**Pruebas.** `madenat_lumber_logistics/tests/test_processor_return_link.py` (**T1–T12**); resultados en
`03_TESTS.md` **§15** y evidencia en `CONCILIACION_ENVIO_RETORNO_20261010/`.

### 19.12 Bloque D — Conciliación cuantitativa: diseño requerido (**NO implementado**)

> **Decisión de etapa (2026-10-10) — opción 3.** Para esta etapa se mantiene: **no** se implementa el
> Bloque D. **No** hay conciliación cuantitativa, saldo de proceso, rendimiento, merma, cierre
> automático del envío ni tolerancias. El estado `linked` significa **«vínculo registrado»**, **no**
> «envío conciliado». La UI muestra **separados** el **volumen enviado**, el **volumen retornado** y el
> **imputado SV** (`shipment_volume_m3`, `return_nominal_m3`, imputación), sin restarlos.

El Bloque D es una **etapa independiente**. Su diseño deberá establecer, como mínimo:

1. **Qué volumen representa cada campo.** Para cada magnitud: campo fuente, unidad, fórmula,
   precisión y significado funcional — volumen enviado (`stock.move.line.quantity`), volumen retornado
   (Σ nominal de etiquetas procesadas; ¿bruto con tarja o neto?), volumen imputado SV
   (`madenat.sv.imputation.sv.line.imputed_volume_m3`), y volumen de compra/embarque
   (`17_CONSTITUCION_VOLUMENES.md`). **No** restar magnitudes **no equivalentes**.
2. **Asignación de cantidades con relaciones N:M.** Regla explícita, determinista y auditable para
   repartir/prorratear una cantidad cuando un envío tiene varios retornos y un retorno varios envíos;
   evitar el **doble conteo**.
3. **Identificación de retornos parciales.** Cómo se reconoce y representa un retorno parcial (por
   volumen, por lote/etiqueta o por declaración del operador) y cuándo un envío pasa a
   «parcialmente retornado».
4. **Clasificación de diferencias.** Qué diferencia corresponde a **transformación** (proceso),
   **merma** (pérdida real) o **datos** (error documental/captura). **Sin** factores inventados.
5. **Aceptación de diferencias y cierre.** Quién **acepta** una diferencia y **cierra** el proceso
   (rol), con motivo, evidencia y trazabilidad; y el efecto de reversas (imputación, retorno, envío).

**Habilitantes del Bloque D (preguntas abiertas):** magnitud común de comparación y tolerancia
(Q-19-4), retorno a granel sin etiquetas (Q-19-3). Hasta resolverlas, el sistema **no** calcula
conciliación cuantitativa ni cierra el envío.

### 19.13 Integridad del vínculo: reversa, compañía, elegibilidad y volúmenes N:M (2026-10-10)

> **Alcance.** Ajuste **mínimo** de los Bloques A/B/C. **No** implementa el Bloque **D** cuantitativo
> (sin conciliación cuantitativa, saldo de proceso, rendimiento, merma, reparto ni tolerancias).

**19.13.1 Procedencia vs. vigencia documental (no confundir).**
- `state` = **procedencia** (`draft`/`linked`/`reversed`): envío y retorno están (o no) relacionados.
- `documentary_status` (derivado, almacenado) = **vigencia documental** real de la imputación
  relacionada: `none` · `draft` (en preparación) · `applied` (vigente) · `reversed` (**revertida;
  requiere reimputación**) · `cancelled`. `requires_reimputation` ⇔ `documentary_status == 'reversed'`.
- **Reversar la imputación NO revierte la procedencia.** El vínculo permanece `linked`; su vigencia
  pasa a `reversed`. `linked` sigue significando **«vínculo registrado»** (no «conciliado»).

**19.13.2 Reimputación.**
- Al aplicar una **nueva** imputación sobre el mismo par, el vínculo **activo se reutiliza** (no se
  duplica), `imputation_id` pasa a la nueva y **`previous_imputation_id` conserva la anterior**.
- Deja **rastro** (chatter + evento de auditoría `processor_return_link` con «reimputación»). **No** se
  sobrescribe en silencio; la imputación anterior permanece (estado `reversed`) como historia.
- Unicidad por par en estados activos e idempotencia: intactas.
- **Dos reimputaciones sucesivas (A→B→C) — confirmado (2026-10-10):** `previous_imputation_id` apunta a
  la **inmediatamente anterior** (C.previous = B) y la **cadena completa** A→B→C queda trazada por los
  **eventos de auditoría append-only** (`processor_return_link` «reimputación X → Y», uno por paso);
  A/B permanecen `reversed`, C `applied`; **1 solo vínculo activo**. Evidencia:
  `CONCILIACION_ENVIO_RETORNO_20261010/v3/reimputation_chain_report.txt`. **No** se añade un modelo de
  historial multinivel: la auditoría ya lo registra (evita duplicar el modelo de auditoría).

**19.13.3 Consistencia de compañía.**
- Constraint `_check_company_consistency`: la compañía del **envío** (origen de `company_id`) y la de la
  **imputación** deben coincidir. `madenat.guia.processing` **no** tiene `company_id` (documento): no se
  compara; `res.partner` es compartido (no es conflicto por sí solo).
- **Regla de registro** (`ir.rule`) multi-compañía del vínculo (`company_id in company_ids` o `= False`).
  Las ACL por grupo **no** sustituyen reglas de registro.
- **Alcance preciso (2026-10-10):** `link.company_id` es `related` de `picking_id.company_id`, que a su
  vez es **`related` de `picking_type_id.company_id`** (la compañía del **tipo de operación** del envío;
  por eso el picking reporta `company_id` no requerido). `madenat.sv.imputation.company_id` es campo
  **propio y requerido**; `madenat.guia.processing` **no** tiene `company_id`. La regla incluye la rama
  **`company_id = False`** para registros **compartidos/neutros** (no se ocultan a todos); en esta base
  hay **0** pickings con compañía nula. Control por **modelo** (constraint) **y** regla de registro; no
  sólo dominio de UI.
- Control por **modelo/ORM/RPC**, no sólo dominio de UI.

**19.13.4 Elegibilidad del envío (control duro).**
- Sólo **`state='done'`** y **`picking_type_id.code='internal'`** con destino de procesador. Se valida en
  el **modelo** (`_check_shipment_is_processor_shipment`) además del dominio de elegibilidad ⇒ una
  **selección forzada por ORM/RPC** de un envío `draft`/`cancel`/`assigned` es **rechazada**.
- **No** se inventa control de saldo físico. Un envío con **devolución** conserva `state='done'` (Odoo
  crea un picking inverso); **no** se altera la elegibilidad por ello (**pendiente declarado**).

**19.13.5 Volúmenes referenciales N:M (presentación).**
- `shipment_volume_m3` y `return_nominal_m3` son **referenciales**: total del documento relacionado. Un
  mismo envío/retorno puede aparecer en **varios** vínculos ⇒ **sumar filas NO produce un total válido**.
- `aggregator=False` (sin `sum`/`avg`/pivot/`read_group`) + ayuda explícita; las vistas no usan
  sumatorios. **No** hay reparto/prorrateo, resta, rendimiento ni saldo (Bloque D).

<!-- actualizado: 2026-10-10 (5) — §19.13 ajuste de integridad A/B/C (reversa vs. procedencia,
reimputación, compañía + regla de registro, elegibilidad dura, volúmenes referenciales N:M).
Bloque D cuantitativo sigue fuera de alcance. Versión 1.9.0 → 1.10.0. -->

<!-- actualizado: 2026-10-10 (4) — §19.12 Bloque D (conciliación cuantitativa): diseño requerido y
decisión de etapa «opción 3» (no implementado; `linked` = vínculo registrado). §19.11 vuelto a
confirmar. V3 (proxy de navegador) de A/B/C ejecutada. Versión 1.9.0. -->
