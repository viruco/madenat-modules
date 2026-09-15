# AUDITORÍA DE RECONCILIACIÓN — VOLUMEN BLANK / TARJAS MSC VIRGO

**Fecha:** 2026-08-15
**Modo:** solo lectura / análisis estático. Sin modificar código, XML, tests, BD, Docker, Git ni CANON.
**Archivo fuente:** `custom_addons/madenat_lumber_docs/RAW/LISTADO Y TARJAS MN MSC VIRGO FA610R.xlsx`

---

## 1. Alcance, fuentes y restricciones

### Alcance
- Validar que el cálculo M3 de las tarjas Blank (BLANK CLEAR y BLANK B) del Excel es consistente con:
  1. la configuración `f5085` (`deduction_factor = 0.0625`),
  2. la implementación de código del cálculo Blank,
  3. el redondeo a 3 decimales.
- RIP ROUGH se analiza solo para confirmar que no usa f5085.

### Fuentes
| Fuente | Tipo |
|---|---|
| `LISTADO Y TARJAS MN MSC VIRGO FA610R.xlsx` (hojas `TARJAS MN MSC VIRGO`, `LISTADO MN MSC VIRGO`) | EXCEL |
| `data/ingestion_seed_fase3.xml` (registro `export_formula_f5085`) | SEED |
| `models/lumber_export_formula.py` | CODE |
| `models/utils_uom.py` (`FACE_DEDUCTION_INCH`, `S2S_WIDTH_ADJUSTMENT_INCH`, `BLANK_CLEAR_FACTOR`) | CODE |
| `models/lumber_reception.py` (`_compute_export_values`) | CODE |
| `tests/test_lumber_reception.py` (T13) | TEST |

### Restricciones
- No se modifica nada. No se declara UAT ejecutada. No se abre auditoría general ni se cambia CANON.
- El Excel se lee con `openpyxl` en `data_only=False` (fórmulas) y `data_only=True` (valores cacheados).

---

## 2. Regla operativa extraída del Excel

Todas las líneas Blank usan, por fila, la fórmula exacta:

```
=(H<n> - 1/16) * (I<n> + 1/8) * J<n> * K<n> / 5085.312
```

Interpretación confirmada:

```
volumen_blank_m3 =
  (espesor_pulgadas - 0.0625)      # H = espesor en pulgadas
  × (ancho_pulgadas + 0.125)       # I = ancho en pulgadas
  × largo_pies                     # J = largo en pies
  × piezas                         # K = piezas
  / 5085.312
```

- La deducción `1/16"` (`0.0625`) se aplica al **espesor**.
- El incremento `1/8"` (`0.125`) se aplica al **ancho**.
- Largo en **pies**; resultado en **m³**.

> **Nota de evidencia:** esto **contradice** la confirmación verbal anterior (tarea de auditoría acotada) que omitía la deducción. El Excel — cálculo manual vigente de Cristhian — **sí incluye** la deducción de 1/16", y es la evidencia primaria. El código y la configuración coinciden con el Excel (no con la transcripción verbal incompleta).

---

## 3. Inventario de fórmulas Blank por hoja/fila

### Hojas
- `TARJAS MN MSC VIRGO` (dims B2:AB162): tarjas de detalle. Lado izquierdo columnas B..N; lado derecho P..AB (espejo impreso). Columna L = M3 (fórmula); columna Z = M3 (valor a 3 decimales).
- `LISTADO MN MSC VIRGO` (dims B2:N105): listado consolidado. Columna L = M3.

### Familias de fórmula detectadas (columna L)

| Familia | Fórmula patrón | Filas | Subproductos |
|---|---|---|---|
| **Blank (f5085)** | `=(H-1/16)*(I+1/8)*J*K/5085.312` | 6–13, 20–27, 34–41, 48–55, 62–69 | BLANK CLEAR y BLANK B |
| **Rough (métrico)** | `=ROUND((H*I*J*K)/1000000,3)` | 76–87, 94–107, 114–125, 132–143, 150–161 | RIP ROUGH (planta FATIMA) |
| Subtotal tarja | `=SUM(L<ini>:L<fin>)` | 14, 28, 42, 56, 70, 88, 108, 126, 144, 162 | — |

**Confirmación:** las 40 líneas Blank (5 tarjas × 8 líneas) usan **exacta y únicamente** la fórmula `=(H-1/16)*(I+1/8)*J*K/5085.312`. No hay variaciones. `5085.312`, `1/16` y `1/8` aparecen como **constantes directas** dentro de la fórmula (no como celdas de referencia).

### Blank Clear vs Blank B
**Ambos usan la MISMA fórmula.** No hay bifurcación por subproducto en el Excel. La distinción entre `BLANK CLEAR` y `BLANK B` es solo de rótulo (`G`), no de cálculo.

