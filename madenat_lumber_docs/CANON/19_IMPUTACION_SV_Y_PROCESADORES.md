# 19 — Imputación SV (etiqueta→SV) y Saldo por Procesador

**Proyecto:** MADENAT Lumber — Odoo 18 CE
**Versión documental:** 1.0.0
**Fecha de creación:** 2026-10-01
**Estado:** ✅ Vigente — Documento canónico de la **imputación declarada** entre la etiqueta de madera procesada y una o varias etiquetas SV (Lote Volumen), y del **saldo por procesador**. **No sustituye** a `00_ARQUITECTURA.md`, `04_DECISION_LOG.md`, `12_FLUJOS_INGESTA.md`, `13_CONSOLIDACION_OPERATIVA.md`, `17_CONSTITUCION_VOLUMENES.md` ni `18_CONSOLIDACION_Y_REBAJA.md`; los referencia y los alinea.
**Responsable revisión:** Arquitecto / Tech Lead — Alta del documento a solicitud del usuario (decisiones D1–D10 del 2026-10-01).
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
| **Imputación (declarada)** | Acto administrativo que **declara** qué etiqueta(s) de retorno corresponden a qué SV. **No es genealogía física**: es la relación **volumen nominal declarado** etiqueta→SV. Registra el ledger SV y **genera la salida nativa del quant del SV** (§4, §5). | propuesto: `madenat.sv.imputation` |
| **Procesador** | Planta externa (cepillado, secado, tratamiento, …) que transforma el SV. Se marca en el maestro de partners. | `res.partner.is_processor` |
| **En poder del procesador X** | **Ubicación interna** de stock por procesador (`stock.location`, `usage='internal'`) bajo un padre **`Procesadores`**. El inventario **sigue siendo de MADENAT** (no es consignación ni propiedad ajena). | `stock.location` |
| **Saldo por procesador** | Volumen SV (nominal/disponible) que **permanece** en la ubicación del procesador sin retorno imputado. | propuesto: `madenat.processor.balance` (vista/reporte) |
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
   │  · registra el ledger SV  (madenat.sv.operation, tipo `imputación`)
   │  · genera la SALIDA NATIVA del quant del SV (AD-82/AD-84)  ◄── único punto de salida del SV
   │  · escribe/actualiza el costo de la etiqueta (stock.lot.cost.line, cost_type='wood')
   │  · si hay merma, registra el evento documental de merma (§7, §11)
   ▼
ETIQUETA PROCESADA (stock nuevo e independiente, lot_flow_type='tarja'/vacío)
   └── sigue el flujo normal (ingesta / consolidación / exportación de `18`)
