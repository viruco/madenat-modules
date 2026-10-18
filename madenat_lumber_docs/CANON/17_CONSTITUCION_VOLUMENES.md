# 17 — Constitución de Volúmenes (NOMINAL / DISPONIBLE / EXPORTACIÓN / OFICIAL)

**Versión documental:** 1.10.0
**Fecha de actualización:** 2026-10-18  <!-- 2026-10-18: Cierre Bloque 4I (AD-121): definición de pruebas oficiales de integridad (Consulta B volúmenes y Consulta A.2 estructural sin write_date), consulta con write_date como informativa (aviso de fila tocada), documentación de fila residuo TEST-LOT-EX (id 49837) y regla de rollback estricto sin registry.cursor(). Versión 1.9.0 → 1.10.0. | 2026-10-18: Cierre Bloque 4H (AD-121). -->
**Estado:** ✅ Vigente — Documento canónico de la **constitución de volúmenes** de MADENAT. Fija qué significa cada volumen, qué proceso usa cuál, y las reglas acordadas para el diseño futuro. No sustituye a `00_ARQUITECTURA.md`, `04_DECISION_LOG.md`, `08_COSTEO.md`, `12_FLUJOS_INGESTA.md` ni `13_CONSOLIDACION_OPERATIVA.md`; los referencia.

> Este documento **fija nomenclatura y reglas de uso**. Las definiciones de §1 corresponden a lo **acordado con el usuario el 2026-10-01**. Las reglas de §2 describen el comportamiento **vigente verificado en código** (informe de auditoría de volúmenes del 2026-10-01). Las de §3 están **ACORDADAS y pendientes de implementación** (no vigentes hasta su ejecución). Las decisiones de §7 son **PROPUESTAS — NO APROBADAS**.

---

## 1. Definiciones acordadas (2026-10-01)

Cuatro volúmenes conviven en el sistema. **No son sinónimos** y su uso equivocado produce descuadres de stock, capacidad y documentos.

### 1.1 Volumen NOMINAL (nominal volume)
- **Definición:** **base de medida del stock de MADENAT**. Es lo que se compra, lo que **Odoo mueve** (movimientos y quants) y lo que se **valoriza**.
- **Campos:** `stock.lot.volume_purchase_m3` y `stock.lot.volumen_m3`.
- **UoM:** metro cúbico (m³) — `uom.product_uom_cubic_meter`.
- **Fuente técnica:** “Constitución técnica de volúmenes” (`madenat_lumber_logistics/models/lumber_export_shipment.py:20-30`) y “LA VERDAD DE BODEGA… este es el nominal” (`madenat_lumber_core/models/lumber_reception.py:316-332`).

### 1.2 Volumen DISPONIBLE (available volume)
- **Definición:** lo que **queda físicamente** en base nominal; **es el stock** (`stock.quant`). Puede ser **menor que `volumen_m3`** tras consumo parcial, salida o ajuste.
- **Campos:** `stock.quant.quantity`, expuesto como `stock.lot.volumen_restante_m3` (`stock_lot.py:622`, compute `_compute_volumen_restante_m3` `stock_lot.py:1022`).

### 1.3 Volumen de EXPORTACIÓN (export / shipment volume)
- **Definición:** **conversión documental** (pulgadas y fracciones; fórmulas export: 1550.003 S2S/métrico, 5085.312 Blank, overmeasure `+1/8"` según exclusiones). Se usa en **manifiesto, BL, tarja y packing list**.
- **Campo:** `stock.lot.vol_shipment_m3` (`stock_lot.py:452`). **Dato de documento: no gobierna stock ni valorización.**

### 1.4 Volumen OFICIAL de la guía (official volume)
- **Definición:** dato **documental** de la guía de **Recepción por Volumen**; jerarquía **PDF > Excel > Packing**. Gobierna el ingreso por Volumen.
- **Campo:** `official_volume_m3` (`madenat_lumber_intake/models/intake_guia_processing.py:111,206`; regla en `12_FLUJOS_INGESTA.md` §11.5, AD-79).
- **Particularidad SV:** en un **lote SV (Lote Volumen)** el volumen oficial **coincide** con el nominal y con la exportación (sin dimensiones; §2.8).

### 1.5 Relación entre los cuatro
```
NOMINAL    = volume_purchase_m3 = volumen_m3             (compra / stock / valorización)
DISPONIBLE = stock.quant.quantity = volumen_restante_m3  (físico remanente en base nominal)
EXPORTACIÓN = vol_shipment_m3                            (documento: manifiesto/BL/tarja/packing)
OFICIAL (SV) = official_volume_m3                        (guía Volumen; = nominal = export en SV)
```

---

## 2. Reglas de uso por proceso (vigente verificado)

> Base: informe de auditoría de volúmenes del 2026-10-01. “Archivo:línea” apunta al código y a la documentación que respaldan cada fila.

