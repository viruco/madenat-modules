# Resultados de pruebas (cierre de avisos y compatibilidad)

## Comandos

- **Positivo:** `run_iso.sh` → `dupval3_iso` sobre `dupval3_iso_20261007` (`logs/iso_run.log`).
- **Negativo:** `run_iso_unpatched.sh` → `dupval3_neg` sobre `dupval3_neg_20261007`
  (`logs/iso_run_unpatched.log`).

Ambos: `-u madenat_lumber_core`, `--test-enable`, usuario operativo real
(`group_madenat_operaciones`), **sin superusuario**.

## Resultado global

| Corrida | Resultado |
|---|---|
| **Positivo (esta entrega)** | **`0 failed, 0 error(s) of 48 tests`** = 10 `TestGuideDuplicateWarnings` + 30 `TestGuideDuplicateIngest` + 8 `TestDuplicateValidation` |
| **Negativo (parche CIERRE)** | `2 failed, 4 error(s) of 10 tests` (sólo la suite de avisos) |

Pruebas que **dependen del cierre** (fallan sin él):

| Test | Qué demuestra | Sin el cierre |
|---|---|---|
| `w2_reception_homonym_warns_guia` | aviso en Recepción (sentido recepción→guía) | error (sin `_warn_guide_homonym` en recepción) |
| `w3_guia_warning_not_repeated_without_change` | no repetición (guía) | falla (avisos repetidos) |
| `w5_reception_warning_not_repeated_when_number_unchanged` | no repetición (recepción) | error (sin helper) |
| `w6_reception_confirmed_duplicate_still_blocks` | compatibilidad del bloqueo | error (sin helper) |
| `w8_warning_rolls_back_with_operation` | atomicidad del aviso | error (sin helper) |
| `w9_shared_warning_on_both_models` | mixin compartido | falla |

`w1` (guía↔recepción), `w4` (cambio de identidad), `w7` (sin fuga), `w10` (contrato C1) pasan en
ambas corridas → **sin regresión** y evidencia de continuidad.

## Cobertura (mapea a §6 del prompt)

`usuario operativo, su=False`.

| Requisito | Test |
|---|---|
| Homónimo guía → Recepción | `w1` |
| Homónimo Recepción → guía | `w2` |
| Guardar repetidamente → un aviso | `w3`, `w5` |
| Releer el mismo documento → sin repetición | `w5` |
| Modificar campo ajeno → sin nuevo aviso | `w3` |
| Cambio real de identidad → comportamiento correcto | `w4` |
| Nueva coincidencia → aviso | `w4` |
| Operación rechazada → rollback del aviso | `w8` |
| Documento no autorizado → sin filtración | `w7` |
| Duplicado confirmado sigue bloqueado | `w6`, `w10`, `TestDuplicateValidation` |
| Identidad incompleta se guarda | `ingest.test_05/06b/27` |
| Completado posterior revalida | `ingest.test_06/06b` |
| Edición propia sin falso positivo | `ingest.test_08` |
| Exclusión no oculta otro modelo con igual ID | `ingest.test_08b` |
| Lotes (`create`/`write` múltiple) | `ingest.test_10/12` |

## Efectos materiales probados (exactos)

- **Cabecera:** sí. **Staging:** sí (`ingest.test_23`). **Lotes / movimientos / `stock.quant`:**
  **NO** (el bloqueo ocurre antes de materializar) → **no** se declara cobertura de stock.

## Concurrencia

No se probó con **dos transacciones simultáneas**. El `search` previo protege lo **secuencial**.
El aviso `message_post` se probó en repetición **secuencial** (no concurrente). Riesgo
`partner_id` nulo **permanece visible**.