---

## 4. Tabla de reconciliación Excel

El Excel solo contiene **2 combinaciones únicas de dimensiones Blank** (no hay espesores de 2" ni 3" en Blank; ver §8).

Combinación A — ancho 2.625" (416 piezas):

```
(1.5625 - 1/16) × (2.625 + 1/8) × 16 × 416 / 5085.312
= 1.5 × 2.75 × 16 × 416 / 5085.312
= 27456 / 5085.312
= 5.399078758589444
```

Combinación B — ancho 3.625" (286 piezas):

```
(1.5625 - 1/16) × (3.625 + 1/8) × 16 × 286 / 5085.312
= 1.5 × 3.75 × 16 × 286 / 5085.312
= 25740 / 5085.312
= 5.061636336177603
```

| Combo | Subproducto | H (esp) | I (ancho) | J (largo) | K (pzas) | Fórmula Excel (L) | Cálculo independiente | M3 redondeado a 3 (tarja Z) | ¿Coincide? |
|---|---|---|---|---|---|---|---|---|---|
| A | BLANK CLEAR / B | 1.5625 | 2.625 | 16 | 416 | `=(H-1/16)*(I+1/8)*J*K/5085.312` | 5.399078758589444 | 5.399 | ✅ exacto |
| B | BLANK CLEAR / B | 1.5625 | 3.625 | 16 | 286 | `=(H-1/16)*(I+1/8)*J*K/5085.312` | 5.061636336177603 | 5.062 | ✅ exacto |

**Resultado:** la fórmula Excel, ejecutada con precisión completa, coincide **exactamente** con el valor calculado de forma independiente, y su redondeo a 3 decimales coincide con el M3 impreso en la tarja (columna Z). Diferencia absoluta = 0.0 en todos los casos.

---

## 5. Comparación con configuración f5085

| Parámetro | Excel | Configuración f5085 | ¿Coincide? |
|---|---|---|---|
| Deducción espesor | `-1/16` (0.0625) | `deduction_factor = 0.0625` (seed `export_formula_f5085`; fallback `FACE_DEDUCTION_INCH`) | ✅ |
| Incremento ancho | `+1/8` (0.125) | `S2S_WIDTH_ADJUSTMENT_INCH = 0.125` (código aplica +1/8 hardcoded en rama blank_clear) | ✅ (matiz abajo) |
| Factor | 5085.312 | `principal_factor = 5085.312` / `BLANK_CLEAR_FACTOR` | ✅ |
| Largo | pies | `unit_mode = imperial_feet` | ✅ |

**Matiz de configuración (hallazgo documental, no numérico):** el seed declara `s2s_adjustment_mode = 'none'` para f5085, pero el `+1/8"` de ancho se aplica igualmente por línea hardcoded en código (`lumber_reception.py:732`). La configuración `none` es **semánticamente ambigua** con el incremento de ancho observado en el Excel, pero el resultado **numérico es correcto e idéntico al Excel**. No afecta el M3.

---

## 6. Comparación con código

Código real — `models/lumber_reception.py`, `_compute_export_values`, rama `formula_kind == 'blank_clear'` (L726–735):

```python
t_calc = t_in - formula['deduction_factor']          # L731: espesor (pulg) - 0.0625
w_calc = w_in + float(S2S_WIDTH_ADJUSTMENT_INCH)     # L732: ancho (pulg) + 0.125
l_ft   = line.length_input_raw or (l_m / METRO_A_PIE)  # largo en pies
vol_exp = (t_calc * w_calc * l_ft * qty) / formula['principal_factor']
```

| Dimensión | Excel | Código | ¿Coincide? |
|---|---|---|---|
| Espesor | `H - 1/16` | `t_in - deduction_factor` (0.0625) | ✅ |
| Ancho | `I + 1/8` | `w_in + S2S_WIDTH_ADJUSTMENT_INCH` (0.125) | ✅ |
| Largo | pies (J) | pies (`length_input_raw`) | ✅ |
| Piezas | K | `qty` | ✅ |
| Factor | 5085.312 | `principal_factor` | ✅ |

**Conclusión de código:** la implementación es matemáticamente idéntica a la fórmula del Excel. Orden de operaciones y unidades coinciden.

**Nota de redondeo interno:** el código almacena `vol_shipment_m3` con `float_round(..., precision_digits=6, HALF-UP)` y presenta a 3 decimales (`digits=(16,3)`). El Excel conserva el valor completo en L (sin redondear) y muestra 5.399 en Z (3 decimales). Compatible.

---

## 7. Evaluación de redondeo a 3 decimales