| Proceso | Volumen que usa | Campo (origen) | Archivo:línea |
|---|---|---|---|
| **Ingreso a stock — Recepción (Producto)** | NOMINAL | `product_uom_qty = Σ line.vol_purchase_m3`; UoM m³ | `madenat_lumber_core/models/reception_service.py:181,216-238` |
| **Ingreso a stock — Guía procesados** | NOMINAL | `product_uom_qty = d['volumen'] = vol_purchase_m3` | `madenat_lumber_core/models/madenat_guia_processing.py:1200,4349-4353` |
| **Ingreso a stock — Volumen SV** | OFICIAL = NOMINAL = EXPORT | `quantity = official_volume_m3` | `madenat_lumber_intake/models/intake_guia_processing.py:557-563,598-620` |
| **Consumo de procesados (a Producción)** | NOMINAL | `product_uom_qty = lot.volumen_m3` | `madenat_guia_processing.py:2260-2266,2414-2416` |
| **Capacidad y ocupación del contenedor** | EXPORT (**desalineado**, §6) | `volume_m3 = Σ lot.vol_shipment_m3`; `fill_percentage`; `remaining_volume_m3` | `madenat_lumber_logistics/models/lumber_container.py:505-534,580-584,608-615` |
| **Validación del asistente de asignación** | NOMINAL | `Σ selected_lot_ids.volumen_m3` vs `max_volume_m3` | `madenat_lumber_logistics/wizards/lumber_container_lot_wizard.py:170-190,212,340-356` |
| **Totales del contenedor** | EXPORT + NOMINAL | `total_vol_shipment_m3`=Σ`vol_shipment_m3`; `total_volume_purchase_m3`=Σ`volume_purchase_m3` | `lumber_container.py:118-136,505-534` |
| **Totales del embarque** | EXPORT + NOMINAL | `total_volume_m3`=Σ cont.`volume_m3`; `total_nominal_volume_m3`=Σ cont.`total_volume_purchase_m3` | `madenat_lumber_logistics/models/lumber_export_shipment.py:366-369` |
| **Rendimiento (yield)** | EXPORT − NOMINAL | `yield_variance_m3 = total_volume_m3 − total_nominal_volume_m3`; `yield_efficiency_pct` | `lumber_export_shipment.py:307-317` |
| **Rebaja SV (asignación a contenedor)** | Saldo SV del **ledger** (no toca stock) | `sv_available_m3 = baseline − rebajado`; `sv_create_rebaja` sin `stock.move`/`stock.quant` | `lumber_container.py:411-446`; `madenat_lumber_core/models/madenat_sv_operation.py:14,923-950,1032-1036` |
| **Documentos — Tarja/Packing XLSX** | EXPORT (izq) + NOMINAL (der) | `vol_shipment_m3` / `volumen_m3` | `lumber_container.py:845,851`; `lumber_export_shipment.py:845,851` |
| **Documentos — Packing PDF** | NOMINAL + EXPORT + MBF | `total_volume_purchase_m3`, `volume_m3`, `volume_mbf` | `madenat_lumber_logistics/reports/lumber_container_packing_list_template.xml:37-39` |
| **Prorrateo de costos — `volume_physical`** | NOMINAL | factor = `lot.volumen_m3 / Σ` | `madenat_lumber_costing/wizards/lumber_cost_distribution.py:75-78,183-185` |
| **Prorrateo de costos — `volume_export`** | EXPORT | factor = `lot.vol_shipment_m3 / Σ` | `lumber_cost_distribution.py:75-78,178-181` |

### 2.8 Nota SV (Lote Volumen) — reescrita 2026-10-01 (AD-87)
- El lote SV se crea con `volume_purchase_m3 = vol_shipment_m3 = volumen_m3 = official_volume_m3` y dimensiones = 0 (`intake_guia_processing.py:557-563`).
- **El SV nunca se exporta** (D1): los lotes `lot_flow_type='volume'` **no** participan de la consolidación/rebaja de exportación (documento `18`), que opera sobre lotes de **tarja**.
- **Salida del stock del SV:** la produce la **imputación** etiqueta→SV (AD-87) mediante **salida nativa** (picking/`stock.move`), de forma **atómica** con el asiento del ledger (`madenat.sv.operation`, tipo `imputacion`). El efecto es **físico y trazable** sobre el quant del SV.
- **Reconciliación (CR-19-01):** la nota previa —«la rebaja SV sólo mueve el ledger, sin efectos en `stock.quant`» (`madenat_sv_operation.py:14`)— describía la **asignación SV a contenedor de exportación**, que **deja de aplicar** al SV (no se exporta). Para el caso **procesados**, la imputación **sí** descuenta el quant del SV. El saldo SV incorpora las imputaciones activas: `sv_available_m3 = sv_regularized_baseline_m3 − Σ rebajas activas − Σ imputaciones activas` (`19` §7.3; AD-84 ampliada).

### 2.9 Invariante verificado en datos (`madenat_test`, 2026-10-01)
- 78 lotes con quant interno > 0; **77 tienen `quant.quantity == volumen_m3`** (nominal) → el stock almacenado **es** el nominal. 41 lotes sin quant interno (consumidos/revertidos).

---

## 3. Reglas acordadas para el diseño futuro — ACORDADO (pendiente de implementación)

> Estado: **ACORDADO** con el usuario el 2026-10-01. **NO vigente**: son reglas objetivo de diseño; el código actual **no** las cumple todavía. No implican cambio de código en esta sesión.

| # | Regla ACORDADA | Situación actual (a corregir) |
|---|---|---|
| A-1 | **La salida nativa de stock ocurre al “rebajar” el contenedor o la nave** (acción explícita de rebaja). El **zarpe deja de descontar** stock. | Hoy el descuento ocurre al zarpe (`action_set_in_transit` → `_action_reduce_stock`, `lumber_export_shipment.py:461,479`) y mueve `quantity=1` por lote (`:571,582`). |
| A-2 | **En lotes SV con asignación parcial, sale exactamente el volumen asignado.** | Hoy sale `1` por lote, sin usar el volumen de la asignación (rebaja) ni el disponible. |
| A-3 | **La capacidad y la validación del contenedor se calculan en DISPONIBLE (base nominal)**, no en export ni en el nominal bruto desactualizado. | Hoy la ocupación usa export (`volume_m3=Σ vol_shipment_m3`, `lumber_container.py:528`) y el asistente usa `volumen_m3` (`lumber_container_lot_wizard.py:187`), ignorando `volumen_restante_m3`/quant. |

