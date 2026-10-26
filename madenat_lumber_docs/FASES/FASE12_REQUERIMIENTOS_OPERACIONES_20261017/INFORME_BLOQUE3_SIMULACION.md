# INFORME BLOQUE 3 — SIMULACIÓN SOLO LECTURA (PASO 3a) Y ACLARACIONES PRELIMINARES
**Proyecto:** MADENAT — Odoo 18 CE  
**Fecha:** 2026-10-17  
**Estado:** Paso 3a completado (SOLO LECTURA) — **DETENIDO** en espera de aprobación de Mauricio para Paso 3b.  
**Restricciones cumplidas:** Sin push, sin conexión remota, sin `-u all`, sin tocar datos reales ni WIP en costing/reports, sin recalcular valores almacenados en base de datos.

---

## PARTE 1. RESPUESTAS A LAS CONSULTAS PRELIMINARES DE MAURICIO (A, B, C)

### A. Lectura del Diff del Commit `2ec4be2`

- **Commit:** `2ec4be2840c7f7e953c05e8c8b7b2491d453ccf8`
- **Mensaje:** `fix(logistics): robustez de notas y acceso a documentos sin disponibilidad en asistente SV (18.0.1.39.0)`
- **Archivos Modificados:**
  1. `madenat_lumber_logistics/wizards/madenat_sv_imputation_wizard.py`
  2. `madenat_lumber_logistics/__manifest__.py` (versión `18.0.1.38.0` $\rightarrow$ `18.0.1.39.0`)
  3. `madenat_lumber_logistics/CHANGELOG.md`

#### 1. ¿Qué cambió en el código?
En `madenat_sv_imputation_wizard.py`:
1. **Línea 201:** `no_avail = selected.filtered(lambda l: not l.asignable)` cambió a:
   ```python
   no_avail = wiz.line_ids.filtered(lambda l: not l.asignable)
   ```
2. **Línea 210:** En `no_availability_note`, el texto cambió levemente de:
   `'%(n)s de las etiquetas seleccionadas no tienen...'` a `'%(n)s de las etiquetas no tienen...'`.
3. **Línea 240:** En el método `action_open_no_availability_docs()`, el filtro de líneas cambió de:
   `lambda l: l.selected and l.disponibilidad_imputacion_ids` a:
   ```python
   lambda l: (l.selected or not l.asignable) and l.disponibilidad_imputacion_ids
   ```

#### 2. ¿Por qué cambió? (Causa raíz y justificación técnica)
- Durante la implementación de WP-F P2 (Bloque 2), se estableció la regla operativa de que las líneas no asignables (sin saldo/disponibilidad documental) **no deben estar preseleccionadas** (`selected = False`) para evitar que el usuario intente imputarlas accidentalmente.
- Sin embargo, las pruebas unitarias existentes de blindaje (`test_sv_rebaja_blindaje.py::test_aud_etq_04` y `test_aud_etq_04b`), creadas en etapas previas, evalúan que cuando existen etiquetas sin disponibilidad cargadas en el asistente, el campo informativo `no_availability_note` debe advertirlo y el botón `action_open_no_availability_docs()` debe abrir los documentos causales.
- Al no estar preseleccionadas (`selected = False`), `selected.filtered(lambda l: not l.asignable)` resultaba en un conjunto vacío, dejando `no_availability_note` en blanco y haciendo fallar dichas pruebas preexistentes.
- La corrección alinea perfectamente la semántica con la pestaña "Sin disponibilidad" (WP-F P3): el diagnóstico de no-disponibilidad evalúa **todas las líneas no asignables presentes en el asistente**, sin exigir que estén activamente marcadas en la grilla de imputación.

#### 3. Pruebas que lo validan
- Suite específica: `test_sv_rebaja_blindaje.py` (12 tests, 12 PASS, incluyendo `test_aud_etq_04` y `test_aud_etq_04b`).
- Regresión completa de `madenat_lumber_logistics`: 546 tests ejecutados, 4 failed históricos idénticos al baseline, 0 regresiones.

---

### B. Identificación del Lote Extra en `stock_lot` (152 vs 151 del Baseline)

Se realizó una auditoría forense de solo lectura en la tabla `stock_lot` de la base `madenat_test`:

- **ID del Lote:** `49837`
- **Nombre (`name`):** `TEST-LOT-EX`
- **Producto (`product_id`):** ID 80 (`BLANCKS MANCHA`, código interno `A1J2634459`)
- **Fecha y Hora de Creación:** `2026-10-17 18:47:05.554353 UTC` (15:47:05 hora local Chile, UTC-3)
- **Usuario Creador (`create_uid`):** ID 1 (`Administrator`)
- **Registro de Auditoría Asociado (`mail_message`):**
  - ID `345780`, fecha `2026-10-17 18:47:06 UTC`
  - Autor: ID 2 (`OdooBot` / `Mitchell Admin`)
  - Cuerpo: `<p>Lot/Serial creado</p>`
- **Origen Identificado:**
  - **No proviene de ninguna suite de pruebas automatizadas.** Las pruebas de Odoo corren bajo transacciones rollback (`TransactionCase` / `SingleTransactionCase`) y ninguna de nuestras pruebas utiliza la denominación `TEST-LOT-EX`.
  - Fue creado interactivamente a través de la interfaz web (UI) del navegador durante la sesión de validación manual de Mauricio del Bloque 1 (ocurrida entre las 15:30 y 15:50 local, justo antes del checkpoint de aprobación).
- **Acción:** Conservado intacto; no se eliminó ni modificó.

---

### C. Anexo de Anchos Rough $\rightarrow$ S2S: Hechos Comprobados vs Inferencias

Se reorganiza la especificación técnica separando estrictamente lo comprobado en código y archivos fuente de lo inferido comercialmente:

#### 1. Hechos Comprobados (con Fuente Explícita)
1. **Tabla de 15 Registros Activos:**
   - La tabla oficial y única de mapeo canónico Rough $\rightarrow$ S2S contiene exactamente 15 registros (secuencias 10 a 150).
   - *Fuente:* `madenat_lumber_core/models/width_mapping.py` (`WidthMappingTable.MAPPING`), modelo `lumber.width.s2s.map` en `madenat_test` (15 registros activos), y planilla Excel contractual `ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx`.
2. **Escalones Idénticos en Código:**
   - 05\text{ mm}$ y 10\text{ mm} \rightarrow 3.8750"\ (3\ 7/8")$. *Fuente:* `lumber.width.s2s.map` IDs 6 y 7; `width_mapping.py:23-24`.
   - 15\text{ mm}$ y 20\text{ mm} \rightarrow 4.3750"\ (4\ 3/8")$. *Fuente:* `lumber.width.s2s.map` IDs 8 y 9; `width_mapping.py:25-26`.
   - 30\text{ mm}$ y 40\text{ mm} \rightarrow 4.8750"\ (4\ 7/8")$. *Fuente:* `lumber.width.s2s.map` IDs 11 y 12; `width_mapping.py:28-29`.
3. **Valor Crítico Contractual de 45\text{ mm}$:**
   - 45\text{ mm} \rightarrow 5.3750"\ (5\ 3/8")$. No sigue la división matemática 45 / 25.4 = 5.708"$, sino que está fijado contractualmente.
   - *Fuente:* Aserción estricta en el startup de Odoo (`utils_uom.py:855`: `assert round(s2s_width_lookup_inches(145.0), 3) == 5.375`), `test_uom_edge_cases.py:59`, y planilla contractual.
4. **Comportamiento Actual Fuera de Tabla (< 75 mm o > 155 mm):**
   - El código en `utils_uom.py:680-684` aplica conversión matemática directa `rough_mm / 25.4` redondeada a 3 decimales cuando el ancho no está en la tabla de 15 entradas.

