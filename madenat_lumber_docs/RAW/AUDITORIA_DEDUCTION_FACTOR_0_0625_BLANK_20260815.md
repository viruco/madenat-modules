# AUDITORÍA ACOTADA — `deduction_factor = 0.0625` / Flujo Blank (`f5085`)

**Fecha:** 2026-08-15
**Alcance:** semántica, origen, uso efectivo e impacto de `deduction_factor = 0.0625` en el flujo Blank.
**Modo:** solo lectura / análisis estático. Sin modificar código, XML, tests, BD, Docker, Git ni CANON.

---

## 1. Alcance y restricción de la auditoría

Se audita exclusivamente el valor `0.0625` asociado a `deduction_factor` y su rol en el cálculo de volumen de exportación del perfil Blank (`f5085`). No se rediseña ninguna fórmula, no se propone corrección de código, y no se declara cierre del pendiente de negocio. Toda afirmación está etiquetada como `CODE`, `DOC`, `SEED`, `TEST` o `INFERENCIA`.

---

## 2. Evidencia de negocio confirmada

Cristhian confirma, para el volumen Blank:

- Espesor en pulgadas.
- Ancho comercial en pulgadas **+ 1/8"** (`0.125`).
- Largo en pies.
- Cantidad de piezas.
- Divisor `5085.312`.

Fórmula confirmada:

    volumen_blank = espesor_pulgadas × (ancho_pulgadas + 0.125) × largo_pies × piezas / 5085.312

**La evidencia de negocio NO menciona una deducción adicional de 1/16" (`0.0625`).**

Archivo de respaldo citado: `ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx` (no presente en el árbol de código auditado; se asume externo). **SIN_EVIDENCIA** de que ese Excel declare la deducción `0.0625`.

---

## 3. Inventario de definiciones y referencias de `deduction_factor`

| Ubicación | Tipo | Línea | Contenido | Naturaleza |
|---|---|---|---|---|
| `models/lumber_export_formula.py` | CODE | 97–102 | `deduction_factor = fields.Float(..., default=0.0, help="... Blank Clear: 0.0625 (-1/16\"). Otros: 0.0.")` | Campo de modelo Fase 3, **default 0.0** |
| `models/lumber_export_formula.py` | CODE | 198 | fallback `f5085` → `deduction_factor = float(utils_uom.FACE_DEDUCTION_INCH)` (= 0.0625) | **Fallback activo** si no hay registro Fase 3 |
| `models/utils_uom.py` | CODE | 639 | `FACE_DEDUCTION_INCH = Decimal('0.0625')  # -1/16" deducción por cara` | Constante canónica |
| `data/ingestion_seed_fase3.xml` | SEED | (reg. `export_formula_f5085`) | `<field name="deduction_factor" eval="0.0625"/>` | **Dato activo** de semilla (noupdate=1, forcecreate=True) |
| `data/ingestion_seed_fase3.xml` | SEED | (nota del reg.) | "Deducción de cara: -1/16" (0.0625). Sin ajuste S2S adicional." | Documentación del seed |
| `data/ingestion_seed_fase3.xml` | SEED | (reg. f1550/metric) | `<field name="deduction_factor" eval="0.0"/>` | 0 para S2S y métrico |

**Distinción explícita:**
- El campo por defecto es `0.0`; el valor `0.0625` se activa **solo** para el registro f5085 vía el seed `noupdate=1` (dato activo configurado) o vía el fallback de `utils_uom` (si el registro no existiera).

---

## 4. Flujo de ejecución real para Blank

`_compute_export_values` en `lumber_reception.py`:

1. Determina regla: `rule = 'f5085'` si `t_in > 0` (L715-717).
2. Resuelve fórmula desde `lumber.export.formula._resolve_for_profile('f5085')` (L720), que retorna `deduction_factor` desde el modelo Fase 3 o desde `FACE_DEDUCTION_INCH`.
3. Entra a rama `formula_kind == 'blank_clear'` (L726-735).

---

## 5. Fórmula efectiva en código

Código real (`lumber_reception.py:731-735`, rama `blank_clear`):

```python
t_calc = t_in - formula['deduction_factor']          # L731: espesor − 0.0625
w_calc = w_in + float(S2S_WIDTH_ADJUSTMENT_INCH)      # L732: ancho + 0.125
l_ft   = line.length_input_raw or (l_m / METRO_A_PIE)
vol_exp = (t_calc * w_calc * l_ft * qty) / formula['principal_factor']
val_mbf = (t_calc * w_calc * l_ft * qty) / formula['mbf_divisor']
```

Fórmula efectiva ejecutada por código para Blank:

    (espesor − 0.0625) × (ancho + 0.125) × largo_pies × piezas / 5085.312

**Confirmado por código:** el `deduction_factor` **sí está en el camino de ejecución Blank**, aplicándose como sustracción al **espesor**.