**Nota:** mientras A-1..A-3 no se implementen, rige el comportamiento de §2 (vigente). Toda implementación debe registrar su AD de aprobación y actualizar §2 y §6.

---

## 4. Glosario de etiquetas (actuales vs propuestas)

> **No se cambia código.** Esta tabla documenta el desajuste entre lo que muestran las superficies y la constitución de §1, y propone la etiqueta correcta (término técnico en inglés entre paréntesis).

| Etiqueta actual | Campo real | Volumen que muestra | ¿Conforme a §1? | Etiqueta propuesta | Archivo:línea |
|---|---|---|---|---|---|
| “Vol. Físico Real (Facturable)” | `total_vol_shipment_m3` | EXPORT | ❌ No | “Vol. Exportación (facturable)” | `lumber_container.py:119-120` |
| “Vol. Nominal (Ref. Costo)” | `total_volume_purchase_m3` | NOMINAL | ✅ Sí | (conservar) / “Vol. Nominal (stock)” | `lumber_container.py:128-130` |
| “Volumen m³ (Total)” (help “Alias de Vol. Físico”) | `volume_m3` | EXPORT | ❌ No | “Vol. Exportación (total)” | `lumber_container.py:145-151` |
| “Vol. Físico (m³)” | `total_vol_shipment_m3` | EXPORT | ❌ No | “Vol. Exportación (m³)” | `lumber_container_views.xml:154-158` |
| “Vol. Nominal (m³)” | `total_volume_purchase_m3` | NOMINAL | ✅ Sí | (conservar) | `lumber_container_views.xml:160-164` |
| “Vol. de Embarque” | `volume_m3` | EXPORT | ⚠️ Ambiguo | “Vol. Exportación (m³)” | `lumber_export_shipment_views.xml:140` |
| “Vol. Físico (m³)” | `physical_volume_m3` → `lot.volumen_m3` | NOMINAL | ⚠️ Nombre | “Vol. Nominal (stock)” | `lumber_shipment_line.py:41-47` |
| “Vol. Físico (Real)” | `vol_shipment_m3` | EXPORT | ❌ No | “Vol. Exportación (m³)” | `mixin_lumber_ingest.py:308` |
| “Vol. Nominal (Compra)” | `vol_purchase_m3` | NOMINAL | ✅ Sí | (conservar) | `mixin_lumber_ingest.py:311` |
| “Vol. Físico Real (Staging)” | `vol_physical_real_m3` | producto métrico físico | ⚠️ Ambiguo | “Vol. métrico físico (staging)” | `lumber_reception.py:310-316` |
| “Vol. Físico (m³)” (help “LA VERDAD DE BODEGA… es el nominal”) | `vol_physical_m3` (mm×mm×m) | producto métrico físico | ❌ No (help) | “Vol. métrico físico” | `lumber_reception.py:319-326` |
| “Vol. Exp (m³)” | `vol_shipment_m3` | EXPORT | ✅ Sí | (conservar) | `lumber_reception.py:413-419` |
| “Vol. Físico m³” (guía) | `vol_fisico` | NOMINAL | ⚠️ Nombre | “Vol. Nominal (stock)” | `views/guia_processing_views.xml:53,581,1087` |
| “Vol. Origen (m³)” | `lot_volumen_m3` | NOMINAL | ✅ Sí | (conservar) | `madenat_lumber_reports/views/inventory_report_views.xml:153` |
| “Stock / Stock Real” | `quantity` (quant) | NOMINAL/DISPONIBLE | ✅ Sí | (conservar) | `inventory_report_views.xml:194,257` |
| “V. STOCK NOMINAL” | `total_volume_purchase_m3` | NOMINAL | ✅ Sí | (conservar) | `lumber_container_packing_list_template.xml:28,37` |
| “VOL. EMBARQUE REAL” | `volume_m3` | EXPORT | ⚠️ Ambiguo | “VOL. EXPORTACIÓN” | `lumber_container_packing_list_template.xml:29,38` |

**Regla editorial propuesta:** reservar **“físico/disponible”** para stock nominal disponible, **“nominal”** para compra/valorización, y **“exportación”** para la conversión documental. Evitar “real” como sinónimo de export.

---

## 5. Conciliación de documentos (tensión y corrección)

Existen tres piezas que hablan de volumen con vocabulario en tensión. Se concilian así, **sin contradicción de fondo** una vez fijada la nomenclatura de §1.

### 5.1 La especificación (base)
`madenat_lumber_logistics/models/lumber_export_shipment.py:20-30` declara:
- **VOLUMEN FÍSICO (Stock Real) → campo NOMINAL (`total_volume_purchase_m3`)**: “lo que Odoo descuenta de los racks”.
- **VOLUMEN DE EMBARQUE (Exportación) → campo REAL (`volume_m3`)**: metraje geométrico del Manifiesto/BL.

Esta es la **base** de la Constitución (§1).

