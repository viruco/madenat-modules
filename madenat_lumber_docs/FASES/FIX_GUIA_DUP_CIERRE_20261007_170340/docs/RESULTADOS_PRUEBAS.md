# Resultados de pruebas en aislamiento

## Comandos

- **Positivo (ajustes A/B/C):** `run_iso.sh` → `dupval2_iso` sobre `dupval2_iso_20261007`
  (`logs/iso_run.log`).
- **Negativo (parche PREVIO, sin A/B/C):** `run_iso_unpatched.sh` → `dupval2_neg` sobre
  `dupval2_neg_20261007` (`logs/iso_run_unpatched.log`).

Ambos: `-u madenat_lumber_core`, `--test-enable`, usuario operativo real
(`group_madenat_operaciones`), **sin superusuario** en las acciones bajo prueba.

## Resultado global

| Corrida | Resultado |
|---|---|
| **Positivo (esta entrega)** | **`0 failed, 0 error(s) of 38 tests`** (30 de `TestGuideDuplicateIngest` + 8 de `TestDuplicateValidation`) |
| **Negativo (parche previo)** | `1 failed, 5 error(s) of 38 tests` |

**Pruebas que dependen de los ajustes** (fallan con el parche previo, pasan con esta entrega):

| Test | Ajuste demostrado |
|---|---|
| `test_02_homonym_guia_vs_reception` | B (simetría cross-model) |
| `test_06b_incomplete_identity_not_blocked_then_completed` | A (incompleto no bloquea + revalidación) |
| `test_27_incomplete_unknown_supplier_then_distinct` | A |
| `test_28_cross_model_symmetric_not_blocked` | B |
| `test_29_homonym_warns_non_blocking` | C (aviso no bloqueante) |
| `test_30_residual_null_partner_risk_documented` | A (límite declarado) |

El resto de la suite (32 tests) pasa en ambas corridas → **sin regresiones**.

## Cobertura (mapea a §8 del prompt)

| Requisito | Test(s) |
|---|---|
| Captura con proveedor desconocido | `test_05`, `test_06b`, `test_27` |
| Completado sin duplicado | `test_06`, `test_27` |
| Completado que confirma duplicado | `test_06`, `test_06b` |
| Mismo número, proveedor distinto | `test_04` |
| Coincidencia entre modelos, **ambos órdenes** | `test_03`, `test_28` |
| Exclusión propia con IDs iguales entre modelos | `test_08`, `test_08b` |
| `create` múltiple | `test_10` |
| `write` múltiple | `test_12` |
| Relectura / archivo complementario | `test_15`, `test_16` |
| Procesado | `test_18` |
| Volúmenes | `test_19` |
| Formulario directo | `test_20`, `test_14` |
| Recepción/Producto (regresión) | `test_21`, `TestDuplicateValidation` (8) |
| Rechazo sin cabecera/staging parcial | `test_23`, `test_24` |
| Restricciones de visibilidad | `test_25` |
| Cancelado sigue contando | `test_07` |
| Homónimo → aviso no bloqueante | `test_29` |
| Conflicto intra-lote | `test_10`, `test_12` |

## Efectos materiales probados (exactos)

- **Cabecera:** sí (todos los casos).
- **Líneas de staging (`processing_line_ids`):** sí (`test_23`).
- **Lotes / movimientos / `stock.quant`:** **NO** — no se alcanzan (el bloqueo ocurre antes
  de materializar). **No** se declara cobertura de stock/productos.

## Concurrencia

- No se ejecutó una prueba de **dos transacciones simultáneas**. El `search` previo protege
  el caso **secuencial**; **no** se declara blindaje concurrente (`test_26` sólo verifica que
  el backstop SQL existe). Riesgo `partner_id` nulo **permanece visible** (ver `test_30`).