---

## 6. Comparación: regla confirmada vs comportamiento implementado

| Dimensión | Regla confirmada (Cristhian) | Código implementado | ¿Coincide? |
|---|---|---|---|
| Espesor | `espesor_pulgadas` (sin deducción) | `espesor − 0.0625` | ❌ NO |
| Ancho | `ancho + 0.125` | `ancho + 0.125` | ✅ SÍ |
| Largo | pies | pies | ✅ SÍ |
| Piezas | `piezas` | `qty` | ✅ SÍ |
| Divisor | `5085.312` | `5085.312` | ✅ SÍ |

**Discrepancia principal:** el código agrega una **deducción de 1/16" al espesor** que la regla de negocio confirmada **no incluye**. La semilla Fase 3 documenta esta deducción como "−1/16" (0.0625)" basada en `ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx`, pero la confirmación reciente de negocio no la menciona.

---

## 7. Riesgo de doble ajuste

**SÍ existe doble ajuste.** El código combina dos modificaciones simultáneas sobre la fórmula canónica:

1. **Ancho** `+0.125` (ajuste S2S, coincidente con la regla).
2. **Espesor** `−0.0625` (deducción de cara, NO coincidente con la regla).

Además, el seed declara `s2s_adjustment_mode = 'none'` para f5085, pero el código aplica el `+0.125` de ancho de forma **hardcoded** (`L732`), ignorando ese modo. El comentario de código lo reconoce: *"s2s_adjustment_mode='none' bloqueaba el +1/8"* (L730). Esto significa que hay **dos fuentes de ajuste** en el flujo Blank y una contradicción entre el seed (`none`) y el código (`+0.125` forzado).

**Ejemplo numérico (efecto del `0.0625`):**
Dado espesor nominal `1.75"`, ancho `5.5"`, largo `8.005 ft`, `20` piezas:

- Regla confirmada: `1.75 × (5.5 + 0.125) × 8.005 × 20 / 5085.312`
- Código: `(1.75 − 0.0625) × (5.5 + 0.125) × 8.005 × 20 / 5085.312`

El código reduce el volumen en factor `(1.75 − 0.0625) / 1.75 = 0.9643`, es decir **≈ −3.57 %** respecto de la regla confirmada (la deducción de espesor es la única diferencia, dado que el `+0.125` de ancho está presente en ambos).

---

## 8. Cobertura de pruebas

- `tests/test_lumber_reception.py` L364-377 (caso T13): calcula el volumen Blank esperado como `round((_e * _a * _l * _p) / 5085.312, 3)` — **sin deducción de espesor y sin +1/8" de ancho**. Es decir, el test actual usa una fórmula **diferente** tanto de la regla de negocio confirmada como del código implementado.
- No existe **ningún test** que ejerza o verifique el valor `deduction_factor = 0.0625` (búsqueda de `deduction_factor`, `0.0625`, `FACE_DEDUCTION`, `blank_clear` en `tests/` arroja 0 coincidencias directas, salvo `f5085` como perfil).
- **`SIN COBERTURA`** para el factor `0.0625`. El test T13 está desactualizado respecto del código (comentario `MADENAT-FIX-BLANK-2026-06-02` vs. `FIX 2026-06-11 v2` en el código), y su `expected_blank_vol` no incorporaría ni la deducción ni el +1/8".

---

## 9. Conclusión clasificada

**Implementación contradictoria con la regla confirmada.**

Justificación (evidencia):
- La fórmula de negocio confirmada no incluye deducción de espesor; el código sí la aplica (`t_calc = t_in - 0.0625`, `lumber_reception.py:731`).
- El factor está activo en datos configurados (seed `noupdate=1` con `0.0625` + fallback `FACE_DEDUCTION_INCH`).
- Existe doble ajuste (espesor −1/16" + ancho +1/8") y contradicción interna seed/código respecto a `s2s_adjustment_mode='none'`.
- No hay cobertura de pruebas que valide el `0.0625`.

---

## 10. Acción mínima recomendada (sin implementar)

Confirmar con Cristhian/Operaciones, con el Excel `ANCHOS-COMPRA-COL-ROUGH-A-S2S.xlsx` como respaldo, si la fórmula Blank debe o no incluir la deducción de **1/16" al espesor**:

- Si **no** debe incluirse → actualizar la fórmula canónica y alinear `deduction_factor` (seed + fallback) a `0.0` para f5085, y corregir el test T13.
- Si **sí** debe incluirse → documentar formalmente la deducción `0.0625` como parte de la regla (hoy ausente de la confirmación de negocio), y corregir el test T13 para reflejar `(t − 0.0625) × (w + 0.125)`.

No se debe cambiar código ni seed hasta obtener confirmación explícita de negocio; la evidencia disponible muestra una contradicción, no una regla unívoca a ejecutar.