### 5.2 `WIKI/02_TECNICO/modelo_despachos.md:449`
- **Texto actual:** “`volume_m3` del contenedor es alias de `total_vol_shipment_m3` (**volumen físico real, no nominal**).”
- **Diagnóstico:** describe el **código correctamente** (`volume_m3 = Σ vol_shipment_m3`, `lumber_container.py:528`), pero **invierte el término**: llama “físico real” al **export**.
- **Corrección propuesta:** “`volume_m3` del contenedor es **alias de `total_vol_shipment_m3` (volumen de EXPORTACIÓN, no nominal)**.”

### 5.3 AD-67 (`CANON/04_DECISION_LOG.md:1471`)
- **Texto actual:** “`stock.lot.volumen_m3` **es documental** (no se ajusta tras consumo parcial)… `volumen_restante_m3` … **fuente de verdad de volumen físico disponible**.”
- **Diagnóstico:** no es contradictorio con la spec, pero **califica `volumen_m3` como “documental”**, cuando en la Constitución `volumen_m3` es el **NOMINAL base de stock** (dato de compra/valorización), no un simple documento. Lo que AD-67 quiere decir es que **`volumen_m3` no se recalcula tras consumo parcial**, mientras que el **DISPONIBLE** (`volumen_restante_m3`/quant) sí.
- **Corrección propuesta (reencuadre, sin cambiar la decisión):** “`stock.lot.volumen_m3` es el **volumen NOMINAL base de stock** (no se ajusta tras consumo parcial); `volumen_restante_m3` es el **volumen DISPONIBLE** (físico remanente en base nominal).”
- **Nota:** la frase “es documental” choca con §1.1; el resto de AD-67 sigue vigente (campo `volumen_restante_m3`, reporte corregido, tests).

### 5.4 `CANON/00_ARQUITECTURA.md:124,176-177`
- Ya nombra `vol_shipment_m3` como “volumen de exportación” y `volume_purchase_m3` como “volumen nominal de compra”: **alineado**. Sólo se recomienda añadir una referencia cruzada a `17` para fijar `volumen_m3` = NOMINAL.

### 5.5 Síntesis de conciliación
| Fuente | Afirmación | Estado tras conciliar |
|---|---|---|
| `lumber_export_shipment.py:20-30` | NOMINAL = stock; EXPORT = documento | **Base** de §1 |
| `modelo_despachos.md:449` | `volume_m3` = export “físico real” | **Corregir etiqueta** → “exportación” |
| `04_DECISION_LOG.md:1471` (AD-67) | `volumen_m3` documental; `volumen_restante_m3` físico | **Reencuadrar** → NOMINAL / DISPONIBLE |
| `00_ARQUITECTURA.md:124,176-177` | nombres de campo | **Alineado** |

---

## 6. Hallazgos — estado (F-01/F-02 RESUELTOS; resto pendiente)

> Registrados por el informe de auditoría de volúmenes del 2026-10-01. **No se aplicó ningún cambio de código, dato ni parámetro.** Se documentan aquí para que su corrección se planifique y registre por su AD correspondiente.

| ID | Hallazgo | Evidencia (archivo:línea) | Impacto | Corrección objetivo (a decidir) |
|---|---|---|---|---|
| **F-01** | ~~La **salida al zarpe** crea el picking con `quantity = 1` por lote (no usa el volumen).~~ **✅ RESUELTO (2026-10-01, AD-82/AD-84)** — el zarpe **ya no descuenta** (`action_set_in_transit` exige contenedores `rebajado`); la salida nativa ocurre al rebajar (volumen por tipo de lote). `_action_reduce_stock` eliminado. | `madenat_lumber_logistics/models/lumber_export_shipment.py` (antes `:571,582`) | Descuento parcial: corregido. | — |
| **F-02** | ~~El **asistente de asignación** calcula y valida capacidad con `volumen_m3` (nominal bruto), **no** con el DISPONIBLE (`volumen_restante_m3`/quant).~~ **✅ RESUELTO (2026-10-01, A-3/AC-5)** — el asistente usa `volumen_restante_m3` (DISPONIBLE base nominal) y excluye lotes sin disponible; caso lote 2585 cubierto por test. | `wizards/lumber_container_lot_wizard.py` (`_compute_new_totals`, dominio) | Sobrestimación corregida. | — |
| **F-03** | `_compute_vol_shipment_m3` en `stock.lot` es **huérfano**: el método existe pero el campo `vol_shipment_m3` **no declara `compute=`**. | `madenat_lumber_core/models/stock_lot.py:452` (campo) vs `:469` (método) | El export del lote es una **copia congelada**; no se recalcula si cambian dimensiones. | Decidir: cablear el compute o eliminar el método muerto. |
| **F-04** | Variable **`v_stock_real` engañosa**: contiene `item.vol_shipment_m3` (**export**), pero se lee como “stock real” y al “stock real” se le asigna `vol_purchase_m3`. | `madenat_guia_processing.py:1164,1167,1230-1240` | Riesgo de mantenimiento (no hay inversión de datos hoy). | Renombrar (`v_export_m3`) sin cambiar el mapping. |
| **F-05** | Comentario de `vol_physical_m3` (“LA VERDAD DE BODEGA… este es el nominal”) **contradice** su cálculo (mm×mm×m métrico) y el move usa `vol_purchase_m3`. | `madenat_lumber_core/models/lumber_reception.py:316-332` (comment) vs `_compute_vol_physical_strict` (`:421-440`) | Documentación interna inconsistente. | Corregir comentario o el campo, según AD. |

