# FASE 13 — SUBFASE 2B · Tramo 1: estado actual y verificación de datos (solo lectura)

**Proyecto:** MADENAT · Odoo 18 CE
**Fecha:** 2026-10-23
**Rama:** `fase13-2a-lectura` · HEAD `5c52d9c`
**Base de datos usada:** `madenat_test` (contenedores `odoo18_app` / `odoo18_db`)
**Alcance ejecutado:** **Paso A (detección de estado)** y **Paso V (verificación de datos, solo lectura)**.
**Código modificado:** **ninguno**. **Datos modificados:** **ninguno** (verificado por checksum, §2.7).
**Documento de origen:** no se encontró `PROMPT_2B.md` en el workspace (ver Q-1). El trabajo se ejecutó contra el enunciado resumido de los Pasos 1–5 de la Subfase 2B.

---

## 0. Resumen ejecutivo

| ID | Hallazgo | Severidad | Evidencia |
|---|---|---|---|
| **F-01** | El árbol de trabajo **no está limpio**: 8 archivos modificados + 3 sin seguimiento, todos de la vertical de **costos** (`madenat_lumber_costing`, `madenat_lumber_reports/views`), con fecha **2026-10-04**, anteriores a esta subfase y ajenos a FASE 13/2B. | Alta (riesgo de mezclar commits) | §1.1 |
| **F-02** | La fórmula vigente de **MBF usa el ancho nominal** (`details['nominal_width_inches']`), mientras **Vol. Export usa el ancho de cubicación** (`nominal + 1/8"`). Por eso el MBF **no** es `vol_shipment_m3 / 2.36` cuando el ancho está en tabla. | Alta (objeto del Paso 5) | §1.4, §2.5 |
| **F-03** | El dataset **ELENOIRE** se reproduce **exactamente** con el código vivo: 102 líneas / 97 etiquetas / 12 guías, embarque **336.555 m³**, compra **411.508 m³**, **0 de 102 líneas fuera de tolerancia 0,001**. | Informativa (base sólida) | §2.5 |
| **F-04** | Con la fórmula actual el MBF del dataset da **139.4730** contra la referencia **142.608** (`336.555 / 2,36`) → **−3.135 MBF (−2,20 %)**. La diferencia es el efecto del `+1/8"` sobre anchos de tabla. | Alta | §2.5 |
| **F-05** | El divisor `mbf_divisor = 12000` es **numéricamente equivalente** a `/2,36` (`12000 × 0,3048 = 3657,6` vs `1550.003096 × 2,36 = 3658,007`, +0,011 %). No hay que “cambiar el divisor”: hay que usar el **ancho de cubicación** en el MBF. | Media (corrige el enfoque) | §1.4 |
| **F-06** | Conviven **3 definiciones de MBF**: línea de recepción (export 1,5" × ancho nominal), lote (`volumen_m3 / 2,36`, base compra 45 mm) y línea de guía (visual × visual). Cuantificado: **+26,36 %** lote vs línea en f1550 y **0 vs 45,467** en perfil métrico. | Alta | §1.6 |
| **F-07** | **20 de 84** líneas de recepción almacenan valores que **no coinciden con la regla vigente** (+3,675 m³ de embarque, +1,452 MBF). Los lotes están **100 % alineados** (0/144). | Alta (decidir recálculo) | §1.8 |
| **F-08** | La tabla `lumber.width.s2s.map` tiene **15 filas** (75–155 mm) y **3 pares de rough distintos con la misma etiqueta** (105/110, 115/120, 130/140). El par **130/140 está confirmado por el packing del cliente**; **110 y 120 quedan sin evidencia** (si fueran errata, el volumen actual estaría −5,9 % y −5,3 %). **No verificable contra el XLSX fuente, ausente del workspace.** | Media (datos) | §2.3 |
| **F-09** | El parámetro legado `madenat.width_s2s_map` contiene **`"170": 170.0`**. Ya **no lo lee nadie** (`get_width_s2s_map` solo consulta la tabla), pero es una **trampa latente**: si se reactivara el fallback, 170 mm se resolvería como **170 pulgadas**. | Media (dato muerto peligroso) | §2.4 |
| **F-10** | `madenat.direct_width_min_mm = 170` se usa **solo** para la política `block`/`warning`; la conversión directa `mm/25,4` **sin +1/8"** se aplica a **cualquier** ancho ausente de tabla, incluidos 156–169 mm (verificado con 160 mm). | Media (aclaración normativa) | §1.5 |
| **F-11** | `ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx` **no existe** en ningún punto de `/home/viruco/dev-stack/odoo` (incluye todos los respaldos). La errata “155 → 6/5” **no se puede confirmar**; en BD 155 → **5 7/8 (5,875)**, que es el valor sano. | Media (bloquea verificación documental) | §2.2 |
| **F-12** | El perfil **métrico deja `vol_mbf = 0` por diseño** (26 líneas), pero sus lotes sí tienen MBF (`volumen_m3/2,36`: **45,467**). Los reportes mezclan ambas fuentes según el modelo consultado. | Media | §1.4, §1.6 |
| **F-13** | **Nuevo (detectado al diseñar el Paso 2, 2026-10-23).** Para la guía **40030**, `declared_volume_m3` devuelve **3322,0** —el **código** «3322 M3», no el volumen 54,518— porque el regex de cabecera del extractor captura código + unidad antes de que la cascada de detalle fije `total_volume_m3 = 54.518`. `_document_volume()` **prefiere** `declared_volume_m3`, así que la **modalidad Volúmenes** precargaría 3322 m³ y marcaría una falsa discrepancia PDF vs Excel. **No** afecta la ruta Producto (usa el parser de Excel). | Alta (dato) | §9.1 |
| **F-14** | **Nuevo (Paso 1, 2026-10-23).** `_fill_staging_table` inyecta `vol_purchase_m3 = volume_m3` (`lumber_reception.py:2198`) y, en el `create`, el compute **no** reemplaza ese valor (campo computado-almacenado con `inverse`). Una recepción recién ingestada queda con la **compra = volumen documental** (base 38,1 mm: 46,158 en 40030) hasta que una dependencia cambie; las líneas históricas están en base 45 mm porque se recomputaron después. El **Paso 2** (escribir el nominal) es también el que corrige la compra de los ingresos nuevos. | Alta | §10.3-10.4 |

**Estado de los pasos del tramo**

| Paso | Estado | Resultado |
|---|---|---|
| A — Detección de estado | ✅ Ejecutado | Repo, entorno, datos y cadena de cálculo documentados; baseline de regresión congelado |
| V — Verificación de datos | ✅ Ejecutado (1 ítem no verificable) | Tabla S2S transcrita y auditada; dataset ELENOIRE reproducido al 100 %; XLSX fuente **ausente** |
| 5 — Cambio de fórmula MBF | ⛔ **No ejecutado** (fuera de este tramo) | Insumos y riesgos en §5 |

---

## 1. Paso A — Estado actual

### 1.1 Repositorio y árbol de trabajo

| Ítem | Valor |
|---|---|
| Raíz git | `/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons` |
| Rama | `fase13-2a-lectura` |
| HEAD | `5c52d9c` — `fix(intake): mensaje de perfil con perfil elegido vacío (2A)` (2026-10-23 15:46 −0300) |
| Commits previos | `d25a32e` (docs 2A-4), `d349dd2` (tests 2A) |
| Stash | vacío |
| **Árbol de trabajo** | **NO limpio** — 8 modificados + 3 sin seguimiento |

```
 M madenat_lumber_costing/__manifest__.py
 M madenat_lumber_costing/models/__init__.py
 M madenat_lumber_costing/models/lumber_cost_distribution.py      (+377)
 M madenat_lumber_costing/models/lumber_shipment_costing.py       (+400)
 M madenat_lumber_costing/security/ir.model.access.csv
 M madenat_lumber_costing/tests/__init__.py
 M madenat_lumber_costing/views/lumber_cost_distribution_views.xml
 M madenat_lumber_reports/views/lumber_reports_menu.xml
?? madenat_lumber_costing/models/stock_lot_cost_line.py
?? madenat_lumber_costing/tests/test_shipment_costing_c2.py
?? madenat_lumber_costing/views/lumber_shipment_costing_views.xml
```

- `git diff --stat`: **830 inserciones / 31 borrados**, todos en `madenat_lumber_costing/**` y `madenat_lumber_reports/views/lumber_reports_menu.xml`.
- `mtime` de los archivos: **2026-10-04 19:56–20:14**, es decir, **19 días antes** de esta subfase. Es trabajo en curso de la vertical de **costos**, no de intake.
- **Ningún archivo de `madenat_lumber_core`, `madenat_lumber_intake`, `madenat_ingestion_engine` ni `madenat_lumber_logistics` está modificado.** La superficie que tocará el Paso 5 está limpia.
- ⚠️ Corrección al supuesto de partida: el árbol **no** estaba limpio en `5c52d9c`. Un `git add -A` arrastraría 830 líneas ajenas. **Recomendación:** commit por ruta explícita (Q-7).

### 1.2 Entorno de ejecución

| Ítem | Valor |
|---|---|
| Contenedores | `odoo18_app` (up), `odoo18_db` (up) |
| Addons en runtime | `/mnt/extra-addons` → `.../odoo-18-ce/custom_addons` |
| Base | `madenat_test` · 88 módulos cargados · registry ≈ 2,0 s |
| Shell | `odoo shell -d madenat_test --config /etc/odoo/odoo.conf --no-http` operativo |
| Python del contenedor | `openpyxl` disponible; binario `odoo` en `/usr/bin/odoo` |

Prueba de que el código cargado es el del árbol de trabajo: el log de arranque de `utils_uom` imprime la cadena canónica (`Factor 1550.003 validado`, `Ajuste S2S: +0.125"`, `Tabla S2S: delegada a modelo lumber.width.s2s.map en BD (AD-120/AD-122)`, `Fuente: Excel ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx`).

### 1.3 Inventario de datos

**Recepciones (8, todas `verified`)**

| ID | Documento | Perfil |
|---|---|---|
| 962 | 41471 | `f1550` |
| 1161 | 39519 | `f1550` |
| 7950 | 41994 | `f1550` |
| 1244 | 97183 | `f5085` |
| 1270 | 100006 | `f5085` |
| 1369 | 15183 | `metric` |
| 1371 | 41964 | `metric` |
| 7900 | 900001 | `metric` |

**Líneas de recepción (84) y lotes (152)**

| Perfil | Líneas | Vol. compra (m³) | Vol. export (m³) | MBF línea |
|---|---|---|---|---|
| `f1550` | 42 | 155,005 | 126,430 | 52,388 |
| `f5085` | 16 | 82,460 | 82,460 | 34,944 |
| `metric` | 26 | 103,019 | 103,019 | **0,000** |
| **Total** | **84** | **340,484** | **311,909** | **87,332** |

- Lotes: **152** totales · **49** con `reception_id` · **103** sin recepción (histórico/otros flujos).
- Agregados de lote: compra 594,796 m³ · embarque 521,682 m³ · `volumen_mbf` 252,033.
- Todos los lotes con recepción tienen su línea homónima (`lot_name`); **0 lotes huérfanos**. Hay **1 `lot_name` duplicado** en líneas (`0000000000446`, 2 líneas → 1 lote), que explica 50 filas de join contra 49 lotes.


### 1.4 Cadena de cálculo vigente

Fuente única de parámetros: `lumber.export.formula._resolve_for_profile()` (`madenat_lumber_core/models/lumber_export_formula.py:138`), resuelto desde el modelo persistente (semilla `data/ingestion_seed_fase3.xml`). Verificado en runtime:

```
_resolve_for_profile('f1550') ->
{'source': 'fase3_model', 'formula_kind': 's2s_imperial',
 'principal_factor': 1550.003096, 'mbf_divisor': 12000.0,
 's2s_adjustment_mode': 'per_width'}
```

| Perfil | `formula_kind` | Vol. Export | MBF | Ancho usado en MBF |
|---|---|---|---|---|
| `f1550` (S2S/Rough) | `s2s_imperial` | `(t_in × w_calc × L_m × pzas) / 1550.003096` (Decimal) | `(t_in × `**`w_nominal`**` × L_ft × pzas) / 12000` | **nominal** (sin +1/8") |
| `f5085` (Blank Clear) | `blank_clear` | `vol_documental_m3` si > 0; si no `(t_in × w_calc × L_ft × pzas) / 5085.312` | `(t_in × `**`w_calc`**` × L_ft × pzas) / 12000` | **calc** (con +1/8") |
| `metric` | `metric_direct` | `(t_mm × w_mm × L_m × pzas) / 1.000.000` | **0,0 por diseño** | — |

Código: `madenat_lumber_core/models/lumber_reception.py:666-780` (`_compute_export_values`), en particular `:746-761` (rama S2S) y `:763-765` (rama métrica).

**Consecuencia aritmética exacta (F-02/F-05).** Con `L_ft = L_m / 0,3048`:

```
MBF = Vol.Export / 2,36   ⇔   w_calc == w_nominal
```

porque `mbf_divisor × 0,3048 = 3657,6` y `principal_factor × 2,36 = 3658,007` (desvío +0,011 %). Por lo tanto:

- Anchos **fuera de tabla** (≥ 156 mm, sin +1/8"): el MBF **ya** equivale a `Vol.Export / 2,36` (±0,011 %).
- Anchos **en tabla**: el MBF queda por debajo en **`(1/8) / w_calc`**: 75 mm → **−4,55 %**, 100 mm → **−3,33 %**, 125 mm → **−2,63 %**, 145 mm → **−2,27 %**, 150 mm → **−2,17 %**.
- Blanks `f5085`: ya usa `w_calc` → coincide al 0,00 % (confirmado con datos, §1.6).

> Es decir: **no hay que “sustituir la fórmula por `/2,36`”**. Hay que usar `calc_width_inches` también en la rama MBF de `s2s_imperial`. Para `f5085` y para anchos fuera de tabla el cambio es neutro (≤0,011 %); para anchos de tabla corrige exactamente el sesgo del `+1/8"`.

### 1.5 Resolución del ancho (API única `resolve_export_width_details`)

Código: `madenat_lumber_core/models/madenat_ingestion_config.py:185-311`. Orden canónico verificado en runtime:

| # | Condición | `nominal` | `calc` | `is_out_of_table` |
|---|---|---|---|---|
| 1 | `record.export_width_manual_inches > 0` | manual | manual | False (`manual_override`) |
| 2 | `is_s2s_inches=True` (ruta de **blanks**) | `rough/25,4` | `nominal + 0,125` | False (no consulta la tabla) |
| 3 | `round(rough_mm)` ∈ tabla activa | `s2s_decimal` | `nominal + overwidth_fila (o global 0,125)` | False (`ok`) |
| 4 | resto | `rough/25,4` | **= nominal (sin +1/8")** | True (`out_of_table_confirm`) |

Salidas reales (ejecutadas contra el código vivo):

```
75   -> nominal=2.625  calc=2.75   display=2 5/8   out=False ok
100  -> nominal=3.625  calc=3.75   display=3 5/8   out=False ok
125  -> nominal=4.625  calc=4.75   display=4 5/8   out=False ok
140  -> nominal=4.875  calc=5.0    display=4 7/8   out=False ok
145  -> nominal=5.375  calc=5.5    display=5 3/8   out=False ok
150  -> nominal=5.625  calc=5.75   display=5 5/8   out=False ok
155  -> nominal=5.875  calc=6.0    display=5 7/8   out=False ok
160  -> nominal=6.2992 calc=6.2992 display=160 mm  out=True  out_of_table_confirm
170  -> nominal=6.6929 calc=6.6929 display=170 mm  out=True  out_of_table_confirm
195  -> nominal=7.6772 calc=7.6772 display=195 mm  out=True  out_of_table_confirm
```

- `madenat.s2s_overwidth_inches = 0.125`
- `madenat.direct_width_min_mm = 170.0` → **solo** umbral de la política `block`/`warning`.
- `madenat.out_of_table_behavior = warning` → no bloquea: **160 mm pasa a `mm/25,4`** emitiendo solo un `WARNING` en log (F-10). La afirmación “≥ 170 mm se usa tal cual” es una simplificación: la conversión directa aplica a **todo** ancho ausente de tabla.
- Las 15 filas de la tabla tienen `overwidth_inches = 0.0`, por lo que el sobreancho efectivo siempre cae al global de 0,125".


### 1.6 Campos que consumen Vol. Export y MBF

| Campo | Modelo · línea | Origen | Consumidores verificados |
|---|---|---|---|
| `vol_shipment_m3` | `lumber.reception.line` · `lumber_reception.py:412` | `_compute_export_values` (por perfil) | `report_helpers`; vistas de reportes de inventario |
| `vol_mbf` | `lumber.reception.line` · `:397` | idem | `report_helpers._report_get_canonical_mbf` (`:409-410`) |
| `board_feet` | `lumber.reception.line` · `:389` | `vol_mbf × 1000` | vistas de recepción |
| `vol_shipment_m3` | `stock.lot` · `stock_lot.py:489` | `_compute_vol_shipment_m3` (`:708-818`), con **salvaguarda de staging** `:730` (`bypass_staging_safeguard`) | `lumber_container.py:342,354,536,547,561`; `lumber_export_shipment.py:1530,1578,1787,1806`; `lumber_shipment_costing.py:118,140`; `stock_move.lot_vol_shipment_m3` (`stock_move.py:48`) |
| `volumen_mbf` | `stock.lot` · `stock_lot.py:983` | `volumen_m3 / 2,36` (`:1348`) o `_calculate_mbf_from_fractions` | `report_helpers` (**Ecosistema B**: `stock.quant → lot_id.volumen_mbf`, `:413-416`); `cost_per_mbf_usd`; `sale_amount_usd` |
| `vol_shipment_m3` / `vol_mbf` | `madenat.guia.processing.line` · `madenat_guia_processing.py:219/210` | `_compute_vol_shipment_m3` / `_compute_vol_mbf` | totales de guía (`:1175`) |
| `vol_shipment_m3` | `mixin_lumber_ingest.py:418` | mixin base de líneas de ingesta | recepción / guía |
| `total_vol_shipment_m3` | `lumber.container` · `lumber_container.py:121` | suma de `lot_ids.vol_shipment_m3` | contenedores y packing de exportación |

El propio `report_helpers` documenta la convivencia (**F-06**): *“Ecosistema A (lumber.reception.line): vol_mbf (fórmula geométrica de exportación) — Ecosistema B (stock.quant): lot_id.volumen_mbf (conversión aproximada m³/2.36)”*.

Medición de la divergencia (join `stock_lot.name = lumber_reception_line.lot_name`, 50 líneas / 49 lotes):

| Perfil | Filas | MBF línea (export) | MBF lote (compra/2,36) | Δ |
|---|---|---|---|---|
| `f1550` | 16 | 17,650 | 22,302 | **+26,36 %** |
| `f5085` | 8 | 18,044 | 18,044 | 0,00 % |
| `metric` | 26 | **0,000** | **45,467** | n/a (no comparable) |

Causa del +26,36 % en `f1550`: el lote divide por 2,36 un volumen de **compra** calculado con espesor nominal de **45 mm** (1,7717") y ancho rough, mientras la línea usa **1,5"** y ancho nominal S2S. Es una tercera definición de MBF, no un error de redondeo.

### 1.7 Baseline de regresión (congelado antes de cualquier cambio)

| Artefacto | Ruta | md5 |
|---|---|---|
| Líneas de recepción (84) | `custom_addons/madenat_lumber_docs/FASES/FASE13_20261023/evidencias/reception_lines.csv` | `45ad15888e36dfbc6d53ea9d54c05ab3` |
| Lotes (152) | `custom_addons/madenat_lumber_docs/FASES/FASE13_20261023/evidencias/stock_lots.csv` | `02d6284d3209f5f6e0dc70e00a8ec4e7` |

Columnas de líneas: `id, lot_name, export_calculation_rule, thickness_nominal, width_nominal, length_nominal, pieces, vol_purchase_m3, vol_shipment_m3, vol_mbf, board_feet`.
Columnas de lotes: `id, name, espesor_mm, ancho_mm, largo_m, piezas, volumen_m3, vol_shipment_m3, volumen_mbf, volume_purchase_m3, reception_id`.

Estos CSV son la referencia de “antes”. El Paso 5 debe demostrar que, tras el cambio, **solo** se mueven las filas que correspondan y que el resto conserva el mismo md5 por fila. Se recomienda comparar con **hash por fila** (no solo el md5 global) para localizar diferencias.

### 1.8 Deriva de valores almacenados (regla vigente vs valores persistidos)

Se recalculó **en caché** cada línea con `_compute_export_values()` (sin escritura; `rollback` explícito) y se comparó contra lo almacenado:

| Perfil | Líneas | Desactualizadas | Embarque almacenado → recalculado | MBF almacenado → recalculado |
|---|---|---|---|---|
| `f1550` | 42 | **4** | 126,430 → 126,671 (**+0,241**) | 52,388 → 52,388 (0,000) |
| `f5085` | 16 | **16** | 82,460 → 85,894 (**+3,434**) | 34,944 → 36,396 (**+1,452**) |
| `metric` | 26 | 0 | 103,019 → 103,019 | 0,000 → 0,000 |
| **Total** | **84** | **20** | **+3,675 m³** | **+1,452 MBF** |

IDs con deriva: `f1550` → **4644, 4648, 4649, 7704**; `f5085` → **4736–4743, 4757–4764** (16).

Ejemplo del patrón: la línea **4644** (150 mm, 4 m, 175 pzas) almacenó **3,810 m³** (= 1,5 × **5,625** × 4 × 175 / 1550,003) y la regla vigente da **3,895 m³** (= 1,5 × **5,750** × …). Son valores calculados **antes** de que el `+1/8"` entrara en esa ruta: no son datos corruptos, son históricos.

Los lotes **no** tienen deriva: el script canónico `madenat_lumber_core/scripts/recalc_h4_ad131.py --dry-run` (precedente AD-131 / Fase 5, que excluye lotes `lot_flow_type='volume'`) reporta sobre 144 lotes analizados:

```
GATE CHECK: Lotes Blanks afectados por recálculo: 0
Lotes cepillados S2S que NO coinciden y requieren recálculo: 0
Diferencia neta total: 0.000 m³
```

⚠️ Hallazgo operativo para el Paso 5: `_compute_vol_shipment_m3` **escribe** en la ruta de fallback (`if not e_mm or not a_mm or not lot.piezas: lot.vol_shipment_m3 = nominal`, `stock_lot.py:752`). Al invocarlo en masa sobre los 152 lotes, el guardián SV (`madenat_sv_operation.py:1223`, `_sv_guard_write`) lanzó `ValidationError` sobre la etiqueta **SV00000000841** (lote `lot_flow_type='volume'`). Conclusión: **cualquier recálculo masivo debe filtrar los lotes SV**, como ya hace el script AD-131. La BD quedó intacta tras el intento (§2.7).


---

## 2. Paso V — Verificación de datos (solo lectura)

### 2.1 Tabla `lumber.width.s2s.map` en BD (transcripción literal)

Consulta: `SELECT sequence, rough_mm, s2s_decimal, s2s_label, overwidth_inches, active FROM lumber_width_s2s_map ORDER BY sequence, rough_mm;`

| seq | rough (mm) | `s2s_decimal` | `s2s_label` | `calc` (+1/8") | nominal (mm) | deducción (mm) |
|---|---|---|---|---|---|---|
| 10 | 75 | 2,6250 | 2 5/8 | **2,750** | 66,675 | −8,33 |
| 20 | 85 | 2,8750 | 2 7/8 | 3,000 | 73,025 | −11,98 |
| 30 | 90 | 3,1250 | 3 1/8 | 3,250 | 79,375 | −10,63 |
| 40 | 95 | 3,3750 | 3 3/8 | 3,500 | 85,725 | −9,28 |
| 50 | 100 | 3,6250 | 3 5/8 | **3,750** | 92,075 | −7,93 |
| 60 | 105 | 3,8750 | 3 7/8 | 4,000 | 98,425 | −6,58 |
| 70 | 110 | **3,8750** | **3 7/8** | 4,000 | 98,425 | −11,58 |
| 80 | 115 | 4,3750 | 4 3/8 | 4,500 | 111,125 | −3,88 |
| 90 | 120 | **4,3750** | **4 3/8** | 4,500 | 111,125 | −8,88 |
| 100 | 125 | 4,6250 | 4 5/8 | **4,750** | 117,475 | −7,53 |
| 110 | 130 | 4,8750 | 4 7/8 | 5,000 | 123,825 | −6,18 |
| 120 | 140 | **4,8750** | **4 7/8** | 5,000 | 123,825 | −16,18 |
| 130 | 145 | 5,3750 | 5 3/8 | **5,500** | 136,525 | −8,48 |
| 140 | 150 | 5,6250 | 5 5/8 | **5,750** | 142,875 | −7,13 |
| 150 | 155 | 5,8750 | 5 7/8 | **6,000** | 149,225 | −5,78 |

- 15 filas, **todas activas**, `overwidth_inches = 0.0` en las 15 (el +1/8" proviene del global).
- No hay fila para **135** ni para **160**; el rango 156–169 mm cae en la ruta métrica directa (F-10).
- Validación empírica con el packing del cliente (§2.5): las filas **75, 100, 125, 140, 145 y 150** reproducen exactamente el volumen declarado; las filas **85, 90, 95, 105, 110, 115, 120, 130, 155** no aparecen en el dataset y quedan sin contraste documental.

### 2.2 Fuente documental: NO DISPONIBLE

Búsqueda ejecutada (sin límite de profundidad, incluye todos los respaldos del proyecto):

```
find /home/viruco/dev-stack/odoo -iname '*ANCHOS*'          -> 0 resultados
find /home/viruco/dev-stack/odoo -maxdepth 3 -iname '*2B*'  -> 0 resultados
```

Rastros del archivo **solo** en código y bitácoras, nunca el archivo:

- `madenat_lumber_core/models/utils_uom.py` (log de arranque): `Fuente: Excel ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx`.
- `madenat_lumber_core/models/lumber_reception.py:788,800`: docstrings que citan el Excel.
- `madenat_lumber_docs/WIKI/05_INCIDENTES/INC-010_thickness_visual_6_4_rango_s2s.md`.

**Consecuencia:** la instrucción “compara la tabla del ERP con `ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx`” **no se puede completar**. La tabla se auditó contra su coherencia interna y contra el packing real del cliente (§2.3 y §2.5). La errata “fila 155 → 6/5” del enunciado **no es verificable**; además `6/5` no es una fracción de pulgada válida, mientras que **5 7/8 (5,875)** sí lo es. Si el Excel realmente dice `6/5`, el valor del ERP es el correcto y el error estaría en el Excel.


### 2.3 Consistencia interna de la tabla (F-08, corregido)

La tabla es monótona no decreciente, pero **no estrictamente creciente**: hay **3 pares de rough distintos con etiqueta idéntica**.

| Par | Etiqueta compartida | Comprobación | Estado |
|---|---|---|---|
| 105 / 110 | 3 7/8 (3,875) | 110 mm = 4,331" → la etiqueta queda 0,456" por debajo | ⚠️ **Sin confirmar** |
| 115 / 120 | 4 3/8 (4,375) | 120 mm = 4,724" → 0,349" por debajo | ⚠️ **Sin confirmar** |
| 130 / 140 | 4 7/8 (4,875) | Fila 73 del packing ELENOIRE: **140 mm × 3,7 m × 175 pzas = 3,133 m³**, que exige `w_calc = 5,000` ⇒ **4 7/8 + 1/8**. El documento del cliente usa el mismo valor. | ✅ **Confirmado por el cliente** |

- Impacto si 110 debiera ser `4 1/8` (4,125): `calc` pasaría de 4,000 a 4,250 → el volumen actual estaría **−5,9 %**. Si 120 debiera ser `4 5/8` (4,625): `calc` 4,500 → 4,750 → **−5,3 %**. Son cifras **condicionales**: sin el XLSX no se puede afirmar que sean erratas.
- **Exposición actual en BD**: entre los anchos poco frecuentes que pasan por tabla, solo **90 mm** (`f1550`, 1 línea, 2,162 m³); el resto de líneas `f1550` usa 75, 100, 125, 145, 150 y 180. Los anchos **110 y 120 no se usan hoy** en `f1550` (el único 120 es `metric`, que no consulta la tabla). La fila **140** no aparece como `width_nominal` en BD, pero **sí en el dataset ELENOIRE** (1 línea, 3,133 m³).
- El resto de las filas es coherente: la deducción rough→S2S oscila entre −3,9 y −16,2 mm (mediana ≈ −8 mm), ninguna etiqueta decrece al crecer el rough y no hay saltos mayores a un escalón de 1/4".

### 2.4 Parámetros relacionados y dato latente (F-09)

| Parámetro | Valor | Uso real |
|---|---|---|
| `madenat.s2s_overwidth_inches` | `0.125` | leído por `get_s2s_overwidth_inches()` en cada resolución |
| `madenat.direct_width_min_mm` | `170.0` | **solo** umbral de política `block`/`warning`; no decide si se aplica la tabla |
| `madenat.out_of_table_behavior` | `warning` | no bloqueante |
| `madenat.nominal_tolerance` | `0.08` | mapeo de espesores |
| `madenat.blanks_nominal_map` | `[[1.0,1.0],[1.25,1.25],[1.5,1.5],[1.5625,1.5],[2.0,2.0],[2.0625,2.0],[2.5,2.5],[3.0,3.0]]` | nominal de blanks |
| `madenat.thickness_visual_ranges` | `[[37,46,1.5,"6/4"],[22,29,1.0,"4/4"],[30,36,1.25,"5/4"],[47,56,2.0,"8/4"]]` | `6/4 → 1,5"` |
| **`madenat.width_s2s_map`** | `{"75":2.625, …, "155":5.875, `**`"170":170.0`**`}` | **DATO MUERTO** |

- `get_width_s2s_map()` (`madenat_ingestion_config.py:86-111`) **solo** consulta `lumber.width.s2s.map`; ya no lee el parámetro. El JSON tiene 16 claves, incluye `"170": 170.0` y no tiene 135. Si alguien restaurara el fallback “param cuando la tabla está vacía”, **170 mm se resolvería como 170 pulgadas** (×6,7 en volumen). **Recomendación para el Paso 5:** eliminar la clave 170 o retirar el parámetro completo.
- **Segunda copia hardcodeada:** `madenat_lumber_core/models/width_mapping.py` mantiene `WidthMappingTable.MAPPING` con las mismas 15 filas, para llamadas sin `env` (búsqueda por vecino más cercano, tolerancia 2,5 mm). Se usa en `_get_excel_mapping` / `_get_trader_width_text` (`lumber_reception.py:786-814`), invocadas desde `:576` para poblar `width_visual` (texto). No altera el volumen cuando `width > 0` (la cubicación usa `rough_mm`), pero es una **tercera fuente de verdad** que el Paso 5 debe tener presente para no divergir.


### 2.5 Reproducción del dataset ELENOIRE (validación de extremo a extremo)

**Fuente:** hoja `TARJAS` del libro ELENOIRE. Layout confirmado: col 6 = `RIP S2S`, col 11 = `m³ embarque`, col 22 = `ancho rough (mm)`, col 25 = `m³ compra`. Se extrajeron **102 líneas** (12 guías, 97 etiquetas) y se enviaron al motor de cálculo vivo por la ruta de recepción (`lumber.reception.line` + `_compute_export_values`, sin persistir).

| Métrica | Declarado (Excel) | Calculado (código vivo) | Δ |
|---|---|---|---|
| Líneas | 102 | 102 | — |
| Etiquetas / guías | 97 / 12 | 97 / 12 | — |
| Piezas | 18.484 | 18.484 | — |
| Vol. embarque (m³) | **336,555** | **336,555** | **0,000** |
| Vol. compra (m³) | **411,508** | **411,508** | **0,000** |
| MBF (`336,555 / 2,36`) | **142,608** | **139,473** ← fórmula vigente | **−3,135 (−2,20 %)** |
| Líneas fuera de tolerancia 0,001 | — | **0 / 102** | ✅ |

El total analítico recalculado a mano con la tabla da **139,478**; los 0,005 de diferencia con el ORM son el redondeo `Decimal` de 4 decimales **línea a línea**, no un desvío de fórmula.

**Brecha de MBF por ancho (calculada sobre el dataset real)**

| Ancho (mm) | Líneas | Piezas | m³ embarque | MBF actual | Brecha vs `/2,36` |
|---|---|---|---|---|---|
| 75 | 3 | 975 | 9,00 | 3,6387 | **−4,55 %** |
| 100 | 19 | 4.520 | 55,41 | 22,6986 | **−3,33 %** |
| 125 | 12 | 2.400 | 39,76 | 16,4068 | **−2,63 %** |
| 140 | 1 | 175 | 3,13 | 1,2945 | **−2,50 %** |
| 145 | 51 | 8.225 | 169,89 | 70,3568 | **−2,27 %** |
| 150 | 2 | 364 | 8,10 | 3,3588 | **−2,17 %** |
| 175 | 2 | 300 | 8,00 | 3,3906 | 0,00 % |
| 180 | 6 | 900 | 24,69 | 10,4625 | 0,00 % |
| 195 | 2 | 125 | 3,33 | 1,4122 | 0,00 % |
| 200 | 4 | 500 | 15,24 | 6,4583 | 0,00 % |
| **Total** | **102** | **18.484** | **336,555** | **139,473** | **−2,20 %** |

La brecha observada coincide con `(1/8)/w_calc` al segundo decimal en **todos** los anchos de tabla, y es **exactamente 0** en los cuatro anchos fuera de tabla. Esto cierra F-02/F-05 con datos del cliente: el único origen de la diferencia es el `+1/8"` que el MBF no aplica.

**Cobertura**

- Anchos **en tabla**: 88 líneas · 16.659 piezas · **285,29 m³ (84,8 %)**.
- Anchos **fuera de tabla** (175, 180, 195, 200): 14 líneas · 1.825 piezas · **≈51,27 m³ (15,2 %)**, resueltos con `mm/25,4` **sin** sobreancho.
- El 15,2 % del embarque ya cumple `Vol.Export/2,36`; el 84,8 % restante es el que corrige el Paso 5.

### 2.6 Qué NO se pudo verificar

| Ítem | Motivo | Impacto |
|---|---|---|
| `ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx` vs tabla | Archivo inexistente en el workspace | No se cierra la auditoría documental de §2.1 → Q-2 |
| Errata “155 → 6/5” | Depende del XLSX | No confirmable; el valor en BD (5 7/8) es sano → Q-3 |
| Filas 85, 90, 95, 105, 110, 115, 120, 130, 155 | No aparecen en ELENOIRE ni en las recepciones cargadas | Auditadas solo por coherencia interna |
| Detalle de la columna 25 (m³ compra) | El Excel solo expone el agregado por línea | Se validó el agregado (411,508), no la regla unidad a unidad |

### 2.7 Garantía de no-escritura

1. Todos los cálculos se hicieron con `new()` + recomputación en caché y `env.cr.rollback()` explícito al final de cada script.
2. Para recomputar lotes fue necesario el contexto `bypass_staging_safeguard` (la salvaguarda de `stock.lot` bloquea escrituras fuera de staging); el contexto **no escribe**, solo habilita la ruta de recomputación.
3. Se tomaron **tres** volcados de la BD: baseline (antes), `recheck` (al terminar) y `recheck2` (tras el intento abortado de recálculo masivo). Los tres son **idénticos**:

```
md5  reception_lines.csv   45ad15888e36dfbc6d53ea9d54c05ab3   (baseline == recheck == recheck2)
md5  stock_lots.csv        02d6284d3209f5f6e0dc70e00a8ec4e7   (baseline == recheck == recheck2)
```

4. `git status` al cierre: idéntico al inicial (§1.1); **ningún archivo de código tocado**.

> Nota: `stock.lot` sí asignó valores **en caché** durante la recomputación; el `ValidationError` del guardián SV abortó antes del `flush`. El volcado `recheck2` prueba que **nada se persistió**.


---

## 3. Preguntas abiertas

| ID | Pregunta | Por qué bloquea | Qué necesito |
|---|---|---|---|
| **Q-1** | ¿Existe `PROMPT_2B.md`? No está en el workspace ni en el historial de esta sesión. | Trabajé contra el resumen de los Pasos 1–5; si el prompt define criterios de aceptación distintos, hay que reencuadrar. | Ruta o contenido del documento |
| **Q-2** | ¿Dónde está `ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx`? `find` sobre todo `/home/viruco/dev-stack/odoo` → 0 resultados. | Sin él no se puede cerrar la auditoría de las 15 filas ni validar 110/120. | Copia del archivo (o confirmación de que la BD es la fuente de verdad) |
| **Q-3** | ¿La errata es “155 → 6/5” o “155 → 5 7/8”? En BD está `5,875` (monótona y coherente con 150 → 5 5/8). | Si la fila 155 estuviera mal, hoy no afecta a ningún dato (no hay líneas de 155 mm), pero afectaría a la próxima importación. | Confirmación del valor correcto |
| **Q-4** | ¿Las filas **110** y **120** son correctas? Comparten etiqueta con 105 y 115 respectivamente. | Afectan −5,9 % / −5,3 % de volumen **si** son erratas. Sin uso actual en `f1550`. | Confirmación o el XLSX |
| **Q-5** | En el Paso 5, ¿el MBF debe unificarse a `Vol.Export / 2,36` en **todas** las rutas (línea, lote, guía) o solo en `lumber.reception.line`? | Cambiar solo la línea deja la divergencia del 26,36 % con los lotes (F-06). Cambiar los lotes obliga a recálculo masivo con guardián SV (F-07 nota). | Decisión de alcance |
| **Q-6** | Las **20 líneas con deriva** (§1.8), ¿se recalculan en el Paso 5 o se dejan como históricas? | Recalcular mueve +3,675 m³ / +1,452 MBF y rompe la comparación con la baseline si no se documenta. | Decisión de alcance + autorización de escritura |
| **Q-7** | El árbol tiene **830 líneas ajenas** en `madenat_lumber_costing`. ¿Se commitea 2B por ruta explícita? | Un `git add -A` mezclaría trabajo de costos con intake. | Confirmación del método de commit |
| **Q-8** | ¿Se retira el parámetro `madenat.width_s2s_map` (incluida la clave `"170": 170.0`)? | Es un dato muerto con potencial de ×6,7 si alguien reactiva el fallback. | Autorización (toca datos, no código) |
| **Q-9** | El perfil `metric` deja `vol_mbf = 0` **por diseño**. ¿Se mantiene así tras el Paso 5? | Si el Paso 5 “unifica MBF”, un `0` pasaría a `volumen/2,36` y cambiaría 26 líneas y todos los reportes métricos. | Confirmación explícita de que `metric` queda fuera |

---

## 4. Lo que NO se hizo (y por qué)

| Ítem | Motivo |
|---|---|
| Cambiar la fórmula de MBF | Es el **Paso 5**, fuera de este tramo |
| Tocar `lumber_reception.py`, `stock_lot.py`, `lumber_export_formula.py` | Instrucción explícita: solo lectura |
| Recargar módulos / actualizar el registry | Solo lectura; el código en runtime ya era el del árbol |
| Recalcular y persistir las 20 líneas desactualizadas | Requiere autorización de escritura (Q-6) |
| Modificar `lumber.width.s2s.map` | Requiere el XLSX y autorización (Q-2, Q-4) |
| Escribir tests | Dependen de la fórmula definitiva del Paso 5 |
| Corregir el parámetro `madenat.width_s2s_map` | Toca datos (Q-8) |

---

## 5. Insumos listos para el Paso 5

1. **Punto exacto del cambio:** `madenat_lumber_core/models/lumber_reception.py:746-761`, rama `s2s_imperial` de `_compute_export_values` — sustituir el ancho usado en el MBF (`details['nominal_width_inches']`) por el ancho de cubicación (`details['calc_width_inches']`), o bien calcular el MBF como `vol_shipment_m3 / 2.36` cuando el perfil no sea `metric`.
2. **Neutro donde debe serlo:** `f5085` (`blank_clear`) ya usa `w_calc`; los anchos fuera de tabla ya cumplen ±0,011 %. El cambio no debe mover ninguna de esas filas.
3. **Baseline de aceptación:** §1.7. Tras el cambio, el único delta esperado en los datos actuales son las 20 líneas de §1.8 (si se recalculan) y, en el dataset ELENOIRE, pasar de **139,473 → 142,608 MBF** con **336,555 m³ intactos**.
4. **Prueba de aceptación propuesta:** `vol_mbf == vol_shipment_m3 / 2.36` (tolerancia 0,05 %) para **todas** las líneas no métricas, incluidas las de ancho en tabla; y `vol_shipment_m3` sin cambios respecto de la baseline.
5. **Riesgos identificados:** guardián SV en recálculo masivo de lotes (§1.8); `metric` con MBF 0 (Q-9); tres definiciones de MBF (F-06, Q-5); árbol sucio (Q-7).

---

## 6. Cierre

**Paso A:** ejecutado. Repositorio, entorno, datos, cadena de cálculo, resolución de ancho y consumidores documentados; baseline de regresión congelado con md5.

**Paso V:** ejecutado con un ítem no verificable (XLSX fuente ausente). La tabla S2S quedó transcrita y auditada; el dataset ELENOIRE se reproduce al 100 % en volumen (0/102 líneas fuera de tolerancia) y se cuantificó la brecha de MBF en **−2,20 %**, con causa exacta identificada.

**Código y datos:** sin cambios; comprobado por triple volcado y md5.

**TRAMO 1 COMPLETADO — A LA ESPERA DE REVISIÓN**

---

## 7. TRAMO 2 — Paso 0 (fix 2A-1b) · ejecutado

**Alcance:** `madenat_lumber_intake` exclusivamente. **Núcleo sin tocar.**

### 7.1 Regla de Oro

| Punto | Resultado |
|---|---|
| 1 Investigar | `intake_classifier.py:35` (`TITLE_LINES = 3`); `:72` (`pdf_title ∈ STRONG_SOURCES`); `:213-215` (`_is_product_row` = «≥2 magnitudes»); `:232` (`title = clean[:TITLE_LINES]`); `:302-311` (match en fuente fuerte ⇒ `procesado`). |
| 2 Mapear | `pdf_signals` → `collect_signals:258` → `wizard._reading_signals:620` → `_reading_analysis` → `_write_reading_result:659-667`. Consumidor externo: `/tmp/fase13_2a_dryrun.py:27` (importa el módulo puro por ruta). |
| 3 Entender | La ventana de título era **posicional**: con cabeceras de 1–3 líneas la fila de producto entraba en el título y su adjetivo de artículo se promovía a **señal fuerte**. |
| 4 Solución mínima | `_is_product_row` = «≥2 magnitudes **o** unidad + cantidad» (en ambos órdenes: `3322 M3`, `M3 54,518`) + `title = [líneas no-producto][:TITLE_LINES]`. **Descartado:** subir `TITLE_LINES` (arbitrario) y añadir `cepill` a `_NOISE_RE` (ocultaría la evidencia). |
| 5 Validar | Reproducción antes/después (§7.2), matriz de casos (§7.3), **prueba en seco de 21 documentos idéntica**, 37 tests / 0 fallos, md5 de baseline intacto (§9.3). |
| 6 Documentar | README §8.1 (señales), §13 (pruebas T2A-1/6/7), §18 (decisión 2A-1b). |
| 7 Deploy | Solo carga de validación (`-u madenat_lumber_intake` con `--test-tags`); **upgrade final pendiente** al cierre del tramo. |

### 7.2 Antes / después (reproducción del caso que fallaba)

Texto del test (guía 41471, glosa «… Cepillada … de 45mm»):

| | `pdf_title` | `tipo` | Fuente del match |
|---|---|---|---|
| **Antes** | `… GUIA DE DESPACHO ELECTRONICA N 41471 3322 M3 52,63 Madera de Pino Radiata Cepillada … de 45mm 221.973,6 …` | `procesado` ❌ | `pdf_title` |
| **Después** | `SOCIEDAD FORESTAL EJEMPLO LTDA GUIA DE DESPACHO ELECTRONICA N 41471` | `producto` ✅ | — (solo advertencia desde `pdf_product`) |

```python
_UNIT_LIST = r'(?:mm|cm|mts|m3|m³|pulg|pies|ft|pcs|pzas|unid)'
_UNIT_QTY_RE = re.compile(
    r'\d+(?:[.,]\d+)?\s*%s(?!\w)|\b%s\s*\d+(?:[.,]\d+)?' % (_UNIT_LIST, _UNIT_LIST),
    re.IGNORECASE)

def _is_product_row(line):
    if len(_NUMBER_RE.findall(line)) >= 2:
        return True
    return bool(_UNIT_QTY_RE.search(line))

title = [line for line in clean if not _is_product_row(line)][:TITLE_LINES]
```

> Se excluyen las unidades de una letra (`m`, `in`) para no confundir texto corrido ni fechas; una fila con dimensión suelta («3.2 m») ya cae por la regla de ≥2 magnitudes.

### 7.3 Matriz de validación (clasificador puro, ejecutado)

| Caso | Resultado | Marca |
|---|---|---|
| `Cepillada` / `CEPILLADO` / `PINO CEP. SECO LATERAL` / `SERVICIO CEPILLADO` | `procesado`, fuente **`pdf_title`** | — |
| Guía 41471 (glosa «Cepillada … de 45mm») | `producto` | «Posible servicio …» |
| Cabeceras de **1, 2 y 3 líneas** + fila de producto | `producto` | «Posible servicio …» |
| `MADERA ASERRADA BRUTA 2 X 4 X 3.2 100 1.234` | `producto` | «Sin señal de tipo …» |
| PDF con «Servicio de Impuestos Internos» + aserrado | `producto` | «Sin señal de tipo …» |
| `SERVICIO Y TRANSPORTES SAEZ LTDA 13956258-5` | `producto` | — (fila administrativa) |
| `TOTAL M3 54,518` | fila de producto (no título) | — |

**Prueba en seco (21 documentos):** `diff` entre la salida previa y la posterior → **sin diferencias**; siguen **7 cambios**, el mismo conjunto y **0 hacia Procesado** (`/tmp/fase13_2a_dryrun.out` vs `/tmp/fase13_2a_dryrun_after2.out`).

**Tests Odoo:** `-u madenat_lumber_intake --test-tags /madenat_lumber_intake:TestIntakeWizard` → contador `37 tests`; resultado **`0 failed, 0 error(s) of 35 tests`**. Se ejecutaron `test_t2a_cepillada_en_glosa_es_senal_debil`, `test_t2a_titulo_servicio_confirmado_en_la_fuente`, `test_t2a_fila_producto_nunca_es_titulo`, `test_t2a_fila_producto_con_unidad_y_cantidad`, `test_t2a_raiz_tildes_y_abreviaturas`, `test_t2a_sin_senal_mantiene_default_y_marca`, `test_t2a_texto_legal_sii_no_clasifica_procesado`, `test_t2a_perfil_y_unidad_en_marca_de_advertencia`. Web levantada: **HTTP 200** en `/web/login`.

> Re-ejecutada sobre el **estado exactamente commiteado** (tras el último ajuste de docstring): mismo resultado (`37 tests`, `0 failed, 0 error(s)`) y md5 de baseline otra vez intactos.

### 7.4 Commits

| Commit | Contenido |
|---|---|
| `2183ed5` | `fix(intake): el titulo del PDF excluye filas de producto (2A-1b)` — `models/intake_classifier.py` |
| `20d33fa` | `test(intake): 2A-1b titulo sin filas de producto y fuente de la coincidencia` — `tests/test_intake_wizard.py` |
| `1196e59` | `docs(intake): 2A-1b en senales, pruebas y decisiones` — `README.md` |

`git add` por ruta explícita; los 830 cambios ajenos de `madenat_lumber_costing` / `madenat_lumber_reports` quedaron **fuera** de los tres commits.

---

## 8. TRAMO 2 — Paso T (diff de la tabla S2S): **NO VERIFICABLE**

| Verificación | Comando | Salida |
|---|---|---|
| Carpeta de referencias | `ls -la REFERENCIAS` | `No such file or directory` |
| XLSX de anchos | `find /home/viruco/dev-stack/odoo -iname '*ANCHOS*' \| wc -l` | `0` |
| Tabla en BD (re-lectura) | `SELECT … FROM lumber_width_s2s_map ORDER BY sequence` | **15 filas** idénticas a §2.1 (75…155, `overwidth_inches = 0.0000`, todas `active`) |

**Conclusión:** sin `ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx` no se puede emitir el diff documental. Se mantiene lo auditado en §2.3: 3 pares con etiqueta repetida (105/110, 115/120, 130/140); 130/140 confirmado por packing real y **110 / 120 pendientes** (Q-4). **Cero datos modificados.**

---

## 9. Estado del TRAMO 2

### 9.1 F-13 — `declared_volume_m3` captura el código, no el volumen

Salida real del motor para `muestras_documentos_ingreso/guias_pdf/Guia 40030.pdf`:

```
header: {'guide_number': '40030', …, 'total_volume_m3': 54.518, 'declared_volume_m3': 3322.0}
line 1: {'material_code': '3322 M3', 'description': 'Radiata Cepillada Calidad Col A de 45mm',
         'volume_m3': 54.518, …}
```

`document_extractor.py:1482` copia `header['total_volume_m3']` a `declared_volume_m3` **antes** de que la cascada de detalle lo sobrescriba con 54.518; el valor copiado es el que pescó el regex de cabecera («3322 M3» = código + unidad). `intake_wizard.py:984-999` prefiere `declared_volume_m3`; se usa en `:1020-1021` (conciliación PDF/Excel de la modalidad Volúmenes) y `:1128-1129` (precarga del volumen operativo).

**Impacto:** modalidad **Volúmenes** con esta guía → precarga 3322 m³ y «Volumen distinto (PDF=3322.000, Excel=46.158)». La ruta **Producto** no lo usa (parser de Excel) y el diseño del **Paso 2** leerá `total_volume_m3` con control de plausibilidad. **No se corrige en este tramo** (Q-10).

### 9.2 Preguntas abiertas nuevas

| ID | Pregunta | Propuesta |
|---|---|---|
| **Q-10** | F-13 (`declared_volume_m3` = 3322 en la guía 40030): ¿se corrige en 2B o pasa a 2C? | Reportarlo y **no** tocarlo; el Paso 2 usa `total_volume_m3` + control de plausibilidad. |
| **Q-11** | El Paso 2 escribe el nominal **solo** en la ruta Producto (como pide el prompt); la ruta Procesado no tiene staging de recepción. | Validar la equivalencia de ambas rutas en el **tramo 3** (criterio transversal). |
| **Q-12** | ¿Fixtures reales (`40030.xls`, `Guia 40030.pdf` en `tests/fixtures/`) o pruebas con texto sintético + patch del extractor? | Preferencia: **sintético + patch** (sin binarios en el repo). |

### 9.3 Regresión y entorno (tras Paso 0)

| Comprobación | Resultado |
|---|---|
| Líneas de recepción (84) | `45ad15888e36dfbc6d53ea9d54c05ab3` — **idéntico a la baseline** |
| Lotes (152) | `02d6284d3209f5f6e0dc70e00a8ec4e7` — **idéntico a la baseline** |
| Respaldo previo | `/tmp/madenat_test_pre_tramo2_20261023.dump` (11,7 MB) |
| Suite intake | 37 tests, 0 fallidos, 0 errores |
| Web | HTTP 200 en `/web/login` |
| Árbol git | Solo `madenat_lumber_costing` + `madenat_lumber_reports` (ajenos, F-01) |

**ESTADO: TRAMO 2 COMPLETADO (PASOS 0, T, 1 Y 2) — A LA ESPERA DE REVISIÓN**

---

## 11. TRAMO 2 — Paso 2 (espesor nominal desde el documento) · ejecutado

### 11.1 Cambio aplicado

| Archivo | Cambio |
|---|---|
| `madenat_lumber_intake/models/intake_nominal.py` | **Nuevo** (100 líneas, módulo puro): `nominal_from_text`, `nominal_from_volume`, `resolve_nominal`, `volume_is_plausible` |
| `madenat_lumber_intake/models/intake_wizard.py` | `_apply_document_nominal_thickness()`, `_declared_purchase_volume()`, `_append_reading_warning()`; llamada en `_route_producto` tras `action_process_documents()`; `import logging` + `_logger` |
| `madenat_lumber_intake/models/__init__.py` | `from . import intake_nominal` |
| `madenat_lumber_intake/tests/test_intake_nominal_thickness.py` | **Nuevo** (208 líneas, 8 casos) |
| `madenat_lumber_intake/tests/__init__.py` | Registro del test |
| `madenat_lumber_intake/README.md` | §8.3 (regla), §13 (T2B-N1..N8), §18 (decisión) |

### 11.2 Regla de Oro

| Punto | Resultado |
|---|---|
| 1 Investigar | Parser `f1550`: `t_nom = thickness_mm` (`reception_parser.py:512-513,534-536`) → 38,1 del packing. Compra con nominal (`lumber_reception.py:842-845`). Embarque con `thickness_visual` derivado del nominal (`:573-575`), y 38,1 y 45 caen en el mismo rango `6/4` (`madenat_ingestion_config.py:389`). Guía 40030: `total_volume_m3 = 54.518`, glosa «… de 45mm». |
| 2 Mapear | `_route_producto` (`intake_wizard.py:901-930`): `create` → `action_process_documents()` → staging (`reception_workflow.py:127`). Único punto donde el intake puede fijar el nominal antes de que el operador edite. |
| 3 Entender | El Excel trae el espesor **físico** y la guía el **nominal de compra**; sin nominal la compra se cubica con el físico y queda igual al embarque (F-14). |
| 4 Solución mínima | Módulo puro + escritura de `thickness_nominal` en el staging (no se toca el parser ni el núcleo). **Descartado:** hacer que `reception_parser` dependa del PDF (re-parseo, riesgo sobre históricos) y recalcular en masa (prohibido). |
| 5 Validar | 8/8 tests del paso; suite completa del intake **436/436**; md5 de baseline intacto; HTTP 200. |
| 6 Documentar | README §8.3/§13/§18 + este informe. |
| 7 Deploy | Upgrade de validación `-u madenat_lumber_intake` con `--test-tags`; **sin cambios de datos** (md5 idéntico). |

### 11.3 Resultados

| Verificación | Resultado |
|---|---|
| `TestIntakeNominalThickness` (8 casos) | **`0 failed, 0 error(s) of 8 tests`** |
| Suite completa `madenat_lumber_intake` | **`0 failed, 0 error(s) of 436 tests`** |
| Suite completa `madenat_lumber_core` (tras Paso 1) | 509/510 — el único rojo es `TestSvConcurrency`, **preexistente** (falla igual con HEAD) |
| md5 líneas / lotes | `45ad1588…` / `02d6284d…` → **sin cambios** |
| Web | **HTTP 200** |

### 11.4 Guía 40030 (ruta Producto, perfil S2S)

| Métrica | Antes | Después |
|---|---|---|
| `thickness_nominal` de las 12 líneas | 38,1 | **45,0** |
| Compra (Σ `vol_purchase_m3`) | 46,158 | **54,518** |
| Embarque (Σ `vol_shipment_m3`) | 44,713 | **44,713** (intacto) |
| `thickness_visual` | `6/4` | `6/4` |
| MBF (Σ `vol_mbf`, fórmula vigente) | 18,512 | 18,512 — el **18,946** llega con el Paso 5 |

### 11.5 Decisiones registradas

1. Tolerancias: glosa ↔ aritmética **±2 mm**; ratio de volumen declarado **1,0–1,4**.
2. Se lee `total_volume_m3`, **no** `declared_volume_m3` (F-13).
3. Sin evidencia → **no escribe** y añade marca; incluye el caso de ingreso S2S **sin PDF** (decisión aceptada por el usuario).
4. El valor del operador (`thickness_nominal != thickness`) prevalece: el método no actúa.

### 11.6 Pendiente para el tramo 3

- Aceptación transversal por **ambas rutas** (Producto y Procesado) para 40030, 19846 y ELENOIRE.
- MBF **18,946** (40030) y **142,608** (ELENOIRE) → **Paso 5**.
- Q-10 (F-13), Q-11 (ruta Procesado) y Q-12 (fixtures) siguen abiertas.

### 11.7 Commits del tramo 2

| Commit | Contenido |
|---|---|
| `2183ed5` | fix(intake): título sin filas de producto (2A-1b) |
| `20d33fa` | test(intake): 2A-1b |
| `1196e59` | docs(intake): 2A-1b |
| `d13af23` | feat(core): regla por perfil (Paso 1) + 5 tests |
| `688ea1d` | feat(intake): nominal declarado (Paso 2) + 8 tests |
| `fc3fcd8` | docs(intake): nominal (Paso 2) |

---

## 10. TRAMO 2 — Paso 1 (en curso): aplicación y primer resultado de tests

### 10.1 Cambio aplicado (aprobado por el usuario: v2)

`madenat_lumber_core/models/lumber_reception.py`:
- `_PROFILE_EXPORT_RULE` (perfil → regla) como única fuente.
- `_fill_staging_table` usa `self._export_rule_for_profile(item.get('export_rule'))`.
- `write()` recuerda la regla que derivaba el perfil **anterior** y `_sync_lines_export_rule()` propaga **solo** a las líneas auto-derivadas y **solo** en `state == 'draft'`.

`madenat_lumber_core/tests/test_reception_export_rule_profile.py` (nuevo, 151 líneas, 5 casos) + registro en `tests/__init__.py`.

### 10.2 Resultado de la suite

**Primera corrida** (`-u madenat_lumber_core --test-tags /madenat_lumber_core:TestReceptionExportRuleProfile`) → **`1 failed, 0 error(s) of 5 tests`**:

| Test | 1.ª corrida | Tras opción A |
|---|---|---|
| `test_01_fill_staging_impone_el_perfil` | ✅ | ✅ |
| `test_02_cambio_de_perfil_en_borrador_propaga` | ✅ | ✅ |
| `test_03_cambio_de_perfil_fuera_de_borrador_no_toca` | ✅ | ✅ |
| `test_05_no_pisa_reglas_ajenas_al_perfil` | ✅ | ✅ |
| `test_04_guia_40030_export_distinto_de_compra` | ❌ `AssertionError: 3.0 != 4.59 … : Compra paquete 1` | ✅ |

**Corrida final de la clase:** `0 failed, 0 error(s) of 5 tests`.

### 10.3 Diagnóstico (shell transaccional, `rollback`)

Fixture de 40030 con `_fill_staging_table` (12 paquetes):

```
PKG-01 rule=f1550 tnom=45.0 w=170 compra=3.0000 emb=3.8860 mbf=1.6470 vis=6/4
PKG-03 rule=f1550 tnom=45.0 w=150 compra=3.0000 emb=3.8950 mbf=1.6150 vis=6/4
…
TOTAL compra=36.000 emb=44.713 mbf=18.512
```

- **La regla sí se propaga**: 12/12 `f1550` (objeto del Paso 1) ✅.
- **El embarque es exacto**: `44.713` ✅.
- **La compra es el `volume_m3` inyectado por `_fill_staging_table:2198`** (`vol_purchase_m3 = vol_detectado`): al crear, el compute **no la sobrescribe** porque el campo es computado-almacenado **con `inverse`** y llega un valor explícito.
- Con los volúmenes reales del Excel el total sería **46.158** (base 38,1 mm), no 54.518: la compra nominal exige que el nominal sea 45 **y** que un cambio de dependencia dispare el recompute.

Verificación del mecanismo previsto para el Paso 2 (mismo shell, `rollback`):

```
--- ANTES (nominal = 38.1, como hoy el parser) ---   compra=19.222  emb=18.547
--- DESPUÉS de escribir nominal=45 ---
PKG-01 compra=4.5900 emb=3.8860      PKG-03 compra=4.7250 emb=3.8950
PKG-05 compra=4.5000 emb=3.6770      PKG-11 compra=4.5000 emb=3.6290
PKG-12 compra=4.3880 emb=3.4600      TOTAL compra=22.703 emb=18.547 (5 paquetes)
```

Escribir `thickness_nominal` **sí** recalcula la compra y **no** mueve el embarque: el mecanismo del Paso 2 es válido.

### 10.4 Hallazgo nuevo F-14

`_fill_staging_table` inyecta `vol_purchase_m3 = volume_m3` y, en el `create`, el compute **no** la reemplaza. Por tanto, **una recepción recién ingestada almacena como compra el volumen documental** (base 38,1 mm) hasta que una dependencia cambie (edición del operador, escritura del nominal, recálculo). Las líneas históricas de la BD están en base 45 mm porque fueron recomputadas después. Implicación: el **Paso 2 es también el que corrige la compra** de los ingresos nuevos.

### 10.5 Opciones para `test_04` — **resuelto con la opción A**

| Opción | Qué hace | Consecuencia |
|---|---|---|
| **A (aplicada)** | Fixture con los volúmenes reales del Excel (3.8862 / 4.0005 / 3.81 / 3.71475) y asserts `emb = 44.713` por paquete y `compra = 46.158` (places=2) | Refleja el comportamiento **real** de hoy y prueba lo que es del Paso 1 (Export ≠ Compra). Los 54.518 / 18.946 se validarán en el test del Paso 2 |
| B (descartada) | Escribir `thickness_nominal = 45` en el test y afirmar 54.518 | Probaría un mecanismo que aún no existe en el producto |
| C (descartada) | Forzar `lines._compute_volume_purchase()` en el test | Recompute artificial, menos representativo |

### 10.6 Regresión completa del núcleo

`-u madenat_lumber_core --test-tags /madenat_lumber_core` → **`1 failed, 0 error(s) of 510 tests`** (644 tests contados en `tests.stats`).

El único fallo es `TestSvConcurrency.test_01_dos_transacciones_no_sobreconsumen` (`test_sv_concurrency.py:265`, `AssertionError: 2 != 1`), **preexistente y ajeno al cambio**:

| Corrida | Código | Resultado |
|---|---|---|
| Suite completa | con Paso 1 | `2 != 1` |
| Clase aislada | con Paso 1 | `2 != 1` |
| Clase aislada | **HEAD (sin Paso 1)** | `2 != 1` |

Se restauró el archivo con el cambio tras la comprobación (`git checkout --` + copia de respaldo), y `lumber_reception.py` quedó con las 4 ocurrencias de `_PROFILE_EXPORT_RULE`.

### 10.7 Estado

- **Commit `d13af23`** — `feat(core): la regla de calculo sigue al perfil elegido (2B Paso 1)` — 3 archivos: modelo, test nuevo y `tests/__init__.py`. Los cambios ajenos de `costing`/`reports` quedaron fuera.
- Suite del Paso 1: **5/5 verde**; núcleo: 509/510 (el rojo es preexistente y está probado contra HEAD).
- Web arriba (**HTTP 200**); md5 de líneas y lotes `45ad1588…` / `02d6284d…` → **sin cambios en datos**.
- Pendiente: **Paso 2** (nominal desde el documento), que es el que lleva la compra de 40030 a 54.518 y el MBF a 18.946.


### 11.8 Cierre del tramo

`git status` (archivos propios del tramo): **limpio**. Los 6 commits están aplicados y los cambios ajenos de `madenat_lumber_costing` / `madenat_lumber_reports` siguen **fuera** de todos ellos.

**Caveat declarado:** la suite del núcleo conserva **1 rojo preexistente** (`TestSvConcurrency.test_01`, `2 != 1`) que se reproduce también con el código original (HEAD), por lo que no proviene de este tramo. Las suites del intake (436) y del Paso 2 (8) están **100 % en verde**.

**TRAMO 2 COMPLETADO — A LA ESPERA DE REVISIÓN**

---

## 12. TRAMO 3 — FASE 13/2D: orden del wizard, procedencia del perfil y lectura vigente

**Estado de esta sección: DIFF PUBLICADO — NO APLICADO.** No se modificó ni una línea de código de `custom_addons/`. La rama es `fase13-2a-lectura` y el árbol propio está limpio (§12.1). El objetivo de esta sección es permitir la revisión *antes* de tocar código, tal como se pidió.

### 12.1 Paso A — Estado detectado antes de diseñar

| Comprobación | Resultado | Etiqueta |
|---|---|---|
| Rama | `fase13-2a-lectura` | [VERIFICADO `git rev-parse --abbrev-ref HEAD`] |
| Árbol propio (`madenat_lumber_intake`, `madenat_ingestion_engine`, `madenat_lumber_core`) | limpio (`git status --short` sin líneas) | [VERIFICADO] |
| Cambios ajenos presentes (`madenat_lumber_costing`, `madenat_lumber_reports`) | quedan fuera de todo commit de este tramo | [VERIFICADO] |
| Módulos instalados en `madenat_test` | `madenat_lumber_intake`, `madenat_ingestion_engine`, `madenat_lumber_core` | [VERIFICADO psql `ir_module_module.state='installed'`] |
| Baseline del informe | `INFORME_FASE_2B.md` md5 `2d54473c4258851717578ab2665c62c5`, 726 líneas al abrir este tramo | [VERIFICADO `md5sum`] |
| Datos de negocio antes del tramo | 8 `lumber.reception`, 13 `madenat.guia.processing`, 112 wizards | [VERIFICADO psql] |
| Datos de negocio después de toda la experimentación | **idénticos** (8 / 13 / 112; 0 wizards con nombre `packing_%`) | [VERIFICADO psql, §12.3 cierre] |

Todos los experimentos de §12.3 se ejecutaron en `odoo shell -d madenat_test` con `env.cr.rollback()` explícito al final; la sesión de shell no confirma transacción al salir.

### 12.2 Defectos reproducidos (estado «antes»)

**D1 — La sugerencia documental pisa la elección explícita del operador (defecto principal).**

`_onchange_suggest_ingestion_profile` (`models/intake_wizard.py:270-332`) escribe `rec.ingestion_profile` sin ninguna condición de procedencia:

```python
# intake_wizard.py:306-319  (ANTES)
if detected == 'packing_metrico_aserrada':
    rec.ingestion_profile = 'metric'          # ← pisa f1550 elegido
    continue

if detected == 'packing_imperial_blanks':
    nombres = ...
    if 'blank' in nombres or 'clear' in nombres:
        rec.ingestion_profile = 'f5085'       # ← pisa f1550 elegido
    elif 's2s' in nombres:
        rec.ingestion_profile = 'f1550'
```

No existe ningún campo que registre *quién* decidió el perfil: `ingestion_profile` (`:66-75`) sólo tiene `default='metric'`. El operador que elige S2S `f1550` y luego adjunta el Excel de un packing métrico termina leyendo con `metric`, sin aviso (el desempate ambiguo sólo advierte en el caso imperial sin palabra clave, `:320-332`).

**D2 — El orden del formulario induce el error.** `views/intake_wizard_views.xml:46-51` coloca «Destino del ingreso» (con «Perfil de lectura») **antes** de «Documentos» (`:72-80`). El operador elige el perfil *antes* de subir el documento, que es exactamente la secuencia en la que el onchange lo sobrescribe.

**D3 — «Leer documento» no guarda ninguna huella de sus entradas.** `action_preview_document` (`:692-813`) escribe `state='previewed'` + campos `preview_*`, pero nada identifica *con qué datos* se leyó. `_guard_route_document` (`:845-897`) sólo comprueba presencia de documentos y `state`, no que la lectura corresponda a los datos actuales. Consecuencia: reemplazar el Excel/PDF o cambiar el perfil **después** de leer y pulsar «Continuar ingreso» deriva a Producto con la lectura vieja (probado en E2a).

**D4 — La invalidación en onchange es insuficiente por diseño.** `state`, `preview_*` son `readonly` en la vista (`:27`, `:85-89`); el cliente descarta lo que devuelve un onchange sobre campos readonly al guardar (probado en E3). Cualquier invalidación que viva sólo en un `@api.onchange` se pierde al guardar.

**D5 — «Procesado» nunca llega a `previewed`.** `action_preview_document` escribe `state='previewed'` sólo en la rama Producto (`:795-803`); la rama Procesado (`:709-733`) deja el wizard en `draft` aun habiendo leído el documento con éxito, mientras el mensaje dice «El documento fue leído correctamente». Esto impide expresar la regla «no se deriva sin lectura» como condición de estado única para las tres modalidades (ver E5 y H2).


**Trazabilidad defecto → parte del diff**

| Defecto | Parte del diff (§12.4) | Prueba que lo fija |
|---|---|---|
| D1 — la sugerencia pisa la elección | 12.4.1 (2), (4), (5) | T-2D-1, T-2D-4 |
| D2 — orden Destino antes de Documentos | 12.4.2 (2) | T-2D-1 (secuencia real del formulario) |
| D3 — lectura sin huella | 12.4.1 (2), (6), (9), (10) | T-2D-6, T-2D-7 |
| D4 — invalidación sólo en onchange | 12.4.1 (7), (11), 12.4.2 (1) | T-2D-5, T-2D-6 |
| D5 — Procesado nunca llega a `previewed` | 12.4.1 (8) | T-2D-9 |

### 12.3 Paso B — Mecanismo validado en runtime (antes de escribir el diff)

Script `/tmp/fase13_2d_mechanism.py`, ejecutado con `odoo shell -d madenat_test --no-http < …`, salida completa en `/tmp/fase13_2d_mechanism.out`. Ningún experimento se confirmó: `env.cr.rollback()` al final + recuento psql posterior.

```
patio usado: PATIO SERVICIO CEPILLADO FERRAMENTA 12564
fixture: packing_metrico_aserrada

=== E1 — bucle recursivo de onchange (servidor) ===
E1a el operador eligió f1550 y sube el Excel -> resultado: metric
    onchange(ingestion_profile) re-entró con: ['metric']
E1b procedencia 'chosen'=False -> ingestion_profile = 'metric'
E1b procedencia 'chosen'=True -> ingestion_profile = None

=== E2 — lectura vieja: ruta actual vs huella ===
state tras reemplazar el archivo: previewed | huella cambió: True
RUTA PERMITIDA con lectura vieja. receptiones creadas: 1
sólo cambia el nombre del PDF -> huella cambió: True
CON GUARDA -> BLOQUEADO: Los datos cambiaron después de leer el documento. Vuelva a leer antes de continuar.
receptiones creadas con guarda: 0
lectura vigente -> ruta permitida, state = routed | target = 14114

=== E3 — onchange que pone state='draft' en un campo readonly ===
en el Form: state = draft | preview_line_count = 0
PERSISTIDO tras Form.save implícito: state = previewed | preview_line_count = 2

=== E4 — invalidación a nivel de write() ===
write directo -> state = draft | preview_line_count = 0 | archivos conservados: True True
re-guardar el MISMO archivo -> state = previewed (no se invalida por ruido del cliente)
Form.save() -> state = draft | preview_line_count = 0
tras invalidar -> BLOQUEADO: Debe leer el documento (preview) antes de derivar a Producto.
preview normal -> state = previewed | líneas = 2
preview volume -> state = previewed

=== E5 — Procesado tras Leer documento ===
procesado -> state = draft | tipo_ingreso = procesado
guarda de ruta para procesado en state='draft': NO BLOQUEA
guarda de ruta para volume en state='draft': NO BLOQUEA

ROLLBACK OK — base sin cambios
```

Lectura de cada experimento:

| Exp. | Qué se probó | Resultado | Etiqueta |
|---|---|---|---|
| **E1a** | `Wizard.onchange(vals ∋ ingestion_profile='f1550', ['excel_file'])` con un packing métrico real | devuelve `ingestion_profile='metric'` y `_onchange_methods['ingestion_profile']` **re-entra** con `['metric']` | [VERIFICADO] |
| **E1b** | la misma llamada con la guarda emulada (`chosen=False` vs `chosen=True`) | `chosen=False` → `metric` (la sugerencia manda); `chosen=True` → la clave `ingestion_profile` **no aparece** en el valor devuelto, es decir el campo **no cambia** (se conserva `f1550`) | [VERIFICADO] |
| **E2** | `state='previewed'` → reemplazar el Excel → `action_route_document()` | **hoy:** ruta permitida, **1 recepción creada** con la lectura vieja. **Con huella:** `UserError`, **0 recepciones**; con lectura fresca la ruta vuelve a pasar (`routed`, target 14114) | [VERIFICADO] |
| **E3** | onchange que escribe `state='draft'` / `preview_line_count=0` (campos readonly en la vista) | en el `Form` se ve `draft`, pero **tras el `save` implícito vuelve a `previewed`** con `preview_line_count=2` | [VERIFICADO] |
| **E4** | invalidación dentro de `write()` (sólo cuando el valor cambia de verdad) | `write` directo → `draft` + preview limpio + **archivos conservados**; `Form.save()` → `draft`; re-guardar el mismo archivo → **no invalida**; tras invalidar, la ruta queda bloqueada por la guarda de estado; un preview normal/volume no se auto-invalida | [VERIFICADO] |
| **E5** | Procesado y Volumen que quedan en `draft` tras leer | `_guard_route_document` **no bloquea** en `draft` para esos dos flujos (hueco D5) | [VERIFICADO] |

Hallazgo lateral de E1b (importante para el diseño): **no sirve reutilizar `tipo_ingreso_auto_detectado` como bandera de procedencia**. En la primera pasada `_onchange_suggest_tipo_ingreso` la limpia (`intake_wizard.py:267`), de modo que la guarda se desactiva sola cuando corre después. Por eso el diff introduce un campo propio (`profile_origin`). [VERIFICADO en la primera ejecución de E1b: `chosen=True` seguía dando `metric`]

Hallazgo lateral de E2: cambiar **sólo el nombre** del PDF ya cambia la huella (el nombre participa del desempate imperial `:311-319`), así que también debe invalidar.

Hallazgo lateral de E3/E4: la invalidación **tiene que vivir en `write()`**; el onchange es sólo el reflejo inmediato en pantalla. [VERIFICADO]


### 12.4 DIFF EXACTO (publicado, **no aplicado**)

Convención: cada bloque indica el ancla (`archivo:línea` del estado actual) y el contenido literal a dejar. `−` = se elimina, `+` = se agrega, sin prefijo = contexto.

Archivos afectados (6):

| Archivo | Tipo de cambio |
|---|---|
| `models/intake_wizard.py` | 5 campos nuevos (`profile_suggested`, `profile_origin`, `profile_mismatch_hint`, `reading_signature`, `has_required_documents`), 2 onchange nuevos, `write()` sobrescrito, guardas en `action_preview_document` / `_guard_route_document`, huella en los 3 previews |
| `views/intake_wizard_views.xml` | reorden Modalidad → Documentos → Destino, aviso no bloqueante, `force_save` en los campos de procedencia, modificadores de botones |
| `__manifest__.py` | `version` 18.0.0.21.0 → 18.0.0.22.0 |
| `migrations/18.0.0.22.0/post-migrate.py` | **nuevo**: marca `chosen` en wizards abiertos con perfil no-default (idempotente) |
| `tests/test_intake_profile_provenance.py` | **nuevo**: 9 pruebas T-2D |
| `README.md` | sección nueva con la regla de procedencia y de lectura vigente |

Ningún otro archivo se toca. En particular **no** se modifican `_route_producto`, `_route_procesado`, `_route_granel`, `_check_profile_coherence`, `_preview_volume` (salvo la huella) ni `_onchange_intake_modality_patio` (§12.7, riesgo R6).

#### 12.4.1 `models/intake_wizard.py`

**(1) Import — `:1-5`**

```diff
 # -*- coding: utf-8 -*-
 import base64
+import hashlib
 import json
 import logging
 import re
```

**(2) Campos nuevos — insertar tras `has_reading_warning` (`:114-119`), antes de `tipo_detalle_granel` (`:121`)**

```diff
     has_reading_warning = fields.Boolean(
         string='Tiene advertencia de lectura',
         readonly=True,
         copy=False,
         default=False,
     )
+
+    # ─────────────────────────────────────────────────────────────────────
+    # Procedencia del perfil (FASE 13/2D): la sugerencia nunca pisa al operador
+    # ─────────────────────────────────────────────────────────────────────
+    profile_suggested = fields.Selection(
+        [('f1550', 'Madera Aserrada S2S'),
+         ('f5085', 'Madera Bruta — Grado Clear'),
+         ('metric', 'Madera Bruta — Sistema Métrico')],
+        string='Perfil sugerido por el documento',
+        copy=False,
+        help='Perfil que sugiere el contenido del documento. Se conserva '
+             'aparte del perfil aplicado y nunca sobrescribe una elección '
+             'explícita del operador.',
+    )
+    profile_origin = fields.Selection(
+        [('default', 'Por defecto'),
+         ('suggested', 'Sugerido por el documento'),
+         ('chosen', 'Elegido por el operador')],
+        string='Procedencia del perfil',
+        default='default',
+        required=True,
+        copy=False,
+        help='Trazabilidad de la decisión: default (valor inicial del campo), '
+             'suggested (fijado por la sugerencia documental) o chosen '
+             '(elección explícita del operador; desde ese momento la '
+             'sugerencia sólo se muestra y ya no la sobrescribe).',
+    )
+    profile_mismatch_hint = fields.Char(
+        string='Aviso de perfil',
+        compute='_compute_profile_mismatch_hint',
+        help='Aviso no bloqueante cuando el operador eligió un perfil distinto '
+             'del que sugiere el documento.',
+    )
+    reading_signature = fields.Char(
+        string='Huella de la lectura',
+        readonly=True,
+        copy=False,
+        help='Huella de los datos con los que se ejecutó la última lectura. Si '
+             'los datos cambian, la lectura deja de ser vigente y debe '
+             'repetirse antes de derivar el ingreso.',
+    )
 
     tipo_detalle_granel = fields.Selection(
```

`profile_origin` y `profile_suggested` **no** son `readonly` a nivel de modelo (deben poder guardarse) pero en la vista van `invisible="1"`: el operador nunca los edita. `reading_signature` sí es `readonly` (sólo lo escribe el servidor). `default='default'` resuelve el valor inicial sin `default_get` ni recomputo masivo.


**(3) Cómputo del aviso — insertar tras `_compute_requirements_info` (`:182-195`)**

```diff
             else:
                 rec.requirements_info = (
                     'Requisitos obligatorios: Guía/PDF, Archivo Excel y Patio '
                     'de Asignación.'
                 )
+
+    @api.depends('ingestion_profile', 'profile_suggested', 'profile_origin')
+    def _compute_profile_mismatch_hint(self):
+        """Aviso NO bloqueante cuando el operador eligió otro perfil.
+
+        La lectura se hace con la elección del operador; el aviso sólo deja
+        constancia de que el documento sugería otra cosa (FASE 13/2D).
+        """
+        labels = dict(self._fields['ingestion_profile'].selection)
+        for rec in self:
+            mismatch = (
+                rec.profile_origin == 'chosen'
+                and rec.profile_suggested
+                and rec.ingestion_profile != rec.profile_suggested
+            )
+            if mismatch:
+                rec.profile_mismatch_hint = _(
+                    'El documento sugiere «%(sug)s»; usted eligió '
+                    '«%(chosen)s». Se leerá con su elección.',
+                    sug=labels.get(rec.profile_suggested,
+                                   rec.profile_suggested),
+                    chosen=labels.get(rec.ingestion_profile,
+                                      rec.ingestion_profile),
+                )
+            else:
+                rec.profile_mismatch_hint = False
 
     # ─────────────────────────────────────────────────────────────────────
     # Estado del wizard (persistente para evidencia e idempotencia)
```


**(4) `_onchange_suggest_ingestion_profile` — reemplaza el cuerpo `:285-332`**

```diff
         Comportamiento "asistido, no determinista", igual que
         _onchange_suggest_tipo_ingreso:
           - Nunca lanza una excepción visible al usuario.
           - Nunca sobrescribe con una decisión de baja confianza; en el caso
             ambiguo, solo advierte, no cambia el valor.
+          - NUNCA sobrescribe una elección explícita del operador (FASE 13/2D):
+            si profile_origin == 'chosen', la sugerencia sólo se registra en
+            profile_suggested y se muestra como aviso no bloqueante.
         """
+        warning = None
         for rec in self:
             # Volúmenes no usa perfil de lectura: no se sugiere ni modifica.
             if rec.intake_modality == 'volume':
                 continue
             if not rec.excel_file:
                 continue
 
             try:
                 excel_bytes = base64.b64decode(rec.excel_file)
             except Exception:
                 continue
 
             try:
                 result = extract_document(
                     excel_bytes, rec.excel_filename or 'packing.xlsx'
                 )
             except (DocumentExtractionError, Exception):
                 continue
 
             detected = getattr(result, 'detected_profile_code', None)
+            suggested = None
 
             if detected == 'packing_metrico_aserrada':
-                rec.ingestion_profile = 'metric'
-                continue
+                suggested = 'metric'
 
-            if detected == 'packing_imperial_blanks':
+            elif detected == 'packing_imperial_blanks':
                 nombres = ' '.join([
                     rec.excel_filename or '',
                     rec.pdf_filename or '',
                 ]).casefold()
 
                 if 'blank' in nombres or 'clear' in nombres:
-                    rec.ingestion_profile = 'f5085'
+                    suggested = 'f5085'
                 elif 's2s' in nombres:
-                    rec.ingestion_profile = 'f1550'
+                    suggested = 'f1550'
                 else:
-                    return {
+                    # Antes: return inmediato (abandonaba el resto de
+                    # registros). Ahora: el aviso se difiere al final.
+                    warning = {
                         'warning': {
                             'title': _('Verifique el perfil de lectura antes de continuar'),
                             'message': _(
                                 'Este packing está en pulgadas. Por el nombre del archivo no '
                                 'fue posible sugerir automáticamente si corresponde a Grado '
                                 'Clear (f5085) o S2S (f1550). Seleccione el perfil correcto en '
                                 'el campo "Perfil de lectura"; esto no bloquea la lectura, solo '
                                 'asegura que se interprete correctamente.'
                             ),
                         }
                     }
+
+            # La sugerencia se registra SIEMPRE aparte (alimenta el aviso y la
+            # trazabilidad), aunque luego no se aplique.
+            rec.profile_suggested = suggested or False
+
+            # La elección del operador manda: la sugerencia no la sobrescribe.
+            if suggested and rec.profile_origin != 'chosen':
+                rec.ingestion_profile = suggested
+                rec.profile_origin = 'suggested'
+
+        if warning:
+            return warning
```


**(5) Onchange nuevo — insertar después de `:332`**

```diff
+    @api.onchange('ingestion_profile')
+    def _onchange_mark_profile_chosen(self):
+        """Marca la elección explícita del operador sin depender del orden.
+
+        Corre dentro del bucle de onchange del servidor (una escritura de
+        ingestion_profile re-entra sus propios onchange). En esa pasada
+        profile_suggested ya está fijada, así que una coincidencia NO se
+        interpreta como elección: la procedencia sigue siendo 'suggested'.
+        """
+        for rec in self:
+            if not rec.ingestion_profile:
+                continue
+            if (rec.profile_suggested
+                    and rec.ingestion_profile == rec.profile_suggested):
+                if rec.profile_origin == 'default':
+                    rec.profile_origin = 'suggested'
+                continue
+            rec.profile_origin = 'chosen'
+
```

Por qué funciona sin depender del orden de captura (validado en E1a/E1b): el servidor ejecuta *todos* los onchange del campo cambiado y, cuando la sugerencia escribe `ingestion_profile`, re-entra `_onchange_methods['ingestion_profile']`. En esa segunda pasada `profile_suggested` ya quedó fijada por la primera, por lo que `ingestion_profile == profile_suggested` es verdadero y **no** marca `chosen`. Si en cambio el operador cambia el perfil a mano, el cliente envía sólo ese campo: `profile_suggested` contiene la sugerencia anterior (o nada) y el valor no coincide → `chosen`. [VERIFICADO el bucle en E1a; la no-marca en la segunda pasada es consecuencia determinista del mismo `_cache` del registro dentro de la misma llamada — la fijan T-2D-2 y T-2D-3]


**(6) Bloque «lectura vigente» — insertar antes de `# Lectura y preview — solo Producto` (`:407-409`)**

```diff
         return None
 
+    # ─────────────────────────────────────────────────────────────────────
+    # Lectura vigente (FASE 13/2D): invalidación y huella de la lectura
+    # ─────────────────────────────────────────────────────────────────────
+    _READING_INPUT_FIELDS = (
+        'intake_modality',
+        'ingestion_profile',
+        'assignment_location_id',
+        'tipo_detalle_granel',
+        'excel_file',
+        'excel_filename',
+        'pdf_file',
+        'pdf_filename',
+    )
+
+    def _reading_signature(self):
+        """Huella estable de las entradas con las que se hizo la lectura."""
+        self.ensure_one()
+        digest = hashlib.md5()
+        for part in (
+            self.intake_modality,
+            self.ingestion_profile,
+            self.assignment_location_id.id,
+            self.tipo_detalle_granel,
+            self.excel_filename or '',
+            self.pdf_filename or '',
+            self.excel_file or '',
+            self.pdf_file or '',
+        ):
+            digest.update(str(part).encode('utf-8'))
+        return digest.hexdigest()
+
+    def _reading_inputs_changed(self, vals):
+        """True si `vals` cambia de verdad alguna entrada de la lectura."""
+        for record in self:
+            for name in self._READING_INPUT_FIELDS:
+                if name not in vals:
+                    continue
+                current = record[name]
+                if record._fields[name].type == 'many2one':
+                    current = current.id
+                if vals[name] != current:
+                    return True
+        return False
+
+    def _reading_invalidated_vals(self):
+        """Valores que devuelven el wizard a Borrador sin tocar los archivos."""
+        return {
+            'state': 'draft',
+            'error_message': False,
+            'preview_data': False,
+            'preview_line_count': 0,
+            'preview_total_volume_m3': 0.0,
+            'preview_guide_no': False,
+            'preview_warnings': False,
+            'preview_guide_date': False,
+            'preview_supplier': False,
+            'preview_oc': False,
+            'preview_origin': False,
+            'preview_exchange_rate': 0.0,
+            'preview_total_packages': 0,
+            'preview_document_lines': False,
+            'preview_has_detail': False,
+            'preview_line_volume_m3': 0.0,
+            'detalle_aplicado': 'consolidated',
+            'detalle_motivo': False,
+            'reading_warning': False,
+            'has_reading_warning': False,
+            'reading_signature': False,
+        }
+
     # ─────────────────────────────────────────────────────────────────────
     # Lectura y preview — solo Producto
     # ─────────────────────────────────────────────────────────────────────
```


**(7) `write()` sobrescrito + onchange de reflejo — insertar tras `_reading_invalidated_vals`**

```diff
+    def write(self, vals):
+        """Invalida la lectura si cambia una de sus entradas ya leídas.
+
+        La verdad vive aquí y no en el onchange: cubre RPC, `Form.save()` y
+        cualquier escritura del servidor (E3/E4). Un vals idéntico al
+        almacenado NO invalida (evita invalidaciones por ruido del cliente).
+        """
+        if vals and self._reading_inputs_changed(vals):
+            stale = self.filtered(lambda r: r.state == 'previewed')
+            if stale:
+                merged = self._reading_invalidated_vals()
+                merged.update(vals)      # lo explícito del llamador manda
+                vals = merged
+        return super().write(vals)
+
+    @api.onchange(
+        'intake_modality', 'ingestion_profile', 'assignment_location_id',
+        'tipo_detalle_granel', 'excel_file', 'excel_filename',
+        'pdf_file', 'pdf_filename',
+    )
+    def _onchange_invalidate_reading(self):
+        """Reflejo inmediato en pantalla de la invalidación.
+
+        Los campos de preview son readonly en la vista, así que el cliente no
+        los guarda (E3): la persistencia la garantiza `write()`.
+        """
+        for rec in self:
+            if rec.state == 'previewed':
+                rec.update(rec._reading_invalidated_vals())
+
```

Nota de alcance: `tipo_ingreso`, `tipo_ingreso_auto_detectado` y `classification_result` **no** son entradas de la lectura (los escribe la propia lectura en `_write_reading_result`, `:668-677`); incluirlos provocaría autoinvalidación inmediata del preview (E4, último bloque). El `merged.update(vals)` garantiza que una escritura explícita del llamador (p. ej. `state='routed'`) prevalezca sobre la invalidación.


**(8) `action_preview_document` — `:692-733`**

```diff
     def action_preview_document(self):
         self.ensure_one()
 
         # Modalidad por Volúmenes: solo PDF; Excel opcional (respaldo/detalle).
         if self.intake_modality == 'volume':
             return self._preview_volume()
 
+        # FASE 13/2D: no se lee sin los documentos requeridos. La comprobación
+        # va ANTES de clasificar para no escribir NADA si falta un documento.
+        if not self.pdf_file:
+            raise UserError(_('Guía/PDF requerido para leer el documento.'))
+        if not self.excel_file:
+            raise UserError(_('Archivo Excel requerido.'))
+
         # Modalidad normal: clasificación Producto/Procesado por contenido real,
         # al ejecutar Leer documento (no al adjuntar). El texto del PDF se
         # extrae una sola vez y se reutiliza en el enriquecimiento posterior.
         pdf_text = self._extract_pdf_text_safe()
         self._classify_normal_document(pdf_text=pdf_text)
 
-        # Normal requiere Excel para el detalle/preview.
-        if not self.excel_file:
-            raise UserError(_('Archivo Excel requerido.'))
-
         if self.tipo_ingreso == 'procesado':
             self.write({
+                'state': 'previewed',
                 'preview_data': False,
                 'preview_line_count': 0,
                 'preview_total_volume_m3': 0.0,
                 'preview_guide_no': False,
                 'preview_warnings': False,
                 'error_message': False,
+                'reading_signature': self._reading_signature(),
             })
```

El bloque `if not self.excel_file: raise` de `:705-707` queda cubierto por la guarda temprana y se retira (código inalcanzable). `test_14_normal_preview_pdf_sin_excel_bloquea` sigue lanzando `UserError` (ahora por el PDF) → **sin cambios en los tests existentes**. Ningún test comprueba `state` tras un preview de Procesado (`test_leer_documento_normal_procesado_clasifica`, `tests/test_intake_wizard.py:614-630`, sólo mira `tipo_ingreso`/`classification_result`), así que D5 se corrige sin tocar pruebas. [VERIFICADO por lectura de `tests/test_intake_wizard.py`, `test_intake_modality.py`, `test_intake_profile_coherence.py`]

**(9) Huella en los previews — `:795-803` (Producto) y `:531-562` (Volumen)**

```diff
         self.write({
             'state': 'previewed',
             'preview_data': '\n'.join(preview_lines),
             'preview_line_count': len(lines),
             'preview_total_volume_m3': total_volume,
             'preview_guide_no': (result.header or {}).get('guide_number') or False,
             'preview_warnings': warnings_text,
             'error_message': False,
+            'reading_signature': self._reading_signature(),
         })
```

```diff
         self.write({
             'state': 'previewed',
             'preview_data': False,
             'preview_line_count': line_count,
             ...
             'error_message': False,
+            'reading_signature': self._reading_signature(),
         })
```

**(10) `_guard_route_document` — insertar tras el bloque de estado (`:873-883`)**

```diff
         # Validaciones de estado según modalidad y tipo.
         if self.intake_modality == 'normal' and self.tipo_ingreso == 'producto':
             if self.state != 'previewed':
                 raise UserError(
                     _('Debe leer el documento (preview) antes de derivar '
                       'a Producto.')
                 )
         elif self.state not in ('draft', 'previewed'):
             raise UserError(
                 _('El ingreso no está en un estado derivable.')
             )
 
+        # FASE 13/2D: la lectura debe seguir vigente. Si los datos cambiaron
+        # después de leer, no se deriva (paridad con el cliente; E2).
+        if (self.state == 'previewed' and self.reading_signature
+                and self.reading_signature != self._reading_signature()):
+            raise UserError(
+                _('Los datos cambiaron después de leer el documento. '
+                  'Vuelva a leer antes de continuar.')
+            )
+
         # Guarda de coherencia de perfil (ADVERTENCIA con confirmación explícita)
```

Compatibilidad: un wizard creado directamente en `previewed` sin pasar por «Leer documento» (patrón de varios tests) tiene `reading_signature` vacío → la guarda **no** se activa. [VERIFICADO E2, tercer bloque: «lectura vigente → ruta permitida»]


**(11) Ajuste del bloque de invalidación para que el estado sea del servidor — sustituye el `if` de (7)**

```diff
         if vals and self._reading_inputs_changed(vals):
             stale = self.filtered(lambda r: r.state == 'previewed')
             if stale:
                 merged = self._reading_invalidated_vals()
-                merged.update(vals)      # lo explícito del llamador manda
+                merged.update(vals)      # lo explícito del llamador manda
+                # Invalidada la lectura, el wizard no puede quedar en
+                # 'previewed': sólo se respeta un estado explícito distinto
+                # (p. ej. 'routed'), nunca un 'previewed' viejo del cliente.
+                if merged.get('state') in (None, 'previewed'):
+                    merged['state'] = 'draft'
                 vals = merged
```

Por eso el statusbar **no** lleva `force_save`: el cliente nunca debe imponer `state`.

**(12) `has_required_documents` — campo requerido por los modificadores de la vista; insertar tras `requirements_info` (`:158-161`)**

```diff
     # Mensaje informativo de requisitos (dependiente de la modalidad).
     requirements_info = fields.Char(
         string='Requisitos del ingreso',
         compute='_compute_requirements_info',
     )
+    has_required_documents = fields.Boolean(
+        string='Documentos requeridos adjuntos',
+        compute='_compute_has_required_documents',
+        help='Verdadero si están adjuntos los documentos exigidos por la '
+             'modalidad (Volúmenes: al menos uno; normal: PDF y Excel). '
+             'Habilita «Leer documento» en el formulario.',
+    )
```

```diff
+    @api.depends('intake_modality', 'pdf_file', 'excel_file')
+    def _compute_has_required_documents(self):
+        for rec in self:
+            if rec.intake_modality == 'volume':
+                rec.has_required_documents = bool(rec.pdf_file or rec.excel_file)
+            else:
+                rec.has_required_documents = bool(rec.pdf_file and rec.excel_file)
+
     @api.depends('intake_modality')
     def _compute_requirements_info(self):
```


#### 12.4.2 `views/intake_wizard_views.xml`

**(1) Botones — `:9-27`**

```diff
                     <button
                         name="action_preview_document"
                         type="object"
                         string="Leer documento"
                         class="btn-secondary"
-                        invisible="state not in ('draft', 'error')" />
+                        invisible="state not in ('draft', 'error') or not has_required_documents" />
                     <button
                         name="action_route_document"
                         type="object"
                         string="Continuar ingreso"
                         class="btn-primary"
-                        invisible="state == 'routed'" />
+                        invisible="state != 'previewed'" />
                     <button
                         name="action_open_intake_target"
                         type="object"
                         string="Abrir registro creado"
                         class="btn-primary"
                         invisible="target_res_id == 0" />
                     <field name="state" widget="statusbar" readonly="1" />
```

`Continuar ingreso` pasa de «oculto sólo si ya se derivó» a «visible sólo con lectura hecha»: es la regla del pedido («no derivar sin lectura vigente») expresada en la UI para las tres modalidades, y sólo es posible porque D5 deja Procesado en `previewed` tras leer. La idempotencia (`state='routed'` → `_open_read_view_action`) no se pierde: el botón «Abrir registro creado» ya aparece con `target_res_id`.

**(2) Reorden — reemplaza `:35-80` entero (Modalidad → Documentos → Destino)**

Antes: `Modalidad (:35-44)` → `Destino (:46-70)` → `Documentos (:72-80)`.
Después: `Modalidad (:35-44, sin cambios)` → `Documentos` → `Destino`.

```diff
                     <group string="Modalidad de Ingesta">
                         <field name="intake_modality" widget="radio"/>
                         <div class="text-muted" invisible="intake_modality != 'normal'">
                             Ingreso normal: PDF/Guía y Excel obligatorios.
                         </div>
                         <div class="text-muted" invisible="intake_modality != 'volume'">
                             Ingreso por Volúmenes: puede adjuntar PDF, Excel o ambos.
                             Si adjunta ambos, se realiza conciliación documental.
                         </div>
                     </group>
 
+                    <group string="Documentos">
+                        <group>
+                            <field name="excel_file" filename="excel_filename"
+                                   required="intake_modality == 'normal'" />
+                            <field name="excel_filename" />
+                            <field name="pdf_file" filename="pdf_filename" required="intake_modality == 'normal'" />
+                            <field name="pdf_filename" />
+                            <field name="has_required_documents" invisible="1" />
+                        </group>
+                    </group>
+
                     <group string="Destino del ingreso">
                         <group>
                             <field name="tipo_ingreso" invisible="1"/>
+                            <field name="profile_suggested" invisible="1" force_save="1"/>
+                            <field name="profile_origin" invisible="1" force_save="1"/>
                             <field
                                 name="ingestion_profile"
                                 invisible="intake_modality == 'volume'" />
+                            <div class="text-muted" invisible="not profile_mismatch_hint">
+                                <i class="fa fa-info-circle me-1" title="Perfil elegido"/>
+                                <field name="profile_mismatch_hint" nolabel="1" readonly="1"/>
+                            </div>
                             <field
                                 name="confirm_profile_mismatch"
                                 invisible="not profile_warning_message and not confirm_profile_mismatch" />
                             ...
                             <field
                                 name="assignment_location_id" />
                             <field
                                 name="tipo_detalle_granel"
                                 invisible="intake_modality != 'volume'" />
                         </group>
                     </group>
-
-                    <group string="Documentos">
-                        <group>
-                            <field name="excel_file" filename="excel_filename"
-                                   required="intake_modality == 'normal'" />
-                            <field name="excel_filename" />
-                            <field name="pdf_file" filename="pdf_filename" required="intake_modality == 'normal'" />
-                            <field name="pdf_filename" />
-                        </group>
-                    </group>
```

Detalles que deben respetarse al aplicar:

- `has_required_documents`, `profile_suggested` y `profile_origin` van **una sola vez** en la vista (Odoo rechaza campos duplicados).
- `force_save="1"` sólo en `profile_suggested` y `profile_origin`: son campos que el onchange escribe pero el cliente no guardaría por estar invisibles; sin `force_save` se perdería la procedencia y el aviso al guardar.
- **Nunca** `force_save` en `state` ni en `reading_signature`: son del servidor y un valor viejo del cliente los pisaría (§12.4.1 (11)).
- `profile_mismatch_hint` va dentro del `div` (patrón ya usado por `requirements_info` y `reading_warning`), no como `<field>` suelto.
- Los `required="intake_modality == 'normal'"` de `excel_file`/`pdf_file` **no cambian** (contrato protegido por `tests/test_intake_wizard_view.py`). [VERIFICADO: ese test busca por *nombre de campo*, no por orden → el reorden no lo rompe]


#### 12.4.3 `__manifest__.py` y migración de datos

**(1) `__manifest__.py:4` — subir versión para que la migración se ejecute en `-u`**

```diff
-    'version': '18.0.0.21.0',
+    'version': '18.0.0.22.0',
```

**(2) `migrations/18.0.0.22.0/post-migrate.py` — archivo NUEVO**

Sigue la convención ya existente en el repo (`madenat_lumber_reports/migrations/18.0.2.2.0/`).

```python
# -*- coding: utf-8 -*-
"""FASE 13/2D — procedencia del perfil en wizards abiertos.

Los wizards creados antes de este cambio no tienen `profile_origin`. Si un
operador ya había elegido un perfil distinto del valor por defecto (`metric`)
y el registro sigue abierto, la primera sugerencia documental volvería a
pisarlo. Se marcan como `chosen` para conservar esa decisión.

Idempotente: sólo toca filas con `profile_origin = 'default'` y perfiles
distintos del default, y sólo mientras el registro no se haya derivado.
No crea, no borra y no recalcula ningún valor de volumen.
"""

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    wizards = env['madenat.lumber.intake.wizard'].search([
        ('state', 'in', ('draft', 'previewed', 'error')),
        ('profile_origin', '=', 'default'),
        ('ingestion_profile', '!=', 'metric'),
    ])
    if not wizards:
        _logger.info('FASE 13/2D: sin wizards abiertos que requieran marca de perfil.')
        return
    _logger.info('FASE 13/2D: marcando %d wizards abiertos como "chosen".', len(wizards))
    wizards.write({'profile_origin': 'chosen'})
```

Sobre el criterio: `metric` es el `default` del campo, así que un perfil distinto **sólo** pudo fijarlo un operador o una sugerencia anterior; marcar `chosen` es la opción conservadora (como mucho impide que una sugerencia posterior *cambie* un valor que ya coincide con lo sugerido, que es inocuo). Se excluyen `routed/cancelled` para no reescribir historia. [HIPÓTESIS: la cantidad de filas afectadas en `madenat_test` es pequeña; el conteo exacto se reporta al aplicar — no se asume]


#### 12.4.4 `tests/test_intake_profile_provenance.py` — archivo NUEVO (9 pruebas)

Arneses ya validados en §12.3: `Wizard.onchange(vals, ['campo'], spec)` para el cableado de onchange (E1) y `Form(...).save()` para la persistencia (E3/E4). Las fixtures reutilizan el patrón de `tests/test_intake_wizard.py` (`Workbook` en memoria → `_b64`) y el `extract_document` simulado con `patch.object(wizard_module, 'extract_document', ...)`.

| # | Escenario | Aserción |
|---|---|---|
| T-2D-1 | Operador elige `f1550` y **luego** sube el packing métrico (onchange) | `ingestion_profile == 'f1550'`, `profile_origin == 'chosen'`, `profile_suggested == 'metric'`, `profile_mismatch_hint` con aviso (**D1 corregido**) |
| T-2D-2 | Sin elección previa, sube el packing métrico | `ingestion_profile == 'metric'`, `profile_origin == 'suggested'`, `profile_suggested == 'metric'`, sin aviso |
| T-2D-3 | Sube el packing métrico (queda `suggested`) y **luego** elige `f1550` | `ingestion_profile == 'f1550'`, `profile_origin == 'chosen'` (independencia del orden — D2) |
| T-2D-4 | `Form`: elige `f1550`, sube el Excel, guarda | Persiste `f1550` / `chosen` / `profile_suggested='metric'` (force_save) |
| T-2D-5 | `Form`: lee (state `previewed`) y cambia el Excel | `form.state == 'draft'`, previews vacíos, `excel_file`/`pdf_file` intactos; tras `save()` la BD dice `draft` (**D4 corregido**, E3) |
| T-2D-6 | `write({'pdf_filename': …})` sobre un wizard `previewed` | `state == 'draft'`, `reading_signature` vacía, archivos conservados (E4) |
| T-2D-7 | `previewed` + `action_route_document()` con datos cambiados por `write()` | `UserError` y **0** registros creados (E2) |
| T-2D-8 | `action_preview_document()` sin PDF / sin Excel (normal) | `UserError`, `state` sin cambios, ningún campo de lectura escrito |
| T-2D-9 | `action_preview_document()` con Procesado | `state == 'previewed'`, `reading_signature` no vacía (**D5 corregido**); luego la ruta procede |

Nota: la lista no incluye un T-2D de Volumen porque el comportamiento de invalidación es común (el mismo `write()`); el caso queda cubierto por T-2D-6, que usa `pdf_filename`, la entrada típica de Volúmenes.

#### 12.4.5 `README.md` — sección nueva (al final)

Texto a agregar (resumen operativo, no normativo):

```markdown
## Procedencia del perfil de lectura y vigencia de la lectura (FASE 13/2D)

- El orden del formulario es **Modalidad → Documentos → Destino**. El perfil se
  decide con el documento ya adjunto.
- `Perfil de lectura` es del operador. Si lo elige explícitamente
  (`profile_origin = chosen`), la sugerencia del documento **nunca** lo
  sobrescribe: sólo se registra en `Perfil sugerido por el documento` y se
  muestra un aviso no bloqueante si no coinciden.
- Si nadie eligió (`default`), la sugerencia fija el perfil y la procedencia
  queda como `suggested`.
- Cambiar modalidad, perfil, patio, nivel de detalle, Excel o PDF **invalida**
  la lectura: el wizard vuelve a Borrador, se limpian los totales de preview y
  los archivos se conservan. Hay que volver a «Leer documento».
- «Continuar ingreso» sólo está disponible con la lectura hecha
  (`state = previewed`) y vigente; el servidor lo valida también por RPC
  (huella `reading_signature`).
```


### 12.5 Regla de Oro aplicada

| Punto | Resultado |
|---|---|
| 1 Investigar | `_onchange_suggest_ingestion_profile` (`intake_wizard.py:270-332`) escribe `ingestion_profile` sin condición de procedencia; no existe campo de procedencia; la vista pone «Destino» antes de «Documentos» (`intake_wizard_views.xml:46-80`); `action_preview_document` no deja huella de datos (`:692-813`); `state`/`preview_*` son readonly en la vista (`:27`, `:85-89`). |
| 2 Mapear | Onchange (servidor y `Form`) → `_apply_onchange_methods` con reentrada del campo escrito; `write()` → única puerta común de RPC + `Form.save()`; `_guard_route_document` (`:845-897`) → único punto previo a `_route_producto/_route_procesado/_route_granel`. |
| 3 Entender | El defecto no es «el onchange está mal escrito» sino que **nadie distingue una decisión del operador de una sugerencia**, y que la invalidación se intentaba en la capa equivocada (onchange sobre campos readonly). |
| 4 Solución mínima | 4 campos de control (`profile_origin`, `profile_suggested`, `profile_mismatch_hint`, `reading_signature`) + 1 campo auxiliar de vista (`has_required_documents`) + 1 guarda en la sugerencia + invalidación en `write()` + reorden de la vista + huella en la guarda de ruta. **Descartado:** un flag `manual_override` booleano (no distingue default de suggested); reutilizar `tipo_ingreso_auto_detectado` (**probado: se limpia solo**, E1b); bloquear la derivación por `profile_origin='chosen'` (contradice «no bloqueante»); recomputar en masa (`default_get`/migración masiva prohibidos); cambiar `_onchange_intake_modality_patio` (riesgo R6, fuera de alcance); meter la invalidación en `action_route_document` (llegaría tarde: el operador ya guardó datos viejos). |
| 5 Validar | Mecanismo E1-E5 **ejecutado** (§12.3) + plan de verificación §12.6 (T-2D-1…9, suite completa del intake, núcleo, md5, HTTP 200) — **pendiente de ejecutar porque el diff no está aplicado**. |
| 6 Documentar | §12 de este informe + README (12.4.5) + docstrings en cada método nuevo. |
| 7 Deploy | **No aplicado.** Al aprobarse: `-u madenat_lumber_intake` con `--test-tags` en `madenat_test`, post-migrate idempotente, `git status` propio y md5 de baseline antes/después. |

### 12.6 Verificación acordada para el momento de aplicar (no ejecutada)

1. `git status --short custom_addons/madenat_lumber_intake` → sólo los 6 archivos listados; `git diff --stat` coherente con §12.4.
2. `docker exec odoo18_app odoo -d madenat_test -u madenat_lumber_intake --stop-after-init --test-tags /madenat_lumber_intake` con `--log-level=test`.
3. Recuento de la migración en el log: `FASE 13/2D: marcando N wizards…` y `SELECT count(*) … profile_origin='chosen'` antes/después.
4. Suite dirigida: `tests/test_intake_profile_provenance.py` (9/9), `test_intake_wizard.py`, `test_intake_modality.py`, `test_intake_profile_coherence.py`, `test_intake_wizard_view.py`, `test_granel_route.py`, `test_volume_operational.py`, `test_volume_extraction.py`.
5. Suite completa del intake (baseline conocida: **436**) y núcleo (baseline **509/510**, el rojo es preexistente `TestSvConcurrency.test_01`).
6. Datos: md5 de líneas/lotes `45ad1588…` / `02d6284d…` **idénticos**; `lumber_reception` 8, `madenat.guia.processing` 13.
7. Web arriba (**HTTP 200**) y recorrido manual: elegir `f1550` → subir packing métrico → verificar que el perfil **no** cambia y que aparece el aviso; cambiar el Excel → verificar que vuelve a Borrador.
8. Criterio de reversión: si (4) o (5) no quedan verdes, `git checkout --` de los 6 archivos y `-u` de retorno; la migración no se deshace sola, pero es un único `UPDATE` idempotente sobre wizards abiertos (§12.7, R2).


### 12.7 Riesgos identificados (con su mitigación en el diff)

| # | Riesgo | Por qué ocurriría | Mitigación publicada | Etiqueta |
|---|---|---|---|---|
| **R1** | El onchange de marcado convierte en `chosen` un perfil que puso la sugerencia | Si el orden de ejecución dejara `profile_suggested` vacío en la segunda pasada | `profile_suggested` se fija **antes** de escribir `ingestion_profile`, en la misma pasada; la comparación ignora coincidencias. Fijado por T-2D-2 | [HIPÓTESIS acotada, verificable con T-2D-2] |
| **R2** | La migración marca de más | Wizards abiertos con perfil no-`metric` que en realidad fueron sugeridos | Marcar `chosen` sólo puede evitar una sobrescritura futura; no altera el perfil aplicado ni la lectura. Reversible con un `UPDATE` inverso | [VERIFICADO por lectura: la migración no toca `ingestion_profile`] |
| **R3** | La invalidación en `write()` dispara en escrituras legítimas (p. ej. `routed`) | Si `vals` incluyera una entrada de lectura | Sólo invalida si el valor **difiere** del almacenado, y con `state in ('draft','error'/'routed')` no hay nada que invalidar; `merged['state']` respeta un estado explícito distinto de `previewed` | [VERIFICADO E4: 3 escenarios + re-guardado idéntico] |
| **R4** | El cliente envía un `state='previewed'` viejo al guardar y resucita la lectura | `force_save` en el statusbar | **No** se pone `force_save` en `state`; el servidor impone `draft` | [VERIFICADO por diseño + E4] |
| **R5** | `Continuar ingreso` desaparece en un flujo hoy válido | Procesado/Volumen derivaban desde `draft` | Se corrige D5 (Procesado → `previewed` tras leer) y la guarda de servidor sigue aceptando `draft` por RPC | [VERIFICADO E5 + lectura de `_guard_route_document`] |
| **R6** | Cambiar la modalidad reasigna el patio (`_onchange_intake_modality_patio:174-180`) y el operador pierde su elección | Comportamiento actual | **No se toca** en este tramo (fuera de alcance); ahora ese cambio además invalida la lectura, que es lo correcto. Se propone como 2D-2 (§12.8, H5) | [VERIFICADO por lectura] |
| **R7** | Coste de la huella en cada guardado | `_reading_signature()` hashea el binario del Excel/PDF | Sólo se calcula si hay `state='previewed'` y un campo de lectura presente; el binario ya está en memoria (`_cache`) | [HIPÓTESIS: no se midió; el wizard es de un registro y el archivo típico < 1 MB] |
| **R8** | Tests existentes que crean el wizard directamente en `previewed` | Nueva guarda de huella | `reading_signature` vacía ⇒ la guarda no se activa (compatibilidad explícita) | [VERIFICADO E2, tercer bloque] |

Ningún riesgo toca el núcleo (`madenat_lumber_core`, `madenat_ingestion_engine`): el diff se limita a `madenat_lumber_intake`.

### 12.8 Preguntas abiertas (bloquean o condicionan la aplicación)

| # | Pregunta | Por qué importa | Opciones |
|---|---|---|---|
| **H1** | **`.clinerules` y `PROMPT_2D.md` no existen** | El pedido los cita como fuente; no hay archivo que los contenga en `/home/viruco/dev-stack` ni en `/home/viruco` (búsqueda `find` sin resultados) | (a) el mensaje del operador es la fuente de verdad — es lo que se usó; (b) aportar los archivos y se re-verifica el diff contra ellos |
| **H2** | Volumen/Procesado: ¿seguir aceptando la derivación desde `draft` por RPC? | La UI ya no lo permite, pero la guarda de servidor sí (E5) | (a) dejarlo (compatibilidad con integraciones); (b) endurecer a `previewed` para las tres modalidades (más coherente, puede romper pruebas de volumen que derivan sin leer) |
| **H3** | ¿Se aplica la migración `post-migrate` (marca `chosen` en wizards abiertos)? | Evita reintroducir el defecto en wizards ya abiertos | (a) sí, con `post-migrate` idempotente (§12.4.3); (b) no, cero migración, aceptando la ventana de una sesión |
| **H4** | Limitación conocida: si el operador elige **exactamente** el perfil ya sugerido, el cliente no envía el campo y la procedencia queda `suggested` | Un documento distinto posterior podría cambiarlo | (a) aceptarlo (el valor ya coincidía); (b) forzar `chosen` con un `Selection` que no dispare onchange — no existe en Odoo; (c) añadir un botón «Confirmar perfil» explícito |
| **H5** | `_onchange_intake_modality_patio` sobrescribe el patio elegido al cambiar la modalidad | Misma familia de defecto que el perfil, pero no está en el pedido | (a) dejarlo para 2D-2; (b) incluirlo ahora (1 condición: `if not self.assignment_location_id`) |
| **H6** | ¿«Leer documento» debe exigir también el patio? | Hoy la guarda de lectura sólo comprueba documentos; el patio se exige al derivar | (a) dejarlo como está; (b) exigirlo también al leer (`has_required_documents` ya está calculado) |

### 12.9 Garantía de no-escritura de este tramo

- Código: **cero** líneas modificadas por este tramo en `custom_addons/`. [VERIFICADO `git status --short` sobre `madenat_lumber_intake`, `madenat_lumber_core`, `madenat_ingestion_engine`: vacío para los tres]
- Nota de transparencia: el árbol de trabajo **ya venía sucio** por trabajo ajeno a este tramo — `madenat_lumber_costing/*` (8 archivos, 830 inserciones) y `madenat_lumber_reports/views/lumber_reports_menu.xml` (inactivación P2-2 del menú 376). Nada de eso se tocó aquí y el diff de §12.4 no depende de ello.
- Base de datos: **cero** filas nuevas o modificadas. [VERIFICADO psql antes/después de E1-E5: 112 wizards, 8 recepciones, 13 guías; 0 wizards `packing_%`]
- Los únicos artefactos escritos son el script de reproducción (`/tmp/fase13_2d_repro.py`), el de mecanismo (`/tmp/fase13_2d_mechanism.py` + `.out`) y este informe.
- Toda la experimentación corrió en `odoo shell` con `env.cr.rollback()` explícito.
- Este informe cierra en **1611 líneas**; su md5 se consigna en el mensaje de entrega (no se puede autocontener sin invalidarse).

**FASE 2D — DIFF PUBLICADO, A LA ESPERA DE APROBACIÓN**


---

## 13. FASE 2D — EJECUCIÓN, VERIFICACIÓN Y CIERRE (2026-10-26)

### 13.1 Decisiones aplicadas

| ID | Decisión aprobada | Resultado |
|---|---|---|
| **H1** | Crear `.clinerules/madenat-regla-de-oro.md` y guardar el prompt | [VERIFICADO — ambos archivos creados; la raíz del stack **no** es repositorio git, quedan fuera de control de versiones] |
| **H2** | Derivación exige lectura vigente en las tres modalidades | [VERIFICADO — implementado y cubierto por T-2D-6; T1–T6 verdes tras ajustar la expectativa de T2] |
| **H3** | Migración sólo si los defaults no bastan | [VERIFICADO — **no hizo falta**: no se creó `migrations/18.0.0.22.0/`; `profile_origin` quedó `NOT NULL` con 112/112 filas en `'default'`] |
| **H4** | Aceptar limitación del distintivo «sugerido» | [VERIFICADO — sin badge adicional; el aviso de discrepancia cubre el caso] |
| **H5** | Diferir `_onchange_intake_modality_patio` (R6) | [DOCUMENTADO — riesgo abierto en CANON/04 AD-134 y CANON/12 §13.5] |

### 13.2 Commits (árbol `custom_addons`, por ruta)

| Hash | Mensaje | Rutas |
|---|---|---|
| `bb398e3` | `feat(intake): procedencia del perfil y lectura vigente (2D)` | `models/intake_wizard.py`, `views/intake_wizard_views.xml`, `__manifest__.py` (→ 18.0.0.22.0) |
| `a3b24bd` | `test(intake): T-2D-1..9 procedencia y vigencia de la lectura (2D)` | `tests/test_intake_profile_provenance.py` (nuevo), `tests/intake_reading_helpers.py` (nuevo), `tests/__init__.py` y 6 suites de derivación |
| `9804066` | `test(intake): lectura rancia por via baja y estado Leido en Procesado (2D)` | `tests/test_intake_profile_provenance.py`, `tests/test_intake_wizard.py` |
| `b5dc5c5` | `docs(intake): 2D procedencia del perfil y vigencia de la lectura` | `README.md` (§19 + historial), `CHANGELOG.md` (18.0.0.22.0) |

### 13.3 Despliegue en `madenat_test`

```
respaldo   /tmp/madenat_test_pre_2d_20261026_0956.dump  (11.679.364 bytes, pg_dump -Fc)
comando    docker compose stop web
           docker compose run --rm -T web odoo -d madenat_test -u madenat_lumber_intake \
               --stop-after-init --test-tags /madenat_lumber_intake --log-level=test
           docker compose start web
versión    ir_module_module.latest_version = 18.0.0.22.0 (state = installed)
servicio   HTTP 200 en /web/login (odoo18_app y odoo18_db arriba)
```

Log de la corrida definitiva: `/tmp/2d_upgrade2.log`.


### 13.4 Matriz de verificación

| Ítem | Resultado | Evidencia |
|---|---|---|
| **T-2D-1 … T-2D-9** | **9/9 verdes** | log `/tmp/2d_upgrade2.log` (`test_intake_profile_provenance`) |
| **T1 … T6** (`test_intake_wizard`) | **verdes** | idem |
| Suites **2A** (clasificación, marca de advertencia, requisitos, totales) | **verdes** | idem |
| Suites **2B** (espesor nominal, coherencia de perfil) | **verdes** | idem |
| Suite del módulo | `madenat_lumber_intake: 541 tests` · **445 post-tests** · **0 failed, 0 error** | `odoo.tests.result` |
| Datos — líneas | 84 registros · md5 `f8df05ac454e09ada66e5e0863cadb93` **antes == después** (hash de **fila completa**, §13.8) | SQL `WHERE id <= 7707` |
| Datos — lotes | 152 registros · md5 `d5bf9ef627561ea67dff17ac3e06c5f3` **antes == después** (hash de **fila completa**, §13.8) | SQL `WHERE id <= 49837` |
| Conteos canónicos | `lumber.reception` **8**, `madenat.guia.processing` **13** (sin cambios) | SQL antes/después |
| CSV congelados de 2B | `reception_lines.csv` `45ad1588…`, `stock_lots.csv` `02d6284d…` intactos y coherentes con los conteos (md5 de **archivo**, §13.8) | `md5sum` |
| Esquema | columnas nuevas creadas; `profile_origin` NOT NULL con todo en `'default'` | `information_schema` |
| Web | **HTTP 200** | `curl -o /dev/null -w '%{http_code}'` |

### 13.5 Incidencias de la verificación (2 fallos esperados, resueltos en el momento)

1. **`test_intake_wizard.test_t2_...`** esperaba `state == 'draft'` tras leer un Procesado. Con **H2** la
   lectura deja `previewed`: se actualizó la expectativa y se añadió la comprobación de huella. Es un cambio
   de contrato **aprobado**, no una regresión.
2. **`T-2D-7`** simulaba una lectura rancia asignando `wizard.pdf_filename = ...`. En ejecución se comprobó
   que **la asignación en Python pasa por `write()`** y por tanto invalida (comportamiento correcto y más
   robusto de lo previsto). La prueba se reescribió para mutar por vía baja (`_write` +
   `invalidate_recordset`), que es el escenario real que cubre la comparación de huella.

Ningún otro test se movió: `0 failed / 0 error` en la corrida definitiva. El `ERROR: canceling statement due
to statement timeout` del log pertenece a `TestDeleteConcurrency.test_01`, que provoca el timeout de
`pg_advisory_xact_lock` a propósito.

### 13.6 Estado final del árbol

```
$ cd custom_addons && git status --short
 M madenat_lumber_costing/__manifest__.py                 ← ajeno (excluido)
 M madenat_lumber_costing/models/__init__.py              ← ajeno
 M madenat_lumber_costing/models/lumber_cost_distribution.py
 M madenat_lumber_costing/models/lumber_shipment_costing.py
 M madenat_lumber_costing/security/ir.model.access.csv
 M madenat_lumber_costing/tests/__init__.py
 M madenat_lumber_costing/views/lumber_cost_distribution_views.xml
?? madenat_lumber_costing/models/stock_lot_cost_line.py
?? madenat_lumber_costing/tests/test_shipment_costing_c2.py
?? madenat_lumber_costing/views/lumber_shipment_costing_views.xml
 M madenat_lumber_reports/views/lumber_reports_menu.xml   ← ajeno (excluido)
 M madenat_lumber_docs/CANON/02_CONTINUIDAD.md            ← documentación 2D (este tramo)
 M madenat_lumber_docs/CANON/03_TESTS.md
 M madenat_lumber_docs/CANON/04_DECISION_LOG.md
 M madenat_lumber_docs/CANON/12_FLUJOS_INGESTA.md
 M madenat_lumber_docs/CANON/INDICE_DOCUMENTACION.md
```

- `madenat_lumber_intake`: **sin cambios pendientes** (todo commiteado).
- `madenat_lumber_costing` y `madenat_lumber_reports`: intactos y fuera de los commits, como exige el encargo.
- `.clinerules/` y el directorio de la fase viven fuera del repositorio git (la raíz del stack no es un
  repositorio); los artefactos creados son `PROMPT_2D.md`, `.clinerules/madenat-regla-de-oro.md` y este §13.
  **Actualización 2026-10-26 (consolidación FASE 2 / E3):** la copia canónica y versionada de este informe y de
  sus evidencias es `custom_addons/madenat_lumber_docs/FASES/FASE13_20261023/`; `.clinerules/` sigue fuera del
  repositorio. El dump previo a la 2D (`madenat_test_pre_2d_20261026_0956.dump`, 11,7 MB) queda fuera de git en
  `/home/viruco/dev-stack/backups/`, con su sha256 anotado en `evidencias/SHA256_FUERA_DE_GIT.csv`.

### 13.7 Riesgos abiertos y punto de retoma

| Riesgo | Descripción | Estado |
|---|---|---|
| **R6** | `_onchange_intake_modality_patio` deferido: cambiar de modalidad no reasigna el patio elegido | Abierto (2D-2) |
| **H4** | Sin badge permanente de «elegido por el operador» (sólo el aviso de discrepancia) | Aceptado |
| — | No se inició 2B tramo 3 ni Fase 2C | Respetado |

### 13.8 Conciliación de md5: «vivo» (`f8df05ac…` / `d5bf9ef6…`) vs CSV congelado (`45ad1588…` / `02d6284d…`)

**Pregunta del operador:** los md5 «vivos» de líneas y lotes no coinciden con los regenerados al cierre del
tramo 2. ¿Cambió algún registro?

**Respuesta: no. Cero registros existentes cambiaron de valor.** La discrepancia es **de procedimiento**: son
dos objetos de hash distintos (agregado SQL de fila completa vs. md5 de archivo CSV de 11 columnas), nunca
comparables entre sí. Todo lo siguiente se ejecutó en **solo lectura** (consultas `SELECT` y diff local).

#### 13.8.1 Los dos md5, reproducidos por separado

| Hash | Objeto | Consulta / comando que lo reproduce |
|---|---|---|
| `f8df05ac454e09ada66e5e0863cadb93` | `string_agg(row::text, E'\n')` de las **84 filas × 61 columnas** de `lumber_reception_line` | `SELECT md5(string_agg(l::text, E'\n' ORDER BY l.id)) FROM lumber_reception_line l WHERE l.id <= 7707;` |
| `d5bf9ef627561ea67dff17ac3e06c5f3` | ídem de las **152 filas × 113 columnas** de `stock_lot` | `SELECT md5(string_agg(l::text, E'\n' ORDER BY l.id)) FROM stock_lot l WHERE l.id <= 49837;` |
| `45ad15888e36dfbc6d53ea9d54c05ab3` | archivo `reception_lines.csv` (cabecera + 84 filas × **11 columnas de negocio**) | `md5sum evidencias/reception_lines.csv` |
| `02d6284d3209f5f6e0dc70e00a8ec4e7` | archivo `stock_lots.csv` (cabecera + 152 filas × **11 columnas de negocio**) | `md5sum evidencias/stock_lots.csv` |

El hash «vivo» arrastra `write_date`, `write_uid`, `create_uid`, `audit_hash`, `audit_snapshot`, `note`,
`lot_properties`, etc.; el CSV sólo lleva las 11 columnas de §1.7 y, además, un md5 de archivo incluye
cabecera, comas y salto final. **Son incomparables por construcción**, aunque ambos se calcularan sobre las
mismas filas.

#### 13.8.2 Prueba de que no hay deriva: el CSV se regenera byte a byte

Volcado de la BD viva con **la misma proyección de 11 columnas** y md5 del archivo resultante:

```
md5  45ad15888e36dfbc6d53ea9d54c05ab3  /tmp/regen_lines.csv   (== evidencias/reception_lines.csv)
md5  02d6284d3209f5f6e0dc70e00a8ec4e7  /tmp/regen_lots.csv    (== evidencias/stock_lots.csv)
```

> **Nota de consolidación (2026-10-26, FASE 2/E3).** Los cuatro CSV citados quedaron congelados en el repositorio:
> `custom_addons/madenat_lumber_docs/FASES/FASE13_20261023/evidencias/` (`reception_lines.csv`, `stock_lots.csv`,
> `regen_lines.csv`, `regen_lots.csv`, más los volcados vivos `live_*_raw*.csv`). Las rutas `evidencias/...` de
> §13.8.1 se resuelven en esa carpeta; el md5 de los cuatro archivos se revalidó tras la copia.

Y `diff` del cuerpo (sin cabecera) contra el congelado: **sin una sola línea de diferencia** en ambos.
Cuerpos idénticos: `9f2c7547…` (líneas) y `f6d43cc6…` (lotes).

#### 13.8.3 Diff por registro y por columna (`evidencias/fase13_md5_vs_csv_compare.py`, solo lectura)

El script queda versionado junto a los CSV; compara el congelado contra el volcado vivo de las 11 columnas
(`/tmp/live_lines_raw.csv`, `/tmp/live_lots_raw.csv`) y sale con código 0 sólo si no hay ninguna celda distinta.

| Modelo | Registros congelado/vivo | IDs faltantes | IDs nuevos | Mismo orden | Celdas distintas |
|---|---|---|---|---|---|
| `lumber_reception_line` | 84 / 84 | ninguno | ninguno | sí | **0 de 924** |
| `stock_lot` | 152 / 152 | ninguno | ninguno | sí | **0 de 1672** |

Las once columnas comparadas dan `84/84` y `152/152` valores iguales en cada caso (`id`, `lot_name`/`name`,
`export_calculation_rule`, `thickness_nominal`/`espesor_mm`, `width_nominal`/`ancho_mm`,
`length_nominal`/`largo_m`, `pieces`/`piezas`, `vol_purchase_m3`/`volume_purchase_m3`,
`vol_shipment_m3`, `vol_mbf`/`volumen_mbf`, `board_feet`/`reception_id`). Sin altas ni bajas: los máximos
`id` (7707 y 49837) siguen siendo el total de la tabla, así que el filtro `id <= …` no ocultaba nada.

**Registros existentes con cambio de valor: ninguno.** No hay lista de IDs ni de columnas que reportar.

#### 13.8.4 Cuándo se escribió por última vez y por qué

| Tabla | Filas | Valores distintos de `write_date` | Última escritura | Filas escritas desde el congelado |
|---|---|---|---|---|
| `lumber_reception_line` | 84 | **1** | `2026-10-21 18:42:15.139202` (UTC) | **0** |
| `stock_lot` | 152 | **1** | `2026-10-21 23:33:20.622530` (UTC) | **0** |

- El congelado de los CSV es del **2026-10-23 17:15:53 −0300 = 20:15:53 UTC** (`mtime`). Las dos últimas
  escrituras son **~2 días anteriores** al congelado; `write_date >= '2026-10-23 20:15:53+00'` devuelve **0**
  filas en ambas tablas. Nada se escribió durante el tramo 3 de 2B, la Fase 2C ni la Fase 2D.
- Que **todas** las filas de cada tabla compartan **un único** `write_date` (mismo microsegundo) y `write_uid = 1`
  significa **una escritura masiva por ORM**, no actividad manual ni edición registro a registro.
- Esa escritura masiva fue un **upgrade de módulo (`-u`)**, no un script de negocio: `ir_act_window` (que se
  reescribe en cada recarga de XML) tiene exactamente **los mismos microsegundos** — `18:42:15.139202`
  (21 acciones) coincide con la escritura de las 84 líneas, y `23:33:20.622530` (1 acción) con la de los 152
  lotes. En esa jornada hay además recargas a `17:58:16`, `18:25:22`, `18:58:43`, `23:23:51` y `23:33:34`.
- Correlato de datos: los campos **almacenados y calculados** introducidos ese día quedaron poblados al
  **100 %** de las filas — `stock_lot`: `merma_dimensional_m3` 152/152, `out_of_table_status` 152/152,
  `ancho_export_display` 152/152; `lumber_reception_line`: `vol_physical_real_m3` 84/84,
  `reconciliation_status` 84/84. Un upgrade que recalcula campos `store=True` reescribe **todas** las filas
  aunque los valores de negocio no cambien: eso explica el `write_date` sin cambio de datos.
- Contexto de la jornada: AD-130/AD-131/AD-132/AD-133 son del **2026-10-21**, y el chatter de `stock.lot`
  registra **87 mensajes «recalculado por AD-131»**, todos con `create_date = 2026-10-21 19:49:47.079036` UTC
  (el recálculo controlado de AD-131). Los 11 campos comparados del CSV **no** fueron corregidos por ese
  recálculo: la deriva histórica de §1.8 (p. ej. línea **4644** con `vol_shipment_m3 = 3.810` frente a 3.895
  recalculado) sigue tal cual en la BD y en el CSV congelado. Es exactamente lo esperado: histórico, no deriva.

**Descartes explícitos**

| Hipótesis | Evidencia | Veredicto |
|---|---|---|
| Cron | Consulta a `ir_cron` × `ir_act_server` para `stock.lot`, `lumber.reception.line`, `lumber.reception`: **0 crons**; `ir_cron_trigger`: **0 filas** (22 crons activos, ninguno sobre estos modelos) | **Descartado** |
| Procedimiento de volcado | El volcado se regenera idéntico (§13.8.2) y el hash de fila completa es estable (§13.8.1) | **Descartado** (era la hipótesis correcta para la *diferencia de md5*, no para un cambio de datos) |
| Upgrade de 2B (2026-10-23 21:01:54–21:02:16) | `ir_act_window` escrito, pero `max(write_date)` de líneas y lotes sigue en 2026-10-21 | **Descartado** |
| Upgrade de 2D (2026-10-26 13:04:58) | `ir_act_window` escrito (7 acciones), `max(write_date)` de líneas y lotes sin cambios | **Descartado** |
| Pruebas de la suite 2D | Corren en transacción con rollback; además ninguna fila quedó con `write_date` posterior a 2026-10-23 | **Descartado** |
| Upgrade / recálculo de campos almacenados del 2026-10-21 | Microsegundos compartidos con `ir_act_window`, `write_uid = 1`, 100 % de filas de la tabla, campos `store=True` del día poblados | **Causa de los `write_date`** |

**Límite de la atribución:** no sobrevive ningún log de Odoo del 2026-10-21 (los contenedores se recrearon);
la asignación de cada uno de los dos timestamps a un `-u` concreto es **inferencia** a partir de las cuatro
evidencias anteriores, no una lectura de log. Lo que **no** es inferencia es el hecho central: en esas dos
escrituras los 11 campos de negocio comparados quedaron con los mismos valores que tienen hoy (§13.8.3).



#### 13.8.5 Conclusión y nota operativa

| Pregunta | Respuesta |
|---|---|
| ¿Cambió algún registro existente? | **No.** 0 de 924 celdas (líneas) y 0 de 1672 (lotes) distintas; 0 altas, 0 bajas |
| ¿Entonces por qué difieren los md5? | Son **objetos distintos**: hash SQL de fila completa (61/113 columnas, incluidas `write_date`/`write_uid`) vs md5 de archivo CSV de 11 columnas |
| ¿Cuándo se escribió por última vez? | **2026-10-21**: líneas `18:42:15.139202` UTC (84/84), lotes `23:33:20.622530` UTC (152/152) |
| ¿Por qué? | Escrituras masivas por ORM de los upgrades/recálculos de campos almacenados de esa jornada (AD-130…AD-133); microsegundos compartidos con `ir_act_window`, `write_uid = 1`, 100 % de filas |
| ¿Fue cron? | **No**: 0 crons sobre `stock.lot` / `lumber.reception.line` / `lumber.reception`; 0 triggers |
| ¿Fue 2B, 2C o 2D? | **No**: 0 filas con `write_date >= 2026-10-23 20:15:53+00` (congelado) |

**Nota operativa (propuesta, no ejecutada):** el md5 «vivo» de fila completa **no** sirve como control de datos
de negocio entre sesiones, porque cambia cuando un upgrade recalcula cualquier campo almacenado o cuando se
toca `write_uid`/`write_date`, aunque no se mueva un solo valor de negocio. El control canónico recomendado es
el volcado de **11 columnas** de §1.7 (`evidencias/*.csv`), que se regenera byte a byte y ya está congelado en
el repositorio; si se quiere un hash de una línea para los informes, debe calcularse **sobre ese archivo** y
declararse explícitamente como «md5 de archivo (11 columnas)». Cualquier cambio de esta práctica queda a
decisión del operador: aquí no se modificó ni el código ni los datos.

**FASE 2D COMPLETADA — A LA ESPERA DE REVISIÓN**

