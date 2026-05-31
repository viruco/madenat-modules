# MADENAT — Matriz de Pruebas

**Versión documental:** 6.0.0  
**Fecha de actualización:** 2026-05-13  
**Estado:** ACTIVO — Base T01–T14 consolidada; T29–T32 definidos pero no cerrados

---

## 1. Regla operativa

Toda modificación de parser, staging, cálculos, units-of-measure, gates o persistencia debe quedar registrada aquí antes de considerarse realmente cerrada.

---

## 2. Matriz principal consolidada

| ID | Caso | Entrada | Esperado | Estado documental |
|---|---|---|---|---|
| T01 | Suma m3 por línea | Packing estándar | Suma líneas = total recepción | CERRADO |
| T02 | Suma MBF por línea | Packing estándar | MBF consistente | CERRADO |
| T03 | Triple capa | Blanks | Visual, física y nominal correctas | CERRADO |
| T04 | Regla `metric` | Línea nacional | `vol_shipment_m3 = vol_physical_m3` | CERRADO |
| T05 | Regla `f1550` | Línea S2S | cálculo exacto con factor oficial | CERRADO |
| T06 | Regla `f5085` | Línea Blanks | cálculo exacto con factor oficial | CERRADO |
| T07 | Gate 2 nominal null | Staging incompleto | bloquea confirmación | CERRADO |
| T08 | Gate 2 producto inválido | producto inactivo | bloquea confirmación | CERRADO |
| T09 | Gate 2 volumen fuera tolerancia | diferencia excesiva | bloquea confirmación | CERRADO |
| T10 | Gate 3 commit | staging válido | crea stock y picking | CERRADO |
| T11 | Recall de lote | recepción cerrada | trazabilidad por lote/paquete | CERRADO |
| T12 | Conciliación comercial-bodega | recepción cerrada | lotes = líneas aprobadas | CERRADO |
| T13 | Standard + Blanks | recepción mixta | sin contaminación entre reglas | CERRADO |
| T14 | Edge cases volumen nulo | dimensiones inválidas | bloqueo | CERRADO |

---

## 3. Matriz de saneamiento ya consolidada

| ID | Caso | Objetivo | Estado documental |
|---|---|---|---|
| T15 | Campos duplicados eliminados | evitar shadowing | CERRADO |
| T16 | `@api.depends` consolidados | eliminar duplicidad | CERRADO |
| T17 | Importaciones reparadas | estabilidad de parser | CERRADO |
| T18 | Variables indefinidas corregidas | flujo robusto | CERRADO |
| T19 | Métodos incompletos completados | base operativa | CERRADO |
| T20 | `WidthMappingTable` funcional | mapeo anchos | CERRADO |
| T21 | `LumberReceptionService` operativo | persistencia desacoplada | CERRADO |
| T22 | Validaciones de rango | calidad de datos | CERRADO |
| T23 | Validaciones de dimensiones | blindaje físico | CERRADO |
| T24 | Pruebas unitarias extendidas | cobertura adicional | CERRADO |
| T25 | Tests Docker | instalación controlada | CERRADO |
| T26 | Staging → stock.lot | persistencia real | CERRADO |
| T27 | Validaciones en create/write | integridad | CERRADO |
| T28 | Cálculos blindados | precisión 3 decimales | CERRADO |

---

## 4. Matriz nueva por largo/unidades

| ID | Caso | Entrada | Esperado | Estado documental |
|---|---|---|---|---|
| T29 | Conversión ft → m | `length_input_raw` en pies | `length` normalizado a metros | PENDIENTE |
| T30 | Conversión mm → m | `length_input_raw` en mm | `length` normalizado a metros | PENDIENTE |
| T31 | Conversión m → m | `length_input_raw` en m | `length` sin alteración | PENDIENTE |
| T32 | Quick-create subproducto | wizard mass update | alta rápida funcional | PENDIENTE |

### Bloqueante común
Ninguno de estos casos puede considerarse cerrado mientras la instalación falle por `Wrong @depends` en `_compute_lengthm`.

---

## 5. Caso base recomendado

- Guía: `40597`
- OC: `MC2603-306`
- Volumen PDF: `55.665 m³`
- Volumen Excel: `55.821 m³`
- Uso: validación integral de staging, cálculo y persistencia

---

## 6. Plantilla de ejecución

```md
### Caso: TXX
- Fecha:
- Operador:
- Ambiente:
- Base de datos:
- Rama / commit:
- Input:
- Esperado:
- Real:
- Logs:
- Evidencia:
- Estado:
- Hallazgos:
```

---

## 7. Criterios globales de aprobación

- 0 writes en Gate 0, 1 y 2
- 0 SQL raw en producción
- solo Gate 3 escribe inventario
- cálculos reproducibles
- trazabilidad desde `package_no` a `lot_name`
- coherencia de naming entre campos, vistas y `@depends`

---

## 8. Lectura rápida de fallos

| Si falla | Revisar |
|---|---|
| T01 / T02 | parser, unidades, sumatorias |
| T03 | staging y triple capa |
| T04 / T05 / T06 | reglas de exportación |
| T07 / T08 / T09 | Gate 2 y catálogo |
| T10 | Gate 3 y servicio stock |
| T11 / T12 | trazabilidad |
| T13 | dispatcher multi-formato |
| T14 | validaciones de edge |
| T29 / T30 / T31 | naming de largo, normalización y computes |
| T32 | wizard, domain y quick-create |

---

## 9. Regla documental final

Una prueba no queda cerrada porque “parece funcionar”.  
Queda cerrada cuando:
- existe esperado explícito,
- existe resultado real,
- hay evidencia,
- y continuidad + backlog quedan actualizados si el hallazgo cambia el estado del proyecto.