---

## 7. Decisiones y su estado (AD-82/AD-83/AD-84 · AD-87)

> Registradas en `04_DECISION_LOG.md`. Estado al 2026-10-01: **AD-82 y AD-84 APROBADAS e implementadas** (contenedores/naves); **AD-83 REEMPLAZADA por AD-87**; **AD-87 APROBADA** (imputación etiqueta→SV y saldo por procesador). Fuente normativa vigente: `19_IMPUTACION_SV_Y_PROCESADORES.md`.

- **AD-82 (APROBADA) — Salida única de stock al rebajar contenedor/nave.** La salida nativa ocurre en la acción de **rebajar**; el **zarpe no descuenta**. Rige la **exportación de lotes de tarja**; el **SV no se exporta** (su salida es la imputación, AD-87).
- **AD-83 (⛔ REEMPLAZADA por AD-87) — Módulo propio de rebaja SV.** Con D1/D3, el «descuento por procesados» se materializa como **imputación**; no se extrae módulo propio y la asignación SV a contenedor de exportación no aplica. El principio «descontar exactamente el volumen asignado (no `1`)» se conserva (AD-82 tarja / AD-87 SV).
- **AD-84 (APROBADA, ampliada por AD-87) — Invariantes del ledger y del stock.** (i) `volumen_restante_m3` = Σ quant interno; (ii) `sv_available_m3` = baseline − Σ rebajas activas − **Σ imputaciones activas**; (iii) Σ (rebajas + imputaciones) por destino ≤ volumen oficial del lote; (iv) todo descuento de stock tiene una única causa trazable (**imputación** para el SV; rebaja para tarja; ajuste autorizado). Con guardas de concurrencia.
- **AD-87 (APROBADA) — Imputación declarada etiqueta→SV y saldo por procesador.** Vínculo declarado, sin genealogía; efecto físico único del SV; ubicación interna `Procesadores/<X>`; merma documental; costo por m3 editable. Detalle: `19`.

Detalle y redacción completa: `CANON/04_DECISION_LOG.md` (AD-82, AD-83, AD-84, AD-87).

---

## 8. Mantenimiento y evidencia

- **Alcance:** documental. Esta sesión **no** modificó código, datos ni parámetros; no hubo commit ni push.
- **Efecto en otros documentos (a ejecutar en la misma sesión documental):** alta de `17` en `INDICE_DOCUMENTACION.md`; alta de AD-82..84 en `04_DECISION_LOG.md`.
- **Correcciones documentales recomendadas (no aplicadas en esta versión de §5, pendientes de decisión):** `WIKI/02_TECNICO/modelo_despachos.md:449` y el reencuadre de `04_DECISION_LOG.md:1471` (AD-67).
- **Fuente de verdad ante contradicción:** `CANON/INDICE_DOCUMENTACION.md` §8 (`17` cede ante el documento canónico del tema y ante `04`).

**Evidencia:**
- Informe de auditoría de volúmenes del 2026-10-01 (verificaciones de código con archivo:línea y consultas de solo lectura sobre `madenat_test`).
- Auditoría asociada: `16_AUDITORIA_20261001.md`.
- Nomenclatura en español con términos técnicos en inglés entre paréntesis, conforme a las convenciones del vault.

---

## 9. Especificación Operativa de Fórmulas y Cubicaciones (Cristhian Elgueta — 2026-10-17 / AD-116)

> Fuente de verdad primaria: Instrucciones de Operaciones (Cristhian Elgueta) y biblioteca de muestras en `muestras_documentos_ingreso/` (subcarpeta `Ejercicio Completo Cristhian Elgueta/`, `LISTADO TARJAS MN MSC ELENOIRE FA543R.xlsx`, `1° SELLOS MSC ELENOIRE FA543R RESERVA 29020535.xlsx`, `FACTURACION PACKING LIST...`, Guías 19820, 19826, 19827, 19846, 39485..39522).

### 9.1 Fórmulas Canónicas de Negocio (F1 a F4)