- El resultado sin redondear es `5.399078758589444` y `5.061636336177603`.
- Redondeo a 3 decimales (mitad hacia arriba): `5.399` y `5.062` respectivamente.
- El M3 de tarja (columna Z) muestra **exactamente** `5.399` y `5.062`.

**Conclusión:** el redondeo a 3 decimales del Excel coincide con la política de presentación del sistema (3 decimales). La diferencia entre el valor completo (L) y el valor impreso (Z) es exclusivamente de presentación/redondeo, no de cálculo.

---

## 8. Evaluación de separación Blank Clear vs Blank B

- En el Excel, `BLANK CLEAR` y `BLANK B` usan **la misma fórmula**, el mismo espesor (1.5625") y las mismas dimensiones; solo cambia el rótulo de subproducto.
- No hay evidencia de que deban calcularse distinto.
- En código, el discriminador de la rama `blank_clear` es **el perfil `f5085`**, no el subproducto puntual. `BLANK B` no es un perfil separado en `lumber.export.formula`.

**Conclusión:** no existe separación de cálculo entre Blank Clear y Blank B ni en Excel ni en código. Ambos caen en la misma rama `blank_clear` y producen el mismo M3 para dimensiones equivalentes.

### Cobertura de espesores
El archivo **no contiene líneas Blank de espesor 2" ni 3"**. El único espesor Blank es `1.5625`" (1 9/16"). Las líneas de 24 mm presentes son RIP ROUGH (métrico), no Blank. Por tanto, la validación de espesores 2"/3" queda **fuera de cobertura** por los datos del archivo (se registra como vacío, no como discrepancia).

### RIP ROUGH (fuera de alcance, solo descarte)
RIP ROUGH usa `ROUND((H*I*J*K)/1000000,3)` con H/I/J en **mm/m** y factor 1.000.000 — NO usa 5085.312 ni la deducción de 1/16". Confirmado que no usa f5085.

---

## 9. Estado de pruebas automatizadas

- `tests/test_lumber_reception.py` T13 (L364–377): el valor esperado se calcula como `(_e * _a * _l * _p) / 5085.312` con `_e = 44.45/25.4`, `_a = 139.7/25.4`, `_l = 2.44/0.3048`, `_p = 20` — es decir **sin deducción de espesor y sin +1/8" de ancho**. El comentario dice explícitamente "BLANK no debe tener +1/8"".
- **Esto está desalineado** con el Excel y con el código, que sí aplican `(espesor − 1/16)` y `(ancho + 1/8)`. El test T13 codifica un supuesto que **no coincide** con la fórmula operativa real de las tarjas.
- No existe prueba automatizada que valide los valores `5.399` / `5.062` contra la fórmula Blank completa.

**Caso de prueba mínimo necesario (a especificar, NO modificar):** un test que, para esp=1.5625", ancho=2.625", largo=16 ft, 416 pzas, espere `vol_shipment_m3 = 5.399` (y el análogo 3.625"/286 pzas = 5.062), usando la rama `blank_clear` con deducción y +1/8".

---

## 10. Conclusión

**Consistente: Excel, configuración y código coinciden.**

Evidencia:
- Las 40 líneas Blank del Excel usan idéntica fórmula `(espesor − 1/16) × (ancho + 1/8) × largo_pies × piezas / 5085.312`.
- El cálculo independiente reproduce exactamente los valores `5.399078758589444` y `5.061636336177603`, y el M3 impreso a 3 decimales (`5.399` / `5.062`) coincide.
- La configuración `f5085` (`deduction_factor = 0.0625`, factor 5085.312) y el código (`lumber_reception.py:731-735`) producen exactamente la misma fórmula.
- La única desalineación está en el **test T13**, que omite la deducción y el incremento; no en el código ni en el Excel.

---

## 11. Acciones mínimas (sin implementar cambios)

1. Alinear la prueba automatizada T13 con la fórmula operativa real: `(espesor − 1/16) × (ancho + 1/8) × largo_pies × piezas / 5085.312`, con casos que esperen `5.399` y `5.062`.
2. Reconciliar la documentación de negocio: la confirmación verbal que omitía la deducción debe actualizarse para reflejar el Excel como evidencia primaria (el Excel sí incluye `−1/16`).
3. Aclarar la semántica de `s2s_adjustment_mode='none'` en el seed f5085 (hoy convive con un `+1/8"` hardcoded en la rama `blank_clear`): documentar si es intencional o redundante; no afecta el resultado M3.
4. Si se requiere validar espesores Blank de 2" y 3", proveer una tarja/Excel que los contenga (no están en este archivo).

**No se reporta discrepancia numérica** entre Excel y sistema para el alcance Blank de este archivo.