```

**Claves [DISEÑO]:**
- La imputación es **la vía única** por la que el volumen SV "sale" del stock (su quant se descuenta en el momento de imputar). No hay descuento del SV vía contenedor de exportación (el SV no se exporta).
- El **retorno es stock nuevo e independiente** (AD-65 §1.6; alineado con DEC-002). El vínculo con el SV es **declarado**, no físico (D2).

### 3.2 Compra de madera procesada (C2) — flujo normal

No hay SV ni imputación: la madera llega procesada con etiquetas/tarjas y se ingesta por los flujos vigentes (`12_FLUJOS_INGESTA.md` §3 y §4; `13_CONSOLIDACION_OPERATIVA.md` §3–§4). Aplica la genealogía `parent_lot_id` **solo cuando el usuario la declare** (opcional, §5.6, D10).

### 3.3 Variante de ubicación del SV

| Variante | Dónde vive el SV al comprarlo | Salida nativa al imputar |
|---|---|---|
| **v1 — Bodega** | Ubicación interna de patio MADENAT | Desde la ubicación vigente del SV (patio o `Procesadores/<X>` si ya se envió) a `Virtual Locations/Production` (o a la ubicación del procesador si aún no se movió). |
| **v2 — Directo a procesador** | `Procesadores/<X>` (nunca toca bodega) | Desde `Procesadores/<X>` a `Virtual Locations/Production`. |

Ambas variantes usan la **misma** imputación y el **mismo** ledger; solo cambia la ubicación de origen del `stock.move`.

---

## 4. Qué es (y qué no es) la imputación

### 4.1 Definición [DISEÑO]

La **imputación** es un registro administrativo que declara la correspondencia **de volumen** entre:
- **un conjunto de etiquetas de retorno** (madera procesada recibida), y
- **uno o varios SV** (etiquetas SV compradas).

**Unidad de captura:** la **etiqueta** (D3), con su **volumen NOMINAL editable**. La etiqueta se imputa contra **uno o varios SV**; un SV puede recibir imputaciones de **varias** etiquetas mientras tenga saldo.

### 4.2 La imputación NO es genealogía física (D2)

- No se crea vínculo lote-a-lote padre/hijo (`parent_lot_id`/`child_lot_ids`) por la imputación.
- El procesador externo **mezcla** físicamente el material: la correspondencia real es desconocida. La imputación es una **declaración profesional** con motivo y auditoría, consistente con `AD-65 §1.6`.
- El retorno es **stock nuevo e independiente** (alineado con DEC-002).

### 4.3 Efectos (D3)

1. **Ledger:** una o más operaciones en `madenat.sv.operation` con `action_type = 'imputacion'` (§5.3), motivo obligatorio y firma (política AD-79/AD-80).
2. **Salida nativa:** un `stock.move`/picking **outgoing** que descuenta la **cantidad imputada** del quant del SV, desde su ubicación vigente hacia `Virtual Locations/Production`. Es el **único** descuento del SV (AD-82/AD-84).
3. **Costo:** escribe la línea de costo de madera de la etiqueta (`stock.lot.cost.line`, `cost_type='wood'`) con el **costo promedio ponderado** de los SV elegidos (§5.5).

### 4.4 Relación con AD-82 / AD-83 / AD-84

| AD | Estado previo | Efecto de este documento |
|---|---|---|
| **AD-82** (salida única de stock al rebajar) | Aprobada e implementada (contenedores/naves) | **Se alinea:** AD-82 rige la **exportación de tarja**; el SV **no** se exporta; su salida única es la **imputación** (§3.1). |
| **AD-83** (módulo propio rebaja SV + descuento por procesados) | Aprobada **en principio** | **REEMPLAZADA por AD-87** (ver §13 y `04_DECISION_LOG.md`): el "descuento por procesados" se materializa como **imputación**; no se extrae módulo propio de rebaja SV; la asignación SV a contenedor de **exportación** deja de ser el caso de uso (el SV no se exporta). |
| **AD-84** (invariantes) | Aprobada e implementada (parcial) | **Se amplía:** el saldo SV resta **también** las imputaciones activas (§5.3, §7); la causa única de descuento del SV es la imputación. |

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
| `sv_operation_ids` | O2M `madenat.sv.operation` | — | Ledger generado (una op. `imputacion` por SV afectado) |
| `picking_id` | M2O `stock.picking` (`copy=False`) | — | **Idempotencia**: la salida nativa se ejecuta una sola vez |
| `executed_by_id` / `execution_date` | M2O `res.users` / Datetime | — | Autoría (política AD-79) |
| `snapshot_json` / `audit_hash` | Text / Char | — | Evidencia firmada (política AD-79/AD-80) |

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
| `sv_available_m3` | Float (related) | Saldo del ledger SV |
| `imputed_volume_m3` | Float, digits (16, 3) | Porción imputada desde ese SV |
| `cost_per_m3_usd` | Float, digits (16, 4) | Costo unitario del SV origen (§5.5) |
| `amount_usd` | Float (compute) | `imputed_volume_m3 × cost_per_m3_usd` |
| `sv_operation_id` | M2O `madenat.sv.operation` | Operación `imputacion` generada |

### 5.3 Tipo de acción del ledger (D3)

- Se **añade** el valor `'imputacion'` al Selection `madenat.sv.operation.action_type` (hoy: `rename`, `regularize_volume`, `rebaja`, `rebaja_reverse`). Etiqueta propuesta: **«Imputación a procesados»**.
- Campos de la operación reutilizados: `lot_id` (SV), `rebaja_volume_m3` (volumen imputado), `destination_reference='Imputación <procesador>'`, `reason` (obligatorio), `state='applied'` al ejecutar, `snapshot_json`/`audit_hash`.
- **Nuevo** vínculo propuesto: `imputation_id` (M2O → `madenat.sv.imputation`) en `madenat.sv.operation`, análogo a `destination_shipment_id`/`destination_container_id` ya existentes en Logistics.
- **Alternativa (si se prefiere cero cambio de Selection):** reutilizar `action_type='rebaja'` con `destination_reference='Imputación <procesador>'`. Se registra como **pregunta abierta** (§17, Q-19-1); la recomendación de este documento es el valor propio `imputacion` (trazabilidad y reporte inequívocos).
- **Saldo SV ampliado (D3):** `sv_available_m3 = sv_regularized_baseline_m3 − Σ rebajas activas − Σ imputaciones activas` (§7, alinea AD-84).

---

### 5.4 Ubicaciones — «En poder del procesador X» (D5)

- **Padre:** `stock.location` **`Procesadores`**, `usage='internal'` (p. ej. bajo `WH/Stock/Procesadores`). Nativo Odoo: **cero desarrollo de modelo**; se crea bajo demanda y **nunca se elimina con stock** (mismo criterio que el patio, AD-65 §1.5).
- **Hijas:** una ubicación por procesador — **`Procesadores/<PROCESADOR>`** — creada bajo demanda al enviar/registrar SV en poder de ese procesador.
- **Propiedad:** `usage='internal'` ⇒ **el inventario es de MADENAT** (no consignación). El saldo por procesador es el Σ de quants de esa ubicación.
- **Saldo por procesador:** vista/reporte de solo lectura propuesto `madenat.processor.balance` (o reporte de `madenat_lumber_reports`) agrupando `stock.quant` por ubicación bajo `Procesadores`, con nominal/disponible y antigüedad.

### 5.5 Costo (D4)

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
| `applied` | Ejecutada | Ledger `imputación` + **salida nativa** + costo | Operaciones |
| `reversed` | Reversada | Contrapartida (retorno nativo + op. SV opuesta ligada) | Jefatura / Gerencia |
| `cancelled` | Anulada sin efecto | No hubo salida | Operaciones / Jefatura |

**Regla [DISEÑO]:** una guía de procesados puede validarse con su imputación en `pending`; el sistema **no bloquea** (D8). La pendiente se **audita** y alimenta las alertas de saldo por procesador.

---

## 7. Reglas

### 7.1 Reglas duras (integridad técnica / financiera)

- **[VIGENTE]** Ningún `stock.move` puede dejar `stock.quant` **negativo**. La salida nativa del SV nunca excede el disponible del quant (techo técnico).
- **[VIGENTE]** Los **permisos por rol** se validan en servidor (patrón `_rebaja_require_group`, AD-86/16).
- **[VIGENTE]** **Reglas financieras**: tipo de cambio, cierre de período y UoM (m³, `digits=(16,3)`) permanecen **duras**.
- **[DISEÑO]** La salida nativa del SV ocurre **una sola vez** por imputación (idempotencia por `picking_id`, causa única AD-84).
- **[DISEÑO]** Los **invariantes** de AD-84 se mantienen verificables (§7.3).

### 7.2 Reglas blandas (D8: advertir, motivar, auditar)

- Si el volumen imputado **supera el saldo SV** disponible para ese origen → **advertencia**, se exige **motivo**, se **audita** (no se impide, salvo el techo técnico del quant).
- Si el volumen nominal de la etiqueta **difiere** de la propuesta automática más allá de una tolerancia (por decidir, §17 Q-19-4) → **advertencia + motivo**.
- Si el **costo por m3** está fuera de rango (respecto del histórico del producto/SV) → **advertencia + motivo**.
- Si el procesador no está marcado `is_processor` o no existe ubicación `Procesadores/<X>` → **advertencia**; se ofrece crearla (nativo).
- **[DISEÑO]** Todo lo anterior se registra en `deviation_flags` y en el snapshot de auditoría.

### 7.3 Invariantes (alineados con AD-84, ampliados)

1. `stock.lot.volumen_restante_m3 = Σ stock.quant.quantity` (ubicaciones internas, base NOMINAL).
2. **Saldo SV ampliado:** `stock.lot.sv_available_m3 = sv_regularized_baseline_m3 − Σ rebajas activas − Σ imputaciones activas`.
3. **Cota por destino:** Σ (rebajas + imputaciones) por SV ≤ volumen oficial (NOMINAL) del lote.
4. **Causa única de descuento del SV:** **imputación** (procesados) o ajuste autorizado; la rebaja aplica solo a lotes de **tarja** en export (AD-82). Sin dobles descuentos.
5. **Concurrencia fail-closed** del ledger (guarda `_sv_concurrency_guard`).

---

## 8. Alertas

| ID | Alerta | Disparador | Destino |
|---|---|---|---|
| AL-01 | **Imputación pendiente** | Imputación en `pending` > umbral de días (a decidir) | Operaciones |
| AL-02 | **Saldo por procesador ≠ 0 al cierre** | Σ quant en `Procesadores/*` > 0 al cierre de período | Operaciones / Auditoría |
| AL-03 | **SV sin retorno** | SV con antigüedad > umbral sin imputación | Operaciones |
| AL-04 | **Desviación de volumen** | `|nominal − propuesta| > tolerancia` | Auditoría |
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

### 10.3 Asistente de contenedores — ocultar SV por defecto (D9)

En el asistente de asignación a contenedor (`lumber.container.lot.wizard`) los **lotes SV (`lot_flow_type='volume'`) se ocultan por defecto** (filtro de visibilidad). **No se impide** seleccionarlos: el filtro es una elección de UX (el SV no se exporta), reversible por el usuario. Alineado con §2.1 (SV nunca se exporta).

### 10.4 Trazabilidad visible

- Bloque «Imputación» en la guía de procesados y en la Consola: SV origen, volumen imputado, saldo restante, costo, motivo y desviaciones.
- Saldo por procesador visible (reporte `madenat.processor.balance`).
- Historial del ledger SV (append-only) y `madenat.audit.log` con firma.

---

## 11. Casos límite

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

- Solo **añadidos**: modelo `madenat.sv.imputation(.line,.sv.line)`, valor de `action_type='imputacion'`, campos opcionales en `madenat.sv.operation` (`imputation_id`) y `res.partner`/`stock.lot` según §5. **Sin renombres.**
- Campos nuevos **no `required`** sobre registros históricos.

### 12.4 `parent_lot_id` opcional (I6)

- Paso **controlado y separado**: revisar consumidores (`madenat_toll_processing`, `12`/`13`) antes de relajar `required`/restricción. **No** en esta fase.

---

## 13. Riesgos y contradicciones

### 13.1 Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| R-19-01 | **Doble descuento del SV** (imputación + rebaja de export) | SV nunca se exporta (§2.1); causa única = imputación (§7.3.4); idempotencia por `picking_id`. |
| R-19-02 | **Saldo SV ⟷ quant desalineado** | Invariante §7.3.2; salida nativa atómica con el ledger. |
| R-19-03 | **Costo del SV inexistente** | Brecha declarada (§5.5); costo por m3 editable + fuente propuesta; fase I5. |
| R-19-04 | **Imputación declarada sin evidencia física** | Por diseño (D2); motivo obligatorio + auditoría + snapshot firmado. |
| R-19-05 | **Uso indebido de ubicación interna** (confundir con consignación) | `usage='internal'` documentado (§5.4); el inventario es MADENAT. |
| R-19-06 | **Exceso de volumen** sobre el saldo | Advertencia + motivo (§7.2); techo técnico del quant. |
| R-19-07 | **Pendientes que cruzan el cierre** | AL-01/AL-02 + regla financiera dura (§7.1, L-08). |

### 13.2 Contradicciones resueltas por este documento

| # | Contradicción | Resolución |
|---|---|---|
| CR-19-01 | `17` §2.8 / AD-83: la rebaja SV **solo** mueve el ledger **sin** efecto en `stock.quant` vs. D3 (el SV sale del quant al imputar). | **Reencuadre:** para el caso **procesados**, la imputación **sí** tiene efecto nativo (salida del quant SV). La rebaja de contenedores del `18` (sin efecto en quant del SV) deja de aplicar al SV (el SV no se exporta). Se actualiza `17` §2.8 y `18`. |
| CR-19-02 | `18` §1.3/§5: «rebajar» el SV a contenedor (export) vs. D1 (SV nunca se exporta). | **Resuelto:** la consolidación/rebaja de export aplica solo a lotes de **tarja**; se actualiza `18` §1.3/§5/§7. |
| CR-19-03 | AD-65 §1.6 usa `parent_lot_id`/genealogía de forma condicional vs. D2 (imputación declarada, sin genealogía). | **Alineado:** la imputación **no** usa genealogía; `parent_lot_id` pasa a opcional en I6 (D10). |
| CR-19-04 | AD-64 registra la brecha de costo pero no el caso SV (SV sin costo) vs. D4. | **Ampliado:** AD-64 se extiende con el costo del SV y su fuente propuesta (§5.5). |
| CR-19-05 | AD-83 (módulo propio rebaja SV) vs. D3 (imputación sin módulo nuevo). | **AD-83 REEMPLAZADA por AD-87** (§4.4, §16). |

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
| B-01 | **Zarpe** exige contenedores en estado `rebajado` (no zarpable si falta rebaja) | `lumber.export.shipment.action_set_in_transit` (`18` §14.1) | **Advertencia con motivo** | Es un evento logístico; bloquear al profesional viola D8. Se advierte el riesgo de **stock residual** y se exige **motivo**; se audita. La causa única de descuento (AD-84) se preserva porque el zarpe **no descuenta**. |
| B-02 | **Rebaja sin disponible** (intentar descontar más que el quant) | salida nativa (`stock.move`) | **Duro (integridad técnica)** | Odoo prohíbe quant negativo. Se acompaña de mensaje profesional que indica ajustar volumen/nominal o dejar la etiqueta sin rebajar. El **exceso nominal** sobre el saldo SV (antes del quant) es **advertencia + motivo** (§7.2). |
| B-03 | **Reversa con embarque entregado** (o viaje cancelado) | `_rev...` / `action_reverse` (`18` §4.5, §14.1) | **Duro** por defecto; **override de Gerencia con motivo** como opción a decidir | Toca **historia** y potencial **período cerrado** (regla financiera dura). Se propone mantenerlo duro y habilitar excepción solo por Gerencia, con motivo y auditoría. **Pregunta abierta** Q-19-5. |
| B-04 | **Saldo SV** (Σ rebajas/imputaciones > saldo) | ledger + invariantes (`18` §5.2, `17` §3) | **Advertencia con motivo** (contable), **duro** en el techo del quant | Cumple D8: se advierte la desviación, se exige motivo y se audita. El límite físico (quant) sigue duro. |
| B-05 | **Rol insuficiente** para consolidar/rebajar/rebajar por nave/reversar | `_rebaja_require_group` (`18` §8) | **Duro** | Permisos por rol son duros (D8). |
| B-06 | **Viaje cerrado** (`shipping.voyage.state ∈ departed/arrived/cancel`) | `shipping_voyage.py`, `18` §4.5 | **Duro** | Regla financiera/período cerrado. |
| B-07 | **Costos distribuidos** impiden rolleo | `lumber_container_rollover_wizard.py:149-162` | **Duro** (con ruta: revertir costos primero) | Integridad financiera. |
| B-08 | **Duplicado de lote** en dos contenedores activos (`_check_lot_duplication`) | `lumber.container` (`18` §14.4, H-N1) | **Duro** (técnico) | Evita doble imputación de un mismo lote. **Pregunta abierta** H-N1 (¿el negocio requiere un lote en varios contenedores?). |

**Síntesis:** pasan a **advertencia con motivo**: **B-01 (zarpe)**, **B-04 (saldo SV)**. Permanecen **duros**: **B-02, B-05, B-06, B-07, B-08**. **B-03** queda duro con **override de Gerencia** sujeto a decisión (Q-19-5). Todos los casos con motivo se registran en `madenat.audit.log` (snapshot + firma) y en `deviation_flags`.

---

## 15. Plan de pruebas T-01..T-12 [DISEÑO]

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

## 16. Backlog por fases I1..I6 (D10, Entregas 4–5)

> Fases **incrementales** del frente de imputación. Cada fase declara **dependencias**, **riesgos** y **criterios de aceptación**. El detalle se refleja en `05_BACKLOG.md`.

### I1 — Cimientos: ubicaciones y saldo por procesador
- **Alcance:** `stock.location` `Procesadores` + hijas bajo demanda; reporte `madenat.processor.balance`; marcar procesadores (`res.partner.is_processor`).
- **Dependencias:** AD-65 §1.5 (patrón patio); `is_processor` (ya existe en `madenat_lumber_reception_improvements`).
- **Riesgos:** R-19-05 (mal uso de ubicación interna).
- **Aceptación:** T-09; ubicaciones creadas bajo demanda sin stock residual al desinstalar; reporte cuadra con Σ quant.

### I2 — Modelo de imputación
- **Alcance:** `madenat.sv.imputation` (+`.line`, +`.sv.line`), estados §6, motivo/`deviation_flags`, secuencia.
- **Dependencias:** I1; `madenat.sv.operation` (AD-79/AD-80).
- **Riesgos:** R-19-04; complejidad de la relación N:M.
- **Aceptación:** T-01..T-03, T-06; CRUD con seguridad por rol; sin efectos en stock en `draft`/`pending`.

### I3 — Salida nativa del SV + ledger `imputacion` + invariantes
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
| Q-19-1 | **Valor de `action_type` del ledger** | ¿Valor propio `imputacion` (recomendado) o reutilizar `rebaja` con `destination_reference`? |
| Q-19-2 | **Fuente del costo del SV** | ¿`total_amount_usd / official_volume_m3` de la guía de Volumen, precio unitario de la OC, o carga manual? |
| Q-19-3 | **Retorno a granel sin etiquetas** | ¿Cómo se imputa un retorno sin detalle de etiquetas (por volumen agregado)? |
| Q-19-4 | **Tolerancias** de desviación | ¿Umbral de volumen (m³/%) y de costo para disparar advertencia? |
| Q-19-5 | **Reversa y rol** (B-03) | ¿Gerencia con motivo puede reversar tras entrega? ¿Ventana? |
| Q-19-6 | **Umbrales de alerta** | ¿Días para AL-01 (pendiente) y AL-03 (SV sin retorno)? |
| Q-19-7 | **`parent_lot_id` opcional (I6)** | ¿Se mantiene `required` hasta I6? ¿Aplica a C2? |
| Q-19-8 | **H-N1** (lote en dos contenedores) | ¿El negocio requiere un lote en varios contenedores activos? |

---

## 18. Mantenimiento y evidencia

- **Alcance de esta versión:** documental. **No** se modificó código, datos ni parámetros; **no** hubo push.
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