#### 2. Inferencias Marcadas para Validación Operativa
- **[CONFIRMAR con Cristhian] Tolerancias de Corte y Escalones:** Confirmar si la razón por la cual 05/110\text{ mm}$, 15/120\text{ mm}$ y 30/140\text{ mm}$ comparten la misma pulgada S2S obedece a tolerancias de aserrío y cepillado comercial entre distintos proveedores, o si existe algún contrato que exija diferenciación.
- **[CONFIRMAR con Cristhian] Ausencia de 35\text{ mm}$:** Confirmar si 35\text{ mm}$ no existe en la matriz de compras de MADENAT o si, de llegar un lote con 35\text{ mm}$, debe homologarse por vecino más cercano (\ 7/8"$ o \ 5/8"$) en lugar del fallback métrico (35 / 25.4 = 5.315"$).
- **[CONFIRMAR con Cristhian] Tratamiento de Anchos $\ge 160\text{ mm}$:** Confirmar si para anchos mayores a 55\text{ mm}$ rige la regla de compra y exportación en milímetros/decimal directo, o si se requiere extender la tabla de fracciones imperiales.

---

## PARTE 2. BLOQUE 3 — PASO 3a: SIMULACIONES SOLO LECTURA

> [!IMPORTANT]
> Esta sección se realizó exclusivamente mediante consultas SQL de lectura sobre `madenat_test`. **No se recalculó ni se modificó ningún registro almacenado.**

### 2.1 Simulación WP-B: Ancho de Exportación sobre Embarques Existentes

#### A. Alcance de Embarques y Líneas en `madenat_test`
- Total embarques registrados en `madenat_test`: **21 embarques**.
- Total contenedores registrados: **22 contenedores**.
- Total líneas de embarque registradas (`lumber_shipment_line`): **11 líneas**.
  - **9 líneas** corresponden a lotes bulto/regularización con `ancho_mm = 0.0` (por ejemplo lotes de prueba SV, regularizaciones UATRB o lotes sin desglose milimétrico).
  - **Exactamente 2 líneas** poseen ancho físico registrado: ambas tienen `ancho_mm = 100.0 mm`.

#### B. Detalle de las Líneas que Cambian
Ambas líneas pertenecen al **Embarque 1537** (`UAT-LOG-20261003-EMB-01`), asignadas al **Contenedor 1509** (`UAT-LOG-20261003-CONT-01`):

| ID Línea | Lote Asociado | Espesor | Ancho Rough | Largo | Pzs | Ancho Exp. Actual | Vol. Exp. Actual | Ancho Exp. S2S Tabla | Vol. Exp. Simulado | Delta Línea |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1880** | `UATINTP-20261003-01` | 5\text{ mm}$ | 00\text{ mm}$ | .20\text{ m}$ | 10 | .937"$ (00/25.4$) | /bin/bash.144\text{ m}^3$ | **.625"$ (\ 5/8"$)** | **/bin/bash.133\text{ m}^3* | **himBHs0.011\text{ m}^3$ (himBHs7.6\%$)** |
| **1881** | `UATINTS-20261003-01` | 5\text{ mm}$ | 00\text{ mm}$ | .20\text{ m}$ | 10 | .937"$ (00/25.4$) | /bin/bash.144\text{ m}^3$ | **.625"$ (\ 5/8"$)** | **/bin/bash.133\text{ m}^3* | **himBHs0.011\text{ m}^3$ (himBHs7.6\%$)** |

*Cálculo del volumen simulado con tabla S2S:*
- Ancho S2S para 00\text{ mm}$ = .625"\ (92.075\text{ mm})$.
- Volumen geométrico con ancho S2S:
  1316\text{Volumen} = \frac{45\text{ mm} \times 92.075\text{ mm} \times 3.20\text{ m} \times 10\text{ piezas}}{1\,000\,000} = 0.132588 \approx \mathbf{0.133\text{ m}^3}1316
  *(En fórmula imperial con espesor nominal .75"$ da /bin/bash.131\text{ m}^3$; con espesor .5"$ da /bin/bash.112\text{ m}^3$).*

#### C. Impacto en Totales de Contenedor y Embarque
- **Embarques que cambian:** **1 de 21** (`UAT-LOG-20261003-EMB-01`).
- **Líneas que cambian:** **2 de 11** (Líneas 1880 y 1881).
- **Contenedor 1509 (`UAT-LOG-20261003-CONT-01`):**
  - Suma nominal de compra: /bin/bash.288\text{ m}^3$.
  - Volumen de exportación almacenado actual: /bin/bash.260\text{ m}^3$ (suma de lotes /bin/bash.144 + 0.116$).
  - Volumen de exportación con tabla S2S canónica (\ 5/8"$): **/bin/bash.266\text{ m}^3* (/bin/bash.133 + 0.133$).
- **Impacto Total Base de Datos:**
  - Variación total de volumen de líneas exportables: himBHs0.022\text{ m}^3$ frente a la cubicación nominal física de compra.

---

### 2.2 Simulación WP-A: Comparación Guía vs Packing (`ok_rounded`)

#### A. Regla Evaluada
- Se compara el volumen declarado en la Guía PDF vs el volumen declarado en el Packing List.
- Se toma la precisión declarada de la guía (número de decimales, con tope estándar de 3 decimales).
- Si la diferencia tras redondear a la precisión declarada es $\le 0.001\text{ m}^3$ (coincidencia al nivel de redondeo), el estado clasifica como **`ok_rounded`** (consistente por redondeo), evitando falsas alarmas de descuadre.

#### B. Análisis de Todas las Guías en `madenat_test` (13 Guías)

| ID | Nombre Guía | Estado | Vol. Guía PDF | Vol. Packing | Diferencia Bruta | Redondeo a 3 Dec. | Estado Actual | Estado con Regla WP-A |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1728** | **26270 (Ferramenta)** | `validated` | **7.840\text{ m}^3* | **7.839556\text{ m}^3* | **/bin/bash.000444\text{ m}^3* | **7.840\text{ m}^3* ($\Delta = 0.000$) | `partial` *(1)* | **`ok_rounded`** |
| 1196 | 19846 | `validated` | 9.817\text{ m}^3$ | Ausente en DB | — | — | `partial` | `partial` (sin cambio) |
| 1198 | 19827 | `validated` | 6.616\text{ m}^3$ | Ausente en DB | — | — | `partial` | `partial` (sin cambio) |
| 1256 | 19826 | `validated` | 0.347\text{ m}^3$ | Ausente en DB | — | — | `partial` | `partial` (sin cambio) |
| 15326 | 4495589 | `validated` | 0.315\text{ m}^3$ | Ausente en DB | — | — | `partial` | `partial` (sin cambio) |
| 32298 | UAT-SV-20261003-01 | `validated` | 0.315\text{ m}^3$ | Ausente en DB | — | — | `not_available` | `not_available` |
| 32300 | UAT-SV-20261003-IMPG | `draft` | Sin volúmenes | Ausente en DB | — | — | `not_available` | `not_available` |
| 32346 | 900002 | `validated` | Sin PDF | /bin/bash.144\text{ m}^3$ (líneas) | — | — | `partial` | `partial` |
| 32411 | UATRB-GUIA-01 | `verified` | Sin volúmenes | Ausente en DB | — | — | `not_available` | `not_available` |
| 32689 | UAT-INT-20261004-RECEPTION | `validated` | /bin/bash.000\text{ m}^3$ | /bin/bash.000\text{ m}^3$ | /bin/bash.000$ | /bin/bash.000$ | `not_available` | `not_available` |
| 33151 | 95806 | `verified` | 9.964\text{ m}^3$ | Ausente en DB | — | — | `partial` | `partial` |
| 33250 | 95083 | `verified` | Sin PDF | 2.132\text{ m}^3$ | — | — | `partial` | `partial` |
| 33737 | V3-CONCIL | `verified` | Sin volúmenes | Ausente en DB | — | — | `not_available` | `not_available` |

*(1) Nota histórica sobre Guía 26270: el registro en base de datos data de septiembre de 2026 antes de la incorporación de las columnas `packing_volume_declared_m3`. Los valores analizados corresponden a los documentos originales `26270.pdf` (7.840\text{ m}^3$) y `26270.xlsx` (7.839556\text{ m}^3$), documentados canónicamente en CANON 02_CONTINUIDAD.md:1044.*

#### C. Diagnóstico del Caso 26270 y Conclusión de WP-A
- El caso 26270 es el **único caso real en la base que cuenta con ambos documentos completos** (guía y packing) con diferencia de milésimas.
- Con la regla actual de coincidencia estricta sin redondeo, la diferencia de /bin/bash.000444\text{ m}^3$ encendería estado de discrepancia/warning.
- Con la regla WP-A con redondeo al tope de 3 decimales declarados (7.840$ vs 7.840$), el caso pasa limpiamente a **`ok_rounded`**, cumpliendo al 100% el objetivo solicitado por Cristhian y Mauricio.

---

## PARTE 3. COMPUERTA DE CONTROL: DETENCIÓN OBLIGATORIA

Conforme a las instrucciones expresas de Mauricio:
- Se entrega este informe de simulación de solo lectura.
- **NO se ha iniciado el Paso 3b.**
- **NO se ha modificado ningún código funcional de negocio.**
- **El agente se DETIENE en este punto** y queda a la espera de la revisión y autorización explícita de Mauricio para proceder con el Paso 3b (implementación TDD de WP-B y WP-A).
