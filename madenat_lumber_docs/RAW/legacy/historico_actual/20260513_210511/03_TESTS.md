# MADENAT — Matriz de Pruebas
**Versión:** 5.0.0  
**Fecha:** 2026-05-03  
**Estado:** ACTIVO - Fase 4 COMPLETADA ✅ (T01-T14 validados)

***

## 1. Regla operativa

Toda modificación de parser, staging, cálculo, Gates o stock debe quedar reflejada aquí antes de considerarse cerrada.

***

## 2. Matriz principal

| ID | Caso | Entrada | Esperado | Resultado | Estado |
|---|---|---|---|---|---|
| T01 | Suma m3 por línea | Packing estándar | Suma líneas = `total_volume_m3` | ✅ PASSED | CERRADO |
| T02 | Suma MBF por línea | Packing estándar | Suma líneas = `total_volume_mbf` | ✅ PASSED | CERRADO |
| T03 | Triple capa | Blanks | Visual ≠ Física ≠ Nominal, cada una correcta | ✅ PASSED | CERRADO |
| T04 | Rule `metric` | Línea nacional | `vol_shipment_m3 = vol_physical_m3` | ✅ PASSED | CERRADO |
| T05 | Rule `f1550` | Línea S2S | cálculo exacto con factor 1550.003 | ✅ PASSED | CERRADO |
| T06 | Rule `f5085` | Línea Blanks | cálculo exacto con factor 5085.312 | ✅ PASSED | CERRADO |
| T07 | Gate 2 nominal null | Staging incompleto | Bloquea confirmación | ✅ PASSED | CERRADO |
| T08 | Gate 2 producto inválido | Producto inactivo | Bloquea confirmación | ✅ PASSED | CERRADO |
| T09 | Gate 2 volumen fuera tolerancia | Diferencia > tolerancia | Bloquea confirmación | ✅ PASSED | CERRADO |
| T10 | Gate 3 commit | Staging válido | crea `stock.lot` y `stock.picking` | ✅ PASSED | CERRADO |
| T11 | Recall de lote | Recepción cerrada | `lot_name` trazable al paquete real | ✅ PASSED | CERRADO |
| T12 | Conciliación comercial-bodega | Recepción cerrada | lotes = líneas aprobadas | ✅ PASSED | CERRADO |
| T13 | Standard + Blanks | Recepción mixta | ambas reglas conviven sin contaminación | ✅ PASSED | CERRADO |
| T14 | Edge cases volumen nulo | Dimensiones inválidas | bloquea confirmación | ✅ PASSED | CERRADO |
| T15 | Campos duplicados eliminados | `lumber_reception.py` | Sin duplicados de campos | ✅ | CERRADO |
| T16 | Decoradores `@api.depends` consolidados | `_compute_volume_purchase` | Un solo decorador | ✅ | CERRADO |
| T17 | Importaciones reparadas | pandas/pdfplumber | Uso de openpyxl nativo | ✅ | CERRADO |
| T18 | Variables indefinidas corregidas | `action_verify_data` | `sheet` definido correctamente | ✅ | CERRADO |
| T19 | Métodos incompletos completados | `_onchange_lot_name`, `create`, etc. | Lógica implementada | ✅ | CERRADO |
| T20 | Tabla `WidthMappingTable` funcional | Anchos mm | Mapeo correcto a fracciones | ✅ | CERRADO |
| T21 | Servicio `LumberReceptionService` operativo | `_create_lots_from_packing` | Lógica extraída y funcional | ✅ | CERRADO |
| T22 | Validaciones de rango de volumen | `_is_valid_volume()` | Método implementado y probado | ✅ | CERRADO |
| T23 | Validaciones de dimensiones de lote | `_validate_lot_dimensions()` | Método implementado y probado | ✅ | CERRADO |
| T24 | Pruebas unitarias extendidas | Tests: lot_name, sanitize, volume, width_mapping, service | 9 test cases implementados y pasando | ✅ PASSED | CERRADO |
| T25 | Tests Docker pasan | Comando completo con -i madenat_lumber_core | Sin errores, módulo instala correctamente | ✅ PASSED | CERRADO |
| T26 | Service staging → stock.lot | `LumberReceptionService.create_lots_from_staging` | Crea lotes reales desde staging | ✅ PASSED | CERRADO |
| T27 | Validaciones integradas en create/write | Sanitización + validación de dimensiones | Se ejecutan correctamente sin errores | ✅ PASSED | CERRADO |
| T28 | Cálculos volumétricos blindados | vol_physical_m3, vol_purchase_m3, vol_shipment_m3 | Todos calculan con precisión 3 decimales | ✅ PASSED | CERRADO |

## 3. Caso base recomendado

- **Guía:** `40597`
- **OC:** `MC2603-306`
- **Volumen PDF:** `55.665 m³`
- **Volumen Excel:** `55.821 m³`
- **Líneas parseadas:** `12/13`



Uso recomendado del caso base:
1. cargar documentos,
2. confirmar Gate 1,
3. inspeccionar staging,
4. ejecutar pruebas de Gate 2,
5. revisar cálculo exportación,
6. validar persistencia de Gate 3.

***

## 4. Plantilla de ejecución por caso

```md
### Caso: TXX
- Fecha:
- Operador:
- Ambiente (Environment):
- Base de datos (Database):
- Módulo / commit:
- Input real:
- Resultado esperado:
- Resultado real:
- Logs relevantes:
- Evidencia adjunta:
- Estado final:
- Hallazgos:
```

***

## 5. Criterios globales de aprobación

- 0 writes en Gate 0, 1 y 2
- 0 SQL Raw en producción
- recepciones confirmadas solo vía Gate 3
- cálculos reproducibles
- trazabilidad desde `package_no` / `lot_name`

***

## 6. Lectura rápida de fallos

| Si falla | Revisar |
| -------- | ------- |
| T01 / T02 | parser, sumatorias, unidades |
| T03 | triple capa y mapeo de staging |
| T04 / T05 / T06 | `_compute_export_values()` y regla aplicada |
| T07 / T08 / T09 | `ingestion_gate.py` y contratos Gate 2 |
| T10 | Gate 3 + stock engine |
| T11 / T12 | propagación `package_no → lot_name` y creación de lotes |
| T13 | dispatcher multi-formato |
| T14 | política de tipo de cambio |

***

## 7. Definición de prueba cerrada

Una prueba no queda cerrada con “parece bien”. Queda cerrada solo si:
- el esperado está escrito,
- el resultado real está escrito,
- hay evidencia,
- se indica estado,
- y el hallazgo queda trazado a backlog o decisión si corresponde.