| Fórmula | Denominación | Expresión Matemática | Propósito, Ámbito y Estado en Código |
|---|---|---|---|
| **F1** | **Compra (Métrica)** | $\frac{\text{Esp}_{mm} \times \text{Ancho}_{mm} \times \text{Largo}_{m} \times \text{Piezas}}{1.000.000}$ | Compra y recepción en verde/bruto. Base del volumen nominal (`vol_purchase_m3`). Estado: **IMPLEMENTADO**. |
| **F2** | **Embarque (S2S Imperial)** | $\frac{\text{Esp}_{in} \times (\text{Ancho}_{S2S} + 0,125") \times \text{Largo}_{m} \times \text{Piezas}}{1550}$ | Exportación de madera seca cepillada S2S. En escuadría 6/4, $\text{Esp}_{in} = 1,5"$; en 5/4, $\text{Esp}_{in} = 1,25"$. Sobreancho $+1/8"$ ($0,125"$) obligatorio en todo el rango S2S activo en datos. Estado: **IMPLEMENTADO**. |
| **F3** | **Real Físico** | $\frac{38,1 \text{ mm} \times \text{Ancho}_{mm} \times \text{Largo}_{m} \times \text{Piezas}}{1.000.000}$ | Geometría física neta ($38,1\text{ mm} = 1,5"$). Estado en código: **FALTA** (no existe campo ni función que compute volumen físico a partir de 38,1 mm para escuadría 6/4). |
| **F4** | **Blanks (Exportación)** | $\frac{1,5" \times (\text{Ancho}_{in} + 0,125") \times \text{Largo}_{ft} \times \text{Piezas}}{5085,312}$ | Exportación en pies. Sin deducción de $1/16"$ en el espesor (espesor neto nominal $1,5"$). Vectores canónicos: $16\text{ ft} \times 250 = 4,425\text{ m³}$; $16\text{ ft} \times 270 = 4,778\text{ m³}$. Estado: **IMPLEMENTADO**. |

### 9.2 Tabla S2S Canónica y Regla de Transición (Cristhian Elgueta — Planilla de Cubicación)

La tabla canónica contractual de Cristhian Elgueta para madera aserrada S2S (Rough mm → S2S en pulgadas) comprende exactamente **15 anchos** activos en el modelo `lumber.width.s2s.map` (incluyendo 115 mm tras revertir `active=False` en `seed_s2s_115`):

| Rough (mm) | S2S Planilla (pulg) | S2S Decimal | + 1/8" (pulg) | Vol. Esperado (m³) 100 pzas, 1.5", 4.0 m | Vol/pza (m³) | Coincidencia Planilla |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 75 | 2 5/8 | 2.625 | 2.750 | 1,065 | 0,011 | COINCIDE |
| 85 | 2 7/8 | 2.875 | 3.000 | 1,161 | 0,012 | COINCIDE |
| 90 | 3 1/8 | 3.125 | 3.250 | 1,258 | 0,013 | COINCIDE |
| 95 | 3 3/8 | 3.375 | 3.500 | 1,355 | 0,014 | COINCIDE |
| 100 | 3 5/8 | 3.625 | 3.750 | 1,452 | 0,015 | COINCIDE |
| 105 | 3 7/8 | 3.875 | 4.000 | 1,548 | 0,015 | COINCIDE |
| 110 | 3 7/8 | 3.875 | 4.000 | 1,548 | 0,015 | COINCIDE |
| 115 | 4 3/8 | 4.375 | 4.500 | 1,742 | 0,017 | COINCIDE |
| 120 | 4 3/8 | 4.375 | 4.500 | 1,742 | 0,017 | COINCIDE |
| 125 | 4 5/8 | 4.625 | 4.750 | 1,839 | 0,018 | COINCIDE |
| 130 | 4 7/8 | 4.875 | 5.000 | 1,935 | 0,019 | COINCIDE |
| 140 | 4 7/8 | 4.875 | 5.000 | 1,935 | 0,019 | COINCIDE (0,01935 → 0,019) |
| 145 | 5 3/8 | 5.375 | 5.500 | 2,129 | 0,021 | COINCIDE |
| 150 | 5 5/8 | 5.625 | 5.750 | 2,226 | 0,022 | COINCIDE |
| 155 | 5 7/8 | 5.875 | 6.000 | 2,323 | 0,023 | COINCIDE |

*Nota metodológica sobre redondeo:* La verificación de volumen por pieza a 3 decimales oculta diferencias significativas en paquetes reales (por ejemplo, para 140 mm, 1 pieza da 0,01935 m³ que en la planilla figura como 0,019 m³, mientras que para 100 piezas da 1,935 m³ exactos). El criterio formal de validación es el cálculo sobre 100 piezas.

- **Anchos ausentes de la tabla S2S:** Todo ancho fuera de la tabla activa y menor al parámetro `madenat.direct_width_min_mm` (170 mm por defecto) aplica la política `madenat.out_of_table_behavior` (`'warning'` por defecto, emitiendo log y advertencia en chatter de la guía y aplicando `mm / 25.4`; `'block'`; o `'direct'`). Los anchos mayores o iguales a 170 mm (170, 175, 180, 195, 200 mm) se calculan mediante conversión métrica directa ($\text{Ancho}_{mm} / 25,4$) sin sobreancho y sin advertencia.
- **Caso REMATE 195 mm (INFERENCIA):** La muestra de línea REMATE que declara 195 mm y 4,043 m³ proviene de un documento de embarque de exportación (muestra MSC Victoria), NO de la Guía 26270 (cuyas 17 líneas corresponden exclusivamente a anchos 100, 125 y 150 mm con espesor nominal 5/4 = 1,25"). Con 194 mm el cálculo daría 4,041 m³ y directo a 195 mm daría 4,062 m³. La causa atribuida a dicha línea queda formalmente rotulada como **INFERENCIA**.
- **Impacto Real en Guía 26270 (Corrección Aritmética Canónica):** Las líneas 5140 y 5141 (ancho 150 mm, espesor 5/4", largo 4,05 y 3,70 m) almacenan actualmente 3,915 m³ y 0,493 m³ (total 4,408 m³), calculados mediante conversión directa $150 / 25,4 = 5,9055"$. Bajo la nueva regla F2 (ancho S2S de tabla 5 5/8" + 0,125" = 5,750"), su volumen recalculado es 3,812 m³ y 0,480 m³ (total 4,292 m³). Si se recalculasen los datos históricos, el total de la guía se reduciría en **-0,116 m³** ($48,009 \to 47,893\text{ m}^3$). El informe previo que estimó un aumento a 48,571 m³ erró al sumar la diferencia respecto a la opción manual (3,730 m³) en lugar de comparar contra los valores almacenados en base de datos. Con ancho manual de 5 5/8" (5,625" netos), el volumen de esas líneas es 3,730 m³ y 0,470 m³ (total 4,200 m³). Sumado a las 15 líneas restantes de 100 y 125 mm (43,601 m³), el total de la Guía 26270 con ancho manual es exactamente **47,801 m³** (impacto de **-0,208 m³** frente al almacenado y **-0,092 m³** frente a F2; el origen del valor previo de 47,417 m³ queda formalmente catalogado como "no reconstruido", al ser aritméticamente inconsistente con 43,601 + 3,730 = 47,331 m³).
- **Dimensiones Normalizadas en Pulgadas S2S y Orden Canónico de Resolución (AD-118):** Se elimina la tolerancia numérica heurística y se establece una señal explícita `is_s2s_inches` provista por el normalizador documental para dimensiones combinadas comerciales (ej. JCE `5/4x5.3/8x16`). Se fija el orden de resolución en 4 ramas canónicas:
  1. *Manual:* `export_width_manual_inches` prevalece si es $> 0$ y posee motivo registrado.
  2. *Tabla S2S:* Si `rough_mm` está en tabla activa, retorna S2S + sobreancho.
  3. *Documental en pulgadas S2S (`is_s2s_inches=True`):* Retorna el sobreancho exacto una sola vez, logrando $4,997\text{ m}^3$ para 231 piezas en Notas de Venta JCE.
  4. *Directo:* Aplica $\text{mm} / 25,4$ considerando el umbral `madenat.direct_width_min_mm` (170 mm) y la política `madenat.out_of_table_behavior`.
- **Extinción de la lista fija de exclusiones:** Queda formalmente extinguida y deprecada la lista `[150, 160, 170, 180, 200]` (`madenat.s2s_exclusion_widths`). La regla se decide por la presencia o ausencia en datos del modelo `lumber.width.s2s.map`.

### 9.3 Blanks en Stock y Declaración Fitosanitaria (F6)

- **Pase Directo a Stock:** Los paquetes de Blanks Clear pasan directo a stock físico y documental cuando se envían; no están sujetos a recálculos dimensionales en el ingreso.
- **Declaración Fitosanitaria:** En todo documento oficial y certificado fitosanitario, los Blanks se declaran y describen taxativamente como **"Madera Aserrada Seca"**.
- **Parámetros de Secado en Horno (Kiln Drying):** Se deben almacenar y certificar:
  - Temperatura de secado: 50–90 °C.
  - Duración del secado: 50–80 horas.
  - Fecha de secado.

### 9.4 Patios y Reglas Generales (F7)

- **Precisión Numérica:** Todos los volúmenes en el sistema se calculan y presentan con **3 decimales**.
- **Editabilidad Operativa:** El volumen y el metraje MBF calculados deben permitir modificación manual justificada por el usuario.
- **Patios Creables:** Soporte explícito en Odoo para que Operaciones cree y gestione recintos como ubicaciones internas (`stock.location`): Patio MARVAL (acopio), Patio Ferramenta (servicio de cepillado), Patio Puerto Coronel (embarque portuario).
- **Consolidación por Motonave:** Consolidación por tarja y contenedor con listados agrupados por buque/motonave (`shipping.vessel`).

---

## 10. Consulta Canónica Fijada de Integridad MD5 (AD-120 G4 / R5)

Para garantizar la inmutabilidad histórica estricta requerida por **R5** y verificar la no-regresión de datos ante intervenciones técnicas y despliegues, se fija la siguiente política canónica de integridad:

### 10.1 Política de Integridad y Pruebas Oficiales (AD-121 / Bloque 4I)
1. **Pruebas Oficiales de Integridad:** Se definen formalmente la **Consulta B** (volúmenes de negocio redondeados a 4 decimales) y la **Consulta A.2** (identificador, volumen y nombre sin marcas temporales) como las **únicas pruebas determinantes de integridad de negocio**.
2. **Rol Informativo de la Consulta con `write_date`:** La consulta histórica que incluye `write_date` pasa a ser una herramienta de auditoría **exclusivamente informativa** (aviso de fila tocada). Cualquier divergencia por actualización de marcas temporales (ej. ejecución de pruebas, recálculo interno o sesiones administrativas) no invalida la integridad del sistema mientras las Consultas B y A.2 permanezcan 100% invariantes.
3. **Regla de Inocuidad en Exploración:** Ningún script exploratorio puede invocar `registry.cursor()` ni ejecutar transacciones con `commit()`. Toda exploración debe ejecutarse obligatoriamente bajo transacción aislada con `rollback()` garantizado.
4. **Registro de Residuos en Pruebas (`TEST-LOT-EX`):** Se documenta la fila `id=49837` (`name='TEST-LOT-EX'`, `create_date='2026-10-17 18:47:05'`, `create_uid=1`, `vol_shipment_m3=NULL`) en la tabla `stock_lot` como residuo histórico de una exploración previa que ejecutó commit en `madenat_test`. En cumplimiento estricto de **R5**, esta fila **NO se elimina** y queda registrada formalmente en esta línea base.

### 10.2 Consulta B — Hash MD5 de Volúmenes Numéricos Redondeados (OFICIAL DE NEGOCIO)

La Consulta B es formalmente una verificación de integridad criptográfica basada en los volúmenes de exportación redondeados a 4 decimales:
```sql
SELECT 
    'stock_lot' as table_name,
    count(*) as row_count,
    md5(string_agg(id::text || ':' || round(coalesce(vol_shipment_m3, 0)::numeric, 4)::text, ',' ORDER BY id)) as md5_vol_shipment
FROM stock_lot
UNION ALL
SELECT 
    'madenat_guia_processing_line' as table_name,
    count(*) as row_count,
    md5(string_agg(id::text || ':' || round(coalesce(vol_shipment_m3, 0)::numeric, 4)::text, ',' ORDER BY id)) as md5_vol_shipment
FROM madenat_guia_processing_line
UNION ALL
SELECT 
    'lumber_shipment_line' as table_name,
    count(*) as row_count,
    md5(string_agg(id::text || ':' || round(coalesce(export_volume_m3, 0)::numeric, 4)::text, ',' ORDER BY id)) as md5_vol_shipment
FROM lumber_shipment_line;
```

**Hashes canónicos oficiales de Consulta B (100% Invariantes):**
- `stock_lot`: 152 filas · Hash = `5c2152193194066e5585b383ffe3673a` (MATCH EXACTO)
- `madenat_guia_processing_line`: 82 filas · Hash = `356e70066083febd59645c1212e11ece` (MATCH EXACTO)
- `lumber_shipment_line`: 11 filas · Hash = `bb5863f5850244b06b9235c2c595709b` (MATCH EXACTO)

**Dato complementario — Suma de volúmenes (Medición al 2026-10-18):**
- `stock_lot`: 152 filas · Suma = 531.2920 m³
- `madenat_guia_processing_line`: 82 filas · Suma = 295.8210 m³
- `lumber_shipment_line`: 11 filas · Suma = 53.6030 m³

### 10.3 Consulta A.2 — Hash MD5 Estructural sin Marcas Temporales (OFICIAL ESTRUCTURAL)
```sql
SELECT 
    'stock_lot' as table_name,
    count(*) as row_count,
    md5(string_agg(id::text || ':' || coalesce(vol_shipment_m3::text, 'NULL'), ',' ORDER BY id)) as hash
FROM stock_lot
UNION ALL
SELECT 
    'madenat_guia_processing_line' as table_name,
    count(*) as row_count,
    md5(string_agg(id::text || ':' || coalesce(vol_shipment_m3::text, 'NULL'), ',' ORDER BY id)) as hash
FROM madenat_guia_processing_line
UNION ALL
SELECT 
    'lumber_shipment_line' as table_name,
    count(*) as row_count,
    md5(string_agg(id::text || ':' || coalesce(export_volume_m3::text, 'NULL'), ',' ORDER BY id)) as hash
FROM lumber_shipment_line;
```

**Hashes canónicos oficiales de Consulta A.2 (100% Invariantes):**
- `stock_lot`: 152 filas · Hash = `6b1ec7d8dcd91cc6bd7ff90772759500` (MATCH EXACTO)
- `madenat_guia_processing_line`: 82 filas · Hash = `e78e0265210add0676b240bed091921f` (MATCH EXACTO)
- `lumber_shipment_line`: 11 filas · Hash = `b13357af2864a6cbeb3a386dff188a8e` (MATCH EXACTO)

### 10.4 Consulta con `write_date` — Auditoría de Marcas Temporales (INFORMATIVA)
```sql
SELECT 'stock_lot' AS tbl, COUNT(*) AS cnt,
  md5(string_agg(id::text || COALESCE(write_date::text,'') || COALESCE(name::text,''), ',' ORDER BY id)) AS hash
FROM stock_lot
UNION ALL
SELECT 'madenat_guia_processing_line', COUNT(*),
  md5(string_agg(id::text || COALESCE(write_date::text,'') || COALESCE(vol_shipment_m3::text,''), ',' ORDER BY id))
FROM madenat_guia_processing_line
UNION ALL
SELECT 'lumber_shipment_line', COUNT(*),
  md5(string_agg(id::text || COALESCE(write_date::text,'') || COALESCE(export_volume_m3::text,''), ',' ORDER BY id))
FROM lumber_shipment_line;
```

**Línea base fijada informativa:**
| Tabla | Filas | Hash MD5 Fijado | Estado Informativo |
|---|---|---|---|
| `stock_lot` | 152 | `6667a4bd9f3aeff24a8588d32da23ed2`* | Auditado al 2026-10-18 (marca temporal actualizada en id 15892) |
| `madenat_guia_processing_line` | 82 | `b43a26b6fd072ff96ed075ca1e2f585e` | Coincidente con línea base |
| `lumber_shipment_line` | 11 | `b048f9428859b4c960b83b9ddf1cc701` | Coincidente con línea base |

### 10.5 Gobernanza de Edición de la Tabla S2S (D6 / G8 / H3 — AD-121)
1. **Edición Segura:** La tabla `lumber.width.s2s.map` es editable por usuarios de los grupos `group_lumber_config_manager` y `group_madenat_auditoria`.
2. **Trazabilidad en Chatter:** Toda modificación de `rough_mm`, `s2s_decimal`, `s2s_label` o `active` genera una entrada en el chatter con usuario, fecha y valores anteriores.
3. **Validación de Coherencia Exacta (H3):** Constraint `_check_decimal_label_coherence` exige coincidencia numérica estricta entre el valor decimal y la fracción (tolerancia máxima de $\pm 0.001"$).
4. **Preservación Histórica:** Modificar un registro en esta tabla **únicamente afecta a cálculos nuevos**. Los valores almacenados históricamente en `vol_shipment_m3` y `vol_purchase_m3` permanecen inalterados.

