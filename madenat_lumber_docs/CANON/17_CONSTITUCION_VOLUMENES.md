# 17 — Constitución de Volúmenes (NOMINAL / DISPONIBLE / EXPORTACIÓN / OFICIAL)

**Versión documental:** 1.0.0
**Fecha de actualización:** 2026-10-01
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

### 2.8 Nota SV (Lote Volumen)
- El lote SV se crea con `volume_purchase_m3 = vol_shipment_m3 = volumen_m3 = official_volume_m3` y dimensiones = 0 (`intake_guia_processing.py:557-563`).
- El **stock** del lote SV se descuenta por la **salida nativa** (picking), no por la rebaja SV. La **rebaja SV** sólo mueve el ledger (`madenat.sv.operation`), **sin efectos en `stock.quant`** (`madenat_sv_operation.py:14`).

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

## 6. Hallazgos — PENDIENTES (no aplicados)

> Registrados por el informe de auditoría de volúmenes del 2026-10-01. **No se aplicó ningún cambio de código, dato ni parámetro.** Se documentan aquí para que su corrección se planifique y registre por su AD correspondiente.

| ID | Hallazgo | Evidencia (archivo:línea) | Impacto | Corrección objetivo (a decidir) |
|---|---|---|---|---|
| **F-01** | La **salida al zarpe** crea el picking con `quantity = 1` por lote (no usa el volumen). | `madenat_lumber_logistics/models/lumber_export_shipment.py:571,582` | Descuento parcial: un lote de 4,5 m³ queda en 3,5; stock sobreestimado y salida subestimada. | Mover el volumen correcto (DISPONIBLE/NOMINAL) o, según A-1, **no descontar en zarpe** y hacerlo en la rebaja. |
| **F-02** | El **asistente de asignación** calcula y valida capacidad con `volumen_m3` (nominal bruto), **no** con el DISPONIBLE (`volumen_restante_m3`/quant). | `wizards/lumber_container_lot_wizard.py:170-190,212,340-356` | Sobrestima disponibilidad (lote 2585: 4.939 vs 4.358 disponibles → +0.581 m³). | Validar con DISPONIBLE base nominal (A-3). |
| **F-03** | `_compute_vol_shipment_m3` en `stock.lot` es **huérfano**: el método existe pero el campo `vol_shipment_m3` **no declara `compute=`**. | `madenat_lumber_core/models/stock_lot.py:452` (campo) vs `:469` (método) | El export del lote es una **copia congelada**; no se recalcula si cambian dimensiones. | Decidir: cablear el compute o eliminar el método muerto. |
| **F-04** | Variable **`v_stock_real` engañosa**: contiene `item.vol_shipment_m3` (**export**), pero se lee como “stock real” y al “stock real” se le asigna `vol_purchase_m3`. | `madenat_guia_processing.py:1164,1167,1230-1240` | Riesgo de mantenimiento (no hay inversión de datos hoy). | Renombrar (`v_export_m3`) sin cambiar el mapping. |
| **F-05** | Comentario de `vol_physical_m3` (“LA VERDAD DE BODEGA… este es el nominal”) **contradice** su cálculo (mm×mm×m métrico) y el move usa `vol_purchase_m3`. | `madenat_lumber_core/models/lumber_reception.py:316-332` (comment) vs `_compute_vol_physical_strict` (`:421-440`) | Documentación interna inconsistente. | Corregir comentario o el campo, según AD. |

---

## 7. Propuestas de decisión (AD) — PROPUESTA (NO aprobadas)

> Registradas como **AD-82, AD-83 y AD-84** en `04_DECISION_LOG.md`, todas en estado **PROPUESTA — NO APROBADA**. **No constituyen regla vigente** hasta su aprobación explícita. **No autorizan cambios de código, datos ni parámetros.**

- **AD-82 (PROPUESTA) — Salida única de stock al rebajar.** Trasladar la salida nativa de stock a la acción de **rebajar contenedor/nave**; el **zarpe deja de descontar**. Objetivo: un único punto de descuento trazable, coherente con A-1. Sustituye el comportamiento de F-01.
- **AD-83 (PROPUESTA) — Módulo propio para la rebaja SV con descuento por procesados.** Extraer la rebaja SV a un módulo/ledger con **descuento explícito por procesados**, de modo que la asignación parcial a contenedores salga **exactamente por el volumen asignado** (A-2), y el stock acompañe al ledger.
- **AD-84 (PROPUESTA) — Regla de invariantes del ledger.** Fijar los **invariantes** del ledger SV y del stock: (i) `volumen_restante_m3` = Σ quant interno; (ii) `sv_available_m3` = baseline − rebajado activo; (iii) suma de rebajas por destino ≤ volumen oficial del lote; (iv) todo descuento de stock tiene una única causa trazable (rebaja, consumo o ajuste). Con guardas de concurrencia.

Detalle y redacción completa: `CANON/04_DECISION_LOG.md` (AD-82, AD-83, AD-84).

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

