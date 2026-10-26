# DICTAMEN DE ALCANCE A/B — Retorno de servicio + imputación posterior (2026-10-07)

## 1. Qué se reutilizó

| Componente | Origen reutilizado |
|---|---|
| Campo/Selection Sí–No y UI inline (radio) | Antecedente `IMPL_SERVICE_RETURN_20261006/` |
| Punto de enganche servidor de «enviar a stock» | `madenat.guia.processing.action_validate` / consola |
| Proxy de consola (compute + inverse) | Patrón de la consola de Intake |
| **Mecanismo completo de imputación SV (I2)** | `madenat.sv.imputation` / `.line` / `.sv.line` (activo, AD-91) |
| Relación origen↔destino | `sv.lot.lot_flow_type='volume'` + `stock.lot.volume_source_guia_id` (guía de Volúmenes) y `imputation.guia_processing_id` (guía Procesada) |
| Permisos, idempotencia, reversa | I2 vigente (Operaciones/Jefatura/Gerencia, `documentary_key`, `action_reverse`) |

## 2. Qué se añadió (mínimo)

- **A:** `service_return_confirmation` (core) + proxy editable (intake) + radio/filtros (core,
  intake) + regla **Sí→No con imputaciones aplicadas** y **relación inversa** `sv_imputation_ids`
  (logistics).
- **B:** exigencia de **destino «Sí» en `action_apply`** + filtro **«Retornos sin imputación
  aplicada»** (logistics).

## 3. Ubicación por dependencias (requisito respetado)

- `service_return_confirmation` (campo neutro) → **core** (sin dependencias nuevas).
- Uso del modelo I2 (relación inversa, regla Sí→No, chequeo destino) → **logistics**, donde existe
  `madenat.sv.imputation`. **No** hay dependencia `core → logistics` ni circular.
- Proxy de edición de la Consola → **intake** (compute + **inverse**), verificado como **editable**
  por el usuario operativo (no sólo lectura).

## 4. Resumen del flujo real

- **Identificación (A):** el operador marca «Sí/No» en la Consola (o en la guía). Vacío = pendiente.
  La marca **no** bloquea la ingesta ni el envío a stock y **no** crea imputaciones.
- **Imputación posterior (B):** desde la guía marcada «Sí», el asistente I2 relaciona las
  **etiquetas procesadas** (destino) con los **SV** (origen de Volúmenes). Al **aplicar**, se exige
  el destino «Sí». Es **documental**: no mueve stock, ledger ni costes.

## 5. ¿Es necesario un módulo nuevo? — **NO**

Sustentado en el **mecanismo existente**, no en preferencia de arquitectura:

- La **imputación posterior** estrella guía-Volúmenes ↔ guía-Procesada ya se materializa en **I2**
  a nivel de **etiqueta/SV** (unidad de captura de la doctrina, CANON/19 §4.1), con relación
  explícita (`sv_lot_id`, `guia_processing_id`), imputación parcial, N:M, usuario/fecha/estado y
  consulta/corrección por permisos.
- La **identificación** (A) se resuelve con **un campo** en la guía y un **proxy** de consola; no
  requiere modelo, asistente ni módulo.
- **Cero módulos nuevos. Cero campos de negocio almacenados nuevos** (el único campo nuevo es la
  clasificación Sí/No; la relación inversa es virtual, sin columna).

## 6. Desviación respecto del antecedente (declarada)

El antecedente **bloqueaba** el envío a stock sin confirmación. El encargo vigente exige lo
contrario: la identificación **no bloquea**. En consecuencia se **elimina** el guard
`_assert_service_return_confirmed` y se conservan el resto de validaciones.
